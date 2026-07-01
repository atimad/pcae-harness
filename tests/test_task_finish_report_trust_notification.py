"""Tests for Phase 105C — Task Finish Report Trust / Telegram Notification
Integration. Non-executing, non-authorizing. No real network calls —
Telegram sends are mocked; "sent" dispatch tests use the filesystem sink.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract
import pcae.core.notifications as notifications_module
from pcae.core.notifications import NotificationResult


def _init_repo(tmp_path: Path) -> HarnessPath:
    root = HarnessPath(tmp_path)
    init_harness(root)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
    return root


def _new_task(root: HarnessPath, **overrides) -> None:
    kwargs: dict[str, Any] = {
        "title": "Smoke task",
        "goal": "smoke",
        "mode": "implementation",
        "allowed_files": [".pcae/**", "tasks/active/**", "tasks/done/**"],
        "allowed_zones": ["config", "tasks"],
    }
    kwargs.update(overrides)
    create_task_contract(root, **kwargs)


def _write_metadata(tmp_path: Path, **overrides) -> dict:
    meta = {
        "phase_id": "205C-T",
        "phase_name": "Task Finish Integration Test",
        "status": "completed",
        "summary": "Test phase for task-finish integration.",
        "files_changed_count": 2,
        "tests_added_or_updated": "5 tests added",
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "clean"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
        ],
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": ""},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "no_go_confirmation": (
            "No runtime enforcement. No execution. No subprocess. No shell. "
            "No network. No Telegram inbound. No apply. No commit authorization. "
            "No push authorization. No rollback. No adapter execution."
        ),
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": "205D — Next Phase",
    }
    meta.update(overrides)
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))
    return meta


def _finish(monkeypatch, tmp_path: Path, *, json_output: bool = False) -> tuple[int, str]:
    args = ["task", "finish", "--staged-file-aware", "--commit", "Smoke finish commit"]
    if json_output:
        args.append("--json")
    exit_code = main(args)
    return exit_code


class _FakeTelegramSink:
    """Stand-in for TelegramSink that never touches the network."""

    should_succeed = True

    def __init__(self, *args, **kwargs):
        pass

    def send(self, event) -> NotificationResult:
        return NotificationResult(
            sink_name="telegram",
            success=self.should_succeed,
            message="mock send" if self.should_succeed else "mock failure",
            event_id=event.event_id,
            attempted_at="2026-01-01T00:00:00+00:00",
            error=None if self.should_succeed else "mock_error",
        )


# ── Group A: Task finish trust validation ───────────────────────────────────


class TestTaskFinishTrustValidation:
    def test_complete_metadata_reports_trust_complete(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        exit_code = _finish(monkeypatch, tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report trust: complete" in output
        assert "Repair required: no" in output

    def test_partial_metadata_reports_repair_required(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        meta = _write_metadata(tmp_path)
        meta["validation_results"] = [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": ""},
            {"name": "fast_green", "result": "TBD", "status": ""},
        ]
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        exit_code = _finish(monkeypatch, tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0  # task finish itself is not blocked (warning-only)
        assert "Report trust: partial" in output
        assert "Repair required: yes" in output

    def test_missing_metadata_produces_warning_not_crash(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        # No metadata file written.
        monkeypatch.chdir(tmp_path)

        exit_code = _finish(monkeypatch, tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report finalization: skipped" in output
        assert "no .pcae/phase-completion-metadata.json" in output


# ── Group B: Task finish notification dispatch ──────────────────────────────


class TestTaskFinishNotificationDispatch:
    def test_complete_report_dispatches_via_filesystem_sink_when_enabled(
        self, tmp_path, monkeypatch, capsys,
    ):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = _finish(monkeypatch, tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report notification: sent" in output
        assert (tmp_path / ".pcae" / "notifications").exists()

    def test_notification_disabled_skips_safely(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        exit_code = _finish(monkeypatch, tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report notification: skipped" in output
        assert "PCAE_NOTIFY_ENABLED" in output

    def test_telegram_dispatch_is_mocked_no_network(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")

        fake = _FakeTelegramSink
        fake.should_succeed = True
        monkeypatch.setattr(notifications_module, "TelegramSink", fake)

        exit_code = _finish(monkeypatch, tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report notification: sent" in output

    def test_dispatch_failure_reported_without_corrupting_completion(
        self, tmp_path, monkeypatch, capsys,
    ):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")

        fake = _FakeTelegramSink
        fake.should_succeed = False
        monkeypatch.setattr(notifications_module, "TelegramSink", fake)

        exit_code = _finish(monkeypatch, tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0  # completion is not corrupted by dispatch failure
        assert "Finished task:" in output
        assert "Report notification: failed" in output

    def test_json_output_includes_expected_fields(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = _finish(monkeypatch, tmp_path, json_output=True)
        data = json.loads(capsys.readouterr().out)

        assert exit_code == 0
        assert data["report_trust"]["complete"] is True
        assert data["repair_required"] is False
        assert data["notification_dispatch"]["status"] == "sent"
        assert data["telegram_runtime"] == "outbound-only"
        assert data["report_path"]
        assert data["metadata_path"] == ".pcae/phase-completion-metadata.json"


# ── Group C: Warning-only behavior ──────────────────────────────────────────


class TestWarningOnlyBehavior:
    def test_partial_report_does_not_hard_fail(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        meta = _write_metadata(tmp_path)
        meta["validation_results"][2] = {"name": "fast_green", "result": "pending", "status": ""}
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        exit_code = _finish(monkeypatch, tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Repair required: yes" in output

    def test_recommended_next_phase_preserved_in_report(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, recommended_next_phase="205D — Hard-Fail Integration")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        _finish(monkeypatch, tmp_path)
        capsys.readouterr()

        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["recommended_next_phase"] == "205D — Hard-Fail Integration"


# ── Group D: Idempotency / duplicate prevention ─────────────────────────────


class TestIdempotency:
    def test_no_duplicate_send_when_already_dispatched_for_same_commit(
        self, tmp_path, monkeypatch,
    ):
        from pcae.commands.task import _finalize_task_report_and_notify

        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205C-DUP")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        first = _finalize_task_report_and_notify("abc1234")
        assert first["status"] == "finalized"
        assert first["notification_status"] == "sent"

        second = _finalize_task_report_and_notify("abc1234")
        assert second["status"] == "skipped_duplicate"
        assert "already dispatched" in second["message"]

    def test_different_commit_is_not_treated_as_duplicate(self, tmp_path, monkeypatch):
        from pcae.commands.task import _finalize_task_report_and_notify

        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205C-DUP2")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        first = _finalize_task_report_and_notify("abc1234")
        assert first["status"] == "finalized"

        second = _finalize_task_report_and_notify("def5678")
        assert second["status"] == "finalized"  # different commit — no marker matched


# ── Group E: Existing phase complete preservation ───────────────────────────


class TestPhaseCompletePreservation:
    def test_phase_complete_still_works(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205C-PC: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Phase complete." in output

    def test_phase_complete_still_validates_trust(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(
            tmp_path,
            phase_id="205P",
            recommended_next_phase="205Q — Next Phase",
            phase_commits=[{"hash": "abc1234500000000"}],
            commit_attribution="phase_owned",
        )
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205P: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Phase report: BLOCKED" not in output
        assert "Trust gate (105B, advisory):" in output


# ── Group F: No-execution guards ─────────────────────────────────────────────


class TestNoExecGuards:
    def test_integration_module_only_uses_existing_subprocess_for_git(self):
        import inspect
        from pcae.commands.task import _finalize_task_report_and_notify

        src = inspect.getsource(_finalize_task_report_and_notify)
        assert "subprocess" not in src
        assert "os.system" not in src

    def test_integration_no_telegram_inbound_or_polling(self):
        import inspect
        from pcae.commands.task import _finalize_task_report_and_notify

        src = inspect.getsource(_finalize_task_report_and_notify)
        assert "getUpdates" not in src
        assert "poll" not in src.lower()

    def test_integration_no_direct_network_calls(self):
        import inspect
        from pcae.commands.task import _finalize_task_report_and_notify

        src = inspect.getsource(_finalize_task_report_and_notify)
        assert "requests." not in src
        assert "urllib" not in src
        assert "socket." not in src


# ── Group G: Report content ─────────────────────────────────────────────────


class TestReportContent:
    def test_report_notification_tests_present_in_written_report(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        _finish(monkeypatch, tmp_path)
        capsys.readouterr()

        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert "report_notification_tests" in latest["test_results"]
        assert "bootstrap_session_reporting_tests" in latest["test_results"]
        assert "fast_green" in latest["test_results"]

    def test_no_go_confirmations_preserved(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        _finish(monkeypatch, tmp_path)
        capsys.readouterr()

        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["explicit_no_go_confirmations"]
        assert "No runtime enforcement" in latest["explicit_no_go_confirmations"][0]
