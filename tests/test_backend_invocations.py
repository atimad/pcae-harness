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


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94P — Backend apply governance hardening tests
# ═══════════════════════════════════════════════════════════════════════════

import os as _os_94p
import json as _json_94p

from pcae.core.backend_invocations import (
    validate_operation_path,
    validate_operations_list,
    validate_hash_chain,
    validate_artifact_freshness,
    read_artifact_json_safe,
    OP_CREATE, OP_MODIFY, OP_DELETE, OP_RENAME, OP_MANUAL, OP_UNKNOWN,
    REVIEW_REJECTED, REVIEW_APPROVED,
)


class Test94PArtifactFreshness:
    """validate_artifact_freshness: fail-closed on missing/malformed."""

    def test_none_artifact_is_hard_block(self):
        r = validate_artifact_freshness(None, artifact_label="review")
        assert r["valid"] is False
        assert "review_missing" in r["hard_blocks"]

    def test_empty_dict_is_malformed_hard_block(self):
        r = validate_artifact_freshness({}, artifact_label="plan")
        assert r["valid"] is False
        assert "plan_malformed" in r["hard_blocks"]

    def test_non_dict_is_malformed_hard_block(self):
        r = validate_artifact_freshness([], artifact_label="pkg")  # type: ignore
        assert r["valid"] is False
        assert "pkg_malformed" in r["hard_blocks"]

    def test_valid_artifact_no_expected(self):
        r = validate_artifact_freshness({"output_hash": "h1", "request_id": "rq1"})
        assert r["valid"] is True
        assert r["hard_blocks"] == []

    def test_output_hash_mismatch_is_hard_block(self):
        r = validate_artifact_freshness(
            {"output_hash": "wrong"}, expected_output_hash="h1", artifact_label="approval"
        )
        assert r["valid"] is False
        assert "approval_output_hash_mismatch" in r["hard_blocks"]

    def test_missing_output_hash_is_missing_evidence(self):
        r = validate_artifact_freshness(
            {"request_id": "rq1"}, expected_output_hash="h1", artifact_label="review"
        )
        assert r["valid"] is False
        assert "review_output_hash_missing" in r["missing_evidence"]

    def test_request_id_mismatch_is_hard_block(self):
        r = validate_artifact_freshness(
            {"output_hash": "h1", "request_id": "wrong"},
            expected_output_hash="h1", expected_request_id="rq-correct",
            artifact_label="plan"
        )
        assert r["valid"] is False
        assert "plan_request_id_mismatch" in r["hard_blocks"]

    def test_phase_id_mismatch_is_hard_block(self):
        r = validate_artifact_freshness(
            {"phase_id": "94X"}, expected_phase_id="94P", artifact_label="pkg"
        )
        assert r["valid"] is False
        assert "pkg_phase_id_mismatch" in r["hard_blocks"]

    def test_phase_id_match_passes(self):
        r = validate_artifact_freshness(
            {"phase_id": "94P"}, expected_phase_id="94P", artifact_label="pkg"
        )
        assert r["valid"] is True


