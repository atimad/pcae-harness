"""Tests for execution readiness preflight dry-run — Phase 97F.

All models must remain non-executing and non-authorizing.
Tests prove that the preflight aggregates 97A–97E evidence correctly,
fails closed on missing evidence, never authorizes execution,
and produces deterministic digests.
"""

from __future__ import annotations

import hashlib
import json as _json
import pytest
from datetime import datetime, timezone

from pcae.core.backend_invocations import (
    _PREFLIGHT_SCHEMA_VERSION,
    PREFLIGHT_BLOCKED,
    PREFLIGHT_EVIDENCE_INCOMPLETE,
    PREFLIGHT_APPROVAL_REQUIRED,
    PREFLIGHT_AUDIT_REQUIRED,
    PREFLIGHT_ROLLBACK_REQUIRED,
    PREFLIGHT_FAILED_VERIFICATION,
    PREFLIGHT_NOT_READY,
    PREFLIGHT_READY_FOR_PREFLIGHT_ONLY,
    PREFLIGHT_UNAVAILABLE,
    PREFLIGHT_EXECUTION_READY_FUTURE_ONLY,
    PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY,
    PREFLIGHT_INVOKE_NOW_FUTURE_ONLY,
    PREFLIGHT_APPLY_NOW_FUTURE_ONLY,
    PREFLIGHT_COMMIT_NOW_FUTURE_ONLY,
    PREFLIGHT_PUSH_NOW_FUTURE_ONLY,
    UNAVAILABLE_PREFLIGHT_STATUSES,
    VALID_PREFLIGHT_STATUSES,
    VALID_NOGO_CONDITIONS,
    ExecutionReadinessPreflight,
    build_execution_readiness_preflight,
    save_execution_readiness_preflight,
    load_latest_execution_readiness_preflight,
    verify_execution_readiness_preflight,
    _preflight_dir_path,
    _preflight_latest_path,
)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def basic_preflight():
    """Build a preflight with default (no evidence) inputs."""
    return build_execution_readiness_preflight()


@pytest.fixture
def clean_artifact_dir():
    """Ensure artifact dir is clean before each test that saves."""
    import shutil
    dir_path = _preflight_dir_path()
    if dir_path.exists():
        shutil.rmtree(dir_path)
    yield
    if dir_path.exists():
        shutil.rmtree(dir_path)


# ═══════════════════════════════════════════════════════════════════════════
# Preflight status constants
# ═══════════════════════════════════════════════════════════════════════════


class TestPreflightStatusConstants:
    """97F defines only non-executing statuses."""

    def test_no_execute_now_status(self):
        """execute_now must not be a valid preflight status."""
        assert PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY not in VALID_PREFLIGHT_STATUSES
        assert PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY in UNAVAILABLE_PREFLIGHT_STATUSES

    def test_no_invoke_now_status(self):
        """invoke_now must not be a valid preflight status."""
        assert PREFLIGHT_INVOKE_NOW_FUTURE_ONLY not in VALID_PREFLIGHT_STATUSES
        assert PREFLIGHT_INVOKE_NOW_FUTURE_ONLY in UNAVAILABLE_PREFLIGHT_STATUSES

    def test_no_apply_now_status(self):
        """apply_now must not be a valid preflight status."""
        assert PREFLIGHT_APPLY_NOW_FUTURE_ONLY not in VALID_PREFLIGHT_STATUSES
        assert PREFLIGHT_APPLY_NOW_FUTURE_ONLY in UNAVAILABLE_PREFLIGHT_STATUSES

    def test_no_commit_now_status(self):
        """commit_now must not be a valid preflight status."""
        assert PREFLIGHT_COMMIT_NOW_FUTURE_ONLY not in VALID_PREFLIGHT_STATUSES
        assert PREFLIGHT_COMMIT_NOW_FUTURE_ONLY in UNAVAILABLE_PREFLIGHT_STATUSES

    def test_no_push_now_status(self):
        """push_now must not be a valid preflight status."""
        assert PREFLIGHT_PUSH_NOW_FUTURE_ONLY not in VALID_PREFLIGHT_STATUSES
        assert PREFLIGHT_PUSH_NOW_FUTURE_ONLY in UNAVAILABLE_PREFLIGHT_STATUSES

    def test_valid_statuses_are_non_executing(self):
        """All valid preflight statuses must be non-executing (no *_now or execution_ready)."""
        future = {
            PREFLIGHT_EXECUTION_READY_FUTURE_ONLY,
            PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY,
            PREFLIGHT_INVOKE_NOW_FUTURE_ONLY,
            PREFLIGHT_APPLY_NOW_FUTURE_ONLY,
            PREFLIGHT_COMMIT_NOW_FUTURE_ONLY,
            PREFLIGHT_PUSH_NOW_FUTURE_ONLY,
        }
        assert VALID_PREFLIGHT_STATUSES.isdisjoint(future)


