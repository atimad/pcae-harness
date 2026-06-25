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


# ===== Known backend exact recognition =====


def test_claude_known():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True
    assert "backend_known" in pf["reason_codes"]


def test_claude_deepseek_known():
    pf = _pf(["--requested-backend", "claude-deepseek", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True


def test_claude_kimi_known():
    pf = _pf(["--requested-backend", "claude-kimi", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True


def test_codex_known():
    pf = _pf(["--requested-backend", "codex", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True


def test_subagent_known():
    pf = _pf(["--requested-backend", "subagent", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_known"] is True


# ===== Unknown backend denial =====


def test_unknown_backend_denied():
    pf = _pf(["--requested-backend", "unknown_backend", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "deny_preflight"
    assert pf["backend_known"] is False


def test_random_ai_denied():
    pf = _pf(["--requested-backend", "random_ai_v2", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "deny_preflight"


def test_empty_string_backend_denied():
    pf = _pf(["--requested-backend", "", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "deny_preflight"
    assert pf["backend_known"] is False


# ===== All known backends require human review =====


def test_claude_requires_review():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["human_review_required"] is True


def test_claude_deepseek_requires_review():
    pf = _pf(["--requested-backend", "claude-deepseek", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["human_review_required"] is True


def test_codex_requires_review():
    pf = _pf(["--requested-backend", "codex", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["human_review_required"] is True


def test_subagent_requires_review():
    pf = _pf(["--requested-backend", "subagent", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["human_review_required"] is True


# ===== Backend recognition does not authorize =====


def test_known_backend_no_authorization():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert pf["backend_invocation_performed"] is False


def test_known_backend_policy_false():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["backend_allowed_by_policy"] is False


# ===== Missing prompt =====


def test_missing_prompt_blocks():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert pf["decision"] == "blocked_by_missing_prompt"
    assert "missing_prompt" in pf["reason_codes"]
    assert pf["prompt_present"] is False


def test_missing_prompt_for_source_mutation():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "source_mutation"])
    assert pf["decision"] == "blocked_by_missing_prompt"


# ===== Prompt present without hash =====


def test_prompt_no_hash_requires_evidence():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present"])
    assert pf["decision"] == "requires_more_evidence"
    assert pf["prompt_present"] is True
    assert pf["prompt_hash_present"] is False
    assert pf["more_evidence_required"] is True


# ===== Prompt present with hash =====


def test_prompt_with_hash_requires_review():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "sha256_abc123"])
    assert pf["decision"] == "requires_human_review"
    assert pf["prompt_present"] is True
    assert pf["prompt_hash_present"] is True
    assert pf["human_review_required"] is True


# ===== Invalid/empty prompt hash =====


def test_empty_prompt_hash_treated_as_missing():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", ""])
    assert pf["prompt_hash_present"] is False
    assert pf["decision"] == "requires_more_evidence"


# ===== File-related scope relationship =====


def test_file_request_evaluates_scope():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["scope_preflight_required"] is True
    assert pf["scope_preflight_decision"] is not None


# ===== Scope allow does not authorize backend =====


def test_scope_allow_still_review():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "requires_human_review"
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False


# ===== Scope denied blocks =====


def test_scope_denied_blocks():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "source_mutation",
              "--requested-file", "README.md",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "blocked_by_scope"
    assert "scope_preflight_denied" in pf["reason_codes"]


# ===== Forbidden file blocks =====


def test_forbidden_file_blocks():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "docs_mutation",
              "--requested-file", "docs/REAL_CAPTURED_TASKS.md",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "blocked_by_scope"


# ===== Out-of-scope file =====


def test_out_of_scope_file():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "source_mutation",
              "--requested-file", "some_nonexistent_file.py",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] in ("requires_human_review", "requires_more_evidence")


# ===== Multi-file all in scope =====


def test_multi_file_all_allowed():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "read",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "CHANGELOG.md",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "requires_human_review"
    assert pf["scope_preflight_decision"] == "allowed"


# ===== Multi-file mixed allowed/forbidden =====


def test_multi_file_forbidden_blocks():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "docs_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "README.md",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "blocked_by_scope"


# ===== Multi-file mixed allowed/unknown =====


def test_multi_file_unknown_partial():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "source_mutation",
              "--requested-file", "PROJECT_STATUS.md",
              "--requested-file", "some_unknown_file.py",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] in ("requires_human_review", "requires_more_evidence")
    assert pf["scope_preflight_decision"] == "partial"


# ===== Unknown action =====


def test_unknown_action():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "unknown",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "requires_human_review"
    assert "unknown_action" in pf["reason_codes"]


def test_unrecognized_action():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "teleport_files",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["decision"] == "requires_human_review"
    assert "unknown_action" in pf["reason_codes"]


# ===== High-risk actions non-authorizing =====


def test_commit_action_non_authorizing():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "commit",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False


def test_push_action_non_authorizing():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "push",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False


def test_adoption_action_non_authorizing():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "adoption",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False


def test_storage_write_action_non_authorizing():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "storage_write",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False


def test_rollback_action_non_authorizing():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "rollback",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False


# ===== Safety flags always false =====


def test_all_safety_flags_false_on_allow_path():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert pf["backend_invocation_performed"] is False
    assert pf["prompt_sent"] is False
    assert pf["capture_performed"] is False
    assert pf["repo_mutation_performed"] is False
    assert pf["storage_written"] is False


def test_all_safety_flags_false_on_deny_path():
    pf = _pf(["--requested-backend", "unknown_backend", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert pf["backend_invocation_performed"] is False
    assert pf["prompt_sent"] is False
    assert pf["capture_performed"] is False
    assert pf["repo_mutation_performed"] is False
    assert pf["storage_written"] is False


def test_all_safety_flags_false_on_blocked_path():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert pf["backend_invocation_performed"] is False
    assert pf["prompt_sent"] is False
    assert pf["capture_performed"] is False
    assert pf["repo_mutation_performed"] is False
    assert pf["storage_written"] is False


# ===== No cache/state/.pcae files =====


def test_no_pcae_artifacts_created():
    pcae_dir = REPO_ROOT / ".pcae"
    dirs = [pcae_dir / "backend", pcae_dir / "backend_preflight",
            pcae_dir / "cache", pcae_dir / "preflight", pcae_dir / "prompts"]
    before = {d: d.exists() for d in dirs}
    _run(["--requested-backend", "claude", "--requested-action", "backend_invocation",
          "--prompt-present", "--prompt-hash", "h1"])
    _run(["--requested-backend", "unknown_backend", "--requested-action", "backend_invocation"])
    _run(["--requested-backend", "claude", "--requested-action", "source_mutation",
          "--requested-file", "README.md", "--prompt-present"])
    for d, existed in before.items():
        if not existed:
            assert not d.exists(), f"{d} was created"


def test_no_repository_mutation():
    r1 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    before = r1.stdout
    _run(["--requested-backend", "claude", "--requested-action", "backend_invocation",
          "--prompt-present", "--prompt-hash", "h1"])
    _run(["--requested-backend", "unknown_backend", "--requested-action", "backend_invocation"])
    r2 = subprocess.run(["git", "status", "--porcelain"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r2.stdout == before


# ===== Existing commands still work =====


def test_scope_preflight_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "preflight", "scope", "--json",
         "--requested-action", "read", "--requested-file", "PROJECT_STATUS.md"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["preflight"]["decision"] == "allow_preflight"


def test_gate_dry_run_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "gate-dry-run", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["gate_count"] == 15


def test_intelligence_commands_still_work():
    for cmd in ["artifact-index", "memory-snapshot", "governance-timeline",
                "decision-log", "risk-register", "project-state"]:
        result = subprocess.run(
            [sys.executable, "-m", "pcae", cmd, "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"{cmd} failed"


# ===== Reason code disclaimer =====


def test_disclaimer_on_review():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert "backend_preflight_only_not_execution_authorization" in pf["reason_codes"]


def test_disclaimer_on_deny():
    pf = _pf(["--requested-backend", "unknown_backend", "--requested-action", "backend_invocation",
              "--prompt-present", "--prompt-hash", "h1"])
    assert "backend_preflight_only_not_execution_authorization" in pf["reason_codes"]


def test_disclaimer_on_blocked():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "backend_invocation"])
    assert "backend_preflight_only_not_execution_authorization" in pf["reason_codes"]


# ===== Determinism =====


def test_deterministic_output():
    args = ["--requested-backend", "claude", "--requested-action", "backend_invocation",
            "--prompt-present", "--prompt-hash", "h1"]
    pf1 = _pf(args)
    pf2 = _pf(args)
    assert pf1["decision"] == pf2["decision"]
    assert pf1["reason_codes"] == pf2["reason_codes"]
    assert pf1["backend_known"] == pf2["backend_known"]


# ===== Read action with backend =====


def test_read_action_non_authorizing():
    pf = _pf(["--requested-backend", "claude", "--requested-action", "read",
              "--prompt-present", "--prompt-hash", "h1"])
    assert pf["authorization_granted"] is False
    assert pf["execution_authorized"] is False
    assert pf["backend_invocation_performed"] is False
