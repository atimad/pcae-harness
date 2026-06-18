from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import unicodedata

from pcae.core.paths import HarnessPath


@dataclass(frozen=True)
class TaskContract:
    task_id: str
    title: str
    relative_path: Path
    created_at: datetime
    content: str


@dataclass(frozen=True)
class ClosedTask:
    task_id: str
    title: str
    source_path: Path
    destination_path: Path


@dataclass(frozen=True)
class TaskSummary:
    task_id: str
    title: str
    status: str
    path: Path


@dataclass(frozen=True)
class ActiveTask:
    path: Path
    task_id: str
    title: str
    status: str
    mode: str
    goal: str | None
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    override_protected_files: tuple[str, ...]
    allowed_zones: tuple[str, ...]
    forbidden_zones: tuple[str, ...]
    allowed_dependencies: tuple[str, ...]
    forbidden_dependencies: tuple[str, ...]
    enforcement_mode: str | None
    acceptance_checks: tuple[str, ...]
    documentation_requirements: tuple[str, ...]


@dataclass(frozen=True)
class TaskUpdate:
    goal: str | None = None
    mode: str | None = None
    allowed_files: tuple[str, ...] | None = None
    forbidden_files: tuple[str, ...] | None = None
    allowed_zones: tuple[str, ...] | None = None
    forbidden_zones: tuple[str, ...] | None = None
    enforcement_mode: str | None = None
    acceptance_checks: tuple[str, ...] | None = None


@dataclass(frozen=True)
class TaskTransitionValidation:
    active_task: ActiveTask | None
    next_title: str | None
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def safe_to_complete(self) -> bool:
        return not self.blockers


@dataclass(frozen=True)
class TaskFinishValidation:
    active_task: ActiveTask | None
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def safe_to_finish(self) -> bool:
        return not self.blockers


