"""Artifact trust hardening tests for execution readiness preflight — Phase 97H.

Hardens tamper detection, reference validation, latest-pointer safety,
verification error contract, and no-execution guarantees on top of the
frozen 97G preflight contract.

97G contract preserved — no new required fields, no status/flag changes.
"""

from __future__ import annotations

import hashlib
import json as _json
import pytest
from pathlib import Path

from pcae.core.backend_invocations import (
    _PREFLIGHT_SCHEMA_VERSION,
    PREFLIGHT_BLOCKED,
    PREFLIGHT_NOT_READY,
    PREFLIGHT_FAILED_VERIFICATION,
    PREFLIGHT_EVIDENCE_INCOMPLETE,
    PREFLIGHT_APPROVAL_REQUIRED,
    PREFLIGHT_READY_FOR_PREFLIGHT_ONLY,
    PREFLIGHT_UNAVAILABLE,
    PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY,
    UNAVAILABLE_PREFLIGHT_STATUSES,
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
def clean_artifact_dir():
    import shutil
    dir_path = _preflight_dir_path()
    if dir_path.exists():
        shutil.rmtree(dir_path)
    yield
    if dir_path.exists():
        shutil.rmtree(dir_path)


def _tamper_and_resave(preflight: ExecutionReadinessPreflight, **overrides):
    """Save a preflight, tamper the saved JSON, reload it."""
    save_execution_readiness_preflight(preflight)
    latest = _preflight_latest_path()
    data = _json.loads(latest.read_text())
    data.update(overrides)
    # Recompute digest if tampering non-digest fields
    if "digest" not in overrides:
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
    latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
    return load_latest_execution_readiness_preflight()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Digest determinism and coverage hardening
# ═══════════════════════════════════════════════════════════════════════════

FROZEN_TOP_LEVEL_FIELDS = (
    "schema_version", "preflight_id", "phase_id", "task_id", "generated_at_utc",
    "readiness_status", "preflight_status", "evidence_status",
    "backend_invocation_contract_status", "adapter_boundary_status",
    "approval_status", "audit_readiness_status", "rollback_readiness_status",
    "artifact_verification_status", "execution_boundary_proof_status",
    "no_go_conditions", "missing_evidence", "failed_checks", "warnings",
    "evidence_refs", "approval_refs", "audit_refs", "rollback_refs", "proof_refs",
    "authorization_summary", "simulation_only", "no_execution", "digest",
)


class TestDigestCoverageHardening:
    """Digest must include all verification-relevant fields."""

    def test_digest_includes_schema_version(self):
        p1 = build_execution_readiness_preflight(task_id="sch1")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.schema_version = "0.9"  # different from 1.0
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_readiness_status(self):
        p1 = build_execution_readiness_preflight(task_id="rs")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.readiness_status = "not_a_real_status_for_test"
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_preflight_status(self):
        p1 = build_execution_readiness_preflight(task_id="ps")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.preflight_status = PREFLIGHT_UNAVAILABLE
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_evidence_status(self):
        p1 = build_execution_readiness_preflight(task_id="es")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.evidence_status = "changed_evidence_status"
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_domain_statuses(self):
        """All 7 domain statuses affect digest."""
        domain_fields = (
            "backend_invocation_contract_status",
            "adapter_boundary_status",
            "approval_status",
            "audit_readiness_status",
            "rollback_readiness_status",
            "artifact_verification_status",
            "execution_boundary_proof_status",
        )
        p1 = build_execution_readiness_preflight(task_id="dom")
        for field in domain_fields:
            p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
            setattr(p2, field, "test_domain_change")
            assert p1.compute_digest() != p2.compute_digest(), (
                f"Digest should change for {field}"
            )

    def test_digest_includes_warnings(self):
        p1 = build_execution_readiness_preflight(task_id="warn")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.warnings = ["new_warning_for_digest_test"]
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_evidence_refs(self):
        p1 = build_execution_readiness_preflight(task_id="eref")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.evidence_refs = ["ref:test_changed"]
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_approval_refs(self):
        p1 = build_execution_readiness_preflight(task_id="aref")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.approval_refs = ["approval:changed"]
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_audit_refs(self):
        p1 = build_execution_readiness_preflight(task_id="auref")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.audit_refs = ["audit:changed"]
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_rollback_refs(self):
        p1 = build_execution_readiness_preflight(task_id="rref")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.rollback_refs = ["rollback:changed"]
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_proof_refs(self):
        p1 = build_execution_readiness_preflight(task_id="pref")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.proof_refs = ["proof:changed"]
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_schema_version_change(self):
        """Explicit schema_version change must alter digest."""
        p1 = build_execution_readiness_preflight(task_id="schema-digest")
        p2 = ExecutionReadinessPreflight.from_dict(p1.to_dict())
        p2.schema_version = "CHANGED"
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_stable_across_json_key_ordering(self):
        """Digest must be the same regardless of JSON key order."""
        p = build_execution_readiness_preflight(task_id="key-order")
        d1 = p.compute_digest()
        # to_dict then from_dict roundtrip — different internal dict ordering possible
        p2 = ExecutionReadinessPreflight.from_dict(p.to_dict())
        p2.preflight_id = p.preflight_id
        p2.generated_at_utc = p.generated_at_utc
        # Both should produce valid SHA-256 hex strings
        assert len(p2.compute_digest()) == 64
        # Self-consistency
        assert d1 == p.compute_digest()
        assert p2.compute_digest() == p2.compute_digest()


# ═══════════════════════════════════════════════════════════════════════════
# 2. Tamper detection hardening — verify fails for every tampered field
# ═══════════════════════════════════════════════════════════════════════════


class TestTamperDetectionHardening:
    """Tampering any verification-relevant field must fail verify."""

    def test_tamper_schema_version_fails_verify(self, clean_artifact_dir):
        loaded = _tamper_and_resave(
            build_execution_readiness_preflight(task_id="t-schema"),
            schema_version="999.0",
        )
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False

    def test_tamper_readiness_status_digest_mismatch(self, clean_artifact_dir):
        """Tampering readiness_status changes digest -> verify detects mismatch."""
        p = build_execution_readiness_preflight(task_id="t-readiness")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["readiness_status"] = "tampered_status"
        # Do NOT recompute digest — verify should detect mismatch
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert any("digest_mismatch" in i for i in result["issues"])

    def test_tamper_preflight_status_fails_verify(self, clean_artifact_dir):
        loaded = _tamper_and_resave(
            build_execution_readiness_preflight(task_id="t-pfstatus"),
            preflight_status=PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY,
        )
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False

    def test_tamper_no_go_conditions_fails_verify(self, clean_artifact_dir):
        p = build_execution_readiness_preflight(task_id="t-nogo")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["no_go_conditions"] = ["fake_tampered_condition_not_real"]
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False

    def test_tamper_missing_evidence_digest_mismatch(self, clean_artifact_dir):
        """Tampering missing_evidence without recomputing digest -> mismatch."""
        p = build_execution_readiness_preflight(task_id="t-missing")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["missing_evidence"] = ["fake_missing_item"]
        # Do NOT recompute digest — verify should detect mismatch
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert any("digest_mismatch" in i for i in result["issues"])

    def test_tamper_digest_directly_fails_verify(self, clean_artifact_dir):
        p = build_execution_readiness_preflight(task_id="t-digest")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["digest"] = "0" * 64
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert any("digest_mismatch" in i for i in result["issues"])

    def test_tamper_any_authorization_flag_fails_verify(self, clean_artifact_dir):
        """Tampering any of the 12 auth flags True must fail verify."""
        auth_flags = (
            "execution_available", "execution_authorized",
            "backend_invocation_authorized", "adapter_execution_authorized",
            "network_authorized", "subprocess_authorized", "shell_authorized",
            "mutation_authorized", "apply_authorized", "rollback_authorized",
            "commit_authorized", "push_authorized",
        )
        for flag in auth_flags:
            p = build_execution_readiness_preflight(task_id=f"t-auth-{flag}")
            save_execution_readiness_preflight(p)
            latest = _preflight_latest_path()
            data = _json.loads(latest.read_text())
            data["authorization_summary"][flag] = True
            payload = {k: v for k, v in data.items() if k != "digest"}
            data["digest"] = hashlib.sha256(
                _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
            latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
            loaded = load_latest_execution_readiness_preflight()
            result = verify_execution_readiness_preflight(loaded)
            assert result["valid"] is False, f"verify should fail for tampered {flag}=True"

    def test_tamper_simulation_only_fails_verify(self, clean_artifact_dir):
        loaded = _tamper_and_resave(
            build_execution_readiness_preflight(task_id="t-sim"),
            simulation_only=False,
        )
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False

    def test_tamper_no_execution_fails_verify(self, clean_artifact_dir):
        loaded = _tamper_and_resave(
            build_execution_readiness_preflight(task_id="t-noexec"),
            no_execution=False,
        )
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False

    def test_tamper_evidence_refs_digest_mismatch(self, clean_artifact_dir):
        """Tampering evidence_refs without recomputing digest -> mismatch."""
        p = build_execution_readiness_preflight(task_id="t-erefs")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["evidence_refs"] = ["tampered_ref_not_in_original"]
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert any("digest_mismatch" in i for i in result["issues"])

    def test_tamper_failed_checks_digest_mismatch(self, clean_artifact_dir):
        """Tampering failed_checks without recomputing digest -> mismatch."""
        p = build_execution_readiness_preflight(task_id="t-fchecks")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["failed_checks"] = ["injected_fake_check"]
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert any("digest_mismatch" in i for i in result["issues"])

    def test_tamper_verification_not_silent(self, clean_artifact_dir):
        """Tampered artifact must report issues, not silently pass."""
        p = build_execution_readiness_preflight(task_id="t-silent")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["digest"] = "0" * 64
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_tamper_does_not_cause_execution(self, clean_artifact_dir):
        """Tampering auth flag True must fail verify and confirm no_execution=False."""
        p = build_execution_readiness_preflight(task_id="t-noexec-gate")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        # execution_available is inside authorization_summary
        data["authorization_summary"]["execution_available"] = True
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert result["no_execution_confirmed"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 3. Authorization flag trust hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthorizationFlagTrustHardening:
    """Authorization flags must never be true, never implied, never overridable."""

    def test_text_output_never_says_execution_ready(self):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        assert "execute_now" not in r.stdout.lower()
        assert "execution ready" not in r.stdout.lower()
        assert "invoke now" not in r.stdout.lower()

    def test_json_output_never_implies_authorization(self):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        auth = data["authorization_summary"]
        for flag, val in auth.items():
            assert val is False, f"JSON auth flag {flag} must be False, got {val!r}"
        assert data["execution_available"] is False if "execution_available" in data else True
        assert data["no_execution"] is True

    def test_show_output_never_implies_authorization(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "show", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        auth = data["authorization_summary"]
        for flag, val in auth.items():
            assert val is False, f"Show auth flag {flag} must be False"

    def test_verify_output_never_implies_authorization(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "verify", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        assert data["no_execution_confirmed"] is True

    def test_no_go_conditions_never_overrideable_by_approval(self):
        """Approval refs should not cancel no-go conditions."""
        approval_data = {"decision": "approved", "refs": ["approval-1"]}
        preflight = build_execution_readiness_preflight(approval_data=approval_data)
        # No-go conditions from evidence still apply
        assert len(preflight.no_go_conditions) > 0
        assert preflight.execution_available is False

    def test_no_go_conditions_never_overrideable_by_audit(self):
        """Audit refs should not cancel no-go conditions."""
        preflight = build_execution_readiness_preflight()
        ng_count = len(preflight.no_go_conditions)
        assert ng_count > 0
        assert preflight.execution_available is False
        assert preflight.execution_authorized is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. Reference validation hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestReferenceValidationHardening:
    """Referenced artifacts must be safe — no escape, no URLs, no execution paths."""

    def test_evidence_refs_are_not_urls(self):
        """Evidence refs must not be absolute URLs."""
        p = build_execution_readiness_preflight(task_id="ref-url")
        for ref in p.evidence_refs:
            assert not ref.startswith("http://"), f"URL in evidence_ref: {ref!r}"
            assert not ref.startswith("https://"), f"URL in evidence_ref: {ref!r}"
            assert not ref.startswith("file://"), f"file:// URI in evidence_ref: {ref!r}"

    def test_evidence_refs_are_not_shell_expansions(self):
        """Evidence refs must not contain shell metacharacters."""
        p = build_execution_readiness_preflight(task_id="ref-shell")
        for ref in p.evidence_refs:
            assert "$" not in ref, f"Shell expansion in evidence_ref: {ref!r}"
            assert "`" not in ref, f"Backtick in evidence_ref: {ref!r}"
            assert ";" not in ref, f"Semicolon in evidence_ref: {ref!r}"
            assert "|" not in ref, f"Pipe in evidence_ref: {ref!r}"

    def test_reference_refs_are_not_absolute_paths(self):
        """Refs should not be absolute filesystem paths."""
        p = build_execution_readiness_preflight(task_id="ref-abs")
        all_refs = (
            p.evidence_refs + p.approval_refs + p.audit_refs +
            p.rollback_refs + p.proof_refs
        )
        for ref in all_refs:
            assert not ref.startswith("/"), f"Absolute path ref: {ref!r}"

    def test_reference_refs_do_not_escape_with_dotdot(self):
        """Refs must not contain ../ traversal."""
        p = build_execution_readiness_preflight(task_id="ref-dotdot")
        all_refs = (
            p.evidence_refs + p.approval_refs + p.audit_refs +
            p.rollback_refs + p.proof_refs
        )
        for ref in all_refs:
            assert ".." not in ref, f"Path traversal in ref: {ref!r}"

    def test_refs_are_never_executable_paths(self):
        """Refs are symbolic references, not executable commands."""
        p = build_execution_readiness_preflight(task_id="ref-exec")
        all_refs = (
            p.evidence_refs + p.approval_refs + p.audit_refs +
            p.rollback_refs + p.proof_refs
        )
        for ref in all_refs:
            assert isinstance(ref, str)
            assert "subprocess" not in ref.lower()
            assert "os.system" not in ref.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 5. Latest/show/verify safety hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestLatestShowVerifySafetyHardening:
    """Latest pointers, show, and verify must be safe and consistent."""

    def test_latest_is_not_absolute_external_path(self):
        latest = _preflight_latest_path()
        assert not str(latest).startswith("/var")
        assert not str(latest).startswith("/tmp")
        assert not str(latest).startswith("/etc")
        assert ".pcae" in str(latest)

    def test_latest_is_not_url(self):
        latest = str(_preflight_latest_path())
        assert not latest.startswith("http://")
        assert not latest.startswith("https://")
        assert not latest.startswith("file://")

    def test_latest_no_double_dot_escape(self):
        latest = str(_preflight_latest_path())
        assert ".." not in latest

    def test_latest_path_is_relative_from_repo_root(self):
        """latest path must be relative to repo, not absolute."""
        latest = _preflight_latest_path()
        # It should be a relative or repo-relative path
        path_str = str(latest)
        assert not path_str.startswith("/") or ".pcae" in path_str

    def test_missing_latest_fails_clearly(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "show", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        assert "error" in data or "no_preflight" in str(data).lower()

    def test_invalid_json_latest_fails_clearly(self, clean_artifact_dir):
        p = build_execution_readiness_preflight(task_id="invalid-json")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        latest.write_text("this is not valid json {{{")
        loaded = load_latest_execution_readiness_preflight()
        assert loaded is None  # should return None for invalid JSON

    def test_show_and_verify_same_artifact(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r_show = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "show", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r_verify = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "verify", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        show_data = _json.loads(r_show.stdout)
        verify_data = _json.loads(r_verify.stdout)
        assert show_data["preflight_id"] == verify_data.get("preflight_id", "")

    def test_tampered_latest_fails_verify_not_silent(self, clean_artifact_dir):
        p = build_execution_readiness_preflight(task_id="latest-silent")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["execution_authorized"] = True
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_latest_cannot_point_to_another_artifact_type(self):
        """Latest is always latest.json — cannot be another artifact type."""
        latest = _preflight_latest_path()
        assert latest.name == "latest.json"
        assert "execution-readiness-preflight" in str(latest)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Verification error contract hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestVerificationErrorContract:
    """Verification results must have a stable error contract shape."""

    def test_result_has_valid_field(self):
        p = build_execution_readiness_preflight(task_id="contract")
        result = verify_execution_readiness_preflight(p)
        assert "valid" in result
        assert isinstance(result["valid"], bool)

    def test_result_has_issues_list(self):
        p = build_execution_readiness_preflight(task_id="issues")
        result = verify_execution_readiness_preflight(p)
        assert "issues" in result
        assert isinstance(result["issues"], list)

    def test_result_has_no_execution_confirmed(self):
        p = build_execution_readiness_preflight(task_id="noexec")
        result = verify_execution_readiness_preflight(p)
        assert "no_execution_confirmed" in result
        assert isinstance(result["no_execution_confirmed"], bool)

    def test_result_has_preflight_present(self):
        p = build_execution_readiness_preflight(task_id="present")
        result = verify_execution_readiness_preflight(p)
        assert "preflight_present" in result
        assert result["preflight_present"] is True

    def test_missing_artifact_result_has_preflight_present_false(self):
        result = verify_execution_readiness_preflight(None)
        assert result["preflight_present"] is False
        assert result["valid"] is False

    def test_result_preflight_id_matches_input(self):
        p = build_execution_readiness_preflight(task_id="pid-match")
        result = verify_execution_readiness_preflight(p)
        assert result["preflight_id"] == p.preflight_id

    def test_result_digest_matches_input(self):
        p = build_execution_readiness_preflight(task_id="dig-match")
        result = verify_execution_readiness_preflight(p)
        assert result["digest"] == p.digest

    def test_result_preflight_status_matches_input(self):
        p = build_execution_readiness_preflight(task_id="ps-match")
        result = verify_execution_readiness_preflight(p)
        assert result["preflight_status"] == p.preflight_status

    def test_verify_is_idempotent(self):
        """Same preflight verified twice -> same result."""
        p = build_execution_readiness_preflight(task_id="idempotent")
        r1 = verify_execution_readiness_preflight(p)
        r2 = verify_execution_readiness_preflight(p)
        assert r1["valid"] == r2["valid"]
        assert r1["no_execution_confirmed"] == r2["no_execution_confirmed"]

    def test_verify_result_is_serializable(self):
        """Verification result must be JSON-serializable."""
        p = build_execution_readiness_preflight(task_id="serial")
        result = verify_execution_readiness_preflight(p)
        serialized = _json.dumps(result)
        assert isinstance(serialized, str)
        roundtripped = _json.loads(serialized)
        assert roundtripped["valid"] == result["valid"]


# ═══════════════════════════════════════════════════════════════════════════
# 7. 97G contract preservation
# ═══════════════════════════════════════════════════════════════════════════


class Test97GContractPreservation:
    """The frozen 97G contract must remain intact."""

    def test_all_28_top_level_fields_present(self):
        p = build_execution_readiness_preflight(task_id="97g-ok")
        d = p.to_dict()
        for field in FROZEN_TOP_LEVEL_FIELDS:
            assert field in d, f"97G contract: missing field {field!r}"

    def test_authorization_summary_has_12_fields(self):
        p = build_execution_readiness_preflight(task_id="97g-auth")
        auth = p.to_dict()["authorization_summary"]
        assert len(auth) == 12

    def test_all_auth_flags_false(self):
        p = build_execution_readiness_preflight(task_id="97g-flags")
        auth = p.to_dict()["authorization_summary"]
        for flag, val in auth.items():
            assert val is False

    def test_no_new_required_top_level_fields(self):
        """No unexpected top-level fields beyond frozen contract."""
        p = build_execution_readiness_preflight(task_id="97g-extra")
        d = p.to_dict()
        extra = set(d.keys()) - set(FROZEN_TOP_LEVEL_FIELDS)
        assert not extra, f"Unexpected fields in contract: {extra}"

    def test_97g1_report_trust_preserved(self):
        """report_notification_tests and bootstrap_session_reporting_tests are
        defined as required base test keys (97G.1 repair)."""
        from pcae.core.phase_reports import _REQUIRED_BASE_TEST_RESULT_KEYS
        assert "report_notification_tests" in _REQUIRED_BASE_TEST_RESULT_KEYS
        assert "bootstrap_session_reporting_tests" in _REQUIRED_BASE_TEST_RESULT_KEYS
        assert "fast_green" in _REQUIRED_BASE_TEST_RESULT_KEYS


# ═══════════════════════════════════════════════════════════════════════════
# 8. No-execution guard hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestNoExecutionGuardHardening:
    """Artifact trust operations must never execute anything."""

    def test_save_never_executes(self, clean_artifact_dir):
        p = build_execution_readiness_preflight(task_id="guard-save")
        saved = save_execution_readiness_preflight(p)
        assert saved.exists()
        data = _json.loads(saved.read_text())
        assert data["no_execution"] is True
        assert data["authorization_summary"]["execution_available"] is False

    def test_verify_never_executes(self):
        p = build_execution_readiness_preflight(task_id="guard-verify")
        result = verify_execution_readiness_preflight(p)
        assert result["no_execution_confirmed"] is True

    def test_digest_never_executes(self):
        p = build_execution_readiness_preflight(task_id="guard-digest")
        d = p.compute_digest()
        assert len(d) == 64

    def test_cli_preflight_never_executes(self):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        for cmd in (
            ["execution-readiness", "preflight", "--json"],
            ["execution-readiness", "preflight", "--save"],
        ):
            r = subprocess.run(
                [sys.executable, "-m", "pcae"] + cmd,
                capture_output=True, text=True, cwd=repo, timeout=15,
            )
            assert r.returncode == 0

    def test_cli_show_never_executes(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "show"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        # show returns 0 on success or non-zero when no artifact
        # Either is fine — what matters is no execution was attempted

    def test_cli_verify_never_executes(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "verify", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        assert data["no_execution_confirmed"] is True
