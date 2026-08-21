"""HATP Hardware Credential Registry -- Phase 149O.2, Wave 5.

A provider-owned, protected, read-only registry mapping an enrolled
hardware `signer_key_id` to the cryptographic public-key material a
provider's `verify()` method needs to check a hardware signature
(HATP-REQ-019(e)/HATP-REQ-025: verification uses "independently trusted
public/provider material that does not originate from the proof
itself").

This is deliberately separate from `hatp_bootstrap.py`'s Wave-2
`HATPTrustStore` (principal/signer/authority/deployment-binding facts,
frozen at Wave 2). This module does not modify, import, or depend on
`hatp_bootstrap.py` at all -- it duplicates that module's fixed-path /
symlink-rejection / read-only discipline independently, mirroring the
same dependency-direction discipline `hatp_bootstrap.py` itself already
applies to its own upstream dependency on `repository_identity.py` only
(149O.1D plan §6, and `hatp_bootstrap.py`'s own deliberate duplication
of `_parse_iso_timestamp` rather than importing it).

Wave-2's `SignerRecord` establishes *identity* binding (which principal,
which provider profile) -- it carries no raw cryptographic key material
today, and this module does not add any (that would be a Wave-2 boundary
change, out of Wave-5 scope, item 131). This module supplies the
*cryptographic* binding a provider's `verify()` needs internally: given
a `signer_key_id` already identity-checked by Wave 4 against the Wave-2
trust store, what public key material should a hardware signature be
checked against. `verify_hatp_proof` (Wave 4) never reads this registry
directly and never gains a new parameter for it -- only a concrete
provider (`hatp_fido2_provider.py`, `hatp_piv_provider.py`) does, fully
inside the opaque `provider.verify()` call Wave 4 already makes.

Enrollment (writing a new credential into this registry) is explicitly
OUT of Wave-5 scope -- HATP-001/149O.1D assign registry-mutation to a
future Human/Admin-only administrative surface (Wave 2/7 territory,
mirroring `hatp_bootstrap.py`'s own enroll/grant/revoke deferral). This
module therefore exposes no `enroll()`/`revoke()`/`rotate()` production
API; only a read-only lookup, exactly mirroring `HATPTrustStore`'s own
read-only discipline. The production root is never caller-selectable:
no constructor parameter, CLI flag, or environment variable accepted by
`.production()`.
"""
from __future__ import annotations

import json
import os
import stat
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

REGISTRY_SCHEMA_VERSION = 1
_REGISTRY_FILE_NAME = "hardware-credentials.json"
_STATUS_VALUES = frozenset({"active", "revoked"})
#: HRWP-REQ-019 (v1.1): additively widened to include "WEBAUTHN" for
#: remote-WebAuthn-enrolled records (HATP_HARDWARE_PROVIDER_V1_REMOTE_
#: WEBAUTHN). This widening is vocabulary-only -- no schema change, and
#: no production factory dispatch to a remote provider (see
#: `hatp_providers.py::_PRODUCTION_HARDWARE_PROVIDER_PROFILES`, unchanged
#: by this widening). Unknown values remain rejected fail-closed.
_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV", "WEBAUTHN"})

# Fixed, platform-level protected locations -- deliberately not derived
# from `Path.home()`, `os.path.expanduser`, `getpass.getuser()`, or any
# environment variable, for the same reasons `hatp_bootstrap.py`'s own
# `_default_production_trust_root` documents (149O.1F.1 repair of
# B-149O.1F-1: the "agent-home trap"). A sibling directory of the Wave-2
# trust-store root, not inside it -- this registry is a distinct
# protected artifact with its own read-only discipline.
_MACOS_FIXED_CREDENTIAL_ROOT = Path("/Library/Application Support/PCAE/HATP/hardware-credentials")
_LINUX_FIXED_CREDENTIAL_ROOT = Path("/etc/pcae/hatp/hardware-credentials")


class HATPHardwareCredentialStoreError(Exception):
    """Base error for the protected hardware-credential registry."""


class HATPHardwareCredentialStoreMalformedError(HATPHardwareCredentialStoreError):
    """The registry document exists but fails strict validation, or
    contains an ambiguous duplicate record. Never partially accepted."""


