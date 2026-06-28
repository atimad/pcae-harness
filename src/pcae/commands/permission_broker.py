"""CLI runners for pcae permission-broker commands.

Phase 88R: evaluate — full governance evidence broker
Phase 91B: status, explain, check — simulation-only 4-outcome broker
"""
from __future__ import annotations

import argparse
import json

from pcae.core.paths import HarnessPath
from pcae.core.permission_broker import (
    build_permission_broker,
    evaluate_permission_broker,
    # Reason codes for explanation
    _broker_decision,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 88R — evaluate
# ═══════════════════════════════════════════════════════════════════════════════


def run_permission_broker_evaluate(args: argparse.Namespace) -> int:
    requested_files: list[str] = list(getattr(args, "requested_file", None) or [])
    data = build_permission_broker(
        repo_root=HarnessPath.cwd().path,
        requested_action=args.requested_action,
        requested_files=requested_files,
        requested_command=getattr(args, "requested_command", None),
        source_backend=getattr(args, "source_backend", None),
        commit_message=getattr(args, "commit_message", None),
        push_target=getattr(args, "push_target", None),
        health_passed=_tri(getattr(args, "health_passed", None)),
        check_passed=_tri(getattr(args, "check_passed", None)),
        doctor_passed=_tri(getattr(args, "doctor_passed", None)),
        push_check_passed=_tri(getattr(args, "push_check_passed", None)),
        tests_present=bool(getattr(args, "tests_present", False)),
        tests_passed=_tri(getattr(args, "tests_passed", None)),
        human_review_present=bool(getattr(args, "human_review_present", False)),
        human_approval_present=bool(getattr(args, "human_approval_present", False)),
        accepted_risk_present=bool(getattr(args, "accepted_risk_present", False)),
    )

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        broker = data["broker"]
        decision = broker["decision"]
        action = broker["requested_action"]
        hard = broker["hard_block_present"]
        active = broker["active_task_detected"]
        print("Permission broker evaluate (prototype)")
        print(f"  Action:      {action}")
        if broker["requested_command"]:
            print(f"  Command:     {broker['requested_command']!r}")
        print(f"  Decision:    {decision}")
        print(f"  Hard block:  {hard}")
        print(f"  Active task: {active}")
        if broker["missing_evidence"]:
            print(f"  Missing:     {', '.join(broker['missing_evidence'])}")
        if broker["reason_codes"]:
            print(f"  Reasons:     {', '.join(broker['reason_codes'])}")
        print()
        print("  [broker_does_not_grant_execution_authorization]")

    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 91B — status, explain, check
# ═══════════════════════════════════════════════════════════════════════════════

# ── Reason-code explanation registry ─────────────────────────────────────────

_REASON_EXPLANATIONS: dict[str, dict[str, str]] = {
    # Hard blocks
    "blocked_by_raw_git_commit": {
        "summary": "Raw git commit is permanently blocked.",
        "category": "hard_block",
        "meaning": "Direct git commit bypasses PCAE governance. Use pcae commit instead.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_raw_git_push": {
        "summary": "Raw git push is permanently blocked.",
        "category": "hard_block",
        "meaning": "Direct git push bypasses PCAE governance. Use pcae push instead.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_force_push": {
        "summary": "Force push is permanently blocked.",
        "category": "hard_block",
        "meaning": "Force push rewrites shared history and is never permitted.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_no_verify": {
        "summary": "The --no-verify flag is permanently blocked.",
        "category": "hard_block",
        "meaning": "Bypassing hooks and governance checks with --no-verify is not permitted.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_destructive_filesystem": {
        "summary": "Destructive filesystem operations are permanently blocked.",
        "category": "hard_block",
        "meaning": "Commands that can cause irreversible data loss (rm -rf, git clean) are blocked.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_unknown_command_class": {
        "summary": "Unknown or ambiguous command class is blocked.",
        "category": "hard_block",
        "meaning": "PCAE must fail closed on commands it cannot classify. Provide an explicit command class.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_out_of_scope": {
        "summary": "Requested paths are outside the active task scope.",
        "category": "hard_block",
        "meaning": "One or more requested files are not in the task contract's allowed files list.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_policy_forbidden_file": {
        "summary": "A policy-forbidden file was requested.",
        "category": "hard_block",
        "meaning": "Certain files (README.md, docs/REAL_CAPTURED_TASKS.md, docs/LINKEDIN_ARTICLE_DRAFT.md) are never mutable, regardless of task scope.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_forbidden_path": {
        "summary": "A task-forbidden path was requested.",
        "category": "hard_block",
        "meaning": "One or more requested files are in the task contract's forbidden files list.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_missing_task": {
        "summary": "No active task contract exists for a mutating action.",
        "category": "hard_block",
        "meaning": "Mutating actions (source_mutation, docs_mutation, commit, push, rollback) require an active task contract.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_enforcement_not_ready": {
        "summary": "Enforcement readiness gates are not satisfied.",
        "category": "hard_block",
        "meaning": "Enforcement readiness gates must be satisfied before mutating actions can proceed.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    "blocked_by_enforcement_not_authorized": {
        "summary": "Enforcement is not authorized.",
        "category": "hard_block",
        "meaning": "An operator must explicitly authorize enforcement before mutating actions can proceed.",
        "overridable": "no — hard blocks cannot be overridden (88V §16)",
    },
    # More evidence
    "missing_action_type": {
        "summary": "No action type was provided.",
        "category": "more_evidence",
        "meaning": "An action type (read, source_mutation, commit, etc.) is required to evaluate the request.",
        "overridable": "n/a — not a block",
    },
    "unknown_action_type": {
        "summary": "The provided action type is not recognized.",
        "category": "more_evidence",
        "meaning": "The action type must be one of: read, source_mutation, docs_mutation, test_mutation, backend_invocation, commit, push, rollback.",
        "overridable": "n/a — not a block",
    },
    "task_scope_unknown": {
        "summary": "Task contract scope is unknown or incomplete.",
        "category": "more_evidence",
        "meaning": "The task contract does not specify allowed files. Configure the task contract with explicit allowed/forbidden file lists.",
        "overridable": "n/a — not a block",
    },
    "repo_dirty_for_commit_push": {
        "summary": "Working tree is dirty for commit/push.",
        "category": "more_evidence",
        "meaning": "Commit and push actions require a clean working tree or explicit staging.",
        "overridable": "n/a — not a block",
    },
    # Human review
    "backend_invocation_requires_human_review": {
        "summary": "Backend invocation requires human review.",
        "category": "human_review",
        "meaning": "Invoking an AI backend requires explicit human review before proceeding.",
        "overridable": "yes — provide human approval",
    },
    "commit_requires_human_review": {
        "summary": "Commit requires human review and approval.",
        "category": "human_review",
        "meaning": "Commit actions require explicit human approval with a fresh, valid approval record.",
        "overridable": "yes — provide human approval",
    },
    "push_requires_human_review": {
        "summary": "Push requires human review and approval.",
        "category": "human_review",
        "meaning": "Push actions require explicit human approval with a fresh, valid approval record.",
        "overridable": "yes — provide human approval",
    },
    "rollback_requires_human_review": {
        "summary": "Rollback requires human review and approval.",
        "category": "human_review",
        "meaning": "Rollback actions require explicit human approval with a fresh, valid approval record.",
        "overridable": "yes — provide human approval",
    },
    "stale_approval": {
        "summary": "Approval is expired or revoked.",
        "category": "human_review",
        "meaning": "The provided approval has expired or been revoked. Fresh approval is required.",
        "overridable": "yes — provide fresh approval",
    },
    # Allow
    "allow_preflight_only": {
        "summary": "All governance checks passed (preflight only).",
        "category": "allow",
        "meaning": "The proposed action would pass all governance checks. This is a preflight-only evaluation — PCAE does NOT authorize execution.",
        "overridable": "n/a — not blocked",
    },
    # Misc
    "accepted_risk_noted": {
        "summary": "Accepted risk was noted but does not override hard blocks.",
        "category": "allow",
        "meaning": "The operator has accepted risk for this action. Accepted risk never overrides hard blocks (88V §16).",
        "overridable": "n/a — not a block",
    },
    "all_checks_passed": {
        "summary": "All governance checks passed.",
        "category": "allow",
        "meaning": "Every governance check was evaluated and passed.",
        "overridable": "n/a — not blocked",
    },
}


# ── CLI runners ──────────────────────────────────────────────────────────────


def run_permission_broker_status(args: argparse.Namespace) -> int:
    """pcae permission-broker status [--json]"""
    status_data = {
        "broker_available": True,
        "simulation_only": True,
        "no_enforcement": True,
        "no_execution": True,
        "enforcement_ready": False,
        "enforcement_authorized": False,
        "decision_model": "4-outcome (allow, deny, human_review, more_evidence)",
        "phase": "91B",
    }

    if args.json:
        print(json.dumps(status_data, indent=2, sort_keys=True))
    else:
        print("Permission broker status")
        print(f"  Available:              {status_data['broker_available']}")
        print(f"  Simulation only:        {status_data['simulation_only']}")
        print(f"  Enforcement active:     {not status_data['no_enforcement']}")
        print(f"  Enforcement ready:      {status_data['enforcement_ready']}")
        print(f"  Enforcement authorized: {status_data['enforcement_authorized']}")
        print(f"  Decision model:         {status_data['decision_model']}")
        print(f"  Phase:                  {status_data['phase']}")
        print()
        print("  ⚠️  Simulation only — no enforcement path is active.")
        print("  The operator retains full authority.")

    return 0


def run_permission_broker_explain(args: argparse.Namespace) -> int:
    """pcae permission-broker explain --reason-code <code> [--json]"""
    reason_code: str = getattr(args, "reason_code", "") or ""

    if not reason_code:
        if args.json:
            print(json.dumps({"error": "missing_reason_code",
                              "message": "No reason code provided. Use --reason-code."}))
        else:
            print("Error: No reason code provided. Use --reason-code <code>.")
        return 1

    explanation = _REASON_EXPLANATIONS.get(reason_code)

    if explanation is None:
        if args.json:
            print(json.dumps({
                "error": "unknown_reason_code",
                "reason_code": reason_code,
                "message": f"Unknown reason code: {reason_code!r}. "
                           f"Use pcae permission-broker explain --reason-code <known-code>.",
            }))
        else:
            print(f"Error: Unknown reason code: {reason_code!r}")
            print("Known reason codes:")
            for code in sorted(_REASON_EXPLANATIONS):
                print(f"  {code}")
        return 1

    if args.json:
        print(json.dumps({
            "reason_code": reason_code,
            "explanation": explanation,
        }, indent=2, sort_keys=True))
    else:
        print(f"Reason code: {reason_code}")
        print(f"  Summary:     {explanation['summary']}")
        print(f"  Category:    {explanation['category']}")
        print(f"  Meaning:     {explanation['meaning']}")
        print(f"  Overridable: {explanation['overridable']}")

    return 0


def run_permission_broker_check(args: argparse.Namespace) -> int:
    """pcae permission-broker check [--json] [--action-type ...] [...]"""
    action_type: str = getattr(args, "action_type", None)
    if action_type is None:
        action_type = "read"
    command_class: str = getattr(args, "command_class", None)
    if command_class is None:
        command_class = "unknown"

    # Parse paths
    path_args: list[str] = list(getattr(args, "path", None) or [])
    allowed_args: list[str] = list(getattr(args, "allowed_path", None) or [])
    forbidden_args: list[str] = list(getattr(args, "forbidden_path", None) or [])

    result = evaluate_permission_broker(
        action_type=action_type,
        command_class=command_class,
        paths=tuple(path_args),
        task_present=bool(getattr(args, "task_present", False)),
        task_scope_known=bool(getattr(args, "task_scope_known", False)),
        allowed_paths=tuple(allowed_args),
        forbidden_paths=tuple(forbidden_args),
        approval_present=bool(getattr(args, "approval_present", False)),
        approval_fresh=bool(getattr(args, "approval_fresh", True)),
        accepted_risk_present=bool(getattr(args, "accepted_risk_present", False)),
        readiness_ready=bool(getattr(args, "readiness_ready", False)),
        enforcement_authorized=bool(getattr(args, "enforcement_authorized", False)),
        repo_dirty=bool(getattr(args, "repo_dirty", False)),
    )

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        decision = result["decision"]
        hard = result["hard_block"]
        print("Permission broker check (simulation only)")
        print(f"  Action type:     {action_type}")
        print(f"  Command class:   {command_class}")
        if path_args:
            print(f"  Paths:           {', '.join(path_args)}")
        print(f"  Decision:        {decision}")
        print(f"  Hard block:      {hard}")
        print(f"  Reason:          {result['reason_code']}")
        if result["required_evidence"]:
            print(f"  Evidence needed: {', '.join(result['required_evidence'])}")
        print(f"  Message:         {result['message']}")
        print()
        print("  ⚠️  Simulation only — PCAE did NOT execute, intercept, or authorize anything.")
        print("  The operator retains full authority.")

    return 0 if result["decision"] != "deny" else 0


def _tri(value: object) -> bool | None:
    """Convert argparse tri-state (None / True) to bool | None."""
    if value is True:
        return True
    if value is False:
        return False
    return None
