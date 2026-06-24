from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_ARTIFACT_CATALOG: list[dict[str, Any]] = [
    {
        "artifact_id": "roadmap-reconciliation-phase-85-plan",
        "artifact_type": "roadmap_artifact",
        "artifact_path": "docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md",
        "artifact_title": "Roadmap Reconciliation and Phase 85 Plan",
        "source_phase": "84L",
        "created_phase": "84L",
        "artifact_version": "0.1",
        "implementation_status": "not_started",
        "authoritative_for": ["phase_85_plan", "roadmap_reconciliation"],
    },
    {
        "artifact_id": "persistent-lifecycle-memory-model",
        "artifact_type": "memory_model_artifact",
        "artifact_path": "docs/PERSISTENT_LIFECYCLE_MEMORY_MODEL.md",
        "artifact_title": "Persistent Lifecycle Memory Model",
        "source_phase": "85A",
        "created_phase": "85A",
        "artifact_version": "0.1",
        "implementation_status": "not_started",
        "authoritative_for": ["memory_model_design"],
    },
    {
        "artifact_id": "artifact-index-design",
        "artifact_type": "artifact_index_design_artifact",
        "artifact_path": "docs/ARTIFACT_INDEX_DESIGN.md",
        "artifact_title": "Artifact Index Design",
        "source_phase": "85B",
        "created_phase": "85B",
        "artifact_version": "0.1",
        "implementation_status": "not_started",
        "authoritative_for": ["artifact_index_design"],
    },
    {
        "artifact_id": "governance-event-timeline-design",
        "artifact_type": "timeline_design_artifact",
        "artifact_path": "docs/GOVERNANCE_EVENT_TIMELINE_DESIGN.md",
        "artifact_title": "Governance Event Timeline Design",
        "source_phase": "85C",
        "created_phase": "85C",
        "artifact_version": "0.1",
        "implementation_status": "not_started",
        "authoritative_for": ["timeline_design"],
    },
    {
        "artifact_id": "decision-log-integration-design",
        "artifact_type": "decision_log_design_artifact",
        "artifact_path": "docs/DECISION_LOG_INTEGRATION_DESIGN.md",
        "artifact_title": "Decision Log Integration Design",
        "source_phase": "85D",
        "created_phase": "85D",
        "artifact_version": "0.1",
        "implementation_status": "not_started",
        "authoritative_for": ["decision_log_design"],
    },
    {
        "artifact_id": "risk-register-design",
        "artifact_type": "risk_register_design_artifact",
        "artifact_path": "docs/RISK_REGISTER_DESIGN.md",
        "artifact_title": "Risk Register Design",
        "source_phase": "85E",
        "created_phase": "85E",
        "artifact_version": "0.1",
        "implementation_status": "not_started",
        "authoritative_for": ["risk_register_design"],
    },
    {
        "artifact_id": "project-state-snapshot-design",
        "artifact_type": "project_state_snapshot_design_artifact",
        "artifact_path": "docs/PROJECT_STATE_SNAPSHOT_DESIGN.md",
        "artifact_title": "Project State Snapshot Design",
        "source_phase": "85F",
        "created_phase": "85F",
        "artifact_version": "0.1",
        "implementation_status": "not_started",
        "authoritative_for": ["project_state_snapshot_design"],
    },
    {
        "artifact_id": "phase-85-implementation-roadmap",
        "artifact_type": "implementation_roadmap_artifact",
        "artifact_path": "docs/PHASE_85_IMPLEMENTATION_ROADMAP.md",
        "artifact_title": "Phase 85 Implementation Roadmap",
        "source_phase": "86A",
        "created_phase": "86A",
        "artifact_version": "0.1",
        "implementation_status": "not_started",
        "authoritative_for": ["implementation_roadmap"],
    },
    {
        "artifact_id": "phase-85-data-model-storage-design",
        "artifact_type": "data_model_storage_design_artifact",
        "artifact_path": "docs/PHASE_85_DATA_MODEL_STORAGE_DESIGN.md",
        "artifact_title": "Phase 85 Data Model and Storage Design",
        "source_phase": "86B",
        "created_phase": "86B",
        "artifact_version": "0.1",
        "implementation_status": "not_started",
        "authoritative_for": ["data_model_storage_design"],
    },
    {
        "artifact_id": "multi-agent-governance-summary",
        "artifact_type": "governance_summary_artifact",
        "artifact_path": "docs/MULTI_AGENT_GOVERNANCE_SUMMARY.md",
        "artifact_title": "Multi-Agent Governance Summary",
        "source_phase": "84K",
        "created_phase": "84K",
        "artifact_version": None,
        "implementation_status": None,
        "authoritative_for": ["governance_summary"],
    },
    {
        "artifact_id": "full-health-baseline-84k3",
        "artifact_type": "health_baseline_artifact",
        "artifact_path": "docs/FULL_HEALTH_BASELINE_84K3.md",
        "artifact_title": "Full Health Baseline After Refresh (84K.3)",
        "source_phase": "84K.3",
        "created_phase": "84K.3",
        "artifact_version": "0.1",
        "implementation_status": None,
        "authoritative_for": ["post_refresh_health_baseline"],
    },
    {
        "artifact_id": "project-status",
        "artifact_type": "status_artifact",
        "artifact_path": "PROJECT_STATUS.md",
        "artifact_title": "Project Status",
        "source_phase": "current",
        "created_phase": "initial",
        "artifact_version": None,
        "implementation_status": None,
        "authoritative_for": ["current_phase_status"],
    },
    {
        "artifact_id": "changelog",
        "artifact_type": "changelog_artifact",
        "artifact_path": "CHANGELOG.md",
        "artifact_title": "Changelog",
        "source_phase": "current",
        "created_phase": "initial",
        "artifact_version": None,
        "implementation_status": None,
        "authoritative_for": ["phase_history"],
    },
    {
        "artifact_id": "readme",
        "artifact_type": "readme_artifact",
        "artifact_path": "README.md",
        "artifact_title": "README",
        "source_phase": "84K",
        "created_phase": "initial",
        "artifact_version": None,
        "implementation_status": None,
        "authoritative_for": ["project_overview"],
    },
]


