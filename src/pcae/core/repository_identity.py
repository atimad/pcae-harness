"""Canonical Repository Identity (CRI Model A), Layer 1 — Phase 149O.1E,
Wave 1.

Owned as a **general PCAE core facility**, not as HATP-specific code
(HATP-REQ-107, HATP-REQ-046). This module implements only Layer 1: a
repository-local, randomly generated, persistent `repository_instance_id`.
Layer 2 (the admin-owned protected deployment binding that is the sole
source of repository-scoped HATP authority) lives in `hatp_bootstrap.py`
and is a structurally separate fact.

Frozen invariant (HATP-REQ-051, HATP-REQ-063): possession, knowledge,
copying, or modification of the identifier defined here SHALL NOT by
itself grant any approval authority. This module therefore has no
knowledge of HATP, the Permission Broker, RAE, or any other authority
concept, and imports none of them.
"""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pcae.core.paths import HarnessPath

SCHEMA_VERSION = 1

REPOSITORY_IDENTITY_RELATIVE_PATH = Path(".pcae") / "repository-identity.json"

_REQUIRED_FIELDS = frozenset({"schema_version", "repository_instance_id", "created_at"})


class RepositoryIdentityError(Exception):
    """Base error for repository-identity operations."""


class RepositoryIdentityMalformedError(RepositoryIdentityError):
    """Identity file exists but is not valid. Never auto-repaired or
    silently regenerated (auto-regeneration could silently change
    security-relevant scope, per governing-prompt item 25)."""


class RepositoryIdentitySymlinkError(RepositoryIdentityError):
    """The identity file position is (or resolves through) a symlink.
    Refused rather than followed, to avoid a caller-controlled write
    target."""


@dataclass(frozen=True)
class RepositoryIdentity:
    schema_version: int
    repository_instance_id: str
    created_at: str

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "repository_instance_id": self.repository_instance_id,
            "created_at": self.created_at,
        }


def _parse_iso_timestamp(value: object) -> Optional[datetime]:
    """Fail-closed timestamp parsing, mirroring
    `rollback_approval_evidence.py::_parse_iso_timestamp` exactly (per
    149O.1D plan §5.13/§39) to avoid reintroducing the Python 3.9
    `fromisoformat` Z-suffix portability defect. Duplicated locally
    rather than imported: Wave 1 imports nothing from
    `rollback_approval_evidence.py` (HATP/RAE dependency-direction
    boundary, 149O.1D plan §62-70)."""

    if not isinstance(value, str) or not value:
        return None
    try:
        text = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def is_valid_repository_instance_id(value: object) -> bool:
    """Public format check for a `repository_instance_id` string (UUID4).

    Exposed for the Layer-2 protected-deployment-binding facility
    (`hatp_bootstrap.py`) to validate the identifier it binds against,
    per the dependency graph in 149O.1D plan §6 (A must exist before C's
    binding can name a `repository_id`). Format validation only -- this
    function makes no authority claim (HATP-REQ-051)."""

    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        return False
    return parsed.version == 4 and str(parsed) == value.lower()


_is_valid_uuid4 = is_valid_repository_instance_id


def validate_repository_identity_document(document: object) -> RepositoryIdentity:
    """Strict validation: closed field set, no permissive coercion. Raises
    `RepositoryIdentityMalformedError` on any deviation -- never returns a
    best-effort partial result."""

    if not isinstance(document, dict):
        raise RepositoryIdentityMalformedError("repository identity document is not a JSON object")

    unknown = set(document.keys()) - _REQUIRED_FIELDS
    if unknown:
        raise RepositoryIdentityMalformedError(f"repository identity document has unrecognized fields: {sorted(unknown)}")

    missing = _REQUIRED_FIELDS - set(document.keys())
    if missing:
        raise RepositoryIdentityMalformedError(f"repository identity document is missing fields: {sorted(missing)}")

    schema_version = document["schema_version"]
    if schema_version != SCHEMA_VERSION:
        raise RepositoryIdentityMalformedError(
            f"repository identity schema_version {schema_version!r} is not supported (expected {SCHEMA_VERSION})"
        )

    repository_instance_id = document["repository_instance_id"]
    if not _is_valid_uuid4(repository_instance_id):
        raise RepositoryIdentityMalformedError("repository_instance_id is not a valid UUID4 string")

    created_at = document["created_at"]
    if _parse_iso_timestamp(created_at) is None:
        raise RepositoryIdentityMalformedError("created_at is not a valid timezone-aware ISO-8601 timestamp")

    return RepositoryIdentity(
        schema_version=schema_version,
        repository_instance_id=repository_instance_id,
        created_at=created_at,
    )


def _reject_symlink(target: Path) -> None:
    if target.is_symlink():
        raise RepositoryIdentitySymlinkError(f"repository identity path is a symlink, refusing: {target}")
    if target.parent.exists() and target.parent.is_symlink():
        raise RepositoryIdentitySymlinkError(f"repository identity parent directory is a symlink, refusing: {target.parent}")


def _write_atomic(path: Path, data: bytes) -> None:
    """Race-safe, crash-consistent write: temp file in the same directory,
    fsync, then atomic `os.replace`. Mirrors the existing project idiom
    (`cltr/persistence.py::_write_atomic`,
    `governance/publication/storage.py::_write_atomic_json`) rather than
    inventing a new one."""

    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    _reject_symlink(path)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-repository-identity-", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        _reject_symlink(path)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def read_repository_identity(root: HarnessPath) -> Optional[RepositoryIdentity]:
    """Read-only lookup, independent of `ensure_repository_identity`
    (useful for future verifier code, per 149O.1D plan §12).

    Returns `None` only when the identity file is genuinely absent.
    Raises `RepositoryIdentityMalformedError` if it exists but fails
    validation -- missing and malformed are deliberately distinct
    outcomes; a caller MUST NOT treat a malformed identity as "no
    constraint." Never accepts a caller-supplied trust override (no
    `trusted_id=`-shaped parameter, per governing-prompt item 27)."""

    target = root.join(REPOSITORY_IDENTITY_RELATIVE_PATH)
    _reject_symlink(target)
    if not target.exists():
        return None
    try:
        raw = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise RepositoryIdentityMalformedError(f"repository identity file could not be read: {exc}") from exc
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RepositoryIdentityMalformedError(f"repository identity file is not valid JSON: {exc}") from exc
    return validate_repository_identity_document(document)


def _generate_repository_identity(now: Optional[datetime] = None) -> RepositoryIdentity:
    timestamp = now or datetime.now(timezone.utc)
    return RepositoryIdentity(
        schema_version=SCHEMA_VERSION,
        repository_instance_id=str(uuid.uuid4()),
        created_at=timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    )


def ensure_repository_identity(root: HarnessPath) -> RepositoryIdentity:
    """Idempotent ensure/create semantics (149O.1D plan §11):

    - identity exists and is valid -> return it unchanged.
    - identity missing -> generate one atomically and return it. This
      confers no authority by itself (HATP-REQ-048/051).
    - identity exists but is malformed -> fail closed
      (`RepositoryIdentityMalformedError`); never silently replaced.
    """

    existing = read_repository_identity(root)
    if existing is not None:
        return existing

    identity = _generate_repository_identity()
    target = root.join(REPOSITORY_IDENTITY_RELATIVE_PATH)
    payload = json.dumps(identity.to_dict(), indent=2, sort_keys=True) + "\n"
    _write_atomic(target, payload.encode("utf-8"))
    return identity
