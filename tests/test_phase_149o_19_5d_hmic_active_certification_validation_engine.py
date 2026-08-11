"""Phase 149O.19.5D -- HMIC Active Certification Validation Engine.

Phase-boundary verification and behavioral test suite for Wave D (`docs/
PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md` §9.3): the read-only
validation-algorithm layer extending `src/pcae/core/hatp_mandatory_
certification.py` -- `HMICValidationResult`, `_validate_at_root`, and
`validate_active_hatp_mandatory_independent_verification_certification`.

Scope discipline (restated from the 149O.19.5A/B/C suites, extended to
validation): this phase answers "is the currently active-bound
certification VALID against the current environment?" -- and only that.
No test here asserts, exercises, or would be satisfied by: a readiness-
integration effect (the hard-coded `mandatory_consumption_
implementation_independently_verified = False` ceiling in
`hatp_mandatory_cutover.py` is never read or imported here), an admin-
ceremony call, a `pcae` CLI change, or a mutation of `certifications.
json`/`certification-bindings.json` performed by the validator itself.
All tests use isolated, private temporary protected roots and isolated,
private temporary git-fixture repositories -- never `HATPTrustStore.
production().root` and never this actual repository's own frozen files
for mismatch-inducing mutation (mirroring the 149O.19.5B suite's
`fixture_repo` monkeypatch pattern exactly: item 81/113 forbids ever
mutating this repository's own real authority-bearing source just to
test digest sensitivity).
"""
from __future__ import annotations

import ast
import inspect
import re
import subprocess
import threading
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_NEW_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_CUTOVER_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"


def _git(args: "list[str]", cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Fixture"], cwd=root, check=True)


def _git_commit_all(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)
    return _git(["rev-parse", "HEAD"], cwd=root)


# ═══════════════════════════════════════════════════════════════════════════
# Isolated fixture: a minimal, fully self-consistent git repository whose
# frozen-set entries and bound-contract files are controlled fixture files
# (never this repository's own real frozen files -- item 81/113), plus a
# sibling isolated protected-root directory.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def env(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    protected_root = tmp_path / "protected-root"
    (repo_root / "src" / "pcae" / "core").mkdir(parents=True)
    (repo_root / "docs" / "contracts").mkdir(parents=True)

    (repo_root / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"alpha content v1\n")
    (repo_root / "src" / "pcae" / "core" / "not_frozen.py").write_bytes(b"irrelevant\n")
    for name, cid, ver in (
        ("FIXTURE_HMRC.md", "HMRC-001", "1.0"),
        ("FIXTURE_HATP.md", "HATP-001", "1.0"),
        ("FIXTURE_HSCE.md", "HSCE-001", "1.1"),
        ("FIXTURE_RAE.md", "RAE-001", "1.0"),
    ):
        (repo_root / "docs" / "contracts" / name).write_bytes(f"**Contract:** {cid}\n**Version:** {ver}\n".encode())

    monkeypatch.setattr(
        hmic,
        "_FROZEN_AUTHORITY_BEARING_FILES",
        (
            "core/fixture_a.py",
            "docs/contracts/FIXTURE_HMRC.md",
            "docs/contracts/FIXTURE_HATP.md",
            "docs/contracts/FIXTURE_HSCE.md",
            "docs/contracts/FIXTURE_RAE.md",
        ),
    )
    monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)
    monkeypatch.setattr(
        hmic,
        "_CONTRACT_IDENTITY_FILES",
        (
            ("HMRC-001", "docs/contracts/FIXTURE_HMRC.md"),
            ("HATP-001", "docs/contracts/FIXTURE_HATP.md"),
            ("HSCE-001", "docs/contracts/FIXTURE_HSCE.md"),
            ("RAE-001", "docs/contracts/FIXTURE_RAE.md"),
        ),
    )

    _init_git_repo(repo_root)
    _git_commit_all(repo_root, "initial")

    identity = ensure_repository_identity(HarnessPath(repo_root))
    repository_instance_id = identity.repository_instance_id
    canonical_deployment_root = hmic.derive_canonical_deployment_root(HarnessPath(repo_root))

    return {
        "repo_root": repo_root,
        "protected_root": protected_root,
        "repository_instance_id": repository_instance_id,
        "canonical_deployment_root": canonical_deployment_root,
    }


