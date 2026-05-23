from __future__ import annotations

import argparse

from pcae.core.architecture import (
    read_architecture_history_summary,
    write_architecture_history_snapshot,
)
from pcae.core.check import run_checks
from pcae.core.paths import HarnessPath


def run_architecture_snapshot(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    check_result = run_checks(root)
    snapshot = write_architecture_history_snapshot(root, check_result)

    print(f"Wrote architecture history: {snapshot.relative_path.as_posix()}")
    print(f"Entries: {len(snapshot.entries)}")
    return 0


def run_architecture_history(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        summary = read_architecture_history_summary(root)
    except ValueError as error:
        print(error)
        return 1

    latest = summary.latest
    active_task = latest.get("active_task")

    print(f"Architecture history: {summary.relative_path.as_posix()}")
    print(f"Total entries: {len(summary.entries)}")
    print(f"Latest snapshot: {latest.get('timestamp', 'unknown')}")
    if isinstance(active_task, dict):
        print(f"Latest active task: {active_task.get('id', 'unknown')}")
        print(f"Latest active task title: {active_task.get('title', 'Untitled task')}")
    else:
        print("Latest active task: none")
    print(f"Latest enforcement mode: {latest.get('enforcement_mode', 'unknown')}")
    print(f"Latest session continuity: {latest.get('session_continuity', 'unknown')}")
    print(
        "Latest dependency warnings: "
        f"{latest.get('dependency_warnings_count', 'unknown')}"
    )
    print("Latest architecture zones touched:")
    zones = latest.get("architecture_zones_touched", {})
    if isinstance(zones, dict) and zones:
        for zone_name, count in zones.items():
            print(f"  {zone_name}: {count} files")
    else:
        print("  none")
    return 0
