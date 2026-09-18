"""HPAC-PAWA-HELPER-001 v1.0 — real canonical-store read adapter
(phase-authorization N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL, §6-§9,
§18-§19).

This module is the narrow store adapter for the two helper operations whose
closed vocabulary is provably read-only against the real canonical protected
stores: ``certification_read`` (§18) and the store-side portion of
``ceremony_entry`` (§19 — verifying the current installation generation, not
conducting a real ceremony).

**Read/write inventory — historical finding, now repaired (Model E).**
N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR-IV independently
verified that HPAC-PAWA-HELPER-001 v3.0 §30B (Model E) genuinely closes the
"the real one-shot helper process has no code path to obtain PRODUCTION-class
write authority against any canonical store" finding this module's docstring
used to record: rather than routing through the legacy, seal-gated
``_mint_production_writer_capability``/``hpac_protected_admin_writer`` path
(REQ-033 continues to forbid the helper importing that module — unchanged),
the three write operations now go through
:mod:`pcae.core.hpac_pawa_helper_writer_authority`'s three new, distinct,
sealed authority families and this module's exact-type recognition
predicates below (``perform_recognized_admin_mutation`` /
``perform_recognized_certification_write`` /
``perform_recognized_presentation_evidence_write`` — HPAC-PAWA-HELPER-REQ-148/149).

The read-only stores wired here require no capability at all — every
``resolve``/``resolve_canonical`` method below is, in the canonical stores'
own words, "open to any caller" — so ``certification_read`` and the
non-mutating half of ``ceremony_entry`` remain wired to real production store
*implementations* exactly as before this repair.
"""

from __future__ import annotations

from typing import Dict, Mapping, Optional

from pcae.core.hpac_foundation import HPACStoreAuthority
from pcae.core.hpac_foundation import HPACAuthorityClass, HPACAuthorityError
from pcae.core.hpac_pawa_helper_protocol import CLOSED_READ_RECORD_TYPES, HelperProtocolError
from pcae.core.human_principal_registry import (
    HumanPrincipalRegistryConflictError,
    HumanPrincipalRegistryError,
    HumanPrincipalRegistryNotFoundError,
    HumanPrincipalRegistryStore,
)
from pcae.core.hpac_rhamp_credential_sidecar import (
    Fido2CredentialSidecar,
    HpacRhampCredentialSidecarStore,
    RhampCredentialSidecarError,
)
from pcae.core.hpac_rhamp_counter_state import HpacRhampCounterStateStore, RhampCounterStateError
from pcae.core.protected_presentation_installation import (
    ProtectedPresentationInstallationError,
    ProtectedPresentationIntegrityError,
    ProtectedPresentationInstallationStore,
    ResolvedCurrentGeneration,
)
from pcae.core.approval_presentation import (
    ApprovalPresentationTrustError,
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationEvidence,
    TrustedApprovalPresentationStore,
)
from pcae.core.hpac_lifecycle import HPACLifecycleError, HPACLifecycleStore

#: Record types this adapter cannot back with a real canonical store under
#: the frozen architecture (see module docstring). Kept as an explicit,
#: reported set rather than a silent fallback.
BLOCKED_READ_RECORD_TYPES = frozenset({"pawa_anchor_record"})

assert BLOCKED_READ_RECORD_TYPES <= CLOSED_READ_RECORD_TYPES
assert BLOCKED_READ_RECORD_TYPES != CLOSED_READ_RECORD_TYPES  # 8 of 9 remain real-store-wireable


def _no_writer_capability(record_type: str) -> HelperProtocolError:
    return HelperProtocolError(
        "internal_fail_closed",
        f"{record_type} write requires a PRODUCTION HPACWriterCapability, which the "
        "helper has no code path to mint under HPAC-PAWA-HELPER-REQ-033 (see phase "
        "completion report) — this operation cannot be backed by a real canonical store",
    )


