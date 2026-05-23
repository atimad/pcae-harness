from __future__ import annotations

import os
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.templates import INIT_TEMPLATES


def test_init_command_creates_pre_commit_hook(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["init"])

    output = capsys.readouterr().out
    pre_commit = tmp_path / ".githooks" / "pre-commit"
    assert exit_code == 0
    assert pre_commit.is_file()
    assert os.access(pre_commit, os.X_OK)
    assert "Created:" in output
    assert "  .githooks/pre-commit" in output


def test_init_creates_required_files(tmp_path: Path) -> None:
    results = init_harness(HarnessPath(tmp_path))

    assert all(result.created for result in results)
    for relative_path in INIT_TEMPLATES:
        assert (tmp_path / relative_path).is_file()


def test_init_is_idempotent_and_does_not_overwrite(tmp_path: Path) -> None:
    existing = tmp_path / "AGENTS.md"
    existing.write_text("custom agent notes\n", encoding="utf-8")

    first_results = init_harness(HarnessPath(tmp_path))
    second_results = init_harness(HarnessPath(tmp_path))

    assert existing.read_text(encoding="utf-8") == "custom agent notes\n"
    assert any(
        result.relative_path == Path("AGENTS.md") and not result.created
        for result in first_results
    )
    assert all(not result.created for result in second_results)


def test_init_creates_cross_platform_check_scripts(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))

    shell_check = tmp_path / "scripts" / "check-docs-updated.sh"
    pre_commit = tmp_path / ".githooks" / "pre-commit"

    assert shell_check.is_file()
    assert (tmp_path / "scripts" / "check-docs-updated.ps1").is_file()
    assert pre_commit.is_file()
    assert os.access(shell_check, os.X_OK)
    assert os.access(pre_commit, os.X_OK)


def test_init_creates_default_policy_file(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))

    policy_file = tmp_path / ".pcae" / "policy.toml"

    assert policy_file.is_file()
    content = policy_file.read_text(encoding="utf-8")
    assert "[protected]" in content
    assert '  ".env",' in content
    assert '  "pyproject.toml",' in content