def _get_commit_ref(repo_root: Path, artifact_path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", artifact_path],
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def build_artifact_index(repo_root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    for entry in _ARTIFACT_CATALOG:
        full_path = repo_root / entry["artifact_path"]
        exists = full_path.is_file()

        if exists:
            status = "current"
            freshness = "fresh"
            evidence_level = "repo_committed_artifact"
        else:
            status = "missing"
            freshness = "unknown"
            evidence_level = "unknown"
            warnings.append(f"Artifact missing: {entry['artifact_path']}")

        commit_ref = _get_commit_ref(repo_root, entry["artifact_path"]) if exists else None

        record: dict[str, Any] = {
            "artifact_id": entry["artifact_id"],
            "artifact_type": entry["artifact_type"],
            "artifact_path": entry["artifact_path"],
            "artifact_title": entry["artifact_title"],
            "artifact_status": status,
            "artifact_version": entry.get("artifact_version"),
            "source_phase": entry["source_phase"],
            "created_phase": entry["created_phase"],
            "last_updated_phase": None,
            "implementation_status": entry.get("implementation_status"),
            "authoritative_for": entry.get("authoritative_for", []),
            "supersedes": None,
            "superseded_by": None,
            "related_artifacts": [],
            "evidence_level": evidence_level,
            "freshness_status": freshness,
            "hash_or_commit_ref": commit_ref,
            "required_for_memory_queries": [],
            "safety_notes": None,
        }
        records.append(record)

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae artifact-index",
        "repository_root": str(repo_root),
        "records": records,
        "record_count": len(records),
        "present_count": sum(1 for r in records if r["artifact_status"] == "current"),
        "missing_count": sum(1 for r in records if r["artifact_status"] == "missing"),
        "warnings": warnings,
        "errors": errors,
        "safety_notes": {
            "artifact_index_is_read_only": True,
            "artifact_index_does_not_authorize_execution": True,
            "artifact_index_does_not_authorize_adoption": True,
            "artifact_index_does_not_authorize_commit_or_push": True,
            "generated_cache_created": False,
            "pcae_storage_created": False,
        },
    }
