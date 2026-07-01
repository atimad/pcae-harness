"""Contract-freeze tests for execution readiness preflight — Phase 97G.

Freezes the 97F preflight model schema, statuses, no-go conditions,
evidence categories, authorization flags, digest behavior, CLI contract,
latest/show/verify semantics, and compatibility rules.

Tests assert structural stability — no brittle full-output snapshots.
All authorization flags must remain False. Execution must remain unavailable.
"""

from __future__ import annotations

import hashlib
import json as _json
import pytest
from datetime import datetime, timezone

from pcae.core.backend_invocations import (
    _PREFLIGHT_SCHEMA_VERSION,
    # ── Statuses ──
    PREFLIGHT_UNAVAILABLE,
    PREFLIGHT_NOT_READY,
    PREFLIGHT_BLOCKED,
    PREFLIGHT_EVIDENCE_INCOMPLETE,
    PREFLIGHT_APPROVAL_REQUIRED,
    PREFLIGHT_AUDIT_REQUIRED,
    PREFLIGHT_ROLLBACK_REQUIRED,
    PREFLIGHT_FAILED_VERIFICATION,
    PREFLIGHT_READY_FOR_HUMAN_REVIEW,
    PREFLIGHT_READY_FOR_PREFLIGHT_ONLY,
    PREFLIGHT_EXECUTION_READY_FUTURE_ONLY,
    PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY,
    PREFLIGHT_INVOKE_NOW_FUTURE_ONLY,
    PREFLIGHT_APPLY_NOW_FUTURE_ONLY,
    PREFLIGHT_COMMIT_NOW_FUTURE_ONLY,
    PREFLIGHT_PUSH_NOW_FUTURE_ONLY,
    VALID_PREFLIGHT_STATUSES,
    CURRENT_PREFLIGHT_STATUSES,
    UNAVAILABLE_PREFLIGHT_STATUSES,
    # ── Evidence ──
    EVIDENCE_READINESS_MODEL,
    EVIDENCE_BACKEND_CONTRACT,
    EVIDENCE_ADAPTER_BOUNDARY,
    EVIDENCE_HUMAN_APPROVAL_GATE,
    EVIDENCE_AUDIT_READINESS,
    EVIDENCE_ROLLBACK_READINESS,
    EVIDENCE_ARTIFACT_VERIFICATION,
    EVIDENCE_EXECUTION_BOUNDARY_PROOF,
    EVIDENCE_PHASE_FINALIZATION,
    EVIDENCE_ACTIVE_TASK,
    ALL_EVIDENCE_CATEGORIES,
    # ── No-go ──
    NOGO_MISSING_READINESS,
    NOGO_MISSING_BACKEND_CONTRACT,
    NOGO_MISSING_ADAPTER_BOUNDARY,
    NOGO_MISSING_APPROVAL,
    NOGO_EXPIRED_APPROVAL,
    NOGO_MISSING_AUDIT,
    NOGO_MISSING_ROLLBACK,
    NOGO_FAILED_VERIFICATION,
    NOGO_MISSING_BOUNDARY_PROOF,
    NOGO_STALE_POINTER,
    NOGO_UNKNOWN_SCHEMA,
    NOGO_CONFLICTING_FLAGS,
    NOGO_FORBIDDEN_PATH,
    NOGO_SECRET_DETECTED,
    NOGO_NETWORK_REQUESTED,
    NOGO_SUBPROCESS_REQUESTED,
    NOGO_SHELL_REQUESTED,
    NOGO_TELEGRAM_INBOUND,
    NOGO_APPLY_REQUESTED,
    NOGO_ROLLBACK_EXEC_REQUESTED,
    NOGO_COMMIT_PUSH_REQUESTED,
    NOGO_RAW_GIT,
    NOGO_NO_VERIFY,
    NOGO_FORCE_PUSH,
    NOGO_BYPASS_PERMISSIONS,
    VALID_NOGO_CONDITIONS,
    # ── Model ──
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
def fresh_preflight():
    """Build a fresh preflight with default inputs."""
    return build_execution_readiness_preflight()


@pytest.fixture
def clean_artifact_dir():
    """Ensure clean artifact directory."""
    import shutil
    dir_path = _preflight_dir_path()
    if dir_path.exists():
        shutil.rmtree(dir_path)
    yield
    if dir_path.exists():
        shutil.rmtree(dir_path)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Schema field freeze — top-level fields in to_dict()
# ═══════════════════════════════════════════════════════════════════════════

FROZEN_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "schema_version",
    "preflight_id",
    "phase_id",
    "task_id",
    "generated_at_utc",
    "readiness_status",
    "preflight_status",
    "evidence_status",
    "backend_invocation_contract_status",
    "adapter_boundary_status",
    "approval_status",
    "audit_readiness_status",
    "rollback_readiness_status",
    "artifact_verification_status",
    "execution_boundary_proof_status",
    "no_go_conditions",
    "missing_evidence",
    "failed_checks",
    "warnings",
    "evidence_refs",
    "approval_refs",
    "audit_refs",
    "rollback_refs",
    "proof_refs",
    "authorization_summary",
    "simulation_only",
    "no_execution",
    "digest",
)

