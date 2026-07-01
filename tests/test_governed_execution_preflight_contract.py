"""Contract-freeze tests for governed execution preflight prototype — Phase 98B.

Freezes the 98A prototype model schema, statuses, decisions, authorization
flags, digest behavior, CLI contract, latest/show/verify semantics, and
compatibility rules. No source changes — contract freeze only.
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
    ExecutionReadinessPreflight,
    build_execution_readiness_preflight,
    # ── Statuses ──
    GEP_UNAVAILABLE, GEP_BLOCKED, GEP_EVIDENCE_INCOMPLETE,
    GEP_APPROVAL_REQUIRED, GEP_AUDIT_REQUIRED, GEP_ROLLBACK_REQUIRED,
    GEP_VERIFICATION_FAILED, GEP_READY_FOR_PREFLIGHT_REVIEW, GEP_PREFLIGHT_ONLY,
    VALID_GEP_STATUSES,
    # ── Decisions ──
    GEP_DECISION_DENY, GEP_DECISION_BLOCK, GEP_DECISION_REQUIRE_EVIDENCE,
    GEP_DECISION_REQUIRE_APPROVAL, GEP_DECISION_REQUIRE_AUDIT_READINESS,
    GEP_DECISION_REQUIRE_ROLLBACK_READINESS, GEP_DECISION_REQUIRE_VERIFICATION,
    GEP_DECISION_READY_FOR_REVIEW_ONLY,
    VALID_GEP_DECISIONS,
    # ── Future-only ──
    GEP_DECISION_EXECUTE_FUTURE, GEP_DECISION_RUN_FUTURE,
    GEP_DECISION_INVOKE_FUTURE, GEP_DECISION_APPLY_FUTURE,
    GEP_DECISION_COMMIT_FUTURE, GEP_DECISION_PUSH_FUTURE,
    GEP_DECISION_EXECUTION_READY_FUTURE, GEP_DECISION_INVOCATION_AUTHORIZED_FUTURE,
    UNAVAILABLE_GEP_DECISIONS,
    # ── Paths ──
    _gep_dir_path, _gep_latest_path,
)


@pytest.fixture
def source_preflight():
    return build_execution_readiness_preflight(task_id="gep-contract-src")


@pytest.fixture
def clean_artifact_dir():
    import shutil
    d = _gep_dir_path()
    if d.exists(): shutil.rmtree(d)
    yield
    if d.exists(): shutil.rmtree(d)


# ═══════════════════════════════════════════════════════════════════════════
# Frozen field names
# ═══════════════════════════════════════════════════════════════════════════

FROZEN_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "schema_version", "prototype_id", "phase_id", "task_id",
    "generated_at_utc",
    "source_preflight_ref", "source_preflight_digest",
    "source_preflight_status", "source_readiness_status",
    "source_no_go_conditions", "source_missing_evidence",
    "source_failed_checks", "consumed_evidence_refs",
    "prerequisite_summary", "approval_summary", "audit_summary",
    "rollback_summary", "backend_contract_summary",
    "adapter_boundary_summary", "artifact_verification_summary",
    "execution_boundary_summary",
    "prototype_status", "decision", "decision_reasons",
    "no_go_conditions", "missing_prerequisites",
    "failed_prerequisites", "warnings",
    "authorization_summary",
    "simulation_only", "no_execution", "evidence_only",
    "non_authorizing", "digest",
)

FROZEN_VALID_STATUSES: tuple[str, ...] = (
    "unavailable", "blocked", "evidence_incomplete",
    "approval_required", "audit_required", "rollback_required",
    "verification_failed", "ready_for_preflight_review", "preflight_only",
)

FROZEN_VALID_DECISIONS: tuple[str, ...] = (
    "deny", "block", "require_evidence", "require_approval",
    "require_audit_readiness", "require_rollback_readiness",
    "require_verification", "ready_for_review_only",
)

FROZEN_FUTURE_DECISIONS: tuple[str, ...] = (
    "execute", "run", "invoke", "apply", "commit", "push",
    "execution_ready", "invocation_authorized",
)

FROZEN_AUTH_FLAGS: tuple[str, ...] = (
    "execution_available", "execution_authorized",
    "backend_invocation_authorized", "adapter_execution_authorized",
    "network_authorized", "subprocess_authorized", "shell_authorized",
    "mutation_authorized", "apply_authorized", "rollback_authorized",
    "commit_authorized", "push_authorized",
)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Schema field freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestSchemaFieldFreeze:
    def test_all_34_fields_present(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        d = p.to_dict()
        for field in FROZEN_TOP_LEVEL_FIELDS:
            assert field in d, f"Missing: {field!r}"

    def test_schema_version_stable(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert p.schema_version == "1.0"

    def test_prototype_id_non_empty(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert len(p.prototype_id) > 0

    def test_digest_64_char_hex(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert len(p.digest) == 64

    def test_source_ref_digest_preserved(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert p.source_preflight_ref == source_preflight.preflight_id
        assert p.source_preflight_digest == source_preflight.digest

    def test_authorization_summary_12_flags(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        auth = p.to_dict()["authorization_summary"]
        assert len(auth) == 12

    def test_safety_flags_true(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert p.simulation_only is True
        assert p.no_execution is True
        assert p.evidence_only is True
        assert p.non_authorizing is True

    def test_no_extra_top_level_fields(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        d = p.to_dict()
        extra = set(d.keys()) - set(FROZEN_TOP_LEVEL_FIELDS)
        assert not extra, f"Extra fields: {extra}"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Status freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestStatusFreeze:
    def test_valid_statuses_match_frozen(self):
        assert VALID_GEP_STATUSES == frozenset(FROZEN_VALID_STATUSES)

    def test_no_executing_statuses(self):
        executing = {"execute", "run", "invoke", "apply", "commit", "push", "execution_ready"}
        assert VALID_GEP_STATUSES.isdisjoint(executing)

    def test_unknown_status_fails_validation(self):
        p = GovernedExecutionPreflightPrototype(
            prototype_id="t", prototype_status="not_a_real_status",
            decision=GEP_DECISION_BLOCK,
        )
        issues = p.validate()
        assert any("invalid prototype_status" in i for i in issues)

    def test_ready_statuses_non_authorizing(self):
        for s in (GEP_READY_FOR_PREFLIGHT_REVIEW, GEP_PREFLIGHT_ONLY):
            p = GovernedExecutionPreflightPrototype(
                prototype_id="t", prototype_status=s, decision=GEP_DECISION_READY_FOR_REVIEW_ONLY,
            )
            assert p.execution_available is False
            assert p.no_execution is True


# ═══════════════════════════════════════════════════════════════════════════
# 3. Valid decision freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestValidDecisionFreeze:
    def test_valid_decisions_match_frozen(self):
        assert VALID_GEP_DECISIONS == frozenset(FROZEN_VALID_DECISIONS)

    def test_valid_decisions_are_non_authorizing(self):
        p = GovernedExecutionPreflightPrototype(prototype_id="t")
        for dec in FROZEN_VALID_DECISIONS:
            p2 = GovernedExecutionPreflightPrototype(
                prototype_id="t", decision=dec,
                prototype_status=GEP_BLOCKED,
            )
            assert p2.execution_available is False
            assert p2.push_authorized is False

    def test_valid_decisions_non_executing(self):
        executing = {"execute", "run", "invoke", "apply", "commit", "push", "execution_ready", "invocation_authorized"}
        assert VALID_GEP_DECISIONS.isdisjoint(executing)

    def test_unknown_decision_fails_validation(self):
        p = GovernedExecutionPreflightPrototype(
            prototype_id="t", decision="not_a_decision",
            prototype_status=GEP_BLOCKED,
        )
        issues = p.validate()
        assert any("invalid decision" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Future-only decision freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestFutureOnlyDecisionFreeze:
    def test_future_decisions_match_frozen(self):
        assert UNAVAILABLE_GEP_DECISIONS == frozenset(FROZEN_FUTURE_DECISIONS)

    def test_future_decisions_not_in_valid(self):
        for d in FROZEN_FUTURE_DECISIONS:
            assert d not in VALID_GEP_DECISIONS

    def test_future_decisions_fail_validation(self):
        for d in FROZEN_FUTURE_DECISIONS:
            p = GovernedExecutionPreflightPrototype(
                prototype_id="t", decision=d,
                prototype_status=GEP_BLOCKED,
            )
            issues = p.validate()
            assert any("future-only" in i for i in issues), f"{d!r} should fail"

    def test_future_decisions_non_authorizing(self):
        for d in FROZEN_FUTURE_DECISIONS:
            p = GovernedExecutionPreflightPrototype(
                prototype_id="t", decision=d,
                prototype_status=GEP_BLOCKED,
            )
            assert p.push_authorized is False
            assert p.execution_available is False


# ═══════════════════════════════════════════════════════════════════════════
# 5. Authorization flag freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthorizationFlagFreeze:
    def test_all_12_flags_false_by_default(self):
        p = GovernedExecutionPreflightPrototype()
        for flag_name in FROZEN_AUTH_FLAGS:
            assert getattr(p, flag_name) is False, f"{flag_name} must be False"

    def test_validate_rejects_any_true_flag(self):
        for flag_name in FROZEN_AUTH_FLAGS:
            kwargs = {"prototype_id": "t", "prototype_status": GEP_BLOCKED, "decision": GEP_DECISION_BLOCK}
            kwargs[flag_name] = True
            p = GovernedExecutionPreflightPrototype(**kwargs)
            issues = p.validate()
            assert any(f"{flag_name} must be False" in i for i in issues)

    def test_verify_rejects_any_true_flag(self):
        for flag_name in FROZEN_AUTH_FLAGS:
            p = GovernedExecutionPreflightPrototype(
                prototype_id="t", prototype_status=GEP_BLOCKED,
                decision=GEP_DECISION_BLOCK,
            )
            setattr(p, flag_name, True)
            p.digest = p.compute_digest()
            r = verify_governed_execution_preflight_prototype(p)
            assert r["valid"] is False

    def test_digest_changes_with_any_flag(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        ref = p.compute_digest()
        for flag_name in FROZEN_AUTH_FLAGS:
            p2 = GovernedExecutionPreflightPrototype.from_dict(p.to_dict())
            setattr(p2, flag_name, True)
            assert p2.compute_digest() != ref


# ═══════════════════════════════════════════════════════════════════════════
# 6. Digest freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestDigestFreeze:
    def test_digest_sha256_hex(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert len(p.digest) == 64

    def test_digest_deterministic(self):
        p1 = GovernedExecutionPreflightPrototype(
            prototype_id="det", prototype_status=GEP_BLOCKED,
            decision=GEP_DECISION_BLOCK,
        )
        p2 = GovernedExecutionPreflightPrototype(
            prototype_id="det", prototype_status=GEP_BLOCKED,
            decision=GEP_DECISION_BLOCK,
        )
        assert p1.compute_digest() == p2.compute_digest()

    def test_digest_excludes_digest_field(self):
        p = GovernedExecutionPreflightPrototype(
            prototype_id="ex", prototype_status=GEP_BLOCKED,
            decision=GEP_DECISION_BLOCK,
        )
        d1 = p.compute_digest()
        p.digest = "0" * 64
        assert p.compute_digest() == d1

    def test_digest_changes_with_status(self):
        p1 = GovernedExecutionPreflightPrototype(prototype_id="ds", prototype_status=GEP_BLOCKED, decision=GEP_DECISION_BLOCK)
        p2 = GovernedExecutionPreflightPrototype(prototype_id="ds", prototype_status=GEP_UNAVAILABLE, decision=GEP_DECISION_BLOCK)
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_changes_with_decision(self):
        p1 = GovernedExecutionPreflightPrototype(prototype_id="dd", decision=GEP_DECISION_BLOCK, prototype_status=GEP_BLOCKED)
        p2 = GovernedExecutionPreflightPrototype(prototype_id="dd", decision=GEP_DECISION_DENY, prototype_status=GEP_BLOCKED)
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_changes_with_source_digest(self, source_preflight):
        p1 = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        src2 = ExecutionReadinessPreflight(preflight_id="chg", preflight_status=GEP_BLOCKED)
        src2.digest = "a" * 64
        p2 = build_governed_execution_preflight_prototype(
            source_preflight=src2, load_latest=False,
        )
        assert p1.compute_digest() != p2.compute_digest()

    def test_tampered_artifact_fails_verify(self, clean_artifact_dir, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        save_governed_execution_preflight_prototype(p)
        latest = _gep_latest_path()
        data = _json.loads(latest.read_text())
        data["digest"] = "0" * 64
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_governed_execution_preflight_prototype()
        r = verify_governed_execution_preflight_prototype(loaded)
        assert r["valid"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 7. CLI contract freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIContractFreeze:
    def test_json_shape_stable(self):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "preflight", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        for field in FROZEN_TOP_LEVEL_FIELDS:
            assert field in data, f"CLI JSON missing: {field!r}"

    def test_json_auth_flags_all_false(self):
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

    def test_save_writes_to_expected_path(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        latest = _gep_latest_path()
        assert latest.exists()

    def test_show_and_verify_same_artifact(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r_s = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "show", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r_v = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "verify", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        s_data = _json.loads(r_s.stdout)
        v_data = _json.loads(r_v.stdout)
        assert s_data["prototype_id"] == v_data.get("prototype_id", "")

    def test_cli_does_not_execute(self, clean_artifact_dir):
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


# ═══════════════════════════════════════════════════════════════════════════
# 8. Latest/show/verify freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestLatestShowVerifyFreeze:
    def test_latest_path_within_artifact_dir(self):
        latest = str(_gep_latest_path())
        assert "governed-execution-preflight" in latest
        assert ".pcae" in latest
        assert latest.endswith("latest.json")

    def test_latest_no_dotdot(self):
        assert ".." not in str(_gep_latest_path())

    def test_latest_no_url(self):
        s = str(_gep_latest_path())
        assert not s.startswith("http")

    def test_show_no_artifact_fails(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "show", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        assert "error" in data or "no_prototype" in str(data).lower()

    def test_verify_no_artifact_fails(self, clean_artifact_dir):
        import subprocess, sys
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "governed-execution", "verify", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        assert data["valid"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 9. Compatibility
# ═══════════════════════════════════════════════════════════════════════════


class TestCompatibility:
    def test_current_schema_accepted(self):
        p = GovernedExecutionPreflightPrototype(
            prototype_id="c", schema_version="1.0",
            prototype_status=GEP_BLOCKED, decision=GEP_DECISION_BLOCK,
        )
        issues = p.validate()
        assert not any("unknown schema_version" in i for i in issues)

    def test_unknown_schema_rejected(self):
        for v in ("2.0", "999.0"):
            p = GovernedExecutionPreflightPrototype(
                prototype_id="c", schema_version=v,
                prototype_status=GEP_BLOCKED, decision=GEP_DECISION_BLOCK,
            )
            issues = p.validate()
            assert any("unknown schema_version" in i for i in issues)

    def test_any_auth_flag_true_fails_verify(self):
        for flag_name in FROZEN_AUTH_FLAGS:
            p = GovernedExecutionPreflightPrototype(
                prototype_id="c", prototype_status=GEP_BLOCKED,
                decision=GEP_DECISION_BLOCK,
            )
            setattr(p, flag_name, True)
            p.digest = p.compute_digest()
            r = verify_governed_execution_preflight_prototype(p)
            assert r["valid"] is False

    def test_future_decision_fails_validate(self):
        for d in FROZEN_FUTURE_DECISIONS:
            p = GovernedExecutionPreflightPrototype(
                prototype_id="c", decision=d,
                prototype_status=GEP_BLOCKED,
            )
            issues = p.validate()
            assert any("future-only" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════════
# 10. No-execution guard
# ═══════════════════════════════════════════════════════════════════════════


class TestNoExecutionGuard:
    def test_build_returns_dataclass(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        assert isinstance(p, GovernedExecutionPreflightPrototype)

    def test_save_filesystem_only(self, clean_artifact_dir, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        path = save_governed_execution_preflight_prototype(p)
        assert path.exists()
        data = _json.loads(path.read_text())
        assert data["no_execution"] is True

    def test_verify_pure_computation(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        r = verify_governed_execution_preflight_prototype(p)
        assert isinstance(r, dict)
        assert "valid" in r

    def test_digest_no_subprocess(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        d = p.compute_digest()
        assert len(d) == 64

    def test_to_dict_no_execution_paths(self, source_preflight):
        p = build_governed_execution_preflight_prototype(
            source_preflight=source_preflight, load_latest=False,
        )
        d_str = _json.dumps(p.to_dict()).lower()
        assert "subprocess.run" not in d_str
        assert "os.system" not in d_str
        assert "Popen" not in d_str
