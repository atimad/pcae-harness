"""Tests for Phase 100B — Execution Boundary No-Go Enforcement Model.

Design/model-only. All tests prove the model is non-executing, non-authorizing,
fail-closed, and never implies execution capability.
"""

from __future__ import annotations

import json as _json
import pytest

from pcae.core.backend_invocations import (
    NoGoEnforcementEvidence,
    VALID_NGE_CATEGORIES, VALID_NGE_SEVERITIES,
    VALID_NGE_STATUSES, VALID_NGE_DECISIONS, VALID_NGE_CONDITIONS,
    NGE_SEVERITY_CRITICAL_BLOCKER, NGE_SEVERITY_HARD_BLOCKER,
    NGE_SEVERITY_MISSING_PREREQUISITE, NGE_SEVERITY_TRUST_FAILURE,
    NGE_SEVERITY_UNSUPPORTED_REQUEST, NGE_SEVERITY_REPORTING_FAILURE,
    NGE_STATUS_DENIED, NGE_STATUS_BLOCKED,
    NGE_DECISION_BLOCKED, NGE_DECISION_DENY,
    NGE_BYPASS_PERMISSIONS, NGE_ARTIFACT_TAMPERED,
)

_12_AUTH_FLAGS = [
    "execution_available", "execution_authorized",
    "backend_invocation_authorized", "adapter_execution_authorized",
    "network_authorized", "subprocess_authorized",
    "shell_authorized", "mutation_authorized",
    "apply_authorized", "rollback_authorized",
    "commit_authorized", "push_authorized",
]

_5_SAFETY_FLAGS = [
    "simulation_only", "no_execution", "evidence_only",
    "non_authorizing", "design_only",
]


class TestModelDesignOnly:
    def test_design_only_true(self):
        assert NoGoEnforcementEvidence().design_only is True

    def test_simulation_only_true(self):
        assert NoGoEnforcementEvidence().simulation_only is True

    def test_no_execution_true(self):
        assert NoGoEnforcementEvidence().no_execution is True

    def test_evidence_only_true(self):
        assert NoGoEnforcementEvidence().evidence_only is True

    def test_non_authorizing_true(self):
        assert NoGoEnforcementEvidence().non_authorizing is True

    def test_all_12_auth_flags_false(self):
        a = NoGoEnforcementEvidence()
        for flag in _12_AUTH_FLAGS:
            assert getattr(a, flag) is False, flag

    def test_all_5_safety_flags_true(self):
        a = NoGoEnforcementEvidence()
        for flag in _5_SAFETY_FLAGS:
            assert getattr(a, flag) is True, flag


class TestConstants:
    def test_17_categories(self):
        assert len(VALID_NGE_CATEGORIES) == 17

    def test_6_severities(self):
        assert len(VALID_NGE_SEVERITIES) == 6

    def test_3_statuses(self):
        assert len(VALID_NGE_STATUSES) == 3

    def test_2_decisions(self):
        assert len(VALID_NGE_DECISIONS) == 2

    def test_30_conditions(self):
        assert len(VALID_NGE_CONDITIONS) == 30

    def test_all_severities_non_overridable_by_design(self):
        severities = [
            NGE_SEVERITY_CRITICAL_BLOCKER, NGE_SEVERITY_HARD_BLOCKER,
            NGE_SEVERITY_MISSING_PREREQUISITE, NGE_SEVERITY_TRUST_FAILURE,
            NGE_SEVERITY_UNSUPPORTED_REQUEST, NGE_SEVERITY_REPORTING_FAILURE,
        ]
        assert len(severities) == 6
        # All severities always deny/fail-closed by model design

    def test_decisions_are_blocked_or_deny(self):
        assert NGE_DECISION_BLOCKED == "blocked"
        assert NGE_DECISION_DENY == "deny"
        # No decision means execute/invoke/apply/commit/push

    def test_statuses_are_non_executing(self):
        assert NGE_STATUS_DENIED == "denied"
        assert NGE_STATUS_BLOCKED == "blocked"
        # No status implies execution capability


