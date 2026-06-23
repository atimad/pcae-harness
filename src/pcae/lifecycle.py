"""Lifecycle state machine for backend-output-adoption (Phase 80A).

Read-only state model. Derives current lifecycle state from artifact
presence. Does not mutate state, invoke backends, or run gates.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LifecycleState:
    state_id: str
    label: str
    description: str
    artifact_dir: str
    artifact_status_field: str
    artifact_status_value: str
    approval_required: bool
    execution_boundary: bool
    allowed_next_actions: tuple[str, ...]


LIFECYCLE_STATES: dict[str, LifecycleState] = {
    "idle": LifecycleState(
        "idle", "Idle", "No active backend-output-adoption lifecycle.",
        "", "", "", False, False,
        ("start_backend_capture",),
    ),
    "backend_capture_attempted": LifecycleState(
        "backend_capture_attempted", "Backend Capture Attempted",
        "Backend capture was attempted; result intake needed.",
        "real-backend-capture-result-intakes", "outcome", "",
        False, False, ("classify_mutation_result",),
    ),
    "mutation_detected": LifecycleState(
        "mutation_detected", "Mutation Detected",
        "Backend execution produced a repo mutation.",
        "backend-retry-mutation-result-intakes", "outcome", "repo_mutation_detected_with_output",
        False, False, ("quarantine_review",),
    ),
    "quarantined": LifecycleState(
        "quarantined", "Quarantined",
        "Backend-created output is quarantined and ready for review.",
        "backend-created-output-quarantine-reviews", "backend_created_output_quarantine_review_status", "reviewed_quarantined_output",
        False, False, ("adoption_preflight",),
    ),
    "adoption_review_ready": LifecycleState(
        "adoption_review_ready", "Adoption Review Ready",
        "Adoption preflight passed; content review needed.",
        "backend-created-output-adoption-preflights", "backend_created_output_adoption_preflight_status", "ready_for_adoption_review",
        False, False, ("adoption_review",),
    ),
    "adoption_reviewed": LifecycleState(
        "adoption_reviewed", "Adoption Reviewed",
        "Content safety review passed; operator approval needed.",
        "backend-created-output-adoption-reviews", "backend_created_output_adoption_review_status", "reviewed_adoption_candidate",
        True, False, ("adoption_approval",),
    ),
    "adoption_approved": LifecycleState(
        "adoption_approved", "Adoption Approved",
        "Operator approved adoption; execution preflight needed.",
        "backend-created-output-adoption-approvals", "backend_created_output_adoption_approval_status", "approved",
        False, False, ("execution_preflight",),
    ),
    "adoption_execution_ready": LifecycleState(
        "adoption_execution_ready", "Execution Ready",
        "Execution preflight passed; staging can proceed.",
        "backend-created-output-adoption-execution-preflights", "backend_created_output_adoption_execution_preflight_status", "ready_for_adoption_execution",
        False, True, ("adoption_execution",),
    ),
    "staged_for_commit": LifecycleState(
        "staged_for_commit", "Staged for Commit",
        "File staged via git add; commit approval needed.",
        "backend-created-output-adoption-executions", "backend_created_output_adoption_execution_status", "staged_for_future_commit",
        True, False, ("commit_approval",),
    ),
    "commit_approved": LifecycleState(
        "commit_approved", "Commit Approved",
        "Commit approved; commit execution can proceed.",
        "backend-created-output-adoption-commit-approvals", "backend_created_output_adoption_commit_approval_status", "approved",
        False, True, ("commit_execution",),
    ),
    "committed_for_push": LifecycleState(
        "committed_for_push", "Committed for Push",
        "Adoption committed; hook-bypass reconciliation or push approval needed.",
        "backend-created-output-adoption-commit-executions", "backend_created_output_adoption_commit_execution_status", "committed_for_future_push",
        False, False, ("hook_bypass_reconciliation", "push_approval"),
    ),
    "hook_bypass_reconciled": LifecycleState(
        "hook_bypass_reconciled", "Hook Bypass Reconciled",
        "Hook bypass reconciled; push approval needed.",
        "adoption-commit-hook-bypass-reconciliations", "hook_bypass_reconciliation_status", "reconciled_documented_exception",
        True, False, ("push_approval",),
    ),
    "push_approved": LifecycleState(
        "push_approved", "Push Approved",
        "Push approved; push execution can proceed.",
        "backend-created-output-adoption-push-approvals", "backend_created_output_adoption_push_approval_status", "approved",
        False, True, ("push_execution",),
    ),
    "pushed": LifecycleState(
        "pushed", "Pushed",
        "Adoption bundle pushed; final verification needed.",
        "backend-created-output-adoption-push-executions", "backend_created_output_adoption_push_execution_status", "pushed",
        False, False, ("final_verification",),
    ),
    "final_verified": LifecycleState(
        "final_verified", "Final Verified",
        "Lifecycle verified; tooling closure may be needed.",
        "backend-created-output-adoption-final-verifications", "backend_created_output_adoption_final_verification_status", "verified",
        False, False, ("tooling_closure",),
    ),
    "closed": LifecycleState(
        "closed", "Closed",
        "Lifecycle complete. No further adoption actions required.",
        "final-verification-tooling-push-decisions", "final_verification_tooling_push_decision_status", "pushed_77v_tooling",
        False, False, ("start_new_lifecycle",),
    ),
    "blocked": LifecycleState(
        "blocked", "Blocked",
        "Lifecycle is blocked by governance issues.",
        "", "", "", False, False, ("resolve_blockers",),
    ),
}

# Ordered from most advanced to least for state detection
_DETECTION_ORDER = [
    "closed", "final_verified", "pushed", "push_approved",
    "hook_bypass_reconciled", "committed_for_push", "commit_approved",
    "staged_for_commit", "adoption_execution_ready", "adoption_approved",
    "adoption_reviewed", "adoption_review_ready", "quarantined",
    "mutation_detected", "backend_capture_attempted",
]


def detect_lifecycle_state(root_path: Path) -> tuple[str, dict[str, Any]]:
    """Detect current lifecycle state from artifacts. Returns (state_id, details)."""
    pcae_dir = root_path / ".pcae"
    detected: dict[str, str] = {}
    artifact_summary: dict[str, bool] = {}

    for state_id in _DETECTION_ORDER:
        state = LIFECYCLE_STATES[state_id]
        if not state.artifact_dir:
            continue
        artifact_path = pcae_dir / state.artifact_dir / "latest.json"
        present = artifact_path.is_file()
        artifact_summary[state.artifact_dir] = present

        if present and state.artifact_status_field:
            try:
                data = json.loads(artifact_path.read_text(encoding="utf-8"))
                actual = data.get(state.artifact_status_field, "")
                if actual == state.artifact_status_value:
                    detected[state_id] = actual
            except (json.JSONDecodeError, OSError):
                pass

    # Find the most advanced state
    for state_id in _DETECTION_ORDER:
        if state_id in detected:
            return state_id, {
                "detected_artifacts": detected,
                "artifact_summary": artifact_summary,
            }

    return "idle", {
        "detected_artifacts": detected,
        "artifact_summary": artifact_summary,
    }


def get_next_recommendation(state_id: str) -> dict[str, Any]:
    """Get advisory next-step recommendation for the given state."""
    state = LIFECYCLE_STATES.get(state_id, LIFECYCLE_STATES["blocked"])
    actions = state.allowed_next_actions

    if state_id == "idle":
        return {
            "recommended_next_action": "start_backend_capture" if actions else "none",
            "recommended_next_phase": "81A — Second Real Captured Task Selection",
            "reason": "No active lifecycle. Start a new backend-output-adoption lifecycle or continue roadmap.",
            "required_approval": False,
            "required_preconditions": ["task contract", "backend lock", "clean working tree"],
        }

    if state_id == "closed":
        return {
            "recommended_next_action": "start_new_lifecycle",
            "recommended_next_phase": "80D — Lifecycle Gate Runner Dry-Run (roadmap continuation)",
            "reason": "Lifecycle is closed. Repository is clean. Continue with roadmap or start second real task.",
            "required_approval": False,
            "required_preconditions": [],
        }

    if state_id == "blocked":
        return {
            "recommended_next_action": "resolve_blockers",
            "recommended_next_phase": None,
            "reason": "Lifecycle is blocked. Resolve governance issues before proceeding.",
            "required_approval": False,
            "required_preconditions": ["resolve all blockers"],
        }

    action_to_phase = {
        "classify_mutation_result": "77K — Mutation Result Intake",
        "quarantine_review": "77L — Quarantine Review",
        "adoption_preflight": "77M — Adoption Preflight",
        "adoption_review": "77N — Adoption Review",
        "adoption_approval": "77O — Adoption Approval",
        "execution_preflight": "77P — Execution Preflight",
        "adoption_execution": "77Q — Adoption Execution",
        "commit_approval": "77R — Commit Approval",
        "commit_execution": "77S — Commit Execution",
        "hook_bypass_reconciliation": "77S.1 — Hook Bypass Reconciliation",
        "push_approval": "77T — Push Approval",
        "push_execution": "77U — Push Execution",
        "final_verification": "77V — Final Verification",
        "tooling_closure": "77V.1 — Tooling Closure",
    }

    next_action = actions[0] if actions else "none"
    return {
        "recommended_next_action": next_action,
        "recommended_next_phase": action_to_phase.get(next_action),
        "reason": f"Current state is '{state.label}'. Next governed action: {next_action}.",
        "required_approval": state.approval_required,
        "required_preconditions": [f"artifact: {state.artifact_dir}"] if state.artifact_dir else [],
    }
