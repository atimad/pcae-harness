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
    build_roadmap_generation_design,
    ROADMAP_GENERATION_DESIGN_ADVISORY,
    build_roadmap_evidence,
    ROADMAP_EVIDENCE_ADVISORY,
    build_roadmap_proposal_dry_run,
    ROADMAP_PROPOSAL_DRY_RUN_ADVISORY,
    build_multi_agent_roadmap,
    MULTI_AGENT_ROADMAP_ADVISORY,
    build_roadmap_approval_design,
    ROADMAP_APPROVAL_DESIGN_ADVISORY,
    build_prompt_generation_design,
    PROMPT_GENERATION_DESIGN_ADVISORY,
    build_adaptive_prompt_design,
    ADAPTIVE_PROMPT_DESIGN_ADVISORY,
    build_prompt_validation_design,
    PROMPT_VALIDATION_DESIGN_ADVISORY,
    build_prompt_governance_design,
    PROMPT_GOVERNANCE_DESIGN_ADVISORY,
    build_prompt_artifact_design,
    PROMPT_ARTIFACT_DESIGN_ADVISORY,
    build_prompt_approval_workflow,
    PROMPT_APPROVAL_WORKFLOW_ADVISORY,
    build_autonomous_phase_proposal,
    AUTONOMOUS_PHASE_PROPOSAL_ADVISORY,
    build_autonomous_prompt_proposal,
    AUTONOMOUS_PROMPT_PROPOSAL_ADVISORY,
    build_prompt_render,
    PROMPT_RENDER_ADVISORY,
    build_prompt_execution_readiness,
    PROMPT_EXECUTION_READINESS_ADVISORY,
    build_prompt_execution_dry_run,
    PROMPT_EXECUTION_DRY_RUN_ADVISORY,
    build_human_agent_execution_design,
    HUMAN_AGENT_EXECUTION_DESIGN_ADVISORY,
    build_governed_execution_pilot,
    GOVERNED_EXECUTION_PILOT_ADVISORY,
    build_live_execution_readiness,
    LIVE_EXECUTION_READINESS_ADVISORY,
    build_execution_audit_design,
    EXECUTION_AUDIT_DESIGN_ADVISORY,
    build_execution_consensus_framework,
    EXECUTION_CONSENSUS_FRAMEWORK_ADVISORY,
    build_live_execution_pilot,
    LIVE_EXECUTION_PILOT_ADVISORY,
    build_invocation_workload_validation,
    INVOCATION_WORKLOAD_VALIDATION_ADVISORY,
    build_execution_authorization_design,
    EXECUTION_AUTHORIZATION_DESIGN_ADVISORY,
    build_read_only_invocation_pilot,
    READ_ONLY_INVOCATION_PILOT_ADVISORY,
    build_execution_result_review_design,
    EXECUTION_RESULT_REVIEW_ADVISORY,
    build_authorization_expiration_design,
    AUTHORIZATION_EXPIRATION_ADVISORY,
    build_invocation_pilot_status,
    INVOCATION_PILOT_STATUS_ADVISORY,
    build_multi_agent_invocation_pilot,
    MULTI_AGENT_INVOCATION_PILOT_ADVISORY,
    build_execution_quality_design,
    EXECUTION_QUALITY_DESIGN_ADVISORY,
    build_read_only_invocation_execution_pilot,
    READ_ONLY_INVOCATION_EXECUTION_PILOT_ADVISORY,
    build_write_invocation_design,
    WRITE_INVOCATION_DESIGN_ADVISORY,
    build_write_preflight_dry_run,
    WRITE_PREFLIGHT_DRY_RUN_ADVISORY,
    build_write_candidate_design,
    WRITE_CANDIDATE_DESIGN_ADVISORY,
    build_write_invocation_pilot,
    WRITE_INVOCATION_PILOT_ADVISORY,
    build_write_result_review_design,
    WRITE_RESULT_REVIEW_DESIGN_ADVISORY,
    build_write_rollback_validation_design,
    WRITE_ROLLBACK_VALIDATION_DESIGN_ADVISORY,
    build_write_execution_readiness,
    WRITE_EXECUTION_READINESS_ADVISORY,
    build_write_rollback_dry_run,
    build_live_readonly_readiness,
    LIVE_READONLY_READINESS_ADVISORY,
    build_live_write_readiness,
    LIVE_WRITE_READINESS_ADVISORY,
    build_live_readonly_pilot,
    LIVE_READONLY_PILOT_ADVISORY,
    build_rollback_execution_pilot,
    ROLLBACK_EXECUTION_PILOT_ADVISORY,
    build_live_write_pilot,
    LIVE_WRITE_PILOT_ADVISORY,
    build_runtime_contracts,
    RUNTIME_CONTRACT_VERIFICATION_ADVISORY,
    build_governance_audit,
    GOVERNANCE_AUDIT_ADVISORY,
    build_runtime_trust,
    RUNTIME_TRUST_ADVISORY,
    build_governance_maturity,
    GOVERNANCE_MATURITY_ADVISORY,
    build_readonly_invocation,
    READONLY_INVOCATION_ADVISORY,
    build_invocation_result_capture,
    INVOCATION_RESULT_CAPTURE_ADVISORY,
    build_runtime_contract_enforcement,
    RUNTIME_CONTRACT_ENFORCEMENT_ADVISORY,
    build_invocation_authorization_enforcement,
    INVOCATION_AUTHORIZATION_ENFORCEMENT_ADVISORY,
    build_invocation_audit_trail,
    INVOCATION_AUDIT_TRAIL_ADVISORY,
    build_readonly_runtime_pilot,
    READONLY_RUNTIME_PILOT_ADVISORY,
    build_invocation_result_review,
    INVOCATION_RESULT_REVIEW_ADVISORY,
    build_invocation_evidence,
    INVOCATION_EVIDENCE_ADVISORY,
    build_multi_agent_readonly_pilot,
    MULTI_AGENT_READONLY_PILOT_ADVISORY,
    build_consensus_engine,
    CONSENSUS_ENGINE_ADVISORY,
    build_arbitration_framework,
    ARBITRATION_ADVISORY,
    build_evidence_framework,
    EVIDENCE_FRAMEWORK_ADVISORY,
    build_decision_record,
    DECISION_RECORD_ADVISORY,
    build_multi_agent_governance_audit,
    MULTI_AGENT_GOVERNANCE_AUDIT_ADVISORY,
    build_governance_state_audit,
    GOVERNANCE_STATE_AUDIT_ADVISORY,
    build_governance_state_repair,
    GOVERNANCE_STATE_REPAIR_ADVISORY,
    build_task_transition_governance,
    TASK_TRANSITION_GOVERNANCE_ADVISORY,
    build_session_continuity_governance,
    SESSION_CONTINUITY_GOVERNANCE_ADVISORY,
    build_governance_invariants,
    GOVERNANCE_INVARIANTS_ADVISORY,
    build_runtime_safety_invariants,
    RUNTIME_SAFETY_INVARIANTS_ADVISORY,
    build_governance_drift,
    GOVERNANCE_DRIFT_ADVISORY,
    build_governance_drift_review,
    GOVERNANCE_DRIFT_REVIEW_ADVISORY,
    build_agent_lock_governance,
    AGENT_LOCK_GOVERNANCE_ADVISORY,
    build_agent_lock_conflicts,
    AGENT_LOCK_CONFLICTS_ADVISORY,
    build_governance_recovery_plan,
    GOVERNANCE_RECOVERY_PLAN_ADVISORY,
    build_write_authorization,
    WRITE_AUTHORIZATION_ADVISORY,
    build_write_authorization_review,
    WRITE_AUTHORIZATION_REVIEW_ADVISORY,
    build_write_authorization_decision,
    WRITE_AUTHORIZATION_DECISION_ADVISORY,
    build_write_authorization_lifecycle,
    WRITE_AUTHORIZATION_LIFECYCLE_ADVISORY,
    build_write_plan,
    WRITE_PLAN_ADVISORY,
    build_write_readiness,
    WRITE_READINESS_ADVISORY,
    build_write_evidence,
    WRITE_EVIDENCE_ADVISORY,
    build_write_audit,
    WRITE_AUDIT_ADVISORY,
    WRITE_ROLLBACK_DRY_RUN_ADVISORY,
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


def run_roadmap_generation_design(args: argparse.Namespace) -> int:
    data = build_roadmap_generation_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Autonomous roadmap generation design")
        print()
        print("Evidence sources:")
        for src in data["evidence_sources"]:
            print(f"  - {src}")
        print()
        print("Roadmap agent roles:")
        for role in data["agent_roles"]:
            print(f"  {role['role']}: {role['responsibility']}")
        print()
        print("Roadmap generation lifecycle:")
        for i, step in enumerate(data["lifecycle"], 1):
            print(f"  {i}. {step}")
        print()
        print("Roadmap proposal model:")
        for field in data["proposal_model"]:
            print(f"  {field['field']} ({field['type']}): {field['description']}")
        print()
        gov = data["governance_rules"]
        print("Governance rules:")
        print(f"  Proposal may:     {', '.join(gov['proposal_may'])}")
        print(f"  Proposal may not: {', '.join(gov['proposal_may_not'])}")
        print(f"  Human approval required: {gov['human_approval_required']}")
        print(f"  Advisory: {gov['advisory']}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_roadmap_evidence(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_roadmap_evidence(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Roadmap evidence collection")
        print(f"Package: {data['package_id']}  Generated: {data['generated_at']}")
        print()
        print("Evidence sources:")
        for src in data["evidence_sources"]:
            print(f"  - {src}")
        print()
        ps = data["project_summary"]
        print("Repository status:")
        print(f"  Current phase:    {ps['current_phase']}")
        print(f"  Status file:      {ps['status_file_lines']} lines")
        print(f"  Changelog:        {ps['changelog_unreleased_entries']} unreleased entries")
        print(f"  Pending tasks:    {ps['todo_entries']}")
        print(f"  Completed tasks:  {ps['done_entries']}")
        print()
        ts = data["test_summary"]
        print("Test status:")
        print(f"  Total collected:  {ts['total_collected']}")
        print(f"  Executed:         {ts['executed']}")
        print(f"  Passed:           {ts['passed']}")
        print(f"  Failed:           {ts['failed']}")
        print()
        cs = data["capability_summary"]
        print("Capability status:")
        print(f"  Agents:           {cs['agent_count']}")
        print(f"  Installed:        {cs['agents_installed']}")
        print(f"  Capabilities:     {cs['total_declared_capabilities']}")
        print(f"  Multi-agent:      {', '.join(cs['multi_agent_capable'])}")
        print()
        rs = data["readiness_summary"]
        print("Readiness status:")
        print(f"  Overall:          {rs['overall_status']}")
        print(f"  Execution safe:   {rs['execution_safe']}")
        print(f"  Ready:            {rs['subsystems_ready']} / {rs['total_areas']}")
        print(f"  Partially ready:  {rs['subsystems_partially_ready']} / {rs['total_areas']}")
        print()
        print("Identified gaps:")
        for gap in data["identified_gaps"]:
            print(f"  [{gap['gap_id']}] ({gap['category']}) {gap['description']}")
        print()
        print("Candidate roadmap focus areas:")
        for area in data["candidate_focus_areas"]:
            print(f"  [{area['area_id']}] [{area['priority']}] {area['focus_area']}")
            print(f"    {area['rationale']}")
        print()
        print(data["advisory"])
    return 0


