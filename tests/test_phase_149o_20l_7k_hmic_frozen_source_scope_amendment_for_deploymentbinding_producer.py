"""Phase 149O.20L.7K -- HMIC Frozen Source-Scope Amendment for the
DeploymentBinding Producer.

Closes 149O.20L.7J's own named, non-blocking finding (7J §31): neither
`src/pcae/core/hatp_deployment_binding_admin.py` nor `scripts/hatp_
deployment_binding_admin.py` was, before this phase, a member of
HMIC-001's frozen authority-bearing file set, despite the directly
analogous `scripts/hatp_certification_admin.py` already being bound.
HMIC-001 is amended v1.3 -> v1.4 (contract §55): HMIC-REQ-052 limb (c)
widened with a third, non-call-graph anchor; HMIC-REQ-050 widened from
28 to 30 entries. `src/pcae/core/hatp_mandatory_certification.py`'s
`_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_
FILES` are realigned to the new 30-file set in this same phase (unlike
149O.20K's split contract-then-alignment sequencing).

This is SOURCE-SCOPE AMENDMENT ONLY. It does not change DeploymentBinding
producer semantics, does not create a RepositoryIdentity or
DeploymentBinding, does not touch Dell, does not initiate first-use
election, does not certify, and does not activate. See contract §55 and
`docs/PHASE_149O_20L_7K_...md` for the full phase record.

Covers:
  * exact production/contract 30-file set equality, independently
    extracted from the live contract text;
  * exact +2 delta against this phase's own entry commit; the
    pre-amendment 28 files remain a strict subset;
  * per-new-file digest sensitivity, exercised individually against the
    real digest-generation mechanism;
  * missing-new-file fail-closed behavior, individually, for each of
    the two new files;
  * non-member control (a disposable file's mutation does not affect
    the digest);
  * path uniqueness/normalization/existence checks over the full
    30-file set;
  * HBDC-001/`contract_versions` (5-member) preservation;
  * B-149O.19.3-1/B-149O.20D-1/CBV-S1 (three Class-B verifier files)
    regression;
  * producer and admin-script byte-identity across this phase;
  * attack-matrix row count (39) and version-header (v1.4) checks.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_HBDC_CONTRACT_PATH = _CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_PRODUCER_PATH = _SRC / "core" / "hatp_deployment_binding_admin.py"
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_deployment_binding_admin.py"
_CERT_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"

#: This phase's own entry commit -- 149O.20L.7J's own finalization commit.
#: Production still implemented the pre-amendment 28-file set at this
#: commit; the contract still declared v1.3.
_PHASE_ENTRY_COMMIT = "6f7073ce"

_NEW_MEMBER_RELATIVE_PATHS = (
    "src/pcae/core/hatp_deployment_binding_admin.py",
    "scripts/hatp_deployment_binding_admin.py",
)

_THREE_CLASS_B_VERIFIER_RELATIVE_PATHS = (
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
    "src/pcae/core/hatp_class_b_conformance.py",
)

_FOUR_PROVIDER_RELATIVE_PATHS = (
    "src/pcae/core/hatp_providers.py",
    "src/pcae/core/hatp_fido2_provider.py",
    "src/pcae/core/hatp_piv_provider.py",
    "src/pcae/core/hatp_hardware_credentials.py",
)


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract_req_050_block(contract_text: str) -> "tuple[str, ...]":
    match = re.search(r"HMIC-REQ-050 \(Exact Enumeration.*?```\n(.*?)```", contract_text, re.S)
    assert match is not None, "HMIC-REQ-050 fenced enumeration block not found in contract text"
    lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    return tuple(lines)


def _live_contract_30_canonical_paths() -> "list[str]":
    contract_text = _CONTRACT_PATH.read_text(encoding="utf-8")
    entries = _extract_req_050_block(contract_text)
    assert len(entries) == 30
    canonical = []
    for entry in entries:
        # Strip trailing "(XYZ-001)" contract-id annotation if present.
        path = entry.split()[0]
        if (_SRC / path).is_file():
            canonical.append(f"src/pcae/{path}")
        else:
            canonical.append(path)
    return canonical


def _production_frozen_paths():
    import importlib
    import pcae.core.hatp_mandatory_certification as m

    importlib.reload(m)
    return list(m._frozen_canonical_paths())


# ═══════════════════════════════════════════════════════════════════════════
# 1. Exact production/contract 30-file set equality
# ═══════════════════════════════════════════════════════════════════════════


def test_live_contract_req_050_enumeration_is_exactly_30_entries():
    entries = _extract_req_050_block(_CONTRACT_PATH.read_text(encoding="utf-8"))
    assert len(entries) == 30


def test_production_frozen_set_exactly_equals_live_contract_30_file_set():
    contract_paths = set(_live_contract_30_canonical_paths())
    production_paths = set(_production_frozen_paths())
    assert len(contract_paths) == 30
    assert len(production_paths) == 30
    assert contract_paths == production_paths


def test_production_frozen_set_count_assertion_is_exactly_30():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", source)
    assert match is not None
    assert match.group(1) == "30"
    assert ">= 30" not in source
    assert ">=30" not in source


def test_both_new_members_present_in_production_and_contract():
    contract_paths = set(_live_contract_30_canonical_paths())
    production_paths = set(_production_frozen_paths())
    for relative in _NEW_MEMBER_RELATIVE_PATHS:
        assert relative in contract_paths, relative
        assert relative in production_paths, relative


# ═══════════════════════════════════════════════════════════════════════════
# 2. Exact +2 delta; pre-amendment 28 remain a strict subset
# ═══════════════════════════════════════════════════════════════════════════


def test_exact_two_entry_delta_between_pre_7k_and_current_frozen_sets():
    pre_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    ns: dict = {}
    exec(compile(pre_source, "<pre-7k hatp_mandatory_certification.py>", "exec"), ns)  # noqa: S102
    pre_src_files = tuple(ns["_FROZEN_SRC_PCAE_RELATIVE_FILES"])
    pre_root_files = tuple(ns["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"])
    pre_set = {f"src/pcae/{p}" for p in pre_src_files} | set(pre_root_files)
    assert len(pre_set) == 28

    current_set = set(_production_frozen_paths())
    assert len(current_set) == 30
    assert pre_set <= current_set
    added = current_set - pre_set
    assert added == set(_NEW_MEMBER_RELATIVE_PATHS)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Per-new-file digest sensitivity (real mechanism, disposable copies)
# ═══════════════════════════════════════════════════════════════════════════


def _current_digest():
    from pcae.core import hatp_mandatory_certification as m
    from pcae.core.paths import HarnessPath

    return m.derive_implementation_scope_digest(HarnessPath.cwd())


@pytest.mark.parametrize("relative_path", _NEW_MEMBER_RELATIVE_PATHS)
def test_new_member_byte_perturbation_changes_digest(relative_path):
    target = _REPO_ROOT / relative_path
    original = target.read_bytes()
    baseline = _current_digest()
    try:
        target.write_bytes(original + b"\n# 7k-digest-sensitivity-probe\n")
        perturbed = _current_digest()
        assert perturbed != baseline
    finally:
        target.write_bytes(original)
    assert _current_digest() == baseline


@pytest.mark.parametrize("relative_path", _NEW_MEMBER_RELATIVE_PATHS)
def test_new_member_missing_file_fails_closed(relative_path):
    target = _REPO_ROOT / relative_path
    original = target.read_bytes()
    try:
        target.unlink()
        with pytest.raises(Exception):
            _current_digest()
    finally:
        target.write_bytes(original)
    assert _current_digest() == _current_digest()


def test_non_member_control_perturbation_does_not_change_digest():
    target = _SRC / "core" / "paths.py"
    original = target.read_bytes()
    baseline = _current_digest()
    try:
        target.write_bytes(original + b"\n# 7k-non-member-control-probe\n")
        perturbed = _current_digest()
        assert perturbed == baseline
    finally:
        target.write_bytes(original)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Path uniqueness / normalization / existence over the full 30-file set
# ═══════════════════════════════════════════════════════════════════════════


def test_all_30_frozen_paths_exist_are_regular_and_not_symlinked():
    paths = _production_frozen_paths()
    assert len(paths) == 30
    for relative in paths:
        full = _REPO_ROOT / relative
        assert full.is_file(), relative
        assert not full.is_symlink(), relative


def test_no_duplicate_frozen_paths():
    paths = _production_frozen_paths()
    assert len(paths) == len(set(paths))


def test_no_unsafe_path_segments():
    for relative in _production_frozen_paths():
        assert not relative.startswith("/"), relative
        assert "\\" not in relative, relative
        segments = relative.split("/")
        assert all(segment not in ("", ".", "..") for segment in segments), relative


# ═══════════════════════════════════════════════════════════════════════════
# 5. HBDC-001 / contract_versions (5-member) preservation
# ═══════════════════════════════════════════════════════════════════════════


def test_hbdc_still_participates_in_contract_versions_and_frozen_set():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in source
    from pcae.core import hatp_mandatory_certification as m

    assert len(m._CONTRACT_IDENTITY_FILES) == 5
    ids = {contract_id for contract_id, _ in m._CONTRACT_IDENTITY_FILES}
    assert ids == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"}


def test_hbdc_contract_byte_unchanged_since_phase_entry():
    pre = _git_show(_PHASE_ENTRY_COMMIT, "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
    current = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
    assert pre == current


# ═══════════════════════════════════════════════════════════════════════════
# 6. B-149O.19.3-1 / B-149O.20D-1 / CBV-S1 regression
# ═══════════════════════════════════════════════════════════════════════════


def test_four_provider_files_still_frozen():
    production_paths = set(_production_frozen_paths())
    for relative in _FOUR_PROVIDER_RELATIVE_PATHS:
        assert relative in production_paths, relative


def test_three_class_b_verifier_files_still_frozen_and_byte_unchanged():
    production_paths = set(_production_frozen_paths())
    for relative in _THREE_CLASS_B_VERIFIER_RELATIVE_PATHS:
        assert relative in production_paths, relative
        pre = _git_show(_PHASE_ENTRY_COMMIT, relative)
        current = (_REPO_ROOT / relative).read_text(encoding="utf-8")
        assert pre == current, relative


# ═══════════════════════════════════════════════════════════════════════════
# 7. Producer and admin-script byte-identity across this phase
# ═══════════════════════════════════════════════════════════════════════════


def test_producer_and_admin_script_byte_identical_since_phase_entry():
    for relative in _NEW_MEMBER_RELATIVE_PATHS:
        pre = _git_show(_PHASE_ENTRY_COMMIT, relative)
        current = (_REPO_ROOT / relative).read_text(encoding="utf-8")
        assert pre == current, relative


def test_certification_admin_script_untouched_since_phase_entry():
    pre = _git_show(_PHASE_ENTRY_COMMIT, "scripts/hatp_certification_admin.py")
    current = _CERT_ADMIN_SCRIPT_PATH.read_text(encoding="utf-8")
    assert pre == current


# ═══════════════════════════════════════════════════════════════════════════
# 8. Attack matrix / version-header checks
# ═══════════════════════════════════════════════════════════════════════════


def test_contract_declares_v1_4_pending_independent_verification():
    text = _CONTRACT_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.4" in text
    assert "not VERIFIED at v1.4" in text


def test_attack_matrix_declares_39_scenarios():
    text = _CONTRACT_PATH.read_text(encoding="utf-8")
    assert "Full Mandatory Attack Matrix (39 Scenarios)" in text
    assert re.search(r"^\| 39 ", text, re.M) is not None


def test_hmic_module_docstring_and_comments_name_30_files_v1_4():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    assert "30-path\nenumeration, v1.4" in source
    assert "30-path tuple" in source
    assert "28-path" not in source
    assert re.search(r"30-entry literal enumeration \(v1\.4", source)


# ═══════════════════════════════════════════════════════════════════════════
# 9. Zero real DeploymentBinding / RepositoryIdentity / Dell footprint
# ═══════════════════════════════════════════════════════════════════════════


def test_no_real_repository_identity_in_this_repositorys_own_working_tree():
    assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()


def test_no_real_registry_json_created_under_a_production_looking_path():
    assert not (_REPO_ROOT / ".pcae" / "registry.json").exists()
