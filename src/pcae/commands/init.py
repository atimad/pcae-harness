from __future__ import annotations

import argparse

from pcae.core.paths import HarnessPath
from pcae.core.templates import INIT_TEMPLATES
from pcae.core.writer import WriteResult, write_missing_files


def init_harness(root: HarnessPath) -> list[WriteResult]:
    return write_missing_files(root, INIT_TEMPLATES)


def run_init(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    results = init_harness(root)

    created = [result for result in results if result.created]
    skipped = [result for result in results if not result.created]

    print(f"PCAE initialized in {root.path}")
    if created:
        print("Created:")
        for result in created:
            print(f"  {result.relative_path.as_posix()}")
    if skipped:
        print("Already present:")
        for result in skipped:
            print(f"  {result.relative_path.as_posix()}")

    return 0