class HATPHardwareCredentialStoreUnsupportedPlatformError(HATPHardwareCredentialStoreError):
    """The current platform has no fixed-root implementation. Fails
    closed rather than falling back to any environment-derived
    location."""


class HATPHardwareCredentialStoreSymlinkError(HATPHardwareCredentialStoreError):
    """The credential-store root or registry file position is (or
    resolves through) a symlink. Refused rather than followed."""


@dataclass(frozen=True)
class HardwareCredentialRecord:
    """One enrolled hardware credential's public identity. Carries no
    private-key material, no PIN, no secret device state (item 73).

    `public_key` is protocol-native public-key encoding: for FIDO2, this
    is CBOR-encoded COSE_Key bytes -- the exact byte format
    `Fido2HardwareProvider.verify()` already consumes via
    `CoseKey.parse(cbor.decode(record.public_key))` (`hatp_fido2_provider.py`).
    HHCE-001 v1.0's original text described this field as "DER
    SubjectPublicKeyInfo," which never matched this verifier's actual
    behavior -- repaired to v1.1 alongside Phase 149O.20L.7O.2F's
    implementation (NBF-149O.20L.7O.2E.1-1)."""

    signer_key_id: str
    provider_profile: str
    protocol_name: str  # "FIDO2" | "PIV" | "WEBAUTHN"
    algorithm: str  # e.g. "ES256" (COSE algorithm identifier name)
    public_key: bytes  # protocol-native encoding (FIDO2: CBOR COSE_Key)
    status: str  # "active" | "revoked"
    #: Widened per HHCE-REQ-008 (closes NBF-2): null/absent while
    #: `status == "active"`, mandatory grammar-valid timestamp while
    #: `status == "revoked"`. Identical discipline to
    #: `hatp_bootstrap.SignerRecord.revoked_at`.
    revoked_at: Optional[str] = None


def _default_production_credential_root() -> Path:
    """The authoritative production credential-registry root: a fixed,
    platform-level path independent of `Path.home()`, `os.environ`, the
    current working directory, repository state, or any caller-supplied
    argument. Never `repo/.pcae/**` -- repository-local storage is
    agent-writable and cannot be a trust anchor."""

    if os.name != "posix":
        raise HATPHardwareCredentialStoreUnsupportedPlatformError(
            f"HATP hardware credential registry has no implementation for platform {os.name!r}; failing closed."
        )
    if sys.platform == "darwin":
        return _MACOS_FIXED_CREDENTIAL_ROOT
    if sys.platform == "linux":
        return _LINUX_FIXED_CREDENTIAL_ROOT
    raise HATPHardwareCredentialStoreUnsupportedPlatformError(
        f"HATP hardware credential registry has no fixed-root implementation for platform {sys.platform!r}; failing closed."
    )


def _parse_iso_timestamp(value: object) -> Optional[datetime]:
    """Duplicated deliberately from `hatp_bootstrap.py::_parse_iso_timestamp`
    (itself duplicated from `repository_identity.py`) rather than
    imported, to keep this module's dependency graph independent of
    `hatp_bootstrap.py` (this module's own docstring's stated
    discipline)."""

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


def _require_timestamp(value: object, *, context: str) -> str:
    if _parse_iso_timestamp(value) is None:
        raise HATPHardwareCredentialStoreMalformedError(
            f"{context}: expected a timezone-aware ISO-8601 timestamp, got {value!r}"
        )
    return value  # type: ignore[return-value]


def _require_revoked_at_consistency(status: str, revoked_at: object, *, context: str) -> Optional[str]:
    """HHCE-REQ-009: identical `_require_revoked_at_consistency` discipline
    to `hatp_bootstrap.py`, duplicated not imported (module independence,
    see module docstring)."""

    if status == "revoked":
        if revoked_at is None:
            raise HATPHardwareCredentialStoreMalformedError(f"{context}: status is 'revoked' but revoked_at is missing")
        return _require_timestamp(revoked_at, context=f"{context}.revoked_at")
    if revoked_at is not None:
        raise HATPHardwareCredentialStoreMalformedError(f"{context}: status is 'active' but revoked_at is set")
    return None


def _reject_symlink(target: Path) -> None:
    if target.is_symlink():
        raise HATPHardwareCredentialStoreSymlinkError(
            f"HATP hardware credential registry path is a symlink, refusing: {target}"
        )


