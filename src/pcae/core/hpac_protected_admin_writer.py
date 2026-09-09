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
import re
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
    "PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS",
    "mint_protected_presentation_evidence_writer",
    # HPAC-PAWA-001 v1.3 §33A / §38A / §42B — the dedicated certification
    # writer factory (distinct from the §36 production_writer factory).
    "CERTIFICATION_FACTORY_CONSUMERS",
    "CERTIFICATION_ROLE_ALLOWLIST",
    "CERTIFICATION_LIFECYCLE_ROLES",
    "CERTIFICATION_COUNTER_ROLE",
    "CertificationWriterHandle",
    "certification_writer",
    # HPAC-PAWA-001 v1.4 §33B / §38B / §42D / §49B / §68B — the dedicated
    # read / ceremony-entry authority accessor (F-5-B1 repair).
    "READ_AUTHORITY_CONSUMERS",
    "CertificationReadAuthority",
    "recognized_certification_read_authority",
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
    """§42 — the closed set of mutation classes (HPAC-PAWA-REQ-095).

    Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156
    ``.1R.30`` bundle — Decision A / RE-MERGE) enables the two remaining
    members: ``enroll_credential`` (a ``CredentialRecord`` + its RHAMP-001
    sidecar + counter-state — one bounded enrollment transaction,
    HPAC-PAWA-REQ-100/106) and ``initialize_credential_sidecar_state``. The
    former "Slice 2" boundary is dissolved by the adjudication
    (``.1R.30R.3.3R``); the sidecar / counter-state schemas live in
    ``hpac_rhamp_credential_sidecar`` / ``hpac_rhamp_counter_state``, the
    ceremony in ``hpac_rhamp_enrollment`` — never here."""

    ENROLL_PRINCIPAL = "enroll_principal"
    REVOKE_PRINCIPAL = "revoke_principal"
    ENROLL_CREDENTIAL = "enroll_credential"
    REVOKE_CREDENTIAL = "revoke_credential"
    INITIALIZE_CREDENTIAL_SIDECAR_STATE = "initialize_credential_sidecar_state"
    #: Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1 — HPAC-PAWA-001 v1.2
    #: (HPAC-PAWA-REQ-095) adds exactly one metadata-only mutation family:
    #: one bounded install / rotate / revoke configuration transaction for
    #: the exact presentation ``mechanism_id`` under HPAC-PPA-001 v1.0, using
    #: writer role ``presentation_mechanism_installer``. It writes only that
    #: contract's installation-generation record, current-generation anchor,
    #: HPAC-REQ-090 descriptor, and their writer-provenance sidecars. It
    #: SHALL NOT create, copy, replace, chmod, chown, or execute helper
    #: bytes. The schema/store/currentness live in
    #: ``protected_presentation_installation``, the ceremony in
    #: ``hpac_protected_presentation_admin`` — never here.
    CONFIGURE_PRESENTATION_MECHANISM = "configure_presentation_mechanism"


#: Registry-record operations that mint a plain single-use capability.
_SLICE1_OPERATIONS = frozenset(
    {PawaOperation.ENROLL_PRINCIPAL, PawaOperation.REVOKE_PRINCIPAL, PawaOperation.REVOKE_CREDENTIAL}
)
#: Phase .1R.30R.3.4 — the multi-artifact enrollment-transaction operations
#: (HPAC-PAWA-REQ-106: the ``enroll_credential`` + sidecar + counter-state
#: writes are one atomic ceremony authorised by one ``_multi_write``
#: capability, spent once via ``authority.complete_multi_write``).
_ENROLLMENT_TRANSACTION_OPERATIONS = frozenset(
    {PawaOperation.ENROLL_CREDENTIAL, PawaOperation.INITIALIZE_CREDENTIAL_SIDECAR_STATE}
)
#: Phase .1R.30R.4R.1 — the v1.2 ``configure_presentation_mechanism`` family.
#: Its descriptor + installation record + anchor + provenance writes are one
#: bounded multi-write transaction authorised by one ``_multi_write``
#: capability, spent once via ``authority.complete_multi_write``
#: (HPAC-PAWA-REQ-095/106; HPAC-PPA-REQ-023).
_PRESENTATION_CONFIG_OPERATIONS = frozenset({PawaOperation.CONFIGURE_PRESENTATION_MECHANISM})
_MULTI_WRITE_OPERATIONS = _ENROLLMENT_TRANSACTION_OPERATIONS | _PRESENTATION_CONFIG_OPERATIONS
#: HPAC-PPA-REQ-005 — the exact installer writer role for the v1.2 family
#: (already frozen by ``approval_presentation.PresentationMechanismDescriptorStore``).
_PRESENTATION_INSTALLER_ROLE = "presentation_mechanism_installer"
_PRESENTATION_LIFECYCLE_ACTIONS = frozenset({"install", "rotate", "revoke"})
_AVAILABLE_OPERATIONS = _SLICE1_OPERATIONS | _ENROLLMENT_TRANSACTION_OPERATIONS | _PRESENTATION_CONFIG_OPERATIONS

