from __future__ import annotations

import argparse
import json

from pcae.core.agent import (
    COLLABORATION_ADVISORY,
    COLLABORATION_WORKFLOWS,
    CONFIG_ADVISORY,
    MULTI_AGENT_REGISTRY,
    REVIEW_ADVISORY,
    REVIEW_WORKFLOWS,
    VALID_AGENT_STATUSES,
    VALID_REVIEW_STATUSES,
    acquire_agent_lock,
    build_agent_status,
    build_collaboration_workflows,
    build_lifecycle_report,
    build_multi_agent_registry,
    build_review_workflows,
    get_agent_by_id,
    get_agent_config,
    release_agent_lock,
    validate_agent_configs,
    validate_agent_registry,
)
from pcae.core.paths import HarnessPath
from pcae.core.provenance import append_provenance_event, build_handoff_history


def run_agent_acquire(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        lock = acquire_agent_lock(root, args.agent_id)
    except ValueError as error:
        print(str(error))
        return 1

    append_provenance_event(
        root,
        "agent_acquired",
        f"Agent lock acquired by {lock.agent_id}",
        agent_id=lock.agent_id,
    )
    print(f"Agent lock acquired by {lock.agent_id}.")
    print(f"Git branch: {lock.data['git_branch']}")
    active_task = lock.data.get("active_task")
    if isinstance(active_task, dict):
        print(f"Active task: {active_task.get('id')} - {active_task.get('title')}")
    else:
        print("Active task: none")
    return 0


def run_agent_release(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    try:
        result = release_agent_lock(
            root,
            args.agent_id,
            force_stale=args.force_stale,
        )
    except ValueError as error:
        print(str(error))
        return 1
    if result.released:
        append_provenance_event(
            root,
            "agent_released",
            f"Agent lock released by {args.agent_id}",
            agent_id=args.agent_id,
        )
    print(result.message)
    return 0 if result.released else 1


def run_agent_status(args: argparse.Namespace) -> int:
    try:
        status = build_agent_status(HarnessPath.cwd())
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print_agent_status(status)
    return 0


def run_agents(args: argparse.Namespace) -> int:
    data = build_multi_agent_registry()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Multi-agent registry")
        print(f"Agent count: {data['agent_count']}")
        for entry in MULTI_AGENT_REGISTRY:
            print(
                f"{entry.agent_id:<18} | role: {entry.role:<16} | status: {entry.status}"
            )
        summary = data["lifecycle_summary"]
        summary_parts = ", ".join(f"{k}={v}" for k, v in sorted(summary.items()) if v > 0)
        print(f"Lifecycle summary: {summary_parts}")
        print(f"Advisory: {data['advisory']}")
    return 0


def run_agents_show(args: argparse.Namespace) -> int:
    entry = get_agent_by_id(args.agent_id)
    if entry is None:
        print(f"Agent not found: '{args.agent_id}'.")
        return 1
    if args.json:
        print(json.dumps(entry.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"Agent: {entry.agent_id}")
        print(f"Type: {entry.agent_type}")
        print(f"Role: {entry.role}")
        print(f"Status: {entry.status}")
        caps = ", ".join(entry.capabilities) if entry.capabilities else "none"
        print(f"Capabilities: {caps}")
        workloads = (
            ", ".join(entry.preferred_workloads) if entry.preferred_workloads else "none"
        )
        print(f"Preferred workloads: {workloads}")
    return 0


def run_agents_validate(args: argparse.Namespace) -> int:
    result = validate_agent_registry()
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Agent registry validation")
        print(f"Agent count: {result.agent_count}")
        print(f"Validation status: {'valid' if result.valid else 'invalid'}")
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
        else:
            print("Errors: none")
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        else:
            print("Warnings: none")
        print(result.advisory)
    return 0 if result.valid else 1


def run_agents_config_show(args: argparse.Namespace) -> int:
    config = get_agent_config(args.agent_id)
    if config is None:
        print(f"Agent not found: '{args.agent_id}'.")
        return 1
    registry_entry = get_agent_by_id(args.agent_id)
    lifecycle_status = registry_entry.status if registry_entry is not None else ""
    if args.json:
        print(json.dumps(config.to_dict(lifecycle_status), indent=2, sort_keys=True))
    else:
        print(f"Agent configuration: {config.agent_id}")
        print(f"Adapter type: {config.adapter_type}")
        print(f"Configuration status: {config.configuration_status}")
        hint = config.executable_hint if config.executable_hint is not None else "(none)"
        print(f"Executable hint: {hint}")
        print(f"Requires manual setup: {'yes' if config.requires_manual_setup else 'no'}")
        print(f"Configuration notes: {config.configuration_notes}")
        print(f"Lifecycle status: {lifecycle_status}")
        print(CONFIG_ADVISORY)
    return 0


def run_agents_config_validate(args: argparse.Namespace) -> int:
    result = validate_agent_configs()
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Agent configuration validation")
        print(f"Agent count: {result.agent_count}")
        print(f"Validation status: {'valid' if result.valid else 'invalid'}")
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
        else:
            print("Errors: none")
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        else:
            print("Warnings: none")
        print(result.advisory)
    return 0 if result.valid else 1


def run_collaboration_handoffs(args: argparse.Namespace) -> int:
    history = build_handoff_history(HarnessPath.cwd())
    if args.json:
        print(json.dumps(history.to_dict(), indent=2, sort_keys=True))
    else:
        print("Handoff history")
        print(f"Handoff count: {history.handoff_count}")
        if not history.handoffs:
            print("No handoff records found.")
        else:
            for idx, rec in enumerate(history.handoffs, start=1):
                label = "Handoff 1 (most recent)" if idx == 1 else f"Handoff {idx}"
                print(f"\n{label}:")
                print(f"  Timestamp: {rec.timestamp}")
                print(f"  Source agent: {rec.source_agent or '(unknown)'}")
                print(f"  Target agent: {rec.target_agent or '(unknown)'}")
                if rec.phase:
                    print(f"  Phase: {rec.phase}")
                if rec.active_task:
                    title = rec.active_task.get("title", "")
                    print(f"  Active task: {title}")
                print(f"  Continuity verified: {'yes' if rec.continuity_verified else 'no'}")
                print(f"  Architecture memory: {'yes' if rec.architecture_memory_present else 'no'}")
                if rec.summary:
                    print(f"  Summary: {rec.summary}")
                if rec.warnings:
                    for w in rec.warnings:
                        print(f"  Warning: {w}")
        print()
        print(history.advisory)
    return 0


def run_collaboration_reviews(args: argparse.Namespace) -> int:
    data = build_review_workflows()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        names = ", ".join(w.workflow_name for w in REVIEW_WORKFLOWS)
        statuses = ", ".join(VALID_REVIEW_STATUSES)
        print("Review workflows")
        print(f"Review workflow count: {len(REVIEW_WORKFLOWS)}")
        print(f"Workflows: {names}")
        print(f"Review statuses: {statuses}")
        for workflow in REVIEW_WORKFLOWS:
            print(f"\n{workflow.workflow_name} ({len(workflow.steps)} steps):")
            for i, step in enumerate(workflow.steps, start=1):
                print(
                    f"  {i}. {step.step_name:<18} | role: {step.recommended_agent_role:<16}"
                    f" | min status: {step.required_lifecycle_status}"
                    f" | review: {step.review_status}"
                )
                print(f"     Purpose: {step.purpose}")
        print()
        print(REVIEW_ADVISORY)
    return 0


def run_collaboration_workflows(args: argparse.Namespace) -> int:
    data = build_collaboration_workflows()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        names = ", ".join(w.workflow_name for w in COLLABORATION_WORKFLOWS)
        print("Collaboration workflows")
        print(f"Workflow count: {len(COLLABORATION_WORKFLOWS)}")
        print(f"Workflows: {names}")
        for workflow in COLLABORATION_WORKFLOWS:
            print(f"\n{workflow.workflow_name} ({len(workflow.steps)} steps):")
            for i, step in enumerate(workflow.steps, start=1):
                print(
                    f"  {i}. {step.step_name:<18} | role: {step.recommended_agent_role:<16}"
                    f" | min status: {step.required_lifecycle_status}"
                )
                print(f"     Purpose: {step.purpose}")
        print()
        print(COLLABORATION_ADVISORY)
    return 0


def run_agents_lifecycle(args: argparse.Namespace) -> int:
    report = build_lifecycle_report()
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print("Lifecycle summary")
        total = sum(report.lifecycle_summary.values())
        print(f"Agent count: {total}")
        dist = ", ".join(
            f"{s}={report.lifecycle_summary[s]}" for s in sorted(VALID_AGENT_STATUSES)
        )
        print(f"State distribution: {dist}")
        print()
        print("Agents by lifecycle state:")
        for state in sorted(VALID_AGENT_STATUSES):
            agents = report.agents_by_state[state]
            print(f"\n{state} ({len(agents)}):")
            if agents:
                for entry in agents:
                    print(f"  - {entry['agent_id']} ({entry['agent_type']}) — {entry['role']}")
            else:
                print("  (none)")
        print()
        print("Lifecycle progression guidance:")
        for state in sorted(VALID_AGENT_STATUSES):
            print(f"  {state}: {report.progression_guidance[state]}")
        if not report.validation.valid:
            print()
            print("Validation errors:")
            for error in report.validation.errors:
                print(f"  - {error}")
        print()
        print(report.advisory)
    return 0


def print_agent_status(status: dict[str, object]) -> None:
    if not status["locked"]:
        print("Agent lock: available")
        print(f"Stale after seconds: {status['stale_after_seconds']}")
        return

    lock = status.get("lock")
    if not isinstance(lock, dict):
        print("Agent lock: unavailable")
        return

    if status["stale"]:
        print("Agent lock: stale")
    else:
        print("Agent lock: held")
    print(f"Agent ID: {lock.get('agent_id')}")
    print(f"Acquired at: {lock.get('acquired_at')}")
    print(f"Age seconds: {status.get('age_seconds')}")
    print(f"Stale after seconds: {status.get('stale_after_seconds')}")
    print(f"Git branch: {lock.get('git_branch')}")
    active_task = lock.get("active_task")
    if isinstance(active_task, dict):
        print(f"Active task: {active_task.get('id')} - {active_task.get('title')}")
    else:
        print("Active task: none")
