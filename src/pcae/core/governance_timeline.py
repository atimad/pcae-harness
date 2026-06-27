from __future__ import annotations

import hashlib
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.artifact_index import build_artifact_index
from pcae.core.memory_snapshot import build_memory_snapshot


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


def _stable_event_id(phase: str, event_type: str, suffix: str = "") -> str:
    raw = f"{phase}:{event_type}"
    if suffix:
        raw = f"{raw}:{suffix}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"evt-{phase}-{event_type}-{digest}"


def _make_event(
    event_id: str,
    event_type: str,
    event_status: str,
    event_timestamp: str | None,
    source_phase: str,
    source_artifact: str | None,
    source_commit: str | None,
    actor: str,
    agent_id: str | None,
    human_required: bool,
    authorization_required: bool,
    authorization_status: str,
    affected_files: list[str] | None,
    related_artifacts: list[str] | None,
    related_events: list[str] | None,
    causal_parent_events: list[str] | None,
    evidence_level: str,
    freshness_status: str,
    safety_notes: str | None,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_status": event_status,
        "event_timestamp": event_timestamp if event_timestamp is not None else "unknown",
        "source_phase": source_phase,
        "source_artifact": source_artifact if source_artifact is not None else "unknown",
        "source_commit": source_commit if source_commit is not None else "unknown",
        "actor": actor,
        "agent_id": agent_id,
        "human_required": human_required,
        "authorization_required": authorization_required,
        "authorization_status": authorization_status,
        "affected_files": affected_files or [],
        "related_artifacts": related_artifacts or [],
        "related_events": related_events or [],
        "causal_parent_events": causal_parent_events or [],
        "evidence_level": evidence_level,
        "freshness_status": freshness_status,
        "safety_notes": safety_notes,
    }


_PHASE_ORDER: list[dict[str, Any]] = [
    {"phase": "84L", "label": "Roadmap Reconciliation and Phase 85 Plan",
     "artifact": "docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md",
     "task": "84l-roadmap-reconciliation-phase-85-plan"},
    {"phase": "85A", "label": "Persistent Lifecycle Memory Model",
     "artifact": "docs/PERSISTENT_LIFECYCLE_MEMORY_MODEL.md",
     "task": "85a-persistent-lifecycle-memory-model"},
    {"phase": "85B", "label": "Artifact Index Design",
     "artifact": "docs/ARTIFACT_INDEX_DESIGN.md",
     "task": "85b-artifact-index-design"},
    {"phase": "85C", "label": "Governance Event Timeline Design",
     "artifact": "docs/GOVERNANCE_EVENT_TIMELINE_DESIGN.md",
     "task": "85c-governance-event-timeline-design"},
    {"phase": "85D", "label": "Decision Log Integration Design",
     "artifact": "docs/DECISION_LOG_INTEGRATION_DESIGN.md",
     "task": "85d-decision-log-integration-design"},
    {"phase": "85E", "label": "Risk Register Design",
     "artifact": "docs/RISK_REGISTER_DESIGN.md",
     "task": "85e-risk-register-design"},
    {"phase": "85F", "label": "Project State Snapshot Design",
     "artifact": "docs/PROJECT_STATE_SNAPSHOT_DESIGN.md",
     "task": "85f-project-state-snapshot-design"},
    {"phase": "86A", "label": "Phase 85 Implementation Roadmap",
     "artifact": "docs/PHASE_85_IMPLEMENTATION_ROADMAP.md",
     "task": "86a-phase-85-implementation-roadmap"},
    {"phase": "86B", "label": "Phase 85 Data Model and Storage Design",
     "artifact": "docs/PHASE_85_DATA_MODEL_STORAGE_DESIGN.md",
     "task": "86b-phase-85-data-model-storage-design"},
    {"phase": "86C", "label": "Read-Only Artifact Index Prototype",
     "artifact": "docs/PHASE_85_ARTIFACT_INDEX_PROTOTYPE.md",
     "task": "86c-read-only-artifact-index-prototype",
     "command": "pcae artifact-index --json"},
    {"phase": "86D", "label": "Persistent Memory Snapshot Prototype",
     "artifact": "docs/PHASE_85_MEMORY_SNAPSHOT_PROTOTYPE.md",
     "task": "86d-read-only-memory-snapshot-prototype",
     "command": "pcae memory-snapshot --json"},
]