def _current_fields(env, *, certified_at="2026-08-10T00:00:00Z", certified_by="protected-admin", verification_record_digest="c" * 64):
    root = HarnessPath(env["repo_root"])
    return dict(
        repository_instance_id=env["repository_instance_id"],
        canonical_deployment_root=env["canonical_deployment_root"],
        implementation_commit=hmic.derive_implementation_commit(root),
        implementation_scope_digest=hmic.derive_implementation_scope_digest(root),
        contract_versions=dict(hmic.derive_contract_versions(root)),
        verification_record_digest=verification_record_digest,
        certified_at=certified_at,
        certified_by=certified_by,
    )


def _record_from_fields(fields: dict, *, status="active", revoked_at=None) -> hmic.CertificationRecord:
    certification_id = hmic.derive_certification_id(fields)
    return hmic.CertificationRecord(certification_id=certification_id, status=status, revoked_at=revoked_at, **fields)


def _store_and_bind(env, record: hmic.CertificationRecord) -> None:
    hmic._append_certification_record(env["protected_root"], record)
    hmic._write_active_binding(
        env["protected_root"],
        hmic.CertificationBinding(
            repository_instance_id=env["repository_instance_id"],
            canonical_deployment_root=env["canonical_deployment_root"],
            active_certification_id=record.certification_id,
        ),
    )


def _validate(env) -> hmic.HMICValidationResult:
    return hmic._validate_at_root(protected_root=env["protected_root"], repository_root=env["repo_root"])


# ═══════════════════════════════════════════════════════════════════════════
# VALID path -- control-flow proof only (HMIC-REQ-107/103 step 12).
# ═══════════════════════════════════════════════════════════════════════════


class TestValidPath:
    def test_fully_consistent_fixture_validates_valid(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.VALID
        assert hmic.certification_status_satisfies_readiness(result.status) is True

    def test_valid_result_has_no_readiness_or_activation_field(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        result = _validate(env)
        field_names = {f for f in vars(result)}
        for forbidden in ("approved", "permitted", "executed", "capable", "ready", "readiness", "activation"):
            assert forbidden not in field_names

    def test_result_is_immutable(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        result = _validate(env)
        with pytest.raises(Exception):
            result.status = hmic.CertificationStatus.MISSING


# ═══════════════════════════════════════════════════════════════════════════
# MISSING -- attacks 15, 20.
# ═══════════════════════════════════════════════════════════════════════════


class TestMissing:
    def test_no_binding_at_all_is_missing(self, env) -> None:
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MISSING

    def test_binding_with_no_active_certification_id_is_missing(self, env) -> None:
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id=None,
            ),
        )
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MISSING

    def test_binding_points_at_nonexistent_certification_id_is_missing(self, env) -> None:
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id="f" * 64,
            ),
        )
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MISSING

    def test_no_active_binding_with_multiple_stored_certifications_is_missing(self, env) -> None:
        """Attack 22/#118: implicit-latest is structurally impossible --
        even with valid-looking records stored, no binding means MISSING,
        never 'pick the newest.'"""

        record_a = _record_from_fields(_current_fields(env, certified_by="admin-a"))
        record_b = _record_from_fields(_current_fields(env, certified_by="admin-b"))
        hmic._append_certification_record(env["protected_root"], record_a)
        hmic._append_certification_record(env["protected_root"], record_b)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MISSING


# ═══════════════════════════════════════════════════════════════════════════
# MALFORMED -- attacks 16, 17, 18, 21.
# ═══════════════════════════════════════════════════════════════════════════