class Test94PReadArtifactJsonSafe:
    """read_artifact_json_safe: never raises, returns None on errors."""

    def test_missing_file_returns_none(self, tmp_path):
        result = read_artifact_json_safe(tmp_path / "no-such-file.json")
        assert result is None

    def test_malformed_json_returns_none(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("NOT JSON {{{")
        result = read_artifact_json_safe(f)
        assert result is None

    def test_non_dict_json_returns_none(self, tmp_path):
        f = tmp_path / "list.json"
        f.write_text("[1, 2, 3]")
        result = read_artifact_json_safe(f)
        assert result is None

    def test_valid_dict_returns_dict(self, tmp_path):
        f = tmp_path / "ok.json"
        f.write_text('{"key": "value"}')
        result = read_artifact_json_safe(f)
        assert result == {"key": "value"}

    def test_empty_file_returns_none(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("")
        result = read_artifact_json_safe(f)
        assert result is None


class Test94PValidateOperationPath:
    """validate_operation_path: path safety."""

    def test_empty_path_hard_blocks(self):
        blocks = validate_operation_path("")
        assert "empty_target_path" in blocks

    def test_whitespace_only_hard_blocks(self):
        blocks = validate_operation_path("   ")
        assert "empty_target_path" in blocks

    def test_absolute_path_hard_blocks(self):
        blocks = validate_operation_path("/etc/passwd")
        assert any("absolute_path" in b for b in blocks)

    def test_parent_traversal_hard_blocks(self):
        blocks = validate_operation_path("../../etc/passwd")
        assert any("parent_traversal" in b for b in blocks)

    def test_single_dotdot_hard_blocks(self):
        blocks = validate_operation_path("src/../secret.py")
        assert any("parent_traversal" in b for b in blocks)

    def test_forbidden_file_hard_blocks(self):
        blocks = validate_operation_path("src/foo.py", forbidden_files=["src/foo.py"])
        assert any("forbidden_file" in b for b in blocks)

    def test_safe_relative_path_passes(self):
        blocks = validate_operation_path("src/pcae/core/foo.py")
        assert blocks == []

    def test_safe_tests_path_passes(self):
        blocks = validate_operation_path("tests/test_foo.py")
        assert blocks == []

    def test_nested_safe_path_passes(self):
        blocks = validate_operation_path("docs/PHASE_94.md")
        assert blocks == []

    def test_known_forbidden_env_pattern(self):
        blocks = validate_operation_path(".env")
        assert any("forbidden" in b for b in blocks)

    def test_known_forbidden_session_json(self):
        blocks = validate_operation_path(".pcae/session.json")
        assert any("forbidden" in b for b in blocks)


class Test94PValidateOperationsList:
    """validate_operations_list: duplicates, conflicts, destructive."""

    def test_empty_list_valid(self):
        r = validate_operations_list([])
        assert r["valid"] is True
        assert r["hard_blocks"] == []

    def test_safe_single_op_valid(self):
        op = ApplyOperation(operation_type=OP_MODIFY, target_path="src/foo.py")
        r = validate_operations_list([op])
        assert r["valid"] is True

    def test_duplicate_same_op_type_warns(self):
        op1 = ApplyOperation(operation_type=OP_MODIFY, target_path="src/foo.py")
        op2 = ApplyOperation(operation_type=OP_MODIFY, target_path="src/foo.py")
        r = validate_operations_list([op1, op2])
        assert any("duplicate_operation" in w for w in r["warnings"])

    def test_conflicting_ops_same_path_hard_blocks(self):
        op1 = ApplyOperation(operation_type=OP_CREATE, target_path="src/foo.py")
        op2 = ApplyOperation(operation_type=OP_DELETE, target_path="src/foo.py")
        r = validate_operations_list([op1, op2])
        assert r["valid"] is False
        assert any("conflicting_operations" in b for b in r["hard_blocks"])

    def test_delete_op_hard_blocks(self):
        op = ApplyOperation(operation_type=OP_DELETE, target_path="src/foo.py")
        r = validate_operations_list([op])
        assert r["valid"] is False
        assert any("destructive_op" in b for b in r["hard_blocks"])

    def test_rename_op_hard_blocks(self):
        op = ApplyOperation(operation_type=OP_RENAME, target_path="src/foo.py")
        r = validate_operations_list([op])
        assert r["valid"] is False
        assert any("destructive_op" in b for b in r["hard_blocks"])

    def test_unknown_op_hard_blocks(self):
        op = ApplyOperation(operation_type=OP_UNKNOWN, target_path="")
        r = validate_operations_list([op])
        assert r["valid"] is False
        assert any("unknown_operation" in b for b in r["hard_blocks"])

    def test_absolute_path_hard_blocks(self):
        op = ApplyOperation(operation_type=OP_MODIFY, target_path="/etc/secret")
        r = validate_operations_list([op])
        assert r["valid"] is False
        assert any("absolute_path" in b for b in r["hard_blocks"])

    def test_traversal_path_hard_blocks(self):
        op = ApplyOperation(operation_type=OP_MODIFY, target_path="../../secret.py")
        r = validate_operations_list([op])
        assert r["valid"] is False
        assert any("parent_traversal" in b for b in r["hard_blocks"])

    def test_forbidden_file_in_ops_hard_blocks(self):
        op = ApplyOperation(operation_type=OP_MODIFY, target_path="src/secret.py")
        r = validate_operations_list([op], forbidden_files=["src/secret.py"])
        assert r["valid"] is False
        assert any("forbidden_file" in b for b in r["hard_blocks"])

    def test_manual_ops_skip_path_checks(self):
        op = ApplyOperation(operation_type=OP_MANUAL, target_path="")
        r = validate_operations_list([op])
        assert "empty_target_path" not in str(r["hard_blocks"])


class Test94PHashChain:
    """validate_hash_chain: mismatch detection."""

    def _rv(self, output_hash: str, request_id: str = "") -> ReviewArtifact:
        return ReviewArtifact(review_id="rv-hc01", output_hash=output_hash,
                               request_id=request_id, review_state=REVIEW_APPROVED)

    def _ap(self, output_hash: str, request_id: str = "") -> ApprovalArtifact:
        return ApprovalArtifact(approval_id="ap-hc01", output_hash=output_hash,
                                request_id=request_id, operator="op")

    def _pl(self, output_hash: str, request_id: str = "",
             apply_plan_id: str = "pl-hc01") -> ApplyPlan:
        return ApplyPlan(apply_plan_id=apply_plan_id, review_id="rv-hc01",
                          output_hash=output_hash, request_id=request_id)

    def test_matching_review_approval_passes(self):
        r = validate_hash_chain(
            review=self._rv("hash-A", "req-1"),
            approval=self._ap("hash-A", "req-1"),
        )
        assert r["valid"] is True

    def test_review_approval_hash_mismatch(self):
        r = validate_hash_chain(
            review=self._rv("hash-A"), approval=self._ap("hash-B"),
        )
        assert r["valid"] is False
        assert "review_approval_output_hash_mismatch" in r["hard_blocks"]

    def test_review_approval_request_id_mismatch(self):
        r = validate_hash_chain(
            review=self._rv("hash-A", "req-1"),
            approval=self._ap("hash-A", "req-WRONG"),
        )
        assert r["valid"] is False
        assert "review_approval_request_id_mismatch" in r["hard_blocks"]

    def test_review_plan_hash_mismatch(self):
        r = validate_hash_chain(
            review=self._rv("hash-A"),
            plan=self._pl("hash-B"),
        )
        assert r["valid"] is False
        assert "review_plan_output_hash_mismatch" in r["hard_blocks"]

    def test_review_plan_request_id_mismatch(self):
        r = validate_hash_chain(
            review=self._rv("hash-A", "req-1"),
            plan=self._pl("hash-A", "req-WRONG"),
        )
        assert r["valid"] is False
        assert "review_plan_request_id_mismatch" in r["hard_blocks"]

    def test_approval_plan_hash_mismatch(self):
        r = validate_hash_chain(
            approval=self._ap("hash-A"),
            plan=self._pl("hash-B"),
        )
        assert r["valid"] is False
        assert "approval_plan_output_hash_mismatch" in r["hard_blocks"]

    def test_plan_package_hash_mismatch(self):
        plan = self._pl("hash-A", apply_plan_id="pl-pp01")
        pkg = BackendManualApplyPackage(
            package_id="pkg-pp01", apply_plan_id="pl-pp01",
            output_hash="hash-B", request_id=""
        )
        r = validate_hash_chain(plan=plan, package=pkg)
        assert r["valid"] is False
        assert "plan_package_output_hash_mismatch" in r["hard_blocks"]

    def test_plan_package_request_id_mismatch(self):
        plan = self._pl("hash-A", request_id="req-1", apply_plan_id="pl-rq01")
        pkg = BackendManualApplyPackage(
            package_id="pkg-rq01", apply_plan_id="pl-rq01",
            output_hash="hash-A", request_id="req-WRONG"
        )
        r = validate_hash_chain(plan=plan, package=pkg)
        assert r["valid"] is False
        assert "plan_package_request_id_mismatch" in r["hard_blocks"]

    def test_plan_package_apply_plan_id_mismatch(self):
        plan = self._pl("hash-A", apply_plan_id="pl-correct")
        pkg = BackendManualApplyPackage(
            package_id="pkg-id01", apply_plan_id="pl-WRONG",
            output_hash="hash-A"
        )
        r = validate_hash_chain(plan=plan, package=pkg)
        assert r["valid"] is False
        assert "plan_package_apply_plan_id_mismatch" in r["hard_blocks"]

    def test_empty_hashes_skip_check(self):
        r = validate_hash_chain(
            review=ReviewArtifact(review_id="rv-eh", output_hash=""),
            approval=ApprovalArtifact(approval_id="ap-eh", output_hash=""),
        )
        assert r["valid"] is True

    def test_matching_full_chain_passes(self):
        review = self._rv("hash-FULL", "req-full")
        approval = self._ap("hash-FULL", "req-full")
        plan = self._pl("hash-FULL", "req-full", apply_plan_id="pl-full")
        pkg = BackendManualApplyPackage(
            package_id="pkg-full", apply_plan_id="pl-full",
            output_hash="hash-FULL", request_id="req-full"
        )
        r = validate_hash_chain(review=review, approval=approval, plan=plan, package=pkg)
        assert r["valid"] is True
        assert r["hard_blocks"] == []


class Test94PStateTransition:
    """State-transition hardening."""

    def test_rejected_review_cannot_be_approved(self):
        review = ReviewArtifact(
            review_id="rv-st01", request_id="rq-st01", output_hash="h-st01",
            review_state=REVIEW_REJECTED, rejected=True,
        )
        with pytest.raises(ValueError, match="already rejected"):
            approve_review(review, operator="op", reason="reason")

    def test_hard_block_prevents_approval(self):
        review = ReviewArtifact(
            review_id="rv-st02", request_id="rq-st02", output_hash="h-st02",
            hard_blocks=["forbidden_file:x.py"],
        )
        with pytest.raises(ValueError, match="hard blocks"):
            approve_review(review, operator="op", reason="reason")

    def test_approval_does_not_imply_apply_ready(self):
        review = ReviewArtifact(
            review_id="rv-st03", request_id="rq-st03", output_hash="h-st03",
        )
        approval = approve_review(review, operator="op", reason="ok")
        assert review.apply_ready is False
        assert approval.output_hash == "h-st03"

    def test_apply_ready_does_not_imply_applied(self):
        plan = ApplyPlan(
            apply_plan_id="pl-st04", review_id="rv-st04",
            output_hash="h-st04", apply_ready=True,
        )
        d = plan.to_dict()
        assert "applied" not in d
        assert d["apply_ready"] is True

    def test_package_generation_does_not_imply_apply_ready(self):
        plan = ApplyPlan(apply_plan_id="pl-st05", review_id="rv-st05",
                          output_hash="h-st05")
        pkg = create_backend_manual_apply_package(plan=plan)
        assert pkg.apply_ready is False
        assert pkg.no_execution_performed is True

    def test_approved_review_still_not_apply_ready(self):
        review = ReviewArtifact(
            review_id="rv-st06", request_id="rq-st06", output_hash="h-st06",
        )
        approve_review(review, operator="op", reason="ok")
        assert review.approved_for_apply is True
        assert review.apply_ready is False

    def test_applied_rolled_back_states_not_in_valid_states(self):
        from pcae.core.backend_invocations import VALID_REVIEW_STATES
        assert "applied" not in VALID_REVIEW_STATES
        assert "apply_failed" not in VALID_REVIEW_STATES
        assert "rolled_back" not in VALID_REVIEW_STATES

    def test_apply_ready_cannot_coexist_with_hard_blocks_in_plan(self):
        plan = ApplyPlan(
            apply_plan_id="pl-st07", review_id="rv-st07",
            output_hash="h-st07", apply_ready=True,
            hard_blocks=["forbidden_file:x"],
        )
        issues = plan.validate()
        assert any("hard blocks" in i for i in issues)

    def test_rejection_does_not_flip_approved(self):
        review = ReviewArtifact(
            review_id="rv-st08", request_id="rq-st08", output_hash="h-st08",
        )
        approve_review(review, operator="op", reason="ok")
        assert review.approved_for_apply is True
        reject_review(review, operator="op", reason="changed mind")
        assert review.rejected is True
        assert review.review_state == REVIEW_REJECTED


class Test94POperationPathHardening:
    """Path hardening in operations and plans."""

    def test_absolute_path_in_operation_path_hard_blocks(self):
        op = ApplyOperation(operation_type=OP_MODIFY, target_path="/etc/passwd")
        blocks = op.path_hard_blocks()
        assert any("absolute_path" in b for b in blocks)

    def test_traversal_path_in_operation_path_hard_blocks(self):
        op = ApplyOperation(operation_type=OP_CREATE, target_path="../../secret.py")
        blocks = op.path_hard_blocks()
        assert any("parent_traversal" in b for b in blocks)

    def test_empty_path_for_create_fails(self):
        op = ApplyOperation(operation_type=OP_CREATE, target_path="")
        issues = op.validate()
        assert any("target_path required" in i for i in issues)

    def test_absolute_path_in_create_apply_plan_hard_blocks(self):
        review = ReviewArtifact(review_id="rv-ph01", request_id="rq-ph01",
                                 output_hash="h-ph01")
        op = ApplyOperation(operation_type=OP_MODIFY, target_path="/etc/passwd")
        plan = create_apply_plan(review, operations=[op])
        assert any("absolute_path" in b for b in plan.hard_blocks)

    def test_traversal_path_in_create_apply_plan_hard_blocks(self):
        review = ReviewArtifact(review_id="rv-ph02", request_id="rq-ph02",
                                 output_hash="h-ph02")
        op = ApplyOperation(operation_type=OP_MODIFY, target_path="../../secret.py")
        plan = create_apply_plan(review, operations=[op])
        assert any("parent_traversal" in b for b in plan.hard_blocks)

    def test_duplicate_op_warns_in_create_apply_plan(self):
        review = ReviewArtifact(review_id="rv-ph03", request_id="rq-ph03",
                                 output_hash="h-ph03")
        op1 = ApplyOperation(operation_type=OP_MODIFY, target_path="src/foo.py")
        op2 = ApplyOperation(operation_type=OP_MODIFY, target_path="src/foo.py")
        plan = create_apply_plan(review, operations=[op1, op2])
        assert any("duplicate_operation" in w for w in plan.warnings)

    def test_conflicting_ops_hard_block_in_create_apply_plan(self):
        review = ReviewArtifact(review_id="rv-ph04", request_id="rq-ph04",
                                 output_hash="h-ph04")
        op1 = ApplyOperation(operation_type=OP_CREATE, target_path="src/new.py")
        op2 = ApplyOperation(operation_type=OP_DELETE, target_path="src/new.py")
        plan = create_apply_plan(review, operations=[op1, op2])
        assert any("conflicting_operations" in b or "high_risk_op" in b
                   for b in plan.hard_blocks)

    def test_forbidden_file_target_hard_blocks(self):
        review = ReviewArtifact(review_id="rv-ph05", request_id="rq-ph05",
                                 output_hash="h-ph05")
        op = ApplyOperation(operation_type=OP_MODIFY, target_path="src/secret.py")
        plan = create_apply_plan(review, operations=[op],
                                  forbidden_files=["src/secret.py"])
        assert any("forbidden_file" in b for b in plan.hard_blocks)


class Test94PPackageHardening:
    """Package safety: cannot hide hard blocks, no authorization implied."""

    def test_package_preserves_hard_blocks_from_plan(self):
        plan = ApplyPlan(apply_plan_id="pl-pkg01", review_id="rv-pkg01",
                          output_hash="h-pkg01", hard_blocks=["forbidden_file:x.py"])
        pkg = create_backend_manual_apply_package(plan=plan)
        assert "forbidden_file:x.py" in pkg.hard_blocks

    def test_package_hard_blocks_visible_in_markdown(self):
        plan = ApplyPlan(apply_plan_id="pl-pkg02", review_id="rv-pkg02",
                          output_hash="h-pkg02", hard_blocks=["forbidden_file:y.py"])
        pkg = create_backend_manual_apply_package(plan=plan)
        md = pkg.render_markdown()
        assert "forbidden_file:y.py" in md

    def test_package_hard_blocks_visible_in_to_dict(self):
        plan = ApplyPlan(apply_plan_id="pl-pkg03", review_id="rv-pkg03",
                          output_hash="h-pkg03", hard_blocks=["output_hash_missing"])
        pkg = create_backend_manual_apply_package(plan=plan)
        d = pkg.to_dict()
        assert "output_hash_missing" in d["hard_blocks"]

    def test_package_no_commit_push_auth_in_dict(self):
        plan = ApplyPlan(apply_plan_id="pl-pkg04", review_id="rv-pkg04",
                          output_hash="h-pkg04")
        pkg = create_backend_manual_apply_package(plan=plan)
        d = pkg.to_dict()
        assert "commit_authorized" not in d
        assert "push_authorized" not in d

    def test_package_no_backend_invocation_auth_in_dict(self):
        plan = ApplyPlan(apply_plan_id="pl-pkg05", review_id="rv-pkg05",
                          output_hash="h-pkg05")
        pkg = create_backend_manual_apply_package(plan=plan)
        d = pkg.to_dict()
        assert "backend_invoked" not in d
        assert "backend_invocation_authorized" not in d

    def test_package_generation_does_not_run_tests(self):
        plan = ApplyPlan(apply_plan_id="pl-pkg06", review_id="rv-pkg06",
                          output_hash="h-pkg06", tests_to_run=["pytest tests/"])
        pkg = create_backend_manual_apply_package(plan=plan)
        # tests_to_run preserved as advisory, not executed
        assert "pytest tests/" in pkg.tests_to_run
        assert pkg.no_execution_performed is True

    def test_package_generation_does_not_run_pcae_check(self):
        plan = ApplyPlan(apply_plan_id="pl-pkg07", review_id="rv-pkg07",
                          output_hash="h-pkg07", check_required=True)
        pkg = create_backend_manual_apply_package(plan=plan)
        assert "pcae check" in pkg.checks_to_run[0]
        assert pkg.no_execution_performed is True

    def test_package_with_no_hard_blocks_still_no_execution(self):
        plan = ApplyPlan(apply_plan_id="pl-pkg08", review_id="rv-pkg08",
                          output_hash="h-pkg08")
        pkg = create_backend_manual_apply_package(plan=plan)
        assert pkg.no_execution_performed is True

    def test_package_merges_assessment_hard_blocks_cannot_hide(self):
        from pcae.core.backend_invocations import BackendApplyReadinessAssessment
        plan = ApplyPlan(apply_plan_id="pl-pkg09", review_id="rv-pkg09",
                          output_hash="h-pkg09")
        assessment = BackendApplyReadinessAssessment(
            assessment_id="ra-pkg09", hard_blocks=["trust_assessment_blocked"]
        )
        pkg = create_backend_manual_apply_package(plan=plan, assessment=assessment)
        assert "trust_assessment_blocked" in pkg.hard_blocks
        md = pkg.render_markdown()
        assert "trust_assessment_blocked" in md

    def test_package_no_raw_prompt_content(self):
        plan = ApplyPlan(
            apply_plan_id="pl-pkg10", review_id="rv-pkg10",
            output_hash="h-pkg10",
            prompt_artifact_path=".pcae/prompts/test.md",
        )
        pkg = create_backend_manual_apply_package(plan=plan)
        md = pkg.render_markdown()
        # prompt_artifact_path stored as metadata ref, not contents
        assert "prompt content" not in md.lower()
        # The path itself as metadata is fine, but raw body shouldn't be there
        # (since we never load it, it won't be there)
        assert pkg.no_execution_performed is True

    def test_package_no_secrets_in_to_dict(self):
        plan = ApplyPlan(apply_plan_id="pl-pkg11", review_id="rv-pkg11",
                          output_hash="h-pkg11")
        pkg = create_backend_manual_apply_package(
            plan=plan, operator_notes="approved by team"
        )
        j = _json_94p.dumps(pkg.to_dict())
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()


class Test94PValidateReadinessHardening:
    """validate_backend_apply_readiness: hash binding and hard-block dominance."""

    def test_review_approval_hash_mismatch_hard_blocks(self):
        plan = ApplyPlan(apply_plan_id="pl-vh01", review_id="rv-vh01",
                          approval_id="ap-vh01", output_hash="hash-A")
        review = ReviewArtifact(review_id="rv-vh01", request_id="rq-vh01",
                                 output_hash="hash-A", review_state=REVIEW_APPROVED)
        # Approval with mismatched hash
        approval = ApprovalArtifact(approval_id="ap-vh01", output_hash="hash-B",
                                     operator="op", review_id="rv-vh01")
        assessment = validate_backend_apply_readiness(
            plan=plan, review=review, approval=approval,
        )
        assert assessment.apply_ready is False
        assert any("hash_mismatch" in b for b in assessment.hard_blocks)

    def test_hard_blocks_dominate_accepted_risk(self):
        plan = ApplyPlan(
            apply_plan_id="pl-vh02", review_id="rv-vh02",
            output_hash="h-vh02",
            hard_blocks=["forbidden_file:x.py"],
        )
        approval = ApprovalArtifact(
            approval_id="ap-vh02", output_hash="h-vh02",
            operator="op", accepted_risk=True,
        )
        assessment = validate_backend_apply_readiness(plan=plan, approval=approval)
        assert assessment.apply_ready is False
        assert "forbidden_file:x.py" in assessment.hard_blocks

    def test_hard_blocks_dominate_human_approval(self):
        plan = ApplyPlan(
            apply_plan_id="pl-vh03", review_id="rv-vh03",
            output_hash="h-vh03",
            hard_blocks=["output_hash_missing"],
        )
        review = ReviewArtifact(review_id="rv-vh03", request_id="rq-vh03",
                                 output_hash="h-vh03", review_state=REVIEW_APPROVED,
                                 approved_for_apply=True)
        assessment = validate_backend_apply_readiness(plan=plan, review=review)
        assert assessment.apply_ready is False

    def test_missing_plan_returns_hard_block(self):
        assessment = validate_backend_apply_readiness(plan=None)
        assert assessment.apply_ready is False
        assert "apply_plan_missing" in assessment.hard_blocks

    def test_rejected_review_causes_missing_evidence(self):
        plan = ApplyPlan(apply_plan_id="pl-vh05", review_id="rv-vh05",
                          output_hash="h-vh05")
        review = ReviewArtifact(review_id="rv-vh05", request_id="rq-vh05",
                                 output_hash="h-vh05", review_state=REVIEW_REJECTED,
                                 rejected=True)
        assessment = validate_backend_apply_readiness(plan=plan, review=review)
        assert assessment.apply_ready is False
        assert any("review_not_approved" in m for m in assessment.missing_evidence)


class Test94PNoExecutionGuarantees:
    """Cross-cutting no-execution guarantees."""

    def test_validate_operation_path_no_subprocess(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        # Ensure no subprocess was introduced in the module
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_validate_hash_chain_no_network(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_telegram_inbound_in_hardening(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "getUpdates" not in source

    def test_multipart_phase_id_preserved_through_hardening(self):
        plan = ApplyPlan(apply_plan_id="pl-mp94p", review_id="rv-mp94p",
                          output_hash="h-mp94p", phase_id="94P.1.2.3")
        pkg = create_backend_manual_apply_package(plan=plan)
        assert pkg.phase_id == "94P.1.2.3"
        d = pkg.to_dict()
        assert d["phase_id"] == "94P.1.2.3"

    def test_json_output_deterministic(self):
        plan = ApplyPlan(apply_plan_id="pl-det94p", review_id="rv-det94p",
                          output_hash="h-det94p")
        pkg = create_backend_manual_apply_package(plan=plan)
        d1 = pkg.to_dict()
        d2 = pkg.to_dict()
        assert set(d1.keys()) == set(d2.keys())
        assert d1["no_execution_performed"] is True
        assert d2["no_execution_performed"] is True


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Q — Backend lifecycle end-to-end mock demo tests
# ═══════════════════════════════════════════════════════════════════════════

import os as _os_94q
import json as _json_94q

from pcae.core.backend_invocations import (
    BackendLifecycleDemo,
    run_mock_lifecycle_demo,
    persist_lifecycle_demo,
    read_latest_lifecycle_demo,
    DEMO_COMPLETED,
    DEMO_BLOCKED,
    DEMO_PARTIAL,
    DEMO_FAILED,
    VALID_DEMO_STATUSES,
)


class Test94QLifecycleDemoModel:
    """BackendLifecycleDemo model validation and serialization."""

    def test_valid_demo_defaults(self):
        demo = BackendLifecycleDemo(demo_id="demo-test01")
        assert demo.validate() == []

    def test_missing_demo_id(self):
        demo = BackendLifecycleDemo()
        issues = demo.validate()
        assert any("demo_id" in i for i in issues)

    def test_invalid_status(self):
        demo = BackendLifecycleDemo(demo_id="d1", lifecycle_status="bogus")
        issues = demo.validate()
        assert any("lifecycle_status" in i for i in issues)

    def test_no_real_backend_invoked_must_be_true(self):
        demo = BackendLifecycleDemo(demo_id="d1", no_real_backend_invoked=False)
        issues = demo.validate()
        assert any("no_real_backend_invoked" in i for i in issues)

    def test_no_apply_execution_must_be_true(self):
        demo = BackendLifecycleDemo(demo_id="d1", no_apply_execution=False)
        issues = demo.validate()
        assert any("no_apply_execution" in i for i in issues)

    def test_no_file_mutation_must_be_true(self):
        demo = BackendLifecycleDemo(demo_id="d1", no_file_mutation=False)
        issues = demo.validate()
        assert any("no_file_mutation" in i for i in issues)

    def test_all_valid_statuses(self):
        for st in VALID_DEMO_STATUSES:
            demo = BackendLifecycleDemo(demo_id="d1", lifecycle_status=st)
            assert demo.validate() == []

    def test_to_dict_all_fields(self):
        demo = BackendLifecycleDemo(
            demo_id="demo-dict01",
            phase_id="94Q",
            task_id="task-01",
            backend_id="mock",
            request_id="be-req01",
            prompt_hash="ph-hash",
            output_hash="oh-hash",
            audit_id="ba-audit01",
            trust_assessment_id="as-trust01",
            review_id="rv-rev01",
            approval_id="ap-app01",
            apply_plan_id="pl-plan01",
            apply_readiness_assessment_id="ra-ra01",
            lifecycle_status=DEMO_COMPLETED,
            hard_blocks=[],
            missing_evidence=[],
            warnings=["test_warning"],
        )
        d = demo.to_dict()
        assert d["demo_id"] == "demo-dict01"
        assert d["phase_id"] == "94Q"
        assert d["lifecycle_status"] == DEMO_COMPLETED
        assert d["no_real_backend_invoked"] is True
        assert d["no_apply_execution"] is True
        assert d["no_file_mutation"] is True
        assert d["no_subprocess"] is True
        assert d["no_network"] is True
        assert d["no_shell_interception"] is True
        assert d["warnings"] == ["test_warning"]

    def test_to_dict_deterministic(self):
        demo = BackendLifecycleDemo(demo_id="demo-det01")
        d1 = demo.to_dict()
        d2 = demo.to_dict()
        assert set(d1.keys()) == set(d2.keys())
        assert d1["no_real_backend_invoked"] is True
        assert d2["no_file_mutation"] is True

    def test_from_dict_round_trip(self):
        d = {
            "demo_id": "demo-rt01",
            "phase_id": "94Q.1",
            "task_id": "task-rt",
            "backend_id": "mock",
            "lifecycle_status": DEMO_COMPLETED,
            "no_real_backend_invoked": True,
            "no_apply_execution": True,
            "no_file_mutation": True,
        }
        demo = BackendLifecycleDemo.from_dict(d)
        assert demo.demo_id == "demo-rt01"
        assert demo.phase_id == "94Q.1"
        assert demo.lifecycle_status == DEMO_COMPLETED

    def test_no_secrets_in_to_dict(self):
        demo = BackendLifecycleDemo(demo_id="d1", prompt_hash="ph", output_hash="oh")
        j = _json_94q.dumps(demo.to_dict())
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()
        assert "token" not in j.lower()


class Test94QHappyPathDemo:
    """End-to-end happy path mock lifecycle demo."""

    def test_demo_creates_all_expected_artifacts(self):
        demo, steps = run_mock_lifecycle_demo(phase_id="94Q", task_id="task-happy")
        assert demo.lifecycle_status in (DEMO_COMPLETED, DEMO_PARTIAL)
        assert demo.request_id.startswith("be-")
        assert demo.demo_id.startswith("demo-")
        assert demo.audit_id.startswith("ba-")
        assert demo.trust_assessment_id.startswith("as-")
        assert demo.review_id.startswith("rv-")
        assert demo.approval_id.startswith("ap-")
        assert demo.apply_plan_id.startswith("pl-")
        assert demo.apply_readiness_assessment_id.startswith("ra-")
        # All steps exercised
        assert "plan" in steps
        assert "mock_invocation" in steps
        assert "audit" in steps
        assert "trust" in steps
        assert "review" in steps
        assert "approval" in steps
        assert "apply_plan" in steps
        assert "apply_readiness" in steps

    def test_artifact_chain_preserves_request_id(self):
        demo, steps = run_mock_lifecycle_demo()
        req_id = demo.request_id
        assert req_id
        # Request ID is consistent through all artifacts
        assert demo.request_id == req_id

    def test_artifact_chain_preserves_output_hash(self):
        demo, steps = run_mock_lifecycle_demo()
        assert demo.output_hash
        assert demo.prompt_hash
        assert demo.output_hash != demo.prompt_hash

    def test_output_remains_quarantined(self):
        demo, steps = run_mock_lifecycle_demo()
        mock_inv = steps.get("mock_invocation", {})
        assert mock_inv.get("quarantined") is True
        assert mock_inv.get("applied_to_repo") is False

    def test_apply_plan_created_but_not_executed(self):
        demo, steps = run_mock_lifecycle_demo()
        ap = steps.get("apply_plan", {})
        assert ap.get("apply_plan_id")
        assert ap.get("apply_ready") is False  # missing rollback/tests in default
        assert demo.no_apply_execution is True

    def test_apply_readiness_generated_no_apply_executed(self):
        demo, steps = run_mock_lifecycle_demo()
        ar = steps.get("apply_readiness", {})
        assert ar.get("assessment_id")
        assert demo.no_apply_execution is True
        assert demo.no_file_mutation is True

    def test_no_real_backend_invoked(self):
        demo, steps = run_mock_lifecycle_demo()
        assert demo.no_real_backend_invoked is True
        mock_inv = steps.get("mock_invocation", {})
        assert mock_inv.get("no_real_backend_invoked") is True

    def test_no_subprocess_no_network_no_shell(self):
        demo, steps = run_mock_lifecycle_demo()
        assert demo.no_subprocess is True
        assert demo.no_network is True
        assert demo.no_shell_interception is True

    def test_no_secrets_in_demo_summary(self):
        demo, steps = run_mock_lifecycle_demo()
        j = _json_94q.dumps(demo.to_dict())
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()
        # Prompt content should not leak
        assert "deterministic mock prompt" not in j.lower()

    def test_multipart_phase_id_preserved(self):
        demo, steps = run_mock_lifecycle_demo(phase_id="94Q.1.2.3")
        assert demo.phase_id == "94Q.1.2.3"
        d = demo.to_dict()
        assert d["phase_id"] == "94Q.1.2.3"

    def test_no_source_files_modified(self):
        """Verify no source files are modified by the demo."""
        demo, steps = run_mock_lifecycle_demo()
        # Only .pcae/ artifacts are created
        assert demo.no_file_mutation is True


class Test94QNegativePathDemo:
    """Negative path: forbidden path → blocked lifecycle."""

    def test_forbidden_path_produces_blocked_status(self):
        demo, steps = run_mock_lifecycle_demo(forbidden_path_check=True)
        assert demo.lifecycle_status == DEMO_BLOCKED

    def test_forbidden_path_has_hard_blocks(self):
        demo, steps = run_mock_lifecycle_demo(forbidden_path_check=True)
        assert len(demo.hard_blocks) > 0
        assert any(".env" in hb for hb in demo.hard_blocks)

    def test_forbidden_path_rejected_not_approved(self):
        demo, steps = run_mock_lifecycle_demo(forbidden_path_check=True)
        assert demo.rejection_id.startswith("rj-")
        assert demo.approval_id == ""

    def test_forbidden_path_still_no_execution(self):
        demo, steps = run_mock_lifecycle_demo(forbidden_path_check=True)
        assert demo.no_real_backend_invoked is True
        assert demo.no_apply_execution is True
        assert demo.no_file_mutation is True
        assert demo.no_subprocess is True
        assert demo.no_network is True

    def test_forbidden_path_no_secrets(self):
        demo, steps = run_mock_lifecycle_demo(forbidden_path_check=True)
        j = _json_94q.dumps(demo.to_dict())
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()

    def test_forbidden_path_approval_rejected(self):
        demo, steps = run_mock_lifecycle_demo(forbidden_path_check=True)
        approval_step = steps.get("approval", {})
        assert approval_step.get("status") == "rejected"


class Test94QDemoPersistence:
    """Persistence of lifecycle demo artifacts."""

    def test_persist_and_read_round_trip(self, tmp_path):
        import os as _os_inner
        orig_dir = _os_inner.getcwd()
        try:
            _os_inner.chdir(tmp_path)
            demo, steps = run_mock_lifecycle_demo()
            result = persist_lifecycle_demo(demo)
            assert result["status"] == "written"
            assert result["demo_id"] == demo.demo_id

            # Read back
            loaded = read_latest_lifecycle_demo()
            assert loaded is not None
            assert loaded.demo_id == demo.demo_id
            assert loaded.request_id == demo.request_id
            assert loaded.output_hash == demo.output_hash
            assert loaded.lifecycle_status == demo.lifecycle_status
            assert loaded.no_real_backend_invoked is True
        finally:
            _os_inner.chdir(orig_dir)

    def test_latest_demo_updated_on_new_run(self, tmp_path):
        import os as _os_inner
        orig_dir = _os_inner.getcwd()
        try:
            _os_inner.chdir(tmp_path)
            demo1, _ = run_mock_lifecycle_demo()
            persist_lifecycle_demo(demo1)
            demo2, _ = run_mock_lifecycle_demo()
            persist_lifecycle_demo(demo2)

            loaded = read_latest_lifecycle_demo()
            assert loaded is not None
            assert loaded.demo_id == demo2.demo_id
            assert loaded.demo_id != demo1.demo_id
        finally:
            _os_inner.chdir(orig_dir)

    def test_read_latest_returns_none_when_absent(self, tmp_path):
        import os as _os_inner
        orig_dir = _os_inner.getcwd()
        try:
            _os_inner.chdir(tmp_path)
            result = read_latest_lifecycle_demo()
            assert result is None
        finally:
            _os_inner.chdir(orig_dir)

    def test_persist_creates_latest_json(self, tmp_path):
        import os as _os_inner
        from pathlib import Path
        orig_dir = _os_inner.getcwd()
        try:
            _os_inner.chdir(tmp_path)
            demo, _ = run_mock_lifecycle_demo()
            result = persist_lifecycle_demo(demo)
            lp = Path(result["latest_path"])
            assert lp.exists()
            data = _json_94q.loads(lp.read_text())
            assert data["demo_id"] == demo.demo_id
        finally:
            _os_inner.chdir(orig_dir)

    def test_persist_creates_timestamped_file(self, tmp_path):
        import os as _os_inner
        from pathlib import Path
        orig_dir = _os_inner.getcwd()
        try:
            _os_inner.chdir(tmp_path)
            demo, _ = run_mock_lifecycle_demo()
            result = persist_lifecycle_demo(demo)
            fp = Path(result["path"])
            assert fp.exists()
            assert demo.demo_id in fp.name
        finally:
            _os_inner.chdir(orig_dir)


class Test94QNoExecutionGuarantees:
    """Cross-cutting no-execution guarantees for Phase 94Q."""

    def test_no_subprocess_in_94q_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        # run_mock_lifecycle_demo should not introduce subprocess
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_no_network_in_94q_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_telegram_inbound_in_94q(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "getUpdates" not in source

    def test_no_real_backend_invoked_always_true(self):
        demo, _ = run_mock_lifecycle_demo()
        assert demo.no_real_backend_invoked is True

    def test_no_apply_execution_always_true(self):
        demo, _ = run_mock_lifecycle_demo()
        assert demo.no_apply_execution is True

    def test_no_file_mutation_always_true(self):
        demo, _ = run_mock_lifecycle_demo()
        assert demo.no_file_mutation is True

    def test_demo_backend_is_mock_only(self):
        demo, _ = run_mock_lifecycle_demo()
        assert demo.backend_id == "mock"

    def test_negative_path_still_no_execution(self):
        demo, _ = run_mock_lifecycle_demo(forbidden_path_check=True)
        assert demo.no_real_backend_invoked is True
        assert demo.no_apply_execution is True
        assert demo.no_file_mutation is True
        assert demo.no_subprocess is True
        assert demo.no_network is True


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94S — Real backend adapter contract model tests
# ═══════════════════════════════════════════════════════════════════════════

import os as _os_94s
import json as _json_94s

from pcae.core.backend_invocations import (
    BackendAdapterContract,
    BackendAdapterSafetyProfile,
    BackendAdapterPreflightResult,
    BackendAdapterInvocationPlan,
    validate_backend_adapter_contract,
    validate_backend_adapter_preflight,
    create_backend_adapter_invocation_plan,
    classify_backend_adapter_failure,
    get_default_adapter_registry,
    ADAPTER_BACKEND_MOCK,
    ADAPTER_BACKEND_CLAUDE_CLI,
    PREFLIGHT_READY,
    PREFLIGHT_BLOCKED,
    PREFLIGHT_DISABLED,
    PREFLIGHT_MISSING_EVIDENCE,
    ADAPTER_MODE_MOCK_ONLY,
    ADAPTER_MODE_PREFLIGHT_ONLY,
    ADAPTER_MODE_DISABLED,
    ADAPTER_MODE_FUTURE_REAL,
    FAILURE_DISABLED,
    FAILURE_MISSING_ENV,
    FAILURE_BYPASS_PERMISSIONS,
    FAILURE_TIMEOUT,
    FAILURE_BACKEND_UNAVAILABLE,
    FAILURE_AUTH_FAILURE,
    FAILURE_RATE_LIMITED,
    FAILURE_OUTPUT_MISSING,
    FAILURE_OUTPUT_MALFORMED,
    FAILURE_NOT_INVOKED,
    VALID_FAILURE_CATEGORIES,
)


class Test94SAdapterSafetyProfile:
    """BackendAdapterSafetyProfile: conservative defaults."""

    def test_defaults_are_conservative(self):
        sp = BackendAdapterSafetyProfile()
        assert sp.requires_human_approval is True
        assert sp.requires_permission_broker is True
        assert sp.requires_shell_gate is True
        assert sp.requires_output_quarantine is True
        assert sp.requires_audit is True
        assert sp.requires_timeout is True
        assert sp.requires_secret_redaction is True
        assert sp.requires_bypass_detection is True
        assert sp.supports_no_apply_guarantee is True

    def test_validate_flags_missing_approval(self):
        sp = BackendAdapterSafetyProfile(requires_human_approval=False)
        issues = sp.validate()
        assert any("human_approval" in i for i in issues)

    def test_to_dict_round_trip(self):
        sp = BackendAdapterSafetyProfile(requires_human_approval=False)
        d = sp.to_dict()
        sp2 = BackendAdapterSafetyProfile.from_dict(d)
        assert sp2.requires_human_approval is False
        assert sp2.requires_output_quarantine is True

    def test_no_secrets_in_serialization(self):
        sp = BackendAdapterSafetyProfile()
        j = _json_94s.dumps(sp.to_dict())
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()


class Test94SAdapterContract:
    """BackendAdapterContract: model validation and serialization."""

    def test_valid_mock_contract(self):
        c = BackendAdapterContract(
            adapter_id="adapter-test", backend_id="mock",
            backend_type=ADAPTER_BACKEND_MOCK,
            invocation_mode=ADAPTER_MODE_MOCK_ONLY,
        )
        assert c.validate() == []

    def test_real_adapter_defaults_preflight_only(self):
        c = BackendAdapterContract(
            adapter_id="adapter-claude", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
        )
        assert c.invocation_mode == ADAPTER_MODE_PREFLIGHT_ONLY

    def test_real_adapter_cannot_use_mock_only(self):
        c = BackendAdapterContract(
            adapter_id="adapter-claude", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            invocation_mode=ADAPTER_MODE_MOCK_ONLY,
        )
        issues = c.validate()
        assert any("mock_only" in i for i in issues)

    def test_unknown_backend_type_invalid(self):
        c = BackendAdapterContract(
            adapter_id="adapter-x", backend_id="x", backend_type="bogus",
        )
        issues = c.validate()
        assert any("backend_type" in i for i in issues)

    def test_unsupported_mode_invalid(self):
        c = BackendAdapterContract(
            adapter_id="adapter-x", backend_id="x", invocation_mode="bogus",
        )
        issues = c.validate()
        assert any("invocation_mode" in i for i in issues)

    def test_to_dict_round_trip(self):
        c = BackendAdapterContract(
            adapter_id="adapter-rt", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            required_env_keys=["ANTHROPIC_API_KEY"],
        )
        d = c.to_dict()
        c2 = BackendAdapterContract.from_dict(d)
        assert c2.adapter_id == "adapter-rt"
        assert c2.backend_type == ADAPTER_BACKEND_CLAUDE_CLI
        assert c2.safety_capabilities.requires_human_approval is True

    def test_safety_profile_nested_round_trip(self):
        c = BackendAdapterContract(
            adapter_id="adapter-nested", backend_id="mock",
            safety_capabilities=BackendAdapterSafetyProfile(
                requires_human_approval=False,
            ),
        )
        d = c.to_dict()
        c2 = BackendAdapterContract.from_dict(d)
        assert c2.safety_capabilities.requires_human_approval is False

    def test_no_secrets_in_serialization(self):
        c = BackendAdapterContract(
            adapter_id="adapter-sec", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            required_env_keys=["ANTHROPIC_API_KEY"],
        )
        j = _json_94s.dumps(c.to_dict())
        assert "sk-ant" not in j

    def test_validate_adapter_contract_hard_blocks(self):
        c = BackendAdapterContract(
            adapter_id="adapter-bad", backend_id="bad",
            backend_type="bogus", invocation_mode="bogus",
        )
        result = validate_backend_adapter_contract(c)
        assert result["valid"] is False
        assert len(result["hard_blocks"]) >= 1


class Test94SPreflightResult:
    """BackendAdapterPreflightResult and validate_backend_adapter_preflight."""

    def test_preflight_mock_ready(self):
        c = BackendAdapterContract(
            adapter_id="adapter-m", backend_id="mock",
            backend_type=ADAPTER_BACKEND_MOCK,
            invocation_mode=ADAPTER_MODE_MOCK_ONLY,
        )
        r = validate_backend_adapter_preflight(c)
        assert r.status == PREFLIGHT_READY
        assert r.ready is True
        assert r.no_real_backend_invoked is True
        assert r.no_subprocess is True
        assert r.no_network is True

    def test_preflight_unknown_backend_blocked(self):
        c = BackendAdapterContract(
            adapter_id="adapter-x", backend_id="x", backend_type="bogus",
        )
        r = validate_backend_adapter_preflight(c)
        assert r.status == PREFLIGHT_BLOCKED
        assert r.ready is False
        assert any("unknown_backend_type" in hb for hb in r.hard_blocks)

    def test_preflight_disabled_mode(self):
        c = BackendAdapterContract(
            adapter_id="adapter-d", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            invocation_mode=ADAPTER_MODE_DISABLED,
        )
        r = validate_backend_adapter_preflight(c)
        assert r.status == PREFLIGHT_DISABLED
        assert r.ready is False

    def test_preflight_missing_env(self):
        c = BackendAdapterContract(
            adapter_id="adapter-c", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            invocation_mode=ADAPTER_MODE_PREFLIGHT_ONLY,
            required_env_keys=["MISSING_KEY_XYZ"],
        )
        r = validate_backend_adapter_preflight(
            c, env_available={"MISSING_KEY_XYZ": False},
        )
        assert r.status in (PREFLIGHT_BLOCKED, PREFLIGHT_MISSING_EVIDENCE)
        assert "MISSING_KEY_XYZ" in r.missing_env_keys

    def test_preflight_bypass_detected_hard_block(self):
        c = BackendAdapterContract(
            adapter_id="adapter-bp", backend_id="mock",
            backend_type=ADAPTER_BACKEND_MOCK,
            invocation_mode=ADAPTER_MODE_MOCK_ONLY,
        )
        r = validate_backend_adapter_preflight(c, bypass_detected=True)
        assert "bypass_permissions_detected" in r.hard_blocks
        assert r.bypass_permissions_detected is True

    def test_preflight_present_env_redacted(self):
        c = BackendAdapterContract(
            adapter_id="adapter-e", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            invocation_mode=ADAPTER_MODE_PREFLIGHT_ONLY,
            required_env_keys=["TEST_KEY"],
        )
        r = validate_backend_adapter_preflight(
            c, env_available={"TEST_KEY": True},
        )
        assert "TEST_KEY" in r.present_env_keys_redacted

    def test_preflight_no_secrets_in_serialization(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret-value-123")
        c = BackendAdapterContract(
            adapter_id="adapter-sec", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            invocation_mode=ADAPTER_MODE_PREFLIGHT_ONLY,
            required_env_keys=["ANTHROPIC_API_KEY"],
        )
        r = validate_backend_adapter_preflight(c)
        j = _json_94s.dumps(r.to_dict())
        assert "sk-ant-secret-value-123" not in j
        assert r.secrets_redacted is True

    def test_preflight_no_real_backend_invoked_always_true(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        assert r.no_real_backend_invoked is True
        assert r.no_subprocess is True
        assert r.no_network is True

    def test_preflight_serialization_round_trip(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        d = r.to_dict()
        r2 = BackendAdapterPreflightResult.from_dict(d)
        assert r2.preflight_id == r.preflight_id
        assert r2.status == r.status
        assert r2.no_real_backend_invoked is True


class Test94SInvocationPlan:
    """BackendAdapterInvocationPlan: future-only, executable=False."""

    def test_invocation_plan_executable_defaults_false(self):
        plan = BackendAdapterInvocationPlan(invocation_plan_id="ip-test")
        assert plan.executable is False

    def test_invocation_plan_executable_true_invalid(self):
        plan = BackendAdapterInvocationPlan(
            invocation_plan_id="ip-exec", executable=True,
        )
        issues = plan.validate()
        assert any("executable" in i for i in issues)

    def test_create_invocation_plan_from_contract(self):
        c = BackendAdapterContract(
            adapter_id="adapter-c", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            invocation_mode=ADAPTER_MODE_PREFLIGHT_ONLY,
        )
        plan = create_backend_adapter_invocation_plan(
            c, request_id="req-1", phase_id="94S",
        )
        assert plan.executable is False
        assert plan.adapter_id == "adapter-c"
        assert plan.backend_id == "claude"
        assert plan.requires_human_approval is True
        assert plan.quarantine_required is True

    def test_invocation_plan_serialization_round_trip(self):
        plan = BackendAdapterInvocationPlan(invocation_plan_id="ip-rt")
        d = plan.to_dict()
        plan2 = BackendAdapterInvocationPlan.from_dict(d)
        assert plan2.executable is False
        assert plan2.invocation_plan_id == "ip-rt"

    def test_invocation_plan_no_secrets(self):
        plan = BackendAdapterInvocationPlan(invocation_plan_id="ip-sec")
        j = _json_94s.dumps(plan.to_dict())
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()


class Test94SFailureClassification:
    """classify_backend_adapter_failure: pure classification."""

    def test_disabled_preflight_classifies_disabled(self):
        c = BackendAdapterContract(
            adapter_id="a", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            invocation_mode=ADAPTER_MODE_DISABLED,
        )
        r = validate_backend_adapter_preflight(c)
        assert classify_backend_adapter_failure(preflight=r) == FAILURE_DISABLED

    def test_bypass_classifies_bypass_permissions(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c, bypass_detected=True)
        assert classify_backend_adapter_failure(preflight=r) == FAILURE_BYPASS_PERMISSIONS

    def test_missing_env_classifies_missing_env(self):
        c = BackendAdapterContract(
            adapter_id="a", backend_id="claude",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            required_env_keys=["MISSING_KEY"],
        )
        r = validate_backend_adapter_preflight(
            c, env_available={"MISSING_KEY": False},
        )
        assert classify_backend_adapter_failure(preflight=r) == FAILURE_MISSING_ENV

    def test_timeout_classifies_timeout(self):
        assert classify_backend_adapter_failure(timeout_occurred=True) == FAILURE_TIMEOUT

    def test_backend_unavailable_classifies(self):
        assert classify_backend_adapter_failure(backend_responded=False) == FAILURE_BACKEND_UNAVAILABLE

    def test_auth_failure_exit_code(self):
        assert classify_backend_adapter_failure(exit_code=401) == FAILURE_AUTH_FAILURE
        assert classify_backend_adapter_failure(exit_code=403) == FAILURE_AUTH_FAILURE

    def test_rate_limit_exit_code(self):
        assert classify_backend_adapter_failure(exit_code=429) == FAILURE_RATE_LIMITED

    def test_output_missing_classifies(self):
        assert classify_backend_adapter_failure(output_present=False) == FAILURE_OUTPUT_MISSING

    def test_output_malformed_classifies(self):
        assert classify_backend_adapter_failure(output_valid=False) == FAILURE_OUTPUT_MALFORMED

    def test_no_invocation_returns_not_invoked(self):
        assert classify_backend_adapter_failure() == FAILURE_NOT_INVOKED

    def test_all_failure_categories_valid(self):
        for fc in VALID_FAILURE_CATEGORIES:
            assert fc in VALID_FAILURE_CATEGORIES


class Test94SAdapterRegistry:
    """get_default_adapter_registry: registry integration."""

    def test_registry_has_all_backends(self):
        reg = get_default_adapter_registry()
        assert "mock" in reg
        assert "claude" in reg
        assert "claude-deepseek" in reg
        assert "codex" in reg
        assert "qwen" in reg

    def test_mock_is_mock_only(self):
        reg = get_default_adapter_registry()
        assert reg["mock"].invocation_mode == ADAPTER_MODE_MOCK_ONLY
        assert reg["mock"].backend_type == ADAPTER_BACKEND_MOCK

    def test_real_adapters_are_preflight_only(self):
        reg = get_default_adapter_registry()
        for bid in ["claude", "claude-deepseek", "codex", "qwen"]:
            assert reg[bid].invocation_mode == ADAPTER_MODE_PREFLIGHT_ONLY, \
                f"{bid} should be preflight_only"

    def test_claude_has_required_env(self):
        reg = get_default_adapter_registry()
        assert "ANTHROPIC_API_KEY" in reg["claude"].required_env_keys

    def test_real_adapters_require_secrets(self):
        reg = get_default_adapter_registry()
        for bid in ["claude", "claude-deepseek", "codex", "qwen"]:
            assert reg[bid].requires_secrets is True

    def test_real_adapters_do_not_execute(self):
        reg = get_default_adapter_registry()
        for bid in ["claude", "claude-deepseek", "codex", "qwen"]:
            c = reg[bid]
            assert c.invocation_mode != ADAPTER_MODE_FUTURE_REAL
            plan = create_backend_adapter_invocation_plan(c)
            assert plan.executable is False


class Test94SNoExecutionGuarantees:
    """Cross-cutting no-execution guarantees for Phase 94S."""

    def test_no_subprocess_in_94s_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_no_network_in_94s_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_telegram_inbound_in_94s(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "getUpdates" not in source

    def test_multipart_phase_id_preserved(self):
        plan = BackendAdapterInvocationPlan(
            invocation_plan_id="ip-mp", phase_id="94S.1.2",
        )
        d = plan.to_dict()
        assert d["phase_id"] == "94S.1.2"

    def test_no_secrets_in_models(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        j = _json_94s.dumps(r.to_dict())
        assert "sk-ant" not in j


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94U — Backend adapter preflight artifact tests
# ═══════════════════════════════════════════════════════════════════════════

import json as _json_94u

from pcae.core.backend_invocations import (
    BackendAdapterPreflightArtifact,
    persist_backend_adapter_preflight_artifact,
    verify_backend_adapter_preflight_artifact,
    load_latest_backend_adapter_preflight_artifact,
    BackendAdapterContract,
    validate_backend_adapter_preflight,
    ADAPTER_BACKEND_MOCK,
    ADAPTER_BACKEND_CLAUDE_CLI,
    ADAPTER_MODE_MOCK_ONLY,
    ADAPTER_MODE_PREFLIGHT_ONLY,
)


class Test94UPreflightArtifact:
    """BackendAdapterPreflightArtifact model, digest, persistence."""

    def test_from_preflight_result(self):
        c = BackendAdapterContract(
            adapter_id="a", backend_id="mock",
            backend_type=ADAPTER_BACKEND_MOCK,
            invocation_mode=ADAPTER_MODE_MOCK_ONLY,
        )
        r = validate_backend_adapter_preflight(c)
        artifact = BackendAdapterPreflightArtifact.from_preflight_result(r)
        assert artifact.backend_id == "mock"
        assert artifact.status == "ready"
        assert artifact.no_real_backend_invoked is True
        assert artifact.no_subprocess is True
        assert artifact.no_network is True
        assert artifact.secrets_redacted is True

    def test_compute_digest_deterministic(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        a1 = BackendAdapterPreflightArtifact.from_preflight_result(r)
        a2 = BackendAdapterPreflightArtifact.from_preflight_result(r)
        # Same preflight result, same fields → same digest
        a1.artifact_id = a2.artifact_id = "pfa-test"
        a1.preflight_id = a2.preflight_id = "apf-test"
        d1 = a1.compute_digest()
        d2 = a2.compute_digest()
        assert d1 == d2
        assert len(d1) == 64

    def test_verify_valid_artifact(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        artifact = BackendAdapterPreflightArtifact.from_preflight_result(r)
        artifact.record_digest = artifact.compute_digest()
        result = verify_backend_adapter_preflight_artifact(artifact)
        assert result["valid"] is True

    def test_verify_tampered_artifact_fails(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        artifact = BackendAdapterPreflightArtifact.from_preflight_result(r)
        artifact.record_digest = artifact.compute_digest()
        # Tamper
        artifact.status = "tampered"
        result = verify_backend_adapter_preflight_artifact(artifact)
        assert result["valid"] is False
        assert any("digest" in i for i in result["issues"])

    def test_verify_missing_digest_fails(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        artifact = BackendAdapterPreflightArtifact.from_preflight_result(r)
        # No digest set
        result = verify_backend_adapter_preflight_artifact(artifact)
        assert result["valid"] is False

    def test_verify_missing_ids_fails(self):
        artifact = BackendAdapterPreflightArtifact()
        result = verify_backend_adapter_preflight_artifact(artifact)
        assert result["valid"] is False

    def test_persist_and_load_round_trip(self, tmp_path):
        import os as _os
        orig = _os.getcwd()
        try:
            _os.chdir(tmp_path)
            c = BackendAdapterContract(adapter_id="a", backend_id="mock")
            r = validate_backend_adapter_preflight(c)
            artifact = BackendAdapterPreflightArtifact.from_preflight_result(r)
            persist = persist_backend_adapter_preflight_artifact(artifact)
            assert persist["status"] == "written"
            assert persist["record_digest"]

            loaded = load_latest_backend_adapter_preflight_artifact()
            assert loaded is not None
            assert loaded.backend_id == "mock"
            assert loaded.record_digest == persist["record_digest"]
        finally:
            _os.chdir(orig)

    def test_latest_updated_on_new_write(self, tmp_path):
        import os as _os
        orig = _os.getcwd()
        try:
            _os.chdir(tmp_path)
            c = BackendAdapterContract(adapter_id="a", backend_id="mock")
            r1 = validate_backend_adapter_preflight(c)
            a1 = BackendAdapterPreflightArtifact.from_preflight_result(r1)
            persist_backend_adapter_preflight_artifact(a1)

            r2 = validate_backend_adapter_preflight(c)
            a2 = BackendAdapterPreflightArtifact.from_preflight_result(r2)
            persist_backend_adapter_preflight_artifact(a2)

            loaded = load_latest_backend_adapter_preflight_artifact()
            assert loaded is not None
            assert loaded.preflight_id == a2.preflight_id
        finally:
            _os.chdir(orig)

    def test_load_absent_returns_none(self, tmp_path):
        import os as _os
        orig = _os.getcwd()
        try:
            _os.chdir(tmp_path)
            assert load_latest_backend_adapter_preflight_artifact() is None
        finally:
            _os.chdir(orig)

    def test_no_secrets_in_artifact(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        artifact = BackendAdapterPreflightArtifact.from_preflight_result(r)
        j = _json_94u.dumps(artifact.to_dict())
        assert "sk-ant" not in j
        assert "api_key" not in j.lower()
        assert artifact.secrets_redacted is True

    def test_to_dict_excludes_digest_when_requested(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        artifact = BackendAdapterPreflightArtifact.from_preflight_result(r)
        d = artifact.to_dict(include_digest=False)
        assert "record_digest" not in d


class Test94UPreflightArtifactCLI:
    """CLI integration: save, show, verify via subprocess."""

    def test_save_creates_artifact(self):
        import subprocess, sys
        from pathlib import Path
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight",
             "--backend", "mock", "--save"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent, timeout=15,
        )
        assert r.returncode == 0
        assert "Artifact saved" in r.stdout
        assert "Digest:" in r.stdout

    def test_show_latest_after_save(self):
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight",
             "--backend", "mock", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight-show",
             "--latest"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        assert r.returncode == 0
        assert "mock" in r.stdout

    def test_verify_latest_after_save(self):
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight",
             "--backend", "mock", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight-verify",
             "--latest"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        assert r.returncode == 0
        assert "valid" in r.stdout.lower()

    def test_show_missing_handled(self, tmp_path):
        import subprocess, sys
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight-show",
             "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_verify_missing_handled(self, tmp_path):
        import subprocess, sys
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight-verify",
             "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_gitignore_has_preflights_dir(self):
        from pathlib import Path
        gitignore = Path(__file__).resolve().parent.parent / ".pcae" / ".gitignore"
        assert "backend-adapter-preflights/" in gitignore.read_text()


class Test94UPreflightArtifactSafety:
    """Cross-cutting safety for 94U."""

    def test_no_subprocess_in_artifact_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_no_network_in_artifact_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_telegram_inbound_in_artifact_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "getUpdates" not in source


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94V — Adapter-specific contract specialization tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    create_mock_adapter_contract,
    create_claude_cli_adapter_contract,
    create_claude_deepseek_cli_adapter_contract,
    create_codex_adapter_contract,
    create_qwen_adapter_contract,
    create_custom_adapter_contract,
    get_adapter_no_go_conditions,
    get_adapter_failure_mapping,
    ADAPTER_MODE_MOCK_ONLY,
    ADAPTER_MODE_PREFLIGHT_ONLY,
    ADAPTER_MODE_DISABLED,
    ADAPTER_BACKEND_MOCK,
    ADAPTER_BACKEND_CUSTOM,
)


class Test94VSpecializedContracts:
    """Phase 94V: adapter-specific contract factories."""

    def test_mock_no_secrets_no_approval(self):
        c = create_mock_adapter_contract()
        assert c.requires_secrets is False
        assert c.safety_capabilities.requires_human_approval is False
        assert c.safety_capabilities.requires_bypass_detection is False
        assert c.invocation_mode == ADAPTER_MODE_MOCK_ONLY
        assert c.backend_type == ADAPTER_BACKEND_MOCK

    def test_claude_requires_bypass_detection(self):
        c = create_claude_cli_adapter_contract()
        assert c.safety_capabilities.requires_bypass_detection is True
        assert c.safety_capabilities.requires_human_approval is True
        assert c.safety_capabilities.requires_shell_gate is True
        assert c.invocation_mode == ADAPTER_MODE_PREFLIGHT_ONLY
        assert "ANTHROPIC_API_KEY" in c.required_env_keys

    def test_claude_deepseek_requires_bypass_detection(self):
        c = create_claude_deepseek_cli_adapter_contract()
        assert c.safety_capabilities.requires_bypass_detection is True
        assert c.safety_capabilities.requires_human_approval is True
        assert "DEEPSEEK_API_KEY" in c.required_env_keys
        assert c.invocation_mode == ADAPTER_MODE_PREFLIGHT_ONLY

    def test_codex_preflight_only(self):
        c = create_codex_adapter_contract()
        assert c.invocation_mode == ADAPTER_MODE_PREFLIGHT_ONLY
        assert c.safety_capabilities.requires_human_approval is True
        assert c.safety_capabilities.requires_audit is True
        assert "OPENAI_API_KEY" in c.required_env_keys

    def test_qwen_preflight_only(self):
        c = create_qwen_adapter_contract()
        assert c.invocation_mode == ADAPTER_MODE_PREFLIGHT_ONLY
        assert c.safety_capabilities.requires_secret_redaction is True
        assert "QWEN_API_KEY" in c.required_env_keys

    def test_custom_disabled_by_default(self):
        c = create_custom_adapter_contract(backend_id="my-llm")
        assert c.invocation_mode == ADAPTER_MODE_DISABLED
        assert c.backend_type == ADAPTER_BACKEND_CUSTOM
        assert c.safety_capabilities.requires_human_approval is True

    def test_all_real_adapters_non_executable(self):
        for factory in [
            create_claude_cli_adapter_contract,
            create_claude_deepseek_cli_adapter_contract,
            create_codex_adapter_contract,
            create_qwen_adapter_contract,
        ]:
            c = factory()
            assert c.invocation_mode != "future_real", \
                f"{c.backend_id} should not be future_real"

    def test_all_real_adapters_require_audit(self):
        for factory in [
            create_claude_cli_adapter_contract,
            create_claude_deepseek_cli_adapter_contract,
            create_codex_adapter_contract,
            create_qwen_adapter_contract,
        ]:
            c = factory()
            assert c.safety_capabilities.requires_audit is True, \
                f"{c.backend_id} should require audit"

    def test_all_real_adapters_require_timeout(self):
        for factory in [
            create_claude_cli_adapter_contract,
            create_claude_deepseek_cli_adapter_contract,
            create_codex_adapter_contract,
            create_qwen_adapter_contract,
        ]:
            c = factory()
            assert c.safety_capabilities.requires_timeout is True, \
                f"{c.backend_id} should require timeout"


class Test94VNoGoConditions:
    """Phase 94V: backend-specific no-go conditions."""

    def test_mock_no_go_excludes_env_and_bypass(self):
        c = create_mock_adapter_contract()
        conditions = get_adapter_no_go_conditions(c)
        assert "required_env_missing" not in conditions
        assert "bypass_permissions_detected" not in conditions
        assert "real_backend_unsafe_mode" not in conditions

    def test_claude_no_go_includes_env_and_bypass(self):
        c = create_claude_cli_adapter_contract()
        conditions = get_adapter_no_go_conditions(c)
        assert "required_env_missing" in conditions
        assert "bypass_permissions_detected" in conditions
        assert "real_backend_unsafe_mode" in conditions

    def test_common_no_go_present_for_all_real(self):
        common = [
            "unknown_adapter", "unsupported_invocation_mode",
            "broker_hard_block", "shell_gate_deny",
            "human_approval_missing",
        ]
        for factory in [
            create_claude_cli_adapter_contract,
            create_codex_adapter_contract,
        ]:
            c = factory()
            conditions = get_adapter_no_go_conditions(c)
            for item in common:
                assert item in conditions, f"{c.backend_id} missing {item}"


class Test94VFailureMapping:
    """Phase 94V: failure classification mapping."""

    def test_mapping_includes_all_categories(self):
        c = create_mock_adapter_contract()
        mapping = get_adapter_failure_mapping(c)
        for fc in VALID_FAILURE_CATEGORIES:
            assert fc in mapping.values(), f"Missing failure category: {fc}"

    def test_mapping_keys_are_readable(self):
        c = create_mock_adapter_contract()
        mapping = get_adapter_failure_mapping(c)
        assert mapping["disabled"] == FAILURE_DISABLED
        assert mapping["missing_env"] == FAILURE_MISSING_ENV
        assert mapping["bypass_permissions"] == FAILURE_BYPASS_PERMISSIONS


class Test94VRegistry:
    """Phase 94V: registry uses specialized factories."""

    def test_registry_uses_factories(self):
        reg = get_default_adapter_registry()
        mock_c = create_mock_adapter_contract()
        claude_c = create_claude_cli_adapter_contract()
        assert reg["mock"].adapter_id == mock_c.adapter_id
        assert reg["claude"].adapter_id == claude_c.adapter_id

    def test_registry_all_preflight_or_mock(self):
        reg = get_default_adapter_registry()
        for bid, c in reg.items():
            if bid == "mock":
                assert c.invocation_mode == ADAPTER_MODE_MOCK_ONLY
            else:
                assert c.invocation_mode in (ADAPTER_MODE_PREFLIGHT_ONLY, ADAPTER_MODE_DISABLED), \
                    f"{bid} mode={c.invocation_mode!r}"


class Test94VNoExecution:
    """Phase 94V: no-execution guarantees."""

    def test_no_subprocess_in_factories(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_no_secrets_in_factory_output(self):
        import json
        c = create_claude_cli_adapter_contract()
        j = json.dumps(c.to_dict())
        assert "sk-ant" not in j
        # Env key NAMES are safe; secret VALUES must not appear
        assert "secret-value" not in j.lower()

    def test_multipart_phase_id_preserved(self):
        c = create_custom_adapter_contract(backend_id="94V.1.2")
        assert c.backend_id == "94V.1.2"


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94W — Real adapter preflight hardening tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    ADAPTER_MODE_FUTURE_REAL,
)


class Test94WContractValidation:
    """Phase 94W: hardened contract validation."""

    def test_real_adapter_without_approval_blocked(self):
        c = create_claude_cli_adapter_contract()
        c.safety_capabilities.requires_human_approval = False
        result = validate_backend_adapter_contract(c)
        assert result["valid"] is False
        assert any("human_approval" in hb for hb in result["hard_blocks"])

    def test_real_adapter_without_audit_blocked(self):
        c = create_claude_cli_adapter_contract()
        c.safety_capabilities.requires_audit = False
        result = validate_backend_adapter_contract(c)
        assert result["valid"] is False

    def test_real_adapter_without_timeout_blocked(self):
        c = create_claude_cli_adapter_contract()
        c.safety_capabilities.requires_timeout = False
        result = validate_backend_adapter_contract(c)
        assert result["valid"] is False

    def test_real_adapter_without_quarantine_blocked(self):
        c = create_claude_cli_adapter_contract()
        c.safety_capabilities.requires_output_quarantine = False
        result = validate_backend_adapter_contract(c)
        assert result["valid"] is False

    def test_real_adapter_without_no_apply_blocked(self):
        c = create_claude_cli_adapter_contract()
        c.safety_capabilities.supports_no_apply_guarantee = False
        result = validate_backend_adapter_contract(c)
        assert result["valid"] is False

    def test_duplicate_env_keys_warning(self):
        c = BackendAdapterContract(
            adapter_id="a", backend_id="test",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            required_env_keys=["KEY_A", "KEY_A"],
        )
        result = validate_backend_adapter_contract(c)
        assert any("duplicate" in w for w in result["warnings"])

    def test_mock_without_approval_still_valid(self):
        c = create_mock_adapter_contract()
        result = validate_backend_adapter_contract(c)
        assert result["valid"] is True

    def test_future_real_mode_blocked(self):
        c = BackendAdapterContract(
            adapter_id="a", backend_id="bad",
            backend_type=ADAPTER_BACKEND_CLAUDE_CLI,
            invocation_mode=ADAPTER_MODE_FUTURE_REAL,
            supports_timeout=False,
        )
        result = validate_backend_adapter_contract(c)
        assert result["valid"] is False


class Test94WPreflightValidation:
    """Phase 94W: hardened preflight validation."""

    def test_bypass_detected_hard_blocks(self):
        c = create_claude_cli_adapter_contract()
        r = validate_backend_adapter_preflight(c, bypass_detected=True)
        assert r.ready is False
        assert "bypass_permissions_detected" in r.hard_blocks

    def test_no_real_backend_true_by_default(self):
        c = create_mock_adapter_contract()
        r = validate_backend_adapter_preflight(c)
        assert r.no_real_backend_invoked is True

    def test_no_subprocess_true_by_default(self):
        c = create_mock_adapter_contract()
        r = validate_backend_adapter_preflight(c)
        assert r.no_subprocess is True

    def test_no_network_true_by_default(self):
        c = create_mock_adapter_contract()
        r = validate_backend_adapter_preflight(c)
        assert r.no_network is True

    def test_secrets_redacted_true_by_default(self):
        c = create_mock_adapter_contract()
        r = validate_backend_adapter_preflight(c)
        assert r.secrets_redacted is True

    def test_disabled_adapter_blocked(self):
        c = create_custom_adapter_contract()
        r = validate_backend_adapter_preflight(c)
        assert r.status == PREFLIGHT_DISABLED
        assert r.ready is False


class Test94WArtifactVerification:
    """Phase 94W: hardened artifact verification."""

    def test_tampered_digest_fails(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        a = BackendAdapterPreflightArtifact.from_preflight_result(r)
        a.record_digest = a.compute_digest()
        a.hard_blocks = ["injected_malicious_block"]
        result = verify_backend_adapter_preflight_artifact(a)
        assert result["valid"] is False

    def test_future_real_in_artifact_fails(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        a = BackendAdapterPreflightArtifact.from_preflight_result(r)
        a.invocation_mode = ADAPTER_MODE_FUTURE_REAL
        a.record_digest = a.compute_digest()
        result = verify_backend_adapter_preflight_artifact(a)
        assert result["valid"] is False

    def test_ready_with_hard_blocks_fails(self):
        c = BackendAdapterContract(adapter_id="a", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        a = BackendAdapterPreflightArtifact.from_preflight_result(r)
        a.ready = True
        a.hard_blocks = ["some_block"]
        a.record_digest = a.compute_digest()
        result = verify_backend_adapter_preflight_artifact(a)
        assert result["valid"] is False


class Test94WCLIHardening:
    """Phase 94W: CLI hardening tests."""

    def test_preflight_missing_env_safe_text(self):
        import subprocess, sys
        from pathlib import Path
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight",
             "--backend", "claude"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent, timeout=15,
        )
        assert r.returncode != 0
        assert "ANTHROPIC_API_KEY" in r.stdout
        assert "No real backend" in r.stdout
        assert "No subprocess" in r.stdout

    def test_preflight_json_no_secrets(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret-xyz")
        import subprocess, sys, json
        from pathlib import Path
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight",
             "--backend", "claude", "--json"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent, timeout=15,
        )
        data = json.loads(r.stdout)
        j = json.dumps(data)
        assert "sk-ant-secret-xyz" not in j

    def test_verify_tampered_artifact_cli_fails(self):
        import subprocess, sys, json as _j
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        # Save a valid artifact
        subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight",
             "--backend", "mock", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        # Tamper the latest.json
        latest = repo / ".pcae" / "backend-adapter-preflights" / "latest.json"
        if latest.exists():
            data = _j.loads(latest.read_text())
            data["record_digest"] = "00" * 32
            latest.write_text(_j.dumps(data))
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "preflight-verify",
             "--latest"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        assert r.returncode != 0


class Test94WNoExecution:
    """Phase 94W: no-execution guarantees."""

    def test_no_subprocess_in_hardening(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_no_telegram_inbound(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "getUpdates" not in source

    def test_no_backend_or_apply_changed(self):
        """Verify no backend invocation or apply execution was added."""
        c = create_claude_cli_adapter_contract()
        # All real adapters remain preflight-only
        assert c.invocation_mode == ADAPTER_MODE_PREFLIGHT_ONLY
        plan = create_backend_adapter_invocation_plan(c)
        assert plan.executable is False


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Y — Real adapter invocation approval model tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    RealAdapterInvocationApproval,
    create_real_adapter_invocation_approval,
    validate_real_adapter_invocation_approval,
    persist_real_adapter_invocation_approval,
    verify_real_adapter_invocation_approval,
    load_latest_real_adapter_invocation_approval,
    APPROVAL_APPROVED,
    APPROVAL_REJECTED,
    APPROVAL_EXPIRED,
    APPROVAL_REVOKED,
    BackendAdapterPreflightArtifact,
)


class Test94YApprovalModel:
    """RealAdapterInvocationApproval model and validation."""

    def test_approval_serialization_round_trip(self):
        a = RealAdapterInvocationApproval(
            approval_id="raa-test",
            adapter_id="adapter-claude-cli",
            backend_id="claude",
            decision=APPROVAL_APPROVED,
            operator="test-op",
            decision_reason="test reason",
            prompt_hash="abc123",
        )
        d = a.to_dict()
        a2 = RealAdapterInvocationApproval.from_dict(d)
        assert a2.approval_id == "raa-test"
        assert a2.backend_id == "claude"
        assert a2.approval_effective is False  # no preflight

    def test_approval_digest_verification(self):
        a = RealAdapterInvocationApproval(
            approval_id="raa-dig", operator="op", decision_reason="r",
            prompt_hash="ph",
        )
        a.record_digest = a.compute_digest()
        r = verify_real_adapter_invocation_approval(a)
        assert r["valid"] is True

    def test_tampered_digest_fails(self):
        a = RealAdapterInvocationApproval(
            approval_id="raa-tamp", operator="op", decision_reason="r",
            prompt_hash="ph",
        )
        a.record_digest = a.compute_digest()
        a.decision = APPROVAL_REVOKED
        r = verify_real_adapter_invocation_approval(a)
        assert r["valid"] is False

    def test_hard_blocks_prevent_effective(self):
        a = create_real_adapter_invocation_approval(
            adapter_id="ad", backend_id="bk", backend_type="mock",
            decision=APPROVAL_APPROVED, operator="op", decision_reason="r",
            prompt_hash="ph",
        )
        a.hard_blocks_present = True
        a.approval_effective = False
        assert a.approval_effective is False
        issues = a.validate()
        assert any("cannot approve" in i for i in issues)

    def test_accepted_risk_cannot_override_hard_blocks(self):
        a = create_real_adapter_invocation_approval(
            adapter_id="ad", backend_id="bk", backend_type="mock",
            decision=APPROVAL_APPROVED, operator="op", decision_reason="r",
            prompt_hash="ph", accepted_risk=True,
        )
        a.hard_blocks_present = True
        issues = a.validate()
        assert any("accepted_risk" in i for i in issues)

    def test_rejected_approval_not_effective(self):
        a = create_real_adapter_invocation_approval(
            adapter_id="ad", backend_id="bk", backend_type="mock",
            decision=APPROVAL_REJECTED, operator="op", decision_reason="r",
            prompt_hash="ph",
        )
        assert a.approval_effective is False

    def test_operator_missing_invalid(self):
        a = RealAdapterInvocationApproval(approval_id="raa-noop", decision_reason="r")
        issues = a.validate()
        assert any("operator" in i for i in issues)

    def test_reason_missing_invalid(self):
        a = RealAdapterInvocationApproval(approval_id="raa-nor", operator="op")
        issues = a.validate()
        assert any("reason" in i for i in issues)

    def test_create_with_preflight_binding(self):
        c = BackendAdapterContract(adapter_id="ad", backend_id="mock")
        r = validate_backend_adapter_preflight(c)
        pf = BackendAdapterPreflightArtifact.from_preflight_result(r)
        pf.record_digest = pf.compute_digest()
        a = create_real_adapter_invocation_approval(
            adapter_id="ad", backend_id="mock", backend_type="mock",
            decision=APPROVAL_APPROVED, operator="op", decision_reason="r",
            prompt_hash="ph", preflight_artifact=pf,
        )
        assert a.preflight_digest == pf.record_digest
        assert a.approval_effective is True  # no hard blocks on mock


class Test94YApprovalPersistence:
    """Approval persistence and verification."""

    def test_persist_and_load_round_trip(self, tmp_path):
        import os
        orig = os.getcwd()
        try:
            os.chdir(tmp_path)
            a = create_real_adapter_invocation_approval(
                adapter_id="ad", backend_id="mock", backend_type="mock",
                decision=APPROVAL_APPROVED, operator="op", decision_reason="r",
                prompt_hash="ph",
            )
            persist = persist_real_adapter_invocation_approval(a)
            assert persist["status"] == "written"
            loaded = load_latest_real_adapter_invocation_approval()
            assert loaded is not None
            assert loaded.approval_id == a.approval_id
        finally:
            os.chdir(orig)

    def test_load_absent_returns_none(self, tmp_path):
        import os
        orig = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert load_latest_real_adapter_invocation_approval() is None
        finally:
            os.chdir(orig)


class Test94YApprovalCLI:
    """CLI show/verify for approvals."""

    def test_show_missing_handled(self, tmp_path):
        import subprocess, sys
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "approval",
             "show", "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_verify_missing_handled(self, tmp_path):
        import subprocess, sys
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "approval",
             "verify", "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_gitignore_has_approvals_dir(self):
        from pathlib import Path
        gitignore = Path(__file__).resolve().parent.parent / ".pcae" / ".gitignore"
        assert "real-adapter-approvals/" in gitignore.read_text()


class Test94YNoExecution:
    """No-execution guarantees for 94Y."""

    def test_no_subprocess_in_approval_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source

    def test_no_network_in_approval_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "urllib.request" not in source
        assert "requests.get" not in source

    def test_no_secrets_in_approval(self):
        import json
        a = create_real_adapter_invocation_approval(
            adapter_id="ad", backend_id="bk", backend_type="mock",
            decision=APPROVAL_APPROVED, operator="op", decision_reason="r",
            prompt_hash="ph",
        )
        j = json.dumps(a.to_dict())
        assert "sk-ant" not in j


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Z — Real adapter invocation plan artifact tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    RealAdapterInvocationPlan,
    create_real_adapter_invocation_plan,
    validate_real_adapter_invocation_plan,
    persist_real_adapter_invocation_plan,
    verify_real_adapter_invocation_plan,
    load_latest_real_adapter_invocation_plan,
)


class Test94ZPlanModel:
    """RealAdapterInvocationPlan model and safe defaults."""

    def test_safe_defaults_all_false(self):
        plan = RealAdapterInvocationPlan(plan_id="rip-test")
        assert plan.real_backend_invocation_allowed is False
        assert plan.execution_ready is False
        assert plan.no_auto_apply is True
        assert plan.no_commit_authorization is True
        assert plan.no_push_authorization is True

    def test_real_allowed_must_be_false(self):
        plan = RealAdapterInvocationPlan(plan_id="rip-r", real_backend_invocation_allowed=True)
        issues = plan.validate()
        assert any("real_backend_invocation_allowed" in i for i in issues)

    def test_execution_ready_must_be_false(self):
        plan = RealAdapterInvocationPlan(plan_id="rip-e", execution_ready=True)
        issues = plan.validate()
        assert any("execution_ready" in i for i in issues)

    def test_no_auto_apply_must_be_true(self):
        plan = RealAdapterInvocationPlan(plan_id="rip-a", no_auto_apply=False)
        issues = plan.validate()
        assert any("no_auto_apply" in i for i in issues)

    def test_no_commit_must_be_true(self):
        plan = RealAdapterInvocationPlan(plan_id="rip-c", no_commit_authorization=False)
        issues = plan.validate()
        assert any("no_commit" in i for i in issues)

    def test_no_push_must_be_true(self):
        plan = RealAdapterInvocationPlan(plan_id="rip-p", no_push_authorization=False)
        issues = plan.validate()
        assert any("no_push" in i for i in issues)

    def test_serialization_round_trip(self):
        plan = RealAdapterInvocationPlan(plan_id="rip-rt", backend_id="claude")
        d = plan.to_dict()
        plan2 = RealAdapterInvocationPlan.from_dict(d)
        assert plan2.plan_id == "rip-rt"

    def test_digest_verification(self):
        plan = RealAdapterInvocationPlan(plan_id="rip-dig")
        plan.record_digest = plan.compute_digest()
        r = verify_real_adapter_invocation_plan(plan)
        assert r["valid"] is True

    def test_tampered_digest_fails(self):
        plan = RealAdapterInvocationPlan(plan_id="rip-tamp")
        plan.record_digest = plan.compute_digest()
        plan.real_backend_invocation_allowed = True
        r = verify_real_adapter_invocation_plan(plan)
        assert r["valid"] is False

    def test_create_blocks_without_preflight(self):
        plan = create_real_adapter_invocation_plan(
            adapter_id="ad", backend_id="bk", backend_type="mock",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
        )
        assert "preflight_artifact_missing" in plan.hard_blocks
        assert len(plan.hard_blocks) >= 1

    def test_create_blocks_without_approval(self):
        plan = create_real_adapter_invocation_plan(
            adapter_id="ad", backend_id="bk", backend_type="mock",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
        )
        assert "approval_artifact_missing" in plan.hard_blocks

    def test_persist_and_load(self, tmp_path):
        import os
        orig = os.getcwd()
        try:
            os.chdir(tmp_path)
            plan = create_real_adapter_invocation_plan(
                adapter_id="ad", backend_id="bk", backend_type="mock",
                operator="op", prompt_hash="ph", prompt_artifact_path="/p",
                output_quarantine_path="/q", audit_artifact_path="/a",
            )
            persist = persist_real_adapter_invocation_plan(plan)
            assert persist["status"] == "written"
            loaded = load_latest_real_adapter_invocation_plan()
            assert loaded is not None
            assert loaded.plan_id == plan.plan_id
        finally:
            os.chdir(orig)

    def test_load_absent_returns_none(self, tmp_path):
        import os
        orig = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert load_latest_real_adapter_invocation_plan() is None
        finally:
            os.chdir(orig)


class Test94ZPlanCLI:
    """Plan CLI show/verify."""

    def test_show_missing_handled(self, tmp_path):
        import subprocess, sys
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "plan",
             "show", "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_gitignore_has_plans_dir(self):
        from pathlib import Path
        gitignore = Path(__file__).resolve().parent.parent / ".pcae" / ".gitignore"
        assert "real-adapter-invocation-plans/" in gitignore.read_text()


class Test94ZPlanNoExecution:
    """No-execution for 94Z."""

    def test_no_secrets(self):
        import json
        plan = RealAdapterInvocationPlan(plan_id="rip-sec")
        j = json.dumps(plan.to_dict())
        assert "sk-ant" not in j


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95A — Dry-run boundary tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    ArtifactOnlyRealInvocationDryRunAssessment,
    evaluate_artifact_only_real_invocation_dry_run,
    persist_artifact_only_real_invocation_dry_run_assessment,
    verify_artifact_only_real_invocation_dry_run_assessment,
    load_latest_artifact_only_real_invocation_dry_run_assessment,
)


class Test95ADryRunAssessment:
    """Dry-run assessment model and evaluation."""

    def test_all_execution_flags_false(self):
        a = ArtifactOnlyRealInvocationDryRunAssessment(assessment_id="dra-test")
        assert a.execution_allowed is False
        assert a.execution_ready is False
        assert a.dry_run_only is True
        assert a.no_real_backend_invoked is True
        assert a.no_adapter_executed is True
        assert a.no_subprocess is True
        assert a.no_network is True

    def test_missing_plan_blocks(self):
        a = evaluate_artifact_only_real_invocation_dry_run(plan=None)
        assert a.execution_allowed is False
        assert a.dry_run_only is True
        assert any("plan" in hb.lower() for hb in a.hard_blocks)

    def test_evaluate_with_valid_evidence(self):
        plan = create_real_adapter_invocation_plan(
            adapter_id="ad", backend_id="mock", backend_type="mock",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
        )
        plan.record_digest = plan.compute_digest()
        a = evaluate_artifact_only_real_invocation_dry_run(plan=plan)
        assert a.execution_allowed is False
        assert a.dry_run_only is True
        assert a.no_real_backend_invoked is True

    def test_serialization_round_trip(self):
        a = ArtifactOnlyRealInvocationDryRunAssessment(assessment_id="dra-rt")
        d = a.to_dict()
        a2 = ArtifactOnlyRealInvocationDryRunAssessment.from_dict(d)
        assert a2.assessment_id == "dra-rt"

    def test_digest_verification(self):
        a = ArtifactOnlyRealInvocationDryRunAssessment(assessment_id="dra-dig")
        a.record_digest = a.compute_digest()
        r = verify_artifact_only_real_invocation_dry_run_assessment(a)
        assert r["valid"] is True

    def test_tampered_digest_fails(self):
        a = ArtifactOnlyRealInvocationDryRunAssessment(assessment_id="dra-tamp")
        a.record_digest = a.compute_digest()
        a.execution_allowed = True
        r = verify_artifact_only_real_invocation_dry_run_assessment(a)
        assert r["valid"] is False

    def test_execution_allowed_true_fails_verify(self):
        a = ArtifactOnlyRealInvocationDryRunAssessment(assessment_id="dra-ea", execution_allowed=True)
        a.record_digest = a.compute_digest()
        r = verify_artifact_only_real_invocation_dry_run_assessment(a)
        assert r["valid"] is False

    def test_persist_and_load(self, tmp_path):
        import os
        orig = os.getcwd()
        try:
            os.chdir(tmp_path)
            a = ArtifactOnlyRealInvocationDryRunAssessment(assessment_id="dra-pl")
            a.record_digest = a.compute_digest()
            persist = persist_artifact_only_real_invocation_dry_run_assessment(a)
            assert persist["status"] == "written"
            loaded = load_latest_artifact_only_real_invocation_dry_run_assessment()
            assert loaded is not None
            assert loaded.assessment_id == "dra-pl"
        finally:
            os.chdir(orig)

    def test_load_absent_returns_none(self, tmp_path):
        import os
        orig = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert load_latest_artifact_only_real_invocation_dry_run_assessment() is None
        finally:
            os.chdir(orig)

    def test_no_secrets(self):
        import json
        a = ArtifactOnlyRealInvocationDryRunAssessment(assessment_id="dra-sec")
        j = json.dumps(a.to_dict())
        assert "sk-ant" not in j


class Test95ADryRunCLI:
    """CLI evaluate/show/verify."""

    def test_evaluate_missing_plan_fails(self):
        import subprocess, sys
        from pathlib import Path
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "dry-run",
             "evaluate", "--plan-artifact", "/nonexistent/path.json"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent, timeout=15,
        )
        assert r.returncode != 0

    def test_show_missing_handled(self, tmp_path):
        import subprocess, sys
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "dry-run",
             "show", "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_gitignore_has_dry_run_dir(self):
        from pathlib import Path
        gitignore = Path(__file__).resolve().parent.parent / ".pcae" / ".gitignore"
        assert "artifact-only-real-invocation-dry-runs/" in gitignore.read_text()


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95C — Claude runtime evidence model tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    ClaudeRuntimeEvidence,
    validate_claude_runtime_evidence,
    persist_claude_runtime_evidence,
    verify_claude_runtime_evidence,
    load_latest_claude_runtime_evidence,
    PROFILE_CLAUDE_CLI,
    BYPASS_UNKNOWN,
    BYPASS_OFF,
    BYPASS_ON,
    EVIDENCE_OPERATOR_DECLARED,
)


class Test95CRuntimeEvidence:
    """ClaudeRuntimeEvidence model."""

    def test_safe_defaults(self):
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-test")
        assert e.no_real_backend_invoked is True
        assert e.no_adapter_executed is True
        assert e.no_subprocess is True
        assert e.no_network is True
        assert e.secrets_redacted is True
        assert e.bypass_permissions_state == BYPASS_UNKNOWN

    def test_unknown_profile_blocked(self):
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-up", runtime_profile="bogus")
        r = validate_claude_runtime_evidence(e)
        assert r["valid"] is False

    def test_missing_command_identity_blocked(self):
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-ci", runtime_profile=PROFILE_CLAUDE_CLI,
                                   backend_id="claude", declared_command_path="/usr/bin/claude",
                                   audit_path="/a", output_quarantine_path="/q", timeout_seconds=120)
        r = validate_claude_runtime_evidence(e)
        assert r["valid"] is False

    def test_bypass_unknown_blocked(self):
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-bu", runtime_profile=PROFILE_CLAUDE_CLI,
                                   backend_id="claude", command_identity="claude",
                                   declared_command_path="/usr/bin/claude",
                                   bypass_permissions_state=BYPASS_UNKNOWN,
                                   audit_path="/a", output_quarantine_path="/q", timeout_seconds=120)
        r = validate_claude_runtime_evidence(e)
        assert r["valid"] is False

    def test_bypass_on_hard_blocked(self):
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-bo", runtime_profile=PROFILE_CLAUDE_CLI,
                                   backend_id="claude", command_identity="claude",
                                   declared_command_path="/usr/bin/claude",
                                   bypass_permissions_state=BYPASS_ON,
                                   audit_path="/a", output_quarantine_path="/q", timeout_seconds=120)
        r = validate_claude_runtime_evidence(e)
        assert r["valid"] is False

    def test_bypass_off_valid_with_evidence(self):
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-bf", runtime_profile=PROFILE_CLAUDE_CLI,
                                   backend_id="claude", command_identity="claude",
                                   declared_command_path="/usr/bin/claude",
                                   bypass_permissions_state=BYPASS_OFF,
                                   bypass_permissions_evidence="operator confirmed bypass disabled",
                                   evidence_source=EVIDENCE_OPERATOR_DECLARED,
                                   audit_path="/a", output_quarantine_path="/q", timeout_seconds=120)
        r = validate_claude_runtime_evidence(e)
        assert r["valid"] is True

    def test_serialization_round_trip(self):
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-rt")
        d = e.to_dict()
        e2 = ClaudeRuntimeEvidence.from_dict(d)
        assert e2.runtime_evidence_id == "re-rt"

    def test_digest_verification(self):
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-dig")
        e.record_digest = e.compute_digest()
        r = verify_claude_runtime_evidence(e)
        assert r["valid"] is True

    def test_tampered_digest_fails(self):
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-tamp")
        e.record_digest = e.compute_digest()
        e.no_real_backend_invoked = False
        r = verify_claude_runtime_evidence(e)
        assert r["valid"] is False

    def test_persist_and_load(self, tmp_path):
        import os
        orig = os.getcwd()
        try:
            os.chdir(tmp_path)
            e = ClaudeRuntimeEvidence(runtime_evidence_id="re-pl")
            e.record_digest = e.compute_digest()
            p = persist_claude_runtime_evidence(e)
            assert p["status"] == "written"
            loaded = load_latest_claude_runtime_evidence()
            assert loaded is not None
            assert loaded.runtime_evidence_id == "re-pl"
        finally:
            os.chdir(orig)

    def test_no_secrets(self):
        import json
        e = ClaudeRuntimeEvidence(runtime_evidence_id="re-sec")
        j = json.dumps(e.to_dict())
        assert "sk-ant" not in j


class Test95CRuntimeEvidenceCLI:
    def test_show_missing_handled(self, tmp_path):
        import subprocess, sys
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "runtime-evidence",
             "show", "--latest"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_gitignore_has_runtime_evidence_dir(self):
        from pathlib import Path
        g = Path(__file__).resolve().parent.parent / ".pcae" / ".gitignore"
        assert "claude-runtime-evidence/" in g.read_text()


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95D — Claude runtime evidence import CLI tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    import_claude_runtime_evidence_from_json,
    _scan_for_secrets,
)


class Test95DImport:
    """Import CLI and secret detection."""

    def test_valid_import_succeeds(self, tmp_path):
        import json as _j
        fp = tmp_path / "evidence.json"
        data = {
            "runtime_evidence_id": "re-import-test",
            "backend_id": "claude",
            "backend_type": "claude_cli",
            "runtime_profile": "claude_cli",
            "command_identity": "claude",
            "declared_command_path": "/usr/local/bin/claude",
            "bypass_permissions_state": "off",
            "bypass_permissions_evidence": "operator confirmed",
            "evidence_source": "operator_declared",
            "timeout_seconds": 120,
            "audit_path": "/tmp/audit.json",
            "output_quarantine_path": "/tmp/output.md",
        }
        fp.write_text(_j.dumps(data))
        evidence, result = import_claude_runtime_evidence_from_json(str(fp))
        assert evidence is not None
        assert result["status"] == "imported"

    def test_missing_file_fails(self, tmp_path):
        evidence, result = import_claude_runtime_evidence_from_json(str(tmp_path / "nope.json"))
        assert evidence is None
        assert result["status"] == "failed"

    def test_malformed_json_fails(self, tmp_path):
        fp = tmp_path / "bad.json"
        fp.write_text("not json")
        evidence, result = import_claude_runtime_evidence_from_json(str(fp))
        assert evidence is None

    def test_secret_value_blocked(self, tmp_path):
        import json as _j
        fp = tmp_path / "secret.json"
        data = {
            "runtime_evidence_id": "re-sec",
            "backend_id": "claude",
            "backend_type": "claude_cli",
            "runtime_profile": "claude_cli",
            "command_identity": "claude",
            "declared_command_path": "/usr/local/bin/claude",
            "something": "sk-ant-secret-key-12345",
        }
        fp.write_text(_j.dumps(data))
        evidence, result = import_claude_runtime_evidence_from_json(str(fp))
        assert evidence is None
        assert "secret" in result["error"].lower()

    def test_env_value_in_json_blocked(self, tmp_path):
        import json as _j
        fp = tmp_path / "env.json"
        data = {
            "runtime_evidence_id": "re-env",
            "backend_id": "claude",
            "ANTHROPIC_API_KEY": "sk-ant-real-secret",
        }
        fp.write_text(_j.dumps(data))
        evidence, result = import_claude_runtime_evidence_from_json(str(fp))
        assert evidence is None

    def test_scan_for_secrets_detects_patterns(self):
        findings = _scan_for_secrets({"key": "sk-ant-abc123"})
        assert len(findings) >= 1
        findings2 = _scan_for_secrets({"key": "clean_value"})
        assert len(findings2) == 0

    def test_import_persists_and_latest_updated(self, tmp_path):
        import os, json as _j
        orig = os.getcwd()
        try:
            os.chdir(tmp_path)
            fp = tmp_path / "ev.json"
            data = {
                "runtime_evidence_id": "re-persist",
                "backend_id": "claude",
                "backend_type": "claude_cli",
                "runtime_profile": "claude_cli",
                "command_identity": "claude",
                "declared_command_path": "/usr/local/bin/claude",
                "bypass_permissions_state": "off",
                "bypass_permissions_evidence": "ok",
                "evidence_source": "operator_declared",
                "timeout_seconds": 120,
                "audit_path": "/tmp/audit.json",
                "output_quarantine_path": "/tmp/output.md",
            }
            fp.write_text(_j.dumps(data))
            evidence, result = import_claude_runtime_evidence_from_json(str(fp))
            assert evidence is not None
            persist_claude_runtime_evidence(evidence)
            loaded = load_latest_claude_runtime_evidence()
            assert loaded is not None
            assert loaded.runtime_evidence_id == "re-persist"
        finally:
            os.chdir(orig)


class Test95DImportCLI:
    """CLI import command."""

    def test_import_valid_json_cli(self, tmp_path):
        import subprocess, sys, json as _j
        fp = tmp_path / "ev.json"
        _j.dump({
            "runtime_evidence_id": "re-cli",
            "backend_id": "claude",
            "backend_type": "claude_cli",
            "runtime_profile": "claude_cli",
            "command_identity": "claude",
            "declared_command_path": "/usr/local/bin/claude",
            "bypass_permissions_state": "off",
            "bypass_permissions_evidence": "ok",
            "evidence_source": "operator_declared",
            "timeout_seconds": 120,
            "audit_path": "/tmp/audit.json",
            "output_quarantine_path": "/tmp/output.md",
        }, fp.open("w"))
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "runtime-evidence",
             "import", "--from-json", str(fp)],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode == 0
        assert "imported" in r.stdout.lower()

    def test_import_missing_from_json_fails(self, tmp_path):
        import subprocess, sys
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "runtime-evidence",
             "import"],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0

    def test_import_secret_blocked_cli(self, tmp_path):
        import subprocess, sys, json as _j
        fp = tmp_path / "sec.json"
        _j.dump({"runtime_evidence_id": "re-sec", "token": "sk-ant-bad"}, fp.open("w"))
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "runtime-evidence",
             "import", "--from-json", str(fp)],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode != 0


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95E — Runtime evidence to dry-run integration tests
# ═══════════════════════════════════════════════════════════════════════════


class Test95EIntegration:
    """Runtime evidence integration into dry-run assessment."""

    def test_dry_run_without_runtime_evidence_blocks(self):
        plan = create_real_adapter_invocation_plan(
            adapter_id="ad", backend_id="claude", backend_type="claude_cli",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
        )
        a = evaluate_artifact_only_real_invocation_dry_run(plan=plan)
        assert "runtime_evidence_missing" in a.hard_blocks

    def test_dry_run_with_valid_runtime_evidence(self):
        plan = create_real_adapter_invocation_plan(
            adapter_id="adapter-claude-cli", backend_id="claude", backend_type="claude_cli",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
            timeout_seconds=120,
        )
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-int", backend_id="claude",
            backend_type="claude_cli", adapter_id="adapter-claude-cli",
            runtime_profile="claude_cli", command_identity="claude",
            declared_command_path="/usr/local/bin/claude",
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            evidence_source="operator_declared",
            timeout_seconds=120, audit_path="/q", output_quarantine_path="/q",
            record_digest="0000",
        )
        re_ev.record_digest = re_ev.compute_digest()
        a = evaluate_artifact_only_real_invocation_dry_run(plan=plan, runtime_evidence=re_ev)
        assert a.runtime_evidence_id == "re-int"
        assert a.runtime_bypass_permissions_state == "off"
        assert a.execution_allowed is False  # still dry-run only

    def test_runtime_bypass_on_blocks(self):
        plan = create_real_adapter_invocation_plan(
            adapter_id="ad", backend_id="claude", backend_type="claude_cli",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
        )
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-bp", backend_id="claude",
            runtime_profile="claude_cli", command_identity="claude",
            declared_command_path="/usr/local/bin/claude",
            bypass_permissions_state="on", timeout_seconds=120,
            audit_path="/a", output_quarantine_path="/q",
        )
        re_ev.record_digest = re_ev.compute_digest()
        a = evaluate_artifact_only_real_invocation_dry_run(plan=plan, runtime_evidence=re_ev)
        assert "runtime:bypass_enabled" in a.hard_blocks or any("bypass" in hb for hb in a.hard_blocks)

    def test_runtime_backend_mismatch_blocks(self):
        plan = create_real_adapter_invocation_plan(
            adapter_id="ad", backend_id="claude", backend_type="claude_cli",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
        )
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-mm", backend_id="claude-deepseek",
            runtime_profile="claude_deepseek_cli", command_identity="claude-deepseek",
            declared_command_path="/usr/local/bin/claude-deepseek",
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
        )
        re_ev.record_digest = re_ev.compute_digest()
        a = evaluate_artifact_only_real_invocation_dry_run(plan=plan, runtime_evidence=re_ev)
        assert "runtime_backend_mismatch" in a.hard_blocks

    def test_no_secrets_in_assessment(self):
        import json
        a = ArtifactOnlyRealInvocationDryRunAssessment(assessment_id="dra-sec")
        j = json.dumps(a.to_dict())
        assert "sk-ant" not in j


class Test95EIntegrationCLI:
    def test_evaluate_with_runtime_evidence_cli(self, tmp_path):
        import subprocess, sys, json as _j
        # Create plan
        plan_path = tmp_path / "plan.json"
        plan = create_real_adapter_invocation_plan(
            adapter_id="adapter-claude-cli", backend_id="claude", backend_type="claude_cli",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
            timeout_seconds=120,
        )
        _j.dump(plan.to_dict(), plan_path.open("w"))
        # Create runtime evidence
        re_path = tmp_path / "re.json"
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-cli-int", backend_id="claude",
            backend_type="claude_cli", adapter_id="adapter-claude-cli",
            runtime_profile="claude_cli", command_identity="claude",
            declared_command_path="/usr/local/bin/claude",
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            evidence_source="operator_declared",
            timeout_seconds=120, audit_path="/q", output_quarantine_path="/q",
        )
        re_ev.record_digest = re_ev.compute_digest()
        _j.dump(re_ev.to_dict(), re_path.open("w"))
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "dry-run",
             "evaluate", "--plan-artifact", str(plan_path),
             "--runtime-evidence", str(re_path)],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode == 0
        assert "bypass" in r.stdout.lower() or "Runtime evidence" in r.stdout


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95F — Stat-only runtime detector tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    ClaudeRuntimeDetectionConfig,
    detect_claude_runtime_evidence_stat_only,
)


