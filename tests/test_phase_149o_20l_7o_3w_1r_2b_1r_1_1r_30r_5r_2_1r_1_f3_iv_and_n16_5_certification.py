"""Independent software evidence for phase .30R.5R.2.1R.1.

Real-human and genuine-authenticator facts belong in the canonical
certification record.  This suite neither supplies an election nor touches a
CTAP2 device.
"""

from __future__ import annotations

import ast
import hashlib
import os
import subprocess
from pathlib import Path

import pytest

from pcae import protected_presentation_helper as helper
from pcae.core import protected_presentation as presentation
from pcae.core.hpac_foundation import resolve_hpac_protected_root


REPO = Path(__file__).resolve().parents[1]
A = "361114d648dea432aa3ef92ecd7e24e748a173aa"
B = "57edf6a93f8b4f01ee95d4b74ceddcaea96f53b3"
R = V = "00c077f6ff3389a8c91d503fb5341ec72775f8e0"
E = "0250e5f79340b659f4c34ce391656d8f7219ccc3"
IMPLEMENTATION = "a85abff66b5a07f9d83b873d625aea7b1c65b19d"
PREDECESSOR = REPO / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_protected_presentation_interactive_election_repair.py"
F3_REPAIR = REPO / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_f3_immutable_phase_entry_evidence_repair.py"
HISTORICAL_IV = REPO / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1_protected_presentation_human_election_iv_and_n16_5_certification.py"
HELPER = REPO / "src/pcae/protected_presentation_helper.py"
LAUNCHER = REPO / "src/pcae/core/protected_presentation.py"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, text=True, capture_output=True).stdout


@pytest.mark.parametrize("sha", [A, B, R, V, E, IMPLEMENTATION])
def test_01_fixed_anchors_are_git_commits(sha):
    assert _git("cat-file", "-t", sha).strip() == "commit"


def test_02_f3_topology_is_independently_exact():
    assert _git("rev-parse", f"{IMPLEMENTATION}^").strip() == E
    assert _git("rev-list", "--parents", "-n", "1", IMPLEMENTATION).split() == [IMPLEMENTATION, E]


def test_03_implementation_commit_is_the_phase_opening_change():
    subject = _git("show", "-s", "--format=%s", IMPLEMENTATION)
    assert "30R.5R.2" in subject and "repair protected human election" in subject
    changed = set(_git("diff", "--name-only", E, IMPLEMENTATION).splitlines())
    assert any(p.startswith("tasks/") for p in changed)
    assert {"src/pcae/protected_presentation_helper.py", "src/pcae/core/protected_presentation.py"} <= changed


def test_04_historical_blocked_iv_is_immutable():
    report = REPO / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1_PROTECTED_PRESENTATION_HUMAN_ELECTION_IV_AND_N_16_5_CERTIFICATION.md"
    assert "Verdict: BLOCKED" in report.read_text()
    assert _git("diff", "--quiet", B, R, "--", str(report.relative_to(REPO))) == ""


def test_05_original_f3_is_reconstructed_from_b():
    old = _git("show", f"{B}:{PREDECESSOR.relative_to(REPO)}")
    assert '_git("rev-parse", "HEAD").strip().startswith(ENTRY)' in old


def test_06_repair_uses_immutable_parent_not_live_head():
    current = PREDECESSOR.read_text()
    assert f'REPAIR_IMPLEMENTATION = "{IMPLEMENTATION}"' in current
    assert '_git("rev-parse", f"{REPAIR_IMPLEMENTATION}^").strip() == ENTRY' in current
    assert '_git("rev-parse", "HEAD").strip().startswith(ENTRY)' not in current


def test_07_no_live_metadata_is_historical_authority():
    body = PREDECESSOR.read_text().split("def test_01_", 1)[1].split("\n\ndef ", 1)[0]
    assert "phase-completion-metadata" not in body
    assert "PROJECT_STATUS" not in body
    assert '"HEAD"' not in body