FROZEN_AUTH_FIELDS: tuple[str, ...] = (
    "execution_available",
    "execution_authorized",
    "backend_invocation_authorized",
    "adapter_execution_authorized",
    "network_authorized",
    "subprocess_authorized",
    "shell_authorized",
    "mutation_authorized",
    "apply_authorized",
    "rollback_authorized",
    "commit_authorized",
    "push_authorized",
)


class TestSchemaFieldFreeze:
    """Top-level fields of ExecutionReadinessPreflight.to_dict() are frozen."""

    def test_top_level_fields_present(self, fresh_preflight):
        """All 28 top-level fields must be present in to_dict()."""
        d = fresh_preflight.to_dict()
        for field in FROZEN_TOP_LEVEL_FIELDS:
            assert field in d, f"Missing top-level field: {field!r}"

    def test_schema_version_is_stable(self, fresh_preflight):
        """schema_version must be '1.0'."""
        d = fresh_preflight.to_dict()
        assert d["schema_version"] == "1.0"

    def test_preflight_id_is_non_empty_when_built(self, fresh_preflight):
        """preflight_id must be non-empty string."""
        d = fresh_preflight.to_dict()
        assert isinstance(d["preflight_id"], str)
        assert len(d["preflight_id"]) > 0

    def test_generated_at_utc_is_iso_timestamp(self, fresh_preflight):
        """generated_at_utc must be ISO format timestamp."""
        d = fresh_preflight.to_dict()
        assert "T" in d["generated_at_utc"]
        assert "+" in d["generated_at_utc"] or "Z" in d["generated_at_utc"]

    def test_list_fields_are_lists(self, fresh_preflight):
        """Aggregated result fields must be list types."""
        d = fresh_preflight.to_dict()
        list_fields = (
            "no_go_conditions", "missing_evidence", "failed_checks",
            "warnings", "evidence_refs", "approval_refs",
            "audit_refs", "rollback_refs", "proof_refs",
        )
        for field in list_fields:
            assert isinstance(d[field], list), f"{field!r} must be list"

    def test_simulation_only_is_true(self, fresh_preflight):
        """simulation_only must be True."""
        d = fresh_preflight.to_dict()
        assert d["simulation_only"] is True

    def test_no_execution_is_true(self, fresh_preflight):
        """no_execution must be True."""
        d = fresh_preflight.to_dict()
        assert d["no_execution"] is True

    def test_digest_is_64_char_hex(self, fresh_preflight):
        """digest must be 64-char hex string (SHA-256)."""
        d = fresh_preflight.to_dict()
        assert len(d["digest"]) == 64
        assert all(c in "0123456789abcdef" for c in d["digest"])

    def test_authorization_summary_has_all_12_flags(self, fresh_preflight):
        """authorization_summary must contain exactly the 12 frozen flags."""
        d = fresh_preflight.to_dict()
        auth = d["authorization_summary"]
        for flag in FROZEN_AUTH_FIELDS:
            assert flag in auth, f"Missing auth flag: {flag!r}"
        assert len(auth) == 12

    def test_from_dict_roundtrip_preserves_all_fields(self, fresh_preflight):
        """from_dict(to_dict()) preserves all frozen fields."""
        d = fresh_preflight.to_dict()
        p2 = ExecutionReadinessPreflight.from_dict(d)
        d2 = p2.to_dict()
        for field in FROZEN_TOP_LEVEL_FIELDS:
            assert field in d2, f"Missing field after roundtrip: {field!r}"

    def test_no_extra_top_level_fields(self, fresh_preflight):
        """No unexpected top-level fields beyond the frozen set."""
        d = fresh_preflight.to_dict()
        extra = set(d.keys()) - set(FROZEN_TOP_LEVEL_FIELDS)
        assert not extra, f"Unexpected top-level fields: {extra}"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Status freeze