class _WriteBlockedEvidenceMap(dict):
    """§21 — a plain dict would let ``presentation_evidence_write`` appear to
    'succeed' by silently writing into fake in-memory state, masking the
    exact same REQ-033 writer-capability blocker documented for
    ``admin_mutation``/``certification_write``. Item assignment fails closed
    with the identical error instead, so all three blocked write operations
    fail the same way — never a silent fake success."""

    def __setitem__(self, key: str, value: Mapping[str, object]) -> None:
        raise _no_writer_capability("presentation_evidence_record")


class RealCanonicalReadAdapter:
    """Real canonical-store backing for ``certification_read`` /
    ``ceremony_entry``'s store-side reads. Duck-type compatible with
    :class:`~pcae.core.hpac_pawa_helper_protocol.ProtectedStoreFoundation`
    (``get_record``, ``ceremonies_started``) so
    ``hpac_pawa_helper_operations.py``'s dispatch handlers are unchanged
    (phase-authorization §9 narrow-adapter principle)."""

    def __init__(self, authority: HPACStoreAuthority) -> None:
        self.authority = authority
        self._principal_registry = HumanPrincipalRegistryStore(authority)
        self._sidecar_store = HpacRhampCredentialSidecarStore(authority)
        self._counter_store = HpacRhampCounterStateStore(authority)
        self._installation_store = ProtectedPresentationInstallationStore(authority)
        self._descriptor_store = PresentationMechanismDescriptorStore(authority)
        self._presentation_store = TrustedApprovalPresentationStore(authority)
        #: NOT durable across process boundaries (documented limitation —
        #: see the phase completion report's ceremony/evidence
        #: cross-process-state finding). Real one-shot-per-exec deployment
        #: never relies on this surviving a process exit; it exists only so
        #: ``ceremony_entry``'s handler keeps its existing in-process
        #: duplicate-use check when exercised as part of a single dispatch
        #: sequence (e.g. in-process tests).
        self.ceremonies_started: Dict[str, str] = {}
        self.presentation_evidence: Dict[str, Mapping[str, object]] = _WriteBlockedEvidenceMap()

    # -- §18 certification_read ------------------------------------------------

    def put_record(self, record_type: str, key: str, value: Mapping[str, object]) -> None:
        """§15/§17 — ``admin_mutation``/``certification_write`` both route
        through here; fail closed identically to the read-side blocker
        rather than raising a bare ``AttributeError`` a caller could mistake
        for an unrelated bug."""
        raise _no_writer_capability(record_type)

    def get_record(self, record_type: str, key: str) -> Optional[Mapping[str, object]]:
        if record_type not in CLOSED_READ_RECORD_TYPES:
            raise HelperProtocolError("operation_scope_invalid", f"record_type {record_type!r} not in enumerated read set")
        if record_type in BLOCKED_READ_RECORD_TYPES:
            raise HelperProtocolError(
                "internal_fail_closed",
                f"{record_type} has no real-store-wireable resolver under the frozen "
                "architecture (REQ-033 writer-mint blocker; see phase report)",
            )
        method = getattr(self, f"_read_{record_type}")
        return method(key)

    def _read_principal_record(self, key: str) -> Optional[Mapping[str, object]]:
        record = self._principal_registry.resolve_principal(key)
        return None if record is None else record.to_document()

    def _read_credential_record(self, key: str) -> Optional[Mapping[str, object]]:
        record = self._principal_registry.resolve_credential(key)
        return None if record is None else record.to_document()

    def _read_rhamp_credential_sidecar(self, key: str) -> Optional[Mapping[str, object]]:
        sidecar = self._sidecar_store.resolve(key)
        return None if sidecar is None else sidecar.to_document(include_digest=True)

    def _read_rhamp_counter_state(self, key: str) -> Optional[Mapping[str, object]]:
        try:
            state = self._counter_store.resolve(key)
        except RhampCounterStateError:
            return None
        return state.to_document(include_digest=True)

    def _read_presentation_installation_record(self, key: str) -> Optional[Mapping[str, object]]:
        resolved = self._resolve_current_generation_or_none()
        if resolved is None or resolved.record.installation_id != key:
            return None
        return resolved.record.document

    def _read_presentation_mechanism_descriptor(self, key: str) -> Optional[Mapping[str, object]]:
        descriptor = self._descriptor_store.resolve(key)
        return None if descriptor is None else descriptor.to_document(include_digest=True)

    def _read_trusted_approval_presentation_record(self, key: str) -> Optional[Mapping[str, object]]:
        """§18/§49 — closed lookup only by the ``(presentation_id,
        presentation_digest)`` pair (this store's own frozen lookup key,
        HPAC-REQ-093); ``key`` is ``"<presentation_id>:<presentation_digest>"``
        (both fields fully bound, never a bare presentation_id — a partial
        key is a request-shape error, not a "not found")."""
        if ":" not in key:
            raise HelperProtocolError(
                "target_scope_invalid", "trusted_approval_presentation_record key must be 'presentation_id:presentation_digest'"
            )
        presentation_id, presentation_digest = key.split(":", 1)
        try:
            evidence = self._presentation_store.resolve_structural(
                presentation_id=presentation_id, presentation_digest=presentation_digest
            )
        except ApprovalPresentationTrustError:
            return None
        return evidence.to_document(include_presentation_digest=True)

    def _read_helper_registration_record(self, key: str) -> Optional[Mapping[str, object]]:
        resolved = self._resolve_current_generation_or_none()
        if resolved is None or resolved.record.installation_id != key:
            return None
        return resolved.record.document

    # -- §19 ceremony_entry (store-side, real-read half only) ------------------

    def _resolve_current_generation_or_none(self) -> Optional[ResolvedCurrentGeneration]:
        try:
            return self._installation_store.resolve_current_generation()
        except (ProtectedPresentationInstallationError, ProtectedPresentationIntegrityError):
            return None

    def verify_current_generation(self, *, installation_id: str, generation: int) -> ResolvedCurrentGeneration:
        """§19/§66 — fail closed unless the request is bound to the live,
        non-revoked current generation. Raises ``HelperProtocolError`` on any
        mismatch/absence/revocation (no partial trust)."""
        resolved = self._resolve_current_generation_or_none()
        if resolved is None:
            raise HelperProtocolError("descriptor_missing", "no current protected-presentation generation installed")
        if resolved.record.installation_id != installation_id or resolved.record.generation != generation:
            raise HelperProtocolError("descriptor_generation_stale", "request installation_id/generation is not current")
        return resolved


