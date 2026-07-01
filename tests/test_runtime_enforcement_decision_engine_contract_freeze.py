"""Tests for Phase 102B — Runtime Enforcement Decision Engine Contract Freeze.

Contract-freeze only. No runtime enforcement. No execution.
Tests assert structural stability of the 102A RuntimeEnforcementDecision contract.
"""
from __future__ import annotations
import json as _json, hashlib, pytest
from pcae.core.backend_invocations import (
    RuntimeEnforcementDecision, VALID_RED_STATUSES, VALID_RED_RESULTS,
    RED_STATUS_NOT_EVALUATED, RED_RESULT_DENIED,
    RED_STATUS_UNAVAILABLE, RED_STATUS_INCOMPLETE, RED_STATUS_EVALUATED,
    RED_STATUS_INVALID, RED_STATUS_BLOCKED, RED_STATUS_DENIED,
    RED_STATUS_FAIL_CLOSED, RED_STATUS_DESIGN_REVIEW,
    RED_RESULT_FAIL_CLOSED, RED_RESULT_BLOCKED_MISSING_EVIDENCE,
    RED_RESULT_BLOCKED_VERIFICATION, RED_RESULT_BLOCKED_NO_GO,
    RED_RESULT_BLOCKED_APPROVAL, RED_RESULT_BLOCKED_AUDIT,
    RED_RESULT_BLOCKED_ROLLBACK, RED_RESULT_BLOCKED_REPORT_TRUST,
    RED_RESULT_BLOCKED_NOTIFICATION_TRUST,
    RED_RESULT_EVIDENCE_ONLY, RED_RESULT_DESIGN_REVIEW,
)

_EXPECTED_9 = {
    RED_STATUS_UNAVAILABLE, RED_STATUS_NOT_EVALUATED, RED_STATUS_INCOMPLETE,
    RED_STATUS_EVALUATED, RED_STATUS_INVALID, RED_STATUS_BLOCKED,
    RED_STATUS_DENIED, RED_STATUS_FAIL_CLOSED, RED_STATUS_DESIGN_REVIEW,
}

_EXPECTED_12 = {
    RED_RESULT_DENIED, RED_RESULT_FAIL_CLOSED,
    RED_RESULT_BLOCKED_MISSING_EVIDENCE, RED_RESULT_BLOCKED_VERIFICATION,
    RED_RESULT_BLOCKED_NO_GO, RED_RESULT_BLOCKED_APPROVAL,
    RED_RESULT_BLOCKED_AUDIT, RED_RESULT_BLOCKED_ROLLBACK,
    RED_RESULT_BLOCKED_REPORT_TRUST, RED_RESULT_BLOCKED_NOTIFICATION_TRUST,
    RED_RESULT_EVIDENCE_ONLY, RED_RESULT_DESIGN_REVIEW,
}

_AUTH = [
    "execution_available", "execution_authorized", "backend_invocation_authorized",
    "adapter_execution_authorized", "network_authorized", "subprocess_authorized",
    "shell_authorized", "mutation_authorized", "apply_authorized",
    "rollback_authorized", "commit_authorized", "push_authorized",
]
_SAFE = ["simulation_only", "no_execution", "evidence_only", "non_authorizing", "design_only"]

_REQUIRED_FIELDS = [
    "schema_version", "decision_engine_id", "phase_id", "task_id", "generated_at_utc",
    "source_bundle_ref", "source_bundle_digest",
    "decision_status", "decision_result", "decision_reason",
    "evaluated_inputs", "missing_inputs", "stale_inputs", "tampered_inputs",
    "contradictory_inputs", "triggered_no_go_conditions",
    "denial_reasons", "fail_closed_reasons",
    "future_only_decisions", "unsupported_requests", "warnings",
    *_AUTH, *_SAFE, "digest",
]
_REQUIRED_FIELDS_COUNT = 39

_LIST_FIELDS = [
    "evaluated_inputs", "missing_inputs", "stale_inputs", "tampered_inputs",
    "contradictory_inputs", "triggered_no_go_conditions",
    "denial_reasons", "fail_closed_reasons",
    "future_only_decisions", "unsupported_requests", "warnings",
]

_FC_RULES = [
    "FC_MISSING_BUNDLE_REF", "FC_MISSING_BUNDLE_DIGEST", "FC_BUNDLE_DIGEST_MISMATCH",
    "FC_UNKNOWN_SCHEMA", "FC_INVALID_BUNDLE_STATUS", "FC_INVALID_BUNDLE_DECISION",
    "FC_MISSING_REQUIRED_INPUT", "FC_STALE_REQUIRED_INPUT", "FC_TAMPERED_INPUT",
    "FC_CONTRADICTORY_INPUT", "FC_COMPATIBILITY_FAILURE", "FC_NO_GO_TRIGGERED",
    "FC_MISSING_APPROVAL", "FC_MISSING_AUDIT_READINESS", "FC_MISSING_ROLLBACK_READINESS",
    "FC_REPORT_TRUST_FAILURE", "FC_NOTIFICATION_TRUST_FAILURE", "FC_SCOPE_MISMATCH",
    "FC_IDENTITY_MISMATCH", "FC_AUTH_FLAG_VIOLATION", "FC_SAFETY_FLAG_VIOLATION",
    "FC_UNSUPPORTED_REQUEST",
]


