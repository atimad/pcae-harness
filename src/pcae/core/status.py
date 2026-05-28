from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
import json
from pathlib import Path
import re
import subprocess

from pcae.core.agent import build_agent_lock_state
from pcae.core.check import run_checks
from pcae.core.git_status import read_git_changes
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
RUNTIME_SNAPSHOT_REQUIRED_RUNTIME_SECTIONS: tuple[str, ...] = tuple(
    key
    for key in RUNTIME_SNAPSHOT_REQUIRED_KEYS
    if key
    not in {
        "snapshot_schema_version",
        "snapshot_kind",
        "exported_by_version",
        "exported_at",
    }
)
RUNTIME_SNAPSHOT_COMPATIBILITY_ADVISORY = (
    "Compatibility analysis is advisory; the user remains authoritative."
)
RUNTIME_SNAPSHOT_MANIFEST_ADVISORY = (
    "Snapshot manifests are advisory; the user remains authoritative."
)
RUNTIME_SNAPSHOT_RETENTION_ADVISORY = (
    "Retention planning is advisory; no snapshots are deleted."
)
RUNTIME_SNAPSHOT_LINEAGE_ADVISORY = (
    "Lineage analysis is advisory; no snapshots are modified."
)
RESTORE_SAFETY_VALIDATION_ADVISORY = (
    "Restore safety validation is advisory; no runtime state is changed."
)
DEFAULT_RUNTIME_SNAPSHOT_RETENTION_KEEP_COUNT = 5


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


@dataclass(frozen=True)
class RuntimeSnapshotCompatibilityCheck:
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
class RuntimeSnapshotCompatibilityReport:
    compatible: bool
    support_level: str
    snapshot_kind: object
    snapshot_schema_version: object
    exported_by_version: object
    compatibility_checks: tuple[RuntimeSnapshotCompatibilityCheck, ...]
    compatibility_warnings: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "compatible": self.compatible,
            "support_level": self.support_level,
            "snapshot_kind": self.snapshot_kind,
            "snapshot_schema_version": self.snapshot_schema_version,
            "exported_by_version": self.exported_by_version,
            "compatibility_checks": [
                check.to_dict() for check in self.compatibility_checks
            ],
            "compatibility_warnings": list(self.compatibility_warnings),
            "advisory": self.advisory,
        }


@dataclass(frozen=True)
class RuntimeSnapshotManifestEntry:
    filename: str
    exported_at: object
    snapshot_kind: object
    snapshot_schema_version: object
    exported_by_version: object
    compatibility_status: str
    support_level: str

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "exported_at": self.exported_at,
            "snapshot_kind": self.snapshot_kind,
            "snapshot_schema_version": self.snapshot_schema_version,
            "exported_by_version": self.exported_by_version,
            "compatibility_status": self.compatibility_status,
            "support_level": self.support_level,
        }


@dataclass(frozen=True)
class RuntimeSnapshotManifest:
    snapshot_count: int
    latest_snapshot: dict | None
    manifest_entries: tuple[RuntimeSnapshotManifestEntry, ...]
    compatibility_summary: dict
    advisory: str

    def to_dict(self) -> dict:
        return {
            "snapshot_count": self.snapshot_count,
            "latest_snapshot": self.latest_snapshot,
            "manifest_entries": [
                entry.to_dict() for entry in self.manifest_entries
            ],
            "compatibility_summary": self.compatibility_summary,
            "advisory": self.advisory,
        }


@dataclass(frozen=True)
class RuntimeSnapshotRetentionPlan:
    snapshot_count: int
    keep_count: int
    prune_candidate_count: int
    keep: tuple[RuntimeSnapshotManifestEntry, ...]
    prune_candidates: tuple[RuntimeSnapshotManifestEntry, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "snapshot_count": self.snapshot_count,
            "keep_count": self.keep_count,
            "prune_candidate_count": self.prune_candidate_count,
            "keep": [entry.to_dict() for entry in self.keep],
            "prune_candidates": [
                entry.to_dict() for entry in self.prune_candidates
            ],
            "advisory": self.advisory,
        }


@dataclass(frozen=True)
class RuntimeSnapshotLineageEntry:
    filename: str
    exported_at: object
    compatibility_status: str
    previous_filename: str | None

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "exported_at": self.exported_at,
            "compatibility_status": self.compatibility_status,
            "previous_filename": self.previous_filename,
        }


@dataclass(frozen=True)
class RuntimeSnapshotLineageChain:
    chain_index: int
    entries: tuple[RuntimeSnapshotLineageEntry, ...]

    @property
    def head(self) -> RuntimeSnapshotLineageEntry:
        return self.entries[-1]

    def to_dict(self) -> dict:
        return {
            "chain_index": self.chain_index,
            "length": len(self.entries),
            "entries": [entry.to_dict() for entry in self.entries],
            "head": self.head.to_dict(),
        }


@dataclass(frozen=True)
class RuntimeSnapshotLineageBreak:
    filename: str
    exported_at: object
    reason: str

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "exported_at": self.exported_at,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RuntimeSnapshotLineage:
    lineage_chains: tuple[RuntimeSnapshotLineageChain, ...]
    lineage_breaks: tuple[RuntimeSnapshotLineageBreak, ...]
    latest_head: RuntimeSnapshotLineageEntry | None
    advisory: str

    def to_dict(self) -> dict:
        return {
            "lineage_chains": [chain.to_dict() for chain in self.lineage_chains],
            "lineage_breaks": [brk.to_dict() for brk in self.lineage_breaks],
            "latest_head": self.latest_head.to_dict() if self.latest_head is not None else None,
            "advisory": self.advisory,
        }


@dataclass(frozen=True)
class RestoreSafetyCheck:
    name: str
    passed: bool
    blocking: bool
    message: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "blocking": self.blocking,
            "message": self.message,
        }


