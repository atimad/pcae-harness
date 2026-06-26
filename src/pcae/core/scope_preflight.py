from __future__ import annotations

import fnmatch
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.gate_dry_run import _detect_task_contract


_SPF_KNOWN_ACTIONS: tuple[str, ...] = (
    "read",
    "docs_mutation",
    "source_mutation",
    "test_mutation",
    "adoption",
    "backend_invocation",
    "commit",
    "push",
    "rollback",
    "storage_write",
    "unknown",
)

_SPF_SCOPE_ONLY_ACTIONS: tuple[str, ...] = (
    "read",
    "docs_mutation",
    "source_mutation",
    "test_mutation",
)

_SPF_NOT_SCOPE_DECIDABLE_ACTIONS: tuple[str, ...] = (
    "adoption",
    "backend_invocation",
    "commit",
    "push",
    "rollback",
    "storage_write",
)

_SPF_DECISION_VALUES: tuple[str, ...] = (
    "allow_preflight",
    "deny_preflight",
    "requires_human_review",
    "requires_more_evidence",
    "blocked_by_scope",
    "blocked_by_lifecycle_state",
    "blocked_by_missing_task_contract",
    "blocked_by_must_never_repeat_control",
    "blocked_by_risk",
    "unknown",
)

# Files that PCAE policy always forbids, independent of the active task contract.
# These protect documents that agents must never modify regardless of task scope.
_SPF_POLICY_FORBIDDEN_FILES: tuple[str, ...] = (
    "README.md",
    "docs/REAL_CAPTURED_TASKS.md",
    "docs/LINKEDIN_ARTICLE_DRAFT.md",
)

_SPF_GOVERNANCE_BOUNDARIES: dict[str, bool] = {
    "scope_preflight_only": True,
    "scope_preflight_does_not_intercept_shell": True,
    "scope_preflight_does_not_authorize_execution": True,
    "scope_preflight_does_not_invoke_backends": True,
    "scope_preflight_does_not_send_prompts": True,
    "scope_preflight_does_not_capture_outputs": True,
    "scope_preflight_does_not_perform_intake": True,
    "scope_preflight_does_not_perform_adoption": True,
    "scope_preflight_does_not_mutate_repo": True,
    "scope_preflight_does_not_commit": True,
    "scope_preflight_does_not_push": True,
    "scope_preflight_does_not_write_storage": True,
    "permission_broker_not_implemented": True,
    "shell_gate_not_implemented": True,
    "storage_not_implemented": True,
}