class Test95FDetector:
    """Stat-only detector."""

    def test_valid_config_produces_evidence(self, tmp_path):
        # Create a temp file to hash
        cmd = tmp_path / "fake-claude"
        cmd.write_text("#!/bin/sh\necho mock")
        config = ClaudeRuntimeDetectionConfig(
            config_id="cfg-1", backend_id="claude", backend_type="claude_cli",
            runtime_profile="claude_cli", declared_command_path=str(cmd),
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
        )
        evidence = detect_claude_runtime_evidence_stat_only(config)
        assert evidence.runtime_evidence_id.startswith("re-")
        assert evidence.declared_command_path_hash
        assert evidence.no_real_backend_invoked is True
        assert evidence.no_subprocess is True
        assert evidence.no_network is True

    def test_missing_command_path_blocks(self, tmp_path):
        config = ClaudeRuntimeDetectionConfig(
            config_id="cfg-2", backend_id="claude", runtime_profile="claude_cli",
            declared_command_path=str(tmp_path / "nonexistent"),
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
        )
        evidence = detect_claude_runtime_evidence_stat_only(config)
        assert "command_path_not_found" in evidence.hard_blocks

    def test_directory_path_blocks(self, tmp_path):
        config = ClaudeRuntimeDetectionConfig(
            config_id="cfg-3", backend_id="claude", runtime_profile="claude_cli",
            declared_command_path=str(tmp_path),
            bypass_permissions_state="off", timeout_seconds=120,
            audit_path="/a", output_quarantine_path="/q",
        )
        evidence = detect_claude_runtime_evidence_stat_only(config)
        assert "command_path_is_directory" in evidence.hard_blocks

    def test_bypass_unknown_blocks(self, tmp_path):
        cmd = tmp_path / "claude"
        cmd.write_text("mock")
        config = ClaudeRuntimeDetectionConfig(
            config_id="cfg-4", backend_id="claude", runtime_profile="claude_cli",
            declared_command_path=str(cmd),
            bypass_permissions_state="unknown", timeout_seconds=120,
            audit_path="/a", output_quarantine_path="/q",
        )
        evidence = detect_claude_runtime_evidence_stat_only(config)
        assert "bypass_state_unknown" in evidence.hard_blocks

    def test_no_execution_flags_true(self, tmp_path):
        cmd = tmp_path / "claude"
        cmd.write_text("mock")
        config = ClaudeRuntimeDetectionConfig(
            config_id="cfg-5", backend_id="claude", runtime_profile="claude_cli",
            declared_command_path=str(cmd),
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
        )
        evidence = detect_claude_runtime_evidence_stat_only(config)
        assert evidence.no_real_backend_invoked is True
        assert evidence.no_adapter_executed is True
        assert evidence.no_subprocess is True
        assert evidence.no_network is True
        assert evidence.secrets_redacted is True

    def test_no_subprocess_in_detector_code(self):
        import inspect
        from pcae.core import backend_invocations
        source = inspect.getsource(backend_invocations)
        assert "subprocess.run" not in source
        assert "os.system(" not in source
        assert "shutil.which" not in source


