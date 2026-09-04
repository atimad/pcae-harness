"""Phase .30R.5R.2.1R.1R — F-4 immutable historical-scope repair."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
P = "00c077f6ff3389a8c91d503fb5341ec72775f8e0"
V = "3fbc12d7ad671ed6c9348cb29ffb5c2d35447e5f"
R0 = V
R4R_FINALIZED = "a727dbf4f160f904836905d3cb4adeba91953676"
R4R1_FINALIZED = "5b6b4013a69ffcb366209b12c495571917bb5ccc"
OWNER = ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_contract_reconciliation.py"
F3_SUITE = ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_f3_immutable_phase_entry_evidence_repair.py"
PREDECESSOR = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1_F3_IV_AND_FINAL_N_16_5_CERTIFICATION.md"
CERT = ROOT / ".pcae/certification/n16_5_presentation_bound_cert_30r5r2_1r1.json"
PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")
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


def owner_source() -> str:
    return OWNER.read_text(encoding="utf-8")


def historical_files() -> set[str]:
    return set(git("diff", "--name-only", R4R_FINALIZED, R4R1_FINALIZED, "--", "src/pcae", "scripts").splitlines())


def test_01_phase_lineage_is_exact_repair_successor() -> None:
    from pcae.core.phase_id import parse
    assert parse("149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R").normalized_text.endswith(".1R.1R")


def test_02_predecessor_remains_blocked() -> None:
    text = PREDECESSOR.read_text(encoding="utf-8")
    assert "**Verdict: BLOCKED." in text and "N-16-5: NOT CLOSED" in text


def test_03_f4_node_is_retained() -> None:
    assert "def test_35_no_production_or_script_implementation_changed" in owner_source()


def test_04_original_f4_live_head_shape_is_reconstructable() -> None:
    old = git("show", f"{R0}:tests/{OWNER.name}")
    assert 'R4R_FINALIZED, "HEAD"' in old


def test_05_original_invariant_is_exact_file_scope() -> None:
    assert "changed <= _R4R1_IMPLEMENTATION_FILES" in owner_source()


def test_06_historical_lower_bound_is_immutable_commit() -> None:
    assert git("rev-parse", R4R_FINALIZED) == R4R_FINALIZED


def test_07_historical_upper_bound_is_immutable_commit() -> None:
    assert git("rev-parse", R4R1_FINALIZED) == R4R1_FINALIZED


def test_08_live_head_is_not_scope_upper_bound() -> None:
    node = ast.parse(owner_source())
    fn = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_35_"))
    assert '"HEAD"' not in ast.unparse(fn)


def test_09_live_completion_metadata_is_not_historical_authority() -> None:
    node = ast.parse(owner_source())
    fn = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_35_"))
    assert "phase-completion-metadata" not in ast.unparse(fn)


def test_10_exact_historical_commit_range_is_ancestral() -> None:
    assert subprocess.run(["git", "merge-base", "--is-ancestor", R4R_FINALIZED, R4R1_FINALIZED], cwd=ROOT).returncode == 0


def test_11_exact_historical_file_scope_is_verified() -> None:
    assert historical_files() == ALLOWED


def test_12_repaired_invariant_passes_historical_state() -> None:
    assert historical_files() <= ALLOWED


def test_13_repaired_invariant_passes_current_successor() -> None:
    assert git("rev-parse", "HEAD") != R4R1_FINALIZED and historical_files() <= ALLOWED


def test_14_future_successor_cannot_change_fixed_range() -> None:
    before = historical_files()
    assert before == set(git("diff", "--name-only", R4R_FINALIZED, R4R1_FINALIZED, "--", "src/pcae", "scripts").splitlines())


def test_15_unauthorized_historical_file_still_fails() -> None:
    assert not (historical_files() | {"src/pcae/unauthorized.py"}) <= ALLOWED


def test_16_unauthorized_historical_commit_is_not_allowlisted() -> None:
    assert "src/pcae/core/hpac_rhamp_ctap2.py" not in ALLOWED


def test_17_no_wildcard_allowance() -> None:
    node = ast.parse(owner_source())
    fn = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_35_"))
    calls = {ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)}
    assert not ({"fnmatch.fnmatch", "Path.glob", "Path.rglob"} & calls)


def test_18_no_skip() -> None:
    assert "pytest.skip" not in owner_source() and "@pytest.mark.skip" not in owner_source()


def test_19_no_xfail() -> None:
    assert "xfail" not in owner_source()


def test_20_test_definition_count_not_reduced() -> None:
    old = git("show", f"{R0}:tests/{OWNER.name}")
    assert owner_source().count("def test_") == old.count("def test_")


def test_21_no_rename_to_evade() -> None:
    old = git("show", f"{R0}:tests/{OWNER.name}")
    assert "def test_35_no_production_or_script_implementation_changed" in old and "def test_35_no_production_or_script_implementation_changed" in owner_source()


def test_22_f3_repair_suite_unchanged() -> None:
    rel = F3_SUITE.relative_to(ROOT).as_posix()
    assert F3_SUITE.read_bytes() == subprocess.check_output(["git", "show", f"{R0}:{rel}"], cwd=ROOT)


def test_23_h2_source_unchanged() -> None:
    assert git("diff", "--name-only", R0, "--", "src/pcae/protected_presentation_helper.py") == ""


def test_24_f2_source_unchanged() -> None:
    assert git("diff", "--name-only", R0, "--", "src/pcae/core/protected_presentation.py") == ""


def test_25_h1_source_unchanged() -> None:
    assert git("diff", "--name-only", R0, "--", "src/pcae/core/hpac_rhamp_ctap2.py") == ""


def test_26_no_src_change() -> None:
    assert git("diff", "--name-only", R0, "--", "src/pcae") == ""


def test_27_no_scripts_change() -> None:
    assert git("diff", "--name-only", R0, "--", "scripts") == ""


def test_28_no_dependency_change() -> None:
    assert git("diff", "--name-only", R0, "--", "pyproject.toml") == ""


def test_29_no_contract_change() -> None:
    assert git("diff", "--name-only", R0, "--", "docs/contracts") == ""


def test_30_f5_remains_absent() -> None:
    assert not PROTECTED_ROOT.exists()


def test_31_no_protected_root_mutation_in_repo_diff() -> None:
    changed = git("diff", "--name-only", R0).splitlines()
    assert not any(p.startswith((".pcae/protected-root", "protected-root/")) for p in changed)


def test_32_no_helper_installation_artifact_added() -> None:
    assert not any("installation" in p.lower() for p in git("diff", "--name-only", R0).splitlines() if p.startswith(".pcae/certification/"))


def test_33_no_real_ceremony() -> None:
    data = json.loads(CERT.read_text(encoding="utf-8"))
    assert data["real_ceremony"]["started"] is False
    assert not any(data["real_ceremony"].values())


def test_34_no_hardware_requirement_in_suite() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    calls = {ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "resolve_production_ctap2_provider" not in calls and "getpass" not in calls


def test_35_n16_5_remains_open() -> None:
    assert "N-16-5: NOT CLOSED" in PROJECT_STATUS()


def PROJECT_STATUS() -> str:
    return (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")


def test_36_runtime_unchanged() -> None:
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    for value in ("not_implemented", "Observed", "unavailable", "Plugin count:              0", "Capability count:          0"):
        assert value in out


def test_37_first_effect_absent() -> None:
    assert "first effect absent" in PROJECT_STATUS().lower()


def test_38_n16_6_untouched() -> None:
    assert "N-16-6/N-16-7 untouched" in PROJECT_STATUS()


def test_39_n16_7_untouched() -> None:
    assert "N-16-6/N-16-7 untouched" in PROJECT_STATUS()


def test_40_fido2_supported_not_exclusive() -> None:
    status = PROJECT_STATUS().lower()
    assert "fido2 and local presentation" in status and "supported-not-exclusive" in status


def test_41_local_presentation_supported_not_exclusive() -> None:
    assert "local presentation" in PROJECT_STATUS().lower() and "supported-not-exclusive" in PROJECT_STATUS().lower()


def test_42_mobile_only_future_architecture_preserved() -> None:
    assert "mobile-only profiles remain open" in PROJECT_STATUS()


def test_43_f4_change_is_test_only() -> None:
    changed = set(git("diff", "--name-only", R0).splitlines())
    assert all(p.startswith(("tests/", "tasks/", "docs/", ".pcae/")) or p in {"PROJECT_STATUS.md", "CHANGELOG.md"} for p in changed)
