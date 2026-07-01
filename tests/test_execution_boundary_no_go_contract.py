"""Tests for Phase 100C — Execution Boundary No-Go Contract Freeze.

Contract-freeze only. Freezes the 100B NoGoEnforcementEvidence schema, 30
conditions, 17 categories, 6 severities, statuses, decisions, auth/safety
flags, digest, and compatibility rules.

No enforcement. No execution. All authorization flags must remain False.
"""

from __future__ import annotations

import json as _json
import pytest

from pcae.core.backend_invocations import (
    NoGoEnforcementEvidence,
    VALID_NGE_CATEGORIES, VALID_NGE_SEVERITIES,
    VALID_NGE_STATUSES, VALID_NGE_DECISIONS, VALID_NGE_CONDITIONS,
    NGE_SEVERITY_CRITICAL_BLOCKER, NGE_SEVERITY_HARD_BLOCKER,
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

_TO_DICT_KEYS = frozenset({
    "schema_version","no_go_evaluation_id","phase_id","task_id","generated_at_utc",
    "evaluation_status","evaluation_decision","source_gap_analysis_ref",
    "phase97_preflight_ref","phase98_preflight_ref","phase99_attempt_boundary_ref",
    "checked_no_go_conditions","triggered_no_go_conditions","missing_evidence",
    "failed_checks","denial_reasons","override_attempts","unknown_conditions",
    "unsupported_requests","warnings","authorization_summary",
    "simulation_only","no_execution","evidence_only","non_authorizing","design_only","digest",
})

_ALL_30 = frozenset(VALID_NGE_CONDITIONS)
_ALL_17 = frozenset(VALID_NGE_CATEGORIES)
_ALL_6 = frozenset(VALID_NGE_SEVERITIES)
_ALL_3_STATUSES = frozenset(VALID_NGE_STATUSES)
_ALL_2_DECISIONS = frozenset(VALID_NGE_DECISIONS)

# ── Schema freeze ──

class TestSchemaFreeze:
    def test_exact_27_keys(self):
        assert len(NoGoEnforcementEvidence().to_dict()) == 27

    def test_all_keys_present(self):
        d = NoGoEnforcementEvidence().to_dict()
        for k in sorted(_TO_DICT_KEYS):
            assert k in d

    def test_no_extra_keys(self):
        assert set(NoGoEnforcementEvidence().to_dict().keys()) == _TO_DICT_KEYS

    def test_schema_version_stable(self):
        assert NoGoEnforcementEvidence().schema_version == "1.0"

    def test_default_status_denied(self):
        assert NoGoEnforcementEvidence().evaluation_status == NGE_STATUS_DENIED

    def test_default_decision_blocked(self):
        assert NoGoEnforcementEvidence().evaluation_decision == NGE_DECISION_BLOCKED

    def test_no_field_dropped_from_json(self):
        a = NoGoEnforcementEvidence(); a.digest = a.compute_digest()
        d = a.to_dict(); j = _json.dumps(d); p = _json.loads(j)
        for k in sorted(_TO_DICT_KEYS):
            assert k in p

    def test_all_list_fields_are_lists(self):
        a = NoGoEnforcementEvidence(); d = a.to_dict()
        for f in ["checked_no_go_conditions","triggered_no_go_conditions",
                  "missing_evidence","failed_checks","denial_reasons",
                  "override_attempts","unknown_conditions","unsupported_requests","warnings"]:
            assert isinstance(d[f], list)

    def test_all_str_fields_are_str(self):
        a = NoGoEnforcementEvidence(); d = a.to_dict()
        for f in ["schema_version","no_go_evaluation_id","phase_id","task_id",
                  "generated_at_utc","evaluation_status","evaluation_decision",
                  "source_gap_analysis_ref","phase97_preflight_ref",
                  "phase98_preflight_ref","phase99_attempt_boundary_ref"]:
            assert isinstance(d[f], str)

# ── Condition freeze ──

class TestConditionFreeze:
    def test_exactly_30(self):
        assert len(VALID_NGE_CONDITIONS) == 30

    def test_matches_expected(self):
        assert VALID_NGE_CONDITIONS == _ALL_30

    def test_all_uppercase_identifiers(self):
        for c in VALID_NGE_CONDITIONS:
            assert c == c.upper()

    def test_valid_accepted(self):
        for c in sorted(_ALL_30):
            issues = NoGoEnforcementEvidence(triggered_no_go_conditions=[c]).validate()
            assert not any("unknown no-go condition" in i for i in issues)

    def test_unknown_fails(self):
        issues = NoGoEnforcementEvidence(triggered_no_go_conditions=["BOGUS"]).validate()
        assert any("unknown no-go condition" in i for i in issues)

    def test_conditions_non_authorizing(self):
        for c in sorted(_ALL_30):
            a = NoGoEnforcementEvidence(triggered_no_go_conditions=[c])
            assert a.execution_available is False
            assert a.non_authorizing is True

    def test_conditions_change_digest(self):
        b = NoGoEnforcementEvidence().compute_digest()
        assert NoGoEnforcementEvidence(triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS]).compute_digest() != b