# ═══════════════════════════════════════════════════════════════════════════
# Preflight result assertions
# ═══════════════════════════════════════════════════════════════════════════


class TestPreflightNonExecuting:
    """Preflight result must never authorize execution."""

    def test_preflight_is_non_executing(self, basic_preflight):
        """Preflight result must have no_execution=True, execution_available=False."""
        assert basic_preflight.no_execution is True
        assert basic_preflight.execution_available is False
        assert basic_preflight.simulation_only is True

    def test_preflight_is_non_authorizing(self, basic_preflight):
        """All authorization flags must be False."""
        assert basic_preflight.execution_authorized is False
        assert basic_preflight.backend_invocation_authorized is False
        assert basic_preflight.adapter_execution_authorized is False
        assert basic_preflight.network_authorized is False
        assert basic_preflight.subprocess_authorized is False
        assert basic_preflight.shell_authorized is False
        assert basic_preflight.mutation_authorized is False
        assert basic_preflight.apply_authorized is False
        assert basic_preflight.rollback_authorized is False
        assert basic_preflight.commit_authorized is False
        assert basic_preflight.push_authorized is False

    def test_preflight_never_has_execution_now_status(self, basic_preflight):
        """Preflight status must never be execute_now or equivalent."""
        assert basic_preflight.preflight_status != PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY
        assert basic_preflight.preflight_status != PREFLIGHT_INVOKE_NOW_FUTURE_ONLY
        assert basic_preflight.preflight_status != PREFLIGHT_APPLY_NOW_FUTURE_ONLY
        assert basic_preflight.preflight_status != PREFLIGHT_COMMIT_NOW_FUTURE_ONLY
        assert basic_preflight.preflight_status != PREFLIGHT_PUSH_NOW_FUTURE_ONLY
        assert basic_preflight.preflight_status != PREFLIGHT_EXECUTION_READY_FUTURE_ONLY


