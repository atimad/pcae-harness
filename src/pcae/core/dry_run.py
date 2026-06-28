"""
Dry-run blocking simulation prototype — Phase 89C.

Read-only, non-authorizing, non-intercepting simulation layer.  Consumes
advisory / broker / shell-gate evidence and produces a simulation decision
previewing what PCAE enforcement would decide.  Never executes commands,
intercepts shell, invokes backends, or grants authorization.

Designed in Phase 89B.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.advisory import (
    ADVISORY_DECISIONS,
    _BROKER_TO_ADVISORY,
    _ADVISORY_RECOMMENDATIONS,
    _operator_message,
    _next_action,
    _empty_performed_flags,
    _explain_decision,
)


# ── Simulation decision vocabulary (89B §15) ────────────────────────────────

SIMULATION_DECISIONS = ADVISORY_DECISIONS  # same 19 values

# ── Severity model (89B §16) ─────────────────────────────────────────────────

_SIMULATION_SEVERITY: dict[str, str] = {
    "would_allow_read_only":               "info",
    "would_allow_governed_preflight_only": "info",
    "would_require_active_task":           "caution",
    "would_require_preflight":             "caution",
    "would_require_more_evidence":         "caution",
    "would_require_human_review":          "review_required",
    "would_block_by_scope":                "blocked",
    "would_block_by_task_contract":        "blocked",
    "would_block_by_raw_git_push":         "blocked",
    "would_block_by_force_push":           "blocked",
    "would_block_by_shell_gate":           "blocked",
    "would_block_by_test_run_lock":        "blocked",
    "would_block_by_failed_health":        "blocked",
    "would_block_by_failed_check":         "blocked",
    "would_block_by_failed_doctor":        "blocked",
    "would_block_by_push_check":           "blocked",
    "would_block_by_conflicting_evidence": "blocked",
    "would_deny":                           "blocked",
    "unknown":                              "unknown",
}

# ── Enforcement readiness per decision (89B §17) ─────────────────────────────

_ENFORCEMENT_READINESS: dict[str, str] = {
    "would_allow_read_only":
        "Ready for enforcement. No changes needed.",
    "would_allow_governed_preflight_only":
        "Ready for enforcement. Preflight-only path confirmed.",
    "would_require_active_task":
        "Create an active task contract before enforcement is active.",
    "would_require_preflight":
        "Run scope preflight before enforcement is active.",
    "would_require_human_review":
        "Under enforcement, human review will be required before proceeding.",
    "would_require_more_evidence":
        "Provide missing evidence before enforcement is active.",
    "would_block_by_raw_git_push":
        "Use pcae push instead. Enforcement will block raw git push.",
    "would_block_by_force_push":
        "Force push will be permanently blocked under enforcement.",
    "would_block_by_shell_gate":
        "Address the shell gate blocking condition.",
    "would_block_by_scope":
        "Ensure files are within the active task scope.",
    "would_block_by_task_contract":
        "Create an active task contract before enforcement.",
    "would_block_by_test_run_lock":
        "Wait for the active test run to complete.",
    "would_block_by_failed_health":
        "Fix health before enforcement. Run pcae health.",
    "would_block_by_failed_check":
        "Fix check before enforcement. Run pcae check.",
    "would_block_by_failed_doctor":
        "Fix doctor before enforcement. Run pcae doctor.",
    "would_block_by_push_check":
        "Fix push readiness before enforcement. Run pcae push check.",
    "would_block_by_conflicting_evidence":
        "Resolve conflicting evidence before enforcement.",
    "would_deny":
        "This command would be permanently denied under enforcement.",
    "unknown":
        "Enforcement readiness could not be determined.",
}

# ── Governed alternatives per block type ─────────────────────────────────────

_GOVERNED_ALTERNATIVES: dict[str, str | None] = {
    "would_block_by_raw_git_push": "pcae push",
    "would_block_by_raw_git_commit": "pcae commit",
    "would_block_by_force_push": None,  # permanently blocked
    "would_deny": None,
}

# ── Safety invariants ────────────────────────────────────────────────────────

def _safety_invariants() -> dict[str, bool]:
    return {
        "simulation_only": True,
        "no_execution": True,
        "no_authorization": True,
        "no_enforcement": True,
        "no_interception": True,
        "no_wrappers": True,
        "no_backend": True,
        "no_persistent_state": True,
        "hard_blocks_preserved": True,
        "secrets_redacted": True,
    }


def _known_limitations() -> list[str]:
    return [
        "Simulation only — no enforcement occurred",
        "Operator can still run command directly in shell",
        "No shell interception or wrapping active",
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# Core simulation evaluation
# ═══════════════════════════════════════════════════════════════════════════════

def build_simulation(
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
    Build the dry-run blocking simulation JSON envelope.

    Consumes advisory (which consumes broker + shell gate) evidence and
    wraps it in a simulation-specific envelope.  Never executes commands,
    invokes backends, or grants authorization.
    """
    import uuid
    from pcae.core.advisory import build_advisory

    now = datetime.now(timezone.utc).isoformat()
    simulation_id = f"sim-{uuid.uuid4().hex[:12]}"

    # Delegate to advisory for the core evaluation
    advisory = build_advisory(
        repo_root=repo_root,
        requested_command=requested_command,
        requested_action=requested_action,
        requested_files=requested_files,
        health_passed=health_passed,
        check_passed=check_passed,
        human_review_present=human_review_present,
        human_approval_present=human_approval_present,
        accepted_risk_present=accepted_risk_present,
    )

    decision = advisory["advisory_decision"]
    severity = _SIMULATION_SEVERITY.get(decision, "unknown")

    # Severity label
    severity_labels = {
        "info": "INFO",
        "caution": "CAUTION",
        "review_required": "REVIEW REQUIRED",
        "blocked": "SIMULATED BLOCK",
        "unknown": "UNKNOWN",
    }

    # Governed alternative
    governed_alt = _GOVERNED_ALTERNATIVES.get(decision)
    # Check broker decision for raw_git_commit mapping
    if governed_alt is None and advisory.get("broker_decision") == "blocked_by_raw_git_commit":
        governed_alt = "pcae commit"

    # Enforcement readiness
    enforcement_readiness = _ENFORCEMENT_READINESS.get(
        decision, "Enforcement readiness could not be determined."
    )

    return {
        "schema_version": "0.1",
        "generated_at": now,
        "repository_root": str(repo_root),
        "simulation_id": simulation_id,

        "simulation_mode": True,
        "simulation_version": "0.1",
        "enforcement_stage": "dry_run_simulation",

        "requested_action": advisory["requested_action"],
        "requested_command": advisory["requested_command"],
        "requested_command_redacted": advisory["requested_command_redacted"],
        "requested_files": advisory.get("requested_files", []),

        "broker_decision": advisory["broker_decision"],
        "shell_gate_decision": advisory.get("shell_gate_decision"),
        "shell_gate_category": advisory.get("shell_gate_category"),
        "simulation_decision": decision,

        "simulation_severity": severity,
        "simulation_severity_label": severity_labels.get(severity, "UNKNOWN"),
        "simulation_recommendation": advisory["advisory_recommendation"],
        "enforcement_would_apply": advisory["would_block"] or advisory["would_deny"],

        "would_allow_read_only": advisory["would_allow_read_only"],
        "would_allow_governed_preflight_only": advisory["would_allow_governed_preflight_only"],
        "would_require_active_task": advisory["would_require_active_task"],
        "would_require_preflight": advisory["would_require_preflight"],
        "would_require_human_review": advisory["would_require_human_review"],
        "would_require_more_evidence": advisory["would_require_more_evidence"],
        "would_block": advisory["would_block"],
        "would_deny": advisory["would_deny"],

        "hard_block_present": advisory["hard_block_present"],
        "hard_block_reason": advisory.get("hard_block_reason"),
        "hard_block_source": advisory.get("hard_block_source"),
        "human_approval_relevant": advisory["human_approval_relevant"],
        "human_approval_would_change_outcome": advisory["human_approval_would_change_outcome"],
        "accepted_risk_relevant": advisory["accepted_risk_relevant"],
        "human_approval_cannot_override_hard_block": True,

        "redaction_applied": advisory["redaction_applied"],
        "redaction_reason": advisory.get("redaction_reason"),
        "safe_to_display": advisory["safe_to_display"],

        "operator_message": advisory["operator_message"],
        "next_required_action": advisory["next_required_action"],
        "governed_alternative": governed_alt,
        "enforcement_readiness": enforcement_readiness,

        "authorization_granted": False,
        "execution_authorized": False,
        "command_executed": False,
        "enforcement_applied": False,
        "shell_intercepted": False,
        "wrapper_installed": False,
        "backend_invoked": False,
        "prompt_sent": False,
        "output_captured": False,
        "intake_performed": False,
        "adoption_performed": False,

        "safety_invariants": _safety_invariants(),

        "evidence_sources": advisory.get("evidence_sources", []),
        "missing_evidence": advisory.get("missing_evidence", []),
        "warnings": advisory.get("warnings", []),
        "errors": advisory.get("errors", []),
        "known_limitations": _known_limitations(),
    }


