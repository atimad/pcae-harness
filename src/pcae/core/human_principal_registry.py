"""
HPAC-001 v2.0 §4-§9 — `HumanPrincipalRegistry` canonical model/store.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 (Layer 1-2 foundation). Implements
only the canonical registry mechanics: `PrincipalRecord`/`CredentialRecord`
models, atomic create/read/list/revoke store operations, and their
preview variants. It does **not** implement the real protected-admin
bootstrap/enrollment ceremony (HPAC-REQ-023/028/029) -- that requires a
real human, real hardware, and a real protected-admin execution context,
none of which this phase may touch (plan §8). Mutation is gated behind
`hpac_foundation.ProtectedAdminCapability`, an honest non-production
marker, not a real ceremony result.

canonical registry mechanics implemented; real trusted enrollment not
implemented (this module's own honest boundary statement, per phase
instruction §7).

This module performs no filesystem write at import time and holds no
mutable module-global canonical-authority cache; every store instance is
explicit and bound to a caller-supplied `root: Path`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACMalformedError,
    ProtectedAdminCapability,
    canonical_digest,
    new_hpac_id,
    read_canonical_json_document,
    reject_symlink,
    require_nonempty_str,
    require_revoked_at_consistency,
    require_status,
    require_timestamp,
    write_atomic_replace,
)

REGISTRY_SCHEMA_VERSION = "HPAC-REGISTRY/2.0"

#: Registry document filename -- deliberately NOT `registry.json`
#: (HATP-001's own filename), stored under an entirely separate root
#: (HPAC-REQ-018).
_REGISTRY_FILENAME = "principal-registry.json"
_REGISTRY_RELATIVE_PATH = Path("principals") / _REGISTRY_FILENAME

_PRINCIPAL_ALLOWED_FIELDS = frozenset(
    {"principal_id", "status", "enrollment_provenance_ref", "enrolled_at", "revoked_at"}
)
_CREDENTIAL_ALLOWED_FIELDS = frozenset(
    {
        "credential_id",
        "principal_id",
        "mechanism_id",
        "public_key",
        "assurance_capabilities",
        "status",
        "enrollment_provenance_ref",
        "enrolled_at",
        "revoked_at",
    }
)


class HumanPrincipalRegistryError(Exception):
    """Base error for `HumanPrincipalRegistry` operations."""


class HumanPrincipalRegistryConflictError(HumanPrincipalRegistryError):
    """A mutation would violate a uniqueness/cardinality/state rule
    (HPAC-REQ-009/027/030)."""


class HumanPrincipalRegistryNotFoundError(HumanPrincipalRegistryError):
    """A mutation or resolve targeted an ID absent from the registry."""


@dataclass(frozen=True)
class PrincipalRecord:
    """HPAC-REQ-013's exact `PrincipalRecord` field set. `principal_id` is
    opaque and immutable (HPAC-REQ-007/009/011); no `display_name`,
    `email`, or other human-facing metadata field exists here, per
    HPAC-REQ-010's explicit omission (not merely separation)."""

    principal_id: str
    status: str
    enrollment_provenance_ref: str
    enrolled_at: str
    revoked_at: Optional[str] = None

    def to_document(self) -> dict:
        return {
            "principal_id": self.principal_id,
            "status": self.status,
            "enrollment_provenance_ref": self.enrollment_provenance_ref,
            "enrolled_at": self.enrolled_at,
            "revoked_at": self.revoked_at,
        }


@dataclass(frozen=True)
class CredentialRecord:
    """HPAC-REQ-013's exact `CredentialRecord` field set. Stores only
    `public_key` and `assurance_capabilities` -- no private key, PIN,
    biometric secret, or repository path field exists on this dataclass
    at all (HPAC-REQ-013/HPAC-REQ-043 credential-security discipline is
    therefore structural, not merely a runtime check that could be
    bypassed)."""

    credential_id: str
    principal_id: str
    mechanism_id: str
    public_key: str
    assurance_capabilities: tuple[str, ...]
    status: str
    enrollment_provenance_ref: str
    enrolled_at: str
    revoked_at: Optional[str] = None

    def to_document(self) -> dict:
        return {
            "credential_id": self.credential_id,
            "principal_id": self.principal_id,
            "mechanism_id": self.mechanism_id,
            "public_key": self.public_key,
            "assurance_capabilities": list(self.assurance_capabilities),
            "status": self.status,
            "enrollment_provenance_ref": self.enrollment_provenance_ref,
            "enrolled_at": self.enrolled_at,
            "revoked_at": self.revoked_at,
        }


