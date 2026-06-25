from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.gate_dry_run import _detect_task_contract


_CPF_COMMIT_ACTIONS: tuple[str, ...] = (
    "commit_preflight", "commit_message_review", "commit_creation",
    "commit_lineage_check",
)

_CPF_PUSH_ACTIONS: tuple[str, ...] = (
    "push_preflight", "push_check", "push_execution",
    "raw_git_push_attempt", "force_push_attempt",
)

_CPF_KNOWN_ACTIONS: tuple[str, ...] = (
    *_CPF_COMMIT_ACTIONS, *_CPF_PUSH_ACTIONS,
    "unknown_commit_push_action", "unknown",
)

_CPF_COMMIT_SAFETY: dict[str, bool] = {
    "commit_push_preflight_only": True,
    "commit_preflight_does_not_create_commits": True,
    "push_preflight_does_not_push": True,
    "push_preflight_does_not_raw_git_push": True,
    "push_preflight_does_not_force_push": True,
    "commit_push_preflight_does_not_stage_files": True,
    "commit_push_preflight_does_not_mutate_repo": True,
    "commit_push_preflight_does_not_invoke_backends": True,
    "commit_push_preflight_does_not_send_prompts": True,
    "commit_push_preflight_does_not_capture_outputs": True,
    "commit_push_preflight_does_not_perform_intake": True,
    "commit_push_preflight_does_not_perform_adoption": True,
    "commit_push_preflight_does_not_write_storage": True,
    "commit_push_preflight_does_not_intercept_shell": True,
    "pcae_push_remains_governed_push_path": True,
    "raw_git_push_forbidden": True,
    "force_push_forbidden": True,
    "permission_broker_not_implemented": True,
    "shell_gate_not_implemented": True,
    "storage_not_implemented": True,
}


