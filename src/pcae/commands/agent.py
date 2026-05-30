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
    build_collaboration_workflows,
    build_lifecycle_report,
    build_multi_agent_registry,
    build_remote_adapters,
    build_remote_approvals,
    build_remote_create_dry_run,
    build_remote_create_persist_preview,
    build_remote_dry_run,
    build_remote_results,
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
    try:
        data = build_remote_results(HarnessPath.cwd(), args.job_id)
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
            stdout_summary = result.get("stdout_summary")
            print(f"\nStdout summary:\n  {stdout_summary or '(none)'}")
            stderr_summary = result.get("stderr_summary")
            if stderr_summary:
                print(f"\nStderr summary:\n  {stderr_summary}")
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
