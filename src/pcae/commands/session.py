from __future__ import annotations

import argparse
from typing import Any

from pcae.core.paths import HarnessPath
from pcae.core.session import read_session_snapshot, write_session_snapshot


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
