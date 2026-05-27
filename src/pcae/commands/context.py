from __future__ import annotations

import argparse
import json

from pcae.core.context import build_context_pack
from pcae.core.paths import HarnessPath


def run_context_pack(args: argparse.Namespace) -> int:
    result = build_context_pack(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance context pack")
        if result.active_task is not None:
            print(
                f"Active task: {result.active_task['id']}"
                f" — {result.active_task['title']}"
            )
        else:
            print("Active task: none")
        gs = result.governance_state
        print("Governance state:")
        print(f"  Health: {gs['health_status']}")
        print(f"  Check: {gs['check_status']}")
        print(f"  Session continuity: {gs['session_continuity']}")
        lock = gs["agent_lock_state"]
        if lock and lock.get("locked"):
            print(f"  Agent lock: held by {lock.get('agent_id', 'unknown')}")
        else:
            print("  Agent lock: free")
        os_ = result.orchestration_state
        print("Orchestration state:")
        print(f"  Default agent: {os_['default_agent']}")
        agents = os_["registered_agents"]
        if agents:
            ids = ", ".join(a["agent_id"] for a in agents)
            print(f"  Registered agents: {ids}")
        else:
            print("  Registered agents: none")
        ps = result.provenance_summary
        print("Provenance summary:")
        print(f"  Event count: {ps['event_count']}")
        if ps["latest_event"] is not None:
            le = ps["latest_event"]
            print(f"  Latest event: [{le['event_type']}] {le['summary']}")
        else:
            print("  Latest event: none")
        rs = result.roadmap_summary
        print("Roadmap summary:")
        print(f"  Current phase: {rs['current_phase']}")
        if rs["next"]:
            print("  Next:")
            for item in rs["next"]:
                print(f"    {item}")
        print("Operational rules:")
        for rule in result.operational_rules:
            print(f"  - {rule}")
        print("Validation commands:")
        for cmd in result.validation_commands:
            print(f"  - {cmd}")
        print("Token optimization note: context pack is compact by design.")
        print(f"Quality preservation note: {result.advisory}")
    return 0
