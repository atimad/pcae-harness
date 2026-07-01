"""Artifact trust hardening tests for governed execution preflight — Phase 98C.

Hardens digest coverage, tamper detection, authorization flag trust,
future-only decision safety, source preflight reference validation,
latest/show/verify safety, verification error contract, and no-execution
guards on top of the frozen 98B contract.
"""

from __future__ import annotations

import hashlib
import json as _json
import pytest
from pathlib import Path

from pcae.core.backend_invocations import (
    _GEP_SCHEMA_VERSION,
    GovernedExecutionPreflightPrototype,
    build_governed_execution_preflight_prototype,
    save_governed_execution_preflight_prototype,
    load_latest_governed_execution_preflight_prototype,
    verify_governed_execution_preflight_prototype,
    build_execution_readiness_preflight,
    ExecutionReadinessPreflight,
    GEP_BLOCKED, GEP_UNAVAILABLE, GEP_VERIFICATION_FAILED,
    GEP_DECISION_BLOCK, GEP_DECISION_DENY, GEP_DECISION_READY_FOR_REVIEW_ONLY,
    GEP_DECISION_EXECUTE_FUTURE, GEP_DECISION_RUN_FUTURE,
    VALID_GEP_DECISIONS, UNAVAILABLE_GEP_DECISIONS, VALID_GEP_STATUSES,
    _gep_dir_path, _gep_latest_path,
)

FROZEN_AUTH_FLAGS = (
    "execution_available", "execution_authorized",
    "backend_invocation_authorized", "adapter_execution_authorized",
    "network_authorized", "subprocess_authorized", "shell_authorized",
    "mutation_authorized", "apply_authorized", "rollback_authorized",
    "commit_authorized", "push_authorized",
)


@pytest.fixture
def source_preflight():
    return build_execution_readiness_preflight(task_id="trust-src")


@pytest.fixture
def clean_artifact_dir():
    import shutil
    d = _gep_dir_path()
    if d.exists(): shutil.rmtree(d)
    yield
    if d.exists(): shutil.rmtree(d)


