"""HATP Protected Trust Store / Authority Registry foundation — Phase
149O.1E, Wave 2.

Implements CRI Model A's Layer 2 (the admin-owned protected deployment
binding, HATP-REQ-052-066) plus the trusted bootstrap store's
principal/signer/authority registry (HATP-REQ-006, HATP-REQ-030-045,
HATP-REQ-086-089). This module builds on `repository_identity.py`'s
Layer 1 `repository_instance_id` (dependency direction A -> C, 149O.1D
plan §6) but has no knowledge of HATP proofs, the Permission Broker,
RAE, or any consumer of `approval_present` -- it is read-only production
substrate, not a verifier (HATP-REQ-094: verifier code has no write
access to this store; this module does not implement a verifier at
all).

Frozen invariants preserved by this module (149O.1D plan §14, §25,
§62-70):

- No production, agent-reachable API exposes `enroll()`, `grant()`,
  `revoke()`, or `rotate()`. Those live on a future, separate,
  Human/Admin-only administrative surface not implemented by this
  phase.
- The production trust-store location is never caller-selectable: no
  constructor parameter, CLI flag, or environment variable accepted by
  `HATPTrustStore.production()`. Test-only injection exists structurally
  outside the production constructor (`HATPTrustStore` directly, never
  reachable through `.production()`).
- No import from `rollback_approval_evidence.py`, `permission_broker.py`,
  `permission_broker_foundation.py`, `agent.py`, or
  `commands/agent.py` -- this module stays HATP/RAE/Permission-Broker
  independent.
- Repository identity generation grants no authority by itself; this
  module is what refuses to honor a copied/stolen `repository_id`
  without a matching `canonical_deployment_root` (HATP-REQ-057-063).
"""
from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pcae.core.repository_identity import is_valid_repository_instance_id

REGISTRY_SCHEMA_VERSION = 1

_STATUS_VALUES = frozenset({"active", "revoked"})


class HATPTrustStoreError(Exception):
    """Base error for protected trust-store operations."""


class HATPTrustStoreMalformedError(HATPTrustStoreError):
    """The registry document exists but fails strict validation, or
    contains an ambiguous duplicate record. Never partially accepted
    (governing-prompt item 69)."""


class HATPBootstrapUnsupportedPlatformError(HATPTrustStoreError):
    """The current platform has no bootstrap-environment readiness
    implementation. Fails closed -- never silently reports readiness by
    omission (149O.1D plan §15-18)."""


class HATPTrustStoreSymlinkError(HATPTrustStoreError):
    """The trust-store root or registry file position is (or resolves
    through) a symlink. Refused rather than followed."""


def _parse_iso_timestamp(value: object) -> Optional[datetime]:
    """Duplicated deliberately from `repository_identity.py` /
    `rollback_approval_evidence.py::_parse_iso_timestamp` (149O.1D plan
    §5.13) rather than imported, to keep this module's only upstream
    dependency `repository_identity.py` (A -> C, §6) and independent of
    RAE (§62-70 boundary)."""

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


# ═══════════════════════════════════════════════════════════════════════════
# Data models
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PrincipalRecord:
    principal_id: str
    status: str


@dataclass(frozen=True)
class SignerRecord:
    signer_key_id: str
    principal_id: str
    provider_profile: str
    status: str
    revoked_at: Optional[str] = None


@dataclass(frozen=True)
class AuthorityRecord:
    principal_id: str
    repository_id: str
    authority_scope: str
    status: str
    valid_from: str
    revoked_at: Optional[str] = None


@dataclass(frozen=True)
class DeploymentBinding:
    repository_id: str
    canonical_deployment_root: str
    principal_id: str
    signer_key_id: str
    provider_profile: str
    authority_scope: str
    valid_from: str
    status: str
    revoked_at: Optional[str] = None


class BootstrapEnvironmentStatus(str, Enum):
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"
    UNSAFE_CONFIGURATION = "UNSAFE_CONFIGURATION"


@dataclass(frozen=True)
class BootstrapEnvironmentResult:
    status: BootstrapEnvironmentStatus
    reasons: tuple[str, ...]


# ═══════════════════════════════════════════════════════════════════════════
# Canonical deployment root resolution (HATP-REQ-053)
# ═══════════════════════════════════════════════════════════════════════════


