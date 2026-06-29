from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pcae.core.agent import (
    acquire_agent_lock_idempotent,
    build_challenge_attention_assessment,
    build_irg_challenge_context,
    read_agent_lock,
    render_irg_challenge_compact_lines_with_allocation,
)

_LOCKABLE_BACKENDS = frozenset({
    "claude-local", "claude-deepseek", "claude-kimi",
    "codex", "manual", "noop",
})


def _sync_backend_lock(root: HarnessPath, agent_id: str) -> dict:
    """Synchronize the backend lock artifact (.pcae/agent-locks/latest.json)."""
    from datetime import datetime, timezone
    import shutil as _shutil

    _BACKEND_INFO = {
        "claude-local": {"backend_type": "claude", "command": "claude", "available": False, "invocation_allowed": False},
        "claude-deepseek": {"backend_type": "claude", "command": "claude-deepseek", "available": False, "invocation_allowed": False},
        "claude-kimi": {"backend_type": "claude", "command": "claude-kimi", "available": False, "invocation_allowed": False},
        "codex": {"backend_type": "codex", "command": "codex", "available": False, "invocation_allowed": False},
        "manual": {"backend_type": "manual", "command": "none", "available": True, "invocation_allowed": False},
        "noop": {"backend_type": "noop", "command": "echo", "available": True, "invocation_allowed": False},
    }

    if agent_id not in _LOCKABLE_BACKENDS:
        return {"lock_synced": False, "lock_backend_name": None, "lock_conflict": False, "blocker": f"'{agent_id}' is not a recognized lockable backend identity", "execution_authorized": False}

    existing_lock = read_agent_lock(root)
    if existing_lock is not None and existing_lock.agent_id != agent_id:
        return {"lock_synced": False, "lock_backend_name": existing_lock.agent_id, "lock_conflict": True, "blocker": f"Core lock held by '{existing_lock.agent_id}', requested '{agent_id}'", "execution_authorized": False}

    info = _BACKEND_INFO.get(agent_id,
        {"backend_type": "claude", "command": agent_id, "available": False, "invocation_allowed": False})
    available = _shutil.which(info["command"]) is not None if info["command"] not in ("none", "echo") else info["available"]
    ts = datetime.now(timezone.utc)
    lock_data = {
        "lock_status": "active", "session_agent": agent_id, "backend_name": agent_id,
        "backend_type": info["backend_type"], "backend_command": info["command"],
        "backend_available": available, "lock_owner": agent_id,
        "started_at": ts.isoformat(), "updated_at": ts.isoformat(),
        "may_modify_files": False, "may_commit": False, "may_push": False,
        "may_execute_shell": agent_id == "noop",
        "invocation_allowed": info["invocation_allowed"],
        "execution_authorized": False, "repo_path": str(root.path),
    }
    d = root.join(Path(".pcae") / "agent-locks"); d.mkdir(parents=True, exist_ok=True)
    (d / ".gitignore").write_text("*\n")
    (d / "latest.json").write_text(json.dumps(lock_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"lock_synced": True, "lock_backend_name": agent_id, "lock_conflict": False, "blocker": None, "execution_authorized": False}
from pcae.core.architecture import (
    read_architecture_history_summary,
    write_architecture_history_snapshot,
)
from pcae.core.check import run_checks
from pcae.core.context import (
    BOOTSTRAP_COMPACT_ADVISORY,
    CONTEXT_PACK_UNIVERSAL_AGENT_NOTE,
    build_bootstrap_prompt,
    build_context_pack,
    resolve_profile,
)
from pcae.core.health import build_health_data
from pcae.core.paths import HarnessPath
from pcae.core.provenance import (
    ProvenanceEvent,
    ProvenanceSession,
    append_provenance_event,
    build_provenance_sessions,
    build_provenance_timeline,
    find_active_session,
)
from pcae.core.session import (
    ContinuityReport,
    SessionUpdate,
    build_continuity_report,
    read_session_snapshot,
    update_session_snapshot,
    write_session_snapshot,
)

from pcae.commands.phase import (
    HANDOFFS_DIR,
    _read_latest_audit,
    _read_phase_queue,
    _read_prompt_metadata,
)
from pcae.core.tasks import find_latest_active_task


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Q.1 — Bootstrap readiness helpers
# ═══════════════════════════════════════════════════════════════════════════

READINESS_READY = "ready"
READINESS_READY_WARNINGS = "ready_with_warnings"
READINESS_NEEDS_ATTENTION = "needs_attention"
READINESS_BLOCKED = "blocked"


def _read_latest_phase_report(root: HarnessPath) -> dict | None:
    """Read the latest phase report from .pcae/phase-reports/latest.json."""
    p = root.join(Path(".pcae") / "phase-reports" / "latest.json")
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _load_push_check(root: HarnessPath) -> dict | None:
    """Determine push state from git.

    Checks origin/main..HEAD count. Returns None if git is unavailable.
    """
    import subprocess
    try:
        r = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True, text=True, cwd=str(root.path), timeout=10,
        )
        if r.returncode == 0:
            count = int(r.stdout.strip())
            return {
                "unpushed_commits": count,
                "mode": "nothing_to_push" if count == 0 else "needs_push",
            }
        return {"unpushed_commits": 0, "mode": "unknown"}
    except Exception:
        return None


