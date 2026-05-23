from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from pcae.core.git_status import GitChange, read_git_branch, read_git_changes
from pcae.core.paths import HarnessPath
from pcae.core.tasks import find_latest_active_task


SESSION_RELATIVE_PATH = Path(".pcae") / "session.json"


@dataclass(frozen=True)
class SessionSnapshot:
    relative_path: Path
    data: dict


@dataclass(frozen=True)
class SessionUpdate:
    objective: str | None = None
    completed_step: str | None = None
    next_step: str | None = None
    blocker: str | None = None
    warning: str | None = None
    note: str | None = None


def read_session_snapshot(root: HarnessPath) -> SessionSnapshot | None:
    target = root.join(SESSION_RELATIVE_PATH)
    if not target.is_file():
        return None

    return SessionSnapshot(
        relative_path=SESSION_RELATIVE_PATH,
        data=json.loads(target.read_text(encoding="utf-8")),
    )


def write_session_snapshot(
    root: HarnessPath,
    created_at: datetime | None = None,
) -> SessionSnapshot:
    timestamp = created_at or datetime.now(timezone.utc)
    data = build_session_snapshot(root, timestamp)
    return write_session_data(root, data)


def update_session_snapshot(
    root: HarnessPath,
    update: SessionUpdate,
) -> SessionSnapshot:
    snapshot = read_session_snapshot(root)
    if snapshot is None:
        snapshot = write_session_snapshot(root)

    data = dict(snapshot.data)
    if update.objective is not None:
        data["current_objective"] = update.objective
    if update.completed_step is not None:
        data["last_completed_step"] = update.completed_step
    if update.next_step is not None:
        data["next_recommended_step"] = update.next_step
    append_session_value(data, "blockers", update.blocker)
    append_session_value(data, "warnings", update.warning)
    append_session_value(data, "architectural_notes", update.note)

    return write_session_data(root, data)


def write_session_data(root: HarnessPath, data: dict) -> SessionSnapshot:
    target = root.join(SESSION_RELATIVE_PATH)

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")

    return SessionSnapshot(relative_path=SESSION_RELATIVE_PATH, data=data)


def append_session_value(data: dict, key: str, value: str | None) -> None:
    if value is None:
        return

    existing = data.get(key)
    if not isinstance(existing, list):
        existing = []
    existing.append(value)
    data[key] = existing


def build_session_snapshot(root: HarnessPath, timestamp: datetime) -> dict:
    active_task = find_latest_active_task(root)
    changes = read_git_changes(root)

    return {
        "active_task": None
        if active_task is None
        else {
            "id": active_task.task_id,
            "title": active_task.title,
        },
        "architectural_notes": [],
        "blockers": [],
        "current_objective": "",
        "git": {
            "branch": read_git_branch(root),
            "changed_files": [
                {
                    "path": change.path.as_posix(),
                    "status": change.status,
                }
                for change in changes
            ],
            "status_summary": summarize_git_changes(changes),
        },
        "last_completed_step": "",
        "next_recommended_step": "",
        "timestamp": timestamp.isoformat(),
        "warnings": [],
    }


def summarize_git_changes(changes: tuple[GitChange, ...]) -> str:
    if not changes:
        return "clean"
    if len(changes) == 1:
        return "1 changed file"
    return f"{len(changes)} changed files"
