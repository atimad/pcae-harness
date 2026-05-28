from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.core.context import (
    CONTEXT_PACK_UNIVERSAL_AGENT_NOTE,
    CONTINUITY_MANIFEST_ADVISORY,
    CONTINUITY_PACK_COMPATIBILITY_ADVISORY,
    CONTINUITY_PACK_GOVERNANCE_CONTINUITY_NOTE,
    CONTINUITY_PACK_INCLUDED_SECTIONS,
    CONTINUITY_RETENTION_ADVISORY,
    analyze_continuity_pack_compatibility,
    build_context_pack,
    build_continuity_manifest,
    build_continuity_pack,
    export_context_pack,
    export_continuity_pack,
    inspect_continuity_pack,
    plan_continuity_retention,
    resolve_profile,
)
from pcae.core.paths import HarnessPath


def run_context_export(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    pack = build_context_pack(root)
    profile_name: str | None = getattr(args, "profile", None)
    profile, _ = resolve_profile(profile_name)
    relative_path, exported_at = export_context_pack(root, pack, profile)

    if args.json:
        print(
            json.dumps(
                {
                    "exported_at": exported_at,
                    "path": relative_path.as_posix(),
                    "profile_type": profile.profile_type,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"Exported: {relative_path.as_posix()}")
        print(f"Profile: {profile.profile_type}")
        print(f"Exported at: {exported_at}")
    return 0


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


def run_continuity_export(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    profile_name: str | None = getattr(args, "profile", None)
    profile, _ = resolve_profile(profile_name)
    continuity_pack = build_continuity_pack(root, profile)
    relative_path, exported_at = export_continuity_pack(root, continuity_pack)

    if args.json:
        print(
            json.dumps(
                {
                    "continuity_summary": {
                        "active_task": continuity_pack.active_task_summary,
                        "governance_check": continuity_pack.governance_state.get(
                            "check_status"
                        ),
                        "governance_health": continuity_pack.governance_state.get(
                            "health_status"
                        ),
                    },
                    "exported_at": exported_at,
                    "included_sections": list(CONTINUITY_PACK_INCLUDED_SECTIONS),
                    "path": relative_path.as_posix(),
                    "profile_type": profile.profile_type,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"Export path: {relative_path.as_posix()}")
        print(f"Profile: {profile.profile_type}")
        print("Included continuity sections:")
        for section in CONTINUITY_PACK_INCLUDED_SECTIONS:
            print(f"  - {section}")
        print("Token optimization note: continuity pack is compact by design.")
        print(f"Governance continuity note: {CONTINUITY_PACK_GOVERNANCE_CONTINUITY_NOTE}")
    return 0


def run_continuity_inspect(args: argparse.Namespace) -> int:
    try:
        result = inspect_continuity_pack(Path(args.path))
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Continuity pack inspection")
        print(f"Pack validity: {'valid' if result.valid else 'invalid'}")
        print(f"Exported: {result.exported_at}")
        print(f"Profile: {result.profile_type}")
        print("Included sections:")
        for section in result.included_sections:
            print(f"  - {section}")
        cs = result.continuity_summary
        print("Continuity summary:")
        at = cs.get("active_task")
        if at is not None:
            print(f"  Active task: {at.get('id')} — {at.get('title')}")
        else:
            print("  Active task: none")
        print(f"  Governance health: {cs.get('governance_health')}")
        print(f"  Governance check: {cs.get('governance_check')}")
        print(f"  Provenance event count: {cs.get('provenance_event_count')}")
        print(f"  Orchestration default agent: {cs.get('orchestration_default_agent')}")
        print(
            f"  Compact context pack present: {cs.get('compact_context_pack_present')}"
        )
        print(
            f"  Compact bootstrap prompt present: {cs.get('compact_bootstrap_prompt_present')}"
        )
        print(
            f"  Stale-context suppression present: {cs.get('stale_context_suppression_present')}"
        )
        print(
            f"  Vendor-neutral note present: {cs.get('vendor_neutral_note_present')}"
        )
        print("Portability notes:")
        for note in result.portability_notes:
            print(f"  - {note}")
        print("Safety notes:")
        for note in result.safety_notes:
            print(f"  - {note}")
        print(result.advisory)
    return 0


def run_continuity_compatibility(args: argparse.Namespace) -> int:
    try:
        result = analyze_continuity_pack_compatibility(Path(args.path))
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Continuity compatibility analysis")
        status = "compatible" if result.compatible else "incompatible"
        print(f"Compatibility status: {status}")
        print(f"Support level: {result.support_level}")
        print("Compatibility checks:")
        for check in result.compatibility_checks:
            status_label = "pass" if check.passed else "warn"
            print(f"  - {check.name}: {status_label} ({check.message})")
        print("Warnings:")
        if result.warnings:
            for warning in result.warnings:
                print(f"  - {warning}")
        else:
            print("  - none")
        cs = result.continuity_summary
        print("Governance continuity summary:")
        at_id = cs.get("active_task_id")
        at_title = cs.get("active_task_title")
        if at_id:
            print(f"  Active task: {at_id} — {at_title}")
        else:
            print("  Active task: none")
        print(f"  Profile: {cs.get('profile_type')}")
        print(f"  Governance health: {cs.get('governance_health')}")
        print(f"  Governance check: {cs.get('governance_check')}")
        print(f"  Exported at: {cs.get('exported_at')}")
        print("Portability summary:")
        print("  Continuity packs are portable, governance-complete, vendor-neutral exports.")
        print("  Compatibility analysis is read-only; no runtime state is changed.")
        print(CONTINUITY_PACK_COMPATIBILITY_ADVISORY)
    return 0


def run_continuity_retention(args: argparse.Namespace) -> int:
    result = plan_continuity_retention(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Continuity retention plan (dry-run)")
        print(f"Pack count: {result.pack_count}")
        print(f"Keep count: {result.keep_count}")
        print(f"Prune candidate count: {result.prune_candidate_count}")
        print("Packs to keep:")
        if result.keep:
            for filename in result.keep:
                print(f"  - {filename}")
        else:
            print("  - none")
        print("Prune candidates:")
        if result.prune_candidates:
            for filename in result.prune_candidates:
                print(f"  - {filename}")
        else:
            print("  - none")
        print(CONTINUITY_RETENTION_ADVISORY)
    return 0


def run_continuity_manifest(args: argparse.Namespace) -> int:
    result = build_continuity_manifest(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Continuity pack manifest")
        print(f"Pack count: {result.pack_count}")
        latest = result.latest_pack
        latest_text = "none" if latest is None else latest["filename"]
        print(f"Latest continuity pack: {latest_text}")
        print("Manifest entries:")
        if result.manifest_entries:
            for entry in result.manifest_entries:
                at_label = entry.active_task_id or "none"
                print(
                    f"  - {entry.filename}: "
                    f"exported_at={entry.exported_at}, "
                    f"profile={entry.profile_type}, "
                    f"task={at_label}, "
                    f"compatibility={entry.compatibility_status}, "
                    f"support={entry.support_level}, "
                    f"vendor_neutral={entry.vendor_neutral}, "
                    f"stale_ctx={entry.stale_context_suppression_present}, "
                    f"bootstrap={entry.compact_bootstrap_present}"
                )
        else:
            print("  - none")
        print("Compatibility summary:")
        for key in (
            "compatible",
            "incompatible",
            "supported",
            "partially-supported",
            "unsupported",
        ):
            print(f"  - {key}: {result.compatibility_summary[key]}")
        print(CONTINUITY_MANIFEST_ADVISORY)
    return 0