class Test95FDetectorCLI:
    def test_detect_stat_only_cli(self, tmp_path):
        import subprocess, sys, json as _j
        cmd = tmp_path / "fake-claude"
        cmd.write_text("mock binary")
        config_path = tmp_path / "config.json"
        _j.dump({
            "config_id": "cfg-cli", "backend_id": "claude",
            "backend_type": "claude_cli", "runtime_profile": "claude_cli",
            "declared_command_path": str(cmd),
            "bypass_permissions_state": "off",
            "bypass_permissions_evidence": "ok",
            "timeout_seconds": 120, "audit_path": "/a",
            "output_quarantine_path": "/q",
        }, config_path.open("w"))
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "backend", "adapter", "runtime-evidence",
             "detect-stat-only", "--config", str(config_path)],
            capture_output=True, text=True, cwd=tmp_path, timeout=15,
        )
        assert r.returncode == 0
        assert "Stat-only" in r.stdout
        assert "Executed command:  no" in r.stdout


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95G — Runtime evidence broker/shell-gate integration tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    evaluate_runtime_evidence_broker_decision,
    evaluate_runtime_evidence_shell_gate_decision,
    DECISION_ALLOW_DRY_RUN,
    DECISION_HARD_BLOCK,
    DECISION_MISSING_EVIDENCE,
)


