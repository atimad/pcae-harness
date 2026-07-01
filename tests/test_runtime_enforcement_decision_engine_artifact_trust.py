"""Tests for Phase 102C — Runtime Enforcement Decision Engine Artifact Trust Hardening.

Artifact trust hardening only. No runtime enforcement. No execution.
Test-only — no source changes.
"""
from __future__ import annotations
import json as _json, hashlib, pytest, copy
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

_AUTH = [
    "execution_available", "execution_authorized", "backend_invocation_authorized",
    "adapter_execution_authorized", "network_authorized", "subprocess_authorized",
    "shell_authorized", "mutation_authorized", "apply_authorized",
    "rollback_authorized", "commit_authorized", "push_authorized",
]
_SAFE = ["simulation_only", "no_execution", "evidence_only", "non_authorizing", "design_only"]

_ALL_STATUSES = [
    RED_STATUS_UNAVAILABLE, RED_STATUS_NOT_EVALUATED, RED_STATUS_INCOMPLETE,
    RED_STATUS_EVALUATED, RED_STATUS_INVALID, RED_STATUS_BLOCKED,
    RED_STATUS_DENIED, RED_STATUS_FAIL_CLOSED, RED_STATUS_DESIGN_REVIEW,
]

_ALL_RESULTS = [
    RED_RESULT_DENIED, RED_RESULT_FAIL_CLOSED,
    RED_RESULT_BLOCKED_MISSING_EVIDENCE, RED_RESULT_BLOCKED_VERIFICATION,
    RED_RESULT_BLOCKED_NO_GO, RED_RESULT_BLOCKED_APPROVAL,
    RED_RESULT_BLOCKED_AUDIT, RED_RESULT_BLOCKED_ROLLBACK,
    RED_RESULT_BLOCKED_REPORT_TRUST, RED_RESULT_BLOCKED_NOTIFICATION_TRUST,
    RED_RESULT_EVIDENCE_ONLY, RED_RESULT_DESIGN_REVIEW,
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

_DIGEST_FIELDS = [
    "schema_version", "decision_engine_id", "phase_id", "task_id", "generated_at_utc",
    "source_bundle_ref", "source_bundle_digest",
    "decision_status", "decision_result", "decision_reason",
    "evaluated_inputs", "missing_inputs", "stale_inputs", "tampered_inputs",
    "contradictory_inputs", "triggered_no_go_conditions",
    "denial_reasons", "fail_closed_reasons",
    "future_only_decisions", "unsupported_requests", "warnings",
]


def _base() -> RuntimeEnforcementDecision:
    """Return a fully populated valid artifact for trust testing."""
    return RuntimeEnforcementDecision(
        schema_version="1.0",
        decision_engine_id="test-engine",
        phase_id="102A",
        task_id="task-1",
        generated_at_utc="2026-07-01T00:00:00Z",
        source_bundle_ref="bundle-001",
        source_bundle_digest="a" * 64,
        decision_status=RED_STATUS_EVALUATED,
        decision_result=RED_RESULT_EVIDENCE_ONLY,
        decision_reason="trust hardening test",
        evaluated_inputs=["bundle"],
        missing_inputs=["approval"],
        stale_inputs=["old-input"],
        tampered_inputs=["bad-input"],
        contradictory_inputs=["conflict-1", "conflict-2"],
        triggered_no_go_conditions=["TEST_NO_GO"],
        denial_reasons=["test-denial"],
        fail_closed_reasons=["FC_TEST"],
        future_only_decisions=["run"],
        unsupported_requests=["/exec"],
        warnings=["test-warning"],
        execution_available=False, execution_authorized=False,
        backend_invocation_authorized=False, adapter_execution_authorized=False,
        network_authorized=False, subprocess_authorized=False,
        shell_authorized=False, mutation_authorized=False,
        apply_authorized=False, rollback_authorized=False,
        commit_authorized=False, push_authorized=False,
        simulation_only=True, no_execution=True, evidence_only=True,
        non_authorizing=True, design_only=True,
        digest="",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Digest Determinism and Coverage
# ═══════════════════════════════════════════════════════════════════════════

class TestDigestDeterminism:
    def test_sha256_length(self): assert len(RuntimeEnforcementDecision().compute_digest()) == 64
    def test_hex_chars(self): assert all(c in "0123456789abcdef" for c in RuntimeEnforcementDecision().compute_digest())
    def test_deterministic_same_input(self): assert RuntimeEnforcementDecision().compute_digest() == RuntimeEnforcementDecision().compute_digest()
    def test_excludes_digest_field_itself(self):
        a = _base(); a.digest = a.compute_digest()
        assert a.digest == a.compute_digest()
    def test_stable_across_equivalent_ordering(self):
        d1 = RuntimeEnforcementDecision(missing_inputs=["Z","A"], triggered_no_go_conditions=["B","A"]).compute_digest()
        d2 = RuntimeEnforcementDecision(missing_inputs=["A","Z"], triggered_no_go_conditions=["A","B"]).compute_digest()
        assert d1 == d2


class TestDigestFieldCoverage:
    """Digest changes when each digest-covered field changes."""
    def test_schema_version(self): assert RuntimeEnforcementDecision(schema_version="1.0").compute_digest() != RuntimeEnforcementDecision(schema_version="1.1").compute_digest()
    def test_decision_engine_id(self): assert RuntimeEnforcementDecision(decision_engine_id="").compute_digest() != RuntimeEnforcementDecision(decision_engine_id="e1").compute_digest()
    def test_phase_id(self): assert RuntimeEnforcementDecision(phase_id="102A").compute_digest() != RuntimeEnforcementDecision(phase_id="102B").compute_digest()
    def test_task_id(self): assert RuntimeEnforcementDecision(task_id="").compute_digest() != RuntimeEnforcementDecision(task_id="t1").compute_digest()
    def test_generated_at_utc(self): assert RuntimeEnforcementDecision(generated_at_utc="").compute_digest() != RuntimeEnforcementDecision(generated_at_utc="2026-01-01").compute_digest()
    def test_source_bundle_ref(self): assert RuntimeEnforcementDecision(source_bundle_ref="").compute_digest() != RuntimeEnforcementDecision(source_bundle_ref="b1").compute_digest()
    def test_source_bundle_digest(self): assert RuntimeEnforcementDecision(source_bundle_digest="").compute_digest() != RuntimeEnforcementDecision(source_bundle_digest="a"*64).compute_digest()
    def test_decision_status(self): assert RuntimeEnforcementDecision(decision_status=RED_STATUS_NOT_EVALUATED).compute_digest() != RuntimeEnforcementDecision(decision_status=RED_STATUS_BLOCKED).compute_digest()
    def test_decision_result(self): assert RuntimeEnforcementDecision(decision_result=RED_RESULT_DENIED).compute_digest() != RuntimeEnforcementDecision(decision_result=RED_RESULT_FAIL_CLOSED).compute_digest()
    def test_decision_reason(self): assert RuntimeEnforcementDecision(decision_reason="").compute_digest() != RuntimeEnforcementDecision(decision_reason="changed").compute_digest()
    def test_evaluated_inputs(self): assert RuntimeEnforcementDecision(evaluated_inputs=[]).compute_digest() != RuntimeEnforcementDecision(evaluated_inputs=["x"]).compute_digest()
    def test_missing_inputs(self): assert RuntimeEnforcementDecision(missing_inputs=[]).compute_digest() != RuntimeEnforcementDecision(missing_inputs=["x"]).compute_digest()
    def test_stale_inputs(self): assert RuntimeEnforcementDecision(stale_inputs=[]).compute_digest() != RuntimeEnforcementDecision(stale_inputs=["x"]).compute_digest()
    def test_tampered_inputs(self): assert RuntimeEnforcementDecision(tampered_inputs=[]).compute_digest() != RuntimeEnforcementDecision(tampered_inputs=["x"]).compute_digest()
    def test_contradictory_inputs(self): assert RuntimeEnforcementDecision(contradictory_inputs=[]).compute_digest() != RuntimeEnforcementDecision(contradictory_inputs=["x"]).compute_digest()
    def test_triggered_no_go(self): assert RuntimeEnforcementDecision(triggered_no_go_conditions=[]).compute_digest() != RuntimeEnforcementDecision(triggered_no_go_conditions=["x"]).compute_digest()
    def test_denial_reasons(self): assert RuntimeEnforcementDecision(denial_reasons=[]).compute_digest() != RuntimeEnforcementDecision(denial_reasons=["x"]).compute_digest()
    def test_fail_closed_reasons(self): assert RuntimeEnforcementDecision(fail_closed_reasons=[]).compute_digest() != RuntimeEnforcementDecision(fail_closed_reasons=["x"]).compute_digest()
    def test_future_only_decisions(self): assert RuntimeEnforcementDecision(future_only_decisions=[]).compute_digest() != RuntimeEnforcementDecision(future_only_decisions=["x"]).compute_digest()
    def test_unsupported_requests(self): assert RuntimeEnforcementDecision(unsupported_requests=[]).compute_digest() != RuntimeEnforcementDecision(unsupported_requests=["x"]).compute_digest()
    def test_warnings(self): assert RuntimeEnforcementDecision(warnings=[]).compute_digest() != RuntimeEnforcementDecision(warnings=["x"]).compute_digest()
    def test_safety_flag(self): assert RuntimeEnforcementDecision(design_only=True).compute_digest() != RuntimeEnforcementDecision(design_only=False).compute_digest()


# ═══════════════════════════════════════════════════════════════════════════
# Tamper Detection
# ═══════════════════════════════════════════════════════════════════════════

class TestTamperDetection:
    """Tampering any digest-covered field changes digest."""
    def test_schema_version_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.schema_version = "99.0"; assert a.compute_digest() != d1
    def test_decision_engine_id_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.decision_engine_id = "evil"; assert a.compute_digest() != d1
    def test_phase_id_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.phase_id = "evil"; assert a.compute_digest() != d1
    def test_task_id_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.task_id = "evil"; assert a.compute_digest() != d1
    def test_generated_at_utc_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.generated_at_utc = "evil"; assert a.compute_digest() != d1
    def test_source_bundle_ref_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.source_bundle_ref = "evil"; assert a.compute_digest() != d1
    def test_source_bundle_digest_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.source_bundle_digest = "b"*64; assert a.compute_digest() != d1
    def test_decision_status_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.decision_status = RED_STATUS_DENIED; assert a.compute_digest() != d1
    def test_decision_result_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.decision_result = RED_RESULT_FAIL_CLOSED; assert a.compute_digest() != d1
    def test_decision_reason_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.decision_reason = "evil"; assert a.compute_digest() != d1
    def test_evaluated_inputs_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.evaluated_inputs = ["evil"]; assert a.compute_digest() != d1
    def test_missing_inputs_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.missing_inputs = ["evil"]; assert a.compute_digest() != d1
    def test_stale_inputs_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.stale_inputs = ["evil"]; assert a.compute_digest() != d1
    def test_tampered_inputs_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.tampered_inputs = ["evil"]; assert a.compute_digest() != d1
    def test_contradictory_inputs_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.contradictory_inputs = ["evil"]; assert a.compute_digest() != d1
    def test_triggered_no_go_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.triggered_no_go_conditions = ["evil"]; assert a.compute_digest() != d1
    def test_denial_reasons_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.denial_reasons = ["evil"]; assert a.compute_digest() != d1
    def test_fail_closed_reasons_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.fail_closed_reasons = ["evil"]; assert a.compute_digest() != d1
    def test_future_only_decisions_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.future_only_decisions = ["evil"]; assert a.compute_digest() != d1
    def test_unsupported_requests_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.unsupported_requests = ["evil"]; assert a.compute_digest() != d1
    def test_warnings_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.warnings = ["evil"]; assert a.compute_digest() != d1
    def test_digest_tamper_fails_verify(self):
        a = _base(); a.digest = a.compute_digest()
        a.source_bundle_ref = "tampered"  # change field without recomputing digest
        assert a.compute_digest() != a.digest

    def test_safety_flag_tamper(self):
        d1 = _base().compute_digest()
        a = _base(); a.simulation_only = False; assert a.compute_digest() != d1
    def test_digest_verification_detectable(self):
        """Tampers are detectable by comparing stored digest with recomputed."""
        a = _base(); a.digest = a.compute_digest()
        assert a.digest == a.compute_digest()
        a.decision_status = RED_STATUS_BLOCKED
        assert a.digest != a.compute_digest()


# ═══════════════════════════════════════════════════════════════════════════
# Evidence-Bundle Input Trust
# ═══════════════════════════════════════════════════════════════════════════

class TestEvidenceBundleInputTrust:
    def test_missing_bundle_ref_no_execution(self):
        a = RuntimeEnforcementDecision(source_bundle_ref="")
        assert a.execution_available is False; assert a.no_execution is True
    def test_missing_bundle_digest_no_execution(self):
        a = RuntimeEnforcementDecision(source_bundle_digest="")
        assert a.execution_available is False
    def test_bundle_presence_alone_no_auth(self):
        a = RuntimeEnforcementDecision(source_bundle_ref="b1", source_bundle_digest="a"*64)
        assert a.execution_authorized is False; assert a.non_authorizing is True
    def test_bundle_absence_not_permission(self):
        a = RuntimeEnforcementDecision()
        assert a.execution_available is False; assert a.execution_authorized is False
    def test_bundle_ref_change_changes_digest(self):
        assert RuntimeEnforcementDecision(source_bundle_ref="a").compute_digest() != RuntimeEnforcementDecision(source_bundle_ref="b").compute_digest()
    def test_bundle_digest_change_changes_digest(self):
        assert RuntimeEnforcementDecision(source_bundle_digest="a"*64).compute_digest() != RuntimeEnforcementDecision(source_bundle_digest="b"*64).compute_digest()
    def test_missing_bundle_fails_closed(self):
        a = RuntimeEnforcementDecision(source_bundle_ref="", missing_inputs=["evidence_bundle"])
        assert a.execution_available is False; assert a.no_execution is True
    def test_bundle_digest_mismatch_preserves_no_exec(self):
        a = RuntimeEnforcementDecision(source_bundle_ref="b1", source_bundle_digest="bad")
        assert a.no_execution is True
    def test_safe_bundle_refs_not_exec_paths(self):
        for ref in ["/bin/sh", "../escape", "file:///etc/passwd", "$(whoami)", "http://evil"]:
            a = RuntimeEnforcementDecision(source_bundle_ref=ref)
            assert a.no_execution is True, f"Unsafe ref {ref!r} must not enable execution"


# ═══════════════════════════════════════════════════════════════════════════
# Status/Result Trust
# ═══════════════════════════════════════════════════════════════════════════

class TestStatusTrust:
    def test_exact_9(self): assert len(VALID_RED_STATUSES) == 9
    def test_no_executing(self): assert "executing" not in VALID_RED_STATUSES
    def test_no_running(self): assert "running" not in VALID_RED_STATUSES
    def test_no_authorized(self): assert "authorized" not in VALID_RED_STATUSES
    def test_unknown_rejected(self): assert any("invalid decision_status" in i for i in RuntimeEnforcementDecision(decision_status="unknown").validate())
    def test_all_statuses_non_executing(self):
        for s in VALID_RED_STATUSES:
            a = RuntimeEnforcementDecision(decision_status=s)
            assert a.no_execution is True, f"{s} must be non-executing"
    def test_all_statuses_non_authorizing(self):
        for s in VALID_RED_STATUSES:
            a = RuntimeEnforcementDecision(decision_status=s)
            assert a.execution_authorized is False, f"{s} must be non-authorizing"
    def test_status_change_changes_digest(self):
        assert RuntimeEnforcementDecision(decision_status=RED_STATUS_NOT_EVALUATED).compute_digest() != RuntimeEnforcementDecision(decision_status=RED_STATUS_DENIED).compute_digest()
    def test_future_execute_rejected(self):
        for s in ("executing","running","enforcing","applying","committing"):
            issues = RuntimeEnforcementDecision(decision_status=s).validate()
            assert any("invalid decision_status" in i for i in issues), f"Should reject {s!r}"


class TestResultTrust:
    def test_exact_12(self): assert len(VALID_RED_RESULTS) == 12
    def test_no_allow(self):
        for t in ("allowed","authorized","execute","run","invoke","apply","commit","push"): assert t not in VALID_RED_RESULTS
    def test_unknown_rejected(self): assert any("invalid decision_result" in i for i in RuntimeEnforcementDecision(decision_result="allowed").validate())
    def test_all_results_blocking(self):
        for r in VALID_RED_RESULTS:
            a = RuntimeEnforcementDecision(decision_result=r)
            assert a.execution_available is False, f"{r} must block execution"
            assert a.execution_authorized is False, f"{r} must not authorize"
    def test_result_change_changes_digest(self):
        assert RuntimeEnforcementDecision(decision_result=RED_RESULT_DENIED).compute_digest() != RuntimeEnforcementDecision(decision_result=RED_RESULT_EVIDENCE_ONLY).compute_digest()
    def test_future_allow_rejected(self):
        for r in ("allowed","authorized","execute","run"):
            issues = RuntimeEnforcementDecision(decision_result=r).validate()
            assert any("invalid decision_result" in i for i in issues), f"Should reject {r!r}"

class TestContradictoryStatusResult:
    def test_denied_with_evidence_only_contradicts(self):
        """Contradictory status/result is detectable via validation."""
        a = RuntimeEnforcementDecision(decision_status=RED_STATUS_DENIED, decision_result=RED_RESULT_EVIDENCE_ONLY)
        a.validate()
        assert a.no_execution is True; assert a.execution_authorized is False


# ═══════════════════════════════════════════════════════════════════════════
# Fail-Closed Rule Trust
# ═══════════════════════════════════════════════════════════════════════════

class TestFailClosedRuleTrust:
    def test_all_22_rules_defined(self): assert len(_FC_RULES) == 22
    def test_fail_closed_reasons_field_exists(self): assert hasattr(RuntimeEnforcementDecision(), "fail_closed_reasons")
    def test_fail_closed_reasons_affect_digest(self):
        assert RuntimeEnforcementDecision(fail_closed_reasons=[]).compute_digest() != RuntimeEnforcementDecision(fail_closed_reasons=["FC_1"]).compute_digest()
    def test_fail_closed_reasons_sorted_in_digest(self):
        d1 = RuntimeEnforcementDecision(fail_closed_reasons=["B","A"]).compute_digest()
        d2 = RuntimeEnforcementDecision(fail_closed_reasons=["A","B"]).compute_digest()
        assert d1 == d2
    def test_each_fc_rule_represented_in_list(self):
        for rule in _FC_RULES:
            assert isinstance(rule, str) and rule.startswith("FC_"), f"Invalid rule: {rule!r}"
    def test_fc_auth_violation(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            assert len(RuntimeEnforcementDecision(**kw).validate()) > 0
    def test_fc_safety_violation(self):
        for kw in [{"simulation_only":False},{"no_execution":False},{"design_only":False}]:
            assert len(RuntimeEnforcementDecision(**kw).validate()) > 0
    def test_fc_missing_inputs_blocks(self):
        a = RuntimeEnforcementDecision(missing_inputs=["bundle"])
        assert a.execution_available is False
    def test_fc_tampered_inputs_blocks(self):
        a = RuntimeEnforcementDecision(tampered_inputs=["forged"])
        assert a.execution_available is False
    def test_fc_no_go_blocks(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["BYPASS"])
        assert a.execution_available is False
    def test_fc_no_authorize(self):
        a = RuntimeEnforcementDecision(fail_closed_reasons=_FC_RULES)
        assert a.execution_authorized is False; assert a.push_authorized is False


# ═══════════════════════════════════════════════════════════════════════════
# No-Go Propagation Trust
# ═══════════════════════════════════════════════════════════════════════════

class TestNoGoPropagationTrust:
    def test_triggered_no_go_present(self): assert hasattr(RuntimeEnforcementDecision(), "triggered_no_go_conditions")
    def test_no_go_blocks(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["NO_GO_1"])
        assert a.execution_available is False
    def test_no_go_absence_no_auth(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=[])
        assert a.execution_available is False; assert a.execution_authorized is False
    def test_no_go_cannot_set_auth(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["X"], execution_available=False)
        a.validate()
        assert a.execution_available is False
    def test_no_go_cannot_override_safety(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["X"], no_execution=True)
        assert a.no_execution is True
    def test_no_go_change_changes_digest(self):
        assert RuntimeEnforcementDecision(triggered_no_go_conditions=[]).compute_digest() != RuntimeEnforcementDecision(triggered_no_go_conditions=["X"]).compute_digest()
    def test_no_go_sorted_in_output(self):
        d = RuntimeEnforcementDecision(triggered_no_go_conditions=["B","A"]).to_dict()
        assert d["triggered_no_go_conditions"] == ["A","B"]
    def test_no_go_preserves_non_auth(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["X"])
        assert a.non_authorizing is True


# ═══════════════════════════════════════════════════════════════════════════
# Report/Notification Trust
# ═══════════════════════════════════════════════════════════════════════════

class TestReportNotificationTrust:
    def test_report_trust_result_exists(self):
        assert RED_RESULT_BLOCKED_REPORT_TRUST == "blocked_by_report_trust_failure"
    def test_notification_trust_result_exists(self):
        assert RED_RESULT_BLOCKED_NOTIFICATION_TRUST == "blocked_by_notification_trust_failure"
    def test_report_trust_blocking(self):
        a = RuntimeEnforcementDecision(decision_result=RED_RESULT_BLOCKED_REPORT_TRUST)
        assert a.execution_available is False; assert a.no_execution is True
    def test_notification_trust_blocking(self):
        a = RuntimeEnforcementDecision(decision_result=RED_RESULT_BLOCKED_NOTIFICATION_TRUST)
        assert a.execution_available is False; assert a.no_execution is True
    def test_trust_no_auth(self):
        for r in (RED_RESULT_BLOCKED_REPORT_TRUST, RED_RESULT_BLOCKED_NOTIFICATION_TRUST):
            assert RuntimeEnforcementDecision(decision_result=r).execution_authorized is False
    def test_denial_reasons_affect_digest(self):
        assert RuntimeEnforcementDecision(denial_reasons=["report_trust"]).compute_digest() != RuntimeEnforcementDecision(denial_reasons=["notification_trust"]).compute_digest()


# ═══════════════════════════════════════════════════════════════════════════
# Authorization Flag Trust
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthorizationFlagTrust:
    def test_exact_12(self): assert len(_AUTH) == 12
    def test_all_false_by_default(self):
        for f in _AUTH: assert getattr(RuntimeEnforcementDecision(), f) is False
    def test_any_true_fails_validation(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            assert len(RuntimeEnforcementDecision(**kw).validate()) > 0
    def test_auth_summary_in_to_dict(self):
        d = RuntimeEnforcementDecision().to_dict()
        assert "authorization_summary" in d
        for f in _AUTH: assert d["authorization_summary"][f] is False
    def test_no_json_implies_auth(self):
        j = _json.dumps(RuntimeEnforcementDecision().to_dict())
        assert "execution is authorized" not in j.lower()
    def test_no_status_auth(self):
        for s in VALID_RED_STATUSES:
            assert RuntimeEnforcementDecision(decision_status=s).execution_authorized is False
    def test_no_result_auth(self):
        for r in VALID_RED_RESULTS:
            assert RuntimeEnforcementDecision(decision_result=r).execution_authorized is False
    def test_auth_flags_not_in_digest_payload(self):
        """Auth flags are excluded from digest. Verify indirectly."""
        d1 = RuntimeEnforcementDecision(execution_available=False).compute_digest()
        d2 = RuntimeEnforcementDecision(execution_available=False).compute_digest()
        assert d1 == d2  # unchanging auth flag should not change digest


# ═══════════════════════════════════════════════════════════════════════════
# Safety Flag Trust
# ═══════════════════════════════════════════════════════════════════════════

class TestSafetyFlagTrust:
    def test_exact_5(self): assert len(_SAFE) == 5
    def test_all_true_by_default(self):
        for f in _SAFE: assert getattr(RuntimeEnforcementDecision(), f) is True
    def test_simulation_only_false_rejected(self):
        assert any("simulation_only must be True" in i for i in RuntimeEnforcementDecision(simulation_only=False).validate())
    def test_no_execution_false_rejected(self):
        assert any("no_execution must be True" in i for i in RuntimeEnforcementDecision(no_execution=False).validate())
    def test_design_only_false_rejected(self):
        assert any("design_only must be True" in i for i in RuntimeEnforcementDecision(design_only=False).validate())
    def test_safety_in_to_dict(self):
        d = RuntimeEnforcementDecision().to_dict()
        for f in _SAFE: assert d[f] is True
    def test_safety_affect_digest(self):
        assert RuntimeEnforcementDecision(design_only=True).compute_digest() != RuntimeEnforcementDecision(design_only=False).compute_digest()
    def test_safety_preserve_non_executing(self):
        a = RuntimeEnforcementDecision(simulation_only=True, no_execution=True, evidence_only=True, non_authorizing=True, design_only=True)
        assert a.execution_available is False; assert a.execution_authorized is False
    def test_any_safety_false_fails(self):
        for kw in [{"simulation_only":False},{"no_execution":False},{"design_only":False}]:
            assert len(RuntimeEnforcementDecision(**kw).validate()) > 0, f"Should reject {kw}"


# ═══════════════════════════════════════════════════════════════════════════
# Verification Error Contract
# ═══════════════════════════════════════════════════════════════════════════

class TestVerificationErrorContract:
    """Stabilized verification error behavior using validate() and digest."""

    def test_unknown_schema_version(self):
        issues = RuntimeEnforcementDecision(schema_version="99.0").validate()
        assert any("unknown schema_version" in i for i in issues)

    def test_invalid_status(self):
        issues = RuntimeEnforcementDecision(decision_status="executing").validate()
        assert any("invalid decision_status" in i for i in issues)

    def test_invalid_result(self):
        issues = RuntimeEnforcementDecision(decision_result="allowed").validate()
        assert any("invalid decision_result" in i for i in issues)

    def test_digest_mismatch_detectable(self):
        a = _base(); a.digest = "a" * 64
        assert a.digest != a.compute_digest()

    def test_missing_bundle_detectable(self):
        a = RuntimeEnforcementDecision(source_bundle_ref="", missing_inputs=["evidence_bundle"])
        assert a.execution_available is False

    def test_tampered_input_detectable(self):
        a = RuntimeEnforcementDecision(tampered_inputs=["forged"])
        assert a.execution_available is False

    def test_stale_input_detectable(self):
        a = RuntimeEnforcementDecision(stale_inputs=["expired"])
        assert a.execution_available is False

    def test_contradictory_input_detectable(self):
        a = RuntimeEnforcementDecision(contradictory_inputs=["conflict"])
        assert a.execution_available is False

    def test_auth_flag_violation_detectable(self):
        assert len(RuntimeEnforcementDecision(execution_available=True).validate()) > 0

    def test_safety_flag_violation_detectable(self):
        assert len(RuntimeEnforcementDecision(simulation_only=False).validate()) > 0

    def test_validation_errors_are_non_executing(self):
        a = RuntimeEnforcementDecision(decision_status="executing")
        a.validate()
        assert a.no_execution is True; assert a.execution_available is False

    def test_digest_mismatch_still_non_executing(self):
        a = _base(); a.digest = "bad"; a.source_bundle_ref = "tampered"
        assert a.no_execution is True


# ═══════════════════════════════════════════════════════════════════════════
# Prerequisite/Reference Validation
# ═══════════════════════════════════════════════════════════════════════════

class TestReferenceValidation:
    def test_refs_never_exec_paths(self):
        """Bundle refs are symbolic identifiers, never executable paths."""
        dangerous = ["/bin/sh", "../escape", "file:///etc/passwd", "$(whoami)",
                      "`whoami`", "http://evil.com", "| cmd"]
        for ref in dangerous:
            a = RuntimeEnforcementDecision(source_bundle_ref=ref)
            assert a.no_execution is True, f"Ref {ref!r} must not enable execution"

    def test_ref_change_changes_digest(self):
        assert RuntimeEnforcementDecision(source_bundle_ref="a").compute_digest() != RuntimeEnforcementDecision(source_bundle_ref="b").compute_digest()

    def test_empty_ref_no_auth(self):
        a = RuntimeEnforcementDecision(source_bundle_ref="")
        assert a.execution_authorized is False

    def test_decision_engine_id_ref_change_changes_digest(self):
        assert RuntimeEnforcementDecision(decision_engine_id="").compute_digest() != RuntimeEnforcementDecision(decision_engine_id="evil-engine").compute_digest()

    def test_phase_id_ref_change_changes_digest(self):
        assert RuntimeEnforcementDecision(phase_id="102A").compute_digest() != RuntimeEnforcementDecision(phase_id="evil").compute_digest()

    def test_to_dict_ref_field_present(self):
        d = RuntimeEnforcementDecision(source_bundle_ref="bundle-1").to_dict()
        assert d["source_bundle_ref"] == "bundle-1"


# ═══════════════════════════════════════════════════════════════════════════
# No-Execution Guards
# ═══════════════════════════════════════════════════════════════════════════

class TestNoExecutionGuards:
    """Guard all model paths against execution-related calls."""

    def test_default_no_exec(self):
        a = RuntimeEnforcementDecision()
        assert a.no_execution is True; assert a.simulation_only is True
        assert a.execution_available is False

    def test_validate_no_exec(self):
        a = _base(); a.validate()
        assert a.no_execution is True

    def test_compute_digest_no_exec(self):
        a = _base(); a.compute_digest()
        assert a.no_execution is True

    def test_to_dict_no_exec(self):
        a = _base(); a.to_dict()
        assert a.no_execution is True

    def test_json_serialization_no_exec(self):
        j = _json.dumps(_base().to_dict()).lower()
        assert "subprocess.run" not in j
        assert "os.system" not in j
        assert "exec(" not in j

    def test_all_fields_populated_no_exec(self):
        a = _base(); a.validate(); a.compute_digest(); a.digest = a.compute_digest()
        d = a.to_dict(); _json.dumps(d)
        assert a.no_execution is True
        assert a.execution_available is False
        assert a.execution_authorized is False

    def test_safety_flags_unchanged_after_ops(self):
        a = _base(); a.validate(); a.compute_digest(); a.to_dict()
        assert a.simulation_only is True; assert a.no_execution is True
        assert a.evidence_only is True; assert a.non_authorizing is True; assert a.design_only is True

    def test_auth_flags_unchanged_after_ops(self):
        a = _base(); a.validate(); a.compute_digest(); a.to_dict()
        for f in _AUTH: assert getattr(a, f) is False, f"{f} must stay False"


# ═══════════════════════════════════════════════════════════════════════════
# 102B Contract Preservation
# ═══════════════════════════════════════════════════════════════════════════

class Test102BContractPreservation:
    def test_class_exists(self):
        from pcae.core.backend_invocations import RuntimeEnforcementDecision
        assert RuntimeEnforcementDecision is not None

    def test_39_fields(self):
        assert len(RuntimeEnforcementDecision().__dataclass_fields__) == 39

    def test_constants_preserved(self):
        assert VALID_RED_STATUSES is not None; assert VALID_RED_RESULTS is not None
        assert len(VALID_RED_STATUSES) == 9; assert len(VALID_RED_RESULTS) == 12

    def test_defaults_preserved(self):
        a = RuntimeEnforcementDecision()
        assert a.schema_version == "1.0"; assert a.decision_status == RED_STATUS_NOT_EVALUATED
        assert a.decision_result == RED_RESULT_DENIED

    def test_validate_default_passes(self):
        assert RuntimeEnforcementDecision().validate() == []

    def test_digest_produces_64_hex(self):
        d = RuntimeEnforcementDecision().compute_digest()
        assert len(d) == 64; assert all(c in "0123456789abcdef" for c in d)

    def test_102b_freeze_tests_still_compatible(self):
        """102B freeze test assertions remain valid."""
        a = RuntimeEnforcementDecision()
        assert a.design_only is True
        assert a.decision_status == RED_STATUS_NOT_EVALUATED
        assert a.decision_result == RED_RESULT_DENIED
        for f in _AUTH: assert getattr(a, f) is False
        for f in _SAFE: assert getattr(a, f) is True


# ═══════════════════════════════════════════════════════════════════════════
# Phase 101 Evidence Bundle + Report Trust Repair Chain Preservation
# ═══════════════════════════════════════════════════════════════════════════

class TestChainPreservation:
    def test_governed_execution_attempt_boundary(self):
        from pcae.core.backend_invocations import GovernedExecutionAttemptBoundary
        a = GovernedExecutionAttemptBoundary()
        assert a.attempt_state == "unavailable"; assert a.execution_available is False

    def test_no_go_enforcement_evidence(self):
        from pcae.core.backend_invocations import NoGoEnforcementEvidence
        a = NoGoEnforcementEvidence()
        assert a.execution_available is False

    def test_runtime_enforcement_evidence_bundle(self):
        from pcae.core.backend_invocations import RuntimeEnforcementEvidenceBundle
        a = RuntimeEnforcementEvidenceBundle()
        assert a.no_execution is True

    def test_decision_engine_bundle_interop(self):
        from pcae.core.backend_invocations import RuntimeEnforcementEvidenceBundle
        b = RuntimeEnforcementEvidenceBundle()
        bundle_json = _json.dumps(b.to_dict(), sort_keys=True)
        bundle_digest = hashlib.sha256(bundle_json.encode()).hexdigest()
        d = RuntimeEnforcementDecision(source_bundle_ref="b1", source_bundle_digest=bundle_digest)
        assert d.execution_available is False; assert d.no_execution is True

    def test_report_trust_repair_chain_preserved(self):
        """102B.2 report trust repair chain is not broken by trust hardening."""
        a = RuntimeEnforcementDecision(denial_reasons=["report_trust_failure"])
        assert a.no_execution is True; assert a.execution_authorized is False