def _count_active_tasks(root: HarnessPath) -> int:
    """Count active task files (excluding .DS_Store)."""
    active_dir = root.join(Path("tasks") / "active")
    if not active_dir.is_dir():
        return 0
    count = 0
    try:
        for f in active_dir.iterdir():
            if f.is_file() and f.name != ".DS_Store" and f.suffix in (".md",):
                count += 1
    except OSError:
        pass
    return count


def _check_telegram_runtime() -> dict:
    """Check Telegram runtime env vars without printing secrets.

    Returns a dict with status fields. Never prints token or chat ID values.
    """
    import os
    token = os.environ.get("PCAE_TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("PCAE_TELEGRAM_CHAT_ID", "")
    enabled = os.environ.get("PCAE_TELEGRAM_ENABLED", "").lower() in ("1", "true", "yes")
    configured = bool(token and chat_id)
    notify_enabled = os.environ.get("PCAE_NOTIFY_ENABLED", "").lower() in ("1", "true", "yes")
    return {
        "runtime_loaded": bool(token or chat_id),
        "telegram_configured": configured,
        "telegram_enabled": enabled and configured,
        "token_present": bool(token),
        "chat_id_present": bool(chat_id),
        "notify_enabled": notify_enabled,
        "status": "loaded" if (token or chat_id) else "not_loaded",
    }


def _extract_phase_number(phase_id: str) -> str:
    """Extract the base phase number from a phase ID like '94Q', '94Q.1', '94P'."""
    if not phase_id:
        return ""
    # Strip trailing dot-subparts like .1, .2
    import re
    m = re.match(r'^(\d+[A-Za-z]+(?:\.[0-9]+)*)', phase_id)
    return m.group(1) if m else phase_id


def _phase_is_completed(phase_id: str, latest_report: dict | None) -> bool:
    """Check whether a phase appears to be completed based on the latest report."""
    if latest_report is None:
        return False
    report_phase = latest_report.get("phase_id", "")
    report_status = latest_report.get("status", "")
    if not report_phase or report_status != "completed":
        return False
    # Phase is completed if it matches or is an ancestor of the report phase
    report_base = _extract_phase_number(report_phase)
    task_base = _extract_phase_number(phase_id)
    # Exact match or task phase is a predecessor
    return task_base == report_base or report_phase.startswith(task_base)


def _classify_bootstrap_readiness(
    *,
    check_passed: bool,
    health_status: str,
    active_task: dict | None,
    latest_report: dict | None,
    latest_handoff: dict | None,
    push_check: dict | None,
    tg_runtime: dict | None,
    task_memory_warnings: bool,
) -> tuple[str, list[str]]:
    """Classify bootstrap readiness across multiple factors.

    Returns (readiness_status, issues_list).
    """
    issues: list[str] = []
    blocked: list[str] = []
    warnings: list[str] = []

    # ── Health/check ────────────────────────────────────────────────────
    if health_status != "healthy":
        blocked.append(f"pcae health: {health_status}")
    if not check_passed:
        blocked.append("pcae check: failed")

    # ── Stale active task ───────────────────────────────────────────────
    if active_task is not None:
        task_id = active_task.get("id", "")
        task_title = active_task.get("title", "")
        if latest_report is not None:
            report_phase = latest_report.get("phase_id", "")
            report_status = latest_report.get("status", "")
            if report_status == "completed" and report_phase:
                # Check if active task phase is already completed
                if _phase_is_completed(report_phase, latest_report):
                    # Active task belongs to a completed phase → stale
                    blocked.append(f"Active task appears stale (phase {report_phase} is completed)")
                # Check if active task phase does not match recommended next
                rec_next = latest_report.get("recommended_next_phase", "")
                if rec_next and task_title:
                    rec_base = _extract_phase_number(rec_next.split("—")[0].strip() if "—" in rec_next else rec_next.split("-")[0].strip())
                    if rec_base and rec_base not in task_title:
                        warnings.append(f"Active task may not match recommended next: {rec_next}")

    # ── Stale handoff ───────────────────────────────────────────────────
    if latest_handoff is not None and latest_report is not None:
        handoff_created = latest_handoff.get("created_at", "")
        report_completed = latest_report.get("completed_at", "") or latest_report.get("created_at", "")
        if handoff_created and report_completed and handoff_created < report_completed:
            warnings.append("Latest handoff is older than latest completed phase report")

    # ── Phase report completeness ────────────────────────────────────────
    if latest_report is not None:
        completeness = latest_report.get("report_completeness", "")
        if completeness == "partial":
            blocked.append("Latest phase report is partial")
        elif completeness == "incomplete":
            blocked.append("Latest phase report is incomplete")
        # Check report consistency
        report_phase = latest_report.get("phase_id", "")
        report_status = latest_report.get("status", "")
        if report_status == "completed" and not report_phase:
            warnings.append("Latest phase report has no phase_id")

    # ── Push state ──────────────────────────────────────────────────────
    if push_check is not None:
        push_mode = push_check.get("mode", "")
        unpushed = push_check.get("unpushed_commits", 0)
        if isinstance(unpushed, str):
            try:
                unpushed = int(unpushed)
            except (ValueError, TypeError):
                unpushed = 0
        if unpushed > 0:
            warnings.append(f"origin/main..HEAD: {unpushed} unpushed commit(s)")

    # ── Task memory ──────────────────────────────────────────────────────
    if task_memory_warnings:
        warnings.append("Task memory has warnings (stale active files)")

    # ── Telegram runtime ─────────────────────────────────────────────────
    if tg_runtime is not None:
        if tg_runtime.get("status") == "not_loaded":
            warnings.append("Telegram runtime env not loaded")
        elif not tg_runtime.get("telegram_enabled", False):
            if tg_runtime.get("telegram_configured", False):
                warnings.append("Telegram configured but not enabled")
            else:
                warnings.append("Telegram not configured")

    # ── Determine status ─────────────────────────────────────────────────
    if blocked:
        return READINESS_BLOCKED, blocked + warnings
    elif warnings:
        return READINESS_READY_WARNINGS, warnings
    else:
        return READINESS_READY, []


def _format_push_status(push_check: dict | None) -> str:
    """Format push status with clear wording."""
    if push_check is None:
        return "unknown"
    mode = push_check.get("mode", "unknown")
    unpushed = push_check.get("unpushed_commits", 0)
    if isinstance(unpushed, str):
        try:
            unpushed = int(unpushed)
        except (ValueError, TypeError):
            unpushed = 0
    if mode == "nothing_to_push" and unpushed == 0:
        return "clean (nothing_to_push)"
    elif unpushed > 0:
        return f"needs_push ({unpushed} unpushed)"
    elif mode == "active_task":
        return "ready"
    return mode


def _load_latest_handoff(root: HarnessPath) -> dict | None:
    latest_path = root.join(HANDOFFS_DIR / "latest.json")
    if not latest_path.is_file():
        return None
    try:
        return json.loads(latest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _refresh_session_snapshot_for_governed_flow(root: HarnessPath) -> None:
    if find_latest_active_task(root) is None:
        return
    write_session_snapshot(root)


def run_session_write(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    snapshot = write_session_snapshot(root)

    print(f"Wrote session snapshot: {snapshot.relative_path.as_posix()}")
    return 0


def run_session_read(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    snapshot = read_session_snapshot(root)
    if snapshot is None:
        print("No session snapshot found at .pcae/session.json.")
        return 1

    print_session_snapshot(snapshot.data)
    return 0


def run_session_update(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    snapshot = update_session_snapshot(
        root,
        SessionUpdate(
            objective=args.objective,
            completed_step=args.completed_step,
            next_step=args.next_step,
            blocker=args.blocker,
            warning=args.warning,
            note=args.note,
        ),
    )

    print(f"Updated session snapshot: {snapshot.relative_path.as_posix()}")
    return 0


def run_session_end(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    _refresh_session_snapshot_for_governed_flow(root)
    check_result = run_checks(root)
    if not check_result.passed:
        print("Session end stopped: pcae check failed.")
        for violation in check_result.violations:
            print(f"  - {violation.text}")
        return 1

    session_snapshot = write_session_snapshot(root)
    architecture_snapshot = write_architecture_history_snapshot(root, check_result)

    print("Session end complete.")
    print_session_end_summary(session_snapshot.data, len(architecture_snapshot.entries))
    return 0


def run_session_bootstrap(args: argparse.Namespace) -> int:
    if getattr(args, "compact", False):
        return _run_compact_bootstrap(args)

    if not args.agent_id:
        print("Error: --agent-id is required when not using --compact.")
        return 1

    root = HarnessPath.cwd()

    try:
        acquire_result = acquire_agent_lock_idempotent(root, args.agent_id)
    except ValueError as error:
        print(str(error))
        return 1

    lock = acquire_result.lock
    already_held = acquire_result.already_held

    if not already_held:
        append_provenance_event(
            root,
            "agent_acquired",
            f"Agent lock acquired by {args.agent_id}",
            agent_id=args.agent_id,
        )

    # Rehydrate backend lock identity
    backend_lock_result = _sync_backend_lock(root, args.agent_id)

    _refresh_session_snapshot_for_governed_flow(root)
    health_data = build_health_data(root)
    health_status: str = health_data["overall_status"]
    check_passed = health_status == "healthy"

    session_snapshot = read_session_snapshot(root)
    active_task = None
    if session_snapshot is not None:
        task_data = session_snapshot.data.get("active_task")
        if isinstance(task_data, dict):
            active_task = task_data

    sessions = build_provenance_sessions(root)
    current_session = find_active_session(sessions)
    timeline = build_provenance_timeline(root)
    latest_event = timeline.latest_event

    handoff = _load_latest_handoff(root)

    # ── Phase 94Q.1: enriched readiness data ────────────────────────────
    latest_report = _read_latest_phase_report(root)
    push_check = _load_push_check(root)
    tg_runtime = _check_telegram_runtime()
    active_task_count = _count_active_tasks(root)
    task_memory_warnings = active_task_count > 1

    readiness, issues = _classify_bootstrap_readiness(
        check_passed=check_passed,
        health_status=health_status,
        active_task=active_task,
        latest_report=latest_report,
        latest_handoff=handoff,
        push_check=push_check,
        tg_runtime=tg_runtime,
        task_memory_warnings=task_memory_warnings,
    )
    ready = readiness in (READINESS_READY, READINESS_READY_WARNINGS)

    if args.json:
        print(
            json.dumps(
                {
                    "active_task": active_task,
                    "active_task_count": active_task_count,
                    "agent_id": args.agent_id,
                    "check_status": "passed" if check_passed else "failed",
                    "current_session": _session_summary(current_session),
                    "health_status": health_status,
                    "latest_event": _event_summary(latest_event),
                    "latest_handoff": handoff,
                    "latest_phase_report": latest_report,
                    "lock_acquired": not already_held,
                    "lock_backend_name": backend_lock_result["lock_backend_name"],
                    "lock_conflict": backend_lock_result["lock_conflict"],
                    "lock_rehydrated": backend_lock_result["lock_synced"],
                    "lock_synced": backend_lock_result["lock_synced"],
                    "provenance_event_count": timeline.event_count,
                    "push_check": push_check,
                    "readiness": readiness,
                    "readiness_issues": issues,
                    "ready": ready,
                    "recognized_backend": args.agent_id in _LOCKABLE_BACKENDS,
                    "task_memory_warnings": task_memory_warnings,
                    "telegram_runtime": tg_runtime,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if ready else 1

    print("Session bootstrap.")
    if already_held:
        print(f"Agent: {args.agent_id} (lock already held)")
    else:
        print(f"Agent: {args.agent_id}")
    if backend_lock_result["lock_synced"]:
        print(f"Backend lock rehydrated: {backend_lock_result['lock_backend_name']}")
    elif backend_lock_result["lock_conflict"]:
        print(f"Backend lock conflict: {backend_lock_result.get('blocker', 'unknown')}")
    elif args.agent_id in _LOCKABLE_BACKENDS:
        print(f"Backend lock: not rehydrated ({backend_lock_result.get('blocker', 'unknown')})")
    print(f"Health: {health_status}")
    print(f"Check: {'passed' if check_passed else 'failed'}")
    for v in health_data["violations"]:
        print(f"  - {v}")
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")
    if current_session is None:
        print("Current session: none")
    else:
        status = "active" if current_session.active else "closed"
        print(f"Current session: {current_session.session_id} ({status})")
    print(f"Provenance events: {timeline.event_count}")
    if latest_event is not None:
        print(f"Latest event: {latest_event.summary}")
    else:
        print("Latest event: none")

    # ── Phase 94Q.1: enriched readiness output ──────────────────────────
    if latest_report is not None:
        rp = latest_report.get("phase_id", "")
        rs = latest_report.get("status", "")
        rc = latest_report.get("report_completeness", "unknown")
        rn = latest_report.get("recommended_next_phase", "")
        print(f"Latest completed phase: {rp} ({rs}, report: {rc})")
        if rn:
            print(f"Recommended next phase: {rn}")

    print(f"Readiness: {readiness}")
    for issue in issues:
        print(f"  - {issue}")

    push_status = _format_push_status(push_check)
    print(f"Push: {push_status}")

    tg_status = tg_runtime.get("status", "unknown")
    tg_note = ""
    if tg_status == "not_loaded":
        tg_note = " (action: source ~/.config/pcae/telegram.env && pcae notify status)"
    elif not tg_runtime.get("telegram_enabled", False) and tg_runtime.get("telegram_configured", False):
        tg_note = " (configured but disabled)"
    print(f"Telegram runtime: {tg_status}{tg_note}")

    if handoff is not None:
        print()
        print("Last handoff:")
        print(f"  Summary: {handoff.get('summary', 'unknown')}")
        print(f"  Created: {handoff.get('created_at', 'unknown')}")
        print(f"  Branch: {handoff.get('branch', 'unknown')}")
        task_state = handoff.get("task_state", "unknown")
        task_id = handoff.get("active_task_id")
        print(f"  Task: {task_state}" + (f" ({task_id})" if task_id else ""))
        print(f"  Health: {handoff.get('health_status', 'unknown')}")
        print(f"  Check: {'passed' if handoff.get('check_passed') else 'failed'}")
        push_ready = handoff.get("push_ready", False)
        push_mode = handoff.get("push_mode", "unknown")
        push_label = "clean" if push_mode == "nothing_to_push" and not push_ready else ("ready" if push_ready else "not ready")
        print(f"  Push: {push_label} ({push_mode})")
        print(f"  Review: {handoff.get('lifecycle_review', 'unknown')}")
        print(f"  Latest commit: {handoff.get('latest_commit', 'unknown')}")
        print(f"  Next action: {handoff.get('recommended_next_action', 'unknown')}")
        if handoff.get("phase_queue_present"):
            print(f"  Phase queue: {handoff['phase_queue_count']} entries")
            print(f"  Next queued: {handoff['phase_queue_next']}")
    challenge = build_irg_challenge_context(root)
    assessment = build_challenge_attention_assessment(root, surface="bootstrap", challenge_data=challenge)
    lines = render_irg_challenge_compact_lines_with_allocation(
        challenge, assessment["allocation"], surface="bootstrap"
    )
    if lines:
        print()
        for line in lines:
            print(line)
    return 0 if ready else 1


def _run_compact_bootstrap(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()

    # Handle --sync-lock for compact bootstrap
    sync_lock: bool = getattr(args, "sync_lock", False)
    agent_id: str | None = getattr(args, "agent_id", None)
    backend_lock_result: dict = {"lock_synced": False, "lock_backend_name": None, "lock_conflict": False, "blocker": None, "execution_authorized": False}
    if sync_lock and agent_id:
        backend_lock_result = _sync_backend_lock(root, agent_id)

    pack = build_context_pack(root)
    challenge = build_irg_challenge_context(root)
    handoff = _load_latest_handoff(root)
    audit = _read_latest_audit(root)
    prompt_meta = _read_prompt_metadata(root)
    profile_name: str | None = getattr(args, "profile", None)
    profile, is_unknown = resolve_profile(profile_name)
    prompt = build_bootstrap_prompt(
        pack, profile, handoff=handoff, audit=audit, prompt=prompt_meta,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "advisory": BOOTSTRAP_COMPACT_ADVISORY,
                    "agent_id": agent_id,
                    "bootstrap_prompt": prompt,
                    "governance_state": pack.governance_state,
                    "independent_challenge_context": challenge,
                    "latest_handoff": handoff,
                    "lock_backend_name": backend_lock_result["lock_backend_name"],
                    "lock_conflict": backend_lock_result["lock_conflict"],
                    "lock_rehydrated": backend_lock_result["lock_synced"],
                    "lock_synced": backend_lock_result["lock_synced"],
                    "operational_rules": list(pack.operational_rules),
                    "orchestration_state": pack.orchestration_state,
                    "profile_type": profile.profile_type,
                    "recognized_backend": agent_id in _LOCKABLE_BACKENDS if agent_id else False,
                    "validation_commands": list(pack.validation_commands),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if sync_lock and agent_id:
        if backend_lock_result["lock_synced"]:
            print(f"Backend lock rehydrated: {backend_lock_result['lock_backend_name']}")
        else:
            print(f"Backend lock not rehydrated: {backend_lock_result.get('blocker', 'unknown')}")

    if is_unknown:
        print(
            f"Warning: unknown profile '{profile_name}';"
            " using universal profile."
        )
    print(f"Profile: {profile.profile_type}")
    print()
    print(prompt)
    print()
    print("Token optimization note: bootstrap prompt is compact by design.")
    print(f"Vendor-neutral note: {CONTEXT_PACK_UNIVERSAL_AGENT_NOTE}")
    print(f"Quality preservation note: {BOOTSTRAP_COMPACT_ADVISORY}")
    assessment = build_challenge_attention_assessment(root, surface="bootstrap", challenge_data=challenge)
    lines = render_irg_challenge_compact_lines_with_allocation(
        challenge, assessment["allocation"], surface="bootstrap"
    )
    if lines:
        print()
        for line in lines:
            print(line)
    return 0


def _session_summary(session: ProvenanceSession | None) -> dict | None:
    if session is None:
        return None
    return {
        "active": session.active,
        "agent_id": session.agent_id,
        "ended_at": session.ended_at,
        "event_count": session.event_count,
        "session_id": session.session_id,
        "started_at": session.started_at,
    }


def _event_summary(event: ProvenanceEvent | None) -> dict | None:
    if event is None:
        return None
    return {
        "agent_id": event.agent_id,
        "event_type": event.event_type,
        "summary": event.summary,
        "timestamp": event.timestamp,
    }


def run_session_start(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    check_result = run_checks(root)
    if not check_result.passed:
        print("Session start stopped: pcae check failed.")
        for violation in check_result.violations:
            print(f"  - {violation.text}")
        return 1

    session_snapshot = read_session_snapshot(root)
    try:
        architecture_summary = read_architecture_history_summary(root)
    except ValueError as error:
        architecture_summary = None
        architecture_message = str(error)
    else:
        architecture_message = None

    print("Session start summary.")
    if session_snapshot is None:
        print("No session snapshot found at .pcae/session.json.")
    else:
        print_session_start_snapshot(session_snapshot.data)

    if architecture_summary is None:
        print(architecture_message)
    else:
        latest = architecture_summary.latest
        print(f"Architecture history entries: {len(architecture_summary.entries)}")
        print(f"Latest enforcement mode: {latest.get('enforcement_mode', 'unknown')}")
        print(
            "Latest session continuity: "
            f"{latest.get('session_continuity', 'unknown')}"
        )
    return 0


def print_session_start_snapshot(data: dict) -> None:
    active_task = data.get("active_task")
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")

    git = data.get("git", {})
    print(f"Git branch: {git.get('branch', 'unknown')}")
    print(f"Git status: {git.get('status_summary', 'unknown')}")
    print(f"Current objective: {data.get('current_objective', '')}")
    print(f"Last completed step: {data.get('last_completed_step', '')}")
    print(f"Next recommended step: {data.get('next_recommended_step', '')}")
    print_list("Blockers", data.get("blockers", []))
    print_list("Warnings", data.get("warnings", []))


def print_session_end_summary(data: dict, architecture_history_count: int) -> None:
    active_task = data.get("active_task")
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")

    git = data.get("git", {})
    print(f"Git status: {git.get('status_summary', 'unknown')}")
    print(f"Architecture history entries: {architecture_history_count}")
    next_step = data.get("next_recommended_step") or "none"
    print(f"Next recommended step: {next_step}")


def print_session_snapshot(data: dict) -> None:
    active_task = data.get("active_task")
    print("Session snapshot:")
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")

    git = data.get("git", {})
    print(f"Git branch: {git.get('branch', 'unknown')}")
    print(f"Git status: {git.get('status_summary', 'unknown')}")
    print(f"Current objective: {data.get('current_objective', '')}")
    print(f"Last completed step: {data.get('last_completed_step', '')}")
    print(f"Next recommended step: {data.get('next_recommended_step', '')}")
    print_list("Blockers", data.get("blockers", []))
    print_list("Warnings", data.get("warnings", []))
    print_list("Architectural notes", data.get("architectural_notes", []))


def run_session_continuity_check(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    handoff = _load_latest_handoff(root)
    audit = _read_latest_audit(root)
    queue = _read_phase_queue(root)
    prompt_meta = _read_prompt_metadata(root)

    report = build_continuity_report(
        root, handoff_data=handoff, audit_data=audit, queue=queue,
        prompt_data=prompt_meta,
    )

    if args.json:
        print(json.dumps(_continuity_report_to_dict(report), indent=2, sort_keys=True))
        return 0 if report.suitable_for_continuation else 1

    print("Continuity check")
    print(f"  Branch: {report.branch}")
    print(f"  Working tree: {report.working_tree}")
    print(f"  Health: {report.health_status}")
    print(f"  Check: {'passed' if report.check_passed else 'failed'}")
    print(f"  Task state: {report.task_state}")
    if report.active_task_id:
        print(f"  Active task: {report.active_task_id}")
    print(f"  Task memory: {report.task_memory_status}")
    print(f"  Push: {report.push_mode}")
    print()
    if report.handoff_present:
        print(f"  Handoff: present (created {report.handoff_created_at})")
        print(f"  Handoff summary: {report.handoff_summary}")
    else:
        print("  Handoff: missing")
    if report.audit_present:
        idle_note = ", healthy idle" if report.audit_healthy_idle else ""
        print(
            f"  Audit: {report.audit_phases_detected} phases, "
            f"{report.audit_warning_count} warnings"
            f"{idle_note} (created {report.audit_created_at})"
        )
    else:
        print("  Audit: missing")
    if report.phase_queue_present:
        print(f"  Phase queue: {report.phase_queue_count} entries")
    else:
        print("  Phase queue: empty")
    if report.prompt_present:
        print(f"  Latest prompt: {report.prompt_title} (created {report.prompt_created_at})")
    print()
    if report.issues:
        print("  Issues:")
        for issue in report.issues:
            print(f"    - {issue}")
        print()
    print(
        f"  Suitable for continuation: "
        f"{'yes' if report.suitable_for_continuation else 'no'}"
    )
    return 0 if report.suitable_for_continuation else 1


def _continuity_report_to_dict(report: ContinuityReport) -> dict:
    return {
        "active_task_id": report.active_task_id,
        "active_task_title": report.active_task_title,
        "audit_created_at": report.audit_created_at,
        "audit_healthy_idle": report.audit_healthy_idle,
        "audit_phases_detected": report.audit_phases_detected,
        "audit_present": report.audit_present,
        "audit_warning_count": report.audit_warning_count,
        "branch": report.branch,
        "check_passed": report.check_passed,
        "handoff_created_at": report.handoff_created_at,
        "handoff_present": report.handoff_present,
        "handoff_summary": report.handoff_summary,
        "health_status": report.health_status,
        "issues": list(report.issues),
        "phase_queue_count": report.phase_queue_count,
        "phase_queue_present": report.phase_queue_present,
        "prompt_created_at": report.prompt_created_at,
        "prompt_path": report.prompt_path,
        "prompt_present": report.prompt_present,
        "prompt_title": report.prompt_title,
        "push_mode": report.push_mode,
        "suitable_for_continuation": report.suitable_for_continuation,
        "task_memory_status": report.task_memory_status,
        "task_state": report.task_state,
        "working_tree": report.working_tree,
    }


def print_list(title: str, values: list[Any]) -> None:
    print(f"{title}:")
    if not values:
        print("  none")
        return

    for value in values:
        print(f"  - {value}")
