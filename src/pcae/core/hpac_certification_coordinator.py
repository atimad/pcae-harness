"""HPAC-PAWA-001 v1.3 §38A — the N-16-5 real-human-authentication
**certification coordinator**: the one bounded, enumerated production
consumer of the §33A ``certification_writer`` factory
(``hpac_protected_admin_writer``). It orchestrates the canonical
authentication-lifecycle chain for one certification ceremony —
challenge → assertion → proof/verified → Gate-5 binding → counter-state —
by minting exactly one single-use, non-bearer, process-local,
restart-dead ``PRODUCTION`` certification-lifecycle ``HPACWriterCapability``
per role per ceremony and threading it into the matching **existing
canonical store** call.

**This module is a non-agent-importable, local, out-of-band
deployment-owner tool** (HPAC-PAWA-REQ-241). Ordinary agent / runtime /
Gate / plugin / ``pcae`` CLI code SHALL NOT import it — directly or
transitively — and the §39A guard tests enforce that against
``src/pcae/cli.py``, ``src/pcae/commands/**``, and
``src/pcae/core/agent.py``. It is not a ``pcae`` CLI subcommand and is not
in any dispatch table. It is reached only from the standalone
``scripts/hpac_certification_admin.py`` entry point (mirroring
``hatp_certification_admin.py``), run by an operator logged in as the
deployment owner.

**What this coordinator SHALL NOT do (HPAC-PAWA-REQ-261..268, PAWA-INV-13):**
it does not manufacture a human APPROVE / REJECT, FIDO2 user presence or
user verification, a real protected presentation, or a real authenticator
assertion; it does not construct a ``PRODUCTION``
``AuthenticatedHumanPrincipal`` (that stays with
``verify_human_authentication(require_real_assurance=True)``); it does not
manufacture or bypass a Gate result, override PB or policy, issue a
runtime approval / capability / ``DispatchEnvelope``, or transition the
runtime out of ``Observed`` / ``observe`` / ``unavailable``. The
certification-authority path **terminates no later than the bounded
Gate-5 certification result**. ``coordinator ≠ human principal``,
``coordinator ≠ protected human approval``, ``coordinator ≠
NativeCtap2Provider``, ``coordinator ≠ credential authority``,
``coordinator ≠ Gate 5``, ``coordinator ≠ human authentication verifier``,
``coordinator ≠ counter store``, ``coordinator ≠ presentation evidence
writer``.

Deterministic authentication / presentation evidence NEVER becomes REAL
assurance through this coordinator — its own production status does not
elevate the evidence class (HPAC-PAWA-REQ-263).

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R
(alias N16-5-H3-IMPL).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import HPACStoreAuthority, HPACWriterCapability
from pcae.core.hpac_lifecycle import HPACLifecycleStore, LifecycleEvent
from pcae.core.hpac_protected_admin_writer import (
    CERTIFICATION_COUNTER_ROLE,
    CertificationWriterHandle,
    PawaError,
    certification_writer,
)
from pcae.core.hpac_rhamp_counter_state import HpacRhampCounterStateStore
from pcae.core.human_authentication_proof import (
    HumanAuthenticationProof,
    HumanAuthenticationProofStore,
    new_proof_id,
)

__all__ = [
    "CertificationCoordinatorError",
    "CertificationSession",
    "HpacCertificationCoordinator",
    "new_certification_session_id",
]

_CHALLENGE_ROLE = "hpac_challenge_coordinator"
_ASSERTION_ROLE = "hpac_assertion_recorder"
_PROOF_VERIFIER_ROLE = "human_authentication_proof_verifier"
_GATE5_BINDER_ROLE = "hpac_gate5_binder"


class CertificationCoordinatorError(Exception):
    """A terminal certification-coordination failure. Wraps the underlying
    :class:`PawaError` / store error; ``pawa_failure_code`` (when present)
    is exactly one member of the unchanged 21-value taxonomy."""

    def __init__(self, message: str, *, pawa_failure_code: Optional[str] = None) -> None:
        super().__init__(message)
        self.pawa_failure_code = pawa_failure_code


def _now() -> str:
    moment = datetime.now(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def new_certification_session_id() -> str:
    import uuid as _uuid

    return f"hcs-{_uuid.uuid4().hex}"


@dataclass(frozen=True)
class _Seams:
    """Disclosed test-only seams (HPAC-PAWA-REQ-166 / §72/§73). A guard
    test asserts no non-test caller populates any of them. They are handed
    straight through to ``certification_writer``; ``ceremony_mode`` becomes
    ``test-only`` when any is set."""

    protected_root: Optional[Path] = None
    configured_agent_identity_source: object = None
    topology_probe: object = None
    caller_module: Optional[str] = None


class HpacCertificationCoordinator:
    """The §38A certification coordinator. One instance per
    ``scripts/hpac_certification_admin.py`` invocation (short-lived — one
    ceremony per invocation, the process exits after, HPAC-PAWA-REQ-259)."""

    def __init__(
        self,
        *,
        _protected_root: Optional[Path] = None,
        _configured_agent_identity_source: object = None,
        _topology_probe: object = None,
        _caller_module: Optional[str] = None,
    ) -> None:
        self._seams = _Seams(
            protected_root=_protected_root,
            configured_agent_identity_source=_configured_agent_identity_source,
            topology_probe=_topology_probe,
            caller_module=_caller_module,
        )

    @property
    def ceremony_mode(self) -> str:
        s = self._seams
        if (
            s.protected_root is not None
            or s.configured_agent_identity_source is not None
            or s.topology_probe is not None
            or s.caller_module is not None
        ):
            return "test-only"
        return "production"

    def begin_session(
        self,
        *,
        principal_id: str,
        credential_id: str,
        proof_id: Optional[str] = None,
    ) -> "CertificationSession":
        """Reserve the ``certification_session_id`` and ``proof_id`` for one
        ceremony (§43A / HPAC-PAWA-REQ-256 — reserved before the ceremony,
        exactly as §100 reserves an enrollment-transaction id). Mints
        nothing; the §33A recognition sequence runs fresh on the first
        capability request."""

        if not isinstance(principal_id, str) or not principal_id.strip():
            raise CertificationCoordinatorError("principal_id must be a non-empty string")
        if not isinstance(credential_id, str) or not credential_id.strip():
            raise CertificationCoordinatorError("credential_id must be a non-empty string")
        return CertificationSession(
            coordinator=self,
            certification_session_id=new_certification_session_id(),
            principal_id=principal_id,
            credential_id=credential_id,
            proof_id=proof_id or new_proof_id(),
        )

    # ── the sole caller of certification_writer (§39A guard target) ──────
    def _mint(
        self,
        role: str,
        *,
        certification_session_id: str,
        principal_id: str,
        credential_id: str,
        proof_id: str,
    ) -> CertificationWriterHandle:
        s = self._seams
        try:
            return certification_writer(
                role,
                certification_session_id=certification_session_id,
                principal_id=principal_id,
                credential_id=credential_id,
                proof_id=proof_id,
                _protected_root=s.protected_root,
                _configured_agent_identity_source=s.configured_agent_identity_source,
                _topology_probe=s.topology_probe,
                _caller_module=s.caller_module,
            )
        except PawaError as exc:
            raise CertificationCoordinatorError(
                f"certification writer mint refused ({exc.code}): {exc.detail}",
                pawa_failure_code=exc.code,
            ) from exc


class CertificationSession:
    """One bounded certification ceremony. Each ``*_canonical`` step mints a
    fresh single-use writer, threads it into exactly one existing canonical
    store call, and discards it (§49A). The raw capabilities are never
    returned to the caller (HPAC-PAWA-REQ-250 / prompt §87)."""

    __slots__ = (
        "_coordinator",
        "certification_session_id",
        "principal_id",
        "credential_id",
        "proof_id",
        "_challenge_done",
        "_assertion_done",
        "_verified_done",
        "_gate5_reached",
    )

    def __init__(
        self,
        *,
        coordinator: HpacCertificationCoordinator,
        certification_session_id: str,
        principal_id: str,
        credential_id: str,
        proof_id: str,
    ) -> None:
        self._coordinator = coordinator
        self.certification_session_id = certification_session_id
        self.principal_id = principal_id
        self.credential_id = credential_id
        self.proof_id = proof_id
        self._challenge_done = False
        self._assertion_done = False
        self._verified_done = False
        self._gate5_reached = False

    def _mint(self, role: str) -> CertificationWriterHandle:
        return self._coordinator._mint(
            role,
            certification_session_id=self.certification_session_id,
            principal_id=self.principal_id,
            credential_id=self.credential_id,
            proof_id=self.proof_id,
        )

    # ── step 1 — open the trusted authentication-challenge lifecycle ─────
    def open_challenge(
        self,
        *,
        approval_id: str,
        invocation_id: str,
        attempt_id: str,
        mechanism_id: str,
        presentation_id: str,
        presentation_digest: str,
        challenge: object,
        occurred_at: Optional[str] = None,
    ) -> LifecycleEvent:
        """The trusted presentation evidence is named by a bare
        ``(presentation_id, presentation_digest)`` and **re-resolved by this
        coordinator on the freshly-recognized §33A production authority** —
        an ``HPACResolvedRecord`` sealed to some other authority instance is
        never accepted (HPAC-REQ-053 discipline)."""

        if self._challenge_done:
            raise CertificationCoordinatorError("challenge already opened for this session")
        handle = self._mint(_CHALLENGE_ROLE)
        authority = handle.authority
        store = HPACLifecycleStore(authority)
        capability = self._consume(handle, _CHALLENGE_ROLE, self.proof_id)
        try:
            from pcae.core.approval_presentation import (
                PresentationMechanismDescriptorStore,
                TrustedApprovalPresentationStore,
            )

            resolved_presentation = TrustedApprovalPresentationStore(authority).resolve_canonical(
                presentation_id=presentation_id,
                presentation_digest=presentation_digest,
                descriptor_store=PresentationMechanismDescriptorStore(authority),
            )
            if resolved_presentation is None:
                raise CertificationCoordinatorError("trusted presentation evidence does not resolve")
            event = store.open_challenge_canonical(
                capability,
                proof_id=self.proof_id,
                approval_id=approval_id,
                invocation_id=invocation_id,
                attempt_id=attempt_id,
                principal_id=self.principal_id,
                credential_id=self.credential_id,
                mechanism_id=mechanism_id,
                occurred_at=occurred_at or _now(),
                resolved_presentation=resolved_presentation,
                challenge=challenge,
            )
        except CertificationCoordinatorError:
            raise
        except Exception as exc:  # noqa: BLE001 — fail-closed boundary
            raise CertificationCoordinatorError(f"open_challenge failed: {type(exc).__name__}: {exc}") from exc
        self._challenge_done = True
        return event

    # ── step 2 — record one validated assertion lifecycle object ────────
    def record_assertion(
        self,
        *,
        assertion_digest: str,
        occurred_at: Optional[str] = None,
    ) -> LifecycleEvent:
        if not self._challenge_done:
            raise CertificationCoordinatorError("record_assertion requires an open challenge")
        if self._assertion_done:
            raise CertificationCoordinatorError("assertion already recorded for this session")
        handle = self._mint(_ASSERTION_ROLE)
        store = HPACLifecycleStore(handle.authority)
        capability = self._consume(handle, _ASSERTION_ROLE, self.proof_id)
        try:
            event = store.record_assertion_canonical(
                capability,
                proof_id=self.proof_id,
                assertion_digest=assertion_digest,
                occurred_at=occurred_at or _now(),
            )
        except Exception as exc:  # noqa: BLE001
            raise CertificationCoordinatorError(f"record_assertion failed: {type(exc).__name__}: {exc}") from exc
        self._assertion_done = True
        return event

    # ── step 3 — create the canonical proof + record verified state ─────
    def record_verified_proof(
        self,
        *,
        proof: HumanAuthenticationProof,
        registry_state_digest: str,
        verifier_version: str,
        occurred_at: Optional[str] = None,
    ) -> LifecycleEvent:
        if not self._assertion_done:
            raise CertificationCoordinatorError("record_verified_proof requires a recorded assertion")
        if self._verified_done:
            raise CertificationCoordinatorError("verified state already recorded for this session")
        if proof.proof_id != self.proof_id:
            raise CertificationCoordinatorError("proof.proof_id does not match the reserved session proof_id")
        occurred_at = occurred_at or _now()
        handle = self._mint(_PROOF_VERIFIER_ROLE)  # minted _multi_write (§42B / §49A)
        authority = handle.authority
        proof_store = HumanAuthenticationProofStore(authority)
        lifecycle_store = HPACLifecycleStore(authority)
        capability = self._consume(handle, _PROOF_VERIFIER_ROLE, self.proof_id)
        try:
            proof_store.create_canonical(
                capability, proof, certification_proof_subject=self.proof_id
            )
            resolved_proof = proof_store.resolve_canonical(self.proof_id)
            event = lifecycle_store.record_verified_canonical(
                capability,
                resolved_proof=resolved_proof,
                registry_state_digest=registry_state_digest,
                verifier_version=verifier_version,
                occurred_at=occurred_at,
            )
        except Exception as exc:  # noqa: BLE001
            raise CertificationCoordinatorError(
                f"record_verified_proof failed: {type(exc).__name__}: {exc}"
            ) from exc
        # §49A — spend the one verification-transaction capability once,
        # after both writes + the read-back.
        handle.complete()
        self._verified_done = True
        return event

    # ── step 4/5 — bind Gate 5 + apply the counter transition, via the
    #     existing real-assurance verifier. Terminates at the bounded
    #     Gate-5 assurance result (§41 / §68A). ──────────────────────────
    def reach_gate5_assurance(
        self,
        *,
        challenge: object,
        approval_id: str,
        now: str,
        occurred_at: Optional[str] = None,
        verifier_version: str = "hpac-verifier/1.0",
        require_real_assurance: bool = True,
        max_proof_age_seconds: Optional[int] = None,
    ) -> object:
        """Mint the ``hpac_gate5_binder`` and
        ``hpac_rhamp_counter_state_verifier`` capabilities and hand them to
        ``verify_human_authentication`` — the sole PRODUCTION
        ``AuthenticatedHumanPrincipal`` issuer, whose
        ``require_real_assurance`` check this coordinator does **not**
        relax. Returns the verifier-issued principal (the bounded assurance
        result); it does not itself invoke Gate 6+ or any runtime effect."""

        if not self._verified_done:
            raise CertificationCoordinatorError("reach_gate5_assurance requires a recorded verified proof")
        if self._gate5_reached:
            raise CertificationCoordinatorError("Gate-5 assurance already reached for this session")
        occurred_at = occurred_at or _now()

        from pcae.core.hpac_verifier import verify_human_authentication

        from pcae.core.approval_presentation import (
            PresentationMechanismDescriptorStore,
            TrustedApprovalPresentationStore,
        )
        from pcae.core.human_principal_registry import HumanPrincipalRegistryStore
        from pcae.core.hpac_rhamp_credential_sidecar import HpacRhampCredentialSidecarStore

        gate5_handle = self._mint(_GATE5_BINDER_ROLE)
        counter_handle = self._mint(CERTIFICATION_COUNTER_ROLE)
        gate5_authority = gate5_handle.authority
        counter_authority = counter_handle.authority

        # Every read store is (re-)built on the freshly-recognized §33A
        # production authority for this step; the counter store is paired
        # with its own writer's authority instance. No caller-supplied
        # resolved record or store crosses an authority-seal boundary.
        lifecycle_store = HPACLifecycleStore(gate5_authority)
        proof_store = HumanAuthenticationProofStore(gate5_authority)
        registry = HumanPrincipalRegistryStore(gate5_authority)
        presentation_store = TrustedApprovalPresentationStore(gate5_authority)
        descriptor_store = PresentationMechanismDescriptorStore(gate5_authority)
        sidecar_store = HpacRhampCredentialSidecarStore(gate5_authority)
        counter_state_store = HpacRhampCounterStateStore(counter_authority)

        gate5_writer = self._consume(gate5_handle, _GATE5_BINDER_ROLE, self.proof_id)
        counter_state_writer = self._consume(
            counter_handle, CERTIFICATION_COUNTER_ROLE, self.credential_id
        )
        try:
            principal = verify_human_authentication(
                registry=registry,
                presentation_store=presentation_store,
                descriptor_store=descriptor_store,
                proof_store=proof_store,
                lifecycle_store=lifecycle_store,
                challenge=challenge,
                proof_id=self.proof_id,
                approval_id=approval_id,
                now=now,
                occurred_at=occurred_at,
                gate5_writer=gate5_writer,
                verifier_version=verifier_version,
                require_real_assurance=require_real_assurance,
                max_proof_age_seconds=max_proof_age_seconds,
                sidecar_store=sidecar_store,
                counter_state_store=counter_state_store,
                counter_state_writer=counter_state_writer,
            )
        except Exception as exc:  # noqa: BLE001
            raise CertificationCoordinatorError(
                f"reach_gate5_assurance failed: {type(exc).__name__}: {exc}"
            ) from exc
        self._gate5_reached = True
        return principal

    def _consume(
        self, handle: CertificationWriterHandle, role: str, subject: str
    ) -> HPACWriterCapability:
        try:
            return handle.consume(
                role,
                certification_session_id=self.certification_session_id,
                subject=subject,
            )
        except PawaError as exc:
            raise CertificationCoordinatorError(
                f"certification capability consume refused ({exc.code}): {exc.detail}",
                pawa_failure_code=exc.code,
            ) from exc
