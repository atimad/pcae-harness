"""Phase 149O.19.5E.1 -- HMIC v1.1 Validator/Admin Implementation Identity
Contract Evolution (finding W-1,
`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
§50; phase document
`docs/PHASE_149O_19_5E_1_HMIC_V1_1_VALIDATOR_ADMIN_IMPLEMENTATION_IDENTITY_CONTRACT_EVOLUTION.md`).

This is a CONTRACT-EVOLUTION-ONLY phase: it modifies no `src/pcae/**`
file, no `scripts/**` file, and no upstream contract (HMRC-001/HATP-001/
HSCE-001/RAE-001/RWMPC-001/PBPA-001/PBPC-001). It widens HMIC-001 from
v1.0 (22-file frozen authority-bearing set) to v1.1 (24-file set, adding
`src/pcae/core/hatp_mandatory_certification.py` and
`scripts/hatp_certification_admin.py`) to resolve Stop Condition W-1 at
the contract level.

This module independently re-verifies, by direct document and source
inspection:

  * the new HMIC-REQ-050 enumeration is exactly 24 paths -- the original
    22 preserved byte-for-byte, plus exactly the two new entries;
  * every frozen path exists on disk, is a regular non-symlinked file,
    and is canonical (repository-relative, POSIX, no traversal);
  * no duplicate entries;
  * the contract's requirement/CIVC/attack-matrix inventory counts
    (144/12/34) after the amendment;
  * the contract declares HMIC-001 v1.1 and states W-1 is repaired at
    the contract level only, not closed;
  * production identity derivation is mechanically confirmed to still
    implement the pre-amendment 22-file set (expected, disclosed,
    fail-closed divergence -- not a defect this phase introduces);
  * the hard-coded readiness ceiling remains `False`;
  * zero readiness/cutover callers of the validator exist;
  * no `src/pcae/**` or `scripts/**` file was modified by this phase;
  * upstream contracts remain byte-identical.
"""
from __future__ import annotations

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
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"

#: This phase's own entry commit -- the last commit before this phase's
#: own first commit (149O.19.5E's own final commit).
_PHASE_ENTRY_COMMIT = "9ab2084a"

#: This phase's own exit commit (its final commit, also 149O.19.5E.2's
#: `_PHASE_ENTRY_COMMIT`) -- pinned rather than diffing to live "HEAD" so
#: this phase's own "did THIS phase touch src/pcae or scripts" checks keep
#: meaning what they always meant after 149O.19.5E.3 (a later phase)
#: legitimately changed `src/pcae/core/hatp_mandatory_certification.py`,
#: following the identical precedent set for
#: `test_phase_149o_19_4_hmic_implementation_plan_completeness.py`/
#: `test_phase_149o_19_5a_hmic_certification_models_canonical_parsing.py`
#: by this same phase's own commit b701234b.
_PHASE_EXIT_COMMIT = "a8282578"


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout

# ---------------------------------------------------------------------------
# Frozen file set
# ---------------------------------------------------------------------------

_ORIGINAL_22_SRC_RELATIVE_PATHS = (
    "core/hatp_mandatory_cutover.py",
    "core/hatp_ag_authority.py",
    "core/hatp_rollback_consumption.py",
    "core/hatp_bootstrap.py",
    "core/human_approval_trusted_provenance.py",
    "core/repository_identity.py",
    "core/rollback_approval_evidence.py",
    "core/hatp_evidence_store.py",
    "core/hatp_signed_evidence.py",
    "core/agent.py",
    "commands/agent.py",
    "cli.py",
    "core/permission_broker.py",
    "core/permission_broker_foundation.py",
    "core/hatp_providers.py",
    "core/hatp_fido2_provider.py",
    "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py",
)

_ORIGINAL_22_CONTRACT_RELATIVE_PATHS = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
)

_ORIGINAL_22 = _ORIGINAL_22_SRC_RELATIVE_PATHS + _ORIGINAL_22_CONTRACT_RELATIVE_PATHS

_NEW_SRC_RELATIVE_ENTRY = "core/hatp_mandatory_certification.py"
_NEW_SCRIPT_ENTRY = "scripts/hatp_certification_admin.py"


