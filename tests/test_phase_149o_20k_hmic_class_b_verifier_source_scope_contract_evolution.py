"""Phase 149O.20K -- HMIC Class-B Verifier Source-Scope Contract Evolution
(`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
§53; phase document
`docs/PHASE_149O_20K_HMIC_CLASS_B_VERIFIER_SOURCE_SCOPE_CONTRACT_EVOLUTION.md`).

This is a CONTRACT-EVOLUTION-ONLY phase, addressing CBV-S1: it modifies
no `src/pcae/**` file, no `scripts/**` file, and no other bound contract
(HMRC-001/HATP-001/HSCE-001/RAE-001/HBDC-001). It widens HMIC-001 from
v1.2 to v1.3, adding a new closure limb (c) to HMIC-REQ-052 and widening
HMIC-REQ-050's frozen enumeration from twenty-five to twenty-eight files
by naming the three Class-B deployment-conformance verifier modules
(`hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`,
`hatp_class_b_conformance.py`) -- derived from a fresh AST/import
dependency walk of the current source tree, not assumed.

This module independently re-verifies, by direct document/source
inspection (never trusting this phase's own prose):

  * the contract declares HMIC-001 v1.3;
  * HMIC-REQ-050's fenced enumeration has exactly 28 entries, matching
    the pre-amendment 25 plus exactly the three Class-B verifier paths;
  * HMIC-REQ-052 now contains limb (c), naming
    `verify_class_b_deployment_conformance` as the anchor call graph;
  * the attack matrix now has 38 rows, with a new "not yet operative"
    row 38 for the Class-B verifier;
  * production's `_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_
    FILES` remain the pre-amendment 25/5 sets -- contract-ahead-of-
    production divergence, intentional and disclosed;
  * the three Class-B verifier modules, HBDC-001, and every other
    pre-existing bound contract are byte-unchanged working-tree files;
  * no `src/pcae/**` or `scripts/**` file is dirty in the working tree;
  * zero production consumers of the three Class-B verifier modules
    exist (re-derived independently, not merely asserted);
  * no import cycle is introduced between the Class-B verifier island
    and `hatp_mandatory_certification.py`/`hatp_certification_admin.py`;
  * CBV-S1 is restated OPEN, not closed, by this amendment;
  * no real certification/binding/revocation artifact exists anywhere
    in the repository.
"""
from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")
_HBDC_CONTRACT_PATH = _CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"

_CLASS_B_VERIFIER_MODULES = (
    "hatp_class_b_topology_verifier.py",
    "hatp_environment_lock_verifier.py",
    "hatp_class_b_conformance.py",
)

_EXISTING_FOUR_BOUND_CONTRACTS = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
)

#: Pre-amendment (v1.2) 25-file enumeration this phase widens from.
_PRE_AMENDMENT_25_FROZEN_PATHS = (
    "src/pcae/core/hatp_mandatory_cutover.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/hatp_rollback_consumption.py",
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/repository_identity.py",
    "src/pcae/core/rollback_approval_evidence.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/agent.py",
    "src/pcae/commands/agent.py",
    "src/pcae/cli.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/hatp_providers.py",
    "src/pcae/core/hatp_fido2_provider.py",
    "src/pcae/core/hatp_piv_provider.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/hatp_mandatory_certification.py",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
    "scripts/hatp_certification_admin.py",
)

#: Current, post-149O.20K enumeration (28 files): the three new entries
#: are src/pcae/-relative, appended after the pre-existing 19 src/pcae/
#: entries and before the six repository-root-relative entries, matching
#: HMIC-REQ-050's own presentation order.
_CURRENT_28_FROZEN_PATHS = _PRE_AMENDMENT_25_FROZEN_PATHS[:19] + (
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
    "src/pcae/core/hatp_class_b_conformance.py",
) + _PRE_AMENDMENT_25_FROZEN_PATHS[19:]


def _extract_req_050_paths() -> "list[str]":
    marker = "HMIC-REQ-050 (Exact Enumeration"
    start = _CONTRACT_TEXT.index(marker)
    fence_start = _CONTRACT_TEXT.index("```", start)
    fence_end = _CONTRACT_TEXT.index("```", fence_start + 3)
    block = _CONTRACT_TEXT[fence_start + 3 : fence_end]
    return [ln.strip() for ln in block.splitlines() if ln.strip()]


