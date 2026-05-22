from __future__ import annotations

import argparse

from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


def run_task_new(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    contract = create_task_contract(root, args.title)

    print(f"Created task contract: {contract.relative_path.as_posix()}")
    return 0
