"""Tests for Phase 103B — Runtime Enforcement Coordinator Contract Freeze. Contract-freeze only. Non-executing."""
from __future__ import annotations
import json as _json, pytest
from pcae.core.backend_invocations import (
    RuntimeEnforcementCoordinator, VALID_REC_STATUSES, VALID_REC_RESULTS,
    ALL_REC_STEPS, REC_STATUS_NOT_STARTED, REC_RESULT_DENIED,
    REC_STATUS_UNAVAILABLE, REC_STATUS_BLOCKED, REC_STATUS_DENIED,
    REC_STATUS_FAIL_CLOSED, REC_STATUS_DESIGN_REVIEW,
    REC_RESULT_FAIL_CLOSED, REC_RESULT_EVIDENCE_ONLY, REC_RESULT_DESIGN_REVIEW,
)

_AUTH = ["execution_available","execution_authorized","backend_invocation_authorized","adapter_execution_authorized","network_authorized","subprocess_authorized","shell_authorized","mutation_authorized","apply_authorized","rollback_authorized","commit_authorized","push_authorized"]
_SAFE = ["simulation_only","no_execution","evidence_only","non_authorizing","design_only"]

REQUIRED = ["schema_version","coordinator_id","phase_id","task_id","generated_at_utc","source_evidence_bundle_ref","source_evidence_bundle_digest","source_decision_ref","source_decision_digest","coordinator_status","coordinator_result","coordinator_reason","requested_surface","evaluated_inputs","missing_inputs","stale_inputs","tampered_inputs","contradictory_inputs","triggered_no_go_conditions","denied_steps","blocked_steps","skipped_steps","future_only_steps","unsupported_requests","denial_reasons","fail_closed_reasons","warnings",*_AUTH,*_SAFE,"digest"]


class TestSchemaFreeze:
    def test_field_count(self): assert len(RuntimeEnforcementCoordinator().__dataclass_fields__) == 45
    def test_all_required_present(self):
        a = RuntimeEnforcementCoordinator()
        for f in REQUIRED: assert hasattr(a, f), f"Missing: {f}"
    def test_schema_version_stable(self): assert RuntimeEnforcementCoordinator().schema_version == "1.0"
    def test_default_status(self): assert RuntimeEnforcementCoordinator().coordinator_status == REC_STATUS_NOT_STARTED
    def test_default_result(self): assert RuntimeEnforcementCoordinator().coordinator_result == REC_RESULT_DENIED
    def test_all_auth_false(self):
        for f in _AUTH: assert getattr(RuntimeEnforcementCoordinator(), f) is False
    def test_all_safety_true(self):
        for f in _SAFE: assert getattr(RuntimeEnforcementCoordinator(), f) is True
    def test_to_dict_keys(self):
        d = RuntimeEnforcementCoordinator().to_dict()
        top = {"schema_version","coordinator_id","phase_id","task_id","generated_at_utc","source_evidence_bundle_ref","source_evidence_bundle_digest","source_decision_ref","source_decision_digest","coordinator_status","coordinator_result","coordinator_reason","requested_surface","evaluated_inputs","missing_inputs","stale_inputs","tampered_inputs","contradictory_inputs","triggered_no_go_conditions","denied_steps","blocked_steps","skipped_steps","future_only_steps","unsupported_requests","denial_reasons","fail_closed_reasons","warnings","authorization_summary","simulation_only","no_execution","evidence_only","non_authorizing","design_only","digest"}
        assert set(d.keys()) == top


class TestStatusFreeze:
    def test_10_statuses(self): assert len(VALID_REC_STATUSES) == 10
    def test_no_executing(self):
        for s in ("coordinating","enforcing","executing","running","authorized"): assert s not in VALID_REC_STATUSES
    def test_unknown_rejected(self): assert any("invalid coordinator_status" in i for i in RuntimeEnforcementCoordinator(coordinator_status="unknown").validate())
    def test_all_non_executing(self):
        for s in VALID_REC_STATUSES:
            assert RuntimeEnforcementCoordinator(coordinator_status=s).no_execution is True


