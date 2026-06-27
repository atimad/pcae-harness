from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.gate_dry_run_context import GateDryRunContext


_GATE_DEFS: list[dict[str, Any]] = [
    {
        "gate_id": "task_start_gate",
        "gate_name": "Task Start Gate",
        "gate_category": "planning_gate",
        "protected_action": "starting a new task or phase",
        "risk_level": "medium",
        "human_review_required": False,
    },
    {
        "gate_id": "scope_check_gate",
        "gate_name": "Scope Check Gate",
        "gate_category": "scope_gate",
        "protected_action": "modifying files within task scope",
        "risk_level": "medium",
        "human_review_required": False,
    },
    {
        "gate_id": "backend_invocation_gate",
        "gate_name": "Backend Invocation Gate",
        "gate_category": "backend_gate",
        "protected_action": "invoking a backend agent",
        "risk_level": "critical",
        "human_review_required": True,
    },
    {
        "gate_id": "prompt_send_gate",
        "gate_name": "Prompt Send Gate",
        "gate_category": "prompt_gate",
        "protected_action": "sending a prompt to a backend",
        "risk_level": "critical",
        "human_review_required": True,
    },
    {
        "gate_id": "capture_acceptance_gate",
        "gate_name": "Capture Acceptance Gate",
        "gate_category": "capture_gate",
        "protected_action": "accepting captured backend output",
        "risk_level": "high",
        "human_review_required": True,
    },
    {
        "gate_id": "intake_review_gate",
        "gate_name": "Intake Review Gate",
        "gate_category": "review_gate",
        "protected_action": "classifying captured output for adoption",
        "risk_level": "high",
        "human_review_required": True,
    },
    {
        "gate_id": "adoption_approval_gate",
        "gate_name": "Adoption Approval Gate",
        "gate_category": "review_gate",
        "protected_action": "approving an adoption candidate",
        "risk_level": "critical",
        "human_review_required": True,
    },
    {
        "gate_id": "source_mutation_gate",
        "gate_name": "Source Mutation Gate",
        "gate_category": "mutation_gate",
        "protected_action": "modifying source code files",
        "risk_level": "high",
        "human_review_required": True,
    },
    {
        "gate_id": "test_mutation_gate",
        "gate_name": "Test Mutation Gate",
        "gate_category": "test_gate",
        "protected_action": "modifying test files",
        "risk_level": "medium",
        "human_review_required": False,
    },
    {
        "gate_id": "commit_gate",
        "gate_name": "Commit Gate",
        "gate_category": "commit_gate",
        "protected_action": "creating a git commit",
        "risk_level": "high",
        "human_review_required": True,
    },
    {
        "gate_id": "push_gate",
        "gate_name": "Push Gate",
        "gate_category": "push_gate",
        "protected_action": "pushing to remote",
        "risk_level": "high",
        "human_review_required": True,
    },
    {
        "gate_id": "rollback_gate",
        "gate_name": "Rollback Gate",
        "gate_category": "rollback_gate",
        "protected_action": "rolling back a previous action",
        "risk_level": "high",
        "human_review_required": True,
    },
    {
        "gate_id": "storage_write_gate",
        "gate_name": "Storage Write Gate",
        "gate_category": "storage_gate",
        "protected_action": "writing to persistent storage",
        "risk_level": "high",
        "human_review_required": True,
    },
    {
        "gate_id": "permission_broker_gate",
        "gate_name": "Permission Broker Gate",
        "gate_category": "broker_gate",
        "protected_action": "runtime permission evaluation",
        "risk_level": "critical",
        "human_review_required": True,
    },
    {
        "gate_id": "shell_command_gate",
        "gate_name": "Shell Command Gate",
        "gate_category": "shell_gate",
        "protected_action": "executing a shell command",
        "risk_level": "critical",
        "human_review_required": True,
    },
]


