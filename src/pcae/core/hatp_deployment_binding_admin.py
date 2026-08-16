"""`DeploymentBinding` Producer, Rotation, and Revocation — Phase
149O.20L.7I, implementing HBDC-001 v1.1 §16.1 (HBDC-REQ-056..070,
`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`).

This is a **sibling module to `hatp_bootstrap.py`, deliberately kept
separate** (HBDC-REQ-056; 149O.20L.7G plan §9.1's own stated preference)
so that `hatp_bootstrap.py` — the read-only production/verification
interface every other HATP/HMIC/HBDC consumer already depends on —
remains byte-unchanged by this phase. `HATPTrustStore` still has zero
write methods; every mutation here goes through this module's own,
separately locked, atomic writer primitives.

Never imported by `cli.py`, `commands/agent.py`, `core/agent.py`, or any
other agent-reachable code path (HBDC-REQ-056/066, mirroring
`hatp_mandatory_certification.py`'s own writer-primitive boundary and
`scripts/hatp_certification_admin.py`'s module docstring exactly). The
intended caller is a future, separate, non-agent-writable admin-tool
script (`scripts/hatp_deployment_binding_admin.py`, 149O.20L.7G plan
§9.1) invoked by an operator running under the Class-B Protected
Administrator OS principal — the only principal with real write access
to `HATPTrustStore.production().root`. Real security boundary
(HBDC-REQ-066, mirroring HMIC-REQ-079/HMIC-REQ-018/HMIC-REQ-020): OS
filesystem write permission on the Protected Root, never an in-process
check. Nothing in this module establishes or substitutes for that
permission.

Producer != first-use authority (HBDC-REQ-064/069): this module accepts
already-resolved authority evidence (`AuthorityEvidence`) from its
caller — it never launches a decision session, never infers human
approval, never accepts a bare `approved=True` boolean, and never mints
its own CHGR. `AuthorityEvidence.election_reference` is recorded as
audit metadata only (HBDC-REQ-065) — this module does not itself
cryptographically verify the referenced election's authenticity, scope,
or currentness (mirrors HMIC-REQ-078's own disposition).

Schema (HBDC-REQ-057/058, unchanged from `hatp_bootstrap.DeploymentBinding`,
§4 of the 149O.20L.7G plan — this phase adds zero fields): `repository_id`
and `canonical_deployment_root` are always derived read-only by this
module (never free-form caller input); `principal_id`/`signer_key_id`/
`provider_profile`/`authority_scope` are drawn from the caller-supplied
`AuthorityEvidence` (the admin's own enrollment context) unchanged and
unvalidated against any registry vocabulary beyond non-empty-string shape
— cross-validation against `principals`/`signers` registry entries is
explicitly deferred (149O.20L.7H finding, HBDC-REQ-058: contract
silence on vocabulary cross-validation; this module preserves the exact
caller-supplied value rather than transforming or widening it).

Implementation-level conservative choices this module makes, none of
them new normative contract text (149O.20L.7H's non-blocking findings,
each carried forward and disposed of here at the implementation layer
only):

- **Idempotency comparison (HBDC-REQ-059).** `create_deployment_binding`
  compares every authority-bearing field (`canonical_deployment_root`,
  `principal_id`, `signer_key_id`, `provider_profile`,
  `authority_scope`) against an existing *active* entry for the same
  `repository_id`. `valid_from` is deliberately excluded from this
  comparison: it is producer-generated freshness metadata (`now`, at
  every call), not caller-supplied authority content, and including it
  would make idempotent-preserve semantics unreachable by construction
  (mirrors `ensure_repository_identity`'s own discipline of never
  comparing its analogous `created_at` field). An exact match on the
  compared fields is `ALREADY_SATISFIED` (no write, no fresh timestamp);
  any difference is `DuplicateConflictingBindingError` (fail closed, no
  overwrite).
- **Create against a revoked entry.** Fails closed
  (`DuplicateConflictingBindingError`) rather than silently
  reactivating — `rotate_deployment_binding` is the only path that may
  transition a `repository_id` back to `active`.
- **Rotate against a nonexistent entry.** Fails closed
  (`DeploymentBindingNotFoundError`) — rotation never silently degrades
  into creation.
- **Rotate against a revoked entry.** Fails closed
  (`DeploymentBindingRevokedError`) — rotation never resurrects revoked
  authority; the same fail-closed rule as create-against-revoked.
- **Revoke against a nonexistent entry.** Fails closed
  (`DeploymentBindingNotFoundError`) — no tombstone is created.
- **Revoke against an already-revoked entry.** Deterministic
  `ALREADY_REVOKED` idempotent result; the original `revoked_at` is
  never overwritten (preserves first-recorded revocation evidence,
  mirroring `hatp_mandatory_certification.py::_write_revocation`'s own
  "first-recorded revocation always wins" monotonic discipline).

Audit evidence (HBDC-REQ-062): every operation — including the two
idempotent no-op outcomes above — emits exactly one
`pcae.core.provenance.append_provenance_event` record against the
*target* repository's own tree (the `repository_root` every public
function here accepts as its neutral locator), reusing this repository's
one existing, generically-named provenance/audit-history mechanism
rather than introducing a bespoke one. `agent_id` is always passed
explicitly as `f"admin:{principal_id}"` — `read_agent_lock` is therefore
never invoked and this module's audit path carries no runtime dependency
on any PCAE agent-lock state. Audit ordering (HBDC-REQ-062, silent on
ordering per 149O.20L.7H; this module's own explicit choice): validate
-> mutate trust store atomically under lock -> read back and verify ->
emit audit record -> return. No operation ever reports success before
durable trust-store publication and read-back verification have both
already succeeded. If audit emission itself fails *after* a successful,
read-back-verified trust-store mutation, the exception propagates
uncaught (this module never silently swallows an audit-emission
failure) — the trust-store mutation is by then already durable and
correct; the caller must reconcile the missing audit record out of
band. This is a known, named limitation of composing two independently
atomic storage systems without a real two-phase commit, not an
oversight.

Atomicity (HBDC-REQ-063): reuses `repository_identity.py::_write_atomic`'s
exact idiom (`mkstemp` in the same directory, `fsync`, `os.replace`,
symlink rejection before and after the write) — no new idiom is
invented. One deliberate, documented deviation: unlike
`repository_identity.py::_write_atomic`, this module never
`mkdir`s the Protected Root itself — its existence is a strict
precondition (`DeploymentBindingTrustStoreUnavailableError` if absent),
never auto-provisioned here (mirrors `hatp_bootstrap.py`'s own stated
"this module never creates it" discipline for the Protected Root).

Concurrency (149O.20L.7H non-blocking finding: HBDC-001 has no
concurrency-lock requirement analogous to HMIC-REQ-097): this module
adds an internal, non-normative `fcntl.flock`-based single-writer lock
(`.deployment-binding-transition.lock`, fixed name directly under the
Protected Root, mirroring `hatp_mandatory_certification.py`'s own
`.certification-transition.lock` pattern) purely as implementation
hardening. Every read of current registry state that determines a
create/rotate/revoke outcome happens *inside* this lock's critical
section, re-read fresh from disk — never validated once outside the
lock and then blindly written (TOCTOU discipline).
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

from pcae.core.hatp_bootstrap import (
    DeploymentBinding,
    HATPTrustStore,
    HATPTrustStoreError,
    HATPTrustStoreMalformedError,
    HATPTrustStoreSymlinkError,
    REGISTRY_SCHEMA_VERSION,
    _parse_registry_document,
    resolve_canonical_deployment_root,
)
from pcae.core.paths import HarnessPath
from pcae.core.provenance import append_provenance_event
from pcae.core.repository_identity import (
    RepositoryIdentityError,
    read_repository_identity,
)

_REGISTRY_FILE_NAME = "registry.json"
_DEPLOYMENT_BINDING_TRANSITION_LOCK_FILE_NAME = ".deployment-binding-transition.lock"

#: HBDC-REQ-067's strict producer-output grammar. Identical to
#: `hatp_mandatory_cutover.py::_TIMESTAMP_PATTERN` /
#: `hatp_mandatory_certification.py::_TIMESTAMP_PATTERN`. Deliberately
#: *not* the same object as `hatp_bootstrap.py::_parse_iso_timestamp`'s
#: permissive read-path grammar (149O.20L.7G plan §8.6) — this module's
#: own output is bound to the strict grammar regardless of what the
#: current read-path parser happens to accept.
_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")

_COMPARED_AUTHORITY_FIELDS = (
    "canonical_deployment_root",
    "principal_id",
    "signer_key_id",
    "provider_profile",
    "authority_scope",
)


# ═══════════════════════════════════════════════════════════════════════════
# Errors — a distinct hierarchy from `HATPTrustStoreError` (read-path) and
# `RepositoryIdentityError`, though both are allowed to propagate
# uncaught where they already represent the correct fail-closed outcome
# (e.g. a malformed registry document, a malformed RepositoryIdentity).
# ═══════════════════════════════════════════════════════════════════════════


class HATPDeploymentBindingAdminError(Exception):
    """Base error for `DeploymentBinding` producer/rotation/revocation
    operations."""


class RepositoryIdentityMissingError(HATPDeploymentBindingAdminError):
    """No `RepositoryIdentity` exists for the target repository
    (HBDC-REQ-057/8.1 of the 149O.20L.7G plan): this module reads an
    *existing* identity — it never calls `ensure_repository_identity()`
    itself, and never silently creates one as a side effect of a binding
    operation."""


class DeploymentRootUnresolvableError(HATPDeploymentBindingAdminError):
    """`resolve_canonical_deployment_root` could not resolve the target
    repository root (e.g. the path does not exist)."""


class AuthorityEvidenceMalformedError(HATPDeploymentBindingAdminError):
    """One of `principal_id`/`signer_key_id`/`provider_profile`/
    `authority_scope` is missing or not a non-empty string
    (HBDC-REQ-058)."""


class AuthorityEvidenceMissingError(HATPDeploymentBindingAdminError):
    """`election_reference` is missing or not a non-empty string
    (HBDC-REQ-064): explicit evidence of a fresh, separate human
    election is required before any write; an unverified boolean or
    free-form "approved" string is never sufficient authority."""


class DeploymentBindingTrustStoreUnavailableError(HATPDeploymentBindingAdminError):
    """The Protected Root does not exist, is not a directory, or is a
    symlink. Never auto-provisioned by this module."""


class DuplicateConflictingBindingError(HATPDeploymentBindingAdminError):
    """`create_deployment_binding` found an existing entry for this
    `repository_id` whose authority-bearing fields differ from the
    candidate (HBDC-REQ-059), or found an existing *revoked* entry (this
    module's own conservative choice: create never reactivates a revoked
    binding). Fail closed; no overwrite."""


class DeploymentBindingNotFoundError(HATPDeploymentBindingAdminError):
    """`rotate_deployment_binding`/`revoke_deployment_binding` found no
    existing entry for this `repository_id`. Fail closed; rotation never
    degrades into creation and revocation never creates a tombstone."""


class DeploymentBindingRevokedError(HATPDeploymentBindingAdminError):
    """`rotate_deployment_binding` found an existing entry that is
    already `revoked`. Fail closed; rotation never resurrects revoked
    authority."""


class DeploymentBindingReadbackMismatchError(HATPDeploymentBindingAdminError):
    """The registry document read back immediately after an atomic write
    does not match what was written. Treated as a hard failure — success
    is never reported on a rename alone."""


# ═══════════════════════════════════════════════════════════════════════════
# Authority evidence input (HBDC-REQ-058/064/065)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class AuthorityEvidence:
    """Already-resolved authority context supplied by the caller (the
    future admin-tool entrypoint, or this phase's own tests) — this
    module neither infers nor verifies any of these fields; it only
    validates their shape and, for `principal_id`/`signer_key_id`/
    `provider_profile`/`authority_scope`, preserves the exact supplied
    value unchanged (HBDC-REQ-058). `election_reference` (HBDC-REQ-064)
    is recorded as audit metadata only (HBDC-REQ-065) — never
    cryptographically verified here."""

    principal_id: str
    signer_key_id: str
    provider_profile: str
    authority_scope: str
    election_reference: str


def _require_nonempty_str(value: object, *, context: str, error_type: type) -> str:
    if not isinstance(value, str) or not value:
        raise error_type(f"{context}: expected a non-empty string, got {value!r}")
    return value


def _validate_authority_evidence(authority: AuthorityEvidence) -> None:
    _require_nonempty_str(
        authority.principal_id, context="authority.principal_id", error_type=AuthorityEvidenceMalformedError
    )
    _require_nonempty_str(
        authority.signer_key_id, context="authority.signer_key_id", error_type=AuthorityEvidenceMalformedError
    )
    _require_nonempty_str(
        authority.provider_profile, context="authority.provider_profile", error_type=AuthorityEvidenceMalformedError
    )
    _require_nonempty_str(
        authority.authority_scope, context="authority.authority_scope", error_type=AuthorityEvidenceMalformedError
    )
    _require_nonempty_str(
        authority.election_reference,
        context="authority.election_reference",
        error_type=AuthorityEvidenceMissingError,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Result model (HBDC-REQ-056..070's producer outcome vocabulary — never
# frozen production API beyond this phase's own implementation; the
# error hierarchy above carries CONFLICT/NOT_FOUND/INVALID/FAILED
# outcomes as typed exceptions, mirroring this codebase's existing
# convention throughout `hatp_mandatory_certification.py`/
# `scripts/hatp_certification_admin.py` rather than folding every
# outcome into one enum.)
# ═══════════════════════════════════════════════════════════════════════════


class DeploymentBindingOutcome(str, Enum):
    CREATED = "created"
    ALREADY_SATISFIED = "already_satisfied"
    ROTATED = "rotated"
    REVOKED = "revoked"
    ALREADY_REVOKED = "already_revoked"


@dataclass(frozen=True)
class DeploymentBindingOperationResult:
    outcome: DeploymentBindingOutcome
    binding: DeploymentBinding
    previous_binding: Optional[DeploymentBinding]


# ═══════════════════════════════════════════════════════════════════════════
# Canonical clock (HBDC-REQ-067). Deliberately duplicated from
# `scripts/hatp_certification_admin.py::_canonical_timestamp_now` /
# `repository_identity.py::_generate_repository_identity` rather than
# imported, mirroring those modules' own stated narrow-duplication
# rationale.
# ═══════════════════════════════════════════════════════════════════════════


def _canonical_timestamp_now() -> str:
    moment = datetime.now(timezone.utc)
    value = moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    assert _TIMESTAMP_PATTERN.fullmatch(value), f"generated timestamp failed its own strict grammar: {value!r}"
    return value


# ═══════════════════════════════════════════════════════════════════════════
# Protected Root resolution (mirrors `scripts/hatp_certification_admin.py::
# _resolve_protected_root` exactly: no CLI/env override on the production
# path; `_protected_root` is a private, non-CLI, test-only seam).
# ═══════════════════════════════════════════════════════════════════════════


def _resolve_protected_root(_protected_root: Optional[Path]) -> Path:
    if _protected_root is not None:
        return _protected_root
    return HATPTrustStore.production().root


def _require_trust_store_available(store_root: Path) -> None:
    if store_root.is_symlink():
        raise HATPTrustStoreSymlinkError(f"HATP trust-store root is a symlink, refusing: {store_root}")
    if not store_root.exists():
        raise DeploymentBindingTrustStoreUnavailableError(
            f"HATP protected trust-store root does not exist: {store_root}; this module never provisions it"
        )
    if not store_root.is_dir():
        raise DeploymentBindingTrustStoreUnavailableError(
            f"HATP protected trust-store root is not a directory: {store_root}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Symlink safety (HBDC-REQ-063, mirroring `repository_identity.py::
# _reject_symlink` exactly — immediate target + immediate parent only;
# HBDC-REQ-063 explicitly cites that module's idiom, not the deeper
# whole-parent-chain walk `hatp_mandatory_certification.py` separately
# uses for its own, differently-scoped HMIC-REQ-128 requirement).
# ═══════════════════════════════════════════════════════════════════════════


def _reject_symlink(target: Path) -> None:
    if target.is_symlink():
        raise HATPTrustStoreSymlinkError(f"HATP trust-store path is a symlink, refusing: {target}")
    if target.parent.exists() and target.parent.is_symlink():
        raise HATPTrustStoreSymlinkError(f"HATP trust-store parent directory is a symlink, refusing: {target.parent}")


# ═══════════════════════════════════════════════════════════════════════════
# Registry document read/write (raw-JSON level; structural validation is
# delegated to `hatp_bootstrap._parse_registry_document`, the exact same
# parser `HATPTrustStore`'s read path already uses — HBDC-REQ item-31's
# producer/consumer round-trip requirement).
# ═══════════════════════════════════════════════════════════════════════════


def _load_raw_registry_document(store_root: Path) -> Optional[dict]:
    registry_path = store_root / _REGISTRY_FILE_NAME
    _reject_symlink(store_root)
    _reject_symlink(registry_path)
    if not registry_path.exists():
        return None
    if not registry_path.is_file():
        raise HATPTrustStoreMalformedError(f"registry path exists but is not a regular file: {registry_path}")
    raw = registry_path.read_text(encoding="utf-8")
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HATPTrustStoreMalformedError(f"registry document is not valid JSON: {exc}") from exc
    return document


def _deployment_binding_to_document(binding: DeploymentBinding) -> dict:
    return {
        "repository_id": binding.repository_id,
        "canonical_deployment_root": binding.canonical_deployment_root,
        "principal_id": binding.principal_id,
        "signer_key_id": binding.signer_key_id,
        "provider_profile": binding.provider_profile,
        "authority_scope": binding.authority_scope,
        "valid_from": binding.valid_from,
        "status": binding.status,
        "revoked_at": binding.revoked_at,
    }


def _registry_document_with_binding(raw_document: Optional[dict], binding: DeploymentBinding) -> dict:
    """Preserves every other top-level key/list (`principals`, `signers`,
    `authorities`, any other `deployment_bindings` entry) byte-for-byte
    from `raw_document` unchanged; replaces only the one entry keyed by
    `binding.repository_id`. Producer must not "repair" the registry
    (item 62 of the governing prompt) — malformed input is rejected
    upstream, by `_parse_registry_document`, before this function is ever
    called."""

    base = dict(raw_document) if raw_document is not None else {"registry_version": REGISTRY_SCHEMA_VERSION}
    existing_bindings = [
        entry
        for entry in (base.get("deployment_bindings") or [])
        if not (isinstance(entry, dict) and entry.get("repository_id") == binding.repository_id)
    ]
    new_bindings = existing_bindings + [_deployment_binding_to_document(binding)]
    new_bindings.sort(key=lambda entry: entry["repository_id"])
    updated = dict(base)
    updated["deployment_bindings"] = new_bindings
    return updated


def _atomic_write_registry(store_root: Path, document: dict) -> None:
    """HBDC-REQ-063: `repository_identity.py::_write_atomic`'s exact
    idiom, except this function never `mkdir`s `store_root` itself (the
    Protected Root's existence is a strict precondition, checked by
    `_require_trust_store_available` before this is ever called)."""

    registry_path = store_root / _REGISTRY_FILE_NAME
    _reject_symlink(registry_path)
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-deployment-binding-", dir=str(store_root))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _reject_symlink(registry_path)
        os.replace(tmp_name, registry_path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _read_back_and_verify(store_root: Path, expected_binding: DeploymentBinding) -> DeploymentBinding:
    """HBDC-REQ item-13/69: never report success on a rename alone. Reads
    `registry.json` fresh from disk, re-parses it through the exact same
    `hatp_bootstrap._parse_registry_document` the production read path
    uses, and confirms the persisted entry for `expected_binding.
    repository_id` is byte-for-byte identical to what was intended."""

    raw = _load_raw_registry_document(store_root)
    if raw is None:
        raise DeploymentBindingReadbackMismatchError(
            f"registry.json is missing immediately after a write for repository_id={expected_binding.repository_id!r}"
        )
    parsed = _parse_registry_document(raw)
    persisted = parsed.deployment_bindings.get(expected_binding.repository_id)
    if persisted != expected_binding:
        raise DeploymentBindingReadbackMismatchError(
            f"registry.json read-back for repository_id={expected_binding.repository_id!r} "
            f"does not match the intended write: persisted={persisted!r} expected={expected_binding!r}"
        )
    return persisted


# ═══════════════════════════════════════════════════════════════════════════
# Locking (non-normative implementation hardening; 149O.20L.7H's
# concurrency-lock finding, disposed of here — see module docstring).
# ═══════════════════════════════════════════════════════════════════════════


@contextmanager
def _deployment_binding_transition_lock(store_root: Path) -> Iterator[None]:
    lock_path = store_root / _DEPLOYMENT_BINDING_TRANSITION_LOCK_FILE_NAME
    _reject_symlink(lock_path)
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


# ═══════════════════════════════════════════════════════════════════════════
# Repository-subject resolution (HBDC-REQ-057/8.1): read-only, never
# calls `ensure_repository_identity()`. A missing identity fails closed
# with a deterministic, typed result rather than silently creating one.
# ═══════════════════════════════════════════════════════════════════════════


def _resolve_repository_id(repository_root: Path) -> str:
    harness_root = HarnessPath(repository_root)
    identity = read_repository_identity(harness_root)  # RepositoryIdentityMalformedError propagates uncaught.
    if identity is None:
        raise RepositoryIdentityMissingError(
            f"no RepositoryIdentity exists for {repository_root}; this module never calls "
            "ensure_repository_identity() as an implicit side effect of a binding operation"
        )
    return identity.repository_instance_id


def _resolve_canonical_root(repository_root: Path) -> str:
    try:
        return resolve_canonical_deployment_root(repository_root)
    except OSError as exc:
        raise DeploymentRootUnresolvableError(
            f"canonical_deployment_root could not be resolved for {repository_root}: {exc}"
        ) from exc


def _audit(
    *,
    repository_root: Path,
    event_type: str,
    summary: str,
    principal_id: str,
) -> None:
    """HBDC-REQ-062. Always the last step of a successful operation (see
    module docstring's audit-ordering discipline). Raises uncaught on
    failure — this module never silently loses authority-mutation
    evidence."""

    append_provenance_event(
        HarnessPath(repository_root),
        event_type,
        summary,
        agent_id=f"admin:{principal_id}",
    )


def _binding_fields_equal_for_idempotency(a: DeploymentBinding, b: DeploymentBinding) -> bool:
    return all(getattr(a, field) == getattr(b, field) for field in _COMPARED_AUTHORITY_FIELDS)


# ═══════════════════════════════════════════════════════════════════════════
# CREATE (HBDC-REQ-057..059/062..067)
# ═══════════════════════════════════════════════════════════════════════════


def create_deployment_binding(
    *,
    repository_root: Path,
    authority: AuthorityEvidence,
    _protected_root: Optional[Path] = None,
) -> DeploymentBindingOperationResult:
    """Creates a new `DeploymentBinding` for `repository_root`'s existing
    `RepositoryIdentity`, or safely no-ops if an identical `active` entry
    already exists (HBDC-REQ-059). Fails closed on any conflicting
    existing entry, active or revoked (see module docstring's
    "create against a revoked entry" disposition)."""

    _validate_authority_evidence(authority)
    repository_id = _resolve_repository_id(repository_root)
    canonical_root = _resolve_canonical_root(repository_root)

    candidate = DeploymentBinding(
        repository_id=repository_id,
        canonical_deployment_root=canonical_root,
        principal_id=authority.principal_id,
        signer_key_id=authority.signer_key_id,
        provider_profile=authority.provider_profile,
        authority_scope=authority.authority_scope,
        valid_from=_canonical_timestamp_now(),
        status="active",
        revoked_at=None,
    )

    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    with _deployment_binding_transition_lock(store_root):
        raw_document = _load_raw_registry_document(store_root)
        parsed = _parse_registry_document(raw_document) if raw_document is not None else None
        existing = parsed.deployment_bindings.get(repository_id) if parsed is not None else None

        if existing is not None:
            if existing.status == "revoked":
                raise DuplicateConflictingBindingError(
                    f"repository_id={repository_id!r} already has a revoked DeploymentBinding entry; "
                    "create() never reactivates a revoked binding -- use rotate_deployment_binding() instead"
                )
            if not _binding_fields_equal_for_idempotency(existing, candidate):
                raise DuplicateConflictingBindingError(
                    f"repository_id={repository_id!r} already has an active DeploymentBinding entry with "
                    "differing field values; create() refuses to overwrite a conflicting entry"
                )
            already_satisfied = True
            persisted = existing
        else:
            already_satisfied = False
            new_document = _registry_document_with_binding(raw_document, candidate)
            # Full-document round-trip validation before ever touching disk.
            _parse_registry_document(new_document)
            _atomic_write_registry(store_root, new_document)
            persisted = _read_back_and_verify(store_root, candidate)

    if already_satisfied:
        _audit(
            repository_root=repository_root,
            event_type="deployment_binding_create_noop",
            summary=(
                f"create_deployment_binding: already_satisfied repository_id={repository_id} "
                f"canonical_deployment_root={canonical_root} election_reference={authority.election_reference}"
            ),
            principal_id=authority.principal_id,
        )
        return DeploymentBindingOperationResult(
            outcome=DeploymentBindingOutcome.ALREADY_SATISFIED, binding=persisted, previous_binding=persisted
        )

    _audit(
        repository_root=repository_root,
        event_type="deployment_binding_created",
        summary=(
            f"create_deployment_binding: created repository_id={repository_id} "
            f"canonical_deployment_root={canonical_root} principal_id={authority.principal_id} "
            f"election_reference={authority.election_reference}"
        ),
        principal_id=authority.principal_id,
    )
    return DeploymentBindingOperationResult(
        outcome=DeploymentBindingOutcome.CREATED, binding=persisted, previous_binding=None
    )


# ═══════════════════════════════════════════════════════════════════════════
# ROTATE (HBDC-REQ-060/061/062..067; in-place logical replacement, no
# dual-active-authority window)
# ═══════════════════════════════════════════════════════════════════════════


def rotate_deployment_binding(
    *,
    repository_root: Path,
    authority: AuthorityEvidence,
    _protected_root: Optional[Path] = None,
) -> DeploymentBindingOperationResult:
    """Full in-place overwrite of the sole existing entry's mutable
    fields (HBDC-REQ-061): new `principal_id`/`signer_key_id`/
    `provider_profile`/`authority_scope`/`canonical_deployment_root`,
    fresh `valid_from`, `status` reset to `"active"`, `revoked_at`
    cleared. Fails closed if no entry exists (never silently creates)
    or if the existing entry is already revoked (never resurrects it)."""

    _validate_authority_evidence(authority)
    repository_id = _resolve_repository_id(repository_root)
    canonical_root = _resolve_canonical_root(repository_root)

    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    with _deployment_binding_transition_lock(store_root):
        raw_document = _load_raw_registry_document(store_root)
        parsed = _parse_registry_document(raw_document) if raw_document is not None else None
        existing = parsed.deployment_bindings.get(repository_id) if parsed is not None else None

        if existing is None:
            raise DeploymentBindingNotFoundError(
                f"no DeploymentBinding entry exists for repository_id={repository_id!r}; "
                "rotate_deployment_binding() never creates -- use create_deployment_binding() first"
            )
        if existing.status == "revoked":
            raise DeploymentBindingRevokedError(
                f"DeploymentBinding entry for repository_id={repository_id!r} is revoked; "
                "rotate_deployment_binding() never resurrects a revoked binding"
            )

        rotated = DeploymentBinding(
            repository_id=repository_id,
            canonical_deployment_root=canonical_root,
            principal_id=authority.principal_id,
            signer_key_id=authority.signer_key_id,
            provider_profile=authority.provider_profile,
            authority_scope=authority.authority_scope,
            valid_from=_canonical_timestamp_now(),
            status="active",
            revoked_at=None,
        )

        new_document = _registry_document_with_binding(raw_document, rotated)
        _parse_registry_document(new_document)
        _atomic_write_registry(store_root, new_document)
        persisted = _read_back_and_verify(store_root, rotated)

    _audit(
        repository_root=repository_root,
        event_type="deployment_binding_rotated",
        summary=(
            f"rotate_deployment_binding: rotated repository_id={repository_id} "
            f"previous_principal_id={existing.principal_id} new_principal_id={authority.principal_id} "
            f"canonical_deployment_root={canonical_root} election_reference={authority.election_reference}"
        ),
        principal_id=authority.principal_id,
    )
    return DeploymentBindingOperationResult(
        outcome=DeploymentBindingOutcome.ROTATED, binding=persisted, previous_binding=existing
    )


# ═══════════════════════════════════════════════════════════════════════════
# REVOKE (HBDC-REQ-061/062..067; field mutation only, never deletion —
# CBD-10)
# ═══════════════════════════════════════════════════════════════════════════


def revoke_deployment_binding(
    *,
    repository_root: Path,
    election_reference: str,
    _protected_root: Optional[Path] = None,
) -> DeploymentBindingOperationResult:
    """`status` -> `"revoked"`, `revoked_at` set; every other field
    (including `principal_id`/`signer_key_id`/`provider_profile`/
    `authority_scope`/`canonical_deployment_root`) preserved unchanged
    (HBDC-REQ-061, CBD-10 -- field mutation, never deletion). Fails
    closed if no entry exists. Idempotent (`ALREADY_REVOKED`, original
    `revoked_at` preserved) if the entry is already revoked."""

    _require_nonempty_str(
        election_reference, context="election_reference", error_type=AuthorityEvidenceMissingError
    )
    repository_id = _resolve_repository_id(repository_root)

    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    with _deployment_binding_transition_lock(store_root):
        raw_document = _load_raw_registry_document(store_root)
        parsed = _parse_registry_document(raw_document) if raw_document is not None else None
        existing = parsed.deployment_bindings.get(repository_id) if parsed is not None else None

        if existing is None:
            raise DeploymentBindingNotFoundError(
                f"no DeploymentBinding entry exists for repository_id={repository_id!r}; "
                "revoke_deployment_binding() never creates a tombstone"
            )

        if existing.status == "revoked":
            outcome_binding = existing
            already_revoked = True
        else:
            revoked = replace(existing, status="revoked", revoked_at=_canonical_timestamp_now())
            new_document = _registry_document_with_binding(raw_document, revoked)
            _parse_registry_document(new_document)
            _atomic_write_registry(store_root, new_document)
            outcome_binding = _read_back_and_verify(store_root, revoked)
            already_revoked = False

    principal_id = existing.principal_id
    if already_revoked:
        _audit(
            repository_root=repository_root,
            event_type="deployment_binding_revoke_noop",
            summary=(
                f"revoke_deployment_binding: already_revoked repository_id={repository_id} "
                f"revoked_at={existing.revoked_at} election_reference={election_reference}"
            ),
            principal_id=principal_id,
        )
        return DeploymentBindingOperationResult(
            outcome=DeploymentBindingOutcome.ALREADY_REVOKED, binding=existing, previous_binding=existing
        )

    _audit(
        repository_root=repository_root,
        event_type="deployment_binding_revoked",
        summary=(
            f"revoke_deployment_binding: revoked repository_id={repository_id} "
            f"revoked_at={outcome_binding.revoked_at} election_reference={election_reference}"
        ),
        principal_id=principal_id,
    )
    return DeploymentBindingOperationResult(
        outcome=DeploymentBindingOutcome.REVOKED, binding=outcome_binding, previous_binding=existing
    )


# ═══════════════════════════════════════════════════════════════════════════
# Read-only preview (HBDC-REQ item-47: "SHOULD", not a numbered "SHALL"
# per 149O.20L.7H -- implemented because it fits cleanly on top of the
# functions above and never writes).
# ═══════════════════════════════════════════════════════════════════════════


class DeploymentBindingPreviewKind(str, Enum):
    WOULD_CREATE = "would_create"
    WOULD_NOOP_ALREADY_SATISFIED = "would_noop_already_satisfied"
    WOULD_CONFLICT = "would_conflict"
    WOULD_ROTATE = "would_rotate"
    WOULD_FAIL_NOT_FOUND = "would_fail_not_found"
    WOULD_FAIL_REVOKED = "would_fail_revoked"
    WOULD_REVOKE = "would_revoke"
    WOULD_NOOP_ALREADY_REVOKED = "would_noop_already_revoked"


@dataclass(frozen=True)
class DeploymentBindingPreview:
    kind: DeploymentBindingPreviewKind
    repository_id: str
    canonical_deployment_root: str
    existing_binding: Optional[DeploymentBinding]
    candidate_binding: Optional[DeploymentBinding]
    registry_path: Path


def preview_create_deployment_binding(
    *, repository_root: Path, authority: AuthorityEvidence, _protected_root: Optional[Path] = None
) -> DeploymentBindingPreview:
    """Read-only. Never writes. Computes exactly what
    `create_deployment_binding` would do without acquiring the
    transition lock or touching disk."""

    _validate_authority_evidence(authority)
    repository_id = _resolve_repository_id(repository_root)
    canonical_root = _resolve_canonical_root(repository_root)
    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    candidate = DeploymentBinding(
        repository_id=repository_id,
        canonical_deployment_root=canonical_root,
        principal_id=authority.principal_id,
        signer_key_id=authority.signer_key_id,
        provider_profile=authority.provider_profile,
        authority_scope=authority.authority_scope,
        valid_from=_canonical_timestamp_now(),
        status="active",
        revoked_at=None,
    )
    raw_document = _load_raw_registry_document(store_root)
    parsed = _parse_registry_document(raw_document) if raw_document is not None else None
    existing = parsed.deployment_bindings.get(repository_id) if parsed is not None else None

    if existing is None:
        kind = DeploymentBindingPreviewKind.WOULD_CREATE
    elif existing.status == "revoked":
        kind = DeploymentBindingPreviewKind.WOULD_CONFLICT
    elif _binding_fields_equal_for_idempotency(existing, candidate):
        kind = DeploymentBindingPreviewKind.WOULD_NOOP_ALREADY_SATISFIED
    else:
        kind = DeploymentBindingPreviewKind.WOULD_CONFLICT

    return DeploymentBindingPreview(
        kind=kind,
        repository_id=repository_id,
        canonical_deployment_root=canonical_root,
        existing_binding=existing,
        candidate_binding=candidate,
        registry_path=store_root / _REGISTRY_FILE_NAME,
    )


def preview_rotate_deployment_binding(
    *, repository_root: Path, authority: AuthorityEvidence, _protected_root: Optional[Path] = None
) -> DeploymentBindingPreview:
    _validate_authority_evidence(authority)
    repository_id = _resolve_repository_id(repository_root)
    canonical_root = _resolve_canonical_root(repository_root)
    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    raw_document = _load_raw_registry_document(store_root)
    parsed = _parse_registry_document(raw_document) if raw_document is not None else None
    existing = parsed.deployment_bindings.get(repository_id) if parsed is not None else None

    if existing is None:
        return DeploymentBindingPreview(
            kind=DeploymentBindingPreviewKind.WOULD_FAIL_NOT_FOUND,
            repository_id=repository_id,
            canonical_deployment_root=canonical_root,
            existing_binding=None,
            candidate_binding=None,
            registry_path=store_root / _REGISTRY_FILE_NAME,
        )
    if existing.status == "revoked":
        return DeploymentBindingPreview(
            kind=DeploymentBindingPreviewKind.WOULD_FAIL_REVOKED,
            repository_id=repository_id,
            canonical_deployment_root=canonical_root,
            existing_binding=existing,
            candidate_binding=None,
            registry_path=store_root / _REGISTRY_FILE_NAME,
        )
    candidate = DeploymentBinding(
        repository_id=repository_id,
        canonical_deployment_root=canonical_root,
        principal_id=authority.principal_id,
        signer_key_id=authority.signer_key_id,
        provider_profile=authority.provider_profile,
        authority_scope=authority.authority_scope,
        valid_from=_canonical_timestamp_now(),
        status="active",
        revoked_at=None,
    )
    return DeploymentBindingPreview(
        kind=DeploymentBindingPreviewKind.WOULD_ROTATE,
        repository_id=repository_id,
        canonical_deployment_root=canonical_root,
        existing_binding=existing,
        candidate_binding=candidate,
        registry_path=store_root / _REGISTRY_FILE_NAME,
    )


def preview_revoke_deployment_binding(
    *, repository_root: Path, _protected_root: Optional[Path] = None
) -> DeploymentBindingPreview:
    repository_id = _resolve_repository_id(repository_root)
    canonical_root = _resolve_canonical_root(repository_root)
    store_root = _resolve_protected_root(_protected_root)
    _require_trust_store_available(store_root)

    raw_document = _load_raw_registry_document(store_root)
    parsed = _parse_registry_document(raw_document) if raw_document is not None else None
    existing = parsed.deployment_bindings.get(repository_id) if parsed is not None else None

    if existing is None:
        kind = DeploymentBindingPreviewKind.WOULD_FAIL_NOT_FOUND
    elif existing.status == "revoked":
        kind = DeploymentBindingPreviewKind.WOULD_NOOP_ALREADY_REVOKED
    else:
        kind = DeploymentBindingPreviewKind.WOULD_REVOKE

    return DeploymentBindingPreview(
        kind=kind,
        repository_id=repository_id,
        canonical_deployment_root=canonical_root,
        existing_binding=existing,
        candidate_binding=None,
        registry_path=store_root / _REGISTRY_FILE_NAME,
    )