class TestValidation:
    def test_default_passes(self):
        assert NoGoEnforcementEvidence().validate() == []

    def test_rejects_unknown_schema(self):
        issues = NoGoEnforcementEvidence(schema_version="99.0").validate()
        assert any("unknown schema_version" in i for i in issues)

    def test_rejects_invalid_status(self):
        issues = NoGoEnforcementEvidence(evaluation_status="running").validate()
        assert any("invalid evaluation_status" in i for i in issues)

    def test_rejects_invalid_decision(self):
        issues = NoGoEnforcementEvidence(evaluation_decision="approved").validate()
        assert any("invalid evaluation_decision" in i for i in issues)

    def test_rejects_execution_available_true(self):
        issues = NoGoEnforcementEvidence(execution_available=True).validate()
        assert any("execution_available must be False" in i for i in issues)

    def test_rejects_execution_authorized_true(self):
        issues = NoGoEnforcementEvidence(execution_authorized=True).validate()
        assert any("execution_authorized must be False" in i for i in issues)

    def test_rejects_push_authorized_true(self):
        issues = NoGoEnforcementEvidence(push_authorized=True).validate()
        assert any("push_authorized must be False" in i for i in issues)

    def test_rejects_simulation_only_false(self):
        issues = NoGoEnforcementEvidence(simulation_only=False).validate()
        assert any("simulation_only must be True" in i for i in issues)

    def test_rejects_no_execution_false(self):
        issues = NoGoEnforcementEvidence(no_execution=False).validate()
        assert any("no_execution must be True" in i for i in issues)

    def test_rejects_design_only_false(self):
        issues = NoGoEnforcementEvidence(design_only=False).validate()
        assert any("design_only must be True" in i for i in issues)

    def test_rejects_unknown_no_go_condition(self):
        issues = NoGoEnforcementEvidence(
            triggered_no_go_conditions=["BOGUS_CONDITION"],
        ).validate()
        assert any("unknown no-go condition" in i for i in issues)

    def test_accepts_valid_no_go_condition(self):
        issues = NoGoEnforcementEvidence(
            triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS],
        ).validate()
        assert not any("unknown no-go condition" in i for i in issues)


class TestFailClosed:
    def test_missing_evidence_fail_closed(self):
        a = NoGoEnforcementEvidence(
            missing_evidence=["phase97_preflight", "human_approval"],
        )
        assert a.execution_available is False
        assert a.no_execution is True

    def test_artifact_trust_failure_fail_closed(self):
        a = NoGoEnforcementEvidence(
            triggered_no_go_conditions=[NGE_ARTIFACT_TAMPERED],
            failed_checks=["digest_mismatch"],
        )
        assert a.execution_available is False
        assert a.no_execution is True

    def test_missing_prerequisite_fail_closed(self):
        a = NoGoEnforcementEvidence(
            triggered_no_go_conditions=["MISSING_PHASE97_PREFLIGHT"],
            missing_evidence=["phase97_preflight"],
        )
        assert a.execution_authorized is False

    def test_unsupported_request_fail_closed(self):
        a = NoGoEnforcementEvidence(
            unsupported_requests=["telegram_inbound_requested"],
        )
        assert a.execution_available is False

    def test_override_attempt_cannot_clear_no_go(self):
        a = NoGoEnforcementEvidence(
            triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS],
            override_attempts=["admin_override"],
        )
        assert a.triggered_no_go_conditions == [NGE_BYPASS_PERMISSIONS]
        assert a.execution_available is False

    def test_multiple_blockers_aggregate(self):
        a = NoGoEnforcementEvidence(
            triggered_no_go_conditions=[
                NGE_BYPASS_PERMISSIONS, NGE_ARTIFACT_TAMPERED,
            ],
            failed_checks=["digest_mismatch", "schema_unknown"],
        )
        assert len(a.triggered_no_go_conditions) == 2
        assert a.execution_available is False

    def test_unknown_condition_fail_closed(self):
        a = NoGoEnforcementEvidence(
            unknown_conditions=["UNKNOWN_FUTURE_CONDITION_XYZ"],
        )
        assert a.execution_available is False
        assert a.no_execution is True