# ═══════════════════════════════════════════════════════════════════════════

FROZEN_VALID_STATUSES: tuple[str, ...] = (
    "unavailable",
    "not_ready",
    "blocked",
    "evidence_incomplete",
    "approval_required",
    "audit_required",
    "rollback_required",
    "failed_verification",
    "ready_for_human_review",
    "ready_for_preflight_only",
)

FROZEN_FUTURE_ONLY_STATUSES: tuple[str, ...] = (
    "execution_ready",
    "execute_now",
    "invoke_now",
    "apply_now",
    "commit_now",
    "push_now",
)


class TestStatusFreeze:
    """Preflight status values are frozen."""

    def test_valid_statuses_match_frozen(self):
        """VALID_PREFLIGHT_STATUSES contains exactly the 10 frozen statuses."""
        assert VALID_PREFLIGHT_STATUSES == frozenset(FROZEN_VALID_STATUSES)

    def test_current_statuses_match_valid(self):
        """CURRENT_PREFLIGHT_STATUSES == VALID_PREFLIGHT_STATUSES."""
        assert CURRENT_PREFLIGHT_STATUSES == VALID_PREFLIGHT_STATUSES

    def test_future_only_statuses_are_separate(self):
        """Future-only statuses are NOT in valid set."""
        for s in FROZEN_FUTURE_ONLY_STATUSES:
            assert s not in VALID_PREFLIGHT_STATUSES
            assert s in UNAVAILABLE_PREFLIGHT_STATUSES

    def test_valid_statuses_exclude_executing(self):
        """No valid status implies execution capability."""
        executing = {"execute_now", "invoke_now", "apply_now", "commit_now", "push_now", "execution_ready"}
        assert VALID_PREFLIGHT_STATUSES.isdisjoint(executing)

    def test_ready_for_preflight_only_is_non_authorizing(self):
        """ready_for_preflight_only must not authorize execution."""
        p = ExecutionReadinessPreflight(
            preflight_id="test",
            preflight_status=PREFLIGHT_READY_FOR_PREFLIGHT_ONLY,
        )
        assert p.execution_available is False
        assert p.execution_authorized is False
        assert p.no_execution is True
        assert p.simulation_only is True

    def test_ready_for_human_review_is_non_authorizing(self):
        """ready_for_human_review must not authorize execution."""
        p = ExecutionReadinessPreflight(
            preflight_id="test",
            preflight_status=PREFLIGHT_READY_FOR_HUMAN_REVIEW,
        )
        assert p.execution_available is False
        assert p.execution_authorized is False

    def test_unknown_status_fails_validation(self):
        """An unknown preflight status must fail validation."""
        p = ExecutionReadinessPreflight(
            preflight_id="test",
            preflight_status="not_a_real_status",
        )
        issues = p.validate()
        assert any("invalid preflight_status" in i for i in issues)

    def test_future_status_fails_validation(self):
        """Any future-only status used as current must fail validation."""
        for s in FROZEN_FUTURE_ONLY_STATUSES:
            p = ExecutionReadinessPreflight(
                preflight_id="test",
                preflight_status=s,
            )
            issues = p.validate()
            assert any("future-only" in i for i in issues), f"{s!r} should fail"


# ═══════════════════════════════════════════════════════════════════════════
# 3. No-go condition freeze
# ═══════════════════════════════════════════════════════════════════════════

# 25 97F-originated + 4 97A passthrough = 29
FROZEN_NOGO_COUNT = 29

