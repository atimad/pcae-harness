from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.session import write_session_snapshot
from pcae.core.tasks import create_task_contract, close_active_task, find_latest_active_task


def init_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path, check=True, capture_output=True,
    )


def commit_all(tmp_path: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=tmp_path, check=True, capture_output=True,
    )


def test_push_check_clean_repo_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Push check task",
        created_at=datetime(2026, 6, 18, 6, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Ready to push." in output
    assert "Working tree: clean" in output


def test_push_check_dirty_tree_reports_not_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Dirty push task",
        created_at=datetime(2026, 6, 18, 6, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Not ready to push:" in output
    assert "working tree is dirty" in output


def test_push_check_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "JSON push task",
        created_at=datetime(2026, 6, 18, 6, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert "branch" in parsed
    assert "working_tree_clean" in parsed
    assert "unpushed_commits" in parsed
    assert "health_status" in parsed
    assert "check_passed" in parsed
    assert "ready" in parsed
    assert "mode" in parsed
    assert parsed["mode"] == "active_task"
    assert isinstance(parsed["unpushed_commits"], int)


def test_push_check_reports_unpushed_commits(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Unpushed task",
        created_at=datetime(2026, 6, 18, 6, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert "Unpushed commits:" in output


def test_push_check_reports_branch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Branch task",
        created_at=datetime(2026, 6, 18, 6, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert "Branch:" in output


# --- Phase 70G: post-finish push readiness ---


def test_70g_push_check_post_finish_closure_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Closeable task",
        created_at=datetime(2026, 6, 18, 6, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")

    active = find_latest_active_task(HarnessPath(tmp_path))
    close_active_task(active)
    commit_all(tmp_path, "Close task")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Ready to push." in output
    assert "Mode: post_finish_closure" in output


def test_70g_push_check_post_finish_closure_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "JSON closure task",
        created_at=datetime(2026, 6, 18, 6, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")

    active = find_latest_active_task(HarnessPath(tmp_path))
    close_active_task(active)
    commit_all(tmp_path, "Close task")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert parsed["ready"] is True
    assert parsed["mode"] == "post_finish_closure"


def test_70g_push_check_no_task_dirty_tree_not_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Dirty closure task",
        created_at=datetime(2026, 6, 18, 6, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")

    active = find_latest_active_task(HarnessPath(tmp_path))
    close_active_task(active)
    commit_all(tmp_path, "Close task")
    (tmp_path / "extra.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Not ready to push:" in output


def test_70g_push_check_no_task_no_closure_commit_not_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "random.txt").write_text("content", encoding="utf-8")
    commit_all(tmp_path, "init without task")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Not ready to push:" in output


def test_70g_push_check_mode_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Active mode task",
        created_at=datetime(2026, 6, 18, 6, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check", "--json"])

    output = capsys.readouterr().out
    parsed = json.loads(output)
    assert parsed["mode"] == "active_task"
