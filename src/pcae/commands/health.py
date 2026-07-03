from __future__ import annotations

import argparse
import json

from pcae.core.command_path_observation import observe
from pcae.core.health import build_health_data, policy_validation_text
from pcae.core.paths import HarnessPath


def run_health(args: argparse.Namespace) -> int:
    data = build_health_data(HarnessPath.cwd())

    # Phase 109B: observation-only Permission Broker consultation. The
    # decision is deliberately discarded — it must never change this
    # command's output or exit code. Defense in depth: even though
    # observe() itself never raises, the call site is wrapped too, so
    # behavior preservation holds regardless of how observe() is
    # implemented. See
    # docs/PHASE_109_FIRST_COMMAND_PATH_INTEGRATION_PROTOTYPE.md.
    active_task = data.get("active_task")
    try:
        observe(
            action_type="read",
            execution_class="none",
            requested_component="COMP-001",
            requested_capability="pcae_health",
            task_id=active_task["id"] if active_task else None,
            evidence_available=True,
            approval_present=True,
        )
    except Exception:
        pass

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_health(data)

    from pcae.core.health import is_healthy

    return 0 if is_healthy(data) else 1


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
