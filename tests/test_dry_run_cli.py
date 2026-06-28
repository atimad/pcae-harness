"""
Dry-run blocking simulation CLI tests — Phase 89D.

Subprocess-based tests that verify pcae dry-run check/explain/status
CLI behavior, exit codes, JSON stability, and human-readable output.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _cli(*args: str) -> subprocess.CompletedProcess:
    """Run pcae dry-run with given arguments, return CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "pcae", "dry-run"] + list(args),
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


def _cli_json(*args: str) -> dict:
    """Run pcae dry-run with --json, return parsed dict."""
    result = _cli(*args, "--json")
    assert result.returncode in (0, 1), f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)


# ═══════════════════════════════════════════════════════════════════════════════
# Exit Code Review
# ═══════════════════════════════════════════════════════════════════════════════

class TestExitCodes:
    """Differentiated exit codes: 0=allow, 1=blocked, nonzero for errors."""

    def test_read_only_exit_0(self):
        r = _cli("check", "--command", "git status")
        assert r.returncode == 0, f"read-only should exit 0, got {r.returncode}"

    def test_governed_pcae_exit_0(self):
        r = _cli("check", "--command", "pcae health")
        assert r.returncode == 0

    def test_blocked_exit_1(self):
        r = _cli("check", "--command", "git push")
        assert r.returncode == 1, f"blocked should exit 1, got {r.returncode}"

    def test_force_push_exit_1(self):
        r = _cli("check", "--command", "git push --force")
        assert r.returncode == 1

    def test_review_required_exit_0(self):
        # Human review is not a block — exit 0
        r = _cli("check", "--command", "OPENAI_API_KEY=x python script.py")
        assert r.returncode == 0

    def test_missing_command_exits_nonzero(self):
        r = _cli("check")
        assert r.returncode != 0, "missing --command should fail"

    def test_explain_exits_0(self):
        r = _cli("explain", "--decision", "would_block_by_raw_git_push")
        assert r.returncode == 0

    def test_status_exits_0(self):
        r = _cli("status")
        assert r.returncode == 0


# ═══════════════════════════════════════════════════════════════════════════════
# CLI JSON Stability
# ═══════════════════════════════════════════════════════════════════════════════

class TestCliJsonStability:
    """CLI --json output is valid and complete."""

    def test_check_json_parses(self):
        data = _cli_json("check", "--command", "git status")
        assert data["simulation_mode"] is True
        assert data["authorization_granted"] is False

    def test_check_json_has_all_invariants(self):
        invariant_falses = [
            "authorization_granted", "execution_authorized", "command_executed",
            "enforcement_applied", "shell_intercepted", "wrapper_installed",
            "backend_invoked", "prompt_sent", "output_captured",
            "intake_performed", "adoption_performed",
        ]
        data = _cli_json("check", "--command", "git push --force")
        for field in invariant_falses:
            assert data[field] is False, f"CLI JSON: {field} must be False"

    def test_explain_json_parses(self):
        data = _cli_json("explain", "--decision", "would_block_by_raw_git_push")
        assert data["valid_decision"] is True

    def test_explain_json_has_severity(self):
        data = _cli_json("explain", "--decision", "would_block_by_force_push")
        assert "severity" in data

    def test_status_json_parses(self):
        data = _cli_json("status")
        assert data["simulation_mode_available"] is True
        assert data["phase"] == "89C"

    @pytest.mark.parametrize("cmd", [
        "git status", "git push", "bash", "env|grep TOKEN",
        "sh -c 'git push'",
    ])
    def test_various_commands_json_valid(self, cmd):
        data = _cli_json("check", "--command", cmd)
        assert "simulation_decision" in data
        assert data["command_executed"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Human-Readable Output Review
# ═══════════════════════════════════════════════════════════════════════════════

class TestCliHumanReadable:
    """Human-readable output contains required sections."""

    def test_output_has_simulation_header(self):
        r = _cli("check", "--command", "git status")
        assert "Dry-Run Simulation" in r.stdout

    def test_output_has_non_authorizing_footer(self):
        r = _cli("check", "--command", "git status")
        assert "simulation complete" in r.stdout.lower()
        assert "no enforcement" in r.stdout.lower()

    def test_blocked_output_has_simulated_block(self):
        r = _cli("check", "--command", "git push")
        assert "SIMULATED BLOCK" in r.stdout

    def test_output_does_not_contain_raw_secret(self):
        r = _cli("check", "--command", "OPENAI_API_KEY=abc123 python script.py")
        assert "abc123" not in r.stdout

    def test_explain_output_has_decision_info(self):
        r = _cli("explain", "--decision", "would_block_by_raw_git_push")
        assert "would_block_by_raw_git_push" in r.stdout
        assert "block" in r.stdout.lower()

    def test_status_output_has_invariants(self):
        r = _cli("status")
        assert "no_command_execution" in r.stdout
        assert "no_enforcement" in r.stdout
