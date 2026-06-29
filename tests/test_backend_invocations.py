"""Tests for Phase 94B — Backend registry and invocation request model."""

from __future__ import annotations

import json
import pytest

from pcae.core.backend_invocations import (
    BackendDefinition,
    InvocationRequest,
    check_invocation_readiness,
    get_default_registry,
    make_invocation_request,
    SCHEMA_VERSION,
    RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL,
    INVOCATION_MODE_ARTIFACT_ONLY, INVOCATION_MODE_DRY_RUN,
    APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_DENIED,
    READINESS_READY, READINESS_BLOCKED, READINESS_NEEDS_HUMAN_REVIEW,
    READINESS_MISSING_EVIDENCE,
)

pytestmark = pytest.mark.fast_green


# ═══════════════════════════════════════════════════════════════════════════
# Backend definition tests
# ═══════════════════════════════════════════════════════════════════════════


class TestBackendDefinition:
    def test_valid_backend(self):
        b = BackendDefinition(backend_id="test", display_name="Test")
        assert b.validate() == []

    def test_missing_backend_id(self):
        b = BackendDefinition()
        issues = b.validate()
        assert any("backend_id" in i for i in issues)

    def test_invalid_risk_level(self):
        b = BackendDefinition(backend_id="x", risk_level="unknown")
        issues = b.validate()
        assert any("risk_level" in i for i in issues)

    def test_critical_risk_requires_approval(self):
        b = BackendDefinition(backend_id="x", risk_level=RISK_CRITICAL,
                              requires_human_approval=False)
        issues = b.validate()
        assert any("critical" in i for i in issues)

    def test_serialization_round_trip(self):
        b = BackendDefinition(
            backend_id="claude", backend_type="cli",
            display_name="Claude", risk_level=RISK_MEDIUM,
        )
        d = b.to_dict()
        b2 = BackendDefinition.from_dict(d)
        assert b2.backend_id == "claude"
        assert b2.risk_level == RISK_MEDIUM


# ═══════════════════════════════════════════════════════════════════════════
# Default registry tests
# ═══════════════════════════════════════════════════════════════════════════


class TestDefaultRegistry:
    def test_registry_has_expected_backends(self):
        reg = get_default_registry()
        assert "claude" in reg
        assert "claude-deepseek" in reg
        assert "codex" in reg
        assert "qwen" in reg
        assert "mock" in reg

    def test_all_backends_valid(self):
        reg = get_default_registry()
        for bid, b in reg.items():
            issues = b.validate()
            assert issues == [], f"{bid}: {issues}"

    def test_mock_backend_is_low_risk(self):
        reg = get_default_registry()
        assert reg["mock"].risk_level == RISK_LOW
        assert reg["mock"].requires_human_approval is False

    def test_claude_backend_is_medium_risk(self):
        reg = get_default_registry()
        assert reg["claude"].risk_level == RISK_MEDIUM

    def test_no_executable_strings_in_registry(self):
        # Registry is metadata only — no command strings that would imply execution
        reg = get_default_registry()
        for b in reg.values():
            d = b.to_dict()
            for val in d.values():
                if isinstance(val, str):
                    assert "subprocess" not in val.lower()


# ═══════════════════════════════════════════════════════════════════════════
# Invocation request tests
# ═══════════════════════════════════════════════════════════════════════════


class TestInvocationRequest:
    def test_valid_request(self):
        req = make_invocation_request(backend_id="mock")
        assert req.request_id.startswith("be-")
        assert req.no_execution_by_default is True

    def test_no_execution_defaults_true(self):
        req = InvocationRequest(backend_id="mock")
        assert req.no_execution_by_default is True

    def test_missing_backend_id(self):
        with pytest.raises(ValueError):
            make_invocation_request(backend_id="")

    def test_invalid_execution_mode(self):
        req = InvocationRequest(backend_id="mock", execution_mode="invalid")
        issues = req.validate()
        assert any("execution_mode" in i for i in issues)

    def test_approval_pending_default(self):
        req = InvocationRequest(backend_id="mock")
        assert req.approval_state == APPROVAL_PENDING

    def test_serialization_round_trip(self):
        req = make_invocation_request(
            backend_id="claude", phase_id="94B",
            task_id="task-1", prompt_artifact_path=".pcae/backend-invocations/prompt.md",
        )
        d = req.to_dict()
        req2 = InvocationRequest.from_dict(d)
        assert req2.backend_id == "claude"
        assert req2.phase_id == "94B"
        assert req2.no_execution_by_default is True

    def test_preserves_multi_part_phase_id(self):
        req = make_invocation_request(backend_id="mock", phase_id="94B.1")
        assert req.phase_id == "94B.1"


