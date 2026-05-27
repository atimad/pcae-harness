from __future__ import annotations

import argparse
import json

from pcae.core.context import (
    CONTEXT_PACK_UNIVERSAL_AGENT_NOTE,
    build_context_pack,
    resolve_profile,
)
from pcae.core.paths import HarnessPath


def run_context_pack(args: argparse.Namespace) -> int:
    result = build_context_pack(HarnessPath.cwd())
    profile_name: str | None = getattr(args, "profile", None)
    profile, is_unknown = resolve_profile(profile_name)

    if args.json:
        d = result.to_dict()
        d["profile_type"] = profile.profile_type
        d["emphasized_sections"] = list(profile.emphasized_sections)
        if is_unknown:
            d["profile_warning"] = (
                f"Unknown profile '{profile_name}'; using universal profile."
            )
        print(json.dumps(d, indent=2, sort_keys=True))
    else:
        if is_unknown:
            print(
                f"Warning: unknown profile '{profile_name}';"
                " using universal profile."
            )
        print(f"Profile: {profile.profile_type}")
        print(f"Emphasized sections: {', '.join(profile.emphasized_sections)}")
        print("Governance context pack")
        if result.active_task is not None:
            print(
                f"Active task: {result.active_task['id']}"
                f" — {result.active_task['title']}"
            )
        else:
            print("Active task: none")
        sb = result.scope_boundaries
        allowed = sb.get("allowed_files", [])
        forbidden = sb.get("forbidden_files", [])
        if allowed or forbidden:
            print("Scope boundaries:")
            if allowed:
                print("  Allowed files:")
                for f in allowed:
                    print(f"    {f}")
            if forbidden:
                print("  Forbidden files:")
                for f in forbidden:
                    print(f"    {f}")
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
        policy_summary = os_.get("orchestration_policy_summary")
        if policy_summary:
            print("  Policy summary:")
            for k, v in policy_summary.items():
                print(f"    {k}: {v}")
        print(f"  Advisory: {os_['advisory_recommendation_semantics']}")
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
        print("Bootstrap/handoff:")
        for note in result.bootstrap_handoff_notes:
            print(f"  - {note}")
        print(f"Universal agent note: {CONTEXT_PACK_UNIVERSAL_AGENT_NOTE}")
        print("Token optimization note: context pack is compact by design.")
        print(f"Quality preservation note: {result.advisory}")
    return 0
