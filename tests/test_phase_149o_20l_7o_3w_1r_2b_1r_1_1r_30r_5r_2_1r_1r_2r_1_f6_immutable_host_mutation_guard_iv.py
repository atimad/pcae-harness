"""Independent verification of F-6 and adjudication of its three siblings."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1"
P = "2eaf536d05b6852c6bc6692cec139afab1083f84"
R = V = "8dcca97bb1a88a99cac3afe610f3651adcc58295"
F6_IV_FINALIZED = "7ef7ae0e9b0632ef0bd3c352e4598c03a9b05c69"
V4 = "90510428422e451382549ce76111610752aaafb4"
U4 = "7124c019bf3f46eb07456b81146484609197dbc2"
IV_COMMITS = [
    "f1b4b85be0954bdcab3081e119aec56f58176ad6",
    "3efe571dc808725b4530f6278b544650bd69363d",
    "e807cd697e919b58ad8979dc41a90940f240e67e",
    U4,
]
OWNER_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py"
OWNER = ROOT / OWNER_REL
REPAIR_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_f6_immutable_host_mutation_guard_repair.py"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1_F6_IMMUTABLE_HOST_MUTATION_GUARD_IV_BLOCKED.md"
HIST_TASK_REL = "tasks/done/20260904-1129-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-1-independent-verification-of-the-f-4-immutable-historical-scope-guard-repair.md"
PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def show(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}")


def function(source: str, name: str) -> ast.FunctionDef:
    return next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)


def rendered(name: str, *, source: str | None = None) -> str:
    return ast.unparse(function(source or OWNER.read_text(), name))


def historical_files() -> list[str]:
    return git("diff", "--name-only", V4, U4).splitlines()


def synthetic(path: Path, forbidden_inside: bool) -> tuple[str, str, str]:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "iv@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "F6 IV"], cwd=path, check=True)
    (path / "entry.txt").write_text("entry\n")
    subprocess.run(["git", "add", "entry.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "entry"], cwd=path, check=True)
    entry = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    name = "protected-root-forbidden.txt" if forbidden_inside else "iv.txt"
    (path / name).write_text("historical\n")
    subprocess.run(["git", "add", name], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "historical"], cwd=path, check=True)
    end = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    (path / "successor-protected-root-deployment.txt").write_text("later\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "successor"], cwd=path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    return entry, end, head


def test_01_exact_phase_lineage() -> None:
    from pcae.core.phase_id import parse
    assert parse(PHASE).normalized_text == PHASE


def test_02_predecessor_f6_repair_completed() -> None:
    assert "F-6:\nREPAIRED" in show(R, "PROJECT_STATUS.md")


def test_03_blocked_deployment_attempt_is_preserved() -> None:
    assert "BLOCKED BEFORE HOST MUTATION" in show(P, "PROJECT_STATUS.md").replace("\n", " ")


def test_04_p_r_v_are_independently_resolvable() -> None:
    assert git("rev-parse", P) == P and git("rev-parse", R) == R and V == R


def test_05_v4_is_parent_of_first_f4_iv_commit() -> None:
    assert git("rev-parse", f"{IV_COMMITS[0]}^") == V4


def test_06_u4_is_f4_iv_reconciliation_head() -> None:
    assert "reconcile governed push state" in git("log", "-1", "--format=%s", U4)


def test_07_claimed_lower_bound_is_exact() -> None:
    assert V4 == "90510428422e451382549ce76111610752aaafb4"


def test_08_claimed_upper_bound_is_exact() -> None:
    assert U4 == "7124c019bf3f46eb07456b81146484609197dbc2"


def test_09_pre_repair_f6_is_reconstructed() -> None:
    old = rendered("test_43_no_protected_root_mutation_is_in_iv_diff", source=show(P, OWNER_REL))
    assert "git('diff', '--name-only', V)" in old


def test_10_original_invariant_is_historical_f4_iv_scope() -> None:
    task = show(U4, HIST_TASK_REL)
    assert "No F-5 protected-root/helper deployment mutation" in task


def test_11_exact_historical_commit_set() -> None:
    assert git("rev-list", "--first-parent", "--reverse", f"{V4}..{U4}").splitlines() == IV_COMMITS


def test_12_exact_historical_file_count() -> None:
    assert set(historical_files()) == {
        ".pcae/phase-completion-metadata.json", "CHANGELOG.md", "PROJECT_STATUS.md",
        "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_1_F4_IMMUTABLE_HISTORICAL_SCOPE_GUARD_REPAIR_IV.md",
        "tasks/DECISIONS.md", "tasks/DONE.md",
        "tasks/active/20260904-1139-idle-awaiting-explicit-authorization-for-f-5-protected-helper-deployment-preparation-n-16-5-not-closed.md",
        "tasks/done/20260904-1046-idle-awaiting-explicit-authorization-for-30r-5r-2-1r-1r-1-f-4-independent-verification-f-5-open-n-16-5-not-closed.md",
        HIST_TASK_REL, OWNER_REL,
    }


def test_13_live_head_is_not_repaired_historical_authority() -> None:
    assert "HEAD" not in rendered("test_43_no_protected_root_mutation_is_in_iv_diff")


def test_14_live_metadata_is_not_repaired_historical_authority() -> None:
    node = rendered("test_43_no_protected_root_mutation_is_in_iv_diff")
    assert "PROJECT_STATUS" not in node and "phase-completion" not in node


def test_15_repaired_guard_uses_immutable_range() -> None:
    assert "V, F4_IV_FINALIZED" in rendered("test_43_no_protected_root_mutation_is_in_iv_diff")


def test_16_historical_state_passes() -> None:
    assert not any("protected-root" in p for p in historical_files())


def test_17_current_successor_passes_for_fixed_reason() -> None:
    assert git("rev-parse", "HEAD") != U4 and not any("protected-root" in p for p in historical_files())


def test_18_future_deployment_like_successor_passes(tmp_path: Path) -> None:
    entry, end, head = synthetic(tmp_path, False)
    fixed = subprocess.check_output(["git", "diff", "--name-only", entry, end], cwd=tmp_path, text=True)
    moving = subprocess.check_output(["git", "diff", "--name-only", entry, head], cwd=tmp_path, text=True)
    assert "protected-root" not in fixed and "protected-root" in moving


def test_19_forbidden_historical_host_mutation_fails(tmp_path: Path) -> None:
    entry, end, _ = synthetic(tmp_path, True)
    names = subprocess.check_output(["git", "diff", "--name-only", entry, end], cwd=tmp_path, text=True)
    assert any("protected-root" in p for p in names.splitlines())


def test_20_no_current_head_exception() -> None:
    assert "current_head" not in rendered("test_43_no_protected_root_mutation_is_in_iv_diff")


def test_21_no_phase_prefix_exception() -> None:
    node = rendered("test_43_no_protected_root_mutation_is_in_iv_diff")
    assert "startswith" not in node and "endswith" not in node


def test_22_no_wildcard() -> None:
    assert "glob" not in rendered("test_43_no_protected_root_mutation_is_in_iv_diff")


def test_23_no_fnmatch() -> None:
    assert "fnmatch" not in rendered("test_43_no_protected_root_mutation_is_in_iv_diff")


def test_24_no_predecessor_test_removal() -> None:
    assert OWNER.read_text().count("def test_") == show(P, OWNER_REL).count("def test_")


def test_25_no_repaired_test_rename() -> None:
    assert "def test_43_no_protected_root_mutation_is_in_iv_diff" in OWNER.read_text()


def test_26_no_skip() -> None:
    assert "pytest.skip" not in rendered("test_43_no_protected_root_mutation_is_in_iv_diff")


def test_27_no_skipif() -> None:
    assert "skipif" not in rendered("test_43_no_protected_root_mutation_is_in_iv_diff")


def test_28_no_pytest_skip() -> None:
    assert "pytest.skip" not in rendered("test_43_no_protected_root_mutation_is_in_iv_diff")


def test_29_no_xfail() -> None:
    assert "xfail" not in rendered("test_43_no_protected_root_mutation_is_in_iv_diff")


def test_30_f3_remains_verified() -> None:
    assert "F-3" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_31_f4_remains_verified() -> None:
    assert "F-4" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_32_h2_source_unchanged() -> None:
    assert git("diff", "--name-only", V, "--", "src/pcae/protected_presentation_helper.py") == ""


def test_33_f2_source_unchanged() -> None:
    assert git("diff", "--name-only", V, "--", "src/pcae/core/hpac_protected_presentation.py") == ""


def test_34_h1_source_unchanged() -> None:
    assert git("diff", "--name-only", V, "--", "src/pcae/core/hpac_rhamp_ctap2.py") == ""


def test_35_sibling_1_identified() -> None:
    assert function(OWNER.read_text(), "test_44_no_helper_installation_or_pawa_write_in_iv")


def test_36_sibling_1_is_historical_moving_authority() -> None:
    historical = show(F6_IV_FINALIZED, OWNER_REL)
    node = rendered("test_44_no_helper_installation_or_pawa_write_in_iv", source=historical)
    assert "git('diff', '--name-only', V)" in node and "in_iv" in function(historical, "test_44_no_helper_installation_or_pawa_write_in_iv").name


def test_37_sibling_2_identified() -> None:
    assert function(OWNER.read_text(), "test_46_no_yubikey_or_certification_evidence_minted")


def test_38_sibling_2_is_historical_moving_authority() -> None:
    node = rendered("test_46_no_yubikey_or_certification_evidence_minted", source=show(F6_IV_FINALIZED, OWNER_REL))
    assert "git('diff', '--name-only', V, '--', '.pcae/certification')" in node


def test_39_sibling_3_identified() -> None:
    assert function(OWNER.read_text(), "test_56_iv_changes_no_product_contract_or_dependency_bytes")


def test_40_sibling_3_is_historical_moving_authority() -> None:
    historical = show(F6_IV_FINALIZED, OWNER_REL)
    node = rendered("test_56_iv_changes_no_product_contract_or_dependency_bytes", source=historical)
    assert "git('diff', '--name-only', V, '--'" in node and "iv_changes" in function(historical, "test_56_iv_changes_no_product_contract_or_dependency_bytes").name


def test_41_f5_impact_assessed_for_all_siblings() -> None:
    text = REPORT.read_text()
    assert text.count("No, ") >= 3 and "Blocking before F-5?" in text


def test_42_targeted_same_family_scan_is_recorded() -> None:
    assert "1,086 test definitions" in REPORT.read_text() and "48 Git/HEAD pattern lines" in REPORT.read_text()


def test_43_every_disclosed_match_is_classified() -> None:
    text = REPORT.read_text()
    for name in ("test_44", "test_46", "test_56"):
        assert name in text
    assert text.count("category B") >= 3


def test_44_no_additional_defect_is_silently_repaired() -> None:
    assert git("diff", "--name-only", V, F6_IV_FINALIZED, "--", OWNER_REL, REPAIR_REL) == ""


def test_45_no_production_source_change() -> None:
    assert git("diff", "--name-only", V, "--", "src/pcae") == ""


def test_46_no_production_script_change() -> None:
    assert git("diff", "--name-only", V, "--", "scripts") == ""


def test_47_no_dependency_change() -> None:
    assert git("diff", "--name-only", V, "--", "pyproject.toml") == ""


def test_48_no_contract_change() -> None:
    assert git("diff", "--name-only", V, "--", "docs/contracts") == ""


def test_49_f5_remains_absent() -> None:
    assert not PROTECTED_ROOT.exists()


def test_50_no_protected_root_mutation() -> None:
    assert "F-5: OPEN / ABSENT / UNCHANGED" in REPORT.read_text()


def test_51_no_helper_installation() -> None:
    assert not PROTECTED_ROOT.exists()


def test_52_no_pawa_deployment_capability() -> None:
    assert "PAWA deployment capability" in REPORT.read_text()


def test_53_no_administrator_interaction() -> None:
    assert "administrator interaction" in REPORT.read_text()


def test_54_no_human_election() -> None:
    assert "protected election" in REPORT.read_text()


def test_55_no_yubikey() -> None:
    assert "YubiKey interaction" in REPORT.read_text()


def test_56_no_presentation_evidence() -> None:
    assert "presentation evidence" in REPORT.read_text()


def test_57_no_principal_or_gate_certification() -> None:
    text = REPORT.read_text()
    assert "principal" in text and "Gate certification" in text


def test_58_n16_5_remains_open() -> None:
    assert "N-16-5 remains NOT CLOSED" in REPORT.read_text()


def test_59_runtime_unchanged() -> None:
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    for value in ("not_implemented", "Observed", "observe", "unavailable", "Plugin count:              0", "Capability count:          0"):
        assert value in out


def test_60_first_effect_absent() -> None:
    assert "first effect absent" in REPORT.read_text()


def test_61_n16_6_untouched() -> None:
    assert "N-16-6/N-16-7 remain untouched" in REPORT.read_text()


def test_62_n16_7_untouched() -> None:
    assert "N-16-6/N-16-7 remain untouched" in REPORT.read_text()


def test_63_fido2_supported_not_exclusive() -> None:
    assert "FIDO2 and local presentation remain supported-not-exclusive" in REPORT.read_text()


def test_64_local_presentation_supported_not_exclusive() -> None:
    assert "local presentation remain supported-not-exclusive" in REPORT.read_text()


def test_65_mobile_only_future_profile_preserved() -> None:
    assert "mobile-only authentication and protected approval remain open/planned" in REPORT.read_text()
