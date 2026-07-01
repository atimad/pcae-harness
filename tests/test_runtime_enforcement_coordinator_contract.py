"""Tests for Phase 103A — Runtime Enforcement Coordinator Contract Design. Design-only. Non-executing."""
from __future__ import annotations
import json as _json, pytest
from pcae.core.backend_invocations import (
    RuntimeEnforcementCoordinator, VALID_REC_STATUSES, VALID_REC_RESULTS,
    ALL_REC_STEPS, REC_STATUS_NOT_STARTED, REC_RESULT_DENIED,
)

_AUTH = ["execution_available","execution_authorized","backend_invocation_authorized","adapter_execution_authorized","network_authorized","subprocess_authorized","shell_authorized","mutation_authorized","apply_authorized","rollback_authorized","commit_authorized","push_authorized"]
_SAFE = ["simulation_only","no_execution","evidence_only","non_authorizing","design_only"]


class TestDesignOnly:
    def test_design_only_true(self): assert RuntimeEnforcementCoordinator().design_only is True
    def test_all_12_auth_false(self):
        a = RuntimeEnforcementCoordinator()
        for f in _AUTH: assert getattr(a, f) is False
    def test_all_5_safety_true(self):
        a = RuntimeEnforcementCoordinator()
        for f in _SAFE: assert getattr(a, f) is True
    def test_default_status(self): assert RuntimeEnforcementCoordinator().coordinator_status == REC_STATUS_NOT_STARTED
    def test_default_result(self): assert RuntimeEnforcementCoordinator().coordinator_result == REC_RESULT_DENIED
    def test_10_statuses(self): assert len(VALID_REC_STATUSES) == 10
    def test_16_results(self): assert len(VALID_REC_RESULTS) == 16
    def test_16_steps(self): assert len(ALL_REC_STEPS) == 16
    def test_no_status_enforcing(self):
        for s in ("coordinating","enforcing","executing","running","invoking_backend","running_adapter","applying","rolling_back","committing","pushing"):
            assert s not in VALID_REC_STATUSES
    def test_no_result_allow(self):
        for t in ("allowed","authorized","execute","run","coordinate_execution","invoke_backend","run_adapter","apply_patch","rollback","commit","push"):
            assert t not in VALID_REC_RESULTS


class TestValidation:
    def test_default_passes(self): assert RuntimeEnforcementCoordinator().validate() == []
    def test_rejects_unknown_schema(self):
        issues = RuntimeEnforcementCoordinator(schema_version="99.0").validate()
        assert any("unknown schema_version" in i for i in issues)
    def test_rejects_invalid_status(self):
        issues = RuntimeEnforcementCoordinator(coordinator_status="executing").validate()
        assert any("invalid coordinator_status" in i for i in issues)
    def test_rejects_invalid_result(self):
        issues = RuntimeEnforcementCoordinator(coordinator_result="allowed").validate()
        assert any("invalid coordinator_result" in i for i in issues)
    def test_rejects_unsafe_auth(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            assert len(RuntimeEnforcementCoordinator(**kw).validate()) > 0


class TestDigest:
    def test_sha256(self): assert len(RuntimeEnforcementCoordinator().compute_digest()) == 64
    def test_deterministic(self):
        assert RuntimeEnforcementCoordinator().compute_digest() == RuntimeEnforcementCoordinator().compute_digest()
    def test_changes_with_status(self):
        d1 = RuntimeEnforcementCoordinator(coordinator_status=REC_STATUS_NOT_STARTED).compute_digest()
        d2 = RuntimeEnforcementCoordinator(coordinator_status="blocked").compute_digest()
        assert d1 != d2


class TestFailClosed:
    def test_missing_bundle_fail_closed(self):
        a = RuntimeEnforcementCoordinator(missing_inputs=["evidence_bundle"])
        assert a.execution_available is False; assert a.no_execution is True
    def test_missing_decision_fail_closed(self):
        a = RuntimeEnforcementCoordinator(missing_inputs=["decision_artifact"])
        assert a.execution_available is False
    def test_no_go_blocks(self):
        a = RuntimeEnforcementCoordinator(triggered_no_go_conditions=["BYPASS"])
        assert a.execution_available is False
    def test_bundle_digest_mismatch_blocks(self):
        a = RuntimeEnforcementCoordinator(source_evidence_bundle_ref="b1", source_evidence_bundle_digest="bad")
        assert a.no_execution is True
    def test_denied_steps_preserved(self):
        a = RuntimeEnforcementCoordinator(denied_steps=["load_evidence_bundle"])
        assert a.no_execution is True


class TestNoExec:
    def test_json_no_exec(self):
        j = _json.dumps(RuntimeEnforcementCoordinator().to_dict()).lower()
        for t in ["subprocess.run","os.system","exec("]: assert t not in j
    def test_all_paths(self):
        a = RuntimeEnforcementCoordinator(missing_inputs=["bundle"]); a.validate(); a.digest = a.compute_digest(); d = a.to_dict(); _json.dumps(d)
        assert a.no_execution is True


class TestPreservation:
    def test_decision_model_preserved(self):
        from pcae.core.backend_invocations import RuntimeEnforcementDecision, RuntimeEnforcementEvidenceBundle, NoGoEnforcementEvidence, GovernedExecutionAttemptBoundary
        assert RuntimeEnforcementDecision().design_only is True
        assert RuntimeEnforcementEvidenceBundle().no_execution is True
        assert NoGoEnforcementEvidence().execution_available is False
        assert GovernedExecutionAttemptBoundary().attempt_state == "unavailable"
