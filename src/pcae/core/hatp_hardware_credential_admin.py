"""HHCE-001 Writer — Hardware Credential Registry Administration. Phase
149O.20L.7O.2F (Surface B), implementing
`docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` §11-§20
(HHCE-REQ-015..049).

Sibling module to `hatp_hardware_credentials.py`, mirroring the
`DeploymentBinding` producer module's own relationship to
`hatp_bootstrap.py`: the read-only registry/schema module
(`hatp_hardware_credentials.py`) stays byte-unchanged in its own public
read API by this module's addition (its schema *was* widened this same
phase, per HHCE-REQ-008, but `HATPHardwareCredentialStore` itself gains
no write method here — `test_credential_store_has_no_enroll_revoke_or_
rotate_method` remains true). Every mutation goes through this module's
own, separately locked, atomic writer primitives.

Never imported by `cli.py`, `commands/agent.py`, `core/agent.py`, or any
other agent-reachable code path (HHCE-REQ-019/020). The intended caller
is `scripts/hatp_hardware_credential_admin.py`, a standalone,
non-agent-writable script invoked by an operator running under the
Class-B Protected Administrator OS principal.

This module accepts already-resolved enrollment evidence
(`CredentialEnrollmentEvidence`) from its caller — typically the output
of a hardware provider's own enrollment ceremony (Surface A,
`Fido2HardwareProvider.enroll_credential()`), translated by the caller
into this module's protocol-neutral input shape. This module never
itself calls a hardware provider, never itself performs device I/O, and
never launches a decision session (HHCE-REQ-049's `enrollment_reference`
disposition mirrors `AuthorityEvidence.election_reference` exactly:
audit metadata only, never cryptographically verified here).

Locking (HHCE-REQ-031..038): a new, distinct `.hardware-credential-
transition.lock`, fixed name directly under `HATPHardwareCredentialStore.
production().root`, `fcntl.flock`-based, mirroring `hatp_deployment_
binding_admin.py::_deployment_binding_transition_lock` exactly. This
module's own two operations (`register_credential`/`revoke_credential`)
each acquire only this one lock for their entire read-check-write-verify
sequence (HHCE-REQ-038) — they never themselves acquire `.deployment-
binding-transition.lock`. `_hardware_credential_transition_lock` is
exported (not underscore-hidden from cross-module import, mirroring this
codebase's existing convention of sibling modules importing each other's
"private" helpers directly) specifically so `hatp_principal_signer_admin.
py`'s `enroll_signer` (Surface C) can acquire it as the fixed *outer*
lock in HPSE-REQ-057's global two-lock ordering, then acquire
`.deployment-binding-transition.lock` as the *inner* lock, holding both
continuously across its own check→write critical section (HHCE-REQ-037).

Atomicity (HHCE-REQ-026..030): reuses `repository_identity.py::_write_
atomic`'s exact idiom, applied to `hardware-credentials.json` — no new
idiom invented. This module never creates the hardware-credential-store
root itself (HHCE-REQ-030): its existence is a strict precondition.

Audit ordering (HHCE-REQ-047/048): validate → mutate the registry
atomically under the lock → read back and verify → emit audit record →
return. An audit-emission failure occurring *after* a successful,
read-back-verified write propagates uncaught — the identical disclosed
limitation the `DeploymentBinding` producer module/HPSE-REQ-039 already carry,
not resolved here.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional

from pcae.core.hatp_hardware_credentials import (
    HardwareCredentialRecord,
    HATPHardwareCredentialStore,
    HATPHardwareCredentialStoreMalformedError,
    HATPHardwareCredentialStoreSymlinkError,
    REGISTRY_SCHEMA_VERSION,
    _parse_credential_registry_document,
    _PROTOCOL_VALUES,
    _reject_symlink as _reject_credential_symlink,
)
from pcae.core.paths import HarnessPath
from pcae.core.provenance import append_provenance_event

_REGISTRY_FILE_NAME = "hardware-credentials.json"
_HARDWARE_CREDENTIAL_TRANSITION_LOCK_FILE_NAME = ".hardware-credential-transition.lock"

_COMPARED_CREDENTIAL_FIELDS = ("provider_profile", "protocol_name", "algorithm", "public_key_hex")


# ═══════════════════════════════════════════════════════════════════════════
# Errors -- HHCE-REQ-045/046, a distinct hierarchy from
# `HATPHardwareCredentialStoreError` (read-path), though that hierarchy
# is allowed to propagate uncaught where it already represents the
# correct fail-closed outcome (e.g. malformed/symlinked registry).
# ═══════════════════════════════════════════════════════════════════════════


class HATPHardwareCredentialAdminError(Exception):
    """Base error for hardware credential registration/revocation."""


class CredentialEvidenceMalformedError(HATPHardwareCredentialAdminError):
    """One of `signer_key_id`/`provider_profile`/`protocol_name`/
    `algorithm`/`public_key_hex` is missing, not a non-empty string, or
    (for `public_key_hex`) not valid hex."""


class CredentialEvidenceMissingError(HATPHardwareCredentialAdminError):
    """`enrollment_reference` is missing or not a non-empty string
    (HHCE-REQ-049): explicit evidence of a fresh, separate human election
    is required before any write."""


class HardwareCredentialStoreUnavailableError(HATPHardwareCredentialAdminError):
    """The hardware-credential-store root does not exist, is not a
    directory, or is a symlink. Never auto-provisioned by this module
    (HHCE-REQ-030)."""


class CredentialConflictError(HATPHardwareCredentialAdminError):
    """`register_credential` found an existing `active` record for this
    `signer_key_id` whose fields differ from the candidate (HHCE-REQ-017),
    or found an existing *revoked* record (register never reactivates —
    mirrors `create_deployment_binding`'s identical disposition)."""


class CredentialNotFoundError(HATPHardwareCredentialAdminError):
    """`revoke_credential` found no existing record for this
    `signer_key_id`. Fail closed; revocation never creates a tombstone."""


class CredentialReadbackMismatchError(HATPHardwareCredentialAdminError):
    """The registry document read back immediately after an atomic write
    does not match what was written (HHCE-REQ-027/READBACK_MISMATCH).
    Success is never reported on a rename alone."""


# ═══════════════════════════════════════════════════════════════════════════
# Enrollment evidence input (HHCE-REQ-012/049) -- protocol-neutral: this
# module never itself constructs a `Fido2HardwareProvider`/`PivHardware
# Provider` or calls a provider method. Callers (a future admin script,
# or `enroll_signer` in `hatp_principal_signer_admin.py`) translate a
# provider's own enrollment-ceremony output into this shape.
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CredentialEnrollmentEvidence:
    signer_key_id: str
    provider_profile: str
    protocol_name: str
    algorithm: str
    public_key_hex: str
    enrollment_reference: str


def _require_nonempty_str(value: object, *, context: str, error_type: type) -> str:
    if not isinstance(value, str) or not value:
        raise error_type(f"{context}: expected a non-empty string, got {value!r}")
    return value


def _validate_enrollment_evidence(evidence: CredentialEnrollmentEvidence) -> None:
    _require_nonempty_str(evidence.signer_key_id, context="evidence.signer_key_id", error_type=CredentialEvidenceMalformedError)
    _require_nonempty_str(evidence.provider_profile, context="evidence.provider_profile", error_type=CredentialEvidenceMalformedError)
    protocol_name = _require_nonempty_str(
        evidence.protocol_name, context="evidence.protocol_name", error_type=CredentialEvidenceMalformedError
    )
    if protocol_name not in _PROTOCOL_VALUES:
        raise CredentialEvidenceMalformedError(
            f"evidence.protocol_name must be one of {sorted(_PROTOCOL_VALUES)}, got {protocol_name!r}"
        )
    _require_nonempty_str(evidence.algorithm, context="evidence.algorithm", error_type=CredentialEvidenceMalformedError)
    public_key_hex = _require_nonempty_str(
        evidence.public_key_hex, context="evidence.public_key_hex", error_type=CredentialEvidenceMalformedError
    )
    try:
        bytes.fromhex(public_key_hex)
    except ValueError as exc:
        raise CredentialEvidenceMalformedError(f"evidence.public_key_hex must be valid hex: {exc}") from exc
    _require_nonempty_str(
        evidence.enrollment_reference, context="evidence.enrollment_reference", error_type=CredentialEvidenceMissingError
    )


# ═══════════════════════════════════════════════════════════════════════════
# Outcome model
# ═══════════════════════════════════════════════════════════════════════════


class HardwareCredentialOutcome(str, Enum):
    REGISTERED = "registered"
    ALREADY_REGISTERED = "already_registered"
    REVOKED = "revoked"
    ALREADY_REVOKED = "already_revoked"


@dataclass(frozen=True)
class HardwareCredentialOperationResult:
    outcome: HardwareCredentialOutcome
    record: HardwareCredentialRecord
    previous_record: Optional[HardwareCredentialRecord]


class HardwareCredentialPreviewKind(str, Enum):
    WOULD_REGISTER = "would_register"
    WOULD_NOOP_ALREADY_REGISTERED = "would_noop_already_registered"
    WOULD_CONFLICT = "would_conflict"
    WOULD_REVOKE = "would_revoke"
    WOULD_NOOP_ALREADY_REVOKED = "would_noop_already_revoked"
    WOULD_FAIL_NOT_FOUND = "would_fail_not_found"


@dataclass(frozen=True)
class HardwareCredentialPreview:
    kind: HardwareCredentialPreviewKind
    signer_key_id: str
    existing_record: Optional[HardwareCredentialRecord]
    candidate_record: Optional[HardwareCredentialRecord]
    registry_path: Path


# ═══════════════════════════════════════════════════════════════════════════
# Canonical clock (HHCE-REQ-010) -- duplicated from `hatp_deployment_
# binding_admin.py::_canonical_timestamp_now` rather than imported,
# mirroring that module's own stated narrow-duplication rationale.
# ═══════════════════════════════════════════════════════════════════════════

_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")


def _canonical_timestamp_now() -> str:
    moment = datetime.now(timezone.utc)
    value = moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    assert _TIMESTAMP_PATTERN.fullmatch(value), f"generated timestamp failed its own strict grammar: {value!r}"
    return value


# ═══════════════════════════════════════════════════════════════════════════
# Store-root resolution (HHCE-REQ-021, mirrors `hatp_deployment_binding_
# admin.py::_resolve_protected_root` exactly).
# ═══════════════════════════════════════════════════════════════════════════


def _resolve_store_root(_store_root: Optional[Path]) -> Path:
    if _store_root is not None:
        return _store_root
    return HATPHardwareCredentialStore.production().root


def _require_store_available(store_root: Path) -> None:
    if store_root.is_symlink():
        raise HATPHardwareCredentialStoreSymlinkError(f"hardware-credential-store root is a symlink, refusing: {store_root}")
    if not store_root.exists():
        raise HardwareCredentialStoreUnavailableError(
            f"hardware-credential-store root does not exist: {store_root}; this module never provisions it"
        )
    if not store_root.is_dir():
        raise HardwareCredentialStoreUnavailableError(f"hardware-credential-store root is not a directory: {store_root}")


# ═══════════════════════════════════════════════════════════════════════════
# Registry document read/write (raw-JSON level; structural validation
# delegated to `hatp_hardware_credentials._parse_credential_registry_
# document`, the identical parser `HATPHardwareCredentialStore`'s read
# path uses -- HHCE-REQ-024's producer/consumer round-trip requirement).
# ═══════════════════════════════════════════════════════════════════════════


def _load_raw_registry_document(store_root: Path) -> Optional[dict]:
    registry_path = store_root / _REGISTRY_FILE_NAME
    _reject_credential_symlink(store_root)
    _reject_credential_symlink(registry_path)
    if not registry_path.exists():
        return None
    if not registry_path.is_file():
        raise HATPHardwareCredentialStoreMalformedError(f"registry path exists but is not a regular file: {registry_path}")
    raw = registry_path.read_text(encoding="utf-8")
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HATPHardwareCredentialStoreMalformedError(f"registry document is not valid JSON: {exc}") from exc
    return document


def _credential_to_document(record: HardwareCredentialRecord) -> dict:
    return {
        "signer_key_id": record.signer_key_id,
        "provider_profile": record.provider_profile,
        "protocol_name": record.protocol_name,
        "algorithm": record.algorithm,
        "public_key_hex": record.public_key.hex(),
        "status": record.status,
        "revoked_at": record.revoked_at,
    }


def _registry_document_with_credential(raw_document: Optional[dict], record: HardwareCredentialRecord) -> dict:
    """Preserves every other credential record byte-for-byte from
    `raw_document` unchanged; replaces only the one entry keyed by
    `record.signer_key_id` (HHCE-REQ-028), sorted by `signer_key_id`
    (HHCE-REQ-029)."""

    base = dict(raw_document) if raw_document is not None else {"schema_version": REGISTRY_SCHEMA_VERSION}
    existing_credentials = [
        entry
        for entry in (base.get("credentials") or [])
        if not (isinstance(entry, dict) and entry.get("signer_key_id") == record.signer_key_id)
    ]
    new_credentials = existing_credentials + [_credential_to_document(record)]
    new_credentials.sort(key=lambda entry: entry["signer_key_id"])
    updated = dict(base)
    updated["schema_version"] = REGISTRY_SCHEMA_VERSION
    updated["credentials"] = new_credentials
    return updated


def _atomic_write_credential_registry(store_root: Path, document: dict) -> None:
    """HHCE-REQ-026: `repository_identity.py::_write_atomic`'s exact
    idiom. Never `mkdir`s `store_root` itself."""

    registry_path = store_root / _REGISTRY_FILE_NAME
    _reject_credential_symlink(registry_path)
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-hardware-credential-", dir=str(store_root))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _reject_credential_symlink(registry_path)
        os.replace(tmp_name, registry_path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _read_back_and_verify_credential(store_root: Path, expected_record: HardwareCredentialRecord) -> HardwareCredentialRecord:
    """HHCE-REQ-027: never report success on a rename alone."""

    raw = _load_raw_registry_document(store_root)
    if raw is None:
        raise CredentialReadbackMismatchError(
            f"hardware-credentials.json is missing immediately after a write for signer_key_id={expected_record.signer_key_id!r}"
        )
    parsed = _parse_credential_registry_document(raw)
    persisted = parsed.credentials.get(expected_record.signer_key_id)
    if persisted != expected_record:
        raise CredentialReadbackMismatchError(
            f"hardware-credentials.json read-back for signer_key_id={expected_record.signer_key_id!r} "
            f"does not match the intended write: persisted={persisted!r} expected={expected_record!r}"
        )
    return persisted


# ═══════════════════════════════════════════════════════════════════════════
# Locking (HHCE-REQ-031..038). Exported (no leading underscore in the
# name callers use) specifically so `hatp_principal_signer_admin.py`
# (Surface C) can acquire this exact lock as the fixed *outer* lock in
# HPSE-REQ-057's cross-registry ordering.
# ═══════════════════════════════════════════════════════════════════════════


@contextmanager
def hardware_credential_transition_lock(store_root: Path) -> Iterator[None]:
    lock_path = store_root / _HARDWARE_CREDENTIAL_TRANSITION_LOCK_FILE_NAME
    _reject_credential_symlink(lock_path)
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


# Backwards-compatible private alias, matching this codebase's existing
# convention of a leading-underscore internal name alongside a public
# one where a sibling module needs the underscore-prefixed spelling.
_hardware_credential_transition_lock = hardware_credential_transition_lock


def _audit(*, repository_root: Path, event_type: str, summary: str, principal_id: str) -> None:
    """HHCE-REQ-047. Always the last step of a successful operation. Raises
    uncaught on failure (HHCE-REQ-048/AUDIT_INCOMPLETE's disclosed
    limitation) -- this module never silently loses authority-mutation
    evidence."""

    append_provenance_event(
        HarnessPath(repository_root),
        event_type,
        summary,
        agent_id=f"admin:{principal_id}",
    )


def _candidate_equal(existing: HardwareCredentialRecord, candidate: HardwareCredentialRecord) -> bool:
    return (
        existing.provider_profile == candidate.provider_profile
        and existing.protocol_name == candidate.protocol_name
        and existing.algorithm == candidate.algorithm
        and existing.public_key == candidate.public_key
    )


# ═══════════════════════════════════════════════════════════════════════════
# REGISTER (HHCE-REQ-015..017/026..030/047..049)
# ═══════════════════════════════════════════════════════════════════════════


def register_credential(
    *,
    repository_root: Path,
    evidence: CredentialEnrollmentEvidence,
    _store_root: Optional[Path] = None,
) -> HardwareCredentialOperationResult:
    """Registers a new `HardwareCredentialRecord`, or safely no-ops if an
    identical `active` entry already exists (HHCE-REQ-016). Fails closed
    on any conflicting existing entry, active-with-differing-fields or
    revoked (HHCE-REQ-017) -- never overwrites, never reactivates."""

    _validate_enrollment_evidence(evidence)
    candidate = HardwareCredentialRecord(
        signer_key_id=evidence.signer_key_id,
        provider_profile=evidence.provider_profile,
        protocol_name=evidence.protocol_name,
        algorithm=evidence.algorithm,
        public_key=bytes.fromhex(evidence.public_key_hex),
        status="active",
        revoked_at=None,
    )

    store_root = _resolve_store_root(_store_root)
    _require_store_available(store_root)

    with hardware_credential_transition_lock(store_root):
        raw_document = _load_raw_registry_document(store_root)
        parsed = _parse_credential_registry_document(raw_document) if raw_document is not None else None
        existing = parsed.credentials.get(evidence.signer_key_id) if parsed is not None else None

        if existing is not None:
            if existing.status == "revoked":
                raise CredentialConflictError(
                    f"signer_key_id={evidence.signer_key_id!r} already has a revoked HardwareCredentialRecord; "
                    "register_credential() never reactivates a revoked credential"
                )
            if not _candidate_equal(existing, candidate):
                raise CredentialConflictError(
                    f"signer_key_id={evidence.signer_key_id!r} already has an active HardwareCredentialRecord with "
                    "differing field values; register_credential() refuses to overwrite a conflicting entry"
                )
            already_registered = True
            persisted = existing
        else:
            already_registered = False
            new_document = _registry_document_with_credential(raw_document, candidate)
            _parse_credential_registry_document(new_document)  # full-document round-trip validation before touching disk
            _atomic_write_credential_registry(store_root, new_document)
            persisted = _read_back_and_verify_credential(store_root, candidate)

    if already_registered:
        _audit(
            repository_root=repository_root,
            event_type="hardware_credential_register_noop",
            summary=(
                f"register_credential: already_registered signer_key_id={evidence.signer_key_id} "
                f"enrollment_reference={evidence.enrollment_reference}"
            ),
            principal_id="admin",
        )
        return HardwareCredentialOperationResult(
            outcome=HardwareCredentialOutcome.ALREADY_REGISTERED, record=persisted, previous_record=persisted
        )

    _audit(
        repository_root=repository_root,
        event_type="hardware_credential_registered",
        summary=(
            f"register_credential: registered signer_key_id={evidence.signer_key_id} "
            f"provider_profile={evidence.provider_profile} protocol_name={evidence.protocol_name} "
            f"enrollment_reference={evidence.enrollment_reference}"
        ),
        principal_id="admin",
    )
    return HardwareCredentialOperationResult(outcome=HardwareCredentialOutcome.REGISTERED, record=persisted, previous_record=None)


# ═══════════════════════════════════════════════════════════════════════════
# REVOKE (HHCE-REQ-011/018/026..030/042..049)
# ═══════════════════════════════════════════════════════════════════════════


def revoke_credential(
    *,
    repository_root: Path,
    signer_key_id: str,
    enrollment_reference: str,
    _store_root: Optional[Path] = None,
) -> HardwareCredentialOperationResult:
    """`status` -> `"revoked"`, `revoked_at` set; every other field
    preserved unchanged. Fails closed if no entry exists. Idempotent
    (`ALREADY_REVOKED`, original `revoked_at` preserved, HHCE-REQ-011's
    monotonicity) if the entry is already revoked. Never automatically
    revokes a referencing `SignerRecord` (HHCE-REQ-043) -- this operation
    performs only a read-only, informational cross-registry check,
    reusing `HATPTrustStore.production().lookup_signer` without
    acquiring `.deployment-binding-transition.lock` at all (reads do not
    require the writer's own transition lock)."""

    _require_nonempty_str(
        enrollment_reference, context="enrollment_reference", error_type=CredentialEvidenceMissingError
    )
    store_root = _resolve_store_root(_store_root)
    _require_store_available(store_root)

    with hardware_credential_transition_lock(store_root):
        raw_document = _load_raw_registry_document(store_root)
        parsed = _parse_credential_registry_document(raw_document) if raw_document is not None else None
        existing = parsed.credentials.get(signer_key_id) if parsed is not None else None

        if existing is None:
            raise CredentialNotFoundError(
                f"no HardwareCredentialRecord exists for signer_key_id={signer_key_id!r}; "
                "revoke_credential() never creates a tombstone"
            )

        if existing.status == "revoked":
            outcome_record = existing
            already_revoked = True
        else:
            revoked = replace(existing, status="revoked", revoked_at=_canonical_timestamp_now())
            new_document = _registry_document_with_credential(raw_document, revoked)
            _parse_credential_registry_document(new_document)
            _atomic_write_credential_registry(store_root, new_document)
            outcome_record = _read_back_and_verify_credential(store_root, revoked)
            already_revoked = False

    referencing_signer_note = _referencing_active_signer_note(signer_key_id)

    if already_revoked:
        _audit(
            repository_root=repository_root,
            event_type="hardware_credential_revoke_noop",
            summary=(
                f"revoke_credential: already_revoked signer_key_id={signer_key_id} "
                f"revoked_at={existing.revoked_at} enrollment_reference={enrollment_reference} "
                f"{referencing_signer_note}"
            ),
            principal_id="admin",
        )
        return HardwareCredentialOperationResult(
            outcome=HardwareCredentialOutcome.ALREADY_REVOKED, record=existing, previous_record=existing
        )

    _audit(
        repository_root=repository_root,
        event_type="hardware_credential_revoked",
        summary=(
            f"revoke_credential: revoked signer_key_id={signer_key_id} revoked_at={outcome_record.revoked_at} "
            f"enrollment_reference={enrollment_reference} {referencing_signer_note}"
        ),
        principal_id="admin",
    )
    return HardwareCredentialOperationResult(outcome=HardwareCredentialOutcome.REVOKED, record=outcome_record, previous_record=existing)


def _referencing_active_signer_note(signer_key_id: str) -> str:
    """HHCE-REQ-043: informational-only, read-only cross-registry check
    -- never a write, never a lock on `.deployment-binding-transition.
    lock`. Failure to resolve the trust store (e.g. it is absent in this
    environment) is itself informative, not fatal to the revocation this
    function is only annotating."""

    try:
        from pcae.core.hatp_bootstrap import HATPTrustStore

        signer = HATPTrustStore.production().lookup_signer(signer_key_id)
    except Exception as exc:  # noqa: BLE001 -- informational only, never blocks revocation
        return f"referencing_signer_check_unavailable:{exc.__class__.__name__}"
    if signer is not None and signer.status == "active":
        return "referencing_active_signer=true"
    return "referencing_active_signer=false"


# ═══════════════════════════════════════════════════════════════════════════
# Read-only preview (HHCE-REQ-018)
# ═══════════════════════════════════════════════════════════════════════════


def preview_register_credential(
    *, evidence: CredentialEnrollmentEvidence, _store_root: Optional[Path] = None
) -> HardwareCredentialPreview:
    _validate_enrollment_evidence(evidence)
    store_root = _resolve_store_root(_store_root)
    _require_store_available(store_root)

    candidate = HardwareCredentialRecord(
        signer_key_id=evidence.signer_key_id,
        provider_profile=evidence.provider_profile,
        protocol_name=evidence.protocol_name,
        algorithm=evidence.algorithm,
        public_key=bytes.fromhex(evidence.public_key_hex),
        status="active",
        revoked_at=None,
    )
    raw_document = _load_raw_registry_document(store_root)
    parsed = _parse_credential_registry_document(raw_document) if raw_document is not None else None
    existing = parsed.credentials.get(evidence.signer_key_id) if parsed is not None else None

    if existing is None:
        kind = HardwareCredentialPreviewKind.WOULD_REGISTER
    elif existing.status == "revoked":
        kind = HardwareCredentialPreviewKind.WOULD_CONFLICT
    elif _candidate_equal(existing, candidate):
        kind = HardwareCredentialPreviewKind.WOULD_NOOP_ALREADY_REGISTERED
    else:
        kind = HardwareCredentialPreviewKind.WOULD_CONFLICT

    return HardwareCredentialPreview(
        kind=kind,
        signer_key_id=evidence.signer_key_id,
        existing_record=existing,
        candidate_record=candidate,
        registry_path=store_root / _REGISTRY_FILE_NAME,
    )


def preview_revoke_credential(*, signer_key_id: str, _store_root: Optional[Path] = None) -> HardwareCredentialPreview:
    store_root = _resolve_store_root(_store_root)
    _require_store_available(store_root)

    raw_document = _load_raw_registry_document(store_root)
    parsed = _parse_credential_registry_document(raw_document) if raw_document is not None else None
    existing = parsed.credentials.get(signer_key_id) if parsed is not None else None

    if existing is None:
        kind = HardwareCredentialPreviewKind.WOULD_FAIL_NOT_FOUND
    elif existing.status == "revoked":
        kind = HardwareCredentialPreviewKind.WOULD_NOOP_ALREADY_REVOKED
    else:
        kind = HardwareCredentialPreviewKind.WOULD_REVOKE

    return HardwareCredentialPreview(
        kind=kind,
        signer_key_id=signer_key_id,
        existing_record=existing,
        candidate_record=None,
        registry_path=store_root / _REGISTRY_FILE_NAME,
    )