def resolve_launcher_deployment_metadata(authority: HPACStoreAuthority) -> ResolvedCurrentGeneration:
    """§65 — the launcher's own trusted metadata resolution, reusing the
    exact same read-only resolver ``RealCanonicalReadAdapter`` uses for
    ``ceremony_entry`` (one canonical source of "what is the current,
    verified helper", never two divergent ones)."""
    store = ProtectedPresentationInstallationStore(authority)
    resolved = store.resolve_current_generation()
    if resolved is None:
        raise HelperProtocolError("descriptor_missing", "no current protected-presentation generation installed")
    return resolved


# ---------------------------------------------------------------------------
# N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL (Model E) — store-side exact-type
# recognition + bounded real-store mutation for the three previously blocked
# write operations (HPAC-PAWA-HELPER-REQ-148/149/150/30B.12/30B.13/30B.14).
#
# Each ``perform_recognized_*`` function is called only from
# ``pcae.core.hpac_pawa_helper_writer_authority``'s facades, immediately after
# that module mints its own new, sealed authority object. Recognition here
# checks ``type(authority) is ExactClass`` (never ``isinstance`` against a
# shared base — PAWAH-INV-20) plus every scoping field (§150) against the
# authority object *and* against live protected-root state, before any write
# is attempted. Imports of the authority classes are local to avoid a
# module-load-time circular import with ``hpac_pawa_helper_writer_authority``
# (which imports these ``perform_recognized_*`` functions).
# ---------------------------------------------------------------------------