@dataclass(frozen=True)
class TaskFinishResult:
    completed_task: ClosedTask
    updated_files: tuple[Path, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class TaskTransitionRecord:
    completed_task: ClosedTask
    next_task: TaskContract
    next_title: str
    updated_files: tuple[Path, ...]
    warnings: tuple[str, ...]


TRANSITION_ALLOWED_FILES: tuple[str, ...] = (
    "tasks/active/**",
    "tasks/done/**",
    "tasks/TODO.md",
    "tasks/DONE.md",
    "tasks/DECISIONS.md",
    "PROJECT_STATUS.md",
    "CHANGELOG.md",
)

TRANSITION_ACCEPTANCE_CHECKS: tuple[str, ...] = (
    "pcae status coherence passes",
    "pcae health passes",
    "pcae check passes",
    "python -m pytest -n auto passes",
)

TRANSITION_FORBIDDEN_CHANGES: tuple[str, ...] = (
    "No runtime invocation",
    "No prompt execution",
    "No source behavior changes outside task/session/handoff governance",
    "No execution authorization",
    "No commit",
    "No push",
    "No rollback",
)

TRANSITION_DOCUMENTATION_REQUIREMENTS: tuple[str, ...] = (
    "Update project memory files when workflow-visible behavior changes.",
)

TRANSITION_SESSION_RELATIVE_PATH = Path(".pcae") / "session.json"
TODO_RELATIVE_PATH = Path("tasks") / "TODO.md"
DONE_RELATIVE_PATH = Path("tasks") / "DONE.md"
DECISIONS_RELATIVE_PATH = Path("tasks") / "DECISIONS.md"
PROJECT_STATUS_RELATIVE_PATH = Path("PROJECT_STATUS.md")
CHANGELOG_RELATIVE_PATH = Path("CHANGELOG.md")


def create_task_contract(
    root: HarnessPath,
    title: str,
    created_at: datetime | None = None,
    mode: str = "implementation",
    goal: str = "TBD",
    allowed_files: tuple[str, ...] = (),
    forbidden_files: tuple[str, ...] = (),
    override_protected_files: tuple[str, ...] = (),
    allowed_zones: tuple[str, ...] = (),
    forbidden_zones: tuple[str, ...] = (),
    allowed_dependencies: tuple[str, ...] = (),
    forbidden_dependencies: tuple[str, ...] = (),
    enforcement_mode: str = "TBD",
    forbidden_changes: tuple[str, ...] = ("TBD",),
    acceptance_checks: tuple[str, ...] = (),
    documentation_requirements: tuple[str, ...] = TRANSITION_DOCUMENTATION_REQUIREMENTS,
) -> TaskContract:
    timestamp = created_at or datetime.now().astimezone()
    slug = slugify_title(title)
    task_id = f"{timestamp:%Y%m%d-%H%M}-{slug}"
    relative_path = Path("tasks") / "active" / f"{task_id}.md"
    content = render_task_contract(
        task_id=task_id,
        title=title,
        created_at=timestamp,
        mode=mode,
        goal=goal,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        override_protected_files=override_protected_files,
        allowed_zones=allowed_zones,
        forbidden_zones=forbidden_zones,
        allowed_dependencies=allowed_dependencies,
        forbidden_dependencies=forbidden_dependencies,
        enforcement_mode=enforcement_mode,
        forbidden_changes=forbidden_changes,
        acceptance_checks=acceptance_checks,
        documentation_requirements=documentation_requirements,
    )

    target = root.join(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as file:
        file.write(content)

    return TaskContract(
        task_id=task_id,
        title=title,
        relative_path=relative_path,
        created_at=timestamp,
        content=content,
    )


def close_latest_active_task(root: HarnessPath) -> ClosedTask | None:
    active_task = find_latest_active_task(root)
    if active_task is None:
        return None
    return close_active_task(active_task)


def pause_latest_active_task(root: HarnessPath) -> ActiveTask | None:
    active_task = find_latest_active_task_with_status(root, "active")
    if active_task is None:
        return None
    return set_active_task_status(active_task, "paused")


def resume_latest_paused_task(root: HarnessPath) -> ActiveTask | None:
    paused_task = find_latest_active_task_with_status(root, "paused")
    if paused_task is None:
        return None
    return set_active_task_status(paused_task, "active")


def complete_latest_active_task(root: HarnessPath) -> ClosedTask | None:
    active_task = find_latest_active_task_with_status(root, "active")
    if active_task is None:
        return None
    return close_active_task(active_task)


def validate_task_finish(root: HarnessPath, skip_checks: bool = False) -> TaskFinishValidation:
    blockers: list[str] = []
    warnings: list[str] = []
    active_task = find_latest_active_task_with_status(root, "active")

    if active_task is None:
        blockers.append("No active task contract found to finish.")
        return TaskFinishValidation(
            active_task=None,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )

    done_path = root.join(Path("tasks") / "done" / active_task.path.name)
    if done_path.exists():
        blockers.append(
            f"Done task already exists for {active_task.task_id} at "
            f"{done_path.relative_to(root.path).as_posix()}."
        )

    if not skip_checks:
        from pcae.core.check import run_checks
        from pcae.core.health import build_health_data
        from pcae.core.status import check_project_status_coherence

        health = build_health_data(root)
        if health.get("overall_status") != "healthy":
            blockers.append("pcae health is unhealthy. Fix health issues before finishing.")

        check_result = run_checks(root)
        if not check_result.passed:
            blockers.append("pcae check has violations. Fix check violations before finishing.")

        coherence = check_project_status_coherence(root)
        if not coherence.coherent:
            warnings.append("pcae status coherence failed — PROJECT_STATUS.md may be stale.")

    return TaskFinishValidation(
        active_task=active_task,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def finish_active_task(root: HarnessPath, skip_checks: bool = False) -> TaskFinishResult:
    validation = validate_task_finish(root, skip_checks=skip_checks)
    if not validation.safe_to_finish or validation.active_task is None:
        raise ValueError(
            validation.blockers[0] if validation.blockers else "Task finish is blocked."
        )

    active_task = validation.active_task
    completed_task = close_active_task(active_task)

    updated_files: list[Path] = [
        completed_task.destination_path.relative_to(root.path),
    ]

    if update_done_memory(root, completed_task):
        updated_files.append(DONE_RELATIVE_PATH)
    if update_todo_memory_for_finish(root, active_task.title):
        updated_files.append(TODO_RELATIVE_PATH)

    from pcae.core.session import write_session_snapshot

    write_session_snapshot(root)
    updated_files.append(TRANSITION_SESSION_RELATIVE_PATH)

    return TaskFinishResult(
        completed_task=completed_task,
        updated_files=tuple(_unique_paths(updated_files)),
        warnings=validation.warnings,
    )


def update_todo_memory_for_finish(root: HarnessPath, finished_title: str) -> bool:
    path = root.join(TODO_RELATIVE_PATH)
    if not path.is_file():
        return False
    original = path.read_text(encoding="utf-8")
    updated = remove_exact_bullets(original, {finished_title})
    if updated == original:
        return False
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)
    return True


def close_active_task_by_identifier(
    root: HarnessPath,
    identifier: str,
) -> ClosedTask | None:
    task_path = active_task_path_for_identifier(root, identifier)
    if not task_path.is_file():
        return None
    return close_active_task(read_active_task(task_path))


def close_active_task(active_task: ActiveTask) -> ClosedTask:
    source_path = active_task.path
    content = source_path.read_text(encoding="utf-8")
    destination_path = source_path.parents[1] / "done" / source_path.name

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with source_path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(replace_task_status(content, "done"))
    source_path.replace(destination_path)

    return ClosedTask(
        task_id=active_task.task_id,
        title=active_task.title,
        source_path=source_path,
        destination_path=destination_path,
    )


def set_active_task_status(active_task: ActiveTask, status: str) -> ActiveTask:
    content = active_task.path.read_text(encoding="utf-8")
    with active_task.path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(replace_task_status(content, status))
    return read_active_task(active_task.path)


def active_task_path_for_identifier(root: HarnessPath, identifier: str) -> Path:
    filename = identifier if identifier.endswith(".md") else f"{identifier}.md"
    return root.join(Path("tasks") / "active" / filename)


def list_task_summaries(root: HarnessPath) -> tuple[TaskSummary, ...]:
    return read_task_summaries(root, "active") + read_task_summaries(root, "done")


def read_task_summaries(root: HarnessPath, status: str) -> tuple[TaskSummary, ...]:
    task_dir = root.join(Path("tasks") / status)
    if not task_dir.is_dir():
        return ()

    return tuple(read_task_summary(path, status) for path in sorted(task_dir.glob("*.md")))


def read_task_summary(task_path: Path, fallback_status: str) -> TaskSummary:
    content = task_path.read_text(encoding="utf-8")
    return TaskSummary(
        task_id=read_task_section_text(content, "Task ID") or task_path.stem,
        title=read_task_section_text(content, "Title") or "Untitled task",
        status=read_task_section_text(content, "Status") or fallback_status,
        path=task_path,
    )


def update_latest_active_task(root: HarnessPath, update: TaskUpdate) -> ActiveTask | None:
    active_task = find_latest_active_task(root)
    if active_task is None:
        return None

    content = active_task.path.read_text(encoding="utf-8")
    if update.goal is not None:
        content = replace_task_section_text(content, "Goal", update.goal)
    if update.mode is not None:
        content = replace_task_section_text(content, "Mode", update.mode)
    if update.allowed_files is not None:
        content = replace_task_section_items(
            content,
            "Allowed Files",
            update.allowed_files,
        )
    if update.forbidden_files is not None:
        content = replace_task_section_items(
            content,
            "Forbidden Files",
            update.forbidden_files,
        )
    if update.allowed_zones is not None:
        content = replace_task_section_items(
            content,
            "Allowed Zones",
            update.allowed_zones,
        )
    if update.forbidden_zones is not None:
        content = replace_task_section_items(
            content,
            "Forbidden Zones",
            update.forbidden_zones,
        )
    if update.enforcement_mode is not None:
        content = replace_task_section_text(
            content,
            "Enforcement Mode",
            update.enforcement_mode,
        )
    if update.acceptance_checks is not None:
        content = replace_task_section_items(
            content,
            "Acceptance Checks",
            update.acceptance_checks,
        )

    with active_task.path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(content)
    return read_active_task(active_task.path)


def slugify_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug or "task"


def _slug_from_task_stem(stem: str) -> str:
    """Extract the slug portion from a task file stem (YYYYMMDD-HHMM-{slug} → {slug})."""
    parts = stem.split("-", 2)
    return parts[2] if len(parts) >= 3 else stem


def list_task_slugs_in_dir(dir_path: Path) -> frozenset[str]:
    """Return slugs for all task files in a directory."""
    if not dir_path.is_dir():
        return frozenset()
    return frozenset(_slug_from_task_stem(f.stem) for f in dir_path.glob("*.md"))


def render_task_contract(
    task_id: str,
    title: str,
    created_at: datetime,
    mode: str = "implementation",
    goal: str = "TBD",
    allowed_files: tuple[str, ...] = (),
    forbidden_files: tuple[str, ...] = (),
    override_protected_files: tuple[str, ...] = (),
    allowed_zones: tuple[str, ...] = (),
    forbidden_zones: tuple[str, ...] = (),
    allowed_dependencies: tuple[str, ...] = (),
    forbidden_dependencies: tuple[str, ...] = (),
    enforcement_mode: str = "TBD",
    forbidden_changes: tuple[str, ...] = ("TBD",),
    acceptance_checks: tuple[str, ...] = (),
    documentation_requirements: tuple[str, ...] = TRANSITION_DOCUMENTATION_REQUIREMENTS,
) -> str:
    optional_override_section = ""
    if override_protected_files:
        optional_override_section = (
            "\n## Override Protected Files\n\n"
            f"{render_task_items(override_protected_files)}\n"
        )
    return f"""# Task Contract

## Task ID

{task_id}

## Title

{title}

## Status

active

## Mode

{mode}

## Goal

{goal}

## Allowed Files

{render_task_items(allowed_files)}

## Forbidden Files

{render_task_items(forbidden_files)}
{optional_override_section}

## Allowed Zones

{render_task_items(allowed_zones)}

## Forbidden Zones

{render_task_items(forbidden_zones)}

## Allowed Dependencies

{render_task_items(allowed_dependencies)}

## Forbidden Dependencies

{render_task_items(forbidden_dependencies)}

## Enforcement Mode

{enforcement_mode}

## Forbidden Changes

{render_task_items(forbidden_changes)}

## Acceptance Checks

{render_task_items(acceptance_checks)}

## Documentation Requirements

{render_task_items(documentation_requirements)}

## Created Timestamp

{created_at.isoformat()}
"""


def render_task_items(items: tuple[str, ...]) -> str:
    if not items:
        return "- TBD"
    return "\n".join(f"- {item}" for item in items)


def find_latest_active_task(root: HarnessPath) -> ActiveTask | None:
    active_dir = root.join(Path("tasks") / "active")
    if not active_dir.is_dir():
        return None

    task_files = sorted(active_dir.glob("*.md"))
    if not task_files:
        return None
    return read_active_task(task_files[-1])


def find_latest_active_task_with_status(
    root: HarnessPath,
    status: str,
) -> ActiveTask | None:
    active_dir = root.join(Path("tasks") / "active")
    if not active_dir.is_dir():
        return None

    for task_file in reversed(sorted(active_dir.glob("*.md"))):
        active_task = read_active_task(task_file)
        if active_task.status == status:
            return active_task
    return None


def validate_task_transition(
    root: HarnessPath,
    next_title: str | None = None,
) -> TaskTransitionValidation:
    blockers: list[str] = []
    warnings: list[str] = []
    active_task = find_latest_active_task_with_status(root, "active")
    resolved_next_title = resolve_next_task_title(root, next_title)

    if active_task is None:
        blockers.append("No active task contract found to transition.")
    else:
        session_issue = validate_transition_session(root, active_task)
        if session_issue is not None:
            blockers.append(session_issue)

        done_path = root.join(Path("tasks") / "done" / active_task.path.name)
        if done_path.exists():
            blockers.append(
                f"Done task already exists for {active_task.task_id} at "
                f"{done_path.relative_to(root.path).as_posix()}."
            )

    if resolved_next_title is None:
        blockers.append("Unable to determine the next task title.")
    elif next_title is None:
        warnings.append("Next task title resolved automatically from governance context.")

    if resolved_next_title is not None and active_task is not None:
        next_slug = slugify_title(resolved_next_title)

        if resolved_next_title.strip().lower() == active_task.title.strip().lower():
            blockers.append(
                f"Next task title '{resolved_next_title}' is the same as the current "
                "active task. Transitioning to the same phase is not allowed."
            )

        done_dir = root.join(Path("tasks") / "done")
        done_slugs = list_task_slugs_in_dir(done_dir)
        if next_slug in done_slugs:
            blockers.append(
                f"Next task title '{resolved_next_title}' matches a completed task in "
                "tasks/done/. Transitioning to a completed phase is not allowed."
            )

        active_dir = root.join(Path("tasks") / "active")
        current_slug = _slug_from_task_stem(active_task.path.stem)
        active_slugs = list_task_slugs_in_dir(active_dir) - {current_slug}
        if next_slug in active_slugs:
            blockers.append(
                f"An active task with title '{resolved_next_title}' already exists. "
                "Use a different title for the next task."
            )

    return TaskTransitionValidation(
        active_task=active_task,
        next_title=resolved_next_title,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def transition_active_task(
    root: HarnessPath,
    next_title: str | None = None,
    created_at: datetime | None = None,
) -> TaskTransitionRecord:
    validation = validate_task_transition(root, next_title)
    if not validation.safe_to_complete or validation.active_task is None or validation.next_title is None:
        raise ValueError(validation.blockers[0] if validation.blockers else "Task transition is blocked.")

    timestamp = created_at or datetime.now().astimezone()
    active_task = validation.active_task
    enforcement_mode = active_task.enforcement_mode
    if enforcement_mode in {None, "", "TBD"}:
        enforcement_mode = "strict"
    completed_task = close_active_task(active_task)
    changed_files = changed_paths_for_transition(root)
    next_task = create_task_contract(
        root,
        validation.next_title,
        created_at=timestamp,
        mode=active_task.mode or "implementation",
        goal=default_next_task_goal(validation.next_title),
        allowed_files=build_transition_allowed_files(changed_files),
        forbidden_files=(),
        override_protected_files=active_task.override_protected_files,
        allowed_zones=(),
        forbidden_zones=(),
        allowed_dependencies=(),
        forbidden_dependencies=(),
        enforcement_mode=enforcement_mode,
        forbidden_changes=TRANSITION_FORBIDDEN_CHANGES,
        acceptance_checks=TRANSITION_ACCEPTANCE_CHECKS,
        documentation_requirements=TRANSITION_DOCUMENTATION_REQUIREMENTS,
    )

    updated_files = [
        completed_task.destination_path.relative_to(root.path),
        next_task.relative_path,
    ]
    if update_done_memory(root, completed_task):
        updated_files.append(DONE_RELATIVE_PATH)
    if update_todo_memory(root, active_task.title, validation.next_title):
        updated_files.append(TODO_RELATIVE_PATH)
    if update_project_status_phase(root, validation.next_title):
        updated_files.append(PROJECT_STATUS_RELATIVE_PATH)
    if update_changelog_transition(root, active_task.title, validation.next_title):
        updated_files.append(CHANGELOG_RELATIVE_PATH)

    return TaskTransitionRecord(
        completed_task=completed_task,
        next_task=next_task,
        next_title=validation.next_title,
        updated_files=tuple(_unique_paths(updated_files)),
        warnings=validation.warnings,
    )


def read_active_task(task_path: Path) -> ActiveTask:
    content = task_path.read_text(encoding="utf-8")
    return ActiveTask(
        path=task_path,
        task_id=read_task_section_text(content, "Task ID") or task_path.stem,
        title=read_task_section_text(content, "Title") or "Untitled task",
        status=read_task_section_text(content, "Status") or "active",
        mode=read_task_section_text(content, "Mode") or "unspecified",
        goal=read_task_section_text(content, "Goal"),
        allowed_files=read_task_section_items_from_text(content, "Allowed Files"),
        forbidden_files=read_task_section_items_from_text(content, "Forbidden Files"),
        override_protected_files=read_task_section_items_from_text(
            content,
            "Override Protected Files",
        ),
        allowed_zones=read_task_section_items_from_text(content, "Allowed Zones"),
        forbidden_zones=read_task_section_items_from_text(content, "Forbidden Zones"),
        allowed_dependencies=read_task_section_items_from_text(
            content,
            "Allowed Dependencies",
        ),
        forbidden_dependencies=read_task_section_items_from_text(
            content,
            "Forbidden Dependencies",
        ),
        enforcement_mode=read_task_section_text(content, "Enforcement Mode"),
        acceptance_checks=read_task_section_items_from_text(
            content,
            "Acceptance Checks",
        ),
        documentation_requirements=read_task_section_items_from_text(
            content,
            "Documentation Requirements",
        ),
    )


def resolve_next_task_title(root: HarnessPath, explicit_title: str | None) -> str | None:
    if explicit_title is not None:
        title = explicit_title.strip()
        return title or None

    todo_title = first_pending_todo_title(root)
    if todo_title is not None:
        return todo_title

    roadmap_title = first_next_roadmap_title(root)
    if roadmap_title is not None:
        return roadmap_title

    return "Next governed task"


def first_pending_todo_title(root: HarnessPath) -> str | None:
    path = root.join(TODO_RELATIVE_PATH)
    if not path.is_file():
        return None
    content = path.read_text(encoding="utf-8")
    return first_markdown_bullet_in_section(content, "Pending")


def first_next_roadmap_title(root: HarnessPath) -> str | None:
    path = root.join(PROJECT_STATUS_RELATIVE_PATH)
    if not path.is_file():
        return None
    content = path.read_text(encoding="utf-8")
    return first_markdown_bullet_in_section(content, "Next Roadmap")


def first_markdown_bullet_in_section(content: str, section_name: str) -> str | None:
    for item in read_markdown_section_items(content, section_name):
        if item != "TBD":
            return item
    return None


def read_markdown_section_items(content: str, section_name: str) -> tuple[str, ...]:
    lines = content.splitlines()
    in_section = False
    items: list[str] = []

    for line in lines:
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            if in_section:
                break
            in_section = current_section == section_name
            continue
        if not in_section:
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped.removeprefix("- ").strip())

    return tuple(items)


def validate_transition_session(root: HarnessPath, active_task: ActiveTask) -> str | None:
    path = root.join(TRANSITION_SESSION_RELATIVE_PATH)
    if not path.is_file():
        return "Session snapshot missing at .pcae/session.json."
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return f"Invalid session JSON: {error.msg}."

    session_task = data.get("active_task")
    current_task = {"id": active_task.task_id, "title": active_task.title}
    if session_task != current_task:
        return (
            "Session active task does not match current active task. "
            "Run `pcae session write` before transitioning."
        )
    return None


def changed_paths_for_transition(root: HarnessPath) -> tuple[str, ...]:
    git_dir = root.join(Path(".git"))
    if not git_dir.exists():
        return ()

    from pcae.core.git_status import read_git_changes

    paths = [
        change.path.as_posix()
        for change in read_git_changes(root)
        if not is_transition_documentation_path(change.path)
    ]
    return tuple(_unique_strings(paths))


def is_transition_documentation_path(path: Path) -> bool:
    path_text = path.as_posix()
    return (
        path_text == "tasks/TODO.md"
        or path_text == "tasks/DONE.md"
        or path_text == "tasks/DECISIONS.md"
        or path_text == "PROJECT_STATUS.md"
        or path_text == "CHANGELOG.md"
        or path_text.startswith("tasks/active/")
        or path_text.startswith("tasks/done/")
    )


def build_transition_allowed_files(changed_paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_unique_strings((*TRANSITION_ALLOWED_FILES, *changed_paths)))


def default_next_task_goal(title: str) -> str:
    return title


def update_done_memory(root: HarnessPath, completed_task: ClosedTask) -> bool:
    line = f"- {completed_task.title} ({completed_task.task_id})"
    return ensure_bullet_in_section(
        root.join(DONE_RELATIVE_PATH),
        "Done",
        "Completed",
        line,
    )


def update_todo_memory(root: HarnessPath, previous_title: str, next_title: str) -> bool:
    path = root.join(TODO_RELATIVE_PATH)
    if not path.is_file():
        return False
    original = path.read_text(encoding="utf-8")
    updated = remove_exact_bullets(original, {previous_title, next_title})
    if updated == original:
        return False
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)
    return True


def update_project_status_phase(root: HarnessPath, next_title: str) -> bool:
    path = root.join(PROJECT_STATUS_RELATIVE_PATH)
    if not path.is_file():
        return False
    phase_text = phase_text_from_title(next_title)
    if phase_text is None:
        return False
    original = path.read_text(encoding="utf-8")
    updated = replace_markdown_section_text(original, "Current Phase", phase_text)
    updated = remove_exact_bullets(updated, {next_title})
    if updated == original:
        return False
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)
    return True


