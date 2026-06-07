from __future__ import annotations

import argparse
import json

from pcae.core.check import run_checks
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.session import SessionUpdate, update_session_snapshot, write_session_snapshot
from pcae.core.status import check_project_status_coherence
from pcae.core.policy import load_policy
from pcae.core.tasks import (
    ActiveTask,
    TaskTransitionRecord,
    TaskUpdate,
    close_active_task_by_identifier,
    close_latest_active_task,
    complete_latest_active_task,
    create_task_contract,
    find_latest_active_task,
    transition_active_task,
    validate_task_transition,
    pause_latest_active_task,
    read_task_summaries,
    resume_latest_paused_task,
    TaskSummary,
    update_latest_active_task,
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


def run_task_pause(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    paused_task = pause_latest_active_task(root)
    if paused_task is None:
        print("No active task contract found to pause.")
        return 1

    print(f"Paused task: {paused_task.task_id}")
    print(f"Title: {paused_task.title}")
    return 0


def run_task_resume(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    resumed_task = resume_latest_paused_task(root)
    if resumed_task is None:
        print("No paused task contract found to resume.")
        return 1

    print(f"Resumed task: {resumed_task.task_id}")
    print(f"Title: {resumed_task.title}")
    return 0


def run_task_complete(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    completed_task = complete_latest_active_task(root)
    if completed_task is None:
        print("No active task contract found to complete.")
        return 1

    print(f"Completed task: {completed_task.task_id}")
    print(f"Title: {completed_task.title}")
    print(f"Moved to: {completed_task.destination_path.relative_to(root.path).as_posix()}")
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


def run_task_update(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    active_task = find_latest_active_task(root)
    if active_task is None:
        print("No active task contract found in tasks/active/.")
        return 1

    allowed_zones = tuple(args.allowed_zone or ())
    forbidden_zones = tuple(args.forbidden_zone or ())
    validation_error = validate_requested_zones(root, allowed_zones + forbidden_zones)
    if validation_error is not None:
        print(validation_error)
        return 1

    if args.enforcement_mode is not None and args.enforcement_mode not in {
        "advisory",
        "strict",
        "TBD",
    }:
        print("Invalid enforcement mode: expected advisory, strict, or TBD.")
        return 1

    updated_task = update_latest_active_task(
        root,
        TaskUpdate(
            goal=args.goal,
            mode=args.mode,
            allowed_files=(
                tuple(args.allowed_file)
                if args.allowed_file is not None
                else None
            ),
            forbidden_files=(
                tuple(args.forbidden_file)
                if args.forbidden_file is not None
                else None
            ),
            allowed_zones=(
                allowed_zones
                if args.allowed_zone is not None
                else None
            ),
            forbidden_zones=(
                forbidden_zones
                if args.forbidden_zone is not None
                else None
            ),
            enforcement_mode=args.enforcement_mode,
            acceptance_checks=(
                tuple(args.acceptance_check)
                if args.acceptance_check is not None
                else None
            ),
        ),
    )
    if updated_task is None:
        print("No active task contract found in tasks/active/.")
        return 1

    print(f"Updated task: {updated_task.task_id}")
    print(f"Title: {updated_task.title}")
    return 0


def run_task_transition(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    validation = validate_task_transition(root, args.next)
    if not validation.safe_to_complete:
        if args.json:
            print(
                json.dumps(
                    {
                        "blockers": list(validation.blockers),
                        "next_title": validation.next_title,
                        "safe_to_complete": False,
                        "warnings": list(validation.warnings),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print("Task transition blocked.")
            for blocker in validation.blockers:
                print(f"  - {blocker}")
        return 1

    try:
        transition = transition_active_task(root, args.next)
    except ValueError as error:
        print(str(error))
        return 1

    session_snapshot = write_session_snapshot(root)
    session_snapshot = update_session_snapshot(
        root,
        SessionUpdate(
            objective=transition.next_task.title,
            completed_step=(
                f"Completed task {transition.completed_task.task_id}: "
                f"{transition.completed_task.title}"
            ),
            next_step=f"Continue active task {transition.next_task.task_id}.",
        ),
    )
    coherence = check_project_status_coherence(root)
    health = build_health_data(root)
    check_result = run_checks(root)

    if args.json:
        print(json.dumps(task_transition_json(transition, session_snapshot.relative_path.as_posix(), coherence.coherent, health, check_result), indent=2, sort_keys=True))
    else:
        print_task_transition_summary(
            transition,
            session_snapshot.relative_path.as_posix(),
            coherence.coherent,
            health,
            check_result,
        )

    return 0 if coherence.coherent and health["overall_status"] == "healthy" and check_result.passed else 1


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


def print_task_transition_summary(
    transition: TaskTransitionRecord,
    session_path: str,
    coherence_passed: bool,
    health: dict,
    check_result,
) -> None:
    print("Task transition complete.")
    print(f"Completed task: {transition.completed_task.task_id}")
    print(f"Completed title: {transition.completed_task.title}")
    print(
        "Moved to: "
        f"{transition.completed_task.destination_path.relative_to(HarnessPath.cwd().path).as_posix()}"
    )
    print(f"Next active task: {transition.next_task.task_id}")
    print(f"Next title: {transition.next_task.title}")
    print(f"Created: {transition.next_task.relative_path.as_posix()}")
    print(f"Session refreshed: {session_path}")
    print(f"Status coherence: {'passed' if coherence_passed else 'failed'}")
    print(f"Health: {health['overall_status']}")
    print(f"Check: {'passed' if check_result.passed else 'failed'}")
    if transition.warnings:
        print("Warnings:")
        for warning in transition.warnings:
            print(f"  - {warning}")
    print("Updated files:")
    for path in transition.updated_files:
        print(f"  - {path.as_posix()}")


def task_transition_json(
    transition: TaskTransitionRecord,
    session_path: str,
    coherence_passed: bool,
    health: dict,
    check_result,
) -> dict[str, object]:
    return {
        "check_passed": check_result.passed,
        "completed_task": {
            "id": transition.completed_task.task_id,
            "title": transition.completed_task.title,
            "path": transition.completed_task.destination_path.relative_to(
                HarnessPath.cwd().path
            ).as_posix(),
        },
        "health_status": health["overall_status"],
        "next_active_task": {
            "id": transition.next_task.task_id,
            "title": transition.next_task.title,
            "path": transition.next_task.relative_path.as_posix(),
        },
        "session_path": session_path,
        "status_coherence_passed": coherence_passed,
        "updated_files": [path.as_posix() for path in transition.updated_files],
        "warnings": list(transition.warnings),
    }
