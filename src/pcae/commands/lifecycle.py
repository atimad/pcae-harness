"""Read-only lifecycle advisory commands (Phases 80B-80D).

These commands inspect lifecycle artifacts and recommend next actions.
They do not mutate state, invoke backends, run gates, or approve anything.
"""
from __future__ import annotations

import argparse
import json
import subprocess

from pcae.core.paths import HarnessPath
from pcae.lifecycle import LIFECYCLE_STATES, detect_lifecycle_state, get_next_recommendation, evaluate_gate_dry_run, evaluate_gate_approval


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


def run_lifecycle_run_gate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    gate_id = getattr(args, "gate", "") or ""
    dry_run = getattr(args, "dry_run", False)

    if not dry_run:
        r = {
            "blockers": ["--dry-run is required. Gate execution is not implemented."],
            "dry_run": False,
            "gate": gate_id,
            "lifecycle_gate_dry_run_status": "dry_run_required",
            "lifecycle_type": "backend-output-adoption",
            "read_only": True,
        }
        if args.json:
            print(json.dumps(r, indent=2, sort_keys=True))
        else:
            print("Gate runner blocked: --dry-run is required.")
        return 1

    state_id, _ = detect_lifecycle_state(root.path)
    r = evaluate_gate_dry_run(gate_id, state_id)

    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        print(f"Gate Dry-Run: {gate_id}")
        print("=" * 40)
        print(f"  Status: {r['lifecycle_gate_dry_run_status']}")
        print(f"  Current state: {r['current_state']}")
        print(f"  Target state: {r['target_state']}")
        print(f"  Gate kind: {r['gate_kind']}")
        print(f"  Dry-run: yes (no execution)")
        print(f"  Action: {r['planned_action_summary']}")
        if r["blockers"]:
            for b in r["blockers"]:
                print(f"  BLOCKED: {b}")
        if r["warnings"]:
            for w in r["warnings"]:
                print(f"  WARNING: {w}")

    return 0 if r["lifecycle_gate_dry_run_status"] == "ready" else 1


def run_lifecycle_approve_gate(args: argparse.Namespace) -> int:
    root = HarnessPath.cwd()
    gate_id = getattr(args, "gate", "") or ""
    approved_by = getattr(args, "approved_by", "") or ""
    reason_val = getattr(args, "reason", "") or ""
    dry_run = getattr(args, "dry_run", False)

    state_id, _ = detect_lifecycle_state(root.path)
    r = evaluate_gate_approval(gate_id, state_id, approved_by, reason_val, dry_run=dry_run)

    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        print(f"Gate Approval: {gate_id}")
        print("=" * 40)
        print(f"  Status: {r['lifecycle_gate_approval_status']}")
        print(f"  Current state: {r['current_state']}")
        print(f"  Target state: {r['target_state']}")
        print(f"  Approved by: {r['approved_by']}")
        print(f"  Reason: {r['reason']}")
        print(f"  Approval performed: {'yes' if r['approval_performed'] else 'no'}")
        print(f"  Execution authorized: no")
        if r["blockers"]:
            for b in r["blockers"]:
                print(f"  BLOCKED: {b}")
        if r["warnings"]:
            for w in r["warnings"]:
                print(f"  WARNING: {w}")

    ok = r["lifecycle_gate_approval_status"] in ("approved", "approval_not_required", "dry_run")
    return 0 if ok else 1
