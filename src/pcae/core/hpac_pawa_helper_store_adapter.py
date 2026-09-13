"""HPAC-PAWA-HELPER-001 v1.0 — real canonical-store read adapter
(phase-authorization N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL, §6-§9,
§18-§19).

This module is the narrow store adapter for the two helper operations whose
closed vocabulary is provably read-only against the real canonical protected
stores: ``certification_read`` (§18) and the store-side portion of
``ceremony_entry`` (§19 — verifying the current installation generation, not
conducting a real ceremony).

**Read/write inventory conclusion (this phase's §6/§7/§93 obligation).**
Every real canonical write path this helper's remaining three operations
would need (``admin_mutation``, ``certification_write``,
``presentation_evidence_write``) requires an ``HPACWriterCapability`` minted
by :meth:`~pcae.core.hpac_foundation.HPACStoreAuthority._mint_production_writer_capability`,
which is gated by ``_PRODUCTION_WRITER_FACTORY_SEAL`` — a seal held
**exclusively** by :mod:`pcae.core.hpac_protected_admin_writer` (every mint
call site in the repository lives in that one module; see
``mint_protected_presentation_evidence_writer`` and the PAWA
``production_writer``/``certification_writer`` factories). HPAC-PAWA-HELPER-
REQ-033 explicitly forbids "the helper" from importing that module, its
production_writer/certification_writer/recognized_certification_read_authority
symbols, or any agent-reachable module. There is no second factory and no
second seal anywhere in the codebase. Consequently, under the frozen
HPAC-PAWA-001/HPAC-PAWA-HELPER-001/HPAC-PPA-001 trio as they exist today,
**the real one-shot helper process has no code path to obtain PRODUCTION-class
write authority against any canonical store** — this is a genuine, contract-
confirmed BLOCKER for the three write operations, not an oversight this module
routes around. See the phase completion report for the full finding and
recommended successor (a narrow contract-evolution phase introducing a
second, helper-scoped mint pathway, or an explicit HPAC-PAWA-HELPER-001
amendment).

The read-only stores wired here require no such capability — every
``resolve``/``resolve_canonical`` method below is, in the canonical stores'
own words, "open to any caller" — so ``certification_read`` and the
non-mutating half of ``ceremony_entry`` can be, and are, genuinely wired to
real production store *implementations* (exercised only against disposable
test roots in this phase, per phase-authorization §45/§46).
"""

from __future__ import annotations

from typing import Dict, Mapping, Optional

from pcae.core.hpac_foundation import HPACStoreAuthority
from pcae.core.hpac_pawa_helper_protocol import CLOSED_READ_RECORD_TYPES, HelperProtocolError
from pcae.core.human_principal_registry import HumanPrincipalRegistryStore
from pcae.core.hpac_rhamp_credential_sidecar import HpacRhampCredentialSidecarStore, RhampCredentialSidecarError
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
    TrustedApprovalPresentationStore,
)

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