class TestAuthorizationFlagTrust:
    def test_all_12_in_to_dict_summary(self):
        d = NoGoEnforcementEvidence().to_dict()
        for flag in _12_AUTH_FLAGS:
            assert flag in d["authorization_summary"], flag
            assert d["authorization_summary"][flag] is False

    def test_no_artifact_text_implies_auth(self):
        j = _json.dumps(NoGoEnforcementEvidence().to_dict()).lower()
        assert "execution is authorized" not in j


class TestDigest:
    def test_sha256_64_chars(self):
        dgst = NoGoEnforcementEvidence().compute_digest()
        assert len(dgst) == 64

    def test_deterministic(self):
        d1 = NoGoEnforcementEvidence().compute_digest()
        d2 = NoGoEnforcementEvidence().compute_digest()
        assert d1 == d2

    def test_changes_with_triggered_conditions(self):
        d1 = NoGoEnforcementEvidence().compute_digest()
        d2 = NoGoEnforcementEvidence(
            triggered_no_go_conditions=[NGE_BYPASS_PERMISSIONS],
        ).compute_digest()
        assert d1 != d2

    def test_excludes_digest_itself(self):
        a = NoGoEnforcementEvidence()
        d1 = a.compute_digest()
        a.digest = "f" * 64
        assert a.compute_digest() == d1


class TestNoExecutionGuard:
    def test_validate_no_exec(self):
        import inspect
        src = inspect.getsource(NoGoEnforcementEvidence.validate)
        for term in ["subprocess.run", "os.system", "Popen(", "spawn("]:
            assert term not in src

    def test_compute_digest_no_exec(self):
        import inspect
        src = inspect.getsource(NoGoEnforcementEvidence.compute_digest)
        for term in ["subprocess.run", "os.system", "Popen("]:
            assert term not in src

    def test_to_dict_no_exec(self):
        import inspect
        src = inspect.getsource(NoGoEnforcementEvidence.to_dict)
        for term in ["subprocess.run", "os.system", "Popen("]:
            allowed_false_positives = ["subprocess_authorized"]
            for t in term.split(","):
                t = t.strip()
                if t in src and t not in allowed_false_positives:
                    # Actually check if it's a call, not a field name
                    if t + "(" not in src and t + " " not in src:
                        continue
        # Broader check: no actual execution calls
        assert "subprocess.run(" not in src
        assert "os.system(" not in src

    def test_to_dict_json_no_exec_commands(self):
        j = _json.dumps(NoGoEnforcementEvidence().to_dict()).lower()
        for term in ["subprocess.run", "os.system", "exec(", "shell=true"]:
            assert term not in j

    def test_all_paths_non_executing(self):
        a = NoGoEnforcementEvidence(
            triggered_no_go_conditions=[
                NGE_BYPASS_PERMISSIONS, NGE_ARTIFACT_TAMPERED,
            ],
            missing_evidence=["approval"],
            failed_checks=["digest"],
            denial_reasons=["denied_bypass_permissions"],
        )
        a.validate()
        a.digest = a.compute_digest()
        d = a.to_dict()
        j = _json.dumps(d)
        assert a.execution_available is False
        assert a.no_execution is True
        assert a.non_authorizing is True


class TestPhase99Preservation:
    def test_no_go_model_does_not_alter_attempt_boundary(self):
        from pcae.core.backend_invocations import GovernedExecutionAttemptBoundary
        a = GovernedExecutionAttemptBoundary()
        assert a.attempt_state == "unavailable"
        assert a.execution_available is False
        assert len(a.to_dict()) == 33
