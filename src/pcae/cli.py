from __future__ import annotations

import argparse
from collections.abc import Sequence

from pcae.commands.architecture import (
    run_architecture_history,
    run_architecture_metrics,
    run_architecture_snapshot,
)
from pcae.commands.check import run_check
from pcae.commands.hooks import run_hooks_install
from pcae.commands.init import run_init
from pcae.commands.inspect import run_inspect
from pcae.commands.session import (
    run_session_read,
    run_session_update,
    run_session_write,
)
from pcae.commands.task import run_task_close, run_task_list, run_task_new


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
    init_parser.set_defaults(handler=run_init)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect PCAE memory files and local harness wiring.",
    )
    inspect_parser.set_defaults(handler=run_inspect)

    check_parser = subparsers.add_parser(
        "check",
        help="Run advisory PCAE validation checks.",
    )
    check_parser.set_defaults(handler=run_check)

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

    task_list_parser = task_subparsers.add_parser(
        "list",
        help="List active and done task contracts.",
    )
    task_list_parser.set_defaults(handler=run_task_list)

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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
