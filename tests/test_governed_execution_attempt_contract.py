"""Tests for governed execution attempt contract freeze — Phase 99B.

Contract-freeze only. Freezes the 99A GovernedExecutionAttemptBoundary artifact
schema, attempt states, denial reasons, hard no-go semantics, prerequisite
semantics, denial/abort/fail-closed semantics, authorization flags, digest
behavior, and compatibility rules.

No execution. No enforcement. All authorization flags must remain False.
"""

from __future__ import annotations

import hashlib
import json as _json
import pytest

from pcae.core.backend_invocations import (
    GovernedExecutionAttemptBoundary,
    # ── States ──
    GEA_UNAVAILABLE, GEA_NOT_REQUESTED, GEA_REQUEST_DRAFTED,
    GEA_PREFLIGHT_REQUIRED, GEA_PREFLIGHT_FAILED,
    GEA_APPROVAL_REQUIRED, GEA_AUDIT_REQUIRED, GEA_ROLLBACK_REQUIRED,
    GEA_DENIED, GEA_ABORTED_BEFORE_EXECUTION,
    GEA_BLOCKED_BY_NO_GO, GEA_BLOCKED_BY_MISSING_EVIDENCE,
    GEA_BLOCKED_BY_FAILED_VERIFICATION, GEA_READY_FOR_DESIGN_REVIEW_ONLY,
    # ── Future-only states ──
    GEA_EXECUTING_FUTURE, GEA_EXECUTED_FUTURE, GEA_RUNNING_FUTURE,
    GEA_INVOKED_FUTURE, GEA_APPLIED_FUTURE, GEA_COMMITTED_FUTURE,
    GEA_PUSHED_FUTURE, GEA_SUCCESS_FUTURE, GEA_EXECUTION_COMPLETE_FUTURE,
    VALID_GEA_STATES, UNAVAILABLE_GEA_STATES,
    # ── Denial reasons ──
    VALID_GEA_DENIAL_REASONS,
    GEA_DENIED_MISSING_PHASE97, GEA_DENIED_INVALID_PHASE97,
    GEA_DENIED_MISSING_PHASE98, GEA_DENIED_INVALID_PHASE98,
    GEA_DENIED_NO_GO_PRESENT, GEA_DENIED_MISSING_APPROVAL,
    GEA_DENIED_APPROVAL_EXPIRED, GEA_DENIED_APPROVAL_REVOKED,
    GEA_DENIED_MISSING_AUDIT, GEA_DENIED_MISSING_ROLLBACK,
    GEA_DENIED_FAILED_VERIFICATION, GEA_DENIED_FAILED_REF_VALIDATION,
    GEA_DENIED_UNKNOWN_SCHEMA, GEA_DENIED_CONFLICTING_FLAGS,
    GEA_DENIED_UNSAFE_AUTH_FLAG,
    GEA_DENIED_BACKEND_REQUESTED, GEA_DENIED_ADAPTER_REQUESTED,
    GEA_DENIED_SUBPROCESS_REQUESTED, GEA_DENIED_SHELL_REQUESTED,
    GEA_DENIED_NETWORK_REQUESTED, GEA_DENIED_TELEGRAM_INBOUND,
    GEA_DENIED_APPLY_REQUESTED, GEA_DENIED_ROLLBACK_EXEC_REQUESTED,
    GEA_DENIED_COMMIT_PUSH_REQUESTED,
    GEA_DENIED_BYPASS_PERMISSIONS, GEA_DENIED_SECRET_DETECTED,
)

# ═══════════════════════════════════════════════════════════════════════════
# Constants frozen from 99A
# ═══════════════════════════════════════════════════════════════════════════

_ALL_14_VALID_STATES = frozenset({
    GEA_UNAVAILABLE, GEA_NOT_REQUESTED, GEA_REQUEST_DRAFTED,
    GEA_PREFLIGHT_REQUIRED, GEA_PREFLIGHT_FAILED,
    GEA_APPROVAL_REQUIRED, GEA_AUDIT_REQUIRED, GEA_ROLLBACK_REQUIRED,
    GEA_DENIED, GEA_ABORTED_BEFORE_EXECUTION,
    GEA_BLOCKED_BY_NO_GO, GEA_BLOCKED_BY_MISSING_EVIDENCE,
    GEA_BLOCKED_BY_FAILED_VERIFICATION, GEA_READY_FOR_DESIGN_REVIEW_ONLY,
})

_ALL_9_FUTURE_STATES = frozenset({
    GEA_EXECUTING_FUTURE, GEA_EXECUTED_FUTURE, GEA_RUNNING_FUTURE,
    GEA_INVOKED_FUTURE, GEA_APPLIED_FUTURE, GEA_COMMITTED_FUTURE,
    GEA_PUSHED_FUTURE, GEA_SUCCESS_FUTURE, GEA_EXECUTION_COMPLETE_FUTURE,
})