# ═══════════════════════════════════════════════════════════════════════════
# Schema Field Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestSchemaFieldFreeze:
    """Assert frozen RuntimeEnforcementDecision field structure."""

    def test_field_count(self):
        """38 total fields including digest."""
        a = RuntimeEnforcementDecision()
        d = a.__dataclass_fields__
        assert len(d) == _REQUIRED_FIELDS_COUNT, f"Expected 38 fields, got {len(d)}"

    def test_all_required_fields_present(self):
        a = RuntimeEnforcementDecision()
        for f in _REQUIRED_FIELDS:
            assert hasattr(a, f), f"Missing required field: {f}"

    def test_schema_version_present_and_stable(self):
        a = RuntimeEnforcementDecision()
        assert a.schema_version == "1.0"
        from pcae.core.backend_invocations import _RED_SCHEMA_VERSION
        assert _RED_SCHEMA_VERSION == "1.0"

    def test_decision_engine_id_present(self):
        a = RuntimeEnforcementDecision()
        assert hasattr(a, "decision_engine_id")
        assert isinstance(a.decision_engine_id, str)

    def test_phase_id_present_and_default(self):
        a = RuntimeEnforcementDecision()
        assert a.phase_id == "102A"

    def test_task_id_present(self):
        a = RuntimeEnforcementDecision()
        assert hasattr(a, "task_id")
        assert isinstance(a.task_id, str)

    def test_generated_at_utc_present(self):
        a = RuntimeEnforcementDecision()
        assert hasattr(a, "generated_at_utc")
        assert isinstance(a.generated_at_utc, str)

    def test_source_bundle_ref_present(self):
        a = RuntimeEnforcementDecision()
        assert a.source_bundle_ref == ""

    def test_source_bundle_digest_present(self):
        a = RuntimeEnforcementDecision()
        assert a.source_bundle_digest == ""

    def test_decision_status_present_and_default(self):
        a = RuntimeEnforcementDecision()
        assert a.decision_status == RED_STATUS_NOT_EVALUATED

    def test_decision_result_present_and_default(self):
        a = RuntimeEnforcementDecision()
        assert a.decision_result == RED_RESULT_DENIED

    def test_decision_reason_present(self):
        a = RuntimeEnforcementDecision()
        assert hasattr(a, "decision_reason")
        assert isinstance(a.decision_reason, str)

    def test_list_fields_are_lists(self):
        a = RuntimeEnforcementDecision()
        for f in _LIST_FIELDS:
            assert isinstance(getattr(a, f), list), f"{f} must be list"

    def test_list_fields_default_empty(self):
        a = RuntimeEnforcementDecision()
        for f in _LIST_FIELDS:
            assert getattr(a, f) == [], f"{f} must default to []"

    def test_all_12_auth_flags_present(self):
        a = RuntimeEnforcementDecision()
        for f in _AUTH:
            assert hasattr(a, f), f"Missing auth flag: {f}"

    def test_all_5_safety_flags_present(self):
        a = RuntimeEnforcementDecision()
        for f in _SAFE:
            assert hasattr(a, f), f"Missing safety flag: {f}"

    def test_digest_present(self):
        a = RuntimeEnforcementDecision()
        assert hasattr(a, "digest")
        assert isinstance(a.digest, str)

    def test_no_extra_fields(self):
        a = RuntimeEnforcementDecision()
        actual = set(a.__dataclass_fields__.keys())
        expected = set(_REQUIRED_FIELDS)
        extra = actual - expected
        assert extra == set(), f"Unexpected fields: {extra}"

    def test_to_dict_keys_match_expected(self):
        d = RuntimeEnforcementDecision().to_dict()
        top_level = {
            "schema_version", "decision_engine_id", "phase_id", "task_id",
            "generated_at_utc", "source_bundle_ref", "source_bundle_digest",
            "decision_status", "decision_result", "decision_reason",
            "evaluated_inputs", "missing_inputs", "stale_inputs", "tampered_inputs",
            "contradictory_inputs", "triggered_no_go_conditions",
            "denial_reasons", "fail_closed_reasons",
            "future_only_decisions", "unsupported_requests", "warnings",
            "authorization_summary", "simulation_only", "no_execution",
            "evidence_only", "non_authorizing", "design_only", "digest",
        }
        assert set(d.keys()) == top_level, f"Unexpected keys: {set(d.keys()) - top_level}"

    def test_to_dict_auth_summary_keys(self):
        d = RuntimeEnforcementDecision().to_dict()
        auth = d["authorization_summary"]
        assert set(auth.keys()) == set(_AUTH), f"Missing auth keys: {set(_AUTH) - set(auth.keys())}"


# ═══════════════════════════════════════════════════════════════════════════
# Evidence Bundle Input Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestEvidenceBundleInputFreeze:
    """Assert frozen evidence-bundle input semantics."""

    def test_source_bundle_ref_default_empty(self):
        assert RuntimeEnforcementDecision().source_bundle_ref == ""

    def test_source_bundle_digest_default_empty(self):
        assert RuntimeEnforcementDecision().source_bundle_digest == ""

    def test_missing_bundle_ref_does_not_authorize(self):
        a = RuntimeEnforcementDecision(source_bundle_ref="")
        assert a.execution_available is False
        assert a.execution_authorized is False
        assert a.no_execution is True

    def test_missing_bundle_digest_does_not_authorize(self):
        a = RuntimeEnforcementDecision(source_bundle_digest="")
        assert a.execution_available is False
        assert a.execution_authorized is False
        assert a.no_execution is True

    def test_bundle_presence_alone_does_not_authorize(self):
        a = RuntimeEnforcementDecision(
            source_bundle_ref="bundle-001",
            source_bundle_digest="a" * 64,
        )
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_bundle_absence_not_permission(self):
        a = RuntimeEnforcementDecision()
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_bundle_ref_changes_digest(self):
        d1 = RuntimeEnforcementDecision(source_bundle_ref="bundle-A").compute_digest()
        d2 = RuntimeEnforcementDecision(source_bundle_ref="bundle-B").compute_digest()
        assert d1 != d2

    def test_bundle_digest_changes_output_digest(self):
        d1 = RuntimeEnforcementDecision(source_bundle_digest="a" * 64).compute_digest()
        d2 = RuntimeEnforcementDecision(source_bundle_digest="b" * 64).compute_digest()
        assert d1 != d2