class TestResultFreeze:
    def test_16_results(self): assert len(VALID_REC_RESULTS) == 16
    def test_no_allow(self):
        for t in ("allowed","authorized","execute","run","coordinate_execution"): assert t not in VALID_REC_RESULTS
    def test_unknown_rejected(self): assert any("invalid coordinator_result" in i for i in RuntimeEnforcementCoordinator(coordinator_result="allowed").validate())
    def test_all_blocking(self):
        for r in VALID_REC_RESULTS:
            assert RuntimeEnforcementCoordinator(coordinator_result=r).execution_available is False


class TestStepFreeze:
    def test_16_steps(self): assert len(ALL_REC_STEPS) == 16
    def test_steps_are_strings(self):
        for s in ALL_REC_STEPS: assert isinstance(s, str)


class TestFailClosedFreeze:
    def test_missing_bundle(self):
        a = RuntimeEnforcementCoordinator(source_evidence_bundle_ref="")
        assert a.execution_available is False
    def test_missing_decision(self):
        a = RuntimeEnforcementCoordinator(source_decision_ref="")
        assert a.execution_available is False
    def test_no_go_blocks(self):
        a = RuntimeEnforcementCoordinator(triggered_no_go_conditions=["X"])
        assert a.execution_available is False
    def test_auth_true_rejected(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            assert len(RuntimeEnforcementCoordinator(**kw).validate()) > 0
    def test_safety_false_rejected(self):
        for kw in [{"simulation_only":False},{"no_execution":False},{"design_only":False}]:
            assert len(RuntimeEnforcementCoordinator(**kw).validate()) > 0


class TestDigestFreeze:
    def test_sha256(self): assert len(RuntimeEnforcementCoordinator().compute_digest()) == 64
    def test_deterministic(self): assert RuntimeEnforcementCoordinator().compute_digest() == RuntimeEnforcementCoordinator().compute_digest()
    def test_changes_with_status(self):
        assert RuntimeEnforcementCoordinator(coordinator_status=REC_STATUS_NOT_STARTED).compute_digest() != RuntimeEnforcementCoordinator(coordinator_status=REC_STATUS_BLOCKED).compute_digest()
    def test_changes_with_bundle_ref(self):
        assert RuntimeEnforcementCoordinator(source_evidence_bundle_ref="a").compute_digest() != RuntimeEnforcementCoordinator(source_evidence_bundle_ref="b").compute_digest()
    def test_changes_with_decision_ref(self):
        assert RuntimeEnforcementCoordinator(source_decision_ref="a").compute_digest() != RuntimeEnforcementCoordinator(source_decision_ref="b").compute_digest()


class TestCompatibility:
    def test_current_schema_accepted(self): assert RuntimeEnforcementCoordinator().validate() == []
    def test_unknown_schema_rejected(self): assert any("unknown schema_version" in i for i in RuntimeEnforcementCoordinator(schema_version="99.0").validate())
    def test_unknown_status_rejected(self): assert any("invalid coordinator_status" in i for i in RuntimeEnforcementCoordinator(coordinator_status="executing").validate())
    def test_unknown_result_rejected(self): assert any("invalid coordinator_result" in i for i in RuntimeEnforcementCoordinator(coordinator_result="execute").validate())


class TestNoExec:
    def test_json_no_exec(self):
        j = _json.dumps(RuntimeEnforcementCoordinator().to_dict()).lower()
        for t in ["subprocess.run","os.system","exec("]: assert t not in j
    def test_all_paths(self):
        a = RuntimeEnforcementCoordinator(); a.validate(); a.digest = a.compute_digest(); a.to_dict();
        assert a.no_execution is True


class TestPreservation:
    def test_103a_preserved(self):
        a = RuntimeEnforcementCoordinator()
        assert a.design_only is True; assert a.coordinator_status == REC_STATUS_NOT_STARTED; assert a.coordinator_result == REC_RESULT_DENIED
    def test_decision_preserved(self):
        from pcae.core.backend_invocations import RuntimeEnforcementDecision, RuntimeEnforcementEvidenceBundle
        assert RuntimeEnforcementDecision().design_only is True
        assert RuntimeEnforcementEvidenceBundle().no_execution is True
