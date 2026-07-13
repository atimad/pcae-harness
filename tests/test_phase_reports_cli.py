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


# ── Phase 135H.2.1 — resumed_completed must not crash the CLI ──────────────
#
# Independently reproduced during the Phase 135H.2.1 governed terminal
# reporting recovery: an unchanged retry of `pcae phase-report create` for a
# report whose finalization transaction had already reached a completed
# checkpoint (same report digest + finalization snapshot) crashed with
# `KeyError: 'paths'`. `run_finalization_transaction()` correctly refuses to
# re-invoke the promotion/dispatch callback (it returns `status="resumed_
# completed"` with `promotion_and_dispatch=None`), but `run_phase_report_
# create()`'s status switch had no branch for that value, so it fell through
# to `outcome = txn_result.promotion_and_dispatch or {}` and then crashed on
# the unconditional `outcome["paths"]`. `pcae phase complete` and `pcae task
# finish` do not share this bug: both read `outcome`/`fin` with `.get()`
# throughout instead of `[...]`.


def _complete_create_args(phase_id: str, reports_dir: str) -> list[str]:
    return [
        "create",
        "--phase-id", phase_id,
        "--phase-name", "Resumed Completed Regression",
        "--status", "completed",
        "--summary", "Regression coverage for the resumed_completed CLI crash.",
        "--files-changed", "1",
        "--tests-run", "0",
        "--pushed-status", "pushed",
        "--origin-main-head-count", "0",
        "--recommended-next-phase", "999Z — Next Phase",
        "--commit", "abc1234500000000",
        "--governance-result", "pcae_health=healthy",
        "--governance-result", "pcae_check=clean",
        "--governance-result", "pcae_doctor_task_memory=clean",
        "--governance-result", "pcae_push_check=clean",
        "--governance-result", "telegram_runtime=configured, enabled, ready",
        "--test-result", "fast_green=1 passed (0 failed)",
        "--test-result", "report_notification_tests=1 passed (0 failed)",
        "--test-result", "bootstrap_session_reporting_tests=1 passed (0 failed)",
    ] + [
        item
        for text in [
            "No engineering work was rerun.",
            "No second logical engineering completion was created.",
            "No completion metadata was overwritten in place.",
            "No production lifecycle source changed.",
            "No CLTR-001 amendment occurred.",
            "No PFN-001 change occurred.",
            "No PFR-001 change occurred.",
            "No runtime capability change occurred.",
            "No duplicate canonical completion was permitted.",
            "No existing marker, checkpoint, or receipt was modified.",
            "No resend of a prior notification occurred.",
            "No next-phase work began.",
            "No raw git commit or push was used.",
            "No force push was used.",
            "No execution capability was introduced.",
        ]
        for item in ("--no-go-confirmation", text)
    ] + ["--reports-dir", reports_dir, "--json"]


def test_create_resumed_completed_does_not_crash(tmp_path, monkeypatch):
    from pcae.cli import main
    from pcae.commands.init import init_harness
    from pcae.core.paths import HarnessPath

    init_harness(HarnessPath(tmp_path))
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")
    monkeypatch.setenv("PCAE_NOTIFY_OUTPUT_DIR", str(tmp_path / "notifications"))

    reports_dir = str(tmp_path / "reports")
    args = _complete_create_args("999Z.1-resume-cli-test", reports_dir)

    first_argv = ["phase-report"] + args
    exit_code_first = main(first_argv)
    assert exit_code_first == 0

    exit_code_second = main(first_argv)
    assert exit_code_second == 0  # must not raise KeyError('paths')
