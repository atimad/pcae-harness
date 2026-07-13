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


def _seed_report(directory: str, *, phase_id: str, phase_name: str, summary: str, files_changed: int = 0, tests_run: int = 0) -> None:
    from pcae.core.phase_reports import make_phase_report, write_phase_report
    report = make_phase_report(
        phase_id=phase_id, phase_name=phase_name, status="completed",
        summary=summary, files_changed=files_changed, tests_run=tests_run,
    )
    write_phase_report(report, Path(directory))


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
        assert result.returncode == 1
        assert "90A-test" in result.stdout
        assert not Path(td, "latest.md").exists()
        assert list(Path(td, "quarantine").glob("*.blocked.json"))


def test_create_json():
    with tempfile.TemporaryDirectory() as td:
        result = _run([
            "create",
            "--phase-id", "90A-test",
            "--phase-name", "Test Phase",
            "--status", "completed",
            "--summary", "All done.",
            "--reports-dir", td, "--json",
        ])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["status"] == "rejected"
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
        assert result.returncode == 1
        assert list(Path(td, "quarantine").glob("*.blocked.json"))


def test_create_missing_required():
    result = _run(["create"])
    assert result.returncode != 0


# ── show ─────────────────────────────────────────────────────────────────────


def test_show_text():
    with tempfile.TemporaryDirectory() as td:
        _seed_report(td, phase_id="90A-test", phase_name="Show Test", summary="Show me.")
        result = _run(["show", "--reports-dir", td])
        assert result.returncode == 0
        assert "Show Test" in result.stdout


def test_show_json():
    with tempfile.TemporaryDirectory() as td:
        _seed_report(td, phase_id="90A-test", phase_name="JSON Test", summary="JSON output.")
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
        _seed_report(
            td, phase_id="91A", phase_name="Round Trip", summary="Full circle.",
            files_changed=3, tests_run=55,
        )
        data = _json(["show", "--reports-dir", td])
        assert data["phase_id"] == "91A"
        assert data["files_changed"] == 3
        assert data["tests_run"] == 55