#: §38 / §86 — the EXACT enumerated factory-consumer inventory. No
#: wildcard, no prefix, no fnmatch, no glob (PAWA-INV-9). At Slice 1 the
#: only production consumer is this module's own bounded principal-admin
#: operations (which the standalone script calls). Future Slice-2 modules
#: are NOT pre-authorised — each fails the guard until explicitly added
#: here AND the contract is amended to name its category.
AUTHORIZED_FACTORY_CONSUMERS = frozenset(
    {
        "pcae.core.hpac_protected_admin_writer",
        # Phase .1R.30R.3.4 — the RHAMP-001 first-credential bootstrap /
        # enrollment ceremony tool (HPAC-PAWA-REQ-087 category 2;
        # RHAMP-REQ-048). Exact dotted-path, no wildcard (PAWA-INV-9). It is
        # itself inside the non-agent-importable fence (a guard test asserts
        # cli.py / commands/** / core/agent.py never import it).
        "pcae.core.hpac_rhamp_enrollment",
        # Phase .1R.30R.4R.1 — HPAC-PAWA-001 v1.2 (HPAC-PAWA-REQ-087) adds
        # exactly one category: the bounded protected-presentation-mechanism
        # configuration administration tool specified by HPAC-PPA-001 v1.0
        # (HPAC-PPA-REQ-022). Exact dotted-path, no wildcard/prefix/glob
        # (PAWA-INV-9). Reached only from the standalone
        # scripts/hpac_protected_presentation_admin.py entry point; itself
        # inside the non-agent-importable fence.
        "pcae.core.hpac_protected_presentation_admin",
    }
)
#: A disclosed, explicit **test-only** consumer allowlist (§16 seam,
#: HPAC-PAWA-REQ-166). Exact names, never a prefix.
_TEST_FACTORY_CONSUMERS = frozenset(
    {
        "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1",
        # Phase .1R.30R.4R.1 — the fresh dedicated implementation suite for the
        # v1.2 configure_presentation_mechanism family (HPAC-PAWA-REQ-166).
        "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_1_protected_presentation_real_assurance",
    }
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
    """Real call-provenance detection (§32 "Recognition predicate 6";
    HPAC-PAWA-REQ-235, PAWA-INV-9).

    N16-5-F-5-B2-IMPL repair: ``explicit`` is retained as a parameter only
    for call-site / source-scan continuity across the four privileged
    factories — it is intentionally **never returned and never otherwise
    consulted**. Trusting a caller-supplied string verbatim was the entire
    root cause of the N16-5-F-5-B2 finding: any in-process caller of
    ``production_writer`` / ``certification_writer`` /
    ``recognized_certification_read_authority`` /
    ``mint_protected_presentation_evidence_writer`` could pass
    ``_caller_module`` set to any enumerated consumer name and be recognized
    as that consumer, defeating the §38/§38A/§38B/HPAC-PPA-REQ-041
    enumerated-consumer allowlists entirely. The consumer identity used by
    §33 step 9 (and its per-factory restatements) is now, unconditionally,
    the REAL importing/calling source module — a build-time / import-time
    fact established by walking the live call stack — never a
    caller-asserted label. A disclosed test seam that needs a different
    *real* module identity must make the call genuinely originate from
    that module (see ``tests/_caller_identity_helper.py``), not merely
    assert a string.
    """
    del explicit  # intentionally ignored — see docstring above.
    stack = inspect.stack()
    # 0: _detect_caller_module, 1: the factory function, 2: its real caller.
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
    authorized_consumers: "frozenset[str]" = AUTHORIZED_FACTORY_CONSUMERS,
    test_consumers: "frozenset[str]" = _TEST_FACTORY_CONSUMERS,
) -> _RecognizedAnchor:
    # §33 step 9 is the authorized-factory-consumer check (§32). The step
    # itself — the check, its position, its ``unauthorized_factory_consumer``
    # code — is verbatim for every factory; only the *enumerated set* it
    # checks against is per-factory (the §36 administrative-mutation factory
    # vs. the v1.3 §33A ``certification_writer`` factory, whose enumerated
    # set is the single §38A consumer). No wildcard / prefix / glob for
    # either set (PAWA-INV-9). HPAC-PAWA-REQ-235.
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
        if caller_module not in authorized_consumers and caller_module not in test_consumers:
            raise PawaError("unauthorized_factory_consumer", f"{caller_module!r} is not an enumerated consumer (§38 / §38A)")

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
        "transaction_id",
        "mechanism_id",
        "presentation_action",
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
        transaction_id: Optional[str] = None,
        mechanism_id: Optional[str] = None,
        presentation_action: Optional[str] = None,
    ) -> None:
        self._capability = capability
        self._authority = authority
        self.operation = operation
        self.principal_id = principal_id
        self.credential_id = credential_id
        self.transaction_id = transaction_id
        self.mechanism_id = mechanism_id
        self.presentation_action = presentation_action
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
        transaction_id: Optional[str] = None,
        mechanism_id: Optional[str] = None,
    ) -> HPACWriterCapability:
        if self._consumed or self._capability._spent:
            raise PawaError("capability_stale", "this PRODUCTION writer has already been used")
        if operation != self.operation:
            raise PawaError("target_scope_invalid", f"handle bound to {self.operation.value}, used for {operation}")
        if principal_id != self.principal_id:
            raise PawaError("target_scope_invalid", "handle bound to a different principal_id")
        if credential_id != self.credential_id:
            raise PawaError("target_scope_invalid", "handle bound to a different credential_id")
        if transaction_id != self.transaction_id:
            raise PawaError("target_scope_invalid", "handle bound to a different enrollment transaction_id")
        if mechanism_id != self.mechanism_id:
            raise PawaError("target_scope_invalid", "handle bound to a different presentation mechanism_id")
        self._consumed = True
        return self._capability

    @property
    def capability_subject(self) -> Optional[str]:
        """The exact ``subject`` the wrapped capability is bound to — the
        enrollment ``transaction_id`` for ``enroll_credential`` (HPAC-PAWA-REQ-100),
        else the ``principal_id`` / ``credential_id``."""

        return self._capability.subject


# ─────────────────────────────────────────────────────────────────────────
# §33 step 10 — the production_writer factory (§36)
# ─────────────────────────────────────────────────────────────────────────


