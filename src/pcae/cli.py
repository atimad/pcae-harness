from __future__ import annotations

import argparse
from collections.abc import Sequence

from pcae.commands.init import run_init


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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
