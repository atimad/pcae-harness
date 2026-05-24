from __future__ import annotations

import argparse
import json

from pcae.core.architecture import (
    ArchitectureDriftMetrics,
    ArchitectureHistorySummary,
    calculate_architecture_drift_metrics,
    read_architecture_history_summary,
    write_architecture_history_snapshot,
)
from pcae.core.check import run_checks
from pcae.core.paths import HarnessPath


def run_architecture_snapshot(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    check_result = run_checks(root)
    snapshot = write_architecture_history_snapshot(root, check_result)
    summary = ArchitectureHistorySummary(
        relative_path=snapshot.relative_path,
        entries=snapshot.entries,
        latest=snapshot.entry,
    )
    metrics = calculate_architecture_drift_metrics(summary)

    print(f"Wrote architecture history: {snapshot.relative_path.as_posix()}")
    print(f"Entries: {len(snapshot.entries)}")
    print("Snapshot metrics:")
    print(f"  Total snapshots: {metrics.total_snapshots}")
    print(f"  Latest dependency warnings: {metrics.latest_dependency_warnings}")
    print(f"  Max dependency warnings: {metrics.max_dependency_warnings}")
    print(f"  Snapshots with warnings: {metrics.snapshots_with_warnings}")
    print(
        "  Most frequently touched zone: "
        f"{metrics.most_frequently_touched_zone or 'none'}"
    )
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


def run_architecture_metrics(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        summary = read_architecture_history_summary(root)
    except ValueError as error:
        print(error)
        return 1

    metrics = calculate_architecture_drift_metrics(summary)
    if args.json:
        print(
            json.dumps(
                architecture_metrics_json_data(metrics),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    most_touched_zone = metrics.most_frequently_touched_zone or "none"

    print("Architecture drift metrics")
    print(f"Total snapshots: {metrics.total_snapshots}")
    print(f"Latest dependency warnings: {metrics.latest_dependency_warnings}")
    print(f"Max dependency warnings: {metrics.max_dependency_warnings}")
    print(
        "Average dependency warnings: "
        f"{metrics.average_dependency_warnings:.2f}"
    )
    print(f"Snapshots with warnings: {metrics.snapshots_with_warnings}")
    print(f"Most frequently touched zone: {most_touched_zone}")
    print(f"Latest enforcement mode: {metrics.latest_enforcement_mode}")
    print(f"Latest session continuity: {metrics.latest_session_continuity}")
    return 0


def architecture_metrics_json_data(
    metrics: ArchitectureDriftMetrics,
) -> dict[str, object]:
    return {
        "average_dependency_warnings": metrics.average_dependency_warnings,
        "latest_dependency_warnings": metrics.latest_dependency_warnings,
        "latest_enforcement_mode": metrics.latest_enforcement_mode,
        "latest_session_continuity": metrics.latest_session_continuity,
        "max_dependency_warnings": metrics.max_dependency_warnings,
        "most_frequently_touched_zone": metrics.most_frequently_touched_zone,
        "snapshots_with_warnings": metrics.snapshots_with_warnings,
        "total_snapshots": metrics.total_snapshots,
    }