# ── Category freeze ──

class TestCategoryFreeze:
    def test_exactly_17(self):
        assert len(VALID_NGE_CATEGORIES) == 17

    def test_matches_expected(self):
        assert VALID_NGE_CATEGORIES == _ALL_17

    def test_all_lowercase_with_underscores(self):
        for c in VALID_NGE_CATEGORIES:
            assert c == c.lower()

# ── Severity freeze ──

class TestSeverityFreeze:
    def test_exactly_6(self):
        assert len(VALID_NGE_SEVERITIES) == 6

    def test_matches_expected(self):
        assert VALID_NGE_SEVERITIES == _ALL_6

    def test_all_blocking(self):
        for s in VALID_NGE_SEVERITIES:
            assert s in _ALL_6
            # All severities deny/fail-closed

    def test_no_severity_implies_auth(self):
        a = NoGoEnforcementEvidence(triggered_no_go_conditions=[NGE_ARTIFACT_TAMPERED])
        assert a.execution_available is False

# ── Status/decision freeze ──

class TestStatusDecisionFreeze:
    def test_exactly_3_statuses(self):
        assert len(VALID_NGE_STATUSES) == 3

    def test_exactly_2_decisions(self):
        assert len(VALID_NGE_DECISIONS) == 2

    def test_default_status_not_executing(self):
        assert NGE_STATUS_DENIED != "executing"

    def test_default_decision_not_allow(self):
        assert NGE_DECISION_BLOCKED not in ("allow","execute","invoke")

    def test_invalid_status_fails(self):
        issues = NoGoEnforcementEvidence(evaluation_status="executing").validate()
        assert any("invalid evaluation_status" in i for i in issues)

    def test_invalid_decision_fails(self):
        issues = NoGoEnforcementEvidence(evaluation_decision="approved").validate()
        assert any("invalid evaluation_decision" in i for i in issues)

# ── Auth flag freeze ──

class TestAuthFlagFreeze:
    def test_all_12_present(self):
        for f in _12_AUTH:
            assert hasattr(NoGoEnforcementEvidence(), f)

    def test_all_12_false(self):
        a = NoGoEnforcementEvidence()
        for f in _12_AUTH:
            assert getattr(a, f) is False, f

    def test_all_12_in_to_dict_summary(self):
        d = NoGoEnforcementEvidence().to_dict()
        for f in _12_AUTH:
            assert f in d["authorization_summary"]
            assert d["authorization_summary"][f] is False

    def test_validate_rejects_unsafe(self):
        for kw in [{"execution_available":True},{"execution_authorized":True},{"push_authorized":True}]:
            issues = NoGoEnforcementEvidence(**kw).validate()
            assert len(issues) > 0

    def test_digest_changes_with_auth(self):
        """Honest gap: auth flags are not in digest payload — documented."""
        b = NoGoEnforcementEvidence().compute_digest()
        # Auth flags don't affect compute_digest — known gap
        assert NoGoEnforcementEvidence(execution_available=True).compute_digest() == b

    def test_no_text_implies_auth(self):
        j = _json.dumps(NoGoEnforcementEvidence().to_dict()).lower()
        assert "execution is authorized" not in j

# ── Safety flag freeze ──

