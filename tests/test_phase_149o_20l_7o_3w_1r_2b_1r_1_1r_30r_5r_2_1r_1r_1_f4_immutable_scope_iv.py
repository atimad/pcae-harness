"""Independent verification for the F-4 immutable historical-scope repair."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.1"
P = "3fbc12d7ad671ed6c9348cb29ffb5c2d35447e5f"
R = "90510428422e451382549ce76111610752aaafb4"
V = R
F4_IV_FINALIZED = "7124c019bf3f46eb07456b81146484609197dbc2"
L = "a727dbf4f160f904836905d3cb4adeba91953676"
U = "5b6b4013a69ffcb366209b12c495571917bb5ccc"
OPEN = "99bc57053947b192592c2c7378fd11e66660c60c"
IMPLEMENT = "25351fb885d2b4d10512f8e7ae2044a164a399c4"
CLOSE = "4d0cdf20c5414191163f132e6da1c4f31fc2d1e2"
STAGE = "f5a52e2a38fc02e197dfde4228df715ceb5c4c8e"
NEXT = "0a5cc6545d95c6ff5f5f0c179d209c5768c6621f"
OWNER_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_contract_reconciliation.py"
OWNER = ROOT / OWNER_REL
REPAIR_SUITE = ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_f4_immutable_scope_repair.py"
F3_SUITE = ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_f3_immutable_phase_entry_evidence_repair.py"
BLOCKED_REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1_F3_IV_AND_FINAL_N_16_5_CERTIFICATION.md"
REPAIR_REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_F4_IMMUTABLE_HISTORICAL_SCOPE_GUARD_REPAIR.md"
CERT = ROOT / ".pcae/certification/n16_5_presentation_bound_cert_30r5r2_1r1.json"
PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")
PHASE_COMMITS = [OPEN, IMPLEMENT, CLOSE, STAGE, U]
ALLOWED = {
    "scripts/hpac_protected_presentation_admin.py",
    "src/pcae/core/approval_presentation.py",
    "src/pcae/core/hpac_protected_admin_writer.py",
    "src/pcae/core/hpac_protected_presentation_admin.py",
    "src/pcae/core/hpac_verifier.py",
    "src/pcae/core/protected_presentation.py",
    "src/pcae/core/protected_presentation_installation.py",
    "src/pcae/protected_presentation_helper.py",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def show(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}")


def owner_at(commit: str) -> str:
    return show(commit, OWNER_REL)


def f4_node(source: str) -> ast.FunctionDef:
    return next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef)
        and node.name == "test_35_no_production_or_script_implementation_changed"
    )


def historical_files() -> set[str]:
    return set(git("diff", "--name-only", L, U, "--", "src/pcae", "scripts").splitlines())


def metadata_at(commit: str) -> dict[str, object]:
    return json.loads(show(commit, ".pcae/phase-completion-metadata.json"))


def test_01_phase_lineage_is_exact() -> None:
    from pcae.core.phase_id import parse
    assert parse(PHASE).normalized_text == PHASE


def test_02_predecessor_repair_phase_is_completed() -> None:
    assert metadata_at(R)["phase_id"].endswith(".1R.1R")
    assert metadata_at(R)["status"] == "completed"


def test_03_historical_blocked_certification_is_preserved() -> None:
    text = BLOCKED_REPORT.read_text()
    assert "**Verdict: BLOCKED." in text and "F-4" in text


def test_04_p_r_v_are_independently_resolved() -> None:
    assert [git("rev-parse", value) for value in (P, R, V)] == [P, R, V]
    assert git("merge-base", "--is-ancestor", P, R) == ""


def test_05_exact_f4_node_is_retained() -> None:
    assert f4_node(OWNER.read_text()).name.endswith("implementation_changed")


def test_06_pre_repair_f4_is_reconstructed() -> None:
    old = ast.unparse(f4_node(owner_at(P)))
    assert "R4R_FINALIZED, 'HEAD'" in old


def test_07_pre_repair_also_had_implicit_head() -> None:
    old = ast.unparse(f4_node(owner_at(P)))
    assert "['git', 'diff', '--name-only', R4R_FINALIZED, '--'" in old


def test_08_original_invariant_is_exact_subset_scope() -> None:
    assert "changed <= _R4R1_IMPLEMENTATION_FILES" in ast.unparse(f4_node(owner_at(P)))


def test_09_lower_bound_is_exact_git_object() -> None:
    assert git("rev-parse", f"{OPEN}^") == L


def test_10_lower_bound_metadata_identifies_30r4() -> None:
    data = metadata_at(L)
    assert data["phase_id"].endswith(".30R.4R") and data["status"] == "completed"


def test_11_upper_bound_is_exact_git_object() -> None:
    assert git("rev-parse", U) == U


def test_12_upper_bound_metadata_identifies_30r4r1() -> None:
    data = metadata_at(U)
    assert data["phase_id"].endswith(".30R.4R.1") and data["status"] == "completed"


def test_13_upper_metadata_records_entry_lower_bound() -> None:
    assert f"A={L}" in str(metadata_at(U)["validation_results"])


def test_14_exact_historical_commit_set_is_five_linear_commits() -> None:
    assert git("rev-list", "--first-parent", "--reverse", f"{L}..{U}").splitlines() == PHASE_COMMITS


def test_15_each_historical_commit_is_in_phase_lineage() -> None:
    subjects = [git("show", "-s", "--format=%s", c) for c in PHASE_COMMITS]
    assert all("149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1" in s for s in subjects)


def test_16_immediate_successor_is_excluded() -> None:
    children = git("rev-list", "--children", "--all").splitlines()
    row = next(line for line in children if line.startswith(U + " "))
    assert row.split()[1] == NEXT and NEXT not in PHASE_COMMITS


def test_17_exact_historical_file_scope_is_eight_files() -> None:
    assert historical_files() == ALLOWED


def test_18_repaired_node_uses_claimed_fixed_bounds() -> None:
    current = ast.unparse(f4_node(OWNER.read_text()))
    assert current.count("R4R_FINALIZED, R4R1_FINALIZED") == 2


def test_19_live_head_is_not_historical_authority() -> None:
    assert "'HEAD'" not in ast.unparse(f4_node(OWNER.read_text()))


def test_20_live_origin_main_is_not_historical_authority() -> None:
    assert "origin/main" not in ast.unparse(f4_node(OWNER.read_text()))


def test_21_live_completion_metadata_is_not_authority() -> None:
    assert "phase-completion-metadata" not in ast.unparse(f4_node(OWNER.read_text()))


def test_22_project_status_is_not_historical_authority() -> None:
    assert "PROJECT_STATUS" not in ast.unparse(f4_node(OWNER.read_text()))


def test_23_historical_state_evaluation_passes() -> None:
    assert historical_files() <= ALLOWED


def test_24_current_successor_evaluation_passes() -> None:
    assert git("rev-parse", "HEAD") != U and historical_files() <= ALLOWED


def test_25_future_successor_cannot_change_fixed_trees() -> None:
    before = git("diff-tree", "-r", "--no-commit-id", "--name-only", L, U, "--", "src/pcae", "scripts")
    assert before.splitlines() == sorted(ALLOWED)


def test_26_unauthorized_historical_source_change_fails() -> None:
    assert not (historical_files() | {"src/pcae/unauthorized.py"}) <= ALLOWED


def test_27_unauthorized_historical_commit_fails_scope() -> None:
    later = "src/pcae/core/hpac_rhamp_ctap2.py"
    assert later in git("diff", "--name-only", L, "0972daab", "--", "src/pcae", "scripts").splitlines()
    assert not (historical_files() | {later}) <= ALLOWED


def test_28_no_current_head_special_case() -> None:
    source = ast.unparse(f4_node(OWNER.read_text()))
    assert "current_head" not in source and "if HEAD" not in source


def test_29_no_wildcard_or_path_prefix_broadening() -> None:
    calls = {ast.unparse(n.func) for n in ast.walk(f4_node(OWNER.read_text())) if isinstance(n, ast.Call)}
    assert not ({"fnmatch.fnmatch", "Path.glob", "Path.rglob"} & calls)


def test_30_no_test_removal() -> None:
    assert OWNER.read_text().count("def test_") == owner_at(P).count("def test_")


def test_31_no_rename_to_evade() -> None:
    name = "def test_35_no_production_or_script_implementation_changed"
    assert name in owner_at(P) and name in OWNER.read_text()


def test_32_no_skip_skipif_pytest_skip_or_xfail() -> None:
    source = ast.unparse(f4_node(OWNER.read_text())).lower()
    assert all(token not in source for token in ("pytest.skip", "skipif", "xfail"))


def test_33_f3_suite_is_byte_unchanged_by_repair() -> None:
    rel = F3_SUITE.relative_to(ROOT).as_posix()
    assert F3_SUITE.read_bytes() == subprocess.check_output(["git", "show", f"{P}:{rel}"], cwd=ROOT)


def test_34_h2_source_bytes_are_unchanged() -> None:
    assert git("diff", "--name-only", P, R, "--", "src/pcae/protected_presentation_helper.py") == ""


def test_35_f2_source_bytes_are_unchanged() -> None:
    assert git("diff", "--name-only", P, R, "--", "src/pcae/core/protected_presentation.py") == ""


def test_36_h1_source_bytes_are_unchanged() -> None:
    assert git("diff", "--name-only", P, R, "--", "src/pcae/core/hpac_rhamp_ctap2.py") == ""


def test_37_no_production_source_changed_in_repair() -> None:
    assert git("diff", "--name-only", P, R, "--", "src/pcae") == ""


def test_38_no_production_script_changed_in_repair() -> None:
    assert git("diff", "--name-only", P, R, "--", "scripts") == ""


def test_39_no_dependency_changed_in_repair() -> None:
    assert git("diff", "--name-only", P, R, "--", "pyproject.toml") == ""


def test_40_no_contract_changed_in_repair() -> None:
    assert git("diff", "--name-only", P, R, "--", "docs/contracts") == ""


def test_41_repair_diff_is_verification_and_lifecycle_only() -> None:
    changed = set(git("diff", "--name-only", P, R).splitlines())
    assert all(path.startswith(("tests/", "docs/", "tasks/", ".pcae/")) or path in {"PROJECT_STATUS.md", "CHANGELOG.md"} for path in changed)


def test_42_f5_protected_root_remains_absent() -> None:
    assert not PROTECTED_ROOT.exists()


def test_43_no_protected_root_mutation_is_in_iv_diff() -> None:
    assert not any(
        "protected-root" in p
        for p in git("diff", "--name-only", V, F4_IV_FINALIZED).splitlines()
    )


def test_44_no_helper_installation_or_pawa_write_in_iv() -> None:
    changed = git("diff", "--name-only", V).splitlines()
    assert not any(p.startswith(("src/pcae", "scripts/", ".pcae/certification/")) for p in changed)


def test_45_no_real_helper_ceremony_or_human_election() -> None:
    ceremony = json.loads(CERT.read_text())["real_ceremony"]
    assert ceremony["started"] is False and not any(ceremony.values())


def test_46_no_yubikey_or_certification_evidence_minted() -> None:
    assert git("diff", "--name-only", V, "--", ".pcae/certification") == ""


def test_47_n16_5_remains_not_closed() -> None:
    assert "N-16-5: NOT CLOSED" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_48_runtime_remains_observed_and_unavailable() -> None:
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    for value in ("not_implemented", "Observed", "observe", "unavailable", "Plugin count:              0", "Capability count:          0"):
        assert value in out


def test_49_first_external_effect_remains_absent() -> None:
    assert "first effect absent" in (ROOT / "PROJECT_STATUS.md").read_text().lower()


def test_50_n16_6_remains_untouched() -> None:
    assert "N-16-6/N-16-7 untouched" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_51_n16_7_remains_untouched() -> None:
    assert "N-16-6/N-16-7 untouched" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_52_fido2_is_supported_not_exclusive() -> None:
    status = (ROOT / "PROJECT_STATUS.md").read_text().lower()
    assert "fido2 and local presentation" in status and "supported-not-exclusive" in status


def test_53_local_presentation_is_supported_not_exclusive() -> None:
    status = (ROOT / "PROJECT_STATUS.md").read_text().lower()
    assert "local presentation" in status and "supported-not-exclusive" in status


def test_54_mobile_only_future_architecture_is_preserved() -> None:
    assert "mobile-only profiles remain open" in (ROOT / "PROJECT_STATUS.md").read_text()


def test_55_repair_report_does_not_claim_f5_or_n16_5_completion() -> None:
    text = REPAIR_REPORT.read_text()
    assert "F-5 remains read-only and untouched" in text and "N-16-5 remains NOT CLOSED" in text


def test_56_iv_changes_no_product_contract_or_dependency_bytes() -> None:
    assert git("diff", "--name-only", V, "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts") == ""
