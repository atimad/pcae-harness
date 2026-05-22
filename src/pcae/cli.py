from __future__ import annotations

import argparse
from collections.abc import Sequence

from pcae.commands.check import run_check
from pcae.commands.hooks import run_hooks_install
from pcae.commands.init import run_init
from pcae.commands.inspect import run_inspect
from pcae.commands.task import run_task_new


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
    task_new_parser.set_defaults(handler=run_task_new)

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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
