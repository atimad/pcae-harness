"""
HPAC-001 v2.0 shared foundation — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.

Bounded supporting helpers reused by every new HPAC-001 model/store module
(`human_principal_registry.py`, `approval_presentation.py`,
`human_authentication_proof.py`, `hpac_lifecycle.py`,
`runtime_invocation_authority_consumption.py`). This module owns nothing
normative on its own -- it exists only to avoid duplicating identical
canonicalization/atomic-write/symlink-rejection code six times (plan
149O.20L.7O.3W.1R.2B.1R.1.1R.2 §35's reuse recommendation), per this
phase's own "bounded supporting validators/helpers" allowance.

This module imports no `subprocess`, `socket`, hardware, or network
primitive, performs no filesystem write or directory creation at import
time, and does not read `hatp_bootstrap.py`'s registry, principal_id
space, or challenge domain (HPAC-REQ-018/084) -- it defines HPAC-001's own
entirely separate protected-root constant.

Canonicalization: `pcae.core.runtime_authority.compute_canonical_digest`
already implements HPAC-REQ-089's exact rule (NFC-normalized strings,
recursively sorted-key compact JSON, SHA-256) and is reused directly
rather than reimplemented, per plan §35's explicit recommendation.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.runtime_authority import compute_canonical_digest

__all__ = [
    "HPACFoundationError",
    "HPACSymlinkError",
    "HPACMalformedError",
    "HPACCorruptionError",
    "HPACDuplicateError",
    "HPACUnsupportedPlatformError",
    "ProtectedAdminCapability",
    "canonical_digest",
    "resolve_hpac_protected_root",
    "reject_symlink",
    "require_nonempty_str",
    "require_status",
    "require_timestamp",
    "require_revoked_at_consistency",
    "new_hpac_id",
    "id_pattern_matches",
    "write_atomic_replace",
    "write_atomic_create_only",
    "read_canonical_json_document",
]


class HPACFoundationError(Exception):
    """Base error for HPAC-001 foundation-layer operations."""


class HPACSymlinkError(HPACFoundationError):
    """A protected HPAC-001 path is, or resolves through, a symlink.
    Refused rather than followed (HPAC-REQ-022/053/093/094)."""


class HPACMalformedError(HPACFoundationError):
    """A document exists but fails strict, closed-schema validation.
    Never partially accepted (HPAC-REQ-017/052/091/095/098)."""


class HPACCorruptionError(HPACFoundationError):
    """A document exists, parses as JSON, but its digest, chain, or
    read-back verification fails. Treated identically to
    'durability-uncertain' -- never interpreted as either valid or
    absent (HPAC-REQ-100)."""


class HPACDuplicateError(HPACFoundationError):
    """A create-only write target already exists. The create-only
    guarantee is never silently overwritten (HPAC-REQ-053/093/098)."""


class HPACUnsupportedPlatformError(HPACFoundationError):
    """No fixed protected-root implementation exists for this platform.
    Fails closed rather than falling back to an environment-derived
    location (mirrors `hatp_bootstrap._default_production_trust_root`'s
    identical discipline)."""


_STATUS_VALUES = frozenset({"active", "revoked"})
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")


@dataclass(frozen=True)
class ProtectedAdminCapability:
    """A structural marker write APIs require as an explicit parameter
    before mutating any HPAC-001 store.

    This is honestly **not** a real protected-admin ceremony
    (HPAC-REQ-023/028/029's external deployment-owner anchor, UV-required
    non-defaultable act, and FIDO2 registration-response verification are
    all explicitly out of scope for this foundation phase). Constructing
    this object is deliberately trivial and grants no real-world
    authority whatsoever -- its only purpose is to make store mutation a
    structurally distinct, non-default call shape that ordinary read
    access can never produce by accident, so that a later phase has a
    single, obvious seam to replace with a verified ceremony result. A
    caller holding one of these MUST NOT be treated, described, or
    logged as "authorized" or "the protected administrator" -- doing so
    would itself violate HPAC-REQ-006's forbidden-authority-shortcut
    rule.
    """

    acknowledgement: str = "phase-1-foundation-non-production-capability-marker"

    def __post_init__(self) -> None:
        if self.acknowledgement != "phase-1-foundation-non-production-capability-marker":
            raise HPACFoundationError(
                "ProtectedAdminCapability.acknowledgement is a fixed constant; "
                "it cannot be repurposed to carry caller-supplied authority claims."
            )


def canonical_digest(value: object) -> str:
    """HPAC-REQ-089's exact canonicalization rule, reused verbatim from
    `runtime_authority.compute_canonical_digest` rather than
    reimplemented."""

    return compute_canonical_digest(value)


# ═══════════════════════════════════════════════════════════════════════
# Deployment/user-scoped protected root (HPAC-REQ-021/022) -- entirely
# separate from HATP's own trust-store root (HPAC-REQ-018).
# ═══════════════════════════════════════════════════════════════════════

_MACOS_FIXED_PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")
_LINUX_FIXED_PROTECTED_ROOT = Path("/etc/pcae/hpac/protected-root")


def resolve_hpac_protected_root() -> Path:
    """The authoritative HPAC-001 protected-root location: a fixed,
    platform-level path taking **no** arguments and consulting no
    repository state, current working directory, environment variable,
    task, or caller input (HPAC-REQ-022/079/080). Deliberately distinct
    from `hatp_bootstrap._default_production_trust_root` -- a different
    path, under a different directory tree, in HPAC-001's own namespace
    (HPAC-REQ-018).

    This function does not create, provision, resolve symlinks in, or
    otherwise touch the returned path -- it is a pure constant lookup.
    Every store in this phase takes a `root: Path` constructor argument
    explicitly so tests can inject an isolated directory; production
    callers are expected to pass `resolve_hpac_protected_root()`. This
    function itself never accepts an override argument, so no caller can
    redirect where a *production* resolution would land.
    """

    if os.name != "posix":
        raise HPACUnsupportedPlatformError(
            f"HPAC-001 protected root has no fixed-path implementation for platform {os.name!r}; failing closed."
        )
    if sys.platform == "darwin":
        return _MACOS_FIXED_PROTECTED_ROOT
    if sys.platform == "linux":
        return _LINUX_FIXED_PROTECTED_ROOT
    raise HPACUnsupportedPlatformError(
        f"HPAC-001 protected root has no fixed-path implementation for platform {sys.platform!r}; failing closed."
    )


def reject_symlink(target: Path) -> None:
    if target.is_symlink():
        raise HPACSymlinkError(f"HPAC-001 protected path is a symlink, refusing: {target}")


def require_nonempty_str(value: object, *, context: str) -> str:
    if not isinstance(value, str) or value == "" or value != value.strip():
        raise HPACMalformedError(f"{context}: expected a non-empty, non-whitespace-padded string, got {value!r}")
    if len(value) > 256:
        raise HPACMalformedError(f"{context}: exceeds the 256-character HPAC-001 identifier grammar bound")
    return value


def require_status(value: object, *, context: str) -> str:
    if value not in _STATUS_VALUES:
        raise HPACMalformedError(f"{context}: status must be one of {sorted(_STATUS_VALUES)}, got {value!r}")
    return value  # type: ignore[return-value]


def require_timestamp(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        raise HPACMalformedError(f"{context}: expected an RFC3339 UTC timestamp, got {value!r}")
    return value


def require_revoked_at_consistency(status: str, revoked_at: object, *, context: str) -> Optional[str]:
    """HPAC-REQ-061/062's monotonic revocation discipline requires
    `revoked_at` to be present exactly when `status == 'revoked'` --
    never present alongside `active`, never absent alongside
    `revoked`."""

    if status == "revoked":
        if revoked_at is None:
            raise HPACMalformedError(f"{context}: status is 'revoked' but revoked_at is missing")
        return require_timestamp(revoked_at, context=f"{context}.revoked_at")
    if revoked_at is not None:
        raise HPACMalformedError(f"{context}: status is 'active' but revoked_at is set")
    return None


_ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "hp": re.compile(r"^hp-[0-9a-f]{32}$"),
    "hpc": re.compile(r"^hpc-[0-9a-f]{32}$"),
    "hap": re.compile(r"^hap-[0-9a-f]{32}$"),
    "hpe": re.compile(r"^hpe-[0-9a-f]{32}$"),
    "hpl": re.compile(r"^hpl-[0-9a-f]{32}$"),
    "hpevt": re.compile(r"^hpevt-[0-9a-f]{32}$"),
    "hpm": re.compile(r"^hpm-[0-9a-f]{32}$"),
}


def new_hpac_id(prefix: str) -> str:
    """Opaque `<prefix>-<32-hex>` ID generator, mirroring
    `runtime_authority.new_approval_id`'s pattern with a new prefix per
    HPAC-001 artifact family. `prefix` must be a key of `_ID_PATTERNS`."""

    if prefix not in _ID_PATTERNS:
        raise HPACFoundationError(f"unknown HPAC-001 ID prefix: {prefix!r}")
    return f"{prefix}-{uuid.uuid4().hex}"


def id_pattern_matches(prefix: str, value: object) -> bool:
    if prefix not in _ID_PATTERNS:
        raise HPACFoundationError(f"unknown HPAC-001 ID prefix: {prefix!r}")
    return isinstance(value, str) and bool(_ID_PATTERNS[prefix].match(value))


# ═══════════════════════════════════════════════════════════════════════
# Atomic write primitives
# ═══════════════════════════════════════════════════════════════════════


def write_atomic_replace(path: Path, data: bytes) -> None:
    """Race-safe, crash-consistent whole-document replace: temp file in
    the same directory, fsync, atomic `os.replace`. Used for the mutable
    (append-only-per-record) `HumanPrincipalRegistry` document, which is
    read-modify-rewritten as a whole file but must never lose or corrupt
    any other record while doing so (HPAC-REQ-015). Mirrors
    `repository_identity._write_atomic`'s existing idiom exactly."""

    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    reject_symlink(path)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-hpac-", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        reject_symlink(path)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_atomic_create_only(path: Path, data: bytes) -> None:
    """Single-winner, create-only atomic commit for every immutable
    per-ID HPAC-001 record (presentation evidence, proof, lifecycle
    event, consumption record): write to a protected temporary sibling,
    fsync, then install only if the final path is absent, using
    `O_CREAT | O_EXCL` for the exclusivity guarantee (HPAC-REQ-093/094/
    100). Two concurrent callers racing for the same path produce
    exactly one winner; the loser raises `HPACDuplicateError` and MUST
    re-read the just-created record rather than retry the create
    (HPAC-REQ-099/HPAC-REQ-024's "no in-process lock is sufficient
    alone" discipline)."""

    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    reject_symlink(path)
    if path.exists():
        raise HPACDuplicateError(f"HPAC-001 create-only path already exists: {path}")
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-hpac-", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            create_fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise HPACDuplicateError(f"HPAC-001 create-only path already exists: {path}") from exc
        os.close(create_fd)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def read_canonical_json_document(path: Path) -> object:
    """Symlink-rejecting, strict-JSON read. Raises `HPACMalformedError`
    on any decode failure -- truncated/corrupt bytes are never
    partially parsed (HPAC-REQ-017/094)."""

    reject_symlink(path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HPACCorruptionError(f"HPAC-001 protected path could not be read: {path}") from exc
    import json

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HPACMalformedError(f"HPAC-001 protected path is not valid JSON: {path}") from exc