def _require_currentness(
    store_authority: HPACStoreAuthority, *, installation_id: str, generation: int
) -> ResolvedCurrentGeneration:
    store = ProtectedPresentationInstallationStore(store_authority)
    try:
        resolved = store.resolve_current_generation()
    except (ProtectedPresentationInstallationError, ProtectedPresentationIntegrityError) as exc:
        raise HelperProtocolError("descriptor_missing", f"no current protected-presentation generation: {exc}")
    if resolved is None:
        raise HelperProtocolError("descriptor_missing", "no current protected-presentation generation installed")
    if resolved.record.installation_id != installation_id:
        raise HelperProtocolError("descriptor_installation_mismatch", "installation_id is not current")
    if resolved.anchor.current_generation != generation:
        raise HelperProtocolError("descriptor_generation_stale", "generation is not current")
    return resolved


def perform_recognized_admin_mutation(
    authority: object,
    store_authority: HPACStoreAuthority,
    *,
    mutation: str,
    subject: Optional[str],
    session_id: str,
    request_id: str,
    installation_id: str,
    generation: int,
    operation_params: Mapping[str, object],
) -> str:
    """§30B.12 row 1 / §157 — ``HelperAdminMutationAuthority`` PERMIT only
    the exact bound ``admin_mutation`` subtype it was minted for; every
    other family/operation combination is unreachable from this function's
    own caller (the writer-authority module only ever calls this with a
    freshly-minted ``HelperAdminMutationAuthority``, but the exact-type check
    below is retained as the mechanical, non-bypassable recognition gate the
    contract requires, independent of caller discipline)."""

    from pcae.core.hpac_pawa_helper_writer_authority import (
        HelperAdminMutationAuthority,
        HelperWriterAuthorityError,
    )

    if type(authority) is not HelperAdminMutationAuthority:
        raise HelperProtocolError("target_scope_invalid", "not a HelperAdminMutationAuthority")
    if authority.authority_class is not HPACAuthorityClass.PRODUCTION:
        raise HelperProtocolError("internal_fail_closed", "NON_REAL authority cannot perform a REAL mutation")
    if (
        authority.mutation != mutation
        or authority.subject != subject
        or authority.session_id != session_id
        or authority.request_id != request_id
        or authority.installation_id != installation_id
        or authority.generation != generation
    ):
        raise HelperProtocolError("target_scope_invalid", "authority binding does not match this request")

    _require_currentness(store_authority, installation_id=installation_id, generation=generation)

    from pcae.core.hpac_pawa_helper_writer_authority import _new_internal_capability

    try:
        if mutation == "enroll_principal":
            store = HumanPrincipalRegistryStore(store_authority)
            cap = _new_internal_capability(store_authority, role=store._WRITER_ROLE, subject=subject)
            record = store.enroll_principal(
                cap,
                principal_id=subject,
                enrollment_provenance_ref=str(operation_params["enrollment_provenance_ref"]),
                enrolled_at=str(operation_params["enrolled_at"]),
            )
            return f"human_principal_registry:principal:{record.principal_id}"

        if mutation == "revoke_principal":
            store = HumanPrincipalRegistryStore(store_authority)
            cap = _new_internal_capability(store_authority, role=store._WRITER_ROLE, subject=subject)
            record = store.revoke_principal(cap, principal_id=subject, revoked_at=str(operation_params["revoked_at"]))
            return f"human_principal_registry:principal:{record.principal_id}"

        if mutation == "revoke_credential":
            store = HumanPrincipalRegistryStore(store_authority)
            cap = _new_internal_capability(store_authority, role=store._WRITER_ROLE, subject=subject)
            record = store.revoke_credential(cap, credential_id=subject, revoked_at=str(operation_params["revoked_at"]))
            return f"human_principal_registry:credential:{record.credential_id}"

        if mutation == "enroll_credential":
            store = HumanPrincipalRegistryStore(store_authority)
            # HPAC-PAWA-REQ-100 — bound to the enrollment transaction id
            # (``subject`` here), not the not-yet-existing credential_id.
            cap = _new_internal_capability(store_authority, role=store._WRITER_ROLE, subject=subject)
            record = store.enroll_credential(
                cap,
                credential_id=str(operation_params["credential_id"]),
                principal_id=str(operation_params["principal_id"]),
                mechanism_id=str(operation_params["mechanism_id"]),
                public_key=str(operation_params["public_key"]),
                assurance_capabilities=tuple(operation_params.get("assurance_capabilities", ())),
                enrollment_provenance_ref=str(operation_params["enrollment_provenance_ref"]),
                enrolled_at=str(operation_params["enrolled_at"]),
                _production_transaction_subject=subject,
            )
            return f"human_principal_registry:credential:{record.credential_id}"

        if mutation == "initialize_credential_sidecar_state":
            sidecar_store = HpacRhampCredentialSidecarStore(store_authority)
            cap = _new_internal_capability(store_authority, role=sidecar_store._WRITER_ROLE, subject=subject)
            sidecar = Fido2CredentialSidecar(
                credential_id=str(operation_params["credential_id"]),
                principal_id=str(operation_params["principal_id"]),
                raw_credential_id=str(operation_params["raw_credential_id"]),
                cose_public_key=str(operation_params["cose_public_key"]),
                transports=tuple(operation_params.get("transports", ())),
                aaguid=operation_params.get("aaguid"),
                created_at=str(operation_params["created_at"]),
                writer_provenance_ref="",
                status="active",
            )
            created = sidecar_store.create_canonical(cap, sidecar, transaction_subject=subject)
            return f"rhamp_credential_sidecar:{created.credential_id}"

        # N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR:
        # ``configure_presentation_mechanism`` and ``configure_privileged_helper``
        # are no longer dispatchable through this admitted helper's own
        # admin_mutation route (HPAC-PAWA-HELPER-REQ-184/HPAC-PAWA-REQ-345).
        # Both are provisioning operations that exist outside
        # ``CLOSED_ADMIN_MUTATIONS`` and are unreachable here by construction;
        # they are dispatched only through the PAWA deployment-root-mediated
        # standalone-script path (Model P-D) —
        # ``pcae.core.hpac_protected_presentation_admin`` for
        # ``configure_presentation_mechanism``.
    except (
        HumanPrincipalRegistryError,
        HumanPrincipalRegistryConflictError,
        HumanPrincipalRegistryNotFoundError,
        RhampCredentialSidecarError,
        ProtectedPresentationInstallationError,
        ProtectedPresentationIntegrityError,
        HPACAuthorityError,
        HelperWriterAuthorityError,
        KeyError,
    ) as exc:
        raise HelperProtocolError("internal_fail_closed", f"{mutation} failed: {exc}") from exc

    raise HelperProtocolError("operation_scope_invalid", f"unrecognized admin mutation {mutation!r}")