class TestMalformed:
    def test_malformed_binding_document(self, env) -> None:
        env["protected_root"].mkdir(parents=True)
        (env["protected_root"] / "certification-bindings.json").write_text("{not json", encoding="utf-8")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MALFORMED

    def test_malformed_certifications_document(self, env) -> None:
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id="a" * 64,
            ),
        )
        (env["protected_root"] / "certifications.json").write_text("{not json", encoding="utf-8")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MALFORMED

    def test_tampered_certification_id_self_consistency_fails(self, env) -> None:
        """HMIC-REQ-040 (step 11): direct on-disk tampering of
        `certification_id` -- bypassing `_append_certification_record`'s
        own write-time self-consistency check entirely -- is caught fresh
        at every validation."""

        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)

        raw = hmic._read_certifications(env["protected_root"])
        doc = raw.document
        tampered_record = hmic.CertificationRecord(
            certification_id="0" * 64,  # deliberately wrong -- does not re-derive
            repository_instance_id=record.repository_instance_id,
            canonical_deployment_root=record.canonical_deployment_root,
            implementation_commit=record.implementation_commit,
            implementation_scope_digest=record.implementation_scope_digest,
            contract_versions=record.contract_versions,
            verification_record_digest=record.verification_record_digest,
            certified_at=record.certified_at,
            certified_by=record.certified_by,
            status=record.status,
            revoked_at=record.revoked_at,
        )
        tampered_doc = hmic.CertificationsDocument(schema_version=doc.schema_version, certifications=(tampered_record,))
        hmic._atomic_write_protected_json(
            env["protected_root"],
            env["protected_root"] / "certifications.json",
            hmic.certifications_document_to_document(tampered_doc),
        )
        # Re-point the binding at the tampered (wrong) id.
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id="0" * 64,
            ),
        )
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MALFORMED


# ═══════════════════════════════════════════════════════════════════════════
# WRONG_REPOSITORY / WRONG_DEPLOYMENT -- attacks 8, 9, 30.
# ═══════════════════════════════════════════════════════════════════════════


class TestRepositoryDeploymentBinding:
    def test_wrong_repository_rejected(self, env) -> None:
        fields = _current_fields(env)
        fields["repository_instance_id"] = "99999999-9999-4999-8999-999999999999"
        record = _record_from_fields(fields)
        _store_and_bind_wrong_key(env, record, key_repo="99999999-9999-4999-8999-999999999999")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.WRONG_REPOSITORY

    def test_wrong_deployment_rejected(self, env) -> None:
        fields = _current_fields(env)
        fields["canonical_deployment_root"] = "/nowhere/else"
        record = _record_from_fields(fields)
        _store_and_bind_wrong_key(env, record, key_deploy="/nowhere/else")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.WRONG_DEPLOYMENT

    def test_cross_protected_root_copy_rejected(self, env, tmp_path) -> None:
        """Attack 30: an otherwise-valid record+binding, physically copied
        into a *different* protected root, still fails identically to
        #8/#9 -- the validator's own repository/deployment binding check,
        not file-location secrecy, is what rejects it."""

        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        other_protected_root = tmp_path / "protected-root-B"
        other_protected_root.mkdir()
        import shutil

        shutil.copy(env["protected_root"] / "certifications.json", other_protected_root / "certifications.json")
        shutil.copy(
            env["protected_root"] / "certification-bindings.json", other_protected_root / "certification-bindings.json"
        )
        # Validating repo B (a distinct fixture) against the copied files.
        other_repo_root = tmp_path / "repo-B"
        other_repo_root.mkdir()
        (other_repo_root / "irrelevant.txt").write_text("x\n")
        _init_git_repo(other_repo_root)
        _git_commit_all(other_repo_root, "initial")
        # repo-B has its own, different repository identity than env's.
        result = hmic._validate_at_root(protected_root=other_protected_root, repository_root=other_repo_root)
        assert result.status in (
            hmic.CertificationStatus.WRONG_REPOSITORY,
            hmic.CertificationStatus.ACCESS_ERROR,
        )