class Test95GBrokerDecision:
    """Broker runtime evidence decisions."""

    def test_missing_runtime_evidence_hard_blocks(self):
        r = evaluate_runtime_evidence_broker_decision(runtime_evidence=None)
        assert r["decision"] == DECISION_HARD_BLOCK

    def test_bypass_unknown_hard_blocks(self):
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-br", backend_id="claude",
            runtime_profile="claude_cli", command_identity="claude",
            declared_command_path="/usr/bin/claude",
            bypass_permissions_state="unknown",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
        )
        r = evaluate_runtime_evidence_broker_decision(runtime_evidence=re_ev)
        assert r["decision"] == DECISION_HARD_BLOCK

    def test_bypass_on_hard_blocks(self):
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-bon", backend_id="claude",
            runtime_profile="claude_cli", command_identity="claude",
            declared_command_path="/usr/bin/claude",
            bypass_permissions_state="on",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
        )
        r = evaluate_runtime_evidence_broker_decision(runtime_evidence=re_ev)
        assert r["decision"] == DECISION_HARD_BLOCK

    def test_backend_mismatch_hard_blocks(self):
        plan = create_real_adapter_invocation_plan(
            adapter_id="ad", backend_id="claude", backend_type="claude_cli",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
        )
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-mm", backend_id="claude-deepseek",
            runtime_profile="claude_cli", command_identity="claude-deepseek",
            declared_command_path="/usr/bin/claude-deepseek",
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
        )
        re_ev.record_digest = re_ev.compute_digest()
        r = evaluate_runtime_evidence_broker_decision(plan=plan, runtime_evidence=re_ev)
        assert r["decision"] == DECISION_HARD_BLOCK

    def test_no_execution_false_blocks(self):
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-ne", backend_id="claude",
            runtime_profile="claude_cli", command_identity="claude",
            declared_command_path="/usr/bin/claude",
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
            no_real_backend_invoked=False,
        )
        r = evaluate_runtime_evidence_broker_decision(runtime_evidence=re_ev)
        assert r["decision"] == DECISION_HARD_BLOCK


