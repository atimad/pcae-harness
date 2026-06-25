from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.gate_dry_run import _detect_task_contract
from pcae.core.scope_preflight import _match_file
from pcae.core.backend_preflight import _BPF_KNOWN_BACKENDS


_MPF_MUTATION_ACTIONS: tuple[str, ...] = (
    "docs_mutation",
    "source_mutation",
    "test_mutation",
    "generated_artifact_mutation",
)

_MPF_ADOPTION_ACTIONS: tuple[str, ...] = (
    "captured_output_review",
    "captured_output_adoption",
    "adoption_review",
    "adoption_approval",
    "adoption_execution",
)

_MPF_KNOWN_ACTIONS: tuple[str, ...] = (
    *_MPF_MUTATION_ACTIONS,
    *_MPF_ADOPTION_ACTIONS,
    "unknown_mutation_action",
    "unknown",
)

_MPF_FILE_ACTIONS: tuple[str, ...] = (
    "docs_mutation",
    "source_mutation",
    "test_mutation",
    "generated_artifact_mutation",
    "captured_output_adoption",
)

_MPF_CAPTURE_REQUIRED_ACTIONS: tuple[str, ...] = (
    "captured_output_review",
    "captured_output_adoption",
    "adoption_review",
)

_MPF_REVIEW_REQUIRED_ACTIONS: tuple[str, ...] = (
    "adoption_approval",
)

_MPF_APPROVAL_REQUIRED_ACTIONS: tuple[str, ...] = (
    "adoption_execution",
)

_MPF_GOVERNANCE_BOUNDARIES: dict[str, bool] = {
    "mutation_preflight_only": True,
    "mutation_preflight_does_not_mutate_files": True,
    "mutation_preflight_does_not_apply_output": True,
    "mutation_preflight_does_not_perform_adoption_review": True,
    "mutation_preflight_does_not_grant_adoption_approval": True,
    "mutation_preflight_does_not_execute_adoption": True,
    "mutation_preflight_does_not_invoke_backends": True,
    "mutation_preflight_does_not_send_prompts": True,
    "mutation_preflight_does_not_capture_outputs": True,
    "mutation_preflight_does_not_perform_intake": True,
    "mutation_preflight_does_not_commit": True,
    "mutation_preflight_does_not_push": True,
    "mutation_preflight_does_not_write_storage": True,
    "mutation_preflight_does_not_intercept_shell": True,
    "scope_preflight_is_separate": True,
    "backend_preflight_is_separate": True,
    "permission_broker_not_implemented": True,
    "shell_gate_not_implemented": True,
    "storage_not_implemented": True,
}


def _evaluate_scope_for_mutation(
    requested_files: list[str],
    task_contract: dict[str, Any] | None,
) -> str | None:
    if not task_contract or not requested_files:
        return None

    allowed_patterns = task_contract["allowed_files"]
    forbidden_patterns = task_contract["forbidden_files"]

    has_forbidden = False
    has_unknown = False

    for rf in requested_files:
        if _match_file(rf, forbidden_patterns):
            has_forbidden = True
        elif not _match_file(rf, allowed_patterns):
            has_unknown = True

    if has_forbidden:
        return "denied"
    if has_unknown:
        return "partial"
    return "allowed"


