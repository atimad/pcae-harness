from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
import json
from pathlib import Path

from pcae.core.agent import build_agent_lock_state
from pcae.core.check import run_checks
from pcae.core.health import build_health_data, session_continuity_status
from pcae.core.paths import HarnessPath
from pcae.core.policy import load_policy
from pcae.core.provenance import (
    PROVENANCE_HISTORY_RELATIVE_PATH,
    build_provenance_timeline,
)
from pcae.core.session import read_session_snapshot
from pcae.core.tasks import find_latest_active_task


PROJECT_STATUS_RELATIVE_PATH = Path("PROJECT_STATUS.md")
ROADMAP_RELATIVE_PATHS = (
    PROJECT_STATUS_RELATIVE_PATH,
    Path("tasks") / "TODO.md",
)

# Phrases known to be stale because the features they describe are already
# implemented. Stale roadmap references in governance documents create
# orchestration risk: agents read them as forward-looking guidance and
# attempt to implement work that has already been done.
KNOWN_STALE_PHRASES: tuple[str, ...] = (
    "Implement `pcae end`",
    "Implement `pcae session end`",
    "Full governance audit: `pcae governance audit` command",
    "Governance repair planning preview: `pcae governance repair --dry-run` command",
)

GOVERNANCE_REPAIR_ADVISORY = (
    "Repair planning is advisory; the user remains authoritative."
)
RUNTIME_SNAPSHOT_ADVISORY = (
    "Snapshot previews are advisory; the user remains authoritative."
)
RUNTIME_SNAPSHOT_INSPECTION_ADVISORY = (
    "Snapshot inspection is advisory; the user remains authoritative."
)
RUNTIME_SNAPSHOT_RESTORE_ADVISORY = (
    "Restore preview is advisory; no runtime state is changed."
)
RUNTIME_SNAPSHOTS_RELATIVE_PATH = Path(".pcae") / "runtime-snapshots"
CURRENT_RUNTIME_SNAPSHOT_SCHEMA_VERSION = 1
RUNTIME_SNAPSHOT_KIND = "pcae-runtime-snapshot"
SUPPORTED_RUNTIME_SNAPSHOT_KINDS: tuple[str, ...] = (RUNTIME_SNAPSHOT_KIND,)
SUPPORTED_RUNTIME_SNAPSHOT_SCHEMA_VERSIONS: tuple[int, ...] = (
    CURRENT_RUNTIME_SNAPSHOT_SCHEMA_VERSION,
)
RUNTIME_SNAPSHOT_REQUIRED_KEYS: tuple[str, ...] = (
    "snapshot_schema_version",
    "snapshot_kind",
    "exported_by_version",
    "exported_at",
    "active_task",
    "agent_lock_state",
    "session_continuity_status",
    "provenance_event_count",
    "latest_provenance_event",
    "orchestration_policy_summary",
    "registered_agents",
    "governance_health_status",
    "governance_check_status",
    "workflow_orchestration_metadata",
)


@dataclass(frozen=True)
class CoherenceWarning:
    document: str
    message: str

    def to_dict(self) -> dict:
        return {"document": self.document, "message": self.message}


@dataclass(frozen=True)
class CoherenceResult:
    warnings: tuple[CoherenceWarning, ...]

    @property
    def coherent(self) -> bool:
        return len(self.warnings) == 0

    def to_dict(self) -> dict:
        return {
            "coherent": self.coherent,
            "warning_count": len(self.warnings),
            "warnings": [w.to_dict() for w in self.warnings],
        }


@dataclass(frozen=True)
class GovernanceAuditCheck:
    name: str
    passed: bool
    message: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass(frozen=True)
class GovernanceAuditSummary:
    check_count: int
    passed_count: int
    failed_count: int
    warning_count: int
    status: str

    def to_dict(self) -> dict:
        return {
            "check_count": self.check_count,
            "failed_count": self.failed_count,
            "passed_count": self.passed_count,
            "status": self.status,
            "warning_count": self.warning_count,
        }


