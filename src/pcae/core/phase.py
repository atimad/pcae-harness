from __future__ import annotations

from dataclasses import dataclass

from pcae.core.agent import acquire_agent_lock, read_agent_lock, release_agent_lock
from pcae.core.paths import HarnessPath
from pcae.core.provenance import (
    ProvenanceTimeline,
    append_provenance_event,
    build_provenance_timeline,
)


@dataclass(frozen=True)
class PhaseCompleteResult:
    summary: str
    agent_id: str | None
    agent_released: bool
    provenance_event_count: int


@dataclass(frozen=True)
class PhaseStartResult:
    agent_id: str
    active_task: dict | None
    timeline: ProvenanceTimeline


def complete_phase(root: HarnessPath, summary: str) -> PhaseCompleteResult:
    lock = read_agent_lock(root)
    agent_id = lock.agent_id if lock is not None else None

    append_provenance_event(root, "phase_completed", summary)

    agent_released = False
    if lock is not None:
        result = release_agent_lock(root, agent_id)
        if result.released:
            append_provenance_event(
                root,
                "agent_released",
                f"Agent lock released by {agent_id}",
                agent_id=agent_id,
            )
            agent_released = True

    timeline = build_provenance_timeline(root)
    return PhaseCompleteResult(
        summary=summary,
        agent_id=agent_id,
        agent_released=agent_released,
        provenance_event_count=timeline.event_count,
    )


def start_phase(root: HarnessPath, agent_id: str) -> PhaseStartResult:
    lock = acquire_agent_lock(root, agent_id)
    append_provenance_event(
        root,
        "agent_acquired",
        f"Agent lock acquired by {agent_id}",
        agent_id=agent_id,
    )
    active_task = lock.data.get("active_task")
    timeline = build_provenance_timeline(root)
    return PhaseStartResult(
        agent_id=agent_id,
        active_task=active_task if isinstance(active_task, dict) else None,
        timeline=timeline,
    )
