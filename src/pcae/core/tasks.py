from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    override_protected_files: tuple[str, ...]


def create_task_contract(
    root: HarnessPath,
    title: str,
    created_at: datetime | None = None,
) -> TaskContract:
    timestamp = created_at or datetime.now().astimezone()
    slug = slugify_title(title)
    task_id = f"{timestamp:%Y%m%d-%H%M}-{slug}"
    relative_path = Path("tasks") / "active" / f"{task_id}.md"
    content = render_task_contract(
        task_id=task_id,
        title=title,
        created_at=timestamp,
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


def slugify_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug or "task"


def render_task_contract(task_id: str, title: str, created_at: datetime) -> str:
    return f"""# Task Contract

## Task ID

{task_id}

## Title

{title}

## Status

active

## Mode

implementation

## Goal

TBD

## Allowed Files

- TBD

## Forbidden Files

- TBD

## Forbidden Changes

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

{created_at.isoformat()}
"""


def find_latest_active_task(root: HarnessPath) -> ActiveTask | None:
    active_dir = root.join(Path("tasks") / "active")
    if not active_dir.is_dir():
        return None

    task_files = sorted(active_dir.glob("*.md"))
    if not task_files:
        return None
    return read_active_task(task_files[-1])


def read_active_task(task_path: Path) -> ActiveTask:
    content = task_path.read_text(encoding="utf-8")
    return ActiveTask(
        path=task_path,
        task_id=read_task_section_text(content, "Task ID") or task_path.stem,
        title=read_task_section_text(content, "Title") or "Untitled task",
        allowed_files=read_task_section_items_from_text(content, "Allowed Files"),
        forbidden_files=read_task_section_items_from_text(content, "Forbidden Files"),
        override_protected_files=read_task_section_items_from_text(
            content,
            "Override Protected Files",
        ),
    )


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
