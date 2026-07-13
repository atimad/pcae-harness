"""Phase 114C: Push Authorization & Post-Push Reconciliation.

Covers the live 114B/114B.1 finding: `_finalize_report_and_notify` /
`_finalize_task_report_and_notify` read `pushed_status` /
`origin_main_head_count` from the declared, static
`.pcae/phase-completion-metadata.json` -- never re-deriving them from live
git state. A genuinely pushed repository (confirmed by `pcae push check`:
`origin/main..HEAD` = 0) was quarantined by `pcae phase complete` because
the metadata file still held pre-push values nobody had refreshed.

These tests exercise `reconcile_push_state`/`compute_live_push_state`
directly (pure-function unit tests) and through both lifecycle commands,
using a real local "origin" remote (a bare repo under `tmp_path`, no
network) so live push state is genuinely determinable -- unlike every
other fixture in this suite, which has no origin/main ref at all and so
exercises the metadata-fallback path instead.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.push_state_reconciliation import (
    LivePushState,
    compute_live_push_state,
    reconcile_push_state,
)
from pcae.core.tasks import create_task_contract

# ═══════════════════════════════════════════════════════════════════════════
# Unit tests: compute_live_push_state() / reconcile_push_state()
# ═══════════════════════════════════════════════════════════════════════════


def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo_with_real_origin(tmp_path: Path) -> Path:
    """A real (local, no-network) origin remote -- so origin/main is an
    actually resolvable ref, unlike every other fixture in this suite."""
    work = tmp_path / "work"
    origin_bare = tmp_path / "origin.git"
    work.mkdir()
    subprocess.run(["git", "init", "--bare", str(origin_bare)], check=True, capture_output=True)
    _run_git(work, "init")
    _run_git(work, "config", "user.email", "test@example.com")
    _run_git(work, "config", "user.name", "Test User")
    _run_git(work, "checkout", "-b", "main")

    root = HarnessPath(work)
    init_harness(root)
    _run_git(work, "add", ".")
    _run_git(work, "commit", "-m", "baseline")
    _run_git(work, "remote", "add", "origin", str(origin_bare))
    _run_git(work, "push", "-u", "origin", "main")
    return work


def _write_extra_commit(work: Path, name: str) -> None:
    (work / name).write_text("content\n")
    _run_git(work, "add", name)
    _run_git(work, "commit", "-m", f"add {name}")


def test_no_origin_ref_is_indeterminate(tmp_path):
    """The common case in this test suite: no real remote configured."""
    _run_git(tmp_path, "init")
    _run_git(tmp_path, "config", "user.email", "test@example.com")
    _run_git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "a.txt").write_text("x")
    _run_git(tmp_path, "add", ".")
    _run_git(tmp_path, "commit", "-m", "init")

    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        state = compute_live_push_state()
    finally:
        os.chdir(old_cwd)

    assert state.determinable is False
    assert state.origin_main_head_count is None
    assert state.pushed_status == ""


def test_live_clean_push_is_determinable(tmp_path):
    import os
    work = _init_repo_with_real_origin(tmp_path)
    old_cwd = os.getcwd()
    try:
        os.chdir(work)
        state = compute_live_push_state()
    finally:
        os.chdir(old_cwd)

    assert state.determinable is True
    assert state.origin_main_head_count == 0
    assert state.pushed_status == "pushed"


def test_live_unpushed_commit_is_determinable(tmp_path):
    import os
    work = _init_repo_with_real_origin(tmp_path)
    _write_extra_commit(work, "extra.txt")
    old_cwd = os.getcwd()
    try:
        os.chdir(work)
        state = compute_live_push_state()
    finally:
        os.chdir(old_cwd)

    assert state.determinable is True
    assert state.origin_main_head_count == 1
    assert state.pushed_status == "not_pushed"


def test_reconcile_falls_back_to_metadata_when_indeterminate():
    live = LivePushState(determinable=False, origin_main_head_count=None, pushed_status="")
    metadata = {"pushed_status": "not_pushed", "origin_main_head_count": 7}

    result = reconcile_push_state(metadata, live=live)

    assert result.source == "metadata"
    assert result.pushed_status == "not_pushed"
    assert result.origin_main_head_count == 7
    assert result.metadata_push_state_stale is False


def test_reconcile_live_clean_overrides_stale_metadata_not_pushed():
    """The exact 114B/114B.1 forensic scenario, at the pure-function level."""
    live = LivePushState(determinable=True, origin_main_head_count=0, pushed_status="pushed")
    metadata = {"pushed_status": "not_pushed", "origin_main_head_count": 7}

    result = reconcile_push_state(metadata, live=live)

    assert result.source == "live"
    assert result.pushed_status == "pushed"
    assert result.origin_main_head_count == 0
    assert result.metadata_push_state_stale is True
    assert result.metadata_pushed_status == "not_pushed"
    assert result.metadata_origin_main_head_count == 7
    assert result.live_origin_main_head_count == 0


def test_reconcile_live_unpushed_overrides_stale_metadata_pushed():
    """Live state cannot be gamed by metadata optimistically claiming clean."""
    live = LivePushState(determinable=True, origin_main_head_count=2, pushed_status="not_pushed")
    metadata = {"pushed_status": "pushed", "origin_main_head_count": 0}

    result = reconcile_push_state(metadata, live=live)

    assert result.source == "live"
    assert result.pushed_status == "not_pushed"
    assert result.origin_main_head_count == 2
    assert result.metadata_push_state_stale is True


def test_reconcile_agreement_is_not_flagged_stale():
    live = LivePushState(determinable=True, origin_main_head_count=0, pushed_status="pushed")
    metadata = {"pushed_status": "pushed", "origin_main_head_count": 0}

    result = reconcile_push_state(metadata, live=live)

    assert result.metadata_push_state_stale is False
    assert result.pushed_status == "pushed"


def test_diagnostics_shape_matches_objective_8():
    live = LivePushState(determinable=True, origin_main_head_count=0, pushed_status="pushed")
    metadata = {"pushed_status": "not_pushed", "origin_main_head_count": 7}
    result = reconcile_push_state(metadata, live=live)
    diagnostics = result.to_diagnostics()

    assert diagnostics["metadata_push_state_stale"] is True
    assert diagnostics["metadata_origin_main_head_count"] == 7
    assert diagnostics["live_origin_main_head_count"] == 0
    assert diagnostics["reconciled_push_state"] == "pushed"


# ═══════════════════════════════════════════════════════════════════════════
# CLI integration: pcae phase complete
# ═══════════════════════════════════════════════════════════════════════════


def _write_phase_metadata(work: Path, phase_id: str, commit_hash: str, **overrides) -> None:
    meta = {
        "phase_id": phase_id,
        "phase_name": f"Test {phase_id}",
        "status": "completed",
        "phase_commits": [{"hash": commit_hash}],
        "recommended_next_phase": "114D — Next",
        "execution_availability": "unavailable",
    }
    meta.update(overrides)
    (work / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))


class TestPhaseCompleteReconciliation:
    def test_certifies_despite_stale_not_pushed_metadata(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        monkeypatch.chdir(work)
        _write_phase_metadata(
            work, "114C", "abc1234567890",
            pushed_status="not_pushed", origin_main_head_count=7,
        )

        exit_code = main(["phase", "complete", "--summary", "Finished 114C", "--allow-partial-report"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Push state reconciliation: stale metadata detected" in out
        assert "metadata_push_state_stale: true" in out
        assert "live_origin_main_head_count: 0" in out
        assert "reconciled_push_state: pushed" in out
        assert "pushed_status is 'not_pushed'" not in out
        assert "origin/main..HEAD is 7, not 0" not in out

    def test_live_unpushed_still_blocks_despite_metadata_claiming_pushed(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        _write_extra_commit(work, "unpushed.txt")
        monkeypatch.chdir(work)
        _write_phase_metadata(
            work, "114C", "abc1234567890",
            pushed_status="pushed", origin_main_head_count=0,
        )

        exit_code = main(["phase", "complete", "--summary", "Finished 114C"])
        out = capsys.readouterr().out

        assert exit_code == 1
        assert "Push state reconciliation: stale metadata detected" in out
        assert "pushed_status is 'not_pushed'" in out
        assert "origin/main..HEAD is 1, not 0" in out

    def test_notification_eligible_after_reconciled_clean_push(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
        _write_phase_metadata(
            work, "114C", "abc1234567890",
            pushed_status="not_pushed", origin_main_head_count=9,
        )

        exit_code = main(["phase", "complete", "--summary", "Finished 114C", "--allow-partial-report"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification certification: eligible" in out
        assert "Notification dispatch: skipped" in out
        assert not (work / ".pcae" / "phase-reports" / "latest.json").exists()


# ═══════════════════════════════════════════════════════════════════════════
# CLI integration: pcae task finish --commit
# ═══════════════════════════════════════════════════════════════════════════


def _new_task(root: HarnessPath, title: str = "Phase 205Z: Reconciliation Fixture") -> None:
    create_task_contract(
        root,
        title=title,
        goal="verify push-state reconciliation integration",
        mode="implementation",
        allowed_files=[".pcae/**", "tasks/active/**", "tasks/done/**"],
        allowed_zones=["config", "tasks"],
    )


def _write_task_metadata(work: Path, **overrides) -> dict:
    meta = {
        "phase_id": "205Z",
        "phase_name": "Reconciliation Fixture",
        "status": "completed",
        "summary": "Task finish reconciliation fixture.",
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
            "No notification integration. No push-check integration. No execution. "
            "No authorization. No Permission Broker enforcement. No Telegram inbound. "
            "No REST. No Web UI. No Dashboard. No package publication. "
            "No lifecycle command beyond task finish."
        ),
        "commit_attribution": "phase_owned",
        "pushed_status": "not_pushed",
        "origin_main_head_count": 8,
        "recommended_next_phase": "114D - Next Phase",
        "execution_availability": "unavailable",
    }
    meta.update(overrides)
    path = work / ".pcae" / "phase-completion-metadata.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


class TestTaskFinishReconciliation:
    def test_live_state_overrides_stale_metadata_value(self, tmp_path, monkeypatch, capsys):
        """`pcae task finish` always creates its own closure commit before
        finalization runs, so live push state at that instant is
        genuinely `not_pushed` -- the true live count is 1 (the closure
        commit itself). The *declared* metadata falsely claims a stale,
        much larger count (8). Reconciliation must report the true live
        value, not the stale declared one -- proving live overrides
        metadata even when both agree on the qualitative "not pushed"
        direction but disagree on the actual count."""
        work = _init_repo_with_real_origin(tmp_path)
        root = HarnessPath(work)
        _new_task(root)
        _write_task_metadata(work)
        monkeypatch.chdir(work)

        main(["task", "finish", "--staged-file-aware", "--commit", "Finish 205Z fixture"])
        out = capsys.readouterr().out

        assert "Push state reconciliation: stale metadata detected" in out
        assert "metadata_origin_main_head_count: 8" in out
        assert "live_origin_main_head_count: 1" in out
        assert "reconciled_push_state: not_pushed" in out


# ═══════════════════════════════════════════════════════════════════════════
# No raw push added; execution unavailable
# ═══════════════════════════════════════════════════════════════════════════


def test_reconciliation_module_never_invokes_git_push():
    import inspect

    import pcae.core.push_state_reconciliation as mod

    source = inspect.getsource(mod)
    assert '"push"' not in source
    assert "'push'" not in source


def test_execution_availability_constant_unchanged():
    from pcae.core.runtime_context import EXECUTION_AVAILABILITY

    assert EXECUTION_AVAILABILITY == "unavailable"