def _v1_1_repo_relative_paths() -> "tuple[str, ...]":
    src_paths = tuple(f"src/pcae/{p}" for p in _ORIGINAL_22_SRC_RELATIVE_PATHS)
    src_paths = src_paths + (f"src/pcae/{_NEW_SRC_RELATIVE_ENTRY}",)
    return src_paths + _ORIGINAL_22_CONTRACT_RELATIVE_PATHS + (_NEW_SCRIPT_ENTRY,)


# ---------------------------------------------------------------------------
# Extraction of HMIC-REQ-050's literal enumeration directly from live
# contract text, independent of any hard-coded constant above.
# ---------------------------------------------------------------------------


def _extract_req_050_paths() -> "list[str]":
    marker = "HMIC-REQ-050 (Exact Enumeration"
    start = _CONTRACT_TEXT.index(marker)
    fence_start = _CONTRACT_TEXT.index("```", start)
    fence_end = _CONTRACT_TEXT.index("```", fence_start + 3)
    block = _CONTRACT_TEXT[fence_start + 3 : fence_end]
    return [ln.strip() for ln in block.splitlines() if ln.strip()]


def _extracted_bare_paths() -> "list[str]":
    """Strip the trailing "(HMIC-ID)" annotation from contract-path lines."""
    return [re.sub(r"\s+\([A-Z0-9-]+\)\s*$", "", ln).strip() for ln in _extract_req_050_paths()]


# ---------------------------------------------------------------------------
# 69-70. Version and file count
# ---------------------------------------------------------------------------


def test_contract_version_is_v1_1():
    assert "**Version:** 1.1" in _CONTRACT_TEXT
    assert "**Contract ID:** HMIC-001" in _CONTRACT_TEXT


def test_frozen_file_set_has_exactly_24_entries():
    extracted = _extract_req_050_paths()
    assert len(extracted) == 24, f"expected 24 lines in HMIC-REQ-050's fenced block, found {len(extracted)}: {extracted}"


def test_hardcoded_local_v1_1_set_has_exactly_24_entries():
    assert len(_v1_1_repo_relative_paths()) == 24


# ---------------------------------------------------------------------------
# 71. Original 22 preserved
# ---------------------------------------------------------------------------


def test_original_22_paths_all_still_present_in_contract_text():
    bare = set(_extracted_bare_paths())
    for rel in _ORIGINAL_22_SRC_RELATIVE_PATHS:
        assert rel in bare, f"original v1.0 src-relative path missing from v1.1 enumeration: {rel}"
    for rel in _ORIGINAL_22_CONTRACT_RELATIVE_PATHS:
        assert rel in bare, f"original v1.0 contract-relative path missing from v1.1 enumeration: {rel}"


# ---------------------------------------------------------------------------
# 72-73. Core module and admin script added
# ---------------------------------------------------------------------------


def test_core_hmic_module_path_present():
    bare = set(_extracted_bare_paths())
    assert _NEW_SRC_RELATIVE_ENTRY in bare


def test_admin_script_path_present():
    bare = set(_extracted_bare_paths())
    assert _NEW_SCRIPT_ENTRY in bare


# ---------------------------------------------------------------------------
# 74-76. Files exist, canonical, unique
# ---------------------------------------------------------------------------


def test_all_24_frozen_paths_exist_are_regular_and_not_symlinked():
    for rel in _v1_1_repo_relative_paths():
        p = _REPO_ROOT / rel
        assert p.exists(), f"frozen file missing: {rel}"
        assert p.is_file() and not p.is_symlink(), f"frozen path not a plain regular file: {rel}"
        cur = p.parent
        while cur != _REPO_ROOT and cur != cur.parent:
            assert not cur.is_symlink(), f"frozen path has symlinked parent: {cur}"
            cur = cur.parent


def test_frozen_file_set_has_no_duplicates():
    paths = _v1_1_repo_relative_paths()
    assert len(set(paths)) == len(paths)


def test_frozen_paths_are_canonical_relative_posix_no_traversal():
    for rel in _v1_1_repo_relative_paths():
        assert not rel.startswith("/"), rel
        assert ".." not in rel.split("/"), rel
        assert "\\" not in rel, rel
        assert rel == rel.strip()


