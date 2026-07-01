"""Tests for Phase 101D — Runtime Enforcement Evidence Bundle Artifact Trust Hardening. Test-only. No enforcement. No execution."""
from __future__ import annotations
import json as _json, pytest
from pcae.core.backend_invocations import (
    RuntimeEnforcementEvidenceBundle, VALID_REEB_STATUSES, VALID_REEB_DECISIONS,
    REEB_STATUS_NOT_COLLECTED, REEB_STATUS_BLOCKED_BY_NO_GO,
    REEB_DECISION_DENIED, REEB_DECISION_BLOCKED,
)
_AUTH=["execution_available","execution_authorized","backend_invocation_authorized","adapter_execution_authorized","network_authorized","subprocess_authorized","shell_authorized","mutation_authorized","apply_authorized","rollback_authorized","commit_authorized","push_authorized"]
_SAFE=["simulation_only","no_execution","evidence_only","non_authorizing","design_only"]

def _dg(**kw): return RuntimeEnforcementEvidenceBundle(**kw).compute_digest()

# ── 1. Digest ──
class TestDigest:
    def test_sha256(self): assert len(_dg())==64
    def test_deterministic(self):
        for _ in range(10): assert _dg(bundle_status=REEB_STATUS_BLOCKED_BY_NO_GO)==_dg(bundle_status=REEB_STATUS_BLOCKED_BY_NO_GO)
    def test_excludes_digest(self):
        a=RuntimeEnforcementEvidenceBundle(); d1=a.compute_digest(); a.digest="f"*64; assert a.compute_digest()==d1
    # Identity
    def test_schema(self): assert _dg(schema_version="1.0")!=_dg(schema_version="2.0")
    def test_bundle_id(self): assert _dg()!=_dg(evidence_bundle_id="b1")
    def test_phase_id(self): assert _dg(phase_id="101B")!=_dg(phase_id="101C")
    def test_task_id(self): assert _dg()!=_dg(task_id="t1")
    def test_utc(self): assert _dg()!=_dg(generated_at_utc="2026-01-01")
    # Status/decision
    def test_status(self): assert _dg(bundle_status=REEB_STATUS_NOT_COLLECTED)!=_dg(bundle_status=REEB_STATUS_BLOCKED_BY_NO_GO)
    def test_decision(self): assert _dg(bundle_decision=REEB_DECISION_DENIED)!=_dg(bundle_decision=REEB_DECISION_BLOCKED)
    # Lists
    def test_required(self): assert _dg()!=_dg(required_evidence=["p97"])
    def test_missing(self): assert _dg()!=_dg(missing_required_evidence=["approval"])
    def test_refs(self): assert _dg()!=_dg(evidence_refs=["ref1"])
    def test_edigests(self): assert _dg()!=_dg(evidence_digests=["abc"])
    def test_nogo(self): assert _dg()!=_dg(no_go_conditions=["BYPASS"])
    def test_denial(self): assert _dg()!=_dg(denial_reasons=["denied"])
    def test_failclosed(self): assert _dg()!=_dg(fail_closed_reasons=["fc1"])
    def test_warnings(self): assert _dg()!=_dg(warnings=["w1"])
    # Safety
    def test_safety(self):
        b=_dg()
        for f in _SAFE: assert _dg(**{f:False})!=b
    # Honest gaps
    def test_refs_not_in_digest(self):
        b=_dg()
        for f in ["approval_ref","audit_readiness_ref","rollback_readiness_ref","report_trust_ref","notification_trust_ref","no_go_evidence_ref","no_go_evidence_digest"]:
            assert _dg(**{f:"x"})==b
    def test_auth_not_in_digest(self):
        b=_dg()
        for f in _AUTH: assert _dg(**{f:True})==b

