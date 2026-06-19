from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from pcae.core.git_status import GitChange, read_git_branch, read_git_changes
from pcae.core.paths import HarnessPath
from pcae.core.tasks import find_latest_active_task


SESSION_RELATIVE_PATH = Path(".pcae") / "session.json"


@dataclass(frozen=True)
class SessionSnapshot:
    relative_path: Path
    data: dict


@dataclass(frozen=True)
class SessionUpdate:
    objective: str | None = None
    completed_step: str | None = None
    next_step: str | None = None
    blocker: str | None = None
    warning: str | None = None
    note: str | None = None


def read_session_snapshot(root: HarnessPath) -> SessionSnapshot | None:
    target = root.join(SESSION_RELATIVE_PATH)
    if not target.is_file():
        return None

    return SessionSnapshot(
        relative_path=SESSION_RELATIVE_PATH,
        data=json.loads(target.read_text(encoding="utf-8")),
    )


def write_session_snapshot(
    root: HarnessPath,
    created_at: datetime | None = None,
) -> SessionSnapshot:
    timestamp = created_at or datetime.now(timezone.utc)
    data = build_session_snapshot(root, timestamp)
    return write_session_data(root, data)


def update_session_snapshot(
    root: HarnessPath,
    update: SessionUpdate,
) -> SessionSnapshot:
    snapshot = read_session_snapshot(root)
    if snapshot is None:
        snapshot = write_session_snapshot(root)

    data = dict(snapshot.data)
    if update.objective is not None:
        data["current_objective"] = update.objective
    if update.completed_step is not None:
        data["last_completed_step"] = update.completed_step
    if update.next_step is not None:
        data["next_recommended_step"] = update.next_step
    append_session_value(data, "blockers", update.blocker)
    append_session_value(data, "warnings", update.warning)
    append_session_value(data, "architectural_notes", update.note)

    return write_session_data(root, data)


def write_session_data(root: HarnessPath, data: dict) -> SessionSnapshot:
    target = root.join(SESSION_RELATIVE_PATH)

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")

    return SessionSnapshot(relative_path=SESSION_RELATIVE_PATH, data=data)


def append_session_value(data: dict, key: str, value: str | None) -> None:
    if value is None:
        return

    existing = data.get(key)
    if not isinstance(existing, list):
        existing = []
    existing.append(value)
    data[key] = existing


def build_session_snapshot(root: HarnessPath, timestamp: datetime) -> dict:
    active_task = find_latest_active_task(root)
    changes = read_git_changes(root)

    return {
        "active_task": None
        if active_task is None
        else {
            "id": active_task.task_id,
            "title": active_task.title,
        },
        "architectural_notes": [],
        "blockers": [],
        "current_objective": "",
        "git": {
            "branch": read_git_branch(root),
            "changed_files": [
                {
                    "path": change.path.as_posix(),
                    "status": change.status,
                }
                for change in changes
            ],
            "status_summary": summarize_git_changes(changes),
        },
        "last_completed_step": "",
        "next_recommended_step": "",
        "timestamp": timestamp.isoformat(),
        "warnings": [],
    }


def summarize_git_changes(changes: tuple[GitChange, ...]) -> str:
    if not changes:
        return "clean"
    if len(changes) == 1:
        return "1 changed file"
    return f"{len(changes)} changed files"


@dataclass(frozen=True)
class ContinuityReport:
    branch: str
    working_tree: str
    health_status: str
    check_passed: bool
    task_state: str
    active_task_id: str | None
    active_task_title: str | None
    handoff_present: bool
    handoff_summary: str | None
    handoff_created_at: str | None
    audit_present: bool
    audit_phases_detected: int | None
    audit_warning_count: int | None
    audit_created_at: str | None
    audit_healthy_idle: bool | None
    phase_queue_present: bool
    phase_queue_count: int
    prompt_present: bool
    prompt_title: str | None
    prompt_created_at: str | None
    prompt_path: str | None
    push_mode: str
    task_memory_status: str
    suitable_for_continuation: bool
    issues: tuple[str, ...]


