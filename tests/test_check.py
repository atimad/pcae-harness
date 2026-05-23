from __future__ import annotations

from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.check import run_checks
from pcae.core.paths import HarnessPath


def test_check_detects_missing_active_task(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    commit_baseline(tmp_path)

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(result, "No active task contract found")


def test_check_detects_out_of_scope_file_changes(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / "src" / "allowed.py", "print('allowed')\n")
    write_file(tmp_path / "src" / "other.py", "print('other')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "other.py", "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "src/other.py: Changed file is outside active task scope "
        "for task 20260522-1930-test-task; no allowed-file pattern matched.",
    )
    assert result.active_task_id == "20260522-1930-test-task"
    assert result.active_task_title == "Test task"


def test_check_detects_source_changes_without_documentation_updates(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / "src" / "allowed.py", "print('allowed')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "allowed.py", "print('changed')\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(result, "Source files changed without documentation file updates.")


def test_check_detects_forbidden_file_changes(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/allowed.py"],
        forbidden_files=["pyproject.toml"],
    )
    write_file(tmp_path / "src" / "allowed.py", "print('allowed')\n")
    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'demo'\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'changed'\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(result, "pyproject.toml: Forbidden file changed.")


def test_check_command_passes_when_changes_are_in_scope_and_documented(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / "src" / "allowed.py", "print('allowed')\n")
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    write_file(tmp_path / "src" / "allowed.py", "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Active task: 20260522-1930-test-task" in output
    assert "Title: Test task" in output
    assert "PCAE check passed." in output


def test_check_command_reports_active_task_and_violating_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / "src" / "other.py", "print('other')\n")
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    write_file(tmp_path / "src" / "other.py", "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Active task: 20260522-1930-test-task" in output
    assert "Title: Test task" in output
    assert "src/other.py: Changed file is outside active task scope" in output
    assert "for task 20260522-1930-test-task" in output


def test_check_detects_missing_required_files(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    commit_baseline(tmp_path)

    (tmp_path / "AGENTS.md").unlink()

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(result, "AGENTS.md: Missing required PCAE file.")


def test_check_uses_newest_active_task(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/old.py"],
        task_id="20260522-1930-old-task",
        title="Old task",
    )
    write_task(
        tmp_path,
        allowed_files=["src/new.py"],
        task_id="20260522-1931-new-task",
        title="New task",
    )
    write_file(tmp_path / "src" / "new.py", "print('new')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "new.py", "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed
    assert result.active_task_id == "20260522-1931-new-task"
    assert result.active_task_title == "New task"


def test_check_supports_direct_directory_wildcard_scope(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/pcae/core/*"])
    write_file(tmp_path / "src" / "pcae" / "core" / "allowed.py", "print('ok')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "allowed.py", "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed


def test_check_direct_directory_wildcard_does_not_match_nested_files(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/pcae/core/*"])
    nested = tmp_path / "src" / "pcae" / "core" / "nested" / "file.py"
    write_file(nested, "print('nested')\n")
    commit_baseline(tmp_path)

    write_file(nested, "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(result, "src/pcae/core/nested/file.py:")


def test_check_supports_recursive_directory_wildcard_scope(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/pcae/commands/**"])
    nested = tmp_path / "src" / "pcae" / "commands" / "nested" / "file.py"
    write_file(nested, "print('nested')\n")
    commit_baseline(tmp_path)

    write_file(nested, "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed


def test_check_supports_basename_wildcard_scope(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["*.py"])
    write_file(tmp_path / "src" / "pcae" / "core" / "allowed.py", "print('ok')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "allowed.py", "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed


def write_task(
    root: Path,
    allowed_files: list[str],
    forbidden_files: list[str] | None = None,
    task_id: str = "20260522-1930-test-task",
    title: str = "Test task",
) -> None:
    forbidden_files = forbidden_files or []
    task_path = root / "tasks" / "active" / f"{task_id}.md"
    allowed = "\n".join(f"- {path}" for path in allowed_files)
    forbidden = "\n".join(f"- {path}" for path in forbidden_files) or "- TBD"
    write_file(
        task_path,
        f"""# Task Contract

## Task ID

{task_id}

## Title

{title}

## Status

active

## Mode

implementation

## Goal

Test check behavior.

## Allowed Files

{allowed}

## Forbidden Files

{forbidden}

## Forbidden Changes

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update docs.

## Created Timestamp

2026-05-22T19:30:00+00:00
""",
    )


def commit_baseline(root: Path) -> None:
    run_git(root, "init")
    run_git(root, "config", "user.email", "test@example.com")
    run_git(root, "config", "user.name", "Test User")
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


def has_violation(result, text: str) -> bool:
    return any(text in violation.text for violation in result.violations)
