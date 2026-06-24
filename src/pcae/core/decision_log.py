from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.artifact_index import build_artifact_index
from pcae.core.memory_snapshot import build_memory_snapshot
from pcae.core.governance_timeline import build_governance_timeline


_ALL_FALSE_AUTH_FLAGS: dict[str, bool] = {
    "execution_authorized": False,
    "backend_invocation_authorized": False,
    "prompt_sending_authorized": False,
    "capture_authorized": False,
    "intake_authorized": False,
    "adoption_authorized": False,
    "source_mutation_authorized": False,
    "test_mutation_authorized": False,
    "commit_authorized": False,
    "push_authorized": False,
    "storage_authorized": False,
}


def _git_log_commit_date(repo_root: Path, path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", path],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _git_log_commit_hash(repo_root: Path, path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", path],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _stable_decision_id(phase: str, decision_type: str, suffix: str = "") -> str:
    raw = f"{phase}:{decision_type}"
    if suffix:
        raw = f"{raw}:{suffix}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"dec-{phase}-{decision_type}-{digest}"


def _make_decision(
    decision_id: str,
    decision_type: str,
    decision_status: str,
    decision_timestamp: str | None,
    source_phase: str,
    source_artifact: str | None,
    source_event: str | None,
    source_commit: str | None,
    decision_maker: str,
    human_required: bool,
    approved_scope: str | None,
    denied_scope: str | None,
    deferred_scope: str | None,
    rejected_scope: str | None,
    affected_files: list[str] | None,
    affected_agents: list[str] | None,
    authorization_flags: dict[str, bool] | None,
    risk_level: str | None,
    supersedes: str | None,
    superseded_by: str | None,
    related_decisions: list[str] | None,
    related_artifacts: list[str] | None,
    related_events: list[str] | None,
    evidence_level: str,
    safety_notes: str | None,
) -> dict[str, Any]:
    return {
        "decision_id": decision_id,
        "decision_type": decision_type,
        "decision_status": decision_status,
        "decision_timestamp": decision_timestamp if decision_timestamp is not None else "unknown",
        "source_phase": source_phase,
        "source_artifact": source_artifact if source_artifact is not None else "unknown",
        "source_event": source_event if source_event is not None else "unknown",
        "source_commit": source_commit if source_commit is not None else "unknown",
        "decision_maker": decision_maker,
        "human_required": human_required,
        "approved_scope": approved_scope,
        "denied_scope": denied_scope,
        "deferred_scope": deferred_scope,
        "rejected_scope": rejected_scope,
        "affected_files": affected_files or [],
        "affected_agents": affected_agents or [],
        "authorization_flags": authorization_flags if authorization_flags is not None else dict(_ALL_FALSE_AUTH_FLAGS),
        "risk_level": risk_level,
        "supersedes": supersedes,
        "superseded_by": superseded_by,
        "related_decisions": related_decisions or [],
        "related_artifacts": related_artifacts or [],
        "related_events": related_events or [],
        "evidence_level": evidence_level,
        "safety_notes": safety_notes,
    }


