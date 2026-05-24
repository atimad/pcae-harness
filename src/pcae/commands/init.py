from __future__ import annotations

import argparse

from pcae.core.paths import HarnessPath
from pcae.core.templates import FORCE_MANAGED_TEMPLATES, INIT_TEMPLATES
from pcae.core.writer import (
    WritePlan,
    WriteResult,
    plan_missing_files,
    write_missing_files,
)


def init_harness(root: HarnessPath, force: bool = False) -> list[WriteResult]:
    force_managed = FORCE_MANAGED_TEMPLATES if force else None
    return write_missing_files(root, INIT_TEMPLATES, force_managed=force_managed)


def run_init(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    if args.dry_run:
        force_managed = FORCE_MANAGED_TEMPLATES if args.force else None
        plans = plan_missing_files(root, INIT_TEMPLATES, force_managed=force_managed)
        print(f"PCAE init dry run in {root.path}")
        print_plan_section("Would create directories:", plans, "directory", True)
        print_plan_section("Would create files:", plans, "file", True)
        print_overwrite_plan_section("Would overwrite files:", plans)
        print_plan_section("Already present directories:", plans, "directory", False)
        print_plan_section("Already present files:", plans, "file", False)
        print_plan_section("Would skip files:", plans, "file", False)
        return 0

    results = init_harness(root, force=args.force)

    created = [result for result in results if result.created]
    overwritten = [result for result in results if result.overwritten]
    skipped = [
        result
        for result in results
        if not result.created and not result.overwritten
    ]

    print(f"PCAE initialized in {root.path}")
    if created:
        print("Created:")
        for result in created:
            print(f"  {result.relative_path.as_posix()}")
    if overwritten:
        print("Overwritten:")
        for result in overwritten:
            print(f"  {result.relative_path.as_posix()}")
    if skipped:
        print("Already present:")
        for result in skipped:
            print(f"  {result.relative_path.as_posix()}")

    return 0


def print_plan_section(
    title: str,
    plans: list[WritePlan],
    kind: str,
    would_create: bool,
) -> None:
    matching = [
        plan
        for plan in plans
        if plan.kind == kind and plan.would_create == would_create
        and not (title == "Would skip files:" and plan.would_overwrite)
    ]
    if not matching:
        return

    print(title)
    for plan in matching:
        print(f"  {plan.relative_path.as_posix()}")


def print_overwrite_plan_section(title: str, plans: list[WritePlan]) -> None:
    matching = [plan for plan in plans if plan.would_overwrite]
    if not matching:
        return

    print(title)
    for plan in matching:
        print(f"  {plan.relative_path.as_posix()}")