def test_08_fixed_parent_survives_multiple_real_successors():
    assert _git("merge-base", "--is-ancestor", IMPLEMENTATION, A) == ""
    assert _git("merge-base", "--is-ancestor", IMPLEMENTATION, B) == ""
    assert _git("merge-base", "--is-ancestor", IMPLEMENTATION, R) == ""
    assert _git("rev-parse", f"{IMPLEMENTATION}^").strip() == E


def test_09_no_future_commit_wildcard_or_fnmatch():
    added = "\n".join(
        line[1:] for line in _git("diff", B, R, "--", str(PREDECESSOR.relative_to(REPO))).splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    assert "fnmatch" not in added and "wildcard" not in added and "startswith(" not in added


def test_10_f3_change_is_only_the_exact_predecessor_test():
    changed = _git("diff", "--name-only", B, R, "--", "tests").splitlines()
    assert set(changed) == {str(PREDECESSOR.relative_to(REPO)), str(F3_REPAIR.relative_to(REPO))}


@pytest.mark.parametrize("zone", ["src/pcae", "scripts", "pyproject.toml", "docs/contracts"])
def test_11_f3_phase_changed_no_production_contract_or_dependency(zone):
    assert _git("diff", "--quiet", B, R, "--", zone) == ""


@pytest.mark.parametrize("rel", [
    "src/pcae/protected_presentation_helper.py",
    "src/pcae/core/protected_presentation.py",
    "src/pcae/core/hpac_rhamp_ctap2.py",
    "src/pcae/core/hpac_verifier.py",
    "src/pcae/core/runtime_dispatch_gate5.py",
    "src/pcae/core/runtime_dispatch_gate9.py",
])
def test_12_security_sources_are_byte_identical_b_to_r(rel):
    assert _git("diff", "--quiet", B, R, "--", rel) == ""


def test_13_h2_trusted_tty_remains_separate():
    tree = ast.parse(HELPER.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_observe_trusted_terminal_election")
    text = ast.get_source_segment(HELPER.read_text(), node)
    assert helper._TRUSTED_TTY_PATH == "/dev/tty"
    assert "sys.stdin" not in text and "input(" not in text


@pytest.mark.parametrize("value,want", [(b"APPROVE\n", "APPROVE"), (b"REJECT\n", "REJECT")])
def test_14_explicit_election_vocabulary_is_closed(monkeypatch, value, want):
    left, right = __import__("socket").socketpair()
    right.sendall(value)
    monkeypatch.setattr(helper.os, "open", lambda *_a: os.dup(left.fileno()))
    try:
        assert helper._observe_election({}, b"bound display\n") == want
    finally:
        left.close(); right.close()


@pytest.mark.parametrize("value", [b"\n", b"approve\n", b"yes\n", b"APPROVE \n", b""])
def test_15_non_explicit_inputs_fail_closed(monkeypatch, value):
    left, right = __import__("socket").socketpair()
    if value:
        right.sendall(value)
    right.close()
    monkeypatch.setattr(helper.os, "open", lambda *_a: os.dup(left.fileno()))
    try:
        assert helper._observe_election({}, b"bound display\n") == "CANCEL"
    finally:
        left.close()


def test_16_no_tty_never_falls_back_to_env_or_caller(monkeypatch):
    monkeypatch.setenv("PCAE_AUTO_APPROVE", "APPROVE")
    monkeypatch.setattr(helper.os, "open", lambda *_a: (_ for _ in ()).throw(OSError("no tty")))
    assert helper._observe_election({"decision": "APPROVE"}, b"display") == "CANCEL"


def test_17_test_directive_is_rejected_in_production():
    source = HELPER.read_text()
    assert 'document["ceremony_mode"] == "production" and "test_decision_directive" in document' in source


@pytest.mark.parametrize("control", ["\x1b", "\r", "\n", "\x08", "\x7f", "\x9b", "\u202e", "\u2066"])
def test_18_terminal_controls_are_neutralized(control):
    assert control not in helper.neutralize_untrusted_text("before" + control + "APPROVE")


def test_19_launcher_remains_fixed_held_byte_invocation():
    source = LAUNCHER.read_text()
    assert '[sys.executable, "-I", "-c", _HELD_HELPER_BOOTSTRAP]' in source
    assert '[sys.executable, "-I", plat_fd]' not in source
    assert "shell=True" not in source and 'child_env["PATH"]' not in source


def test_20_no_generic_process_or_network_authority():
    tree = ast.parse(LAUNCHER.read_text() + "\n" + HELPER.read_text())
    attrs = {getattr(n.func, "attr", "") for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "posix_spawn" in attrs
    assert not ({"Popen", "run", "system", "popen", "execvp", "spawnvp", "connect", "listen"} & attrs)


def test_21_evidence_write_remains_after_approve_only():
    source = LAUNCHER.read_text()
    start = source.index("def run_protected_presentation_ceremony")
    body = source[start:source.index("def _canonical_subject_bound_presentation_digest", start)]
    assert body.index('if decision == "REJECT"') < body.index("evidence = _build_and_persist_evidence")
    assert "store.create_canonical(writer, evidence, installed_descriptor)" in source


def test_22_no_test_weakening_in_f3_patch():
    old = ast.parse(_git("show", f"{B}:{PREDECESSOR.relative_to(REPO)}"))
    new = ast.parse(PREDECESSOR.read_text())
    old_names = {n.name for n in ast.walk(old) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")}
    new_names = {n.name for n in ast.walk(new) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")}
    assert old_names == new_names
    added = _git("diff", B, R, "--", str(PREDECESSOR.relative_to(REPO)))
    assert not any(token in added for token in ("pytest.skip", "@pytest.mark.skip", "xfail", "fnmatch"))


def test_23_historical_iv_failure_is_only_obsolete_f3_demonstration():
    source = HISTORICAL_IV.read_text()
    assert "test_30_repair_suite_contains_a_stale_live_head_assertion_finding_f3" in source
    assert "Verdict: BLOCKED" in _git("show", f"{B}:docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1_PROTECTED_PRESENTATION_HUMAN_ELECTION_IV_AND_N_16_5_CERTIFICATION.md")


def test_24_production_root_precondition_is_currently_absent():
    root = resolve_hpac_protected_root()
    assert root == Path("/Library/Application Support/PCAE/HPAC/protected-root")
    assert not root.exists()


def test_25_missing_root_means_no_current_production_helper_generation():
    root = resolve_hpac_protected_root()
    assert not (root / "presentation-mechanisms/v2/pcae-protected-local-presentation/current-generation.json").exists()


def test_26_phase_entry_has_no_production_or_contract_drift():
    assert _git("diff", "--name-only", V, "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts").strip() == ""


def test_27_runtime_and_profile_status_remain_explicit():
    status = (REPO / "PROJECT_STATUS.md").read_text().lower()
    assert "observed / observe / unavailable" in status
    assert "supported-not-exclusive" in status or "not globally mandatory" in status
    assert "mobile-only" in status


def test_28_no_effect_or_n16_6_symbols_added_this_phase():
    added = _git("diff", V, "--", "src/pcae")
    assert added == ""


def test_29_fresh_suite_itself_has_no_skip_xfail_or_device_io():
    source = Path(__file__).read_text()
    tree = ast.parse(source)
    decorators = "\n".join(ast.unparse(d) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) for d in n.decorator_list)
    assert "skip" not in decorators and "xfail" not in decorators
    imported = {n.name for n in ast.walk(tree) if isinstance(n, ast.alias)}
    called = {ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "resolve_production_ctap2_provider" not in imported | called


def test_30_contract_requires_real_helper_and_human_election_before_closure():
    contract = (REPO / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md").read_text()
    assert "RHAMP-REQ-152" in contract
    section = contract.split("RHAMP-REQ-152", 1)[1].split("RHAMP-REQ-153", 1)[0]
    assert "real helper render" in section and "explicit Approve election" in section
