from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.core.agent import read_agent_lock
from pcae.core.git_status import read_git_branch
from pcae.core.paths import HarnessPath
from pcae.core.tasks import find_latest_active_task


PROVENANCE_HISTORY_RELATIVE_PATH = Path(".pcae") / "provenance-history.json"


@dataclass(frozen=True)
class ProvenanceEvent:
    timestamp: str
    event_type: str
    agent_id: str | None
    active_task: dict | None
    git_branch: str | None
    summary: str

    def to_dict(self) -> dict:
        return {
            "active_task": self.active_task,
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "git_branch": self.git_branch,
            "summary": self.summary,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProvenanceEvent:
        active_task = data.get("active_task")
        return cls(
            timestamp=_str(data.get("timestamp")),
            event_type=_str(data.get("event_type")),
            agent_id=_optional_str(data.get("agent_id")),
            active_task=active_task if isinstance(active_task, dict) else None,
            git_branch=_optional_str(data.get("git_branch")),
            summary=_str(data.get("summary")),
        )


@dataclass(frozen=True)
class ProvenanceStatus:
    exists: bool
    event_count: int
    latest_summary: str | None
    relative_path: Path


@dataclass(frozen=True)
class ProvenanceHistory:
    relative_path: Path
    events: tuple[ProvenanceEvent, ...]


def build_provenance_event(
    root: HarnessPath,
    event_type: str,
    summary: str,
    created_at: datetime | None = None,
) -> ProvenanceEvent:
    timestamp = created_at or datetime.now(timezone.utc)
    lock = read_agent_lock(root)
    agent_id = lock.agent_id if lock is not None else None
    active_task_obj = find_latest_active_task(root)
    active_task = (
        {"id": active_task_obj.task_id, "title": active_task_obj.title}
        if active_task_obj is not None
        else None
    )
    return ProvenanceEvent(
        timestamp=timestamp.isoformat(),
        event_type=event_type,
        agent_id=agent_id or None,
        active_task=active_task,
        git_branch=_safe_git_branch(root),
        summary=summary,
    )


def append_provenance_event(
    root: HarnessPath,
    event_type: str,
    summary: str,
    created_at: datetime | None = None,
) -> ProvenanceEvent:
    event = build_provenance_event(root, event_type, summary, created_at)
    existing = _read_raw_events(root)
    entries = list(existing) + [event.to_dict()]
    target = root.join(PROVENANCE_HISTORY_RELATIVE_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(entries, file, indent=2, sort_keys=True)
        file.write("\n")
    return event


def read_provenance_status(root: HarnessPath) -> ProvenanceStatus:
    target = root.join(PROVENANCE_HISTORY_RELATIVE_PATH)
    if not target.is_file():
        return ProvenanceStatus(
            exists=False,
            event_count=0,
            latest_summary=None,
            relative_path=PROVENANCE_HISTORY_RELATIVE_PATH,
        )
    events = _read_raw_events(root)
    latest_summary: str | None = None
    if events:
        last = events[-1]
        value = last.get("summary")
        if isinstance(value, str) and value:
            latest_summary = value
    return ProvenanceStatus(
        exists=True,
        event_count=len(events),
        latest_summary=latest_summary,
        relative_path=PROVENANCE_HISTORY_RELATIVE_PATH,
    )


def read_provenance_history(root: HarnessPath) -> ProvenanceHistory:
    events = tuple(
        ProvenanceEvent.from_dict(entry) for entry in _read_raw_events(root)
    )
    return ProvenanceHistory(
        relative_path=PROVENANCE_HISTORY_RELATIVE_PATH,
        events=events,
    )


def _read_raw_events(root: HarnessPath) -> tuple[dict, ...]:
    target = root.join(PROVENANCE_HISTORY_RELATIVE_PATH)
    if not target.is_file():
        return ()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ()
    if not isinstance(data, list):
        return ()
    return tuple(entry for entry in data if isinstance(entry, dict))


def _safe_git_branch(root: HarnessPath) -> str | None:
    try:
        return read_git_branch(root)
    except subprocess.CalledProcessError:
        return None


def _str(value: object) -> str:
    return value if isinstance(value, str) else ""


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
