from __future__ import annotations

from dataclasses import dataclass

from pcae.core.agent import acquire_agent_lock, read_agent_lock, release_agent_lock
from pcae.core.health import build_health_data
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


@dataclass(frozen=True)
class PhaseHandoffResult:
    summary: str
    released_agent: str | None
    next_agent: str
    health_status: str
    check_passed: bool
    provenance_event_count: int
    next_lock_acquired: bool
    violations: tuple[str, ...]


def handoff_phase(
    root: HarnessPath,
    summary: str,
    next_agent: str,
) -> PhaseHandoffResult:
    # Capture current agent before any mutations so provenance is attributed correctly.
    lock = read_agent_lock(root)
    released_agent = lock.agent_id if lock is not None else None

    # Record phase completion while the current agent lock is still held.
    append_provenance_event(root, "phase_completed", summary)

    # Run governance validation (health + check semantics) before releasing.
    from pcae.core.health import is_healthy

    health_data = build_health_data(root)
    health_status: str = health_data["overall_status"]
    check_passed = is_healthy(health_data)
    violations = tuple(health_data["violations"])

    # Release current lock and record agent_released.
    if lock is not None:
        result = release_agent_lock(root, released_agent)
        if result.released:
            append_provenance_event(
                root,
                "agent_released",
                f"Agent lock released by {released_agent}",
                agent_id=released_agent,
            )

    # Acquire the next agent's lock and record agent_acquired.
    # This is the deterministic reacquire step: releasing and immediately
    # acquiring transfers governance custody to next_agent in one atomic
    # provenance sequence.
    next_lock_acquired = False
    try:
        acquire_agent_lock(root, next_agent)
        append_provenance_event(
            root,
            "agent_acquired",
            f"Agent lock acquired by {next_agent}",
            agent_id=next_agent,
        )
        next_lock_acquired = True
    except ValueError:
        pass

    timeline = build_provenance_timeline(root)
    return PhaseHandoffResult(
        summary=summary,
        released_agent=released_agent,
        next_agent=next_agent,
        health_status=health_status,
        check_passed=check_passed,
        provenance_event_count=timeline.event_count,
        next_lock_acquired=next_lock_acquired,
        violations=violations,
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
