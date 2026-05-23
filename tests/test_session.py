from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.session import (
    SessionUpdate,
    read_session_snapshot,
    update_session_snapshot,
    write_session_snapshot,
)
from pcae.core.tasks import create_task_contract


def test_session_write_creates_readable_snapshot(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Write handoff snapshot",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    write_file(tmp_path / "src" / "changed.py", "print('changed')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "changed.py", "print('changed again')\n")

    snapshot = write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    session_file = tmp_path / ".pcae" / "session.json"
    assert snapshot.relative_path == Path(".pcae/session.json")
    assert session_file.is_file()

    data = json.loads(session_file.read_text(encoding="utf-8"))
    assert data["timestamp"] == "2026-05-23T08:00:00+00:00"
    assert data["active_task"] == {
        "id": "20260523-0730-write-handoff-snapshot",
        "title": "Write handoff snapshot",
    }
    assert data["git"]["branch"] in {"main", "master"}
    assert data["git"]["status_summary"] == "1 changed file"
    assert data["git"]["changed_files"] == [
        {"path": "src/changed.py", "status": " M"}
    ]
    assert data["current_objective"] == ""
    assert data["last_completed_step"] == ""
    assert data["next_recommended_step"] == ""
    assert data["blockers"] == []
    assert data["warnings"] == []
    assert data["architectural_notes"] == []


def test_session_write_works_without_active_task(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)

    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    data = json.loads((tmp_path / ".pcae" / "session.json").read_text(encoding="utf-8"))
    assert data["active_task"] is None


def test_session_write_command_reports_output(tmp_path: Path, monkeypatch, capsys) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "write"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Wrote session snapshot: .pcae/session.json" in output
    assert (tmp_path / ".pcae" / "session.json").is_file()


def test_session_write_does_not_overwrite_policy_config(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    policy_file = tmp_path / ".pcae" / "policy.toml"
    before = policy_file.read_text(encoding="utf-8")

    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    assert policy_file.read_text(encoding="utf-8") == before


def test_session_update_replaces_and_appends_fields(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    snapshot = update_session_snapshot(
        HarnessPath(tmp_path),
        SessionUpdate(
            objective="Implement session update",
            completed_step="Added core updater",
            next_step="Run checks",
            blocker="None",
            warning="Keep policy untouched",
            note="Preserve git fields",
        ),
    )

    assert snapshot.data["current_objective"] == "Implement session update"
    assert snapshot.data["last_completed_step"] == "Added core updater"
    assert snapshot.data["next_recommended_step"] == "Run checks"
    assert snapshot.data["blockers"] == ["None"]
    assert snapshot.data["warnings"] == ["Keep policy untouched"]
    assert snapshot.data["architectural_notes"] == ["Preserve git fields"]
    assert snapshot.data["git"]["branch"] in {"main", "master"}


def test_session_update_creates_snapshot_when_missing(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Update handoff",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )

    snapshot = update_session_snapshot(
        HarnessPath(tmp_path),
        SessionUpdate(objective="Create on update"),
    )

    assert (tmp_path / ".pcae" / "session.json").is_file()
    assert snapshot.data["current_objective"] == "Create on update"
    assert snapshot.data["active_task"] == {
        "id": "20260523-0730-update-handoff",
        "title": "Update handoff",
    }


def test_session_update_does_not_overwrite_policy_config(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    policy_file = tmp_path / ".pcae" / "policy.toml"
    before = policy_file.read_text(encoding="utf-8")

    update_session_snapshot(
        HarnessPath(tmp_path),
        SessionUpdate(objective="Keep policy stable"),
    )

    assert policy_file.read_text(encoding="utf-8") == before


def test_session_read_loads_snapshot(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )

    snapshot = read_session_snapshot(HarnessPath(tmp_path))

    assert snapshot is not None
    assert snapshot.relative_path == Path(".pcae/session.json")
    assert snapshot.data["timestamp"] == "2026-05-23T08:00:00+00:00"


def test_session_read_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_session_snapshot(HarnessPath(tmp_path)) is None


def test_session_read_command_prints_resume_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Resume work",
        created_at=datetime(2026, 5, 23, 7, 30, tzinfo=timezone.utc),
    )
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "read"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Session snapshot:" in output
    assert "Active task: 20260523-0730-resume-work" in output
    assert "Title: Resume work" in output
    assert "Git branch:" in output
    assert "Git status:" in output
    assert "Current objective:" in output
    assert "Last completed step:" in output
    assert "Next recommended step:" in output
    assert "Blockers:\n  none" in output
    assert "Warnings:\n  none" in output
    assert "Architectural notes:\n  none" in output


def test_session_read_command_prints_blockers_and_warnings(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    session_file = tmp_path / ".pcae" / "session.json"
    session_file.write_text(
        json.dumps(
            {
                "active_task": None,
                "architectural_notes": ["Keep parser simple"],
                "blockers": ["Need review"],
                "current_objective": "Finish session read",
                "git": {"status_summary": "clean"},
                "last_completed_step": "Added tests",
                "next_recommended_step": "Run checks",
                "warnings": ["Pending docs"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "read"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Active task: none" in output
    assert "Git branch: unknown" in output
    assert "Git status: clean" in output
    assert "Current objective: Finish session read" in output
    assert "Last completed step: Added tests" in output
    assert "Next recommended step: Run checks" in output
    assert "  - Need review" in output
    assert "  - Pending docs" in output
    assert "  - Keep parser simple" in output


def test_session_read_command_reports_missing_snapshot(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "read"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No session snapshot found at .pcae/session.json." in output


def test_session_update_command_updates_read_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    update_exit_code = main(
        [
            "session",
            "update",
            "--objective",
            "Finish Phase 8A",
            "--completed-step",
            "Added update command",
            "--next-step",
            "Run validation",
            "--blocker",
            "None",
            "--warning",
            "Watch docs",
            "--note",
            "Session JSON stays readable",
        ]
    )
    update_output = capsys.readouterr().out

    read_exit_code = main(["session", "read"])
    read_output = capsys.readouterr().out

    assert update_exit_code == 0
    assert "Updated session snapshot: .pcae/session.json" in update_output
    assert read_exit_code == 0
    assert "Current objective: Finish Phase 8A" in read_output
    assert "Last completed step: Added update command" in read_output
    assert "Next recommended step: Run validation" in read_output
    assert "  - None" in read_output
    assert "  - Watch docs" in read_output
    assert "  - Session JSON stays readable" in read_output


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


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