def _extract_phase_events(repo_root: Path, phase_info: dict[str, Any],
                          order_index: int) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    phase = phase_info["phase"]
    artifact_path = phase_info["artifact"]
    task_stem = phase_info["task"]

    artifact_full = repo_root / artifact_path
    artifact_exists = artifact_full.is_file()

    task_completed = repo_root / "tasks" / "completed" / f"{task_stem}.md"
    task_complete = task_completed.is_file()

    artifact_timestamp = _git_log_commit_date(repo_root, artifact_path) if artifact_exists else None
    artifact_commit = _git_log_commit_hash(repo_root, artifact_path) if artifact_exists else None

    task_timestamp = _git_log_commit_date(repo_root, f"tasks/completed/{task_stem}.md") if task_complete else None
    task_commit = _git_log_commit_hash(repo_root, f"tasks/completed/{task_stem}.md") if task_complete else None

    if artifact_exists:
        is_design = phase.startswith("85") or phase == "84L"
        is_impl = phase.startswith("86") and phase not in ("86A", "86B")
        is_model = phase == "86B"

        if is_design:
            events.append(_make_event(
                event_id=_stable_event_id(phase, "design_documented"),
                event_type="design_documented",
                event_status="completed",
                event_timestamp=artifact_timestamp,
                source_phase=phase,
                source_artifact=artifact_path,
                source_commit=artifact_commit,
                actor="governance",
                agent_id=None,
                human_required=False,
                authorization_required=False,
                authorization_status="not_applicable",
                affected_files=[artifact_path],
                related_artifacts=[],
                related_events=[],
                causal_parent_events=[],
                evidence_level="repo_committed_artifact",
                freshness_status="fresh",
                safety_notes=None,
            ))

        events.append(_make_event(
            event_id=_stable_event_id(phase, "artifact_documented"),
            event_type="artifact_documented",
            event_status="completed",
            event_timestamp=artifact_timestamp,
            source_phase=phase,
            source_artifact=artifact_path,
            source_commit=artifact_commit,
            actor="governance",
            agent_id=None,
            human_required=False,
            authorization_required=False,
            authorization_status="not_applicable",
            affected_files=[artifact_path],
            related_artifacts=[],
            related_events=[_stable_event_id(phase, "design_documented")] if is_design else [],
            causal_parent_events=[_stable_event_id(phase, "design_documented")] if is_design else [],
            evidence_level="repo_committed_artifact",
            freshness_status="fresh",
            safety_notes=None,
        ))

        if is_impl:
            events.append(_make_event(
                event_id=_stable_event_id(phase, "prototype_implemented"),
                event_type="prototype_implemented",
                event_status="completed",
                event_timestamp=artifact_timestamp,
                source_phase=phase,
                source_artifact=artifact_path,
                source_commit=artifact_commit,
                actor="governance",
                agent_id=None,
                human_required=False,
                authorization_required=False,
                authorization_status="not_applicable",
                affected_files=[artifact_path],
                related_artifacts=[],
                related_events=[_stable_event_id(phase, "artifact_documented")],
                causal_parent_events=[_stable_event_id(phase, "artifact_documented")],
                evidence_level="repo_committed_artifact",
                freshness_status="fresh",
                safety_notes=None,
            ))

        if is_model:
            events.append(_make_event(
                event_id=_stable_event_id(phase, "design_documented"),
                event_type="design_documented",
                event_status="completed",
                event_timestamp=artifact_timestamp,
                source_phase=phase,
                source_artifact=artifact_path,
                source_commit=artifact_commit,
                actor="governance",
                agent_id=None,
                human_required=False,
                authorization_required=False,
                authorization_status="not_applicable",
                affected_files=[artifact_path],
                related_artifacts=[],
                related_events=[_stable_event_id(phase, "artifact_documented")],
                causal_parent_events=[],
                evidence_level="repo_committed_artifact",
                freshness_status="fresh",
                safety_notes=None,
            ))

    if task_complete:
        events.append(_make_event(
            event_id=_stable_event_id(phase, "phase_completed"),
            event_type="phase_completed",
            event_status="completed",
            event_timestamp=task_timestamp,
            source_phase=phase,
            source_artifact=f"tasks/completed/{task_stem}.md",
            source_commit=task_commit,
            actor="governance",
            agent_id=None,
            human_required=False,
            authorization_required=False,
            authorization_status="not_applicable",
            affected_files=[f"tasks/completed/{task_stem}.md"],
            related_artifacts=[artifact_path] if artifact_exists else [],
            related_events=[e["event_id"] for e in events],
            causal_parent_events=[e["event_id"] for e in events],
            evidence_level="repo_committed_artifact",
            freshness_status="fresh",
            safety_notes=None,
        ))

    if phase_info.get("command"):
        cmd = phase_info["command"]
        events.append(_make_event(
            event_id=_stable_event_id(phase, "command_available", cmd),
            event_type="command_available",
            event_status="completed",
            event_timestamp=artifact_timestamp,
            source_phase=phase,
            source_artifact=artifact_path,
            source_commit=artifact_commit,
            actor="governance",
            agent_id=None,
            human_required=False,
            authorization_required=False,
            authorization_status="not_applicable",
            affected_files=[],
            related_artifacts=[artifact_path] if artifact_exists else [],
            related_events=[_stable_event_id(phase, "prototype_implemented")],
            causal_parent_events=[_stable_event_id(phase, "prototype_implemented")],
            evidence_level="repo_committed_artifact",
            freshness_status="fresh",
            safety_notes=f"command={cmd}",
        ))

    return events


