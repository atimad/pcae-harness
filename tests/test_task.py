from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pcae.cli import main
from pcae.core.paths import HarnessPath
from pcae.core.tasks import (
    close_active_task_by_identifier,
    close_latest_active_task,
    create_task_contract,
    find_latest_active_task,
    read_task_summaries,
    slugify_title,
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
