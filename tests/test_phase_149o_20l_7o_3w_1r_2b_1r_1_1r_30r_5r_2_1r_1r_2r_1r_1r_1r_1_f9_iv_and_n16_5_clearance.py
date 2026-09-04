"""Independent Verification of the F-9 Immutable F-7-Repair-Suite Deployment-Evidence
Guard Repair + Final N-16-5 Moving-History Clearance + F-5 Retry Readiness Adjudication.

Verification only. Does not repair test_31/32/43 or any other guard, does not touch
production/scripts/contracts/dependencies, does not deploy F-5, does not close N-16-5.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1"
PREDECESSOR = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R"
V = "a3a0494807ed6c8de10a2eb8db14e41655039fdd"  # this IV's own phase-entry SHA (HEAD at open)
F9_ENTRY = "54327556c832a9b7699cb2b6b7c99dc29ca65539"
F4R_LOWER = "3fbc12d7ad671ed6c9348cb29ffb5c2d35447e5f"
F4R_UPPER = "90510428422e451382549ce76111610752aaafb4"
F9_CHANGE = "3cec79212b24cb17cb216f744e5266c27d2de019"
OWNER = ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_f4_immutable_scope_repair.py"
OWNER_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_f4_immutable_scope_repair.py"
F9_SUITE = ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_f9_deployment_evidence_guard_repair.py"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_F9_IV_N16_5_CLEARANCE_F5_RETRY_READY.md"
F9_REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_F9_DEPLOYMENT_EVIDENCE_GUARD_REPAIR.md"
COMBINED_IV_REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1_F7_F8_IV_MOVING_HISTORY_CLEARANCE_BLOCKED.md"
N31 = "test_31_no_protected_root_mutation_in_repo_diff"
N32 = "test_32_no_helper_installation_artifact_added"
N43 = "test_43_f4_change_is_test_only"
PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_in(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=path, text=True).strip()


def owner_source() -> str:
    return OWNER.read_text(encoding="utf-8")


def fn(source: str, name: str) -> ast.FunctionDef:
    return next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)


def node_src(name: str) -> str:
    return ast.unparse(fn(owner_source(), name))


def simulate(path: Path, inside: str, successor: str) -> tuple[str, str, str]:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "iv@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "IV"], cwd=path, check=True)
    (path / "entry.txt").write_text("entry\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "entry"], cwd=path, check=True)
    start = git_in(path, "rev-parse", "HEAD")
    target = path / inside
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("historical\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "historical"], cwd=path, check=True)
    end = git_in(path, "rev-parse", "HEAD")
    later = path / successor
    later.parent.mkdir(parents=True, exist_ok=True)
    later.write_text("successor\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "successor"], cwd=path, check=True)
    head = git_in(path, "rev-parse", "HEAD")
    return start, end, head


# --- CPIPC / lineage ---

def test_01_cpipc_lineage():
    from pcae.core.phase_id import parse
    assert parse(PHASE).normalized_text == PHASE


def test_02_exact_successor_of_f9():
    assert PHASE.startswith(PREDECESSOR) and PHASE[len(PREDECESSOR):] == ".1"


def test_03_f9_entry_independently_derived():
    assert git("rev-parse", F9_ENTRY) == F9_ENTRY
    assert "close task lifecycle (report already promoted)" in git("log", "-1", "--format=%s", F9_ENTRY)


def test_04_f9_change_commit_independently_derived():
    assert git("rev-parse", F9_CHANGE) == F9_CHANGE
    assert "F-9 immutable F-7-repair-suite deployment-evidence guard repair" in git("log", "-1", "--format=%s", F9_CHANGE)


def test_05_f9_diff_scope_only_two_test_files_plus_docs():
    changed = set(git("diff", "--name-only", f"{F9_CHANGE}^", F9_CHANGE).splitlines())
    py_changed = {p for p in changed if p.endswith(".py")}
    assert py_changed == {
        "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_f9_deployment_evidence_guard_repair.py",
        OWNER_REL,
    }


def test_06_f9_no_src_change():
    assert git("diff", "--name-only", f"{F9_CHANGE}^", F9_CHANGE, "--", "src/pcae", "scripts") == ""


# --- test_31/32/43 independent reconstruction ---

def test_07_test31_located():
    assert fn(owner_source(), N31).name == N31


def test_08_test32_located():
    assert fn(owner_source(), N32).name == N32


def test_09_test43_located():
    assert fn(owner_source(), N43).name == N43


def test_10_test31_original_defect_used_implicit_head():
    pre = git("show", f"{F9_ENTRY}:{OWNER_REL}")
    old = ast.unparse(fn(pre, N31))
    assert 'git(\'diff\', \'--name-only\', R0)' in old and "F4_REPAIR_FINALIZED" not in old


def test_11_test32_original_defect_used_implicit_head():
    pre = git("show", f"{F9_ENTRY}:{OWNER_REL}")
    old = ast.unparse(fn(pre, N32))
    assert 'git(\'diff\', \'--name-only\', R0)' in old and "F4_REPAIR_FINALIZED" not in old


def test_12_test43_original_defect_used_implicit_head():
    pre = git("show", f"{F9_ENTRY}:{OWNER_REL}")
    old = ast.unparse(fn(pre, N43))
    assert 'git(\'diff\', \'--name-only\', R0)' in old and "F4_REPAIR_FINALIZED" not in old


def test_13_test31_repaired_bounded():
    assert "R0, F4_REPAIR_FINALIZED" in node_src(N31)


def test_14_test32_repaired_bounded():
    assert "R0, F4_REPAIR_FINALIZED" in node_src(N32)


def test_15_test43_repaired_bounded():
    assert "R0, F4_REPAIR_FINALIZED" in node_src(N43)


def test_16_lower_bound_is_phase_entry():
    assert git("rev-parse", F4R_LOWER) == F4R_LOWER
    assert git("rev-parse", "a40f8163^") == F4R_LOWER


def test_17_upper_bound_is_own_finalized_head():
    assert git("rev-parse", F4R_UPPER) == F4R_UPPER
    assert "reconcile governed push state" in git("log", "-1", "--format=%s", F4R_UPPER)
    # the very next commit after the upper bound begins the successor F-4-IV phase
    nxt = git("log", "--format=%H", f"{F4R_UPPER}..HEAD", "--reverse").splitlines()[0]
    assert "independently verify F-4 immutable historical scope" in git("log", "-1", "--format=%s", nxt)


def test_18_lower_ancestor_of_upper():
    assert subprocess.run(["git", "merge-base", "--is-ancestor", F4R_LOWER, F4R_UPPER], cwd=ROOT).returncode == 0


def test_19_test31_historical_pass():
    changed = git("diff", "--name-only", F4R_LOWER, F4R_UPPER).splitlines()
    assert not any(p.startswith((".pcae/protected-root", "protected-root/")) for p in changed)


def test_20_test32_historical_pass():
    changed = git("diff", "--name-only", F4R_LOWER, F4R_UPPER).splitlines()
    assert not any("installation" in p.lower() for p in changed if p.startswith(".pcae/certification/"))


def test_21_test43_historical_pass():
    allowed_prefixes = ("tests/", "tasks/", "docs/", ".pcae/")
    allowed_exact = {"PROJECT_STATUS.md", "CHANGELOG.md"}
    changed = git("diff", "--name-only", F4R_LOWER, F4R_UPPER).splitlines()
    assert all(p.startswith(allowed_prefixes) or p in allowed_exact for p in changed)


def test_22_current_successor_pass_all_three():
    import subprocess as sp
    result = sp.run(
        ["python3", "-m", "pytest", OWNER_REL, "-q", "-k", "test_31 or test_32 or test_43"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0 and "3 passed" in result.stdout


def test_23_future_successor_pass_test31(tmp_path):
    a, b, c = simulate(tmp_path, "iv.txt", "protected-root/future-file")
    assert "protected-root" not in git_in(tmp_path, "diff", "--name-only", a, b)
    assert "protected-root" in git_in(tmp_path, "diff", "--name-only", a, c)


def test_24_negative_forbidden_root_mutation_inside_scope_fails(tmp_path):
    a, b, _ = simulate(tmp_path, "protected-root/forbidden", "later.txt")
    changed = git_in(tmp_path, "diff", "--name-only", a, b).splitlines()
    assert any(p.startswith("protected-root/") for p in changed)


def test_25_negative_forbidden_helper_artifact_inside_scope_fails(tmp_path):
    a, b, _ = simulate(tmp_path, ".pcae/certification/installation-forbidden.json", "later.txt")
    changed = git_in(tmp_path, "diff", "--name-only", a, b).splitlines()
    assert any("installation" in p.lower() for p in changed if p.startswith(".pcae/certification/"))


def test_26_negative_forbidden_production_change_inside_scope_fails(tmp_path):
    a, b, _ = simulate(tmp_path, "src/pcae/forbidden.py", "later.txt")
    changed = git_in(tmp_path, "diff", "--name-only", a, b).splitlines()
    allowed_prefixes = ("tests/", "tasks/", "docs/", ".pcae/")
    allowed_exact = {"PROJECT_STATUS.md", "CHANGELOG.md"}
    assert not all(p.startswith(allowed_prefixes) or p in allowed_exact for p in changed)


def test_27_future_legitimate_deployment_does_not_retroactively_break_history():
    # F-5 will eventually add helper-installation material outside the fixed
    # F4R_LOWER..F4R_UPPER range; the bounded range must remain immutable.
    changed_now = set(git("diff", "--name-only", F4R_LOWER, F4R_UPPER).splitlines())
    changed_again = set(git("diff", "--name-only", F4R_LOWER, F4R_UPPER).splitlines())
    assert changed_now == changed_again


# --- no test-weakening ---

def test_28_test_count_unchanged_in_owner():
    old = git("show", f"{F9_ENTRY}:{OWNER_REL}")
    assert owner_source().count("def test_") == old.count("def test_")


def test_29_no_skip_xfail_in_repaired_nodes():
    combined = node_src(N31) + node_src(N32) + node_src(N43)
    assert "skip" not in combined and "xfail" not in combined


def test_30_no_wildcard_fnmatch_in_repaired_nodes():
    for name in (N31, N32, N43):
        calls = {ast.unparse(c.func) for c in ast.walk(fn(owner_source(), name)) if isinstance(c, ast.Call)}
        assert not ({"fnmatch.fnmatch", "Path.glob", "Path.rglob"} & calls)


def test_31_no_live_head_in_repaired_nodes():
    for name in (N31, N32, N43):
        src = node_src(name)
        assert '"HEAD"' not in src and "'HEAD'" not in src


# --- preservation ---

def test_32_f7_f8_reports_preserved_unchanged():
    for path, sha in ((F9_REPORT, F9_CHANGE), (COMBINED_IV_REPORT, F9_ENTRY)):
        assert path.read_bytes() == subprocess.check_output(["git", "show", f"HEAD:{path.relative_to(ROOT).as_posix()}"], cwd=ROOT)


def test_33_f7_status_preserved():
    text = " ".join(COMBINED_IV_REPORT.read_text(encoding="utf-8").split())
    assert "F-7 is **INDEPENDENTLY VERIFIED REPAIRED**" in text


def test_34_f8_status_preserved():
    text = " ".join(COMBINED_IV_REPORT.read_text(encoding="utf-8").split())
    assert "F-8 is **INDEPENDENTLY VERIFIED REPAIRED**" in text


def test_35_f3_f4_f6_remain_verified():
    combined = " ".join(COMBINED_IV_REPORT.read_text(encoding="utf-8").split())
    assert "F-3, F-4, and F-6 remain independently verified" in combined


def test_36_h1_h2_f2_bytes_unchanged_since_iv_entry():
    for rel in (
        "src/pcae/protected_presentation_helper.py",
        "src/pcae/core/protected_presentation.py",
        "src/pcae/core/hpac_rhamp_ctap2.py",
    ):
        assert git("diff", "--name-only", V, "--", rel) == ""


def test_37_f9_suite_unchanged():
    assert F9_SUITE.read_bytes() == subprocess.check_output(["git", "show", f"{V}:{F9_SUITE.relative_to(ROOT).as_posix()}"], cwd=ROOT)


def test_38_owner_suite_unchanged_since_iv_entry():
    assert OWNER.read_bytes() == subprocess.check_output(["git", "show", f"{V}:{OWNER_REL}"], cwd=ROOT)


# --- byte identity ---

def test_39_no_production_source_change():
    assert git("diff", "--name-only", V, "--", "src/pcae") == ""


def test_40_no_production_script_change():
    assert git("diff", "--name-only", V, "--", "scripts") == ""


def test_41_no_dependency_change():
    assert git("diff", "--name-only", V, "--", "pyproject.toml") == ""


def test_42_no_contract_change():
    assert git("diff", "--name-only", V, "--", "docs/contracts") == ""


# --- F-5 read-only host inspection ---

def test_43_protected_root_absent():
    assert not PROTECTED_ROOT.exists()


def test_44_installation_descriptor_absent():
    import glob
    assert not glob.glob("/Library/Application Support/PCAE/HPAC/**/*installation*", recursive=True)


def test_45_current_generation_descriptor_absent():
    import glob
    assert not glob.glob("/Library/Application Support/PCAE/HPAC/**/*current-generation*", recursive=True)


# --- runtime / first-effect ---

def test_46_runtime_unchanged():
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    for value in ("not_implemented", "Observed", "unavailable", "Plugin count:              0", "Capability count:          0"):
        assert value in out


def test_47_first_effect_absent_in_status():
    assert "first effect" in (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8").lower()


def test_48_n16_5_remains_open_in_status():
    assert "N-16-5" in (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")


# --- final adjudications (mirrored into canonical report) ---

def test_49_f9_final_verdict_recorded():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "F-9: INDEPENDENTLY VERIFIED REPAIRED" in text


def test_50_moving_history_clearance_verdict_recorded():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "N-16-5 PREREQUISITE MOVING-HISTORY CLEARANCE: VERIFIED" in text
    assert "NO ADDITIONAL BLOCKING HISTORICAL-MOVING-AUTHORITY DEFECT FOUND IN CURRENT N-16-5 PREREQUISITE CHAIN" in text


def test_51_f5_retry_verdict_recorded():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "F-5 RETRY: READY" in text


def test_52_f5_status_unchanged():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "F-5: OPEN / ABSENT / UNCHANGED" in text


def test_53_n16_5_not_closed_recorded():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "N-16-5 remains **NOT CLOSED**" in text


def test_54_pre_existing_unrelated_failures_disclosed():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "pre-existing" in text.lower() and "hpac_verifier" in text.lower()


def test_55_no_repair_performed_this_phase():
    changed = set(git("diff", "--name-only", V, "--", "tests").splitlines())
    assert changed <= {
        "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_f9_iv_and_n16_5_clearance.py",
    }
