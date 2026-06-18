from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.agent import (
    HANDOFF_STATE_REFRESH_ADVISORY,
    build_handoff_state_refresh,
)
from pcae.core.check import run_checks
from pcae.core.paths import HarnessPath
from pcae.core.session import read_session_snapshot, write_session_snapshot
from pcae.core.status import check_project_status_coherence
from pcae.core.tasks import (
    close_active_task_by_identifier,
    close_latest_active_task,
    create_task_contract,
    find_latest_active_task,
    finish_active_task,
    read_task_summaries,
    slugify_title,
    validate_task_finish,
)


def init_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )


def commit_all(tmp_path: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )


def test_slugify_title_uses_safe_filename_parts() -> None:
    assert slugify_title("Implement inspect command") == "implement-inspect-command"
    assert slugify_title(" Fix: hooks/install!! ") == "fix-hooks-install"
    assert slugify_title("!!!") == "task"


def test_create_task_contract_writes_markdown_file(tmp_path: Path) -> None:
    created_at = datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc)

    contract = create_task_contract(
        HarnessPath(tmp_path),
        "Implement inspect command",
        created_at=created_at,
    )

    assert contract.task_id == "20260522-1930-implement-inspect-command"
    assert contract.relative_path == Path(
        "tasks/active/20260522-1930-implement-inspect-command.md"
    )

    task_file = tmp_path / contract.relative_path
    assert task_file.is_file()
    content = task_file.read_text(encoding="utf-8")
    assert "## Task ID" in content
    assert "20260522-1930-implement-inspect-command" in content
    assert "## Title" in content
    assert "Implement inspect command" in content
    assert "## Status" in content
    assert "active" in content
    assert "## Mode" in content
    assert "implementation" in content
    assert "## Goal" in content
    assert "## Allowed Files" in content
    assert "## Forbidden Files" in content
    assert "## Allowed Zones" in content
    assert "## Allowed Zones\n\n- TBD" in content
    assert "## Forbidden Zones" in content
    assert "## Forbidden Zones\n\n- TBD" in content
    assert "## Allowed Dependencies\n\n- TBD" in content
    assert "## Forbidden Dependencies\n\n- TBD" in content
    assert "## Enforcement Mode\n\nTBD" in content
    assert "## Forbidden Changes" in content
    assert "## Acceptance Checks" in content
    assert "## Documentation Requirements" in content
    assert "## Created Timestamp" in content
    assert "2026-05-22T19:30:00+00:00" in content


def test_create_task_contract_writes_requested_zones(tmp_path: Path) -> None:
    created_at = datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc)

    contract = create_task_contract(
        HarnessPath(tmp_path),
        "Implement zone task",
        created_at=created_at,
        allowed_zones=("core", "tests"),
        forbidden_zones=("commands",),
    )

    content = (tmp_path / contract.relative_path).read_text(encoding="utf-8")
    assert "## Allowed Zones\n\n- core\n- tests" in content
    assert "## Forbidden Zones\n\n- commands" in content


def test_task_new_command_creates_one_active_task_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "new", "Implement inspect command"])

    output = capsys.readouterr().out
    task_files = list((tmp_path / "tasks" / "active").glob("*.md"))
    assert exit_code == 0
    assert len(task_files) == 1
    assert task_files[0].name.endswith("-implement-inspect-command.md")
    content = task_files[0].read_text(encoding="utf-8")
    assert "## Allowed Zones\n\n- TBD" in content
    assert "## Forbidden Zones\n\n- TBD" in content
    assert "Created task contract: tasks/active/" in output


def test_task_new_command_writes_allowed_and_forbidden_zones(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy_with_zones(tmp_path, ["core", "tests", "commands", "docs"])
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "task",
            "new",
            "Fix check bug",
            "--allowed-zone",
            "core",
            "--allowed-zone",
            "tests",
            "--forbidden-zone",
            "commands",
        ]
    )

    output = capsys.readouterr().out
    task_files = list((tmp_path / "tasks" / "active").glob("*.md"))
    content = task_files[0].read_text(encoding="utf-8")
    assert exit_code == 0
    assert len(task_files) == 1
    assert "## Allowed Zones\n\n- core\n- tests" in content
    assert "## Forbidden Zones\n\n- commands" in content
    assert "Created task contract: tasks/active/" in output


def test_task_new_command_rejects_unknown_zone(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy_with_zones(tmp_path, ["core"])
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "task",
            "new",
            "Fix check bug",
            "--allowed-zone",
            "missing",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Unknown architecture zone: missing" in output
    assert not (tmp_path / "tasks" / "active").exists()


def test_find_latest_active_task_reads_task_identity(tmp_path: Path) -> None:
    created_at = datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc)
    create_task_contract(HarnessPath(tmp_path), "Old task", created_at=created_at)
    create_task_contract(
        HarnessPath(tmp_path),
        "New task",
        created_at=datetime(2026, 5, 22, 19, 31, tzinfo=timezone.utc),
    )

    active_task = find_latest_active_task(HarnessPath(tmp_path))

    assert active_task is not None
    assert active_task.task_id == "20260522-1931-new-task"
    assert active_task.title == "New task"
    assert active_task.status == "active"
    assert active_task.mode == "implementation"
    assert active_task.goal == "TBD"


def test_find_latest_active_task_reads_override_protected_files(tmp_path: Path) -> None:
    task_path = tmp_path / "tasks" / "active" / "20260522-1930-test-task.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        """# Task Contract

## Task ID

20260522-1930-test-task

## Title

Test task

## Allowed Files

- pyproject.toml

## Forbidden Files

- TBD

## Override Protected Files

- pyproject.toml
- *.pem
""",
        encoding="utf-8",
    )

    active_task = find_latest_active_task(HarnessPath(tmp_path))

    assert active_task is not None
    assert active_task.override_protected_files == ("pyproject.toml", "*.pem")


def test_find_latest_active_task_reads_allowed_and_forbidden_zones(
    tmp_path: Path,
) -> None:
    task_path = tmp_path / "tasks" / "active" / "20260522-1930-test-task.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        """# Task Contract

## Task ID

20260522-1930-test-task

