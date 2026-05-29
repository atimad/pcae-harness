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
PROVENANCE_EXPORTS_RELATIVE_PATH = Path(".pcae") / "provenance-exports"
_ARCHITECTURE_HISTORY_PATH = Path(".pcae") / "architecture-history.json"

HANDOFF_ADVISORY = "Handoff reporting is advisory; no handoff state is modified."


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
class ProvenanceSession:
    session_id: str
    active: bool
    agent_id: str | None
    event_count: int
    started_at: str
    ended_at: str | None
    events: tuple[ProvenanceEvent, ...]

    def to_dict(self) -> dict:
        return {
            "active": self.active,
            "agent_id": self.agent_id,
            "ended_at": self.ended_at,
            "event_count": self.event_count,
            "events": [e.to_dict() for e in self.events],
            "session_id": self.session_id,
            "started_at": self.started_at,
        }


@dataclass(frozen=True)
class ProvenanceTimeline:
    event_count: int
    agent_ids: tuple[str, ...]
    event_types: tuple[str, ...]
    latest_event: ProvenanceEvent | None
    timeline: tuple[ProvenanceEvent, ...]


@dataclass(frozen=True)
class ProvenanceExportBundle:
    relative_path: Path
    data: dict


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
    agent_id: str | None = None,
) -> ProvenanceEvent:
    timestamp = created_at or datetime.now(timezone.utc)
    if agent_id is None:
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
    agent_id: str | None = None,
) -> ProvenanceEvent:
    event = build_provenance_event(root, event_type, summary, created_at, agent_id)
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


def filter_events(
    events: tuple[ProvenanceEvent, ...],
    event_type: str | None = None,
    agent_id: str | None = None,
) -> tuple[ProvenanceEvent, ...]:
    result = events
    if event_type is not None:
        result = tuple(e for e in result if e.event_type == event_type)
    if agent_id is not None:
        result = tuple(e for e in result if e.agent_id == agent_id)
    return result


def build_provenance_timeline(root: HarnessPath) -> ProvenanceTimeline:
    history = read_provenance_history(root)
    events = history.events
    agent_ids = tuple(sorted({e.agent_id for e in events if e.agent_id is not None}))
    event_types = tuple(sorted({e.event_type for e in events}))
    return ProvenanceTimeline(
        event_count=len(events),
        agent_ids=agent_ids,
        event_types=event_types,
        latest_event=events[-1] if events else None,
        timeline=events,
    )


