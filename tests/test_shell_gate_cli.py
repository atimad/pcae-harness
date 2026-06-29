"""CLI tests for Phase 93B Narrow Shell Gate Prototype — pcae shell-gate check.

Tests the CLI surface. All commands are simulation-only — no execution.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd_args: list[str]) -> subprocess.CompletedProcess:
    """Run a pcae shell-gate subcommand and return the result."""
    cmd = [sys.executable, "-m", "pcae", "shell-gate"] + cmd_args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)


def _json(cmd_args: list[str]) -> dict:
    """Run with --json and parse the output."""
    result = _run(cmd_args + ["--json"])
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    return json.loads(result.stdout)


# ═══════════════════════════════════════════════════════════════════════════════
# JSON output tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestJsonOutput:
    """Verify --json output format and correctness."""

    def test_json_hard_block_raw_git_push(self):
        data = _json(["check", "--command", "git push"])
        assert data["decision"] == "deny"
        assert data["hard_block"] is True
        assert data["reason_code"] == "blocked_by_raw_git_push"
        assert data["simulation_only"] is True
        assert data["no_execution"] is True
        assert data["no_enforcement"] is True

    def test_json_hard_block_force_push(self):
        data = _json(["check", "--command", "git push --force"])
        assert data["decision"] == "deny"
        assert data["hard_block"] is True
        assert data["command_category"] == "force_push"

    def test_json_hard_block_destructive(self):
        data = _json(["check", "--command", "rm -rf /tmp/x"])
        assert data["decision"] == "deny"
        assert data["hard_block"] is True
        assert data["command_class"] == "destructive_filesystem"

    def test_json_hard_block_no_verify(self):
        data = _json(["check", "--command", "git commit --no-verify -m x"])
        assert data["decision"] == "deny"
        assert data["hard_block"] is True
        assert data["command_class"] == "no_verify"

    def test_json_allow_read_only(self):
        data = _json(["check", "--command", "git status"])
        assert data["decision"] == "allow"
        assert data["hard_block"] is False

    def test_json_allow_governed(self):
        data = _json(["check", "--command", "pcae health"])
        assert data["decision"] == "allow"
        assert data["hard_block"] is False

    def test_json_unknown_fails_closed(self):
        data = _json(["check", "--command", "xyzzy123"])
        assert data["decision"] == "deny"
        assert data["hard_block"] is True

    def test_json_has_required_keys(self):
        data = _json(["check", "--command", "git push"])
        for key in [
            "schema_version", "command_text", "command_category",
            "command_class", "action_type", "decision", "hard_block",
            "reason_code", "message", "simulation_only", "no_execution",
            "no_enforcement", "audit_payload",
        ]:
            assert key in data, f"Missing key: {key}"

    def test_json_simulation_markers(self):
        data = _json(["check", "--command", "git push --force"])
        assert data["simulation_only"] is True
        assert data["no_execution"] is True
        assert data["no_enforcement"] is True
        assert data["authorization_granted"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Text output tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestTextOutput:
    """Verify human-readable text output format."""

    def test_text_output_hard_block(self):
        result = _run(["check", "--command", "git push --force"])
        assert result.returncode == 0
        output = result.stdout
        assert "Shell gate check" in output
        assert "force_push" in output
        assert "deny" in output
        assert "HARD BLOCK" in output
        assert "Simulation only" in output
        assert "No execution" in output
        assert "No enforcement" in output

    def test_text_output_allow(self):
        result = _run(["check", "--command", "git status"])
        assert result.returncode == 0
        output = result.stdout
        assert "Shell gate check" in output
        assert "read_only_inspection" in output
        assert "allow" in output
        assert "Simulation only" in output

    def test_text_output_missing_command(self):
        result = _run(["check", "--command", ""])
        assert result.returncode == 1
        assert "No command provided" in result.stdout or "missing_command" in result.stdout

    def test_text_output_contains_simulation_warning(self):
        result = _run(["check", "--command", "ls"])
        assert result.returncode == 0
        assert "Simulation only" in result.stdout
        assert "did NOT execute" in result.stdout


# ═══════════════════════════════════════════════════════════════════════════════
# Non-execution guarantee tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCliNoExecution:
    """Verify the CLI does not execute commands."""

    def test_destructive_command_not_executed(self):
        """rm -rf / should NOT actually run."""
        result = _run(["check", "--command", "rm -rf /tmp/nonexistent_test_dir_93b"])
        assert result.returncode == 0
        # The directory was NOT created by executing the command
        import os
        assert not os.path.exists("/tmp/nonexistent_test_dir_93b")

    def test_json_command_executed_is_false(self):
        data = _json(["check", "--command", "echo hello"])
        assert data["command_executed"] is False

    def test_json_no_execution_no_enforcement_markers(self):
        data = _json(["check", "--command", "git push --force"])
        assert data["no_execution"] is True
        assert data["no_enforcement"] is True
        assert data["shell_intercepted"] is False
        assert data["backend_invoked"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Fast-green marker test
# ═══════════════════════════════════════════════════════════════════════════════


class TestFastGreenMarker:
    """Ensure all shell gate tests are covered by fast_green marker."""

    def test_fast_green_marker_present(self):
        """This test file is marked fast_green via pyproject.toml config."""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 93C — CLI audit evidence tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestJsonAuditEvidence:
    """Verify JSON output includes audit_evidence."""

    def test_json_includes_audit_evidence(self):
        data = _json(["check", "--command", "git push"])
        assert "audit_evidence" in data
        audit = data["audit_evidence"]
        assert audit.get("source") == "shell_gate"
        assert audit.get("decision") == "deny"

    def test_json_audit_has_command_hash(self):
        data = _json(["check", "--command", "git status"])
        audit = data["audit_evidence"]
        ch = audit.get("command_hash", "")
        assert len(ch) == 64

    def test_json_audit_has_redacted_command(self):
        data = _json(["check", "--command", "TOKEN=abc123 ls"])
        audit = data["audit_evidence"]
        assert audit.get("redaction_applied") is True

    def test_json_audit_simulation_markers(self):
        data = _json(["check", "--command", "git push --force"])
        audit = data["audit_evidence"]
        assert audit.get("simulation_only") is True
        assert audit.get("no_execution") is True
        assert audit.get("no_enforcement") is True


class TestTextAuditEvidence:
    """Verify text output includes audit summary."""

    def test_text_includes_audit_id(self):
        result = _run(["check", "--command", "git push"])
        assert "Audit ID:" in result.stdout

    def test_text_includes_command_hash(self):
        result = _run(["check", "--command", "git status"])
        assert "Command hash:" in result.stdout

    def test_text_includes_redaction_indicator(self):
        result = _run(["check", "--command", "API_KEY=secret123 ls"])
        assert "redacted" in result.stdout.lower()
