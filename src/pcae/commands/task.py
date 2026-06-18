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
    TaskFinishResult,
    TaskMemoryDiagnostics,
    TaskTransitionRecord,
    TaskUpdate,
    close_active_task_by_identifier,
    close_latest_active_task,
    complete_latest_active_task,
    create_task_contract,
    diagnose_task_memory,
    find_latest_active_task,
    finish_active_task,
    repair_task_memory,
    transition_active_task,
    validate_task_finish,
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

    allowed_files = tuple(args.allowed_file) if args.allowed_file else ()
    forbidden_files = tuple(args.forbidden_file) if args.forbidden_file else ()
    acceptance_checks = tuple(args.acceptance_check) if args.acceptance_check else ()
    goal = args.goal if args.goal else "TBD"
    mode = args.mode if args.mode else "implementation"
    enforcement_mode = args.enforcement_mode if args.enforcement_mode else "TBD"

    contract = create_task_contract(
        root,
        args.title,
        goal=goal,
        mode=mode,
        allowed_files=allowed_files,
        forbidden_files=forbidden_files,
        allowed_zones=allowed_zones,
        forbidden_zones=forbidden_zones,
        enforcement_mode=enforcement_mode,
        acceptance_checks=acceptance_checks,
    )

    from pcae.core.session import write_session_snapshot

    try:
        write_session_snapshot(root)
    except Exception:
        pass

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


def run_task_finish(args: argparse.Namespace) -> int:
    import subprocess

    root = HarnessPath.cwd()
    skip_checks = getattr(args, "skip_checks", False)
    commit_message = getattr(args, "commit", None)

    if commit_message:
        from pcae.core.git_status import read_git_changes

        pre_changes = read_git_changes(root)
        if pre_changes:
            blocker = (
                f"Working tree has {len(pre_changes)} pre-existing change(s). "
                "Commit or stash them before using --commit."
            )
            if args.json:
                print(json.dumps({"blockers": [blocker], "committed": False, "finished": False}, indent=2, sort_keys=True))
            else:
                print(f"Task finish blocked.\n  - {blocker}")
            return 1

    validation = validate_task_finish(root, skip_checks=skip_checks)
    if not validation.safe_to_finish:
        if args.json:
            print(
                json.dumps(
                    {
                        "blockers": list(validation.blockers),
                        "committed": False if commit_message else None,
                        "finished": False,
                        "task_id": (
                            validation.active_task.task_id
                            if validation.active_task
                            else None
                        ),
                        "warnings": list(validation.warnings),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print("Task finish blocked.")
            for blocker in validation.blockers:
                print(f"  - {blocker}")
        return 1

    active_task_path = validation.active_task.path.relative_to(root.path)

    try:
        result = finish_active_task(root, skip_checks=skip_checks)
    except ValueError as error:
        print(str(error))
        return 1

    commit_hash = None
    if commit_message:
        paths_to_stage = [str(active_task_path)]
        for p in result.updated_files:
            paths_to_stage.append(p.as_posix())
        paths_to_stage.append(
            result.completed_task.destination_path.relative_to(root.path).as_posix()
        )
        unique_paths = list(dict.fromkeys(paths_to_stage))

        stageable_paths = []
        for p in unique_paths:
            check_ignored = subprocess.run(
                ["git", "check-ignore", "-q", p],
                cwd=root.path,
                capture_output=True,
            )
            if check_ignored.returncode != 0:
                stageable_paths.append(p)

        try:
            if stageable_paths:
                subprocess.run(
                    ["git", "add", "--"] + stageable_paths,
                    cwd=root.path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            commit_result = subprocess.run(
                ["git", "commit", "--no-verify", "-m", commit_message],
                cwd=root.path,
                check=True,
                capture_output=True,
                text=True,
            )
            for line in commit_result.stdout.splitlines():
                if line.startswith("["):
                    parts = line.split()
                    if len(parts) >= 2:
                        commit_hash = parts[1].rstrip("]")
                    break
        except subprocess.CalledProcessError as error:
            if args.json:
                print(json.dumps({"committed": False, "error": error.stderr.strip(), "finished": True, "task_id": result.completed_task.task_id}, indent=2, sort_keys=True))
            else:
                print(f"Task finished but commit failed: {error.stderr.strip()}")
            return 1

    if args.json:
        data = {
            "finished": True,
            "task_id": result.completed_task.task_id,
            "title": result.completed_task.title,
            "moved_to": result.completed_task.destination_path.relative_to(
                root.path
            ).as_posix(),
            "updated_files": [p.as_posix() for p in result.updated_files],
            "warnings": list(result.warnings),
        }
        if commit_message:
            data["committed"] = True
            data["commit_hash"] = commit_hash
            data["commit_message"] = commit_message
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"Finished task: {result.completed_task.task_id}")
        print(f"Title: {result.completed_task.title}")
        print(
            f"Moved to: {result.completed_task.destination_path.relative_to(root.path).as_posix()}"
        )
        if result.updated_files:
            print("Updated files:")
            for path in result.updated_files:
                print(f"  - {path.as_posix()}")
        if commit_hash:
            print(f"Committed: {commit_hash}")
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

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


def run_doctor_task_memory(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    fix = getattr(args, "fix", False)
    dry_run = getattr(args, "dry_run", False)

    if fix:
        result = repair_task_memory(root, dry_run=dry_run)
        if args.json:
            print(json.dumps({
                "dry_run": dry_run,
                "post_findings": [
                    {"check": f.check, "message": f.message, "severity": f.severity}
                    for f in result.post_findings
                ],
                "pre_findings": [
                    {"check": f.check, "message": f.message, "severity": f.severity}
                    for f in result.pre_findings
                ],
                "repairs": [
                    {"action": r.action, "check": r.check, "path": r.path}
                    for r in result.repairs
                ],
                "skipped": [
                    {"check": f.check, "message": f.message, "severity": f.severity}
                    for f in result.skipped
                ],
            }, indent=2, sort_keys=True))
        else:
            if dry_run:
                print("Task memory repair (dry run)")
            else:
                print("Task memory repair")
            if result.repairs:
                print("Repairs:" if not dry_run else "Would repair:")
                for repair in result.repairs:
                    print(f"  [{repair.check}] {repair.action} → {repair.path}")
            if result.skipped:
                print("Skipped (requires human action):")
                for finding in result.skipped:
                    print(f"  [{finding.severity}] {finding.message}")
            if not dry_run:
                post_count = len(result.post_findings)
                if post_count == 0:
                    print("Post-fix: clean")
                else:
                    print(f"Post-fix: {post_count} finding(s) remaining")
        return 0

    diagnostics = diagnose_task_memory(root)

    if args.json:
        print(
            json.dumps(
                {
                    "clean": diagnostics.clean,
                    "findings": [
                        {
                            "check": f.check,
                            "severity": f.severity,
                            "message": f.message,
                        }
                        for f in diagnostics.findings
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        if diagnostics.clean:
            print("Task memory: clean")
            print("No inconsistencies detected.")
        else:
            print("Task memory: issues detected")
            for finding in diagnostics.findings:
                print(f"  [{finding.severity}] {finding.message}")

    return 1 if diagnostics.has_errors else 0