def write_provenance_export(
    root: HarnessPath,
    exported_at: datetime | None = None,
) -> ProvenanceExportBundle:
    timestamp = exported_at or datetime.now(timezone.utc)
    data = build_provenance_export_data(root, timestamp)
    relative_path = PROVENANCE_EXPORTS_RELATIVE_PATH / (
        f"provenance-export-{timestamp.strftime('%Y%m%d-%H%M%S')}.json"
    )
    target = root.join(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")
    return ProvenanceExportBundle(relative_path=relative_path, data=data)


def build_provenance_export_data(root: HarnessPath, timestamp: datetime) -> dict:
    events = _read_raw_events(root)
    active_task_obj = find_latest_active_task(root)
    active_task = (
        {"id": active_task_obj.task_id, "title": active_task_obj.title}
        if active_task_obj is not None
        else None
    )
    return {
        "active_task": active_task,
        "event_count": len(events),
        "events": list(events),
        "exported_at": timestamp.isoformat(),
        "git_branch": _safe_git_branch(root),
    }


def build_provenance_sessions(root: HarnessPath) -> tuple[ProvenanceSession, ...]:
    history = read_provenance_history(root)
    sessions: list[ProvenanceSession] = []
    current: list[ProvenanceEvent] = []
    in_session = False

    for event in history.events:
        if event.event_type == "agent_acquired":
            current = [event]
            in_session = True
        elif in_session:
            current.append(event)
            if event.event_type == "agent_released":
                sessions.append(_make_session(current, active=False))
                current = []
                in_session = False

    if in_session and current:
        sessions.append(_make_session(current, active=True))

    return tuple(sessions)


def find_active_session(
    sessions: tuple[ProvenanceSession, ...],
) -> ProvenanceSession | None:
    for session in sessions:
        if session.active:
            return session
    return None


@dataclass(frozen=True)
class HandoffRecord:
    source_agent: str | None
    target_agent: str | None
    timestamp: str
    phase: str | None
    active_task: dict | None
    continuity_verified: bool
    architecture_memory_present: bool
    summary: str | None
    warnings: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "active_task": self.active_task,
            "architecture_memory_present": self.architecture_memory_present,
            "continuity_verified": self.continuity_verified,
            "phase": self.phase,
            "source_agent": self.source_agent,
            "summary": self.summary,
            "target_agent": self.target_agent,
            "timestamp": self.timestamp,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class HandoffHistory:
    handoff_count: int
    handoffs: tuple[HandoffRecord, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "advisory": self.advisory,
            "handoff_count": self.handoff_count,
            "handoffs": [h.to_dict() for h in self.handoffs],
        }


def build_handoff_history(root: HarnessPath) -> HandoffHistory:
    """Return a read-only derived handoff history from provenance events."""
    history = read_provenance_history(root)
    arch_present = _has_architecture_memory(root)
    records = _extract_handoff_records(history.events, arch_present)
    return HandoffHistory(
        handoff_count=len(records),
        handoffs=records,
        advisory=HANDOFF_ADVISORY,
    )


def _has_architecture_memory(root: HarnessPath) -> bool:
    target = root.join(_ARCHITECTURE_HISTORY_PATH)
    if not target.is_file():
        return False
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return isinstance(data, list) and len(data) > 0


def _extract_handoff_records(
    events: tuple[ProvenanceEvent, ...],
    architecture_memory_present: bool,
) -> tuple[HandoffRecord, ...]:
    records: list[HandoffRecord] = []

    for i, event in enumerate(events):
        if event.event_type != "agent_released":
            continue

        # Look for an agent_acquired within the next few events.
        acquired_event: ProvenanceEvent | None = None
        gap = 0
        for j in range(i + 1, min(i + 4, len(events))):
            if events[j].event_type == "agent_acquired":
                acquired_event = events[j]
                gap = j - (i + 1)
                break

        if acquired_event is None:
            continue

        # Find the most recent phase_completed before this release.
        phase_completed: ProvenanceEvent | None = None
        for k in range(i - 1, -1, -1):
            if events[k].event_type == "phase_completed":
                phase_completed = events[k]
                break

        source_agent = event.agent_id
        target_agent = acquired_event.agent_id

        active_task: dict | None = None
        if phase_completed is not None and isinstance(phase_completed.active_task, dict):
            active_task = phase_completed.active_task
        elif isinstance(event.active_task, dict):
            active_task = event.active_task

        summary = phase_completed.summary if phase_completed is not None else None

        phase: str | None = None
        if isinstance(active_task, dict):
            task_id = active_task.get("id")
            if isinstance(task_id, str) and task_id:
                phase = task_id

        continuity_verified = gap == 0

        warnings: list[str] = []
        if source_agent is None:
            warnings.append("Source agent ID missing in agent_released event.")
        if target_agent is None:
            warnings.append("Target agent ID missing in agent_acquired event.")
        if not _is_valid_timestamp(event.timestamp):
            warnings.append(f"Timestamp could not be parsed: {event.timestamp!r}.")

        records.append(
            HandoffRecord(
                source_agent=source_agent,
                target_agent=target_agent,
                timestamp=event.timestamp,
                phase=phase,
                active_task=active_task,
                continuity_verified=continuity_verified,
                architecture_memory_present=architecture_memory_present,
                summary=summary,
                warnings=tuple(warnings),
            )
        )

    # Return most recent first.
    return tuple(reversed(records))


def _is_valid_timestamp(ts: str) -> bool:
    try:
        datetime.fromisoformat(ts)
        return True
    except (ValueError, TypeError):
        return False


def _make_session(events: list[ProvenanceEvent], active: bool) -> ProvenanceSession:
    start = events[0]
    agent_id = start.agent_id
    ended_at = events[-1].timestamp if not active else None
    return ProvenanceSession(
        session_id=_session_id_from_timestamp(start.timestamp),
        active=active,
        agent_id=agent_id,
        event_count=len(events),
        started_at=start.timestamp,
        ended_at=ended_at,
        events=tuple(events),
    )


def _session_id_from_timestamp(ts: str) -> str:
    date_time = ts[:19]
    date_part = date_time[:10].replace("-", "")
    time_part = date_time[11:].replace(":", "")
    return f"session-{date_part}-{time_part}"


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
