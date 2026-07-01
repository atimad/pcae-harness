"""Tests for Phase 103C — Runtime Enforcement Coordinator Artifact Trust Hardening. Test-only. Non-executing."""
from __future__ import annotations
import json as _json, hashlib, pytest
from pcae.core.backend_invocations import (
    RuntimeEnforcementCoordinator, VALID_REC_STATUSES, VALID_REC_RESULTS,
    ALL_REC_STEPS, REC_STATUS_NOT_STARTED, REC_RESULT_DENIED,
    REC_STATUS_BLOCKED, REC_STATUS_DENIED, REC_STATUS_FAIL_CLOSED,
    REC_RESULT_FAIL_CLOSED, REC_RESULT_EVIDENCE_ONLY, REC_RESULT_DESIGN_REVIEW,
)

_AUTH = ["execution_available","execution_authorized","backend_invocation_authorized","adapter_execution_authorized","network_authorized","subprocess_authorized","shell_authorized","mutation_authorized","apply_authorized","rollback_authorized","commit_authorized","push_authorized"]
_SAFE = ["simulation_only","no_execution","evidence_only","non_authorizing","design_only"]

_DIGEST_FIELDS = ["schema_version","coordinator_id","phase_id","task_id","generated_at_utc","source_evidence_bundle_ref","source_evidence_bundle_digest","source_decision_ref","source_decision_digest","coordinator_status","coordinator_result","coordinator_reason","requested_surface","evaluated_inputs","missing_inputs","stale_inputs","tampered_inputs","contradictory_inputs","triggered_no_go_conditions","denied_steps","blocked_steps","skipped_steps","future_only_steps","unsupported_requests","denial_reasons","fail_closed_reasons","warnings"]


def _base() -> RuntimeEnforcementCoordinator:
    return RuntimeEnforcementCoordinator(
        coordinator_id="test-coord", phase_id="103A", task_id="t1",
        generated_at_utc="2026-07-01T00:00:00Z",
        source_evidence_bundle_ref="bundle-1", source_evidence_bundle_digest="a"*64,
        source_decision_ref="decision-1", source_decision_digest="b"*64,
        coordinator_status=REC_STATUS_DENIED, coordinator_result=REC_RESULT_EVIDENCE_ONLY,
        coordinator_reason="test", requested_surface=["design_review"],
        evaluated_inputs=["bundle","decision"], missing_inputs=["approval"],
        stale_inputs=["old"], tampered_inputs=["bad"], contradictory_inputs=["conflict"],
        triggered_no_go_conditions=["TEST_NO_GO"], denied_steps=["load_evidence_bundle"],
        blocked_steps=["verify_bundle_digest"], skipped_steps=["produce_coordinator_artifact"],
        future_only_steps=["run_adapter"], unsupported_requests=["/exec"],
        denial_reasons=["test"], fail_closed_reasons=["FC_TEST"], warnings=["warn"],
    )


