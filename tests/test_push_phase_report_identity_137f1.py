"""Phase 137F.1 evidence: push readiness must reject a canonical phase
report that is absent or stale relative to the most recently completed
phase task.

Reproduces the Phase 137F incident: verification work was committed and
pushed while `.pcae/phase-reports/latest.json` still identified the
*previous* phase, because neither `pcae check` nor the pre-existing
phase-report-trust gate compared the report's declared `phase_id` against
the latest completed phase task -- only the report's own internal schema
completeness.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.session import write_session_snapshot
from pcae.core.tasks import (
    close_active_task,
    create_task_contract,
    find_latest_active_task,
)


def init_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)


def commit_all(tmp_path: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=tmp_path, check=True, capture_output=True)


def _close_phase_task(root: HarnessPath, title: str, when: datetime) -> None:
    create_task_contract(root, title, created_at=when)
    active = find_latest_active_task(root)
    close_active_task(active)


def _open_idle_task(root: HarnessPath, title: str, when: datetime) -> None:
    create_task_contract(root, title, created_at=when, mode="idle")


def _write_latest_report(root: HarnessPath, phase_id: str) -> None:
    """Write a *content-complete* canonical report (105A/105B schema) so
    tests targeting the 137F.1 identity gate specifically are not
    incidentally blocked by the pre-existing content-completeness gate."""
    reports_dir = root.path / ".pcae" / "phase-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "latest.json").write_text(
        json.dumps(
            {
                "phase_id": phase_id,
                "status": "completed",
                "files_changed": 1,
                "tests_run": 1,
                "commits": ["deadbeef"],
                "pushed": "pushed",
                "summary": "Reproduction fixture report.",
                "recommended_next_phase": "900Z",
                "governance_results": {
                    "pcae_health": "healthy",
                    "pcae_check": "passed",
                    "pcae_doctor_task_memory": "clean",
                    "pcae_push_check": "clean",
                    "telegram_runtime": "configured",
                },
                "test_results": {
                    "report_notification_tests": "passed",
                    "bootstrap_session_reporting_tests": "passed",
                    "fast_green": "passed",
                },
            }
        ),
        encoding="utf-8",
    )


def _setup_with_remote(tmp_path: Path) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))


def _add_remote_and_fetch(tmp_path: Path) -> None:
    remote_path = tmp_path.parent / f"remote-{tmp_path.name}.git"
    subprocess.run(["git", "clone", "--bare", str(tmp_path), str(remote_path)], capture_output=True, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_path)], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "fetch", "origin"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "branch", "--set-upstream-to=origin/main", "main"], cwd=tmp_path, capture_output=True, check=True)


def test_137f1_missing_canonical_report_blocks_push_after_idle_closure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Reproduces the exact 137F incident: a completed phase task exists,
    the active task is idle, and no canonical report was ever written."""
    _setup_with_remote(tmp_path)
    root = HarnessPath(tmp_path)
    _close_phase_task(root, "Phase 900A — Reproduction Phase", datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc))
    _open_idle_task(root, "Idle: awaiting next governed phase (post-900a)", datetime(2026, 7, 19, 19, 5, tzinfo=timezone.utc))
    write_session_snapshot(root)
    commit_all(tmp_path, "reproduction commit")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Not ready to push:" in output
    assert "canonical phase report is stale or missing" in output
    assert "Phase 900A" in output


def test_137f1_stale_prior_phase_report_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The exact 137F shape: latest.json exists and is schema-complete,
    but it still names the *previous* phase, not the one just closed."""
    _setup_with_remote(tmp_path)
    root = HarnessPath(tmp_path)
    _close_phase_task(root, "Phase 900B — Reproduction Phase", datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc))
    _open_idle_task(root, "Idle: awaiting next governed phase (post-900b)", datetime(2026, 7, 19, 19, 5, tzinfo=timezone.utc))
    _write_latest_report(root, "900A")  # stale: names the phase before 900B
    write_session_snapshot(root)
    commit_all(tmp_path, "reproduction commit")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Not ready to push:" in output
    assert "'900A'" in output
    assert "900B" in output


def test_137f1_matching_canonical_report_does_not_block_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A canonical report whose phase_id matches the latest completed
    phase task must not be treated as stale."""
    _setup_with_remote(tmp_path)
    root = HarnessPath(tmp_path)
    _close_phase_task(root, "Phase 900C — Reproduction Phase", datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc))
    _open_idle_task(root, "Idle: awaiting next governed phase (post-900c)", datetime(2026, 7, 19, 19, 5, tzinfo=timezone.utc))
    _write_latest_report(root, "900C")
    write_session_snapshot(root)
    commit_all(tmp_path, "reproduction commit")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Ready to push." in output
    assert "Phase report identity: passed" in output