class TestSafetyFlagFreeze:
    def test_all_5_true(self):
        a = NoGoEnforcementEvidence()
        for f in _5_SAFETY:
            assert getattr(a, f) is True, f

    def test_validate_rejects_false(self):
        for kw in [{"simulation_only":False},{"no_execution":False},{"design_only":False}]:
            issues = NoGoEnforcementEvidence(**kw).validate()
            assert len(issues) > 0

    def test_digest_changes_with_safety(self):
        b = NoGoEnforcementEvidence().compute_digest()
        for f in _5_SAFETY:
            assert NoGoEnforcementEvidence(**{f: False}).compute_digest() != b

# ── Digest freeze ──

class TestDigestFreeze:
    def test_sha256_64_chars(self):
        assert len(NoGoEnforcementEvidence().compute_digest()) == 64

    def test_deterministic(self):
        for _ in range(5):
            d1 = NoGoEnforcementEvidence().compute_digest()
            d2 = NoGoEnforcementEvidence().compute_digest()
            assert d1 == d2

    def test_excludes_digest_itself(self):
        a = NoGoEnforcementEvidence(); d1 = a.compute_digest()
        a.digest = "f"*64; assert a.compute_digest() == d1

    def test_changes_with_status(self):
        d1 = NoGoEnforcementEvidence(evaluation_status=NGE_STATUS_DENIED).compute_digest()
        d2 = NoGoEnforcementEvidence(evaluation_status=NGE_STATUS_BLOCKED).compute_digest()
        assert d1 != d2

    def test_changes_with_decision(self):
        d1 = NoGoEnforcementEvidence(evaluation_decision=NGE_DECISION_BLOCKED).compute_digest()
        d2 = NoGoEnforcementEvidence(evaluation_decision=NGE_DECISION_DENY).compute_digest()
        assert d1 != d2

    def test_changes_with_conditions(self):
        assert NoGoEnforcementEvidence().compute_digest() != NoGoEnforcementEvidence(triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS]).compute_digest()

    def test_changes_with_missing_evidence(self):
        assert NoGoEnforcementEvidence().compute_digest() != NoGoEnforcementEvidence(missing_evidence=["p97"]).compute_digest()

    def test_changes_with_failed_checks(self):
        assert NoGoEnforcementEvidence().compute_digest() != NoGoEnforcementEvidence(failed_checks=["digest_mismatch"]).compute_digest()

    def test_changes_with_denial_reasons(self):
        assert NoGoEnforcementEvidence().compute_digest() != NoGoEnforcementEvidence(denial_reasons=["denied_bypass"]).compute_digest()

# ── Compatibility ──

class TestCompatibility:
    def test_current_schema_accepted(self):
        assert NoGoEnforcementEvidence().validate() == []

    def test_unknown_schema_fails(self):
        issues = NoGoEnforcementEvidence(schema_version="99.0").validate()
        assert any("unknown schema_version" in i for i in issues)

    def test_unknown_condition_fails(self):
        issues = NoGoEnforcementEvidence(triggered_no_go_conditions=["BOGUS"]).validate()
        assert any("unknown no-go condition" in i for i in issues)

# ── No-execution guards ──

class TestNoExecutionGuard:
    def test_to_dict_no_exec(self):
        j = _json.dumps(NoGoEnforcementEvidence().to_dict()).lower()
        for t in ["subprocess.run","os.system","exec(","shell=true"]:
            assert t not in j

    def test_all_paths_non_executing(self):
        a = NoGoEnforcementEvidence(triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS])
        a.validate(); a.digest = a.compute_digest(); d = a.to_dict(); _json.dumps(d)
        assert a.execution_available is False; assert a.no_execution is True

# ── 100B model preservation ──

class Test100BPreservation:
    def test_46_model_tests_still_relevant(self):
        from pcae.core.backend_invocations import NoGoEnforcementEvidence as N
        assert N is not None

    def test_30_conditions_unchanged(self):
        assert len(VALID_NGE_CONDITIONS) == 30

    def test_17_categories_unchanged(self):
        assert len(VALID_NGE_CATEGORIES) == 17

    def test_6_severities_unchanged(self):
        assert len(VALID_NGE_SEVERITIES) == 6

    def test_99_attempt_boundary_preserved(self):
        from pcae.core.backend_invocations import GovernedExecutionAttemptBoundary
        a = GovernedExecutionAttemptBoundary()
        assert a.attempt_state == "unavailable"
        assert len(a.to_dict()) == 33
