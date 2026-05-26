from __future__ import annotations

import argparse
import json

from pcae.core.paths import HarnessPath
from pcae.core.provenance import (
    PROVENANCE_HISTORY_RELATIVE_PATH,
    append_provenance_event,
    read_provenance_history,
    read_provenance_status,
    write_provenance_export,
)


def run_provenance_status(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    status = read_provenance_status(root)

    print(f"Provenance history: {PROVENANCE_HISTORY_RELATIVE_PATH.as_posix()}")
    if status.exists:
        print("File: present")
        print(f"Event count: {status.event_count}")
        if status.latest_summary is not None:
            print(f"Latest event: {status.latest_summary}")
        else:
            print("Latest event: none")
    else:
        print("File: absent")
        print("Event count: 0")
        print("Latest event: none")
    return 0


def run_provenance_export(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    bundle = write_provenance_export(root)

    if args.json:
        print(
            json.dumps(
                {
                    "active_task": bundle.data["active_task"],
                    "event_count": bundle.data["event_count"],
                    "exported_at": bundle.data["exported_at"],
                    "git_branch": bundle.data["git_branch"],
                    "path": bundle.relative_path.as_posix(),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    print(f"Wrote provenance export: {bundle.relative_path.as_posix()}")
    print(f"Event count: {bundle.data['event_count']}")
    return 0


def run_provenance_record(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    event = append_provenance_event(root, args.event_type, args.summary)
    print(f"Recorded: [{event.timestamp}] {event.event_type}: {event.summary}")
    return 0


def run_provenance_history(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    history = read_provenance_history(root)

    if args.json:
        print(
            json.dumps(
                [event.to_dict() for event in history.events],
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    print(f"Provenance history: {PROVENANCE_HISTORY_RELATIVE_PATH.as_posix()}")
    print(f"Event count: {len(history.events)}")
    if not history.events:
        print("No provenance events recorded.")
        return 0

    print("")
    for event in history.events:
        print(f"  [{event.timestamp}] {event.event_type}: {event.summary}")
        if event.agent_id is not None:
            print(f"    agent: {event.agent_id}")
        if event.active_task is not None:
            task_id = event.active_task.get("id", "unknown")
            print(f"    task: {task_id}")
        if event.git_branch is not None:
            print(f"    branch: {event.git_branch}")
    return 0
