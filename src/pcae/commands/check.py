from __future__ import annotations

import argparse

from pcae.core.check import run_checks
from pcae.core.paths import HarnessPath


def run_check(args: argparse.Namespace) -> int:
    result = run_checks(HarnessPath.cwd())

    if result.active_task_id is not None:
        print(f"Active task: {result.active_task_id}")
        print(f"Title: {result.active_task_title}")
    else:
        print("Active task: none")

    if result.architecture_zones_touched:
        print("Architecture zones touched:")
        for zone in result.architecture_zones_touched:
            print(f"  {zone.name}: {zone.file_count} files")

    for warning in result.warnings:
        print(f"  - warning: {warning.text}")

    for info in result.infos:
        print(f"  - info: {info.text}")

    if result.passed:
        print("PCAE check passed.")
        return 0

    print("PCAE check found violations:")
    for violation in result.violations:
        print(f"  - {violation.text}")

    return 1
