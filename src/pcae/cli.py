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
    run_execution_framework_design,
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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