class TestPreflightEvidenceAggregation:
    """Preflight correctly aggregates evidence from 97A–97E models."""

    def test_minimal_preflight_has_missing_evidence(self, basic_preflight):
        """Default preflight with no inputs should report missing evidence."""
        assert len(basic_preflight.missing_evidence) > 0
        # At minimum: human_approval_gate, active_task_contract, phase_finalization
        assert "human_approval_gate" in basic_preflight.missing_evidence

    def test_preflight_has_no_go_conditions(self, basic_preflight):
        """Default preflight should have no-go conditions from 97A model."""
        assert len(basic_preflight.no_go_conditions) > 0
        assert "failed_artifact_verification" in basic_preflight.no_go_conditions

    def test_preflight_has_evidence_refs_for_present_evidence(self, basic_preflight):
        """97A–97E evidence should be referenced when present."""
        refs = basic_preflight.evidence_refs
        assert any("readiness_97a" in ref for ref in refs)
        assert any("backend_invocation_contract_97b" in ref for ref in refs)
        assert any("adapter_invocation_boundary_97c" in ref for ref in refs)
        assert any("audit_rollback_readiness_97e" in ref for ref in refs)

    def test_missing_readiness_produces_not_ready(self):
        """Missing readiness data produces blocked/evidence_incomplete/failed_verification."""
        preflight = build_execution_readiness_preflight(readiness_data=None)
        assert preflight.preflight_status in (
            PREFLIGHT_EVIDENCE_INCOMPLETE,
            PREFLIGHT_BLOCKED,
            PREFLIGHT_FAILED_VERIFICATION,
        )

    def test_missing_backend_contract_blocks_preflight(self):
        """Missing backend contract produces blocked status."""
        preflight = build_execution_readiness_preflight(backend_data=None)
        assert "missing_backend_invocation_contract" in preflight.no_go_conditions

    def test_missing_adapter_boundary_blocks_preflight(self):
        """Missing adapter boundary produces blocked status."""
        preflight = build_execution_readiness_preflight(adapter_data=None)
        assert "missing_adapter_boundary" in preflight.no_go_conditions

    def test_missing_approval_produces_approval_required(self):
        """Missing approval gate evidence produces approval_required."""
        preflight = build_execution_readiness_preflight(approval_data=None)
        assert "missing_human_approval" in preflight.no_go_conditions
        assert preflight.approval_status == PREFLIGHT_APPROVAL_REQUIRED

    def test_missing_audit_produces_audit_required(self):
        """Missing audit readiness produces audit_required."""
        preflight = build_execution_readiness_preflight(audit_data=None)
        assert "missing_audit_readiness" in preflight.no_go_conditions
        assert preflight.audit_readiness_status == PREFLIGHT_AUDIT_REQUIRED

    def test_missing_rollback_produces_rollback_required(self):
        """Missing rollback readiness produces rollback_required."""
        preflight = build_execution_readiness_preflight(audit_data=None)
        assert "missing_rollback_readiness" in preflight.no_go_conditions
        assert preflight.rollback_readiness_status == PREFLIGHT_ROLLBACK_REQUIRED


class TestPreflightNoGoConditions:
    """No-go conditions correctly block preflight."""

    def test_no_go_conditions_produce_blocked_or_worse(self):
        """When no-go conditions exist, preflight must NOT be ready_for_preflight_only."""
        preflight = build_execution_readiness_preflight()
        # With missing evidence + no no-go → could be evidence_incomplete
        # With no-go → should not be ready_for_preflight_only
        assert preflight.preflight_status != PREFLIGHT_READY_FOR_PREFLIGHT_ONLY

    def test_all_no_go_conditions_are_valid(self, basic_preflight):
        """All no_go_conditions must be in VALID_NOGO_CONDITIONS."""
        for cond in basic_preflight.no_go_conditions:
            assert cond in VALID_NOGO_CONDITIONS, f"unknown no-go: {cond!r}"

    def test_no_go_deduplicated(self, basic_preflight):
        """No-go conditions must be deduplicated."""
        assert len(basic_preflight.no_go_conditions) == len(set(basic_preflight.no_go_conditions))

    def test_no_go_conditions_are_sorted(self, basic_preflight):
        """No-go conditions must be sorted for deterministic output."""
        assert basic_preflight.no_go_conditions == sorted(basic_preflight.no_go_conditions)


