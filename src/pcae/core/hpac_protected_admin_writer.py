"""HPAC-PAWA-001 v1.1 — the PRODUCTION protected-admin writer anchor:
the §33 positive recognition sequence, the ``production_writer`` factory,
the one-operation capability lifetime, the closed 21-value failure
taxonomy, the ``.authority/`` protected record I/O, and the bounded
protected principal-administration operations.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 (Slice 1). FIDO2-free. No RHAMP
credential sidecar, no ``RHAMP-COUNTER-STATE``, no enrollment ceremony, no
FIDO2 authenticator, no real-mechanism verifier branch, no eligible-mechanism
allowlist widening, no Gate wiring, no runtime / effect change.

**This module is the non-agent-importable admin-writer fence**
(HPAC-PAWA-REQ-084/085). Ordinary agent / runtime / Gate / plugin /
``pcae`` CLI code SHALL NOT import it — directly or transitively — and a
guard test (the fresh ``.1R.30R.3.1`` suite) enforces that against
``src/pcae/cli.py``, ``src/pcae/commands/**``, and
``src/pcae/core/agent.py``. It is not a ``pcae`` CLI subcommand and is not
in any dispatch table. The out-of-band ``provision`` / ``set-agent-exclusion``
/ ``rotate`` / ``revoke`` operations and the bounded principal-admin
operations are driven by the standalone ``scripts/hpac_protected_root_admin.py``,
run by an operator logged in as the deployment owner — the only principal
with real OS write access to ``<HPAC_PROTECTED_ROOT>`` (HPAC-PAWA-REQ-010,
the real security boundary; never an in-process check).

The ``.1R.30R.3.1`` A1 atomic unit: this module ships **together with**
``hpac_pawa_agent_exclusion.resolve_configured_agent_identity()`` — no
``production_writer`` factory is reachable without the resolver
(HPAC-PAWA-REQ-208, PAWA-INV-3/PAWA-INV-12).
"""

from __future__ import annotations

import hashlib
import inspect
import os
import stat
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    _PRODUCTION_WRITER_FACTORY_SEAL,
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACFoundationError,
    HPACStoreAuthority,
    HPACWriterCapability,
    canonical_digest,
    canonical_json_bytes,
    read_canonical_json_document,
    reject_symlink,
    resolve_hpac_protected_root,
    write_atomic_create_only,
    write_atomic_replace,
)
from pcae.core.hpac_pawa_agent_exclusion import (
    AgentExclusionError,
    ConfiguredAgentAuthorityIdentity,
    build_agent_exclusion_document,
    resolve_configured_agent_identity,
)
from pcae.core.hpac_pawa_schemas import (
    AUTHORITY_NAMESPACE,
    PawaSchemaError,
    build_authority_descriptor_document,
    build_current_generation_document,
    build_issuance_evidence_document,
    new_anchor_id,
    new_installation_id,
    new_operation_id,
    validate_authority_descriptor,
    validate_current_generation,
)

__all__ = [
    "PAWA_FAILURE_CODES",
    "RHAMP_TERMINAL_REASON_MAP",
    "PawaError",
    "PawaOperation",
    "ProductionWriterHandle",
    "production_writer",
    "enroll_principal_via_pawa",
    "revoke_principal_via_pawa",
    "revoke_credential_via_pawa",
    "provision_protected_root",
    "set_agent_exclusion",
    "rotate_descriptor",
    "revoke_anchor",
    "AUTHORIZED_FACTORY_CONSUMERS",
]


# ─────────────────────────────────────────────────────────────────────────
# §56 — the closed 21-value pawa_failure_code vocabulary (HPAC-PAWA-REQ-121)
# ─────────────────────────────────────────────────────────────────────────

PAWA_FAILURE_CODES = (
    "protected_root_missing",              # 1
    "protected_root_untrusted",            # 2
    "agent_principal_unknown",             # 3
    "agent_has_protected_write_authority",  # 4
    "descriptor_missing",                  # 5
    "descriptor_malformed",                # 6
    "descriptor_wrong_owner",              # 7
    "descriptor_wrong_mode",               # 8
    "descriptor_root_identity_mismatch",   # 9
    "descriptor_installation_mismatch",    # 10
    "descriptor_generation_stale",         # 11
    "descriptor_revoked",                  # 12
    "write_probe_failed",                  # 13
    "current_context_is_agent",            # 14
    "unauthorized_factory_consumer",       # 15
    "operation_scope_invalid",             # 16
    "target_scope_invalid",                # 17
    "capability_stale",                    # 18
    "duplicate_bootstrap",                 # 19
    "reconstruction_attempt",              # 20
    "internal_fail_closed",                # 21
)
assert len(PAWA_FAILURE_CODES) == 21 and len(set(PAWA_FAILURE_CODES)) == 21

#: §57 — deterministic map onto RHAMP-001 v1.0 §49's frozen 41-value
#: ``terminal_reason_code`` vocabulary (HPAC-PAWA-REQ-123/204). NO new
#: terminal_reason_code; RHAMP-001 is not edited by this phase.
RHAMP_TERMINAL_REASON_MAP = {
    "descriptor_missing": "bootstrap_authority_unproven",
    "descriptor_malformed": "bootstrap_authority_unproven",
    "descriptor_wrong_owner": "bootstrap_authority_unproven",
    "descriptor_wrong_mode": "bootstrap_authority_unproven",
    "descriptor_root_identity_mismatch": "bootstrap_authority_unproven",
    "descriptor_installation_mismatch": "bootstrap_authority_unproven",
    "descriptor_generation_stale": "bootstrap_authority_unproven",
    "descriptor_revoked": "bootstrap_authority_unproven",
    "agent_principal_unknown": "bootstrap_authority_unproven",
    "duplicate_bootstrap": "bootstrap_authority_unproven",
    "current_context_is_agent": "enrollment_not_protected_admin",
    "agent_has_protected_write_authority": "enrollment_not_protected_admin",
    "unauthorized_factory_consumer": "enrollment_not_protected_admin",
    "write_probe_failed": "enrollment_not_protected_admin",
    "protected_root_missing": "protected_root_invalid",
    "protected_root_untrusted": "protected_root_invalid",
    "operation_scope_invalid": "internal_verification_error",
    "target_scope_invalid": "internal_verification_error",
    "capability_stale": "internal_verification_error",
    "reconstruction_attempt": "internal_verification_error",
    "internal_fail_closed": "internal_verification_error",
}
assert set(RHAMP_TERMINAL_REASON_MAP) == set(PAWA_FAILURE_CODES)


