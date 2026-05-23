from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
import json
from pathlib import Path

from pcae.core.git_status import GitChange, read_git_changes
from pcae.core.manifest import MANIFEST_ENTRIES
from pcae.core.paths import HarnessPath
from pcae.core.policy import load_policy
from pcae.core.session import read_session_snapshot
from pcae.core.tasks import ActiveTask, find_latest_active_task


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
    violations.extend(check_session_continuity(root, active_task, warnings))

    changes = read_git_changes(root)
    changed_paths = tuple(change.path for change in changes)
    policy = load_policy(root)
    if not policy.valid:
        violations.append(
            CheckMessage(
                reason=policy.error or "Invalid policy file.",
                path=policy.path.relative_to(root.path),
            )
        )

    if active_task is not None:
        violations.extend(check_forbidden_changes(changes, active_task))
        violations.extend(
            check_global_protected_changes(
                changes,
                active_task,
                policy.protected_patterns,
            )
        )
        violations.extend(check_allowed_scope(changes, active_task, policy.protected_patterns))

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


def check_session_continuity(
    root: HarnessPath,
    active_task: ActiveTask | None,
    warnings: list[CheckMessage],
) -> tuple[CheckMessage, ...]:
    try:
        snapshot = read_session_snapshot(root)
    except json.JSONDecodeError as error:
        return (
            CheckMessage(
                reason=f"Invalid session JSON: {error.msg}.",
                path=Path(".pcae/session.json"),
            ),
        )

    if snapshot is None:
        warnings.append(
            CheckMessage(
                "Session snapshot missing at .pcae/session.json. "
                "Run `pcae session write`."
            )
        )
        return ()

    session_task = snapshot.data.get("active_task")
    current_task = None
    if active_task is not None:
        current_task = {
            "id": active_task.task_id,
            "title": active_task.title,
        }

    if session_task != current_task:
        return (
            CheckMessage(
                reason=(
                    "Session active task does not match current active task. "
                    "Run `pcae session write`."
                ),
                path=Path(".pcae/session.json"),
            ),
        )

    warnings.append(CheckMessage("Session active task matches current active task."))
    return ()


def check_forbidden_changes(
    changes: tuple[GitChange, ...], active_task: ActiveTask
) -> tuple[CheckMessage, ...]:
    violations: list[CheckMessage] = []
    for change in changes:
        matched_pattern = first_matching_pattern(change.path, active_task.forbidden_files)
        if matched_pattern is None:
            continue
        violations.append(
            CheckMessage(
                reason=forbidden_failure_reason(active_task, matched_pattern),
                path=change.path,
            )
        )
    return tuple(violations)


def check_allowed_scope(
    changes: tuple[GitChange, ...],
    active_task: ActiveTask,
    protected_patterns: tuple[str, ...],
) -> tuple[CheckMessage, ...]:
    scoped_changes = tuple(
        change
        for change in changes
        if not is_documentation_path(change.path)
        and not path_matches_any(change.path, active_task.forbidden_files)
        and not protected_change_is_blocked(change.path, active_task, protected_patterns)
    )
    if not scoped_changes:
        return ()

    allowed_patterns = active_task.allowed_files
    if not allowed_patterns:
        return tuple(
            CheckMessage(
                reason=scope_failure_reason(active_task),
                path=change.path,
            )
            for change in scoped_changes
        )

    return tuple(
        CheckMessage(
            reason=scope_failure_reason(active_task),
            path=change.path,
        )
        for change in scoped_changes
        if not path_matches_any(change.path, allowed_patterns)
    )


def check_global_protected_changes(
    changes: tuple[GitChange, ...],
    active_task: ActiveTask,
    protected_patterns: tuple[str, ...],
) -> tuple[CheckMessage, ...]:
    violations: list[CheckMessage] = []
    for change in changes:
        if path_matches_any(change.path, active_task.forbidden_files):
            continue
        matched_pattern = first_matching_pattern(change.path, protected_patterns)
        if matched_pattern is None:
            continue
        if path_matches_any(change.path, active_task.override_protected_files):
            continue
        violations.append(
            CheckMessage(
                reason=protected_failure_reason(active_task, matched_pattern),
                path=change.path,
            )
        )
    return tuple(violations)


def protected_change_is_blocked(
    path: Path,
    active_task: ActiveTask,
    protected_patterns: tuple[str, ...],
) -> bool:
    if first_matching_pattern(path, protected_patterns) is None:
        return False
    return not path_matches_any(path, active_task.override_protected_files)


def path_matches_any(path: Path, patterns: tuple[str, ...]) -> bool:
    return first_matching_pattern(path, patterns) is not None


def first_matching_pattern(path: Path, patterns: tuple[str, ...]) -> str | None:
    path_text = path.as_posix()
    for pattern in patterns:
        normalized = pattern.strip()
        if not normalized:
            continue
        if path_matches_pattern(path_text, normalized):
            return normalized
    return None


def path_matches_pattern(path_text: str, pattern: str) -> bool:
    if pattern.endswith("/"):
        return path_text.startswith(pattern)
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path_text == prefix or path_text.startswith(f"{prefix}/")
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        if not path_text.startswith(f"{prefix}/"):
            return False
        remainder = path_text[len(prefix) + 1 :]
        return "/" not in remainder
    if "/" not in pattern and fnmatch(Path(path_text).name, pattern):
        return True
    return fnmatch(path_text, pattern)


def scope_failure_reason(active_task: ActiveTask) -> str:
    return (
        "Changed file is outside active task scope "
        f"for task {active_task.task_id}; no allowed-file pattern matched."
    )


def forbidden_failure_reason(active_task: ActiveTask, matched_pattern: str) -> str:
    return (
        "Forbidden file changed "
        f"for task {active_task.task_id} ({active_task.title}); "
        f"matched forbidden pattern '{matched_pattern}'."
    )


def protected_failure_reason(active_task: ActiveTask, matched_pattern: str) -> str:
    return (
        "Protected file changed "
        f"for task {active_task.task_id} ({active_task.title}); "
        f"matched protected pattern '{matched_pattern}'. "
        "To allow this intentionally, list the file or pattern under "
        "'Override Protected Files'."
    )


def source_changed(paths: tuple[Path, ...]) -> bool:
    return any(path.as_posix().startswith(SOURCE_PREFIXES) for path in paths)


def documentation_changed(paths: tuple[Path, ...]) -> bool:
    return any(is_documentation_path(path) for path in paths)


def is_documentation_path(path: Path) -> bool:
    return path in DOCUMENTATION_PATHS or path.as_posix().startswith("tasks/active/")