@dataclass(frozen=True)
class PreviewResult:
    """Never-writes preview classification (HPAC-REQ-026), mirroring
    HPSE-REQ-026/030's would-enroll/already-enrolled/conflict/
    would-revoke/already-revoked/not-found vocabulary."""

    classification: str
    detail: str = ""


def _parse_principal(document: dict) -> PrincipalRecord:
    if not isinstance(document, dict):
        raise HPACMalformedError("principal record is not an object")
    unknown = set(document.keys()) - _PRINCIPAL_ALLOWED_FIELDS
    if unknown:
        raise HPACMalformedError(f"principal record has unrecognized fields: {sorted(unknown)}")
    principal_id = require_nonempty_str(document.get("principal_id"), context="principal.principal_id")
    status = require_status(document.get("status"), context=f"principal[{principal_id}]")
    provenance_ref = require_nonempty_str(
        document.get("enrollment_provenance_ref"), context=f"principal[{principal_id}].enrollment_provenance_ref"
    )
    enrolled_at = require_timestamp(document.get("enrolled_at"), context=f"principal[{principal_id}].enrolled_at")
    revoked_at = require_revoked_at_consistency(status, document.get("revoked_at"), context=f"principal[{principal_id}]")
    return PrincipalRecord(
        principal_id=principal_id,
        status=status,
        enrollment_provenance_ref=provenance_ref,
        enrolled_at=enrolled_at,
        revoked_at=revoked_at,
    )


def _parse_credential(document: dict) -> CredentialRecord:
    if not isinstance(document, dict):
        raise HPACMalformedError("credential record is not an object")
    unknown = set(document.keys()) - _CREDENTIAL_ALLOWED_FIELDS
    if unknown:
        raise HPACMalformedError(f"credential record has unrecognized fields: {sorted(unknown)}")
    credential_id = require_nonempty_str(document.get("credential_id"), context="credential.credential_id")
    principal_id = require_nonempty_str(document.get("principal_id"), context=f"credential[{credential_id}].principal_id")
    mechanism_id = require_nonempty_str(document.get("mechanism_id"), context=f"credential[{credential_id}].mechanism_id")
    public_key = require_nonempty_str(document.get("public_key"), context=f"credential[{credential_id}].public_key")
    capabilities = document.get("assurance_capabilities")
    if not isinstance(capabilities, list) or not all(isinstance(item, str) and item for item in capabilities):
        raise HPACMalformedError(f"credential[{credential_id}].assurance_capabilities must be a list of non-empty strings")
    status = require_status(document.get("status"), context=f"credential[{credential_id}]")
    provenance_ref = require_nonempty_str(
        document.get("enrollment_provenance_ref"), context=f"credential[{credential_id}].enrollment_provenance_ref"
    )
    enrolled_at = require_timestamp(document.get("enrolled_at"), context=f"credential[{credential_id}].enrolled_at")
    revoked_at = require_revoked_at_consistency(status, document.get("revoked_at"), context=f"credential[{credential_id}]")
    return CredentialRecord(
        credential_id=credential_id,
        principal_id=principal_id,
        mechanism_id=mechanism_id,
        public_key=public_key,
        assurance_capabilities=tuple(capabilities),
        status=status,
        enrollment_provenance_ref=provenance_ref,
        enrolled_at=enrolled_at,
        revoked_at=revoked_at,
    )


@dataclass(frozen=True)
class _ParsedRegistry:
    schema_version: str
    principals: tuple[PrincipalRecord, ...]
    credentials: tuple[CredentialRecord, ...]


