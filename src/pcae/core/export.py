from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from pcae.core.architecture import (
    ArchitectureDriftMetrics,
    ArchitectureHistorySummary,
    calculate_architecture_drift_metrics,
    read_architecture_history_summary,
)
from pcae.core.check import CheckResult, run_checks
from pcae.core.git_status import GitChange, read_git_branch, read_git_changes
from pcae.core.inspect import inspect_harness
from pcae.core.paths import HarnessPath
from pcae.core.policy import Policy, load_policy
from pcae.core.session import read_session_snapshot, summarize_git_changes


EXPORTS_RELATIVE_PATH = Path(".pcae") / "exports"
GOVERNANCE_BUNDLE_REQUIRED_KEYS = frozenset(
    {
        "active_task",
        "architecture_metrics",
        "check_summary",
        "generated_timestamp",
        "git_status_summary",
        "health_summary",
        "latest_architecture_history_summary",
        "policy_summary",
        "session_snapshot",
    }
)


@dataclass(frozen=True)
class GovernanceExportBundle:
    relative_path: Path
    data: dict


def write_governance_export_bundle(
    root: HarnessPath,
    generated_at: datetime | None = None,
) -> GovernanceExportBundle:
    timestamp = generated_at or datetime.now(timezone.utc)
    data = build_governance_export_bundle(root, timestamp)
    relative_path = EXPORTS_RELATIVE_PATH / (
        f"governance-bundle-{timestamp.strftime('%Y%m%d-%H%M%S')}.json"
    )
    target = root.join(relative_path)

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")

    return GovernanceExportBundle(relative_path=relative_path, data=data)


def build_governance_export_bundle(root: HarnessPath, timestamp: datetime) -> dict:
    check_result = run_checks(root)
    changes = read_git_changes(root)
    policy = load_policy(root)
    architecture_summary = optional_architecture_summary(root)

    return {
        "active_task": active_task_data(check_result),
        "architecture_metrics": architecture_metrics_data(architecture_summary),
        "check_summary": check_summary_data(check_result, changes),
        "generated_timestamp": timestamp.isoformat(),
        "git_status_summary": git_status_summary_data(root, changes),
        "health_summary": health_summary_data(
            root,
            check_result,
            changes,
            architecture_summary,
        ),
        "latest_architecture_history_summary": architecture_history_data(
            architecture_summary
        ),
        "policy_summary": policy_summary_data(policy),
        "session_snapshot": session_snapshot_data(root),
    }


def optional_architecture_summary(
    root: HarnessPath,
) -> ArchitectureHistorySummary | None:
    try:
        return read_architecture_history_summary(root)
    except ValueError:
        return None


def session_snapshot_data(root: HarnessPath) -> dict | None:
    try:
        snapshot = read_session_snapshot(root)
    except json.JSONDecodeError as error:
        return {"error": f"Invalid session JSON: {error.msg}."}
    if snapshot is None:
        return None
    return snapshot.data


def active_task_data(check_result: CheckResult) -> dict[str, str] | None:
    if check_result.active_task_id is None:
        return None
    return {
        "id": check_result.active_task_id,
        "title": check_result.active_task_title or "",
    }


def check_summary_data(
    check_result: CheckResult,
    changes: tuple[GitChange, ...],
) -> dict[str, object]:
    return {
        "active_task": active_task_data(check_result),
        "architecture_zones_touched": {
            zone.name: zone.file_count for zone in check_result.architecture_zones_touched
        },
        "dependency_warnings": [
            warning.text for warning in check_result.architecture_dependency_warnings
        ],
        "enforcement_mode": check_result.architecture_enforcement_mode,
        "git_status": git_status_data(changes),
        "session_continuity": session_continuity_status(check_result),
        "status": "passed" if check_result.passed else "failed",
        "violations": [violation.text for violation in check_result.violations],
        "warnings": [warning.text for warning in check_result.warnings],
    }


