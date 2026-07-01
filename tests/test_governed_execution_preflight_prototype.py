"""Tests for governed execution preflight prototype — Phase 98A.

All models must remain non-executing and non-authorizing.
Tests prove the prototype consumes Phase 97 preflight correctly,
fails closed, and never authorizes execution.
"""

from __future__ import annotations

import hashlib
import json as _json
import pytest
from pathlib import Path

from pcae.core.backend_invocations import (
    GovernedExecutionPreflightPrototype,
    build_governed_execution_preflight_prototype,
    save_governed_execution_preflight_prototype,
    load_latest_governed_execution_preflight_prototype,
    verify_governed_execution_preflight_prototype,
    build_execution_readiness_preflight,
    save_execution_readiness_preflight,
    ExecutionReadinessPreflight,
    GEP_BLOCKED, GEP_UNAVAILABLE, GEP_EVIDENCE_INCOMPLETE,
    GEP_APPROVAL_REQUIRED, GEP_VERIFICATION_FAILED,
    GEP_DECISION_BLOCK, GEP_DECISION_REQUIRE_EVIDENCE,
    GEP_DECISION_READY_FOR_REVIEW_ONLY,
    VALID_GEP_STATUSES, VALID_GEP_DECISIONS, UNAVAILABLE_GEP_DECISIONS,
    _gep_dir_path, _gep_latest_path, _preflight_latest_path,
)


@pytest.fixture
def clean_artifact_dirs():
    import shutil
    for dir_path in (_gep_dir_path(),):
        if dir_path.exists():
            shutil.rmtree(dir_path)
    yield
    for dir_path in (_gep_dir_path(),):
        if dir_path.exists():
            shutil.rmtree(dir_path)


@pytest.fixture
def source_preflight():
    return build_execution_readiness_preflight(task_id="src-test")


# ═══════════════════════════════════════════════════════════════════════════
# Non-executing / non-authorizing
# ═══════════════════════════════════════════════════════════════════════════


class TestPrototypeNonExecuting:
    def test_no_execution_statuses_or_decisions(self):
        assert "execute" not in VALID_GEP_STATUSES
        assert "run" not in VALID_GEP_STATUSES
        assert "invoke" not in VALID_GEP_STATUSES
        assert "apply" not in VALID_GEP_DECISIONS
        assert "commit" not in VALID_GEP_DECISIONS
        assert "push" not in VALID_GEP_DECISIONS
        assert "execution_ready" not in VALID_GEP_DECISIONS

    def test_future_decisions_are_unavailable(self):
        futures = {"execute", "run", "invoke", "apply", "commit", "push", "execution_ready", "invocation_authorized"}
        assert futures.issubset(UNAVAILABLE_GEP_DECISIONS)

    def test_default_prototype_all_auth_flags_false(self):
        p = GovernedExecutionPreflightPrototype()
        assert p.execution_available is False
        assert p.execution_authorized is False
        assert p.push_authorized is False
        assert p.simulation_only is True
        assert p.no_execution is True
        assert p.evidence_only is True
        assert p.non_authorizing is True

    def test_built_prototype_all_auth_flags_false(self):
        p = build_governed_execution_preflight_prototype(load_latest=False)
        assert p.execution_available is False
        assert p.execution_authorized is False
        assert p.push_authorized is False
        assert p.no_execution is True
        assert p.evidence_only is True


# ═══════════════════════════════════════════════════════════════════════════
# Source preflight handling
# ═══════════════════════════════════════════════════════════════════════════