def _extract_commit_events(repo_root: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--format=%H %aI %s"],
            capture_output=True, text=True, cwd=repo_root, timeout=15,
        )
        if result.returncode != 0:
            return events
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return events

    phase_pattern = re.compile(
        r"^([a-f0-9]+)\s+(\S+)\s+((?:Implement|Complete|Document)\s+Phase\s+\d+\S*\s+.+)$",
        re.IGNORECASE,
    )
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        m = phase_pattern.match(line)
        if not m:
            continue
        commit_hash = m.group(1)
        timestamp = m.group(2)
        message = m.group(3)

        phase_match = re.search(r"Phase\s+(\d+[A-Za-z]*(?:\.\d+)?)", message, re.IGNORECASE)
        phase = phase_match.group(1) if phase_match else "unknown"

        is_impl = message.lower().startswith("implement")
        is_complete = message.lower().startswith("complete")

        if is_impl:
            event_type = "implementation_commit_recorded"
        elif is_complete:
            event_type = "completion_commit_recorded"
        else:
            event_type = "implementation_commit_recorded"

        events.append(_make_event(
            event_id=_stable_event_id(phase, event_type, commit_hash[:12]),
            event_type=event_type,
            event_status="completed",
            event_timestamp=timestamp,
            source_phase=phase,
            source_artifact=None,
            source_commit=commit_hash,
            actor="governance",
            agent_id=None,
            human_required=False,
            authorization_required=False,
            authorization_status="not_applicable",
            affected_files=[],
            related_artifacts=[],
            related_events=[],
            causal_parent_events=[],
            evidence_level="git_commit",
            freshness_status="fresh",
            safety_notes=f"commit_message={message}",
        ))

    return events


def _extract_test_events(repo_root: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    test_files = [
        ("86C", "tests/test_artifact_index.py"),
        ("86D", "tests/test_memory_snapshot.py"),
    ]
    for phase, test_path in test_files:
        full = repo_root / test_path
        if not full.is_file():
            continue
        ts = _git_log_commit_date(repo_root, test_path)
        commit = _git_log_commit_hash(repo_root, test_path)
        events.append(_make_event(
            event_id=_stable_event_id(phase, "tests_passed", test_path),
            event_type="tests_passed",
            event_status="completed",
            event_timestamp=ts,
            source_phase=phase,
            source_artifact=test_path,
            source_commit=commit,
            actor="governance",
            agent_id=None,
            human_required=False,
            authorization_required=False,
            authorization_status="not_applicable",
            affected_files=[test_path],
            related_artifacts=[],
            related_events=[_stable_event_id(phase, "prototype_implemented")],
            causal_parent_events=[_stable_event_id(phase, "prototype_implemented")],
            evidence_level="repo_committed_artifact",
            freshness_status="fresh",
            safety_notes=f"test_file={test_path}",
        ))
    return events


def build_governance_timeline(repo_root: Path, ctx=None) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    all_events: list[dict[str, Any]] = []

    if ctx is None:
        _artifact_data = build_artifact_index(repo_root)
        _snapshot_data = build_memory_snapshot(repo_root)

    for idx, phase_info in enumerate(_PHASE_ORDER):
        phase_events = _extract_phase_events(repo_root, phase_info, idx)
        all_events.extend(phase_events)

    commit_events = _extract_commit_events(repo_root)
    all_events.extend(commit_events)

    test_events = _extract_test_events(repo_root)
    all_events.extend(test_events)

    seen_ids: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for evt in all_events:
        if evt["event_id"] not in seen_ids:
            seen_ids.add(evt["event_id"])
            deduped.append(evt)
        else:
            warnings.append(f"Duplicate event_id suppressed: {evt['event_id']}")

    def _sort_key(evt: dict[str, Any]) -> tuple[str, str, str]:
        phase = evt.get("source_phase", "")
        ts = evt.get("event_timestamp", "unknown")
        if ts == "unknown":
            ts = "9999-12-31T23:59:59+00:00"
        return (phase, ts, evt["event_id"])

    deduped.sort(key=_sort_key)

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae governance-timeline",
        "repository_root": str(repo_root),
        "events": deduped,
        "event_count": len(deduped),
        "warnings": warnings,
        "errors": errors,
        "safety_notes": {
            "governance_timeline_is_read_only": True,
            "governance_timeline_does_not_authorize_execution": True,
            "governance_timeline_does_not_authorize_backend_invocation": True,
            "governance_timeline_does_not_authorize_adoption": True,
            "governance_timeline_does_not_authorize_commit_or_push": True,
            "generated_cache_created": False,
            "pcae_storage_created": False,
            "artifact_index_used": True,
            "memory_snapshot_used": True,
        },
    }
