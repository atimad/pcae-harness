from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
import json
from pathlib import Path
import re

from pcae.core.architecture import analyze_changed_python_dependencies, zones_for_path
from pcae.core.git_status import GitChange, read_git_changes
from pcae.core.manifest import MANIFEST_ENTRIES
from pcae.core.paths import HarnessPath
from pcae.core.policy import (
    ARCHITECTURE_ENFORCEMENT_ADVISORY,
    ARCHITECTURE_ENFORCEMENT_STRICT,
    load_policy,
)
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
DEPENDENCY_SEPARATOR = "->"

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
class ArchitectureZoneCount:
    name: str
    file_count: int


@dataclass(frozen=True)
class TaskDependencyScope:
    allowed_rules: dict[str, tuple[str, ...]]
    forbidden_dependencies: tuple[tuple[str, str], ...]
    violations: tuple[CheckMessage, ...]


@dataclass(frozen=True)
class CheckResult:
    violations: tuple[CheckMessage, ...]
    warnings: tuple[CheckMessage, ...]
    infos: tuple[CheckMessage, ...]
    architecture_zones_touched: tuple[ArchitectureZoneCount, ...]
    architecture_dependency_warnings: tuple[CheckMessage, ...]
    architecture_enforcement_mode: str
    active_task_id: str | None = None
    active_task_title: str | None = None

    @property
    def passed(self) -> bool:
        return not self.violations


def run_checks(root: HarnessPath) -> CheckResult:
    from pcae.core.status import check_strategic_registry_coherence

    violations: list[CheckMessage] = []
    warnings: list[CheckMessage] = []
    infos: list[CheckMessage] = []

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
    violations.extend(check_session_continuity(root, active_task, warnings, infos))

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
        violations.extend(check_active_task_phase_alignment(root, active_task))
        violations.extend(check_forbidden_changes(changes, active_task))
        violations.extend(
            check_global_protected_changes(
                changes,
                active_task,
                policy.protected_patterns,
            )
        )
        violations.extend(check_allowed_scope(changes, active_task, policy.protected_patterns))
        violations.extend(
            check_task_zone_scope(
                changes,
                active_task,
                policy.architecture_zones,
            )
        )

    if source_changed(changed_paths) and not documentation_changed(changed_paths):
        violations.append(
            CheckMessage("Source files changed without documentation file updates.")
        )

    coherence_result = check_strategic_registry_coherence(root)
    for warning in coherence_result.warnings:
        message = warning.message
        if warning.detected_state:
            message = f"{message} Detected: {warning.detected_state}."
        if warning.expected_state:
            message = f"{message} Expected: {warning.expected_state}."
        if warning.remediation:
            message = f"{message} Remediation: {warning.remediation}"
        check_message = CheckMessage(message, Path(warning.document))
        if warning.blocking:
            violations.append(check_message)
        else:
            warnings.append(check_message)

    architecture_enforcement_mode = policy.architecture_enforcement_mode
    if active_task is not None:
        task_mode, mode_violation = task_enforcement_mode(active_task)
        if mode_violation is not None:
            violations.append(mode_violation)
        elif task_mode is not None:
            architecture_enforcement_mode = task_mode

    architecture_rules = policy.architecture_rules
    forbidden_dependencies: tuple[tuple[str, str], ...] = ()
    if active_task is not None:
        dependency_scope = build_task_dependency_scope(
            active_task,
            policy.architecture_zones,
        )
        violations.extend(dependency_scope.violations)
        architecture_rules = dependency_scope.allowed_rules or policy.architecture_rules
        forbidden_dependencies = dependency_scope.forbidden_dependencies

    architecture_result = analyze_changed_python_dependencies(
        root,
        changes,
        policy.architecture_zones,
        architecture_rules,
        forbidden_dependencies,
    )
    warnings.extend(
        CheckMessage(warning.reason, warning.path)
        for warning in architecture_result.parse_warnings
    )
    architecture_dependency_warnings = tuple(
        CheckMessage(warning.text)
        for warning in architecture_result.dependency_warnings
    )
    if architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_STRICT:
        violations.extend(architecture_dependency_warnings)

    return CheckResult(
        violations=tuple(violations),
        warnings=tuple(warnings),
        infos=tuple(infos),
        architecture_zones_touched=classify_architecture_zones(
            changed_paths,
            policy.architecture_zones,
        ),
        architecture_dependency_warnings=architecture_dependency_warnings,
        architecture_enforcement_mode=architecture_enforcement_mode,
        active_task_id=active_task.task_id if active_task is not None else None,
        active_task_title=active_task.title if active_task is not None else None,
    )


