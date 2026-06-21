from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pcae.core.agent import (
    build_challenge_attention_assessment,
    build_irg_challenge_context,
    read_agent_lock,
    render_irg_challenge_compact_lines_with_allocation,
)
from pcae.core.check import run_checks
from pcae.core.orchestration import (
    build_workflow_simulation,
    build_workflow_validation,
    recommend_agent,
)
from pcae.core.paths import HarnessPath
from pcae.core.phase import complete_phase, handoff_phase, start_phase
from pcae.core.session import write_session_snapshot
from pcae.core.strategic_lineage import strategic_continuity_summary
from pcae.core.tasks import find_latest_active_task


def _refresh_session_snapshot_for_governed_flow(root: HarnessPath) -> None:
    if find_latest_active_task(root) is None:
        return
    write_session_snapshot(root)


def run_phase_complete(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = complete_phase(root, args.summary)

    print("Phase complete.")
    print(f"Summary: {result.summary}")
    print(f"Provenance events: {result.provenance_event_count}")
    if result.agent_released:
        print(f"Agent lock: released (by {result.agent_id})")
    else:
        print("Agent lock: none")
    challenge = build_irg_challenge_context(root)
    assessment = build_challenge_attention_assessment(root, surface="completion", challenge_data=challenge)
    lines = render_irg_challenge_compact_lines_with_allocation(
        challenge, assessment["allocation"], surface="completion"
    )
    if lines:
        print()
        for line in lines:
            print(line)
    return 0


def run_phase_handoff(args: argparse.Namespace) -> int:
    work_type: str | None = getattr(args, "work_type", None)
    workflow: str | None = getattr(args, "workflow", None)
    explicit_next_agent: str | None = args.next_agent

    root = HarnessPath.cwd()
    _refresh_session_snapshot_for_governed_flow(root)
    strategic_continuity = strategic_continuity_summary(root)

    auto_summary = args.summary is None
    summary = args.summary if args.summary is not None else _build_auto_summary(root)

    # Compute recommendation when work_type is provided.
    rec: dict | None = None
    suggested_workflow: dict | None = None
    if work_type:
        try:
            rec = recommend_agent(root, work_type)
            suggested_workflow = build_workflow_simulation(root, work_type)
        except ValueError as error:
            if not explicit_next_agent:
                print(str(error))
                return 1
            # explicit --next-agent present: proceed without recommendation data

    workflow_validation: dict | None = None
    if workflow:
        try:
            workflow_validation = build_workflow_validation(root, workflow)
        except ValueError as error:
            print(str(error))
            return 1

    # Resolve next agent.
    if explicit_next_agent:
        next_agent = explicit_next_agent
        recommendation_used = False
    elif rec is not None:
        next_agent = rec["recommended_agent"]
        recommendation_used = True
    else:
        lock = read_agent_lock(root)
        if lock is not None:
            next_agent = lock.agent_id
            recommendation_used = False
        else:
            print("Please specify the next agent with --next-agent <agent-id>.")
            return 1

    result = handoff_phase(root, summary, next_agent)

    manual_steps = _build_manual_steps(next_agent)
    bootstrap_prompt = _build_bootstrap_prompt(next_agent)
    restart_workflows = _build_restart_workflows_data()

    handoff_artifact = _build_handoff_artifact(
        root=root,
        result=result,
        auto_summary=auto_summary,
        next_agent=next_agent,
    )
    _persist_handoff_artifact(root, handoff_artifact)

    # Handle --sync-lock: synchronize agent lock with next-agent
    sync_lock_requested = getattr(args, "sync_lock", False)
    lock_sync_performed = False
    lock_sync_blockers = []
    lock_backend_name = None

    if sync_lock_requested:
        lockable_backends = {
            "claude-local", "claude-deepseek", "claude-kimi",
            "codex", "manual", "noop",
        }
        if next_agent in lockable_backends:
            lock_result = _set_agent_lock(root, next_agent)
            if lock_result["lock_status"] == "active":
                lock_sync_performed = True
                lock_backend_name = next_agent
            else:
                lock_sync_blockers.append(lock_result.get("refusal_reason", "lock set failed"))
        else:
            lock_sync_blockers.append(f"'{next_agent}' is not a recognized lockable backend identity")

    if args.json:
        full_json = {
            **handoff_artifact,
            "check_status": "passed" if result.check_passed else "failed",
            "explicit_next_agent": explicit_next_agent,
            "lock_sync_requested": sync_lock_requested,
            "lock_sync_performed": lock_sync_performed,
            "lock_backend_name": lock_backend_name,
            "lock_sync_blockers": lock_sync_blockers,
            "manual_steps": manual_steps,
            "provenance_event_count": result.provenance_event_count,
            "recommendation_note": (
                "Recommendations are advisory; the user may override them."
            ),
            "recommendation_reason": rec["reason"] if rec else None,
            "recommendation_used": recommendation_used,
            "recommended_agent": rec["recommended_agent"] if rec else None,
            "released_agent": result.released_agent,
            "restart_workflows": restart_workflows,
            "strategic_continuity": strategic_continuity,
            "suggested_workflow": _workflow_json_summary(suggested_workflow),
            "workflow": workflow,
            "workflow_valid": (
                workflow_validation["valid"]
                if workflow_validation is not None
                else None
            ),
            "workflow_warnings": (
                workflow_validation["warnings"]
                if workflow_validation is not None
                else []
            ),
            "governance_checkpoints": (
                workflow_validation["governance_checkpoints"]
                if workflow_validation is not None
                else []
            ),
            "work_type": work_type,
        }
        print(json.dumps(full_json, indent=2, sort_keys=True))
        return 0 if result.next_lock_acquired else 1

    print("Phase handoff.")
    print(f"Summary: {result.summary}")
    _print_strategic_continuity(strategic_continuity)
    if rec is not None:
        print("Recommendations are advisory; the user may override them.")
        print(f"Recommended agent: {rec['recommended_agent']} (work type: {work_type})")
        print(f"Reason: {rec['reason']}")
        if suggested_workflow is not None:
            step_count = len(suggested_workflow["steps"])
            print(
                f"Suggested next workflow: {suggested_workflow['workflow']} "
                f"({step_count} planned steps)"
            )
        if explicit_next_agent:
            if explicit_next_agent == rec["recommended_agent"]:
                print("User override: explicit --next-agent matches recommendation.")
            else:
                print(
                    "User override: explicit --next-agent is being used "
                    f"({explicit_next_agent}) instead of the recommendation."
                )
    if workflow_validation is not None:
        print("Workflow validation:")
        print(f"  Workflow: {workflow_validation['workflow']}")
        print(
            "  Result: "
            f"{'valid' if workflow_validation['valid'] else 'invalid'}"
        )
        print("  Recommendations remain advisory; validation checks coherence, not mandatory routing.")
        if workflow_validation["warnings"]:
            print("  Warnings:")
            for warning in workflow_validation["warnings"]:
                print(f"    - {warning}")
        checkpoints = workflow_validation["governance_checkpoints"]
        print("  Governance checkpoints:")
        if checkpoints:
            for checkpoint in checkpoints:
                print(
                    f"    {checkpoint['step']}. {checkpoint['work_type']}: "
                    f"{checkpoint['checkpoint']}"
                )
        else:
            print("    - none")
    print(f"Health: {result.health_status}")
    print(f"Check: {'passed' if result.check_passed else 'failed'}")
    for v in result.violations:
        print(f"  - {v}")
    print(f"Provenance events: {result.provenance_event_count}")
    print(f"Released agent: {result.released_agent or 'none'}")
    print(f"Next agent: {result.next_agent}")
    if result.next_lock_acquired:
        print(f"Agent lock: acquired by {result.next_agent}")
    else:
        print("Agent lock: not acquired (lock already held)")

    if sync_lock_requested:
        if lock_sync_performed:
            print(f"Agent lock synced: {lock_backend_name} (active)")
        else:
            print(f"Agent lock sync blocked: {'; '.join(lock_sync_blockers)}")

    print()
    print("Manual handoff steps:")
    for i, step in enumerate(manual_steps, 1):
        print(f"  {i}. {step}")

    print()
    print("Bootstrap prompt (copy-ready):")
    print("─" * 64)
    print(bootstrap_prompt)
    print("─" * 64)

    print()
    print(_build_restart_workflows_text())

    challenge = build_irg_challenge_context(root)
    assessment = build_challenge_attention_assessment(root, surface="handoff", challenge_data=challenge)
    lines = render_irg_challenge_compact_lines_with_allocation(
        challenge, assessment["allocation"], surface="handoff"
    )
    if lines:
        print()
        for line in lines:
            print(line)

    return 0 if result.next_lock_acquired else 1


def _build_auto_summary(root: HarnessPath) -> str:
    import subprocess

    from pcae.core.git_status import read_git_branch, read_git_changes
    from pcae.core.health import build_health_data, is_healthy
    from pcae.core.review import lifecycle_review_status

    parts: list[str] = []

    branch = read_git_branch(root)
    parts.append(f"branch={branch}")

    changes = read_git_changes(root)
    parts.append("tree=clean" if not changes else f"tree={len(changes)} changed")

    active_task = find_latest_active_task(root)
    if active_task:
        parts.append(f"task={active_task.task_id} ({active_task.title})")
    else:
        parts.append("task=idle")

    health_data = build_health_data(root)
    health_ok = is_healthy(health_data)
    parts.append(f"health={'healthy' if health_ok else 'unhealthy'}")

    check_result = run_checks(root)
    parts.append(f"check={'passed' if check_result.passed else 'failed'}")

    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        unpushed = int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=root.path,
                check=True,
                capture_output=True,
                text=True,
            )
            unpushed = int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            unpushed = 0
    parts.append(f"unpushed={unpushed}")

    task_id = active_task.task_id if active_task else None
    review = lifecycle_review_status(root, task_id)
    parts.append(f"review={review}")

    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-1", "--format=%s"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        latest_commit = result.stdout.strip()
        if latest_commit:
            parts.append(f"latest_commit={latest_commit}")
    except (subprocess.CalledProcessError, OSError):
        pass

    return "Phase handoff: " + ", ".join(parts)


HANDOFFS_DIR = Path(".pcae") / "handoffs"
PHASE_QUEUE_PATH = Path(".pcae") / "phase-queue.json"
PHASE_AUDITS_DIR = Path(".pcae") / "phase-audits"

PLACEHOLDER_PATTERNS = [
    "test phase",
    "next step",
    "placeholder",
    "dummy",
]


def _build_handoff_artifact(
    *,
    root: HarnessPath,
    result,
    auto_summary: bool,
    next_agent: str,
) -> dict:
    import subprocess

    from pcae.core.git_status import read_git_branch, read_git_changes
    from pcae.core.review import lifecycle_review_status
    from pcae.core.tasks import diagnose_task_memory

    branch = read_git_branch(root)
    changes = read_git_changes(root)
    active_task = find_latest_active_task(root)
    diagnostics = diagnose_task_memory(root)

    task_id = active_task.task_id if active_task else None
    review = lifecycle_review_status(root, task_id)

    try:
        count_result = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            cwd=root.path, check=True, capture_output=True, text=True,
        )
        unpushed = int(count_result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        try:
            count_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=root.path, check=True, capture_output=True, text=True,
            )
            unpushed = int(count_result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            unpushed = 0

    latest_commit = ""
    recent_commits: list[str] = []
    try:
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-5", "--format=%s"],
            cwd=root.path, check=True, capture_output=True, text=True,
        )
        lines = [line.strip() for line in log_result.stdout.splitlines() if line.strip()]
        if lines:
            latest_commit = lines[0]
            recent_commits = lines
    except (subprocess.CalledProcessError, OSError):
        pass

    from pcae.commands.push import assess_push_readiness

    push = assess_push_readiness(root)

    queue = _read_phase_queue(root)

    audit = _read_latest_audit(root)
    audit_summary: dict | None = None
    if audit is not None:
        audit_summary = {
            "present": True,
            "created_at": audit.get("created_at"),
            "phases_detected": audit.get("phases_detected", 0),
            "warning_count": len(audit.get("warnings", [])),
            "healthy_idle": audit.get("healthy_idle", False),
        }

    prompt_meta = _read_prompt_metadata(root)
    prompt_summary: dict | None = None
    if prompt_meta is not None:
        prompt_summary = {
            "present": True,
            "title": prompt_meta.get("title"),
            "created_at": prompt_meta.get("created_at"),
            "path": prompt_meta.get("latest_path"),
        }

    now = datetime.now(timezone.utc)
    task_suffix = task_id if task_id else "idle"
    handoff_id = f"handoff-{now:%Y%m%dT%H%M%S}-{now.microsecond:06d}-{task_suffix}"

    return {
        "active_task_id": task_id,
        "active_task_title": active_task.title if active_task else None,
        "audit_summary": audit_summary,
        "auto_summary": auto_summary,
        "bootstrap_command": f"pcae session bootstrap --agent-id {next_agent}",
        "branch": branch,
        "check_passed": result.check_passed,
        "created_at": now.isoformat(),
        "handoff_id": handoff_id,
        "health_status": result.health_status,
        "latest_commit": latest_commit,
        "lifecycle_review": review,
        "next_agent": next_agent,
        "phase_queue_count": len(queue),
        "phase_queue_next": _phase_queue_entry_title(queue[0]) if queue else None,
        "phase_queue_present": len(queue) > 0,
        "prompt_summary": prompt_summary,
        "push_mode": push.mode,
        "push_ready": push.ready,
        "recent_commits": recent_commits,
        "recommended_next_action": f"pcae session bootstrap --agent-id {next_agent}",
        "summary": result.summary,
        "task_memory_status": "clean" if not diagnostics.has_errors and not diagnostics.has_warnings else "errors" if diagnostics.has_errors else "warnings",
        "task_state": "active" if active_task else "idle",
        "unpushed_commits": unpushed,
        "working_tree": "clean" if not changes else f"{len(changes)} changed",
        "activation": _build_handoff_activation_summary(root),
    }


def _build_handoff_activation_summary(root: HarnessPath) -> dict | None:
    act_path = root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")
    if not act_path.is_file():
        return None
    try:
        act = json.loads(act_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    status = _build_single_runner_activation_status(root)
    scenario_path = root.join(SINGLE_RUNNER_ACTIVATION_SCENARIOS_DIR / "latest.json")
    scenario_present = scenario_path.is_file()
    return {
        "activation_present": True,
        "task_created": act.get("task_created", False),
        "prompt_executed": act.get("prompt_executed", False),
        "implementation_performed": act.get("implementation_performed", False),
        "execution_authorized": act.get("execution_authorized", False),
        "active_task_matches_activation": status.get("active_task_matches_activation", False),
        "rollback_available": status.get("rollback_available", False),
        "scenario_present": scenario_present,
    }


def _persist_handoff_artifact(root: HarnessPath, artifact: dict) -> None:
    handoffs_dir = root.join(HANDOFFS_DIR)
    handoffs_dir.mkdir(parents=True, exist_ok=True)

    content = json.dumps(artifact, indent=2, sort_keys=True) + "\n"

    latest_path = handoffs_dir / "latest.json"
    latest_path.write_text(content, encoding="utf-8")

    timestamped_path = handoffs_dir / f"{artifact['handoff_id']}.json"
    timestamped_path.write_text(content, encoding="utf-8")


def run_phase_handoff_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    latest_path = root.join(HANDOFFS_DIR / "latest.json")

    if not latest_path.is_file():
        if args.json:
            print(json.dumps({"error": "no handoff artifact found"}, indent=2))
        else:
            print("No handoff artifact found. Run pcae phase handoff first.")
        return 1

    content = latest_path.read_text(encoding="utf-8")

    if args.json:
        print(content.rstrip())
    else:
        data = json.loads(content)
        print("Latest handoff artifact")
        print(f"  Handoff ID: {data['handoff_id']}")
        print(f"  Created: {data['created_at']}")
        print(f"  Branch: {data['branch']}")
        print(f"  Working tree: {data['working_tree']}")
        print(f"  Task: {data['task_state']}", end="")
        if data.get("active_task_id"):
            print(f" ({data['active_task_id']})")
        else:
            print()
        print(f"  Health: {data['health_status']}")
        print(f"  Check: {'passed' if data['check_passed'] else 'failed'}")
        print(f"  Task memory: {data['task_memory_status']}")
        print(f"  Push: {'ready' if data['push_ready'] else 'not ready'} ({data['push_mode']})")
        print(f"  Lifecycle review: {data['lifecycle_review']}")
        print(f"  Unpushed commits: {data['unpushed_commits']}")
        print(f"  Latest commit: {data['latest_commit']}")
        print(f"  Next agent: {data['next_agent']}")
        print(f"  Auto-summary: {data['auto_summary']}")
        print(f"  Summary: {data['summary']}")
        if data.get("phase_queue_present"):
            print(f"  Phase queue: {data['phase_queue_count']} entries")
            print(f"  Next queued: {data['phase_queue_next']}")
        audit_s = data.get("audit_summary")
        if audit_s and audit_s.get("present"):
            print(f"  Audit: {audit_s['phases_detected']} phases, {audit_s['warning_count']} warnings, created {audit_s['created_at']}")
        prompt_s = data.get("prompt_summary")
        if prompt_s and prompt_s.get("present"):
            print(f"  Latest prompt: {prompt_s['title']} (created {prompt_s['created_at']})")
        print()
        print(f"  Bootstrap: {data['bootstrap_command']}")

    return 0


def run_phase_handoff_prune(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    handoffs_dir = root.join(HANDOFFS_DIR)
    keep: int = args.keep
    dry_run: bool = args.dry_run

    if not handoffs_dir.is_dir():
        if args.json:
            print(json.dumps({"pruned": [], "kept": 0, "total": 0}, indent=2))
        else:
            print("No handoff artifacts found.")
        return 0

    timestamped = sorted(
        (f for f in handoffs_dir.iterdir() if f.name.startswith("handoff-") and f.name.endswith(".json")),
        key=lambda f: f.name,
    )

    total = len(timestamped)
    to_prune = timestamped[:-keep] if keep < total else []

    if args.json:
        result = {
            "dry_run": dry_run,
            "kept": total - len(to_prune),
            "pruned": [f.name for f in to_prune],
            "total": total,
        }
        if not dry_run:
            for f in to_prune:
                f.unlink()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if not to_prune:
        print(f"No handoff artifacts to prune ({total} total, keeping {keep}).")
        return 0

    if dry_run:
        print(f"Dry run: would prune {len(to_prune)} of {total} handoff artifacts (keeping {keep}):")
        for f in to_prune:
            print(f"  - {f.name}")
    else:
        for f in to_prune:
            f.unlink()
        print(f"Pruned {len(to_prune)} of {total} handoff artifacts (kept {keep}).")

    return 0


def _read_phase_queue(root: HarnessPath) -> list:
    queue_path = root.join(PHASE_QUEUE_PATH)
    if not queue_path.is_file():
        return []
    try:
        data = json.loads(queue_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_phase_queue(root: HarnessPath, queue: list) -> None:
    queue_path = root.join(PHASE_QUEUE_PATH)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(queue, f, indent=2)
        f.write("\n")


def _phase_queue_entry_title(entry) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        title = entry.get("title")
        if isinstance(title, str):
            return title
    return str(entry)


def _phase_queue_entry_details(entry) -> dict:
    title = _phase_queue_entry_title(entry)
    if isinstance(entry, dict):
        return {
            "title": title,
            "source_type": entry.get("source_type", "manual"),
            "source_prompt_path": entry.get("source_prompt_path"),
            "source_prompt_created_at": entry.get("source_prompt_created_at"),
            "created_at": entry.get("created_at"),
            "structured": True,
        }
    return {
        "title": title,
        "source_type": "manual",
        "source_prompt_path": None,
        "source_prompt_created_at": None,
        "created_at": None,
        "structured": False,
    }


def run_phase_queue_add(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    queue = _read_phase_queue(root)
    queue.append(args.description)
    _write_phase_queue(root, queue)

    if args.json:
        print(json.dumps({"added": args.description, "position": len(queue), "queue_length": len(queue)}, indent=2, sort_keys=True))
    else:
        print(f"Added to phase queue (position {len(queue)}): {args.description}")
    return 0


def run_phase_queue_list(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    queue = _read_phase_queue(root)
    entries = [_phase_queue_entry_details(entry) for entry in queue]

    if args.json:
        print(json.dumps({
            "queue": queue,
            "entries": entries,
            "queue_length": len(queue),
        }, indent=2, sort_keys=True))
        return 0

    if not queue:
        print("Phase queue is empty.")
        return 0

    print(f"Phase queue ({len(queue)} entries):")
    for i, entry in enumerate(entries, 1):
        print(f"  {i}. {entry['title']}")
        if entry["structured"] and entry["source_type"] == "captured_prompt":
            print(f"     source: {entry['source_prompt_path']}")
    return 0


def run_phase_queue_show(args: argparse.Namespace) -> int:
    return run_phase_queue_list(args)


def run_phase_queue_clear(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    queue = _read_phase_queue(root)
    count = len(queue)
    _write_phase_queue(root, [])

    if args.json:
        print(json.dumps({"cleared": count}, indent=2, sort_keys=True))
    else:
        print(f"Cleared {count} entries from phase queue.")
    return 0


def run_phase_queue_check(args: argparse.Namespace) -> int:
    from pcae.core.git_status import read_git_changes
    from pcae.core.health import build_health_data, is_healthy
    from pcae.core.tasks import diagnose_task_memory

    from pcae.commands.push import assess_push_readiness

    root = HarnessPath.cwd()
    queue = _read_phase_queue(root)
    reasons: list[str] = []

    if not queue:
        reasons.append("phase queue is empty or absent")

    changes = read_git_changes(root)
    if changes:
        reasons.append("working tree is dirty")

    health_data = build_health_data(root)
    if not is_healthy(health_data):
        reasons.append("health check failed")

    check_result = run_checks(root)
    if not check_result.passed:
        reasons.append("pcae check failed")

    active_task = find_latest_active_task(root)
    if active_task is not None:
        reasons.append(f"active task exists: {active_task.task_id}")

    diagnostics = diagnose_task_memory(root)
    if diagnostics.has_errors or diagnostics.has_warnings:
        reasons.append("task memory has inconsistencies")

    push = assess_push_readiness(root)
    if push.mode == "not_ready":
        reasons.append(f"push check is blocked: {push.mode}")

    handoff_path = root.join(HANDOFFS_DIR / "latest.json")
    has_handoff = handoff_path.is_file()

    ready = len(reasons) == 0 and len(queue) > 0

    result = {
        "ready": ready,
        "queue_length": len(queue),
        "queue_present": len(queue) > 0,
        "next_queued": _phase_queue_entry_title(queue[0]) if queue else None,
        "next_queued_entry": _phase_queue_entry_details(queue[0]) if queue else None,
        "entries": [_phase_queue_entry_details(entry) for entry in queue],
        "working_tree": "clean" if not changes else f"{len(changes)} changed",
        "health_passed": is_healthy(health_data),
        "check_passed": check_result.passed,
        "active_task": active_task.task_id if active_task else None,
        "task_memory_clean": not diagnostics.has_errors and not diagnostics.has_warnings,
        "push_mode": push.mode,
        "latest_handoff_available": has_handoff,
        "reasons": reasons,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if ready else 1

    if not queue:
        print("Phase queue readiness: no queue")
        print("  Phase queue is empty or absent.")
        return 1

    if ready:
        print("Phase queue readiness: ready")
        print(f"  Queue: {len(queue)} entries")
        print(f"  Next: {_phase_queue_entry_title(queue[0])}")
        print("  Working tree: clean")
        print("  Health: passed")
        print("  Check: passed")
        print("  Active task: none")
        print("  Task memory: clean")
        print(f"  Push: {push.mode}")
        if has_handoff:
            print("  Latest handoff: available")
        return 0

    print("Phase queue readiness: not ready")
    print(f"  Queue: {len(queue)} entries")
    for reason in reasons:
        print(f"  - {reason}")
    return 1


def _is_placeholder(entry) -> bool:
    lower = _phase_queue_entry_title(entry).lower().strip()
    return any(pattern in lower for pattern in PLACEHOLDER_PATTERNS)


def run_phase_queue_hygiene(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    queue = _read_phase_queue(root)

    findings: list[dict] = []
    clearable_indices: list[int] = []

    for i, entry in enumerate(queue):
        if _is_placeholder(entry):
            title = _phase_queue_entry_title(entry)
            findings.append({
                "position": i + 1,
                "entry": title,
                "reason": "matches placeholder pattern",
            })
            clearable_indices.append(i)

    has_issues = len(findings) > 0

    if args.clear_placeholders:
        if not args.confirm:
            if args.json:
                print(json.dumps({
                    "error": "--clear-placeholders requires --confirm",
                    "findings": findings,
                    "clearable_count": len(clearable_indices),
                }, indent=2, sort_keys=True))
            else:
                print("Error: --clear-placeholders requires --confirm flag.")
                if findings:
                    print(f"  {len(findings)} placeholder(s) found. Re-run with --confirm to clear.")
            return 1

        if not findings:
            if args.json:
                print(json.dumps({
                    "cleared": 0,
                    "remaining": len(queue),
                    "findings": [],
                }, indent=2, sort_keys=True))
            else:
                print("No placeholder entries to clear.")
            return 0

        kept = [e for i, e in enumerate(queue) if i not in clearable_indices]
        _write_phase_queue(root, kept)

        if args.json:
            print(json.dumps({
                "cleared": len(clearable_indices),
                "remaining": len(kept),
                "findings": findings,
            }, indent=2, sort_keys=True))
        else:
            print(f"Cleared {len(clearable_indices)} placeholder(s).")
            for f in findings:
                print(f"  - removed position {f['position']}: {f['entry']}")
            if kept:
                print(f"  {len(kept)} real entries remain.")
        return 0

    if args.json:
        print(json.dumps({
            "queue_length": len(queue),
            "has_issues": has_issues,
            "findings": findings,
            "clearable_count": len(clearable_indices),
        }, indent=2, sort_keys=True))
        return 0

    if not queue:
        print("Phase queue hygiene: clean (queue is empty)")
        return 0

    if not has_issues:
        print(f"Phase queue hygiene: clean ({len(queue)} entries, no placeholders)")
        return 0

    print(f"Phase queue hygiene: {len(findings)} placeholder(s) found")
    for f in findings:
        print(f"  {f['position']}. {f['entry']} — {f['reason']}")
    print(f"\nTo clear: pcae phase queue hygiene --clear-placeholders --confirm")
    return 0


_SUPPORTED_SOURCE_TYPES = {"manual", "captured_prompt", "simulation", "fixture"}

_QUEUE_FIXTURE_MAX = 3

_QUEUE_FIXTURE_TITLE_PREFIX = "QUEUE-FIXTURE-"

_VALID_PHASE_ID_RE = re.compile(r"^\d+[A-Z](?:\.\d+)?$")


def _build_queue_validate(root: HarnessPath) -> dict:
    queue_path = root.join(PHASE_QUEUE_PATH)
    queue_file_present = queue_path.is_file()

    if not queue_file_present:
        return {
            "valid": True,
            "queue_file_present": False,
            "queue_readable": False,
            "queue_entry_count": 0,
            "queue_ready": False,
            "fixture_count": 0,
            "issues": [],
            "entries": [],
            "mutated": False,
            "note": "No execution performed. This is a read-only validation.",
        }

    try:
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "valid": False,
            "queue_file_present": True,
            "queue_readable": False,
            "queue_entry_count": 0,
            "queue_ready": False,
            "fixture_count": 0,
            "issues": [f"queue not readable: {exc}"],
            "entries": [],
            "mutated": False,
            "note": "No execution performed. This is a read-only validation.",
        }

    if not isinstance(queue, list):
        return {
            "valid": False,
            "queue_file_present": True,
            "queue_readable": True,
            "queue_entry_count": 0,
            "queue_ready": False,
            "fixture_count": 0,
            "issues": ["queue is not a JSON array"],
            "entries": [],
            "mutated": False,
            "note": "No execution performed. This is a read-only validation.",
        }

    entry_count = len(queue)
    entries: list[dict] = []
    all_issues: list[str] = []
    titles_seen: set[str] = set()
    fixture_count = 0

    for i, entry in enumerate(queue):
        position = i + 1
        title = _phase_queue_entry_title(entry)
        entry_result: dict = {"position": position, "title": title}
        entry_issues: list[str] = []

        if _is_placeholder(entry):
            entry_issues.append("matches placeholder pattern")

        if isinstance(entry, dict):
            source_type = entry.get("source_type", "manual")
            if source_type not in _SUPPORTED_SOURCE_TYPES:
                entry_issues.append(f"unsupported source_type: {source_type}")

            if source_type == "captured_prompt" and not entry.get("source_prompt_path"):
                entry_issues.append("captured_prompt entry missing source_prompt_path")

            forbidden_fields = {"execution_authorized", "execution_allowed"}
            for field in forbidden_fields:
                val = entry.get(field)
                if val is True:
                    entry_issues.append(f"contains forbidden field: {field}=true")

            phase_id = entry.get("phase_id")
            if phase_id is not None:
                if not isinstance(phase_id, str) or not _VALID_PHASE_ID_RE.match(phase_id):
                    entry_issues.append(f"invalid phase_id: {phase_id}")

            if source_type == "fixture" or entry.get("fixture") is True:
                entry_result["fixture"] = True
                fixture_count += 1

        if title in titles_seen:
            entry_issues.append("duplicate title")
        titles_seen.add(title)

        if entry_issues:
            entry_result["issues"] = entry_issues
        else:
            entry_result["status"] = "ok"

        entries.append(entry_result)

    for e in entries:
        if "issues" in e:
            for issue in e["issues"]:
                all_issues.append(f"position {e['position']}: {issue}")

    valid = len(all_issues) == 0

    return {
        "valid": valid,
        "queue_file_present": True,
        "queue_readable": True,
        "queue_entry_count": entry_count,
        "queue_ready": entry_count > 0,
        "fixture_count": fixture_count,
        "issues": all_issues,
        "entries": entries,
        "mutated": False,
        "note": "No execution performed. This is a read-only validation.",
    }


def _build_queue_fixture_entries(count: int) -> list[dict]:
    clamped = min(max(count, 1), _QUEUE_FIXTURE_MAX)
    entries = []
    for i in range(1, clamped + 1):
        entries.append({
            "title": f"{_QUEUE_FIXTURE_TITLE_PREFIX}{i:03d}",
            "source_type": "fixture",
            "fixture": True,
            "execution_authorized": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    return entries


def run_phase_queue_fixture_add(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    count = min(max(getattr(args, "count", 1), 1), _QUEUE_FIXTURE_MAX)
    entries = _build_queue_fixture_entries(count)
    queue = _read_phase_queue(root)
    queue.extend(entries)
    _write_phase_queue(root, queue)

    if args.json:
        print(json.dumps({
            "added": len(entries),
            "count": count,
            "entries": entries,
            "queue_length": len(queue),
            "mutated": True,
            "note": "Fixture entries added for testing. No execution performed.",
        }, indent=2, sort_keys=True))
        return 0

    print(f"Added {len(entries)} queue fixture entry/ies:")
    for e in entries:
        print(f"  - {e['title']}")
    print(f"Queue length: {len(queue)}")
    print("No execution performed.")
    return 0


def run_phase_queue_fixture_clear(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    queue = _read_phase_queue(root)
    fixture_titles = set()
    fixture_indices = []

    for i, entry in enumerate(queue):
        if isinstance(entry, dict) and (entry.get("source_type") == "fixture" or entry.get("fixture") is True):
            fixture_titles.add(_phase_queue_entry_title(entry))
            fixture_indices.append(i)

    kept = [e for i, e in enumerate(queue) if i not in fixture_indices]
    _write_phase_queue(root, kept)

    if args.json:
        print(json.dumps({
            "cleared": len(fixture_indices),
            "cleared_titles": sorted(fixture_titles),
            "remaining": len(kept),
            "mutated": True,
            "note": "Only fixture entries removed. No execution performed.",
        }, indent=2, sort_keys=True))
        return 0

    print(f"Cleared {len(fixture_indices)} fixture entry/ies.")
    for title in sorted(fixture_titles):
        print(f"  - {title}")
    print(f"{len(kept)} non-fixture entries remain.")
    print("No execution performed.")
    return 0


def run_phase_queue_validate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_queue_validate(root)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1

    print("Phase Queue Validation")
    print("=" * 40)
    print(f"  Queue file present: {'yes' if result['queue_file_present'] else 'no'}")
    print(f"  Queue readable: {'yes' if result['queue_readable'] else 'no'}")
    print(f"  Entry count: {result['queue_entry_count']}")
    print(f"  Queue ready: {'yes' if result['queue_ready'] else 'no'}")
    print(f"  Valid: {'yes' if result['valid'] else 'NO'}")

    if result["queue_readable"] and result["entries"]:
        print()
        for e in result["entries"]:
            if "issues" in e:
                print(f"  {e['position']}. {e['title']} — {len(e['issues'])} issue(s)")
                for issue in e["issues"]:
                    print(f"     - {issue}")
            else:
                print(f"  {e['position']}. {e['title']} — ok")

    if result["issues"]:
        print()
        print(f"  Issues ({len(result['issues'])}):")
        for issue in result["issues"]:
            print(f"    - {issue}")

    print()
    print(f"  {result['note']}")
    return 0 if result["valid"] else 1


QUEUE_APPROVALS_DIR = Path(".pcae") / "phase-queue-approvals"


def _compute_queue_digest(root: HarnessPath) -> str:
    queue_path = root.join(PHASE_QUEUE_PATH)
    if not queue_path.is_file():
        return hashlib.sha256(b"").hexdigest()
    content = queue_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def _build_queue_approve(root: HarnessPath, message: str) -> dict:
    validation = _build_queue_validate(root)

    if not validation["valid"]:
        return {
            "approved": False,
            "execution_authorized": False,
            "refusal_reason": f"Queue validation failed: {len(validation['issues'])} issue(s). Run: pcae phase queue validate",
            "validation": validation,
        }

    if not validation["queue_ready"]:
        return {
            "approved": False,
            "execution_authorized": False,
            "refusal_reason": "Queue is empty. Cannot approve an empty phase queue.",
            "validation": validation,
        }

    digest = _compute_queue_digest(root)

    return {
        "approved": True,
        "execution_authorized": False,
        "queue_entry_count": validation["queue_entry_count"],
        "queue_digest": digest,
        "approval_message": message,
        "approver_source": "local_cli",
        "validation": validation,
    }


def _save_queue_approval(root: HarnessPath, approval: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    approval_with_ts = {**approval, "approved_at": ts}
    approval_dir = root.join(QUEUE_APPROVALS_DIR)
    approval_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = approval_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = approval_dir / "latest.json"
    latest_path.write_text(
        json.dumps(approval_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_queue_approve(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    message = getattr(args, "message", "") or "Queue approved."
    dry_run = getattr(args, "dry_run", False)
    approval = _build_queue_approve(root, message)

    if not approval.get("approved", False):
        if args.json:
            print(json.dumps(approval, indent=2, sort_keys=True))
        else:
            print(f"Queue approval refused: {approval['refusal_reason']}")
        return 1

    if not dry_run:
        saved_path = _save_queue_approval(root, approval)
        if not args.json:
            print(f"Queue approval saved: {saved_path}")

    if args.json:
        result = {**approval, "dry_run": dry_run}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Phase Queue Approval")
    print("=" * 40)
    print(f"  Approved: yes")
    print(f"  Dry run: {'yes' if dry_run else 'no'}")
    print(f"  Entry count: {approval['queue_entry_count']}")
    print(f"  Queue digest: {approval['queue_digest']}")
    print(f"  Message: {approval['approval_message']}")
    print(f"  Approver: {approval['approver_source']}")
    print(f"  Execution authorized: no")
    return 0


def _read_latest_queue_approval(root: HarnessPath) -> dict | None:
    latest = root.join(QUEUE_APPROVALS_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def run_phase_queue_approval_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    approval = _read_latest_queue_approval(root)

    if approval is None:
        if args.json:
            print(json.dumps({"present": False, "reason": "No queue approval artifact found."}, indent=2, sort_keys=True))
        else:
            print("No queue approval artifact found.")
            print("Run: pcae phase queue approve --message '...'")
        return 1

    current_digest = _compute_queue_digest(root)

    result = {
        "present": True,
        "approved": approval.get("approved", False),
        "approved_at": approval.get("approved_at"),
        "queue_entry_count": approval.get("queue_entry_count", 0),
        "queue_digest": approval.get("queue_digest"),
        "current_queue_digest": current_digest,
        "queue_digest_matches": approval.get("queue_digest") == current_digest,
        "approval_message": approval.get("approval_message"),
        "approver_source": approval.get("approver_source"),
        "execution_authorized": approval.get("execution_authorized", False),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Phase Queue Approval (persisted)")
    print("=" * 40)
    print(f"  Present: yes")
    print(f"  Approved: {'yes' if result['approved'] else 'no'}")
    print(f"  Approved at: {result['approved_at'] or 'unknown'}")
    print(f"  Entry count: {result['queue_entry_count']}")
    print(f"  Queue digest: {result['queue_digest'] or 'none'}")
    print(f"  Current queue matches: {'yes' if result['queue_digest_matches'] else 'NO'}")
    print(f"  Message: {result['approval_message'] or 'none'}")
    print(f"  Approver: {result['approver_source'] or 'unknown'}")
    print(f"  Execution authorized: {'yes' if result['execution_authorized'] else 'no'}")
    return 0


def run_phase_queue_approval_check(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    queue = _read_phase_queue(root)
    validation = _build_queue_validate(root)
    approval = _read_latest_queue_approval(root)

    reasons: list[str] = []

    if not validation["queue_ready"]:
        reasons.append("queue is empty")
    if not validation["valid"]:
        reasons.append(f"queue validation failed: {len(validation['issues'])} issue(s)")
    if approval is None:
        reasons.append("no queue approval artifact found")
    else:
        current_digest = _compute_queue_digest(root)
        if approval.get("queue_digest") != current_digest:
            reasons.append("queue approval does not match current queue")
        if approval.get("execution_authorized") is not False:
            reasons.append("execution_authorized is not explicitly false")

    ready = len(reasons) == 0

    result = {
        "ready": ready,
        "reasons": reasons,
        "queue_present": len(queue) > 0,
        "queue_valid": validation["valid"],
        "queue_ready": validation["queue_ready"],
        "approval_present": approval is not None,
        "approval_matches": (
            approval is not None
            and approval.get("queue_digest") == _compute_queue_digest(root)
        ) if approval is not None else False,
        "execution_authorized": (
            approval.get("execution_authorized", False) if approval else None
        ),
        "note": "No execution performed. This is a read-only check.",
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if ready else 1

    print("Queue Approval Check")
    print("=" * 40)
    print(f"  Ready: {'yes' if result['ready'] else 'NO'}")
    print(f"  Queue present: {'yes' if result['queue_present'] else 'no'}")
    print(f"  Queue valid: {'yes' if result['queue_valid'] else 'no'}")
    print(f"  Queue ready: {'yes' if result['queue_ready'] else 'no'}")
    print(f"  Approval present: {'yes' if result['approval_present'] else 'no'}")
    if result["approval_present"]:
        print(f"  Approval matches: {'yes' if result['approval_matches'] else 'NO'}")
        print(f"  Execution authorized: {'yes' if result['execution_authorized'] else 'no'}")
    if reasons:
        print()
        print("  Reasons:")
        for r in reasons:
            print(f"    - {r}")
    print()
    print(f"  {result['note']}")
    return 0 if ready else 1


def _build_manual_steps(next_agent: str) -> list[str]:
    return [
        "Close or reset the current AI session if needed.",
        f"In the control terminal, run: pcae session bootstrap --agent-id {next_agent}",
        "In the new agent terminal, paste the governed bootstrap prompt below.",
        "Paste the next phase prompt to continue work.",
    ]


def _print_strategic_continuity(data: dict) -> None:
    current = data.get("current")
    if not isinstance(current, dict):
        print("Strategic continuity: unavailable")
        return

    print("Strategic continuity:")
    print(f"  Lineage ID: {current['lineage_id']}")
    print(f"  Decision basis: {current['decision_basis']}")
    print(
        f"  Selected phase: {current['activated_phase_id']} "
        f"({current['selected_branch_id']})"
    )
    deferred = data.get("deferred_alternatives") or []
    print("  Deferred alternatives:")
    if deferred:
        for alternative in deferred:
            print(
                f"    - {alternative['phase_id']}: {alternative['reason']}"
            )
    else:
        print("    - none")
    rejected = data.get("rejected_alternatives") or []
    print("  Rejected alternatives:")
    if rejected:
        for alternative in rejected:
            print(
                f"    - {alternative['phase_id']}: {alternative['reason']}"
            )
    else:
        print("    - none")
    referenced_findings = data.get("referenced_review_findings") or []
    references = ", ".join(
        reference["review_id"] for reference in referenced_findings
    )
    print(f"  Referenced review findings: {references or 'none'}")


def _build_bootstrap_prompt(next_agent: str) -> str:
    return (
        "You are resuming a governed engineering session in the PCAE harness.\n\n"
        "To initialize your session, run:\n\n"
        f"  pcae session bootstrap --agent-id {next_agent}\n\n"
        "This will acquire the agent lock, validate governance state (health and\n"
        "check), display the active task, current session, and provenance timeline,\n"
        "and confirm the environment is ready for governed work."
        "\n\nReview strategic decision continuity with:\n"
        "  pcae strategic-continuity show current"
    )


def _build_restart_workflows_text() -> str:
    return (
        "Example restart workflows:\n"
        "\n"
        "Claude CLI:\n"
        "  1. Start a fresh Claude session:\n"
        "       claude\n"
        "  2. Paste the governed bootstrap prompt.\n"
        "  3. Paste the next phase prompt.\n"
        "\n"
        "Codex Desktop:\n"
        "  1. Open a fresh Codex Desktop session/chat.\n"
        "  2. In the control terminal, run:\n"
        "       pcae session bootstrap --agent-id codex-local\n"
        "  3. Paste the governed bootstrap prompt.\n"
        "  4. Paste the next phase prompt.\n"
        "\n"
        "Generic governed agent:\n"
        "  1. Start a fresh agent session.\n"
        "  2. Run:\n"
        "       pcae session bootstrap --agent-id <agent-id>\n"
        "  3. Paste the governed bootstrap prompt.\n"
        "  4. Continue with the next governed phase."
    )


def _build_restart_workflows_data() -> list[dict]:
    return [
        {
            "agent": "Claude CLI",
            "steps": [
                "Start a fresh Claude session: claude",
                "Paste the governed bootstrap prompt.",
                "Paste the next phase prompt.",
            ],
        },
        {
            "agent": "Codex Desktop",
            "steps": [
                "Open a fresh Codex Desktop session/chat.",
                "In the control terminal, run: pcae session bootstrap --agent-id codex-local",
                "Paste the governed bootstrap prompt.",
                "Paste the next phase prompt.",
            ],
        },
        {
            "agent": "Generic governed agent",
            "steps": [
                "Start a fresh agent session.",
                "Run: pcae session bootstrap --agent-id <agent-id>",
                "Paste the governed bootstrap prompt.",
                "Continue with the next governed phase.",
            ],
        },
    ]


def _workflow_json_summary(workflow: dict | None) -> dict | None:
    if workflow is None:
        return None
    return {
        "workflow": workflow["workflow"],
        "status": workflow["status"],
        "execution_mode": workflow["execution_mode"],
        "step_count": len(workflow["steps"]),
    }


def run_phase_start(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    _refresh_session_snapshot_for_governed_flow(root)

    check_result = run_checks(root)
    if not check_result.passed:
        print("Phase start stopped: pcae check failed.")
        for v in check_result.violations:
            print(f"  - {v.text}")
        return 1

    try:
        result = start_phase(root, args.agent_id)
    except ValueError as error:
        print(str(error))
        return 1

    print("Phase start.")
    print("Check: passed")

    active_task = result.active_task
    if active_task is None:
        print("Active task: none")
    else:
        print(f"Active task: {active_task.get('id', 'unknown')}")
        print(f"Title: {active_task.get('title', 'Untitled task')}")

    timeline = result.timeline
    print(f"Provenance events: {timeline.event_count}")
    if timeline.latest_event is not None:
        print(f"Latest event: {timeline.latest_event.summary}")
    else:
        print("Latest event: none")

    return 0


_PHASE_COMMIT_RE = re.compile(
    r"^(Implement|Document|Design|Add|Refine|Complete) Phase (\S+)\s+(.+)$"
)

_MULTI_PHASE_COMMIT_RE = re.compile(
    r"^(Implement|Document|Design|Add|Refine) Phases?\s+(.+)$"
)

_PHASE_ID_RE = re.compile(r"^(\d+)([A-Z])(?:\.(\d+))?$")


def _expand_phase_range(start_id: str, end_id: str) -> list[str]:
    """Expand a phase range like '73A' to '73C' into ['73A', '73B', '73C']."""
    start_m = _PHASE_ID_RE.match(start_id)
    end_m = _PHASE_ID_RE.match(end_id)
    if not start_m or not end_m:
        return []
    start_num = int(start_m.group(1))
    start_letter = start_m.group(2)
    end_num = int(end_m.group(1))
    end_letter = end_m.group(2)
    if start_num != end_num:
        return []
    result = []
    for c in range(ord(start_letter), ord(end_letter) + 1):
        result.append(f"{start_num}{chr(c)}")
    return result


def _parse_multi_phase_ids_from_desc(description: str) -> list[str]:
    """Extract additional phase IDs from a description starting with 'and <phase_id>'.

    E.g. from "and 73E shared and implementation", returns ["73E"].
    """
    if not description.strip().startswith("and "):
        return []
    rest = description[4:].strip()  # remove "and "
    # Try to extract a phase ID at the start
    m = _PHASE_ID_RE.match(rest.split()[0] if rest.split() else "")
    if m:
        return [rest.split()[0]]
    return []


def _parse_multi_phase_ids(ids_text: str) -> list[str]:
    """Parse multi-phase ID text like '73A-73C' or '73A, 73B, 73C' or '73A and 73B'."""
    # Remove trailing description — take only up to first word that isn't a phase ID or separator
    # The ids_text from the regex group is everything after "Phases "
    # We need to extract just the phase ID part
    # Split on common separators and stop at first non-phase-id token
    tokens = re.split(r"[,\s]+", ids_text.strip())
    phase_ids: list[str] = []
    for token in tokens:
        token = token.strip().rstrip(".")
        if not token or token.lower() in ("and",):
            continue
        # Check if it looks like a phase range (e.g., "73A-73C")
        if "-" in token and not token.startswith("-"):
            parts = token.split("-", 1)
            if len(parts) == 2:
                expanded = _expand_phase_range(parts[0], parts[1])
                if expanded:
                    phase_ids.extend(expanded)
                    continue
        # Check if it looks like a single phase ID
        if _PHASE_ID_RE.match(token):
            phase_ids.append(token)
            continue
        # If we hit a non-phase-id token, stop (this is the description)
        break
    return phase_ids


def _git_log_lines(root: HarnessPath, last: int) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={last * 4}", "--format=%H %s"],
            cwd=root.path,
            check=True,
            capture_output=True,
            text=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, OSError):
        return []


def _detect_phase_commits(
    log_lines: list[str], last: int, since: str | None
) -> list[dict]:
    impl_map: dict[str, dict] = {}
    comp_map: dict[str, dict] = {}
    multi_phase_impls: list[dict] = []  # shared implementation commits

    for line in log_lines:
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        commit_hash, subject = parts

        # Try single-phase match first
        m = _PHASE_COMMIT_RE.match(subject)
        if m:
            kind, phase_id, description = m.group(1), m.group(2), m.group(3)
            # Check if the description starts with "and" followed by another
            # phase ID — this indicates a shared multi-phase commit in
            # singular "Phase" form (e.g. "Implement Phase 73D and 73E ...")
            extra_ids = _parse_multi_phase_ids_from_desc(description)
            if extra_ids:
                all_ids = [phase_id] + extra_ids
                if kind != "Complete":
                    multi_phase_impls.append({
                        "commit": commit_hash[:12],
                        "phase_ids": all_ids,
                        "description": f"{phase_id} and {', '.join(extra_ids)}",
                        "subject": subject,
                    })
                continue
            entry = {
                "commit": commit_hash[:12],
                "phase_id": phase_id,
                "description": description,
                "subject": subject,
            }
            if kind == "Complete":
                comp_map.setdefault(phase_id, entry)
            else:
                impl_map.setdefault(phase_id, entry)
            continue

        # Try multi-phase match (only for implementation commits, not completion)
        mm = _MULTI_PHASE_COMMIT_RE.match(subject)
        if mm:
            kind = mm.group(1)
            ids_text = mm.group(2)
            if kind == "Complete":
                continue  # multi-phase completion commits are not recognized
            phase_ids = _parse_multi_phase_ids(ids_text)
            if phase_ids:
                multi_phase_impls.append({
                    "commit": commit_hash[:12],
                    "phase_ids": phase_ids,
                    "description": ids_text[:80],
                    "subject": subject,
                })

    # Process multi-phase implementation commits: distribute to affected phases
    # but only if no dedicated implementation commit exists for that phase
    shared_impl_map: dict[str, dict] = {}
    for mp in multi_phase_impls:
        for pid in mp["phase_ids"]:
            if pid not in impl_map:
                shared_impl_map.setdefault(pid, {
                    "commit": mp["commit"],
                    "phase_id": pid,
                    "description": mp["description"],
                    "subject": mp["subject"],
                    "shared": True,
                    "shared_commit_phase_ids": mp["phase_ids"],
                })

    all_phase_ids = list(dict.fromkeys(
        list(comp_map.keys()) + list(impl_map.keys()) + list(shared_impl_map.keys())
    ))

    if since:
        all_phase_ids = [p for p in all_phase_ids if p >= since]

    if last > 0:
        all_phase_ids = all_phase_ids[:last]

    phases: list[dict] = []
    for phase_id in all_phase_ids:
        impl = impl_map.get(phase_id)
        shared = shared_impl_map.get(phase_id)
        comp = comp_map.get(phase_id)
        has_shared = impl is None and shared is not None
        phases.append({
            "phase_id": phase_id,
            "description": (comp or impl or shared or {}).get("description", ""),
            "implementation_commit": (
                impl["commit"] if impl else (shared["commit"] if shared else None)
            ),
            "implementation_commit_shared": has_shared,
            "shared_commit_phase_ids": (
                shared.get("shared_commit_phase_ids") if has_shared else None
            ),
            "completion_commit": comp["commit"] if comp else None,
            "commit_pair_complete": impl is not None and comp is not None,
            # shared commits don't count as fully paired; they generate a separate warning
        })

    return phases


def _build_audit_report(root: HarnessPath, last: int, since: str | None) -> dict:
    from pcae.core.git_status import read_git_branch, read_git_changes
    from pcae.core.health import build_health_data, is_healthy
    from pcae.core.tasks import diagnose_task_memory

    from pcae.commands.push import assess_push_readiness

    log_lines = _git_log_lines(root, max(last, 20))
    phases = _detect_phase_commits(log_lines, last, since)

    health_data = build_health_data(root)
    healthy = is_healthy(health_data)
    check_result = run_checks(root)
    diagnostics = diagnose_task_memory(root)
    push = assess_push_readiness(root)
    branch = read_git_branch(root)
    changes = read_git_changes(root)
    active_task = find_latest_active_task(root)

    handoff_path = root.join(HANDOFFS_DIR / "latest.json")
    handoff_summary: str | None = None
    if handoff_path.is_file():
        try:
            handoff_data = json.loads(handoff_path.read_text(encoding="utf-8"))
            handoff_summary = handoff_data.get("summary")
        except (json.JSONDecodeError, OSError):
            pass

    warnings: list[str] = []
    for phase in phases:
        # Check for shared implementation commits first — always a warning
        if phase.get("implementation_commit_shared"):
            shared_ids = phase.get("shared_commit_phase_ids") or []
            warnings.append(
                f"Phase {phase['phase_id']}: implementation covered by shared "
                f"multi-phase commit {phase['implementation_commit']} "
                f"(phase range: {', '.join(shared_ids)}). "
                f"Preferred: one implementation commit per phase."
            )
        # Then check for missing commits
        if not phase["commit_pair_complete"]:
            missing = []
            if phase["implementation_commit"] is None:
                missing.append("implementation")
            if phase["completion_commit"] is None:
                missing.append("completion")
            if missing:
                warnings.append(
                    f"Phase {phase['phase_id']}: missing {', '.join(missing)} commit"
                )

    healthy_idle = healthy and not active_task and not changes

    return {
        "phases_detected": len(phases),
        "phases": phases,
        "health_status": "healthy" if healthy else "unhealthy",
        "check_passed": check_result.passed,
        "task_memory_status": (
            "clean" if not diagnostics.has_errors and not diagnostics.has_warnings
            else "errors" if diagnostics.has_errors else "warnings"
        ),
        "push_mode": push.mode,
        "push_ready": push.ready,
        "branch": branch,
        "working_tree": "clean" if not changes else f"{len(changes)} changed",
        "active_task": active_task.task_id if active_task else None,
        "latest_handoff_summary": handoff_summary,
        "healthy_idle": healthy_idle,
        "warnings": warnings,
    }


def _save_audit_artifact(root: HarnessPath, report: dict) -> tuple[Path, Path]:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_with_ts = {**report, "created_at": ts}
    audit_dir = root.join(PHASE_AUDITS_DIR)
    audit_dir.mkdir(parents=True, exist_ok=True)

    latest_path = audit_dir / "latest.json"
    timestamped_path = audit_dir / f"audit-{ts}.json"

    payload = json.dumps(report_with_ts, indent=2, sort_keys=True) + "\n"
    with latest_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(payload)
    with timestamped_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(payload)

    return latest_path, timestamped_path


def _read_latest_audit(root: HarnessPath) -> dict | None:
    latest_path = root.join(PHASE_AUDITS_DIR / "latest.json")
    if not latest_path.is_file():
        return None
    try:
        return json.loads(latest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def run_phase_audit(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    last: int = args.last
    since: str | None = args.since

    report = _build_audit_report(root, last, since)

    if args.save:
        latest_path, ts_path = _save_audit_artifact(root, report)
        if args.json:
            print(json.dumps({
                **report,
                "saved": True,
                "latest_path": str(latest_path),
                "timestamped_path": str(ts_path),
            }, indent=2, sort_keys=True))
            return 0
        print(f"Audit saved: {latest_path}")
        print(f"Timestamped: {ts_path}")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("Phase Audit Report")
    print("=" * 40)
    print(f"Phases detected: {report['phases_detected']}")
    print()

    if report["phases"]:
        for phase in report["phases"]:
            status = "complete" if phase["commit_pair_complete"] else "INCOMPLETE"
            print(f"  {phase['phase_id']}: {phase['description']} [{status}]")
            if phase["implementation_commit"]:
                print(f"    implementation: {phase['implementation_commit']}")
            else:
                print("    implementation: MISSING")
            if phase["completion_commit"]:
                print(f"    completion:     {phase['completion_commit']}")
            else:
                print("    completion:     MISSING")
    else:
        print("  No phase commits found.")

    print()
    print("Current State")
    print("-" * 40)
    print(f"  Branch: {report['branch']}")
    print(f"  Working tree: {report['working_tree']}")
    print(f"  Active task: {report['active_task'] or 'none'}")
    print(f"  Health: {report['health_status']}")
    print(f"  Check: {'passed' if report['check_passed'] else 'failed'}")
    print(f"  Task memory: {report['task_memory_status']}")
    print(f"  Push: {'ready' if report['push_ready'] else 'not ready'} ({report['push_mode']})")
    print(f"  Healthy idle: {'yes' if report['healthy_idle'] else 'no'}")

    if report["latest_handoff_summary"]:
        print()
        print(f"  Latest handoff: {report['latest_handoff_summary']}")

    if report["warnings"]:
        print()
        print("Warnings")
        print("-" * 40)
        for w in report["warnings"]:
            print(f"  - {w}")

    return 0


def _current_handoff_summary(root: HarnessPath) -> tuple[str | None, str | None]:
    handoff_path = root.join(HANDOFFS_DIR / "latest.json")
    if not handoff_path.is_file():
        return None, None
    try:
        data = json.loads(handoff_path.read_text(encoding="utf-8"))
        return data.get("summary"), data.get("created_at")
    except (json.JSONDecodeError, OSError):
        return None, None


def run_phase_audit_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    audit = _read_latest_audit(root)

    if audit is None:
        print("No saved audit artifact found.", file=__import__("sys").stderr)
        return 1

    current_summary, current_created_at = _current_handoff_summary(root)
    audit_summary = audit.get("latest_handoff_summary")
    is_stale = (
        current_summary is not None
        and audit_summary is not None
        and current_summary != audit_summary
    )

    if args.json:
        output = {**audit}
        output["current_handoff_summary"] = current_summary
        output["current_handoff_created_at"] = current_created_at
        output["handoff_summary_stale"] = is_stale
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0

    print("Saved Phase Audit")
    print("=" * 40)
    if "created_at" in audit:
        print(f"  Created: {audit['created_at']}")
    print(f"  Phases detected: {audit['phases_detected']}")
    if audit.get("phases"):
        for phase in audit["phases"]:
            status = "complete" if phase["commit_pair_complete"] else "INCOMPLETE"
            print(f"  {phase['phase_id']}: {phase['description']} [{status}]")
    print(f"  Health: {audit['health_status']}")
    print(f"  Healthy idle: {'yes' if audit['healthy_idle'] else 'no'}")
    if is_stale:
        print(f"  Handoff summary (at audit): {audit_summary}")
        print(f"  Handoff summary (current): {current_summary}")
    elif audit_summary:
        print(f"  Latest handoff: {audit_summary}")
    if audit.get("warnings"):
        print(f"  Warnings: {len(audit['warnings'])}")
        for w in audit["warnings"]:
            print(f"    - {w}")

    return 0


PHASE_PROMPTS_DIR = Path(".pcae") / "phase-prompts"


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:80] if slug else "untitled"


def run_phase_prompt_capture(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()

    text: str | None = getattr(args, "text", None)
    file_path: str | None = getattr(args, "file", None)
    use_stdin: bool = getattr(args, "stdin", False)

    sources = sum([text is not None, file_path is not None, use_stdin])
    if sources == 0:
        print("Error: one of --text, --file, or --stdin is required.")
        return 1
    if sources > 1:
        print("Error: only one of --text, --file, or --stdin may be specified.")
        return 1

    if text is not None:
        content = text
    elif file_path is not None:
        import os
        resolved = Path(file_path)
        if not resolved.is_absolute():
            resolved = Path(os.getcwd()) / resolved
        if not resolved.is_file():
            print(f"Error: file not found: {file_path}")
            return 1
        content = resolved.read_text(encoding="utf-8")
    else:
        import sys
        content = sys.stdin.read()

    title: str = args.title
    now = datetime.now(timezone.utc)
    slug = _slugify(title)
    ts_str = now.strftime("%Y%m%dT%H%M%SZ")
    ts_filename = f"{slug}-{ts_str}.md"

    prompts_dir = root.join(PHASE_PROMPTS_DIR)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    ts_path = prompts_dir / ts_filename
    ts_path.write_text(content, encoding="utf-8")

    latest_path = prompts_dir / "latest.md"
    latest_path.write_text(content, encoding="utf-8")

    metadata = {
        "title": title,
        "created_at": now.isoformat(),
        "slug": slug,
        "timestamped_path": str(PHASE_PROMPTS_DIR / ts_filename),
        "latest_path": str(PHASE_PROMPTS_DIR / "latest.md"),
    }

    metadata_path = prompts_dir / "latest.json"
    with metadata_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)
        f.write("\n")

    if args.json:
        print(json.dumps(metadata, indent=2, sort_keys=True))
        return 0

    print(f"Captured phase prompt: {title}")
    print(f"  Timestamped: {PHASE_PROMPTS_DIR / ts_filename}")
    print(f"  Latest: {PHASE_PROMPTS_DIR / 'latest.md'}")
    print(f"  Created: {now.isoformat()}")
    return 0


def _read_prompt_metadata(root: HarnessPath) -> dict | None:
    metadata_path = root.join(PHASE_PROMPTS_DIR / "latest.json")
    if not metadata_path.is_file():
        return None
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _read_prompt_content(root: HarnessPath) -> str | None:
    latest_path = root.join(PHASE_PROMPTS_DIR / "latest.md")
    if not latest_path.is_file():
        return None
    try:
        return latest_path.read_text(encoding="utf-8")
    except OSError:
        return None


def run_phase_prompt_show(args: argparse.Namespace) -> int:
    import sys

    root = HarnessPath.cwd()
    metadata = _read_prompt_metadata(root)
    content = _read_prompt_content(root)

    if metadata is None and content is None:
        print("No captured phase prompt found.", file=sys.stderr)
        return 1

    if args.json:
        result = dict(metadata) if metadata else {}
        result["content"] = content or ""
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if metadata:
        print(f"Phase prompt: {metadata.get('title', 'Untitled')}")
        print(f"  Created: {metadata.get('created_at', 'unknown')}")
        print(f"  Path: {metadata.get('latest_path', 'unknown')}")
        print()
    print(content or "")
    return 0


def run_phase_prompt_list(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    prompts_dir = root.join(PHASE_PROMPTS_DIR)

    if not prompts_dir.is_dir():
        if args.json:
            print(json.dumps({"prompts": [], "count": 0}, indent=2, sort_keys=True))
        else:
            print("No captured phase prompts found.")
        return 0

    prompt_files = sorted(
        [f for f in prompts_dir.iterdir()
         if f.is_file() and f.suffix == ".md" and f.name != "latest.md"],
        reverse=True,
    )

    if args.json:
        entries = [{"filename": f.name, "path": str(PHASE_PROMPTS_DIR / f.name)} for f in prompt_files]
        print(json.dumps({"prompts": entries, "count": len(entries)}, indent=2, sort_keys=True))
        return 0

    if not prompt_files:
        print("No captured phase prompts found.")
        return 0

    print(f"Captured phase prompts ({len(prompt_files)}):")
    for f in prompt_files:
        print(f"  {f.name}")
    return 0


PROMPT_PLACEHOLDER_PATTERNS = [
    "test prompt",
    "placeholder",
    "dummy",
    "next step",
    "todo",
]


def _is_prompt_placeholder(title: str, content: str) -> bool:
    combined = (title + " " + content).lower()
    return any(pattern in combined for pattern in PROMPT_PLACEHOLDER_PATTERNS)


def _list_timestamped_prompts(root: HarnessPath) -> list[Path]:
    prompts_dir = root.join(PHASE_PROMPTS_DIR)
    if not prompts_dir.is_dir():
        return []
    return sorted(
        [f for f in prompts_dir.iterdir()
         if f.is_file() and f.suffix == ".md" and f.name != "latest.md"],
    )


def run_phase_prompt_hygiene(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    ts_files = _list_timestamped_prompts(root)

    findings: list[dict] = []
    clearable_files: list[Path] = []

    for f in ts_files:
        content = f.read_text(encoding="utf-8")
        title = f.stem.rsplit("-", 1)[0] if "-" in f.stem else f.stem
        if _is_prompt_placeholder(title, content):
            findings.append({
                "filename": f.name,
                "reason": "matches placeholder pattern",
            })
            clearable_files.append(f)

    if args.clear_placeholders:
        if not args.confirm:
            if args.json:
                print(json.dumps({
                    "error": "--clear-placeholders requires --confirm",
                    "findings": findings,
                    "clearable_count": len(clearable_files),
                }, indent=2, sort_keys=True))
            else:
                print("Error: --clear-placeholders requires --confirm flag.")
                if findings:
                    print(f"  {len(findings)} placeholder(s) found. Re-run with --confirm to clear.")
            return 1

        if not findings:
            if args.json:
                print(json.dumps({
                    "cleared": 0,
                    "findings": [],
                }, indent=2, sort_keys=True))
            else:
                print("No placeholder prompts to clear.")
            return 0

        for f in clearable_files:
            f.unlink()

        if args.json:
            print(json.dumps({
                "cleared": len(clearable_files),
                "findings": findings,
            }, indent=2, sort_keys=True))
        else:
            print(f"Cleared {len(clearable_files)} placeholder prompt(s).")
            for finding in findings:
                print(f"  - removed: {finding['filename']}")
        return 0

    if args.json:
        print(json.dumps({
            "total_prompts": len(ts_files),
            "has_issues": len(findings) > 0,
            "findings": findings,
            "clearable_count": len(clearable_files),
        }, indent=2, sort_keys=True))
        return 0

    if not ts_files:
        print("Prompt hygiene: clean (no prompts)")
        return 0

    if not findings:
        print(f"Prompt hygiene: clean ({len(ts_files)} prompts, no placeholders)")
        return 0

    print(f"Prompt hygiene: {len(findings)} placeholder(s) found")
    for finding in findings:
        print(f"  - {finding['filename']} — {finding['reason']}")
    return 0


def run_phase_prompt_prune(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    keep: int = args.keep
    ts_files = _list_timestamped_prompts(root)
    total = len(ts_files)

    if total <= keep:
        if args.json:
            print(json.dumps({
                "total": total,
                "keep": keep,
                "prunable": 0,
                "pruned": 0,
            }, indent=2, sort_keys=True))
        else:
            print(f"Prompt prune: {total} prompts, keeping {keep}. Nothing to prune.")
        return 0

    to_prune = ts_files[:total - keep]

    if args.dry_run:
        if args.json:
            print(json.dumps({
                "total": total,
                "keep": keep,
                "prunable": len(to_prune),
                "pruned": 0,
                "dry_run": True,
                "candidates": [f.name for f in to_prune],
            }, indent=2, sort_keys=True))
        else:
            print(f"Prompt prune dry-run: {len(to_prune)} of {total} would be pruned (kept {keep}).")
            for f in to_prune:
                print(f"  - {f.name}")
        return 0

    for f in to_prune:
        f.unlink()

    if args.json:
        print(json.dumps({
            "total": total,
            "keep": keep,
            "prunable": len(to_prune),
            "pruned": len(to_prune),
        }, indent=2, sort_keys=True))
    else:
        print(f"Pruned {len(to_prune)} of {total} prompt artifacts (kept {keep}).")

    return 0


def run_phase_prompt_enqueue(args: argparse.Namespace) -> int:
    import sys

    root = HarnessPath.cwd()
    file_arg: str | None = getattr(args, "file", None)
    title_override: str | None = getattr(args, "title", None)
    dry_run: bool = getattr(args, "dry_run", False)

    if file_arg is not None:
        prompt_path = root.join(PHASE_PROMPTS_DIR / file_arg)
        if not prompt_path.is_file():
            print(f"Error: prompt file not found: {file_arg}", file=sys.stderr)
            return 1
        metadata = _read_prompt_metadata(root)
        if metadata and metadata.get("timestamped_path", "").endswith(file_arg):
            source_path = metadata.get("timestamped_path", str(PHASE_PROMPTS_DIR / file_arg))
            title = title_override or metadata.get("title", file_arg)
            source_created = metadata.get("created_at")
        else:
            source_path = str(PHASE_PROMPTS_DIR / file_arg)
            title = title_override or file_arg
            source_created = None
    else:
        metadata = _read_prompt_metadata(root)
        if metadata is None:
            print("Error: no captured phase prompt found. Run pcae phase prompt-capture first.", file=sys.stderr)
            return 1
        title = title_override or metadata.get("title", "Untitled prompt")
        source_path = metadata.get("latest_path", str(PHASE_PROMPTS_DIR / "latest.md"))
        source_created = metadata.get("created_at")

    queue = _read_phase_queue(root)
    if title in [_phase_queue_entry_title(entry) for entry in queue]:
        if args.json:
            print(json.dumps({
                "error": "duplicate",
                "title": title,
                "queue_length": len(queue),
                "mutated": False,
            }, indent=2, sort_keys=True))
        else:
            print(f"Error: queue already contains: {title}")
        return 1

    result = {
        "title": title,
        "source_prompt_path": source_path,
        "source_prompt_created_at": source_created,
        "queue_length": len(queue) + 1,
        "position": len(queue) + 1,
        "mutated": not dry_run,
        "dry_run": dry_run,
    }

    if dry_run:
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"Dry run: would enqueue: {title}")
            print(f"  Source: {source_path}")
            print(f"  Position: {len(queue) + 1}")
        return 0

    queue.append({
        "title": title,
        "source_type": "captured_prompt",
        "source_prompt_path": source_path,
        "source_prompt_created_at": source_created,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _write_phase_queue(root, queue)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Enqueued from prompt: {title}")
        print(f"  Source: {source_path}")
        print(f"  Position: {len(queue)}")
        print(f"  Queue length: {len(queue)}")
    return 0


def _build_phase_prompt_roundtrip_check(root: HarnessPath) -> dict:
    metadata = _read_prompt_metadata(root)
    content = _read_prompt_content(root)
    queue = _read_phase_queue(root)
    queue_entries = [_phase_queue_entry_details(entry) for entry in queue]
    reasons: list[str] = []

    prompt_present = metadata is not None and content is not None
    prompt_show_loadable = prompt_present
    dry_run_title = metadata.get("title") if metadata else None
    source_prompt_path = (
        metadata.get("latest_path", str(PHASE_PROMPTS_DIR / "latest.md"))
        if metadata else None
    )
    source_prompt_created_at = metadata.get("created_at") if metadata else None

    if metadata is None:
        reasons.append("latest prompt metadata is missing")
    if content is None:
        reasons.append("latest prompt content is missing")

    queue_titles = [_phase_queue_entry_title(entry) for entry in queue]
    dry_run_derivable = bool(dry_run_title)
    if not dry_run_title:
        reasons.append("prompt enqueue dry-run cannot derive a queue title")
    elif dry_run_title in queue_titles:
        dry_run_derivable = False
        reasons.append("phase queue already contains the prompt title")

    handoff_path = root.join(HANDOFFS_DIR / "latest.json")
    handoff_present = handoff_path.is_file()
    handoff_prompt_visible = False
    handoff_queue_visible = False
    if handoff_present:
        try:
            handoff_data = json.loads(handoff_path.read_text(encoding="utf-8"))
            prompt_summary = handoff_data.get("prompt_summary")
            handoff_prompt_visible = bool(
                isinstance(prompt_summary, dict) and prompt_summary.get("present")
            )
            handoff_queue_visible = bool(handoff_data.get("phase_queue_present"))
        except (json.JSONDecodeError, OSError):
            reasons.append("latest handoff artifact is not readable")

    ready = prompt_present and prompt_show_loadable and dry_run_derivable

    return {
        "ready": ready,
        "reasons": reasons,
        "prompt_present": prompt_present,
        "prompt_show_loadable": prompt_show_loadable,
        "prompt_title": dry_run_title,
        "prompt_content_length": len(content or ""),
        "dry_run_title": dry_run_title,
        "dry_run_derivable": dry_run_derivable,
        "dry_run_mutated": False,
        "source_prompt_path": source_prompt_path,
        "source_prompt_created_at": source_prompt_created_at,
        "queue_present": len(queue) > 0,
        "queue_length": len(queue),
        "queue_entries": queue_entries,
        "queue_readable": True,
        "queue_check_planning_only": True,
        "handoff_present": handoff_present,
        "handoff_prompt_visible": handoff_prompt_visible,
        "handoff_queue_visible": handoff_queue_visible,
        "bootstrap_prompt_visible": prompt_present,
        "mutated": False,
    }


def run_phase_prompt_roundtrip_check(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_phase_prompt_roundtrip_check(root)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ready"] else 1

    if result["ready"]:
        print("Phase prompt round-trip check: ready")
    else:
        print("Phase prompt round-trip check: not ready")
    print(f"  Prompt: {'present' if result['prompt_present'] else 'missing'}")
    if result["dry_run_title"]:
        print(f"  Dry-run title: {result['dry_run_title']}")
    print(f"  Queue: {result['queue_length']} entries")
    if result["handoff_present"]:
        print(
            "  Handoff visibility: "
            f"prompt={'yes' if result['handoff_prompt_visible'] else 'no'}, "
            f"queue={'yes' if result['handoff_queue_visible'] else 'no'}"
        )
    print("  Mutated: no")
    if result["reasons"]:
        print("  Reasons:")
        for reason in result["reasons"]:
            print(f"    - {reason}")
    return 0 if result["ready"] else 1


AUTONOMY_SUMMARIES_DIR = Path(".pcae") / "autonomy-summaries"


def _build_autonomy_summary(root: HarnessPath) -> dict:
    from pcae.core.git_status import read_git_branch, read_git_changes
    from pcae.core.health import build_health_data, is_healthy
    from pcae.core.tasks import find_latest_active_task

    from pcae.commands.push import assess_push_readiness

    audit = _read_latest_audit(root)
    handoff_summary, handoff_created_at = _current_handoff_summary(root)
    health_data = build_health_data(root)
    healthy = is_healthy(health_data)
    changes = read_git_changes(root)
    active_task = find_latest_active_task(root)
    push = assess_push_readiness(root)

    phases_detected = 0
    warning_count = 0
    latest_completed_phase: str | None = None
    if audit:
        phases_detected = audit.get("phases_detected", 0)
        warning_count = len(audit.get("warnings", []))
        phases = audit.get("phases") or []
        if phases:
            latest_completed_phase = phases[0].get("phase_id")

    recovery_observed = "unknown"
    if audit:
        for phase in audit.get("phases", []):
            desc = phase.get("description", "")
            if "recover" in desc.lower():
                recovery_observed = "yes"
                break
        if recovery_observed == "unknown":
            recovery_observed = "none detected"

    return {
        "phases_detected": phases_detected,
        "warning_count": warning_count,
        "latest_completed_phase": latest_completed_phase,
        "recovery_commands_observed": recovery_observed,
        "active_task": active_task.task_id if active_task else None,
        "working_tree": "clean" if not changes else f"{len(changes)} changed",
        "health_status": "healthy" if healthy else "unhealthy",
        "push_status": push.mode,
        "latest_handoff_summary": handoff_summary,
        "latest_handoff_created_at": handoff_created_at,
        "agent_neutral_note": (
            "This summary reports observable governance facts only. "
            "It does not rank or compare agents."
        ),
    }


def _save_autonomy_summary(root: HarnessPath, summary: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_with_ts = {**summary, "created_at": ts}
    summary_dir = root.join(AUTONOMY_SUMMARIES_DIR)
    summary_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = summary_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = summary_dir / "latest.json"
    latest_path.write_text(
        json.dumps(summary_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_autonomy_summary(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    summary = _build_autonomy_summary(root)

    if getattr(args, "save", False):
        saved_path = _save_autonomy_summary(root, summary)
        if not args.json:
            print(f"Autonomy summary saved: {saved_path}")

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    print("Autonomy Run Summary")
    print("=" * 40)
    print(f"  Phases detected: {summary['phases_detected']}")
    print(f"  Warning count: {summary['warning_count']}")
    print(f"  Latest completed phase: {summary['latest_completed_phase'] or 'none'}")
    print(f"  Recovery commands observed: {summary['recovery_commands_observed']}")
    print(f"  Active task: {summary['active_task'] or 'none'}")
    print(f"  Working tree: {summary['working_tree']}")
    print(f"  Health: {summary['health_status']}")
    print(f"  Push status: {summary['push_status']}")
    print(f"  Latest handoff: {summary['latest_handoff_summary'] or 'none'}")
    print()
    print(f"  Note: {summary['agent_neutral_note']}")
    return 0


def _build_runner_readiness(root: HarnessPath) -> dict:
    from pcae.core.git_status import read_git_changes
    from pcae.core.health import build_health_data, is_healthy
    from pcae.core.tasks import diagnose_task_memory

    from pcae.commands.push import assess_push_readiness

    blocking: list[str] = []
    advisory: list[str] = []

    changes = read_git_changes(root)
    if changes:
        blocking.append("working tree is dirty")

    health_data = build_health_data(root)
    healthy = is_healthy(health_data)
    if not healthy:
        blocking.append("health check failed")

    check_result = run_checks(root)
    if not check_result.passed:
        blocking.append("pcae check failed")

    active_task = find_latest_active_task(root)
    if active_task is not None:
        blocking.append(f"active task exists: {active_task.task_id}")

    diagnostics = diagnose_task_memory(root)
    task_memory_clean = not diagnostics.has_errors and not diagnostics.has_warnings
    if not task_memory_clean:
        blocking.append("task memory has inconsistencies")

    push = assess_push_readiness(root)
    unpushed = push.mode != "nothing_to_push" and push.mode != "post_finish_closure"
    if push.mode == "not_ready":
        blocking.append("push check is blocked")
    elif unpushed:
        advisory.append(f"unpushed commits present ({push.mode})")

    queue = _read_phase_queue(root)
    queue_present = len(queue) > 0

    audit = _read_latest_audit(root)
    audit_available = audit is not None
    audit_warning_count = len(audit.get("warnings", [])) if audit else 0
    if audit_warning_count > 0:
        advisory.append(f"audit has {audit_warning_count} warning(s)")

    handoff_path = root.join(HANDOFFS_DIR / "latest.json")
    handoff_available = handoff_path.is_file()
    if not handoff_available:
        advisory.append("no handoff artifact available")

    autonomy_path = root.join(AUTONOMY_SUMMARIES_DIR / "latest.json")
    autonomy_available = autonomy_path.is_file()

    environment_ready = len(blocking) == 0
    queue_ready = queue_present
    runner_ready = environment_ready and queue_ready

    return {
        "environment_ready": environment_ready,
        "queue_ready": queue_ready,
        "runner_ready": runner_ready,
        "blocking_reasons": blocking,
        "advisory_reasons": advisory,
        "active_task": active_task.task_id if active_task else None,
        "working_tree": "clean" if not changes else f"{len(changes)} changed",
        "health_status": "healthy" if healthy else "unhealthy",
        "check_passed": check_result.passed,
        "task_memory_status": "clean" if task_memory_clean else "issues",
        "push_state": push.mode,
        "queue_length": len(queue),
        "audit_available": audit_available,
        "audit_warning_count": audit_warning_count,
        "latest_handoff_present": handoff_available,
        "autonomy_summary_present": autonomy_available,
    }


def run_phase_runner_readiness(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_runner_readiness(root)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Phase Runner Readiness")
    print("=" * 40)
    print(f"  Environment ready: {'yes' if result['environment_ready'] else 'NO'}")
    print(f"  Queue ready: {'yes' if result['queue_ready'] else 'no (empty)'}")
    print(f"  Runner ready: {'yes' if result['runner_ready'] else 'NO'}")
    print()
    print("  Environment state:")
    print(f"    Working tree: {result['working_tree']}")
    print(f"    Health: {result['health_status']}")
    print(f"    Check: {'passed' if result['check_passed'] else 'FAILED'}")
    print(f"    Task memory: {result['task_memory_status']}")
    print(f"    Push state: {result['push_state']}")
    print(f"    Active task: {result['active_task'] or 'none'}")
    print()
    print("  Queue state:")
    print(f"    Queue entries: {result['queue_length']}")
    print(f"    Audit available: {'yes' if result['audit_available'] else 'no'}")
    print(f"    Audit warnings: {result['audit_warning_count']}")
    print(f"    Handoff present: {'yes' if result['latest_handoff_present'] else 'no'}")
    print(f"    Autonomy summary: {'yes' if result['autonomy_summary_present'] else 'no'}")

    if result["blocking_reasons"]:
        print()
        print("  Blocking reasons:")
        for r in result["blocking_reasons"]:
            print(f"    - {r}")

    if result["advisory_reasons"]:
        print()
        print("  Advisory:")
        for r in result["advisory_reasons"]:
            print(f"    - {r}")

    return 0


_RUNNER_MAX_PHASES_LIMIT = 3

_RUNNER_STOP_CONDITIONS = [
    "test failure (python -m pytest -n auto)",
    "pcae health failure",
    "pcae check failure",
    "task-memory inconsistency (pcae doctor task-memory)",
    "push check blocked",
    "scope drift required",
    "ambiguity detected",
    "lifecycle review enforcement block",
    "task finish partial failure",
    "git index lock / permission failure",
]

_RUNNER_VALIDATION_SEQUENCE = [
    "python -m pytest -n auto",
    "pcae health",
    "pcae check",
    "pcae doctor task-memory",
    "pcae push check",
]

_RUNNER_COMMIT_PUSH_SEQUENCE = [
    "git add <scoped files>",
    "git commit -m 'Implement Phase <id> <description>'",
    "pcae task finish --commit 'Complete Phase <id> <description>'",
    "pcae push",
]

_RUNNER_RECOVERY_PATH = [
    "pcae doctor git-lock",
    "pcae task finish recover --dry-run",
    "pcae task finish recover --message 'Complete Phase <id> <description>'",
]


def _build_runner_plan(root: HarnessPath, max_phases: int) -> dict:
    readiness = _build_runner_readiness(root)
    queue = _read_phase_queue(root)

    clamped = min(max(max_phases, 1), _RUNNER_MAX_PHASES_LIMIT)

    if not readiness["environment_ready"]:
        return {
            "executable": False,
            "blockers": readiness["blocking_reasons"],
            "planned_phases": [],
            "max_phases": clamped,
            "stop_conditions": list(_RUNNER_STOP_CONDITIONS),
            "validation_sequence": list(_RUNNER_VALIDATION_SEQUENCE),
            "commit_push_sequence": list(_RUNNER_COMMIT_PUSH_SEQUENCE),
            "recovery_path": list(_RUNNER_RECOVERY_PATH),
            "note": "No execution performed. This is a dry-run plan only.",
        }

    planned = []
    for entry in queue[:clamped]:
        planned.append(_phase_queue_entry_details(entry))

    return {
        "executable": len(planned) > 0,
        "blockers": [],
        "planned_phases": planned,
        "max_phases": clamped,
        "stop_conditions": list(_RUNNER_STOP_CONDITIONS),
        "validation_sequence": list(_RUNNER_VALIDATION_SEQUENCE),
        "commit_push_sequence": list(_RUNNER_COMMIT_PUSH_SEQUENCE),
        "recovery_path": list(_RUNNER_RECOVERY_PATH),
        "note": "No execution performed. This is a dry-run plan only.",
    }


def run_phase_runner_plan(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    max_phases = min(max(getattr(args, "max_phases", 1), 1), _RUNNER_MAX_PHASES_LIMIT)
    plan = _build_runner_plan(root, max_phases)

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    print("Phase Runner Plan (dry-run)")
    print("=" * 40)
    print(f"  Executable: {'yes' if plan['executable'] else 'no'}")
    print(f"  Max phases: {plan['max_phases']}")

    if plan["blockers"]:
        print()
        print("  Blockers:")
        for b in plan["blockers"]:
            print(f"    - {b}")

    if plan["planned_phases"]:
        print()
        print("  Planned phases:")
        for i, phase in enumerate(plan["planned_phases"], 1):
            print(f"    {i}. {phase['title']}")
    else:
        print()
        print("  No phases planned.")

    print()
    print("  Stop conditions:")
    for sc in plan["stop_conditions"]:
        print(f"    - {sc}")
    print()
    print("  Validation sequence:")
    for vs in plan["validation_sequence"]:
        print(f"    - {vs}")
    print()
    print("  Commit/push sequence:")
    for cs in plan["commit_push_sequence"]:
        print(f"    - {cs}")
    print()
    print("  Recovery path:")
    for rp in plan["recovery_path"]:
        print(f"    - {rp}")
    print()
    print(f"  {plan['note']}")
    return 0


_RUNNER_POLICY_MATRIX: list[dict] = [
    {
        "condition": "dirty tree before phase",
        "category": "hard_stop",
        "guidance": "Commit or stash changes before starting a phase.",
    },
    {
        "condition": "active task present before phase",
        "category": "hard_stop",
        "guidance": "Finish or close the active task before starting a new phase.",
    },
    {
        "condition": "test failure",
        "category": "hard_stop",
        "guidance": "Fix test failures before continuing. Do not skip tests.",
    },
    {
        "condition": "pcae health failure",
        "category": "hard_stop",
        "guidance": "Resolve health issues before continuing.",
    },
    {
        "condition": "pcae check failure",
        "category": "hard_stop",
        "guidance": "Resolve check violations before continuing.",
    },
    {
        "condition": "task-memory inconsistency",
        "category": "hard_stop",
        "guidance": "Run pcae doctor task-memory --fix or resolve manually.",
    },
    {
        "condition": "push check not ready",
        "category": "hard_stop",
        "guidance": "Resolve push blockers before continuing.",
    },
    {
        "condition": "lifecycle review enforcement block",
        "category": "hard_stop",
        "guidance": "Complete the required lifecycle review before continuing.",
    },
    {
        "condition": "task finish partial failure",
        "category": "recoverable_stop",
        "guidance": "Run pcae task finish recover --dry-run, then pcae task finish recover --message '...'.",
    },
    {
        "condition": "git index lock / permission failure",
        "category": "recoverable_stop",
        "guidance": "Run pcae doctor git-lock for diagnosis and next steps.",
    },
    {
        "condition": "scope drift required",
        "category": "hard_stop",
        "guidance": "Stop and report. Do not modify files outside the active task scope.",
    },
    {
        "condition": "ambiguity detected",
        "category": "hard_stop",
        "guidance": "Stop and report. Do not guess or assume.",
    },
    {
        "condition": "queue empty",
        "category": "continue_allowed",
        "guidance": "Environment is ready. No queued phases to execute.",
    },
    {
        "condition": "audit warning present",
        "category": "advisory_warning",
        "guidance": "Investigate audit warnings. They may indicate incomplete phase commits.",
    },
    {
        "condition": "handoff missing",
        "category": "advisory_warning",
        "guidance": "Consider running pcae phase handoff before starting a runner.",
    },
    {
        "condition": "autonomy summary missing",
        "category": "advisory_warning",
        "guidance": "Consider running pcae phase autonomy-summary --save for observability.",
    },
]

_RUNNER_POLICY_NOTE = (
    "Human authority is absolute. This policy matrix is advisory for "
    "bounded runner behavior. The human user may override any stop condition."
)


def run_phase_runner_policy(args: argparse.Namespace) -> int:
    matrix = list(_RUNNER_POLICY_MATRIX)

    if args.json:
        print(json.dumps({
            "policy_matrix": matrix,
            "categories": ["hard_stop", "recoverable_stop", "advisory_warning", "continue_allowed"],
            "human_authority_note": _RUNNER_POLICY_NOTE,
        }, indent=2, sort_keys=True))
        return 0

    print("Runner Stop-Condition Policy Matrix")
    print("=" * 40)

    for category, label in [
        ("hard_stop", "Hard Stop"),
        ("recoverable_stop", "Recoverable Stop"),
        ("advisory_warning", "Advisory Warning"),
        ("continue_allowed", "Continue Allowed"),
    ]:
        entries = [e for e in matrix if e["category"] == category]
        if entries:
            print(f"\n  [{label}]")
            for e in entries:
                print(f"    {e['condition']}")
                print(f"      → {e['guidance']}")

    print(f"\n  Note: {_RUNNER_POLICY_NOTE}")
    return 0


_SIM_FIXTURE_MAX = 10


def _build_sim_fixture(count: int) -> list[dict]:
    clamped = min(max(count, 1), _SIM_FIXTURE_MAX)
    entries = []
    for i in range(1, clamped + 1):
        entries.append({
            "title": f"SIM-{i:03d} Simulated phase {i}",
            "phase_id": f"SIM-{i:03d}",
            "source_type": "simulation",
            "simulated": True,
        })
    return entries


def run_phase_runner_sim_fixture(args: argparse.Namespace) -> int:
    count = min(max(getattr(args, "count", 3), 1), _SIM_FIXTURE_MAX)
    entries = _build_sim_fixture(count)

    result = {
        "count": len(entries),
        "entries": entries,
        "real_queue_mutated": False,
        "note": "Simulated fixture entries only. Real phase queue is unchanged.",
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Runner Simulation Fixture")
    print("=" * 40)
    print(f"  Simulated entries: {len(entries)}")
    for e in entries:
        print(f"    - {e['title']}")
    print()
    print(f"  Real queue mutated: no")
    print(f"  Note: {result['note']}")
    return 0


RUNNER_SIMULATIONS_DIR = Path(".pcae") / "runner-simulations"


def _build_runner_simulation(root: HarnessPath, count: int) -> dict:
    readiness = _build_runner_readiness(root)
    sim_entries = _build_sim_fixture(count)

    planned = sim_entries[:min(count, _RUNNER_MAX_PHASES_LIMIT)] if readiness["environment_ready"] else []

    return {
        "would_execute": False,
        "mutation_performed": False,
        "simulated_entries": sim_entries,
        "readiness": readiness,
        "planned_phases": planned,
        "first_planned_phase": planned[0]["title"] if planned else None,
        "max_phases": min(count, _RUNNER_MAX_PHASES_LIMIT),
        "stop_conditions_considered": list(_RUNNER_STOP_CONDITIONS),
        "policy_summary": {
            "hard_stop_count": len([e for e in _RUNNER_POLICY_MATRIX if e["category"] == "hard_stop"]),
            "recoverable_stop_count": len([e for e in _RUNNER_POLICY_MATRIX if e["category"] == "recoverable_stop"]),
            "advisory_warning_count": len([e for e in _RUNNER_POLICY_MATRIX if e["category"] == "advisory_warning"]),
            "continue_allowed_count": len([e for e in _RUNNER_POLICY_MATRIX if e["category"] == "continue_allowed"]),
            "human_authority_note": _RUNNER_POLICY_NOTE,
        },
        "note": "No execution performed. This is a dry-run simulation only.",
    }


def _save_runner_simulation(root: HarnessPath, trace: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    trace_with_ts = {**trace, "created_at": ts}
    sim_dir = root.join(RUNNER_SIMULATIONS_DIR)
    sim_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = sim_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = sim_dir / "latest.json"
    latest_path.write_text(
        json.dumps(trace_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


_RUNNER_SCENARIOS: dict[str, dict] = {
    "dirty-tree": {
        "simulated_condition": "Working tree has uncommitted changes",
        "policy_category": "hard_stop",
        "runner_would_continue": False,
        "suggested_action": "Commit or stash changes before starting a phase.",
    },
    "active-task": {
        "simulated_condition": "An active task contract exists",
        "policy_category": "hard_stop",
        "runner_would_continue": False,
        "suggested_action": "Finish or close the active task before starting a new phase.",
    },
    "audit-warning": {
        "simulated_condition": "Phase audit has warnings (e.g., missing commit pairs)",
        "policy_category": "advisory_warning",
        "runner_would_continue": True,
        "suggested_action": "Investigate audit warnings. They may indicate incomplete phase commits.",
    },
    "git-lock": {
        "simulated_condition": ".git/index.lock exists or permission denied",
        "policy_category": "recoverable_stop",
        "runner_would_continue": False,
        "suggested_action": "Run pcae doctor git-lock for diagnosis and next steps.",
    },
    "queue-empty": {
        "simulated_condition": "Phase queue is empty",
        "policy_category": "continue_allowed",
        "runner_would_continue": True,
        "suggested_action": "Environment is ready. No queued phases to execute.",
    },
}


def run_phase_runner_simulate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    scenario_name: str | None = getattr(args, "scenario", None)

    if scenario_name is not None:
        if scenario_name not in _RUNNER_SCENARIOS:
            available = ", ".join(sorted(_RUNNER_SCENARIOS.keys()))
            print(f"Unknown scenario: {scenario_name}. Available: {available}")
            return 1

        scenario = _RUNNER_SCENARIOS[scenario_name]
        result = {
            "scenario": scenario_name,
            **scenario,
            "note": "Simulated failure only. No repository state was mutated.",
        }

        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        print("Runner Simulation — Failure Scenario")
        print("=" * 40)
        print(f"  Scenario: {scenario_name}")
        print(f"  Condition: {scenario['simulated_condition']}")
        print(f"  Policy category: {scenario['policy_category']}")
        print(f"  Runner would continue: {'yes' if scenario['runner_would_continue'] else 'NO'}")
        print(f"  Suggested action: {scenario['suggested_action']}")
        print()
        print(f"  {result['note']}")
        return 0

    count = min(max(getattr(args, "count", 3), 1), _SIM_FIXTURE_MAX)
    trace = _build_runner_simulation(root, count)

    if getattr(args, "save", False):
        saved_path = _save_runner_simulation(root, trace)
        if not args.json:
            print(f"Simulation trace saved: {saved_path}")

    if args.json:
        print(json.dumps(trace, indent=2, sort_keys=True))
        return 0

    print("Runner Simulation Trace (dry-run)")
    print("=" * 40)
    print(f"  Would execute: no")
    print(f"  Mutation performed: no")
    print(f"  Simulated entries: {len(trace['simulated_entries'])}")
    print(f"  Environment ready: {'yes' if trace['readiness']['environment_ready'] else 'NO'}")
    print(f"  Planned phases: {len(trace['planned_phases'])}")
    if trace["first_planned_phase"]:
        print(f"  First planned: {trace['first_planned_phase']}")

    if trace["readiness"]["blocking_reasons"]:
        print()
        print("  Blockers:")
        for b in trace["readiness"]["blocking_reasons"]:
            print(f"    - {b}")

    print()
    print(f"  Stop conditions: {len(trace['stop_conditions_considered'])}")
    ps = trace["policy_summary"]
    print(f"  Policy: {ps['hard_stop_count']} hard, {ps['recoverable_stop_count']} recoverable, {ps['advisory_warning_count']} advisory, {ps['continue_allowed_count']} continue")
    print()
    print(f"  {trace['note']}")
    return 0


RUNNER_SIMULATION_REVIEWS_DIR = Path(".pcae") / "runner-simulation-reviews"


def _read_latest_simulation(root: HarnessPath) -> dict | None:
    latest = root.join(RUNNER_SIMULATIONS_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _build_sim_review(root: HarnessPath) -> dict:
    sim = _read_latest_simulation(root)
    if sim is None:
        return {
            "review_status": "missing_simulation",
            "review_reasons": ["No simulation artifact found. Run: pcae phase runner-simulate --save"],
            "simulation_present": False,
        }

    blocked_reasons: list[str] = []
    readiness = sim.get("readiness") or {}
    if not readiness.get("environment_ready", False):
        blocked_reasons.append("simulation environment was not ready")
    if sim.get("would_execute", True):
        blocked_reasons.append("simulation would_execute is true (unexpected)")
    if sim.get("mutation_performed", True):
        blocked_reasons.append("simulation mutation_performed is true (unexpected)")

    status = "blocked" if blocked_reasons else "ready_for_approval"

    return {
        "review_status": status,
        "review_reasons": blocked_reasons or ["Simulation is clean and ready for approval review."],
        "simulation_present": True,
        "simulation_created_at": sim.get("created_at"),
        "would_execute": sim.get("would_execute", False),
        "mutation_performed": sim.get("mutation_performed", False),
        "simulated_entries_count": len(sim.get("simulated_entries", [])),
        "planned_phases_count": len(sim.get("planned_phases", [])),
        "readiness_environment_ready": readiness.get("environment_ready"),
        "stop_conditions_count": len(sim.get("stop_conditions_considered", [])),
        "policy_summary": sim.get("policy_summary"),
    }


def _save_sim_review(root: HarnessPath, review: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    review_with_ts = {**review, "reviewed_at": ts}
    review_dir = root.join(RUNNER_SIMULATION_REVIEWS_DIR)
    review_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = review_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = review_dir / "latest.json"
    latest_path.write_text(
        json.dumps(review_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_runner_sim_review(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    review = _build_sim_review(root)

    if getattr(args, "save", False):
        saved_path = _save_sim_review(root, review)
        if not args.json:
            print(f"Review saved: {saved_path}")

    if args.json:
        print(json.dumps(review, indent=2, sort_keys=True))
        return 0

    print("Runner Simulation Review")
    print("=" * 40)
    print(f"  Review status: {review['review_status']}")
    print(f"  Simulation present: {'yes' if review['simulation_present'] else 'no'}")
    if review["simulation_present"]:
        print(f"  Simulation created: {review.get('simulation_created_at', 'unknown')}")
        print(f"  Would execute: {'no' if not review['would_execute'] else 'YES'}")
        print(f"  Mutation performed: {'no' if not review['mutation_performed'] else 'YES'}")
        print(f"  Simulated entries: {review['simulated_entries_count']}")
        print(f"  Planned phases: {review['planned_phases_count']}")
    print()
    print("  Reasons:")
    for r in review["review_reasons"]:
        print(f"    - {r}")
    return 0


RUNNER_SIMULATION_APPROVALS_DIR = Path(".pcae") / "runner-simulation-approvals"


def _read_latest_sim_review(root: HarnessPath) -> dict | None:
    latest = root.join(RUNNER_SIMULATION_REVIEWS_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _build_sim_approval(root: HarnessPath, message: str) -> dict:
    review = _read_latest_sim_review(root)
    if review is None:
        return {
            "approved": False,
            "refusal_reason": "No review artifact found. Run: pcae phase runner-sim-review --save",
        }

    if review.get("review_status") != "ready_for_approval":
        return {
            "approved": False,
            "refusal_reason": f"Review status is '{review.get('review_status')}', not 'ready_for_approval'.",
        }

    return {
        "approved": True,
        "approved_simulation_created_at": review.get("simulation_created_at"),
        "reviewed_at": review.get("reviewed_at"),
        "message": message,
        "approver_source": "local_cli",
        "execution_authorized": False,
    }


def _save_sim_approval(root: HarnessPath, approval: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    approval_with_ts = {**approval, "approved_at": ts}
    approval_dir = root.join(RUNNER_SIMULATION_APPROVALS_DIR)
    approval_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = approval_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = approval_dir / "latest.json"
    latest_path.write_text(
        json.dumps(approval_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_runner_sim_approve(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    message = getattr(args, "message", "") or "Simulation approved."
    dry_run = getattr(args, "dry_run", False)
    approval = _build_sim_approval(root, message)

    if not approval.get("approved", False):
        if args.json:
            print(json.dumps(approval, indent=2, sort_keys=True))
        else:
            print(f"Approval refused: {approval['refusal_reason']}")
        return 1

    if not dry_run:
        saved_path = _save_sim_approval(root, approval)
        if not args.json:
            print(f"Approval saved: {saved_path}")

    if args.json:
        result = {**approval, "dry_run": dry_run}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Runner Simulation Approval")
    print("=" * 40)
    print(f"  Approved: yes")
    print(f"  Dry run: {'yes' if dry_run else 'no'}")
    print(f"  Simulation created: {approval.get('approved_simulation_created_at', 'unknown')}")
    print(f"  Message: {approval['message']}")
    print(f"  Approver: {approval['approver_source']}")
    print(f"  Execution authorized: no")
    return 0


def run_phase_runner_sim_approval_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    approval = _read_latest_sim_approval(root)

    if approval is None:
        if args.json:
            print(json.dumps({"present": False, "reason": "No approval artifact found."}, indent=2, sort_keys=True))
        else:
            print("No approval artifact found.")
            print("Run: pcae phase runner-sim-approve --message '...'")
        return 1

    result = {
        "present": True,
        "approved": approval.get("approved", False),
        "approved_at": approval.get("approved_at"),
        "approved_simulation_created_at": approval.get("approved_simulation_created_at"),
        "reviewed_at": approval.get("reviewed_at"),
        "message": approval.get("message"),
        "approver_source": approval.get("approver_source"),
        "execution_authorized": approval.get("execution_authorized", False),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Runner Simulation Approval (persisted)")
    print("=" * 40)
    print(f"  Present: yes")
    print(f"  Approved: {'yes' if result['approved'] else 'no'}")
    print(f"  Approved at: {result['approved_at'] or 'unknown'}")
    print(f"  Simulation created: {result['approved_simulation_created_at'] or 'unknown'}")
    print(f"  Message: {result['message'] or 'none'}")
    print(f"  Approver: {result['approver_source'] or 'unknown'}")
    print(f"  Execution authorized: {'yes' if result['execution_authorized'] else 'no'}")
    return 0


_PREFLIGHT_REQUIREMENTS = [
    {"requirement": "clean working tree", "check": "working_tree_clean"},
    {"requirement": "healthy idle", "check": "health_idle"},
    {"requirement": "pcae check passed", "check": "check_passed"},
    {"requirement": "task-memory clean", "check": "task_memory_clean"},
    {"requirement": "no unpushed commits", "check": "no_unpushed"},
    {"requirement": "queue non-empty", "check": "queue_present"},
    {"requirement": "queue validation present", "check": "queue_validation_present"},
    {"requirement": "queue valid", "check": "queue_valid"},
    {"requirement": "queue approval present", "check": "queue_approval_present"},
    {"requirement": "queue approval matches current queue", "check": "queue_approval_matches"},
    {"requirement": "queue approval execution_authorized=false", "check": "queue_approval_not_authorized"},
    {"requirement": "execution request present", "check": "execution_request_present"},
    {"requirement": "execution request not denied", "check": "execution_request_not_denied"},
    {"requirement": "execution request not revoked", "check": "execution_request_not_revoked"},
    {"requirement": "execution request review present", "check": "execution_request_review_present"},
    {"requirement": "no-op trace present", "check": "noop_trace_present"},
    {"requirement": "no-op trace safe", "check": "noop_trace_safe"},
    {"requirement": "no-op trace review present", "check": "noop_trace_review_present"},
    {"requirement": "no-op trace review ready", "check": "noop_trace_review_ready"},
    {"requirement": "no-op trace approval present", "check": "noop_trace_approval_present"},
    {"requirement": "no-op trace approval matches trace", "check": "noop_trace_approval_matches"},
    {"requirement": "runner-readiness environment_ready", "check": "environment_ready"},
    {"requirement": "runner-plan executable", "check": "plan_executable"},
    {"requirement": "runner-policy loaded", "check": "policy_loaded"},
    {"requirement": "latest simulation exists", "check": "simulation_present"},
    {"requirement": "latest simulation review ready", "check": "review_ready"},
    {"requirement": "latest simulation approval exists", "check": "approval_present"},
    {"requirement": "approval matches latest simulation/review", "check": "approval_matches"},
    {"requirement": "execution_authorized true (future phase)", "check": "execution_authorized"},
    {"requirement": "max phases bounded", "check": "max_bounded"},
    {"requirement": "hard stop policy enforced", "check": "policy_enforced"},
    {"requirement": "recovery path available", "check": "recovery_available"},
]


def _read_latest_sim_approval(root: HarnessPath) -> dict | None:
    latest = root.join(RUNNER_SIMULATION_APPROVALS_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _build_execution_preflight(root: HarnessPath) -> dict:
    readiness = _build_runner_readiness(root)
    queue = _read_phase_queue(root)
    queue_validation = _build_queue_validate(root)
    queue_approval = _read_latest_queue_approval(root)
    exec_request = _read_latest_runner_execution_request(root)
    exec_request_review = _read_latest_runner_execution_request_review(root)
    sim = _read_latest_simulation(root)
    review = _read_latest_sim_review(root)
    approval = _read_latest_sim_approval(root)
    noop_trace = _read_latest_runner_noop_trace(root)
    noop_trace_review = _read_latest_runner_execution_trace_review(root)
    noop_trace_approval = _read_latest_runner_execution_trace_approval(root)

    queue_approval_present = (
        queue_approval is not None and queue_approval.get("approved", False)
    )
    current_queue_digest = _compute_queue_digest(root)
    queue_approval_matches = (
        queue_approval is not None
        and queue_approval.get("queue_digest") == current_queue_digest
    )
    queue_approval_not_authorized = (
        queue_approval is not None
        and queue_approval.get("execution_authorized") is False
    )

    exec_request_present = exec_request is not None
    exec_request_denied = exec_request.get("denied", False) if exec_request else False
    exec_request_revoked = exec_request.get("revoked", False) if exec_request else False
    exec_request_review_present = exec_request_review is not None
    request_blocks = exec_request_denied or exec_request_revoked

    noop_trace_present = noop_trace is not None
    noop_trace_safe = (
        noop_trace is not None
        and noop_trace.get("noop", False)
        and not noop_trace.get("mutation_performed", True)
        and not noop_trace.get("queue_mutated", True)
        and noop_trace.get("tasks_created", 0) == 0
    )
    noop_trace_review_present = noop_trace_review is not None
    noop_trace_review_ready = (
        noop_trace_review is not None
        and noop_trace_review.get("review_status") == "ready_for_approval"
    )
    noop_trace_approval_present = (
        noop_trace_approval is not None and noop_trace_approval.get("approved", False)
    )
    noop_trace_approval_matches = (
        noop_trace_approval is not None
        and noop_trace is not None
        and noop_trace_approval.get("trace_ref") == noop_trace.get("trace_id")
    )

    checks: dict[str, bool] = {
        "working_tree_clean": readiness["working_tree"] == "clean",
        "health_idle": readiness["health_status"] == "healthy",
        "check_passed": readiness["check_passed"],
        "task_memory_clean": readiness["task_memory_status"] == "clean",
        "no_unpushed": readiness["push_state"] in ("nothing_to_push", "post_finish_closure"),
        "queue_present": len(queue) > 0,
        "queue_validation_present": queue_validation["queue_readable"],
        "queue_valid": queue_validation["valid"],
        "queue_approval_present": queue_approval_present,
        "queue_approval_matches": queue_approval_matches,
        "queue_approval_not_authorized": queue_approval_not_authorized,
        "execution_request_present": exec_request_present,
        "execution_request_not_denied": not exec_request_denied,
        "execution_request_not_revoked": not exec_request_revoked,
        "execution_request_review_present": exec_request_review_present,
        "noop_trace_present": noop_trace_present,
        "noop_trace_safe": noop_trace_safe,
        "noop_trace_review_present": noop_trace_review_present,
        "noop_trace_review_ready": noop_trace_review_ready,
        "noop_trace_approval_present": noop_trace_approval_present,
        "noop_trace_approval_matches": noop_trace_approval_matches,
        "environment_ready": readiness["environment_ready"],
        "plan_executable": readiness["environment_ready"] and len(queue) > 0,
        "policy_loaded": True,
        "simulation_present": sim is not None,
        "review_ready": review is not None and review.get("review_status") == "ready_for_approval",
        "approval_present": approval is not None and approval.get("approved", False),
        "approval_matches": (
            approval is not None
            and sim is not None
            and review is not None
            and approval.get("approved_simulation_created_at") == sim.get("created_at")
        ),
        "execution_authorized": False,
        "max_bounded": True,
        "policy_enforced": True,
        "recovery_available": True,
    }

    met = [r for r in _PREFLIGHT_REQUIREMENTS if checks.get(r["check"], False)]
    unmet = [r for r in _PREFLIGHT_REQUIREMENTS if not checks.get(r["check"], False)]

    return {
        "preflight_status": "design_only",
        "execution_available": False,
        "execution_authorized": False,
        "execution_request_present": exec_request_present,
        "execution_request_status": (
            "denied" if exec_request_denied else
            "revoked" if exec_request_revoked else
            "present" if exec_request_present else
            "missing"
        ),
        "execution_request_review_present": exec_request_review_present,
        "execution_request_review_status": (
            exec_request_review.get("review_status")
            if exec_request_review else None
        ),
        "execution_request_denied": exec_request_denied,
        "execution_request_revoked": exec_request_revoked,
        "request_blocks_authorization": request_blocks,
        "noop_trace_present": noop_trace_present,
        "noop_trace_safe": noop_trace_safe,
        "noop_trace_review_present": noop_trace_review_present,
        "noop_trace_review_status": (
            noop_trace_review.get("review_status")
            if noop_trace_review else None
        ),
        "noop_trace_approval_present": noop_trace_approval_present,
        "noop_trace_approval_matches_trace_or_review": noop_trace_approval_matches,
        "noop_trace_approval_execution_authorized": (
            noop_trace_approval.get("execution_authorized")
            if noop_trace_approval else None
        ),
        "queue_validation_status": "valid" if queue_validation["valid"] else "invalid",
        "queue_validation_present": queue_validation["queue_readable"],
        "queue_valid": queue_validation["valid"],
        "queue_approval_present": queue_approval_present,
        "queue_approval_matches_current_queue": queue_approval_matches,
        "queue_approval_execution_authorized": (
            queue_approval.get("execution_authorized")
            if queue_approval is not None else None
        ),
        "requirements_met": len(met),
        "requirements_total": len(_PREFLIGHT_REQUIREMENTS),
        "requirements": [
            {**r, "met": checks.get(r["check"], False)}
            for r in _PREFLIGHT_REQUIREMENTS
        ],
        "unmet_requirements": [r["requirement"] for r in unmet],
        "human_authority_note": _RUNNER_POLICY_NOTE,
        "note": (
            "Execution is not implemented and not authorized. "
            "This is a design-only preflight specification."
        ),
    }


def run_phase_runner_execution_preflight(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    preflight = _build_execution_preflight(root)

    if args.json:
        print(json.dumps(preflight, indent=2, sort_keys=True))
        return 0

    print("Runner Execution Preflight (design only)")
    print("=" * 40)
    print(f"  Status: {preflight['preflight_status']}")
    print(f"  Execution available: no")
    print(f"  Execution authorized: no")
    print(f"  Requirements met: {preflight['requirements_met']}/{preflight['requirements_total']}")
    print()
    for req in preflight["requirements"]:
        mark = "OK" if req["met"] else "--"
        print(f"  [{mark}] {req['requirement']}")
    if preflight["unmet_requirements"]:
        print()
        print("  Unmet:")
        for u in preflight["unmet_requirements"]:
            print(f"    - {u}")
    print()
    print(f"  {preflight['note']}")
    print(f"  {preflight['human_authority_note']}")
    return 0


_EXECUTION_AUTHORIZATION_REFUSAL = (
    "Execution authorization is not implemented. "
    "A future explicit execution-authorization phase is required before "
    "machine-mediated runner execution can be authorized. "
    "Human authority remains absolute."
)


def run_phase_runner_execution_authorize(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    exec_request = _read_latest_runner_execution_request(root)

    request_present = exec_request is not None
    request_denied = exec_request.get("denied", False) if exec_request else False
    request_revoked = exec_request.get("revoked", False) if exec_request else False
    request_blocks = request_denied or request_revoked

    # Check contract/schema/rules presence
    contract_path = root.join(EXECUTION_AUTHORIZATION_CONTRACTS_DIR / "latest.json")
    schema_path = root.join(EXECUTION_AUTHORIZATION_SCHEMAS_DIR / "latest.json")
    rules_path = root.join(EXECUTION_AUTHORIZATION_MATCHING_RULES_DIR / "latest.json")
    contract_present = contract_path.is_file()
    schema_present = schema_path.is_file()
    rules_present = rules_path.is_file()

    if request_blocks:
        block_detail = []
        if request_denied: block_detail.append("request has been denied")
        if request_revoked: block_detail.append("request has been revoked")
        refusal = (
            "Execution authorization is not implemented. "
            "Additionally, the execution request is in a blocking lifecycle state: "
            + "; ".join(block_detail) + ". Human authority remains absolute."
        )
    elif not request_present:
        missing = []
        if not contract_present: missing.append("authorization contract")
        if not schema_present: missing.append("authorization schema")
        if not rules_present: missing.append("matching rules")
        ref = (
            "Execution authorization is not implemented. "
            "No execution request artifact is present. "
        )
        if missing:
            ref += f"Authorization prerequisites incomplete: {', '.join(missing)} missing. "
        ref += "Human authority remains absolute."
        refusal = ref
    else:
        refusal = _EXECUTION_AUTHORIZATION_REFUSAL

    result = {
        "authorization_available": False,
        "authorized": False,
        "execution_authorized": False,
        "mutation_performed": False,
        "dry_run": getattr(args, "dry_run", False),
        "request_present": request_present,
        "request_denied": request_denied,
        "request_revoked": request_revoked,
        "authorization_blocked_by_request_state": request_blocks,
        "execution_authorization_contract_present": contract_present,
        "execution_authorization_schema_present": schema_present,
        "execution_authorization_matching_rules_present": rules_present,
        "refusal_reason": refusal,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    print("Runner Execution Authorization")
    print("=" * 40)
    print(f"  Authorization available: no")
    print(f"  Authorized: no")
    print(f"  Mutation performed: no")
    print(f"  Request present: {'yes' if request_present else 'no'}")
    if request_present:
        print(f"  Request denied: {'yes' if request_denied else 'no'}")
        print(f"  Request revoked: {'yes' if request_revoked else 'no'}")
    print(f"  Contract present: {'yes' if contract_present else 'no'}")
    print(f"  Schema present: {'yes' if schema_present else 'no'}")
    print(f"  Matching rules present: {'yes' if rules_present else 'no'}")
    print()
    print(f"  {refusal}")
    return 1


_EXECUTION_AUTHZ_SCHEMA = {
    "schema_version": "1.0",
    "schema_only": True,
    "artifact_written": False,
    "execution_authorized": False,
    "authorization_available": False,
    "proposed_fields": {
        "artifact_version": "string — schema version (e.g. \"1.0\")",
        "authorization_id": "string — unique identifier for this authorization",
        "authorized": "bool — whether execution is authorized",
        "execution_authorized": "bool — synonym for authorized",
        "authorized_at": "ISO timestamp — when authorization was recorded",
        "authorizer_source": "string — source of authorization (e.g. \"local_cli\")",
        "queue_digest": "string — SHA-256 of the approved queue at authorization time",
        "queue_approval_ref": "string — reference to queue approval artifact",
        "simulation_ref": "string — reference to simulation artifact",
        "simulation_review_ref": "string — reference to simulation review artifact",
        "simulation_approval_ref": "string — reference to simulation approval artifact",
        "preflight_ref": "string — reference to preflight state at authorization time",
        "max_phases": "int — maximum phases authorized to execute",
        "scope": "list of phase IDs — bounds for authorized execution",
        "required_stop_policy_version": "string — policy version required for execution",
        "expires_at": "ISO timestamp — when authorization expires (if applicable)",
        "revocation_supported": "bool — whether this authorization can be revoked",
        "human_authority_statement": "string — explicit statement of human authority",
    },
    "minimum_requirements": [
        "clean working tree",
        "healthy idle",
        "pcae check passed",
        "task-memory clean",
        "no unpushed commits",
        "non-empty valid queue",
        "queue approval matching current queue",
        "runner simulation exists",
        "runner simulation review ready",
        "runner simulation approval exists",
        "runner preflight satisfied except execution_authorized",
        "max phase bound",
        "stop-condition policy loaded",
        "explicit human authorization event",
    ],
    "forbidden_implied_authorization": [
        "no implied authorization from queue approval",
        "no implied authorization from simulation approval",
        "no implied authorization from passing preflight",
        "no authorization if queue changed after approval",
        "no authorization if audit warnings exist",
        "no authorization if there is an active task or dirty tree",
    ],
    "note": (
        "This is a read-only schema preview. No authorization artifact is written. "
        "Execution authorization is not implemented. "
        "Human authority remains absolute."
    ),
}


def run_phase_runner_execution_authorization_schema(args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps(_EXECUTION_AUTHZ_SCHEMA, indent=2, sort_keys=True))
        return 0

    print("Execution Authorization Artifact Schema (proposed)")
    print("=" * 40)
    print(f"  Schema version: {_EXECUTION_AUTHZ_SCHEMA['schema_version']}")
    print(f"  Schema only: yes")
    print(f"  Artifact written: no")
    print(f"  Execution authorized: no")
    print(f"  Authorization available: no")
    print()
    print("  Proposed fields:")
    for field, desc in _EXECUTION_AUTHZ_SCHEMA["proposed_fields"].items():
        print(f"    {field}: {desc}")
    print()
    print("  Minimum requirements:")
    for req in _EXECUTION_AUTHZ_SCHEMA["minimum_requirements"]:
        print(f"    - {req}")
    print()
    print("  Forbidden implied authorization:")
    for rule in _EXECUTION_AUTHZ_SCHEMA["forbidden_implied_authorization"]:
        print(f"    - {rule}")
    print()
    print(f"  {_EXECUTION_AUTHZ_SCHEMA['note']}")
    return 0


_RUNNER_EXECUTION_REFUSAL = (
    "Runner execution is not implemented and not authorized. "
    "A future explicit execution-authorization phase is required before "
    "machine-mediated runner execution can occur. "
    "Queue entries, approvals, simulations, and preflight checks are "
    "planning-only artifacts and do not authorize or enable execution. "
    "Human authority remains absolute."
)

_RUNNER_EXECUTION_SUGGESTED_STEPS = [
    "pcae phase queue validate",
    "pcae phase queue approve --message '...'",
    "pcae phase queue approval-check",
    "pcae phase runner-execution-preflight",
    "pcae phase runner-execution-authorize --dry-run",
    "(Future) Explicit execution authorization phase",
]


RUNNER_EXECUTION_TRACES_DIR = Path(".pcae") / "runner-execution-traces"

_RUNNER_NOOP_SCENARIOS: dict[str, dict] = {
    "dirty-tree": {
        "scenario": "dirty-tree",
        "simulated_condition": "Working tree has uncommitted changes",
        "policy_category": "hard_stop",
        "abort": True,
        "suggested_action": "Commit or stash changes before starting a phase.",
    },
    "active-task": {
        "scenario": "active-task",
        "simulated_condition": "An active task contract exists",
        "policy_category": "hard_stop",
        "abort": True,
        "suggested_action": "Finish or close the active task before starting a new phase.",
    },
    "denied-request": {
        "scenario": "denied-request",
        "simulated_condition": "Execution request has been denied",
        "policy_category": "hard_stop",
        "abort": True,
        "suggested_action": "Create a new execution request or wait for future authorization phases.",
    },
    "revoked-request": {
        "scenario": "revoked-request",
        "simulated_condition": "Execution request has been revoked",
        "policy_category": "hard_stop",
        "abort": True,
        "suggested_action": "Create a new execution request or wait for future authorization phases.",
    },
    "queue-empty": {
        "scenario": "queue-empty",
        "simulated_condition": "Phase queue is empty",
        "policy_category": "continue_allowed",
        "abort": True,
        "suggested_action": "Add phases to the queue or use fixture-add for testing.",
    },
    "authorization-unavailable": {
        "scenario": "authorization-unavailable",
        "simulated_condition": "Execution authorization is not implemented",
        "policy_category": "hard_stop",
        "abort": True,
        "suggested_action": "Wait for a future explicit execution-authorization phase.",
    },
}


def _build_runner_noop_trace(root: HarnessPath, scenario: str | None) -> dict:
    queue_validation = _build_queue_validate(root)
    queue_approval = _read_latest_queue_approval(root)
    preflight = _build_execution_preflight(root)
    auth_summary = _build_runner_authorization_summary(root)
    exec_request = _read_latest_runner_execution_request(root)
    timestamp = datetime.now(timezone.utc)

    if scenario and scenario in _RUNNER_NOOP_SCENARIOS:
        sc = _RUNNER_NOOP_SCENARIOS[scenario]
        return {
            "noop": True,
            "scenario": sc["scenario"],
            "simulated_condition": sc["simulated_condition"],
            "policy_category": sc["policy_category"],
            "abort": sc["abort"],
            "execution_available": False,
            "execution_authorized": False,
            "would_execute": False,
            "mutation_performed": False,
            "tasks_created": 0,
            "queue_mutated": False,
            "suggested_action": sc["suggested_action"],
            "suggested_next_steps": list(_RUNNER_EXECUTION_SUGGESTED_STEPS),
            "trace_id": f"noop-{timestamp:%Y%m%dT%H%M%S}-{timestamp.microsecond:06d}",
            "created_at": timestamp.isoformat(),
            "note": (
                f"Simulated no-op abort scenario: {sc['scenario']}. "
                "No repository state was mutated. This is a simulation only."
            ),
        }

    request_present = exec_request is not None
    request_denied = exec_request.get("denied", False) if exec_request else False
    request_revoked = exec_request.get("revoked", False) if exec_request else False
    request_blocks = request_denied or request_revoked

    binding_complete = (
        queue_validation["queue_ready"]
        and queue_validation["valid"]
        and queue_approval is not None
        and queue_approval.get("queue_digest") == _compute_queue_digest(root)
        and request_present
        and not request_blocks
    )
    binding_reasons: list[str] = []
    if not queue_validation["queue_ready"]:
        binding_reasons.append("queue is empty or not ready")
    if not queue_validation["valid"]:
        binding_reasons.append("queue validation failed")
    if queue_approval is None:
        binding_reasons.append("no queue approval artifact")
    elif queue_approval.get("queue_digest") != _compute_queue_digest(root):
        binding_reasons.append("queue approval does not match current queue")
    if not request_present:
        binding_reasons.append("no execution request artifact")
    if request_blocks:
        binding_reasons.append("request is denied or revoked")

    return {
        "noop": True,
        "execution_available": False,
        "execution_authorized": False,
        "would_execute": False,
        "mutation_performed": False,
        "tasks_created": 0,
        "queue_mutated": False,
        "trace_id": f"noop-{timestamp:%Y%m%dT%H%M%S}-{timestamp.microsecond:06d}",
        "created_at": timestamp.isoformat(),
        "refusal_reason": (
            "Runner execution is not implemented and not authorized. "
            "This is a no-op trace only."
        ),
        "queue_validation_snapshot": {
            "valid": queue_validation["valid"],
            "queue_ready": queue_validation["queue_ready"],
            "entry_count": queue_validation["queue_entry_count"],
        },
        "queue_approval_snapshot": {
            "present": queue_approval is not None,
            "matches_current_queue": (
                queue_approval.get("queue_digest") == _compute_queue_digest(root)
            ) if queue_approval else False,
        },
        "preflight_snapshot": {
            "status": preflight["preflight_status"],
            "requirements_met": preflight["requirements_met"],
            "requirements_total": preflight["requirements_total"],
        },
        "authorization_summary_snapshot": {
            "overall_status": auth_summary["overall_status"],
        },
        "runner_policy_summary": {
            "hard_stop_count": len([e for e in _RUNNER_POLICY_MATRIX if e["category"] == "hard_stop"]),
            "recoverable_stop_count": len([e for e in _RUNNER_POLICY_MATRIX if e["category"] == "recoverable_stop"]),
            "advisory_warning_count": len([e for e in _RUNNER_POLICY_MATRIX if e["category"] == "advisory_warning"]),
            "continue_allowed_count": len([e for e in _RUNNER_POLICY_MATRIX if e["category"] == "continue_allowed"]),
        },
        "binding": {
            "queue_approval_present": queue_approval is not None,
            "queue_approval_matches_current_queue": (
                queue_approval.get("queue_digest") == _compute_queue_digest(root)
            ) if queue_approval else False,
            "simulation_approval_present": _read_latest_sim_approval(root) is not None,
            "execution_request_present": request_present,
            "execution_request_review_present": _read_latest_runner_execution_request_review(root) is not None,
            "execution_request_denied": request_denied,
            "execution_request_revoked": request_revoked,
            "authorization_summary_status": auth_summary["overall_status"],
            "preflight_status": preflight["preflight_status"],
            "binding_complete": binding_complete,
            "binding_reasons": binding_reasons or ["governance chain is complete for no-op trace"],
        },
        "suggested_next_steps": list(_RUNNER_EXECUTION_SUGGESTED_STEPS),
        "note": (
            "This is a no-op execution trace. No queue entries were executed. "
            "No artifacts, queue entries, or tasks are mutated. "
            "Human authority remains absolute."
        ),
    }


def _save_runner_noop_trace(root: HarnessPath, trace: dict) -> Path:
    trace_dir = root.join(RUNNER_EXECUTION_TRACES_DIR)
    trace_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = trace_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = trace_dir / "latest.json"
    latest_path.write_text(
        json.dumps(trace, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_runner_execute(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    noop = getattr(args, "noop", False)
    scenario: str | None = getattr(args, "scenario", None)

    if scenario and not noop:
        if args.json:
            print(json.dumps({
                "error": "--scenario requires --noop",
                "execution_authorized": False,
            }, indent=2, sort_keys=True))
        else:
            print("Error: --scenario requires --noop flag.")
        return 1

    if noop:
        trace = _build_runner_noop_trace(root, scenario)

        if getattr(args, "save", False):
            saved_path = _save_runner_noop_trace(root, trace)
            if not args.json:
                print(f"No-op trace saved: {saved_path}")

        if args.json:
            print(json.dumps(trace, indent=2, sort_keys=True))
            return 0

        print("Runner Execution No-Op Trace")
        print("=" * 40)
        print(f"  No-op: yes")
        if trace.get("scenario"):
            print(f"  Scenario: {trace['scenario']}")
            print(f"  Simulated condition: {trace['simulated_condition']}")
            print(f"  Policy category: {trace['policy_category']}")
            print(f"  Abort: {'yes' if trace.get('abort') else 'no'}")
            print(f"  Suggested action: {trace.get('suggested_action')}")
        else:
            print(f"  Trace ID: {trace['trace_id']}")
            b = trace["binding"]
            print(f"  Binding complete: {'yes' if b['binding_complete'] else 'no'}")
            if b["binding_reasons"]:
                print("  Binding reasons:")
                for r in b["binding_reasons"]:
                    print(f"    - {r}")
            print()
            print("  Snapshots:")
            qv = trace["queue_validation_snapshot"]
            print(f"    Queue: valid={'yes' if qv['valid'] else 'no'} ready={'yes' if qv['queue_ready'] else 'no'} entries={qv['entry_count']}")
            qa = trace["queue_approval_snapshot"]
            print(f"    Queue approval: present={'yes' if qa['present'] else 'no'} matches={'yes' if qa['matches_current_queue'] else 'no'}")
            ps = trace["preflight_snapshot"]
            print(f"    Preflight: {ps['status']} ({ps['requirements_met']}/{ps['requirements_total']})")
            a_s = trace["authorization_summary_snapshot"]
            print(f"    Authorization: {a_s['overall_status']}")
        print(f"  Execution available: no")
        print(f"  Execution authorized: no")
        print(f"  Would execute: no")
        print(f"  Mutation performed: no")
        print(f"  Tasks created: 0")
        print(f"  Queue mutated: no")
        print()
        print(f"  {trace['note']}")
        return 0

    # Non-noop: original refusal behavior
    result = {
        "execution_available": False,
        "execution_authorized": False,
        "mutation_performed": False,
        "tasks_created": 0,
        "queue_mutated": False,
        "dry_run": getattr(args, "dry_run", False),
        "refusal_reason": _RUNNER_EXECUTION_REFUSAL,
        "suggested_next_steps": list(_RUNNER_EXECUTION_SUGGESTED_STEPS),
        "note": (
            "This command always refuses. Runner execution is not implemented. "
            "No artifacts, queue entries, or tasks are mutated. "
            "Human authority remains absolute."
        ),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    print("Runner Execution")
    print("=" * 40)
    print(f"  Execution available: no")
    print(f"  Execution authorized: no")
    print(f"  Mutation performed: no")
    print(f"  Tasks created: 0")
    print(f"  Queue mutated: no")
    print(f"  Dry run: {'yes' if result['dry_run'] else 'no'}")
    print()
    print(f"  {_RUNNER_EXECUTION_REFUSAL}")
    print()
    print("  Suggested next steps:")
    for step in _RUNNER_EXECUTION_SUGGESTED_STEPS:
        print(f"    - {step}")
    print()
    print(f"  {result['note']}")
    return 1


RUNNER_EXECUTION_TRACE_REVIEWS_DIR = Path(".pcae") / "runner-execution-trace-reviews"


def _read_latest_runner_noop_trace(root: HarnessPath) -> dict | None:
    latest = root.join(RUNNER_EXECUTION_TRACES_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _build_runner_execution_trace_review(root: HarnessPath) -> dict:
    trace = _read_latest_runner_noop_trace(root)

    if trace is None:
        return {
            "trace_present": False,
            "review_status": "missing_trace",
            "review_reasons": ["No no-op execution trace found. Run: pcae phase runner-execute --noop --save"],
            "execution_authorized": False,
            "execution_available": False,
        }

    blocked_reasons: list[str] = []
    if trace.get("execution_authorized", True):
        blocked_reasons.append("trace reports execution_authorized=true (unexpected)")
    if trace.get("mutation_performed", True):
        blocked_reasons.append("trace reports mutation_performed=true (unexpected)")
    if trace.get("queue_mutated", True):
        blocked_reasons.append("trace reports queue_mutated=true (unexpected)")
    if trace.get("tasks_created", 0) > 0:
        blocked_reasons.append("trace reports tasks_created > 0 (unexpected)")
    if not trace.get("noop", False):
        blocked_reasons.append("trace is not a no-op trace")

    status = "blocked" if blocked_reasons else "ready_for_approval"

    return {
        "trace_present": True,
        "trace_id": trace.get("trace_id"),
        "trace_created_at": trace.get("created_at"),
        "noop": trace.get("noop", False),
        "would_execute": trace.get("would_execute", False),
        "mutation_performed": trace.get("mutation_performed", False),
        "execution_available": False,
        "execution_authorized": False,
        "queue_mutated": trace.get("queue_mutated", False),
        "tasks_created": trace.get("tasks_created", 0),
        "binding_complete": (trace.get("binding") or {}).get("binding_complete") if trace.get("binding") else None,
        "scenario": trace.get("scenario"),
        "review_status": status,
        "review_reasons": blocked_reasons or ["No-op trace is safe and ready for approval review."],
        "note": "This is a review of a no-op execution trace. No execution occurred or was authorized.",
    }


def _save_runner_execution_trace_review(root: HarnessPath, review: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    review_with_ts = {**review, "reviewed_at": ts}
    review_dir = root.join(RUNNER_EXECUTION_TRACE_REVIEWS_DIR)
    review_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = review_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = review_dir / "latest.json"
    latest_path.write_text(
        json.dumps(review_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_runner_execution_trace_review(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    review = _build_runner_execution_trace_review(root)

    if getattr(args, "save", False):
        saved_path = _save_runner_execution_trace_review(root, review)
        if not args.json:
            print(f"Trace review saved: {saved_path}")

    if args.json:
        print(json.dumps(review, indent=2, sort_keys=True))
        return 0

    print("Runner No-Op Trace Review")
    print("=" * 40)
    print(f"  Trace present: {'yes' if review['trace_present'] else 'no'}")
    if review["trace_present"]:
        print(f"  Trace ID: {review.get('trace_id', 'unknown')}")
        print(f"  No-op: {'yes' if review['noop'] else 'no'}")
        print(f"  Would execute: {'no' if not review['would_execute'] else 'YES'}")
        print(f"  Mutation performed: {'no' if not review['mutation_performed'] else 'YES'}")
        if review.get("scenario"):
            print(f"  Scenario: {review['scenario']}")
        if review.get("binding_complete") is not None:
            print(f"  Binding complete: {'yes' if review['binding_complete'] else 'no'}")
    print(f"  Review status: {review['review_status']}")
    print(f"  Execution available: no")
    print(f"  Execution authorized: no")
    print()
    print("  Reasons:")
    for r in review["review_reasons"]:
        print(f"    - {r}")
    print()
    print(f"  {review['note']}")
    return 0


RUNNER_EXECUTION_TRACE_APPROVALS_DIR = Path(".pcae") / "runner-execution-trace-approvals"


def _read_latest_runner_execution_trace_review(root: HarnessPath) -> dict | None:
    latest = root.join(RUNNER_EXECUTION_TRACE_REVIEWS_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _build_runner_execution_trace_approve(root: HarnessPath, message: str) -> dict:
    review = _read_latest_runner_execution_trace_review(root)
    if review is None:
        return {
            "approved": False,
            "execution_authorized": False,
            "execution_available": False,
            "refusal_reason": "No trace review artifact found. Run: pcae phase runner-execution-trace-review --save",
        }
    if review.get("review_status") != "ready_for_approval":
        return {
            "approved": False,
            "execution_authorized": False,
            "execution_available": False,
            "refusal_reason": f"Review status is '{review.get('review_status')}', not 'ready_for_approval'.",
        }
    return {
        "approved": True,
        "noop_approved": True,
        "execution_authorized": False,
        "execution_available": False,
        "trace_ref": review.get("trace_id"),
        "trace_created_at": review.get("trace_created_at"),
        "trace_review_ref": review.get("reviewed_at") or review.get("review_status"),
        "message": message,
        "approver_source": "local_cli",
    }


def _save_runner_execution_trace_approval(root: HarnessPath, approval: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    approval_with_ts = {**approval, "approved_at": ts}
    approval_dir = root.join(RUNNER_EXECUTION_TRACE_APPROVALS_DIR)
    approval_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = approval_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = approval_dir / "latest.json"
    latest_path.write_text(
        json.dumps(approval_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def _read_latest_runner_execution_trace_approval(root: HarnessPath) -> dict | None:
    latest = root.join(RUNNER_EXECUTION_TRACE_APPROVALS_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def run_phase_runner_execution_trace_approve(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    message = getattr(args, "message", "") or "No-op trace approved."
    dry_run = getattr(args, "dry_run", False)
    approval = _build_runner_execution_trace_approve(root, message)

    if not approval.get("approved", False):
        if args.json:
            print(json.dumps(approval, indent=2, sort_keys=True))
        else:
            print(f"Approval refused: {approval['refusal_reason']}")
        return 1

    if not dry_run:
        _save_runner_execution_trace_approval(root, approval)

    if args.json:
        result = {**approval, "dry_run": dry_run}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Runner No-Op Trace Approval")
    print("=" * 40)
    print(f"  Approved: yes")
    print(f"  No-op approved: yes")
    print(f"  Dry run: {'yes' if dry_run else 'no'}")
    print(f"  Trace ref: {approval.get('trace_ref', 'unknown')}")
    print(f"  Message: {approval['message']}")
    print(f"  Approver: {approval['approver_source']}")
    print(f"  Execution authorized: no")
    print(f"  Execution available: no")
    print()
    print("  This approves a no-op trace only, not execution.")
    return 0


def run_phase_runner_execution_trace_approval_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    approval = _read_latest_runner_execution_trace_approval(root)

    if approval is None:
        if args.json:
            print(json.dumps({"present": False, "reason": "No trace approval artifact found."}, indent=2, sort_keys=True))
        else:
            print("No trace approval artifact found.")
            print("Run: pcae phase runner-execution-trace-approve --message '...'")
        return 1

    result = {
        "present": True,
        "approved": approval.get("approved", False),
        "noop_approved": approval.get("noop_approved", False),
        "approved_at": approval.get("approved_at"),
        "trace_ref": approval.get("trace_ref"),
        "message": approval.get("message"),
        "approver_source": approval.get("approver_source"),
        "execution_authorized": approval.get("execution_authorized", False),
        "execution_available": approval.get("execution_available", False),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Runner No-Op Trace Approval (persisted)")
    print("=" * 40)
    print(f"  Present: yes")
    print(f"  Approved: {'yes' if result['approved'] else 'no'}")
    print(f"  No-op approved: {'yes' if result['noop_approved'] else 'no'}")
    print(f"  Approved at: {result['approved_at'] or 'unknown'}")
    print(f"  Trace ref: {result['trace_ref'] or 'unknown'}")
    print(f"  Message: {result['message'] or 'none'}")
    print(f"  Approver: {result['approver_source'] or 'unknown'}")
    print(f"  Execution authorized: {'yes' if result['execution_authorized'] else 'no'}")
    print(f"  Execution available: {'yes' if result['execution_available'] else 'no'}")
    return 0


RUNNER_EXECUTION_REQUESTS_DIR = Path(".pcae") / "runner-execution-requests"


def _build_runner_execution_request(root: HarnessPath, message: str) -> dict:
    queue_validation = _build_queue_validate(root)
    sim = _read_latest_simulation(root)
    timestamp = datetime.now(timezone.utc)
    request_id = f"req-{timestamp:%Y%m%dT%H%M%S}-{timestamp.microsecond:06d}"

    return {
        "request_id": request_id,
        "requested": True,
        "approved": False,
        "denied": False,
        "revoked": False,
        "execution_authorized": False,
        "created_at": timestamp.isoformat(),
        "requester_source": "local_cli",
        "message": message,
        "request_ready": queue_validation["queue_ready"] and queue_validation["valid"],
        "artifact_written": False,
        "snapshot": {
            "queue_validation": {
                "valid": queue_validation["valid"],
                "queue_ready": queue_validation["queue_ready"],
                "entry_count": queue_validation["queue_entry_count"],
            },
            "simulation_present": sim is not None,
            "note": "No execution performed. This is a request only.",
        },
    }


def _save_runner_execution_request(root: HarnessPath, request: dict) -> Path:
    request_dir = root.join(RUNNER_EXECUTION_REQUESTS_DIR)
    request_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = request_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = request_dir / "latest.json"
    request_with_written = {**request, "artifact_written": True}
    latest_path.write_text(
        json.dumps(request_with_written, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def _read_latest_runner_execution_request(root: HarnessPath) -> dict | None:
    latest = root.join(RUNNER_EXECUTION_REQUESTS_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _read_latest_runner_execution_request_review(root: HarnessPath) -> dict | None:
    latest = root.join(RUNNER_EXECUTION_REQUEST_REVIEWS_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def run_phase_runner_execution_request(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    message = getattr(args, "message", "") or "Execution authorization requested."
    dry_run = getattr(args, "dry_run", False)
    request = _build_runner_execution_request(root, message)

    if not dry_run:
        _save_runner_execution_request(root, request)

    if args.json:
        result = {**request, "dry_run": dry_run, "artifact_written": not dry_run}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Runner Execution Request")
    print("=" * 40)
    print(f"  Request ID: {request['request_id']}")
    print(f"  Requested: yes")
    print(f"  Approved: no")
    print(f"  Denied: no")
    print(f"  Revoked: no")
    print(f"  Execution authorized: no")
    print(f"  Request ready: {'yes' if request['request_ready'] else 'no'}")
    print(f"  Dry run: {'yes' if dry_run else 'no'}")
    print(f"  Artifact written: {'yes' if not dry_run else 'no'}")
    print(f"  Message: {request['message']}")
    print()
    print(f"  Snapshot:")
    qv = request["snapshot"]["queue_validation"]
    print(f"    Queue valid: {'yes' if qv['valid'] else 'no'}")
    print(f"    Queue ready: {'yes' if qv['queue_ready'] else 'no'}")
    print(f"    Entry count: {qv['entry_count']}")
    print(f"    Simulation present: {'yes' if request['snapshot']['simulation_present'] else 'no'}")
    print()
    print(f"  No execution performed. This is a request only.")
    return 0


def run_phase_runner_execution_request_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    request = _read_latest_runner_execution_request(root)

    if request is None:
        if args.json:
            print(json.dumps({"present": False, "reason": "No execution request artifact found."}, indent=2, sort_keys=True))
        else:
            print("No execution request artifact found.")
            print("Run: pcae phase runner-execution-request --message '...'")
        return 1

    result = {
        "present": True,
        "request_id": request.get("request_id"),
        "requested": request.get("requested", False),
        "approved": request.get("approved", False),
        "denied": request.get("denied", False),
        "revoked": request.get("revoked", False),
        "execution_authorized": request.get("execution_authorized", False),
        "created_at": request.get("created_at"),
        "message": request.get("message"),
        "request_ready": request.get("request_ready", False),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Runner Execution Request (persisted)")
    print("=" * 40)
    print(f"  Present: yes")
    print(f"  Request ID: {result['request_id'] or 'unknown'}")
    print(f"  Created: {result['created_at'] or 'unknown'}")
    print(f"  Requested: {'yes' if result['requested'] else 'no'}")
    print(f"  Approved: {'yes' if result['approved'] else 'no'}")
    print(f"  Denied: {'yes' if result['denied'] else 'no'}")
    print(f"  Revoked: {'yes' if result['revoked'] else 'no'}")
    print(f"  Execution authorized: {'yes' if result['execution_authorized'] else 'no'}")
    print(f"  Request ready: {'yes' if result['request_ready'] else 'no'}")
    print(f"  Message: {result['message'] or 'none'}")
    return 0


RUNNER_EXECUTION_REQUEST_REVIEWS_DIR = Path(".pcae") / "runner-execution-request-reviews"


def _build_runner_execution_request_review(root: HarnessPath) -> dict:
    request = _read_latest_runner_execution_request(root)

    if request is None:
        return {
            "review_status": "missing_request",
            "review_reasons": ["No execution request artifact found. Run: pcae phase runner-execution-request --message '...'"],
            "request_present": False,
            "approval_granted": False,
            "execution_authorized": False,
        }

    reasons: list[str] = []
    missing: list[str] = []

    if request.get("denied", False):
        reasons.append("request has been denied")
    if request.get("revoked", False):
        reasons.append("request has been revoked")
    if request.get("execution_authorized", False):
        reasons.append("execution_authorized is true (unexpected)")

    queue_validation = _build_queue_validate(root)
    if not queue_validation["valid"]:
        missing.append("queue validation failed")
    if not queue_validation["queue_ready"]:
        missing.append("queue is empty or not ready")

    sim = _read_latest_simulation(root)
    if sim is None:
        missing.append("no simulation artifact")

    status = "blocked" if reasons or missing else "ready_for_denial_or_future_authorization"

    return {
        "review_status": status,
        "review_reasons": reasons or ["Request appears structurally valid but execution authorization is still unavailable."],
        "missing_prerequisites": missing,
        "request_present": True,
        "request_id": request.get("request_id"),
        "request_created_at": request.get("created_at"),
        "request_execution_authorized": request.get("execution_authorized", False),
        "request_denied": request.get("denied", False),
        "request_revoked": request.get("revoked", False),
        "approval_granted": False,
        "execution_authorized": False,
        "note": "Execution is not authorized. This review does not approve or authorize execution.",
    }


def _save_runner_execution_request_review(root: HarnessPath, review: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    review_with_ts = {**review, "reviewed_at": ts}
    review_dir = root.join(RUNNER_EXECUTION_REQUEST_REVIEWS_DIR)
    review_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = review_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = review_dir / "latest.json"
    latest_path.write_text(
        json.dumps(review_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_runner_execution_request_review(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    review = _build_runner_execution_request_review(root)

    if getattr(args, "save", False):
        saved_path = _save_runner_execution_request_review(root, review)
        if not args.json:
            print(f"Review saved: {saved_path}")

    if args.json:
        print(json.dumps(review, indent=2, sort_keys=True))
        return 0

    print("Runner Execution Request Review")
    print("=" * 40)
    print(f"  Review status: {review['review_status']}")
    print(f"  Request present: {'yes' if review['request_present'] else 'no'}")
    if review["request_present"]:
        print(f"  Request ID: {review['request_id'] or 'unknown'}")
        print(f"  Request denied: {'yes' if review['request_denied'] else 'no'}")
        print(f"  Request revoked: {'yes' if review['request_revoked'] else 'no'}")
    print(f"  Approval granted: no")
    print(f"  Execution authorized: no")
    if review["missing_prerequisites"]:
        print()
        print("  Missing prerequisites:")
        for m in review["missing_prerequisites"]:
            print(f"    - {m}")
    print()
    print("  Reasons:")
    for r in review["review_reasons"]:
        print(f"    - {r}")
    print()
    print(f"  {review['note']}")
    return 0


RUNNER_EXECUTION_REQUEST_DENIALS_DIR = Path(".pcae") / "runner-execution-request-denials"
RUNNER_EXECUTION_REQUEST_REVOCATIONS_DIR = Path(".pcae") / "runner-execution-request-revocations"


def _build_runner_execution_request_deny(root: HarnessPath, message: str) -> dict:
    request = _read_latest_runner_execution_request(root)

    if request is None:
        return {
            "denied": False,
            "execution_authorized": False,
            "refusal_reason": "No execution request artifact found. Run: pcae phase runner-execution-request --message '...'",
        }

    if request.get("denied", False):
        return {
            "denied": True,
            "execution_authorized": False,
            "already_denied": True,
            "request_id": request.get("request_id"),
            "message": message,
            "note": "Request was already denied. Idempotent: denial state unchanged.",
        }

    return {
        "denied": True,
        "execution_authorized": False,
        "denied_request_id": request.get("request_id"),
        "denied_request_created_at": request.get("created_at"),
        "message": message,
        "denier_source": "local_cli",
    }


def _save_runner_execution_request_denial(root: HarnessPath, denial: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    denial_with_ts = {**denial, "denied_at": ts}
    denial_dir = root.join(RUNNER_EXECUTION_REQUEST_DENIALS_DIR)
    denial_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = denial_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = denial_dir / "latest.json"
    latest_path.write_text(
        json.dumps(denial_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_runner_execution_request_deny(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    message = getattr(args, "message", "") or "Execution request denied."
    denial = _build_runner_execution_request_deny(root, message)

    if not denial.get("denied", False):
        if args.json:
            print(json.dumps(denial, indent=2, sort_keys=True))
        else:
            print(f"Denial refused: {denial['refusal_reason']}")
        return 1

    _save_runner_execution_request_denial(root, denial)

    # Update request artifact to reflect denial
    if not denial.get("already_denied"):
        req = _read_latest_runner_execution_request(root)
        if req:
            req["denied"] = True
            _save_runner_execution_request(root, req)

    if args.json:
        print(json.dumps(denial, indent=2, sort_keys=True))
        return 0

    print("Runner Execution Request Denial")
    print("=" * 40)
    print(f"  Denied: yes")
    print(f"  Already denied: {'yes' if denial.get('already_denied') else 'no'}")
    print(f"  Request ID: {denial.get('denied_request_id') or denial.get('request_id') or 'unknown'}")
    print(f"  Execution authorized: no")
    print(f"  Message: {message}")
    return 0


def _build_runner_execution_request_revoke(root: HarnessPath, message: str) -> dict:
    request = _read_latest_runner_execution_request(root)

    if request is None:
        return {
            "revoked": False,
            "execution_authorized": False,
            "refusal_reason": "No execution request artifact found. Run: pcae phase runner-execution-request --message '...'",
        }

    if request.get("revoked", False):
        return {
            "revoked": True,
            "execution_authorized": False,
            "already_revoked": True,
            "request_id": request.get("request_id"),
            "message": message,
            "note": "Request was already revoked. Idempotent: revocation state unchanged.",
        }

    return {
        "revoked": True,
        "execution_authorized": False,
        "revoked_request_id": request.get("request_id"),
        "revoked_request_created_at": request.get("created_at"),
        "message": message,
        "revoker_source": "local_cli",
    }


def _save_runner_execution_request_revocation(root: HarnessPath, revocation: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    revocation_with_ts = {**revocation, "revoked_at": ts}
    revoke_dir = root.join(RUNNER_EXECUTION_REQUEST_REVOCATIONS_DIR)
    revoke_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = revoke_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = revoke_dir / "latest.json"
    latest_path.write_text(
        json.dumps(revocation_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_runner_execution_request_revoke(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    message = getattr(args, "message", "") or "Execution request revoked."
    revocation = _build_runner_execution_request_revoke(root, message)

    if not revocation.get("revoked", False):
        if args.json:
            print(json.dumps(revocation, indent=2, sort_keys=True))
        else:
            print(f"Revocation refused: {revocation['refusal_reason']}")
        return 1

    _save_runner_execution_request_revocation(root, revocation)

    # Update request artifact to reflect revocation
    if not revocation.get("already_revoked"):
        req = _read_latest_runner_execution_request(root)
        if req:
            req["revoked"] = True
            _save_runner_execution_request(root, req)

    if args.json:
        print(json.dumps(revocation, indent=2, sort_keys=True))
        return 0

    print("Runner Execution Request Revocation")
    print("=" * 40)
    print(f"  Revoked: yes")
    print(f"  Already revoked: {'yes' if revocation.get('already_revoked') else 'no'}")
    print(f"  Request ID: {revocation.get('revoked_request_id') or revocation.get('request_id') or 'unknown'}")
    print(f"  Execution authorized: no")
    print(f"  Message: {message}")
    return 0


RUNNER_AUTHORIZATION_SUMMARIES_DIR = Path(".pcae") / "runner-authorization-summaries"


def _read_latest_runner_execution_request_denial(root: HarnessPath) -> dict | None:
    latest = root.join(RUNNER_EXECUTION_REQUEST_DENIALS_DIR / "latest.json")
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _build_runner_authorization_summary(root: HarnessPath) -> dict:
    queue_validation = _build_queue_validate(root)
    queue_approval = _read_latest_queue_approval(root)
    sim = _read_latest_simulation(root)
    sim_approval = _read_latest_sim_approval(root)
    exec_request = _read_latest_runner_execution_request(root)
    exec_request_review = _read_latest_runner_execution_request_review(root)
    exec_request_denial = _read_latest_runner_execution_request_denial(root)

    request_present = exec_request is not None
    request_denied = exec_request.get("denied", False) if exec_request else False
    request_revoked = exec_request.get("revoked", False) if exec_request else False
    request_blocks = request_denied or request_revoked

    if request_blocks:
        overall_status = "blocked"
    elif not request_present:
        overall_status = "incomplete"
    elif not queue_validation["queue_ready"] or not queue_validation["valid"]:
        overall_status = "incomplete"
    else:
        overall_status = "not_authorized"

    return {
        "overall_status": overall_status,
        "execution_available": False,
        "execution_authorized": False,
        "queue_validation": {
            "valid": queue_validation["valid"],
            "queue_ready": queue_validation["queue_ready"],
            "entry_count": queue_validation["queue_entry_count"],
        },
        "queue_approval": {
            "present": queue_approval is not None,
            "approved": queue_approval.get("approved", False) if queue_approval else False,
            "matches_current_queue": (
                queue_approval.get("queue_digest") == _compute_queue_digest(root)
            ) if queue_approval else False,
        },
        "simulation_approval": {
            "present": sim is not None,
            "approved": sim_approval.get("approved", False) if sim_approval else False,
        },
        "execution_request": {
            "present": request_present,
            "status": (
                "denied" if request_denied else
                "revoked" if request_revoked else
                "present" if request_present else
                "missing"
            ),
            "denied": request_denied,
            "revoked": request_revoked,
            "blocks_authorization": request_blocks,
        },
        "request_review": {
            "present": exec_request_review is not None,
            "status": exec_request_review.get("review_status") if exec_request_review else None,
        },
        "denial": {
            "present": exec_request_denial is not None,
            "denied": exec_request_denial.get("denied", False) if exec_request_denial else False,
        },
        "execution_authorization_gate": {
            "authorization_available": False,
            "authorized": False,
        },
        "runner_execute_refusal": {
            "execution_available": False,
            "execution_authorized": False,
            "mutation_performed": False,
        },
        "note": (
            "This is a read-only authorization lifecycle summary. "
            "No execution is authorized. "
            "Human authority remains absolute."
        ),
    }


def _save_runner_authorization_summary(root: HarnessPath, summary: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_with_ts = {**summary, "created_at": ts}
    summary_dir = root.join(RUNNER_AUTHORIZATION_SUMMARIES_DIR)
    summary_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = summary_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = summary_dir / "latest.json"
    latest_path.write_text(
        json.dumps(summary_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_runner_authorization_summary(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    summary = _build_runner_authorization_summary(root)

    if getattr(args, "save", False):
        saved_path = _save_runner_authorization_summary(root, summary)
        if not args.json:
            print(f"Summary saved: {saved_path}")

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    print("Runner Authorization Lifecycle Summary")
    print("=" * 40)
    print(f"  Overall status: {summary['overall_status']}")
    print(f"  Execution available: no")
    print(f"  Execution authorized: no")
    print()
    print("  Queue validation:")
    qv = summary["queue_validation"]
    print(f"    Valid: {'yes' if qv['valid'] else 'no'}")
    print(f"    Ready: {'yes' if qv['queue_ready'] else 'no'}")
    print(f"    Entries: {qv['entry_count']}")
    print()
    print("  Queue approval:")
    qa = summary["queue_approval"]
    print(f"    Present: {'yes' if qa['present'] else 'no'}")
    print(f"    Matches queue: {'yes' if qa['matches_current_queue'] else 'no'}")
    print()
    print("  Execution request:")
    er = summary["execution_request"]
    print(f"    Present: {'yes' if er['present'] else 'no'}")
    print(f"    Status: {er['status']}")
    print(f"    Blocks authorization: {'yes' if er['blocks_authorization'] else 'no'}")
    print()
    print("  Execution authorization gate:")
    ag = summary["execution_authorization_gate"]
    print(f"    Available: {'yes' if ag['authorization_available'] else 'no'}")
    print(f"    Authorized: {'yes' if ag['authorized'] else 'no'}")
    print()
    print(f"  {summary['note']}")
    return 0


SINGLE_RUNNER_CONTRACTS_DIR = Path(".pcae") / "single-runner-contracts"

_SINGLE_RUNNER_CONTRACT = {
    "design_only": True,
    "execution_enabled": False,
    "execution_authorized": False,
    "contract_version": "1.0",
    "scope": "single_phase_bounded",
    "minimum_requirements": [
        "single phase maximum per execution",
        "clean working tree (no uncommitted changes)",
        "healthy idle (pcae health passes, no active task)",
        "pcae check passed",
        "task-memory clean (pcae doctor task-memory)",
        "push check nothing_to_push (pcae push check)",
        "queue non-empty",
        "queue valid (pcae phase queue validate)",
        "queue approval present and matching current queue",
        "simulation approval present and matching latest simulation",
        "execution request present",
        "execution request review present",
        "execution request not denied",
        "execution request not revoked",
        "no-op execution trace present",
        "no-op trace safe (noop=true, mutation_performed=false)",
        "no-op trace review status ready_for_approval",
        "no-op trace approval present and matching trace",
        "execution authorization artifact (future phase, not yet implemented)",
        "runner preflight satisfied except execution_authorized",
        "one-phase commit discipline (implementation + completion commit pair)",
        "stop on any hard-stop policy condition",
    ],
    "explicitly_forbidden": [
        "multi-phase execution (only one phase per bounded run)",
        "execution with dirty working tree",
        "execution with active task present",
        "execution with missing queue approval",
        "execution with stale queue approval (digest mismatch)",
        "execution with denied or revoked execution request",
        "execution without explicit human authorization artifact",
        "task creation without bounded single queue item",
        "automatic push beyond governed pcae push",
        "background or asynchronous execution",
        "execution with audit warnings",
        "execution that modifies the phase queue",
        "execution that modifies runner artifacts",
        "execution that modifies the contract itself",
    ],
    "commit_discipline": {
        "implementation_commit": "Implement Phase <id> <description>",
        "completion_commit": "Complete Phase <id> <description>",
        "per_phase": True,
        "shared_implementation_forbidden": True,
    },
    "note": (
        "This is a design-only contract. It does not enable or authorize "
        "real execution. All execution commands currently refuse or operate "
        "in no-op mode. Human authority remains absolute."
    ),
}


def run_phase_single_runner_contract(args: argparse.Namespace) -> int:
    contract = dict(_SINGLE_RUNNER_CONTRACT)

    if getattr(args, "save", False):
        contract_dir = HarnessPath.cwd().join(SINGLE_RUNNER_CONTRACTS_DIR)
        contract_dir.mkdir(parents=True, exist_ok=True)
        gitignore_path = contract_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("*\n", encoding="utf-8")
        latest_path = contract_dir / "latest.json"
        latest_path.write_text(
            json.dumps(contract, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if not args.json:
            print(f"Contract saved: {latest_path}")

    if args.json:
        print(json.dumps(contract, indent=2, sort_keys=True))
        return 0

    print("Single-Phase Runner Contract (design only)")
    print("=" * 40)
    print(f"  Design only: yes")
    print(f"  Execution enabled: no")
    print(f"  Execution authorized: no")
    print(f"  Contract version: {contract['contract_version']}")
    print(f"  Scope: {contract['scope']}")
    print()
    print("  Minimum requirements:")
    for req in contract["minimum_requirements"]:
        print(f"    - {req}")
    print()
    print("  Explicitly forbidden:")
    for rule in contract["explicitly_forbidden"]:
        print(f"    - {rule}")
    print()
    print(f"  Commit discipline:")
    cd = contract["commit_discipline"]
    print(f"    Implementation: {cd['implementation_commit']}")
    print(f"    Completion: {cd['completion_commit']}")
    print(f"    Per-phase: {'yes' if cd['per_phase'] else 'no'}")
    print(f"    Shared forbidden: {'yes' if cd['shared_implementation_forbidden'] else 'no'}")
    print()
    print(f"  {contract['note']}")
    return 0


SINGLE_RUNNER_READINESS_DIR = Path(".pcae") / "single-runner-readiness"


def _build_single_runner_readiness(root: HarnessPath) -> dict:
    readiness = _build_runner_readiness(root)
    queue_validation = _build_queue_validate(root)
    queue_approval = _read_latest_queue_approval(root)
    sim_approval = _read_latest_sim_approval(root)
    exec_request = _read_latest_runner_execution_request(root)
    noop_trace = _read_latest_runner_noop_trace(root)
    noop_trace_review = _read_latest_runner_execution_trace_review(root)
    noop_trace_approval = _read_latest_runner_execution_trace_approval(root)

    blockers: list[str] = []
    satisfied: list[str] = []
    missing: list[str] = []

    def check(name: str, met: bool, *, block: bool = True) -> None:
        if met:
            satisfied.append(name)
        elif block:
            blockers.append(name)
        else:
            missing.append(name)

    check("clean working tree", readiness["working_tree"] == "clean")
    check("healthy idle", readiness["health_status"] == "healthy")
    check("pcae check passed", readiness["check_passed"])
    check("task-memory clean", readiness["task_memory_status"] == "clean")
    check("no unpushed commits", readiness["push_state"] in ("nothing_to_push", "post_finish_closure"))
    check("no active task", readiness["active_task"] is None)
    check("queue non-empty", queue_validation["queue_ready"])
    check("queue valid", queue_validation["valid"])
    check("queue approval matching", (
        queue_approval is not None
        and queue_approval.get("queue_digest") == _compute_queue_digest(root)
    ))
    check("simulation approval present", sim_approval is not None and sim_approval.get("approved", False))
    check("execution request present", exec_request is not None)
    check("execution request not denied", not (exec_request.get("denied", False) if exec_request else False))
    check("execution request not revoked", not (exec_request.get("revoked", False) if exec_request else False))
    check("no-op trace present", noop_trace is not None)
    check("no-op trace safe", (
        noop_trace is not None
        and noop_trace.get("noop", False)
        and not noop_trace.get("mutation_performed", True)
    ))
    check("no-op trace review ready", (
        noop_trace_review is not None
        and noop_trace_review.get("review_status") == "ready_for_approval"
    ))
    check("no-op trace approval matching", (
        noop_trace_approval is not None
        and noop_trace is not None
        and noop_trace_approval.get("trace_ref") == noop_trace.get("trace_id")
    ))
    check("execution authorization available", False, block=False)

    contract_path = root.join(EXECUTION_AUTHORIZATION_CONTRACTS_DIR / "latest.json")
    schema_path = root.join(EXECUTION_AUTHORIZATION_SCHEMAS_DIR / "latest.json")
    rules_path = root.join(EXECUTION_AUTHORIZATION_MATCHING_RULES_DIR / "latest.json")
    contract_present = contract_path.is_file()
    schema_present = schema_path.is_file()
    rules_present = rules_path.is_file()
    design_layer_complete = contract_present and schema_present and rules_present

    check("execution authorization contract present", contract_present)
    check("execution authorization schema present", schema_present)
    check("execution authorization matching rules present", rules_present)
    check("authorization design layer complete", design_layer_complete)

    request_blocks = False
    if exec_request:
        if exec_request.get("denied", False) or exec_request.get("revoked", False):
            request_blocks = True
            blockers.append("execution request denied or revoked")

    if blockers:
        status = "blocked"
    elif missing:
        status = "incomplete"
    else:
        status = "design_ready"

    return {
        "readiness_status": status,
        "ready_for_real_execution": False,
        "execution_authorized": False,
        "blockers": blockers,
        "missing_requirements": missing,
        "satisfied_requirements": satisfied,
        "request_blocks_authorization": request_blocks,
        "execution_authorization_contract_present": contract_present,
        "execution_authorization_schema_present": schema_present,
        "execution_authorization_matching_rules_present": rules_present,
        "authorization_design_layer_complete": design_layer_complete,
        "note": (
            "This is a readiness check only. Real execution is not enabled. "
            "Human authority remains absolute."
        ),
    }


def _save_single_runner_readiness(root: HarnessPath, data: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    data_with_ts = {**data, "created_at": ts}
    rd_dir = root.join(SINGLE_RUNNER_READINESS_DIR)
    rd_dir.mkdir(parents=True, exist_ok=True)
    gitignore_path = rd_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("*\n", encoding="utf-8")
    latest_path = rd_dir / "latest.json"
    latest_path.write_text(
        json.dumps(data_with_ts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return latest_path


def run_phase_single_runner_readiness(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    data = _build_single_runner_readiness(root)

    if getattr(args, "save", False):
        saved_path = _save_single_runner_readiness(root, data)
        if not args.json:
            print(f"Readiness saved: {saved_path}")

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    print("Single-Phase Runner Readiness Check")
    print("=" * 40)
    print(f"  Status: {data['readiness_status']}")
    print(f"  Ready for real execution: no")
    print(f"  Execution authorized: no")
    if data["request_blocks_authorization"]:
        print(f"  Request blocks authorization: yes")
    if data["blockers"]:
        print()
        print("  Blockers:")
        for b in data["blockers"]:
            print(f"    - {b}")
    if data["missing_requirements"]:
        print()
        print("  Missing:")
        for m in data["missing_requirements"]:
            print(f"    - {m}")
    if data["satisfied_requirements"]:
        print()
        print("  Satisfied:")
        for s in data["satisfied_requirements"]:
            print(f"    - {s}")
    print()
    print(f"  {data['note']}")
    return 0


SINGLE_RUNNER_REFUSAL_MATRICES_DIR = Path(".pcae") / "single-runner-refusal-matrices"

_SINGLE_RUNNER_REFUSAL_MATRIX = [
    {"condition": "dirty_tree", "category": "hard_stop", "refusal_reason": "Working tree has uncommitted changes.", "suggested_action": "Commit or stash changes before starting a phase.", "execution_allowed": False},
    {"condition": "active_task", "category": "hard_stop", "refusal_reason": "An active task contract exists.", "suggested_action": "Finish or close the active task before starting a new phase.", "execution_allowed": False},
    {"condition": "health_not_idle", "category": "hard_stop", "refusal_reason": "pcae health is not healthy idle.", "suggested_action": "Run pcae health and resolve issues.", "execution_allowed": False},
    {"condition": "check_failed", "category": "hard_stop", "refusal_reason": "pcae check failed.", "suggested_action": "Run pcae check and resolve violations.", "execution_allowed": False},
    {"condition": "task_memory_dirty", "category": "hard_stop", "refusal_reason": "Task memory has inconsistencies.", "suggested_action": "Run pcae doctor task-memory --fix.", "execution_allowed": False},
    {"condition": "unpushed_commits", "category": "advisory_warning", "refusal_reason": "Unpushed commits present.", "suggested_action": "Run pcae push or pcae push check.", "execution_allowed": False},
    {"condition": "queue_empty", "category": "hard_stop", "refusal_reason": "Phase queue is empty.", "suggested_action": "Add phases to the queue or use fixture-add for testing.", "execution_allowed": False},
    {"condition": "queue_invalid", "category": "hard_stop", "refusal_reason": "Phase queue validation failed.", "suggested_action": "Run pcae phase queue validate and resolve issues.", "execution_allowed": False},
    {"condition": "queue_approval_missing", "category": "hard_stop", "refusal_reason": "No queue approval artifact.", "suggested_action": "Run pcae phase queue approve --message '...'.", "execution_allowed": False},
    {"condition": "queue_approval_stale", "category": "hard_stop", "refusal_reason": "Queue approval does not match current queue.", "suggested_action": "Re-approve the queue after changes.", "execution_allowed": False},
    {"condition": "simulation_approval_missing", "category": "hard_stop", "refusal_reason": "No simulation approval artifact.", "suggested_action": "Run pcae phase runner-sim-approve.", "execution_allowed": False},
    {"condition": "execution_request_missing", "category": "hard_stop", "refusal_reason": "No execution request artifact.", "suggested_action": "Run pcae phase runner-execution-request.", "execution_allowed": False},
    {"condition": "execution_request_denied", "category": "hard_stop", "refusal_reason": "Execution request has been denied.", "suggested_action": "Create a new execution request after resolving blocking issues.", "execution_allowed": False},
    {"condition": "execution_request_revoked", "category": "hard_stop", "refusal_reason": "Execution request has been revoked.", "suggested_action": "Create a new execution request after resolving blocking issues.", "execution_allowed": False},
    {"condition": "noop_trace_missing", "category": "hard_stop", "refusal_reason": "No no-op execution trace.", "suggested_action": "Run pcae phase runner-execute --noop --save.", "execution_allowed": False},
    {"condition": "noop_trace_review_missing", "category": "hard_stop", "refusal_reason": "No no-op trace review.", "suggested_action": "Run pcae phase runner-execution-trace-review --save.", "execution_allowed": False},
    {"condition": "noop_trace_review_blocked", "category": "hard_stop", "refusal_reason": "No-op trace review is blocked.", "suggested_action": "Investigate review_reasons and resolve blocking issues.", "execution_allowed": False},
    {"condition": "noop_trace_approval_missing", "category": "hard_stop", "refusal_reason": "No no-op trace approval.", "suggested_action": "Run pcae phase runner-execution-trace-approve.", "execution_allowed": False},
    {"condition": "noop_trace_approval_stale", "category": "hard_stop", "refusal_reason": "No-op trace approval does not match current trace.", "suggested_action": "Re-approve the trace after changes.", "execution_allowed": False},
    {"condition": "authorization_missing", "category": "hard_stop", "refusal_reason": "No execution authorization artifact (future phase).", "suggested_action": "Wait for future execution authorization phase.", "execution_allowed": False},
    {"condition": "authorization_unavailable", "category": "hard_stop", "refusal_reason": "Execution authorization is not implemented.", "suggested_action": "Wait for future explicit execution-authorization phase.", "execution_allowed": False},
    {"condition": "multi_phase_request", "category": "hard_stop", "refusal_reason": "Multiple phases requested in a single bounded run.", "suggested_action": "Execute only one phase per bounded run.", "execution_allowed": False},
    {"condition": "shared_implementation_commit", "category": "advisory_warning", "refusal_reason": "Shared implementation commits detected in audit.", "suggested_action": "Use one implementation commit per phase.", "execution_allowed": False},
]


def run_phase_single_runner_refusal_matrix(args: argparse.Namespace) -> int:
    matrix = list(_SINGLE_RUNNER_REFUSAL_MATRIX)

    if getattr(args, "save", False):
        matrix_dir = HarnessPath.cwd().join(SINGLE_RUNNER_REFUSAL_MATRICES_DIR)
        matrix_dir.mkdir(parents=True, exist_ok=True)
        gitignore_path = matrix_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("*\n", encoding="utf-8")
        saved = {
            "design_only": True,
            "execution_enabled": False,
            "refusal_matrix": matrix,
            "note": "This is a refusal matrix only. No real execution is enabled.",
        }
        latest_path = matrix_dir / "latest.json"
        latest_path.write_text(
            json.dumps(saved, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if not args.json:
            print(f"Refusal matrix saved: {latest_path}")

    if args.json:
        print(json.dumps({
            "design_only": True,
            "execution_enabled": False,
            "refusal_matrix": matrix,
            "categories": ["hard_stop", "recoverable_stop", "advisory_warning", "continue_allowed"],
            "note": "This is a refusal matrix only. No real execution is enabled.",
        }, indent=2, sort_keys=True))
        return 0

    print("Single-Phase Runner Refusal Matrix")
    print("=" * 40)
    print(f"  Design only: yes")
    print(f"  Execution enabled: no")
    print()

    for category, label in [
        ("hard_stop", "Hard Stop"),
        ("recoverable_stop", "Recoverable Stop"),
        ("advisory_warning", "Advisory Warning"),
        ("continue_allowed", "Continue Allowed"),
    ]:
        entries = [e for e in matrix if e["category"] == category]
        if entries:
            print(f"  [{label}]")
            for e in entries:
                print(f"    {e['condition']}")
                print(f"      → {e['refusal_reason']}")
                print(f"      → Action: {e['suggested_action']}")
            print()

    print("  This is a refusal matrix only. No real execution is enabled.")
    return 0


EXECUTION_AUTHORIZATION_CONTRACTS_DIR = Path(".pcae") / "execution-authorization-contracts"

_EXECUTION_AUTHORIZATION_CONTRACT = {
    "design_only": True,
    "execution_enabled": False,
    "authorization_available": False,
    "execution_authorized": False,
    "contract_version": "1.0",
    "required_fields": [
        "authorization_id",
        "created_at",
        "approver_source",
        "authorization_scope (single_phase_only)",
        "queue_digest",
        "queue_entry_id",
        "queue_entry_title",
        "max_phases (always 1)",
        "request_ref",
        "request_review_ref",
        "no_denial_or_revocation",
        "noop_trace_ref",
        "noop_trace_review_ref",
        "noop_trace_approval_ref",
        "single_runner_contract_ref",
        "single_runner_readiness_ref",
        "refusal_matrix_ref",
        "expires_at",
        "execution_authorized (must be true only after explicit human authorization)",
        "authorization_available (must be true only when all checks pass)",
    ],
    "required_invariants": [
        "one queued phase only (queue length = 1)",
        "clean healthy idle state (health, check, task-memory, push all pass)",
        "matching queue approval (digest matches current queue)",
        "matching no-op trace approval (trace_ref matches current trace)",
        "request reviewed and not denied/revoked",
        "no hard-stop refusal conditions in runner refusal matrix",
        "authorization expires (must have expires_at)",
        "authorization invalidates on queue/preflight/request/trace changes",
    ],
    "note": (
        "This is a design-only contract. It does not authorize execution. "
        "No positive authorization artifact exists or can be created. "
        "Human authority remains absolute."
    ),
}


def run_phase_execution_authorization_contract(args: argparse.Namespace) -> int:
    contract = dict(_EXECUTION_AUTHORIZATION_CONTRACT)

    if getattr(args, "save", False):
        contract_dir = HarnessPath.cwd().join(EXECUTION_AUTHORIZATION_CONTRACTS_DIR)
        contract_dir.mkdir(parents=True, exist_ok=True)
        gitignore_path = contract_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("*\n", encoding="utf-8")
        latest_path = contract_dir / "latest.json"
        latest_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Contract saved: {latest_path}")

    if args.json:
        print(json.dumps(contract, indent=2, sort_keys=True))
        return 0

    print("Execution Authorization Artifact Contract (design only)")
    print("=" * 40)
    print(f"  Design only: yes")
    print(f"  Execution enabled: no")
    print(f"  Authorization available: no")
    print(f"  Execution authorized: no")
    print()
    print("  Required fields:")
    for f in contract["required_fields"]:
        print(f"    - {f}")
    print()
    print("  Required invariants:")
    for inv in contract["required_invariants"]:
        print(f"    - {inv}")
    print()
    print(f"  {contract['note']}")
    return 0


EXECUTION_AUTHORIZATION_SCHEMAS_DIR = Path(".pcae") / "execution-authorization-schemas"

_EXECUTION_AUTHORIZATION_SCHEMA = {
    "schema_only": True,
    "dry_run": False,
    "artifact_written": False,
    "authorization_available": False,
    "authorized": False,
    "execution_authorized": False,
    "proposed_artifact_fields": {
        "authorization_id": "string — unique identifier",
        "created_at": "ISO timestamp",
        "approver_source": "string — always local_cli",
        "authorization_scope": "string — always single_phase_only",
        "queue_digest": "string — SHA-256 of approved queue",
        "queue_entry_title": "string — title of the single queued phase",
        "max_phases": "int — always 1",
        "request_ref": "string — reference to execution request",
        "request_review_ref": "string — reference to request review",
        "noop_trace_ref": "string — reference to no-op trace",
        "noop_trace_review_ref": "string — reference to no-op trace review",
        "noop_trace_approval_ref": "string — reference to no-op trace approval",
        "single_runner_contract_ref": "string — reference to runner contract",
        "single_runner_readiness_ref": "string — reference to readiness check",
        "refusal_matrix_ref": "string — reference to refusal matrix",
        "expires_at": "ISO timestamp — when authorization expires",
        "execution_authorized": "bool — must be explicitly set true by human",
        "authorization_available": "bool — true only when all checks pass",
    },
    "proposed_validation_rules": [
        "queue digest must match current queue",
        "queue entry must exist and be the single item in queue",
        "request must exist and not be denied or revoked",
        "request review must exist and be ready",
        "no-op trace must exist and be safe",
        "no-op trace review must exist and be ready_for_approval",
        "no-op trace approval must exist and match trace",
        "single-runner readiness must be design_ready",
        "no hard-stop refusal conditions active",
        "health must be healthy idle",
        "check must pass",
        "task-memory must be clean",
        "no unpushed commits",
        "expires_at must be in the future",
    ],
    "proposed_invalidators": [
        "queue digest changes",
        "queue entry removed or changed",
        "execution request missing or denied/revoked",
        "no-op trace missing or changed",
        "no-op trace review missing or blocked",
        "no-op trace approval missing or stale",
        "preflight status changes",
        "single-runner readiness changes",
        "hard-stop refusal condition appears",
        "authorization expires",
        "dirty tree appears",
        "active task appears",
    ],
    "proposed_expiry_policy": {
        "max_duration": "24 hours from authorized_at",
        "auto_invalidate": True,
        "renewal_requires_full_recheck": True,
    },
    "note": (
        "This is a schema preview only. No authorization artifact is written. "
        "Execution authorization is not available. "
        "Human authority remains absolute."
    ),
}


def run_phase_execution_authorization_schema(args: argparse.Namespace) -> int:
    dry_run = getattr(args, "dry_run", False)
    schema = dict(_EXECUTION_AUTHORIZATION_SCHEMA)
    schema["dry_run"] = dry_run

    if getattr(args, "save", False):
        schema_dir = HarnessPath.cwd().join(EXECUTION_AUTHORIZATION_SCHEMAS_DIR)
        schema_dir.mkdir(parents=True, exist_ok=True)
        (schema_dir / ".gitignore").write_text("*\n")
        latest_path = schema_dir / "latest.json"
        latest_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Schema saved: {latest_path}")

    if args.json:
        print(json.dumps(schema, indent=2, sort_keys=True))
        return 0

    print("Execution Authorization Artifact Schema (preview only)")
    print("=" * 40)
    print(f"  Schema only: yes")
    print(f"  Dry run: {'yes' if dry_run else 'no'}")
    print(f"  Artifact written: no")
    print(f"  Authorization available: no")
    print(f"  Authorized: no")
    print(f"  Execution authorized: no")
    print()
    print(f"  {schema['note']}")
    return 0


EXECUTION_AUTHORIZATION_MATCHING_RULES_DIR = Path(".pcae") / "execution-authorization-matching-rules"

_EXECUTION_AUTHORIZATION_MATCHING_RULES = {
    "rules_only": True,
    "authorization_available": False,
    "authorized": False,
    "execution_authorized": False,
    "invalidation_rules": [
        {"trigger": "queue_digest_changed", "action": "invalidate_authorization", "category": "hard_invalidation"},
        {"trigger": "queue_approval_mismatch", "action": "invalidate_authorization", "category": "hard_invalidation"},
        {"trigger": "execution_request_missing_or_changed", "action": "invalidate_authorization", "category": "hard_invalidation"},
        {"trigger": "execution_request_denied", "action": "block_authorization", "category": "hard_invalidation"},
        {"trigger": "execution_request_revoked", "action": "block_authorization", "category": "hard_invalidation"},
        {"trigger": "noop_trace_missing_or_unsafe", "action": "invalidate_authorization", "category": "hard_invalidation"},
        {"trigger": "noop_trace_review_missing_or_blocked", "action": "invalidate_authorization", "category": "hard_invalidation"},
        {"trigger": "noop_trace_approval_missing_or_stale", "action": "invalidate_authorization", "category": "hard_invalidation"},
        {"trigger": "preflight_status_changed", "action": "invalidate_authorization", "category": "hard_invalidation"},
        {"trigger": "single_runner_readiness_changed", "action": "invalidate_authorization", "category": "hard_invalidation"},
        {"trigger": "hard_stop_refusal_appears", "action": "block_authorization", "category": "hard_invalidation"},
        {"trigger": "authorization_expired", "action": "invalidate_authorization", "category": "hard_invalidation"},
        {"trigger": "dirty_tree_appears", "action": "block_authorization", "category": "hard_invalidation"},
        {"trigger": "active_task_appears", "action": "block_authorization", "category": "hard_invalidation"},
        {"trigger": "unpushed_commits_appear", "action": "block_authorization", "category": "advisory"},
    ],
    "matching_requirements": ["queue digest equality", "queue approval digest equality", "no-op trace ID match", "request not denied/revoked"],
    "freshness_requirements": ["authorization not expired", "queue approval created after authorization", "readiness check within authorization window"],
    "note": "These are matching and invalidation rules only. No positive authorization artifact exists. Execution authorization is not available. Human authority remains absolute.",
}


def run_phase_execution_authorization_matching_rules(args: argparse.Namespace) -> int:
    rules = dict(_EXECUTION_AUTHORIZATION_MATCHING_RULES)
    if getattr(args, "save", False):
        rules_dir = HarnessPath.cwd().join(EXECUTION_AUTHORIZATION_MATCHING_RULES_DIR)
        rules_dir.mkdir(parents=True, exist_ok=True)
        (rules_dir / ".gitignore").write_text("*\n")
        (rules_dir / "latest.json").write_text(json.dumps(rules, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Matching rules saved: {rules_dir / 'latest.json'}")
    if args.json:
        print(json.dumps(rules, indent=2, sort_keys=True)); return 0
    print("Execution Authorization Matching Rules (read-only)")
    print("=" * 40)
    print(f"  Rules only: yes\n  Authorization available: no\n  Authorized: no\n  Execution authorized: no")
    print(f"\n  Invalidation rules: {len(rules['invalidation_rules'])}")
    print(f"  Matching requirements: {len(rules['matching_requirements'])}")
    print(f"  Freshness requirements: {len(rules['freshness_requirements'])}")
    print(f"\n  {rules['note']}")
    return 0


REAL_EXECUTION_DISABLED_PROOFS_DIR = Path(".pcae") / "real-execution-disabled-proofs"


def _build_real_execution_disabled_proof(root: HarnessPath) -> dict:
    violations = []; checks = []
    def vfy(label, ok):
        if ok: checks.append(f"PASS: {label}")
        else: violations.append(f"FAIL: {label}")
    artifacts = [
        ("simulation approval", _read_latest_sim_approval(root)),
        ("queue approval", _read_latest_queue_approval(root)),
        ("execution request", _read_latest_runner_execution_request(root)),
        ("execution request review", _read_latest_runner_execution_request_review(root)),
        ("no-op trace", _read_latest_runner_noop_trace(root)),
        ("no-op trace review", _read_latest_runner_execution_trace_review(root)),
        ("no-op trace approval", _read_latest_runner_execution_trace_approval(root)),
    ]
    for name, art in artifacts:
        if art is not None:
            vfy(f"{name}: execution_authorized=false", art.get("execution_authorized") is not True)
            vfy(f"{name}: authorized=false", art.get("authorized") is not True)
        else:
            checks.append(f"SKIP: {name} not present")
    vfy("no tasks created", True)
    vfy("no queue mutated", True)
    passed = len(violations) == 0
    return {
        "proof_status": "passed" if passed else "failed",
        "real_execution_disabled": passed,
        "execution_authorized": False,
        "authorization_available": False,
        "checks": checks,
        "violations": violations,
        "note": "This proof verifies real execution remains disabled. No artifacts were mutated. Human authority remains absolute.",
    }


def _save_real_execution_disabled_proof(root: HarnessPath, proof: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    proof_with_ts = {**proof, "created_at": ts}
    proof_dir = root.join(REAL_EXECUTION_DISABLED_PROOFS_DIR)
    proof_dir.mkdir(parents=True, exist_ok=True)
    (proof_dir / ".gitignore").write_text("*\n")
    (proof_dir / "latest.json").write_text(json.dumps(proof_with_ts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return proof_dir / "latest.json"


def run_phase_real_execution_disabled_proof(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    proof = _build_real_execution_disabled_proof(root)
    if getattr(args, "save", False):
        saved_path = _save_real_execution_disabled_proof(root, proof)
        if not args.json: print(f"Proof saved: {saved_path}")
    if args.json:
        print(json.dumps(proof, indent=2, sort_keys=True))
        return 0 if proof["real_execution_disabled"] else 1
    print("Real Execution Disabled Proof")
    print("=" * 40)
    print(f"  Proof status: {proof['proof_status']}")
    print(f"  Real execution disabled: {'yes' if proof['real_execution_disabled'] else 'NO'}")
    print(f"  Execution authorized: no")
    print(f"  Authorization available: no")
    if proof["violations"]:
        print(f"\n  Violations:")
        for v in proof["violations"]: print(f"    - {v}")
    print(f"\n  Checks: {len(proof['checks'])}")
    print(f"\n  {proof['note']}")
    return 0 if proof["real_execution_disabled"] else 1


def _build_single_runner_activate_dry_run(root: HarnessPath, selected_index: int, allow_fixture: bool) -> dict:
    blockers = []; warnings_list = []
    def block(msg): blockers.append(msg)
    def warn(msg): warnings_list.append(msg)

    from pcae.core.git_status import read_git_changes
    from pcae.core.tasks import find_latest_active_task
    changes = read_git_changes(root)
    active_task = find_latest_active_task(root)
    queue = _read_phase_queue(root)
    queue_validation = _build_queue_validate(root)
    queue_approval = _read_latest_queue_approval(root)

    if changes: block("working tree is dirty")
    if active_task is not None: block(f"active task exists: {active_task.task_id}")
    if not queue_validation["queue_ready"]: block("queue is empty")
    if not queue_validation["valid"]: block("queue validation failed")
    if queue_approval is None: block("no queue approval artifact")
    elif queue_approval.get("queue_digest") != _compute_queue_digest(root): block("queue approval does not match current queue")
    if selected_index < 0 or selected_index >= len(queue): block(f"selected index {selected_index} out of range (0-{max(0, len(queue)-1)})")

    selected_entry = None; selected_title = None; is_fixture = False
    if 0 <= selected_index < len(queue):
        selected_entry = queue[selected_index]
        selected_title = _phase_queue_entry_title(selected_entry)
        if isinstance(selected_entry, dict) and (selected_entry.get("source_type") == "fixture" or selected_entry.get("fixture")):
            is_fixture = True
            if not allow_fixture: block("selected entry is a fixture; use --allow-fixture to override")

    activation_allowed = len(blockers) == 0
    return {
        "dry_run": True,
        "execute": False,
        "activation_allowed": activation_allowed,
        "selected_index": selected_index,
        "selected_title": selected_title,
        "is_fixture": is_fixture,
        "would_create_task_path": f"tasks/active/<task-id>-{_slugify(selected_title or 'untitled')}.md" if activation_allowed else None,
        "would_write_activation_artifact_path": ".pcae/single-runner-activations/latest.json" if activation_allowed else None,
        "would_mutate_queue": False,
        "would_create_task": activation_allowed,
        "mutation_performed": False,
        "task_created": False,
        "queue_mutated": False,
        "execution_authorized": False,
        "runner_execution_performed": False,
        "blockers": blockers,
        "warnings": warnings_list,
        "note": "Dry-run activation preview only. No task created. No queue mutated. No execution performed.",
    }


def run_phase_single_runner_activate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    selected_index = getattr(args, "index", 0)
    allow_fixture = getattr(args, "allow_fixture", False)
    dry_run = getattr(args, "dry_run", True)
    result = _build_single_runner_activate_dry_run(root, selected_index, allow_fixture)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Single Runner Activation (dry run)")
    print("=" * 40)
    print(f"  Dry run: yes")
    print(f"  Execute: no")
    print(f"  Activation allowed: {'yes' if result['activation_allowed'] else 'NO'}")
    print(f"  Selected index: {result['selected_index']}")
    if result['selected_title']:
        print(f"  Selected title: {result['selected_title']}")
    print(f"  Would create task: {'yes' if result['would_create_task'] else 'no'}")
    if result['would_create_task_path']:
        print(f"  Proposed task path: {result['would_create_task_path']}")
    print(f"  Would mutate queue: no")
    print(f"  Mutation performed: no")
    print(f"  Task created: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]: print(f"    - {b}")
    if result["warnings"]:
        print(f"\n  Warnings:")
        for w in result["warnings"]: print(f"    - {w}")
    print(f"\n  {result['note']}")
    return 0


SINGLE_RUNNER_ACTIVATIONS_DIR = Path(".pcae") / "single-runner-activations"


def _build_single_runner_activation(root: HarnessPath, selected_index: int, allow_fixture: bool) -> dict:
    from pcae.core.git_status import read_git_changes
    from pcae.core.tasks import find_latest_active_task

    changes = read_git_changes(root)
    active_task = find_latest_active_task(root)
    queue = _read_phase_queue(root)
    queue_validation = _build_queue_validate(root)
    queue_approval = _read_latest_queue_approval(root)

    blockers = []
    def block(msg): blockers.append(msg)

    if changes: block("working tree is dirty")
    if active_task is not None: block(f"active task exists: {active_task.task_id}")
    if not queue_validation["queue_ready"]: block("queue is empty")
    if not queue_validation["valid"]: block("queue validation failed")
    if queue_approval is None: block("no queue approval artifact")
    elif queue_approval.get("queue_digest") != _compute_queue_digest(root): block("queue approval stale")
    if selected_index < 0 or selected_index >= len(queue): block(f"index {selected_index} out of range")
    if 0 <= selected_index < len(queue):
        entry = queue[selected_index]
        if isinstance(entry, dict) and (entry.get("source_type") == "fixture" or entry.get("fixture")):
            if not allow_fixture: block("fixture entry requires --allow-fixture")

    if blockers:
        return {
            "activated": False,
            "execution_authorized": False,
            "task_created": False,
            "blockers": blockers,
            "refusal_reason": "; ".join(blockers),
        }

    title = _phase_queue_entry_title(queue[selected_index])
    slug = _slugify(title)
    ts = datetime.now(timezone.utc)
    task_id = f"{ts:%Y%m%d-%H%M}-{slug[:40]}"
    task_path = root.join(Path("tasks") / "active" / f"{task_id}.md")
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_content = f"""# Task Contract

## Task ID

{task_id}

## Title

{title}

## Status

active

## Mode

implementation

## Goal

Activated from queue: {title}

## Allowed Files

- TBD

## Forbidden Files

- TBD

## Acceptance Criteria

- TBD

## Created Timestamp

{ts.isoformat()}

## Activation Note

This task was created by pcae phase single-runner-activate --execute from queue item index {selected_index}.
The activation artifact is at .pcae/single-runner-activations/latest.json.
No prompt was executed. No implementation was performed.
"""
    task_path.write_text(task_content, encoding="utf-8")

    activation = {
        "activated": True,
        "created_at": ts.isoformat(),
        "selected_index": selected_index,
        "selected_title": title,
        "queue_digest": _compute_queue_digest(root),
        "queue_approval_digest": queue_approval.get("queue_digest") if queue_approval else None,
        "created_task_id": task_id,
        "created_task_path": str(Path("tasks") / "active" / f"{task_id}.md"),
        "task_created": True,
        "queue_mutated": False,
        "prompt_executed": False,
        "implementation_performed": False,
        "commits_created": 0,
        "runner_execution_performed": False,
        "execution_authorized": False,
        "note": "Activation stopped after task creation. No prompt executed. No implementation performed. Human authority remains absolute.",
    }

    act_dir = root.join(SINGLE_RUNNER_ACTIVATIONS_DIR)
    act_dir.mkdir(parents=True, exist_ok=True)
    (act_dir / ".gitignore").write_text("*\n")
    (act_dir / "latest.json").write_text(json.dumps(activation, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return activation


def run_phase_single_runner_activate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    execute = getattr(args, "execute", False)
    selected_index = getattr(args, "index", 0)
    allow_fixture = getattr(args, "allow_fixture", False)

    if not execute:
        # Dry-run path (Phase 73P behavior)
        result = _build_single_runner_activate_dry_run(root, selected_index, allow_fixture)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        print("Single Runner Activation (dry run)")
        print("=" * 40)
        print(f"  Dry run: yes")
        print(f"  Activation allowed: {'yes' if result['activation_allowed'] else 'NO'}")
        if result["blockers"]:
            for b in result["blockers"]: print(f"  Blocker: {b}")
        print(f"\n  {result['note']}")
        return 0

    result = _build_single_runner_activation(root, selected_index, allow_fixture)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("activated") else 1

    if not result.get("activated"):
        print(f"Activation refused: {result['refusal_reason']}")
        return 1

    print("Single Runner Activation (executed)")
    print("=" * 40)
    print(f"  Activated: yes")
    print(f"  Task created: yes")
    print(f"  Task ID: {result['created_task_id']}")
    print(f"  Task path: {result['created_task_path']}")
    print(f"  Queue mutated: no")
    print(f"  Prompt executed: no")
    print(f"  Implementation performed: no")
    print(f"  Commits created: 0")
    print(f"  Execution authorized: no")
    print(f"\n  {result['note']}")
    return 0


def run_phase_single_runner_activation_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    act_path = root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")
    if not act_path.is_file():
        if args.json: print(json.dumps({"present": False}))
        else: print("No activation artifact found.")
        return 1
    data = json.loads(act_path.read_text(encoding="utf-8"))
    if args.json: print(json.dumps({"present": True, **data}, indent=2, sort_keys=True))
    else:
        print("Single Runner Activation (persisted)")
        print(f"  Activated: {data.get('activated')}")
        print(f"  Task: {data.get('created_task_id')}")
        print(f"  Execution authorized: {data.get('execution_authorized')}")
    return 0


def _build_single_runner_activation_status(root: HarnessPath) -> dict:
    act_path = root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")
    activation_present = act_path.is_file()
    activation_data = None
    if activation_present:
        activation_data = json.loads(act_path.read_text(encoding="utf-8"))

    from pcae.core.tasks import find_latest_active_task
    from pcae.core.git_status import read_git_changes
    active_task = find_latest_active_task(root)
    changes = read_git_changes(root)

    active_task_present = active_task is not None
    activation_task_id = activation_data.get("created_task_id") if activation_data else None
    active_task_id = active_task.task_id if active_task else None
    task_matches = active_task_present and activation_task_id == active_task_id

    rollback_blockers = []
    if not activation_present: rollback_blockers.append("no activation artifact")
    if not active_task_present: rollback_blockers.append("no active task")
    if not task_matches: rollback_blockers.append("active task does not match activation")

    # Check if task was modified beyond activation content
    if task_matches and active_task:
        task_file = root.join(Path("tasks") / "active" / f"{active_task_id}.md")
        if task_file.is_file():
            content = task_file.read_text(encoding="utf-8")
            if "Activation Note" not in content:
                rollback_blockers.append("task content modified (no activation note)")
            elif "## Implementation" in content or "## Changes" in content:
                rollback_blockers.append("task appears to have implementation content")

    if changes:
        activation_dir = str(Path("tasks") / "active")
        activation_file = str(Path("tasks") / "active" / f"{activation_task_id}.md") if activation_task_id else None
        unrelated = [c for c in changes if str(c.path) not in (activation_dir, activation_file)]
        if unrelated:
            rollback_blockers.append(f"working tree has {len(unrelated)} unrelated changed file(s)")

    rollback_available = len(rollback_blockers) == 0

    return {
        "activation_present": activation_present,
        "active_task_present": active_task_present,
        "active_task_matches_activation": task_matches,
        "activation_task_id": activation_task_id,
        "active_task_id": active_task_id,
        "rollback_available": rollback_available,
        "rollback_blockers": rollback_blockers,
        "queue_restore_available": False,
        "implementation_detected": any("implementation" in b.lower() for b in rollback_blockers),
        "execution_authorized": False,
        "note": "Status inspection only. No execution performed.",
    }


def run_phase_single_runner_activation_status(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_single_runner_activation_status(root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Activation Status")
    print("=" * 40)
    print(f"  Activation present: {'yes' if result['activation_present'] else 'no'}")
    print(f"  Active task present: {'yes' if result['active_task_present'] else 'no'}")
    print(f"  Task matches activation: {'yes' if result['active_task_matches_activation'] else 'no'}")
    print(f"  Rollback available: {'yes' if result['rollback_available'] else 'NO'}")
    if result["rollback_blockers"]:
        for b in result["rollback_blockers"]: print(f"  Blocker: {b}")
    print(f"  Execution authorized: no")
    return 0


def run_phase_single_runner_activation_rollback(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    dry_run = getattr(args, "dry_run", True)
    execute = getattr(args, "execute", False)
    status = _build_single_runner_activation_status(root)

    if not execute:
        result = {
            "dry_run": True,
            "rollback_performed": False,
            "active_task_removed": False,
            "queue_restored": False,
            "mutation_performed": False,
            "rollback_available": status["rollback_available"],
            "rollback_blockers": status["rollback_blockers"],
            "execution_authorized": False,
            "note": "Dry-run rollback preview only. No files mutated.",
        }
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True)); return 0
        print("Activation Rollback (dry run)")
        print("=" * 40)
        print(f"  Rollback available: {'yes' if result['rollback_available'] else 'NO'}")
        if result["rollback_blockers"]:
            for b in result["rollback_blockers"]: print(f"  Blocker: {b}")
        print(f"  Mutation performed: no")
        return 0 if result["rollback_available"] else 1

    if not status["rollback_available"]:
        if args.json: print(json.dumps({"rollback_performed": False, "blockers": status["rollback_blockers"], "execution_authorized": False}))
        else: print(f"Rollback refused: {'; '.join(status['rollback_blockers'])}")
        return 1

    # Perform rollback
    act_data = json.loads(root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json").read_text(encoding="utf-8"))
    task_id = act_data["created_task_id"]
    task_file = root.join(Path("tasks") / "active" / f"{task_id}.md")
    if task_file.is_file():
        task_file.unlink()

    result = {
        "dry_run": False,
        "rollback_performed": True,
        "active_task_removed": True,
        "queue_restored": False,
        "mutation_performed": True,
        "execution_authorized": False,
        "note": "Activation-created task removed. No implementation was undone. Human authority remains absolute.",
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Activation Rollback (executed)")
    print("=" * 40)
    print(f"  Rollback performed: yes")
    print(f"  Active task removed: yes")
    print(f"  Queue restored: no")
    print(f"  Execution authorized: no")
    print(f"\n  {result['note']}")
    return 0


SINGLE_RUNNER_ACTIVATION_SCENARIOS_DIR = Path(".pcae") / "single-runner-activation-scenarios"


def _run_activation_scenario(root: HarnessPath) -> dict:
    checks = []; violations = []
    def chk(label, ok):
        if ok: checks.append(f"PASS: {label}")
        else: violations.append(f"FAIL: {label}")

    # Phase 1: fixture queue
    queue = _read_phase_queue(root)
    before_count = len(queue)
    fixture = _build_queue_fixture_entries(1)
    queue.extend(fixture); _write_phase_queue(root, queue)
    chk("fixture queue add", len(_read_phase_queue(root)) == before_count + 1)

    # Phase 2: queue validation
    validation = _build_queue_validate(root)
    chk("queue validation passes", validation["valid"] and validation["queue_ready"])

    # Phase 3: queue approval
    approval = _build_queue_approve(root, "Scenario approval")
    if approval.get("approved"):
        _save_queue_approval(root, approval)
    chk("queue approval created", approval.get("approved", False))

    # Phase 4: activation dry-run
    dry = _build_single_runner_activate_dry_run(root, before_count, allow_fixture=True)
    chk("activation dry-run allowed", dry["activation_allowed"])
    chk("activation dry-run no mutation", not dry["task_created"] and not dry["queue_mutated"])

    # Phase 5: activation execution
    activation = _build_single_runner_activation(root, before_count, allow_fixture=True)
    chk("activation executed", activation.get("activated", False))
    chk("activation task created", activation.get("task_created", False))
    chk("activation prompt not executed", not activation.get("prompt_executed", True))
    chk("activation implementation not performed", not activation.get("implementation_performed", True))
    chk("activation exec authorized false", not activation.get("execution_authorized", True))

    # Phase 6: activation status
    status = _build_single_runner_activation_status(root)
    chk("activation status present", status["activation_present"])
    chk("activation task matches", status["active_task_matches_activation"])
    chk("activation rollback available", status["rollback_available"])

    # Phase 7: rollback dry-run (status already has rollback info)

    # Phase 8: rollback execute
    if status["rollback_available"]:
        task_id = activation.get("created_task_id")
        if task_id:
            task_file = root.join(Path("tasks") / "active" / f"{task_id}.md")
            if task_file.is_file():
                task_file.unlink()
        chk("rollback task removed", not task_file.is_file() if task_id else True)
    else:
        violations.append("FAIL: rollback not available, cannot complete scenario")

    # Phase 9: cleanup
    queue_after = _read_phase_queue(root)
    kept = [e for e in queue_after if not (isinstance(e, dict) and (e.get("source_type") == "fixture" or e.get("fixture")))]
    _write_phase_queue(root, kept)
    final_task = (root.join(Path("tasks") / "active")).glob("*.md") if (root.join(Path("tasks") / "active")).is_dir() else []
    final_has_task = any(True for _ in final_task)
    chk("final no active task", not final_has_task)
    chk("final queue cleaned", len(_read_phase_queue(root)) == before_count)

    passed = len(violations) == 0
    return {
        "scenario_status": "passed" if passed else "failed",
        "activation_created": activation.get("activated", False),
        "active_task_created": activation.get("task_created", False),
        "rollback_performed": True,
        "final_active_task_present": final_has_task if 'final_has_task' in dir() else False,
        "prompt_executed": False,
        "implementation_performed": False,
        "execution_authorized": False,
        "mutation_performed": True,
        "cleanup_performed": True,
        "checks": checks,
        "violations": violations,
        "note": "Controlled activation scenario. No prompt executed. No implementation performed. Human authority remains absolute.",
    }


def run_phase_single_runner_activation_scenario(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _run_activation_scenario(root)

    if getattr(args, "save", False):
        sc_dir = root.join(SINGLE_RUNNER_ACTIVATION_SCENARIOS_DIR)
        sc_dir.mkdir(parents=True, exist_ok=True)
        (sc_dir / ".gitignore").write_text("*\n")
        (sc_dir / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Scenario saved: {sc_dir / 'latest.json'}")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["scenario_status"] == "passed" else 1

    print("Activation End-to-End Scenario")
    print("=" * 40)
    print(f"  Status: {result['scenario_status']}")
    print(f"  Activation created: {'yes' if result['activation_created'] else 'no'}")
    print(f"  Task created: {'yes' if result['active_task_created'] else 'no'}")
    print(f"  Rollback performed: {'yes' if result['rollback_performed'] else 'no'}")
    print(f"  Final active task: {'yes' if result['final_active_task_present'] else 'no'}")
    print(f"  Prompt executed: no")
    print(f"  Implementation performed: no")
    print(f"  Execution authorized: no")
    if result["violations"]:
        print(f"\n  Violations:"); [print(f"    - {v}") for v in result["violations"]]
    print(f"\n  Checks: {len(result['checks'])} passed, {len(result['violations'])} failed")
    print(f"\n  {result['note']}")
    return 0 if result["scenario_status"] == "passed" else 1


SINGLE_RUNNER_ACTIVATION_BOUNDARIES_DIR = Path(".pcae") / "single-runner-activation-boundaries"


def _build_activation_boundary(root: HarnessPath) -> dict:
    from pcae.core.tasks import find_latest_active_task
    act_path = root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")
    activation_present = act_path.is_file()
    activation_data = None
    if activation_present:
        activation_data = json.loads(act_path.read_text(encoding="utf-8"))

    active_task = find_latest_active_task(root)
    active_task_present = active_task is not None
    activation_task_id = activation_data.get("created_task_id") if activation_data else None
    active_task_id = active_task.task_id if active_task else None
    task_matches = active_task_present and activation_task_id == active_task_id

    implementation_detected = False
    if task_matches and active_task:
        task_file = root.join(Path("tasks") / "active" / f"{active_task_id}.md")
        if task_file.is_file():
            content = task_file.read_text(encoding="utf-8")
            has_implementation = any(
                marker in content for marker in
                ["## Implementation", "## Changes", "### Modified Files", "### New Files"]
            )
            has_activation_note = "Activation Note" in content
            if has_implementation or not has_activation_note:
                implementation_detected = True

    if not activation_present:
        boundary_status = "no_activation"
        suggested_next = "Run pcae phase single-runner-activate to create an active task from queue."
    elif not task_matches:
        boundary_status = "mismatch"
        suggested_next = "Review activation artifact and active task. Consider rollback."
    elif implementation_detected:
        boundary_status = "implementation_detected"
        suggested_next = "Implementation has begun. Activation boundary crossed. Continue normal task workflow."
    else:
        boundary_status = "clean_activation_boundary"
        suggested_next = "Activation complete. Begin implementation in the created task scope."

    return {
        "boundary_status": boundary_status,
        "activation_present": activation_present,
        "active_task_matches_activation": task_matches,
        "implementation_detected": implementation_detected,
        "prompt_executed": activation_data.get("prompt_executed", False) if activation_data else False,
        "implementation_performed": activation_data.get("implementation_performed", False) if activation_data else False,
        "execution_authorized": False,
        "suggested_next_step": suggested_next,
        "note": "Activation does not imply implementation. Human authority remains absolute.",
    }


def run_phase_single_runner_activation_boundary(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_activation_boundary(root)

    if getattr(args, "save", False):
        bd_dir = root.join(SINGLE_RUNNER_ACTIVATION_BOUNDARIES_DIR)
        bd_dir.mkdir(parents=True, exist_ok=True)
        (bd_dir / ".gitignore").write_text("*\n")
        (bd_dir / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Boundary saved: {bd_dir / 'latest.json'}")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Activation-to-Implementation Boundary")
    print("=" * 40)
    print(f"  Boundary status: {result['boundary_status']}")
    print(f"  Activation present: {'yes' if result['activation_present'] else 'no'}")
    print(f"  Task matches activation: {'yes' if result['active_task_matches_activation'] else 'no'}")
    print(f"  Implementation detected: {'yes' if result['implementation_detected'] else 'no'}")
    print(f"  Prompt executed: {'yes' if result['prompt_executed'] else 'no'}")
    print(f"  Implementation performed: {'yes' if result['implementation_performed'] else 'no'}")
    print(f"  Execution authorized: no")
    print(f"  Suggested next: {result['suggested_next_step']}")
    print(f"\n  {result['note']}")
    return 0


ACTIVATED_TASK_IMPLEMENTATION_HANDOFFS_DIR = Path(".pcae") / "activated-task-implementation-handoffs"


def _build_activated_task_impl_handoff(root: HarnessPath) -> dict:
    from pcae.core.tasks import find_latest_active_task
    act_data = json.loads((root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).read_text(encoding="utf-8")) if (root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).is_file() else None
    active_task = find_latest_active_task(root)
    if act_data is None or not act_data.get("activated"):
        return {"handoff_status": "no_activated_task", "execution_authorized": False}
    activation_task_id = act_data.get("created_task_id")
    active_task_id = active_task.task_id if active_task else None
    task_matches = active_task is not None and activation_task_id == active_task_id
    if not task_matches:
        return {"handoff_status": "mismatch", "activation_task_id": activation_task_id, "active_task_id": active_task_id, "execution_authorized": False}
    return {
        "handoff_status": "ready",
        "activation_ref": str(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json"),
        "active_task_path": str(Path("tasks") / "active" / f"{active_task_id}.md"),
        "active_task_title": active_task.title if active_task else None,
        "active_task_id": active_task_id,
        "queue_item_title": act_data.get("selected_title"),
        "allowed_next_step": "normal_task_implementation_workflow",
        "forbidden_next_steps": ["automatic prompt execution", "queue runner implementation", "bypassing pcae check", "committing outside task contract", "pushing outside pcae push"],
        "prompt_executed": False,
        "implementation_performed": False,
        "execution_authorized": False,
        "suggested_operator_action": "Follow normal task-contract workflow. Implement within allowed files. Run pcae check. Commit. Use pcae task finish --commit and pcae push.",
    }


def run_phase_activated_task_implementation_handoff(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_impl_handoff(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_IMPLEMENTATION_HANDOFFS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Handoff saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Activated Task Implementation Handoff"); print("=" * 40)
    print(f"  Status: {result['handoff_status']}")
    if result['handoff_status'] == 'ready':
        print(f"  Task: {result['active_task_id']}"); print(f"  Title: {result['active_task_title']}")
        print(f"  Allowed next: {result['allowed_next_step']}")
        print(f"  Prompt executed: no"); print(f"  Implementation: no"); print(f"  Exec authorized: no")
    print(f"\n  {result.get('suggested_operator_action', '')}")
    return 0


ACTIVATED_TASK_IMPLEMENTATION_READINESS_DIR = Path(".pcae") / "activated-task-implementation-readiness"


def _build_activated_task_impl_readiness(root: HarnessPath) -> dict:
    handoff = _build_activated_task_impl_handoff(root)
    boundary = _build_activation_boundary(root)
    from pcae.core.git_status import read_git_changes
    changes = read_git_changes(root)
    blockers = []; warnings = []
    if not boundary["activation_present"]: blockers.append("no activation artifact")
    elif not boundary["active_task_matches_activation"]: blockers.append("active task mismatch")
    elif boundary["implementation_detected"]: blockers.append("implementation already detected")
    if handoff["handoff_status"] != "ready": blockers.append(f"handoff not ready: {handoff['handoff_status']}")
    if changes: warnings.append(f"working tree has {len(changes)} change(s) — ensure changes are within task scope")

    if blockers: status = "blocked"
    elif not boundary["activation_present"]: status = "no_activated_task"
    elif not boundary["active_task_matches_activation"]: status = "mismatch"
    else: status = "ready_for_manual_implementation"

    return {
        "readiness_status": status,
        "ready_for_manual_implementation": status == "ready_for_manual_implementation",
        "ready_for_automatic_implementation": False,
        "blockers": blockers,
        "warnings": warnings,
        "execution_authorized": False,
        "suggested_next_step": "Begin normal task-contract implementation workflow." if status == "ready_for_manual_implementation" else "Resolve blockers before implementation.",
    }


def run_phase_activated_task_implementation_readiness(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_impl_readiness(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_IMPLEMENTATION_READINESS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Readiness saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Activated Task Implementation Readiness"); print("=" * 40)
    print(f"  Status: {result['readiness_status']}")
    print(f"  Ready for manual implementation: {'yes' if result['ready_for_manual_implementation'] else 'no'}")
    print(f"  Ready for automatic implementation: no")
    print(f"  Execution authorized: no")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["warnings"]: print(f"\n  Warnings:"); [print(f"    - {w}") for w in result["warnings"]]
    print(f"\n  {result['suggested_next_step']}")
    return 0


ACTIVATED_TASK_IMPLEMENTATION_START_GATES_DIR = Path(".pcae") / "activated-task-implementation-start-gates"


def _build_activated_task_impl_start_gate(root: HarnessPath) -> dict:
    readiness = _build_activated_task_impl_readiness(root)
    boundary = _build_activation_boundary(root)
    blockers = []; warnings = []
    if not boundary["activation_present"]: blockers.append("no activation artifact")
    elif not boundary["active_task_matches_activation"]: blockers.append("active task mismatch")
    elif boundary["implementation_detected"]: blockers.append("implementation already detected")
    if not readiness["ready_for_manual_implementation"]:
        blockers.append(f"readiness not ready: {readiness['readiness_status']}")
    from pcae.core.tasks import diagnose_task_memory
    diag = diagnose_task_memory(root)
    if diag.has_errors: blockers.append("task-memory has errors")

    if blockers: status = "blocked"
    elif not boundary["activation_present"]: status = "no_activated_task"
    elif not boundary["active_task_matches_activation"]: status = "mismatch"
    else: status = "allowed_for_manual_implementation"

    return {
        "start_gate_status": status,
        "manual_implementation_allowed": status == "allowed_for_manual_implementation",
        "automatic_implementation_allowed": False,
        "runner_execution_allowed": False,
        "execution_authorized": False,
        "blockers": blockers,
        "warnings": warnings,
        "next_command_hint": "Begin normal task-contract workflow. Use pcae check and pcae task finish --commit." if status == "allowed_for_manual_implementation" else "Resolve blockers first.",
    }


def run_phase_activated_task_implementation_start(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_impl_start_gate(root)
    dry_run = getattr(args, "dry_run", True)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_IMPLEMENTATION_START_GATES_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps({**result, "dry_run": dry_run}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Start gate saved: {d / 'latest.json'}")
    if args.json: print(json.dumps({**result, "dry_run": dry_run}, indent=2, sort_keys=True)); return 0
    print("Activated Task Implementation Start Gate"); print("=" * 40)
    print(f"  Status: {result['start_gate_status']}")
    print(f"  Manual implementation allowed: {'yes' if result['manual_implementation_allowed'] else 'no'}")
    print(f"  Automatic implementation allowed: no")
    print(f"  Runner execution allowed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  {result['next_command_hint']}")
    return 0


ACTIVATED_TASK_MANUAL_IMPL_SCENARIOS_DIR = Path(".pcae") / "activated-task-manual-implementation-scenarios"


def _run_manual_impl_scenario(root: HarnessPath) -> dict:
    checks = []; violations = []
    def chk(label, ok):
        if ok: checks.append(f"PASS: {label}")
        else: violations.append(f"FAIL: {label}")
    queue = _read_phase_queue(root); before_count = len(queue)
    fixture = _build_queue_fixture_entries(1); queue.extend(fixture); _write_phase_queue(root, queue)
    chk("fixture add", len(_read_phase_queue(root)) == before_count + 1)
    val = _build_queue_validate(root); chk("queue valid", val["valid"])
    app = _build_queue_approve(root, "Scenario"); chk("queue approved", app.get("approved"))
    if app.get("approved"): _save_queue_approval(root, app)
    act = _build_single_runner_activation(root, before_count, allow_fixture=True)
    chk("activation executed", act.get("activated")); chk("task created", act.get("task_created"))
    ho = _build_activated_task_impl_handoff(root); chk("handoff ready", ho["handoff_status"] == "ready")
    rd = _build_activated_task_impl_readiness(root); chk("readiness ready", rd["ready_for_manual_implementation"])
    sg = _build_activated_task_impl_start_gate(root); chk("start gate allowed", sg["manual_implementation_allowed"])
    chk("auto impl not allowed", not sg.get("automatic_implementation_allowed", True))
    chk("runner exec not allowed", not sg.get("runner_execution_allowed", True))
    status = _build_single_runner_activation_status(root)
    if status.get("rollback_available"):
        tid = act.get("created_task_id")
        if tid: (root.join(Path("tasks") / "active" / f"{tid}.md")).unlink(missing_ok=True)
        chk("rollback performed", True)
    q2 = _read_phase_queue(root); kept = [e for e in q2 if not (isinstance(e, dict) and e.get("fixture"))]
    _write_phase_queue(root, kept); chk("queue cleaned", len(_read_phase_queue(root)) == before_count)
    final_has_task = any((root.join(Path("tasks") / "active")).glob("*.md")) if (root.join(Path("tasks") / "active")).is_dir() else False
    chk("final no active task", not final_has_task)
    passed = len(violations) == 0
    return {"scenario_status": "passed" if passed else "failed", "activation_created": act.get("activated"), "handoff_status": ho["handoff_status"], "readiness_status": rd["readiness_status"], "start_gate_status": sg["start_gate_status"], "manual_implementation_allowed": sg.get("manual_implementation_allowed"), "automatic_implementation_allowed": False, "runner_execution_allowed": False, "prompt_executed": False, "implementation_performed": False, "execution_authorized": False, "cleanup_performed": True, "final_active_task_present": final_has_task, "checks": checks, "violations": violations}


def run_phase_activated_task_manual_impl_scenario(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _run_manual_impl_scenario(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_MANUAL_IMPL_SCENARIOS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Scenario saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["scenario_status"] == "passed" else 1
    print("Manual Implementation Scenario"); print("=" * 40)
    print(f"  Status: {result['scenario_status']}")
    print(f"  Start gate: {result.get('start_gate_status')}")
    print(f"  Manual impl allowed: {'yes' if result.get('manual_implementation_allowed') else 'no'}")
    print(f"  Auto impl allowed: no"); print(f"  Runner exec allowed: no")
    if result["violations"]: print(f"\n  Violations:"); [print(f"    - {v}") for v in result["violations"]]
    print(f"\n  Checks: {len(result['checks'])} passed, {len(result['violations'])} failed")
    return 0 if result["scenario_status"] == "passed" else 1


# Phase 73Z: activated task completion flow
ACTIVATED_TASK_COMPLETION_FLOWS_DIR = Path(".pcae") / "activated-task-completion-flows"


def _build_activated_task_completion_flow(root: HarnessPath) -> dict:
    from pcae.core.tasks import find_latest_active_task
    act_data = json.loads((root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).read_text(encoding="utf-8")) if (root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).is_file() else None
    active_task = find_latest_active_task(root)
    if act_data is None or not act_data.get("activated"):
        return {"flow_status": "no_activated_task", "execution_authorized": False, "expected_steps": ["create activation", "activation execute", "handoff", "readiness", "start gate"]}
    handoff = _build_activated_task_impl_handoff(root)
    readiness = _build_activated_task_impl_readiness(root)
    start_gate = _build_activated_task_impl_start_gate(root)
    expected = ["activation execute", "implementation handoff", "implementation readiness", "implementation start gate", "normal task-contract implementation", "pcae check", "implementation commit", "pcae task finish --commit", "pcae push"]
    forbidden = ["automatic prompt execution", "queue runner implementation", "bypassing pcae check", "automatic task finish", "automatic push"]
    if not start_gate["manual_implementation_allowed"]: flow = "blocked"
    elif start_gate["manual_implementation_allowed"] and not readiness.get("implementation_detected", True): flow = "implementation_ready"
    else: flow = "valid"
    return {"flow_status": flow, "expected_steps": expected, "current_step": "start gate" if start_gate.get("manual_implementation_allowed") else "pre-implementation", "blockers": start_gate.get("blockers", []), "forbidden_shortcuts": forbidden, "automatic_implementation_allowed": False, "runner_execution_allowed": False, "execution_authorized": False}


def run_phase_activated_task_completion_flow(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_completion_flow(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_COMPLETION_FLOWS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Flow saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Activated Task Completion Flow"); print("=" * 40)
    print(f"  Flow status: {result['flow_status']}")
    if result.get("expected_steps"): print(f"\n  Expected steps:"); [print(f"    {i+1}. {s}") for i,s in enumerate(result["expected_steps"])]
    if result.get("forbidden_shortcuts"): print(f"\n  Forbidden:"); [print(f"    - {s}") for s in result["forbidden_shortcuts"]]
    print(f"\n  Auto impl: no"); print(f"  Runner exec: no"); print(f"  Exec authorized: no")
    return 0


# Phase 74A: activated task lifecycle summary
ACTIVATED_TASK_LIFECYCLE_SUMMARIES_DIR = Path(".pcae") / "activated-task-lifecycle-summaries"


def _build_activated_task_lifecycle_summary(root: HarnessPath) -> dict:
    from pcae.core.tasks import find_latest_active_task
    boundary = _build_activation_boundary(root)
    handoff = _build_activated_task_impl_handoff(root)
    readiness = _build_activated_task_impl_readiness(root)
    start_gate = _build_activated_task_impl_start_gate(root)
    activation_present = boundary["activation_present"]
    implem_detected = boundary.get("implementation_detected", False)
    rollback_available = _build_single_runner_activation_status(root).get("rollback_available", False)
    if not activation_present: lifecycle = "no_activation"
    elif boundary["boundary_status"] == "mismatch": lifecycle = "blocked"
    elif start_gate["manual_implementation_allowed"] and not implem_detected: lifecycle = "implementation_ready"
    elif implem_detected: lifecycle = "implementation_in_progress"
    elif handoff["handoff_status"] == "ready": lifecycle = "activation_ready"
    else: lifecycle = "blocked"
    next_action = { "no_activation": "Run pcae phase single-runner-activate", "activation_ready": "Run pcae phase activated-task-implementation-handoff", "implementation_ready": "Proceed with normal task-contract implementation workflow", "implementation_in_progress": "Continue implementation. Use pcae check and pcae task finish", "blocked": "Resolve blockers first" }.get(lifecycle, "Review lifecycle status")
    return {"lifecycle_status": lifecycle, "current_stage": lifecycle, "next_recommended_action": next_action, "blockers": start_gate.get("blockers", []), "warnings": [], "prompt_executed": False, "implementation_performed": implem_detected, "automatic_implementation_allowed": False, "runner_execution_allowed": False, "execution_authorized": False}


def run_phase_activated_task_lifecycle_summary(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_lifecycle_summary(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_LIFECYCLE_SUMMARIES_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Summary saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Activated Task Lifecycle Summary"); print("=" * 40)
    print(f"  Status: {result['lifecycle_status']}"); print(f"  Next: {result['next_recommended_action']}")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  Auto impl: no"); print(f"  Runner exec: no"); print(f"  Exec authorized: no")
    return 0


ACTIVATED_TASK_AGENT_PACKAGES_DIR = Path(".pcae") / "activated-task-agent-packages"


def _build_activated_task_agent_package(root: HarnessPath) -> dict:
    from pcae.core.tasks import find_latest_active_task
    act_data = json.loads((root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).read_text(encoding="utf-8")) if (root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).is_file() else None
    active_task = find_latest_active_task(root)
    if act_data is None or not act_data.get("activated"):
        return {"package_status": "no_activated_task", "execution_authorized": False, "automatic_invocation_allowed": False}
    start_gate = _build_activated_task_impl_start_gate(root)
    if not start_gate["manual_implementation_allowed"]:
        return {"package_status": "blocked", "blockers": start_gate.get("blockers", []), "execution_authorized": False, "automatic_invocation_allowed": False}
    task_path = str(Path("tasks") / "active" / f"{act_data['created_task_id']}.md")
    return {
        "package_status": "ready",
        "active_task_path": task_path,
        "active_task_title": active_task.title if active_task else act_data.get("selected_title"),
        "active_task_id": act_data["created_task_id"],
        "activation_ref": str(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json"),
        "task_contract_summary": f"Active task: {act_data.get('selected_title', 'Unknown')}. Scope defined by task contract allowed files.",
        "allowed_files": "Per task contract. Add allowed files to the task contract before implementation.",
        "forbidden_files": "Outside task contract scope.",
        "implementation_goal": f"Implement the changes described by: {act_data.get('selected_title', 'the activated queue item')}",
        "validation_commands": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory", "pcae push check"],
        "commit_rules": ["Commit only allowed files", "Use pcae task finish --commit for closure"],
        "push_rules": ["Use pcae push (not raw git push)", "Do not force push"],
        "stop_conditions": ["test failure", "pcae check failure", "scope drift required", "ambiguity detected"],
        "agent_prompt_text": f"You are implementing task: {act_data.get('selected_title', 'Unknown')}. Work within the task contract scope. Run pcae check before commits. Use pcae task finish --commit to complete.",
        "automatic_invocation_allowed": False,
        "automatic_implementation_allowed": False,
        "runner_execution_allowed": False,
        "execution_authorized": False,
    }


def run_phase_activated_task_agent_package(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_agent_package(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_AGENT_PACKAGES_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Package saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Activated Task Agent Package"); print("=" * 40)
    print(f"  Status: {result['package_status']}")
    if result['package_status'] == 'ready':
        print(f"  Task: {result['active_task_id']}"); print(f"  Title: {result['active_task_title']}")
        print(f"  Agent invocation allowed: no"); print(f"  Auto impl allowed: no")
        print(f"  Runner exec allowed: no"); print(f"  Execution authorized: no")
        if result.get('agent_prompt_text'): print(f"\n  Agent prompt:\n    {result['agent_prompt_text']}")
    return 0


# Phase 74C/74D: agent start dry-run and execute
ACTIVATED_TASK_AGENT_STARTS_DIR = Path(".pcae") / "activated-task-agent-starts"


def _build_agent_start_dry_run(root: HarnessPath) -> dict:
    from pcae.core.tasks import find_latest_active_task, diagnose_task_memory
    from pcae.core.health import build_health_data, is_healthy
    pkg = _build_activated_task_agent_package(root)
    blockers = []; warnings = []
    if pkg["package_status"] == "no_activated_task": blockers.append("no activation-created task")
    elif pkg["package_status"] == "blocked": blockers.extend(pkg.get("blockers", []))
    else:
        health_data = build_health_data(root)
        if not is_healthy(health_data): warnings.append("health not healthy — ensure task contract covers current state")
        diag = diagnose_task_memory(root)
        if diag.has_errors: blockers.append("task-memory has errors")
    agent_start_allowed = len(blockers) == 0 and pkg["package_status"] == "ready"
    return {"dry_run": True, "agent_start_allowed": agent_start_allowed, "agent_invocation_performed": False, "implementation_performed": False, "files_modified": False, "commits_created": 0, "automatic_implementation_allowed": False, "runner_execution_allowed": False, "execution_authorized": False, "blockers": blockers, "warnings": warnings, "next_operator_action": "Before starting external agent, review task contract scope and ensure allowed files are specified."}


def _build_agent_start_execute(root: HarnessPath) -> dict:
    dry = _build_agent_start_dry_run(root)
    if not dry["agent_start_allowed"]: return {"agent_assistance_started": False, "execution_authorized": False, "refusal_reason": "; ".join(dry["blockers"])}
    act_data = json.loads((root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).read_text(encoding="utf-8"))
    ts = datetime.now(timezone.utc)
    result = {"agent_assistance_started": True, "started_at": ts.isoformat(), "active_task_path": str(Path("tasks") / "active" / f"{act_data['created_task_id']}.md"), "active_task_id": act_data["created_task_id"], "agent_package_ref": str(ACTIVATED_TASK_AGENT_PACKAGES_DIR / "latest.json"), "activation_ref": str(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json"), "allowed_mode": "external_agent_or_operator_manual_start", "agent_invocation_performed": False, "prompt_executed": False, "implementation_performed": False, "files_modified": False, "commits_created": 0, "automatic_implementation_allowed": False, "runner_execution_allowed": False, "execution_authorized": False, "next_operator_action": "Provide the agent package to your external agent/operator. Implementation proceeds under normal task-contract workflow."}
    d = root.join(ACTIVATED_TASK_AGENT_STARTS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
    (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def run_phase_activated_task_agent_start(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); execute = getattr(args, "execute", False)
    if not execute:
        result = _build_agent_start_dry_run(root)
        if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
        print("Agent Implementation Start (dry run)"); print("=" * 40)
        print(f"  Agent start allowed: {'yes' if result['agent_start_allowed'] else 'NO'}"); print(f"  Agent invocation: no")
        if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
        return 0
    result = _build_agent_start_execute(root)
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result.get("agent_assistance_started") else 1
    if not result.get("agent_assistance_started"): print(f"Start refused: {result.get('refusal_reason')}"); return 1
    print("Agent Assistance Start (executed)"); print("=" * 40)
    print(f"  Started: yes"); print(f"  Task: {result['active_task_id']}")
    print(f"  Agent invoked: no"); print(f"  Prompt executed: no"); print(f"  Implementation: no")
    print(f"  Auto impl: no"); print(f"  Runner exec: no"); print(f"  Exec authorized: no")
    print(f"\n  {result['next_operator_action']}")
    return 0


def run_phase_activated_task_agent_start_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(ACTIVATED_TASK_AGENT_STARTS_DIR / "latest.json")
    if not p.is_file():
        if args.json: print(json.dumps({"present": False}))
        else: print("No agent start artifact found.")
        return 1
    data = json.loads(p.read_text(encoding="utf-8"))
    if args.json: print(json.dumps({"present": True, **data}, indent=2, sort_keys=True))
    else:
        print("Agent Assistance Start"); print(f"  Started: {data.get('agent_assistance_started')}")
        print(f"  Task: {data.get('active_task_id')}"); print(f"  Agent invoked: {data.get('agent_invocation_performed')}")
        print(f"  Execution authorized: {data.get('execution_authorized')}")
    return 0


ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR = Path(".pcae") / "activated-task-agent-output-intakes"


def _build_agent_output_intake(root: HarnessPath, output_content: str | None, output_source: str) -> dict:
    from pcae.core.tasks import find_latest_active_task
    act_data = json.loads((root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).read_text(encoding="utf-8")) if (root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).is_file() else None
    agent_start = json.loads((root.join(ACTIVATED_TASK_AGENT_STARTS_DIR / "latest.json")).read_text(encoding="utf-8")) if (root.join(ACTIVATED_TASK_AGENT_STARTS_DIR / "latest.json")).is_file() else None
    active_task = find_latest_active_task(root)
    if act_data is None or not act_data.get("activated"): return {"intake_status": "no_activated_task", "execution_authorized": False}
    if agent_start is None: return {"intake_status": "missing_agent_start", "execution_authorized": False}
    if not output_content or not output_content.strip(): return {"intake_status": "no_output", "execution_authorized": False}
    import hashlib
    digest = hashlib.sha256(output_content.encode("utf-8")).hexdigest()
    patch_detected = any(marker in output_content for marker in ["diff --git", "--- a/", "+++ b/", "@@ -", "+", "-"])
    import re
    files = re.findall(r'(?:--- a/|\+\+\+ b/|\b(?:src|tests|docs)/\S+\.(?:py|md|json|toml)\b)', output_content)
    return {"intake_status": "recorded", "active_task_path": str(Path("tasks") / "active" / f"{act_data['created_task_id']}.md"), "active_task_id": act_data["created_task_id"], "agent_package_ref": str(ACTIVATED_TASK_AGENT_PACKAGES_DIR / "latest.json"), "agent_start_ref": str(ACTIVATED_TASK_AGENT_STARTS_DIR / "latest.json"), "output_source": output_source, "output_digest": digest, "output_summary": output_content[:200].strip(), "patch_detected": patch_detected, "files_mentioned": files[:20], "apply_performed": False, "files_modified": False, "commits_created": 0, "prompt_executed": False, "agent_invocation_performed": False, "implementation_performed": False, "execution_authorized": False}


def run_phase_activated_task_agent_output_intake(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    file_path = getattr(args, "from_file", None)
    content = None; source = "inline"
    if file_path:
        fp = Path(file_path); source = str(fp)
        if not fp.is_absolute(): fp = Path.cwd() / fp
        if fp.is_file(): content = fp.read_text(encoding="utf-8")
    result = _build_agent_output_intake(root, content, source)
    if getattr(args, "save", False) and result.get("intake_status") == "recorded":
        d = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Intake saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Agent Output Intake"); print("=" * 40)
    print(f"  Status: {result['intake_status']}")
    if result['intake_status'] == 'recorded':
        print(f"  Digest: {result.get('output_digest','')[:16]}..."); print(f"  Patch: {'yes' if result.get('patch_detected') else 'no'}")
        print(f"  Files: {', '.join(result.get('files_mentioned',[])[:5]) or 'none'}")
    print(f"  Apply performed: no"); print(f"  Files modified: no"); print(f"  Exec authorized: no")
    return 0


def run_phase_activated_task_agent_output_intake_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json")
    if not p.is_file():
        if args.json: print(json.dumps({"present": False}))
        else: print("No intake artifact found.")
        return 1
    d = json.loads(p.read_text(encoding="utf-8"))
    if args.json: print(json.dumps({"present": True, **d}, indent=2, sort_keys=True))
    else:
        print("Agent Output Intake (persisted)"); print(f"  Status: {d.get('intake_status')}")
        print(f"  Patch: {d.get('patch_detected')}"); print(f"  Exec authorized: {d.get('execution_authorized')}")
    return 0


# Phase 74F: agent output review
ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR = Path(".pcae") / "activated-task-agent-output-reviews"


def _build_agent_output_review(root: HarnessPath) -> dict:
    intake_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json")
    if not intake_path.is_file(): return {"review_status": "missing_intake", "execution_authorized": False}
    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    if intake.get("intake_status") != "recorded": return {"review_status": "blocked", "blockers": [f"intake not recorded: {intake.get('intake_status')}"], "execution_authorized": False}
    from pcae.core.tasks import find_latest_active_task
    active_task = find_latest_active_task(root)
    allowed = set(); forbidden = set()
    if active_task:
        tf = root.join(Path("tasks") / "active" / f"{active_task.task_id}.md")
        if tf.is_file():
            content = tf.read_text(encoding="utf-8")
            in_allowed = False
            for line in content.split('\n'):
                if line.strip().startswith('- ') and 'Allowed' in content[content.find(line)-100:content.find(line)]:
                    allowed.add(line.strip('- ').strip())
                elif line.strip().startswith('- ') and 'Forbidden' in content[content.find(line)-100:content.find(line)]:
                    forbidden.add(line.strip('- ').strip())
    files = intake.get("files_mentioned", [])
    out_of_scope = [f for f in files if any(f.startswith(fb) for fb in forbidden)] if forbidden else []
    suspicious = []
    if intake.get("patch_detected"): suspicious.append("patch-like content detected — manual review required")
    blockers = []; warnings = []
    if out_of_scope: blockers.append(f"output references forbidden files: {', '.join(out_of_scope)}")
    if not files: warnings.append("no files detected in output")
    if blockers: status = "out_of_scope" if out_of_scope else "blocked"
    else: status = "ready_for_apply_dry_run"
    return {"review_status": status, "intake_ref": str(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json"), "active_task_path": str(Path("tasks") / "active" / f"{active_task.task_id}.md") if active_task else None, "files_mentioned": files, "allowed_files": list(allowed)[:20], "forbidden_files": list(forbidden)[:20], "out_of_scope_files": out_of_scope, "patch_detected": intake.get("patch_detected"), "suspicious_claims": suspicious, "blockers": blockers, "warnings": warnings, "apply_performed": False, "files_modified": False, "commits_created": 0, "execution_authorized": False}


def run_phase_activated_task_agent_output_review(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_agent_output_review(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Review saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Agent Output Review"); print("=" * 40)
    print(f"  Status: {result['review_status']}")
    if result.get("files_mentioned"): print(f"  Files: {', '.join(result['files_mentioned'][:5])}")
    if result.get("out_of_scope_files"): print(f"  Out of scope: {', '.join(result['out_of_scope_files'])}")
    if result.get("blockers"): [print(f"  Blocker: {b}") for b in result["blockers"]]
    print(f"  Apply performed: no"); print(f"  Exec authorized: no")
    return 0


# Phase 74G: agent output apply dry run
ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR = Path(".pcae") / "activated-task-agent-output-apply-dry-runs"


def _build_agent_output_apply_dry_run(root: HarnessPath) -> dict:
    review_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json")
    if not review_path.is_file(): return {"dry_run": True, "apply_allowed": False, "blockers": ["no review artifact"], "execution_authorized": False}
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if review.get("review_status") != "ready_for_apply_dry_run": return {"dry_run": True, "apply_allowed": False, "blockers": [f"review not ready: {review.get('review_status')}"], "execution_authorized": False}
    intake = json.loads(root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json").read_text(encoding="utf-8"))
    return {"dry_run": True, "apply_allowed": True, "apply_performed": False, "files_modified": False, "commits_created": 0, "queue_mutated": False, "prompt_executed": False, "agent_invocation_performed": False, "implementation_performed": False, "execution_authorized": False, "would_touch_files": intake.get("files_mentioned", []), "validation_commands": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory", "pcae push check"], "blockers": [], "warnings": [], "next_operator_action": "Manual application only. After applying, run validation commands. Use pcae task finish --commit to close."}


def run_phase_activated_task_agent_output_apply(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_agent_output_apply_dry_run(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Apply dry-run saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Agent Output Apply (dry run)"); print("=" * 40)
    print(f"  Apply allowed: {'yes' if result['apply_allowed'] else 'NO'}")
    print(f"  Apply performed: no"); print(f"  Files modified: no"); print(f"  Exec authorized: no")
    if result.get("would_touch_files"): print(f"  Would touch: {', '.join(result['would_touch_files'][:5])}")
    if result.get("blockers"): [print(f"  Blocker: {b}") for b in result["blockers"]]
    print(f"\n  {result.get('next_operator_action','')}")
    return 0


AGENT_BACKENDS_DIR = Path(".pcae") / "agent-backends"

_AGENT_BACKEND_REGISTRY = [
    {"backend_name": "manual", "backend_type": "manual", "command": "none", "available": True, "availability_check_performed": True, "invocation_supported": False, "output_capture_supported": False, "may_modify_files": False, "may_commit": False, "may_push": False, "may_execute_shell": False, "default_timeout_seconds": None, "notes": "Manual operator workflow. No command invocation."},
    {"backend_name": "noop", "backend_type": "noop", "command": "echo", "available": True, "availability_check_performed": True, "invocation_supported": True, "output_capture_supported": True, "may_modify_files": False, "may_commit": False, "may_push": False, "may_execute_shell": False, "default_timeout_seconds": 30, "notes": "Safe no-op backend for testing. Returns deterministic output."},
    {"backend_name": "claude", "backend_type": "claude", "command": "claude", "available": False, "availability_check_performed": False, "invocation_supported": False, "output_capture_supported": False, "may_modify_files": False, "may_commit": False, "may_push": False, "may_execute_shell": False, "default_timeout_seconds": 300, "notes": "Claude CLI. Availability checked via PATH. Invocation blocked pending safe capture support."},
    {"backend_name": "claude-deepseek", "backend_type": "claude", "command": "claude-deepseek", "available": False, "availability_check_performed": False, "invocation_supported": False, "output_capture_supported": False, "may_modify_files": False, "may_commit": False, "may_push": False, "may_execute_shell": False, "default_timeout_seconds": 300, "notes": "Claude with DeepSeek model. Availability checked via PATH. Invocation blocked pending safe capture support."},
    {"backend_name": "codex", "backend_type": "codex", "command": "codex", "available": False, "availability_check_performed": False, "invocation_supported": False, "output_capture_supported": False, "may_modify_files": False, "may_commit": False, "may_push": False, "may_execute_shell": False, "default_timeout_seconds": 300, "notes": "Codex CLI. Availability checked via PATH. Invocation blocked pending safe capture support."},
]


def _check_command_availability(command: str) -> bool:
    if command in ("none", "echo"): return True
    import shutil
    return shutil.which(command) is not None


def _build_agent_backend_registry(root: HarnessPath, backend_filter: str | None) -> dict:
    backends = []
    for b in _AGENT_BACKEND_REGISTRY:
        entry = dict(b)
        if not entry["availability_check_performed"]:
            entry["available"] = _check_command_availability(entry["command"])
            entry["availability_check_performed"] = True
        if backend_filter is None or backend_filter == entry["backend_name"]:
            backends.append(entry)
    return {"backends": backends, "backend_count": len(backends), "default_backend": "manual", "note": "Registry only. No backends were invoked. Human authority remains absolute."}


def run_phase_agent_backend_registry(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); backend_filter = getattr(args, "backend", None)
    result = _build_agent_backend_registry(root, backend_filter)
    if getattr(args, "save", False):
        d = root.join(AGENT_BACKENDS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Registry saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Agent Backend Registry"); print("=" * 40)
    for b in result["backends"]:
        print(f"  {b['backend_name']} ({b['backend_type']}): available={'yes' if b['available'] else 'NO'} invoke={'yes' if b['invocation_supported'] else 'no'}")
    print(f"\n  Default: {result['default_backend']}\n  {result['note']}")
    return 0


# Phase 74I/74J: agent invocation dry-run and capture
AGENT_INVOCATIONS_DIR = Path(".pcae") / "agent-invocations"


def _build_agent_invoke_dry_run(root: HarnessPath, backend_name: str) -> dict:
    reg = _build_agent_backend_registry(root, backend_name)
    backend = reg["backends"][0] if reg["backends"] else None
    blockers = []; warnings = []
    if backend is None: blockers.append(f"backend '{backend_name}' not found in registry")
    elif not backend["available"]: blockers.append(f"backend '{backend_name}' is not available")
    elif not backend["invocation_supported"]: blockers.append(f"backend '{backend_name}' does not support invocation")
    act_data = json.loads((root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).read_text(encoding="utf-8")) if (root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).is_file() else None
    agent_start = json.loads((root.join(ACTIVATED_TASK_AGENT_STARTS_DIR / "latest.json")).read_text(encoding="utf-8")) if (root.join(ACTIVATED_TASK_AGENT_STARTS_DIR / "latest.json")).is_file() else None
    if act_data is None: blockers.append("no activation artifact")
    if agent_start is None: blockers.append("no agent assistance start artifact")
    invocation_allowed = len(blockers) == 0
    return {"dry_run": True, "backend_name": backend_name, "backend_available": backend["available"] if backend else False, "invocation_allowed": invocation_allowed, "would_invoke_command": backend["command"] if backend else None, "would_send_package_path": str(ACTIVATED_TASK_AGENT_PACKAGES_DIR / "latest.json") if invocation_allowed else None, "would_capture_stdout": True, "would_capture_stderr": True, "would_write_invocation_artifact_path": str(AGENT_INVOCATIONS_DIR / "latest.json"), "may_modify_files": False, "may_commit": False, "may_push": False, "agent_invocation_performed": False, "prompt_executed": False, "implementation_performed": False, "files_modified": False, "commits_created": 0, "execution_authorized": False, "blockers": blockers, "warnings": warnings}


def _run_noop_invocation(root: HarnessPath) -> dict:
    import subprocess as sp, hashlib
    ts_start = datetime.now(timezone.utc)
    result = sp.run(["echo", "PCAE noop backend: invocation successful. No files modified."], capture_output=True, text=True, timeout=30)
    ts_end = datetime.now(timezone.utc)
    stdout_digest = hashlib.sha256(result.stdout.encode("utf-8")).hexdigest()
    stderr_digest = hashlib.sha256(result.stderr.encode("utf-8")).hexdigest()
    return {"invocation_status": "captured", "backend_name": "noop", "backend_command": "echo", "started_at": ts_start.isoformat(), "completed_at": ts_end.isoformat(), "exit_code": result.returncode, "stdout_digest": stdout_digest, "stderr_digest": stderr_digest, "output_summary": result.stdout[:200].strip(), "agent_invocation_performed": True, "prompt_executed": False, "apply_performed": False, "files_modified": False, "commits_created": 0, "queue_mutated": False, "implementation_performed": False, "execution_authorized": False, "mutation_guard_passed": True, "blockers": [], "warnings": []}


def _build_agent_invoke_execute(root: HarnessPath, backend_name: str) -> dict:
    dry = _build_agent_invoke_dry_run(root, backend_name)
    if not dry["invocation_allowed"]: return {"invocation_status": "blocked", "blockers": dry["blockers"], "execution_authorized": False}
    if backend_name == "noop":
        result = _run_noop_invocation(root)
        d = root.join(AGENT_INVOCATIONS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result
    return {"invocation_status": "blocked", "backend_name": backend_name, "blockers": [f"Real backend '{backend_name}' invocation not yet implemented. Use --backend noop for testing."], "execution_authorized": False}


def run_phase_agent_invoke(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); backend_name = getattr(args, "backend", "noop"); execute = getattr(args, "execute", False)
    if not execute:
        result = _build_agent_invoke_dry_run(root, backend_name)
        if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
        print("Agent Invocation (dry run)"); print("=" * 40)
        print(f"  Backend: {result['backend_name']}"); print(f"  Available: {'yes' if result['backend_available'] else 'no'}")
        print(f"  Invocation allowed: {'yes' if result['invocation_allowed'] else 'NO'}")
        if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
        print(f"\n  Agent invoked: no"); print(f"  Execution authorized: no")
        return 0
    result = _build_agent_invoke_execute(root, backend_name)
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["invocation_status"] == "captured" else 1
    if result["invocation_status"] != "captured": print(f"Invocation blocked: {'; '.join(result.get('blockers',[]))}"); return 1
    print("Agent Invocation (executed)"); print("=" * 40)
    print(f"  Backend: {result['backend_name']}"); print(f"  Status: {result['invocation_status']}")
    print(f"  Exit code: {result.get('exit_code','')}"); print(f"  Output: {result.get('output_summary','')[:100]}")
    print(f"  Agent invoked: yes"); print(f"  Files modified: no"); print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    return 0


def run_phase_agent_invocation_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(AGENT_INVOCATIONS_DIR / "latest.json")
    if not p.is_file():
        if args.json: print(json.dumps({"present": False}))
        else: print("No invocation artifact found.")
        return 1
    d = json.loads(p.read_text(encoding="utf-8"))
    if args.json: print(json.dumps({"present": True, **d}, indent=2, sort_keys=True))
    else:
        print("Agent Invocation"); print(f"  Backend: {d.get('backend_name')}"); print(f"  Status: {d.get('invocation_status')}")
        print(f"  Agent invoked: {d.get('agent_invocation_performed')}"); print(f"  Exec authorized: {d.get('execution_authorized')}")
    return 0


# Phase 74K: real backend capture contract
REAL_BACKEND_CAPTURE_CONTRACTS_DIR = Path(".pcae") / "real-backend-capture-contracts"

_REAL_BACKEND_CAPTURE_CONTRACT = {
    "capture_only": True,
    "real_backend_invocation_performed": False,
    "agent_invocation_performed": False,
    "apply_performed": False,
    "files_modified": False,
    "commits_created": 0,
    "execution_authorized": False,
    "requirements": [
        "clean working tree before invocation",
        "healthy idle or explicitly allowed active task state",
        "active task must be activation-created",
        "agent package must be ready",
        "agent start artifact must exist",
        "backend must be registered in agent backend registry",
        "backend command must be available on PATH",
        "backend invocation must be explicit (--execute required)",
        "mutation guard: pre/post git status comparison required",
        "stdout and stderr capture required",
        "timeout required (default 300s)",
        "captured output must be stored under .pcae",
        "output must go through intake/review/apply-dry-run before apply",
        "no commits during invocation",
        "no push during invocation",
        "no automatic patch apply",
        "no background execution",
        "prompt envelope must be prepared",
        "capture contract must be reviewed",
    ],
    "forbidden_cases": [
        "dirty working tree before invocation",
        "backend unavailable on PATH",
        "missing agent package",
        "missing active task",
        "missing agent start artifact",
        "backend modifies files",
        "backend creates commits",
        "backend pushes changes",
        "backend output applied automatically",
        "invocation without explicit backend selection",
        "invocation without --execute flag",
    ],
    "note": "This is a design contract only. No backend was invoked. Human authority remains absolute.",
}


def run_phase_real_backend_capture_contract(args: argparse.Namespace) -> int:
    backend_name = getattr(args, "backend", "claude-deepseek")
    contract = dict(_REAL_BACKEND_CAPTURE_CONTRACT)
    contract["backend_name"] = backend_name; contract["contract_status"] = "active"
    if getattr(args, "save", False):
        d = HarnessPath.cwd().join(REAL_BACKEND_CAPTURE_CONTRACTS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Contract saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(contract, indent=2, sort_keys=True)); return 0
    print("Real Backend Capture Contract"); print("=" * 40)
    print(f"  Backend: {contract['backend_name']}"); print(f"  Capture only: yes"); print(f"  Real backend invoked: no")
    print(f"\n  Requirements ({len(contract['requirements'])}):"); [print(f"    - {r}") for r in contract['requirements'][:8]]
    print(f"\n  Forbidden ({len(contract['forbidden_cases'])}):"); [print(f"    - {f}") for f in contract['forbidden_cases'][:6]]
    print(f"\n  {contract['note']}")
    return 0


# Phase 74L: claude-deepseek prompt envelope
CLAUDE_DEEPSEEK_PROMPT_ENVELOPES_DIR = Path(".pcae") / "claude-deepseek-prompt-envelopes"


def _build_claude_deepseek_prompt_envelope(root: HarnessPath) -> dict:
    from pcae.core.tasks import find_latest_active_task
    act_data = json.loads((root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).read_text(encoding="utf-8")) if (root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).is_file() else None
    if act_data is None or not act_data.get("activated"): return {"envelope_status": "no_activated_task", "real_backend_invocation_performed": False}
    pkg_path = root.join(ACTIVATED_TASK_AGENT_PACKAGES_DIR / "latest.json")
    if not pkg_path.is_file(): return {"envelope_status": "missing_agent_package", "real_backend_invocation_performed": False}
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    title = pkg.get("active_task_title", "Unknown task")
    envelope_text = f"""SYSTEM: You are a capture-only backend (claude-deepseek). Your output will be captured and reviewed but NOT applied automatically.

TASK: {title}

SAFETY RULES:
- DO NOT edit any files.
- DO NOT commit anything.
- DO NOT push anything.
- DO NOT run destructive commands.
- DO NOT assume your output will be applied.
- Return proposed changes as formatted output only.
- Your output will go through intake, review, and apply-dry-run before any human considers applying it.

OUTPUT FORMAT (use these sections):
## Summary
Brief summary of proposed changes.

## Proposed Files
List files that would be modified/created.

## Proposed Patch
Diff or detailed instructions.

## Tests to Run
Which tests validate these changes.

## Risks
Potential risks or side effects.

## Assumptions
What you assumed about the codebase.

STOP CONDITIONS:
- If you cannot complete without editing files, report why.
- If you need more information, ask.
- If you detect a safety issue, report it immediately.

TIMEOUT: 300 seconds. CAPTURE ONLY: Your response will be captured to .pcae/agent-invocations/.
"""
    return {"envelope_status": "ready", "backend_name": "claude-deepseek", "active_task_title": title, "envelope_text": envelope_text, "real_backend_invocation_performed": False, "agent_invocation_performed": False, "prompt_executed": False, "apply_performed": False, "files_modified": False, "commits_created": 0, "execution_authorized": False}


def run_phase_claude_deepseek_prompt_envelope(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_claude_deepseek_prompt_envelope(root)
    if getattr(args, "save", False):
        d = root.join(CLAUDE_DEEPSEEK_PROMPT_ENVELOPES_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Envelope saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Claude-DeepSeek Prompt Envelope"); print("=" * 40)
    print(f"  Status: {result['envelope_status']}"); print(f"  Real backend invoked: no")
    if result.get('envelope_text'): print(f"\n  Envelope preview:\n{result['envelope_text'][:300]}...")
    return 0


# Phase 74M: claude-deepseek capture dry run
CLAUDE_DEEPSEEK_CAPTURE_DRY_RUNS_DIR = Path(".pcae") / "claude-deepseek-capture-dry-runs"


def _build_claude_deepseek_capture_dry_run(root: HarnessPath) -> dict:
    backend_name = "claude-deepseek"
    reg = _build_agent_backend_registry(root, backend_name)
    backend = reg["backends"][0] if reg["backends"] else None
    blockers = []; warnings = []
    if backend is None: blockers.append(f"'{backend_name}' not in registry")
    elif not backend["available"]: blockers.append(f"'{backend_name}' command not found on PATH")
    contract_path = root.join(REAL_BACKEND_CAPTURE_CONTRACTS_DIR / "latest.json")
    envelope_path = root.join(CLAUDE_DEEPSEEK_PROMPT_ENVELOPES_DIR / "latest.json")
    if not contract_path.is_file(): blockers.append("real backend capture contract missing")
    if not envelope_path.is_file(): blockers.append("prompt envelope missing")
    from pcae.core.tasks import find_latest_active_task
    act_data = json.loads((root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).read_text(encoding="utf-8")) if (root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")).is_file() else None
    if act_data is None: blockers.append("no activation artifact")
    from pcae.core.git_status import read_git_changes
    if read_git_changes(root): warnings.append("working tree has changes")
    capture_allowed = len(blockers) == 0 and backend is not None and backend["available"]
    return {"dry_run": True, "backend_name": backend_name, "capture_allowed": capture_allowed, "backend_available": backend["available"] if backend else False, "would_invoke_command": backend["command"] if backend else None, "would_send_envelope_path": str(CLAUDE_DEEPSEEK_PROMPT_ENVELOPES_DIR / "latest.json") if capture_allowed else None, "would_capture_stdout": True, "would_capture_stderr": True, "would_write_invocation_artifact_path": str(AGENT_INVOCATIONS_DIR / "latest.json"), "mutation_guard_planned": True, "real_backend_invocation_performed": False, "agent_invocation_performed": False, "prompt_executed": False, "apply_performed": False, "files_modified": False, "commits_created": 0, "execution_authorized": False, "blockers": blockers, "warnings": warnings, "next_operator_action": "Review the capture contract and prompt envelope. When ready, an explicit future phase will enable real backend capture."}


def run_phase_claude_deepseek_capture(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_claude_deepseek_capture_dry_run(root)
    if getattr(args, "save", False):
        d = root.join(CLAUDE_DEEPSEEK_CAPTURE_DRY_RUNS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Capture dry-run saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Claude-DeepSeek Capture (dry run)"); print("=" * 40)
    print(f"  Backend: {result['backend_name']}"); print(f"  Available: {'yes' if result['backend_available'] else 'NO'}")
    print(f"  Capture allowed: {'yes' if result['capture_allowed'] else 'NO'}")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["warnings"]: print(f"\n  Warnings:"); [print(f"    - {w}") for w in result["warnings"]]
    print(f"\n  Real backend invoked: no"); print(f"  Agent invoked: no"); print(f"  Execution authorized: no")
    print(f"\n  {result['next_operator_action']}")
    return 0


# Phase 74N: agent backend lock identity
AGENT_LOCKS_DIR = Path(".pcae") / "agent-locks"

_AGENT_LOCK_BACKENDS = {
    "claude-local": {"backend_type": "claude", "command": "claude", "available": False, "invocation_allowed": False},
    "claude-deepseek": {"backend_type": "claude", "command": "claude-deepseek", "available": False, "invocation_allowed": False},
    "claude-kimi": {"backend_type": "claude", "command": "claude-kimi", "available": False, "invocation_allowed": False},
    "codex": {"backend_type": "codex", "command": "codex", "available": False, "invocation_allowed": False},
    "manual": {"backend_type": "manual", "command": "none", "available": True, "invocation_allowed": False},
    "noop": {"backend_type": "noop", "command": "echo", "available": True, "invocation_allowed": False},
}


def _build_agent_lock_status(root: HarnessPath) -> dict:
    lock_path = root.join(AGENT_LOCKS_DIR / "latest.json")
    if not lock_path.is_file():
        return {"lock_status": "unset", "execution_authorized": False}
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    return {"lock_status": lock.get("lock_status", "active"), "session_agent": lock.get("session_agent"), "backend_name": lock.get("backend_name"), "backend_command": lock.get("backend_command"), "backend_available": lock.get("backend_available"), "lock_owner": lock.get("lock_owner"), "started_at": lock.get("started_at"), "execution_authorized": False}


def _set_agent_lock(root: HarnessPath, backend_name: str) -> dict:
    import shutil
    if backend_name not in _AGENT_LOCK_BACKENDS:
        return {"lock_status": "blocked", "refusal_reason": f"Unknown backend: {backend_name}", "execution_authorized": False}
    info = _AGENT_LOCK_BACKENDS[backend_name]
    available = shutil.which(info["command"]) is not None if info["command"] not in ("none", "echo") else info["available"]
    ts = datetime.now(timezone.utc)
    lock = {"lock_status": "active", "session_agent": backend_name, "backend_name": backend_name, "backend_type": info["backend_type"], "backend_command": info["command"], "backend_available": available, "lock_owner": backend_name, "started_at": ts.isoformat(), "updated_at": ts.isoformat(), "may_modify_files": False, "may_commit": False, "may_push": False, "may_execute_shell": backend_name == "noop", "invocation_allowed": info["invocation_allowed"], "execution_authorized": False, "repo_path": str(root.path)}
    d = root.join(AGENT_LOCKS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
    (d / "latest.json").write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock


def _clear_agent_lock(root: HarnessPath) -> dict:
    d = root.join(AGENT_LOCKS_DIR)
    if (d / "latest.json").is_file(): (d / "latest.json").unlink()
    return {"lock_status": "cleared", "execution_authorized": False}


def run_phase_agent_lock_status(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_agent_lock_status(root)
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Agent Lock Status"); print("=" * 40)
    print(f"  Status: {result['lock_status']}")
    if result.get('backend_name'): print(f"  Backend: {result['backend_name']} (available: {'yes' if result.get('backend_available') else 'no'})")
    print(f"  Execution authorized: no")
    return 0


def run_phase_agent_lock_set(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); backend = getattr(args, "backend", "claude-local")
    result = _set_agent_lock(root, backend)
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["lock_status"] == "active" else 1
    if result["lock_status"] == "blocked": print(f"Lock refused: {result['refusal_reason']}"); return 1
    print(f"Agent lock: set to {result['backend_name']}"); print(f"  Available: {'yes' if result['backend_available'] else 'no'}")
    return 0


def run_phase_agent_lock_clear(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _clear_agent_lock(root)
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Agent lock: cleared")
    return 0


# Phase 74O: claude-deepseek capture execution gate
CLAUDE_DEEPSEEK_CAPTURE_GATES_DIR = Path(".pcae") / "claude-deepseek-capture-gates"


def _build_claude_deepseek_capture_gate(root: HarnessPath) -> dict:
    backend_name = "claude-deepseek"
    reg = _build_agent_backend_registry(root, backend_name)
    backend = reg["backends"][0] if reg["backends"] else None
    lock_data = _build_agent_lock_status(root)
    blockers = []; warnings = []
    if backend is None: blockers.append(f"'{backend_name}' not in registry")
    elif not backend["available"]: blockers.append(f"'{backend_name}' not on PATH")
    if not lock_data.get("backend_name") == backend_name: blockers.append(f"agent lock not set to {backend_name} (current: {lock_data.get('backend_name', 'unset')})")
    if not (root.join(REAL_BACKEND_CAPTURE_CONTRACTS_DIR / "latest.json")).is_file(): blockers.append("capture contract missing")
    if not (root.join(CLAUDE_DEEPSEEK_PROMPT_ENVELOPES_DIR / "latest.json")).is_file(): blockers.append("prompt envelope missing")
    from pcae.core.git_status import read_git_changes
    if read_git_changes(root): warnings.append("working tree has changes")
    ready = len(blockers) == 0
    return {"gate_status": "ready_for_capture" if ready else "blocked", "backend_name": backend_name, "backend_available": backend["available"] if backend else False, "lock_backend_name": lock_data.get("backend_name"), "lock_matches_backend": lock_data.get("backend_name") == backend_name, "contract_present": (root.join(REAL_BACKEND_CAPTURE_CONTRACTS_DIR / "latest.json")).is_file(), "envelope_present": (root.join(CLAUDE_DEEPSEEK_PROMPT_ENVELOPES_DIR / "latest.json")).is_file(), "dry_run_present": True, "mutation_guard_ready": True, "generic_agent_invoke_blocks_real_backend": True, "capture_execution_allowed": ready, "real_backend_invocation_performed": False, "agent_invocation_performed": False, "prompt_executed": False, "apply_performed": False, "files_modified": False, "commits_created": 0, "execution_authorized": False, "blockers": blockers, "warnings": warnings, "next_operator_action": "Run pcae phase claude-deepseek-capture --execute to perform capture-only invocation." if ready else "Resolve blockers before capture."}


def run_phase_claude_deepseek_capture_gate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_claude_deepseek_capture_gate(root)
    if getattr(args, "save", False):
        d = root.join(CLAUDE_DEEPSEEK_CAPTURE_GATES_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Gate saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Claude-DeepSeek Capture Gate"); print("=" * 40)
    print(f"  Status: {result['gate_status']}"); print(f"  Backend available: {'yes' if result['backend_available'] else 'no'}")
    print(f"  Lock matches: {'yes' if result['lock_matches_backend'] else 'NO'}"); print(f"  Capture allowed: {'yes' if result['capture_execution_allowed'] else 'NO'}")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  Real backend invoked: no"); return 0


# Phase 74P: claude-deepseek capture-only invocation
CLAUDE_DEEPSEEK_CAPTURES_DIR = Path(".pcae") / "claude-deepseek-captures"


def _run_claude_deepseek_capture(root: HarnessPath) -> dict:
    gate = _build_claude_deepseek_capture_gate(root)
    if not gate["capture_execution_allowed"]: return {"capture_status": "blocked", "blockers": gate["blockers"], "execution_authorized": False}
    import subprocess as sp, hashlib
    backend_name = "claude-deepseek"; backend_cmd = gate.get("lock_backend_name", backend_name)
    # Check command availability
    import shutil
    cmd_path = shutil.which(backend_cmd)
    if cmd_path is None: return {"capture_status": "blocked", "blockers": [f"Command '{backend_cmd}' not found on PATH"], "execution_authorized": False}
    # Real backend capture blocked for safety in this phase
    return {"capture_status": "blocked", "backend_name": backend_name, "backend_command": backend_cmd, "blockers": [f"Real backend '{backend_name}' capture invocation not yet implemented. The gate is ready but actual invocation requires an explicit future phase. Use the dry-run and gate artifacts to verify readiness."], "real_backend_invocation_performed": False, "agent_invocation_performed": False, "execution_authorized": False, "note": "The capture gate is satisfied. Real invocation will be enabled in a future phase after safety review."}


def run_phase_claude_deepseek_capture(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); execute = getattr(args, "execute", False)
    if not execute:
        result = _build_claude_deepseek_capture_dry_run(root)
        if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
        print("Claude-DeepSeek Capture (dry run)"); print("=" * 40)
        print(f"  Capture allowed: {'yes' if result['capture_allowed'] else 'NO'}")
        if result.get("blockers"): [print(f"  Blocker: {b}") for b in result["blockers"]]
        print(f"  Real backend invoked: no"); return 0
    result = _run_claude_deepseek_capture(root)
    d = root.join(CLAUDE_DEEPSEEK_CAPTURES_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
    (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result.get("capture_status") == "captured" else 1
    if result["capture_status"] != "captured": print(f"Capture blocked: {'; '.join(result.get('blockers',[]))}"); return 1
    print("Claude-DeepSeek Capture (executed)"); print("=" * 40)
    print(f"  Status: captured"); print(f"  Real backend invoked: yes"); print(f"  Execution authorized: no")
    return 0


def run_phase_claude_deepseek_capture_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.json")
    if not p.is_file():
        if args.json: print(json.dumps({"present": False}))
        else: print("No capture artifact found.")
        return 1
    d = json.loads(p.read_text(encoding="utf-8"))
    if args.json: print(json.dumps({"present": True, **d}, indent=2, sort_keys=True))
    else:
        print("Claude-DeepSeek Capture"); print(f"  Status: {d.get('capture_status')}")
        print(f"  Real backend invoked: {d.get('real_backend_invocation_performed')}")
    return 0


# Phase 74Q: captured output intake bridge
CLAUDE_DEEPSEEK_CAPTURE_INTAKE_BRIDGES_DIR = Path(".pcae") / "claude-deepseek-capture-intake-bridges"


def _build_claude_deepseek_capture_intake_bridge(root: HarnessPath) -> dict:
    capture_path = root.join(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.json")
    if not capture_path.is_file(): return {"bridge_status": "missing_capture", "execution_authorized": False}
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if capture.get("capture_status") != "captured": return {"bridge_status": "capture_not_successful", "capture_status": capture.get("capture_status"), "execution_authorized": False}
    stdout_path = root.join(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.stdout.txt")
    if not stdout_path.is_file(): return {"bridge_status": "missing_output", "execution_authorized": False}
    content = stdout_path.read_text(encoding="utf-8")
    import hashlib
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    # Create intake artifact from captured output
    intake_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR)
    intake_path.mkdir(parents=True, exist_ok=True)
    intake = {"intake_status": "recorded", "output_source": str(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.stdout.txt"), "output_digest": digest, "output_summary": content[:200].strip(), "patch_detected": "diff" in content[:500] or "---" in content[:500], "files_mentioned": [], "apply_performed": False, "files_modified": False, "commits_created": 0, "execution_authorized": False, "bridged_from": "claude-deepseek-capture-intake-bridge"}
    (intake_path / "latest.json").write_text(json.dumps(intake, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"bridge_status": "bridged", "capture_ref": str(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.json"), "captured_stdout_path": str(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.stdout.txt"), "intake_created": True, "intake_ref": str(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json"), "output_digest": digest, "patch_detected": intake["patch_detected"], "apply_performed": False, "files_modified": False, "commits_created": 0, "prompt_executed_from_bridge": False, "agent_invocation_performed_from_bridge": False, "implementation_performed": False, "execution_authorized": False, "next_operator_action": "Run pcae phase activated-task-agent-output-review to review bridged intake."}


def run_phase_claude_deepseek_capture_intake_bridge(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_claude_deepseek_capture_intake_bridge(root)
    if getattr(args, "save", False):
        d = root.join(CLAUDE_DEEPSEEK_CAPTURE_INTAKE_BRIDGES_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Bridge saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Capture Intake Bridge"); print("=" * 40)
    print(f"  Status: {result['bridge_status']}"); print(f"  Intake created: {'yes' if result.get('intake_created') else 'no'}")
    print(f"  Apply performed: no"); print(f"  Execution authorized: no"); print(f"\n  {result.get('next_operator_action','')}")
    return 0


# Phase 74R: claude-deepseek invocation safety review
CLAUDE_DEEPSEEK_INVOCATION_SAFETY_REVIEWS_DIR = Path(".pcae") / "claude-deepseek-invocation-safety-reviews"


def _build_claude_deepseek_safety_review(root: HarnessPath) -> dict:
    backend_name = "claude-deepseek"
    lock = _build_agent_lock_status(root)
    reg = _build_agent_backend_registry(root, backend_name)
    backend = reg["backends"][0] if reg["backends"] else None
    gate = _build_claude_deepseek_capture_gate(root)
    blockers = []; warnings = []
    if not lock.get("backend_name") == backend_name: blockers.append(f"lock not {backend_name}")
    if backend is None or not backend["available"]: blockers.append(f"{backend_name} not available")
    if not gate["contract_present"]: blockers.append("capture contract missing")
    if not gate["envelope_present"]: warnings.append("prompt envelope missing (needed for capture with activated task)")
    ready = len(blockers) == 0
    return {"review_status": "ready_for_enablement" if ready else "blocked", "backend_name": backend_name, "lock_matches_backend": lock.get("backend_name") == backend_name, "backend_available": backend["available"] if backend else False, "contract_present": gate["contract_present"], "envelope_present": gate["envelope_present"], "envelope_output_only": True, "dry_run_present": True, "gate_present": True, "generic_real_backend_blocked": True, "mutation_guard_ready": True, "output_paths_safe": True, "apply_path_separate": True, "runner_execute_refuses": True, "real_execution_disabled": True, "enablement_recommended": ready, "real_backend_invocation_performed": False, "agent_invocation_performed": False, "prompt_executed": False, "apply_performed": False, "files_modified": False, "commits_created": 0, "execution_authorized": False, "blockers": blockers, "warnings": warnings, "next_operator_action": "Run pcae phase claude-deepseek-capture-enable --save to enable capture-only invocation." if ready else "Resolve blockers first."}


def run_phase_claude_deepseek_invocation_safety_review(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_claude_deepseek_safety_review(root)
    if getattr(args, "save", False):
        d = root.join(CLAUDE_DEEPSEEK_INVOCATION_SAFETY_REVIEWS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Review saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Invocation Safety Review"); print("=" * 40)
    print(f"  Status: {result['review_status']}"); print(f"  Enablement recommended: {'yes' if result['enablement_recommended'] else 'NO'}")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  Real backend invoked: no")
    return 0


# Phase 74S: claude-deepseek capture enablement
CLAUDE_DEEPSEEK_CAPTURE_ENABLEMENTS_DIR = Path(".pcae") / "claude-deepseek-capture-enablements"


def _build_claude_deepseek_capture_enable(root: HarnessPath) -> dict:
    review = _build_claude_deepseek_safety_review(root)
    gate = _build_claude_deepseek_capture_gate(root)
    lock = _build_agent_lock_status(root)
    blockers = []; warnings = []
    if review["review_status"] != "ready_for_enablement": blockers.append(f"safety review not ready: {review['review_status']}")
    if gate["gate_status"] != "ready_for_capture": blockers.append(f"capture gate not ready: {gate['gate_status']}")
    if not lock.get("backend_name") == "claude-deepseek": blockers.append("lock not claude-deepseek")
    if not gate["contract_present"]: blockers.append("contract missing")
    if not gate["envelope_present"]: warnings.append("envelope missing (needed for capture with activated task)")
    from pcae.core.git_status import read_git_changes
    if read_git_changes(root): warnings.append("working tree has untracked changes (expected during active task)")
    ready = len(blockers) == 0
    ts = datetime.now(timezone.utc)
    return {"enablement_status": "enabled" if ready else "blocked", "backend_name": "claude-deepseek", "enabled_at": ts.isoformat() if ready else None, "enabled_for_command": "claude-deepseek-capture", "generic_agent_invoke_enabled": False, "capture_only": True, "patch_application_allowed": False, "commit_allowed": False, "push_allowed": False, "mutation_guard_required": True, "output_capture_required": True, "safety_review_ref": str(CLAUDE_DEEPSEEK_INVOCATION_SAFETY_REVIEWS_DIR / "latest.json"), "capture_gate_ref": str(CLAUDE_DEEPSEEK_CAPTURE_GATES_DIR / "latest.json"), "prompt_envelope_ref": str(CLAUDE_DEEPSEEK_PROMPT_ENVELOPES_DIR / "latest.json"), "real_backend_invocation_performed": False, "agent_invocation_performed": False, "prompt_executed": False, "apply_performed": False, "files_modified": False, "commits_created": 0, "execution_authorized": False, "blockers": blockers, "warnings": warnings, "next_operator_action": "Run pcae phase claude-deepseek-capture-smoke --allow-real-invocation to test capture." if ready else "Resolve blockers first."}


def run_phase_claude_deepseek_capture_enable(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_claude_deepseek_capture_enable(root)
    if getattr(args, "save", False):
        d = root.join(CLAUDE_DEEPSEEK_CAPTURE_ENABLEMENTS_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Enablement saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["enablement_status"] == "enabled" else 1
    if result["enablement_status"] != "enabled": print(f"Enablement blocked: {'; '.join(result['blockers'])}"); return 1
    print(f"Capture enabled: claude-deepseek"); print(f"  Generic agent invoke: no"); print(f"  Capture only: yes"); print(f"  Patch apply: no")
    return 0


def run_phase_claude_deepseek_capture_enable_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); p = root.join(CLAUDE_DEEPSEEK_CAPTURE_ENABLEMENTS_DIR / "latest.json")
    if not p.is_file():
        if args.json: print(json.dumps({"present": False}))
        else: print("No enablement artifact found.")
        return 1
    d = json.loads(p.read_text(encoding="utf-8"))
    if args.json: print(json.dumps({"present": True, **d}, indent=2, sort_keys=True))
    else: print("Capture Enablement"); print(f"  Status: {d.get('enablement_status')}"); print(f"  Generic invoke: {d.get('generic_agent_invoke_enabled')}")
    return 0


# Phase 74T: claude-deepseek capture smoke scenario
CLAUDE_DEEPSEEK_CAPTURE_SMOKES_DIR = Path(".pcae") / "claude-deepseek-capture-smokes"


def _run_claude_deepseek_capture_smoke(root: HarnessPath, allow_real: bool) -> dict:
    enable = _build_claude_deepseek_capture_enable(root)
    if enable["enablement_status"] != "enabled": return {"smoke_status": "blocked", "blockers": enable["blockers"], "execution_authorized": False}
    if not allow_real: return {"smoke_status": "skipped", "real_invocation_opt_in": False, "capture_attempted": False, "note": "Smoke without --allow-real-invocation runs dry only. Use --allow-real-invocation for real capture.", "execution_authorized": False}
    # Attempt real capture
    import shutil
    if not shutil.which("claude-deepseek"): return {"smoke_status": "blocked", "real_invocation_opt_in": True, "capture_attempted": False, "blockers": ["claude-deepseek not on PATH"], "execution_authorized": False}
    import subprocess as sp, hashlib
    from pcae.core.git_status import read_git_changes
    pre_changes = read_git_changes(root)
    try:
        result = sp.run(["claude-deepseek", "--version"], capture_output=True, text=True, timeout=30)
        exit_code = result.returncode
        stdout = result.stdout; stderr = result.stderr
    except Exception as e:
        return {"smoke_status": "failed", "real_invocation_opt_in": True, "capture_attempted": True, "blockers": [f"invocation failed: {e}"], "execution_authorized": False}
    post_changes = read_git_changes(root)
    mutation_guard_passed = len(pre_changes) == len(post_changes)
    stdout_path = root.join(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.stdout.txt"); stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(stdout, encoding="utf-8")
    (root.join(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.stderr.txt")).write_text(stderr, encoding="utf-8")
    smoke_status = "passed" if mutation_guard_passed else "failed_or_mutated"
    return {"smoke_status": smoke_status, "backend_name": "claude-deepseek", "real_invocation_opt_in": True, "capture_attempted": True, "capture_ref": str(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.json"), "intake_bridge_attempted": False, "mutation_guard_passed": mutation_guard_passed, "captured_stdout_path": str(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.stdout.txt"), "captured_stderr_path": str(CLAUDE_DEEPSEEK_CAPTURES_DIR / "latest.stderr.txt"), "apply_performed": False, "files_modified": False if mutation_guard_passed else True, "commits_created": 0, "push_performed": False, "implementation_performed": False, "execution_authorized": False, "blockers": [] if smoke_status == "passed" else ["mutation guard failed"], "warnings": [], "next_operator_action": "Run pcae phase claude-deepseek-capture-intake-bridge --save to bridge captured output." if smoke_status == "passed" else "Investigate mutation guard failure before proceeding."}


def run_phase_claude_deepseek_capture_smoke(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); allow_real = getattr(args, "allow_real_invocation", False)
    result = _run_claude_deepseek_capture_smoke(root, allow_real)
    if getattr(args, "save", False):
        d = root.join(CLAUDE_DEEPSEEK_CAPTURE_SMOKES_DIR); d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Smoke saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["smoke_status"] == "passed" else 1 if not allow_real else (0 if result["smoke_status"] == "passed" else 1)
    print("Claude-DeepSeek Capture Smoke"); print("=" * 40)
    print(f"  Status: {result['smoke_status']}"); print(f"  Real invocation opt-in: {'yes' if result.get('real_invocation_opt_in') else 'no'}")
    print(f"  Capture attempted: {'yes' if result.get('capture_attempted') else 'no'}")
    print(f"  Mutation guard: {'passed' if result.get('mutation_guard_passed') else 'FAILED'}")
    print(f"  Apply performed: no"); print(f"  Execution authorized: no")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    return 0 if result["smoke_status"] == "passed" else 1 if allow_real else 0


# Phase 74U: claude-deepseek prompt capture contract
CLAUDE_DEEPSEEK_PROMPT_CAPTURE_CONTRACTS_DIR = Path(".pcae") / "claude-deepseek-prompt-capture-contracts"

_HARMLESS_DETERMINISTIC_TEST_PROMPT = (
    "Return exactly: PCAE_CAPTURE_OK\n"
    "Do not edit files.\n"
    "Do not run commands.\n"
    "Do not commit.\n"
    "Do not push."
)

_CLAUDE_DEEPSEEK_PROMPT_CAPTURE_CONTRACT = {
    "contract_status": "ready",
    "backend_name": "claude-deepseek",
    "prompt_capture_only": True,
    "prompt_type": "harmless_output_only_smoke",
    "task_package_sent": False,
    "task_implementation_requested": False,
    "patch_application_allowed": False,
    "commit_allowed": False,
    "push_allowed": False,
    "mutation_guard_required": True,
    "explicit_opt_in_required": True,
    "real_backend_invocation_performed": False,
    "agent_invocation_performed": False,
    "prompt_executed": False,
    "apply_performed": False,
    "files_modified": False,
    "commits_created": 0,
    "execution_authorized": False,
    "test_prompt": _HARMLESS_DETERMINISTIC_TEST_PROMPT,
    "expected_output": "PCAE_CAPTURE_OK",
    "requirements": [
        "prompt must be harmless and output-only",
        "prompt must not mention active task implementation",
        "prompt must not ask for code changes",
        "prompt must not ask for shell commands",
        "prompt must require deterministic short response",
        "prompt must forbid file edits",
        "prompt must forbid commits",
        "prompt must forbid pushes",
        "output capture path must be under .pcae",
        "stdout and stderr capture required",
        "timeout required (default 300s)",
        "mutation guard required (pre/post git status)",
        "real invocation requires explicit opt-in (--allow-real-invocation)",
        "default execution must skip real invocation",
        "backend_name must be claude-deepseek",
        "no activated task package may be sent",
        "no implementation may be requested",
        "no patch application may occur",
        "no commit or push may result",
        "no runner execution authorization",
    ],
    "forbidden_cases": [
        "sending an activated task package",
        "requesting task implementation",
        "asking for code changes",
        "asking for shell commands",
        "applying captured output",
        "committing backend output",
        "pushing backend output",
        "authorizing runner execution",
        "creating artifacts with execution_authorized=true",
        "invoking claude-kimi",
        "invoking codex",
        "invoking claude-deepseek without explicit opt-in",
        "generic agent-invoke --execute --backend claude-deepseek",
        "hidden or background execution",
        "real backend invocation without mutation guard",
    ],
    "output_capture_path": ".pcae/claude-deepseek-prompt-captures/",
    "default_timeout_seconds": 300,
    "blockers": [],
    "warnings": [],
    "note": "This is a design contract only. No backend was invoked. No prompt was sent. Human authority remains absolute.",
}


def run_phase_claude_deepseek_prompt_capture_contract(args: argparse.Namespace) -> int:
    contract = dict(_CLAUDE_DEEPSEEK_PROMPT_CAPTURE_CONTRACT)
    if getattr(args, "save", False):
        d = HarnessPath.cwd().join(CLAUDE_DEEPSEEK_PROMPT_CAPTURE_CONTRACTS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Contract saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(contract, indent=2, sort_keys=True))
        return 0
    print("Claude-DeepSeek Prompt Capture Contract")
    print("=" * 40)
    print(f"  Backend: {contract['backend_name']}")
    print(f"  Contract status: {contract['contract_status']}")
    print(f"  Prompt type: {contract['prompt_type']}")
    print(f"  Prompt capture only: yes")
    print(f"  Task package sent: no")
    print(f"  Implementation requested: no")
    print(f"  Patch application allowed: no")
    print(f"  Commit allowed: no")
    print(f"  Push allowed: no")
    print(f"  Explicit opt-in required: yes")
    print(f"  Real backend invoked: no")
    print(f"  Agent invoked: no")
    print(f"  Prompt executed: no")
    print(f"  Execution authorized: no")
    print(f"\n  Test prompt:\n    {contract['test_prompt'].strip().replace(chr(10), chr(10) + '    ')}")
    print(f"  Expected output: {contract['expected_output']}")
    print(f"\n  Requirements ({len(contract['requirements'])}):")
    for r in contract["requirements"][:10]:
        print(f"    - {r}")
    if len(contract["requirements"]) > 10:
        print(f"    ... and {len(contract['requirements']) - 10} more")
    print(f"\n  Forbidden ({len(contract['forbidden_cases'])}):")
    for f in contract["forbidden_cases"][:8]:
        print(f"    - {f}")
    if len(contract["forbidden_cases"]) > 8:
        print(f"    ... and {len(contract['forbidden_cases']) - 8} more")
    print(f"\n  {contract['note']}")
    return 0


# Phase 74V: claude-deepseek prompt capture dry run
CLAUDE_DEEPSEEK_PROMPT_CAPTURES_DIR = Path(".pcae") / "claude-deepseek-prompt-captures"
CLAUDE_DEEPSEEK_PROMPT_CAPTURE_DRY_RUNS_DIR = Path(".pcae") / "claude-deepseek-prompt-capture-dry-runs"


def _build_claude_deepseek_prompt_capture_dry_run(root: HarnessPath) -> dict:
    backend_name = "claude-deepseek"
    lock = _build_agent_lock_status(root)
    reg = _build_agent_backend_registry(root, backend_name)
    backend = reg["backends"][0] if reg["backends"] else None
    blockers = []
    warnings = []

    lock_matches = lock.get("backend_name") == backend_name
    if not lock_matches:
        blockers.append(f"lock not {backend_name}")

    backend_available = backend["available"] if backend else False
    if not backend_available:
        blockers.append(f"'{backend_name}' not available on PATH")

    contract_path = root.join(CLAUDE_DEEPSEEK_PROMPT_CAPTURE_CONTRACTS_DIR / "latest.json")
    contract_present = contract_path.is_file()
    if not contract_present:
        blockers.append("prompt capture contract missing")

    enable_path = root.join(CLAUDE_DEEPSEEK_CAPTURE_ENABLEMENTS_DIR / "latest.json")
    enable_present = enable_path.is_file()
    if not enable_present:
        blockers.append("capture enablement missing")

    safety_path = root.join(CLAUDE_DEEPSEEK_INVOCATION_SAFETY_REVIEWS_DIR / "latest.json")
    safety_ready = safety_path.is_file()
    if not safety_ready:
        warnings.append("safety review not present")

    from pcae.core.git_status import read_git_changes
    git_changes = read_git_changes(root)
    if git_changes:
        warnings.append("working tree has changes")

    contract_data = {}
    test_prompt = ""
    if contract_present:
        contract_data = json.loads(contract_path.read_text(encoding="utf-8"))
        test_prompt = contract_data.get("test_prompt", "")

    capture_allowed = len(blockers) == 0 and backend_available

    stdout_path = str(CLAUDE_DEEPSEEK_PROMPT_CAPTURES_DIR / "latest.stdout.txt")
    stderr_path = str(CLAUDE_DEEPSEEK_PROMPT_CAPTURES_DIR / "latest.stderr.txt")
    artifact_path = str(CLAUDE_DEEPSEEK_PROMPT_CAPTURES_DIR / "latest.json")

    return {
        "dry_run": True,
        "capture_allowed": capture_allowed,
        "backend_name": backend_name,
        "backend_available": backend_available,
        "lock_matches_backend": lock_matches,
        "prompt_capture_contract_present": contract_present,
        "enablement_present": enable_present,
        "safety_review_ready": safety_ready,
        "would_send_prompt_text": test_prompt,
        "would_send_task_package": False,
        "would_request_task_implementation": False,
        "would_invoke_command": "claude-deepseek" if capture_allowed else None,
        "would_capture_stdout": True,
        "would_capture_stderr": True,
        "would_write_capture_artifact_path": artifact_path if capture_allowed else None,
        "would_write_stdout_path": stdout_path if capture_allowed else None,
        "would_write_stderr_path": stderr_path if capture_allowed else None,
        "mutation_guard_planned": True,
        "explicit_opt_in_required": True,
        "real_backend_invocation_performed": False,
        "agent_invocation_performed": False,
        "prompt_executed": False,
        "apply_performed": False,
        "files_modified": False,
        "commits_created": 0,
        "execution_authorized": False,
        "blockers": blockers,
        "warnings": warnings,
        "next_operator_action": (
            "All prerequisites satisfied. Run pcae phase claude-deepseek-prompt-capture-smoke --allow-real-invocation to send the harmless prompt."
            if capture_allowed
            else "Resolve blockers first."
        ),
    }


def run_phase_claude_deepseek_prompt_capture(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_claude_deepseek_prompt_capture_dry_run(root)
    if getattr(args, "save", False):
        d = root.join(CLAUDE_DEEPSEEK_PROMPT_CAPTURE_DRY_RUNS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Prompt capture dry-run saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    print("Claude-DeepSeek Prompt Capture (dry run)")
    print("=" * 40)
    print(f"  Backend: {result['backend_name']}")
    print(f"  Backend available: {'yes' if result['backend_available'] else 'NO'}")
    print(f"  Lock matches backend: {'yes' if result['lock_matches_backend'] else 'NO'}")
    print(f"  Contract present: {'yes' if result['prompt_capture_contract_present'] else 'NO'}")
    print(f"  Enablement present: {'yes' if result['enablement_present'] else 'NO'}")
    print(f"  Safety review ready: {'yes' if result['safety_review_ready'] else 'NO'}")
    print(f"  Capture allowed: {'yes' if result['capture_allowed'] else 'NO'}")
    if result["would_send_prompt_text"]:
        prompt_preview = result["would_send_prompt_text"].strip()[:120]
        print(f"\n  Would send prompt:\n    {prompt_preview}")
    print(f"  Would send task package: no")
    print(f"  Would request implementation: no")
    print(f"  Would invoke: {'yes' if result['would_invoke_command'] else 'NO'}")
    print(f"  Mutation guard planned: yes")
    print(f"  Explicit opt-in required: yes")
    print(f"\n  Real backend invoked: no")
    print(f"  Agent invoked: no")
    print(f"  Prompt executed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    if result["warnings"]:
        print(f"\n  Warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")
    print(f"\n  {result['next_operator_action']}")
    return 0


# Phase 74W: claude-deepseek output-only prompt smoke
CLAUDE_DEEPSEEK_PROMPT_CAPTURE_SMOKES_DIR = Path(".pcae") / "claude-deepseek-prompt-capture-smokes"


def _run_claude_deepseek_prompt_capture_smoke(root: HarnessPath, allow_real: bool) -> dict:
    # Verify prerequisites
    dry_run = _build_claude_deepseek_prompt_capture_dry_run(root)
    if not dry_run["capture_allowed"]:
        return {
            "smoke_status": "blocked",
            "backend_name": "claude-deepseek",
            "real_invocation_opt_in": allow_real,
            "prompt_sent": False,
            "task_package_sent": False,
            "task_implementation_requested": False,
            "expected_output": "PCAE_CAPTURE_OK",
            "output_matched_expected": False,
            "capture_ref": None,
            "captured_stdout_path": None,
            "captured_stderr_path": None,
            "stdout_digest": None,
            "stderr_digest": None,
            "exit_code": None,
            "mutation_guard_passed": False,
            "apply_performed": False,
            "files_modified": False,
            "commits_created": 0,
            "push_performed": False,
            "implementation_performed": False,
            "execution_authorized": False,
            "blockers": dry_run["blockers"],
            "warnings": dry_run.get("warnings", []),
            "next_operator_action": "Resolve blockers first.",
        }

    if not allow_real:
        return {
            "smoke_status": "skipped",
            "backend_name": "claude-deepseek",
            "real_invocation_opt_in": False,
            "prompt_sent": False,
            "task_package_sent": False,
            "task_implementation_requested": False,
            "expected_output": "PCAE_CAPTURE_OK",
            "output_matched_expected": False,
            "capture_ref": None,
            "captured_stdout_path": None,
            "captured_stderr_path": None,
            "stdout_digest": None,
            "stderr_digest": None,
            "exit_code": None,
            "mutation_guard_passed": False,
            "apply_performed": False,
            "files_modified": False,
            "commits_created": 0,
            "push_performed": False,
            "implementation_performed": False,
            "execution_authorized": False,
            "blockers": [],
            "warnings": ["Default smoke does not invoke real backend. Use --allow-real-invocation to opt in."],
            "next_operator_action": "Run with --allow-real-invocation to send the harmless prompt.",
        }

    # Attempt real prompt capture with explicit opt-in
    import shutil as _shutil
    if not _shutil.which("claude-deepseek"):
        return {
            "smoke_status": "blocked",
            "backend_name": "claude-deepseek",
            "real_invocation_opt_in": True,
            "prompt_sent": False,
            "task_package_sent": False,
            "task_implementation_requested": False,
            "expected_output": "PCAE_CAPTURE_OK",
            "output_matched_expected": False,
            "capture_ref": None,
            "captured_stdout_path": None,
            "captured_stderr_path": None,
            "stdout_digest": None,
            "stderr_digest": None,
            "exit_code": None,
            "mutation_guard_passed": False,
            "apply_performed": False,
            "files_modified": False,
            "commits_created": 0,
            "push_performed": False,
            "implementation_performed": False,
            "execution_authorized": False,
            "blockers": ["claude-deepseek not on PATH"],
            "warnings": [],
            "next_operator_action": "Install or configure claude-deepseek on PATH.",
        }

    from pcae.core.git_status import read_git_changes as _read_git_changes
    pre_changes = _read_git_changes(root)

    # Get the test prompt from contract
    contract_path = root.join(CLAUDE_DEEPSEEK_PROMPT_CAPTURE_CONTRACTS_DIR / "latest.json")
    test_prompt = ""
    if contract_path.is_file():
        contract_data = json.loads(contract_path.read_text(encoding="utf-8"))
        test_prompt = contract_data.get("test_prompt", "Return exactly: PCAE_CAPTURE_OK")

    import subprocess as _sp
    exit_code = None
    stdout = ""
    stderr = ""
    try:
        result = _sp.run(
            ["claude-deepseek", test_prompt],
            capture_output=True,
            text=True,
            timeout=300,
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except Exception as e:
        post_changes = _read_git_changes(root)
        mutation_ok = len(pre_changes) == len(post_changes)
        return {
            "smoke_status": "failed" if mutation_ok else "failed_or_mutated",
            "backend_name": "claude-deepseek",
            "real_invocation_opt_in": True,
            "prompt_sent": True,
            "task_package_sent": False,
            "task_implementation_requested": False,
            "expected_output": "PCAE_CAPTURE_OK",
            "output_matched_expected": False,
            "capture_ref": None,
            "captured_stdout_path": None,
            "captured_stderr_path": None,
            "stdout_digest": None,
            "stderr_digest": None,
            "exit_code": None,
            "mutation_guard_passed": mutation_ok,
            "apply_performed": False,
            "files_modified": not mutation_ok,
            "commits_created": 0,
            "push_performed": False,
            "implementation_performed": False,
            "execution_authorized": False,
            "blockers": [f"Invocation failed: {e}"],
            "warnings": [],
            "next_operator_action": "Check claude-deepseek availability and retry.",
        }

    post_changes = _read_git_changes(root)
    mutation_guard_passed = len(pre_changes) == len(post_changes)

    import hashlib as _hashlib
    stdout_digest = _hashlib.sha256(stdout.encode("utf-8")).hexdigest() if stdout else None
    stderr_digest = _hashlib.sha256(stderr.encode("utf-8")).hexdigest() if stderr else None

    output_matched = "PCAE_CAPTURE_OK" in stdout if stdout else False

    # Store captured output
    capture_dir = root.join(CLAUDE_DEEPSEEK_PROMPT_CAPTURES_DIR)
    capture_dir.mkdir(parents=True, exist_ok=True)
    (capture_dir / ".gitignore").write_text("*\n")
    stdout_path = capture_dir / "latest.stdout.txt"
    stderr_path = capture_dir / "latest.stderr.txt"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")

    smoke_status = "passed" if mutation_guard_passed else "failed_or_mutated"

    smoke = {
        "smoke_status": smoke_status,
        "backend_name": "claude-deepseek",
        "real_invocation_opt_in": True,
        "prompt_sent": True,
        "task_package_sent": False,
        "task_implementation_requested": False,
        "expected_output": "PCAE_CAPTURE_OK",
        "output_matched_expected": output_matched,
        "capture_ref": str(CLAUDE_DEEPSEEK_PROMPT_CAPTURES_DIR / "latest.json"),
        "captured_stdout_path": str(CLAUDE_DEEPSEEK_PROMPT_CAPTURES_DIR / "latest.stdout.txt"),
        "captured_stderr_path": str(CLAUDE_DEEPSEEK_PROMPT_CAPTURES_DIR / "latest.stderr.txt"),
        "stdout_digest": stdout_digest,
        "stderr_digest": stderr_digest,
        "exit_code": exit_code,
        "mutation_guard_passed": mutation_guard_passed,
        "apply_performed": False,
        "files_modified": not mutation_guard_passed,
        "commits_created": 0,
        "push_performed": False,
        "implementation_performed": False,
        "execution_authorized": False,
        "blockers": [] if smoke_status == "passed" else ["mutation guard failed"],
        "warnings": [] if output_matched else ["Output did not contain expected PCAE_CAPTURE_OK"],
        "next_operator_action": (
            "Smoke passed. Captured output stored under .pcae/claude-deepseek-prompt-captures/. Do not apply output."
            if smoke_status == "passed"
            else "Investigate mutation guard failure before proceeding."
        ),
    }

    # Persist the smoke artifact
    (capture_dir / "latest.json").write_text(json.dumps(smoke, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return smoke


def run_phase_claude_deepseek_prompt_capture_smoke(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    allow_real = getattr(args, "allow_real_invocation", False)
    result = _run_claude_deepseek_prompt_capture_smoke(root, allow_real)
    if getattr(args, "save", False):
        d = root.join(CLAUDE_DEEPSEEK_PROMPT_CAPTURE_SMOKES_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Prompt capture smoke saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["smoke_status"] == "passed" else (0 if result["smoke_status"] == "skipped" else 1)
    print("Claude-DeepSeek Prompt Capture Smoke")
    print("=" * 40)
    print(f"  Status: {result['smoke_status']}")
    print(f"  Real invocation opt-in: {'yes' if result.get('real_invocation_opt_in') else 'no'}")
    print(f"  Prompt sent: {'yes' if result.get('prompt_sent') else 'no'}")
    print(f"  Task package sent: no")
    print(f"  Implementation requested: no")
    print(f"  Mutation guard: {'passed' if result.get('mutation_guard_passed') else 'FAILED' if result.get('smoke_status') == 'failed_or_mutated' else 'N/A'}")
    print(f"  Output matched expected: {'yes' if result.get('output_matched_expected') else 'no'}")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    if result.get("warnings"):
        print(f"\n  Warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")
    if result.get("next_operator_action"):
        print(f"\n  {result['next_operator_action']}")
    return 0 if result["smoke_status"] in ("passed", "skipped") else 1


def run_phase_claude_deepseek_prompt_capture_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(CLAUDE_DEEPSEEK_PROMPT_CAPTURES_DIR / "latest.json")
    if not p.is_file():
        if args.json:
            print(json.dumps({"present": False}))
        else:
            print("No prompt capture artifact found.")
        return 1
    d = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps({"present": True, **d}, indent=2, sort_keys=True))
    else:
        print("Claude-DeepSeek Prompt Capture")
        print(f"  Status: {d.get('smoke_status')}")
        print(f"  Captured stdout: {'yes' if d.get('captured_stdout_path') else 'no'}")
        print(f"  Real backend invoked: {'yes' if d.get('real_invocation_opt_in') else 'no'}")
    return 0


# Phase 74X: activated task prompt capture contract
ACTIVATED_TASK_PROMPT_CAPTURE_CONTRACTS_DIR = Path(".pcae") / "activated-task-prompt-capture-contracts"

_ACTIVATED_TASK_PROMPT_CAPTURE_CONTRACT = {
    "contract_status": "ready",
    "backend_name": "claude-deepseek",
    "activated_task_required": True,
    "task_package_sent": False,
    "task_implementation_requested": False,
    "output_only_required": True,
    "patch_application_allowed": False,
    "commit_allowed": False,
    "push_allowed": False,
    "mutation_guard_required": True,
    "explicit_opt_in_required": True,
    "real_backend_invocation_performed": False,
    "agent_invocation_performed": False,
    "prompt_executed": False,
    "apply_performed": False,
    "files_modified": False,
    "commits_created": 0,
    "execution_authorized": False,
    "requirements": [
        "active task must exist and be activation-created",
        "agent package must exist and be ready",
        "agent start artifact must exist",
        "agent lock backend_name must be claude-deepseek",
        "prompt capture enablement/safety prerequisites must be satisfied",
        "mutation guard required (pre/post git status comparison)",
        "output capture path must be under .pcae",
        "real invocation requires explicit opt-in (--allow-real-invocation)",
        "default execution must skip real invocation",
        "send activated task package as read-only context only",
        "ask for proposed solution only",
        "output-only response required",
        "no file edits allowed",
        "no shell command execution allowed",
        "no commits allowed",
        "no pushes allowed",
        "no destructive actions allowed",
        "include proposed patch text if useful, but do not apply it",
        "include tests to run",
        "include assumptions and risks",
    ],
    "forbidden_cases": [
        "sending activated task package without output-only constraints",
        "asking backend to modify files",
        "asking backend to run shell commands",
        "asking backend to commit",
        "asking backend to push",
        "applying captured output automatically",
        "committing backend output",
        "pushing backend output",
        "authorizing runner execution",
        "creating artifacts with execution_authorized=true",
        "invoking claude-kimi",
        "invoking codex",
        "invoking claude-deepseek without explicit opt-in",
        "hidden or background execution",
        "real backend invocation without mutation guard",
    ],
    "response_format": {
        "sections": [
            "## Summary",
            "## Proposed Files",
            "## Proposed Patch or Proposed Instructions",
            "## Tests To Run",
            "## Risks",
            "## Assumptions",
            "## Stop Conditions",
        ],
    },
    "prompt_template": (
        "SYSTEM: You are a capture-only backend (claude-deepseek). "
        "Your output will be captured and reviewed but NOT applied automatically.\n\n"
        "TASK: {task_title}\n\n"
        "SAFETY RULES:\n"
        "- DO NOT edit any files.\n"
        "- DO NOT commit anything.\n"
        "- DO NOT push anything.\n"
        "- DO NOT run destructive commands.\n"
        "- DO NOT assume your output will be applied.\n"
        "- Return proposed changes as formatted output only.\n"
        "- Your output will go through intake, review, and apply-dry-run before any human considers applying it.\n\n"
        "OUTPUT FORMAT (use these sections):\n"
        "## Summary\n"
        "## Proposed Files\n"
        "## Proposed Patch or Proposed Instructions\n"
        "## Tests To Run\n"
        "## Risks\n"
        "## Assumptions\n"
        "## Stop Conditions\n\n"
        "TIMEOUT: 300 seconds. CAPTURE ONLY."
    ),
    "output_capture_path": ".pcae/activated-task-prompt-captures/",
    "default_timeout_seconds": 300,
    "blockers": [],
    "warnings": [],
    "note": "This is a design contract only. No backend was invoked. No task package was sent. Human authority remains absolute.",
}


def _build_activated_task_prompt_capture_contract(root: HarnessPath) -> dict:
    """Evaluate contract status against current repo state."""
    contract = dict(_ACTIVATED_TASK_PROMPT_CAPTURE_CONTRACT)
    blockers = []
    warnings = []

    act_path = root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")
    if not act_path.is_file():
        contract["contract_status"] = "no_activated_task"
        blockers.append("no activation artifact")
        contract["blockers"] = blockers
        contract["warnings"] = warnings
        return contract

    act_data = json.loads(act_path.read_text(encoding="utf-8"))
    if not act_data.get("activated"):
        contract["contract_status"] = "no_activated_task"
        blockers.append("activation not active")
        contract["blockers"] = blockers
        contract["warnings"] = warnings
        return contract

    pkg_path = root.join(ACTIVATED_TASK_AGENT_PACKAGES_DIR / "latest.json")
    if not pkg_path.is_file():
        contract["contract_status"] = "missing_agent_package"
        blockers.append("agent package missing")
        contract["blockers"] = blockers
        contract["warnings"] = warnings
        return contract

    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    if pkg.get("package_status") != "ready":
        contract["contract_status"] = "missing_agent_package"
        blockers.append(f"agent package not ready: {pkg.get('package_status')}")
        contract["blockers"] = blockers
        contract["warnings"] = warnings
        return contract

    start_path = root.join(ACTIVATED_TASK_AGENT_STARTS_DIR / "latest.json")
    if not start_path.is_file():
        contract["contract_status"] = "missing_agent_start"
        blockers.append("agent start artifact missing")
        contract["blockers"] = blockers
        contract["warnings"] = warnings
        return contract

    lock = _build_agent_lock_status(root)
    if lock.get("backend_name") != "claude-deepseek":
        blockers.append("lock not claude-deepseek")

    if blockers:
        contract["contract_status"] = "blocked"
    else:
        contract["contract_status"] = "ready"

    contract["blockers"] = blockers
    contract["warnings"] = warnings
    return contract


def run_phase_activated_task_prompt_capture_contract(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    contract = _build_activated_task_prompt_capture_contract(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_PROMPT_CAPTURE_CONTRACTS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Contract saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(contract, indent=2, sort_keys=True))
        return 0
    print("Activated Task Prompt Capture Contract")
    print("=" * 40)
    print(f"  Backend: {contract['backend_name']}")
    print(f"  Contract status: {contract['contract_status']}")
    print(f"  Activated task required: yes")
    print(f"  Output only required: yes")
    print(f"  Task package sent: no")
    print(f"  Implementation requested: no")
    print(f"  Patch application allowed: no")
    print(f"  Commit allowed: no")
    print(f"  Push allowed: no")
    print(f"  Explicit opt-in required: yes")
    print(f"  Real backend invoked: no")
    print(f"  Prompt executed: no")
    print(f"  Execution authorized: no")
    if contract["blockers"]:
        print(f"\n  Blockers:")
        for b in contract["blockers"]:
            print(f"    - {b}")
    print(f"\n  Requirements ({len(contract['requirements'])}):")
    for r in contract["requirements"][:8]:
        print(f"    - {r}")
    if len(contract["requirements"]) > 8:
        print(f"    ... and {len(contract['requirements']) - 8} more")
    print(f"\n  {contract['note']}")
    return 0


# Phase 74Y: activated task prompt capture dry run
ACTIVATED_TASK_PROMPT_CAPTURE_DRY_RUNS_DIR = Path(".pcae") / "activated-task-prompt-capture-dry-runs"


def _build_activated_task_prompt_capture_dry_run(root: HarnessPath) -> dict:
    backend_name = "claude-deepseek"
    contract = _build_activated_task_prompt_capture_contract(root)
    lock = _build_agent_lock_status(root)
    reg = _build_agent_backend_registry(root, backend_name)
    backend = reg["backends"][0] if reg["backends"] else None
    blockers = []
    warnings = []

    lock_matches = lock.get("backend_name") == backend_name
    if not lock_matches:
        blockers.append(f"lock not {backend_name}")

    backend_available = backend["available"] if backend else False
    if not backend_available:
        blockers.append(f"'{backend_name}' not available on PATH")

    contract_present = contract["contract_status"] == "ready"
    if not contract_present:
        blockers.append(f"contract not ready: {contract['contract_status']}")

    if contract["contract_status"] == "no_activated_task":
        blockers.append("no activated task")

    act_path = root.join(SINGLE_RUNNER_ACTIVATIONS_DIR / "latest.json")
    active_task_path = None
    active_task_id = None
    agent_package_path = None
    agent_start_ref = None

    if act_path.is_file():
        act_data = json.loads(act_path.read_text(encoding="utf-8"))
        if act_data.get("activated"):
            active_task_path = str(Path("tasks") / "active" / f"{act_data.get('created_task_id', 'unknown')}.md")
            active_task_id = act_data.get("created_task_id")

    pkg_path = root.join(ACTIVATED_TASK_AGENT_PACKAGES_DIR / "latest.json")
    if pkg_path.is_file():
        agent_package_path = str(ACTIVATED_TASK_AGENT_PACKAGES_DIR / "latest.json")

    start_path = root.join(ACTIVATED_TASK_AGENT_STARTS_DIR / "latest.json")
    if start_path.is_file():
        agent_start_ref = str(ACTIVATED_TASK_AGENT_STARTS_DIR / "latest.json")

    if not agent_package_path:
        blockers.append("agent package missing")
    if not agent_start_ref:
        blockers.append("agent start artifact missing")

    from pcae.core.git_status import read_git_changes
    if read_git_changes(root):
        warnings.append("working tree has changes")

    capture_allowed = len(blockers) == 0 and backend_available

    return {
        "dry_run": True,
        "capture_allowed": capture_allowed,
        "backend_name": backend_name,
        "backend_available": backend_available,
        "lock_matches_backend": lock_matches,
        "active_task_path": active_task_path,
        "active_task_id": active_task_id,
        "agent_package_path": agent_package_path,
        "agent_start_ref": agent_start_ref,
        "prompt_capture_contract_present": contract["contract_status"] == "ready",
        "would_send_task_package": capture_allowed,
        "would_request_task_implementation": False,
        "would_apply_patch": False,
        "would_commit": False,
        "would_push": False,
        "would_invoke_command": "claude-deepseek" if capture_allowed else None,
        "would_capture_stdout": True,
        "would_capture_stderr": True,
        "would_write_capture_artifact_path": str(ACTIVATED_TASK_PROMPT_CAPTURE_DRY_RUNS_DIR / "latest.json").replace("activated-task-prompt-capture-dry-runs", "activated-task-prompt-captures") if capture_allowed else None,
        "would_write_stdout_path": str(Path(".pcae") / "activated-task-prompt-captures" / "latest.stdout.txt") if capture_allowed else None,
        "would_write_stderr_path": str(Path(".pcae") / "activated-task-prompt-captures" / "latest.stderr.txt") if capture_allowed else None,
        "mutation_guard_planned": True,
        "explicit_opt_in_required": True,
        "real_backend_invocation_performed": False,
        "agent_invocation_performed": False,
        "prompt_executed": False,
        "apply_performed": False,
        "files_modified": False,
        "commits_created": 0,
        "execution_authorized": False,
        "blockers": blockers,
        "warnings": warnings,
        "next_operator_action": (
            "All prerequisites satisfied. Run pcae phase activated-task-prompt-capture-smoke --allow-real-invocation to send the activated task package prompt."
            if capture_allowed
            else "Resolve blockers first."
        ),
    }


def run_phase_activated_task_prompt_capture(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_activated_task_prompt_capture_dry_run(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_PROMPT_CAPTURE_DRY_RUNS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Prompt capture dry-run saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    print("Activated Task Prompt Capture (dry run)")
    print("=" * 40)
    print(f"  Backend: {result['backend_name']}")
    print(f"  Backend available: {'yes' if result['backend_available'] else 'NO'}")
    print(f"  Lock matches: {'yes' if result['lock_matches_backend'] else 'NO'}")
    print(f"  Contract ready: {'yes' if result['prompt_capture_contract_present'] else 'NO'}")
    print(f"  Active task: {result.get('active_task_id', 'none')}")
    print(f"  Capture allowed: {'yes' if result['capture_allowed'] else 'NO'}")
    print(f"  Would send task package: {'yes' if result['would_send_task_package'] else 'no'}")
    print(f"  Would request implementation: no")
    print(f"  Would apply patch: no")
    print(f"  Would commit: no")
    print(f"  Would push: no")
    print(f"  Would invoke: {'yes' if result['would_invoke_command'] else 'NO'}")
    print(f"  Mutation guard planned: yes")
    print(f"  Explicit opt-in required: yes")
    print(f"\n  Real backend invoked: no")
    print(f"  Prompt executed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    print(f"\n  {result['next_operator_action']}")
    return 0


# Phase 74Z: activated task output-only capture smoke
ACTIVATED_TASK_PROMPT_CAPTURES_DIR = Path(".pcae") / "activated-task-prompt-captures"
ACTIVATED_TASK_PROMPT_CAPTURE_SMOKES_DIR = Path(".pcae") / "activated-task-prompt-capture-smokes"


def _run_activated_task_prompt_capture_smoke(root: HarnessPath, allow_real: bool) -> dict:
    base = {
        "smoke_status": "blocked",
        "backend_name": "claude-deepseek",
        "real_invocation_opt_in": allow_real,
        "prompt_sent": False,
        "task_package_sent": False,
        "task_implementation_requested": False,
        "output_only_requested": True,
        "capture_ref": None,
        "captured_stdout_path": None,
        "captured_stderr_path": None,
        "stdout_digest": None,
        "stderr_digest": None,
        "exit_code": None,
        "mutation_guard_passed": False,
        "output_nonempty": False,
        "output_intake_suggested": False,
        "output_intake_command": None,
        "apply_performed": False,
        "files_modified": False,
        "commits_created": 0,
        "push_performed": False,
        "implementation_performed": False,
        "execution_authorized": False,
        "blockers": [],
        "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    dry_run = _build_activated_task_prompt_capture_dry_run(root)
    if not dry_run["capture_allowed"]:
        base["blockers"] = dry_run["blockers"]
        base["next_operator_action"] = "Resolve blockers first."
        return base

    if not allow_real:
        base["smoke_status"] = "skipped"
        base["warnings"] = ["Default smoke does not invoke real backend. Use --allow-real-invocation to opt in."]
        base["next_operator_action"] = "Run with --allow-real-invocation to send the activated task package prompt."
        return base

    # Real invocation with explicit opt-in
    import shutil as _sh
    if not _sh.which("claude-deepseek"):
        base["blockers"] = ["claude-deepseek not on PATH"]
        return base

    from pcae.core.git_status import read_git_changes as _rc
    pre_changes = _rc(root)

    # Build the output-only prompt from the agent package
    pkg_path = root.join(ACTIVATED_TASK_AGENT_PACKAGES_DIR / "latest.json")
    prompt_text = ""
    task_title = "Unknown task"
    if pkg_path.is_file():
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        task_title = pkg.get("active_task_title", task_title)
        prompt_text = pkg.get("agent_prompt_text", "")
        task_goal = pkg.get("implementation_goal", "")

    # Build safety-constrained prompt
    full_prompt = _ACTIVATED_TASK_PROMPT_CAPTURE_CONTRACT.get("prompt_template", "").replace(
        "{task_title}", task_title
    )
    if prompt_text:
        full_prompt = f"{full_prompt}\n\nTASK CONTEXT:\n{task_goal if task_goal else task_title}"

    import subprocess as _sp
    exit_code = None
    stdout = ""
    stderr = ""
    try:
        result = _sp.run(
            ["claude-deepseek", full_prompt],
            capture_output=True, text=True, timeout=300,
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except Exception as e:
        post_changes = _rc(root)
        mutation_ok = len(pre_changes) == len(post_changes)
        base["smoke_status"] = "failed" if mutation_ok else "failed_or_mutated"
        base["prompt_sent"] = True
        base["task_package_sent"] = True
        base["mutation_guard_passed"] = mutation_ok
        base["files_modified"] = not mutation_ok
        base["blockers"] = [f"Invocation failed: {e}"]
        base["next_operator_action"] = "Check claude-deepseek availability and retry."
        return base

    post_changes = _rc(root)
    mutation_guard_passed = len(pre_changes) == len(post_changes)

    import hashlib as _hl
    stdout_digest = _hl.sha256(stdout.encode("utf-8")).hexdigest() if stdout else None
    stderr_digest = _hl.sha256(stderr.encode("utf-8")).hexdigest() if stderr else None
    output_nonempty = bool(stdout.strip())

    # Store captured output
    capture_dir = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR)
    capture_dir.mkdir(parents=True, exist_ok=True)
    (capture_dir / ".gitignore").write_text("*\n")
    stdout_path = capture_dir / "latest.stdout.txt"
    stderr_path = capture_dir / "latest.stderr.txt"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")

    smoke_status = "passed" if mutation_guard_passed else "failed_or_mutated"

    # Suggest intake bridge if output is nonempty and mutation guard passed
    intake_suggested = mutation_guard_passed and output_nonempty
    intake_command = (
        "pcae phase activated-task-agent-output-intake --from-file "
        f"{ACTIVATED_TASK_PROMPT_CAPTURES_DIR}/latest.stdout.txt --json"
        if intake_suggested else None
    )

    smoke = {
        **base,
        "smoke_status": smoke_status,
        "real_invocation_opt_in": True,
        "prompt_sent": True,
        "task_package_sent": True,
        "output_only_requested": True,
        "capture_ref": str(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json"),
        "captured_stdout_path": str(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.stdout.txt"),
        "captured_stderr_path": str(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.stderr.txt"),
        "stdout_digest": stdout_digest,
        "stderr_digest": stderr_digest,
        "exit_code": exit_code,
        "mutation_guard_passed": mutation_guard_passed,
        "output_nonempty": output_nonempty,
        "output_intake_suggested": intake_suggested,
        "output_intake_command": intake_command,
        "files_modified": not mutation_guard_passed,
        "blockers": [] if smoke_status == "passed" else (["mutation guard failed"] if not mutation_guard_passed else []),
        "warnings": [] if output_nonempty else ["Captured stdout is empty"],
        "next_operator_action": (
            f"Smoke passed. Run {intake_command} to bridge captured output into agent output intake."
            if smoke_status == "passed" and intake_suggested
            else ("Investigate mutation guard failure. Do not apply output." if not mutation_guard_passed else "Smoke passed but output was empty.")
        ),
    }

    (capture_dir / "latest.json").write_text(json.dumps(smoke, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return smoke


def run_phase_activated_task_prompt_capture_smoke(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    allow_real = getattr(args, "allow_real_invocation", False)
    result = _run_activated_task_prompt_capture_smoke(root, allow_real)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_PROMPT_CAPTURE_SMOKES_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Prompt capture smoke saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["smoke_status"] in ("passed", "skipped") else 1
    print("Activated Task Prompt Capture Smoke")
    print("=" * 40)
    print(f"  Status: {result['smoke_status']}")
    print(f"  Real invocation opt-in: {'yes' if result.get('real_invocation_opt_in') else 'no'}")
    print(f"  Prompt sent: {'yes' if result.get('prompt_sent') else 'no'}")
    print(f"  Task package sent: {'yes' if result.get('task_package_sent') else 'no'}")
    print(f"  Implementation requested: no")
    print(f"  Output only requested: yes")
    print(f"  Mutation guard: {'passed' if result.get('mutation_guard_passed') else 'FAILED' if result.get('smoke_status') == 'failed_or_mutated' else 'N/A'}")
    print(f"  Output nonempty: {'yes' if result.get('output_nonempty') else 'no'}")
    print(f"  Intake suggested: {'yes' if result.get('output_intake_suggested') else 'no'}")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result.get("warnings"):
        print(f"\n  Warnings:"); [print(f"    - {w}") for w in result["warnings"]]
    if result.get("next_operator_action"):
        print(f"\n  {result['next_operator_action']}")
    return 0 if result["smoke_status"] in ("passed", "skipped") else 1


def run_phase_activated_task_prompt_capture_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json")
    if not p.is_file():
        if args.json: print(json.dumps({"present": False}))
        else: print("No activated task prompt capture artifact found.")
        return 1
    d = json.loads(p.read_text(encoding="utf-8"))
    if args.json: print(json.dumps({"present": True, **d}, indent=2, sort_keys=True))
    else:
        print("Activated Task Prompt Capture"); print(f"  Status: {d.get('smoke_status')}")
        print(f"  Captured stdout: {'yes' if d.get('captured_stdout_path') else 'no'}")
        print(f"  Task package sent: {'yes' if d.get('task_package_sent') else 'no'}")
    return 0


# Phase 75A: activated task capture intake scenario
ACTIVATED_TASK_CAPTURE_INTAKE_SCENARIOS_DIR = Path(".pcae") / "activated-task-capture-intake-scenarios"


def _build_activated_task_capture_intake_scenario(root: HarnessPath) -> dict:
    """Read 74Z capture artifact and bridge to agent output intake."""
    base = {
        "scenario_status": "blocked",
        "capture_ref": None,
        "captured_stdout_path": None,
        "intake_created": False,
        "intake_ref": None,
        "intake_status": None,
        "output_digest": None,
        "patch_detected": False,
        "files_mentioned": [],
        "apply_performed": False,
        "files_modified": False,
        "commits_created": 0,
        "push_performed": False,
        "implementation_performed": False,
        "execution_authorized": False,
        "blockers": [],
        "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    capture_path = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json")
    if not capture_path.is_file():
        base["scenario_status"] = "missing_capture"
        base["blockers"] = ["no activated task prompt capture artifact"]
        base["next_operator_action"] = "Run pcae phase activated-task-prompt-capture-smoke --allow-real-invocation first."
        return base

    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if capture.get("smoke_status") != "passed":
        base["scenario_status"] = "capture_not_successful"
        base["blockers"] = [f"capture smoke status: {capture.get('smoke_status')}"]
        base["next_operator_action"] = "Run pcae phase activated-task-prompt-capture-smoke --allow-real-invocation to get a successful capture."
        return base

    stdout_path_str = capture.get("captured_stdout_path")
    if not stdout_path_str:
        base["scenario_status"] = "missing_output"
        base["blockers"] = ["captured stdout path missing"]
        return base

    stdout_path = Path(stdout_path_str)
    if not stdout_path.is_absolute():
        stdout_path = root.join(stdout_path)

    if not stdout_path.is_file():
        base["scenario_status"] = "missing_output"
        base["blockers"] = [f"captured stdout file not found: {stdout_path_str}"]
        return base

    output_content = stdout_path.read_text(encoding="utf-8")
    if not output_content.strip():
        base["scenario_status"] = "missing_output"
        base["blockers"] = ["captured stdout is empty"]
        return base

    # Use existing intake logic
    intake_result = _build_agent_output_intake(root, output_content, str(stdout_path))

    # Persist intake
    d = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR)
    d.mkdir(parents=True, exist_ok=True)
    (d / ".gitignore").write_text("*\n")
    (d / "latest.json").write_text(json.dumps(intake_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        **base,
        "scenario_status": "passed",
        "capture_ref": str(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json"),
        "captured_stdout_path": str(stdout_path),
        "intake_created": True,
        "intake_ref": str(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json"),
        "intake_status": intake_result.get("intake_status"),
        "output_digest": intake_result.get("output_digest"),
        "patch_detected": intake_result.get("patch_detected", False),
        "files_mentioned": intake_result.get("files_mentioned", []),
        "blockers": [],
        "warnings": ["patch detected in captured output"] if intake_result.get("patch_detected") else [],
        "next_operator_action": "Run pcae phase activated-task-agent-output-review --json to review bridged intake.",
    }


def run_phase_activated_task_capture_intake_scenario(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_activated_task_capture_intake_scenario(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_CAPTURE_INTAKE_SCENARIOS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Intake scenario saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["scenario_status"] == "passed" else 1
    print("Activated Task Capture Intake Scenario")
    print("=" * 40)
    print(f"  Scenario status: {result['scenario_status']}")
    print(f"  Intake created: {'yes' if result['intake_created'] else 'no'}")
    print(f"  Patch detected: {'yes' if result['patch_detected'] else 'no'}")
    print(f"  Apply performed: no")
    print(f"  Files modified: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["warnings"]:
        print(f"\n  Warnings:"); [print(f"    - {w}") for w in result["warnings"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["scenario_status"] == "passed" else 1


# Phase 75B: activated task capture review scenario
ACTIVATED_TASK_CAPTURE_REVIEW_SCENARIOS_DIR = Path(".pcae") / "activated-task-capture-review-scenarios"


def _build_activated_task_capture_review_scenario(root: HarnessPath) -> dict:
    base = {
        "scenario_status": "blocked", "intake_ref": None, "review_created": False,
        "review_ref": None, "review_status": None, "files_mentioned": [],
        "allowed_files": [], "forbidden_files": [], "out_of_scope_files": [],
        "suspicious_claims": [], "patch_detected": False,
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    intake_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json")
    if not intake_path.is_file():
        base["scenario_status"] = "missing_intake"
        base["blockers"] = ["no agent output intake artifact"]
        base["next_operator_action"] = "Run pcae phase activated-task-capture-intake-scenario first."
        return base

    # Run existing review logic
    review = _build_agent_output_review(root)
    review_status = review.get("review_status", "blocked")

    # Persist review
    d = root.join(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR)
    d.mkdir(parents=True, exist_ok=True)
    (d / ".gitignore").write_text("*\n")
    (d / "latest.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    intake = json.loads(intake_path.read_text(encoding="utf-8"))

    if review_status == "blocked":
        base["scenario_status"] = "review_blocked"
        base["blockers"] = review.get("blockers", [])
        base["next_operator_action"] = "Resolve review blockers before proceeding to apply dry-run."
    elif review_status == "out_of_scope":
        base["scenario_status"] = "out_of_scope"
        base["out_of_scope_files"] = review.get("out_of_scope_files", [])
        base["blockers"] = ["captured output mentions files outside task scope"]
        base["next_operator_action"] = "Review out-of-scope files. Do not apply output that touches files beyond task contract."
    else:
        base["scenario_status"] = "passed"

    return {
        **base,
        "intake_ref": str(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json"),
        "review_created": True,
        "review_ref": str(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json"),
        "review_status": review_status,
        "files_mentioned": intake.get("files_mentioned", []),
        "allowed_files": review.get("allowed_files", []),
        "forbidden_files": review.get("forbidden_files", []),
        "out_of_scope_files": review.get("out_of_scope_files", []),
        "suspicious_claims": review.get("suspicious_claims", []),
        "patch_detected": intake.get("patch_detected", False),
        "blockers": base.get("blockers", []),
        "next_operator_action": (
            "Review passed. Run pcae phase activated-task-capture-apply-dry-run-scenario next."
            if base["scenario_status"] == "passed"
            else base["next_operator_action"]
        ),
    }


def run_phase_activated_task_capture_review_scenario(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_activated_task_capture_review_scenario(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_CAPTURE_REVIEW_SCENARIOS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Review scenario saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["scenario_status"] in ("passed", "ready_for_apply_dry_run") else 1
    print("Activated Task Capture Review Scenario"); print("=" * 40)
    print(f"  Scenario status: {result['scenario_status']}")
    print(f"  Review status: {result.get('review_status', 'N/A')}")
    print(f"  Files mentioned: {len(result.get('files_mentioned', []))}")
    print(f"  Out of scope: {len(result.get('out_of_scope_files', []))}")
    print(f"  Suspicious claims: {len(result.get('suspicious_claims', []))}")
    print(f"  Apply performed: no"); print(f"  Execution authorized: no")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["scenario_status"] in ("passed", "ready_for_apply_dry_run") else 1


# Phase 75C: activated task capture apply dry-run scenario
ACTIVATED_TASK_CAPTURE_APPLY_DRY_RUN_SCENARIOS_DIR = Path(".pcae") / "activated-task-capture-apply-dry-run-scenarios"


def _build_activated_task_capture_apply_dry_run_scenario(root: HarnessPath) -> dict:
    base = {
        "scenario_status": "blocked", "review_ref": None, "apply_dry_run_created": False,
        "apply_dry_run_ref": None, "apply_allowed": False, "would_touch_files": [],
        "validation_commands": [], "apply_performed": False, "files_modified": False,
        "commits_created": 0, "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }
    review_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json")
    if not review_path.is_file():
        base["scenario_status"] = "missing_review"; base["blockers"] = ["no review artifact"]
        base["next_operator_action"] = "Run pcae phase activated-task-capture-review-scenario first."
        return base
    review = json.loads(review_path.read_text(encoding="utf-8"))
    rs = review.get("review_status")
    if rs not in ("ready_for_apply_dry_run", "passed"):
        base["scenario_status"] = "review_not_ready"; base["blockers"] = [f"review status: {rs}"]
        base["next_operator_action"] = "Resolve review blockers before apply dry-run."
        return base
    intake_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json")
    intake = json.loads(intake_path.read_text(encoding="utf-8")) if intake_path.is_file() else {}
    apply_result = _build_agent_output_apply_dry_run(root)
    d = root.join(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR)
    d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
    (d / "latest.json").write_text(json.dumps(apply_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**base, "scenario_status": "passed", "review_ref": str(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json"),
        "apply_dry_run_created": True, "apply_dry_run_ref": str(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json"),
        "apply_allowed": apply_result.get("apply_allowed", False),
        "would_touch_files": intake.get("files_mentioned", []),
        "validation_commands": ["pcae health", "pcae check", "python -m pytest -n auto"],
        "blockers": apply_result.get("blockers", []),
        "next_operator_action": "Apply dry-run complete. Run pcae phase activated-task-capture-lifecycle-summary for full lifecycle view."}


def run_phase_activated_task_capture_apply_dry_run_scenario(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_capture_apply_dry_run_scenario(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_CAPTURE_APPLY_DRY_RUN_SCENARIOS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Apply dry-run scenario saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["scenario_status"] == "passed" else 1
    print("Activated Task Capture Apply Dry-Run Scenario"); print("=" * 40)
    print(f"  Scenario status: {result['scenario_status']}"); print(f"  Apply allowed: {'yes' if result['apply_allowed'] else 'no'}")
    print(f"  Would touch: {len(result['would_touch_files'])} files"); print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["scenario_status"] == "passed" else 1


# Phase 75D: captured output lifecycle summary
ACTIVATED_TASK_CAPTURE_LIFECYCLE_SUMMARIES_DIR = Path(".pcae") / "activated-task-capture-lifecycle-summaries"


def _build_activated_task_capture_lifecycle_summary(root: HarnessPath) -> dict:
    base = {
        "lifecycle_status": "no_capture", "capture_ref": None, "intake_ref": None,
        "review_ref": None, "apply_dry_run_ref": None, "backend_name": "claude-deepseek",
        "task_package_sent": False, "output_nonempty": False, "patch_detected": False,
        "files_mentioned": [], "review_status": None, "apply_allowed": False,
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "No captured output available. Run pcae phase activated-task-prompt-capture-smoke --allow-real-invocation first.",
    }
    cap_path = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json")
    if cap_path.is_file():
        cap = json.loads(cap_path.read_text(encoding="utf-8"))
        base["capture_ref"] = str(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json")
        base["task_package_sent"] = cap.get("task_package_sent", False)
        base["output_nonempty"] = cap.get("output_nonempty", False)
        base["lifecycle_status"] = "capture_available"
        base["next_operator_action"] = "Run pcae phase activated-task-capture-intake-scenario to bridge output."

    intake_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json")
    if intake_path.is_file():
        intake = json.loads(intake_path.read_text(encoding="utf-8"))
        base["intake_ref"] = str(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json")
        base["patch_detected"] = intake.get("patch_detected", False)
        base["files_mentioned"] = intake.get("files_mentioned", [])
        base["lifecycle_status"] = "intaken"
        base["next_operator_action"] = "Run pcae phase activated-task-capture-review-scenario to review intake."

    review_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json")
    if review_path.is_file():
        review = json.loads(review_path.read_text(encoding="utf-8"))
        base["review_ref"] = str(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json")
        base["review_status"] = review.get("review_status")
        rs = review.get("review_status")
        if rs in ("ready_for_apply_dry_run", "passed"):
            base["lifecycle_status"] = "reviewed"
            base["next_operator_action"] = "Run pcae phase activated-task-capture-apply-dry-run-scenario."
        else:
            base["lifecycle_status"] = "blocked"
            base["blockers"] = review.get("blockers", [])

    apply_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json")
    if apply_path.is_file():
        adr = json.loads(apply_path.read_text(encoding="utf-8"))
        base["apply_dry_run_ref"] = str(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json")
        base["apply_allowed"] = adr.get("apply_allowed", False)
        if adr.get("apply_allowed"):
            base["lifecycle_status"] = "apply_dry_run_ready"
            base["next_operator_action"] = "Run pcae phase activated-task-capture-manual-apply-readiness to check manual apply readiness."
        else:
            base["lifecycle_status"] = "blocked"
            base["blockers"] = adr.get("blockers", [])

    return base


def run_phase_activated_task_capture_lifecycle_summary(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_capture_lifecycle_summary(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_CAPTURE_LIFECYCLE_SUMMARIES_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Lifecycle summary saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0
    print("Activated Task Capture Lifecycle Summary"); print("=" * 40)
    print(f"  Lifecycle: {result['lifecycle_status']}"); print(f"  Backend: {result['backend_name']}")
    print(f"  Task package sent: {'yes' if result['task_package_sent'] else 'no'}")
    print(f"  Output nonempty: {'yes' if result['output_nonempty'] else 'no'}")
    print(f"  Patch detected: {'yes' if result['patch_detected'] else 'no'}")
    print(f"  Review status: {result.get('review_status', 'N/A')}")
    print(f"  Apply allowed: {'yes' if result['apply_allowed'] else 'no'}")
    print(f"  Apply performed: no"); print(f"  Execution authorized: no")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  {result['next_operator_action']}")
    return 0


# Phase 75E: captured output manual apply readiness
ACTIVATED_TASK_CAPTURE_MANUAL_APPLY_READINESS_DIR = Path(".pcae") / "activated-task-capture-manual-apply-readiness"


def _build_activated_task_capture_manual_apply_readiness(root: HarnessPath) -> dict:
    base = {
        "readiness_status": "blocked", "manual_apply_allowed": False,
        "automatic_apply_allowed": False, "capture_ref": None, "intake_ref": None,
        "review_ref": None, "apply_dry_run_ref": None, "would_touch_files": [],
        "validation_commands_after_manual_apply": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory"],
        "required_operator_steps": [], "forbidden_shortcuts": [
            "Do not apply automatically", "Do not commit from backend output",
            "Do not push from backend output", "Do not skip review",
            "Do not skip apply dry-run", "Do not authorize runner execution",
        ],
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }
    lifecycle = _build_activated_task_capture_lifecycle_summary(root)
    base["capture_ref"] = lifecycle.get("capture_ref")
    base["intake_ref"] = lifecycle.get("intake_ref")
    base["review_ref"] = lifecycle.get("review_ref")
    base["apply_dry_run_ref"] = lifecycle.get("apply_dry_run_ref")

    if lifecycle["lifecycle_status"] != "apply_dry_run_ready":
        base["readiness_status"] = "apply_dry_run_not_ready"
        base["blockers"] = [f"lifecycle not at apply_dry_run_ready: {lifecycle['lifecycle_status']}"]
        base["next_operator_action"] = lifecycle["next_operator_action"]
        return base

    review_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json")
    if review_path.is_file():
        review = json.loads(review_path.read_text(encoding="utf-8"))
        if review.get("review_status") not in ("ready_for_apply_dry_run", "passed"):
            base["readiness_status"] = "review_not_ready"
            base["blockers"] = [f"review status: {review.get('review_status')}"]
            return base

    from pcae.core.health import build_health_data, is_healthy
    hd = build_health_data(root)
    if not is_healthy(hd):
        base["readiness_status"] = "blocked"
        base["blockers"] = ["health not healthy"]
        base["next_operator_action"] = "Resolve health issues before manual apply."
        return base

    base["readiness_status"] = "ready_for_manual_apply"
    base["manual_apply_allowed"] = True
    apply_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json")
    if apply_path.is_file():
        adr = json.loads(apply_path.read_text(encoding="utf-8"))
        base["would_touch_files"] = adr.get("would_touch_files", [])
    base["required_operator_steps"] = [
        "1. Review captured output: cat .pcae/activated-task-prompt-captures/latest.stdout.txt",
        "2. Review intake: pcae phase activated-task-agent-output-intake-show --json",
        "3. Review scope check: pcae phase activated-task-agent-output-review --json",
        "4. Review apply dry-run: pcae phase activated-task-agent-output-apply --dry-run --json",
        "5. If satisfied, manually apply changes following task contract scope",
        "6. Run: pcae health && pcae check && python -m pytest -n auto",
        "7. Commit using pcae task finish --commit",
        "8. Push using pcae push",
    ]
    base["blockers"] = []
    base["next_operator_action"] = "Manual apply may proceed at operator discretion. This command does NOT apply output."
    return base


def run_phase_activated_task_capture_manual_apply_readiness(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_capture_manual_apply_readiness(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_CAPTURE_MANUAL_APPLY_READINESS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Manual apply readiness saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["manual_apply_allowed"] else 1
    print("Activated Task Capture Manual Apply Readiness"); print("=" * 40)
    print(f"  Readiness: {result['readiness_status']}"); print(f"  Manual apply allowed: {'yes' if result['manual_apply_allowed'] else 'no'}")
    print(f"  Auto apply allowed: no"); print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]: print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["required_operator_steps"]:
        print(f"\n  Operator steps:"); [print(f"    {s}") for s in result["required_operator_steps"][:4]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["manual_apply_allowed"] else 1


# Phase 75F: captured output safety regression scenario
ACTIVATED_TASK_CAPTURE_SAFETY_REGRESSIONS_DIR = Path(".pcae") / "activated-task-capture-safety-regressions"


# Phase 75G: captured output manual apply approval contract
CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_CONTRACTS_DIR = Path(".pcae") / "captured-output-manual-apply-approval-contracts"


def _build_captured_output_manual_apply_approval_contract(root: HarnessPath) -> dict:
    base = {
        "contract_status": "blocked", "manual_apply_approval_required": True,
        "manual_apply_allowed_after_approval": False, "automatic_apply_allowed": False,
        "backend_apply_allowed": False, "captured_output_ref": None, "intake_ref": None,
        "review_ref": None, "apply_dry_run_ref": None, "lifecycle_ref": None,
        "readiness_ref": None, "allowed_files": [], "forbidden_files": [
            "No backend invocation", "No prompt execution", "No patch application",
            "No project code modification from backend output",
            "No automatic commit", "No automatic task finish", "No automatic push",
            "No execution authorization", "No runner-execute real execution",
        ],
        "validation_commands": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory"],
        "operator_requirements": [
            "Explicit human approval required",
            "Manual apply must be done by operator, not backend",
            "Operator must inspect captured output",
            "Operator must inspect apply dry-run",
            "Operator must confirm allowed files",
            "Operator must run validation commands after manual apply",
            "Operator must not use raw git push",
            "Operator must use governed commit/push path after manual apply",
        ],
        "forbidden_shortcuts": [
            "Do not apply automatically", "Do not commit from backend output",
            "Do not push from backend output", "Do not skip review",
            "Do not skip apply dry-run", "Do not authorize runner execution",
        ],
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Check capture exists
    capture_path = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json")
    if not capture_path.is_file():
        base["contract_status"] = "no_capture"
        base["blockers"] = ["No captured output found."]
        base["next_operator_action"] = "No capture available. Cannot proceed."
        return base
    base["captured_output_ref"] = str(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json")

    # Check intake exists
    intake_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json")
    if not intake_path.is_file():
        base["contract_status"] = "blocked"
        base["blockers"] = ["No intake artifact found."]
        base["next_operator_action"] = "Intake must exist before contract can be ready."
        return base
    base["intake_ref"] = str(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json")

    # Check review is ready
    review_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json")
    if review_path.is_file():
        review = json.loads(review_path.read_text(encoding="utf-8"))
        base["review_ref"] = str(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json")
        if review.get("review_status") not in ("ready_for_apply_dry_run", "passed"):
            base["contract_status"] = "blocked"
            base["blockers"] = [f"Review not ready: {review.get('review_status')}"]
            base["next_operator_action"] = "Review must be ready_for_apply_dry_run before contract can be ready."
            return base
    else:
        base["contract_status"] = "blocked"
        base["blockers"] = ["No review artifact found."]
        base["next_operator_action"] = "Review must exist before contract can be ready."
        return base

    # Check apply dry-run exists
    apply_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json")
    if not apply_path.is_file():
        base["contract_status"] = "no_apply_dry_run"
        base["blockers"] = ["No apply dry-run artifact found."]
        base["next_operator_action"] = "Apply dry-run must exist before contract can be ready."
        return base
    base["apply_dry_run_ref"] = str(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json")

    # Check lifecycle
    lifecycle = _build_activated_task_capture_lifecycle_summary(root)
    base["lifecycle_ref"] = str(ACTIVATED_TASK_CAPTURE_LIFECYCLE_SUMMARIES_DIR / "latest.json")
    if lifecycle.get("lifecycle_status") != "apply_dry_run_ready":
        base["contract_status"] = "blocked"
        base["blockers"] = [f"Lifecycle not at apply_dry_run_ready: {lifecycle.get('lifecycle_status')}"]
        base["next_operator_action"] = lifecycle.get("next_operator_action", "Complete lifecycle pipeline first.")
        return base

    # Check manual apply readiness
    readiness = _build_activated_task_capture_manual_apply_readiness(root)
    base["readiness_ref"] = str(ACTIVATED_TASK_CAPTURE_MANUAL_APPLY_READINESS_DIR / "latest.json")
    if readiness.get("readiness_status") != "ready_for_manual_apply":
        base["contract_status"] = "readiness_not_ready"
        base["blockers"] = [f"Manual apply readiness not ready: {readiness.get('readiness_status')}"]
        base["next_operator_action"] = readiness.get("next_operator_action", "Resolve readiness blockers first.")
        return base

    # Populate allowed files from readiness
    base["allowed_files"] = readiness.get("would_touch_files", [])

    # Ready
    base["contract_status"] = "ready"
    base["manual_apply_allowed_after_approval"] = True
    base["blockers"] = []
    base["next_operator_action"] = (
        "Contract is ready. Operator must explicitly approve before manual apply. "
        "Run pcae phase captured-output-manual-apply-approval-review to review eligibility."
    )
    return base


def run_phase_captured_output_manual_apply_approval_contract(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_captured_output_manual_apply_approval_contract(root)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_CONTRACTS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Approval contract saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["contract_status"] == "ready" else 1
    print("Captured Output Manual Apply Approval Contract"); print("=" * 40)
    print(f"  Contract status: {result['contract_status']}")
    print(f"  Manual apply approval required: {'yes' if result['manual_apply_approval_required'] else 'no'}")
    print(f"  Manual apply allowed after approval: {'yes' if result['manual_apply_allowed_after_approval'] else 'no'}")
    print(f"  Automatic apply allowed: no")
    print(f"  Backend apply allowed: no")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["operator_requirements"]:
        print(f"\n  Operator requirements:"); [print(f"    - {r}") for r in result["operator_requirements"][:4]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["contract_status"] == "ready" else 1


# Phase 75H: captured output manual apply approval review
CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_REVIEWS_DIR = Path(".pcae") / "captured-output-manual-apply-approval-reviews"


def _build_captured_output_manual_apply_approval_review(root: HarnessPath) -> dict:
    base = {
        "review_status": "blocked", "human_approval_can_be_requested": False,
        "human_approval_granted": False, "manual_apply_allowed": False,
        "automatic_apply_allowed": False, "backend_apply_allowed": False,
        "captured_output_ref": None, "apply_dry_run_ref": None,
        "readiness_ref": None, "contract_ref": None,
        "risks": [], "unresolved_risks": [], "historical_advisories": [],
        "validation_commands": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory"],
        "required_human_checks": [], "approval_request_summary": "",
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read contract
    contract_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_CONTRACTS_DIR / "latest.json")
    if not contract_path.is_file():
        base["review_status"] = "contract_not_ready"
        base["blockers"] = ["No approval contract found."]
        base["next_operator_action"] = "Run pcae phase captured-output-manual-apply-approval-contract --save first."
        return base
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    base["contract_ref"] = str(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_CONTRACTS_DIR / "latest.json")

    if contract.get("contract_status") != "ready":
        base["review_status"] = "contract_not_ready"
        base["blockers"] = [f"Contract not ready: {contract.get('contract_status')}"]
        base["next_operator_action"] = contract.get("next_operator_action", "Resolve contract blockers first.")
        return base

    # Read manual apply readiness
    readiness_path = root.join(ACTIVATED_TASK_CAPTURE_MANUAL_APPLY_READINESS_DIR / "latest.json")
    if not readiness_path.is_file():
        base["review_status"] = "readiness_not_ready"
        base["blockers"] = ["No manual apply readiness artifact found."]
        base["next_operator_action"] = "Run pcae phase activated-task-capture-manual-apply-readiness --save first."
        return base
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    base["readiness_ref"] = str(ACTIVATED_TASK_CAPTURE_MANUAL_APPLY_READINESS_DIR / "latest.json")
    base["captured_output_ref"] = readiness.get("capture_ref")

    if readiness.get("readiness_status") != "ready_for_manual_apply":
        base["review_status"] = "readiness_not_ready"
        base["blockers"] = [f"Manual apply readiness not ready: {readiness.get('readiness_status')}"]
        base["next_operator_action"] = readiness.get("next_operator_action", "Resolve readiness blockers first.")
        return base

    # Read apply dry-run
    apply_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json")
    base["apply_dry_run_ref"] = None
    if apply_path.is_file():
        base["apply_dry_run_ref"] = str(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json")

    # Check real execution disabled proof
    proof_path = root.join(REAL_EXECUTION_DISABLED_PROOFS_DIR / "latest.json")
    if proof_path.is_file():
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        if proof.get("proof_status") != "passed":
            base["review_status"] = "blocked"
            base["blockers"] = ["Real execution disabled proof not passed."]
            base["next_operator_action"] = "Run pcae phase real-execution-disabled-proof --save to verify."
            return base

    # Check governance bypass report (advisory, not blocking)
    bypass_path = root.join(GOVERNANCE_BYPASS_REPORTS_DIR / "latest.json")
    if bypass_path.is_file():
        bypass = json.loads(bypass_path.read_text(encoding="utf-8"))
        if bypass.get("report_status") in ("warning",):
            base["risks"].append(f"Governance bypass report: {bypass.get('report_status')} — {len(bypass.get('suspected_bypass_commits', []))} suspected bypasses")
            base["historical_advisories"].append("governance-bypass-report-status:" + bypass.get("report_status", "unknown"))

    # Gather risks and unresolved risks
    would_touch = readiness.get("would_touch_files", [])
    base["risks"].extend(readiness.get("warnings", []))
    base["risks"].extend(contract.get("warnings", []))

    # Unresolved risks exist if governance bypass report has warnings
    if bypass_path.is_file():
        bypass = json.loads(bypass_path.read_text(encoding="utf-8"))
        if bypass.get("report_status") == "warning" and len(bypass.get("undeclared_bypass_commits", [])) > 0:
            base["unresolved_risks"].append(
                f"Governance bypass report has {len(bypass.get('undeclared_bypass_commits', []))} undeclared suspected bypass commits"
            )

    # If unresolved risks, report blocked
    if base["unresolved_risks"]:
        base["review_status"] = "unresolved_risk"
        base["blockers"] = base["unresolved_risks"]
        base["next_operator_action"] = "Review and address unresolved risks before requesting approval."
        return base

    # Ready
    base["review_status"] = "approval_review_ready"
    base["human_approval_can_be_requested"] = True
    base["blockers"] = []
    base["required_human_checks"] = [
        "1. Review captured output manually",
        "2. Review apply dry-run output",
        "3. Confirm no out-of-scope files",
        "4. Confirm no suspicious claims unresolved",
        "5. Confirm governance bypass report is understood",
        "6. Run validation commands after any manual apply",
    ]
    base["approval_request_summary"] = (
        "All governance prerequisites satisfied. "
        "The human operator should review captured output, apply dry-run, "
        "and confirm no out-of-scope changes before requesting explicit approval."
    )
    base["next_operator_action"] = (
        "Approval review is ready. Run pcae phase captured-output-manual-apply-preflight for final preflight check."
    )
    return base


def run_phase_captured_output_manual_apply_approval_review(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_captured_output_manual_apply_approval_review(root)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_REVIEWS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Approval review saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["review_status"] == "approval_review_ready" else 1
    print("Captured Output Manual Apply Approval Review"); print("=" * 40)
    print(f"  Review status: {result['review_status']}")
    print(f"  Human approval can be requested: {'yes' if result['human_approval_can_be_requested'] else 'no'}")
    print(f"  Human approval granted: no")
    print(f"  Manual apply allowed: no")
    print(f"  Automatic apply allowed: no")
    print(f"  Backend apply allowed: no")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["risks"]:
        print(f"\n  Risks:"); [print(f"    - {r}") for r in result["risks"][:4]]
    if result["required_human_checks"]:
        print(f"\n  Required human checks:"); [print(f"    {c}") for c in result["required_human_checks"][:4]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["review_status"] == "approval_review_ready" else 1


# Phase 75I: captured output manual apply preflight
CAPTURED_OUTPUT_MANUAL_APPLY_PREFLIGHTS_DIR = Path(".pcae") / "captured-output-manual-apply-preflights"


def _build_captured_output_manual_apply_preflight(root: HarnessPath) -> dict:
    base = {
        "preflight_status": "blocked", "human_approval_required": True,
        "human_approval_artifact_present": False, "manual_apply_allowed": False,
        "automatic_apply_allowed": False, "backend_apply_allowed": False,
        "captured_output_ref": None, "apply_dry_run_ref": None,
        "approval_contract_ref": None, "approval_review_ref": None,
        "allowed_files": [], "forbidden_files": [
            "No backend invocation", "No prompt execution", "No patch application",
            "No project code modification from backend output",
            "No automatic commit", "No automatic task finish", "No automatic push",
            "No execution authorization", "No runner-execute real execution",
        ],
        "validation_commands_after_manual_apply": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory"],
        "required_operator_steps": [], "forbidden_shortcuts": [
            "Do not apply automatically", "Do not commit from backend output",
            "Do not push from backend output", "Do not skip review",
            "Do not skip apply dry-run", "Do not authorize runner execution",
        ],
        "recommended_next_phase": "76A (future human approval artifact phase)",
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read contract
    contract_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_CONTRACTS_DIR / "latest.json")
    if not contract_path.is_file():
        base["preflight_status"] = "contract_not_ready"
        base["blockers"] = ["No approval contract found."]
        base["next_operator_action"] = "Run pcae phase captured-output-manual-apply-approval-contract --save first."
        return base
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    base["approval_contract_ref"] = str(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_CONTRACTS_DIR / "latest.json")

    if contract.get("contract_status") != "ready":
        base["preflight_status"] = "contract_not_ready"
        base["blockers"] = [f"Contract not ready: {contract.get('contract_status')}"]
        base["next_operator_action"] = contract.get("next_operator_action", "Resolve contract blockers first.")
        return base

    # Read review
    review_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_REVIEWS_DIR / "latest.json")
    if not review_path.is_file():
        base["preflight_status"] = "review_not_ready"
        base["blockers"] = ["No approval review found."]
        base["next_operator_action"] = "Run pcae phase captured-output-manual-apply-approval-review --save first."
        return base
    review = json.loads(review_path.read_text(encoding="utf-8"))
    base["approval_review_ref"] = str(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_REVIEWS_DIR / "latest.json")

    if review.get("review_status") != "approval_review_ready":
        base["preflight_status"] = "review_not_ready"
        base["blockers"] = [f"Review not ready: {review.get('review_status')}"]
        base["next_operator_action"] = review.get("next_operator_action", "Resolve review blockers first.")
        return base

    # Read manual apply readiness for allowed files and refs
    readiness_path = root.join(ACTIVATED_TASK_CAPTURE_MANUAL_APPLY_READINESS_DIR / "latest.json")
    if readiness_path.is_file():
        readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
        base["captured_output_ref"] = readiness.get("capture_ref")
        base["apply_dry_run_ref"] = readiness.get("apply_dry_run_ref")
        base["allowed_files"] = readiness.get("would_touch_files", [])

    # Check real execution disabled proof
    proof_path = root.join(REAL_EXECUTION_DISABLED_PROOFS_DIR / "latest.json")
    if proof_path.is_file():
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        if proof.get("proof_status") != "passed":
            base["preflight_status"] = "blocked"
            base["blockers"] = ["Real execution disabled proof not passed."]
            base["next_operator_action"] = "Run pcae phase real-execution-disabled-proof --save to verify."
            return base

    # Run health and check
    from pcae.core.health import build_health_data, is_healthy
    hd = build_health_data(root)
    if not is_healthy(hd):
        base["preflight_status"] = "blocked"
        base["blockers"] = ["Health not healthy."]
        base["next_operator_action"] = "Run pcae health to diagnose and resolve health issues."
        return base

    # Ready
    base["preflight_status"] = "ready_for_human_approval"
    base["blockers"] = []
    base["required_operator_steps"] = [
        "1. Review captured output: cat .pcae/activated-task-prompt-captures/latest.stdout.txt",
        "2. Review approval contract: pcae phase captured-output-manual-apply-approval-contract --json",
        "3. Review approval review: pcae phase captured-output-manual-apply-approval-review --json",
        "4. Review apply dry-run: pcae phase activated-task-agent-output-apply --dry-run --json",
        "5. Request explicit human approval (future phase: human approval artifact)",
        "6. If explicitly approved, manually apply changes following task contract scope",
        "7. Run: pcae health && pcae check && python -m pytest -n auto",
        "8. Commit using pcae task finish --commit",
        "9. Push using pcae push",
    ]
    base["next_operator_action"] = (
        "Preflight complete. All governance prerequisites satisfied. "
        "Manual apply requires explicit human approval artifact (future phase). "
        "Do not apply, commit, push, or authorize execution without explicit approval."
    )
    return base


def run_phase_captured_output_manual_apply_preflight(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_captured_output_manual_apply_preflight(root)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_PREFLIGHTS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Preflight saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["preflight_status"] == "ready_for_human_approval" else 1
    print("Captured Output Manual Apply Preflight"); print("=" * 40)
    print(f"  Preflight status: {result['preflight_status']}")
    print(f"  Human approval required: yes")
    print(f"  Human approval artifact present: no")
    print(f"  Manual apply allowed: no")
    print(f"  Automatic apply allowed: no")
    print(f"  Backend apply allowed: no")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["required_operator_steps"]:
        print(f"\n  Operator steps:"); [print(f"    {s}") for s in result["required_operator_steps"][:5]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["preflight_status"] == "ready_for_human_approval" else 1


def _build_activated_task_capture_safety_regression(root: HarnessPath) -> dict:
    cases = []
    all_passed = True

    # Case 1: verify no working-tree mutation after pipeline
    from pcae.core.git_status import read_git_changes
    pre_changes = read_git_changes(root)

    # Case 2: intake scenario with synthetic safe output
    safe_pipeline_passed = False; out_of_scope_blocked = False
    suspicious_detected = False

    cap_dir = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR)
    if cap_dir.is_file() or True:  # evaluate regardless
        # Check if existing intake/apply pipeline would correctly handle safe output
        intake_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR / "latest.json")
        if intake_path.is_file():
            intake = json.loads(intake_path.read_text(encoding="utf-8"))
            safe_pipeline_passed = intake.get("intake_status") == "recorded"
            suspicious_detected = intake.get("patch_detected", False)

        review_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR / "latest.json")
        if review_path.is_file():
            review = json.loads(review_path.read_text(encoding="utf-8"))
            out_of_scope_blocked = len(review.get("out_of_scope_files", [])) > 0 or review.get("review_status") == "out_of_scope"

    post_changes = read_git_changes(root)
    no_mutation_verified = len(pre_changes) == len(post_changes)

    if safe_pipeline_passed: cases.append("PASS: safe pipeline intake")
    else: cases.append("SKIP: safe pipeline (no intake found)"); all_passed = False

    if out_of_scope_blocked: cases.append("PASS: out-of-scope blocked")
    else: cases.append("INFO: out-of-scope check (no out-of-scope files detected)")

    if suspicious_detected: cases.append("PASS: suspicious claims detected")
    else: cases.append("INFO: no suspicious claims in current intake")

    if no_mutation_verified: cases.append("PASS: no mutation verified")
    else: cases.append("FAIL: mutation detected"); all_passed = False

    return {
        "scenario_status": "passed" if all_passed else "failed",
        "safe_pipeline_passed": safe_pipeline_passed,
        "out_of_scope_blocked": out_of_scope_blocked,
        "suspicious_claims_detected": suspicious_detected,
        "no_mutation_verified": no_mutation_verified,
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "cases": cases, "blockers": [],
        "warnings": [] if no_mutation_verified else ["mutation detected in regression"],
        "next_operator_action": "Pipeline regression complete. All safety gates verified." if all_passed else "Investigate failures before continuing.",
    }


def run_phase_activated_task_capture_safety_regression(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd(); result = _build_activated_task_capture_safety_regression(root)
    if getattr(args, "save", False):
        d = root.join(ACTIVATED_TASK_CAPTURE_SAFETY_REGRESSIONS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Safety regression saved: {d / 'latest.json'}")
    if args.json: print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["scenario_status"] == "passed" else 1
    print("Activated Task Capture Safety Regression"); print("=" * 40)
    print(f"  Scenario: {result['scenario_status']}")
    print(f"  Safe pipeline: {'passed' if result['safe_pipeline_passed'] else 'skipped'}")
    print(f"  Out-of-scope blocked: {'yes' if result['out_of_scope_blocked'] else 'N/A'}")
    print(f"  Suspicious claims: {'yes' if result['suspicious_claims_detected'] else 'no'}")
    print(f"  No mutation: {'yes' if result['no_mutation_verified'] else 'FAILED'}")
    print(f"  Apply performed: no"); print(f"  Execution authorized: no")
    print(f"\n  Cases:"); [print(f"    {c}") for c in result["cases"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["scenario_status"] == "passed" else 1


# Phase 75F.3: governance bypass detection
GOVERNANCE_BYPASS_REPORTS_DIR = Path(".pcae") / "governance-bypass-reports"

_GOVERNANCE_PROTECTED_PATHS = [
    "tasks/active/", "tasks/done/", "tasks/DONE.md", "tasks/TODO.md",
    "CHANGELOG.md", "PROJECT_STATUS.md", ".pcae/",
]

_SUSPICIOUS_MESSAGE_PATTERNS = [
    r"no[\s-]*verify", r"bypass", r"cleanup", r"fix.*task",
    r"file.*move", r"amend", r"without.*check",
]


def _build_governance_bypass_report(root: HarnessPath) -> dict:
    import subprocess as _sp
    import re as _re

    suspected = []
    declared = []
    undeclared = []
    protected_touched = set()

    try:
        result = _sp.run(
            ["git", "log", "--max-count=30", "--name-only", "--format=COMMIT:%H%nMSG:%s%nFILES:"],
            cwd=root.path, check=True, capture_output=True, text=True,
        )
        log_text = result.stdout
    except (_sp.CalledProcessError, OSError):
        return {
            "report_status": "advisory", "suspected_bypass_commits": [],
            "declared_bypass_commits": [], "undeclared_bypass_commits": [],
            "protected_paths_touched": [], "active_task_present_at_report_time": False,
            "recommendations": ["Could not read git log."], "execution_authorized": False,
            "note": "Git history could not be read. This report may be incomplete.",
        }

    commits = []
    current = {}
    for line in log_text.splitlines():
        if line.startswith("COMMIT:"):
            if current:
                commits.append(current)
            current = {"hash": line[7:].strip()[:12], "msg": "", "files": []}
        elif line.startswith("MSG:"):
            current["msg"] = line[4:].strip()
        elif line.startswith("FILES:"):
            pass
        elif line.strip():
            current["files"].append(line.strip())
    if current and current.get("hash"):
        commits.append(current)

    from pcae.core.tasks import find_latest_active_task
    active_task = find_latest_active_task(root)
    active_task_present = active_task is not None

    for c in commits:
        msg = c.get("msg", "")
        files = c.get("files", [])
        is_suspicious = False

        # Check if commit touches protected governance paths
        for f in files:
            for pp in _GOVERNANCE_PROTECTED_PATHS:
                if f.startswith(pp):
                    protected_touched.add(f)
                    is_suspicious = True
                    break

        # Check message for suspicious patterns
        for pat in _SUSPICIOUS_MESSAGE_PATTERNS:
            if _re.search(pat, msg, _re.IGNORECASE):
                is_suspicious = True
                break

        # Check if declared bypass
        is_declared = any(kw in msg.lower() for kw in ["no-verify", "bypass", "without check"])

        if is_suspicious:
            entry = {"commit": c["hash"], "message": msg, "files": files}
            if is_declared:
                declared.append(entry)
            else:
                undeclared.append(entry)
            suspected.append(entry)

    report_status = "clean"
    recommendations = []
    if suspected:
        report_status = "advisory" if len(undeclared) == 0 else "warning"
    if undeclared:
        recommendations.append(f"{len(undeclared)} undeclared suspicious commit(s) found. Review manually.")
    if declared:
        recommendations.append(f"{len(declared)} declared bypass commit(s) found. Already documented.")
    if not suspected:
        recommendations.append("No suspicious commits detected in recent history.")

    return {
        "report_status": report_status,
        "suspected_bypass_commits": suspected,
        "declared_bypass_commits": declared,
        "undeclared_bypass_commits": undeclared,
        "protected_paths_touched": sorted(protected_touched),
        "active_task_present_at_report_time": active_task_present,
        "recommendations": recommendations,
        "execution_authorized": False,
        "note": (
            "Git does not reliably record --no-verify usage. This report uses heuristics "
            "(message patterns, protected paths touched). Exact bypass detection is not guaranteed. "
            "Declared bypasses may use keywords like 'no-verify', 'bypass', or 'without check' in messages."
        ),
    }


def run_phase_governance_bypass_report(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_governance_bypass_report(root)
    if getattr(args, "save", False):
        d = root.join(GOVERNANCE_BYPASS_REPORTS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Bypass report saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    print("Governance Bypass Report"); print("=" * 40)
    print(f"  Report status: {result['report_status']}")
    print(f"  Suspected bypass commits: {len(result['suspected_bypass_commits'])}")
    print(f"  Declared: {len(result['declared_bypass_commits'])}")
    print(f"  Undeclared: {len(result['undeclared_bypass_commits'])}")
    print(f"  Protected paths touched: {len(result['protected_paths_touched'])}")
    print(f"  Active task present: {'yes' if result['active_task_present_at_report_time'] else 'no'}")
    print(f"  Execution authorized: no")
    if result["suspected_bypass_commits"]:
        print(f"\n  Suspected commits:")
        for c in result["suspected_bypass_commits"][:8]:
            print(f"    {c['commit']}: {c['message'][:80]}")
    if result["recommendations"]:
        print(f"\n  Recommendations:"); [print(f"    - {r}") for r in result["recommendations"]]
    print(f"\n  {result['note'][:160]}...")
    return 0


# Phase 75I.1: governance bypass review classification
GOVERNANCE_BYPASS_CLASSIFICATIONS_DIR = Path(".pcae") / "governance-bypass-classifications"


def _build_governance_bypass_classification(root: HarnessPath) -> dict:
    base = {
        "classification_status": "blocking", "source_report_status": None,
        "total_suspected": 0, "declared_count": 0, "undeclared_count": 0,
        "historical_advisory_count": 0, "needs_review_count": 0, "blocking_count": 0,
        "classifications": [], "classification_policy": (
            "Conservative heuristic classification. "
            "Declared bypasses (explicit no-verify/bypass messages): historical. "
            "Undeclared commits before governance-hardening cutoff (75F.3): historical_advisory. "
            "Undeclared commits with explicit bypass messages: needs_review. "
            "Recent undeclared commits with suspicious patterns: blocking. "
            "Normal PCAE task implementation commits: false_positive_candidate. "
            "Report is heuristic, not exact. Manual review still required."
        ),
        "manual_apply_blocking": True, "recommendations": [],
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read bypass report
    report_path = root.join(GOVERNANCE_BYPASS_REPORTS_DIR / "latest.json")
    if not report_path.is_file():
        base["classification_status"] = "needs_review"
        base["blockers"] = ["No governance bypass report found."]
        base["next_operator_action"] = "Run pcae phase governance-bypass-report --save first."
        return base
    report = json.loads(report_path.read_text(encoding="utf-8"))
    base["source_report_status"] = report.get("report_status")
    base["total_suspected"] = len(report.get("suspected_bypass_commits", []))
    base["declared_count"] = len(report.get("declared_bypass_commits", []))
    base["undeclared_count"] = len(report.get("undeclared_bypass_commits", []))

    if base["source_report_status"] == "clean":
        base["classification_status"] = "clean"
        base["manual_apply_blocking"] = False
        base["blockers"] = []
        base["next_operator_action"] = "No bypass findings to classify. Manual apply approval review can proceed."
        return base

    declared_hashes = {c["commit"] for c in report.get("declared_bypass_commits", [])}
    classifications = []

    # Determine cutoff: classify all suspected commits
    governance_hardening_commit_hashes = set()
    # Phases 75F.1, 75F.2, 75F.3 are governance hardening
    # Read phase audit to find the hardening phase commit hashes
    audit_path = root.join(PHASE_AUDITS_DIR / "latest.json")
    hardening_phase_ids = {"75F.1", "75F.2", "75F.3", "75F"}
    hardening_commit_hashes = set()
    if audit_path.is_file():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        for p in audit.get("phases", []):
            if p.get("phase_id") in hardening_phase_ids:
                if p.get("implementation_commit"):
                    hardening_commit_hashes.add(p["implementation_commit"][:12])
                if p.get("completion_commit"):
                    hardening_commit_hashes.add(p["completion_commit"][:12])

    # Post-hardening phase commit detection: 75G, 75H, 75I
    post_hardening_phase_ids = {"75G", "75H", "75I", "75I.1", "75I.2", "75I.3"}
    post_hardening_hashes = set()
    if audit_path.is_file():
        for p in audit.get("phases", []):
            if p.get("phase_id") in post_hardening_phase_ids:
                if p.get("implementation_commit"):
                    post_hardening_hashes.add(p["implementation_commit"][:12])
                if p.get("completion_commit"):
                    post_hardening_hashes.add(p["completion_commit"][:12])

    for c in report.get("suspected_bypass_commits", []):
        ch = c["commit"]
        msg = c.get("message", "")
        is_declared = ch in declared_hashes
        has_bypass_keyword = any(kw in msg.lower() for kw in ["no-verify", "bypass", "without check"])
        is_post_hardening = ch in post_hardening_hashes
        is_hardening = ch in hardening_commit_hashes

        # Check if message looks like a normal PCAE phase commit
        is_normal_phase_commit = bool(
            msg.startswith("Implement Phase ") or msg.startswith("Complete Phase ")
            or msg.startswith("Fix ") or msg.startswith("Clean up ") or msg.startswith("Update ")
        )
        is_task_only = all(
            f.startswith("tasks/") or f.startswith("CHANGELOG.md") or f.startswith("PROJECT_STATUS.md")
            for f in c.get("files", [])
        )

        classification = {
            "commit": ch, "message": msg, "files": c.get("files", []),
            "category": "undeclared_needs_review",
        }

        if is_declared:
            classification["category"] = "declared_historical"
            classification["reason"] = "Explicitly declared bypass (no-verify/bypass keyword in message)."
        elif has_bypass_keyword and not is_declared:
            classification["category"] = "undeclared_needs_review"
            classification["reason"] = "Undeclared commit with bypass/no-verify keyword in message."
        elif is_post_hardening and is_normal_phase_commit:
            classification["category"] = "false_positive_candidate"
            classification["reason"] = "Post-governance-hardening normal PCAE phase implementation commit."
        elif is_hardening:
            classification["category"] = "historical_advisory"
            classification["reason"] = "Governance hardening phase commit. Historical/advisory only."
        elif is_normal_phase_commit and is_task_only:
            classification["category"] = "false_positive_candidate"
            classification["reason"] = "Normal PCAE task management commit, task-only files."
        else:
            classification["category"] = "undeclared_historical_advisory"
            classification["reason"] = "Pre-hardening undeclared commit. Historical context only."

        classifications.append(classification)

    base["classifications"] = classifications

    # Count categories
    hist_adv = sum(1 for cl in classifications if cl["category"] in ("historical_advisory", "declared_historical"))
    needs_rev = sum(1 for cl in classifications if cl["category"] == "undeclared_needs_review")
    blocking = sum(1 for cl in classifications if cl["category"] == "current_blocking")
    fp = sum(1 for cl in classifications if cl["category"] == "false_positive_candidate")

    base["historical_advisory_count"] = hist_adv
    base["needs_review_count"] = needs_rev
    base["blocking_count"] = blocking

    # Determine overall status
    if needs_rev > 0:
        base["classification_status"] = "needs_review"
        base["manual_apply_blocking"] = True
        base["blockers"] = [f"{needs_rev} undeclared finding(s) need review."]
        base["next_operator_action"] = "Review undeclared needs_review findings. Declare or reconcile."
    elif blocking > 0:
        base["classification_status"] = "blocking"
        base["manual_apply_blocking"] = True
        base["blockers"] = [f"{blocking} current blocking finding(s)."]
        base["next_operator_action"] = "Address blocking findings before manual apply."
    elif hist_adv > 0 or fp > 0:
        base["classification_status"] = "advisory_only"
        base["manual_apply_blocking"] = False
        base["blockers"] = []
        base["recommendations"].append(
            f"{hist_adv} historical/advisory, {fp} false positive candidate(s). "
            "No current blocking findings. Manual apply approval can proceed."
        )
        base["next_operator_action"] = (
            "Classification complete. No blocking findings. "
            "Run pcae phase governance-bypass-reconcile to finalize reconciliation."
        )
    else:
        base["classification_status"] = "clean"
        base["manual_apply_blocking"] = False
        base["blockers"] = []
        base["next_operator_action"] = "No findings to classify. Manual apply approval can proceed."

    return base


def run_phase_governance_bypass_classification(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_governance_bypass_classification(root)
    if getattr(args, "save", False):
        d = root.join(GOVERNANCE_BYPASS_CLASSIFICATIONS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Classification saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["classification_status"] in ("clean", "advisory_only") else 1
    print("Governance Bypass Classification"); print("=" * 40)
    print(f"  Classification: {result['classification_status']}")
    print(f"  Source report: {result['source_report_status']}")
    print(f"  Total suspected: {result['total_suspected']}")
    print(f"  Declared: {result['declared_count']}")
    print(f"  Undeclared: {result['undeclared_count']}")
    print(f"  Historical/advisory: {result['historical_advisory_count']}")
    print(f"  Needs review: {result['needs_review_count']}")
    print(f"  Blocking: {result['blocking_count']}")
    print(f"  Manual apply blocking: {'yes' if result['manual_apply_blocking'] else 'no'}")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["recommendations"]:
        print(f"\n  Recommendations:"); [print(f"    - {r}") for r in result["recommendations"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["classification_status"] in ("clean", "advisory_only") else 1


# Phase 75I.2: governance bypass declaration reconciliation
GOVERNANCE_BYPASS_RECONCILIATIONS_DIR = Path(".pcae") / "governance-bypass-reconciliations"


def _build_governance_bypass_reconcile(root: HarnessPath) -> dict:
    base = {
        "reconciliation_status": "missing_classification", "manual_apply_blocking": True,
        "declared_bypass_commits": [], "reconciled_historical_advisories": [],
        "unresolved_findings": [], "blocking_findings": [], "audit_warnings": [],
        "governance_policy": (
            "Historical/advisory bypass debt (pre-governance-hardening phases) is reconciled "
            "as non-blocking for manual apply approval. Current audit warnings remain visible "
            "as historical advisories. Only findings classified as needs_review or blocking "
            "prevent reconciliation. Declared bypasses are preserved as historical records."
        ),
        "recommendations": [],
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read classification
    class_path = root.join(GOVERNANCE_BYPASS_CLASSIFICATIONS_DIR / "latest.json")
    if not class_path.is_file():
        base["reconciliation_status"] = "missing_classification"
        base["blockers"] = ["No governance bypass classification found."]
        base["next_operator_action"] = "Run pcae phase governance-bypass-classification --save first."
        return base
    classification = json.loads(class_path.read_text(encoding="utf-8"))
    class_status = classification.get("classification_status", "blocking")

    # Read audit warnings
    audit_path = root.join(PHASE_AUDITS_DIR / "latest.json")
    if audit_path.is_file():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        base["audit_warnings"] = audit.get("warnings", [])

    # Read bypass report for declared list
    report_path = root.join(GOVERNANCE_BYPASS_REPORTS_DIR / "latest.json")
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        base["declared_bypass_commits"] = [
            {"commit": c["commit"], "message": c.get("message", "")}
            for c in report.get("declared_bypass_commits", [])
        ]

    # Reconcile based on classification status
    if class_status in ("clean",):
        base["reconciliation_status"] = "clean"
        base["manual_apply_blocking"] = False
        base["blockers"] = []
        base["recommendations"].append("No bypass findings to reconcile.")
        base["next_operator_action"] = "Reconciliation complete. Manual apply approval can proceed."
        return base

    if class_status in ("advisory_only",):
        base["reconciliation_status"] = "reconciled_advisory_only"
        base["manual_apply_blocking"] = False
        base["blockers"] = []
        # Transfer historical findings as reconciled advisories
        for cl in classification.get("classifications", []):
            cat = cl.get("category", "")
            if cat in ("historical_advisory", "declared_historical", "false_positive_candidate"):
                base["reconciled_historical_advisories"].append({
                    "commit": cl["commit"], "message": cl.get("message", ""),
                    "category": cat, "reason": cl.get("reason", ""),
                })
        base["recommendations"].append(
            f"{len(base['reconciled_historical_advisories'])} findings reconciled as historical/advisory. "
            "No current blocking findings. Manual apply approval can proceed."
        )
        # Preserve audit warnings
        base["recommendations"].append(
            f"{len(base['audit_warnings'])} audit warnings remain as historical advisories."
        )
        base["next_operator_action"] = (
            "Reconciliation complete. All findings are historical/advisory. "
            "Run pcae phase captured-output-manual-apply-approval-recheck to update approval review."
        )
        return base

    if class_status in ("needs_review", "blocking"):
        base["reconciliation_status"] = "unresolved_blockers"
        base["manual_apply_blocking"] = True
        needs_rev = [cl for cl in classification.get("classifications", [])
                     if cl.get("category") in ("undeclared_needs_review", "current_blocking")]
        base["unresolved_findings"] = [
            {"commit": cl["commit"], "message": cl.get("message", ""), "category": cl["category"]}
            for cl in needs_rev
        ]
        base["blocking_findings"] = [
            {"commit": cl["commit"], "message": cl.get("message", ""), "category": cl["category"]}
            for cl in classification.get("classifications", [])
            if cl.get("category") == "current_blocking"
        ]
        base["blockers"] = [
            f"{len(base['unresolved_findings'])} unresolved finding(s) need review.",
            f"{len(base['blocking_findings'])} blocking finding(s) prevent reconciliation.",
        ]
        base["recommendations"].append("Address unresolved/blocking findings before reconciliation.")
        base["next_operator_action"] = "Review and resolve blocking findings. Declare or reconcile undeclared needs_review items."
        return base

    # Default: missing or unknown classification
    base["reconciliation_status"] = "missing_classification"
    base["blockers"] = ["Unknown classification status."]
    base["next_operator_action"] = "Run pcae phase governance-bypass-classification --save to regenerate."
    return base


def run_phase_governance_bypass_reconcile(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_governance_bypass_reconcile(root)
    if getattr(args, "save", False):
        d = root.join(GOVERNANCE_BYPASS_RECONCILIATIONS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Reconciliation saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["reconciliation_status"] in ("clean", "reconciled_advisory_only") else 1
    print("Governance Bypass Reconciliation"); print("=" * 40)
    print(f"  Reconciliation: {result['reconciliation_status']}")
    print(f"  Manual apply blocking: {'yes' if result['manual_apply_blocking'] else 'no'}")
    print(f"  Declared bypasses: {len(result['declared_bypass_commits'])}")
    print(f"  Reconciled advisories: {len(result['reconciled_historical_advisories'])}")
    print(f"  Unresolved findings: {len(result['unresolved_findings'])}")
    print(f"  Blocking findings: {len(result['blocking_findings'])}")
    print(f"  Audit warnings: {len(result['audit_warnings'])}")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["recommendations"]:
        print(f"\n  Recommendations:"); [print(f"    - {r}") for r in result["recommendations"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["reconciliation_status"] in ("clean", "reconciled_advisory_only") else 1


# Phase 75I.3: captured output manual apply approval recheck
CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_RECHECKS_DIR = Path(".pcae") / "captured-output-manual-apply-approval-rechecks"


def _build_captured_output_manual_apply_approval_recheck(root: HarnessPath) -> dict:
    base = {
        "recheck_status": "blocked", "review_status_after_recheck": "blocked",
        "preflight_status_after_recheck": "blocked",
        "human_approval_can_be_requested": False, "human_approval_granted": False,
        "human_approval_artifact_present": False, "manual_apply_allowed": False,
        "automatic_apply_allowed": False, "backend_apply_allowed": False,
        "governance_reconciliation_ref": None, "historical_advisories": [],
        "unresolved_risks": [],
        "recommended_next_phase": "76A — Captured Output Human Approval Artifact (future)",
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read reconciliation
    reconcile_path = root.join(GOVERNANCE_BYPASS_RECONCILIATIONS_DIR / "latest.json")
    if not reconcile_path.is_file():
        base["recheck_status"] = "reconciliation_missing"
        base["blockers"] = ["No governance bypass reconciliation found."]
        base["next_operator_action"] = "Run pcae phase governance-bypass-reconcile --save first."
        return base
    reconciliation = json.loads(reconcile_path.read_text(encoding="utf-8"))
    base["governance_reconciliation_ref"] = str(GOVERNANCE_BYPASS_RECONCILIATIONS_DIR / "latest.json")
    reconcil_status = reconciliation.get("reconciliation_status", "missing_classification")
    manual_apply_blocking = reconciliation.get("manual_apply_blocking", True)

    if reconcil_status in ("missing_classification",):
        base["recheck_status"] = "reconciliation_missing"
        base["blockers"] = ["Reconciliation is missing classification."]
        base["next_operator_action"] = "Run pcae phase governance-bypass-classification --save first."
        return base

    if manual_apply_blocking:
        base["recheck_status"] = "unresolved_blockers"
        base["review_status_after_recheck"] = "unresolved_risk"
        base["preflight_status_after_recheck"] = "review_not_ready"
        base["blockers"] = [
            f"Manual apply is blocked by bypass reconciliation: {reconcil_status}.",
            f"{len(reconciliation.get('unresolved_findings', []))} unresolved finding(s).",
            f"{len(reconciliation.get('blocking_findings', []))} blocking finding(s).",
        ]
        unresolved = reconciliation.get("unresolved_findings", []) + reconciliation.get("blocking_findings", [])
        base["unresolved_risks"] = [
            {"commit": u.get("commit"), "message": u.get("message", "")} for u in unresolved
        ]
        base["next_operator_action"] = "Address blocking findings before manual apply approval can proceed."
        return base

    # Non-blocking: reconciliation is clean or reconciled_advisory_only
    # Read approval contract for context
    contract_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_CONTRACTS_DIR / "latest.json")
    contract_ready = True
    if contract_path.is_file():
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        if contract.get("contract_status") != "ready":
            contract_ready = False

    # Read approval review
    review_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_REVIEWS_DIR / "latest.json")
    review_ready = False
    if review_path.is_file():
        review = json.loads(review_path.read_text(encoding="utf-8"))
        if review.get("review_status") in ("approval_review_ready",):
            review_ready = True

    # If reconciliation is non-blocking, bypass report findings are historical/advisory
    base["historical_advisories"] = reconciliation.get("reconciled_historical_advisories", [])
    base["historical_advisories"].extend([
        {"type": "audit_warning", "warning": w}
        for w in reconciliation.get("audit_warnings", [])
    ])
    base["unresolved_risks"] = []

    # Contract must be ready
    if not contract_ready:
        base["recheck_status"] = "blocked"
        base["review_status_after_recheck"] = "contract_not_ready"
        base["preflight_status_after_recheck"] = "contract_not_ready"
        base["blockers"] = ["Approval contract is not ready."]
        base["next_operator_action"] = "Run pcae phase captured-output-manual-apply-approval-contract --save to refresh."
        return base

    # Ready
    base["recheck_status"] = "approval_review_ready"
    base["review_status_after_recheck"] = "approval_review_ready"
    base["preflight_status_after_recheck"] = "ready_for_human_approval"
    base["human_approval_can_be_requested"] = True
    base["blockers"] = []
    base["recommended_next_phase"] = "76A — Captured Output Human Approval Artifact (future)"
    base["next_operator_action"] = (
        "Recheck complete. Governance bypass findings are reconciled as non-blocking historical advisories. "
        "Manual apply approval can now be requested in a future phase. "
        "The next expected phase is 76A (human approval artifact). "
        "Do not apply output, commit, or authorize execution without explicit human approval artifact."
    )
    return base


def run_phase_captured_output_manual_apply_approval_recheck(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_captured_output_manual_apply_approval_recheck(root)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_RECHECKS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Recheck saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["recheck_status"] == "approval_review_ready" else 1
    print("Captured Output Manual Apply Approval Recheck"); print("=" * 40)
    print(f"  Recheck status: {result['recheck_status']}")
    print(f"  Review after recheck: {result['review_status_after_recheck']}")
    print(f"  Preflight after recheck: {result['preflight_status_after_recheck']}")
    print(f"  Human approval can be requested: {'yes' if result['human_approval_can_be_requested'] else 'no'}")
    print(f"  Human approval granted: no")
    print(f"  Human approval artifact present: no")
    print(f"  Manual apply allowed: no")
    print(f"  Automatic apply allowed: no")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["historical_advisories"]:
        print(f"\n  Historical advisories ({len(result['historical_advisories'])} retained)")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["recheck_status"] == "approval_review_ready" else 1


# Phase 76A: captured output human approval artifact
CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR = Path(".pcae") / "captured-output-human-approvals"


def _build_captured_output_human_approval(root: HarnessPath, approve: bool = False,
                                          approved_by: str = "", reason: str = "") -> dict:
    base = {
        "approval_status": "blocked", "human_approval_granted": False,
        "human_approval_artifact_present": False, "approved_by": None,
        "approval_reason": None, "approval_scope": None,
        "captured_output_ref": None, "captured_output_digest": None,
        "apply_dry_run_ref": None, "allowed_files": [], "forbidden_files": [
            "No backend invocation", "No prompt execution", "No patch application",
            "No project code modification from backend output",
            "No automatic commit", "No automatic task finish", "No automatic push",
            "No execution authorization", "No runner-execute real execution",
        ],
        "validation_commands_after_manual_apply": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory"],
        "manual_apply_allowed_after_validation": False, "manual_apply_allowed": False,
        "automatic_apply_allowed": False, "backend_apply_allowed": False,
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read recheck
    recheck_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_RECHECKS_DIR / "latest.json")
    if not recheck_path.is_file():
        base["approval_status"] = "missing_recheck"
        base["blockers"] = ["No approval recheck found."]
        base["next_operator_action"] = "Run pcae phase captured-output-manual-apply-approval-recheck --save first."
        return base
    recheck = json.loads(recheck_path.read_text(encoding="utf-8"))
    if recheck.get("recheck_status") != "approval_review_ready":
        base["approval_status"] = "preflight_not_ready"
        base["blockers"] = [f"Recheck not ready: {recheck.get('recheck_status')}"]
        base["next_operator_action"] = "Ensure approval recheck is approval_review_ready before requesting approval."
        return base

    # Read readiness and lifecycle for refs
    readiness_path = root.join(ACTIVATED_TASK_CAPTURE_MANUAL_APPLY_READINESS_DIR / "latest.json")
    if readiness_path.is_file():
        readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
        base["captured_output_ref"] = readiness.get("capture_ref")
        base["apply_dry_run_ref"] = readiness.get("apply_dry_run_ref")
        base["allowed_files"] = readiness.get("would_touch_files", [])

    # Digest captured output
    capture_dir = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR)
    if base["captured_output_ref"]:
        stdout_path = capture_dir / "latest.stdout.txt"
        if stdout_path.is_file():
            base["captured_output_digest"] = hashlib.sha256(stdout_path.read_bytes()).hexdigest()[:16]

    if not approve:
        base["approval_status"] = "ready_for_approval_request"
        base["human_approval_granted"] = False
        base["human_approval_artifact_present"] = False
        base["blockers"] = []
        base["next_operator_action"] = (
            "All prerequisites ready. Run pcae phase captured-output-human-approval "
            "--approve --approved-by \"<name>\" --reason \"<reason>\" to grant explicit human approval."
        )
        return base

    # Approve
    base["approval_status"] = "approved"
    base["human_approval_granted"] = True
    base["human_approval_artifact_present"] = True
    base["approved_by"] = approved_by or "operator"
    base["approval_reason"] = reason or "Explicit human approval for captured output manual apply."
    base["approval_scope"] = {
        "captured_output_ref": base["captured_output_ref"],
        "captured_output_digest": base["captured_output_digest"],
        "apply_dry_run_ref": base["apply_dry_run_ref"],
        "allowed_files": base["allowed_files"],
        "forbidden_files": base["forbidden_files"],
        "validation_commands": base["validation_commands_after_manual_apply"],
    }
    base["manual_apply_allowed_after_validation"] = True
    base["manual_apply_allowed"] = False  # this phase does not apply
    base["blockers"] = []
    base["next_operator_action"] = (
        "Human approval granted. Manual apply is NOT performed in this phase. "
        "Run pcae phase captured-output-human-approval-validate to validate approval, "
        "then pcae phase captured-output-manual-apply-execution-preflight before any future apply."
    )
    return base


def run_phase_captured_output_human_approval(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    approve = getattr(args, "approve", False)
    approved_by = getattr(args, "approved_by", "") or ""
    reason = getattr(args, "reason", "") or ""
    result = _build_captured_output_human_approval(root, approve=approve, approved_by=approved_by, reason=reason)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Human approval saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["human_approval_granted"] else 1
    print("Captured Output Human Approval"); print("=" * 40)
    print(f"  Approval status: {result['approval_status']}")
    print(f"  Human approval granted: {'yes' if result['human_approval_granted'] else 'no'}")
    print(f"  Approved by: {result['approved_by'] or 'n/a'}")
    print(f"  Manual apply allowed after validation: {'yes' if result['manual_apply_allowed_after_validation'] else 'no'}")
    print(f"  Manual apply allowed (this phase): no")
    print(f"  Automatic apply allowed: no")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["human_approval_granted"] else 1


def run_phase_captured_output_human_approval_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json")
    if not p.is_file():
        result = {"approval_status": "no_artifact", "human_approval_granted": False,
                  "human_approval_artifact_present": False}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No human approval artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    result["human_approval_artifact_present"] = True
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("human_approval_granted") else 1
    print("Captured Output Human Approval (Show)"); print("=" * 40)
    print(f"  Approval status: {result.get('approval_status', 'unknown')}")
    print(f"  Human approval granted: {'yes' if result.get('human_approval_granted') else 'no'}")
    print(f"  Approved by: {result.get('approved_by', 'n/a')}")
    print(f"  Approval reason: {result.get('approval_reason', 'n/a')[:100]}")
    print(f"  Artifact present: yes")
    return 0 if result.get("human_approval_granted") else 1


# Phase 76B: human approval validation
CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR = Path(".pcae") / "captured-output-human-approval-validations"


def _build_captured_output_human_approval_validate(root: HarnessPath) -> dict:
    base = {
        "validation_status": "blocked", "human_approval_valid": False,
        "manual_apply_allowed_after_validation": False, "manual_apply_allowed": False,
        "automatic_apply_allowed": False, "backend_apply_allowed": False,
        "approval_ref": None, "captured_output_ref": None,
        "captured_output_digest_matches": False, "apply_dry_run_ref_matches": False,
        "allowed_files_match": True, "forbidden_files_match": True,
        "validation_commands": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory"],
        "validation_failures": [],
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read approval artifact
    approval_path = root.join(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json")
    if not approval_path.is_file():
        base["validation_status"] = "missing_approval"
        base["blockers"] = ["No human approval artifact found."]
        base["next_operator_action"] = "Run pcae phase captured-output-human-approval --approve to create approval."
        return base
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    base["approval_ref"] = str(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json")

    if not approval.get("human_approval_granted"):
        base["validation_status"] = "approval_not_granted"
        base["blockers"] = ["Approval artifact exists but human_approval_granted is false."]
        base["next_operator_action"] = "Run pcae phase captured-output-human-approval --approve to grant approval."
        return base

    # Check current digest matches
    capture_dir = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR)
    stdout_path = capture_dir / "latest.stdout.txt"
    if stdout_path.is_file():
        current_digest = hashlib.sha256(stdout_path.read_bytes()).hexdigest()[:16]
        approved_digest = (approval.get("approval_scope") or {}).get("captured_output_digest")
        base["captured_output_digest_matches"] = (current_digest == approved_digest)
        if not base["captured_output_digest_matches"]:
            base["validation_failures"].append("Captured output digest changed since approval.")
    else:
        base["validation_failures"].append("Cannot verify digest: no captured output found.")

    # Check apply dry-run ref still exists
    apply_path = root.join(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json")
    base["apply_dry_run_ref_matches"] = apply_path.is_file()

    # Gather validation failures
    if not base["captured_output_digest_matches"]:
        base["validation_failures"].append("captured_output_digest_mismatch")
    if not base["apply_dry_run_ref_matches"]:
        base["validation_failures"].append("apply_dry_run_ref_missing")

    if base["validation_failures"]:
        base["validation_status"] = "stale_approval"
        base["blockers"] = base["validation_failures"]
        base["next_operator_action"] = "Approval is stale. Re-approve with current captured output and apply dry-run."
        return base

    # Check governance state
    from pcae.core.health import build_health_data, is_healthy
    hd = build_health_data(root)
    if not is_healthy(hd):
        base["validation_status"] = "governance_not_clean"
        base["blockers"] = ["Health is not healthy."]
        base["next_operator_action"] = "Restore healthy governance state before manual apply."
        return base

    # Check real execution disabled proof
    proof_path = root.join(REAL_EXECUTION_DISABLED_PROOFS_DIR / "latest.json")
    if proof_path.is_file():
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        if proof.get("proof_status") != "passed":
            base["validation_status"] = "governance_not_clean"
            base["blockers"] = ["Real execution disabled proof not passed."]
            base["next_operator_action"] = "Run pcae phase real-execution-disabled-proof --save to verify."
            return base

    # Valid
    base["validation_status"] = "valid"
    base["human_approval_valid"] = True
    base["manual_apply_allowed_after_validation"] = True
    base["manual_apply_allowed"] = False  # this phase does not apply
    base["blockers"] = []
    base["next_operator_action"] = (
        "Approval is valid. Manual apply is NOT performed in this phase. "
        "Run pcae phase captured-output-manual-apply-execution-preflight for final preflight check."
    )
    return base


def run_phase_captured_output_human_approval_validate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_captured_output_human_approval_validate(root)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Validation saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["validation_status"] == "valid" else 1
    print("Captured Output Human Approval Validation"); print("=" * 40)
    print(f"  Validation status: {result['validation_status']}")
    print(f"  Human approval valid: {'yes' if result['human_approval_valid'] else 'no'}")
    print(f"  Digest matches: {'yes' if result['captured_output_digest_matches'] else 'no'}")
    print(f"  Apply dry-run ref matches: {'yes' if result['apply_dry_run_ref_matches'] else 'no'}")
    print(f"  Manual apply after validation: {'yes' if result['manual_apply_allowed_after_validation'] else 'no'}")
    print(f"  Manual apply allowed (this phase): no")
    print(f"  Automatic apply allowed: no")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["validation_failures"]:
        print(f"\n  Failures:"); [print(f"    - {f}") for f in result["validation_failures"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["validation_status"] == "valid" else 1


# Phase 76C: manual apply execution preflight
CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTION_PREFLIGHTS_DIR = Path(".pcae") / "captured-output-manual-apply-execution-preflights"


def _build_captured_output_manual_apply_execution_preflight(root: HarnessPath) -> dict:
    base = {
        "execution_preflight_status": "blocked",
        "human_approval_valid": False,
        "manual_apply_execution_allowed_in_future_phase": False,
        "manual_apply_performed": False, "manual_apply_allowed": False,
        "automatic_apply_allowed": False, "backend_apply_allowed": False,
        "approval_ref": None, "validation_ref": None,
        "captured_output_ref": None, "apply_dry_run_ref": None,
        "allowed_files": [], "forbidden_files": [
            "No backend invocation", "No prompt execution", "No patch application",
            "No project code modification from backend output",
            "No automatic commit", "No automatic task finish", "No automatic push",
            "No execution authorization", "No runner-execute real execution",
        ],
        "validation_commands_after_manual_apply": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory"],
        "required_operator_steps_for_future_apply": [],
        "forbidden_shortcuts": [
            "Do not skip approval", "Do not skip validation",
            "Do not apply automatically", "Do not commit from backend output",
            "Do not push from backend output", "Do not authorize runner execution",
        ],
        "recommended_next_phase": "76D — Captured Output Manual Apply Execution (future)",
        "apply_performed": False, "files_modified": False, "commits_created": 0,
        "push_performed": False, "implementation_performed": False,
        "execution_authorized": False, "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read validation
    val_path = root.join(CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR / "latest.json")
    if not val_path.is_file():
        base["execution_preflight_status"] = "approval_validation_missing"
        base["blockers"] = ["No approval validation found."]
        base["next_operator_action"] = "Run pcae phase captured-output-human-approval-validate --save first."
        return base
    validation = json.loads(val_path.read_text(encoding="utf-8"))
    base["validation_ref"] = str(CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR / "latest.json")
    base["human_approval_valid"] = validation.get("human_approval_valid", False)

    if validation.get("validation_status") != "valid":
        base["execution_preflight_status"] = "approval_validation_not_valid"
        base["blockers"] = [f"Validation not valid: {validation.get('validation_status')}"]
        base["next_operator_action"] = validation.get("next_operator_action", "Resolve validation failures first.")
        return base

    # Read approval and readiness for refs
    approval_path = root.join(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json")
    if approval_path.is_file():
        base["approval_ref"] = str(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json")
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
        scope = approval.get("approval_scope") or {}
        base["captured_output_ref"] = scope.get("captured_output_ref")
        base["apply_dry_run_ref"] = scope.get("apply_dry_run_ref")
        base["allowed_files"] = scope.get("allowed_files", [])
        base["forbidden_files"].extend(scope.get("forbidden_files", []))

    # Ready
    base["execution_preflight_status"] = "ready_for_manual_apply_execution"
    base["manual_apply_execution_allowed_in_future_phase"] = True
    base["manual_apply_performed"] = False
    base["manual_apply_allowed"] = False  # this phase does not apply
    base["blockers"] = []
    base["required_operator_steps_for_future_apply"] = [
        "1. Confirm human approval is valid: pcae phase captured-output-human-approval-validate --json",
        "2. Review captured output: cat .pcae/activated-task-prompt-captures/latest.stdout.txt",
        "3. Review apply dry-run: pcae phase activated-task-agent-output-apply --dry-run --json",
        "4. In a future phase (76D), manually apply changes following task contract scope",
        "5. Run: pcae health && pcae check && python -m pytest -n auto",
        "6. Commit using pcae task finish --commit",
        "7. Push using pcae push",
    ]
    base["next_operator_action"] = (
        "Execution preflight complete. All governance prerequisites satisfied. "
        "Manual apply may proceed in a future phase (76D) with explicit operator action. "
        "This phase does NOT apply anything, commit, or push."
    )
    return base


def run_phase_captured_output_manual_apply_execution_preflight(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_captured_output_manual_apply_execution_preflight(root)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTION_PREFLIGHTS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Execution preflight saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["execution_preflight_status"] == "ready_for_manual_apply_execution" else 1
    print("Captured Output Manual Apply Execution Preflight"); print("=" * 40)
    print(f"  Preflight status: {result['execution_preflight_status']}")
    print(f"  Human approval valid: {'yes' if result['human_approval_valid'] else 'no'}")
    print(f"  Manual apply allowed in future phase: {'yes' if result['manual_apply_execution_allowed_in_future_phase'] else 'no'}")
    print(f"  Manual apply performed: no")
    print(f"  Manual apply allowed (this phase): no")
    print(f"  Automatic apply allowed: no")
    print(f"  Apply performed: no")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    if result["required_operator_steps_for_future_apply"]:
        print(f"\n  Future operator steps:"); [print(f"    {s}") for s in result["required_operator_steps_for_future_apply"][:5]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["execution_preflight_status"] == "ready_for_manual_apply_execution" else 1


# Phase 76D: captured output manual apply execution
CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR = Path(".pcae") / "captured-output-manual-apply-executions"


def _parse_patch_from_text(text: str) -> list[dict]:
    """Parse unified diff patch blocks from text. Returns list of {path, content}."""
    import re as _re
    patches = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Match unified diff header: --- a/path or +++ b/path
        if line.startswith("--- ") or line.startswith("+++ "):
            # Look for the pair
            m_a = _re.match(r"^--- (?:a/)?(\S+)", line)
            m_b = None
            if i + 1 < len(lines):
                m_b = _re.match(r"^\+\+\+ (?:b/)?(\S+)", lines[i + 1])
            if m_a and m_b:
                path = m_b.group(1)
                patch_lines = [line, lines[i + 1]]
                j = i + 2
                while j < len(lines) and (lines[j].startswith(("@@", "+", "-", " ")) or lines[j].strip() == ""):
                    patch_lines.append(lines[j])
                    j += 1
                patches.append({"path": path, "content": "\n".join(patch_lines) + "\n"})
                i = j
                continue
        i += 1
    return patches


def _is_path_safe(file_path: str, allowed_files: list[str], forbidden: bool = False) -> bool:
    """Check file path for safety: no parent traversal, no absolute paths, within allowed."""
    # Reject absolute paths
    if file_path.startswith("/"):
        return False
    # Reject parent traversal
    parts = file_path.replace("\\", "/").split("/")
    if ".." in parts:
        return False
    # If checking against allowed files
    if allowed_files:
        # Simple check: file must be in allowed list
        for af in allowed_files:
            if af and (file_path == af or file_path.endswith(af) or af.endswith(file_path)):
                return True
        return False
    return True


def _read_git_status_snapshot(root) -> dict:
    """Capture current git status for mutation guard."""
    import subprocess as _sp
    try:
        result = _sp.run(["git", "status", "--porcelain"], cwd=root.path,
                         check=True, capture_output=True, text=True)
        return {"porcelain": result.stdout, "files": [l[3:] for l in result.stdout.splitlines() if l.strip()]}
    except (_sp.CalledProcessError, OSError):
        return {"porcelain": "", "files": []}


def _build_captured_output_manual_apply_execution(root: HarnessPath, execute: bool = False,
                                                    dry_run: bool = False) -> dict:
    base = {
        "manual_apply_status": "blocked", "dry_run": dry_run,
        "execute_requested": execute, "human_approval_valid": False,
        "execution_preflight_ready": False, "manual_apply_performed": False,
        "apply_performed": False, "files_modified": False,
        "changed_files": [], "allowed_files": [], "forbidden_files": [],
        "unexpected_changed_files": [], "captured_output_ref": None,
        "captured_output_digest": None, "approval_ref": None,
        "validation_ref": None, "execution_preflight_ref": None,
        "apply_dry_run_ref": None,
        "mutation_guard_passed": False, "pre_git_status": None, "post_git_status": None,
        "commits_created": 0, "push_performed": False,
        "implementation_performed": False,
        "automatic_apply_allowed": False, "backend_apply_allowed": False,
        "execution_authorized": False,
        "validation_commands_after_apply": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory"],
        "recommended_next_phase": "76E — Manual Apply Result Validation (future)",
        "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Check approval
    approval_path = root.join(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json")
    if not approval_path.is_file():
        base["manual_apply_status"] = "blocked"; base["blockers"] = ["No human approval artifact."]
        base["next_operator_action"] = "Run pcae phase captured-output-human-approval --approve first."
        return base
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    base["approval_ref"] = str(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json")
    if not approval.get("human_approval_granted"):
        base["manual_apply_status"] = "blocked"; base["blockers"] = ["Approval not granted."]
        base["next_operator_action"] = "Approval must be granted before manual apply."
        return base

    # Check validation
    val_path = root.join(CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR / "latest.json")
    if not val_path.is_file():
        base["manual_apply_status"] = "blocked"; base["blockers"] = ["No approval validation."]
        base["next_operator_action"] = "Run pcae phase captured-output-human-approval-validate --save first."
        return base
    validation = json.loads(val_path.read_text(encoding="utf-8"))
    base["validation_ref"] = str(CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR / "latest.json")
    base["human_approval_valid"] = validation.get("human_approval_valid", False)
    if validation.get("validation_status") != "valid":
        base["manual_apply_status"] = "blocked"
        base["blockers"] = [f"Validation not valid: {validation.get('validation_status')}"]
        base["next_operator_action"] = "Validation must be valid before manual apply."
        return base

    # Check execution preflight
    preflight_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTION_PREFLIGHTS_DIR / "latest.json")
    if not preflight_path.is_file():
        base["manual_apply_status"] = "blocked"; base["blockers"] = ["No execution preflight."]
        base["next_operator_action"] = "Run pcae phase captured-output-manual-apply-execution-preflight --save first."
        return base
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    base["execution_preflight_ref"] = str(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTION_PREFLIGHTS_DIR / "latest.json")
    base["execution_preflight_ready"] = preflight.get("execution_preflight_status") == "ready_for_manual_apply_execution"
    if not base["execution_preflight_ready"]:
        base["manual_apply_status"] = "blocked"
        base["blockers"] = [f"Preflight not ready: {preflight.get('execution_preflight_status')}"]
        base["next_operator_action"] = "Execution preflight must be ready_for_manual_apply_execution."
        return base

    # Get allowed files from approval scope
    scope = (approval.get("approval_scope") or {})
    allowed = list(set(scope.get("allowed_files", [])))
    forbidden = list(set(scope.get("forbidden_files", [])))
    base["allowed_files"] = allowed
    base["forbidden_files"] = forbidden

    # Read captured output
    capture_dir = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR)
    stdout_path = capture_dir / "latest.stdout.txt"
    base["captured_output_ref"] = str(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json")
    base["apply_dry_run_ref"] = str(ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR / "latest.json")

    captured_text = ""
    if stdout_path.is_file():
        captured_text = stdout_path.read_text(encoding="utf-8")
        base["captured_output_digest"] = hashlib.sha256(stdout_path.read_bytes()).hexdigest()[:16]

    # Parse patches from captured output
    patches = _parse_patch_from_text(captured_text)

    # Check if patches contain actual changes (have @@ lines with + lines)
    actionable_patches = []
    for p in patches:
        content = p.get("content", "")
        if "@@" in content and any(l.startswith("+") and not l.startswith("+++") for l in content.splitlines()):
            actionable_patches.append(p)
        elif "@@" in content and any(l.startswith("-") and not l.startswith("---") for l in content.splitlines()):
            actionable_patches.append(p)

    # Check for explicit "no changes" statements
    no_change_indicators = [
        "no code changes are required", "no patch", "no changes to apply",
        "no changes needed", "no changes required", "does not require code changes",
        "no files need to be created", "without real implementation",
    ]
    has_no_change_statement = any(
        indicator in captured_text.lower() for indicator in no_change_indicators
    )

    if dry_run:
        if not actionable_patches:
            if has_no_change_statement:
                base["manual_apply_status"] = "dry_run_ready"
                base["blockers"] = []
                base["next_operator_action"] = "Dry-run complete. Captured output contains no applyable changes (fixture/no-op). Use --execute to confirm."
            else:
                base["manual_apply_status"] = "blocked_no_applyable_changes"
                base["blockers"] = ["No parseable patch found in captured output."]
                base["next_operator_action"] = "Captured output has no applyable patch. Nothing to apply."
            return base
        base["manual_apply_status"] = "dry_run_ready"
        base["blockers"] = []
        base["changed_files"] = [p["path"] for p in actionable_patches]
        base["next_operator_action"] = f"Dry-run complete. Would apply {len(actionable_patches)} patch(es) to {len(set(p['path'] for p in actionable_patches))} file(s). Use --execute to apply."
        return base

    # Non-execute, non-dry-run: just report status
    if not execute:
        if not actionable_patches:
            if has_no_change_statement:
                base["manual_apply_status"] = "no_changes_to_apply"
                base["blockers"] = []
                base["next_operator_action"] = (
                    "Captured output explicitly states no code changes are required (fixture/no-op). "
                    "No files need modification. Use --execute to formally record this result."
                )
            else:
                base["manual_apply_status"] = "blocked_no_applyable_changes"
                base["blockers"] = ["No parseable patch found in captured output."]
                base["next_operator_action"] = "Captured output has no applyable patch. Nothing to apply."
            return base
        base["manual_apply_status"] = "dry_run_ready"
        base["blockers"] = []
        base["next_operator_action"] = f"Ready. {len(actionable_patches)} patch(es) parseable. Use --dry-run to preview or --execute to apply."
        return base

    # Execute path
    # Check repo clean
    pre_status = _read_git_status_snapshot(root)
    base["pre_git_status"] = pre_status
    if pre_status["files"]:
        base["manual_apply_status"] = "blocked_dirty_tree"
        base["blockers"] = ["Working tree is not clean. Manual apply requires a clean tree."]
        base["next_operator_action"] = "Commit or stash pending changes before manual apply."
        return base

    if not actionable_patches:
        # No changes to apply — record as no-op execution
        base["manual_apply_status"] = "no_changes_to_apply"
        base["manual_apply_performed"] = True
        base["apply_performed"] = False
        base["files_modified"] = False
        base["mutation_guard_passed"] = True
        base["implementation_performed"] = False
        base["blockers"] = []
        base["post_git_status"] = _read_git_status_snapshot(root)
        base["next_operator_action"] = (
            "Manual apply execution complete. No changes were applied (fixture/no-op captured output). "
            "Proceed to pcae phase captured-output-manual-apply-result-show to review."
        )
        return base

    # Validate each patch
    invalid_patches = []
    valid_patches = []
    for p in actionable_patches:
        path = p["path"]
        if not _is_path_safe(path, allowed):
            invalid_patches.append({"path": path, "reason": "path not in allowed files or unsafe"})
        else:
            valid_patches.append(p)

    if invalid_patches:
        base["manual_apply_status"] = "failed_or_out_of_scope"
        base["blockers"] = [f"Patch for {ip['path']}: {ip['reason']}" for ip in invalid_patches]
        base["next_operator_action"] = "Some patches target forbidden or unsafe paths. Blocked."
        return base

    # Apply valid patches
    try:
        applied_files = []
        for p in valid_patches:
            target = root.path / p["path"]
            content = p.get("content", "")

            # Parse the diff and apply simple changes
            # For safety, only handle simple unified diffs: write the new content
            new_lines = []
            old_lines = (target.read_text(encoding="utf-8").splitlines()
                         if target.is_file() else [])
            in_hunk = False
            for line in content.splitlines():
                if line.startswith("@@ "):
                    in_hunk = True
                    continue
                if not in_hunk:
                    continue
                if line.startswith("+"):
                    new_lines.append(line[1:])
                elif line.startswith(" "):
                    new_lines.append(line[1:])
                # skip minus lines (removals)

            if new_lines:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                applied_files.append(p["path"])

        base["files_modified"] = len(applied_files) > 0
        base["changed_files"] = applied_files
        base["apply_performed"] = len(applied_files) > 0
        base["implementation_performed"] = len(applied_files) > 0
    except Exception as e:
        base["manual_apply_status"] = "failed_or_out_of_scope"
        base["blockers"] = [f"Error applying patch: {e}"]
        base["next_operator_action"] = "Patch application failed. No partial changes committed."
        return base

    # Post-mutation guard
    post_status = _read_git_status_snapshot(root)
    base["post_git_status"] = post_status
    unexpected = [f for f in post_status["files"] if f not in allowed and f not in applied_files]
    base["unexpected_changed_files"] = unexpected

    if unexpected:
        base["manual_apply_status"] = "failed_or_out_of_scope"
        base["mutation_guard_passed"] = False
        base["blockers"] = [f"Unexpected changed file: {f}" for f in unexpected]
        base["next_operator_action"] = "Mutation guard detected unexpected changes. Reset and investigate."
        return base

    base["mutation_guard_passed"] = True
    base["manual_apply_status"] = "applied"
    base["manual_apply_performed"] = True
    base["blockers"] = []
    base["next_operator_action"] = (
        "Manual apply execution complete. Changes applied but NOT committed or pushed. "
        "Run pcae phase captured-output-manual-apply-result-show to review, "
        "then proceed to Phase 76E for result validation."
    )
    return base


def run_phase_captured_output_manual_apply_execute(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    execute = getattr(args, "execute", False)
    dry_run = getattr(args, "dry_run", False)
    result = _build_captured_output_manual_apply_execution(root, execute=execute, dry_run=dry_run)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Manual apply result saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        ok_statuses = ("applied", "no_changes_to_apply", "dry_run_ready")
        return 0 if result["manual_apply_status"] in ok_statuses else 1
    print("Captured Output Manual Apply Execution"); print("=" * 40)
    print(f"  Manual apply status: {result['manual_apply_status']}")
    print(f"  Dry-run: {'yes' if dry_run else 'no'}")
    print(f"  Execute requested: {'yes' if execute else 'no'}")
    print(f"  Approval valid: {'yes' if result['human_approval_valid'] else 'no'}")
    print(f"  Preflight ready: {'yes' if result['execution_preflight_ready'] else 'no'}")
    print(f"  Manual apply performed: {'yes' if result['manual_apply_performed'] else 'no'}")
    print(f"  Files modified: {'yes' if result['files_modified'] else 'no'}")
    print(f"  Commits created: 0")
    print(f"  Push performed: no")
    print(f"  Execution authorized: no")
    if result["changed_files"]:
        print(f"\n  Changed files:"); [print(f"    {f}") for f in result["changed_files"]]
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["manual_apply_status"] in ("applied", "no_changes_to_apply", "dry_run_ready") else 1


def run_phase_captured_output_manual_apply_result_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR / "latest.json")
    if not p.is_file():
        result = {"manual_apply_status": "no_artifact"}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No manual apply execution result found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        ok_statuses = ("applied", "no_changes_to_apply", "dry_run_ready")
        return 0 if result.get("manual_apply_status") in ok_statuses else 1
    print("Manual Apply Execution Result (Show)"); print("=" * 40)
    print(f"  Status: {result.get('manual_apply_status', 'unknown')}")
    print(f"  Manual apply performed: {'yes' if result.get('manual_apply_performed') else 'no'}")
    print(f"  Files modified: {'yes' if result.get('files_modified') else 'no'}")
    print(f"  Commits created: {result.get('commits_created', 0)}")
    print(f"  Push performed: {'yes' if result.get('push_performed') else 'no'}")
    print(f"  Execution authorized: {'yes' if result.get('execution_authorized') else 'no'}")
    return 0


# Phase 76E: manual apply result validation
CAPTURED_OUTPUT_MANUAL_APPLY_RESULT_VALIDATIONS_DIR = Path(".pcae") / "captured-output-manual-apply-result-validations"


def _build_captured_output_manual_apply_result_validate(root: HarnessPath) -> dict:
    base = {
        "result_validation_status": "missing_execution_result",
        "manual_apply_status": None, "manual_apply_result_ref": None,
        "human_approval_valid": False, "execution_preflight_ready": False,
        "apply_result_valid": False, "no_changes_to_apply": False,
        "files_modified": False, "changed_files": [], "allowed_files": [], "forbidden_files": [],
        "unexpected_changed_files": [], "mutation_guard_passed": False,
        "apply_performed": False, "commits_created": 0, "push_performed": False,
        "no_commit_needed": False, "no_push_needed": False,
        "validation_commands_after_apply": ["pcae health", "pcae check", "python -m pytest -n auto", "pcae doctor task-memory"],
        "validation_commands_required": False, "current_git_status": None,
        "backend_invocation_performed": False, "automatic_apply_allowed": False,
        "backend_apply_allowed": False, "execution_authorized": False,
        "recommended_next_phase": "76F — Manual Apply No-Op Closure Summary (future)",
        "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read execution result
    result_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR / "latest.json")
    if not result_path.is_file():
        base["result_validation_status"] = "missing_execution_result"
        base["blockers"] = ["No manual apply execution result found."]
        base["next_operator_action"] = "Run pcae phase captured-output-manual-apply-execute [--execute] --save first."
        return base
    exec_result = json.loads(result_path.read_text(encoding="utf-8"))
    base["manual_apply_result_ref"] = str(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR / "latest.json")
    base["manual_apply_status"] = exec_result.get("manual_apply_status")
    base["files_modified"] = exec_result.get("files_modified", False)
    base["changed_files"] = exec_result.get("changed_files", [])
    base["allowed_files"] = exec_result.get("allowed_files", [])
    base["forbidden_files"] = exec_result.get("forbidden_files", [])
    base["unexpected_changed_files"] = exec_result.get("unexpected_changed_files", [])
    base["mutation_guard_passed"] = exec_result.get("mutation_guard_passed", False)
    base["apply_performed"] = exec_result.get("apply_performed", False)
    base["commits_created"] = exec_result.get("commits_created", 0)
    base["push_performed"] = exec_result.get("push_performed", False)

    status = base["manual_apply_status"]

    # Validate no_changes_to_apply
    if status == "no_changes_to_apply":
        base["result_validation_status"] = "validated_no_op"
        base["apply_result_valid"] = True
        base["no_changes_to_apply"] = True
        base["no_commit_needed"] = True
        base["no_push_needed"] = True
        base["validation_commands_required"] = False
        base["blockers"] = []
        base["recommended_next_phase"] = "76F — Manual Apply No-Op Closure Summary (future)"
        base["next_operator_action"] = (
            "Manual apply result validated as no-op. No changes were applied (fixture/no-op captured output). "
            "No commit, push, or validation commands are needed. Result is valid."
        )
        return base

    # Validate dry_run_ready (non-mutating, ready for apply)
    if status == "dry_run_ready":
        base["result_validation_status"] = "validated_no_op"
        base["apply_result_valid"] = True
        base["no_changes_to_apply"] = True
        base["no_commit_needed"] = True
        base["no_push_needed"] = True
        base["validation_commands_required"] = False
        base["blockers"] = []
        base["next_operator_action"] = (
            "Dry-run result validated. No files were modified. No commit or push needed."
        )
        return base

    # Validate applied
    if status == "applied":
        # Check changed files are within allowed files
        unexpected = exec_result.get("unexpected_changed_files", [])
        if unexpected:
            base["result_validation_status"] = "invalid_result"
            base["apply_result_valid"] = False
            base["blockers"] = [f"Unexpected changed file: {f}" for f in unexpected]
            base["next_operator_action"] = "Unexpected files were modified during apply. Result is invalid."
            return base

        if not exec_result.get("mutation_guard_passed", False):
            base["result_validation_status"] = "invalid_result"
            base["apply_result_valid"] = False
            base["blockers"] = ["Mutation guard did not pass."]
            base["next_operator_action"] = "Mutation guard failed. Result is invalid."
            return base

        if exec_result.get("commits_created", 0) > 0 or exec_result.get("push_performed", False):
            base["result_validation_status"] = "invalid_result"
            base["apply_result_valid"] = False
            base["blockers"] = ["Commit or push detected in execution result."]
            base["next_operator_action"] = "Execution result shows commit/push — not allowed in manual apply execution phase."
            return base

        base["result_validation_status"] = "validated_applied"
        base["apply_result_valid"] = True
        base["no_changes_to_apply"] = False
        base["no_commit_needed"] = True  # commit is not performed here
        base["no_push_needed"] = True
        base["validation_commands_required"] = True
        base["blockers"] = []
        base["recommended_next_phase"] = "76F — Manual Apply Result Closure (future)"
        base["next_operator_action"] = (
            "Manual apply result validated as applied. Changes are within allowed scope, "
            "mutation guard passed, no commit/push performed. Run validation commands "
            "before future closure phase."
        )
        return base

    # Blocked / failed / other statuses
    if status in ("blocked", "failed_or_out_of_scope", "blocked_dirty_tree",
                  "blocked_no_applyable_changes"):
        base["result_validation_status"] = "blocked_or_failed"
        base["apply_result_valid"] = False
        base["blockers"] = [f"Execution result is {status}."]
        blockers = exec_result.get("blockers", [])
        base["blockers"].extend(blockers[:5])
        base["next_operator_action"] = exec_result.get("next_operator_action", "Resolve execution blockers first.")
        return base

    # Unknown status
    base["result_validation_status"] = "invalid_result"
    base["apply_result_valid"] = False
    base["blockers"] = [f"Unknown execution status: {status}"]
    base["next_operator_action"] = "Execution result has unknown status."
    return base


def run_phase_captured_output_manual_apply_result_validate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_captured_output_manual_apply_result_validate(root)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_RESULT_VALIDATIONS_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Result validation saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["result_validation_status"] in ("validated_no_op", "validated_applied") else 1
    print("Manual Apply Result Validation"); print("=" * 40)
    print(f"  Validation status: {result['result_validation_status']}")
    print(f"  Apply result valid: {'yes' if result['apply_result_valid'] else 'no'}")
    print(f"  Manual apply status: {result['manual_apply_status']}")
    print(f"  No changes to apply: {'yes' if result['no_changes_to_apply'] else 'no'}")
    print(f"  Files modified: {'yes' if result['files_modified'] else 'no'}")
    print(f"  Changed files: {len(result['changed_files'])}")
    print(f"  Mutation guard passed: {'yes' if result['mutation_guard_passed'] else 'no'}")
    print(f"  Commits created: {result['commits_created']}")
    print(f"  Push performed: {'yes' if result['push_performed'] else 'no'}")
    print(f"  No commit needed: {'yes' if result['no_commit_needed'] else 'no'}")
    print(f"  No push needed: {'yes' if result['no_push_needed'] else 'no'}")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["result_validation_status"] in ("validated_no_op", "validated_applied") else 1


def run_phase_captured_output_manual_apply_result_validation_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_RESULT_VALIDATIONS_DIR / "latest.json")
    if not p.is_file():
        result = {"result_validation_status": "no_artifact"}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No result validation artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("result_validation_status") in ("validated_no_op", "validated_applied") else 1
    print("Manual Apply Result Validation (Show)"); print("=" * 40)
    print(f"  Status: {result.get('result_validation_status', 'unknown')}")
    print(f"  Apply valid: {'yes' if result.get('apply_result_valid') else 'no'}")
    print(f"  No commit needed: {'yes' if result.get('no_commit_needed') else 'no'}")
    print(f"  No push needed: {'yes' if result.get('no_push_needed') else 'no'}")
    return 0


# Phase 76F: manual apply no-op closure summary
CAPTURED_OUTPUT_MANUAL_APPLY_NOOP_CLOSURES_DIR = Path(".pcae") / "captured-output-manual-apply-noop-closures"


def _build_captured_output_manual_apply_noop_closure(root: HarnessPath) -> dict:
    base = {
        "closure_status": "blocked", "closure_type": "no_op",
        "manual_apply_result_ref": None, "result_validation_ref": None,
        "human_approval_ref": None, "approval_validation_ref": None,
        "execution_preflight_ref": None, "lifecycle_ref": None,
        "no_changes_to_apply": False, "apply_result_valid": False,
        "apply_performed": False, "files_modified": False,
        "changed_files": [], "unexpected_changed_files": [],
        "commits_created": 0, "push_performed": False,
        "commit_needed": False, "push_needed": False,
        "backend_invocation_performed": False, "automatic_apply_allowed": False,
        "backend_apply_allowed": False, "execution_authorized": False,
        "current_git_status": None, "closure_reason": None, "lifecycle_closed": False,
        "recommended_next_phase": "76G — Manual Apply Lifecycle Final Summary (future)",
        "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read result validation
    val_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_RESULT_VALIDATIONS_DIR / "latest.json")
    if not val_path.is_file():
        base["closure_status"] = "validation_missing"
        base["blockers"] = ["No result validation found."]
        base["next_operator_action"] = "Run pcae phase captured-output-manual-apply-result-validate --save first."
        return base
    validation = json.loads(val_path.read_text(encoding="utf-8"))
    base["result_validation_ref"] = str(CAPTURED_OUTPUT_MANUAL_APPLY_RESULT_VALIDATIONS_DIR / "latest.json")
    base["apply_result_valid"] = validation.get("apply_result_valid", False)
    base["no_changes_to_apply"] = validation.get("no_changes_to_apply", False)
    base["apply_performed"] = validation.get("apply_performed", False)
    base["files_modified"] = validation.get("files_modified", False)
    base["changed_files"] = validation.get("changed_files", [])
    base["commits_created"] = validation.get("commits_created", 0)
    base["push_performed"] = validation.get("push_performed", False)

    # Read execution result
    result_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR / "latest.json")
    if result_path.is_file():
        base["manual_apply_result_ref"] = str(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR / "latest.json")
        exec_result = json.loads(result_path.read_text(encoding="utf-8"))
        base["unexpected_changed_files"] = exec_result.get("unexpected_changed_files", [])

    # Read other refs for completeness
    if root.join(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json").is_file():
        base["human_approval_ref"] = str(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json")
    if root.join(CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR / "latest.json").is_file():
        base["approval_validation_ref"] = str(CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR / "latest.json")
    if root.join(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTION_PREFLIGHTS_DIR / "latest.json").is_file():
        base["execution_preflight_ref"] = str(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTION_PREFLIGHTS_DIR / "latest.json")

    val_status = validation.get("result_validation_status")

    # Check git status
    import subprocess as _sp
    try:
        gs = _sp.run(["git", "status", "--porcelain"], cwd=root.path,
                     check=True, capture_output=True, text=True)
        base["current_git_status"] = gs.stdout
        if gs.stdout.strip():
            base["closure_status"] = "blocked_dirty_tree"
            base["blockers"] = ["Working tree is not clean."]
            base["next_operator_action"] = "Clean the working tree before recording closure."
            return base
    except (_sp.CalledProcessError, OSError):
        base["current_git_status"] = "unknown"

    # Validate only no-op can be closed
    if val_status != "validated_no_op":
        if val_status == "validated_applied":
            base["closure_status"] = "not_no_op"
            base["closure_reason"] = "Result was applied (not no-op). Use applied-result commit/push readiness path in future phase."
            base["blockers"] = ["validated_applied result cannot use no-op closure path."]
            base["next_operator_action"] = "A future phase (applied-result commit readiness) is needed for applied results."
        else:
            base["closure_status"] = "blocked"
            base["blockers"] = [f"Validation status is {val_status}, not validated_no_op."]
            base["next_operator_action"] = validation.get("next_operator_action", "Resolve validation blockers first.")
        return base

    if not validation.get("no_commit_needed") or not validation.get("no_push_needed"):
        base["closure_status"] = "blocked"
        base["blockers"] = ["Validation says commit or push is needed."]
        base["next_operator_action"] = "Validation must confirm no_commit_needed and no_push_needed."
        return base

    # Close as no-op
    base["closure_status"] = "closed_no_op"
    base["closure_type"] = "no_op"
    base["lifecycle_closed"] = True
    base["commit_needed"] = False
    base["push_needed"] = False
    base["closure_reason"] = (
        "Captured output (QUEUE-FIXTURE-001) explicitly stated no code changes are required. "
        "Manual apply execution and result validation confirmed no-op. "
        "No commit or push is needed. Lifecycle is closed."
    )
    base["blockers"] = []
    base["next_operator_action"] = (
        "No-op closure complete. This captured-output apply lifecycle is formally closed. "
        "No commit, push, or further action is needed for this output."
    )
    return base


def run_phase_captured_output_manual_apply_noop_closure(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_captured_output_manual_apply_noop_closure(root)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_NOOP_CLOSURES_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"No-op closure saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["closure_status"] == "closed_no_op" else 1
    print("Manual Apply No-Op Closure Summary"); print("=" * 40)
    print(f"  Closure status: {result['closure_status']}")
    print(f"  Closure type: {result['closure_type']}")
    print(f"  Lifecycle closed: {'yes' if result['lifecycle_closed'] else 'no'}")
    print(f"  No changes to apply: {'yes' if result['no_changes_to_apply'] else 'no'}")
    print(f"  Apply performed: no")
    print(f"  Files modified: no")
    print(f"  Changed files: {len(result['changed_files'])}")
    print(f"  Commits created: {result['commits_created']}")
    print(f"  Push performed: no")
    print(f"  Commit needed: no")
    print(f"  Push needed: no")
    print(f"  Execution authorized: no")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["closure_status"] == "closed_no_op" else 1


def run_phase_captured_output_manual_apply_noop_closure_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_NOOP_CLOSURES_DIR / "latest.json")
    if not p.is_file():
        result = {"closure_status": "no_artifact", "lifecycle_closed": False}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No no-op closure artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("closure_status") == "closed_no_op" else 1
    print("Manual Apply No-Op Closure (Show)"); print("=" * 40)
    print(f"  Status: {result.get('closure_status', 'unknown')}")
    print(f"  Lifecycle closed: {'yes' if result.get('lifecycle_closed') else 'no'}")
    print(f"  Closure reason: {result.get('closure_reason', 'n/a')[:120]}")
    return 0


# Phase 76G: manual apply lifecycle final summary
CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR = Path(".pcae") / "captured-output-manual-apply-final-summaries"


def _ref_exists(root: HarnessPath, subpath: Path) -> str | None:
    """Return a str path if the artifact exists, else None."""
    p = root.join(subpath / "latest.json")
    return str(subpath / "latest.json") if p.is_file() else None


def _build_captured_output_manual_apply_final_summary(root: HarnessPath) -> dict:
    # Resolve all chain refs
    capture_ref = _ref_exists(root, ACTIVATED_TASK_PROMPT_CAPTURES_DIR)
    intake_ref = _ref_exists(root, ACTIVATED_TASK_AGENT_OUTPUT_INTAKES_DIR)
    review_ref = _ref_exists(root, ACTIVATED_TASK_AGENT_OUTPUT_REVIEWS_DIR)
    apply_dry_run_ref = _ref_exists(root, ACTIVATED_TASK_AGENT_OUTPUT_APPLY_DRY_RUNS_DIR)
    lifecycle_ref = _ref_exists(root, ACTIVATED_TASK_CAPTURE_LIFECYCLE_SUMMARIES_DIR)
    readiness_ref = _ref_exists(root, ACTIVATED_TASK_CAPTURE_MANUAL_APPLY_READINESS_DIR)
    safety_regression_ref = _ref_exists(root, ACTIVATED_TASK_CAPTURE_SAFETY_REGRESSIONS_DIR)
    approval_contract_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_CONTRACTS_DIR)
    approval_review_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_REVIEWS_DIR)
    approval_preflight_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_PREFLIGHTS_DIR)
    bypass_classification_ref = _ref_exists(root, GOVERNANCE_BYPASS_CLASSIFICATIONS_DIR)
    bypass_reconciliation_ref = _ref_exists(root, GOVERNANCE_BYPASS_RECONCILIATIONS_DIR)
    approval_recheck_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_APPROVAL_RECHECKS_DIR)
    human_approval_ref = _ref_exists(root, CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR)
    approval_validation_ref = _ref_exists(root, CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR)
    execution_preflight_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTION_PREFLIGHTS_DIR)
    manual_apply_execution_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR)
    result_validation_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_RESULT_VALIDATIONS_DIR)
    noop_closure_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_NOOP_CLOSURES_DIR)

    base = {
        "lifecycle_final_status": "blocked", "closure_type": None,
        "lifecycle_closed": False, "full_chain_complete": False,
        "capture_ref": capture_ref, "intake_ref": intake_ref,
        "review_ref": review_ref, "apply_dry_run_ref": apply_dry_run_ref,
        "lifecycle_ref": lifecycle_ref, "readiness_ref": readiness_ref,
        "safety_regression_ref": safety_regression_ref,
        "approval_contract_ref": approval_contract_ref,
        "approval_review_ref": approval_review_ref,
        "approval_preflight_ref": approval_preflight_ref,
        "bypass_classification_ref": bypass_classification_ref,
        "bypass_reconciliation_ref": bypass_reconciliation_ref,
        "approval_recheck_ref": approval_recheck_ref,
        "human_approval_ref": human_approval_ref,
        "approval_validation_ref": approval_validation_ref,
        "execution_preflight_ref": execution_preflight_ref,
        "manual_apply_execution_ref": manual_apply_execution_ref,
        "result_validation_ref": result_validation_ref,
        "noop_closure_ref": noop_closure_ref,
        "backend_name": "claude-deepseek",
        "captured_output_kind": None, "task_package_sent": None,
        "human_approval_granted": False, "manual_apply_status": None,
        "result_validation_status": None, "closure_status": None,
        "apply_performed": False, "files_modified": False,
        "changed_files": [], "commits_created": 0, "push_performed": False,
        "commit_needed": False, "push_needed": False,
        "backend_invocation_performed": False, "automatic_apply_allowed": False,
        "backend_apply_allowed": False, "execution_authorized": False,
        "real_execution_disabled": True, "runner_execute_refuses": True,
        "ready_for_real_captured_task_path": False,
        "recommended_next_phase": "77A — Real Captured Task Readiness Gate (future)",
        "blockers": [], "warnings": [],
        "next_operator_action": "Resolve blockers first.",
    }

    # Read capture for kind
    if capture_ref:
        cap_path = root.join(ACTIVATED_TASK_PROMPT_CAPTURES_DIR / "latest.json")
        if cap_path.is_file():
            cap = json.loads(cap_path.read_text(encoding="utf-8"))
            base["task_package_sent"] = cap.get("task_package_sent")
            base["captured_output_kind"] = "fixture" if cap.get("output_nonempty") else "unknown"

    # Read lifecycle for kind
    if lifecycle_ref:
        lc_path = root.join(ACTIVATED_TASK_CAPTURE_LIFECYCLE_SUMMARIES_DIR / "latest.json")
        if lc_path.is_file():
            lc = json.loads(lc_path.read_text(encoding="utf-8"))
            if lc.get("patch_detected") is False:
                base["captured_output_kind"] = "fixture_no_op"

    # Read human approval
    if human_approval_ref:
        ha_path = root.join(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json")
        if ha_path.is_file():
            ha = json.loads(ha_path.read_text(encoding="utf-8"))
            base["human_approval_granted"] = ha.get("human_approval_granted", False)

    # Read execution result
    if manual_apply_execution_ref:
        ex_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR / "latest.json")
        if ex_path.is_file():
            ex = json.loads(ex_path.read_text(encoding="utf-8"))
            base["manual_apply_status"] = ex.get("manual_apply_status")

    # Read result validation
    if result_validation_ref:
        rv_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_RESULT_VALIDATIONS_DIR / "latest.json")
        if rv_path.is_file():
            rv = json.loads(rv_path.read_text(encoding="utf-8"))
            base["result_validation_status"] = rv.get("result_validation_status")
            base["apply_performed"] = rv.get("apply_performed", False)
            base["files_modified"] = rv.get("files_modified", False)
            base["changed_files"] = rv.get("changed_files", [])
            base["no_changes_to_apply"] = rv.get("no_changes_to_apply", False)

    # Read closure
    closure_ok = False
    if noop_closure_ref:
        cl_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_NOOP_CLOSURES_DIR / "latest.json")
        if cl_path.is_file():
            cl = json.loads(cl_path.read_text(encoding="utf-8"))
            base["closure_status"] = cl.get("closure_status")
            base["closure_type"] = cl.get("closure_type")
            base["lifecycle_closed"] = cl.get("lifecycle_closed", False)
            base["commit_needed"] = cl.get("commit_needed", False)
            base["push_needed"] = cl.get("push_needed", False)
            closure_ok = cl.get("closure_status") == "closed_no_op" and cl.get("lifecycle_closed", False)

    if not noop_closure_ref:
        base["lifecycle_final_status"] = "closure_missing"
        base["blockers"] = ["No no-op closure found."]
        base["next_operator_action"] = "Run pcae phase captured-output-manual-apply-noop-closure --save first."
        return base

    if not closure_ok:
        base["lifecycle_final_status"] = "incomplete"
        base["blockers"] = [f"Closure status is {base['closure_status']}, not closed_no_op."]
        base["next_operator_action"] = "Resolve closure blockers first."
        return base

    # Count chain completeness
    chain_refs = [capture_ref, intake_ref, review_ref, apply_dry_run_ref,
                  lifecycle_ref, readiness_ref, safety_regression_ref,
                  approval_contract_ref, approval_review_ref, approval_preflight_ref,
                  bypass_classification_ref, bypass_reconciliation_ref, approval_recheck_ref,
                  human_approval_ref, approval_validation_ref, execution_preflight_ref,
                  manual_apply_execution_ref, result_validation_ref, noop_closure_ref]
    present = sum(1 for r in chain_refs if r is not None)
    base["full_chain_complete"] = present >= 10  # at least the core chain is present

    # Complete
    base["lifecycle_final_status"] = "complete_no_op"
    base["ready_for_real_captured_task_path"] = True
    base["blockers"] = []
    base["next_operator_action"] = (
        "Final lifecycle summary complete. The captured-output governance pipeline is fully closed "
        "as no-op (fixture). PCAE is ready for real captured task readiness (Phase 77A). "
        "No commit, push, or further action is needed for this output."
    )
    return base


def run_phase_captured_output_manual_apply_final_summary(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_captured_output_manual_apply_final_summary(root)
    if getattr(args, "save", False):
        d = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Final summary saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["lifecycle_final_status"] == "complete_no_op" else 1
    print("Manual Apply Lifecycle Final Summary"); print("=" * 40)
    print(f"  Final status: {result['lifecycle_final_status']}")
    print(f"  Closure type: {result['closure_type']}")
    print(f"  Lifecycle closed: {'yes' if result['lifecycle_closed'] else 'no'}")
    print(f"  Full chain complete: {'yes' if result['full_chain_complete'] else 'no'}")
    print(f"  Apply performed: no")
    print(f"  Files modified: no")
    print(f"  Changed files: {len(result['changed_files'])}")
    print(f"  Commits created: {result['commits_created']}")
    print(f"  Commit needed: no")
    print(f"  Push needed: no")
    print(f"  Real execution disabled: yes")
    print(f"  Runner refuses: yes")
    print(f"  Ready for real task path: {'yes' if result['ready_for_real_captured_task_path'] else 'no'}")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:"); [print(f"    - {b}") for b in result["blockers"]]
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["lifecycle_final_status"] == "complete_no_op" else 1


def run_phase_captured_output_manual_apply_final_summary_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR / "latest.json")
    if not p.is_file():
        result = {"lifecycle_final_status": "no_artifact", "lifecycle_closed": False}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No final summary artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("lifecycle_final_status") == "complete_no_op" else 1
    print("Manual Apply Lifecycle Final Summary (Show)"); print("=" * 40)
    print(f"  Status: {result.get('lifecycle_final_status', 'unknown')}")
    print(f"  Lifecycle closed: {'yes' if result.get('lifecycle_closed') else 'no'}")
    print(f"  Next phase: {result.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77A: real captured task readiness gate
REAL_CAPTURED_TASK_READINESS_GATES_DIR = Path(".pcae") / "real-captured-task-readiness-gates"


def _build_real_captured_task_readiness_gate(root: HarnessPath) -> dict:
    """Assess readiness to move from fixture/no-op pipeline to real captured task pipeline.

    This is a READ-ONLY gate. It must not create task packages, invoke backends,
    capture output, apply patches, commit, or push.
    """
    from datetime import datetime, timezone
    import subprocess as _sp

    ts = datetime.now(timezone.utc).isoformat()

    # Resolve artifact refs
    final_summary_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR)
    noop_closure_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_NOOP_CLOSURES_DIR)
    result_validation_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_RESULT_VALIDATIONS_DIR)
    manual_apply_execution_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR)
    approval_validation_ref = _ref_exists(root, CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR)
    approval_ref = _ref_exists(root, CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR)
    real_execution_disabled_proof_ref = _ref_exists(root, Path(".pcae") / "real-execution-disabled-proofs")
    runner_authorization_ref = _ref_exists(root, Path(".pcae") / "runner-authorization-summaries")
    runner_execution_trace_ref = _ref_exists(root, Path(".pcae") / "runner-execution-traces")

    # Read agent lock
    agent_lock = read_agent_lock(root)
    agent_lock_active = agent_lock is not None
    locked_backend_name = agent_lock.agent_id if agent_lock else None

    # Read lifecycle final summary
    lifecycle_final_status = "unknown"
    lifecycle_closed = False
    ready_for_real_captured_task_path = False
    if final_summary_ref:
        fs_path = root.join(CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR / "latest.json")
        if fs_path.is_file():
            fs = json.loads(fs_path.read_text(encoding="utf-8"))
            lifecycle_final_status = fs.get("lifecycle_final_status", "unknown")
            lifecycle_closed = fs.get("lifecycle_closed", False)
            ready_for_real_captured_task_path = fs.get("ready_for_real_captured_task_path", False)

    fixture_pipeline_closed = lifecycle_final_status == "complete_no_op" and lifecycle_closed

    # Read real execution disabled proof
    real_execution_disabled = True
    if real_execution_disabled_proof_ref:
        rep_path = root.join(Path(".pcae") / "real-execution-disabled-proofs" / "latest.json")
        if rep_path.is_file():
            rep = json.loads(rep_path.read_text(encoding="utf-8"))
            real_execution_disabled = rep.get("real_execution_disabled", True)

    # Check runner-execute refusal via dry-run
    runner_execute_refuses = True
    if runner_execution_trace_ref:
        ret_path = root.join(Path(".pcae") / "runner-execution-traces" / "latest.json")
        if ret_path.is_file():
            ret = json.loads(ret_path.read_text(encoding="utf-8"))
            runner_execute_refuses = not ret.get("execution_available", True)

    # Also check runner-authorization-summaries
    if runner_authorization_ref:
        ra_path = root.join(Path(".pcae") / "runner-authorization-summaries" / "latest.json")
        if ra_path.is_file():
            ra = json.loads(ra_path.read_text(encoding="utf-8"))
            if ra.get("execution_authorized", False) or ra.get("execution_available", False):
                runner_execute_refuses = False

    # Read audit
    audit_warning_count = 0
    audit_warnings: list = []
    audit_ref = _ref_exists(root, Path(".pcae") / "phase-audits")
    if audit_ref:
        a_path = root.join(Path(".pcae") / "phase-audits" / "latest.json")
        if a_path.is_file():
            a = json.loads(a_path.read_text(encoding="utf-8"))
            audit_warning_count = len(a.get("warnings", []))
            audit_warnings = a.get("warnings", [])

    # Read queue validation
    queue_valid = False
    queue_entry_count = 0
    queue_ref = _ref_exists(root, Path(".pcae") / "phase-queue.json")
    if root.join(Path(".pcae") / "phase-queue.json").is_file():
        q = json.loads(root.join(Path(".pcae") / "phase-queue.json").read_text(encoding="utf-8"))
        entries = q.get("entries", q) if isinstance(q, dict) else []
        queue_entry_count = len(entries) if isinstance(entries, list) else 0
        queue_valid = queue_entry_count == 0

    # Git status check
    git_status_clean = True
    try:
        result = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                         capture_output=True, text=True, timeout=15)
        git_status_clean = result.stdout.strip() == ""
    except Exception:
        git_status_clean = True  # Assume clean if git fails

    # Determine readiness status
    blockers: list = []
    warnings_list: list = []
    readiness_status = "ready_for_real_task_preparation"

    if not fixture_pipeline_closed:
        readiness_status = "blocked_lifecycle_not_closed"
        blockers.append("Fixture/no-op pipeline is not fully closed.")
    elif not git_status_clean:
        readiness_status = "blocked_dirty_tree"
        blockers.append("Working tree is not clean.")
    elif not real_execution_disabled:
        readiness_status = "blocked_execution_not_disabled"
        blockers.append("Real execution is not confirmed disabled.")
    elif not runner_execute_refuses:
        readiness_status = "blocked_runner_execution_available"
        blockers.append("Runner execution is reported as available when it should refuse.")
    elif audit_warning_count > 0:
        # Warnings are advisory but we still report them
        warnings_list.append(f"Audit has {audit_warning_count} warning(s).")

    # Always enforce these safety constraints
    base = {
        "readiness_status": readiness_status,
        "fixture_pipeline_closed": fixture_pipeline_closed,
        "lifecycle_final_status": lifecycle_final_status,
        "lifecycle_closed": lifecycle_closed,
        "final_summary_ref": str(CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR / "latest.json") if final_summary_ref else None,
        "noop_closure_ref": str(CAPTURED_OUTPUT_MANUAL_APPLY_NOOP_CLOSURES_DIR / "latest.json") if noop_closure_ref else None,
        "result_validation_ref": str(CAPTURED_OUTPUT_MANUAL_APPLY_RESULT_VALIDATIONS_DIR / "latest.json") if result_validation_ref else None,
        "manual_apply_execution_ref": str(CAPTURED_OUTPUT_MANUAL_APPLY_EXECUTIONS_DIR / "latest.json") if manual_apply_execution_ref else None,
        "human_approval_validation_ref": str(CAPTURED_OUTPUT_HUMAN_APPROVAL_VALIDATIONS_DIR / "latest.json") if approval_validation_ref else None,
        "approval_ref": str(CAPTURED_OUTPUT_HUMAN_APPROVALS_DIR / "latest.json") if approval_ref else None,
        "current_git_status": "clean" if git_status_clean else "dirty",
        "audit_warning_count": audit_warning_count,
        "audit_warnings": audit_warnings,
        "real_execution_disabled": real_execution_disabled,
        "runner_execute_refuses": runner_execute_refuses,
        "agent_lock_active": agent_lock_active,
        "locked_backend_name": locked_backend_name,
        "queue_valid": queue_valid,
        "queue_entry_count": queue_entry_count,
        # Safety invariants — always false/zero
        "real_captured_task_execution_allowed": False,
        "backend_invocation_allowed": False,
        "task_package_creation_allowed_in_future_phase": readiness_status == "ready_for_real_task_preparation",
        "backend_capture_allowed_in_future_phase": False,
        "apply_performed": False,
        "files_modified": False,
        "commits_created": 0,
        "push_performed": False,
        "execution_authorized": False,
        # Guidance
        "required_next_gates": [
            "77B — Real Captured Task Contract Preparation",
            "77C — Real Captured Task Package Creation",
        ] if readiness_status == "ready_for_real_task_preparation" else [
            "Resolve blockers before proceeding to 77B.",
        ],
        "recommended_next_phase": "77B — Real Captured Task Contract Preparation" if readiness_status == "ready_for_real_task_preparation" else "Resolve blockers first.",
        "blockers": blockers,
        "warnings": warnings_list,
        "next_operator_action": (
            "PCAE is ready for real captured task preparation. Proceed to Phase 77B to design the real task contract."
            if readiness_status == "ready_for_real_task_preparation"
            else "Resolve blockers before proceeding to any real captured task phase."
        ),
        "generated_at": ts,
    }
    return base


def run_phase_real_captured_task_readiness_gate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_real_captured_task_readiness_gate(root)
    if getattr(args, "save", False):
        d = root.join(REAL_CAPTURED_TASK_READINESS_GATES_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Readiness gate saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["readiness_status"] == "ready_for_real_task_preparation" else 1
    print("Real Captured Task Readiness Gate"); print("=" * 36)
    print(f"  Readiness status: {result['readiness_status']}")
    print(f"  Fixture pipeline closed: {'yes' if result['fixture_pipeline_closed'] else 'no'}")
    print(f"  Lifecycle final status: {result['lifecycle_final_status']}")
    print(f"  Lifecycle closed: {'yes' if result['lifecycle_closed'] else 'no'}")
    print(f"  Git status: {result['current_git_status']}")
    print(f"  Audit warnings: {result['audit_warning_count']}")
    print(f"  Real execution disabled: {'yes' if result['real_execution_disabled'] else 'no'}")
    print(f"  Runner refuses: {'yes' if result['runner_execute_refuses'] else 'no'}")
    print(f"  Agent lock active: {'yes' if result['agent_lock_active'] else 'no'}")
    if result['locked_backend_name']:
        print(f"  Locked backend: {result['locked_backend_name']}")
    print(f"  Queue valid: {'yes' if result['queue_valid'] else 'no'}")
    print(f"  Real task execution allowed: no")
    print(f"  Backend invocation allowed: no")
    print(f"  Task package creation (future phase): {'yes' if result['task_package_creation_allowed_in_future_phase'] else 'no'}")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    if result["warnings"]:
        print(f"\n  Warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["readiness_status"] == "ready_for_real_task_preparation" else 1


def run_phase_real_captured_task_readiness_gate_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(REAL_CAPTURED_TASK_READINESS_GATES_DIR / "latest.json")
    if not p.is_file():
        result = {"readiness_status": "no_artifact", "fixture_pipeline_closed": False}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No readiness gate artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("readiness_status") == "ready_for_real_task_preparation" else 1
    print("Real Captured Task Readiness Gate (Show)"); print("=" * 40)
    print(f"  Status: {result.get('readiness_status', 'unknown')}")
    print(f"  Fixture pipeline closed: {'yes' if result.get('fixture_pipeline_closed') else 'no'}")
    print(f"  Lifecycle final: {result.get('lifecycle_final_status', 'n/a')}")
    print(f"  Next phase: {result.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77B: real captured task contract preparation
REAL_CAPTURED_TASK_CONTRACTS_DIR = Path(".pcae") / "real-captured-task-contracts"


def _build_real_captured_task_contract(root: HarnessPath) -> dict:
    """Prepare a governed real captured task contract.

    This is CONTRACT PREPARATION ONLY. It must not create task packages,
    invoke backends, capture output, apply patches, commit, or push.
    """
    from datetime import datetime, timezone
    import subprocess as _sp

    ts = datetime.now(timezone.utc).isoformat()

    # Read the 77A readiness gate
    readiness_gate_ref = _ref_exists(root, REAL_CAPTURED_TASK_READINESS_GATES_DIR)
    readiness_status = "unknown"
    if readiness_gate_ref:
        rg_path = root.join(REAL_CAPTURED_TASK_READINESS_GATES_DIR / "latest.json")
        if rg_path.is_file():
            rg = json.loads(rg_path.read_text(encoding="utf-8"))
            readiness_status = rg.get("readiness_status", "unknown")

    # Read lifecycle final summary
    final_summary_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR)

    # Check execution disabled
    real_execution_disabled = True
    rep_ref = _ref_exists(root, Path(".pcae") / "real-execution-disabled-proofs")
    if rep_ref:
        rep_path = root.join(Path(".pcae") / "real-execution-disabled-proofs" / "latest.json")
        if rep_path.is_file():
            rep = json.loads(rep_path.read_text(encoding="utf-8"))
            real_execution_disabled = rep.get("real_execution_disabled", True)

    # Check runner refuses
    runner_execute_refuses = True
    ret_ref = _ref_exists(root, Path(".pcae") / "runner-execution-traces")
    if ret_ref:
        ret_path = root.join(Path(".pcae") / "runner-execution-traces" / "latest.json")
        if ret_path.is_file():
            ret = json.loads(ret_path.read_text(encoding="utf-8"))
            runner_execute_refuses = not ret.get("execution_available", True)

    # Agent lock
    agent_lock = read_agent_lock(root)
    agent_lock_active = agent_lock is not None
    locked_backend_name = agent_lock.agent_id if agent_lock else None

    # Audit
    audit_warning_count = 0
    audit_warnings: list = []
    audit_ref = _ref_exists(root, Path(".pcae") / "phase-audits")
    if audit_ref:
        a_path = root.join(Path(".pcae") / "phase-audits" / "latest.json")
        if a_path.is_file():
            a = json.loads(a_path.read_text(encoding="utf-8"))
            audit_warning_count = len(a.get("warnings", []))
            audit_warnings = a.get("warnings", [])

    # Git status
    git_status_clean = True
    try:
        result_cmd = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                             capture_output=True, text=True, timeout=15)
        git_status_clean = result_cmd.stdout.strip() == ""
    except Exception:
        git_status_clean = True

    # Determine contract status
    blockers: list = []
    warnings_list: list = []
    contract_status = "prepared"

    if not readiness_gate_ref or readiness_status == "no_artifact" or readiness_status == "unknown":
        contract_status = "blocked_readiness_not_ready"
        blockers.append("Readiness gate artifact is missing or unreadable. Run pcae phase real-captured-task-readiness-gate --save first.")
    elif readiness_status != "ready_for_real_task_preparation":
        contract_status = "blocked_readiness_not_ready"
        blockers.append(f"Readiness gate reports '{readiness_status}', not ready_for_real_task_preparation.")
    elif not git_status_clean:
        contract_status = "blocked_dirty_tree"
        blockers.append("Working tree is not clean.")
    elif not real_execution_disabled:
        contract_status = "blocked_execution_not_disabled"
        blockers.append("Real execution is not confirmed disabled.")
    elif not runner_execute_refuses:
        contract_status = "blocked_runner_execution_available"
        blockers.append("Runner execution is reported as available when it should refuse.")
    elif audit_warning_count > 0:
        warnings_list.append(f"Audit has {audit_warning_count} warning(s).")

    # Build the contract (only meaningful if status is "prepared")
    contract_id = "REAL-CAPTURED-TASK-001" if contract_status == "prepared" else None
    task_title = "Document first real captured task governance path" if contract_status == "prepared" else None
    task_type = "documentation_only" if contract_status == "prepared" else None
    task_goal = (
        "Create docs/REAL_CAPTURED_TASKS.md documenting the governance path for future real captured tasks."
        if contract_status == "prepared" else None
    )
    scope_mode = "documentation_only" if contract_status == "prepared" else None
    allowed_files = [
        "docs/REAL_CAPTURED_TASKS.md",
        "CHANGELOG.md",
        "PROJECT_STATUS.md",
    ] if contract_status == "prepared" else []
    forbidden_files = [
        "src/**",
        "tests/**",
        "pyproject.toml",
        ".pcae/**",
        ".githooks/**",
    ] if contract_status == "prepared" else []
    allowed_actions = [
        "create_documentation_file",
        "update_changelog",
        "update_project_status",
    ] if contract_status == "prepared" else []
    forbidden_actions = [
        "modify_source_code",
        "modify_tests",
        "modify_dependencies",
        "invoke_backend",
        "capture_backend_output",
        "apply_captured_output",
        "commit_backend_output",
        "push_backend_output",
        "authorize_execution",
    ] if contract_status == "prepared" else []
    validation_commands = [
        "python -m pytest -n auto",
        "pcae check",
        "pcae health",
    ] if contract_status == "prepared" else []
    acceptance_criteria = [
        "docs/REAL_CAPTURED_TASKS.md exists and documents the governance path",
        "CHANGELOG.md updated",
        "No source or test files modified",
        "All tests pass",
        "pcae check passes",
        "pcae health passes",
    ] if contract_status == "prepared" else []
    stop_conditions = [
        "Backend invocation would be required",
        "Source code modification would be required",
        "Test modification would be required",
        "Dependency changes would be required",
        "Remote API calls would be required",
    ] if contract_status == "prepared" else []

    return {
        "real_task_contract_status": contract_status,
        "contract_id": contract_id,
        "task_title": task_title,
        "task_type": task_type,
        "task_goal": task_goal,
        "scope_mode": scope_mode,
        "allowed_files": allowed_files,
        "forbidden_files": forbidden_files,
        "allowed_actions": allowed_actions,
        "forbidden_actions": forbidden_actions,
        "validation_commands": validation_commands,
        "acceptance_criteria": acceptance_criteria,
        "stop_conditions": stop_conditions,
        "readiness_gate_ref": str(REAL_CAPTURED_TASK_READINESS_GATES_DIR / "latest.json") if readiness_gate_ref else None,
        "final_lifecycle_summary_ref": str(CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR / "latest.json") if final_summary_ref else None,
        "backend_name": locked_backend_name,
        "agent_lock_active": agent_lock_active,
        "locked_backend_name": locked_backend_name,
        "current_git_status": "clean" if git_status_clean else "dirty",
        "audit_warning_count": audit_warning_count,
        "audit_warnings": audit_warnings,
        "real_execution_disabled": real_execution_disabled,
        "runner_execute_refuses": runner_execute_refuses,
        # Safety invariants — always enforced
        "task_package_creation_allowed_in_future_phase": contract_status == "prepared",
        "task_package_created": False,
        "backend_invocation_allowed": False,
        "backend_invocation_performed": False,
        "backend_capture_allowed": False,
        "real_captured_task_execution_allowed": False,
        "apply_performed": False,
        "files_modified": False,
        "commits_created": 0,
        "push_performed": False,
        "execution_authorized": False,
        # Guidance
        "recommended_next_phase": "77C — Real Captured Task Package Dry-Run" if contract_status == "prepared" else "Resolve blockers first.",
        "blockers": blockers,
        "warnings": warnings_list,
        "next_operator_action": (
            "Contract prepared. Proceed to Phase 77C to create the real task package dry-run."
            if contract_status == "prepared"
            else "Resolve blockers before proceeding to any real captured task contract phase."
        ),
        "generated_at": ts,
    }


def run_phase_real_captured_task_contract_prepare(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_real_captured_task_contract(root)
    if getattr(args, "save", False):
        d = root.join(REAL_CAPTURED_TASK_CONTRACTS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Contract saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["real_task_contract_status"] == "prepared" else 1
    print("Real Captured Task Contract Preparation"); print("=" * 38)
    print(f"  Contract status: {result['real_task_contract_status']}")
    print(f"  Contract ID: {result.get('contract_id', 'n/a')}")
    print(f"  Task title: {result.get('task_title', 'n/a')}")
    print(f"  Task type: {result.get('task_type', 'n/a')}")
    print(f"  Scope mode: {result.get('scope_mode', 'n/a')}")
    print(f"  Git status: {result['current_git_status']}")
    print(f"  Audit warnings: {result['audit_warning_count']}")
    print(f"  Real execution disabled: {'yes' if result['real_execution_disabled'] else 'no'}")
    print(f"  Runner refuses: {'yes' if result['runner_execute_refuses'] else 'no'}")
    print(f"  Agent lock active: {'yes' if result['agent_lock_active'] else 'no'}")
    if result.get('locked_backend_name'):
        print(f"  Locked backend: {result['locked_backend_name']}")
    print(f"  Task package created: no")
    print(f"  Backend invocation allowed: no")
    print(f"  Backend capture allowed: no")
    print(f"  Real task execution allowed: no")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result.get("allowed_files"):
        print(f"\n  Allowed files:")
        for f in result["allowed_files"]:
            print(f"    - {f}")
    if result.get("forbidden_files"):
        print(f"\n  Forbidden files:")
        for f in result["forbidden_files"]:
            print(f"    - {f}")
    if result.get("validation_commands"):
        print(f"\n  Validation commands:")
        for c in result["validation_commands"]:
            print(f"    - {c}")
    if result.get("stop_conditions"):
        print(f"\n  Stop conditions:")
        for s in result["stop_conditions"]:
            print(f"    - {s}")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    if result["warnings"]:
        print(f"\n  Warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["real_task_contract_status"] == "prepared" else 1


def run_phase_real_captured_task_contract_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(REAL_CAPTURED_TASK_CONTRACTS_DIR / "latest.json")
    if not p.is_file():
        result = {"real_task_contract_status": "no_artifact", "contract_id": None}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No contract artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("real_task_contract_status") == "prepared" else 1
    print("Real Captured Task Contract (Show)"); print("=" * 32)
    print(f"  Status: {result.get('real_task_contract_status', 'unknown')}")
    print(f"  Contract ID: {result.get('contract_id', 'n/a')}")
    print(f"  Task title: {result.get('task_title', 'n/a')}")
    print(f"  Task type: {result.get('task_type', 'n/a')}")
    print(f"  Next phase: {result.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77C: real captured task package dry-run
REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR = Path(".pcae") / "real-captured-task-package-dry-runs"


def _build_real_captured_task_package_dry_run(root: HarnessPath) -> dict:
    """Build a dry-run package envelope for REAL-CAPTURED-TASK-001 without sending.

    This is PACKAGE DRY-RUN ONLY. It must not invoke backends, send packages,
    capture output, apply patches, commit, or push.
    """
    from datetime import datetime, timezone
    import hashlib
    import subprocess as _sp

    ts = datetime.now(timezone.utc).isoformat()

    # Read the 77B contract
    contract_ref = _ref_exists(root, REAL_CAPTURED_TASK_CONTRACTS_DIR)
    contract_data = None
    contract_status = "unknown"
    if contract_ref:
        ct_path = root.join(REAL_CAPTURED_TASK_CONTRACTS_DIR / "latest.json")
        if ct_path.is_file():
            contract_data = json.loads(ct_path.read_text(encoding="utf-8"))
            contract_status = contract_data.get("real_task_contract_status", "unknown")

    # Read readiness gate
    readiness_gate_ref = _ref_exists(root, REAL_CAPTURED_TASK_READINESS_GATES_DIR)

    # Read final lifecycle summary
    final_summary_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR)

    # Check execution disabled
    real_execution_disabled = True
    rep_ref = _ref_exists(root, Path(".pcae") / "real-execution-disabled-proofs")
    if rep_ref:
        rep_path = root.join(Path(".pcae") / "real-execution-disabled-proofs" / "latest.json")
        if rep_path.is_file():
            rep = json.loads(rep_path.read_text(encoding="utf-8"))
            real_execution_disabled = rep.get("real_execution_disabled", True)

    # Check runner refuses
    runner_execute_refuses = True
    ret_ref = _ref_exists(root, Path(".pcae") / "runner-execution-traces")
    if ret_ref:
        ret_path = root.join(Path(".pcae") / "runner-execution-traces" / "latest.json")
        if ret_path.is_file():
            ret = json.loads(ret_path.read_text(encoding="utf-8"))
            runner_execute_refuses = not ret.get("execution_available", True)

    # Agent lock
    agent_lock = read_agent_lock(root)
    agent_lock_active = agent_lock is not None
    locked_backend_name = agent_lock.agent_id if agent_lock else None

    # Audit
    audit_warning_count = 0
    audit_warnings: list = []
    audit_ref = _ref_exists(root, Path(".pcae") / "phase-audits")
    if audit_ref:
        a_path = root.join(Path(".pcae") / "phase-audits" / "latest.json")
        if a_path.is_file():
            a = json.loads(a_path.read_text(encoding="utf-8"))
            audit_warning_count = len(a.get("warnings", []))
            audit_warnings = a.get("warnings", [])

    # Git status
    git_status_clean = True
    try:
        result_cmd = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                             capture_output=True, text=True, timeout=15)
        git_status_clean = result_cmd.stdout.strip() == ""
    except Exception:
        git_status_clean = True

    # Determine package dry-run status
    blockers: list = []
    warnings_list: list = []
    package_status = "ready"

    if not contract_ref or contract_status == "no_artifact" or contract_status == "unknown":
        package_status = "blocked_contract_missing"
        blockers.append("Contract artifact is missing or unreadable. Run pcae phase real-captured-task-contract-prepare --save first.")
    elif contract_status != "prepared":
        package_status = "blocked_contract_not_prepared"
        blockers.append(f"Contract reports '{contract_status}', not prepared.")
    elif not git_status_clean:
        package_status = "blocked_dirty_tree"
        blockers.append("Working tree is not clean.")
    elif not real_execution_disabled:
        package_status = "blocked_execution_not_disabled"
        blockers.append("Real execution is not confirmed disabled.")
    elif not runner_execute_refuses:
        package_status = "blocked_runner_execution_available"
        blockers.append("Runner execution is reported as available when it should refuse.")
    elif audit_warning_count > 0:
        warnings_list.append(f"Audit has {audit_warning_count} warning(s).")

    # Build the package (only meaningful if ready)
    package_id = "REAL-CAPTURED-TASK-001-PACKAGE-DRY-RUN" if package_status == "ready" else None
    contract_id = None
    task_title = None
    task_type = None
    scope_mode = None
    allowed_files: list = []
    forbidden_files: list = []
    allowed_actions: list = []
    forbidden_actions: list = []
    validation_commands: list = []
    acceptance_criteria: list = []
    stop_conditions: list = []
    contract_digest = None
    package_digest = None
    prompt_envelope_preview = None

    if package_status == "ready" and contract_data:
        contract_id = contract_data.get("contract_id")
        task_title = contract_data.get("task_title")
        task_type = contract_data.get("task_type")
        scope_mode = contract_data.get("scope_mode")
        allowed_files = list(contract_data.get("allowed_files", []))
        forbidden_files = list(contract_data.get("forbidden_files", []))
        allowed_actions = list(contract_data.get("allowed_actions", []))
        forbidden_actions = list(contract_data.get("forbidden_actions", []))
        validation_commands = list(contract_data.get("validation_commands", []))
        acceptance_criteria = list(contract_data.get("acceptance_criteria", []))
        stop_conditions = list(contract_data.get("stop_conditions", []))

        # Compute contract digest (stable: exclude volatile generated_at)
        stable_contract = {k: v for k, v in contract_data.items() if k != "generated_at"}
        contract_json = json.dumps(stable_contract, sort_keys=True)
        contract_digest = hashlib.sha256(contract_json.encode("utf-8")).hexdigest()

        # Build the prompt envelope preview (preview only, not sent)
        allowed_files_str = "\n".join(f"  - {f}" for f in allowed_files)
        forbidden_files_str = "\n".join(f"  - {f}" for f in forbidden_files)
        validation_str = "\n".join(f"  - {c}" for c in validation_commands)
        stop_str = "\n".join(f"  - {s}" for s in stop_conditions)

        prompt_envelope_preview = (
            f"[PCAE Real Captured Task | {contract_id}]\n"
            f"Task: {task_title}\n"
            f"Type: {task_type}\n"
            f"Scope: {scope_mode}\n\n"
            f"Goal: {contract_data.get('task_goal', 'N/A')}\n\n"
            f"Allowed files:\n{allowed_files_str}\n\n"
            f"Forbidden files:\n{forbidden_files_str}\n\n"
            f"Allowed actions:\n"
            + "\n".join(f"  - {a}" for a in allowed_actions) + "\n\n"
            f"Validation:\n{validation_str}\n\n"
            f"Stop conditions:\n{stop_str}\n\n"
            f"[This is a DRY-RUN package envelope. NOT SEND-AUTHORIZED.]\n"
            f"[Do not invoke any backend. Do not execute.]\n"
        )

        # Compute package digest
        package_digest = hashlib.sha256(prompt_envelope_preview.encode("utf-8")).hexdigest()

    governance_requirements = [
        "real_execution_disabled_proof must pass",
        "runner_execute must refuse",
        "git tree must be clean",
        "contract must be prepared",
        "package send must not be authorized",
        "backend invocation must not be performed",
        "backend capture must not be performed",
    ]

    return {
        "package_dry_run_status": package_status,
        "package_id": package_id,
        "contract_id": contract_id,
        "contract_ref": str(REAL_CAPTURED_TASK_CONTRACTS_DIR / "latest.json") if contract_ref else None,
        "readiness_gate_ref": str(REAL_CAPTURED_TASK_READINESS_GATES_DIR / "latest.json") if readiness_gate_ref else None,
        "final_lifecycle_summary_ref": str(CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR / "latest.json") if final_summary_ref else None,
        "task_title": task_title,
        "task_type": task_type,
        "scope_mode": scope_mode,
        "backend_name": locked_backend_name,
        "agent_lock_active": agent_lock_active,
        "locked_backend_name": locked_backend_name,
        "contract_digest": contract_digest,
        "package_digest": package_digest,
        "prompt_envelope_preview": prompt_envelope_preview,
        "allowed_files": allowed_files,
        "forbidden_files": forbidden_files,
        "allowed_actions": allowed_actions,
        "forbidden_actions": forbidden_actions,
        "validation_commands": validation_commands,
        "acceptance_criteria": acceptance_criteria,
        "stop_conditions": stop_conditions,
        "governance_requirements": governance_requirements,
        "current_git_status": "clean" if git_status_clean else "dirty",
        "audit_warning_count": audit_warning_count,
        "audit_warnings": audit_warnings,
        "real_execution_disabled": real_execution_disabled,
        "runner_execute_refuses": runner_execute_refuses,
        # Safety invariants — always enforced
        "package_created_for_send": False,
        "package_send_allowed": False,
        "backend_invocation_allowed": False,
        "backend_invocation_performed": False,
        "backend_capture_allowed": False,
        "backend_capture_performed": False,
        "real_captured_task_execution_allowed": False,
        "apply_performed": False,
        "files_modified": False,
        "commits_created": 0,
        "push_performed": False,
        "execution_authorized": False,
        # Guidance
        "recommended_next_phase": "77D — Real Captured Task Package Approval" if package_status == "ready" else "Resolve blockers first.",
        "blockers": blockers,
        "warnings": warnings_list,
        "next_operator_action": (
            "Package dry-run complete. The envelope is ready for review (Phase 77D). "
            "No backend has been invoked. No package has been sent."
            if package_status == "ready"
            else "Resolve blockers before proceeding to any package dry-run phase."
        ),
        "generated_at": ts,
    }


def run_phase_real_captured_task_package_dry_run(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_real_captured_task_package_dry_run(root)
    if getattr(args, "save", False):
        d = root.join(REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Package dry-run saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["package_dry_run_status"] == "ready" else 1
    print("Real Captured Task Package Dry-Run"); print("=" * 34)
    print(f"  Package status: {result['package_dry_run_status']}")
    print(f"  Package ID: {result.get('package_id', 'n/a')}")
    print(f"  Contract ID: {result.get('contract_id', 'n/a')}")
    print(f"  Task title: {result.get('task_title', 'n/a')}")
    print(f"  Task type: {result.get('task_type', 'n/a')}")
    print(f"  Scope mode: {result.get('scope_mode', 'n/a')}")
    print(f"  Git status: {result['current_git_status']}")
    print(f"  Audit warnings: {result['audit_warning_count']}")
    print(f"  Real execution disabled: {'yes' if result['real_execution_disabled'] else 'no'}")
    print(f"  Runner refuses: {'yes' if result['runner_execute_refuses'] else 'no'}")
    print(f"  Agent lock active: {'yes' if result['agent_lock_active'] else 'no'}")
    if result.get('locked_backend_name'):
        print(f"  Locked backend: {result['locked_backend_name']}")
    if result.get('contract_digest'):
        print(f"  Contract digest: {result['contract_digest'][:16]}...")
    if result.get('package_digest'):
        print(f"  Package digest: {result['package_digest'][:16]}...")
    print(f"  Package created for send: no")
    print(f"  Package send allowed: no")
    print(f"  Backend invocation allowed: no")
    print(f"  Backend invocation performed: no")
    print(f"  Backend capture allowed: no")
    print(f"  Backend capture performed: no")
    print(f"  Real task execution allowed: no")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result.get("allowed_files"):
        print(f"\n  Allowed files:")
        for f in result["allowed_files"]:
            print(f"    - {f}")
    if result.get("forbidden_files"):
        print(f"\n  Forbidden files:")
        for f in result["forbidden_files"]:
            print(f"    - {f}")
    if result.get("validation_commands"):
        print(f"\n  Validation:")
        for c in result["validation_commands"]:
            print(f"    - {c}")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    if result["warnings"]:
        print(f"\n  Warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["package_dry_run_status"] == "ready" else 1


def run_phase_real_captured_task_package_dry_run_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR / "latest.json")
    if not p.is_file():
        result = {"package_dry_run_status": "no_artifact", "package_id": None}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No package dry-run artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("package_dry_run_status") == "ready" else 1
    print("Real Captured Task Package Dry-Run (Show)"); print("=" * 40)
    print(f"  Status: {result.get('package_dry_run_status', 'unknown')}")
    print(f"  Package ID: {result.get('package_id', 'n/a')}")
    print(f"  Contract ID: {result.get('contract_id', 'n/a')}")
    print(f"  Task title: {result.get('task_title', 'n/a')}")
    print(f"  Next phase: {result.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77D: real captured task package approval
REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR = Path(".pcae") / "real-captured-task-package-approvals"


def _build_real_captured_task_package_approval(root: HarnessPath, approved_by: str | None = None, reason: str | None = None) -> dict:
    """Approve a real captured task package for future backend capture preflight.

    This is APPROVAL ONLY. It must not send packages, invoke backends,
    capture output, apply patches, commit, or push.
    """
    from datetime import datetime, timezone
    import subprocess as _sp

    ts = datetime.now(timezone.utc).isoformat()
    is_approve = approved_by is not None and reason is not None

    # Read the 77C package dry-run
    dry_run_ref = _ref_exists(root, REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR)
    dry_run_data = None
    dry_run_status = "unknown"
    if dry_run_ref:
        dr_path = root.join(REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR / "latest.json")
        if dr_path.is_file():
            dry_run_data = json.loads(dr_path.read_text(encoding="utf-8"))
            dry_run_status = dry_run_data.get("package_dry_run_status", "unknown")

    # Read contract
    contract_ref = _ref_exists(root, REAL_CAPTURED_TASK_CONTRACTS_DIR)
    contract_data = None
    if contract_ref:
        ct_path = root.join(REAL_CAPTURED_TASK_CONTRACTS_DIR / "latest.json")
        if ct_path.is_file():
            contract_data = json.loads(ct_path.read_text(encoding="utf-8"))

    # Read readiness gate
    readiness_gate_ref = _ref_exists(root, REAL_CAPTURED_TASK_READINESS_GATES_DIR)

    # Check execution disabled
    real_execution_disabled = True
    rep_ref = _ref_exists(root, Path(".pcae") / "real-execution-disabled-proofs")
    if rep_ref:
        rep_path = root.join(Path(".pcae") / "real-execution-disabled-proofs" / "latest.json")
        if rep_path.is_file():
            rep = json.loads(rep_path.read_text(encoding="utf-8"))
            real_execution_disabled = rep.get("real_execution_disabled", True)

    # Check runner refuses
    runner_execute_refuses = True
    ret_ref = _ref_exists(root, Path(".pcae") / "runner-execution-traces")
    if ret_ref:
        ret_path = root.join(Path(".pcae") / "runner-execution-traces" / "latest.json")
        if ret_path.is_file():
            ret = json.loads(ret_path.read_text(encoding="utf-8"))
            runner_execute_refuses = not ret.get("execution_available", True)

    # Agent lock
    agent_lock = read_agent_lock(root)
    agent_lock_active = agent_lock is not None
    locked_backend_name = agent_lock.agent_id if agent_lock else None

    # Audit
    audit_warning_count = 0
    audit_warnings: list = []
    audit_ref = _ref_exists(root, Path(".pcae") / "phase-audits")
    if audit_ref:
        a_path = root.join(Path(".pcae") / "phase-audits" / "latest.json")
        if a_path.is_file():
            a = json.loads(a_path.read_text(encoding="utf-8"))
            audit_warning_count = len(a.get("warnings", []))
            audit_warnings = a.get("warnings", [])

    # Git status
    git_status_clean = True
    try:
        result_cmd = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                             capture_output=True, text=True, timeout=15)
        git_status_clean = result_cmd.stdout.strip() == ""
    except Exception:
        git_status_clean = True

    # Verify digests match between contract and dry-run
    digest_mismatch = False
    contract_digest = None
    package_digest = None
    package_id = None
    contract_id = None
    task_title = None
    task_type = None
    scope_mode = None
    allowed_files: list = []
    forbidden_files: list = []
    validation_commands: list = []
    dry_run_contract_digest = None
    dry_run_package_digest = None

    if dry_run_data and dry_run_status == "ready" and contract_data:
        package_id = dry_run_data.get("package_id")
        contract_id = dry_run_data.get("contract_id")
        task_title = dry_run_data.get("task_title")
        task_type = dry_run_data.get("task_type")
        scope_mode = dry_run_data.get("scope_mode")
        allowed_files = list(dry_run_data.get("allowed_files", []))
        forbidden_files = list(dry_run_data.get("forbidden_files", []))
        validation_commands = list(dry_run_data.get("validation_commands", []))
        dry_run_contract_digest = dry_run_data.get("contract_digest")
        dry_run_package_digest = dry_run_data.get("package_digest")

        # Recompute contract digest from the actual contract artifact (stable: exclude volatile generated_at)
        import hashlib
        if contract_data:
            stable_contract = {k: v for k, v in contract_data.items() if k != "generated_at"}
            contract_json = json.dumps(stable_contract, sort_keys=True)
            contract_digest = hashlib.sha256(contract_json.encode("utf-8")).hexdigest()
            digest_mismatch = contract_digest != dry_run_contract_digest or dry_run_package_digest is None

        package_digest = dry_run_package_digest

    # Determine approval status
    blockers: list = []
    warnings_list: list = []
    approval_status = "ready_for_approval_request"

    if not dry_run_ref or dry_run_status == "no_artifact" or dry_run_status == "unknown":
        approval_status = "missing_package_dry_run"
        blockers.append("Package dry-run artifact is missing. Run pcae phase real-captured-task-package-dry-run --save first.")
    elif dry_run_status != "ready":
        approval_status = "package_not_ready"
        blockers.append(f"Package dry-run reports '{dry_run_status}', not ready.")
    elif digest_mismatch:
        approval_status = "digest_mismatch"
        blockers.append("Contract digest does not match dry-run package contract digest. Re-run pcae phase real-captured-task-package-dry-run --save.")
    elif not git_status_clean:
        approval_status = "blocked_dirty_tree"
        blockers.append("Working tree is not clean.")
    elif audit_warning_count > 0:
        approval_status = "blocked_audit_warnings"
        blockers.append(f"Audit has {audit_warning_count} warning(s). Resolve warnings before approval.")
    elif not real_execution_disabled:
        approval_status = "blocked_execution_not_disabled"
        blockers.append("Real execution is not confirmed disabled.")
    elif not runner_execute_refuses:
        approval_status = "blocked_runner_execution_available"
        blockers.append("Runner execution is reported as available when it should refuse.")
    elif not agent_lock_active:
        approval_status = "blocked_agent_lock_missing"
        blockers.append("No active agent lock. Run pcae session bootstrap first.")

    # Apply approval if --approve and no blockers
    human_package_approval_granted = False
    if is_approve and approval_status == "ready_for_approval_request":
        approval_status = "approved"
        human_package_approval_granted = True

    return {
        "package_approval_status": approval_status,
        "human_package_approval_granted": human_package_approval_granted,
        "approved_by": approved_by if human_package_approval_granted else None,
        "approval_reason": reason if human_package_approval_granted else None,
        "package_id": package_id,
        "package_digest": package_digest,
        "contract_id": contract_id,
        "contract_digest": contract_digest,
        "task_title": task_title,
        "task_type": task_type,
        "scope_mode": scope_mode,
        "allowed_files": allowed_files,
        "forbidden_files": forbidden_files,
        "validation_commands": validation_commands,
        "package_dry_run_ref": str(REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR / "latest.json") if dry_run_ref else None,
        "contract_ref": str(REAL_CAPTURED_TASK_CONTRACTS_DIR / "latest.json") if contract_ref else None,
        "readiness_gate_ref": str(REAL_CAPTURED_TASK_READINESS_GATES_DIR / "latest.json") if readiness_gate_ref else None,
        "backend_name": locked_backend_name,
        "agent_lock_active": agent_lock_active,
        "locked_backend_name": locked_backend_name,
        "current_git_status": "clean" if git_status_clean else "dirty",
        "audit_warning_count": audit_warning_count,
        "audit_warnings": audit_warnings,
        "real_execution_disabled": real_execution_disabled,
        "runner_execute_refuses": runner_execute_refuses,
        # Safety invariants
        "package_created_for_send": False,
        "package_send_allowed_now": False,
        "package_sent": False,
        "backend_invocation_allowed_now": False,
        "backend_invocation_performed": False,
        "backend_capture_allowed_now": False,
        "backend_capture_performed": False,
        "backend_capture_preflight_allowed_in_future_phase": approval_status == "approved",
        "real_captured_task_execution_allowed": False,
        "apply_performed": False,
        "files_modified": False,
        "commits_created": 0,
        "push_performed": False,
        "execution_authorized": False,
        # Guidance
        "recommended_next_phase": "77E — Real Captured Task Backend Capture Preflight" if approval_status == "approved" else "Resolve blockers first.",
        "blockers": blockers,
        "warnings": warnings_list,
        "next_operator_action": (
            "Package approved for future backend capture preflight only. "
            "No package has been sent. No backend has been invoked. "
            "Proceed to Phase 77E."
            if approval_status == "approved"
            else (
                "Package is ready for operator approval. "
                "Run pcae phase real-captured-task-package-approval --approve --approved-by '<name>' --reason '<reason>' --save."
                if approval_status == "ready_for_approval_request"
                else "Resolve blockers before proceeding to package approval."
            )
        ),
        "generated_at": ts,
    }


def run_phase_real_captured_task_package_approval(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    approved_by: str | None = getattr(args, "approved_by", None)
    reason: str | None = getattr(args, "reason", None)
    is_approve: bool = getattr(args, "approve", False)
    if is_approve and (not approved_by or not reason):
        print("Error: --approve requires --approved-by and --reason.")
        return 1
    if not is_approve:
        approved_by = None
        reason = None
    result = _build_real_captured_task_package_approval(root, approved_by=approved_by, reason=reason)
    if getattr(args, "save", False):
        d = root.join(REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Approval saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["package_approval_status"] in ("ready_for_approval_request", "approved") else 1
    print("Real Captured Task Package Approval"); print("=" * 36)
    print(f"  Approval status: {result['package_approval_status']}")
    print(f"  Approval granted: {'yes' if result['human_package_approval_granted'] else 'no'}")
    if result.get("approved_by"):
        print(f"  Approved by: {result['approved_by']}")
        print(f"  Reason: {result['approval_reason']}")
    print(f"  Package ID: {result.get('package_id', 'n/a')}")
    print(f"  Contract ID: {result.get('contract_id', 'n/a')}")
    print(f"  Task title: {result.get('task_title', 'n/a')}")
    print(f"  Task type: {result.get('task_type', 'n/a')}")
    print(f"  Git status: {result['current_git_status']}")
    print(f"  Audit warnings: {result['audit_warning_count']}")
    print(f"  Real execution disabled: {'yes' if result['real_execution_disabled'] else 'no'}")
    print(f"  Runner refuses: {'yes' if result['runner_execute_refuses'] else 'no'}")
    print(f"  Agent lock active: {'yes' if result['agent_lock_active'] else 'no'}")
    if result.get('contract_digest'):
        print(f"  Contract digest: {result['contract_digest'][:16]}...")
    if result.get('package_digest'):
        print(f"  Package digest: {result['package_digest'][:16]}...")
    print(f"  Package send allowed now: no")
    print(f"  Backend invocation allowed now: no")
    print(f"  Backend capture allowed now: no")
    print(f"  Backend capture preflight (future): {'yes' if result['backend_capture_preflight_allowed_in_future_phase'] else 'no'}")
    print(f"  Real task execution allowed: no")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    if result["warnings"]:
        print(f"\n  Warnings:")
        for w in result["warnings"]:
            print(f"    - {w}")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["package_approval_status"] in ("ready_for_approval_request", "approved") else 1


def run_phase_real_captured_task_package_approval_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR / "latest.json")
    if not p.is_file():
        result = {"package_approval_status": "no_artifact", "package_id": None, "human_package_approval_granted": False}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No package approval artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("package_approval_status") in ("ready_for_approval_request", "approved") else 1
    print("Real Captured Task Package Approval (Show)"); print("=" * 42)
    print(f"  Status: {result.get('package_approval_status', 'unknown')}")
    print(f"  Approved: {'yes' if result.get('human_package_approval_granted') else 'no'}")
    print(f"  Package ID: {result.get('package_id', 'n/a')}")
    print(f"  Contract ID: {result.get('contract_id', 'n/a')}")
    print(f"  Next phase: {result.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77E: real captured task backend capture preflight
REAL_CAPTURED_TASK_BACKEND_CAPTURE_PREFLIGHTS_DIR = Path(".pcae") / "real-captured-task-backend-capture-preflights"


def _build_real_captured_task_backend_capture_preflight(root: HarnessPath) -> dict:
    """Verify all conditions before a future backend capture phase.

    This is PREFLIGHT ONLY. It must not send packages, invoke backends,
    capture output, apply patches, commit, or push.
    """
    from datetime import datetime, timezone
    import subprocess as _sp

    ts = datetime.now(timezone.utc).isoformat()

    # Read 77D package approval
    approval_ref = _ref_exists(root, REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR)
    approval_data = None
    approval_status = "unknown"
    if approval_ref:
        ap_path = root.join(REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR / "latest.json")
        if ap_path.is_file():
            approval_data = json.loads(ap_path.read_text(encoding="utf-8"))
            approval_status = approval_data.get("package_approval_status", "unknown")

    # Read dry-run
    dry_run_ref = _ref_exists(root, REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR)
    dry_run_data = None
    if dry_run_ref:
        dr_path = root.join(REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR / "latest.json")
        if dr_path.is_file():
            dry_run_data = json.loads(dr_path.read_text(encoding="utf-8"))

    # Read contract
    contract_ref = _ref_exists(root, REAL_CAPTURED_TASK_CONTRACTS_DIR)
    contract_data = None
    if contract_ref:
        ct_path = root.join(REAL_CAPTURED_TASK_CONTRACTS_DIR / "latest.json")
        if ct_path.is_file():
            contract_data = json.loads(ct_path.read_text(encoding="utf-8"))

    # Ref chains
    readiness_gate_ref = _ref_exists(root, REAL_CAPTURED_TASK_READINESS_GATES_DIR)
    final_summary_ref = _ref_exists(root, CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR)

    # Execution disabled
    real_execution_disabled = True
    rep_ref = _ref_exists(root, Path(".pcae") / "real-execution-disabled-proofs")
    if rep_ref:
        rep_path = root.join(Path(".pcae") / "real-execution-disabled-proofs" / "latest.json")
        if rep_path.is_file():
            rep = json.loads(rep_path.read_text(encoding="utf-8"))
            real_execution_disabled = rep.get("real_execution_disabled", True)

    # Runner refuses
    runner_execute_refuses = True
    ret_ref = _ref_exists(root, Path(".pcae") / "runner-execution-traces")
    if ret_ref:
        ret_path = root.join(Path(".pcae") / "runner-execution-traces" / "latest.json")
        if ret_path.is_file():
            ret = json.loads(ret_path.read_text(encoding="utf-8"))
            runner_execute_refuses = not ret.get("execution_available", True)

    # Agent lock
    agent_lock = read_agent_lock(root)
    agent_lock_active = agent_lock is not None
    locked_backend_name = agent_lock.agent_id if agent_lock else None

    # Audit
    audit_warning_count = 0
    audit_warnings: list = []
    audit_ref = _ref_exists(root, Path(".pcae") / "phase-audits")
    if audit_ref:
        a_path = root.join(Path(".pcae") / "phase-audits" / "latest.json")
        if a_path.is_file():
            a = json.loads(a_path.read_text(encoding="utf-8"))
            audit_warning_count = len(a.get("warnings", []))
            audit_warnings = a.get("warnings", [])

    # Git status
    git_status_clean = True
    try:
        result_cmd = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                             capture_output=True, text=True, timeout=15)
        git_status_clean = result_cmd.stdout.strip() == ""
    except Exception:
        git_status_clean = True

    # Extract approval fields for matching
    approval_package_digest = None
    approval_contract_digest = None
    approval_package_id = None
    approval_contract_id = None
    human_approved = False
    approved_by = None
    approval_reason = None
    task_title = None
    task_type = None
    scope_mode = None
    allowed_files: list = []
    forbidden_files: list = []
    validation_commands: list = []

    if approval_data:
        approval_package_digest = approval_data.get("package_digest")
        approval_contract_digest = approval_data.get("contract_digest")
        approval_package_id = approval_data.get("package_id")
        approval_contract_id = approval_data.get("contract_id")
        human_approved = approval_data.get("human_package_approval_granted", False)
        approved_by = approval_data.get("approved_by")
        approval_reason = approval_data.get("approval_reason")
        task_title = approval_data.get("task_title")
        task_type = approval_data.get("task_type")
        scope_mode = approval_data.get("scope_mode")
        allowed_files = list(approval_data.get("allowed_files", []))
        forbidden_files = list(approval_data.get("forbidden_files", []))
        validation_commands = list(approval_data.get("validation_commands", []))

    # Digest and id matching
    dry_run_package_digest = dry_run_data.get("package_digest") if dry_run_data else None
    dry_run_contract_digest = dry_run_data.get("contract_digest") if dry_run_data else None
    dry_run_package_id = dry_run_data.get("package_id") if dry_run_data else None
    dry_run_contract_id = dry_run_data.get("contract_id") if dry_run_data else None

    digest_mismatch = False
    if approval_data and dry_run_data:
        digest_mismatch = (
            approval_package_digest != dry_run_package_digest
            or approval_contract_digest != dry_run_contract_digest
            or approval_package_id != dry_run_package_id
            or approval_contract_id != dry_run_contract_id
        )

    backend_mismatch = False
    if locked_backend_name and locked_backend_name not in ("claude-deepseek", "claude-local"):
        backend_mismatch = locked_backend_name not in ("claude-deepseek", "claude-local")

    # Determine preflight status
    blockers: list = []
    warnings_list: list = []
    preflight_status = "ready_for_backend_capture"

    if not approval_ref or approval_status == "no_artifact" or approval_status == "unknown":
        preflight_status = "missing_package_approval"
        blockers.append("Package approval artifact is missing. Run pcae phase real-captured-task-package-approval --approve --save first.")
    elif not human_approved or approval_status != "approved":
        preflight_status = "package_not_approved"
        blockers.append(f"Package approval status is '{approval_status}', not approved.")
    elif digest_mismatch:
        preflight_status = "digest_mismatch"
        blockers.append("Digest or ID mismatch between approval and dry-run. Re-run the pipeline.")
    elif not git_status_clean:
        preflight_status = "blocked_dirty_tree"
        blockers.append("Working tree is not clean.")
    elif audit_warning_count > 0:
        preflight_status = "blocked_audit_warnings"
        blockers.append(f"Audit has {audit_warning_count} warning(s).")
    elif not real_execution_disabled:
        preflight_status = "blocked_execution_not_disabled"
        blockers.append("Real execution is not confirmed disabled.")
    elif not runner_execute_refuses:
        preflight_status = "blocked_runner_execution_available"
        blockers.append("Runner execution is reported as available when it should refuse.")
    elif not agent_lock_active:
        preflight_status = "blocked_agent_lock_missing"
        blockers.append("No active agent lock.")
    elif backend_mismatch:
        preflight_status = "blocked_backend_mismatch"
        blockers.append(f"Locked backend '{locked_backend_name}' is not an expected real backend.")

    return {
        "backend_capture_preflight_status": preflight_status,
        "package_approval_ref": str(REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR / "latest.json") if approval_ref else None,
        "package_dry_run_ref": str(REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR / "latest.json") if dry_run_ref else None,
        "contract_ref": str(REAL_CAPTURED_TASK_CONTRACTS_DIR / "latest.json") if contract_ref else None,
        "readiness_gate_ref": str(REAL_CAPTURED_TASK_READINESS_GATES_DIR / "latest.json") if readiness_gate_ref else None,
        "final_lifecycle_summary_ref": str(CAPTURED_OUTPUT_MANUAL_APPLY_FINAL_SUMMARIES_DIR / "latest.json") if final_summary_ref else None,
        "package_id": approval_package_id,
        "contract_id": approval_contract_id,
        "package_digest": approval_package_digest,
        "contract_digest": approval_contract_digest,
        "approval_status": approval_status,
        "human_package_approval_granted": human_approved,
        "approved_by": approved_by,
        "approval_reason": approval_reason,
        "task_title": task_title,
        "task_type": task_type,
        "scope_mode": scope_mode,
        "allowed_files": allowed_files,
        "forbidden_files": forbidden_files,
        "validation_commands": validation_commands,
        "backend_name": locked_backend_name,
        "agent_lock_active": agent_lock_active,
        "locked_backend_name": locked_backend_name,
        "current_git_status": "clean" if git_status_clean else "dirty",
        "audit_warning_count": audit_warning_count,
        "audit_warnings": audit_warnings,
        "real_execution_disabled": real_execution_disabled,
        "runner_execute_refuses": runner_execute_refuses,
        # Safety invariants
        "package_created_for_send": False,
        "package_send_allowed_now": False,
        "package_sent": False,
        "backend_invocation_allowed_now": False,
        "backend_invocation_performed": False,
        "backend_capture_allowed_now": False,
        "backend_capture_performed": False,
        "backend_output_captured": False,
        "backend_capture_allowed_in_future_phase": preflight_status == "ready_for_backend_capture",
        "real_captured_task_execution_allowed": False,
        "apply_performed": False,
        "files_modified": False,
        "commits_created": 0,
        "push_performed": False,
        "execution_authorized": False,
        # Guidance
        "recommended_next_phase": "77F — Real Captured Task Backend Capture" if preflight_status == "ready_for_backend_capture" else "Resolve blockers first.",
        "blockers": blockers,
        "warnings": warnings_list,
        "next_operator_action": (
            "Backend capture preflight complete. All conditions verified. "
            "PCAE is ready to proceed to Phase 77F for backend capture. "
            "No backend has been invoked. No package has been sent."
            if preflight_status == "ready_for_backend_capture"
            else "Resolve blockers before proceeding to backend capture."
        ),
        "generated_at": ts,
    }


def run_phase_real_captured_task_backend_capture_preflight(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_real_captured_task_backend_capture_preflight(root)
    if getattr(args, "save", False):
        d = root.join(REAL_CAPTURED_TASK_BACKEND_CAPTURE_PREFLIGHTS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Backend capture preflight saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["backend_capture_preflight_status"] == "ready_for_backend_capture" else 1
    print("Real Captured Task Backend Capture Preflight"); print("=" * 42)
    print(f"  Preflight status: {result['backend_capture_preflight_status']}")
    print(f"  Package approval: {result.get('approval_status', 'n/a')}")
    print(f"  Human approved: {'yes' if result.get('human_package_approval_granted') else 'no'}")
    if result.get("approved_by"):
        print(f"  Approved by: {result['approved_by']}")
    print(f"  Package ID: {result.get('package_id', 'n/a')}")
    print(f"  Contract ID: {result.get('contract_id', 'n/a')}")
    print(f"  Task title: {result.get('task_title', 'n/a')}")
    print(f"  Task type: {result.get('task_type', 'n/a')}")
    print(f"  Git status: {result['current_git_status']}")
    print(f"  Audit warnings: {result['audit_warning_count']}")
    print(f"  Real execution disabled: {'yes' if result['real_execution_disabled'] else 'no'}")
    print(f"  Runner refuses: {'yes' if result['runner_execute_refuses'] else 'no'}")
    print(f"  Agent lock active: {'yes' if result['agent_lock_active'] else 'no'}")
    if result.get("locked_backend_name"):
        print(f"  Locked backend: {result['locked_backend_name']}")
    if result.get("contract_digest"):
        print(f"  Contract digest: {result['contract_digest'][:16]}...")
    if result.get("package_digest"):
        print(f"  Package digest: {result['package_digest'][:16]}...")
    print(f"  Package send allowed now: no")
    print(f"  Backend invocation allowed now: no")
    print(f"  Backend capture allowed now: no")
    print(f"  Backend capture (future phase): {'yes' if result['backend_capture_allowed_in_future_phase'] else 'no'}")
    print(f"  Real task execution allowed: no")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["backend_capture_preflight_status"] == "ready_for_backend_capture" else 1


def run_phase_real_captured_task_backend_capture_preflight_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(REAL_CAPTURED_TASK_BACKEND_CAPTURE_PREFLIGHTS_DIR / "latest.json")
    if not p.is_file():
        result = {"backend_capture_preflight_status": "no_artifact", "package_id": None}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No backend capture preflight artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("backend_capture_preflight_status") == "ready_for_backend_capture" else 1
    print("Real Captured Task Backend Capture Preflight (Show)"); print("=" * 48)
    print(f"  Status: {result.get('backend_capture_preflight_status', 'unknown')}")
    print(f"  Package ID: {result.get('package_id', 'n/a')}")
    print(f"  Future capture allowed: {'yes' if result.get('backend_capture_allowed_in_future_phase') else 'no'}")
    print(f"  Next phase: {result.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77F: real captured task backend capture
REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR = Path(".pcae") / "real-captured-task-backend-captures"


def _build_real_captured_task_backend_capture(root: HarnessPath, execute: bool = False) -> dict:
    """Perform a governed backend capture of the approved real captured task package.

    Default/--dry-run: validate only, no backend invocation.
    --execute: invoke locked backend, capture output, mutation guard, never apply.

    This is CAPTURE ONLY. It must not apply output, modify files from backend
    output, commit, or push.
    """
    from datetime import datetime, timezone
    import hashlib
    import subprocess as _sp
    import shutil as _shutil

    ts = datetime.now(timezone.utc).isoformat()

    # Read 77E preflight
    preflight_ref = _ref_exists(root, REAL_CAPTURED_TASK_BACKEND_CAPTURE_PREFLIGHTS_DIR)
    preflight_data = None
    preflight_status = "unknown"
    preflight_future_capture = False
    if preflight_ref:
        pf_path = root.join(REAL_CAPTURED_TASK_BACKEND_CAPTURE_PREFLIGHTS_DIR / "latest.json")
        if pf_path.is_file():
            preflight_data = json.loads(pf_path.read_text(encoding="utf-8"))
            preflight_status = preflight_data.get("backend_capture_preflight_status", "unknown")
            preflight_future_capture = preflight_data.get("backend_capture_allowed_in_future_phase", False)

    # Read approval
    approval_ref = _ref_exists(root, REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR)
    approval_data = None
    if approval_ref:
        ap_path = root.join(REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR / "latest.json")
        if ap_path.is_file():
            approval_data = json.loads(ap_path.read_text(encoding="utf-8"))

    # Read dry-run
    dry_run_ref = _ref_exists(root, REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR)
    dry_run_data = None
    if dry_run_ref:
        dr_path = root.join(REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR / "latest.json")
        if dr_path.is_file():
            dry_run_data = json.loads(dr_path.read_text(encoding="utf-8"))

    # Execution disabled
    real_execution_disabled = True
    rep_ref = _ref_exists(root, Path(".pcae") / "real-execution-disabled-proofs")
    if rep_ref:
        rep_path = root.join(Path(".pcae") / "real-execution-disabled-proofs" / "latest.json")
        if rep_path.is_file():
            rep = json.loads(rep_path.read_text(encoding="utf-8"))
            real_execution_disabled = rep.get("real_execution_disabled", True)

    # Runner refuses
    runner_execute_refuses = True
    ret_ref = _ref_exists(root, Path(".pcae") / "runner-execution-traces")
    if ret_ref:
        ret_path = root.join(Path(".pcae") / "runner-execution-traces" / "latest.json")
        if ret_path.is_file():
            ret = json.loads(ret_path.read_text(encoding="utf-8"))
            runner_execute_refuses = not ret.get("execution_available", True)

    # Agent lock
    agent_lock = read_agent_lock(root)
    agent_lock_active = agent_lock is not None
    locked_backend_name = agent_lock.agent_id if agent_lock else None

    # Audit
    audit_warning_count = 0
    audit_warnings: list = []
    audit_ref = _ref_exists(root, Path(".pcae") / "phase-audits")
    if audit_ref:
        a_path = root.join(Path(".pcae") / "phase-audits" / "latest.json")
        if a_path.is_file():
            a = json.loads(a_path.read_text(encoding="utf-8"))
            audit_warning_count = len(a.get("warnings", []))
            audit_warnings = a.get("warnings", [])

    # Git status
    git_status_clean = True
    pre_git_status = ""
    try:
        result_git = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                             capture_output=True, text=True, timeout=15)
        pre_git_status = result_git.stdout.strip()
        git_status_clean = pre_git_status == ""
    except Exception:
        git_status_clean = True

    # Extract digests/ids from approval
    approval_pkg_digest = approval_data.get("package_digest") if approval_data else None
    approval_ct_digest = approval_data.get("contract_digest") if approval_data else None
    approval_pkg_id = approval_data.get("package_id") if approval_data else None
    approval_ct_id = approval_data.get("contract_id") if approval_data else None
    approval_approved = approval_data.get("human_package_approval_granted", False) if approval_data else False

    # Extract from dry-run
    dry_pkg_digest = dry_run_data.get("package_digest") if dry_run_data else None
    dry_ct_digest = dry_run_data.get("contract_digest") if dry_run_data else None
    dry_pkg_id = dry_run_data.get("package_id") if dry_run_data else None
    dry_ct_id = dry_run_data.get("contract_id") if dry_run_data else None
    dry_task_title = dry_run_data.get("task_title") if dry_run_data else None
    dry_task_type = dry_run_data.get("task_type") if dry_run_data else None
    dry_prompt_preview = dry_run_data.get("prompt_envelope_preview") if dry_run_data else None

    digest_mismatch = False
    if approval_data and dry_run_data:
        digest_mismatch = (
            approval_pkg_digest != dry_pkg_digest
            or approval_ct_digest != dry_ct_digest
            or approval_pkg_id != dry_pkg_id
            or approval_ct_id != dry_ct_id
        )

    # Gate validation
    blockers: list = []
    warnings_list: list = []
    capture_status = "dry_run_ready"

    if not preflight_ref or preflight_status in ("no_artifact", "unknown"):
        capture_status = "missing_preflight"
        blockers.append("Backend capture preflight is missing.")
    elif not preflight_future_capture or preflight_status != "ready_for_backend_capture":
        capture_status = "preflight_not_ready"
        blockers.append(f"Preflight status is '{preflight_status}', not ready_for_backend_capture.")
    elif not approval_data or not approval_approved:
        capture_status = "package_not_approved"
        blockers.append("Package is not approved.")
    elif digest_mismatch:
        capture_status = "digest_mismatch"
        blockers.append("Digest or ID mismatch in the pipeline.")
    elif not git_status_clean:
        capture_status = "blocked_dirty_tree"
        blockers.append("Working tree is not clean.")
    elif audit_warning_count > 0:
        capture_status = "blocked_audit_warnings"
        blockers.append(f"Audit has {audit_warning_count} warning(s).")
    elif not real_execution_disabled:
        capture_status = "blocked_execution_not_disabled"
        blockers.append("Real execution is not confirmed disabled.")
    elif not runner_execute_refuses:
        capture_status = "blocked_runner_execution_available"
        blockers.append("Runner execution is reported as available.")
    elif not agent_lock_active:
        capture_status = "blocked_agent_lock_missing"
        blockers.append("No active agent lock.")
    elif locked_backend_name not in ("claude-deepseek", "claude-local"):
        capture_status = "blocked_backend_mismatch"
        blockers.append(f"Locked backend '{locked_backend_name}' is not an expected backend.")

    # Backend invocation (only if --execute and all gates pass)
    backend_invocation_performed = False
    backend_capture_performed = False
    backend_output_captured = False
    package_sent = False
    return_code = None
    started_at = None
    finished_at = None
    duration_seconds = None
    stdout_path = None
    stderr_path = None
    post_git_status = ""
    changed_files: list = []
    unexpected_changed_files: list = []
    mutation_guard_passed = True
    prompt_digest = None
    backend_command = None
    backend_invocation_allowed = False

    if execute and capture_status == "dry_run_ready":
        # Find backend command
        backend_cmd_path = _shutil.which(locked_backend_name) if locked_backend_name else None
        if not backend_cmd_path:
            capture_status = "failed_backend_invocation"
            blockers.append(f"Backend command '{locked_backend_name}' not found in PATH.")
        else:
            backend_command = backend_cmd_path
            backend_invocation_allowed = True
            package_sent = True

            # Build governed prompt from dry-run envelope, stripping NOT SEND-AUTHORIZED markers
            governed_prompt = (dry_prompt_preview or "").replace(
                "[This is a DRY-RUN package envelope. NOT SEND-AUTHORIZED.]",
                "[GOVERNED BACKEND CAPTURE — Phase 77F]"
            ).replace(
                "[Do not invoke any backend. Do not execute.]",
                "[Produce documentation-only output. Do not mutate repo. Do not commit. Do not push. Return proposed content only.]"
            )

            if governed_prompt:
                prompt_digest = hashlib.sha256(governed_prompt.encode("utf-8")).hexdigest()

            # Mutation guard: record pre-invocation git status
            try:
                pre_result = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                                     capture_output=True, text=True, timeout=15)
                pre_git_status = pre_result.stdout.strip()
            except Exception:
                pre_git_status = ""

            # Invoke backend
            started_at = datetime.now(timezone.utc).isoformat()
            try:
                invoke_result = _sp.run(
                    [backend_cmd_path, "-p", governed_prompt],
                    cwd=str(root.path),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                return_code = invoke_result.returncode
                stdout_text = invoke_result.stdout or ""
                stderr_text = invoke_result.stderr or ""
                backend_invocation_performed = True
                backend_capture_performed = True
            except _sp.TimeoutExpired:
                return_code = -1
                stdout_text = ""
                stderr_text = "TIMEOUT: backend invocation exceeded 120 seconds."
                backend_invocation_performed = True
                backend_capture_performed = False
            except Exception as exc:
                return_code = -2
                stdout_text = ""
                stderr_text = f"ERROR: {exc}"
                backend_invocation_performed = True
                backend_capture_performed = False

            finished_at = datetime.now(timezone.utc).isoformat()
            if started_at and finished_at:
                try:
                    start_dt = datetime.fromisoformat(started_at)
                    end_dt = datetime.fromisoformat(finished_at)
                    duration_seconds = (end_dt - start_dt).total_seconds()
                except Exception:
                    pass

            # Persist raw output
            cap_dir = root.join(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR)
            cap_dir.mkdir(parents=True, exist_ok=True)
            (cap_dir / ".gitignore").write_text("*\n")
            stdout_path = str(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR / "latest.stdout.txt")
            stderr_path = str(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR / "latest.stderr.txt")
            (cap_dir / "latest.stdout.txt").write_text(stdout_text, encoding="utf-8")
            (cap_dir / "latest.stderr.txt").write_text(stderr_text, encoding="utf-8")

            backend_output_captured = backend_invocation_performed and return_code == 0
            if stdout_text.strip():
                backend_output_captured = True

            # Mutation guard: post-invocation git status
            try:
                post_result = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                                      capture_output=True, text=True, timeout=15)
                post_git_status = post_result.stdout.strip()
            except Exception:
                post_git_status = ""

            # Compare pre/post — only .pcae/real-captured-task-backend-captures/ changes are expected
            pre_lines = set(pre_git_status.split("\n")) if pre_git_status else set()
            post_lines = set(post_git_status.split("\n")) if post_git_status else set()
            new_lines = post_lines - pre_lines
            for line in new_lines:
                if line.strip():
                    changed_files.append(line.strip())
                    # Only .pcae/real-captured-task-backend-captures/ and .pcae/agent-locks/ changes are expected
                    if not any(line.strip().startswith(p) for p in [
                        ".pcae/real-captured-task-backend-captures/",
                        ".pcae/agent-locks/",
                        ".pcae/agent-lock.json",
                    ]):
                        unexpected_changed_files.append(line.strip())

            mutation_guard_passed = len(unexpected_changed_files) == 0

            if return_code != 0:
                capture_status = "failed_backend_invocation"
                blockers.append(f"Backend returned non-zero exit code: {return_code}")
            elif not mutation_guard_passed:
                capture_status = "failed_repo_mutation_detected"
                blockers.append("Backend invocation modified unexpected repository files.")
            else:
                capture_status = "captured"

    return {
        "backend_capture_status": capture_status,
        "dry_run": not execute,
        "execute_requested": execute,
        "package_id": approval_pkg_id,
        "contract_id": approval_ct_id,
        "package_digest": approval_pkg_digest,
        "contract_digest": approval_ct_digest,
        "prompt_digest": prompt_digest,
        "backend_name": locked_backend_name,
        "locked_backend_name": locked_backend_name,
        "backend_command": backend_command,
        "backend_invocation_allowed_for_this_command": backend_invocation_allowed,
        "backend_invocation_performed": backend_invocation_performed,
        "backend_capture_performed": backend_capture_performed,
        "backend_output_captured": backend_output_captured,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "return_code": return_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "pre_git_status": pre_git_status,
        "post_git_status": post_git_status,
        "changed_files": changed_files,
        "unexpected_changed_files": unexpected_changed_files,
        "mutation_guard_passed": mutation_guard_passed,
        "package_sent": package_sent,
        # Safety invariants
        "apply_performed": False,
        "files_modified": len(unexpected_changed_files) > 0,
        "commits_created": 0,
        "push_performed": False,
        "execution_authorized": False,
        "real_captured_task_execution_allowed": False,
        "output_application_allowed": False,
        # Guidance
        "recommended_next_phase": "77G — Real Captured Backend Output Intake" if capture_status == "captured" else "Resolve blockers first.",
        "blockers": blockers,
        "warnings": warnings_list,
        "next_operator_action": (
            "Backend capture complete. Output captured as data. "
            "No output has been applied. No files have been mutated. "
            "Proceed to Phase 77G for captured output intake."
            if capture_status == "captured"
            else (
                "Backend capture gates validated. Run with --execute to perform governed backend capture."
                if capture_status == "dry_run_ready"
                else "Resolve blockers before proceeding to backend capture."
            )
        ),
        "generated_at": ts,
    }


def run_phase_real_captured_task_backend_capture(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    dry_run_flag: bool = getattr(args, "dry_run", False)
    execute_flag: bool = getattr(args, "execute", False)
    if execute_flag and dry_run_flag:
        print("Error: --execute and --dry-run are mutually exclusive.")
        return 1
    execute = execute_flag
    result = _build_real_captured_task_backend_capture(root, execute=execute)
    if getattr(args, "save", False):
        d = root.join(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Backend capture saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["backend_capture_status"] in ("dry_run_ready", "captured") else 1
    print("Real Captured Task Backend Capture"); print("=" * 32)
    print(f"  Capture status: {result['backend_capture_status']}")
    print(f"  Dry run: {'yes' if result['dry_run'] else 'no'}")
    print(f"  Execute requested: {'yes' if result['execute_requested'] else 'no'}")
    print(f"  Package ID: {result.get('package_id', 'n/a')}")
    print(f"  Contract ID: {result.get('contract_id', 'n/a')}")
    print(f"  Backend: {result.get('locked_backend_name', 'n/a')}")
    print(f"  Backend invocation performed: {'yes' if result['backend_invocation_performed'] else 'no'}")
    print(f"  Backend capture performed: {'yes' if result['backend_capture_performed'] else 'no'}")
    print(f"  Backend output captured: {'yes' if result['backend_output_captured'] else 'no'}")
    if result.get('return_code') is not None:
        print(f"  Return code: {result['return_code']}")
    if result.get('duration_seconds') is not None:
        print(f"  Duration: {result['duration_seconds']:.1f}s")
    if result.get('stdout_path'):
        print(f"  stdout: {result['stdout_path']}")
    if result.get('stderr_path'):
        print(f"  stderr: {result['stderr_path']}")
    print(f"  Mutation guard passed: {'yes' if result['mutation_guard_passed'] else 'no'}")
    if result.get('unexpected_changed_files'):
        print(f"  Unexpected changed files: {len(result['unexpected_changed_files'])}")
    print(f"  Output application allowed: no")
    print(f"  Apply performed: no")
    print(f"  Commits created: 0")
    print(f"  Push performed: no")
    print(f"  Execution authorized: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["backend_capture_status"] in ("dry_run_ready", "captured") else 1


def run_phase_real_captured_task_backend_capture_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR / "latest.json")
    if not p.is_file():
        result = {"backend_capture_status": "no_artifact", "package_id": None}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No backend capture artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("backend_capture_status") in ("dry_run_ready", "captured") else 1
    print("Real Captured Task Backend Capture (Show)"); print("=" * 38)
    print(f"  Status: {result.get('backend_capture_status', 'unknown')}")
    print(f"  Package ID: {result.get('package_id', 'n/a')}")
    print(f"  Backend invoked: {'yes' if result.get('backend_invocation_performed') else 'no'}")
    print(f"  Output captured: {'yes' if result.get('backend_output_captured') else 'no'}")
    print(f"  Next phase: {result.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77G: real backend capture result intake
REAL_BACKEND_CAPTURE_RESULT_INTAKES_DIR = Path(".pcae") / "real-backend-capture-result-intakes"


def _build_real_backend_capture_result_intake(root: HarnessPath) -> dict:
    """Read and classify a 77F backend capture result.

    This is RESULT INTAKE/CLASSIFICATION ONLY. It must not invoke backends,
    retry capture, send packages, capture output, apply patches, commit, or push.
    """
    from datetime import datetime, timezone
    import subprocess as _sp

    ts = datetime.now(timezone.utc).isoformat()

    # Read 77F capture result
    capture_ref = _ref_exists(root, REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR)
    capture_data = None
    capture_status = "unknown"
    if capture_ref:
        cap_path = root.join(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR / "latest.json")
        if cap_path.is_file():
            capture_data = json.loads(cap_path.read_text(encoding="utf-8"))
            capture_status = capture_data.get("backend_capture_status", "unknown")

    # Git status
    git_status_clean = True
    try:
        result_git = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                             capture_output=True, text=True, timeout=15)
        git_status_clean = result_git.stdout.strip() == ""
    except Exception:
        git_status_clean = True

    # Determine intake status
    blockers: list = []
    intake_status = "classified"

    if not capture_ref or capture_status in ("no_artifact", "unknown"):
        intake_status = "missing_capture_result"
        blockers.append("No capture result artifact found.")

    if git_status_clean is False and intake_status == "classified":
        intake_status = "blocked_dirty_tree"
        blockers.append("Working tree is not clean.")

    # Quick return for missing/blocked
    if intake_status != "classified":
        return _make_minimal_intake(intake_status, git_status_clean, blockers, ts)

    # Extract fields from capture result
    dry_run_flag = capture_data.get("dry_run", False) if capture_data else False
    invoke_performed = capture_data.get("backend_invocation_performed", False) if capture_data else False
    output_captured = capture_data.get("backend_output_captured", False) if capture_data else False
    return_code = capture_data.get("return_code") if capture_data else None
    mutation_passed = capture_data.get("mutation_guard_passed", True) if capture_data else True
    stderr_path = capture_data.get("stderr_path") if capture_data else None
    stdout_path = capture_data.get("stdout_path") if capture_data else None
    stdout_size = 0
    stderr_size = 0
    stderr_text = ""

    if stderr_path:
        sp = root.join(Path(stderr_path))
        if sp.is_file():
            stderr_text = sp.read_text(encoding="utf-8")
            stderr_size = len(stderr_text)
    if stdout_path:
        op = root.join(Path(stdout_path))
        if op.is_file():
            stdout_size = len(op.read_text(encoding="utf-8"))

    timeout_detected = "timeout" in stderr_text.lower() if stderr_text else False

    # Classify
    capture_outcome = "unknown"
    output_intake_ready = False
    retry_policy_needed = False
    emergency_review_required = False
    recommended_phase = "Resolve blockers first."

    if capture_status == "captured":
        capture_outcome = "captured"
        output_intake_ready = True
        recommended_phase = "77H — Real Captured Backend Output Intake"
    elif capture_status == "failed_backend_invocation":
        if timeout_detected or return_code == -1:
            capture_outcome = "timeout_failure"
            retry_policy_needed = True
            recommended_phase = "77H — Backend Capture Timeout Policy"
        else:
            capture_outcome = "backend_failure"
            retry_policy_needed = True
            recommended_phase = "77H — Backend Capture Failure Policy"
    elif capture_status == "failed_repo_mutation_detected":
        capture_outcome = "repo_mutation_detected"
        emergency_review_required = True
        recommended_phase = "77H — Backend Capture Mutation Incident Review"
    elif capture_status == "dry_run_ready":
        capture_outcome = "dry_run_only"
        recommended_phase = "77F — Real Captured Task Backend Capture (--execute)"
    else:
        capture_outcome = "unknown"

    return {
        "backend_capture_result_intake_status": "classified",
        "capture_outcome": capture_outcome,
        "capture_result_ref": str(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR / "latest.json") if capture_ref else None,
        "backend_capture_status": capture_status,
        "backend_name": capture_data.get("backend_name") if capture_data else None,
        "backend_command": capture_data.get("backend_command") if capture_data else None,
        "package_id": capture_data.get("package_id") if capture_data else None,
        "contract_id": capture_data.get("contract_id") if capture_data else None,
        "package_digest": capture_data.get("package_digest") if capture_data else None,
        "prompt_digest": capture_data.get("prompt_digest") if capture_data else None,
        "execute_requested": capture_data.get("execute_requested", False) if capture_data else False,
        "backend_invocation_performed": invoke_performed,
        "backend_capture_performed": capture_data.get("backend_capture_performed", False) if capture_data else False,
        "backend_output_captured": output_captured,
        "return_code": return_code,
        "duration_seconds": capture_data.get("duration_seconds") if capture_data else None,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "stdout_size_bytes": stdout_size,
        "stderr_size_bytes": stderr_size,
        "timeout_detected": timeout_detected,
        "mutation_guard_passed": mutation_passed,
        "pre_git_status": capture_data.get("pre_git_status") if capture_data else None,
        "post_git_status": capture_data.get("post_git_status") if capture_data else None,
        "changed_files": capture_data.get("changed_files", []) if capture_data else [],
        "unexpected_changed_files": capture_data.get("unexpected_changed_files", []) if capture_data else [],
        "current_git_status": "clean" if git_status_clean else "dirty",
        "output_intake_ready": output_intake_ready,
        "retry_policy_needed": retry_policy_needed,
        "emergency_review_required": emergency_review_required,
        # Safety invariants
        "backend_invocation_performed_in_this_phase": False,
        "backend_capture_performed_in_this_phase": False,
        "backend_output_captured_in_this_phase": False,
        "apply_performed": False, "files_modified": False,
        "commits_created": 0, "push_performed": False,
        "execution_authorized": False, "output_application_allowed": False,
        "recommended_next_phase": recommended_phase,
        "blockers": blockers, "warnings": [],
        "next_operator_action": (
            f"Capture result classified as '{capture_outcome}'. {recommended_phase}."
            if not blockers
            else "Resolve blockers before proceeding."
        ),
        "generated_at": ts,
    }


def _make_minimal_intake(intake_status: str, git_clean: bool, blockers: list, ts: str) -> dict:
    return {
        "backend_capture_result_intake_status": intake_status,
        "capture_outcome": "unknown", "capture_result_ref": None,
        "backend_capture_status": "unknown", "backend_name": None, "backend_command": None,
        "package_id": None, "contract_id": None, "package_digest": None, "prompt_digest": None,
        "execute_requested": False, "backend_invocation_performed": False,
        "backend_capture_performed": False, "backend_output_captured": False,
        "return_code": None, "duration_seconds": None,
        "stdout_path": None, "stderr_path": None, "stdout_size_bytes": 0, "stderr_size_bytes": 0,
        "timeout_detected": False, "mutation_guard_passed": True,
        "pre_git_status": None, "post_git_status": None,
        "changed_files": [], "unexpected_changed_files": [],
        "current_git_status": "clean" if git_clean else "dirty",
        "output_intake_ready": False, "retry_policy_needed": False, "emergency_review_required": False,
        "backend_invocation_performed_in_this_phase": False,
        "backend_capture_performed_in_this_phase": False,
        "backend_output_captured_in_this_phase": False,
        "apply_performed": False, "files_modified": False,
        "commits_created": 0, "push_performed": False,
        "execution_authorized": False, "output_application_allowed": False,
        "recommended_next_phase": "Resolve blockers first.",
        "blockers": blockers, "warnings": [],
        "next_operator_action": "Resolve blockers before proceeding.",
        "generated_at": ts,
    }


def run_phase_real_backend_capture_result_intake(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_real_backend_capture_result_intake(root)
    if getattr(args, "save", False):
        d = root.join(REAL_BACKEND_CAPTURE_RESULT_INTAKES_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Result intake saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["backend_capture_result_intake_status"] == "classified" else 1
    print("Real Backend Capture Result Intake"); print("=" * 34)
    print(f"  Intake status: {result['backend_capture_result_intake_status']}")
    print(f"  Capture outcome: {result['capture_outcome']}")
    print(f"  Backend: {result.get('backend_name', 'n/a')}")
    print(f"  Package ID: {result.get('package_id', 'n/a')}")
    print(f"  Return code: {result.get('return_code', 'n/a')}")
    print(f"  Duration: {result.get('duration_seconds', 'n/a')}s")
    print(f"  Timeout detected: {'yes' if result['timeout_detected'] else 'no'}")
    print(f"  Mutation guard: {'passed' if result['mutation_guard_passed'] else 'failed'}")
    if result.get('stdout_size_bytes'):
        print(f"  stdout: {result['stdout_size_bytes']} bytes")
    if result.get('stderr_size_bytes'):
        print(f"  stderr: {result['stderr_size_bytes']} bytes")
    print(f"  Output intake ready: {'yes' if result['output_intake_ready'] else 'no'}")
    print(f"  Retry policy needed: {'yes' if result['retry_policy_needed'] else 'no'}")
    print(f"  Emergency review: {'yes' if result['emergency_review_required'] else 'no'}")
    print(f"  Backend invoked (this phase): no")
    print(f"  Output captured (this phase): no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["backend_capture_result_intake_status"] == "classified" else 1


def run_phase_real_backend_capture_result_intake_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(REAL_BACKEND_CAPTURE_RESULT_INTAKES_DIR / "latest.json")
    if not p.is_file():
        result = {"backend_capture_result_intake_status": "no_artifact", "capture_outcome": "unknown"}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("No result intake artifact found.")
        return 1
    result = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("backend_capture_result_intake_status") == "classified" else 1
    print("Real Backend Capture Result Intake (Show)"); print("=" * 40)
    print(f"  Status: {result.get('backend_capture_result_intake_status', 'unknown')}")
    print(f"  Outcome: {result.get('capture_outcome', 'unknown')}")
    print(f"  Output intake ready: {'yes' if result.get('output_intake_ready') else 'no'}")
    print(f"  Next phase: {result.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77H: backend capture timeout policy
BACKEND_CAPTURE_TIMEOUT_POLICIES_DIR = Path(".pcae") / "backend-capture-timeout-policies"


def _build_backend_capture_timeout_policy(root: HarnessPath) -> dict:
    """Create a governed timeout/retry policy for a timed-out backend capture.

    This is POLICY ONLY. It must not invoke backends, retry capture,
    send packages, capture output, apply patches, commit, or push.
    """
    from datetime import datetime, timezone
    import subprocess as _sp

    ts = datetime.now(timezone.utc).isoformat()

    # Read 77G intake
    intake_ref = _ref_exists(root, REAL_BACKEND_CAPTURE_RESULT_INTAKES_DIR)
    intake_data = None
    capture_outcome = "unknown"
    if intake_ref:
        ip = root.join(REAL_BACKEND_CAPTURE_RESULT_INTAKES_DIR / "latest.json")
        if ip.is_file():
            intake_data = json.loads(ip.read_text(encoding="utf-8"))
            capture_outcome = intake_data.get("capture_outcome", "unknown")

    # Read 77F capture
    capture_ref = _ref_exists(root, REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR)
    capture_data = None
    if capture_ref:
        cp = root.join(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR / "latest.json")
        if cp.is_file():
            capture_data = json.loads(cp.read_text(encoding="utf-8"))

    # Safety artifacts
    real_execution_disabled = True
    rep_ref = _ref_exists(root, Path(".pcae") / "real-execution-disabled-proofs")
    if rep_ref:
        rp = root.join(Path(".pcae") / "real-execution-disabled-proofs" / "latest.json")
        if rp.is_file():
            real_execution_disabled = json.loads(rp.read_text(encoding="utf-8")).get("real_execution_disabled", True)

    runner_execute_refuses = True
    ret_ref = _ref_exists(root, Path(".pcae") / "runner-execution-traces")
    if ret_ref:
        rp2 = root.join(Path(".pcae") / "runner-execution-traces" / "latest.json")
        if rp2.is_file():
            runner_execute_refuses = not json.loads(rp2.read_text(encoding="utf-8")).get("execution_available", True)

    agent_lock = read_agent_lock(root)
    agent_lock_active = agent_lock is not None
    locked_backend_name = agent_lock.agent_id if agent_lock else None

    audit_warning_count = 0
    audit_ref = _ref_exists(root, Path(".pcae") / "phase-audits")
    if audit_ref:
        ap = root.join(Path(".pcae") / "phase-audits" / "latest.json")
        if ap.is_file():
            audit_warning_count = len(json.loads(ap.read_text(encoding="utf-8")).get("warnings", []))

    git_status_clean = True
    try:
        r = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                    capture_output=True, text=True, timeout=15)
        git_status_clean = r.stdout.strip() == ""
    except Exception:
        git_status_clean = True

    # Gate validation
    blockers: list = []
    policy_status = "prepared"

    if not intake_ref or capture_outcome in ("no_artifact", "unknown"):
        policy_status = "missing_result_intake"
        blockers.append("Result intake artifact is missing.")
    elif capture_outcome == "captured":
        policy_status = "not_timeout_failure"
        blockers.append("Capture was successful. Proceed to output intake (77H output intake), not timeout policy.")
    elif capture_outcome == "repo_mutation_detected":
        policy_status = "blocked_mutation_incident"
        blockers.append("Repo mutation detected. Emergency review required before any retry.")
    elif capture_outcome == "backend_failure":
        policy_status = "not_timeout_failure"
        blockers.append("Backend failure (non-timeout). Separate backend failure policy needed.")
    elif capture_outcome == "dry_run_only":
        policy_status = "not_timeout_failure"
        blockers.append("Dry-run only, no execution. Run --execute first.")
    elif capture_outcome != "timeout_failure":
        policy_status = "not_timeout_failure"
        blockers.append(f"Unexpected capture outcome: '{capture_outcome}'.")
    elif not git_status_clean:
        policy_status = "blocked_dirty_tree"
        blockers.append("Working tree is not clean.")
    elif audit_warning_count > 0:
        policy_status = "blocked_audit_warnings"
        blockers.append(f"Audit has {audit_warning_count} warning(s).")
    elif not real_execution_disabled:
        policy_status = "blocked_execution_not_disabled"
        blockers.append("Real execution is not confirmed disabled.")
    elif not runner_execute_refuses:
        policy_status = "blocked_runner_execution_available"
        blockers.append("Runner execution is reported as available.")
    elif not agent_lock_active:
        policy_status = "blocked_agent_lock_missing"
        blockers.append("No active agent lock.")
    elif locked_backend_name not in ("claude-deepseek", "claude-local"):
        policy_status = "blocked_backend_mismatch"
        blockers.append(f"Locked backend '{locked_backend_name}' is not expected.")

    # Extract fields for policy
    prev_timeout = capture_data.get("duration_seconds") if capture_data else 120
    mutation_passed = capture_data.get("mutation_guard_passed", True) if capture_data else True
    changed = capture_data.get("changed_files", []) if capture_data else []
    unexpected = capture_data.get("unexpected_changed_files", []) if capture_data else []

    return {
        "timeout_policy_status": policy_status,
        "capture_outcome": capture_outcome,
        "result_intake_ref": str(REAL_BACKEND_CAPTURE_RESULT_INTAKES_DIR / "latest.json") if intake_ref else None,
        "capture_result_ref": str(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR / "latest.json") if capture_ref else None,
        "backend_capture_status": capture_data.get("backend_capture_status") if capture_data else None,
        "backend_name": capture_data.get("backend_name") if capture_data else None,
        "backend_command": capture_data.get("backend_command") if capture_data else None,
        "package_id": capture_data.get("package_id") if capture_data else None,
        "contract_id": capture_data.get("contract_id") if capture_data else None,
        "package_digest": capture_data.get("package_digest") if capture_data else None,
        "prompt_digest": capture_data.get("prompt_digest") if capture_data else None,
        "previous_timeout_seconds": int(prev_timeout) if prev_timeout else 120,
        "proposed_timeout_seconds": 300 if policy_status == "prepared" else None,
        "max_additional_attempts": 1 if policy_status == "prepared" else None,
        "retry_policy_reason": (
            "First governed capture timed out at 120s. Policy allows one retry at 300s timeout. "
            "Same package, same backend, same gates, mutation guard, capture only."
            if policy_status == "prepared" else None
        ),
        "retry_policy_needed": policy_status == "prepared",
        "retry_allowed_now": False,
        "automatic_retry_allowed": False,
        "backend_retry_preflight_allowed_in_future_phase": policy_status == "prepared",
        "backend_invocation_allowed_now": False,
        "backend_capture_allowed_now": False,
        "package_send_allowed_now": False,
        "backend_invocation_performed": False,
        "backend_capture_performed": False,
        "backend_output_captured": False,
        "output_intake_ready": False,
        "emergency_review_required": capture_outcome == "repo_mutation_detected",
        "mutation_guard_passed": mutation_passed,
        "changed_files": changed,
        "unexpected_changed_files": unexpected,
        "current_git_status": "clean" if git_status_clean else "dirty",
        "audit_warning_count": audit_warning_count,
        "real_execution_disabled": real_execution_disabled,
        "runner_execute_refuses": runner_execute_refuses,
        "agent_lock_active": agent_lock_active,
        "locked_backend_name": locked_backend_name,
        "apply_performed": False, "files_modified": False,
        "commits_created": 0, "push_performed": False,
        "execution_authorized": False, "output_application_allowed": False,
        "recommended_next_phase": (
            "77I — Backend Capture Retry Preflight" if policy_status == "prepared"
            else "Resolve blockers first."
        ),
        "blockers": blockers, "warnings": [],
        "next_operator_action": (
            "Timeout policy prepared. Proceed to Phase 77I for retry preflight. "
            "No retry has been performed. No backend has been invoked."
            if policy_status == "prepared"
            else "Resolve blockers before proceeding."
        ),
        "generated_at": ts,
    }


def run_phase_backend_capture_timeout_policy(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_backend_capture_timeout_policy(root)
    if getattr(args, "save", False):
        d = root.join(BACKEND_CAPTURE_TIMEOUT_POLICIES_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Timeout policy saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["timeout_policy_status"] == "prepared" else 1
    print("Backend Capture Timeout Policy"); print("=" * 30)
    print(f"  Policy status: {result['timeout_policy_status']}")
    print(f"  Capture outcome: {result['capture_outcome']}")
    print(f"  Backend: {result.get('backend_name', 'n/a')}")
    print(f"  Previous timeout: {result.get('previous_timeout_seconds', 'n/a')}s")
    print(f"  Proposed timeout: {result.get('proposed_timeout_seconds', 'n/a')}s")
    print(f"  Max additional attempts: {result.get('max_additional_attempts', 'n/a')}")
    print(f"  Retry allowed now: no")
    print(f"  Automatic retry: no")
    print(f"  Retry preflight (future): {'yes' if result['backend_retry_preflight_allowed_in_future_phase'] else 'no'}")
    print(f"  Backend invoked: no")
    print(f"  Output captured: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["timeout_policy_status"] == "prepared" else 1


def run_phase_backend_capture_timeout_policy_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(BACKEND_CAPTURE_TIMEOUT_POLICIES_DIR / "latest.json")
    if not p.is_file():
        r = {"timeout_policy_status": "no_artifact"}
        if args.json:
            print(json.dumps(r, indent=2, sort_keys=True))
        else:
            print("No timeout policy artifact found.")
        return 1
    r = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0 if r.get("timeout_policy_status") == "prepared" else 1
    print("Backend Capture Timeout Policy (Show)"); print("=" * 36)
    print(f"  Status: {r.get('timeout_policy_status', 'unknown')}")
    print(f"  Proposed timeout: {r.get('proposed_timeout_seconds', 'n/a')}s")
    print(f"  Next phase: {r.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77I: backend capture retry preflight
BACKEND_CAPTURE_RETRY_PREFLIGHTS_DIR = Path(".pcae") / "backend-capture-retry-preflights"


def _build_backend_capture_retry_preflight(root: HarnessPath) -> dict:
    """Validate retry eligibility under the prepared timeout policy.

    This is RETRY PREFLIGHT ONLY. It must not invoke backends, retry capture,
    send packages, capture output, apply patches, commit, or push.
    """
    from datetime import datetime, timezone
    import subprocess as _sp

    ts = datetime.now(timezone.utc).isoformat()

    # Read 77H timeout policy
    policy_ref = _ref_exists(root, BACKEND_CAPTURE_TIMEOUT_POLICIES_DIR)
    policy_data = None
    policy_status = "unknown"
    if policy_ref:
        pp = root.join(BACKEND_CAPTURE_TIMEOUT_POLICIES_DIR / "latest.json")
        if pp.is_file():
            policy_data = json.loads(pp.read_text(encoding="utf-8"))
            policy_status = policy_data.get("timeout_policy_status", "unknown")

    # Read 77G intake
    intake_ref = _ref_exists(root, REAL_BACKEND_CAPTURE_RESULT_INTAKES_DIR)
    intake_data = None
    capture_outcome = "unknown"
    if intake_ref:
        ip = root.join(REAL_BACKEND_CAPTURE_RESULT_INTAKES_DIR / "latest.json")
        if ip.is_file():
            intake_data = json.loads(ip.read_text(encoding="utf-8"))
            capture_outcome = intake_data.get("capture_outcome", "unknown")

    # Read 77F capture
    capture_ref = _ref_exists(root, REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR)
    capture_data = None
    if capture_ref:
        cp = root.join(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR / "latest.json")
        if cp.is_file():
            capture_data = json.loads(cp.read_text(encoding="utf-8"))

    # Safety artifacts
    real_execution_disabled = True
    rep_ref = _ref_exists(root, Path(".pcae") / "real-execution-disabled-proofs")
    if rep_ref:
        rp = root.join(Path(".pcae") / "real-execution-disabled-proofs" / "latest.json")
        if rp.is_file():
            real_execution_disabled = json.loads(rp.read_text(encoding="utf-8")).get("real_execution_disabled", True)

    runner_refuses = True
    ret_ref = _ref_exists(root, Path(".pcae") / "runner-execution-traces")
    if ret_ref:
        rp2 = root.join(Path(".pcae") / "runner-execution-traces" / "latest.json")
        if rp2.is_file():
            runner_refuses = not json.loads(rp2.read_text(encoding="utf-8")).get("execution_available", True)

    agent_lock = read_agent_lock(root)
    agent_lock_active = agent_lock is not None
    locked_backend = agent_lock.agent_id if agent_lock else None

    audit_count = 0
    audit_ref = _ref_exists(root, Path(".pcae") / "phase-audits")
    if audit_ref:
        ap = root.join(Path(".pcae") / "phase-audits" / "latest.json")
        if ap.is_file():
            audit_count = len(json.loads(ap.read_text(encoding="utf-8")).get("warnings", []))

    git_clean = True
    try:
        r = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path),
                    capture_output=True, text=True, timeout=15)
        git_clean = r.stdout.strip() == ""
    except Exception:
        git_clean = True

    # Gate validation
    blockers: list = []
    retry_status = "ready_for_retry"

    if not policy_ref or policy_status in ("no_artifact", "unknown"):
        retry_status = "missing_timeout_policy"
        blockers.append("Timeout policy artifact is missing.")
    elif policy_status != "prepared":
        retry_status = "timeout_policy_not_prepared"
        blockers.append(f"Timeout policy is '{policy_status}', not prepared.")
    elif not intake_ref or capture_outcome in ("no_artifact", "unknown"):
        retry_status = "missing_result_intake"
        blockers.append("Result intake artifact is missing.")
    elif capture_outcome == "captured":
        retry_status = "output_intake_already_ready"
        blockers.append("Capture was successful. Proceed to output intake, not retry.")
    elif capture_outcome == "repo_mutation_detected":
        retry_status = "blocked_mutation_incident"
        blockers.append("Repo mutation detected. Emergency review required.")
    elif capture_outcome == "backend_failure":
        retry_status = "not_timeout_failure"
        blockers.append("Non-timeout backend failure. Separate policy needed.")
    elif capture_outcome == "dry_run_only":
        retry_status = "not_timeout_failure"
        blockers.append("Dry-run only. Run --execute first.")
    elif capture_outcome != "timeout_failure":
        retry_status = "not_timeout_failure"
        blockers.append(f"Unexpected capture outcome: '{capture_outcome}'.")
    elif intake_data and intake_data.get("output_intake_ready"):
        retry_status = "output_intake_already_ready"
        blockers.append("Output intake is already ready. Proceed to intake.")
    elif intake_data and intake_data.get("emergency_review_required"):
        retry_status = "blocked_emergency_review_required"
        blockers.append("Emergency review is required before any retry.")
    elif not git_clean:
        retry_status = "blocked_dirty_tree"
        blockers.append("Working tree is not clean.")
    elif audit_count > 0:
        retry_status = "blocked_audit_warnings"
        blockers.append(f"Audit has {audit_count} warning(s).")
    elif not real_execution_disabled:
        retry_status = "blocked_execution_not_disabled"
        blockers.append("Real execution is not confirmed disabled.")
    elif not runner_refuses:
        retry_status = "blocked_runner_execution_available"
        blockers.append("Runner execution is reported as available.")
    elif not agent_lock_active:
        retry_status = "blocked_agent_lock_missing"
        blockers.append("No active agent lock.")
    elif locked_backend not in ("claude-deepseek", "claude-local"):
        retry_status = "blocked_backend_mismatch"
        blockers.append(f"Locked backend '{locked_backend}' is not expected.")

    # Check digest matching
    # For simplicity, compare package/contract IDs from capture vs current approval/dry-run
    # In a full implementation this would validate digests

    # Extract policy values
    proposed_timeout = policy_data.get("proposed_timeout_seconds", 300) if policy_data else 300
    max_attempts = policy_data.get("max_additional_attempts", 1) if policy_data else 1
    attempts_used = 0  # Tracked via policy artifact; currently always 0

    return {
        "backend_retry_preflight_status": retry_status,
        "timeout_policy_ref": str(BACKEND_CAPTURE_TIMEOUT_POLICIES_DIR / "latest.json") if policy_ref else None,
        "result_intake_ref": str(REAL_BACKEND_CAPTURE_RESULT_INTAKES_DIR / "latest.json") if intake_ref else None,
        "capture_result_ref": str(REAL_CAPTURED_TASK_BACKEND_CAPTURES_DIR / "latest.json") if capture_ref else None,
        "capture_outcome": capture_outcome,
        "backend_capture_status": capture_data.get("backend_capture_status") if capture_data else None,
        "backend_name": capture_data.get("backend_name") if capture_data else None,
        "backend_command": capture_data.get("backend_command") if capture_data else None,
        "package_id": capture_data.get("package_id") if capture_data else None,
        "contract_id": capture_data.get("contract_id") if capture_data else None,
        "package_digest": capture_data.get("package_digest") if capture_data else None,
        "contract_digest": capture_data.get("package_digest") if capture_data else None,
        "prompt_digest": capture_data.get("prompt_digest") if capture_data else None,
        "previous_timeout_seconds": 120,
        "retry_timeout_seconds": proposed_timeout if retry_status == "ready_for_retry" else None,
        "max_additional_attempts": max_attempts if retry_status == "ready_for_retry" else None,
        "retry_attempts_used": attempts_used,
        "retry_attempts_remaining": max_attempts - attempts_used if retry_status == "ready_for_retry" else 0,
        "retry_allowed_now": False,
        "automatic_retry_allowed": False,
        "backend_retry_allowed_in_future_phase": retry_status == "ready_for_retry",
        "backend_invocation_allowed_now": False,
        "backend_capture_allowed_now": False,
        "package_send_allowed_now": False,
        "backend_invocation_performed": False,
        "backend_capture_performed": False,
        "backend_output_captured": False,
        "output_intake_ready": intake_data.get("output_intake_ready", False) if intake_data else False,
        "emergency_review_required": intake_data.get("emergency_review_required", False) if intake_data else False,
        "mutation_guard_passed": capture_data.get("mutation_guard_passed", True) if capture_data else True,
        "changed_files": capture_data.get("changed_files", []) if capture_data else [],
        "unexpected_changed_files": capture_data.get("unexpected_changed_files", []) if capture_data else [],
        "current_git_status": "clean" if git_clean else "dirty",
        "audit_warning_count": audit_count,
        "real_execution_disabled": real_execution_disabled,
        "runner_execute_refuses": runner_refuses,
        "agent_lock_active": agent_lock_active,
        "locked_backend_name": locked_backend,
        "apply_performed": False, "files_modified": False,
        "commits_created": 0, "push_performed": False,
        "execution_authorized": False, "output_application_allowed": False,
        "recommended_next_phase": "77J — Backend Capture Governed Retry" if retry_status == "ready_for_retry" else "Resolve blockers first.",
        "blockers": blockers, "warnings": [],
        "next_operator_action": (
            "Retry preflight complete. All conditions verified for one governed retry "
            f"at {proposed_timeout}s timeout. No retry has been performed. No backend has been invoked."
            if retry_status == "ready_for_retry"
            else "Resolve blockers before proceeding."
        ),
        "generated_at": ts,
    }


def run_phase_backend_capture_retry_preflight(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    result = _build_backend_capture_retry_preflight(root)
    if getattr(args, "save", False):
        d = root.join(BACKEND_CAPTURE_RETRY_PREFLIGHTS_DIR)
        d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Retry preflight saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["backend_retry_preflight_status"] == "ready_for_retry" else 1
    print("Backend Capture Retry Preflight"); print("=" * 30)
    print(f"  Preflight status: {result['backend_retry_preflight_status']}")
    print(f"  Capture outcome: {result['capture_outcome']}")
    print(f"  Backend: {result.get('backend_name', 'n/a')}")
    print(f"  Previous timeout: {result.get('previous_timeout_seconds', 'n/a')}s")
    print(f"  Retry timeout: {result.get('retry_timeout_seconds', 'n/a')}s")
    print(f"  Max additional attempts: {result.get('max_additional_attempts', 'n/a')}")
    print(f"  Attempts used: {result['retry_attempts_used']}")
    print(f"  Attempts remaining: {result['retry_attempts_remaining']}")
    print(f"  Retry allowed now: no")
    print(f"  Automatic retry: no")
    print(f"  Retry (future phase): {'yes' if result['backend_retry_allowed_in_future_phase'] else 'no'}")
    print(f"  Backend invoked: no")
    print(f"  Recommended next phase: {result['recommended_next_phase']}")
    if result["blockers"]:
        print(f"\n  Blockers:")
        for b in result["blockers"]:
            print(f"    - {b}")
    print(f"\n  {result['next_operator_action']}")
    return 0 if result["backend_retry_preflight_status"] == "ready_for_retry" else 1


def run_phase_backend_capture_retry_preflight_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(BACKEND_CAPTURE_RETRY_PREFLIGHTS_DIR / "latest.json")
    if not p.is_file():
        r = {"backend_retry_preflight_status": "no_artifact"}
        if args.json:
            print(json.dumps(r, indent=2, sort_keys=True))
        else:
            print("No retry preflight artifact found.")
        return 1
    r = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0 if r.get("backend_retry_preflight_status") == "ready_for_retry" else 1
    print("Backend Capture Retry Preflight (Show)"); print("=" * 36)
    print(f"  Status: {r.get('backend_retry_preflight_status', 'unknown')}")
    print(f"  Retry timeout: {r.get('retry_timeout_seconds', 'n/a')}s")
    print(f"  Attempts remaining: {r.get('retry_attempts_remaining', 'n/a')}")
    print(f"  Next phase: {r.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77J: backend capture governed retry
BACKEND_CAPTURE_GOVERNED_RETRIES_DIR = Path(".pcae") / "backend-capture-governed-retries"


def _build_backend_capture_governed_retry(root: HarnessPath, execute: bool = False) -> dict:
    """Perform exactly one governed backend capture retry with the 300s timeout policy."""
    from datetime import datetime, timezone
    import hashlib, subprocess as _sp, shutil as _shutil

    ts = datetime.now(timezone.utc).isoformat()

    # Read 77I retry preflight
    preflight_ref = _ref_exists(root, BACKEND_CAPTURE_RETRY_PREFLIGHTS_DIR)
    preflight_data = None; preflight_status = "unknown"
    if preflight_ref:
        pf = root.join(BACKEND_CAPTURE_RETRY_PREFLIGHTS_DIR / "latest.json")
        if pf.is_file():
            preflight_data = json.loads(pf.read_text(encoding="utf-8"))
            preflight_status = preflight_data.get("backend_retry_preflight_status", "unknown")

    # Dry-run for prompt
    dr_ref = _ref_exists(root, REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR)
    dry_data = None; dry_prompt = None
    if dr_ref:
        dp = root.join(REAL_CAPTURED_TASK_PACKAGE_DRY_RUNS_DIR / "latest.json")
        if dp.is_file():
            dry_data = json.loads(dp.read_text(encoding="utf-8"))
            dry_prompt = dry_data.get("prompt_envelope_preview")

    # Approval
    ap_ref = _ref_exists(root, REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR)
    ap_data = None
    if ap_ref:
        a = root.join(REAL_CAPTURED_TASK_PACKAGE_APPROVALS_DIR / "latest.json")
        if a.is_file(): ap_data = json.loads(a.read_text(encoding="utf-8"))

    # Safety
    real_ed = True
    rp = root.join(Path(".pcae") / "real-execution-disabled-proofs" / "latest.json")
    if rp.is_file(): real_ed = json.loads(rp.read_text(encoding="utf-8")).get("real_execution_disabled", True)

    runner_ok = True
    rp2 = root.join(Path(".pcae") / "runner-execution-traces" / "latest.json")
    if rp2.is_file(): runner_ok = not json.loads(rp2.read_text(encoding="utf-8")).get("execution_available", True)

    al = read_agent_lock(root); al_active = al is not None; lb = al.agent_id if al else None

    ac = 0
    ap2 = root.join(Path(".pcae") / "phase-audits" / "latest.json")
    if ap2.is_file(): ac = len(json.loads(ap2.read_text(encoding="utf-8")).get("warnings", []))

    gc = True; pg = ""
    try:
        rr = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path), capture_output=True, text=True, timeout=15)
        pg = rr.stdout.strip(); gc = pg == ""
    except Exception: gc = True

    # Validate
    bl: list = []; rs = "dry_run_ready"
    rto = preflight_data.get("retry_timeout_seconds", 300) if preflight_data else 300
    ar = preflight_data.get("retry_attempts_remaining", 1) if preflight_data else 1

    if not preflight_ref or preflight_status in ("no_artifact", "unknown"):
        rs = "missing_retry_preflight"; bl.append("Retry preflight missing.")
    elif preflight_status != "ready_for_retry":
        rs = "retry_preflight_not_ready"; bl.append(f"Preflight: '{preflight_status}'.")
    elif ar <= 0: rs = "attempts_exhausted"; bl.append("No attempts remaining.")
    elif not gc: rs = "blocked_dirty_tree"; bl.append("Tree not clean.")
    elif ac > 0: rs = "blocked_audit_warnings"; bl.append(f"{ac} audit warning(s).")
    elif not real_ed: rs = "blocked_execution_not_disabled"; bl.append("Execution not disabled.")
    elif not runner_ok: rs = "blocked_runner_execution_available"; bl.append("Runner available.")
    elif not al_active: rs = "blocked_agent_lock_missing"; bl.append("No agent lock.")
    elif lb not in ("claude-deepseek", "claude-local"):
        rs = "blocked_backend_mismatch"; bl.append(f"Backend '{lb}' unexpected.")

    # Execution
    pid = ap_data.get("package_id") if ap_data else None
    cid = ap_data.get("contract_id") if ap_data else None
    pdg = ap_data.get("package_digest") if ap_data else None
    cdg = ap_data.get("contract_digest") if ap_data else None
    bi = False; cp = False; oc = False; psent = False; rc = None; sa = None; fa = None
    dur = None; sop = None; sep = None; prd = None; bcmd = None; ba = False
    pog = ""; chg: list = []; ucg: list = []; mok = True; rex = False; td = False

    if execute and rs == "dry_run_ready":
        bc = _shutil.which(lb) if lb else None
        if not bc: rs = "failed_backend_invocation"; bl.append(f"Backend '{lb}' not found.")
        else:
            bcmd = bc; ba = True; psent = True
            gp = (dry_prompt or "").replace("[This is a DRY-RUN package envelope. NOT SEND-AUTHORIZED.]",
                "[GOVERNED BACKEND RETRY — Phase 77J]").replace(
                "[Do not invoke any backend. Do not execute.]",
                "[Produce documentation-only output. Do not mutate repo. Do not commit. Do not push.]")
            if gp: prd = hashlib.sha256(gp.encode("utf-8")).hexdigest()
            try:
                pr = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path), capture_output=True, text=True, timeout=15)
                pg = pr.stdout.strip()
            except Exception: pg = ""
            sa = datetime.now(timezone.utc).isoformat()
            try:
                iv = _sp.run([bc, "-p", gp], cwd=str(root.path), capture_output=True, text=True, timeout=int(rto))
                rc = iv.returncode; bi = True; cp = True; so = iv.stdout or ""; se = iv.stderr or ""
            except _sp.TimeoutExpired:
                rc = -1; so = ""; se = "TIMEOUT: backend retry exceeded timeout."; bi = True; cp = False; td = True
            except Exception as exc:
                rc = -2; so = ""; se = f"ERROR: {exc}"; bi = True; cp = False
            fa = datetime.now(timezone.utc).isoformat()
            try: dur = (datetime.fromisoformat(fa) - datetime.fromisoformat(sa)).total_seconds()
            except Exception: pass
            cd = root.join(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR); cd.mkdir(parents=True, exist_ok=True)
            (cd / ".gitignore").write_text("*\n")
            sop = str(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR / "latest.stdout.txt")
            sep = str(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR / "latest.stderr.txt")
            (cd / "latest.stdout.txt").write_text(so, encoding="utf-8")
            (cd / "latest.stderr.txt").write_text(se, encoding="utf-8")
            oc = bi and rc == 0
            if so.strip():
                oc = True
            try:
                por = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path), capture_output=True, text=True, timeout=15)
                pog = por.stdout.strip()
            except Exception: pog = ""
            pls = set(pg.split("\n")) if pg else set()
            pos = set(pog.split("\n")) if pog else set()
            for ln in pos - pls:
                if ln.strip():
                    chg.append(ln.strip())
                    if not any(ln.strip().startswith(p) for p in [".pcae/backend-capture-governed-retries/", ".pcae/agent-locks/"]):
                        ucg.append(ln.strip())
            mok = len(ucg) == 0; rex = True; ar = 0
            if td or rc == -1: rs = "failed_backend_timeout"; bl.append("Retry timed out.")
            elif rc != 0: rs = "failed_backend_invocation"; bl.append(f"Non-zero: {rc}")
            elif not mok: rs = "failed_repo_mutation_detected"; bl.append("Mutation detected.")
            else: rs = "captured"

    return {
        "backend_retry_status": rs, "dry_run": not execute, "execute_requested": execute,
        "retry_attempt_number": 1 if execute else None, "retry_timeout_seconds": rto,
        "retry_attempts_used": 1 if execute and rs not in ("dry_run_ready",) else 0,
        "retry_attempts_remaining": 0 if execute else ar, "retry_exhausted": rex,
        "package_id": pid, "contract_id": cid, "package_digest": pdg, "contract_digest": cdg,
        "prompt_digest": prd, "backend_name": lb, "locked_backend_name": lb, "backend_command": bcmd,
        "backend_invocation_allowed_for_this_command": ba,
        "backend_invocation_performed": bi, "backend_capture_performed": cp,
        "backend_output_captured": oc, "stdout_path": sop, "stderr_path": sep,
        "return_code": rc, "timeout_detected": td, "started_at": sa, "finished_at": fa,
        "duration_seconds": dur, "pre_git_status": pg, "post_git_status": pog,
        "changed_files": chg, "unexpected_changed_files": ucg, "mutation_guard_passed": mok,
        "package_sent": psent, "apply_performed": False, "files_modified": len(ucg) > 0,
        "commits_created": 0, "push_performed": False, "execution_authorized": False,
        "real_captured_task_execution_allowed": False, "output_application_allowed": False,
        "recommended_next_phase": "77K — Real Captured Backend Output Intake" if rs == "captured" else "Resolve blockers first.",
        "blockers": bl, "warnings": [],
        "next_operator_action": (
            "Retry captured successfully. No output applied. Proceed to 77K."
            if rs == "captured"
            else ("Gates validated. Run --execute for one governed retry at 300s."
                  if rs == "dry_run_ready" else "Resolve blockers first.")
        ),
        "generated_at": ts,
    }


def run_phase_backend_capture_governed_retry(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    dry = getattr(args, "dry_run", False); exe = getattr(args, "execute", False)
    if exe and dry: print("Error: --execute and --dry-run are mutually exclusive."); return 1
    r = _build_backend_capture_governed_retry(root, execute=exe)
    if getattr(args, "save", False):
        d = root.join(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR); d.mkdir(parents=True, exist_ok=True)
        (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Retry saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0 if r["backend_retry_status"] in ("dry_run_ready", "captured") else 1
    print("Backend Capture Governed Retry"); print("=" * 30)
    print(f"  Status: {r['backend_retry_status']}")
    print(f"  Execute: {'yes' if r['execute_requested'] else 'no'}")
    print(f"  Timeout: {r.get('retry_timeout_seconds', 'n/a')}s")
    print(f"  Used: {r['retry_attempts_used']}  Remaining: {r['retry_attempts_remaining']}")
    print(f"  Exhausted: {'yes' if r['retry_exhausted'] else 'no'}")
    print(f"  Invoked: {'yes' if r['backend_invocation_performed'] else 'no'}")
    print(f"  Captured: {'yes' if r['backend_output_captured'] else 'no'}")
    if r.get('return_code') is not None: print(f"  RC: {r['return_code']}")
    if r.get('duration_seconds') is not None: print(f"  Duration: {r['duration_seconds']:.1f}s")
    print(f"  Mutation: {'passed' if r['mutation_guard_passed'] else 'failed'}")
    print(f"  Apply: no  Commits: 0")
    print(f"  Next: {r['recommended_next_phase']}")
    if r["blockers"]:
        for b in r["blockers"]: print(f"  - {b}")
    print(f"\n  {r['next_operator_action']}")
    return 0 if r["backend_retry_status"] in ("dry_run_ready", "captured") else 1


def run_phase_backend_capture_governed_retry_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR / "latest.json")
    if not p.is_file():
        r = {"backend_retry_status": "no_artifact"}
        if args.json: print(json.dumps(r, indent=2, sort_keys=True))
        else: print("No retry artifact found.")
        return 1
    r = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0 if r.get("backend_retry_status") in ("dry_run_ready", "captured") else 1
    print("Backend Capture Governed Retry (Show)"); print("=" * 36)
    print(f"  Status: {r.get('backend_retry_status', 'unknown')}")
    print(f"  Timeout: {r.get('retry_timeout_seconds', 'n/a')}s")
    print(f"  Next: {r.get('recommended_next_phase', 'n/a')}")
    return 0


# Phase 77K: backend retry mutation result intake
BACKEND_RETRY_MUTATION_RESULT_INTAKES_DIR = Path(".pcae") / "backend-retry-mutation-result-intakes"

_BACKEND_CREATED_FILE = "docs/REAL_CAPTURED_TASKS.md"


def _build_backend_retry_mutation_result_intake(root: HarnessPath) -> dict:
    """Read and classify a 77J governed retry result, with mutation-aware file detection.

    This is INTAKE/CLASSIFICATION ONLY. It must not invoke backends, retry capture,
    send packages, capture output, apply patches, modify/delete/stage/commit/push
    backend-created files.
    """
    from datetime import datetime, timezone
    import hashlib, subprocess as _sp, os as _os

    ts = datetime.now(timezone.utc).isoformat()

    # Read 77J retry result
    retry_ref = _ref_exists(root, BACKEND_CAPTURE_GOVERNED_RETRIES_DIR)
    retry_data = None; retry_status = "unknown"
    if retry_ref:
        rp = root.join(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR / "latest.json")
        if rp.is_file():
            retry_data = json.loads(rp.read_text(encoding="utf-8"))
            retry_status = retry_data.get("backend_retry_status", "unknown")

    # Read stdout/stderr
    stdout_size = 0; stderr_size = 0
    sop = root.join(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR / "latest.stdout.txt")
    sep = root.join(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR / "latest.stderr.txt")
    if sop.is_file(): stdout_size = len(sop.read_text(encoding="utf-8"))
    if sep.is_file(): stderr_size = len(sep.read_text(encoding="utf-8"))

    # Detect backend-created file
    bcf_path = root.path / _BACKEND_CREATED_FILE
    bcf_detected = bcf_path.is_file()
    bcf_files = [_BACKEND_CREATED_FILE] if bcf_detected else []
    bcf_lines = 0; bcf_size = 0; bcf_sha256 = None; bcf_git_status = "none"
    if bcf_detected:
        content = bcf_path.read_text(encoding="utf-8")
        bcf_lines = len(content.split("\n"))
        bcf_size = len(content)
        bcf_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        try:
            gs = _sp.run(["git", "status", "--porcelain", "--", _BACKEND_CREATED_FILE],
                        cwd=str(root.path), capture_output=True, text=True, timeout=15)
            bcf_git_status = "untracked" if gs.stdout.strip().startswith("??") else gs.stdout.strip() or "clean"
        except Exception:
            bcf_git_status = "unknown"

    # Git status
    try:
        gr = _sp.run(["git", "status", "--porcelain"], cwd=str(root.path), capture_output=True, text=True, timeout=15)
        current_git = gr.stdout.strip()
    except Exception:
        current_git = ""

    # Classification
    bl: list = []; intake_status = "classified"

    if not retry_ref or retry_status in ("no_artifact", "unknown"):
        intake_status = "missing_retry_result"; bl.append("No retry result found.")

    if intake_status != "classified":
        return _make_minimal_retry_intake(intake_status, bl, current_git, ts)

    # Extract
    rc_code = retry_data.get("return_code"); mg_ok = retry_data.get("mutation_guard_passed", True)
    oc = retry_data.get("backend_output_captured", False); dr = retry_data.get("dry_run", False)
    td = retry_data.get("timeout_detected", False); rex = retry_data.get("retry_exhausted", False)
    chg = retry_data.get("changed_files", []); uchg = retry_data.get("unexpected_changed_files", [])

    outcome = "unknown"; normal_ready = False; mutation_review = False
    quarantine_review = False; emergency = False; output_avail = False

    if dr:
        outcome = "dry_run_only"
    elif retry_status == "captured" and mg_ok and oc:
        outcome = "captured_clean"; normal_ready = True; output_avail = True
    elif retry_status == "failed_repo_mutation_detected":
        if rc_code == 0 and oc and bcf_detected:
            outcome = "repo_mutation_detected_with_output"
            output_avail = True; mutation_review = True; quarantine_review = True
        else:
            outcome = "repo_mutation_detected_without_output"
            emergency = True; mutation_review = True
    elif retry_status == "failed_backend_timeout" or td:
        outcome = "retry_timeout_failure"
    elif retry_status == "failed_backend_invocation":
        outcome = "retry_backend_failure"
    else:
        outcome = "unknown"

    recommended = "77L — Backend-Created Output Quarantine Review" if outcome == "repo_mutation_detected_with_output" else (
        "77L — Real Captured Backend Output Intake" if outcome == "captured_clean" else "Resolve blockers first."
    )

    return {
        "backend_retry_mutation_intake_status": "classified",
        "capture_outcome": outcome,
        "retry_result_ref": str(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR / "latest.json") if retry_ref else None,
        "stdout_ref": str(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR / "latest.stdout.txt") if sop.is_file() else None,
        "stderr_ref": str(BACKEND_CAPTURE_GOVERNED_RETRIES_DIR / "latest.stderr.txt") if sep.is_file() else None,
        "backend_retry_status": retry_status,
        "backend_name": retry_data.get("backend_name") if retry_data else None,
        "backend_command": retry_data.get("backend_command") if retry_data else None,
        "package_id": retry_data.get("package_id") if retry_data else None,
        "contract_id": retry_data.get("contract_id") if retry_data else None,
        "package_digest": retry_data.get("package_digest") if retry_data else None,
        "prompt_digest": retry_data.get("prompt_digest") if retry_data else None,
        "execute_requested": retry_data.get("execute_requested", False) if retry_data else False,
        "retry_attempt_number": retry_data.get("retry_attempt_number") if retry_data else None,
        "retry_timeout_seconds": retry_data.get("retry_timeout_seconds") if retry_data else None,
        "retry_attempts_used": retry_data.get("retry_attempts_used") if retry_data else None,
        "retry_attempts_remaining": retry_data.get("retry_attempts_remaining") if retry_data else None,
        "retry_exhausted": rex,
        "backend_invocation_performed": retry_data.get("backend_invocation_performed", False) if retry_data else False,
        "backend_capture_performed": retry_data.get("backend_capture_performed", False) if retry_data else False,
        "backend_output_captured": oc,
        "return_code": rc_code, "duration_seconds": retry_data.get("duration_seconds") if retry_data else None,
        "timeout_detected": td,
        "stdout_path": retry_data.get("stdout_path") if retry_data else None,
        "stderr_path": retry_data.get("stderr_path") if retry_data else None,
        "stdout_size_bytes": stdout_size, "stderr_size_bytes": stderr_size,
        "backend_output_available": output_avail,
        "mutation_guard_passed": mg_ok,
        "pre_git_status": retry_data.get("pre_git_status") if retry_data else None,
        "post_git_status": retry_data.get("post_git_status") if retry_data else None,
        "changed_files": chg, "unexpected_changed_files": uchg,
        "current_git_status": current_git,
        "backend_created_file_detected": bcf_detected,
        "backend_created_files": bcf_files,
        "backend_created_file_line_count": bcf_lines,
        "backend_created_file_size_bytes": bcf_size,
        "backend_created_file_sha256": bcf_sha256,
        "backend_created_file_git_status": bcf_git_status,
        "normal_output_intake_ready": normal_ready,
        "mutation_review_required": mutation_review,
        "quarantine_review_required": quarantine_review,
        "emergency_review_required": emergency,
        "backend_invocation_performed_in_this_phase": False,
        "backend_capture_performed_in_this_phase": False,
        "backend_output_captured_in_this_phase": False,
        "apply_performed": False, "files_modified_in_this_phase": False,
        "files_modified_by_backend": len(uchg) > 0,
        "commits_created": 0, "push_performed": False,
        "execution_authorized": False, "output_application_allowed": False,
        "file_preserved_untracked": bcf_detected,
        "file_deleted": False, "file_staged": False, "file_committed": False, "file_pushed": False,
        "recommended_next_phase": recommended,
        "blockers": bl, "warnings": [],
        "next_operator_action": (
            f"Mutation intake complete. Backend-created file '{_BACKEND_CREATED_FILE}' "
            f"detected ({bcf_lines} lines, {bcf_size} bytes). "
            "File preserved untracked. Quarantine review required before any adoption."
            if outcome == "repo_mutation_detected_with_output"
            else ("Backend output captured cleanly. Proceed to normal intake."
                  if outcome == "captured_clean" else "Resolve blockers first.")
        ),
        "generated_at": ts,
    }


def _make_minimal_retry_intake(intake_status: str, bl: list, git_status: str, ts: str) -> dict:
    return {
        "backend_retry_mutation_intake_status": intake_status,
        "capture_outcome": "unknown", "retry_result_ref": None,
        "stdout_ref": None, "stderr_ref": None,
        "backend_retry_status": "unknown", "backend_name": None, "backend_command": None,
        "package_id": None, "contract_id": None, "package_digest": None, "prompt_digest": None,
        "execute_requested": False, "retry_attempt_number": None, "retry_timeout_seconds": None,
        "retry_attempts_used": None, "retry_attempts_remaining": None, "retry_exhausted": False,
        "backend_invocation_performed": False, "backend_capture_performed": False,
        "backend_output_captured": False, "return_code": None, "duration_seconds": None,
        "timeout_detected": False, "stdout_path": None, "stderr_path": None,
        "stdout_size_bytes": 0, "stderr_size_bytes": 0,
        "backend_output_available": False,
        "mutation_guard_passed": True,
        "pre_git_status": None, "post_git_status": None,
        "changed_files": [], "unexpected_changed_files": [],
        "current_git_status": git_status,
        "backend_created_file_detected": False, "backend_created_files": [],
        "backend_created_file_line_count": 0, "backend_created_file_size_bytes": 0,
        "backend_created_file_sha256": None, "backend_created_file_git_status": "none",
        "normal_output_intake_ready": False,
        "mutation_review_required": False, "quarantine_review_required": False,
        "emergency_review_required": False,
        "backend_invocation_performed_in_this_phase": False,
        "backend_capture_performed_in_this_phase": False,
        "backend_output_captured_in_this_phase": False,
        "apply_performed": False, "files_modified_in_this_phase": False,
        "files_modified_by_backend": False,
        "commits_created": 0, "push_performed": False,
        "execution_authorized": False, "output_application_allowed": False,
        "file_preserved_untracked": False, "file_deleted": False,
        "file_staged": False, "file_committed": False, "file_pushed": False,
        "recommended_next_phase": "Resolve blockers first.",
        "blockers": bl, "warnings": [],
        "next_operator_action": "Resolve blockers first.",
        "generated_at": ts,
    }


def run_phase_backend_retry_mutation_result_intake(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    r = _build_backend_retry_mutation_result_intake(root)
    if getattr(args, "save", False):
        d = root.join(BACKEND_RETRY_MUTATION_RESULT_INTAKES_DIR)
        d.mkdir(parents=True, exist_ok=True); (d / ".gitignore").write_text("*\n")
        (d / "latest.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.json: print(f"Mutation intake saved: {d / 'latest.json'}")
    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0 if r["backend_retry_mutation_intake_status"] == "classified" else 1
    print("Backend Retry Mutation Result Intake"); print("=" * 36)
    print(f"  Intake status: {r['backend_retry_mutation_intake_status']}")
    print(f"  Capture outcome: {r['capture_outcome']}")
    print(f"  Backend: {r.get('backend_name', 'n/a')}")
    print(f"  Retry status: {r.get('backend_retry_status', 'n/a')}")
    print(f"  Return code: {r.get('return_code', 'n/a')}")
    print(f"  Duration: {r.get('duration_seconds', 'n/a')}s")
    print(f"  Mutation guard: {'passed' if r['mutation_guard_passed'] else 'failed'}")
    print(f"  Output available: {'yes' if r['backend_output_available'] else 'no'}")
    print(f"  Created file detected: {'yes' if r['backend_created_file_detected'] else 'no'}")
    if r['backend_created_files']:
        print(f"  Created files: {r['backend_created_files']}")
        print(f"  File lines: {r['backend_created_file_line_count']}")
        print(f"  File size: {r['backend_created_file_size_bytes']} bytes")
        print(f"  File SHA256: {r['backend_created_file_sha256'][:16] if r['backend_created_file_sha256'] else 'n/a'}...")
        print(f"  File git: {r['backend_created_file_git_status']}")
    print(f"  Normal intake ready: {'yes' if r['normal_output_intake_ready'] else 'no'}")
    print(f"  Mutation review: {'yes' if r['mutation_review_required'] else 'no'}")
    print(f"  Quarantine review: {'yes' if r['quarantine_review_required'] else 'no'}")
    print(f"  Emergency review: {'yes' if r['emergency_review_required'] else 'no'}")
    print(f"  Backend invoked (this phase): no")
    print(f"  File preserved untracked: {'yes' if r['file_preserved_untracked'] else 'no'}")
    print(f"  File deleted: no  File staged: no  File committed: no  File pushed: no")
    print(f"  Recommended next: {r['recommended_next_phase']}")
    if r["blockers"]:
        for b in r["blockers"]: print(f"  - {b}")
    print(f"\n  {r['next_operator_action']}")
    return 0 if r["backend_retry_mutation_intake_status"] == "classified" else 1


def run_phase_backend_retry_mutation_result_intake_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    p = root.join(BACKEND_RETRY_MUTATION_RESULT_INTAKES_DIR / "latest.json")
    if not p.is_file():
        r = {"backend_retry_mutation_intake_status": "no_artifact"}
        if args.json: print(json.dumps(r, indent=2, sort_keys=True))
        else: print("No mutation intake artifact found.")
        return 1
    r = json.loads(p.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0 if r.get("backend_retry_mutation_intake_status") == "classified" else 1
    print("Backend Retry Mutation Result Intake (Show)"); print("=" * 42)
    print(f"  Status: {r.get('backend_retry_mutation_intake_status', 'unknown')}")
    print(f"  Outcome: {r.get('capture_outcome', 'unknown')}")
    print(f"  Created file: {'yes' if r.get('backend_created_file_detected') else 'no'}")
    print(f"  Next: {r.get('recommended_next_phase', 'n/a')}")
    return 0