def _detect_task_contract(repo_root: Path) -> dict[str, Any] | None:
    active_dir = repo_root / "tasks" / "active"
    if not active_dir.is_dir():
        return None
    for f in sorted(active_dir.iterdir()):
        if f.suffix == ".md" and not f.name.startswith("."):
            allowed: list[str] = []
            forbidden: list[str] = []
            section = ""
            try:
                for line in f.read_text().splitlines():
                    stripped = line.strip()
                    if stripped.startswith("## Allowed Files"):
                        section = "allowed"
                    elif stripped.startswith("## Forbidden Files"):
                        section = "forbidden"
                    elif stripped.startswith("## "):
                        section = ""
                    elif stripped.startswith("- ") and section in ("allowed", "forbidden"):
                        entry = stripped[2:].strip()
                        if section == "allowed":
                            allowed.append(entry)
                        else:
                            forbidden.append(entry)
            except OSError:
                pass
            return {
                "path": str(f.relative_to(repo_root)),
                "stem": f.stem,
                "allowed_files": allowed,
                "forbidden_files": forbidden,
            }
    return None


def _evaluate_scope(
    repo_root: Path,
    requested_action: str | None,
    requested_files: list[str],
    task_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    if not task_contract:
        return {
            "scope_status": "unknown",
            "requested_files": requested_files,
            "allowed_files": [],
            "forbidden_files": [],
            "matched_allowed_files": [],
            "matched_forbidden_files": [],
            "unknown_files": requested_files,
            "task_contract_detected": False,
            "task_contract_path": None,
            "evidence_sources": [],
            "scope_notes": "no task contract detected",
        }

    # Late import avoids circular dep: scope_preflight imports _detect_task_contract from here.
    from pcae.core.scope_preflight import _SPF_POLICY_FORBIDDEN_FILES, _match_file
    allowed_patterns = task_contract["allowed_files"]
    task_forbidden = list(task_contract["forbidden_files"])
    policy_additions = [f for f in _SPF_POLICY_FORBIDDEN_FILES if f not in task_forbidden]
    forbidden_patterns = task_forbidden + policy_additions

    matched_allowed: list[str] = []
    matched_forbidden: list[str] = []
    unknown: list[str] = []

    for rf in requested_files:
        is_forbidden = _match_file(rf, forbidden_patterns)
        is_allowed = _match_file(rf, list(allowed_patterns))
        if is_forbidden:
            matched_forbidden.append(rf)
        elif is_allowed:
            matched_allowed.append(rf)
        else:
            unknown.append(rf)

    if not requested_files:
        scope_status = "unknown"
    elif matched_forbidden:
        scope_status = "out_of_scope"
    elif unknown:
        scope_status = "partially_in_scope" if matched_allowed else "unknown"
    else:
        scope_status = "in_scope"

    return {
        "scope_status": scope_status,
        "requested_files": requested_files,
        "allowed_files": allowed_patterns,
        "forbidden_files": forbidden_patterns,
        "matched_allowed_files": matched_allowed,
        "matched_forbidden_files": matched_forbidden,
        "unknown_files": unknown,
        "task_contract_detected": True,
        "task_contract_path": task_contract["path"],
        "evidence_sources": [task_contract["path"]],
        "scope_notes": f"scope_status={scope_status}, requested_action={requested_action or 'default'}",
    }


_KNOWN_BACKENDS = {"claude", "claude-deepseek", "claude-kimi", "codex", "subagent"}


def _evaluate_backend(
    requested_backend: str | None,
    requested_action: str | None,
    prompt_present: bool,
    task_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    if not requested_backend and requested_action != "backend_invocation":
        return {
            "backend_status": "not_requested",
            "requested_backend": None,
            "requested_action": requested_action,
            "prompt_present": prompt_present,
            "backend_allowed_by_scope": False,
            "backend_approval_detected": False,
            "human_approval_detected": False,
            "task_contract_detected": task_contract is not None,
            "task_contract_path": task_contract["path"] if task_contract else None,
            "evidence_sources": [],
            "backend_notes": "backend invocation not requested",
        }

    backend = requested_backend or "unknown"
    tc_detected = task_contract is not None

    if backend not in _KNOWN_BACKENDS and backend != "unknown":
        status = "requested_unknown"
    elif not tc_detected:
        status = "requested_requires_more_evidence"
    elif not prompt_present:
        status = "requested_requires_more_evidence"
    else:
        status = "requested_requires_human_review"

    return {
        "backend_status": status,
        "requested_backend": backend,
        "requested_action": requested_action or "backend_invocation",
        "prompt_present": prompt_present,
        "backend_allowed_by_scope": False,
        "backend_approval_detected": False,
        "human_approval_detected": False,
        "task_contract_detected": tc_detected,
        "task_contract_path": task_contract["path"] if task_contract else None,
        "evidence_sources": [task_contract["path"]] if tc_detected else [],
        "backend_notes": f"backend={backend}, status={status}, dry_run_only=true",
    }


def _evaluate_adoption(
    requested_action: str | None,
    requested_files: list[str],
    adoption_artifact_present: bool,
    human_approved: bool,
    task_contract: dict[str, Any] | None,
    scope_status: str | None,
) -> dict[str, Any]:
    is_adoption = requested_action == "adoption"
    if not is_adoption:
        return {
            "adoption_status": "not_requested",
            "requested_action": requested_action,
            "requested_files": requested_files,
            "adoption_artifact_present": adoption_artifact_present,
            "adoption_review_detected": False,
            "adoption_approval_detected": False,
            "human_approval_detected": False,
            "task_contract_detected": task_contract is not None,
            "task_contract_path": task_contract["path"] if task_contract else None,
            "scope_status": scope_status,
            "evidence_sources": [],
            "adoption_notes": "adoption not requested",
        }

    tc_detected = task_contract is not None
    if not tc_detected:
        status = "requested_requires_more_evidence"
    elif not adoption_artifact_present:
        status = "requested_requires_more_evidence"
    elif human_approved:
        status = "requested_requires_human_review"
    else:
        status = "requested_requires_human_review"

    return {
        "adoption_status": status,
        "requested_action": requested_action,
        "requested_files": requested_files,
        "adoption_artifact_present": adoption_artifact_present,
        "adoption_review_detected": False,
        "adoption_approval_detected": False,
        "human_approval_detected": human_approved,
        "task_contract_detected": tc_detected,
        "task_contract_path": task_contract["path"] if tc_detected else None,
        "scope_status": scope_status,
        "evidence_sources": [task_contract["path"]] if tc_detected else [],
        "adoption_notes": f"adoption_status={status}, dry_run_only=true",
    }


def _evaluate_mutation(
    requested_action: str | None,
    requested_files: list[str],
    human_approved: bool,
    task_contract: dict[str, Any] | None,
    scope_result: dict[str, Any] | None,
) -> dict[str, Any]:
    mutation_types = {"source_mutation": "source", "test_mutation": "test", "docs_mutation": "docs"}
    mt = mutation_types.get(requested_action or "", "unknown")
    is_mutation = requested_action in mutation_types

    if not is_mutation:
        return {
            "mutation_status": "not_requested",
            "requested_action": requested_action,
            "requested_files": requested_files,
            "mutation_type": mt,
            "scope_status": None,
            "matched_allowed_files": [],
            "matched_forbidden_files": [],
            "unknown_files": requested_files,
            "human_approval_detected": False,
            "task_contract_detected": task_contract is not None,
            "task_contract_path": task_contract["path"] if task_contract else None,
            "evidence_sources": [],
            "mutation_notes": "mutation not requested",
        }

    tc_detected = task_contract is not None
    ss = scope_result.get("scope_status") if scope_result else None
    matched_allowed = scope_result.get("matched_allowed_files", []) if scope_result else []
    matched_forbidden = scope_result.get("matched_forbidden_files", []) if scope_result else []
    unknown = scope_result.get("unknown_files", requested_files) if scope_result else requested_files

    if not tc_detected:
        status = "requested_requires_more_evidence"
    elif matched_forbidden:
        status = "requested_blocked"
    elif not requested_files:
        status = "requested_requires_more_evidence"
    elif unknown:
        status = "requested_requires_more_evidence"
    else:
        status = "requested_requires_human_review"

    return {
        "mutation_status": status,
        "requested_action": requested_action,
        "requested_files": requested_files,
        "mutation_type": mt,
        "scope_status": ss,
        "matched_allowed_files": matched_allowed,
        "matched_forbidden_files": matched_forbidden,
        "unknown_files": unknown,
        "human_approval_detected": human_approved,
        "task_contract_detected": tc_detected,
        "task_contract_path": task_contract["path"] if tc_detected else None,
        "evidence_sources": [task_contract["path"]] if tc_detected else [],
        "mutation_notes": f"mutation_status={status}, mutation_type={mt}, dry_run_only=true",
    }


def _git_porcelain(repo_root: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _git_branch_name(repo_root: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _git_ahead_count(repo_root: Path) -> int | None:
    try:
        r = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        if r.returncode == 0:
            return int(r.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None


def _evaluate_commit(
    requested_action: str | None,
    commit_message_present: bool,
    human_approved: bool,
    task_contract: dict[str, Any] | None,
    ctx: GateDryRunContext,
    snap: dict[str, Any],
) -> dict[str, Any]:
    is_commit = requested_action == "commit"
    porcelain = ctx.git_porcelain
    repo_clean = porcelain == "" if porcelain is not None else None
    staged = porcelain is not None and any(
        line and line[0] in "AMDRC" for line in porcelain.split("\n")
    ) if porcelain else False
    unstaged = porcelain is not None and any(
        line and len(line) > 1 and line[1] in "MD" for line in porcelain.split("\n")
    ) if porcelain else False

    if not is_commit:
        return {
            "commit_status": "not_requested",
            "requested_action": requested_action,
            "repository_clean": repo_clean,
            "staged_changes_detected": staged,
            "unstaged_changes_detected": unstaged,
            "commit_message_present": commit_message_present,
            "human_approval_detected": False,
            "task_contract_detected": task_contract is not None,
            "task_contract_path": task_contract["path"] if task_contract else None,
            "lifecycle_state": snap.get("current_lifecycle_state", "unknown"),
            "check_status": "unknown",
            "health_status": "unknown",
            "evidence_sources": [],
            "commit_notes": "commit not requested",
        }

    tc_detected = task_contract is not None
    if not tc_detected:
        status = "requested_requires_more_evidence"
    elif not commit_message_present:
        status = "requested_requires_more_evidence"
    elif human_approved:
        status = "requested_requires_human_review"
    else:
        status = "requested_requires_human_review"

    return {
        "commit_status": status,
        "requested_action": "commit",
        "repository_clean": repo_clean,
        "staged_changes_detected": staged,
        "unstaged_changes_detected": unstaged,
        "commit_message_present": commit_message_present,
        "human_approval_detected": human_approved,
        "task_contract_detected": tc_detected,
        "task_contract_path": task_contract["path"] if tc_detected else None,
        "lifecycle_state": snap.get("current_lifecycle_state", "unknown"),
        "check_status": "unknown",
        "health_status": "unknown",
        "evidence_sources": [task_contract["path"]] if tc_detected else [],
        "commit_notes": f"commit_status={status}, dry_run_only=true",
    }


def _evaluate_push(
    requested_action: str | None,
    push_target: str | None,
    human_approved: bool,
    task_contract: dict[str, Any] | None,
    ctx: GateDryRunContext,
    snap: dict[str, Any],
) -> dict[str, Any]:
    is_push = requested_action == "push"
    branch = ctx.git_branch
    ahead = ctx.git_ahead_count
    if ahead is not None and ahead == 0:
        sync = "synced"
    elif ahead is not None:
        sync = f"ahead_by_{ahead}"
    else:
        sync = "unknown"

    if not is_push:
        return {
            "push_status": "not_requested",
            "requested_action": requested_action,
            "branch": branch,
            "origin_sync_status": sync,
            "origin_main_head_count": ahead,
            "push_target": push_target,
            "raw_push_detected": False,
            "force_push_detected": False,
            "human_approval_detected": False,
            "task_contract_detected": task_contract is not None,
            "task_contract_path": task_contract["path"] if task_contract else None,
            "lifecycle_state": snap.get("current_lifecycle_state", "unknown"),
            "push_check_status": "unknown",
            "evidence_sources": [],
            "push_notes": "push not requested",
        }

    tc_detected = task_contract is not None
    if not tc_detected:
        status = "requested_requires_more_evidence"
    elif human_approved:
        status = "requested_requires_human_review"
    else:
        status = "requested_requires_human_review"

    return {
        "push_status": status,
        "requested_action": "push",
        "branch": branch,
        "origin_sync_status": sync,
        "origin_main_head_count": ahead,
        "push_target": push_target or "origin/main",
        "raw_push_detected": False,
        "force_push_detected": False,
        "human_approval_detected": human_approved,
        "task_contract_detected": tc_detected,
        "task_contract_path": task_contract["path"] if tc_detected else None,
        "lifecycle_state": snap.get("current_lifecycle_state", "unknown"),
        "push_check_status": "unknown",
        "evidence_sources": [task_contract["path"]] if tc_detected else [],
        "push_notes": f"push_status={status}, dry_run_only=true",
    }


_HIGH_RISK_ACTIONS = {
    "backend_invocation", "prompt_send", "adoption", "storage_write", "shell_command",
}
_WRITE_ACTIONS = {
    "source_mutation", "test_mutation", "docs_mutation", "commit", "push",
    "backend_invocation", "prompt_send", "adoption", "storage_write", "shell_command",
}


def _evaluate_gate(gate_def: dict[str, Any], ps: dict[str, Any],
                   rr: dict[str, Any], ctx: GateDryRunContext,
                   requested_action: str | None,
                   requested_files: list[str],
                   requested_backend: str | None = None,
                   prompt_present: bool = False,
                   adoption_artifact_present: bool = False,
                   human_approved: bool = False,
                   commit_message_present: bool = False,
                   push_target: str | None = None) -> dict[str, Any]:
    gate_id = gate_def["gate_id"]
    risk_level = gate_def["risk_level"]
    now = datetime.now(timezone.utc).isoformat()

    snap = ps.get("snapshot", {})
    active_risks = snap.get("active_risks", [])
    mnr = snap.get("must_never_repeat_controls", [])

    reason_codes: list[str] = []
    decision = "deny"
    scope_evaluation: dict[str, Any] | None = None
    backend_evaluation: dict[str, Any] | None = None
    adoption_evaluation: dict[str, Any] | None = None
    mutation_evaluation: dict[str, Any] | None = None
    commit_evaluation: dict[str, Any] | None = None
    push_evaluation: dict[str, Any] | None = None

    task_contract = ctx.task_contract

    if gate_id == "permission_broker_gate":
        decision = "deny"
        reason_codes = ["permission_broker_not_implemented"]
    elif gate_id == "shell_command_gate":
        decision = "deny"
        reason_codes = ["shell_gate_not_implemented"]
    elif gate_id == "storage_write_gate":
        decision = "deny"
        reason_codes = ["storage_write_not_authorized"]
    elif gate_id == "backend_invocation_gate":
        backend_evaluation = _evaluate_backend(
            requested_backend, requested_action, prompt_present, task_contract,
        )
        bs = backend_evaluation["backend_status"]
        if bs == "not_requested":
            decision = "requires_more_evidence"
            reason_codes = ["backend_invocation_not_authorized", "missing_artifact_evidence"]
        elif bs == "requested_requires_human_review":
            decision = "requires_human_review"
            reason_codes = ["backend_invocation_not_authorized", "human_approval_required"]
        elif bs == "requested_requires_more_evidence":
            decision = "requires_more_evidence"
            reason_codes = ["backend_invocation_not_authorized", "missing_artifact_evidence"]
        elif bs == "requested_blocked":
            decision = "deny"
            reason_codes = ["backend_invocation_not_authorized"]
        elif bs == "requested_unknown":
            decision = "requires_more_evidence"
            reason_codes = ["backend_invocation_not_authorized", "unknown_state"]
        else:
            decision = "deny"
            reason_codes = ["backend_invocation_not_authorized", "human_approval_required"]
        for ctrl in mnr:
            if "invocation" in ctrl.get("risk_type", "") or "backend" in ctrl.get("risk_type", ""):
                if "must_never_repeat_control_applies" not in reason_codes:
                    reason_codes.append("must_never_repeat_control_applies")
                break
    elif gate_id == "prompt_send_gate":
        decision = "deny"
        reason_codes = ["prompt_send_not_authorized", "human_approval_required"]
    elif gate_id == "adoption_approval_gate":
        scope_for_adoption = _evaluate_scope(
            ctx.repo_root, requested_action, requested_files, task_contract,
        ) if requested_files else None
        adoption_evaluation = _evaluate_adoption(
            requested_action, requested_files, adoption_artifact_present,
            human_approved, task_contract,
            scope_for_adoption.get("scope_status") if scope_for_adoption else None,
        )
        ads = adoption_evaluation["adoption_status"]
        if ads == "not_requested":
            decision = "requires_more_evidence"
            reason_codes = ["human_approval_required", "missing_artifact_evidence"]
        elif ads == "requested_requires_human_review":
            decision = "requires_human_review"
            reason_codes = ["human_approval_required"]
        elif ads == "requested_requires_more_evidence":
            decision = "requires_more_evidence"
            reason_codes = ["human_approval_required", "missing_artifact_evidence"]
        elif ads == "requested_blocked":
            decision = "blocked_by_scope"
            reason_codes = ["scope_not_authorized"]
        else:
            decision = "deny"
            reason_codes = ["human_approval_required"]
        for ctrl in mnr:
            if "adoption" in ctrl.get("risk_type", ""):
                if "must_never_repeat_control_applies" not in reason_codes:
                    reason_codes.append("must_never_repeat_control_applies")
                break
    elif gate_id == "capture_acceptance_gate":
        decision = "requires_more_evidence"
        reason_codes = ["missing_artifact_evidence"]
    elif gate_id == "intake_review_gate":
        decision = "requires_more_evidence"
        reason_codes = ["missing_artifact_evidence"]
    elif gate_id == "rollback_gate":
        decision = "deny"
        reason_codes = ["rollback_not_authorized", "human_approval_required"]
    elif gate_id == "commit_gate":
        commit_evaluation = _evaluate_commit(
            requested_action, commit_message_present, human_approved,
            task_contract, ctx, snap,
        )
        cs = commit_evaluation["commit_status"]
        if cs == "not_requested":
            decision = "requires_more_evidence"
            reason_codes = ["commit_not_authorized", "missing_artifact_evidence"]
        elif cs == "requested_requires_human_review":
            decision = "requires_human_review"
            reason_codes = ["commit_not_authorized", "human_approval_required"]
        elif cs == "requested_requires_more_evidence":
            decision = "requires_more_evidence"
            reason_codes = ["commit_not_authorized", "missing_artifact_evidence"]
        elif cs == "requested_blocked":
            decision = "deny"
            reason_codes = ["commit_not_authorized"]
        else:
            decision = "requires_human_review"
            reason_codes = ["commit_not_authorized", "human_approval_required"]
        for ctrl in mnr:
            if "hook_bypass" in ctrl.get("risk_type", ""):
                if "must_never_repeat_control_applies" not in reason_codes:
                    reason_codes.append("must_never_repeat_control_applies")
                break
    elif gate_id == "push_gate":
        push_evaluation = _evaluate_push(
            requested_action, push_target, human_approved,
            task_contract, ctx, snap,
        )
        ps_status = push_evaluation["push_status"]
        if ps_status == "not_requested":
            decision = "requires_more_evidence"
            reason_codes = ["push_not_authorized", "missing_artifact_evidence"]
        elif ps_status == "requested_requires_human_review":
            decision = "requires_human_review"
            reason_codes = ["push_not_authorized", "human_approval_required"]
        elif ps_status == "requested_requires_more_evidence":
            decision = "requires_more_evidence"
            reason_codes = ["push_not_authorized", "missing_artifact_evidence"]
        elif ps_status == "requested_blocked":
            decision = "deny"
            reason_codes = ["push_not_authorized"]
        else:
            decision = "requires_human_review"
            reason_codes = ["push_not_authorized", "human_approval_required"]
        for ctrl in mnr:
            if "raw_push" in ctrl.get("risk_type", ""):
                if "must_never_repeat_control_applies" not in reason_codes:
                    reason_codes.append("must_never_repeat_control_applies")
                break
    elif gate_id in ("source_mutation_gate", "test_mutation_gate"):
        scope_for_mut = _evaluate_scope(
            ctx.repo_root, requested_action, requested_files, task_contract,
        ) if requested_files else None
        mutation_evaluation = _evaluate_mutation(
            requested_action, requested_files, human_approved,
            task_contract, scope_for_mut,
        )
        ms = mutation_evaluation["mutation_status"]
        if ms == "not_requested":
            if snap.get("current_active_phase"):
                decision = "requires_more_evidence"
                reason_codes = ["scope_not_authorized"]
            else:
                decision = "deny"
                reason_codes = ["missing_task_contract"]
        elif ms == "requested_requires_human_review":
            decision = "requires_human_review"
            reason_codes = ["human_approval_required"]
        elif ms == "requested_requires_more_evidence":
            decision = "requires_more_evidence"
            reason_codes = ["missing_artifact_evidence"]
        elif ms == "requested_blocked":
            decision = "blocked_by_scope"
            reason_codes = ["scope_not_authorized"]
        else:
            decision = "requires_more_evidence"
            reason_codes = ["unknown_state"]
        if gate_id == "source_mutation_gate":
            if "source_mutation_not_authorized" not in reason_codes:
                reason_codes.append("source_mutation_not_authorized")
        else:
            if "test_mutation_not_authorized" not in reason_codes:
                reason_codes.append("test_mutation_not_authorized")
    elif gate_id == "scope_check_gate":
        scope_evaluation = _evaluate_scope(
            ctx.repo_root, requested_action, requested_files, task_contract,
        )
        ss = scope_evaluation["scope_status"]
        if not task_contract:
            decision = "deny"
            reason_codes = ["missing_task_contract"]
        elif ss == "out_of_scope":
            decision = "blocked_by_scope"
            reason_codes = ["scope_not_authorized"]
        elif ss == "in_scope":
            if requested_action and requested_action in _WRITE_ACTIONS:
                decision = "requires_human_review"
                reason_codes = ["human_approval_required"]
            elif requested_action and requested_action in _HIGH_RISK_ACTIONS:
                decision = "deny"
                reason_codes = [f"{requested_action}_not_authorized"]
            else:
                decision = "requires_more_evidence"
                reason_codes = ["scope_not_authorized"]
        elif ss == "partially_in_scope":
            decision = "blocked_by_scope"
            reason_codes = ["scope_not_authorized"]
        else:
            decision = "requires_more_evidence"
            reason_codes = ["scope_not_authorized"]
    elif gate_id == "task_start_gate":
        lifecycle = snap.get("current_lifecycle_state", "unknown")
        if lifecycle == "closed":
            decision = "requires_more_evidence"
            reason_codes = ["lifecycle_state_not_ready"]
        else:
            decision = "requires_more_evidence"
            reason_codes = ["missing_task_contract"]

    if active_risks and risk_level in ("critical", "high"):
        if "risk_active" not in reason_codes:
            reason_codes.append("risk_active")

    evidence_artifacts = [r.get("risk_id", "") for r in active_risks[:3]]
    evidence_risks = [r.get("risk_id", "") for r in rr.get("risks", [])[:5]]

    result: dict[str, Any] = {
        "gate_id": gate_id,
        "gate_name": gate_def["gate_name"],
        "gate_category": gate_def["gate_category"],
        "protected_action": gate_def["protected_action"],
        "risk_level": risk_level,
        "decision": decision,
        "reason_codes": reason_codes,
        "human_review_required": gate_def["human_review_required"],
        "evidence_artifacts": evidence_artifacts,
        "evidence_events": [],
        "evidence_decisions": [],
        "evidence_risks": evidence_risks,
        "allowed_scope": None,
        "denied_scope": gate_def["protected_action"],
        "requested_action": requested_action or gate_def["protected_action"],
        "requested_actor": "dry_run_evaluator",
        "requested_files": requested_files,
        "dry_run": True,
        "enforcement_performed": False,
        "authorization_granted": False,
        "safety_notes": f"dry_run_only=true, gate={gate_id}, decision={decision}",
        "generated_at": now,
        "schema_version": "0.1",
    }

    if scope_evaluation is not None:
        result["scope_evaluation"] = scope_evaluation
    if backend_evaluation is not None:
        result["backend_evaluation"] = backend_evaluation
    if adoption_evaluation is not None:
        result["adoption_evaluation"] = adoption_evaluation
    if mutation_evaluation is not None:
        result["mutation_evaluation"] = mutation_evaluation
    if commit_evaluation is not None:
        result["commit_evaluation"] = commit_evaluation
    if push_evaluation is not None:
        result["push_evaluation"] = push_evaluation

    return result


def build_gate_dry_run(
    repo_root: Path,
    requested_action: str | None = None,
    requested_files: list[str] | None = None,
    requested_backend: str | None = None,
    prompt_present: bool = False,
    adoption_artifact_present: bool = False,
    human_approved: bool = False,
    commit_message_present: bool = False,
    push_target: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    req_files = requested_files or []

    ctx = GateDryRunContext(repo_root)
    ps = ctx.project_state

    # Derive risk register evidence from project_state snapshot to avoid a
    # second cascading build-function call (project_state already called
    # build_risk_register internally).  _evaluate_gate only needs risk IDs.
    snap_ps = ps.get("snapshot", {})
    rr: dict[str, Any] = {
        "risks": snap_ps.get("active_risks", []) + snap_ps.get("accepted_risks", []),
    }

    gates: list[dict[str, Any]] = []
    for gate_def in _GATE_DEFS:
        result = _evaluate_gate(gate_def, ps, rr, ctx,
                                requested_action, req_files,
                                requested_backend, prompt_present,
                                adoption_artifact_present, human_approved,
                                commit_message_present, push_target)
        gates.append(result)

    return {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "pcae gate-dry-run",
        "repository_root": str(repo_root),
        "dry_run": True,
        "taxonomy_version": "0.1",
        "gate_count": len(gates),
        "gates": gates,
        "warnings": warnings,
        "errors": errors,
        "safety_notes": {
            "gate_dry_run_only": True,
            "gate_dry_run_does_not_authorize_action": True,
            "gate_dry_run_does_not_enforce_action": True,
            "gate_dry_run_does_not_invoke_backends": True,
            "gate_dry_run_does_not_send_prompts": True,
            "gate_dry_run_does_not_capture_outputs": True,
            "gate_dry_run_does_not_perform_intake": True,
            "gate_dry_run_does_not_perform_adoption": True,
            "gate_dry_run_does_not_mutate_repo": True,
            "gate_dry_run_does_not_commit": True,
            "gate_dry_run_does_not_push": True,
            "gate_dry_run_does_not_write_storage": True,
            "permission_broker_not_implemented": True,
            "shell_gate_not_implemented": True,
            "storage_not_implemented": True,
            "backend_gate_dry_run_only": True,
            "backend_gate_does_not_invoke_backend": True,
            "backend_gate_does_not_send_prompt": True,
            "backend_gate_does_not_capture_output": True,
            "backend_gate_does_not_authorize_backend_invocation": True,
            "backend_gate_requires_human_review_for_invocation": True,
            "requested_backend_is_not_approval": True,
            "prompt_presence_is_not_approval": True,
            "scope_match_is_not_backend_approval": True,
            "commit_gate_dry_run_only": True,
            "commit_gate_does_not_stage_files": True,
            "commit_gate_does_not_create_commit": True,
            "commit_gate_does_not_authorize_commit": True,
            "push_gate_dry_run_only": True,
            "push_gate_does_not_push": True,
            "push_gate_does_not_raw_push": True,
            "push_gate_does_not_force_push": True,
            "push_gate_does_not_authorize_push": True,
            "human_approval_flag_is_not_commit_authorization": True,
            "human_approval_flag_is_not_push_authorization": True,
            "clean_repo_is_not_commit_authorization": True,
            "push_check_pass_is_not_push_authorization": True,
            "adoption_gate_dry_run_only": True,
            "adoption_gate_does_not_review_output": True,
            "adoption_gate_does_not_approve_output": True,
            "adoption_gate_does_not_apply_output": True,
            "adoption_gate_does_not_authorize_adoption": True,
            "mutation_gate_dry_run_only": True,
            "mutation_gate_does_not_mutate_source": True,
            "mutation_gate_does_not_mutate_tests": True,
            "mutation_gate_does_not_mutate_docs": True,
            "mutation_gate_does_not_authorize_mutation": True,
            "scope_match_is_not_mutation_approval": True,
            "human_approval_flag_is_not_execution": True,
            "adoption_artifact_presence_is_not_approval": True,
            "scope_gate_dry_run_only": True,
            "scope_gate_does_not_authorize_mutation": True,
            "scope_gate_does_not_authorize_commit": True,
            "scope_gate_does_not_authorize_push": True,
            "scope_gate_does_not_authorize_backend_invocation": True,
            "scope_gate_does_not_authorize_shell_execution": True,
            "scope_in_scope_is_not_overall_authorization": True,
            "backend_invocation_performed": False,
            "repo_mutation_performed": False,
            "storage_written": False,
        },
    }