def resolve_canonical_deployment_root(path: Path) -> str:
    """Deterministic canonicalization of a local deployment root: absolute
    path, symlink resolution, platform normalization. Never trusts a raw
    caller-supplied path string as-is (HATP-REQ-053).

    This resolves the *subject* directory itself (there is no separate
    trusted containment root to check against, unlike the trust-store
    path below) -- it therefore cannot and does not claim symlink-escape
    containment; it only guarantees the same physical directory always
    canonicalizes to the same string, which is what deployment-root
    comparison actually needs."""

    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    normalized = Path(os.path.normpath(str(candidate)))
    resolved = normalized.resolve(strict=True)
    return resolved.as_posix()


def deployment_binding_matches(
    binding: Optional[DeploymentBinding],
    *,
    repository_id: str,
    canonical_deployment_root: str,
) -> bool:
    """The load-bearing copy/clone/theft defense (HATP-REQ-057-063): a
    binding only matches when both the `repository_id` (Layer 1) and the
    `canonical_deployment_root` (Layer 2) agree, and the binding is not
    revoked. A copied `repository_id` at the wrong root, or the right
    root with the wrong id, both return `False`."""

    if binding is None:
        return False
    if binding.status != "active":
        return False
    return (
        binding.repository_id == repository_id
        and binding.canonical_deployment_root == canonical_deployment_root
    )


# ═══════════════════════════════════════════════════════════════════════════
# Production trust-store location (HATP-REQ-030-035)
# ═══════════════════════════════════════════════════════════════════════════

_REGISTRY_FILE_NAME = "registry.json"


def _default_production_trust_root() -> Path:
    """User-level protected directory under the admin principal's own
    home directory (149O.1D plan §13's illustrative candidate B). Never
    `repo/.pcae/**` (HATP-REQ-032/149O.1B.1 §12's explicit prohibition:
    repository-local storage is agent-writable and cannot be the trust
    anchor). Not influenced by any environment variable or CLI flag
    (HATP-REQ-034/035)."""

    if os.name != "posix":
        raise HATPBootstrapUnsupportedPlatformError(
            f"HATP bootstrap trust store has no implementation for platform {os.name!r}; failing closed."
        )
    return Path.home() / ".pcae-hatp" / "trust-store"


def _reject_symlink(target: Path) -> None:
    if target.is_symlink():
        raise HATPTrustStoreSymlinkError(f"HATP trust-store path is a symlink, refusing: {target}")


# ═══════════════════════════════════════════════════════════════════════════
# Registry document validation (strict, closed schema)
# ═══════════════════════════════════════════════════════════════════════════


def _require_status(value: object, *, context: str) -> str:
    if value not in _STATUS_VALUES:
        raise HATPTrustStoreMalformedError(f"{context}: status must be one of {sorted(_STATUS_VALUES)}, got {value!r}")
    return value