def health_summary_data(
    root: HarnessPath,
    check_result: CheckResult,
    changes: tuple[GitChange, ...],
    architecture_summary: ArchitectureHistorySummary | None,
) -> dict[str, object]:
    inspection = inspect_harness(root)
    latest_enforcement_mode = check_result.architecture_enforcement_mode
    latest_dependency_warnings = None
    architecture_history_entries = None
    if architecture_summary is not None:
        architecture_history_entries = len(architecture_summary.entries)
        latest_enforcement_mode = architecture_summary.latest.get(
            "enforcement_mode",
            "unknown",
        )
        latest_dependency_warnings = architecture_summary.latest.get(
            "dependency_warnings_count"
        )

    return {
        "active_task": active_task_data(check_result),
        "architecture_history_entries": architecture_history_entries,
        "git_status": summarize_git_changes(changes),
        "latest_dependency_warnings": latest_dependency_warnings,
        "latest_enforcement_mode": latest_enforcement_mode,
        "overall_status": "healthy" if check_result.passed else "unhealthy",
        "policy_source": inspection.policy.source,
        "policy_validation": "valid" if inspection.policy.valid else "invalid",
        "required_files_status": required_file_status(inspection.missing_paths),
        "session_continuity": session_continuity_status(check_result),
        "violations": [violation.text for violation in check_result.violations],
        "warnings": [warning.text for warning in check_result.warnings],
    }


def required_file_status(missing_paths: tuple[Path, ...]) -> str:
    if not missing_paths:
        return "all present"
    if len(missing_paths) == 1:
        return "1 missing"
    return f"{len(missing_paths)} missing"


def architecture_metrics_data(
    architecture_summary: ArchitectureHistorySummary | None,
) -> dict[str, object] | None:
    if architecture_summary is None:
        return None
    metrics = calculate_architecture_drift_metrics(architecture_summary)
    return architecture_metrics_values(metrics)


def architecture_metrics_values(metrics: ArchitectureDriftMetrics) -> dict[str, object]:
    return {
        "average_dependency_warnings": metrics.average_dependency_warnings,
        "latest_dependency_warnings": metrics.latest_dependency_warnings,
        "latest_enforcement_mode": metrics.latest_enforcement_mode,
        "latest_session_continuity": metrics.latest_session_continuity,
        "max_dependency_warnings": metrics.max_dependency_warnings,
        "most_frequently_touched_zone": metrics.most_frequently_touched_zone,
        "snapshots_with_warnings": metrics.snapshots_with_warnings,
        "total_snapshots": metrics.total_snapshots,
    }


def architecture_history_data(
    architecture_summary: ArchitectureHistorySummary | None,
) -> dict[str, object] | None:
    if architecture_summary is None:
        return None
    return {
        "entries": len(architecture_summary.entries),
        "latest": architecture_summary.latest,
        "path": architecture_summary.relative_path.as_posix(),
    }


def policy_summary_data(policy: Policy) -> dict[str, object]:
    return {
        "architecture_enforcement_mode": policy.architecture_enforcement_mode,
        "architecture_rule_count": len(policy.architecture_rules),
        "architecture_zones": {
            zone_name: len(patterns)
            for zone_name, patterns in policy.architecture_zones.items()
        },
        "file_exists": policy.file_exists,
        "path": Path(".pcae/policy.toml").as_posix(),
        "protected_pattern_count": len(policy.protected_patterns),
        "source": policy.source,
        "valid": policy.valid,
        "error": policy.error,
    }


def git_status_summary_data(
    root: HarnessPath,
    changes: tuple[GitChange, ...],
) -> dict[str, object]:
    return {
        "branch": read_git_branch(root),
        "changed_file_count": len(changes),
        "changed_files": [
            {
                "path": change.path.as_posix(),
                "status": change.status.strip(),
            }
            for change in changes
        ],
        "summary": summarize_git_changes(changes),
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


def session_continuity_status(check_result: CheckResult) -> str:
    if any("Session continuity verified." in info.text for info in check_result.infos):
        return "verified"
    if any(
        "Session snapshot missing" in warning.text
        for warning in check_result.warnings
    ):
        return "missing"
    if any(
        "Session active task does not match current active task" in violation.text
        for violation in check_result.violations
    ):
        return "mismatch"
    if any(
        "Invalid session JSON" in violation.text
        for violation in check_result.violations
    ):
        return "invalid"
    return "unknown"