def _reject_duplicate_keys(pairs: list) -> dict:
    """Duplicated deliberately from
    `human_approval_trusted_provenance.py::_reject_duplicate_keys`
    rather than imported, to keep this module's dependency graph
    independent (same discipline `hatp_bootstrap.py` documents for its
    own duplicated `_parse_iso_timestamp`)."""

    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise HATPHardwareCredentialStoreMalformedError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


_CREDENTIAL_ALLOWED_FIELDS = frozenset(
    {"signer_key_id", "provider_profile", "protocol_name", "algorithm", "public_key_hex", "status", "revoked_at"}
)


def _parse_credential(raw: object) -> HardwareCredentialRecord:
    if not isinstance(raw, dict):
        raise HATPHardwareCredentialStoreMalformedError("credential record must be a JSON object")
    unknown = set(raw.keys()) - _CREDENTIAL_ALLOWED_FIELDS
    if unknown:
        raise HATPHardwareCredentialStoreMalformedError(f"credential record has unrecognized fields: {sorted(unknown)}")
    try:
        signer_key_id = raw["signer_key_id"]
        provider_profile = raw["provider_profile"]
        protocol_name = raw["protocol_name"]
        algorithm = raw["algorithm"]
        public_key_hex = raw["public_key_hex"]
        status = raw["status"]
    except KeyError as exc:
        raise HATPHardwareCredentialStoreMalformedError(f"malformed hardware credential record, missing {exc}") from exc

    if not isinstance(signer_key_id, str) or not signer_key_id:
        raise HATPHardwareCredentialStoreMalformedError("signer_key_id must be a non-empty string")
    if not isinstance(provider_profile, str) or not provider_profile:
        raise HATPHardwareCredentialStoreMalformedError("provider_profile must be a non-empty string")
    if protocol_name not in _PROTOCOL_VALUES:
        raise HATPHardwareCredentialStoreMalformedError(f"invalid protocol_name: {protocol_name!r}")
    if not isinstance(algorithm, str) or not algorithm:
        raise HATPHardwareCredentialStoreMalformedError("algorithm must be a non-empty string")
    if status not in _STATUS_VALUES:
        raise HATPHardwareCredentialStoreMalformedError(f"invalid status: {status!r}")
    if not isinstance(public_key_hex, str):
        raise HATPHardwareCredentialStoreMalformedError("public_key_hex must be a string")
    try:
        public_key = bytes.fromhex(public_key_hex)
    except ValueError as exc:
        raise HATPHardwareCredentialStoreMalformedError(f"public_key_hex must be valid hex: {exc}") from exc
    revoked_at = _require_revoked_at_consistency(status, raw.get("revoked_at"), context=f"credential[{signer_key_id}]")

    return HardwareCredentialRecord(
        signer_key_id=signer_key_id,
        provider_profile=provider_profile,
        protocol_name=protocol_name,
        algorithm=algorithm,
        public_key=public_key,
        status=status,
        revoked_at=revoked_at,
    )


@dataclass(frozen=True)
class _ParsedCredentialRegistry:
    schema_version: int
    credentials: Dict[str, HardwareCredentialRecord]


def _parse_credential_registry_document(document: object) -> "_ParsedCredentialRegistry":
    """Document-level parse (HHCE-REQ-003/024): the shared parser both
    the read-only `HATPHardwareCredentialStore` and the future writer
    (`hatp_hardware_credential_admin.py`) use, mirroring
    `hatp_bootstrap._parse_registry_document`'s exact discipline.
    `schema_version` defaults to `REGISTRY_SCHEMA_VERSION` when absent
    for backwards compatibility with documents written before HHCE-001
    v1.0 added the field -- an explicit mismatching value still fails
    closed."""

    if not isinstance(document, dict):
        raise HATPHardwareCredentialStoreMalformedError("registry document must be a JSON object")
    allowed_top = {"schema_version", "credentials"}
    unknown_top = set(document.keys()) - allowed_top
    if unknown_top:
        raise HATPHardwareCredentialStoreMalformedError(
            f"registry document has unrecognized top-level fields: {sorted(unknown_top)}"
        )
    schema_version = document.get("schema_version", REGISTRY_SCHEMA_VERSION)
    if schema_version != REGISTRY_SCHEMA_VERSION:
        raise HATPHardwareCredentialStoreMalformedError(
            f"schema_version {schema_version!r} is not supported (expected {REGISTRY_SCHEMA_VERSION})"
        )
    raw_credentials = document.get("credentials", [])
    if not isinstance(raw_credentials, list):
        raise HATPHardwareCredentialStoreMalformedError("credentials must be a JSON array")
    credentials: Dict[str, HardwareCredentialRecord] = {}
    for raw in raw_credentials:
        record = _parse_credential(raw)
        if record.signer_key_id in credentials:
            raise HATPHardwareCredentialStoreMalformedError(f"duplicate conflicting credential record: {record.signer_key_id}")
        credentials[record.signer_key_id] = record
    return _ParsedCredentialRegistry(schema_version=schema_version, credentials=credentials)


