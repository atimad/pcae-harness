"""Independent verification for .30R.5R.2.1.

This verification-only suite does not repair the implementation or substitute
deterministic interaction for the required real-human certification ceremony.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import socket
import subprocess
from pathlib import Path

import pytest

from pcae import protected_presentation_helper as helper
from pcae.core import protected_presentation as presentation
from pcae.core.protected_presentation_installation import verify_helper_bytes


REPO = Path(__file__).resolve().parents[1]
A = "0250e5f7"
I = "361114d6"
V = "361114d6"
HELPER = REPO / "src/pcae/protected_presentation_helper.py"
LAUNCHER = REPO / "src/pcae/core/protected_presentation.py"
REPAIR_SUITE = REPO / "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_protected_presentation_interactive_election_repair.py"

CONTRACTS = (
    "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md",
    "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md",
    "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
    "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
    "docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md",
)

GUARDS = (
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_1_protected_presentation_real_assurance.py",
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_2_protected_presentation_real_assurance_iv.py",
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_ctap2_pin_uv_repair.py",
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_1_ctap2_pin_uv_repair_iv.py",
    "tests/test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py",
    "tests/test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py",
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_1_writer_anchor_adjudication_iv.py",
    "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_6_multi_write_completion_integrity_repair.py",
    "tests/test_gate5_approval_validation_coordinator_integration_independent_verification_3w1r2b1r1_1r11.py",
)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=True).stdout


def _facts(**changes) -> dict:
    value = {
        "repository_identity": "repo-iv",
        "repository_display": "pcae-harness",
        "task_id": "task-iv",
        "task_display": "bounded certification",
        "runtime_target_id": "local-cli.fixed-argv.v1",
        "runtime_target_display": "local fixed argv",
        "operation_effect_scope_display": "no network; no external effect",
        "prompt_hash": "a" * 64,
        "prompt_instruction_display": "bounded harmless certification",
        "invocation_id": "inv-iv",
        "invocation_display": "bounded invocation",
        "expires_at": "2099-01-01T00:00:00.000Z",
        "one_shot_notice": True,
    }
    value.update(changes)
    return value


def _request(decision="APPROVE", request_id="hpr-a") -> dict:
    facts = _facts()
    shown = helper.render_human_visible_bytes(facts, renderer_profile="profile-v1")
    value = {
        "request_schema_version": helper.REQUEST_SCHEMA_VERSION,
        "ceremony_mode": "test-only",
        "nonce": "n" * 64,
        "request_id": request_id,
        "approval_id": "ria-" + "a" * 32,
        "challenge_id": "challenge-a",
        "presentation_digest": "b" * 64,
        "approval_subject_digest": "c" * 64,
        "principal_id": "hp-" + "d" * 32,
        "invocation_id": "inv-a",
        "attempt_id": "attempt-a",
        "expires_at": facts["expires_at"],
        "mechanism_id": helper.MECHANISM_ID,
        "installation_id": "hppi-" + "e" * 32,
        "generation": 1,
        "installation_digest": "f" * 64,
        "descriptor_digest": "1" * 64,
        "renderer_profile": "profile-v1",
        "human_visible_facts": facts,
        "request_digest": "",
    }
    value["request_digest"] = helper._self_excluding_digest(value, field="request_digest")
    value["test_decision_directive"] = {
        "decision": decision,
        "displayed_digest_ack": hashlib.sha256(shown).hexdigest(),
    }
    return value


def _terminal(monkeypatch, raw: bytes):
    helper_end, human_end = socket.socketpair()
    human_end.sendall(raw)
    monkeypatch.setattr(helper.os, "open", lambda *_a: os.dup(helper_end.fileno()))
    try:
        decision = helper._observe_election({}, b"exact bound display\n")
        shown = human_end.recv(65536)
    finally:
        helper_end.close()
        human_end.close()
    return decision, shown


def _launch(decision: str, monkeypatch=None, executable=None):
    fd = os.open(HELPER, os.O_RDONLY)
    if executable is not None:
        monkeypatch.setattr(presentation.sys, "executable", executable)
    return presentation._launch_and_exchange(fd, _request(decision), timeout_seconds=5)


@pytest.mark.parametrize("sha,phase", [(A, "5R.1"), (I, "5R.2"), (V, "5R.2")])
def test_01_a_i_v_are_derived_git_objects(sha, phase):
    assert len(_git("rev-parse", sha).strip()) == 40
    assert phase in _git("log", "-1", "--format=%s", sha)


def test_02_production_diff_is_exact():
    assert set(_git("diff", "--name-only", A, I, "--", "src/pcae", "scripts", "pyproject.toml").split()) == {
        "src/pcae/core/protected_presentation.py", "src/pcae/protected_presentation_helper.py"
    }


@pytest.mark.parametrize("rel", CONTRACTS)
def test_03_contract_bytes_unchanged(rel):
    assert _git("diff", "--quiet", A, I, "--", rel) == ""


def test_04_historical_h2_reconstructed_at_a():
    old = _git("show", f"{A}:src/pcae/protected_presentation_helper.py")
    body = old.split("def _observe_election", 1)[1].split("\n\ndef ", 1)[0]
    assert 'return "CANCEL"' in body and "/dev/tty" not in body


def test_05_historical_f2_reconstructed_at_a():
    old = _git("show", f"{A}:src/pcae/core/protected_presentation.py")
    assert '[sys.executable, "-I", plat_fd]' in old


def test_06_production_directive_is_rejected():
    req = _request()
    req["ceremony_mode"] = "production"
    with pytest.raises(helper.ProtectedPresentationHelperError):
        helper._validate_request(req)


def test_07_trusted_tty_is_fixed_and_stdin_absent():
    tree = ast.parse(HELPER.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_observe_trusted_terminal_election")
    text = ast.get_source_segment(HELPER.read_text(), node)
    assert "_TRUSTED_TTY_PATH" in text and "sys.stdin" not in text and "input(" not in text
    assert helper._TRUSTED_TTY_PATH == "/dev/tty"


@pytest.mark.parametrize("raw,want", [(b"APPROVE\n", "APPROVE"), (b"REJECT\n", "REJECT")])
def test_08_exact_elections(monkeypatch, raw, want):
    got, shown = _terminal(monkeypatch, raw)
    assert got == want and shown.startswith(b"exact bound display\n")


@pytest.mark.parametrize("raw", [b"\n", b"approve\n", b"yes\n", b"1\n", b" APPROVE\n", b"APPROVE \n", b"APPROVE\r\n", b"X" * 40 + b"\n"])
def test_09_invalid_input_fails_closed(monkeypatch, raw):
    assert _terminal(monkeypatch, raw)[0] == "CANCEL"


def test_10_no_tty_does_not_fall_back(monkeypatch):
    monkeypatch.setenv("PCAE_AUTO_APPROVE", "APPROVE")
    monkeypatch.setattr(helper.os, "open", lambda *_a: (_ for _ in ()).throw(OSError()))
    monkeypatch.setattr("builtins.input", lambda *_a: "APPROVE")
    assert helper._observe_election({"decision": "APPROVE"}, b"display") == "CANCEL"


def test_11_eof_fails_closed(monkeypatch):
    left, right = socket.socketpair(); right.close()
    monkeypatch.setattr(helper.os, "open", lambda *_a: os.dup(left.fileno()))
    try:
        assert helper._observe_election({}, b"display") == "CANCEL"
    finally:
        left.close()


def test_12_interruption_fails_closed(monkeypatch):
    monkeypatch.setattr(helper.os, "open", lambda *_a: 91)
    monkeypatch.setattr(helper, "_write_all", lambda *_a: None)
    monkeypatch.setattr(helper, "_read_one_terminal_line", lambda *_a: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr(helper.os, "close", lambda *_a: None)
    assert helper._observe_election({}, b"display") == "CANCEL"


@pytest.mark.parametrize("source", ["protocol", "environment", "argv", "caller"])
def test_13_nonhuman_channels_cannot_approve(monkeypatch, source):
    monkeypatch.setenv("PCAE_PPLP_DECISION", "APPROVE")
    monkeypatch.setattr(helper.os, "open", lambda *_a: (_ for _ in ()).throw(OSError(source)))
    assert helper._observe_election({source: "APPROVE"}, b"display") == "CANCEL"


@pytest.mark.parametrize("control", ["\x1b", "\r", "\n", "\t", "\x08", "\x7f", "\x9b", "\u202e", "\u2066"])
def test_14_control_characters_are_neutralized(control):
    neutral = helper.neutralize_untrusted_text("before" + control + "[APPROVE]")
    assert control not in neutral
    rendered = helper.render_human_visible_bytes(_facts(task_display="before" + control + "[APPROVE]"), renderer_profile="profile-v1")
    assert ("task_display\t" + neutral).encode() in rendered


@pytest.mark.parametrize("field", ["repository_identity", "task_id", "runtime_target_id", "operation_effect_scope_display", "prompt_hash", "invocation_id", "expires_at"])
def test_15_visible_authority_fields_change_digest(field):
    base = helper.render_human_visible_bytes(_facts(), renderer_profile="profile-v1")
    changed = helper.render_human_visible_bytes(_facts(**{field: "changed"}), renderer_profile="profile-v1")
    assert hashlib.sha256(base).digest() != hashlib.sha256(changed).digest()


def test_16_response_substitution_rejected():
    a, b = _request(request_id="hpr-a"), _request(request_id="hpr-b")
    shown = helper.render_human_visible_bytes(_facts(), renderer_profile="profile-v1")
    response = helper._build_response(a, "APPROVE", hashlib.sha256(shown).hexdigest(), now="2099-01-01T00:00:00.000Z")
    with pytest.raises(presentation.ProtectedPresentationCeremonyError):
        presentation._validate_response(response, b, displayed_digest=hashlib.sha256(shown).hexdigest())


def test_17_portable_bootstrap_executes_helper_on_system_python39(monkeypatch):
    assert "(3, 9)" in subprocess.run(["/usr/bin/python3", "-c", "import sys;print(sys.version_info[:2])"], text=True, capture_output=True, check=True).stdout
    assert _launch("APPROVE", monkeypatch, "/usr/bin/python3")["decision"] == "APPROVE"


def test_18_launcher_is_closed_and_path_independent():
    source = LAUNCHER.read_text(); tree = ast.parse(source)
    calls = {getattr(n.func, "attr", "") for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "posix_spawn" in calls and not ({"Popen", "run", "system", "popen", "execvp", "spawnvp"} & calls)
    assert '[sys.executable, "-I", "-c", _HELD_HELPER_BOOTSTRAP]' in source
    assert '"PATH"' not in source and "shell=True" not in source


@pytest.mark.parametrize("decision,want", [("APPROVE", "APPROVE"), ("REJECT", "REJECT"), ("NO_RESPONSE", None)])
def test_19_child_protocol_outcomes(decision, want):
    response = _launch(decision)
    assert (None if response is None else response["decision"]) == want


@pytest.mark.parametrize("decision", ["CRASH", "MALFORMED_RESPONSE"])
def test_20_bad_child_fails_closed(decision):
    with pytest.raises(presentation.ProtectedPresentationCeremonyError):
        _launch(decision)


def test_21_held_fd_defeats_path_substitution(tmp_path):
    original = b"print('trusted')\n"; path = tmp_path / "helper"
    path.write_bytes(original); path.chmod(0o500)
    verified = verify_helper_bytes(path, expected_sha256=hashlib.sha256(original).hexdigest(), deployment_owner_uid=os.getuid(), protected_root=tmp_path)
    replacement = tmp_path / "replacement"; replacement.write_bytes(b"print('bad')\n"); replacement.chmod(0o500); os.replace(replacement, path)
    try:
        assert os.read(verified.fd, 65536) == original
    finally:
        os.close(verified.fd)


def test_22_revalidation_precedes_evidence_write():
    text = LAUNCHER.read_text(); start = text.index("response = _launch_and_exchange")
    assert start < text.index("revalidated = _resolve_or_terminal", start) < text.index("evidence = _build_and_persist_evidence", start)


@pytest.mark.parametrize("rel", [
    "src/pcae/core/hpac_rhamp_ctap2.py", "src/pcae/core/human_authenticator_fido2.py",
    "src/pcae/core/hpac_verifier.py", "src/pcae/core/runtime_dispatch_gate5.py",
    "src/pcae/core/runtime_dispatch_gate9.py", "src/pcae/core/approval_presentation.py",
    "src/pcae/core/protected_presentation_installation.py", "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/runtime_dispatch_permission.py", "src/pcae/core/runtime_introspection.py",
])
def test_23_forbidden_production_surfaces_unchanged(rel):
    assert _git("diff", "--quiet", A, I, "--", rel) == ""


@pytest.mark.parametrize("rel", GUARDS)
def test_24_guard_definitions_preserved_and_not_skipped(rel):
    old = ast.parse(_git("show", f"{A}:{rel}")); new = ast.parse((REPO / rel).read_text())
    old_names = {n.name for n in ast.walk(old) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    new_names = {n.name for n in ast.walk(new) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
    assert old_names <= new_names
    for node in ast.walk(new):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            assert not any(x in " ".join(ast.unparse(d) for d in node.decorator_list) for x in ("skip", "xfail"))


def test_25_no_wildcard_or_fnmatch_broadening():
    added = "\n".join(x[1:] for x in _git("diff", A, I, "--", *GUARDS).splitlines() if x.startswith("+") and not x.startswith("+++"))
    assert "fnmatch" not in added and "rglob" not in added and "glob(" not in added


def test_26_hardware_evidence_preserved():
    evidence = json.loads((REPO / ".pcae/certification/rhamp_hardware_cert_30r5r1.json").read_text())
    assert evidence["A"]["result"] == "PASS"
    assert evidence["A"]["real_flag_up"] is True and evidence["A"]["real_flag_uv"] is True
    assert evidence["A"]["real_observed_sign_count_1"] == 6 and "6 -> 8" in evidence["A"]["real_counter_currentness"]


def test_27_profiles_are_supported_not_exclusive_and_mobile_stays_open():
    status = (REPO / "PROJECT_STATUS.md").read_text().lower()
    assert "not globally mandatory" in status and "not the exclusive" in status
    assert "mobile-only" in status


def test_28_runtime_and_effect_boundaries_unchanged():
    combined = HELPER.read_text() + LAUNCHER.read_text()
    tree = ast.parse(combined)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "DispatchEnvelope" not in names and "adapter" not in names
    assert "import socket" not in combined


def test_29_evidence_is_written_only_after_approve_and_is_create_only():
    source = LAUNCHER.read_text()
    assert source.index('if decision == "REJECT"') < source.index("evidence = _build_and_persist_evidence")
    assert "TrustedApprovalPresentationStore(authority)" in source
    assert "store.create_canonical(writer, evidence, installed_descriptor)" in source


def test_30_repair_suite_contains_a_stale_live_head_assertion_finding_f3():
    source = REPAIR_SUITE.read_text()
    assert 'assert _git("rev-parse", "HEAD").strip().startswith(ENTRY)' in source
    assert _git("rev-parse", "HEAD").strip() != _git("rev-parse", A).strip()


def test_31_current_phase_changes_no_production_or_contract():
    changed = set(_git("diff", "--name-only", V).split())
    assert not any(p.startswith("src/pcae/") or p.startswith("docs/contracts/") or p == "pyproject.toml" for p in changed)


def test_32_fresh_suite_has_no_skip_xfail_or_fnmatch_calls():
    tree = ast.parse(Path(__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            assert not any(x in " ".join(ast.unparse(d) for d in node.decorator_list) for x in ("skip", "xfail"))
        if isinstance(node, ast.Call):
            assert (getattr(node.func, "attr", None) or getattr(node.func, "id", None)) not in {"skip", "xfail", "fnmatch", "fnmatchcase"}