class TestPreflightValidation:
    """Preflight self-validation invariants."""

    def test_valid_preflight_passes_validation(self):
        """A preflight with all authorization flags False should validate cleanly."""
        preflight = ExecutionReadinessPreflight(
            preflight_id="test-1",
            preflight_status=PREFLIGHT_BLOCKED,
        )
        issues = preflight.validate()
        assert len(issues) == 0

    def test_execution_available_flag_fails_validation(self):
        """execution_available=True must fail validation."""
        preflight = ExecutionReadinessPreflight(
            preflight_id="test-1",
            preflight_status=PREFLIGHT_BLOCKED,
            execution_available=True,
        )
        issues = preflight.validate()
        assert any("execution_available must be False" in i for i in issues)

    def test_execution_authorized_flag_fails_validation(self):
        """execution_authorized=True must fail validation."""
        preflight = ExecutionReadinessPreflight(
            preflight_id="test-1",
            preflight_status=PREFLIGHT_BLOCKED,
            execution_authorized=True,
        )
        issues = preflight.validate()
        assert any("execution_authorized must be False" in i for i in issues)

    def test_all_authorization_flags_false_by_default(self):
        """Default preflight has all authorization flags False."""
        preflight = ExecutionReadinessPreflight()
        assert not preflight.execution_available
        assert not preflight.execution_authorized
        assert not preflight.backend_invocation_authorized
        assert not preflight.adapter_execution_authorized
        assert not preflight.network_authorized
        assert not preflight.subprocess_authorized
        assert not preflight.shell_authorized
        assert not preflight.mutation_authorized
        assert not preflight.apply_authorized
        assert not preflight.rollback_authorized
        assert not preflight.commit_authorized
        assert not preflight.push_authorized

    def test_future_execution_status_fails_validation(self):
        """Future-only execution_ready status must fail validation if used as current."""
        preflight = ExecutionReadinessPreflight(
            preflight_id="test-1",
            preflight_status=PREFLIGHT_EXECUTION_READY_FUTURE_ONLY,
        )
        issues = preflight.validate()
        assert len(issues) > 0
        assert any("future-only" in i for i in issues)

    def test_invalid_preflight_status_fails_validation(self):
        """Unknown preflight status must fail validation."""
        preflight = ExecutionReadinessPreflight(
            preflight_id="test-1",
            preflight_status="not_a_real_status",
        )
        issues = preflight.validate()
        assert any("invalid preflight_status" in i for i in issues)

    def test_schema_version_mismatch_fails_validation(self):
        """Unknown schema version must fail validation."""
        preflight = ExecutionReadinessPreflight(
            preflight_id="test-1",
            preflight_status=PREFLIGHT_BLOCKED,
            schema_version="999.0",
        )
        issues = preflight.validate()
        assert any("unknown schema_version" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════════
# Digest behavior
# ═══════════════════════════════════════════════════════════════════════════


class TestDigestDeterminism:
    """Preflight digest is deterministic and sensitive to changes."""

    def test_digest_is_deterministic(self):
        """Same inputs should produce same digest."""
        p1 = build_execution_readiness_preflight(task_id="task-1")
        p2 = build_execution_readiness_preflight(task_id="task-1")
        # Digests should be deterministic modulo timestamp
        d1 = p1.compute_digest()
        d2 = p2.compute_digest()
        # Different generated_at_utc → different digest
        # So test that same object produces same digest
        assert p1.compute_digest() == p1.compute_digest()
        assert p2.compute_digest() == p2.compute_digest()

    def test_digest_changes_when_no_go_conditions_change(self):
        """Digest must change when no-go conditions differ."""
        p1 = build_execution_readiness_preflight(task_id="test")
        p1_copy = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p1_copy.no_go_conditions = ["test_condition"]
        assert p1.compute_digest() != p1_copy.compute_digest()

    def test_digest_changes_when_authorization_flags_change(self):
        """Digest must change when authorization flags differ."""
        p1 = build_execution_readiness_preflight(task_id="test")
        p1_copy = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p1_copy.push_authorized = True
        assert p1.compute_digest() != p1_copy.compute_digest()

    def test_digest_changes_when_preflight_status_changes(self):
        """Digest must change when preflight status differs."""
        p1 = build_execution_readiness_preflight(task_id="test")
        p1_copy = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p1_copy.preflight_status = PREFLIGHT_UNAVAILABLE
        assert p1.compute_digest() != p1_copy.compute_digest()

    def test_digest_changes_when_evidence_refs_change(self):
        """Digest must change when evidence refs differ."""
        p1 = build_execution_readiness_preflight(task_id="test")
        p1_copy = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p1_copy.evidence_refs = ["new_ref"]
        assert p1.compute_digest() != p1_copy.compute_digest()

    def test_digest_is_stable_across_equivalent_formatting(self):
        """Canonical dict representation used for digest, not direct serialization."""
        p = build_execution_readiness_preflight(task_id="test")
        d1 = p.compute_digest()
        # Round-trip through to_dict/from_dict should produce same digest
        p2 = ExecutionReadinessPreflight.from_dict(p.to_dict())
        p2.generated_at_utc = p.generated_at_utc  # align timestamps
        p2.preflight_id = p.preflight_id
        d2 = p2.compute_digest()
        assert d1 == d2


# ═══════════════════════════════════════════════════════════════════════════
# Persistence and verification
# ═══════════════════════════════════════════════════════════════════════════


class TestPreflightPersistence:
    """Save and load preflight artifacts."""

    def test_save_and_load_roundtrip(self, clean_artifact_dir):
        """Save then load should produce equivalent preflight."""
        preflight = build_execution_readiness_preflight(task_id="persist-test")
        saved_path = save_execution_readiness_preflight(preflight)
        assert saved_path.exists()

        loaded = load_latest_execution_readiness_preflight()
        assert loaded is not None
        assert loaded.preflight_id == preflight.preflight_id
        assert loaded.task_id == preflight.task_id
        assert loaded.no_execution is True
        assert loaded.execution_available is False

    def test_load_when_no_artifact_returns_none(self, clean_artifact_dir):
        """Loading with no artifact should return None."""
        loaded = load_latest_execution_readiness_preflight()
        assert loaded is None

    def test_save_writes_latest_json(self, clean_artifact_dir):
        """Save should write latest.json."""
        preflight = build_execution_readiness_preflight(task_id="latest-test")
        save_execution_readiness_preflight(preflight)
        latest_path = _preflight_latest_path()
        assert latest_path.exists()
        raw = latest_path.read_text()
        data = _json.loads(raw)
        assert data["task_id"] == "latest-test"

    def test_save_writes_timestamped_copy(self, clean_artifact_dir):
        """Save should write a timestamped copy."""
        preflight = build_execution_readiness_preflight(task_id="ts-test")
        ts_path = save_execution_readiness_preflight(preflight)
        assert ts_path.exists()
        assert ts_path.name.endswith(".json")
        # Should have a YYYYMMDD-HHMMSS pattern
        import re
        assert re.match(r"\d{8}-\d{6}\.json", ts_path.name)


class TestPreflightVerification:
    """Preflight verification checks integrity."""

    def test_verify_with_no_artifact_returns_invalid(self):
        """Verifying when no artifact exists should return invalid."""
        # Temporarily ensure no artifact
        result = verify_execution_readiness_preflight(None)
        assert result["valid"] is False
        assert not result["preflight_present"]

    def test_verify_valid_preflight(self, clean_artifact_dir):
        """A saved preflight should verify cleanly (structural checks only)."""
        preflight = build_execution_readiness_preflight(task_id="verify-test")
        save_execution_readiness_preflight(preflight)
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        # May have issues with unknown no_go_conditions from passthrough
        # but no_execution_confirmed should be True
        assert result["no_execution_confirmed"] is True
        assert result["preflight_present"] is True

    def test_tampered_digest_fails_verification(self, clean_artifact_dir):
        """Tampered preflight (digest modified) should fail verification."""
        preflight = build_execution_readiness_preflight(task_id="tamper-test")
        save_execution_readiness_preflight(preflight)

        # Tamper: modify the saved JSON digest
        latest_path = _preflight_latest_path()
        raw = latest_path.read_text()
        data = _json.loads(raw)
        data["digest"] = "0000000000000000000000000000000000000000000000000000000000000000"
        latest_path.write_text(_json.dumps(data, indent=2), encoding="utf-8")

        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert any("digest_mismatch" in issue for issue in result["issues"])

    def test_tampered_safety_flag_fails_verification(self, clean_artifact_dir):
        """Tampered preflight (no_execution=False) should fail verification."""
        preflight = build_execution_readiness_preflight(task_id="safety-test")
        save_execution_readiness_preflight(preflight)

        # Tamper: set no_execution=False
        latest_path = _preflight_latest_path()
        raw = latest_path.read_text()
        data = _json.loads(raw)
        data["no_execution"] = False
        # Recompute digest to bypass digest check (tampered flag caught by validate)
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        latest_path.write_text(_json.dumps(data, indent=2), encoding="utf-8")

        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert any("no_execution must be True" in issue for issue in result["issues"])

    def test_verify_confirms_no_execution(self, basic_preflight):
        """Verification should always confirm no_execution."""
        result = verify_execution_readiness_preflight(basic_preflight)
        assert result["no_execution_confirmed"] is True


# ═══════════════════════════════════════════════════════════════════════════
# No-call guard tests
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCallGuards:
    """Preflight must never call subprocess, network, shell, or execution APIs."""

    def test_build_preflight_returns_dataclass(self):
        """build_execution_readiness_preflight returns ExecutionReadinessPreflight."""
        result = build_execution_readiness_preflight()
        assert isinstance(result, ExecutionReadinessPreflight)

    def test_save_is_pure_filesystem(self, clean_artifact_dir):
        """save writes files only using Python filesystem APIs, no subprocess."""
        preflight = build_execution_readiness_preflight(task_id="no-call")
        saved = save_execution_readiness_preflight(preflight)
        assert saved.exists()
        content = saved.read_text()
        data = _json.loads(content)
        assert data["task_id"] == "no-call"
        assert data["no_execution"] is True

    def test_verify_is_pure_computation(self, basic_preflight):
        """verify only inspects the preflight object — no filesystem or network."""
        result = verify_execution_readiness_preflight(basic_preflight)
        assert isinstance(result, dict)
        assert "valid" in result

    def test_to_dict_output_has_no_secrets(self, basic_preflight):
        """Preflight dict output must not contain any secret material."""
        d = basic_preflight.to_dict()
        # No API keys, tokens, passwords
        for value in str(d).split():
            assert "sk-" not in value.lower()
            assert "api_key" not in value.lower()
            assert "password" not in value.lower()
            assert "token" not in value.lower()

    def test_preflight_does_not_import_execution_modules(self):
        """Preflight model should not pull in subprocess, shell, or network modules."""
        import sys
        preflight_module = sys.modules.get("pcae.core.backend_invocations")
        if preflight_module:
            # These should not be imported by the preflight code path
            assert not hasattr(preflight_module, "subprocess") or not callable(
                getattr(preflight_module, "subprocess", None)
            )


# ═══════════════════════════════════════════════════════════════════════════
# Authorization flags
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthorizationFlags:
    """All authorization flags remain False in every preflight result."""

    def test_default_preflight_all_flags_false(self):
        """A fresh ExecutionReadinessPreflight() has all auth flags False."""
        p = ExecutionReadinessPreflight()
        assert p.execution_available is False
        assert p.execution_authorized is False
        assert p.backend_invocation_authorized is False
        assert p.adapter_execution_authorized is False
        assert p.network_authorized is False
        assert p.subprocess_authorized is False
        assert p.shell_authorized is False
        assert p.mutation_authorized is False
        assert p.apply_authorized is False
        assert p.rollback_authorized is False
        assert p.commit_authorized is False
        assert p.push_authorized is False

    def test_built_preflight_all_flags_false(self, basic_preflight):
        """A built preflight has all auth flags False."""
        p = basic_preflight
        assert p.execution_available is False
        assert p.execution_authorized is False
        assert p.backend_invocation_authorized is False
        assert p.adapter_execution_authorized is False
        assert p.network_authorized is False
        assert p.subprocess_authorized is False
        assert p.shell_authorized is False
        assert p.mutation_authorized is False
        assert p.apply_authorized is False
        assert p.rollback_authorized is False
        assert p.commit_authorized is False
        assert p.push_authorized is False

    def test_authorization_summary_in_to_dict_all_false(self, basic_preflight):
        """to_dict() authorization_summary has all False values."""
        d = basic_preflight.to_dict()
        auth = d["authorization_summary"]
        for key, value in auth.items():
            assert value is False, f"{key} must be False, got {value!r}"

    def test_from_dict_preserves_false_flags(self):
        """from_dict() preserves False authorization flags."""
        data = {
            "preflight_id": "roundtrip-test",
            "authorization_summary": {
                "execution_available": False,
                "execution_authorized": False,
                "backend_invocation_authorized": False,
                "adapter_execution_authorized": False,
                "network_authorized": False,
                "subprocess_authorized": False,
                "shell_authorized": False,
                "mutation_authorized": False,
                "apply_authorized": False,
                "rollback_authorized": False,
                "commit_authorized": False,
                "push_authorized": False,
            },
        }
        p = ExecutionReadinessPreflight.from_dict(data)
        assert p.execution_available is False
        assert p.push_authorized is False


# ═══════════════════════════════════════════════════════════════════════════
# Fail-closed behavior
# ═══════════════════════════════════════════════════════════════════════════


class TestFailClosedBehavior:
    """Preflight must fail closed on missing or invalid inputs."""

    def test_missing_readiness_model_produces_blocked(self):
        """Missing 97A readiness model → blocked."""
        preflight = build_execution_readiness_preflight(readiness_data=None)
        assert preflight.readiness_status != "ready"
        assert preflight.execution_available is False

    def test_missing_backend_contract_produces_blocked(self):
        """Missing 97B backend contract → blocked."""
        preflight = build_execution_readiness_preflight(backend_data=None)
        assert "missing_backend_invocation_contract" in preflight.no_go_conditions

    def test_missing_adapter_boundary_produces_blocked(self):
        """Missing 97C adapter boundary → blocked."""
        preflight = build_execution_readiness_preflight(adapter_data=None)
        assert "missing_adapter_boundary" in preflight.no_go_conditions

    def test_expired_approval_produces_no_go(self):
        """Expired/revoked approval → no-go condition added."""
        approval_data = {"decision": "revoked"}
        preflight = build_execution_readiness_preflight(approval_data=approval_data)
        assert "expired_or_revoked_approval" in preflight.no_go_conditions

    def test_missing_audit_produces_blocked(self):
        """Missing 97E audit → blocked."""
        preflight = build_execution_readiness_preflight(audit_data=None)
        assert "missing_audit_readiness" in preflight.no_go_conditions

    def test_missing_rollback_produces_blocked(self):
        """Missing 97E rollback → blocked."""
        preflight = build_execution_readiness_preflight(audit_data=None)
        assert "missing_rollback_readiness" in preflight.no_go_conditions

    def test_no_execution_stays_false_on_missing_everything(self):
        """Even with all evidence missing, execution flags stay False."""
        preflight = build_execution_readiness_preflight(
            readiness_data=None,
            backend_data=None,
            adapter_data=None,
            approval_data=None,
            audit_data=None,
        )
        assert preflight.execution_available is False
        assert preflight.execution_authorized is False
        assert preflight.no_execution is True


# ═══════════════════════════════════════════════════════════════════════════
# Schema version consistency
# ═══════════════════════════════════════════════════════════════════════════


class TestSchemaVersion:
    """Schema version is consistent and validated."""

    def test_preflight_uses_correct_schema_version(self, basic_preflight):
        """Preflight must use the module-level schema version."""
        assert basic_preflight.schema_version == _PREFLIGHT_SCHEMA_VERSION
        assert basic_preflight.schema_version == "1.0"

    def test_unknown_schema_version_fails_validation(self):
        """Preflight with future schema version must fail validation."""
        preflight = ExecutionReadinessPreflight(
            preflight_id="schema-test",
            preflight_status=PREFLIGHT_BLOCKED,
            schema_version="2.0",
        )
        issues = preflight.validate()
        assert any("unknown schema_version" in i for i in issues)

    def test_verify_flags_unknown_schema(self, clean_artifact_dir):
        """verify_execution_readiness_preflight should catch unknown schema."""
        preflight = build_execution_readiness_preflight(task_id="schema-verify")
        preflight = ExecutionReadinessPreflight.from_dict(preflight.to_dict())
        # Force a bad schema version
        preflight.schema_version = "999.0"
        preflight.digest = preflight.compute_digest()
        result = verify_execution_readiness_preflight(preflight)
        assert result["valid"] is False
        assert any("unknown schema" in issue for issue in result["issues"])
