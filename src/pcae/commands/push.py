from __future__ import annotations

import argparse
import json
import subprocess

from pcae.core.check import run_checks
from pcae.core.git_status import read_git_branch, read_git_changes
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.tasks import diagnose_task_memory


def run_push_check(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()

    changes = read_git_changes(root)
    branch = read_git_branch(root)
    unpushed = _count_unpushed_commits(root)
    health = build_health_data(root)
    check_result = run_checks(root)
    diagnostics = diagnose_task_memory(root)

    clean = not changes
    health_ok = health["overall_status"] == "healthy"
    check_ok = check_result.passed
    doctor_ok = not diagnostics.has_errors

    mode = _determine_mode(
        clean=clean,
        health_ok=health_ok,
        check_ok=check_ok,
        doctor_ok=doctor_ok,
        unpushed=unpushed,
        check_result=check_result,
        root=root,
    )

    ready = mode in ("active_task", "post_finish_closure")

    if args.json:
        print(
            json.dumps(
                {
                    "branch": branch,
                    "check_passed": check_ok,
                    "doctor_errors": diagnostics.has_errors,
                    "doctor_warnings": diagnostics.has_warnings,
                    "health_status": health["overall_status"],
                    "mode": mode,
                    "ready": ready,
                    "unpushed_commits": unpushed,
                    "working_tree_clean": clean,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print("Push readiness check")
        print(f"  Branch: {branch}")
        print(f"  Working tree: {'clean' if clean else f'{len(changes)} changed file(s)'}")
        print(f"  Unpushed commits: {unpushed}")
        print(f"  Health: {health['overall_status']}")
        print(f"  Check: {'passed' if check_ok else 'failed'}")
        print(f"  Task memory: {'clean' if not diagnostics.has_errors and not diagnostics.has_warnings else 'errors' if diagnostics.has_errors else 'warnings'}")
        print(f"  Mode: {mode}")
        print()
        if ready:
            print("Ready to push.")
        elif mode == "nothing_to_push":
            print("Nothing to push.")
        else:
            reasons = []
            if not clean:
                reasons.append("working tree is dirty")
            if not health_ok and not _only_missing_active_task(check_result):
                reasons.append("health is unhealthy")
            elif not health_ok:
                reasons.append("no active task (not a valid closure state)")
            if not check_ok and not _only_missing_active_task(check_result):
                reasons.append("check has violations")
            if diagnostics.has_errors:
                reasons.append("task memory has errors")
            print("Not ready to push:")
            for reason in reasons:
                print(f"  - {reason}")

    return 0 if ready or mode == "nothing_to_push" else 1


def _determine_mode(
    *,
    clean: bool,
    health_ok: bool,
    check_ok: bool,
    doctor_ok: bool,
    unpushed: int,
    check_result,
    root: HarnessPath,
) -> str:
    if unpushed == 0:
        return "nothing_to_push"

    if clean and health_ok and check_ok and doctor_ok:
        return "active_task"

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