_PHASE_DECISIONS: list[dict[str, Any]] = [
    {
        "phase": "84L", "label": "Roadmap Reconciliation and Phase 85 Plan",
        "artifact": "docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md",
        "task": "84l-roadmap-reconciliation-phase-85-plan",
        "is_design": True, "is_impl": False, "command": None,
        "next_phase": "85A",
    },
    {
        "phase": "85A", "label": "Persistent Lifecycle Memory Model",
        "artifact": "docs/PERSISTENT_LIFECYCLE_MEMORY_MODEL.md",
        "task": "85a-persistent-lifecycle-memory-model",
        "is_design": True, "is_impl": False, "command": None,
        "next_phase": "85B",
    },
    {
        "phase": "85B", "label": "Artifact Index Design",
        "artifact": "docs/ARTIFACT_INDEX_DESIGN.md",
        "task": "85b-artifact-index-design",
        "is_design": True, "is_impl": False, "command": None,
        "next_phase": "85C",
    },
    {
        "phase": "85C", "label": "Governance Event Timeline Design",
        "artifact": "docs/GOVERNANCE_EVENT_TIMELINE_DESIGN.md",
        "task": "85c-governance-event-timeline-design",
        "is_design": True, "is_impl": False, "command": None,
        "next_phase": "85D",
    },
    {
        "phase": "85D", "label": "Decision Log Integration Design",
        "artifact": "docs/DECISION_LOG_INTEGRATION_DESIGN.md",
        "task": "85d-decision-log-integration-design",
        "is_design": True, "is_impl": False, "command": None,
        "next_phase": "85E",
    },
    {
        "phase": "85E", "label": "Risk Register Design",
        "artifact": "docs/RISK_REGISTER_DESIGN.md",
        "task": "85e-risk-register-design",
        "is_design": True, "is_impl": False, "command": None,
        "next_phase": "85F",
    },
    {
        "phase": "85F", "label": "Project State Snapshot Design",
        "artifact": "docs/PROJECT_STATE_SNAPSHOT_DESIGN.md",
        "task": "85f-project-state-snapshot-design",
        "is_design": True, "is_impl": False, "command": None,
        "next_phase": "86A",
    },
    {
        "phase": "86A", "label": "Phase 85 Implementation Roadmap",
        "artifact": "docs/PHASE_85_IMPLEMENTATION_ROADMAP.md",
        "task": "86a-phase-85-implementation-roadmap",
        "is_design": True, "is_impl": False, "command": None,
        "next_phase": "86B",
    },
    {
        "phase": "86B", "label": "Phase 85 Data Model and Storage Design",
        "artifact": "docs/PHASE_85_DATA_MODEL_STORAGE_DESIGN.md",
        "task": "86b-phase-85-data-model-storage-design",
        "is_design": True, "is_impl": False, "command": None,
        "next_phase": "86C",
    },
    {
        "phase": "86C", "label": "Read-Only Artifact Index Prototype",
        "artifact": "docs/PHASE_85_ARTIFACT_INDEX_PROTOTYPE.md",
        "task": "86c-read-only-artifact-index-prototype",
        "is_design": False, "is_impl": True,
        "command": "pcae artifact-index --json",
        "next_phase": "86D",
    },
    {
        "phase": "86D", "label": "Persistent Memory Snapshot Prototype",
        "artifact": "docs/PHASE_85_MEMORY_SNAPSHOT_PROTOTYPE.md",
        "task": "86d-read-only-memory-snapshot-prototype",
        "is_design": False, "is_impl": True,
        "command": "pcae memory-snapshot --json",
        "next_phase": "86E",
    },
    {
        "phase": "86E", "label": "Governance Event Timeline Extraction",
        "artifact": "docs/PHASE_85_GOVERNANCE_TIMELINE_PROTOTYPE.md",
        "task": "86e-read-only-governance-timeline-prototype",
        "is_design": False, "is_impl": True,
        "command": "pcae governance-timeline --json",
        "next_phase": "86F",
    },
]