# ═══════════════════════════════════════════════════════════════════════════
# Readiness tests
# ═══════════════════════════════════════════════════════════════════════════


class TestReadiness:
    def test_mock_backend_ready(self):
        req = make_invocation_request(
            backend_id="mock", prompt_artifact_path="/tmp/prompt.md",
        )
        result = check_invocation_readiness(req)
        assert result["status"] == READINESS_READY

    def test_unknown_backend_blocked(self):
        req = make_invocation_request(backend_id="nonexistent")
        result = check_invocation_readiness(req)
        assert result["status"] == READINESS_BLOCKED
        assert any("unknown backend" in hb for hb in result["hard_blocks"])

    def test_missing_prompt_artifact(self):
        req = make_invocation_request(backend_id="mock")
        result = check_invocation_readiness(req)
        assert result["status"] == READINESS_MISSING_EVIDENCE
        assert "prompt_artifact_path" in result["missing_evidence"]

    def test_high_risk_needs_approval(self):
        reg = get_default_registry()
        reg["high-risk"] = BackendDefinition(
            backend_id="high-risk", risk_level=RISK_HIGH,
            requires_human_approval=True,
        )
        req = make_invocation_request(
            backend_id="high-risk", prompt_artifact_path="/tmp/p.md",
        )
        result = check_invocation_readiness(req, reg)
        assert result["status"] == READINESS_NEEDS_HUMAN_REVIEW

    def test_high_risk_approved_ready(self):
        reg = get_default_registry()
        reg["high-risk-ok"] = BackendDefinition(
            backend_id="high-risk-ok", risk_level=RISK_HIGH,
            requires_human_approval=True,
        )
        req = make_invocation_request(
            backend_id="high-risk-ok", prompt_artifact_path="/tmp/p.md",
            approval_state=APPROVAL_APPROVED,
        )
        result = check_invocation_readiness(req, reg)
        assert result["status"] == READINESS_READY

    def test_denied_approval_blocked(self):
        req = make_invocation_request(
            backend_id="mock", prompt_artifact_path="/tmp/p.md",
            approval_state=APPROVAL_DENIED,
        )
        result = check_invocation_readiness(req)
        assert result["status"] == READINESS_BLOCKED

    def test_critical_risk_hard_blocked(self):
        reg = get_default_registry()
        reg["critical-be"] = BackendDefinition(
            backend_id="critical-be", risk_level=RISK_CRITICAL,
            requires_human_approval=True,
        )
        req = make_invocation_request(
            backend_id="critical-be", prompt_artifact_path="/tmp/p.md",
            approval_state=APPROVAL_APPROVED,
        )
        result = check_invocation_readiness(req, reg)
        assert result["status"] == READINESS_BLOCKED
        assert any("critical" in hb for hb in result["hard_blocks"])

    def test_no_execution_false_is_blocked(self):
        req = make_invocation_request(backend_id="mock")
        req.no_execution_by_default = False
        result = check_invocation_readiness(req)
        assert result["status"] == READINESS_BLOCKED

    def test_no_subprocess_execution(self):
        # Verify module has no subprocess/exec calls
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "import subprocess" not in source
        assert "subprocess.run" not in source
        assert "Popen(" not in source


# ═══════════════════════════════════════════════════════════════════════════
# No-secret-leak tests
# ═══════════════════════════════════════════════════════════════════════════


class TestNoSecretLeak:
    def test_registry_does_not_contain_secret_values(self):
        reg = get_default_registry()
        for b in reg.values():
            for req_name in b.secret_requirements:
                # Secret names are OK (e.g., "ANTHROPIC_API_KEY")
                # but actual values must never appear
                assert not req_name.startswith("sk-")
                assert not req_name.startswith("ghp_")
                assert len(req_name) < 100  # not a token

    def test_serialized_registry_no_raw_secrets(self):
        reg = get_default_registry()
        for b in reg.values():
            j = json.dumps(b.to_dict())
            assert "sk-ant" not in j
            assert "ghp_" not in j