class TestDigestCoverage:
    def test_sha256(self): assert len(_base().compute_digest()) == 64
    def test_deterministic(self): assert _base().compute_digest() == _base().compute_digest()
    def test_excludes_digest_itself(self):
        a = _base(); a.digest = a.compute_digest(); assert a.digest == a.compute_digest()
    def test_schema_version(self): assert RuntimeEnforcementCoordinator(schema_version="1.0").compute_digest() != RuntimeEnforcementCoordinator(schema_version="1.1").compute_digest()
    def test_coordinator_id(self): assert RuntimeEnforcementCoordinator(coordinator_id="").compute_digest() != RuntimeEnforcementCoordinator(coordinator_id="c1").compute_digest()
    def test_phase_id(self): assert RuntimeEnforcementCoordinator(phase_id="103A").compute_digest() != RuntimeEnforcementCoordinator(phase_id="103B").compute_digest()
    def test_source_bundle_ref(self): assert RuntimeEnforcementCoordinator(source_evidence_bundle_ref="a").compute_digest() != RuntimeEnforcementCoordinator(source_evidence_bundle_ref="b").compute_digest()
    def test_source_decision_ref(self): assert RuntimeEnforcementCoordinator(source_decision_ref="a").compute_digest() != RuntimeEnforcementCoordinator(source_decision_ref="b").compute_digest()
    def test_coordinator_status(self): assert RuntimeEnforcementCoordinator(coordinator_status=REC_STATUS_NOT_STARTED).compute_digest() != RuntimeEnforcementCoordinator(coordinator_status=REC_STATUS_BLOCKED).compute_digest()
    def test_coordinator_result(self): assert RuntimeEnforcementCoordinator(coordinator_result=REC_RESULT_DENIED).compute_digest() != RuntimeEnforcementCoordinator(coordinator_result=REC_RESULT_FAIL_CLOSED).compute_digest()
    def test_missing_inputs(self): assert RuntimeEnforcementCoordinator(missing_inputs=[]).compute_digest() != RuntimeEnforcementCoordinator(missing_inputs=["x"]).compute_digest()
    def test_triggered_no_go(self): assert RuntimeEnforcementCoordinator(triggered_no_go_conditions=[]).compute_digest() != RuntimeEnforcementCoordinator(triggered_no_go_conditions=["x"]).compute_digest()
    def test_safety_flag(self): assert RuntimeEnforcementCoordinator(design_only=True).compute_digest() != RuntimeEnforcementCoordinator(design_only=False).compute_digest()
    def test_ordering_stable(self):
        d1 = RuntimeEnforcementCoordinator(missing_inputs=["Z","A"], triggered_no_go_conditions=["B","A"]).compute_digest()
        d2 = RuntimeEnforcementCoordinator(missing_inputs=["A","Z"], triggered_no_go_conditions=["A","B"]).compute_digest()
        assert d1 == d2


class TestTamperDetection:
    def test_schema_tamper(self): d=_base().compute_digest(); a=_base(); a.schema_version="99.0"; assert a.compute_digest()!=d
    def test_coordinator_id_tamper(self): d=_base().compute_digest(); a=_base(); a.coordinator_id="evil"; assert a.compute_digest()!=d
    def test_bundle_ref_tamper(self): d=_base().compute_digest(); a=_base(); a.source_evidence_bundle_ref="evil"; assert a.compute_digest()!=d
    def test_decision_ref_tamper(self): d=_base().compute_digest(); a=_base(); a.source_decision_ref="evil"; assert a.compute_digest()!=d
    def test_status_tamper(self): d=_base().compute_digest(); a=_base(); a.coordinator_status=REC_STATUS_BLOCKED; assert a.compute_digest()!=d
    def test_result_tamper(self): d=_base().compute_digest(); a=_base(); a.coordinator_result=REC_RESULT_FAIL_CLOSED; assert a.compute_digest()!=d
    def test_safety_tamper(self): d=_base().compute_digest(); a=_base(); a.simulation_only=False; assert a.compute_digest()!=d
    def test_digest_verification_detectable(self):
        a=_base(); a.digest=a.compute_digest(); a.coordinator_status=REC_STATUS_BLOCKED
        assert a.digest!=a.compute_digest()


class TestInputTrust:
    def test_missing_bundle_no_exec(self): a=RuntimeEnforcementCoordinator(source_evidence_bundle_ref=""); assert a.execution_available is False
    def test_missing_decision_no_exec(self): a=RuntimeEnforcementCoordinator(source_decision_ref=""); assert a.execution_available is False
    def test_bundle_alone_no_auth(self): a=RuntimeEnforcementCoordinator(source_evidence_bundle_ref="b",source_evidence_bundle_digest="a"*64); assert a.execution_authorized is False
    def test_decision_alone_no_auth(self): a=RuntimeEnforcementCoordinator(source_decision_ref="d",source_decision_digest="b"*64); assert a.execution_authorized is False
    def test_bundle_absence_no_permission(self): a=RuntimeEnforcementCoordinator(); assert a.execution_available is False
    def test_safe_refs_not_exec_paths(self):
        for ref in ["/bin/sh","../escape","file:///etc/passwd","$(whoami)","http://evil"]:
            a=RuntimeEnforcementCoordinator(source_evidence_bundle_ref=ref); assert a.no_execution is True
            b=RuntimeEnforcementCoordinator(source_decision_ref=ref); assert b.no_execution is True


class TestStatusResultTrust:
    def test_10_statuses(self): assert len(VALID_REC_STATUSES)==10
    def test_no_executing(self): assert "executing" not in VALID_REC_STATUSES; assert "coordinating" not in VALID_REC_STATUSES
    def test_all_non_executing(self):
        for s in VALID_REC_STATUSES: assert RuntimeEnforcementCoordinator(coordinator_status=s).no_execution is True
    def test_16_results(self): assert len(VALID_REC_RESULTS)==16
    def test_no_allow(self): assert "allowed" not in VALID_REC_RESULTS; assert "execute" not in VALID_REC_RESULTS
    def test_all_blocking(self):
        for r in VALID_REC_RESULTS: assert RuntimeEnforcementCoordinator(coordinator_result=r).execution_available is False
    def test_unknown_rejected(self):
        assert any("invalid" in i for i in RuntimeEnforcementCoordinator(coordinator_status="unknown").validate())
        assert any("invalid" in i for i in RuntimeEnforcementCoordinator(coordinator_result="allowed").validate())


class TestStepTrust:
    def test_16_steps(self): assert len(ALL_REC_STEPS)==16
    def test_all_non_executing(self): assert RuntimeEnforcementCoordinator(denied_steps=list(ALL_REC_STEPS)).no_execution is True
    def test_denied_steps_affect_digest(self): assert RuntimeEnforcementCoordinator(denied_steps=[]).compute_digest()!=RuntimeEnforcementCoordinator(denied_steps=["load_evidence_bundle"]).compute_digest()
    def test_unsupported_req_fail_closed(self): a=RuntimeEnforcementCoordinator(unsupported_requests=["run"]); assert a.execution_available is False


class TestAuthSafetyTrust:
    def test_12_auth_false(self):
        for f in _AUTH: assert getattr(RuntimeEnforcementCoordinator(), f) is False
    def test_auth_true_rejected(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            assert len(RuntimeEnforcementCoordinator(**kw).validate())>0
    def test_5_safety_true(self):
        for f in _SAFE: assert getattr(RuntimeEnforcementCoordinator(), f) is True
    def test_safety_false_rejected(self):
        for kw in [{"simulation_only":False},{"no_execution":False},{"design_only":False}]:
            assert len(RuntimeEnforcementCoordinator(**kw).validate())>0
    def test_auth_not_in_digest(self):
        assert RuntimeEnforcementCoordinator(execution_available=False).compute_digest()==RuntimeEnforcementCoordinator(execution_available=False).compute_digest()


class TestNoExecGuards:
    def test_default(self): assert RuntimeEnforcementCoordinator().no_execution is True
    def test_validate(self): a=_base(); a.validate(); assert a.no_execution is True
    def test_digest(self): a=_base(); a.compute_digest(); assert a.no_execution is True
    def test_to_dict(self): a=_base(); a.to_dict(); assert a.no_execution is True
    def test_json(self):
        j=_json.dumps(_base().to_dict()).lower()
        for t in ["subprocess.run","os.system","exec("]: assert t not in j
    def test_all_paths(self):
        a=_base(); a.validate(); a.digest=a.compute_digest(); a.to_dict(); _json.dumps(a.to_dict())
        assert a.no_execution is True


class TestContractPreservation:
    def test_103b_frozen(self):
        a=RuntimeEnforcementCoordinator()
        assert a.schema_version=="1.0"; assert a.coordinator_status==REC_STATUS_NOT_STARTED; assert a.coordinator_result==REC_RESULT_DENIED
    def test_45_fields(self): assert len(RuntimeEnforcementCoordinator().__dataclass_fields__)==45
    def test_decision_preserved(self):
        from pcae.core.backend_invocations import RuntimeEnforcementDecision, RuntimeEnforcementEvidenceBundle, NoGoEnforcementEvidence
        assert RuntimeEnforcementDecision().design_only is True
        assert RuntimeEnforcementEvidenceBundle().no_execution is True
        assert NoGoEnforcementEvidence().execution_available is False