def update_changelog_transition(root: HarnessPath, previous_title: str, next_title: str) -> bool:
    line = f"- Transitioned active task from {previous_title} to {next_title}; session refreshed and governance continuity revalidated."
    return ensure_bullet_in_section(
        root.join(CHANGELOG_RELATIVE_PATH),
        "Changelog",
        "Unreleased",
        line,
    )


def ensure_bullet_in_section(
    path: Path,
    document_title: str,
    section_name: str,
    bullet: str,
) -> bool:
    if path.is_file():
        original = path.read_text(encoding="utf-8")
    else:
        original = f"# {document_title}\n\n## {section_name}\n\n"
    existing_items = read_markdown_section_items(original, section_name)
    if bullet.removeprefix("- ").strip() in existing_items:
        return False
    updated = insert_bullet_in_section(original, section_name, bullet)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)
    return True


def insert_bullet_in_section(content: str, section_name: str, bullet: str) -> str:
    lines = content.splitlines()
    normalized_bullet = bullet if bullet.startswith("- ") else f"- {bullet}"
    start_index = None
    end_index = len(lines)
    for index, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        current_section = line.removeprefix("## ").strip()
        if current_section == section_name:
            start_index = index
            continue
        if start_index is not None:
            end_index = index
            break
    if start_index is None:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend([f"## {section_name}", "", normalized_bullet])
        return "\n".join(lines).rstrip() + "\n"

    insertion_index = start_index + 1
    while insertion_index < len(lines) and lines[insertion_index] == "":
        insertion_index += 1
    updated_lines = lines[:insertion_index] + [normalized_bullet] + lines[insertion_index:end_index]
    return "\n".join(updated_lines).rstrip() + "\n"