@dataclass(frozen=True)
class GovernanceAuditResult:
    checks: tuple[GovernanceAuditCheck, ...]
    warnings: tuple[CoherenceWarning, ...]
    summary: GovernanceAuditSummary

    @property
    def valid(self) -> bool:
        return self.summary.status == "valid"

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "checks": [check.to_dict() for check in self.checks],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "summary": self.summary.to_dict(),
        }


@dataclass(frozen=True)
class GovernanceRepairPlan:
    repairable: bool
    detected_issues: tuple[str, ...]
    proposed_repairs: tuple[str, ...]
    safety_notes: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "repairable": self.repairable,
            "detected_issues": list(self.detected_issues),
            "proposed_repairs": list(self.proposed_repairs),
            "safety_notes": list(self.safety_notes),
            "advisory": self.advisory,
        }


@dataclass(frozen=True)
class RuntimeSnapshotPreview:
    snapshot_ready: bool
    included_sections: tuple[str, ...]
    portability_notes: tuple[str, ...]
    safety_notes: tuple[str, ...]
    advisory: str
    runtime_summary: dict

    def to_dict(self) -> dict:
        return {
            "snapshot_ready": self.snapshot_ready,
            "included_sections": list(self.included_sections),
            "portability_notes": list(self.portability_notes),
            "safety_notes": list(self.safety_notes),
            "advisory": self.advisory,
            "runtime_summary": self.runtime_summary,
        }


@dataclass(frozen=True)
class RuntimeSnapshotExport:
    export_path: Path
    exported_at: str
    snapshot_ready: bool
    snapshot: dict

    def to_dict(self) -> dict:
        return {
            "export_path": self.export_path.as_posix(),
            "exported_at": self.exported_at,
            "snapshot_schema_version": self.snapshot["snapshot_schema_version"],
            "snapshot_kind": self.snapshot["snapshot_kind"],
            "exported_by_version": self.snapshot["exported_by_version"],
            "snapshot_ready": self.snapshot_ready,
            "snapshot": self.snapshot,
        }


@dataclass(frozen=True)
class RuntimeSnapshotInspection:
    valid: bool
    exported_at: str
    snapshot_schema_version: int
    snapshot_kind: str
    compatibility_status: str
    compatibility_notes: tuple[str, ...]
    included_sections: tuple[str, ...]
    runtime_summary: dict
    portability_notes: tuple[str, ...]
    safety_notes: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "exported_at": self.exported_at,
            "snapshot_schema_version": self.snapshot_schema_version,
            "snapshot_kind": self.snapshot_kind,
            "compatibility_status": self.compatibility_status,
            "compatibility_notes": list(self.compatibility_notes),
            "included_sections": list(self.included_sections),
            "runtime_summary": self.runtime_summary,
            "portability_notes": list(self.portability_notes),
            "safety_notes": list(self.safety_notes),
            "advisory": self.advisory,
        }


@dataclass(frozen=True)
class RuntimeSnapshotRestorePreview:
    valid: bool
    restore_preview: dict
    snapshot_schema_version: int
    snapshot_kind: str
    compatibility_status: str
    compatibility_notes: tuple[str, ...]
    would_restore: tuple[str, ...]
    would_not_restore: tuple[str, ...]
    safety_notes: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "restore_preview": self.restore_preview,
            "snapshot_schema_version": self.snapshot_schema_version,
            "snapshot_kind": self.snapshot_kind,
            "compatibility_status": self.compatibility_status,
            "compatibility_notes": list(self.compatibility_notes),
            "would_restore": list(self.would_restore),
            "would_not_restore": list(self.would_not_restore),
            "safety_notes": list(self.safety_notes),
            "advisory": self.advisory,
        }


def check_project_status_coherence(root: HarnessPath) -> CoherenceResult:
    """Return coherence warnings for PROJECT_STATUS.md stale roadmap references."""
    path = root.join(PROJECT_STATUS_RELATIVE_PATH)
    if not path.is_file():
        return CoherenceResult(
            warnings=(
                CoherenceWarning(
                    document=str(PROJECT_STATUS_RELATIVE_PATH),
                    message="PROJECT_STATUS.md not found",
                ),
            )
        )
    text = path.read_text(encoding="utf-8")
    warnings = []
    for phrase in KNOWN_STALE_PHRASES:
        if phrase in text:
            warnings.append(
                CoherenceWarning(
                    document=str(PROJECT_STATUS_RELATIVE_PATH),
                    message=f"Stale roadmap reference: {phrase!r} — feature already implemented.",
                )
            )
    return CoherenceResult(warnings=tuple(warnings))