@dataclass(frozen=True)
class RestoreSafetyValidation:
    safe_to_restore: bool
    validation_checks: tuple[RestoreSafetyCheck, ...]
    blocking_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    lineage_status: str
    advisory: str

    def to_dict(self) -> dict:
        return {
            "safe_to_restore": self.safe_to_restore,
            "validation_checks": [check.to_dict() for check in self.validation_checks],
            "blocking_issues": list(self.blocking_issues),
            "warnings": list(self.warnings),
            "lineage_status": self.lineage_status,
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
        check_artifact_sync_drift(root),
    ]
    warnings = (
        find_stale_roadmap_references(root) + find_artifact_sync_drift_warnings(root)
    )
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


def analyze_runtime_snapshot_compatibility(
    root: HarnessPath,
    snapshot_path: Path,
) -> RuntimeSnapshotCompatibilityReport:
    """Return deterministic read-only compatibility analysis for a snapshot."""
    path = snapshot_path if snapshot_path.is_absolute() else root.join(snapshot_path)
    if not path.is_file():
        raise ValueError(f"Invalid runtime snapshot: file not found: {snapshot_path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid runtime snapshot JSON: {error.msg}") from error
    if not isinstance(data, dict):
        raise ValueError("Invalid runtime snapshot: top-level JSON value must be an object.")

    snapshot_kind = data.get("snapshot_kind")
    snapshot_schema_version = data.get("snapshot_schema_version")
    exported_version = data.get("exported_by_version")

    checks: list[RuntimeSnapshotCompatibilityCheck] = []
    warnings: list[str] = []

    kind_supported = (
        isinstance(snapshot_kind, str)
        and snapshot_kind in SUPPORTED_RUNTIME_SNAPSHOT_KINDS
    )
    if kind_supported:
        kind_message = f"Snapshot kind {snapshot_kind!r} is supported."
    elif isinstance(snapshot_kind, str) and snapshot_kind:
        kind_message = (
            f"Unknown snapshot kind: {snapshot_kind!r}; expected {RUNTIME_SNAPSHOT_KIND!r}."
        )
        warnings.append(kind_message)
    else:
        kind_message = "Snapshot kind is missing or not a non-empty string."
        warnings.append(kind_message)
    checks.append(
        RuntimeSnapshotCompatibilityCheck(
            name="snapshot_kind_compatibility",
            passed=kind_supported,
            message=kind_message,
        )
    )

    schema_supported = (
        isinstance(snapshot_schema_version, int)
        and snapshot_schema_version in SUPPORTED_RUNTIME_SNAPSHOT_SCHEMA_VERSIONS
    )
    if schema_supported:
        schema_message = (
            f"Runtime snapshot schema version {snapshot_schema_version} is supported."
        )
    elif isinstance(snapshot_schema_version, int):
        schema_message = (
            "Unsupported runtime snapshot schema version: "
            f"{snapshot_schema_version}; supported versions: "
            f"{', '.join(str(v) for v in SUPPORTED_RUNTIME_SNAPSHOT_SCHEMA_VERSIONS)}."
        )
        warnings.append(schema_message)
    else:
        schema_message = "Snapshot schema version is missing or not an integer."
        warnings.append(schema_message)
    checks.append(
        RuntimeSnapshotCompatibilityCheck(
            name="schema_version_compatibility",
            passed=schema_supported,
            message=schema_message,
        )
    )

    exported_visible = isinstance(exported_version, str) and bool(exported_version)
    exported_message = (
        f"Snapshot exporter version is visible: {exported_version}."
        if exported_visible
        else "Snapshot exporter version is missing or not a non-empty string."
    )
    if not exported_visible:
        warnings.append(exported_message)
    checks.append(
        RuntimeSnapshotCompatibilityCheck(
            name="exported_by_version_visibility",
            passed=exported_visible,
            message=exported_message,
        )
    )

    missing_sections = [
        key for key in RUNTIME_SNAPSHOT_REQUIRED_RUNTIME_SECTIONS if key not in data
    ]
    sections_present = not missing_sections
    sections_message = (
        "All required runtime sections are present."
        if sections_present
        else "Missing required runtime section(s): " + ", ".join(missing_sections) + "."
    )
    if missing_sections:
        warnings.append(sections_message)
    checks.append(
        RuntimeSnapshotCompatibilityCheck(
            name="required_runtime_sections_presence",
            passed=sections_present,
            message=sections_message,
        )
    )

    future_exporter = False
    if exported_visible:
        current_version = exported_by_version()
        future_exporter = version_tuple(exported_version) > version_tuple(current_version)
        future_message = (
            f"Snapshot exporter version {exported_version} is newer than current PCAE runtime {current_version}."
            if future_exporter
            else f"Snapshot exporter version is not newer than current PCAE runtime {current_version}."
        )
        if future_exporter:
            warnings.append(future_message)
    else:
        future_message = "Future-version warning could not compare because exporter version is not visible."
    checks.append(
        RuntimeSnapshotCompatibilityCheck(
            name="future_version_warning_support",
            passed=not future_exporter,
            message=future_message,
        )
    )

    unknown_kind_handled = kind_supported
    unknown_kind_message = (
        "Snapshot kind is recognized; unknown-kind handling was not needed."
        if kind_supported
        else "Unknown snapshot kind is handled as unsupported; no migration or conversion is available."
    )
    checks.append(
        RuntimeSnapshotCompatibilityCheck(
            name="unknown_snapshot_kind_handling",
            passed=unknown_kind_handled,
            message=unknown_kind_message,
        )
    )

    if not kind_supported or not schema_supported:
        support_level = "unsupported"
        if "No migration or automatic conversion is available." not in warnings:
            warnings.append("No migration or automatic conversion is available.")
    elif warnings:
        support_level = "partially-supported"
    else:
        support_level = "supported"

    return RuntimeSnapshotCompatibilityReport(
        compatible=support_level == "supported",
        support_level=support_level,
        snapshot_kind=snapshot_kind,
        snapshot_schema_version=snapshot_schema_version,
        exported_by_version=exported_version,
        compatibility_checks=tuple(checks),
        compatibility_warnings=tuple(unique_preserving_order(warnings)),
        advisory=RUNTIME_SNAPSHOT_COMPATIBILITY_ADVISORY,
    )