## Title

Test task

## Allowed Zones

- core
- tests

## Forbidden Zones

- commands
- config
""",
        encoding="utf-8",
    )

    active_task = find_latest_active_task(HarnessPath(tmp_path))

    assert active_task is not None
    assert active_task.allowed_zones == ("core", "tests")
    assert active_task.forbidden_zones == ("commands", "config")


def test_find_latest_active_task_reads_allowed_and_forbidden_dependencies(
    tmp_path: Path,
) -> None:
    task_path = tmp_path / "tasks" / "active" / "20260522-1930-test-task.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        """# Task Contract

## Task ID

20260522-1930-test-task

## Title

Test task

## Allowed Dependencies

- core -> core
- commands -> core

## Forbidden Dependencies

- core -> commands
""",
        encoding="utf-8",
    )

    active_task = find_latest_active_task(HarnessPath(tmp_path))

    assert active_task is not None
    assert active_task.allowed_dependencies == ("core -> core", "commands -> core")
    assert active_task.forbidden_dependencies == ("core -> commands",)


def test_find_latest_active_task_reads_enforcement_mode(tmp_path: Path) -> None:
    task_path = tmp_path / "tasks" / "active" / "20260522-1930-test-task.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        """# Task Contract

## Task ID

20260522-1930-test-task

## Title

Test task

## Enforcement Mode

strict
""",
        encoding="utf-8",
    )

    active_task = find_latest_active_task(HarnessPath(tmp_path))

    assert active_task is not None
    assert active_task.enforcement_mode == "strict"


def test_close_latest_active_task_marks_done_and_moves_file(tmp_path: Path) -> None:
    created_at = datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc)
    contract = create_task_contract(
        HarnessPath(tmp_path),
        "Implement inspect command",
        created_at=created_at,
    )

    closed_task = close_latest_active_task(HarnessPath(tmp_path))

    assert closed_task is not None
    assert closed_task.task_id == "20260522-1930-implement-inspect-command"
    assert closed_task.title == "Implement inspect command"
    assert not (tmp_path / contract.relative_path).exists()

    done_path = tmp_path / "tasks" / "done" / contract.relative_path.name
    assert done_path.is_file()
    content = done_path.read_text(encoding="utf-8")
    assert "## Status\n\ndone" in content


def test_close_latest_active_task_closes_newest_task(tmp_path: Path) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Old task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "New task",
        created_at=datetime(2026, 5, 22, 19, 31, tzinfo=timezone.utc),
    )

    closed_task = close_latest_active_task(HarnessPath(tmp_path))

    assert closed_task is not None
    assert closed_task.task_id == "20260522-1931-new-task"
    assert (tmp_path / "tasks" / "active" / "20260522-1930-old-task.md").is_file()
    assert (tmp_path / "tasks" / "done" / "20260522-1931-new-task.md").is_file()


def test_close_active_task_by_identifier_closes_specific_task(tmp_path: Path) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Old task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "New task",
        created_at=datetime(2026, 5, 22, 19, 31, tzinfo=timezone.utc),
    )

    closed_task = close_active_task_by_identifier(
        HarnessPath(tmp_path),
        "20260522-1930-old-task",
    )

    assert closed_task is not None
    assert closed_task.task_id == "20260522-1930-old-task"
    assert (tmp_path / "tasks" / "done" / "20260522-1930-old-task.md").is_file()
    assert (tmp_path / "tasks" / "active" / "20260522-1931-new-task.md").is_file()


def test_close_active_task_by_filename_closes_specific_task(tmp_path: Path) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Target task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )

    closed_task = close_active_task_by_identifier(
        HarnessPath(tmp_path),
        "20260522-1930-target-task.md",
    )

    assert closed_task is not None
    assert closed_task.task_id == "20260522-1930-target-task"
    assert (tmp_path / "tasks" / "done" / "20260522-1930-target-task.md").is_file()


def test_close_active_task_by_identifier_returns_none_when_missing(
    tmp_path: Path,
) -> None:
    assert (
        close_active_task_by_identifier(HarnessPath(tmp_path), "missing-task")
        is None
    )


def test_close_latest_active_task_returns_none_without_active_task(tmp_path: Path) -> None:
    assert close_latest_active_task(HarnessPath(tmp_path)) is None


def test_task_close_command_reports_closed_task(tmp_path: Path, monkeypatch, capsys) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Clean up bootstrap task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "close"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Closed task: 20260522-1930-clean-up-bootstrap-task" in output
    assert "Title: Clean up bootstrap task" in output
    assert "Moved to: tasks/done/20260522-1930-clean-up-bootstrap-task.md" in output


def test_task_close_command_accepts_task_id(tmp_path: Path, monkeypatch, capsys) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Specific task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "close", "20260522-1930-specific-task"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Closed task: 20260522-1930-specific-task" in output
    assert (tmp_path / "tasks" / "done" / "20260522-1930-specific-task.md").is_file()


def test_task_close_command_accepts_task_filename(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Specific task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "close", "20260522-1930-specific-task.md"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Closed task: 20260522-1930-specific-task" in output
    assert (tmp_path / "tasks" / "done" / "20260522-1930-specific-task.md").is_file()


def test_task_close_command_reports_missing_identifier(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "close", "missing-task"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No active task contract found for: missing-task" in output


def write_policy_with_zones(root: Path, zones: list[str]) -> None:
    rendered_zones = "\n".join(
        f'{zone} = ["src/{zone}/**"]'
        for zone in zones
    )
    policy_file = root / ".pcae" / "policy.toml"
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        f"""[protected]
patterns = [
  ".env",
]

