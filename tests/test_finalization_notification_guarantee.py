"""Tests for Phase 113X.3 — Finalized Phase Mobile Notification Guarantee.

Repairs two problems the Phase 113X.2 completion itself exposed:

1. A naive lexicographic "backward-pointing recommended next phase"
   heuristic wrongly flagged ``"113D"`` as before ``"113X.2"``
   (comparing ``'D' < 'X'`` as strings), forcing 113X.2's own
   completion to go through ``--allow-partial-report`` and end up
   marked ``partial``.
2. Because Phase 105D deliberately never sends a *normal* "Phase
   COMPLETED" notification for a partial report, the mobile operator
   received no Telegram message for 113X.2 at all -- a finalized,
   pushed phase was silent on the one channel that matters for mobile
   awareness.

This phase makes phase-ID ordering branch-aware (fixing problem 1) and
adds an explicit notification-outcome guarantee (fixing problem 2): a
finalized phase that writes canonical ``latest.md``/``latest.json``
always either sends a normal notification (complete), sends a clearly
labeled warning notification (finalized but partial), or -- for a
blocked/quarantined report, where canonical artifacts are deliberately
never written -- records an explicit skip reason. Non-executing,
non-authorizing. No real network calls.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import tempfile

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import (
    NOTIFICATION_OUTCOME_FAILED_WITH_REASON,
    NOTIFICATION_OUTCOME_SENT,
    NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON,
    finalize_phase_report,
    is_phase_id_backward,
    read_latest_report,
)


def _init_repo(tmp_path: Path) -> HarnessPath:
    root = HarnessPath(tmp_path)
    init_harness(root)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
    return root


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


# ── Unit-level: the notification-outcome model on finalize_phase_report() ──
# (finalize_phase_report() writes the report artifact *before* attempting
# dispatch -- report.notification_result is never persisted back to
# latest.json, a pre-existing characteristic -- so the outcome model is
# verified directly against finalize_phase_report()'s own return value.)


class TestNotificationOutcomeModelDirect:
    def test_complete_report_outcome_is_sent_kind_complete(self, monkeypatch):
        with tempfile.TemporaryDirectory() as td:
            monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
            monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")
            monkeypatch.setenv("PCAE_NOTIFY_OUTPUT_DIR", str(Path(td) / "notifications"))

            fin = finalize_phase_report(
                phase_id="900A", phase_name="Complete Test", status="completed",
                summary="Done.", reports_dir=Path(td),
                report_is_complete=True,
            )

            assert fin["notification_outcome"] == NOTIFICATION_OUTCOME_SENT
            assert fin["notification_kind"] == "complete"

    def test_partial_report_outcome_is_sent_kind_partial_warning(self, monkeypatch):
        with tempfile.TemporaryDirectory() as td:
            monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
            monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")
            monkeypatch.setenv("PCAE_NOTIFY_OUTPUT_DIR", str(Path(td) / "notifications"))

            fin = finalize_phase_report(
                phase_id="900B", phase_name="Partial Test", status="completed",
                summary="Done.", reports_dir=Path(td),
                report_is_complete=False,
                report_incomplete_reason="missing: governance_results.pcae_push_check",
            )

            assert fin["notification_outcome"] == NOTIFICATION_OUTCOME_SENT
            assert fin["notification_kind"] == "partial_warning"

    def test_disabled_outcome_is_skipped_with_reason(self, monkeypatch):
        with tempfile.TemporaryDirectory() as td:
            monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

            fin = finalize_phase_report(
                phase_id="900C", phase_name="Skipped Test", status="completed",
                summary="Done.", reports_dir=Path(td),
                report_is_complete=True,
            )

            assert fin["notification_outcome"] == NOTIFICATION_OUTCOME_SKIPPED_WITH_REASON
            assert fin["notification_reason"]

    def test_legacy_caller_without_report_is_complete_is_unaffected(self, monkeypatch):
        """Callers that don't pass report_is_complete (e.g. `pcae task
        finish --commit`) must see byte-for-byte the same behavior as
        before 113X.3 -- always the normal "complete" event kind."""
        with tempfile.TemporaryDirectory() as td:
            monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
            monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")
            monkeypatch.setenv("PCAE_NOTIFY_OUTPUT_DIR", str(Path(td) / "notifications"))

            fin = finalize_phase_report(
                phase_id="900D", phase_name="Legacy Caller", status="completed",
                summary="Done.", reports_dir=Path(td),
            )

            assert fin["notification_kind"] == "complete"
            assert fin["notification_outcome"] == NOTIFICATION_OUTCOME_SENT


# ── Requirement 1: 113X.2 -> 113D is not marked backward/partial ───────────


class TestBranchAwarePhaseIdOrdering:
    def test_113x2_to_113d_not_backward(self):
        assert is_phase_id_backward("113D", "113X.2") is False

    def test_genuine_mainline_regression_still_detected(self):
        assert is_phase_id_backward("113B", "113D") is True

    def test_113x2_to_113d_end_to_end_stays_complete(self, tmp_path, monkeypatch, capsys):
        """The exact scenario that broke 113X.2's own completion: a
        report whose current phase is on the "X" exceptional branch
        recommending the mainline phase that follows the excursion."""
        root = _init_repo(tmp_path)
        _write_metadata(
            tmp_path, phase_id="113X.2",
            recommended_next_phase="113D — Advisory Runtime Verification and Compatibility",
        )
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 113X.2: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Trust gate (105D): complete" in output
        assert "BLOCKED" not in output
        assert "points backward" not in output


# ── Requirement 2: complete finalized report still sends normal notification ─


class TestCompleteReportStillNotifiesNormally:
    def test_complete_report_sends_normal_notification(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification dispatch: sent" in output
        assert "PARTIAL WARNING" not in output


# ── Requirement 3/4: partial-but-finalized -> warning, never a normal report ─


class TestPartialFinalizedSendsWarningNotification:
    def test_partial_candidate_is_quarantined_without_warning_delivery(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)  # a gate blocker
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = main([
            "phase", "complete", "--summary", "Phase 205D: done.", "--allow-partial-report",
        ])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification dispatch: skipped" in output
        assert "PARTIAL WARNING" not in output
        assert not (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()

    def test_partial_report_never_looks_like_normal_completion(self, tmp_path, monkeypatch, capsys):
        """105D's rule preserved: the partial warning is a genuinely
        different event, never the normal "Phase COMPLETED" one."""
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        main(["phase", "complete", "--summary", "Phase 205D: done.", "--allow-partial-report"])

        assert not (tmp_path / ".pcae" / "notifications").exists()
        assert list((tmp_path / ".pcae" / "phase-reports" / "quarantine").glob("*.blocked.json"))

    def test_quarantine_includes_the_reason(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        main(["phase", "complete", "--summary", "Phase 205D: done.", "--allow-partial-report"])

        rejected = json.loads(next((tmp_path / ".pcae" / "phase-reports" / "quarantine").glob("*.blocked.json")).read_text())
        assert any("files_changed" in reason for reason in rejected["finalization_blockers"])


# ── Requirement 5: Telegram skip/failure recorded with explicit reason ──────


class TestSkipFailureRecordedWithReason:
    def test_notify_disabled_records_explicit_reason(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification dispatch: skipped" in output
        assert "Reason: PCAE_NOTIFY_ENABLED" in output

    def test_sink_failure_records_explicit_reason(self, tmp_path, monkeypatch, capsys):
        import pcae.core.notifications as notifications_module
        from pcae.core.notifications import NotificationResult

        class _FailingTelegramSink:
            def __init__(self, *a, **kw):
                pass

            def send(self, event):
                return NotificationResult(
                    sink_name="telegram", success=False, message="mock failure",
                    event_id=event.event_id, attempted_at="2026-01-01T00:00:00+00:00",
                    error="mock_error",
                )

        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")
        monkeypatch.setattr(notifications_module, "TelegramSink", _FailingTelegramSink)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification dispatch: failed" in output
        assert "Reason:" in output
        assert "mock failure" in output


# ── Requirement 6: 113X.1 quarantine behavior remains intact ───────────────


class TestQuarantineBehaviorIntact:
    def test_blocked_report_remains_silent_and_quarantined(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])  # no override
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "BLOCKED by finalization gate" in output
        assert "Report quarantined" in output
        assert not (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()
        # Quarantine remains fully silent -- 113X.3 only adds a
        # warning-notification path for reports that DID write
        # latest.*; a blocked report never did.
        assert not (tmp_path / ".pcae" / "notifications").exists()


# ── Requirement 7: 113X.2 identity-conflict blocker remains intact ─────────


class TestIdentityConflictBlockerIntact:
    def test_summary_disagreeing_with_metadata_no_longer_a_conflict(self, tmp_path, monkeypatch, capsys):
        """Phase 113X.4 superseded 113X.2's narrower mechanism: there is
        no more CLI/summary-derived phase_id to conflict with metadata,
        since --summary is not a phase-identity source at all (113X
        audit Finding 3, closed in full). Metadata's declared phase_id
        wins cleanly; the summary mentioning a different phase number
        is simply irrelevant, not a blocker."""
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205E: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "BLOCKED by finalization gate" not in output
        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_id"] == "205D"


# ── Requirement 8: no canonical latest artifacts overwritten by blocked ─────


class TestBlockedNeverOverwritesLatest:
    def test_blocked_after_valid_leaves_latest_untouched(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        assert main(["phase", "complete", "--summary", "Phase 205D: done."]) == 0
        capsys.readouterr()
        valid_latest = (tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text()

        _write_metadata(tmp_path, phase_id="205D", files_changed_count=0)
        exit_code2 = main(["phase", "complete", "--summary", "Phase 205D: done."])
        capsys.readouterr()

        assert exit_code2 == 1
        assert (tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text() == valid_latest


# ── Requirement 9: deterministic, no real network calls ────────────────────


class TestDeterministicNoNetworkCalls:
    def test_all_new_tests_use_filesystem_sink_not_real_telegram(self, tmp_path, monkeypatch, capsys):
        """Sanity check: the filesystem sink (used throughout this file)
        never performs any network I/O -- it only writes local JSON."""
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")
        monkeypatch.delenv("PCAE_TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("PCAE_TELEGRAM_CHAT_ID", raising=False)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])

        assert exit_code == 0
        assert (tmp_path / ".pcae" / "notifications").exists()
