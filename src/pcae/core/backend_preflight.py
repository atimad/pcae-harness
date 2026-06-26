from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.gate_dry_run import _detect_task_contract
from pcae.core.scope_preflight import _match_file, _SPF_POLICY_FORBIDDEN_FILES


_BPF_KNOWN_BACKENDS: tuple[str, ...] = (
    "claude",
    "claude-deepseek",
    "claude-kimi",
    "codex",
    "subagent",
)

_BPF_KNOWN_ACTIONS: tuple[str, ...] = (
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

_BPF_PROMPT_REQUIRED_ACTIONS: tuple[str, ...] = (
    "docs_mutation",
    "source_mutation",
    "test_mutation",
    "adoption",
    "backend_invocation",
)

_BPF_FILE_RELATED_ACTIONS: tuple[str, ...] = (
    "read",
    "docs_mutation",
    "source_mutation",
    "test_mutation",
    "adoption",
)

_BPF_GOVERNANCE_BOUNDARIES: dict[str, bool] = {
    "backend_preflight_only": True,
    "backend_preflight_does_not_invoke_backends": True,
    "backend_preflight_does_not_send_prompts": True,
    "backend_preflight_does_not_capture_outputs": True,
    "backend_preflight_does_not_perform_intake": True,
    "backend_preflight_does_not_perform_adoption": True,
    "backend_preflight_does_not_mutate_repo": True,
    "backend_preflight_does_not_commit": True,
    "backend_preflight_does_not_push": True,
    "backend_preflight_does_not_write_storage": True,
    "backend_preflight_does_not_intercept_shell": True,
    "scope_preflight_is_separate": True,
    "permission_broker_not_implemented": True,
    "shell_gate_not_implemented": True,
    "storage_not_implemented": True,
}


def _evaluate_scope_for_files(
    requested_files: list[str],
    task_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    if not task_contract or not requested_files:
        return {
            "scope_evaluated": False,
            "scope_decision": None,
            "matched_allowed": [],
            "matched_forbidden": [],
            "unknown": requested_files,
        }

    allowed_patterns = task_contract["allowed_files"]
    task_forbidden = list(task_contract["forbidden_files"])
    policy_additions = [f for f in _SPF_POLICY_FORBIDDEN_FILES if f not in task_forbidden]
    forbidden_patterns = task_forbidden + policy_additions
    matched_allowed: list[str] = []
    matched_forbidden: list[str] = []
    unknown: list[str] = []

    for rf in requested_files:
        if _match_file(rf, forbidden_patterns):
            matched_forbidden.append(rf)
        elif _match_file(rf, allowed_patterns):
            matched_allowed.append(rf)
        else:
            unknown.append(rf)

    if matched_forbidden:
        decision = "denied"
    elif unknown:
        decision = "partial"
    elif matched_allowed:
        decision = "allowed"
    else:
        decision = None

    return {
        "scope_evaluated": True,
        "scope_decision": decision,
        "matched_allowed": matched_allowed,
        "matched_forbidden": matched_forbidden,
        "unknown": unknown,
    }


def _evaluate_backend_preflight(
    requested_backend: str,
    requested_action: str,
    requested_files: list[str],
    prompt_present: bool,
    prompt_hash: str | None,
    task_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    backend_known = requested_backend in _BPF_KNOWN_BACKENDS
    is_known_action = requested_action in _BPF_KNOWN_ACTIONS
    prompt_required = requested_action in _BPF_PROMPT_REQUIRED_ACTIONS
    is_file_related = requested_action in _BPF_FILE_RELATED_ACTIONS
    scope_preflight_required = is_file_related and bool(requested_files)
    prompt_hash_present = prompt_hash is not None and prompt_hash != ""
    prompt_hash_required = prompt_present

    scope_result = _evaluate_scope_for_files(requested_files, task_contract)
    scope_decision = scope_result["scope_decision"]

    reason_codes: list[str] = []
    human_review_required = True
    more_evidence_required = False

    if backend_known:
        reason_codes.append("backend_known")
    else:
        reason_codes.append("backend_unknown")

    if task_contract:
        reason_codes.append("task_contract_detected")
    else:
        reason_codes.append("missing_task_contract")

    if prompt_present:
        reason_codes.append("prompt_present")
    elif prompt_required:
        reason_codes.append("missing_prompt")

    if prompt_hash_present:
        reason_codes.append("prompt_hash_present")
    elif prompt_present and prompt_hash_required:
        reason_codes.append("missing_prompt_hash")

    if scope_preflight_required:
        reason_codes.append("scope_preflight_required")
        if scope_decision == "allowed":
            reason_codes.append("scope_preflight_allowed")
        elif scope_decision == "denied":
            reason_codes.append("scope_preflight_denied")
        elif scope_decision is None:
            reason_codes.append("scope_preflight_missing")

    if not backend_known:
        decision = "deny_preflight"
        reason_codes.append("human_review_required")
    elif not task_contract:
        decision = "blocked_by_missing_task_contract"
        more_evidence_required = True
        reason_codes.append("more_evidence_required")
    elif not is_known_action or requested_action == "unknown":
        decision = "requires_human_review"
        reason_codes.append("unknown_action")
        reason_codes.append("human_review_required")
    elif prompt_required and not prompt_present:
        decision = "blocked_by_missing_prompt"
        more_evidence_required = True
        reason_codes.append("more_evidence_required")
    elif prompt_present and not prompt_hash_present:
        decision = "requires_more_evidence"
        more_evidence_required = True
        reason_codes.append("more_evidence_required")
    elif scope_preflight_required and scope_decision == "denied":
        decision = "blocked_by_scope"
        reason_codes.append("human_review_required")
    elif scope_preflight_required and scope_decision is None:
        decision = "requires_more_evidence"
        more_evidence_required = True
        reason_codes.append("scope_preflight_missing")
        reason_codes.append("more_evidence_required")
    else:
        decision = "requires_human_review"
        reason_codes.append("human_review_required")

    reason_codes.append("backend_preflight_only_not_execution_authorization")

    notes_parts = [
        f"decision={decision}",
        f"backend={requested_backend}",
        f"action={requested_action}",
        f"prompt_present={prompt_present}",
        f"backend_known={backend_known}",
    ]

    return {
        "preflight_type": "backend_invocation_preflight",
        "requested_backend": requested_backend,
        "requested_action": requested_action,
        "requested_files": requested_files,
        "decision": decision,
        "reason_codes": reason_codes,
        "backend_known": backend_known,
        "backend_allowed_by_policy": False,
        "prompt_present": prompt_present,
        "prompt_required": prompt_required,
        "prompt_hash_present": prompt_hash_present,
        "prompt_hash_required": prompt_hash_required,
        "scope_preflight_required": scope_preflight_required,
        "scope_preflight_decision": scope_decision,
        "human_review_required": human_review_required,
        "more_evidence_required": more_evidence_required,
        "task_contract_detected": task_contract is not None,
        "task_contract_path": task_contract["path"] if task_contract else None,
        "lifecycle_state": "active" if task_contract else "unknown",
        "evidence_sources": [task_contract["path"]] if task_contract else [],
        "backend_notes": ", ".join(notes_parts),
        "authorization_granted": False,
        "execution_authorized": False,
        "backend_invocation_performed": False,
        "prompt_sent": False,
        "capture_performed": False,
        "repo_mutation_performed": False,
        "storage_written": False,
    }


def build_backend_preflight(
    repo_root: Path,
    requested_backend: str,
    requested_action: str,
    requested_files: list[str],
    prompt_present: bool = False,
    prompt_hash: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    task_contract = _detect_task_contract(repo_root)
    preflight = _evaluate_backend_preflight(
        requested_backend, requested_action, requested_files,
        prompt_present, prompt_hash, task_contract,
    )

    if not task_contract:
        warnings.append("no active task contract detected")
    if requested_backend not in _BPF_KNOWN_BACKENDS:
        warnings.append(f"unknown backend: {requested_backend}")

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae preflight backend",
        "repository_root": str(repo_root),
        "preflight": preflight,
        "warnings": warnings,
        "errors": errors,
        "safety_notes": dict(_BPF_GOVERNANCE_BOUNDARIES),
    }
