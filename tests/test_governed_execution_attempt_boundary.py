"""Tests for governed execution attempt boundary design — Phase 99A.

Design-only phase. All models must remain non-executing and non-authorizing.
Tests prove the attempt boundary is design-only, non-authorizing, fail-closed.
"""

from __future__ import annotations

import hashlib
import json as _json
import pytest

from pcae.core.backend_invocations import (
    GovernedExecutionAttemptBoundary,
    GEA_UNAVAILABLE, GEA_DENIED, GEA_BLOCKED_BY_NO_GO,
    GEA_EXECUTING_FUTURE, GEA_EXECUTED_FUTURE, GEA_RUNNING_FUTURE,
    GEA_INVOKED_FUTURE, GEA_APPLIED_FUTURE, GEA_COMMITTED_FUTURE,
    GEA_PUSHED_FUTURE, GEA_SUCCESS_FUTURE, GEA_EXECUTION_COMPLETE_FUTURE,
    VALID_GEA_STATES, UNAVAILABLE_GEA_STATES, VALID_GEA_DENIAL_REASONS,
    GEA_DENIED_MISSING_PHASE97, GEA_DENIED_NO_GO_PRESENT,
    GEA_DENIED_UNSAFE_AUTH_FLAG,
)


class TestAttemptBoundaryDesign:
    def test_is_design_only(self):
        a = GovernedExecutionAttemptBoundary()
        assert a.design_only is True
        assert a.simulation_only is True
        assert a.no_execution is True
        assert a.evidence_only is True
        assert a.non_authorizing is True

    def test_all_auth_flags_false(self):
        a = GovernedExecutionAttemptBoundary()
        assert a.execution_available is False
        assert a.execution_authorized is False
        assert a.push_authorized is False

    def test_default_state_is_unavailable(self):
        a = GovernedExecutionAttemptBoundary()
        assert a.attempt_state == GEA_UNAVAILABLE
        assert a.attempt_decision == GEA_DENIED


class TestAttemptStates:
    def test_no_executing_states(self):
        futures = {GEA_EXECUTING_FUTURE, GEA_EXECUTED_FUTURE, GEA_RUNNING_FUTURE,
                   GEA_INVOKED_FUTURE, GEA_APPLIED_FUTURE, GEA_COMMITTED_FUTURE,
                   GEA_PUSHED_FUTURE, GEA_SUCCESS_FUTURE, GEA_EXECUTION_COMPLETE_FUTURE}
        assert futures.issubset(UNAVAILABLE_GEA_STATES)
        assert VALID_GEA_STATES.isdisjoint(futures)

    def test_14_valid_states(self):
        assert len(VALID_GEA_STATES) == 14

    def test_future_state_fails_validation(self):
        for s in (GEA_EXECUTING_FUTURE, GEA_RUNNING_FUTURE, GEA_INVOKED_FUTURE,
                  GEA_APPLIED_FUTURE, GEA_SUCCESS_FUTURE):
            a = GovernedExecutionAttemptBoundary(attempt_state=s)
            issues = a.validate()
            assert any("future-only" in i for i in issues)

    def test_unknown_state_fails_validation(self):
        a = GovernedExecutionAttemptBoundary(attempt_state="launching")
        issues = a.validate()
        assert any("invalid attempt_state" in i for i in issues)


class TestDenialReasons:
    def test_26_denial_reasons(self):
        assert len(VALID_GEA_DENIAL_REASONS) == 26

    def test_denial_reasons_non_authorizing(self):
        a = GovernedExecutionAttemptBoundary(
            denial_reasons=[GEA_DENIED_MISSING_PHASE97, GEA_DENIED_NO_GO_PRESENT],
        )
        assert a.execution_available is False

    def test_unknown_denial_fails_validation(self):
        a = GovernedExecutionAttemptBoundary(denial_reasons=["not_a_real_reason_xyz"])
        issues = a.validate()
        assert any("unknown denial_reason" in i for i in issues)


class TestDigest:
    def test_digest_is_sha256(self):
        a = GovernedExecutionAttemptBoundary()
        a.digest = a.compute_digest()
        assert len(a.digest) == 64

    def test_digest_changes_with_state(self):
        a1 = GovernedExecutionAttemptBoundary(attempt_state=GEA_UNAVAILABLE)
        a2 = GovernedExecutionAttemptBoundary(attempt_state=GEA_DENIED)
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_with_denial(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(denial_reasons=[GEA_DENIED_NO_GO_PRESENT])
        assert a1.compute_digest() != a2.compute_digest()

    def test_digest_changes_with_auth_flag(self):
        a1 = GovernedExecutionAttemptBoundary()
        a2 = GovernedExecutionAttemptBoundary(push_authorized=True)
        assert a1.compute_digest() != a2.compute_digest()


class TestSafetyInvariants:
    def test_validate_rejects_execution_available(self):
        a = GovernedExecutionAttemptBoundary(execution_available=True)
        assert any("execution_available" in i for i in a.validate())

    def test_validate_rejects_no_execution_false(self):
        a = GovernedExecutionAttemptBoundary(no_execution=False)
        assert any("no_execution must be True" in i for i in a.validate())

    def test_validate_rejects_design_only_false(self):
        a = GovernedExecutionAttemptBoundary(design_only=False)
        assert any("design_only must be True" in i for i in a.validate())

    def test_validate_rejects_unsafe_auth_flag(self):
        a = GovernedExecutionAttemptBoundary(execution_authorized=True)
        assert any("execution_authorized" in i for i in a.validate())

    def test_to_dict_has_all_required_keys(self):
        a = GovernedExecutionAttemptBoundary()
        d = a.to_dict()
        expected = (
            "schema_version", "attempt_boundary_id", "phase_id", "task_id",
            "generated_at_utc", "attempt_state", "attempt_decision",
            "phase97_preflight_ref", "phase97_preflight_digest",
            "phase98_preflight_ref", "phase98_preflight_digest",
            "denial_reasons", "hard_no_go_conditions",
            "missing_prerequisites", "failed_checks", "warnings",
            "authorization_summary", "simulation_only", "no_execution",
            "evidence_only", "non_authorizing", "design_only", "digest",
        )
        for key in expected:
            assert key in d


class TestNoExecutionGuard:
    def test_to_dict_no_execution_paths(self):
        a = GovernedExecutionAttemptBoundary()
        s = _json.dumps(a.to_dict()).lower()
        assert "subprocess.run" not in s
        assert "os.system" not in s