def test_scripts_entry_is_not_src_pcae_relative():
    # §8/§75 of the phase doc: the `scripts/` bucket is repository-root
    # relative, distinct from the `src/pcae/`-relative bucket the other
    # 19 entries live in.
    assert not _NEW_SCRIPT_ENTRY.startswith("src/")
    assert _NEW_SCRIPT_ENTRY.startswith("scripts/")


# ---------------------------------------------------------------------------
# 77-79. Requirement / CIVC / attack inventory counts
# ---------------------------------------------------------------------------


def test_requirement_ids_are_exactly_001_to_144():
    ids = sorted(int(m) for m in re.findall(r"\*\*HMIC-REQ-(\d{3})", _CONTRACT_TEXT))
    assert ids == list(range(1, 145))
    assert len(set(ids)) == 144


def test_civc_invariants_are_exactly_1_to_12():
    ids = sorted(int(m) for m in re.findall(r"- \*\*CIVC-(\d+)\.\*\*", _CONTRACT_TEXT))
    assert ids == list(range(1, 13))


def test_attack_matrix_has_exactly_34_rows():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    rows = re.findall(r"^\| ([0-9]+) ", table, flags=re.MULTILINE)
    assert [int(r) for r in rows] == list(range(1, 35))


def test_attack_matrix_heading_declares_34_scenarios():
    assert "## 41. Full Mandatory Attack Matrix (34 Scenarios)" in _CONTRACT_TEXT


def test_attack_row_11_names_the_two_v1_1_bound_files():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    row_11 = next(line for line in table.splitlines() if line.startswith("| 11 |"))
    assert "hatp_mandatory_certification.py" in row_11
    assert "hatp_certification_admin.py" in row_11


def test_attack_rows_33_and_34_present_and_named():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    row_33 = next(line for line in table.splitlines() if line.startswith("| 33 "))
    row_34 = next(line for line in table.splitlines() if line.startswith("| 34 "))
    assert "v1.0-scope replay" in row_33
    assert "v1.1" in row_33
    assert "File-set downgrade" in row_34
    assert "not yet operative" in row_33 or "Not yet operative" in row_33


# ---------------------------------------------------------------------------
# 80. W-1 language: validator/admin binding before readiness integration
# ---------------------------------------------------------------------------


def test_w1_contract_status_is_repaired_at_contract_level_not_closed():
    assert "REPAIRED AT CONTRACT LEVEL" in _CONTRACT_TEXT
    assert "INDEPENDENT VERIFICATION PENDING" in _CONTRACT_TEXT
    assert "PRODUCTION TWENTY-FOUR-FILE\nALIGNMENT PENDING" in _CONTRACT_TEXT or (
        "PRODUCTION TWENTY-FOUR-FILE" in _CONTRACT_TEXT and "ALIGNMENT PENDING" in _CONTRACT_TEXT
    )
    assert "W-1 CLOSED" not in _CONTRACT_TEXT


def test_contract_does_not_authorize_wave_f():
    assert "Not `VERIFIED`. Not `READY FOR WAVE" in _CONTRACT_TEXT


# ---------------------------------------------------------------------------
# 81-82. Production alignment still pending; hard-coded False unchanged
# ---------------------------------------------------------------------------