def _validate_operation_inputs(
    operation,
    principal_id: Optional[str],
    credential_id: Optional[str],
    transaction_id: Optional[str] = None,
    mechanism_id: Optional[str] = None,
    presentation_action: Optional[str] = None,
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
    if op not in _AVAILABLE_OPERATIONS:
        raise PawaError("operation_scope_invalid", f"{op.value} is not an available §42 mutation class")
    if principal_id is not None and (not isinstance(principal_id, str) or not principal_id.strip()):
        raise PawaError("operation_scope_invalid", "principal_id must be a non-empty string or None")
    if credential_id is not None and (not isinstance(credential_id, str) or not credential_id.strip()):
        raise PawaError("operation_scope_invalid", "credential_id must be a non-empty string or None")
    if transaction_id is not None and (not isinstance(transaction_id, str) or not transaction_id.strip()):
        raise PawaError("operation_scope_invalid", "transaction_id must be a non-empty string or None")
    if op is PawaOperation.ENROLL_PRINCIPAL and (principal_id is None or credential_id is not None):
        raise PawaError("operation_scope_invalid", "enroll_principal requires principal_id and no credential_id")
    if op is PawaOperation.REVOKE_PRINCIPAL and (principal_id is None or credential_id is not None):
        raise PawaError("operation_scope_invalid", "revoke_principal requires principal_id and no credential_id")
    if op is PawaOperation.REVOKE_CREDENTIAL and (credential_id is None):
        raise PawaError("operation_scope_invalid", "revoke_credential requires credential_id")
    if op is PawaOperation.ENROLL_CREDENTIAL:
        # HPAC-PAWA-REQ-100 — the fresh opaque hpc-<hex> credential_id does
        # not exist until the write; the capability binds to the enrollment
        # transaction id + the target principal_id, NOT to a credential_id.
        if principal_id is None or transaction_id is None or credential_id is not None:
            raise PawaError(
                "operation_scope_invalid",
                "enroll_credential requires principal_id + transaction_id and no credential_id (HPAC-PAWA-REQ-100)",
            )
    if op is PawaOperation.INITIALIZE_CREDENTIAL_SIDECAR_STATE and credential_id is None:
        raise PawaError("operation_scope_invalid", "initialize_credential_sidecar_state requires credential_id")
    if op is PawaOperation.CONFIGURE_PRESENTATION_MECHANISM:
        # HPAC-PAWA-REQ-093/095 — bound to the exact presentation mechanism_id
        # and one configuration transaction; no principal/credential scope is
        # inferred from a mechanism subject.
        if (
            mechanism_id is None
            or not isinstance(mechanism_id, str)
            or not mechanism_id.strip()
            or transaction_id is None
            or principal_id is not None
            or credential_id is not None
        ):
            raise PawaError(
                "operation_scope_invalid",
                "configure_presentation_mechanism requires mechanism_id + transaction_id and "
                "no principal_id/credential_id (HPAC-PAWA-REQ-093/095)",
            )
        if presentation_action not in _PRESENTATION_LIFECYCLE_ACTIONS:
            raise PawaError(
                "operation_scope_invalid",
                "configure_presentation_mechanism requires a closed lifecycle action "
                f"(one of {sorted(_PRESENTATION_LIFECYCLE_ACTIONS)})",
            )
    elif mechanism_id is not None or presentation_action is not None:
        raise PawaError(
            "operation_scope_invalid",
            "mechanism_id / presentation_action are only valid for configure_presentation_mechanism",
        )
    return op


def production_writer(
    operation,
    *,
    principal_id: Optional[str] = None,
    credential_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
    mechanism_id: Optional[str] = None,
    presentation_action: Optional[str] = None,
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
    op = _validate_operation_inputs(
        operation, principal_id, credential_id, transaction_id, mechanism_id, presentation_action
    )
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
    is_txn = op in _MULTI_WRITE_OPERATIONS
    if op is PawaOperation.CONFIGURE_PRESENTATION_MECHANISM:
        # HPAC-PAWA-REQ-093 — subject is the exact presentation mechanism_id;
        # role is the frozen installer role, not the registry role.
        subject = mechanism_id
        mint_role = _PRESENTATION_INSTALLER_ROLE
    elif op is PawaOperation.ENROLL_CREDENTIAL:
        # HPAC-PAWA-REQ-100 — bound to the enrollment transaction id.
        subject = transaction_id
        mint_role = _REGISTRY_WRITER_ROLE
    elif principal_id is not None:
        subject = principal_id
        mint_role = _REGISTRY_WRITER_ROLE
    else:
        subject = credential_id
        mint_role = _REGISTRY_WRITER_ROLE
    try:
        capability = recognized.authority._mint_production_writer_capability(
            mint_role,
            subject,
            _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL,
            multi_write=is_txn,
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
        transaction_id=transaction_id,
        mechanism_id=mechanism_id,
        presentation_action=presentation_action,
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
        enrollment_transaction_id=transaction_id,
        result="issued",
        capability_identifier="hpaw-cap-" + hashlib.sha256(operation_id.encode()).hexdigest()[:32],
        context_annotation=(
            # HPAC-PAWA-REQ-093 — record (but do not add as a bearer capability
            # field) the exact presentation configuration transaction id and
            # requested lifecycle action.
            f"configure_presentation_mechanism:{mechanism_id}:{presentation_action}"
            if op is PawaOperation.CONFIGURE_PRESENTATION_MECHANISM
            else None
        ),
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
    enrollment_transaction_id: Optional[str] = None,
    context_annotation: Optional[str] = None,
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
        enrollment_transaction_id=enrollment_transaction_id,
        issued_at=_now(),
        issuer=_ISSUER,
        result=result,
        capability_identifier=capability_identifier,
        context_annotation=context_annotation,
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


# ─────────────────────────────────────────────────────────────────────────
# HPAC-PPA-001 v1.0 §8 — the runtime protected-presentation evidence-writer
# factory. Distinct authority from the §42 PAWA installer factory
# (INSTALLER AUTHORITY != LAUNCHER AUTHORITY != RUNTIME EVIDENCE-WRITER
# AUTHORITY, .30R.4R). Reachable ONLY from the trusted launcher mediator
# `pcae.core.protected_presentation` (HPAC-PPA-REQ-041); a guard test
# asserts no other production module imports or calls it, and
# `hpac_verifier` / the helper process never reach it.
# ─────────────────────────────────────────────────────────────────────────

#: HPAC-PPA-REQ-041/052 — the exact finite set of modules that may request a
#: `protected_presentation_mechanism` runtime evidence-writer capability. No
#: wildcard, no prefix, no glob (PAWA-INV-9).
PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS = frozenset({"pcae.core.protected_presentation"})
_PROTECTED_PRESENTATION_EVIDENCE_WRITER_ROLE = "protected_presentation_mechanism"

#: A disclosed, explicit **test-only** consumer allowlist for
#: ``mint_protected_presentation_evidence_writer`` (§16 seam,
#: HPAC-PAWA-REQ-166 discipline — mirrors ``_TEST_FACTORY_CONSUMERS`` /
#: ``_CERTIFICATION_TEST_CONSUMERS`` / ``_READ_AUTHORITY_TEST_CONSUMERS``).
#: Exact module names, never a prefix. Extracted from the former inline
#: literal (N16-5-F-5-B2-IMPL) so a second disclosed test consumer could be
#: added without duplicating the set at the call site.
_PROTECTED_PRESENTATION_EVIDENCE_TEST_CONSUMERS = frozenset(
    {
        "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_1_protected_presentation_real_assurance",
        "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_2_protected_presentation_real_assurance_iv",
    }
)


def mint_protected_presentation_evidence_writer(
    authority: HPACStoreAuthority,
    *,
    mechanism_id: str,
    _caller_module: Optional[str] = None,
) -> HPACWriterCapability:
    """HPAC-PPA-REQ-041/042 — mint one process-local, non-serializable,
    restart-dead, single-use ``HPACWriterCapability`` for the existing
    ``protected_presentation_mechanism`` runtime evidence-writer role, bound
    to this ``HPACStoreAuthority`` instance's private ``_seal`` and to the
    exact presentation ``mechanism_id``.

    It is NOT a PAWA installer capability and does not extend the §42
    mutation set (HPAC-PPA-REQ-040). It authorizes exactly one create-only
    ``HPAC-PRESENTATION-EVIDENCE/2.0`` write; the launcher enforces the
    one-APPROVE / one-write / single-use invariant (HPAC-PPA-REQ-043..046).
    """

    caller_module = _detect_caller_module(_caller_module)
    if (
        caller_module not in PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS
        and caller_module not in _PROTECTED_PRESENTATION_EVIDENCE_TEST_CONSUMERS
    ):
        raise PawaError(
            "unauthorized_factory_consumer",
            f"{caller_module!r} is not the trusted protected-presentation launcher (HPAC-PPA-REQ-041)",
        )
    if not isinstance(mechanism_id, str) or not mechanism_id.strip():
        raise PawaError("operation_scope_invalid", "mechanism_id must be a non-empty string")
    if not isinstance(authority, HPACStoreAuthority) or authority.authority_class is not HPACAuthorityClass.PRODUCTION:
        raise PawaError(
            "internal_fail_closed",
            "the runtime evidence writer requires a PRODUCTION HPACStoreAuthority",
        )
    try:
        return authority._mint_production_writer_capability(
            _PROTECTED_PRESENTATION_EVIDENCE_WRITER_ROLE,
            mechanism_id,
            _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL,
            multi_write=False,
        )
    except HPACAuthorityError as exc:
        raise PawaError("internal_fail_closed", f"evidence-writer mint refused: {exc}")


# ─────────────────────────────────────────────────────────────────────────
# HPAC-PAWA-001 v1.3 §33A / §38A / §42B / §49A — the dedicated
# ``certification_writer`` factory. DISTINCT from the §36 ``production_writer``
# administrative-mutation factory: a separate symbol, its own recognition
# entry, its own closed consumer inventory, its own closed role allowlist.
# It reuses the §33 steps 1–9 verbatim (via ``_run_recognition_sequence``,
# only the enumerated consumer set swapped), the same
# ``_PRODUCTION_WRITER_FACTORY_SEAL`` mint trust root, the same
# ``HPACWriterCapability`` type, and the same single-use / non-bearer /
# process-local / restart-dead semantics (§45–§49, §49A). It introduces
# NO new ``PawaOperation``, NO new ``pawa_failure_code``, NO schema, NO
# generic string-addressable role escalation, NO caller-controlled generic
# writer. HPAC-PAWA-REQ-234..268, PAWA-INV-13.
# ─────────────────────────────────────────────────────────────────────────

#: §38A (HPAC-PAWA-REQ-239) — the EXACT enumerated certification-writer
#: consumer inventory: the one bounded N-16-5 real-human-authentication
#: certification coordinator. No launcher, helper, presentation store,
#: verifier, Gate, gate coordinator, runtime, agent, CLI, or plugin. No
#: wildcard / prefix / glob / fnmatch (PAWA-INV-9). Any new consumer fails
#: the §39A guard until explicitly added here AND the contract is amended by
#: a new governed evolution.
CERTIFICATION_FACTORY_CONSUMERS = frozenset({"pcae.core.hpac_certification_coordinator"})

#: A disclosed, explicit **test-only** certification-consumer allowlist
#: (§16 seam, HPAC-PAWA-REQ-166 / HPAC-PAWA-REQ-265). Exact module names,
#: never a prefix. A guard test asserts no non-test module is a member.
_CERTIFICATION_TEST_CONSUMERS = frozenset(
    {
        "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_h3_impl",
    }
)

#: §42B (HPAC-PAWA-REQ-246) — the CLOSED five-role certification-lifecycle
#: writer allowlist, EXACTLY. Independently revalidated against primary
#: source: ``HPACLifecycleStore._GENESIS_WRITER_ROLE`` /
#: ``_ASSERTION_WRITER_ROLE`` / ``_VERIFIED_WRITER_ROLE`` / ``_BOUND_WRITER_ROLE``
#: and ``hpac_rhamp_counter_state.COUNTER_STATE_VERIFIER_ROLE``.
#: ``HPACLifecycleStore._TERMINAL_WRITER_ROLE`` ("hpac_lifecycle_terminator",
#: negative terminal states only) is **explicitly NOT** a member. No
#: wildcard, no prefix, no fnmatch, no arbitrary role argument.
CERTIFICATION_LIFECYCLE_ROLES = (
    "hpac_challenge_coordinator",
    "hpac_assertion_recorder",
    "human_authentication_proof_verifier",
    "hpac_gate5_binder",
)
CERTIFICATION_COUNTER_ROLE = "hpac_rhamp_counter_state_verifier"
CERTIFICATION_ROLE_ALLOWLIST = frozenset(CERTIFICATION_LIFECYCLE_ROLES + (CERTIFICATION_COUNTER_ROLE,))
assert len(CERTIFICATION_ROLE_ALLOWLIST) == 5
#: The role explicitly denied even though it is a real lifecycle writer role
#: (defence-in-depth readability; the allowlist membership check already
#: rejects it — this is only to make the intent legible and testable).
_CERTIFICATION_DENIED_TERMINATOR_ROLE = "hpac_lifecycle_terminator"
assert _CERTIFICATION_DENIED_TERMINATOR_ROLE not in CERTIFICATION_ROLE_ALLOWLIST

#: The proof-verifier role performs one bounded verification transaction —
#: two canonical writes (``HumanAuthenticationProofStore.create_canonical``
#: → ``proof.json`` and ``HPACLifecycleStore.record_verified_canonical`` →
#: ``STATE_PROOF_VERIFIED``) that §42B / §49A treat as **one** verification
#: lifecycle. It is minted ``_multi_write`` and spent once by the coordinator
#: via ``authority.complete_multi_write`` after both writes + read-back.
#: Every other role performs exactly one canonical write and is minted as an
#: ordinary single-use (spend-on-first-write) capability.
_CERTIFICATION_MULTI_WRITE_ROLES = frozenset({"human_authentication_proof_verifier"})

_CERTIFICATION_ISSUER = "pcae.core.hpac_protected_admin_writer.certification_writer/1.3"


class CertificationWriterHandle:
    """A single-use, role- and session-scoped handle around one
    ``PRODUCTION`` certification-lifecycle ``HPACWriterCapability`` (§42B /
    §49A). The wrapped capability is ``_single_use`` at the foundation layer;
    this handle additionally refuses a second ``.consume()`` at the factory
    layer with ``capability_stale`` and refuses a mismatched
    role / session / subject with ``target_scope_invalid``.

    FACTORY ≠ CONSUMER, CONSUMER ≠ MINTER (§15 / HPAC-PAWA-REQ-250): the
    handle exposes no remint / delegate / convert-to-generic / serialise /
    reissue path. ``__reduce__`` raises. A second ``certification_writer``
    call re-runs the full §33A sequence.
    """

    __slots__ = (
        "_capability",
        "_authority",
        "role",
        "certification_session_id",
        "subject",
        "principal_id",
        "credential_id",
        "proof_id",
        "multi_write",
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
        role: str,
        certification_session_id: str,
        subject: str,
        principal_id: str,
        credential_id: str,
        proof_id: Optional[str],
        multi_write: bool,
        operation_id: str,
        anchor_id: str,
        installation_id: str,
        descriptor_generation: int,
    ) -> None:
        self._capability = capability
        self._authority = authority
        self.role = role
        self.certification_session_id = certification_session_id
        self.subject = subject
        self.principal_id = principal_id
        self.credential_id = credential_id
        self.proof_id = proof_id
        self.multi_write = multi_write
        self.operation_id = operation_id
        self.anchor_id = anchor_id
        self.installation_id = installation_id
        self.descriptor_generation = descriptor_generation
        self._consumed = False

    def __reduce__(self):
        raise TypeError("CertificationWriterHandle is process-local and non-serializable")

    @property
    def authority(self) -> HPACStoreAuthority:
        return self._authority

    def consume(
        self,
        role: str,
        *,
        certification_session_id: str,
        subject: str,
    ) -> HPACWriterCapability:
        """Hand the wrapped one-shot capability to the exact canonical store
        call it was minted for. A second call, a wrong role, a wrong
        session, or a wrong subject fails closed."""

        if self._consumed or getattr(self._capability, "_spent", True):
            raise PawaError("capability_stale", "this certification writer has already been used")
        if role != self.role:
            raise PawaError("target_scope_invalid", f"handle bound to role {self.role!r}, used for {role!r}")
        if certification_session_id != self.certification_session_id:
            raise PawaError("target_scope_invalid", "handle bound to a different certification_session_id")
        if subject != self.subject:
            raise PawaError("target_scope_invalid", "handle bound to a different subject")
        if not self.multi_write:
            self._consumed = True
        return self._capability

    def complete(self) -> None:
        """Spend a ``_multi_write`` proof-verifier capability exactly once,
        after both of its bounded writes + read-back (§49A). A non-multi-write
        handle is already spent by its single ``record_write``."""

        if not self.multi_write:
            return
        if self._consumed:
            raise PawaError("capability_stale", "this certification writer has already been completed")
        self._consumed = True
        try:
            self._authority.complete_multi_write(self._capability)
        except HPACAuthorityError as exc:
            raise PawaError("capability_stale", f"multi-write completion refused: {exc}")


def _validate_certification_inputs(
    role: object,
    certification_session_id: object,
    principal_id: object,
    credential_id: object,
    proof_id: object,
) -> "tuple[str, str, str, str, Optional[str]]":
    # §42B / §42C (HPAC-PAWA-REQ-246/252) — role ∉ allowlist (incl.
    # ``hpac_lifecycle_terminator``, a wildcard, a prefix, an arbitrary
    # string) → ``operation_scope_invalid`` (#16). EXACT set membership;
    # no ``startswith`` / glob / fnmatch / regex family recognition.
    if not isinstance(role, str) or role not in CERTIFICATION_ROLE_ALLOWLIST:
        raise PawaError(
            "operation_scope_invalid",
            f"{role!r} is not a member of the closed §42B certification role allowlist",
        )

    def _req(value: object, name: str) -> str:
        # §33A step 3 (HPAC-PAWA-REQ-236.3) — a nonempty string; an explicit
        # ``None`` / empty / whitespace / non-str bypass → ``operation_scope_invalid``.
        if not isinstance(value, str) or not value.strip():
            raise PawaError("operation_scope_invalid", f"{name} must be a non-empty string")
        return value

    sid = _req(certification_session_id, "certification_session_id")
    pid = _req(principal_id, "principal_id")
    cid = _req(credential_id, "credential_id")
    # Every certification role is bound into one ceremony identified by its
    # reserved ``proof_id`` (§43A / HPAC-PAWA-REQ-256 — reserved before the
    # ceremony, exactly as §100 reserves an enrollment-transaction id). It is
    # the ``subject`` for the four lifecycle roles and the session anchor for
    # the counter role (whose ``subject`` is the ``credential_id``).
    pf = _req(proof_id, "proof_id")
    if not re.fullmatch(r"hap-[0-9a-f]{32}", pf):
        raise PawaError("operation_scope_invalid", "proof_id does not match the reserved hap- grammar")
    return role, sid, pid, cid, pf


def _validate_certification_session_binding(
    authority: HPACStoreAuthority,
    *,
    principal_id: str,
    credential_id: str,
) -> None:
    """§33A step 3 (HPAC-PAWA-REQ-236.3 / §42C HPAC-PAWA-REQ-252) — the
    target ``principal_id`` SHALL resolve to an **active, not-revoked**
    ``PrincipalRecord`` (the canonical record is mechanism-neutral by
    construction — HPAC-REQ-013 has no mechanism field), and the target
    ``credential_id`` SHALL resolve to an **active, not-revoked**
    ``CredentialRecord`` **bound to that principal**. Any failure →
    ``operation_scope_invalid``. This is a pure protected-store read; it
    mints nothing and writes nothing."""

    from pcae.core.human_principal_registry import HumanPrincipalRegistryStore

    try:
        registry = HumanPrincipalRegistryStore(authority)
        principal = registry.resolve_principal(principal_id)
        credential = registry.resolve_credential(credential_id)
    except Exception as exc:  # noqa: BLE001 — fail-closed read boundary (§0)
        raise PawaError("operation_scope_invalid", f"certification target resolution failed: {type(exc).__name__}: {exc}")
    if principal is None or getattr(principal, "status", None) != "active":
        raise PawaError("operation_scope_invalid", "certification target principal is unresolvable or not active")
    if credential is None or getattr(credential, "status", None) != "active":
        raise PawaError("operation_scope_invalid", "certification target credential is unresolvable or not active")
    if credential.principal_id != principal_id:
        raise PawaError("operation_scope_invalid", "certification target credential is not bound to the target principal")


def certification_writer(
    role: str,
    *,
    certification_session_id: str,
    principal_id: str,
    credential_id: str,
    proof_id: Optional[str] = None,
    _protected_root: Optional[Path] = None,
    _configured_agent_identity_source=None,
    _topology_probe: Optional["TopologyProbe"] = None,
    _caller_module: Optional[str] = None,
) -> CertificationWriterHandle:
    """§33A (HPAC-PAWA-REQ-234..238) — mint exactly one process-local,
    single-use, restart-dead ``PRODUCTION`` certification-lifecycle
    ``HPACWriterCapability`` (§42B) after a fresh, complete §33 recognition
    sequence (steps 1–9 verbatim) plus the certification-specific
    consumer / role-allowlist / session-binding / mint / audit steps.

    Runs fresh on every call — no result is cached (HPAC-PAWA-REQ-237).
    ``HPACStoreAuthority.writer(role)`` still ``raise``s for every
    non-``FIXTURE_NON_REAL`` class (HPAC-PAWA-REQ-092 unchanged); this is not
    a generic ``production_writer`` and takes no caller-controlled generic
    role.

    ``_protected_root`` / ``_configured_agent_identity_source`` /
    ``_topology_probe`` / ``_caller_module`` are the disclosed test-only
    seams (§72/§73 / HPAC-PAWA-REQ-166); a guard test asserts no non-test
    module passes any of them and that the only production caller is the
    §38A consumer's §33A path.

    Raises :class:`PawaError` (code ∈ :data:`PAWA_FAILURE_CODES`, unchanged
    21-value taxonomy) on any failure; mints nothing on any failure
    (HPAC-PAWA-REQ-238, fail-closed).
    """

    caller_module = _detect_caller_module(_caller_module)
    role, sid, pid, cid, pf = _validate_certification_inputs(
        role, certification_session_id, principal_id, credential_id, proof_id
    )

    recognized = _run_recognition_sequence(
        protected_root=_protected_root,
        configured_agent_identity_source=_configured_agent_identity_source,
        caller_module=caller_module,
        topology_probe=_topology_probe,
        authorized_consumers=CERTIFICATION_FACTORY_CONSUMERS,
        test_consumers=_CERTIFICATION_TEST_CONSUMERS,
    )

    # §33A additional step 1 (HPAC-PAWA-REQ-236.1) — restate the exact §38A
    # consumer check explicitly (defence in depth; step 9 above already
    # enforced it against the certification set).
    if caller_module not in CERTIFICATION_FACTORY_CONSUMERS and caller_module not in _CERTIFICATION_TEST_CONSUMERS:
        raise PawaError("unauthorized_factory_consumer", f"{caller_module!r} is not the §38A certification consumer")

    # §33A additional step 3 — certification-session context binding, keyed
    # off the recognized PRODUCTION authority (a protected-store read only).
    _validate_certification_session_binding(recognized.authority, principal_id=pid, credential_id=cid)

    # STEP 10 — bind the configured-agent identity, then mint (identical
    # trust root and seal discipline as ``production_writer`` — §36 / §41).
    recognized.authority._bind_configured_agent_identity(
        (recognized.configured_agent.uid, recognized.configured_agent.gids),
        _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL,
    )
    is_multi = role in _CERTIFICATION_MULTI_WRITE_ROLES
    subject = cid if role == CERTIFICATION_COUNTER_ROLE else pf
    try:
        capability = recognized.authority._mint_production_writer_capability(
            role,
            subject,
            _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL,
            multi_write=is_multi,
        )
    except HPACAuthorityError as exc:
        raise PawaError("internal_fail_closed", f"certification mint refused: {exc}")

    operation_id = new_operation_id()
    handle = CertificationWriterHandle(
        capability=capability,
        authority=recognized.authority,
        role=role,
        certification_session_id=sid,
        subject=subject,
        principal_id=pid,
        credential_id=cid,
        proof_id=pf,
        multi_write=is_multi,
        operation_id=operation_id,
        anchor_id=recognized.anchor_id,
        installation_id=recognized.installation_id,
        descriptor_generation=recognized.generation,
    )

    # §42B / §55 (HPAC-PAWA-REQ-246/251) — the issuance audit event. The
    # role / certification_session_id / proof_id / ceremony phase are
    # recorded as NON-AUTHORITATIVE facts (never capability fields, never the
    # seal). No new schema; the existing HPAC-PAWA-ISSUANCE-EVIDENCE/1.0
    # ``operation`` / ``context_annotation`` fields carry them.
    _record_issuance_evidence(
        recognized.root,
        operation_id=operation_id,
        operation=f"certification_lifecycle_writer:{role}",
        anchor_id=recognized.anchor_id,
        installation_id=recognized.installation_id,
        descriptor_generation=recognized.generation,
        protected_root_identity=recognized.live_root_identity,
        target_principal_id=pid,
        target_credential_id=cid,
        enrollment_transaction_id=None,
        result="issued",
        capability_identifier="hpaw-cert-" + hashlib.sha256(operation_id.encode()).hexdigest()[:32],
        context_annotation=f"certification_session={sid};role={role};proof_id={pf};phase=issue",
    )
    return handle


# ─────────────────────────────────────────────────────────────────────────
# HPAC-PAWA-001 v1.4 §33B / §38B / §42D / §49B / §68B — the dedicated
# recognized_certification_read_authority accessor (F-5-B1 repair,
# alias N16-5-F-5-B1-IMPL). DISTINCT from ``certification_writer``: this
# path grants NO HPACWriterCapability and NO mutation authority of any
# kind — read-only access to a closed, enumerated set of canonical
# protected-store records plus a single bounded protected-presentation
# ceremony-entry hand-off. It reuses the §33 steps 1-9 verbatim (via
# ``_run_recognition_sequence``, only the enumerated consumer set
# swapped — reusing the already-enumerated §38A/§38B set, HPAC-PAWA-REQ-281),
# the same ``_PRODUCTION_WRITER_FACTORY_SEAL`` trust root discipline (reused
# for the constructor seal and the configured-agent bind, never a second
# root), and the same process-local / non-bearer / restart-dead / one-shot
# semantics (§45-§49, §49B). It introduces NO new ``PawaOperation``, NO new
# ``pawa_failure_code``, NO schema, NO writer role, and exposes NO ``writer()``
# / ``production_writer`` / ``certification_writer`` / raw-authority escape.
# HPAC-PAWA-REQ-276..300, PAWA-INV-3/9/10/12/13/14.
#
# F-5-B1 root cause repaired here: the underlying
# ``HPACStoreAuthority._validate_production_boundary`` negative check keys
# off ``_configured_agent_identity`` when bound, and off the *live invoking
# process* identity when not. Running the deployment-owner tool under real
# sudo/root means the live process identity legitimately CAN write the
# protected root, so any protected-store read attempted on an unbound
# authority while running as root/sudo fails the boundary check outright
# (`production HPAC root is not protected from the configured agent
# principal`) -- root is never implicitly trusted. Binding the resolved
# CONFIGURED-AGENT identity (REQ-278.3, done here BEFORE the first
# protected-store canonical read) repairs this: the boundary is then
# evaluated against the configured agent (who genuinely lacks write
# access), so the deployment owner's real reads succeed while an
# unbound / never-recognized direct read stays denied.
# ─────────────────────────────────────────────────────────────────────────

#: §38B (HPAC-PAWA-REQ-281) — v1.4 adds NO new factory-consumer category;
#: the sole authorized read-authority consumer is the already-enumerated
#: §38A N-16-5 certification coordinator.
READ_AUTHORITY_CONSUMERS = CERTIFICATION_FACTORY_CONSUMERS

#: A disclosed, explicit **test-only** read-authority consumer allowlist
#: (§16 seam, HPAC-PAWA-REQ-166/282/265 discipline). Exact module names,
#: never a prefix. A guard test asserts no non-test module is a member.
_READ_AUTHORITY_TEST_CONSUMERS = frozenset(
    {
        "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_f5b1_impl",
    }
)

_READ_AUTHORITY_ISSUER = "pcae.core.hpac_protected_admin_writer.recognized_certification_read_authority/1.4"


def _validate_read_authority_inputs(
    certification_session_id: object,
    principal_id: object,
    credential_id: object,
    proof_id: object,
) -> "tuple[str, str, str, str]":
    # §33B step (HPAC-PAWA-REQ-278.2) — a nonempty string for each; an
    # explicit ``None`` / empty / whitespace / non-str bypass →
    # ``operation_scope_invalid``.
    def _req(value: object, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise PawaError("operation_scope_invalid", f"{name} must be a non-empty string")
        return value

    sid = _req(certification_session_id, "certification_session_id")
    pid = _req(principal_id, "principal_id")
    cid = _req(credential_id, "credential_id")
    pf = _req(proof_id, "proof_id")
    if not re.fullmatch(r"hap-[0-9a-f]{32}", pf):
        raise PawaError("operation_scope_invalid", "proof_id does not match the reserved hap- grammar")
    return sid, pid, cid, pf


def _validate_read_authority_session_binding(
    authority: HPACStoreAuthority,
    *,
    principal_id: str,
    credential_id: str,
) -> None:
    """§33B step (HPAC-PAWA-REQ-278.2, executed AFTER the configured-agent
    bind per the phase's independently-verified normative execution order
    — HPAC-PAWA-REQ-278 note): resolve the bound principal / credential
    through the **provenance-verified canonical** reads
    (``resolve_canonical_principal`` / ``resolve_canonical_credential``),
    which route through ``HPACStoreAuthority.store_id`` ->
    ``_ensure_root(create=False)`` -> ``_validate_production_boundary()``.
    This is the exact protected-store read the F-5-B1 finding requires to
    pass under the CONFIGURED-AGENT binding rather than the ambient
    (sudo/root) invoking-process identity. A pure read; mints nothing."""

    from pcae.core.human_principal_registry import HumanPrincipalRegistryStore

    try:
        registry = HumanPrincipalRegistryStore(authority)
        principal_resolution = registry.resolve_canonical_principal(principal_id)
        credential_resolution = registry.resolve_canonical_credential(credential_id)
    except HPACAuthorityError:
        raise
    except Exception as exc:  # noqa: BLE001 — fail-closed read boundary (§0)
        raise PawaError("operation_scope_invalid", f"read-authority target resolution failed: {type(exc).__name__}: {exc}")
    if principal_resolution is None or getattr(principal_resolution.record, "status", None) != "active":
        raise PawaError("operation_scope_invalid", "read-authority target principal is unresolvable or not active")
    if credential_resolution is None or getattr(credential_resolution.record, "status", None) != "active":
        raise PawaError("operation_scope_invalid", "read-authority target credential is unresolvable or not active")
    if credential_resolution.record.principal_id != principal_id:
        raise PawaError("operation_scope_invalid", "read-authority target credential is not bound to the target principal")


class CertificationReadAuthority:
    """§33B/§42D/§49B (v1.4) — a process-local, single-ceremony-entry,
    restart-dead, non-bearer handle wrapping a recognized ``PRODUCTION``
    ``HPACStoreAuthority``. Exposes **only** the §42D closed read scope
    plus **one** bounded protected-presentation ceremony-entry hand-off.

    Grants **no** ``HPACWriterCapability``, no ``writer()`` /
    ``production_writer(...)`` / ``certification_writer(...)`` /
    ``_mint_production_writer_capability(...)`` /
    ``_bind_configured_agent_identity(...)`` re-invocation, and no
    remint / delegate / serialise / generic-authority conversion (§68B,
    HPAC-PAWA-REQ-287). ``__reduce__`` raises. There is intentionally no
    public method or property that returns the wrapped
    ``HPACStoreAuthority`` (no raw-authority escape).

    Constructed **only** by :func:`recognized_certification_read_authority`.
    """

    __slots__ = (
        "_authority",
        "certification_session_id",
        "principal_id",
        "credential_id",
        "proof_id",
        "anchor_id",
        "installation_id",
        "descriptor_generation",
        "_ceremony_consumed",
    )

    def __init__(
        self,
        *,
        _factory_seal: object,
        authority: HPACStoreAuthority,
        certification_session_id: str,
        principal_id: str,
        credential_id: str,
        proof_id: str,
        anchor_id: str,
        installation_id: str,
        descriptor_generation: int,
    ) -> None:
        if _factory_seal is not _PRODUCTION_WRITER_FACTORY_SEAL:
            raise HPACAuthorityError(
                "CertificationReadAuthority can only be constructed by the recognized read-authority factory"
            )
        if not isinstance(authority, HPACStoreAuthority) or authority.authority_class is not HPACAuthorityClass.PRODUCTION:
            raise HPACAuthorityError("CertificationReadAuthority requires a PRODUCTION HPACStoreAuthority")
        self._authority = authority
        self.certification_session_id = certification_session_id
        self.principal_id = principal_id
        self.credential_id = credential_id
        self.proof_id = proof_id
        self.anchor_id = anchor_id
        self.installation_id = installation_id
        self.descriptor_generation = descriptor_generation
        self._ceremony_consumed = False

    def __reduce__(self):
        raise TypeError("CertificationReadAuthority is process-local and non-serializable")

    def _check_live(self) -> None:
        # §49B (HPAC-PAWA-REQ-294) — confers no authority once the
        # session's ceremony has been entered.
        if self._ceremony_consumed:
            raise PawaError("capability_stale", "this read authority's ceremony entry has already been used")
        # Force the F-5-B1-repaired boundary check on *every* read,
        # independent of which specific store method is used underneath
        # (``store_id`` -> ``_ensure_root(create=False)`` ->
        # ``_validate_production_boundary()``).
        try:
            self._authority.store_id
        except HPACAuthorityError as exc:
            raise PawaError("internal_fail_closed", f"read-authority boundary re-check failed: {exc}")

    # ── §42D closed read scope (HPAC-PAWA-REQ-284) ───────────────────────

    def read_principal_and_credential(self):
        """The ``PrincipalRecord`` for the bound ``principal_id`` and the
        ``CredentialRecord`` for the bound ``credential_id``, both via
        provenance-verified canonical resolution. Returns plain records —
        never an ``HPACResolvedRecord`` (which carries ``authority_seal``)."""

        self._check_live()
        from pcae.core.human_principal_registry import HumanPrincipalRegistryStore

        registry = HumanPrincipalRegistryStore(self._authority)
        principal_resolution = registry.resolve_canonical_principal(self.principal_id)
        credential_resolution = registry.resolve_canonical_credential(self.credential_id)
        if principal_resolution is None or getattr(principal_resolution.record, "status", None) != "active":
            raise PawaError("operation_scope_invalid", "bound principal is unresolvable or not active")
        if credential_resolution is None or getattr(credential_resolution.record, "status", None) != "active":
            raise PawaError("operation_scope_invalid", "bound credential is unresolvable or not active")
        if credential_resolution.record.principal_id != self.principal_id:
            raise PawaError("operation_scope_invalid", "bound credential is not bound to the bound principal")
        return principal_resolution.record, credential_resolution.record

    def read_credential_sidecar_and_counter(self):
        """The bound credential's RHAMP FIDO2-credential sidecar record and
        its **current** counter-state record, read only — no counter
        transition. Returns plain records."""

        self._check_live()
        from pcae.core.hpac_rhamp_credential_sidecar import HpacRhampCredentialSidecarStore
        from pcae.core.hpac_rhamp_counter_state import HpacRhampCounterStateStore

        sidecar_resolution = HpacRhampCredentialSidecarStore(self._authority).resolve_canonical(self.credential_id)
        if sidecar_resolution is None:
            raise PawaError("operation_scope_invalid", "no RHAMP sidecar for the bound credential")
        counter_resolution = HpacRhampCounterStateStore(self._authority).resolve_canonical(self.credential_id)
        return sidecar_resolution.record, counter_resolution.record

    def read_presentation_state(
        self,
        *,
        mechanism_id: str,
        presentation_id: Optional[str] = None,
        presentation_digest: Optional[str] = None,
    ):
        """The current-generation protected-presentation installation
        record, the HPAC-REQ-090 mechanism descriptor, and — when a prior
        ``(presentation_id, presentation_digest)`` is supplied — the
        trusted-approval-presentation record it names. No arbitrary
        installation enumeration, no unrelated mechanism, no unrelated
        presentation."""

        self._check_live()
        if not isinstance(mechanism_id, str) or not mechanism_id.strip():
            raise PawaError("operation_scope_invalid", "mechanism_id must be a non-empty string")
        from pcae.core.approval_presentation import (
            PresentationMechanismDescriptorStore,
            TrustedApprovalPresentationStore,
        )
        from pcae.core.protected_presentation_installation import ProtectedPresentationInstallationStore

        descriptor_store = PresentationMechanismDescriptorStore(self._authority)
        descriptor_resolution = descriptor_store.resolve_canonical(mechanism_id)
        installation = ProtectedPresentationInstallationStore(self._authority).resolve_current_generation()
        presentation = None
        if presentation_id is not None or presentation_digest is not None:
            if not isinstance(presentation_id, str) or not isinstance(presentation_digest, str):
                raise PawaError("operation_scope_invalid", "presentation_id / presentation_digest must both be strings")
            presentation_resolution = TrustedApprovalPresentationStore(self._authority).resolve_canonical(
                presentation_id=presentation_id,
                presentation_digest=presentation_digest,
                descriptor_store=descriptor_store,
            )
            presentation = presentation_resolution.record if presentation_resolution is not None else None
        return (
            descriptor_resolution.record if descriptor_resolution is not None else None,
            installation,
            presentation,
        )

    # ── §42D one bounded ceremony-entry hand-off (HPAC-PAWA-REQ-285) ─────

    def enter_ceremony(
        self,
        *,
        approval_id: str,
        challenge_id: str,
        canonical_subject: object,
        human_visible_facts: dict,
        invocation_id: str,
        attempt_id: str,
        presented_at: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> object:
        """Hand the wrapped recognized authority to the **existing**
        ``run_protected_presentation_ceremony`` production boundary for
        **exactly one** protected-presentation ceremony in this bound
        session. Does not itself manufacture, seal, or persist presentation
        evidence (the existing ``mint_protected_presentation_evidence_writer``
        path remains the sole author, unchanged). Ceremony entry authority
        ≠ human APPROVE/REJECT ≠ FIDO2 assurance (§68B). This method exposes
        no test-decision-directive parameter of its own — a production API
        seam-free by construction (§40 of the phase prompt); tests observe
        this path by monkeypatching the imported production reference, not
        by injecting a seam.

        A second call — for this handle, in this process — fails closed
        with ``capability_stale``, spent at the point of entry regardless
        of the ceremony's own outcome (mirrors ``CertificationWriterHandle
        .consume``)."""

        self._check_live()
        self._ceremony_consumed = True

        from pcae.core import protected_presentation as _pp

        kwargs = dict(
            authority=self._authority,
            approval_id=approval_id,
            challenge_id=challenge_id,
            canonical_subject=canonical_subject,
            human_visible_facts=human_visible_facts,
            principal_id=self.principal_id,
            invocation_id=invocation_id,
            attempt_id=attempt_id,
        )
        if presented_at is not None:
            kwargs["presented_at"] = presented_at
        if timeout_seconds is not None:
            kwargs["timeout_seconds"] = timeout_seconds
        return _pp.run_protected_presentation_ceremony(**kwargs)


def recognized_certification_read_authority(
    *,
    certification_session_id: str,
    principal_id: str,
    credential_id: str,
    proof_id: str,
    _protected_root: Optional[Path] = None,
    _configured_agent_identity_source=None,
    _topology_probe: Optional["TopologyProbe"] = None,
    _caller_module: Optional[str] = None,
) -> CertificationReadAuthority:
    """§33B (HPAC-PAWA-REQ-276..280) — obtain exactly one process-local,
    single-ceremony-entry, restart-dead ``CertificationReadAuthority`` after
    a fresh, complete §33 recognition sequence (steps 1-9 verbatim, reusing
    the §33/§33A machinery) plus the §33B-specific consumer-restatement /
    configured-agent-bind / session-binding / construction / audit steps.

    Runs fresh on **every** call — no result is cached (HPAC-PAWA-REQ-279).
    Grants **no** ``HPACWriterCapability`` and no write authority of any
    kind (HPAC-PAWA-REQ-284/287). Fails closed on any conjunct failure —
    the corresponding §42E code; no read authority is returned
    (HPAC-PAWA-REQ-280).

    ``_protected_root`` / ``_configured_agent_identity_source`` /
    ``_topology_probe`` / ``_caller_module`` are the disclosed test-only
    seams (§72/§73 / HPAC-PAWA-REQ-166); a guard test asserts no non-test
    module passes any of them and that the only production caller is the
    §38B consumer.
    """

    caller_module = _detect_caller_module(_caller_module)
    sid, pid, cid, pf = _validate_read_authority_inputs(
        certification_session_id, principal_id, credential_id, proof_id
    )

    recognized = _run_recognition_sequence(
        protected_root=_protected_root,
        configured_agent_identity_source=_configured_agent_identity_source,
        caller_module=caller_module,
        topology_probe=_topology_probe,
        authorized_consumers=READ_AUTHORITY_CONSUMERS,
        test_consumers=_READ_AUTHORITY_TEST_CONSUMERS,
    )

    # HPAC-PAWA-REQ-278.1 — restate the exact §38B consumer check
    # explicitly (defence in depth; step 9 above already enforced it).
    if caller_module not in READ_AUTHORITY_CONSUMERS and caller_module not in _READ_AUTHORITY_TEST_CONSUMERS:
        raise PawaError("unauthorized_factory_consumer", f"{caller_module!r} is not the §38B read-authority consumer")

    # HPAC-PAWA-REQ-278.3 (F-5-B1 repair) — bind the configured-agent
    # identity BEFORE the first protected-store canonical read, so every
    # subsequent ``_validate_production_boundary`` on this instance keys
    # the negative boundary off the CONFIGURED AGENT, not the invoking
    # (sudo/root) process.
    recognized.authority._bind_configured_agent_identity(
        (recognized.configured_agent.uid, recognized.configured_agent.gids),
        _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL,
    )

    # HPAC-PAWA-REQ-278.2 — certification-session context binding, now
    # evaluated on the freshly-bound authority via provenance-verified
    # canonical reads (the exact repair proof: this call denies on an
    # unbound authority under ambient root, and succeeds here).
    _validate_read_authority_session_binding(recognized.authority, principal_id=pid, credential_id=cid)

    handle = CertificationReadAuthority(
        _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL,
        authority=recognized.authority,
        certification_session_id=sid,
        principal_id=pid,
        credential_id=cid,
        proof_id=pf,
        anchor_id=recognized.anchor_id,
        installation_id=recognized.installation_id,
        descriptor_generation=recognized.generation,
    )

    operation_id = new_operation_id()
    # §42D / HPAC-PAWA-REQ-290 — the issuance audit event. Non-authoritative
    # facts only (never the seal, never anything a working authority could
    # be reconstructed from). No new schema; the existing
    # HPAC-PAWA-ISSUANCE-EVIDENCE/1.0 operation / context_annotation fields
    # carry them.
    _record_issuance_evidence(
        recognized.root,
        operation_id=operation_id,
        operation="certification_read_authority",
        anchor_id=recognized.anchor_id,
        installation_id=recognized.installation_id,
        descriptor_generation=recognized.generation,
        protected_root_identity=recognized.live_root_identity,
        target_principal_id=pid,
        target_credential_id=cid,
        enrollment_transaction_id=None,
        result="issued",
        capability_identifier="hpaw-readauth-" + hashlib.sha256((sid + pf).encode()).hexdigest()[:32],
        context_annotation=f"certification_session={sid};proof_id={pf};phase=read_authority_issue",
    )
    return handle