class TestSourcePreflightHandling:
    def test_missing_source_preflight_blocks(self):
        p = build_governed_execution_preflight_prototype(load_latest=False)
        assert p.prototype_status == GEP_UNAVAILABLE
        assert p.decision == GEP_DECISION_BLOCK
        assert "source_preflight" in p.missing_prerequisites

    def test_source_with_no_go_conditions_blocks(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert p.no_go_conditions  # should have no-go from source
        assert p.decision == GEP_DECISION_BLOCK

    def test_source_missing_evidence_preserved(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert p.source_missing_evidence == source_preflight.missing_evidence
        assert p.source_failed_checks == source_preflight.failed_checks

    def test_source_no_execution_false_blocks(self):
        src = ExecutionReadinessPreflight(
            preflight_id="bad-src", preflight_status=GEP_BLOCKED,
            no_execution=False,
        )
        p = build_governed_execution_preflight_prototype(
            source_preflight=src, load_latest=False,
        )
        assert "source_no_execution_is_false" in p.decision_reasons

    def test_source_auth_flag_true_blocks(self):
        src = ExecutionReadinessPreflight(
            preflight_id="bad-auth", preflight_status=GEP_BLOCKED,
            execution_available=True,
        )
        p = build_governed_execution_preflight_prototype(
            source_preflight=src, load_latest=False,
        )
        assert p.decision == GEP_DECISION_BLOCK
        assert any("execution_available" in r for r in p.decision_reasons)

    def test_source_preflight_ref_preserved(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert p.source_preflight_ref == source_preflight.preflight_id
        assert p.source_preflight_digest == source_preflight.digest


# ═══════════════════════════════════════════════════════════════════════════
# Digest behavior
# ═══════════════════════════════════════════════════════════════════════════


class TestPrototypeDigest:
    def test_digest_is_sha256_hex(self):
        p = build_governed_execution_preflight_prototype(load_latest=False)
        assert len(p.digest) == 64

    def test_digest_changes_with_source_digest(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        src2 = ExecutionReadinessPreflight(
            preflight_id="diff", preflight_status=GEP_BLOCKED,
        )
        src2.digest = "a" * 64
        p2 = build_governed_execution_preflight_prototype(
            source_preflight=src2, load_latest=False,
        )
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_changes_with_decision(self):
        p1 = GovernedExecutionPreflightPrototype(prototype_id="d1", decision=GEP_DECISION_BLOCK)
        p2 = GovernedExecutionPreflightPrototype(prototype_id="d1", decision=GEP_DECISION_READY_FOR_REVIEW_ONLY)
        assert p1.compute_digest() != p2.compute_digest()

    def test_tampered_digest_fails_verify(self, clean_artifact_dirs, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        save_governed_execution_preflight_prototype(p)
        latest = _gep_latest_path()
        data = _json.loads(latest.read_text())
        data["digest"] = "0" * 64
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_governed_execution_preflight_prototype()
        result = verify_governed_execution_preflight_prototype(loaded)
        assert result["valid"] is False
        assert any("digest_mismatch" in i for i in result["issues"])


# ═══════════════════════════════════════════════════════════════════════════
# Persistence and verification
# ═══════════════════════════════════════════════════════════════════════════


class TestPrototypePersistence:
    def test_save_and_load_roundtrip(self, clean_artifact_dirs, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        save_governed_execution_preflight_prototype(p)
        loaded = load_latest_governed_execution_preflight_prototype()
        assert loaded is not None
        assert loaded.prototype_id == p.prototype_id

    def test_load_no_artifact_returns_none(self, clean_artifact_dirs):
        assert load_latest_governed_execution_preflight_prototype() is None

    def test_verify_no_artifact(self):
        r = verify_governed_execution_preflight_prototype(None)
        assert r["valid"] is False
        assert not r["prototype_present"]

    def test_verify_valid_prototype(self, clean_artifact_dirs, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        save_governed_execution_preflight_prototype(p)
        loaded = load_latest_governed_execution_preflight_prototype()
        r = verify_governed_execution_preflight_prototype(loaded)
        assert r["prototype_present"] is True
        assert r["no_execution_confirmed"] is True


# ═══════════════════════════════════════════════════════════════════════════
# CLI contract
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIContract:
    def test_preflight_json_auth_flags_false(self):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "preflight", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        auth = data["authorization_summary"]
        for flag, val in auth.items():
            assert val is False

    def test_preflight_save_and_show(self, clean_artifact_dirs):
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
        data = _json.loads(r.stdout)
        assert "prototype_id" in data
        assert data["no_execution"] is True

    def test_preflight_verify(self, clean_artifact_dirs):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "verify", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        assert data["no_execution_confirmed"] is True


# ═══════════════════════════════════════════════════════════════════════════
# No-execution guard
# ═══════════════════════════════════════════════════════════════════════════


class TestNoExecutionGuard:
    def test_build_returns_dataclass(self):
        p = build_governed_execution_preflight_prototype(load_latest=False)
        assert isinstance(p, GovernedExecutionPreflightPrototype)

    def test_save_uses_filesystem_only(self, clean_artifact_dirs, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        path = save_governed_execution_preflight_prototype(p)
        assert path.exists()
        data = _json.loads(path.read_text())
        assert data["no_execution"] is True

    def test_verify_is_pure_computation(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        r = verify_governed_execution_preflight_prototype(p)
        assert isinstance(r, dict)
        assert "valid" in r

    def test_output_has_no_execution_commands(self):
        p = build_governed_execution_preflight_prototype(load_latest=False)
        d_str = _json.dumps(p.to_dict()).lower()
        assert "subprocess.run" not in d_str
        assert "os.system" not in d_str
        assert "Popen" not in d_str
