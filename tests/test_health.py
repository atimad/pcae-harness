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


def test_health_command_reports_healthy_governance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_ready_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )
    write_architecture_history(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["health"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PCAE health" in output
    assert "Overall status: healthy" in output
    assert "Required PCAE files: all present" in output
    assert "Policy validation: valid (repo config)" in output
    assert "Active task: 20260524-0800-health-task" in output
    assert "Title: Health task" in output
    assert "Session continuity: verified" in output
    assert "Architecture history entries: 1" in output
    assert "Latest enforcement mode: advisory" in output
    assert "Latest dependency warnings: 0" in output
    assert "Git status: clean" in output


def test_health_command_reports_warnings_without_failing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_ready_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["health"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Overall status: healthy" in output
    assert "Session continuity: missing" in output
    assert "Architecture history entries: missing" in output
    assert "warning: Session snapshot missing at .pcae/session.json." in output
    assert "warning: No architecture history found at .pcae/architecture-history.json." in output


def test_health_command_returns_nonzero_when_check_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["health"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Overall status: unhealthy" in output
    assert "Health check failed:" in output
    assert "No active task contract found in tasks/active/." in output


def test_health_command_is_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    init_ready_repo(tmp_path)
    write_session_snapshot(
        HarnessPath(tmp_path),
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )
    write_architecture_history(tmp_path)
    commit_baseline(tmp_path)
    before = text_file_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["health"])

    after = text_file_snapshot(tmp_path)
    capsys.readouterr()
    assert exit_code == 0
    assert after == before


def init_ready_repo(root: Path) -> None:
    init_harness(HarnessPath(root))
    init_git_repo(root)
    create_task_contract(
        HarnessPath(root),
        "Health task",
        created_at=datetime(2026, 5, 24, 8, 0, tzinfo=timezone.utc),
    )


def write_architecture_history(root: Path) -> None:
    write_file(
        root / ".pcae" / "architecture-history.json",
        json.dumps(
            [
                {
                    "active_task": {
                        "id": "20260524-0800-health-task",
                        "title": "Health task",
                    },
                    "architecture_zones_touched": {},
                    "changed_files_count": 0,
                    "dependency_warnings_count": 0,
                    "enforcement_mode": "advisory",
                    "git_branch": "main",
                    "session_continuity": "verified",
                    "timestamp": "2026-05-24T08:00:00+00:00",
                }
            ]
        ),
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


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def text_file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }
