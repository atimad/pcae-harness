from __future__ import annotations

from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.core.hooks import install_hooks
from pcae.core.paths import HarnessPath


def test_hooks_install_configures_git_hooks_path(tmp_path: Path) -> None:
    init_git_repo(tmp_path)
    write_pre_commit_hook(tmp_path)

    result = install_hooks(HarnessPath(tmp_path))

    assert result.installed
    assert read_git_config(tmp_path, "core.hooksPath") == ".githooks"


def test_hooks_install_requires_git_repo(tmp_path: Path) -> None:
    write_pre_commit_hook(tmp_path)

    result = install_hooks(HarnessPath(tmp_path))

    assert not result.installed
    assert "not inside a Git repository" in result.message


def test_hooks_install_requires_pre_commit_hook(tmp_path: Path) -> None:
    init_git_repo(tmp_path)

    result = install_hooks(HarnessPath(tmp_path))

    assert not result.installed
    assert ".githooks/pre-commit is missing" in result.message


def test_hooks_install_command_prints_success(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_git_repo(tmp_path)
    write_pre_commit_hook(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["hooks", "install"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "core.hooksPath is .githooks" in output
    assert read_git_config(tmp_path, "core.hooksPath") == ".githooks"


def test_pre_commit_hook_calls_pcae_check() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pre_commit = repo_root / ".githooks" / "pre-commit"

    content = pre_commit.read_text(encoding="utf-8")

    assert "pcae check" in content


def init_git_repo(root: Path) -> None:
    run_git(root, "init")


def write_pre_commit_hook(root: Path) -> None:
    hook_path = root / ".githooks" / "pre-commit"
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(
        "#!/usr/bin/env sh\nset -eu\n\npcae check\n",
        encoding="utf-8",
    )


def read_git_config(root: Path, key: str) -> str:
    completed = subprocess.run(
        ["git", "config", key],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