def _extracted_bare_paths() -> "list[str]":
    return [re.sub(r"\s+\([A-Z0-9-]+\)\s*$", "", ln).strip() for ln in _extract_req_050_paths()]


# ---------------------------------------------------------------------------
# Version identity
# ---------------------------------------------------------------------------


def test_contract_version_is_v1_3():
    assert "**Contract ID:** HMIC-001" in _CONTRACT_TEXT
    assert "**Version:** 1.3" in _CONTRACT_TEXT


def test_status_line_declares_pending_independent_verification_not_verified():
    idx = _CONTRACT_TEXT.index("**Status:**")
    line = _CONTRACT_TEXT[idx : _CONTRACT_TEXT.index("\n", idx)]
    assert "CLASS-B VERIFIER SOURCE-SCOPE CLOSURE EVOLVED" in line
    assert "PENDING INDEPENDENT VERIFICATION" in line
    assert "not VERIFIED at v1.3" in line


def test_amended_by_line_names_this_phase():
    assert "**Amended by:** Phase 149O.20K" in _CONTRACT_TEXT


# ---------------------------------------------------------------------------
# HMIC-REQ-050 widened to exactly 28 entries
# ---------------------------------------------------------------------------


def test_frozen_file_set_now_has_exactly_28_entries():
    extracted = _extract_req_050_paths()
    assert len(extracted) == 28, f"expected 28 lines in HMIC-REQ-050's fenced block, found {len(extracted)}: {extracted}"


def test_frozen_file_set_matches_current_28_file_enumeration():
    bare = _extracted_bare_paths()
    src_relative = [p for p in bare if not p.startswith("docs/") and not p.startswith("scripts/")]
    others = [p for p in bare if p.startswith("docs/") or p.startswith("scripts/")]
    reconstructed = [f"src/pcae/{p}" for p in src_relative] + others
    assert sorted(reconstructed) == sorted(_CURRENT_28_FROZEN_PATHS)


@pytest.mark.parametrize("module_name", _CLASS_B_VERIFIER_MODULES)
def test_class_b_verifier_module_present_in_frozen_enumeration(module_name):
    bare = set(_extracted_bare_paths())
    assert f"core/{module_name}" in bare


def test_pre_amendment_25_set_did_not_include_class_b_verifiers():
    for module_name in _CLASS_B_VERIFIER_MODULES:
        assert f"src/pcae/core/{module_name}" not in _PRE_AMENDMENT_25_FROZEN_PATHS


# ---------------------------------------------------------------------------
# HMIC-REQ-052 widened with new limb (c)
# ---------------------------------------------------------------------------


def test_hmic_req_052_contains_new_limb_c():
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-052")
    section_end = _CONTRACT_TEXT.index("A file SHALL NOT be added merely")
    text = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "(c)" in text
    assert "added v1.3, §53" in text
    assert "verify_class_b_deployment_conformance" in text


def test_hmic_req_052_limb_c_names_anticipatory_zero_consumer_state():
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-052")
    section_end = _CONTRACT_TEXT.index("A file SHALL NOT be added merely")
    text = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "anticipatory" in text.lower()
    assert "zero production consumers" in text.lower() or "no readiness" in text.lower()


def test_hmic_req_052_union_derivation_names_five_sources():
    section_start = _CONTRACT_TEXT.index("This enumeration is derived as the union of")
    section_end = _CONTRACT_TEXT.index("**HMIC-REQ-053")
    text = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "(e) Phase 149O.20K" in text
    assert "hatp_class_b_topology_verifier.py" in text
    assert "hatp_environment_lock_verifier.py" in text
    assert "hatp_class_b_conformance.py" in text
    assert "All five sources are now" in text


# ---------------------------------------------------------------------------
# Attack matrix widened to 38 scenarios
# ---------------------------------------------------------------------------


def test_attack_matrix_heading_declares_38_scenarios():
    assert "## 41. Full Mandatory Attack Matrix (38 Scenarios)" in _CONTRACT_TEXT


def _attack_matrix_table_text() -> str:
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    return _CONTRACT_TEXT[table_start:table_end]


def test_attack_matrix_has_exactly_38_rows_sequential():
    table = _attack_matrix_table_text()
    rows = re.findall(r"^\| ([0-9]+) ", table, flags=re.MULTILINE)
    assert [int(r) for r in rows] == list(range(1, 39))