def _parse_registry_document(document: object) -> _ParsedRegistry:
    if not isinstance(document, dict):
        raise HPACMalformedError("HumanPrincipalRegistry document is not an object")
    unknown = set(document.keys()) - {"schema_version", "principals", "credentials"}
    if unknown:
        raise HPACMalformedError(f"HumanPrincipalRegistry document has unrecognized fields: {sorted(unknown)}")
    schema_version = document.get("schema_version")
    if schema_version != REGISTRY_SCHEMA_VERSION:
        raise HPACMalformedError(
            f"HumanPrincipalRegistry unknown schema_version {schema_version!r}; failing closed "
            f"(expected {REGISTRY_SCHEMA_VERSION!r})"
        )
    raw_principals = document.get("principals")
    raw_credentials = document.get("credentials")
    if not isinstance(raw_principals, list) or not isinstance(raw_credentials, list):
        raise HPACMalformedError("HumanPrincipalRegistry 'principals'/'credentials' must be lists")

    principals: list[PrincipalRecord] = []
    seen_principal_ids: set[str] = set()
    for raw in raw_principals:
        record = _parse_principal(raw)
        if record.principal_id in seen_principal_ids:
            raise HPACMalformedError(f"duplicate principal_id in registry: {record.principal_id}")
        seen_principal_ids.add(record.principal_id)
        principals.append(record)

    credentials: list[CredentialRecord] = []
    seen_credential_ids: set[str] = set()
    for raw in raw_credentials:
        record = _parse_credential(raw)
        if record.credential_id in seen_credential_ids:
            raise HPACMalformedError(f"duplicate credential_id in registry: {record.credential_id}")
        seen_credential_ids.add(record.credential_id)
        if record.principal_id not in seen_principal_ids:
            raise HPACMalformedError(
                f"credential {record.credential_id} names unknown principal_id {record.principal_id}"
            )
        credentials.append(record)

    return _ParsedRegistry(
        schema_version=schema_version,
        principals=tuple(sorted(principals, key=lambda p: p.principal_id)),
        credentials=tuple(sorted(credentials, key=lambda c: c.credential_id)),
    )