def _git_branch(repo_root: Path) -> str | None:
    try:
        r = subprocess.run(["git", "branch", "--show-current"],
                           capture_output=True, text=True, cwd=repo_root, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _git_head(repo_root: Path) -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, cwd=repo_root, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _git_ahead_behind(repo_root: Path, target: str) -> tuple[int | None, int | None]:
    try:
        r = subprocess.run(["git", "rev-list", "--left-right", "--count", f"{target}...HEAD"],
                           capture_output=True, text=True, cwd=repo_root, timeout=10)
        if r.returncode == 0:
            parts = r.stdout.strip().split()
            if len(parts) == 2:
                return int(parts[1]), int(parts[0])
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None, None


def _safety_fields() -> dict[str, Any]:
    return {
        "authorization_granted": False,
        "execution_authorized": False,
        "commit_performed": False,
        "push_performed": False,
        "raw_git_push_performed": False,
        "force_push_performed": False,
        "repo_mutation_performed": False,
        "storage_written": False,
    }


def _evaluate_commit_preflight(
    requested_action: str,
    commit_message: str | None,
    diff_present: bool,
    tests_present: bool,
    tests_passed: bool,
    pcae_check_passed: bool,
    pcae_health_passed: bool,
    doctor_passed: bool,
    requested_files: list[str],
    task_contract: dict[str, Any] | None,
    repo_root: Path,
) -> dict[str, Any]:
    is_known = requested_action in _CPF_KNOWN_ACTIONS
    cm_present = commit_message is not None and commit_message != ""
    branch = _git_branch(repo_root)
    head = _git_head(repo_root)

    reason_codes: list[str] = []
    human_review_required = True
    more_evidence_required = False

    if task_contract:
        reason_codes.append("task_contract_detected")
    else:
        reason_codes.append("missing_task_contract")

    reason_codes.append("commit_message_required")
    if cm_present:
        reason_codes.append("commit_message_present")
    else:
        reason_codes.append("missing_commit_message")

    reason_codes.append("diff_required")
    if diff_present:
        reason_codes.append("diff_present")
    else:
        reason_codes.append("missing_diff")

    reason_codes.append("tests_required")
    if tests_present:
        reason_codes.append("tests_present")
        if tests_passed:
            reason_codes.append("tests_passed")
        else:
            reason_codes.append("tests_failed")
    else:
        reason_codes.append("missing_tests")

    if pcae_check_passed:
        reason_codes.append("pcae_check_passed")
    if pcae_health_passed:
        reason_codes.append("pcae_health_passed")
    if doctor_passed:
        reason_codes.append("doctor_passed")

    if not task_contract:
        decision = "blocked_by_missing_task_contract"
        more_evidence_required = True
    elif not is_known or requested_action in ("unknown_commit_push_action", "unknown"):
        decision = "requires_human_review"
        reason_codes.append("unknown_action" if not is_known else "unknown_action")
    elif not cm_present:
        decision = "blocked_by_missing_commit_message"
        more_evidence_required = True
    elif not diff_present:
        decision = "blocked_by_missing_diff"
        more_evidence_required = True
    elif tests_present and not tests_passed:
        decision = "blocked_by_failed_tests"
    elif not tests_present:
        decision = "blocked_by_missing_tests"
        more_evidence_required = True
    elif not pcae_check_passed:
        decision = "blocked_by_failed_check"
    elif not pcae_health_passed:
        decision = "blocked_by_failed_health"
    elif not doctor_passed:
        decision = "blocked_by_failed_doctor"
    else:
        decision = "requires_human_review"

    reason_codes.append("human_review_required")
    reason_codes.append("commit_preflight_only_not_execution_authorization")

    return {
        "preflight_type": "commit_preflight",
        "requested_action": requested_action,
        "decision": decision,
        "reason_codes": reason_codes,
        "task_contract_detected": task_contract is not None,
        "task_contract_path": task_contract["path"] if task_contract else None,
        "lifecycle_state": "active" if task_contract else "unknown",
        "requested_files": requested_files,
        "commit_message_required": True,
        "commit_message_present": cm_present,
        "diff_required": True,
        "diff_present": diff_present,
        "tests_required": True,
        "tests_present": tests_present,
        "tests_passed": tests_passed,
        "pcae_check_required": True,
        "pcae_check_passed": pcae_check_passed,
        "pcae_health_required": True,
        "pcae_health_passed": pcae_health_passed,
        "doctor_required": True,
        "doctor_passed": doctor_passed,
        "branch_name": branch,
        "head_commit": head,
        "human_review_required": human_review_required,
        "more_evidence_required": more_evidence_required,
        "evidence_sources": [task_contract["path"]] if task_contract else [],
        "commit_notes": f"decision={decision}, action={requested_action}",
        **_safety_fields(),
    }


def _evaluate_push_preflight(
    requested_action: str,
    push_target: str | None,
    push_check_passed: bool,
    pcae_check_passed: bool,
    pcae_health_passed: bool,
    doctor_passed: bool,
    tests_present: bool,
    tests_passed: bool,
    raw_git_push_requested: bool,
    force_push_requested: bool,
    task_contract: dict[str, Any] | None,
    repo_root: Path,
) -> dict[str, Any]:
    is_known = requested_action in _CPF_KNOWN_ACTIONS
    branch = _git_branch(repo_root)
    head = _git_head(repo_root)
    target = push_target or "origin/main"
    ahead, behind = _git_ahead_behind(repo_root, target)

    reason_codes: list[str] = []
    human_review_required = True
    more_evidence_required = False

    if task_contract:
        reason_codes.append("task_contract_detected")
    else:
        reason_codes.append("missing_task_contract")

    reason_codes.append("push_check_required")
    if push_check_passed:
        reason_codes.append("push_check_passed")
    else:
        reason_codes.append("push_check_failed")

    reason_codes.append("tests_required")
    if tests_present:
        reason_codes.append("tests_present")
        if tests_passed:
            reason_codes.append("tests_passed")
        else:
            reason_codes.append("tests_failed")
    else:
        reason_codes.append("missing_tests")

    if pcae_check_passed:
        reason_codes.append("pcae_check_passed")
    if pcae_health_passed:
        reason_codes.append("pcae_health_passed")
    if doctor_passed:
        reason_codes.append("doctor_passed")

    if raw_git_push_requested:
        reason_codes.append("raw_git_push_requested")
        reason_codes.append("raw_git_push_blocked")
    if force_push_requested:
        reason_codes.append("force_push_requested")
        reason_codes.append("force_push_blocked")

    if branch and ahead is not None:
        reason_codes.append("branch_state_known")
    else:
        reason_codes.append("branch_state_unknown")

    if raw_git_push_requested:
        decision = "blocked_by_raw_git_push"
    elif force_push_requested:
        decision = "blocked_by_force_push"
    elif not task_contract:
        decision = "blocked_by_missing_task_contract"
        more_evidence_required = True
    elif not is_known or requested_action in ("unknown_commit_push_action", "unknown"):
        decision = "requires_human_review"
        reason_codes.append("unknown_action")
    elif not push_check_passed:
        decision = "blocked_by_push_check"
    elif tests_present and not tests_passed:
        decision = "blocked_by_failed_tests"
    elif not tests_present:
        decision = "blocked_by_missing_tests"
        more_evidence_required = True
    elif not pcae_check_passed:
        decision = "blocked_by_failed_check"
    elif not pcae_health_passed:
        decision = "blocked_by_failed_health"
    elif not doctor_passed:
        decision = "blocked_by_failed_doctor"
    elif push_target is None:
        decision = "blocked_by_branch_state"
        more_evidence_required = True
    else:
        decision = "requires_human_review"

    reason_codes.append("human_review_required")
    reason_codes.append("push_preflight_only_not_execution_authorization")
    reason_codes.append("pcae_push_required_for_governed_push")

    return {
        "preflight_type": "push_preflight",
        "requested_action": requested_action,
        "decision": decision,
        "reason_codes": reason_codes,
        "task_contract_detected": task_contract is not None,
        "task_contract_path": task_contract["path"] if task_contract else None,
        "lifecycle_state": "active" if task_contract else "unknown",
        "push_target": push_target,
        "remote_name": "origin" if push_target else None,
        "remote_branch": push_target.split("/", 1)[1] if push_target and "/" in push_target else push_target,
        "branch_name": branch,
        "head_commit": head,
        "ahead_count": ahead,
        "behind_count": behind,
        "push_check_required": True,
        "push_check_passed": push_check_passed,
        "pcae_check_required": True,
        "pcae_check_passed": pcae_check_passed,
        "pcae_health_required": True,
        "pcae_health_passed": pcae_health_passed,
        "doctor_required": True,
        "doctor_passed": doctor_passed,
        "tests_required": True,
        "tests_present": tests_present,
        "tests_passed": tests_passed,
        "raw_git_push_requested": raw_git_push_requested,
        "force_push_requested": force_push_requested,
        "human_review_required": human_review_required,
        "more_evidence_required": more_evidence_required,
        "evidence_sources": [task_contract["path"]] if task_contract else [],
        "push_notes": f"decision={decision}, action={requested_action}",
        **_safety_fields(),
    }


def build_commit_preflight(
    repo_root: Path,
    requested_action: str = "commit_preflight",
    commit_message: str | None = None,
    diff_present: bool = False,
    tests_present: bool = False,
    tests_passed: bool = False,
    pcae_check_passed: bool = False,
    pcae_health_passed: bool = False,
    doctor_passed: bool = False,
    requested_files: list[str] | None = None,
) -> dict[str, Any]:
    tc = _detect_task_contract(repo_root)
    pf = _evaluate_commit_preflight(
        requested_action, commit_message, diff_present,
        tests_present, tests_passed, pcae_check_passed,
        pcae_health_passed, doctor_passed,
        requested_files or [], tc, repo_root,
    )
    warnings: list[str] = []
    if not tc:
        warnings.append("no active task contract detected")
    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae preflight commit",
        "repository_root": str(repo_root),
        "preflight": pf,
        "warnings": warnings,
        "errors": [],
        "safety_notes": dict(_CPF_COMMIT_SAFETY),
    }


def build_push_preflight(
    repo_root: Path,
    requested_action: str = "push_preflight",
    push_target: str | None = None,
    push_check_passed: bool = False,
    pcae_check_passed: bool = False,
    pcae_health_passed: bool = False,
    doctor_passed: bool = False,
    tests_present: bool = False,
    tests_passed: bool = False,
    raw_git_push_requested: bool = False,
    force_push_requested: bool = False,
) -> dict[str, Any]:
    tc = _detect_task_contract(repo_root)
    pf = _evaluate_push_preflight(
        requested_action, push_target, push_check_passed,
        pcae_check_passed, pcae_health_passed, doctor_passed,
        tests_present, tests_passed,
        raw_git_push_requested, force_push_requested,
        tc, repo_root,
    )
    warnings: list[str] = []
    if not tc:
        warnings.append("no active task contract detected")
    if raw_git_push_requested:
        warnings.append("raw git push requested — blocked by policy")
    if force_push_requested:
        warnings.append("force push requested — blocked by policy")
    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae preflight push",
        "repository_root": str(repo_root),
        "preflight": pf,
        "warnings": warnings,
        "errors": [],
        "safety_notes": dict(_CPF_COMMIT_SAFETY),
    }