def perform_recognized_certification_write(
    authority: object,
    store_authority: HPACStoreAuthority,
    *,
    role: str,
    subject: str,
    session_id: str,
    request_id: str,
    installation_id: str,
    generation: int,
    operation_params: Mapping[str, object],
) -> str:
    """§30B.13 — five-role matrix: ``HelperCertificationWriteAuthority``
    minted for role R permits only role R's own store action."""

    from pcae.core.hpac_pawa_helper_writer_authority import (
        HelperCertificationWriteAuthority,
        HelperWriterAuthorityError,
    )

    if type(authority) is not HelperCertificationWriteAuthority:
        raise HelperProtocolError("target_scope_invalid", "not a HelperCertificationWriteAuthority")
    if authority.authority_class is not HPACAuthorityClass.PRODUCTION:
        raise HelperProtocolError("internal_fail_closed", "NON_REAL authority cannot perform a REAL mutation")
    if (
        authority.role != role
        or authority.subject != subject
        or authority.session_id != session_id
        or authority.request_id != request_id
        or authority.installation_id != installation_id
        or authority.generation != generation
    ):
        raise HelperProtocolError("target_scope_invalid", "authority binding does not match this request")

    _require_currentness(store_authority, installation_id=installation_id, generation=generation)

    from pcae.core.hpac_pawa_helper_writer_authority import _new_internal_capability

    lifecycle = HPACLifecycleStore(store_authority)
    try:
        if role == "hpac_challenge_coordinator":
            cap = _new_internal_capability(store_authority, role="hpac_challenge_coordinator", subject=subject)
            event = lifecycle.open_challenge(
                proof_id=subject,
                approval_id=str(operation_params["approval_id"]),
                invocation_id=str(operation_params["invocation_id"]),
                attempt_id=str(operation_params["attempt_id"]),
                principal_id=str(operation_params["principal_id"]),
                credential_id=str(operation_params["credential_id"]),
                mechanism_id=str(operation_params["mechanism_id"]),
                approval_subject_digest=str(operation_params["approval_subject_digest"]),
                challenge_digest=str(operation_params["challenge_digest"]),
                occurred_at=str(operation_params["occurred_at"]),
                resolved_presentation=operation_params["resolved_presentation"],
                _writer=cap,
            )
            return f"hpac_lifecycle:{event.proof_id}:{event.state}"

        if role == "hpac_assertion_recorder":
            cap = _new_internal_capability(store_authority, role="hpac_assertion_recorder", subject=subject)
            event = lifecycle.record_assertion(
                proof_id=subject,
                assertion_digest=str(operation_params["assertion_digest"]),
                occurred_at=str(operation_params["occurred_at"]),
                _writer=cap,
            )
            return f"hpac_lifecycle:{event.proof_id}:{event.state}"

        if role == "human_authentication_proof_verifier":
            cap = _new_internal_capability(
                store_authority, role="human_authentication_proof_verifier", subject=subject
            )
            event = lifecycle.record_verified(
                proof_id=subject,
                proof_digest=str(operation_params["proof_digest"]),
                registry_state_digest=str(operation_params["registry_state_digest"]),
                verifier_version=str(operation_params["verifier_version"]),
                occurred_at=str(operation_params["occurred_at"]),
                _writer=cap,
            )
            return f"hpac_lifecycle:{event.proof_id}:{event.state}"

        if role == "hpac_gate5_binder":
            cap = _new_internal_capability(store_authority, role="hpac_gate5_binder", subject=subject)
            event = lifecycle.bind_gate5(
                proof_id=subject,
                approval_digest=str(operation_params["approval_digest"]),
                occurred_at=str(operation_params["occurred_at"]),
                _writer=cap,
            )
            return f"hpac_lifecycle:{event.proof_id}:{event.state}"

        if role == "hpac_rhamp_counter_state_verifier":
            counter_store = HpacRhampCounterStateStore(store_authority)
            cap = _new_internal_capability(
                store_authority, role="human_principal_registry_admin", subject=subject
            )
            state = counter_store.initialize_canonical(
                cap,
                credential_id=subject,
                updated_at=str(operation_params["updated_at"]),
                transaction_subject=subject,
            )
            return f"rhamp_counter_state:{state.credential_id}"
    except (HPACLifecycleError, RhampCounterStateError, HPACAuthorityError, HelperWriterAuthorityError, KeyError) as exc:
        raise HelperProtocolError("internal_fail_closed", f"certification_write[{role}] failed: {exc}") from exc

    raise HelperProtocolError("operation_scope_invalid", f"unrecognized certification role {role!r}")


