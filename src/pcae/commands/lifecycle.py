"""Read-only lifecycle advisory commands (Phases 80B-80C).

These commands inspect lifecycle artifacts and recommend next actions.
They do not mutate state, invoke backends, run gates, or approve anything.
"""
from __future__ import annotations

import argparse
import json
import subprocess

from pcae.core.paths import HarnessPath
from pcae.lifecycle import LIFECYCLE_STATES, detect_lifecycle_state, get_next_recommendation


def _repo_indicators(root_path) -> dict:
    clean = True
    unpushed = 0
    try:
        r = subprocess.run(["git", "status", "--short"], cwd=root_path,
                           capture_output=True, text=True, timeout=15)
        clean = not r.stdout.strip()
    except Exception:
        pass
    try:
        r = subprocess.run(["git", "rev-list", "--count", "origin/main..HEAD"],
                           cwd=root_path, capture_output=True, text=True, timeout=15)
        unpushed = int(r.stdout.strip()) if r.returncode == 0 else 0
    except Exception:
        pass
    return {"repo_clean": clean, "origin_main_head_count": unpushed}


def run_lifecycle_status(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    state_id, details = detect_lifecycle_state(root.path)
    state = LIFECYCLE_STATES.get(state_id, LIFECYCLE_STATES["blocked"])
    repo = _repo_indicators(root.path)

    bl: list[str] = []
    wl: list[str] = []

    if not repo["repo_clean"]:
        wl.append("Working tree is not clean.")
    if repo["origin_main_head_count"] > 0:
        wl.append(f"{repo['origin_main_head_count']} unpushed commit(s).")

    lifecycle_closed = state_id in ("closed", "final_verified")
    status = "closed" if lifecycle_closed else ("active" if state_id not in ("idle", "blocked") else state_id)

    r = {
        "allowed_next_actions": list(state.allowed_next_actions),
        "approval_required_for_next": state.approval_required,
        "artifact_summary": details.get("artifact_summary", {}),
        "backend_invocation_performed": False,
        "blockers": bl,
        "current_state": state_id,
        "current_state_label": state.label,
        "detected_artifacts": details.get("detected_artifacts", {}),
        "execution_allowed_now": False,
        "force_push_performed": False,
        "lifecycle_closed": lifecycle_closed,
        "lifecycle_status": status,
        "lifecycle_type": "backend-output-adoption",
        "missing_artifacts": [],
        "origin_main_head_count": repo["origin_main_head_count"],
        "push_performed": False,
        "raw_git_push_performed": False,
        "read_only": True,
        "repo_clean": repo["repo_clean"],
        "runner_execute_performed": False,
        "warnings": wl,
    }

    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        print("Lifecycle Status: backend-output-adoption")
        print("=" * 46)
        print(f"  Status: {status}")
        print(f"  State: {state.label} ({state_id})")
        print(f"  Closed: {'yes' if lifecycle_closed else 'no'}")
        print(f"  Repo clean: {'yes' if repo['repo_clean'] else 'no'}")
        print(f"  Unpushed: {repo['origin_main_head_count']}")
        print(f"  Read-only: yes")
        if wl:
            for w in wl:
                print(f"  WARNING: {w}")
        if state.allowed_next_actions:
            print(f"  Next actions: {', '.join(state.allowed_next_actions)}")
    return 0


def run_lifecycle_next(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    state_id, details = detect_lifecycle_state(root.path)
    rec = get_next_recommendation(state_id)
    state = LIFECYCLE_STATES.get(state_id, LIFECYCLE_STATES["blocked"])

    bl: list[str] = []
    wl: list[str] = []

    if state_id == "blocked":
        bl.append("Lifecycle is blocked; resolve issues before proceeding.")

    r = {
        "approval_performed": False,
        "backend_invocation_performed": False,
        "blockers": bl,
        "current_state": state_id,
        "execution_performed": False,
        "force_push_performed": False,
        "lifecycle_next_status": "recommendation_available",
        "lifecycle_type": "backend-output-adoption",
        "push_performed": False,
        "raw_git_push_performed": False,
        "read_only": True,
        "reason": rec["reason"],
        "recommended_next_action": rec["recommended_next_action"],
        "recommended_next_phase": rec["recommended_next_phase"],
        "required_approval": rec["required_approval"],
        "required_preconditions": rec["required_preconditions"],
        "runner_execute_performed": False,
        "warnings": wl,
    }

    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        print("Lifecycle Next Step: backend-output-adoption")
        print("=" * 48)
        print(f"  Current state: {state.label} ({state_id})")
        print(f"  Recommended action: {rec['recommended_next_action']}")
        if rec["recommended_next_phase"]:
            print(f"  Recommended phase: {rec['recommended_next_phase']}")
        print(f"  Reason: {rec['reason']}")
        if rec["required_approval"]:
            print(f"  Approval required: yes")
        print(f"  Read-only: yes (no execution performed)")
        if bl:
            for b in bl:
                print(f"  BLOCKED: {b}")
    return 0
