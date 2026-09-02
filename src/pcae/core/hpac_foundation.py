"""Shared HPAC-001 v2.0 trust-store foundation.

The public HPAC dataclasses are data. Authority is established separately by
an :class:`HPACStoreAuthority`, an opaque writer capability bound to that
authority, protected canonical store state, and a resolver-produced
``HPACResolvedRecord``. Serialized fields, public digests, and paths never
serialize the in-process authority seal.

``HPACStoreAuthority.writer()`` deliberately exposes only fixture writer
capabilities. They are permanently ``FIXTURE_NON_REAL`` and therefore cannot
qualify for real-runtime human authority.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 (HPAC-PAWA-001 v1.1 Slice 1) adds
the ``PRODUCTION`` writer-capability minting *primitive*
(``_mint_production_writer_capability`` — a single, seal-guarded low-level
factory reachable only from the non-agent-importable
``hpac_protected_admin_writer`` module, HPAC-PAWA-REQ-081/084). ``writer()``
still raises for every non-``FIXTURE_NON_REAL`` class — there is intentionally
no public production-writer factory on this class, and a fixture writer can
never authorize a production store. The §33 positive recognition sequence,
the ``.authority/`` descriptor / current-generation / agent-exclusion I/O,
the one-operation lifetime, and the failure taxonomy all live in
``hpac_protected_admin_writer`` / ``hpac_pawa_agent_exclusion`` /
``hpac_pawa_schemas``, never here.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import sys
import tempfile
import threading
import unicodedata
import uuid
from collections.abc import Mapping
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Generic, Optional, TypeVar

from pcae.core.runtime_authority import compute_canonical_digest

__all__ = [
    "HPACFoundationError",
    "HPACSymlinkError",
    "HPACMalformedError",
    "HPACCorruptionError",
    "HPACDuplicateError",
    "HPACAuthorityError",
    "HPACUnsupportedPlatformError",
    "HPACAuthorityClass",
    "HPACStoreAuthority",
    "HPACWriterCapability",
    "HPACResolvedRecord",
    "ProtectedAdminCapability",
    "canonical_digest",
    "canonical_json_bytes",
    "resolve_hpac_protected_root",
    "reject_symlink",
    "require_nonempty_str",
    "require_status",
    "require_timestamp",
    "require_revoked_at_consistency",
    "new_hpac_id",
    "id_pattern_matches",
    "require_safe_relative_id_component",
    "write_atomic_replace",
    "write_atomic_create_only",
    "read_canonical_json_document",
]


class HPACFoundationError(Exception):
    """Base error for HPAC-001 foundation-layer operations."""


class HPACSymlinkError(HPACFoundationError):
    """A protected path is, or contains, a symlink."""


class HPACMalformedError(HPACFoundationError):
    """A document fails closed schema or canonical-byte validation."""


class HPACCorruptionError(HPACFoundationError):
    """A protected record fails integrity/provenance validation."""


class HPACDuplicateError(HPACFoundationError):
    """A create-only target already exists."""


class HPACAuthorityError(HPACFoundationError):
    """The requested writer, root, or resolution lacks HPAC authority."""


class HPACUnsupportedPlatformError(HPACFoundationError):
    """No fixed production HPAC root exists for this platform."""


class HPACAuthorityClass(str, Enum):
    FIXTURE_NON_REAL = "fixture_non_real"
    PRODUCTION = "production"


_STATUS_VALUES = frozenset({"active", "revoked"})
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")
_AUTHORITY_SCHEMA_VERSION = "HPAC-STORE-AUTHORITY/1.0"
_PROVENANCE_SCHEMA_VERSION = "HPAC-WRITER-PROVENANCE/1.0"
_AUTHORITY_DIR = ".authority"
_AUTHORITY_MANIFEST = "manifest.json"
_AUTHORITY_CONSTRUCTOR_SEAL = object()
_WRITER_CONSTRUCTOR_SEAL = object()
_RESOLUTION_CONSTRUCTOR_SEAL = object()
#: HPAC-PAWA-001 v1.1 §36/§37 (Phase .1R.30R.3.1) — the only object that
#: authorises the ``PRODUCTION`` writer-capability mint. Held privately by
#: the non-agent-importable ``hpac_protected_admin_writer`` module and by
#: nothing else. A caller without it can never reach the mint.
_PRODUCTION_WRITER_FACTORY_SEAL = object()
#: A disclosed, documented **test-only** seam (HPAC-PAWA-REQ-166 / §72 /
#: §73): builds a ``PRODUCTION``-class authority pinned to an isolated
#: fixture protected root so the positive §33 boundary can be exercised
#: without sudo and without touching the real deployment root. A guard
#: test asserts no non-test module ever imports or uses it.
_PRODUCTION_TEST_FIXTURE_SEAL = object()


class ProtectedAdminCapability:
    """Legacy fixture-only mutation marker retained for `.3` tests.

    It is intentionally public and reproducible, and for exactly that reason
    can never authorize a production store. New repair tests use a bound
    :class:`HPACWriterCapability`; this marker is only a compatibility seam for
    non-real fixtures.
    """

    __slots__ = ()

    def __reduce__(self):  # pragma: no cover - defensive serialization guard
        raise TypeError("ProtectedAdminCapability is process-local and non-serializable")


def _normalize_recursive(value: object) -> object:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Mapping):
        return {key: _normalize_recursive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_recursive(item) for item in value]
    return value


def canonical_json_bytes(value: object) -> bytes:
    normalized = _normalize_recursive(value)
    return json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_digest(value: object) -> str:
    return compute_canonical_digest(value)


_MACOS_FIXED_PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")
_LINUX_FIXED_PROTECTED_ROOT = Path("/etc/pcae/hpac/protected-root")


def resolve_hpac_protected_root() -> Path:
    """Return the fixed production root; no override input is accepted."""

    if os.name != "posix":
        raise HPACUnsupportedPlatformError(
            f"HPAC-001 protected root has no fixed-path implementation for {os.name!r}"
        )
    if sys.platform == "darwin":
        return _MACOS_FIXED_PROTECTED_ROOT
    if sys.platform == "linux":
        return _LINUX_FIXED_PROTECTED_ROOT
    raise HPACUnsupportedPlatformError(
        f"HPAC-001 protected root has no fixed-path implementation for {sys.platform!r}"
    )


def reject_symlink(target: Path) -> None:
    try:
        mode = target.lstat().st_mode
    except FileNotFoundError:
        return
    except OSError as exc:
        raise HPACCorruptionError(f"cannot inspect HPAC path: {target}") from exc
    if stat.S_ISLNK(mode):
        raise HPACSymlinkError(f"HPAC-001 protected path is a symlink: {target}")


def _reject_symlink_components(path: Path) -> None:
    """Reject every existing component without resolving through a link."""

    absolute = Path(path).absolute()
    for component in reversed((absolute, *absolute.parents)):
        reject_symlink(component)


def _ensure_directory(path: Path, *, create: bool) -> bool:
    """Reject symlinks/non-directories and create missing descendants 0700."""

    absolute = path.absolute()
    _reject_symlink_components(absolute)
    missing: list[Path] = []
    current = absolute
    while not current.exists():
        reject_symlink(current)
        missing.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    reject_symlink(current)
    if current.exists() and not current.is_dir():
        raise HPACAuthorityError(f"HPAC path ancestor is not a directory: {current}")
    if missing and not create:
        return False
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
    reject_symlink(absolute)
    if not absolute.is_dir():
        raise HPACAuthorityError(f"HPAC path is not a directory: {absolute}")
    return True


def _regular_single_link(path: Path) -> os.stat_result:
    reject_symlink(path)
    try:
        result = path.stat()
    except OSError as exc:
        raise HPACCorruptionError(f"cannot stat HPAC record: {path}") from exc
    if not stat.S_ISREG(result.st_mode) or result.st_nlink != 1:
        raise HPACCorruptionError(f"HPAC record is not a single-link regular file: {path}")
    return result


class HPACWriterCapability:
    """Opaque, non-serializable, authority-instance-bound writer token.

    HPAC-PAWA-001 v1.1 (Phase .1R.30R.3.1) adds two additive, never-caller-
    resettable slots for the ``PRODUCTION`` one-operation lifetime
    (HPAC-PAWA-REQ-106/107, §49/§55): ``_single_use`` marks a capability
    that authorises exactly one bounded mutation, and ``_spent`` is set —
    only through :meth:`HPACStoreAuthority.record_write` under the seal —
    after that mutation succeeds. A spent capability fails
    :meth:`HPACStoreAuthority.require_writer` (→ ``capability_stale``). The
    shape change is strictly additive; no existing semantics are weakened
    (HPAC-PAWA-REQ-082).
    """

    #: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP bundle) adds
    #: one further additive, never-caller-resettable slot: ``_multi_write``
    #: marks a ``_single_use`` capability whose **one bounded operation is a
    #: multi-artifact transaction** — HPAC-PAWA-001 v1.1 §49
    #: (HPAC-PAWA-REQ-106): the ``enroll_credential`` operation's three
    #: protected writes are *one atomic ceremony* and share *one*
    #: capability. For such a capability
    #: :meth:`HPACStoreAuthority.record_write` does **not** auto-spend on the
    #: first write; the transaction owner spends it exactly once via
    #: :meth:`HPACStoreAuthority.complete_multi_write` after the final write
    #: + read-back. A non-``_multi_write`` ``_single_use`` capability keeps
    #: the existing spend-on-first-write semantics byte-for-byte
    #: (HPAC-PAWA-REQ-082 — strictly additive, no existing semantics
    #: weakened).
    __slots__ = (
        "_authority_seal",
        "role",
        "subject",
        "authority_class",
        "_single_use",
        "_spent",
        "_multi_write",
    )

    def __init__(
        self,
        authority_seal: object,
        role: str,
        subject: Optional[str],
        authority_class: HPACAuthorityClass,
        *,
        _seal: object,
        single_use: bool = False,
        multi_write: bool = False,
    ) -> None:
        if _seal is not _WRITER_CONSTRUCTOR_SEAL:
            raise HPACAuthorityError("HPAC writer capabilities cannot be caller-constructed")
        self._authority_seal = authority_seal
        self.role = require_nonempty_str(role, context="writer.role")
        self.subject = subject
        self.authority_class = authority_class
        self._single_use = bool(single_use)
        self._spent = False
        self._multi_write = bool(multi_write)

    def __reduce__(self):
        raise TypeError("HPACWriterCapability is process-local and non-serializable")

    def _mark_spent(self, seal: object) -> None:
        """Set by :meth:`HPACStoreAuthority.record_write` only. Not
        caller-reachable (the seal is module-private) and not resettable
        (there is no un-spend path)."""

        if seal is not _WRITER_CONSTRUCTOR_SEAL:
            raise HPACAuthorityError("HPAC writer-capability spend state cannot be caller-set")
        self._spent = True


class _CapabilityIssuanceState(str, Enum):
    ACTIVE = "active"
    CONSUMED = "consumed"


_MISSING = object()


class _CapabilityIssuanceRecord:
    """Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2.1 (N-16-5 repair) — a
    process-local, non-serializable issuance-membership record binding one
    canonical, factory-issued :class:`HPACWriterCapability` *object* (by
    identity, never by value) to the scope it was minted with.

    HPAC-PAWA-REQ-102's identity check (``writer._authority_seal is
    self._seal``) is necessary but was independently found (.1R.30R.3.2,
    BLOCKED) insufficient: ``_authority_seal`` is an ordinary readable
    instance attribute, so any code that already legitimately holds one
    issued capability can copy that exact seal reference onto a fresh
    ``object.__new__`` shell, which then also satisfies ``is`` identity —
    genuinely, not by reconstruction, because the shell holds the very same
    object. No per-capability field can close this gap, because any field
    stored *on* the capability object is, by the same argument, readable and
    copyable onto a shell.

    The fix is therefore not a stronger field but an out-of-band fact no
    shell can carry: whether *this exact object* — not a structurally
    identical one — is the one the canonical factory (``_new_capability``,
    the sole construction site) actually returned and has not yet consumed.
    That fact lives here, keyed by object identity, never on the capability
    itself; a copy/deepcopy/pickle/``__new__``-reconstruction/attribute
    transplant can carry no membership in this table because membership is
    not a value, it is being the literal object.

    A strong reference to the capability is kept for the life of the entry
    (there is no explicit eviction) so ``id()`` can never be reused for a
    different live object while the entry stands — the classic id-reuse
    forgery this table would otherwise itself be vulnerable to. This is a
    process-local, admin-tool-scale table (HPAC-PAWA-REQ-108 — the enclosing
    admin tool is short-lived, one operation per invocation); it is never
    serialized, never written to disk, and does not survive a process
    restart (HPAC-PAWA-REQ-105), matching every other PAWA process-local
    fact.
    """

    __slots__ = ("capability", "issuance_id", "role", "subject", "authority_class", "state")

    def __init__(
        self,
        capability: "HPACWriterCapability",
        *,
        role: str,
        subject: Optional[str],
        authority_class: "HPACAuthorityClass",
    ) -> None:
        self.capability = capability
        #: Non-authoritative, process-local, never exposed on the capability
        #: object or in any audit projection (HPAC-PAWA-REQ-104) — a
        #: debugging/observability aid only. Authority is the table
        #: membership + object identity, not this value.
        self.issuance_id = secrets.token_bytes(32)
        self.role = role
        self.subject = subject
        self.authority_class = authority_class
        self.state = _CapabilityIssuanceState.ACTIVE


_ISSUANCE_REGISTRY_LOCK = threading.Lock()
#: Keyed by ``id(capability)`` for O(1) lookup; every read verifies
#: ``record.capability is writer`` so a stale/reused id can never match a
#: different live object (defense in depth on top of the strong reference).
_ISSUED_CAPABILITY_REGISTRY: "dict[int, _CapabilityIssuanceRecord]" = {}


def _register_issued_capability(
    capability: "HPACWriterCapability",
    *,
    role: str,
    subject: Optional[str],
    authority_class: "HPACAuthorityClass",
) -> None:
    """Called only from :meth:`HPACStoreAuthority._new_capability` — the
    single construction site — immediately after a capability is minted."""

    record = _CapabilityIssuanceRecord(capability, role=role, subject=subject, authority_class=authority_class)
    with _ISSUANCE_REGISTRY_LOCK:
        _ISSUED_CAPABILITY_REGISTRY[id(capability)] = record


def _lookup_issued_capability(capability: object) -> Optional[_CapabilityIssuanceRecord]:
    with _ISSUANCE_REGISTRY_LOCK:
        record = _ISSUED_CAPABILITY_REGISTRY.get(id(capability))
    if record is None or record.capability is not capability:
        return None
    return record


def _mark_capability_consumed(
    capability: "HPACWriterCapability",
    *,
    authority_class: Optional["HPACAuthorityClass"] = None,
    require_multi_write: bool = False,
) -> None:
    """Transition one canonical issuance to ``CONSUMED`` under its lock.

    ``require_multi_write`` is the .1R.30R.3.6 completion boundary: its
    ACTIVE check, canonical object/scope checks, object-local spend, and
    terminal registry transition are one critical section.  The default
    preserves ``record_write``'s pre-existing post-write transition, where
    the object-local flag has already been set at the adjacent call site.
    """

    with _ISSUANCE_REGISTRY_LOCK:
        record = _ISSUED_CAPABILITY_REGISTRY.get(id(capability))
        if record is None or record.capability is not capability:
            if require_multi_write:
                raise HPACAuthorityError(
                    "writer capability is absent, forged, or bound to another HPAC root"
                )
            return
        if require_multi_write:
            if (
                record.role != getattr(capability, "role", _MISSING)
                or record.subject != getattr(capability, "subject", _MISSING)
            ):
                raise HPACAuthorityError(
                    "writer capability role/subject does not match its canonical issuance"
                )
            if record.authority_class is not authority_class:
                raise HPACAuthorityError("writer capability assurance-class mismatch")
            if not getattr(capability, "_single_use", False) or not getattr(
                capability, "_multi_write", False
            ):
                raise HPACAuthorityError(
                    "complete_multi_write is only valid for a multi-write transaction capability"
                )
            if (
                record.state is _CapabilityIssuanceState.CONSUMED
                or getattr(capability, "_spent", True)
            ):
                raise HPACAuthorityError(
                    "writer capability is spent (one-operation lifetime exhausted)"
                )
            capability._mark_spent(_WRITER_CONSTRUCTOR_SEAL)
        record.state = _CapabilityIssuanceState.CONSUMED


T = TypeVar("T")


class HPACResolvedRecord(Generic[T]):
    """A resolver-produced canonical record plus non-serialized provenance."""

    __slots__ = (
        "record",
        "authority_class",
        "store_id",
        "record_digest",
        "record_path",
        "writer_role",
        "writer_subject",
        "_authority_seal",
    )

    def __init__(
        self,
        *,
        record: T,
        authority_class: HPACAuthorityClass,
        store_id: str,
        record_digest: str,
        record_path: Path,
        writer_role: str,
        writer_subject: Optional[str],
        authority_seal: object,
        _seal: object,
    ) -> None:
        if _seal is not _RESOLUTION_CONSTRUCTOR_SEAL:
            raise HPACAuthorityError("canonical HPAC resolutions cannot be caller-constructed")
        self.record = record
        self.authority_class = authority_class
        self.store_id = store_id
        self.record_digest = record_digest
        self.record_path = record_path
        self.writer_role = writer_role
        self.writer_subject = writer_subject
        self._authority_seal = authority_seal

    @property
    def is_real_runtime_eligible(self) -> bool:
        return self.authority_class is HPACAuthorityClass.PRODUCTION

    def __reduce__(self):
        raise TypeError("HPACResolvedRecord authority is process-local and non-serializable")


class HPACStoreAuthority:
    """Canonical root identity plus process-internal authority seal.

    ``fixture()`` accepts a root but permanently labels it non-real.
    ``production()`` accepts no root and resolves the platform constant.
    There is intentionally no public production-writer factory on this
    class; the ``PRODUCTION`` mint primitive
    (``_mint_production_writer_capability``) is seal-guarded and reachable
    only from ``hpac_protected_admin_writer`` (HPAC-PAWA-001 v1.1 §36/§37).
    """

    __slots__ = (
        "root",
        "authority_class",
        "_seal",
        "_store_id",
        "_root_identity_digest",
        "_configured_agent_identity",
        "_test_fixture_root",
        "_topology_probe",
    )

    def __init__(
        self,
        root: Path,
        authority_class: HPACAuthorityClass,
        *,
        _seal: object,
    ) -> None:
        if _seal is not _AUTHORITY_CONSTRUCTOR_SEAL:
            raise HPACAuthorityError("HPACStoreAuthority must be obtained from a trusted factory")
        self.root = Path(root).absolute()
        self.authority_class = authority_class
        self._seal = object()
        self._store_id: Optional[str] = None
        self._root_identity_digest: Optional[str] = None
        #: F-1 (HPAC-PAWA-REQ-021/022): on the production-writer path the
        #: negative boundary check is evaluated against the *configured
        #: agent principal's* ``(uid, gids)`` — resolved from
        #: ``HPAC-PAWA-AGENT-EXCLUSION/1.0`` (§32A), never ``os.geteuid()``.
        #: ``None`` ⇒ fall back to the live invoking process (pre-PAWA
        #: behaviour; no production caller relies on that fallback).
        self._configured_agent_identity: Optional["tuple[int, frozenset[int]]"] = None
        #: Test-only: skip the ``resolve_hpac_protected_root()`` identity
        #: pin so an isolated fixture topology can be validated (§72/§73).
        self._test_fixture_root = False
        #: Test-only (HPAC-PAWA-REQ-132/166): a deterministic
        #: ``(effective_write_access, ancestor_chain_safe)`` pair
        #: substituting for the platform ACL adapter, which is unavailable
        #: in sandboxed CI. ``None`` in production ⇒ the real
        #: ``hatp_class_b_topology_verifier`` functions.
        self._topology_probe: Optional[object] = None

    @classmethod
    def fixture(cls, root: Path) -> "HPACStoreAuthority":
        return cls(Path(root), HPACAuthorityClass.FIXTURE_NON_REAL, _seal=_AUTHORITY_CONSTRUCTOR_SEAL)

    def _effective_write_helpers(self):
        probe = self._topology_probe
        if probe is not None:
            return probe.effective_write_access, probe.ancestor_chain_safe
        from pcae.core.hatp_class_b_topology_verifier import (
            _ancestor_chain_safe,
            _effective_write_access,
        )

        return _effective_write_access, _ancestor_chain_safe

    @classmethod
    def _production_test_fixture(
        cls, root: Path, *, _seal: object, _topology_probe: object = None
    ) -> "HPACStoreAuthority":
        """Disclosed test-only seam (HPAC-PAWA-REQ-166, §72/§73). A
        ``PRODUCTION``-class authority pinned to an isolated fixture
        protected root. Never reachable from ordinary production API — a
        guard test asserts no non-test module imports
        ``_PRODUCTION_TEST_FIXTURE_SEAL`` or calls this method."""

        if _seal is not _PRODUCTION_TEST_FIXTURE_SEAL:
            raise HPACAuthorityError("_production_test_fixture is a test-only seam")
        authority = cls(Path(root).resolve(), HPACAuthorityClass.PRODUCTION, _seal=_AUTHORITY_CONSTRUCTOR_SEAL)
        authority._test_fixture_root = True
        authority._topology_probe = _topology_probe
        return authority

    def _bind_configured_agent_identity(
        self, identity: "tuple[int, frozenset[int]]", *, _factory_seal: object
    ) -> None:
        """Called by the §33 recognition sequence (after step 2 resolves
        ``HPAC-PAWA-AGENT-EXCLUSION/1.0``) so every subsequent
        ``_validate_production_boundary`` / ``_relative_record_path``
        re-run keys the negative boundary off the configured agent
        principal, not the live process (F-1)."""

        if _factory_seal is not _PRODUCTION_WRITER_FACTORY_SEAL:
            raise HPACAuthorityError("configured-agent identity can only be bound by the PAWA writer factory")
        uid, gids = identity
        self._configured_agent_identity = (int(uid), frozenset(int(g) for g in gids))

    @classmethod
    def production(cls) -> "HPACStoreAuthority":
        return cls(resolve_hpac_protected_root(), HPACAuthorityClass.PRODUCTION, _seal=_AUTHORITY_CONSTRUCTOR_SEAL)

    @property
    def is_real_runtime_eligible(self) -> bool:
        return self.authority_class is HPACAuthorityClass.PRODUCTION

    @property
    def store_id(self) -> str:
        self._ensure_root(create=False)
        assert self._store_id is not None
        return self._store_id

    def _manifest_path(self) -> Path:
        return self.root / _AUTHORITY_DIR / _AUTHORITY_MANIFEST

    def _root_identity(self) -> dict:
        result = self.root.stat()
        return {"device": result.st_dev, "inode": result.st_ino}

    def _validate_fixture_permissions(self) -> None:
        mode = stat.S_IMODE(self.root.stat().st_mode)
        if mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise HPACAuthorityError("fixture HPAC root is group/world writable")

    def _validate_production_boundary(self) -> None:
        if not self._test_fixture_root and self.root != resolve_hpac_protected_root().absolute():
            raise HPACAuthorityError("production HPAC authority cannot be redirected")
        from pcae.core.hatp_class_b_topology_verifier import _current_agent_identity

        _effective_write_access, _ancestor_chain_safe = self._effective_write_helpers()

        # F-1 (HPAC-PAWA-REQ-022): on the production-writer path the
        # negative boundary keys off the CONFIGURED agent principal, not
        # the invoking process. The invoking process (the deployment
        # owner) legitimately DOES hold write authority here — that is
        # what the §28 positive write probe proves separately.
        if self._configured_agent_identity is not None:
            agent_uid, agent_gids = self._configured_agent_identity
        else:
            agent_uid, agent_gids = _current_agent_identity()
        writable, reason, _evidence = _effective_write_access(self.root, agent_uid, agent_gids)
        ancestors_safe, diagnostics = _ancestor_chain_safe(self.root, agent_uid, agent_gids)
        if writable is not False or ancestors_safe is not True:
            raise HPACAuthorityError(
                "production HPAC root is not protected from the configured agent principal "
                f"(root={reason}, ancestors={diagnostics})"
            )

    def _ensure_root(self, *, create: bool) -> None:
        _reject_symlink_components(self.root)
        if not self.root.exists():
            if not create or self.authority_class is HPACAuthorityClass.PRODUCTION:
                raise HPACAuthorityError(f"HPAC authority root is unavailable: {self.root}")
            _ensure_directory(self.root, create=True)
            os.chmod(self.root, 0o700)
        reject_symlink(self.root)
        if not self.root.is_dir():
            raise HPACAuthorityError(f"HPAC authority root is not a directory: {self.root}")
        if self.authority_class is HPACAuthorityClass.PRODUCTION:
            self._validate_production_boundary()
        else:
            self._validate_fixture_permissions()

        authority_dir = self.root / _AUTHORITY_DIR
        manifest_path = self._manifest_path()
        if not manifest_path.exists():
            if not create or self.authority_class is HPACAuthorityClass.PRODUCTION:
                raise HPACAuthorityError("HPAC authority manifest is absent")
            _ensure_directory(authority_dir, create=True)
            os.chmod(authority_dir, 0o700)
            identity = self._root_identity()
            manifest = {
                "schema_version": _AUTHORITY_SCHEMA_VERSION,
                "store_id": f"hpacs-{uuid.uuid4().hex}",
                "authority_class": self.authority_class.value,
                "root_identity": identity,
            }
            write_atomic_create_only(manifest_path, canonical_json_bytes(manifest))

        manifest = read_canonical_json_document(manifest_path)
        if not isinstance(manifest, dict) or set(manifest) != {
            "schema_version", "store_id", "authority_class", "root_identity"
        }:
            raise HPACAuthorityError("HPAC authority manifest has an invalid closed schema")
        if manifest.get("schema_version") != _AUTHORITY_SCHEMA_VERSION:
            raise HPACAuthorityError("HPAC authority manifest version is unsupported")
        if manifest.get("authority_class") != self.authority_class.value:
            raise HPACAuthorityError("HPAC root assurance class does not match its resolver")
        if manifest.get("root_identity") != self._root_identity():
            raise HPACAuthorityError("HPAC root was copied or replaced; root identity binding failed")
        store_id = manifest.get("store_id")
        if not isinstance(store_id, str) or not store_id.startswith("hpacs-"):
            raise HPACAuthorityError("HPAC authority manifest store_id is malformed")
        self._store_id = store_id
        self._root_identity_digest = canonical_digest(manifest["root_identity"])

    def _new_capability(
        self,
        role: str,
        subject: Optional[str],
        *,
        single_use: bool = False,
        multi_write: bool = False,
    ) -> HPACWriterCapability:
        """The single ``HPACWriterCapability`` construction site (shared by
        the fixture ``writer()`` and the seal-guarded ``PRODUCTION`` mint —
        HPAC-PAWA-REQ-091). Every capability is bound to *this* authority
        instance's private ``_seal``."""

        if subject is not None:
            require_nonempty_str(subject, context="writer.subject")
        capability = HPACWriterCapability(
            self._seal,
            role,
            subject,
            self.authority_class,
            _seal=_WRITER_CONSTRUCTOR_SEAL,
            single_use=single_use,
            multi_write=multi_write,
        )
        # .1R.30R.3.2.1 (N-16-5 repair) — every capability, from this sole
        # construction site, is registered as canonically issued. A shell
        # built any other way (object.__new__, copy, a hand-built lookalike)
        # is never inserted here and therefore never satisfies
        # require_writer, regardless of which fields it carries.
        _register_issued_capability(
            capability, role=role, subject=subject, authority_class=self.authority_class
        )
        return capability

    def writer(self, role: str, *, subject: Optional[str] = None) -> HPACWriterCapability:
        """Issue a bound fixture writer; real writer ceremony is deferred."""

        if self.authority_class is not HPACAuthorityClass.FIXTURE_NON_REAL:
            raise HPACAuthorityError("no production HPAC writer is implemented in this foundation phase")
        self._ensure_root(create=True)
        return self._new_capability(role, subject)

    def _mint_production_writer_capability(
        self,
        role: str,
        subject: Optional[str],
        *,
        _factory_seal: object,
        multi_write: bool = False,
    ) -> HPACWriterCapability:
        """HPAC-PAWA-001 v1.1 §36 — the low-level ``PRODUCTION`` mint.

        Reachable **only** from ``hpac_protected_admin_writer`` (which holds
        ``_PRODUCTION_WRITER_FACTORY_SEAL``). It does not itself run the §33
        recognition sequence — that is the factory's job, and it is atomic
        with this call (PAWA-INV-3). This primitive only: verifies the
        factory seal, requires a ``PRODUCTION``-class authority, re-runs
        ``_ensure_root`` (re-validating the F-1-scoped boundary and the
        root-identity binding on every mint — §30/§70), and mints a
        single-use, operation-scoped capability bound to this instance's
        ``_seal``."""

        if _factory_seal is not _PRODUCTION_WRITER_FACTORY_SEAL:
            raise HPACAuthorityError("the PRODUCTION HPAC writer mint is reachable only from the PAWA factory")
        if self.authority_class is not HPACAuthorityClass.PRODUCTION:
            raise HPACAuthorityError("a PRODUCTION writer requires a PRODUCTION HPACStoreAuthority")
        self._ensure_root(create=False)
        return self._new_capability(
            role, subject, single_use=True, multi_write=multi_write
        )

    def complete_multi_write(self, writer: HPACWriterCapability) -> None:
        """Phase .1R.30R.3.4 — spend a ``_multi_write`` ``_single_use``
        capability exactly once, after its multi-artifact enrollment
        transaction's final write + read-back (HPAC-PAWA-REQ-106/107 — the
        bounded transaction is "one operation"). A second call, or any
        subsequent ``require_writer`` / ``record_write``, fails closed
        (``capability_stale``). A non-``_multi_write`` capability is already
        spent by ``record_write`` and passing one here is a no-op-safe
        error path."""

        if not isinstance(writer, HPACWriterCapability):
            raise HPACAuthorityError("complete_multi_write requires an HPACWriterCapability")
        if getattr(writer, "_authority_seal", _MISSING) is not self._seal:
            raise HPACAuthorityError("writer capability is absent, forged, or bound to another HPAC root")
        # Phase .1R.30R.3.6 — canonical registry state, not the mutable
        # ``_spent`` slot, is authoritative.  The helper performs the ACTIVE
        # check and ACTIVE -> CONSUMED transition under the registry lock so
        # racing callers cannot both succeed.
        _mark_capability_consumed(
            writer,
            authority_class=self.authority_class,
            require_multi_write=True,
        )

    def legacy_fixture_writer(
        self, capability: ProtectedAdminCapability, role: str, *, subject: Optional[str] = None
    ) -> HPACWriterCapability:
        if not isinstance(capability, ProtectedAdminCapability):
            raise HPACAuthorityError("legacy fixture mutation requires ProtectedAdminCapability")
        return self.writer(role, subject=subject)

    def require_writer(
        self, writer: HPACWriterCapability, role: str, *, subject: Optional[str] = None
    ) -> None:
        if not isinstance(writer, HPACWriterCapability):
            raise HPACAuthorityError("writer capability is absent, forged, or bound to another HPAC root")
        # ``getattr`` with a sentinel, not direct attribute access: an
        # object.__new__ shell that never ran __init__ has no
        # ``_authority_seal`` slot value at all, and a bare attribute read
        # would raise AttributeError instead of failing closed cleanly
        # (§0; HPAC-PAWA-REQ-103, "object.__new__ ... reconstruction").
        if getattr(writer, "_authority_seal", _MISSING) is not self._seal:
            raise HPACAuthorityError("writer capability is absent, forged, or bound to another HPAC root")
        # .1R.30R.3.2.1 (N-16-5 repair) — HPAC-PAWA-REQ-102/106/107. Seal
        # *identity* alone is necessary but not sufficient: it is a plain
        # readable attribute, so a caller who already holds one legitimately
        # issued capability can copy that exact seal reference onto a fresh
        # ``object.__new__`` shell, which then also satisfies ``is``
        # identity. The decisive additional check is canonical-issuance
        # *object* membership — a fact that lives only in the process-local
        # issuance registry, never on the capability itself, and therefore
        # cannot be copied onto a shell no matter which fields it carries
        # (.1R.30R.3.2 finding §5).
        record = _lookup_issued_capability(writer)
        if record is None:
            raise HPACAuthorityError("writer capability is absent, forged, or bound to another HPAC root")
        # Registry-bound canonical scope dominates the (plain, mutable,
        # attacker-reachable) object fields: even a legitimately-issued
        # capability's ``role``/``subject`` slots could otherwise be
        # reassigned after mint to widen scope.
        if record.role != role or record.subject != subject:
            raise HPACAuthorityError("writer capability role/subject does not match this operation")
        if record.authority_class is not self.authority_class:
            raise HPACAuthorityError("writer capability assurance-class mismatch")
        if record.state is _CapabilityIssuanceState.CONSUMED or getattr(writer, "_spent", True):
            # HPAC-PAWA-REQ-106/107, §49 — a PRODUCTION single-use
            # capability authorises exactly one bounded mutation; a second
            # attempt is stale. Registry state is authoritative (it cannot
            # be reset by external attribute assignment the way a plain
            # ``_spent`` slot could be); the object's own ``_spent`` flag is
            # still consulted too, defense in depth.
            raise HPACAuthorityError("writer capability is spent (one-operation lifetime exhausted)")
        self._ensure_root(create=True)

    @contextmanager
    def writer_transaction(
        self, writer: HPACWriterCapability, role: str, *, subject: Optional[str] = None
    ):
        """Serialize one read/validate/write transaction at the root.

        The lock is only a concurrency primitive; it carries no authority.
        Authority is checked before the lock is opened and remains rooted in
        the writer seal plus protected store state.
        """

        self.require_writer(writer, role, subject=subject)
        import fcntl

        lock_path = self.root / _AUTHORITY_DIR / "writer.lock"
        reject_symlink(lock_path)
        fd = os.open(
            lock_path,
            os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            result = os.fstat(fd)
            if not stat.S_ISREG(result.st_mode) or result.st_nlink != 1:
                raise HPACAuthorityError("HPAC writer lock is not a single-link regular file")
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _relative_record_path(self, path: Path) -> str:
        absolute = Path(path).absolute()
        _reject_symlink_components(absolute)
        try:
            relative = absolute.relative_to(self.root)
        except ValueError as exc:
            raise HPACAuthorityError("record path escapes the canonical HPAC root") from exc
        if any(part in {"", ".", ".."} for part in relative.parts):
            raise HPACAuthorityError("record path contains traversal components")
        current = self.root
        reject_symlink(current)
        for part in relative.parts:
            current = current / part
            reject_symlink(current)
            if current.exists() and current.is_dir():
                if self.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL:
                    mode = stat.S_IMODE(current.stat().st_mode)
                    if mode & (stat.S_IWGRP | stat.S_IWOTH):
                        raise HPACAuthorityError(
                            f"fixture HPAC descendant directory is group/world writable: {current}"
                        )
                else:
                    from pcae.core.hatp_class_b_topology_verifier import _current_agent_identity

                    _effective_write_access, _acs = self._effective_write_helpers()

                    # F-1: descendant not-writable is asserted against the
                    # configured agent principal on the production-writer
                    # path (not the deployment owner running the mutation).
                    if self._configured_agent_identity is not None:
                        agent_uid, agent_gids = self._configured_agent_identity
                    else:
                        agent_uid, agent_gids = _current_agent_identity()
                    writable, reason, _evidence = _effective_write_access(
                        current, agent_uid, agent_gids
                    )
                    if writable is not False:
                        raise HPACAuthorityError(
                            f"production HPAC descendant is configured-agent-writable or indeterminate: {current}:{reason}"
                        )
        return relative.as_posix()

    def _provenance_path(self, record_path: Path) -> Path:
        relative = self._relative_record_path(record_path)
        key = hashlib.sha256(relative.encode("utf-8")).hexdigest()
        return self.root / _AUTHORITY_DIR / "provenance" / f"{key}.json"

    def record_write(
        self,
        record_path: Path,
        record_digest: str,
        writer: HPACWriterCapability,
        *,
        role: str,
        subject: Optional[str] = None,
        replace: bool = False,
    ) -> None:
        self.require_writer(writer, role, subject=subject)
        _regular_single_link(record_path)
        relative = self._relative_record_path(record_path)
        provenance = {
            "schema_version": _PROVENANCE_SCHEMA_VERSION,
            "store_id": self.store_id,
            "authority_class": self.authority_class.value,
            "root_identity_digest": self._root_identity_digest,
            "record_relative_path": relative,
            "record_digest": record_digest,
            "writer_role": role,
            "writer_subject": subject,
        }
        provenance_path = self._provenance_path(record_path)
        payload = canonical_json_bytes(provenance)
        if replace:
            write_atomic_replace(provenance_path, payload)
        else:
            write_atomic_create_only(provenance_path, payload)
        if writer._single_use and not writer._multi_write:
            # HPAC-PAWA-REQ-107, §49 — the one bounded mutation has been
            # recorded; the same capability object can never authorise a
            # second record_write (→ ``capability_stale``). Both the
            # object-local flag (existing) and the registry-side state
            # (.1R.30R.3.2.1 repair) are set at this same transition point;
            # the registry copy cannot be reset by external attribute
            # assignment on the capability object the way ``_spent`` alone
            # could be.
            #
            # Phase .1R.30R.3.4: a ``_multi_write`` capability's one bounded
            # operation is a multi-artifact enrollment transaction
            # (HPAC-PAWA-REQ-106) — it is spent once by
            # ``complete_multi_write`` after the final write, not here.
            writer._mark_spent(_WRITER_CONSTRUCTOR_SEAL)
            _mark_capability_consumed(writer)

    def verify_record(
        self,
        record_path: Path,
        record_digest: str,
        *,
        roles: frozenset[str],
        subject: Optional[str] = None,
    ) -> dict:
        self._ensure_root(create=False)
        _regular_single_link(record_path)
        relative = self._relative_record_path(record_path)
        provenance_path = self._provenance_path(record_path)
        if not provenance_path.exists():
            raise HPACAuthorityError("HPAC record has no writer provenance")
        try:
            provenance = read_canonical_json_document(provenance_path)
        except HPACFoundationError as exc:
            raise HPACAuthorityError("HPAC writer provenance is malformed or corrupt") from exc
        if not isinstance(provenance, dict) or set(provenance) != {
            "schema_version", "store_id", "authority_class", "root_identity_digest",
            "record_relative_path", "record_digest", "writer_role", "writer_subject",
        }:
            raise HPACAuthorityError("HPAC writer provenance has an invalid closed schema")
        expected = {
            "schema_version": _PROVENANCE_SCHEMA_VERSION,
            "store_id": self.store_id,
            "authority_class": self.authority_class.value,
            "root_identity_digest": self._root_identity_digest,
            "record_relative_path": relative,
            "record_digest": record_digest,
        }
        for key, value in expected.items():
            if provenance.get(key) != value:
                raise HPACAuthorityError(f"HPAC writer provenance mismatch: {key}")
        if provenance.get("writer_role") not in roles:
            raise HPACAuthorityError("HPAC record was not emitted by an allowed writer role")
        if subject is not None and provenance.get("writer_subject") != subject:
            raise HPACAuthorityError("HPAC writer subject binding mismatch")
        return provenance

    def resolve_record(
        self,
        *,
        record: T,
        record_path: Path,
        record_digest: str,
        roles: frozenset[str],
        subject: Optional[str] = None,
    ) -> HPACResolvedRecord[T]:
        provenance = self.verify_record(
            record_path, record_digest, roles=roles, subject=subject
        )
        return HPACResolvedRecord(
            record=record,
            authority_class=self.authority_class,
            store_id=self.store_id,
            record_digest=record_digest,
            record_path=record_path,
            writer_role=provenance["writer_role"],
            writer_subject=provenance["writer_subject"],
            authority_seal=self._seal,
            _seal=_RESOLUTION_CONSTRUCTOR_SEAL,
        )

    def require_resolution(self, resolution: HPACResolvedRecord[T]) -> T:
        if not isinstance(resolution, HPACResolvedRecord) or resolution._authority_seal is not self._seal:
            raise HPACAuthorityError("canonical record resolution is forged or belongs to another HPAC root")
        if resolution.store_id != self.store_id or resolution.authority_class is not self.authority_class:
            raise HPACAuthorityError("canonical record resolution store/assurance mismatch")
        return resolution.record


def require_nonempty_str(value: object, *, context: str) -> str:
    if not isinstance(value, str) or value == "" or value != value.strip():
        raise HPACMalformedError(f"{context}: expected a non-empty, non-whitespace-padded string")
    if len(value) > 256:
        raise HPACMalformedError(f"{context}: exceeds the 256-character bound")
    return value


def require_safe_relative_id_component(value: object, *, context: str) -> str:
    """Require `value` to be usable as exactly one filesystem path segment.

    A canonical store's record identity is not its filesystem location
    (contract principle: RECORD ID != FILESYSTEM PATH). Rejecting `.`, `..`,
    and any path separator here -- before the caller-supplied identifier is
    ever joined onto a store root -- means an absolute path, a UNC/drive
    form (which cannot be expressed without a backslash), or a `../`
    traversal segment can never select a storage location outside the
    owning store's configured root; `Path.__truediv__` silently discards a
    root prefix when joined with an absolute string, so this check must run
    before that join, not after.
    """

    text = require_nonempty_str(value, context=context)
    if text in {".", ".."} or "/" in text or "\\" in text:
        raise HPACMalformedError(f"{context}: must be exactly one safe path component")
    return text


def require_status(value: object, *, context: str) -> str:
    if value not in _STATUS_VALUES:
        raise HPACMalformedError(f"{context}: invalid status {value!r}")
    return value  # type: ignore[return-value]


def require_timestamp(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        raise HPACMalformedError(f"{context}: expected an RFC3339 UTC timestamp")
    return value


def require_revoked_at_consistency(status: str, revoked_at: object, *, context: str) -> Optional[str]:
    if status == "revoked":
        if revoked_at is None:
            raise HPACMalformedError(f"{context}: revoked_at is required")
        return require_timestamp(revoked_at, context=f"{context}.revoked_at")
    if revoked_at is not None:
        raise HPACMalformedError(f"{context}: active record cannot carry revoked_at")
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
    if prefix not in _ID_PATTERNS:
        raise HPACFoundationError(f"unknown HPAC-001 ID prefix: {prefix!r}")
    return f"{prefix}-{uuid.uuid4().hex}"


def id_pattern_matches(prefix: str, value: object) -> bool:
    if prefix not in _ID_PATTERNS:
        raise HPACFoundationError(f"unknown HPAC-001 ID prefix: {prefix!r}")
    return isinstance(value, str) and bool(_ID_PATTERNS[prefix].match(value))


def write_atomic_replace(path: Path, data: bytes) -> None:
    directory = path.parent
    _ensure_directory(directory, create=True)
    reject_symlink(path)
    fd, temporary = tempfile.mkstemp(prefix=".tmp-hpac-", dir=str(directory))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        reject_symlink(path)
        os.replace(temporary, path)
        directory_fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_atomic_create_only(path: Path, data: bytes) -> None:
    """Durably link a complete temp file into an absent final name."""

    directory = path.parent
    _ensure_directory(directory, create=True)
    reject_symlink(path)
    if path.exists():
        raise HPACDuplicateError(f"HPAC-001 create-only path already exists: {path}")
    fd, temporary = tempfile.mkstemp(prefix=".tmp-hpac-", dir=str(directory))
    temporary_path = Path(temporary)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise HPACDuplicateError(f"HPAC-001 create-only path already exists: {path}") from exc
        directory_fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


class _DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise _DuplicateKeyError(key)
        output[key] = value
    return output


def read_canonical_json_document(path: Path) -> object:
    """Read one single-link regular file and require exact canonical bytes."""

    _regular_single_link(path)
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        document = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeDecodeError) as exc:
        raise HPACCorruptionError(f"HPAC-001 record could not be read: {path}") from exc
    except (json.JSONDecodeError, _DuplicateKeyError) as exc:
        raise HPACMalformedError(f"HPAC-001 record is not strict JSON: {path}") from exc
    if raw != canonical_json_bytes(document):
        raise HPACMalformedError(f"HPAC-001 record is not encoded as exact canonical JSON: {path}")
    return document
