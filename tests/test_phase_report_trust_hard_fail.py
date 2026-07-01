"""Tests for Phase 105D — Phase Report Trust Gate Hard-Fail / Push-Check
Integration. Non-executing, non-authorizing. No real network calls.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.commands.push import assess_push_readiness
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


def _complete_metadata(**overrides) -> dict:
    meta = {
        "phase_id": "205D",
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
        "recommended_next_phase": "205E — Next Phase",
        "phase_commits": [{"hash": "abc1234500000000"}],
        "commit_attribution": "phase_owned",
    }
    meta.update(overrides)
    return meta


def _write_metadata(tmp_path: Path, **overrides) -> dict:
    meta = _complete_metadata(**overrides)
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))
    return meta


class _FakeTelegramSink:
    should_succeed = True

    def __init__(self, *args, **kwargs):
        pass

    def send(self, event) -> NotificationResult:
        return NotificationResult(
            sink_name="telegram", success=self.should_succeed,
            message="mock send" if self.should_succeed else "mock failure",
            event_id=event.event_id, attempted_at="2026-01-01T00:00:00+00:00",
            error=None if self.should_succeed else "mock_error",
        )


# ── Group A: Phase complete hard-fail ───────────────────────────────────────


class TestPhaseCompleteHardFail:
    def test_complete_report_passes(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Trust gate (105D): complete" in output

    def test_missing_files_changed_fails(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "Phase completion refused" in output

    def test_missing_pcae_push_check_fails(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        gov = [g for g in _complete_metadata()["governance_results"] if g["name"] != "pcae_push_check"]
        _write_metadata(tmp_path, governance_results=gov)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "governance_results.pcae_push_check" in output

    def test_missing_report_notification_tests_fails(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        vr = [v for v in _complete_metadata()["validation_results"] if v["name"] != "report_notification_tests"]
        _write_metadata(tmp_path, validation_results=vr)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        assert exit_code == 1

    def test_pending_fast_green_fails(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        vr = list(_complete_metadata()["validation_results"])
        vr[2] = {"name": "fast_green", "result": "pending", "status": ""}
        _write_metadata(tmp_path, validation_results=vr)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "fast_green" in output

    def test_not_pushed_fails_final_completion(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=[
                             {"name": "pcae_health", "status": "healthy"},
                             {"name": "pcae_check", "status": "passed"},
                             {"name": "pcae_doctor_task_memory", "status": "clean"},
                             {"name": "pcae_push_check", "status": "pending final commit"},
                             {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
                         ])
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "pushed_status" in output

    def test_origin_main_head_nonzero_fails(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, origin_main_head_count=3)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        assert exit_code == 1

    def test_failure_prevents_telegram_dispatch(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert "Notification dispatch: skipped" in output
        assert not (tmp_path / ".pcae" / "notifications").exists()

    def test_failure_reports_missing_and_placeholder_fields(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        vr = list(_complete_metadata()["validation_results"])
        vr[2] = {"name": "fast_green", "result": "TBD", "status": ""}
        _write_metadata(tmp_path, validation_results=vr)
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert "Missing fields:" in output or "Placeholder fields:" in output
        assert "Repair required: yes" in output

    def test_allow_partial_report_bypasses_hard_fail(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)

        exit_code = main([
            "phase", "complete", "--summary", "Phase 205D: done.", "--allow-partial-report",
        ])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "--allow-partial-report" in output

    def test_allow_partial_report_still_suppresses_telegram(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = main([
            "phase", "complete", "--summary", "Phase 205D: done.", "--allow-partial-report",
        ])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification dispatch: skipped" in output
        assert not (tmp_path / ".pcae" / "notifications").exists()


# ── Group B: Push-check integration ─────────────────────────────────────────


class TestPushCheckIntegration:
    def test_complete_trusted_report_passes_gate(self, tmp_path, monkeypatch):
        root = _init_repo(tmp_path)
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "205D-P", "status": "completed", "files_changed": 1, "tests_run": 1,
            "commits": ["abc1234"], "pushed": "pushed", "summary": "s",
            "recommended_next_phase": "205D-N",
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
        readiness = assess_push_readiness(root)
        assert readiness.phase_report_trust_status == "passed"

    def test_partial_report_fails_push_check(self, tmp_path, monkeypatch):
        root = _init_repo(tmp_path)
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "205D-Q", "status": "completed", "summary": "s",
        }))
        readiness = assess_push_readiness(root)
        assert readiness.phase_report_trust_status == "failed"
        assert readiness.ready is False

    def test_pending_push_check_field_does_not_fail_gate(self, tmp_path):
        # Deliberate design: push-state fields (pushed_status/origin_main_head/
        # pcae_push_check) are NOT required to already say "pushed" here —
        # otherwise push-check could never pass for a normal pre-push
        # task-finish report. See _assess_phase_report_trust docstring.
        root = _init_repo(tmp_path)
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "205D-R", "status": "completed", "files_changed": 1, "tests_run": 1,
            "commits": ["abc1234"], "pushed": "not_pushed", "summary": "s",
            "recommended_next_phase": "205D-N",
            "governance_results": {
                "pcae_health": "healthy", "pcae_check": "passed",
                "pcae_doctor_task_memory": "clean", "pcae_push_check": "pending final commit",
                "telegram_runtime": "loaded, configured, enabled",
            },
            "test_results": {
                "report_notification_tests": "1/1", "bootstrap_session_reporting_tests": "present",
                "fast_green": "1/1",
            },
        }))
        readiness = assess_push_readiness(root)
        assert readiness.phase_report_trust_status == "passed"

    def test_missing_report_preserves_existing_behavior(self, tmp_path):
        root = _init_repo(tmp_path)
        readiness = assess_push_readiness(root)
        assert readiness.phase_report_trust_status == "skipped"

    def test_json_output_includes_phase_report_trust(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "205D-S", "status": "completed", "summary": "s",
        }))
        monkeypatch.chdir(tmp_path)

        main(["push", "check", "--json"])
        data = json.loads(capsys.readouterr().out)

        assert data["phase_report_trust"] == "failed"
        assert "phase_report_trust_missing_fields" in data
        assert "phase_report_trust_repair_required" in data


# ── Group C: Task finish compatibility ──────────────────────────────────────


class TestTaskFinishCompatibility:
    def test_task_finish_still_warning_only_prepush(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=[
                             {"name": "pcae_health", "status": "healthy"},
                             {"name": "pcae_check", "status": "passed"},
                             {"name": "pcae_doctor_task_memory", "status": "clean"},
                             {"name": "pcae_push_check", "status": "pending final commit"},
                             {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
                         ])
        monkeypatch.chdir(tmp_path)

        exit_code = main(["task", "finish", "--staged-file-aware", "--commit", "test commit"])
        assert exit_code == 0

    def test_task_finish_still_suppresses_telegram_for_prepush(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8,
                         governance_results=[
                             {"name": "pcae_health", "status": "healthy"},
                             {"name": "pcae_check", "status": "passed"},
                             {"name": "pcae_doctor_task_memory", "status": "clean"},
                             {"name": "pcae_push_check", "status": "pending final commit"},
                             {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
                         ])
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        main(["task", "finish", "--staged-file-aware", "--commit", "test commit"])
        output = capsys.readouterr().out

        assert "Report notification: skipped_incomplete" in output
        assert not (tmp_path / ".pcae" / "notifications").exists()

    def test_task_finish_completes_governed_commit_flow(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _new_task(root)
        _write_metadata(tmp_path, pushed_status="not_pushed", origin_main_head_count=8)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["task", "finish", "--staged-file-aware", "--commit", "test commit"])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Committed:" in output

    def test_no_duplicate_sends_after_hard_fail_changes(self, tmp_path, monkeypatch):
        from pcae.commands.task import _finalize_task_report_and_notify

        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D-DUP")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        first = _finalize_task_report_and_notify("abc1234")
        assert first["notification_status"] == "sent"
        second = _finalize_task_report_and_notify("abc1234")
        assert second["status"] == "skipped_duplicate"


# ── Group D: Telegram dispatch ──────────────────────────────────────────────


class TestTelegramDispatchGating:
    def test_phase_complete_hard_fail_suppresses_dispatch(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")
        fake = _FakeTelegramSink
        fake.should_succeed = True
        monkeypatch.setattr(notifications_module, "TelegramSink", fake)

        main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert "Notification dispatch: skipped" in output

    def test_complete_trusted_state_can_dispatch(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")
        fake = _FakeTelegramSink
        fake.should_succeed = True
        monkeypatch.setattr(notifications_module, "TelegramSink", fake)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification dispatch: sent" in output

    def test_partial_report_never_updates_last_notified_marker(self, tmp_path, monkeypatch):
        from pcae.commands.task import _finalize_task_report_and_notify

        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D-M", pushed_status="not_pushed",
                         origin_main_head_count=8,
                         governance_results=[
                             {"name": "pcae_health", "status": "healthy"},
                             {"name": "pcae_check", "status": "passed"},
                             {"name": "pcae_doctor_task_memory", "status": "clean"},
                             {"name": "pcae_push_check", "status": "pending final commit"},
                             {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
                         ])
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        _finalize_task_report_and_notify("abc1234")
        assert not (tmp_path / ".pcae" / "phase-reports" / ".last-notified.json").exists()


# ── Group E: No-execution guards ────────────────────────────────────────────


class TestNoExecGuards:
    def test_phase_complete_hard_fail_no_subprocess(self):
        import inspect
        from pcae.commands.phase import _finalize_report_and_notify

        src = inspect.getsource(_finalize_report_and_notify)
        assert "subprocess" not in src
        assert "os.system" not in src

    def test_push_check_trust_no_subprocess(self):
        import inspect
        from pcae.commands.push import _assess_phase_report_trust

        src = inspect.getsource(_assess_phase_report_trust)
        assert "subprocess" not in src
        assert "os.system" not in src

    def test_no_telegram_inbound_or_polling(self):
        import inspect
        from pcae.commands.phase import _finalize_report_and_notify

        src = inspect.getsource(_finalize_report_and_notify)
        assert "getUpdates" not in src
        assert "poll" not in src.lower()

    def test_no_backend_or_adapter_invocation(self):
        import inspect
        from pcae.commands.phase import _finalize_report_and_notify
        from pcae.commands.push import _assess_phase_report_trust

        for fn in (_finalize_report_and_notify, _assess_phase_report_trust):
            src = inspect.getsource(fn)
            assert "backend" not in src.lower()
            assert "adapter" not in src.lower()


# ── Group F: Backward compatibility ─────────────────────────────────────────


class TestBackwardCompatibility:
    def test_phase_report_trust_cli_still_works(self, tmp_path, monkeypatch):
        root = _init_repo(tmp_path)
        reports_dir = tmp_path / "phase-reports"
        reports_dir.mkdir()
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "205D-BC1", "status": "completed", "files_changed": 1, "tests_run": 1,
            "commits": ["abc1234"], "pushed": "pushed", "summary": "s",
            "recommended_next_phase": "205D-N",
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

    def test_phase_report_show_trust_still_works(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        reports_dir = tmp_path / "phase-reports"
        main(["phase-report", "create", "--phase-id", "205D-BC2", "--phase-name", "X",
              "--status", "completed", "--summary", "s", "--reports-dir", str(reports_dir)])
        capsys.readouterr()
        exit_code = main(["phase-report", "show", "--reports-dir", str(reports_dir), "--trust"])
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "Trust Gate (Phase 105B)" in output