def test_production_identity_derivation_still_implements_22_files_not_24():
    """This is the EXPECTED, disclosed contract-only-phase state: the
    contract now enumerates 24 files, but production's own frozen-file
    constant was deliberately NOT updated by this phase (§21/§27 of the
    phase doc) -- a future bounded implementation-alignment phase must
    do that, and must itself be independently verified. This test fails
    the moment someone accidentally "fixes" production during what
    should be a contract-only phase, which is exactly the guardrail
    intended.

    Read via `git show` at this phase's own exit commit
    (`_PHASE_EXIT_COMMIT`), not the live working tree: 149O.19.5E.3
    subsequently and legitimately aligned production to 24 files, so this
    is now a historical snapshot of what this contract-only phase itself
    left behind, not a claim about current production state."""
    source = _git_show(_PHASE_EXIT_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", source)
    assert match, "could not locate the frozen-file-count assertion in hatp_mandatory_certification.py"
    assert match.group(1) == "22", (
        "production frozen-file count changed during a contract-only phase -- "
        "this phase must not touch src/pcae/**"
    )


def test_hardcoded_readiness_ceiling_still_literal_false():
    source = (_SRC / "core" / "hatp_mandatory_cutover.py").read_text(encoding="utf-8")
    match = re.search(
        r'"mandatory_consumption_implementation_independently_verified",\s*\n\s*(False|True)\s*,',
        source,
    )
    assert match, "could not locate the readiness-ceiling check literal in hatp_mandatory_cutover.py"
    assert match.group(1) == "False"


# ---------------------------------------------------------------------------
# 83. No readiness caller
# ---------------------------------------------------------------------------


def test_hatp_mandatory_cutover_does_not_import_hmic_validator():
    source = (_SRC / "core" / "hatp_mandatory_cutover.py").read_text(encoding="utf-8")
    assert "hatp_mandatory_certification" not in source
    assert "validate_active_hatp_mandatory_independent_verification_certification" not in source


# ---------------------------------------------------------------------------
# 84. No production diff
# ---------------------------------------------------------------------------


def _diff_since_entry(pathspec: str) -> str:
    """Pinned to this phase's own exit commit (`_PHASE_EXIT_COMMIT`), not
    live "HEAD": this phase (149O.19.5E.1) was contract-evolution-only and
    must show zero `src/pcae/`/`scripts/` diff across its own span, but a
    later phase (149O.19.5E.3) legitimately touched
    `src/pcae/core/hatp_mandatory_certification.py` to align production --
    diffing to a moving "HEAD" would make this test fail for a reason
    unrelated to what it actually checks."""
    result = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, _PHASE_EXIT_COMMIT, "--", pathspec],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout


def test_no_src_pcae_files_changed_this_phase():
    diff = _diff_since_entry("src/pcae/")
    assert diff.strip() == "", f"production source changed this phase: {diff}"


def test_no_scripts_files_changed_this_phase():
    diff = _diff_since_entry("scripts/")
    assert diff.strip() == "", f"scripts/ source changed this phase: {diff}"


# ---------------------------------------------------------------------------
# 85. Upstream contract bytes unchanged; only HMIC-001 changed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "existing_contract",
    [
        "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
        "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
        "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
        "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
        "REPOSITORY_WRITE_MERGE_PUSH_CONTROL_CONTRACT.md",
        "PERMISSION_BROKER_POLICY_ADAPTER_CONTRACT.md",
        "PERMISSION_BROKER_POLICY_CONTRACT.md",
    ],
)
def test_upstream_contract_byte_unchanged_by_this_amendment(existing_contract):
    diff = _diff_since_entry(f"docs/contracts/{existing_contract}")
    assert existing_contract not in diff, f"{existing_contract} was modified by this contract-only amendment"


def test_only_hmic_contract_file_changed_under_docs_contracts():
    diff = _diff_since_entry("docs/contracts/")
    changed = [ln for ln in diff.splitlines() if ln.strip()]
    assert changed == ["docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"]


# ---------------------------------------------------------------------------
# No real certification state; no Cutover Record; runtime state unchanged
# ---------------------------------------------------------------------------


def test_no_certification_state_artifacts_exist():
    for name in ("certifications.json", "certification-bindings.json", "active_certification.json"):
        hits = [h for h in _REPO_ROOT.rglob(name) if ".git" not in h.parts and ".venv" not in h.parts]
        assert hits == []


def test_w1_history_section_50_present_and_after_section_49():
    idx_49 = _CONTRACT_TEXT.index("## 49. Contract Repair History")
    idx_50 = _CONTRACT_TEXT.index("## 50. Contract Amendment History")
    assert idx_50 > idx_49


def test_hmic_req_052_closure_rule_covers_certification_implementation_itself():
    section_start = _CONTRACT_TEXT.index("HMIC-REQ-052 (Transitive-Dependency Coverage")
    section_end = _CONTRACT_TEXT.index("HMIC-REQ-053")
    section = _CONTRACT_TEXT[section_start:section_end]
    normalized = " ".join(section.split())
    assert "certification's own implementation semantics" in normalized
    assert "validate_active_hatp_mandatory_independent_verification_certification" in normalized
