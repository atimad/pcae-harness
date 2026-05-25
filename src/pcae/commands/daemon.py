from __future__ import annotations

import argparse
import json

from pcae.core.daemon import DaemonDryRunResult, run_daemon_dry_run_cycle


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


def print_daemon_dry_run(result: DaemonDryRunResult) -> None:
    print("PCAE daemon")
    print("Mode: dry-run")
    print(f"Monitoring cycles: {result.cycle_count}")
    print("Planned checks:")
    for index, step in enumerate(result.steps, start=1):
        print(f"  {index}. {step.name}: {step.status}")
        print(f"     {step.message}")
    print(f"Daemon result: {result.status}")


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
