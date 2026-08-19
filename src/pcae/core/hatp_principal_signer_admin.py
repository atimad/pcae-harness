"""HPSE-001 Writer — Principal/Signer Enrollment Administration. Phase
149O.20L.7O.2F (Surface C), implementing
`docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` §11-§18,
§29-§31 (HPSE-REQ-026..046, HPSE-REQ-056..058).

Sibling module to `hatp_bootstrap.py` and `hatp_deployment_binding_
admin.py`, mirroring the latter's structure closely: `hatp_bootstrap.py`
(the read-only trust-store module) stays byte-unchanged in its own
public read API by this module's addition (its schema *was* widened
this same phase for `PrincipalRecord.revoked_at`, Surface D). Every
mutation goes through this module's own writer primitives, sharing
`registry.json`'s existing `.deployment-binding-transition.lock` with
`hatp_deployment_binding_admin.py` (HPSE-REQ-033: one whole-registry-
document transition lock, not a second section-scoped one).

Never imported by `cli.py`, `commands/agent.py`, `core/agent.py`, or any
other agent-reachable code path (HPSE-REQ-028/029). The intended caller
is `scripts/hatp_principal_signer_admin.py`, a standalone,
non-agent-writable script.

**The cross-registry precondition (HPSE-REQ-056) and continuous two-lock
hold (HHCE-REQ-037) are this module's load-bearing property.** `enroll_
signer` is the only operation in this bundled implementation that needs
both `hardware-credentials.json`'s lock and `registry.json`'s lock. It
acquires them in HPSE-REQ-057's fixed global order -- the hardware-
credential-store lock (`hatp_hardware_credential_admin.
hardware_credential_transition_lock`) OUTER, `.deployment-binding-
transition.lock` INNER -- and holds BOTH continuously from the
HPSE-REQ-056 precondition check, through principal/signer validation,
through the `registry.json` write, through that write's read-back
verification, through outcome classification. No release/reacquire
occurs between the precondition check and the write (HHCE-REQ-037): the
two `with` statements below are nested, not sequential, and the entire
critical section (from `_hardware_credential_transition_lock(hw_root):`
to the end of the inner `with` block) executes inside both context
managers at once. This makes HPSE-REQ-058(C) ("signer write succeeds,
credential record missing") structurally unreachable through this
writer, not merely improbable -- there is no code path where the
credential-precondition check and the signer write are not both
protected by the identical, continuously-held pair of locks.

`enroll_signer` never accepts a caller-supplied `signer_key_id`
(HPSE-REQ-010): it is resolved live, once, from the enrolling hardware
provider's own enrollment ceremony -- a `CredentialEnrollmentEvidence`-
shaped object the caller has already obtained (e.g. from `Fido2Hardware
Provider.enroll_credential()`, Surface A) and, in the same administrative
session, already registered via `hatp_hardware_credential_admin.
register_credential()` (Surface B) before `enroll_signer` is called.
`enroll_signer` re-checks that registration live, under the lock, rather
than trusting the caller's claim that registration happened.

Every mutating operation, including idempotent no-ops, emits exactly one
audit event (HPSE-REQ-038/070): registration and enrollment are always
two distinct, separately attributable acts, even within one logical
administrative session.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pcae.core.hatp_bootstrap import (
    HATPTrustStoreSymlinkError,
    PrincipalRecord,
    REGISTRY_SCHEMA_VERSION,
    SignerRecord,
    _parse_registry_document,
)
from pcae.core.hatp_deployment_binding_admin import (
    _atomic_write_registry,
    _deployment_binding_transition_lock,
    _load_raw_registry_document,
    _resolve_protected_root,
    _require_trust_store_available,
)
from pcae.core.hatp_hardware_credential_admin import (
    HardwareCredentialStoreUnavailableError,
    hardware_credential_transition_lock,
)
from pcae.core.hatp_hardware_credentials import HATPHardwareCredentialStore
from pcae.core.hatp_providers import _PRODUCTION_HARDWARE_PROVIDER_PROFILES
from pcae.core.paths import HarnessPath
from pcae.core.provenance import append_provenance_event

_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")


# ═══════════════════════════════════════════════════════════════════════════
# Errors (HPSE-REQ-034/071)
# ═══════════════════════════════════════════════════════════════════════════


class HATPPrincipalSignerAdminError(Exception):
    """Base error for principal/signer enrollment/revocation."""


class PrincipalEvidenceMalformedError(HATPPrincipalSignerAdminError):
    """`principal_id`/`election_reference` missing or not a non-empty
    string."""


class PrincipalNotFoundError(HATPPrincipalSignerAdminError):
    """`enroll_signer`/`revoke_principal` target `principal_id` has no
    `PrincipalRecord`."""


class PrincipalRevokedError(HATPPrincipalSignerAdminError):
    """`enroll_signer` target `principal_id` resolves to a `revoked`
    `PrincipalRecord` (HPSE-REQ-027)."""


class DuplicatePrincipalError(HATPPrincipalSignerAdminError):
    """`enroll_principal` found an existing, differing, or revoked
    record for this `principal_id` (mirrors `DuplicateConflictingBindingError`)."""


class SignerNotFoundError(HATPPrincipalSignerAdminError):
    """`revoke_signer` target `signer_key_id` has no `SignerRecord`."""


class DuplicateSignerError(HATPPrincipalSignerAdminError):
    """`enroll_signer` found an existing, differing, or revoked
    `SignerRecord` for this `signer_key_id`."""


class UnsupportedProviderProfileError(HATPPrincipalSignerAdminError):
    """`provider_profile` is outside the closed allowlist
    (`hatp_providers._PRODUCTION_HARDWARE_PROVIDER_PROFILES`, HPSE-REQ-020)."""


class HardwareProviderUnimplementedError(HATPPrincipalSignerAdminError):
    """HPSE-REQ-060's prerequisite unsatisfied: no working
    credential-identity implementation was used to produce the supplied
    enrollment evidence. Raised only when the caller's own evidence
    object fails this module's own minimal shape validation -- this
    module cannot itself re-derive whether a *live* provider ceremony
    actually occurred; it validates the evidence it was given."""


class HardwareCredentialNotRegisteredError(HATPPrincipalSignerAdminError):
    """HPSE-REQ-056's precondition unsatisfied at `enroll_signer` time:
    no matching `active` `HardwareCredentialRecord` was found for the
    supplied `signer_key_id`, checked live, under the continuously-held
    two-lock critical section (HHCE-REQ-037)."""


class HardwareCredentialConflictError(HATPPrincipalSignerAdminError):
    """The registered hardware credential's `provider_profile` does not
    match the signer-enrollment evidence's own `provider_profile`
    (HPSE-REQ-020's cross-check, restated at the credential boundary)."""


class ReadbackMismatchError(HATPPrincipalSignerAdminError):
    """The registry document read back immediately after an atomic write
    does not match what was written."""


# ═══════════════════════════════════════════════════════════════════════════
# Input evidence
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PrincipalEnrollmentEvidence:
    principal_id: str
    election_reference: str


@dataclass(frozen=True)
class SignerEnrollmentEvidence:
    """`signer_key_id`/`provider_profile`/`algorithm`/`public_key_hex`
    are exactly a `hatp_hardware_credential_admin.CredentialEnrollment
    Evidence`'s own identity fields (HPSE-REQ-061's equivalence) -- this
    module does not re-derive them independently; the caller supplies
    the identical values it already used (or is about to use) to call
    `register_credential()` (Surface B). `principal_id` binds this
    credential to an already-enrolled principal. `election_reference`
    is this specific signer-enrollment act's own fresh evidence
    (HPSE-REQ-042), distinct from -- and never reused across -- the
    credential-registration act's own `enrollment_reference`."""

    principal_id: str
    signer_key_id: str
    provider_profile: str
    election_reference: str


def _require_nonempty_str(value: object, *, context: str, error_type: type) -> str:
    if not isinstance(value, str) or not value:
        raise error_type(f"{context}: expected a non-empty string, got {value!r}")
    return value


def _validate_principal_evidence(evidence: PrincipalEnrollmentEvidence) -> None:
    _require_nonempty_str(evidence.principal_id, context="evidence.principal_id", error_type=PrincipalEvidenceMalformedError)
    _require_nonempty_str(
        evidence.election_reference, context="evidence.election_reference", error_type=PrincipalEvidenceMalformedError
    )


def _validate_signer_evidence(evidence: SignerEnrollmentEvidence) -> None:
    _require_nonempty_str(evidence.principal_id, context="evidence.principal_id", error_type=PrincipalEvidenceMalformedError)
    _require_nonempty_str(evidence.signer_key_id, context="evidence.signer_key_id", error_type=PrincipalEvidenceMalformedError)
    provider_profile = _require_nonempty_str(
        evidence.provider_profile, context="evidence.provider_profile", error_type=PrincipalEvidenceMalformedError
    )
    if provider_profile not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES:
        raise UnsupportedProviderProfileError(
            f"evidence.provider_profile {provider_profile!r} is outside the closed production allowlist "
            f"{_PRODUCTION_HARDWARE_PROVIDER_PROFILES}"
        )
    _require_nonempty_str(
        evidence.election_reference, context="evidence.election_reference", error_type=PrincipalEvidenceMalformedError
    )


# ═══════════════════════════════════════════════════════════════════════════
# Outcome model
# ═══════════════════════════════════════════════════════════════════════════


class PrincipalOutcome(str, Enum):
    ENROLLED = "enrolled"
    ALREADY_ENROLLED = "already_enrolled"
    REVOKED = "revoked"
    ALREADY_REVOKED = "already_revoked"


@dataclass(frozen=True)
class PrincipalOperationResult:
    outcome: PrincipalOutcome
    record: PrincipalRecord
    previous_record: Optional[PrincipalRecord]


class SignerOutcome(str, Enum):
    ENROLLED = "enrolled"
    ALREADY_ENROLLED = "already_enrolled"
    REVOKED = "revoked"
    ALREADY_REVOKED = "already_revoked"


@dataclass(frozen=True)
class SignerOperationResult:
    outcome: SignerOutcome
    record: SignerRecord
    previous_record: Optional[SignerRecord]


class PrincipalPreviewKind(str, Enum):
    WOULD_ENROLL = "would_enroll"
    WOULD_NOOP_ALREADY_ENROLLED = "would_noop_already_enrolled"
    WOULD_CONFLICT = "would_conflict"
    WOULD_REVOKE = "would_revoke"
    WOULD_NOOP_ALREADY_REVOKED = "would_noop_already_revoked"
    WOULD_FAIL_NOT_FOUND = "would_fail_not_found"


@dataclass(frozen=True)
class PrincipalPreview:
    kind: PrincipalPreviewKind
    principal_id: str
    existing_record: Optional[PrincipalRecord]


class SignerPreviewKind(str, Enum):
    WOULD_ENROLL = "would_enroll"
    WOULD_NOOP_ALREADY_ENROLLED = "would_noop_already_enrolled"
    WOULD_CONFLICT = "would_conflict"
    WOULD_FAIL_PRINCIPAL_NOT_FOUND = "would_fail_principal_not_found"
    WOULD_FAIL_PRINCIPAL_REVOKED = "would_fail_principal_revoked"
    #: v1.1 note (HPSE-REQ-030): "would-enroll but no matching hardware
    #: credential registered" is its own distinct preview outcome, never
    #: silently folded into a generic conflict classification.
    WOULD_FAIL_CREDENTIAL_NOT_REGISTERED = "would_fail_credential_not_registered"
    WOULD_FAIL_CREDENTIAL_PROVIDER_MISMATCH = "would_fail_credential_provider_mismatch"
    WOULD_REVOKE = "would_revoke"
    WOULD_NOOP_ALREADY_REVOKED = "would_noop_already_revoked"
    WOULD_FAIL_NOT_FOUND = "would_fail_not_found"


@dataclass(frozen=True)
class SignerPreview:
    kind: SignerPreviewKind
    signer_key_id: str
    existing_record: Optional[SignerRecord]


# ═══════════════════════════════════════════════════════════════════════════
# Canonical clock -- duplicated per this codebase's existing narrow-
# duplication convention.
# ═══════════════════════════════════════════════════════════════════════════


def _canonical_timestamp_now() -> str:
    moment = datetime.now(timezone.utc)
    value = moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    assert _TIMESTAMP_PATTERN.fullmatch(value), f"generated timestamp failed its own strict grammar: {value!r}"
    return value


# ═══════════════════════════════════════════════════════════════════════════
# registry.json <-> PrincipalRecord/SignerRecord document helpers
# (HPSE-REQ-023/024: preserve every other top-level section and every
# other record byte-for-byte; sort by key field).
# ═══════════════════════════════════════════════════════════════════════════


def _principal_to_document(record: PrincipalRecord) -> dict:
    return {"principal_id": record.principal_id, "status": record.status, "revoked_at": record.revoked_at}


def _signer_to_document(record: SignerRecord) -> dict:
    return {
        "signer_key_id": record.signer_key_id,
        "principal_id": record.principal_id,
        "provider_profile": record.provider_profile,
        "status": record.status,
        "revoked_at": record.revoked_at,
    }


def _registry_document_with_principal(raw_document: Optional[dict], record: PrincipalRecord) -> dict:
    base = dict(raw_document) if raw_document is not None else {"registry_version": REGISTRY_SCHEMA_VERSION}
    existing = [
        entry
        for entry in (base.get("principals") or [])
        if not (isinstance(entry, dict) and entry.get("principal_id") == record.principal_id)
    ]
    new_principals = existing + [_principal_to_document(record)]
    new_principals.sort(key=lambda entry: entry["principal_id"])
    updated = dict(base)
    updated["principals"] = new_principals
    return updated


def _registry_document_with_signer(raw_document: Optional[dict], record: SignerRecord) -> dict:
    base = dict(raw_document) if raw_document is not None else {"registry_version": REGISTRY_SCHEMA_VERSION}
    existing = [
        entry
        for entry in (base.get("signers") or [])
        if not (isinstance(entry, dict) and entry.get("signer_key_id") == record.signer_key_id)
    ]
    new_signers = existing + [_signer_to_document(record)]
    new_signers.sort(key=lambda entry: entry["signer_key_id"])
    updated = dict(base)
    updated["signers"] = new_signers
    return updated


def _read_back_principal(store_root: Path, expected: PrincipalRecord) -> PrincipalRecord:
    raw = _load_raw_registry_document(store_root)
    if raw is None:
        raise ReadbackMismatchError(f"registry.json missing immediately after write for principal_id={expected.principal_id!r}")
    parsed = _parse_registry_document(raw)
    persisted = parsed.principals.get(expected.principal_id)
    if persisted != expected:
        raise ReadbackMismatchError(
            f"registry.json read-back for principal_id={expected.principal_id!r} does not match the intended "
            f"write: persisted={persisted!r} expected={expected!r}"
        )
    return persisted


def _read_back_signer(store_root: Path, expected: SignerRecord) -> SignerRecord:
    raw = _load_raw_registry_document(store_root)
    if raw is None:
        raise ReadbackMismatchError(f"registry.json missing immediately after write for signer_key_id={expected.signer_key_id!r}")
    parsed = _parse_registry_document(raw)
    persisted = parsed.signers.get(expected.signer_key_id)
    if persisted != expected:
        raise ReadbackMismatchError(
            f"registry.json read-back for signer_key_id={expected.signer_key_id!r} does not match the intended "
            f"write: persisted={persisted!r} expected={expected!r}"
        )
    return persisted


def _audit(*, repository_root: Path, event_type: str, summary: str, principal_id: str) -> None:
    append_provenance_event(
        HarnessPath(repository_root),
        event_type,
        summary,
        agent_id=f"admin:{principal_id}",
    )


# ═══════════════════════════════════════════════════════════════════════════
# PRINCIPAL enrollment / revocation (HPSE-REQ-026/030)
# ═══════════════════════════════════════════════════════════════════════════


def enroll_principal(
    *, repository_root: Path, evidence: PrincipalEnrollmentEvidence, _protected_root: Optional[Path] = None
) -> PrincipalOperationResult:
    """Idempotent for the identical `principal_id` (`status == "active"`,
    `revoked_at is None`) -- there is only one authority-bearing field
    (`status`) besides the key, so idempotency reduces to "already
    active." Fails closed against a revoked principal (never
    reactivates -- `revoke_principal` is monotonic, HPSE-REQ-006)."""

    _validate_principal_evidence(evidence)
    candidate = PrincipalRecord(principal_id=evidence.principal_id, status="active", revoked_at=None)

    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    with _deployment_binding_transition_lock(store_root):
        raw_document = _load_raw_registry_document(store_root)
        parsed = _parse_registry_document(raw_document) if raw_document is not None else None
        existing = parsed.principals.get(evidence.principal_id) if parsed is not None else None

        if existing is not None:
            if existing.status == "revoked":
                raise DuplicatePrincipalError(
                    f"principal_id={evidence.principal_id!r} already has a revoked PrincipalRecord; "
                    "enroll_principal() never reactivates a revoked principal"
                )
            already_enrolled = True
            persisted = existing
        else:
            already_enrolled = False
            new_document = _registry_document_with_principal(raw_document, candidate)
            _parse_registry_document(new_document)
            _atomic_write_registry(store_root, new_document)
            persisted = _read_back_principal(store_root, candidate)

    if already_enrolled:
        _audit(
            repository_root=repository_root,
            event_type="principal_enroll_noop",
            summary=f"enroll_principal: already_enrolled principal_id={evidence.principal_id} election_reference={evidence.election_reference}",
            principal_id=evidence.principal_id,
        )
        return PrincipalOperationResult(outcome=PrincipalOutcome.ALREADY_ENROLLED, record=persisted, previous_record=persisted)

    _audit(
        repository_root=repository_root,
        event_type="principal_enrolled",
        summary=f"enroll_principal: enrolled principal_id={evidence.principal_id} election_reference={evidence.election_reference}",
        principal_id=evidence.principal_id,
    )
    return PrincipalOperationResult(outcome=PrincipalOutcome.ENROLLED, record=persisted, previous_record=None)


def revoke_principal(
    *, repository_root: Path, principal_id: str, election_reference: str, _protected_root: Optional[Path] = None
) -> PrincipalOperationResult:
    _require_nonempty_str(election_reference, context="election_reference", error_type=PrincipalEvidenceMalformedError)
    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    with _deployment_binding_transition_lock(store_root):
        raw_document = _load_raw_registry_document(store_root)
        parsed = _parse_registry_document(raw_document) if raw_document is not None else None
        existing = parsed.principals.get(principal_id) if parsed is not None else None

        if existing is None:
            raise PrincipalNotFoundError(f"no PrincipalRecord exists for principal_id={principal_id!r}")

        if existing.status == "revoked":
            outcome_record = existing
            already_revoked = True
        else:
            revoked = replace(existing, status="revoked", revoked_at=_canonical_timestamp_now())
            new_document = _registry_document_with_principal(raw_document, revoked)
            _parse_registry_document(new_document)
            _atomic_write_registry(store_root, new_document)
            outcome_record = _read_back_principal(store_root, revoked)
            already_revoked = False

    if already_revoked:
        _audit(
            repository_root=repository_root,
            event_type="principal_revoke_noop",
            summary=f"revoke_principal: already_revoked principal_id={principal_id} revoked_at={existing.revoked_at} election_reference={election_reference}",
            principal_id=principal_id,
        )
        return PrincipalOperationResult(outcome=PrincipalOutcome.ALREADY_REVOKED, record=existing, previous_record=existing)

    _audit(
        repository_root=repository_root,
        event_type="principal_revoked",
        summary=f"revoke_principal: revoked principal_id={principal_id} revoked_at={outcome_record.revoked_at} election_reference={election_reference}",
        principal_id=principal_id,
    )
    return PrincipalOperationResult(outcome=PrincipalOutcome.REVOKED, record=outcome_record, previous_record=existing)


def preview_enroll_principal(
    *, evidence: PrincipalEnrollmentEvidence, _protected_root: Optional[Path] = None
) -> PrincipalPreview:
    _validate_principal_evidence(evidence)
    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)
    raw_document = _load_raw_registry_document(store_root)
    parsed = _parse_registry_document(raw_document) if raw_document is not None else None
    existing = parsed.principals.get(evidence.principal_id) if parsed is not None else None
    if existing is None:
        kind = PrincipalPreviewKind.WOULD_ENROLL
    elif existing.status == "revoked":
        kind = PrincipalPreviewKind.WOULD_CONFLICT
    else:
        kind = PrincipalPreviewKind.WOULD_NOOP_ALREADY_ENROLLED
    return PrincipalPreview(kind=kind, principal_id=evidence.principal_id, existing_record=existing)


