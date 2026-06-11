from __future__ import annotations

import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.agent import acquire_agent_lock
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
        allowed_files=["pyproject.toml"],
        forbidden_files=["pyproject.toml"],
    )
    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'demo'\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'changed'\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "pyproject.toml: Forbidden file changed "
        "for task 20260522-1930-test-task (Test task); "
        "matched forbidden pattern 'pyproject.toml'.",
    )
    assert not has_violation(result, "outside active task scope")


def test_check_command_passes_when_changes_are_in_scope_and_documented(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / "src" / "allowed.py", "print('allowed')\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
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


def test_check_json_command_reports_passed_result(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / "src" / "allowed.py", "print('allowed')\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    write_file(tmp_path / "src" / "allowed.py", "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    exit_code = main(["check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["status"] == "passed"
    assert data["active_task"] == {
        "id": "20260522-1930-test-task",
        "title": "Test task",
    }
    assert data["agent_lock"] == {
        "age_seconds": None,
        "agent_id": None,
        "locked": False,
        "stale": False,
        "stale_after_seconds": 14400,
    }
    assert data["git_status"]["changed_file_count"] == 2
    assert data["session_continuity"] == "verified"
    assert data["violations"] == []
    assert data["warnings"] == []
    assert data["dependency_warnings"] == []
    assert data["enforcement_mode"] == "advisory"


def test_check_json_command_reports_agent_lock(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / "src" / "allowed.py", "print('allowed')\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    run_git(tmp_path, "init")
    run_git(tmp_path, "config", "user.email", "test@example.com")
    run_git(tmp_path, "config", "user.name", "Test User")
    acquire_agent_lock(HarnessPath(tmp_path), "agent-a")
    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-m", "baseline")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["agent_lock"]["locked"] is True
    assert data["agent_lock"]["stale"] is False
    assert data["agent_lock"]["agent_id"] == "agent-a"
    assert isinstance(data["agent_lock"]["age_seconds"], int)
    assert data["agent_lock"]["stale_after_seconds"] == 14400


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


def test_check_json_command_reports_failed_result(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / "src" / "other.py", "print('other')\n")
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    write_file(tmp_path / "src" / "other.py", "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    exit_code = main(["check", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["status"] == "failed"
    assert data["active_task"]["id"] == "20260522-1930-test-task"
    assert data["session_continuity"] == "missing"
    assert any(
        "src/other.py: Changed file is outside active task scope" in violation
        for violation in data["violations"]
    )
    assert any("Session snapshot missing" in violation for violation in data["violations"])


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
    write_session(
        tmp_path,
        task_id="20260522-1931-new-task",
        title="New task",
    )
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
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
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
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(nested, "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed


def test_check_supports_basename_wildcard_scope(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["*.py"])
    write_file(tmp_path / "src" / "pcae" / "core" / "allowed.py", "print('ok')\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "allowed.py", "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed


def test_check_forbidden_direct_directory_wildcard_scope(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/*"],
        forbidden_files=["src/pcae/core/*"],
    )
    target = tmp_path / "src" / "pcae" / "core" / "protected.py"
    write_file(target, "print('protected')\n")
    commit_baseline(tmp_path)

    write_file(target, "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "src/pcae/core/protected.py: Forbidden file changed "
        "for task 20260522-1930-test-task (Test task); "
        "matched forbidden pattern 'src/pcae/core/*'.",
    )


def test_check_forbidden_direct_directory_wildcard_ignores_nested_files(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/**"],
        forbidden_files=["src/pcae/core/*"],
    )
    target = tmp_path / "src" / "pcae" / "core" / "nested" / "allowed.py"
    write_file(target, "print('nested')\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(target, "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed


def test_check_forbidden_recursive_directory_wildcard_scope(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/commands/**"],
        forbidden_files=["src/pcae/commands/**"],
    )
    target = tmp_path / "src" / "pcae" / "commands" / "nested" / "protected.py"
    write_file(target, "print('protected')\n")
    commit_baseline(tmp_path)

    write_file(target, "print('changed')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "src/pcae/commands/nested/protected.py: Forbidden file changed "
        "for task 20260522-1930-test-task (Test task); "
        "matched forbidden pattern 'src/pcae/commands/**'.",
    )


def test_check_forbidden_basename_wildcard_scope(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/protected.toml"],
        forbidden_files=["*.toml"],
    )
    target = tmp_path / "src" / "pcae" / "core" / "protected.toml"
    write_file(target, "name = 'protected'\n")
    commit_baseline(tmp_path)

    write_file(target, "name = 'changed'\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "src/pcae/core/protected.toml: Forbidden file changed "
        "for task 20260522-1930-test-task (Test task); "
        "matched forbidden pattern '*.toml'.",
    )


def test_check_global_protected_exact_file_fails(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["pyproject.toml"])
    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'demo'\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'changed'\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "pyproject.toml: Protected file changed "
        "for task 20260522-1930-test-task (Test task); "
        "matched protected pattern 'pyproject.toml'. "
        "To allow this intentionally, list the file or pattern under "
        "'Override Protected Files'.",
    )


def test_check_reads_protected_patterns_from_policy_file(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["custom.lock"])
    write_file(tmp_path / ".pcae" / "policy.toml", policy_with_patterns(["custom.lock"]))
    write_file(tmp_path / "custom.lock", "locked\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "custom.lock", "changed\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "custom.lock: Protected file changed "
        "for task 20260522-1930-test-task (Test task); "
        "matched protected pattern 'custom.lock'.",
    )


def test_check_missing_policy_file_falls_back_to_default_protection(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    (tmp_path / ".pcae" / "policy.toml").unlink()
    write_task(tmp_path, allowed_files=["pyproject.toml"])
    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'demo'\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'changed'\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(result, "matched protected pattern 'pyproject.toml'.")


def test_check_fails_when_policy_file_is_invalid(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / ".pcae" / "policy.toml", "[protected]\npatterns = [42]\n")
    commit_baseline(tmp_path)

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        ".pcae/policy.toml: Invalid policy: every protected pattern "
        "must be a non-empty string.",
    )


def test_check_command_invalid_policy_returns_nonzero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / ".pcae" / "policy.toml", "[protected]\npatterns = [42]\n")
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "PCAE check found violations:" in output
    assert (
        ".pcae/policy.toml: Invalid policy: every protected pattern "
        "must be a non-empty string."
    ) in output


def test_check_global_protected_wildcard_file_fails(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["secrets/private.pem"])
    write_file(tmp_path / "secrets" / "private.pem", "secret\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "secrets" / "private.pem", "changed\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "secrets/private.pem: Protected file changed "
        "for task 20260522-1930-test-task (Test task); "
        "matched protected pattern '*.pem'.",
    )


def test_check_global_protected_directory_fails(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["node_modules/pkg/index.js"])
    write_file(tmp_path / "node_modules" / "pkg" / "index.js", "module.exports = 1;\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "node_modules" / "pkg" / "index.js", "module.exports = 2;\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "node_modules/pkg/index.js: Protected file changed "
        "for task 20260522-1930-test-task (Test task); "
        "matched protected pattern 'node_modules/**'.",
    )


def test_check_override_protected_files_allows_protected_change(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["pyproject.toml"],
        override_protected_files=["pyproject.toml"],
    )
    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'demo'\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'changed'\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed


def test_check_forbidden_files_win_over_protected_override(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["pyproject.toml"],
        forbidden_files=["pyproject.toml"],
        override_protected_files=["pyproject.toml"],
    )
    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'demo'\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'changed'\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(result, "matched forbidden pattern 'pyproject.toml'.")
    assert not has_violation(result, "matched protected pattern 'pyproject.toml'.")


def test_check_warns_when_session_snapshot_is_missing(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    commit_baseline(tmp_path)

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(result, "Session snapshot missing at .pcae/session.json.")


def test_check_passes_when_session_active_task_matches(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed
    assert has_info(result, "Session continuity verified.")


def test_check_fails_when_session_active_task_differs(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_session(
        tmp_path,
        task_id="20260522-1931-other-task",
        title="Other task",
    )
    commit_baseline(tmp_path)

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        ".pcae/session.json: Session active task does not match current active task. "
        "Run `pcae session write`.",
    )


def test_check_command_mismatched_session_returns_nonzero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_session(
        tmp_path,
        task_id="20260522-1931-other-task",
        title="Other task",
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "PCAE check found violations:" in output
    assert (
        ".pcae/session.json: Session active task does not match current active task. "
        "Run `pcae session write`."
    ) in output


def test_check_fails_when_session_json_is_invalid(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / ".pcae" / "session.json", "{invalid\n")
    commit_baseline(tmp_path)

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(result, ".pcae/session.json: Invalid session JSON:")


def test_check_command_prints_missing_session_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Session snapshot missing at .pcae/session.json." in output
    assert "PCAE check found violations:" in output


def test_check_command_prints_session_continuity_info(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "info: Session continuity verified." in output
    assert "warning: Session active task matches current active task." not in output
    assert "PCAE check passed." in output


def test_check_classifies_changed_files_by_architecture_zone(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=[
            "src/pcae/core/changed.py",
            "tests/test_changed.py",
            "CHANGELOG.md",
            "misc.txt",
        ],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_zones(
            {
                "core": ["src/pcae/core/**"],
                "tests": ["tests/**"],
                "docs": ["*.md"],
            }
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "tests" / "test_changed.py", "def test_old(): pass\n")
    write_file(tmp_path / "misc.txt", "old\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('new')\n")
    write_file(tmp_path / "tests" / "test_changed.py", "def test_new(): pass\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")
    write_file(tmp_path / "misc.txt", "new\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed
    assert zone_counts(result) == {
        "core": 1,
        "tests": 1,
        "docs": 1,
        "unclassified": 1,
    }


def test_check_classifies_common_project_files_without_unclassified(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=[
            "src/pcae/cli.py",
            "scripts/check-docs-updated.sh",
            ".githooks/pre-commit",
            "pyproject.toml",
            ".pcae/session.json",
            ".pcae/policy.toml",
        ],
        override_protected_files=[
            "pyproject.toml",
            ".pcae/session.json",
            ".pcae/policy.toml",
        ],
    )
    write_file(tmp_path / "src" / "pcae" / "cli.py", "print('old')\n")
    write_file(tmp_path / "scripts" / "check-docs-updated.sh", "old\n")
    write_file(tmp_path / ".githooks" / "pre-commit", "old\n")
    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'old'\n")
    write_file(tmp_path / ".pcae" / "session.json", "{}\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "cli.py", "print('new')\n")
    write_file(tmp_path / "scripts" / "check-docs-updated.sh", "new\n")
    write_file(tmp_path / ".githooks" / "pre-commit", "new\n")
    write_file(tmp_path / "pyproject.toml", "[project]\nname = 'new'\n")
    write_file(tmp_path / ".pcae" / "session.json", '{"updated": true}\n')
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        default_policy_text() + "# changed for zone classification\n",
    )

    result = run_checks(HarnessPath(tmp_path))

    counts = zone_counts(result)
    assert "unclassified" not in counts
    assert counts["cli"] == 1
    assert counts["scripts"] == 1
    assert counts["hooks"] == 1
    assert counts["package"] == 1
    assert counts["session"] == 1
    assert counts["policy"] == 1


def test_check_omits_architecture_zone_summary_when_clean(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"])
    write_file(tmp_path / ".pcae" / "policy.toml", policy_with_architecture_zones({"core": ["src/**"]}))
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed
    assert result.architecture_zones_touched == ()


def test_check_command_prints_architecture_zone_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md", "misc.txt"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_zones({"core": ["src/pcae/core/**"]}),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "misc.txt", "old\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('new')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")
    write_file(tmp_path / "misc.txt", "new\n")

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Architecture zones touched:" in output
    assert "  core: 1 files" in output
    assert "  unclassified: 2 files" in output
    assert "PCAE check passed." in output


def test_check_command_prints_architecture_dependency_warnings(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=[
            "src/pcae/core/changed.py",
            "CHANGELOG.md",
        ],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Architecture dependency warnings:" in output
    assert (
        "src/pcae/core/changed.py: core -> commands is not allowed by policy"
        in output
    )
    assert "PCAE check passed." in output


def test_check_command_advisory_architecture_warning_does_not_fail(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=[
            "src/pcae/core/changed.py",
            "CHANGELOG.md",
        ],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
            enforcement_mode="advisory",
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Architecture dependency warnings:" in output
    assert (
        "src/pcae/core/changed.py: core -> commands is not allowed by policy"
        in output
    )
    assert "PCAE check passed." in output


def test_check_command_policy_strict_architecture_warning_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=[
            "src/pcae/core/changed.py",
            "CHANGELOG.md",
        ],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
            enforcement_mode="strict",
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    exit_code = main(["check"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Architecture dependency warnings:" in output
    assert "PCAE check found violations:" in output
    assert (
        "src/pcae/core/changed.py: core -> commands is not allowed by policy"
        in output
    )


def test_check_strict_architecture_mode_fails_on_dependency_warning(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=[
            "src/pcae/core/changed.py",
            "CHANGELOG.md",
        ],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
            enforcement_mode="strict",
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    commit_baseline(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "src/pcae/core/changed.py: core -> commands is not allowed by policy",
    )
    assert any(
        "src/pcae/core/changed.py: core -> commands is not allowed by policy"
        in warning.text
        for warning in result.architecture_dependency_warnings
    )


def test_check_missing_architecture_enforcement_defaults_to_advisory(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=[
            "src/pcae/core/changed.py",
            "CHANGELOG.md",
        ],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed
    assert result.architecture_dependency_warnings
    assert not has_violation(result, "is not allowed by policy")


def test_check_task_allowed_dependency_overrides_repo_rules(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        allowed_dependencies=["core -> commands"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed
    assert result.architecture_dependency_warnings == ()


def test_check_task_forbidden_dependency_wins_over_allowed(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        allowed_dependencies=["core -> commands"],
        forbidden_dependencies=["core -> commands"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
            enforcement_mode="strict",
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    commit_baseline(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "src/pcae/core/changed.py: core -> commands is not allowed by policy",
    )


def test_check_task_forbidden_dependency_fails_with_task_strict_mode(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        allowed_dependencies=["core -> commands"],
        forbidden_dependencies=["core -> commands"],
        enforcement_mode="strict",
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
            enforcement_mode="advisory",
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    commit_baseline(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert result.architecture_enforcement_mode == "strict"
    assert has_violation(
        result,
        "src/pcae/core/changed.py: core -> commands is not allowed by policy",
    )


def test_check_task_advisory_enforcement_overrides_policy_strict(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        enforcement_mode="advisory",
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
            enforcement_mode="strict",
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed
    assert result.architecture_enforcement_mode == "advisory"
    assert result.architecture_dependency_warnings


def test_check_task_strict_enforcement_overrides_policy_advisory(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        enforcement_mode="strict",
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            },
            rules={
                "core": ["core"],
                "commands": ["core", "commands"],
                "docs": ["*"],
            },
            enforcement_mode="advisory",
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    commit_baseline(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert result.architecture_enforcement_mode == "strict"
    assert has_violation(
        result,
        "src/pcae/core/changed.py: core -> commands is not allowed by policy",
    )


def test_check_invalid_task_enforcement_mode_fails_clearly(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        enforcement_mode="blocking",
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={"core": ["src/pcae/core/**"], "docs": ["*.md"]},
            rules={"core": ["core"], "docs": ["*"]},
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('new')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "Invalid task Enforcement Mode: 'blocking'. Expected 'advisory' or 'strict'.",
    )


def test_check_invalid_task_dependency_format_fails_clearly(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        allowed_dependencies=["core commands"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={"core": ["src/pcae/core/**"], "docs": ["*.md"]},
            rules={"core": ["core"], "docs": ["*"]},
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('new')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "Invalid dependency format in task Allowed Dependencies: "
        "'core commands'. Expected 'source -> target'.",
    )


def test_check_unknown_task_dependency_zone_fails_clearly(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        forbidden_dependencies=["core -> missing"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={"core": ["src/pcae/core/**"], "docs": ["*.md"]},
            rules={"core": ["core"], "docs": ["*"]},
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('new')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "Unknown architecture zone 'missing' listed in task Forbidden Dependencies.",
    )


def test_check_allowed_task_zone_passes(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        allowed_zones=["core", "docs"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_zones(
            {
                "core": ["src/pcae/core/**"],
                "docs": ["*.md"],
            }
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('new')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed


def test_check_disallowed_task_zone_fails(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/commands/changed.py", "CHANGELOG.md"],
        allowed_zones=["core", "docs"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_zones(
            {
                "core": ["src/pcae/core/**"],
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            }
        ),
    )
    write_file(
        tmp_path / "src" / "pcae" / "commands" / "changed.py",
        "print('old')\n",
    )
    commit_baseline(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "commands" / "changed.py",
        "print('new')\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "src/pcae/commands/changed.py: Changed file touches architecture zone "
        "'commands' outside Allowed Zones",
    )


def test_check_forbidden_task_zone_fails(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/commands/changed.py", "CHANGELOG.md"],
        allowed_zones=["commands", "docs"],
        forbidden_zones=["commands"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_zones(
            {
                "commands": ["src/pcae/commands/**"],
                "docs": ["*.md"],
            }
        ),
    )
    write_file(
        tmp_path / "src" / "pcae" / "commands" / "changed.py",
        "print('old')\n",
    )
    commit_baseline(tmp_path)

    write_file(
        tmp_path / "src" / "pcae" / "commands" / "changed.py",
        "print('new')\n",
    )
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "src/pcae/commands/changed.py: Changed file touches forbidden architecture "
        "zone 'commands'",
    )
    assert not has_violation(result, "outside Allowed Zones")


def test_check_unclassified_zone_requires_allowed_entry(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["misc.txt"],
        allowed_zones=["core"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_zones({"core": ["src/pcae/core/**"]}),
    )
    write_file(tmp_path / "misc.txt", "old\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "misc.txt", "new\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "misc.txt: Changed file touches architecture zone 'unclassified' outside "
        "Allowed Zones",
    )


def test_check_unclassified_forbidden_zone_fails(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["misc.txt"],
        forbidden_zones=["unclassified"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_zones({"core": ["src/pcae/core/**"]}),
    )
    write_file(tmp_path / "misc.txt", "old\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "misc.txt", "new\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "misc.txt: Changed file touches forbidden architecture zone 'unclassified'",
    )


def test_check_unknown_task_zone_fails_clearly(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=["src/pcae/core/changed.py", "CHANGELOG.md"],
        allowed_zones=["unknown"],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_zones(
            {
                "core": ["src/pcae/core/**"],
                "docs": ["*.md"],
            }
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('new')\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert not result.passed
    assert has_violation(
        result,
        "Unknown architecture zone 'unknown' listed in task Allowed Zones.",
    )


def test_check_warns_when_changed_python_file_cannot_be_parsed(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(
        tmp_path,
        allowed_files=[
            "src/pcae/core/changed.py",
            "CHANGELOG.md",
        ],
    )
    write_file(
        tmp_path / ".pcae" / "policy.toml",
        policy_with_architecture_rules(
            zones={"core": ["src/pcae/core/**"]},
            rules={"core": ["core"]},
        ),
    )
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "print('old')\n")
    write_session(
        tmp_path,
        task_id="20260522-1930-test-task",
        title="Test task",
    )
    commit_baseline(tmp_path)

    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "def broken(:\n")
    write_file(tmp_path / "CHANGELOG.md", "# Changelog\n\nUpdated docs.\n")

    result = run_checks(HarnessPath(tmp_path))

    assert result.passed
    assert has_warning(
        result,
        "src/pcae/core/changed.py: Could not parse Python imports:",
    )


def write_task(
    root: Path,
    allowed_files: list[str],
    forbidden_files: list[str] | None = None,
    override_protected_files: list[str] | None = None,
    allowed_zones: list[str] | None = None,
    forbidden_zones: list[str] | None = None,
    allowed_dependencies: list[str] | None = None,
    forbidden_dependencies: list[str] | None = None,
    enforcement_mode: str | None = None,
    task_id: str = "20260522-1930-test-task",
    title: str = "Test task",
) -> None:
    forbidden_files = forbidden_files or []
    override_protected_files = override_protected_files or []
    allowed_zones = allowed_zones or []
    forbidden_zones = forbidden_zones or []
    allowed_dependencies = allowed_dependencies or []
    forbidden_dependencies = forbidden_dependencies or []
    task_path = root / "tasks" / "active" / f"{task_id}.md"
    allowed = "\n".join(f"- {path}" for path in allowed_files)
    forbidden = "\n".join(f"- {path}" for path in forbidden_files) or "- TBD"
    overrides = "\n".join(f"- {path}" for path in override_protected_files) or "- TBD"
    allowed_zone_items = "\n".join(f"- {zone}" for zone in allowed_zones) or "- TBD"
    forbidden_zone_items = "\n".join(f"- {zone}" for zone in forbidden_zones) or "- TBD"
    allowed_dependency_items = (
        "\n".join(f"- {dependency}" for dependency in allowed_dependencies) or "- TBD"
    )
    forbidden_dependency_items = (
        "\n".join(f"- {dependency}" for dependency in forbidden_dependencies) or "- TBD"
    )
    rendered_enforcement_mode = enforcement_mode or "TBD"
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

## Override Protected Files

{overrides}

## Allowed Zones

{allowed_zone_items}

## Forbidden Zones

{forbidden_zone_items}

## Allowed Dependencies

{allowed_dependency_items}

## Forbidden Dependencies

{forbidden_dependency_items}

## Enforcement Mode

{rendered_enforcement_mode}

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


def write_session(root: Path, task_id: str, title: str) -> None:
    write_file(
        root / ".pcae" / "session.json",
        f"""{{
  "active_task": {{
    "id": "{task_id}",
    "title": "{title}"
  }},
  "architectural_notes": [],
  "blockers": [],
  "current_objective": "",
  "git": {{
    "branch": "main",
    "changed_files": [],
    "status_summary": "clean"
  }},
  "last_completed_step": "",
  "next_recommended_step": "",
  "timestamp": "2026-05-23T08:00:00+00:00",
  "warnings": []
}}
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


def has_warning(result, text: str) -> bool:
    return any(text in warning.text for warning in result.warnings)


def has_info(result, text: str) -> bool:
    return any(text in info.text for info in result.infos)


def zone_counts(result) -> dict[str, int]:
    return {
        zone.name: zone.file_count
        for zone in result.architecture_zones_touched
    }


def policy_with_patterns(patterns: list[str]) -> str:
    rendered_patterns = "\n".join(f'  "{pattern}",' for pattern in patterns)
    return f"""[protected]
patterns = [
{rendered_patterns}
]
"""


def policy_with_architecture_zones(zones: dict[str, list[str]]) -> str:
    rendered_zones = "\n".join(
        f"{name} = [{', '.join(render_string(pattern) for pattern in patterns)}]"
        for name, patterns in zones.items()
    )
    return f"""[protected]
patterns = [
  ".env",
]

[architecture.zones]
{rendered_zones}
"""


def default_policy_text() -> str:
    return """[protected]
patterns = [
  ".git/**",
  ".env",
  ".env.*",
  "*.pem",
  "*.key",
  "*.p12",
  "*.pfx",
  "**/__pycache__/**",
  ".venv/**",
  "venv/**",
  "node_modules/**",
  "pyproject.toml",
  "poetry.lock",
  "package-lock.json",
  "pnpm-lock.yaml",
  "yarn.lock",
  "Cargo.toml",
  "Cargo.lock",
]

[architecture.zones]
core = ["src/pcae/core/**"]
commands = ["src/pcae/commands/**"]
cli = ["src/pcae/cli.py", "src/pcae/__main__.py", "src/pcae/__init__.py"]
tests = ["tests/**"]
docs = ["docs/**", "*.md"]
tasks = ["tasks/**"]
scripts = ["scripts/**"]
hooks = [".githooks/**"]
package = ["pyproject.toml"]
session = [".pcae/session.json"]
policy = [".pcae/policy.toml"]
config = [".pcae/**", "pyproject.toml"]

[architecture.rules]
core = ["core"]
commands = ["core", "commands"]
cli = ["core", "commands", "cli"]
tests = ["*"]
docs = ["*"]
tasks = ["*"]
scripts = ["*"]
hooks = ["hooks"]
package = ["package"]
session = ["session"]
policy = ["policy"]
config = ["config"]

[architecture.enforcement]
mode = "advisory"
"""


def policy_with_architecture_rules(
    zones: dict[str, list[str]],
    rules: dict[str, list[str]],
    enforcement_mode: str | None = None,
) -> str:
    rendered_zones = "\n".join(
        f"{name} = [{', '.join(render_string(pattern) for pattern in patterns)}]"
        for name, patterns in zones.items()
    )
    rendered_rules = "\n".join(
        f"{name} = [{', '.join(render_string(target) for target in targets)}]"
        for name, targets in rules.items()
    )
    enforcement = ""
    if enforcement_mode is not None:
        enforcement = f"""
[architecture.enforcement]
mode = "{enforcement_mode}"
"""
    return f"""[protected]
patterns = [
  ".env",
]

[architecture.zones]
{rendered_zones}

[architecture.rules]
{rendered_rules}
{enforcement}"""


def render_string(value: str) -> str:
    return f'"{value}"'


# ---------------------------------------------------------------------------
# Phase 62E — check_active_task_phase_alignment regression tests
# ---------------------------------------------------------------------------

from pcae.core.check import check_active_task_phase_alignment  # noqa: E402
from pcae.core.tasks import read_active_task  # noqa: E402


def _write_project_status(root: Path, phase_line: str) -> None:
    content = f"# Project Status\n\n## Current Phase\n\n{phase_line}\n"
    write_file(root / "PROJECT_STATUS.md", content)


def _write_task_with_phase(root: Path, phase_title: str) -> "ActiveTask":
    task_path = root / "tasks" / "active" / "20260608-0000-test.md"
    write_file(
        task_path,
        f"# Task Contract\n\n## Task ID\n\n20260608-0000-test\n\n## Title\n\n{phase_title}\n\n## Status\n\nactive\n",
    )
    return read_active_task(task_path)


def test_62e_check_passes_when_phases_aligned(tmp_path: Path) -> None:
    _write_project_status(tmp_path, "Phase 62E: Task State Alignment — active.")
    task = _write_task_with_phase(tmp_path, "62E active task state repair")
    violations = check_active_task_phase_alignment(HarnessPath(tmp_path), task)
    assert violations == ()


def test_62e_check_fails_when_phases_differ(tmp_path: Path) -> None:
    _write_project_status(tmp_path, "Phase 62D: Runtime Review Workflow — complete.")
    task = _write_task_with_phase(tmp_path, "62B runtime output capture")
    violations = check_active_task_phase_alignment(HarnessPath(tmp_path), task)
    assert len(violations) == 1
    assert "62B" in violations[0].text
    assert "62D" in violations[0].text
    assert "pcae task transition" in violations[0].text


def test_62e_check_skips_when_project_status_missing(tmp_path: Path) -> None:
    task = _write_task_with_phase(tmp_path, "62E active task state repair")
    violations = check_active_task_phase_alignment(HarnessPath(tmp_path), task)
    assert violations == ()


def test_62e_check_skips_when_phase_code_unextractable(tmp_path: Path) -> None:
    _write_project_status(tmp_path, "Work in progress.")
    task = _write_task_with_phase(tmp_path, "no phase code here")
    violations = check_active_task_phase_alignment(HarnessPath(tmp_path), task)
    assert violations == ()


def test_62e_check_case_insensitive_comparison(tmp_path: Path) -> None:
    _write_project_status(tmp_path, "Phase 62e: Some task — active.")
    task = _write_task_with_phase(tmp_path, "62E active task state repair")
    violations = check_active_task_phase_alignment(HarnessPath(tmp_path), task)
    assert violations == ()


def test_65j_implemented_task_does_not_require_activation_alignment(
    tmp_path: Path,
) -> None:
    _write_project_status(
        tmp_path,
        "Phase 65J: Strategic Decision Continuity.",
    )
    task = _write_task_with_phase(tmp_path, "65J Strategic Decision Continuity")
    violations = check_active_task_phase_alignment(HarnessPath(tmp_path), task)
    assert violations == ()


def test_62e_check_integrated_in_run_checks(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    write_task(tmp_path, allowed_files=["src/allowed.py"], title="62B runtime output capture")
    _write_project_status(tmp_path, "Phase 62D: Runtime Review Workflow — complete.")
    write_file(tmp_path / "src" / "allowed.py", "x = 1\n")
    commit_baseline(tmp_path)
    result = run_checks(HarnessPath(tmp_path))
    assert has_violation(result, "does not match PROJECT_STATUS.md current phase")
