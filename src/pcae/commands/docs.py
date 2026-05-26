from __future__ import annotations

import argparse

from pcae.core.docs import (
    COMMANDS_RELATIVE_PATH,
    generate_commands_reference,
    render_commands_reference,
)
from pcae.core.paths import HarnessPath


def run_docs_commands(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()

    if args.dry_run:
        print(f"Would write {COMMANDS_RELATIVE_PATH.as_posix()}:")
        print(render_commands_reference(), end="")
        return 0

    try:
        result = generate_commands_reference(root, force=args.force)
    except FileExistsError as error:
        print(str(error))
        return 1

    if result.overwritten:
        print(f"Overwritten: {result.relative_path.as_posix()}")
    elif result.created:
        print(f"Created: {result.relative_path.as_posix()}")
    else:
        print(f"Already present: {result.relative_path.as_posix()}")
    return 0