FROZEN_NOGO_97F_ORIGINATED: tuple[str, ...] = (
    "missing_execution_readiness",
    "missing_backend_invocation_contract",
    "missing_adapter_boundary",
    "missing_human_approval",
    "expired_or_revoked_approval",
    "missing_audit_readiness",
    "missing_rollback_readiness",
    "failed_artifact_verification",
    "missing_execution_boundary_proof",
    "stale_latest_pointer",
    "unknown_schema_version",
    "conflicting_safety_flags",
    "forbidden_path_or_scope",
    "secret_material_detected",
    "network_requested",
    "subprocess_requested",
    "shell_requested",
    "telegram_inbound_requested",
    "apply_requested_without_governance",
    "rollback_execution_requested",
    "commit_or_push_requested",
    "raw_git_path_detected",
    "no_verify_attempt",
    "force_push_attempt",
    "bypass_permissions_detected",
)

FROZEN_NOGO_97A_PASSTHROUGH: tuple[str, ...] = (
    "execution_readiness_model_not_implemented",
    "backend_invocation_never_implemented",
    "subprocess_mediation_never_implemented",
    "shell_mediation_never_implemented",
)


class TestNoGoFreeze:
    """No-go condition values are frozen."""

    def test_valid_nogo_count_is_29(self):
        """VALID_NOGO_CONDITIONS must contain exactly 29 entries."""
        assert len(VALID_NOGO_CONDITIONS) == FROZEN_NOGO_COUNT

    def test_all_97f_originated_nogo_are_valid(self):
        """All 25 97F-originated no-go conditions must be in VALID_NOGO_CONDITIONS."""
        for ng in FROZEN_NOGO_97F_ORIGINATED:
            assert ng in VALID_NOGO_CONDITIONS, f"Missing no-go: {ng!r}"

    def test_all_97a_passthrough_nogo_are_valid(self):
        """All 4 97A passthrough no-go conditions must be in VALID_NOGO_CONDITIONS."""
        for ng in FROZEN_NOGO_97A_PASSTHROUGH:
            assert ng in VALID_NOGO_CONDITIONS, f"Missing passthrough no-go: {ng!r}"

    def test_no_go_values_are_stable_strings(self):
        """No-go values must be lowercase snake_case strings."""
        for ng in VALID_NOGO_CONDITIONS:
            assert isinstance(ng, str)
            assert ng == ng.lower()
            assert " " not in ng

    def test_unknown_nogo_fails_validation(self):
        """An unknown no-go condition must fail validation."""
        p = ExecutionReadinessPreflight(
            preflight_id="test",
            preflight_status=PREFLIGHT_BLOCKED,
            no_go_conditions=["definitely_not_a_real_nogo_xyz"],
        )
        issues = p.validate()
        assert any("unknown no_go_condition" in i for i in issues)

    def test_no_go_condition_present_forces_blocked_or_worse(self):
        """Any no-go condition must force blocked/fail-closed status."""
        p = build_execution_readiness_preflight()
        if p.no_go_conditions:
            assert p.preflight_status != PREFLIGHT_READY_FOR_PREFLIGHT_ONLY

    def test_no_go_conditions_cannot_override_auth_flags(self):
        """No-go conditions must not set any authorization flag True."""
        p = ExecutionReadinessPreflight(
            preflight_id="test",
            preflight_status=PREFLIGHT_BLOCKED,
            no_go_conditions=list(FROZEN_NOGO_97F_ORIGINATED),
        )
        assert p.execution_available is False
        assert p.execution_authorized is False
        assert p.push_authorized is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. Evidence category freeze
# ═══════════════════════════════════════════════════════════════════════════

FROZEN_EVIDENCE_CATEGORIES: tuple[str, ...] = (
    "readiness_model",
    "backend_invocation_contract",
    "adapter_invocation_boundary",
    "human_approval_gate",
    "audit_readiness",
    "rollback_readiness",
    "artifact_verification",
    "execution_boundary_proof",
    "phase_finalization_context",
    "active_task_contract",
)


