from __future__ import annotations

import argparse

from pcae.core.ci import (
    GITHUB_WORKFLOW_RELATIVE_PATH,
    generate_github_actions_workflow,
    render_github_actions_workflow,
)
from pcae.core.paths import HarnessPath


def run_ci_generate_github(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()

    if args.dry_run:
        print(f"Would write {GITHUB_WORKFLOW_RELATIVE_PATH.as_posix()}:")
        print(render_github_actions_workflow(), end="")
        return 0

    try:
        result = generate_github_actions_workflow(root, force=args.force)
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