def test_137f1_phase_still_in_progress_is_not_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A phase actively being worked on (active task is not idle) must
    never be blocked merely because no report exists yet -- the report is
    only expected once the phase reaches finalization."""
    _setup_with_remote(tmp_path)
    root = HarnessPath(tmp_path)
    _close_phase_task(root, "Phase 900D — Reproduction Phase", datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc))
    create_task_contract(root, "Phase 900E — In Progress Phase", created_at=datetime(2026, 7, 19, 19, 5, tzinfo=timezone.utc))
    write_session_snapshot(root)
    commit_all(tmp_path, "reproduction commit")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Phase report identity: not_applicable" in output


def test_137f1_no_completed_phase_task_is_not_blocked(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A bootstrapped repository with no phase work yet must not be
    blocked by this gate (nothing to reconcile against)."""
    _setup_with_remote(tmp_path)
    root = HarnessPath(tmp_path)
    create_task_contract(root, "Plain task", created_at=datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc))
    write_session_snapshot(root)
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Phase report identity: not_applicable" in output


def test_137f1_malformed_latest_report_json_blocks_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _setup_with_remote(tmp_path)
    root = HarnessPath(tmp_path)
    _close_phase_task(root, "Phase 900F — Reproduction Phase", datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc))
    _open_idle_task(root, "Idle: awaiting next governed phase (post-900f)", datetime(2026, 7, 19, 19, 5, tzinfo=timezone.utc))
    reports_dir = root.path / ".pcae" / "phase-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "latest.json").write_text("{not valid json", encoding="utf-8")
    write_session_snapshot(root)
    commit_all(tmp_path, "reproduction commit")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "not valid JSON" in output


def test_137f1_bare_push_prints_mutating_banner_distinct_from_check(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """`pcae push` must print an explicit, unambiguous banner before it
    executes a real `git push`, so its output cannot be mistaken for the
    read-only `pcae push check` report."""
    _setup_with_remote(tmp_path)
    root = HarnessPath(tmp_path)
    _close_phase_task(root, "Phase 900G — Reproduction Phase", datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc))
    _open_idle_task(root, "Idle: awaiting next governed phase (post-900g)", datetime(2026, 7, 19, 19, 5, tzinfo=timezone.utc))
    _write_latest_report(root, "900G")
    write_session_snapshot(root)
    commit_all(tmp_path, "reproduction commit")
    _add_remote_and_fetch(tmp_path)
    # Create one unpushed commit so readiness is ready and a real push occurs.
    (tmp_path / "extra.txt").write_text("extra", encoding="utf-8")
    commit_all(tmp_path, "extra commit")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "EXECUTING REAL PUSH" in output
    assert "PUSH EXECUTED." in output


def test_137f1_push_check_never_prints_mutating_banner(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _setup_with_remote(tmp_path)
    root = HarnessPath(tmp_path)
    _close_phase_task(root, "Phase 900H — Reproduction Phase", datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc))
    _open_idle_task(root, "Idle: awaiting next governed phase (post-900h)", datetime(2026, 7, 19, 19, 5, tzinfo=timezone.utc))
    _write_latest_report(root, "900H")
    write_session_snapshot(root)
    commit_all(tmp_path, "reproduction commit")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "EXECUTING REAL PUSH" not in output
    assert "PUSH EXECUTED" not in output


def test_137f1_push_help_text_discloses_mutation(capsys) -> None:
    with pytest.raises(SystemExit):
        main(["push", "--help"])
    output = capsys.readouterr().out
    assert "MUTATING" in output

    with pytest.raises(SystemExit):
        main(["push", "check", "--help"])
    output = capsys.readouterr().out
    assert "READ-ONLY" in output
