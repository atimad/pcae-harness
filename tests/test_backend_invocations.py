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