def build_runtime_snapshot_manifest(root: HarnessPath) -> RuntimeSnapshotManifest:
    """Return a deterministic read-only index of exported runtime snapshots."""
    snapshot_dir = root.join(RUNTIME_SNAPSHOTS_RELATIVE_PATH)
    if not snapshot_dir.is_dir():
        entries: tuple[RuntimeSnapshotManifestEntry, ...] = ()
        return RuntimeSnapshotManifest(
            snapshot_count=0,
            latest_snapshot=None,
            manifest_entries=entries,
            compatibility_summary=runtime_snapshot_manifest_summary(entries),
            advisory=RUNTIME_SNAPSHOT_MANIFEST_ADVISORY,
        )

    entries = tuple(
        sorted(
            (
                runtime_snapshot_manifest_entry(root, path)
                for path in snapshot_dir.iterdir()
                if path.is_file() and path.suffix == ".json"
            ),
            key=runtime_snapshot_manifest_sort_key,
        )
    )
    latest = entries[0].to_dict() if entries else None
    return RuntimeSnapshotManifest(
        snapshot_count=len(entries),
        latest_snapshot=latest,
        manifest_entries=entries,
        compatibility_summary=runtime_snapshot_manifest_summary(entries),
        advisory=RUNTIME_SNAPSHOT_MANIFEST_ADVISORY,
    )


def runtime_snapshot_manifest_entry(
    root: HarnessPath,
    path: Path,
) -> RuntimeSnapshotManifestEntry:
    filename = path.name
    relative_path = RUNTIME_SNAPSHOTS_RELATIVE_PATH / filename
    try:
        compatibility = analyze_runtime_snapshot_compatibility(root, relative_path)
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return RuntimeSnapshotManifestEntry(
            filename=filename,
            exported_at=None,
            snapshot_kind=None,
            snapshot_schema_version=None,
            exported_by_version=None,
            compatibility_status="incompatible",
            support_level="unsupported",
        )
    return RuntimeSnapshotManifestEntry(
        filename=filename,
        exported_at=data.get("exported_at"),
        snapshot_kind=compatibility.snapshot_kind,
        snapshot_schema_version=compatibility.snapshot_schema_version,
        exported_by_version=compatibility.exported_by_version,
        compatibility_status="compatible"
        if compatibility.compatible
        else "incompatible",
        support_level=compatibility.support_level,
    )


def runtime_snapshot_manifest_sort_key(
    entry: RuntimeSnapshotManifestEntry,
) -> tuple[int, str, str]:
    exported_at = entry.exported_at if isinstance(entry.exported_at, str) else ""
    missing_exported_at = 0 if exported_at else 1
    return (missing_exported_at, reverse_text_sort_key(exported_at), entry.filename)


def reverse_text_sort_key(value: str) -> str:
    return "".join(chr(0x10FFFF - ord(character)) for character in value)


def runtime_snapshot_manifest_summary(
    entries: tuple[RuntimeSnapshotManifestEntry, ...],
) -> dict:
    summary = {
        "compatible": 0,
        "incompatible": 0,
        "supported": 0,
        "partially-supported": 0,
        "unsupported": 0,
    }
    for entry in entries:
        if entry.compatibility_status == "compatible":
            summary["compatible"] += 1
        else:
            summary["incompatible"] += 1
        if entry.support_level in summary:
            summary[entry.support_level] += 1
    return summary


def plan_runtime_snapshot_retention(
    root: HarnessPath,
    keep_latest: int = DEFAULT_RUNTIME_SNAPSHOT_RETENTION_KEEP_COUNT,
) -> RuntimeSnapshotRetentionPlan:
    """Return a read-only retention preview for exported runtime snapshots."""
    manifest = build_runtime_snapshot_manifest(root)
    keep = manifest.manifest_entries[:keep_latest]
    prune_candidates = manifest.manifest_entries[keep_latest:]
    return RuntimeSnapshotRetentionPlan(
        snapshot_count=manifest.snapshot_count,
        keep_count=len(keep),
        prune_candidate_count=len(prune_candidates),
        keep=keep,
        prune_candidates=prune_candidates,
        advisory=RUNTIME_SNAPSHOT_RETENTION_ADVISORY,
    )


def build_runtime_snapshot_lineage(root: HarnessPath) -> RuntimeSnapshotLineage:
    """Return a deterministic read-only lineage analysis of exported runtime snapshots."""
    manifest = build_runtime_snapshot_manifest(root)
    # manifest entries are newest-first; reverse for oldest-first chronological order
    chronological = list(reversed(manifest.manifest_entries))

    chains: list[list[RuntimeSnapshotManifestEntry]] = []
    breaks: list[RuntimeSnapshotManifestEntry] = []
    current: list[RuntimeSnapshotManifestEntry] = []

    for entry in chronological:
        if entry.compatibility_status == "compatible":
            current.append(entry)
        else:
            if current:
                chains.append(current)
                current = []
            breaks.append(entry)

    if current:
        chains.append(current)

    lineage_chains_list: list[RuntimeSnapshotLineageChain] = []
    for i, chain in enumerate(chains):
        entries = tuple(
            RuntimeSnapshotLineageEntry(
                filename=e.filename,
                exported_at=e.exported_at,
                compatibility_status=e.compatibility_status,
                previous_filename=chain[j - 1].filename if j > 0 else None,
            )
            for j, e in enumerate(chain)
        )
        lineage_chains_list.append(
            RuntimeSnapshotLineageChain(chain_index=i, entries=entries)
        )

    lineage_chains = tuple(lineage_chains_list)
    lineage_breaks = tuple(
        RuntimeSnapshotLineageBreak(
            filename=entry.filename,
            exported_at=entry.exported_at,
            reason="incompatible snapshot breaks lineage continuity",
        )
        for entry in breaks
    )
    latest_head = lineage_chains[-1].head if lineage_chains else None

    return RuntimeSnapshotLineage(
        lineage_chains=lineage_chains,
        lineage_breaks=lineage_breaks,
        latest_head=latest_head,
        advisory=RUNTIME_SNAPSHOT_LINEAGE_ADVISORY,
    )