def build_continuity_report(
    root: HarnessPath,
    *,
    handoff_data: dict | None = None,
    audit_data: dict | None = None,
    queue: list[str] | None = None,
    prompt_data: dict | None = None,
) -> ContinuityReport:
    from pcae.core.git_status import read_git_branch, read_git_changes
    from pcae.core.health import build_health_data, is_healthy
    from pcae.core.check import run_checks
    from pcae.core.tasks import diagnose_task_memory

    branch = read_git_branch(root)
    changes = read_git_changes(root)
    working_tree = "clean" if not changes else f"{len(changes)} changed files"

    health_data = build_health_data(root)
    health_status: str = health_data["overall_status"]
    health_ok = is_healthy(health_data)

    check_result = run_checks(root)
    check_passed = check_result.passed

    active_task = find_latest_active_task(root)
    task_state = "active" if active_task else "idle"
    task_id = active_task.task_id if active_task else None
    task_title = active_task.title if active_task else None

    diagnostics = diagnose_task_memory(root)
    task_memory_status = "clean" if not diagnostics.has_errors else "inconsistent"

    handoff_present = handoff_data is not None
    handoff_summary = handoff_data.get("summary") if handoff_data else None
    handoff_created_at = handoff_data.get("created_at") if handoff_data else None

    audit_present = audit_data is not None
    audit_phases = audit_data.get("phases_detected") if audit_data else None
    audit_warnings = len(audit_data.get("warnings", [])) if audit_data else None
    audit_created_at = audit_data.get("created_at") if audit_data else None
    audit_healthy_idle = audit_data.get("healthy_idle") if audit_data else None

    queue = queue or []
    phase_queue_present = len(queue) > 0
    phase_queue_count = len(queue)

    prompt_present = prompt_data is not None
    prompt_title = prompt_data.get("title") if prompt_data else None
    prompt_created_at = prompt_data.get("created_at") if prompt_data else None
    prompt_path = prompt_data.get("latest_path") if prompt_data else None

    push_mode = "nothing_to_push"
    if changes:
        push_mode = "dirty_tree"

    issues: list[str] = []
    if not health_ok:
        issues.append(f"Health is not healthy: {health_status}")
    if not check_passed:
        issues.append("Check did not pass")
    if not handoff_present:
        issues.append("No handoff artifact found")
    if not audit_present:
        issues.append("No audit artifact found")
    if changes:
        issues.append("Working tree is not clean")
    if task_memory_status != "clean":
        issues.append("Task memory has inconsistencies")

    suitable = health_ok and check_passed and not changes

    return ContinuityReport(
        branch=branch,
        working_tree=working_tree,
        health_status=health_status,
        check_passed=check_passed,
        task_state=task_state,
        active_task_id=task_id,
        active_task_title=task_title,
        handoff_present=handoff_present,
        handoff_summary=handoff_summary,
        handoff_created_at=handoff_created_at,
        audit_present=audit_present,
        audit_phases_detected=audit_phases,
        audit_warning_count=audit_warnings,
        audit_created_at=audit_created_at,
        audit_healthy_idle=audit_healthy_idle,
        phase_queue_present=phase_queue_present,
        phase_queue_count=phase_queue_count,
        prompt_present=prompt_present,
        prompt_title=prompt_title,
        prompt_created_at=prompt_created_at,
        prompt_path=prompt_path,
        push_mode=push_mode,
        task_memory_status=task_memory_status,
        suitable_for_continuation=suitable,
        issues=tuple(issues),
    )


def session_continuity_status(check_result) -> str:
    if any("Session continuity verified." in info.text for info in check_result.infos):
        return "verified"
    if any("Session snapshot missing" in v.text for v in check_result.violations):
        return "missing"
    if any("Session snapshot missing" in w.text for w in check_result.warnings):
        return "missing"
    if any(
        "Session active task does not match current active task" in v.text
        for v in check_result.violations
    ):
        return "mismatch"
    if any("Invalid session JSON" in v.text for v in check_result.violations):
        return "invalid"
    return "unknown"
