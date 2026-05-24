from __future__ import annotations

import argparse
import json

from pcae.core.check import CheckResult, run_checks
from pcae.core.git_status import GitChange, read_git_changes
from pcae.core.paths import HarnessPath


def run_check(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = run_checks(root)

    if args.json:
        print(json.dumps(check_json_data(root, result), indent=2, sort_keys=True))
        return 0 if result.passed else 1

    if result.active_task_id is not None:
        print(f"Active task: {result.active_task_id}")
        print(f"Title: {result.active_task_title}")
    else:
        print("Active task: none")

    if result.architecture_zones_touched:
        print("Architecture zones touched:")
        for zone in result.architecture_zones_touched:
            print(f"  {zone.name}: {zone.file_count} files")

    if result.architecture_dependency_warnings:
        print("Architecture dependency warnings:")
        for warning in result.architecture_dependency_warnings:
            print(f"  {warning.text}")

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


def check_json_data(root: HarnessPath, result: CheckResult) -> dict[str, object]:
    changes = read_git_changes(root)
    return {
        "active_task": active_task_data(result),
        "architecture_zones_touched": {
            zone.name: zone.file_count for zone in result.architecture_zones_touched
        },
        "dependency_warnings": [
            warning.text for warning in result.architecture_dependency_warnings
        ],
        "enforcement_mode": result.architecture_enforcement_mode,
        "git_status": git_status_data(changes),
        "session_continuity": session_continuity_status(result),
        "status": "passed" if result.passed else "failed",
        "violations": [violation.text for violation in result.violations],
        "warnings": [warning.text for warning in result.warnings],
    }


def active_task_data(result: CheckResult) -> dict[str, str] | None:
    if result.active_task_id is None:
        return None
    return {
        "id": result.active_task_id,
        "title": result.active_task_title or "",
    }


def git_status_data(changes: tuple[GitChange, ...]) -> dict[str, object]:
    return {
        "changed_file_count": len(changes),
        "changed_files": [
            {
                "path": change.path.as_posix(),
                "status": change.status.strip(),
            }
            for change in changes
        ],
    }


def session_continuity_status(result: CheckResult) -> str:
    if any("Session continuity verified." in info.text for info in result.infos):
        return "verified"
    if any("Session snapshot missing" in warning.text for warning in result.warnings):
        return "missing"
    if any("Invalid session JSON" in violation.text for violation in result.violations):
        return "invalid"
    if any(
        "Session active task does not match current active task" in violation.text
        for violation in result.violations
    ):
        return "mismatched"
    return "unknown"
