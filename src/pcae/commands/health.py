from __future__ import annotations

import argparse
import json

from pcae.core.health import build_health_data, policy_validation_text
from pcae.core.paths import HarnessPath


def run_health(args: argparse.Namespace) -> int:
    data = build_health_data(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_health(data)

    return 0 if data["overall_status"] == "healthy" else 1


def print_health(data: dict) -> None:
    print("PCAE health")
    print(f"Overall status: {data['overall_status']}")
    print(f"Required PCAE files: {data['required_files_status']}")
    print(f"Policy validation: {policy_validation_text(data)}")
    print_active_task(data["active_task"])
    print_agent_lock(data["agent_lock"])
    print(f"Session continuity: {data['session_continuity']}")
    if data["architecture_history_entries"] is None:
        print("Architecture history entries: missing")
        print(f"Latest enforcement mode: {data['latest_enforcement_mode']}")
        print("Latest dependency warnings: unknown")
    else:
        print(f"Architecture history entries: {data['architecture_history_entries']}")
        print(f"Latest enforcement mode: {data['latest_enforcement_mode']}")
        print(f"Latest dependency warnings: {data['latest_dependency_warnings']}")
    print(f"Git status: {data['git_status']}")

    for warning in data["warnings"]:
        print(f"  - warning: {warning}")

    if data["overall_status"] == "unhealthy":
        print("Health check failed:")
        for violation in data["violations"]:
            print(f"  - {violation}")


def print_active_task(active_task: dict | None) -> None:
    if active_task is None:
        print("Active task: none")
        return

    print(f"Active task: {active_task['id']}")
    print(f"Title: {active_task['title']}")


def print_agent_lock(agent_lock: dict) -> None:
    if not agent_lock["locked"]:
        print("Agent lock: available")
        return
    if agent_lock["stale"]:
        print(f"Agent lock: stale ({agent_lock['agent_id']})")
        return
    print(f"Agent lock: held by {agent_lock['agent_id']}")
