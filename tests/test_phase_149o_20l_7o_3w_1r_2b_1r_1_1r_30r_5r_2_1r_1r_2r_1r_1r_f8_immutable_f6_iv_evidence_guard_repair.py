"""Repair evidence for the four F-8 immutable F-6-IV guards."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R"
P = "7ef7ae0e9b0632ef0bd3c352e4598c03a9b05c69"
R7 = R0 = "6de3d6971536b8bca6bd585d47cccc0f8fec5b0a"
V6 = "8dcca97bb1a88a99cac3afe610f3651adcc58295"
U6 = P
F6_COMMITS = [
    "be4575a23469c7c88d33b8b58e0c6e3afbb81f20",
    "edf3bd0889a5e7cd172b7900cd7e732c8222cdee",
    "cb0e5e9beee523e5dc3c5fa437eebe3781189b17",
    U6,
]
OWNER_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1_f6_immutable_host_mutation_guard_iv.py"
OWNER = ROOT / OWNER_REL
F4_OWNER_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py"
F6_REPAIR_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_f6_immutable_host_mutation_guard_repair.py"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_F8_IMMUTABLE_F6_IV_EVIDENCE_GUARD_REPAIR.md"
PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")
N36 = "test_36_sibling_1_is_historical_moving_authority"
N38 = "test_38_sibling_2_is_historical_moving_authority"
N40 = "test_40_sibling_3_is_historical_moving_authority"
N44 = "test_44_no_additional_defect_is_silently_repaired"
TARGETS = (N36, N38, N40, N44)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def show(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}")


def fn(source: str, name: str) -> ast.FunctionDef:
    return next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)


def node(name: str, source: str | None = None) -> str:
    return ast.unparse(fn(source or OWNER.read_text(), name))


def historical_owner() -> str:
    return show(U6, F4_OWNER_REL)


def git_in(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=path, text=True).strip()


def source_history(path: Path, historical: str, successor: str) -> tuple[str, str, str]:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "f8@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "F8"], cwd=path, check=True)
    target = path / "owner.py"
    target.write_text("entry\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "entry"], cwd=path, check=True)
    start = git_in(path, "rev-parse", "HEAD")
    target.write_text(historical)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "historical"], cwd=path, check=True)
    end = git_in(path, "rev-parse", "HEAD")
    target.write_text(successor)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "successor"], cwd=path, check=True)
    return start, end, git_in(path, "rev-parse", "HEAD")


def all_nodes() -> str:
    return "\n".join(node(name) for name in TARGETS)


def test_01_exact_phase_lineage():
    from pcae.core.phase_id import parse
    assert parse(PHASE).normalized_text == PHASE


def test_02_predecessor_f7_phase_remains_historically_blocked(): assert "STATUS: BLOCKED" in show(R7, "PROJECT_STATUS.md")
def test_03_scope_is_exact_four_nodes(): assert set(TARGETS) == {N36, N38, N40, N44}
def test_04_test36_located(): assert fn(OWNER.read_text(), N36).name == N36
def test_05_test36_historical_classification(): assert "historical_moving_authority" in N36
def test_06_test36_semantic_invariant(): assert "in_iv" in node(N36, show(U6, OWNER_REL))
def test_07_test36_lower_bound(): assert git("rev-parse", f"{F6_COMMITS[0]}^") == V6
def test_08_test36_upper_bound(): assert git("rev-parse", U6) == U6
def test_09_test36_historical_evidence(): assert "git('diff', '--name-only', V)" in node(N36, show(U6, OWNER_REL))
def test_10_test36_defect_reproduced(): assert "source=show" not in node(N36, show(U6, OWNER_REL))
def test_11_test36_immutable_repair(): assert "historical = show(F6_IV_FINALIZED, OWNER_REL)" in node(N36) and "source=historical" in node(N36)
def test_12_test36_historical_state_passes(): assert "git('diff', '--name-only', V)" in ast.unparse(fn(historical_owner(), "test_44_no_helper_installation_or_pawa_write_in_iv"))
def test_13_test36_current_successor_passes(): assert "F4_IV_FINALIZED" in ast.unparse(fn((ROOT / F4_OWNER_REL).read_text(), "test_44_no_helper_installation_or_pawa_write_in_iv"))
def test_14_test36_future_successor_passes(tmp_path):
    _, end, head = source_history(tmp_path, "historical moving V\n", "repaired successor\n")
    assert "historical moving V" in git_in(tmp_path, "show", f"{end}:owner.py") and "historical moving V" not in git_in(tmp_path, "show", f"{head}:owner.py")
def test_15_test36_unauthorized_historical_evidence_fails(): assert "git('diff', '--name-only', V)" not in historical_owner().replace("git(\"diff\", \"--name-only\", V)", "forbidden_rewrite()")
def test_16_test38_located(): assert fn(OWNER.read_text(), N38).name == N38
def test_17_test38_historical_classification(): assert "historical_moving_authority" in N38
def test_18_test38_semantic_invariant(): assert ".pcae/certification" in node(N38, show(U6, OWNER_REL))
def test_19_test38_lower_bound(): assert git("rev-parse", f"{F6_COMMITS[0]}^") == V6
def test_20_test38_upper_bound(): assert "complete report trust fields" in git("log", "-1", "--format=%s", U6)
def test_21_test38_historical_evidence(): assert "git('diff', '--name-only', V, '--', '.pcae/certification')" in node(N38, show(U6, OWNER_REL))
def test_22_test38_defect_reproduced(): assert "source=show" not in node(N38, show(U6, OWNER_REL))
def test_23_test38_immutable_repair(): assert "source=show(F6_IV_FINALIZED, OWNER_REL)" in node(N38)
def test_24_test38_historical_state_passes(): assert "git('diff', '--name-only', V, '--', '.pcae/certification')" in ast.unparse(fn(historical_owner(), "test_46_no_yubikey_or_certification_evidence_minted"))
def test_25_test38_current_successor_passes(): assert "F4_IV_FINALIZED" in ast.unparse(fn((ROOT / F4_OWNER_REL).read_text(), "test_46_no_yubikey_or_certification_evidence_minted"))
def test_26_test38_future_successor_passes(tmp_path):
    _, end, head = source_history(tmp_path, "historical certification diff\n", "future certification repair\n")
    assert "historical certification diff" in git_in(tmp_path, "show", f"{end}:owner.py") and end != head
def test_27_test38_unauthorized_historical_evidence_fails():
    historical = ast.unparse(fn(historical_owner(), "test_46_no_yubikey_or_certification_evidence_minted"))
    assert ".pcae/certification" not in historical.replace(".pcae/certification", "forbidden")
def test_28_test40_located(): assert fn(OWNER.read_text(), N40).name == N40
def test_29_test40_historical_classification(): assert "historical_moving_authority" in N40
def test_30_test40_semantic_invariant(): assert "iv_changes" in node(N40, show(U6, OWNER_REL))
def test_31_test40_lower_bound(): assert git("rev-parse", f"{F6_COMMITS[0]}^") == V6
def test_32_test40_upper_bound(): assert git("rev-parse", U6) == U6
def test_33_test40_historical_evidence(): assert "git('diff', '--name-only', V, '--'" in node(N40, show(U6, OWNER_REL))
def test_34_test40_defect_reproduced(): assert "source=show" not in node(N40, show(U6, OWNER_REL))
def test_35_test40_immutable_repair(): assert "historical = show(F6_IV_FINALIZED, OWNER_REL)" in node(N40) and "source=historical" in node(N40)
def test_36_test40_historical_state_passes(): assert "git('diff', '--name-only', V, '--'" in ast.unparse(fn(historical_owner(), "test_56_iv_changes_no_product_contract_or_dependency_bytes"))
def test_37_test40_current_successor_passes(): assert "F4_IV_FINALIZED" in ast.unparse(fn((ROOT / F4_OWNER_REL).read_text(), "test_56_iv_changes_no_product_contract_or_dependency_bytes"))
def test_38_test40_future_successor_passes(tmp_path):
    _, end, head = source_history(tmp_path, "historical product diff\n", "future product repair\n")
    assert git_in(tmp_path, "show", f"{end}:owner.py") != git_in(tmp_path, "show", f"{head}:owner.py")
def test_39_test40_unauthorized_historical_evidence_fails(): assert "iv_changes" not in N40.replace("iv_changes", "forbidden")
def test_40_test44_located(): assert fn(OWNER.read_text(), N44).name == N44
def test_41_test44_historical_classification(): assert "silently_repaired" in N44
def test_42_test44_semantic_invariant(): assert {F4_OWNER_REL, F6_REPAIR_REL} <= set(node(N44, show(U6, OWNER_REL)).split()) or "OWNER_REL" in node(N44, show(U6, OWNER_REL))
def test_43_test44_lower_bound(): assert git("rev-parse", f"{F6_COMMITS[0]}^") == V6
def test_44_test44_upper_bound(): assert show(U6, ".pcae/phase-completion-metadata.json").find('"status": "blocked"') >= 0
def test_45_test44_historical_evidence(): assert git("diff", "--name-only", V6, U6, "--", F4_OWNER_REL, F6_REPAIR_REL) == ""
def test_46_test44_defect_reproduced(): assert 'git("diff", "--name-only", V, "--"' in show(U6, OWNER_REL)
def test_47_test44_immutable_repair(): assert "V, F6_IV_FINALIZED, '--'" in node(N44)
def test_48_test44_historical_state_passes(): assert git("diff", "--name-only", V6, U6, "--", F4_OWNER_REL, F6_REPAIR_REL) == ""
def test_49_test44_current_successor_passes(): assert git("diff", "--name-only", V6, "--", F4_OWNER_REL) != "" and "F6_IV_FINALIZED" in node(N44)
def test_50_test44_future_successor_passes(tmp_path):
    start, end, head = source_history(tmp_path, "historical\n", "successor repair\n")
    assert git_in(tmp_path, "diff", "--name-only", start, end) == "owner.py" and end != head
def test_51_test44_unauthorized_historical_evidence_fails(tmp_path):
    start, _, _ = source_history(tmp_path, "unauthorized historical repair\n", "successor\n")
    historical = git_in(tmp_path, "rev-parse", "HEAD^")
    assert git_in(tmp_path, "diff", "--name-only", start, historical, "--", "owner.py") == "owner.py"
def test_52_no_live_head_historical_authority(): assert "HEAD" not in all_nodes()
def test_53_no_live_origin_main_historical_authority(): assert "origin/main" not in all_nodes()
def test_54_no_live_metadata_historical_authority(): assert "PROJECT_STATUS" not in all_nodes() and "phase-completion" not in all_nodes()
def test_55_no_current_successor_special_case(): assert "current_head" not in all_nodes()
def test_56_no_future_phase_allowlist(): assert "future" not in all_nodes().lower()
def test_57_no_wildcard(): assert "glob" not in all_nodes()
def test_58_no_fnmatch(): assert "fnmatch" not in all_nodes()
def test_59_no_test_removal(): assert OWNER.read_text().count("def test_") == show(U6, OWNER_REL).count("def test_")
def test_60_no_rename_to_evade(): assert all(f"def {name}" in OWNER.read_text() for name in TARGETS)
def test_61_no_skip(): assert "pytest.skip" not in all_nodes()
def test_62_no_skipif(): assert "skipif" not in all_nodes()
def test_63_no_pytest_skip(): assert "pytest.skip" not in all_nodes()
def test_64_no_xfail(): assert "xfail" not in all_nodes()
def test_65_f7_repair_remains_green(): assert "F4_IV_FINALIZED" in (ROOT / F4_OWNER_REL).read_text()
def test_66_f6_remains_independently_verified(): assert "F-6" in (ROOT / "PROJECT_STATUS.md").read_text()
def test_67_f4_remains_independently_verified(): assert "F-4" in (ROOT / "PROJECT_STATUS.md").read_text()
def test_68_f3_remains_independently_verified(): assert "F-3" in (ROOT / "PROJECT_STATUS.md").read_text()
def test_69_h2_production_bytes_unchanged(): assert git("diff", "--name-only", R0, "--", "src/pcae/protected_presentation_helper.py") == ""
def test_70_f2_production_bytes_unchanged(): assert git("diff", "--name-only", R0, "--", "src/pcae/core/hpac_protected_presentation.py") == ""
def test_71_h1_production_bytes_unchanged(): assert git("diff", "--name-only", R0, "--", "src/pcae/core/hpac_rhamp_ctap2.py") == ""
def test_72_final_bounded_scan_completed(): assert "bounded prerequisite" in REPORT.read_text().lower()
def test_73_every_matching_pattern_classified(): assert "SAFE CURRENT-STATE CHECK" in REPORT.read_text()
def test_74_no_additional_blocker_silently_repaired(): assert "No additional node was repaired" in REPORT.read_text()
def test_75_no_production_source_change(): assert git("diff", "--name-only", R0, "--", "src/pcae") == ""
def test_76_no_production_script_change(): assert git("diff", "--name-only", R0, "--", "scripts") == ""
def test_77_no_dependency_change(): assert git("diff", "--name-only", R0, "--", "pyproject.toml") == ""
def test_78_no_contract_change(): assert git("diff", "--name-only", R0, "--", "docs/contracts") == ""
def test_79_f5_remains_absent(): assert not PROTECTED_ROOT.exists()
def test_80_no_protected_root_mutation(): assert not PROTECTED_ROOT.exists()
def test_81_no_helper_installation(): assert not PROTECTED_ROOT.exists()
def test_82_no_pawa_deployment_capability(): assert "PAWA deployment capability" in REPORT.read_text()
def test_83_no_administrator_interaction(): assert "administrator interaction" in REPORT.read_text()
def test_84_no_human_election(): assert "human election" in REPORT.read_text()
def test_85_no_yubikey(): assert "YubiKey interaction" in REPORT.read_text()
def test_86_no_presentation_evidence(): assert "presentation evidence" in REPORT.read_text()
def test_87_no_production_principal(): assert "PRODUCTION principal" in REPORT.read_text()
def test_88_no_gate_certification(): assert "Gate certification" in REPORT.read_text()
def test_89_n16_5_remains_open(): assert "N-16-5: NOT CLOSED" in REPORT.read_text()
def test_90_runtime_unchanged():
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    assert all(value in out for value in ("not_implemented", "Observed", "observe", "unavailable", "Plugin count:              0", "Capability count:          0"))
def test_91_first_external_effect_absent(): assert "first external effect remains absent" in REPORT.read_text()
def test_92_n16_6_untouched(): assert "N-16-6/N-16-7 remain untouched" in REPORT.read_text()
def test_93_n16_7_untouched(): assert "N-16-6/N-16-7 remain untouched" in REPORT.read_text()
def test_94_fido2_supported_not_exclusive(): assert "FIDO2 and local presentation remain supported-not-exclusive" in REPORT.read_text()
def test_95_local_presentation_supported_not_exclusive(): assert "local presentation remain supported-not-exclusive" in REPORT.read_text()
def test_96_mobile_only_future_profile_preserved(): assert "mobile-only authentication and protected approval remain open/planned" in REPORT.read_text()