def inspect_credential_store_environment(store_root: Path) -> "CredentialStoreEnvironmentResult":
    """Machine-verifiable readiness only, mirroring
    `hatp_bootstrap.inspect_bootstrap_environment`'s exact discipline
    (duplicated, not imported): file ownership/permissions of the
    credential-store root."""

    if os.name != "posix":
        return CredentialStoreEnvironmentResult("UNAVAILABLE", ("unsupported_platform",))

    if store_root.is_symlink():
        return CredentialStoreEnvironmentResult("UNSAFE_CONFIGURATION", ("credential_store_root_is_symlink",))

    if not store_root.exists():
        return CredentialStoreEnvironmentResult("UNAVAILABLE", ("credential_store_missing",))

    reasons: list = []
    store_stat = store_root.stat()
    mode = stat.S_IMODE(store_stat.st_mode)
    if mode & (stat.S_IWGRP | stat.S_IWOTH):
        reasons.append("credential_store_group_or_other_writable")

    parent = store_root.parent
    if parent.exists() and not parent.is_symlink():
        parent_stat = parent.stat()
        parent_mode = stat.S_IMODE(parent_stat.st_mode)
        if parent_mode & stat.S_IWOTH:
            reasons.append("credential_store_parent_world_writable")

    if reasons:
        return CredentialStoreEnvironmentResult("UNSAFE_CONFIGURATION", tuple(reasons))
    return CredentialStoreEnvironmentResult("READY", ())


@dataclass(frozen=True)
class CredentialStoreEnvironmentResult:
    status: str  # "READY" | "UNAVAILABLE" | "UNSAFE_CONFIGURATION"
    reasons: tuple


class HATPHardwareCredentialStore:
    """Read-only lookup interface over the protected hardware-credential
    registry. No method here mutates state -- enrollment/revocation are
    administrative-surface-only and not implemented by this module at
    all. The constructor accepts only a private, test-only root
    override; production code MUST use `.production()`, which accepts
    no path, environment variable, or CLI-sourced override."""

    def __init__(self, *, _test_only_root: Optional[Path] = None) -> None:
        if _test_only_root is not None:
            self._root = Path(_test_only_root)
        else:
            self._root = _default_production_credential_root()

    @classmethod
    def production(cls) -> "HATPHardwareCredentialStore":
        """The only production construction path. Accepts no argument."""

        return cls()

    @property
    def root(self) -> Path:
        return self._root

    def _registry_path(self) -> Path:
        return self._root / _REGISTRY_FILE_NAME

    def environment_status(self) -> CredentialStoreEnvironmentResult:
        return inspect_credential_store_environment(self._root)

    def _load_registry(self) -> Optional["_ParsedCredentialRegistry"]:
        registry_path = self._registry_path()
        _reject_symlink(self._root)
        _reject_symlink(registry_path)
        if not registry_path.exists():
            return None
        raw = registry_path.read_text(encoding="utf-8")
        try:
            document = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
        except json.JSONDecodeError as exc:
            raise HATPHardwareCredentialStoreMalformedError(f"registry document is not valid JSON: {exc}") from exc
        return _parse_credential_registry_document(document)

    def lookup_credential(self, signer_key_id: str) -> Optional[HardwareCredentialRecord]:
        """Look up the enrolled public-key material for `signer_key_id`.
        Returns `None` if no credential is enrolled -- callers MUST
        treat that as fail-closed (unknown credential), never as an
        implicit trust grant."""

        registry = self._load_registry()
        if registry is None:
            return None
        return registry.credentials.get(signer_key_id)
