"""Phase 114B: Notification Certification & Idempotency.

Covers the actual gap this phase closes: the Repository Transition
Validator's ``TransitionKind.NOTIFY`` / ``notification_eligible()`` (frozen
since 113T/113U) was never wired into the real dispatch call sites
(``pcae phase complete``, ``pcae task finish --commit``). Both callers
independently decided "was this already dispatched" from the Phase 113V.N
marker file alone. ``certify_notification_transition()``
(``pcae.core.notification_certification``) is now the single function both
consume; these tests exercise it directly (pure-function unit tests) and
through both lifecycle commands (CLI integration).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.notification_certification import (
    NotificationCertificationOutcome,
    certify_notification_transition,
)
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import make_phase_report, read_notification_dispatch_marker
from pcae.core.repository_transition_validator import TransitionKind, TransitionVerdict
from pcae.core.tasks import create_task_contract

# ═══════════════════════════════════════════════════════════════════════════
# Unit tests: certify_notification_transition() as a pure function
# ═══════════════════════════════════════════════════════════════════════════


def _trial_report(**overrides):
    kwargs = dict(
        phase_id="114B",
        phase_name="Notification Enforcement & Idempotency",
        status="completed",
        summary="Test phase for notification certification.",
        files_changed=2,
        tests_run=3,
        test_results={"focused": "3/3 (passed)"},
        commits=["abc12345"],
        pushed_status="pushed",
        origin_main_head_count=0,
        recommended_next_phase="114C — Push Authorization & Repository Trust Integration",
    )
    kwargs.update(overrides)
    report = make_phase_report(**kwargs)
    report.report_completeness = "complete"
    return report


def _certify(monkeypatch, marker_path, **overrides):
    origin_main_head_count = overrides.pop("origin_main_head_count", 0)
    kwargs = dict(
        phase_id="114B",
        requested_phase_id="114B",
        active_task_title=None,
        metadata={"execution_availability": "unavailable"},
        lifecycle_current_phase_line=None,
        trial_report=_trial_report(origin_main_head_count=origin_main_head_count),
        recommended_next_phase="114C — Push Authorization & Repository Trust Integration",
        origin_main_head_count=origin_main_head_count,
        commit_hash="abc12345",
        source_transition_kind=TransitionKind.COMPLETE_PHASE,
        marker_path=marker_path,
    )
    kwargs.update(overrides)
    return certify_notification_transition(**kwargs)


class TestCertifyNotificationTransitionEligible:
    def test_eligible_when_all_conditions_hold(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
        result = _certify(monkeypatch, tmp_path / ".last-notified.json")
        assert result.eligible is True
        assert result.outcome == NotificationCertificationOutcome.ELIGIBLE
        assert result.transition_verdict == TransitionVerdict.ACCEPT
        assert result.reasons == ()


class TestCertifyNotificationTransitionAlreadyDispatched:
    def test_already_dispatched_is_ineligible(self, tmp_path, monkeypatch):
        from pcae.core.phase_reports import write_notification_dispatch_marker

        marker_path = tmp_path / ".last-notified.json"
        write_notification_dispatch_marker("114B", "abc12345", marker_path=marker_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        result = _certify(monkeypatch, marker_path)
        assert result.eligible is False
        assert result.outcome == NotificationCertificationOutcome.ALREADY_DISPATCHED
        assert any("already dispatched" in r for r in result.reasons)

    def test_different_commit_same_phase_is_same_logical_completion(self, tmp_path, monkeypatch):
        """A bookkeeping/repair commit cannot create another ordinary completion."""
        from pcae.core.phase_reports import write_notification_dispatch_marker

        marker_path = tmp_path / ".last-notified.json"
        write_notification_dispatch_marker("114B", "abc12345", marker_path=marker_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        result = _certify(monkeypatch, marker_path, commit_hash="def09876")
        assert result.eligible is False
        assert result.outcome == NotificationCertificationOutcome.ALREADY_DISPATCHED


class TestCertifyNotificationTransitionDisabled:
    def test_notify_not_enabled_is_disabled(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        result = _certify(monkeypatch, tmp_path / ".last-notified.json")
        assert result.eligible is False
        assert result.outcome == NotificationCertificationOutcome.DISABLED


class TestCertifyNotificationTransitionTransportUnavailable:
    def test_no_sinks_configured_is_transport_unavailable(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "")

        result = _certify(monkeypatch, tmp_path / ".last-notified.json")
        assert result.eligible is False
        assert result.outcome == NotificationCertificationOutcome.TRANSPORT_UNAVAILABLE


class TestCertifyNotificationTransitionPushNotClean:
    def test_unpushed_commits_reject_notify_transition(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        result = _certify(monkeypatch, tmp_path / ".last-notified.json", origin_main_head_count=3)
        assert result.eligible is False
        assert result.outcome == NotificationCertificationOutcome.NOT_CERTIFIED
        assert any("push" in r for r in result.reasons)


class TestCertifyNotificationTransitionExecutionUnavailable:
    def test_execution_available_metadata_rejects(self, tmp_path, monkeypatch):
        """The `no_execution_availability_unless_contracted` invariant is not
        bypassed for NOTIFY transitions -- 114B does not grant execution
        capability any more than 113U/113Z/114A did."""
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        result = _certify(
            monkeypatch, tmp_path / ".last-notified.json",
            metadata={"execution_availability": "available"},
        )
        assert result.eligible is False
        assert result.transition_verdict == TransitionVerdict.REJECT
        assert any("execution_availability" in r for r in result.reasons)

    def test_execution_availability_constant_unchanged(self):
        from pcae.core.runtime_context import EXECUTION_AVAILABILITY

        assert EXECUTION_AVAILABILITY == "unavailable"


# ═══════════════════════════════════════════════════════════════════════════
# CLI integration: pcae phase complete
# ═══════════════════════════════════════════════════════════════════════════


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True)


def _write_phase_metadata(root: Path, phase_id: str, commit_hash: str, **overrides) -> None:
    meta = {
        "phase_id": phase_id,
        "phase_name": f"Test {phase_id}",
        "status": "completed",
        "phase_commits": [{"hash": commit_hash}],
        "recommended_next_phase": "114C — Next",
        "execution_availability": "unavailable",
    }
    meta.update(overrides)
    (root / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))


class TestPhaseCompleteNotificationCertification:
    def test_eligible_dispatch_is_certified_and_sent(self, tmp_path, monkeypatch, capsys):
        root = HarnessPath(tmp_path)
        init_harness(root)
        _init_git_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
        _write_phase_metadata(tmp_path, "150D", "abc1234567890")

        exit_code = main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification certification: eligible" in out
        assert "Notification dispatch: sent" in out
        marker = read_notification_dispatch_marker(tmp_path / ".pcae" / "phase-reports" / ".last-notified.json")
        assert marker["phase_id"] == "150D"
        assert marker["commit"] == "abc12345"
        assert marker["delivery_purpose"] == "ordinary_completion"
        assert marker["report_digest"]
        assert marker["finalization_snapshot_id"]

    def test_duplicate_dispatch_is_certified_already_dispatched(self, tmp_path, monkeypatch, capsys):
        root = HarnessPath(tmp_path)
        init_harness(root)
        _init_git_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
        _write_phase_metadata(tmp_path, "150D", "abc1234567890")

        main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
        capsys.readouterr()

        exit_code = main(["phase", "complete", "--summary", "Finished 150D again", "--allow-partial-report"])
        out = capsys.readouterr().out

        assert exit_code == 1
        assert "Notification certification: payload_conflict" in out
        assert "Notification dispatch: sent" not in out

    def test_transport_unavailable_skips_without_attempt(self, tmp_path, monkeypatch, capsys):
        root = HarnessPath(tmp_path)
        init_harness(root)
        _init_git_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "")
        _write_phase_metadata(tmp_path, "150D", "abc1234567890")

        exit_code = main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification certification: transport_unavailable" in out
        assert "Notification dispatch: sent" not in out

    def test_push_not_clean_blocks_dispatch(self, tmp_path, monkeypatch, capsys):
        """New in 114B: a NOTIFY transition is not certified while
        origin/main..HEAD has unpushed commits, even with notifications
        enabled and a working sink -- previously this path dispatched
        regardless of push state."""
        root = HarnessPath(tmp_path)
        init_harness(root)
        _init_git_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
        _write_phase_metadata(tmp_path, "150D", "abc1234567890", origin_main_head_count=3)

        exit_code = main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification certification: not_certified" in out
        assert "Notification dispatch: sent" not in out
        marker = read_notification_dispatch_marker(tmp_path / ".pcae" / "phase-reports" / ".last-notified.json")
        assert marker == {}

    def test_canonical_report_written_even_when_dispatch_fails(self, tmp_path, monkeypatch, capsys):
        """Notification failure must never corrupt canonical repository
        state: latest.md/latest.json are written regardless of whether the
        transport attempt succeeds."""
        root = HarnessPath(tmp_path)
        init_harness(root)
        _init_git_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")
        monkeypatch.delenv("PCAE_TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("PCAE_TELEGRAM_CHAT_ID", raising=False)
        monkeypatch.delenv("PCAE_TELEGRAM_ENABLED", raising=False)
        _write_phase_metadata(tmp_path, "150D", "abc1234567890")

        exit_code = main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification certification: eligible" in out
        assert "Notification dispatch: failed" in out
        latest_json = tmp_path / ".pcae" / "phase-reports" / "latest.json"
        assert latest_json.exists()
        assert json.loads(latest_json.read_text())["phase_id"] == "150D"
        marker = read_notification_dispatch_marker(tmp_path / ".pcae" / "phase-reports" / ".last-notified.json")
        assert marker == {}

    def test_retry_after_failed_dispatch_is_not_blocked(self, tmp_path, monkeypatch, capsys):
        """A failed dispatch attempt never writes the idempotency marker,
        so retrying (e.g. once Telegram is actually configured) must still
        be certified eligible -- retries are safe by construction."""
        root = HarnessPath(tmp_path)
        init_harness(root)
        _init_git_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "telegram")
        monkeypatch.delenv("PCAE_TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("PCAE_TELEGRAM_CHAT_ID", raising=False)
        monkeypatch.delenv("PCAE_TELEGRAM_ENABLED", raising=False)
        _write_phase_metadata(tmp_path, "150D", "abc1234567890")

        main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
        capsys.readouterr()

        # Retry with a working sink instead (simulates the operator fixing
        # Telegram configuration and re-running).
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
        exit_code = main(["phase", "complete", "--summary", "Finished 150D retry", "--allow-partial-report"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification certification: eligible" in out
        assert "Notification dispatch: sent" in out
        marker = read_notification_dispatch_marker(tmp_path / ".pcae" / "phase-reports" / ".last-notified.json")
        assert marker["phase_id"] == "150D"
        assert marker["commit"] == "abc12345"
        assert marker["delivery_purpose"] == "ordinary_completion"
        assert marker["report_digest"]
        assert marker["finalization_snapshot_id"]


# ═══════════════════════════════════════════════════════════════════════════
# CLI integration: pcae task finish --commit
# ═══════════════════════════════════════════════════════════════════════════


def _init_repo_with_baseline_commit(tmp_path: Path) -> HarnessPath:
    """`pcae task finish` requires clean `pcae health`/`pcae check`, which
    needs a committed baseline -- unlike `pcae phase complete`, which does
    not gate on those. Mirrors ``test_repository_transition_validator_task_
    finish_integration.py``'s ``_init_repo``."""
    root = HarnessPath(tmp_path)
    init_harness(root)
    _init_git_repo(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
    return root


def _new_task(root: HarnessPath, title: str = "Phase 205Z: Notification Fixture") -> None:
    create_task_contract(
        root,
        title=title,
        goal="verify task-finish notification certification integration",
        mode="implementation",
        allowed_files=[".pcae/**", "tasks/active/**", "tasks/done/**"],
        allowed_zones=["config", "tasks"],
    )


def _write_task_metadata(tmp_path: Path, **overrides) -> dict:
    meta = {
        "phase_id": "205Z",
        "phase_name": "Notification Fixture",
        "status": "completed",
        "summary": "Task finish notification certification fixture.",
        "files_changed_count": 2,
        "tests_added_or_updated": "4 tests added",
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "clean"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
        ],
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": "passed"},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "no_go_confirmation": (
            "No notification integration beyond certified transitions. No push-check "
            "integration. No execution. No authorization. No Permission Broker "
            "enforcement. No Telegram inbound. No REST. No Web UI. No Dashboard. "
            "No package publication. No lifecycle command beyond task finish."
        ),
        "commit_attribution": "phase_owned",
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": "205A - Next Phase",
        "execution_availability": "unavailable",
    }
    meta.update(overrides)
    path = tmp_path / ".pcae" / "phase-completion-metadata.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def _finish(tmp_path: Path, monkeypatch, commit_message: str = "Smoke finish commit") -> int:
    """`--commit` takes a commit *message*; `task finish` makes a real git
    commit and derives its own hash from that, so distinct invocations
    naturally produce distinct hashes -- unlike `pcae phase complete`,
    which reads a caller-declared hash straight from metadata."""
    monkeypatch.chdir(tmp_path)
    return main(["task", "finish", "--staged-file-aware", "--commit", commit_message])