def test_attack_row_38_present_and_named():
    table = _attack_matrix_table_text()
    row_38 = next(line for line in table.splitlines() if line.startswith("| 38 "))
    assert "Class-B verifier" in row_38
    assert "IMPLEMENTATION_MISMATCH" in row_38
    assert "not yet operative" in row_38.lower()
    assert "zero production consumers" in row_38.lower()


# ---------------------------------------------------------------------------
# §53 amendment-history section present, self-consistent
# ---------------------------------------------------------------------------


def test_history_section_53_present_and_after_section_52():
    idx_52 = _CONTRACT_TEXT.index("## 52. Contract Repair History")
    idx_53 = _CONTRACT_TEXT.index("## 53. Contract Amendment History")
    assert idx_53 > idx_52


def test_cbv_s1_restated_open_not_closed():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 53. Contract Amendment History") :]
    assert "CBV-S1: OPEN" in section
    assert "NOT CLOSED" in section


def test_cbv_s10_untouched_reference_present():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 53. Contract Amendment History") :]
    assert "CBV-S10" in section
    assert "untouched" in section.lower()


def test_no_hbdc_amendment_expectation_restated():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 53. Contract Amendment History") :]
    text = " ".join(section.split())
    assert "unchanged by this phase" in text
    assert "HBDC-001" in text


def test_recommended_next_phase_is_149o_20k_1_not_production_alignment():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 53. Contract Amendment History") :]
    assert "149O.20K.1" in section
    assert "does not authorize production alignment or readiness integration" in " ".join(section.split())


def test_w1_and_prior_findings_not_reopened():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 53. Contract Amendment History") :]
    text = " ".join(section.split())
    assert "W-1" in text and "not reopened" in text
    assert "B-149O.19.3-1" in text
    assert "B-149O.20D-1" in text


def test_pcae_core_paths_exclusion_reasoning_present():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 53. Contract Amendment History") :]
    assert "pcae.core.paths" in section
    assert "Category B" in section


def test_cycle_analysis_present_and_concludes_no_cycle():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 53. Contract Amendment History") :]
    text = " ".join(section.split())
    assert "literal duplicate" in text.lower() or "not an import" in text.lower()
    assert "no cycle exists" in text.lower() or "no cycle is introduced" in text.lower()


# ---------------------------------------------------------------------------
# Fresh, independent zero-consumer / no-cycle re-derivation directly from
# current source (does not merely trust the contract's own prose above)
# ---------------------------------------------------------------------------


def _class_b_module_source(module_name: str) -> str:
    return (_SRC / "core" / module_name).read_text(encoding="utf-8")


@pytest.mark.parametrize("module_name", _CLASS_B_VERIFIER_MODULES)
def test_class_b_verifier_module_exists_on_disk(module_name):
    assert (_SRC / "core" / module_name).is_file()


def test_zero_production_consumers_of_class_b_verifier_island():
    consumer_markers = (
        "hatp_class_b_topology_verifier",
        "hatp_environment_lock_verifier",
        "hatp_class_b_conformance",
        "verify_class_b_deployment_conformance",
    )
    for path in _SRC.rglob("*.py"):
        if path.name in _CLASS_B_VERIFIER_MODULES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in consumer_markers:
            assert marker not in text, f"unexpected Class-B verifier reference in {path}: {marker}"


def test_no_import_cycle_between_verifier_island_and_hmic_certification_module():
    cert_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    admin_source = (_REPO_ROOT / "scripts" / "hatp_certification_admin.py").read_text(encoding="utf-8")
    for module_name in _CLASS_B_VERIFIER_MODULES:
        stem = module_name[:-3]
        assert f"import {stem}" not in cert_source
        assert f"from pcae.core.{stem}" not in cert_source
        assert f"import {stem}" not in admin_source
        assert f"from pcae.core.{stem}" not in admin_source
    for module_name in _CLASS_B_VERIFIER_MODULES:
        source = _class_b_module_source(module_name)
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        assert not any("hatp_mandatory_certification" in m for m in imported_modules)
        assert not any("hatp_certification_admin" in m for m in imported_modules)


