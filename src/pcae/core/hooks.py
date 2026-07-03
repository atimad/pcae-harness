from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import subprocess

from pcae.core.paths import HarnessPath

# The canonical value PCAE configures `core.hooksPath` to. Hook scripts
# live directly in this tracked directory, so there is no separate
# "installed copy" to go stale — once `core.hooksPath` points here,
# Git always runs whatever is currently checked out.
HOOKS_PATH_VALUE = ".githooks"

# Hook files PCAE expects to find in `.githooks/` (Phase 108E adds
# `pre-push` alongside the original `pre-commit`).
EXPECTED_HOOK_FILES: tuple[str, ...] = ("pre-commit", "pre-push")

HOOK_STATUS_INSTALLED = "installed"
HOOK_STATUS_NOT_A_GIT_REPO = "not_a_git_repo"
HOOK_STATUS_HOOKS_PATH_MISSING = "hooks_path_missing"
HOOK_STATUS_HOOKS_PATH_INCORRECT = "hooks_path_incorrect"
HOOK_STATUS_HOOK_FILES_MISSING = "hook_files_missing"
HOOK_STATUS_HOOK_FILES_NOT_EXECUTABLE = "hook_files_not_executable"


@dataclass(frozen=True)
class HookInstallResult:
    installed: bool
    message: str


@dataclass(frozen=True)
class HookStatus:
    """Diagnosis of local Git hook governance (Phase 108E).

    `healthy` is True only for `HOOK_STATUS_INSTALLED` — every other
    status means a fresh clone or an existing checkout is not fully
    protected by local governance yet.
    """

    status: str
    git_repo: bool
    hooks_path_configured: str | None
    hooks_path_expected: str
    missing_hook_files: tuple[str, ...]
    non_executable_hook_files: tuple[str, ...]
    healthy: bool
    recommended_remediation: tuple[str, ...]


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
        ["git", "config", "core.hooksPath", HOOKS_PATH_VALUE],
        cwd=root.path,
        check=True,
    )

    message = f"Installed PCAE Git hooks: core.hooksPath is {HOOKS_PATH_VALUE}"
    pre_push = root.join(Path(".githooks") / "pre-push")
    if not pre_push.is_file():
        message += (
            " (note: .githooks/pre-push not found — pre-push governance "
            "checks will not run until it is added; run `pcae init --force` "
            "to create it, then re-run `pcae hooks install`)"
        )
    return HookInstallResult(installed=True, message=message)


def is_git_repo(root: HarnessPath) -> bool:
    completed = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root.path,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def _read_hooks_path(root: HarnessPath) -> str | None:
    completed = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=root.path,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def diagnose_hooks(root: HarnessPath) -> HookStatus:
    """Read-only diagnosis of local Git hook governance state.

    Never modifies repository state, git config, or any file. Used by
    both `pcae hooks status` and `pcae doctor hooks`.
    """
    if not is_git_repo(root):
        return HookStatus(
            status=HOOK_STATUS_NOT_A_GIT_REPO,
            git_repo=False,
            hooks_path_configured=None,
            hooks_path_expected=HOOKS_PATH_VALUE,
            missing_hook_files=(),
            non_executable_hook_files=(),
            healthy=False,
            recommended_remediation=(
                "Run this command from inside a Git repository.",
            ),
        )

    configured = _read_hooks_path(root)

    missing: list[str] = []
    non_executable: list[str] = []
    for name in EXPECTED_HOOK_FILES:
        hook_path = root.join(Path(".githooks") / name)
        if not hook_path.is_file():
            missing.append(name)
        elif not os.access(hook_path, os.X_OK):
            non_executable.append(name)

    if configured is None:
        status = HOOK_STATUS_HOOKS_PATH_MISSING
    elif configured != HOOKS_PATH_VALUE:
        status = HOOK_STATUS_HOOKS_PATH_INCORRECT
    elif missing:
        status = HOOK_STATUS_HOOK_FILES_MISSING
    elif non_executable:
        status = HOOK_STATUS_HOOK_FILES_NOT_EXECUTABLE
    else:
        status = HOOK_STATUS_INSTALLED

    remediation: tuple[str, ...]
    if status == HOOK_STATUS_HOOKS_PATH_MISSING:
        remediation = ("Run: pcae hooks install",)
    elif status == HOOK_STATUS_HOOKS_PATH_INCORRECT:
        remediation = (
            f"core.hooksPath is set to {configured!r}, not "
            f"{HOOKS_PATH_VALUE!r}. Run: git config core.hooksPath "
            f"{HOOKS_PATH_VALUE}",
        )
    elif status == HOOK_STATUS_HOOK_FILES_MISSING:
        remediation = (
            f"Missing hook file(s): {', '.join(missing)}. "
            "Run: pcae init --force, then pcae hooks install",
        )
    elif status == HOOK_STATUS_HOOK_FILES_NOT_EXECUTABLE:
        chmod_targets = " ".join(f".githooks/{name}" for name in non_executable)
        remediation = (
            f"Hook file(s) not executable: {', '.join(non_executable)}. "
            f"Run: chmod +x {chmod_targets}",
        )
    else:
        remediation = ()

    return HookStatus(
        status=status,
        git_repo=True,
        hooks_path_configured=configured,
        hooks_path_expected=HOOKS_PATH_VALUE,
        missing_hook_files=tuple(missing),
        non_executable_hook_files=tuple(non_executable),
        healthy=status == HOOK_STATUS_INSTALLED,
        recommended_remediation=remediation,
    )