def _evaluate_mutation_preflight(
    requested_action: str,
    requested_files: list[str],
    captured_output_present: bool,
    captured_output_hash: str | None,
    diff_present: bool,
    diff_hash: str | None,
    adoption_review_present: bool,
    adoption_approval_present: bool,
    source_backend: str | None,
    task_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    is_known = requested_action in _MPF_KNOWN_ACTIONS
    is_file_action = requested_action in _MPF_FILE_ACTIONS
    is_capture_required = requested_action in _MPF_CAPTURE_REQUIRED_ACTIONS
    is_review_required = requested_action in _MPF_REVIEW_REQUIRED_ACTIONS
    is_approval_required = requested_action in _MPF_APPROVAL_REQUIRED_ACTIONS
    is_adoption = requested_action in _MPF_ADOPTION_ACTIONS

    scope_required = is_file_action and bool(requested_files)
    scope_decision = _evaluate_scope_for_mutation(requested_files, task_contract) if scope_required else None

    backend_required = source_backend is not None
    backend_known = source_backend in _BPF_KNOWN_BACKENDS if source_backend else False

    co_hash_present = captured_output_hash is not None and captured_output_hash != ""
    d_hash_present = diff_hash is not None and diff_hash != ""

    reason_codes: list[str] = []
    human_review_required = True
    more_evidence_required = False

    if task_contract:
        reason_codes.append("task_contract_detected")
    else:
        reason_codes.append("missing_task_contract")

    if scope_required:
        reason_codes.append("scope_preflight_required")
        if scope_decision == "allowed":
            reason_codes.append("scope_preflight_allowed")
        elif scope_decision == "denied":
            reason_codes.append("scope_preflight_denied")
        elif scope_decision is None:
            reason_codes.append("scope_preflight_missing")

    if backend_required:
        reason_codes.append("backend_preflight_required")
        if backend_known:
            reason_codes.append("backend_preflight_present")
        else:
            reason_codes.append("backend_preflight_missing")

    if is_capture_required or is_adoption:
        reason_codes.append("captured_output_required")
        if captured_output_present:
            reason_codes.append("captured_output_present")
            if co_hash_present:
                reason_codes.append("captured_output_hash_present")
            else:
                reason_codes.append("missing_captured_output_hash")
        else:
            reason_codes.append("missing_captured_output")

    if is_file_action and diff_present:
        reason_codes.append("diff_present")
        if d_hash_present:
            reason_codes.append("diff_hash_present")
        else:
            reason_codes.append("missing_diff_hash")

    if is_review_required:
        reason_codes.append("adoption_review_required")
        if adoption_review_present:
            reason_codes.append("adoption_review_present")
        else:
            reason_codes.append("missing_adoption_review")

    if is_approval_required:
        reason_codes.append("adoption_review_required")
        reason_codes.append("adoption_approval_required")
        if adoption_review_present:
            reason_codes.append("adoption_review_present")
        else:
            reason_codes.append("missing_adoption_review")
        if adoption_approval_present:
            reason_codes.append("adoption_approval_present")
        else:
            reason_codes.append("missing_adoption_approval")

    if not task_contract:
        decision = "blocked_by_missing_task_contract"
        more_evidence_required = True
    elif not is_known or requested_action in ("unknown_mutation_action", "unknown"):
        decision = "requires_human_review"
        reason_codes.append("unknown_action")
    elif scope_required and scope_decision == "denied":
        decision = "blocked_by_scope"
    elif scope_required and scope_decision is None:
        decision = "requires_more_evidence"
        more_evidence_required = True
        reason_codes.append("more_evidence_required")
    elif is_capture_required and not captured_output_present:
        decision = "blocked_by_missing_capture"
        more_evidence_required = True
    elif is_adoption and not captured_output_present and requested_action in (
        "captured_output_adoption",
    ):
        decision = "blocked_by_missing_capture"
        more_evidence_required = True
    elif captured_output_present and not co_hash_present and (is_capture_required or is_adoption):
        decision = "requires_more_evidence"
        more_evidence_required = True
        reason_codes.append("more_evidence_required")
    elif is_review_required and not adoption_review_present:
        decision = "blocked_by_missing_adoption_review"
        more_evidence_required = True
    elif is_approval_required and not adoption_review_present:
        decision = "blocked_by_missing_adoption_review"
        more_evidence_required = True
    elif is_approval_required and not adoption_approval_present:
        decision = "blocked_by_missing_adoption_approval"
        more_evidence_required = True
    elif backend_required and not backend_known:
        decision = "requires_more_evidence"
        more_evidence_required = True
        reason_codes.append("more_evidence_required")
    else:
        decision = "requires_human_review"

    reason_codes.append("human_review_required")
    reason_codes.append("mutation_preflight_only_not_execution_authorization")

    if scope_required and scope_decision == "allowed":
        reason_codes.append("scope_allow_not_mutation_authorization")
    if captured_output_present:
        reason_codes.append("captured_output_not_adoption_authorization")
    if adoption_review_present and is_review_required:
        reason_codes.append("adoption_review_not_approval")
    if adoption_approval_present and is_approval_required:
        reason_codes.append("adoption_approval_not_execution")

    return {
        "preflight_type": "mutation_adoption_preflight",
        "requested_action": requested_action,
        "requested_files": requested_files,
        "decision": decision,
        "reason_codes": reason_codes,
        "task_contract_detected": task_contract is not None,
        "task_contract_path": task_contract["path"] if task_contract else None,
        "lifecycle_state": "active" if task_contract else "unknown",
        "scope_preflight_required": scope_required,
        "scope_preflight_decision": scope_decision,
        "backend_preflight_required": backend_required,
        "backend_preflight_decision": "known" if backend_known else ("unknown" if source_backend else None),
        "captured_output_required": is_capture_required or (is_adoption and requested_action == "captured_output_adoption"),
        "captured_output_present": captured_output_present,
        "captured_output_hash_present": co_hash_present,
        "diff_required": False,
        "diff_present": diff_present,
        "diff_hash_present": d_hash_present,
        "adoption_review_required": is_review_required or is_approval_required,
        "adoption_review_present": adoption_review_present,
        "adoption_approval_required": is_approval_required,
        "adoption_approval_present": adoption_approval_present,
        "human_review_required": human_review_required,
        "more_evidence_required": more_evidence_required,
        "evidence_sources": [task_contract["path"]] if task_contract else [],
        "mutation_notes": f"decision={decision}, action={requested_action}",
        "authorization_granted": False,
        "execution_authorized": False,
        "mutation_performed": False,
        "adoption_review_performed": False,
        "adoption_approval_granted": False,
        "adoption_execution_performed": False,
        "backend_invocation_performed": False,
        "prompt_sent": False,
        "capture_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "repo_mutation_performed": False,
        "storage_written": False,
    }


def build_mutation_preflight(
    repo_root: Path,
    requested_action: str,
    requested_files: list[str],
    captured_output_present: bool = False,
    captured_output_hash: str | None = None,
    diff_present: bool = False,
    diff_hash: str | None = None,
    adoption_review_present: bool = False,
    adoption_approval_present: bool = False,
    source_backend: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    task_contract = _detect_task_contract(repo_root)
    preflight = _evaluate_mutation_preflight(
        requested_action, requested_files,
        captured_output_present, captured_output_hash,
        diff_present, diff_hash,
        adoption_review_present, adoption_approval_present,
        source_backend, task_contract,
    )

    if not task_contract:
        warnings.append("no active task contract detected")

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae preflight mutation",
        "repository_root": str(repo_root),
        "preflight": preflight,
        "warnings": warnings,
        "errors": errors,
        "safety_notes": dict(_MPF_GOVERNANCE_BOUNDARIES),
    }