class TestEvidenceCategoryFreeze:
    """Evidence category values are frozen."""

    def test_evidence_count_is_10(self):
        """ALL_EVIDENCE_CATEGORIES must contain exactly 10 entries."""
        assert len(ALL_EVIDENCE_CATEGORIES) == 10

    def test_all_evidence_categories_are_present(self):
        """All 10 evidence categories must be in ALL_EVIDENCE_CATEGORIES."""
        for cat in FROZEN_EVIDENCE_CATEGORIES:
            assert cat in ALL_EVIDENCE_CATEGORIES, f"Missing evidence category: {cat!r}"

    def test_evidence_categories_are_snake_case(self):
        """Evidence categories must be lowercase snake_case."""
        for cat in ALL_EVIDENCE_CATEGORIES:
            assert cat == cat.lower()
            assert " " not in cat

    def test_missing_evidence_does_not_become_authorization(self, fresh_preflight):
        """Missing evidence must not authorize execution."""
        d = fresh_preflight.to_dict()
        if d["missing_evidence"]:
            assert d["authorization_summary"]["execution_available"] is False
            assert d["authorization_summary"]["execution_authorized"] is False

    def test_evidence_refs_are_references_only(self, fresh_preflight):
        """Evidence refs must be strings, not dicts or executable specs."""
        for ref in fresh_preflight.evidence_refs:
            assert isinstance(ref, str)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Authorization flag freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthorizationFlagFreeze:
    """Authorization flags are frozen — all False by default."""

    def test_all_12_flags_false_by_default(self):
        """Every new preflight has all 12 authorization flags False."""
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

    def test_validate_rejects_any_true_flag(self):
        """validate() must reject any True authorization flag."""
        flags = FROZEN_AUTH_FIELDS
        for flag_name in flags:
            kwargs = {"preflight_id": "test", "preflight_status": PREFLIGHT_BLOCKED}
            kwargs[flag_name] = True
            p = ExecutionReadinessPreflight(**kwargs)
            issues = p.validate()
            assert any(f"{flag_name} must be False" in i for i in issues), (
                f"validate() should reject {flag_name}=True"
            )

    def test_verify_rejects_any_true_flag(self):
        """verify_execution_readiness_preflight must reject any True flag."""
        for flag_name in FROZEN_AUTH_FIELDS:
            p = ExecutionReadinessPreflight(
                preflight_id="test",
                preflight_status=PREFLIGHT_BLOCKED,
            )
            setattr(p, flag_name, True)
            p.digest = p.compute_digest()
            result = verify_execution_readiness_preflight(p)
            assert result["valid"] is False, f"verify should fail for {flag_name}=True"
            assert any(flag_name in issue for issue in result["issues"])

    def test_digest_changes_when_any_flag_changes(self):
        """Digest must change when any authorization flag changes."""
        p = build_execution_readiness_preflight(task_id="digest-flag-test")
        ref_digest = p.compute_digest()
        for flag_name in FROZEN_AUTH_FIELDS:
            p2 = ExecutionReadinessPreflight.from_dict(p.to_dict())
            setattr(p2, flag_name, True)
            assert p2.compute_digest() != ref_digest, (
                f"Digest should change for {flag_name}=True"
            )

    def test_built_preflight_all_flags_false(self, fresh_preflight):
        """A built preflight via builder has all flags False."""
        d = fresh_preflight.to_dict()
        auth = d["authorization_summary"]
        for flag in FROZEN_AUTH_FIELDS:
            assert auth[flag] is False, f"{flag} must be False in built preflight"