def perform_recognized_presentation_evidence_write(
    authority: object,
    store_authority: HPACStoreAuthority,
    *,
    invocation_id: str,
    attempt_id: str,
    session_id: str,
    request_id: str,
    installation_id: str,
    generation: int,
    operation_params: Mapping[str, object],
) -> str:
    """§30B.12 row 3 / §158 — create-only; the exact ceremony binding is
    checked against the authority object, then the real store's own
    create-only atomic write (never overwrite) is the terminal gate."""

    from pcae.core.hpac_pawa_helper_writer_authority import (
        HelperPresentationEvidenceAuthority,
        HelperWriterAuthorityError,
    )

    if type(authority) is not HelperPresentationEvidenceAuthority:
        raise HelperProtocolError("target_scope_invalid", "not a HelperPresentationEvidenceAuthority")
    if authority.authority_class is not HPACAuthorityClass.PRODUCTION:
        raise HelperProtocolError("internal_fail_closed", "NON_REAL authority cannot perform a REAL mutation")
    if (
        authority.invocation_id != invocation_id
        or authority.attempt_id != attempt_id
        or authority.session_id != session_id
        or authority.request_id != request_id
        or authority.installation_id != installation_id
        or authority.generation != generation
    ):
        raise HelperProtocolError("target_scope_invalid", "authority binding does not match this request")

    _require_currentness(store_authority, installation_id=installation_id, generation=generation)

    forbidden = {"approved", "verified", "human_present", "authenticated"}
    if forbidden & set(operation_params):
        raise HelperProtocolError(
            "operation_scope_invalid",
            "presentation_evidence_write cannot accept caller-asserted approval/authentication facts",
        )
    if not operation_params.get("ceremony_approve_ref"):
        raise HelperProtocolError("target_scope_invalid", "no bound ceremony_approve_ref for this evidence write")

    from pcae.core.hpac_pawa_helper_writer_authority import _new_internal_capability
    from pcae.core.hpac_foundation import canonical_digest

    try:
        mechanism_id = str(operation_params["mechanism_id"])
        body = {
            "presentation_schema_version": "HPAC-PRESENTATION-EVIDENCE/2.0",
            "presentation_id": str(operation_params["presentation_id"]),
            "approval_id": str(operation_params["approval_id"]),
            "canonical_subject": dict(operation_params["canonical_subject"]),
            "approval_subject_digest": str(operation_params["approval_subject_digest"]),
            "mechanism_ref": dict(operation_params["mechanism_ref"]),
            "human_visible_facts": dict(operation_params["human_visible_facts"]),
            "human_visible_representation_digest": str(operation_params["human_visible_representation_digest"]),
            "presented_at": str(operation_params["presented_at"]),
            "election": dict(operation_params["election"]),
            "mechanism_attestation": str(operation_params["mechanism_attestation"]),
            "mechanism_attestation_digest": str(operation_params["mechanism_attestation_digest"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise HelperProtocolError(
            "operation_scope_invalid", f"presentation_evidence_write operation_params malformed or incomplete: {exc}"
        ) from exc
    presentation_digest = canonical_digest(body)
    evidence = TrustedApprovalPresentationEvidence(
        presentation_schema_version=body["presentation_schema_version"],
        presentation_id=body["presentation_id"],
        presentation_digest=presentation_digest,
        approval_id=body["approval_id"],
        canonical_subject=body["canonical_subject"],
        approval_subject_digest=body["approval_subject_digest"],
        mechanism_ref=body["mechanism_ref"],
        human_visible_facts=body["human_visible_facts"],
        human_visible_representation_digest=body["human_visible_representation_digest"],
        presented_at=body["presented_at"],
        election=body["election"],
        mechanism_attestation=body["mechanism_attestation"],
        mechanism_attestation_digest=body["mechanism_attestation_digest"],
    )

    presentation_store = TrustedApprovalPresentationStore(store_authority)
    try:
        # _new_internal_capability minted but unused by the plain create()
        # path (kept only so a future canonical-binding upgrade to
        # create_canonical() has the capability already in hand); create()
        # is this store's own sole write path and independently re-validates
        # every structural invariant on read (module docstring, approval_presentation.py).
        _new_internal_capability(store_authority, role=presentation_store._WRITER_ROLE, subject=mechanism_id)
        created = presentation_store.create(evidence)
    except (ApprovalPresentationTrustError, HPACAuthorityError, HelperWriterAuthorityError) as exc:
        raise HelperProtocolError("internal_fail_closed", f"presentation_evidence_write failed: {exc}") from exc
    return f"trusted_approval_presentation:{created.presentation_id}"
