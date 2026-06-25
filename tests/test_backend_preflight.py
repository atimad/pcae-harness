from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(extra_args: list[str] | None = None) -> dict:
    cmd = [sys.executable, "-m", "pcae", "preflight", "backend", "--json"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


def _pf(extra_args: list[str] | None = None) -> dict:
    return _run(extra_args)["preflight"]


# --- Command exists ---


def test_command_exits_successfully():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "backend", "--json",
         "--requested-backend", "claude", "--requested-action", "backend_invocation"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_command_output_is_valid_json():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "backend", "--json",
         "--requested-backend", "claude", "--requested-action", "backend_invocation"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    data = json.loads(result.stdout)
    assert isinstance(data, dict)


# --- JSON envelope fields ---


def test_envelope_schema_version():
    data = _run(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert data["schema_version"] == "0.1"


def test_envelope_source_command():
    data = _run(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert data["source_command"] == "pcae preflight backend"


def test_envelope_has_preflight():
    data = _run(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert "preflight" in data


def test_envelope_has_safety_notes():
    data = _run(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert isinstance(data["safety_notes"], dict)


# --- Preflight object fields ---


def test_preflight_has_all_required_fields():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "abc123"])
    required = [
        "preflight_type", "requested_backend", "requested_action", "requested_files",
        "decision", "reason_codes", "backend_known", "backend_allowed_by_policy",
        "prompt_present", "prompt_required", "prompt_hash_present", "prompt_hash_required",
        "scope_preflight_required", "scope_preflight_decision",
        "human_review_required", "more_evidence_required",
        "task_contract_detected", "task_contract_path", "lifecycle_state",
        "evidence_sources", "backend_notes",
        "authorization_granted", "execution_authorized",
        "backend_invocation_performed", "prompt_sent", "capture_performed",
        "repo_mutation_performed", "storage_written",
    ]
    for field in required:
        assert field in pf, f"Missing field: {field}"


def test_preflight_type():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert pf["preflight_type"] == "backend_invocation_preflight"


# --- Known backend recognized ---


def test_claude_recognized():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True
    assert "backend_known" in pf["reason_codes"]


def test_claude_deepseek_recognized():
    pf = _pf(["--requested-backend", "claude-deepseek", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True


def test_claude_kimi_recognized():
    pf = _pf(["--requested-backend", "claude-kimi", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True


def test_codex_recognized():
    pf = _pf(["--requested-backend", "codex", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True


def test_subagent_recognized():
    pf = _pf(["--requested-backend", "subagent", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True


# --- Unknown backend blocked ---


def test_unknown_backend_denied():
    pf = _pf(["--requested-backend", "unknown_backend", "--requested-action", "backend_invocation",
              "--prompt-present"])
    assert pf["decision"] == "deny_preflight"
    assert pf["backend_known"] is False
    assert "backend_unknown" in pf["reason_codes"]


def test_random_backend_denied():
    pf = _pf(["--requested-backend", "some_random_ai", "--requested-action", "backend_invocation"])
    assert pf["decision"] == "deny_preflight"
    assert pf["backend_known"] is False


# --- Missing task contract ---


# (task contract is present in repo, so test known backend with contract)
def test_task_contract_detected():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["task_contract_detected"] is True


# --- Prompt handling ---


def test_prompt_missing_blocks():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert pf["decision"] == "blocked_by_missing_prompt"
    assert pf["prompt_present"] is False
    assert "missing_prompt" in pf["reason_codes"]


def test_prompt_present_reflected():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present"])
    assert pf["prompt_present"] is True
    assert "prompt_present" in pf["reason_codes"]


def test_prompt_hash_reflected():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "sha256abc"])
    assert pf["prompt_hash_present"] is True
    assert "prompt_hash_present" in pf["reason_codes"]


def test_prompt_present_no_hash_requires_evidence():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present"])
    assert pf["decision"] == "requires_more_evidence"
    assert pf["more_evidence_required"] is True


def test_prompt_with_hash_requires_review():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "requires_human_review"
    assert pf["human_review_required"] is True


# --- File-related scope relationship ---


def test_file_request_scope_evaluated():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md", "--prompt-present", "--prompt-hash", "h1"])
    assert pf["scope_preflight_required"] is True
    assert pf["scope_preflight_decision"] is not None


def test_file_forbidden_scope_blocks():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "source_mutation",
              "--requested-file", "README.md", "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "blocked_by_scope"
    assert "scope_preflight_denied" in pf["reason_codes"]


# --- Scope allow does not authorize backend ---


def test_scope_allow_still_requires_review():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md", "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "requires_human_review"
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert pf["backend_invocation_performed"] is False


# --- Human review required for every backend invocation ---


def test_human_review_always_required():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["human_review_required"] is True


# --- Unknown action ---


def test_unknown_action_requires_review():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "unknown",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "requires_human_review"
    assert "unknown_action" in pf["reason_codes"]


def test_unrecognized_action():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "destroy_everything",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "requires_human_review"
    assert "unknown_action" in pf["reason_codes"]


# --- Safety flags always false ---


def test_authorization_granted_false():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False


def test_execution_authorized_false():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["execution_authorized"] is False


def test_backend_invocation_performed_false():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_invocation_performed"] is False


def test_prompt_sent_false():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["prompt_sent"] is False


def test_capture_performed_false():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["capture_performed"] is False


def test_repo_mutation_performed_false():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert pf["repo_mutation_performed"] is False


def test_storage_written_false():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert pf["storage_written"] is False


# --- No cache/state/.pcae files ---


def test_no_pcae_backend_files():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [pcae_dir / "backend", pcae_dir / "backend_preflight",
            pcae_dir / "cache", pcae_dir / "preflight"]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-backend", "claude", "--requested-action", "backend_invocation",
          "--prompt-present"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"


def test_no_repository_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-backend", "claude", "--requested-action", "backend_invocation",
          "--prompt-present"])
    r2 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before


# --- Existing commands still work ---


def test_scope_preflight_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "scope", "--json",
         "--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["preflight"]["decision"] == "allow_preflight"


def test_gate_dry_run_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["gate_count"] == 15


def test_intelligence_commands_still_work():
    for cmd in ["artifact-index", "memory-snapshot", "governance-timeline",
                "decision-log", "risk-register", "project-state"]:
        result = subprocess.run(
            [sys.executable, "-m", "pcae", cmd, "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"{cmd} failed"


# --- Safety notes ---


def test_safety_notes_backend_preflight_only():
    data = _run(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    sn = data["safety_notes"]
    assert sn["backend_preflight_only"] is True
    assert sn["backend_preflight_does_not_invoke_backends"] is True
    assert sn["backend_preflight_does_not_send_prompts"] is True
    assert sn["backend_preflight_does_not_capture_outputs"] is True
    assert sn["backend_preflight_does_not_mutate_repo"] is True
    assert sn["backend_preflight_does_not_intercept_shell"] is True
    assert sn["scope_preflight_is_separate"] is True
    assert sn["permission_broker_not_implemented"] is True
    assert sn["shell_gate_not_implemented"] is True
    assert sn["storage_not_implemented"] is True


# --- Reason code disclaimer ---


def test_reason_code_disclaimer_present():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert "backend_preflight_only_not_execution_authorization" in pf["reason_codes"]


# --- Plain text output ---


def test_plain_text_output():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "backend",
         "--requested-backend", "claude", "--requested-action", "backend_invocation"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "Backend invocation preflight evaluation" in result.stdout
    assert "Decision:" in result.stdout