class PawaError(Exception):
    """A terminal PAWA failure. ``code`` is exactly one member of
    :data:`PAWA_FAILURE_CODES` (§56 / §42A — never a free-form reason
    string, never a new vocabulary entry). ``rhamp_terminal_reason`` is
    the §57 mapping, for a caller inside a RHAMP ceremony."""

    def __init__(self, code: str, detail: str = "") -> None:
        if code not in PAWA_FAILURE_CODES:
            raise AssertionError(f"non-vocabulary pawa_failure_code: {code!r}")
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail

    @property
    def rhamp_terminal_reason(self) -> str:
        return RHAMP_TERMINAL_REASON_MAP[self.code]


class PawaOperation(str, Enum):
    """§42 — the closed set of mutation classes. Slice 1 mints and drives
    the three registry-record operations; ``enroll_credential`` and
    ``initialize_credential_sidecar_state`` are recognised as valid
    members of the closed set but are **Slice 2** (they require the RHAMP
    ceremony / sidecar — §58: do not fake a Slice-2 operation)."""

    ENROLL_PRINCIPAL = "enroll_principal"
    REVOKE_PRINCIPAL = "revoke_principal"
    ENROLL_CREDENTIAL = "enroll_credential"
    REVOKE_CREDENTIAL = "revoke_credential"
    INITIALIZE_CREDENTIAL_SIDECAR_STATE = "initialize_credential_sidecar_state"


_SLICE1_OPERATIONS = frozenset(
    {PawaOperation.ENROLL_PRINCIPAL, PawaOperation.REVOKE_PRINCIPAL, PawaOperation.REVOKE_CREDENTIAL}
)

#: §38 / §86 — the EXACT enumerated factory-consumer inventory. No
#: wildcard, no prefix, no fnmatch, no glob (PAWA-INV-9). At Slice 1 the
#: only production consumer is this module's own bounded principal-admin
#: operations (which the standalone script calls). Future Slice-2 modules
#: are NOT pre-authorised — each fails the guard until explicitly added
#: here AND the contract is amended to name its category.
AUTHORIZED_FACTORY_CONSUMERS = frozenset({"pcae.core.hpac_protected_admin_writer"})
#: A disclosed, explicit **test-only** consumer allowlist (§16 seam,
#: HPAC-PAWA-REQ-166). Exact names, never a prefix.
_TEST_FACTORY_CONSUMERS = frozenset(
    {"test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1"}
)

_ISSUER = "pcae.core.hpac_protected_admin_writer.production_writer/1.1"
_PROVENANCE_SCHEMA = "HPAC-WRITER-PROVENANCE/1.0"
_ANCHOR_WRITER_ROLE = "hpac_pawa_protected_admin"
_REGISTRY_WRITER_ROLE = "human_principal_registry_admin"

_DESCRIPTOR_NAME = "deployment-owner.json"
_CURRENT_GENERATION_NAME = "current-generation.json"
_AGENT_EXCLUSION_NAME = "agent-exclusion.json"
_MANIFEST_NAME = "manifest.json"
_ISSUANCE_EVIDENCE_DIR = "issuance-evidence"
_PROVENANCE_DIR = "provenance"


# ─────────────────────────────────────────────────────────────────────────
# Trusted clock
# ─────────────────────────────────────────────────────────────────────────