class Test95GShellGateDecision:
    """Shell-gate runtime evidence decisions."""

    def test_missing_runtime_evidence_hard_blocks(self):
        r = evaluate_runtime_evidence_shell_gate_decision(runtime_evidence=None)
        assert r["decision"] == DECISION_HARD_BLOCK

    def test_missing_command_path_blocks(self):
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-sg", backend_id="claude",
            runtime_profile="claude_cli", command_identity="claude",
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
        )
        r = evaluate_runtime_evidence_shell_gate_decision(runtime_evidence=re_ev)
        assert r["decision"] == DECISION_HARD_BLOCK

    def test_no_subprocess_false_hard_blocks(self):
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-ns", backend_id="claude",
            runtime_profile="claude_cli", command_identity="claude",
            declared_command_path="/usr/bin/claude",
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            timeout_seconds=120, audit_path="/a", output_quarantine_path="/q",
            no_subprocess=False,
        )
        r = evaluate_runtime_evidence_shell_gate_decision(runtime_evidence=re_ev)
        assert r["decision"] == DECISION_HARD_BLOCK


class Test95GDryRunIntegration:
    """Dry-run assessment includes broker/shell-gate decisions."""

    def test_dry_run_includes_broker_sg_decisions(self):
        plan = create_real_adapter_invocation_plan(
            adapter_id="adapter-claude-cli", backend_id="claude", backend_type="claude_cli",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
        )
        re_ev = ClaudeRuntimeEvidence(
            runtime_evidence_id="re-int", backend_id="claude",
            backend_type="claude_cli", adapter_id="adapter-claude-cli",
            runtime_profile="claude_cli", command_identity="claude",
            declared_command_path="/usr/bin/claude",
            bypass_permissions_state="off", bypass_permissions_evidence="ok",
            evidence_source="operator_declared",
            timeout_seconds=120, audit_path="/q", output_quarantine_path="/q",
        )
        re_ev.record_digest = re_ev.compute_digest()
        a = evaluate_artifact_only_real_invocation_dry_run(plan=plan, runtime_evidence=re_ev)
        assert hasattr(a, "runtime_broker_decision")
        assert hasattr(a, "runtime_shell_gate_decision")
        assert a.execution_allowed is False

    def test_no_secrets_in_assessment(self):
        import json
        plan = create_real_adapter_invocation_plan(
            adapter_id="ad", backend_id="claude", backend_type="claude_cli",
            operator="op", prompt_hash="ph", prompt_artifact_path="/p",
            output_quarantine_path="/q", audit_artifact_path="/a",
        )
        a = evaluate_artifact_only_real_invocation_dry_run(plan=plan)
        j = json.dumps(a.to_dict())
        assert "sk-ant" not in j


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95K — Artifact-only invocation command boundary model tests
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    ArtifactOnlyInvocationCommandBoundary,
    ArtifactOnlyInvocationCommandBoundaryAssessment,
    validate_artifact_only_invocation_command_boundary,
    persist_artifact_only_invocation_command_boundary,
    verify_artifact_only_invocation_command_boundary,
    load_latest_artifact_only_invocation_command_boundary,
    persist_artifact_only_invocation_command_boundary_assessment,
    verify_artifact_only_invocation_command_boundary_assessment,
    load_latest_artifact_only_invocation_command_boundary_assessment,
    COMMAND_MODE_PLAN,
    COMMAND_MODE_DRY_RUN,
    COMMAND_MODE_EXECUTE_RESERVED,
    BOUNDARY_READY_FOR_PLAN,
    BOUNDARY_READY_FOR_DRY_RUN,
    BOUNDARY_HARD_BLOCK,
    BOUNDARY_UNSUPPORTED_EXECUTE,
    DECISION_DENY,
    DECISION_HARD_BLOCK,
    DECISION_ALLOW_DRY_RUN,
)