def validate_runtime_snapshot_restore_safety(
    root: HarnessPath,
    snapshot_path: Path,
) -> RestoreSafetyValidation:
    """Return deterministic read-only restore safety validation for a runtime snapshot."""
    checks: list[RestoreSafetyCheck] = []
    blocking_issues: list[str] = []
    warnings_list: list[str] = []
    lineage_status = "unknown"

    # 1. Snapshot compatibility status
    try:
        compat_report = analyze_runtime_snapshot_compatibility(root, snapshot_path)
    except ValueError as error:
        message = str(error)
        checks.append(RestoreSafetyCheck(
            name="snapshot_compatibility",
            passed=False,
            blocking=True,
            message=message,
        ))
        blocking_issues.append(message)
        return RestoreSafetyValidation(
            safe_to_restore=False,
            validation_checks=tuple(checks),
            blocking_issues=tuple(blocking_issues),
            warnings=(),
            lineage_status=lineage_status,
            advisory=RESTORE_SAFETY_VALIDATION_ADVISORY,
        )

    if compat_report.compatible:
        checks.append(RestoreSafetyCheck(
            name="snapshot_compatibility",
            passed=True,
            blocking=False,
            message="Snapshot is compatible.",
        ))
    else:
        message = "Snapshot is not compatible; restore is not safe."
        checks.append(RestoreSafetyCheck(
            name="snapshot_compatibility",
            passed=False,
            blocking=True,
            message=message,
        ))
        blocking_issues.append(message)

    # 2. Snapshot support level
    support_level = compat_report.support_level
    if support_level == "supported":
        checks.append(RestoreSafetyCheck(
            name="snapshot_support_level",
            passed=True,
            blocking=False,
            message=f"Snapshot support level is '{support_level}'.",
        ))
    elif support_level == "partially-supported":
        message = (
            f"Snapshot support level is '{support_level}';"
            " restore may not cover all runtime sections."
        )
        checks.append(RestoreSafetyCheck(
            name="snapshot_support_level",
            passed=False,
            blocking=False,
            message=message,
        ))
        warnings_list.append(message)
    else:
        message = f"Snapshot support level is '{support_level}'; restore is blocked."
        checks.append(RestoreSafetyCheck(
            name="snapshot_support_level",
            passed=False,
            blocking=True,
            message=message,
        ))
        blocking_issues.append(message)

    # 3. Repo cleanliness
    try:
        changes = read_git_changes(root)
        if not changes:
            checks.append(RestoreSafetyCheck(
                name="repo_cleanliness",
                passed=True,
                blocking=False,
                message="Repository working tree is clean.",
            ))
        else:
            message = (
                f"Repository has {len(changes)} uncommitted change(s);"
                " restore may overwrite in-progress work."
            )
            checks.append(RestoreSafetyCheck(
                name="repo_cleanliness",
                passed=False,
                blocking=True,
                message=message,
            ))
            blocking_issues.append(message)
    except (OSError, subprocess.CalledProcessError):
        message = "Repository cleanliness could not be determined."
        checks.append(RestoreSafetyCheck(
            name="repo_cleanliness",
            passed=False,
            blocking=True,
            message=message,
        ))
        blocking_issues.append(message)

    # 4. Session continuity state
    check_result = run_checks(root)
    continuity = session_continuity_status(check_result)
    if continuity == "verified":
        checks.append(RestoreSafetyCheck(
            name="session_continuity",
            passed=True,
            blocking=False,
            message="Session continuity is verified.",
        ))
    else:
        message = (
            f"Session continuity is '{continuity}';"
            " snapshot may not match current session state."
        )
        checks.append(RestoreSafetyCheck(
            name="session_continuity",
            passed=False,
            blocking=False,
            message=message,
        ))
        warnings_list.append(message)

    # 5. Active task presence
    active_task = find_latest_active_task(root)
    if active_task is not None:
        checks.append(RestoreSafetyCheck(
            name="active_task_presence",
            passed=True,
            blocking=False,
            message=f"Active task present: {active_task.task_id}.",
        ))
    else:
        message = "No active task found; restore may not correspond to an active governance context."
        checks.append(RestoreSafetyCheck(
            name="active_task_presence",
            passed=False,
            blocking=False,
            message=message,
        ))
        warnings_list.append(message)

    # 6. Policy configuration validity
    policy = load_policy(root)
    if policy.valid:
        checks.append(RestoreSafetyCheck(
            name="policy_configuration",
            passed=True,
            blocking=False,
            message=f"Policy configuration is valid ({policy.source}).",
        ))
    else:
        message = policy.error or "Policy configuration is invalid."
        checks.append(RestoreSafetyCheck(
            name="policy_configuration",
            passed=False,
            blocking=True,
            message=message,
        ))
        blocking_issues.append(message)

    # 7. Agent lock safety
    lock_state = build_agent_lock_state(root)
    locked = bool(lock_state.get("locked"))
    is_stale = bool(lock_state.get("stale"))
    holding_agent = lock_state.get("agent_id")
    if locked and not is_stale:
        message = (
            f"Agent lock is held by '{holding_agent}' and is not stale;"
            " restore may conflict with active agent work."
        )
        checks.append(RestoreSafetyCheck(
            name="agent_lock_safety",
            passed=False,
            blocking=False,
            message=message,
        ))
        warnings_list.append(message)
    elif locked and is_stale:
        checks.append(RestoreSafetyCheck(
            name="agent_lock_safety",
            passed=True,
            blocking=False,
            message=(
                f"Agent lock is held by '{holding_agent}' but is stale;"
                " restore is unlikely to conflict."
            ),
        ))
    else:
        checks.append(RestoreSafetyCheck(
            name="agent_lock_safety",
            passed=True,
            blocking=False,
            message="No active agent lock held; restore would not conflict with agent work.",
        ))

    # 8. Lineage continuity
    lineage = build_runtime_snapshot_lineage(root)
    snapshot_filename = Path(snapshot_path).name
    lineage_status = _snapshot_lineage_status(snapshot_filename, lineage)
    if lineage_status in ("head_of_chain", "chain_start", "in_chain"):
        checks.append(RestoreSafetyCheck(
            name="lineage_continuity",
            passed=True,
            blocking=False,
            message=(
                f"Snapshot is part of a compatible lineage chain"
                f" (position: {lineage_status})."
            ),
        ))
    elif lineage_status == "lineage_break":
        message = (
            "Snapshot is a lineage break; restoring it would skip governance continuity."
        )
        checks.append(RestoreSafetyCheck(
            name="lineage_continuity",
            passed=False,
            blocking=False,
            message=message,
        ))
        warnings_list.append(message)
    else:
        message = (
            "Snapshot lineage status could not be determined;"
            " it may not be indexed in the current manifest."
        )
        checks.append(RestoreSafetyCheck(
            name="lineage_continuity",
            passed=False,
            blocking=False,
            message=message,
        ))
        warnings_list.append(message)

    # 9. Governance health/check status
    if check_result.passed:
        checks.append(RestoreSafetyCheck(
            name="governance_health",
            passed=True,
            blocking=False,
            message="Governance check passed.",
        ))
    else:
        message = "Governance check did not pass; restore may not be safe."
        checks.append(RestoreSafetyCheck(
            name="governance_health",
            passed=False,
            blocking=False,
            message=message,
        ))
        warnings_list.append(message)

    return RestoreSafetyValidation(
        safe_to_restore=len(blocking_issues) == 0,
        validation_checks=tuple(checks),
        blocking_issues=tuple(blocking_issues),
        warnings=tuple(warnings_list),
        lineage_status=lineage_status,
        advisory=RESTORE_SAFETY_VALIDATION_ADVISORY,
    )


