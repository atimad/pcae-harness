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

    if args.json:
        full_json = {
            **handoff_artifact,
            "check_status": "passed" if result.check_passed else "failed",
            "explicit_next_agent": explicit_next_agent,
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

    for line in log_lines:
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        commit_hash, subject = parts
        m = _PHASE_COMMIT_RE.match(subject)
        if not m:
            continue
        kind, phase_id, description = m.group(1), m.group(2), m.group(3)
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

    all_phase_ids = list(dict.fromkeys(
        list(comp_map.keys()) + list(impl_map.keys())
    ))

    if since:
        all_phase_ids = [p for p in all_phase_ids if p >= since]

    if last > 0:
        all_phase_ids = all_phase_ids[:last]

    phases: list[dict] = []
    for phase_id in all_phase_ids:
        impl = impl_map.get(phase_id)
        comp = comp_map.get(phase_id)
        phases.append({
            "phase_id": phase_id,
            "description": (comp or impl or {}).get("description", ""),
            "implementation_commit": impl["commit"] if impl else None,
            "completion_commit": comp["commit"] if comp else None,
            "commit_pair_complete": impl is not None and comp is not None,
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
        if not phase["commit_pair_complete"]:
            missing = []
            if phase["implementation_commit"] is None:
                missing.append("implementation")
            if phase["completion_commit"] is None:
                missing.append("completion")
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
    sim = _read_latest_simulation(root)
    review = _read_latest_sim_review(root)
    approval = _read_latest_sim_approval(root)

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
    result = {
        "authorization_available": False,
        "authorized": False,
        "refusal_reason": _EXECUTION_AUTHORIZATION_REFUSAL,
        "mutation_performed": False,
        "dry_run": getattr(args, "dry_run", False),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    print("Runner Execution Authorization")
    print("=" * 40)
    print(f"  Authorization available: no")
    print(f"  Authorized: no")
    print(f"  Mutation performed: no")
    print()
    print(f"  {_EXECUTION_AUTHORIZATION_REFUSAL}")
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


def run_phase_runner_execute(args: argparse.Namespace) -> int:
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