def _require_nonempty_str(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise HATPTrustStoreMalformedError(f"{context}: expected a non-empty string, got {value!r}")
    return value


def _require_timestamp(value: object, *, context: str) -> str:
    if _parse_iso_timestamp(value) is None:
        raise HATPTrustStoreMalformedError(f"{context}: expected a timezone-aware ISO-8601 timestamp, got {value!r}")
    return value  # type: ignore[return-value]


def _require_revoked_at_consistency(status: str, revoked_at: object, *, context: str) -> Optional[str]:
    if status == "revoked":
        if revoked_at is None:
            raise HATPTrustStoreMalformedError(f"{context}: status is 'revoked' but revoked_at is missing")
        return _require_timestamp(revoked_at, context=f"{context}.revoked_at")
    if revoked_at is not None:
        raise HATPTrustStoreMalformedError(f"{context}: status is 'active' but revoked_at is set")
    return None


def _parse_principal(document: dict) -> PrincipalRecord:
    allowed = {"principal_id", "status"}
    unknown = set(document.keys()) - allowed
    if unknown:
        raise HATPTrustStoreMalformedError(f"principal record has unrecognized fields: {sorted(unknown)}")
    principal_id = _require_nonempty_str(document.get("principal_id"), context="principal.principal_id")
    status = _require_status(document.get("status"), context=f"principal[{principal_id}]")
    return PrincipalRecord(principal_id=principal_id, status=status)


def _parse_signer(document: dict) -> SignerRecord:
    allowed = {"signer_key_id", "principal_id", "provider_profile", "status", "revoked_at"}
    unknown = set(document.keys()) - allowed
    if unknown:
        raise HATPTrustStoreMalformedError(f"signer record has unrecognized fields: {sorted(unknown)}")
    signer_key_id = _require_nonempty_str(document.get("signer_key_id"), context="signer.signer_key_id")
    principal_id = _require_nonempty_str(document.get("principal_id"), context=f"signer[{signer_key_id}].principal_id")
    provider_profile = _require_nonempty_str(
        document.get("provider_profile"), context=f"signer[{signer_key_id}].provider_profile"
    )
    status = _require_status(document.get("status"), context=f"signer[{signer_key_id}]")
    revoked_at = _require_revoked_at_consistency(status, document.get("revoked_at"), context=f"signer[{signer_key_id}]")
    return SignerRecord(
        signer_key_id=signer_key_id,
        principal_id=principal_id,
        provider_profile=provider_profile,
        status=status,
        revoked_at=revoked_at,
    )


def _parse_authority(document: dict) -> AuthorityRecord:
    allowed = {"principal_id", "repository_id", "authority_scope", "status", "valid_from", "revoked_at"}
    unknown = set(document.keys()) - allowed
    if unknown:
        raise HATPTrustStoreMalformedError(f"authority record has unrecognized fields: {sorted(unknown)}")
    principal_id = _require_nonempty_str(document.get("principal_id"), context="authority.principal_id")
    repository_id = document.get("repository_id")
    if not is_valid_repository_instance_id(repository_id):
        raise HATPTrustStoreMalformedError(f"authority[{principal_id}]: repository_id is not a valid UUID4 string")
    authority_scope = _require_nonempty_str(
        document.get("authority_scope"), context=f"authority[{principal_id}/{repository_id}].authority_scope"
    )
    status = _require_status(document.get("status"), context=f"authority[{principal_id}/{repository_id}]")
    valid_from = _require_timestamp(
        document.get("valid_from"), context=f"authority[{principal_id}/{repository_id}].valid_from"
    )
    revoked_at = _require_revoked_at_consistency(
        status, document.get("revoked_at"), context=f"authority[{principal_id}/{repository_id}]"
    )
    return AuthorityRecord(
        principal_id=principal_id,
        repository_id=repository_id,
        authority_scope=authority_scope,
        status=status,
        valid_from=valid_from,
        revoked_at=revoked_at,
    )


def _parse_deployment_binding(document: dict) -> DeploymentBinding:
    allowed = {
        "repository_id",
        "canonical_deployment_root",
        "principal_id",
        "signer_key_id",
        "provider_profile",
        "authority_scope",
        "valid_from",
        "status",
        "revoked_at",
    }
    unknown = set(document.keys()) - allowed
    if unknown:
        raise HATPTrustStoreMalformedError(f"deployment binding has unrecognized fields: {sorted(unknown)}")
    repository_id = document.get("repository_id")
    if not is_valid_repository_instance_id(repository_id):
        raise HATPTrustStoreMalformedError("deployment binding: repository_id is not a valid UUID4 string")
    canonical_deployment_root = _require_nonempty_str(
        document.get("canonical_deployment_root"), context=f"binding[{repository_id}].canonical_deployment_root"
    )
    principal_id = _require_nonempty_str(document.get("principal_id"), context=f"binding[{repository_id}].principal_id")
    signer_key_id = _require_nonempty_str(document.get("signer_key_id"), context=f"binding[{repository_id}].signer_key_id")
    provider_profile = _require_nonempty_str(
        document.get("provider_profile"), context=f"binding[{repository_id}].provider_profile"
    )
    authority_scope = _require_nonempty_str(
        document.get("authority_scope"), context=f"binding[{repository_id}].authority_scope"
    )
    status = _require_status(document.get("status"), context=f"binding[{repository_id}]")
    valid_from = _require_timestamp(document.get("valid_from"), context=f"binding[{repository_id}].valid_from")
    revoked_at = _require_revoked_at_consistency(
        status, document.get("revoked_at"), context=f"binding[{repository_id}]"
    )
    return DeploymentBinding(
        repository_id=repository_id,
        canonical_deployment_root=canonical_deployment_root,
        principal_id=principal_id,
        signer_key_id=signer_key_id,
        provider_profile=provider_profile,
        authority_scope=authority_scope,
        valid_from=valid_from,
        status=status,
        revoked_at=revoked_at,
    )


@dataclass(frozen=True)
class _ParsedRegistry:
    principals: dict[str, PrincipalRecord]
    signers: dict[str, SignerRecord]
    deployment_bindings: dict[str, DeploymentBinding]
    authorities: dict[tuple[str, str], AuthorityRecord]


def _parse_registry_document(document: object) -> _ParsedRegistry:
    if not isinstance(document, dict):
        raise HATPTrustStoreMalformedError("registry document is not a JSON object")

    allowed_top = {"registry_version", "principals", "signers", "deployment_bindings", "authorities"}
    unknown_top = set(document.keys()) - allowed_top
    if unknown_top:
        raise HATPTrustStoreMalformedError(f"registry document has unrecognized top-level fields: {sorted(unknown_top)}")

    registry_version = document.get("registry_version")
    if registry_version != REGISTRY_SCHEMA_VERSION:
        raise HATPTrustStoreMalformedError(
            f"registry_version {registry_version!r} is not supported (expected {REGISTRY_SCHEMA_VERSION})"
        )

    principals: dict[str, PrincipalRecord] = {}
    for raw in document.get("principals", []) or []:
        record = _parse_principal(raw)
        if record.principal_id in principals:
            raise HATPTrustStoreMalformedError(f"duplicate conflicting principal record: {record.principal_id}")
        principals[record.principal_id] = record

    signers: dict[str, SignerRecord] = {}
    for raw in document.get("signers", []) or []:
        record = _parse_signer(raw)
        if record.signer_key_id in signers:
            raise HATPTrustStoreMalformedError(f"duplicate conflicting signer record: {record.signer_key_id}")
        signers[record.signer_key_id] = record

    deployment_bindings: dict[str, DeploymentBinding] = {}
    for raw in document.get("deployment_bindings", []) or []:
        record = _parse_deployment_binding(raw)
        if record.repository_id in deployment_bindings:
            raise HATPTrustStoreMalformedError(f"duplicate conflicting deployment binding: {record.repository_id}")
        deployment_bindings[record.repository_id] = record

    authorities: dict[tuple[str, str], AuthorityRecord] = {}
    for raw in document.get("authorities", []) or []:
        record = _parse_authority(raw)
        key = (record.principal_id, record.repository_id)
        if key in authorities:
            raise HATPTrustStoreMalformedError(f"duplicate conflicting authority record: {key}")
        authorities[key] = record

    return _ParsedRegistry(
        principals=principals,
        signers=signers,
        deployment_bindings=deployment_bindings,
        authorities=authorities,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Bootstrap environment readiness (HATP-REQ-026-029, HATP-REQ-090-093)
# ═══════════════════════════════════════════════════════════════════════════


def inspect_bootstrap_environment(store_root: Path) -> BootstrapEnvironmentResult:
    """Machine-verifiable readiness only (149O.1D plan §16's three-tier
    distinction): file ownership/permissions of the trust-store root, and
    whether the Agent OS principal and the store-owning principal are the
    same OS user. This does NOT and cannot mechanically prove the absence
    of a privilege-escalation path (`sudo`, setuid, group membership) --
    that remains a deployment-verification obligation (Wave 7), never
    overclaimed here (governing-prompt item 35)."""

    if os.name != "posix":
        return BootstrapEnvironmentResult(BootstrapEnvironmentStatus.UNAVAILABLE, ("unsupported_platform",))

    if store_root.is_symlink():
        return BootstrapEnvironmentResult(BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION, ("trust_store_root_is_symlink",))

    if not store_root.exists():
        return BootstrapEnvironmentResult(BootstrapEnvironmentStatus.UNAVAILABLE, ("trust_store_missing",))

    reasons: list[str] = []
    store_stat = store_root.stat()
    mode = stat.S_IMODE(store_stat.st_mode)
    if mode & (stat.S_IWGRP | stat.S_IWOTH):
        reasons.append("trust_store_group_or_other_writable")

    parent = store_root.parent
    if parent.exists():
        if parent.is_symlink():
            reasons.append("trust_store_parent_is_symlink")
        else:
            parent_stat = parent.stat()
            parent_mode = stat.S_IMODE(parent_stat.st_mode)
            if parent_mode & stat.S_IWOTH:
                reasons.append("trust_store_parent_world_writable")
            if parent_stat.st_uid != store_stat.st_uid:
                reasons.append("trust_store_parent_owner_mismatch")

    current_uid = os.getuid()
    if store_stat.st_uid == current_uid:
        reasons.append("agent_and_admin_share_os_principal")

    if reasons:
        return BootstrapEnvironmentResult(BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION, tuple(reasons))
    return BootstrapEnvironmentResult(BootstrapEnvironmentStatus.READY, ())


# ═══════════════════════════════════════════════════════════════════════════
# HATPTrustStore -- read-only production/verification interface
# ═══════════════════════════════════════════════════════════════════════════


class HATPTrustStore:
    """Read-only lookup interface over the protected trust registry.

    No method here mutates state (HATP-REQ-036-042: enrollment,
    revocation, and rotation are administrative-surface-only and are not
    implemented by this phase at all). The constructor accepts only a
    private, test-only override; ordinary production code MUST use
    `HATPTrustStore.production()`, which accepts no path argument."""

    def __init__(self, *, _test_only_root: Optional[Path] = None) -> None:
        if _test_only_root is not None:
            self._root = Path(_test_only_root)
        else:
            self._root = _default_production_trust_root()

    @classmethod
    def production(cls) -> "HATPTrustStore":
        """The only production construction path. Accepts no path,
        environment variable, or CLI-sourced override (HATP-REQ-034/035)."""

        return cls()

    @property
    def root(self) -> Path:
        return self._root

    def _registry_path(self) -> Path:
        return self._root / _REGISTRY_FILE_NAME

    def _load_registry(self) -> Optional[_ParsedRegistry]:
        registry_path = self._registry_path()
        _reject_symlink(self._root)
        _reject_symlink(registry_path)
        if not registry_path.exists():
            return None
        raw = registry_path.read_text(encoding="utf-8")
        try:
            document = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HATPTrustStoreMalformedError(f"registry document is not valid JSON: {exc}") from exc
        return _parse_registry_document(document)

    def environment_status(self) -> BootstrapEnvironmentResult:
        try:
            registry = self._load_registry()
        except HATPTrustStoreError:
            return BootstrapEnvironmentResult(BootstrapEnvironmentStatus.UNSAFE_CONFIGURATION, ("trust_store_malformed",))
        if registry is None:
            return BootstrapEnvironmentResult(BootstrapEnvironmentStatus.UNAVAILABLE, ("trust_store_missing",))
        return inspect_bootstrap_environment(self._root)

    def load_repository_enrollment(self, repository_id: str) -> Optional[DeploymentBinding]:
        registry = self._load_registry()
        if registry is None:
            return None
        return registry.deployment_bindings.get(repository_id)

    def lookup_principal(self, principal_id: str) -> Optional[PrincipalRecord]:
        registry = self._load_registry()
        if registry is None:
            return None
        return registry.principals.get(principal_id)

    def lookup_signer(self, signer_key_id: str) -> Optional[SignerRecord]:
        registry = self._load_registry()
        if registry is None:
            return None
        return registry.signers.get(signer_key_id)

    def lookup_authority(self, principal_id: str, repository_id: str) -> Optional[AuthorityRecord]:
        registry = self._load_registry()
        if registry is None:
            return None
        return registry.authorities.get((principal_id, repository_id))

    def signer_revoked(self, signer_key_id: str) -> bool:
        record = self.lookup_signer(signer_key_id)
        if record is None:
            return False
        return record.status == "revoked"

    def resolve_deployment_authorization(
        self, *, repository_id: str, canonical_deployment_root: str
    ) -> Optional[DeploymentBinding]:
        """Strict Layer-1 + Layer-2 match (HATP-REQ-062, HATP-REQ-081/082):
        a binding registered for `repository_id` at a *different* root is
        deliberately not returned here -- callers must never treat a
        same-ID/wrong-root lookup as authorized."""

        binding = self.load_repository_enrollment(repository_id)
        if not deployment_binding_matches(
            binding, repository_id=repository_id, canonical_deployment_root=canonical_deployment_root
        ):
            return None
        return binding