def audit_governance_coherence(root: HarnessPath) -> GovernanceAuditResult:
    """Return a lightweight read-only governance coherence audit."""
    checks = [
        check_project_status_current_phase(root),
        check_project_status_next_section(root),
        check_active_task_readable(root),
        check_session_continuity_available(root),
        check_provenance_history_exists(root),
        check_policy_parses(root),
        check_agent_registry_non_empty(root),
    ]
    warnings = find_stale_roadmap_references(root)
    passed_count = sum(1 for check in checks if check.passed)
    failed_count = len(checks) - passed_count
    status = "valid" if failed_count == 0 and len(warnings) == 0 else "warnings"
    if failed_count > 0:
        status = "invalid"
    return GovernanceAuditResult(
        checks=tuple(checks),
        warnings=warnings,
        summary=GovernanceAuditSummary(
            check_count=len(checks),
            passed_count=passed_count,
            failed_count=failed_count,
            warning_count=len(warnings),
            status=status,
        ),
    )


def plan_governance_repairs(root: HarnessPath) -> GovernanceRepairPlan:
    """Return deterministic read-only repair recommendations for audit issues."""
    audit = audit_governance_coherence(root)
    detected_issues = tuple(audit_issue_messages(audit))
    proposed_repairs = tuple(audit_repair_recommendations(audit))
    return GovernanceRepairPlan(
        repairable=True,
        detected_issues=detected_issues,
        proposed_repairs=proposed_repairs,
        safety_notes=(
            "Dry-run only; no governance artifacts will be modified.",
            "No roadmap content is rewritten automatically.",
            "No semantic AI analysis, remote sync, dashboards, or database writes are used.",
        ),
        advisory=GOVERNANCE_REPAIR_ADVISORY,
    )


def preview_runtime_snapshot(root: HarnessPath) -> RuntimeSnapshotPreview:
    """Return a read-only preview of portable governed runtime snapshot contents."""
    health = build_health_data(root)
    check_result = run_checks(root)
    policy = load_policy(root)
    active_task = find_latest_active_task(root)
    session = read_session_snapshot(root)
    provenance = build_provenance_timeline(root)

    runtime_summary = {
        "active_task": None
        if active_task is None
        else {
            "id": active_task.task_id,
            "title": active_task.title,
            "status": active_task.status,
            "mode": active_task.mode,
            "goal": active_task.goal,
        },
        "agent_lock_state": build_agent_lock_state(root),
        "session_continuity_status": session_continuity_status(check_result),
        "provenance_event_count": provenance.event_count,
        "latest_provenance_event": None
        if provenance.latest_event is None
        else provenance.latest_event.to_dict(),
        "orchestration_policy_summary": policy.orchestration.to_dict(),
        "registered_agents": [entry.to_dict() for entry in policy.agent_registry],
        "governance_health_status": health["overall_status"],
        "governance_check_status": "passed" if check_result.passed else "failed",
        "workflow_orchestration_metadata": workflow_orchestration_metadata(
            active_task,
            session.data if session is not None else None,
        ),
    }
    return RuntimeSnapshotPreview(
        snapshot_ready=health["overall_status"] == "healthy" and check_result.passed,
        included_sections=(
            "active task",
            "agent lock state",
            "session continuity status",
            "provenance event count",
            "latest provenance event",
            "orchestration policy summary",
            "registered agents",
            "governance health status",
            "governance check status",
            "workflow/orchestration metadata",
        ),
        portability_notes=(
            "Preview describes portable runtime sections only; no archive is written.",
            "Local paths and agent identifiers remain advisory runtime metadata.",
            "Restoration is intentionally out of scope for this preview.",
        ),
        safety_notes=(
            "Preview only; no files are exported.",
            "Runtime state is not restored or modified.",
            "Governance artifacts are not mutated.",
        ),
        advisory=RUNTIME_SNAPSHOT_ADVISORY,
        runtime_summary=runtime_summary,
    )


