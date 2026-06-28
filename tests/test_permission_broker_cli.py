"""CLI tests for Phase 91B permission broker commands.

Tests pcae permission-broker status, explain, and check commands.
All commands are simulation-only — no enforcement, no execution.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd_args: list[str]) -> subprocess.CompletedProcess:
    """Run a pcae permission-broker subcommand and return the result."""
    cmd = [sys.executable, "-m", "pcae", "permission-broker"] + cmd_args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)


def _json(cmd_args: list[str]) -> dict:
    """Run with --json and parse the output."""
    result = _run(cmd_args + ["--json"])
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


# ═══════════════════════════════════════════════════════════════════════════════
# status
# ═══════════════════════════════════════════════════════════════════════════════


def test_status_text():
    result = _run(["status"])
    assert result.returncode == 0
    assert "Simulation only" in result.stdout
    assert "no enforcement" in result.stdout


def test_status_json():
    data = _json(["status"])
    assert data["broker_available"] is True
    assert data["simulation_only"] is True
    assert data["no_enforcement"] is True
    assert data["no_execution"] is True
    assert data["enforcement_ready"] is False
    assert data["enforcement_authorized"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# explain
# ═══════════════════════════════════════════════════════════════════════════════


def test_explain_known_reason_code_text():
    result = _run(["explain", "--reason-code", "blocked_by_force_push"])
    assert result.returncode == 0
    assert "blocked_by_force_push" in result.stdout
    assert "hard_block" in result.stdout


def test_explain_known_reason_code_json():
    data = _json(["explain", "--reason-code", "blocked_by_raw_git_push"])
    assert data["reason_code"] == "blocked_by_raw_git_push"
    assert data["explanation"]["category"] == "hard_block"


def test_explain_unknown_reason_code_fails_safe_text():
    result = _run(["explain", "--reason-code", "nonexistent_code"])
    assert result.returncode != 0


def test_explain_unknown_reason_code_fails_safe_json():
    result = _run(["explain", "--reason-code", "nonexistent_code", "--json"])
    assert result.returncode != 0
    data = json.loads(result.stdout)
    assert data.get("error") == "unknown_reason_code"


def test_explain_missing_reason_code():
    result = _run(["explain"])
    assert result.returncode != 0


def test_explain_more_evidence_code():
    data = _json(["explain", "--reason-code", "task_scope_unknown"])
    assert data["explanation"]["category"] == "more_evidence"


def test_explain_human_review_code():
    data = _json(["explain", "--reason-code", "commit_requires_human_review"])
    assert data["explanation"]["category"] == "human_review"


def test_explain_allow_code():
    data = _json(["explain", "--reason-code", "allow_preflight_only"])
    assert data["explanation"]["category"] == "allow"


# ═══════════════════════════════════════════════════════════════════════════════
# check — allow
# ═══════════════════════════════════════════════════════════════════════════════


def test_check_allow_text():
    result = _run(["check", "--action-type", "read", "--command-class", "read_only"])
    assert result.returncode == 0
    assert "allow" in result.stdout.lower()
    assert "Simulation only" in result.stdout


def test_check_allow_json():
    data = _json([
        "check", "--action-type", "read", "--command-class", "read_only",
    ])
    assert data["decision"] == "allow"
    assert data["hard_block"] is False
    assert data["simulation_only"] is True
    assert data["no_execution"] is True
    assert data["no_enforcement"] is True


def test_check_allow_mutation_with_full_evidence():
    data = _json([
        "check",
        "--action-type", "source_mutation",
        "--command-class", "governed",
        "--path", "src/pcae/core/example.py",
        "--task-present",
        "--task-scope-known",
        "--allowed-path", "src/pcae/core/example.py",
        "--readiness-ready",
        "--enforcement-authorized",
    ])
    assert data["decision"] == "allow"


# ═══════════════════════════════════════════════════════════════════════════════
# check — hard-block
# ═══════════════════════════════════════════════════════════════════════════════


def test_check_hard_block_raw_git_commit():
    data = _json([
        "check", "--action-type", "source_mutation",
        "--command-class", "raw_git_commit",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True
    assert "blocked_by_raw_git_commit" in data["reason_code"]


def test_check_hard_block_raw_git_push():
    data = _json([
        "check", "--action-type", "push", "--command-class", "raw_git_push",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True


def test_check_hard_block_force_push():
    data = _json([
        "check", "--action-type", "push", "--command-class", "force_push",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True
    assert data["reason_code"] == "blocked_by_force_push"


def test_check_hard_block_no_verify():
    data = _json([
        "check", "--action-type", "commit", "--command-class", "no_verify",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True
    assert data["reason_code"] == "blocked_by_no_verify"


def test_check_hard_block_destructive_fs():
    data = _json([
        "check", "--action-type", "source_mutation",
        "--command-class", "destructive_filesystem",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True


def test_check_hard_block_out_of_scope():
    data = _json([
        "check",
        "--action-type", "source_mutation",
        "--command-class", "governed",
        "--path", "src/pcae/core/other.py",
        "--task-present",
        "--task-scope-known",
        "--allowed-path", "src/pcae/core/example.py",
        "--readiness-ready",
        "--enforcement-authorized",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True
    assert data["reason_code"] == "blocked_by_out_of_scope"


def test_check_hard_block_forbidden_path():
    data = _json([
        "check",
        "--action-type", "docs_mutation",
        "--command-class", "governed",
        "--path", "README.md",
        "--task-present",
        "--task-scope-known",
        "--allowed-path", "README.md",
        "--allowed-path", "PROJECT_STATUS.md",
        "--readiness-ready",
        "--enforcement-authorized",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True


def test_check_hard_block_missing_task():
    data = _json([
        "check",
        "--action-type", "source_mutation",
        "--command-class", "governed",
        "--readiness-ready",
        "--enforcement-authorized",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True
    assert data["reason_code"] == "blocked_by_missing_task"


def test_check_hard_block_unknown_command_class():
    data = _json([
        "check", "--action-type", "read", "--command-class", "unknown",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# check — more_evidence
# ═══════════════════════════════════════════════════════════════════════════════


def test_check_more_evidence_unknown_scope():
    data = _json([
        "check",
        "--action-type", "source_mutation",
        "--command-class", "governed",
        "--task-present",
        "--readiness-ready",
        "--enforcement-authorized",
    ])
    assert data["decision"] == "more_evidence"
    assert data["reason_code"] == "task_scope_unknown"


def test_check_more_evidence_missing_action():
    data = _json([
        "check", "--action-type", "",
    ])
    assert data["decision"] == "more_evidence"


# ═══════════════════════════════════════════════════════════════════════════════
# check — human_review
# ═══════════════════════════════════════════════════════════════════════════════


def test_check_human_review_backend():
    data = _json([
        "check",
        "--action-type", "backend_invocation",
        "--command-class", "backend_invocation",
        "--task-present",
        "--task-scope-known",
    ])
    assert data["decision"] == "human_review"
    assert data["hard_block"] is False


def test_check_human_review_commit_no_approval():
    data = _json([
        "check",
        "--action-type", "commit",
        "--command-class", "governed",
        "--task-present",
        "--task-scope-known",
        "--readiness-ready",
        "--enforcement-authorized",
    ])
    assert data["decision"] == "human_review"


# ═══════════════════════════════════════════════════════════════════════════════
# check — approval and accepted risk cannot override hard blocks
# ═══════════════════════════════════════════════════════════════════════════════


def test_check_approval_cannot_override_force_push():
    data = _json([
        "check",
        "--action-type", "push",
        "--command-class", "force_push",
        "--approval-present",
        "--approval-fresh",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True


def test_check_accepted_risk_cannot_override_destructive():
    data = _json([
        "check",
        "--action-type", "source_mutation",
        "--command-class", "destructive_filesystem",
        "--accepted-risk-present",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# check — simulation invariants
# ═══════════════════════════════════════════════════════════════════════════════


def test_check_simulation_only_marker():
    data = _json(["check", "--action-type", "read", "--command-class", "read_only"])
    assert data["simulation_only"] is True
    assert data["no_execution"] is True
    assert data["no_enforcement"] is True
    assert data["authorization_granted"] is False


def test_check_never_executes():
    """CLI must never execute the proposed command — only evaluate metadata."""
    result = _run(["check", "--action-type", "read", "--command-class", "read_only"])
    assert "Simulation only" in result.stdout
    assert "did NOT execute" in result.stdout


def test_check_malformed_input_fails_safe():
    """Unknown command class should return deny, not crash."""
    data = _json([
        "check", "--action-type", "read", "--command-class", "bogus",
    ])
    assert data["decision"] == "deny"
    assert data["hard_block"] is True