class HumanPrincipalRegistryStore:
    """Deployment/user-scoped canonical `HumanPrincipalRegistry` store
    (HPAC-REQ-012/021). Constructed with an explicit `root: Path` --
    production callers pass `hpac_foundation.resolve_hpac_protected_root()`;
    tests inject an isolated directory. This class itself performs **no**
    repository/cwd/environment/task lookup anywhere in its own code, so
    repository-controlled state structurally cannot select, override, or
    influence which registry a given instance reads or writes
    (HPAC-REQ-079/080) -- the only input is the `root` the caller
    supplied at construction.
    """

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._path = self._root / _REGISTRY_RELATIVE_PATH

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> _ParsedRegistry:
        reject_symlink(self._root)
        reject_symlink(self._path)
        if not self._path.exists():
            return _ParsedRegistry(schema_version=REGISTRY_SCHEMA_VERSION, principals=(), credentials=())
        document = read_canonical_json_document(self._path)
        return _parse_registry_document(document)

    def _write(self, parsed: _ParsedRegistry) -> None:
        document = {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "principals": [p.to_document() for p in parsed.principals],
            "credentials": [c.to_document() for c in parsed.credentials],
        }
        import json

        payload = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        write_atomic_replace(self._path, payload)
        # Read-back verification (HPAC-REQ-015).
        readback = read_canonical_json_document(self._path)
        if readback != document:
            raise HPACMalformedError("HumanPrincipalRegistry read-back verification failed after write")

    # ── read-only resolution (open to any caller, HPAC-REQ-021) ──────

    def resolve_principal(self, principal_id: str) -> Optional[PrincipalRecord]:
        parsed = self._load()
        for record in parsed.principals:
            if record.principal_id == principal_id:
                return record
        return None

    def resolve_credential(self, credential_id: str) -> Optional[CredentialRecord]:
        parsed = self._load()
        for record in parsed.credentials:
            if record.credential_id == credential_id:
                return record
        return None

    def list_principals(self) -> tuple[PrincipalRecord, ...]:
        return self._load().principals

    def list_credentials(self) -> tuple[CredentialRecord, ...]:
        return self._load().credentials

    # ── preview (never writes, HPAC-REQ-026) ─────────────────────────

    def preview_enroll_principal(self, principal_id: str) -> PreviewResult:
        existing = self.resolve_principal(principal_id)
        if existing is None:
            return PreviewResult("would_enroll")
        if existing.status == "active":
            return PreviewResult("already_enrolled")
        return PreviewResult("conflict", "principal_id previously revoked; identifiers are never reused")

    def preview_revoke_principal(self, principal_id: str) -> PreviewResult:
        existing = self.resolve_principal(principal_id)
        if existing is None:
            return PreviewResult("not_found")
        if existing.status == "revoked":
            return PreviewResult("already_revoked")
        return PreviewResult("would_revoke")

    def preview_enroll_credential(self, credential_id: str, principal_id: str) -> PreviewResult:
        principal = self.resolve_principal(principal_id)
        if principal is None or principal.status != "active":
            return PreviewResult("conflict", "principal missing or not active (HPAC-REQ-027)")
        existing = self.resolve_credential(credential_id)
        if existing is None:
            return PreviewResult("would_enroll")
        if existing.status == "active":
            return PreviewResult("already_enrolled")
        return PreviewResult("conflict", "credential_id previously revoked; identifiers are never reused")

    def preview_revoke_credential(self, credential_id: str) -> PreviewResult:
        existing = self.resolve_credential(credential_id)
        if existing is None:
            return PreviewResult("not_found")
        if existing.status == "revoked":
            return PreviewResult("already_revoked")
        return PreviewResult("would_revoke")

    # ── protected-admin-gated mutation (HPAC-REQ-024/026/028/029) ────

    def enroll_principal(
        self,
        capability: ProtectedAdminCapability,
        *,
        principal_id: str,
        enrollment_provenance_ref: str,
        enrolled_at: str,
    ) -> PrincipalRecord:
        if not isinstance(capability, ProtectedAdminCapability):
            raise HumanPrincipalRegistryError("enroll_principal requires a ProtectedAdminCapability marker")
        parsed = self._load()
        for record in parsed.principals:
            if record.principal_id == principal_id:
                raise HumanPrincipalRegistryConflictError(f"principal_id already exists: {principal_id}")
        new_record = PrincipalRecord(
            principal_id=require_nonempty_str(principal_id, context="enroll_principal.principal_id"),
            status="active",
            enrollment_provenance_ref=require_nonempty_str(
                enrollment_provenance_ref, context="enroll_principal.enrollment_provenance_ref"
            ),
            enrolled_at=require_timestamp(enrolled_at, context="enroll_principal.enrolled_at"),
            revoked_at=None,
        )
        updated = _ParsedRegistry(
            schema_version=parsed.schema_version,
            principals=tuple(sorted((*parsed.principals, new_record), key=lambda p: p.principal_id)),
            credentials=parsed.credentials,
        )
        self._write(updated)
        return new_record

    def revoke_principal(
        self, capability: ProtectedAdminCapability, *, principal_id: str, revoked_at: str
    ) -> PrincipalRecord:
        if not isinstance(capability, ProtectedAdminCapability):
            raise HumanPrincipalRegistryError("revoke_principal requires a ProtectedAdminCapability marker")
        parsed = self._load()
        existing = None
        for record in parsed.principals:
            if record.principal_id == principal_id:
                existing = record
                break
        if existing is None:
            raise HumanPrincipalRegistryNotFoundError(f"unknown principal_id: {principal_id}")
        if existing.status == "revoked":
            return existing  # monotonic idempotent no-op, HPAC-REQ-061
        revoked_record = PrincipalRecord(
            principal_id=existing.principal_id,
            status="revoked",
            enrollment_provenance_ref=existing.enrollment_provenance_ref,
            enrolled_at=existing.enrolled_at,
            revoked_at=require_timestamp(revoked_at, context="revoke_principal.revoked_at"),
        )
        remaining = tuple(r for r in parsed.principals if r.principal_id != principal_id)
        updated = _ParsedRegistry(
            schema_version=parsed.schema_version,
            principals=tuple(sorted((*remaining, revoked_record), key=lambda p: p.principal_id)),
            credentials=parsed.credentials,
        )
        self._write(updated)
        return revoked_record

    def enroll_credential(
        self,
        capability: ProtectedAdminCapability,
        *,
        credential_id: str,
        principal_id: str,
        mechanism_id: str,
        public_key: str,
        assurance_capabilities: tuple[str, ...],
        enrollment_provenance_ref: str,
        enrolled_at: str,
    ) -> CredentialRecord:
        if not isinstance(capability, ProtectedAdminCapability):
            raise HumanPrincipalRegistryError("enroll_credential requires a ProtectedAdminCapability marker")
        parsed = self._load()
        principal = next((p for p in parsed.principals if p.principal_id == principal_id), None)
        if principal is None or principal.status != "active":
            # HPAC-REQ-027: enrolling against a missing or revoked principal fails closed.
            raise HumanPrincipalRegistryConflictError(
                f"cannot enroll credential: principal {principal_id!r} is missing or not active"
            )
        for record in parsed.credentials:
            if record.credential_id == credential_id:
                raise HumanPrincipalRegistryConflictError(f"credential_id already exists: {credential_id}")
        new_record = CredentialRecord(
            credential_id=require_nonempty_str(credential_id, context="enroll_credential.credential_id"),
            principal_id=principal_id,
            mechanism_id=require_nonempty_str(mechanism_id, context="enroll_credential.mechanism_id"),
            public_key=require_nonempty_str(public_key, context="enroll_credential.public_key"),
            assurance_capabilities=tuple(assurance_capabilities),
            status="active",
            enrollment_provenance_ref=require_nonempty_str(
                enrollment_provenance_ref, context="enroll_credential.enrollment_provenance_ref"
            ),
            enrolled_at=require_timestamp(enrolled_at, context="enroll_credential.enrolled_at"),
            revoked_at=None,
        )
        updated = _ParsedRegistry(
            schema_version=parsed.schema_version,
            principals=parsed.principals,
            credentials=tuple(sorted((*parsed.credentials, new_record), key=lambda c: c.credential_id)),
        )
        self._write(updated)
        return new_record

    def revoke_credential(
        self, capability: ProtectedAdminCapability, *, credential_id: str, revoked_at: str
    ) -> CredentialRecord:
        if not isinstance(capability, ProtectedAdminCapability):
            raise HumanPrincipalRegistryError("revoke_credential requires a ProtectedAdminCapability marker")
        parsed = self._load()
        existing = next((c for c in parsed.credentials if c.credential_id == credential_id), None)
        if existing is None:
            raise HumanPrincipalRegistryNotFoundError(f"unknown credential_id: {credential_id}")
        if existing.status == "revoked":
            return existing  # monotonic idempotent no-op, HPAC-REQ-062
        revoked_record = CredentialRecord(
            credential_id=existing.credential_id,
            principal_id=existing.principal_id,
            mechanism_id=existing.mechanism_id,
            public_key=existing.public_key,
            assurance_capabilities=existing.assurance_capabilities,
            status="revoked",
            enrollment_provenance_ref=existing.enrollment_provenance_ref,
            enrolled_at=existing.enrolled_at,
            revoked_at=require_timestamp(revoked_at, context="revoke_credential.revoked_at"),
        )
        remaining = tuple(c for c in parsed.credentials if c.credential_id != credential_id)
        updated = _ParsedRegistry(
            schema_version=parsed.schema_version,
            principals=parsed.principals,
            credentials=tuple(sorted((*remaining, revoked_record), key=lambda c: c.credential_id)),
        )
        self._write(updated)
        return revoked_record


def new_principal_id() -> str:
    return new_hpac_id("hp")


def new_credential_id() -> str:
    return new_hpac_id("hpc")


def principal_digest(record: PrincipalRecord) -> str:
    """Not authority -- a digest match alone never proves canonical
    registry membership (HPAC-REQ-005). Provided only as a convenience
    for audit/equality comparisons of a record already resolved through
    `HumanPrincipalRegistryStore`."""

    return canonical_digest(record.to_document())
