"""Phase 149O.20L.7O.2G.1 -- HMIC Trust-Enrollment / Signing Target-Set
Reconciliation.

Mechanically re-validates the reconciliation in `docs/PHASE_149O_20L_7O_
2G_1_HMIC_TRUST_ENROLLMENT_SIGNING_TARGET_SET_RECONCILIATION.md`: 2G's
own report recommended binding both content and version for HPSE-001/
HHCE-001 (mirroring the HBDC-001 precedent) but its total future
source/content-set arithmetic (30 -> 33) only reflected the 3 new
Python source files, omitting the 2 new contract-content files its own
recommendation requires. This phase corrects the arithmetic to 30 -> 35
and re-derives the full future membership, without modifying any
production HMIC constant.

No production change (as of 149O.20L.7O.2G.1 itself). No signing,
enrollment, or certification code path is exercised for a decision --
only static analysis, constant comparison, and file-existence/header
checks.

Superseded-by note: Phase 149O.20L.7O.2H (v1.4 -> v1.5) is this
reconciliation's own implementing successor -- it amended HMIC-001 and
aligned production to exactly the 35-file/7-contract target this module
derived. Several assertions below therefore now read against the
CURRENT (post-2H) production state rather than the pre-2H "not yet
bound" state this file originally asserted -- this file's enduring
value is proving 2H implemented exactly the reconciled target, not
merely that the target was correctly derived pre-implementation.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from pcae.core import hatp_mandatory_certification as hmic_impl

REPO_ROOT = Path(__file__).resolve().parent.parent

#: This phase's own phase-entry commit (Phase 149O.20L.7O.2G.1: close
#: governed task, transition to idle) -- the last commit before
#: 149O.20L.7O.2H's own production/contract amendment.
_PHASE_ENTRY_COMMIT = "e65b4ce0"


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout

_NEW_SRC_PCAE_RELATIVE = (
    "core/hatp_signing_ceremony.py",
    "core/hatp_hardware_credential_admin.py",
    "core/hatp_principal_signer_admin.py",
)

_NEW_CONTRACT_ROOT_RELATIVE = (
    "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
    "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
)

_NEW_CONTRACT_IDENTITY = (
    ("HPSE-001", "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"),
    ("HHCE-001", "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"),
)


def test_pre_2g_1_baseline_was_thirty_files_five_contracts() -> None:
    """As of 149O.20L.7O.2G.1 itself, the live baseline was exactly
    23/7/30/5; 149O.20L.7O.2H then implemented the reconciled 26/9/35/7
    target this module derives below. This historical snapshot is
    reconstructed from the fixed pre-2H entry commit, not from live
    production state, which has since moved forward."""
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    ns: dict = {}
    exec(compile(entry_source, "<pre-2H hatp_mandatory_certification.py>", "exec"), ns)  # noqa: S102
    assert len(ns["_FROZEN_SRC_PCAE_RELATIVE_FILES"]) == 23
    assert len(ns["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"]) == 7
    assert len(ns["_FROZEN_AUTHORITY_BEARING_FILES"]) == 30
    assert len(ns["_CONTRACT_IDENTITY_FILES"]) == 5


def test_every_current_contract_versions_member_is_also_content_bound() -> None:
    """HMIC-REQ-053's own current text: 'every contract_versions member
    ... receives both bindings uniformly -- no contract_versions member
    is exempted from the digest binding.' Mechanically verified against
    live production state: this is the decisive fact that forces
    content binding for any contract added to contract_versions,
    HPSE-001/HHCE-001 included."""

    current_canonical = set(hmic_impl._frozen_canonical_paths())
    for _contract_id, relative_path in hmic_impl._CONTRACT_IDENTITY_FILES:
        assert relative_path in current_canonical, (
            f"{relative_path} is a contract_versions member but is not content-bound -- "
            "contradicts HMIC-REQ-053's current uniform-coverage rule"
        )


def test_two_candidate_contracts_exist_and_are_now_bound_by_2h() -> None:
    """As of 149O.20L.7O.2G.1 these were candidates, not yet bound;
    149O.20L.7O.2H bound both (content and version)."""
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    bound_contract_paths = {path for _, path in hmic_impl._CONTRACT_IDENTITY_FILES}
    for relative in _NEW_CONTRACT_ROOT_RELATIVE:
        on_disk = REPO_ROOT / relative
        assert on_disk.is_file(), f"candidate contract missing: {relative}"
        assert relative in current_canonical, f"{relative} should be content-bound by 2H"
        assert relative in bound_contract_paths, f"{relative} should be version-bound by 2H"


def test_three_candidate_sources_exist_and_are_now_bound_by_2h() -> None:
    """As of 149O.20L.7O.2G.1 these were candidates, not yet bound;
    149O.20L.7O.2H bound all three under closure limb (d)."""
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    for relative in _NEW_SRC_PCAE_RELATIVE:
        on_disk = REPO_ROOT / "src" / "pcae" / relative
        assert on_disk.is_file(), f"candidate source missing: {relative}"
        canonical = f"src/pcae/{relative}"
        assert canonical in current_canonical, f"{relative} should be HMIC-bound by 2H"


def test_hpse_hhce_headers_parse_as_version_1_1() -> None:
    for contract_id, relative_path in _NEW_CONTRACT_IDENTITY:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        id_match = hmic_impl._CONTRACT_ID_HEADER_RE.search(text)
        version_match = hmic_impl._CONTRACT_VERSION_HEADER_RE.search(text)
        assert id_match is not None and id_match.group(1) == contract_id
        assert version_match is not None and version_match.group(1) == "1.1"


def test_reconciled_future_source_set_is_twenty_six_entries() -> None:
    """As of 149O.20L.7O.2G.1, this was a *proposed* future set
    (pre-2H current + 3 candidates); 149O.20L.7O.2H implemented it, so
    it is now simply the live production set."""
    future_src = hmic_impl._FROZEN_SRC_PCAE_RELATIVE_FILES
    assert len(future_src) == 26
    assert len(set(future_src)) == len(future_src), "duplicate entries in reconciled source set"
    for relative in future_src:
        assert (REPO_ROOT / "src" / "pcae" / relative).is_file(), f"missing on disk: {relative}"
    for relative in _NEW_SRC_PCAE_RELATIVE:
        assert relative in future_src, f"{relative} missing from implemented source set"


def test_reconciled_future_root_relative_set_is_nine_entries() -> None:
    """As of 149O.20L.7O.2G.1, this was a *proposed* future set;
    149O.20L.7O.2H implemented it, so at 2H's own exit commit
    (0893f40a) it was exactly the live production set.

    Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
    governing prompt): true at 0893f40a. Superseded for LIVE
    production state by Phase 149O.20L.7O.2M's own HMIC v1.7
    widening (9 -> 11, binding the two standalone Trust-Enrollment
    admin scripts)."""
    entry_source = _git_show("0893f40a", "src/pcae/core/hatp_mandatory_certification.py")
    ns: dict = {}
    exec(compile(entry_source, "<2H-exit hatp_mandatory_certification.py>", "exec"), ns)  # noqa: S102
    assert len(ns["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"]) == 9

    # Live production state after Phase 149O.20L.7O.2M's own widening:
    future_root = hmic_impl._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
    assert len(future_root) == 11
    assert len(set(future_root)) == len(future_root), "duplicate entries in reconciled root-relative set"
    for relative in future_root:
        assert (REPO_ROOT / relative).is_file(), f"missing on disk: {relative}"
    for relative in _NEW_CONTRACT_ROOT_RELATIVE:
        assert relative in future_root, f"{relative} missing from implemented root-relative set"


def test_reconciled_future_frozen_set_is_exactly_thirty_five_not_thirty_three() -> None:
    """The load-bearing reconciliation result. 2G's own report concluded
    (in its own text, not merely by analogy) that HPSE-001/HHCE-001
    require both content and version binding, but its total-count
    arithmetic (33) only reflected the 3 source additions. 149O.20L.7O.2H
    implemented the corrected, reconciled 35-entry figure, not 2G's
    uncorrected 33-entry figure -- this test would fail if it had not."""

    future_total = hmic_impl._FROZEN_AUTHORITY_BEARING_FILES

    assert len(future_total) == 35
    assert len(future_total) != 33, "reconciled target regressed to 2G's uncorrected source-only count"
    assert len(future_total) == len(set(future_total)), "duplicate entries in reconciled total frozen set"

    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    ns: dict = {}
    exec(compile(entry_source, "<pre-2H hatp_mandatory_certification.py>", "exec"), ns)  # noqa: S102
    pre_2h_total_count = len(ns["_FROZEN_AUTHORITY_BEARING_FILES"])
    assert pre_2h_total_count == 30
    assert len(future_total) - pre_2h_total_count == 5, "delta must be +5 (+3 source, +2 contract-content)"


def test_reconciled_future_contract_identity_set_is_seven_members() -> None:
    """As of 149O.20L.7O.2G.1, this was a *proposed* future set;
    149O.20L.7O.2H implemented it, so it is now the live production set."""
    future_identity = hmic_impl._CONTRACT_IDENTITY_FILES
    assert len(future_identity) == 7
    future_ids = {contract_id for contract_id, _ in future_identity}
    assert future_ids == {
        "HMRC-001",
        "HATP-001",
        "HSCE-001",
        "RAE-001",
        "HBDC-001",
        "HPSE-001",
        "HHCE-001",
    }
    assert len(future_ids) == len(future_identity), "duplicate contract_versions member"


def test_hsce_001_already_fully_current_unaffected_by_reconciliation() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    assert "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md" in current_canonical
    bound_ids = {c for c, _ in hmic_impl._CONTRACT_IDENTITY_FILES}
    assert "HSCE-001" in bound_ids


def test_class_b_and_deploymentbinding_members_remain_bound_unchanged() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    for relative in (
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hatp_deployment_binding_admin.py",
        "scripts/hatp_deployment_binding_admin.py",
    ):
        assert relative in current_canonical


def test_no_production_hmic_constant_modified_by_this_phase() -> None:
    """This phase (149O.20L.7O.2G.1) itself made no production change --
    reconstructed from the fixed pre-2H entry commit, since live
    production has since been aligned forward by 149O.20L.7O.2H."""
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    ns: dict = {}
    exec(compile(entry_source, "<pre-2H hatp_mandatory_certification.py>", "exec"), ns)  # noqa: S102
    assert len(ns["_FROZEN_SRC_PCAE_RELATIVE_FILES"]) == 23
    assert len(ns["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"]) == 7
    assert len(ns["_FROZEN_AUTHORITY_BEARING_FILES"]) == 30
    assert len(ns["_CONTRACT_IDENTITY_FILES"]) == 5
    contract_ids = {contract_id for contract_id, _ in ns["_CONTRACT_IDENTITY_FILES"]}
    assert contract_ids == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"}