def classify_architecture_zones(
    paths: tuple[Path, ...],
    zones: dict[str, tuple[str, ...]],
) -> tuple[ArchitectureZoneCount, ...]:
    if not paths:
        return ()

    counts = {zone_name: 0 for zone_name in zones}
    unclassified_count = 0

    for path in paths:
        matched = False
        for zone_name, patterns in zones.items():
            if path_matches_any(path, patterns):
                counts[zone_name] += 1
                matched = True
        if not matched:
            unclassified_count += 1

    zone_counts = [
        ArchitectureZoneCount(name=zone_name, file_count=count)
        for zone_name, count in counts.items()
        if count
    ]
    if unclassified_count:
        zone_counts.append(
            ArchitectureZoneCount(
                name="unclassified",
                file_count=unclassified_count,
            )
        )

    return tuple(zone_counts)


def build_task_dependency_scope(
    active_task: ActiveTask,
    architecture_zones: dict[str, tuple[str, ...]],
) -> TaskDependencyScope:
    known_zones = set(architecture_zones)
    allowed_rules, allowed_violations = parse_dependency_rules(
        active_task.allowed_dependencies,
        known_zones,
        "Allowed Dependencies",
    )
    forbidden_dependencies, forbidden_violations = parse_dependency_pairs(
        active_task.forbidden_dependencies,
        known_zones,
        "Forbidden Dependencies",
    )
    return TaskDependencyScope(
        allowed_rules=allowed_rules,
        forbidden_dependencies=forbidden_dependencies,
        violations=allowed_violations + forbidden_violations,
    )


def parse_dependency_rules(
    dependencies: tuple[str, ...],
    known_zones: set[str],
    section_name: str,
) -> tuple[dict[str, tuple[str, ...]], tuple[CheckMessage, ...]]:
    pairs, violations = parse_dependency_pairs(dependencies, known_zones, section_name)
    rules: dict[str, list[str]] = {}
    for source_zone, target_zone in pairs:
        rules.setdefault(source_zone, []).append(target_zone)
    return (
        {source_zone: tuple(targets) for source_zone, targets in rules.items()},
        violations,
    )


def parse_dependency_pairs(
    dependencies: tuple[str, ...],
    known_zones: set[str],
    section_name: str,
) -> tuple[tuple[tuple[str, str], ...], tuple[CheckMessage, ...]]:
    pairs: list[tuple[str, str]] = []
    violations: list[CheckMessage] = []
    for dependency in dependencies:
        parsed = parse_dependency_pair(dependency)
        if parsed is None:
            violations.append(
                CheckMessage(
                    f"Invalid dependency format in task {section_name}: "
                    f"'{dependency}'. Expected 'source -> target'."
                )
            )
            continue

        source_zone, target_zone = parsed
        if source_zone not in known_zones:
            violations.append(
                CheckMessage(
                    f"Unknown architecture zone '{source_zone}' listed in task "
                    f"{section_name}."
                )
            )
        if target_zone != "*" and target_zone not in known_zones:
            violations.append(
                CheckMessage(
                    f"Unknown architecture zone '{target_zone}' listed in task "
                    f"{section_name}."
                )
            )
        pairs.append((source_zone, target_zone))

    return tuple(pairs), tuple(violations)


def parse_dependency_pair(dependency: str) -> tuple[str, str] | None:
    if dependency.count(DEPENDENCY_SEPARATOR) != 1:
        return None
    source_zone, target_zone = (
        part.strip()
        for part in dependency.split(DEPENDENCY_SEPARATOR, 1)
    )
    if not source_zone or not target_zone:
        return None
    return source_zone, target_zone