def export_runtime_snapshot(
    root: HarnessPath,
    exported_at: datetime | None = None,
) -> RuntimeSnapshotExport:
    timestamp = exported_at or datetime.now(timezone.utc)
    exported_at_text = timestamp.isoformat()
    preview = preview_runtime_snapshot(root)
    snapshot = {
        "snapshot_schema_version": CURRENT_RUNTIME_SNAPSHOT_SCHEMA_VERSION,
        "snapshot_kind": RUNTIME_SNAPSHOT_KIND,
        "exported_by_version": exported_by_version(),
        "exported_at": exported_at_text,
        **preview.runtime_summary,
    }
    relative_path = RUNTIME_SNAPSHOTS_RELATIVE_PATH / (
        f"runtime-snapshot-{timestamp.strftime('%Y%m%d-%H%M%S')}.json"
    )
    target = root.join(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(snapshot, file, indent=2, sort_keys=True)
        file.write("\n")
    return RuntimeSnapshotExport(
        export_path=relative_path,
        exported_at=exported_at_text,
        snapshot_ready=preview.snapshot_ready,
        snapshot=snapshot,
    )


def inspect_runtime_snapshot(root: HarnessPath, snapshot_path: Path) -> RuntimeSnapshotInspection:
    path = snapshot_path if snapshot_path.is_absolute() else root.join(snapshot_path)
    if not path.is_file():
        raise ValueError(f"Invalid runtime snapshot: file not found: {snapshot_path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid runtime snapshot JSON: {error.msg}") from error
    if not isinstance(data, dict):
        raise ValueError("Invalid runtime snapshot: top-level JSON value must be an object.")

    missing = [key for key in RUNTIME_SNAPSHOT_REQUIRED_KEYS if key not in data]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Invalid runtime snapshot: missing required field(s): {missing_text}.")

    exported_at = data.get("exported_at")
    if not isinstance(exported_at, str) or not exported_at:
        raise ValueError("Invalid runtime snapshot: exported_at must be a non-empty string.")
    snapshot_schema_version = data.get("snapshot_schema_version")
    if not isinstance(snapshot_schema_version, int):
        raise ValueError(
            "Invalid runtime snapshot: snapshot_schema_version must be an integer."
        )
    snapshot_kind = data.get("snapshot_kind")
    if not isinstance(snapshot_kind, str) or not snapshot_kind:
        raise ValueError("Invalid runtime snapshot: snapshot_kind must be a non-empty string.")
    compatibility = validate_runtime_snapshot_compatibility(
        snapshot_schema_version,
        snapshot_kind,
    )

    runtime_summary = {key: data.get(key) for key in RUNTIME_SNAPSHOT_REQUIRED_KEYS if key != "exported_at"}
    return RuntimeSnapshotInspection(
        valid=True,
        exported_at=exported_at,
        snapshot_schema_version=snapshot_schema_version,
        snapshot_kind=snapshot_kind,
        compatibility_status=compatibility.status,
        compatibility_notes=compatibility.notes,
        included_sections=runtime_snapshot_included_sections(data),
        runtime_summary=runtime_summary,
        portability_notes=(
            "Snapshot was read for inspection only; runtime state was not restored.",
            "Local paths and agent identifiers are portable metadata, not authority.",
            "Schema/version metadata is reported when present.",
        ),
        safety_notes=(
            "Inspection only; no files are modified.",
            "Governance artifacts are not mutated.",
            "Snapshot contents are not rewritten.",
        ),
        advisory=RUNTIME_SNAPSHOT_INSPECTION_ADVISORY,
    )


def preview_runtime_snapshot_restore(
    root: HarnessPath,
    snapshot_path: Path,
) -> RuntimeSnapshotRestorePreview:
    inspection = inspect_runtime_snapshot(root, snapshot_path)
    summary = inspection.runtime_summary
    incompatible = inspection.compatibility_status != "compatible"
    restore_preview = {
        "exported_at": inspection.exported_at,
        "snapshot_schema_version": inspection.snapshot_schema_version,
        "snapshot_kind": inspection.snapshot_kind,
        "compatibility_status": inspection.compatibility_status,
        "active_task": summary["active_task"],
        "agent_lock_state": summary["agent_lock_state"],
        "session_continuity_status": summary["session_continuity_status"],
        "provenance_summary": {
            "event_count": summary["provenance_event_count"],
            "latest_event": summary["latest_provenance_event"],
        },
        "orchestration_policy_summary": summary["orchestration_policy_summary"],
        "registered_agents": summary["registered_agents"],
        "governance_health_status": summary["governance_health_status"],
        "governance_check_status": summary["governance_check_status"],
        "workflow_orchestration_metadata": summary["workflow_orchestration_metadata"],
    }
    return RuntimeSnapshotRestorePreview(
        valid=not incompatible,
        restore_preview=restore_preview,
        snapshot_schema_version=inspection.snapshot_schema_version,
        snapshot_kind=inspection.snapshot_kind,
        compatibility_status=inspection.compatibility_status,
        compatibility_notes=inspection.compatibility_notes,
        would_restore=()
        if incompatible
        else (
            "active task metadata",
            "agent lock state",
            "session continuity state",
            "provenance summary",
            "orchestration policy summary",
            "registered agents",
            "governance health/check status",
            "workflow/orchestration metadata",
        ),
        would_not_restore=(
            "all runtime state because the snapshot is not compatible",
        )
        if incompatible
        else (
            "active task files",
            "agent lock file",
            "session snapshot",
            "provenance history",
            "orchestration policy file",
            "runtime snapshot file",
        ),
        safety_notes=(
            "Dry-run only; no runtime state is restored.",
            "No files are written.",
            "Agent locks, provenance, session state, and history are not modified.",
        ),
        advisory=RUNTIME_SNAPSHOT_RESTORE_ADVISORY,
    )


@dataclass(frozen=True)
class RuntimeSnapshotCompatibility:
    status: str
    notes: tuple[str, ...]


def validate_runtime_snapshot_compatibility(
    snapshot_schema_version: int,
    snapshot_kind: str,
) -> RuntimeSnapshotCompatibility:
    notes: list[str] = []
    if snapshot_kind not in SUPPORTED_RUNTIME_SNAPSHOT_KINDS:
        notes.append(
            f"Unknown snapshot kind: {snapshot_kind!r}; expected {RUNTIME_SNAPSHOT_KIND!r}."
        )
    if snapshot_schema_version not in SUPPORTED_RUNTIME_SNAPSHOT_SCHEMA_VERSIONS:
        notes.append(
            "Unsupported runtime snapshot schema version: "
            f"{snapshot_schema_version}; supported versions: "
            f"{', '.join(str(v) for v in SUPPORTED_RUNTIME_SNAPSHOT_SCHEMA_VERSIONS)}."
        )
    if notes:
        notes.append("No migration or automatic conversion is available.")
        return RuntimeSnapshotCompatibility(
            status="incompatible",
            notes=tuple(notes),
        )
    return RuntimeSnapshotCompatibility(
        status="compatible",
        notes=(
            "Snapshot kind is supported.",
            f"Runtime snapshot schema version {snapshot_schema_version} is supported.",
        ),
    )


def exported_by_version() -> str:
    try:
        return metadata.version("pcae-harness")
    except metadata.PackageNotFoundError:
        return "0.1.0"


def runtime_snapshot_included_sections(data: dict) -> tuple[str, ...]:
    sections = []
    labels = {
        "active_task": "active task",
        "agent_lock_state": "agent lock state",
        "session_continuity_status": "session continuity status",
        "provenance_event_count": "provenance event count",
        "latest_provenance_event": "latest provenance event",
        "orchestration_policy_summary": "orchestration policy summary",
        "registered_agents": "registered agents",
        "governance_health_status": "governance health status",
        "governance_check_status": "governance check status",
        "workflow_orchestration_metadata": "workflow/orchestration metadata",
    }
    for key, label in labels.items():
        if key in data:
            sections.append(label)
    if "snapshot_schema_version" in data or "snapshot_kind" in data:
        sections.append("snapshot schema/version metadata")
    return tuple(sections)


def workflow_orchestration_metadata(active_task: object, session_data: dict | None) -> dict:
    metadata: dict[str, object] = {
        "available": False,
        "active_task_mode": None,
        "active_task_goal": None,
        "session_current_objective": None,
        "session_next_recommended_step": None,
    }
    if active_task is not None:
        metadata["active_task_mode"] = getattr(active_task, "mode", None)
        metadata["active_task_goal"] = getattr(active_task, "goal", None)
    if session_data is not None:
        metadata["session_current_objective"] = session_data.get("current_objective")
        metadata["session_next_recommended_step"] = session_data.get(
            "next_recommended_step"
        )
    metadata["available"] = any(
        metadata[key]
        for key in (
            "active_task_mode",
            "active_task_goal",
            "session_current_objective",
            "session_next_recommended_step",
        )
    )
    return metadata


def audit_issue_messages(audit: GovernanceAuditResult) -> list[str]:
    issues: list[str] = []
    for check in audit.checks:
        if not check.passed:
            issues.append(f"{check.name}: {check.message}")
    for warning in audit.warnings:
        issues.append(f"{warning.document}: {warning.message}")
    return issues


def audit_repair_recommendations(audit: GovernanceAuditResult) -> list[str]:
    repairs: list[str] = []
    for check in audit.checks:
        if check.passed:
            continue
        repairs.extend(repairs_for_failed_check(check.name))
    for warning in audit.warnings:
        repairs.extend(repairs_for_warning(warning))
    return unique_preserving_order(repairs)


def repairs_for_failed_check(check_name: str) -> tuple[str, ...]:
    if check_name == "project_status_current_phase":
        return (
            "synchronize PROJECT_STATUS.md roadmap guidance",
            "refresh governance summaries",
        )
    if check_name == "project_status_next":
        return (
            "synchronize PROJECT_STATUS.md roadmap guidance",
            "refresh stale \"Next\" references",
        )
    if check_name == "active_task":
        return ("refresh governance summaries",)
    if check_name == "session_continuity":
        return ("refresh governance summaries",)
    if check_name == "provenance_history":
        return ("refresh governance summaries",)
    if check_name == "policy_configuration":
        return (
            "refresh governance summaries",
            "refresh orchestration guidance",
        )
    if check_name == "agent_registry":
        return (
            "refresh orchestration guidance",
            "refresh governance summaries",
        )
    return ("refresh governance summaries",)


def repairs_for_warning(warning: CoherenceWarning) -> tuple[str, ...]:
    repairs = [
        "synchronize PROJECT_STATUS.md roadmap guidance",
        "refresh governance summaries",
    ]
    if warning.document == PROJECT_STATUS_RELATIVE_PATH.as_posix():
        repairs.append('refresh stale "Next" references')
    if "orchestration" in warning.message.lower():
        repairs.append("refresh orchestration guidance")
    if "docs commands" in warning.message.lower():
        repairs.append("refresh docs command coverage references")
    return tuple(repairs)


def unique_preserving_order(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def check_project_status_current_phase(root: HarnessPath) -> GovernanceAuditCheck:
    text = read_project_status_text(root)
    if text is None:
        return GovernanceAuditCheck(
            name="project_status_current_phase",
            passed=False,
            message="PROJECT_STATUS.md not found.",
        )
    phase = read_markdown_section_text(text, "Current Phase")
    if phase is None:
        return GovernanceAuditCheck(
            name="project_status_current_phase",
            passed=False,
            message="PROJECT_STATUS.md Current Phase section is missing or empty.",
        )
    return GovernanceAuditCheck(
        name="project_status_current_phase",
        passed=True,
        message=f"Current phase: {first_line(phase)}",
    )


def check_project_status_next_section(root: HarnessPath) -> GovernanceAuditCheck:
    text = read_project_status_text(root)
    if text is None:
        return GovernanceAuditCheck(
            name="project_status_next",
            passed=False,
            message="PROJECT_STATUS.md not found.",
        )
    next_text = read_markdown_section_text(text, "Next")
    if next_text is None:
        return GovernanceAuditCheck(
            name="project_status_next",
            passed=False,
            message="PROJECT_STATUS.md Next section is missing or empty.",
        )
    return GovernanceAuditCheck(
        name="project_status_next",
        passed=True,
        message=f"Next: {first_line(next_text)}",
    )


def check_active_task_readable(root: HarnessPath) -> GovernanceAuditCheck:
    try:
        active_task = find_latest_active_task(root)
    except OSError as error:
        return GovernanceAuditCheck(
            name="active_task",
            passed=False,
            message=f"Active task could not be read: {error}",
        )
    if active_task is None:
        return GovernanceAuditCheck(
            name="active_task",
            passed=False,
            message="No active task contract found in tasks/active/.",
        )
    return GovernanceAuditCheck(
        name="active_task",
        passed=True,
        message=f"Active task: {active_task.task_id}",
    )


def check_session_continuity_available(root: HarnessPath) -> GovernanceAuditCheck:
    try:
        snapshot = read_session_snapshot(root)
    except (OSError, ValueError) as error:
        return GovernanceAuditCheck(
            name="session_continuity",
            passed=False,
            message=f"Session continuity status is unavailable: {error}",
        )
    if snapshot is None:
        return GovernanceAuditCheck(
            name="session_continuity",
            passed=False,
            message="Session snapshot missing at .pcae/session.json.",
        )
    return GovernanceAuditCheck(
        name="session_continuity",
        passed=True,
        message="Session continuity status is available.",
    )


def check_provenance_history_exists(root: HarnessPath) -> GovernanceAuditCheck:
    if root.join(PROVENANCE_HISTORY_RELATIVE_PATH).is_file():
        return GovernanceAuditCheck(
            name="provenance_history",
            passed=True,
            message=".pcae/provenance-history.json exists.",
        )
    return GovernanceAuditCheck(
        name="provenance_history",
        passed=False,
        message=".pcae/provenance-history.json is missing.",
    )


def check_policy_parses(root: HarnessPath) -> GovernanceAuditCheck:
    policy = load_policy(root)
    if policy.valid:
        return GovernanceAuditCheck(
            name="policy_configuration",
            passed=True,
            message=f"Policy parses successfully ({policy.source}).",
        )
    return GovernanceAuditCheck(
        name="policy_configuration",
        passed=False,
        message=policy.error or "Policy configuration is invalid.",
    )


def check_agent_registry_non_empty(root: HarnessPath) -> GovernanceAuditCheck:
    policy = load_policy(root)
    if not policy.valid:
        return GovernanceAuditCheck(
            name="agent_registry",
            passed=False,
            message=policy.error or "Agent registry unavailable because policy is invalid.",
        )
    if not policy.agent_registry:
        return GovernanceAuditCheck(
            name="agent_registry",
            passed=False,
            message="Agent registry is empty.",
        )
    return GovernanceAuditCheck(
        name="agent_registry",
        passed=True,
        message=f"Agent registry contains {len(policy.agent_registry)} agent(s).",
    )


def find_stale_roadmap_references(root: HarnessPath) -> tuple[CoherenceWarning, ...]:
    warnings: list[CoherenceWarning] = []
    for relative_path in ROADMAP_RELATIVE_PATHS:
        path = root.join(relative_path)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in KNOWN_STALE_PHRASES:
            if phrase in text:
                warnings.append(
                    CoherenceWarning(
                        document=relative_path.as_posix(),
                        message=(
                            f"Stale roadmap reference: {phrase!r} "
                            "— feature already implemented."
                        ),
                    )
                )
    return tuple(warnings)


def read_project_status_text(root: HarnessPath) -> str | None:
    path = root.join(PROJECT_STATUS_RELATIVE_PATH)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def read_markdown_section_text(content: str, section_name: str) -> str | None:
    lines = content.splitlines()
    values: list[str] = []
    in_section = False
    target = f"## {section_name}"

    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() == target
            continue
        if in_section and line.strip():
            values.append(line.strip())

    if not values:
        return None
    return "\n".join(values)


def first_line(text: str) -> str:
    return text.splitlines()[0]