def preview_revoke_principal(*, principal_id: str, _protected_root: Optional[Path] = None) -> PrincipalPreview:
    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)
    raw_document = _load_raw_registry_document(store_root)
    parsed = _parse_registry_document(raw_document) if raw_document is not None else None
    existing = parsed.principals.get(principal_id) if parsed is not None else None
    if existing is None:
        kind = PrincipalPreviewKind.WOULD_FAIL_NOT_FOUND
    elif existing.status == "revoked":
        kind = PrincipalPreviewKind.WOULD_NOOP_ALREADY_REVOKED
    else:
        kind = PrincipalPreviewKind.WOULD_REVOKE
    return PrincipalPreview(kind=kind, principal_id=principal_id, existing_record=existing)


# ═══════════════════════════════════════════════════════════════════════════
# Shared cross-registry precondition check (HPSE-REQ-056), read under the
# continuously-held two-lock critical section by `enroll_signer`, and
# read lock-free (informational only) by preview.
# ═══════════════════════════════════════════════════════════════════════════


def _resolve_active_credential_or_none(hw_store_root: Path, signer_key_id: str):
    hw_store = HATPHardwareCredentialStore(_test_only_root=hw_store_root)
    record = hw_store.lookup_credential(signer_key_id)
    if record is None or record.status != "active":
        return None
    return record