[architecture.zones]
{rendered_zones}
""",
        encoding="utf-8",
    )


def test_task_close_command_reports_missing_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "close"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No active task contract found in tasks/active/." in output


def test_read_task_summaries_reads_active_and_done_tasks(tmp_path: Path) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Active task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    done_task = create_task_contract(
        HarnessPath(tmp_path),
        "Done task",
        created_at=datetime(2026, 5, 22, 19, 31, tzinfo=timezone.utc),
    )
    close_active_task_by_identifier(HarnessPath(tmp_path), done_task.task_id)

    active_tasks = read_task_summaries(HarnessPath(tmp_path), "active")
    done_tasks = read_task_summaries(HarnessPath(tmp_path), "done")

    assert [task.task_id for task in active_tasks] == ["20260522-1930-active-task"]
    assert [task.task_id for task in done_tasks] == ["20260522-1931-done-task"]
    assert done_tasks[0].status == "done"


def test_task_list_command_shows_active_then_done_tasks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Active task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    done_task = create_task_contract(
        HarnessPath(tmp_path),
        "Done task",
        created_at=datetime(2026, 5, 22, 19, 31, tzinfo=timezone.utc),
    )
    close_active_task_by_identifier(HarnessPath(tmp_path), done_task.task_id)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.index("Active tasks:") < output.index("Done tasks:")
    assert "[active] 20260522-1930-active-task - Active task" in output
    assert "[done] 20260522-1931-done-task - Done task" in output


def test_task_list_command_works_without_done_directory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Active task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Active tasks:" in output
    assert "[active] 20260522-1930-active-task - Active task" in output
    assert "Done tasks:\n  none" in output


def test_task_list_command_reports_no_tasks(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No task contracts found." in output


def test_task_list_command_does_not_modify_files(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Active task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "list"])

    after = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    capsys.readouterr()
    assert exit_code == 0
    assert after == before


def test_task_show_command_displays_latest_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    task_path = tmp_path / "tasks" / "active" / "20260522-1930-show-task.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        """# Task Contract

## Task ID

20260522-1930-show-task

## Title

Show task

## Status

active

## Mode

implementation

## Goal

Display the active task clearly.

## Allowed Files

- src/pcae/core/tasks.py
- tests/test_task.py

## Forbidden Files

- pyproject.toml

## Allowed Zones

- core
- tests

## Forbidden Zones

- config

## Allowed Dependencies

- core -> core
- tests -> *

## Forbidden Dependencies

- core -> commands

## Enforcement Mode

strict

## Acceptance Checks

- pcae task show works
- tests pass

## Documentation Requirements

- Update project memory files.
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "show"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Active task:" in output
    assert "Task ID: 20260522-1930-show-task" in output
    assert "Title: Show task" in output
    assert "Status: active" in output
    assert "Mode: implementation" in output
    assert "Goal: Display the active task clearly." in output
    assert "Allowed files:\n  - src/pcae/core/tasks.py\n  - tests/test_task.py" in output
    assert "Forbidden files:\n  - pyproject.toml" in output
    assert "Allowed zones:\n  - core\n  - tests" in output
    assert "Forbidden zones:\n  - config" in output
    assert "Allowed dependencies:\n  - core -> core\n  - tests -> *" in output
    assert "Forbidden dependencies:\n  - core -> commands" in output
    assert "Enforcement mode: strict" in output
    assert "Acceptance checks:\n  - pcae task show works\n  - tests pass" in output
    assert "Documentation requirements:\n  - Update project memory files." in output


def test_task_show_command_reports_missing_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "show"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No active task contract found in tasks/active/." in output


def test_task_show_command_does_not_modify_files(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Read only task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "show"])

    after = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    capsys.readouterr()
    assert exit_code == 0
    assert after == before


def test_task_update_command_updates_goal_and_preserves_unspecified_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Update task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "update", "--goal", "Ship task updates"])

    output = capsys.readouterr().out
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 0
    assert "Updated task: 20260522-1930-update-task" in output
    assert active_task is not None
    assert active_task.goal == "Ship task updates"
    assert active_task.mode == "implementation"
    assert active_task.allowed_files == ()


def test_task_update_command_replaces_repeatable_allowed_files(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Update task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "task",
            "update",
            "--allowed-file",
            "src/pcae/core/tasks.py",
            "--allowed-file",
            "tests/test_task.py",
        ]
    )

    capsys.readouterr()
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 0
    assert active_task is not None
    assert active_task.allowed_files == (
        "src/pcae/core/tasks.py",
        "tests/test_task.py",
    )


def test_task_update_command_replaces_repeatable_allowed_zones(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy_with_zones(tmp_path, ["core", "tests", "docs"])
    create_task_contract(
        HarnessPath(tmp_path),
        "Update task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "task",
            "update",
            "--allowed-zone",
            "core",
            "--allowed-zone",
            "tests",
        ]
    )

    capsys.readouterr()
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 0
    assert active_task is not None
    assert active_task.allowed_zones == ("core", "tests")


def test_task_update_command_updates_enforcement_mode(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Update task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "update", "--enforcement-mode", "strict"])

    capsys.readouterr()
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 0
    assert active_task is not None
    assert active_task.enforcement_mode == "strict"


def test_task_update_command_replaces_acceptance_checks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Update task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "task",
            "update",
            "--acceptance-check",
            "pcae task show reflects updates",
            "--acceptance-check",
            "tests pass",
        ]
    )

    capsys.readouterr()
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 0
    assert active_task is not None
    assert active_task.acceptance_checks == (
        "pcae task show reflects updates",
        "tests pass",
    )


