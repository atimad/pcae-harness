from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pcae.cli import main
from pcae.core.paths import HarnessPath
from pcae.core.tasks import (
    close_latest_active_task,
    create_task_contract,
    find_latest_active_task,
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
    assert "## Forbidden Changes" in content
    assert "## Acceptance Checks" in content
    assert "## Documentation Requirements" in content
    assert "## Created Timestamp" in content
    assert "2026-05-22T19:30:00+00:00" in content


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
    assert "Created task contract: tasks/active/" in output


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


def test_task_close_command_reports_missing_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["task", "close"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "No active task contract found in tasks/active/." in output
