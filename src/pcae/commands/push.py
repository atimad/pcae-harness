from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import subprocess

from pcae.core.check import run_checks
from pcae.core.git_status import read_git_branch, read_git_changes
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.tasks import diagnose_task_memory


@dataclass(frozen=True)
class PushReadiness:
    branch: str
    clean: bool
    unpushed: int
    health_ok: bool
    check_ok: bool
    doctor_ok: bool
    doctor_warnings: bool
    mode: str
    ready: bool
    change_count: int
    review_status: str


def assess_push_readiness(root: HarnessPath) -> PushReadiness:
    changes = read_git_changes(root)
    branch = read_git_branch(root)
    unpushed = _count_unpushed_commits(root)
    health = build_health_data(root)
    check_result = run_checks(root)
    diagnostics = diagnose_task_memory(root)

    clean = not changes
    from pcae.core.health import is_healthy

    health_ok = is_healthy(health)
    idle = health.get("idle", False)
    check_ok = check_result.passed
    doctor_ok = not diagnostics.has_errors

    mode = _determine_mode(
        clean=clean,
        health_ok=health_ok,
        idle=idle,
        check_ok=check_ok,
        doctor_ok=doctor_ok,
        unpushed=unpushed,
        check_result=check_result,
        root=root,
    )

    ready = mode in ("active_task", "post_finish_closure")

    from pcae.core.review import lifecycle_review_status
    from pcae.core.tasks import find_latest_active_task

    active_task = find_latest_active_task(root)
    task_id = active_task.task_id if active_task else None
    review = lifecycle_review_status(root, task_id)

    return PushReadiness(
        branch=branch,
        clean=clean,
        unpushed=unpushed,
        health_ok=health_ok,
        check_ok=check_ok,
        doctor_ok=doctor_ok,
        doctor_warnings=diagnostics.has_warnings,
        mode=mode,
        ready=ready,
        change_count=len(changes),
        review_status=review,
    )


def run_push_check(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    readiness = assess_push_readiness(root)
    _print_readiness(readiness, args.json)
    return 0 if readiness.ready or readiness.mode == "nothing_to_push" else 1


def run_push(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    readiness = assess_push_readiness(root)
    dry_run = getattr(args, "dry_run", False)

    if not readiness.ready:
        if args.json:
            print(json.dumps({
                **_readiness_dict(readiness),
                "pushed": False,
            }, indent=2, sort_keys=True))
        else:
            _print_readiness(readiness, json_mode=False)
        return 0 if readiness.mode == "nothing_to_push" else 1

    if dry_run:
        if args.json:
            print(json.dumps({
                **_readiness_dict(readiness),
                "dry_run": True,
                "pushed": False,
            }, indent=2, sort_keys=True))
        else:
            _print_readiness(readiness, json_mode=False)
            print("Dry run: push skipped.")
        return 0

    try:
        push_result = subprocess.run(
            ["git", "push"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        push_output = (push_result.stdout + push_result.stderr).strip()
    except subprocess.CalledProcessError as error:
        if args.json:
            print(json.dumps({
                **_readiness_dict(readiness),
                "error": error.stderr.strip(),
                "pushed": False,
            }, indent=2, sort_keys=True))
        else:
            print(f"Push failed: {error.stderr.strip()}")
        return 1

    if args.json:
        print(json.dumps({
            **_readiness_dict(readiness),
            "push_output": push_output,
            "pushed": True,
        }, indent=2, sort_keys=True))
    else:
        _print_readiness(readiness, json_mode=False)
        print(f"Pushed: {push_output}")

    return 0


def _readiness_dict(readiness: PushReadiness) -> dict:
    return {
        "branch": readiness.branch,
        "check_passed": readiness.check_ok,
        "doctor_errors": not readiness.doctor_ok,
        "doctor_warnings": readiness.doctor_warnings,
        "health_status": "healthy" if readiness.health_ok else "unhealthy",
        "lifecycle_review": readiness.review_status,
        "mode": readiness.mode,
        "ready": readiness.ready,
        "unpushed_commits": readiness.unpushed,
        "working_tree_clean": readiness.clean,
    }


def _print_readiness(readiness: PushReadiness, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(_readiness_dict(readiness), indent=2, sort_keys=True))
        return

    print("Push readiness check")
    print(f"  Branch: {readiness.branch}")
    print(f"  Working tree: {'clean' if readiness.clean else f'{readiness.change_count} changed file(s)'}")
    print(f"  Unpushed commits: {readiness.unpushed}")
    print(f"  Health: {'healthy' if readiness.health_ok else 'unhealthy'}")
    print(f"  Check: {'passed' if readiness.check_ok else 'failed'}")
    doctor_status = "clean" if readiness.doctor_ok and not readiness.doctor_warnings else "errors" if not readiness.doctor_ok else "warnings"
    print(f"  Task memory: {doctor_status}")
    print(f"  Lifecycle review: {readiness.review_status}")
    print(f"  Mode: {readiness.mode}")
    print()
    if readiness.ready:
        print("Ready to push.")
    elif readiness.mode == "nothing_to_push":
        print("Nothing to push.")
    else:
        reasons = []
        if not readiness.clean:
            reasons.append("working tree is dirty")
        if not readiness.health_ok and readiness.mode != "post_finish_closure":
            reasons.append("health is unhealthy")
        elif not readiness.health_ok:
            reasons.append("no active task (not a valid closure state)")
        if not readiness.check_ok and readiness.mode != "post_finish_closure":
            reasons.append("check has violations")
        if not readiness.doctor_ok:
            reasons.append("task memory has errors")
        print("Not ready to push:")
        for reason in reasons:
            print(f"  - {reason}")


def _determine_mode(
    *,
    clean: bool,
    health_ok: bool,
    idle: bool,
    check_ok: bool,
    doctor_ok: bool,
    unpushed: int,
    check_result,
    root: HarnessPath,
) -> str:
    if unpushed == 0:
        return "nothing_to_push"

    if clean and health_ok and check_ok and doctor_ok and not idle:
        return "active_task"

    if clean and idle and check_ok and doctor_ok:
        return "post_finish_closure"

    if (
        clean
        and not health_ok
        and not check_ok
        and _only_missing_active_task(check_result)
        and doctor_ok
        and _latest_unpushed_is_closure(root)
    ):
        return "post_finish_closure"

    return "not_ready"


def _only_missing_active_task(check_result) -> bool:
    if not check_result.violations:
        return False
    return all(
        "No active task contract found" in v.text
        or "Session active task does not match current active task" in v.text
        for v in check_result.violations
    )


def _latest_unpushed_is_closure(root: HarnessPath) -> bool:
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        paths = result.stdout.strip().splitlines()
        return any(p.startswith("tasks/done/") for p in paths)
    except subprocess.CalledProcessError:
        return False


def _count_unpushed_commits(root: HarnessPath) -> int:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=root.path,
                check=True,
                capture_output=True,
                text=True,
            )
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 0
