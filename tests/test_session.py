from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.session import write_session_snapshot
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