def _snapshot_lineage_status(
    filename: str,
    lineage: RuntimeSnapshotLineage,
) -> str:
    for chain in lineage.lineage_chains:
        for entry in chain.entries:
            if entry.filename == filename:
                if entry is chain.head:
                    return "head_of_chain"
                if entry.previous_filename is None:
                    return "chain_start"
                return "in_chain"
    for brk in lineage.lineage_breaks:
        if brk.filename == filename:
            return "lineage_break"
    return "unknown"


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


def version_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for value in version.split("."):
        digits = ""
        for character in value:
            if not character.isdigit():
                break
            digits += character
        if digits == "":
            break
        parts.append(int(digits))
    return tuple(parts)


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


# ---------------------------------------------------------------------------
# Governance artifact lifecycle classification (Phase 35R)
# ---------------------------------------------------------------------------

_ARTIFACT_CLASSIFICATION_REGISTRY: dict[str, tuple[str, str]] = {
    "PROJECT_STATUS.md": (
        "operational",
        "live roadmap guidance; operational drift candidate",
    ),
    "tasks/TODO.md": (
        "operational",
        "pending work tracking; operational drift candidate",
    ),
    "CHANGELOG.md": (
        "historical",
        "historical change record; preserved by design",
    ),
    "tasks/DONE.md": (
        "historical",
        "historical completion record; preserved by design",
    ),
    ".pcae/provenance-history.json": (
        "runtime",
        "runtime governance state; not proposed for source repair",
    ),
    ".pcae/agent-lock.json": (
        "runtime",
        "runtime governance state; not proposed for source repair",
    ),
    ".pcae/session.json": (
        "runtime",
        "runtime governance state; not proposed for source repair",
    ),
}

_GENERATED_ARTIFACT_PREFIXES: tuple[str, ...] = (
    ".pcae/runtime-snapshots/",
    ".pcae/context-packs/",
    ".pcae/continuity-packs/",
)


@dataclass(frozen=True)
class ArtifactClassification:
    artifact_type: str  # canonical artifact path identifier
    artifact_class: str  # "operational" | "historical" | "runtime" | "generated"
    governance_role: str

    def to_dict(self) -> dict:
        return {
            "artifact_type": self.artifact_type,
            "artifact_class": self.artifact_class,
            "governance_role": self.governance_role,
        }


def classify_governance_artifact(artifact: str) -> ArtifactClassification:
    """Return deterministic classification for a governance artifact path."""
    if artifact in _ARTIFACT_CLASSIFICATION_REGISTRY:
        artifact_class, governance_role = _ARTIFACT_CLASSIFICATION_REGISTRY[artifact]
        return ArtifactClassification(
            artifact_type=artifact,
            artifact_class=artifact_class,
            governance_role=governance_role,
        )
    for prefix in _GENERATED_ARTIFACT_PREFIXES:
        if artifact.startswith(prefix):
            return ArtifactClassification(
                artifact_type=artifact,
                artifact_class="generated",
                governance_role="generated artifact; not proposed for source repair",
            )
    return ArtifactClassification(
        artifact_type=artifact,
        artifact_class="operational",
        governance_role="governance artifact; treated as operational by default",
    )


ARTIFACT_CLASSIFICATION_ADVISORY = (
    "Artifact classification is advisory; the user remains authoritative."
)


@dataclass(frozen=True)
class GovernanceArtifactEntry:
    path: str
    artifact_class: str  # "operational" | "historical" | "runtime" | "generated"
    governance_role: str
    repair_policy: str   # "actionable" | "preserve" | "ignore"
    source_control_role: str  # "tracked" | "ignored" | "generated_ignored"

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "artifact_class": self.artifact_class,
            "governance_role": self.governance_role,
            "repair_policy": self.repair_policy,
            "source_control_role": self.source_control_role,
        }


