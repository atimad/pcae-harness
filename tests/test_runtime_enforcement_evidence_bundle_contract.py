"""Tests for Phase 101B — Runtime Enforcement Evidence Bundle Contract Design. Design-only. Non-executing. Non-authorizing."""
from __future__ import annotations
import json as _json, pytest
from pcae.core.backend_invocations import (
    RuntimeEnforcementEvidenceBundle, VALID_REEB_STATUSES, VALID_REEB_DECISIONS,
    REEB_STATUS_NOT_COLLECTED, REEB_DECISION_DENIED,
)
_AUTH = ["execution_available","execution_authorized","backend_invocation_authorized","adapter_execution_authorized","network_authorized","subprocess_authorized","shell_authorized","mutation_authorized","apply_authorized","rollback_authorized","commit_authorized","push_authorized"]
_SAFE = ["simulation_only","no_execution","evidence_only","non_authorizing","design_only"]

class TestDesignOnly:
    def test_design_only_true(self): assert RuntimeEnforcementEvidenceBundle().design_only is True
    def test_all_12_auth_false(self):
        a = RuntimeEnforcementEvidenceBundle()
        for f in _AUTH: assert getattr(a, f) is False
    def test_all_5_safety_true(self):
        a = RuntimeEnforcementEvidenceBundle()
        for f in _SAFE: assert getattr(a, f) is True
    def test_default_status_not_collected(self): assert RuntimeEnforcementEvidenceBundle().bundle_status == REEB_STATUS_NOT_COLLECTED
    def test_default_decision_denied(self): assert RuntimeEnforcementEvidenceBundle().bundle_decision == REEB_DECISION_DENIED
    def test_9_statuses(self): assert len(VALID_REEB_STATUSES) == 9
    def test_5_decisions(self): assert len(VALID_REEB_DECISIONS) == 5
    def test_no_status_means_executing(self): assert "executing" not in VALID_REEB_STATUSES
    def test_no_decision_permits_execution(self):
        for t in ("allow","execute","run","invoke","apply","commit","push"): assert t not in VALID_REEB_DECISIONS

class TestValidation:
    def test_default_passes(self): assert RuntimeEnforcementEvidenceBundle().validate() == []
    def test_rejects_unknown_schema(self):
        issues = RuntimeEnforcementEvidenceBundle(schema_version="99.0").validate()
        assert any("unknown schema_version" in i for i in issues)
    def test_rejects_invalid_status(self):
        issues = RuntimeEnforcementEvidenceBundle(bundle_status="executing").validate()
        assert any("invalid bundle_status" in i for i in issues)
    def test_rejects_invalid_decision(self):
        issues = RuntimeEnforcementEvidenceBundle(bundle_decision="approved").validate()
        assert any("invalid bundle_decision" in i for i in issues)
    def test_rejects_unsafe_auth(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            assert len(RuntimeEnforcementEvidenceBundle(**kw).validate()) > 0
    def test_rejects_unsafe_safety(self):
        for kw in [{"simulation_only":False},{"no_execution":False},{"design_only":False}]:
            assert len(RuntimeEnforcementEvidenceBundle(**kw).validate()) > 0

class TestDigest:
    def test_sha256_64(self): assert len(RuntimeEnforcementEvidenceBundle().compute_digest()) == 64
    def test_deterministic(self):
        d1 = RuntimeEnforcementEvidenceBundle().compute_digest()
        d2 = RuntimeEnforcementEvidenceBundle().compute_digest()
        assert d1 == d2
    def test_changes_with_status(self):
        d1 = RuntimeEnforcementEvidenceBundle(bundle_status=REEB_STATUS_NOT_COLLECTED).compute_digest()
        d2 = RuntimeEnforcementEvidenceBundle(bundle_status="blocked_by_no_go").compute_digest()
        assert d1 != d2

class TestFailClosed:
    def test_missing_evidence_fail_closed(self):
        a = RuntimeEnforcementEvidenceBundle(missing_required_evidence=["phase97"])
        assert a.execution_available is False; assert a.no_execution is True
    def test_no_go_condition_fail_closed(self):
        a = RuntimeEnforcementEvidenceBundle(no_go_conditions=["BYPASS_PERMISSIONS"])
        assert a.execution_available is False

class TestNoExec:
    def test_to_dict_no_exec(self):
        j = _json.dumps(RuntimeEnforcementEvidenceBundle().to_dict()).lower()
        for t in ["subprocess.run","os.system","exec("]: assert t not in j
    def test_all_paths(self):
        a = RuntimeEnforcementEvidenceBundle(); a.validate(); a.digest = a.compute_digest(); d = a.to_dict(); _json.dumps(d)
        assert a.no_execution is True