def task_enforcement_mode(active_task: ActiveTask) -> tuple[str | None, CheckMessage | None]:
    mode = active_task.enforcement_mode
    if mode is None:
        return None, None
    if mode in {"TBD", ""}:
        return None, None
    if mode in {ARCHITECTURE_ENFORCEMENT_ADVISORY, ARCHITECTURE_ENFORCEMENT_STRICT}:
        return mode, None
    return (
        None,
        CheckMessage(
            "Invalid task Enforcement Mode: "
            f"'{mode}'. Expected 'advisory' or 'strict'."
        ),
    )


def check_session_continuity(
    root: HarnessPath,
    active_task: ActiveTask | None,
    warnings: list[CheckMessage],
    infos: list[CheckMessage],
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
        return (
            CheckMessage(
                reason=(
                    "Session snapshot missing at .pcae/session.json. "
                    "Run `pcae session write`."
                ),
                path=Path(".pcae/session.json"),
            ),
        )

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

    infos.append(CheckMessage("Session continuity verified."))
    return ()


def check_task_zone_scope(
    changes: tuple[GitChange, ...],
    active_task: ActiveTask,
    architecture_zones: dict[str, tuple[str, ...]],
) -> tuple[CheckMessage, ...]:
    if not active_task.allowed_zones and not active_task.forbidden_zones:
        return ()

    violations: list[CheckMessage] = []
    known_zones = set(architecture_zones) | {"unclassified"}
    violations.extend(
        unknown_task_zone_violations(
            active_task.allowed_zones,
            known_zones,
            "Allowed Zones",
        )
    )
    violations.extend(
        unknown_task_zone_violations(
            active_task.forbidden_zones,
            known_zones,
            "Forbidden Zones",
        )
    )
    if violations:
        return tuple(violations)

    for change in changes:
        changed_zones = zones_for_changed_path(change.path, architecture_zones)
        forbidden_matches = tuple(
            zone for zone in changed_zones if zone in active_task.forbidden_zones
        )
        if forbidden_matches:
            violations.extend(
                CheckMessage(
                    reason=(
                        f"Changed file touches forbidden architecture zone '{zone}' "
                        f"for task {active_task.task_id}."
                    ),
                    path=change.path,
                )
                for zone in forbidden_matches
            )
            continue

        if not active_task.allowed_zones:
            continue

        violations.extend(
            CheckMessage(
                reason=(
                    f"Changed file touches architecture zone '{zone}' outside "
                    f"Allowed Zones for task {active_task.task_id}."
                ),
                path=change.path,
            )
            for zone in changed_zones
            if zone not in active_task.allowed_zones
        )

    return tuple(violations)


def zones_for_changed_path(
    path: Path,
    architecture_zones: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    matched_zones = zones_for_path(path, architecture_zones)
    return matched_zones or ("unclassified",)


def unknown_task_zone_violations(
    zones: tuple[str, ...],
    known_zones: set[str],
    section_name: str,
) -> tuple[CheckMessage, ...]:
    return tuple(
        CheckMessage(
            f"Unknown architecture zone '{zone}' listed in task {section_name}."
        )
        for zone in zones
        if zone not in known_zones
    )


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


_PHASE_CODE_RE = re.compile(r"\b(\d+[A-Z][\d.A-Z]*)\b")


def _extract_phase_code_from_project_status(content: str) -> str | None:
    in_section = False
    for line in content.splitlines():
        if line.strip() == "## Current Phase":
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("#"):
                break
            match = _PHASE_CODE_RE.search(line)
            if match:
                return match.group(1)
    return None


def _extract_phase_code_from_title(title: str) -> str | None:
    match = _PHASE_CODE_RE.match(title.strip())
    return match.group(1) if match else None


def check_active_task_phase_alignment(
    root: HarnessPath,
    active_task: ActiveTask,
) -> tuple[CheckMessage, ...]:
    status_path = root.join(Path("PROJECT_STATUS.md"))
    if not status_path.is_file():
        return ()

    content = status_path.read_text(encoding="utf-8")
    status_phase = _extract_phase_code_from_project_status(content)
    task_phase = _extract_phase_code_from_title(active_task.title)

    if status_phase is None or task_phase is None:
        return ()

    if status_phase.upper() == task_phase.upper():
        return ()

    return (
        CheckMessage(
            reason=(
                f"Active task phase '{task_phase}' does not match "
                f"PROJECT_STATUS.md current phase '{status_phase}'. "
                "Run `pcae task transition` to advance task state."
            ),
        ),
    )
