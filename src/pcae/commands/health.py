from __future__ import annotations

import argparse

from pcae.core.architecture import read_architecture_history_summary
from pcae.core.check import CheckResult, run_checks
from pcae.core.git_status import read_git_changes
from pcae.core.inspect import InspectionResult, inspect_harness
from pcae.core.paths import HarnessPath
from pcae.core.session import summarize_git_changes


def run_health(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    inspection = inspect_harness(root)
    check_result = run_checks(root)
    changes = read_git_changes(root)

    try:
        architecture_summary = read_architecture_history_summary(root)
    except ValueError as error:
        architecture_summary = None
        architecture_warning = str(error)
    else:
        architecture_warning = None

    print("PCAE health")
    print(f"Overall status: {'healthy' if check_result.passed else 'unhealthy'}")
    print(f"Required PCAE files: {required_file_status(inspection)}")
    print(f"Policy validation: {policy_status(inspection)}")
    print_active_task(check_result)
    print(f"Session continuity: {session_continuity_status(check_result)}")
    if architecture_summary is None:
        print("Architecture history entries: missing")
        print(f"Latest enforcement mode: {check_result.architecture_enforcement_mode}")
        print("Latest dependency warnings: unknown")
    else:
        latest = architecture_summary.latest
        print(f"Architecture history entries: {len(architecture_summary.entries)}")
        print(f"Latest enforcement mode: {latest.get('enforcement_mode', 'unknown')}")
        print(
            "Latest dependency warnings: "
            f"{latest.get('dependency_warnings_count', 'unknown')}"
        )
    print(f"Git status: {summarize_git_changes(changes)}")

    for warning in check_result.warnings:
        print(f"  - warning: {warning.text}")
    if architecture_warning is not None:
        print(f"  - warning: {architecture_warning}")

    if check_result.passed:
        return 0

    print("Health check failed:")
    for violation in check_result.violations:
        print(f"  - {violation.text}")
    return 1


def required_file_status(inspection: InspectionResult) -> str:
    missing_count = len(inspection.missing_paths)
    if missing_count == 0:
        return "all present"
    if missing_count == 1:
        return "1 missing"
    return f"{missing_count} missing"


def policy_status(inspection: InspectionResult) -> str:
    if inspection.policy.valid:
        return f"valid ({inspection.policy.source})"
    return f"invalid: {inspection.policy.error or 'unknown error'}"


def print_active_task(check_result: CheckResult) -> None:
    if check_result.active_task_id is None:
        print("Active task: none")
        return

    print(f"Active task: {check_result.active_task_id}")
    print(f"Title: {check_result.active_task_title}")


def session_continuity_status(check_result: CheckResult) -> str:
    if any("Session continuity verified." in info.text for info in check_result.infos):
        return "verified"
    if any("Session snapshot missing" in warning.text for warning in check_result.warnings):
        return "missing"
    if any(
        "Session active task does not match current active task" in violation.text
        for violation in check_result.violations
    ):
        return "mismatch"
    if any("Invalid session JSON" in violation.text for violation in check_result.violations):
        return "invalid"
    return "unknown"
