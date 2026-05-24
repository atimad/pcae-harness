from __future__ import annotations

import argparse

from pcae.core.paths import HarnessPath
from pcae.core.policy import load_policy
from pcae.core.tasks import (
    ActiveTask,
    close_active_task_by_identifier,
    close_latest_active_task,
    create_task_contract,
    find_latest_active_task,
    read_task_summaries,
    TaskSummary,
)


def run_task_new(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    allowed_zones = tuple(args.allowed_zone)
    forbidden_zones = tuple(args.forbidden_zone)
    validation_error = validate_requested_zones(root, allowed_zones + forbidden_zones)
    if validation_error is not None:
        print(validation_error)
        return 1

    contract = create_task_contract(
        root,
        args.title,
        allowed_zones=allowed_zones,
        forbidden_zones=forbidden_zones,
    )

    print(f"Created task contract: {contract.relative_path.as_posix()}")
    return 0


def validate_requested_zones(root: HarnessPath, requested_zones: tuple[str, ...]) -> str | None:
    if not requested_zones:
        return None

    policy = load_policy(root)
    if not policy.file_exists:
        return None
    if not policy.valid:
        return policy.error or "Invalid policy file."

    known_zones = set(policy.architecture_zones)
    for zone in requested_zones:
        if zone not in known_zones:
            return f"Unknown architecture zone: {zone}"
    return None


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


def run_task_list(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    active_tasks = read_task_summaries(root, "active")
    done_tasks = read_task_summaries(root, "done")

    if not active_tasks and not done_tasks:
        print("No task contracts found.")
        return 0

    print_task_section("Active tasks", active_tasks)
    print_task_section("Done tasks", done_tasks)
    return 0


def run_task_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    active_task = find_latest_active_task(root)
    if active_task is None:
        print("No active task contract found in tasks/active/.")
        return 1

    print(format_active_task(active_task))
    return 0


def print_task_section(title: str, tasks: tuple[TaskSummary, ...]) -> None:
    print(f"{title}:")
    if not tasks:
        print("  none")
        return

    for task in tasks:
        print(f"  [{task.status}] {task.task_id} - {task.title}")


def format_active_task(active_task: ActiveTask) -> str:
    lines = [
        "Active task:",
        f"  Task ID: {active_task.task_id}",
        f"  Title: {active_task.title}",
        f"  Status: {active_task.status}",
        f"  Mode: {active_task.mode}",
        f"  Goal: {active_task.goal or 'TBD'}",
        "Allowed files:",
        *format_items(active_task.allowed_files),
        "Forbidden files:",
        *format_items(active_task.forbidden_files),
        "Allowed zones:",
        *format_items(active_task.allowed_zones),
        "Forbidden zones:",
        *format_items(active_task.forbidden_zones),
        "Allowed dependencies:",
        *format_items(active_task.allowed_dependencies),
        "Forbidden dependencies:",
        *format_items(active_task.forbidden_dependencies),
        f"Enforcement mode: {active_task.enforcement_mode or 'TBD'}",
        "Acceptance checks:",
        *format_items(active_task.acceptance_checks),
        "Documentation requirements:",
        *format_items(active_task.documentation_requirements),
    ]
    return "\n".join(lines)


def format_items(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["  - none"]
    return [f"  - {item}" for item in items]
