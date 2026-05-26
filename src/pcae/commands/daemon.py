from __future__ import annotations

import argparse
import json

from pcae.core.daemon import (
    DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS,
    DaemonDryRunResult,
    DaemonStatus,
    DaemonWatchPlan,
    build_daemon_watch_plan,
    daemon_status,
    run_daemon_dry_run_cycle,
)


def run_daemon(args: argparse.Namespace) -> int:
    if not args.dry_run:
        print("Daemon run is only available with --dry-run in this phase.")
        return 1

    result = run_daemon_dry_run_cycle()
    if args.json:
        print(json.dumps(daemon_json_data(result), indent=2, sort_keys=True))
    else:
        print_daemon_dry_run(result)
    return 0


def run_daemon_status(args: argparse.Namespace) -> int:
    status = daemon_status()
    if args.json:
        print(json.dumps(daemon_status_json_data(status), indent=2, sort_keys=True))
    else:
        print_daemon_status(status)
    return 0


def run_daemon_watch(args: argparse.Namespace) -> int:
    if not args.dry_run:
        print("Daemon watch is only available with --dry-run in this phase.")
        return 1

    try:
        plan = build_daemon_watch_plan(args.interval_seconds)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(daemon_watch_json_data(plan), indent=2, sort_keys=True))
    else:
        print_daemon_watch_plan(plan)
    return 0


def print_daemon_dry_run(result: DaemonDryRunResult) -> None:
    print("PCAE daemon")
    print("Mode: dry-run")
    print(f"Monitoring cycles: {result.cycle_count}")
    print("Planned checks:")
    for index, step in enumerate(result.steps, start=1):
        print(f"  {index}. {step.name}: {step.status}")
        print(f"     {step.message}")
    print(f"Daemon result: {result.status}")


def print_daemon_status(status: DaemonStatus) -> None:
    print("PCAE daemon status")
    print(f"Supported: {format_bool(status.supported)}")
    print(f"Running: {format_bool(status.running)}")
    print(f"Mode: {status.mode}")
    print(f"Watch supported: {format_bool(status.watch_supported)}")
    print(f"Dry-run supported: {format_bool(status.dry_run_supported)}")
    print(f"Planned checks: {len(status.planned_checks)}")
    for index, check in enumerate(status.planned_checks, start=1):
        print(f"  {index}. {check}")


def print_daemon_watch_plan(plan: DaemonWatchPlan) -> None:
    print("PCAE daemon watch")
    print("Mode: dry-run")
    print(f"Interval seconds: {plan.interval_seconds}")
    print(f"Would repeat continuously: {format_bool(plan.would_repeat_continuously)}")
    print(f"Planned checks: {len(plan.planned_checks)}")
    for index, check in enumerate(plan.planned_checks, start=1):
        print(f"  {index}. {check}")


def daemon_json_data(result: DaemonDryRunResult) -> dict[str, object]:
    return {
        "cycle_count": result.cycle_count,
        "mode": result.mode,
        "status": result.status,
        "steps": [
            {
                "name": step.name,
                "status": step.status,
                "summary": step.message,
            }
            for step in result.steps
        ],
    }


def daemon_watch_json_data(plan: DaemonWatchPlan) -> dict[str, object]:
    return {
        "interval_seconds": plan.interval_seconds,
        "mode": plan.mode,
        "planned_checks": list(plan.planned_checks),
        "planned_checks_count": len(plan.planned_checks),
        "would_repeat_continuously": plan.would_repeat_continuously,
    }


def daemon_status_json_data(status: DaemonStatus) -> dict[str, object]:
    return {
        "dry_run_supported": status.dry_run_supported,
        "mode": status.mode,
        "planned_checks": list(status.planned_checks),
        "planned_checks_count": len(status.planned_checks),
        "running": status.running,
        "supported": status.supported,
        "watch_supported": status.watch_supported,
    }


def format_bool(value: bool) -> str:
    return "true" if value else "false"


def default_watch_interval_seconds() -> int:
    return DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS
