"""Tests for human approval gate models — Phase 97D.

All models must remain non-executing and non-authorizing.
Tests prove that approval artifacts cannot authorize execution,
cannot override no-go conditions, and are properly fail-closed.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from pcae.core.human_approval_gate import (
    SCHEMA_VERSION,
    APPROVAL_DECISION_APPROVED,
    APPROVAL_DECISION_DENIED,
    APPROVAL_DECISION_REVOKED,
    APPROVAL_DECISION_EXPIRED,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    SCOPE_READINESS_REVIEW,
    SCOPE_BACKEND_INVOCATION,
    SCOPE_ADAPTER_EXECUTION,
    SCOPE_APPLY,
    SCOPE_COMMIT,
    SCOPE_PUSH,
    SCOPE_OUTPUT_REVIEW,
    DENIED_MISSING_READINESS,
    DENIED_MISSING_BACKEND_REQUEST,
    DENIED_MISSING_ADAPTER_REQUEST,
    DENIED_MISSING_EVIDENCE_CHAIN,
    DENIED_NO_GO_CONDITION_PRESENT,
    DENIED_SCOPE_MISMATCH,
    DENIED_TASK_MISMATCH,
    DENIED_PHASE_MISMATCH,
    DENIED_EXPIRED,
    DENIED_REVOKED,
    DENIED_STALE_ARTIFACT,
    DENIED_FAILED_VERIFICATION,
    DENIED_FORBIDDEN_SCOPE,
    DENIED_BYPASS_PERMISSIONS,
    DENIED_RAW_GIT_PATH,
    DENIED_NO_VERIFY_ATTEMPT,
    DENIED_FORCE_PUSH_ATTEMPT,
    DENIED_UNKNOWN_SCHEMA,
    DENIED_CONFLICTING_SAFETY_FLAGS,
    APPROVAL_STATUS_DENIED,
    VALID_APPROVAL_SCOPES,
    VALID_APPROVAL_DECISIONS,
    VALID_DENIAL_REASONS,
    REVIEW_ONLY_SCOPES,
    EXECUTION_SCOPES,
    MUTATION_SCOPES,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalRevocation,
    ApprovalDenial,
    ApprovalVerificationResult,
    verify_approval,
)


# ── Helper factories ───────────────────────────────────────────────────────

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _future_iso(hours: int = 8) -> str:
    return (_utc_now() + timedelta(hours=hours)).isoformat()


def _past_iso(hours: int = 1) -> str:
    return (_utc_now() - timedelta(hours=hours)).isoformat()


def make_request(**overrides) -> ApprovalRequest:
    """Create a valid, minimal approval request."""
    kwargs = {
        "phase_id": "phase-97d",
        "task_id": "task-97d-test",
        "requested_by": "test-operator",
        "requested_action_class": "readiness_review",
        "requested_scope": SCOPE_READINESS_REVIEW,
        "readiness_artifact_ref": "ref/readiness/97d",
        "evidence_chain_ref": "ref/evidence/97d",
        "artifact_verification_ref": "ref/verify/97d",
        "execution_boundary_proof_ref": "ref/proof/97d",
        "expires_at_utc": _future_iso(8),
        "risk_summary": "Low risk — design phase only",
        **overrides,
    }
    return ApprovalRequest(**kwargs)


def make_decision(request: ApprovalRequest | None = None, **overrides) -> ApprovalDecision:
    """Create a valid, minimal approval decision linked to a request."""
    req = request or make_request()
    kwargs = {
        "approval_request_id": req.approval_request_id,
        "phase_id": req.phase_id,
        "task_id": req.task_id,
        "decided_by": "test-operator",
        "decision": APPROVAL_DECISION_APPROVED,
        "approval_scope": req.requested_scope,
        "readiness_artifact_ref": req.readiness_artifact_ref,
        "evidence_chain_ref": req.evidence_chain_ref,
        "artifact_verification_ref": req.artifact_verification_ref,
        "expiry": req.expires_at_utc,
        "human_confirmation_text": "I approve this design-only phase.",
        **overrides,
    }
    return ApprovalDecision(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# Constants / enums
# ═══════════════════════════════════════════════════════════════════════════


class TestConstants:
    """Verify constant sets are well-formed."""

    def test_valid_scopes_are_comprehensive(self):
        assert len(VALID_APPROVAL_SCOPES) == 9
        assert SCOPE_READINESS_REVIEW in VALID_APPROVAL_SCOPES
        assert SCOPE_BACKEND_INVOCATION in VALID_APPROVAL_SCOPES
        assert SCOPE_ADAPTER_EXECUTION in VALID_APPROVAL_SCOPES
        assert SCOPE_APPLY in VALID_APPROVAL_SCOPES
        assert SCOPE_COMMIT in VALID_APPROVAL_SCOPES
        assert SCOPE_PUSH in VALID_APPROVAL_SCOPES

    def test_review_scopes_are_subset(self):
        assert REVIEW_ONLY_SCOPES.issubset(VALID_APPROVAL_SCOPES)
        assert SCOPE_BACKEND_INVOCATION not in REVIEW_ONLY_SCOPES
        assert SCOPE_APPLY not in REVIEW_ONLY_SCOPES

    def test_execution_scopes_are_subset(self):
        assert EXECUTION_SCOPES.issubset(VALID_APPROVAL_SCOPES)
        assert SCOPE_READINESS_REVIEW not in EXECUTION_SCOPES

    def test_mutation_scopes_are_subset(self):
        assert MUTATION_SCOPES.issubset(VALID_APPROVAL_SCOPES)
        assert SCOPE_READINESS_REVIEW not in MUTATION_SCOPES

    def test_review_execution_mutation_disjoint(self):
        """Review, execution, and mutation scopes should not overlap."""
        assert REVIEW_ONLY_SCOPES.isdisjoint(EXECUTION_SCOPES)
        assert REVIEW_ONLY_SCOPES.isdisjoint(MUTATION_SCOPES)
        assert EXECUTION_SCOPES.isdisjoint(MUTATION_SCOPES)

    def test_denial_reasons_count(self):
        assert len(VALID_DENIAL_REASONS) == 21

    def test_valid_decisions(self):
        assert APPROVAL_DECISION_APPROVED in VALID_APPROVAL_DECISIONS
        assert APPROVAL_DECISION_DENIED in VALID_APPROVAL_DECISIONS
        assert APPROVAL_DECISION_REVOKED in VALID_APPROVAL_DECISIONS
        assert APPROVAL_DECISION_EXPIRED in VALID_APPROVAL_DECISIONS


# ═══════════════════════════════════════════════════════════════════════════
# ApprovalRequest — non-execution invariants
# ═══════════════════════════════════════════════════════════════════════════


class TestApprovalRequestNonExecuting:
    """Approval requests must always be non-executing."""

    def test_request_is_non_executing_by_default(self):
        req = make_request()
        assert req.is_non_executing()
        assert req.execution_available is False
        assert req.execution_authorized is False
        assert req.backend_invocation_authorized is False
        assert req.adapter_execution_authorized is False
        assert req.apply_authorized is False
        assert req.commit_authorized is False
        assert req.push_authorized is False
        assert req.simulation_only is True
        assert req.no_execution is True
        assert req.human_review_required is True

    def test_request_cannot_set_execution_available_true(self):
        req = make_request()
        # Direct assignment should be overridden by __post_init__
        # But we can test that a freshly created request always has it false
        req2 = ApprovalRequest(
            execution_available=True,
            execution_authorized=True,
            backend_invocation_authorized=True,
            adapter_execution_authorized=True,
            apply_authorized=True,
            commit_authorized=True,
            push_authorized=True,
            simulation_only=False,
            no_execution=False,
        )
        # __post_init__ forces them all back to non-executing
        assert req2.execution_available is False
        assert req2.execution_authorized is False
        assert req2.backend_invocation_authorized is False
        assert req2.adapter_execution_authorized is False
        assert req2.apply_authorized is False
        assert req2.commit_authorized is False
        assert req2.push_authorized is False
        assert req2.simulation_only is True
        assert req2.no_execution is True
        assert req2.is_non_executing()

    def test_request_validate_rejects_execution_available_true(self):
        req = make_request()
        req.execution_available = True  # bypass __post_init__
        issues = req.validate()
        assert any("execution_available must be False" in i for i in issues)

    def test_request_validate_rejects_simulation_only_false(self):
        req = make_request()
        req.simulation_only = False
        issues = req.validate()
        assert any("simulation_only must be True" in i for i in issues)

    def test_request_validate_rejects_no_execution_false(self):
        req = make_request()
        req.no_execution = False
        issues = req.validate()
        assert any("no_execution must be True" in i for i in issues)


class TestApprovalRequestValidation:
    """Basic validation rules for approval requests."""

    def test_valid_request_passes_validation(self):
        req = make_request()
        issues = req.validate()
        assert issues == []

    def test_missing_phase_id(self):
        req = make_request(phase_id="")
        issues = req.validate()
        assert any("phase_id is required" in i for i in issues)

    def test_missing_task_id(self):
        req = make_request(task_id="")
        issues = req.validate()
        assert any("task_id is required" in i for i in issues)

    def test_missing_requested_by(self):
        req = make_request(requested_by="")
        issues = req.validate()
        assert any("requested_by is required" in i for i in issues)

    def test_invalid_scope(self):
        req = make_request(requested_scope="invalid_scope")
        issues = req.validate()
        assert any("invalid requested_scope" in i for i in issues)

    def test_invalid_approval_status(self):
        req = make_request(approval_status="bogus")
        issues = req.validate()
        assert any("invalid approval_status" in i for i in issues)

    def test_auto_generated_request_id(self):
        req = ApprovalRequest()
        assert req.approval_request_id != ""

    def test_auto_generated_timestamp(self):
        req = ApprovalRequest()
        assert req.requested_at_utc != ""

    def test_compute_digest_is_stable(self):
        req = make_request()
        d1 = req.compute_digest()
        d2 = req.compute_digest()
        assert d1 == d2
        assert len(d1) == 64  # SHA-256 hex

    def test_digest_changes_on_field_change(self):
        req = make_request()
        d1 = req.compute_digest()
        req.phase_id = "different-phase"
        d2 = req.compute_digest()
        assert d1 != d2

    def test_to_dict_and_from_dict_roundtrip(self):
        req = make_request()
        req.compute_digest()
        data = req.to_dict()
        req2 = ApprovalRequest.from_dict(data)
        assert req2.approval_request_id == req.approval_request_id
        assert req2.phase_id == req.phase_id
        assert req2.task_id == req.task_id
        assert req2.digest == req.digest
        assert req2.is_non_executing()


# ═══════════════════════════════════════════════════════════════════════════
# ApprovalDecision — non-execution invariants
# ═══════════════════════════════════════════════════════════════════════════


class TestApprovalDecisionNonExecuting:
    """Approval decisions must always be non-executing, even when approved."""

    def test_approved_decision_is_non_executing(self):
        dec = make_decision(decision=APPROVAL_DECISION_APPROVED)
        assert dec.is_non_executing()
        assert dec.execution_available is False
        assert dec.execution_authorized is False
        assert dec.backend_invocation_authorized is False
        assert dec.adapter_execution_authorized is False
        assert dec.apply_authorized is False
        assert dec.commit_authorized is False
        assert dec.push_authorized is False
        assert dec.simulation_only is True
        assert dec.no_execution is True

    def test_approved_decision_does_not_set_execution_authorized_true(self):
        """Even an approved decision must have execution_authorized=False."""
        dec = make_decision(decision=APPROVAL_DECISION_APPROVED)
        assert dec.execution_authorized is False, (
            "execution_authorized must remain False even for approved decisions"
        )

    def test_backend_invocation_authorized_remains_false(self):
        dec = make_decision(decision=APPROVAL_DECISION_APPROVED)
        assert dec.backend_invocation_authorized is False

    def test_adapter_execution_authorized_remains_false(self):
        dec = make_decision(decision=APPROVAL_DECISION_APPROVED)
        assert dec.adapter_execution_authorized is False

    def test_apply_commit_push_remain_false(self):
        dec = make_decision(decision=APPROVAL_DECISION_APPROVED)
        assert dec.apply_authorized is False
        assert dec.commit_authorized is False
        assert dec.push_authorized is False

    def test_decision_forces_non_executing_regardless_of_input(self):
        """__post_init__ must force all auth flags false even if passed True."""
        dec = ApprovalDecision(
            execution_available=True,
            execution_authorized=True,
            backend_invocation_authorized=True,
            adapter_execution_authorized=True,
            apply_authorized=True,
            commit_authorized=True,
            push_authorized=True,
            simulation_only=False,
            no_execution=False,
            non_transferable=False,
            no_override_no_go=False,
            no_override_failed_verification=False,
            no_override_scope_violation=False,
            no_raw_git_allowed=False,
            no_no_verify_allowed=False,
            no_force_push_allowed=False,
        )
        assert dec.execution_available is False
        assert dec.execution_authorized is False
        assert dec.backend_invocation_authorized is False
        assert dec.adapter_execution_authorized is False
        assert dec.apply_authorized is False
        assert dec.commit_authorized is False
        assert dec.push_authorized is False
        assert dec.simulation_only is True
        assert dec.no_execution is True
        assert dec.non_transferable is True
        assert dec.no_override_no_go is True
        assert dec.no_override_failed_verification is True
        assert dec.no_override_scope_violation is True
        assert dec.no_raw_git_allowed is True
        assert dec.no_no_verify_allowed is True
        assert dec.no_force_push_allowed is True


class TestApprovalDecisionValidation:
    """Basic validation rules for approval decisions."""

    def test_valid_decision_passes_validation(self):
        dec = make_decision()
        issues = dec.validate()
        assert issues == []

    def test_missing_decision_id(self):
        dec = make_decision()
        dec.approval_decision_id = ""  # bypass __post_init__ auto-gen
        issues = dec.validate()
        assert any("approval_decision_id is required" in i for i in issues)

    def test_missing_request_id(self):
        dec = make_decision(approval_request_id="")
        issues = dec.validate()
        assert any("approval_request_id is required" in i for i in issues)

    def test_missing_decided_by(self):
        dec = make_decision(decided_by="")
        issues = dec.validate()
        assert any("decided_by is required" in i for i in issues)

    def test_invalid_decision_status(self):
        dec = make_decision(decision="bogus")
        issues = dec.validate()
        assert any("invalid decision" in i for i in issues)

    def test_invalid_scope(self):
        dec = make_decision(approval_scope="invalid_scope")
        issues = dec.validate()
        assert any("invalid approval_scope" in i for i in issues)

    def test_validate_rejects_non_transferable_false(self):
        dec = make_decision()
        dec.non_transferable = False  # bypass __post_init__
        issues = dec.validate()
        assert any("non_transferable must be True" in i for i in issues)

    def test_validate_rejects_no_override_no_go_false(self):
        dec = make_decision()
        dec.no_override_no_go = False  # bypass __post_init__
        issues = dec.validate()
        assert any("no_override_no_go must be True" in i for i in issues)

    def test_validate_rejects_no_raw_git_allowed_false(self):
        dec = make_decision()
        dec.no_raw_git_allowed = False  # bypass __post_init__
        issues = dec.validate()
        assert any("no_raw_git_allowed must be True" in i for i in issues)

    def test_validate_rejects_no_no_verify_allowed_false(self):
        dec = make_decision()
        dec.no_no_verify_allowed = False  # bypass __post_init__
        issues = dec.validate()
        assert any("no_no_verify_allowed must be True" in i for i in issues)

    def test_validate_rejects_no_force_push_allowed_false(self):
        dec = make_decision()
        dec.no_force_push_allowed = False  # bypass __post_init__
        issues = dec.validate()
        assert any("no_force_push_allowed must be True" in i for i in issues)

    def test_auto_generated_decision_id(self):
        dec = ApprovalDecision()
        assert dec.approval_decision_id != ""

    def test_auto_generated_timestamp(self):
        dec = ApprovalDecision()
        assert dec.decided_at_utc != ""

    def test_compute_digest_is_stable(self):
        dec = make_decision()
        d1 = dec.compute_digest()
        d2 = dec.compute_digest()
        assert d1 == d2

    def test_to_dict_and_from_dict_roundtrip(self):
        dec = make_decision()
        dec.compute_digest()
        data = dec.to_dict()
        dec2 = ApprovalDecision.from_dict(data)
        assert dec2.approval_decision_id == dec.approval_decision_id
        assert dec2.decision == dec.decision
        assert dec2.digest == dec.digest
        assert dec2.is_non_executing()


# ═══════════════════════════════════════════════════════════════════════════
# Approval artifact is non-transferable
# ═══════════════════════════════════════════════════════════════════════════


class TestApprovalNonTransferable:
    """Approval artifacts must be non-transferable."""

    def test_decision_is_non_transferable_by_default(self):
        dec = make_decision()
        assert dec.non_transferable is True

    def test_decision_cannot_be_made_transferable(self):
        dec = ApprovalDecision(non_transferable=False)
        assert dec.non_transferable is True  # forced by __post_init__

    def test_approval_for_backend_invocation_does_not_authorize_apply(self):
        req = make_request(
            requested_scope=SCOPE_BACKEND_INVOCATION,
            requested_action_class="backend_invocation",
        )
        dec = make_decision(
            request=req,
            approval_scope=SCOPE_BACKEND_INVOCATION,
        )
        assert dec.apply_authorized is False
        assert dec.commit_authorized is False
        assert dec.push_authorized is False

    def test_approval_for_backend_invocation_does_not_authorize_adapter(self):
        req = make_request(
            requested_scope=SCOPE_BACKEND_INVOCATION,
            requested_action_class="backend_invocation",
        )
        dec = make_decision(
            request=req,
            approval_scope=SCOPE_BACKEND_INVOCATION,
        )
        assert dec.adapter_execution_authorized is False


# ═══════════════════════════════════════════════════════════════════════════
# Approval scope separation
# ═══════════════════════════════════════════════════════════════════════════


class TestScopeSeparation:
    """Each scope is independent — approval for one does not authorize another."""

    def test_readiness_review_does_not_authorize_backend_invocation(self):
        req = make_request(requested_scope=SCOPE_READINESS_REVIEW)
        dec = make_decision(request=req, approval_scope=SCOPE_READINESS_REVIEW)
        assert dec.execution_authorized is False
        assert dec.backend_invocation_authorized is False

    def test_backend_invocation_does_not_authorize_apply(self):
        req = make_request(requested_scope=SCOPE_BACKEND_INVOCATION)
        dec = make_decision(request=req, approval_scope=SCOPE_BACKEND_INVOCATION)
        assert dec.apply_authorized is False

    def test_apply_does_not_authorize_commit(self):
        req = make_request(requested_scope=SCOPE_APPLY)
        dec = make_decision(request=req, approval_scope=SCOPE_APPLY)
        assert dec.commit_authorized is False

    def test_commit_does_not_authorize_push(self):
        req = make_request(requested_scope=SCOPE_COMMIT)
        dec = make_decision(request=req, approval_scope=SCOPE_COMMIT)
        assert dec.push_authorized is False


# ═══════════════════════════════════════════════════════════════════════════
# Approval verification — fail-closed
# ═══════════════════════════════════════════════════════════════════════════


class TestApprovalVerificationPasses:
    """Happy-path verification scenarios."""

    def test_verify_matching_approval_passes(self):
        req = make_request()
        dec = make_decision(request=req)
        dec.compute_digest()
        result = verify_approval(
            dec, req,
            expected_task_id=req.task_id,
            expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
        )
        assert result.verified is True, f"Expected pass, got: {result.denial_reasons}"
        assert result.denial_reasons == []


class TestApprovalVerificationFailClosed:
    """Fail-closed behavior: every mismatch or missing field must deny."""

    def test_expired_approval_fails_verification(self):
        req = make_request(expires_at_utc=_past_iso(1))
        dec = make_decision(request=req, expiry=_past_iso(1))
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_EXPIRED in result.denial_reasons

    def test_revoked_approval_fails_verification(self):
        req = make_request()
        dec = make_decision(
            request=req, decision=APPROVAL_DECISION_REVOKED,
            revocation_ref="ref/revocation/1")
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_REVOKED in result.denial_reasons

    def test_denied_decision_fails_verification(self):
        req = make_request()
        dec = make_decision(request=req, decision=APPROVAL_DECISION_DENIED)
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert "denied_by_operator" in result.denial_reasons

    def test_expired_decision_fails_verification(self):
        req = make_request()
        dec = make_decision(request=req, decision=APPROVAL_DECISION_EXPIRED)
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_EXPIRED in result.denial_reasons

    def test_scope_mismatch_fails_verification(self):
        req = make_request(requested_scope=SCOPE_READINESS_REVIEW)
        dec = make_decision(request=req, approval_scope=SCOPE_BACKEND_INVOCATION)
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_SCOPE_MISMATCH in result.denial_reasons

    def test_task_mismatch_fails_verification(self):
        req = make_request(task_id="task-A")
        dec = make_decision(request=req, task_id="task-A")
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id="task-B", expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_TASK_MISMATCH in result.denial_reasons

    def test_phase_mismatch_fails_verification(self):
        req = make_request(phase_id="phase-A")
        dec = make_decision(request=req, phase_id="phase-A")
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id="phase-B",
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_PHASE_MISMATCH in result.denial_reasons

    def test_no_go_condition_present_fails_verification(self):
        req = make_request(no_go_conditions=["test_no_go"])
        dec = make_decision(request=req)
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
            no_go_conditions_present=["active_blocker"])
        assert result.verified is False
        assert DENIED_NO_GO_CONDITION_PRESENT in result.denial_reasons

    def test_failed_artifact_verification_fails_approval(self):
        req = make_request()
        dec = make_decision(request=req)
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
            artifact_verification_failed=True)
        assert result.verified is False
        assert DENIED_FAILED_VERIFICATION in result.denial_reasons

    def test_bypass_permissions_fails_verification(self):
        req = make_request()
        dec = make_decision(request=req)
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
            bypass_permissions_detected=True)
        assert result.verified is False
        assert DENIED_BYPASS_PERMISSIONS in result.denial_reasons

    def test_raw_git_fails_verification(self):
        req = make_request()
        dec = make_decision(request=req)
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
            raw_git_detected=True)
        assert result.verified is False
        assert DENIED_RAW_GIT_PATH in result.denial_reasons

    def test_no_verify_fails_verification(self):
        req = make_request()
        dec = make_decision(request=req)
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
            no_verify_detected=True)
        assert result.verified is False
        assert DENIED_NO_VERIFY_ATTEMPT in result.denial_reasons

    def test_force_push_fails_verification(self):
        req = make_request()
        dec = make_decision(request=req)
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
            force_push_detected=True)
        assert result.verified is False
        assert DENIED_FORCE_PUSH_ATTEMPT in result.denial_reasons

    def test_stale_digest_fails_verification(self):
        req = make_request()
        dec = make_decision(request=req)
        dec.compute_digest()
        # Tamper with a non-scope field that affects digest but not other checks
        dec.human_confirmation_text = "Tampered text"
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_STALE_ARTIFACT in result.denial_reasons

    def test_request_decision_mismatch_fails_verification(self):
        req = make_request()
        dec = make_decision(request=req)
        dec.compute_digest()
        # Link decision to a different request
        dec.approval_request_id = "different-request-id"
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert "denied_request_decision_mismatch" in result.denial_reasons

    def test_contradictory_safety_flags_fail_verification(self):
        req = make_request()
        dec = make_decision(request=req)
        dec.compute_digest()
        dec.no_override_no_go = False
        dec.no_override_failed_verification = False
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_CONFLICTING_SAFETY_FLAGS in result.denial_reasons

    def test_missing_readiness_ref_fails_verification(self):
        req = make_request(readiness_artifact_ref="")
        dec = make_decision(request=req, readiness_artifact_ref="")
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_MISSING_READINESS in result.denial_reasons

    def test_missing_evidence_chain_fails_verification(self):
        req = make_request(evidence_chain_ref="")
        dec = make_decision(request=req, evidence_chain_ref="")
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref)
        assert result.verified is False
        assert DENIED_MISSING_EVIDENCE_CHAIN in result.denial_reasons

    def test_forbidden_scope_fails_verification(self):
        req = make_request(
            requested_scope=SCOPE_APPLY,
            requested_action_class=SCOPE_APPLY,
        )
        dec = make_decision(
            request=req,
            approval_scope=SCOPE_APPLY,
            approval_exclusions=[SCOPE_APPLY],
        )
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_FORBIDDEN_SCOPE in result.denial_reasons

    def test_approval_cannot_override_no_go_condition(self):
        """Even with an approved decision, a no-go condition blocks verification."""
        req = make_request(no_go_conditions=["active_blocker"])
        dec = make_decision(
            request=req,
            decision=APPROVAL_DECISION_APPROVED,
        )
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
            no_go_conditions_present=["active_blocker"])
        assert result.verified is False
        assert DENIED_NO_GO_CONDITION_PRESENT in result.denial_reasons
        # Even though the decision is "approved"
        assert dec.decision == APPROVAL_DECISION_APPROVED
        assert dec.no_override_no_go is True


# ═══════════════════════════════════════════════════════════════════════════
# ApprovalRevocation
# ═══════════════════════════════════════════════════════════════════════════


class TestApprovalRevocation:
    """Approval revocations record negation of prior decisions."""

    def test_revocation_auto_generates_id(self):
        rev = ApprovalRevocation(
            approval_decision_id="dec-1",
            approval_request_id="req-1",
            revoked_by="operator",
            reason="Mistake in scope",
        )
        assert rev.revocation_id != ""
        assert rev.revoked_at_utc != ""

    def test_revocation_validation_requires_fields(self):
        rev = ApprovalRevocation()
        issues = rev.validate()
        assert any("approval_decision_id is required" in i for i in issues)
        assert any("revoked_by is required" in i for i in issues)
        assert any("reason is required" in i for i in issues)

    def test_revocation_becomes_verification_blocker(self):
        req = make_request()
        dec = make_decision(
            request=req, decision=APPROVAL_DECISION_REVOKED,
            revocation_ref="ref/rev/1")
        dec.compute_digest()
        result = verify_approval(dec, req,
            expected_task_id=req.task_id, expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref)
        assert result.verified is False
        assert DENIED_REVOKED in result.denial_reasons


# ═══════════════════════════════════════════════════════════════════════════
# ApprovalDenial
# ═══════════════════════════════════════════════════════════════════════════


class TestApprovalDenial:
    """Approval denials record explicit rejection of requests."""

    def test_denial_auto_generates_id(self):
        den = ApprovalDenial(
            approval_request_id="req-1",
            denied_by="operator",
            denial_reasons=[DENIED_SCOPE_MISMATCH],
        )
        assert den.denial_id != ""
        assert den.denied_at_utc != ""

    def test_denial_validation_requires_reasons(self):
        den = ApprovalDenial(
            approval_request_id="req-1",
            denied_by="operator",
        )
        issues = den.validate()
        assert any("at least one denial_reason" in i for i in issues)

    def test_denial_validation_rejects_invalid_reasons(self):
        den = ApprovalDenial(
            approval_request_id="req-1",
            denied_by="operator",
            denial_reasons=["bogus_reason"],
        )
        issues = den.validate()
        assert any("invalid denial_reason" in i for i in issues)

    def test_all_denial_reasons_are_valid(self):
        for reason in VALID_DENIAL_REASONS:
            den = ApprovalDenial(
                approval_request_id="req-1",
                denied_by="operator",
                denial_reasons=[reason],
            )
            issues = den.validate()
            assert not any("invalid denial_reason" in i for i in issues), \
                f"Expected {reason!r} to be valid, got issues: {issues}"


# ═══════════════════════════════════════════════════════════════════════════
# Integration: full approval lifecycle
# ═══════════════════════════════════════════════════════════════════════════


class TestApprovalLifecycle:
    """End-to-end approval lifecycle: request → decision → verify → revoke."""

    def test_full_lifecycle_request_approve_verify(self):
        # 1. Create request
        req = make_request(
            phase_id="phase-97d",
            task_id="task-lifecycle-test",
            requested_scope=SCOPE_READINESS_REVIEW,
            readiness_artifact_ref="ref/readiness/xyz",
            evidence_chain_ref="ref/evidence/xyz",
        )
        req.compute_digest()
        assert req.is_non_executing()
        assert req.approval_status == APPROVAL_STATUS_PENDING

        # 2. Create decision (approved)
        dec = make_decision(
            request=req,
            decision=APPROVAL_DECISION_APPROVED,
            approval_scope=SCOPE_READINESS_REVIEW,
            human_confirmation_text="Design phase, safe to proceed.",
        )
        dec.compute_digest()
        assert dec.is_non_executing()
        assert dec.execution_authorized is False

        # 3. Verify
        result = verify_approval(
            dec, req,
            expected_task_id=req.task_id,
            expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
        )
        assert result.verified is True

        # 4. Revoke
        rev = ApprovalRevocation(
            approval_decision_id=dec.approval_decision_id,
            approval_request_id=req.approval_request_id,
            revoked_by="test-operator",
            reason="Scope changed",
            phase_id=req.phase_id,
            task_id=req.task_id,
        )
        assert rev.revocation_id != ""

        # 5. Verify after revocation — should fail
        dec2 = make_decision(
            request=req,
            decision=APPROVAL_DECISION_REVOKED,
            approval_scope=SCOPE_READINESS_REVIEW,
            revocation_ref=rev.revocation_id,
            human_confirmation_text="Revoked.",
        )
        dec2.compute_digest()
        result2 = verify_approval(
            dec2, req,
            expected_task_id=req.task_id,
            expected_phase_id=req.phase_id,
            expected_readiness_ref=req.readiness_artifact_ref,
            expected_evidence_chain_ref=req.evidence_chain_ref,
        )
        assert result2.verified is False
        assert DENIED_REVOKED in result2.denial_reasons

    def test_approval_for_execution_scope_still_non_executing(self):
        """Even approval scoped to backend_invocation must be non-executing."""
        req = make_request(
            requested_scope=SCOPE_BACKEND_INVOCATION,
            requested_action_class="backend_invocation",
        )
        dec = make_decision(
            request=req,
            decision=APPROVAL_DECISION_APPROVED,
            approval_scope=SCOPE_BACKEND_INVOCATION,
            human_confirmation_text="Approved for future execution.",
        )
        # The decision is "approved" but still non-executing
        assert dec.is_non_executing()
        assert dec.execution_available is False
        assert dec.execution_authorized is False
        assert dec.backend_invocation_authorized is False
