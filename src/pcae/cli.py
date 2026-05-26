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
from pcae.commands.daemon import (
    default_watch_interval_seconds,
    run_daemon,
    run_daemon_status,
    run_daemon_watch,
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
from pcae.commands.hooks import run_hooks_install
from pcae.commands.import_ import run_import_bundle
from pcae.commands.init import run_init
from pcae.commands.inspect import run_inspect
from pcae.commands.pipeline import run_pipeline, run_pipeline_list
from pcae.commands.repo import run_repo_apply, run_repo_trial
from pcae.commands.session import (
    run_session_end,
    run_session_read,
    run_session_start,
    run_session_update,
    run_session_write,
)
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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