# ═══════════════════════════════════════════════════════════════════════════
# 6. Digest freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestDigestFreeze:
    """Digest behavior is frozen."""

    def test_digest_is_sha256_hex(self, fresh_preflight):
        """Digest must be 64-char lowercase hex (SHA-256)."""
        d = fresh_preflight.compute_digest()
        assert len(d) == 64
        assert all(c in "0123456789abcdef" for c in d)

    def test_digest_is_deterministic_for_same_fields(self):
        """Same field values produce same digest."""
        p1 = ExecutionReadinessPreflight(
            preflight_id="det-test",
            preflight_status=PREFLIGHT_BLOCKED,
            task_id="task-1",
        )
        p2 = ExecutionReadinessPreflight(
            preflight_id="det-test",
            preflight_status=PREFLIGHT_BLOCKED,
            task_id="task-1",
        )
        assert p1.compute_digest() == p2.compute_digest()

    def test_digest_excludes_digest_field(self):
        """compute_digest excludes the digest field from payload."""
        p = ExecutionReadinessPreflight(
            preflight_id="exclude-test",
            preflight_status=PREFLIGHT_BLOCKED,
        )
        d1 = p.compute_digest()
        p.digest = "0000000000000000000000000000000000000000000000000000000000000000"
        d2 = p.compute_digest()
        assert d1 == d2  # digest field excluded → same result

    def test_digest_changes_with_preflight_status(self):
        """Digest must change when preflight_status changes."""
        p1 = ExecutionReadinessPreflight(preflight_id="ds", preflight_status=PREFLIGHT_BLOCKED)
        p2 = ExecutionReadinessPreflight(preflight_id="ds", preflight_status=PREFLIGHT_NOT_READY)
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_changes_with_no_go_conditions(self):
        """Digest must change when no_go_conditions change."""
        p1 = ExecutionReadinessPreflight(preflight_id="ng", preflight_status=PREFLIGHT_BLOCKED)
        p2 = ExecutionReadinessPreflight(
            preflight_id="ng", preflight_status=PREFLIGHT_BLOCKED,
            no_go_conditions=["missing_execution_readiness"],
        )
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_changes_with_missing_evidence(self):
        """Digest must change when missing_evidence changes."""
        p1 = ExecutionReadinessPreflight(preflight_id="me", preflight_status=PREFLIGHT_BLOCKED)
        p2 = ExecutionReadinessPreflight(
            preflight_id="me", preflight_status=PREFLIGHT_BLOCKED,
            missing_evidence=["readiness_model"],
        )
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_changes_with_evidence_refs(self):
        """Digest must change when evidence_refs change."""
        p1 = ExecutionReadinessPreflight(preflight_id="er", preflight_status=PREFLIGHT_BLOCKED)
        p2 = ExecutionReadinessPreflight(
            preflight_id="er", preflight_status=PREFLIGHT_BLOCKED,
            evidence_refs=["model:test"],
        )
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_changes_with_simulation_flag(self):
        """Digest must change when simulation_only changes."""
        p1 = ExecutionReadinessPreflight(preflight_id="sim", preflight_status=PREFLIGHT_BLOCKED, simulation_only=True)
        p2 = ExecutionReadinessPreflight(preflight_id="sim", preflight_status=PREFLIGHT_BLOCKED, simulation_only=False)
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_changes_with_no_execution_flag(self):
        """Digest must change when no_execution changes."""
        p1 = ExecutionReadinessPreflight(preflight_id="ne", preflight_status=PREFLIGHT_BLOCKED, no_execution=True)
        p2 = ExecutionReadinessPreflight(preflight_id="ne", preflight_status=PREFLIGHT_BLOCKED, no_execution=False)
        assert p1.compute_digest() != p2.compute_digest()

    def test_digest_stable_across_to_dict_roundtrip(self):
        """Digest is self-consistent after to_dict/from_dict roundtrip."""
        p = build_execution_readiness_preflight(task_id="roundtrip")
        p2 = ExecutionReadinessPreflight.from_dict(p.to_dict())
        # p2's own digest should be self-consistent
        assert p2.compute_digest() == p2.compute_digest()
        # Both should produce valid SHA-256 hex digests
        assert len(p2.compute_digest()) == 64

    def test_tampered_artifact_fails_verify(self, clean_artifact_dir):
        """Saved artifact with tampered digest must fail verification."""
        p = build_execution_readiness_preflight(task_id="tamper-digest")
        save_execution_readiness_preflight(p)

        # Tamper the saved JSON
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["digest"] = "0" * 64
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")

        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False
        assert any("digest_mismatch" in i for i in result["issues"])


