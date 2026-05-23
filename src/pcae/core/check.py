from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.git_status import GitChange, read_git_changes
from pcae.core.manifest import MANIFEST_ENTRIES
from pcae.core.paths import HarnessPath
from pcae.core.tasks import find_latest_active_task


DOCUMENTATION_PATHS = {
    Path("AGENTS.md"),
    Path("CHANGELOG.md"),
    Path("PROJECT_STATUS.md"),
    Path("README.md"),
    Path("tasks/TODO.md"),
    Path("tasks/DONE.md"),
    Path("tasks/DECISIONS.md"),
}

SOURCE_PREFIXES = ("src/", "tests/")


@dataclass(frozen=True)
class CheckMessage:
    reason: str
    path: Path | None = None

    @property
    def text(self) -> str:
        if self.path is None:
            return self.reason
        return f"{self.path.as_posix()}: {self.reason}"


@dataclass(frozen=True)
class CheckResult:
    violations: tuple[CheckMessage, ...]
    warnings: tuple[CheckMessage, ...]
    active_task_id: str | None = None
    active_task_title: str | None = None

    @property
    def passed(self) -> bool:
        return not self.violations


def run_checks(root: HarnessPath) -> CheckResult:
    violations: list[CheckMessage] = []
    warnings: list[CheckMessage] = []

    for entry in MANIFEST_ENTRIES:
        if not root.join(entry.relative_path).is_file():
            violations.append(
                CheckMessage(
                    reason="Missing required PCAE file.",
                    path=entry.relative_path,
                )
            )

    active_task = find_latest_active_task(root)
    if active_task is None:
        violations.append(
            CheckMessage("No active task contract found in tasks/active/.")
        )

    changes = read_git_changes(root)
    changed_paths = tuple(change.path for change in changes)

    if active_task is not None:
        violations.extend(check_forbidden_changes(changes, active_task.forbidden_files))
        violations.extend(check_allowed_scope(changes, active_task.allowed_files))

    if source_changed(changed_paths) and not documentation_changed(changed_paths):
        violations.append(
            CheckMessage("Source files changed without documentation file updates.")
        )

    return CheckResult(
        violations=tuple(violations),
        warnings=tuple(warnings),
        active_task_id=active_task.task_id if active_task is not None else None,
        active_task_title=active_task.title if active_task is not None else None,
    )


def check_forbidden_changes(
    changes: tuple[GitChange, ...], forbidden_patterns: tuple[str, ...]
) -> tuple[CheckMessage, ...]:
    return tuple(
        CheckMessage(reason="Forbidden file changed.", path=change.path)
        for change in changes
        if path_matches_any(change.path, forbidden_patterns)
    )


def check_allowed_scope(
    changes: tuple[GitChange, ...], allowed_patterns: tuple[str, ...]
) -> tuple[CheckMessage, ...]:
    scoped_changes = tuple(
        change for change in changes if not is_documentation_path(change.path)
    )
    if not scoped_changes:
        return ()

    if not allowed_patterns:
        return tuple(
            CheckMessage(
                reason="Changed file is outside active task scope.",
                path=change.path,
            )
            for change in scoped_changes
        )

    return tuple(
        CheckMessage(
            reason="Changed file is outside active task scope.",
            path=change.path,
        )
        for change in scoped_changes
        if not path_matches_any(change.path, allowed_patterns)
    )


def path_matches_any(path: Path, patterns: tuple[str, ...]) -> bool:
    path_text = path.as_posix()
    for pattern in patterns:
        if pattern.endswith("/") and path_text.startswith(pattern):
            return True
        if path_text == pattern:
            return True
    return False


def source_changed(paths: tuple[Path, ...]) -> bool:
    return any(path.as_posix().startswith(SOURCE_PREFIXES) for path in paths)


def documentation_changed(paths: tuple[Path, ...]) -> bool:
    return any(is_documentation_path(path) for path in paths)


def is_documentation_path(path: Path) -> bool:
    return path in DOCUMENTATION_PATHS or path.as_posix().startswith("tasks/active/")