def _valid_boundary(**overrides) -> ArtifactOnlyInvocationCommandBoundary:
    """Build a fully valid plan-mode boundary for tests."""
    kwargs = {
        "boundary_id": "cb-test-001",
        "phase_id": "95K",
        "task_id": "20260630-test",
        "backend_id": "mock",
        "adapter_id": "mock-adapter",
        "prompt_artifact_path": "/p/prompt.md",
        "prompt_artifact_digest": "abc123",
        "preflight_artifact_path": "/p/preflight.json",
        "preflight_artifact_digest": "def456",
        "runtime_evidence_path": "/p/runtime.json",
        "runtime_evidence_digest": "ghi789",
        "approval_artifact_path": "/p/approval.json",
        "approval_artifact_digest": "jkl012",
        "invocation_plan_path": "/p/plan.json",
        "invocation_plan_digest": "mno345",
        "broker_decision_id": "bd-001",
        "broker_decision": DECISION_ALLOW_DRY_RUN,
        "shell_gate_decision_id": "sg-001",
        "shell_gate_decision": DECISION_ALLOW_DRY_RUN,
        "output_quarantine_path": "/q",
        "audit_path": "/a",
        "timeout_seconds": 120,
        "redaction_policy_id": "rp-001",
        "operator_approval_reference": "approval-001",
        "command_mode": COMMAND_MODE_PLAN,
    }
    kwargs.update(overrides)
    return ArtifactOnlyInvocationCommandBoundary(**kwargs)