def remove_exact_bullets(content: str, titles: set[str]) -> str:
    lines = content.splitlines()
    filtered = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") and stripped.removeprefix("- ").strip() in titles:
            continue
        filtered.append(line)
    return "\n".join(filtered).rstrip() + "\n"


def replace_markdown_section_text(content: str, section_name: str, value: str) -> str:
    return replace_task_section(content, section_name, (value,))


def phase_text_from_title(title: str) -> str | None:
    match = re.match(r"(?P<phase>\d+[A-Z])\s*:\s*(?P<label>.+)", title)
    if match is not None:
        label = match.group("label").rstrip(".").strip()
        return f"Phase {match.group('phase')}: {label}."

    match = re.search(r"\(Phase (?P<phase>[^)]+)\)", title)
    if match is None:
        return None
    phase = match.group("phase").strip()
    label = title[: match.start()].strip().rstrip("-: ")
    if not label:
        return f"Phase {phase}."
    return f"Phase {phase}: {label}."


def _unique_strings(items: tuple[str, ...] | list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _unique_paths(items: list[Path]) -> list[Path]:
    seen: set[str] = set()
    ordered: list[Path] = []
    for item in items:
        key = item.as_posix()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def read_task_section_items(task_path: Path, section_name: str) -> tuple[str, ...]:
    return read_task_section_items_from_text(
        task_path.read_text(encoding="utf-8"),
        section_name,
    )


def read_task_section_items_from_text(content: str, section_name: str) -> tuple[str, ...]:
    lines = content.splitlines()
    items: list[str] = []
    in_section = False

    for line in lines:
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            in_section = current_section == section_name
            continue

        if not in_section:
            continue

        stripped = line.strip()
        if not stripped.startswith("- "):
            continue

        item = stripped.removeprefix("- ").strip()
        if item and item != "TBD":
            items.append(item)

    return tuple(items)


def read_task_section_text(content: str, section_name: str) -> str | None:
    lines = content.splitlines()
    in_section = False
    values: list[str] = []

    for line in lines:
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            if in_section:
                break
            in_section = current_section == section_name
            continue

        if in_section and line.strip():
            values.append(line.strip())

    if not values:
        return None
    return "\n".join(values)


def replace_task_status(content: str, status: str) -> str:
    lines = content.splitlines()
    in_status_section = False

    for index, line in enumerate(lines):
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            if in_status_section:
                break
            in_status_section = current_section == "Status"
            continue

        if in_status_section and line.strip():
            lines[index] = status
            return "\n".join(lines) + "\n"

    return content


def replace_task_section_text(content: str, section_name: str, value: str) -> str:
    return replace_task_section(content, section_name, (value,))


def replace_task_section_items(
    content: str,
    section_name: str,
    items: tuple[str, ...],
) -> str:
    return replace_task_section(
        content,
        section_name,
        tuple(f"- {item}" for item in items),
    )


def replace_task_section(
    content: str,
    section_name: str,
    replacement_lines: tuple[str, ...],
) -> str:
    lines = content.splitlines()
    start_index = None
    end_index = len(lines)

    for index, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        current_section = line.removeprefix("## ").strip()
        if current_section == section_name:
            start_index = index
            continue
        if start_index is not None:
            end_index = index
            break

    if start_index is None:
        return content

    replacement = ["", *replacement_lines, ""]
    updated_lines = lines[: start_index + 1] + replacement + lines[end_index:]
    return "\n".join(updated_lines).rstrip() + "\n"


# --- Task-memory doctor diagnostics ---


@dataclass(frozen=True)
class TaskMemoryFinding:
    check: str
    severity: str
    message: str


@dataclass(frozen=True)
class TaskMemoryDiagnostics:
    findings: tuple[TaskMemoryFinding, ...]

    @property
    def has_errors(self) -> bool:
        return any(f.severity == "error" for f in self.findings)

    @property
    def has_warnings(self) -> bool:
        return any(f.severity == "warning" for f in self.findings)

    @property
    def clean(self) -> bool:
        return not self.findings


def diagnose_task_memory(root: HarnessPath) -> TaskMemoryDiagnostics:
    findings: list[TaskMemoryFinding] = []

    active_dir = root.join(Path("tasks") / "active")
    done_dir = root.join(Path("tasks") / "done")

    active_files = sorted(active_dir.glob("*.md")) if active_dir.is_dir() else []
    done_files = sorted(done_dir.glob("*.md")) if done_dir.is_dir() else []

    # Check 1: multiple active tasks
    if len(active_files) > 1:
        findings.append(TaskMemoryFinding(
            check="multiple_active_tasks",
            severity="warning",
            message=f"Found {len(active_files)} active task files; expected at most 1.",
        ))

    # Check 2: active task matches session
    session_path = root.join(Path(".pcae") / "session.json")
    if active_files and session_path.is_file():
        try:
            session_data = json.loads(session_path.read_text(encoding="utf-8"))
            session_task = session_data.get("active_task", {})
            session_task_id = session_task.get("id") if isinstance(session_task, dict) else None
            latest_active = read_active_task(active_files[-1])
            if session_task_id and session_task_id != latest_active.task_id:
                findings.append(TaskMemoryFinding(
                    check="session_task_mismatch",
                    severity="error",
                    message=(
                        f"Session references task '{session_task_id}' but latest active "
                        f"task is '{latest_active.task_id}'."
                    ),
                ))
        except (json.JSONDecodeError, OSError):
            pass

    # Check 3: done files missing from tasks/DONE.md
    done_md_path = root.join(DONE_RELATIVE_PATH)
    if done_files and done_md_path.is_file():
        done_md_content = done_md_path.read_text(encoding="utf-8")
        for done_file in done_files:
            task_id = done_file.stem
            if task_id not in done_md_content:
                task = read_task_summary(done_file, "done")
                if task.title not in done_md_content:
                    findings.append(TaskMemoryFinding(
                        check="done_file_missing_from_done_md",
                        severity="warning",
                        message=(
                            f"Task '{task.task_id}' ({task.title}) is in tasks/done/ "
                            "but not listed in tasks/DONE.md."
                        ),
                    ))

    # Check 4: TODO.md entries referring to completed tasks
    todo_path = root.join(TODO_RELATIVE_PATH)
    if done_files and todo_path.is_file():
        todo_content = todo_path.read_text(encoding="utf-8")
        done_titles = set()
        for done_file in done_files:
            task = read_task_summary(done_file, "done")
            done_titles.add(task.title)
        for title in done_titles:
            if title in todo_content:
                findings.append(TaskMemoryFinding(
                    check="todo_references_completed_task",
                    severity="warning",
                    message=f"tasks/TODO.md still references completed task: '{title}'.",
                ))

    # Check 5: done-status task files in tasks/active
    for active_file in active_files:
        task = read_active_task(active_file)
        if task.status == "done":
            findings.append(TaskMemoryFinding(
                check="done_status_in_active_folder",
                severity="error",
                message=(
                    f"Task '{task.task_id}' has status 'done' but is still in "
                    "tasks/active/."
                ),
            ))

    # Check 6: active-status task files in tasks/done
    for done_file in done_files:
        content = done_file.read_text(encoding="utf-8")
        status = read_task_section_text(content, "Status")
        if status == "active":
            task_id = read_task_section_text(content, "Task ID") or done_file.stem
            findings.append(TaskMemoryFinding(
                check="active_status_in_done_folder",
                severity="error",
                message=(
                    f"Task '{task_id}' has status 'active' but is in tasks/done/."
                ),
            ))

    return TaskMemoryDiagnostics(findings=tuple(findings))


REPAIRABLE_CHECKS: frozenset[str] = frozenset({
    "done_file_missing_from_done_md",
    "todo_references_completed_task",
    "done_status_in_active_folder",
})


@dataclass(frozen=True)
class TaskMemoryRepair:
    check: str
    action: str
    path: str


@dataclass(frozen=True)
class TaskMemoryRepairResult:
    pre_findings: tuple[TaskMemoryFinding, ...]
    repairs: tuple[TaskMemoryRepair, ...]
    skipped: tuple[TaskMemoryFinding, ...]
    post_findings: tuple[TaskMemoryFinding, ...]


def repair_task_memory(root: HarnessPath, dry_run: bool = False) -> TaskMemoryRepairResult:
    pre = diagnose_task_memory(root)
    repairs: list[TaskMemoryRepair] = []
    skipped: list[TaskMemoryFinding] = []

    for finding in pre.findings:
        if finding.check not in REPAIRABLE_CHECKS:
            skipped.append(finding)
            continue

        if dry_run:
            repairs.append(TaskMemoryRepair(
                check=finding.check,
                action="would_repair",
                path=_repair_path_for_finding(root, finding),
            ))
            continue

        repair = _apply_repair(root, finding)
        if repair is not None:
            repairs.append(repair)
        else:
            skipped.append(finding)

    post = pre if dry_run else diagnose_task_memory(root)

    return TaskMemoryRepairResult(
        pre_findings=pre.findings,
        repairs=tuple(repairs),
        skipped=tuple(skipped),
        post_findings=post.findings,
    )


def _repair_path_for_finding(root: HarnessPath, finding: TaskMemoryFinding) -> str:
    if finding.check == "done_file_missing_from_done_md":
        return DONE_RELATIVE_PATH.as_posix()
    if finding.check == "todo_references_completed_task":
        return TODO_RELATIVE_PATH.as_posix()
    if finding.check == "done_status_in_active_folder":
        task_id = _extract_task_id_from_message(finding.message)
        if task_id:
            return f"tasks/done/{task_id}.md"
    return ""


def _apply_repair(root: HarnessPath, finding: TaskMemoryFinding) -> TaskMemoryRepair | None:
    if finding.check == "done_file_missing_from_done_md":
        return _repair_done_file_missing(root, finding)
    if finding.check == "todo_references_completed_task":
        return _repair_todo_references_completed(root, finding)
    if finding.check == "done_status_in_active_folder":
        return _repair_done_status_in_active(root, finding)
    return None


def _repair_done_file_missing(root: HarnessPath, finding: TaskMemoryFinding) -> TaskMemoryRepair | None:
    task_id = _extract_task_id_from_message(finding.message)
    title = _extract_title_from_message(finding.message)
    if not task_id or not title:
        return None
    line = f"- {title} ({task_id})"
    ensure_bullet_in_section(
        root.join(DONE_RELATIVE_PATH),
        "Done",
        "Completed",
        line,
    )
    return TaskMemoryRepair(
        check="done_file_missing_from_done_md",
        action="appended_to_done_md",
        path=DONE_RELATIVE_PATH.as_posix(),
    )


def _repair_todo_references_completed(root: HarnessPath, finding: TaskMemoryFinding) -> TaskMemoryRepair | None:
    title = _extract_todo_title_from_message(finding.message)
    if not title:
        return None
    path = root.join(TODO_RELATIVE_PATH)
    if not path.is_file():
        return None
    original = path.read_text(encoding="utf-8")
    updated = remove_exact_bullets(original, {title})
    if updated == original:
        return None
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)
    return TaskMemoryRepair(
        check="todo_references_completed_task",
        action="removed_from_todo_md",
        path=TODO_RELATIVE_PATH.as_posix(),
    )


def _repair_done_status_in_active(root: HarnessPath, finding: TaskMemoryFinding) -> TaskMemoryRepair | None:
    task_id = _extract_task_id_from_message(finding.message)
    if not task_id:
        return None
    active_path = root.join(Path("tasks") / "active" / f"{task_id}.md")
    if not active_path.is_file():
        return None
    done_path = root.join(Path("tasks") / "done" / f"{task_id}.md")
    done_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.replace(done_path)
    return TaskMemoryRepair(
        check="done_status_in_active_folder",
        action="moved_to_done",
        path=f"tasks/done/{task_id}.md",
    )


def _extract_task_id_from_message(message: str) -> str | None:
    match = re.search(r"Task '([^']+)'", message)
    return match.group(1) if match else None


def _extract_title_from_message(message: str) -> str | None:
    match = re.search(r"\(([^)]+)\) is in tasks/done/", message)
    return match.group(1) if match else None


def _extract_todo_title_from_message(message: str) -> str | None:
    match = re.search(r"completed task: '([^']+)'", message)
    return match.group(1) if match else None
