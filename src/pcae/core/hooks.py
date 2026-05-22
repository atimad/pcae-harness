from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from pcae.core.paths import HarnessPath


@dataclass(frozen=True)
class HookInstallResult:
    installed: bool
    message: str


def install_hooks(root: HarnessPath) -> HookInstallResult:
    if not is_git_repo(root):
        return HookInstallResult(
            installed=False,
            message="Cannot install hooks: current directory is not inside a Git repository.",
        )

    pre_commit = root.join(Path(".githooks") / "pre-commit")
    if not pre_commit.is_file():
        return HookInstallResult(
            installed=False,
            message="Cannot install hooks: .githooks/pre-commit is missing.",
        )

    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        cwd=root.path,
        check=True,
    )
    return HookInstallResult(
        installed=True,
        message="Installed PCAE Git hooks: core.hooksPath is .githooks",
    )


def is_git_repo(root: HarnessPath) -> bool:
    completed = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root.path,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0 and completed.stdout.strip() == "true"
