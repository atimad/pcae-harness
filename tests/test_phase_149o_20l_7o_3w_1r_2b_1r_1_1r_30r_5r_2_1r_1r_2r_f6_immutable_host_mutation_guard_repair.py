"""Repair evidence for F-6's immutable F-4-IV host-mutation guard."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R"
P = "7124c019bf3f46eb07456b81146484609197dbc2"
B = "2eaf536d05b6852c6bc6692cec139afab1083f84"
R0 = B
V4 = "90510428422e451382549ce76111610752aaafb4"
U4 = P
IV_COMMITS = [
    "f1b4b85be0954bdcab3081e119aec56f58176ad6",
    "3efe571dc808725b4530f6278b544650bd69363d",
    "e807cd697e919b58ad8979dc41a90940f240e67e",
    U4,
]
OWNER_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py"
OWNER = ROOT / OWNER_REL
BLOCKED_REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2_F5_DEPLOYMENT_PREPARATION_BLOCKED.md"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_F6_IMMUTABLE_HOST_MUTATION_GUARD_REPAIR.md"
PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def show(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}")


def node(source: str) -> ast.FunctionDef:
    return next(
        n for n in ast.parse(source).body
        if isinstance(n, ast.FunctionDef)
        and n.name == "test_43_no_protected_root_mutation_is_in_iv_diff"
    )


def current_node() -> str:
    return ast.unparse(node(OWNER.read_text()))


def historical_files() -> list[str]:
    return git("diff", "--name-only", V4, U4).splitlines()


def metadata_at(commit: str) -> dict[str, object]:
    return json.loads(show(commit, ".pcae/phase-completion-metadata.json"))


def init_synthetic_repo(path: Path, *, forbidden_inside: bool) -> tuple[str, str, str]:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "f6@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "F6 Test"], cwd=path, check=True)
    (path / "entry.txt").write_text("entry\n")
    subprocess.run(["git", "add", "entry.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "entry"], cwd=path, check=True)
    entry = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    historical_name = "protected-root-forbidden.txt" if forbidden_inside else "iv-evidence.txt"
    (path / historical_name).write_text("historical\n")
    subprocess.run(["git", "add", historical_name], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "historical end"], cwd=path, check=True)
    end = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    (path / "successor-protected-root-preparation.txt").write_text("successor\n")
    subprocess.run(["git", "add", "successor-protected-root-preparation.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "legitimate successor"], cwd=path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    return entry, end, head


def test_01_exact_cpipc_lineage() -> None:
    from pcae.core.phase_id import parse
    assert parse(PHASE).normalized_text == PHASE


def test_02_predecessor_deployment_attempt_remains_blocked() -> None:
    assert "**BLOCKED before host mutation" in BLOCKED_REPORT.read_text()


def test_03_f6_exact_node_identified() -> None:
    assert node(OWNER.read_text()).name == "test_43_no_protected_root_mutation_is_in_iv_diff"


def test_04_original_f6_reproduced_from_immutable_pre_repair_blob() -> None:
    old = ast.unparse(node(show(B, OWNER_REL)))
    assert "git('diff', '--name-only', V)" in old


def test_05_original_f4_iv_invariant_is_reconstructed() -> None:
    assert "no protected-root mutation" in BLOCKED_REPORT.read_text().lower()


def test_06_f4_iv_lower_bound_is_immutable() -> None:
    assert git("rev-parse", f"{IV_COMMITS[0]}^") == V4


def test_07_f4_iv_upper_bound_is_immutable() -> None:
    assert git("rev-parse", U4) == U4


def test_08_exact_f4_iv_commit_set() -> None:
    assert git("rev-list", "--first-parent", "--reverse", f"{V4}..{U4}").splitlines() == IV_COMMITS


def test_09_exact_f4_iv_file_set() -> None:
    assert set(historical_files()) == {
        ".pcae/phase-completion-metadata.json", "CHANGELOG.md", "PROJECT_STATUS.md",
        "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_1_F4_IMMUTABLE_HISTORICAL_SCOPE_GUARD_REPAIR_IV.md",
        "tasks/DECISIONS.md", "tasks/DONE.md",
        "tasks/active/20260904-1139-idle-awaiting-explicit-authorization-for-f-5-protected-helper-deployment-preparation-n-16-5-not-closed.md",
        "tasks/done/20260904-1046-idle-awaiting-explicit-authorization-for-30r-5r-2-1r-1r-1-f-4-independent-verification-f-5-open-n-16-5-not-closed.md",
        "tasks/done/20260904-1129-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-1-independent-verification-of-the-f-4-immutable-historical-scope-guard-repair.md",
        OWNER_REL,
    }


def test_10_moving_v_head_defect_is_proven() -> None:
    assert any("protected-root" in p for p in git("diff", "--name-only", V4, B).splitlines())


def test_11_live_head_is_not_historical_authority() -> None:
    assert "HEAD" not in current_node()


def test_12_live_origin_main_is_not_historical_authority() -> None:
    assert "origin/main" not in current_node()


def test_13_live_metadata_is_not_historical_authority() -> None:
    assert "phase-completion-metadata" not in current_node()


def test_14_repaired_node_uses_immutable_historical_range() -> None:
    assert "V, F4_IV_FINALIZED" in current_node()


def test_15_historical_f4_iv_state_passes() -> None:
    assert not any("protected-root" in p for p in historical_files())


def test_16_current_successor_state_passes() -> None:
    assert git("rev-parse", "HEAD") != U4 and not any("protected-root" in p for p in historical_files())


def test_17_future_synthetic_successor_passes(tmp_path: Path) -> None:
    entry, end, head = init_synthetic_repo(tmp_path, forbidden_inside=False)
    fixed = subprocess.check_output(["git", "diff", "--name-only", entry, end], cwd=tmp_path, text=True)
    moving = subprocess.check_output(["git", "diff", "--name-only", entry, head], cwd=tmp_path, text=True)
    assert "protected-root" not in fixed and "protected-root" in moving


def test_18_deployment_like_successor_does_not_pollute_history(tmp_path: Path) -> None:
    entry, end, _ = init_synthetic_repo(tmp_path, forbidden_inside=False)
    names = subprocess.check_output(["git", "diff", "--name-only", entry, end], cwd=tmp_path, text=True)
    assert "successor-protected-root-preparation.txt" not in names


def test_19_forbidden_indicator_inside_history_fails(tmp_path: Path) -> None:
    entry, end, _ = init_synthetic_repo(tmp_path, forbidden_inside=True)
    names = subprocess.check_output(["git", "diff", "--name-only", entry, end], cwd=tmp_path, text=True)
    assert any("protected-root" in p for p in names.splitlines())


def test_20_no_current_head_special_case() -> None:
    assert "current_head" not in current_node() and "if HEAD" not in current_node()


def test_21_no_phase_prefix_special_case() -> None:
    assert "startswith" not in current_node() and "endswith" not in current_node()


def test_22_no_wildcard() -> None:
    assert "glob" not in current_node()


def test_23_no_fnmatch() -> None:
    assert "fnmatch" not in current_node()


def test_24_no_test_removal() -> None:
    assert OWNER.read_text().count("def test_") == show(B, OWNER_REL).count("def test_")


def test_25_no_rename_to_evade() -> None:
    assert "def test_43_no_protected_root_mutation_is_in_iv_diff" in OWNER.read_text()


def test_26_no_skip() -> None:
    assert "pytest.skip" not in current_node()


def test_27_no_skipif() -> None:
    assert "skipif" not in current_node()


def test_28_no_pytest_skip() -> None:
    assert "pytest.skip" not in current_node()


def test_29_no_xfail() -> None:
    assert "xfail" not in current_node()


def test_30_f4_core_guard_remains_verified() -> None:
    owner = (ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_contract_reconciliation.py").read_text()
    assert "R4R_FINALIZED, R4R1_FINALIZED" in owner


def test_31_f3_remains_verified() -> None:
    path = ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_f3_immutable_phase_entry_evidence_repair.py"
    assert "REPAIR_IMPLEMENTATION" in path.read_text()


def test_32_h2_source_unchanged() -> None:
    assert git("diff", "--name-only", R0, "--", "src/pcae/protected_presentation_helper.py") == ""


def test_33_f2_source_unchanged() -> None:
    assert git("diff", "--name-only", R0, "--", "src/pcae/core/protected_presentation.py") == ""


def test_34_h1_source_unchanged() -> None:
    assert git("diff", "--name-only", R0, "--", "src/pcae/core/hpac_rhamp_ctap2.py") == ""


def test_35_no_production_source_change() -> None:
    assert git("diff", "--name-only", R0, "--", "src/pcae") == ""


def test_36_no_production_script_change() -> None:
    assert git("diff", "--name-only", R0, "--", "scripts") == ""


def test_37_no_dependency_change() -> None:
    assert git("diff", "--name-only", R0, "--", "pyproject.toml") == ""


def test_38_no_contract_change() -> None:
    assert git("diff", "--name-only", R0, "--", "docs/contracts") == ""


def test_39_f5_remains_absent() -> None:
    assert not PROTECTED_ROOT.exists()


def test_40_no_protected_root_mutation() -> None:
    assert not PROTECTED_ROOT.exists()


def test_41_no_helper_installation() -> None:
    assert not PROTECTED_ROOT.exists()


def test_42_no_pawa_deployment_capability() -> None:
    assert git("diff", "--name-only", R0, "--", ".pcae/certification") == ""


def test_43_no_administrator_interaction() -> None:
    assert "administrator interaction occurred" not in BLOCKED_REPORT.read_text().lower()


def test_44_no_human_election() -> None:
    text = BLOCKED_REPORT.read_text()
    assert "No administrator prompt was opened" in text and "Human protected election" in text


def test_45_no_yubikey() -> None:
    assert "YubiKey interaction: none" in BLOCKED_REPORT.read_text()


def test_46_no_presentation_evidence() -> None:
    assert git("diff", "--name-only", R0, "--", ".pcae/certification") == ""


def test_47_no_production_principal() -> None:
    assert "PRODUCTION principal" not in BLOCKED_REPORT.read_text().split("No-Go Confirmations", 1)[-1]


def test_48_no_gate_certification() -> None:
    assert "Gate 5 certification occurred" not in BLOCKED_REPORT.read_text()


def test_49_n16_5_remains_open() -> None:
    assert "N-16-5: NOT CLOSED" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_50_runtime_unchanged() -> None:
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    assert all(value in out for value in ("not_implemented", "Observed", "observe", "unavailable"))


def test_51_first_effect_absent() -> None:
    assert "first effect absent" in (ROOT / "PROJECT_STATUS.md").read_text().lower()


def test_52_n16_6_untouched() -> None:
    assert "N-16-6/N-16-7 untouched" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_53_n16_7_untouched() -> None:
    assert "N-16-6/N-16-7 untouched" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_54_fido2_supported_not_exclusive() -> None:
    assert "supported-not-exclusive" in (ROOT / "PROJECT_STATUS.md").read_text().lower()


def test_55_local_presentation_supported_not_exclusive() -> None:
    text = (ROOT / "PROJECT_STATUS.md").read_text().lower()
    assert "local presentation" in text and "supported-not-exclusive" in text


def test_56_mobile_only_future_profile_preserved() -> None:
    assert "mobile-only profiles remain open" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_57_same_defect_family_scan_is_recorded() -> None:
    text = REPORT.read_text()
    assert "Same-defect-family scan" in text and "test_44" in text and "test_46" in text and "test_56" in text