def run_roadmap_proposal_dry_run(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_roadmap_proposal_dry_run(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Roadmap proposal dry-run")
        print(f"Proposal: {data['proposal_id']}  Generated: {data['generated_at']}")
        print(f"Evidence:  {data['evidence_package_id']}")
        print()
        ga = data["gap_analysis"]
        print(f"Gap analysis (total: {ga['total']}):")
        print(f"  Readiness gaps:          {len(ga['readiness_gaps'])} {ga['readiness_gaps']}")
        print(f"  Capability gaps:         {len(ga['capability_gaps'])} {ga['capability_gaps']}")
        print(f"  Runtime integration:     {len(ga['runtime_integration_gaps'])} {ga['runtime_integration_gaps']}")
        print(f"  Validation gaps:         {len(ga['validation_gaps'])} {ga['validation_gaps']}")
        print(f"  Governance gaps:         {len(ga['governance_gaps'])} {ga['governance_gaps']}")
        print()
        print(f"Candidate phases ({len(data['candidate_phases'])}):")
        for phase in data["candidate_phases"]:
            print(f"  [{phase['phase_id']}] {phase['title']} (confidence: {phase['confidence']})")
            print(f"    {phase['rationale']}")
            print(f"    evidence_refs: {', '.join(phase['evidence_refs'])}")
        print()
        print("Dependency graph summary:")
        for dep in data["dependencies"]:
            print(f"  {dep['from_phase']} → {dep['to_phase']} [{dep['relationship']}]")
        print(f"  Recommended ordering: {' → '.join(data['recommended_ordering'])}")
        print()
        print(f"Risks ({len(data['risks'])}):")
        for risk in data["risks"]:
            print(f"  [{risk['risk_id']}] ({risk['severity']}) {risk['description']}")
            print(f"    Mitigation: {risk['mitigation']}")
        print()
        print(f"Assumptions ({len(data['assumptions'])}):")
        for i, assumption in enumerate(data["assumptions"], 1):
            print(f"  {i}. {assumption}")
        print()
        print(f"Overall confidence: {data['confidence']}")
        print(f"Human review required: {data['human_decision_required']}")
        print()
        gov = data["governance_rules"]
        print("Governance:")
        print(f"  May:     {', '.join(gov['proposal_may'])}")
        print(f"  May not: {', '.join(gov['proposal_may_not'])}")
        print()
        print(data["advisory"])
    return 0


def run_multi_agent_roadmap(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_multi_agent_roadmap(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Multi-agent roadmap proposal")
        print(f"Proposal: {data['proposal_id']}  Generated: {data['generated_at']}")
        print(f"Dry-run:  {data['dry_run_proposal_id']}")
        print(f"Evidence: {data['evidence_package_id']}")
        print()
        for prop in data["agent_proposals"]:
            print(f"{prop['agent_id']} proposal ({prop['proposal_id']}):")
            print(f"  Recommendation: {prop['recommendation']}  Confidence: {prop['confidence']}")
            print(f"  Rationale: {prop['rationale']}")
            phase_ids = [p["phase_id"] for p in prop["candidate_phases"]]
            print(f"  Phases ({len(phase_ids)}): {', '.join(phase_ids)}")
            print(f"  Risks: {'; '.join(prop['risks'])}")
            print()
        cmp = data["proposal_comparison"]
        print("Proposal comparison:")
        print(f"  Shared recommendations:     {', '.join(cmp['shared_recommendations'])}")
        for agent_id, phases in cmp["unique_recommendations"].items():
            if phases:
                print(f"  Unique to {agent_id}: {', '.join(phases)}")
        for conflict in cmp["conflicting_recommendations"]:
            print(
                f"  Conflict [{conflict['phase_id']}]: "
                f"recommended by {conflict['recommended_by']}, "
                f"not by {conflict['not_recommended_by']}"
            )
        print()
        ca = data["consensus_analysis"]
        print(f"Consensus analysis:")
        print(f"  Agreements ({ca['agreement_count']}): {', '.join(a['phase_id'] for a in ca['agreements'])}")
        print(f"  Conflicts ({ca['conflict_count']}): {', '.join(c['phase_id'] for c in ca['conflicts'])}")
        cd = ca["confidence_differences"]
        print(f"  Confidence: min={cd['min_confidence']} max={cd['max_confidence']} spread={cd['confidence_spread']}")
        rd = ca["recommendation_distribution"]
        print(f"  Votes: approve={rd['approve']} request_changes={rd['request_changes']}")
        print()
        cr = data["consensus_recommendation"]
        print("Consensus recommendation:")
        print(f"  Outcome:              {cr['outcome']}")
        print(f"  Basis:                {cr['basis']}")
        print(f"  Recommended phases:   {', '.join(cr['recommended_phases'])}")
        print(f"  Consensus confidence: {cr['consensus_confidence']}")
        print(f"  Conflict phases:      {', '.join(cr['conflict_phases'])}")
        print()
        hr = data["human_review"]
        print("Human review:")
        print(f"  Required:         {hr['human_review_required']}")
        print(f"  Reason:           {hr['review_reason']}")
        print(f"  Reviewable phases:{', '.join(hr['reviewable_phases'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_roadmap_approval_design(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_roadmap_approval_design(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        wf = data["roadmap_approval_workflow"]
        print("Roadmap approval workflow")
        print(f"Workflow: {wf['workflow_id']}  Generated: {wf['generated_at']}")
        print(f"Proposal: {wf['proposal_id']}")
        print(f"Current approval state: {wf['current_approval_state']}")
        print()
        print("Approval lifecycle:")
        for step in wf["approval_lifecycle"]:
            print(f"  {step['step']}. {step['name']}: {step['description']}")
        print()
        print("Approval states:")
        for state in data["approval_states"]:
            terminal = "terminal" if state["terminal"] else "non-terminal"
            print(f"  {state['state']} ({terminal}): {state['description']}")
        print()
        dm = data["decision_model"]
        print("Decision model:")
        print(f"  Authority:  {dm['decision_authority']}")
        print(f"  Valid:      {', '.join(dm['valid_decisions'])}")
        print(f"  Advisory:   {dm['advisory']}")
        print()
        am = data["artifact_model"]
        print(f"Artifact model: {am['artifact_name']}")
        fields = [f["name"] for f in am["fields"]]
        print(f"  Fields: {', '.join(fields)}")
        print(f"  Creation: {am['artifact_creation']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['approval_workflow_may'])}")
        print(f"  May not: {', '.join(gb['approval_workflow_may_not'])}")
        print()
        print("Future evolution:")
        for entry in data["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_prompt_generation_design(args: argparse.Namespace) -> int:
    data = build_prompt_generation_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["prompt_generation_design"]
        print("Prompt generation design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print(f"Summary: {design['summary']}")
        print()
        print("Prompt generation lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}: {step['description']}")
        print()
        cm = data["canonical_prompt_model"]
        field_names = ", ".join(f["name"] for f in cm["fields"])
        print(f"Canonical prompt model: {cm['model_name']}")
        print(f"  Fields: {field_names}")
        print()
        sections = design["required_sections"]
        print(f"Required sections ({len(sections)}):")
        for s in sections:
            print(f"  - {s}")
        print()
        tm = data["traceability_model"]
        refs = ", ".join(r["field"] for r in tm["required_references"])
        print("Traceability model:")
        print(f"  Required references: {refs}")
        print(f"  Traceability required: {'yes' if tm['traceability_is_required'] else 'no'}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['prompt_generation_may'])}")
        print(f"  May not: {', '.join(gb['prompt_generation_may_not'])}")
        print()
        print("Future evolution:")
        for entry in design["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_adaptive_prompt_design(args: argparse.Namespace) -> int:
    data = build_adaptive_prompt_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["adaptive_prompt_design"]
        print("Adaptive agent-specific prompt generation design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print(f"Summary: {design['summary']}")
        print()
        print("Adaptive prompt lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}: {step['description']}")
        print()
        sel = data["human_agent_selection"]
        agents_str = ", ".join(sel["supported_agents"])
        print("Human agent selection:")
        print(f"  Supported agents: {agents_str}")
        print(f"  Multi-agent allowed: {'yes' if sel['multi_agent_allowed'] else 'no'}")
        print(f"  Selection authority: {sel['selection_authority']}")
        print(f"  PCAE recommendation: {sel['pcae_recommendation']}")
        print()
        print("Agent adaptation profiles:")
        for profile in data["adaptation_profiles"]:
            emphasis = ", ".join(profile["emphasis"])
            print(f"  {profile['agent_id']} ({profile['adaptation_focus']}):")
            print(f"    Style: {profile['style']}")
            print(f"    Emphasis: {emphasis}")
        print()
        ipr = data["intent_preservation_rules"]
        may_change = ", ".join(ipr["adaptation_may_change"])
        must_not = ", ".join(ipr["adaptation_must_not_change"])
        print("Intent preservation rules:")
        print(f"  May change:      {may_change}")
        print(f"  Must not change: {must_not}")
        print(f"  Preservation check required: {'yes' if ipr['preservation_check_required'] else 'no'}")
        print()
        ps = data["prompt_set_model"]
        field_names = ", ".join(f["name"] for f in ps["fields"])
        print(f"Prompt set model: {ps['model_name']}")
        print(f"  Fields: {field_names}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['adaptive_prompt_generation_may'])}")
        print(f"  May not: {', '.join(gb['adaptive_prompt_generation_may_not'])}")
        print()
        print("Future evolution:")
        for entry in design["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_prompt_validation_design(args: argparse.Namespace) -> int:
    data = build_prompt_validation_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["prompt_validation_design"]
        print("Prompt validation framework")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print(f"Summary: {design['summary']}")
        print()
        print(f"Validation categories ({len(data['validation_categories'])}):")
        for cat in data["validation_categories"]:
            print(f"  {cat['category']} (severity: {cat['failure_severity']}): {cat['description']}")
            for rule in cat["rules"]:
                print(f"    - {rule}")
        print()
        sections = data["required_sections"]
        print(f"Required sections ({len(sections)}):")
        for s in sections:
            print(f"  - {s}")
        print()
        tr = data["traceability_requirements"]
        refs = ", ".join(r["field"] for r in tr["required_references"])
        print("Traceability requirements:")
        print(f"  Required references: {refs}")
        print(f"  Traceability required: {'yes' if tr['traceability_is_required'] else 'no'}")
        print(f"  Missing reference severity: {tr['missing_reference_severity']}")
        print()
        print(f"Safety rules ({len(data['safety_rules'])}):")
        for rule in data["safety_rules"]:
            print(f"  - {rule}")
        print()
        vrm = data["validation_result_model"]
        field_names = ", ".join(f["name"] for f in vrm["fields"])
        statuses = ", ".join(vrm["validation_statuses"])
        print(f"Validation result model: {vrm['model_name']}")
        print(f"  Fields: {field_names}")
        print(f"  Statuses: {statuses}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['prompt_validation_may'])}")
        print(f"  May not: {', '.join(gb['prompt_validation_may_not'])}")
        print()
        print("Future evolution:")
        for entry in design["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_prompt_governance_design(args: argparse.Namespace) -> int:
    data = build_prompt_governance_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["prompt_governance_design"]
        print("Prompt governance design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print(f"Summary: {design['summary']}")
        print()
        print("Governance lifecycle:")
        for step in data["governance_lifecycle"]:
            print(f"  {step['step']}. {step['name']}: {step['description']}")
        print()
        print(f"Governed prompt types ({len(data['governed_prompt_types'])}):")
        for pt in data["governed_prompt_types"]:
            req = "requires approval" if pt["requires_approval"] else "no approval required"
            print(f"  {pt['type']}: {pt['description']} ({req})")
        print()
        lm = data["lineage_model"]
        fields = ", ".join(f["name"] for f in lm["tracked_fields"])
        print(f"Lineage model: {lm['model_name']}")
        print(f"  Tracked fields: {fields}")
        print(f"  Append-only: {'yes' if lm['lineage_is_append_only'] else 'no'}")
        print()
        print(f"Approval requirements ({len(data['approval_requirements'])}):")
        for req in data["approval_requirements"]:
            print(f"  - {req}")
        print()
        print(f"Governance states ({len(data['governance_states'])}):")
        for gs in data["governance_states"]:
            terminal = "terminal" if gs["terminal"] else "non-terminal"
            print(f"  {gs['state']} ({terminal}): {gs['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['prompt_governance_may'])}")
        print(f"  May not: {', '.join(gb['prompt_governance_may_not'])}")
        print()
        print("Future evolution:")
        for entry in design["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_prompt_artifact_design(args: argparse.Namespace) -> int:
    data = build_prompt_artifact_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["prompt_artifact_design"]
        print("Prompt artifact design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print(f"Summary: {design['summary']}")
        print()
        print("Prompt artifact lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}: {step['description']}")
        print()
        am = data["artifact_model"]
        print(f"Artifact model: {am['model_name']} ({am['field_count']} fields)")
        for group, fields in am["field_groups"].items():
            names = ", ".join(f["name"] for f in fields)
            print(f"  {group}: {names}")
        print()
        apm = data["adapted_prompt_model"]
        field_names = ", ".join(f["name"] for f in apm["fields"])
        print(f"Adapted prompt model: {apm['model_name']}")
        print(f"  Fields: {field_names}")
        print()
        states = design["artifact_states"]
        print(f"Artifact states ({len(states)}): {', '.join(states)}")
        print()
        inv = data["invariants"]
        print("Invariants:")
        print(f"  Must always have: {', '.join(inv['must_always_have'])}")
        print(f"  Must never allow: {', '.join(inv['must_never_allow'])}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['artifact_model_may'])}")
        print(f"  May not: {', '.join(gb['artifact_model_may_not'])}")
        print()
        print("Future evolution:")
        for entry in design["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_prompt_approval_workflow(args: argparse.Namespace) -> int:
    data = build_prompt_approval_workflow()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        wf = data["prompt_approval_workflow"]
        print("Prompt approval workflow")
        print(f"Workflow: {wf['workflow_id']}  Generated: {wf['generated_at']}")
        print(f"Phase: {wf['phase']} — {wf['title']}")
        print(f"Summary: {wf['summary']}")
        print()
        print("Approval lifecycle:")
        for step in data["approval_lifecycle"]:
            print(f"  {step['step']}. {step['name']}: {step['description']}")
        print()
        print("Approval states:")
        for state in data["approval_states"]:
            terminal = "terminal" if state["terminal"] else "non-terminal"
            print(f"  {state['state']} ({terminal}): {state['description']}")
        print()
        reqs = data["approval_requirements"]
        print(f"Approval requirements ({len(reqs)}):")
        for req in reqs:
            print(f"  - {req}")
        print()
        am = data["approved_artifact_model"]
        field_names = ", ".join(f["name"] for f in am["fields"])
        print(f"Approved artifact model: {am['model_name']}")
        print(f"  Fields: {field_names}")
        print(f"  Immutable after approval: {'yes' if am['artifact_is_immutable_after_approval'] else 'no'}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['approval_workflow_may'])}")
        print(f"  May not: {', '.join(gb['approval_workflow_may_not'])}")
        print()
        print("Future evolution:")
        for entry in wf["future_evolution"]:
            print(f"  {entry['phase']}: {entry['description']}")
        print()
        print(data["advisory"])
    return 0


def run_autonomous_phase_proposal(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_autonomous_phase_proposal(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        proposal = data["autonomous_phase_proposal"]
        print("Autonomous phase proposal")
        print(f"Proposal: {proposal['proposal_id']}  Generated: {proposal['generated_at']}")
        print(f"Phase: {proposal['phase']} — {proposal['title']}")
        print(f"Evidence package: {proposal['evidence_package_id']}")
        print()
        print("Candidate phases:")
        for phase in data["candidate_phases"]:
            deps = ", ".join(phase["dependencies"]) if phase["dependencies"] else "none"
            print(f"  {phase['phase_id']}: {phase['title']}")
            print(f"    Rationale: {phase['rationale']}")
            print(f"    Confidence: {phase['confidence']}")
            print(f"    Dependencies: {deps}")
        print()
        print("Priorities:")
        for p in data["priorities"]:
            print(
                f"  {p['priority']}. {p['phase_id']}:"
                f" impact={p['impact_estimate']},"
                f" complexity={p['implementation_complexity']}"
            )
        print()
        print("Dependency analysis:")
        for dep in data["dependencies"]:
            prereqs = ", ".join(dep["prerequisite_phases"]) if dep["prerequisite_phases"] else "none"
            print(f"  {dep['phase_id']}: prerequisites={prereqs}, order={dep['recommended_ordering']}")
        print()
        print(f"Risks ({len(data['risks'])}):")
        for risk in data["risks"]:
            print(f"  - {risk}")
        print()
        print(f"Overall confidence: {data['confidence']}")
        print(f"Human review required: {'yes' if data['human_review_required'] else 'no'}")
        print()
        print(data["advisory"])
    return 0


def run_autonomous_prompt_proposal(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_autonomous_prompt_proposal(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        proposal = data["autonomous_prompt_proposal"]
        print("Autonomous prompt proposal")
        print(f"Proposal: {proposal['proposal_id']}  Generated: {proposal['generated_at']}")
        print(f"Phase: {proposal['phase']} — {proposal['title']}")
        print(f"Selected phase: {proposal['selected_phase_id']}")
        print()
        cp = data["canonical_prompt"]
        print("Canonical prompt:")
        print(f"  ID: {cp['prompt_id']}")
        print(f"  Phase: {cp['phase_id']}")
        print(f"  Title: {cp['title']}")
        objective_preview = cp["objective"][:80] + "..." if len(cp["objective"]) > 80 else cp["objective"]
        print(f"  Objective: {objective_preview}")
        deps = ", ".join(cp["dependencies"]) if cp["dependencies"] else "none"
        print(f"  Dependencies: {deps}")
        print(f"  Acceptance criteria: {len(cp['acceptance_criteria'])} items")
        print()
        print("Adapted prompts:")
        for ap in data["adapted_prompts"]:
            preview = ap["prompt_text"][:60] + "..." if len(ap["prompt_text"]) > 60 else ap["prompt_text"]
            print(f"  {ap['agent_id']} ({ap['adaptation_profile']}): {preview}")
        print()
        vs = data["validation_summary"]
        print(f"Validation summary: status={vs['validation_status']}")
        print(f"  Canonical prompt valid: {'yes' if vs['canonical_prompt_valid'] else 'no'}")
        print(f"  Adapted prompts valid: {'yes' if vs['adapted_prompts_valid'] else 'no'}")
        print(f"  Intent preservation valid: {'yes' if vs['intent_preservation_valid'] else 'no'}")
        print()
        ips = data["intent_preservation_status"]
        print("Intent preservation summary:")
        for check in ips["checks_performed"]:
            status = "preserved" if ips.get(check, False) else "not preserved"
            print(f"  {check}: {status}")
        print(f"  Overall: {ips['overall_status']}")
        print()
        print(f"Confidence: {data['confidence']}")
        print(f"Human review required: {'yes' if data['human_review_required'] else 'no'}")
        print()
        print(data["advisory"])
    return 0


def run_prompt_render(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = build_prompt_render(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        sep = "=" * 49
        rps = data["rendered_prompt_set"]
        print(f"Render: {rps['render_id']}  Generated: {rps['generated_at']}")
        print(f"Phase: {rps['phase']} — {rps['title']}")
        print(f"Selected phase: {rps['selected_phase_id']}")
        print()

        print(sep)
        print("Canonical Prompt")
        print(sep)
        print()
        print(rps["canonical_prompt_text"])
        print()

        agent_labels = {
            "codex-local": "Codex Prompt",
            "claude-local": "Claude Prompt",
            "kimi-local": "Kimi Prompt",
        }
        for ap in data["adapted_prompts"]:
            agent_id = ap["agent_id"]
            label = agent_labels.get(agent_id, f"{agent_id} Prompt")
            print(sep)
            print(label)
            print(sep)
            print()
            print(rps["adapted_prompt_texts"].get(agent_id, ""))
            print()

        print(sep)
        print("Intent Preservation Summary")
        print(sep)
        print()
        ips = data["intent_preservation_summary"]
        for check in ips.get("checks_performed", []):
            status = "preserved" if ips.get(check, False) else "not preserved"
            print(f"  {check}: {status}")
        print(f"  Overall: {ips.get('overall_status', 'unknown')}")
        print()
        print(f"Human review required: {'yes' if data['human_review_required'] else 'no'}")
        print()
        print(data["advisory"])
    return 0


def run_prompt_execution_readiness(args: argparse.Namespace) -> int:
    data = build_prompt_execution_readiness()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        summary = data["readiness_summary"]
        print("Prompt execution readiness assessment")
        print(f"Assessment: {summary['assessment_id']}  Generated: {summary['generated_at']}")
        print(f"Phase: {summary['phase']} — {summary['title']}")
        print()
        print(f"Overall status: {summary['overall_status']}")
        print(f"Execution recommended: {'yes' if summary['execution_recommended'] else 'no'}")
        print(f"Human review required: {'yes' if summary['human_review_required'] else 'no'}")
        print(
            f"Areas: {summary['area_count']} total"
            f" ({summary['ready_count']} ready,"
            f" {summary['partially_ready_count']} partially_ready,"
            f" {summary['not_ready_count']} not_ready)"
        )
        print()
        print("Readiness by area:")
        for area in data["readiness_areas"]:
            print(f"  {area['area']}: {area['readiness_status']}")
            for blocker in area["blockers"]:
                print(f"    ! {blocker}")
        print()
        print(f"Gaps ({summary['gap_count']}):")
        for gap in data["gaps"]:
            areas_str = ", ".join(gap["affected_areas"])
            print(f"  [{gap['severity']}] {gap['gap_id']}: {gap['description']}")
            print(f"    Affected: {areas_str}")
        print()
        print(f"Risks ({summary['risk_count']}):")
        for risk in data["risks"]:
            print(f"  [{risk['severity']}] {risk['risk_id']}: {risk['description']}")
        print()
        print("Recommendations:")
        for rec in data["recommendations"]:
            if rec["recommended_next_steps"]:
                print(f"  {rec['area']} ({rec['readiness_status']}):")
                for step in rec["recommended_next_steps"]:
                    print(f"    - {step}")
        print()
        print(data["advisory"])
    return 0


def run_prompt_execution_dry_run(args: argparse.Namespace) -> int:
    data = build_prompt_execution_dry_run()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        result = data["dry_run_result"]
        plan = data["execution_plan"]
        print("Prompt execution dry-run")
        print(f"Execution: {result['execution_id']}  Generated: {result['generated_at']}")
        print(f"Phase: {result['phase']} — {result['title']}")
        print()
        print(f"Execution status:  {result['execution_status']}")
        print(f"Governance status: {result['governance_status']}")
        print(f"Runtime status:    {result['runtime_status']}")
        print(f"Readiness status:  {result['readiness_status']}")
        print(f"Human review required: {'yes' if result['human_review_required'] else 'no'}")
        print()
        print("Execution plan:")
        print(f"  Selected prompt: {plan['selected_prompt']['prompt_id']}")
        print(f"  Target agents:   {', '.join(plan['target_agents'])}")
        for step in plan["invocation_plan"]:
            print(
                f"  [{step['agent_id']}] runtime={step['runtime']}"
                f" adapter={step['adapter']} simulated={step['simulated']}"
            )
        print()
        print("Governance gate results:")
        for gate in data["governance_results"]["gate_results"]:
            print(f"  {gate['gate']}: {gate['status']}")
            print(f"    {gate['rationale']}")
        print()
        print("Runtime resolution:")
        for agent in data["runtime_results"]["agents"]:
            print(f"  {agent['agent_id']}: {agent['resolution_status']}")
            for note in agent["notes"]:
                print(f"    - {note}")
        print()
        print(f"Blockers ({result['blocker_count']}):")
        for blocker in data["blockers"]:
            print(f"  [{blocker['severity']}] {blocker['blocker_id']}: {blocker['description']}")
        print()
        print(f"Warnings ({result['warning_count']}):")
        for warning in data["warnings"]:
            print(f"  [{warning['severity']}] {warning['warning_id']}: {warning['description']}")
        print()
        print("Recommendations:")
        for rec in data["recommendations"]:
            print(f"  {rec['area']} (→ {rec['target_phase']}):")
            for step in rec["recommended_next_steps"]:
                print(f"    - {step}")
        print()
        print(data["advisory"])
    return 0


def run_human_agent_execution_design(args: argparse.Namespace) -> int:
    data = build_human_agent_execution_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["human_agent_execution_design"]
        print("Human-selected agent execution design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Human agent selection lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}")
            print(f"     {step['description']}")
        print()
        print("Human selection options:")
        for opt in data["selection_options"]:
            roles = ", ".join(opt["recommended_for"])
            print(
                f"  {opt['agent_id']}: variant={opt['prompt_variant']}"
                f" mode={opt['invocation_mode']} recommended_for=[{roles}]"
            )
        print()
        print("Agent compatibility checks:")
        for chk in data["compatibility_checks"]:
            print(f"  {chk['check_id']}: {chk['check']}")
            print(f"    {chk['description']}")
            print(f"    required={chk['required']}  failure_action={chk['failure_action']}")
        print()
        print("Prompt variant selection rules:")
        for rule in data["prompt_variant_selection"]:
            print(
                f"  {rule['agent_id']}: variant={rule['variant']}"
                f" profile={rule['adaptation_profile']}"
            )
        print()
        print("Execution candidate model:")
        ecm = data["execution_candidate_model"]
        for field in ecm["fields"]:
            print(f"  {field['name']} ({field['type']}): {field['description']}")
        print(f"  creation_triggers_execution: {ecm['creation_triggers_execution']}")
        print(f"  human_authorization_required: {ecm['human_authorization_required']}")
        print()
        print(f"Blockers ({design['blocker_count']}):")
        for blocker in data["blockers"]:
            print(f"  [{blocker['severity']}] {blocker['blocker_id']}: {blocker['description']}")
        print()
        print("Governance boundaries:")
        gb = data["governance_boundaries"]
        print(f"  May:     {', '.join(gb['design_may'])}")
        print(f"  May not: {', '.join(gb['design_may_not'])}")
        print(f"  Human selection authoritative: {gb['human_selection_authoritative']}")
        print(f"  PCAE recommendation advisory:  {gb['pcae_recommendation_advisory']}")
        print(f"  Human review required:         {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_governed_execution_pilot(args: argparse.Namespace) -> int:
    data = build_governed_execution_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        pilot = data["governed_execution_pilot"]
        print("Governed execution pilot")
        print(f"Pilot: {pilot['pilot_id']}  Generated: {pilot['generated_at']}")
        print(f"Phase: {pilot['phase']} — {pilot['title']}")
        print()
        print(pilot["summary"])
        print()
        print("Governed execution lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}")
            print(f"     {step['description']}")
        print()
        print("Governance gate results:")
        gov = data["governance_results"]
        for gate in gov["gate_results"]:
            print(f"  {gate['gate']}: {gate['status']}")
            print(f"    {gate['rationale']}")
        print(
            f"  Overall: {gov['overall_governance_status']}"
            f" ({gov['blocked_count']} blocked,"
            f" {gov['pending_count']} pending,"
            f" {gov['advisory_count']} advisory)"
        )
        print()
        print("Runtime resolution:")
        rt = data["runtime_results"]
        for agent in rt["agents"]:
            print(f"  {agent['agent_id']}: {agent['overall_resolution']}")
            for note in agent["notes"]:
                print(f"    - {note}")
        print(f"  Overall: {rt['overall_runtime_status']}")
        print()
        auth = data["authorization_results"]
        print("Authorization results:")
        print(f"  Authorization: {auth['authorization_id']}")
        print(f"  Status:        {auth['authorization_status']}")
        print(f"  Governance:    {auth['governance_status']}")
        print(f"  Runtime:       {auth['runtime_status']}")
        print(f"  Blockers:      {auth['blocker_count']}")
        print(f"  Warnings:      {auth['warning_count']}")
        print()
        print(f"Blockers ({pilot['blocker_count']}):")
        for blocker in data["blockers"]:
            print(f"  [{blocker['severity']}] {blocker['blocker_id']}: {blocker['description']}")
        print()
        print("Audit summary:")
        ar = data["audit_record"]
        print(f"  Audit:    {ar['audit_id']}")
        print(f"  Prompt:   {ar['prompt_id']}")
        print(f"  Agents:   {', '.join(ar['selected_agents'])}")
        print(f"  Result:   {ar['authorization_result']['authorization_status']}")
        print()
        print("Recommendations:")
        for rec in data["recommendations"]:
            print(f"  [{rec['area']} → {rec['target_phase']}] {rec['description']}")
        print()
        print(data["advisory"])
    return 0


def run_live_execution_readiness(args: argparse.Namespace) -> int:
    data = build_live_execution_readiness()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        summary = data["readiness_summary"]
        print("Live execution readiness assessment")
        print(f"Assessment: {summary['assessment_id']}  Generated: {summary['generated_at']}")
        print(f"Phase: {summary['phase']} — {summary['title']}")
        print()
        print(f"Overall status:              {summary['overall_status']}")
        print(f"Live execution recommended:  {'yes' if summary['live_execution_recommended'] else 'no'}")
        print(f"Human review required:       {'yes' if summary['human_review_required'] else 'no'}")
        print(
            f"Areas: {summary['area_count']} total"
            f" ({summary['ready_count']} ready,"
            f" {summary['partially_ready_count']} partially_ready,"
            f" {summary['not_ready_count']} not_ready)"
        )
        print()
        print("Readiness by area:")
        for area in data["readiness_areas"]:
            print(f"  {area['area']}: {area['readiness_status']}")
            for blocker in area["blockers"]:
                print(f"    ! {blocker}")
        print()
        print(f"Blockers ({summary['blocker_count']}):")
        for blocker in data["blockers"]:
            print(f"  [{blocker['severity']}] {blocker['blocker_id']}: {blocker['description']}")
            print(f"    Category: {blocker['category']}  Blocks: {blocker['blocks_area']}")
        print()
        print(f"Risks ({summary['risk_count']}):")
        for risk in data["risks"]:
            print(f"  [{risk['severity']}] {risk['risk_id']}: {risk['description']}")
        print()
        print("Recommendations:")
        for rec in data["recommendations"]:
            if rec["recommended_actions"]:
                print(f"  {rec['area']} ({rec['readiness_status']}):")
                for action in rec["recommended_actions"]:
                    print(f"    - {action}")
        print()
        print(data["advisory"])
    return 0


def run_execution_audit_design(args: argparse.Namespace) -> int:
    data = build_execution_audit_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["execution_audit_design"]
        print("Execution audit storage design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Audit lifecycle:")
        for step in data["audit_lifecycle"]:
            print(f"  {step['step']}. {step['name']}")
            print(f"     {step['description']}")
        print()
        print("Audit record model (ExecutionAuditRecord):")
        ecm = data["audit_record_model"]
        print(f"  Fields: {ecm['field_count']}  Required: {ecm['required_field_count']}")
        for group in ecm["field_groups"]:
            fields_in_group = [f for f in ecm["fields"] if f["group"] == group]
            if fields_in_group:
                print(f"  [{group}]")
                for field in fields_in_group:
                    req = "required" if field["required"] else "optional"
                    print(f"    {field['name']} ({field['type']}, {req}): {field['description']}")
        print(f"  All fields immutable after creation: {ecm['all_fields_immutable_after_creation']}")
        print()
        print("Storage invariants:")
        for inv in data["storage_invariants"]:
            print(f"  {inv['invariant']} = {inv['value']}")
            print(f"    {inv['description']}")
            print(
                f"    enforcement={inv['enforcement']}"
                f"  violation_severity={inv['violation_severity']}"
            )
        print()
        print("Query model:")
        for q in data["query_model"]:
            indexed = "indexed" if q["index_required"] else "unindexed"
            print(f"  {q['query_field']} ({indexed}): {q['description']}")
        print()
        print("Retention requirements:")
        ret = data["retention_requirements"]
        print(f"  retention_required:      {ret['retention_required']}")
        print(f"  audit_history_required:  {ret['audit_history_required']}")
        print(f"  minimum_retention:       {ret['minimum_retention_period']}")
        print(f"  pruning_allowed:         {ret['pruning_allowed']}")
        print(f"  archival_allowed:        {ret['archival_allowed']}")
        print()
        print("Governance boundaries:")
        gb = data["governance_boundaries"]
        print(f"  May:     {', '.join(gb['audit_system_may'])}")
        print(f"  May not: {', '.join(gb['audit_system_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_execution_consensus_framework(args: argparse.Namespace) -> int:
    data = build_execution_consensus_framework()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["execution_consensus_design"]
        print("Execution consensus framework design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Consensus lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}")
            print(f"     {step['description']}")
        print()
        print("Consensus modes:")
        for mode in data["consensus_modes"]:
            print(f"  {mode['mode']}")
            print(f"    {mode['description']}")
        print()
        print("Conflict detection rules:")
        for rule in data["conflict_detection_rules"]:
            print(f"  {rule['conflict_type']} (severity={rule['severity']})")
            print(f"    {rule['description']}")
        print()
        print("Resolution rules:")
        rr = data["resolution_rules"]
        print(f"  May:     {', '.join(rr['framework_may'])}")
        print(f"  May not: {', '.join(rr['framework_may_not'])}")
        print()
        print("Consensus record model (ConsensusAuditRecord):")
        crm = data["consensus_record_model"]
        print(f"  Fields: {crm['field_count']}  Required: {crm['required_field_count']}")
        for field in crm["fields"]:
            req = "required" if field["required"] else "optional"
            print(f"    {field['name']} ({field['type']}, {req}): {field['description']}")
        print(f"  All fields immutable after creation: {crm['all_fields_immutable_after_creation']}")
        print()
        print("Governance boundaries:")
        gb = data["governance_boundaries"]
        print(f"  May:     {', '.join(gb['framework_may'])}")
        print(f"  May not: {', '.join(gb['framework_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_live_execution_pilot(args: argparse.Namespace) -> int:
    data = build_live_execution_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        pilot = data["live_execution_pilot"]
        print("Governed live execution pilot design")
        print(f"Pilot: {pilot['pilot_id']}  Generated: {pilot['generated_at']}")
        print(f"Phase: {pilot['phase']} — {pilot['title']}")
        print()
        print(pilot["summary"])
        print()
        print("Pilot lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}")
            print(f"     {step['description']}")
        print()
        print("Required gates:")
        for gate in data["required_gates"]:
            blocking = "blocking" if gate["blocking"] else "advisory"
            print(f"  {gate['gate']} ({blocking})")
            print(f"    {gate['description']}")
        print()
        print("Runtime pilot plan:")
        for runtime in data["runtime_pilot_plan"]:
            print(f"  {runtime['runtime']}")
            print(f"    invocation_contract: {runtime['invocation_contract_status']}")
            print(f"    adapter:             {runtime['adapter_status']}")
            print(f"    sandbox:             {runtime['sandbox_status']}")
            print(f"    workload_readiness:  {runtime['execution_workload_readiness']}")
        print()
        print("Audit integration:")
        for artifact in data["audit_integration"]:
            print(f"  {artifact['artifact']}")
            print(f"    {artifact['description']}")
        print()
        print("Consensus integration:")
        for path in data["consensus_integration"]:
            escalation = "human escalation" if path["human_escalation"] else "no human escalation"
            print(f"  {path['path']} ({escalation})")
            print(f"    {path['description']}")
        print()
        print("Blockers:")
        for blocker in data["blockers"]:
            print(f"  [{blocker['blocker_id']}] {blocker['category']} (severity={blocker['severity']})")
            print(f"    {blocker['description']}")
        print()
        print("Recommendations:")
        for rec in data["recommendations"]:
            print(f"  - {rec}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['pilot_may'])}")
        print(f"  May not: {', '.join(gb['pilot_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_workload_validation(args: argparse.Namespace) -> int:
    data = build_invocation_workload_validation()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        val = data["invocation_workload_validation"]
        print("Invocation workload validation")
        print(f"Validation: {val['validation_id']}  Generated: {val['generated_at']}")
        print(f"Phase: {val['phase']} — {val['title']}")
        print()
        print(val["summary"])
        print()
        print("Workload types:")
        for wt in data["workload_types"]:
            write = "write_allowed" if wt["write_allowed"] else "read_only"
            print(f"  {wt['workload_type']} ({write})")
            print(f"    {wt['description']}")
        print()
        print("Runtime matrix:")
        runtimes_seen: list[str] = []
        rows_by_runtime: dict[str, list[dict]] = {}
        for row in data["runtime_matrix"]:
            rt = row["runtime_id"]
            if rt not in rows_by_runtime:
                runtimes_seen.append(rt)
                rows_by_runtime[rt] = []
            rows_by_runtime[rt].append(row)
        for rt in runtimes_seen:
            print(f"  [{rt}]")
            for row in rows_by_runtime[rt]:
                status = row["readiness_status"]
                print(f"    {row['workload_type']}: {status}")
                if row["blockers"]:
                    print(f"      blockers: {', '.join(row['blockers'])}")
                if row["warnings"]:
                    for w in row["warnings"]:
                        print(f"      warning: {w}")
        print()
        print("Blockers:")
        for b in data["blockers"]:
            print(f"  [{b['blocker_id']}] {b['category']} — {b['runtime']} (severity={b['severity']})")
            print(f"    {b['description']}")
        print()
        print("Warnings:")
        for w in data["warnings"]:
            print(f"  - {w}")
        print()
        print("Recommendations:")
        for rec in data["recommendations"]:
            print(f"  - {rec}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['validation_may'])}")
        print(f"  May not: {', '.join(gb['validation_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_execution_authorization_design(args: argparse.Namespace) -> int:
    data = build_execution_authorization_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["execution_authorization_design"]
        print("Execution authorization artifact design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Authorization lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}")
            print(f"     {step['description']}")
        print()
        print("Authorization artifact model (ExecutionAuthorizationArtifact):")
        model = data["artifact_model"]
        print(f"  Fields: {model['field_count']}  Required: {model['required_field_count']}")
        for group in model["field_groups"]:
            fields_in_group = [f for f in model["fields"] if f["group"] == group]
            if fields_in_group:
                print(f"  [{group}]")
                for field in fields_in_group:
                    req = "required" if field["required"] else "optional"
                    print(f"    {field['name']} ({field['type']}, {req}): {field['description']}")
        print(f"  All fields immutable after creation: {model['all_fields_immutable_after_creation']}")
        print()
        print("Authorization states:")
        for state in data["authorization_states"]:
            terminal = "terminal" if state["terminal"] else "non-terminal"
            print(f"  {state['state']} ({terminal}): {state['description']}")
        print()
        print("Authorization requirements (all blocking):")
        for req in data["requirements"]:
            print(f"  {req['requirement']}: {req['description']}")
        print()
        print("Artifact invariants:")
        for inv in data["invariants"]:
            if inv.get("must_have"):
                print(f"  must_have  [{inv['violation_severity']}] {inv['invariant']}: {inv['description']}")
            else:
                print(f"  must_never [{inv['violation_severity']}] {inv['invariant']}: {inv['description']}")
        print()
        print("Lineage model:")
        lm = data["lineage_model"]
        for field in lm["tracked_fields"]:
            print(f"  {field}: {lm[field]}")
        print(f"  lineage_immutable:    {lm['lineage_immutable']}")
        print(f"  lineage_append_only:  {lm['lineage_append_only']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['artifact_may'])}")
        print(f"  May not: {', '.join(gb['artifact_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_read_only_invocation_pilot(args: argparse.Namespace) -> int:
    data = build_read_only_invocation_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        pilot = data["read_only_invocation_pilot"]
        print("Read-only invocation pilot design")
        print(f"Pilot: {pilot['pilot_id']}  Generated: {pilot['generated_at']}")
        print(f"Phase: {pilot['phase']} — {pilot['title']}")
        print()
        print(pilot["summary"])
        print()
        print("Pilot lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}")
            print(f"     {step['description']}")
        print()
        print("Supported runtimes:")
        for rt in data["supported_runtimes"]:
            print(f"  {rt['runtime']} — {rt['pilot_readiness']}")
            print(f"    contract: {rt['read_only_contract']}")
            if rt["blockers"]:
                print(f"    blockers: {', '.join(rt['blockers'])}")
        print()
        print("Invocation plan model (InvocationPlan):")
        model = data["invocation_plan_model"]
        print(f"  Fields: {model['field_count']}  Required: {model['required_field_count']}")
        print(f"  sandbox_mode_constraint: {model['sandbox_mode_constraint']}")
        for field in model["fields"]:
            req = "required" if field["required"] else "optional"
            print(f"    {field['name']} ({field['type']}, {req}): {field['description']}")
        print()
        print("Output capture design:")
        for capture in data["output_capture_design"]:
            req = "required" if capture["required"] else "optional"
            print(f"  {capture['capture_target']} ({req}): {capture['description']}")
        print()
        print("Audit integration:")
        for artifact in data["audit_integration"]:
            print(f"  {artifact['artifact']}")
            print(f"    {artifact['description']}")
        print()
        print("Consensus integration:")
        for path in data["consensus_integration"]:
            escalation = "human escalation" if path["human_escalation"] else "no human escalation"
            print(f"  {path['path']} ({escalation})")
            print(f"    {path['description']}")
        print()
        print("Blockers:")
        for b in data["blockers"]:
            rt = f" — {b['runtime']}" if "runtime" in b else ""
            print(f"  [{b['blocker_id']}] {b['category']}{rt} (severity={b['severity']})")
            print(f"    {b['description']}")
        print()
        print("Recommendations:")
        for rec in data["recommendations"]:
            print(f"  - {rec}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['pilot_may'])}")
        print(f"  May not: {', '.join(gb['pilot_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_execution_result_review_design(args: argparse.Namespace) -> int:
    data = build_execution_result_review_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["execution_result_review_design"]
        print("Execution result review workflow design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Review lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}")
            print(f"     {step['description']}")
        print()
        print("Review categories:")
        for cat in data["review_categories"]:
            blocking = "blocking" if cat["blocking_on_failure"] else "non-blocking"
            print(f"  {cat['category']} ({blocking})")
            print(f"    {cat['description']}")
        print()
        print("Review statuses:")
        for status in data["review_statuses"]:
            terminal = "terminal" if status["terminal"] else "non-terminal"
            print(f"  {status['status']} ({terminal})")
            print(f"    {status['description']}")
        print()
        print("Review record model (ResultReviewRecord):")
        model = data["review_record_model"]
        print(f"  Fields: {model['field_count']}  Required: {model['required_field_count']}")
        for group, names in model["field_groups"].items():
            print(f"  Group '{group}': {', '.join(names)}")
        print()
        print("Review requirements:")
        for req in data["review_requirements"]:
            blocking = "blocking" if req["blocking"] else "non-blocking"
            print(f"  {req['requirement']} ({blocking})")
            print(f"    {req['description']}")
        print()
        print("Escalation rules:")
        for rule in data["escalation_rules"]:
            print(f"  [{rule['rule_id']}] {rule['trigger']} (severity={rule['severity']})")
            print(f"    {rule['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['workflow_may'])}")
        print(f"  May not: {', '.join(gb['workflow_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_pilot_status(args: argparse.Namespace) -> int:
    data = build_invocation_pilot_status()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        status = data["invocation_pilot_status"]
        print("Invocation pilot status")
        print(f"Status: {status['status_id']}  Generated: {status['generated_at']}")
        print(f"Phase: {status['phase']} — {status['title']}")
        print()
        print(status["summary"])
        print()
        print("InvocationCandidate model:")
        cm = data["invocation_candidate_model"]
        print(f"  Fields: {cm['field_count']}  Required: {cm['required_field_count']}")
        print(f"  Sandbox constraint: {cm['sandbox_mode_constraint']}")
        print(f"  Statuses: {', '.join(s['status'] for s in cm['statuses'])}")
        for field in cm["fields"]:
            req = "required" if field["required"] else "optional"
            mut = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {req}, {mut}): {field['description']}")
        print()
        print("InvocationPlan model:")
        pm = data["invocation_plan_model"]
        print(f"  Fields: {pm['field_count']}  Required: {pm['required_field_count']}")
        print(f"  All fields immutable: {pm['all_fields_immutable']}")
        for field in pm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        print("OutputCaptureArtifact model:")
        oc = data["output_capture_artifact_model"]
        print(f"  Fields: {oc['field_count']}  Required: {oc['required_field_count']}")
        for field in oc["fields"]:
            req = "required" if field["required"] else "optional"
            print(f"    {field['name']} ({field['type']}, {req}): {field['description']}")
        print()
        print("Readiness evaluation:")
        re_ = data["readiness_evaluation"]
        for area in re_["areas"]:
            blocking = "blocking" if area["blocking"] else "non-blocking"
            print(f"  {area['area']} ({blocking})")
            print(f"    {area['description']}")
            for check in area["checks"]:
                print(f"    - {check}")
        print()
        print("Governance requirements:")
        for req in data["governance_requirements"]:
            blocking = "blocking" if req["blocking"] else "non-blocking"
            print(f"  {req['requirement']} ({blocking}, checked in {req['checked_in']})")
            print(f"    {req['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['pilot_may'])}")
        print(f"  May not: {', '.join(gb['pilot_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_authorization_expiration_design(args: argparse.Namespace) -> int:
    data = build_authorization_expiration_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["authorization_expiration_design"]
        print("Authorization expiration workflow design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Authorization lifecycle:")
        for step in data["lifecycle"]:
            print(f"  {step['step']}. {step['name']}")
            print(f"     {step['description']}")
        print()
        print("Authorization states:")
        for state in data["authorization_states"]:
            terminal = "terminal" if state["terminal"] else "non-terminal"
            exec_ok = "execution allowed" if state["allows_execution"] else "no execution"
            print(f"  {state['state']} ({terminal}, {exec_ok})")
            print(f"    {state['description']}")
        print()
        print("Expiration triggers:")
        for trigger in data["expiration_triggers"]:
            auto = "auto-fires" if trigger["auto_fires"] else "manual"
            print(f"  {trigger['trigger']} ({auto}, severity={trigger['severity']}, sets_state={trigger['sets_state']})")
            print(f"    {trigger['description']}")
        print()
        print("Renewal requirements:")
        for req in data["renewal_requirements"]:
            blocking = "blocking" if req["blocking"] else "non-blocking"
            print(f"  {req['requirement']} ({blocking})")
            print(f"    {req['description']}")
        print()
        print("Expiration record model (AuthorizationExpirationRecord):")
        model = data["expiration_record_model"]
        print(f"  Fields: {model['field_count']}  Required: {model['required_field_count']}")
        print(f"  Immutable fields: {', '.join(model['immutable_fields'])}")
        print(f"  Mutable fields:   {', '.join(model['mutable_fields'])}")
        print()
        print("Audit integration:")
        for history in data["audit_integration"]:
            print(f"  {history['history_type']} (append_only={history['append_only']}, immutable={history['immutable']})")
            print(f"    {history['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['workflow_may'])}")
        print(f"  May not: {', '.join(gb['workflow_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_multi_agent_invocation_pilot(args: argparse.Namespace) -> int:
    data = build_multi_agent_invocation_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        pilot = data["multi_agent_invocation_pilot"]
        print("Multi-agent invocation pilot")
        print(f"Pilot: {pilot['pilot_id']}  Generated: {pilot['generated_at']}")
        print(f"Phase: {pilot['phase']} — {pilot['title']}")
        print()
        print(pilot["summary"])
        print()
        print("MultiAgentInvocationCandidate model:")
        cm = data["multi_agent_candidate_model"]
        print(f"  Fields: {cm['field_count']}  Required: {cm['required_field_count']}")
        print(f"  Statuses: {', '.join(s['status'] for s in cm['statuses'])}")
        for field in cm["fields"]:
            req = "required" if field["required"] else "optional"
            mut = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {req}, {mut}): {field['description']}")
        print()
        print("MultiAgentInvocationPlan model:")
        pm = data["multi_agent_plan_model"]
        print(f"  Fields: {pm['field_count']}  Required: {pm['required_field_count']}")
        print(f"  All fields immutable: {pm['all_fields_immutable']}")
        for field in pm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        print("MultiAgentOutputCapturePlan model:")
        oc = data["output_capture_plan_model"]
        print(f"  Fields: {oc['field_count']}  Required: {oc['required_field_count']}")
        for field in oc["fields"]:
            req = "required" if field["required"] else "optional"
            print(f"    {field['name']} ({field['type']}, {req}): {field['description']}")
        print()
        print("Invocation strategies:")
        strat = data["invocation_strategies"]
        for s in strat["strategies"]:
            parallel = "parallel" if s["parallel"] else "sequential-mode"
            consensus = ", consensus required" if s["consensus_required"] else ""
            print(f"  {s['strategy']} ({parallel}{consensus})")
            print(f"    {s['description']}")
        print()
        print("Readiness evaluation:")
        re_ = data["readiness_evaluation"]
        for area in re_["areas"]:
            blocking = "blocking" if area["blocking"] else "non-blocking"
            print(f"  {area['area']} ({blocking})")
            print(f"    {area['description']}")
            for check in area["checks"]:
                print(f"    - {check}")
        print()
        print("Governance requirements:")
        for req in data["governance_requirements"]:
            blocking = "blocking" if req["blocking"] else "non-blocking"
            print(f"  {req['requirement']} ({blocking}, checked in {req['checked_in']})")
            print(f"    {req['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['pilot_may'])}")
        print(f"  May not: {', '.join(gb['pilot_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_execution_quality_design(args: argparse.Namespace) -> int:
    data = build_execution_quality_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["execution_quality_design"]
        print("Execution result quality framework")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Quality dimensions:")
        qdm = data["quality_dimensions"]
        for dim in qdm["dimensions"]:
            blocking = "blocking" if dim["blocking"] else "non-blocking"
            escalation = ", escalation on failure" if dim["escalation_on_failure"] else ""
            print(f"  {dim['name']} ({blocking}{escalation})")
            print(f"    {dim['description']}")
        print()
        print("Quality statuses:")
        qsm = data["quality_statuses"]
        for status in qsm["statuses"]:
            terminal = "terminal" if status["terminal"] else "non-terminal"
            review = "human review required" if status["requires_human_review"] else "human review advisory"
            blocks = ", blocks consensus" if status["blocks_consensus"] else ""
            print(f"  {status['status']} ({terminal}, {review}{blocks})")
            print(f"    {status['description']}")
        print()
        print("ResultQualityRecord model:")
        rqr = data["result_quality_record"]
        print(f"  Fields: {rqr['field_count']}  Required: {rqr['required_field_count']}")
        print(f"  Immutable: {', '.join(rqr['immutable_fields'])}")
        print(f"  Mutable:   {', '.join(rqr['mutable_fields'])}")
        for field in rqr["fields"]:
            req = "required" if field["required"] else "optional"
            mut = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {req}, {mut}): {field['description']}")
        print()
        print("Evaluation model:")
        em = data["evaluation_model"]
        for area in em["areas"]:
            blocking = "blocking" if area["blocking"] else "non-blocking"
            print(f"  {area['area']} ({blocking})")
            print(f"    {area['description']}")
            for check in area["checks"]:
                print(f"    - {check}")
        print()
        print("Evaluation rules:")
        for rule in em["rules"]:
            print(f"  {rule['rule_id']} {rule['rule']} (priority={rule['priority']}, sets_status={rule['sets_status']})")
            print(f"    {rule['description']}")
        print()
        print("Governance requirements:")
        for req in data["governance_requirements"]:
            blocking = "blocking" if req["blocking"] else "non-blocking"
            print(f"  {req['requirement']} ({blocking}, checked in {req['checked_in']})")
            print(f"    {req['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['framework_may'])}")
        print(f"  May not: {', '.join(gb['framework_may_not'])}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_read_only_invocation_execution_pilot(args: argparse.Namespace) -> int:
    data = build_read_only_invocation_execution_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        pilot = data["read_only_invocation_execution_pilot"]
        print("Read-only invocation execution pilot")
        print(f"Design: {pilot['pilot_design_id']}  Generated: {pilot['generated_at']}")
        print(f"Phase: {pilot['phase']} — {pilot['title']}")
        print()
        print(pilot["summary"])
        print()
        print("Execution pilot lifecycle:")
        for step in data["execution_pilot_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("Preflight gates:")
        pg = data["preflight_gates"]
        print(f"  Gate count: {pg['gate_count']}  All blocking: {pg['all_gates_blocking']}")
        for gate in pg["gates"]:
            blocking = "blocking" if gate["blocking"] else "non-blocking"
            print(f"  {gate['gate_id']} {gate['gate']} ({blocking})")
            print(f"    {gate['description']}")
            for check in gate["checks"]:
                print(f"    - {check}")
        print()
        print("Pilot result model (PilotResult):")
        rm = data["pilot_result_model"]
        print(f"  Fields: {rm['field_count']}  Required: {rm['required_field_count']}")
        print(f"  All fields immutable: {rm['all_fields_immutable']}")
        print(f"  execution_allowed always False: {rm['execution_allowed_always_false']}")
        for field in rm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        print("Readiness statuses:")
        rs = data["readiness_statuses"]
        for status in rs["statuses"]:
            exec_ok = "execution allowed" if status["execution_allowed"] else "no execution"
            auth = "human auth required" if status["human_authorization_required"] else ""
            print(f"  {status['status']} ({exec_ok}, {auth})")
            print(f"    {status['description']}")
        print()
        print("Governance requirements:")
        for req in data["governance_requirements"]:
            blocking = "blocking" if req["blocking"] else "non-blocking"
            print(f"  {req['requirement']} ({blocking}, checked in {req['checked_in']})")
            print(f"    {req['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['pilot_may'])}")
        print(f"  May not: {', '.join(gb['pilot_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_invocation_design(args: argparse.Namespace) -> int:
    data = build_write_invocation_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["write_invocation_design"]
        print("Governed write invocation design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Write invocation lifecycle:")
        for step in data["write_invocation_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("Write authorization requirements:")
        war = data["write_authorization_requirements"]
        print(f"  Requirement count: {war['requirement_count']}  All blocking: {war['all_requirements_blocking']}")
        for req in war["requirements"]:
            blocking = "blocking" if req["blocking"] else "non-blocking"
            print(f"  {req['requirement']} ({blocking})")
            print(f"    {req['description']}")
        print()
        print("File scope model (FileScopeArtifact):")
        fsm = data["file_scope_model"]
        print(f"  Fields: {fsm['field_count']}  All required: {fsm['all_fields_required']}")
        for field in fsm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        print("Write invocation candidate model (WriteInvocationCandidate):")
        wcm = data["write_candidate_model"]
        print(f"  Fields: {wcm['field_count']}  Required: {wcm['required_field_count']}")
        print(f"  writable_allowed always False: {wcm['writable_allowed_always_false']}")
        for field in wcm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        print("Write candidate statuses:")
        wcs = data["write_candidate_statuses"]
        for status in wcs["statuses"]:
            writable = "writable allowed" if status["writable_allowed"] else "no write"
            terminal = "terminal" if status["terminal"] else "non-terminal"
            print(f"  {status['status']} ({writable}, {terminal})")
            print(f"    {status['description']}")
        print()
        print("Preflight gates:")
        pg = data["preflight_gates"]
        print(f"  Gate count: {pg['gate_count']}  All blocking: {pg['all_gates_blocking']}")
        for gate in pg["gates"]:
            blocking = "blocking" if gate["blocking"] else "non-blocking"
            print(f"  {gate['gate_id']} {gate['gate']} ({blocking})")
            print(f"    {gate['description']}")
            for check in gate["checks"]:
                print(f"    - {check}")
        print()
        print("Safety constraints:")
        for constraint in data["safety_constraints"]:
            print(f"  {constraint['constraint']}")
            print(f"    {constraint['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['design_may'])}")
        print(f"  May not: {', '.join(gb['design_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_preflight_dry_run(args: argparse.Namespace) -> int:
    data = build_write_preflight_dry_run()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["write_preflight_dry_run"]
        print("Write invocation preflight dry-run")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Dry-run lifecycle:")
        for step in data["dry_run_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("Preflight gates:")
        pg = data["preflight_gates"]
        print(f"  Gate count: {pg['gate_count']}  All blocking: {pg['all_gates_blocking']}")
        print(f"  Human approval gate simulated result: {pg['human_approval_gate_simulated_result']}")
        for gate in pg["gates"]:
            blocking = "blocking" if gate["blocking"] else "non-blocking"
            print(f"  {gate['gate_id']} {gate['gate']} ({blocking}, simulated: {gate['simulated_result']})")
            print(f"    {gate['description']}")
            for check in gate["checks"]:
                print(f"    - {check}")
        print()
        print("Dry-run result model (WritePreflightDryRunResult):")
        rm = data["dry_run_result_model"]
        print(f"  Fields: {rm['field_count']}  Required: {rm['required_field_count']}")
        print(f"  write_execution_allowed always False: {rm['write_execution_allowed_always_false']}")
        for field in rm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        print("File scope simulation (FileScopeSimulation):")
        fsm = data["file_scope_simulation"]
        print(f"  Fields: {fsm['field_count']}  All required: {fsm['all_fields_required']}")
        for field in fsm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['dry_run_may'])}")
        print(f"  May not: {', '.join(gb['dry_run_may_not'])}")
        print(f"  Write execution allowed: {gb['write_execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_candidate_design(args: argparse.Namespace) -> int:
    data = build_write_candidate_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["write_candidate_design"]
        print("Governed write candidate artifact design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("GovernedWriteCandidate lifecycle:")
        for step in data["write_candidate_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("GovernedWriteCandidate model:")
        wcm = data["write_candidate_model"]
        print(f"  Fields: {wcm['field_count']}  Required: {wcm['required_field_count']}")
        print(f"  Immutable: {wcm['immutable_field_count']}")
        print(f"  execution_allowed always False: {wcm['execution_allowed_always_false']}")
        for field in wcm["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        print("Candidate statuses:")
        cs = data["candidate_statuses"]
        print(f"  Status count: {cs['status_count']}")
        print(f"  All execution_allowed False: {cs['all_statuses_execution_allowed_false']}")
        print(f"  Terminal statuses: {', '.join(cs['terminal_statuses'])}")
        for status in cs["statuses"]:
            exec_ok = "execution allowed" if status["execution_allowed"] else "no execution"
            terminal = "terminal" if status["terminal"] else "non-terminal"
            print(f"  {status['status']} ({exec_ok}, {terminal})")
            print(f"    {status['description']}")
        print()
        print("File scope requirements:")
        fsr = data["file_scope_requirements"]
        print(f"  Fields: {fsr['field_count']}  All required: {fsr['all_fields_required']}")
        for field in fsr["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        print("Rollback plan requirements:")
        rr = data["rollback_requirements"]
        print(f"  Fields: {rr['field_count']}  All required: {rr['all_fields_required']}")
        for field in rr["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        print("Audit plan requirements:")
        ar = data["audit_requirements"]
        print(f"  Fields: {ar['field_count']}  All required: {ar['all_fields_required']}")
        for field in ar["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        print("Artifact invariants:")
        inv = data["artifact_invariants"]
        print(f"  Must always have: {', '.join(inv['must_always_have'])}")
        print(f"  Must never allow: {', '.join(inv['must_never_allow'])}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['artifact_may'])}")
        print(f"  May not: {', '.join(gb['artifact_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_invocation_pilot(args: argparse.Namespace) -> int:
    data = build_write_invocation_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["write_invocation_pilot"]
        print("Controlled write invocation pilot")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Pilot lifecycle:")
        for step in data["pilot_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("ControlledWritePlan model:")
        wpm = data["write_plan_model"]
        print(f"  Fields: {wpm['field_count']}  Required: {wpm['required_field_count']}")
        print(f"  All fields immutable: {wpm['all_fields_immutable']}")
        print(f"  execution_allowed always False: {wpm['execution_allowed_always_false']}")
        for field in wpm["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        print("Runtime writable contracts:")
        rc = data["runtime_writable_contracts"]
        print(f"  Contract count: {rc['contract_count']}  All available: {rc['all_contracts_available']}")
        for contract in rc["contracts"]:
            available = "available" if contract["contract_available"] else "unavailable"
            print(f"  {contract['runtime']} ({contract['writable_mode']}, {available})")
            print(f"    Command: {contract['command_template']}")
            print(f"    Scope enforcement: {contract['scope_enforcement']}")
        print()
        print("Write safety gates:")
        sg = data["safety_gates"]
        print(f"  Gate count: {sg['gate_count']}  All blocking: {sg['all_gates_blocking']}")
        print(f"  Human approval always required: {sg['human_approval_gate_always_required']}")
        for gate in sg["gates"]:
            blocking = "blocking" if gate["blocking"] else "non-blocking"
            print(f"  {gate['gate_id']} {gate['gate']} ({blocking})")
            print(f"    {gate['description']}")
            for check in gate["checks"]:
                print(f"    - {check}")
        print()
        print("Pilot result model (ControlledWritePilotResult):")
        rm = data["pilot_result_model"]
        print(f"  Fields: {rm['field_count']}  Required: {rm['required_field_count']}")
        print(f"  All fields immutable: {rm['all_fields_immutable']}")
        print(f"  write_execution_allowed always False: {rm['write_execution_allowed_always_false']}")
        print(f"  human_review_required always True: {rm['human_review_required_always_true']}")
        for field in rm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['pilot_may'])}")
        print(f"  May not: {', '.join(gb['pilot_may_not'])}")
        print(f"  Write execution allowed: {gb['write_execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_result_review_design(args: argparse.Namespace) -> int:
    data = build_write_result_review_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["write_result_review_design"]
        print("Write result review workflow design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Review lifecycle:")
        for step in data["review_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("Review categories:")
        for cat in data["review_categories"]:
            blocking = "blocking" if cat["blocking"] else "non-blocking"
            print(f"  {cat['category']} ({blocking})")
            print(f"    {cat['description']}")
        print()
        print("WriteReviewRecord model:")
        m = data["write_review_record_model"]
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}  Groups: {', '.join(m['groups'])}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    [{field['group']}] {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        print("Review statuses:")
        rs = data["review_statuses"]
        print(f"  Status count: {rs['status_count']}")
        print(f"  Terminal: {', '.join(rs['terminal_statuses'])}")
        print(f"  Requires rollback: {', '.join(rs['rollback_statuses'])}")
        print(f"  Escalation: {', '.join(rs['escalation_statuses'])}")
        for status in rs["statuses"]:
            terminal = "terminal" if status["terminal"] else "non-terminal"
            print(f"  {status['status']} ({terminal})")
            print(f"    {status['description']}")
        print()
        print("Scope compliance rules:")
        sc = data["scope_compliance_rules"]
        print(f"  Rule count: {sc['rule_count']}  All violations trigger escalation: {sc['all_violations_trigger_escalation']}")
        for rule in sc["rules"]:
            print(f"  {rule['rule']} → {rule['violation_triggers']}")
            print(f"    {rule['description']}")
        print()
        print("Rollback validation rules:")
        rv = data["rollback_validation_rules"]
        print(f"  Rule count: {rv['rule_count']}  All violations trigger escalation: {rv['all_violations_trigger_escalation']}")
        for rule in rv["rules"]:
            print(f"  {rule['rule']} → {rule['violation_triggers']}")
            print(f"    {rule['description']}")
        print()
        print("Escalation rules:")
        er = data["escalation_rules"]
        print(f"  Rule count: {er['rule_count']}  All escalate to: {er['all_escalate_to']}")
        for rule in er["rules"]:
            print(f"  {rule['condition']} → {rule['escalation_status']}")
            print(f"    {rule['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['workflow_may'])}")
        print(f"  May not: {', '.join(gb['workflow_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_execution_readiness(args: argparse.Namespace) -> int:
    data = build_write_execution_readiness()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        r = data["write_execution_readiness"]
        print("Write execution readiness assessment")
        print(f"Assessment: {r['readiness_id']}  Generated: {r['generated_at']}")
        print(f"Phase: {r['phase']} — {r['title']}")
        print()
        print(r["summary"])
        print()
        print("Assessment results:")
        print(f"  Overall status:              {r['overall_status']}")
        print(f"  Write execution recommended: {'yes' if r['write_execution_recommended'] else 'no'}")
        print(f"  Human review required:       {'yes' if r['human_review_required'] else 'no'}")
        print(f"  Areas assessed:              {r['area_count']}")
        print(f"  Not ready:                   {r['not_ready_area_count']}")
        print(f"  Partially ready:             {r['partially_ready_area_count']}")
        print(f"  Ready:                       {r['ready_area_count']}")
        print(f"  Active blockers:             {r['active_blocker_count']}")
        print()
        print(f"Readiness areas ({len(data['readiness_areas'])}):")
        for area in data["readiness_areas"]:
            critical = "critical" if area["critical"] else "non-critical"
            print(f"  [{area['status']}] {area['area']} ({critical})")
            print(f"    {area['description']}")
            print(f"    Rationale: {area['rationale']}")
            print(f"    Governance source: {area['governance_source']}")
        print()
        print("Readiness result model:")
        m = data["readiness_result_model"]
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}  Groups: {', '.join(m['groups'])}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    [{field['group']}] {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        bl = data["blockers"]
        print(f"Blockers ({bl['active_blocker_count']} active of {bl['blocker_count']}):")
        for b in bl["blockers"]:
            active = "active" if b["active"] else "inactive"
            print(f"  [{active}] {b['blocker']} (severity: {b['severity']})")
            print(f"    {b['description']}")
        print()
        ri = data["risks"]
        print(f"Risks ({ri['risk_count']}):")
        for risk in ri["risks"]:
            print(f"  {risk['risk']} (severity: {risk['severity']})")
            print(f"    {risk['description']}")
            print(f"    Mitigated by: {risk['mitigated_by']}")
        print()
        rec = data["recommendations"]
        print("Recommendations:")
        print(f"  Readiness: {rec['readiness_recommendation']}")
        phases = ", ".join(rec["required_follow_up_phases"])
        print(f"  Required follow-up phases: {phases}")
        print(f"  Authorization: {rec['execution_authorization_recommendation']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['workflow_may'])}")
        print(f"  May not: {', '.join(gb['workflow_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_rollback_dry_run(args: argparse.Namespace) -> int:
    data = build_write_rollback_dry_run()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        r = data["write_rollback_dry_run"]
        print("Write rollback dry-run simulation")
        print(f"Dry-run: {r['dry_run_id']}  Generated: {r['generated_at']}")
        print(f"Phase: {r['phase']} — {r['title']}")
        print()
        print(r["summary"])
        print()
        print("Dry-run results:")
        print(f"  Dry-run result:              {r['dry_run_result']}")
        print(f"  Rollback execution allowed:  {'yes' if r['rollback_execution_allowed'] else 'no'}")
        print(f"  Human review required:       {'yes' if r['human_review_required'] else 'no'}")
        print(f"  Gates met:                   {r['gates_met']} of {r['gate_count']}")
        print(f"  Allowed modes:               {r['allowed_mode_count']}")
        print(f"  Forbidden modes:             {r['forbidden_mode_count']}")
        print()
        print(f"Dry-run lifecycle ({len(data['dry_run_lifecycle'])} steps):")
        for step in data["dry_run_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("RollbackDryRunResult model:")
        m = data["rollback_dry_run_result_model"]
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}  Groups: {', '.join(m['groups'])}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    [{field['group']}] {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        rm = data["rollback_modes"]
        print(f"Rollback modes ({rm['allowed_mode_count']} allowed, {rm['forbidden_mode_count']} forbidden):")
        for mode in rm["allowed_modes"]:
            print(f"  [allowed]  {mode['mode']}: {mode['description']}")
        for mode in rm["forbidden_modes"]:
            print(f"  [FORBIDDEN] {mode['mode']}: {mode['description']}")
            print(f"    Reason: {mode['reason']}")
        print()
        gm = data["dry_run_gates"]
        print(f"Governance gates ({gm['gates_met']} met, {gm['gates_not_met']} not met):")
        for gate in gm["gates"]:
            blocker = "blocker" if gate["blocker_if_not_met"] else "warning"
            print(f"  [{gate['status']}] {gate['gate']} ({blocker} if not met)")
            print(f"    {gate['description']}")
            print(f"    Rationale: {gate['rationale']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['workflow_may'])}")
        print(f"  May not:               {', '.join(gb['workflow_may_not'])}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  Rollback allowed:      {gb['rollback_execution_allowed']}")
        print(f"  git reset forbidden:   {gb['git_reset_forbidden']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_live_readonly_readiness(args: argparse.Namespace) -> int:
    data = build_live_readonly_readiness()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        r = data["live_readonly_readiness"]
        print("Live read-only execution readiness assessment")
        print(f"Assessment: {r['readiness_id']}  Generated: {r['generated_at']}")
        print(f"Phase: {r['phase']} — {r['title']}")
        print()
        print(r["summary"])
        print()
        print("Assessment results:")
        print(f"  Overall status:             {r['overall_status']}")
        print(f"  Live execution recommended: {'yes' if r['live_execution_recommended'] else 'no'}")
        print(f"  Human review required:      {'yes' if r['human_review_required'] else 'no'}")
        print(f"  Areas assessed:             {r['area_count']}")
        print(f"  Not ready:                  {r['not_ready_area_count']}")
        print(f"  Partially ready:            {r['partially_ready_area_count']}")
        print(f"  Ready:                      {r['ready_area_count']}")
        print(f"  Active blockers:            {r['active_blocker_count']}")
        print(f"  Runtime count:              {r['runtime_count']}")
        print()
        print(f"Readiness areas ({len(data['readiness_areas'])}):")
        for area in data["readiness_areas"]:
            critical = "critical" if area["critical"] else "non-critical"
            print(f"  [{area['status']}] {area['area']} ({critical})")
            print(f"    {area['description']}")
            print(f"    Rationale: {area['rationale']}")
            print(f"    Governance source: {area['governance_source']}")
        print()
        rt = data["runtime_results"]
        print(f"Runtime assessment ({rt['runtime_count']} runtimes):")
        for runtime in rt["runtimes"]:
            print(f"  [{runtime['status']}] {runtime['runtime']} ({runtime['adapter_type']})")
            print(f"    Rationale: {runtime['rationale']}")
            print(f"    Capabilities verified: {'yes' if runtime['capabilities_verified'] else 'no'}")
            print(f"    Live execution tested: {'yes' if runtime['live_execution_tested'] else 'no'}")
        print()
        print("LiveReadOnlyReadinessResult model:")
        m = data["readiness_result_model"]
        print(f"  Model: {m['model_name']}")
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}  Groups: {', '.join(m['groups'])}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(
                f"    [{field['group']}] {field['name']} ({field['type']}, {imm}):"
                f" {field['description']}"
            )
        print()
        bl = data["blockers"]
        print(f"Blockers ({bl['active_blocker_count']} active of {bl['blocker_count']}):")
        for b in bl["blockers"]:
            active = "active" if b["active"] else "inactive"
            print(f"  [{active}] {b['blocker']} (severity: {b['severity']})")
            print(f"    {b['description']}")
        print()
        warnings = data["warnings"]
        print(f"Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()
        rec = data["recommendations"]
        print("Recommendations:")
        print(f"  Readiness: {rec['readiness_recommendation']}")
        phases = ", ".join(rec["required_follow_up_phases"])
        print(f"  Required follow-up phases: {phases}")
        print(f"  Authorization: {rec['execution_authorization_recommendation']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['workflow_may'])}")
        print(f"  May not: {', '.join(gb['workflow_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_live_write_readiness(args: argparse.Namespace) -> int:
    data = build_live_write_readiness()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        r = data["live_write_readiness"]
        print("Live write execution readiness assessment")
        print(f"Assessment: {r['readiness_id']}  Generated: {r['generated_at']}")
        print(f"Phase: {r['phase']} — {r['title']}")
        print()
        print(r["summary"])
        print()
        print("Assessment results:")
        print(f"  Overall status:           {r['overall_status']}")
        print(f"  Live write recommended:   {'yes' if r['live_write_recommended'] else 'no'}")
        print(f"  Human review required:    {'yes' if r['human_review_required'] else 'no'}")
        print(f"  Areas assessed:           {r['area_count']}")
        print(f"  Not ready:                {r['not_ready_area_count']}")
        print(f"  Partially ready:          {r['partially_ready_area_count']}")
        print(f"  Ready:                    {r['ready_area_count']}")
        print(f"  Active blockers:          {r['active_blocker_count']}")
        print(f"  Risk count:               {r['risk_count']}")
        print(f"  Runtime count:            {r['runtime_count']}")
        print()
        print(f"Readiness areas ({len(data['readiness_areas'])}):")
        for area in data["readiness_areas"]:
            critical = "critical" if area["critical"] else "non-critical"
            print(f"  [{area['status']}] {area['area']} ({critical})")
            print(f"    {area['description']}")
            print(f"    Rationale: {area['rationale']}")
            print(f"    Governance source: {area['governance_source']}")
        print()
        rt = data["runtime_results"]
        print(f"Runtime writable assessment ({rt['runtime_count']} runtimes):")
        for runtime in rt["runtimes"]:
            print(f"  [{runtime['status']}] {runtime['runtime']} ({runtime['adapter_type']})")
            print(f"    Writable contract: {runtime['writable_contract']}")
            print(f"    Rationale: {runtime['rationale']}")
            print(f"    Contract verified: {'yes' if runtime['contract_verified'] else 'no'}")
            print(f"    Live write tested: {'yes' if runtime['live_write_tested'] else 'no'}")
        print()
        print("LiveWriteReadinessResult model:")
        m = data["readiness_result_model"]
        print(f"  Model: {m['model_name']}")
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}  Groups: {', '.join(m['groups'])}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(
                f"    [{field['group']}] {field['name']} ({field['type']}, {imm}):"
                f" {field['description']}"
            )
        print()
        bl = data["blockers"]
        print(f"Blockers ({bl['active_blocker_count']} active of {bl['blocker_count']}):")
        for b in bl["blockers"]:
            active = "active" if b["active"] else "inactive"
            print(f"  [{active}] {b['blocker']} (severity: {b['severity']})")
            print(f"    {b['description']}")
        print()
        ri = data["risks"]
        print(f"Risks ({ri['risk_count']}):")
        for risk in ri["risks"]:
            print(f"  {risk['risk']} (severity: {risk['severity']})")
            print(f"    {risk['description']}")
            print(f"    Mitigated by: {risk['mitigated_by']}")
        print()
        rec = data["recommendations"]
        print("Recommendations:")
        print(f"  Readiness: {rec['readiness_recommendation']}")
        phases = ", ".join(rec["required_follow_up_phases"])
        print(f"  Required follow-up phases: {phases}")
        print(f"  Authorization: {rec['execution_authorization_recommendation']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['workflow_may'])}")
        print(f"  May not: {', '.join(gb['workflow_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  File modification allowed: {gb['file_modification_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_live_readonly_pilot(args: argparse.Namespace) -> int:
    data = build_live_readonly_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        pilot = data["live_readonly_pilot"]
        print("Governed live read-only pilot")
        print(f"Pilot: {pilot['pilot_id']}  Generated: {pilot['generated_at']}")
        print(f"Phase: {pilot['phase']} — {pilot['title']}")
        print()
        print(pilot["summary"])
        print()
        print("Pilot status:")
        print(f"  Readiness status:      {pilot['readiness_status']}")
        print(f"  Execution allowed:     {'yes' if pilot['execution_allowed'] else 'no'}")
        print(f"  Human review required: {'yes' if pilot['human_review_required'] else 'no'}")
        print(f"  Lifecycle steps:       {pilot['lifecycle_step_count']}")
        print(f"  Gates met:             {pilot['gates_met']} of {pilot['gate_count']}")
        print(f"  Runtime count:         {pilot['runtime_count']}")
        print()
        print(f"Pilot lifecycle ({len(data['pilot_lifecycle'])} steps):")
        for step in data["pilot_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("PilotCandidate model:")
        m = data["pilot_candidate_model"]
        print(f"  Model: {m['model_name']}")
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}")
        print(f"  execution_allowed always False: {m['execution_allowed_always_false']}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        pg = data["pilot_gates"]
        print(f"Pilot gates ({pg['gates_met']} met, {pg['gates_not_met']} not met):")
        print(
            f"  All required: {pg['all_gates_required']}"
            f"  All blocking: {pg['all_gates_blocking']}"
        )
        for gate in pg["gates"]:
            print(f"  [{gate['status']}] {gate['gate_id']} {gate['gate']}")
            print(f"    {gate['description']}")
        print()
        rt = data["runtime_assessment"]
        print(f"Runtime assessment ({rt['runtime_count']} runtimes):")
        for runtime in rt["runtimes"]:
            print(f"  [{runtime['status']}] {runtime['runtime']} ({runtime['adapter_type']})")
            print(f"    Rationale: {runtime['rationale']}")
            print(
                f"    Read-only validated: {'yes' if runtime['read_only_validated'] else 'no'}"
            )
        print()
        print("PilotResult model:")
        rm = data["pilot_result_model"]
        print(f"  Model: {rm['model_name']}")
        print(f"  Fields: {rm['field_count']}  Required: {rm['required_field_count']}")
        print(f"  All fields immutable: {rm['all_fields_immutable']}")
        print(f"  execution_allowed always False: {rm['execution_allowed_always_false']}")
        print(f"  human_review_required always True: {rm['human_review_required_always_true']}")
        for field in rm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['pilot_may'])}")
        print(f"  May not: {', '.join(gb['pilot_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_rollback_execution_pilot(args: argparse.Namespace) -> int:
    data = build_rollback_execution_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        pilot = data["rollback_execution_pilot"]
        print("Governed rollback execution pilot")
        print(f"Pilot: {pilot['pilot_id']}  Generated: {pilot['generated_at']}")
        print(f"Phase: {pilot['phase']} — {pilot['title']}")
        print()
        print(pilot["summary"])
        print()
        print("Pilot status:")
        print(f"  Readiness status:      {pilot['readiness_status']}")
        print(f"  Execution allowed:     {'yes' if pilot['execution_allowed'] else 'no'}")
        print(f"  Human review required: {'yes' if pilot['human_review_required'] else 'no'}")
        print(f"  git_reset forbidden:   {'yes' if pilot['git_reset_forbidden'] else 'no'}")
        print(f"  Lifecycle steps:       {pilot['lifecycle_step_count']}")
        print(f"  Gates met:             {pilot['gates_met']} of {pilot['gate_count']}")
        print()
        print(f"Pilot lifecycle ({len(data['pilot_lifecycle'])} steps):")
        for step in data["pilot_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("RollbackCandidate model:")
        m = data["rollback_candidate_model"]
        print(f"  Model: {m['model_name']}")
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}")
        print(f"  execution_allowed always False: {m['execution_allowed_always_false']}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        rm = data["rollback_modes"]
        print(
            f"Rollback modes ({rm['allowed_mode_count']} allowed,"
            f" {rm['forbidden_mode_count']} forbidden):"
        )
        print(f"  git_reset forbidden: {rm['git_reset_forbidden']}")
        for mode in rm["allowed_modes"]:
            print(f"  [allowed]   {mode['mode']}: {mode['description']}")
        for mode in rm["forbidden_modes"]:
            print(f"  [FORBIDDEN] {mode['mode']}: {mode['reason']}")
        print()
        pg = data["pilot_gates"]
        print(f"Pilot gates ({pg['gates_met']} met, {pg['gates_not_met']} not met):")
        print(
            f"  All required: {pg['all_gates_required']}"
            f"  All blocking: {pg['all_gates_blocking']}"
        )
        for gate in pg["gates"]:
            print(f"  [{gate['status']}] {gate['gate_id']} {gate['gate']}")
            print(f"    {gate['description']}")
        print()
        print("PilotResult model:")
        pr = data["pilot_result_model"]
        print(f"  Model: {pr['model_name']}")
        print(f"  Fields: {pr['field_count']}  Required: {pr['required_field_count']}")
        print(f"  All fields immutable: {pr['all_fields_immutable']}")
        print(f"  execution_allowed always False: {pr['execution_allowed_always_false']}")
        print(f"  human_review_required always True: {pr['human_review_required_always_true']}")
        for field in pr["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['pilot_may'])}")
        print(f"  May not:               {', '.join(gb['pilot_may_not'])}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  git_reset forbidden:   {gb['git_reset_forbidden']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_live_write_pilot(args: argparse.Namespace) -> int:
    data = build_live_write_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        pilot = data["live_write_pilot"]
        print("Governed live write pilot")
        print(f"Pilot: {pilot['pilot_id']}  Generated: {pilot['generated_at']}")
        print(f"Phase: {pilot['phase']} — {pilot['title']}")
        print()
        print(pilot["summary"])
        print()
        print("Pilot status:")
        print(f"  Readiness status:      {pilot['readiness_status']}")
        print(f"  Execution allowed:     {'yes' if pilot['execution_allowed'] else 'no'}")
        print(f"  Human review required: {'yes' if pilot['human_review_required'] else 'no'}")
        print(f"  git_reset forbidden:   {'yes' if pilot['git_reset_forbidden'] else 'no'}")
        print(f"  Lifecycle steps:       {pilot['lifecycle_step_count']}")
        print(f"  Gates met:             {pilot['gates_met']} of {pilot['gate_count']}")
        print(f"  Runtime count:         {pilot['runtime_count']}")
        print()
        print(f"Pilot lifecycle ({len(data['pilot_lifecycle'])} steps):")
        for step in data["pilot_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("LiveWritePilotCandidate model:")
        m = data["pilot_candidate_model"]
        print(f"  Model: {m['model_name']}")
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}")
        print(f"  execution_allowed always False: {m['execution_allowed_always_false']}")
        print(f"  human_review_required always True: {m['human_review_required_always_true']}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        pg = data["pilot_gates"]
        print(f"Pilot gates ({pg['gates_met']} met, {pg['gates_not_met']} not met):")
        print(
            f"  All required: {pg['all_gates_required']}"
            f"  All blocking: {pg['all_gates_blocking']}"
        )
        for gate in pg["gates"]:
            print(f"  [{gate['status']}] {gate['gate_id']} {gate['gate']}")
            print(f"    {gate['description']}")
        print()
        rt = data["runtime_assessment"]
        print(f"Runtime writable assessment ({rt['runtime_count']} runtimes):")
        for runtime in rt["runtimes"]:
            print(f"  [{runtime['status']}] {runtime['runtime']} ({runtime['adapter_type']})")
            print(f"    Rationale: {runtime['rationale']}")
            print(
                f"    Write validated: {'yes' if runtime['write_validated'] else 'no'}"
            )
        print()
        print("PilotResult model:")
        rm = data["pilot_result_model"]
        print(f"  Model: {rm['model_name']}")
        print(f"  Fields: {rm['field_count']}  Required: {rm['required_field_count']}")
        print(f"  All fields immutable: {rm['all_fields_immutable']}")
        print(f"  execution_allowed always False: {rm['execution_allowed_always_false']}")
        print(f"  human_review_required always True: {rm['human_review_required_always_true']}")
        for field in rm["fields"]:
            print(f"    {field['name']} ({field['type']}): {field['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['pilot_may'])}")
        print(f"  May not:               {', '.join(gb['pilot_may_not'])}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  git_reset forbidden:   {gb['git_reset_forbidden']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_runtime_contracts(args: argparse.Namespace) -> int:
    data = build_runtime_contracts()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        rc = data["runtime_contracts"]
        print("Runtime contract verification")
        print(f"Verification: {rc['verification_id']}  Generated: {rc['generated_at']}")
        print(f"Phase: {rc['phase']} — {rc['title']}")
        print()
        print(rc["summary"])
        print()
        print("Verification summary:")
        print(f"  Runtime count:               {rc['runtime_count']}")
        print(f"  Verification areas:          {rc['verification_area_count']}")
        print(f"  Runtimes verified:           {rc['verified_count']}")
        print(f"  Runtimes partially verified: {rc['partially_verified_count']}")
        print(f"  Runtimes unverified:         {rc['unverified_count']}")
        print(f"  Areas verified:              {rc['verified_area_count']}")
        print(f"  Areas partially verified:    {rc['partially_verified_area_count']}")
        print(f"  Areas unverified:            {rc['unverified_area_count']}")
        print(f"  Execution allowed:           {'yes' if rc['execution_allowed'] else 'no'}")
        print()
        print("RuntimeContract model:")
        m = data["runtime_contract_model"]
        print(f"  Model: {m['model_name']}")
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        vs = data["verification_statuses"]
        print(f"Verification statuses ({vs['status_count']}):")
        for s in vs["statuses"]:
            print(f"  {s['status']}: {s['description']}")
        print()
        print(f"Verification areas ({len(data['verification_areas'])}):")
        for area in data["verification_areas"]:
            print(f"  {area['area']}: {area['description']}")
        print()
        print(f"Runtime contracts ({len(data['contracts'])} runtimes):")
        for contract in data["contracts"]:
            print(
                f"  [{contract['verification_status']}] {contract['runtime_id']}"
                f" ({contract['runtime_type']}, {contract['invocation_method']})"
            )
            print(f"    Sandbox mode: {contract['sandbox_mode']}")
            print(
                f"    Writable supported: {'yes' if contract['writable_supported'] else 'no'}"
                f"  Readonly supported: {'yes' if contract['readonly_supported'] else 'no'}"
            )
            for ar in contract["area_results"]:
                print(f"    [{ar['status']}] {ar['area']}: {ar['rationale']}")
        print()
        print("Verification records:")
        for rec in data["verification_records"]:
            print(f"  {rec['verification_id']} [{rec['verification_status']}]")
            print(f"    Verified:  {rec['verified_capabilities'] or 'none'}")
            print(f"    Missing:   {rec['missing_capabilities']}")
            print(f"    Blockers:  {rec['blockers']}")
            print(f"    Warnings:  {rec['warnings'] or 'none'}")
        print()
        print("RuntimeContractVerificationRecord model:")
        rm = data["verification_record_model"]
        print(f"  Model: {rm['model_name']}")
        print(f"  Fields: {rm['field_count']}  Required: {rm['required_field_count']}")
        print(f"  Immutable: {rm['immutable_field_count']}")
        for field in rm["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['verification_may'])}")
        print(f"  May not:           {', '.join(gb['verification_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print()
        print(data["advisory"])
    return 0


def run_execution_governance_audit(args: argparse.Namespace) -> int:
    data = build_governance_audit()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ga = data["governance_audit"]
        print("Live execution governance audit")
        print(f"Audit: {ga['audit_id']}  Generated: {ga['audit_timestamp']}")
        print(f"Phase: {ga['phase']} — {ga['title']}")
        print()
        print(ga["summary"])
        print()
        print("Audit summary:")
        print(f"  Overall status:            {ga['overall_status']}")
        print(f"  Domains audited:           {ga['domain_count']}")
        print(f"  Compliant:                 {ga['compliant_count']}")
        print(f"  Partially compliant:       {ga['partially_compliant_count']}")
        print(f"  Non-compliant:             {ga['non_compliant_count']}")
        print(f"  Checks:                    {ga['check_count']}")
        print(f"  Checks met:                {ga['checks_met']}")
        print(f"  Checks partially met:      {ga['checks_partially_met']}")
        print(f"  Checks not met:            {ga['checks_not_met']}")
        print(f"  Blockers:                  {ga['blocker_count']}")
        print(f"  Warnings:                  {ga['warning_count']}")
        print(f"  Recommendations:           {ga['recommendation_count']}")
        print(f"  Execution allowed:         {'yes' if ga['execution_allowed'] else 'no'}")
        print()
        print("GovernanceAuditRecord model:")
        m = data["audit_record_model"]
        print(f"  Model: {m['model_name']}")
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        ds = data["domain_statuses"]
        print(f"Domain statuses ({ds['status_count']}):")
        for s in ds["statuses"]:
            print(f"  {s['status']}: {s['description']}")
        print()
        print(f"Domain results ({len(data['domain_results'])} domains):")
        for domain in data["domain_results"]:
            print(f"  [{domain['status']}] {domain['domain']}")
            print(f"    {domain['rationale']}")
            if domain["blockers"]:
                print(f"    Blockers: {', '.join(domain['blockers'])}")
        print()
        print(f"Audit checks ({len(data['audit_checks'])}):")
        for check in data["audit_checks"]:
            print(f"  [{check['status']}] {check['check_id']} {check['check']}")
            print(f"    {check['rationale']}")
        print()
        gap = data["gap_analysis"]
        print(f"Gap analysis ({gap['gap_count']} gaps):")
        print(f"  Missing paths:             {gap['missing_governance_paths']}")
        print(f"  Incomplete paths:          {gap['incomplete_governance_paths']}")
        print(f"  Unverified contracts:      {gap['unverified_runtime_contracts']}")
        print(f"  Unresolved blockers:       {gap['unresolved_blockers']}")
        print()
        print(f"Recommendations ({len(data['recommendations'])}):")
        for rec in data["recommendations"]:
            print(f"  [{rec['priority']}] {rec['recommendation_id']}: {rec['recommendation']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['audit_may'])}")
        print(f"  May not:           {', '.join(gb['audit_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print()
        print(data["advisory"])
    return 0


def run_runtime_trust(args: argparse.Namespace) -> int:
    data = build_runtime_trust()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        rt = data["runtime_trust"]
        print("Runtime trust assessment")
        print(f"Assessment: {rt['assessment_id']}  Generated: {rt['generated_at']}")
        print(f"Phase: {rt['phase']} — {rt['title']}")
        print()
        print(rt["summary"])
        print()
        print("Assessment summary:")
        print(f"  Runtime count:       {rt['runtime_count']}")
        print(f"  Trusted:             {rt['trusted_count']}")
        print(f"  Partially trusted:   {rt['partially_trusted_count']}")
        print(f"  Untrusted:           {rt['untrusted_count']}")
        print(f"  Assessment areas:    {rt['assessment_area_count']}")
        print(f"  Human review req'd:  {'yes' if rt['human_review_required'] else 'no'}")
        print(f"  Execution allowed:   {'yes' if rt['execution_allowed'] else 'no'}")
        print()
        print("RuntimeTrustRecord model:")
        m = data["trust_record_model"]
        print(f"  Model: {m['model_name']}")
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}")
        print(f"  human_review_required always True: {m['human_review_required_always_true']}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        tl = data["trust_levels"]
        print(f"Trust levels ({tl['level_count']}):")
        for level in tl["levels"]:
            print(f"  {level['level']}: {level['description']}")
        print()
        print(f"Assessment areas ({len(data['assessment_areas'])}):")
        for area in data["assessment_areas"]:
            print(f"  {area['area']}: {area['description']}")
        print()
        print(f"Trust records ({len(data['trust_records'])} runtimes):")
        for rec in data["trust_records"]:
            print(f"  [{rec['trust_level']}] {rec['trust_id']} (runtime: {rec['runtime_id']})")
            print(f"    Human review required: {'yes' if rec['human_review_required'] else 'no'}")
            for area in rec["assessment_areas"]:
                print(f"    [{area['confidence']}] {area['area']}: {area['rationale']}")
            if rec["blockers"]:
                print(f"    Blockers: {', '.join(rec['blockers'])}")
            if rec["warnings"]:
                print(f"    Warnings: {', '.join(rec['warnings'])}")
            print(f"    Recommendations: {', '.join(rec['recommendations'])}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['assessment_may'])}")
        print(f"  May not:             {', '.join(gb['assessment_may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_governance_maturity(args: argparse.Namespace) -> int:
    data = build_governance_maturity()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        rec = data["maturity_record"]
        print("Governance maturity assessment")
        print(f"Assessment: {rec['maturity_id']}  Generated at: {data['maturity_record_model']['model_name']}")
        print(f"Phase: 47I — Governance Maturity Assessment")
        print(f"Overall maturity: {rec['overall_maturity']}")
        print(f"Human review required: {'yes' if rec['human_review_required'] else 'no'}")
        print()
        ml = data["maturity_levels"]
        print(f"Maturity levels ({ml['level_count']}):")
        for lvl in ml["levels"]:
            print(f"  {lvl['level']}: {lvl['description']}")
        print()
        print(f"Domain assessments ({len(data['domain_assessments'])}):")
        for d in data["domain_assessments"]:
            print(f"  [{d['maturity_level']}] {d['domain']}")
            if d["blockers"]:
                print(f"    Blockers: {', '.join(d['blockers'])}")
            if d["warnings"]:
                print(f"    Warnings: {', '.join(d['warnings'])}")
        print()
        if rec["blockers"]:
            print(f"Global blockers ({len(rec['blockers'])}):")
            for b in rec["blockers"]:
                print(f"  - {b}")
            print()
        if rec["warnings"]:
            print(f"Global warnings ({len(rec['warnings'])}):")
            for w in rec["warnings"]:
                print(f"  - {w}")
            print()
        print("Execution readiness recommendation:")
        print(f"  {rec['execution_readiness_recommendation']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['assessment_may'])}")
        print(f"  May not:             {', '.join(gb['assessment_may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_readonly_invocation(args: argparse.Namespace) -> int:
    data = build_readonly_invocation()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ss = data["scaffold_summary"]
        print("Controlled read-only runtime invocation scaffold")
        print(f"Scaffold: {ss['scaffold_id']}  Generated: {ss['generated_at']}")
        print(f"Phase: {ss['phase']} — {ss['title']}")
        print()
        print(ss["summary"])
        print()
        print(f"Execution allowed: {'yes' if ss['execution_allowed'] else 'no'}")
        print(f"Human review required: {'yes' if ss['human_review_required'] else 'no'}")
        print()
        rm = data["request_model"]
        print(f"Request model: {rm['model_name']} ({rm['field_count']} fields, {rm['required_field_count']} required)")
        for f in rm["fields"]:
            print(f"  {f['name']} ({f['type']}): {f['description']}")
        print()
        pm = data["preflight_model"]
        print(f"Preflight model: {pm['model_name']} ({pm['field_count']} fields, {pm['required_field_count']} required)")
        print(f"  execution_allowed always False in 48A: {pm['execution_allowed_always_false_in_48a']}")
        for f in pm["fields"]:
            print(f"  {f['name']} ({f['type']}): {f['description']}")
        print()
        rp = data["result_placeholder_model"]
        print(f"Result placeholder model: {rp['model_name']} ({rp['field_count']} fields)")
        print(f"  Note: {rp['placeholder_note']}")
        print()
        sp = data["sample_preflight"]
        print("Sample preflight evaluation:")
        print(f"  execution_allowed: {sp['execution_allowed']}")
        print(f"  Blockers: {', '.join(sp['blockers'])}")
        if sp["warnings"]:
            print(f"  Warnings: {', '.join(sp['warnings'])}")
        print()
        res = data["result_placeholder"]
        print(f"Result placeholder: status={res['status']}, stdout={res['stdout']}, stderr={res['stderr']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_result_capture(args: argparse.Namespace) -> int:
    data = build_invocation_result_capture()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ss = data["scaffold_summary"]
        print("Invocation result capture scaffold")
        print(f"Scaffold: {ss['scaffold_id']}  Generated: {ss['generated_at']}")
        print(f"Phase: {ss['phase']} — {ss['title']}")
        print()
        print(ss["summary"])
        print()
        print(f"Capture allowed: {'yes' if ss['capture_allowed'] else 'no'}")
        print(f"Human review required: {'yes' if ss['human_review_required'] else 'no'}")
        print(f"Supported capture statuses: {', '.join(ss['supported_capture_statuses'])}")
        print()
        cm = data["capture_model"]
        print(f"Capture model: {cm['model_name']} ({cm['field_count']} fields, {cm['required_field_count']} required)")
        for f in cm["fields"]:
            print(f"  {f['name']} ({f['type']}): {f['description']}")
        print()
        pm = data["preflight_model"]
        print(f"Preflight model: {pm['model_name']} ({pm['field_count']} fields, {pm['required_field_count']} required)")
        print(f"  capture_allowed always False in 48B: {pm['capture_allowed_always_false_in_48b']}")
        for f in pm["fields"]:
            print(f"  {f['name']} ({f['type']}): {f['description']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields, {sm['required_field_count']} required)")
        for f in sm["fields"]:
            print(f"  {f['name']} ({f['type']}): {f['description']}")
        print()
        sp = data["sample_preflight"]
        print("Sample capture preflight:")
        print(f"  capture_allowed: {sp['capture_allowed']}")
        print(f"  Blockers: {', '.join(sp['blockers'])}")
        if sp["warnings"]:
            print(f"  Warnings: {', '.join(sp['warnings'])}")
        print()
        sc = data["sample_capture"]
        print(f"Sample capture: status={sc['capture_status']}, stdout={sc['stdout']}, stderr={sc['stderr']}, exit_code={sc['exit_code']}")
        print()
        ssum = data["sample_summary"]
        print(f"Sample summary: ready_for_review={ssum['ready_for_review']}, stdout_present={ssum['stdout_present']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Capture allowed:     {gb['capture_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_runtime_contract_enforcement(args: argparse.Namespace) -> int:
    data = build_runtime_contract_enforcement()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        es = data["enforcement_summary"]
        print("Runtime contract enforcement")
        print(f"Assessment: {es['summary_id']}  Generated: {es['generated_at']}")
        print(f"Phase: {es['phase']} — {es['title']}")
        print()
        print(es["summary"])
        print()
        print(f"Runtimes evaluated:      {es['runtime_count']}")
        print(f"Blocked:                 {es['blocked_count']}")
        print(f"Allowed:                 {es['allowed_count']}")
        print(f"Enforcement checks:      {es['enforcement_check_count']}")
        print(f"Execution allowed:       {'yes' if es['execution_allowed'] else 'no'}")
        print(f"Human review required:   {'yes' if es['human_review_required'] else 'no'}")
        print()
        rm = data["result_model"]
        print(f"Result model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  Supported statuses: {', '.join(rm['supported_statuses'])}")
        print(f"  execution_allowed always False in 48C: {rm['execution_allowed_always_false_in_48c']}")
        print()
        print(f"Enforcement checks ({len(data['enforcement_checks'])}):")
        for chk in data["enforcement_checks"]:
            blocking = "blocking" if chk["blocking"] else "advisory"
            print(f"  [{blocking}] {chk['check_id']}: {chk['description']}")
        print()
        print(f"Enforcement results ({len(data['enforcement_results'])} runtimes):")
        for res in data["enforcement_results"]:
            print(f"  [{res['enforcement_status']}] {res['runtime_id']}")
            print(f"    execution_allowed: {res['execution_allowed']}")
            if res["failed_checks"]:
                print(f"    Failed checks: {', '.join(res['failed_checks'])}")
            if res["warnings"]:
                print(f"    Warnings: {', '.join(res['warnings'])}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_authorization_enforcement(args: argparse.Namespace) -> int:
    data = build_invocation_authorization_enforcement()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        es = data["enforcement_summary"]
        print("Invocation authorization enforcement")
        print(f"Assessment: {es['summary_id']}  Generated: {es['generated_at']}")
        print(f"Phase: {es['phase']} — {es['title']}")
        print()
        print(es["summary"])
        print()
        print(f"Runtimes evaluated:      {es['runtime_count']}")
        print(f"Blocked:                 {es['blocked_count']}")
        print(f"Allowed:                 {es['allowed_count']}")
        print(f"Enforcement chain steps: {es['enforcement_chain_length']}")
        print(f"Execution allowed:       {'yes' if es['execution_allowed'] else 'no'}")
        print(f"Human review required:   {'yes' if es['human_review_required'] else 'no'}")
        print()
        rm = data["result_model"]
        print(f"Result model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  Supported statuses: {', '.join(rm['supported_statuses'])}")
        print(f"  execution_allowed always False in 48D: {rm['execution_allowed_always_false_in_48d']}")
        print()
        print(f"Enforcement chain ({len(data['enforcement_chain'])} steps):")
        for step in data["enforcement_chain"]:
            print(f"  {step['step']}. [{step['input']}] {step['check_id']}: {step['description']}")
        print()
        print(f"Enforcement results ({len(data['enforcement_results'])} runtimes):")
        for res in data["enforcement_results"]:
            print(f"  [{res['enforcement_status']}] {res['runtime_id']}")
            print(f"    execution_allowed: {res['execution_allowed']}")
            print(f"    authorization_status: {res['authorization_status']}")
            print(f"    contract_status: {res['contract_status']}")
            print(f"    preflight_status: {res['preflight_status']}")
            print(f"    capture_status: {res['capture_status']}")
            if res["failed_checks"]:
                print(f"    Failed checks ({len(res['failed_checks'])}): {', '.join(res['failed_checks'])}")
            if res["warnings"]:
                print(f"    Warnings: {', '.join(res['warnings'])}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_audit_trail(args: argparse.Namespace) -> int:
    data = build_invocation_audit_trail()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        aus = data["audit_summary"]
        print("Invocation audit trail")
        print(f"Assessment: {aus['summary_id']}  Generated: {aus['generated_at']}")
        print(f"Phase: {aus['phase']} — {aus['title']}")
        print()
        print(aus["summary"])
        print()
        print(f"Runtimes evaluated:  {aus['runtime_count']}")
        print(f"Blocked:             {aus['blocked_count']}")
        print(f"Audit ready:         {aus['audit_ready_count']}")
        print(f"Models defined:      {aus['model_count']}")
        print(f"Execution allowed:   {'yes' if aus['execution_allowed'] else 'no'}")
        print(f"Human review req'd:  {'yes' if aus['human_review_required'] else 'no'}")
        print()
        print(f"Audit models ({len(data['audit_models'])}):")
        for m in data["audit_models"]:
            print(f"  {m['model_name']}: {m['field_count']} fields ({m['required_field_count']} required)")
        print()
        print(f"Audit records ({len(data['audit_records'])} runtimes):")
        for rec in data["audit_records"]:
            print(f"  [{rec['audit_status']}] {rec['runtime_id']}")
            print(f"    audit_id:     {rec['audit_id']}")
            print(f"    created_by:   {rec['created_by']}")
        print()
        print(f"Audit preflights ({len(data['audit_preflights'])} runtimes):")
        for pf in data["audit_preflights"]:
            print(f"  [{pf['runtime_id']}] audit_ready: {pf['audit_ready']}")
            if pf["blockers"]:
                print(f"    Blockers ({len(pf['blockers'])}): {', '.join(pf['blockers'])}")
        print()
        print(f"Audit summaries ({len(data['audit_summaries'])} runtimes):")
        for s in data["audit_summaries"]:
            print(f"  [{s['runtime_id']}] execution_allowed: {s['execution_allowed']}, "
                  f"audit_ready: {s['audit_ready']}, human_review_required: {s['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_readonly_runtime_pilot(args: argparse.Namespace) -> int:
    data = build_readonly_runtime_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ps = data["pilot_summary"]
        print("Controlled read-only runtime invocation pilot")
        print(f"Assessment: {ps['summary_id']}  Generated: {ps['generated_at']}")
        print(f"Phase: {ps['phase']} — {ps['title']}")
        print()
        print(ps["summary"])
        print()
        print(f"Runtimes evaluated:  {ps['runtime_count']}")
        print(f"Blocked:             {ps['blocked_count']}")
        print(f"Eligible:            {ps['eligible_count']}")
        print(f"Lifecycle steps:     {ps['lifecycle_steps']}")
        print(f"Execution allowed:   {'yes' if ps['execution_allowed'] else 'no'}")
        print(f"Human review req'd:  {'yes' if ps['human_review_required'] else 'no'}")
        print()
        rm = data["result_model"]
        print(f"Result model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  Supported statuses: {', '.join(rm['supported_statuses'])}")
        print(f"  execution_allowed always False in 48F: {rm['execution_allowed_always_false_in_48f']}")
        print()
        print(f"Pilot lifecycle ({len(data['pilot_lifecycle'])} steps):")
        for step in data["pilot_lifecycle"]:
            print(f"  {step['step']}. [{step['input']}] {step['name']}: {step['description']}")
        print()
        print(f"Pilot results ({len(data['pilot_results'])} runtimes):")
        for res in data["pilot_results"]:
            print(f"  [{res['pilot_status']}] {res['runtime_id']}")
            print(f"    execution_allowed:    {res['execution_allowed']}")
            print(f"    authorization_status: {res['authorization_status']}")
            print(f"    contract_status:      {res['contract_status']}")
            print(f"    preflight_status:     {res['preflight_status']}")
            print(f"    audit_status:         {res['audit_status']}")
            print(f"    capture_status:       {res['capture_status']}")
            print(f"    human_approval:       {res['human_approval_status']}")
            if res["blockers"]:
                print(f"    Blockers ({len(res['blockers'])}): {', '.join(res['blockers'])}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_result_review(args: argparse.Namespace) -> int:
    data = build_invocation_result_review()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        rs = data["review_summary"]
        print("Invocation result review workflow")
        print(f"Assessment: {rs['summary_id']}  Generated: {rs['generated_at']}")
        print(f"Phase: {rs['phase']} — {rs['title']}")
        print()
        print(rs["summary"])
        print()
        print(f"Runtimes evaluated:  {rs['runtime_count']}")
        print(f"Not executed:        {rs['not_executed_count']}")
        print(f"Review ready:        {rs['review_ready_count']}")
        print(f"Models defined:      {rs['model_count']}")
        print(f"Execution allowed:   {'yes' if rs['execution_allowed'] else 'no'}")
        print(f"Human review req'd:  {'yes' if rs['human_review_required'] else 'no'}")
        print()
        print(f"Review models ({len(data['review_models'])}):")
        for m in data["review_models"]:
            print(f"  {m['model_name']}: {m['field_count']} fields ({m['required_field_count']} required)")
        print()
        print(f"Review records ({len(data['review_records'])} runtimes):")
        for rec in data["review_records"]:
            print(f"  [{rec['review_status']}] {rec['runtime_id']}")
            print(f"    review_id:              {rec['review_id']}")
            print(f"    human_review_required:  {rec['human_review_required']}")
            if rec["errors"]:
                print(f"    Errors ({len(rec['errors'])}): {', '.join(rec['errors'])}")
        print()
        print(f"Review preflights ({len(data['review_preflights'])} runtimes):")
        for pf in data["review_preflights"]:
            print(f"  [{pf['runtime_id']}] review_allowed: {pf['review_allowed']}")
            if pf["blockers"]:
                print(f"    Blockers ({len(pf['blockers'])}): {', '.join(pf['blockers'])}")
        print()
        print(f"Review summaries ({len(data['review_summaries'])} runtimes):")
        for s in data["review_summaries"]:
            print(f"  [{s['runtime_id']}] review_status: {s['review_status']}, "
                  f"ready_for_human_review: {s['ready_for_human_review']}, "
                  f"execution_allowed: {s['execution_allowed']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_invocation_evidence(args: argparse.Namespace) -> int:
    data = build_invocation_evidence()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        es = data["evidence_summary"]
        print("Invocation evidence model")
        print(f"Assessment: {es['summary_id']}  Generated: {es['generated_at']}")
        print(f"Phase: {es['phase']} — {es['title']}")
        print()
        print(es["summary"])
        print()
        print(f"Runtimes evaluated:  {es['runtime_count']}")
        print(f"Not executed:        {es['not_executed_count']}")
        print(f"Evidence ready:      {es['evidence_ready_count']}")
        print(f"Models defined:      {es['model_count']}")
        print(f"Execution allowed:   {'yes' if es['execution_allowed'] else 'no'}")
        print(f"Human review req'd:  {'yes' if es['human_review_required'] else 'no'}")
        print()
        print(f"Evidence models ({len(data['evidence_models'])}):")
        for m in data["evidence_models"]:
            print(f"  {m['model_name']}: {m['field_count']} fields ({m['required_field_count']} required)")
        print()
        print(f"Evidence records ({len(data['evidence_records'])} runtimes):")
        for rec in data["evidence_records"]:
            print(f"  [{rec['evidence_status']}] {rec['runtime_id']}")
            print(f"    evidence_id:  {rec['evidence_id']}")
            print(f"    created_at:   {rec['created_at']}")
        print()
        print(f"Evidence preflights ({len(data['evidence_preflights'])} runtimes):")
        for pf in data["evidence_preflights"]:
            print(f"  [{pf['runtime_id']}] evidence_ready: {pf['evidence_ready']}")
            if pf["blockers"]:
                print(f"    Blockers ({len(pf['blockers'])}): {', '.join(pf['blockers'])}")
        print()
        print(f"Evidence summaries ({len(data['evidence_summaries'])} runtimes):")
        for s in data["evidence_summaries"]:
            print(f"  [{s['runtime_id']}] evidence_ready: {s['evidence_ready']}, "
                  f"execution_allowed: {s['execution_allowed']}, "
                  f"human_review_required: {s['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_rollback_validation_design(args: argparse.Namespace) -> int:
    data = build_write_rollback_validation_design()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        design = data["write_rollback_validation_design"]
        print("Write rollback validation workflow design")
        print(f"Design: {design['design_id']}  Generated: {design['generated_at']}")
        print(f"Phase: {design['phase']} — {design['title']}")
        print()
        print(design["summary"])
        print()
        print("Rollback validation lifecycle:")
        for step in data["rollback_lifecycle"]:
            req = "required" if step["required"] else "optional"
            print(f"  {step['step']}. {step['name']} ({req})")
            print(f"     {step['description']}")
            print(f"     Completed by: {step['completed_by']}")
        print()
        print("RollbackValidationRecord model:")
        m = data["rollback_validation_record_model"]
        print(f"  Fields: {m['field_count']}  Required: {m['required_field_count']}")
        print(f"  Immutable: {m['immutable_field_count']}  Groups: {', '.join(m['groups'])}")
        for field in m["fields"]:
            imm = "immutable" if field["immutable"] else "mutable"
            print(f"    [{field['group']}] {field['name']} ({field['type']}, {imm}): {field['description']}")
        print()
        print("Validation statuses:")
        vs = data["validation_statuses"]
        print(f"  Status count: {vs['status_count']}")
        print(f"  Terminal: {', '.join(vs['terminal_statuses'])}")
        print(f"  Escalation: {', '.join(vs['escalation_statuses'])}")
        for status in vs["statuses"]:
            terminal = "terminal" if status["terminal"] else "non-terminal"
            print(f"  {status['status']} ({terminal})")
            print(f"    {status['description']}")
        print()
        print("Rollback scope validation rules:")
        sr = data["rollback_scope_validation_rules"]
        print(f"  Rule count: {sr['rule_count']}  All violations trigger escalation: {sr['all_violations_trigger_escalation']}")
        for rule in sr["rules"]:
            print(f"  {rule['rule']} → {rule['violation_triggers']}")
            print(f"    {rule['description']}")
        print()
        print("Rollback target validation rules:")
        tr = data["rollback_target_validation_rules"]
        print(f"  Rule count: {tr['rule_count']}  All violations trigger escalation: {tr['all_violations_trigger_escalation']}")
        for rule in tr["rules"]:
            print(f"  {rule['rule']} → {rule['violation_triggers']}")
            print(f"    {rule['description']}")
        print()
        print("Rollback risk assessment:")
        ra = data["rollback_risk_assessment"]
        print(f"  Risk dimensions: {ra['risk_count']}")
        for risk in ra["risks"]:
            print(f"  {risk['risk']} (severity: {risk['severity']})")
            print(f"    {risk['description']}")
        print()
        print("Governance requirements:")
        gr = data["governance_requirements"]
        print(f"  Requirement count: {gr['requirement_count']}  All required: {gr['all_required']}")
        for req in gr["requirements"]:
            print(f"  {req['requirement']}: {req['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:     {', '.join(gb['workflow_may'])}")
        print(f"  May not: {', '.join(gb['workflow_may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review required: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_multi_agent_readonly_pilot(args: argparse.Namespace) -> int:
    data = build_multi_agent_readonly_pilot()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ps = data["pilot_summary"]
        print("Multi-agent read-only pilot")
        print(f"Assessment: {ps['summary_id']}  Generated: {ps['generated_at']}")
        print(f"Phase: {ps['phase']} — {ps['title']}")
        print()
        print(ps["summary"])
        print()
        print(f"Runtimes evaluated:  {ps['runtime_count']}")
        print(f"Blocked:             {ps['blocked_count']}")
        print(f"Eligible:            {ps['eligible_count']}")
        print(f"Consensus status:    {ps['consensus_status']}")
        print(f"Lifecycle steps:     {ps['lifecycle_steps']}")
        print(f"Execution allowed:   {'yes' if ps['execution_allowed'] else 'no'}")
        print(f"Human review req'd:  {'yes' if ps['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported strategies: {', '.join(cm['supported_strategies'])}")
        print(f"  execution_allowed always False in 49A: {cm['execution_allowed_always_false_in_49a']}")
        print()
        rm = data["result_model"]
        print(f"Result model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  Supported consensus statuses: {', '.join(rm['supported_consensus_statuses'])}")
        print(f"  execution_allowed always False in 49A: {rm['execution_allowed_always_false_in_49a']}")
        print()
        print(f"Pilot lifecycle ({len(data['pilot_lifecycle'])} steps):")
        for step in data["pilot_lifecycle"]:
            print(f"  {step['step']}. [{step['input']}] {step['name']}: {step['description']}")
        print()
        pr = data["pilot_result"]
        print("Pilot result:")
        print(f"  pilot_id:              {pr['pilot_id']}")
        print(f"  consensus_status:      {pr['consensus_status']}")
        print(f"  execution_allowed:     {pr['execution_allowed']}")
        print(f"  human_review_required: {pr['human_review_required']}")
        print(f"  Runtime results ({len(pr['runtime_results'])} runtimes):")
        for res in pr["runtime_results"]:
            print(f"    [{res['pilot_status']}] {res['runtime_id']} (trust: {res['trust_status']})")
            if res["blockers"]:
                print(f"      Blockers ({len(res['blockers'])}): {', '.join(res['blockers'])}")
            if res["warnings"]:
                print(f"      Warnings ({len(res['warnings'])}): {', '.join(res['warnings'])}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_consensus_engine(args: argparse.Namespace) -> int:
    data = build_consensus_engine()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        cs = data["consensus_summary"]
        print("Multi-agent consensus engine")
        print(f"Assessment: {cs['summary_id']}  Generated: {cs['generated_at']}")
        print(f"Phase: {cs['phase']} — {cs['title']}")
        print()
        print(cs["summary"])
        print()
        print(f"Agents evaluated:    {cs['agent_count']}")
        print(f"Agreement:           {cs['agreement_count']}")
        print(f"Disagreement:        {cs['disagreement_count']}")
        print(f"Unavailable:         {cs['unavailable_count']}")
        print(f"Consensus status:    {cs['consensus_status']}")
        print(f"Escalation required: {'yes' if cs['escalation_required'] else 'no'}")
        print(f"Escalation paths:    {cs['escalation_path_count']}")
        print(f"Execution allowed:   {'yes' if cs['execution_allowed'] else 'no'}")
        print(f"Human review req'd:  {'yes' if cs['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported strategies: {', '.join(cm['supported_strategies'])}")
        print(f"  execution_allowed always False in 49B: {cm['execution_allowed_always_false_in_49b']}")
        print()
        rm = data["result_model"]
        print(f"Result model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  Supported consensus statuses: {', '.join(rm['supported_consensus_statuses'])}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        sr = data["sample_result"]
        print("Sample result:")
        print(f"  consensus_status:    {sr['consensus_status']}")
        print(f"  escalation_required: {sr['escalation_required']}")
        print(f"  Agent positions ({len(sr['agent_positions'])} agents):")
        for pos in sr["agent_positions"]:
            print(f"    [{pos['position']}] {pos['agent_id']} (trust: {pos['trust_level']})")
            if pos.get("blocker"):
                print(f"      Blocker: {pos['blocker']}")
        print()
        print(f"Escalation paths ({len(data['escalation_paths'])}):")
        for ep in data["escalation_paths"]:
            print(f"  {ep['path']} (trigger: {ep['trigger']}, human_required: {ep['human_required']})")
            print(f"    {ep['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_decision_record(args: argparse.Namespace) -> int:
    data = build_decision_record()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        s = data["decision_summary"]
        print("Multi-agent decision record")
        print(f"Assessment: {s['summary_id']}  Generated: {s['generated_at']}")
        print(f"Phase: {s['phase']} — {s['title']}")
        print()
        print(s["summary"])
        print()
        print(f"Agents:              {s['agent_count']}")
        print(f"Decision status:     {s['decision_status']}")
        print(f"Execution allowed:   {'yes' if s['execution_allowed'] else 'no'}")
        print(f"Human review req'd:  {'yes' if s['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported decision statuses: {', '.join(cm['supported_decision_statuses'])}")
        print(f"  execution_allowed always False in 49E: {cm['execution_allowed_always_false_in_49e']}")
        print()
        rm = data["record_model"]
        print(f"Record model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  Supported decision statuses: {', '.join(rm['supported_decision_statuses'])}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        sr = data["sample_record"]
        print("Sample record:")
        print(f"  decision_status:     {sr['decision_status']}")
        print(f"  consensus_status:    {sr['consensus_status']}")
        print(f"  arbitration_status:  {sr['arbitration_status']}")
        print(f"  execution_allowed:   {sr['execution_allowed']}")
        print(f"  human_review_req'd:  {sr['human_review_required']}")
        print(f"  Blockers ({len(sr['blockers'])}):")
        for b in sr["blockers"]:
            print(f"    {b}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_evidence_framework(args: argparse.Namespace) -> int:
    data = build_evidence_framework()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        s = data["framework_summary"]
        print("Multi-agent evidence framework")
        print(f"Assessment: {s['summary_id']}  Generated: {s['generated_at']}")
        print(f"Phase: {s['phase']} — {s['title']}")
        print()
        print(s["summary"])
        print()
        print(f"Agents:                {s['agent_count']}")
        print(f"Evidence kinds:        {s['evidence_kind_count']}")
        print(f"Review workflow steps: {s['review_workflow_step_count']}")
        print(f"Execution allowed:     {'yes' if s['execution_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if s['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported evidence kinds: {', '.join(cm['supported_evidence_kinds'])}")
        print(f"  execution_allowed always False in 49D: {cm['execution_allowed_always_false_in_49d']}")
        print()
        rm = data["record_model"]
        print(f"Record model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  Trust levels:        {', '.join(rm['supported_trust_levels'])}")
        print(f"  Validation statuses: {', '.join(rm['supported_validation_statuses'])}")
        print()
        bm = data["bundle_model"]
        print(f"Bundle model: {bm['model_name']} ({bm['field_count']} fields)")
        print(f"  Bundle statuses: {', '.join(bm['supported_bundle_statuses'])}")
        print()
        sb = data["sample_bundle"]
        print(f"Sample bundle: {sb['bundle_id']} (status: {sb['bundle_status']})")
        print(f"  Participating agents ({len(sb['participating_agents'])}):")
        for agent_id in sb["participating_agents"]:
            print(f"    {agent_id}")
        print(f"  Evidence records ({len(sb['evidence_records'])}):")
        for rec in sb["evidence_records"]:
            print(
                f"    [{rec['validation_status']}] {rec['source_agent']} "
                f"(trust: {rec['trust_level']}, kind: {rec['evidence_kind']})"
            )
        print()
        print(f"Review workflow ({len(data['review_workflow'])} steps):")
        for step in data["review_workflow"]:
            human_flag = " [human required]" if step["human_required"] else ""
            print(f"  {step['step']}{human_flag}")
            print(f"    {step['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_arbitration(args: argparse.Namespace) -> int:
    data = build_arbitration_framework()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        s = data["arbitration_summary"]
        print("Multi-agent arbitration framework")
        print(f"Assessment: {s['summary_id']}  Generated: {s['generated_at']}")
        print(f"Phase: {s['phase']} — {s['title']}")
        print()
        print(s["summary"])
        print()
        print(f"Agents evaluated:      {s['agent_count']}")
        print(f"Arbitration reasons:   {s['arbitration_reason_count']}")
        print(f"Arbitration status:    {s['arbitration_status']}")
        print(f"Escalation required:   {'yes' if s['escalation_required'] else 'no'}")
        print(f"Escalation paths:      {s['escalation_path_count']}")
        print(f"Execution allowed:     {'yes' if s['execution_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if s['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported arbitration reasons: {', '.join(cm['supported_arbitration_reasons'])}")
        print(f"  execution_allowed always False in 49C: {cm['execution_allowed_always_false_in_49c']}")
        print()
        dm = data["decision_model"]
        print(f"Decision model: {dm['model_name']} ({dm['field_count']} fields)")
        print(f"  Supported arbitration statuses: {', '.join(dm['supported_arbitration_statuses'])}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        sd = data["sample_decision"]
        print("Sample decision:")
        print(f"  arbitration_status:  {sd['arbitration_status']}")
        print(f"  escalation_required: {sd['escalation_required']}")
        print(f"  execution_allowed:   {sd['execution_allowed']}")
        print(f"  Agent positions ({len(sd['agent_positions'])} agents):")
        for pos in sd["agent_positions"]:
            print(f"    [{pos['position']}] {pos['agent_id']}")
            if pos.get("blocker"):
                print(f"      Blocker: {pos['blocker']}")
        print()
        print(f"Escalation paths ({len(data['escalation_paths'])}):")
        for ep in data["escalation_paths"]:
            print(f"  {ep['path']} (trigger: {ep['trigger']}, human_required: {ep['human_required']})")
            print(f"    {ep['description']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_multi_agent_governance_audit(args: argparse.Namespace) -> int:
    data = build_multi_agent_governance_audit()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        s = data["audit_overview"]
        print("Multi-agent governance audit")
        print(f"Assessment: {s['summary_id']}  Generated: {s['generated_at']}")
        print(f"Phase: {s['phase']} — {s['title']}")
        print()
        print(s["summary"])
        print()
        print(f"Domains assessed:    {s['domain_count']}")
        print(f"Blockers:            {s['blocker_count']}")
        print(f"Warnings:            {s['warning_count']}")
        print(f"Audit status:        {s['audit_status']}")
        print(f"Execution allowed:   {'yes' if s['execution_allowed'] else 'no'}")
        print(f"Human review req'd:  {'yes' if s['human_review_required'] else 'no'}")
        print()
        rm = data["record_model"]
        print(f"Record model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  Supported audit statuses: {', '.join(rm['supported_audit_statuses'])}")
        print(f"  execution_allowed always False in 49F: {rm['execution_allowed_always_false_in_49f']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Domain findings:")
        for domain, finding in data["domain_findings"].items():
            print(f"  [{finding['status'].upper()}] {domain}: {finding['finding']}")
        print()
        sr = data["sample_record"]
        print("Sample record:")
        print(f"  audit_status:        {sr['audit_status']}")
        print(f"  execution_allowed:   {sr['execution_allowed']}")
        print(f"  human_review_req'd:  {sr['human_review_required']}")
        if sr["warnings"]:
            print(f"  Warnings ({len(sr['warnings'])}):")
            for w in sr["warnings"]:
                print(f"    {w}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                 {', '.join(gb['may'])}")
        print(f"  May not:             {', '.join(gb['may_not'])}")
        print(f"  Execution allowed:   {gb['execution_allowed']}")
        print(f"  Human review req'd:  {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_governance_state_audit(args: argparse.Namespace) -> int:
    data = build_governance_state_audit()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        s = data["audit_overview"]
        print("Governance state integrity audit")
        print(f"Assessment: {s['summary_id']}  Generated: {s['generated_at']}")
        print(f"Phase: {s['phase']} — {s['title']}")
        print()
        print(s["summary"])
        print()
        print(f"Domains assessed:      {s['domain_count']}")
        print(f"Blockers:              {s['blocker_count']}")
        print(f"Warnings:              {s['warning_count']}")
        print(f"Stale references:      {s['stale_reference_count']}")
        print(f"Audit status:          {s['audit_status']}")
        print(f"Execution allowed:     {'yes' if s['execution_allowed'] else 'no'}")
        print()
        rm = data["record_model"]
        print(f"Record model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  Supported audit statuses: {', '.join(rm['supported_audit_statuses'])}")
        print(f"  execution_allowed always False in 49G: {rm['execution_allowed_always_false_in_49g']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Domain findings:")
        for domain, finding in data["domain_findings"].items():
            stale = finding["stale_references"]
            stale_tag = f" [stale_refs={stale}]" if stale else ""
            print(f"  [{finding['status'].upper()}]{stale_tag} {domain}: {finding['finding']}")
        print()
        sr = data["sample_record"]
        print("Sample record:")
        print(f"  audit_status:          {sr['audit_status']}")
        print(f"  execution_allowed:     {sr['execution_allowed']}")
        if sr["warnings"]:
            print(f"  Warnings ({len(sr['warnings'])}):")
            for w in sr["warnings"]:
                print(f"    {w}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  stale_reference_count: {ss['stale_reference_count']}")
        print(f"  audit_status:          {ss['audit_status']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['may'])}")
        print(f"  May not:           {', '.join(gb['may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print()
        print(data["advisory"])
    return 0


def run_governance_state_repair(args: argparse.Namespace) -> int:
    data = build_governance_state_repair()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["repair_overview"]
        print("Governance state repair framework")
        print(f"Assessment: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Repair domains:        {ov['repair_domain_count']}")
        print(f"Candidates:            {ov['candidate_count']}")
        print(f"Blocked:               {ov['blocked_count']}")
        print(f"Warnings:              {ov['warning_count']}")
        print(f"Plan status:           {ov['plan_status']}")
        print(f"Repair allowed:        {'yes' if ov['repair_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported repair statuses: {', '.join(cm['supported_repair_statuses'])}")
        print(f"  repair_allowed always False in 49H: {cm['repair_allowed_always_false_in_49h']}")
        print()
        pm = data["plan_model"]
        print(f"Plan model: {pm['model_name']} ({pm['field_count']} fields)")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Repair candidates:")
        for c in data["repair_candidates"]:
            print(
                f"  [{c['repair_status'].upper()}] {c['repair_domain']}: "
                f"{c['recommended_action']}"
            )
        print()
        rp = data["repair_plan"]
        print("Repair plan:")
        print(f"  plan_status:           {rp['plan_status']}")
        print(f"  repair_allowed:        {rp['repair_allowed']}")
        print(f"  human_review_req'd:    {rp['human_review_required']}")
        if rp["warnings"]:
            print(f"  Warnings ({len(rp['warnings'])}):")
            for w in rp["warnings"]:
                print(f"    {w}")
        print()
        rs = data["repair_summary"]
        print("Repair summary:")
        print(f"  candidate_count:       {rs['candidate_count']}")
        print(f"  blocked_count:         {rs['blocked_count']}")
        print(f"  warning_count:         {rs['warning_count']}")
        print(f"  repair_allowed:        {rs['repair_allowed']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['may'])}")
        print(f"  May not:           {', '.join(gb['may_not'])}")
        print(f"  Repair allowed:    {gb['repair_allowed']}")
        print(f"  Human review req'd:{gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_task_transition_governance(args: argparse.Namespace) -> int:
    data = build_task_transition_governance()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["transition_overview"]
        print("Task transition governance")
        print(f"Assessment: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Transition domains:    {ov['transition_domain_count']}")
        print(f"Blockers:              {ov['blocker_count']}")
        print(f"Warnings:              {ov['warning_count']}")
        print(f"Validation status:     {ov['validation_status']}")
        print(f"Transition allowed:    {'yes' if ov['transition_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses: {', '.join(cm['supported_transition_statuses'])}")
        print(f"  transition_allowed always False in 49I: {cm['transition_allowed_always_false_in_49i']}")
        print()
        vm = data["validation_model"]
        print(f"Validation model: {vm['model_name']} ({vm['field_count']} fields)")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Domain checks:")
        for domain, check in data["domain_checks"].items():
            warn_tag = f" [{len(check['warnings'])} warning(s)]" if check["warnings"] else ""
            print(f"  [{check['status'].upper()}]{warn_tag} {domain}: {check['finding']}")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  transition_type:       {sc['transition_type']}")
        print(f"  transition_allowed:    {sc['transition_allowed']}")
        print(f"  human_review_req'd:    {sc['human_review_required']}")
        if sc["required_actions"]:
            print(f"  Required actions ({len(sc['required_actions'])}):")
            for a in sc["required_actions"]:
                print(f"    {a}")
        print()
        sv = data["sample_validation"]
        print("Sample validation:")
        print(f"  previous_task_status:  {sv['previous_task_status']}")
        print(f"  next_task_status:      {sv['next_task_status']}")
        print(f"  session_status:        {sv['session_status']}")
        print(f"  continuity_status:     {sv['continuity_status']}")
        print(f"  scope_status:          {sv['scope_status']}")
        if sv["warnings"]:
            print(f"  Warnings ({len(sv['warnings'])}):")
            for w in sv["warnings"]:
                print(f"    {w}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  validation_status:     {ss['validation_status']}")
        print(f"  blocker_count:         {ss['blocker_count']}")
        print(f"  warning_count:         {ss['warning_count']}")
        print(f"  transition_allowed:    {ss['transition_allowed']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                {', '.join(gb['may'])}")
        print(f"  May not:            {', '.join(gb['may_not'])}")
        print(f"  Transition allowed: {gb['transition_allowed']}")
        print(f"  Human review req'd: {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_session_continuity_governance(args: argparse.Namespace) -> int:
    data = build_session_continuity_governance()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["continuity_overview"]
        print("Session continuity governance")
        print(f"Assessment: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Governance domains:    {ov['governance_domain_count']}")
        print(f"Blockers:              {ov['blocker_count']}")
        print(f"Warnings:              {ov['warning_count']}")
        print(f"Validation status:     {ov['validation_status']}")
        print(f"Refresh allowed:       {'yes' if ov['refresh_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses: {', '.join(cm['supported_continuity_statuses'])}")
        print(f"  refresh_allowed always False in 49J: {cm['refresh_allowed_always_false_in_49j']}")
        print()
        vm = data["validation_model"]
        print(f"Validation model: {vm['model_name']} ({vm['field_count']} fields)")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Domain checks:")
        for domain, check in data["domain_checks"].items():
            warn_tag = f" [{len(check['warnings'])} warning(s)]" if check["warnings"] else ""
            print(f"  [{check['status'].upper()}]{warn_tag} {domain}: {check['finding']}")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  continuity_status:     {sc['continuity_status']}")
        print(f"  refresh_allowed:       {sc['refresh_allowed']}")
        print(f"  human_review_req'd:    {sc['human_review_required']}")
        print()
        sv = data["sample_validation"]
        print("Sample validation:")
        print(f"  active_task_status:    {sv['active_task_status']}")
        print(f"  session_task_status:   {sv['session_task_status']}")
        print(f"  stale_reference_status:{sv['stale_reference_status']}")
        print(f"  orphaned_state_status: {sv['orphaned_state_status']}")
        print(f"  handoff_alignment:     {sv['handoff_alignment_status']}")
        if sv["warnings"]:
            print(f"  Warnings ({len(sv['warnings'])}):")
            for w in sv["warnings"]:
                print(f"    {w}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  validation_status:     {ss['validation_status']}")
        print(f"  blocker_count:         {ss['blocker_count']}")
        print(f"  warning_count:         {ss['warning_count']}")
        print(f"  refresh_allowed:       {ss['refresh_allowed']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['may'])}")
        print(f"  May not:           {', '.join(gb['may_not'])}")
        print(f"  Refresh allowed:   {gb['refresh_allowed']}")
        print(f"  Human review req'd:{gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_governance_invariants(args: argparse.Namespace) -> int:
    data = build_governance_invariants()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["invariant_overview"]
        print("Governance invariant enforcement")
        print(f"Assessment: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Invariant domains:     {ov['invariant_domain_count']}")
        print(f"Invariants audited:    {ov['invariant_count']}")
        print(f"Compliant:             {ov['compliant_count']}")
        print(f"Warnings:              {ov['warning_count']}")
        print(f"Blockers:              {ov['blocker_count']}")
        print(f"Assessment status:     {ov['assessment_status']}")
        print(f"Execution allowed:     {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        im = data["invariant_model"]
        print(f"Invariant model: {im['model_name']} ({im['field_count']} fields)")
        print(f"  Supported statuses: {', '.join(im['supported_invariant_statuses'])}")
        print(f"  execution_allowed always False in 49K: {im['execution_allowed_always_false_in_49k']}")
        print()
        am = data["assessment_model"]
        print(f"Assessment model: {am['model_name']} ({am['field_count']} fields)")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Invariant results:")
        for r in data["invariant_results"]:
            warn_tag = f" [{len(r['warnings'])} warning(s)]" if r["warnings"] else ""
            print(
                f"  [{r['invariant_status'].upper()}]{warn_tag} "
                f"{r['invariant_name']} ({r['invariant_domain']})"
            )
        print()
        sa = data["sample_assessment"]
        print("Sample assessment:")
        print(f"  assessment_status:     {sa['assessment_status']}")
        print(f"  compliant_count:       {sa['compliant_count']}")
        print(f"  warning_count:         {sa['warning_count']}")
        print(f"  blocker_count:         {sa['blocker_count']}")
        print(f"  execution_allowed:     {sa['execution_allowed']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  invariant_count:       {ss['invariant_count']}")
        print(f"  assessment_status:     {ss['assessment_status']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['may'])}")
        print(f"  May not:           {', '.join(gb['may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review req'd:{gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_runtime_safety_invariants(args: argparse.Namespace) -> int:
    data = build_runtime_safety_invariants()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["safety_overview"]
        print("Runtime safety invariant framework")
        print(f"Assessment: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Invariant domains:     {ov['invariant_domain_count']}")
        print(f"Runtimes assessed:     {ov['runtime_count']}")
        print(f"Invariants audited:    {ov['invariant_count']}")
        print(f"Compliant:             {ov['compliant_count']}")
        print(f"Warnings:              {ov['warning_count']}")
        print(f"Blockers:              {ov['blocker_count']}")
        print(f"Assessment status:     {ov['assessment_status']}")
        print(f"Execution allowed:     {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        im = data["invariant_model"]
        print(f"Invariant model: {im['model_name']} ({im['field_count']} fields)")
        print(f"  Supported statuses: {', '.join(im['supported_invariant_statuses'])}")
        print(f"  execution_allowed always False in 49L: {im['execution_allowed_always_false_in_49l']}")
        print()
        am = data["assessment_model"]
        print(f"Assessment model: {am['model_name']} ({am['field_count']} fields)")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Invariant results:")
        for r in data["invariant_results"]:
            warn_tag = f" [{len(r['warnings'])} warning(s)]" if r["warnings"] else ""
            print(
                f"  [{r['invariant_status'].upper()}]{warn_tag} "
                f"{r['invariant_name']} "
                f"[runtime={r['runtime_id']}] ({r['invariant_domain']})"
            )
        print()
        sa = data["sample_assessment"]
        print("Sample assessment:")
        print(f"  assessment_status:     {sa['assessment_status']}")
        print(f"  compliant_count:       {sa['compliant_count']}")
        print(f"  warning_count:         {sa['warning_count']}")
        print(f"  blocker_count:         {sa['blocker_count']}")
        print(f"  execution_allowed:     {sa['execution_allowed']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  runtime_count:         {ss['runtime_count']}")
        print(f"  invariant_count:       {ss['invariant_count']}")
        print(f"  assessment_status:     {ss['assessment_status']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['may'])}")
        print(f"  May not:           {', '.join(gb['may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review req'd:{gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_governance_drift(args: argparse.Namespace) -> int:
    data = build_governance_drift()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["drift_overview"]
        print("Governance drift detection")
        print(f"Assessment: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Drift domains:         {ov['drift_domain_count']}")
        print(f"Drift signals:         {ov['drift_count']}")
        print(f"Blockers:              {ov['blocker_count']}")
        print(f"Warnings:              {ov['warning_count']}")
        print(f"Assessment status:     {ov['assessment_status']}")
        print(f"Repair recommended:    {'yes' if ov['repair_recommended'] else 'no'}")
        print(f"Execution allowed:     {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        sm = data["signal_model"]
        print(f"Signal model: {sm['model_name']} ({sm['field_count']} fields)")
        print(f"  Supported severities: {', '.join(sm['supported_severity_values'])}")
        print(f"  execution_allowed always False in 49M: {sm['execution_allowed_always_false_in_49m']}")
        print()
        am = data["assessment_model"]
        print(f"Assessment model: {am['model_name']} ({am['field_count']} fields)")
        print()
        summ = data["summary_model"]
        print(f"Summary model: {summ['model_name']} ({summ['field_count']} fields)")
        print()
        print("Drift signals:")
        for s in data["drift_signals"]:
            print(
                f"  [{s['severity'].upper()}] {s['drift_type']} "
                f"({s['drift_domain']})"
            )
        print()
        sa = data["sample_assessment"]
        print("Sample assessment:")
        print(f"  assessment_status:     {sa['assessment_status']}")
        print(f"  drift_count:           {sa['drift_count']}")
        print(f"  blocker_count:         {sa['blocker_count']}")
        print(f"  warning_count:         {sa['warning_count']}")
        print(f"  repair_recommended:    {sa['repair_recommended']}")
        print(f"  execution_allowed:     {sa['execution_allowed']}")
        print()
        ss2 = data["sample_summary"]
        print("Sample summary:")
        print(f"  drift_count:           {ss2['drift_count']}")
        print(f"  assessment_status:     {ss2['assessment_status']}")
        print(f"  human_review_required: {ss2['human_review_required']}")
        print()
        gb2 = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb2['may'])}")
        print(f"  May not:           {', '.join(gb2['may_not'])}")
        print(f"  Execution allowed: {gb2['execution_allowed']}")
        print(f"  Human review req'd:{gb2['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_governance_drift_review(args: argparse.Namespace) -> int:
    data = build_governance_drift_review()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["review_overview"]
        print("Governance drift review workflow")
        print(f"Review: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Review domains:        {ov['review_domain_count']}")
        print(f"Review status:         {ov['review_status']}")
        print(f"Repair allowed:        {'yes' if ov['repair_allowed'] else 'no'}")
        print(f"Execution allowed:     {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses: {', '.join(cm['supported_review_statuses'])}")
        print(f"  repair_allowed always False in 49N: {cm['repair_allowed_always_false_in_49n']}")
        print()
        rm = data["record_model"]
        print(f"Record model: {rm['model_name']} ({rm['field_count']} fields)")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Review domains:")
        for d in data["review_domains"]:
            print(f"  [{d['review_status'].upper()}] {d['domain']}")
            print(f"    {d['description']}")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  review_status:         {sc['review_status'] if 'review_status' in sc else 'pending_human_review'}")
        print(f"  drift_count:           {sc['drift_count']}")
        print(f"  blocker_count:         {sc['blocker_count']}")
        print(f"  warning_count:         {sc['warning_count']}")
        print(f"  repair_recommended:    {sc['repair_recommended']}")
        print(f"  review_allowed:        {sc['review_allowed']}")
        print(f"  human_review_required: {sc['human_review_required']}")
        print()
        sr = data["sample_record"]
        print("Sample record:")
        print(f"  review_status:     {sr['review_status']}")
        print(f"  repair_allowed:    {sr['repair_allowed']}")
        print(f"  human_review_required: {sr['human_review_required']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  review_status:     {ss['review_status']}")
        print(f"  repair_allowed:    {ss['repair_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['may'])}")
        print(f"  May not:           {', '.join(gb['may_not'])}")
        print(f"  Repair allowed:    {gb['repair_allowed']}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review req'd:{gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_agent_lock_governance(args: argparse.Namespace) -> int:
    data = build_agent_lock_governance()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["lock_overview"]
        print("Agent lock governance")
        print(f"Assessment: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Governance domains:    {ov['governance_domain_count']}")
        print(f"Locks inspected:       {ov['lock_count']}")
        print(f"Stale locks:           {ov['stale_lock_count']}")
        print(f"Conflicts:             {ov['conflict_count']}")
        print(f"Blockers:              {ov['blocker_count']}")
        print(f"Warnings:              {ov['warning_count']}")
        print(f"Assessment status:     {ov['assessment_status']}")
        print(f"Repair recommended:    {'yes' if ov['repair_recommended'] else 'no'}")
        print(f"Execution allowed:     {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses: {', '.join(cm['supported_lock_statuses'])}")
        print(f"  execution_allowed always False in 49O: {cm['execution_allowed_always_false_in_49o']}")
        print()
        am = data["assessment_model"]
        print(f"Assessment model: {am['model_name']} ({am['field_count']} fields)")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Lock candidates:")
        for c in data["lock_candidates"]:
            stale_tag = " [STALE]" if c["stale"] else ""
            print(
                f"  [{c['lock_status'].upper()}]{stale_tag} "
                f"{c['agent_id']} → {c['task_id']}"
            )
        print()
        print("Domain findings:")
        for d in data["domain_findings"]:
            print(f"  [{d['severity'].upper()}] {d['domain']} ({d['lock_status']})")
        print()
        sa = data["sample_assessment"]
        print("Sample assessment:")
        print(f"  assessment_status:     {sa['assessment_status']}")
        print(f"  lock_count:            {sa['lock_count']}")
        print(f"  stale_lock_count:      {sa['stale_lock_count']}")
        print(f"  conflict_count:        {sa['conflict_count']}")
        print(f"  blocker_count:         {sa['blocker_count']}")
        print(f"  warning_count:         {sa['warning_count']}")
        print(f"  repair_recommended:    {sa['repair_recommended']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  assessment_status:     {ss['assessment_status']}")
        print(f"  stale_lock_count:      {ss['stale_lock_count']}")
        print(f"  conflict_count:        {ss['conflict_count']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['may'])}")
        print(f"  May not:           {', '.join(gb['may_not'])}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review req'd:{gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_agent_lock_conflicts(args: argparse.Namespace) -> int:
    data = build_agent_lock_conflicts()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["conflict_overview"]
        print("Multi-agent lock conflict governance")
        print(f"Assessment: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Conflict domains:      {ov['conflict_domain_count']}")
        print(f"Conflicts detected:    {ov['conflict_count']}")
        print(f"Blockers:              {ov['blocker_count']}")
        print(f"Warnings:              {ov['warning_count']}")
        print(f"Conflict status:       {ov['conflict_status']}")
        print(f"Repair recommended:    {'yes' if ov['repair_recommended'] else 'no'}")
        print(f"Execution allowed:     {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses:  {', '.join(cm['supported_conflict_statuses'])}")
        print(f"  Supported severities:{', '.join(cm['supported_severity_values'])}")
        print(f"  execution_allowed always False in 49P: {cm['execution_allowed_always_false_in_49p']}")
        print()
        am = data["assessment_model"]
        print(f"Assessment model: {am['model_name']} ({am['field_count']} fields)")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Conflict candidates:")
        for c in data["conflict_candidates"]:
            print(
                f"  [{c['severity'].upper()}] {c['conflict_type']} "
                f"agents={c['involved_agents']}"
            )
        print()
        print("Domain findings:")
        for d in data["domain_findings"]:
            print(f"  [{d['severity'].upper()}] {d['domain']} ({d['conflict_status']})")
        print()
        sa = data["sample_assessment"]
        print("Sample assessment:")
        print(f"  conflict_status:       {sa['conflict_status']}")
        print(f"  conflict_count:        {sa['conflict_count']}")
        print(f"  blocker_count:         {sa['blocker_count']}")
        print(f"  warning_count:         {sa['warning_count']}")
        print(f"  repair_recommended:    {sa['repair_recommended']}")
        print(f"  execution_allowed:     {sa['execution_allowed']}")
        print()
        ss2 = data["sample_summary"]
        print("Sample summary:")
        print(f"  conflict_status:       {ss2['conflict_status']}")
        print(f"  conflict_count:        {ss2['conflict_count']}")
        print(f"  human_review_required: {ss2['human_review_required']}")
        print()
        gb2 = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb2['may'])}")
        print(f"  May not:           {', '.join(gb2['may_not'])}")
        print(f"  Execution allowed: {gb2['execution_allowed']}")
        print(f"  Human review req'd:{gb2['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_governance_recovery_plan(args: argparse.Namespace) -> int:
    data = build_governance_recovery_plan()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["recovery_overview"]
        print("Governance recovery planning")
        print(f"Plan: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Recovery domains:      {ov['recovery_domain_count']}")
        print(f"Recovery candidates:   {ov['candidate_count']}")
        print(f"Blockers:              {ov['blocker_count']}")
        print(f"Warnings:              {ov['warning_count']}")
        print(f"Plan status:           {ov['plan_status']}")
        print(f"Recovery allowed:      {'yes' if ov['recovery_allowed'] else 'no'}")
        print(f"Execution allowed:     {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:    {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported severities: {', '.join(cm['supported_severity_values'])}")
        print(f"  recovery_allowed always False in 49Q: {cm['recovery_allowed_always_false_in_49q']}")
        print()
        pm = data["plan_model"]
        print(f"Plan model: {pm['model_name']} ({pm['field_count']} fields)")
        print(f"  Supported plan statuses: {', '.join(pm['supported_plan_statuses'])}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Recovery candidates:")
        for c in data["recovery_candidates"]:
            print(f"  [{c['severity'].upper()}] {c['recovery_domain']}")
            print(f"    Issue:  {c['source_issue'][:80]}...")
            print(f"    Action: {c['recommended_action'][:80]}...")
        print()
        sp = data["sample_plan"]
        print("Sample plan:")
        print(f"  plan_status:           {sp['plan_status']}")
        print(f"  candidate_count:       {sp['candidate_count']}")
        print(f"  blocker_count:         {sp['blocker_count']}")
        print(f"  warning_count:         {sp['warning_count']}")
        print(f"  recovery_allowed:      {sp['recovery_allowed']}")
        print(f"  human_review_required: {sp['human_review_required']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  plan_status:           {ss['plan_status']}")
        print(f"  candidate_count:       {ss['candidate_count']}")
        print(f"  recovery_allowed:      {ss['recovery_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:               {', '.join(gb['may'])}")
        print(f"  May not:           {', '.join(gb['may_not'])}")
        print(f"  Recovery allowed:  {gb['recovery_allowed']}")
        print(f"  Execution allowed: {gb['execution_allowed']}")
        print(f"  Human review req'd:{gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_authorization(args: argparse.Namespace) -> int:
    data = build_write_authorization()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["write_authorization_overview"]
        print("Controlled write authorization")
        print(f"Authorization: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Authorization domains:  {ov['authorization_domain_count']}")
        print(f"Domains assessed:       {ov['domain_count']}")
        print(f"Blockers:               {ov['blocker_count']}")
        print(f"Warnings:               {ov['warning_count']}")
        print(f"Authorization status:   {ov['authorization_status']}")
        print(f"Authorization allowed:  {'yes' if ov['authorization_allowed'] else 'no'}")
        print(f"Execution allowed:      {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:     {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses:  {', '.join(cm['supported_authorization_statuses'])}")
        print(f"  authorization_allowed always False in 50A: {cm['authorization_allowed_always_false_in_50a']}")
        print()
        pm = data["policy_model"]
        print(f"Policy model: {pm['model_name']} ({pm['field_count']} fields)")
        print(f"  automatic_approval_allowed always False in 50A: {pm['automatic_approval_allowed_always_false_in_50a']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Domain assessments:")
        for d in data["domain_assessments"]:
            print(f"  [{d['severity'].upper()}] {d['domain']}")
            print(f"    {d['finding'][:80]}...")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  authorization_allowed: {sc['authorization_allowed']}")
        print(f"  human_review_required: {sc['human_review_required']}")
        print(f"  selected_runtime:      {sc['selected_runtime']}")
        print(f"  selected_agent:        {sc['selected_agent']}")
        print()
        sp = data["sample_policy"]
        print("Sample policy:")
        print(f"  human_approval_required:    {sp['human_approval_required']}")
        print(f"  automatic_approval_allowed: {sp['automatic_approval_allowed']}")
        print(f"  expiration_required:        {sp['expiration_required']}")
        print(f"  revocation_supported:       {sp['revocation_supported']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  authorization_status:  {ss['authorization_status']}")
        print(f"  domain_count:          {ss['domain_count']}")
        print(f"  blocker_count:         {ss['blocker_count']}")
        print(f"  warning_count:         {ss['warning_count']}")
        print(f"  authorization_allowed: {ss['authorization_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['may'])}")
        print(f"  May not:               {', '.join(gb['may_not'])}")
        print(f"  Authorization allowed: {gb['authorization_allowed']}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  Human review req'd:    {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_authorization_review(args: argparse.Namespace) -> int:
    data = build_write_authorization_review()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["write_authorization_review_overview"]
        print("Write authorization review workflow")
        print(f"Review: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Review domains:         {ov['review_domain_count']}")
        print(f"Domains defined:        {ov['domain_count']}")
        print(f"Review status:          {ov['review_status']}")
        print(f"Authorization allowed:  {'yes' if ov['authorization_allowed'] else 'no'}")
        print(f"Execution allowed:      {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:     {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses:  {', '.join(cm['supported_review_statuses'])}")
        print(f"  authorization_allowed always False in 50B: {cm['authorization_allowed_always_false_in_50b']}")
        print()
        rm = data["record_model"]
        print(f"Record model: {rm['model_name']} ({rm['field_count']} fields)")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print()
        print("Domain findings:")
        for d in data["domain_findings"]:
            print(f"  [{d['review_status'].upper()}] {d['domain']}")
            print(f"    {d['description'][:80]}...")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  review_allowed:        {sc['review_allowed']}")
        print(f"  human_review_required: {sc['human_review_required']}")
        print(f"  selected_runtime:      {sc['selected_runtime']}")
        print(f"  selected_agent:        {sc['selected_agent']}")
        print()
        sr = data["sample_record"]
        print("Sample record:")
        print(f"  review_status:         {sr['review_status']}")
        print(f"  authorization_allowed: {sr['authorization_allowed']}")
        print(f"  human_review_required: {sr['human_review_required']}")
        print(f"  reviewed_domains:      {sr['reviewed_domains']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  review_status:         {ss['review_status']}")
        print(f"  domain_count:          {ss['domain_count']}")
        print(f"  requested_change_count:{ss['requested_change_count']}")
        print(f"  escalation_count:      {ss['escalation_count']}")
        print(f"  authorization_allowed: {ss['authorization_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['may'])}")
        print(f"  May not:               {', '.join(gb['may_not'])}")
        print(f"  Authorization allowed: {gb['authorization_allowed']}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  Human review req'd:    {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_authorization_decision(args: argparse.Namespace) -> int:
    data = build_write_authorization_decision()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["write_authorization_decision_overview"]
        print("Write authorization decision record")
        print(f"Decision: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Decision domains:       {ov['decision_domain_count']}")
        print(f"Domains defined:        {ov['domain_count']}")
        print(f"Decision status:        {ov['decision_status']}")
        print(f"Authorization allowed:  {'yes' if ov['authorization_allowed'] else 'no'}")
        print(f"Execution allowed:      {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:     {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses:  {', '.join(cm['supported_decision_statuses'])}")
        print(f"  authorization_allowed always False in 50C: {cm['authorization_allowed_always_false_in_50c']}")
        print()
        rm = data["record_model"]
        print(f"Record model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  authorization_allowed always False in 50C: {rm['authorization_allowed_always_false_in_50c']}")
        print(f"  execution_allowed always False in 50C:     {rm['execution_allowed_always_false_in_50c']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print(f"  authorization_allowed always False in 50C: {sm['authorization_allowed_always_false_in_50c']}")
        print(f"  execution_allowed always False in 50C:     {sm['execution_allowed_always_false_in_50c']}")
        print()
        print("Domain findings:")
        for d in data["domain_findings"]:
            print(f"  [{d['decision_status'].upper()}] {d['domain']}")
            print(f"    {d['description'][:80]}...")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  decision_allowed:      {sc['decision_allowed']}")
        print(f"  human_review_required: {sc['human_review_required']}")
        print(f"  selected_runtime:      {sc['selected_runtime']}")
        print(f"  selected_agent:        {sc['selected_agent']}")
        print()
        sr = data["sample_record"]
        print("Sample record:")
        print(f"  decision_status:       {sr['decision_status']}")
        print(f"  authorization_allowed: {sr['authorization_allowed']}")
        print(f"  execution_allowed:     {sr['execution_allowed']}")
        print(f"  human_review_required: {sr['human_review_required']}")
        print(f"  accepted_domains:      {sr['accepted_domains']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  decision_status:       {ss['decision_status']}")
        print(f"  domain_count:          {ss['domain_count']}")
        print(f"  accepted_count:        {ss['accepted_count']}")
        print(f"  rejected_count:        {ss['rejected_count']}")
        print(f"  requested_change_count:{ss['requested_change_count']}")
        print(f"  escalation_count:      {ss['escalation_count']}")
        print(f"  authorization_allowed: {ss['authorization_allowed']}")
        print(f"  execution_allowed:     {ss['execution_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['may'])}")
        print(f"  May not:               {', '.join(gb['may_not'])}")
        print(f"  Authorization allowed: {gb['authorization_allowed']}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  Human review req'd:    {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_authorization_lifecycle(args: argparse.Namespace) -> int:
    data = build_write_authorization_lifecycle()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["write_authorization_lifecycle_overview"]
        print("Write authorization lifecycle policy")
        print(f"Lifecycle: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Lifecycle domains:      {ov['lifecycle_domain_count']}")
        print(f"Domains defined:        {ov['domain_count']}")
        print(f"Lifecycle status:       {ov['lifecycle_status']}")
        print(f"Authorization allowed:  {'yes' if ov['authorization_allowed'] else 'no'}")
        print(f"Execution allowed:      {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:     {'yes' if ov['human_review_required'] else 'no'}")
        print(f"Automatic renewal:      {'yes' if ov['automatic_renewal_allowed'] else 'no'}")
        print()
        pm = data["policy_model"]
        print(f"Policy model: {pm['model_name']} ({pm['field_count']} fields)")
        print(f"  Supported statuses:  {', '.join(pm['supported_lifecycle_statuses'])}")
        print(f"  automatic_renewal_allowed always False in 50D: {pm['automatic_renewal_allowed_always_false_in_50d']}")
        print(f"  authorization_allowed always False in 50D:     {pm['authorization_allowed_always_false_in_50d']}")
        print()
        rm = data["record_model"]
        print(f"Record model: {rm['model_name']} ({rm['field_count']} fields)")
        print(f"  authorization_allowed always False in 50D: {rm['authorization_allowed_always_false_in_50d']}")
        print(f"  execution_allowed always False in 50D:     {rm['execution_allowed_always_false_in_50d']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print(f"  authorization_allowed always False in 50D: {sm['authorization_allowed_always_false_in_50d']}")
        print(f"  execution_allowed always False in 50D:     {sm['execution_allowed_always_false_in_50d']}")
        print()
        print("Domain findings:")
        for d in data["domain_findings"]:
            print(f"  [{d['lifecycle_status'].upper()}] {d['domain']}")
            print(f"    {d['description'][:80]}...")
        print()
        sp = data["sample_policy"]
        print("Sample policy:")
        print(f"  expiration_required:      {sp['expiration_required']}")
        print(f"  revocation_supported:     {sp['revocation_supported']}")
        print(f"  renewal_supported:        {sp['renewal_supported']}")
        print(f"  supersession_supported:   {sp['supersession_supported']}")
        print(f"  human_reapproval_required:{sp['human_reapproval_required']}")
        print(f"  automatic_renewal_allowed:{sp['automatic_renewal_allowed']}")
        print()
        sr = data["sample_record"]
        print("Sample record:")
        print(f"  current_status:        {sr['current_status']}")
        print(f"  authorization_allowed: {sr['authorization_allowed']}")
        print(f"  execution_allowed:     {sr['execution_allowed']}")
        print(f"  human_review_required: {sr['human_review_required']}")
        print(f"  blockers:              {sr['blockers']}")
        print(f"  warnings:              {sr['warnings']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  current_status:        {ss['current_status']}")
        print(f"  blocker_count:         {ss['blocker_count']}")
        print(f"  warning_count:         {ss['warning_count']}")
        print(f"  authorization_allowed: {ss['authorization_allowed']}")
        print(f"  execution_allowed:     {ss['execution_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['may'])}")
        print(f"  May not:               {', '.join(gb['may_not'])}")
        print(f"  Authorization allowed: {gb['authorization_allowed']}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  Automatic renewal:     {gb['automatic_renewal_allowed']}")
        print(f"  Human review req'd:    {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_plan(args: argparse.Namespace) -> int:
    data = build_write_plan()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["write_plan_overview"]
        print("Controlled write planning")
        print(f"Plan: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Planning domains:       {ov['planning_domain_count']}")
        print(f"Domains assessed:       {ov['domain_count']}")
        print(f"Blockers:               {ov['blocker_count']}")
        print(f"Warnings:               {ov['warning_count']}")
        print(f"Plan status:            {ov['plan_status']}")
        print(f"Plan allowed:           {'yes' if ov['plan_allowed'] else 'no'}")
        print(f"Execution allowed:      {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:     {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses:  {', '.join(cm['supported_plan_statuses'])}")
        print(f"  plan_allowed always False in 50E: {cm['plan_allowed_always_false_in_50e']}")
        print()
        pm = data["policy_model"]
        print(f"Policy model: {pm['model_name']} ({pm['field_count']} fields)")
        print(f"  automatic_plan_approval_allowed always False in 50E: {pm['automatic_plan_approval_allowed_always_false_in_50e']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print(f"  plan_allowed always False in 50E:      {sm['plan_allowed_always_false_in_50e']}")
        print(f"  execution_allowed always False in 50E: {sm['execution_allowed_always_false_in_50e']}")
        print()
        print("Domain assessments:")
        for d in data["domain_assessments"]:
            print(f"  [{d['severity'].upper()}] {d['domain']}")
            print(f"    {d['finding'][:80]}...")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  plan_allowed:          {sc['plan_allowed']}")
        print(f"  human_review_required: {sc['human_review_required']}")
        print(f"  selected_runtime:      {sc['selected_runtime']}")
        print(f"  selected_agent:        {sc['selected_agent']}")
        print(f"  file_scope:            {sc['file_scope']}")
        print()
        sp = data["sample_policy"]
        print("Sample policy:")
        print(f"  human_approval_required:          {sp['human_approval_required']}")
        print(f"  automatic_plan_approval_allowed:  {sp['automatic_plan_approval_allowed']}")
        print(f"  file_scope_required:              {sp['file_scope_required']}")
        print(f"  rollback_required:                {sp['rollback_required']}")
        print(f"  audit_required:                   {sp['audit_required']}")
        print(f"  evidence_required:                {sp['evidence_required']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  plan_status:           {ss['plan_status']}")
        print(f"  domain_count:          {ss['domain_count']}")
        print(f"  blocker_count:         {ss['blocker_count']}")
        print(f"  warning_count:         {ss['warning_count']}")
        print(f"  plan_allowed:          {ss['plan_allowed']}")
        print(f"  execution_allowed:     {ss['execution_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['may'])}")
        print(f"  May not:               {', '.join(gb['may_not'])}")
        print(f"  Plan allowed:          {gb['plan_allowed']}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  Human review req'd:    {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_readiness(args: argparse.Namespace) -> int:
    data = build_write_readiness()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["write_readiness_overview"]
        print("Controlled write readiness assessment")
        print(f"Readiness: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Readiness domains:      {ov['readiness_domain_count']}")
        print(f"Domains assessed:       {ov['domain_count']}")
        print(f"Compliant:              {ov['compliant_count']}")
        print(f"Blockers:               {ov['blocker_count']}")
        print(f"Warnings:               {ov['warning_count']}")
        print(f"Readiness status:       {ov['readiness_status']}")
        print(f"Readiness allowed:      {'yes' if ov['readiness_allowed'] else 'no'}")
        print(f"Execution allowed:      {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:     {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses:  {', '.join(cm['supported_readiness_statuses'])}")
        print(f"  readiness_allowed always False in 50F: {cm['readiness_allowed_always_false_in_50f']}")
        print()
        am = data["assessment_model"]
        print(f"Assessment model: {am['model_name']} ({am['field_count']} fields)")
        print(f"  readiness_allowed always False in 50F: {am['readiness_allowed_always_false_in_50f']}")
        print(f"  execution_allowed always False in 50F: {am['execution_allowed_always_false_in_50f']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print(f"  readiness_allowed always False in 50F: {sm['readiness_allowed_always_false_in_50f']}")
        print(f"  execution_allowed always False in 50F: {sm['execution_allowed_always_false_in_50f']}")
        print()
        print("Domain assessments:")
        for d in data["domain_assessments"]:
            print(f"  [{d['severity'].upper()}] {d['domain']}")
            print(f"    {d['finding'][:80]}...")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  readiness_allowed:     {sc['readiness_allowed']}")
        print(f"  human_review_required: {sc['human_review_required']}")
        print(f"  selected_runtime:      {sc['selected_runtime']}")
        print(f"  selected_agent:        {sc['selected_agent']}")
        print()
        sa = data["sample_assessment"]
        print("Sample assessment:")
        print(f"  readiness_status:      {sa['readiness_status']}")
        print(f"  domain_count:          {sa['domain_count']}")
        print(f"  compliant_count:       {sa['compliant_count']}")
        print(f"  blocker_count:         {sa['blocker_count']}")
        print(f"  warning_count:         {sa['warning_count']}")
        print(f"  readiness_allowed:     {sa['readiness_allowed']}")
        print(f"  execution_allowed:     {sa['execution_allowed']}")
        print(f"  human_review_required: {sa['human_review_required']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  readiness_status:      {ss['readiness_status']}")
        print(f"  domain_count:          {ss['domain_count']}")
        print(f"  compliant_count:       {ss['compliant_count']}")
        print(f"  blocker_count:         {ss['blocker_count']}")
        print(f"  warning_count:         {ss['warning_count']}")
        print(f"  readiness_allowed:     {ss['readiness_allowed']}")
        print(f"  execution_allowed:     {ss['execution_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['may'])}")
        print(f"  May not:               {', '.join(gb['may_not'])}")
        print(f"  Readiness allowed:     {gb['readiness_allowed']}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  Human review req'd:    {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_evidence(args: argparse.Namespace) -> int:
    data = build_write_evidence()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["write_evidence_overview"]
        print("Controlled write evidence requirements")
        print(f"Evidence: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Evidence domains:       {ov['evidence_domain_count']}")
        print(f"Domains assessed:       {ov['domain_count']}")
        print(f"Compliant:              {ov['compliant_count']}")
        print(f"Blockers:               {ov['blocker_count']}")
        print(f"Warnings:               {ov['warning_count']}")
        print(f"Evidence status:        {ov['evidence_status']}")
        print(f"Evidence complete:      {'yes' if ov['evidence_complete'] else 'no'}")
        print(f"Execution allowed:      {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:     {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses:  {', '.join(cm['supported_evidence_statuses'])}")
        print(f"  evidence_complete always False in 50G: {cm['evidence_complete_always_false_in_50g']}")
        print()
        am = data["assessment_model"]
        print(f"Assessment model: {am['model_name']} ({am['field_count']} fields)")
        print(f"  evidence_complete always False in 50G: {am['evidence_complete_always_false_in_50g']}")
        print(f"  execution_allowed always False in 50G: {am['execution_allowed_always_false_in_50g']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print(f"  evidence_complete always False in 50G: {sm['evidence_complete_always_false_in_50g']}")
        print(f"  execution_allowed always False in 50G: {sm['execution_allowed_always_false_in_50g']}")
        print()
        print("Domain assessments:")
        for d in data["domain_assessments"]:
            print(f"  [{d['severity'].upper()}] {d['domain']}")
            print(f"    {d['finding'][:80]}...")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  evidence_complete:     {sc['evidence_complete']}")
        print(f"  human_review_required: {sc['human_review_required']}")
        print(f"  evidence_count:        {sc['evidence_count']}")
        print()
        sa = data["sample_assessment"]
        print("Sample assessment:")
        print(f"  evidence_status:       {sa['evidence_status']}")
        print(f"  domain_count:          {sa['domain_count']}")
        print(f"  compliant_count:       {sa['compliant_count']}")
        print(f"  blocker_count:         {sa['blocker_count']}")
        print(f"  warning_count:         {sa['warning_count']}")
        print(f"  evidence_complete:     {sa['evidence_complete']}")
        print(f"  execution_allowed:     {sa['execution_allowed']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  evidence_status:       {ss['evidence_status']}")
        print(f"  domain_count:          {ss['domain_count']}")
        print(f"  compliant_count:       {ss['compliant_count']}")
        print(f"  blocker_count:         {ss['blocker_count']}")
        print(f"  warning_count:         {ss['warning_count']}")
        print(f"  evidence_complete:     {ss['evidence_complete']}")
        print(f"  execution_allowed:     {ss['execution_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['may'])}")
        print(f"  May not:               {', '.join(gb['may_not'])}")
        print(f"  Evidence complete:     {gb['evidence_complete']}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  Human review req'd:    {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0


def run_write_audit(args: argparse.Namespace) -> int:
    data = build_write_audit()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        ov = data["write_audit_overview"]
        print("Controlled write audit requirements")
        print(f"Audit: {ov['overview_id']}  Generated: {ov['generated_at']}")
        print(f"Phase: {ov['phase']} — {ov['title']}")
        print()
        print(ov["summary"])
        print()
        print(f"Audit domains:          {ov['audit_domain_count']}")
        print(f"Domains assessed:       {ov['domain_count']}")
        print(f"Compliant:              {ov['compliant_count']}")
        print(f"Blockers:               {ov['blocker_count']}")
        print(f"Warnings:               {ov['warning_count']}")
        print(f"Audit status:           {ov['audit_status']}")
        print(f"Audit complete:         {'yes' if ov['audit_complete'] else 'no'}")
        print(f"Execution allowed:      {'yes' if ov['execution_allowed'] else 'no'}")
        print(f"Human review req'd:     {'yes' if ov['human_review_required'] else 'no'}")
        print()
        cm = data["candidate_model"]
        print(f"Candidate model: {cm['model_name']} ({cm['field_count']} fields)")
        print(f"  Supported statuses:  {', '.join(cm['supported_audit_statuses'])}")
        print(f"  audit_complete always False in 50H: {cm['audit_complete_always_false_in_50h']}")
        print()
        am = data["assessment_model"]
        print(f"Assessment model: {am['model_name']} ({am['field_count']} fields)")
        print(f"  audit_complete always False in 50H:    {am['audit_complete_always_false_in_50h']}")
        print(f"  execution_allowed always False in 50H: {am['execution_allowed_always_false_in_50h']}")
        print()
        sm = data["summary_model"]
        print(f"Summary model: {sm['model_name']} ({sm['field_count']} fields)")
        print(f"  audit_complete always False in 50H:    {sm['audit_complete_always_false_in_50h']}")
        print(f"  execution_allowed always False in 50H: {sm['execution_allowed_always_false_in_50h']}")
        print()
        print("Domain assessments:")
        for d in data["domain_assessments"]:
            print(f"  [{d['severity'].upper()}] {d['domain']}")
            print(f"    {d['finding'][:80]}...")
        print()
        sc = data["sample_candidate"]
        print("Sample candidate:")
        print(f"  audit_complete:        {sc['audit_complete']}")
        print(f"  human_review_required: {sc['human_review_required']}")
        print(f"  audit_count:           {sc['audit_count']}")
        print()
        sa = data["sample_assessment"]
        print("Sample assessment:")
        print(f"  audit_status:          {sa['audit_status']}")
        print(f"  domain_count:          {sa['domain_count']}")
        print(f"  compliant_count:       {sa['compliant_count']}")
        print(f"  blocker_count:         {sa['blocker_count']}")
        print(f"  warning_count:         {sa['warning_count']}")
        print(f"  audit_complete:        {sa['audit_complete']}")
        print(f"  execution_allowed:     {sa['execution_allowed']}")
        print()
        ss = data["sample_summary"]
        print("Sample summary:")
        print(f"  audit_status:          {ss['audit_status']}")
        print(f"  domain_count:          {ss['domain_count']}")
        print(f"  compliant_count:       {ss['compliant_count']}")
        print(f"  blocker_count:         {ss['blocker_count']}")
        print(f"  warning_count:         {ss['warning_count']}")
        print(f"  audit_complete:        {ss['audit_complete']}")
        print(f"  execution_allowed:     {ss['execution_allowed']}")
        print(f"  human_review_required: {ss['human_review_required']}")
        print()
        gb = data["governance_boundaries"]
        print("Governance boundaries:")
        print(f"  May:                   {', '.join(gb['may'])}")
        print(f"  May not:               {', '.join(gb['may_not'])}")
        print(f"  Audit complete:        {gb['audit_complete']}")
        print(f"  Execution allowed:     {gb['execution_allowed']}")
        print(f"  Human review req'd:    {gb['human_review_required']}")
        print()
        print(data["advisory"])
    return 0
