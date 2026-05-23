from __future__ import annotations

import argparse

from pcae.core.architecture import write_architecture_history_snapshot
from pcae.core.check import run_checks
from pcae.core.paths import HarnessPath


def run_architecture_snapshot(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    check_result = run_checks(root)
    snapshot = write_architecture_history_snapshot(root, check_result)

    print(f"Wrote architecture history: {snapshot.relative_path.as_posix()}")
    print(f"Entries: {len(snapshot.entries)}")
    return 0
