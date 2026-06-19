from __future__ import annotations

import argparse
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
        "phase_queue_next": queue[0] if queue else None,
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


def _read_phase_queue(root: HarnessPath) -> list[str]:
    queue_path = root.join(PHASE_QUEUE_PATH)
    if not queue_path.is_file():
        return []
    try:
        data = json.loads(queue_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_phase_queue(root: HarnessPath, queue: list[str]) -> None:
    queue_path = root.join(PHASE_QUEUE_PATH)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(queue, f, indent=2)
        f.write("\n")


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

    if args.json:
        print(json.dumps({"queue": queue, "queue_length": len(queue)}, indent=2, sort_keys=True))
        return 0

    if not queue:
        print("Phase queue is empty.")
        return 0

    print(f"Phase queue ({len(queue)} entries):")
    for i, entry in enumerate(queue, 1):
        print(f"  {i}. {entry}")
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
        "next_queued": queue[0] if queue else None,
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
        print(f"  Next: {queue[0]}")
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


def _is_placeholder(entry: str) -> bool:
    lower = entry.lower().strip()
    return any(pattern in lower for pattern in PLACEHOLDER_PATTERNS)


def run_phase_queue_hygiene(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    queue = _read_phase_queue(root)

    findings: list[dict] = []
    clearable_indices: list[int] = []

    for i, entry in enumerate(queue):
        if _is_placeholder(entry):
            findings.append({
                "position": i + 1,
                "entry": entry,
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
    r"^(Implement|Complete) Phase (\S+)\s+(.+)$"
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
        if kind == "Implement":
            impl_map.setdefault(phase_id, entry)
        else:
            comp_map.setdefault(phase_id, entry)

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


def run_phase_audit_show(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    audit = _read_latest_audit(root)

    if audit is None:
        print("No saved audit artifact found.", file=__import__("sys").stderr)
        return 1

    if args.json:
        print(json.dumps(audit, indent=2, sort_keys=True))
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
