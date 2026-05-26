from __future__ import annotations

import argparse
import json

from pcae.core.check import run_checks
from pcae.core.paths import HarnessPath
from pcae.core.phase import complete_phase, handoff_phase, start_phase


def run_phase_complete(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = complete_phase(root, args.summary)

    print("Phase complete.")
    print(f"Summary: {result.summary}")
    print(f"Provenance events: {result.provenance_event_count}")
    if result.agent_released:
        print(f"Agent lock: released (by {result.agent_id})")
    else:
        print("Agent lock: none")
    return 0


def run_phase_handoff(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = handoff_phase(root, args.summary, args.next_agent)

    if args.json:
        print(
            json.dumps(
                {
                    "check_status": "passed" if result.check_passed else "failed",
                    "health_status": result.health_status,
                    "next_agent": result.next_agent,
                    "provenance_event_count": result.provenance_event_count,
                    "released_agent": result.released_agent,
                    "summary": result.summary,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if result.next_lock_acquired else 1

    print("Phase handoff.")
    print(f"Summary: {result.summary}")
    print(f"Health: {result.health_status}")
    print(f"Check: {'passed' if result.check_passed else 'failed'}")
    for v in result.violations:
        print(f"  - {v}")
    print(f"Provenance events: {result.provenance_event_count}")
    print(f"Released agent: {result.released_agent or 'none'}")
    print(f"Next agent: {result.next_agent}")
    if result.next_lock_acquired:
        print(f"Agent lock: acquired by {result.next_agent}")
    else:
        print("Agent lock: not acquired (lock already held)")

    print()
    print("Restart commands:")
    if not result.next_lock_acquired:
        print(f"  pcae agent acquire --agent-id {result.next_agent}")
    print("  pcae health")
    print("  pcae check")
    print("  pcae provenance timeline")

    return 0 if result.next_lock_acquired else 1


def run_phase_start(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()

    check_result = run_checks(root)
    if not check_result.passed:
        print("Phase start stopped: pcae check failed.")
        for v in check_result.violations:
            print(f"  - {v.text}")
        return 1

    try:
        result = start_phase(root, args.agent_id)
    except ValueError as error:
        print(str(error))
        return 1

    print("Phase start.")
    print("Check: passed")

    active_task = result.active_task
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")

    timeline = result.timeline
    print(f"Provenance events: {timeline.event_count}")
    if timeline.latest_event is not None:
        print(f"Latest event: {timeline.latest_event.summary}")
    else:
        print("Latest event: none")

    return 0
