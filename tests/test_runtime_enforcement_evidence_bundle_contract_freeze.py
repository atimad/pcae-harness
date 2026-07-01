"""Tests for Phase 101C — Runtime Enforcement Evidence Bundle Contract Freeze. Contract-freeze only. No enforcement. No execution."""
from __future__ import annotations
import json as _json, pytest
from pcae.core.backend_invocations import (
    RuntimeEnforcementEvidenceBundle, VALID_REEB_STATUSES, VALID_REEB_DECISIONS,
    REEB_STATUS_NOT_COLLECTED, REEB_STATUS_BLOCKED_BY_NO_GO, REEB_DECISION_DENIED, REEB_DECISION_BLOCKED,
)
_AUTH=["execution_available","execution_authorized","backend_invocation_authorized","adapter_execution_authorized","network_authorized","subprocess_authorized","shell_authorized","mutation_authorized","apply_authorized","rollback_authorized","commit_authorized","push_authorized"]
_SAFE=["simulation_only","no_execution","evidence_only","non_authorizing","design_only"]

_TO_DICT_KEYS=frozenset({"schema_version","evidence_bundle_id","phase_id","task_id","generated_at_utc","bundle_status","bundle_decision","required_evidence","missing_required_evidence","evidence_refs","evidence_digests","no_go_evidence_ref","no_go_evidence_digest","no_go_conditions","approval_ref","audit_readiness_ref","rollback_readiness_ref","report_trust_ref","notification_trust_ref","denial_reasons","fail_closed_reasons","warnings","authorization_summary","simulation_only","no_execution","evidence_only","non_authorizing","design_only","digest"})

def _dg(**kw): return RuntimeEnforcementEvidenceBundle(**kw).compute_digest()

# ── Schema freeze ──
class TestSchemaFreeze:
    def test_29_keys(self): assert len(RuntimeEnforcementEvidenceBundle().to_dict()) == 29
    def test_all_keys_present(self):
        d = RuntimeEnforcementEvidenceBundle().to_dict()
        for k in sorted(_TO_DICT_KEYS): assert k in d
    def test_schema_version_stable(self): assert RuntimeEnforcementEvidenceBundle().schema_version == "1.0"
    def test_default_status(self): assert RuntimeEnforcementEvidenceBundle().bundle_status == REEB_STATUS_NOT_COLLECTED
    def test_default_decision(self): assert RuntimeEnforcementEvidenceBundle().bundle_decision == REEB_DECISION_DENIED
    def test_all_list_fields_are_lists(self):
        d = RuntimeEnforcementEvidenceBundle().to_dict()
        for f in ["required_evidence","missing_required_evidence","evidence_refs","evidence_digests","no_go_conditions","denial_reasons","fail_closed_reasons","warnings"]:
            assert isinstance(d[f], list)
    def test_no_field_dropped(self):
        a = RuntimeEnforcementEvidenceBundle(); a.digest = a.compute_digest()
        d = a.to_dict(); p = _json.loads(_json.dumps(d))
        for k in sorted(_TO_DICT_KEYS): assert k in p

# ── Status/decision freeze ──
class TestStatusDecisionFreeze:
    def test_9_statuses(self): assert len(VALID_REEB_STATUSES) == 9
    def test_5_decisions(self): assert len(VALID_REEB_DECISIONS) == 5
    def test_no_status_executing(self): assert "executing" not in VALID_REEB_STATUSES
    def test_no_decision_allow(self):
        for t in ("allow","execute","run","invoke","apply","commit","push"): assert t not in VALID_REEB_DECISIONS
    def test_unknown_status_fails(self):
        issues = RuntimeEnforcementEvidenceBundle(bundle_status="executing").validate()
        assert any("invalid bundle_status" in i for i in issues)
    def test_unknown_decision_fails(self):
        issues = RuntimeEnforcementEvidenceBundle(bundle_decision="approved").validate()
        assert any("invalid bundle_decision" in i for i in issues)

# ── Auth/safety flag freeze ──
class TestAuthSafetyFreeze:
    def test_all_12_false(self):
        a = RuntimeEnforcementEvidenceBundle()
        for f in _AUTH: assert getattr(a, f) is False
    def test_all_5_true(self):
        a = RuntimeEnforcementEvidenceBundle()
        for f in _SAFE: assert getattr(a, f) is True
    def test_validate_rejects_unsafe_auth(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            assert len(RuntimeEnforcementEvidenceBundle(**kw).validate()) > 0
    def test_validate_rejects_unsafe_safety(self):
        for kw in [{"simulation_only":False},{"no_execution":False},{"design_only":False}]:
            assert len(RuntimeEnforcementEvidenceBundle(**kw).validate()) > 0

# ── Digest freeze ──
class TestDigestFreeze:
    def test_sha256_64(self): assert len(_dg()) == 64
    def test_deterministic(self):
        for _ in range(5): assert _dg(bundle_status=REEB_STATUS_BLOCKED_BY_NO_GO) == _dg(bundle_status=REEB_STATUS_BLOCKED_BY_NO_GO)
    def test_excludes_digest_itself(self):
        a = RuntimeEnforcementEvidenceBundle(); d1 = a.compute_digest(); a.digest = "f"*64; assert a.compute_digest() == d1
    def test_status(self): assert _dg(bundle_status=REEB_STATUS_NOT_COLLECTED) != _dg(bundle_status=REEB_STATUS_BLOCKED_BY_NO_GO)
    def test_decision(self): assert _dg(bundle_decision=REEB_DECISION_DENIED) != _dg(bundle_decision=REEB_DECISION_BLOCKED)
    def test_required_evidence(self): assert _dg() != _dg(required_evidence=["phase97"])
    def test_missing_required(self): assert _dg() != _dg(missing_required_evidence=["approval"])
    def test_no_go_conditions(self): assert _dg() != _dg(no_go_conditions=["BYPASS"])
    def test_safety_flags(self):
        b = _dg()
        for f in _SAFE: assert _dg(**{f: False}) != b
    def test_auth_not_in_digest(self):
        b = _dg()
        for f in _AUTH: assert _dg(**{f: True}) == b

# ── Compatibility ──
class TestCompatibility:
    def test_current_schema_ok(self): assert RuntimeEnforcementEvidenceBundle().validate() == []
    def test_unknown_schema_fails(self):
        issues = RuntimeEnforcementEvidenceBundle(schema_version="99.0").validate()
        assert any("unknown schema_version" in i for i in issues)

# ── No-execution ──
class TestNoExec:
    def test_json_no_exec(self):
        j = _json.dumps(RuntimeEnforcementEvidenceBundle().to_dict()).lower()
        for t in ["subprocess.run","os.system","exec(","shell=true"]: assert t not in j
    def test_all_paths(self):
        a = RuntimeEnforcementEvidenceBundle(missing_required_evidence=["p97"]); a.validate(); a.digest = a.compute_digest(); d = a.to_dict(); _json.dumps(d)
        assert a.no_execution is True; assert a.execution_available is False

# ── 101B preservation ──
class Test101BPreservation:
    def test_9_statuses(self): assert len(VALID_REEB_STATUSES) == 9
    def test_5_decisions(self): assert len(VALID_REEB_DECISIONS) == 5
    def test_29_fields(self): assert len(RuntimeEnforcementEvidenceBundle().to_dict()) == 29
    def test_99_preserved(self):
        from pcae.core.backend_invocations import GovernedExecutionAttemptBoundary
        a = GovernedExecutionAttemptBoundary()
        assert a.attempt_state == "unavailable"
        assert len(a.to_dict()) == 33
