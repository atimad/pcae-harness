"""Tests for enforcement readiness CLI (89N, simulation-only)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_status(args: list[str] | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "pcae", "enforcement-readiness", "status"]
    if args:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        capture_output=True, text=True, cwd=REPO_ROOT,
    )


def _run_status_json() -> tuple[subprocess.CompletedProcess, dict]:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "enforcement-readiness", "status", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    data = json.loads(result.stdout)
    return result, data


# ---------------------------------------------------------------------------
# CLI registration
# ---------------------------------------------------------------------------

class TestCLIRegistration:
    """Tests that the CLI command is properly registered."""

    def test_enforcement_readiness_help_shows_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "enforcement-readiness", "--help"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "status" in result.stdout

    def test_status_help_shows_json_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "pcae", "enforcement-readiness", "status", "--help"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "--json" in result.stdout


# ---------------------------------------------------------------------------
# Human-readable output
# ---------------------------------------------------------------------------

class TestHumanReadableCLI:
    """Tests for human-readable CLI output."""

    def test_status_exits_successfully(self):
        result = _run_status()
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_status_output_is_not_empty(self):
        result = _run_status()
        assert len(result.stdout) > 0

    def test_status_includes_gate_summary(self):
        result = _run_status()
        assert "Gate Summary" in result.stdout

    def test_status_includes_enforcement_not_authorized(self):
        result = _run_status()
        assert "NOT authorized" in result.stdout

    def test_status_includes_gates_by_dimension(self):
        result = _run_status()
        assert "Gates by Dimension" in result.stdout
        for dim in ("design", "implementation", "test"):
            assert dim in result.stdout

    def test_status_includes_evidence_references(self):
        result = _run_status()
        assert "Evidence" in result.stdout

    def test_status_includes_recommended_next_phase(self):
        result = _run_status()
        assert "90A" in result.stdout

    def test_status_includes_safety_footer(self):
        result = _run_status()
        assert "Readiness report only" in result.stdout


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

class TestJsonCLI:
    """Tests for JSON CLI output."""

    def test_json_exits_successfully(self):
        result, data = _run_status_json()
        assert result.returncode == 0

    def test_json_is_dict(self):
        result, data = _run_status_json()
        assert isinstance(data, dict)

    def test_json_total_gates_is_69(self):
        result, data = _run_status_json()
        assert data["total_gates"] == 69

    def test_json_enforcement_authorized_false(self):
        result, data = _run_status_json()
        assert data["enforcement_authorized"] is False

    def test_json_enforcement_ready_false(self):
        result, data = _run_status_json()
        assert data["enforcement_ready"] is False

    def test_json_gates_list_length(self):
        result, data = _run_status_json()
        assert len(data["gates"]) == 69

    def test_json_has_evidence_references(self):
        result, data = _run_status_json()
        assert len(data["evidence_references"]) > 0

    def test_json_has_missing_evidence(self):
        result, data = _run_status_json()
        assert len(data["missing_evidence"]) > 0

    def test_json_safety_footer_present(self):
        result, data = _run_status_json()
        assert "no enforcement" in data["safety_footer"].lower()


# ---------------------------------------------------------------------------
# Counts
# ---------------------------------------------------------------------------

class TestCLICounts:
    """Tests for gate counts in CLI output."""

    def test_counts_sum_to_total(self):
        result, data = _run_status_json()
        total = (data["satisfied"] + data["unsatisfied"] +
                  data["conditional"] + data["deferred"])
        assert total == data["total_gates"]

    def test_human_output_shows_correct_counts(self):
        result = _run_status()
        assert "Total gates" in result.stdout


# ---------------------------------------------------------------------------
# No execution / read-only
# ---------------------------------------------------------------------------

class TestCLINoExecution:
    """Tests that the CLI doesn't execute, enforce, or authorize."""

    def test_json_is_read_only(self):
        result, data = _run_status_json()
        assert data["enforcement_authorized"] is False
        assert data["enforcement_ready"] is False

    def test_human_output_clearly_states_not_authorized(self):
        result = _run_status()
        # Collapse any run of spaces for more robust matching
        normalized = re.sub(r" +", " ", result.stdout)
        assert "Enforcement authorized: NO" in normalized
        assert "Enforcement ready: NO" in normalized