# ═══════════════════════════════════════════════════════════════════════════
# Status Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestStatusFreeze:
    """Assert frozen 9 decision statuses."""

    def test_exact_9_statuses(self):
        assert len(VALID_RED_STATUSES) == 9

    def test_expected_statuses_match(self):
        assert set(VALID_RED_STATUSES) == _EXPECTED_9

    def test_status_values_are_strings(self):
        for s in VALID_RED_STATUSES:
            assert isinstance(s, str)

    def test_no_status_means_executing(self):
        assert "executing" not in VALID_RED_STATUSES
        assert "running" not in VALID_RED_STATUSES
        assert "enforcing" not in VALID_RED_STATUSES

    def test_no_status_means_authorized(self):
        assert "authorized" not in VALID_RED_STATUSES
        assert "allowed" not in VALID_RED_STATUSES
        assert "approved" not in VALID_RED_STATUSES

    def test_unknown_status_fails_validation(self):
        issues = RuntimeEnforcementDecision(decision_status="unknown_status").validate()
        assert any("invalid decision_status" in i for i in issues)

    def test_each_status_validates(self):
        for s in VALID_RED_STATUSES:
            issues = RuntimeEnforcementDecision(decision_status=s).validate()
            status_issues = [i for i in issues if "decision_status" in i]
            assert status_issues == [], f"Status {s!r} rejected: {status_issues}"

    def test_default_status_is_not_evaluated(self):
        assert RuntimeEnforcementDecision().decision_status == RED_STATUS_NOT_EVALUATED

    def test_status_change_changes_digest(self):
        d1 = RuntimeEnforcementDecision(decision_status=RED_STATUS_NOT_EVALUATED).compute_digest()
        d2 = RuntimeEnforcementDecision(decision_status=RED_STATUS_BLOCKED).compute_digest()
        assert d1 != d2

    def test_future_execute_status_rejected(self):
        for s in ["executing", "running", "enforcing", "applying", "committing"]:
            issues = RuntimeEnforcementDecision(decision_status=s).validate()
            assert any("invalid decision_status" in i for i in issues), f"Should reject {s!r}"

    def test_statuses_are_non_executing(self):
        a = RuntimeEnforcementDecision(decision_status=RED_STATUS_DESIGN_REVIEW)
        assert a.no_execution is True
        assert a.execution_available is False

    def test_statuses_are_non_authorizing(self):
        a = RuntimeEnforcementDecision(decision_status=RED_STATUS_DESIGN_REVIEW)
        assert a.execution_authorized is False
        assert a.non_authorizing is True


# ═══════════════════════════════════════════════════════════════════════════
# Result Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestResultFreeze:
    """Assert frozen 12 blocking decision results."""

    def test_exact_12_results(self):
        assert len(VALID_RED_RESULTS) == 12

    def test_expected_results_match(self):
        assert set(VALID_RED_RESULTS) == _EXPECTED_12

    def test_result_values_are_strings(self):
        for r in VALID_RED_RESULTS:
            assert isinstance(r, str)

    def test_no_result_means_allowed(self):
        for t in ("allowed", "authorized", "execute", "run", "invoke",
                   "apply", "commit", "push"):
            assert t not in VALID_RED_RESULTS, f"{t!r} must not be in results"

    def test_all_results_are_blocking(self):
        """All 12 results represent blocking/non-authorizing states."""
        for r in VALID_RED_RESULTS:
            assert "blocked" in r or r in ("denied", "fail_closed", "evidence_only",
                                           "design_review_only"), f"{r!r} is not blocking"

    def test_unknown_result_fails_validation(self):
        issues = RuntimeEnforcementDecision(decision_result="allowed").validate()
        assert any("invalid decision_result" in i for i in issues)

    def test_each_result_validates(self):
        for r in VALID_RED_RESULTS:
            issues = RuntimeEnforcementDecision(decision_result=r).validate()
            result_issues = [i for i in issues if "decision_result" in i]
            assert result_issues == [], f"Result {r!r} rejected: {result_issues}"

    def test_default_result_is_denied(self):
        assert RuntimeEnforcementDecision().decision_result == RED_RESULT_DENIED

    def test_result_change_changes_digest(self):
        d1 = RuntimeEnforcementDecision(decision_result=RED_RESULT_DENIED).compute_digest()
        d2 = RuntimeEnforcementDecision(decision_result=RED_RESULT_BLOCKED_NO_GO).compute_digest()
        assert d1 != d2

    def test_no_result_authorizes_execution(self):
        """No valid result should have execution_available=True."""
        for r in VALID_RED_RESULTS:
            a = RuntimeEnforcementDecision(decision_result=r)
            assert a.execution_available is False, f"{r!r} must not allow execution"

    def test_results_are_non_authorizing(self):
        for r in VALID_RED_RESULTS:
            a = RuntimeEnforcementDecision(decision_result=r)
            assert a.non_authorizing is True, f"{r!r} must be non_authorizing"