_ALL_26_DENIAL_REASONS = frozenset({
    GEA_DENIED_MISSING_PHASE97, GEA_DENIED_INVALID_PHASE97,
    GEA_DENIED_MISSING_PHASE98, GEA_DENIED_INVALID_PHASE98,
    GEA_DENIED_NO_GO_PRESENT, GEA_DENIED_MISSING_APPROVAL,
    GEA_DENIED_APPROVAL_EXPIRED, GEA_DENIED_APPROVAL_REVOKED,
    GEA_DENIED_MISSING_AUDIT, GEA_DENIED_MISSING_ROLLBACK,
    GEA_DENIED_FAILED_VERIFICATION, GEA_DENIED_FAILED_REF_VALIDATION,
    GEA_DENIED_UNKNOWN_SCHEMA, GEA_DENIED_CONFLICTING_FLAGS,
    GEA_DENIED_UNSAFE_AUTH_FLAG,
    GEA_DENIED_BACKEND_REQUESTED, GEA_DENIED_ADAPTER_REQUESTED,
    GEA_DENIED_SUBPROCESS_REQUESTED, GEA_DENIED_SHELL_REQUESTED,
    GEA_DENIED_NETWORK_REQUESTED, GEA_DENIED_TELEGRAM_INBOUND,
    GEA_DENIED_APPLY_REQUESTED, GEA_DENIED_ROLLBACK_EXEC_REQUESTED,
    GEA_DENIED_COMMIT_PUSH_REQUESTED,
    GEA_DENIED_BYPASS_PERMISSIONS, GEA_DENIED_SECRET_DETECTED,
})

_12_AUTH_FLAGS = [
    "execution_available", "execution_authorized",
    "backend_invocation_authorized", "adapter_execution_authorized",
    "network_authorized", "subprocess_authorized",
    "shell_authorized", "mutation_authorized",
    "apply_authorized", "rollback_authorized",
    "commit_authorized", "push_authorized",
]

_5_SAFETY_FLAGS = [
    "simulation_only", "no_execution", "evidence_only",
    "non_authorizing", "design_only",
]

_TO_DICT_REQUIRED_KEYS = frozenset({
    "schema_version", "attempt_boundary_id", "phase_id", "task_id",
    "generated_at_utc", "attempt_state", "attempt_decision",
    "phase97_preflight_ref", "phase97_preflight_digest",
    "phase98_preflight_ref", "phase98_preflight_digest",
    "approval_ref", "audit_readiness_ref", "rollback_readiness_ref",
    "backend_contract_ref", "adapter_boundary_ref",
    "artifact_verification_ref", "no_go_review_ref",
    "execution_boundary_proof_ref",
    "hard_no_go_conditions", "missing_prerequisites", "failed_checks",
    "denial_reasons", "abort_reasons", "evidence_refs", "warnings",
    "authorization_summary",
    "simulation_only", "no_execution", "evidence_only",
    "non_authorizing", "design_only", "digest",
})

# Fields NOT in digest payload (per 99A implementation)
_DIGEST_EXCLUDED_REFS = frozenset({
    "approval_ref", "audit_readiness_ref", "rollback_readiness_ref",
    "backend_contract_ref", "adapter_boundary_ref",
    "artifact_verification_ref", "no_go_review_ref",
    "execution_boundary_proof_ref",
})


