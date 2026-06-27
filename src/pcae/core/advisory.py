"""
Advisory mode prototype — Phase 88X.

Read-only, non-authorizing advisory layer. Consumes broker + shell gate
evidence and produces a would-* advisory decision. Never executes commands,
intercepts shell, invokes backends, or grants authorization.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.permission_broker import (
    BPE_DECISIONS,
    BPE_HARD_BLOCK_DECISIONS,
    build_permission_broker,
)


# ── Advisory decision vocabulary (88W §17) ───────────────────────────────────

ADVISORY_DECISIONS: tuple[str, ...] = (
    "would_allow_read_only",
    "would_allow_governed_preflight_only",
    "would_require_active_task",
    "would_require_preflight",
    "would_require_human_review",
    "would_require_more_evidence",
    "would_block_by_scope",
    "would_block_by_task_contract",
    "would_block_by_raw_git_push",
    "would_block_by_force_push",
    "would_block_by_shell_gate",
    "would_block_by_test_run_lock",
    "would_block_by_failed_health",
    "would_block_by_failed_check",
    "would_block_by_failed_doctor",
    "would_block_by_push_check",
    "would_block_by_conflicting_evidence",
    "would_deny",
    "unknown",
)

# ── Broker → Advisory decision mapping ───────────────────────────────────────

_BROKER_TO_ADVISORY: dict[str, str] = {
    "allow_preflight_only":              "would_allow_governed_preflight_only",
    "requires_human_review":             "would_require_human_review",
    "requires_more_evidence":            "would_require_more_evidence",
    "blocked_by_scope":                  "would_block_by_scope",
    "blocked_by_task_contract":          "would_block_by_task_contract",
    "blocked_by_raw_git_push":           "would_block_by_raw_git_push",
    "blocked_by_force_push":             "would_block_by_force_push",
    "blocked_by_shell_gate":             "would_block_by_shell_gate",
    "blocked_by_test_run_lock":          "would_block_by_test_run_lock",
    "blocked_by_failed_health":          "would_block_by_failed_health",
    "blocked_by_failed_check":           "would_block_by_failed_check",
    "blocked_by_failed_doctor":          "would_block_by_failed_doctor",
    "blocked_by_push_check":             "would_block_by_push_check",
    "blocked_by_conflicting_evidence":   "would_block_by_conflicting_evidence",
    # Generic hard blocks map to would_block_by_shell_gate
    "blocked_by_backend_policy":         "would_block_by_shell_gate",
    "blocked_by_mutation_policy":        "would_block_by_shell_gate",
    "blocked_by_commit_policy":          "would_block_by_shell_gate",
    "blocked_by_push_policy":            "would_block_by_shell_gate",
    "blocked_by_lifecycle_state":        "would_block_by_shell_gate",
    "blocked_by_risk":                   "would_block_by_shell_gate",
    "blocked_by_must_never_repeat":      "would_block_by_shell_gate",
    "blocked_by_failed_tests":           "would_block_by_shell_gate",
    "deny":                              "would_deny",
    "unknown":                           "unknown",
}

# ── Advisory recommendations per advisory decision ───────────────────────────

_ADVISORY_RECOMMENDATIONS: dict[str, str] = {
    "would_allow_read_only":
        "This command is read-only. It would be allowed without restrictions.",
    "would_allow_governed_preflight_only":
        "This command would pass all governance checks. "
        "Execution authorization is not granted (preflight only).",
    "would_require_active_task":
        "An active task contract is required before this command can proceed.",
    "would_require_preflight":
        "Scope preflight evaluation is required before this command can proceed.",
    "would_require_human_review":
        "Human review is required before this command can proceed.",
    "would_require_more_evidence":
        "Additional governance evidence is missing. "
        "Provide the missing items and re-evaluate.",
    "would_block_by_scope":
        "This command would be blocked: the requested files are outside "
        "the active task scope.",
    "would_block_by_task_contract":
        "This command would be blocked: no active task contract. "
        "Create a task before performing mutating actions.",
    "would_block_by_raw_git_push":
        "This command would be blocked: raw git push. "
        "Use pcae push instead.",
    "would_block_by_force_push":
        "This command would be blocked: force push is permanently blocked.",
    "would_block_by_shell_gate":
        "This command would be blocked by PCAE shell gate policy.",
    "would_block_by_test_run_lock":
        "This command would be blocked: a test run is already in progress. "
        "Wait for it to complete.",
    "would_block_by_failed_health":
        "This command would be blocked: PCAE health check is failing. "
        "Run pcae health to diagnose.",
    "would_block_by_failed_check":
        "This command would be blocked: PCAE governance check is failing. "
        "Run pcae check to diagnose.",
    "would_block_by_failed_doctor":
        "This command would be blocked: PCAE doctor check is failing. "
        "Run pcae doctor to diagnose.",
    "would_block_by_push_check":
        "This command would be blocked: push readiness check is failing.",
    "would_block_by_conflicting_evidence":
        "This command would be blocked: contradictory governance evidence "
        "was detected.",
    "would_deny":
        "This command would be unconditionally denied by PCAE policy.",
    "unknown":
        "The advisory decision could not be determined. "
        "More evidence is needed.",
}

# ── Operator messages per advisory decision ──────────────────────────────────

def _operator_message(advisory_decision: str, hard_block_present: bool,
                      hard_block_reason: str | None) -> str:
    """Build a contextual operator message."""
    if hard_block_present:
        reason = hard_block_reason or "policy"
        return (
            f"This command would be blocked by PCAE policy ({reason}). "
            f"Advisory mode does not enforce this block. "
            f"The operator may still run this command directly in the shell, "
            f"but PCAE policy recommends against it."
        )
    if advisory_decision == "would_require_human_review":
        return (
            "This command would require human review. "
            "Provide human review evidence and re-evaluate."
        )
    if advisory_decision == "would_require_more_evidence":
        return (
            "Additional evidence is required. "
            "Provide the missing evidence items and re-evaluate."
        )
    if advisory_decision == "would_require_active_task":
        return (
            "An active task contract is required. "
            "Create a task with pcae task create."
        )
    return (
        f"Advisory evaluation complete. Decision: {advisory_decision}. "
        f"PCAE advisory mode is non-authorizing. "
        f"The operator retains full authority."
    )


# ── Next required action ─────────────────────────────────────────────────────

def _next_action(advisory_decision: str, hard_block_present: bool,
                 missing_evidence: list[str]) -> str:
    """Recommend the next operator action."""
    if hard_block_present:
        return (
            "Resolve the blocking condition before proceeding. "
            "See: pcae advisory explain <decision>"
        )
    if advisory_decision == "would_require_more_evidence":
        items = ", ".join(missing_evidence) if missing_evidence else "unknown"
        return f"Provide missing evidence: {items}"
    if advisory_decision == "would_require_human_review":
        return "Obtain human review and re-evaluate with --human-review-present."
    if advisory_decision == "would_require_active_task":
        return "Create an active task contract with pcae task create."
    if advisory_decision == "would_require_preflight":
        return "Run scope preflight: pcae preflight scope <files>"
    return "Operator may proceed at their own discretion."


# ── Performed flags (always false) ───────────────────────────────────────────

def _empty_performed_flags() -> dict[str, bool]:
    return {
        "authorization_granted": False,
        "execution_authorized": False,
        "command_executed": False,
        "repo_mutation_performed": False,
        "backend_invocation_performed": False,
        "prompt_sent": False,
        "capture_performed": False,
        "intake_performed": False,
        "adoption_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "raw_git_push_performed": False,
        "force_push_performed": False,
        "storage_written": False,
    }


# ── Advisory decision explanations ───────────────────────────────────────────

_ADVISORY_EXPLANATIONS: dict[str, dict[str, str]] = {
    "would_allow_read_only": {
        "summary": "Command is read-only inspection.",
        "meaning": "The shell gate classifier determined this command performs "
                   "only read-only operations (no file writes, no network "
                   "access, no secret access, no environment mutation).",
        "would_block": "no",
        "can_override": "n/a (not blocked)",
        "next_step": "Operator may proceed.",
    },
    "would_allow_governed_preflight_only": {
        "summary": "Command would pass all governance checks (preflight only).",
        "meaning": "All provided governance evidence passed. The command would "
                   "be allowed to proceed to preflight authorization. Execution "
                   "is never authorized in advisory mode.",
        "would_block": "no",
        "can_override": "n/a (not blocked)",
        "next_step": "Operator may proceed to preflight.",
    },
    "would_require_human_review": {
        "summary": "Human review is required.",
        "meaning": "The broker determined that this command requires explicit "
                   "human review before it can proceed. This is not a hard "
                   "block — providing human review evidence will allow the "
                   "command to proceed to preflight.",
        "would_block": "no",
        "can_override": "yes — provide human review evidence",
        "next_step": "Provide human review and re-evaluate.",
    },
    "would_block_by_force_push": {
        "summary": "Force push is permanently blocked.",
        "meaning": "Force push is a permanently hard-blocked action. No "
                   "human approval, accepted risk, or operator override can "
                   "authorize a force push.",
        "would_block": "yes",
        "can_override": "no — force push is permanently blocked",
        "next_step": "Do not force push. Use normal push flow.",
    },
    "would_block_by_shell_gate": {
        "summary": "Command would be blocked by shell gate classifier.",
        "meaning": "The shell gate classifier found a condition that would "
                   "block this command. This is a hard block — it cannot be "
                   "overridden by human approval or accepted risk.",
        "would_block": "yes",
        "can_override": "no — hard blocks cannot be overridden",
        "next_step": "Address the blocking condition.",
    },
    "would_deny": {
        "summary": "Command would be unconditionally denied.",
        "meaning": "The shell gate or broker issued an unconditional deny "
                   "for this command. This is the strongest form of block.",
        "would_block": "yes",
        "can_override": "no — deny is permanent",
        "next_step": "Do not run this command. No workaround exists.",
    },
}


def _explain_decision(advisory_decision: str) -> dict[str, str]:
    """Return explanation for an advisory decision. Unknown decisions
    get a safe fallback explanation."""
    if advisory_decision in _ADVISORY_EXPLANATIONS:
        return dict(_ADVISORY_EXPLANATIONS[advisory_decision])
    return {
        "summary": f"Advisory decision: {advisory_decision}",
        "meaning": "This is a valid advisory decision value. See pcae advisory "
                   "explain for more details on specific decisions.",
        "would_block": "unknown",
        "can_override": "unknown",
        "next_step": "Review the advisory decision documentation.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Core advisory evaluation
# ═══════════════════════════════════════════════════════════════════════════════

def build_advisory(
    repo_root: Path,
    requested_command: str,
    requested_action: str | None = None,
    requested_files: list[str] | None = None,
    health_passed: bool | None = None,
    check_passed: bool | None = None,
    human_review_present: bool = False,
    human_approval_present: bool = False,
    accepted_risk_present: bool = False,
) -> dict[str, Any]:
    """
    Build the advisory mode JSON envelope.

    Consumes broker + shell gate evidence and produces would-* advisory
    output. Never executes commands, invokes backends, or grants authorization.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Derive action from command if not explicit
    if requested_action is None:
        requested_action = "read"

    # Build broker evidence (this internally runs shell gate classification)
    broker_envelope = build_permission_broker(
        repo_root=repo_root,
        requested_action=requested_action,
        requested_files=requested_files or [],
        requested_command=requested_command,
        health_passed=health_passed,
        check_passed=check_passed,
        human_review_present=human_review_present,
        human_approval_present=human_approval_present,
        accepted_risk_present=accepted_risk_present,
    )

    broker = broker_envelope["broker"]
    broker_decision: str = broker["decision"]
    sg_evidence = broker.get("shell_gate_evidence")

    # Map broker decision to advisory decision
    advisory_decision = _BROKER_TO_ADVISORY.get(broker_decision, "unknown")

    # Extract fields
    hard_block_present: bool = broker["hard_block_present"]
    hard_block_reason: str | None = broker_decision if hard_block_present else None
    hard_block_source: str | None = None
    if hard_block_present:
        hard_block_sources = broker.get("hard_block_sources", [])
        hard_block_source = hard_block_sources[0] if hard_block_sources else "broker"

    sg_decision: str | None = sg_evidence["decision"] if sg_evidence else None
    sg_category: str | None = sg_evidence["command_category"] if sg_evidence else None

    command_redacted: bool = broker.get("shell_gate_command_text_redacted", False)
    redaction_reason: str | None = None
    if command_redacted:
        if sg_evidence and sg_evidence.get("secret_access_detected"):
            redaction_reason = "secret_access_detected"
        else:
            redaction_reason = "policy"

    requested_command_safe = broker.get("requested_command", requested_command)

    # Determine would-* booleans
    would_block = advisory_decision.startswith("would_block") or advisory_decision == "would_deny"
    would_require_human_review = advisory_decision == "would_require_human_review"
    would_require_preflight = advisory_decision == "would_require_preflight"
    would_require_active_task = advisory_decision == "would_require_active_task"
    would_require_more_evidence = advisory_decision == "would_require_more_evidence"
    would_deny = advisory_decision == "would_deny"

    # Human approval / accepted risk relevance
    human_approval_relevant = would_require_human_review
    human_approval_would_change = would_require_human_review
    accepted_risk_relevant = False  # reserved for future stages

    # Messages
    op_message = _operator_message(advisory_decision, hard_block_present, hard_block_reason)
    next_action = _next_action(
        advisory_decision, hard_block_present,
        broker.get("missing_evidence", []),
    )

    advisory_recommendation = _ADVISORY_RECOMMENDATIONS.get(
        advisory_decision,
        f"Advisory evaluation complete. Decision: {advisory_decision}.",
    )

    # Evidence sources
    evidence_sources: list[str] = list(broker.get("evidence_sources", []))
    missing_evidence: list[str] = list(broker.get("missing_evidence", []))
    warnings: list[str] = list(broker_envelope.get("warnings", []))
    errors: list[str] = list(broker_envelope.get("errors", []))

    return {
        "schema_version": "0.1",
        "generated_at": now,
        "repository_root": str(repo_root),
        "advisory_mode": True,
        "advisory_mode_version": "0.1",
        "requested_action": requested_action,
        "requested_command": requested_command_safe,
        "requested_command_redacted": command_redacted,
        "requested_files": requested_files or [],
        "broker_decision": broker_decision,
        "shell_gate_decision": sg_decision,
        "shell_gate_category": sg_category,
        "advisory_decision": advisory_decision,
        "advisory_recommendation": advisory_recommendation,
        "would_allow_read_only": advisory_decision == "would_allow_read_only",
        "would_allow_governed_preflight_only": advisory_decision == "would_allow_governed_preflight_only",
        "would_require_active_task": would_require_active_task,
        "would_require_preflight": would_require_preflight,
        "would_require_human_review": would_require_human_review,
        "would_require_more_evidence": would_require_more_evidence,
        "would_block": would_block,
        "would_deny": would_deny,
        "hard_block_present": hard_block_present,
        "hard_block_reason": hard_block_reason,
        "hard_block_source": hard_block_source,
        "human_approval_relevant": human_approval_relevant,
        "human_approval_would_change_outcome": human_approval_would_change,
        "accepted_risk_relevant": accepted_risk_relevant,
        "redaction_applied": command_redacted,
        "redaction_reason": redaction_reason,
        "safe_to_display": True,
        "operator_message": op_message,
        "next_required_action": next_action,
        "authorization_granted": False,
        "execution_authorized": False,
        "command_executed": False,
        "enforcement_applied": False,
        "shell_intercepted": False,
        "performed_flags": _empty_performed_flags(),
        "evidence_sources": evidence_sources,
        "missing_evidence": missing_evidence,
        "warnings": warnings,
        "errors": errors,
    }


def build_advisory_explain(advisory_decision: str) -> dict[str, Any]:
    """Build the advisory explain JSON envelope."""
    explanation = _explain_decision(advisory_decision)
    return {
        "schema_version": "0.1",
        "advisory_decision": advisory_decision,
        "explanation": explanation,
        "valid_decision": advisory_decision in ADVISORY_DECISIONS,
        "all_decisions": list(ADVISORY_DECISIONS),
    }


def build_advisory_status() -> dict[str, Any]:
    """Build the advisory status JSON envelope."""
    return {
        "schema_version": "0.1",
        "advisory_mode_available": True,
        "advisory_mode_version": "0.1",
        "implementation_status": "prototype",
        "phase": "88X",
        "invariants": {
            "no_command_execution": True,
            "no_shell_interception": True,
            "no_shell_wrappers": True,
            "no_backend_invocation": True,
            "no_prompts_or_capture": True,
            "no_authorization": True,
            "no_enforcement": True,
            "performed_flags_always_false": True,
        },
    }
