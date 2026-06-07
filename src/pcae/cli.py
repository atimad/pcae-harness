from __future__ import annotations

import argparse
from collections.abc import Sequence

from pcae.commands.analytics import run_analytics_risk, run_analytics_trends
from pcae.commands.agent import (
    run_agent_acquire,
    run_agent_release,
    run_agent_status,
    run_agents,
    run_agents_adapter_inspect,
    run_agents_adapter_show,
    run_agents_adapters,
    run_agents_config_show,
    run_agents_config_validate,
    run_agents_lifecycle,
    run_agents_runtime_discover,
    run_agents_show,
    run_agents_validate,
    run_collaboration_design,
    run_consensus_design,
    run_coordinator_design,
    run_orchestration_design,
    run_parallel_execution_design,
    run_adapter_design,
    run_execution_framework_design,
    run_invocation_design,
    run_real_planning_design,
    run_consensus_execution_design,
    run_runtime_execution_prototype,
    run_planner_adapter_prototype,
    run_multi_agent_prototype,
    run_consensus_prototype,
    run_invocation_pilot,
    run_multi_runtime_pilot,
    run_consensus_runtime_pilot,
    run_governed_execution_dry_run,
    run_invocation_contracts,
    run_execution_readiness,
    run_adapter_registry_design,
    run_roadmap_generation_design,
    run_roadmap_evidence,
    run_roadmap_proposal_dry_run,
    run_multi_agent_roadmap,
    run_roadmap_approval_design,
    run_prompt_generation_design,
    run_adaptive_prompt_design,
    run_prompt_validation_design,
    run_prompt_governance_design,
    run_prompt_artifact_design,
    run_prompt_approval_workflow,
    run_autonomous_phase_proposal,
    run_autonomous_prompt_proposal,
    run_prompt_render,
    run_prompt_execution_readiness,
    run_prompt_execution_dry_run,
    run_human_agent_execution_design,
    run_governed_execution_pilot,
    run_live_execution_readiness,
    run_execution_audit_design,
    run_execution_consensus_framework,
    run_live_execution_pilot,
    run_invocation_workload_validation,
    run_execution_authorization_design,
    run_read_only_invocation_pilot,
    run_execution_result_review_design,
    run_authorization_expiration_design,
    run_invocation_pilot_status,
    run_multi_agent_invocation_pilot,
    run_execution_quality_design,
    run_read_only_invocation_execution_pilot,
    run_write_invocation_design,
    run_write_preflight_dry_run,
    run_write_candidate_design,
    run_write_invocation_pilot,
    run_write_result_review_design,
    run_write_rollback_validation_design,
    run_write_execution_readiness,
    run_write_rollback_dry_run,
    run_live_readonly_readiness,
    run_live_write_readiness,
    run_live_readonly_pilot,
    run_rollback_execution_pilot,
    run_live_write_pilot,
    run_runtime_contracts,
    run_execution_governance_audit,
    run_runtime_trust,
    run_governance_maturity,
    run_readonly_invocation,
    run_invocation_result_capture,
    run_runtime_contract_enforcement,
    run_invocation_authorization_enforcement,
    run_invocation_audit_trail,
    run_readonly_runtime_pilot,
    run_invocation_result_review,
    run_invocation_evidence,
    run_multi_agent_readonly_pilot,
    run_consensus_engine,
    run_arbitration,
    run_evidence_framework,
    run_decision_record,
    run_multi_agent_governance_audit,
    run_governance_state_audit,
    run_governance_state_repair,
    run_task_transition_governance,
    run_session_continuity_governance,
    run_governance_invariants,
    run_runtime_safety_invariants,
    run_governance_drift,
    run_governance_drift_review,
    run_agent_lock_governance,
    run_agent_lock_conflicts,
    run_governance_recovery_plan,
    run_write_authorization,
    run_write_authorization_review,
    run_write_authorization_decision,
    run_write_authorization_lifecycle,
    run_write_plan,
    run_write_readiness,
    run_write_evidence,
    run_write_audit,
    run_write_rollback_verification,
    run_write_governance_audit,
    run_write_recommendation,
    run_execution_request,
    run_execution_review,
    run_execution_decision,
    run_execution_lifecycle,
    run_execution_plan,
    run_execution_readiness_assessment,
    run_execution_evidence,
    run_execution_audit,
    run_execution_rollback_verification,
    run_execution_chain_governance_audit,
    run_execution_recommendation,
    run_task_lifecycle_hardening,
    run_session_recovery,
    run_governance_state_recovery,
    run_agent_lock_recovery,
    run_corruption_recovery,
    run_runtime_contract_hardening,
    run_sandbox_hardening,
    run_timeout_hardening,
    run_output_integrity_verification,
    run_concurrency_safety,
    run_parallel_agent_coordination,
    run_multi_agent_state_consistency,
    run_conflict_resolution_engine,
    run_chaos_testing,
    run_failure_injection,
    run_corruption_simulation,
    run_recovery_validation,
    run_runtime_integration_readiness,
    run_read_only_runtime_invocation,
    run_runtime_output_persistence,
    run_runtime_output_review,
    run_multi_agent_read_only_execution,
    run_controlled_write_dry_run,
    run_single_file_write_pilot,
    run_runtime_registry,
    run_runtime_discovery_assessment,
    run_runtime_capability_inventory,
    run_runtime_trust_model,
    run_task_lifecycle_governance,
    run_agent_handoff_modernization,
    run_handoff_state_refresh,
    run_roadmap_continuity,
    run_planning_dry_run,
    run_planning_execution_design,
    run_planning_prototype_design,
    run_capability_registry,
    run_capability_discovery,
    run_capability_validation,
    run_collaboration_handoffs,
    run_collaboration_reviews,
    run_collaboration_workflows,
    run_remote_adapters,
    run_remote_approvals,
    run_remote_create,
    run_remote_dry_run,
    run_remote_strategy,
    run_remote_approve,
    run_remote_deny,
    run_remote_execute,
    run_remote_ready,
    run_remote_jobs,
    run_remote_jobs_list,
    run_remote_jobs_show,
    run_remote_plan,
    run_remote_policy,
    run_remote_analytics,
    run_remote_benchmark,
    run_remote_benchmark_controlled,
    run_remote_changes,
    run_remote_changes_approve,
    run_remote_changes_deny,
    run_remote_changes_show,
    run_remote_commit,
    run_remote_push,
    run_remote_rollback_approve,
    run_remote_rollback_deny,
    run_remote_rollback_execute,
    run_remote_rollback_governance,
    run_remote_rollback_push,
    run_remote_rollback_review,
    run_remote_file_governance,
    run_remote_writable_contract,
    run_remote_report_export,
    run_remote_report_inspect,
    run_remote_trends,
    run_remote_results,
    run_remote_status,
    run_remote_validate,
)
from pcae.commands.architecture import (
    run_architecture_add,
    run_architecture_decisions,
    run_architecture_export,
    run_architecture_history,
    run_architecture_metrics,
    run_architecture_restore_session,
    run_architecture_show,
    run_architecture_snapshot,
    run_architecture_validate,
)
from pcae.commands.check import run_check
from pcae.commands.context import (
    run_context_export,
    run_context_pack,
    run_continuity_compatibility,
    run_continuity_export,
    run_continuity_inspect,
    run_continuity_manifest,
    run_continuity_retention,
)
from pcae.commands.ci import (
    run_ci_drift,
    run_ci_generate_github,
    run_ci_repair,
    run_ci_status,
)
from pcae.commands.daemon import (
    default_watch_interval_seconds,
    run_daemon,
    run_daemon_status,
    run_daemon_watch,
)
from pcae.commands.docs import run_docs_architecture, run_docs_commands, run_docs_glossary
from pcae.commands.provenance import (
    run_provenance_export,
    run_provenance_history,
    run_provenance_record,
    run_provenance_session_current,
    run_provenance_sessions,
    run_provenance_status,
    run_provenance_timeline,
)
from pcae.commands.export import run_export_bundle
from pcae.commands.fleet import (
    run_fleet_add,
    run_fleet_apply,
    run_fleet_drift,
    run_fleet_export,
    run_fleet_health,
    run_fleet_inspect,
    run_fleet_list,
    run_fleet_remove,
)
from pcae.commands.health import run_health
from pcae.commands.orchestration import (
    run_orchestration_agents,
    run_orchestration_capabilities,
    run_orchestration_explain,
    run_orchestration_plan,
    run_orchestration_policy,
    run_orchestration_readiness,
    run_orchestration_recommend,
    run_orchestration_select,
    run_orchestration_simulate,
    run_orchestration_validate,
)
from pcae.commands.status import (
    run_governance_artifacts,
    run_governance_artifacts_export,
    run_governance_audit,
    run_governance_registry_audit,
    run_governance_repair,
    run_governance_sync_check,
    run_governance_sync_repair,
    run_runtime_snapshot,
    run_runtime_snapshot_compatibility,
    run_runtime_snapshot_export,
    run_runtime_snapshot_inspect,
    run_runtime_snapshot_lineage,
    run_runtime_snapshot_manifest,
    run_runtime_snapshot_retention,
    run_runtime_snapshot_restore,
    run_runtime_snapshot_validate_restore,
    run_roadmap_next,
    run_status_coherence,
)
from pcae.commands.hooks import run_hooks_install
from pcae.commands.import_ import run_import_bundle
from pcae.commands.init import run_init
from pcae.commands.inspect import run_inspect
from pcae.commands.pipeline import run_pipeline, run_pipeline_list
from pcae.commands.repo import run_repo_apply, run_repo_trial
from pcae.commands.session import (
    run_session_bootstrap,
    run_session_end,
    run_session_read,
    run_session_start,
    run_session_update,
    run_session_write,
)
from pcae.commands.phase import run_phase_complete, run_phase_handoff, run_phase_start
from pcae.commands.task import (
    run_task_close,
    run_task_complete,
    run_task_list,
    run_task_new,
    run_task_pause,
    run_task_resume,
    run_task_show,
    run_task_transition,
    run_task_update,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pcae",
        description="Persistent Constrained Agentic Engineering Harness.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="Create PCAE memory files in the current repository.",
    )
    init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview files and directories without writing them.",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite PCAE-managed template files.",
    )
    init_parser.set_defaults(handler=run_init)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect PCAE memory files and local harness wiring.",
    )
    inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON inspection output.",
    )
    inspect_parser.set_defaults(handler=run_inspect)

    check_parser = subparsers.add_parser(
        "check",
        help="Run advisory PCAE validation checks.",
    )
    check_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON check output.",
    )
    check_parser.set_defaults(handler=run_check)

    context_parser = subparsers.add_parser(
        "context",
        help="Inspect PCAE governed context for AI agents.",
    )
    context_subparsers = context_parser.add_subparsers(
        dest="context_command",
        required=True,
    )
    context_pack_parser = context_subparsers.add_parser(
        "pack",
        help="Preview a compact governed context pack for AI agents.",
    )
    context_pack_parser.add_argument(
        "--preview",
        action="store_true",
        required=True,
        help="Preview context pack contents without writing files.",
    )
    context_pack_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON context pack output.",
    )
    context_pack_parser.add_argument(
        "--profile",
        default=None,
        metavar="PROFILE",
        help=(
            "Work-mode context profile: implementation, documentation, "
            "validation, handoff. Omit for balanced universal profile."
        ),
    )
    context_pack_parser.set_defaults(handler=run_context_pack)

    context_export_parser = context_subparsers.add_parser(
        "export",
        help="Export a compact governed context pack to .pcae/context-packs/.",
    )
    context_export_parser.add_argument(
        "--profile",
        default=None,
        metavar="PROFILE",
        help=(
            "Work-mode context profile for the export: "
            "implementation, documentation, validation, handoff."
        ),
    )
    context_export_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON export result.",
    )
    context_export_parser.set_defaults(handler=run_context_export)

    continuity_parser = subparsers.add_parser(
        "continuity",
        help="Export, inspect, analyze, and index governed continuity restore packs.",
    )
    continuity_subparsers = continuity_parser.add_subparsers(
        dest="continuity_command",
        required=True,
    )
    continuity_export_parser = continuity_subparsers.add_parser(
        "export",
        help="Export a governed continuity restore pack to .pcae/continuity-packs/.",
    )
    continuity_export_parser.add_argument(
        "--profile",
        default=None,
        metavar="PROFILE",
        help=(
            "Work-mode context profile: implementation, documentation, "
            "validation, handoff. Omit for balanced universal profile."
        ),
    )
    continuity_export_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON export result.",
    )
    continuity_export_parser.set_defaults(handler=run_continuity_export)

    continuity_inspect_parser = continuity_subparsers.add_parser(
        "inspect",
        help="Inspect a governed continuity restore pack read-only.",
    )
    continuity_inspect_parser.add_argument(
        "path",
        metavar="PATH",
        help="Path to the continuity pack JSON file.",
    )
    continuity_inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON inspection result.",
    )
    continuity_inspect_parser.set_defaults(handler=run_continuity_inspect)

    continuity_compatibility_parser = continuity_subparsers.add_parser(
        "compatibility",
        help="Analyze compatibility of a governed continuity pack against the current runtime.",
    )
    continuity_compatibility_parser.add_argument(
        "path",
        metavar="PATH",
        help="Path to the continuity pack JSON file.",
    )
    continuity_compatibility_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON compatibility result.",
    )
    continuity_compatibility_parser.set_defaults(handler=run_continuity_compatibility)

    continuity_manifest_parser = continuity_subparsers.add_parser(
        "manifest",
        help="Build a deterministic index of exported continuity packs.",
    )
    continuity_manifest_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON manifest result.",
    )
    continuity_manifest_parser.set_defaults(handler=run_continuity_manifest)

    continuity_retention_parser = continuity_subparsers.add_parser(
        "retention",
        help="Preview retention actions for continuity packs without deleting anything.",
    )
    continuity_retention_parser.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="Preview retention plan without deleting any continuity packs.",
    )
    continuity_retention_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON retention plan.",
    )
    continuity_retention_parser.set_defaults(handler=run_continuity_retention)

    ci_parser = subparsers.add_parser(
        "ci",
        help="Generate CI governance templates.",
    )
    ci_subparsers = ci_parser.add_subparsers(
        dest="ci_command",
        required=True,
    )
    ci_generate_parser = ci_subparsers.add_parser(
        "generate",
        help="Generate CI governance workflow files.",
    )
    ci_generate_subparsers = ci_generate_parser.add_subparsers(
        dest="ci_generate_target",
        required=True,
    )
    ci_generate_github_parser = ci_generate_subparsers.add_parser(
        "github",
        help="Generate a GitHub Actions PCAE governance workflow.",
    )
    ci_generate_github_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the GitHub Actions workflow without writing it.",
    )
    ci_generate_github_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing GitHub Actions workflow.",
    )
    ci_generate_github_parser.set_defaults(handler=run_ci_generate_github)

    ci_status_parser = ci_subparsers.add_parser(
        "status",
        help="Inspect generated PCAE CI workflow configuration.",
    )
    ci_status_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON CI status output.",
    )
    ci_status_parser.set_defaults(handler=run_ci_status)

    ci_drift_parser = ci_subparsers.add_parser(
        "drift",
        help="Detect PCAE governance drift in the generated CI workflow.",
    )
    ci_drift_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON CI drift output.",
    )
    ci_drift_parser.set_defaults(handler=run_ci_drift)

    ci_repair_parser = ci_subparsers.add_parser(
        "repair",
        help="Preview repairing PCAE governance CI drift.",
    )
    ci_repair_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview CI repair actions without writing files.",
    )
    ci_repair_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON CI repair dry-run output.",
    )
    ci_repair_parser.add_argument(
        "--force",
        action="store_true",
        help="Apply CI repair actions by writing the generated workflow.",
    )
    ci_repair_parser.set_defaults(handler=run_ci_repair)

    docs_parser = subparsers.add_parser(
        "docs",
        help="Generate PCAE documentation artifacts.",
    )
    docs_subparsers = docs_parser.add_subparsers(
        dest="docs_command",
        required=True,
    )
    docs_commands_parser = docs_subparsers.add_parser(
        "commands",
        help="Generate the PCAE command reference.",
    )
    docs_commands_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the command reference without writing it.",
    )
    docs_commands_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing command reference.",
    )
    docs_commands_parser.set_defaults(handler=run_docs_commands)

    docs_architecture_parser = docs_subparsers.add_parser(
        "architecture",
        help="Generate the PCAE architecture overview.",
    )
    docs_architecture_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the architecture overview without writing it.",
    )
    docs_architecture_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing architecture overview.",
    )
    docs_architecture_parser.set_defaults(handler=run_docs_architecture)

    docs_glossary_parser = docs_subparsers.add_parser(
        "glossary",
        help="Generate the PCAE governance glossary.",
    )
    docs_glossary_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the glossary without writing it.",
    )
    docs_glossary_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing glossary.",
    )
    docs_glossary_parser.set_defaults(handler=run_docs_glossary)

    health_parser = subparsers.add_parser(
        "health",
        help="Summarize PCAE governance readiness.",
    )
    health_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON health output.",
    )
    health_parser.set_defaults(handler=run_health)

    status_parser = subparsers.add_parser(
        "status",
        help="Check governance status coherence.",
    )
    status_subparsers = status_parser.add_subparsers(dest="status_command", required=True)
    status_coherence_parser = status_subparsers.add_parser(
        "coherence",
        help="Check PROJECT_STATUS.md for stale roadmap references.",
    )
    status_coherence_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON coherence output.",
    )
    status_coherence_parser.set_defaults(handler=run_status_coherence)

    roadmap_parser = subparsers.add_parser(
        "roadmap",
        help="Preview governed roadmap recommendations.",
    )
    roadmap_subparsers = roadmap_parser.add_subparsers(
        dest="roadmap_command",
        required=True,
    )
    roadmap_next_parser = roadmap_subparsers.add_parser(
        "next",
        help="Recommend the next governed phase without modifying state.",
    )
    roadmap_next_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON roadmap recommendation output.",
    )
    roadmap_next_parser.set_defaults(handler=run_roadmap_next)

    governance_parser = subparsers.add_parser(
        "governance",
        help="Audit PCAE governance coherence.",
    )
    governance_subparsers = governance_parser.add_subparsers(
        dest="governance_command",
        required=True,
    )
    governance_audit_parser = governance_subparsers.add_parser(
        "audit",
        help="Run a lightweight read-only governance coherence audit.",
    )
    governance_audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON governance audit output.",
    )
    governance_audit_parser.set_defaults(handler=run_governance_audit)

    governance_repair_parser = governance_subparsers.add_parser(
        "repair",
        help="Preview deterministic governance repair recommendations.",
    )
    governance_repair_parser.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="Preview repair recommendations without modifying files.",
    )
    governance_repair_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON governance repair output.",
    )
    governance_repair_parser.set_defaults(handler=run_governance_repair)

    governance_sync_check_parser = governance_subparsers.add_parser(
        "sync-check",
        help="Detect stale or inconsistent governance artifacts read-only.",
    )
    governance_sync_check_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON synchronization check output.",
    )
    governance_sync_check_parser.set_defaults(handler=run_governance_sync_check)

    governance_sync_repair_parser = governance_subparsers.add_parser(
        "sync-repair",
        help="Preview or apply deterministic repairs for stale governance artifacts.",
    )
    governance_sync_repair_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview repair actions without modifying any governance artifacts.",
    )
    governance_sync_repair_parser.add_argument(
        "--force",
        action="store_true",
        help="Apply safe operational repairs (removes completed TODO entries only).",
    )
    governance_sync_repair_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    governance_sync_repair_parser.set_defaults(handler=run_governance_sync_repair)

    governance_artifacts_parser = governance_subparsers.add_parser(
        "artifacts",
        help="List known governance artifacts and their lifecycle semantics.",
    )
    governance_artifacts_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON governance artifact registry output.",
    )
    governance_artifacts_parser.set_defaults(handler=run_governance_artifacts)
    governance_artifacts_subparsers = governance_artifacts_parser.add_subparsers(
        dest="governance_artifacts_command",
    )
    governance_artifacts_export_parser = governance_artifacts_subparsers.add_parser(
        "export",
        help="Export the governance artifact classification registry to .pcae/governance-exports/.",
    )
    governance_artifacts_export_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON governance artifact registry export output.",
    )
    governance_artifacts_export_parser.set_defaults(handler=run_governance_artifacts_export)

    governance_registry_audit_parser = governance_subparsers.add_parser(
        "registry-audit",
        help="Audit whether key governance systems are registry-backed.",
    )
    governance_registry_audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON registry audit output.",
    )
    governance_registry_audit_parser.set_defaults(handler=run_governance_registry_audit)

    runtime_parser = subparsers.add_parser(
        "runtime",
        help="Preview PCAE governed runtime state.",
    )
    runtime_subparsers = runtime_parser.add_subparsers(
        dest="runtime_command",
        required=True,
    )
    runtime_snapshot_parser = runtime_subparsers.add_parser(
        "snapshot",
        help="Preview a portable governed runtime snapshot.",
    )
    runtime_snapshot_parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview snapshot contents without exporting files.",
    )
    runtime_snapshot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime snapshot preview output.",
    )
    runtime_snapshot_parser.set_defaults(handler=run_runtime_snapshot)
    runtime_snapshot_subparsers = runtime_snapshot_parser.add_subparsers(
        dest="runtime_snapshot_command",
    )
    runtime_snapshot_export_parser = runtime_snapshot_subparsers.add_parser(
        "export",
        help="Export a portable governed runtime snapshot.",
    )
    runtime_snapshot_export_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime snapshot export output.",
    )
    runtime_snapshot_export_parser.set_defaults(handler=run_runtime_snapshot_export)
    runtime_snapshot_inspect_parser = runtime_snapshot_subparsers.add_parser(
        "inspect",
        help="Inspect an exported governed runtime snapshot.",
    )
    runtime_snapshot_inspect_parser.add_argument(
        "path",
        metavar="PATH",
        help="Path to an exported runtime snapshot JSON file.",
    )
    runtime_snapshot_inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime snapshot inspection output.",
    )
    runtime_snapshot_inspect_parser.set_defaults(handler=run_runtime_snapshot_inspect)
    runtime_snapshot_compatibility_parser = runtime_snapshot_subparsers.add_parser(
        "compatibility",
        help="Analyze runtime snapshot compatibility.",
    )
    runtime_snapshot_compatibility_parser.add_argument(
        "path",
        metavar="PATH",
        help="Path to an exported runtime snapshot JSON file.",
    )
    runtime_snapshot_compatibility_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime snapshot compatibility output.",
    )
    runtime_snapshot_compatibility_parser.set_defaults(
        handler=run_runtime_snapshot_compatibility
    )
    runtime_snapshot_manifest_parser = runtime_snapshot_subparsers.add_parser(
        "manifest",
        help="Index exported governed runtime snapshots.",
    )
    runtime_snapshot_manifest_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime snapshot manifest output.",
    )
    runtime_snapshot_manifest_parser.set_defaults(handler=run_runtime_snapshot_manifest)
    runtime_snapshot_retention_parser = runtime_snapshot_subparsers.add_parser(
        "retention",
        help="Preview runtime snapshot retention actions.",
    )
    runtime_snapshot_retention_parser.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="Preview retention actions without deleting snapshots.",
    )
    runtime_snapshot_retention_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime snapshot retention preview output.",
    )
    runtime_snapshot_retention_parser.set_defaults(handler=run_runtime_snapshot_retention)
    runtime_snapshot_lineage_parser = runtime_snapshot_subparsers.add_parser(
        "lineage",
        help="Analyze runtime snapshot lineage relationships.",
    )
    runtime_snapshot_lineage_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime snapshot lineage output.",
    )
    runtime_snapshot_lineage_parser.set_defaults(handler=run_runtime_snapshot_lineage)
    runtime_snapshot_restore_parser = runtime_snapshot_subparsers.add_parser(
        "restore",
        help="Preview restoring a governed runtime snapshot.",
    )
    runtime_snapshot_restore_parser.add_argument(
        "path",
        metavar="PATH",
        help="Path to an exported runtime snapshot JSON file.",
    )
    runtime_snapshot_restore_parser.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="Preview restore effects without modifying runtime state.",
    )
    runtime_snapshot_restore_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime snapshot restore preview output.",
    )
    runtime_snapshot_restore_parser.set_defaults(handler=run_runtime_snapshot_restore)
    runtime_snapshot_validate_restore_parser = runtime_snapshot_subparsers.add_parser(
        "validate-restore",
        help="Validate whether a governance runtime snapshot would be safe to restore.",
    )
    runtime_snapshot_validate_restore_parser.add_argument(
        "path",
        metavar="PATH",
        help="Path to an exported runtime snapshot JSON file.",
    )
    runtime_snapshot_validate_restore_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON restore safety validation output.",
    )
    runtime_snapshot_validate_restore_parser.set_defaults(
        handler=run_runtime_snapshot_validate_restore
    )

    orchestration_parser = subparsers.add_parser(
        "orchestration",
        help="Inspect PCAE orchestration policy.",
    )
    orchestration_subparsers = orchestration_parser.add_subparsers(
        dest="orchestration_command",
        required=True,
    )
    orchestration_policy_parser = orchestration_subparsers.add_parser(
        "policy",
        help="Show effective orchestration policy.",
    )
    orchestration_policy_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON orchestration policy output.",
    )
    orchestration_policy_parser.set_defaults(handler=run_orchestration_policy)

    orchestration_agents_parser = orchestration_subparsers.add_parser(
        "agents",
        help="List registered agents and their capabilities.",
    )
    orchestration_agents_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON agent registry output.",
    )
    orchestration_agents_parser.set_defaults(handler=run_orchestration_agents)

    orchestration_capabilities_parser = orchestration_subparsers.add_parser(
        "capabilities",
        help="Show the governed agent capability matrix.",
    )
    orchestration_capabilities_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON capability matrix output.",
    )
    orchestration_capabilities_parser.set_defaults(handler=run_orchestration_capabilities)

    orchestration_recommend_parser = orchestration_subparsers.add_parser(
        "recommend",
        help="Recommend the best governed agent for a work type.",
    )
    orchestration_recommend_parser.add_argument(
        "--work-type",
        required=True,
        metavar="TEXT",
        help="Work type to match against agent roles.",
    )
    orchestration_recommend_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON recommendation output.",
    )
    orchestration_recommend_parser.set_defaults(handler=run_orchestration_recommend)

    orchestration_select_parser = orchestration_subparsers.add_parser(
        "select",
        help="Select a recommended governed agent for a task type.",
    )
    orchestration_select_parser.add_argument(
        "task_type",
        metavar="TASK_TYPE",
        help="Task type to match against agent roles.",
    )
    orchestration_select_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON selection output.",
    )
    orchestration_select_parser.set_defaults(handler=run_orchestration_select)

    orchestration_explain_parser = orchestration_subparsers.add_parser(
        "explain",
        help="Explain why a governed agent recommendation was selected.",
    )
    orchestration_explain_parser.add_argument(
        "task_type",
        metavar="TASK_TYPE",
        help="Task type to explain against agent roles.",
    )
    orchestration_explain_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON explanation output.",
    )
    orchestration_explain_parser.set_defaults(handler=run_orchestration_explain)

    orchestration_plan_parser = orchestration_subparsers.add_parser(
        "plan",
        help="Generate a governance-aware orchestration workflow plan.",
    )
    orchestration_plan_parser.add_argument(
        "--workflow",
        required=True,
        metavar="TEXT",
        help="Workflow name (documentation, implementation, validation, release).",
    )
    orchestration_plan_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON workflow plan output.",
    )
    orchestration_plan_parser.set_defaults(handler=run_orchestration_plan)

    orchestration_simulate_parser = orchestration_subparsers.add_parser(
        "simulate",
        help="Preview executable orchestration workflow steps without running them.",
    )
    orchestration_simulate_parser.add_argument(
        "--workflow",
        required=True,
        metavar="TEXT",
        help="Workflow name (documentation, implementation, validation, release).",
    )
    orchestration_simulate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON workflow simulation output.",
    )
    orchestration_simulate_parser.set_defaults(handler=run_orchestration_simulate)

    orchestration_validate_parser = orchestration_subparsers.add_parser(
        "validate",
        help="Validate advisory orchestration workflow coherence.",
    )
    orchestration_validate_parser.add_argument(
        "--workflow",
        required=True,
        metavar="TEXT",
        help="Workflow name (documentation, implementation, validation, release).",
    )
    orchestration_validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON workflow validation output.",
    )
    orchestration_validate_parser.set_defaults(handler=run_orchestration_validate)

    orchestration_readiness_parser = orchestration_subparsers.add_parser(
        "readiness",
        help="Preview whether an advisory orchestration workflow is ready.",
    )
    orchestration_readiness_parser.add_argument(
        "--workflow",
        required=True,
        metavar="TEXT",
        help="Workflow name (documentation, implementation, validation, release).",
    )
    orchestration_readiness_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON workflow readiness output.",
    )
    orchestration_readiness_parser.set_defaults(handler=run_orchestration_readiness)

    daemon_parser = subparsers.add_parser(
        "daemon",
        help="Preview PCAE governance daemon monitoring.",
    )
    daemon_subparsers = daemon_parser.add_subparsers(
        dest="daemon_command",
        required=True,
    )
    daemon_run_parser = daemon_subparsers.add_parser(
        "run",
        help="Run one daemon monitoring dry-run cycle.",
    )
    daemon_run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview one daemon monitoring cycle without writing files.",
    )
    daemon_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON daemon dry-run output.",
    )
    daemon_run_parser.set_defaults(handler=run_daemon)

    daemon_status_parser = daemon_subparsers.add_parser(
        "status",
        help="Show PCAE daemon capability status.",
    )
    daemon_status_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON daemon status output.",
    )
    daemon_status_parser.set_defaults(handler=run_daemon_status)

    daemon_watch_parser = daemon_subparsers.add_parser(
        "watch",
        help="Preview future daemon watch behavior.",
    )
    daemon_watch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview daemon watch behavior without looping or writing files.",
    )
    daemon_watch_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON daemon watch dry-run output.",
    )
    daemon_watch_parser.add_argument(
        "--interval-seconds",
        type=int,
        default=default_watch_interval_seconds(),
        help="Preview watch interval in seconds.",
    )
    daemon_watch_parser.set_defaults(handler=run_daemon_watch)

    agent_parser = subparsers.add_parser(
        "agent",
        help="Manage local PCAE agent session leases.",
    )
    agent_subparsers = agent_parser.add_subparsers(
        dest="agent_command",
        required=True,
    )
    agent_acquire_parser = agent_subparsers.add_parser(
        "acquire",
        help="Acquire the local PCAE agent lock.",
    )
    agent_acquire_parser.add_argument("--agent-id", required=True)
    agent_acquire_parser.set_defaults(handler=run_agent_acquire)

    agent_release_parser = agent_subparsers.add_parser(
        "release",
        help="Release the local PCAE agent lock.",
    )
    agent_release_parser.add_argument("--agent-id", required=True)
    agent_release_parser.add_argument(
        "--force-stale",
        action="store_true",
        help="Release a stale lock even if held by another agent.",
    )
    agent_release_parser.set_defaults(handler=run_agent_release)

    agent_status_parser = agent_subparsers.add_parser(
        "status",
        help="Show the local PCAE agent lock status.",
    )
    agent_status_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON agent lock status.",
    )
    agent_status_parser.set_defaults(handler=run_agent_status)

    agents_parser = subparsers.add_parser(
        "agents",
        help="Inspect the multi-agent collaboration registry.",
    )
    agents_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON agent registry output.",
    )
    agents_parser.set_defaults(handler=run_agents)
    agents_subparsers = agents_parser.add_subparsers(dest="agents_command")

    agents_show_parser = agents_subparsers.add_parser(
        "show",
        help="Show detailed metadata for a single agent.",
    )
    agents_show_parser.add_argument(
        "agent_id",
        metavar="AGENT_ID",
        help="Agent identifier to inspect.",
    )
    agents_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON agent detail output.",
    )
    agents_show_parser.set_defaults(handler=run_agents_show)

    agents_validate_parser = agents_subparsers.add_parser(
        "validate",
        help="Validate agent registry consistency.",
    )
    agents_validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON validation output.",
    )
    agents_validate_parser.set_defaults(handler=run_agents_validate)

    agents_lifecycle_parser = agents_subparsers.add_parser(
        "lifecycle",
        help="Report lifecycle state distribution and progression guidance.",
    )
    agents_lifecycle_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON lifecycle report output.",
    )
    agents_lifecycle_parser.set_defaults(handler=run_agents_lifecycle)

    agents_config_parser = agents_subparsers.add_parser(
        "config",
        help="Inspect agent configuration metadata.",
    )
    agents_config_subparsers = agents_config_parser.add_subparsers(
        dest="agents_config_command",
        required=True,
    )

    agents_config_show_parser = agents_config_subparsers.add_parser(
        "show",
        help="Show configuration metadata for a single agent.",
    )
    agents_config_show_parser.add_argument(
        "agent_id",
        metavar="AGENT_ID",
        help="Agent identifier to inspect.",
    )
    agents_config_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON configuration output.",
    )
    agents_config_show_parser.set_defaults(handler=run_agents_config_show)

    agents_config_validate_parser = agents_config_subparsers.add_parser(
        "validate",
        help="Validate agent configuration model consistency.",
    )
    agents_config_validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON validation output.",
    )
    agents_config_validate_parser.set_defaults(handler=run_agents_config_validate)

    agents_runtime_discover_parser = agents_subparsers.add_parser(
        "runtime-discover",
        help="Discover local CLI runtime capabilities for known agents.",
    )
    agents_runtime_discover_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime discovery output.",
    )
    agents_runtime_discover_parser.set_defaults(handler=run_agents_runtime_discover)

    agents_adapters_parser = agents_subparsers.add_parser(
        "adapters",
        help="List all agent adapter definitions.",
    )
    agents_adapters_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON adapter registry output.",
    )
    agents_adapters_parser.set_defaults(handler=run_agents_adapters)

    agents_adapter_parser = agents_subparsers.add_parser(
        "adapter",
        help="Inspect a single agent adapter definition.",
    )
    agents_adapter_subparsers = agents_adapter_parser.add_subparsers(
        dest="agents_adapter_command",
        required=True,
    )
    agents_adapter_show_parser = agents_adapter_subparsers.add_parser(
        "show",
        help="Show adapter metadata for a single agent.",
    )
    agents_adapter_show_parser.add_argument(
        "agent_id",
        metavar="AGENT_ID",
        help="Agent identifier to inspect.",
    )
    agents_adapter_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON adapter output.",
    )
    agents_adapter_show_parser.set_defaults(handler=run_agents_adapter_show)

    agents_adapter_inspect_parser = agents_adapter_subparsers.add_parser(
        "inspect",
        help="Deep capability inspection for a single agent adapter.",
    )
    agents_adapter_inspect_parser.add_argument(
        "agent_id",
        metavar="AGENT_ID",
        help="Agent identifier to inspect.",
    )
    agents_adapter_inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON capability inspection output.",
    )
    agents_adapter_inspect_parser.set_defaults(handler=run_agents_adapter_inspect)

    collaboration_parser = subparsers.add_parser(
        "collaboration",
        help="Inspect governed multi-agent collaboration workflow templates.",
    )
    collaboration_subparsers = collaboration_parser.add_subparsers(
        dest="collaboration_command",
        required=True,
    )
    collaboration_workflows_parser = collaboration_subparsers.add_parser(
        "workflows",
        help="List collaboration workflow templates.",
    )
    collaboration_workflows_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON workflow output.",
    )
    collaboration_workflows_parser.set_defaults(handler=run_collaboration_workflows)

    collaboration_handoffs_parser = collaboration_subparsers.add_parser(
        "handoffs",
        help="Show read-only multi-agent handoff history.",
    )
    collaboration_handoffs_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON handoff history output.",
    )
    collaboration_handoffs_parser.set_defaults(handler=run_collaboration_handoffs)

    collaboration_reviews_parser = collaboration_subparsers.add_parser(
        "reviews",
        help="List review workflow templates and review statuses.",
    )
    collaboration_reviews_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON review workflow output.",
    )
    collaboration_reviews_parser.set_defaults(handler=run_collaboration_reviews)

    collaboration_design_parser = subparsers.add_parser(
        "collaboration-design",
        help="Show read-only multi-agent collaboration architecture design.",
    )
    collaboration_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON collaboration design output.",
    )
    collaboration_design_parser.set_defaults(handler=run_collaboration_design)

    orchestration_design_parser = subparsers.add_parser(
        "orchestration-design",
        help="Show read-only multi-agent orchestration architecture design.",
    )
    orchestration_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON orchestration design output.",
    )
    orchestration_design_parser.set_defaults(handler=run_orchestration_design)

    coordinator_design_parser = subparsers.add_parser(
        "coordinator-design",
        help="Show read-only coordinator agent architecture design.",
    )
    coordinator_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON coordinator design output.",
    )
    coordinator_design_parser.set_defaults(handler=run_coordinator_design)

    consensus_design_parser = subparsers.add_parser(
        "consensus-design",
        help="Show read-only consensus engine architecture design.",
    )
    consensus_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON consensus design output.",
    )
    consensus_design_parser.set_defaults(handler=run_consensus_design)

    parallel_execution_design_parser = subparsers.add_parser(
        "parallel-execution-design",
        help="Show read-only parallel agent execution architecture design.",
    )
    parallel_execution_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON parallel execution design output.",
    )
    parallel_execution_design_parser.set_defaults(handler=run_parallel_execution_design)

    planning_prototype_design_parser = subparsers.add_parser(
        "planning-prototype-design",
        help="Show read-only multi-agent planning prototype architecture design.",
    )
    planning_prototype_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON planning prototype design output.",
    )
    planning_prototype_design_parser.set_defaults(handler=run_planning_prototype_design)

    planning_dry_run_parser = subparsers.add_parser(
        "planning-dry-run",
        help="Simulate a multi-agent planning workflow without executing agents.",
    )
    planning_dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON planning dry-run output.",
    )
    planning_dry_run_parser.set_defaults(handler=run_planning_dry_run)

    planning_execution_design_parser = subparsers.add_parser(
        "planning-execution-design",
        help="Show read-only multi-agent planning execution architecture design (Phase 44J).",
    )
    planning_execution_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON planning execution design output.",
    )
    planning_execution_design_parser.set_defaults(handler=run_planning_execution_design)

    execution_framework_design_parser = subparsers.add_parser(
        "execution-framework-design",
        help="Show read-only agent execution framework architecture design (Phase 44K).",
    )
    execution_framework_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON execution framework design output.",
    )
    execution_framework_design_parser.set_defaults(handler=run_execution_framework_design)

    adapter_design_parser = subparsers.add_parser(
        "adapter-design",
        help="Show read-only runtime adapter integration architecture design (Phase 44L).",
    )
    adapter_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON adapter design output.",
    )
    adapter_design_parser.set_defaults(handler=run_adapter_design)

    invocation_design_parser = subparsers.add_parser(
        "invocation-design",
        help="Show read-only controlled agent invocation architecture design (Phase 44M).",
    )
    invocation_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON invocation design output.",
    )
    invocation_design_parser.set_defaults(handler=run_invocation_design)

    real_planning_design_parser = subparsers.add_parser(
        "real-planning-design",
        help="Show read-only real multi-agent planning architecture design (Phase 44N).",
    )
    real_planning_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON real planning design output.",
    )
    real_planning_design_parser.set_defaults(handler=run_real_planning_design)

    consensus_execution_design_parser = subparsers.add_parser(
        "consensus-execution-design",
        help="Show read-only multi-agent consensus execution architecture design (Phase 44O).",
    )
    consensus_execution_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON consensus execution design output.",
    )
    consensus_execution_design_parser.set_defaults(handler=run_consensus_execution_design)

    runtime_execution_prototype_parser = subparsers.add_parser(
        "runtime-execution-prototype",
        help="Show read-only controlled runtime execution prototype design (Phase 44P).",
    )
    runtime_execution_prototype_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime execution prototype output.",
    )
    runtime_execution_prototype_parser.set_defaults(handler=run_runtime_execution_prototype)

    planner_adapter_prototype_parser = subparsers.add_parser(
        "planner-adapter-prototype",
        help="Show read-only planner runtime adapter prototype preview (Phase 44Q).",
    )
    planner_adapter_prototype_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON planner adapter prototype output.",
    )
    planner_adapter_prototype_parser.set_defaults(handler=run_planner_adapter_prototype)

    multi_agent_prototype_parser = subparsers.add_parser(
        "multi-agent-prototype",
        help="Show read-only multi-agent execution prototype preview (Phase 44R).",
    )
    multi_agent_prototype_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON multi-agent prototype output.",
    )
    multi_agent_prototype_parser.set_defaults(handler=run_multi_agent_prototype)

    consensus_prototype_parser = subparsers.add_parser(
        "consensus-prototype",
        help="Show read-only consensus prototype with simulated multi-agent outputs (Phase 44S).",
    )
    consensus_prototype_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON consensus prototype output.",
    )
    consensus_prototype_parser.set_defaults(handler=run_consensus_prototype)

    invocation_pilot_parser = subparsers.add_parser(
        "invocation-pilot",
        help="Show read-only controlled runtime invocation pilot design (Phase 44T).",
    )
    invocation_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON invocation pilot output.",
    )
    invocation_pilot_parser.set_defaults(handler=run_invocation_pilot)

    multi_runtime_pilot_parser = subparsers.add_parser(
        "multi-runtime-pilot",
        help="Show read-only multi-runtime pilot preview (Phase 44U).",
    )
    multi_runtime_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON multi-runtime pilot output.",
    )
    multi_runtime_pilot_parser.set_defaults(handler=run_multi_runtime_pilot)

    consensus_runtime_pilot_parser = subparsers.add_parser(
        "consensus-runtime-pilot",
        help="Show read-only consensus runtime pilot with simulated multi-runtime outputs (Phase 44V).",
    )
    consensus_runtime_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON consensus runtime pilot output.",
    )
    consensus_runtime_pilot_parser.set_defaults(handler=run_consensus_runtime_pilot)

    governed_execution_dry_run_parser = subparsers.add_parser(
        "governed-execution-dry-run",
        help="Show read-only governed execution dry-run simulating the full lifecycle (Phase 44W).",
    )
    governed_execution_dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON governed execution dry-run output.",
    )
    governed_execution_dry_run_parser.set_defaults(handler=run_governed_execution_dry_run)

    invocation_contracts_parser = subparsers.add_parser(
        "invocation-contracts",
        help="Report validated runtime invocation contracts and flag invalid preview contracts (Phase 44X).",
    )
    invocation_contracts_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON invocation contracts output.",
    )
    invocation_contracts_parser.set_defaults(handler=run_invocation_contracts)

    execution_readiness_parser = subparsers.add_parser(
        "execution-readiness",
        help="Assess PCAE readiness for future real runtime execution (Phase 44Y).",
    )
    execution_readiness_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON execution readiness output.",
    )
    execution_readiness_parser.set_defaults(handler=run_execution_readiness)

    adapter_registry_design_parser = subparsers.add_parser(
        "adapter-registry-design",
        help="Show read-only runtime adapter registry design (Phase 44Z).",
    )
    adapter_registry_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON adapter registry design output.",
    )
    adapter_registry_design_parser.set_defaults(handler=run_adapter_registry_design)

    roadmap_generation_design_parser = subparsers.add_parser(
        "roadmap-generation-design",
        help="Show read-only autonomous roadmap generation architecture design (Phase 45A).",
    )
    roadmap_generation_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON roadmap generation design output.",
    )
    roadmap_generation_design_parser.set_defaults(handler=run_roadmap_generation_design)

    roadmap_evidence_parser = subparsers.add_parser(
        "roadmap-evidence",
        help="Collect read-only repository evidence for roadmap generation (Phase 45B).",
    )
    roadmap_evidence_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON evidence package output.",
    )
    roadmap_evidence_parser.set_defaults(handler=run_roadmap_evidence)

    roadmap_proposal_dry_run_parser = subparsers.add_parser(
        "roadmap-proposal-dry-run",
        help="Generate a simulated roadmap proposal from evidence (Phase 45C).",
    )
    roadmap_proposal_dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON roadmap proposal output.",
    )
    roadmap_proposal_dry_run_parser.set_defaults(handler=run_roadmap_proposal_dry_run)

    multi_agent_roadmap_parser = subparsers.add_parser(
        "multi-agent-roadmap",
        help="Generate a simulated multi-agent roadmap proposal (Phase 45D).",
    )
    multi_agent_roadmap_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON multi-agent roadmap output.",
    )
    multi_agent_roadmap_parser.set_defaults(handler=run_multi_agent_roadmap)

    roadmap_approval_design_parser = subparsers.add_parser(
        "roadmap-approval-design",
        help="Design a governed roadmap approval workflow (Phase 45E).",
    )
    roadmap_approval_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON roadmap approval design output.",
    )
    roadmap_approval_design_parser.set_defaults(handler=run_roadmap_approval_design)

    prompt_generation_design_parser = subparsers.add_parser(
        "prompt-generation-design",
        help="Design the canonical prompt generation architecture (Phase 45F).",
    )
    prompt_generation_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON prompt generation design output.",
    )
    prompt_generation_design_parser.set_defaults(handler=run_prompt_generation_design)

    adaptive_prompt_design_parser = subparsers.add_parser(
        "adaptive-prompt-design",
        help="Design adaptive agent-specific prompt generation (Phase 45G).",
    )
    adaptive_prompt_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON adaptive prompt design output.",
    )
    adaptive_prompt_design_parser.set_defaults(handler=run_adaptive_prompt_design)

    prompt_validation_design_parser = subparsers.add_parser(
        "prompt-validation-design",
        help="Design the prompt validation framework (Phase 45H).",
    )
    prompt_validation_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON prompt validation design output.",
    )
    prompt_validation_design_parser.set_defaults(handler=run_prompt_validation_design)

    prompt_governance_design_parser = subparsers.add_parser(
        "prompt-governance-design",
        help="Design governance controls for canonical and adapted prompts (Phase 45I).",
    )
    prompt_governance_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON prompt governance design output.",
    )
    prompt_governance_design_parser.set_defaults(handler=run_prompt_governance_design)

    prompt_artifact_design_parser = subparsers.add_parser(
        "prompt-artifact-design",
        help="Define the canonical PromptArtifact model (Phase 45J).",
    )
    prompt_artifact_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON prompt artifact design output.",
    )
    prompt_artifact_design_parser.set_defaults(handler=run_prompt_artifact_design)

    prompt_approval_workflow_parser = subparsers.add_parser(
        "prompt-approval-design",
        help="Design the governed prompt approval workflow (Phase 45K).",
    )
    prompt_approval_workflow_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON prompt approval workflow output.",
    )
    prompt_approval_workflow_parser.set_defaults(handler=run_prompt_approval_workflow)

    autonomous_phase_proposal_parser = subparsers.add_parser(
        "autonomous-phase-proposal",
        help="Generate candidate future phases from repository evidence (Phase 45L).",
    )
    autonomous_phase_proposal_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON autonomous phase proposal output.",
    )
    autonomous_phase_proposal_parser.set_defaults(handler=run_autonomous_phase_proposal)

    autonomous_prompt_proposal_parser = subparsers.add_parser(
        "autonomous-prompt-proposal",
        help="Generate governed prompt proposals from autonomously proposed phases (Phase 45M).",
    )
    autonomous_prompt_proposal_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON autonomous prompt proposal output.",
    )
    autonomous_prompt_proposal_parser.set_defaults(handler=run_autonomous_prompt_proposal)

    prompt_render_parser = subparsers.add_parser(
        "prompt-render",
        help="Render governed prompt proposals into human-readable text (Phase 45M.1).",
    )
    prompt_render_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON prompt render output.",
    )
    prompt_render_parser.set_defaults(handler=run_prompt_render)

    prompt_execution_readiness_parser = subparsers.add_parser(
        "prompt-execution-readiness",
        help="Assess PCAE readiness for future governed prompt execution (Phase 45N).",
    )
    prompt_execution_readiness_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON prompt execution readiness output.",
    )
    prompt_execution_readiness_parser.set_defaults(handler=run_prompt_execution_readiness)

    prompt_execution_dry_run_parser = subparsers.add_parser(
        "prompt-execution-dry-run",
        help="Simulate governed prompt execution pipeline without invoking agents (Phase 45O).",
    )
    prompt_execution_dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON prompt execution dry-run output.",
    )
    prompt_execution_dry_run_parser.set_defaults(handler=run_prompt_execution_dry_run)

    human_agent_execution_design_parser = subparsers.add_parser(
        "human-agent-execution-design",
        help="Design human-selected agent execution for governed prompts (Phase 45P).",
    )
    human_agent_execution_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON human-agent execution design output.",
    )
    human_agent_execution_design_parser.set_defaults(handler=run_human_agent_execution_design)

    governed_execution_pilot_parser = subparsers.add_parser(
        "governed-execution-pilot",
        help="Simulate the complete governed prompt execution workflow (Phase 45Q).",
    )
    governed_execution_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON governed execution pilot output.",
    )
    governed_execution_pilot_parser.set_defaults(handler=run_governed_execution_pilot)

    live_execution_readiness_parser = subparsers.add_parser(
        "live-execution-readiness",
        help="Assess PCAE readiness for future governed live prompt execution (Phase 46A).",
    )
    live_execution_readiness_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON live execution readiness output.",
    )
    live_execution_readiness_parser.set_defaults(handler=run_live_execution_readiness)

    execution_audit_design_parser = subparsers.add_parser(
        "execution-audit-design",
        help="Design governed runtime audit storage for prompt execution (Phase 46B).",
    )
    execution_audit_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON execution audit design output.",
    )
    execution_audit_design_parser.set_defaults(handler=run_execution_audit_design)

    execution_consensus_framework_parser = subparsers.add_parser(
        "execution-consensus-design",
        help="Design consensus framework for reconciling multi-agent execution outcomes (Phase 46C).",
    )
    execution_consensus_framework_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON execution consensus framework output.",
    )
    execution_consensus_framework_parser.set_defaults(handler=run_execution_consensus_framework)

    live_execution_pilot_parser = subparsers.add_parser(
        "live-execution-pilot",
        help="Design governed live execution pilot architecture (Phase 46D).",
    )
    live_execution_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON live execution pilot output.",
    )
    live_execution_pilot_parser.set_defaults(handler=run_live_execution_pilot)

    invocation_workload_validation_parser = subparsers.add_parser(
        "invocation-workload-validation",
        help="Validate runtime invocation contracts against prompt-execution workloads (Phase 46E).",
    )
    invocation_workload_validation_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON invocation workload validation output.",
    )
    invocation_workload_validation_parser.set_defaults(handler=run_invocation_workload_validation)

    execution_authorization_design_parser = subparsers.add_parser(
        "execution-authorization-design",
        help="Define the ExecutionAuthorizationArtifact model for governed prompt execution (Phase 46F).",
    )
    execution_authorization_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON execution authorization design output.",
    )
    execution_authorization_design_parser.set_defaults(handler=run_execution_authorization_design)

    read_only_invocation_pilot_parser = subparsers.add_parser(
        "read-only-invocation-pilot",
        help="Design governed read-only runtime invocation pilot architecture (Phase 46G).",
    )
    read_only_invocation_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON read-only invocation pilot output.",
    )
    read_only_invocation_pilot_parser.set_defaults(handler=run_read_only_invocation_pilot)

    execution_result_review_design_parser = subparsers.add_parser(
        "execution-result-review-design",
        help="Design governed live execution result review workflow (Phase 46H).",
    )
    execution_result_review_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON execution result review design output.",
    )
    execution_result_review_design_parser.set_defaults(handler=run_execution_result_review_design)

    authorization_expiration_design_parser = subparsers.add_parser(
        "authorization-expiration-design",
        help="Design governance controls for authorization expiration workflow (Phase 46I).",
    )
    authorization_expiration_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON authorization expiration design output.",
    )
    authorization_expiration_design_parser.set_defaults(handler=run_authorization_expiration_design)

    invocation_pilot_status_parser = subparsers.add_parser(
        "invocation-pilot-status",
        help="Show read-only invocation pilot infrastructure status (Phase 46J).",
    )
    invocation_pilot_status_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON invocation pilot status output.",
    )
    invocation_pilot_status_parser.set_defaults(handler=run_invocation_pilot_status)

    multi_agent_invocation_pilot_parser = subparsers.add_parser(
        "multi-agent-invocation-pilot",
        help="Design governed multi-agent read-only invocation pilot structures (Phase 46K).",
    )
    multi_agent_invocation_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON multi-agent invocation pilot output.",
    )
    multi_agent_invocation_pilot_parser.set_defaults(handler=run_multi_agent_invocation_pilot)

    execution_quality_design_parser = subparsers.add_parser(
        "execution-quality-design",
        help="Design execution result quality framework for future runtime invocations (Phase 46L).",
    )
    execution_quality_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON execution quality design output.",
    )
    execution_quality_design_parser.set_defaults(handler=run_execution_quality_design)

    read_only_invocation_execution_pilot_parser = subparsers.add_parser(
        "read-only-invocation-execution-pilot",
        help="Design controlled read-only invocation execution pilot structures (Phase 46M).",
    )
    read_only_invocation_execution_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON read-only invocation execution pilot output.",
    )
    read_only_invocation_execution_pilot_parser.set_defaults(
        handler=run_read_only_invocation_execution_pilot
    )

    write_invocation_design_parser = subparsers.add_parser(
        "write-invocation-design",
        help="Design governed write invocation governance model (Phase 46N).",
    )
    write_invocation_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON write invocation design output.",
    )
    write_invocation_design_parser.set_defaults(handler=run_write_invocation_design)

    write_preflight_dry_run_parser = subparsers.add_parser(
        "write-preflight-dry-run",
        help="Simulate governed write invocation preflight process (Phase 46O).",
    )
    write_preflight_dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON write preflight dry-run output.",
    )
    write_preflight_dry_run_parser.set_defaults(handler=run_write_preflight_dry_run)

    write_candidate_design_parser = subparsers.add_parser(
        "write-candidate-design",
        help="Define governed write candidate artifact model (Phase 46P).",
    )
    write_candidate_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON write candidate design output.",
    )
    write_candidate_design_parser.set_defaults(handler=run_write_candidate_design)

    write_invocation_pilot_parser = subparsers.add_parser(
        "write-invocation-pilot",
        help="Simulate controlled write invocation pilot (Phase 46Q).",
    )
    write_invocation_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON write invocation pilot output.",
    )
    write_invocation_pilot_parser.set_defaults(handler=run_write_invocation_pilot)

    write_result_review_design_parser = subparsers.add_parser(
        "write-result-review-design",
        help="Design write result review governance workflow (Phase 46R).",
    )
    write_result_review_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON write result review design output.",
    )
    write_result_review_design_parser.set_defaults(handler=run_write_result_review_design)

    write_rollback_validation_design_parser = subparsers.add_parser(
        "write-rollback-validation-design",
        help="Design write rollback validation governance workflow (Phase 46S).",
    )
    write_rollback_validation_design_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON write rollback validation design output.",
    )
    write_rollback_validation_design_parser.set_defaults(
        handler=run_write_rollback_validation_design
    )

    write_execution_readiness_parser = subparsers.add_parser(
        "write-execution-readiness",
        help="Assess write execution readiness for governed write pilot (Phase 46T).",
    )
    write_execution_readiness_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON write execution readiness output.",
    )
    write_execution_readiness_parser.set_defaults(handler=run_write_execution_readiness)

    write_rollback_dry_run_parser = subparsers.add_parser(
        "write-rollback-dry-run",
        help="Simulate governed rollback dry-run path without executing rollback (Phase 46U).",
    )
    write_rollback_dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON write rollback dry-run output.",
    )
    write_rollback_dry_run_parser.set_defaults(handler=run_write_rollback_dry_run)

    live_readonly_readiness_parser = subparsers.add_parser(
        "live-readonly-readiness",
        help="Assess governed live read-only execution readiness (Phase 47A).",
    )
    live_readonly_readiness_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON live read-only readiness output.",
    )
    live_readonly_readiness_parser.set_defaults(handler=run_live_readonly_readiness)

    live_write_readiness_parser = subparsers.add_parser(
        "live-write-readiness",
        help="Assess governed live write execution readiness (Phase 47B).",
    )
    live_write_readiness_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON live write readiness output.",
    )
    live_write_readiness_parser.set_defaults(handler=run_live_write_readiness)

    live_readonly_pilot_parser = subparsers.add_parser(
        "live-readonly-pilot",
        help="Define the first governed live read-only execution pilot (Phase 47C).",
    )
    live_readonly_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON live read-only pilot output.",
    )
    live_readonly_pilot_parser.set_defaults(handler=run_live_readonly_pilot)

    rollback_execution_pilot_parser = subparsers.add_parser(
        "rollback-execution-pilot",
        help="Define the first governed rollback execution pilot (Phase 47D).",
    )
    rollback_execution_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON rollback execution pilot output.",
    )
    rollback_execution_pilot_parser.set_defaults(handler=run_rollback_execution_pilot)

    live_write_pilot_parser = subparsers.add_parser(
        "live-write-pilot",
        help="Define the first governed live write execution pilot (Phase 47E).",
    )
    live_write_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON live write pilot output.",
    )
    live_write_pilot_parser.set_defaults(handler=run_live_write_pilot)

    runtime_contracts_parser = subparsers.add_parser(
        "runtime-contracts",
        help="Define and verify governed runtime contracts (Phase 47F).",
    )
    runtime_contracts_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime contracts output.",
    )
    runtime_contracts_parser.set_defaults(handler=run_runtime_contracts)

    exec_governance_audit_parser = subparsers.add_parser(
        "governance-audit",
        help="Perform a whole-system governance audit of PCAE execution architecture (Phase 47G).",
    )
    exec_governance_audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON governance audit output.",
    )
    exec_governance_audit_parser.set_defaults(handler=run_execution_governance_audit)

    runtime_trust_parser = subparsers.add_parser(
        "runtime-trust",
        help="Assess trust levels for PCAE runtimes (Phase 47H).",
    )
    runtime_trust_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON runtime trust assessment output.",
    )
    runtime_trust_parser.set_defaults(handler=run_runtime_trust)

    governance_maturity_parser = subparsers.add_parser(
        "governance-maturity",
        help="Assess overall PCAE governance maturity (Phase 47I).",
    )
    governance_maturity_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON governance maturity assessment output.",
    )
    governance_maturity_parser.set_defaults(handler=run_governance_maturity)

    readonly_invocation_parser = subparsers.add_parser(
        "readonly-invocation",
        help="Controlled read-only runtime invocation scaffold (Phase 48A).",
    )
    readonly_invocation_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    readonly_invocation_parser.set_defaults(handler=run_readonly_invocation)

    invocation_result_capture_parser = subparsers.add_parser(
        "invocation-result-capture",
        help="Governed invocation result capture scaffold (Phase 48B).",
    )
    invocation_result_capture_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    invocation_result_capture_parser.set_defaults(handler=run_invocation_result_capture)

    runtime_contract_enforcement_parser = subparsers.add_parser(
        "runtime-contract-enforcement",
        help="Evaluate runtime contract enforcement checks (Phase 48C).",
    )
    runtime_contract_enforcement_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    runtime_contract_enforcement_parser.set_defaults(handler=run_runtime_contract_enforcement)

    invocation_authorization_enforcement_parser = subparsers.add_parser(
        "invocation-authorization-enforcement",
        help="Evaluate invocation authorization enforcement chain (Phase 48D).",
    )
    invocation_authorization_enforcement_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    invocation_authorization_enforcement_parser.set_defaults(
        handler=run_invocation_authorization_enforcement
    )

    invocation_audit_trail_parser = subparsers.add_parser(
        "invocation-audit",
        help="Scaffold governed invocation audit trail models (Phase 48E).",
    )
    invocation_audit_trail_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    invocation_audit_trail_parser.set_defaults(handler=run_invocation_audit_trail)

    readonly_runtime_pilot_parser = subparsers.add_parser(
        "readonly-runtime-pilot",
        help="Evaluate controlled read-only runtime invocation pilot gates (Phase 48F).",
    )
    readonly_runtime_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    readonly_runtime_pilot_parser.set_defaults(handler=run_readonly_runtime_pilot)

    invocation_result_review_parser = subparsers.add_parser(
        "invocation-result-review",
        help="Scaffold governed invocation result review workflow models (Phase 48G).",
    )
    invocation_result_review_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    invocation_result_review_parser.set_defaults(handler=run_invocation_result_review)

    invocation_evidence_parser = subparsers.add_parser(
        "invocation-evidence",
        help="Scaffold governed invocation evidence models (Phase 48H).",
    )
    invocation_evidence_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    invocation_evidence_parser.set_defaults(handler=run_invocation_evidence)

    multi_agent_readonly_pilot_parser = subparsers.add_parser(
        "multi-agent-readonly-pilot",
        help="Define the first governed multi-agent read-only pilot (Phase 49A).",
    )
    multi_agent_readonly_pilot_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    multi_agent_readonly_pilot_parser.set_defaults(handler=run_multi_agent_readonly_pilot)

    consensus_engine_parser = subparsers.add_parser(
        "consensus-engine",
        help="Define the multi-agent consensus engine governance model (Phase 49B).",
    )
    consensus_engine_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    consensus_engine_parser.set_defaults(handler=run_consensus_engine)

    arbitration_parser = subparsers.add_parser(
        "arbitration",
        help="Define the multi-agent arbitration framework governance model (Phase 49C).",
    )
    arbitration_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    arbitration_parser.set_defaults(handler=run_arbitration)

    evidence_framework_parser = subparsers.add_parser(
        "evidence-framework",
        help="Define the multi-agent evidence framework governance model (Phase 49D).",
    )
    evidence_framework_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    evidence_framework_parser.set_defaults(handler=run_evidence_framework)

    decision_record_parser = subparsers.add_parser(
        "decision-record",
        help="Define the multi-agent decision record governance model (Phase 49E).",
    )
    decision_record_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    decision_record_parser.set_defaults(handler=run_decision_record)

    capability_registry_parser = subparsers.add_parser(
        "capability-registry",
        help="Show the evidence-based agent capability registry (no CLI probing).",
    )
    capability_registry_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON capability registry output.",
    )
    capability_registry_parser.set_defaults(handler=run_capability_registry)

    capability_discovery_parser = subparsers.add_parser(
        "capability-discovery",
        help="Run auto-discovery of agent capabilities via CLI help inspection.",
    )
    capability_discovery_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON capability discovery output.",
    )
    capability_discovery_parser.set_defaults(handler=run_capability_discovery)

    capability_validation_parser = subparsers.add_parser(
        "capability-validation",
        help="Show the capability validation framework and promotion rules (Phase 44D).",
    )
    capability_validation_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON capability validation output.",
    )
    capability_validation_parser.set_defaults(handler=run_capability_validation)

    remote_parser = subparsers.add_parser(
        "remote",
        help="Inspect Remote Autonomous Coding readiness.",
    )
    remote_subparsers = remote_parser.add_subparsers(dest="remote_command", required=True)
    remote_status_parser = remote_subparsers.add_parser(
        "status",
        help="Report Remote Autonomous Coding readiness status.",
    )
    remote_status_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON remote status output.",
    )
    remote_status_parser.set_defaults(handler=run_remote_status)

    remote_adapters_parser = remote_subparsers.add_parser(
        "adapters",
        help="Select the best available adapter for Remote Autonomous Coding.",
    )
    remote_adapters_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON remote adapter selection output.",
    )
    remote_adapters_parser.set_defaults(handler=run_remote_adapters)

    remote_strategy_parser = remote_subparsers.add_parser(
        "strategy",
        help="Report the Remote Autonomous Coding runtime selection strategy.",
    )
    remote_strategy_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON remote strategy output.",
    )
    remote_strategy_parser.set_defaults(handler=run_remote_strategy)

    remote_dry_run_parser = remote_subparsers.add_parser(
        "dry-run",
        help="Preview a Remote Autonomous Coding execution without running agents.",
    )
    remote_dry_run_parser.add_argument(
        "--agent",
        required=True,
        help="Agent ID to use for the dry run (e.g. codex-local).",
    )
    remote_dry_run_parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt text to preview (not submitted to any agent).",
    )
    remote_dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON dry-run output.",
    )
    remote_dry_run_parser.set_defaults(handler=run_remote_dry_run)

    remote_create_parser = remote_subparsers.add_parser(
        "create",
        help="Preview creation of a Remote Autonomous Coding job.",
    )
    remote_create_parser.add_argument(
        "--agent",
        required=True,
        help="Agent ID for the job (e.g. codex-local).",
    )
    remote_create_parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt text for the job (not submitted to any agent).",
    )
    _create_mode = remote_create_parser.add_mutually_exclusive_group(required=True)
    _create_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the job creation without persisting or executing it.",
    )
    _create_mode.add_argument(
        "--preview-persist",
        dest="preview_persist",
        action="store_true",
        help="Preview what would be persisted, including the job file path.",
    )
    _create_mode.add_argument(
        "--persist",
        action="store_true",
        help="Persist the job definition to .pcae/remote/jobs/ without executing it.",
    )
    remote_create_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON job creation preview.",
    )
    remote_create_parser.set_defaults(handler=run_remote_create)

    remote_jobs_parser = remote_subparsers.add_parser(
        "jobs",
        help="Manage Remote Autonomous Coding job definitions.",
    )
    remote_jobs_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON remote jobs output.",
    )
    remote_jobs_parser.set_defaults(handler=run_remote_jobs)

    remote_jobs_subparsers = remote_jobs_parser.add_subparsers(
        dest="jobs_command",
        required=False,
    )

    remote_jobs_list_parser = remote_jobs_subparsers.add_parser(
        "list",
        help="List persisted Remote Autonomous Coding jobs.",
    )
    remote_jobs_list_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON job listing.",
    )
    remote_jobs_list_parser.set_defaults(handler=run_remote_jobs_list)

    remote_jobs_show_parser = remote_jobs_subparsers.add_parser(
        "show",
        help="Inspect a persisted Remote Autonomous Coding job.",
    )
    remote_jobs_show_parser.add_argument(
        "job_id",
        help="ID of the job to inspect.",
    )
    remote_jobs_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON job details.",
    )
    remote_jobs_show_parser.set_defaults(handler=run_remote_jobs_show)

    remote_approve_parser = remote_subparsers.add_parser(
        "approve",
        help="Approve a persisted Remote Autonomous Coding job.",
    )
    remote_approve_parser.add_argument(
        "job_id",
        help="ID of the job to approve.",
    )
    remote_approve_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON approval output.",
    )
    remote_approve_parser.set_defaults(handler=run_remote_approve)

    remote_deny_parser = remote_subparsers.add_parser(
        "deny",
        help="Deny a persisted Remote Autonomous Coding job.",
    )
    remote_deny_parser.add_argument(
        "job_id",
        help="ID of the job to deny.",
    )
    remote_deny_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON denial output.",
    )
    remote_deny_parser.set_defaults(handler=run_remote_deny)

    remote_ready_parser = remote_subparsers.add_parser(
        "ready",
        help="Check execution readiness of a persisted Remote Autonomous Coding job.",
    )
    remote_ready_parser.add_argument(
        "job_id",
        help="ID of the job to check.",
    )
    remote_ready_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON readiness output.",
    )
    remote_ready_parser.set_defaults(handler=run_remote_ready)

    remote_execute_parser = remote_subparsers.add_parser(
        "execute",
        help="Preview or invoke a persisted Remote Autonomous Coding job.",
    )
    remote_execute_parser.add_argument(
        "job_id",
        help="ID of the job to execute.",
    )
    _execute_mode = remote_execute_parser.add_mutually_exclusive_group()
    _execute_mode.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Preview execution without invoking any agent.",
    )
    _execute_mode.add_argument(
        "--invoke",
        action="store_true",
        dest="invoke",
        help="Invoke the agent for real under PCAE governance.",
    )
    remote_execute_parser.add_argument(
        "--allow-file-changes",
        action="store_true",
        dest="allow_file_changes",
        help=(
            "Allow the agent to write files under governed scope rules. "
            "Requires --invoke. No commit or push is performed."
        ),
    )
    remote_execute_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_execute_parser.set_defaults(handler=run_remote_execute)

    remote_validate_parser = remote_subparsers.add_parser(
        "validate",
        help="Validate Remote Autonomous Coding job definitions.",
    )
    remote_validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON remote validation output.",
    )
    remote_validate_parser.set_defaults(handler=run_remote_validate)

    remote_approvals_parser = remote_subparsers.add_parser(
        "approvals",
        help="Report Remote Autonomous Coding approval workflow.",
    )
    remote_approvals_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON remote approvals output.",
    )
    remote_approvals_parser.set_defaults(handler=run_remote_approvals)

    remote_policy_parser = remote_subparsers.add_parser(
        "policy",
        help="Report Remote Autonomous Coding execution policy.",
    )
    remote_policy_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON remote policy output.",
    )
    remote_policy_parser.set_defaults(handler=run_remote_policy)

    remote_plan_parser = remote_subparsers.add_parser(
        "plan",
        help="Generate a Remote Autonomous Coding execution plan.",
    )
    remote_plan_parser.add_argument(
        "--agent",
        default="codex-local",
        help="Requested agent for the execution plan (default: codex-local).",
    )
    remote_plan_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON remote plan output.",
    )
    remote_plan_parser.set_defaults(handler=run_remote_plan)

    remote_results_parser = remote_subparsers.add_parser(
        "results",
        help="List all execution results, or report results for a specific job.",
    )
    remote_results_parser.add_argument(
        "job_id",
        nargs="?",
        default=None,
        help="Job ID to report results for. Omit to list all persisted results.",
    )
    remote_results_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_results_parser.set_defaults(handler=run_remote_results)

    remote_analytics_parser = remote_subparsers.add_parser(
        "analytics",
        help="Compute analytics over persisted execution result artifacts.",
    )
    remote_analytics_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON analytics output.",
    )
    remote_analytics_parser.set_defaults(handler=run_remote_analytics)

    remote_trends_parser = remote_subparsers.add_parser(
        "trends",
        help="Analyze historical execution trends from persisted result artifacts.",
    )
    remote_trends_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON trends output.",
    )
    remote_trends_parser.set_defaults(handler=run_remote_trends)

    remote_benchmark_parser = remote_subparsers.add_parser(
        "benchmark",
        help="Benchmark supported runtimes using persisted execution history.",
    )
    remote_benchmark_subparsers = remote_benchmark_parser.add_subparsers(
        dest="benchmark_command",
    )
    remote_benchmark_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON benchmark output.",
    )
    remote_benchmark_parser.set_defaults(handler=run_remote_benchmark)

    remote_benchmark_controlled_parser = remote_benchmark_subparsers.add_parser(
        "controlled",
        help="Preview a controlled benchmark plan without executing agents.",
    )
    remote_benchmark_controlled_parser.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="Preview the controlled benchmark plan (required).",
    )
    remote_benchmark_controlled_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON benchmark plan.",
    )
    remote_benchmark_controlled_parser.set_defaults(handler=run_remote_benchmark_controlled)

    remote_file_governance_parser = remote_subparsers.add_parser(
        "file-governance",
        help="Display the governance design for future file-modifying autonomous coding.",
    )
    remote_file_governance_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON governance design.",
    )
    remote_file_governance_parser.set_defaults(handler=run_remote_file_governance)

    remote_changes_parser = remote_subparsers.add_parser(
        "changes",
        help="Review and approve/deny governed change artifacts.",
    )
    remote_changes_parser.set_defaults(handler=run_remote_changes)

    remote_changes_subparsers = remote_changes_parser.add_subparsers(
        dest="changes_command",
        required=False,
    )

    remote_changes_show_parser = remote_changes_subparsers.add_parser(
        "show",
        help="Review change artifacts for a file-modifying remote execution.",
    )
    remote_changes_show_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID to review changes for.",
    )
    remote_changes_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_changes_show_parser.set_defaults(handler=run_remote_changes_show)

    remote_changes_approve_parser = remote_changes_subparsers.add_parser(
        "approve",
        help="Approve file changes produced by a remote execution.",
    )
    remote_changes_approve_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID whose changes to approve.",
    )
    remote_changes_approve_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_changes_approve_parser.set_defaults(handler=run_remote_changes_approve)

    remote_changes_deny_parser = remote_changes_subparsers.add_parser(
        "deny",
        help="Deny file changes produced by a remote execution.",
    )
    remote_changes_deny_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID whose changes to deny.",
    )
    remote_changes_deny_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_changes_deny_parser.set_defaults(handler=run_remote_changes_deny)

    remote_commit_parser = remote_subparsers.add_parser(
        "commit",
        help="Create a governed git commit for approved file changes.",
    )
    remote_commit_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID whose approved changes to commit.",
    )
    remote_commit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_commit_parser.set_defaults(handler=run_remote_commit)

    remote_push_parser = remote_subparsers.add_parser(
        "push",
        help="Execute a governed git push for an approved, committed job.",
    )
    remote_push_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID whose governed commit to push.",
    )
    remote_push_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_push_parser.set_defaults(handler=run_remote_push)

    remote_rollback_governance_parser = remote_subparsers.add_parser(
        "rollback-governance",
        help="Display the rollback governance design (read-only).",
    )
    remote_rollback_governance_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_rollback_governance_parser.set_defaults(handler=run_remote_rollback_governance)

    remote_rollback_review_parser = remote_subparsers.add_parser(
        "rollback-review",
        help="Generate a governed rollback review artifact for a job (read-only).",
    )
    remote_rollback_review_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID to generate a rollback review for.",
    )
    remote_rollback_review_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_rollback_review_parser.set_defaults(handler=run_remote_rollback_review)

    remote_rollback_parser = remote_subparsers.add_parser(
        "rollback",
        help="Approve or deny a governed rollback plan for a job.",
    )
    remote_rollback_subparsers = remote_rollback_parser.add_subparsers(
        dest="rollback_command",
        required=True,
    )

    remote_rollback_approve_parser = remote_rollback_subparsers.add_parser(
        "approve",
        help="Approve a rollback plan for an eligible job.",
    )
    remote_rollback_approve_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID whose rollback plan to approve.",
    )
    remote_rollback_approve_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_rollback_approve_parser.set_defaults(handler=run_remote_rollback_approve)

    remote_rollback_deny_parser = remote_rollback_subparsers.add_parser(
        "deny",
        help="Deny a rollback plan for a job.",
    )
    remote_rollback_deny_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID whose rollback plan to deny.",
    )
    remote_rollback_deny_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_rollback_deny_parser.set_defaults(handler=run_remote_rollback_deny)

    remote_rollback_execute_parser = remote_rollback_subparsers.add_parser(
        "execute",
        help="Execute a governed rollback using git revert for an approved job.",
    )
    remote_rollback_execute_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID whose approved rollback plan to execute.",
    )
    remote_rollback_execute_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_rollback_execute_parser.set_defaults(handler=run_remote_rollback_execute)

    remote_rollback_push_parser = remote_rollback_subparsers.add_parser(
        "push",
        help="Push a rollback commit after governed rollback execution.",
    )
    remote_rollback_push_parser.add_argument(
        "job_id",
        metavar="JOB_ID",
        help="Job ID whose rollback commit to push.",
    )
    remote_rollback_push_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_rollback_push_parser.set_defaults(handler=run_remote_rollback_push)

    remote_writable_contract_parser = remote_subparsers.add_parser(
        "writable-contract",
        help="Inspect the writable execution contract for a given agent (read-only).",
    )
    remote_writable_contract_parser.add_argument(
        "agent_id",
        metavar="AGENT_ID",
        help="Agent ID to inspect (e.g. claude-local).",
    )
    remote_writable_contract_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    remote_writable_contract_parser.set_defaults(handler=run_remote_writable_contract)

    remote_report_parser = remote_subparsers.add_parser(
        "report",
        help="Export execution report artifacts.",
    )
    remote_report_subparsers = remote_report_parser.add_subparsers(
        dest="report_command",
        required=True,
    )
    remote_report_export_parser = remote_report_subparsers.add_parser(
        "export",
        help="Export execution report to .pcae/remote/reports/.",
    )
    remote_report_export_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON export metadata.",
    )
    remote_report_export_parser.set_defaults(handler=run_remote_report_export)

    remote_report_inspect_parser = remote_report_subparsers.add_parser(
        "inspect",
        help="Inspect an exported execution report file.",
    )
    remote_report_inspect_parser.add_argument(
        "report_file",
        help="Path to the exported report file to inspect.",
    )
    remote_report_inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON inspection output.",
    )
    remote_report_inspect_parser.set_defaults(handler=run_remote_report_inspect)

    analytics_parser = subparsers.add_parser(
        "analytics",
        help="Analyze PCAE governance history.",
    )
    analytics_subparsers = analytics_parser.add_subparsers(
        dest="analytics_command",
        required=True,
    )
    analytics_trends_parser = analytics_subparsers.add_parser(
        "trends",
        help="Summarize governance trends from architecture history.",
    )
    analytics_trends_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON analytics trends output.",
    )
    analytics_trends_parser.set_defaults(handler=run_analytics_trends)
    analytics_risk_parser = analytics_subparsers.add_parser(
        "risk",
        help="Compute a simple governance risk score.",
    )
    analytics_risk_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON analytics risk output.",
    )
    analytics_risk_parser.set_defaults(handler=run_analytics_risk)

    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run predefined PCAE governance workflows.",
    )
    pipeline_subparsers = pipeline_parser.add_subparsers(
        dest="pipeline_command",
        required=True,
    )
    pipeline_list_parser = pipeline_subparsers.add_parser(
        "list",
        help="List available governance pipelines.",
    )
    pipeline_list_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON pipeline list output.",
    )
    pipeline_list_parser.set_defaults(handler=run_pipeline_list)

    pipeline_run_parser = pipeline_subparsers.add_parser(
        "run",
        help="Run a predefined governance pipeline.",
    )
    pipeline_run_parser.add_argument(
        "name",
        nargs="?",
        default="default",
        help="Pipeline name to run.",
    )
    pipeline_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON pipeline output.",
    )
    pipeline_run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview pipeline execution without writing operational artifacts.",
    )
    pipeline_run_parser.set_defaults(handler=run_pipeline)

    fleet_parser = subparsers.add_parser(
        "fleet",
        help="Manage the local PCAE governed repository registry.",
    )
    fleet_subparsers = fleet_parser.add_subparsers(
        dest="fleet_command",
        required=True,
    )

    fleet_add_parser = fleet_subparsers.add_parser(
        "add",
        help="Register a governed repository path.",
    )
    fleet_add_parser.add_argument("path")
    fleet_add_parser.set_defaults(handler=run_fleet_add)

    fleet_list_parser = fleet_subparsers.add_parser(
        "list",
        help="List registered governed repositories.",
    )
    fleet_list_parser.set_defaults(handler=run_fleet_list)

    fleet_remove_parser = fleet_subparsers.add_parser(
        "remove",
        help="Remove a governed repository path from the fleet registry.",
    )
    fleet_remove_parser.add_argument("path")
    fleet_remove_parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Remove the repo only if the registered path no longer exists.",
    )
    fleet_remove_parser.set_defaults(handler=run_fleet_remove)

    fleet_health_parser = fleet_subparsers.add_parser(
        "health",
        help="Summarize governance health across registered repositories.",
    )
    fleet_health_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON fleet health output.",
    )
    fleet_health_parser.set_defaults(handler=run_fleet_health)

    fleet_inspect_parser = fleet_subparsers.add_parser(
        "inspect",
        help="Inspect PCAE readiness across registered repositories.",
    )
    fleet_inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON fleet inspection output.",
    )
    fleet_inspect_parser.set_defaults(handler=run_fleet_inspect)

    fleet_drift_parser = fleet_subparsers.add_parser(
        "drift",
        help="Detect governance drift across registered repositories.",
    )
    fleet_drift_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON fleet drift output.",
    )
    fleet_drift_parser.set_defaults(handler=run_fleet_drift)

    fleet_apply_parser = fleet_subparsers.add_parser(
        "apply",
        help="Apply PCAE governance onboarding across registered repositories.",
    )
    fleet_apply_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview fleet governance apply actions without writing files.",
    )
    fleet_apply_parser.add_argument(
        "--force",
        action="store_true",
        help="Apply governance files using PCAE-managed overwrite rules.",
    )
    fleet_apply_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON fleet apply output.",
    )
    fleet_apply_parser.set_defaults(handler=run_fleet_apply)

    fleet_export_parser = fleet_subparsers.add_parser(
        "export",
        help="Write a portable fleet governance JSON bundle.",
    )
    fleet_export_parser.set_defaults(handler=run_fleet_export)

    export_parser = subparsers.add_parser(
        "export",
        help="Export PCAE governance state.",
    )
    export_subparsers = export_parser.add_subparsers(
        dest="export_command",
        required=True,
    )

    export_bundle_parser = export_subparsers.add_parser(
        "bundle",
        help="Write a portable governance JSON bundle.",
    )
    export_bundle_parser.set_defaults(handler=run_export_bundle)

    import_parser = subparsers.add_parser(
        "import",
        help="Preview importing PCAE governance state.",
    )
    import_subparsers = import_parser.add_subparsers(
        dest="import_command",
        required=True,
    )

    import_bundle_parser = import_subparsers.add_parser(
        "bundle",
        help="Preview a governance JSON bundle import.",
    )
    import_bundle_parser.add_argument("bundle")
    import_bundle_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview import actions without writing files.",
    )
    import_bundle_parser.add_argument(
        "--merge-history",
        action="store_true",
        help="Merge architecture history instead of replacing it.",
    )
    import_bundle_parser.set_defaults(handler=run_import_bundle)

    repo_parser = subparsers.add_parser(
        "repo",
        help="Evaluate PCAE behavior against another repository.",
    )
    repo_subparsers = repo_parser.add_subparsers(
        dest="repo_command",
        required=True,
    )

    repo_trial_parser = repo_subparsers.add_parser(
        "trial",
        help="Preview PCAE adoption behavior for a target repo.",
    )
    repo_trial_parser.add_argument("path")
    repo_trial_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview trial results without modifying the target repo.",
    )
    repo_trial_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON trial output.",
    )
    repo_trial_parser.set_defaults(handler=run_repo_trial)

    repo_apply_parser = repo_subparsers.add_parser(
        "apply",
        help="Preview applying PCAE onboarding to a target repo.",
    )
    repo_apply_parser.add_argument("path")
    repo_apply_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview apply actions without modifying the target repo.",
    )
    repo_apply_parser.add_argument(
        "--force",
        action="store_true",
        help="Apply PCAE onboarding templates to the target repo.",
    )
    repo_apply_parser.set_defaults(handler=run_repo_apply)

    architecture_parser = subparsers.add_parser(
        "architecture",
        help="Manage PCAE architecture history.",
    )
    architecture_subparsers = architecture_parser.add_subparsers(
        dest="architecture_command",
        required=True,
    )

    architecture_snapshot_parser = architecture_subparsers.add_parser(
        "snapshot",
        help="Write an architecture check history snapshot.",
    )
    architecture_snapshot_parser.set_defaults(handler=run_architecture_snapshot)

    architecture_history_parser = architecture_subparsers.add_parser(
        "history",
        help="Read the latest architecture history summary.",
    )
    architecture_history_parser.set_defaults(handler=run_architecture_history)

    architecture_metrics_parser = architecture_subparsers.add_parser(
        "metrics",
        help="Summarize architecture history drift metrics.",
    )
    architecture_metrics_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON architecture metrics output.",
    )
    architecture_metrics_parser.set_defaults(handler=run_architecture_metrics)

    architecture_decisions_parser = architecture_subparsers.add_parser(
        "decisions",
        help="List governed architecture decision records.",
    )
    architecture_decisions_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON architecture decisions output.",
    )
    architecture_decisions_parser.set_defaults(handler=run_architecture_decisions)

    architecture_show_parser = architecture_subparsers.add_parser(
        "show",
        help="Show a governed architecture decision record by ID.",
    )
    architecture_show_parser.add_argument(
        "decision_id",
        metavar="DECISION_ID",
        help="Architecture decision record identifier.",
    )
    architecture_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON architecture decision output.",
    )
    architecture_show_parser.set_defaults(handler=run_architecture_show)

    architecture_add_parser = architecture_subparsers.add_parser(
        "add",
        help="Create a governed architecture decision record.",
    )
    architecture_add_parser.add_argument(
        "--title",
        required=True,
        metavar="TEXT",
        help="Decision title.",
    )
    architecture_add_parser.add_argument(
        "--rationale",
        required=True,
        metavar="TEXT",
        help="Rationale for the decision.",
    )
    architecture_add_parser.add_argument(
        "--author",
        required=True,
        metavar="TEXT",
        help="Human author of the decision.",
    )
    architecture_add_parser.add_argument(
        "--status",
        default="accepted",
        metavar="TEXT",
        help="Decision status (default: accepted).",
    )
    architecture_add_parser.add_argument(
        "--alternative",
        action="append",
        default=[],
        metavar="TEXT",
        help="Alternative considered (repeatable).",
    )
    architecture_add_parser.add_argument(
        "--consequence",
        action="append",
        default=[],
        metavar="TEXT",
        help="Consequence of the decision (repeatable).",
    )
    architecture_add_parser.add_argument(
        "--phase-reference",
        default=None,
        metavar="TEXT",
        help="PCAE phase reference (e.g. 36H).",
    )
    architecture_add_parser.add_argument(
        "--contributor",
        action="append",
        default=[],
        metavar="TEXT",
        help="Vendor-neutral contributor identifier (repeatable).",
    )
    architecture_add_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    architecture_add_parser.set_defaults(handler=run_architecture_add)

    architecture_export_parser = architecture_subparsers.add_parser(
        "export",
        help="Export all governed architecture decision records.",
    )
    architecture_export_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON export result.",
    )
    architecture_export_parser.set_defaults(handler=run_architecture_export)

    architecture_validate_parser = architecture_subparsers.add_parser(
        "validate",
        help="Validate governed architecture decision record statuses.",
    )
    architecture_validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON validation result.",
    )
    architecture_validate_parser.set_defaults(handler=run_architecture_validate)

    architecture_restore_session_parser = architecture_subparsers.add_parser(
        "restore-session",
        help="Generate a read-only architecture memory restore summary for fresh AI sessions.",
    )
    architecture_restore_session_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON restore session output.",
    )
    architecture_restore_session_parser.set_defaults(
        handler=run_architecture_restore_session
    )

    task_parser = subparsers.add_parser(
        "task",
        help="Manage PCAE task contracts.",
    )
    task_subparsers = task_parser.add_subparsers(dest="task_command", required=True)

    task_new_parser = task_subparsers.add_parser(
        "new",
        help="Create a structured task contract.",
    )
    task_new_parser.add_argument("title")
    task_new_parser.add_argument("--allowed-zone", action="append", default=[])
    task_new_parser.add_argument("--forbidden-zone", action="append", default=[])
    task_new_parser.set_defaults(handler=run_task_new)

    task_close_parser = task_subparsers.add_parser(
        "close",
        help="Close an active task contract.",
    )
    task_close_parser.add_argument("identifier", nargs="?")
    task_close_parser.set_defaults(handler=run_task_close)

    task_pause_parser = task_subparsers.add_parser(
        "pause",
        help="Pause the latest active task contract.",
    )
    task_pause_parser.set_defaults(handler=run_task_pause)

    task_resume_parser = task_subparsers.add_parser(
        "resume",
        help="Resume the latest paused task contract.",
    )
    task_resume_parser.set_defaults(handler=run_task_resume)

    task_complete_parser = task_subparsers.add_parser(
        "complete",
        help="Complete the latest active task contract.",
    )
    task_complete_parser.set_defaults(handler=run_task_complete)

    task_list_parser = task_subparsers.add_parser(
        "list",
        help="List active and done task contracts.",
    )
    task_list_parser.set_defaults(handler=run_task_list)

    task_show_parser = task_subparsers.add_parser(
        "show",
        help="Show the latest active task contract.",
    )
    task_show_parser.set_defaults(handler=run_task_show)

    task_update_parser = task_subparsers.add_parser(
        "update",
        help="Update the latest active task contract.",
    )
    task_update_parser.add_argument("--goal")
    task_update_parser.add_argument("--mode")
    task_update_parser.add_argument("--allowed-file", action="append")
    task_update_parser.add_argument("--forbidden-file", action="append")
    task_update_parser.add_argument("--allowed-zone", action="append")
    task_update_parser.add_argument("--forbidden-zone", action="append")
    task_update_parser.add_argument("--enforcement-mode")
    task_update_parser.add_argument("--acceptance-check", action="append")
    task_update_parser.set_defaults(handler=run_task_update)

    task_transition_parser = task_subparsers.add_parser(
        "transition",
        help="Complete the current task, create the next one, and refresh session continuity.",
    )
    task_transition_parser.add_argument(
        "--next",
        help="Explicit title for the next active task.",
    )
    task_transition_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    task_transition_parser.set_defaults(handler=run_task_transition)

    hooks_parser = subparsers.add_parser(
        "hooks",
        help="Manage PCAE Git hook integration.",
    )
    hooks_subparsers = hooks_parser.add_subparsers(
        dest="hooks_command",
        required=True,
    )

    hooks_install_parser = hooks_subparsers.add_parser(
        "install",
        help="Configure Git to use .githooks.",
    )
    hooks_install_parser.set_defaults(handler=run_hooks_install)

    session_parser = subparsers.add_parser(
        "session",
        help="Manage PCAE session handoff snapshots.",
    )
    session_subparsers = session_parser.add_subparsers(
        dest="session_command",
        required=True,
    )

    session_write_parser = session_subparsers.add_parser(
        "write",
        help="Write a resumable session snapshot.",
    )
    session_write_parser.set_defaults(handler=run_session_write)

    session_read_parser = session_subparsers.add_parser(
        "read",
        help="Read the current session snapshot.",
    )
    session_read_parser.set_defaults(handler=run_session_read)

    session_update_parser = session_subparsers.add_parser(
        "update",
        help="Update handoff metadata in the current session snapshot.",
    )
    session_update_parser.add_argument("--objective")
    session_update_parser.add_argument("--completed-step")
    session_update_parser.add_argument("--next-step")
    session_update_parser.add_argument("--blocker")
    session_update_parser.add_argument("--warning")
    session_update_parser.add_argument("--note")
    session_update_parser.set_defaults(handler=run_session_update)

    session_start_parser = session_subparsers.add_parser(
        "start",
        help="Summarize the current governed engineering session.",
    )
    session_start_parser.set_defaults(handler=run_session_start)

    session_end_parser = session_subparsers.add_parser(
        "end",
        help="Finalize the current engineering session.",
    )
    session_end_parser.set_defaults(handler=run_session_end)

    session_bootstrap_parser = session_subparsers.add_parser(
        "bootstrap",
        help="Acquire agent lock and initialize a fresh governed session.",
    )
    session_bootstrap_parser.add_argument(
        "--agent-id",
        default=None,
        help=(
            "Agent identifier to acquire the lock for. "
            "Required unless --compact is specified."
        ),
    )
    session_bootstrap_parser.add_argument(
        "--compact",
        action="store_true",
        help=(
            "Generate a compact governed bootstrap prompt without acquiring a lock. "
            "Read-only; does not mutate governance state."
        ),
    )
    session_bootstrap_parser.add_argument(
        "--profile",
        default=None,
        metavar="PROFILE",
        help=(
            "Work-mode profile for compact bootstrap: "
            "implementation, documentation, validation, handoff."
        ),
    )
    session_bootstrap_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON bootstrap result.",
    )
    session_bootstrap_parser.set_defaults(handler=run_session_bootstrap)

    provenance_parser = subparsers.add_parser(
        "provenance",
        help="Inspect PCAE governance provenance history.",
    )
    provenance_subparsers = provenance_parser.add_subparsers(
        dest="provenance_command",
        required=True,
    )

    provenance_status_parser = provenance_subparsers.add_parser(
        "status",
        help="Show provenance history file status and event count.",
    )
    provenance_status_parser.set_defaults(handler=run_provenance_status)

    provenance_timeline_parser = provenance_subparsers.add_parser(
        "timeline",
        help="Show a chronological governance provenance timeline.",
    )
    provenance_timeline_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON timeline output.",
    )
    provenance_timeline_parser.set_defaults(handler=run_provenance_timeline)

    provenance_history_parser = provenance_subparsers.add_parser(
        "history",
        help="Show recorded provenance events.",
    )
    provenance_history_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON provenance history output.",
    )
    provenance_history_parser.add_argument(
        "--event-type",
        default=None,
        help="Filter events by event_type.",
    )
    provenance_history_parser.add_argument(
        "--agent-id",
        default=None,
        help="Filter events by agent_id.",
    )
    provenance_history_parser.set_defaults(handler=run_provenance_history)

    provenance_export_parser = provenance_subparsers.add_parser(
        "export",
        help="Export provenance history to a portable JSON bundle.",
    )
    provenance_export_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON export result.",
    )
    provenance_export_parser.set_defaults(handler=run_provenance_export)

    provenance_sessions_parser = provenance_subparsers.add_parser(
        "sessions",
        help="List governance execution sessions derived from provenance history.",
    )
    provenance_sessions_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON sessions output.",
    )
    provenance_sessions_parser.set_defaults(handler=run_provenance_sessions)

    provenance_session_parser = provenance_subparsers.add_parser(
        "session",
        help="Inspect a specific governance execution session.",
    )
    provenance_session_subparsers = provenance_session_parser.add_subparsers(
        dest="provenance_session_command",
        required=True,
    )
    provenance_session_current_parser = provenance_session_subparsers.add_parser(
        "current",
        help="Show the current active governance session.",
    )
    provenance_session_current_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON current session output.",
    )
    provenance_session_current_parser.set_defaults(handler=run_provenance_session_current)

    provenance_record_parser = provenance_subparsers.add_parser(
        "record",
        help="Append a manual provenance event.",
    )
    provenance_record_parser.add_argument(
        "--event-type",
        required=True,
        help="Event type label (e.g. phase_completed, session.start).",
    )
    provenance_record_parser.add_argument(
        "--summary",
        required=True,
        help="Human-readable summary of the event.",
    )
    provenance_record_parser.set_defaults(handler=run_provenance_record)

    phase_parser = subparsers.add_parser(
        "phase",
        help="Manage governed phase lifecycle.",
    )
    phase_subparsers = phase_parser.add_subparsers(
        dest="phase_command",
        required=True,
    )

    phase_complete_parser = phase_subparsers.add_parser(
        "complete",
        help="Record phase completion and release agent lock.",
    )
    phase_complete_parser.add_argument(
        "--summary",
        required=True,
        help="Summary of the completed phase.",
    )
    phase_complete_parser.set_defaults(handler=run_phase_complete)

    phase_start_parser = phase_subparsers.add_parser(
        "start",
        help="Acquire agent lock and begin a new governed phase.",
    )
    phase_start_parser.add_argument(
        "--agent-id",
        required=True,
        help="Agent identifier for the new phase session.",
    )
    phase_start_parser.set_defaults(handler=run_phase_start)

    phase_handoff_parser = phase_subparsers.add_parser(
        "handoff",
        help="Record phase completion, validate governance, and transfer agent lock.",
    )
    phase_handoff_parser.add_argument(
        "--summary",
        required=True,
        help="Summary of the completed phase.",
    )
    phase_handoff_parser.add_argument(
        "--next-agent",
        default=None,
        help="Agent identifier that will own the next phase session.",
    )
    phase_handoff_parser.add_argument(
        "--work-type",
        default=None,
        metavar="TEXT",
        help="Work type to recommend next agent via orchestration policy.",
    )
    phase_handoff_parser.add_argument(
        "--workflow",
        default=None,
        metavar="TEXT",
        help="Workflow name to validate for handoff guidance.",
    )
    phase_handoff_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON handoff result.",
    )
    phase_handoff_parser.set_defaults(handler=run_phase_handoff)

    multi_agent_governance_audit_parser = subparsers.add_parser(
        "multi-agent-governance-audit",
        help="Audit the complete multi-agent governance architecture (Phase 49F).",
    )
    multi_agent_governance_audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    multi_agent_governance_audit_parser.set_defaults(handler=run_multi_agent_governance_audit)

    governance_state_audit_parser = subparsers.add_parser(
        "governance-state-audit",
        help="Audit PCAE governance state for consistency and integrity (Phase 49G).",
    )
    governance_state_audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    governance_state_audit_parser.set_defaults(handler=run_governance_state_audit)

    governance_state_repair_parser = subparsers.add_parser(
        "governance-state-repair",
        help="Define repair framework for governance state inconsistencies (Phase 49H).",
    )
    governance_state_repair_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    governance_state_repair_parser.set_defaults(handler=run_governance_state_repair)

    task_transition_governance_parser = subparsers.add_parser(
        "task-transition-governance",
        help="Define governance checks for safe task transitions (Phase 49I).",
    )
    task_transition_governance_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    task_transition_governance_parser.set_defaults(handler=run_task_transition_governance)

    session_continuity_governance_parser = subparsers.add_parser(
        "session-continuity-governance",
        help="Define governance checks for session continuity integrity (Phase 49J).",
    )
    session_continuity_governance_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    session_continuity_governance_parser.set_defaults(handler=run_session_continuity_governance)

    governance_invariants_parser = subparsers.add_parser(
        "governance-invariants",
        help="Audit core governance invariants across PCAE workflows (Phase 49K).",
    )
    governance_invariants_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    governance_invariants_parser.set_defaults(handler=run_governance_invariants)

    runtime_safety_invariants_parser = subparsers.add_parser(
        "runtime-safety-invariants",
        help="Audit runtime safety invariants before controlled write authorization (Phase 49L).",
    )
    runtime_safety_invariants_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    runtime_safety_invariants_parser.set_defaults(handler=run_runtime_safety_invariants)

    governance_drift_parser = subparsers.add_parser(
        "governance-drift",
        help="Detect governance drift across tasks, sessions, roadmap, docs, and artifacts (Phase 49M).",
    )
    governance_drift_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    governance_drift_parser.set_defaults(handler=run_governance_drift)

    governance_drift_review_parser = subparsers.add_parser(
        "governance-drift-review",
        help="Define human review workflow for governance drift signals (Phase 49N).",
    )
    governance_drift_review_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    governance_drift_review_parser.set_defaults(handler=run_governance_drift_review)

    agent_lock_governance_parser = subparsers.add_parser(
        "agent-lock-governance",
        help="Governance checks for agent lock lifecycle, stale lock detection, and handoff (Phase 49O).",
    )
    agent_lock_governance_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    agent_lock_governance_parser.set_defaults(handler=run_agent_lock_governance)

    agent_lock_conflicts_parser = subparsers.add_parser(
        "agent-lock-conflicts",
        help="Detect multi-agent lock conflicts, ownership conflicts, and contention (Phase 49P).",
    )
    agent_lock_conflicts_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    agent_lock_conflicts_parser.set_defaults(handler=run_agent_lock_conflicts)

    governance_recovery_plan_parser = subparsers.add_parser(
        "governance-recovery-plan",
        help="Define recovery plans for governance issues across all detected domains (Phase 49Q).",
    )
    governance_recovery_plan_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    governance_recovery_plan_parser.set_defaults(handler=run_governance_recovery_plan)

    write_authorization_parser = subparsers.add_parser(
        "write-authorization",
        help="Define the governed authorization model required before PCAE may allow write-capable execution (Phase 50A).",
    )
    write_authorization_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_authorization_parser.set_defaults(handler=run_write_authorization)

    write_authorization_review_parser = subparsers.add_parser(
        "write-authorization-review",
        help="Define the human review workflow for write authorization candidates (Phase 50B).",
    )
    write_authorization_review_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_authorization_review_parser.set_defaults(handler=run_write_authorization_review)

    write_authorization_decision_parser = subparsers.add_parser(
        "write-authorization-decision",
        help="Define the governed decision artifact produced after write authorization review (Phase 50C).",
    )
    write_authorization_decision_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_authorization_decision_parser.set_defaults(handler=run_write_authorization_decision)

    write_authorization_lifecycle_parser = subparsers.add_parser(
        "write-authorization-lifecycle",
        help="Define expiration and revocation lifecycle governance for write authorization decisions (Phase 50D).",
    )
    write_authorization_lifecycle_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_authorization_lifecycle_parser.set_defaults(handler=run_write_authorization_lifecycle)

    write_plan_parser = subparsers.add_parser(
        "write-plan",
        help="Define the governed write plan model required before any future write-capable execution (Phase 50E).",
    )
    write_plan_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_plan_parser.set_defaults(handler=run_write_plan)

    write_readiness_parser = subparsers.add_parser(
        "write-readiness",
        help="Assess whether a governed write plan satisfies all prerequisites for future controlled write execution (Phase 50F).",
    )
    write_readiness_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_readiness_parser.set_defaults(handler=run_write_readiness)

    write_evidence_parser = subparsers.add_parser(
        "write-evidence",
        help="Define evidence requirements that must exist before a write authorization can be considered ready (Phase 50G).",
    )
    write_evidence_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_evidence_parser.set_defaults(handler=run_write_evidence)

    write_audit_parser = subparsers.add_parser(
        "write-audit",
        help="Define audit requirements that must exist before a write authorization can be considered eligible for execution (Phase 50H).",
    )
    write_audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_audit_parser.set_defaults(handler=run_write_audit)

    write_rollback_verification_parser = subparsers.add_parser(
        "write-rollback-verification",
        help="Define rollback verification requirements that must exist before a write authorization can be considered eligible for execution (Phase 50I).",
    )
    write_rollback_verification_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_rollback_verification_parser.set_defaults(handler=run_write_rollback_verification)

    write_governance_audit_parser = subparsers.add_parser(
        "write-governance-audit",
        help="Audit the complete controlled-write governance chain established in phases 50A–50I (Phase 50J).",
    )
    write_governance_audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_governance_audit_parser.set_defaults(handler=run_write_governance_audit)

    write_recommendation_parser = subparsers.add_parser(
        "write-recommendation",
        help="Determine whether a governed write should be recommended for future consideration based on governance readiness (Phase 50K).",
    )
    write_recommendation_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    write_recommendation_parser.set_defaults(handler=run_write_recommendation)

    execution_request_parser = subparsers.add_parser(
        "execution-request",
        help="Define the governed execution request artifact that serves as the entry point for future controlled execution orchestration (Phase 51A).",
    )
    execution_request_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_request_parser.set_defaults(handler=run_execution_request)

    execution_review_parser = subparsers.add_parser(
        "execution-review",
        help="Define the governed execution review workflow for assessing execution requests against policy (Phase 51B).",
    )
    execution_review_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_review_parser.set_defaults(handler=run_execution_review)

    execution_decision_parser = subparsers.add_parser(
        "execution-decision",
        help="Define the governed execution decision artifact produced after execution review (Phase 51C).",
    )
    execution_decision_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_decision_parser.set_defaults(handler=run_execution_decision)

    execution_lifecycle_parser = subparsers.add_parser(
        "execution-lifecycle",
        help="Define the governed execution lifecycle artifact that tracks request, review, and decision state across their full lifecycle (Phase 51D).",
    )
    execution_lifecycle_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_lifecycle_parser.set_defaults(handler=run_execution_lifecycle)

    execution_plan_parser = subparsers.add_parser(
        "execution-plan",
        help="Define the governed execution plan artifact that describes how a future execution would occur (Phase 51E).",
    )
    execution_plan_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_plan_parser.set_defaults(handler=run_execution_plan)

    execution_readiness_assessment_parser = subparsers.add_parser(
        "execution-readiness-assessment",
        help="Assess whether an execution plan satisfies all prerequisites for future controlled execution (Phase 51F).",
    )
    execution_readiness_assessment_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_readiness_assessment_parser.set_defaults(
        handler=run_execution_readiness_assessment
    )

    execution_evidence_parser = subparsers.add_parser(
        "execution-evidence",
        help="Define evidence requirements that must exist before an execution plan can be eligible for future controlled execution (Phase 51G).",
    )
    execution_evidence_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_evidence_parser.set_defaults(handler=run_execution_evidence)

    execution_audit_parser = subparsers.add_parser(
        "execution-audit",
        help="Define audit requirements that must exist before an execution plan can be eligible for future controlled execution (Phase 51H).",
    )
    execution_audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_audit_parser.set_defaults(handler=run_execution_audit)

    execution_rollback_verification_parser = subparsers.add_parser(
        "execution-rollback-verification",
        help="Define rollback verification requirements that must exist before an execution plan can be eligible for future controlled execution (Phase 51I).",
    )
    execution_rollback_verification_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_rollback_verification_parser.set_defaults(
        handler=run_execution_rollback_verification
    )

    execution_governance_audit_parser = subparsers.add_parser(
        "execution-governance-audit",
        help="Audit the complete execution governance chain established in phases 51A–51I (Phase 51J).",
    )
    execution_governance_audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_governance_audit_parser.set_defaults(handler=run_execution_chain_governance_audit)

    execution_recommendation_parser = subparsers.add_parser(
        "execution-recommendation",
        help="Determine whether a governed execution plan should be recommended based on the 51A–51J governance chain (Phase 51K).",
    )
    execution_recommendation_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    execution_recommendation_parser.set_defaults(handler=run_execution_recommendation)

    task_lifecycle_hardening_parser = subparsers.add_parser(
        "task-lifecycle-hardening",
        help="Harden PCAE task lifecycle validation to detect stale, inconsistent, or ambiguous task state (Phase 52A).",
    )
    task_lifecycle_hardening_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    task_lifecycle_hardening_parser.set_defaults(handler=run_task_lifecycle_hardening)

    session_recovery_parser = subparsers.add_parser(
        "session-recovery",
        help="Define recovery planning for stale, missing, mismatched, or orphaned PCAE session state (Phase 52B).",
    )
    session_recovery_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    session_recovery_parser.set_defaults(handler=run_session_recovery)

    governance_state_recovery_parser = subparsers.add_parser(
        "governance-state-recovery",
        help="Define recovery planning for inconsistent, stale, missing, or corrupted PCAE governance state (Phase 52C).",
    )
    governance_state_recovery_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    governance_state_recovery_parser.set_defaults(handler=run_governance_state_recovery)

    agent_lock_recovery_parser = subparsers.add_parser(
        "agent-lock-recovery",
        help="Define recovery planning for stale, conflicting, orphaned, or mismatched agent lock state (Phase 52D).",
    )
    agent_lock_recovery_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    agent_lock_recovery_parser.set_defaults(handler=run_agent_lock_recovery)

    corruption_recovery_parser = subparsers.add_parser(
        "corruption-recovery",
        help="Define recovery planning for corrupted, malformed, missing, or inconsistent PCAE project state artifacts (Phase 52E).",
    )
    corruption_recovery_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    corruption_recovery_parser.set_defaults(handler=run_corruption_recovery)

    runtime_contract_hardening_parser = subparsers.add_parser(
        "runtime-contract-hardening",
        help="Define and validate runtime contract requirements for deterministic, governable execution interfaces (Phase 52F).",
    )
    runtime_contract_hardening_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    runtime_contract_hardening_parser.set_defaults(handler=run_runtime_contract_hardening)

    sandbox_hardening_parser = subparsers.add_parser(
        "sandbox-hardening",
        help="Define and validate sandbox isolation requirements for constrained, deterministic runtime execution (Phase 52G).",
    )
    sandbox_hardening_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    sandbox_hardening_parser.set_defaults(handler=run_sandbox_hardening)

    timeout_hardening_parser = subparsers.add_parser(
        "timeout-hardening",
        help="Define and validate timeout governance requirements for bounded, recoverable runtime execution (Phase 52H).",
    )
    timeout_hardening_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    timeout_hardening_parser.set_defaults(handler=run_timeout_hardening)

    output_integrity_verification_parser = subparsers.add_parser(
        "output-integrity-verification",
        help="Define and validate output integrity requirements for deterministic, attributable runtime outputs (Phase 52I).",
    )
    output_integrity_verification_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    output_integrity_verification_parser.set_defaults(
        handler=run_output_integrity_verification
    )

    concurrency_safety_parser = subparsers.add_parser(
        "concurrency-safety",
        help="Define and validate concurrency safety for simultaneous agents, sessions, and governance workflows (Phase 52J).",
    )
    concurrency_safety_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    concurrency_safety_parser.set_defaults(handler=run_concurrency_safety)

    parallel_agent_coordination_parser = subparsers.add_parser(
        "parallel-agent-coordination",
        help="Define and validate coordination requirements for agents operating in parallel (Phase 52K).",
    )
    parallel_agent_coordination_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    parallel_agent_coordination_parser.set_defaults(
        handler=run_parallel_agent_coordination
    )

    multi_agent_state_consistency_parser = subparsers.add_parser(
        "multi-agent-state-consistency",
        help="Define and validate shared-state consistency across coordinated agents (Phase 52L).",
    )
    multi_agent_state_consistency_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    multi_agent_state_consistency_parser.set_defaults(
        handler=run_multi_agent_state_consistency
    )

    conflict_resolution_engine_parser = subparsers.add_parser(
        "conflict-resolution-engine",
        help="Detect, classify, escalate, and plan advisory resolution for multi-agent conflicts (Phase 52M).",
    )
    conflict_resolution_engine_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    conflict_resolution_engine_parser.set_defaults(
        handler=run_conflict_resolution_engine
    )

    chaos_testing_parser = subparsers.add_parser(
        "chaos-testing",
        help="Define chaos testing scenarios for PCAE governance and recovery workflows (Phase 52N).",
    )
    chaos_testing_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    chaos_testing_parser.set_defaults(handler=run_chaos_testing)

    failure_injection_parser = subparsers.add_parser(
        "failure-injection",
        help="Define controlled failure-injection scenarios for PCAE detection and recovery validation (Phase 52O).",
    )
    failure_injection_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    failure_injection_parser.set_defaults(handler=run_failure_injection)

    corruption_simulation_parser = subparsers.add_parser(
        "corruption-simulation",
        help="Define controlled corruption simulation scenarios for PCAE detection and recovery validation (Phase 52P).",
    )
    corruption_simulation_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    corruption_simulation_parser.set_defaults(handler=run_corruption_simulation)

    recovery_validation_parser = subparsers.add_parser(
        "recovery-validation",
        help="Validate recovery plan completeness for chaos, failure, and corruption scenarios (Phase 52Q).",
    )
    recovery_validation_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    recovery_validation_parser.set_defaults(handler=run_recovery_validation)

    rir_parser = subparsers.add_parser(
        "runtime-integration-readiness",
        help="Assess readiness for runtime integration across all governance layers (Phase 54A).",
    )
    rir_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    rir_parser.set_defaults(handler=run_runtime_integration_readiness)

    rori_parser = subparsers.add_parser(
        "read-only-runtime-invocation",
        help="Plan and validate governed read-only runtime invocation requirements (Phase 55A).",
    )
    rori_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    rori_parser.set_defaults(handler=run_read_only_runtime_invocation)

    rop_parser = subparsers.add_parser(
        "runtime-output-persistence",
        help="Define persistence requirements for future runtime invocation outputs (Phase 56A).",
    )
    rop_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    rop_parser.set_defaults(handler=run_runtime_output_persistence)

    ror_parser = subparsers.add_parser(
        "runtime-output-review",
        help="Define governed human review workflow for future runtime invocation outputs (Phase 57A).",
    )
    ror_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    ror_parser.set_defaults(handler=run_runtime_output_review)

    marep_parser = subparsers.add_parser(
        "multi-agent-read-only-execution",
        help="Define governed multi-agent read-only execution pilot model (Phase 58A).",
    )
    marep_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    marep_parser.set_defaults(handler=run_multi_agent_read_only_execution)

    cwdr_parser = subparsers.add_parser(
        "controlled-write-dry-run",
        help="Define governed dry-run model for future controlled write execution (Phase 59A).",
    )
    cwdr_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    cwdr_parser.set_defaults(handler=run_controlled_write_dry_run)

    sfwp_parser = subparsers.add_parser(
        "single-file-write-pilot",
        help="Define first governed single-file write pilot model (Phase 60A).",
    )
    sfwp_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    sfwp_parser.set_defaults(handler=run_single_file_write_pilot)

    rr_parser = subparsers.add_parser(
        "runtime-registry",
        help="Define governed runtime registry model for PCAE (Phase 61A).",
    )
    rr_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    rr_parser.set_defaults(handler=run_runtime_registry)

    rd_parser = subparsers.add_parser(
        "runtime-discovery",
        help="Define governed runtime discovery readiness model for PCAE (Phase 61B).",
    )
    rd_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    rd_parser.set_defaults(handler=run_runtime_discovery_assessment)

    rci_parser = subparsers.add_parser(
        "runtime-capability-inventory",
        help="Define governed runtime capability inventory model for PCAE (Phase 61C).",
    )
    rci_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    rci_parser.set_defaults(handler=run_runtime_capability_inventory)

    rtm_parser = subparsers.add_parser(
        "runtime-trust-model",
        help="Define governed runtime trust model for PCAE (Phase 61D).",
    )
    rtm_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    rtm_parser.set_defaults(handler=run_runtime_trust_model)

    tlg_parser = subparsers.add_parser(
        "task-lifecycle-governance",
        help="Inspect and harden task/phase/session lifecycle governance relationships (Phase 61E).",
    )
    tlg_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    tlg_parser.set_defaults(handler=run_task_lifecycle_governance)

    ahm_parser = subparsers.add_parser(
        "agent-handoff-modernization",
        help="Modernize PCAE agent handoff continuity requirements without rewriting handoff state (Phase 61F).",
    )
    ahm_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    ahm_parser.set_defaults(handler=run_agent_handoff_modernization)

    rcv_parser = subparsers.add_parser(
        "roadmap-continuity",
        help="Validate roadmap/task/session continuity before real runtime invocation work (Phase 61G).",
    )
    rcv_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    rcv_parser.set_defaults(handler=run_roadmap_continuity)

    hsr_parser = subparsers.add_parser(
        "handoff-state-refresh",
        help="Refresh and modernize PCAE handoff state for accurate, current, roadmap-aware continuation guidance (Phase 61I).",
    )
    hsr_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    hsr_parser.set_defaults(handler=run_handoff_state_refresh)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