# ═══════════════════════════════════════════════════════════════════════════
# 1. Schema field freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestSchemaFieldFreeze:
    """Assert 33 top-level fields in to_dict() with correct types."""

    def test_to_dict_has_exactly_33_keys(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        assert len(d) == 33

    def test_all_required_keys_present(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        for key in sorted(_TO_DICT_REQUIRED_KEYS):
            assert key in d, f"missing required key: {key}"

    def test_no_extra_keys_beyond_expected(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        assert set(d.keys()) == _TO_DICT_REQUIRED_KEYS

    def test_schema_version_is_stable(self):
        a = GovernedExecutionAttemptBoundary()
        assert a.schema_version == "1.0"
        assert a.to_dict()["schema_version"] == "1.0"

    def test_attempt_boundary_id_is_str(self):
        a = GovernedExecutionAttemptBoundary()
        assert isinstance(a.attempt_boundary_id, str)
        assert isinstance(a.to_dict()["attempt_boundary_id"], str)

    def test_phase_id_is_stable(self):
        a = GovernedExecutionAttemptBoundary()
        assert a.phase_id == "99A"

    def test_task_id_is_str(self):
        a = GovernedExecutionAttemptBoundary()
        assert isinstance(a.task_id, str)

    def test_generated_at_utc_is_str(self):
        a = GovernedExecutionAttemptBoundary()
        assert isinstance(a.generated_at_utc, str)

    def test_attempt_state_type(self):
        a = GovernedExecutionAttemptBoundary()
        assert isinstance(a.attempt_state, str)
        assert isinstance(a.to_dict()["attempt_state"], str)

    def test_attempt_decision_type(self):
        a = GovernedExecutionAttemptBoundary()
        assert isinstance(a.attempt_decision, str)
        assert isinstance(a.to_dict()["attempt_decision"], str)

    def test_all_ref_fields_are_str(self):
        ref_fields = [
            "phase97_preflight_ref", "phase97_preflight_digest",
            "phase98_preflight_ref", "phase98_preflight_digest",
            "approval_ref", "audit_readiness_ref", "rollback_readiness_ref",
            "backend_contract_ref", "adapter_boundary_ref",
            "artifact_verification_ref", "no_go_review_ref",
            "execution_boundary_proof_ref",
        ]
        a = GovernedExecutionAttemptBoundary()
        d = a.to_dict()
        for field in ref_fields:
            assert isinstance(getattr(a, field), str), f"{field} not str"
            assert isinstance(d[field], str), f"{field} not str in dict"

    def test_all_list_fields_are_list(self):
        list_fields = [
            "hard_no_go_conditions", "missing_prerequisites", "failed_checks",
            "denial_reasons", "abort_reasons", "evidence_refs", "warnings",
        ]
        a = GovernedExecutionAttemptBoundary()
        d = a.to_dict()
        for field in list_fields:
            assert isinstance(getattr(a, field), list), f"{field} not list"
            assert isinstance(d[field], list), f"{field} not list in dict"

    def test_all_bool_fields_are_bool(self):
        bool_fields = _12_AUTH_FLAGS + _5_SAFETY_FLAGS
        a = GovernedExecutionAttemptBoundary()
        d = a.to_dict()
        for field in bool_fields:
            assert isinstance(getattr(a, field), bool), f"{field} not bool"

    def test_digest_is_str(self):
        a = GovernedExecutionAttemptBoundary()
        a.digest = a.compute_digest()
        assert isinstance(a.digest, str)
        assert isinstance(a.to_dict()["digest"], str)

    def test_no_required_field_silently_dropped_from_json(self):
        """Round-trip: every required key survives to_dict -> JSON -> parse."""
        a = GovernedExecutionAttemptBoundary()
        a.digest = a.compute_digest()
        d = a.to_dict()
        j = _json.dumps(d)
        parsed = _json.loads(j)
        for key in sorted(_TO_DICT_REQUIRED_KEYS):
            assert key in parsed, f"field {key!r} dropped in JSON round-trip"

    def test_authorization_summary_is_dict(self):
        a = GovernedExecutionAttemptBoundary()
        d = a.to_dict()
        assert isinstance(d["authorization_summary"], dict)

    def test_authorization_summary_has_all_12_flags(self):
        a = GovernedExecutionAttemptBoundary()
        d = a.to_dict()
        for flag in _12_AUTH_FLAGS:
            assert flag in d["authorization_summary"], (
                f"auth flag {flag!r} missing from authorization_summary"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 2. Attempt state freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestAttemptStateFreeze:
    """Assert exactly 14 valid states, 9 future-only, frozen semantics."""

    def test_exactly_14_valid_states(self):
        assert len(VALID_GEA_STATES) == 14

    def test_valid_states_match_expected(self):
        assert VALID_GEA_STATES == _ALL_14_VALID_STATES

    def test_exactly_9_future_states(self):
        assert len(UNAVAILABLE_GEA_STATES) == 9

    def test_future_states_match_expected(self):
        assert UNAVAILABLE_GEA_STATES == _ALL_9_FUTURE_STATES

    def test_valid_and_future_disjoint(self):
        assert VALID_GEA_STATES.isdisjoint(UNAVAILABLE_GEA_STATES)

    def test_all_states_are_stable_strings(self):
        for state in VALID_GEA_STATES | UNAVAILABLE_GEA_STATES:
            assert isinstance(state, str)
            assert state == state.lower()
            assert " " not in state

    @pytest.mark.parametrize("state", sorted(_ALL_14_VALID_STATES))
    def test_each_valid_state_accepted(self, state):
        a = GovernedExecutionAttemptBoundary(attempt_state=state)
        issues = a.validate()
        assert not any("invalid attempt_state" in i for i in issues), (
            f"valid state {state!r} rejected"
        )

    def test_unknown_state_fails_validation(self):
        a = GovernedExecutionAttemptBoundary(attempt_state="launching")
        issues = a.validate()
        assert any("invalid attempt_state" in i for i in issues)

    def test_no_state_means_executing(self):
        """No current state represents 'executing' as valid."""
        assert "executing" not in VALID_GEA_STATES

    def test_no_state_means_executed(self):
        assert "executed" not in VALID_GEA_STATES

    def test_no_state_means_running(self):
        assert "running" not in VALID_GEA_STATES

    def test_no_state_means_invoked(self):
        assert "invoked" not in VALID_GEA_STATES

    def test_no_state_means_applied(self):
        assert "applied" not in VALID_GEA_STATES

    def test_no_state_means_committed(self):
        assert "committed" not in VALID_GEA_STATES

    def test_no_state_means_pushed(self):
        assert "pushed" not in VALID_GEA_STATES

    def test_ready_for_design_review_is_non_authorizing(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_READY_FOR_DESIGN_REVIEW_ONLY,
        )
        assert a.execution_available is False
        assert a.non_authorizing is True
        assert a.design_only is True

    def test_blocked_denied_aborted_states_non_executing(self):
        blocked_etc = {
            GEA_DENIED, GEA_ABORTED_BEFORE_EXECUTION,
            GEA_BLOCKED_BY_NO_GO, GEA_BLOCKED_BY_MISSING_EVIDENCE,
            GEA_BLOCKED_BY_FAILED_VERIFICATION,
        }
        for state in blocked_etc:
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            assert a.no_execution is True, f"{state} should have no_execution=True"
            assert a.execution_available is False, (
                f"{state} should have execution_available=False"
            )

    def test_all_future_states_fail_validation(self):
        for state in sorted(UNAVAILABLE_GEA_STATES):
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            issues = a.validate()
            assert any("future-only" in i for i in issues), (
                f"future state {state!r} should report future-only"
            )

    def test_default_state_is_unavailable(self):
        a = GovernedExecutionAttemptBoundary()
        assert a.attempt_state == GEA_UNAVAILABLE

    def test_default_decision_is_denied(self):
        a = GovernedExecutionAttemptBoundary()
        assert a.attempt_decision == GEA_DENIED


# ═══════════════════════════════════════════════════════════════════════════
# 3. Denial reason freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestDenialReasonFreeze:
    """Assert exactly 26 denial reasons, frozen semantics."""

    def test_exactly_26_denial_reasons(self):
        assert len(VALID_GEA_DENIAL_REASONS) == 26

    def test_denial_reasons_match_expected(self):
        assert VALID_GEA_DENIAL_REASONS == _ALL_26_DENIAL_REASONS

    def test_all_denial_reasons_are_stable_strings(self):
        for reason in VALID_GEA_DENIAL_REASONS:
            assert isinstance(reason, str)
            assert reason.startswith("denied_"), (
                f"denial reason {reason!r} should start with 'denied_'"
            )

    @pytest.mark.parametrize("reason", sorted(_ALL_26_DENIAL_REASONS))
    def test_each_denial_reason_accepted(self, reason):
        a = GovernedExecutionAttemptBoundary(denial_reasons=[reason])
        issues = a.validate()
        assert not any("unknown denial_reason" in i for i in issues), (
            f"valid denial reason {reason!r} rejected"
        )

    def test_unknown_denial_reason_fails_validation(self):
        a = GovernedExecutionAttemptBoundary(denial_reasons=["not_a_real_reason_xyz"])
        issues = a.validate()
        assert any("unknown denial_reason" in i for i in issues)

    def test_denial_reasons_are_non_authorizing(self):
        """Any denial reason keeps all auth flags False."""
        for reason in sorted(_ALL_26_DENIAL_REASONS):
            a = GovernedExecutionAttemptBoundary(denial_reasons=[reason])
            assert a.execution_available is False, reason
            assert a.execution_authorized is False, reason
            assert a.push_authorized is False, reason
            assert a.non_authorizing is True, reason

    def test_denial_reasons_not_overridden_by_approval_ref(self):
        a = GovernedExecutionAttemptBoundary(
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
            approval_ref="some-approval-123",
        )
        assert a.denial_reasons == [GEA_DENIED_NO_GO_PRESENT]
        assert a.execution_available is False

    def test_denial_reasons_not_overridden_by_audit_rollback_refs(self):
        a = GovernedExecutionAttemptBoundary(
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
            audit_readiness_ref="audit-123",
            rollback_readiness_ref="rollback-123",
        )
        assert a.denial_reasons == [GEA_DENIED_NO_GO_PRESENT]
        assert a.execution_available is False

    def test_denial_reasons_not_overridden_by_preflight_refs(self):
        a = GovernedExecutionAttemptBoundary(
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
            phase97_preflight_ref="p97-123",
            phase97_preflight_digest="abc123",
            phase98_preflight_ref="p98-123",
            phase98_preflight_digest="def456",
        )
        assert a.denial_reasons == [GEA_DENIED_NO_GO_PRESENT]
        assert a.execution_available is False

    def test_denial_reasons_do_not_set_any_auth_flag_true(self):
        a = GovernedExecutionAttemptBoundary(
            denial_reasons=list(_ALL_26_DENIAL_REASONS),
        )
        assert a.execution_available is False
        assert a.execution_authorized is False
        assert a.backend_invocation_authorized is False
        assert a.adapter_execution_authorized is False
        assert a.network_authorized is False
        assert a.subprocess_authorized is False
        assert a.shell_authorized is False
        assert a.mutation_authorized is False
        assert a.apply_authorized is False
        assert a.rollback_authorized is False
        assert a.commit_authorized is False
        assert a.push_authorized is False

    def test_denial_reason_change_affects_digest(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
        )
        assert a1.compute_digest() != a2.compute_digest()


# ═══════════════════════════════════════════════════════════════════════════
# 4. Hard no-go semantics freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestHardNoGoFreeze:
    """Assert hard no-go conditions are non-overridable, always block/deny."""

    def test_hard_no_go_conditions_non_overridable(self):
        """Hard no-go present → still denied even with all refs filled."""
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["unsafe_execution_path"],
            approval_ref="approved-123",
            audit_readiness_ref="audit-ok",
            rollback_readiness_ref="rollback-ok",
            phase97_preflight_ref="p97-ok",
            phase97_preflight_digest="sha256ok",
            phase98_preflight_ref="p98-ok",
            phase98_preflight_digest="sha256ok",
        )
        # Hard no-go conditions are stored and visible
        assert "unsafe_execution_path" in a.hard_no_go_conditions
        # Auth flags remain False
        assert a.execution_available is False

    def test_hard_no_go_always_deny_or_block(self):
        states_with_no_go = [
            GEA_BLOCKED_BY_NO_GO,
            GEA_DENIED,
        ]
        for state in states_with_no_go:
            a = GovernedExecutionAttemptBoundary(
                attempt_state=state,
                hard_no_go_conditions=["test_condition"],
            )
            assert a.execution_available is False
            assert a.no_execution is True

    def test_hard_no_go_keeps_all_auth_flags_false(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["condition_a", "condition_b"],
        )
        assert a.execution_available is False
        assert a.execution_authorized is False
        assert a.push_authorized is False
        assert a.apply_authorized is False
        assert a.commit_authorized is False

    def test_hard_no_go_visible_in_artifact(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["visible_condition"],
        )
        d = a.to_dict()
        assert "visible_condition" in d["hard_no_go_conditions"]

    def test_hard_no_go_changes_affect_digest(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["new_condition"],
        )
        assert a1.compute_digest() != a2.compute_digest()

    def test_approval_cannot_override_hard_no_go(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["no_go_x"],
            approval_ref="approved",
        )
        assert "no_go_x" in a.hard_no_go_conditions
        assert a.execution_available is False

    def test_audit_readiness_cannot_override_hard_no_go(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["no_go_y"],
            audit_readiness_ref="audit-ready",
        )
        assert a.execution_available is False

    def test_rollback_readiness_cannot_override_hard_no_go(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["no_go_z"],
            rollback_readiness_ref="rollback-ready",
        )
        assert a.execution_available is False

    def test_phase97_preflight_cannot_override_hard_no_go(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["no_go_p97"],
            phase97_preflight_ref="p97",
            phase97_preflight_digest="abc",
        )
        assert a.execution_available is False

    def test_phase98_preflight_cannot_override_hard_no_go(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["no_go_p98"],
            phase98_preflight_ref="p98",
            phase98_preflight_digest="def",
        )
        assert a.execution_available is False

    def test_unknown_unsafe_hard_no_go_is_fail_closed(self):
        """Adding unknown hard no-go conditions does not open any exec path."""
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["completely_unknown_condition_xyz"],
        )
        assert a.execution_available is False
        assert a.no_execution is True
        assert a.non_authorizing is True


# ═══════════════════════════════════════════════════════════════════════════
# 5. Prerequisite semantics freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestPrerequisiteFreeze:
    """Assert missing/invalid prerequisites → deny/block, remain evidence."""

    def test_missing_phase97_preflight_is_a_denial_reason(self):
        assert GEA_DENIED_MISSING_PHASE97 in VALID_GEA_DENIAL_REASONS
        a = GovernedExecutionAttemptBoundary(
            denial_reasons=[GEA_DENIED_MISSING_PHASE97],
        )
        assert a.execution_available is False

    def test_invalid_phase97_preflight_is_a_denial_reason(self):
        assert GEA_DENIED_INVALID_PHASE97 in VALID_GEA_DENIAL_REASONS

    def test_missing_phase98_preflight_is_a_denial_reason(self):
        assert GEA_DENIED_MISSING_PHASE98 in VALID_GEA_DENIAL_REASONS

    def test_invalid_phase98_preflight_is_a_denial_reason(self):
        assert GEA_DENIED_INVALID_PHASE98 in VALID_GEA_DENIAL_REASONS

    def test_missing_approval_is_a_denial_reason(self):
        assert GEA_DENIED_MISSING_APPROVAL in VALID_GEA_DENIAL_REASONS

    def test_missing_audit_is_a_denial_reason(self):
        assert GEA_DENIED_MISSING_AUDIT in VALID_GEA_DENIAL_REASONS

    def test_missing_rollback_is_a_denial_reason(self):
        assert GEA_DENIED_MISSING_ROLLBACK in VALID_GEA_DENIAL_REASONS

    def test_failed_verification_is_a_denial_reason(self):
        assert GEA_DENIED_FAILED_VERIFICATION in VALID_GEA_DENIAL_REASONS

    def test_missing_prerequisites_remain_evidence_not_authorization(self):
        a = GovernedExecutionAttemptBoundary(
            missing_prerequisites=["phase97_preflight", "human_approval"],
        )
        assert a.execution_available is False
        assert a.non_authorizing is True
        assert a.evidence_only is True

    def test_prerequisite_refs_cannot_imply_execution_availability(self):
        """Filling prerequisite refs does not toggle execution_available."""
        a = GovernedExecutionAttemptBoundary(
            phase97_preflight_ref="ref-ok",
            phase97_preflight_digest="digest-ok",
            phase98_preflight_ref="ref-ok",
            phase98_preflight_digest="digest-ok",
            approval_ref="approved",
            audit_readiness_ref="audit-ok",
            rollback_readiness_ref="rollback-ok",
            artifact_verification_ref="verify-ok",
            execution_boundary_proof_ref="proof-ok",
        )
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_missing_prerequisites_visible_in_artifact(self):
        a = GovernedExecutionAttemptBoundary(
            missing_prerequisites=["prereq_a", "prereq_b"],
        )
        d = a.to_dict()
        assert "prereq_a" in d["missing_prerequisites"]
        assert "prereq_b" in d["missing_prerequisites"]

    def test_missing_prerequisites_change_affects_digest(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(
            missing_prerequisites=["something_missing"],
        )
        assert a1.compute_digest() != a2.compute_digest()


# ═══════════════════════════════════════════════════════════════════════════
# 6. Denial/abort/fail-closed semantics freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestDenialAbortFailClosedFreeze:
    """Assert deny/abort/fail-closed semantics are non-executing, non-authorizing."""

    def test_denial_means_no_execution_boundary_crossing(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_DENIED,
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
        )
        assert a.no_execution is True
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_abort_means_no_backend_adapter_shell_network_subprocess(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_ABORTED_BEFORE_EXECUTION,
        )
        assert a.execution_available is False
        assert a.backend_invocation_authorized is False
        assert a.adapter_execution_authorized is False
        assert a.shell_authorized is False
        assert a.network_authorized is False
        assert a.subprocess_authorized is False

    def test_failed_verification_means_fail_closed(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_BLOCKED_BY_FAILED_VERIFICATION,
            failed_checks=["verification_check_failed"],
        )
        assert a.no_execution is True
        assert a.execution_available is False
        assert a.non_authorizing is True

    def test_missing_evidence_means_fail_closed(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_BLOCKED_BY_MISSING_EVIDENCE,
            missing_prerequisites=["required_evidence"],
        )
        assert a.no_execution is True
        assert a.execution_available is False

    def test_contradictory_safety_flags_mean_fail_closed(self):
        """simulation_only and no_execution must both be True; anything else is fail-closed."""
        issues = GovernedExecutionAttemptBoundary(no_execution=False).validate()
        assert any("no_execution must be True" in i for i in issues)

    def test_unsafe_authorization_flag_means_fail_closed(self):
        issues = GovernedExecutionAttemptBoundary(execution_authorized=True).validate()
        assert any("execution_authorized" in i for i in issues)

    def test_denial_artifacts_are_evidence_only(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_DENIED,
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
        )
        assert a.evidence_only is True
        assert a.non_authorizing is True

    def test_abort_artifacts_are_evidence_only(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_ABORTED_BEFORE_EXECUTION,
        )
        assert a.evidence_only is True
        assert a.non_authorizing is True

    def test_fail_closed_path_is_non_executing_and_non_authorizing(self):
        """Every fail-closed state: no_execution=True, non_authorizing=True."""
        fail_closed_states = [
            GEA_DENIED, GEA_ABORTED_BEFORE_EXECUTION,
            GEA_BLOCKED_BY_NO_GO, GEA_BLOCKED_BY_MISSING_EVIDENCE,
            GEA_BLOCKED_BY_FAILED_VERIFICATION, GEA_UNAVAILABLE,
            GEA_PREFLIGHT_FAILED,
        ]
        for state in fail_closed_states:
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            assert a.no_execution is True, f"{state}: no_execution must be True"
            assert a.non_authorizing is True, f"{state}: non_authorizing must be True"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Authorization flag freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthorizationFlagFreeze:
    """Assert exactly 12 auth flags, all False by default."""

    def test_exactly_12_auth_flags_in_dataclass(self):
        a = GovernedExecutionAttemptBoundary()
        for flag in _12_AUTH_FLAGS:
            assert hasattr(a, flag), f"missing auth flag attribute: {flag}"

    def test_all_12_flags_false_by_default(self):
        a = GovernedExecutionAttemptBoundary()
        for flag in _12_AUTH_FLAGS:
            assert getattr(a, flag) is False, f"{flag} must be False by default"

    def test_all_12_flags_false_in_to_dict(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        for flag in _12_AUTH_FLAGS:
            assert d["authorization_summary"][flag] is False, (
                f"{flag} must be False in to_dict authorization_summary"
            )

    def test_validate_rejects_execution_available_true(self):
        a = GovernedExecutionAttemptBoundary(execution_available=True)
        issues = a.validate()
        assert any("execution_available must be False" in i for i in issues)

    def test_validate_rejects_execution_authorized_true(self):
        a = GovernedExecutionAttemptBoundary(execution_authorized=True)
        issues = a.validate()
        assert any("execution_authorized must be False" in i for i in issues)

    def test_validate_rejects_push_authorized_true(self):
        a = GovernedExecutionAttemptBoundary(push_authorized=True)
        issues = a.validate()
        assert any("push_authorized must be False" in i for i in issues)

    def test_digest_changes_if_any_auth_flag_changes(self):
        for flag in ("execution_available", "execution_authorized",
                     "push_authorized"):
            a1 = GovernedExecutionAttemptBoundary()
            a2 = GovernedExecutionAttemptBoundary(**{flag: True})
            assert a1.compute_digest() != a2.compute_digest(), (
                f"digest should change when {flag} changes"
            )

    def test_no_artifact_text_implies_authorization(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        j = _json.dumps(d).lower()
        assert "execution is authorized" not in j
        assert "execution_authorized" not in j or d["authorization_summary"]["execution_authorized"] is False

    def test_no_json_output_implies_authorization(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        for flag in _12_AUTH_FLAGS:
            assert d["authorization_summary"][flag] is False, (
                f"{flag} implied as authorized in JSON"
            )

    def test_no_state_implies_authorization(self):
        """No attempt state carries authorization semantics."""
        for state in sorted(VALID_GEA_STATES):
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            assert a.execution_authorized is False, (
                f"state {state} should not imply authorization"
            )

    def test_no_denial_reason_implies_authorization(self):
        for reason in sorted(VALID_GEA_DENIAL_REASONS):
            a = GovernedExecutionAttemptBoundary(denial_reasons=[reason])
            assert a.execution_authorized is False, (
                f"reason {reason} should not imply authorization"
            )

    def test_auth_flags_present_in_to_dict_authorization_summary(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        for flag in _12_AUTH_FLAGS:
            assert flag in d["authorization_summary"], (
                f"auth flag {flag!r} missing from to_dict authorization_summary"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 8. Digest freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestDigestFreeze:
    """Assert SHA-256, deterministic, changes with field changes."""

    def test_digest_is_sha256_hex(self):
        a = GovernedExecutionAttemptBoundary()
        dgst = a.compute_digest()
        assert len(dgst) == 64
        assert all(c in "0123456789abcdef" for c in dgst)

    def test_digest_is_deterministic(self):
        for _ in range(5):
            a = GovernedExecutionAttemptBoundary()
            assert a.compute_digest() == a.compute_digest()

    def test_digest_excludes_digest_field_itself(self):
        """Setting digest after compute_digest does not change compute_digest."""
        a = GovernedExecutionAttemptBoundary()
        d1 = a.compute_digest()
        a.digest = "0" * 64
        d2 = a.compute_digest()
        assert d1 == d2  # digest field not in payload

    def test_digest_changes_when_attempt_state_changes(self):
        a1 = GovernedExecutionAttemptBoundary(attempt_state=GEA_UNAVAILABLE)
        a2 = GovernedExecutionAttemptBoundary(attempt_state=GEA_DENIED)
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_attempt_decision_changes(self):
        a1 = GovernedExecutionAttemptBoundary(attempt_decision=GEA_DENIED)
        # attempt_decision is a str field; test with different value
        a2 = GovernedExecutionAttemptBoundary(attempt_decision="blocked")
        # Note: 'blocked' may not be a valid GEA state but digest still differs
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_hard_no_go_conditions_change(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(hard_no_go_conditions=["new_no_go"])
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_missing_prerequisites_change(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(missing_prerequisites=["p97_missing"])
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_failed_checks_change(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(failed_checks=["check_failed"])
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_denial_reasons_change(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
        )
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_abort_reasons_change(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(abort_reasons=["user_aborted"])
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_evidence_refs_change(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(evidence_refs=["evidence_001"])
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_warnings_change(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(warnings=["test_warning"])
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_phase97_preflight_ref_changes(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(phase97_preflight_ref="p97-new-ref")
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_phase97_preflight_digest_changes(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(phase97_preflight_digest="abc123")
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_phase98_preflight_ref_changes(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(phase98_preflight_ref="p98-new-ref")
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_phase98_preflight_digest_changes(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(phase98_preflight_digest="def456")
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_when_safety_flag_changes(self):
        """simulation_only/no_execution/evidence_only/non_authorizing/design_only affect digest."""
        a1 = GovernedExecutionAttemptBoundary()
        # Even though validate() rejects False, the digest still differs
        a2 = GovernedExecutionAttemptBoundary(simulation_only=False)
        assert a1.compute_digest() != a2.compute_digest()
        a3 = GovernedExecutionAttemptBoundary(no_execution=False)
        assert a1.compute_digest() != a3.compute_digest()
        a4 = GovernedExecutionAttemptBoundary(evidence_only=False)
        assert a1.compute_digest() != a4.compute_digest()
        a5 = GovernedExecutionAttemptBoundary(non_authorizing=False)
        assert a1.compute_digest() != a5.compute_digest()
        a6 = GovernedExecutionAttemptBoundary(design_only=False)
        assert a1.compute_digest() != a6.compute_digest()

    def test_digest_stable_across_equivalent_formatting(self):
        """Same state produces same digest every time."""
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_BLOCKED_BY_NO_GO,
            hard_no_go_conditions=["no_go_a", "no_go_b"],
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
        )
        d1 = a.compute_digest()
        d2 = a.compute_digest()
        assert d1 == d2

    def test_digest_not_affected_by_excluded_ref_fields(self):
        """Fields excluded from digest payload don't affect digest."""
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(
            approval_ref="some-approval-id",
            audit_readiness_ref="some-audit-id",
            rollback_readiness_ref="some-rollback-id",
            backend_contract_ref="some-backend-id",
            adapter_boundary_ref="some-adapter-id",
            artifact_verification_ref="some-verify-id",
            no_go_review_ref="some-nogo-id",
            execution_boundary_proof_ref="some-proof-id",
        )
        assert a1.compute_digest() == a2.compute_digest(), (
            "digest should be unaffected by excluded ref fields"
        )

    def test_tampered_artifact_fails_verification(self):
        """If digest is stored, modifying fields breaks digest match."""
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_UNAVAILABLE,
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
        )
        a.digest = a.compute_digest()
        stored = a.digest

        # Tamper: change state
        a.attempt_state = GEA_DENIED
        assert a.compute_digest() != stored


# ═══════════════════════════════════════════════════════════════════════════
# 9. Compatibility behavior
# ═══════════════════════════════════════════════════════════════════════════

class TestCompatibilityFreeze:
    """Assert current schema accepted, unknown/missing rejected cleanly."""

    def test_current_schema_version_accepted(self):
        a = GovernedExecutionAttemptBoundary(schema_version="1.0")
        issues = a.validate()
        assert not any("unknown schema_version" in i for i in issues)

    def test_missing_schema_version_empty_string_fails(self):
        """Empty string is not '1.0', so validate reports unknown schema."""
        a = GovernedExecutionAttemptBoundary(schema_version="")
        issues = a.validate()
        assert any("unknown schema_version" in i for i in issues)

    def test_unknown_future_major_schema_fails(self):
        a = GovernedExecutionAttemptBoundary(schema_version="99.0")
        issues = a.validate()
        assert any("unknown schema_version" in i for i in issues)

    def test_unknown_attempt_state_fails_clearly(self):
        a = GovernedExecutionAttemptBoundary(attempt_state="launching")
        issues = a.validate()
        assert any("invalid attempt_state" in i for i in issues)

    def test_unknown_denial_reason_fails_clearly(self):
        a = GovernedExecutionAttemptBoundary(denial_reasons=["bogus_reason"])
        issues = a.validate()
        assert any("unknown denial_reason" in i for i in issues)

    def test_contradictory_safety_fields_fail_clearly(self):
        issues = GovernedExecutionAttemptBoundary(no_execution=False).validate()
        assert any("no_execution must be True" in i for i in issues)

        issues2 = GovernedExecutionAttemptBoundary(simulation_only=False).validate()
        assert any("simulation_only must be True" in i for i in issues2)

        issues3 = GovernedExecutionAttemptBoundary(design_only=False).validate()
        assert any("design_only must be True" in i for i in issues3)

    def test_unsafe_auth_flag_fails_validation(self):
        for flag_val in [("execution_available", True),
                         ("execution_authorized", True),
                         ("push_authorized", True)]:
            flag_name, flag_value = flag_val
            a = GovernedExecutionAttemptBoundary(**{flag_name: flag_value})
            issues = a.validate()
            assert any(f"{flag_name} must be False" in i for i in issues), (
                f"{flag_name}=True should fail validation"
            )

    def test_no_future_execution_state_accepted_as_current(self):
        for state in sorted(UNAVAILABLE_GEA_STATES):
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            issues = a.validate()
            assert any("future-only" in i for i in issues), (
                f"future state {state!r} should not be accepted as current"
            )

    def test_extra_unknown_fields_not_in_schema(self):
        """Unknown dict keys from to_dict are limited to the 33 known keys."""
        d = GovernedExecutionAttemptBoundary().to_dict()
        assert set(d.keys()) == _TO_DICT_REQUIRED_KEYS


# ═══════════════════════════════════════════════════════════════════════════
# 10. No-execution guards
# ═══════════════════════════════════════════════════════════════════════════

class TestNoExecutionGuard:
    """Assert no execution paths exist in artifact creation/validation/digest."""

    def test_to_dict_contains_no_execution_commands(self):
        j = _json.dumps(GovernedExecutionAttemptBoundary().to_dict()).lower()
        forbidden = [
            "subprocess.run", "subprocess.popen", "os.system",
            "pty.spawn", "shell_exec", "execute_backend",
        ]
        for term in forbidden:
            assert term not in j, f"to_dict JSON contains forbidden term: {term}"

    def test_validate_contains_no_execution_commands(self):
        """validate() is pure logic; verify its output contains no exec commands."""
        a = GovernedExecutionAttemptBoundary(
            attempt_state="launching",
            denial_reasons=["bogus"],
        )
        issues = a.validate()
        issues_str = _json.dumps(issues).lower()
        forbidden = ["subprocess.run", "os.system", "shell"]
        for term in forbidden:
            assert term not in issues_str, (
                f"validate output contains forbidden term: {term}"
            )

    def test_compute_digest_contains_no_execution_commands(self):
        """Digest computation is pure hashing; verify it uses no exec."""
        # compute_digest uses json.dumps and hashlib — verify no exec in source
        import inspect
        src = inspect.getsource(GovernedExecutionAttemptBoundary.compute_digest)
        forbidden = ["subprocess", "os.system", "Popen", "spawn"]
        for term in forbidden:
            assert term not in src, (
                f"compute_digest source contains forbidden term: {term}"
            )

    def test_attempt_boundary_creation_no_execution(self):
        """Creating an attempt boundary does not trigger any execution."""
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_BLOCKED_BY_NO_GO,
            hard_no_go_conditions=["test"],
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
        )
        assert a.no_execution is True
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_hard_no_go_validation_no_execution(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["unsafe_condition"],
        )
        issues = a.validate()
        assert a.no_execution is True
        assert a.execution_available is False

    def test_prerequisite_validation_no_execution(self):
        a = GovernedExecutionAttemptBoundary(
            missing_prerequisites=["phase97", "phase98"],
            denial_reasons=[
                GEA_DENIED_MISSING_PHASE97,
                GEA_DENIED_MISSING_PHASE98,
            ],
        )
        assert a.no_execution is True

    def test_denial_abort_fail_closed_no_execution(self):
        for state in [GEA_DENIED, GEA_ABORTED_BEFORE_EXECUTION,
                      GEA_BLOCKED_BY_FAILED_VERIFICATION]:
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            assert a.no_execution is True, f"{state} must be non-executing"

    def test_json_serialization_no_execution_call(self):
        """to_dict + json.dumps does not invoke any execution primitive."""
        a = GovernedExecutionAttemptBoundary()
        d = a.to_dict()
        j = _json.dumps(d, indent=2)
        # Verify no execution-related paths in serialized output
        forbidden_in_output = [
            "subprocess.run", "os.system", "Popen(",
            "exec(", "shell=True", "spawn",
        ]
        for term in forbidden_in_output:
            assert term not in j, (
                f"JSON serialization contains forbidden term: {term}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 11. Contract preservation — 99A design invariants
# ═══════════════════════════════════════════════════════════════════════════

class Test99AContractPreserved:
    """Assert 99A design invariants remain intact after 99B contract freeze."""

    def test_design_only_remains_true(self):
        assert GovernedExecutionAttemptBoundary().design_only is True

    def test_simulation_only_remains_true(self):
        assert GovernedExecutionAttemptBoundary().simulation_only is True

    def test_no_execution_remains_true(self):
        assert GovernedExecutionAttemptBoundary().no_execution is True

    def test_evidence_only_remains_true(self):
        assert GovernedExecutionAttemptBoundary().evidence_only is True

    def test_non_authorizing_remains_true(self):
        assert GovernedExecutionAttemptBoundary().non_authorizing is True

    def test_default_state_unavailable(self):
        assert GovernedExecutionAttemptBoundary().attempt_state == GEA_UNAVAILABLE

    def test_default_decision_denied(self):
        assert GovernedExecutionAttemptBoundary().attempt_decision == GEA_DENIED

    def test_14_valid_states_unchanged(self):
        assert len(VALID_GEA_STATES) == 14

    def test_26_denial_reasons_unchanged(self):
        assert len(VALID_GEA_DENIAL_REASONS) == 26

    def test_9_future_states_unchanged(self):
        assert len(UNAVAILABLE_GEA_STATES) == 9

    def test_validate_rejects_execution_paths(self):
        a = GovernedExecutionAttemptBoundary(execution_available=True)
        assert len(a.validate()) > 0

    def test_digest_is_sha256(self):
        dgst = GovernedExecutionAttemptBoundary().compute_digest()
        assert len(dgst) == 64
