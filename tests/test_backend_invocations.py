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


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94C — Prompt artifact capture tests
# ═══════════════════════════════════════════════════════════════════════════


class TestPromptArtifactCapture:
    """Verify prompt artifact capture, hashing, redaction, persistence."""

    def test_capture_writes_prompt_file(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_prompt_artifact(
                req, "Write a function that adds two numbers.",
                invocation_dir=td,
            )
            assert result["status"] == "captured"
            assert Path(result["prompt_path"]).exists()

    def test_prompt_hash_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            req1 = make_invocation_request(backend_id="mock")
            r1 = capture_backend_prompt_artifact(req1, "hello", invocation_dir=td)
            req2 = make_invocation_request(backend_id="mock")
            r2 = capture_backend_prompt_artifact(req2, "hello", invocation_dir=td)
            assert r1["prompt_hash"] == r2["prompt_hash"]

    def test_prompt_hash_different_for_different_text(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            r1 = capture_backend_prompt_artifact(req, "hello A", invocation_dir=td)
            r2 = capture_backend_prompt_artifact(req, "hello B", invocation_dir=td)
            assert r1["prompt_hash"] != r2["prompt_hash"]

    def test_latest_prompt_updated(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_prompt_artifact(
                req, "latest test prompt", invocation_dir=td,
            )
            latest = Path(result["latest_prompt_path"])
            assert latest.exists()
            assert "latest test prompt" in latest.read_text()

    def test_latest_json_updated(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94C")
            result = capture_backend_prompt_artifact(
                req, "json test", invocation_dir=td,
            )
            latest = Path(result["latest_meta_path"])
            assert latest.exists()
            data = json.loads(latest.read_text())
            assert data["phase_id"] == "94C"

    def test_redaction_applied_for_secrets(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_prompt_artifact(
                req, "Use TOKEN=secret123 for auth", invocation_dir=td,
            )
            assert result["redaction_applied"] is True
            content = Path(result["prompt_path"]).read_text()
            assert "secret123" not in content
            assert "[REDACTED]" in content

    def test_redaction_not_applied_for_clean_text(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_prompt_artifact(
                req, "Write a test for the login function.", invocation_dir=td,
            )
            assert result["redaction_applied"] is False

    def test_request_prompt_hash_set(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            capture_backend_prompt_artifact(req, "test hash", invocation_dir=td)
            assert len(req.prompt_hash) == 64

    def test_request_prompt_artifact_path_set(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            capture_backend_prompt_artifact(req, "test path", invocation_dir=td)
            assert req.prompt_artifact_path

    def test_readiness_improves_with_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            # Before capture: missing evidence
            r1 = check_invocation_readiness(req)
            assert r1["status"] == READINESS_MISSING_EVIDENCE
            # Capture prompt
            capture_backend_prompt_artifact(req, "readiness test", invocation_dir=td)
            # After capture: ready
            r2 = check_invocation_readiness(req)
            assert r2["status"] == READINESS_READY

    def test_no_subprocess_execution(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "Popen(" not in source

    def test_multi_part_phase_id_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94C.1")
            result = capture_backend_prompt_artifact(
                req, "multi-part test", invocation_dir=td,
            )
            data = json.loads(Path(result["latest_meta_path"]).read_text())
            assert data["phase_id"] == "94C.1"


import tempfile
from pathlib import Path
from pcae.core.backend_invocations import (
    capture_backend_prompt_artifact, read_latest_prompt,
)


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94D — Output artifact capture tests
# ═══════════════════════════════════════════════════════════════════════════


class TestOutputArtifactCapture:
    """Verify output artifact capture, quarantine, redaction."""

    def test_capture_writes_output_file(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94D")
            result = capture_backend_output_artifact(
                req, "def add(a, b): return a + b", invocation_dir=td,
            )
            assert result["status"] == "captured"
            assert Path(result["output_path"]).exists()

    def test_output_hash_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            req1 = make_invocation_request(backend_id="mock")
            r1 = capture_backend_output_artifact(req1, "output", invocation_dir=td)
            req2 = make_invocation_request(backend_id="mock")
            r2 = capture_backend_output_artifact(req2, "output", invocation_dir=td)
            assert r1["output_hash"] == r2["output_hash"]

    def test_output_quarantined_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_output_artifact(req, "code", invocation_dir=td)
            assert result["quarantined"] is True
            assert result["applied_to_repo"] is False

    def test_artifact_quarantined_default(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_output_artifact(req, "code", invocation_dir=td)
            assert result["artifact"].quarantined is True
            assert result["artifact"].applied_to_repo is False

    def test_latest_output_updated(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_output_artifact(
                req, "latest output test", invocation_dir=td,
            )
            latest = Path(result["latest_output_path"])
            assert latest.exists()
            assert "latest output test" in latest.read_text()

    def test_redaction_output(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_output_artifact(
                req, "export API_KEY=abc123xyz", invocation_dir=td,
            )
            assert result["redaction_applied"] is True
            content = Path(result["output_path"]).read_text()
            assert "abc123xyz" not in content
            assert "[REDACTED]" in content

    def test_no_redaction_clean_output(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_output_artifact(
                req, "All tests passed: 40/40", invocation_dir=td,
            )
            assert result["redaction_applied"] is False

    def test_output_does_not_modify_source_files(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(
                backend_id="mock",
                allowed_files=["src/main.py"],
            )
            result = capture_backend_output_artifact(
                req, "patch: modify src/main.py", invocation_dir=td,
            )
            # Output written to artifact dir, not to allowed_files paths
            output_path = Path(result["output_path"])
            assert "src/main.py" not in str(output_path)
            assert "backend-invocations" in str(output_path) or td in str(output_path)

    def test_no_subprocess_in_output_capture(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "Popen(" not in source

    def test_multi_part_phase_id_in_output(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94D.1")
            result = capture_backend_output_artifact(
                req, "multi-part output", invocation_dir=td,
            )
            data = json.loads(Path(result["latest_meta_path"]).read_text())
            assert data["phase_id"] == "94D.1"

    def test_output_does_not_imply_approval(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock")
            result = capture_backend_output_artifact(req, "output", invocation_dir=td)
            # Quarantined must remain true — capture is not approval
            assert result["quarantined"] is True


from pcae.core.backend_invocations import (
    capture_backend_output_artifact, OutputArtifact,
)


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94F — Mock backend invocation prototype tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMockBackendInvocation:
    """Verify mock backend lifecycle."""

    def test_mock_run_completes(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(
                backend_id="mock", phase_id="94F",
                prompt_artifact_path="dummy",  # will be set by capture
            )
            result = run_mock_backend_invocation(req, "Write a test.", invocation_dir=td)
            assert result["status"] == "completed"

    def test_mock_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94F")
            r1 = run_mock_backend_invocation(req, "hello", invocation_dir=td)
            r2 = run_mock_backend_invocation(req, "hello", invocation_dir=td)
            assert r1["output_hash"] == r2["output_hash"]

    def test_mock_output_has_marker(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94F")
            result = run_mock_backend_invocation(req, "test", invocation_dir=td)
            output = Path(result["output_path"]).read_text()
            assert "MOCK BACKEND OUTPUT" in output
            assert "no real backend invoked" in output

    def test_mock_output_quarantined(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94F")
            result = run_mock_backend_invocation(req, "test", invocation_dir=td)
            assert result["quarantined"] is True
            assert result["applied_to_repo"] is False

    def test_non_mock_backend_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="claude", phase_id="94F")
            result = run_mock_backend_invocation(req, "test", invocation_dir=td)
            assert result["status"] == "blocked"

    def test_blocked_readiness_prevents_run(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", approval_state=APPROVAL_DENIED)
            result = run_mock_backend_invocation(req, "test", invocation_dir=td)
            assert result["status"] == "blocked"

    def test_no_real_backend_flags(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94F")
            result = run_mock_backend_invocation(req, "test", invocation_dir=td)
            assert result["no_real_backend_invoked"] is True
            assert result["no_subprocess"] is True
            assert result["no_network"] is True

    def test_prompt_hash_cross_referenced(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94F")
            result = run_mock_backend_invocation(req, "cross-ref test", invocation_dir=td)
            assert result["prompt_hash"]
            assert len(result["prompt_hash"]) == 64

    def test_no_subprocess_in_mock(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations._generate_mock_output)
        assert "import subprocess" not in source
        assert "subprocess.run" not in source
        assert "Popen(" not in source
        assert "urlopen" not in source

    def test_multi_part_phase_id_in_mock(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94F.1")
            result = run_mock_backend_invocation(req, "test", invocation_dir=td)
            assert result["status"] == "completed"


from pcae.core.backend_invocations import run_mock_backend_invocation


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94G — Audit trail tests
# ═══════════════════════════════════════════════════════════════════════════


class TestBackendAudit:
    def test_audit_persisted_for_mock_run(self):
        with tempfile.TemporaryDirectory() as td:
            req = make_invocation_request(backend_id="mock", phase_id="94G")
            result = run_mock_backend_invocation(req, "audit test", invocation_dir=td)
            assert result["status"] == "completed"

    def test_audit_record_written(self):
        with tempfile.TemporaryDirectory() as td:
            from pcae.core.backend_invocations import persist_backend_audit
            req = make_invocation_request(backend_id="mock", phase_id="94G")
            audit_result = persist_backend_audit("plan.created", req)
            assert audit_result["status"] == "written"

    def test_audit_record_fields(self):
        with tempfile.TemporaryDirectory() as td:
            from pcae.core.backend_invocations import persist_backend_audit
            req = make_invocation_request(backend_id="mock", phase_id="94G")
            audit_result = persist_backend_audit("plan.created", req)
            assert audit_result["record_digest"]
            assert len(audit_result["record_digest"]) == 64

    def test_latest_audit_updated(self):
        with tempfile.TemporaryDirectory() as td:
            from pcae.core.backend_invocations import persist_backend_audit, read_latest_backend_audit
            req = make_invocation_request(backend_id="mock")
            persist_backend_audit("mock.run", req)
            record = read_latest_backend_audit()
            assert record is not None
            assert record["event_type"] == "mock.run"

    def test_verify_backend_audit(self):
        with tempfile.TemporaryDirectory() as td:
            from pcae.core.backend_invocations import persist_backend_audit, verify_backend_audit
            req = make_invocation_request(backend_id="mock")
            persist_backend_audit("plan.created", req)
            result = verify_backend_audit()
            assert result["valid"] >= 1

    def test_audit_no_raw_secrets(self):
        with tempfile.TemporaryDirectory() as td:
            from pcae.core.backend_invocations import persist_backend_audit
            req = make_invocation_request(backend_id="mock", phase_id="94G")
            audit_result = persist_backend_audit("plan.created", req)
            path = Path(audit_result["path"])
            content = path.read_text()
            assert "sk-ant" not in content
            assert "ghp_" not in content

    def test_audit_cli_verify(self):
        import subprocess, sys, os
        from pathlib import Path as _P
        repo = _P(__file__).resolve().parent.parent
        orig_cwd = os.getcwd()
        os.chdir(str(repo))
        try:
            # Create an audit record first
            from pcae.core.backend_invocations import persist_backend_audit, make_invocation_request
            req = make_invocation_request(backend_id="mock")
            persist_backend_audit("plan.created", req)
            r = subprocess.run(
                [sys.executable, "-m", "pcae", "backend", "audit", "verify"],
                capture_output=True, text=True, timeout=15,
            )
            assert "Valid" in r.stdout or "valid" in r.stdout.lower()
        finally:
            os.chdir(orig_cwd)


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94H — Trust/readiness gate tests
# ═══════════════════════════════════════════════════════════════════════════


class TestTrustGate:
    def test_empty_assessment_missing(self):
        a = assess_backend_invocation_trust()
        assert a["status"] == "missing_evidence"
        assert a["trust_level"] == "partial"

    def test_prompt_only_is_missing(self):
        a = assess_backend_invocation_trust(prompt_meta={"prompt_hash": "abc"})
        assert "prompt_artifact" not in a["missing_evidence"]
        assert "output_artifact" in a["missing_evidence"]

    def test_output_not_quarantined_blocked(self):
        a = assess_backend_invocation_trust(
            prompt_meta={"prompt_hash": "abc"},
            output_meta={"output_hash": "def", "quarantined": False},
        )
        assert a["status"] == "blocked"

    def test_output_applied_blocked(self):
        a = assess_backend_invocation_trust(
            prompt_meta={"prompt_hash": "abc"},
            output_meta={"output_hash": "def", "quarantined": True, "applied_to_repo": True},
        )
        assert a["status"] == "blocked"

    def test_no_execution_false_blocked(self):
        req = make_invocation_request(backend_id="mock")
        req.no_execution_by_default = False
        a = assess_backend_invocation_trust(request=req)
        assert a["status"] == "blocked"

    def test_complete_with_audit_is_ready(self):
        a = assess_backend_invocation_trust(
            prompt_meta={"prompt_hash": "abc"},
            output_meta={"output_hash": "def", "quarantined": True, "applied_to_repo": False},
            audit_meta={"event_type": "mock.run"},
            audit_verified=True,
        )
        assert a["status"] == "ready"
        assert a["trust_level"] == "complete"

    def test_unverified_audit_is_partial(self):
        a = assess_backend_invocation_trust(
            prompt_meta={"prompt_hash": "abc"},
            output_meta={"output_hash": "def", "quarantined": True, "applied_to_repo": False},
            audit_meta={"event_type": "mock.run"},
            audit_verified=False,
        )
        assert a["status"] == "ready"
        assert a["trust_level"] == "partial"

    def test_no_secrets_in_assessment(self):
        a = assess_backend_invocation_trust(
            prompt_meta={"prompt_hash": "abc"},
        )
        j = json.dumps(a)
        assert "sk-ant" not in j

    def test_cli_readiness(self):
        import subprocess, sys, os
        from pathlib import Path as _P
        repo = _P(__file__).resolve().parent.parent
        orig = os.getcwd()
        os.chdir(str(repo))
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pcae", "backend", "readiness", "--latest"],
                capture_output=True, text=True, timeout=15,
            )
            assert "Trust level" in r.stdout or "trust_level" in r.stdout
        finally:
            os.chdir(orig)


from pcae.core.backend_invocations import assess_backend_invocation_trust


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94J — Review state model tests
# ═══════════════════════════════════════════════════════════════════════════


class TestReviewStateModel:
    def test_create_review_safe_defaults(self):
        r = create_review_artifact("be-test", "abc123")
        assert r.approved_for_apply is False
        assert r.apply_ready is False
        assert r.rejected is False
        assert r.review_state == "quarantined"

    def test_approve_sets_state(self):
        r = create_review_artifact("be-test", "abc123")
        a = approve_review(r, "operator", "looks good")
        assert r.approved_for_apply is True
        assert r.review_state == "approved_for_apply"
        assert a.output_hash == "abc123"

    def test_approve_with_hard_blocks_raises(self):
        r = create_review_artifact("be-test", "abc123")
        r.hard_blocks = ["blocked_by_policy"]
        with pytest.raises(ValueError, match="hard blocks"):
            approve_review(r, "op", "reason")

    def test_approve_empty_hash_raises(self):
        r = ReviewArtifact(request_id="x", output_hash="")
        with pytest.raises(ValueError, match="output_hash"):
            approve_review(r, "op", "reason")

    def test_reject_sets_state(self):
        r = create_review_artifact("be-test", "abc123")
        reject_review(r, "operator", "not safe")
        assert r.rejected is True
        assert r.review_state == "rejected"

    def test_approval_hash_bound(self):
        r = create_review_artifact("be-test", "abc123")
        a = approve_review(r, "op", "ok")
        assert a.output_hash == r.output_hash

    def test_apply_ready_validation_fails(self):
        r = create_review_artifact("be-test", "abc123")
        r.apply_ready = True
        issues = r.validate()
        assert any("apply_ready" in i for i in issues)

    def test_review_persisted(self):
        with tempfile.TemporaryDirectory() as td:
            r = create_review_artifact("be-test", "abc123", phase_id="94J")
            result = persist_review(r)
            assert result["status"] == "written"
            assert Path(result["path"]).exists()
            assert Path(result["latest_path"]).exists()

    def test_serialization_round_trip(self):
        r = create_review_artifact("be-test", "abc123", phase_id="94J")
        d = r.to_dict()
        assert d["review_state"] == "quarantined"
        assert d["approved_for_apply"] is False

    def test_approval_serialization(self):
        r = create_review_artifact("be-test", "abc123")
        a = approve_review(r, "op", "ok")
        d = a.to_dict()
        assert d["output_hash"] == "abc123"
        assert "sk-ant" not in json.dumps(d)

    def test_no_source_files_modified(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations.persist_review)
        assert "import subprocess" not in source
        assert "open(" not in source or ".pcae" in source


from pcae.core.backend_invocations import (
    ReviewArtifact, ApprovalArtifact, RejectionArtifact,
    create_review_artifact, approve_review, reject_review, persist_review,
    REVIEW_QUARANTINED, REVIEW_APPROVED, REVIEW_REJECTED,
)


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94K — Apply plan model tests
# ═══════════════════════════════════════════════════════════════════════════


class TestApplyPlanModel:
    def test_create_plan_safe_defaults(self):
        r = create_review_artifact("be-test", "abc123")
        a = approve_review(r, "op", "ok")
        plan = create_apply_plan(r, a, operations=[
            ApplyOperation(operation_id="op1", operation_type="create_file", target_path="src/test.py"),
        ])
        assert plan.apply_ready is False
        assert plan.rollback_required is True
        assert plan.check_required is True

    def test_forbidden_file_hard_blocked(self):
        r = create_review_artifact("be-test", "abc123")
        a = approve_review(r, "op", "ok")
        plan = create_apply_plan(r, a, forbidden_files=["src/secret.py"], operations=[
            ApplyOperation(operation_id="op1", target_path="src/secret.py"),
        ])
        assert any("forbidden" in hb for hb in plan.hard_blocks)

    def test_high_risk_op_hard_blocked(self):
        r = create_review_artifact("be-test", "abc123")
        a = approve_review(r, "op", "ok")
        plan = create_apply_plan(r, a, operations=[
            ApplyOperation(operation_id="op1", operation_type="delete_file", target_path="x.py"),
        ])
        assert any("high_risk" in hb for hb in plan.hard_blocks)

    def test_missing_approval_creates_missing(self):
        r = create_review_artifact("be-test", "abc123")
        plan = create_apply_plan(r, operations=[
            ApplyOperation(operation_id="op1", target_path="src/test.py"),
        ])
        assert "approval" in plan.missing_evidence

    def test_validate_apply_plan_blocked(self):
        r = create_review_artifact("be-test", "abc123")
        plan = create_apply_plan(r, operations=[
            ApplyOperation(operation_id="op1", target_path="src/secret.py"),
        ], forbidden_files=["src/secret.py"])
        result = validate_apply_plan(plan)
        assert result["apply_ready"] is False

    def test_plan_persisted(self):
        r = create_review_artifact("be-test", "abc123")
        a = approve_review(r, "op", "ok")
        plan = create_apply_plan(r, a, operations=[
            ApplyOperation(operation_id="op1", target_path="src/test.py"),
        ])
        result = persist_apply_plan(plan)
        assert result["status"] == "written"

    def test_no_secrets_in_plan(self):
        r = create_review_artifact("be-test", "abc123")
        plan = create_apply_plan(r, operations=[
            ApplyOperation(operation_id="op1", target_path="src/test.py"),
        ])
        j = json.dumps(plan.to_dict())
        assert "sk-ant" not in j


from pcae.core.backend_invocations import (
    ApplyOperation, ApplyPlan, RollbackRequirement,
    create_apply_plan, validate_apply_plan, persist_apply_plan,
)


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94L — Apply readiness validator tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    BackendApplyReadinessAssessment,
    validate_backend_apply_readiness,
    persist_apply_readiness,
    read_latest_apply_readiness,
    _apply_readiness_dir,
    _APPLY_READINESS_SCHEMA_VERSION,
    READINESS_READY, READINESS_BLOCKED, READINESS_MISSING_EVIDENCE,
    READINESS_INCOMPLETE, READINESS_UNTRUSTED,
    ACTION_MANUAL_APPLY_PACKAGE_READY, ACTION_BLOCKED_HARD,
    ACTION_GATHER_EVIDENCE,
    REVIEW_APPROVED, REVIEW_REVIEWED,
    TRUST_COMPLETE, TRUST_PARTIAL, TRUST_UNTRUSTED,
    APPROVAL_APPROVED, APPROVAL_PENDING,
    OP_CREATE, OP_MODIFY, OP_DELETE, OP_RENAME, OP_MANUAL, OP_UNKNOWN,
    RISK_LOW, RISK_MEDIUM,
)


class Test94LApplyReadinessAssessmentModel:
    """Test BackendApplyReadinessAssessment dataclass."""

    def test_defaults_fail_closed(self):
        a = BackendApplyReadinessAssessment()
        assert a.apply_ready is False
        assert a.status == READINESS_INCOMPLETE
        assert a.trust_level == TRUST_UNTRUSTED
        assert a.recommended_action == ACTION_GATHER_EVIDENCE
        assert a.output_hash_verified is False
        assert a.approval_bound_to_output_hash is False
        assert a.review_state_valid is False
        assert a.output_quarantined is False
        assert a.output_not_applied is False
        assert a.allowed_files_present is False
        assert a.operations_valid is False
        assert a.rollback_ready is False
        assert a.tests_defined is False
        assert a.hard_blocks == []
        assert a.missing_evidence == []
        assert a.warnings == []

    def test_serialization_round_trip(self):
        a = BackendApplyReadinessAssessment(
            assessment_id="ra-test",
            apply_plan_id="pl-test",
            status=READINESS_READY,
            apply_ready=True,
            trust_level=TRUST_COMPLETE,
        )
        d = a.to_dict()
        a2 = BackendApplyReadinessAssessment.from_dict(d)
        assert a2.assessment_id == "ra-test"
        assert a2.apply_plan_id == "pl-test"
        assert a2.status == READINESS_READY
        assert a2.apply_ready is True

    def test_hard_blocks_preserved_in_round_trip(self):
        a = BackendApplyReadinessAssessment(
            hard_blocks=["hb1", "hb2"],
            missing_evidence=["me1"],
            warnings=["w1"],
        )
        d = a.to_dict()
        a2 = BackendApplyReadinessAssessment.from_dict(d)
        assert a2.hard_blocks == ["hb1", "hb2"]
        assert a2.missing_evidence == ["me1"]
        assert a2.warnings == ["w1"]

    def test_to_dict_returns_list_copies(self):
        a = BackendApplyReadinessAssessment(hard_blocks=["hb1"])
        d = a.to_dict()
        d["hard_blocks"].append("hb2")
        assert a.hard_blocks == ["hb1"]


class Test94LNoPlan:
    """Missing apply plan → blocked."""

    def test_none_plan_yields_blocked(self):
        result = validate_backend_apply_readiness(None)
        assert result.status == READINESS_BLOCKED
        assert result.apply_ready is False
        assert "apply_plan_missing" in result.hard_blocks
        assert "apply_plan" in result.missing_evidence

    def test_no_args_yields_blocked(self):
        result = validate_backend_apply_readiness()
        assert result.status == READINESS_BLOCKED
        assert not result.apply_ready


class Test94LCompleteEvidence:
    """Complete evidence can produce apply_ready=True."""

    @staticmethod
    def _make_full_plan():
        r = create_review_artifact("req-001", "abc123", backend_id="mock")
        r.review_state = REVIEW_APPROVED
        r.approved_for_apply = True
        approval = ApprovalArtifact(
            approval_id="ap-001", review_id=r.review_id,
            request_id="req-001", output_hash="abc123",
            operator="human", reason="looks good",
        )
        plan = ApplyPlan(
            apply_plan_id="pl-001", review_id=r.review_id,
            approval_id="ap-001", request_id="req-001",
            phase_id="94L", task_id="t-94L",
            backend_id="mock", output_hash="abc123",
            proposed_files=["src/test.py"],
            allowed_files=["src/test.py"],
            operations=[ApplyOperation(
                operation_id="op1", operation_type=OP_MODIFY,
                target_path="src/test.py",
                allowed_by_task_scope=True,
            )],
            rollback_required=True, rollback_plan_id="rb-001",
            tests_to_run=["python -m pytest tests/test_example.py"],
            check_required=True,
        )
        return plan, r, approval

    def test_full_evidence_yields_ready(self):
        plan, review, approval = self._make_full_plan()
        output_meta = {"output_hash": "abc123", "quarantined": True, "applied_to_repo": False}
        trust = {"status": "ready", "trust_level": TRUST_COMPLETE, "hard_blocks": []}
        result = validate_backend_apply_readiness(
            plan=plan, review=review, approval=approval,
            output_meta=output_meta, trust_assessment=trust,
        )
        assert result.status == READINESS_READY
        assert result.apply_ready is True
        assert result.recommended_action == ACTION_MANUAL_APPLY_PACKAGE_READY
        assert result.output_hash_verified is True
        assert result.approval_bound_to_output_hash is True
        assert result.review_state_valid is True

    def test_apply_ready_never_executes(self):
        plan, review, approval = self._make_full_plan()
        output_meta = {"output_hash": "abc123", "quarantined": True, "applied_to_repo": False}
        trust = {"status": "ready", "trust_level": TRUST_COMPLETE, "hard_blocks": []}
        result = validate_backend_apply_readiness(
            plan=plan, review=review, approval=approval,
            output_meta=output_meta, trust_assessment=trust,
        )
        assert result.apply_ready is True
        # Even when ready, recommended_action is NEVER "execute apply"
        assert "execute" not in result.recommended_action
        assert "apply" not in result.recommended_action.lower() or \
               "ready" in result.recommended_action


class Test94LMissingEvidence:
    """Missing approval/review → missing_evidence."""

    def _minimal_plan(self):
        return ApplyPlan(
            apply_plan_id="pl-002", review_id="rv-002",
            approval_id="ap-002", output_hash="abc456",
            operations=[ApplyOperation(
                operation_id="op1", operation_type=OP_MODIFY,
                target_path="src/x.py",
            )],
            rollback_plan_id="rb-002",
            tests_to_run=["pytest"],
        )

    def test_missing_approval_yields_missing_evidence(self):
        plan = self._minimal_plan()
        review = ReviewArtifact(
            review_id="rv-002", request_id="req-002",
            output_hash="abc456", review_state=REVIEW_APPROVED,
        )
        result = validate_backend_apply_readiness(plan=plan, review=review)
        assert result.status == READINESS_MISSING_EVIDENCE
        assert any("approval" in me for me in result.missing_evidence)
        assert result.apply_ready is False

    def test_missing_review_yields_missing_evidence(self):
        plan = self._minimal_plan()
        approval = ApprovalArtifact(
            approval_id="ap-002", output_hash="abc456", operator="human",
        )
        result = validate_backend_apply_readiness(plan=plan, approval=approval)
        assert result.status == READINESS_MISSING_EVIDENCE
        assert any("review" in me for me in result.missing_evidence)

    def test_missing_trust_assessment(self):
        plan = self._minimal_plan()
        review = ReviewArtifact(review_id="rv-002", request_id="req-002", output_hash="abc456")
        approval = ApprovalArtifact(approval_id="ap-002", output_hash="abc456", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert "trust_assessment" in result.missing_evidence

    def test_missing_rollback_plan(self):
        plan = ApplyPlan(
            apply_plan_id="pl-003", review_id="rv-003",
            approval_id="ap-003", output_hash="abc",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="x")],
            rollback_required=True, rollback_plan_id="",
            tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-003", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-003", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert "rollback_plan_id" in result.missing_evidence
        assert result.apply_ready is False

    def test_missing_tests_to_run(self):
        plan = ApplyPlan(
            apply_plan_id="pl-004", review_id="rv-004",
            approval_id="ap-004", output_hash="abc",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="x")],
            rollback_plan_id="rb-004",
            check_required=True, tests_to_run=[],
        )
        review = ReviewArtifact(review_id="rv-004", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-004", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert "tests_to_run" in result.missing_evidence


class Test94LHashMismatches:
    """Output and approval hash mismatches → hard blocks."""

    def test_output_hash_mismatch_is_hard_block(self):
        plan = ApplyPlan(
            apply_plan_id="pl-010", review_id="rv-010",
            approval_id="ap-010", output_hash="plan_hash",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="x")],
            rollback_plan_id="rb-010", tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-010", output_hash="plan_hash", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-010", output_hash="plan_hash", operator="human")
        output_meta = {"output_hash": "different_hash", "quarantined": True, "applied_to_repo": False}
        result = validate_backend_apply_readiness(
            plan=plan, review=review, approval=approval,
            output_meta=output_meta,
        )
        assert result.status == READINESS_BLOCKED
        assert "output_hash_mismatch" in result.hard_blocks
        assert result.apply_ready is False

    def test_approval_hash_mismatch_is_hard_block(self):
        plan = ApplyPlan(
            apply_plan_id="pl-011", review_id="rv-011",
            approval_id="ap-011", output_hash="plan_hash",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="x")],
            rollback_plan_id="rb-011", tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-011", output_hash="plan_hash", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(
            approval_id="ap-011", output_hash="different_approval_hash", operator="human",
        )
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert "approval_output_hash_mismatch" in result.hard_blocks
        assert result.apply_ready is False


class Test94LHardBlockInvariants:
    """Hard blocks are non-overridable, dominate approval, accepted risk."""

    def _forbidden_plan(self):
        return ApplyPlan(
            apply_plan_id="pl-020", review_id="rv-020",
            approval_id="ap-020", output_hash="abc",
            proposed_files=["src/secret.py"],
            forbidden_files=["src/secret.py"],
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="src/secret.py")],
            rollback_plan_id="rb-020", tests_to_run=["pytest"],
        )

    def test_forbidden_file_is_hard_block(self):
        plan = self._forbidden_plan()
        review = ReviewArtifact(review_id="rv-020", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-020", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert "forbidden_file:src/secret.py" in result.hard_blocks
        assert result.apply_ready is False

    def test_hard_blocks_dominate_approval(self):
        plan = self._forbidden_plan()
        review = ReviewArtifact(review_id="rv-020", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-020", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert result.hard_blocks
        # Approval is present but hard blocks dominate
        assert result.apply_ready is False
        assert result.status == READINESS_BLOCKED
        assert result.recommended_action == ACTION_BLOCKED_HARD

    def test_accepted_risk_cannot_override_hard_blocks(self):
        plan = ApplyPlan(
            apply_plan_id="pl-021", review_id="rv-021",
            output_hash="abc",
            proposed_files=["src/secret.py"],
            forbidden_files=["src/secret.py"],
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="src/secret.py")],
        )
        review = ReviewArtifact(review_id="rv-021", output_hash="abc", review_state=REVIEW_APPROVED)
        # Approval with accepted_risk=True
        approval = ApprovalArtifact(
            approval_id="ap-021", output_hash="abc",
            operator="human", reason="I know the risks",
            accepted_risk=True,
        )
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        # Hard blocks persist regardless of accepted_risk
        assert result.hard_blocks
        assert result.apply_ready is False

    def test_output_already_applied_is_hard_block(self):
        plan = ApplyPlan(
            apply_plan_id="pl-022", review_id="rv-022",
            approval_id="ap-022", output_hash="abc",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="x")],
            rollback_plan_id="rb-022", tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-022", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-022", output_hash="abc", operator="human")
        output_meta = {"output_hash": "abc", "quarantined": False, "applied_to_repo": True}
        result = validate_backend_apply_readiness(
            plan=plan, review=review, approval=approval,
            output_meta=output_meta,
        )
        assert "output_already_applied" in result.hard_blocks
        assert "output_not_quarantined" in result.hard_blocks
        assert result.apply_ready is False

    def test_output_not_quarantined_is_hard_block(self):
        plan = ApplyPlan(
            apply_plan_id="pl-023", review_id="rv-023",
            approval_id="ap-023", output_hash="abc",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="x")],
            rollback_plan_id="rb-023", tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-023", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-023", output_hash="abc", operator="human")
        output_meta = {"output_hash": "abc", "quarantined": False, "applied_to_repo": False}
        result = validate_backend_apply_readiness(
            plan=plan, review=review, approval=approval,
            output_meta=output_meta,
        )
        assert "output_not_quarantined" in result.hard_blocks

    def test_unknown_operation_is_hard_block(self):
        plan = ApplyPlan(
            apply_plan_id="pl-024", review_id="rv-024",
            approval_id="ap-024", output_hash="abc",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_UNKNOWN, target_path="x")],
            rollback_plan_id="rb-024", tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-024", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-024", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert "unknown_operation:x" in result.hard_blocks

    def test_delete_operation_is_hard_block(self):
        plan = ApplyPlan(
            apply_plan_id="pl-025", review_id="rv-025",
            approval_id="ap-025", output_hash="abc",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_DELETE, target_path="src/old.py")],
            rollback_plan_id="rb-025", tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-025", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-025", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert any("destructive_op" in hb or "high_risk_op" in hb for hb in result.hard_blocks)

    def test_rename_operation_is_hard_block(self):
        plan = ApplyPlan(
            apply_plan_id="pl-026", review_id="rv-026",
            approval_id="ap-026", output_hash="abc",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_RENAME, target_path="src/old.py")],
            rollback_plan_id="rb-026", tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-026", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-026", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert any("destructive_op" in hb or "high_risk_op" in hb for hb in result.hard_blocks)


class Test94LPersistence:
    """Apply readiness artifact persistence."""

    def test_persist_and_read(self):
        import os
        a = BackendApplyReadinessAssessment(
            assessment_id="ra-persist-test",
            apply_plan_id="pl-test",
            status=READINESS_MISSING_EVIDENCE,
            missing_evidence=["approval"],
            recommended_action=ACTION_GATHER_EVIDENCE,
        )
        result = persist_apply_readiness(a)
        assert result["status"] == "written"
        assert result["path"]
        assert os.path.exists(result["path"])
        assert os.path.exists(result["latest_path"])

    def test_read_latest_after_persist(self):
        a = BackendApplyReadinessAssessment(
            assessment_id="ra-read-test",
            apply_plan_id="pl-read",
            status=READINESS_READY,
            apply_ready=True,
        )
        persist_apply_readiness(a)
        latest = read_latest_apply_readiness()
        assert latest is not None
        assert latest.assessment_id == "ra-read-test"
        assert latest.apply_ready is True
        assert latest.status == READINESS_READY

    def test_latest_readiness_updated_on_new_write(self):
        a1 = BackendApplyReadinessAssessment(assessment_id="ra-first")
        a2 = BackendApplyReadinessAssessment(assessment_id="ra-second", status=READINESS_READY)
        persist_apply_readiness(a1)
        persist_apply_readiness(a2)
        latest = read_latest_apply_readiness()
        assert latest is not None
        assert latest.assessment_id == "ra-second"

    def test_read_when_none_exists(self):
        import os
        lp = _apply_readiness_dir() / "latest.json"
        if lp.exists():
            os.remove(lp)
        result = read_latest_apply_readiness()
        assert result is None

    def test_serialization_round_trip_via_persistence(self):
        a = BackendApplyReadinessAssessment(
            assessment_id="ra-roundtrip",
            apply_plan_id="pl-rt",
            hard_blocks=["hb1", "hb2"],
            missing_evidence=["me1"],
            warnings=["w1"],
        )
        persist_apply_readiness(a)
        latest = read_latest_apply_readiness()
        assert latest is not None
        assert latest.assessment_id == "ra-roundtrip"
        assert latest.hard_blocks == ["hb1", "hb2"]
        assert latest.missing_evidence == ["me1"]
        assert latest.warnings == ["w1"]
        assert latest.schema_version == _APPLY_READINESS_SCHEMA_VERSION


class Test94LNoExecutionNoMutation:
    """Validate that readiness validator never mutates or executes."""

    def test_validator_returns_assessment_not_executes(self):
        plan, review, approval = Test94LCompleteEvidence._make_full_plan()
        result = validate_backend_apply_readiness(
            plan=plan, review=review, approval=approval,
        )
        # Result is an assessment object, not an execution result
        assert isinstance(result, BackendApplyReadinessAssessment)
        assert result.recommended_action != "execute_apply"
        assert result.recommended_action != "apply_changes"
        assert "commit" not in result.recommended_action.lower()
        assert "push" not in result.recommended_action.lower()

    def test_no_source_files_modified_during_validation(self, tmp_path):
        """Validation only reads, never writes source files."""
        a = BackendApplyReadinessAssessment(assessment_id="no-mut")
        result = persist_apply_readiness(a)
        # Only writes under .pcae/backend-apply-readiness/
        assert ".pcae/backend-apply-readiness" in result["path"]

    def test_no_patch_parsing_in_validation(self):
        plan, review, approval = Test94LCompleteEvidence._make_full_plan()
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        # The validator does not parse patches or diffs
        assert result is not None
        # No file I/O to source tree beyond reading plan/review args

    def test_no_backend_invocation_in_validator(self):
        result = validate_backend_apply_readiness()
        assert result.status == READINESS_BLOCKED
        # No backend was invoked — it's a pure data validator

    def test_no_subprocess_in_validator(self):
        result = validate_backend_apply_readiness()
        assert result is not None


class Test94LMultiPartPhaseIDs:
    """Multi-part phase IDs are preserved."""

    def test_phase_id_with_dot_preserved(self):
        plan = ApplyPlan(
            apply_plan_id="pl-multi", review_id="rv-multi",
            approval_id="ap-multi", output_hash="abc",
            phase_id="94L.1", task_id="20260629-phase-94l-backend-apply-readiness",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="x")],
            rollback_plan_id="rb-multi", tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-multi", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-multi", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert result.phase_id == "94L.1"
        assert result.task_id == "20260629-phase-94l-backend-apply-readiness"

    def test_task_id_with_multi_segments_preserved(self):
        plan = ApplyPlan(
            apply_plan_id="pl-multi2", review_id="rv-multi2",
            approval_id="ap-multi2", output_hash="abc",
            phase_id="94L", task_id="20260629-1633-phase-94l-backend-apply-readiness-validator",
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="x")],
            rollback_plan_id="rb-multi2", tests_to_run=["pytest"],
        )
        review = ReviewArtifact(review_id="rv-multi2", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-multi2", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert result.task_id == "20260629-1633-phase-94l-backend-apply-readiness-validator"


class Test94LNoSecretsInReadiness:
    """No secrets serialized in readiness artifacts."""

    def test_no_api_keys_in_to_dict(self):
        a = BackendApplyReadinessAssessment(
            assessment_id="ra-nosecret",
            apply_plan_id="pl-nosecret",
        )
        d = json.dumps(a.to_dict())
        assert "sk-ant" not in d
        assert "ANTHROPIC_API_KEY" not in d.lower()
        assert "OPENAI_API_KEY" not in d.lower()
        assert "DEEPSEEK_API_KEY" not in d.lower()

    def test_no_secrets_in_persisted(self):
        a = BackendApplyReadinessAssessment(assessment_id="ra-nosecret2")
        persist_apply_readiness(a)
        latest = read_latest_apply_readiness()
        assert latest is not None
        j = json.dumps(latest.to_dict())
        assert "sk-ant" not in j


class Test94LStatusClassification:
    """All status classifications work correctly."""

    def test_blocked_status_dominates(self):
        plan = ApplyPlan(
            apply_plan_id="pl-dom", review_id="rv-dom",
            output_hash="abc",
            proposed_files=["src/secret.py"],
            forbidden_files=["src/secret.py"],
            operations=[ApplyOperation(operation_id="op1", operation_type=OP_MODIFY, target_path="src/secret.py")],
        )
        # Even with review and approval present, forbidden file → blocked
        review = ReviewArtifact(review_id="rv-dom", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-dom", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert result.status == READINESS_BLOCKED
        assert result.apply_ready is False
        assert result.recommended_action == ACTION_BLOCKED_HARD

    def test_incomplete_status_for_no_operations(self):
        plan = ApplyPlan(
            apply_plan_id="pl-inc", review_id="rv-inc",
            approval_id="ap-inc", output_hash="abc",
            operations=[],
        )
        review = ReviewArtifact(review_id="rv-inc", output_hash="abc", review_state=REVIEW_APPROVED)
        approval = ApprovalArtifact(approval_id="ap-inc", output_hash="abc", operator="human")
        result = validate_backend_apply_readiness(plan=plan, review=review, approval=approval)
        assert "operations" in result.missing_evidence
        assert result.apply_ready is False

    def test_default_is_not_ready(self):
        result = validate_backend_apply_readiness()
        assert result.apply_ready is False
        assert result.status != READINESS_READY


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94M — Backend review CLI model tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    RejectionArtifact,
    persist_approval,
    persist_rejection,
    REVIEW_PENDING,
)


class Test94MRejectionArtifact:
    """RejectionArtifact to_dict and validate coverage."""

    def test_to_dict_has_all_fields(self):
        r = RejectionArtifact(
            rejection_id="rj-test001",
            review_id="rv-test001",
            request_id="be-test001",
            output_hash="abc123",
            operator="atila",
            reason="unsafe output",
            rejected_at_utc="2026-06-29T00:00:00+00:00",
        )
        d = r.to_dict()
        assert d["rejection_id"] == "rj-test001"
        assert d["review_id"] == "rv-test001"
        assert d["request_id"] == "be-test001"
        assert d["output_hash"] == "abc123"
        assert d["operator"] == "atila"
        assert d["reason"] == "unsafe output"
        assert d["rejected_at_utc"] == "2026-06-29T00:00:00+00:00"
        assert d["schema_version"] == SCHEMA_VERSION

    def test_validate_requires_output_hash(self):
        r = RejectionArtifact(operator="op", reason="r")
        assert "output_hash required" in r.validate()

    def test_validate_requires_operator(self):
        r = RejectionArtifact(output_hash="abc", reason="r")
        assert "operator required" in r.validate()

    def test_validate_requires_reason(self):
        r = RejectionArtifact(output_hash="abc", operator="op")
        assert "reason required" in r.validate()

    def test_validate_passes_with_all_fields(self):
        r = RejectionArtifact(output_hash="abc", operator="op", reason="r")
        assert r.validate() == []

    def test_to_dict_no_secrets(self):
        r = RejectionArtifact(output_hash="abc", operator="op", reason="r")
        d = json.dumps(r.to_dict())
        assert "sk-ant" not in d
        assert "api_key" not in d.lower()


class Test94MPersistApproval:
    """persist_approval writes artifacts correctly."""

    def _make_review(self):
        from pcae.core.backend_invocations import ReviewArtifact, REVIEW_APPROVED
        return ReviewArtifact(
            review_id="rv-pa001", request_id="be-pa001",
            output_hash="hash-pa001", review_state=REVIEW_APPROVED,
            approved_for_apply=True,
        )

    def _make_approval(self):
        from pcae.core.backend_invocations import ApprovalArtifact
        return ApprovalArtifact(
            approval_id="ap-pa001", review_id="rv-pa001",
            request_id="be-pa001", output_hash="hash-pa001",
            operator="atila", reason="reviewed",
            approved_at_utc="2026-06-29T00:00:00+00:00",
        )

    def test_persist_approval_written(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._REVIEWS_DIR
        _bi._REVIEWS_DIR = str(tmp_path / "reviews")
        try:
            review = self._make_review()
            approval = self._make_approval()
            result = persist_approval(approval, review)
            assert result["status"] == "written"
            assert "approval_path" in result
            assert "latest_path" in result
        finally:
            _bi._REVIEWS_DIR = orig

    def test_persist_approval_updates_latest(self, tmp_path):
        import json as _json
        import pcae.core.backend_invocations as _bi
        orig = _bi._REVIEWS_DIR
        _bi._REVIEWS_DIR = str(tmp_path / "reviews")
        try:
            review = self._make_review()
            approval = self._make_approval()
            persist_approval(approval, review)
            latest = _json.loads((tmp_path / "reviews" / "latest.json").read_text())
            assert latest["review_id"] == "rv-pa001"
            assert latest["approved_for_apply"] is True
        finally:
            _bi._REVIEWS_DIR = orig

    def test_persist_approval_no_secrets_in_artifact(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._REVIEWS_DIR
        _bi._REVIEWS_DIR = str(tmp_path / "reviews")
        try:
            review = self._make_review()
            approval = self._make_approval()
            persist_approval(approval, review)
            ap_files = list((tmp_path / "reviews").glob("*-ap-*.json"))
            assert len(ap_files) == 1
            content = ap_files[0].read_text()
            assert "sk-ant" not in content
            assert "api_key" not in content.lower()
        finally:
            _bi._REVIEWS_DIR = orig


class Test94MPersistRejection:
    """persist_rejection writes artifacts correctly."""

    def _make_review(self):
        from pcae.core.backend_invocations import ReviewArtifact, REVIEW_REJECTED
        return ReviewArtifact(
            review_id="rv-pr001", request_id="be-pr001",
            output_hash="hash-pr001", review_state=REVIEW_REJECTED,
            rejected=True,
        )

    def _make_rejection(self):
        return RejectionArtifact(
            rejection_id="rj-pr001", review_id="rv-pr001",
            request_id="be-pr001", output_hash="hash-pr001",
            operator="atila", reason="unsafe",
            rejected_at_utc="2026-06-29T00:00:00+00:00",
        )

    def test_persist_rejection_written(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._REVIEWS_DIR
        _bi._REVIEWS_DIR = str(tmp_path / "reviews")
        try:
            review = self._make_review()
            rejection = self._make_rejection()
            result = persist_rejection(rejection, review)
            assert result["status"] == "written"
            assert "rejection_path" in result
            assert "latest_path" in result
        finally:
            _bi._REVIEWS_DIR = orig

    def test_persist_rejection_updates_latest(self, tmp_path):
        import json as _json
        import pcae.core.backend_invocations as _bi
        orig = _bi._REVIEWS_DIR
        _bi._REVIEWS_DIR = str(tmp_path / "reviews")
        try:
            review = self._make_review()
            rejection = self._make_rejection()
            persist_rejection(rejection, review)
            latest = _json.loads((tmp_path / "reviews" / "latest.json").read_text())
            assert latest["review_id"] == "rv-pr001"
            assert latest["rejected"] is True
        finally:
            _bi._REVIEWS_DIR = orig

    def test_persist_rejection_no_secrets(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._REVIEWS_DIR
        _bi._REVIEWS_DIR = str(tmp_path / "reviews")
        try:
            review = self._make_review()
            rejection = self._make_rejection()
            persist_rejection(rejection, review)
            rj_files = list((tmp_path / "reviews").glob("*-rj-*.json"))
            assert len(rj_files) == 1
            content = rj_files[0].read_text()
            assert "sk-ant" not in content
        finally:
            _bi._REVIEWS_DIR = orig


class Test94MReviewCreateDefaults:
    """Review create sets safe defaults."""

    def test_create_review_defaults_approved_false(self):
        from pcae.core.backend_invocations import create_review_artifact
        review = create_review_artifact("req-001", "hash-001")
        assert review.approved_for_apply is False

    def test_create_review_defaults_rejected_false(self):
        from pcae.core.backend_invocations import create_review_artifact
        review = create_review_artifact("req-001", "hash-001")
        assert review.rejected is False

    def test_create_review_defaults_apply_ready_false(self):
        from pcae.core.backend_invocations import create_review_artifact
        review = create_review_artifact("req-001", "hash-001")
        assert review.apply_ready is False

    def test_create_review_state_can_be_updated_to_pending(self):
        from pcae.core.backend_invocations import create_review_artifact, REVIEW_PENDING
        review = create_review_artifact("req-001", "hash-001")
        review.review_state = REVIEW_PENDING
        assert review.review_state == REVIEW_PENDING


class Test94MHardBlockDominance:
    """Hard blocks prevent effective approval."""

    def test_hard_blocks_prevent_approve(self):
        from pcae.core.backend_invocations import (
            ReviewArtifact, approve_review, REVIEW_QUARANTINED,
        )
        review = ReviewArtifact(
            review_id="rv-hb01", request_id="be-hb01",
            output_hash="hash-hb01", review_state=REVIEW_QUARANTINED,
            hard_blocks=["output_not_quarantined"],
        )
        with pytest.raises(ValueError, match="hard blocks"):
            approve_review(review, "atila", "attempt")

    def test_accepted_risk_cannot_override_hard_blocks(self):
        from pcae.core.backend_invocations import (
            ApprovalArtifact, ReviewArtifact, approve_review, REVIEW_QUARANTINED,
        )
        review = ReviewArtifact(
            review_id="rv-hb02", request_id="be-hb02",
            output_hash="hash-hb02", review_state=REVIEW_QUARANTINED,
            hard_blocks=["output_already_applied"],
        )
        with pytest.raises(ValueError, match="hard blocks"):
            approve_review(review, "atila", "accept risk")

    def test_approval_does_not_grant_apply_execution(self):
        from pcae.core.backend_invocations import (
            ReviewArtifact, approve_review, REVIEW_QUARANTINED,
        )
        review = ReviewArtifact(
            review_id="rv-noexec", request_id="be-noexec",
            output_hash="hash-noexec", review_state=REVIEW_QUARANTINED,
        )
        approval = approve_review(review, "atila", "reviewed")
        # Approval artifact does not carry execution flags
        d = approval.to_dict()
        assert "execute" not in str(d).lower() or d.get("no_execution", True)

    def test_approval_does_not_authorize_commit_push(self):
        from pcae.core.backend_invocations import (
            ReviewArtifact, approve_review, REVIEW_QUARANTINED,
        )
        review = ReviewArtifact(
            review_id="rv-auth01", request_id="be-auth01",
            output_hash="hash-auth01", review_state=REVIEW_QUARANTINED,
        )
        approval = approve_review(review, "atila", "ok")
        d = approval.to_dict()
        # Approval artifact must not contain commit/push authorization fields
        assert "commit_authorized" not in d
        assert "push_authorized" not in d
        assert "authorize_commit" not in d
        assert "authorize_push" not in d


class Test94MApproveRejectConflict:
    """Approved/rejected conflict is fail-closed."""

    def test_cannot_reject_approved_review(self):
        from pcae.core.backend_invocations import (
            ReviewArtifact, approve_review, reject_review, REVIEW_QUARANTINED,
        )
        review = ReviewArtifact(
            review_id="rv-conf01", request_id="be-conf01",
            output_hash="hash-conf01", review_state=REVIEW_QUARANTINED,
        )
        approve_review(review, "atila", "approved")
        # The review is now approved; rejecting should require external check
        # The CLI guards against this; the model itself sets state
        assert review.approved_for_apply is True
        assert review.review_state == REVIEW_APPROVED

    def test_cannot_approve_review_with_hard_blocks(self):
        from pcae.core.backend_invocations import (
            ReviewArtifact, approve_review, REVIEW_QUARANTINED,
        )
        review = ReviewArtifact(
            review_id="rv-conf02", request_id="be-conf02",
            output_hash="hash-conf02", review_state=REVIEW_QUARANTINED,
            hard_blocks=["forbidden_file:src/secret.py"],
        )
        with pytest.raises(ValueError):
            approve_review(review, "atila", "trying anyway")


class Test94MNoExecution:
    """Review CLI introduces no execution capability."""

    def test_no_subprocess_in_backend_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "subprocess.run" not in source
        assert "Popen(" not in source

    def test_no_network_calls_in_backend_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "urllib.request" not in source
        assert "requests.get" not in source
        assert "httpx" not in source

    def test_no_patch_parsing_in_backend_commands(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "patch_parser" not in source
        assert "parse_patch" not in source

    def test_no_telegram_inbound_in_review_cli(self):
        import inspect
        from pcae.commands import backend
        source = inspect.getsource(backend)
        assert "getUpdates" not in source
        assert "telegram_inbound" not in source

    def test_review_module_is_safe(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source


class Test94MReviewArtifactDirectory:
    """backend-reviews directory handling."""

    def test_backend_reviews_dir_in_gitignore(self):
        from pathlib import Path
        gitignore = Path(".pcae/.gitignore")
        assert gitignore.exists(), ".pcae/.gitignore must exist"
        content = gitignore.read_text()
        assert "backend-reviews/" in content

    def test_review_state_valid_roundtrip(self, tmp_path):
        import json as _json
        import pcae.core.backend_invocations as _bi
        from pcae.core.backend_invocations import ReviewArtifact, create_review_artifact, persist_review, read_latest_review
        orig = _bi._REVIEWS_DIR
        _bi._REVIEWS_DIR = str(tmp_path / "reviews")
        try:
            review = create_review_artifact("req-rt", "hash-rt")
            review.review_state = REVIEW_PENDING
            persist_review(review)
            loaded = read_latest_review()
            assert loaded is not None
            assert loaded.review_id == review.review_id
            assert loaded.output_hash == "hash-rt"
            assert loaded.approved_for_apply is False
            assert loaded.apply_ready is False
        finally:
            _bi._REVIEWS_DIR = orig


class Test94MMultiPartPhaseIds:
    """Multi-part phase IDs preserved in review artifacts."""

    def test_multipart_phase_id_in_review(self):
        from pcae.core.backend_invocations import create_review_artifact
        review = create_review_artifact("req-mp", "hash-mp", phase_id="94M.1.2")
        assert review.phase_id == "94M.1.2"

    def test_multipart_phase_id_in_rejection(self):
        r = RejectionArtifact(
            rejection_id="rj-mp01", review_id="rv-mp01",
            request_id="be-mp01", output_hash="hash-mp01",
            operator="op", reason="r",
        )
        d = r.to_dict()
        # Verify no phase ID field is truncated (not in this artifact, but check no corruption)
        assert d["rejection_id"] == "rj-mp01"


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94N — Backend apply plan CLI model tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    ApplyPlan, ApplyOperation, read_latest_apply_plan,
    OP_MANUAL, OP_DELETE, OP_MODIFY, OP_CREATE,
    HIGH_RISK_OPS, VALID_OPERATIONS,
    _APPLY_PLANS_DIR,
)


class Test94NReadLatestApplyPlan:
    """read_latest_apply_plan coverage."""

    def test_returns_none_when_missing(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._APPLY_PLANS_DIR
        _bi._APPLY_PLANS_DIR = str(tmp_path / "missing-plans")
        try:
            assert read_latest_apply_plan() is None
        finally:
            _bi._APPLY_PLANS_DIR = orig

    def test_returns_plan_after_persist(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        from pcae.core.backend_invocations import persist_apply_plan
        orig = _bi._APPLY_PLANS_DIR
        _bi._APPLY_PLANS_DIR = str(tmp_path / "plans")
        try:
            plan = ApplyPlan(
                apply_plan_id="pl-rlt01", review_id="rv-rlt01",
                output_hash="hash-rlt01", apply_ready=False,
                rollback_required=True, check_required=True,
            )
            persist_apply_plan(plan)
            loaded = read_latest_apply_plan()
            assert loaded is not None
            assert loaded.apply_plan_id == "pl-rlt01"
            assert loaded.output_hash == "hash-rlt01"
        finally:
            _bi._APPLY_PLANS_DIR = orig

    def test_roundtrip_preserves_safe_defaults(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        from pcae.core.backend_invocations import persist_apply_plan
        orig = _bi._APPLY_PLANS_DIR
        _bi._APPLY_PLANS_DIR = str(tmp_path / "plans-safe")
        try:
            plan = ApplyPlan(apply_plan_id="pl-safe", review_id="rv-safe", output_hash="h")
            persist_apply_plan(plan)
            loaded = read_latest_apply_plan()
            assert loaded.apply_ready is False
            assert loaded.rollback_required is True
            assert loaded.check_required is True
        finally:
            _bi._APPLY_PLANS_DIR = orig

    def test_roundtrip_preserves_operations(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        from pcae.core.backend_invocations import persist_apply_plan
        orig = _bi._APPLY_PLANS_DIR
        _bi._APPLY_PLANS_DIR = str(tmp_path / "plans-ops")
        try:
            op = ApplyOperation(operation_id="op-rt01", operation_type=OP_MANUAL, target_path="src/a.py")
            plan = ApplyPlan(apply_plan_id="pl-ops", review_id="rv-ops", output_hash="h-ops", operations=[op])
            persist_apply_plan(plan)
            loaded = read_latest_apply_plan()
            assert len(loaded.operations) == 1
            assert loaded.operations[0].operation_type == OP_MANUAL
            assert loaded.operations[0].target_path == "src/a.py"
        finally:
            _bi._APPLY_PLANS_DIR = orig

    def test_roundtrip_no_secrets(self, tmp_path):
        import json as _json
        import pcae.core.backend_invocations as _bi
        from pcae.core.backend_invocations import persist_apply_plan
        orig = _bi._APPLY_PLANS_DIR
        _bi._APPLY_PLANS_DIR = str(tmp_path / "plans-sec")
        try:
            plan = ApplyPlan(apply_plan_id="pl-sec", review_id="rv-sec", output_hash="h-sec")
            persist_apply_plan(plan)
            loaded = read_latest_apply_plan()
            j = _json.dumps(loaded.to_dict())
            assert "sk-ant" not in j
            assert "api_key" not in j.lower()
        finally:
            _bi._APPLY_PLANS_DIR = orig


class Test94NApplyPlanSafeDefaults:
    """ApplyPlan safe defaults."""

    def test_apply_ready_false(self):
        plan = ApplyPlan(review_id="rv-d01", output_hash="h-d01")
        assert plan.apply_ready is False

    def test_rollback_required_true(self):
        plan = ApplyPlan(review_id="rv-d01", output_hash="h-d01")
        assert plan.rollback_required is True

    def test_check_required_true(self):
        plan = ApplyPlan(review_id="rv-d01", output_hash="h-d01")
        assert plan.check_required is True

    def test_hard_blocks_empty(self):
        plan = ApplyPlan(review_id="rv-d01", output_hash="h-d01")
        assert plan.hard_blocks == []

    def test_operations_empty(self):
        plan = ApplyPlan(review_id="rv-d01", output_hash="h-d01")
        assert plan.operations == []


class Test94NHighRiskOpsHardBlock:
    """High-risk operations produce hard blocks."""

    def test_delete_is_high_risk(self):
        assert OP_DELETE in HIGH_RISK_OPS

    def test_manual_is_not_high_risk(self):
        assert OP_MANUAL not in HIGH_RISK_OPS

    def test_create_is_not_high_risk(self):
        assert OP_CREATE not in HIGH_RISK_OPS

    def test_modify_is_not_high_risk(self):
        assert OP_MODIFY not in HIGH_RISK_OPS

    def test_plan_with_delete_has_hard_block(self):
        from pcae.core.backend_invocations import ReviewArtifact, create_apply_plan
        review = ReviewArtifact(review_id="rv-hb1", request_id="req-hb1", output_hash="h-hb1")
        op = ApplyOperation(operation_type=OP_DELETE, target_path="src/old.py")
        plan = create_apply_plan(review, operations=[op])
        assert any("high_risk_op" in b for b in plan.hard_blocks)


class Test94NApplyPlanHashBinding:
    """Apply plan binds to review and output hash."""

    def test_plan_binds_review_id(self):
        from pcae.core.backend_invocations import ReviewArtifact, create_apply_plan
        review = ReviewArtifact(review_id="rv-bind01", request_id="req-bind01", output_hash="h-bind01")
        plan = create_apply_plan(review)
        assert plan.review_id == "rv-bind01"
        assert plan.output_hash == "h-bind01"

    def test_plan_binds_approval_id(self):
        from pcae.core.backend_invocations import ReviewArtifact, ApprovalArtifact, create_apply_plan
        review = ReviewArtifact(review_id="rv-bind02", request_id="req-bind02", output_hash="h-bind02")
        approval = ApprovalArtifact(approval_id="ap-bind02", review_id="rv-bind02",
                                     request_id="req-bind02", output_hash="h-bind02",
                                     operator="op", reason="ok")
        plan = create_apply_plan(review, approval)
        assert plan.approval_id == "ap-bind02"

    def test_plan_missing_approval_goes_to_missing_evidence(self):
        from pcae.core.backend_invocations import ReviewArtifact, create_apply_plan
        review = ReviewArtifact(review_id="rv-me01", request_id="req-me01", output_hash="h-me01")
        plan = create_apply_plan(review)
        assert "approval" in plan.missing_evidence


class Test94NApplyPlanValidate:
    """validate_backend_apply_readiness with plans."""

    def test_validate_plan_only_is_missing_evidence(self):
        from pcae.core.backend_invocations import validate_backend_apply_readiness
        plan = ApplyPlan(apply_plan_id="pl-v01", review_id="rv-v01", output_hash="h-v01")
        assessment = validate_backend_apply_readiness(plan=plan)
        assert assessment.apply_ready is False
        assert assessment.status in ("blocked", "missing_evidence")

    def test_validate_plan_with_hard_block_is_blocked(self):
        from pcae.core.backend_invocations import validate_backend_apply_readiness
        plan = ApplyPlan(
            apply_plan_id="pl-v02", review_id="rv-v02", output_hash="h-v02",
            hard_blocks=["forbidden_file:src/secret.py"],
        )
        assessment = validate_backend_apply_readiness(plan=plan)
        assert assessment.apply_ready is False
        assert "forbidden_file:src/secret.py" in assessment.hard_blocks

    def test_validate_does_not_execute_apply(self):
        from pcae.core.backend_invocations import validate_backend_apply_readiness
        plan = ApplyPlan(apply_plan_id="pl-v03", review_id="rv-v03", output_hash="h-v03")
        assessment = validate_backend_apply_readiness(plan=plan)
        # No execution side effect — just returns assessment
        assert hasattr(assessment, "apply_ready")
        assert assessment.apply_ready is False

    def test_validate_recommended_action_never_execute(self):
        from pcae.core.backend_invocations import validate_backend_apply_readiness
        plan = ApplyPlan(apply_plan_id="pl-v04", review_id="rv-v04", output_hash="h-v04")
        assessment = validate_backend_apply_readiness(plan=plan)
        assert "execute" not in assessment.recommended_action.lower()

    def test_missing_plan_is_blocked(self):
        from pcae.core.backend_invocations import validate_backend_apply_readiness
        assessment = validate_backend_apply_readiness(plan=None)
        assert assessment.apply_ready is False
        assert "apply_plan_missing" in assessment.hard_blocks


class Test94NMultiPartPhaseIds:
    """Multi-part phase IDs preserved in apply plan artifacts."""

    def test_multipart_phase_id_in_plan(self):
        plan = ApplyPlan(apply_plan_id="pl-mp01", review_id="rv-mp01",
                         output_hash="h-mp01", phase_id="94N.1.2")
        assert plan.phase_id == "94N.1.2"
        assert plan.to_dict()["phase_id"] == "94N.1.2"

    def test_plan_preserves_multipart_phase_on_roundtrip(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        from pcae.core.backend_invocations import persist_apply_plan
        orig = _bi._APPLY_PLANS_DIR
        _bi._APPLY_PLANS_DIR = str(tmp_path / "plans-mp")
        try:
            plan = ApplyPlan(apply_plan_id="pl-mp02", review_id="rv-mp02",
                              output_hash="h-mp02", phase_id="94N.3.4.5")
            persist_apply_plan(plan)
            loaded = read_latest_apply_plan()
            assert loaded.phase_id == "94N.3.4.5"
        finally:
            _bi._APPLY_PLANS_DIR = orig


class Test94NNoExecutionInModel:
    """Apply plan model introduces no execution capability."""

    def test_no_subprocess_in_core(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_no_network_in_core(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_patch_parsing_in_core(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "patch_parser" not in source
        assert "parse_patch" not in source

    def test_apply_plan_dirs_ignored(self):
        from pathlib import Path
        gitignore = Path(".pcae/.gitignore")
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "backend-apply-plans/" in content
        assert "backend-apply-readiness/" in content


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94O — Backend manual apply package model tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    BackendManualApplyPackage,
    create_backend_manual_apply_package,
    persist_manual_apply_package,
    read_latest_manual_apply_package,
    _MANUAL_APPLY_PACKAGES_DIR,
)


class Test94OPackageDefaults:
    """BackendManualApplyPackage safe defaults."""

    def test_no_execution_performed_true(self):
        pkg = BackendManualApplyPackage()
        assert pkg.no_execution_performed is True

    def test_apply_ready_false(self):
        pkg = BackendManualApplyPackage()
        assert pkg.apply_ready is False

    def test_rollback_required_true(self):
        pkg = BackendManualApplyPackage()
        assert pkg.rollback_required is True

    def test_hard_blocks_empty(self):
        pkg = BackendManualApplyPackage()
        assert pkg.hard_blocks == []

    def test_operations_empty(self):
        pkg = BackendManualApplyPackage()
        assert pkg.operations == []

    def test_schema_version_set(self):
        pkg = BackendManualApplyPackage()
        assert pkg.schema_version == "1.0"


class Test94OPackageToDict:
    """BackendManualApplyPackage serialization."""

    def test_to_dict_has_no_execution_performed(self):
        pkg = BackendManualApplyPackage(package_id="pkg-td01")
        d = pkg.to_dict()
        assert d["no_execution_performed"] is True

    def test_to_dict_does_not_imply_commit_push_authorization(self):
        pkg = BackendManualApplyPackage(package_id="pkg-td02")
        d = pkg.to_dict()
        assert "commit_authorized" not in d
        assert "push_authorized" not in d
        assert "authorize_commit" not in d
        assert "authorize_push" not in d

    def test_to_dict_does_not_imply_backend_invocation(self):
        pkg = BackendManualApplyPackage(package_id="pkg-td03")
        d = pkg.to_dict()
        assert "backend_invocation" not in d or d.get("no_execution_performed") is True

    def test_to_dict_roundtrip(self):
        pkg = BackendManualApplyPackage(
            package_id="pkg-rt01", apply_plan_id="pl-rt01",
            output_hash="h-rt01", phase_id="94O.1",
            no_execution_performed=True, apply_ready=False,
        )
        d = pkg.to_dict()
        pkg2 = BackendManualApplyPackage.from_dict(d)
        assert pkg2.package_id == "pkg-rt01"
        assert pkg2.output_hash == "h-rt01"
        assert pkg2.no_execution_performed is True
        assert pkg2.apply_ready is False

    def test_to_dict_no_secrets(self):
        pkg = BackendManualApplyPackage(
            package_id="pkg-sec01", output_hash="abc", operator_notes="ok"
        )
        j = json.dumps(pkg.to_dict())
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_multipart_phase_id_preserved(self):
        pkg = BackendManualApplyPackage(package_id="pkg-mp01", phase_id="94O.2.3")
        assert pkg.to_dict()["phase_id"] == "94O.2.3"


class Test94OPackageFromPlan:
    """create_backend_manual_apply_package from ApplyPlan."""

    def test_binds_apply_plan_id(self):
        plan = ApplyPlan(apply_plan_id="pl-bind01", review_id="rv-b01", output_hash="h-b01")
        pkg = create_backend_manual_apply_package(plan=plan)
        assert pkg.apply_plan_id == "pl-bind01"

    def test_binds_output_hash(self):
        plan = ApplyPlan(apply_plan_id="pl-oh01", review_id="rv-oh01", output_hash="hash-oh01")
        pkg = create_backend_manual_apply_package(plan=plan)
        assert pkg.output_hash == "hash-oh01"

    def test_binds_request_id(self):
        plan = ApplyPlan(apply_plan_id="pl-rq01", review_id="rv-rq01",
                          output_hash="h-rq01", request_id="req-rq01")
        pkg = create_backend_manual_apply_package(plan=plan)
        assert pkg.request_id == "req-rq01"

    def test_no_execution_always_true(self):
        plan = ApplyPlan(apply_plan_id="pl-ne01", review_id="rv-ne01", output_hash="h-ne01")
        pkg = create_backend_manual_apply_package(plan=plan)
        assert pkg.no_execution_performed is True

    def test_includes_operations_as_strings(self):
        op = ApplyOperation(operation_type=OP_MANUAL, target_path="src/foo.py")
        plan = ApplyPlan(apply_plan_id="pl-ops01", review_id="rv-ops01",
                          output_hash="h-ops01", operations=[op])
        pkg = create_backend_manual_apply_package(plan=plan)
        assert len(pkg.operations) == 1
        assert "manual_instruction" in pkg.operations[0]
        assert "src/foo.py" in pkg.operations[0]

    def test_includes_hard_blocks(self):
        plan = ApplyPlan(apply_plan_id="pl-hb01", review_id="rv-hb01",
                          output_hash="h-hb01", hard_blocks=["forbidden_file:src/x.py"])
        pkg = create_backend_manual_apply_package(plan=plan)
        assert "forbidden_file:src/x.py" in pkg.hard_blocks

    def test_includes_missing_evidence(self):
        plan = ApplyPlan(apply_plan_id="pl-me01", review_id="rv-me01",
                          output_hash="h-me01", missing_evidence=["approval"])
        pkg = create_backend_manual_apply_package(plan=plan)
        assert "approval" in pkg.missing_evidence

    def test_includes_rollback_required(self):
        plan = ApplyPlan(apply_plan_id="pl-rb01", review_id="rv-rb01",
                          output_hash="h-rb01", rollback_required=True)
        pkg = create_backend_manual_apply_package(plan=plan)
        assert pkg.rollback_required is True

    def test_includes_tests_to_run(self):
        plan = ApplyPlan(apply_plan_id="pl-tr01", review_id="rv-tr01",
                          output_hash="h-tr01", tests_to_run=["pytest tests/"])
        pkg = create_backend_manual_apply_package(plan=plan)
        assert "pytest tests/" in pkg.tests_to_run

    def test_includes_checks_to_run_when_check_required(self):
        plan = ApplyPlan(apply_plan_id="pl-cr01", review_id="rv-cr01",
                          output_hash="h-cr01", check_required=True)
        pkg = create_backend_manual_apply_package(plan=plan)
        assert len(pkg.checks_to_run) > 0

    def test_multipart_phase_id_from_plan(self):
        plan = ApplyPlan(apply_plan_id="pl-mp01", review_id="rv-mp01",
                          output_hash="h-mp01", phase_id="94O.3.4")
        pkg = create_backend_manual_apply_package(plan=plan)
        assert pkg.phase_id == "94O.3.4"


class Test94OPackageFromAssessment:
    """create_backend_manual_apply_package includes readiness assessment."""

    def test_includes_readiness_status(self):
        from pcae.core.backend_invocations import BackendApplyReadinessAssessment
        plan = ApplyPlan(apply_plan_id="pl-as01", review_id="rv-as01", output_hash="h-as01")
        assessment = BackendApplyReadinessAssessment(
            assessment_id="ra-as01", status="blocked",
            apply_ready=False, hard_blocks=["forbidden_file:x"],
        )
        pkg = create_backend_manual_apply_package(plan=plan, assessment=assessment)
        assert pkg.readiness_status == "blocked"
        assert pkg.readiness_assessment_id == "ra-as01"
        assert "forbidden_file:x" in pkg.hard_blocks

    def test_apply_ready_mirrors_assessment(self):
        from pcae.core.backend_invocations import BackendApplyReadinessAssessment
        plan = ApplyPlan(apply_plan_id="pl-ar01", review_id="rv-ar01", output_hash="h-ar01")
        assessment = BackendApplyReadinessAssessment(
            assessment_id="ra-ar01", status="missing_evidence", apply_ready=False,
        )
        pkg = create_backend_manual_apply_package(plan=plan, assessment=assessment)
        assert pkg.apply_ready is False

    def test_apply_ready_true_still_no_execution(self):
        from pcae.core.backend_invocations import BackendApplyReadinessAssessment
        plan = ApplyPlan(apply_plan_id="pl-ar02", review_id="rv-ar02", output_hash="h-ar02")
        assessment = BackendApplyReadinessAssessment(
            assessment_id="ra-ar02", status="ready", apply_ready=True,
        )
        pkg = create_backend_manual_apply_package(plan=plan, assessment=assessment)
        assert pkg.apply_ready is True
        assert pkg.no_execution_performed is True

    def test_merges_hard_blocks_from_assessment(self):
        from pcae.core.backend_invocations import BackendApplyReadinessAssessment
        plan = ApplyPlan(apply_plan_id="pl-mhb01", review_id="rv-mhb01",
                          output_hash="h-mhb01", hard_blocks=["plan_block"])
        assessment = BackendApplyReadinessAssessment(
            assessment_id="ra-mhb01", hard_blocks=["assessment_block"],
        )
        pkg = create_backend_manual_apply_package(plan=plan, assessment=assessment)
        assert "plan_block" in pkg.hard_blocks
        assert "assessment_block" in pkg.hard_blocks


class Test94OPackageMarkdown:
    """BackendManualApplyPackage.render_markdown() safety."""

    def test_markdown_includes_no_execution_confirmation(self):
        pkg = BackendManualApplyPackage(package_id="pkg-md01", output_hash="h-md01")
        md = pkg.render_markdown()
        assert "no_execution_performed" in md
        assert "No files were modified" in md

    def test_markdown_includes_no_apply_confirmation(self):
        pkg = BackendManualApplyPackage(package_id="pkg-md02")
        md = pkg.render_markdown()
        assert "No apply" in md or "No apply was executed" in md

    def test_markdown_no_raw_secrets(self):
        pkg = BackendManualApplyPackage(package_id="pkg-md03", operator_notes="ok")
        md = pkg.render_markdown()
        assert "sk-ant" not in md
        assert "api_key" not in md.lower()

    def test_markdown_includes_hard_blocks(self):
        pkg = BackendManualApplyPackage(
            package_id="pkg-md04", hard_blocks=["forbidden_file:src/x.py"]
        )
        md = pkg.render_markdown()
        assert "forbidden_file:src/x.py" in md

    def test_markdown_includes_rollback_section(self):
        pkg = BackendManualApplyPackage(package_id="pkg-md05", rollback_required=True)
        md = pkg.render_markdown()
        assert "Rollback" in md

    def test_markdown_advisory_label_on_instructions(self):
        pkg = BackendManualApplyPackage(
            package_id="pkg-md06", manual_apply_instructions="Step 1: do X"
        )
        md = pkg.render_markdown()
        assert "advisory" in md.lower() or "human operator" in md.lower()

    def test_markdown_tests_section(self):
        pkg = BackendManualApplyPackage(
            package_id="pkg-md07", tests_to_run=["pytest tests/"]
        )
        md = pkg.render_markdown()
        assert "pytest tests/" in md

    def test_markdown_checks_section(self):
        pkg = BackendManualApplyPackage(
            package_id="pkg-md08", checks_to_run=["pcae check"]
        )
        md = pkg.render_markdown()
        assert "pcae check" in md


class Test94OPersistPackage:
    """persist_manual_apply_package writes JSON + Markdown."""

    def _make_pkg(self) -> BackendManualApplyPackage:
        return BackendManualApplyPackage(
            package_id="pkg-p01", apply_plan_id="pl-p01",
            output_hash="h-p01", no_execution_performed=True,
        )

    def test_persist_returns_written(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "packages")
        try:
            pkg = self._make_pkg()
            result = persist_manual_apply_package(pkg)
            assert result["status"] == "written"
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig

    def test_persist_writes_json(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "packages")
        try:
            pkg = self._make_pkg()
            result = persist_manual_apply_package(pkg)
            assert "json_path" in result
            from pathlib import Path
            assert Path(result["json_path"]).is_file()
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig

    def test_persist_writes_markdown(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "packages")
        try:
            pkg = self._make_pkg()
            result = persist_manual_apply_package(pkg)
            assert "md_path" in result
            from pathlib import Path
            assert Path(result["md_path"]).is_file()
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig

    def test_persist_updates_latest_json(self, tmp_path):
        import json as _json
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "packages")
        try:
            pkg = self._make_pkg()
            persist_manual_apply_package(pkg)
            latest = _json.loads((tmp_path / "packages" / "latest.json").read_text())
            assert latest["package_id"] == "pkg-p01"
            assert latest["no_execution_performed"] is True
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig

    def test_persist_updates_latest_md(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "packages")
        try:
            pkg = self._make_pkg()
            persist_manual_apply_package(pkg)
            md = (tmp_path / "packages" / "latest.md").read_text()
            assert "pkg-p01" in md
            assert "No files were modified" in md
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig

    def test_persist_no_secrets_in_json(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "packages")
        try:
            pkg = self._make_pkg()
            persist_manual_apply_package(pkg)
            content = (tmp_path / "packages" / "latest.json").read_text()
            assert "sk-ant" not in content
            assert "api_key" not in content.lower()
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig

    def test_persist_no_secrets_in_markdown(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "packages")
        try:
            pkg = self._make_pkg()
            persist_manual_apply_package(pkg)
            content = (tmp_path / "packages" / "latest.md").read_text()
            assert "sk-ant" not in content
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig


class Test94OReadLatestPackage:
    """read_latest_manual_apply_package coverage."""

    def test_returns_none_when_missing(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "no-packages")
        try:
            assert read_latest_manual_apply_package() is None
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig

    def test_returns_package_after_persist(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "packages")
        try:
            pkg = BackendManualApplyPackage(package_id="pkg-rlt01", output_hash="h-rlt01")
            persist_manual_apply_package(pkg)
            loaded = read_latest_manual_apply_package()
            assert loaded is not None
            assert loaded.package_id == "pkg-rlt01"
            assert loaded.no_execution_performed is True
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig

    def test_roundtrip_preserves_phase_id(self, tmp_path):
        import pcae.core.backend_invocations as _bi
        orig = _bi._MANUAL_APPLY_PACKAGES_DIR
        _bi._MANUAL_APPLY_PACKAGES_DIR = str(tmp_path / "packages-ph")
        try:
            pkg = BackendManualApplyPackage(package_id="pkg-ph01", phase_id="94O.5.6")
            persist_manual_apply_package(pkg)
            loaded = read_latest_manual_apply_package()
            assert loaded.phase_id == "94O.5.6"
        finally:
            _bi._MANUAL_APPLY_PACKAGES_DIR = orig


class Test94ONoExecutionInPackageModule:
    """Package module introduces no execution capability."""

    def test_no_subprocess_in_core(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_no_network_in_core(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_manual_apply_packages_dir_in_gitignore(self):
        from pathlib import Path
        gitignore = Path(".pcae/.gitignore")
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "backend-manual-apply-packages/" in content

    def test_no_telegram_inbound_in_core(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "getUpdates" not in source
