"""HPAC-PAWA-001 v4.0 / HPAC-PAWA-HELPER-001 v5.0 -- the shared, neutral
§33 positive-recognition core (steps 1-8 only).

Phase 150G (N16-5-F-5-TB-HELPER-ADMISSION-RECOGNITION-CORE-IMPLEMENTATION)
realizes the Model B architecture Phase 150F selected: steps 1-8 of
``hpac_protected_admin_writer._run_recognition_sequence`` extracted into
one neutral module, safely importable by both the legacy
``hpac_protected_admin_writer.py`` factory and a future privileged-helper
implementation (helper wiring itself is explicitly deferred; see below).

**This module is read-only and non-authoritative.** It resolves and
validates the ``.authority/`` protected-record chain and the
configured-agent-exclusion boundary for a caller-supplied protected root,
and returns an ordinary, immutable, descriptive result
(:class:`RecognizedAnchorFacts`). It does not mint, hold, or export any
writer/helper authority object, capability, or seal:

    recognition result != authority
    recognition result != writer capability
    recognition result != permission to mutate
    recognition result != helper admission
    recognition result != PB permission
    recognition result != runtime capability

Trust derives from *performing* the steps below against live, current
protected state on every call -- never from possession of the returned
object. No caching, no memoization, no process-lifetime pin: every call
re-reads live state (HPAC-PAWA-REQ-075's "runs fresh on every call"
property, preserved here for the shared steps).

**This module is non-agent-importable**, mirroring
``hpac_protected_admin_writer.py``'s own REQ-084/085 fence: ordinary
agent / runtime / Gate / plugin / ``pcae`` CLI code SHALL NOT import it.
It is not a ``pcae`` CLI subcommand and is not in any dispatch table.

**Explicitly NOT done here (deferred, not begun by Phase 150G):**
step 9 (the authorized-factory-consumer check -- stays in the legacy
factory, since its enumerated allowlist is factory-specific, §32/§38),
step 10/11 (configured-agent binding and capability minting -- stay in
the legacy factory, since they require ``_PRODUCTION_WRITER_FACTORY_SEAL``,
which this module never imports and never will), any privileged-helper
admission wiring, and any helper-side "step 9-prime" definition.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import (
    HPACFoundationError,
    canonical_digest,
    read_canonical_json_document,
    reject_symlink,
)
from pcae.core.hpac_pawa_agent_exclusion import (
    AgentExclusionError,
    ConfiguredAgentAuthorityIdentity,
    resolve_configured_agent_identity,
)
from pcae.core.hpac_pawa_schemas import (
    AUTHORITY_NAMESPACE,
    PawaSchemaError,
    validate_authority_descriptor,
    validate_current_generation,
)

_DESCRIPTOR_NAME = "deployment-owner.json"
_CURRENT_GENERATION_NAME = "current-generation.json"
_AGENT_EXCLUSION_NAME = "agent-exclusion.json"
_MANIFEST_NAME = "manifest.json"
_PROVENANCE_DIR = "provenance"
_PROVENANCE_SCHEMA = "HPAC-WRITER-PROVENANCE/1.0"
_ANCHOR_WRITER_ROLE = "hpac_pawa_protected_admin"

#: The closed, read-only failure vocabulary this module raises. Every
#: value here is a member of the legacy ``PAWA_FAILURE_CODES`` set (the
#: legacy factory's ``_run_recognition_sequence`` re-wraps a
#: :class:`RecognitionError` raised here into its own ``PawaError`` with
#: the identical ``code``/``detail``, so the closed vocabulary and every
#: downstream ``rhamp_terminal_reason`` mapping are preserved unchanged).
RECOGNITION_FAILURE_CODES = frozenset(
    {
        "protected_root_missing",
        "protected_root_untrusted",
        "descriptor_missing",
        "descriptor_malformed",
        "descriptor_revoked",
        "descriptor_root_identity_mismatch",
        "descriptor_installation_mismatch",
        "descriptor_generation_stale",
        "descriptor_wrong_owner",
        "descriptor_wrong_mode",
        "agent_principal_unknown",
        "agent_has_protected_write_authority",
        "current_context_is_agent",
        "write_probe_failed",
        "internal_fail_closed",
    }
)


class RecognitionError(Exception):
    """A terminal, read-only recognition failure. ``code`` is exactly one
    member of :data:`RECOGNITION_FAILURE_CODES` -- never a free-form
    reason string, mirroring the legacy ``PawaError`` discipline this
    module intentionally does not import (no reverse dependency on the
    legacy factory module)."""

    def __init__(self, code: str, detail: str = "") -> None:
        if code not in RECOGNITION_FAILURE_CODES:
            raise AssertionError(f"non-vocabulary recognition_failure_code: {code!r}")
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class TopologyProbe:
    """Disclosed test-only seam (HPAC-PAWA-REQ-132/166), moved here
    unchanged from ``hpac_protected_admin_writer.py`` because it is this
    module's own steps (3/7) that consume it. A deterministic
    ``(effective_write_access, ancestor_chain_safe)`` pair standing in for
    the platform ACL adapter, unavailable in sandboxed CI. Each callable
    has the exact signature of its ``hatp_class_b_topology_verifier``
    counterpart. A guard test asserts no non-test module constructs or
    passes one. Purely descriptive -- carries two arbitrary callables,
    never an authority object."""

    effective_write_access: object
    ancestor_chain_safe: object


def _real_topology():
    from pcae.core.hatp_class_b_topology_verifier import (
        _ancestor_chain_safe,
        _effective_write_access,
    )

    return _effective_write_access, _ancestor_chain_safe


@dataclass(frozen=True)
class RecognizedAnchorFacts:
    """The steps-1-8 recognition result. Purely descriptive: every field
    is an ordinary value (path, dict, str, int, or the pre-existing
    :class:`ConfiguredAgentAuthorityIdentity`, itself descriptive per its
    own docstring -- "its authority basis is live effective filesystem
    write access, never the uid integer itself"). No field carries a
    capability, seal, or authority object. Recognition result structure
    != trusted provenance: trust came from the checks that produced this
    value, not from holding it."""

    root: Path
    live_root_identity: dict
    live_root_identity_digest: str
    anchor_id: str
    installation_id: str
    generation: int
    configured_agent: ConfiguredAgentAuthorityIdentity


def _authority_dir(root: Path) -> Path:
    return root / AUTHORITY_NAMESPACE


def _root_identity(root: Path) -> dict:
    st = root.stat()
    return {"device": st.st_dev, "inode": st.st_ino}


def _reject_component_symlinks(path: Path) -> None:
    for component in (path, *Path(path).parents):
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise RecognitionError("protected_root_untrusted", f"cannot inspect {component}: {exc!r}")
        if stat.S_ISLNK(mode):
            raise RecognitionError("protected_root_untrusted", f"symlinked protected component: {component}")


def _read_protected_json(path: Path, *, missing_code: str, malformed_code: str) -> object:
    _reject_component_symlinks(path)
    if not path.exists():
        raise RecognitionError(missing_code, f"absent: {path}")
    if path.is_symlink():
        raise RecognitionError(malformed_code, f"symlink: {path}")
    try:
        st = path.stat()
    except OSError as exc:
        raise RecognitionError(malformed_code, f"cannot stat {path}: {exc!r}")
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise RecognitionError(malformed_code, f"not a single-link regular file: {path}")
    try:
        return read_canonical_json_document(path)
    except HPACFoundationError as exc:
        raise RecognitionError(malformed_code, f"non-canonical / malformed record {path}: {exc}")


def _require_owner_and_mode(
    path: Path,
    *,
    root_owner_uid: int,
    wrong_owner_code: str,
    wrong_mode_code: str,
) -> None:
    try:
        st = path.lstat()
    except OSError as exc:
        raise RecognitionError(wrong_mode_code, f"cannot lstat {path}: {exc!r}")
    if st.st_uid != root_owner_uid:
        raise RecognitionError(wrong_owner_code, f"{path} is not owned by the deployment owner (uid {root_owner_uid})")
    if stat.S_IMODE(st.st_mode) & (stat.S_IWGRP | stat.S_IWOTH):
        raise RecognitionError(wrong_mode_code, f"{path} is group- or other-writable")


def _require_not_configured_agent_writable(
    path: Path,
    identity: ConfiguredAgentAuthorityIdentity,
    effective_write_access,
    *,
    code: str,
) -> None:
    writable, reason, _evidence = effective_write_access(path, identity.uid, identity.gids)
    if writable is not False:
        raise RecognitionError(code, f"configured agent can write {path}: {reason}")


def _exclusion_provenance_ref(document: object) -> str:
    if isinstance(document, dict) and isinstance(document.get("provenance_ref"), str):
        return document["provenance_ref"]
    return ""


def _verify_provenance(
    root: Path,
    *,
    record_relative_posix: str,
    record_digest: str,
    live_root_identity_digest: str,
    provenance_ref: str,
    malformed_code: str,
    root_identity_code: str,
) -> None:
    import hashlib

    key = hashlib.sha256(record_relative_posix.encode("utf-8")).hexdigest()
    provenance_path = _authority_dir(root) / _PROVENANCE_DIR / f"{key}.json"
    document = _read_protected_json(
        provenance_path, missing_code=malformed_code, malformed_code=malformed_code
    )
    if not isinstance(document, dict) or set(document) != {
        "schema_version",
        "store_id",
        "authority_class",
        "root_identity_digest",
        "record_relative_path",
        "record_digest",
        "writer_role",
        "writer_subject",
    }:
        raise RecognitionError(malformed_code, f"provenance {provenance_path} has an invalid closed schema")
    if document["schema_version"] != _PROVENANCE_SCHEMA:
        raise RecognitionError(malformed_code, "provenance schema_version unsupported")
    if document["authority_class"] != "production":
        raise RecognitionError(malformed_code, "provenance authority_class is not 'production'")
    if document["root_identity_digest"] != live_root_identity_digest:
        raise RecognitionError(root_identity_code, "provenance root_identity_digest does not match the live root")
    if document["record_relative_path"] != record_relative_posix:
        raise RecognitionError(malformed_code, "provenance record_relative_path mismatch")
    if document["record_digest"] != record_digest:
        raise RecognitionError(malformed_code, "provenance record_digest mismatch")
    if document["writer_role"] != _ANCHOR_WRITER_ROLE:
        raise RecognitionError(malformed_code, "provenance writer_role is not the protected-admin role")
    if provenance_ref != f"{_PROVENANCE_DIR}/{key}.json":
        raise RecognitionError(malformed_code, "record provenance_ref does not name its provenance record")


def _positive_write_probe(authority_dir: Path) -> None:
    """§28 / §29 / §30 -- operation-based proof that the current
    invocation holds real OS-authorized write over ``.authority/`` now.
    Dedicated random sentinel, O_CREAT|O_EXCL|O_NOFOLLOW, write + fsync +
    close + unlink -- self-cleaning, no lasting state change (already
    confirmed mutation-free by Phase 150F's own analysis)."""

    sentinel = authority_dir / f".probe-{os.urandom(16).hex()}"
    reject_symlink(sentinel)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(sentinel, flags, 0o600)
    except OSError as exc:
        raise RecognitionError("write_probe_failed", f"probe create failed: {exc!r}")
    try:
        os.write(fd, b"hpac-pawa-probe\n")
        os.fsync(fd)
    except OSError as exc:
        raise RecognitionError("write_probe_failed", f"probe write failed: {exc!r}")
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    try:
        os.unlink(sentinel)
    except OSError as exc:
        raise RecognitionError("write_probe_failed", f"probe sentinel could not be unlinked: {exc!r}")


def recognize_protected_anchor(
    *,
    root: Path,
    configured_agent_identity_source,
    topology_probe: Optional[TopologyProbe] = None,
) -> RecognizedAnchorFacts:
    """§33 steps 1 (root-content checks only; the canonical-root
    *resolution* itself stays with the caller, which alone is entitled to
    construct an ``HPACStoreAuthority`` -- this function never imports or
    references that type), 4, 5, 6, 2, 3, 7, 8 -- in that exact original
    order, since step 4-5-6's provenance verification depends on step 1's
    identity digest, and step 2-3's exclusion resolution depends on step
    4-5-6's descriptor/current-generation facts. Every step required; no
    step is skippable.

    ``root`` is an ordinary, already-resolved filesystem path (the
    caller's ``HPACStoreAuthority.root`` or equivalent) -- a location, not
    an authority. Fails closed with :class:`RecognitionError` on any
    failure, including any unexpected internal exception
    (``internal_fail_closed``, mirroring the legacy factory's own §0
    fail-closed boundary).
    """

    if topology_probe is not None:
        effective_write_access = topology_probe.effective_write_access
        ancestor_chain_safe = topology_probe.ancestor_chain_safe
    else:
        effective_write_access, ancestor_chain_safe = _real_topology()
    try:
        # STEP 1 — root-content checks (resolution itself is the caller's).
        _reject_component_symlinks(root)
        if not root.exists():
            raise RecognitionError("protected_root_missing", f"{root} is absent")
        if root.is_symlink() or not root.is_dir():
            raise RecognitionError("protected_root_untrusted", f"{root} is a symlink or not a directory")
        try:
            root_owner_uid = root.stat().st_uid
        except OSError as exc:
            raise RecognitionError("protected_root_untrusted", f"cannot stat {root}: {exc!r}")
        if stat.S_IMODE(root.stat().st_mode) & (stat.S_IWGRP | stat.S_IWOTH):
            raise RecognitionError("protected_root_untrusted", "protected root is group- or other-writable")
        authority_dir = _authority_dir(root)
        _reject_component_symlinks(authority_dir)
        if not authority_dir.is_dir():
            raise RecognitionError("protected_root_missing", "the .authority/ namespace is absent")
        live_root_identity = _root_identity(root)
        live_root_identity_digest = canonical_digest(live_root_identity)

        # STEP 4 — HPAC-STORE-AUTHORITY/1.0 manifest + {device,inode}.
        manifest_path = authority_dir / _MANIFEST_NAME
        manifest = _read_protected_json(
            manifest_path,
            missing_code="protected_root_missing",
            malformed_code="protected_root_untrusted",
        )
        if (
            not isinstance(manifest, dict)
            or set(manifest) != {"schema_version", "store_id", "authority_class", "root_identity"}
            or manifest["schema_version"] != "HPAC-STORE-AUTHORITY/1.0"
            or manifest["authority_class"] != "production"
        ):
            raise RecognitionError("protected_root_untrusted", "store-authority manifest has an invalid closed schema")
        manifest_root_identity = manifest["root_identity"]
        if manifest_root_identity != live_root_identity:
            raise RecognitionError("protected_root_untrusted", "HPAC root was copied or replaced; {device,inode} binding failed")
        _require_owner_and_mode(
            authority_dir,
            root_owner_uid=root_owner_uid,
            wrong_owner_code="protected_root_untrusted",
            wrong_mode_code="protected_root_untrusted",
        )

        # STEP 5 — the authority descriptor.
        descriptor_path = authority_dir / _DESCRIPTOR_NAME
        descriptor_doc = _read_protected_json(
            descriptor_path, missing_code="descriptor_missing", malformed_code="descriptor_malformed"
        )
        _require_owner_and_mode(
            descriptor_path,
            root_owner_uid=root_owner_uid,
            wrong_owner_code="descriptor_wrong_owner",
            wrong_mode_code="descriptor_wrong_mode",
        )
        try:
            descriptor = validate_authority_descriptor(descriptor_doc)
        except PawaSchemaError as exc:
            raise RecognitionError("descriptor_malformed", str(exc))
        if descriptor.protected_root_identity != live_root_identity or descriptor.protected_root_identity != manifest_root_identity:
            raise RecognitionError("descriptor_root_identity_mismatch", "descriptor protected_root_identity != live root / manifest")
        if descriptor.state == "REVOKED":
            raise RecognitionError("descriptor_revoked", "descriptor state is REVOKED")
        if descriptor.state != "ACTIVE":
            raise RecognitionError("descriptor_malformed", f"descriptor state is {descriptor.state}, not ACTIVE")

        # STEP 6 — the current-generation anchor (v1.1 closed 7-field set).
        current_generation_path = authority_dir / _CURRENT_GENERATION_NAME
        cg_doc = _read_protected_json(
            current_generation_path,
            missing_code="descriptor_installation_mismatch",
            malformed_code="descriptor_installation_mismatch",
        )
        _require_owner_and_mode(
            current_generation_path,
            root_owner_uid=root_owner_uid,
            wrong_owner_code="descriptor_wrong_owner",
            wrong_mode_code="descriptor_wrong_mode",
        )
        try:
            current_generation = validate_current_generation(cg_doc)
        except PawaSchemaError as exc:
            raise RecognitionError("descriptor_installation_mismatch", str(exc))
        if current_generation.installation_id != descriptor.installation_id:
            raise RecognitionError("descriptor_installation_mismatch", "descriptor installation_id != current-generation")
        if descriptor.generation > current_generation.current_generation:
            raise RecognitionError("descriptor_installation_mismatch", "descriptor generation is ahead of the anchor")
        if descriptor.generation < current_generation.current_generation:
            raise RecognitionError("descriptor_generation_stale", "a superseded descriptor cannot mint (rollback)")
        if descriptor.descriptor_digest != current_generation.descriptor_digest:
            raise RecognitionError("descriptor_installation_mismatch", "descriptor digest != anchored descriptor_digest")
        _verify_provenance(
            root,
            record_relative_posix=f"{AUTHORITY_NAMESPACE}/{_DESCRIPTOR_NAME}",
            record_digest=descriptor.descriptor_digest,
            live_root_identity_digest=live_root_identity_digest,
            provenance_ref=descriptor.provenance_ref,
            malformed_code="descriptor_malformed",
            root_identity_code="descriptor_root_identity_mismatch",
        )

        # STEP 2 — the configured-agent-principal resolution source
        # (HPAC-PAWA-AGENT-EXCLUSION/1.0). v1.1 atomic substeps.
        exclusion_path = authority_dir / _AGENT_EXCLUSION_NAME
        try:
            exclusion_doc = _read_protected_json(
                exclusion_path, missing_code="agent_principal_unknown", malformed_code="agent_principal_unknown"
            )
            _require_owner_and_mode(
                exclusion_path,
                root_owner_uid=root_owner_uid,
                wrong_owner_code="agent_principal_unknown",
                wrong_mode_code="agent_principal_unknown",
            )
            configured_agent = resolve_configured_agent_identity(
                exclusion_doc,
                installation_id=descriptor.installation_id,
                live_root_identity=live_root_identity,
                manifest_root_identity=manifest_root_identity,
                anchor_agent_exclusion_digest=current_generation.agent_exclusion_digest,
                _configured_agent_identity_source=configured_agent_identity_source,
            )
        except AgentExclusionError as exc:
            raise RecognitionError("agent_principal_unknown", str(exc))
        _verify_provenance(
            root,
            record_relative_posix=f"{AUTHORITY_NAMESPACE}/{_AGENT_EXCLUSION_NAME}",
            record_digest=configured_agent.record_digest,
            live_root_identity_digest=live_root_identity_digest,
            provenance_ref=_exclusion_provenance_ref(exclusion_doc),
            malformed_code="agent_principal_unknown",
            root_identity_code="agent_principal_unknown",
        )

        # STEP 3 — configured-agent exclusion + safe ancestors (F-1: the
        # CONFIGURED agent identity, NOT os.geteuid()).
        from pcae.core.hatp_class_b_topology_verifier import _current_agent_identity

        writable, reason, _ev = effective_write_access(root, configured_agent.uid, configured_agent.gids)
        ancestors_safe, diagnostics = ancestor_chain_safe(root, configured_agent.uid, configured_agent.gids)
        if writable is True:
            raise RecognitionError("agent_has_protected_write_authority", f"configured agent can write the root: {reason}")
        if writable is None or ancestors_safe is None:
            raise RecognitionError("protected_root_untrusted", f"indeterminate permissions: {reason} / {diagnostics}")
        if ancestors_safe is not True:
            raise RecognitionError("agent_has_protected_write_authority", f"configured-agent-writable ancestor: {diagnostics}")
        _require_not_configured_agent_writable(
            authority_dir, configured_agent, effective_write_access, code="agent_has_protected_write_authority"
        )
        _require_not_configured_agent_writable(
            descriptor_path, configured_agent, effective_write_access, code="agent_has_protected_write_authority"
        )
        _require_not_configured_agent_writable(
            exclusion_path, configured_agent, effective_write_access, code="agent_has_protected_write_authority"
        )

        # STEP 7 — the current administrative context is NOT the
        # configured agent principal (live uid vs. resolved configured
        # agent uid; never an agent_id label, never groups alone).
        live_uid, _live_gids = _current_agent_identity()
        if live_uid == configured_agent.uid:
            raise RecognitionError("current_context_is_agent", "the current invocation is running as the configured agent account")

        # STEP 8 — the positive O_EXCL|O_NOFOLLOW write probe (current
        # invoking process; §28/§29).
        _positive_write_probe(authority_dir)

        return RecognizedAnchorFacts(
            root=root,
            live_root_identity=live_root_identity,
            live_root_identity_digest=live_root_identity_digest,
            anchor_id=descriptor.anchor_id,
            installation_id=descriptor.installation_id,
            generation=descriptor.generation,
            configured_agent=configured_agent,
        )
    except RecognitionError:
        raise
    except Exception as exc:  # noqa: BLE001 -- deliberate fail-closed boundary, mirrors §0.
        raise RecognitionError("internal_fail_closed", f"{type(exc).__name__}: {exc}") from exc