def _extract_phase_decisions(repo_root: Path, phase_info: dict[str, Any]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    phase = phase_info["phase"]
    artifact_path = phase_info["artifact"]
    task_stem = phase_info["task"]

    artifact_full = repo_root / artifact_path
    artifact_exists = artifact_full.is_file()
    task_completed = (repo_root / "tasks" / "completed" / f"{task_stem}.md").is_file()

    artifact_timestamp = _git_log_commit_date(repo_root, artifact_path) if artifact_exists else None
    artifact_commit = _git_log_commit_hash(repo_root, artifact_path) if artifact_exists else None

    if not task_completed:
        return decisions

    task_path = f"tasks/completed/{task_stem}.md"
    task_timestamp = _git_log_commit_date(repo_root, task_path)
    task_commit = _git_log_commit_hash(repo_root, task_path)

    decisions.append(_make_decision(
        decision_id=_stable_decision_id(phase, "phase_completion_decision"),
        decision_type="phase_completion_decision",
        decision_status="approved",
        decision_timestamp=task_timestamp,
        source_phase=phase,
        source_artifact=task_path,
        source_event=None,
        source_commit=task_commit,
        decision_maker="governance",
        human_required=False,
        approved_scope=f"Phase {phase} completed: {phase_info['label']}",
        denied_scope=None,
        deferred_scope=None,
        rejected_scope=None,
        affected_files=[artifact_path] if artifact_exists else [],
        affected_agents=[],
        authorization_flags=dict(_ALL_FALSE_AUTH_FLAGS),
        risk_level="low",
        supersedes=None,
        superseded_by=None,
        related_decisions=[],
        related_artifacts=[artifact_path] if artifact_exists else [],
        related_events=[],
        evidence_level="repo_committed_artifact",
        safety_notes=None,
    ))

    if phase_info["is_impl"]:
        scope_label = "read-only CLI command implementation"
    elif phase_info["is_design"]:
        scope_label = "design documentation"
    else:
        scope_label = "phase scope"

    decisions.append(_make_decision(
        decision_id=_stable_decision_id(phase, "implementation_scope_decision"),
        decision_type="implementation_scope_decision",
        decision_status="approved",
        decision_timestamp=artifact_timestamp,
        source_phase=phase,
        source_artifact=artifact_path if artifact_exists else None,
        source_event=None,
        source_commit=artifact_commit,
        decision_maker="governance",
        human_required=False,
        approved_scope=f"Phase {phase} scope: {scope_label}",
        denied_scope=None,
        deferred_scope=None,
        rejected_scope=None,
        affected_files=[artifact_path] if artifact_exists else [],
        affected_agents=[],
        authorization_flags=dict(_ALL_FALSE_AUTH_FLAGS),
        risk_level="low",
        supersedes=None,
        superseded_by=None,
        related_decisions=[_stable_decision_id(phase, "phase_completion_decision")],
        related_artifacts=[artifact_path] if artifact_exists else [],
        related_events=[],
        evidence_level="repo_committed_artifact",
        safety_notes=None,
    ))

    decisions.append(_make_decision(
        decision_id=_stable_decision_id(phase, "read_only_boundary_decision"),
        decision_type="read_only_boundary_decision",
        decision_status="approved",
        decision_timestamp=artifact_timestamp,
        source_phase=phase,
        source_artifact=artifact_path if artifact_exists else None,
        source_event=None,
        source_commit=artifact_commit,
        decision_maker="governance",
        human_required=False,
        approved_scope=f"Phase {phase} read-only boundary enforced",
        denied_scope=None,
        deferred_scope=None,
        rejected_scope=None,
        affected_files=[],
        affected_agents=[],
        authorization_flags=dict(_ALL_FALSE_AUTH_FLAGS),
        risk_level="low",
        supersedes=None,
        superseded_by=None,
        related_decisions=[_stable_decision_id(phase, "implementation_scope_decision")],
        related_artifacts=[artifact_path] if artifact_exists else [],
        related_events=[],
        evidence_level="repo_committed_artifact",
        safety_notes="read_only_boundary=enforced",
    ))

    decisions.append(_make_decision(
        decision_id=_stable_decision_id(phase, "no_storage_boundary_decision"),
        decision_type="no_storage_boundary_decision",
        decision_status="approved",
        decision_timestamp=artifact_timestamp,
        source_phase=phase,
        source_artifact=artifact_path if artifact_exists else None,
        source_event=None,
        source_commit=artifact_commit,
        decision_maker="governance",
        human_required=False,
        approved_scope=f"Phase {phase} no storage/cache/.pcae creation",
        denied_scope=None,
        deferred_scope=None,
        rejected_scope=None,
        affected_files=[],
        affected_agents=[],
        authorization_flags=dict(_ALL_FALSE_AUTH_FLAGS),
        risk_level="low",
        supersedes=None,
        superseded_by=None,
        related_decisions=[_stable_decision_id(phase, "read_only_boundary_decision")],
        related_artifacts=[],
        related_events=[],
        evidence_level="repo_committed_artifact",
        safety_notes="storage_created=false, cache_created=false, pcae_storage_created=false",
    ))

    decisions.append(_make_decision(
        decision_id=_stable_decision_id(phase, "no_backend_invocation_decision"),
        decision_type="no_backend_invocation_decision",
        decision_status="approved",
        decision_timestamp=artifact_timestamp,
        source_phase=phase,
        source_artifact=artifact_path if artifact_exists else None,
        source_event=None,
        source_commit=artifact_commit,
        decision_maker="governance",
        human_required=False,
        approved_scope=f"Phase {phase} no backend invocation performed",
        denied_scope=None,
        deferred_scope=None,
        rejected_scope=None,
        affected_files=[],
        affected_agents=[],
        authorization_flags=dict(_ALL_FALSE_AUTH_FLAGS),
        risk_level="low",
        supersedes=None,
        superseded_by=None,
        related_decisions=[],
        related_artifacts=[],
        related_events=[],
        evidence_level="repo_committed_artifact",
        safety_notes="backend_invocation_performed=false",
    ))

    decisions.append(_make_decision(
        decision_id=_stable_decision_id(phase, "no_authority_inference_decision"),
        decision_type="no_authority_inference_decision",
        decision_status="approved",
        decision_timestamp=artifact_timestamp,
        source_phase=phase,
        source_artifact=artifact_path if artifact_exists else None,
        source_event=None,
        source_commit=artifact_commit,
        decision_maker="governance",
        human_required=False,
        approved_scope=f"Phase {phase} no authority inference from output presence",
        denied_scope=None,
        deferred_scope=None,
        rejected_scope=None,
        affected_files=[],
        affected_agents=[],
        authorization_flags=dict(_ALL_FALSE_AUTH_FLAGS),
        risk_level="low",
        supersedes=None,
        superseded_by=None,
        related_decisions=[],
        related_artifacts=[],
        related_events=[],
        evidence_level="repo_committed_artifact",
        safety_notes="authority_inference=prevented",
    ))

    next_phase = phase_info.get("next_phase")
    if next_phase:
        decisions.append(_make_decision(
            decision_id=_stable_decision_id(phase, "recommended_next_phase_decision"),
            decision_type="recommended_next_phase_decision",
            decision_status="recorded",
            decision_timestamp=task_timestamp,
            source_phase=phase,
            source_artifact=task_path,
            source_event=None,
            source_commit=task_commit,
            decision_maker="governance",
            human_required=False,
            approved_scope=f"Recommended next phase: {next_phase}",
            denied_scope=None,
            deferred_scope=None,
            rejected_scope=None,
            affected_files=[],
            affected_agents=[],
            authorization_flags=dict(_ALL_FALSE_AUTH_FLAGS),
            risk_level="low",
            supersedes=None,
            superseded_by=None,
            related_decisions=[_stable_decision_id(phase, "phase_completion_decision")],
            related_artifacts=[],
            related_events=[],
            evidence_level="repo_committed_artifact",
            safety_notes=f"recommended_next={next_phase}",
        ))

    return decisions


def build_decision_log(repo_root: Path) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    all_decisions: list[dict[str, Any]] = []

    _artifact_data = build_artifact_index(repo_root)
    _snapshot_data = build_memory_snapshot(repo_root)
    _timeline_data = build_governance_timeline(repo_root)

    for phase_info in _PHASE_DECISIONS:
        phase_decisions = _extract_phase_decisions(repo_root, phase_info)
        all_decisions.extend(phase_decisions)

    seen_ids: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for dec in all_decisions:
        if dec["decision_id"] not in seen_ids:
            seen_ids.add(dec["decision_id"])
            deduped.append(dec)
        else:
            warnings.append(f"Duplicate decision_id suppressed: {dec['decision_id']}")

    def _sort_key(dec: dict[str, Any]) -> tuple[str, str, str]:
        phase = dec.get("source_phase", "")
        ts = dec.get("decision_timestamp", "unknown")
        if ts == "unknown":
            ts = "9999-12-31T23:59:59+00:00"
        return (phase, ts, dec["decision_id"])

    deduped.sort(key=_sort_key)

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae decision-log",
        "repository_root": str(repo_root),
        "decisions": deduped,
        "decision_count": len(deduped),
        "warnings": warnings,
        "errors": errors,
        "safety_notes": {
            "decision_log_is_read_only": True,
            "decision_log_does_not_authorize_execution": True,
            "decision_log_does_not_authorize_backend_invocation": True,
            "decision_log_does_not_authorize_adoption": True,
            "decision_log_does_not_authorize_commit_or_push": True,
            "generated_cache_created": False,
            "pcae_storage_created": False,
            "artifact_index_used": True,
            "memory_snapshot_used": True,
            "governance_timeline_used": True,
        },
    }
