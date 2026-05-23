from __future__ import annotations

import argparse

from pcae.core.paths import HarnessPath
from pcae.core.tasks import (
    close_active_task_by_identifier,
    close_latest_active_task,
    create_task_contract,
)


def run_task_new(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    contract = create_task_contract(root, args.title)

    print(f"Created task contract: {contract.relative_path.as_posix()}")
    return 0


def run_task_close(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    if args.identifier is None:
        closed_task = close_latest_active_task(root)
    else:
        closed_task = close_active_task_by_identifier(root, args.identifier)

    if closed_task is None:
        if args.identifier is None:
            print("No active task contract found in tasks/active/.")
        else:
            print(f"No active task contract found for: {args.identifier}")
        return 1

    print(f"Closed task: {closed_task.task_id}")
    print(f"Title: {closed_task.title}")
    print(f"Moved to: {closed_task.destination_path.relative_to(root.path).as_posix()}")
    return 0