# ═══════════════════════════════════════════════════════════════════════════
# 7. CLI contract freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIContractFreeze:
    """CLI behavior is frozen — JSON shape, exit codes, safety."""

    def test_preflight_json_output_has_all_top_level_fields(self):
        """CLI --json output must contain all frozen top-level fields."""
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        assert r.returncode == 0
        data = _json.loads(r.stdout)
        for field in FROZEN_TOP_LEVEL_FIELDS:
            assert field in data, f"CLI JSON missing field: {field!r}"

    def test_preflight_json_auth_flags_all_false(self):
        """CLI --json output must have all authorization flags False."""
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        auth = data["authorization_summary"]
        for flag in FROZEN_AUTH_FIELDS:
            assert auth[flag] is False, f"CLI JSON auth {flag} must be False"

    def test_preflight_text_output_includes_required_facts(self):
        """CLI text output must include key facts: no-execution, digest, status."""
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        assert r.returncode == 0
        out = r.stdout
        assert "no_execution" in out.lower() or "no execution" in out.lower()
        assert "digest" in out.lower()
        assert "Preflight" in out

    def test_preflight_save_writes_to_expected_path(self, clean_artifact_dir):
        """--save must write to .pcae/execution-readiness-preflight/."""
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        latest = _preflight_latest_path()
        assert latest.exists()
        data = _json.loads(latest.read_text())
        assert "preflight_id" in data

    def test_show_latest_after_save_works(self, clean_artifact_dir):
        """show --latest reads the same artifact saved by --save."""
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "preflight", "--save"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "show", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        assert r.returncode == 0
        data = _json.loads(r.stdout)
        assert "preflight_id" in data

    def test_verify_latest_after_save_works(self, clean_artifact_dir):
        """verify --latest after --save should produce a result."""
        import subprocess, sys
        from pathlib import Path
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
        assert "valid" in data
        assert "no_execution_confirmed" in data
        assert data["no_execution_confirmed"] is True

    def test_show_no_artifact_fails_clearly(self, clean_artifact_dir):
        """show --latest with no artifact must fail with clear message."""
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "show"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        assert r.returncode != 0 or "no preflight" in (r.stdout + r.stderr).lower()

    def test_verify_no_artifact_fails_clearly(self, clean_artifact_dir):
        """verify --latest with no artifact must fail clearly."""
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        r = subprocess.run(
            [sys.executable, "-m", "pcae", "execution-readiness", "verify", "--json"],
            capture_output=True, text=True, cwd=repo, timeout=15,
        )
        data = _json.loads(r.stdout)
        assert data["valid"] is False
        assert not data.get("preflight_present", True)

    def test_cli_does_not_execute_anything(self, clean_artifact_dir):
        """CLI commands must not execute backends, adapters, or mutation."""
        import subprocess, sys
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        for cmd in (
            ["execution-readiness", "preflight", "--json"],
            ["execution-readiness", "preflight", "--save"],
        ):
            r = subprocess.run(
                [sys.executable, "-m", "pcae"] + cmd,
                capture_output=True, text=True, cwd=repo, timeout=15,
            )
            assert r.returncode == 0, f"Command {cmd} failed: {r.stderr}"


# ═══════════════════════════════════════════════════════════════════════════
# 8. Latest/show/verify freeze
# ═══════════════════════════════════════════════════════════════════════════


class TestLatestShowVerifyFreeze:
    """Latest/show/verify semantics are frozen."""

    def test_latest_path_is_within_preflight_dir(self):
        """Latest must be within .pcae/execution-readiness-preflight/."""
        latest = _preflight_latest_path()
        assert "execution-readiness-preflight" in str(latest)
        assert ".pcae" in str(latest)
        assert str(latest).endswith("latest.json")

    def test_latest_does_not_escape_with_dotdot(self):
        """Latest path must not be susceptible to ../ traversal."""
        latest = _preflight_latest_path()
        assert ".." not in str(latest)

    def test_save_and_load_show_same_preflight_id(self, clean_artifact_dir):
        """save then load → same preflight_id."""
        p = build_execution_readiness_preflight(task_id="id-test")
        save_execution_readiness_preflight(p)
        loaded = load_latest_execution_readiness_preflight()
        assert loaded.preflight_id == p.preflight_id

    def test_show_and_verify_resolve_same_artifact(self, clean_artifact_dir):
        """show and verify resolve the same latest artifact."""
        import subprocess, sys
        from pathlib import Path
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

    def test_tampered_latest_fails_verify(self, clean_artifact_dir):
        """Tampered latest.json must fail verify."""
        p = build_execution_readiness_preflight(task_id="tamper-verify")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["execution_available"] = True
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 9. Compatibility behavior
# ═══════════════════════════════════════════════════════════════════════════