GOVERNANCE_ARTIFACT_REGISTRY: tuple[GovernanceArtifactEntry, ...] = (
    GovernanceArtifactEntry(
        path="PROJECT_STATUS.md",
        artifact_class="operational",
        governance_role="live roadmap guidance; operational drift candidate",
        repair_policy="actionable",
        source_control_role="tracked",
    ),
    GovernanceArtifactEntry(
        path="tasks/TODO.md",
        artifact_class="operational",
        governance_role="pending work tracking; operational drift candidate",
        repair_policy="actionable",
        source_control_role="tracked",
    ),
    GovernanceArtifactEntry(
        path="CHANGELOG.md",
        artifact_class="historical",
        governance_role="historical change record; preserved by design",
        repair_policy="preserve",
        source_control_role="tracked",
    ),
    GovernanceArtifactEntry(
        path="tasks/DONE.md",
        artifact_class="historical",
        governance_role="historical completion record; preserved by design",
        repair_policy="preserve",
        source_control_role="tracked",
    ),
    GovernanceArtifactEntry(
        path=".pcae/provenance-history.json",
        artifact_class="runtime",
        governance_role="runtime governance state; not proposed for source repair",
        repair_policy="ignore",
        source_control_role="ignored",
    ),
    GovernanceArtifactEntry(
        path=".pcae/agent-lock.json",
        artifact_class="runtime",
        governance_role="runtime governance state; not proposed for source repair",
        repair_policy="ignore",
        source_control_role="ignored",
    ),
    GovernanceArtifactEntry(
        path=".pcae/session.json",
        artifact_class="runtime",
        governance_role="runtime governance state; not proposed for source repair",
        repair_policy="ignore",
        source_control_role="ignored",
    ),
    GovernanceArtifactEntry(
        path=".pcae/runtime-snapshots/**",
        artifact_class="generated",
        governance_role="generated artifact; not proposed for source repair",
        repair_policy="ignore",
        source_control_role="generated_ignored",
    ),
    GovernanceArtifactEntry(
        path=".pcae/context-packs/**",
        artifact_class="generated",
        governance_role="generated artifact; not proposed for source repair",
        repair_policy="ignore",
        source_control_role="generated_ignored",
    ),
    GovernanceArtifactEntry(
        path=".pcae/continuity-packs/**",
        artifact_class="generated",
        governance_role="generated artifact; not proposed for source repair",
        repair_policy="ignore",
        source_control_role="generated_ignored",
    ),
)


@dataclass(frozen=True)
class GovernanceArtifactReport:
    artifacts: tuple[GovernanceArtifactEntry, ...]
    classes: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "artifacts": [a.to_dict() for a in self.artifacts],
            "classes": list(self.classes),
            "advisory": self.advisory,
        }


def build_governance_artifact_registry() -> GovernanceArtifactReport:
    """Return the governance artifact registry grouped by class."""
    seen: dict[str, None] = {}
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        seen[entry.artifact_class] = None
    return GovernanceArtifactReport(
        artifacts=GOVERNANCE_ARTIFACT_REGISTRY,
        classes=tuple(seen),
        advisory=ARTIFACT_CLASSIFICATION_ADVISORY,
    )


# ---------------------------------------------------------------------------
# Governance artifact synchronization validation (Phase 35L)
# ---------------------------------------------------------------------------

GOVERNANCE_SYNC_CHECK_ADVISORY = (
    "Synchronization analysis is advisory; no governance artifacts are modified."
)

_SYNC_ARTIFACT_TODO = Path("tasks") / "TODO.md"
_SYNC_ARTIFACT_DONE = Path("tasks") / "DONE.md"
_SYNC_ARTIFACT_CHANGELOG = Path("CHANGELOG.md")

# Checks that the current governance audit runs.  Any check name absent from
# this set and listed in _GOVERNANCE_AUDIT_GAP_CHECKS is reported as a gap.
_GOVERNANCE_AUDIT_KNOWN_CHECKS: frozenset[str] = frozenset({
    "project_status_current_phase",
    "project_status_next",
    "active_task",
    "session_continuity",
    "provenance_history",
    "policy_configuration",
    "agent_registry",
    "artifact_sync_drift",  # added in Phase 35M
})

# Capability checks that SHOULD exist in the audit but do not (yet).
_GOVERNANCE_AUDIT_GAP_CHECKS: tuple[str, ...] = (
    "artifact_sync_drift",
)


@dataclass(frozen=True)
class GovernanceSyncCheckResult:
    synchronized: bool
    operational_stale_references: tuple[str, ...]
    preserved_historical_references: tuple[str, ...]
    completed_todo_entries: tuple[str, ...]
    inconsistent_entries: tuple[str, ...]
    governance_drift_warnings: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "advisory": self.advisory,
            "completed_todo_entries": list(self.completed_todo_entries),
            "governance_drift_warnings": list(self.governance_drift_warnings),
            "inconsistent_entries": list(self.inconsistent_entries),
            "operational_stale_references": list(self.operational_stale_references),
            "preserved_historical_references": list(self.preserved_historical_references),
            "synchronized": self.synchronized,
        }


def _read_sync_artifact(root: HarnessPath, rel_path: Path) -> str:
    path = root.join(rel_path)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_section_bullets(text: str, section_name: str) -> list[str]:
    """Return bullet item bodies (without leading dash) from a ## section."""
    items: list[str] = []
    in_section = False
    target = f"## {section_name}"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped == target
            continue
        if in_section and stripped.startswith("-"):
            items.append(stripped[1:].strip())
    return items


def _extract_pcae_commands(text: str) -> list[str]:
    """Extract `pcae ...` command strings (without backticks) from text."""
    return re.findall(r'`(pcae[^`]+)`', text)


def _item_appears_completed(item: str, done_text: str, changelog_text: str) -> bool:
    """Return True if any pcae command named in item appears in done or changelog."""
    commands = _extract_pcae_commands(item)
    if not commands:
        return False
    reference = done_text + "\n" + changelog_text
    return any(f"`{cmd}`" in reference for cmd in commands)


def _stale_references_across_artifacts(
    root: HarnessPath,
    phrases: tuple[str, ...],
) -> list[str]:
    artifact_paths = (
        PROJECT_STATUS_RELATIVE_PATH,
        _SYNC_ARTIFACT_TODO,
        _SYNC_ARTIFACT_CHANGELOG,
        _SYNC_ARTIFACT_DONE,
    )
    found: list[str] = []
    for rel_path in artifact_paths:
        text = _read_sync_artifact(root, rel_path)
        for phrase in phrases:
            if phrase in text:
                found.append(
                    f"{rel_path.as_posix()}: stale reference: {phrase!r}"
                )
    return found