def _now() -> str:
    moment = datetime.now(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ─────────────────────────────────────────────────────────────────────────
# Authority resolution (production / disclosed test fixture)
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TopologyProbe:
    """Disclosed test-only seam (HPAC-PAWA-REQ-132/166). A deterministic
    ``(effective_write_access, ancestor_chain_safe)`` pair standing in for
    the platform ACL adapter, which is unavailable in sandboxed CI. Each
    callable has the exact signature of its
    ``hatp_class_b_topology_verifier`` counterpart. A guard test asserts no
    non-test module constructs or passes one."""

    effective_write_access: object
    ancestor_chain_safe: object


def _real_topology():
    from pcae.core.hatp_class_b_topology_verifier import (
        _ancestor_chain_safe,
        _effective_write_access,
    )

    return _effective_write_access, _ancestor_chain_safe


def _resolve_authority(
    protected_root: Optional[Path], topology_probe: Optional[TopologyProbe]
) -> HPACStoreAuthority:
    """§25 / §29 — production resolves the fixed compiled-in path with no
    caller override. ``protected_root`` / ``topology_probe`` are the
    disclosed test-only seams (§72/§73): a guard test asserts no non-test
    module passes either."""

    if protected_root is None:
        return HPACStoreAuthority.production()
    return HPACStoreAuthority._production_test_fixture(
        Path(protected_root), _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=topology_probe
    )


def _root_identity(root: Path) -> dict:
    st = root.stat()
    return {"device": st.st_dev, "inode": st.st_ino}


def _authority_dir(root: Path) -> Path:
    return root / AUTHORITY_NAMESPACE


def _reject_component_symlinks(path: Path) -> None:
    absolute = Path(path).resolve().parent
    # Reject a symlinked authority namespace / record entry without
    # following it (§12 / §21 / §66).
    for component in (path, *Path(path).parents):
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise PawaError("protected_root_untrusted", f"cannot inspect {component}: {exc!r}")
        if stat.S_ISLNK(mode):
            raise PawaError("protected_root_untrusted", f"symlinked protected component: {component}")


# ─────────────────────────────────────────────────────────────────────────
# Protected read helpers (identity-independent; do NOT invoke the F-1
# production boundary — that runs only after the configured agent identity
# is resolved, §33 step 3 / step 10)
# ─────────────────────────────────────────────────────────────────────────


def _read_protected_json(path: Path, *, missing_code: str, malformed_code: str) -> object:
    _reject_component_symlinks(path)
    if not path.exists():
        raise PawaError(missing_code, f"absent: {path}")
    if path.is_symlink():
        raise PawaError(malformed_code, f"symlink: {path}")
    try:
        st = path.stat()
    except OSError as exc:
        raise PawaError(malformed_code, f"cannot stat {path}: {exc!r}")
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise PawaError(malformed_code, f"not a single-link regular file: {path}")
    try:
        return read_canonical_json_document(path)
    except HPACFoundationError as exc:
        raise PawaError(malformed_code, f"non-canonical / malformed record {path}: {exc}")


def _require_owner_and_mode(
    path: Path,
    *,
    root_owner_uid: int,
    wrong_owner_code: str,
    wrong_mode_code: str,
) -> None:
    """§17 / §32 — the ``.authority/`` subtree and each record SHALL be
    owned by the deployment owner (== the protected-root owner uid) and
    SHALL NOT be group- or other-writable."""

    try:
        st = path.lstat()
    except OSError as exc:
        raise PawaError(wrong_mode_code, f"cannot lstat {path}: {exc!r}")
    if st.st_uid != root_owner_uid:
        raise PawaError(wrong_owner_code, f"{path} is not owned by the deployment owner (uid {root_owner_uid})")
    if stat.S_IMODE(st.st_mode) & (stat.S_IWGRP | stat.S_IWOTH):
        raise PawaError(wrong_mode_code, f"{path} is group- or other-writable")


def _require_not_configured_agent_writable(
    path: Path,
    identity: ConfiguredAgentAuthorityIdentity,
    effective_write_access,
    *,
    code: str,
) -> None:
    """§26 / §32 — the configured agent principal SHALL hold no write
    access (mode, group, or ACL) to ``path``."""

    writable, reason, _evidence = effective_write_access(path, identity.uid, identity.gids)
    if writable is not False:
        raise PawaError(code, f"configured agent can write {path}: {reason}")


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
    """§19 / §38 — resolve and verify the ``HPAC-WRITER-PROVENANCE/1.0``
    record for a protected anchor record. Provisioning writes it with the
    same closed schema ``hpac_foundation.record_write`` uses (filesystem
    primitives; no ``HPACWriterCapability`` — non-circular, §23(i))."""

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
        raise PawaError(malformed_code, f"provenance {provenance_path} has an invalid closed schema")
    if document["schema_version"] != _PROVENANCE_SCHEMA:
        raise PawaError(malformed_code, "provenance schema_version unsupported")
    if document["authority_class"] != "production":
        raise PawaError(malformed_code, "provenance authority_class is not 'production'")
    if document["root_identity_digest"] != live_root_identity_digest:
        raise PawaError(root_identity_code, "provenance root_identity_digest does not match the live root")
    if document["record_relative_path"] != record_relative_posix:
        raise PawaError(malformed_code, "provenance record_relative_path mismatch")
    if document["record_digest"] != record_digest:
        raise PawaError(malformed_code, "provenance record_digest mismatch")
    if document["writer_role"] != _ANCHOR_WRITER_ROLE:
        raise PawaError(malformed_code, "provenance writer_role is not the protected-admin role")
    if provenance_ref != f"{_PROVENANCE_DIR}/{key}.json":
        raise PawaError(malformed_code, "record provenance_ref does not name its provenance record")


# ─────────────────────────────────────────────────────────────────────────
# §33 — the positive validation sequence (11 steps, every step required)
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _RecognizedAnchor:
    authority: HPACStoreAuthority
    root: Path
    live_root_identity: dict
    live_root_identity_digest: str
    anchor_id: str
    installation_id: str
    generation: int
    configured_agent: ConfiguredAgentAuthorityIdentity


def _detect_caller_module(explicit: Optional[str]) -> str:
    if explicit is not None:
        return explicit
    stack = inspect.stack()
    # 0: _detect_caller_module, 1: production_writer, 2: the caller.
    for frame_info in stack[2:]:
        name = frame_info.frame.f_globals.get("__name__")
        if name and name != __name__ + ".<locals>" and name != "contextlib":
            return name or "<unknown>"
    return "<unknown>"


def _run_recognition_sequence(
    *,
    protected_root: Optional[Path],
    configured_agent_identity_source,
    caller_module: str,
    topology_probe: Optional["TopologyProbe"],
) -> _RecognizedAnchor:
    if topology_probe is not None:
        effective_write_access = topology_probe.effective_write_access
        ancestor_chain_safe = topology_probe.ancestor_chain_safe
    else:
        effective_write_access, ancestor_chain_safe = _real_topology()
    try:
        # STEP 1 — resolve the canonical protected root (no input).
        authority = _resolve_authority(protected_root, topology_probe)
        root = authority.root
        _reject_component_symlinks(root)
        if not root.exists():
            raise PawaError("protected_root_missing", f"{root} is absent")
        if root.is_symlink() or not root.is_dir():
            raise PawaError("protected_root_untrusted", f"{root} is a symlink or not a directory")
        try:
            root_owner_uid = root.stat().st_uid
        except OSError as exc:
            raise PawaError("protected_root_untrusted", f"cannot stat {root}: {exc!r}")
        if stat.S_IMODE(root.stat().st_mode) & (stat.S_IWGRP | stat.S_IWOTH):
            raise PawaError("protected_root_untrusted", "protected root is group- or other-writable")
        authority_dir = _authority_dir(root)
        _reject_component_symlinks(authority_dir)
        if not authority_dir.is_dir():
            raise PawaError("protected_root_missing", "the .authority/ namespace is absent")
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
            raise PawaError("protected_root_untrusted", "store-authority manifest has an invalid closed schema")
        manifest_root_identity = manifest["root_identity"]
        if manifest_root_identity != live_root_identity:
            raise PawaError("protected_root_untrusted", "HPAC root was copied or replaced; {device,inode} binding failed")
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
            raise PawaError("descriptor_malformed", str(exc))
        if descriptor.protected_root_identity != live_root_identity or descriptor.protected_root_identity != manifest_root_identity:
            raise PawaError("descriptor_root_identity_mismatch", "descriptor protected_root_identity != live root / manifest")
        if descriptor.state == "REVOKED":
            raise PawaError("descriptor_revoked", "descriptor state is REVOKED")
        if descriptor.state != "ACTIVE":
            raise PawaError("descriptor_malformed", f"descriptor state is {descriptor.state}, not ACTIVE")

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
            raise PawaError("descriptor_installation_mismatch", str(exc))
        if current_generation.installation_id != descriptor.installation_id:
            raise PawaError("descriptor_installation_mismatch", "descriptor installation_id != current-generation")
        if descriptor.generation > current_generation.current_generation:
            raise PawaError("descriptor_installation_mismatch", "descriptor generation is ahead of the anchor")
        if descriptor.generation < current_generation.current_generation:
            raise PawaError("descriptor_generation_stale", "a superseded descriptor cannot mint (rollback)")
        if descriptor.descriptor_digest != current_generation.descriptor_digest:
            raise PawaError("descriptor_installation_mismatch", "descriptor digest != anchored descriptor_digest")
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
            raise PawaError("agent_principal_unknown", str(exc))
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
            raise PawaError("agent_has_protected_write_authority", f"configured agent can write the root: {reason}")
        if writable is None or ancestors_safe is None:
            raise PawaError("protected_root_untrusted", f"indeterminate permissions: {reason} / {diagnostics}")
        if ancestors_safe is not True:
            raise PawaError("agent_has_protected_write_authority", f"configured-agent-writable ancestor: {diagnostics}")
        _require_not_configured_agent_writable(
            authority_dir, configured_agent, effective_write_access, code="agent_has_protected_write_authority"
        )
        _require_not_configured_agent_writable(
            descriptor_path, configured_agent, effective_write_access, code="agent_has_protected_write_authority"
        )
        _require_not_configured_agent_writable(
            exclusion_path, configured_agent, effective_write_access, code="agent_has_protected_write_authority"
        )

        # STEP 7 — the current administrative context is NOT the configured
        # agent principal (compare live uid against the resolved
        # configured-agent uid; never an agent_id label, never groups
        # alone — HPAC-PAWA-REQ-201).
        live_uid, _live_gids = _current_agent_identity()
        if live_uid == configured_agent.uid:
            raise PawaError("current_context_is_agent", "the current invocation is running as the configured agent account")

        # STEP 8 — the positive O_EXCL|O_NOFOLLOW write probe (current
        # invoking process; §28/§29).
        _positive_write_probe(authority_dir)

        # STEP 9 — the calling module is an authorized factory consumer.
        if caller_module not in AUTHORIZED_FACTORY_CONSUMERS and caller_module not in _TEST_FACTORY_CONSUMERS:
            raise PawaError("unauthorized_factory_consumer", f"{caller_module!r} is not an enumerated consumer (§38)")

        return _RecognizedAnchor(
            authority=authority,
            root=root,
            live_root_identity=live_root_identity,
            live_root_identity_digest=live_root_identity_digest,
            anchor_id=descriptor.anchor_id,
            installation_id=descriptor.installation_id,
            generation=descriptor.generation,
            configured_agent=configured_agent,
        )
    except PawaError:
        raise
    except Exception as exc:  # noqa: BLE001 — deliberate fail-closed boundary (§0)
        raise PawaError("internal_fail_closed", f"{type(exc).__name__}: {exc}") from exc


def _exclusion_provenance_ref(document: object) -> str:
    if isinstance(document, dict) and isinstance(document.get("provenance_ref"), str):
        return document["provenance_ref"]
    return ""


def _positive_write_probe(authority_dir: Path) -> None:
    """§28 / §29 / §30 — operation-based proof that the current
    administrative invocation holds real OS-authorized write over
    ``.authority/`` now. Dedicated random sentinel, O_CREAT|O_EXCL|
    O_NOFOLLOW, write + fsync + close + unlink. Cleanup failure is
    ``write_probe_failed`` — never left behind silently."""

    sentinel = authority_dir / f".probe-{os.urandom(16).hex()}"
    reject_symlink(sentinel)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(sentinel, flags, 0o600)
    except OSError as exc:
        raise PawaError("write_probe_failed", f"probe create failed: {exc!r}")
    try:
        os.write(fd, b"hpac-pawa-probe\n")
        os.fsync(fd)
    except OSError as exc:
        raise PawaError("write_probe_failed", f"probe write failed: {exc!r}")
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    try:
        os.unlink(sentinel)
    except OSError as exc:
        raise PawaError("write_probe_failed", f"probe sentinel could not be unlinked: {exc!r}")


# ─────────────────────────────────────────────────────────────────────────
# One-operation capability handle (§49 / §107)
# ─────────────────────────────────────────────────────────────────────────


class ProductionWriterHandle:
    """A single-use, operation-scoped handle around one ``PRODUCTION``
    ``HPACWriterCapability``. The wrapped capability is additionally
    ``_single_use`` at the foundation layer (spent on first
    ``record_write``); this handle refuses a second ``.consume()`` at the
    factory layer with ``capability_stale`` and refuses a mismatched
    operation / principal / credential with ``target_scope_invalid``."""

    __slots__ = (
        "_capability",
        "_authority",
        "operation",
        "principal_id",
        "credential_id",
        "operation_id",
        "anchor_id",
        "installation_id",
        "descriptor_generation",
        "_consumed",
    )

    def __init__(
        self,
        *,
        capability: HPACWriterCapability,
        authority: HPACStoreAuthority,
        operation: PawaOperation,
        principal_id: Optional[str],
        credential_id: Optional[str],
        operation_id: str,
        anchor_id: str,
        installation_id: str,
        descriptor_generation: int,
    ) -> None:
        self._capability = capability
        self._authority = authority
        self.operation = operation
        self.principal_id = principal_id
        self.credential_id = credential_id
        self.operation_id = operation_id
        self.anchor_id = anchor_id
        self.installation_id = installation_id
        self.descriptor_generation = descriptor_generation
        self._consumed = False

    def __reduce__(self):
        raise TypeError("ProductionWriterHandle is process-local and non-serializable")

    @property
    def authority(self) -> HPACStoreAuthority:
        return self._authority

    def consume(
        self,
        operation: PawaOperation,
        *,
        principal_id: Optional[str] = None,
        credential_id: Optional[str] = None,
    ) -> HPACWriterCapability:
        if self._consumed or self._capability._spent:
            raise PawaError("capability_stale", "this PRODUCTION writer has already been used")
        if operation != self.operation:
            raise PawaError("target_scope_invalid", f"handle bound to {self.operation.value}, used for {operation}")
        if principal_id != self.principal_id:
            raise PawaError("target_scope_invalid", "handle bound to a different principal_id")
        if credential_id != self.credential_id:
            raise PawaError("target_scope_invalid", "handle bound to a different credential_id")
        self._consumed = True
        return self._capability


# ─────────────────────────────────────────────────────────────────────────
# §33 step 10 — the production_writer factory (§36)
# ─────────────────────────────────────────────────────────────────────────


def _validate_operation_inputs(
    operation,
    principal_id: Optional[str],
    credential_id: Optional[str],
) -> PawaOperation:
    if isinstance(operation, PawaOperation):
        op = operation
    elif isinstance(operation, str):
        try:
            op = PawaOperation(operation)
        except ValueError:
            raise PawaError("operation_scope_invalid", f"{operation!r} is not a §42 mutation class")
    else:
        raise PawaError("operation_scope_invalid", f"operation must be a str / PawaOperation, got {type(operation)}")
    if op not in _SLICE1_OPERATIONS:
        raise PawaError("operation_scope_invalid", f"{op.value} is a Slice-2 operation, not available in Slice 1")
    if principal_id is not None and (not isinstance(principal_id, str) or not principal_id.strip()):
        raise PawaError("operation_scope_invalid", "principal_id must be a non-empty string or None")
    if credential_id is not None and (not isinstance(credential_id, str) or not credential_id.strip()):
        raise PawaError("operation_scope_invalid", "credential_id must be a non-empty string or None")
    if op is PawaOperation.ENROLL_PRINCIPAL and (principal_id is None or credential_id is not None):
        raise PawaError("operation_scope_invalid", "enroll_principal requires principal_id and no credential_id")
    if op is PawaOperation.REVOKE_PRINCIPAL and (principal_id is None or credential_id is not None):
        raise PawaError("operation_scope_invalid", "revoke_principal requires principal_id and no credential_id")
    if op is PawaOperation.REVOKE_CREDENTIAL and (credential_id is None):
        raise PawaError("operation_scope_invalid", "revoke_credential requires credential_id")
    return op


def production_writer(
    operation,
    *,
    principal_id: Optional[str] = None,
    credential_id: Optional[str] = None,
    _protected_root: Optional[Path] = None,
    _configured_agent_identity_source=None,
    _topology_probe: Optional["TopologyProbe"] = None,
    _caller_module: Optional[str] = None,
) -> ProductionWriterHandle:
    """§36 — mint exactly one process-local, operation-scoped ``PRODUCTION``
    ``HPACWriterCapability`` after a fresh, complete §33 recognition
    sequence (every step required; PAWA-INV-3). Runs fresh on every call
    — no result is cached (HPAC-PAWA-REQ-075).

    ``_protected_root`` and ``_configured_agent_identity_source`` are the
    disclosed test-only seams (§72/§73 / HPAC-PAWA-REQ-166); a guard test
    asserts no non-test module passes either.

    Raises :class:`PawaError` (code ∈ :data:`PAWA_FAILURE_CODES`) on any
    failure; records a durable failure-context evidence entry where a
    lifecycle path exists.
    """

    caller_module = _detect_caller_module(_caller_module)
    op = _validate_operation_inputs(operation, principal_id, credential_id)
    recognized = _run_recognition_sequence(
        protected_root=_protected_root,
        configured_agent_identity_source=_configured_agent_identity_source,
        caller_module=caller_module,
        topology_probe=_topology_probe,
    )

    # STEP 10 — bind the configured-agent identity into the authority so
    # every subsequent _validate_production_boundary / record_write re-run
    # keys the negative boundary off the configured agent (F-1), then mint.
    recognized.authority._bind_configured_agent_identity(
        (recognized.configured_agent.uid, recognized.configured_agent.gids),
        _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL,
    )
    subject = principal_id if principal_id is not None else credential_id
    try:
        capability = recognized.authority._mint_production_writer_capability(
            _REGISTRY_WRITER_ROLE, subject, _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL
        )
    except HPACAuthorityError as exc:
        raise PawaError("internal_fail_closed", f"mint refused: {exc}")

    operation_id = new_operation_id()
    handle = ProductionWriterHandle(
        capability=capability,
        authority=recognized.authority,
        operation=op,
        principal_id=principal_id,
        credential_id=credential_id,
        operation_id=operation_id,
        anchor_id=recognized.anchor_id,
        installation_id=recognized.installation_id,
        descriptor_generation=recognized.generation,
    )

    # STEP 11 — the issuance audit evidence (§55; audit is never
    # capability, PAWA-INV-10).
    _record_issuance_evidence(
        recognized.root,
        operation_id=operation_id,
        operation=op.value,
        anchor_id=recognized.anchor_id,
        installation_id=recognized.installation_id,
        descriptor_generation=recognized.generation,
        protected_root_identity=recognized.live_root_identity,
        target_principal_id=principal_id,
        target_credential_id=credential_id,
        result="issued",
        capability_identifier="hpaw-cap-" + hashlib.sha256(operation_id.encode()).hexdigest()[:32],
    )
    return handle


def _record_issuance_evidence(
    root: Path,
    *,
    operation_id: str,
    operation: str,
    anchor_id: str,
    installation_id: str,
    descriptor_generation: int,
    protected_root_identity: dict,
    target_principal_id: Optional[str],
    target_credential_id: Optional[str],
    result: str,
    capability_identifier: Optional[str],
) -> None:
    document = build_issuance_evidence_document(
        operation_id=operation_id,
        operation=operation,
        anchor_id=anchor_id,
        installation_id=installation_id,
        descriptor_generation=descriptor_generation,
        protected_root_identity=protected_root_identity,
        target_principal_id=target_principal_id,
        target_credential_id=target_credential_id,
        enrollment_transaction_id=None,
        issued_at=_now(),
        issuer=_ISSUER,
        result=result,
        capability_identifier=capability_identifier,
        context_annotation=None,
    )
    path = _authority_dir(root) / _ISSUANCE_EVIDENCE_DIR / f"{operation_id}.json"
    _ensure_authority_subdir(path.parent)
    try:
        write_atomic_create_only(path, canonical_json_bytes(document))
    except HPACFoundationError:
        # Best-effort audit; a duplicate operation_id is astronomically
        # unlikely and never a security-relevant failure.
        pass


def _ensure_authority_subdir(path: Path) -> None:
    reject_symlink(path)
    if not path.exists():
        path.mkdir(mode=0o700)
    reject_symlink(path)


# ─────────────────────────────────────────────────────────────────────────
# Bounded protected principal-administration operations (§38 category 1 —
# the only Slice-1 production consumers of production_writer)
# ─────────────────────────────────────────────────────────────────────────


def enroll_principal_via_pawa(
    *,
    principal_id: str,
    enrollment_provenance_ref: str,
    _protected_root: Optional[Path] = None,
    _configured_agent_identity_source=None,
    _topology_probe=None,
) -> "object":
    from pcae.core.human_principal_registry import HumanPrincipalRegistryStore

    handle = production_writer(
        PawaOperation.ENROLL_PRINCIPAL,
        principal_id=principal_id,
        _protected_root=_protected_root,
        _configured_agent_identity_source=_configured_agent_identity_source,
        _topology_probe=_topology_probe,
    )
    capability = handle.consume(PawaOperation.ENROLL_PRINCIPAL, principal_id=principal_id)
    store = HumanPrincipalRegistryStore(handle.authority)
    return store.enroll_principal(
        capability,
        principal_id=principal_id,
        enrollment_provenance_ref=enrollment_provenance_ref,
        enrolled_at=_now(),
    )


def revoke_principal_via_pawa(
    *,
    principal_id: str,
    _protected_root: Optional[Path] = None,
    _configured_agent_identity_source=None,
    _topology_probe=None,
) -> "object":
    from pcae.core.human_principal_registry import HumanPrincipalRegistryStore

    handle = production_writer(
        PawaOperation.REVOKE_PRINCIPAL,
        principal_id=principal_id,
        _protected_root=_protected_root,
        _configured_agent_identity_source=_configured_agent_identity_source,
        _topology_probe=_topology_probe,
    )
    capability = handle.consume(PawaOperation.REVOKE_PRINCIPAL, principal_id=principal_id)
    store = HumanPrincipalRegistryStore(handle.authority)
    return store.revoke_principal(capability, principal_id=principal_id, revoked_at=_now())


def revoke_credential_via_pawa(
    *,
    credential_id: str,
    _protected_root: Optional[Path] = None,
    _configured_agent_identity_source=None,
    _topology_probe=None,
) -> "object":
    from pcae.core.human_principal_registry import HumanPrincipalRegistryStore

    handle = production_writer(
        PawaOperation.REVOKE_CREDENTIAL,
        credential_id=credential_id,
        _protected_root=_protected_root,
        _configured_agent_identity_source=_configured_agent_identity_source,
        _topology_probe=_topology_probe,
    )
    capability = handle.consume(PawaOperation.REVOKE_CREDENTIAL, credential_id=credential_id)
    store = HumanPrincipalRegistryStore(handle.authority)
    return store.revoke_credential(capability, credential_id=credential_id, revoked_at=_now())


# ─────────────────────────────────────────────────────────────────────────
# Out-of-band provisioning / rotation / revocation (§23 / §32B / §50 / §51)
# — filesystem primitives only; NO HPACWriterCapability, NO FIDO2,
#   NO enrolled principal (PAWA-INV-4, non-circular).
# ─────────────────────────────────────────────────────────────────────────


class ProvisioningError(Exception):
    """An out-of-band provisioning / rotation / revocation fault. Distinct
    from :class:`PawaError` — provisioning is a filesystem administrative
    act, not a recognition. Maps to ``duplicate_bootstrap`` / a descriptor
    code where the §56 taxonomy applies (§32B.3)."""


def _write_anchor_provenance(
    root: Path,
    *,
    record_relative_posix: str,
    record_digest: str,
    store_id: str,
) -> str:
    key = hashlib.sha256(record_relative_posix.encode("utf-8")).hexdigest()
    provenance_dir = _authority_dir(root) / _PROVENANCE_DIR
    _ensure_authority_subdir(provenance_dir)
    document = {
        "schema_version": _PROVENANCE_SCHEMA,
        "store_id": store_id,
        "authority_class": "production",
        "root_identity_digest": canonical_digest(_root_identity(root)),
        "record_relative_path": record_relative_posix,
        "record_digest": record_digest,
        "writer_role": _ANCHOR_WRITER_ROLE,
        "writer_subject": None,
    }
    path = provenance_dir / f"{key}.json"
    write_atomic_replace(path, canonical_json_bytes(document))
    os.chmod(path, 0o600)
    return f"{_PROVENANCE_DIR}/{key}.json"


def _load_store_id(root: Path) -> str:
    manifest = read_canonical_json_document(_authority_dir(root) / _MANIFEST_NAME)
    return manifest["store_id"]  # type: ignore[index]


def _existing_active_anchor(root: Path) -> bool:
    descriptor_path = _authority_dir(root) / _DESCRIPTOR_NAME
    cg_path = _authority_dir(root) / _CURRENT_GENERATION_NAME
    if not descriptor_path.exists() or not cg_path.exists():
        return False
    try:
        descriptor = validate_authority_descriptor(read_canonical_json_document(descriptor_path))
        validate_current_generation(read_canonical_json_document(cg_path))
    except (PawaSchemaError, HPACFoundationError):
        return False
    return descriptor.state == "ACTIVE"


def provision_protected_root(
    *,
    protected_root: Path,
    agent_account: str,
    agent_uid: int,
) -> dict:
    """§23 / §32B.1 — the one-time out-of-band bootstrap. Creates
    ``<protected_root>`` 0700, the ``HPAC-STORE-AUTHORITY/1.0`` manifest,
    ``deployment-owner.json``@generation 1, ``current-generation.json``@1
    (with ``agent_exclusion_digest``, §20A), ``agent-exclusion.json``
    (create-only), and their provenance records. Requires OS write
    authority on ``protected_root`` and its parent (the real boundary).

    Not silently repeatable over a live valid installation (§24 / §32B.3):
    a second call raises ``ProvisioningError`` (→ ``duplicate_bootstrap``).
    """

    protected_root = Path(protected_root)
    if _existing_active_anchor(protected_root):
        raise ProvisioningError(
            "duplicate_bootstrap: an ACTIVE HPAC-PAWA anchor already exists; "
            "use rotate_descriptor / set_agent_exclusion, never a silent authority reset"
        )
    authority_dir = _authority_dir(protected_root)
    reject_symlink(protected_root)
    protected_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(protected_root, 0o700)
    reject_symlink(authority_dir)
    authority_dir.mkdir(mode=0o700, exist_ok=True)
    os.chmod(authority_dir, 0o700)

    manifest_path = authority_dir / _MANIFEST_NAME
    if not manifest_path.exists():
        import uuid as _uuid

        manifest = {
            "schema_version": "HPAC-STORE-AUTHORITY/1.0",
            "store_id": f"hpacs-{_uuid.uuid4().hex}",
            "authority_class": "production",
            "root_identity": _root_identity(protected_root),
        }
        write_atomic_create_only(manifest_path, canonical_json_bytes(manifest))
        os.chmod(manifest_path, 0o600)
    store_id = _load_store_id(protected_root)

    anchor_id = new_anchor_id()
    installation_id = new_installation_id()
    root_identity = _root_identity(protected_root)
    now = _now()

    descriptor = build_authority_descriptor_document(
        anchor_id=anchor_id,
        installation_id=installation_id,
        protected_root_identity=root_identity,
        generation=1,
        created_at=now,
        provenance_ref="pending",
        supersedes=None,
    )
    descriptor_rel = f"{AUTHORITY_NAMESPACE}/{_DESCRIPTOR_NAME}"
    descriptor_provenance_ref = _write_anchor_provenance(
        protected_root,
        record_relative_posix=descriptor_rel,
        record_digest=descriptor["descriptor_digest"],
        store_id=store_id,
    )
    descriptor = build_authority_descriptor_document(
        anchor_id=anchor_id,
        installation_id=installation_id,
        protected_root_identity=root_identity,
        generation=1,
        created_at=now,
        provenance_ref=descriptor_provenance_ref,
        supersedes=None,
    )
    # provenance record digest must track the final descriptor bytes.
    descriptor_provenance_ref = _write_anchor_provenance(
        protected_root,
        record_relative_posix=descriptor_rel,
        record_digest=descriptor["descriptor_digest"],
        store_id=store_id,
    )
    _atomic_create_record(authority_dir / _DESCRIPTOR_NAME, descriptor)

    exclusion = _build_and_write_exclusion(
        protected_root,
        symbolic_account=agent_account,
        provisioned_uid=agent_uid,
        installation_id=installation_id,
        root_identity=root_identity,
        generation=1,
        created_at=now,
        supersedes=None,
        store_id=store_id,
        replace=False,
    )

    cg = build_current_generation_document(
        installation_id=installation_id,
        current_generation=1,
        descriptor_digest=descriptor["descriptor_digest"],
        agent_exclusion_digest=exclusion["record_digest"],
        updated_at=now,
    )
    _atomic_create_record(authority_dir / _CURRENT_GENERATION_NAME, cg)

    return {
        "anchor_id": anchor_id,
        "installation_id": installation_id,
        "generation": 1,
        "symbolic_account": agent_account,
        "provisioned_uid": agent_uid,
        "descriptor_digest": descriptor["descriptor_digest"],
        "agent_exclusion_digest": exclusion["record_digest"],
    }


def _atomic_create_record(path: Path, document: dict) -> None:
    reject_symlink(path)
    if path.exists():
        raise ProvisioningError(f"duplicate_bootstrap: {path} already exists")
    write_atomic_create_only(path, canonical_json_bytes(document))
    os.chmod(path, 0o600)


def _atomic_replace_record(path: Path, document: dict) -> None:
    reject_symlink(path)
    write_atomic_replace(path, canonical_json_bytes(document))
    os.chmod(path, 0o600)


def _build_and_write_exclusion(
    protected_root: Path,
    *,
    symbolic_account: str,
    provisioned_uid: int,
    installation_id: str,
    root_identity: dict,
    generation: int,
    created_at: str,
    supersedes: Optional[dict],
    store_id: str,
    replace: bool,
) -> dict:
    exclusion = build_agent_exclusion_document(
        symbolic_account=symbolic_account,
        provisioned_uid=provisioned_uid,
        installation_id=installation_id,
        protected_root_identity=root_identity,
        generation=generation,
        created_at=created_at,
        provenance_ref="pending",
        supersedes=supersedes,
    )
    exclusion_rel = f"{AUTHORITY_NAMESPACE}/{_AGENT_EXCLUSION_NAME}"
    _write_anchor_provenance(
        protected_root,
        record_relative_posix=exclusion_rel,
        record_digest=exclusion["record_digest"],
        store_id=store_id,
    )
    provenance_ref = _write_anchor_provenance(
        protected_root,
        record_relative_posix=exclusion_rel,
        record_digest=exclusion["record_digest"],
        store_id=store_id,
    )
    exclusion = build_agent_exclusion_document(
        symbolic_account=symbolic_account,
        provisioned_uid=provisioned_uid,
        installation_id=installation_id,
        protected_root_identity=root_identity,
        generation=generation,
        created_at=created_at,
        provenance_ref=provenance_ref,
        supersedes=supersedes,
    )
    _write_anchor_provenance(
        protected_root,
        record_relative_posix=exclusion_rel,
        record_digest=exclusion["record_digest"],
        store_id=store_id,
    )
    path = _authority_dir(protected_root) / _AGENT_EXCLUSION_NAME
    if replace:
        _atomic_replace_record(path, exclusion)
    else:
        _atomic_create_record(path, exclusion)
    return exclusion


def _load_anchor_state(protected_root: Path):
    authority_dir = _authority_dir(protected_root)
    descriptor = validate_authority_descriptor(read_canonical_json_document(authority_dir / _DESCRIPTOR_NAME))
    cg = validate_current_generation(read_canonical_json_document(authority_dir / _CURRENT_GENERATION_NAME))
    return descriptor, cg


def set_agent_exclusion(
    *,
    protected_root: Path,
    agent_account: str,
    agent_uid: int,
) -> dict:
    """§32B.4 — an explicit deployment-owner rotation of the
    configured-agent OS account. Writes a new exclusion record at
    ``generation = old + 1`` with ``supersedes``, re-stamps
    ``current-generation.json``'s ``agent_exclusion_digest`` and
    ``current_generation`` by atomic replace, and (per §32B.4) advances
    the descriptor generation too so the single monotonic anchor stays
    authoritative. The old record no longer satisfies §33."""

    protected_root = Path(protected_root)
    descriptor, cg = _load_anchor_state(protected_root)
    if descriptor.state != "ACTIVE":
        raise ProvisioningError("descriptor is not ACTIVE; provision or rotate first")
    old_exclusion = read_canonical_json_document(_authority_dir(protected_root) / _AGENT_EXCLUSION_NAME)
    store_id = _load_store_id(protected_root)
    now = _now()
    new_generation = cg.current_generation + 1
    root_identity = _root_identity(protected_root)

    new_descriptor = build_authority_descriptor_document(
        anchor_id=descriptor.anchor_id,
        installation_id=descriptor.installation_id,
        protected_root_identity=root_identity,
        generation=new_generation,
        created_at=now,
        provenance_ref="pending",
        supersedes={"previous_generation": descriptor.generation, "previous_descriptor_digest": descriptor.descriptor_digest},
    )
    descriptor_rel = f"{AUTHORITY_NAMESPACE}/{_DESCRIPTOR_NAME}"
    ref = _write_anchor_provenance(
        protected_root, record_relative_posix=descriptor_rel,
        record_digest=new_descriptor["descriptor_digest"], store_id=store_id,
    )
    new_descriptor = build_authority_descriptor_document(
        anchor_id=descriptor.anchor_id,
        installation_id=descriptor.installation_id,
        protected_root_identity=root_identity,
        generation=new_generation,
        created_at=now,
        provenance_ref=ref,
        supersedes={"previous_generation": descriptor.generation, "previous_descriptor_digest": descriptor.descriptor_digest},
    )
    _write_anchor_provenance(
        protected_root, record_relative_posix=descriptor_rel,
        record_digest=new_descriptor["descriptor_digest"], store_id=store_id,
    )

    new_exclusion = _build_and_write_exclusion(
        protected_root,
        symbolic_account=agent_account,
        provisioned_uid=agent_uid,
        installation_id=descriptor.installation_id,
        root_identity=root_identity,
        generation=new_generation,
        created_at=now,
        supersedes={
            "previous_generation": old_exclusion["generation"],
            "previous_record_digest": old_exclusion["record_digest"],
        },
        store_id=store_id,
        replace=True,
    )

    _atomic_replace_record(_authority_dir(protected_root) / _DESCRIPTOR_NAME, new_descriptor)
    cg_doc = build_current_generation_document(
        installation_id=descriptor.installation_id,
        current_generation=new_generation,
        descriptor_digest=new_descriptor["descriptor_digest"],
        agent_exclusion_digest=new_exclusion["record_digest"],
        updated_at=now,
    )
    _atomic_replace_record(_authority_dir(protected_root) / _CURRENT_GENERATION_NAME, cg_doc)
    return {
        "generation": new_generation,
        "symbolic_account": agent_account,
        "provisioned_uid": agent_uid,
        "agent_exclusion_digest": new_exclusion["record_digest"],
    }


def rotate_descriptor(*, protected_root: Path) -> dict:
    """§50 — an explicit deployment-owner descriptor rotation (carries the
    agent-exclusion binding forward unchanged, re-stamps the anchor)."""

    protected_root = Path(protected_root)
    descriptor, cg = _load_anchor_state(protected_root)
    if descriptor.state != "ACTIVE":
        raise ProvisioningError("only an ACTIVE descriptor can be rotated")
    exclusion = read_canonical_json_document(_authority_dir(protected_root) / _AGENT_EXCLUSION_NAME)
    return set_agent_exclusion(
        protected_root=protected_root,
        agent_account=exclusion["symbolic_account"],
        agent_uid=exclusion["provisioned_uid"],
    )


def revoke_anchor(*, protected_root: Path) -> dict:
    """§51 — the deployment owner explicitly revokes the anchor. The
    descriptor state becomes REVOKED; recognition fails closed
    (``descriptor_revoked``) until a fresh provision / rotation."""

    protected_root = Path(protected_root)
    authority_dir = _authority_dir(protected_root)
    descriptor, cg = _load_anchor_state(protected_root)
    store_id = _load_store_id(protected_root)
    now = _now()
    revoked = build_authority_descriptor_document(
        anchor_id=descriptor.anchor_id,
        installation_id=descriptor.installation_id,
        protected_root_identity=_root_identity(protected_root),
        generation=descriptor.generation,
        created_at=now,
        provenance_ref="pending",
        supersedes=descriptor.supersedes,
        state="REVOKED",
    )
    descriptor_rel = f"{AUTHORITY_NAMESPACE}/{_DESCRIPTOR_NAME}"
    ref = _write_anchor_provenance(
        protected_root, record_relative_posix=descriptor_rel,
        record_digest=revoked["descriptor_digest"], store_id=store_id,
    )
    revoked = build_authority_descriptor_document(
        anchor_id=descriptor.anchor_id,
        installation_id=descriptor.installation_id,
        protected_root_identity=_root_identity(protected_root),
        generation=descriptor.generation,
        created_at=now,
        provenance_ref=ref,
        supersedes=descriptor.supersedes,
        state="REVOKED",
    )
    _write_anchor_provenance(
        protected_root, record_relative_posix=descriptor_rel,
        record_digest=revoked["descriptor_digest"], store_id=store_id,
    )
    _atomic_replace_record(authority_dir / _DESCRIPTOR_NAME, revoked)
    cg_doc = build_current_generation_document(
        installation_id=descriptor.installation_id,
        current_generation=cg.current_generation,
        descriptor_digest=revoked["descriptor_digest"],
        agent_exclusion_digest=cg.agent_exclusion_digest,
        updated_at=now,
    )
    _atomic_replace_record(authority_dir / _CURRENT_GENERATION_NAME, cg_doc)
    return {"state": "REVOKED", "generation": descriptor.generation}
