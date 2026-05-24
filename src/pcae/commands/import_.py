from __future__ import annotations

import argparse
from pathlib import Path

from pcae.core.import_ import GovernanceBundlePreview, read_governance_bundle_preview


def run_import_bundle(args: argparse.Namespace) -> int:
    if not args.dry_run:
        print("Real import is not implemented yet. Use --dry-run.")
        return 1

    try:
        preview = read_governance_bundle_preview(Path(args.bundle))
    except ValueError as error:
        print(error)
        return 1

    print_import_preview(preview)
    return 0


def print_import_preview(preview: GovernanceBundlePreview) -> None:
    data = preview.data
    print("Governance bundle import preview")
    print(f"Bundle timestamp: {data.get('generated_timestamp', 'unknown')}")
    print_active_task(data.get("active_task"))
    print(f"Session snapshot: {availability(data.get('session_snapshot'))}")
    print(f"Health status: {summary_value(data.get('health_summary'), 'overall_status')}")
    print(f"Check status: {summary_value(data.get('check_summary'), 'status')}")
    print(
        "Architecture metrics: "
        f"{availability(data.get('architecture_metrics'))}"
    )
    print(f"Policy summary: {availability(data.get('policy_summary'))}")
    print("Files that would be touched by a future real import:")
    for target in preview.future_import_targets:
        print(f"  {target}")


def print_active_task(active_task) -> None:
    if not isinstance(active_task, dict):
        print("Active task: none")
        return
    print(f"Active task: {active_task.get('id', 'unknown')}")
    print(f"Title: {active_task.get('title', 'Untitled task')}")


def availability(value) -> str:
    if value is None:
        return "missing"
    return "available"


def summary_value(value, key: str) -> str:
    if not isinstance(value, dict):
        return "missing"
    result = value.get(key)
    if isinstance(result, str) and result:
        return result
    return "unknown"