class TestTaskFinishNotificationCertification:
    def test_eligible_dispatch_is_certified_and_sent(self, tmp_path, monkeypatch, capsys):
        root = _init_repo_with_baseline_commit(tmp_path)
        _new_task(root)
        _write_task_metadata(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        exit_code = _finish(tmp_path, monkeypatch)
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Report notification: sent" in out
        marker = read_notification_dispatch_marker(tmp_path / ".pcae" / "phase-reports" / ".last-notified.json")
        assert marker["phase_id"] == "205Z"
        assert marker["commit"]

    def test_duplicate_dispatch_is_skipped_for_same_commit(self, tmp_path, monkeypatch, capsys):
        """Same phase_id + same actual commit hash must not dispatch twice.
        Exercised at the ``_finalize_task_report_and_notify`` level with a
        fixed ``commit_hash`` -- a real `task finish --commit MESSAGE`
        creates a genuinely new git commit (and hash) each call, so two
        separate CLI invocations are not actually a duplicate transition;
        this reproduces the same-commit-retried-twice case the idempotency
        guard exists for (e.g. a crashed finalization retried without a new
        commit)."""
        from pcae.commands.task import _finalize_task_report_and_notify

        root = _init_repo_with_baseline_commit(tmp_path)
        _new_task(root)
        _write_task_metadata(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
        monkeypatch.chdir(tmp_path)

        first = _finalize_task_report_and_notify("abc1234567890", active_task_title="Phase 205Z: Notification Fixture")
        assert first["notification_status"] == "sent"

        second = _finalize_task_report_and_notify("abc1234567890", active_task_title="Phase 205Z: Notification Fixture")
        assert second["status"] == "skipped_duplicate"

    # Push-not-clean enforcement for the NOTIFY transition itself is
    # covered directly by TestCertifyNotificationTransitionPushNotClean and,
    # end-to-end, by TestPhaseCompleteNotificationCertification. On this
    # path specifically, an unclean push already makes
    # `validate_finalization_gate()` classify `report_completeness` as
    # partial before certification is ever reached (task finish has no
    # `--allow-partial-report` override), so it quarantines upstream --
    # there is no reachable CLI scenario where certification is the first
    # thing to catch it here.


# ═══════════════════════════════════════════════════════════════════════════
# Single notification authority: both callers share one certification path
# ═══════════════════════════════════════════════════════════════════════════


class TestSingleNotificationAuthority:
    def test_phase_complete_and_task_finish_call_the_same_certification_function(self):
        import inspect

        import pcae.commands.phase as phase_module
        import pcae.commands.task as task_module

        phase_src = inspect.getsource(phase_module._finalize_report_and_notify)
        task_src = inspect.getsource(task_module._finalize_task_report_and_notify)

        assert "certify_notification_transition(" in phase_src
        assert "certify_notification_transition(" in task_src