def _resolve_hardware_credential_store_root(_hardware_store_root: Optional[Path]) -> Path:
    if _hardware_store_root is not None:
        return _hardware_store_root
    return HATPHardwareCredentialStore.production().root


def _require_hardware_store_available(store_root: Path) -> None:
    if store_root.is_symlink():
        raise HATPTrustStoreSymlinkError(f"hardware-credential-store root is a symlink, refusing: {store_root}")
    if not store_root.exists():
        raise HardwareCredentialStoreUnavailableError(
            f"hardware-credential-store root does not exist: {store_root}; enroll_signer never provisions it"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SIGNER enrollment (HPSE-REQ-027/029/056/057/058, HHCE-REQ-036/037 --
# the load-bearing continuous two-lock critical section)
# ═══════════════════════════════════════════════════════════════════════════


def enroll_signer(
    *,
    repository_root: Path,
    evidence: SignerEnrollmentEvidence,
    _protected_root: Optional[Path] = None,
    _hardware_store_root: Optional[Path] = None,
) -> SignerOperationResult:
    """Requires (a) an existing, `active` `PrincipalRecord` for
    `evidence.principal_id` (HPSE-REQ-027), and (b) a durable, `active`
    `HardwareCredentialRecord` for `evidence.signer_key_id` whose
    `provider_profile` matches (HPSE-REQ-056/020) -- both checked live,
    under BOTH locks held continuously (HHCE-REQ-037), immediately
    before the signer write. `signer_key_id` is never independently
    invented by this function: it is exactly `evidence.signer_key_id`,
    which the caller obtained from a provider's own enrollment ceremony
    (HPSE-REQ-010) and already registered via Surface B."""

    _validate_signer_evidence(evidence)

    hw_store_root = _resolve_hardware_credential_store_root(_hardware_store_root)
    binding_store_root = _resolve_protected_root(_protected_root)

    # HPSE-REQ-057: hardware-credential-store lock OUTER, then
    # `.deployment-binding-transition.lock` INNER. Nested `with`
    # statements, never sequential acquire/release -- HHCE-REQ-037
    # requires both held continuously across the entire critical section
    # below (precondition check -> validation -> write -> read-back ->
    # outcome classification). No code path releases the outer lock
    # before the inner lock is released, and no code path re-acquires
    # either lock mid-operation.
    with hardware_credential_transition_lock(hw_store_root):
        _require_hardware_store_available(hw_store_root)
        credential = _resolve_active_credential_or_none(hw_store_root, evidence.signer_key_id)

        with _deployment_binding_transition_lock(binding_store_root):
            _require_trust_store_available(binding_store_root)

            raw_document = _load_raw_registry_document(binding_store_root)
            parsed = _parse_registry_document(raw_document) if raw_document is not None else None

            principal = parsed.principals.get(evidence.principal_id) if parsed is not None else None
            if principal is None:
                raise PrincipalNotFoundError(f"no PrincipalRecord exists for principal_id={evidence.principal_id!r}")
            if principal.status != "active":
                raise PrincipalRevokedError(f"principal_id={evidence.principal_id!r} is not active")

            # HPSE-REQ-056 precondition, re-checked here (inside both
            # locks, immediately before the write) -- not trusted from
            # the outer-lock-scope read above alone, though in this
            # single-process implementation the value cannot itself
            # change between the two reads; this second reference keeps
            # the precondition check textually adjacent to the write it
            # gates, matching HHCE-REQ-037's own framing.
            if credential is None:
                raise HardwareCredentialNotRegisteredError(
                    f"no active HardwareCredentialRecord exists for signer_key_id={evidence.signer_key_id!r}; "
                    "enroll_signer() requires hardware credential registration (Surface B) before signer enrollment"
                )
            if credential.provider_profile != evidence.provider_profile:
                raise HardwareCredentialConflictError(
                    f"signer_key_id={evidence.signer_key_id!r}: registered credential provider_profile="
                    f"{credential.provider_profile!r} does not match evidence.provider_profile={evidence.provider_profile!r}"
                )

            existing_signer = parsed.signers.get(evidence.signer_key_id) if parsed is not None else None
            candidate = SignerRecord(
                signer_key_id=evidence.signer_key_id,
                principal_id=evidence.principal_id,
                provider_profile=evidence.provider_profile,
                status="active",
                revoked_at=None,
            )

            if existing_signer is not None:
                if existing_signer.status == "revoked":
                    raise DuplicateSignerError(
                        f"signer_key_id={evidence.signer_key_id!r} already has a revoked SignerRecord; "
                        "enroll_signer() never reactivates a revoked signer"
                    )
                if (
                    existing_signer.principal_id != candidate.principal_id
                    or existing_signer.provider_profile != candidate.provider_profile
                ):
                    raise DuplicateSignerError(
                        f"signer_key_id={evidence.signer_key_id!r} already has an active SignerRecord with "
                        "differing principal_id/provider_profile; enroll_signer() refuses to overwrite"
                    )
                already_enrolled = True
                persisted = existing_signer
            else:
                already_enrolled = False
                new_document = _registry_document_with_signer(raw_document, candidate)
                _parse_registry_document(new_document)
                _atomic_write_registry(binding_store_root, new_document)
                persisted = _read_back_signer(binding_store_root, candidate)

                # Cross-registry post-write verification (governing
                # prompt §22): reload both stores under the still-held
                # critical section and re-derive the invariant, rather
                # than trusting the writer-local assumption that
                # `credential` (read at the top of this function) is
                # still what `hardware-credentials.json` durably holds.
                reverified_credential = _resolve_active_credential_or_none(hw_store_root, evidence.signer_key_id)
                if reverified_credential is None or reverified_credential.provider_profile != persisted.provider_profile:
                    raise HardwareCredentialNotRegisteredError(
                        f"post-write cross-registry re-verification failed for signer_key_id={evidence.signer_key_id!r}: "
                        "hardware credential no longer active/matching immediately after signer write"
                    )
                if persisted.status != "active" or persisted.principal_id != evidence.principal_id:
                    raise ReadbackMismatchError(
                        f"post-write cross-registry re-verification failed for signer_key_id={evidence.signer_key_id!r}: "
                        f"persisted SignerRecord does not reflect the intended enrollment: {persisted!r}"
                    )

    if already_enrolled:
        _audit(
            repository_root=repository_root,
            event_type="signer_enroll_noop",
            summary=(
                f"enroll_signer: already_enrolled signer_key_id={evidence.signer_key_id} "
                f"principal_id={evidence.principal_id} election_reference={evidence.election_reference}"
            ),
            principal_id=evidence.principal_id,
        )
        return SignerOperationResult(outcome=SignerOutcome.ALREADY_ENROLLED, record=persisted, previous_record=persisted)

    _audit(
        repository_root=repository_root,
        event_type="signer_enrolled",
        summary=(
            f"enroll_signer: enrolled signer_key_id={evidence.signer_key_id} principal_id={evidence.principal_id} "
            f"provider_profile={evidence.provider_profile} election_reference={evidence.election_reference}"
        ),
        principal_id=evidence.principal_id,
    )
    return SignerOperationResult(outcome=SignerOutcome.ENROLLED, record=persisted, previous_record=None)


def revoke_signer(
    *, repository_root: Path, signer_key_id: str, election_reference: str, _protected_root: Optional[Path] = None
) -> SignerOperationResult:
    """Single-lock operation (HHCE-REQ-038's own binding is `enroll_
    signer`-specific): revocation touches only `registry.json`, so this
    function acquires only `.deployment-binding-transition.lock`. Never
    automatically revokes the referencing hardware credential
    (mirrors HHCE-REQ-043's symmetric no-cascade disposition) -- live
    verification-time re-checking of `SignerRecord.status` (already
    implemented, `human_approval_trusted_provenance.py`) is the
    security-relevant checkpoint."""

    _require_nonempty_str(election_reference, context="election_reference", error_type=PrincipalEvidenceMalformedError)
    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    with _deployment_binding_transition_lock(store_root):
        raw_document = _load_raw_registry_document(store_root)
        parsed = _parse_registry_document(raw_document) if raw_document is not None else None
        existing = parsed.signers.get(signer_key_id) if parsed is not None else None

        if existing is None:
            raise SignerNotFoundError(f"no SignerRecord exists for signer_key_id={signer_key_id!r}")

        if existing.status == "revoked":
            outcome_record = existing
            already_revoked = True
        else:
            revoked = replace(existing, status="revoked", revoked_at=_canonical_timestamp_now())
            new_document = _registry_document_with_signer(raw_document, revoked)
            _parse_registry_document(new_document)
            _atomic_write_registry(store_root, new_document)
            outcome_record = _read_back_signer(store_root, revoked)
            already_revoked = False

    if already_revoked:
        _audit(
            repository_root=repository_root,
            event_type="signer_revoke_noop",
            summary=f"revoke_signer: already_revoked signer_key_id={signer_key_id} revoked_at={existing.revoked_at} election_reference={election_reference}",
            principal_id=existing.principal_id,
        )
        return SignerOperationResult(outcome=SignerOutcome.ALREADY_REVOKED, record=existing, previous_record=existing)

    _audit(
        repository_root=repository_root,
        event_type="signer_revoked",
        summary=f"revoke_signer: revoked signer_key_id={signer_key_id} revoked_at={outcome_record.revoked_at} election_reference={election_reference}",
        principal_id=existing.principal_id,
    )
    return SignerOperationResult(outcome=SignerOutcome.REVOKED, record=outcome_record, previous_record=existing)


def preview_enroll_signer(
    *,
    evidence: SignerEnrollmentEvidence,
    _protected_root: Optional[Path] = None,
    _hardware_store_root: Optional[Path] = None,
) -> SignerPreview:
    """Read-only. Never acquires either transition lock, never writes --
    a best-effort point-in-time snapshot (HPSE-REQ-030), subject to the
    identical TOCTOU caveat every preview function in this codebase
    already carries relative to its own mutating counterpart."""

    _validate_signer_evidence(evidence)
    hw_store_root = _resolve_hardware_credential_store_root(_hardware_store_root)
    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    raw_document = _load_raw_registry_document(store_root)
    parsed = _parse_registry_document(raw_document) if raw_document is not None else None
    principal = parsed.principals.get(evidence.principal_id) if parsed is not None else None
    existing_signer = parsed.signers.get(evidence.signer_key_id) if parsed is not None else None

    if principal is None:
        return SignerPreview(kind=SignerPreviewKind.WOULD_FAIL_PRINCIPAL_NOT_FOUND, signer_key_id=evidence.signer_key_id, existing_record=existing_signer)
    if principal.status != "active":
        return SignerPreview(kind=SignerPreviewKind.WOULD_FAIL_PRINCIPAL_REVOKED, signer_key_id=evidence.signer_key_id, existing_record=existing_signer)

    try:
        _require_hardware_store_available(hw_store_root)
    except HardwareCredentialStoreUnavailableError:
        return SignerPreview(
            kind=SignerPreviewKind.WOULD_FAIL_CREDENTIAL_NOT_REGISTERED, signer_key_id=evidence.signer_key_id, existing_record=existing_signer
        )
    credential = _resolve_active_credential_or_none(hw_store_root, evidence.signer_key_id)
    if credential is None:
        return SignerPreview(
            kind=SignerPreviewKind.WOULD_FAIL_CREDENTIAL_NOT_REGISTERED, signer_key_id=evidence.signer_key_id, existing_record=existing_signer
        )
    if credential.provider_profile != evidence.provider_profile:
        return SignerPreview(
            kind=SignerPreviewKind.WOULD_FAIL_CREDENTIAL_PROVIDER_MISMATCH, signer_key_id=evidence.signer_key_id, existing_record=existing_signer
        )

    if existing_signer is None:
        kind = SignerPreviewKind.WOULD_ENROLL
    elif existing_signer.status == "revoked":
        kind = SignerPreviewKind.WOULD_CONFLICT
    elif existing_signer.principal_id == evidence.principal_id and existing_signer.provider_profile == evidence.provider_profile:
        kind = SignerPreviewKind.WOULD_NOOP_ALREADY_ENROLLED
    else:
        kind = SignerPreviewKind.WOULD_CONFLICT

    return SignerPreview(kind=kind, signer_key_id=evidence.signer_key_id, existing_record=existing_signer)


def preview_revoke_signer(*, signer_key_id: str, _protected_root: Optional[Path] = None) -> SignerPreview:
    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)
    raw_document = _load_raw_registry_document(store_root)
    parsed = _parse_registry_document(raw_document) if raw_document is not None else None
    existing = parsed.signers.get(signer_key_id) if parsed is not None else None
    if existing is None:
        kind = SignerPreviewKind.WOULD_FAIL_NOT_FOUND
    elif existing.status == "revoked":
        kind = SignerPreviewKind.WOULD_NOOP_ALREADY_REVOKED
    else:
        kind = SignerPreviewKind.WOULD_REVOKE
    return SignerPreview(kind=kind, signer_key_id=signer_key_id, existing_record=existing)