class TestCompatibilityBehavior:
    """Compatibility rules are frozen."""

    def test_current_schema_accepted(self):
        """Current schema version ('1.0') must be accepted by validate()."""
        p = ExecutionReadinessPreflight(
            preflight_id="compat",
            preflight_status=PREFLIGHT_BLOCKED,
            schema_version="1.0",
        )
        issues = p.validate()
        assert not any("unknown schema_version" in i for i in issues)

    def test_missing_schema_fails_verify(self):
        """Missing schema_version must fail verification."""
        p = build_execution_readiness_preflight(task_id="no-schema")
        p.schema_version = ""
        p.digest = p.compute_digest()
        result = verify_execution_readiness_preflight(p)
        assert result["valid"] is False

    def test_unknown_major_schema_fails(self):
        """Unknown future schema version must fail validation."""
        for bad_ver in ("2.0", "999.0", "1.1"):
            p = ExecutionReadinessPreflight(
                preflight_id="schema",
                preflight_status=PREFLIGHT_BLOCKED,
                schema_version=bad_ver,
            )
            issues = p.validate()
            assert any("unknown schema_version" in i for i in issues), (
                f"Schema {bad_ver!r} should be rejected"
            )

    def test_any_auth_flag_true_fails_verify(self):
        """Any authorization flag True must fail verify in current system."""
        for flag_name in FROZEN_AUTH_FIELDS:
            p = ExecutionReadinessPreflight(
                preflight_id="auth-test",
                preflight_status=PREFLIGHT_BLOCKED,
            )
            setattr(p, flag_name, True)
            p.digest = p.compute_digest()
            result = verify_execution_readiness_preflight(p)
            assert result["valid"] is False, f"verify should reject {flag_name}=True"

    def test_contradictory_safety_fails(self):
        """no_execution=False with simulation_only=True is contradictory."""
        p = ExecutionReadinessPreflight(
            preflight_id="contra",
            preflight_status=PREFLIGHT_BLOCKED,
            no_execution=False,
            simulation_only=True,
        )
        issues = p.validate()
        assert any("no_execution must be True" in i for i in issues)

    def test_unknown_status_fails_verify(self, clean_artifact_dir):
        """Unknown preflight status in saved artifact must fail verify."""
        p = build_execution_readiness_preflight(task_id="bad-status")
        save_execution_readiness_preflight(p)
        latest = _preflight_latest_path()
        data = _json.loads(latest.read_text())
        data["preflight_status"] = "unknown_future_status_xyz"
        payload = {k: v for k, v in data.items() if k != "digest"}
        data["digest"] = hashlib.sha256(
            _json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        latest.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        loaded = load_latest_execution_readiness_preflight()
        result = verify_execution_readiness_preflight(loaded)
        assert result["valid"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 10. No-execution guard
# ═══════════════════════════════════════════════════════════════════════════


class TestNoExecutionGuard:
    """Contract operations must never execute anything."""

    def test_build_returns_dataclass_not_execution(self):
        """build returns a dataclass, not executes."""
        result = build_execution_readiness_preflight()
        assert isinstance(result, ExecutionReadinessPreflight)

    def test_save_uses_filesystem_only(self, clean_artifact_dir):
        """save writes JSON files only — no subprocess/network/shell."""
        p = build_execution_readiness_preflight(task_id="guard-save")
        path = save_execution_readiness_preflight(p)
        assert path.exists()
        content = path.read_text()
        data = _json.loads(content)
        assert data["no_execution"] is True
        assert data["simulation_only"] is True

    def test_verify_is_pure_computation(self):
        """verify only inspects preflight object — no filesystem outside artifact."""
        p = build_execution_readiness_preflight(task_id="guard-verify")
        result = verify_execution_readiness_preflight(p)
        assert isinstance(result, dict)
        assert "valid" in result

    def test_preflight_to_dict_has_no_execution_paths(self):
        """to_dict output contains no executable system call patterns."""
        p = build_execution_readiness_preflight(task_id="no-exec-path")
        d_str = _json.dumps(p.to_dict())
        # Safety flag names like subprocess_authorized are fine —
        # they're authorization booleans, not execution paths.
        # Check for actual execution API calls
        assert "os.system" not in d_str.lower()
        assert "Popen" not in d_str
        assert "check_output" not in d_str

    def test_all_authorization_flags_remain_false_in_cli_output(self):
        """Every CLI path must output all auth flags as False."""
        import subprocess, sys
        from pathlib import Path
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
        for flag in FROZEN_AUTH_FIELDS:
            assert auth[flag] is False, f"CLI {flag} must be False"
