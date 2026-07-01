"""Tests for Phase 105C.1 — Task Finish Report Notification Ordering /
Completeness Repair. Non-executing, non-authorizing. No real network calls.

Repairs 105C: automatic Telegram dispatch from `pcae task finish --commit`
must not send a report as a final trusted handoff while final push state
(pushed_status / origin_main_head / governance_results.pcae_push_check) is
still pending.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

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


def _new_task(root: HarnessPath) -> None:
    create_task_contract(
        root, title="Smoke task", goal="smoke", mode="implementation",
        allowed_files=[".pcae/**", "tasks/active/**", "tasks/done/**"],
        allowed_zones=["config", "tasks"],
    )


def _write_metadata(tmp_path: Path, **overrides) -> dict:
    meta = {
        "phase_id": "205C1-T",
        "phase_name": "Ordering Repair Test",
        "status": "completed",
        "summary": "Test phase for notification ordering repair.",
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
        "recommended_next_phase": "205C2 — Next Phase",
    }
    meta.update(overrides)
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))
    return meta


def _finish(tmp_path: Path, *, json_output: bool = False) -> int:
    args = ["task", "finish", "--staged-file-aware", "--commit", "Smoke finish commit"]
    if json_output:
        args.append("--json")
    return main(args)


def _pending_push_governance() -> list[dict]:
    return [
        {"name": "pcae_health", "status": "healthy"},
        {"name": "pcae_check", "status": "passed"},
        {"name": "pcae_doctor_task_memory", "status": "clean"},
        {"name": "pcae_push_check", "status": "pending final commit"},
        {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
    ]


class _FakeTelegramSink:
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


# ── Group A: Partial report dispatch suppression ────────────────────────────


class TestPartialDispatchSuppression:
    def test_missing_pushed_status_skips_final_send(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = _finish(tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report notification: skipped_incomplete" in output
        assert not (tmp_path / ".pcae" / "notifications").exists()
        assert not (tmp_path / ".pcae" / "phase-reports" / ".last-notified.json").exists()

    def test_missing_origin_main_head_skips_final_send(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, origin_main_head_count=3)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = _finish(tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report notification: skipped_incomplete" in output
        assert not (tmp_path / ".pcae" / "notifications").exists()

    def test_pending_push_check_skips_final_send(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = _finish(tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report notification: skipped_incomplete" in output
        assert not (tmp_path / ".pcae" / "notifications").exists()

    def test_output_lists_missing_fields_and_repair_required(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        _finish(tmp_path)
        output = capsys.readouterr().out

        assert "Report trust: partial" in output
        assert "Repair required: yes" in output
        assert "pushed_status" in output
        assert "origin_main_head" in output
        assert "governance_results.pcae_push_check" in output

    def test_no_notify_env_still_correctly_reports_partial(self, tmp_path, monkeypatch, capsys):
        # Even without notifications enabled, the push-state gate must
        # still surface "partial" (it must not silently look complete).
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        _finish(tmp_path)
        output = capsys.readouterr().out

        assert "Report trust: partial" in output
        assert "Repair required: yes" in output


# ── Group B: Complete report dispatch ────────────────────────────────────────


class TestCompleteDispatch:
    def test_complete_trusted_report_dispatches(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = _finish(tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report trust: complete" in output
        assert "Report notification: sent" in output
        assert (tmp_path / ".pcae" / "notifications").exists()

    def test_complete_dispatch_updates_marker(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        _finish(tmp_path)
        capsys.readouterr()

        marker = tmp_path / ".pcae" / "phase-reports" / ".last-notified.json"
        assert marker.exists()
        data = json.loads(marker.read_text())
        assert data["phase_id"] == "205C1-T"

    def test_telegram_dispatch_uses_existing_outbound_path_mocked(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")
        fake = _FakeTelegramSink
        fake.should_succeed = True
        monkeypatch.setattr(notifications_module, "TelegramSink", fake)

        exit_code = _finish(tmp_path)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Report notification: sent" in output


# ── Group C: Idempotency marker ─────────────────────────────────────────────


class TestIdempotencyMarker:
    def test_partial_report_does_not_write_marker(self, tmp_path, monkeypatch):
        from pcae.commands.task import _finalize_task_report_and_notify

        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205C1-IDEM1", pushed_status="not_pushed",
                         origin_main_head_count=8, governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        result = _finalize_task_report_and_notify("abc1234")
        assert result["notification_status"] == "skipped_incomplete"
        assert not (tmp_path / ".pcae" / "phase-reports" / ".last-notified.json").exists()

    def test_later_complete_report_can_still_send_after_partial(self, tmp_path, monkeypatch):
        from pcae.commands.task import _finalize_task_report_and_notify

        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205C1-IDEM2", pushed_status="not_pushed",
                         origin_main_head_count=8, governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        first = _finalize_task_report_and_notify("abc1234")
        assert first["notification_status"] == "skipped_incomplete"

        # Now push state resolves (e.g. after `pcae push`); metadata is
        # updated and a later finalization (same commit) must be able to
        # send, since the partial attempt never marked it as sent.
        _write_metadata(tmp_path, phase_id="205C1-IDEM2", pushed_status="pushed",
                         origin_main_head_count=0)
        second = _finalize_task_report_and_notify("abc1234")
        assert second["notification_status"] == "sent"
        assert (tmp_path / ".pcae" / "phase-reports" / ".last-notified.json").exists()

    def test_complete_already_notified_report_skips_duplicate(self, tmp_path, monkeypatch):
        from pcae.commands.task import _finalize_task_report_and_notify

        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205C1-IDEM3")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        first = _finalize_task_report_and_notify("def5678")
        assert first["notification_status"] == "sent"

        second = _finalize_task_report_and_notify("def5678")
        assert second["status"] == "skipped_duplicate"


# ── Group D: Report trust behavior ──────────────────────────────────────────


class TestReportTrustBehavior:
    def test_trust_result_controls_send_decision(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        _finish(tmp_path)
        output = capsys.readouterr().out
        assert "Report notification: skipped_incomplete" in output

    def test_partial_reports_remain_visible_as_partial_in_written_report(
        self, tmp_path, monkeypatch, capsys,
    ):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        _finish(tmp_path)
        capsys.readouterr()

        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["report_completeness"] == "partial"
        assert "pushed_status" in latest["missing_trust_fields"]

    def test_no_silent_auto_repair_of_missing_fields(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        _finish(tmp_path)
        capsys.readouterr()

        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["pushed_status"] == "not_pushed"
        assert latest["origin_main_head_count"] == 8


# ── Group E: CLI / UX ────────────────────────────────────────────────────────


class TestCliUx:
    def test_human_output_includes_required_lines(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        _finish(tmp_path)
        output = capsys.readouterr().out

        assert "Report trust:" in output
        assert "Repair required:" in output
        assert "Report notification:" in output
        assert "Telegram: outbound-only" in output

    def test_json_output_includes_required_fields(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=_pending_push_governance())
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        _finish(tmp_path, json_output=True)
        data = json.loads(capsys.readouterr().out)

        assert data["report_trust"]["complete"] is False
        assert data["repair_required"] is True
        assert data["notification_dispatch"]["status"] == "skipped_incomplete"
        assert data["telegram_runtime"] == "outbound-only"
        assert data["report_path"]
        assert data["metadata_path"] == ".pcae/phase-completion-metadata.json"


# ── Group F: Existing behavior preservation ─────────────────────────────────


class TestExistingBehaviorPreservation:
    def test_phase_complete_still_works(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205Q: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Phase complete." in output

    def test_phase_report_trust_cli_unchanged(self, tmp_path, monkeypatch):
        root = _init_repo(tmp_path)
        reports_dir = tmp_path / "phase-reports"
        reports_dir.mkdir()
        payload = _write_metadata(tmp_path)  # reuse shape, not written to reports_dir
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "205Q2", "status": "completed", "files_changed": 1, "tests_run": 1,
            "commits": ["abc1234"], "pushed": "pushed", "summary": "s",
            "recommended_next_phase": "205Q3",
            "governance_results": {
                "pcae_health": "healthy", "pcae_check": "passed",
                "pcae_doctor_task_memory": "clean", "pcae_push_check": "clean",
                "telegram_runtime": "loaded, configured, enabled",
            },
            "test_results": {
                "report_notification_tests": "1/1", "bootstrap_session_reporting_tests": "present",
                "fast_green": "1/1",
            },
        }))
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase-report", "trust", "--reports-dir", str(reports_dir), "--json"])
        assert exit_code == 0

    def test_phase_report_show_trust_unchanged(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        reports_dir = tmp_path / "phase-reports"
        exit_code = main([
            "phase-report", "create", "--phase-id", "205Q4", "--phase-name", "X",
            "--status", "completed", "--summary", "s", "--reports-dir", str(reports_dir),
        ])
        capsys.readouterr()
        exit_code = main(["phase-report", "show", "--reports-dir", str(reports_dir), "--trust"])
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "Trust Gate (Phase 105B)" in output


# ── Group G: No-execution guards ─────────────────────────────────────────────


class TestNoExecGuards:
    def test_push_state_gate_no_subprocess(self):
        import inspect
        from pcae.commands.task import _apply_push_state_gate, _finalize_task_report_and_notify

        for fn in (_apply_push_state_gate, _finalize_task_report_and_notify):
            src = inspect.getsource(fn)
            assert "subprocess" not in src
            assert "os.system" not in src

    def test_no_telegram_inbound_or_polling(self):
        import inspect
        from pcae.commands.task import _finalize_task_report_and_notify

        src = inspect.getsource(_finalize_task_report_and_notify)
        assert "getUpdates" not in src
        assert "poll" not in src.lower()

    def test_no_backend_or_adapter_invocation(self):
        import inspect
        from pcae.commands.task import _finalize_task_report_and_notify

        src = inspect.getsource(_finalize_task_report_and_notify)
        assert "backend" not in src.lower()
        assert "adapter" not in src.lower()
