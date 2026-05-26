from __future__ import annotations

import argparse
import json
from typing import Any

from pcae.core.agent import acquire_agent_lock
from pcae.core.architecture import (
    read_architecture_history_summary,
    write_architecture_history_snapshot,
)
from pcae.core.check import run_checks
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.provenance import (
    ProvenanceEvent,
    ProvenanceSession,
    append_provenance_event,
    build_provenance_sessions,
    build_provenance_timeline,
    find_active_session,
)
from pcae.core.session import (
    SessionUpdate,
    read_session_snapshot,
    update_session_snapshot,
    write_session_snapshot,
)


def run_session_write(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    snapshot = write_session_snapshot(root)

    print(f"Wrote session snapshot: {snapshot.relative_path.as_posix()}")
    return 0


def run_session_read(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    snapshot = read_session_snapshot(root)
    if snapshot is None:
        print("No session snapshot found at .pcae/session.json.")
        return 1

    print_session_snapshot(snapshot.data)
    return 0


def run_session_update(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    snapshot = update_session_snapshot(
        root,
        SessionUpdate(
            objective=args.objective,
            completed_step=args.completed_step,
            next_step=args.next_step,
            blocker=args.blocker,
            warning=args.warning,
            note=args.note,
        ),
    )

    print(f"Updated session snapshot: {snapshot.relative_path.as_posix()}")
    return 0


def run_session_end(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    check_result = run_checks(root)
    if not check_result.passed:
        print("Session end stopped: pcae check failed.")
        for violation in check_result.violations:
            print(f"  - {violation.text}")
        return 1

    session_snapshot = write_session_snapshot(root)
    architecture_snapshot = write_architecture_history_snapshot(root, check_result)

    print("Session end complete.")
    print_session_end_summary(session_snapshot.data, len(architecture_snapshot.entries))
    return 0


def run_session_bootstrap(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()

    try:
        lock = acquire_agent_lock(root, args.agent_id)
    except ValueError as error:
        print(str(error))
        return 1

    append_provenance_event(
        root,
        "agent_acquired",
        f"Agent lock acquired by {args.agent_id}",
        agent_id=args.agent_id,
    )

    health_data = build_health_data(root)
    health_status: str = health_data["overall_status"]
    check_passed = health_status == "healthy"

    active_task = lock.data.get("active_task")
    if not isinstance(active_task, dict):
        active_task = None

    sessions = build_provenance_sessions(root)
    current_session = find_active_session(sessions)
    timeline = build_provenance_timeline(root)
    latest_event = timeline.latest_event
    ready = check_passed

    if args.json:
        print(
            json.dumps(
                {
                    "active_task": active_task,
                    "agent_id": args.agent_id,
                    "check_status": "passed" if check_passed else "failed",
                    "current_session": _session_summary(current_session),
                    "health_status": health_status,
                    "latest_event": _event_summary(latest_event),
                    "provenance_event_count": timeline.event_count,
                    "ready": ready,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if ready else 1

    print("Session bootstrap.")
    print(f"Agent: {args.agent_id}")
    print(f"Health: {health_status}")
    print(f"Check: {'passed' if check_passed else 'failed'}")
    for v in health_data["violations"]:
        print(f"  - {v}")
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")
    if current_session is None:
        print("Current session: none")
    else:
        status = "active" if current_session.active else "closed"
        print(f"Current session: {current_session.session_id} ({status})")
    print(f"Provenance events: {timeline.event_count}")
    if latest_event is not None:
        print(f"Latest event: {latest_event.summary}")
    else:
        print("Latest event: none")
    print(f"Ready: {'yes' if ready else 'no'}")
    return 0 if ready else 1


def _session_summary(session: ProvenanceSession | None) -> dict | None:
    if session is None:
        return None
    return {
        "active": session.active,
        "agent_id": session.agent_id,
        "ended_at": session.ended_at,
        "event_count": session.event_count,
        "session_id": session.session_id,
        "started_at": session.started_at,
    }


def _event_summary(event: ProvenanceEvent | None) -> dict | None:
    if event is None:
        return None
    return {
        "agent_id": event.agent_id,
        "event_type": event.event_type,
        "summary": event.summary,
        "timestamp": event.timestamp,
    }


def run_session_start(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    check_result = run_checks(root)
    if not check_result.passed:
        print("Session start stopped: pcae check failed.")
        for violation in check_result.violations:
            print(f"  - {violation.text}")
        return 1

    session_snapshot = read_session_snapshot(root)
    try:
        architecture_summary = read_architecture_history_summary(root)
    except ValueError as error:
        architecture_summary = None
        architecture_message = str(error)
    else:
        architecture_message = None

    print("Session start summary.")
    if session_snapshot is None:
        print("No session snapshot found at .pcae/session.json.")
    else:
        print_session_start_snapshot(session_snapshot.data)

    if architecture_summary is None:
        print(architecture_message)
    else:
        latest = architecture_summary.latest
        print(f"Architecture history entries: {len(architecture_summary.entries)}")
        print(f"Latest enforcement mode: {latest.get('enforcement_mode', 'unknown')}")
        print(
            "Latest session continuity: "
            f"{latest.get('session_continuity', 'unknown')}"
        )
    return 0


def print_session_start_snapshot(data: dict) -> None:
    active_task = data.get("active_task")
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")

    git = data.get("git", {})
    print(f"Git branch: {git.get('branch', 'unknown')}")
    print(f"Git status: {git.get('status_summary', 'unknown')}")
    print(f"Current objective: {data.get('current_objective', '')}")
    print(f"Last completed step: {data.get('last_completed_step', '')}")
    print(f"Next recommended step: {data.get('next_recommended_step', '')}")
    print_list("Blockers", data.get("blockers", []))
    print_list("Warnings", data.get("warnings", []))


def print_session_end_summary(data: dict, architecture_history_count: int) -> None:
    active_task = data.get("active_task")
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")

    git = data.get("git", {})
    print(f"Git status: {git.get('status_summary', 'unknown')}")
    print(f"Architecture history entries: {architecture_history_count}")
    next_step = data.get("next_recommended_step") or "none"
    print(f"Next recommended step: {next_step}")


def print_session_snapshot(data: dict) -> None:
    active_task = data.get("active_task")
    print("Session snapshot:")
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")

    git = data.get("git", {})
    print(f"Git branch: {git.get('branch', 'unknown')}")
    print(f"Git status: {git.get('status_summary', 'unknown')}")
    print(f"Current objective: {data.get('current_objective', '')}")
    print(f"Last completed step: {data.get('last_completed_step', '')}")
    print(f"Next recommended step: {data.get('next_recommended_step', '')}")
    print_list("Blockers", data.get("blockers", []))
    print_list("Warnings", data.get("warnings", []))
    print_list("Architectural notes", data.get("architectural_notes", []))


def print_list(title: str, values: list[Any]) -> None:
    print(f"{title}:")
    if not values:
        print("  none")
        return

    for value in values:
        print(f"  - {value}")
