from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.artifact_index import build_artifact_index


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


def _detect_active_task(repo_root: Path) -> str | None:
    active_dir = repo_root / "tasks" / "active"
    if not active_dir.is_dir():
        return None
    for f in sorted(active_dir.iterdir()):
        if f.suffix == ".md" and not f.name.startswith("."):
            return f.stem
    return None


def _detect_latest_completed_phase(repo_root: Path) -> str | None:
    completed_dir = repo_root / "tasks" / "completed"
    if not completed_dir.is_dir():
        return None
    phases = []
    for f in sorted(completed_dir.iterdir()):
        if f.suffix == ".md" and not f.name.startswith("."):
            phases.append(f.stem)
    return phases[-1] if phases else None


def _read_first_line_match(repo_root: Path, filename: str, prefix: str) -> str | None:
    path = repo_root / filename
    if not path.is_file():
        return None
    try:
        with open(path) as fh:
            for line in fh:
                stripped = line.strip()
                if stripped.startswith(prefix):
                    return stripped[len(prefix):].strip()
    except OSError:
        pass
    return None


def build_memory_snapshot(repo_root: Path, ctx=None) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    artifact_data = ctx.artifact_index if ctx is not None else build_artifact_index(repo_root)
    present_count = artifact_data.get("present_count", 0)
    missing_count = artifact_data.get("missing_count", 0)

    if present_count > 0 and missing_count == 0:
        artifact_index_status = "available"
    elif present_count > 0:
        artifact_index_status = "partial"
        warnings.append(f"Artifact index: {missing_count} artifacts missing")
    else:
        artifact_index_status = "unavailable"
        warnings.append("Artifact index: no artifacts found")

    head_commit = _git_head_commit(repo_root)
    branch = _git_branch(repo_root)
    origin_count = _git_origin_count(repo_root)

    if origin_count is not None and origin_count == 0:
        origin_sync = "synced"
    elif origin_count is not None:
        origin_sync = f"ahead_by_{origin_count}"
    else:
        origin_sync = "unknown"

    active_task = _detect_active_task(repo_root)
    latest_completed = _detect_latest_completed_phase(repo_root)

    current_phase_label: str | None = None
    if active_task:
        current_phase_label = active_task
    else:
        current_phase_label = None

    phase_status_line = _read_first_line_match(repo_root, "PROJECT_STATUS.md", "Phase ")
    roadmap_position = phase_status_line if phase_status_line else "unknown"

    provenance_artifacts = [
        r["artifact_path"]
        for r in artifact_data.get("records", [])
        if r["artifact_status"] == "current"
    ]

    snapshot: dict[str, Any] = {
        "memory_snapshot_id": f"snapshot-{uuid.uuid4().hex[:12]}",
        "memory_model_version": "0.1",
        "project_id": "pcae-harness",
        "repository_path": str(repo_root),
        "current_phase": current_phase_label,
        "latest_completed_phase": latest_completed,
        "current_lifecycle_state": "closed",
        "roadmap_position": roadmap_position,
        "phase_sequence_position": "86D" if active_task and "86d" in (active_task or "").lower() else "unknown",
        "last_verified_commit": head_commit,
        "origin_sync_status": origin_sync,
        "health_status": "unknown",
        "governance_status": "restrictive",
        "artifact_index_status": artifact_index_status,
        "timeline_status": "design_documented",
        "decision_log_status": "design_documented",
        "risk_status": "design_documented",
        "next_safe_actions": [
            "Complete 86D memory snapshot prototype",
            "Proceed to 86E governance event timeline extraction",
        ],
        "forbidden_actions": [
            "Backend invocation without guard approval",
            "Prompt sending without lifecycle authorization",
            "Adoption without intake/review/approval",
            "Source/test mutation outside active task scope",
            "Commit/push without governed pcae push",
            "Force push",
            "Raw git push",
        ],
        "provenance": {
            "source_artifacts": provenance_artifacts,
            "head_commit": head_commit,
            "branch": branch,
            "origin_ahead_count": origin_count,
        },
        "safety_notes": None,
    }

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae memory-snapshot",
        "repository_root": str(repo_root),
        "snapshot": snapshot,
        "warnings": warnings,
        "errors": errors,
        "safety_notes": {
            "memory_snapshot_is_read_only": True,
            "memory_snapshot_does_not_authorize_execution": True,
            "memory_snapshot_does_not_authorize_backend_invocation": True,
            "memory_snapshot_does_not_authorize_adoption": True,
            "memory_snapshot_does_not_authorize_commit_or_push": True,
            "generated_cache_created": False,
            "pcae_storage_created": False,
            "artifact_index_used": True,
        },
    }
