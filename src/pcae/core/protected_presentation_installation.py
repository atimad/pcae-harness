"""HPAC-PPA-001 v1.0 §2–§4 / §6 — the protected-presentation helper
installation, current-generation, and helper-integrity layer.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1 — N-16-5 Protected
Human-Approval Presentation and Real-Assurance Consumption Implementation
After Authority Reconciliation.

This module owns exactly:

* the ``HPAC-PRESENTATION-INSTALLATION/1.0`` immutable installation-generation
  record schema (HPAC-PPA-REQ-013/014) — closed field set, canonical bytes,
  self-excluding ``installation_digest``;
* the ``HPAC-PRESENTATION-CURRENT-GENERATION/1.0`` current-generation anchor
  schema (HPAC-PPA-REQ-017/018) — closed field set, self-excluding
  ``anchor_digest``;
* the fixed content-addressed helper path derivation (HPAC-PPA-REQ-010/011),
  and the pre-launch / configuration-time helper-byte integrity check
  (HPAC-PPA-REQ-012/029) — non-symlink chain, regular single-link file,
  deployment-owner ownership, no group/other/configured-agent write, and the
  opened-byte SHA-256 equals the pinned ``helper_sha256``;
* :class:`ProtectedPresentationInstallationStore` — the canonical store that
  resolves the current generation (anchor + immutable record + descriptor
  agreement + writer provenance, HPAC-PPA-REQ-019/020) and, given one bounded
  ``configure_presentation_mechanism`` PAWA capability, applies exactly one
  ``install`` / ``rotate`` / ``revoke`` configuration transaction as a single
  bounded multi-write (HPAC-PPA-REQ-023).

It installs no executable bytes (HPAC-PPA-REQ-004): the helper is installed
out of band by the deployment owner; this module only registers and pins
metadata. It mints no writer capability, launches no helper, writes no
presentation evidence, and touches no Gate, runtime, adapter, or effect.

Every fault fails closed (HPAC-PPA-REQ-002). Configuration-input faults raise
:class:`ProtectedPresentationInstallationError`; a resolution/integrity fault
maps onto the frozen RHAMP-001 §49 terminal reason
``helper_integrity_unverified`` (HPAC-PPA-REQ-076) via
:class:`ProtectedPresentationIntegrityError`.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.approval_presentation import (
    PRESENTATION_MECHANISM_SCHEMA_VERSION,
    PresentationMechanismDescriptor,
    PresentationMechanismDescriptorStore,
)
from pcae.core.hpac_foundation import (
    HPACAuthorityError,
    HPACFoundationError,
    HPACResolvedRecord,
    HPACStoreAuthority,
    HPACWriterCapability,
    canonical_digest,
    canonical_json_bytes,
    read_canonical_json_document,
    reject_symlink,
    write_atomic_create_only,
    write_atomic_replace,
)

__all__ = [
    "INSTALLATION_SCHEMA_VERSION",
    "CURRENT_GENERATION_SCHEMA_VERSION",
    "MECHANISM_ID",
    "VERIFIER_KIND",
    "INSTALLER_WRITER_ROLE",
    "LIFECYCLE_ACTIONS",
    "ProtectedPresentationInstallationError",
    "ProtectedPresentationIntegrityError",
    "InstallationRecord",
    "CurrentGenerationAnchor",
    "ResolvedCurrentGeneration",
    "new_installation_id",
    "helper_content_addressed_path",
    "verify_helper_bytes",
    "build_installation_record",
    "build_current_generation_anchor",
    "validate_installation_record",
    "validate_current_generation_anchor",
    "ProtectedPresentationInstallationStore",
]


# ─────────────────────────────────────────────────────────────────────────
# Fixed production identities (HPAC-PPA-REQ-008/009/010)
# ─────────────────────────────────────────────────────────────────────────

INSTALLATION_SCHEMA_VERSION = "HPAC-PRESENTATION-INSTALLATION/1.0"
CURRENT_GENERATION_SCHEMA_VERSION = "HPAC-PRESENTATION-CURRENT-GENERATION/1.0"

#: HPAC-PPA-REQ-008 — the sole v1.0 production mechanism identity and the
#: sole real verifier kind. Exact string equality only.
MECHANISM_ID = "pcae-protected-local-presentation"
VERIFIER_KIND = "pcae-protected-local-presentation/1.0"

#: HPAC-PPA-REQ-005/015 — the installer writer role (already frozen by
#: ``approval_presentation.PresentationMechanismDescriptorStore``).
INSTALLER_WRITER_ROLE = "presentation_mechanism_installer"

#: HPAC-PPA-REQ-014 — closed ``lifecycle_action`` enum.
LIFECYCLE_ACTIONS = ("install", "rotate", "revoke")

_MECHANISM_DIR_SEGMENTS = ("presentation-mechanisms", "v2", MECHANISM_ID)
_HELPER_INSTALL_SEGMENTS = ("presentation-helper", "installations")
_HELPER_FILENAME = MECHANISM_ID

_INSTALLATION_ID_RE = re.compile(r"^hppi-[0-9a-f]{32}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")


# ─────────────────────────────────────────────────────────────────────────
# Errors
# ─────────────────────────────────────────────────────────────────────────


class ProtectedPresentationInstallationError(HPACFoundationError):
    """A ``configure_presentation_mechanism`` configuration-input,
    closed-schema, canonical-byte, or lifecycle fault. Fails closed
    (HPAC-PPA-REQ-002)."""


class ProtectedPresentationIntegrityError(HPACFoundationError):
    """A helper-integrity / installation-currentness resolution fault. Maps
    onto the frozen RHAMP-001 §49 terminal reason
    ``helper_integrity_unverified`` (HPAC-PPA-REQ-076). No new terminal
    reason is introduced."""

    terminal_reason_code = "helper_integrity_unverified"


# ─────────────────────────────────────────────────────────────────────────
# Grammar primitives
# ─────────────────────────────────────────────────────────────────────────


def new_installation_id() -> str:
    return f"hppi-{uuid.uuid4().hex}"


def _require_hex64(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not _HEX64_RE.fullmatch(value):
        raise ProtectedPresentationInstallationError(f"{field}: expected 64 lowercase hex characters")
    return value


def _require_installation_id(value: object, *, field: str = "installation_id") -> str:
    if not isinstance(value, str) or not _INSTALLATION_ID_RE.fullmatch(value):
        raise ProtectedPresentationInstallationError(f"{field}: expected an hppi-<hex32> identifier")
    return value


def _require_generation(value: object, *, field: str = "generation") -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ProtectedPresentationInstallationError(f"{field}: expected an integer >= 1")
    return value


def _require_timestamp(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        raise ProtectedPresentationInstallationError(f"{field}: expected an RFC3339 UTC timestamp")
    return value


def _require_nonempty(value: object, *, field: str) -> str:
    if not isinstance(value, str) or value == "" or value != value.strip():
        raise ProtectedPresentationInstallationError(f"{field}: expected a non-empty, non-padded string")
    return value


def _self_excluding_digest(document: dict, *, digest_field: str) -> str:
    if digest_field not in document:
        raise ProtectedPresentationInstallationError(f"digest field {digest_field!r} absent from record")
    projected = dict(document)
    projected[digest_field] = ""
    return canonical_digest(projected)


# ─────────────────────────────────────────────────────────────────────────
# Typed views
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class InstallationRecord:
    document: dict
    installation_id: str
    mechanism_id: str
    helper_path: str
    helper_sha256: str
    descriptor_digest: str
    verifier_configuration_digest: str
    renderer_profile: str
    helper_implementation_version: str
    generation: int
    lifecycle_action: str
    status: str
    installation_digest: str
    supersedes: Optional[dict]


@dataclass(frozen=True)
class CurrentGenerationAnchor:
    document: dict
    installation_id: str
    mechanism_id: str
    current_generation: int
    installation_digest: str
    descriptor_digest: str
    status: str
    anchor_digest: str


@dataclass(frozen=True)
class ResolvedCurrentGeneration:
    anchor: CurrentGenerationAnchor
    record: InstallationRecord
    descriptor: PresentationMechanismDescriptor
    mechanism_dir: Path
    helper_path: Path


# ─────────────────────────────────────────────────────────────────────────
# HPAC-PRESENTATION-INSTALLATION/1.0 (HPAC-PPA-REQ-014)
# ─────────────────────────────────────────────────────────────────────────

_INSTALLATION_FIELDS = frozenset(
    {
        "installation_schema_version",
        "installation_id",
        "mechanism_id",
        "helper_implementation_id",
        "helper_implementation_version",
        "helper_path",
        "helper_sha256",
        "descriptor_digest",
        "verifier_configuration_digest",
        "renderer_profile",
        "generation",
        "lifecycle_action",
        "status",
        "installed_at",
        "supersedes",
        "installation_digest",
    }
)


def _validate_supersedes(value: object, generation: int, *, digest_key: str) -> Optional[dict]:
    if generation == 1:
        if value is not None:
            raise ProtectedPresentationInstallationError("supersedes: must be null for generation 1")
        return None
    if not isinstance(value, dict) or set(value) != {"generation", digest_key}:
        raise ProtectedPresentationInstallationError(
            f"supersedes: expected a closed {{generation, {digest_key}}} object for generation > 1"
        )
    prev = value["generation"]
    if not isinstance(prev, int) or isinstance(prev, bool) or prev < 1 or prev >= generation:
        raise ProtectedPresentationInstallationError("supersedes.generation: must be an integer in [1, generation)")
    _require_hex64(value[digest_key], field=f"supersedes.{digest_key}")
    return value


def build_installation_record(
    *,
    installation_id: str,
    helper_path: str,
    helper_sha256: str,
    helper_implementation_version: str,
    descriptor_digest: str,
    verifier_configuration_digest: str,
    renderer_profile: str,
    generation: int,
    lifecycle_action: str,
    installed_at: str,
    supersedes: Optional[dict],
) -> dict:
    if lifecycle_action not in LIFECYCLE_ACTIONS:
        raise ProtectedPresentationInstallationError(
            f"lifecycle_action {lifecycle_action!r} is outside the closed enum {LIFECYCLE_ACTIONS}"
        )
    status = "revoked" if lifecycle_action == "revoke" else "active"
    document = {
        "installation_schema_version": INSTALLATION_SCHEMA_VERSION,
        "installation_id": _require_installation_id(installation_id),
        "mechanism_id": MECHANISM_ID,
        "helper_implementation_id": MECHANISM_ID,
        "helper_implementation_version": _require_nonempty(
            helper_implementation_version, field="helper_implementation_version"
        ),
        "helper_path": _require_nonempty(helper_path, field="helper_path"),
        "helper_sha256": _require_hex64(helper_sha256, field="helper_sha256"),
        "descriptor_digest": _require_hex64(descriptor_digest, field="descriptor_digest"),
        "verifier_configuration_digest": _require_hex64(
            verifier_configuration_digest, field="verifier_configuration_digest"
        ),
        "renderer_profile": _require_nonempty(renderer_profile, field="renderer_profile"),
        "generation": _require_generation(generation),
        "lifecycle_action": lifecycle_action,
        "status": status,
        "installed_at": _require_timestamp(installed_at, field="installed_at"),
        "supersedes": _validate_supersedes(supersedes, generation, digest_key="installation_digest"),
        "installation_digest": "",
    }
    if not Path(document["helper_path"]).is_absolute():
        raise ProtectedPresentationInstallationError("helper_path must be an absolute path (HPAC-PPA-REQ-011)")
    document["installation_digest"] = _self_excluding_digest(document, digest_field="installation_digest")
    return document


def validate_installation_record(document: object) -> InstallationRecord:
    if not isinstance(document, dict):
        raise ProtectedPresentationInstallationError("installation record is not an object")
    if set(document) != _INSTALLATION_FIELDS:
        raise ProtectedPresentationInstallationError(
            "installation record closed-field-set violation: "
            f"{sorted(set(document) ^ _INSTALLATION_FIELDS)}"
        )
    if document["installation_schema_version"] != INSTALLATION_SCHEMA_VERSION:
        raise ProtectedPresentationInstallationError("installation record schema version is not the frozen const")
    if document["mechanism_id"] != MECHANISM_ID or document["helper_implementation_id"] != MECHANISM_ID:
        raise ProtectedPresentationInstallationError("installation record mechanism/helper id is not the frozen const")
    digest = _require_hex64(document["installation_digest"], field="installation_digest")
    if _self_excluding_digest(document, digest_field="installation_digest") != digest:
        raise ProtectedPresentationInstallationError("installation record installation_digest does not recompute")
    installation_id = _require_installation_id(document["installation_id"])
    helper_path = _require_nonempty(document["helper_path"], field="helper_path")
    if not Path(helper_path).is_absolute():
        raise ProtectedPresentationInstallationError("installation record helper_path is not absolute")
    helper_sha256 = _require_hex64(document["helper_sha256"], field="helper_sha256")
    descriptor_digest = _require_hex64(document["descriptor_digest"], field="descriptor_digest")
    verifier_configuration_digest = _require_hex64(
        document["verifier_configuration_digest"], field="verifier_configuration_digest"
    )
    renderer_profile = _require_nonempty(document["renderer_profile"], field="renderer_profile")
    helper_implementation_version = _require_nonempty(
        document["helper_implementation_version"], field="helper_implementation_version"
    )
    generation = _require_generation(document["generation"])
    action = document["lifecycle_action"]
    if action not in LIFECYCLE_ACTIONS:
        raise ProtectedPresentationInstallationError("installation record lifecycle_action is outside the closed enum")
    status = document["status"]
    expected_status = "revoked" if action == "revoke" else "active"
    if status != expected_status:
        raise ProtectedPresentationInstallationError(
            f"installation record status {status!r} does not match lifecycle_action {action!r}"
        )
    _require_timestamp(document["installed_at"], field="installed_at")
    supersedes = _validate_supersedes(document["supersedes"], generation, digest_key="installation_digest")
    return InstallationRecord(
        document=document,
        installation_id=installation_id,
        mechanism_id=MECHANISM_ID,
        helper_path=helper_path,
        helper_sha256=helper_sha256,
        descriptor_digest=descriptor_digest,
        verifier_configuration_digest=verifier_configuration_digest,
        renderer_profile=renderer_profile,
        helper_implementation_version=helper_implementation_version,
        generation=generation,
        lifecycle_action=action,
        status=status,
        installation_digest=digest,
        supersedes=supersedes,
    )


# ─────────────────────────────────────────────────────────────────────────
# HPAC-PRESENTATION-CURRENT-GENERATION/1.0 (HPAC-PPA-REQ-018)
# ─────────────────────────────────────────────────────────────────────────

_ANCHOR_FIELDS = frozenset(
    {
        "current_generation_schema_version",
        "installation_id",
        "mechanism_id",
        "current_generation",
        "installation_digest",
        "descriptor_digest",
        "status",
        "updated_at",
        "anchor_digest",
    }
)
_ANCHOR_STATUS_VOCAB = frozenset({"active", "revoked"})


def build_current_generation_anchor(
    *,
    installation_id: str,
    current_generation: int,
    installation_digest: str,
    descriptor_digest: str,
    status: str,
    updated_at: str,
) -> dict:
    if status not in _ANCHOR_STATUS_VOCAB:
        raise ProtectedPresentationInstallationError(f"anchor status {status!r} is outside {sorted(_ANCHOR_STATUS_VOCAB)}")
    document = {
        "current_generation_schema_version": CURRENT_GENERATION_SCHEMA_VERSION,
        "installation_id": _require_installation_id(installation_id),
        "mechanism_id": MECHANISM_ID,
        "current_generation": _require_generation(current_generation, field="current_generation"),
        "installation_digest": _require_hex64(installation_digest, field="installation_digest"),
        "descriptor_digest": _require_hex64(descriptor_digest, field="descriptor_digest"),
        "status": status,
        "updated_at": _require_timestamp(updated_at, field="updated_at"),
        "anchor_digest": "",
    }
    document["anchor_digest"] = _self_excluding_digest(document, digest_field="anchor_digest")
    return document


def validate_current_generation_anchor(document: object) -> CurrentGenerationAnchor:
    if not isinstance(document, dict):
        raise ProtectedPresentationInstallationError("current-generation anchor is not an object")
    if set(document) != _ANCHOR_FIELDS:
        raise ProtectedPresentationInstallationError(
            "current-generation anchor closed-field-set violation: "
            f"{sorted(set(document) ^ _ANCHOR_FIELDS)}"
        )
    if document["current_generation_schema_version"] != CURRENT_GENERATION_SCHEMA_VERSION:
        raise ProtectedPresentationInstallationError("anchor schema version is not the frozen const")
    if document["mechanism_id"] != MECHANISM_ID:
        raise ProtectedPresentationInstallationError("anchor mechanism_id is not the frozen const")
    digest = _require_hex64(document["anchor_digest"], field="anchor_digest")
    if _self_excluding_digest(document, digest_field="anchor_digest") != digest:
        raise ProtectedPresentationInstallationError("anchor anchor_digest does not recompute")
    installation_id = _require_installation_id(document["installation_id"])
    current_generation = _require_generation(document["current_generation"], field="current_generation")
    installation_digest = _require_hex64(document["installation_digest"], field="installation_digest")
    descriptor_digest = _require_hex64(document["descriptor_digest"], field="descriptor_digest")
    status = document["status"]
    if status not in _ANCHOR_STATUS_VOCAB:
        raise ProtectedPresentationInstallationError("anchor status is outside the closed vocabulary")
    _require_timestamp(document["updated_at"], field="updated_at")
    return CurrentGenerationAnchor(
        document=document,
        installation_id=installation_id,
        mechanism_id=MECHANISM_ID,
        current_generation=current_generation,
        installation_digest=installation_digest,
        descriptor_digest=descriptor_digest,
        status=status,
        anchor_digest=digest,
    )


# ─────────────────────────────────────────────────────────────────────────
# Helper path + byte integrity (HPAC-PPA-REQ-010/011/012/029/030)
# ─────────────────────────────────────────────────────────────────────────


def helper_content_addressed_path(root: Path, helper_sha256: str) -> Path:
    """HPAC-PPA-REQ-010 — the fixed content-addressed helper path beneath
    the protected root. Not caller-selectable; derived only from the pinned
    digest."""

    digest = _require_hex64(helper_sha256, field="helper_sha256")
    return (Path(root) / _HELPER_INSTALL_SEGMENTS[0] / _HELPER_INSTALL_SEGMENTS[1] / digest / _HELPER_FILENAME)


@dataclass(frozen=True)
class VerifiedHelper:
    """A helper whose bytes have been opened once and verified. ``fd`` is an
    open read-only file descriptor addressing the *exact* validated object
    (HPAC-PPA-REQ-030 — validation and execution address the same opened
    object). The caller owns closing it."""

    fd: int
    sha256: str
    path: Path


def _reject_symlink_chain(path: Path, *, stop_at: Path) -> None:
    """HPAC-PPA-REQ-012 — the helper object and every existing ancestor from
    the protected root to it must be non-symlink."""

    path = Path(path)
    stop_at = Path(stop_at)
    components = [path]
    for parent in path.parents:
        components.append(parent)
        if parent == stop_at:
            break
    for component in components:
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ProtectedPresentationIntegrityError(f"cannot inspect helper component {component}: {exc!r}")
        if stat.S_ISLNK(mode):
            raise ProtectedPresentationIntegrityError(f"symlinked helper component: {component}")


def verify_helper_bytes(
    helper_path: Path,
    *,
    expected_sha256: str,
    deployment_owner_uid: int,
    protected_root: Path,
    configured_agent_writable=None,
) -> VerifiedHelper:
    """Open the fixed helper once with no symlink traversal, validate
    type / link count / owner / mode / ACL, hash the opened bytes, and
    require exact ``expected_sha256`` (HPAC-PPA-REQ-012/029). Returns the
    open fd so the launcher executes the same object (HPAC-PPA-REQ-030).

    ``configured_agent_writable`` is an optional callable
    ``(path) -> bool | None`` (the launcher supplies the resolved
    configured-agent ACL probe). ``True`` or ``None`` fails closed.
    """

    expected = _require_hex64(expected_sha256, field="expected_sha256")
    helper_path = Path(helper_path)
    _reject_symlink_chain(helper_path, stop_at=Path(protected_root))

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(helper_path, flags)
    except OSError as exc:
        raise ProtectedPresentationIntegrityError(f"cannot open helper {helper_path}: {exc!r}")
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise ProtectedPresentationIntegrityError(f"helper {helper_path} is not a regular file")
        if st.st_nlink != 1:
            raise ProtectedPresentationIntegrityError(f"helper {helper_path} does not have exactly one hard link")
        if st.st_uid != deployment_owner_uid:
            raise ProtectedPresentationIntegrityError(
                f"helper {helper_path} is not owned by the deployment owner (uid {deployment_owner_uid})"
            )
        if stat.S_IMODE(st.st_mode) & (stat.S_IWGRP | stat.S_IWOTH):
            raise ProtectedPresentationIntegrityError(f"helper {helper_path} is group- or other-writable")
        if configured_agent_writable is not None:
            writable = configured_agent_writable(helper_path)
            if writable is not False:
                raise ProtectedPresentationIntegrityError(
                    f"helper {helper_path} is writable by the configured agent principal or indeterminate"
                )
        digest = hashlib.sha256()
        while True:
            chunk = os.read(fd, 1 << 20)
            if not chunk:
                break
            digest.update(chunk)
        actual = digest.hexdigest()
        if actual != expected:
            raise ProtectedPresentationIntegrityError(
                f"helper {helper_path} opened-byte SHA-256 {actual} != pinned {expected}"
            )
        os.lseek(fd, 0, os.SEEK_SET)
    except BaseException:
        os.close(fd)
        raise
    return VerifiedHelper(fd=fd, sha256=actual, path=helper_path)


# ─────────────────────────────────────────────────────────────────────────
# Canonical store
# ─────────────────────────────────────────────────────────────────────────


class ProtectedPresentationInstallationStore:
    """Canonical store for the ``pcae-protected-local-presentation`` helper
    installation lineage under one :class:`HPACStoreAuthority`.

    Resolution (:meth:`resolve_current_generation`) is read-only and used by
    the launcher and the HPAC verifier. Mutation
    (:meth:`apply_configuration`) requires a bounded
    ``configure_presentation_mechanism`` PAWA capability and is driven only
    by :mod:`pcae.core.hpac_protected_presentation_admin`.
    """

    def __init__(self, authority: HPACStoreAuthority) -> None:
        if not isinstance(authority, HPACStoreAuthority):
            raise ProtectedPresentationInstallationError("an HPACStoreAuthority is required")
        self._authority = authority
        self._root = authority.root
        self._descriptor_store = PresentationMechanismDescriptorStore(authority)

    @property
    def authority(self) -> HPACStoreAuthority:
        return self._authority

    # -- paths ----------------------------------------------------------

    def _mechanism_dir(self) -> Path:
        path = self._root
        for segment in _MECHANISM_DIR_SEGMENTS:
            path = path / segment
        return path

    def _descriptor_path(self) -> Path:
        return self._mechanism_dir() / "descriptor.json"

    def _installation_path(self, generation: int) -> Path:
        return self._mechanism_dir() / "installations" / str(_require_generation(generation)) / "installation.json"

    def _anchor_path(self) -> Path:
        return self._mechanism_dir() / "current-generation.json"

    def helper_path_for(self, helper_sha256: str) -> Path:
        return helper_content_addressed_path(self._root, helper_sha256)

    # -- resolution (HPAC-PPA-REQ-019/020) -----------------------------

    def resolve_current_generation(self) -> Optional[ResolvedCurrentGeneration]:
        anchor_path = self._anchor_path()
        reject_symlink(anchor_path)
        if not anchor_path.exists():
            return None
        try:
            anchor = validate_current_generation_anchor(read_canonical_json_document(anchor_path))
        except HPACFoundationError as exc:
            raise ProtectedPresentationIntegrityError(f"current-generation anchor is unreadable/malformed: {exc}")

        record_path = self._installation_path(anchor.current_generation)
        reject_symlink(record_path)
        if not record_path.exists():
            raise ProtectedPresentationIntegrityError(
                f"no installation record for the anchored generation {anchor.current_generation}"
            )
        try:
            record = validate_installation_record(read_canonical_json_document(record_path))
        except HPACFoundationError as exc:
            raise ProtectedPresentationIntegrityError(f"installation record is unreadable/malformed: {exc}")

        # HPAC-PPA-REQ-019 — anchor and immutable record must agree exactly.
        if (
            record.installation_id != anchor.installation_id
            or record.mechanism_id != anchor.mechanism_id
            or record.generation != anchor.current_generation
            or record.installation_digest != anchor.installation_digest
            or record.descriptor_digest != anchor.descriptor_digest
        ):
            raise ProtectedPresentationIntegrityError("anchor and installation record disagree")
        anchor_status_from_action = "revoked" if record.lifecycle_action == "revoke" else "active"
        if anchor.status != anchor_status_from_action:
            raise ProtectedPresentationIntegrityError("anchor status disagrees with the installation record")

        # Writer provenance (HPAC-PPA-REQ-015/020) — installer role, subject
        # the exact mechanism id, on both the anchor and the record.
        for path, digest in (
            (record_path, record.installation_digest),
            (anchor_path, anchor.anchor_digest),
        ):
            try:
                self._authority.verify_record(
                    path, digest, roles=frozenset({INSTALLER_WRITER_ROLE}), subject=MECHANISM_ID
                )
            except HPACAuthorityError as exc:
                raise ProtectedPresentationIntegrityError(f"installer provenance verification failed for {path.name}: {exc}")

        # HPAC-PPA-REQ-016/019 — the HPAC-REQ-090 descriptor must agree.
        installed = self._descriptor_store.resolve_canonical(MECHANISM_ID)
        if installed is None:
            raise ProtectedPresentationIntegrityError("no installed HPAC-REQ-090 descriptor for the mechanism")
        try:
            descriptor = self._authority.require_resolution(installed)
        except HPACAuthorityError as exc:
            raise ProtectedPresentationIntegrityError(f"descriptor resolution belongs to another root: {exc}")
        if descriptor.descriptor_schema_version != PRESENTATION_MECHANISM_SCHEMA_VERSION:
            raise ProtectedPresentationIntegrityError("descriptor schema version is not the frozen const")
        if descriptor.mechanism_id != MECHANISM_ID or descriptor.verifier_kind != VERIFIER_KIND:
            raise ProtectedPresentationIntegrityError("descriptor mechanism_id / verifier_kind mismatch")
        if (
            descriptor.descriptor_digest != record.descriptor_digest
            or descriptor.verifier_configuration_digest != record.verifier_configuration_digest
            or descriptor.renderer_profile != record.renderer_profile
        ):
            raise ProtectedPresentationIntegrityError("descriptor digest/config/renderer disagree with the record")

        expected_descriptor_status = "revoked" if record.lifecycle_action == "revoke" else "active"
        if descriptor.status != expected_descriptor_status:
            raise ProtectedPresentationIntegrityError("descriptor status disagrees with the installation record")

        if anchor.status == "revoked" or record.status == "revoked":
            raise ProtectedPresentationIntegrityError("current generation is revoked; production presentation is unavailable")
        if not (
            descriptor.protected_output
            and descriptor.agent_substitution_resistant
            and descriptor.canonical_subject_rendering
            and descriptor.explicit_election_support
        ):
            raise ProtectedPresentationIntegrityError("descriptor protection guarantees are not all true")

        helper_path = Path(record.helper_path)
        expected_helper_path = self.helper_path_for(record.helper_sha256)
        if helper_path != expected_helper_path:
            raise ProtectedPresentationIntegrityError(
                "installation record helper_path is not the content-addressed path for its helper_sha256"
            )

        return ResolvedCurrentGeneration(
            anchor=anchor,
            record=record,
            descriptor=descriptor,
            mechanism_dir=self._mechanism_dir(),
            helper_path=helper_path,
        )

    # -- configuration transaction (HPAC-PPA-REQ-023) ------------------

    def apply_configuration(
        self,
        capability: HPACWriterCapability,
        *,
        action: str,
        helper_sha256: str,
        helper_implementation_version: str,
        verifier_configuration_digest: str,
        renderer_profile: str,
        descriptor_version: str,
        installed_at: str,
        installation_id: Optional[str] = None,
    ) -> ResolvedCurrentGeneration:
        """Apply exactly one ``install`` / ``rotate`` / ``revoke``
        configuration transaction as a single bounded multi-write: the
        HPAC-REQ-090 descriptor, the immutable installation-generation
        record, the current-generation anchor, and their writer-provenance
        sidecars, then ``complete_multi_write`` exactly once.

        The ``capability`` MUST be a bounded ``configure_presentation_mechanism``
        PAWA capability minted for ``subject == MECHANISM_ID`` with role
        ``presentation_mechanism_installer`` (HPAC-PPA-REQ-005/023).
        """

        if action not in LIFECYCLE_ACTIONS:
            raise ProtectedPresentationInstallationError(f"action {action!r} is outside the closed enum {LIFECYCLE_ACTIONS}")

        current = self._resolve_current_generation_or_none_for_config()

        if action == "install":
            if current is not None:
                raise ProtectedPresentationInstallationError(
                    "an ACTIVE presentation-mechanism installation already exists; "
                    "use rotate/revoke, never a silent reset (HPAC-PPA-REQ-024)"
                )
            generation = 1
            supersedes = None
            installation_id = _require_installation_id(installation_id or new_installation_id())
        else:
            if current is None:
                raise ProtectedPresentationInstallationError(
                    f"{action} requires a current active generation (HPAC-PPA-REQ-025/026)"
                )
            if current.record.lifecycle_action == "revoke" or current.anchor.status == "revoked":
                raise ProtectedPresentationInstallationError("the current generation is revoked; reprovision via install")
            generation = current.anchor.current_generation + 1
            supersedes = {
                "generation": current.anchor.current_generation,
                "installation_digest": current.anchor.installation_digest,
            }
            installation_id = current.anchor.installation_id
            if action == "revoke":
                helper_sha256 = current.record.helper_sha256
                helper_implementation_version = current.record.helper_implementation_version
                verifier_configuration_digest = current.record.verifier_configuration_digest
                renderer_profile = current.record.renderer_profile
                descriptor_version = current.descriptor.descriptor_version

        _require_hex64(helper_sha256, field="helper_sha256")
        helper_path = self.helper_path_for(helper_sha256)
        descriptor_status = "revoked" if action == "revoke" else "active"

        if action in ("install", "rotate"):
            # HPAC-PPA-REQ-004/010/025 — the helper bytes must already be
            # installed out of band at the derived content-addressed path and
            # hash to the pinned digest. This module never writes those bytes.
            try:
                verified = verify_helper_bytes(
                    helper_path,
                    expected_sha256=helper_sha256,
                    deployment_owner_uid=os.getuid(),
                    protected_root=self._root,
                )
            except ProtectedPresentationIntegrityError as exc:
                raise ProtectedPresentationInstallationError(
                    f"out-of-band helper bytes are absent or non-canonical at the derived path: {exc}"
                )
            os.close(verified.fd)

        descriptor = PresentationMechanismDescriptor(
            descriptor_schema_version=PRESENTATION_MECHANISM_SCHEMA_VERSION,
            mechanism_id=MECHANISM_ID,
            descriptor_version=_require_nonempty(descriptor_version, field="descriptor_version"),
            verifier_kind=VERIFIER_KIND,
            verifier_configuration_digest=_require_hex64(
                verifier_configuration_digest, field="verifier_configuration_digest"
            ),
            renderer_profile=_require_nonempty(renderer_profile, field="renderer_profile"),
            protected_output=True,
            agent_substitution_resistant=True,
            canonical_subject_rendering=True,
            explicit_election_support=True,
            status=descriptor_status,
        )
        descriptor_digest = canonical_digest(descriptor.to_document(include_digest=False))
        sealed_descriptor = PresentationMechanismDescriptor(
            **{**descriptor.__dict__, "descriptor_digest": descriptor_digest}
        )

        record_doc = build_installation_record(
            installation_id=installation_id,
            helper_path=str(helper_path),
            helper_sha256=helper_sha256,
            helper_implementation_version=helper_implementation_version,
            descriptor_digest=descriptor_digest,
            verifier_configuration_digest=descriptor.verifier_configuration_digest,
            renderer_profile=descriptor.renderer_profile,
            generation=generation,
            lifecycle_action=action,
            installed_at=installed_at,
            supersedes=supersedes,
        )
        anchor_doc = build_current_generation_anchor(
            installation_id=installation_id,
            current_generation=generation,
            installation_digest=record_doc["installation_digest"],
            descriptor_digest=descriptor_digest,
            status=descriptor_status,
            updated_at=installed_at,
        )

        with self._authority.writer_transaction(capability, INSTALLER_WRITER_ROLE, subject=MECHANISM_ID):
            self._write_record(
                self._descriptor_path(),
                canonical_json_bytes(sealed_descriptor.to_document(include_digest=True)),
                descriptor_digest,
                capability,
                replace=(action != "install"),
            )
            record_path = self._installation_path(generation)
            self._write_record(
                record_path,
                canonical_json_bytes(record_doc),
                record_doc["installation_digest"],
                capability,
                replace=False,
            )
            anchor_path = self._anchor_path()
            self._write_record(
                anchor_path,
                canonical_json_bytes(anchor_doc),
                anchor_doc["anchor_digest"],
                capability,
                replace=(action != "install"),
            )
            # HPAC-PPA-REQ-017 — read-back verify the anchor within the txn.
            read_back = validate_current_generation_anchor(read_canonical_json_document(anchor_path))
            if read_back.anchor_digest != anchor_doc["anchor_digest"]:
                raise ProtectedPresentationInstallationError("anchor read-back digest mismatch inside the transaction")

        self._authority.complete_multi_write(capability)

        if action == "revoke":
            # A revoked generation deliberately fails ``resolve_current_generation``
            # (fail-closed for the launcher / verifier). Return a direct view of
            # the just-written revoked lineage for the admin tool's report.
            return ResolvedCurrentGeneration(
                anchor=validate_current_generation_anchor(anchor_doc),
                record=validate_installation_record(record_doc),
                descriptor=sealed_descriptor,
                mechanism_dir=self._mechanism_dir(),
                helper_path=helper_path,
            )
        resolved = self.resolve_current_generation()
        if resolved is None:
            raise ProtectedPresentationInstallationError("configuration transaction did not produce a resolvable generation")
        return resolved

    # -- internals ----------------------------------------------------

    def _resolve_current_generation_or_none_for_config(self) -> Optional[ResolvedCurrentGeneration]:
        try:
            return self.resolve_current_generation()
        except ProtectedPresentationIntegrityError:
            # A damaged / unresolvable lineage is not a valid base for
            # rotate/revoke and is not "no installation" for install —
            # HPAC-PPA-REQ-024/027 require an explicit reprovision.
            raise ProtectedPresentationInstallationError(
                "the existing installation lineage is unresolvable; explicit deployment-owner "
                "reprovision is required (HPAC-PPA-REQ-027)"
            )

    def _write_record(
        self,
        path: Path,
        payload: bytes,
        digest: str,
        capability: HPACWriterCapability,
        *,
        replace: bool,
    ) -> None:
        reject_symlink(path)
        if replace:
            write_atomic_replace(path, payload)
        else:
            write_atomic_create_only(path, payload)
        os.chmod(path, 0o600)
        self._authority.record_write(
            path,
            digest,
            capability,
            role=INSTALLER_WRITER_ROLE,
            subject=MECHANISM_ID,
            replace=replace,
        )
