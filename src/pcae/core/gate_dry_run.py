from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.artifact_index import build_artifact_index
from pcae.core.memory_snapshot import build_memory_snapshot
from pcae.core.governance_timeline import build_governance_timeline
from pcae.core.decision_log import build_decision_log
from pcae.core.risk_register import build_risk_register
from pcae.core.project_state import build_project_state


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
    import fnmatch

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

    allowed_patterns = task_contract["allowed_files"]
    forbidden_patterns = task_contract["forbidden_files"]

    matched_allowed: list[str] = []
    matched_forbidden: list[str] = []
    unknown: list[str] = []

    for rf in requested_files:
        is_allowed = any(
            fnmatch.fnmatch(rf, pat) or rf == pat or rf.startswith(pat.rstrip("*"))
            for pat in allowed_patterns
        )
        is_forbidden = any(
            fnmatch.fnmatch(rf, pat) or rf == pat or rf.startswith(pat.rstrip("*"))
            for pat in forbidden_patterns
        )
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


_HIGH_RISK_ACTIONS = {
    "backend_invocation", "prompt_send", "adoption", "storage_write", "shell_command",
}
_WRITE_ACTIONS = {
    "source_mutation", "test_mutation", "docs_mutation", "commit", "push",
    "backend_invocation", "prompt_send", "adoption", "storage_write", "shell_command",
}


def _evaluate_gate(gate_def: dict[str, Any], ps: dict[str, Any],
                   rr: dict[str, Any], repo_root: Path,
                   requested_action: str | None,
                   requested_files: list[str]) -> dict[str, Any]:
    gate_id = gate_def["gate_id"]
    risk_level = gate_def["risk_level"]
    now = datetime.now(timezone.utc).isoformat()

    snap = ps.get("snapshot", {})
    active_risks = snap.get("active_risks", [])
    mnr = snap.get("must_never_repeat_controls", [])

    reason_codes: list[str] = []
    decision = "deny"
    scope_evaluation: dict[str, Any] | None = None

    task_contract = _detect_task_contract(repo_root)

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
        decision = "deny"
        reason_codes = ["backend_invocation_not_authorized", "human_approval_required"]
    elif gate_id == "prompt_send_gate":
        decision = "deny"
        reason_codes = ["prompt_send_not_authorized", "human_approval_required"]
    elif gate_id == "adoption_approval_gate":
        decision = "deny"
        reason_codes = ["human_approval_required"]
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
        decision = "requires_human_review"
        reason_codes = ["human_approval_required"]
    elif gate_id == "push_gate":
        decision = "requires_human_review"
        reason_codes = ["human_approval_required"]
        for ctrl in mnr:
            if "raw_push" in ctrl.get("risk_type", ""):
                reason_codes.append("must_never_repeat_control_applies")
                break
    elif gate_id == "source_mutation_gate":
        decision = "requires_human_review"
        reason_codes = ["human_approval_required"]
    elif gate_id == "test_mutation_gate":
        if snap.get("current_active_phase"):
            decision = "requires_more_evidence"
            reason_codes = ["scope_not_authorized"]
        else:
            decision = "deny"
            reason_codes = ["missing_task_contract"]
    elif gate_id == "scope_check_gate":
        scope_evaluation = _evaluate_scope(
            repo_root, requested_action, requested_files, task_contract,
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

    return result


def build_gate_dry_run(
    repo_root: Path,
    requested_action: str | None = None,
    requested_files: list[str] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    req_files = requested_files or []

    _ai = build_artifact_index(repo_root)
    _ms = build_memory_snapshot(repo_root)
    _gt = build_governance_timeline(repo_root)
    _dl = build_decision_log(repo_root)
    rr = build_risk_register(repo_root)
    ps = build_project_state(repo_root)

    gates: list[dict[str, Any]] = []
    for gate_def in _GATE_DEFS:
        result = _evaluate_gate(gate_def, ps, rr, repo_root,
                                requested_action, req_files)
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