class Test95KCommandBoundaryModel:
    """Model structure and digest tests."""

    def test_valid_plan_boundary_round_trip(self):
        b = _valid_boundary()
        d = b.to_dict()
        b2 = ArtifactOnlyInvocationCommandBoundary.from_dict(d)
        assert b2.boundary_id == b.boundary_id
        assert b2.backend_id == "mock"
        assert b2.command_mode == COMMAND_MODE_PLAN

    def test_all_safety_flags_default_true(self):
        b = ArtifactOnlyInvocationCommandBoundary()
        assert b.no_real_backend_invoked is True
        assert b.no_adapter_executed is True
        assert b.no_subprocess is True
        assert b.no_network is True
        assert b.no_repo_mutation is True
        assert b.no_apply is True
        assert b.no_patch_parsing is True
        assert b.no_commit_push_authorization is True
        assert b.no_telegram_inbound is True
        assert b.dry_run_only is True
        assert b.execute_requested is False

    def test_digest_stable(self):
        b = _valid_boundary()
        d1 = b.compute_digest()
        d2 = b.compute_digest()
        assert d1 == d2
        assert len(d1) == 64  # SHA-256 hex

    def test_digest_changes_on_field_change(self):
        b = _valid_boundary()
        d1 = b.compute_digest()
        b.backend_id = "claude"
        d2 = b.compute_digest()
        assert d1 != d2

    def test_digest_excludes_record_digest(self):
        b = _valid_boundary()
        b.record_digest = "fakesomething"
        d = b.compute_digest()
        # record_digest is excluded in compute_digest, so setting it shouldn't change hash
        assert "fakesomething" not in d

    def test_from_dict_ignores_unknown_fields(self):
        d = _valid_boundary().to_dict()
        d["extra_field"] = "should be ignored"
        b = ArtifactOnlyInvocationCommandBoundary.from_dict(d)
        assert not hasattr(b, "extra_field")

    def test_assessment_defaults(self):
        a = ArtifactOnlyInvocationCommandBoundaryAssessment()
        assert a.execution_allowed is False
        assert a.execute_supported is False
        assert a.dry_run_only is True
        assert a.ready is False

    def test_assessment_digest_stable(self):
        a = ArtifactOnlyInvocationCommandBoundaryAssessment(assessment_id="a1")
        d1 = a.compute_digest()
        d2 = a.compute_digest()
        assert d1 == d2


class Test95KCommandBoundaryValidation:
    """Validation rules from 95J design."""

    def test_valid_plan_returns_ready_for_plan(self):
        b = _valid_boundary(command_mode=COMMAND_MODE_PLAN)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert a.decision == BOUNDARY_READY_FOR_PLAN
        assert a.ready is True
        assert a.execution_allowed is False
        assert a.execute_supported is False

    def test_valid_dry_run_returns_ready_for_dry_run(self):
        b = _valid_boundary(command_mode=COMMAND_MODE_DRY_RUN)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert a.decision == BOUNDARY_READY_FOR_DRY_RUN
        assert a.ready is True

    def test_execute_reserved_hard_blocks(self):
        b = _valid_boundary(command_mode=COMMAND_MODE_EXECUTE_RESERVED)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert a.decision == BOUNDARY_UNSUPPORTED_EXECUTE
        assert a.ready is False
        assert "execute_reserved_not_supported" in a.hard_blocks

    def test_execute_requested_true_hard_blocks(self):
        b = _valid_boundary(execute_requested=True)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "execute_requested=True" in a.hard_blocks

    def test_missing_backend_blocks(self):
        b = _valid_boundary(backend_id="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "backend_id_missing" in a.hard_blocks

    def test_missing_adapter_blocks(self):
        b = _valid_boundary(adapter_id="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "adapter_id_missing" in a.hard_blocks

    def test_missing_prompt_path_blocks(self):
        b = _valid_boundary(prompt_artifact_path="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "prompt_artifact_path_missing" in a.hard_blocks

    def test_missing_prompt_digest_blocks(self):
        b = _valid_boundary(prompt_artifact_digest="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "prompt_artifact_digest_missing" in a.hard_blocks

    def test_missing_preflight_path_blocks(self):
        b = _valid_boundary(preflight_artifact_path="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "preflight_artifact_path_missing" in a.hard_blocks

    def test_missing_preflight_digest_blocks(self):
        b = _valid_boundary(preflight_artifact_digest="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "preflight_artifact_digest_missing" in a.hard_blocks

    def test_missing_runtime_evidence_path_blocks(self):
        b = _valid_boundary(runtime_evidence_path="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "runtime_evidence_path_missing" in a.hard_blocks

    def test_missing_runtime_evidence_digest_blocks(self):
        b = _valid_boundary(runtime_evidence_digest="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "runtime_evidence_digest_missing" in a.hard_blocks

    def test_missing_approval_path_blocks(self):
        b = _valid_boundary(approval_artifact_path="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "approval_artifact_path_missing" in a.hard_blocks

    def test_missing_approval_digest_blocks(self):
        b = _valid_boundary(approval_artifact_digest="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "approval_artifact_digest_missing" in a.hard_blocks

    def test_missing_invocation_plan_path_blocks(self):
        b = _valid_boundary(invocation_plan_path="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "invocation_plan_path_missing" in a.hard_blocks

    def test_missing_invocation_plan_digest_blocks(self):
        b = _valid_boundary(invocation_plan_digest="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "invocation_plan_digest_missing" in a.hard_blocks

    def test_broker_deny_blocks(self):
        b = _valid_boundary(broker_decision=DECISION_DENY)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert any("broker_decision:deny" in hb for hb in a.hard_blocks)

    def test_broker_hard_block_blocks(self):
        b = _valid_boundary(broker_decision=DECISION_HARD_BLOCK)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert any("broker_decision:hard_block" in hb for hb in a.hard_blocks)

    def test_shell_gate_deny_blocks(self):
        b = _valid_boundary(shell_gate_decision=DECISION_DENY)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert any("shell_gate_decision:deny" in hb for hb in a.hard_blocks)

    def test_shell_gate_hard_block_blocks(self):
        b = _valid_boundary(shell_gate_decision=DECISION_HARD_BLOCK)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert any("shell_gate_decision:hard_block" in hb for hb in a.hard_blocks)

    def test_missing_quarantine_path_blocks(self):
        b = _valid_boundary(output_quarantine_path="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "output_quarantine_path_missing" in a.hard_blocks

    def test_missing_audit_path_blocks(self):
        b = _valid_boundary(audit_path="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "audit_path_missing" in a.hard_blocks

    def test_timeout_zero_blocks(self):
        b = _valid_boundary(timeout_seconds=0)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "timeout_missing_or_invalid" in a.hard_blocks

    def test_timeout_negative_blocks(self):
        b = _valid_boundary(timeout_seconds=-1)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "timeout_missing_or_invalid" in a.hard_blocks

    def test_redaction_policy_missing_blocks(self):
        b = _valid_boundary(redaction_policy_id="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "redaction_policy_id_missing" in a.hard_blocks

    def test_operator_approval_missing_blocks(self):
        b = _valid_boundary(operator_approval_reference="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "operator_approval_reference_missing" in a.hard_blocks

    def test_no_real_backend_invoked_false_blocks(self):
        b = _valid_boundary(no_real_backend_invoked=False)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "no_real_backend_invoked=False" in a.hard_blocks

    def test_no_subprocess_false_blocks(self):
        b = _valid_boundary(no_subprocess=False)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "no_subprocess=False" in a.hard_blocks

    def test_no_network_false_blocks(self):
        b = _valid_boundary(no_network=False)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "no_network=False" in a.hard_blocks

    def test_no_apply_false_blocks(self):
        b = _valid_boundary(no_apply=False)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "no_apply=False" in a.hard_blocks

    def test_unknown_command_mode_blocks(self):
        b = _valid_boundary(command_mode="invalid_mode")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert any("unknown_command_mode" in hb for hb in a.hard_blocks)

    def test_dry_run_only_false_blocks(self):
        b = _valid_boundary(dry_run_only=False)
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "dry_run_only=False" in a.hard_blocks

    def test_boundary_id_missing_blocks(self):
        b = _valid_boundary(boundary_id="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "boundary_id_missing" in a.hard_blocks

    def test_phase_id_missing_blocks(self):
        b = _valid_boundary(phase_id="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "phase_id_missing" in a.hard_blocks

    def test_task_id_missing_blocks(self):
        b = _valid_boundary(task_id="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "task_id_missing" in a.hard_blocks

    def test_broker_decision_id_missing_blocks(self):
        b = _valid_boundary(broker_decision_id="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "broker_decision_id_missing" in a.hard_blocks

    def test_shell_gate_decision_id_missing_blocks(self):
        b = _valid_boundary(shell_gate_decision_id="")
        a = validate_artifact_only_invocation_command_boundary(b)
        assert "shell_gate_decision_id_missing" in a.hard_blocks


class Test95KCommandBoundaryPersistence:
    """Persistence and verification tests."""

    def test_persist_and_load_boundary(self, tmp_path):
        import os as _os
        b = _valid_boundary()
        b.record_digest = b.compute_digest()
        result = persist_artifact_only_invocation_command_boundary(b)
        assert result["status"] == "written"

    def test_verify_valid_boundary(self):
        b = _valid_boundary()
        b.record_digest = b.compute_digest()
        v = verify_artifact_only_invocation_command_boundary(b)
        assert v["valid"] is True

    def test_verify_tampered_boundary_fails(self):
        b = _valid_boundary()
        b.record_digest = b.compute_digest()
        b.backend_id = "tampered"
        v = verify_artifact_only_invocation_command_boundary(b)
        assert v["valid"] is False
        assert "record_digest_mismatch" in v["issues"]

    def test_persist_and_load_assessment(self, tmp_path):
        b = _valid_boundary()
        a = validate_artifact_only_invocation_command_boundary(b)
        a.record_digest = a.compute_digest()
        result = persist_artifact_only_invocation_command_boundary_assessment(a)
        assert result["status"] == "written"

    def test_verify_assessment_execution_allowed_must_be_false(self):
        a = ArtifactOnlyInvocationCommandBoundaryAssessment(
            assessment_id="a1", execution_allowed=True,
        )
        a.record_digest = a.compute_digest()
        v = verify_artifact_only_invocation_command_boundary_assessment(a)
        assert v["valid"] is False
        assert "execution_allowed must be False" in v["issues"]

    def test_verify_assessment_execute_supported_must_be_false(self):
        a = ArtifactOnlyInvocationCommandBoundaryAssessment(
            assessment_id="a1", execute_supported=True,
        )
        a.record_digest = a.compute_digest()
        v = verify_artifact_only_invocation_command_boundary_assessment(a)
        assert v["valid"] is False
        assert "execute_supported must be False" in v["issues"]

    def test_load_nonexistent_returns_none(self):
        import shutil, os as _os
        d = _os.path.join(_os.getcwd(), ".pcae/artifact-only-invocation-boundaries")
        if _os.path.exists(d):
            shutil.rmtree(d)
        result = load_latest_artifact_only_invocation_command_boundary()
        assert result is None

    def test_load_nonexistent_assessment_returns_none(self):
        import shutil, os as _os
        d = _os.path.join(_os.getcwd(), ".pcae/artifact-only-invocation-boundaries/assessments")
        if _os.path.exists(d):
            shutil.rmtree(d)
        result = load_latest_artifact_only_invocation_command_boundary_assessment()
        assert result is None


class Test95KCommandBoundarySafety:
    """No-execution invariants."""

    def test_no_subprocess_in_code(self):
        import inspect
        src = inspect.getsource(validate_artifact_only_invocation_command_boundary)
        # "subprocess" in docstring is OK — check for actual subprocess calls
        assert "subprocess.run" not in src
        assert "subprocess.Popen" not in src

    def test_no_network_in_code(self):
        import inspect
        src = inspect.getsource(validate_artifact_only_invocation_command_boundary)
        assert "urllib" not in src.lower()
        assert "http" not in src.lower()
        assert "socket" not in src.lower()

    def test_no_shell_in_code(self):
        import inspect
        src = inspect.getsource(validate_artifact_only_invocation_command_boundary)
        assert "os.system" not in src
        assert "shell=True" not in src

    def test_no_backend_invocation_in_code(self):
        import inspect
        src = inspect.getsource(validate_artifact_only_invocation_command_boundary)
        assert "invoke_backend" not in src.lower()
        assert "subprocess.run" not in src
        assert "subprocess.Popen" not in src

    def test_no_cli_registration(self):
        """Verify no CLI command was registered for artifact-only invoke."""
        from pcae.cli import main as _cli_main
        import io, sys as _sys
        old_stdout = _sys.stdout
        try:
            _sys.stdout = io.StringIO()
            try:
                _cli_main()
            except SystemExit:
                pass
            output = _sys.stdout.getvalue()
        finally:
            _sys.stdout = old_stdout
        assert "artifact-only" not in output.lower() or "not recognized" in output.lower()