def check_artifact_sync_drift(root: HarnessPath) -> GovernanceAuditCheck:
    """Return an audit check for governance artifact synchronization drift.

    Covers completed-TODO and inconsistent-roadmap issues only.  Stale
    KNOWN_STALE_PHRASES are already surfaced by find_stale_roadmap_references
    and are intentionally excluded here to avoid double-counting.
    """
    sync = check_governance_sync(root)
    issue_count = len(sync.completed_todo_entries) + len(sync.inconsistent_entries)
    if issue_count == 0:
        return GovernanceAuditCheck(
            name="artifact_sync_drift",
            passed=True,
            message="Governance artifacts are synchronized; no artifact drift detected.",
        )
    return GovernanceAuditCheck(
        name="artifact_sync_drift",
        passed=True,  # check ran successfully; issues are surfaced as warnings
        message=(
            f"Artifact sync drift detected: {issue_count} issue(s);"
            " see audit warnings for details."
        ),
    )


def find_artifact_sync_drift_warnings(
    root: HarnessPath,
) -> tuple[CoherenceWarning, ...]:
    """Return CoherenceWarning items for completed-TODO and inconsistent-roadmap drift.

    Stale KNOWN_STALE_PHRASES are excluded; they are already covered by
    find_stale_roadmap_references.
    """
    sync = check_governance_sync(root)
    warnings: list[CoherenceWarning] = []
    for entry in sync.completed_todo_entries:
        warnings.append(CoherenceWarning(
            document="tasks/TODO.md",
            message=f"Completed TODO entry still listed as pending: {entry!r}",
        ))
    for entry in sync.inconsistent_entries:
        warnings.append(CoherenceWarning(
            document="PROJECT_STATUS.md",
            message=entry,
        ))
    return tuple(warnings)


GOVERNANCE_SYNC_REPAIR_ADVISORY = (
    "Repair preview is advisory; no governance artifacts are modified."
)

def _artifact_type_for(artifact: str) -> str:
    return classify_governance_artifact(artifact).artifact_class


def _stale_ref_proposed_action(artifact: str) -> str:
    artifact_class = classify_governance_artifact(artifact).artifact_class
    if artifact_class == "historical":
        return "preserve"
    if artifact_class in ("runtime", "generated"):
        return "ignore"
    if artifact == "PROJECT_STATUS.md":
        return "update"
    return "remove"


@dataclass(frozen=True)
class SyncRepairEntry:
    artifact: str
    artifact_type: str
    stale_entry: str
    proposed_action: str
    rationale: str

    def to_dict(self) -> dict:
        classification = classify_governance_artifact(self.artifact)
        return {
            "artifact": self.artifact,
            "artifact_type": self.artifact_type,
            "artifact_class": classification.artifact_class,
            "governance_role": classification.governance_role,
            "stale_entry": self.stale_entry,
            "proposed_action": self.proposed_action,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class GovernanceSyncRepairPreview:
    repairable: bool
    proposed_repairs: tuple[SyncRepairEntry, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "repairable": self.repairable,
            "proposed_repairs": [r.to_dict() for r in self.proposed_repairs],
            "advisory": self.advisory,
        }


def plan_governance_sync_repairs(root: HarnessPath) -> GovernanceSyncRepairPreview:
    """Return deterministic read-only repair previews for stale governance artifacts."""
    sync = check_governance_sync(root)
    repairs: list[SyncRepairEntry] = []

    for entry in sync.completed_todo_entries:
        repairs.append(SyncRepairEntry(
            artifact="tasks/TODO.md",
            artifact_type="operational",
            stale_entry=entry,
            proposed_action="remove",
            rationale=(
                "Entry is already completed; it appears in DONE.md or CHANGELOG.md "
                "and should be removed from the Pending section."
            ),
        ))

    for ref in (*sync.operational_stale_references, *sync.preserved_historical_references):
        artifact_part, sep, stale_phrase = ref.partition(": stale reference: ")
        artifact = artifact_part if sep else "governance artifact"
        stale_entry = stale_phrase if sep else ref
        artifact_type = _artifact_type_for(artifact)
        proposed_action = _stale_ref_proposed_action(artifact)
        if artifact_type == "historical":
            rationale = (
                "Historical record; stale reference is preserved as-is. "
                "Historical artifacts are not proposed for modification."
            )
        else:
            rationale = (
                "Feature already implemented; stale reference creates orchestration risk "
                "for agents reading roadmap guidance."
            )
        repairs.append(SyncRepairEntry(
            artifact=artifact,
            artifact_type=artifact_type,
            stale_entry=stale_entry,
            proposed_action=proposed_action,
            rationale=rationale,
        ))

    for entry in sync.inconsistent_entries:
        repairs.append(SyncRepairEntry(
            artifact="PROJECT_STATUS.md",
            artifact_type="operational",
            stale_entry=entry,
            proposed_action="update",
            rationale=(
                "Roadmap item appears already completed in DONE.md; "
                "the Next section guidance should be updated."
            ),
        ))

    for warning in sync.governance_drift_warnings:
        repairs.append(SyncRepairEntry(
            artifact="governance audit",
            artifact_type="operational",
            stale_entry=warning,
            proposed_action="update",
            rationale=(
                "Governance audit has a capability gap; "
                "update the audit to include this check."
            ),
        ))

    return GovernanceSyncRepairPreview(
        repairable=True,
        proposed_repairs=tuple(repairs),
        advisory=GOVERNANCE_SYNC_REPAIR_ADVISORY,
    )


@dataclass(frozen=True)
class AppliedSyncRepairResult:
    applied_repairs: tuple[SyncRepairEntry, ...]
    no_op: bool

    def to_dict(self) -> dict:
        return {
            "applied_repairs": [r.to_dict() for r in self.applied_repairs],
            "no_op": self.no_op,
        }


def apply_governance_sync_repairs(root: HarnessPath) -> AppliedSyncRepairResult:
    """Remove completed entries from tasks/TODO.md; skip all historical artifacts."""
    preview = plan_governance_sync_repairs(root)
    applicable = [
        r for r in preview.proposed_repairs
        if r.artifact_type == "operational"
        and r.artifact == "tasks/TODO.md"
        and r.proposed_action == "remove"
    ]
    if not applicable:
        return AppliedSyncRepairResult(applied_repairs=(), no_op=True)

    todo_path = root.join(_SYNC_ARTIFACT_TODO)
    if not todo_path.is_file():
        return AppliedSyncRepairResult(applied_repairs=(), no_op=True)

    entries_to_remove = {f"- {r.stale_entry}" for r in applicable}
    original = todo_path.read_text(encoding="utf-8")
    filtered = [
        line for line in original.splitlines(keepends=True)
        if line.strip() not in entries_to_remove
    ]
    todo_path.write_text("".join(filtered), encoding="utf-8")
    return AppliedSyncRepairResult(applied_repairs=tuple(applicable), no_op=False)


# ---------------------------------------------------------------------------
# Governance registry consumers audit (Phase 35T)
# ---------------------------------------------------------------------------

REGISTRY_AUDIT_ADVISORY = (
    "Registry audit is advisory; no governance artifacts are modified."
)

_REGISTRY_CONSUMERS: tuple[tuple[str, bool, str], ...] = (
    (
        "sync-check",
        True,
        "uses classify_governance_artifact via _artifact_type_for",
    ),
    (
        "sync-repair",
        True,
        "uses classify_governance_artifact via _artifact_type_for and _stale_ref_proposed_action",
    ),
    (
        "governance audit",
        True,
        "uses classify_governance_artifact via artifact_sync_drift check",
    ),
    (
        "artifact registry",
        True,
        "uses GOVERNANCE_ARTIFACT_REGISTRY directly",
    ),
)


@dataclass(frozen=True)
class RegistryConsumerAuditEntry:
    name: str
    registry_backed: bool
    note: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "registry_backed": self.registry_backed,
            "note": self.note,
        }


