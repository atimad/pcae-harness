from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.artifact_index import build_artifact_index
from pcae.core.memory_snapshot import build_memory_snapshot
from pcae.core.governance_timeline import build_governance_timeline
from pcae.core.decision_log import build_decision_log
from pcae.core.risk_register import build_risk_register


def _git_status_clean(repo_root: Path) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip() == ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _git_branch(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _git_origin_count(repo_root: Path) -> int | None:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None


def _git_head_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def build_project_state(repo_root: Path, ctx=None) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    artifact_data = ctx.artifact_index if ctx is not None else build_artifact_index(repo_root)
    snapshot_data = ctx.memory_snapshot if ctx is not None else build_memory_snapshot(repo_root)
    timeline_data = ctx.governance_timeline if ctx is not None else build_governance_timeline(repo_root)
    decision_data = ctx.decision_log if ctx is not None else build_decision_log(repo_root)
    risk_data = ctx.risk_register if ctx is not None else build_risk_register(repo_root)

    mem = snapshot_data.get("snapshot", {})

    if ctx is not None:
        porcelain = ctx.git_porcelain
        repo_clean = (porcelain == "") if porcelain is not None else None
        branch = ctx.git_branch
        origin_count = ctx.git_ahead_count
        head_commit = mem.get("last_verified_commit")
    else:
        repo_clean = _git_status_clean(repo_root)
        branch = _git_branch(repo_root)
        origin_count = _git_origin_count(repo_root)
        head_commit = _git_head_commit(repo_root)

    if origin_count is not None and origin_count == 0:
        origin_sync = "synced"
    elif origin_count is not None:
        origin_sync = f"ahead_by_{origin_count}"
    else:
        origin_sync = "unknown"

    active_risks = [
        {"risk_id": r["risk_id"], "risk_type": r["risk_type"],
         "risk_title": r["risk_title"], "risk_severity": r["risk_severity"]}
        for r in risk_data.get("risks", [])
        if r["risk_status"] == "active"
    ]
    accepted_risks = [
        {"risk_id": r["risk_id"], "risk_type": r["risk_type"],
         "risk_title": r["risk_title"], "acceptance_rationale": r.get("acceptance_rationale")}
        for r in risk_data.get("risks", [])
        if r["risk_status"] == "accepted"
    ]
    stale_signals = [
        {"risk_id": r["risk_id"], "risk_type": r["risk_type"],
         "risk_title": r["risk_title"]}
        for r in risk_data.get("risks", [])
        if r["risk_status"] == "stale_signal"
    ]
    must_never_repeat = [
        {"risk_id": r["risk_id"], "risk_type": r["risk_type"],
         "risk_title": r["risk_title"]}
        for r in risk_data.get("risks", [])
        if r["risk_type"] in ("must_never_repeat_risk", "raw_push_exception_risk",
                               "hook_bypass_exception_risk")
    ]
    deferred_items = [
        {"risk_id": r["risk_id"], "risk_type": r["risk_type"],
         "risk_title": r["risk_title"]}
        for r in risk_data.get("risks", [])
        if r["risk_status"] == "deferred"
    ]

    evidence_artifacts = [
        r["artifact_path"]
        for r in artifact_data.get("records", [])
        if r["artifact_status"] == "current"
    ]

    snapshot_id_raw = f"project-state:{head_commit or 'unknown'}:{branch or 'unknown'}"
    snapshot_id = f"pstate-{hashlib.sha256(snapshot_id_raw.encode()).hexdigest()[:16]}"

    snapshot: dict[str, Any] = {
        "snapshot_id": snapshot_id,
        "snapshot_version": "0.1",
        "snapshot_status": "current",
        "snapshot_created_at": datetime.now(timezone.utc).isoformat(),
        "source_phase": "86H",
        "latest_completed_phase": mem.get("latest_completed_phase", "unknown"),
        "current_active_phase": mem.get("current_phase"),
        "current_lifecycle_state": mem.get("current_lifecycle_state", "unknown"),
        "roadmap_position": mem.get("roadmap_position", "unknown"),
        "recommended_next_phase": "86I",
        "repository_clean": repo_clean,
        "branch": branch,
        "origin_sync_status": origin_sync,
        "origin_main_head_count": origin_count,
        "health_status": "unknown",
        "check_status": "unknown",
        "doctor_status": "unknown",
        "push_check_status": "unknown",
        "execution_authorized": False,
        "backend_invocation_authorized": False,
        "prompt_sending_authorized": False,
        "capture_authorized": False,
        "intake_authorized": False,
        "adoption_authorized": False,
        "source_mutation_authorized": False,
        "test_mutation_authorized": False,
        "readme_mutation_authorized": False,
        "docs_real_captured_tasks_mutation_authorized": False,
        "active_blockers": [],
        "active_deferred_items": deferred_items,
        "active_rejected_items": [],
        "active_risks": active_risks,
        "accepted_risks": accepted_risks,
        "must_never_repeat_controls": must_never_repeat,
        "stale_signals": stale_signals,
        "evidence_artifacts": evidence_artifacts,
        "evidence_commits": [head_commit] if head_commit else [],
        "next_safe_actions": [
            "Proceed to 86I — Phase 85 Integration Tests (recommendation only, not authorization)",
        ],
        "forbidden_actions": [
            "Backend invocation without guard approval",
            "Prompt sending without lifecycle authorization",
            "Adoption without intake/review/approval",
            "Commit/push without governed pcae push",
            "Force push",
            "Raw git push",
            "Storage/cache/.pcae creation without explicit storage gate",
            "Source/test mutation outside active task scope",
            "README mutation without explicit authorization",
        ],
        "human_review_required": False,
        "confidence": "high",
        "safety_notes": "project_state_is_read_only=true, next_safe_actions_are_recommendations_not_authorizations=true",
    }

    layer_summary = {
        "artifact_index": {
            "record_count": artifact_data.get("record_count", 0),
            "present_count": artifact_data.get("present_count", 0),
            "missing_count": artifact_data.get("missing_count", 0),
        },
        "governance_timeline": {
            "event_count": timeline_data.get("event_count", 0),
        },
        "decision_log": {
            "decision_count": decision_data.get("decision_count", 0),
        },
        "risk_register": {
            "risk_count": risk_data.get("risk_count", 0),
            "active_count": len(active_risks),
            "accepted_count": len(accepted_risks),
            "stale_signal_count": len(stale_signals),
        },
    }

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae project-state",
        "repository_root": str(repo_root),
        "snapshot": snapshot,
        "layer_summary": layer_summary,
        "warnings": warnings,
        "errors": errors,
        "safety_notes": {
            "project_state_is_read_only": True,
            "project_state_does_not_authorize_execution": True,
            "project_state_does_not_authorize_backend_invocation": True,
            "project_state_does_not_authorize_adoption": True,
            "project_state_does_not_authorize_commit_or_push": True,
            "next_safe_actions_are_recommendations_not_authorizations": True,
            "generated_cache_created": False,
            "pcae_storage_created": False,
            "artifact_index_used": True,
            "memory_snapshot_used": True,
            "governance_timeline_used": True,
            "decision_log_used": True,
            "risk_register_used": True,
        },
    }
