"""Phase .30R.5R.2 — trusted election and portable helper-launch repair.

Fresh repair evidence. Hardware-free tests remain NON_REAL; they do not close
N-16-5 or substitute for the required successor IV/certification ceremony.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from pcae import protected_presentation_helper as helper
from pcae.core import protected_presentation as presentation
from pcae.core.hpac_foundation import canonical_json_bytes
from pcae.core.protected_presentation_installation import verify_helper_bytes


REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
ENTRY = "0250e5f79340b659f4c34ce391656d8f7219ccc3"
REPAIR_IMPLEMENTATION = "a85abff66b5a07f9d83b873d625aea7b1c65b19d"
PRESENTATION_HEAD = "5b6b4013"
IV_ENTRY = "ea40c47e"
HELPER_PATH = SRC / "protected_presentation_helper.py"
LAUNCHER_PATH = SRC / "core" / "protected_presentation.py"

CONTRACTS = (
    "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md",
    "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md",
    "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md",
    "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
    "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
    "docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md",
)

MODIFIED_HISTORICAL_TESTS = (
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
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout


def _facts(**updates) -> dict:
    facts = {
        "repository_identity": "repo-123",
        "repository_display": "pcae-harness",
        "task_id": "task-123",
        "task_display": "bounded certification task",
        "runtime_target_id": "local-cli.fixed-argv.v1",
        "runtime_target_display": "local fixed argv",
        "operation_effect_scope_display": "no network; one bounded attempt",
        "prompt_hash": "a" * 64,
        "prompt_instruction_display": "bounded harmless operation",
        "invocation_id": "inv-123",
        "invocation_display": "bounded invocation",
        "expires_at": "2099-01-01T00:00:00.000Z",
        "one_shot_notice": True,
    }
    facts.update(updates)
    return facts


def _request(decision: str = "APPROVE", *, request_id: str = "hpr-a") -> dict:
    facts = _facts()
    displayed = helper.render_human_visible_bytes(facts, renderer_profile="profile-v1")
    document = {
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
    document["request_digest"] = helper._self_excluding_digest(
        document, field="request_digest"
    )
    document["test_decision_directive"] = {
        "decision": decision,
        "displayed_digest_ack": hashlib.sha256(displayed).hexdigest(),
    }
    return document


def _launch(decision: str, monkeypatch=None, executable: str | None = None):
    fd = os.open(HELPER_PATH, os.O_RDONLY)
    if executable is not None:
        monkeypatch.setattr(presentation.sys, "executable", executable)
    return presentation._launch_and_exchange(fd, _request(decision), timeout_seconds=5)


def _terminal_election(monkeypatch, decision_bytes: bytes, displayed=b"bound display\n"):
    helper_end, human_end = socket.socketpair()
    human_end.sendall(decision_bytes)
    monkeypatch.setattr(helper.os, "open", lambda path, flags: os.dup(helper_end.fileno()))
    try:
        decision = helper._observe_election({}, displayed)
        rendered = human_end.recv(1 << 16)
    finally:
        helper_end.close()
        human_end.close()
    return decision, rendered


def test_01_phase_entry_and_historical_heads_are_primary_git_objects():
    assert _git("rev-parse", f"{REPAIR_IMPLEMENTATION}^").strip() == ENTRY
    assert _git("rev-parse", REPAIR_IMPLEMENTATION).strip() == REPAIR_IMPLEMENTATION
    assert "1R.30R.5R.2" in _git("log", "-1", "--format=%s", REPAIR_IMPLEMENTATION)
    assert "1R.30R.5R.1" in _git("log", "-1", "--format=%s", ENTRY)
    assert "1R.30R.4R.1" in _git("log", "-1", "--format=%s", PRESENTATION_HEAD)
    assert "1R.30R.5R" in _git("log", "-1", "--format=%s", IV_ENTRY)


def test_02_historical_blocked_report_preserved():
    text = (REPO / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_1_CTAP2_PIN_UV_REPAIR_IV_REAL_HARDWARE_VERIFICATION_AND_N_16_5_CLOSURE.md").read_text()
    assert "BLOCKED" in text and "finding H-2" in text and "N-16-5" in text


def test_03_h2_and_f2_are_reconstructed_from_the_entry_blob():
    old_helper = _git("show", f"{ENTRY}:src/pcae/protected_presentation_helper.py")
    old_launcher = _git("show", f"{ENTRY}:src/pcae/core/protected_presentation.py")
    observe = old_helper.split("def _observe_election", 1)[1].split("\n\ndef ", 1)[0]
    assert 'return "CANCEL"' in observe and "/dev/tty" not in observe
    assert '[sys.executable, "-I", plat_fd]' in old_launcher


def test_04_no_normative_contract_changed():
    assert _git("diff", "--name-only", ENTRY, "--", "docs/contracts").strip() == ""
    for rel in CONTRACTS:
        assert _git("diff", "--quiet", ENTRY, "--", rel) == ""


def test_05_production_diff_is_exactly_the_two_authorized_files():
    assert set(_git("diff", "--name-only", ENTRY, "--", "src/pcae").split()) == {
        "src/pcae/protected_presentation_helper.py",
        "src/pcae/core/protected_presentation.py",
    }


def test_06_test_directive_remains_non_real_and_forbidden_in_production():
    req = _request()
    req["ceremony_mode"] = "production"
    with pytest.raises(helper.ProtectedPresentationHelperError):
        helper._validate_request(req)


def test_07_production_election_uses_only_direct_trusted_tty():
    source = ast.parse(HELPER_PATH.read_text())
    observe = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "_observe_trusted_terminal_election")
    calls = {ast.unparse(n.func) for n in ast.walk(observe) if isinstance(n, ast.Call)}
    assert "os.open" in calls and "os.read" not in calls
    text = ast.get_source_segment(HELPER_PATH.read_text(), observe)
    assert "_TRUSTED_TTY_PATH" in text
    assert "sys.stdin" not in text and "input(" not in text


@pytest.mark.parametrize(
    "raw,expected",
    [(b"APPROVE\n", "APPROVE"), (b"REJECT\n", "REJECT")],
)
def test_08_explicit_closed_elections(monkeypatch, raw, expected):
    decision, rendered = _terminal_election(monkeypatch, raw)
    assert decision == expected
    assert rendered.startswith(b"bound display\n")
    assert helper._DECISION_PROMPT in rendered


@pytest.mark.parametrize(
    "raw",
    [b"\n", b"approve\n", b"yes\n", b"1\n", b" APPROVE\n", b"APPROVE \n", b"APPROVE\r\n", b"X" * 40 + b"\n"],
)
def test_09_empty_or_invalid_input_never_approves(monkeypatch, raw):
    assert _terminal_election(monkeypatch, raw)[0] == "CANCEL"


def test_10_no_tty_fails_closed_without_stdin_fallback(monkeypatch):
    monkeypatch.setenv("PCAE_PPLP_DECISION", "APPROVE")
    monkeypatch.setattr(helper.os, "open", lambda *_a, **_k: (_ for _ in ()).throw(OSError("no tty")))
    monkeypatch.setattr("builtins.input", lambda *_a: "APPROVE")
    assert helper._observe_election({}, b"display") == "CANCEL"


def test_11_eof_fails_closed(monkeypatch):
    left, right = socket.socketpair()
    right.close()
    monkeypatch.setattr(helper.os, "open", lambda *_a, **_k: os.dup(left.fileno()))
    try:
        assert helper._observe_election({}, b"display") == "CANCEL"
    finally:
        left.close()


def test_12_interruption_fails_closed(monkeypatch):
    monkeypatch.setattr(helper.os, "open", lambda *_a, **_k: 91)
    monkeypatch.setattr(helper, "_write_all", lambda *_a, **_k: None)
    monkeypatch.setattr(helper, "_read_one_terminal_line", lambda *_a: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr(helper.os, "close", lambda *_a: None)
    assert helper._observe_election({}, b"display") == "CANCEL"


def test_13_protocol_and_environment_cannot_select_production_approve(monkeypatch):
    monkeypatch.setenv("PCAE_AUTO_APPROVE", "APPROVE")
    monkeypatch.setattr(helper.os, "open", lambda *_a, **_k: (_ for _ in ()).throw(OSError()))
    request = {"decision": "APPROVE", "protocol_input": "APPROVE"}
    assert helper._observe_election(request, b"display") == "CANCEL"


@pytest.mark.parametrize("control", ["\x1b", "\r", "\n", "\t", "\x08", "\x7f", "\x9b", "\u202e", "\u2066"])
def test_14_all_untrusted_terminal_controls_are_neutralized(control):
    value = "before" + control + "[APPROVE] forged\nafter"
    neutral = helper.neutralize_untrusted_text(value)
    assert control not in neutral
    rendered = helper.render_human_visible_bytes(
        _facts(task_display=value), renderer_profile="profile-v1"
    ).decode()
    assert "\n[APPROVE] forged\n" not in rendered


def test_15_canonical_display_and_request_digest_are_exactly_bound():
    request = _request()
    displayed = helper.render_human_visible_bytes(
        request["human_visible_facts"], renderer_profile=request["renderer_profile"]
    )
    assert request["test_decision_directive"]["displayed_digest_ack"] == hashlib.sha256(displayed).hexdigest()
    assert helper._validate_request(request)["request_digest"] == request["request_digest"]


@pytest.mark.parametrize(
    "field",
    ["repository_identity", "task_id", "runtime_target_id", "prompt_hash", "invocation_id", "expires_at"],
)
def test_16_each_authority_relevant_visible_field_changes_display_digest(field):
    base = helper.render_human_visible_bytes(_facts(), renderer_profile="profile-v1")
    changed = _facts(**{field: "changed-value"})
    assert hashlib.sha256(base).digest() != hashlib.sha256(
        helper.render_human_visible_bytes(changed, renderer_profile="profile-v1")
    ).digest()


def test_17_response_substitution_is_rejected():
    request_a = _request(request_id="hpr-a")
    request_b = _request(request_id="hpr-b")
    displayed = helper.render_human_visible_bytes(_facts(), renderer_profile="profile-v1")
    response_a = helper._build_response(
        request_a, "APPROVE", hashlib.sha256(displayed).hexdigest(), now="2099-01-01T00:00:00.000Z"
    )
    with pytest.raises(presentation.ProtectedPresentationCeremonyError):
        presentation._validate_response(response_a, request_b, displayed_digest=hashlib.sha256(displayed).hexdigest())


def test_18_portable_launch_executes_current_helper_on_system_python39(monkeypatch):
    system_python = Path("/usr/bin/python3")
    assert system_python.exists()
    completed = subprocess.run(
        [str(system_python), "-c", "import sys; print(sys.version_info[:2])"],
        capture_output=True, text=True, check=True,
    )
    assert "(3, 9)" in completed.stdout
    response = _launch("APPROVE", monkeypatch, str(system_python))
    assert response["decision"] == "APPROVE"


def test_19_launch_has_no_dev_fd_path_shell_path_lookup_or_caller_argv():
    source = LAUNCHER_PATH.read_text()
    tree = ast.parse(source)
    attrs = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "posix_spawn" in attrs
    assert not ({"Popen", "run", "system", "popen", "execvp", "spawnvp"} & attrs)
    string_literals = {
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }
    assert not any(value.startswith(("/dev/fd/", "/proc/self/fd/")) for value in string_literals)
    assert '[sys.executable, "-I", "-c", _HELD_HELPER_BOOTSTRAP]' in source
    assert '"PATH"' not in source and "shell=True" not in source


def test_20_child_environment_is_closed_and_carries_no_decision_or_path():
    source = LAUNCHER_PATH.read_text()
    assert all(name in source for name in (
        "PCAE_PPLP_REQUEST_FD", "PCAE_PPLP_RESPONSE_FD", "PCAE_PPLP_HELPER_FD", "LC_ALL"
    ))
    for banned in ("PCAE_PPLP_DECISION", "PCAE_AUTO_APPROVE", "PCAE_HELPER_PATH", "PCAE_VERIFIER_KIND"):
        assert banned not in source


@pytest.mark.parametrize(
    "directive,outcome",
    [("APPROVE", "APPROVE"), ("REJECT", "REJECT"), ("NO_RESPONSE", None)],
)
def test_21_real_child_protocol_outcomes(directive, outcome):
    response = _launch(directive)
    assert (None if response is None else response["decision"]) == outcome


@pytest.mark.parametrize("directive", ["CRASH", "MALFORMED_RESPONSE"])
def test_22_abnormal_or_malformed_child_fails_closed(directive):
    with pytest.raises(presentation.ProtectedPresentationCeremonyError) as exc:
        _launch(directive)
    assert exc.value.terminal_reason_code == "helper_response_untrusted"


def test_23_held_descriptor_survives_path_substitution(tmp_path):
    original = b"print('trusted bytes')\n"
    path = tmp_path / "helper"
    path.write_bytes(original)
    path.chmod(0o500)
    verified = verify_helper_bytes(
        path,
        expected_sha256=hashlib.sha256(original).hexdigest(),
        deployment_owner_uid=os.getuid(),
        protected_root=tmp_path,
    )
    replacement = tmp_path / "replacement"
    replacement.write_bytes(b"print('substituted')\n")
    replacement.chmod(0o500)
    os.replace(replacement, path)
    try:
        assert os.read(verified.fd, 1 << 16) == original
    finally:
        os.close(verified.fd)


def test_24_launcher_revalidates_generation_before_evidence_persistence():
    text = LAUNCHER_PATH.read_text()
    first = text.index("response = _launch_and_exchange")
    revalidate = text.index("revalidated = _resolve_or_terminal", first)
    persist = text.index("evidence = _build_and_persist_evidence", revalidate)
    assert first < revalidate < persist


def test_25_evidence_writer_and_gate_semantics_are_unchanged():
    for rel in (
        "src/pcae/core/approval_presentation.py",
        "src/pcae/core/hpac_verifier.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    ):
        assert _git("diff", "--quiet", ENTRY, "--", rel) == ""


def test_26_no_runtime_effect_or_new_authority_surface():
    combined = HELPER_PATH.read_text() + LAUNCHER_PATH.read_text()
    tree = ast.parse(combined)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "DispatchEnvelope" not in names and "adapter" not in names
    assert "import socket" not in combined and "adapter.dispatch(" not in combined


def test_27_profiles_remain_local_and_supported_not_global():
    contract = (REPO / CONTRACTS[0]).read_text()
    assert "local interactive control-plane host" in contract
    assert "headless / remote / networked approval is out of scope" in contract
    status = (REPO / "PROJECT_STATUS.md").read_text()
    assert "one VERIFIED SUPPORTED REAL human-authentication" in status
    assert "mobile-only" in status.lower()


def test_28_repair_requires_fresh_independent_verification_before_closure():
    rhamp = (REPO / CONTRACTS[0]).read_text()
    ppa = (REPO / CONTRACTS[1]).read_text()
    normalized_rhamp = " ".join(rhamp.split())
    assert "each is its own explicitly human-authorized phase with its own independent-verification pair" in normalized_rhamp
    assert "must be followed by a fresh\n  independent verification" in ppa


def test_29_historical_test_definitions_not_removed_renamed_or_skipped():
    for rel in MODIFIED_HISTORICAL_TESTS:
        old = ast.parse(_git("show", f"{ENTRY}:{rel}"))
        new = ast.parse((REPO / rel).read_text())
        old_names = {n.name for n in ast.walk(old) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")}
        new_names = {n.name for n in ast.walk(new) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")}
        assert old_names <= new_names, (rel, sorted(old_names - new_names))
        for node in ast.walk(new):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                decorators = " ".join(ast.unparse(d) for d in node.decorator_list)
                assert not any(mark in decorators for mark in ("skip", "skipif", "xfail"))


def test_30_no_wildcard_or_fnmatch_guard_broadening():
    diff = _git("diff", ENTRY, "--", *MODIFIED_HISTORICAL_TESTS)
    added = "\n".join(line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    assert "fnmatch" not in added
    assert "rglob" not in added and "glob(" not in added


def test_31_runtime_and_n16_later_stages_are_untouched():
    assert _git("diff", "--name-only", ENTRY, "--", "src/pcae/core/runtime_introspection.py").strip() == ""
    for token in ("N-16-6", "N-16-7"):
        assert token in (REPO / "PROJECT_STATUS.md").read_text()


def test_32_helper_source_is_python39_parseable():
    system_python = Path("/usr/bin/python3")
    assert system_python.exists()
    result = subprocess.run(
        [str(system_python), "-c", "import ast,sys; ast.parse(sys.stdin.read())"],
        input=HELPER_PATH.read_text(), text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "rel",
    [
        "src/pcae/core/hpac_rhamp_ctap2.py",
        "src/pcae/core/human_authenticator_fido2.py",
        "src/pcae/core/hpac_rhamp_enrollment.py",
        "src/pcae/core/hpac_rhamp_credential_sidecar.py",
        "src/pcae/core/hpac_rhamp_counter_state.py",
        "src/pcae/core/hpac_verifier.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/approval_presentation.py",
        "src/pcae/core/protected_presentation_installation.py",
        "src/pcae/core/hpac_protected_presentation_admin.py",
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_introspection.py",
    ],
)
def test_33_forbidden_production_surfaces_are_byte_unchanged(rel):
    assert _git("diff", "--quiet", ENTRY, "--", rel) == ""


def test_34_fresh_suite_has_no_skip_xfail_or_fnmatch_calls():
    tree = ast.parse(Path(__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = " ".join(ast.unparse(d) for d in node.decorator_list)
            assert not any(mark in decorators for mark in ("skip", "skipif", "xfail"))
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            assert name not in {"skip", "xfail", "fnmatch", "fnmatchcase"}