@dataclass(frozen=True)
class RegistryAuditResult:
    registry_audit_status: str
    consumers: tuple[RegistryConsumerAuditEntry, ...]
    warnings: tuple[str, ...]
    advisory: str

    def to_dict(self) -> dict:
        return {
            "registry_audit_status": self.registry_audit_status,
            "consumers": [c.to_dict() for c in self.consumers],
            "warnings": list(self.warnings),
            "advisory": self.advisory,
        }


def audit_registry_consumers() -> RegistryAuditResult:
    """Return read-only audit of governance registry consumer coverage."""
    consumers = tuple(
        RegistryConsumerAuditEntry(name=name, registry_backed=backed, note=note)
        for name, backed, note in _REGISTRY_CONSUMERS
    )
    warnings = tuple(
        f"{c.name}: not registry-backed"
        for c in consumers
        if not c.registry_backed
    )
    return RegistryAuditResult(
        registry_audit_status="pass" if not warnings else "warn",
        consumers=consumers,
        warnings=warnings,
        advisory=REGISTRY_AUDIT_ADVISORY,
    )


def check_governance_sync(root: HarnessPath) -> GovernanceSyncCheckResult:
    """Return read-only governance artifact synchronization analysis.

    Checks four deterministic conditions across PROJECT_STATUS.md,
    tasks/TODO.md, CHANGELOG.md, and tasks/DONE.md.  Never mutates any file.
    """
    todo_text = _read_sync_artifact(root, _SYNC_ARTIFACT_TODO)
    done_text = _read_sync_artifact(root, _SYNC_ARTIFACT_DONE)
    changelog_text = _read_sync_artifact(root, _SYNC_ARTIFACT_CHANGELOG)
    project_status_text = _read_sync_artifact(root, PROJECT_STATUS_RELATIVE_PATH)

    # 1. Stale references: known stale phrases in any of the four artifacts.
    #    Split into operational (actionable drift) and historical (preserved records).
    all_stale = _stale_references_across_artifacts(root, KNOWN_STALE_PHRASES)
    operational_stale_references = [
        ref for ref in all_stale
        if _artifact_type_for(ref.partition(": stale reference: ")[0]) == "operational"
    ]
    preserved_historical_references = [
        ref for ref in all_stale
        if _artifact_type_for(ref.partition(": stale reference: ")[0]) == "historical"
    ]

    # 2. Completed TODO entries: Pending items whose pcae commands appear in
    #    DONE.md or CHANGELOG.md, indicating the work is already done.
    pending_items = _parse_section_bullets(todo_text, "Pending")
    completed_todo_entries = [
        item
        for item in pending_items
        if _item_appears_completed(item, done_text, changelog_text)
    ]

    # 3. Inconsistent "Next" roadmap entries: items in PROJECT_STATUS.md's
    #    Next section whose pcae commands appear in DONE.md, meaning they
    #    should have been removed from the roadmap.
    next_items = _parse_section_bullets(project_status_text, "Next")
    inconsistent_entries = [
        f"Next roadmap item appears already completed: {item!r}"
        for item in next_items
        if _item_appears_completed(item, done_text, done_text)
    ]

    # 4. Governance drift warnings: capability gaps in the current audit.
    governance_drift_warnings = [
        f"Governance audit has no '{gap}' check;"
        " artifact synchronization drift is not currently audited."
        for gap in _GOVERNANCE_AUDIT_GAP_CHECKS
        if gap not in _GOVERNANCE_AUDIT_KNOWN_CHECKS
    ]

    # Historical preserved references are not actionable drift; only
    # operational stale references, completed TODO entries, and inconsistent
    # roadmap entries make the repo out of sync.
    synchronized = (
        len(operational_stale_references) == 0
        and len(completed_todo_entries) == 0
        and len(inconsistent_entries) == 0
    )

    return GovernanceSyncCheckResult(
        synchronized=synchronized,
        operational_stale_references=tuple(operational_stale_references),
        preserved_historical_references=tuple(preserved_historical_references),
        completed_todo_entries=tuple(completed_todo_entries),
        inconsistent_entries=tuple(inconsistent_entries),
        governance_drift_warnings=tuple(governance_drift_warnings),
        advisory=GOVERNANCE_SYNC_CHECK_ADVISORY,
    )
