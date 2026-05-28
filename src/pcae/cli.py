from __future__ import annotations

import argparse
from collections.abc import Sequence

from pcae.commands.analytics import run_analytics_risk, run_analytics_trends
from pcae.commands.agent import (
    run_agent_acquire,
    run_agent_release,
    run_agent_status,
)
from pcae.commands.architecture import (
    run_architecture_history,
    run_architecture_metrics,
    run_architecture_snapshot,
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