def _match_file(filepath: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if filepath == pat:
            return True
        if fnmatch.fnmatch(filepath, pat):
            return True
        stripped = pat.rstrip("*")
        if stripped and stripped.endswith("/") and filepath.startswith(stripped):
            return True
        if stripped and not stripped.endswith("/") and filepath.startswith(stripped):
            return True
    return False


def _evaluate_preflight(
    requested_action: str,
    requested_files: list[str],
    task_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    if not task_contract:
        return {
            "preflight_type": "scope_gate_preflight",
            "requested_action": requested_action,
            "requested_files": requested_files,
            "decision": "blocked_by_missing_task_contract",
            "reason_codes": ["missing_task_contract"],
            "task_contract_detected": False,
            "task_contract_path": None,
            "lifecycle_state": "unknown",
            "allowed_files": [],
            "forbidden_files": [],
            "matched_allowed_files": [],
            "matched_forbidden_files": [],
            "unknown_files": requested_files,
            "human_review_required": False,
            "more_evidence_required": True,
            "evidence_sources": [],
            "scope_notes": "no active task contract detected",
            "authorization_granted": False,
            "execution_authorized": False,
            "repo_mutation_performed": False,
            "storage_written": False,
            "backend_invocation_performed": False,
        }

    allowed_patterns = task_contract["allowed_files"]
    # Merge task forbidden list with PCAE policy-protected files.
    # Policy files are always forbidden regardless of the active task contract.
    task_forbidden = list(task_contract["forbidden_files"])
    policy_additions = [f for f in _SPF_POLICY_FORBIDDEN_FILES if f not in task_forbidden]
    forbidden_patterns = task_forbidden + policy_additions

    matched_allowed: list[str] = []
    matched_forbidden: list[str] = []
    unknown: list[str] = []

    for rf in requested_files:
        is_forbidden = _match_file(rf, forbidden_patterns)
        is_allowed = _match_file(rf, allowed_patterns)
        if is_forbidden:
            matched_forbidden.append(rf)
        elif is_allowed:
            matched_allowed.append(rf)
        else:
            unknown.append(rf)

    is_known_action = requested_action in _SPF_KNOWN_ACTIONS
    is_scope_decidable = requested_action in _SPF_SCOPE_ONLY_ACTIONS
    is_not_scope_decidable = requested_action in _SPF_NOT_SCOPE_DECIDABLE_ACTIONS

    reason_codes: list[str] = []
    human_review_required = False
    more_evidence_required = False

    if not is_known_action or requested_action == "unknown":
        decision = "requires_human_review"
        reason_codes.append("unknown_action")
        reason_codes.append("human_review_required")
        human_review_required = True
    elif is_not_scope_decidable:
        decision = "requires_human_review"
        reason_codes.append("human_review_required")
        reason_codes.append(f"{requested_action}_not_scope_decidable")
        human_review_required = True
    elif matched_forbidden:
        if matched_allowed or unknown:
            decision = "deny_preflight"
            reason_codes.append("forbidden_file_requested")
            if matched_allowed:
                reason_codes.append("scope_allowed")
            if unknown:
                reason_codes.append("unknown_file_scope")
        else:
            decision = "blocked_by_scope"
            reason_codes.append("forbidden_file_requested")
    elif unknown and not matched_allowed:
        decision = "requires_more_evidence"
        reason_codes.append("unknown_file_scope")
        reason_codes.append("more_evidence_required")
        more_evidence_required = True
    elif unknown and matched_allowed:
        decision = "requires_human_review"
        reason_codes.append("scope_allowed")
        reason_codes.append("unknown_file_scope")
        reason_codes.append("human_review_required")
        human_review_required = True
    elif not requested_files:
        decision = "requires_more_evidence"
        reason_codes.append("more_evidence_required")
        more_evidence_required = True
    elif matched_allowed and not matched_forbidden and not unknown:
        decision = "allow_preflight"
        reason_codes.append("scope_allowed")
    else:
        decision = "requires_more_evidence"
        reason_codes.append("more_evidence_required")
        more_evidence_required = True

    reason_codes.append("preflight_only_not_execution_authorization")

    scope_notes_parts = [
        f"decision={decision}",
        f"requested_action={requested_action}",
        f"files_requested={len(requested_files)}",
        f"allowed_matched={len(matched_allowed)}",
        f"forbidden_matched={len(matched_forbidden)}",
        f"unknown={len(unknown)}",
    ]

    return {
        "preflight_type": "scope_gate_preflight",
        "requested_action": requested_action,
        "requested_files": requested_files,
        "decision": decision,
        "reason_codes": reason_codes,
        "task_contract_detected": True,
        "task_contract_path": task_contract["path"],
        "lifecycle_state": "active",
        "allowed_files": list(allowed_patterns),
        "forbidden_files": list(forbidden_patterns),
        "matched_allowed_files": matched_allowed,
        "matched_forbidden_files": matched_forbidden,
        "unknown_files": unknown,
        "human_review_required": human_review_required,
        "more_evidence_required": more_evidence_required,
        "evidence_sources": [task_contract["path"]],
        "scope_notes": ", ".join(scope_notes_parts),
        "authorization_granted": False,
        "execution_authorized": False,
        "repo_mutation_performed": False,
        "storage_written": False,
        "backend_invocation_performed": False,
    }


def build_scope_preflight(
    repo_root: Path,
    requested_action: str,
    requested_files: list[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    task_contract = _detect_task_contract(repo_root)
    preflight = _evaluate_preflight(requested_action, requested_files, task_contract)

    if not task_contract:
        warnings.append("no active task contract detected")

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae preflight scope",
        "repository_root": str(repo_root),
        "preflight": preflight,
        "warnings": warnings,
        "errors": errors,
        "safety_notes": dict(_SPF_GOVERNANCE_BOUNDARIES),
    }