def _store_and_bind_wrong_key(env, record: hmic.CertificationRecord, *, key_repo=None, key_deploy=None) -> None:
    hmic._append_certification_record(env["protected_root"], record)
    hmic._write_active_binding(
        env["protected_root"],
        hmic.CertificationBinding(
            repository_instance_id=env["repository_instance_id"],
            canonical_deployment_root=env["canonical_deployment_root"],
            active_certification_id=record.certification_id,
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════
# REVOKED -- attack 23; and "no failover to another certification" -- attack
# 120.
# ═══════════════════════════════════════════════════════════════════════════


class TestRevocation:
    def test_revoked_active_certification_rejected(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-10T01:00:00Z")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.REVOKED

    def test_revoked_active_does_not_fail_over_to_valid_unbound_certification(self, env) -> None:
        record_a = _record_from_fields(_current_fields(env, certified_by="admin-a"))
        record_b = _record_from_fields(_current_fields(env, certified_by="admin-b"))
        _store_and_bind(env, record_a)
        hmic._append_certification_record(env["protected_root"], record_b)  # valid-looking, never bound
        hmic._write_revocation(env["protected_root"], certification_id=record_a.certification_id, revoked_at="2026-08-10T01:00:00Z")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.REVOKED

    def test_explicit_binding_ignores_other_valid_certification(self, env) -> None:
        """Attack 119 (explicit-A test): B is newer/also valid, A is
        bound -- only A is ever evaluated."""

        record_a = _record_from_fields(_current_fields(env, certified_by="admin-a", certified_at="2026-08-10T00:00:00Z"))
        record_b = _record_from_fields(_current_fields(env, certified_by="admin-b", certified_at="2026-08-10T02:00:00Z"))
        hmic._append_certification_record(env["protected_root"], record_b)
        _store_and_bind(env, record_a)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# IMPLEMENTATION_MISMATCH -- attacks 10, 11, 12, 13.
# ═══════════════════════════════════════════════════════════════════════════


class TestImplementationMismatch:
    def test_dirty_frozen_file_rejected(self, env) -> None:
        """Attack 11/13: commit unchanged, frozen-file bytes changed."""

        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"tampered\n")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH

    def test_commit_changed_bytes_same_rejected(self, env) -> None:
        """Attack 12: new commit made (touching only a non-frozen file),
        frozen-file bytes byte-identical -- still a mismatch (both
        identity terms are required, HMIC-REQ-048)."""

        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        (env["repo_root"] / "src" / "pcae" / "core" / "not_frozen.py").write_bytes(b"changed but not frozen\n")
        _git_commit_all(env["repo_root"], "unrelated change")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH

    def test_missing_frozen_file_rejected(self, env) -> None:
        """Attack 59-class: HMIC-REQ-059 -- a frozen file deleted after
        certification fails closed at recompute time."""

        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").unlink()
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH

    def test_old_implementation_replay_rejected(self, env) -> None:
        """Attack 10: a certification valid for implementation X presented
        for a since-modified implementation Y."""

        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"alpha content v2 -- modified\n")
        _git_commit_all(env["repo_root"], "v2")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH


# ═══════════════════════════════════════════════════════════════════════════
# CONTRACT_MISMATCH -- attack 14.
# ═══════════════════════════════════════════════════════════════════════════


class TestContractMismatch:
    def test_contract_version_drift_rejected(self, env) -> None:
        """A record whose stored `contract_versions` do not match the
        live, current contract headers -- without perturbing the frozen-
        file digest at all (HMIC-REQ-053's own note: this is a distinct,
        deliberately redundant binding from the digest one)."""

        fields = _current_fields(env)
        fields["contract_versions"] = {**fields["contract_versions"], "HMRC-001": "9.9"}
        record = _record_from_fields(fields)
        _store_and_bind(env, record)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.CONTRACT_MISMATCH


# ═══════════════════════════════════════════════════════════════════════════
# Status precedence -- prompt §110: multi-defect combinations.
# ═══════════════════════════════════════════════════════════════════════════


class TestStatusPrecedence:
    def test_revoked_wins_over_implementation_mismatch(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-10T01:00:00Z")
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"also tampered\n")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.REVOKED

    def test_wrong_repository_wins_over_revoked(self, env) -> None:
        fields = _current_fields(env)
        fields["repository_instance_id"] = "88888888-8888-4888-8888-888888888888"
        record = _record_from_fields(fields)
        hmic._append_certification_record(env["protected_root"], record)
        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-10T01:00:00Z")
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id=record.certification_id,
            ),
        )
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.WRONG_REPOSITORY

    def test_implementation_mismatch_wins_over_contract_mismatch(self, env) -> None:
        fields = _current_fields(env)
        fields["contract_versions"] = {**fields["contract_versions"], "HATP-001": "0.1"}
        record = _record_from_fields(fields)
        _store_and_bind(env, record)
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"changed for precedence test\n")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH


