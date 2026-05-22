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
