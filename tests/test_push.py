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


def test_70g_push_check_no_task_clean_tree_is_idle_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "random.txt").write_text("content", encoding="utf-8")
    commit_all(tmp_path, "init without task")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Ready to push." in output


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


# --- Phase 70H: pcae push (governed push execution) ---


def test_70h_push_run_dry_run_does_not_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Dry run task",
        created_at=datetime(2026, 6, 18, 7, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Dry run: push skipped." in output
    assert "Ready to push." in output


def test_70h_push_run_refuses_dirty_tree(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Dirty run task",
        created_at=datetime(2026, 6, 18, 7, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Not ready to push:" in output


def test_70h_push_run_dry_run_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "JSON dry run task",
        created_at=datetime(2026, 6, 18, 7, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "--dry-run", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert parsed["ready"] is True
    assert parsed["dry_run"] is True
    assert parsed["pushed"] is False


def test_70h_push_run_nothing_to_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Nothing task",
        created_at=datetime(2026, 6, 18, 7, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    # Create a fake remote so unpushed count = 0
    remote_path = tmp_path.parent / "remote.git"
    subprocess.run(["git", "clone", "--bare", str(tmp_path), str(remote_path)],
                   capture_output=True, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_path)],
                   cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "fetch", "origin"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "branch", "--set-upstream-to=origin/main", "main"],
                   cwd=tmp_path, capture_output=True, check=True)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Nothing to push." in output


def test_70h_push_run_json_refuses_not_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Not ready task",
        created_at=datetime(2026, 6, 18, 7, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    parsed = json.loads(output)
    assert parsed["pushed"] is False
    assert parsed["ready"] is False


# --- Phase 70S: lifecycle review status in push check ---


def test_70s_push_check_shows_missing_review(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "No review task",
        created_at=datetime(2026, 6, 18, 11, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Lifecycle review: missing" in output


def test_70s_push_check_shows_approved_review(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from pcae.core.review import create_lifecycle_review

    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Approved review task",
        created_at=datetime(2026, 6, 18, 11, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    create_lifecycle_review(HarnessPath(tmp_path), disposition="approved")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Lifecycle review: approved" in output


def test_70s_push_check_json_includes_review(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "JSON review task",
        created_at=datetime(2026, 6, 18, 11, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check", "--json"])

    output = capsys.readouterr().out
    parsed = json.loads(output)
    assert "lifecycle_review" in parsed
    assert parsed["lifecycle_review"] == "missing"


def test_70s_missing_review_does_not_block_push(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "No block task",
        created_at=datetime(2026, 6, 18, 11, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Ready to push." in output


def test_70s_idle_review_not_applicable(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["push", "check", "--json"])

    output = capsys.readouterr().out
    parsed = json.loads(output)
    assert parsed["lifecycle_review"] == "not_applicable"