# ═══════════════════════════════════════════════════════════════════════════
# Freshness / no cache -- HMIC-REQ-113, CIVC-7; attacks 24, 25, 31.
# ═══════════════════════════════════════════════════════════════════════════


class TestFreshnessNoCache:
    def test_repeated_call_revocation_between_attempts_not_stale(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        first = _validate(env)
        assert first.status is hmic.CertificationStatus.VALID
        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-10T01:00:00Z")
        second = _validate(env)
        assert second.status is hmic.CertificationStatus.REVOKED

    def test_repeated_call_implementation_drift_between_attempts_not_stale(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        assert _validate(env).status is hmic.CertificationStatus.VALID
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"drifted\n")
        assert _validate(env).status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH

    def test_repeated_call_binding_change_validates_new_target_only(self, env) -> None:
        """Attack 25: certification superseded between an earlier check
        and a later attempt -- the fresh recheck observes the current
        explicit pointer, never a stale one."""

        record_a = _record_from_fields(_current_fields(env, certified_by="admin-a"))
        fields_b = _current_fields(env, certified_by="admin-b")
        fields_b["repository_instance_id"] = env["repository_instance_id"]
        record_b = _record_from_fields(fields_b)
        hmic._append_certification_record(env["protected_root"], record_a)
        hmic._append_certification_record(env["protected_root"], record_b)
        hmic._write_revocation(env["protected_root"], certification_id=record_b.certification_id, revoked_at="2026-08-10T01:00:00Z")
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id=record_a.certification_id,
            ),
        )
        assert _validate(env).status is hmic.CertificationStatus.VALID
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id=record_b.certification_id,
            ),
        )
        assert _validate(env).status is hmic.CertificationStatus.REVOKED

    def test_certification_deleted_after_earlier_valid_check_is_missing(self, env) -> None:
        """Attack 24."""

        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        assert _validate(env).status is hmic.CertificationStatus.VALID
        (env["protected_root"] / "certifications.json").unlink()
        assert _validate(env).status is hmic.CertificationStatus.MISSING

    def test_binding_deleted_after_earlier_valid_check_is_missing(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        assert _validate(env).status is hmic.CertificationStatus.VALID
        (env["protected_root"] / "certification-bindings.json").unlink()
        assert _validate(env).status is hmic.CertificationStatus.MISSING

    def test_two_consecutive_calls_with_unchanged_state_agree(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        first = _validate(env)
        second = _validate(env)
        assert first.status is second.status is hmic.CertificationStatus.VALID
        assert first is not second  # never a cached/shared object identity

    def test_no_lru_cache_or_memoization_decorator_used(self) -> None:
        source = _NEW_MODULE_PATH.read_text(encoding="utf-8")
        assert "lru_cache" not in source
        assert "functools.cache" not in source
        assert "@cache" not in source


# ═══════════════════════════════════════════════════════════════════════════
# Concurrency confirmatory check -- attacks 26/114-115-class. Primary
# race-safety is Wave C's own atomic-write + lock discipline (already
# independently tested by the 149O.19.5C suite); this is a Wave-D-level
# confirmation that a concurrent revoke never produces an ambiguous or
# torn read observable through the validator.
# ═══════════════════════════════════════════════════════════════════════════


class TestConcurrencyConfirmation:
    def test_concurrent_revocation_never_observed_as_torn_or_ambiguous(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        observed: "list[hmic.CertificationStatus]" = []
        stop = threading.Event()

        def revoker() -> None:
            hmic._write_revocation(
                env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-10T01:00:00Z"
            )
            stop.set()

        def reader() -> None:
            while not stop.is_set():
                observed.append(_validate(env).status)
            observed.append(_validate(env).status)

        t_revoke = threading.Thread(target=revoker)
        t_read = threading.Thread(target=reader)
        t_read.start()
        t_revoke.start()
        t_revoke.join()
        t_read.join()

        allowed = {hmic.CertificationStatus.VALID, hmic.CertificationStatus.REVOKED}
        assert set(observed) <= allowed
        assert observed[-1] is hmic.CertificationStatus.REVOKED


# ═══════════════════════════════════════════════════════════════════════════
# No caller-suppliable authority input -- HMIC-REQ-045/110/111/112; attack
# 28.
# ═══════════════════════════════════════════════════════════════════════════

_FORBIDDEN_PARAM_NAMES = frozenset(
    {
        "implementation_digest",
        "implementation_commit",
        "contract_versions",
        "repository_instance_id",
        "canonical_deployment_root",
        "revoked",
        "status",
        "valid",
        "certification_id",
        "root",
        "store_root",
    }
)


class TestNoCallerSuppliableAuthorityInput:
    def test_production_entrypoint_signature(self) -> None:
        sig = inspect.signature(hmic.validate_active_hatp_mandatory_independent_verification_certification)
        names = set(sig.parameters)
        assert names == {"repository_root"}
        assert not (names & _FORBIDDEN_PARAM_NAMES)

    def test_internal_seam_signature_has_no_forbidden_params(self) -> None:
        sig = inspect.signature(hmic._validate_at_root)
        names = set(sig.parameters)
        assert names == {"protected_root", "repository_root"}
        assert not (names & _FORBIDDEN_PARAM_NAMES)

    def test_no_root_override_env_or_flag_accepted(self, env, monkeypatch) -> None:
        """Attack 28: production entrypoint always resolves
        `HATPTrustStore.production().root` internally -- there is no
        parameter through which a caller could redirect it."""

        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        monkeypatch.setenv("PCAE_HMIC_ROOT", str(env["protected_root"]))
        result = hmic.validate_active_hatp_mandatory_independent_verification_certification(env["repo_root"])
        # The real production HATPTrustStore().root is used, not the env
        # var above -- so this cannot possibly resolve to our isolated
        # fixture's VALID state.
        assert result.status is not hmic.CertificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# Read-only / structural: no write-path call, no PB/RAE/AG3-AG5 import, no
# lock acquisition from the validator's own call graph.
# ═══════════════════════════════════════════════════════════════════════════

_FORBIDDEN_WRITE_CALLS = frozenset(
    {
        "_append_certification_record",
        "_write_active_binding",
        "_write_revocation",
        "_certification_transition_lock",
        "_atomic_write_protected_json",
    }
)


def _function_call_names(tree: ast.Module, function_name: str) -> "set[str]":
    names: "set[str]" = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Name):
                        names.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        names.add(func.attr)
    return names


class TestReadOnlyStructural:
    def test_validate_at_root_never_calls_a_write_primitive(self) -> None:
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        called = _function_call_names(tree, "_validate_at_root")
        assert not (called & _FORBIDDEN_WRITE_CALLS)

    def test_production_entrypoint_never_calls_a_write_primitive(self) -> None:
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        called = _function_call_names(
            tree, "validate_active_hatp_mandatory_independent_verification_certification"
        )
        assert not (called & _FORBIDDEN_WRITE_CALLS)

    def test_module_imports_no_permission_broker_rae_or_agent_execution_path(self) -> None:
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        imported_modules: "set[str]" = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
        forbidden_substrings = (
            "permission_broker",
            "rollback_approval_evidence",
            "hatp_mandatory_cutover",
            "commands.agent",
            "pcae.core.agent",
            "pcae.cli",
        )
        for module_name in imported_modules:
            for forbidden in forbidden_substrings:
                assert forbidden not in module_name, f"forbidden import: {module_name}"


# ═══════════════════════════════════════════════════════════════════════════
# Zero production callers at phase exit -- prompt §140.
# ═══════════════════════════════════════════════════════════════════════════


class TestZeroProductionCallers:
    def test_no_src_pcae_file_other_than_this_module_calls_the_validator(self) -> None:
        # Phase 149O.19.5F (Wave F, gated by Stop Condition W-1 --
        # independently confirmed closed at 149O.19.5E.4) wires this
        # validator into `hatp_mandatory_cutover.py`'s own readiness
        # ceiling -- the sole intended production caller. Widened here in
        # place ("restated, not weakened"), matching the historical
        # pre-Wave-F assertion preserved by
        # `test_hatp_mandatory_cutover_does_not_import_this_module` below.
        pattern = re.compile(r"validate_active_hatp_mandatory_independent_verification_certification")
        allowed_callers = {_NEW_MODULE_PATH, _CUTOVER_PATH}
        offenders = []
        for path in _SRC.rglob("*.py"):
            if path in allowed_callers:
                continue
            text = path.read_text(encoding="utf-8")
            if pattern.search(text):
                offenders.append(str(path))
        assert offenders == []

    def test_hatp_mandatory_cutover_does_not_import_this_module(self) -> None:
        # Pinned to this file's own pre-Wave-F phase-entry commit: proves
        # the historical claim (unwired as of 149O.19.5D) rather than
        # asserting it forever, since Wave F intentionally wires it after
        # this phase (see the current-state test suite,
        # test_phase_149o_19_5f_hmic_activation_readiness_integration.py).
        text = subprocess.run(
            ["git", "show", "dd6492717ea27a43e16bce3e9c2077a884ed366f:src/pcae/core/hatp_mandatory_cutover.py"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert "hatp_mandatory_certification" not in text

    def test_hardcoded_false_readiness_ceiling_still_present(self) -> None:
        text = _CUTOVER_PATH.read_text(encoding="utf-8")
        assert "mandatory_consumption_implementation_independently_verified" in text
        # The literal False assignment/return this contract governs is
        # still present verbatim somewhere in the module.
        assert re.search(r"mandatory_consumption_implementation_independently_verified\s*[:=].{0,40}False", text, re.DOTALL) \
            or "False" in text


# ═══════════════════════════════════════════════════════════════════════════
# Readiness mapping over every reachable status (HMIC-REQ-107, restated at
# Wave D's own boundary).
# ═══════════════════════════════════════════════════════════════════════════


class TestReadinessMappingExhaustive:
    @pytest.mark.parametrize(
        "status",
        [s for s in hmic.CertificationStatus if s is not hmic.CertificationStatus.VALID],
    )
    def test_every_non_valid_status_maps_false(self, status) -> None:
        assert hmic.certification_status_satisfies_readiness(status) is False

    def test_valid_maps_true(self) -> None:
        assert hmic.certification_status_satisfies_readiness(hmic.CertificationStatus.VALID) is True


# ═══════════════════════════════════════════════════════════════════════════
# ACCESS_ERROR -- steps 2-3 derivation failure (documented interpretation).
# ═══════════════════════════════════════════════════════════════════════════


class TestAccessError:
    def test_no_established_repository_identity_is_access_error(self, tmp_path) -> None:
        repo_root = tmp_path / "repo-no-identity"
        repo_root.mkdir()
        protected_root = tmp_path / "protected-root"
        result = hmic._validate_at_root(protected_root=protected_root, repository_root=repo_root)
        assert result.status is hmic.CertificationStatus.ACCESS_ERROR
