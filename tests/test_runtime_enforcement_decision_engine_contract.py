"""Tests for Phase 102A — Runtime Enforcement Decision Engine Contract Design. Design-only. Non-executing."""
from __future__ import annotations
import json as _json, pytest
from pcae.core.backend_invocations import (
    RuntimeEnforcementDecision, VALID_RED_STATUSES, VALID_RED_RESULTS,
    RED_STATUS_NOT_EVALUATED, RED_RESULT_DENIED,
)
_AUTH=["execution_available","execution_authorized","backend_invocation_authorized","adapter_execution_authorized","network_authorized","subprocess_authorized","shell_authorized","mutation_authorized","apply_authorized","rollback_authorized","commit_authorized","push_authorized"]
_SAFE=["simulation_only","no_execution","evidence_only","non_authorizing","design_only"]

class TestDesignOnly:
    def test_design_only_true(self): assert RuntimeEnforcementDecision().design_only is True
    def test_all_12_auth_false(self):
        a = RuntimeEnforcementDecision()
        for f in _AUTH: assert getattr(a, f) is False
    def test_all_5_safety_true(self):
        a = RuntimeEnforcementDecision()
        for f in _SAFE: assert getattr(a, f) is True
    def test_default_status(self): assert RuntimeEnforcementDecision().decision_status == RED_STATUS_NOT_EVALUATED
    def test_default_result(self): assert RuntimeEnforcementDecision().decision_result == RED_RESULT_DENIED
    def test_9_statuses(self): assert len(VALID_RED_STATUSES) == 9
    def test_12_results(self): assert len(VALID_RED_RESULTS) == 12
    def test_no_status_executing(self): assert "executing" not in VALID_RED_STATUSES
    def test_no_result_allow(self):
        for t in ("allowed","authorized","execute","run","invoke","apply","commit","push"): assert t not in VALID_RED_RESULTS

class TestValidation:
    def test_default_passes(self): assert RuntimeEnforcementDecision().validate() == []
    def test_rejects_unknown_schema(self):
        issues = RuntimeEnforcementDecision(schema_version="99.0").validate()
        assert any("unknown schema_version" in i for i in issues)
    def test_rejects_invalid_status(self):
        issues = RuntimeEnforcementDecision(decision_status="executing").validate()
        assert any("invalid decision_status" in i for i in issues)
    def test_rejects_invalid_result(self):
        issues = RuntimeEnforcementDecision(decision_result="allowed").validate()
        assert any("invalid decision_result" in i for i in issues)
    def test_rejects_unsafe_auth(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            assert len(RuntimeEnforcementDecision(**kw).validate()) > 0

class TestDigest:
    def test_sha256(self): assert len(RuntimeEnforcementDecision().compute_digest()) == 64
    def test_deterministic(self):
        d1 = RuntimeEnforcementDecision().compute_digest()
        d2 = RuntimeEnforcementDecision().compute_digest()
        assert d1 == d2
    def test_changes_with_status(self):
        d1 = RuntimeEnforcementDecision(decision_status=RED_STATUS_NOT_EVALUATED).compute_digest()
        d2 = RuntimeEnforcementDecision(decision_status="blocked").compute_digest()
        assert d1 != d2

class TestFailClosed:
    def test_missing_bundle_fail_closed(self):
        a = RuntimeEnforcementDecision(missing_inputs=["evidence_bundle"])
        assert a.execution_available is False; assert a.no_execution is True
    def test_no_go_blocks(self):
        a = RuntimeEnforcementDecision(triggered_no_go_conditions=["BYPASS_PERMISSIONS"])
        assert a.execution_available is False

class TestNoExec:
    def test_json_no_exec(self):
        j = _json.dumps(RuntimeEnforcementDecision().to_dict()).lower()
        for t in ["subprocess.run","os.system","exec("]: assert t not in j
    def test_all_paths(self):
        a = RuntimeEnforcementDecision(missing_inputs=["bundle"]); a.validate(); a.digest = a.compute_digest(); d = a.to_dict(); _json.dumps(d)
        assert a.no_execution is True

class TestPreservation:
    def test_700_combined(self):
        from pcae.core.backend_invocations import GovernedExecutionAttemptBoundary, NoGoEnforcementEvidence, RuntimeEnforcementEvidenceBundle
        assert GovernedExecutionAttemptBoundary().attempt_state == "unavailable"
        assert NoGoEnforcementEvidence().execution_available is False
        assert RuntimeEnforcementEvidenceBundle().no_execution is True
