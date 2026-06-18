from __future__ import annotations

import argparse
import json
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

    now = datetime.now(timezone.utc)
    task_suffix = task_id if task_id else "idle"
    handoff_id = f"handoff-{now:%Y%m%dT%H%M%S}-{now.microsecond:06d}-{task_suffix}"

    return {
        "active_task_id": task_id,
        "active_task_title": active_task.title if active_task else None,
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
        print()
        print(f"  Bootstrap: {data['bootstrap_command']}")

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
