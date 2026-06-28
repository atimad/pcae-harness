"""
Permission broker prototype — Phase 88R.

Read-only decision aggregator.  Consumes governance evidence and returns a
conservative broker decision envelope.  Never executes commands, invokes
backends, sends prompts, writes storage, or grants real authorisation.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.core.gate_dry_run import _detect_task_contract
from pcae.core.scope_preflight import build_scope_preflight
from pcae.core.shell_gate import _call_doctor_test_run, _classify_command, _decide as _sg_decide


# ── Public constant surfaces ───────────────────────────────────────────────

BPE_DECISIONS: tuple[str, ...] = (
    "allow_preflight_only",
    "deny",
    "requires_human_review",
    "requires_more_evidence",
    "blocked_by_scope",
    "blocked_by_backend_policy",
    "blocked_by_mutation_policy",
    "blocked_by_commit_policy",
    "blocked_by_push_policy",
    "blocked_by_lifecycle_state",
    "blocked_by_task_contract",
    "blocked_by_risk",
    "blocked_by_must_never_repeat",
    "blocked_by_failed_check",
    "blocked_by_failed_health",
    "blocked_by_failed_doctor",
    "blocked_by_failed_tests",
    "blocked_by_push_check",
    "blocked_by_raw_git_push",
    "blocked_by_force_push",
    "blocked_by_shell_gate",
    "blocked_by_test_run_lock",
    "blocked_by_conflicting_evidence",
    "unknown",
)

BPE_HARD_BLOCK_DECISIONS: frozenset[str] = frozenset({
    "blocked_by_scope",
    "blocked_by_backend_policy",
    "blocked_by_mutation_policy",
    "blocked_by_commit_policy",
    "blocked_by_push_policy",
    "blocked_by_lifecycle_state",
    "blocked_by_task_contract",
    "blocked_by_risk",
    "blocked_by_must_never_repeat",
    "blocked_by_failed_check",
    "blocked_by_failed_health",
    "blocked_by_failed_doctor",
    "blocked_by_failed_tests",
    "blocked_by_push_check",
    "blocked_by_raw_git_push",
    "blocked_by_force_push",
    "blocked_by_shell_gate",
    "blocked_by_test_run_lock",
    "blocked_by_conflicting_evidence",
})

# Actions that require an active task contract
BPE_MUTATING_ACTIONS: frozenset[str] = frozenset({
    "source_mutation",
    "test_mutation",
    "docs_mutation",
    "filesystem_write",
    "environment_mutation",
    "adoption",
    "commit",
    "push",
    "rollback",
    "storage_write",
    "backend_invocation",
})

# Shell gate decisions that map to hard broker blocks
_SG_HARD_BLOCK_TO_BROKER: dict[str, str] = {
    "blocked_by_raw_git_commit":         "blocked_by_shell_gate",
    "blocked_by_raw_git_push":           "blocked_by_raw_git_push",
    "blocked_by_force_push":             "blocked_by_force_push",
    "blocked_by_history_rewrite":        "blocked_by_shell_gate",
    "blocked_by_destructive_filesystem": "blocked_by_shell_gate",
    "blocked_by_policy_forbidden_file":  "blocked_by_scope",        # consistent with scope preflight
    "blocked_by_backend_policy":         "blocked_by_backend_policy",
    "blocked_by_prompt_policy":          "blocked_by_shell_gate",
    "blocked_by_adoption_policy":        "blocked_by_shell_gate",
    "blocked_by_test_run_lock":          "blocked_by_test_run_lock",
    "blocked_by_unknown_command":        "blocked_by_shell_gate",
    "blocked_by_missing_task":           "blocked_by_task_contract", # promoted from missing-evidence
    "deny":                              "blocked_by_shell_gate",
}

# Shell gate allow-type decisions (never grant execution authorization)
_SG_ALLOW_DECISIONS: frozenset[str] = frozenset({
    "allow_read_only",
    "allow_governed",
    "allow_test_execution",
})

# Shell gate decisions that imply hard_block_present=True at the shell gate level
_SG_HARD_BLOCK_DECISIONS_SET: frozenset[str] = frozenset(_SG_HARD_BLOCK_TO_BROKER.keys())

# Performed/authorization keys that must never be True in sg evidence
_SG_PERFORMED_FORBIDDEN_KEYS: frozenset[str] = frozenset({
    "command_executed",
    "authorization_granted",
    "execution_authorized",
    "repo_mutation_performed",
    "backend_invocation_performed",
    "prompt_sent",
    "capture_performed",
    "intake_performed",
    "adoption_performed",
    "commit_performed",
    "push_performed",
    "raw_git_push_performed",
    "force_push_performed",
    "storage_written",
})

_SG_SCHEMA_VERSION: str = "0.1"

# Scope preflight decisions that map to broker blocks
_SPF_BLOCK_TO_BROKER: dict[str, str] = {
    "blocked_by_scope":                    "blocked_by_scope",
    "deny_preflight":                      "blocked_by_scope",
    "blocked_by_lifecycle_state":          "blocked_by_lifecycle_state",
    "blocked_by_missing_task_contract":    "blocked_by_task_contract",
    "blocked_by_must_never_repeat_control": "blocked_by_must_never_repeat",
    "blocked_by_risk":                     "blocked_by_risk",
}


def _check_sg_contradiction(
    sg_evidence: dict[str, Any],
    requested_action: str,
    human_approval_present: bool = False,
    accepted_risk_present: bool = False,
) -> list[str]:
    """
    Detect contradictions in shell gate evidence.
    Returns list of contradiction descriptions (empty = clean).
    Any non-empty result should yield blocked_by_conflicting_evidence.
    """
    details: list[str] = []
    sg_decision = sg_evidence.get("decision", "")
    command_category = sg_evidence.get("command_category", "")
    detected_flags = sg_evidence.get("detected_flags", {})
    sg_hard_block = sg_evidence.get("hard_block_present", False)

    # Schema version mismatch
    if sg_evidence.get("schema_version") != _SG_SCHEMA_VERSION:
        got = sg_evidence.get("schema_version")
        details.append(f"sg_schema_version_mismatch:expected_{_SG_SCHEMA_VERSION}_got_{got}")

    # Performed/authorization flags must never be True in sg evidence
    for key in _SG_PERFORMED_FORBIDDEN_KEYS:
        if sg_evidence.get(key) is True or detected_flags.get(key) is True:
            details.append(f"sg_performed_flag_true:{key}")

    # hard_block_present=True but decision is an allow decision
    if sg_hard_block and sg_decision in _SG_ALLOW_DECISIONS:
        details.append(f"sg_hard_block_with_allow_decision:{sg_decision}")

    # force_push_detected=True but decision is not blocked_by_force_push
    if detected_flags.get("force_push_detected") and sg_decision != "blocked_by_force_push":
        details.append(f"sg_force_push_flag_but_decision:{sg_decision}")

    # raw_git_push_detected=True but decision is an allow decision
    if detected_flags.get("raw_git_push_detected") and sg_decision in _SG_ALLOW_DECISIONS:
        details.append(f"sg_raw_git_push_flag_with_allow_decision:{sg_decision}")

    # Unknown category + allow decision
    if command_category == "unknown" and sg_decision in _SG_ALLOW_DECISIONS:
        details.append(f"sg_unknown_category_with_allow_decision:{sg_decision}")

    # Mutating broker action + allow_read_only from sg
    if requested_action in BPE_MUTATING_ACTIONS and sg_decision == "allow_read_only":
        details.append(f"sg_allow_read_only_for_mutating_action:{requested_action}")

    # Secret access evidence not redacted
    secret_detected = (
        detected_flags.get("secret_access_detected")
        or sg_evidence.get("secret_access_detected")
    )
    command_text = sg_evidence.get("command_text", "")
    if secret_detected and command_text != "<redacted_secret_access_command>":
        details.append("sg_secret_access_command_not_redacted")

    # Human approval alongside sg hard block
    if sg_hard_block and human_approval_present:
        details.append("human_approval_alongside_sg_hard_block")

    # Accepted risk alongside sg hard block
    if sg_hard_block and accepted_risk_present:
        details.append("accepted_risk_alongside_sg_hard_block")

    return details


def _broker_shell_gate_evidence(
    command_text: str,
    active_task_detected: bool,
    test_run_clear: bool,
) -> dict[str, Any]:
    """Collect shell gate evidence for the requested command."""
    classification = _classify_command(command_text)
    command_category = classification["command_category"]
    classify_reason_codes = classification["reason_codes"]
    detected_flags = classification["detected_flags"]
    decision, decision_reason_codes = _sg_decide(
        command_category, detected_flags, active_task_detected, test_run_clear
    )
    return {
        "command_text": command_text,
        "command_category": command_category,
        "decision": decision,
        "reason_codes": classify_reason_codes + decision_reason_codes,
        "detected_flags": detected_flags,
    }


def _broker_decide(
    requested_action: str,
    task_contract: dict | None,
    sg_evidence: dict | None,
    scope_decision: str | None,
    health_passed: bool | None,
    check_passed: bool | None,
    doctor_passed: bool | None,
    push_check_passed: bool | None,
    tests_passed: bool | None,
    test_run_clear: bool | None,
    human_review_present: bool,
    contradiction_details: list[str] | None = None,
) -> tuple[str, list[str], list[str]]:
    """
    Returns (decision, reason_codes, missing_evidence).
    Priority: SG hard blocks → contradiction detection → evidence failures
    → task contract → scope denial → test run lock → missing evidence
    → human review → allow_preflight_only.
    """
    reason_codes: list[str] = []
    missing_evidence: list[str] = []

    # 1. Shell gate hard blocks (checked before any evidence)
    if sg_evidence is not None:
        sg_decision = sg_evidence["decision"]

        # 1d. requires_active_task from shell gate when no task → hard block
        if sg_decision == "requires_active_task" and task_contract is None:
            reason_codes.append(f"shell_gate_decision:{sg_decision}")
            reason_codes.append("no_active_task_contract")
            return "blocked_by_task_contract", reason_codes, missing_evidence

        if sg_decision in _SG_HARD_BLOCK_TO_BROKER:
            broker_block = _SG_HARD_BLOCK_TO_BROKER[sg_decision]
            reason_codes.append(f"shell_gate_decision:{sg_decision}")
            return broker_block, reason_codes, missing_evidence

    # 2. Contradiction detection (immediately after SG hard blocks)
    if contradiction_details:
        reason_codes.append("contradictory_shell_gate_evidence")
        reason_codes.extend(contradiction_details)
        return "blocked_by_conflicting_evidence", reason_codes, missing_evidence

    # 3. Explicit evidence failures
    if health_passed is False:
        reason_codes.append("health_check_failed")
        return "blocked_by_failed_health", reason_codes, missing_evidence
    if check_passed is False:
        reason_codes.append("governance_check_failed")
        return "blocked_by_failed_check", reason_codes, missing_evidence
    if doctor_passed is False:
        reason_codes.append("doctor_check_failed")
        return "blocked_by_failed_doctor", reason_codes, missing_evidence
    if tests_passed is False:
        reason_codes.append("tests_failed")
        return "blocked_by_failed_tests", reason_codes, missing_evidence
    if push_check_passed is False and requested_action == "push":
        reason_codes.append("push_check_failed")
        return "blocked_by_push_check", reason_codes, missing_evidence

    # 4. Test run lock (when expensive test execution detected)
    if test_run_clear is False:
        reason_codes.append("test_run_lock_active")
        return "blocked_by_test_run_lock", reason_codes, missing_evidence

    # 5. Missing active task for mutating actions
    if requested_action in BPE_MUTATING_ACTIONS and task_contract is None:
        reason_codes.append("no_active_task_contract")
        return "blocked_by_task_contract", reason_codes, missing_evidence

    # 6. Scope preflight denial
    if scope_decision is not None and scope_decision in _SPF_BLOCK_TO_BROKER:
        broker_block = _SPF_BLOCK_TO_BROKER[scope_decision]
        reason_codes.append(f"scope_preflight_decision:{scope_decision}")
        return broker_block, reason_codes, missing_evidence

    # 7. Collect missing evidence (informational — may upgrade to requires_more_evidence)
    if sg_evidence is not None:
        sg_dec = sg_evidence["decision"]
        if sg_dec == "requires_more_evidence":
            missing_evidence.append("additional_evidence_for_command")
        elif sg_dec == "requires_preflight":
            missing_evidence.append("scope_preflight_for_command")
        elif sg_dec == "requires_active_task":
            # task present (otherwise fired at 1d) — constraint is satisfied
            pass

    if requested_action in BPE_MUTATING_ACTIONS:
        if health_passed is None:
            missing_evidence.append("health_check")
        if check_passed is None:
            missing_evidence.append("governance_check")

    if requested_action == "push" and push_check_passed is None:
        missing_evidence.append("push_check")

    if missing_evidence:
        reason_codes.append("missing_evidence_items")
        return "requires_more_evidence", reason_codes, missing_evidence

    # 8. Human review gate
    if sg_evidence is not None and sg_evidence["decision"] == "requires_human_review":
        if not human_review_present:
            reason_codes.append("shell_gate_requires_human_review")
            return "requires_human_review", reason_codes, missing_evidence

    if requested_action in (
        "adoption", "backend_invocation", "rollback", "storage_write", "push", "commit"
    ):
        if not human_review_present:
            reason_codes.append(f"action_requires_human_review:{requested_action}")
            return "requires_human_review", reason_codes, missing_evidence

    # 9. All checks pass — preflight only (not execution authorization)
    reason_codes.append("all_provided_evidence_passes")
    return "allow_preflight_only", reason_codes, missing_evidence


def build_permission_broker(
    repo_root: Path,
    requested_action: str,
    requested_files: list[str] | None = None,
    requested_command: str | None = None,
    source_backend: str | None = None,
    commit_message: str | None = None,
    push_target: str | None = None,
    health_passed: bool | None = None,
    check_passed: bool | None = None,
    doctor_passed: bool | None = None,
    push_check_passed: bool | None = None,
    tests_present: bool = False,
    tests_passed: bool | None = None,
    human_review_present: bool = False,
    human_approval_present: bool = False,
    accepted_risk_present: bool = False,
) -> dict[str, Any]:
    """
    Build the permission broker JSON envelope.

    Never executes requested_command.  Never invokes backends.  Never sends
    prompts.  Never writes storage.  All performed/authorization flags are
    unconditionally false.
    """
    now = datetime.now(timezone.utc).isoformat()
    files: list[str] = list(requested_files or [])

    task_contract = _detect_task_contract(repo_root)
    active_task_detected = task_contract is not None
    task_contract_path: str | None = task_contract["path"] if task_contract else None

    # Shell gate evidence (internal — no execution)
    sg_evidence: dict[str, Any] | None = None
    test_run_preflight_required = False
    test_run_clear: bool | None = None
    secret_detected = False
    if requested_command:
        classification = _classify_command(requested_command)
        command_category = classification["command_category"]
        detected_flags = classification["detected_flags"]

        test_run_preflight_required = (
            command_category == "test_execution"
            and detected_flags.get("expensive_test_execution_detected", False)
        )
        if test_run_preflight_required:
            test_run_clear = _call_doctor_test_run(repo_root)

        decision_for_sg, decision_reason_codes = _sg_decide(
            command_category, detected_flags, active_task_detected,
            test_run_clear if test_run_clear is not None else True,
        )
        sg_hard_block = decision_for_sg in _SG_HARD_BLOCK_DECISIONS_SET
        secret_detected = bool(detected_flags.get("secret_access_detected"))

        # Redact secret-access command text before storing in evidence
        stored_command_text = (
            "<redacted_secret_access_command>" if secret_detected else requested_command
        )

        sg_evidence = {
            "schema_version": _SG_SCHEMA_VERSION,
            "command_text": stored_command_text,
            "command_text_redacted": secret_detected,
            "command_category": command_category,
            "decision": decision_for_sg,
            "reason_codes": classification["reason_codes"] + decision_reason_codes,
            "detected_flags": detected_flags,
            "hard_block_present": sg_hard_block,
            "secret_access_detected": secret_detected,
        }

    # Contradiction detection (before _broker_decide so it can inject at priority 2)
    contradiction_details: list[str] = []
    if sg_evidence is not None:
        contradiction_details = _check_sg_contradiction(
            sg_evidence,
            requested_action,
            human_approval_present=human_approval_present,
            accepted_risk_present=accepted_risk_present,
        )

    # Scope preflight evidence (internal — no execution)
    scope_decision: str | None = None
    scope_preflight_envelope: dict[str, Any] | None = None
    if requested_action and files:
        scope_preflight_envelope = build_scope_preflight(repo_root, requested_action, files)
        scope_decision = scope_preflight_envelope["preflight"].get("decision")

    # Broker decision
    broker_decision, reason_codes, missing_evidence = _broker_decide(
        requested_action=requested_action,
        task_contract=task_contract,
        sg_evidence=sg_evidence,
        scope_decision=scope_decision,
        health_passed=health_passed,
        check_passed=check_passed,
        doctor_passed=doctor_passed,
        push_check_passed=push_check_passed,
        tests_passed=tests_passed,
        test_run_clear=test_run_clear,
        human_review_present=human_review_present,
        contradiction_details=contradiction_details,
    )

    hard_block_present = broker_decision in BPE_HARD_BLOCK_DECISIONS

    # Evidence sources collected
    evidence_sources: list[str] = []
    if task_contract_path:
        evidence_sources.append(task_contract_path)
    if sg_evidence is not None:
        cat_label = sg_evidence.get("command_category", "unknown")
        evidence_sources.append(f"pcae shell-gate classifier (internal) category:{cat_label}")
    if scope_preflight_envelope is not None:
        evidence_sources.append("pcae preflight scope (internal)")
    if test_run_preflight_required:
        evidence_sources.append("pcae doctor test-run")
    for flag_name, flag_val in [
        ("health_passed", health_passed),
        ("check_passed", check_passed),
        ("doctor_passed", doctor_passed),
        ("push_check_passed", push_check_passed),
    ]:
        if flag_val is not None:
            evidence_sources.append(f"explicit:{flag_name}={flag_val}")

    # Audit helpers
    sg_cmd_text_hash: str | None = None
    if sg_evidence is not None and not sg_evidence.get("command_text_redacted"):
        raw = sg_evidence.get("command_text", "")
        if raw:
            sg_cmd_text_hash = hashlib.sha256(raw.encode()).hexdigest()

    hard_block_sources: list[str] = []
    if sg_evidence is not None and sg_evidence.get("hard_block_present"):
        hard_block_sources.append("shell_gate")
    if hard_block_present and not hard_block_sources:
        hard_block_sources.append("broker")

    human_review_sources: list[str] = [
        rc for rc in reason_codes if "human_review" in rc or "shell_gate_requires" in rc
    ]

    broker_mapping_reason = (
        f"sg:{sg_evidence['decision'] if sg_evidence else 'none'}"
        f"->broker:{broker_decision}"
    )

    warnings: list[str] = []
    if contradiction_details:
        warnings.append(f"contradictions_detected:{len(contradiction_details)}")

    safety_notes: dict[str, bool] = {
        "permission_broker_prototype_only": True,
        "broker_does_not_execute_commands": True,
        "broker_does_not_intercept_shell": True,
        "broker_does_not_invoke_backends": True,
        "broker_does_not_send_prompts": True,
        "broker_does_not_capture_outputs": True,
        "broker_does_not_perform_intake": True,
        "broker_does_not_perform_adoption": True,
        "broker_does_not_mutate_repo": True,
        "broker_does_not_commit": True,
        "broker_does_not_push": True,
        "broker_does_not_write_storage": True,
        "broker_does_not_replace_human_review": True,
        "broker_does_not_override_hard_blocks": True,
        "execution_authorization_not_granted": True,
    }

    # Redact requested_command in the broker envelope when secret_access detected
    # (GAP-3 repair, 88V.1). The sg_evidence.command_text is already redacted;
    # the outer envelope field must also be redacted so serialized JSON is safe.
    safe_requested_command: str | None = requested_command
    if secret_detected:
        safe_requested_command = "<redacted_secret_access_command>"

    broker: dict[str, Any] = {
        "broker_type": "permission_broker_prototype",
        "requested_action": requested_action,
        "requested_files": files,
        "requested_command": safe_requested_command,
        "source_backend": source_backend,
        "commit_message": commit_message,
        "push_target": push_target,
        "decision": broker_decision,
        "reason_codes": reason_codes,
        "hard_block_present": hard_block_present,
        "active_task_detected": active_task_detected,
        "task_contract_path": task_contract_path,
        "shell_gate_evidence": sg_evidence,
        "scope_preflight_decision": scope_decision,
        "test_run_preflight_required": test_run_preflight_required,
        "test_run_clear_to_run": test_run_clear,
        "evidence_provided": {
            "health_passed": health_passed,
            "check_passed": check_passed,
            "doctor_passed": doctor_passed,
            "push_check_passed": push_check_passed,
            "tests_present": tests_present,
            "tests_passed": tests_passed,
            "human_review_present": human_review_present,
            "human_approval_present": human_approval_present,
            "accepted_risk_present": accepted_risk_present,
        },
        "evidence_sources": evidence_sources,
        "missing_evidence": missing_evidence,
        # Performed / authorization flags — unconditionally false (invariant)
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
        "safety_notes": safety_notes,
        # Audit fields (new in 88T)
        "shell_gate_schema_version": (
            sg_evidence.get("schema_version") if sg_evidence else None
        ),
        "shell_gate_command_category": (
            sg_evidence.get("command_category") if sg_evidence else None
        ),
        "shell_gate_command_text_hash": sg_cmd_text_hash,
        "shell_gate_command_text_redacted": (
            sg_evidence.get("command_text_redacted", False) if sg_evidence else False
        ),
        "shell_gate_decision": (
            sg_evidence.get("decision") if sg_evidence else None
        ),
        "shell_gate_reason_codes": (
            sg_evidence.get("reason_codes", []) if sg_evidence else []
        ),
        "shell_gate_hard_block_present": (
            sg_evidence.get("hard_block_present") if sg_evidence else None
        ),
        "conflicting_evidence_detected": bool(contradiction_details),
        "conflicting_evidence_details": contradiction_details,
        "hard_block_sources": hard_block_sources,
        "human_review_sources": human_review_sources,
        "accepted_risk_noted": accepted_risk_present,
        "broker_mapping_reason": broker_mapping_reason,
    }

    return {
        "schema_version": "0.1",
        "generated_at": now,
        "source_command": "pcae permission-broker evaluate",
        "repository_root": str(repo_root),
        "broker": broker,
        "warnings": warnings,
        "errors": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 91A — Simulation-only permission broker decision model
# ═══════════════════════════════════════════════════════════════════════════════

# Decision outcomes (4-value model per 90A/90C)
BROKER_ALLOW = "allow"
BROKER_DENY = "deny"
BROKER_HUMAN_REVIEW = "human_review"
BROKER_MORE_EVIDENCE = "more_evidence"

BROKER_DECISIONS_91A: tuple[str, ...] = (
    BROKER_ALLOW,
    BROKER_DENY,
    BROKER_HUMAN_REVIEW,
    BROKER_MORE_EVIDENCE,
)

# Action types the broker can evaluate
ACTION_READ = "read"
ACTION_SOURCE_MUTATION = "source_mutation"
ACTION_DOCS_MUTATION = "docs_mutation"
ACTION_TEST_MUTATION = "test_mutation"
ACTION_BACKEND_INVOCATION = "backend_invocation"
ACTION_COMMIT = "commit"
ACTION_PUSH = "push"
ACTION_ROLLBACK = "rollback"

KNOWN_ACTIONS_91A: frozenset[str] = frozenset({
    ACTION_READ,
    ACTION_SOURCE_MUTATION,
    ACTION_DOCS_MUTATION,
    ACTION_TEST_MUTATION,
    ACTION_BACKEND_INVOCATION,
    ACTION_COMMIT,
    ACTION_PUSH,
    ACTION_ROLLBACK,
})

# Command classes
CMD_READ_ONLY = "read_only"
CMD_GOVERNED = "governed"
CMD_RAW_GIT_COMMIT = "raw_git_commit"
CMD_RAW_GIT_PUSH = "raw_git_push"
CMD_FORCE_PUSH = "force_push"
CMD_NO_VERIFY = "no_verify"
CMD_DESTRUCTIVE_FS = "destructive_filesystem"
CMD_BACKEND = "backend_invocation"
CMD_UNKNOWN = "unknown"

KNOWN_COMMAND_CLASSES_91A: frozenset[str] = frozenset({
    CMD_READ_ONLY,
    CMD_GOVERNED,
    CMD_RAW_GIT_COMMIT,
    CMD_RAW_GIT_PUSH,
    CMD_FORCE_PUSH,
    CMD_NO_VERIFY,
    CMD_DESTRUCTIVE_FS,
    CMD_BACKEND,
    CMD_UNKNOWN,
})

# Hard-block command classes — non-overridable (88V §16)
HARD_BLOCK_COMMAND_CLASSES: frozenset[str] = frozenset({
    CMD_RAW_GIT_COMMIT,
    CMD_RAW_GIT_PUSH,
    CMD_FORCE_PUSH,
    CMD_NO_VERIFY,
    CMD_DESTRUCTIVE_FS,
    CMD_UNKNOWN,
})

# Hard-block reason codes per command class
HARD_BLOCK_REASONS: dict[str, str] = {
    CMD_RAW_GIT_COMMIT: "blocked_by_raw_git_commit",
    CMD_RAW_GIT_PUSH: "blocked_by_raw_git_push",
    CMD_FORCE_PUSH: "blocked_by_force_push",
    CMD_NO_VERIFY: "blocked_by_no_verify",
    CMD_DESTRUCTIVE_FS: "blocked_by_destructive_filesystem",
    CMD_UNKNOWN: "blocked_by_unknown_command_class",
}

# Actions that require an active task
MUTATING_ACTIONS_91A: frozenset[str] = frozenset({
    ACTION_SOURCE_MUTATION,
    ACTION_DOCS_MUTATION,
    ACTION_TEST_MUTATION,
    ACTION_COMMIT,
    ACTION_PUSH,
    ACTION_ROLLBACK,
})

# Policy-forbidden files (from 88N.3, 90A)
POLICY_FORBIDDEN_FILES_91A: frozenset[str] = frozenset({
    "README.md",
    "docs/REAL_CAPTURED_TASKS.md",
    "docs/LINKEDIN_ARTICLE_DRAFT.md",
})


def evaluate_permission_broker(
    *,
    action_type: str,
    command_class: str = CMD_UNKNOWN,
    paths: tuple[str, ...] = (),
    task_present: bool = False,
    task_scope_known: bool = False,
    allowed_paths: tuple[str, ...] = (),
    forbidden_paths: tuple[str, ...] = (),
    approval_present: bool = False,
    approval_fresh: bool = True,
    accepted_risk_present: bool = False,
    readiness_ready: bool = False,
    enforcement_authorized: bool = False,
    repo_dirty: bool = False,
    metadata: dict[str, str] | None = None,
) -> dict[str, object]:
    """
    Evaluate a proposed governed action and return a simulation-only
    permission broker decision.

    Phase 91A — simulation prototype.  Never executes commands, never
    intercepts shell, never invokes backends, never grants authorization.

    Returns a dict with keys:
      decision        — one of allow / deny / human_review / more_evidence
      hard_block      — True if the block is non-overridable (88V §16)
      reason_code     — primary machine-readable reason
      reason_codes    — all reason codes (list)
      message          — human-readable operator message
      required_evidence — list of evidence items needed (empty if allow/deny)
      audit_payload    — dict with audit-relevant fields
    """

    reason_codes: list[str] = []
    required_evidence: list[str] = []

    # ── 0. Validate required inputs ──────────────────────────────────────
    if not action_type:
        return _broker_decision(
            BROKER_MORE_EVIDENCE, False,
            "missing_action_type",
            ["missing_action_type"],
            "No action type provided. Cannot evaluate.",
            ["action_type"],
        )

    if action_type not in KNOWN_ACTIONS_91A:
        return _broker_decision(
            BROKER_MORE_EVIDENCE, False,
            "unknown_action_type",
            ["unknown_action_type", f"action_type:{action_type}"],
            f"Unknown action type: {action_type!r}. Cannot evaluate.",
            ["valid_action_type"],
        )

    if command_class not in KNOWN_COMMAND_CLASSES_91A:
        return _broker_decision(
            BROKER_DENY, True,
            "blocked_by_unknown_command_class",
            ["unknown_command_class", f"command_class:{command_class}"],
            f"Unknown or ambiguous command class: {command_class!r}. "
            f"PCAE must fail closed on unknown commands.",
            [],
        )

    # ── 1. Hard-block command classes (non-overridable) ──────────────────
    if command_class in HARD_BLOCK_COMMAND_CLASSES:
        reason = HARD_BLOCK_REASONS.get(command_class, "blocked_by_policy")
        reason_codes.append(reason)
        return _broker_decision(
            BROKER_DENY, True,
            reason,
            reason_codes,
            f"Hard block: {command_class}. This action is permanently "
            f"blocked by PCAE policy. No override exists (88V §16).",
            [],
        )

    # ── 2. Enforcement readiness gates ───────────────────────────────────
    if not enforcement_authorized and action_type in MUTATING_ACTIONS_91A:
        reason_codes.append("enforcement_not_authorized")
        return _broker_decision(
            BROKER_DENY, True,
            "blocked_by_enforcement_not_authorized",
            reason_codes,
            "Enforcement is not authorized. Mutating actions are blocked.",
            ["enforcement_authorization"],
        )

    if not readiness_ready and action_type in MUTATING_ACTIONS_91A:
        reason_codes.append("enforcement_not_ready")
        return _broker_decision(
            BROKER_DENY, True,
            "blocked_by_enforcement_not_ready",
            reason_codes,
            "Enforcement readiness gates are not satisfied. "
            "Mutating actions are blocked.",
            ["readiness_gates"],
        )

    # ── 3. Task contract checks ──────────────────────────────────────────
    if action_type in MUTATING_ACTIONS_91A and not task_present:
        reason_codes.append("missing_active_task")
        return _broker_decision(
            BROKER_DENY, True,
            "blocked_by_missing_task",
            reason_codes,
            "No active task contract. Mutating actions require an active task.",
            ["active_task_contract"],
        )

    if action_type in MUTATING_ACTIONS_91A and not task_scope_known:
        reason_codes.append("task_scope_unknown")
        required_evidence.append("task_scope")
        return _broker_decision(
            BROKER_MORE_EVIDENCE, False,
            "task_scope_unknown",
            reason_codes,
            "Task contract scope is unknown or incomplete. "
            "Cannot evaluate file scope.",
            required_evidence,
        )

    # ── 4. Path/scope checks ─────────────────────────────────────────────
    if paths:
        # Check for policy-forbidden files (independent of task scope)
        policy_forbidden = [p for p in paths if p in POLICY_FORBIDDEN_FILES_91A]
        if policy_forbidden:
            reason_codes.append("policy_forbidden_file")
            reason_codes.append(f"forbidden:{','.join(policy_forbidden)}")
            return _broker_decision(
                BROKER_DENY, True,
                "blocked_by_policy_forbidden_file",
                reason_codes,
                f"Policy-forbidden file(s) requested: "
                f"{', '.join(policy_forbidden)}. "
                f"These files are never mutable.",
                [],
            )

        # Check for out-of-scope paths (when task scope is known)
        if task_scope_known and allowed_paths:
            out_of_scope = [
                p for p in paths
                if p not in allowed_paths and p not in POLICY_FORBIDDEN_FILES_91A
            ]
            if out_of_scope:
                reason_codes.append("out_of_scope_path")
                reason_codes.append(f"out_of_scope:{','.join(out_of_scope)}")
                return _broker_decision(
                    BROKER_DENY, True,
                    "blocked_by_out_of_scope",
                    reason_codes,
                    f"Path(s) outside active task scope: "
                    f"{', '.join(out_of_scope)}.",
                    [],
                )

        # Check for explicitly forbidden paths
        if forbidden_paths:
            forbidden_matches = [p for p in paths if p in forbidden_paths]
            if forbidden_matches:
                reason_codes.append("forbidden_path")
                reason_codes.append(f"forbidden:{','.join(forbidden_matches)}")
                return _broker_decision(
                    BROKER_DENY, True,
                    "blocked_by_forbidden_path",
                    reason_codes,
                    f"Path(s) in task forbidden list: "
                    f"{', '.join(forbidden_matches)}.",
                    [],
                )

    # ── 5. Backend invocation check ──────────────────────────────────────
    if command_class == CMD_BACKEND or action_type == ACTION_BACKEND_INVOCATION:
        # Backend invocation requires human review (not a hard block)
        reason_codes.append("backend_invocation_requires_review")
        return _broker_decision(
            BROKER_HUMAN_REVIEW, False,
            "backend_invocation_requires_human_review",
            reason_codes,
            "Backend invocation requires human review before proceeding.",
            ["human_review"],
        )

    # ── 6. Dirty repo check ──────────────────────────────────────────────
    if repo_dirty and action_type in (ACTION_COMMIT, ACTION_PUSH):
        reason_codes.append("repo_dirty")
        return _broker_decision(
            BROKER_MORE_EVIDENCE, False,
            "repo_dirty_for_commit_push",
            reason_codes,
            "Working tree is dirty. Commit/push actions require a clean "
            "working tree or explicit staging.",
            ["clean_working_tree"],
        )

    # ── 7. Human review for high-risk non-hard-block actions ─────────────
    if action_type in (ACTION_COMMIT, ACTION_PUSH, ACTION_ROLLBACK):
        if not approval_present:
            reason_codes.append(f"{action_type}_requires_human_review")
            return _broker_decision(
                BROKER_HUMAN_REVIEW, False,
                f"{action_type}_requires_human_review",
                reason_codes,
                f"Action '{action_type}' requires human review and approval.",
                ["human_approval"],
            )
        if not approval_fresh:
            reason_codes.append("approval_stale")
            return _broker_decision(
                BROKER_HUMAN_REVIEW, False,
                "stale_approval",
                reason_codes,
                "Approval is expired or revoked. Fresh approval required.",
                ["fresh_approval"],
            )

    # ── 8. Accepted risk for reviewable non-hard-block cases ─────────────
    if accepted_risk_present and action_type not in MUTATING_ACTIONS_91A:
        # Accepted risk on non-mutating actions: allow with note
        reason_codes.append("accepted_risk_noted")
        reason_codes.append("risk_does_not_override_hard_blocks")

    # ── 9. All checks pass — allow (preflight only, not authorization) ──
    reason_codes.append("all_checks_passed")
    return _broker_decision(
        BROKER_ALLOW, False,
        "allow_preflight_only",
        reason_codes,
        "All governance checks passed. This is a preflight-only evaluation. "
        "PCAE does NOT authorize execution. The operator retains full authority.",
        [],
    )


def _broker_decision(
    decision: str,
    hard_block: bool,
    reason_code: str,
    reason_codes: list[str],
    message: str,
    required_evidence: list[str],
) -> dict[str, object]:
    """Build a broker decision envelope (91A model).

    Simulation-only.  No execution, no authorization, no enforcement.
    """
    import uuid
    import hashlib
    from datetime import datetime, timezone

    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    message_hash = hashlib.sha256(message.encode()).hexdigest()[:16]

    return {
        "decision": decision,
        "hard_block": hard_block,
        "reason_code": reason_code,
        "reason_codes": reason_codes,
        "message": message,
        "required_evidence": required_evidence,
        "audit_payload": {
            "event_id": event_id,
            "event_type": (
                "enforcement.blocked" if hard_block
                else "enforcement.gated_review" if decision == BROKER_HUMAN_REVIEW
                else "enforcement.allowed" if decision == BROKER_ALLOW
                else "enforcement.decision"
            ),
            "timestamp": now,
            "decision": decision,
            "hard_block": hard_block,
            "overridable": not hard_block,
            "reason_code": reason_code,
            "message_hash": message_hash,
            "required_evidence": required_evidence,
        },
        "simulation_only": True,
        "no_execution": True,
        "no_enforcement": True,
        "authorization_granted": False,
        "execution_authorized": False,
        "schema_version": "1.0",
    }