def test_task_update_command_rejects_invalid_zone(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy_with_zones(tmp_path, ["core"])
    create_task_contract(
        HarnessPath(tmp_path),
        "Update task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "update", "--allowed-zone", "missing"])

    output = capsys.readouterr().out
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 1
    assert "Unknown architecture zone: missing" in output
    assert active_task is not None
    assert active_task.allowed_zones == ()


def test_task_update_command_rejects_invalid_enforcement_mode(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Update task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "update", "--enforcement-mode", "blocking"])

    output = capsys.readouterr().out
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 1
    assert "Invalid enforcement mode: expected advisory, strict, or TBD." in output
    assert active_task is not None
    assert active_task.enforcement_mode == "TBD"


def test_task_update_command_reports_missing_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "update", "--goal", "No task"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No active task contract found in tasks/active/." in output


def test_task_update_command_does_not_modify_done_tasks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    done_task = create_task_contract(
        HarnessPath(tmp_path),
        "Done task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    close_active_task_by_identifier(HarnessPath(tmp_path), done_task.task_id)
    done_path = tmp_path / "tasks" / "done" / f"{done_task.task_id}.md"
    before = done_path.read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "update", "--goal", "No active task"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No active task contract found in tasks/active/." in output
    assert done_path.read_text(encoding="utf-8") == before


def test_task_show_reflects_task_update(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Update task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    update_exit = main(
        [
            "task",
            "update",
            "--goal",
            "Show updated task",
            "--allowed-file",
            "src/pcae/core/tasks.py",
            "--enforcement-mode",
            "advisory",
        ]
    )
    capsys.readouterr()
    show_exit = main(["task", "show"])

    output = capsys.readouterr().out
    assert update_exit == 0
    assert show_exit == 0
    assert "Goal: Show updated task" in output
    assert "Allowed files:\n  - src/pcae/core/tasks.py" in output
    assert "Enforcement mode: advisory" in output


def test_task_pause_command_changes_active_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Pause task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "pause"])

    output = capsys.readouterr().out
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 0
    assert "Paused task: 20260522-1930-pause-task" in output
    assert active_task is not None
    assert active_task.status == "paused"


def test_task_resume_command_changes_paused_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Resume task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    paused_task = find_latest_active_task(HarnessPath(tmp_path))
    assert paused_task is not None
    paused_task.path.write_text(
        paused_task.path.read_text(encoding="utf-8").replace(
            "## Status\n\nactive",
            "## Status\n\npaused",
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "resume"])

    output = capsys.readouterr().out
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 0
    assert "Resumed task: 20260522-1930-resume-task" in output
    assert active_task is not None
    assert active_task.status == "active"


def test_task_complete_command_marks_done_and_moves_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Complete task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "complete"])

    output = capsys.readouterr().out
    done_path = tmp_path / "tasks" / "done" / "20260522-1930-complete-task.md"
    assert exit_code == 0
    assert "Completed task: 20260522-1930-complete-task" in output
    assert "Moved to: tasks/done/20260522-1930-complete-task.md" in output
    assert done_path.is_file()
    assert "## Status\n\ndone" in done_path.read_text(encoding="utf-8")
    assert not (
        tmp_path / "tasks" / "active" / "20260522-1930-complete-task.md"
    ).exists()


def test_task_pause_command_reports_missing_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "pause"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No active task contract found to pause." in output


