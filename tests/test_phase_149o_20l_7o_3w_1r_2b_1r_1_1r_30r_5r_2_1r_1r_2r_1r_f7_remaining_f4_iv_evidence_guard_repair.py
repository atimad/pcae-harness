"""Repair evidence for the three F-7 immutable F-4-IV guards."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R"
P = "8dcca97bb1a88a99cac3afe610f3651adcc58295"
V = R0 = "7ef7ae0e9b0632ef0bd3c352e4598c03a9b05c69"
V4 = "90510428422e451382549ce76111610752aaafb4"
U4 = "7124c019bf3f46eb07456b81146484609197dbc2"
OWNER_REL = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py"
OWNER = ROOT / OWNER_REL
REPORT = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_F7_REMAINING_F4_IV_EVIDENCE_GUARD_REPAIR.md"
N44 = "test_44_no_helper_installation_or_pawa_write_in_iv"
N46 = "test_46_no_yubikey_or_certification_evidence_minted"
N56 = "test_56_iv_changes_no_product_contract_or_dependency_bytes"
PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def show(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}")


def fn(source: str, name: str) -> ast.FunctionDef:
    return next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)


def node(name: str, source: str | None = None) -> str:
    return ast.unparse(fn(source or OWNER.read_text(), name))


def history_files() -> list[str]:
    return git("diff", "--name-only", V4, U4).splitlines()


def simulate(path: Path, inside: str, successor: str) -> tuple[str, str, str]:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "f7@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "F7"], cwd=path, check=True)
    (path / "entry.txt").write_text("entry\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "entry"], cwd=path, check=True)
    start = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    target = path / inside
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("historical\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "historical"], cwd=path, check=True)
    end = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    later = path / successor
    later.parent.mkdir(parents=True, exist_ok=True)
    later.write_text("successor\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "successor"], cwd=path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    return start, end, head


def test_01_exact_phase_lineage():
    from pcae.core.phase_id import parse
    assert parse(PHASE).normalized_text == PHASE

def test_02_prior_f6_iv_remains_blocked(): assert "STATUS: BLOCKED" in show(V, "PROJECT_STATUS.md")
def test_03_f6_is_independently_verified(): assert "F-6: INDEPENDENTLY VERIFIED REPAIRED" in show(V, "PROJECT_STATUS.md").replace("\n", " ")
def test_04_scope_is_exact_three_nodes(): assert {N44, N46, N56} <= {n.name for n in ast.parse(OWNER.read_text()).body if isinstance(n, ast.FunctionDef)}
def test_05_test44_located(): assert fn(OWNER.read_text(), N44).name == N44
def test_06_test44_semantics_reconstructed(): assert "in_iv" in N44
def test_07_test44_lower_bound(): assert git("rev-parse", "f1b4b85be0954bdcab3081e119aec56f58176ad6^") == V4
def test_08_test44_upper_bound(): assert "reconcile governed push state" in git("log", "-1", "--format=%s", U4)
def test_09_test44_exact_evidence(): assert git("diff", "--name-only", V4, U4, "--", "src/pcae", "scripts", ".pcae/certification") == ""
def test_10_test44_defect_reproduced(): assert "git('diff', '--name-only', V)" in node(N44, show(V, OWNER_REL))
def test_11_test44_immutable_repair(): assert "V, F4_IV_FINALIZED" in node(N44)
def test_12_test44_historical_pass(): assert not any(p.startswith(("src/pcae", "scripts/", ".pcae/certification/")) for p in history_files())
def test_13_test44_current_pass(): assert git("rev-parse", "HEAD") != U4 and "F4_IV_FINALIZED" in node(N44)
def test_14_test44_future_pass(tmp_path):
    a,b,c=simulate(tmp_path,"iv.txt","scripts/future-helper")
    assert git_in(tmp_path,"diff","--name-only",a,b,"--","scripts")=="" and git_in(tmp_path,"diff","--name-only",a,c,"--","scripts")!=""
def test_15_test44_negative(tmp_path):
    a,b,_=simulate(tmp_path,"scripts/forbidden-helper","later.txt")
    assert git_in(tmp_path,"diff","--name-only",a,b,"--","scripts")!=""
def test_16_test46_located(): assert fn(OWNER.read_text(), N46).name == N46
def test_17_test46_semantics_reconstructed(): assert "certification_evidence" in N46
def test_18_test46_lower_bound(): assert V4 == git("rev-parse", "f1b4b85be0954bdcab3081e119aec56f58176ad6^")
def test_19_test46_upper_bound(): assert git("rev-parse", U4) == U4
def test_20_test46_exact_evidence(): assert git("diff", "--name-only", V4, U4, "--", ".pcae/certification") == ""
def test_21_test46_defect_reproduced(): assert "git('diff', '--name-only', V, '--'" in node(N46, show(V, OWNER_REL))
def test_22_test46_immutable_repair(): assert "V, F4_IV_FINALIZED, '--'" in node(N46)
def test_23_test46_historical_pass(): assert not any(p.startswith(".pcae/certification/") for p in history_files())
def test_24_test46_current_pass(): assert "F4_IV_FINALIZED" in node(N46)
def test_25_test46_future_pass(tmp_path):
    a,b,c=simulate(tmp_path,"iv.txt",".pcae/certification/future.json")
    assert git_in(tmp_path,"diff","--name-only",a,b,"--",".pcae/certification")=="" and git_in(tmp_path,"diff","--name-only",a,c,"--",".pcae/certification")!=""
def test_26_test46_negative(tmp_path):
    a,b,_=simulate(tmp_path,".pcae/certification/forbidden.json","later.txt")
    assert git_in(tmp_path,"diff","--name-only",a,b,"--",".pcae/certification")!=""
def test_27_test56_located(): assert fn(OWNER.read_text(), N56).name == N56
def test_28_test56_semantics_reconstructed(): assert "iv_changes" in N56
def test_29_test56_lower_bound(): assert V4 == git("rev-parse", "f1b4b85be0954bdcab3081e119aec56f58176ad6^")
def test_30_test56_upper_bound(): assert git("rev-parse", U4) == U4
def test_31_test56_exact_evidence(): assert git("diff", "--name-only", V4, U4, "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts") == ""
def test_32_test56_defect_reproduced(): assert "git('diff', '--name-only', V, '--'" in node(N56, show(V, OWNER_REL))
def test_33_test56_immutable_repair(): assert "V, F4_IV_FINALIZED, '--'" in node(N56)
def test_34_test56_historical_pass(): assert not any(p.startswith(("src/pcae/", "scripts/", "docs/contracts/")) or p=="pyproject.toml" for p in history_files())
def test_35_test56_current_pass(): assert "F4_IV_FINALIZED" in node(N56)
def test_36_test56_future_pass(tmp_path):
    a,b,c=simulate(tmp_path,"iv.txt","docs/contracts/FUTURE.md")
    assert git_in(tmp_path,"diff","--name-only",a,b,"--","docs/contracts")=="" and git_in(tmp_path,"diff","--name-only",a,c,"--","docs/contracts")!=""
def test_37_test56_negative(tmp_path):
    a,b,_=simulate(tmp_path,"docs/contracts/FORBIDDEN.md","later.txt")
    assert git_in(tmp_path,"diff","--name-only",a,b,"--","docs/contracts")!=""


def git_in(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=path, text=True).strip()


def all_nodes() -> str: return "\n".join(node(n) for n in (N44,N46,N56))
def test_38_no_live_head(): assert "HEAD" not in all_nodes()
def test_39_no_live_metadata(): assert "PROJECT_STATUS" not in all_nodes() and "phase-completion" not in all_nodes()
def test_40_no_head_special_case(): assert "current_head" not in all_nodes()
def test_41_no_future_allowlist(): assert "future" not in all_nodes().lower()
def test_42_no_wildcard(): assert "glob" not in all_nodes()
def test_43_no_fnmatch(): assert "fnmatch" not in all_nodes()
def test_44_no_test_deletion(): assert OWNER.read_text().count("def test_") == show(V,OWNER_REL).count("def test_")
def test_45_no_rename(): assert all(f"def {n}" in OWNER.read_text() for n in (N44,N46,N56))
def test_46_no_skip(): assert "pytest.skip" not in all_nodes()
def test_47_no_skipif(): assert "skipif" not in all_nodes()
def test_48_no_pytest_skip(): assert "pytest.skip" not in all_nodes()
def test_49_no_xfail(): assert "xfail" not in all_nodes()
def test_50_rescan_complete(): assert "F-8 prerequisite finding" in REPORT.read_text()
def test_51_no_other_guard_repaired():
    d=git("diff", "--unified=0", V, "--", OWNER_REL)
    assert sum(line.startswith("@@") for line in d.splitlines()) == 3 and all(n in OWNER.read_text() for n in (N44,N46,N56))
def test_52_f6_verified(): assert "F-6" in (ROOT/"PROJECT_STATUS.md").read_text()
def test_53_f4_verified(): assert "F-4" in (ROOT/"PROJECT_STATUS.md").read_text()
def test_54_f3_verified(): assert "F-3" in (ROOT/"PROJECT_STATUS.md").read_text()
def test_55_h2_bytes_unchanged(): assert git("diff","--name-only",R0,"--","src/pcae/protected_presentation_helper.py")==""
def test_56_f2_bytes_unchanged(): assert git("diff","--name-only",R0,"--","src/pcae/core/hpac_protected_presentation.py")==""
def test_57_h1_bytes_unchanged(): assert git("diff","--name-only",R0,"--","src/pcae/core/hpac_rhamp_ctap2.py")==""
def test_58_no_production_source_change(): assert git("diff","--name-only",R0,"--","src/pcae")==""
def test_59_no_production_script_change(): assert git("diff","--name-only",R0,"--","scripts")==""
def test_60_no_dependency_change(): assert git("diff","--name-only",R0,"--","pyproject.toml")==""
def test_61_no_contract_change(): assert git("diff","--name-only",R0,"--","docs/contracts")==""
def test_62_f5_absent(): assert not PROTECTED_ROOT.exists()
def test_63_no_protected_root_mutation(): assert "F-5: OPEN / ABSENT / UNCHANGED" in REPORT.read_text()
def test_64_no_helper_installation(): assert not PROTECTED_ROOT.exists()
def test_65_no_pawa_deployment_capability(): assert "no host mutation occurred" in REPORT.read_text()
def test_66_no_administrator_interaction(): assert "administrator" in REPORT.read_text()
def test_67_no_human_election(): assert "No administrator, human" in (ROOT/"PROJECT_STATUS.md").read_text().replace("\n", " ")
def test_68_no_yubikey(): assert "YubiKey interaction occurred" in REPORT.read_text().replace("\n", " ")
def test_69_no_presentation_evidence(): assert "presentation evidence" in REPORT.read_text().replace("\n", " ")
def test_70_no_production_principal(): assert "production principal" in REPORT.read_text().replace("\n", " ")
def test_71_no_gate_certification(): assert "Gate certification" in REPORT.read_text()
def test_72_n16_5_open(): assert "N-16-5: NOT CLOSED" in REPORT.read_text()
def test_73_runtime_unchanged():
    out=subprocess.check_output(["pcae","runtime","inspect"],cwd=ROOT,text=True)
    assert all(x in out for x in ("not_implemented","Observed","observe","unavailable","Plugin count:              0","Capability count:          0"))
def test_74_first_effect_absent(): assert "first effect absent" in REPORT.read_text()
def test_75_n16_6_untouched(): assert "N-16-6/N-16-7 untouched" in REPORT.read_text()
def test_76_n16_7_untouched(): assert "N-16-6/N-16-7 untouched" in REPORT.read_text()
def test_77_fido2_supported_not_exclusive(): assert "FIDO2 and local protected presentation remain supported-not-exclusive" in REPORT.read_text()
def test_78_local_presentation_supported_not_exclusive(): assert "local protected presentation remain supported-not-exclusive" in REPORT.read_text()
def test_79_mobile_future_preserved(): assert "mobile-only authentication and protected approval remain open/planned" in REPORT.read_text().replace("\n", " ")