def build_simulation_explain(decision: str) -> dict[str, Any]:
    """Build the simulation explain JSON envelope."""
    explanation = _explain_decision(decision)
    severity = _SIMULATION_SEVERITY.get(decision, "unknown")
    governed = _GOVERNED_ALTERNATIVES.get(decision)
    enforcement = _ENFORCEMENT_READINESS.get(decision, "Unknown.")
    return {
        "schema_version": "0.1",
        "simulation_decision": decision,
        "explanation": explanation,
        "valid_decision": decision in SIMULATION_DECISIONS,
        "all_decisions": list(SIMULATION_DECISIONS),
        "severity": severity,
        "governed_alternative": governed,
        "enforcement_readiness": enforcement,
    }


def build_simulation_status() -> dict[str, Any]:
    """Build the simulation status JSON envelope."""
    return {
        "schema_version": "0.1",
        "simulation_mode_available": True,
        "simulation_mode_version": "0.1",
        "implementation_status": "prototype",
        "phase": "89C",
        "enforcement_stage": "dry_run_simulation",
        "design_source": "89B",
        "invariants": {
            "no_command_execution": True,
            "no_shell_interception": True,
            "no_shell_wrappers": True,
            "no_backend_invocation": True,
            "no_prompts_or_capture": True,
            "no_authorization": True,
            "no_enforcement": True,
            "simulation_only": True,
        },
        "known_limitations": _known_limitations(),
    }
