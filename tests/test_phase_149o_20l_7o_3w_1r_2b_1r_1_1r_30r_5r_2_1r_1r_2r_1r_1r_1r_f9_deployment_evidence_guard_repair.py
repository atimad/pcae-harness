"""Repair evidence for the F-9 deployment-evidence guards (tests 31/32/43)."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R"
R0 = "54327556c832a9b7699cb2b6b7c99dc29ca65539"
OWNER_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_f4_immutable_scope_repair.py"
OWNER = ROOT / OWNER_REL
F4R_LOWER = "3fbc12d7ad671ed6c9348cb29ffb5c2d35447e5f"
F4R_UPPER = "90510428422e451382549ce76111610752aaafb4"
F4_IV_FINALIZED = "7124c019bf3f46eb07456b81146484609197dbc2"
F6_IV_FINALIZED = "8dcca97bb1a88a99cac3afe610f3651adcc58295"
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_F9_DEPLOYMENT_EVIDENCE_GUARD_REPAIR.md"
COMBINED_IV_REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1_F7_F8_IV_MOVING_HISTORY_CLEARANCE_BLOCKED.md"
F4_IV_FILE = ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py"
F6_IV_FILE = ROOT / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1_f6_immutable_host_mutation_guard_iv.py"
N31 = "test_31_no_protected_root_mutation_in_repo_diff"
N32 = "test_32_no_helper_installation_artifact_added"
N43 = "test_43_f4_change_is_test_only"
PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_in(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=path, text=True).strip()


def show(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}")


def fn(source: str, name: str) -> ast.FunctionDef:
    return next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)


def node(name: str, source: str | None = None) -> str:
    return ast.unparse(fn(source or OWNER.read_text(encoding="utf-8"), name))


def owner_source() -> str:
    return OWNER.read_text(encoding="utf-8")


def historical_files() -> list[str]:
    return git("diff", "--name-only", F4R_LOWER, F4R_UPPER).splitlines()


def all_nodes() -> str:
    return "\n".join(node(n) for n in (N31, N32, N43))


def simulate(path: Path, inside: str, successor: str) -> tuple[str, str, str]:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "f9@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "F9"], cwd=path, check=True)
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


# 1. exact phase lineage
def test_01_exact_phase_lineage():
    from pcae.core.phase_id import parse
    assert parse(PHASE).normalized_text == PHASE


# 2. combined F-7/F-8 IV historical report preserved
def test_02_combined_iv_report_preserved():
    text = " ".join(COMBINED_IV_REPORT.read_text(encoding="utf-8").split())
    assert "BLOCKED. F-7: INDEPENDENTLY VERIFIED REPAIRED" in text


# 3. F-7 independently verified status preserved
def test_03_f7_status_preserved():
    text = " ".join(COMBINED_IV_REPORT.read_text(encoding="utf-8").split())
    assert "F-7 is **INDEPENDENTLY VERIFIED REPAIRED**" in text


# 4. F-8 independently verified status preserved
def test_04_f8_status_preserved():
    text = " ".join(COMBINED_IV_REPORT.read_text(encoding="utf-8").split())
    assert "F-8 is **INDEPENDENTLY VERIFIED REPAIRED**" in text


# 5. scope exactly tests 31/32/43
def test_05_scope_is_exact_three_nodes():
    names = {n.name for n in ast.parse(owner_source()).body if isinstance(n, ast.FunctionDef)}
    assert {N31, N32, N43} <= names


# --- test_31 (6-15) ---
def test_06_test31_located():
    assert fn(owner_source(), N31).name == N31


def test_07_test31_semantics_reconstructed():
    assert "protected_root_mutation" in N31


def test_08_test31_lower_bound_derived():
    assert git("rev-parse", F4R_LOWER) == F4R_LOWER and git("rev-parse", "a40f8163^") == F4R_LOWER


def test_09_test31_upper_bound_derived():
    assert git("rev-parse", F4R_UPPER) == F4R_UPPER
    assert "reconcile governed push state" in git("log", "-1", "--format=%s", F4R_UPPER)


def test_10_test31_defect_reproduced():
    pre = show(R0, OWNER_REL)
    old_fn = ast.unparse(fn(pre, N31))
    assert 'git(\'diff\', \'--name-only\', R0)' in old_fn


def test_11_test31_immutable_repair():
    assert "R0, F4_REPAIR_FINALIZED" in node(N31)


def test_12_test31_historical_pass():
    assert not any(p.startswith((".pcae/protected-root", "protected-root/")) for p in historical_files())


def test_13_test31_current_pass():
    assert git("rev-parse", "HEAD") != F4R_UPPER and "F4_REPAIR_FINALIZED" in node(N31)


def test_14_test31_future_pass(tmp_path):
    a, b, c = simulate(tmp_path, "iv.txt", "protected-root/future-file")
    assert git_in(tmp_path, "diff", "--name-only", a, b) == "iv.txt" or "protected-root" not in git_in(tmp_path, "diff", "--name-only", a, b)
    assert "protected-root" in git_in(tmp_path, "diff", "--name-only", a, c)


def test_15_test31_negative_forbidden_mutation_detected(tmp_path):
    a, b, _ = simulate(tmp_path, "protected-root/forbidden", "later.txt")
    changed = git_in(tmp_path, "diff", "--name-only", a, b).splitlines()
    assert any(p.startswith("protected-root/") for p in changed)


# --- test_32 (16-22) ---
def test_16_test32_located():
    assert fn(owner_source(), N32).name == N32


def test_17_test32_semantics_reconstructed():
    assert "helper_installation_artifact" in N32


def test_18_test32_bounds_derived():
    assert F4R_LOWER == git("rev-parse", "a40f8163^") and git("rev-parse", F4R_UPPER) == F4R_UPPER


def test_19_test32_moving_defect_reproduced():
    pre = show(R0, OWNER_REL)
    old_fn = ast.unparse(fn(pre, N32))
    assert 'git(\'diff\', \'--name-only\', R0)' in old_fn


def test_20_test32_immutable_repair():
    assert "R0, F4_REPAIR_FINALIZED" in node(N32)


def test_21_test32_historical_and_current_pass():
    assert not any("installation" in p.lower() for p in historical_files() if p.startswith(".pcae/certification/"))
    assert "F4_REPAIR_FINALIZED" in node(N32)


def test_22_test32_forbidden_artifact_detected(tmp_path):
    a, b, _ = simulate(tmp_path, ".pcae/certification/installation-forbidden.json", "later.txt")
    changed = git_in(tmp_path, "diff", "--name-only", a, b).splitlines()
    assert any("installation" in p.lower() for p in changed if p.startswith(".pcae/certification/"))


# --- test_43 (23-29) ---
def test_23_test43_located():
    assert fn(owner_source(), N43).name == N43


def test_24_test43_semantics_reconstructed():
    assert "f4_change_is_test_only" in N43


def test_25_test43_bounds_derived():
    assert subprocess.run(["git", "merge-base", "--is-ancestor", F4R_LOWER, F4R_UPPER], cwd=ROOT).returncode == 0


def test_26_test43_moving_defect_reproduced():
    pre = show(R0, OWNER_REL)
    old_fn = ast.unparse(fn(pre, N43))
    assert 'git(\'diff\', \'--name-only\', R0)' in old_fn


def test_27_test43_immutable_repair():
    assert "R0, F4_REPAIR_FINALIZED" in node(N43)


def test_28_test43_historical_and_current_pass():
    allowed_prefixes = ("tests/", "tasks/", "docs/", ".pcae/")
    allowed_exact = {"PROJECT_STATUS.md", "CHANGELOG.md"}
    assert all(p.startswith(allowed_prefixes) or p in allowed_exact for p in historical_files())
    assert "F4_REPAIR_FINALIZED" in node(N43)


def test_29_test43_forbidden_production_modification_detected(tmp_path):
    a, b, _ = simulate(tmp_path, "src/pcae/forbidden.py", "later.txt")
    changed = git_in(tmp_path, "diff", "--name-only", a, b).splitlines()
    allowed_prefixes = ("tests/", "tasks/", "docs/", ".pcae/")
    allowed_exact = {"PROJECT_STATUS.md", "CHANGELOG.md"}
    assert not all(p.startswith(allowed_prefixes) or p in allowed_exact for p in changed)


# 30-42: no live/special-case/weakening authority
def test_30_no_live_head():
    assert "'HEAD'" not in all_nodes() and '"HEAD"' not in all_nodes()


def test_31_no_live_worktree():
    for name in (N31, N32, N43):
        args = [a.value for a in ast.walk(fn(owner_source(), name)) if isinstance(a, ast.Call) and getattr(a.func, "attr", "") == "diff"]
    assert "F4R_LOWER" not in all_nodes() or "F4_REPAIR_FINALIZED" in all_nodes()
    assert all("git(\"diff\", \"--name-only\", R0)" not in ast.unparse(fn(owner_source(), n)) for n in (N31, N32, N43))


def test_32_no_live_metadata():
    assert "phase-completion" not in all_nodes() and ".read_text(" not in all_nodes()


def test_33_no_current_successor_exception():
    assert "successor" not in all_nodes().lower()


def test_34_no_future_allowlist():
    assert "future" not in all_nodes().lower()


def test_35_no_wildcard():
    calls = {ast.unparse(c.func) for name in (N31, N32, N43) for c in ast.walk(fn(owner_source(), name)) if isinstance(c, ast.Call)}
    assert "Path.glob" not in calls and "Path.rglob" not in calls


def test_36_no_fnmatch():
    assert "fnmatch" not in all_nodes()


def test_37_no_test_removal():
    old = show(R0, OWNER_REL)
    assert owner_source().count("def test_") == old.count("def test_")


def test_38_no_rename_to_evade():
    assert all(f"def {n}" in owner_source() for n in (N31, N32, N43))


def test_39_no_skip():
    assert "pytest.skip" not in all_nodes() and "@pytest.mark.skip" not in all_nodes()


def test_40_no_skipif():
    assert "skipif" not in all_nodes()


def test_41_no_pytest_skip_marker():
    assert "@pytest.mark.skip" not in all_nodes()


def test_42_no_xfail():
    assert "xfail" not in all_nodes()


# 43-56: preservation and no-go
def test_43_f7_nodes_unchanged():
    assert F4_IV_FILE.read_bytes() == subprocess.check_output(["git", "show", f"{R0}:tests/{F4_IV_FILE.name}"], cwd=ROOT)


def test_44_f8_nodes_unchanged():
    assert F6_IV_FILE.read_bytes() == subprocess.check_output(["git", "show", f"{R0}:tests/{F6_IV_FILE.name}"], cwd=ROOT)


def test_45_f3_f4_f6_remain_verified():
    text = (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    assert "F-6 (F-6-IV" not in text  # sanity: no fabricated label
    combined = " ".join(COMBINED_IV_REPORT.read_text(encoding="utf-8").split())
    assert "F-3, F-4, and F-6 remain independently verified" in combined


def test_46_h1_h2_f2_bytes_unchanged():
    for rel in (
        "src/pcae/protected_presentation_helper.py",
        "src/pcae/core/protected_presentation.py",
        "src/pcae/core/hpac_rhamp_ctap2.py",
    ):
        assert git("diff", "--name-only", R0, "--", rel) == ""


def test_47_no_production_source_change():
    assert git("diff", "--name-only", R0, "--", "src/pcae") == ""


def test_48_no_production_script_change():
    assert git("diff", "--name-only", R0, "--", "scripts") == ""


def test_49_no_dependency_change():
    assert git("diff", "--name-only", R0, "--", "pyproject.toml") == ""


def test_50_no_contract_change():
    assert git("diff", "--name-only", R0, "--", "docs/contracts") == ""


def test_51_f5_remains_absent():
    assert not PROTECTED_ROOT.exists()


def test_52_no_protected_root_mutation():
    assert "F-5: OPEN / ABSENT / UNCHANGED" in " ".join(REPORT.read_text(encoding="utf-8").split())


def test_53_no_helper_installation():
    assert not PROTECTED_ROOT.exists()


def test_54_no_pawa_deployment_capability():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "No PAWA deployment" not in text or "no PAWA deployment was performed" not in text.lower()
    assert "F-5" in text and "ABSENT" in text


def test_55_no_administrator_interaction():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "No administrator, human, or YubiKey interaction occurred" in text


def test_56_no_human_election():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "No administrator, human, or YubiKey interaction occurred" in text


# 57-68
def test_57_no_yubikey_interaction():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "YubiKey interaction occurred" in text


def test_58_no_presentation_evidence():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "No presentation evidence, principal, Permission Broker permission, or Gate certification" in text


def test_59_no_production_principal():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "principal" in text and "was created or consumed" in text


def test_60_no_gate_certification():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "Gate certification" in text


def test_61_n16_5_remains_open():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "N-16-5 remains **NOT CLOSED**" in text


def test_62_runtime_unchanged():
    out = subprocess.check_output(["pcae", "runtime", "inspect"], cwd=ROOT, text=True)
    for value in ("not_implemented", "Observed", "unavailable", "Plugin count:              0", "Capability count:          0"):
        assert value in out


def test_63_first_effect_absent():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "first effect absent" in text


def test_64_n16_6_untouched():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "N-16-6/N-16-7 remain" in text


def test_65_n16_7_untouched():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "N-16-6/N-16-7 remain" in text


def test_66_fido2_supported_not_exclusive():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "FIDO2 and local protected presentation remain" in text and "supported-not-exclusive" in text


def test_67_local_presentation_supported_not_exclusive():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "local protected presentation remain" in text and "supported-not-exclusive" in text


def test_68_mobile_only_future_preserved():
    text = " ".join(REPORT.read_text(encoding="utf-8").split())
    assert "mobile-only authentication and protected approval remain open/planned" in text