def test_class_b_verifier_pcae_owned_imports_are_bounded():
    """Independent re-derivation of §53.3's AST walk: every PCAE-owned
    import reached from the three verifier modules is either a sibling
    verifier module or already a pre-amendment HMIC-REQ-050 member
    (`hatp_bootstrap`, `repository_identity`) or the disclosed excluded
    dependency (`pcae.core.paths`)."""
    allowed_pcae_targets = {
        "pcae.core.hatp_bootstrap",
        "pcae.core.hatp_class_b_topology_verifier",
        "pcae.core.hatp_environment_lock_verifier",
        "pcae.core.repository_identity",
        "pcae.core.paths",
    }
    allowed_from_pcae_core_names = {"hatp_bootstrap", "repository_identity"}
    for module_name in _CLASS_B_VERIFIER_MODULES:
        tree = ast.parse(_class_b_module_source(module_name))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("pcae"):
                if node.module == "pcae.core":
                    for alias in node.names:
                        assert alias.name in allowed_from_pcae_core_names, (
                            f"unexpected PCAE-owned import in {module_name}: from pcae.core import {alias.name}"
                        )
                else:
                    assert node.module in allowed_pcae_targets, f"unexpected PCAE-owned import in {module_name}: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("pcae"):
                        assert alias.name in allowed_pcae_targets, f"unexpected PCAE-owned import in {module_name}: {alias.name}"


# ---------------------------------------------------------------------------
# HBDC-001 itself, and every other pre-existing bound contract, unchanged
# ---------------------------------------------------------------------------


def test_hbdc_contract_still_declares_v1_0():
    hbdc_text = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.0" in hbdc_text
    assert "**Contract:** HBDC-001" in hbdc_text


@pytest.mark.parametrize("existing_contract", _EXISTING_FOUR_BOUND_CONTRACTS)
def test_other_bound_contracts_clean_in_working_tree(existing_contract):
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", existing_contract],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
        )
    except Exception:
        pytest.skip("git unavailable in this environment")
    if proc.returncode != 0:
        pytest.skip("not a git checkout")
    assert proc.stdout.strip() == "", f"unexpected modification to {existing_contract}: {proc.stdout}"


def test_hbdc_contract_itself_clean_in_working_tree():
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
        )
    except Exception:
        pytest.skip("git unavailable in this environment")
    if proc.returncode != 0:
        pytest.skip("not a git checkout")
    assert proc.stdout.strip() == "", f"unexpected modification to HBDC-001: {proc.stdout}"


# ---------------------------------------------------------------------------
# No production source touched; production identity still pre-amendment 25/5
# ---------------------------------------------------------------------------


def test_no_src_pcae_files_dirty_in_working_tree():
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", "src/pcae"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
        )
    except Exception:
        pytest.skip("git unavailable in this environment")
    if proc.returncode != 0:
        pytest.skip("not a git checkout")
    assert proc.stdout.strip() == "", f"production source dirty during a contract-only phase: {proc.stdout}"


def test_no_scripts_files_dirty_in_working_tree():
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", "scripts"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
        )
    except Exception:
        pytest.skip("git unavailable in this environment")
    if proc.returncode != 0:
        pytest.skip("not a git checkout")
    assert proc.stdout.strip() == "", f"scripts/ dirty during a contract-only phase: {proc.stdout}"


def test_production_frozen_file_count_still_25():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 25" in source
    for module_name in _CLASS_B_VERIFIER_MODULES:
        assert f'"core/{module_name}"' not in source


def test_production_contract_identity_files_still_five_pre_existing():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    match = re.search(r"_CONTRACT_IDENTITY_FILES:.*?=\s*\(\s*(.*?)\n\)", source, re.DOTALL)
    assert match, "could not locate _CONTRACT_IDENTITY_FILES in hatp_mandatory_certification.py"
    body = match.group(1)
    ids = re.findall(r'\("([A-Z0-9-]+)",', body)
    assert ids == ["HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"]


# ---------------------------------------------------------------------------
# No real certification state anywhere in the repository
# ---------------------------------------------------------------------------


def test_no_certification_state_artifacts_exist():
    for name in ("certifications.json", "certification-bindings.json", "active_certification.json"):
        hits = [h for h in _REPO_ROOT.rglob(name) if ".git" not in h.parts and ".venv" not in h.parts]
        assert hits == []
