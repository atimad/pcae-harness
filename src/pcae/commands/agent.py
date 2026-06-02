from __future__ import annotations

import argparse
import json

from pcae.core.agent import (
    ADAPTER_ADVISORY,
    COLLABORATION_ADVISORY,
    COLLABORATION_WORKFLOWS,
    CONFIG_ADVISORY,
    MULTI_AGENT_REGISTRY,
    REVIEW_ADVISORY,
    REVIEW_WORKFLOWS,
    RUNTIME_DISCOVERY_ADVISORY,
    VALID_AGENT_STATUSES,
    VALID_REVIEW_STATUSES,
    acquire_agent_lock,
    build_adapter_inspection,
    build_agent_adapters,
    build_agent_status,
    build_collaboration_design,
    build_collaboration_workflows,
    build_consensus_design,
    build_coordinator_design,
    build_orchestration_design,
    build_parallel_execution_design,
    build_planning_dry_run,
    build_adapter_design,
    build_execution_framework_design,
    build_invocation_design,
    build_real_planning_design,
    REAL_PLANNING_DESIGN_ADVISORY,
    build_consensus_execution_design,
    CONSENSUS_EXECUTION_DESIGN_ADVISORY,
    build_runtime_execution_prototype,
    RUNTIME_EXECUTION_PROTOTYPE_ADVISORY,
    build_planner_adapter_prototype,
    PLANNER_ADAPTER_PROTOTYPE_ADVISORY,
    build_multi_agent_execution_prototype,
    MULTI_AGENT_EXECUTION_PROTOTYPE_ADVISORY,
    build_consensus_prototype,
    CONSENSUS_PROTOTYPE_ADVISORY,
    build_invocation_pilot,
    INVOCATION_PILOT_ADVISORY,
    build_multi_runtime_pilot,
    MULTI_RUNTIME_PILOT_ADVISORY,
    build_consensus_runtime_pilot,
    CONSENSUS_RUNTIME_PILOT_ADVISORY,
    build_governed_execution_dry_run,
    GOVERNED_EXECUTION_DRY_RUN_ADVISORY,
    build_invocation_contracts,
    INVOCATION_CONTRACTS_ADVISORY,
    build_execution_readiness,
    EXECUTION_READINESS_ADVISORY,
    build_adapter_registry_design,
    ADAPTER_REGISTRY_DESIGN_ADVISORY,
    build_planning_execution_design,
    build_planning_prototype_design,
    build_capability_registry,
    build_capability_discovery,
    build_capability_validation,
    CAPABILITY_CATEGORIES,
    build_controlled_benchmark_plan,
    approve_file_changes,
    approve_rollback,
    commit_file_changes,
    deny_file_changes,
    deny_rollback,
    execute_rollback,
    push_file_changes,
    push_rollback,
    build_change_review,
    build_claude_writable_contract,
    build_writable_contract,
    build_file_governance_design,
    build_rollback_governance,
    build_rollback_review,
    invoke_remote_job_with_file_changes,
    build_lifecycle_report,
    build_multi_agent_registry,
    build_remote_adapters,
    build_remote_approvals,
    build_remote_create_dry_run,
    build_remote_create_persist_preview,
    build_remote_dry_run,
    build_remote_execution_analytics,
    build_remote_execution_trends,
    build_remote_results,
    build_remote_runtime_benchmark,
    export_remote_execution_report,
    inspect_remote_execution_report,
    build_remote_results_registry,
    persist_remote_job,
    build_remote_strategy,
    build_remote_jobs,
    load_persisted_jobs,
    inspect_persisted_job,
    approve_remote_job,
    deny_remote_job,
    check_remote_job_readiness,
    build_remote_execute_dry_run,
    invoke_remote_job,
    build_remote_plan,
    build_remote_validate,
    build_remote_policy,
    build_remote_status,
    build_review_workflows,
    build_runtime_discovery,
    get_agent_adapter,
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


def run_agents_runtime_discover(args: argparse.Namespace) -> int:
    result = build_runtime_discovery()
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        data = result.to_dict()
        summary = data["discovery_summary"]
        print("Runtime discovery")
        print(f"Agents checked: {summary['agents_checked']}")
        print(f"Agents installed: {summary['agents_installed']}")
        for entry in result.agents:
            caps = entry.capabilities
            print(f"\n{entry.agent_id} ({entry.executable}):")
            print(f"  Installed: {'yes' if caps.installed else 'no'}")
            if caps.installed:
                print(f"  Executable: {caps.executable_path}")
                print(f"  Version: {caps.version or '(unknown)'}")
                print(f"  Interactive: {caps.interactive_supported}")
                print(f"  Non-interactive: {caps.non_interactive_supported}")
                print(f"  Stdin prompt: {caps.stdin_prompt_supported}")
                print(f"  Prompt file: {caps.prompt_file_supported}")
                print(f"  Structured output: {caps.structured_output_supported}")
                print(f"  MCP: {caps.mcp_supported}")
                print(f"  Hooks: {caps.hooks_supported}")
                print(f"  Subagents: {caps.subagents_supported}")
                print(f"  Remote: {caps.remote_supported}")
                if caps.known_limitations:
                    for lim in caps.known_limitations:
                        print(f"  Limitation: {lim}")
                else:
                    print("  Known limitations: none")
        print()
        print(RUNTIME_DISCOVERY_ADVISORY)
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


def run_collaboration_design(args: argparse.Namespace) -> int:
    data = build_collaboration_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Multi-agent collaboration design")
        print()
        print("Agent roles:")
        for role_def in data["collaboration_design"]["agent_roles"]:
            may = "yes" if role_def["may_modify_files"] else "no"
            print(f"  {role_def['role']:<14} — {role_def['description']} (may modify files: {may})")
        print()
        print("Runtime mapping:")
        for mapping in data["runtime_mapping"]:
            roles = ", ".join(mapping["supported_roles"])
            print(f"  {mapping['agent_id']:<14} — {roles}")
        print()
        print("Collaboration patterns:")
        for pattern in data["collaboration_design"]["collaboration_patterns"]:
            steps = " → ".join(pattern["steps"])
            print(f"  {pattern['pattern']:<16} — {steps}")
        print()
        print("Governance rules:")
        for rule in data["governance_model"]["rules"]:
            print(f"  - {rule}")
        print()
        print("Conflict model:")
        for item in data["conflict_model"]:
            print(f"  if {item['condition']}: {item['outcome']}")
        print()
        print("Future extensions:")
        for ext in data["future_extensions"]:
            print(f"  - {ext}")
        print()
        print(data["advisory"])
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


def _fmt_installed(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "not checked"


def run_agents_adapters(args: argparse.Namespace) -> int:
    data = build_agent_adapters()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        summary = data["adapter_summary"]
        print("Agent adapters")
        print(f"Total: {summary['total']}")
        for atype in ("cli", "native", "api", "desktop_manual", "undeclared"):
            count = summary[atype]
            if count:
                print(f"  {atype}: {count}")
        print()
        print("Adapters:")
        for entry in data["adapters"]:
            print(
                f"\n  {entry['agent_id']}"
                f" ({entry['adapter_type']}, {entry['lifecycle_status']}):"
            )
            print(f"    Installed: {_fmt_installed(entry['runtime_installed'])}")
            if entry["runtime_installed"]:
                ver = entry["runtime_version"] or "(none)"
                print(f"    Version: {ver}")
                print(f"    Interactive: {entry['supports_interactive']}")
                print(f"    Non-interactive: {entry['supports_non_interactive']}")
                print(f"    MCP: {entry['supports_mcp']}")
                print(f"    Hooks: {entry['supports_hooks']}")
                print(f"    Remote: {entry['supports_remote']}")
        print()
        print(ADAPTER_ADVISORY)
    return 0


def run_agents_adapter_show(args: argparse.Namespace) -> int:
    entry = get_agent_adapter(args.agent_id)
    if entry is None:
        print(f"Agent not found: '{args.agent_id}'.")
        return 1
    if args.json:
        print(json.dumps(entry, indent=2, sort_keys=True))
    else:
        print(f"Agent adapter: {entry['agent_id']}")
        print(f"Adapter type: {entry['adapter_type']}")
        print(f"Lifecycle status: {entry['lifecycle_status']}")
        print(f"Installed: {_fmt_installed(entry['runtime_installed'])}")
        ver = entry["runtime_version"] or "(none)"
        print(f"Version: {ver}")
        print(f"Supports interactive: {entry['supports_interactive']}")
        print(f"Supports non-interactive: {entry['supports_non_interactive']}")
        print(f"Supports MCP: {entry['supports_mcp']}")
        print(f"Supports hooks: {entry['supports_hooks']}")
        print(f"Supports remote: {entry['supports_remote']}")
        print(f"Notes: {entry['notes']}")
        print(ADAPTER_ADVISORY)
    return 0


def run_agents_adapter_inspect(args: argparse.Namespace) -> int:
    data = build_adapter_inspection(args.agent_id)
    if data is None:
        print(f"Agent not found: '{args.agent_id}'.")
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Adapter inspection")
        print(f"Agent: {data['agent_id']}")
        print(f"Adapter type: {data['adapter_type']}")
        print(f"Version: {data['runtime_version'] or '(none)'}")
        print(f"Executable: {data['executable_path'] or '(none)'}")
        modes = data["execution_modes"]
        print(f"Execution modes: {', '.join(modes) if modes else 'none'}")
        discovered = [c for c in data["capabilities"] if c["status"] == "yes"]
        unknown = [c for c in data["capabilities"] if c["status"] != "yes"]
        if discovered:
            print()
            print("Discovered capabilities:")
            for cap in discovered:
                print(
                    f"  {cap['name']:<24} [yes]     "
                    f"({cap['source']}) {cap['notes']}"
                )
        if unknown:
            print()
            print("Unknown capabilities:")
            for cap in unknown:
                print(
                    f"  {cap['name']:<24} [unknown] "
                    f"({cap['source']}) {cap['notes']}"
                )
        print()
        print(data["advisory"])
    return 0


def run_remote_status(args: argparse.Namespace) -> int:
    data = build_remote_status(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Remote Autonomous Coding status")
        print(f"Readiness: {data['readiness_status']}")
        agents = data["available_agents"]
        print(f"\nAvailable runtimes ({len(agents)}):")
        if agents:
            for a in agents:
                ver = a["runtime_version"] or "(unknown)"
                print(f"  {a['agent_id']} ({a['adapter_type']}, {ver})")
                print(f"    Non-interactive: {a['non_interactive']}")
                print(f"    MCP: {a['mcp']}")
                print(f"    Hooks: {a['hooks']}")
                print(f"    Remote: {a['remote']}")
        else:
            print("  (none)")
        adapters = data["supported_adapters"]
        print(f"\nSupported adapters: {', '.join(adapters) if adapters else 'none'}")
        missing = data["missing_capabilities"]
        if missing:
            print("\nMissing capabilities:")
            for cap in missing:
                print(f"  {cap}")
        else:
            print("\nMissing capabilities: none")
        gov = data["governance_readiness"]
        print("\nGovernance readiness:")
        print(f"  Session active: {'yes' if gov['session_active'] else 'no'}")
        print(f"  Architecture memory: {'yes' if gov['architecture_memory_present'] else 'no'}")
        print(f"  Active task: {'yes' if gov['active_task_present'] else 'no'}")
        print("\nSafety notes:")
        for note in data["safety_notes"]:
            print(f"  - {note}")
        print()
        print(data["advisory"])
    return 0


def run_remote_create(args: argparse.Namespace) -> int:
    if getattr(args, "preview_persist", False):
        return _run_remote_create_persist_preview(args)
    if getattr(args, "persist", False):
        return _run_remote_create_persist(args)
    return _run_remote_create_dry_run(args)


def _run_remote_create_dry_run(args: argparse.Namespace) -> int:
    try:
        data = build_remote_create_dry_run(HarnessPath.cwd(), args.agent, args.prompt)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        job = data["job_preview"]
        comp = job["policy_compliance"]
        val = data["validation"]
        print("Remote job creation preview")
        print(f"Job ID: {job['job_id']}")
        print(f"Selected agent: {job['requested_agent']}")
        print(f"Status: {job['status']}")
        print(f"Approval state: {job['approval_state']}")
        print(f"Execution mode: {job['execution_mode']}")
        print("\nPolicy compliance:")
        print(f"  Agent allowed: {'yes' if comp['agent_allowed'] else 'no'}")
        print(f"  Adapter allowed: {'yes' if comp['adapter_allowed'] else 'no'}")
        print(f"  Compliant: {'yes' if comp['compliant'] else 'no'}")
        approvals = job["required_approvals"]
        print(f"\nRequired approvals ({len(approvals)}):")
        for item in approvals:
            print(f"  - {item}")
        checks = job["required_checks"]
        print(f"\nRequired checks ({len(checks)}):")
        for item in checks:
            print(f"  - {item}")
        valid_label = "valid" if val["valid"] else "invalid"
        print(f"\nValidation: {valid_label}")
        if val["errors"]:
            for e in val["errors"]:
                print(f"  error: {e}")
        if val["warnings"]:
            for w in val["warnings"]:
                print(f"  warning: {w}")
        if val["blockers"]:
            for b in val["blockers"]:
                print(f"  blocker: {b}")
        print("\nSafety notes:")
        for note in job["safety_notes"]:
            print(f"  - {note}")
        print()
        print(data["advisory"])
    return 0


def _run_remote_create_persist_preview(args: argparse.Namespace) -> int:
    try:
        data = build_remote_create_persist_preview(HarnessPath.cwd(), args.agent, args.prompt)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        job = data["job_preview"]
        comp = job["policy_compliance"]
        val = data["validation"]
        print("Remote job persistence preview")
        print(f"Job ID: {job['job_id']}")
        print(f"Job file path: {data['job_file_path']}")
        print(f"Output directory: {data['output_directory']}")
        print(f"Selected agent: {job['requested_agent']}")
        print(f"Status: {job['status']}")
        print(f"Approval state: {job['approval_state']}")
        print(f"Execution mode: {job['execution_mode']}")
        print("\nPolicy compliance:")
        print(f"  Agent allowed: {'yes' if comp['agent_allowed'] else 'no'}")
        print(f"  Adapter allowed: {'yes' if comp['adapter_allowed'] else 'no'}")
        print(f"  Compliant: {'yes' if comp['compliant'] else 'no'}")
        approvals = job["required_approvals"]
        print(f"\nRequired approvals ({len(approvals)}):")
        for item in approvals:
            print(f"  - {item}")
        checks = job["required_checks"]
        print(f"\nRequired checks ({len(checks)}):")
        for item in checks:
            print(f"  - {item}")
        valid_label = "valid" if val["valid"] else "invalid"
        print(f"\nValidation: {valid_label}")
        if val["errors"]:
            for e in val["errors"]:
                print(f"  error: {e}")
        if val["warnings"]:
            for w in val["warnings"]:
                print(f"  warning: {w}")
        if val["blockers"]:
            for b in val["blockers"]:
                print(f"  blocker: {b}")
        print("\nSafety notes:")
        for note in job["safety_notes"]:
            print(f"  - {note}")
        print()
        print(data["advisory"])
    return 0


def _run_remote_create_persist(args: argparse.Namespace) -> int:
    try:
        data = persist_remote_job(HarnessPath.cwd(), args.agent, args.prompt)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        job = data["job"]
        print("Job created")
        print(f"Job ID: {job['job_id']}")
        print(f"Selected agent: {job['requested_agent']}")
        print(f"Persisted path: {data['job_path']}")
        print(f"Status: {job['status']}")
        print(f"Approval state: {job['approval_state']}")
        print()
        print(data["advisory"])
    return 0


def run_remote_dry_run(args: argparse.Namespace) -> int:
    try:
        data = build_remote_dry_run(HarnessPath.cwd(), args.agent, args.prompt)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Remote Autonomous Coding dry run")
        print(f"Selected agent: {data['selected_agent']}")
        print(f"Execution mode: {data['execution_mode']}")
        print(f"Dry-run result: {data['dry_run_result']}")
        preview = data["prompt_preview"]
        print(f"\nPrompt preview:\n  \"{preview}\"")
        comp = data["policy_compliance"]
        print("\nPolicy compliance:")
        print(f"  Agent allowed: {'yes' if comp['agent_allowed'] else 'no'}")
        print(f"  Adapter allowed: {'yes' if comp['adapter_allowed'] else 'no'}")
        print(f"  Compliant: {'yes' if comp['compliant'] else 'no'}")
        approvals = data["required_approvals"]
        print(f"\nRequired approvals ({len(approvals)}):")
        for item in approvals:
            print(f"  - {item}")
        checks = data["required_checks"]
        print(f"\nRequired checks ({len(checks)}):")
        for item in checks:
            print(f"  - {item}")
        caps = data["adapter_capabilities"]
        print("\nAdapter capabilities:")
        print(f"  Installed: {'yes' if caps.get('installed') else 'no'}")
        print(f"  Non-interactive: {caps.get('non_interactive', 'unknown')}")
        print(f"  Remote: {caps.get('remote', 'unknown')}")
        print(f"  MCP: {caps.get('mcp', 'unknown')}")
        print(f"  Hooks: {caps.get('hooks', 'unknown')}")
        blockers = data["blockers"]
        if blockers:
            print(f"\nBlockers ({len(blockers)}):")
            for b in blockers:
                print(f"  - {b}")
        else:
            print("\nBlockers: none")
        print("\nSafety notes:")
        for note in data["safety_notes"]:
            print(f"  - {note}")
        print()
        print(data["advisory"])
    return 0


def run_remote_strategy(args: argparse.Namespace) -> int:
    data = build_remote_strategy()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        preferred = data["preferred_runtime"]
        fallback = data["fallback_runtimes"]
        tie_break = data["tie_break_rule"]
        print("Remote execution strategy")
        print(f"Selection strategy: {data['selection_strategy']}")
        print(f"Preferred runtime: {preferred if preferred is not None else '(none)'}")
        fb_str = ", ".join(fallback) if fallback else "(none)"
        print(f"Fallback runtimes: {fb_str}")
        print(f"Tie-break rule: {tie_break if tie_break is not None else '(none)'}")
        print(f"Human override: {'enabled' if data['human_override_enabled'] else 'disabled'}")
        notes = data["advisory_notes"]
        print(f"\nAdvisory notes ({len(notes)}):")
        for note in notes:
            print(f"  - {note}")
        print()
        print(data["advisory"])
    return 0


def run_remote_adapters(args: argparse.Namespace) -> int:
    data = build_remote_adapters()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        rec = data["recommended_remote_runtime"]
        print("Remote adapter selection")
        print(f"Recommended runtime: {rec if rec else '(none)'}")
        agents = data["eligible_agents"]
        print(f"\nAgents ({len(agents)}):")
        for a in agents:
            tag = "[eligible]" if a["eligible"] else "[ineligible]"
            ver = a["runtime_version"] or "(unknown)"
            print(f"  {tag} {a['agent_id']} ({a['adapter_type']}, {ver})")
            print(f"    Policy allowed: {'yes' if a['policy_allowed'] else 'no'}")
            print(f"    Installed: {'yes' if a['runtime_installed'] else 'no'}")
            print(f"    Non-interactive: {a['non_interactive']}")
            print(f"    Remote: {a['remote']}")
            print(f"    Reason: {a['eligibility_reason']}")
            if a["missing_capabilities"]:
                print(f"    Missing: {', '.join(a['missing_capabilities'])}")
        notes = data["selection_notes"]
        if notes:
            print("\nSelection notes:")
            for n in notes:
                print(f"  - {n}")
        print(f"\nRationale: {data['rationale']}")
        print()
        print(data["advisory"])
    return 0


def run_remote_approvals(args: argparse.Namespace) -> int:
    data = build_remote_approvals()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        states = data["approval_states"]
        print("Remote approval workflow")
        print(f"Approval states ({len(states)}): {', '.join(states)}")
        gates = data["approval_gates"]
        required_gates = [g for g in gates if g["required"]]
        print(f"\nRequired approval gates ({len(required_gates)}):")
        for g in gates:
            tag = "[required]" if g["required"] else "[optional]"
            print(f"  {tag} {g['gate']} — {g['description']}")
        pending = data["pending_approvals"]
        print(f"\nPending approvals: {len(pending)}")
        for p in pending:
            print(f"  [{p['state']}] {p['job_id']} ({p['requested_agent']}) at {p['gate']}")
        print()
        print(data["advisory"])
    return 0


def run_remote_validate(args: argparse.Namespace) -> int:
    data = build_remote_validate()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        status_label = "valid" if data["valid"] else "invalid"
        print("Remote job validation")
        print(f"Status: {status_label}")
        print(f"Jobs validated: {data['job_count']}")
        errors = data["errors"]
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
        warnings = data["warnings"]
        print(f"Warnings: {len(warnings)}")
        for w in warnings:
            print(f"  - {w}")
        blockers = data["blockers"]
        print(f"Blockers: {len(blockers)}")
        for b in blockers:
            print(f"  - {b}")
        print()
        print(data["advisory"])
    return 0


def run_remote_jobs(args: argparse.Namespace) -> int:
    data = build_remote_jobs()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        jobs = data["jobs"]
        print("Remote job registry")
        print(f"Jobs: {len(jobs)}")
        if jobs:
            for job in jobs:
                print(f"  [{job['status']}] {job['job_id']} — {job['requested_task']}")
        statuses = data["supported_statuses"]
        print(f"\nSupported statuses ({len(statuses)}):")
        for s in statuses:
            print(f"  - {s}")
        print()
        print(data["advisory"])
    return 0


def run_remote_jobs_list(args: argparse.Namespace) -> int:
    data = load_persisted_jobs(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Remote job listing")
        print(f"Job count: {data['job_count']}")
        for job in data["jobs"]:
            print(f"\n  [{job.get('status', '?')}] {job.get('job_id', '?')}")
            print(f"    Agent:    {job.get('requested_agent', '?')}")
            print(f"    Approval: {job.get('approval_state', '?')}")
            print(f"    Created:  {job.get('created_at', '?')}")
        warnings = data["warnings"]
        if warnings:
            print(f"\nWarnings ({len(warnings)}):")
            for w in warnings:
                print(f"  - {w}")
        print()
        print(data["advisory"])
    return 0


def run_remote_jobs_show(args: argparse.Namespace) -> int:
    try:
        data = inspect_persisted_job(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        job = data["job"]
        print("Remote job details")
        print(f"Job ID:           {job.get('job_id', '?')}")
        print(f"Agent:            {job.get('requested_agent', '?')}")
        print(f"Task:             {job.get('requested_task', '?')}")
        print(f"Execution mode:   {job.get('execution_mode', '?')}")
        print(f"Status:           {job.get('status', '?')}")
        print(f"Approval state:   {job.get('approval_state', '?')}")
        print(f"Created at:       {job.get('created_at', '?')}")
        comp = job.get("policy_compliance", {})
        if isinstance(comp, dict):
            print(f"Policy compliant: {'yes' if comp.get('compliant') else 'no'}")
        checks = job.get("required_checks", [])
        print(f"\nRequired checks ({len(checks)}):")
        for item in checks:
            print(f"  - {item}")
        approvals = job.get("required_approvals", [])
        print(f"\nRequired approvals ({len(approvals)}):")
        for item in approvals:
            print(f"  - {item}")
        notes = job.get("safety_notes", [])
        print(f"\nSafety notes ({len(notes)}):")
        for note in notes:
            print(f"  - {note}")
        print()
        print(data["advisory"])
    return 0


def _run_remote_approval_mutation(args: argparse.Namespace, mutate_fn) -> int:
    try:
        data = mutate_fn(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Job ID:                 {data['job'].get('job_id', '?')}")
        print(f"Previous approval state: {data['previous_approval_state']}")
        print(f"New approval state:      {data['new_approval_state']}")
        print(f"Status:                  {data['job'].get('status', '?')}")
        print()
        print(data["advisory"])
    return 0


def run_remote_approve(args: argparse.Namespace) -> int:
    return _run_remote_approval_mutation(args, approve_remote_job)


def run_remote_deny(args: argparse.Namespace) -> int:
    return _run_remote_approval_mutation(args, deny_remote_job)


def run_remote_ready(args: argparse.Namespace) -> int:
    try:
        data = check_remote_job_readiness(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        status_label = "READY" if data["ready"] else "NOT READY"
        print(f"Execution readiness: {status_label}")
        print(f"Job ID:          {data['job_id']}")
        print(f"Requested agent: {data['requested_agent']}")
        checks = data["checks"]
        passed = sum(1 for v in checks.values() if v is True)
        print(f"Checks passed:   {passed}/{len(checks)}")
        blockers = data["blockers"]
        if blockers:
            print(f"\nBlockers ({len(blockers)}):")
            for b in blockers:
                print(f"  - {b}")
        warnings = data["warnings"]
        if warnings:
            print(f"\nWarnings ({len(warnings)}):")
            for w in warnings:
                print(f"  - {w}")
        print()
        print(data["advisory"])
    return 0


def run_remote_execute(args: argparse.Namespace) -> int:
    invoke = getattr(args, "invoke", False)
    dry_run = getattr(args, "dry_run", False)
    allow_file_changes = getattr(args, "allow_file_changes", False)

    if invoke and allow_file_changes:
        return _run_remote_execute_invoke_file_changes(args)
    if invoke:
        return _run_remote_execute_invoke(args)
    if dry_run:
        return _run_remote_execute_dry_run(args)
    print(
        "Either --dry-run or --invoke is required for 'pcae remote execute'. "
        "No agent was invoked."
    )
    return 1


def _run_remote_execute_dry_run(args: argparse.Namespace) -> int:
    try:
        data = build_remote_execute_dry_run(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        preview = data["execution_preview"]
        status_label = "READY" if preview["readiness_status"] == "ready" else "NOT READY"
        print("Remote execution dry run")
        print(f"Readiness:       {status_label}")
        print(f"Job ID:          {preview['job_id']}")
        print(f"Agent:           {preview['selected_agent']}")
        print(f"Execution mode:  {preview['execution_mode']}")
        print(f"Dry-run result:  {preview['dry_run_result']}")
        cmd = preview.get("command_preview")
        if cmd:
            print(f"\nExecution command preview:\n  {cmd}")
        print(f"\nPrompt preview:\n  {preview['prompt_preview']}")
        blockers = preview["blockers"]
        if blockers:
            print(f"\nBlockers ({len(blockers)}):")
            for b in blockers:
                print(f"  - {b}")
        checks_label = preview.get("required_checks", [])
        if checks_label:
            print(f"\nRequired checks ({len(checks_label)}):")
            for c in checks_label:
                print(f"  - {c}")
        approvals = preview.get("required_approvals", [])
        if approvals:
            print(f"\nRequired approvals ({len(approvals)}):")
            for a in approvals:
                print(f"  - {a}")
        notes = preview.get("safety_notes", [])
        print(f"\nSafety notes ({len(notes)}):")
        for n in notes:
            print(f"  - {n}")
        print()
        print(data["advisory"])
    return 0


def _run_remote_execute_invoke(args: argparse.Namespace) -> int:
    try:
        data = invoke_remote_job(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        status_label = "COMPLETED" if data["final_status"] == "completed" else data["final_status"].upper()
        print("Remote execution result")
        print(f"Job ID:         {data['job_id']}")
        print(f"Agent:          {data['selected_agent']}")
        print(f"Command:        {' '.join(data['command'])}")
        print(f"Started at:     {data.get('started_at', '(not recorded)')}")
        print(f"Finished at:    {data.get('finished_at', '(not recorded)')}")
        duration = data.get("duration_seconds")
        print(f"Duration:       {f'{duration}s' if duration is not None else '(not recorded)'}")
        print(f"Exit code:      {data['exit_code']}")
        print(f"Final status:   {status_label}")
        print(f"Artifact:       {data['output_path']}")
        stdout_summary = data["stdout"][:500] if data["stdout"] else "(none)"
        stderr_summary = data["stderr"][:200] if data["stderr"] else "(none)"
        print(f"\nStdout summary:\n  {stdout_summary}")
        if data["stderr"]:
            print(f"\nStderr summary:\n  {stderr_summary}")
        print()
        print(data["advisory"])
    return 0


def run_remote_plan(args: argparse.Namespace) -> int:
    data = build_remote_plan(HarnessPath.cwd(), requested_agent=args.agent)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Remote Autonomous Coding execution plan")
        print(f"Requested agent: {data['requested_agent']}")
        print(f"Execution mode: {data['execution_mode']}")
        print(f"Readiness: {data['readiness_status']}")
        comp = data["policy_compliance"]
        print("\nPolicy compliance:")
        print(f"  Agent allowed: {'yes' if comp['agent_allowed'] else 'no'}")
        print(f"  Adapter allowed: {'yes' if comp['adapter_allowed'] else 'no'}")
        print(f"  Execution mode allowed: {'yes' if comp['execution_mode_allowed'] else 'no'}")
        print(f"  Compliant: {'yes' if comp['compliant'] else 'no'}")
        approvals = data["required_approvals"]
        print(f"\nRequired approvals ({len(approvals)}):")
        for item in approvals:
            print(f"  - {item}")
        checks = data["required_checks"]
        print(f"\nRequired checks ({len(checks)}):")
        for item in checks:
            print(f"  - {item}")
        blockers = data["blockers"]
        if blockers:
            print(f"\nBlockers ({len(blockers)}):")
            for b in blockers:
                print(f"  - {b}")
        else:
            print("\nBlockers: none")
        gov = data["governance_readiness"]
        print("\nGovernance readiness:")
        print(f"  Session active: {'yes' if gov['session_active'] else 'no'}")
        print(f"  Architecture memory: {'yes' if gov['architecture_memory_present'] else 'no'}")
        print(f"  Active task: {'yes' if gov['active_task_present'] else 'no'}")
        print("\nSafety notes:")
        for note in data["safety_notes"]:
            print(f"  - {note}")
        print()
        print(data["advisory"])
    return 0


def run_remote_policy(args: argparse.Namespace) -> int:
    data = build_remote_policy()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Remote Autonomous Coding execution policy")
        print(f"Approval required: {'yes' if data['approval_required'] else 'no'}")
        print(f"Allowed agents: {', '.join(data['allowed_agents'])}")
        print(f"Allowed adapters: {', '.join(data['allowed_adapters'])}")
        print(f"Allowed execution modes: {', '.join(data['allowed_execution_modes'])}")
        max_files = data["max_files_changed"]
        max_mins = data["max_runtime_minutes"]
        print(f"Max files changed: {max_files if max_files is not None else '(unlimited)'}")
        print(f"Max runtime minutes: {max_mins if max_mins is not None else '(unlimited)'}")
        print(f"Require clean git: {'yes' if data['require_clean_git'] else 'no'}")
        print(f"Require pcae check: {'yes' if data['require_pcae_check'] else 'no'}")
        print(f"Require tests: {'yes' if data['require_tests'] else 'no'}")
        print(
            f"Require human approval before commit: "
            f"{'yes' if data['require_human_approval_before_commit'] else 'no'}"
        )
        print(
            f"Require human approval before push: "
            f"{'yes' if data['require_human_approval_before_push'] else 'no'}"
        )
        ops = data["disallowed_operations"]
        print(f"\nDisallowed operations ({len(ops)}):")
        for op in ops:
            print(f"  - {op}")
        print()
        print(data["advisory"])
    return 0


def run_remote_results(args: argparse.Namespace) -> int:
    job_id: str | None = getattr(args, "job_id", None)
    if job_id is None:
        return _run_remote_results_registry(args)
    return _run_remote_results_single(args, job_id)


def _run_remote_results_registry(args: argparse.Namespace) -> int:
    data = build_remote_results_registry(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Execution result registry")
        print(f"Result count: {data['result_count']}")
        for entry in data["results"]:
            print(f"  Job ID:                {entry['job_id']}")
            print(f"  Agent:                 {entry.get('selected_agent') or '(unknown)'}")
            print(f"  Final status:          {entry.get('final_status') or '(unknown)'}")
            print(f"  Exit code:             {entry.get('exit_code')}")
            print(f"  Duration (s):          {entry.get('duration_seconds')}")
            print(f"  Output classification: {entry.get('output_classification') or '(unknown)'}")
            print(f"  Output path:           {entry.get('output_path')}")
            print(f"  Finished at:           {entry.get('finished_at') or '(not recorded)'}")
            print()
        for warning in data["warnings"]:
            print(f"Warning: {warning}")
        print(data["advisory"])
    return 0


def _run_remote_results_single(args: argparse.Namespace, job_id: str) -> int:
    try:
        data = build_remote_results(HarnessPath.cwd(), job_id)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Execution results")
        print(f"Job ID:          {data['job_id']}")
        print(f"Requested agent: {data['requested_agent']}")
        if not data["result_available"]:
            print("Result:          no execution result available")
        else:
            result = data["execution_result"]
            cmd = result.get("command_used")
            print(f"Command:         {' '.join(cmd) if cmd else '(none)'}")
            started = result.get("execution_started_at")
            print(f"Started at:      {started if started is not None else '(not recorded)'}")
            finished = result.get("execution_finished_at")
            print(f"Finished at:     {finished if finished is not None else '(not recorded)'}")
            duration = result.get("duration_seconds")
            print(f"Duration:        {duration if duration is not None else '(not recorded)'}")
            print(f"Exit code:       {result.get('exit_code')}")
            print(f"Final status:    {result.get('final_status')}")
            print(f"Output path:     {result.get('output_path')}")
            readiness = result.get("readiness_at_execution")
            if readiness is not None:
                print(f"Readiness at execution: {readiness}")
            print(f"Output classification: {result.get('output_classification', '(not recorded)')}")
            stdout_summary = result.get("stdout_summary")
            print(f"\nStdout summary:\n  {stdout_summary or '(none)'}")
            stderr_summary = result.get("stderr_summary")
            if stderr_summary:
                print(f"\nStderr summary:\n  {stderr_summary}")
            normalized = result.get("normalized_final_output")
            if normalized is not None:
                print(f"\nNormalized final output:\n  {normalized}")
        print()
        print(data["advisory"])
    return 0


def run_remote_analytics(args: argparse.Namespace) -> int:
    data = build_remote_execution_analytics(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        a = data["analytics"]
        print("Execution analytics summary")
        print(f"Total executions:       {a['total_executions']}")
        print(f"Successful:             {a['successful_executions']}")
        print(f"Failed:                 {a['failed_executions']}")
        sr = a["success_rate"]
        print(f"Success rate:           {sr if sr is not None else '(no data)'}")
        avg = a["average_duration_seconds"]
        print(f"Average duration (s):   {avg if avg is not None else '(no data)'}")
        fastest = a["fastest_execution"]
        if fastest:
            print(
                f"Fastest execution:      {fastest['job_id']} "
                f"({fastest['duration_seconds']}s, {fastest['selected_agent']})"
            )
        slowest = a["slowest_execution"]
        if slowest:
            print(
                f"Slowest execution:      {slowest['job_id']} "
                f"({slowest['duration_seconds']}s, {slowest['selected_agent']})"
            )
        latest = a["latest_execution"]
        if latest:
            print(
                f"Latest execution:       {latest['job_id']} "
                f"({latest['finished_at']}, {latest['selected_agent']})"
            )
        rm = data["runtime_metrics"]
        if rm:
            print("\nRuntime breakdown")
            for agent, m in sorted(rm.items()):
                print(f"  {agent}:")
                print(f"    Executions:     {m['executions']}")
                print(f"    Successes:      {m['successes']}")
                print(f"    Failures:       {m['failures']}")
                avg_rt = m["average_duration"]
                print(f"    Avg duration:   {avg_rt if avg_rt is not None else '(no data)'}")
        for warning in data["warnings"]:
            print(f"Warning: {warning}")
        print()
        print(data["advisory"])
    return 0


def run_remote_trends(args: argparse.Namespace) -> int:
    data = build_remote_execution_trends(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ts = data["trend_summary"]
        print("Execution trends summary")
        print(f"Total executions:     {ts['total_executions']}")
        print(f"Trend status:         {ts['trend_status']}")
        print(f"Success rate trend:   {ts['success_rate_trend']}")
        print(f"Avg duration trend:   {ts['average_duration_trend']}")
        span = ts["execution_timespan"]
        print(f"Execution timespan:   {f'{span}s' if span is not None else '(no data)'}")
        oldest = ts["oldest_execution"]
        if oldest:
            print(
                f"Oldest execution:     {oldest['job_id']} "
                f"({oldest['selected_agent']}, {oldest['finished_at']})"
            )
        newest = ts["newest_execution"]
        if newest:
            print(
                f"Newest execution:     {newest['job_id']} "
                f"({newest['selected_agent']}, {newest['finished_at']})"
            )
        rt = data["runtime_trends"]
        if rt:
            print("\nRuntime trend breakdown")
            for agent, m in sorted(rt.items()):
                print(f"  {agent}:")
                print(f"    Executions:   {m['execution_count']}")
                sr = m["success_rate"]
                print(f"    Success rate: {sr if sr is not None else '(no data)'}")
                avg = m["average_duration"]
                print(f"    Avg duration: {f'{avg}s' if avg is not None else '(no data)'}")
                fastest = m["fastest_execution"]
                if fastest:
                    print(f"    Fastest:      {fastest['job_id']} ({fastest['duration_seconds']}s)")
                slowest = m["slowest_execution"]
                if slowest:
                    print(f"    Slowest:      {slowest['job_id']} ({slowest['duration_seconds']}s)")
        for warning in data["warnings"]:
            print(f"Warning: {warning}")
        print()
        print(data["advisory"])
    return 0


def run_remote_benchmark(args: argparse.Namespace) -> int:
    data = build_remote_runtime_benchmark(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        bs = data["benchmark_summary"]
        print("Runtime benchmark summary")
        print(f"Total executions: {bs['total_executions']}")
        print(f"Runtimes:         {bs['runtime_count']}")
        print(f"Confidence:       {bs['benchmark_confidence']}")
        r = data["rankings"]
        fastest = r["fastest_runtime"]
        slowest = r["slowest_runtime"]
        highest = r["highest_success_rate"]
        if fastest or slowest or highest:
            print("\nRankings")
            if fastest:
                avg = data["runtime_metrics"][fastest]["average_duration_seconds"]
                print(f"  Fastest runtime:      {fastest} (avg {avg}s)")
            if slowest:
                avg = data["runtime_metrics"][slowest]["average_duration_seconds"]
                print(f"  Slowest runtime:      {slowest} (avg {avg}s)")
            if highest:
                sr = data["runtime_metrics"][highest]["success_rate"]
                print(f"  Highest success rate: {highest} ({sr})")
        rm = data["runtime_metrics"]
        if rm:
            print("\nRuntime metrics")
            for agent, m in rm.items():
                print(f"  {agent}:")
                print(f"    Executions:    {m['execution_count']}")
                print(f"    Success rate:  {m['success_rate']}")
                avg = m["average_duration_seconds"]
                print(f"    Avg duration:  {f'{avg}s' if avg is not None else '(no data)'}")
                fastest_s = m["fastest_execution_seconds"]
                print(f"    Fastest:       {f'{fastest_s}s' if fastest_s is not None else '(no data)'}")
                slowest_s = m["slowest_execution_seconds"]
                print(f"    Slowest:       {f'{slowest_s}s' if slowest_s is not None else '(no data)'}")
                bd = m["output_classification_breakdown"]
                parts = ", ".join(f"{k}={v}" for k, v in bd.items() if v > 0)
                print(f"    Classifications: {parts if parts else 'none'}")
        for warning in data["warnings"]:
            print(f"Warning: {warning}")
        print()
        print(data["advisory"])
    return 0


def _run_remote_execute_invoke_file_changes(args: argparse.Namespace) -> int:
    try:
        data = invoke_remote_job_with_file_changes(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        final_status = data["final_status"]
        status_label = "COMPLETED" if final_status == "completed" else final_status.upper()
        print("Remote execution result (file changes allowed)")
        print(f"Job ID:              {data['job_id']}")
        print(f"Agent:               {data['selected_agent']}")
        print(f"Sandbox mode:        {data.get('sandbox_mode', 'n/a')}")
        print(f"Permission mode:     {data.get('permission_mode', 'n/a')}")
        print(f"Command:             {' '.join(data['command'])}")
        print(f"Pre-execution HEAD:  {data['pre_execution_head']}")
        print(f"Exit code:           {data['exit_code']}")
        print(f"Final status:        {status_label}")
        changed = data["changed_files"]
        if changed:
            print(f"\nChanged files ({len(changed)}):")
            for f in changed:
                print(f"  {f}")
        else:
            print("\nChanged files: none")
        scope = data["scope_validation"]
        scope_label = "PASS" if scope["valid"] else "FAIL"
        print(f"\nScope validation:    {scope_label}")
        for v in scope.get("violations", []):
            print(f"  - {v}")
        diff = data.get("diff_summary", "")
        if diff:
            print(f"\nDiff summary:\n  {diff}")
        stdout_summary = data["stdout"][:500] if data["stdout"] else "(none)"
        print(f"\nStdout summary:\n  {stdout_summary}")
        if data["stderr"]:
            print(f"\nStderr summary:\n  {data['stderr'][:200]}")
        print()
        print(data["advisory"])
    return 0


def run_remote_benchmark_controlled(args: argparse.Namespace) -> int:
    data = build_controlled_benchmark_plan()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        plan = data["benchmark_plan"]
        print("Controlled benchmark plan (dry run)")
        print(f"Runtimes:         {', '.join(plan['runtimes'])}")
        print(f"Identical prompt: {plan['prompt']}")
        print(f"Runs per runtime: {plan['runs_per_runtime']}")
        print(f"Total runs:       {plan['total_planned_runs']}")
        print(f"Execution mode:   {plan['execution_mode']}")
        print(f"Sandbox behavior: {plan['sandbox_behavior']}")
        print(f"Human approval:   required before real execution")
        print("\nPlanned metrics")
        for metric in data["planned_metrics"]:
            print(f"  - {metric}")
        print("\nLimitations")
        for limitation in data["limitations"]:
            print(f"  - {limitation}")
        print()
        print(data["advisory"])
    return 0


def run_remote_file_governance(args: argparse.Namespace) -> int:
    data = build_file_governance_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["governance_design"]
        print("File Modification Governance Design")
        print()

        scope = design["writable_scope_rules"]
        print("Writable Scope Rules")
        print(f"  Repository root: {scope['repository_root_constraint']}")
        print("  Allowed paths:")
        for p in scope["allowed_paths"]:
            print(f"    - {p}")
        print("  Denied paths:")
        for p in scope["denied_paths"]:
            print(f"    - {p}")
        print("  Protected files:")
        for p in scope["protected_files"]:
            print(f"    - {p}")
        print()

        capture = design["change_capture"]
        print("Change Capture")
        for field, desc in capture.items():
            print(f"  {field}: {desc}")
        print()

        approval = design["approval_workflow"]
        print("Approval Workflow")
        print(f"  Human review required: {approval['human_review_required']}")
        print("  Checkpoints:")
        for checkpoint in approval["approval_checkpoints"]:
            print(f"    - {checkpoint}")
        print(f"  Rejection: {approval['rejection_handling']}")
        print()

        commit = design["commit_governance"]
        print("Commit Governance")
        print(f"  {commit['commit_separated_from_modification']}")
        print("  Approval requirements:")
        for req in commit["commit_approval_requirements"]:
            print(f"    - {req}")
        print()

        push = design["push_governance"]
        print("Push Governance")
        print(f"  {push['push_separated_from_commit']}")
        print("  Branch restrictions:")
        for r in push["branch_restrictions"]:
            print(f"    - {r}")
        print()

        rollback = design["rollback_strategy"]
        print("Rollback Strategy")
        print("  Prerequisites:")
        for p in rollback["rollback_prerequisites"]:
            print(f"    - {p}")
        print("  Recovery workflow:")
        for step in rollback["recovery_workflow"]:
            print(f"    - {step}")
        print()

        safety = design["safety_model"]
        print("Safety Model")
        print(f"  Default: {safety['read_only_default']}")
        print(f"  Opt-in:  {safety['file_modifying_opt_in']}")
        print()

        risk = data["risk_model"]
        print("Risk Model")
        print(f"  Levels: {', '.join(risk['risk_levels'])}")
        for level, desc in sorted(risk["classification_scheme"].items()):
            print(f"  {level}: {desc}")
        print(f"  Note: {risk['risk_note']}")
        print()

        print(data["advisory"])
    return 0


def run_remote_changes(args: argparse.Namespace) -> int:
    print("Usage: pcae remote changes <show|approve|deny> JOB_ID [--json]")
    return 1


def run_remote_changes_show(args: argparse.Namespace) -> int:
    try:
        data = build_change_review(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    review = data["change_review"]
    print(f"Change Review — {review['job_id']}")
    print(f"Agent:          {review['requested_agent']}")
    print(f"Final status:   {review['final_status']}")
    print(f"Risk level:     {review['risk_level']}")
    print()
    changed = review["changed_files"]
    if changed:
        print(f"Changed files ({len(changed)}):")
        for f in changed:
            print(f"  {f}")
    else:
        print("Changed files: none")
    print()
    scope = review["scope_validation"]
    scope_label = "PASS" if scope.get("valid") else "FAIL"
    print(f"Scope validation: {scope_label}")
    for v in scope.get("violations", []):
        print(f"  - {v}")
    diff = review.get("diff_summary", "")
    if diff:
        print(f"\nDiff summary:\n  {diff}")
    print()
    print("Approval guidance:")
    print(f"  Approval required: {'yes' if review['approval_required'] else 'no'}")
    print(f"  Commit allowed:    {'yes' if review['commit_allowed'] else 'no'}")
    print(f"  Push allowed:      {'yes' if review['push_allowed'] else 'no'}")
    print()
    print(data["advisory"])
    return 0


def run_remote_changes_approve(args: argparse.Namespace) -> int:
    try:
        data = approve_file_changes(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"Change approval updated — {data['job_id']}")
    print(f"Previous state:  {data['previous_change_approval_state']}")
    print(f"New state:       {data['new_change_approval_state']}")
    print(f"Commit allowed:  {'yes' if data['commit_allowed'] else 'no'}")
    print(f"Push allowed:    {'yes' if data['push_allowed'] else 'no'}")
    print()
    print(data["advisory"])
    return 0


def run_remote_changes_deny(args: argparse.Namespace) -> int:
    try:
        data = deny_file_changes(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"Change approval updated — {data['job_id']}")
    print(f"Previous state:  {data['previous_change_approval_state']}")
    print(f"New state:       {data['new_change_approval_state']}")
    print(f"Commit allowed:  {'yes' if data['commit_allowed'] else 'no'}")
    print(f"Push allowed:    {'yes' if data['push_allowed'] else 'no'}")
    print()
    print(data["advisory"])
    return 0


def run_remote_commit(args: argparse.Namespace) -> int:
    try:
        data = commit_file_changes(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"Commit created — {data['job_id']}")
    print(f"Approval state:  approved")
    changed = data["changed_files"]
    print(f"Changed files ({len(changed)}):")
    for f in changed:
        print(f"  {f}")
    print(f"Commit SHA:      {data['commit_sha']}")
    print(f"Push allowed:    no")
    print()
    print(data["advisory"])
    return 0


def run_remote_rollback_review(args: argparse.Namespace) -> int:
    try:
        data = build_rollback_review(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    review = data["rollback_review"]
    print(f"Rollback Review — {review['job_id']}")
    print(f"Agent:           {review['requested_agent']}")
    print(f"Original commit: {review['original_commit_sha'] or '(none)'}")
    print()
    affected = review["affected_files"]
    if affected:
        print(f"Affected files ({len(affected)}):")
        for f in affected:
            print(f"  {f}")
    else:
        print("Affected files: none")
    print()
    print(f"Rollback recommendation: {review['rollback_mode_recommendation']}")
    print(f"Rollback eligible:       {'yes' if review['rollback_eligible'] else 'no'}")
    for note in review.get("eligibility_notes", []):
        print(f"  Note: {note}")
    print(f"Risk level:              {review['rollback_risk_level']}")
    print()
    print("Approval guidance:")
    print(f"  Approval required: {'yes' if review['rollback_approval_required'] else 'no'}")
    print(f"  Commit required:   {'yes' if review['rollback_commit_required'] else 'no'}")
    print(f"  Push required:     {'yes' if review['rollback_push_required'] else 'no'}")
    print()
    print(data["advisory"])
    return 0


def run_remote_rollback_approve(args: argparse.Namespace) -> int:
    try:
        data = approve_rollback(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"Rollback Approval — {data['job_id']}")
    print(f"Previous rollback approval state: {data['previous_rollback_approval_state']}")
    print(f"New rollback approval state:      {data['new_rollback_approval_state']}")
    print(f"Rollback eligible:                {'yes' if data['rollback_eligible'] else 'no'}")
    print(f"Rollback mode recommendation:     {data['rollback_mode_recommendation']}")
    print()
    print(data["advisory"])
    return 0


def run_remote_rollback_deny(args: argparse.Namespace) -> int:
    try:
        data = deny_rollback(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"Rollback Denial — {data['job_id']}")
    print(f"Previous rollback approval state: {data['previous_rollback_approval_state']}")
    print(f"New rollback approval state:      {data['new_rollback_approval_state']}")
    print(f"Rollback eligible:                {'yes' if data['rollback_eligible'] else 'no'}")
    print(f"Rollback mode recommendation:     {data['rollback_mode_recommendation']}")
    print()
    print(data["advisory"])
    return 0


def run_remote_rollback_execute(args: argparse.Namespace) -> int:
    try:
        data = execute_rollback(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"Rollback Execution — {data['job_id']}")
    print(f"Original commit SHA:  {data['original_commit_sha']}")
    print(f"Rollback commit SHA:  {data['rollback_commit_sha']}")
    print(f"Rollback status:      {data['rollback_status']}")
    print()
    print(data["advisory"])
    return 0


def run_remote_rollback_push(args: argparse.Namespace) -> int:
    try:
        data = push_rollback(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"Rollback Push — {data['job_id']}")
    print(f"Rollback approval state: approved")
    print(f"Rollback commit SHA:     {data['rollback_commit_sha']}")
    print(f"Push status:             {data['push_status']}")
    print(f"Remote branch:           {data['remote_branch']}")
    print()
    print(data["advisory"])
    return 0


def run_remote_rollback_governance(args: argparse.Namespace) -> int:
    data = build_rollback_governance()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    print("Rollback Governance Design")
    print()

    gov = data["rollback_governance"]

    print("Eligibility Model")
    print("  Required conditions:")
    for c in gov["eligibility_model"]["required_conditions"]:
        print(f"    - {c}")
    print("  Blocking conditions:")
    for c in gov["eligibility_model"]["blocking_conditions"]:
        print(f"    - {c}")
    print()

    print("Rollback Modes")
    for mode in data["rollback_modes"]:
        tag = " (preferred)" if mode["preferred"] else ""
        allowed = "allowed" if mode["allowed_by_default"] else "NOT allowed by default"
        print(f"  {mode['mode']}{tag}")
        print(f"    Description: {mode['description']}")
        print(f"    Risk level:  {mode['risk_level']}")
        print(f"    Default:     {allowed}")
        print(f"    Notes:       {mode['notes']}")
    print()

    print("Safety Rules")
    for rule in gov["safety_rules"]:
        print(f"  - {rule}")
    print()

    print("Risk Model")
    for lvl in data["risk_model"]["levels"]:
        print(f"  {lvl['level']}: {lvl['description']}")
    print()

    print("Approval Model")
    am = data["approval_model"]
    print(f"  Rollback review required:   {'yes' if am['rollback_review_required'] else 'no'}")
    print(f"  Rollback approval required: {'yes' if am['rollback_approval_required'] else 'no'}")
    print(f"  Rollback commit separate:   {'yes' if am['rollback_commit_separate'] else 'no'}")
    print(f"  Rollback push separate:     {'yes' if am['rollback_push_separate'] else 'no'}")
    print(f"  Auto rollback allowed:      {'yes' if am['auto_rollback_allowed'] else 'no'}")
    print()

    print(data["advisory"])
    return 0


def run_remote_push(args: argparse.Namespace) -> int:
    try:
        data = push_file_changes(HarnessPath.cwd(), args.job_id)
    except ValueError as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"Push completed — {data['job_id']}")
    print(f"Approval state:  approved")
    print(f"Commit SHA:      {data['commit_sha']}")
    print(f"Push status:     {data['push_status']}")
    print(f"Remote branch:   {data['remote_branch']}")
    for warning in data.get("warnings", []):
        print(f"Warning: {warning}")
    print()
    print(data["advisory"])
    return 0


def run_remote_writable_contract(args: argparse.Namespace) -> int:
    data = build_writable_contract(args.agent_id)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0 if "error" not in data else 1
    if "error" in data:
        print(f"Error: {data['error']}")
        print(data["advisory"])
        return 1
    print(f"Writable Execution Contract — {data['agent_id']}")
    print()
    print(f"Invocation command:    {data['current_invocation_command']}")
    print(f"Writable support:      {data['writable_support_status']}")
    print()
    print("Known read-only behavior:")
    for item in data["known_read_only_behavior"]:
        print(f"  - {item}")
    print()
    print("Required flags (if known):")
    if data["required_flags_if_known"]:
        for flag in data["required_flags_if_known"]:
            print(f"  - {flag}")
    else:
        print("  None confirmed.")
    print()
    dangerous = data.get("dangerous_flags", [])
    if dangerous:
        print("Dangerous flags (not allowed under PCAE governance):")
        for flag in dangerous:
            print(f"  - {flag}")
        print()
    print("Unknowns:")
    for item in data["unknowns"]:
        print(f"  - {item}")
    print()
    print(f"Safety recommendation: {data['safety_recommendation']}")
    print()
    print(data["advisory"])
    return 0


def run_remote_report_export(args: argparse.Namespace) -> int:
    result = export_remote_execution_report(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Export path:      {result['export_path']}")
        print(f"Total executions: {result['total_executions']}")
        sr = result["success_rate"]
        print(f"Success rate:     {sr if sr is not None else '(no data)'}")
        print()
        print(result["advisory"])
    return 0


def run_remote_report_inspect(args: argparse.Namespace) -> int:
    try:
        data = inspect_remote_execution_report(HarnessPath.cwd(), args.report_file)
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Report summary")
        print(f"File:             {args.report_file}")
        print(f"Validation:       {data['validation_status']}")
        report = data["report"]
        if report is not None:
            print(f"Exported at:      {report.get('exported_at', '(not recorded)')}")
            print(f"Total executions: {report.get('total_executions')}")
            print(f"Successful:       {report.get('successful_executions')}")
            print(f"Failed:           {report.get('failed_executions')}")
            sr = report.get("success_rate")
            print(f"Success rate:     {sr if sr is not None else '(no data)'}")
            rb = report.get("runtime_breakdown") or {}
            if rb:
                agents = ", ".join(sorted(rb.keys()))
                print(f"Runtime breakdown: {len(rb)} agent(s) ({agents})")
            latest = report.get("latest_execution")
            if latest:
                print(
                    f"Latest execution: {latest.get('job_id')} "
                    f"({latest.get('selected_agent')})"
                )
            if "report_version" in report:
                print(f"Report version:   {report['report_version']}")
        for warning in data["warnings"]:
            print(f"Warning: {warning}")
        print()
        print(data["advisory"])
    return 0


def _print_capability_registry_data(data: dict) -> None:
    print("Capability registry")
    summary = data["discovery_summary"]
    print(f"Agents: {summary['agents_checked']} checked, "
          f"{summary['agents_installed']} installed, "
          f"{summary['agents_not_installed']} not installed")
    subagent_capable = summary.get("subagent_capable_agents", [])
    swarm_capable = summary.get("swarm_capable_agents", [])
    multi_agent = summary.get("multi_agent_capable_agents", [])
    extensibility = summary.get("extensibility_capable_agents", [])
    print(f"Subagent-capable agents: "
          f"{', '.join(subagent_capable) if subagent_capable else 'none'}")
    print(f"Swarm-capable agents:    "
          f"{', '.join(swarm_capable) if swarm_capable else 'none'}")
    print(f"Multi-agent capable:     "
          f"{', '.join(multi_agent) if multi_agent else 'none'}")
    print(f"Extensibility capable:   "
          f"{', '.join(extensibility) if extensibility else 'none'}")
    print()
    for profile in data["capability_registry"]:
        installed_label = "installed" if profile["installed"] else "not installed"
        ver = profile.get("version") or "(unknown)"
        print(f"{profile['agent_id']} [{profile['lifecycle_status']}, {installed_label}]"
              f" version={ver}")
        caps = profile["capabilities"]
        proven = [c for c in caps if c["confidence"] == "proven"]
        validated = [c for c in caps if c["confidence"] == "validated"]
        observed = [c for c in caps if c["confidence"] == "observed"]
        unknown = [c for c in caps if c["confidence"] == "unknown"]
        if proven:
            print(f"  Proven:    {', '.join(c['name'] for c in proven)}")
        if validated:
            print(f"  Validated: {', '.join(c['name'] for c in validated)}")
        if observed:
            print(f"  Observed:  {', '.join(c['name'] for c in observed)}")
        if unknown:
            print(f"  Unknown:   {', '.join(c['name'] for c in unknown)}")
        sp = profile["subagent_profile"]
        subagent_label = "supported" if sp["supported"] else "not supported"
        print(f"  Subagent:  {subagent_label} [{sp['confidence']}]"
              f" mechanism={sp['mechanism']}")
        print()
    print(data["advisory"])


def run_capability_registry(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_capability_registry(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        _print_capability_registry_data(data)
    return 0


def run_capability_discovery(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_capability_discovery(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Capability discovery")
        print()
        _print_capability_registry_data(data)
    return 0


def run_capability_validation(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_capability_validation(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    fw = data["validation_framework"]
    print("Capability validation framework")
    print()
    print("Confidence lifecycle:")
    for level in fw["lifecycle"]:
        desc = fw["lifecycle_descriptions"][level]
        print(f"  {level}: {desc}")
    print()
    print("Validation sources:")
    for src in fw["validation_sources"]:
        print(f"  - {src}")
    print()
    print("Promotion rules:")
    for rule in fw["promotion_rules"]:
        sources = ", ".join(rule["validation_sources"]) if rule["validation_sources"] else "n/a"
        print(
            f"  {rule['from_confidence']} → {rule['to_confidence']}: "
            f"{rule['required_validation']} (sources: {sources})"
        )
        print(f"    {rule['description']}")
    print()
    print("Validation candidates (per agent):")
    for agent in data["validation_candidates"]:
        installed_label = "installed" if agent["installed"] else "not installed"
        print(f"  {agent['agent_id']} [{installed_label}]")
        if agent["observed_capabilities"]:
            print(f"    Observed:   {', '.join(agent['observed_capabilities'])}")
        if agent["validated_capabilities"]:
            print(f"    Validated:  {', '.join(agent['validated_capabilities'])}")
        if agent["proven_capabilities"]:
            print(f"    Proven:     {', '.join(agent['proven_capabilities'])}")
        next_cands = agent["next_validation_candidates"]
        if next_cands:
            print(f"    Next candidates ({len(next_cands)}):")
            for c in next_cands:
                print(
                    f"      {c['capability']}: {c['promotion_path']} "
                    f"[method: {c['recommended_validation_method']}]"
                )
        else:
            print("    Next candidates: none")
        if agent["recommended_validation_method"] != "not_applicable":
            print(f"    Recommended method: {agent['recommended_validation_method']}")
    print()
    ns = data.get("normalized_summary", {})
    if ns:
        print("Normalized capability groups:")
        _fmt = lambda lst: ", ".join(lst) if lst else "none"
        print(f"  multi_agent_capable:   {_fmt(ns.get('multi_agent_capable_agents', []))}")
        print(f"  extensibility_capable: {_fmt(ns.get('extensibility_capable_agents', []))}")
        print(f"  swarm_capable:         {_fmt(ns.get('swarm_capable_agents', []))}")
        print(f"  subagent_capable:      {_fmt(ns.get('subagent_capable_agents', []))}")
        print()
    print(data["advisory"])
    return 0


def run_orchestration_design(args: argparse.Namespace) -> int:
    data = build_orchestration_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Multi-agent orchestration design")
        print()
        print("Coordinator responsibilities:")
        for resp in data["orchestration_design"]["coordinator_responsibilities"]:
            print(f"  {resp['name']}: {resp['description']}")
        print()
        print("Capability profile model:")
        fields = ", ".join(data["capability_profile_model"]["fields"])
        print(f"  Fields: {fields}")
        cats = ", ".join(data["capability_profile_model"]["capability_categories"])
        print(f"  Capability categories: {cats}")
        print()
        print("Orchestration patterns:")
        for pattern in data["orchestration_patterns"]:
            parallel_label = "parallel" if pattern["parallel"] else "sequential"
            steps = " → ".join(pattern["steps"])
            print(f"  {pattern['pattern']:<18} [{parallel_label}] — {steps}")
            print(f"    {pattern['description']}")
        print()
        print("Governance integration:")
        for rule in data["governance_integration"]["rules"]:
            print(f"  - {rule}")
        print()
        print("Conflict resolution:")
        for policy in data["conflict_resolution"]["policies"]:
            default_label = " (default)" if policy["policy"] == data["conflict_resolution"]["default_policy"] else ""
            print(f"  {policy['policy']}{default_label}: {policy['description']}")
        print(f"  Escalation rule: {data['conflict_resolution']['escalation_rule']}")
        print()
        print("Future agent expansion:")
        for agent in data["future_agent_expansion"]:
            print(f"  {agent['agent_id']} [{agent['status']}]: {agent['notes']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_design(args: argparse.Namespace) -> int:
    data = build_invocation_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        inv = data["invocation_design"]
        print("Controlled agent invocation design")
        print()
        print("Invocation flow:")
        for i, step in enumerate(inv["invocation_flow"], 1):
            print(f"  {i}. {step}")
        print("Result flow:")
        for i, step in enumerate(inv["result_flow"], 1):
            print(f"  {i}. {step}")
        print()
        print("Invocation lifecycle:")
        for stage in data["invocation_lifecycle"]:
            print(f"  {stage['stage']}. {stage['name']}: {stage['description']}")
        print()
        print("Invocation request model fields:")
        print(f"  {', '.join(data['invocation_request_model']['fields'])}")
        print()
        gates = data["safety_gates"]
        print("Safety gates — required before invocation:")
        for gate in gates["required_before_invocation"]:
            print(f"  - {gate}")
        print("Safety gates — blocked if:")
        for condition in gates["blocked_if"]:
            print(f"  - {condition}")
        print()
        wr = data["writable_rules"]
        print(f"Writable invocation — default: {wr['default']}")
        print("Writable invocation requires:")
        for req in wr["writable_requires"]:
            print(f"  - {req}")
        print()
        print("Result capture model fields:")
        print(f"  {', '.join(data['result_capture_model']['fields'])}")
        print()
        gov = data["governance_integration"]
        print("Governance integration:")
        print(f"  System may: {', '.join(gov['system_may'])}")
        print(f"  System may not: {', '.join(gov['system_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_real_planning_design(args: argparse.Namespace) -> int:
    data = build_real_planning_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Real multi-agent planning design")
        print()
        print("Planning lifecycle:")
        for stage in data["planning_lifecycle"]:
            print(f"  {stage['stage']}. {stage['name']}: {stage['description']}")
        print()
        elig = data["planner_eligibility"]
        print("Planner eligibility — planner must:")
        for criterion in elig["criteria"]:
            print(f"  - {criterion}")
        print()
        print("Planning execution modes:")
        for mode in data["execution_modes"]:
            print(f"  {mode['mode']}: {mode['description']}")
        print()
        print("Planning artifact model fields:")
        print(f"  {', '.join(data['planning_artifact_model']['fields'])}")
        print()
        print("Consensus integration (feeds into):")
        for target in data["consensus_integration"]["feeds_into"]:
            print(f"  - {target}")
        print()
        review = data["human_review_model"]
        print("Human review model — human may:")
        for action in review["actions"]:
            print(f"  - {action}")
        print(f"  Human review required: {review['human_review_required']}")
        print()
        gov = data["governance_integration"]
        print("Governance integration:")
        print(f"  System may: {', '.join(gov['system_may'])}")
        print(f"  System may not: {', '.join(gov['system_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_consensus_execution_design(args: argparse.Namespace) -> int:
    data = build_consensus_execution_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Multi-agent consensus execution design")
        print()
        print("Consensus execution lifecycle:")
        for stage in data["execution_lifecycle"]:
            print(f"  {stage['stage']}. {stage['name']}: {stage['description']}")
        print()
        print("Consensus input model fields:")
        print(f"  {', '.join(data['consensus_input_model']['fields'])}")
        print()
        print("Agreement analysis identifies:")
        for item in data["agreement_analysis"]["identifies"]:
            print(f"  - {item}")
        print()
        print("Conflict analysis identifies:")
        for item in data["conflict_analysis"]["identifies"]:
            print(f"  - {item}")
        print()
        print("Weighting model inputs:")
        for item in data["weighting_model"]["inputs"]:
            print(f"  - {item}")
        print()
        print("Recommendation types:")
        for rec in data["recommendation_types"]:
            print(f"  {rec['type']}: {rec['description']}")
        print()
        review = data["human_review_requirements"]
        print("Human review required when:")
        for condition in review["human_required_when"]:
            print(f"  - {condition}")
        print()
        gov = data["governance_integration"]
        print("Governance integration:")
        print(f"  System may: {', '.join(gov['system_may'])}")
        print(f"  System may not: {', '.join(gov['system_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_runtime_execution_prototype(args: argparse.Namespace) -> int:
    data = build_runtime_execution_prototype()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Controlled runtime execution prototype")
        print()
        print("Execution request model fields:")
        print(f"  {', '.join(data['execution_request_model']['fields'])}")
        print()
        print("Adapter resolution steps:")
        for i, step in enumerate(data["adapter_resolution_model"]["steps"], 1):
            print(f"  {i}. {step}")
        print()
        inv = data["runtime_invocation_model"]
        print("Runtime invocation abstraction:")
        print(f"  Execution mode:     {inv['execution_mode']}")
        print(f"  Delivery methods:   {', '.join(inv['delivery_methods'])}")
        print(f"  Output capture:     {inv['output_capture']}")
        print(f"  Timeout enforcement:{inv['timeout_enforcement']}")
        print(f"  Single runtime:     {'yes' if inv['single_runtime'] else 'no'}")
        print(f"  Writable:           {'yes' if inv['writable'] else 'no'}")
        print()
        rc = data["result_capture_model"]
        print("Result capture model fields:")
        print(f"  {', '.join(rc['fields'])}")
        print(f"  Statuses: {', '.join(rc['statuses'])}")
        print()
        print("Timeout handling rules:")
        for rule in data["timeout_model"]["rules"]:
            print(f"  - {rule}")
        print()
        print("Failure types:")
        for ft in data["failure_model"]["types"]:
            print(f"  {ft['type']}: {ft['description']}")
        print()
        restrictions = data["prototype_restrictions"]
        print(f"Prototype restrictions ({len(restrictions)}):")
        for r in restrictions:
            print(f"  - {r}")
        print()
        gov = data["governance_integration"]
        print("Governance integration:")
        print(f"  System may: {', '.join(gov['system_may'])}")
        print(f"  System may not: {', '.join(gov['system_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_planner_adapter_prototype(args: argparse.Namespace) -> int:
    data = build_planner_adapter_prototype()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        proto = data["planner_adapter_prototype"]
        print("Planner adapter prototype")
        print(f"  Planner request ID: {proto['planner_request_id']}")
        print(f"  Selected runtime:   {proto['selected_runtime']}")
        print(f"  Selected agent:     {proto['selected_agent']}")
        print(f"  Capability:         {proto['capability_required']}")
        print(f"  Execution mode:     {proto['execution_mode']}")
        print(f"  Timeout (seconds):  {proto['timeout_seconds']}")
        print()
        res = data["adapter_resolution"]
        print("Adapter resolution:")
        print(f"  Registry lookup:    {res['registry_lookup']}")
        print(f"  Adapter type:       {res['adapter_type']}")
        print(f"  Health check:       {res['health_check']}")
        print(f"  Capability:         {res['capability_verified']}")
        print(f"  Resolution status:  {res['resolution_status']}")
        print()
        inv = data["invocation_preview"]
        print("Invocation preview:")
        print(f"  Command: {inv['invocation_command_preview']}")
        print(f"  Mode:    {inv['execution_mode']}")
        print(f"  Timeout: {inv['timeout_seconds']}s")
        print(f"  Result capture fields: {', '.join(inv['result_capture_model'])}")
        print()
        print("Safety gates:")
        for gate in data["safety_gates"]:
            print(f"  - {gate}")
        print()
        blockers = data["blockers"]
        print(f"Blockers ({len(blockers)}):")
        for b in blockers:
            print(f"  - {b}")
        print()
        print(data["advisory"])
    return 0


def run_adapter_design(args: argparse.Namespace) -> int:
    data = build_adapter_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ad = data["adapter_design"]
        print("Runtime adapter integration design")
        print()
        print("Adapter architecture layers:")
        for i, layer in enumerate(ad["architecture_layers"], 1):
            print(f"  {i}. {layer}")
        print()
        reg = data["adapter_registry"]
        print("Adapter registry responsibilities:")
        for resp in reg["responsibilities"]:
            print(f"  - {resp}")
        print("Adapter registry fields:")
        print(f"  {', '.join(reg['fields'])}")
        print()
        contract = data["adapter_contract"]
        print("Adapter contract required methods:")
        for method in contract["required_methods"]:
            print(f"  - {method}")
        print("Adapter contract optional methods:")
        for method in contract["optional_methods"]:
            print(f"  - {method}")
        print()
        print("Initial runtime adapters:")
        for adapter in ad["initial_adapters"]:
            supports = ", ".join(adapter["supports"])
            print(f"  {adapter['adapter_id']}: {supports}")
        print("Future runtime adapters:")
        for adapter in ad["future_adapters"]:
            print(f"  - {adapter}")
        print()
        health = data["adapter_health_model"]
        print(f"Adapter health states: {', '.join(health['states'])}")
        print(f"Capability sync: {', '.join(health['capability_sync'])}")
        print(f"  {health['capability_registry_note']}")
        print()
        gov = data["governance_integration"]
        print("Governance integration:")
        print(f"  Adapters may: {', '.join(gov['adapters_may'])}")
        print(f"  Adapters may not: {', '.join(gov['adapters_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_execution_framework_design(args: argparse.Namespace) -> int:
    data = build_execution_framework_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        fwd = data["execution_framework_design"]
        print("Agent execution framework design")
        print()
        print("Supported runtimes:")
        for rt in fwd["supported_runtimes"]:
            print(f"  - {rt}")
        print("Future runtimes:")
        for rt in fwd["future_runtimes"]:
            print(f"  - {rt}")
        print()
        print("Execution lifecycle:")
        for stage in data["execution_lifecycle"]:
            print(f"  {stage['stage']}. {stage['name']}: {stage['description']}")
        print()
        contract = data["runtime_adapter_contract"]
        print("Runtime adapter contract fields:")
        print(f"  {', '.join(contract['fields'])}")
        print("Required operations:")
        for op in contract["required_operations"]:
            print(f"  - {op}")
        print()
        print("Execution request model fields:")
        print(f"  {', '.join(data['execution_request_model']['fields'])}")
        print()
        print("Result model fields:")
        print(f"  {', '.join(data['result_model']['fields'])}")
        print()
        gov = data["governance_integration"]
        print("Governance integration:")
        print(f"  Framework may: {', '.join(gov['framework_may'])}")
        print(f"  Framework may not: {', '.join(gov['framework_may_not'])}")
        print(f"  Note: {gov['note']}")
        print()
        fm = data["failure_model"]
        print("Failure model:")
        print(f"  Types: {', '.join(fm['failure_types'])}")
        print(f"  Escalation: {fm['escalation']}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_planning_dry_run(args: argparse.Namespace) -> int:
    data = build_planning_dry_run()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        obj = data["objective"]
        print("Planning dry-run summary")
        print(f"  Objective: {obj['objective_text']}")
        print(f"  Objective ID: {obj['objective_id']}")
        print(f"  Scope: {obj['planning_scope']}")
        caps = ", ".join(obj["required_capabilities"])
        print(f"  Required capabilities: {caps}")
        print()
        sel = data["planner_selection"]
        agents = ", ".join(sel["selected_agents"])
        print(f"Planner selection: {agents}")
        for detail in sel["selection_details"]:
            print(f"  {detail['agent_id']}: {detail['capability_used']} "
                  f"[{detail['confidence_level']}] — {detail['selection_reason']}")
        print()
        print("Simulated plans:")
        for plan in data["simulated_plans"]:
            print(f"  {plan['planner_id']}:")
            for phase in plan["proposed_phases"]:
                print(f"    - {phase}")
            if plan["risks"]:
                print(f"    Risks: {'; '.join(plan['risks'])}")
        print()
        cons = data["simulated_consensus"]
        print("Simulated consensus:")
        print("  Agreements:")
        for item in cons["agreements"]:
            print(f"    - {item}")
        print("  Conflicts:")
        for item in cons["conflicts"]:
            print(f"    - {item}")
        print(f"  Summary: {cons['consensus_summary']}")
        print()
        review = data["human_review"]
        print(f"Human review required: {review['human_decision_required']}")
        for item in review["review_items"]:
            print(f"  - {item}")
        print()
        print("Next actions:")
        for action in data["next_actions"]:
            print(f"  - {action}")
        print()
        print(data["advisory"])
    return 0


def run_planning_execution_design(args: argparse.Namespace) -> int:
    data = build_planning_execution_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Multi-agent planning execution design")
        print()
        print("Planning execution lifecycle:")
        for stage in data["planning_execution_design"]["lifecycle"]:
            print(f"  {stage['stage']}. {stage['name']}: {stage['description']}")
        print()
        print("Planning task model fields:")
        print(f"  {', '.join(data['planning_task_model']['fields'])}")
        print()
        print("Planner runtime requirements:")
        for req in data["planner_runtime_requirements"]:
            print(f"  - {req}")
        print()
        print("Execution modes:")
        for mode in data["execution_modes"]:
            print(f"  {mode['mode']}: {mode['description']}")
        print()
        print("Planning artifact collection fields:")
        print(f"  {', '.join(data['artifact_collection']['fields'])}")
        print()
        print("Consensus integration (feeds into):")
        for target in data["consensus_integration"]["feeds_into"]:
            print(f"  - {target}")
        print()
        gov = data["governance_integration"]
        print("Governance integration:")
        print(f"  Roadmap policy: {gov['roadmap_policy']}")
        print("  Human approval required before:")
        for item in gov["human_approval_required_before"]:
            print(f"    - {item}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_planning_prototype_design(args: argparse.Namespace) -> int:
    data = build_planning_prototype_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Multi-agent planning prototype design")
        print()
        print("Planning objective model fields:")
        print(f"  {', '.join(data['planning_objective_model']['fields'])}")
        print()
        print("Planner selection:")
        caps = ", ".join(data["planner_selection"]["required_capabilities"])
        print(f"  Required capabilities: {caps}")
        print("  Selection rules:")
        for rule in data["planner_selection"]["selection_rules"]:
            print(f"    - {rule}")
        print()
        print("Parallel planning flow:")
        for i, step in enumerate(data["parallel_planning_flow"], 1):
            print(f"  {i}. {step}")
        print()
        print("Planning artifact model fields:")
        print(f"  {', '.join(data['planning_artifact_model']['fields'])}")
        print()
        print("Governance rules:")
        for rule in data["governance_rules"]:
            print(f"  - {rule}")
        print()
        print("Conflict handling:")
        for item in data["conflict_handling"]:
            print(f"  - {item}")
        print()
        print("Future path:")
        for entry in data["planning_prototype_design"]["future_path"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_parallel_execution_design(args: argparse.Namespace) -> int:
    data = build_parallel_execution_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Parallel agent execution design")
        print()
        print("Coordinator responsibilities:")
        for resp in data["parallel_execution_design"]["coordinator_responsibilities"]:
            print(f"  - {resp}")
        print()
        print("Execution topologies:")
        for topo in data["execution_topologies"]:
            parallel_label = "parallel" if topo["parallel"] else "sequential"
            print(f"  {topo['topology']:<24} [{parallel_label}] — {topo['description']}")
        print()
        print("Child task model fields:")
        print(f"  {', '.join(data['child_task_model']['fields'])}")
        print()
        print("Safety rules:")
        for rule in data["safety_rules"]:
            print(f"  - {rule}")
        print()
        print("Failure model:")
        statuses = ", ".join(data["failure_model"]["statuses"])
        print(f"  Statuses: {statuses}")
        print("  Failure handling:")
        for item in data["failure_model"]["failure_handling"]:
            print(f"    - {item}")
        print()
        print("Result aggregation fields:")
        print(f"  {', '.join(data['result_aggregation']['aggregate_fields'])}")
        print()
        print("Governance integration (feeds into):")
        for target in data["governance_integration"]["feeds_into"]:
            print(f"  - {target}")
        print()
        print(data["advisory"])
    return 0


def run_consensus_design(args: argparse.Namespace) -> int:
    data = build_consensus_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Consensus engine architecture design")
        print()
        print("Consensus inputs:")
        fields = ", ".join(data["consensus_design"]["input_fields"])
        print(f"  Fields: {fields}")
        print(f"  Default policy: {data['consensus_design']['default_policy']}")
        print()
        print("Decision types:")
        for dt in data["decision_types"]:
            print(f"  {dt['decision']}: {dt['description']}")
        print()
        print("Consensus policies:")
        for policy in data["consensus_policies"]:
            default_label = " (default)" if policy["is_default"] else ""
            print(f"  {policy['policy']}{default_label}: {policy['description']}")
        print()
        print("Weighting model:")
        print(f"  {data['weighting_model']['description']}")
        print("  Weight sources:")
        for source in data["weighting_model"]["weight_sources"]:
            print(f"    {source['source']}: {source['description']}")
        print()
        print("Conflict handling:")
        print(f"  Rule: {data['conflict_handling']['rule']}")
        print("  Steps:")
        for step in data["conflict_handling"]["steps"]:
            print(f"    - {step}")
        print()
        print("Governance boundaries:")
        gov = data["governance_boundaries"]
        print("  Engine may:")
        for item in gov["engine_may"]:
            print(f"    - {item}")
        print("  Engine may not:")
        for item in gov["engine_may_not"]:
            print(f"    - {item}")
        print(f"  Note: {gov['note']}")
        print()
        print("Future expansions:")
        for ext in data["future_expansions"]:
            print(f"  - {ext}")
        print()
        print(data["advisory"])
    return 0


def run_coordinator_design(args: argparse.Namespace) -> int:
    data = build_coordinator_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Coordinator agent architecture design")
        print()
        print("Coordinator responsibilities:")
        for resp in data["coordinator_design"]["responsibilities"]:
            print(f"  {resp['name']}: {resp['description']}")
        print()
        print("Task classification:")
        classes = ", ".join(data["task_classification"]["supported_task_classes"])
        print(f"  Supported task classes: {classes}")
        print()
        print("Capability-based selection model:")
        model = data["selection_model"]
        print(f"  Rule: {model['rule']}")
        print("  Prohibited hardcoding:")
        for item in model["prohibited_hardcoding"]:
            print(f"    - {item}")
        print("  Selection criteria:")
        for criterion in model["selection_criteria"]:
            print(f"    {criterion['criterion']}: {criterion['description']}")
        print("  Selection output fields:")
        print(f"    {', '.join(model['selection_output_fields'])}")
        print()
        print("Orchestration strategies:")
        for strategy in data["orchestration_strategies"]:
            parallel_label = "parallel" if strategy["parallel"] else "sequential"
            print(f"  {strategy['strategy']:<22} [{parallel_label}] — {strategy['example']}")
            print(f"    {strategy['description']}")
        print()
        print("Governance integration:")
        gov = data["governance_integration"]
        print("  Coordinator may:")
        for item in gov["coordinator_may"]:
            print(f"    - {item}")
        print("  Coordinator may not:")
        for item in gov["coordinator_may_not"]:
            print(f"    - {item}")
        print(f"  Note: {gov['note']}")
        print()
        print("Future agent expansion:")
        agents = ", ".join(data["future_agent_expansion"])
        print(f"  {agents}")
        print()
        print(data["advisory"])
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


def run_multi_agent_prototype(args: argparse.Namespace) -> int:
    data = build_multi_agent_execution_prototype()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        plan = data["execution_plan"]
        print("Multi-agent execution prototype")
        print(f"  Execution ID:           {plan['execution_id']}")
        print(f"  Orchestration strategy: {plan['orchestration_strategy']}")
        print()
        agents = data["selected_agents"]
        roles = plan["assigned_roles"]
        print(f"Selected agents ({len(agents)}):")
        for aid in agents:
            print(f"  {aid:<16} role={roles[aid]}")
        print()
        print(f"Capabilities used: {', '.join(plan['capabilities_used'])}")
        print()
        print("Invocation previews:")
        for inv in data["invocation_previews"]:
            print(f"  {inv['runtime_id']}:")
            print(f"    adapter:  {inv['adapter_id']}")
            print(f"    preview:  {inv['invocation_preview']}")
            print(f"    timeout:  {inv['timeout_seconds']}s")
            print(f"    writable: {'yes' if inv['writable_allowed'] else 'no'}")
        print()
        agg = data["aggregation_plan"]
        rc = agg["result_collection_plan"]
        ac = agg["artifact_collection_plan"]
        ci = agg["consensus_input_plan"]
        print("Aggregation plan:")
        print(
            f"  Result collection: {rc['collection_mode']}, "
            f"per-agent, partial results preserved"
        )
        print(f"  Artifact collection: {ac['collection_mode']}, {ac['persistence']}")
        print(f"  Consensus input: {ci['aggregation']}")
        print()
        gov = data["governance_rules"]
        print("Governance:")
        print(f"  Prototype may:     {', '.join(gov['prototype_may'])}")
        print(f"  Prototype may not: {', '.join(gov['prototype_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_consensus_prototype(args: argparse.Namespace) -> int:
    data = build_consensus_prototype()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Consensus prototype (simulated)")
        print()
        inputs = data["simulated_inputs"]
        print(f"Simulated inputs ({len(inputs)}):")
        for inp in inputs:
            print(
                f"  {inp['agent_id']:<14} "
                f"recommendation={inp['recommendation']:<16} "
                f"confidence={inp['confidence']}"
            )
        print()
        agg = data["aggregation"]
        print("Aggregation:")
        print(f"  Agreement candidates: {', '.join(agg['agreement_candidates'])}")
        print(f"  Conflict candidates:  {', '.join(agg['conflict_candidates'])}")
        print()
        aa = data["agreement_analysis"]
        print(f"Agreement analysis ({aa['agreement_count']} agreement(s)):")
        for a in aa["agreements"]:
            print(f"  - {a}")
        print()
        ca = data["conflict_analysis"]
        cd = ca["confidence_differences"]
        print(f"Conflict analysis ({ca['conflict_count']} conflict(s)):")
        for c in ca["conflicts"]:
            print(f"  - {c}")
        print(
            f"  Confidence spread: {cd['spread']} "
            f"(max={cd['max']}, min={cd['min']})"
        )
        print()
        wp = data["weighting_preview"]
        print("Weighting preview (no real scoring):")
        for w in wp["weights"]:
            print(
                f"  {w['agent_id']:<14} "
                f"capability={w['capability_confidence']:<10} "
                f"task_fit={w['task_fit']:<8} "
                f"role={w['role_fit']:<16} "
                f"weight={w['preview_weight']}"
            )
        print()
        rp = data["recommendation_preview"]
        print("Recommendation preview:")
        print(f"  Recommended outcome:  {rp['recommended_outcome']}")
        print(f"  Basis:                {rp['basis']}")
        print(f"  Human review required: {'yes' if rp['human_review_required'] else 'no'}")
        print(f"  Human review reason:  {rp['human_review_reason']}")
        print()
        gov = data["governance_rules"]
        print("Governance:")
        print(f"  Prototype may:     {', '.join(gov['prototype_may'])}")
        print(f"  Prototype may not: {', '.join(gov['prototype_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_pilot(args: argparse.Namespace) -> int:
    data = build_invocation_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        req = data["pilot_request_model"]
        print("Controlled runtime invocation pilot")
        print()
        print(f"  Default runtime: {req['runtime_id']}")
        print(f"  Governance mode: {req['governance_mode']}")
        print()
        lifecycle = data["pilot_lifecycle"]
        print(f"Pilot lifecycle ({len(lifecycle)} stages):")
        for i, stage in enumerate(lifecycle, 1):
            print(f"  {i}. {stage}")
        print()
        print("Pilot request model fields:")
        print(f"  {', '.join(req['fields'])}")
        print()
        gates = data["safety_gates"]
        print(f"Safety gates ({len(gates)}):")
        for gate in gates:
            print(f"  - {gate}")
        print()
        rc = data["result_capture"]
        print("Result capture fields:")
        print(f"  {', '.join(rc['fields'])}")
        print()
        scope = data["pilot_scope"]
        print(f"Pilot scope ({len(scope)} restrictions):")
        for restriction in scope:
            print(f"  - {restriction}")
        print()
        gov = data["governance_rules"]
        print("Governance:")
        print(f"  Pilot may:     {', '.join(gov['pilot_may'])}")
        print(f"  Pilot may not: {', '.join(gov['pilot_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_multi_runtime_pilot(args: argparse.Namespace) -> int:
    data = build_multi_runtime_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        rs = data["runtime_selection"]
        plan = data["execution_plan"]
        print("Multi-runtime pilot")
        print(f"  Pilot ID:               {plan['pilot_id']}")
        print(f"  Orchestration strategy: {plan['orchestration_strategy']}")
        print()
        runtimes = rs["selected_runtimes"]
        agents = rs["selected_agents"]
        caps = rs["capability_summary"]
        print(f"Selected runtimes ({len(runtimes)}):")
        for rid in runtimes:
            print(
                f"  {rid:<16} agent={agents[rid]:<8} "
                f"capabilities={', '.join(caps[rid])}"
            )
        print()
        previews = data["invocation_previews"]
        print("Invocation previews:")
        for inv in previews:
            print(f"  {inv['runtime_id']}:")
            print(f"    adapter:  {inv['adapter_id']}")
            print(f"    preview:  {inv['invocation_preview']}")
            print(f"    timeout:  {inv['timeout_seconds']}s")
            print(f"    writable: {'yes' if inv['writable_allowed'] else 'no'}")
        print()
        rcp = data["result_capture_plan"]
        print("Result capture plan:")
        print(f"  Expected artifacts:       {', '.join(rcp['expected_artifacts'])}")
        print(f"  Expected recommendations: {', '.join(rcp['expected_recommendations'])}")
        print(f"  Expected confidence:      {rcp['expected_confidence']}")
        print(f"  Expected metadata:        {', '.join(rcp['expected_metadata'])}")
        print()
        cp = data["consensus_preparation"]
        print("Consensus preparation:")
        print(f"  Consensus inputs:    {', '.join(cp['consensus_inputs'])}")
        print(f"  Agreement candidates: {cp['agreement_candidates']}")
        print(f"  Conflict candidates:  {cp['conflict_candidates']}")
        print(f"  Note: {cp['note']}")
        print()
        gov = data["governance_rules"]
        print("Governance:")
        print(f"  Pilot may:     {', '.join(gov['pilot_may'])}")
        print(f"  Pilot may not: {', '.join(gov['pilot_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_consensus_runtime_pilot(args: argparse.Namespace) -> int:
    data = build_consensus_runtime_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Consensus runtime pilot")
        print(f"  Pilot ID: {data['pilot_id']}")
        print()
        print("Runtime pilot summary:")
        rs = data["result_collection"]["runtime_summary"]
        print(f"  Total runtimes:    {rs['total_runtimes']}")
        print(f"  Outputs collected: {rs['outputs_collected']}")
        dist = rs["recommendation_distribution"]
        for rec, count in dist.items():
            print(f"  {rec}: {count}")
        print()
        print("Collected outputs:")
        for out in data["runtime_outputs"]:
            print(f"  {out['runtime_id']}:")
            print(f"    recommendation:   {out['recommendation']}")
            print(f"    confidence:       {out['confidence']}")
            print(f"    rationale:        {out['rationale']}")
            print(f"    artifact_summary: {out['artifact_summary']}")
        print()
        ag = data["agreement_analysis"]
        print("Agreement analysis:")
        print(f"  Matching runtimes:       {', '.join(ag['matching_recommendations'])}")
        print(f"  Matching recommendation: {ag['matching_recommendation']}")
        for ev in ag["supporting_evidence"]:
            print(f"  Evidence: {ev}")
        print()
        cf = data["conflict_analysis"]
        print("Conflict analysis:")
        for conflict in cf["conflicting_recommendations"]:
            print(f"  {conflict['runtime_id']} recommends {conflict['recommendation']}")
            print(f"    conflicts with: {conflict['conflicts_with']}")
        cdiff = cf["confidence_differences"]
        print(f"  Confidence spread: {cdiff['confidence_spread']}")
        for gap in cf["missing_evidence"]:
            print(f"  Missing evidence: {gap}")
        print()
        rp = data["recommendation_preview"]
        print("Recommendation preview:")
        print(f"  Consensus recommendation: {rp['consensus_recommendation']}")
        print(f"  Basis:                    {rp['basis']}")
        print(f"  Human review required:    {'yes' if rp['human_review_required'] else 'no'}")
        print(f"  Human review reason:      {rp['human_review_reason']}")
        print()
        gov = data["governance_rules"]
        print("Governance:")
        print(f"  Pilot may:     {', '.join(gov['pilot_may'])}")
        print(f"  Pilot may not: {', '.join(gov['pilot_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_governed_execution_dry_run(args: argparse.Namespace) -> int:
    data = build_governed_execution_dry_run()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Governed execution dry-run")
        print(f"  Dry-run ID: {data['dry_run_id']}")
        print()
        print("Lifecycle:")
        for stage in data["lifecycle"]:
            print(f"  {stage['step']}. {stage['name']}: {stage['description']}")
        print()
        obj = data["objective_intake"]
        print("Objective intake:")
        print(f"  ID:           {obj['objective_id']}")
        print(f"  Description:  {obj['description']}")
        print(f"  Capabilities: {', '.join(obj['requested_capabilities'])}")
        print(f"  Mode:         {obj['governance_mode']}, writable={obj['writable_allowed']}")
        print()
        cap = data["capability_discovery"]
        print("Capability discovery:")
        print(f"  Coverage:           {cap['coverage']}")
        print(f"  Unmet capabilities: {cap['unmet_capabilities'] or 'none'}")
        for capability, runtimes in cap["discovered_runtimes"].items():
            print(f"  {capability}: {', '.join(runtimes)}")
        print()
        rs = data["runtime_selection"]
        print(f"Runtime selection ({len(rs['selected_runtimes'])} runtimes, basis={rs['selection_basis']}):")
        for rid in rs["selected_runtimes"]:
            print(f"  {rid}")
        print()
        print(f"Invocation plan ({len(data['invocation_plan'])} steps):")
        for step in data["invocation_plan"]:
            print(f"  Step {step['step']}: {step['runtime_id']} [{step['capability']}]")
            print(f"    checkpoint: {step['governance_checkpoint']}, writable={step['writable_allowed']}")
        print()
        srp = data["simulated_result_plan"]
        print("Simulated result plan:")
        print(f"  Collection mode:  {srp['collection_mode']}")
        print(f"  Partial handling: {srp['partial_result_handling']}")
        for outcome in srp["simulated_outcomes"]:
            print(f"  {outcome['runtime_id']}: status={outcome['status']}, confidence={outcome['confidence']}")
        print()
        ch = data["consensus_handoff"]
        print("Consensus handoff:")
        print(f"  Inputs prepared:   {', '.join(ch['inputs_prepared'])}")
        print(f"  Agreement threshold: {ch['agreement_threshold']}")
        print(f"  Conflict escalation: {ch['conflict_escalation']}")
        print(f"  Human review:      {'required' if ch['human_review_required'] else 'optional'}")
        print(f"  Note: {ch['note']}")
        print()
        print("Governance checkpoints:")
        for cp in data["governance_checkpoints"]:
            cmd = cp["command"] or "—"
            print(f"  [{cp['checkpoint']}] {cp['description']}")
            print(f"    command={cmd}, required={cp['required']}")
        print()
        print("Blockers:")
        for blocker in data["blockers"]:
            print(f"  {blocker}")
        print()
        gov = data["governance_rules"]
        print("Governance:")
        print(f"  Dry-run may:     {', '.join(gov['dry_run_may'])}")
        print(f"  Dry-run may not: {', '.join(gov['dry_run_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_contracts(args: argparse.Namespace) -> int:
    data = build_invocation_contracts()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        contracts = data["invocation_contracts"]
        print("Invocation contract validation summary")
        print(f"  Validated runtimes: {len(contracts)}")
        print()
        for contract in contracts:
            rid = contract["runtime_id"]
            ro = contract["read_only"]
            wr = contract["writable"]
            print(f"{rid} [{contract['status']}]")
            print(f"  read-only: {ro['command']}")
            print(f"  writable:  {wr['command']}")
        print()
        invalid = data["invalid_preview_contracts"]
        print(f"Invalid preview contracts ({len(invalid)} — do not use for real execution):")
        for inv in invalid:
            print(f"  [{inv['runtime_id']}] {inv['command']}")
            print(f"    status: {inv['status']}")
            print(f"    reason: {inv['reason']}")
        print()
        gov = data["governance_rules"]
        print("Governance:")
        print(f"  Validation may:     {', '.join(gov['validation_may'])}")
        print(f"  Validation may not: {', '.join(gov['validation_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_execution_readiness(args: argparse.Namespace) -> int:
    data = build_execution_readiness()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        summary = data["readiness_summary"]
        print("Execution readiness assessment")
        print(f"  Assessment ID:  {summary['assessment_id']}")
        print(f"  Overall status: {summary['overall_status']}")
        print(
            f"  Areas: {summary['total_areas']} total — "
            f"{summary['ready']} ready, "
            f"{summary['partially_ready']} partially_ready, "
            f"{summary['not_ready']} not_ready"
        )
        print(f"  Execution safe: {'yes' if summary['execution_safe'] else 'no'}")
        print(f"  Reason: {summary['execution_safe_reason']}")
        print()
        print("Subsystem readiness:")
        for assessment in data["subsystem_assessments"]:
            area = assessment["area"]
            status = assessment["status"]
            met_count = sum(1 for e in assessment["evaluated"] if e["met"])
            total = len(assessment["evaluated"])
            print(f"  [{status}] {area} ({met_count}/{total} criteria met)")
            for ev in assessment["evaluated"]:
                mark = "+" if ev["met"] else "-"
                print(f"    {mark} {ev['criterion']}: {ev['detail']}")
        print()
        gap = data["gap_analysis"]
        print("Gap analysis:")
        print("  Missing implementations:")
        for item in gap["missing_implementations"]:
            print(f"    - {item}")
        print("  Missing validations:")
        for item in gap["missing_validations"]:
            print(f"    - {item}")
        print("  Missing runtime integrations:")
        for item in gap["missing_runtime_integrations"]:
            print(f"    - {item}")
        print()
        print("Recommended next steps:")
        for i, rec in enumerate(data["recommendations"], 1):
            print(f"  {i}. {rec}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_adapter_registry_design(args: argparse.Namespace) -> int:
    data = build_adapter_registry_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Runtime adapter registry design")
        print()
        print("Registry responsibilities:")
        for resp in data["registry_responsibilities"]:
            print(f"  - {resp}")
        print()
        print("Adapter registration model:")
        for field in data["adapter_registration_model"]:
            print(f"  {field['field']} ({field['type']}): {field['description']}")
        print()
        res = data["adapter_resolution"]
        print("Adapter resolution:")
        print("  Input:")
        for k, v in res["input"].items():
            print(f"    {k}: {v}")
        print("  Output:")
        for k, v in res["output"].items():
            print(f"    {k}: {v}")
        print("  Resolution steps:")
        for i, step in enumerate(res["resolution_steps"], 1):
            print(f"    {i}. {step}")
        print(f"  Fallback: {res['fallback']}")
        print()
        hm = data["health_model"]
        print(f"Health model (probe_mode={hm['probe_mode']}):")
        for state in hm["states"]:
            print(f"  {state}: {hm['state_descriptions'][state]}")
        print(f"  Note: {hm['probe_note']}")
        print()
        cs = data["capability_synchronization"]
        print("Capability synchronization:")
        print(f"  Source of truth: {cs['source_of_truth']}")
        print(f"  Registry may receive: {', '.join(cs['registry_may_receive'])}")
        print(f"  Note: {cs['sync_note']}")
        print()
        gov = data["governance_rules"]
        print("Governance:")
        print(f"  Registry may:     {', '.join(gov['registry_may'])}")
        print(f"  Registry may not: {', '.join(gov['registry_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0