# ── 2. Tamper ──
class TestTamper:
    def _t(self,**kw):
        a=RuntimeEnforcementEvidenceBundle(); a.digest=a.compute_digest(); s=a.digest
        for f,v in kw.items(): setattr(a,f,v)
        assert a.compute_digest()!=s
    def test_schema(self): self._t(schema_version="99.0")
    def test_bundle_id(self): self._t(evidence_bundle_id="tampered")
    def test_phase_id(self): self._t(phase_id="99X")
    def test_task_id(self): self._t(task_id="tampered")
    def test_utc(self): self._t(generated_at_utc="2060-01-01")
    def test_status(self): self._t(bundle_status=REEB_STATUS_BLOCKED_BY_NO_GO)
    def test_decision(self): self._t(bundle_decision=REEB_DECISION_BLOCKED)
    def test_required(self): self._t(required_evidence=["tampered"])
    def test_missing(self): self._t(missing_required_evidence=["tampered"])
    def test_refs(self): self._t(evidence_refs=["tampered"])
    def test_edigests(self): self._t(evidence_digests=["tampered"])
    def test_nogo(self): self._t(no_go_conditions=["TAMPERED"])
    def test_denial(self): self._t(denial_reasons=["tampered"])
    def test_failclosed(self): self._t(fail_closed_reasons=["tampered"])
    def test_warnings(self): self._t(warnings=["tampered"])
    def test_safety(self):
        for f in _SAFE: self._t(**{f:False})
    def test_digest_mismatch(self):
        a=RuntimeEnforcementEvidenceBundle(bundle_status=REEB_STATUS_NOT_COLLECTED)
        a.digest=a.compute_digest(); s=a.digest; a.bundle_status=REEB_STATUS_BLOCKED_BY_NO_GO
        assert a.compute_digest()!=s
    def test_tampering_never_executes(self):
        a=RuntimeEnforcementEvidenceBundle(execution_available=True)
        assert a.no_execution is True; assert a.non_authorizing is True

# ── 3. Evidence trust ──
class TestEvidenceTrust:
    def test_missing_fail_closed(self):
        a=RuntimeEnforcementEvidenceBundle(missing_required_evidence=["phase97_preflight"])
        assert a.execution_available is False; assert a.no_execution is True
    def test_required_never_auth(self):
        a=RuntimeEnforcementEvidenceBundle(required_evidence=["phase97"])
        assert a.execution_available is False
    def test_no_go_blocker(self):
        a=RuntimeEnforcementEvidenceBundle(no_go_conditions=["BYPASS_PERMISSIONS"])
        assert a.execution_available is False

# ── 4. Status/decision ──
class TestStatusDecision:
    def test_9_statuses(self): assert len(VALID_REEB_STATUSES)==9
    def test_5_decisions(self): assert len(VALID_REEB_DECISIONS)==5
    def test_no_status_executing(self): assert "executing" not in VALID_REEB_STATUSES
    def test_no_decision_allow(self):
        for t in ("allow","execute","run","invoke","apply","commit","push"): assert t not in VALID_REEB_DECISIONS

# ── 5. Auth/safety ──
class TestAuthSafety:
    def test_all_12_false(self):
        a=RuntimeEnforcementEvidenceBundle()
        for f in _AUTH: assert getattr(a, f) is False
    def test_all_5_true(self):
        a=RuntimeEnforcementEvidenceBundle()
        for f in _SAFE: assert getattr(a, f) is True
    def test_validate_rejects(self):
        for kw in [{"execution_available":True},{"simulation_only":False}]:
            assert len(RuntimeEnforcementEvidenceBundle(**kw).validate())>0
    def test_json_no_auth(self):
        j=_json.dumps(RuntimeEnforcementEvidenceBundle().to_dict()).lower()
        assert "execution is authorized" not in j

# ── 6. References ──
class TestReferences:
    def test_refs_strings_never_executed(self):
        a=RuntimeEnforcementEvidenceBundle(
            evidence_refs=["../escape","file://etc/shadow","$(curl evil)"])
        assert a.no_execution is True; assert a.execution_available is False

# ── 7. No-execution ──
class TestNoExec:
    def test_json_clean(self):
        j=_json.dumps(RuntimeEnforcementEvidenceBundle().to_dict()).lower()
        for t in ["subprocess.run","os.system","exec(","shell=true"]: assert t not in j
    def test_all_paths(self):
        a=RuntimeEnforcementEvidenceBundle(missing_required_evidence=["p97"])
        a.validate(); a.digest=a.compute_digest(); d=a.to_dict(); _json.dumps(d)
        assert a.no_execution is True

# ── 8. Contract preservation ──
class TestPreservation:
    def test_29_fields(self): assert len(RuntimeEnforcementEvidenceBundle().to_dict())==29
    def test_9_statuses(self): assert len(VALID_REEB_STATUSES)==9
    def test_5_decisions(self): assert len(VALID_REEB_DECISIONS)==5
    def test_all_12_false(self):
        a=RuntimeEnforcementEvidenceBundle()
        for f in _AUTH: assert getattr(a, f) is False
    def test_all_5_true(self):
        a=RuntimeEnforcementEvidenceBundle()
        for f in _SAFE: assert getattr(a, f) is True
    def test_sha256(self): assert len(_dg())==64
    def test_phase99(self):
        from pcae.core.backend_invocations import GovernedExecutionAttemptBoundary
        a=GovernedExecutionAttemptBoundary()
        assert a.attempt_state=="unavailable"; assert len(a.to_dict())==33