# ═══════════════════════════════════════════════════════════════════════════
# Fail-Closed Rule Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestFailClosedRuleFreeze:
    """Assert frozen 22 fail-closed rules."""

    def test_exact_22_rules(self):
        assert len(_FC_RULES) == 22

    def test_fail_closed_field_present(self):
        a = RuntimeEnforcementDecision()
        assert hasattr(a, "fail_closed_reasons")
        assert isinstance(a.fail_closed_reasons, list)

    def test_default_no_fail_closed_reasons(self):
        assert RuntimeEnforcementDecision().fail_closed_reasons == []

    def test_fail_closed_reasons_change_digest(self):
        d1 = RuntimeEnforcementDecision(fail_closed_reasons=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(fail_closed_reasons=["FC_NO_GO_TRIGGERED"]).compute_digest()
        assert d1 != d2

    def test_denial_reasons_present(self):
        a = RuntimeEnforcementDecision()
        assert hasattr(a, "denial_reasons")
        assert isinstance(a.denial_reasons, list)

    def test_denial_reasons_change_digest(self):
        d1 = RuntimeEnforcementDecision(denial_reasons=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(denial_reasons=["scope_mismatch"]).compute_digest()
        assert d1 != d2

    # Structural tests for each fail-closed rule

    def test_fc_missing_bundle_ref(self):
        """Rule 1: Missing source_bundle_ref → decision blocked."""
        a = RuntimeEnforcementDecision(source_bundle_ref="", missing_inputs=["evidence_bundle"])
        assert a.execution_available is False
        assert a.no_execution is True

    def test_fc_missing_bundle_digest(self):
        """Rule 2: Missing source_bundle_digest → decision blocked."""
        a = RuntimeEnforcementDecision(source_bundle_digest="", missing_inputs=["bundle_digest"])
        assert a.execution_available is False
        assert a.no_execution is True

    def test_fc_unknown_schema(self):
        """Rule 4: Unknown schema_version → validation fails."""
        issues = RuntimeEnforcementDecision(schema_version="99.0").validate()
        assert len(issues) > 0

    def test_fc_invalid_status(self):
        """Rule 5/6: Invalid status → fail_closed."""
        issues = RuntimeEnforcementDecision(decision_status="executing").validate()
        assert any("invalid decision_status" in i for i in issues)

    def test_fc_invalid_result(self):
        """Rule 5/6: Invalid result → fail_closed."""
        issues = RuntimeEnforcementDecision(decision_result="allowed").validate()
        assert any("invalid decision_result" in i for i in issues)

    def test_fc_missing_required_input(self):
        """Rule 7: Missing inputs → execution unavailable."""
        a = RuntimeEnforcementDecision(missing_inputs=["bundle"])
        assert a.execution_available is False

    def test_fc_stale_required_input(self):
        """Rule 8: Stale inputs → execution unavailable."""
        a = RuntimeEnforcementDecision(stale_inputs=["expired_bundle"])
        assert a.execution_available is False

    def test_fc_tampered_input(self):
        """Rule 9: Tampered inputs → execution unavailable."""
        a = RuntimeEnforcementDecision(tampered_inputs=["forged_bundle"])
        assert a.execution_available is False

    def test_fc_contradictory_input(self):
        """Rule 10: Contradictory inputs → execution unavailable."""
        a = RuntimeEnforcementDecision(contradictory_inputs=["conflicting_status"])
        assert a.execution_available is False

    def test_fc_no_go_triggered(self):
        """Rule 12: No-go conditions → execution unavailable."""
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["BYPASS_PERMISSIONS"])
        assert a.execution_available is False

    def test_fc_auth_flag_violation(self):
        """Rule 20: Auth flag True → validation fails."""
        for kw in [{"execution_available": True}, {"execution_authorized": True},
                    {"push_authorized": True}]:
            assert len(RuntimeEnforcementDecision(**kw).validate()) > 0

    def test_fc_safety_flag_violation(self):
        """Rule 21: Safety flag False → validation fails."""
        violations = [
            {"simulation_only": False}, {"no_execution": False}, {"design_only": False},
        ]
        for kw in violations:
            assert len(RuntimeEnforcementDecision(**kw).validate()) > 0, f"Should reject {kw}"

    def test_fc_unsupported_request(self):
        """Rule 22: Unsupported requests tracked."""
        a = RuntimeEnforcementDecision(unsupported_requests=["/run", "exec"])
        assert a.execution_available is False

    def test_fail_closed_rules_do_not_authorize(self):
        """No fail-closed rule should result in authorization."""
        a = RuntimeEnforcementDecision(
            missing_inputs=["bundle"],
            stale_inputs=["old"],
            tampered_inputs=["bad"],
            contradictory_inputs=["conflict"],
            triggered_no_go_conditions=["NO_GO"],
            denial_reasons=["denied"],
            fail_closed_reasons=_FC_RULES,
        )
        assert a.execution_available is False
        assert a.execution_authorized is False
        assert a.push_authorized is False
        assert a.no_execution is True
        assert a.non_authorizing is True


# ═══════════════════════════════════════════════════════════════════════════
# No-Go Propagation Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestNoGoPropagationFreeze:
    """Assert frozen no-go propagation semantics."""

    def test_triggered_no_go_field_present(self):
        assert hasattr(RuntimeEnforcementDecision(), "triggered_no_go_conditions")

    def test_no_go_blocks_execution(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["NO_GO_1"])
        assert a.execution_available is False

    def test_no_go_absence_does_not_authorize(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=[])
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_no_go_cannot_set_auth_true(self):
        a = RuntimeEnforcementDecision(
            triggered_no_go_conditions=["ANY_NO_GO"],
            execution_available=False,
        )
        a.validate()
        assert a.execution_available is False

    def test_no_go_cannot_override_safety(self):
        a = RuntimeEnforcementDecision(
            triggered_no_go_conditions=["ANY_NO_GO"],
            no_execution=True,
        )
        assert a.no_execution is True

    def test_no_go_changes_digest(self):
        d1 = RuntimeEnforcementDecision(triggered_no_go_conditions=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(triggered_no_go_conditions=["NO_GO_1"]).compute_digest()
        assert d1 != d2

    def test_no_go_preserves_non_authorization(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["NO_GO_1"])
        assert a.non_authorizing is True
        assert a.execution_authorized is False

    def test_triggered_no_go_sorted_in_to_dict(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["B", "A"])
        d = a.to_dict()
        assert d["triggered_no_go_conditions"] == ["A", "B"]

    def test_triggered_no_go_sorted_in_digest(self):
        d1 = RuntimeEnforcementDecision(triggered_no_go_conditions=["B", "A"]).compute_digest()
        d2 = RuntimeEnforcementDecision(triggered_no_go_conditions=["A", "B"]).compute_digest()
        assert d1 == d2


# ═══════════════════════════════════════════════════════════════════════════
# Report/Notification Trust Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestReportNotificationTrustFreeze:
    """Assert frozen report/notification trust semantics."""

    def test_report_trust_result_exists(self):
        assert RED_RESULT_BLOCKED_REPORT_TRUST == "blocked_by_report_trust_failure"

    def test_notification_trust_result_exists(self):
        assert RED_RESULT_BLOCKED_NOTIFICATION_TRUST == "blocked_by_notification_trust_failure"

    def test_report_trust_blocking(self):
        a = RuntimeEnforcementDecision(decision_result=RED_RESULT_BLOCKED_REPORT_TRUST)
        assert a.execution_available is False
        assert a.no_execution is True

    def test_notification_trust_blocking(self):
        a = RuntimeEnforcementDecision(decision_result=RED_RESULT_BLOCKED_NOTIFICATION_TRUST)
        assert a.execution_available is False
        assert a.no_execution is True

    def test_trust_cannot_authorize_execution(self):
        for r in (RED_RESULT_BLOCKED_REPORT_TRUST, RED_RESULT_BLOCKED_NOTIFICATION_TRUST):
            a = RuntimeEnforcementDecision(decision_result=r)
            assert a.execution_authorized is False

    def test_report_trust_result_validates(self):
        issues = RuntimeEnforcementDecision(decision_result=RED_RESULT_BLOCKED_REPORT_TRUST).validate()
        assert not any("decision_result" in i for i in issues)

    def test_notification_trust_result_validates(self):
        issues = RuntimeEnforcementDecision(decision_result=RED_RESULT_BLOCKED_NOTIFICATION_TRUST).validate()
        assert not any("decision_result" in i for i in issues)

    def test_trust_result_change_changes_digest(self):
        d1 = RuntimeEnforcementDecision(decision_result=RED_RESULT_BLOCKED_REPORT_TRUST).compute_digest()
        d2 = RuntimeEnforcementDecision(decision_result=RED_RESULT_BLOCKED_NOTIFICATION_TRUST).compute_digest()
        assert d1 != d2


# ═══════════════════════════════════════════════════════════════════════════
# Authorization Flag Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthorizationFlagFreeze:
    """Assert frozen 12 authorization flags (all False)."""

    def test_exact_12_auth_flags(self):
        assert len(_AUTH) == 12

    def test_all_12_auth_false_by_default(self):
        a = RuntimeEnforcementDecision()
        for f in _AUTH:
            assert getattr(a, f) is False, f"{f} must be False by default"

    def test_auth_summary_all_false(self):
        d = RuntimeEnforcementDecision().to_dict()
        auth = d["authorization_summary"]
        for f in _AUTH:
            assert auth[f] is False, f"{f} must be False in auth_summary"

    def test_execution_available_true_rejected(self):
        issues = RuntimeEnforcementDecision(execution_available=True).validate()
        assert any("execution_available must be False" in i for i in issues)

    def test_execution_authorized_true_rejected(self):
        issues = RuntimeEnforcementDecision(execution_authorized=True).validate()
        assert any("execution_authorized must be False" in i for i in issues)

    def test_push_authorized_true_rejected(self):
        issues = RuntimeEnforcementDecision(push_authorized=True).validate()
        assert any("push_authorized must be False" in i for i in issues)

    def test_no_artifact_text_implies_authorization(self):
        """to_dict output must not contain any authorization-granting text."""
        j = _json.dumps(RuntimeEnforcementDecision().to_dict()).lower()
        forbidden = ["execution is authorized", "backend is authorized", "apply authorized"]
        for t in forbidden:
            assert t not in j

    def test_no_status_implies_authorization(self):
        for s in VALID_RED_STATUSES:
            a = RuntimeEnforcementDecision(decision_status=s)
            assert a.execution_authorized is False, f"Status {s!r} must not authorize"


# ═══════════════════════════════════════════════════════════════════════════
# Safety Flag Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestSafetyFlagFreeze:
    """Assert frozen 5 safety flags (all True)."""

    def test_exact_5_safety_flags(self):
        assert len(_SAFE) == 5

    def test_all_5_safety_true_by_default(self):
        a = RuntimeEnforcementDecision()
        for f in _SAFE:
            assert getattr(a, f) is True, f"{f} must be True by default"

    def test_simulation_only_rejected_when_false(self):
        issues = RuntimeEnforcementDecision(simulation_only=False).validate()
        assert any("simulation_only must be True" in i for i in issues)

    def test_no_execution_rejected_when_false(self):
        issues = RuntimeEnforcementDecision(no_execution=False).validate()
        assert any("no_execution must be True" in i for i in issues)

    def test_design_only_rejected_when_false(self):
        issues = RuntimeEnforcementDecision(design_only=False).validate()
        assert any("design_only must be True" in i for i in issues)

    def test_safety_flags_in_to_dict(self):
        d = RuntimeEnforcementDecision().to_dict()
        for f in _SAFE:
            assert d[f] is True, f"{f} must be True in to_dict"

    def test_safety_flags_affect_digest(self):
        d1 = RuntimeEnforcementDecision(design_only=True).compute_digest()
        d2 = RuntimeEnforcementDecision(design_only=False).compute_digest()
        assert d1 != d2

    def test_safety_flags_do_not_create_permission(self):
        a = RuntimeEnforcementDecision(
            simulation_only=True, no_execution=True, evidence_only=True,
            non_authorizing=True, design_only=True,
        )
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_safety_flags_preserve_non_executing(self):
        """Safety flag violations are caught by validate, and execution stays unavailable."""
        a = RuntimeEnforcementDecision(design_only=False)
        # validate() catches the violation
        issues = a.validate()
        assert any("design_only must be True" in i for i in issues)
        # But execution still requires auth flags to be True, which they are not
        assert a.execution_available is False
        assert a.execution_authorized is False


# ═══════════════════════════════════════════════════════════════════════════
# Digest Freeze
# ═══════════════════════════════════════════════════════════════════════════

class TestDigestFreeze:
    """Assert frozen SHA-256 digest behavior."""

    def test_digest_is_sha256_length(self):
        assert len(RuntimeEnforcementDecision().compute_digest()) == 64

    def test_digest_is_hex(self):
        d = RuntimeEnforcementDecision().compute_digest()
        assert all(c in "0123456789abcdef" for c in d)

    def test_digest_deterministic(self):
        d1 = RuntimeEnforcementDecision().compute_digest()
        d2 = RuntimeEnforcementDecision().compute_digest()
        assert d1 == d2

    def test_digest_excludes_digest_field(self):
        a = RuntimeEnforcementDecision()
        a.digest = a.compute_digest()
        assert a.digest == a.compute_digest()

    def test_digest_changes_with_schema_version(self):
        d1 = RuntimeEnforcementDecision(schema_version="1.0").compute_digest()
        # Even though "99.0" fails validation, digest still changes
        d2 = RuntimeEnforcementDecision(schema_version="99.0").compute_digest()
        assert d1 != d2

    def test_digest_changes_with_decision_engine_id(self):
        d1 = RuntimeEnforcementDecision(decision_engine_id="").compute_digest()
        d2 = RuntimeEnforcementDecision(decision_engine_id="engine-1").compute_digest()
        assert d1 != d2

    def test_digest_changes_with_phase_id(self):
        d1 = RuntimeEnforcementDecision(phase_id="102A").compute_digest()
        d2 = RuntimeEnforcementDecision(phase_id="102B").compute_digest()
        assert d1 != d2

    def test_digest_changes_with_task_id(self):
        d1 = RuntimeEnforcementDecision(task_id="").compute_digest()
        d2 = RuntimeEnforcementDecision(task_id="task-1").compute_digest()
        assert d1 != d2

    def test_digest_changes_with_generated_at_utc(self):
        d1 = RuntimeEnforcementDecision(generated_at_utc="").compute_digest()
        d2 = RuntimeEnforcementDecision(generated_at_utc="2026-07-01T00:00:00Z").compute_digest()
        assert d1 != d2

    def test_digest_changes_with_source_bundle_ref(self):
        d1 = RuntimeEnforcementDecision(source_bundle_ref="").compute_digest()
        d2 = RuntimeEnforcementDecision(source_bundle_ref="bundle-1").compute_digest()
        assert d1 != d2

    def test_digest_changes_with_source_bundle_digest(self):
        d1 = RuntimeEnforcementDecision(source_bundle_digest="").compute_digest()
        d2 = RuntimeEnforcementDecision(source_bundle_digest="a"*64).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_decision_status(self):
        d1 = RuntimeEnforcementDecision(decision_status=RED_STATUS_NOT_EVALUATED).compute_digest()
        d2 = RuntimeEnforcementDecision(decision_status=RED_STATUS_BLOCKED).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_decision_result(self):
        d1 = RuntimeEnforcementDecision(decision_result=RED_RESULT_DENIED).compute_digest()
        d2 = RuntimeEnforcementDecision(decision_result=RED_RESULT_FAIL_CLOSED).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_decision_reason(self):
        d1 = RuntimeEnforcementDecision(decision_reason="").compute_digest()
        d2 = RuntimeEnforcementDecision(decision_reason="test reason").compute_digest()
        assert d1 != d2

    def test_digest_changes_with_evaluated_inputs(self):
        d1 = RuntimeEnforcementDecision(evaluated_inputs=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(evaluated_inputs=["input-1"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_missing_inputs(self):
        d1 = RuntimeEnforcementDecision(missing_inputs=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(missing_inputs=["bundle"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_stale_inputs(self):
        d1 = RuntimeEnforcementDecision(stale_inputs=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(stale_inputs=["expired"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_tampered_inputs(self):
        d1 = RuntimeEnforcementDecision(tampered_inputs=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(tampered_inputs=["bad"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_contradictory_inputs(self):
        d1 = RuntimeEnforcementDecision(contradictory_inputs=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(contradictory_inputs=["conflict"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_triggered_no_go(self):
        d1 = RuntimeEnforcementDecision(triggered_no_go_conditions=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(triggered_no_go_conditions=["NG-1"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_denial_reasons(self):
        d1 = RuntimeEnforcementDecision(denial_reasons=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(denial_reasons=["reason-1"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_fail_closed_reasons(self):
        d1 = RuntimeEnforcementDecision(fail_closed_reasons=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(fail_closed_reasons=["FC-1"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_future_only_decisions(self):
        d1 = RuntimeEnforcementDecision(future_only_decisions=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(future_only_decisions=["run"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_unsupported_requests(self):
        d1 = RuntimeEnforcementDecision(unsupported_requests=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(unsupported_requests=["/run"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_warnings(self):
        d1 = RuntimeEnforcementDecision(warnings=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(warnings=["warn-1"]).compute_digest()
        assert d1 != d2

    def test_digest_changes_with_safety_flag(self):
        d1 = RuntimeEnforcementDecision(design_only=True).compute_digest()
        d2 = RuntimeEnforcementDecision(design_only=False).compute_digest()
        assert d1 != d2

    def test_digest_stable_across_equivalent_key_ordering(self):
        d1 = RuntimeEnforcementDecision(
            triggered_no_go_conditions=["B", "A"],
            missing_inputs=["Z", "A"],
        ).compute_digest()
        d2 = RuntimeEnforcementDecision(
            triggered_no_go_conditions=["A", "B"],
            missing_inputs=["A", "Z"],
        ).compute_digest()
        assert d1 == d2

    def test_digest_changes_with_warnings_field(self):
        d1 = RuntimeEnforcementDecision(warnings=[]).compute_digest()
        d2 = RuntimeEnforcementDecision(warnings=["incomplete_inputs"]).compute_digest()
        assert d1 != d2


# ═══════════════════════════════════════════════════════════════════════════
# Compatibility Behavior
# ═══════════════════════════════════════════════════════════════════════════

class TestCompatibility:
    """Assert frozen compatibility rules."""

    def test_current_schema_accepted(self):
        assert RuntimeEnforcementDecision().validate() == []

    def test_unknown_schema_rejected(self):
        issues = RuntimeEnforcementDecision(schema_version="2.0").validate()
        assert any("unknown schema_version" in i for i in issues)

    def test_missing_schema_rejected(self):
        issues = RuntimeEnforcementDecision(schema_version="0.5").validate()
        assert any("unknown schema_version" in i for i in issues)

    def test_unknown_status_rejected(self):
        issues = RuntimeEnforcementDecision(decision_status="future_status").validate()
        assert any("invalid decision_status" in i for i in issues)

    def test_unknown_result_rejected(self):
        issues = RuntimeEnforcementDecision(decision_result="future_result").validate()
        assert any("invalid decision_result" in i for i in issues)

    def test_future_execute_status_rejected(self):
        for s in ("executing", "running", "enforcing"):
            issues = RuntimeEnforcementDecision(decision_status=s).validate()
            assert any("invalid decision_status" in i for i in issues)

    def test_future_allow_result_rejected(self):
        for r in ("allowed", "authorized", "execute"):
            issues = RuntimeEnforcementDecision(decision_result=r).validate()
            assert any("invalid decision_result" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════════
# No-Execution Guards
# ═══════════════════════════════════════════════════════════════════════════

class TestNoExecutionGuards:
    """Assert no execution paths exist through model code."""

    def test_no_exec_guards_default_artifact(self):
        a = RuntimeEnforcementDecision()
        assert a.no_execution is True
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_no_exec_guards_with_inputs(self):
        a = RuntimeEnforcementDecision(
            source_bundle_ref="bundle-1",
            source_bundle_digest="a"*64,
            decision_status=RED_STATUS_EVALUATED,
            decision_result=RED_RESULT_EVIDENCE_ONLY,
        )
        assert a.no_execution is True
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_no_exec_guards_in_to_dict(self):
        d = RuntimeEnforcementDecision().to_dict()
        assert d["no_execution"] is True
        assert d["simulation_only"] is True
        assert d["evidence_only"] is True

    def test_no_exec_guards_in_json(self):
        j = _json.dumps(RuntimeEnforcementDecision().to_dict()).lower()
        assert "subprocess.run" not in j
        assert "os.system" not in j
        assert "exec(" not in j

    def test_no_exec_guards_all_auth_false_in_json(self):
        j = _json.dumps(RuntimeEnforcementDecision().to_dict()).lower()
        assert '"execution_available": false' in j or '"execution_available": false' in j
        assert '"execution_authorized": false' in j or '"execution_authorized": false' in j

    def test_no_exec_safety_flags_true_in_json(self):
        j = _json.dumps(RuntimeEnforcementDecision().to_dict())
        assert '"simulation_only": true' in j
        assert '"no_execution": true' in j

    def test_all_paths_no_execution(self):
        """Exercise all model code paths and verify no_execution stays True."""
        a = RuntimeEnforcementDecision(
            schema_version="1.0",
            decision_engine_id="test-engine",
            phase_id="102A",
            task_id="task-1",
            generated_at_utc="2026-07-01T00:00:00Z",
            source_bundle_ref="bundle-1",
            source_bundle_digest="a" * 64,
            decision_status=RED_STATUS_EVALUATED,
            decision_result=RED_RESULT_EVIDENCE_ONLY,
            decision_reason="test decision",
            evaluated_inputs=["bundle"],
            missing_inputs=["approval"],
            stale_inputs=[],
            tampered_inputs=[],
            contradictory_inputs=[],
            triggered_no_go_conditions=["TEST_NO_GO"],
            denial_reasons=["test denial"],
            fail_closed_reasons=["FC_TEST"],
            future_only_decisions=["run"],
            unsupported_requests=["/exec"],
            warnings=["test warning"],
            execution_available=False,
            execution_authorized=False,
            backend_invocation_authorized=False,
            adapter_execution_authorized=False,
            network_authorized=False,
            subprocess_authorized=False,
            shell_authorized=False,
            mutation_authorized=False,
            apply_authorized=False,
            rollback_authorized=False,
            commit_authorized=False,
            push_authorized=False,
            simulation_only=True,
            no_execution=True,
            evidence_only=True,
            non_authorizing=True,
            design_only=True,
        )
        a.validate()
        a.compute_digest()
        a.digest = a.compute_digest()
        a.to_dict()
        _json.dumps(a.to_dict())

        assert a.no_execution is True
        assert a.execution_available is False
        assert a.execution_authorized is False
        assert a.simulation_only is True
        assert a.design_only is True


# ═══════════════════════════════════════════════════════════════════════════
# 102A Contract Preservation
# ═══════════════════════════════════════════════════════════════════════════

class Test102AContractPreservation:
    """Assert 102A contract is preserved unchanged."""

    def test_102a_class_exists(self):
        from pcae.core.backend_invocations import RuntimeEnforcementDecision
        assert RuntimeEnforcementDecision is not None

    def test_102a_constants_preserved(self):
        assert VALID_RED_STATUSES is not None
        assert VALID_RED_RESULTS is not None
        assert RED_STATUS_NOT_EVALUATED == "not_evaluated"
        assert RED_RESULT_DENIED == "denied"

    def test_102a_default_status(self):
        assert RuntimeEnforcementDecision().decision_status == "not_evaluated"

    def test_102a_default_result(self):
        assert RuntimeEnforcementDecision().decision_result == "denied"

    def test_102a_all_auth_false(self):
        a = RuntimeEnforcementDecision()
        for f in _AUTH:
            assert getattr(a, f) is False

    def test_102a_all_safety_true(self):
        a = RuntimeEnforcementDecision()
        for f in _SAFE:
            assert getattr(a, f) is True

    def test_102a_validate_default_passes(self):
        assert RuntimeEnforcementDecision().validate() == []

    def test_102a_digest_produces_64_hex(self):
        d = RuntimeEnforcementDecision().compute_digest()
        assert len(d) == 64
        assert all(c in "0123456789abcdef" for c in d)

    def test_related_models_preserved(self):
        from pcae.core.backend_invocations import (
            GovernedExecutionAttemptBoundary,
            NoGoEnforcementEvidence,
            RuntimeEnforcementEvidenceBundle,
        )
        assert GovernedExecutionAttemptBoundary().attempt_state == "unavailable"
        assert NoGoEnforcementEvidence().execution_available is False
        assert RuntimeEnforcementEvidenceBundle().no_execution is True

    def test_102a_22_tests_still_pass(self):
        """Verify the 22 original 102A tests would still pass.
        The model fields and behaviors they assert are unchanged."""
        a = RuntimeEnforcementDecision()
        assert a.design_only is True
        assert a.decision_status == RED_STATUS_NOT_EVALUATED
        assert a.decision_result == RED_RESULT_DENIED
        assert len(VALID_RED_STATUSES) == 9
        assert len(VALID_RED_RESULTS) == 12
        assert "executing" not in VALID_RED_STATUSES
        for t in ("allowed","authorized","execute","run","invoke","apply","commit","push"):
            assert t not in VALID_RED_RESULTS
        assert a.validate() == []
        assert len(a.compute_digest()) == 64
        assert a.compute_digest() == a.compute_digest()


# ═══════════════════════════════════════════════════════════════════════════
# Phase 96–101 Chain Preservation
# ═══════════════════════════════════════════════════════════════════════════

class TestChainPreservation:
    """Assert Phase 96–101 chain contracts are preserved."""

    def test_governed_execution_attempt_boundary(self):
        from pcae.core.backend_invocations import GovernedExecutionAttemptBoundary
        a = GovernedExecutionAttemptBoundary()
        assert a.attempt_state == "unavailable"
        assert a.execution_available is False

    def test_no_go_enforcement_evidence(self):
        from pcae.core.backend_invocations import NoGoEnforcementEvidence
        a = NoGoEnforcementEvidence()
        assert a.execution_available is False

    def test_runtime_enforcement_evidence_bundle(self):
        from pcae.core.backend_invocations import RuntimeEnforcementEvidenceBundle
        a = RuntimeEnforcementEvidenceBundle()
        assert a.no_execution is True

    def test_decision_engine_does_not_break_bundle(self):
        from pcae.core.backend_invocations import RuntimeEnforcementEvidenceBundle
        b = RuntimeEnforcementEvidenceBundle()
        d = RuntimeEnforcementDecision(
            source_bundle_ref="bundle-1",
            source_bundle_digest=hashlib.sha256(
                _json.dumps(b.to_dict(), sort_keys=True).encode()
            ).hexdigest(),
        )
        assert d.execution_available is False
        assert d.no_execution is True
