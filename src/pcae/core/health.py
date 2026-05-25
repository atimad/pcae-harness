from __future__ import annotations

from pcae.core.architecture import read_architecture_history_summary
from pcae.core.agent import build_agent_lock_state
from pcae.core.check import CheckResult, run_checks
from pcae.core.git_status import read_git_changes
from pcae.core.inspect import InspectionResult, inspect_harness
from pcae.core.paths import HarnessPath
from pcae.core.session import summarize_git_changes


def build_health_data(root: HarnessPath) -> dict:
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

    warnings = [warning.text for warning in check_result.warnings]
    if architecture_warning is not None:
        warnings.append(architecture_warning)

    latest_enforcement_mode = check_result.architecture_enforcement_mode
    latest_dependency_warnings = None
    architecture_history_entries = None
    if architecture_summary is not None:
        latest = architecture_summary.latest
        architecture_history_entries = len(architecture_summary.entries)
        latest_enforcement_mode = latest.get("enforcement_mode", "unknown")
        latest_dependency_warnings = latest.get("dependency_warnings_count")

    return {
        "active_task": active_task_data(check_result),
        "agent_lock": build_agent_lock_state(root),
        "architecture_history_entries": architecture_history_entries,
        "git_status": summarize_git_changes(changes),
        "latest_dependency_warnings": latest_dependency_warnings,
        "latest_enforcement_mode": latest_enforcement_mode,
        "overall_status": "healthy" if check_result.passed else "unhealthy",
        "policy_source": inspection.policy.source,
        "policy_validation": "valid" if inspection.policy.valid else "invalid",
        "required_files_status": required_file_status(inspection),
        "session_continuity": session_continuity_status(check_result),
        "violations": [violation.text for violation in check_result.violations],
        "warnings": warnings,
    }


def required_file_status(inspection: InspectionResult) -> str:
    missing_count = len(inspection.missing_paths)
    if missing_count == 0:
        return "all present"
    if missing_count == 1:
        return "1 missing"
    return f"{missing_count} missing"


def policy_validation_text(data: dict) -> str:
    if data["policy_validation"] == "valid":
        return f"valid ({data['policy_source']})"
    return "invalid"


def active_task_data(check_result: CheckResult) -> dict | None:
    if check_result.active_task_id is None:
        return None
    return {
        "id": check_result.active_task_id,
        "title": check_result.active_task_title,
    }


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
