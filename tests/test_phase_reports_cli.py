"""CLI tests for Phase 92A phase report commands."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(args: list[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "pcae", "phase-report"] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)


def _json(args: list[str]) -> dict:
    result = _run(args + ["--json"])
    assert result.returncode == 0, f"Failed: {result.stderr}"
    return json.loads(result.stdout)


# ── create ───────────────────────────────────────────────────────────────────


def test_create_text():
    with tempfile.TemporaryDirectory() as td:
        result = _run([
            "create",
            "--phase-id", "90A-test",
            "--phase-name", "Test Phase",
            "--status", "completed",
            "--summary", "All done.",
            "--reports-dir", td,
        ])
        assert result.returncode == 0
        assert "90A-test" in result.stdout
        assert Path(td, "latest.md").exists()
        assert Path(td, "latest.json").exists()


def test_create_json():
    with tempfile.TemporaryDirectory() as td:
        data = _json([
            "create",
            "--phase-id", "90A-test",
            "--phase-name", "Test Phase",
            "--status", "completed",
            "--summary", "All done.",
            "--reports-dir", td,
        ])
        assert data["status"] == "created"
        assert data["phase_id"] == "90A-test"


def test_create_rejects_invalid_status():
    result = _run([
        "create",
        "--phase-id", "X",
        "--phase-name", "X",
        "--status", "bogus",
        "--summary", "Y",
    ])
    assert result.returncode != 0


def test_create_with_all_fields():
    with tempfile.TemporaryDirectory() as td:
        result = _run([
            "create",
            "--phase-id", "90A",
            "--phase-name", "Full Test",
            "--status", "completed",
            "--summary", "Everything passed.",
            "--files-changed", "5",
            "--tests-run", "3221",
            "--pushed-status", "pushed",
            "--origin-main-head-count", "0",
            "--recommended-next-phase", "91A",
            "--reports-dir", td,
        ])
        assert result.returncode == 0


def test_create_missing_required():
    result = _run(["create"])
    assert result.returncode != 0


# ── show ─────────────────────────────────────────────────────────────────────


def test_show_text():
    with tempfile.TemporaryDirectory() as td:
        _run([
            "create",
            "--phase-id", "90A-test",
            "--phase-name", "Show Test",
            "--status", "completed",
            "--summary", "Show me.",
            "--reports-dir", td,
        ])
        result = _run(["show", "--reports-dir", td])
        assert result.returncode == 0
        assert "Show Test" in result.stdout


def test_show_json():
    with tempfile.TemporaryDirectory() as td:
        _run([
            "create",
            "--phase-id", "90A-test",
            "--phase-name", "JSON Test",
            "--status", "completed",
            "--summary", "JSON output.",
            "--reports-dir", td,
        ])
        data = _json(["show", "--reports-dir", td])
        assert data["phase_name"] == "JSON Test"
        assert data["schema_version"] == "1.0"


def test_show_no_report():
    with tempfile.TemporaryDirectory() as td:
        result = _run(["show", "--reports-dir", td])
        assert result.returncode != 0


# ── create then show round-trip ─────────────────────────────────────────────


def test_round_trip_json():
    with tempfile.TemporaryDirectory() as td:
        _run([
            "create",
            "--phase-id", "91A",
            "--phase-name", "Round Trip",
            "--status", "completed",
            "--summary", "Full circle.",
            "--files-changed", "3",
            "--tests-run", "55",
            "--reports-dir", td,
        ])
        data = _json(["show", "--reports-dir", td])
        assert data["phase_id"] == "91A"
        assert data["files_changed"] == 3
        assert data["tests_run"] == 55
