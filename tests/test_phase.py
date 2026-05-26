from __future__ import annotations

from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.agent import acquire_agent_lock, read_agent_lock
from pcae.core.paths import HarnessPath
from pcae.core.provenance import read_provenance_history
from pcae.core.tasks import create_task_contract


# ---------------------------------------------------------------------------
# pcae phase complete
# ---------------------------------------------------------------------------


def test_phase_complete_records_phase_completed_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Finished Phase 32A"])

    capsys.readouterr()
    assert exit_code == 0
    history = read_provenance_history(root)
    assert any(e.event_type == "phase_completed" for e in history.events)
    phase_event = next(e for e in history.events if e.event_type == "phase_completed")
    assert phase_event.summary == "Finished Phase 32A"


def test_phase_complete_releases_lock_and_records_agent_released(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Phase done with lock"])

    capsys.readouterr()
    assert exit_code == 0
    assert read_agent_lock(root) is None
    history = read_provenance_history(root)
    event_types = [e.event_type for e in history.events]
    assert "phase_completed" in event_types
    assert "agent_released" in event_types


def test_phase_complete_without_lock_succeeds(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "No lock held"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent lock: none" in output


def test_phase_complete_prints_summary_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Completed Phase 32B"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase complete." in output
    assert "Summary: Completed Phase 32B" in output
    assert "Provenance events:" in output
    assert "Agent lock: none" in output


def test_phase_complete_with_lock_prints_released(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "complete", "--summary", "Phase done"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent lock: released (by claude-local)" in output


def test_phase_complete_phase_completed_captures_agent_id(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    acquire_agent_lock(root, "claude-local")
    monkeypatch.chdir(tmp_path)

    main(["phase", "complete", "--summary", "Lock held at record time"])

    capsys.readouterr()
    history = read_provenance_history(root)
    phase_event = next(e for e in history.events if e.event_type == "phase_completed")
    assert phase_event.agent_id == "claude-local"


# ---------------------------------------------------------------------------
# pcae phase start
# ---------------------------------------------------------------------------


def test_phase_start_acquires_agent_lock(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Phase start task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    capsys.readouterr()
    assert exit_code == 0
    lock = read_agent_lock(root)
    assert lock is not None
    assert lock.agent_id == "claude-local"


def test_phase_start_records_agent_acquired_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Phase start task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["phase", "start", "--agent-id", "claude-local"])

    capsys.readouterr()
    history = read_provenance_history(root)
    assert any(e.event_type == "agent_acquired" for e in history.events)
    acquired = next(e for e in history.events if e.event_type == "agent_acquired")
    assert acquired.agent_id == "claude-local"


def test_phase_start_stops_when_check_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Phase start stopped: pcae check failed." in output
    assert "No active task contract found in tasks/active/." in output
    assert read_agent_lock(root) is None


def test_phase_start_stops_when_lock_already_held(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Phase lock task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    acquire_agent_lock(root, "other-agent")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Agent lock already held by other-agent." in output


def test_phase_start_prints_active_task_and_timeline(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Timeline test task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase start." in output
    assert "Check: passed" in output
    assert "Active task:" in output
    assert "Title: Timeline test task" in output
    assert "Provenance events:" in output
    assert "Latest event:" in output


def test_phase_start_no_provenance_reports_none(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Fresh repo task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["phase", "start", "--agent-id", "claude-local"])

    output = capsys.readouterr().out
    assert exit_code == 0
    # After start_phase, at least the agent_acquired event exists
    assert "Provenance events: 1" in output
    assert "Latest event: Agent lock acquired by claude-local" in output


# ---------------------------------------------------------------------------
# round-trip: phase start → phase complete
# ---------------------------------------------------------------------------


def test_phase_start_then_complete_round_trip(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = HarnessPath(tmp_path)
    init_harness(root)
    init_git_repo(tmp_path)
    create_task_contract(root, "Round trip task")
    patch_task_allowed_files(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    start_code = main(["phase", "start", "--agent-id", "claude-local"])
    capsys.readouterr()
    complete_code = main(["phase", "complete", "--summary", "Round trip done"])
    capsys.readouterr()

    assert start_code == 0
    assert complete_code == 0
    assert read_agent_lock(root) is None
    history = read_provenance_history(root)
    event_types = [e.event_type for e in history.events]
    assert event_types == ["agent_acquired", "phase_completed", "agent_released"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def patch_task_allowed_files(root: Path) -> None:
    task_dir = root / "tasks" / "active"
    for task_file in task_dir.glob("*.md"):
        content = task_file.read_text(encoding="utf-8")
        task_file.write_text(
            content.replace(
                "## Allowed Files\n\n- TBD",
                "## Allowed Files\n\n- .pcae/**",
            ),
            encoding="utf-8",
        )


def init_git_repo(root: Path) -> None:
    run_git(root, "init")
    run_git(root, "config", "user.email", "test@example.com")
    run_git(root, "config", "user.name", "Test User")


def commit_baseline(root: Path) -> None:
    run_git(root, "add", ".")
    run_git(root, "commit", "-m", "baseline")


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