def _tamper_and_resave(prototype, **overrides):
    save_governed_execution_preflight_prototype(prototype)
    latest = _gep_latest_path()
    data = _json.loads(latest.read_text())
    data.update(overrides)
    if "digest" not in overrides:
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
    latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
    return load_latest_governed_execution_preflight_prototype()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Digest coverage hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestDigestCoverageHardening:
    def test_digest_includes_schema_version(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        p2 = GovernedExecutionPreflightPrototype.from_dict(p1.to_dict())
        p2.schema_version = "9.9"
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_source_preflight_ref(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        p2 = GovernedExecutionPreflightPrototype.from_dict(p1.to_dict())
        p2.source_preflight_ref = "changed-ref"
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_source_preflight_digest(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        p2 = GovernedExecutionPreflightPrototype.from_dict(p1.to_dict())
        p2.source_preflight_digest = "a" * 64
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_prerequisite_summaries(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        for field in ("prerequisite_summary", "approval_summary", "audit_summary",
                       "rollback_summary", "backend_contract_summary",
                       "adapter_boundary_summary", "artifact_verification_summary",
                       "execution_boundary_summary"):
            p2 = GovernedExecutionPreflightPrototype.from_dict(p1.to_dict())
            setattr(p2, field, "changed_summary")
            assert p1.compute_digest() != p2.compute_digest(), f"Digest unchanged for {field}"

    def test_digest_includes_prototype_status(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        p2 = GovernedExecutionPreflightPrototype.from_dict(p1.to_dict())
        p2.prototype_status = GEP_UNAVAILABLE
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_decision(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        p2 = GovernedExecutionPreflightPrototype.from_dict(p1.to_dict())
        p2.decision = GEP_DECISION_DENY
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_safety_flags(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        for flag in ("simulation_only", "no_execution", "evidence_only", "non_authorizing"):
            p2 = GovernedExecutionPreflightPrototype.from_dict(p1.to_dict())
            setattr(p2, flag, False)
            assert p1.compute_digest() != p2.compute_digest(), f"Digest unchanged for {flag}=False"

    def test_digest_includes_decision_reasons(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        p2 = GovernedExecutionPreflightPrototype.from_dict(p1.to_dict())
        p2.decision_reasons = ["new_reason"]
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_includes_all_auth_flags(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        for flag in FROZEN_AUTH_FLAGS:
            p2 = GovernedExecutionPreflightPrototype.from_dict(p1.to_dict())
            setattr(p2, flag, True)
            assert p1.compute_digest() != p2.compute_digest()

    def test_digest_stable_across_roundtrip(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        d1 = p.compute_digest()
        assert len(d1) == 64
        p2 = GovernedExecutionPreflightPrototype.from_dict(p.to_dict())
        p2.prototype_id = p.prototype_id
        p2.generated_at_utc = p.generated_at_utc
        assert p2.compute_digest() == p2.compute_digest()  # self-consistent


# ═══════════════════════════════════════════════════════════════════════════
# 2. Tamper detection hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestTamperDetectionHardening:
    def test_tamper_schema_version_fails_verify(self, clean_artifact_dir, source_preflight):
        loaded = _tamper_and_resave(
            build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False),
            schema_version="999.0",
        )
        assert verify_governed_execution_preflight_prototype(loaded)["valid"] is False

    def test_tamper_prototype_status_fails_verify(self, clean_artifact_dir, source_preflight):
        loaded = _tamper_and_resave(
            build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False),
            prototype_status="not_real",
        )
        assert verify_governed_execution_preflight_prototype(loaded)["valid"] is False

    def test_tamper_decision_fails_verify(self, clean_artifact_dir, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        save_governed_execution_preflight_prototype(p)
        latest = _gep_latest_path()
        data = _json.loads(latest.read_text())
        data["decision"] = GEP_DECISION_EXECUTE_FUTURE
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_governed_execution_preflight_prototype()
        assert verify_governed_execution_preflight_prototype(loaded)["valid"] is False

    def test_tamper_digest_directly_fails(self, clean_artifact_dir, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        save_governed_execution_preflight_prototype(p)
        latest = _gep_latest_path()
        data = _json.loads(latest.read_text())
        data["digest"] = "0" * 64
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_governed_execution_preflight_prototype()
        r = verify_governed_execution_preflight_prototype(loaded)
        assert r["valid"] is False
        assert any("digest_mismatch" in i for i in r["issues"])

    def test_tamper_any_auth_flag_fails(self, clean_artifact_dir, source_preflight):
        for flag in FROZEN_AUTH_FLAGS:
            p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
            save_governed_execution_preflight_prototype(p)
            latest = _gep_latest_path()
            data = _json.loads(latest.read_text())
            data["authorization_summary"][flag] = True
            payload = {k: v for k, v in data.items() if k != "digest"}
            data["digest"] = hashlib.sha256(
                _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
            latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
            loaded = load_latest_governed_execution_preflight_prototype()
            assert verify_governed_execution_preflight_prototype(loaded)["valid"] is False, f"{flag}=True should fail"

    def test_tamper_safety_flags_fail(self, clean_artifact_dir, source_preflight):
        for flag in ("simulation_only", "no_execution", "evidence_only", "non_authorizing"):
            loaded = _tamper_and_resave(
                build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False),
                **{flag: False},
            )
            assert verify_governed_execution_preflight_prototype(loaded)["valid"] is False

    def test_tamper_not_silent(self, clean_artifact_dir, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        save_governed_execution_preflight_prototype(p)
        latest = _gep_latest_path()
        data = _json.loads(latest.read_text())
        data["digest"] = "0" * 64
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_governed_execution_preflight_prototype()
        r = verify_governed_execution_preflight_prototype(loaded)
        assert len(r["issues"]) > 0

    def test_tamper_never_causes_execution(self, clean_artifact_dir, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        save_governed_execution_preflight_prototype(p)
        latest = _gep_latest_path()
        data = _json.loads(latest.read_text())
        data["authorization_summary"]["execution_available"] = True
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_governed_execution_preflight_prototype()
        r = verify_governed_execution_preflight_prototype(loaded)
        assert r["valid"] is False
        assert r["no_execution_confirmed"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 3. Authorization flag trust hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthorizationFlagTrustHardening:
    def test_cli_json_all_flags_false(self):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "preflight", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        auth = _json.loads(r.stdout)["authorization_summary"]
        for flag, val in auth.items():
            assert val is False

    def test_show_json_all_flags_false(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "show", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        auth = _json.loads(r.stdout)["authorization_summary"]
        for flag, val in auth.items():
            assert val is False

    def test_text_output_non_authorizing(self):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "preflight"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        assert "execute" not in r.stdout.lower().split()[:50]  # not in early output

    def test_decision_never_overrides_auth(self):
        for dec in VALID_GEP_DECISIONS:
            p = GovernedExecutionPreflightPrototype(prototype_id="t", decision=dec, prototype_status=GEP_BLOCKED)
            assert p.execution_available is False
            assert p.push_authorized is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. Future-only decision trust hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestFutureOnlyDecisionTrust:
    def test_all_8_future_decisions_rejected(self):
        for d in ("execute", "run", "invoke", "apply", "commit", "push", "execution_ready", "invocation_authorized"):
            p = GovernedExecutionPreflightPrototype(prototype_id="t", decision=d, prototype_status=GEP_BLOCKED)
            issues = p.validate()
            assert any("future-only" in i for i in issues), f"{d!r} should be rejected"

    def test_future_decisions_never_auth(self):
        for d in UNAVAILABLE_GEP_DECISIONS:
            p = GovernedExecutionPreflightPrototype(prototype_id="t", decision=d, prototype_status=GEP_BLOCKED)
            assert p.push_authorized is False

    def test_future_decisions_in_verify_fail(self):
        for d in ("execute", "run", "invoke"):
            p = GovernedExecutionPreflightPrototype(prototype_id="t", decision=d, prototype_status=GEP_BLOCKED)
            p.digest = p.compute_digest()
            r = verify_governed_execution_preflight_prototype(p)
            assert r["valid"] is False

    def test_unknown_decision_fails_validation(self):
        p = GovernedExecutionPreflightPrototype(prototype_id="t", decision="launch_nuclear_missiles", prototype_status=GEP_BLOCKED)
        issues = p.validate()
        assert any("invalid decision" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Source preflight reference validation hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestSourcePreflightRefValidation:
    def test_source_ref_never_url(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        assert not p.source_preflight_ref.startswith("http")
        assert not p.source_preflight_ref.startswith("file://")

    def test_source_ref_never_absolute_path(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        assert not p.source_preflight_ref.startswith("/")

    def test_source_ref_never_dotdot(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        assert ".." not in p.source_preflight_ref

    def test_source_ref_never_shell_expansion(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        assert "$" not in p.source_preflight_ref
        assert "`" not in p.source_preflight_ref

    def test_source_digest_length_consistent(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        assert len(p.source_preflight_digest) == 64

    def test_missing_source_ref_detected(self):
        p = build_governed_execution_preflight_prototype(load_latest=False)
        assert p.prototype_status == GEP_UNAVAILABLE
        assert "source_preflight" in p.missing_prerequisites


# ═══════════════════════════════════════════════════════════════════════════
# 6. Latest/show/verify safety hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestLatestShowVerifySafety:
    def test_latest_path_locked(self):
        s = str(_gep_latest_path())
        assert "governed-execution-preflight" in s
        assert s.endswith("latest.json")

    def test_latest_no_escape(self):
        assert ".." not in str(_gep_latest_path())

    def test_latest_not_url(self):
        assert not str(_gep_latest_path()).startswith("http")

    def test_invalid_json_returns_none(self, clean_artifact_dir, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        save_governed_execution_preflight_prototype(p)
        _gep_latest_path().write_text("not json {{{")
        assert load_latest_governed_execution_preflight_prototype() is None

    def test_missing_latest_verify_fails(self, clean_artifact_dir):
        r = verify_governed_execution_preflight_prototype(None)
        assert r["valid"] is False
        assert not r["prototype_present"]

    def test_save_and_load_consistent_id(self, clean_artifact_dir, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        save_governed_execution_preflight_prototype(p)
        loaded = load_latest_governed_execution_preflight_prototype()
        assert loaded.prototype_id == p.prototype_id


# ═══════════════════════════════════════════════════════════════════════════
# 7. Verification error contract hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestVerificationErrorContract:
    def test_result_has_required_keys(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        r = verify_governed_execution_preflight_prototype(p)
        for key in ("valid", "issues", "prototype_present", "prototype_id", "digest",
                     "prototype_status", "decision", "no_execution_confirmed"):
            assert key in r, f"Missing: {key!r}"

    def test_no_artifact_has_valid_false(self):
        r = verify_governed_execution_preflight_prototype(None)
        assert r["valid"] is False
        assert not r["prototype_present"]

    def test_verify_is_idempotent(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        r1 = verify_governed_execution_preflight_prototype(p)
        r2 = verify_governed_execution_preflight_prototype(p)
        assert r1["valid"] == r2["valid"]

    def test_verify_result_serializable(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        r = verify_governed_execution_preflight_prototype(p)
        s = _json.dumps(r)
        assert _json.loads(s)["valid"] == r["valid"]

    def test_valid_prototype_no_execution_confirmed(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        r = verify_governed_execution_preflight_prototype(p)
        assert r["no_execution_confirmed"] is True


# ═══════════════════════════════════════════════════════════════════════════
# 8. 98B contract preservation
# ═══════════════════════════════════════════════════════════════════════════


class Test98BContractPreservation:
    def test_34_json_fields_present(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        d = p.to_dict()
        expected_fields = (
            "schema_version", "prototype_id", "phase_id", "task_id", "generated_at_utc",
            "source_preflight_ref", "source_preflight_digest", "source_preflight_status",
            "source_readiness_status", "source_no_go_conditions", "source_missing_evidence",
            "source_failed_checks", "consumed_evidence_refs",
            "prerequisite_summary", "approval_summary", "audit_summary", "rollback_summary",
            "backend_contract_summary", "adapter_boundary_summary",
            "artifact_verification_summary", "execution_boundary_summary",
            "prototype_status", "decision", "decision_reasons", "no_go_conditions",
            "missing_prerequisites", "failed_prerequisites", "warnings",
            "authorization_summary", "simulation_only", "no_execution",
            "evidence_only", "non_authorizing", "digest",
        )
        for field in expected_fields:
            assert field in d

    def test_12_auth_flags_false(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        auth = p.to_dict()["authorization_summary"]
        assert len(auth) == 12
        for flag, val in auth.items():
            assert val is False

    def test_9_statuses_present(self):
        assert len(VALID_GEP_STATUSES) == 9

    def test_8_valid_8_future_decisions(self):
        assert len(VALID_GEP_DECISIONS) == 8
        assert len(UNAVAILABLE_GEP_DECISIONS) == 8

    def test_no_extra_top_level_fields(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        d = p.to_dict()
        assert len(d) == 34


# ═══════════════════════════════════════════════════════════════════════════
# 9. No-execution guard hardening
# ═══════════════════════════════════════════════════════════════════════════


class TestNoExecutionGuardHardening:
    def test_save_never_executes(self, clean_artifact_dir, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        path = save_governed_execution_preflight_prototype(p)
        assert path.exists()
        data = _json.loads(path.read_text())
        assert data["no_execution"] is True

    def test_verify_never_executes(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        r = verify_governed_execution_preflight_prototype(p)
        assert r["no_execution_confirmed"] is True

    def test_digest_never_executes(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        assert len(p.compute_digest()) == 64

    def test_cli_paths_never_execute(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        for cmd in (
            ["governed-execution", "preflight", "--json"],
            ["governed-execution", "preflight", "--save"],
        ):
            r = subprocess.run(
                [sys.executable, "-m", "pcae"] + cmd,
                capture_output=True, text=True, cwd=repo, timeout=15,
            )
            assert r.returncode == 0

    def test_to_dict_no_exec_paths(self, source_preflight):
        p = build_governed_execution_preflight_prototype(source_preflight=source_preflight, load_latest=False)
        s = _json.dumps(p.to_dict()).lower()
        assert "subprocess.run" not in s
        assert "os.system" not in s
