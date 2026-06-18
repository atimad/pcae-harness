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
    ready = clean and health_ok and check_ok and doctor_ok and unpushed > 0

    if args.json:
        print(
            json.dumps(
                {
                    "branch": branch,
                    "check_passed": check_ok,
                    "doctor_errors": diagnostics.has_errors,
                    "doctor_warnings": diagnostics.has_warnings,
                    "health_status": health["overall_status"],
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
        print()
        if ready:
            print("Ready to push.")
        elif unpushed == 0:
            print("Nothing to push.")
        else:
            reasons = []
            if not clean:
                reasons.append("working tree is dirty")
            if not health_ok:
                reasons.append("health is unhealthy")
            if not check_ok:
                reasons.append("check has violations")
            if diagnostics.has_errors:
                reasons.append("task memory has errors")
            print("Not ready to push:")
            for reason in reasons:
                print(f"  - {reason}")

    return 0 if ready or unpushed == 0 else 1


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