def test_task_pause_command_rejects_paused_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Already paused",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    main_cwd = tmp_path
    monkeypatch.chdir(main_cwd)
    assert main(["task", "pause"]) == 0
    capsys.readouterr()

    exit_code = main(["task", "pause"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No active task contract found to pause." in output


def test_task_resume_command_rejects_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Already active",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "resume"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No paused task contract found to resume." in output


def test_task_complete_command_rejects_paused_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Paused task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)
    assert main(["task", "pause"]) == 0
    capsys.readouterr()

    exit_code = main(["task", "complete"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No active task contract found to complete." in output
    assert (tmp_path / "tasks" / "active" / "20260522-1930-paused-task.md").is_file()


def test_task_show_reflects_paused_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Pause show task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)
    assert main(["task", "pause"]) == 0
    capsys.readouterr()

    exit_code = main(["task", "show"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Status: paused" in output


def test_task_close_command_still_closes_latest_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Close lifecycle task",
        created_at=datetime(2026, 5, 22, 19, 30, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "close"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Closed task: 20260522-1930-close-lifecycle-task" in output
    assert (
        tmp_path / "tasks" / "done" / "20260522-1930-close-lifecycle-task.md"
    ).is_file()


def test_61h_task_transition_command_creates_next_task_and_refreshes_session(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n"
        "## Current Phase\n\n"
        "Phase 61H: Automated Task Transition.\n\n"
        "## Next Roadmap\n\n"
        "- 61I: Session Bootstrap Automation\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "TODO.md").write_text(
        "# TODO\n\n"
        "## Pending\n\n"
        "- 61I: Session Bootstrap Automation\n",
        encoding="utf-8",
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "Automated Task Transition (Phase 61H)",
        created_at=datetime(2026, 6, 7, 14, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "transition"])

    output = capsys.readouterr().out
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    session = read_session_snapshot(HarnessPath(tmp_path))
    assert exit_code == 0
    assert "Task transition complete." in output
    assert "Completed task: 20260607-1400-automated-task-transition-phase-61h" in output
    assert active_task is not None
    assert active_task.title == "61I: Session Bootstrap Automation"
    assert active_task.enforcement_mode == "strict"
    assert ".pcae/session.json" not in active_task.allowed_files
    assert "tasks/active/**" in active_task.allowed_files
    assert "tasks/done/**" in active_task.allowed_files
    assert session is not None
    assert session.data["active_task"]["title"] == "61I: Session Bootstrap Automation"
    assert session.data["current_objective"] == "61I: Session Bootstrap Automation"
    assert (
        tmp_path
        / "tasks"
        / "done"
        / "20260607-1400-automated-task-transition-phase-61h.md"
    ).is_file()
    assert (
        "Automated Task Transition (Phase 61H) "
        "(20260607-1400-automated-task-transition-phase-61h)"
        in (tmp_path / "tasks" / "DONE.md").read_text(encoding="utf-8")
    )
    assert "61I: Session Bootstrap Automation" not in (
        tmp_path / "tasks" / "TODO.md"
    ).read_text(encoding="utf-8")
    assert "Phase 61I: Session Bootstrap Automation." in (
        tmp_path / "PROJECT_STATUS.md"
    ).read_text(encoding="utf-8")
    assert "Transitioned active task from Automated Task Transition (Phase 61H)" in (
        tmp_path / "CHANGELOG.md"
    ).read_text(encoding="utf-8")
    assert check_project_status_coherence(HarnessPath(tmp_path)).coherent is True
    assert run_checks(HarnessPath(tmp_path)).passed is True


def test_61h_task_transition_command_supports_explicit_next_title_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n"
        "## Current Phase\n\n"
        "Phase 61H: Automated Task Transition.\n\n"
        "## Next Roadmap\n\n"
        "- 61I: Explicit Next Task\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "TODO.md").write_text(
        "# TODO\n\n"
        "## Pending\n\n"
        "- 61I: Explicit Next Task\n",
        encoding="utf-8",
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "Current phase task",
        created_at=datetime(2026, 6, 7, 14, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["task", "transition", "--next", "61I: Explicit Next Task", "--json"]
    )

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["status_coherence_passed"] is True
    assert data["health_status"] == "healthy"
    assert data["check_passed"] is True
    assert data["next_active_task"]["title"] == "61I: Explicit Next Task"
    assert data["completed_task"]["title"] == "Current phase task"
    assert data["session_path"] == ".pcae/session.json"


def test_61h_task_transition_command_blocks_on_stale_session(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Current phase task",
        created_at=datetime(2026, 6, 7, 14, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    session_path = tmp_path / ".pcae" / "session.json"
    data = json.loads(session_path.read_text(encoding="utf-8"))
    data["active_task"] = {"id": "different-task", "title": "Different task"}
    session_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "transition", "--next", "61I: Explicit Next Task"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Task transition blocked." in output
    assert "Session active task does not match current active task." in output
    assert (
        tmp_path / "tasks" / "active" / "20260607-1400-current-phase-task.md"
    ).is_file()
    assert not (
        tmp_path / "tasks" / "done" / "20260607-1400-current-phase-task.md"
    ).exists()


def test_61h_task_transition_scopes_dirty_source_into_next_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n"
        "## Current Phase\n\n"
        "Phase 61H: Automated Task Transition.\n\n"
        "## Next Roadmap\n\n"
        "- 61I: Explicit Next Task\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "TODO.md").write_text(
        "# TODO\n\n"
        "## Pending\n\n"
        "- 61I: Explicit Next Task\n",
        encoding="utf-8",
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "Current phase task",
        created_at=datetime(2026, 6, 7, 14, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    dirty_source = tmp_path / "src" / "dirty_feature.py"
    dirty_source.parent.mkdir(parents=True, exist_ok=True)
    dirty_source.write_text("before\n", encoding="utf-8")
    commit_all(tmp_path, "baseline")
    dirty_source.write_text("after\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "transition", "--next", "61I: Explicit Next Task"])

    capsys.readouterr()
    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert exit_code == 0
    assert active_task is not None
    assert "src/dirty_feature.py" in active_task.allowed_files
    assert run_checks(HarnessPath(tmp_path)).passed is True


# ---------------------------------------------------------------------------
# Phase 62A.1: Task Transition Idempotency Hardening tests
# ---------------------------------------------------------------------------

from pcae.core.tasks import list_task_slugs_in_dir, _slug_from_task_stem  # noqa: E402


def test_62a1_transition_blocks_same_title(tmp_path: Path, monkeypatch, capsys) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "62A controlled runtime execution pilot",
        created_at=datetime(2026, 6, 7, 20, 23, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["task", "transition", "--next", "62A controlled runtime execution pilot"]
    )

    capsys.readouterr()
    assert exit_code == 1
    active_files = list((tmp_path / "tasks" / "active").glob("*.md"))
    assert len(active_files) == 1, "No new active task should have been created"


def test_62a1_transition_blocks_same_title_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "62A controlled runtime execution pilot",
        created_at=datetime(2026, 6, 7, 20, 23, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["task", "transition", "--next", "62A controlled runtime execution pilot"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "same as the current active task" in output
    assert not (
        tmp_path / "tasks" / "done" / "20260607-2023-62a-controlled-runtime-execution-pilot.md"
    ).exists()


def test_62a1_transition_blocks_completed_title(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    done_dir = tmp_path / "tasks" / "done"
    done_dir.mkdir(parents=True, exist_ok=True)
    (done_dir / "20260607-2023-62a-controlled-runtime-execution-pilot.md").write_text(
        "# Task Contract\n\n## Status\n\ndone\n", encoding="utf-8"
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "62A.1 task transition idempotency hardening",
        created_at=datetime(2026, 6, 7, 20, 40, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["task", "transition", "--next", "62A controlled runtime execution pilot"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "matches a completed task" in output
    active_files = list((tmp_path / "tasks" / "active").glob("*.md"))
    assert len(active_files) == 1, "No new duplicate active task should have been created"


def test_62a1_transition_blocks_existing_active_duplicate(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    # Earlier task (will be the alphabetically-last active task after write_session_snapshot)
    create_task_contract(
        HarnessPath(tmp_path),
        "62C governance cleanup",
        created_at=datetime(2026, 6, 7, 20, 50, tzinfo=timezone.utc),
    )
    # Earlier existing active task with a title we'll try to transition to
    (tmp_path / "tasks" / "active" / "20260607-2040-62b-runtime-output-capture.md").write_text(
        "# Task Contract\n\n## Status\n\nactive\n", encoding="utf-8"
    )
    write_session_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        ["task", "transition", "--next", "62B runtime output capture"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "already exists" in output


def test_62a1_slug_helpers() -> None:
    assert _slug_from_task_stem("20260607-2023-62a-pilot") == "62a-pilot"
    assert _slug_from_task_stem("20260101-1200-my-task-title") == "my-task-title"
    assert _slug_from_task_stem("nodash") == "nodash"


def test_62a1_list_task_slugs_in_dir(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks" / "active"
    task_dir.mkdir(parents=True)
    (task_dir / "20260607-2023-62a-pilot.md").write_text("", encoding="utf-8")
    (task_dir / "20260607-2033-62b-output-capture.md").write_text("", encoding="utf-8")
    slugs = list_task_slugs_in_dir(task_dir)
    assert "62a-pilot" in slugs
    assert "62b-output-capture" in slugs
    assert len(slugs) == 2


# ---------------------------------------------------------------------------
# Phase 61I: Handoff State Refresh tests
# ---------------------------------------------------------------------------


def test_61i_handoff_state_refresh_overview_fields() -> None:
    data = build_handoff_state_refresh()
    overview = data["handoff_state_refresh_overview"]
    assert overview["phase"] == "61I"
    assert overview["title"] == "Handoff State Refresh"
    assert overview["domain_count"] == 10
    assert overview["signal_count"] == 10
    assert overview["handoff_update_allowed"] is True
    assert overview["execution_allowed"] is False
    assert overview["human_review_required"] is True


def test_61i_handoff_state_refresh_models() -> None:
    data = build_handoff_state_refresh()
    assert data["signal_model"]["model_name"] == "HandoffStateRefreshSignal"
    assert data["signal_model"]["field_count"] == 8
    assert data["assessment_model"]["model_name"] == "HandoffStateRefreshAssessment"
    assert data["assessment_model"]["field_count"] == 7
    assert data["summary_model"]["model_name"] == "HandoffStateRefreshSummary"
    assert data["summary_model"]["field_count"] == 9


def test_61i_handoff_state_refresh_signals_have_required_fields() -> None:
    data = build_handoff_state_refresh()
    for signal in data["signals"]:
        assert "signal_id" in signal
        assert "handoff_id" in signal
        assert "refresh_domain" in signal
        assert "signal_type" in signal
        assert "severity" in signal
        assert "detected_state" in signal
        assert "expected_state" in signal
        assert signal["human_review_required"] is True


def test_61i_handoff_state_refresh_all_domains_covered() -> None:
    data = build_handoff_state_refresh()
    domains = {s["refresh_domain"] for s in data["signals"]}
    expected = {
        "active_task_summary_refresh",
        "completed_phase_summary_refresh",
        "next_phase_summary_refresh",
        "roadmap_position_refresh",
        "governance_status_refresh",
        "runtime_status_refresh",
        "bootstrap_profile_refresh",
        "bootstrap_validation_refresh",
        "handoff_freshness_refresh",
        "agent_context_refresh",
    }
    assert domains == expected


def test_61i_handoff_state_refresh_bootstrap_modernization() -> None:
    data = build_handoff_state_refresh()
    bm = data["bootstrap_modernization"]
    assert bm["modern_test_command"] == "python -m pytest -n auto"
    assert bm["battery_conscious_command"] == "python -m pytest -n 4"
    assert len(bm["retained_uses"]) >= 3
    contexts = {r["context"] for r in bm["retained_uses"]}
    assert "release verification workflows" in contexts
    assert "debugging workflows" in contexts
    assert "compatibility workflows" in contexts


def test_61i_handoff_state_refresh_governance_boundaries() -> None:
    data = build_handoff_state_refresh()
    boundaries = data["governance_boundaries"]
    assert boundaries["handoff_update_allowed"] is True
    assert boundaries["execution_allowed"] is False
    assert boundaries["human_review_required"] is True
    assert "commit" in boundaries["may_not"]
    assert "invoke runtimes" in boundaries["may_not"]
    assert "refresh handoff state" in boundaries["may"]


def test_61i_handoff_state_refresh_advisory() -> None:
    data = build_handoff_state_refresh()
    assert data["advisory"] == HANDOFF_STATE_REFRESH_ADVISORY


def test_61i_handoff_state_refresh_sample_assessment_fields() -> None:
    data = build_handoff_state_refresh()
    assessment = data["sample_assessment"]
    assert "assessment_id" in assessment
    assert "signal_count" in assessment
    assert "blocker_count" in assessment
    assert "warning_count" in assessment
    assert "refresh_status" in assessment
    assert assessment["handoff_update_allowed"] is True
    assert assessment["human_review_required"] is True


def test_61i_handoff_state_refresh_sample_summary_fields() -> None:
    data = build_handoff_state_refresh()
    summary = data["sample_summary"]
    assert "summary_id" in summary
    assert "assessment_id" in summary
    assert "domain_count" in summary
    assert summary["handoff_update_allowed"] is True
    assert summary["human_review_required"] is True


def test_61i_cli_handoff_state_refresh_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["handoff-state-refresh"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Handoff state refresh" in output
    assert "Refresh domains:" in output
    assert "Bootstrap modernization:" in output


def test_61i_cli_handoff_state_refresh_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["handoff-state-refresh", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert "handoff_state_refresh_overview" in parsed
    assert "signal_model" in parsed
    assert "assessment_model" in parsed
    assert "summary_model" in parsed
    assert "bootstrap_modernization" in parsed
    assert parsed["handoff_state_refresh_overview"]["phase"] == "61I"


# --- Phase 70A: pcae task finish ---


def test_70a_task_finish_moves_task_and_updates_memory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    (tmp_path / "tasks" / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Finish target\n", encoding="utf-8"
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "Finish target",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "finish"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Finished task: 20260617-2000-finish-target" in output
    assert "Moved to: tasks/done/20260617-2000-finish-target.md" in output
    done_path = tmp_path / "tasks" / "done" / "20260617-2000-finish-target.md"
    assert done_path.is_file()
    assert "## Status\n\ndone" in done_path.read_text(encoding="utf-8")
    assert not (tmp_path / "tasks" / "active" / "20260617-2000-finish-target.md").exists()
    done_md = (tmp_path / "tasks" / "DONE.md").read_text(encoding="utf-8")
    assert "Finish target (20260617-2000-finish-target)" in done_md
    todo_md = (tmp_path / "tasks" / "TODO.md").read_text(encoding="utf-8")
    assert "Finish target" not in todo_md
    session = read_session_snapshot(HarnessPath(tmp_path))
    assert session is not None


def test_70a_task_finish_refuses_when_no_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tasks" / "active").mkdir(parents=True)

    exit_code = main(["task", "finish"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Task finish blocked." in output
    assert "No active task contract found to finish." in output


def test_70a_task_finish_refuses_when_checks_fail(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Blocked task",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "finish"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Task finish blocked." in output


def test_70a_task_finish_skip_checks_bypasses_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Skip checks task",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "finish", "--skip-checks"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Finished task: 20260617-2000-skip-checks-task" in output
    assert (tmp_path / "tasks" / "done" / "20260617-2000-skip-checks-task.md").is_file()


def test_70a_task_finish_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "JSON output task",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "finish", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert parsed["finished"] is True
    assert parsed["task_id"] == "20260617-2000-json-output-task"
    assert parsed["title"] == "JSON output task"
    assert "tasks/done/20260617-2000-json-output-task.md" in parsed["moved_to"]
    assert isinstance(parsed["updated_files"], list)
    assert isinstance(parsed["warnings"], list)


def test_70a_task_finish_json_output_on_refusal(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tasks" / "active").mkdir(parents=True)

    exit_code = main(["task", "finish", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    parsed = json.loads(output)
    assert parsed["finished"] is False
    assert len(parsed["blockers"]) > 0
    assert parsed["task_id"] is None


def test_70a_task_finish_session_refresh(
    tmp_path: Path, monkeypatch
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Session refresh task",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)

    result = finish_active_task(root, skip_checks=True)

    assert result.completed_task.task_id == "20260617-2000-session-refresh-task"
    session = read_session_snapshot(root)
    assert session is not None
    assert Path(".pcae/session.json") in result.updated_files


def test_70a_validate_task_finish_blocks_duplicate_done(
    tmp_path: Path, monkeypatch
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Duplicate done",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    done_dir = tmp_path / "tasks" / "done"
    done_dir.mkdir(parents=True, exist_ok=True)
    (done_dir / "20260617-2000-duplicate-done.md").write_text(
        "# already done", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    root = HarnessPath(tmp_path)

    validation = validate_task_finish(root, skip_checks=True)

    assert not validation.safe_to_finish
    assert any("already exists" in b for b in validation.blockers)


def test_70a_task_complete_backward_compatibility(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Backward compat",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "complete"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Completed task: 20260617-2000-backward-compat" in output
    assert (tmp_path / "tasks" / "done" / "20260617-2000-backward-compat.md").is_file()
    assert not (tmp_path / "tasks" / "DONE.md").exists()


# --- Phase 70B: pcae doctor task-memory ---


def test_70b_doctor_task_memory_clean(tmp_path: Path, monkeypatch, capsys) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n- My task (20260617-2000-my-task)\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    create_task_contract(
        HarnessPath(tmp_path),
        "My task",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Task memory: clean" in output


def test_70b_doctor_task_memory_detects_multiple_active_tasks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "First task",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "Second task",
        created_at=datetime(2026, 6, 17, 21, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Found 2 active task files" in output


def test_70b_doctor_task_memory_detects_session_mismatch(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path),
        "Current task",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    session_path = tmp_path / ".pcae" / "session.json"
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(
        json.dumps({"active_task": {"id": "old-task-id", "title": "Old task"}}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Session references task 'old-task-id'" in output


def test_70b_doctor_task_memory_detects_missing_done_md_entries(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "Completed task",
        created_at=datetime(2026, 6, 17, 20, 0, tzinfo=timezone.utc),
    )
    from pcae.core.tasks import close_active_task, read_active_task

    active_path = tmp_path / "tasks" / "active" / "20260617-2000-completed-task.md"
    close_active_task(read_active_task(active_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "not listed in tasks/DONE.md" in output


def test_70b_doctor_task_memory_detects_todo_references_completed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Already done task\n", encoding="utf-8"
    )
    done_path = tmp_path / "tasks" / "done" / "20260617-2000-already-done-task.md"
    done_path.write_text(
        "# Task Contract\n\n## Task ID\n\n20260617-2000-already-done-task\n\n"
        "## Title\n\nAlready done task\n\n## Status\n\ndone\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "TODO.md still references completed task" in output


def test_70b_doctor_task_memory_detects_done_status_in_active(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "20260617-2000-stuck-task.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260617-2000-stuck-task\n\n"
        "## Title\n\nStuck task\n\n## Status\n\ndone\n\n## Mode\n\nimplementation\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "has status 'done' but is still in tasks/active/" in output


def test_70b_doctor_task_memory_detects_active_status_in_done(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    done_dir = tmp_path / "tasks" / "done"
    done_dir.mkdir(parents=True, exist_ok=True)
    (done_dir / "20260617-2000-wrong-folder.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260617-2000-wrong-folder\n\n"
        "## Title\n\nWrong folder task\n\n## Status\n\nactive\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "has status 'active' but is in tasks/done/" in output


def test_70b_doctor_task_memory_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "active").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "active" / "20260617-2000-task-a.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260617-2000-task-a\n\n"
        "## Title\n\nTask A\n\n## Status\n\ndone\n\n## Mode\n\nimplementation\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    parsed = json.loads(output)
    assert parsed["clean"] is False
    assert len(parsed["findings"]) >= 1
    assert parsed["findings"][0]["severity"] == "error"
    assert parsed["findings"][0]["check"] == "done_status_in_active_folder"


# --- Phase 70D: pcae task new ergonomics ---


def test_70d_task_new_with_all_flags(tmp_path: Path, monkeypatch, capsys) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "task", "new", "Full contract task",
        "--goal", "Implement the feature",
        "--mode", "implementation",
        "--allowed-file", "src/app.py",
        "--allowed-file", "tests/test_app.py",
        "--forbidden-file", "secrets.env",
        "--enforcement-mode", "advisory",
        "--acceptance-check", "pcae health passes",
        "--acceptance-check", "python -m pytest passes",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Created task contract:" in output

    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert active_task is not None
    assert active_task.title == "Full contract task"
    assert active_task.goal == "Implement the feature"
    assert active_task.mode == "implementation"
    assert "src/app.py" in active_task.allowed_files
    assert "tests/test_app.py" in active_task.allowed_files
    assert "secrets.env" in active_task.forbidden_files
    assert active_task.enforcement_mode == "advisory"
    assert "pcae health passes" in active_task.acceptance_checks
    assert "python -m pytest passes" in active_task.acceptance_checks


def test_70d_task_new_without_flags_preserves_defaults(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "new", "Simple task"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Created task contract:" in output

    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert active_task is not None
    assert active_task.title == "Simple task"
    assert active_task.goal == "TBD"
    assert active_task.mode == "implementation"
    assert active_task.enforcement_mode == "TBD"


def test_70d_task_new_refreshes_session(tmp_path: Path, monkeypatch) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    main(["task", "new", "Session refresh task", "--goal", "Test session"])

    session = read_session_snapshot(HarnessPath(tmp_path))
    assert session is not None
    assert session.data["active_task"]["title"] == "Session refresh task"


def test_70d_task_update_unchanged(tmp_path: Path, monkeypatch, capsys) -> None:
    create_task_contract(
        HarnessPath(tmp_path),
        "Update target",
        created_at=datetime(2026, 6, 18, 5, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "task", "update",
        "--goal", "Updated goal",
        "--allowed-file", "new_file.py",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Updated task:" in output

    active_task = find_latest_active_task(HarnessPath(tmp_path))
    assert active_task is not None
    assert active_task.goal == "Updated goal"
    assert "new_file.py" in active_task.allowed_files


# --- Phase 70E: pcae task finish --commit ---


def test_70e_task_finish_commit_creates_commit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "Commit test task",
        created_at=datetime(2026, 6, 18, 5, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "finish", "--skip-checks", "--commit", "Complete the commit test task"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Finished task: 20260618-0500-commit-test-task" in output
    assert "Committed:" in output
    result = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    assert "Complete the commit test task" in result.stdout
    result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == ""


def test_70e_task_finish_commit_refuses_dirty_tree(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "Dirty tree task",
        created_at=datetime(2026, 6, 18, 5, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    (tmp_path / "unrelated.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "finish", "--commit", "Should not commit"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "pre-existing change" in output
    assert find_latest_active_task(HarnessPath(tmp_path)) is not None


def test_70e_task_finish_commit_json_includes_hash(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    create_task_contract(
        HarnessPath(tmp_path),
        "JSON commit task",
        created_at=datetime(2026, 6, 18, 5, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "finish", "--skip-checks", "--commit", "JSON commit", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert parsed["finished"] is True
    assert parsed["committed"] is True
    assert parsed["commit_hash"] is not None
    assert parsed["commit_message"] == "JSON commit"


def test_70e_task_finish_without_commit_unchanged(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "No commit task",
        created_at=datetime(2026, 6, 18, 5, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "finish", "--skip-checks"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Finished task:" in output
    assert "Committed:" not in output


def test_70e_task_finish_commit_dirty_tree_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path),
        "JSON dirty task",
        created_at=datetime(2026, 6, 18, 5, 0, tzinfo=timezone.utc),
    )
    write_session_snapshot(HarnessPath(tmp_path))
    commit_all(tmp_path, "init")
    (tmp_path / "extra.txt").write_text("dirty", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "finish", "--commit", "Nope", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 1
    parsed = json.loads(output)
    assert parsed["finished"] is False
    assert parsed["committed"] is False
    assert len(parsed["blockers"]) > 0


# --- Phase 70I: pcae doctor task-memory --fix ---


def test_70i_fix_repairs_done_file_missing_from_done_md(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    (tmp_path / "tasks" / "done" / "20260618-0500-missing-task.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260618-0500-missing-task\n\n"
        "## Title\n\nMissing task\n\n## Status\n\ndone\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory", "--fix"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "appended_to_done_md" in output
    done_md = (tmp_path / "tasks" / "DONE.md").read_text(encoding="utf-8")
    assert "Missing task (20260618-0500-missing-task)" in done_md


def test_70i_fix_repairs_todo_references_completed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n- Stale task (20260618-0500-stale)\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Stale task\n- Other task\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "done" / "20260618-0500-stale.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260618-0500-stale\n\n"
        "## Title\n\nStale task\n\n## Status\n\ndone\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory", "--fix"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "removed_from_todo_md" in output
    todo_md = (tmp_path / "tasks" / "TODO.md").read_text(encoding="utf-8")
    assert "Stale task" not in todo_md
    assert "Other task" in todo_md


def test_70i_fix_repairs_done_status_in_active(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "20260618-0500-stuck.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260618-0500-stuck\n\n"
        "## Title\n\nStuck task\n\n## Status\n\ndone\n\n## Mode\n\nimplementation\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory", "--fix"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "moved_to_done" in output
    assert not (active_dir / "20260618-0500-stuck.md").exists()
    assert (tmp_path / "tasks" / "done" / "20260618-0500-stuck.md").is_file()


def test_70i_fix_dry_run_does_not_mutate(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    (tmp_path / "tasks" / "done" / "20260618-0500-dry-task.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260618-0500-dry-task\n\n"
        "## Title\n\nDry task\n\n## Status\n\ndone\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory", "--fix", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "would_repair" in output
    done_md = (tmp_path / "tasks" / "DONE.md").read_text(encoding="utf-8")
    assert "Dry task" not in done_md


def test_70i_fix_skips_unrepairable_findings(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "done" / "20260618-0500-wrong.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260618-0500-wrong\n\n"
        "## Title\n\nWrong folder\n\n## Status\n\nactive\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory", "--fix"])

    output = capsys.readouterr().out
    assert "Skipped (requires human action):" in output
    assert "status 'active' but is in tasks/done/" in output


def test_70i_fix_json_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    (tmp_path / "tasks" / "done" / "20260618-0500-json-fix.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260618-0500-json-fix\n\n"
        "## Title\n\nJSON fix task\n\n## Status\n\ndone\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory", "--fix", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert "pre_findings" in parsed
    assert "repairs" in parsed
    assert "skipped" in parsed
    assert "post_findings" in parsed
    assert len(parsed["repairs"]) == 1
    assert parsed["repairs"][0]["action"] == "appended_to_done_md"
    assert len(parsed["post_findings"]) == 0


def test_70i_fix_is_idempotent(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    (tmp_path / "tasks" / "done" / "20260618-0500-idem.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260618-0500-idem\n\n"
        "## Title\n\nIdempotent task\n\n## Status\n\ndone\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    main(["doctor", "task-memory", "--fix"])
    capsys.readouterr()

    exit_code = main(["doctor", "task-memory", "--fix"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Post-fix: clean" in output


def test_70i_doctor_without_fix_unchanged(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# Done\n\n## Completed\n\n", encoding="utf-8"
    )
    (tmp_path / "tasks" / "done" / "20260618-0500-noop.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260618-0500-noop\n\n"
        "## Title\n\nNoop task\n\n## Status\n\ndone\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["doctor", "task-memory"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "issues detected" in output
    done_md = (tmp_path / "tasks" / "DONE.md").read_text(encoding="utf-8")
    assert "Noop task" not in done_md
