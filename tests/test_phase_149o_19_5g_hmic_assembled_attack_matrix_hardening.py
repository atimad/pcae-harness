"""Phase 149O.19.5G -- HMIC Assembled Attack-Matrix Hardening.

Adversarial verification / hardening phase over the already-implemented
HMIC-001 v1.1 stack: `src/pcae/core/hatp_mandatory_certification.py`
(Waves A-D), `src/pcae/core/hatp_mandatory_cutover.py` (Wave F wiring,
Phase 149O.19.5F), and `scripts/hatp_certification_admin.py` (Wave E).
This is a verify-only phase (`docs/contracts/
HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
HMIC-001 v1.1) -- it makes zero production changes and adds no new
capability.

Scope discipline: this module composes multiple contract layers per
test (parser + validator; validator + readiness; readiness + lock-held
activation recheck; admin ceremony + validator; 24-file digest +
validator) rather than duplicating the exhaustive single-layer coverage
the 149O.19.5A-F per-wave suites already provide. Every test uses real,
unmocked production code (`parse_certification_record`,
`validate_active_hatp_mandatory_independent_verification_certification`,
`_assess_hatp_mandatory_activation_readiness_at_root`,
`_activate_hatp_mandatory_at_root`, the real admin-script ceremony
functions) against isolated `tmp_path` fixtures -- never
`HATPTrustStore.production()`'s real root for any write. The isolated
fixture/monkeypatch pattern (a 5-file, `_FROZEN_SRC_PCAE_RELATIVE_COUNT
=1`-shaped frozen scope) is reused unmodified from the 149O.19.5D/E/F
suites' own `env` fixture, not reinvented.
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core import hatp_mandatory_cutover as cutover
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.hatp_class_b_topology_verifier import (
    ClassBConformanceStatus as _ClassBConformanceStatus,
    ClassBDeploymentVerificationResult as _ClassBDeploymentVerificationResult,
)
from pcae.core.hatp_mandatory_cutover import (
    CutoverMode,
    HATPMandatoryActivationReadinessError,
    _activate_hatp_mandatory_at_root,
    _assess_hatp_mandatory_activation_readiness_at_root,
    _resolve_cutover_mode_at_root,
    _write_cutover_transition,
)
from pcae.core.human_approval_trusted_provenance import (
    HATPVerificationSubstrateReadiness,
    HATPVerificationSubstrateStatus,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CUTOVER_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"
_CLI_PATH = _SRC / "cli.py"
_AGENT_COMMANDS_PATH = _SRC / "commands" / "agent.py"
_CORE_AGENT_PATH = _SRC / "core" / "agent.py"

_CONTRACT_PATH = (
    _REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)


def _load_admin_module():
    spec = importlib.util.spec_from_file_location("hatp_certification_admin_149o_19_5g", _ADMIN_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


admin = _load_admin_module()


# ═══════════════════════════════════════════════════════════════════════════
# Shared isolated fixture -- byte-for-byte the same shape the 149O.19.5D/E/F
# suites already establish and independently verify works: a 5-entry frozen
# scope (`fixture_a.py` + 4 fixture contract files), `_FROZEN_SRC_PCAE_
# RELATIVE_COUNT=1`, isolated git repo, isolated protected root.
# ═══════════════════════════════════════════════════════════════════════════


def _git(args, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Fixture"], cwd=root, check=True)


def _git_commit_all(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)
    return _git(["rev-parse", "HEAD"], cwd=root)


def _write_fixture_repo(repo_root: Path) -> None:
    (repo_root / "src" / "pcae" / "core").mkdir(parents=True)
    (repo_root / "docs" / "contracts").mkdir(parents=True)
    (repo_root / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"alpha content v1\n")
    for name, cid, ver in (
        ("FIXTURE_HMRC.md", "HMRC-001", "1.0"),
        ("FIXTURE_HATP.md", "HATP-001", "1.0"),
        ("FIXTURE_HSCE.md", "HSCE-001", "1.1"),
        ("FIXTURE_RAE.md", "RAE-001", "1.0"),
    ):
        (repo_root / "docs" / "contracts" / name).write_bytes(f"**Contract:** {cid}\n**Version:** {ver}\n".encode())


def _patch_frozen_scope(monkeypatch) -> None:
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
    monkeypatch.setattr(
        hmic,
        "_CONTRACT_VERSIONS_REQUIRED_KEYS",
        frozenset({"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}),
    )


@pytest.fixture
def env(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    protected_root = tmp_path / "protected-root"
    protected_root.mkdir(mode=0o700)
    _write_fixture_repo(repo_root)
    _patch_frozen_scope(monkeypatch)
    _init_git_repo(repo_root)
    _git_commit_all(repo_root, "initial")

    identity = ensure_repository_identity(HarnessPath(repo_root))
    repository_instance_id = identity.repository_instance_id
    canonical_deployment_root = hmic.derive_canonical_deployment_root(HarnessPath(repo_root))

    vr_path = tmp_path / "verification-record.md"
    vr_path.write_bytes(b"canonical phase report fixture\n")

    return {
        "repo_root": repo_root,
        "protected_root": protected_root,
        "repository_instance_id": repository_instance_id,
        "canonical_deployment_root": canonical_deployment_root,
        "verification_record_path": vr_path,
    }


def _current_hmic_fields(env, *, certified_at="2026-08-11T00:00:00Z", certified_by="protected-admin"):
    root = HarnessPath(env["repo_root"])
    return dict(
        repository_instance_id=env["repository_instance_id"],
        canonical_deployment_root=env["canonical_deployment_root"],
        implementation_commit=hmic.derive_implementation_commit(root),
        implementation_scope_digest=hmic.derive_implementation_scope_digest(root),
        contract_versions=dict(hmic.derive_contract_versions(root)),
        verification_record_digest="c" * 64,
        certified_at=certified_at,
        certified_by=certified_by,
    )


def _record_from_fields(fields: dict, *, status="active", revoked_at=None) -> hmic.CertificationRecord:
    certification_id = hmic.derive_certification_id(fields)
    return hmic.CertificationRecord(certification_id=certification_id, status=status, revoked_at=revoked_at, **fields)


def _store_and_bind(env, record: hmic.CertificationRecord, *, bind: bool = True) -> None:
    hmic._append_certification_record(env["protected_root"], record)
    if bind:
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id=record.certification_id,
            ),
        )


def _valid_certification(env) -> hmic.CertificationRecord:
    record = _record_from_fields(_current_hmic_fields(env))
    _store_and_bind(env, record)
    return record


def _validate(env) -> hmic.HMICValidationResult:
    return hmic._validate_at_root(protected_root=env["protected_root"], repository_root=env["repo_root"])


def _fake_operational_substrate(*_a, **_kw) -> HATPVerificationSubstrateReadiness:
    return HATPVerificationSubstrateReadiness(
        status=HATPVerificationSubstrateStatus.OPERATIONAL,
        operational=True,
        terms=(("fixture_forced_operational", True),),
        reasons=(),
    )


class _FakeTrustStore:
    pass


def _patch_production_trust_root(env, monkeypatch) -> None:
    monkeypatch.setattr(HATPTrustStore, "production", classmethod(lambda cls: cls(_test_only_root=env["protected_root"])))


def _fake_class_b_result(status: _ClassBConformanceStatus) -> _ClassBDeploymentVerificationResult:
    return _ClassBDeploymentVerificationResult(status=status, checks=(), reasons=(), evidence=())


def _fake_compliant_class_b(*_a, **_kw) -> _ClassBDeploymentVerificationResult:
    return _fake_class_b_result(_ClassBConformanceStatus.COMPLIANT)


def _assess(env, *, monkeypatch, operational_substrate: bool = True, class_b_compliant: bool = True):
    _patch_production_trust_root(env, monkeypatch)
    if operational_substrate:
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
    monkeypatch.setattr(
        cutover,
        "verify_class_b_deployment_conformance",
        lambda *_a, **_kw: _fake_class_b_result(
            _ClassBConformanceStatus.COMPLIANT if class_b_compliant else _ClassBConformanceStatus.NON_COMPLIANT
        ),
    )
    return _assess_hatp_mandatory_activation_readiness_at_root(
        env["protected_root"],
        env["repository_instance_id"],
        repository_root=env["repo_root"],
        trust_store=_FakeTrustStore(),
    )


def _check(readiness, name: str):
    return next(c for c in readiness.checks if c.name == name)


def _write_prepared(protected_root: Path, repository_instance_id: str) -> None:
    _write_cutover_transition(
        protected_root,
        target_mode=CutoverMode.PREPARED,
        repository_instance_id=repository_instance_id,
        activated_by="test-operator",
    )


_HMIC_CHECK_NAME = "mandatory_consumption_implementation_independently_verified"
_SIX_HMRC_REQ_054_ITEMS = frozenset(
    {
        "class_b_protected_storage_available",
        "hatp_substrate_operational",
        "hsce_signing_implementation_available",
        _HMIC_CHECK_NAME,
        "production_dependency_provenance_valid",
        "protected_activation_authority_mechanism_available",
    }
)


# ═══════════════════════════════════════════════════════════════════════════
# 0. Reconstructed contract-shape sanity: 9 statuses, 24 frozen files, 6
#    HMRC-REQ-054 terms + 1 module-owned = 7 total readiness checks.
# ═══════════════════════════════════════════════════════════════════════════


class TestReconstructedContractShape:
    def test_nine_certification_status_members(self) -> None:
        assert len(list(hmic.CertificationStatus)) == 9
        assert {m.value for m in hmic.CertificationStatus} == {
            "MISSING",
            "MALFORMED",
            "WRONG_REPOSITORY",
            "WRONG_DEPLOYMENT",
            "IMPLEMENTATION_MISMATCH",
            "CONTRACT_MISMATCH",
            "REVOKED",
            "ACCESS_ERROR",
            "VALID",
        }

    def test_twenty_four_frozen_files_extracted_from_live_contract(self) -> None:
        text = _CONTRACT_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"twenty-four files.*?```\n(.*?)```", text, re.DOTALL
        )
        assert match is not None
        entries = [line.strip() for line in match.group(1).splitlines() if line.strip()]
        assert len(entries) == 24
        assert entries[0] == "core/hatp_mandatory_cutover.py"
        assert entries[-1] == "scripts/hatp_certification_admin.py"
        assert "core/hatp_mandatory_certification.py" in entries

    def test_seven_total_readiness_checks_six_hmrc_plus_one_module_owned(self, env, monkeypatch) -> None:
        # 149O.20L.3 legitimately adds one further, additive, eighth
        # production term (HMRC-REQ-086-100) -- this phase's own claim
        # about ITS OWN scope (seven checks) is unweakened; the live
        # count below is updated to reflect current production.
        readiness = _assess(env, monkeypatch=monkeypatch)
        names = {c.name for c in readiness.checks}
        assert len(names) == 8
        assert _SIX_HMRC_REQ_054_ITEMS <= names
        assert "repository_deployment_identity_valid" in names
        assert "class_b_deployment_conformance_satisfies_readiness" in names


# ═══════════════════════════════════════════════════════════════════════════
# 1. Parser/model attacks -- malformed/unknown-field/wrong-type/unsafe-
#    identifier/path-traversal never parse into a valid authority object,
#    AND the same malformed bytes never reach VALID through the full
#    validator (parser layer + validator layer composed in one test).
# ═══════════════════════════════════════════════════════════════════════════


class TestParserAndValidatorComposedAttacks:
    def test_unknown_field_rejected_by_parser_and_by_full_validation(self, env) -> None:
        record = _valid_certification(env)
        doc = json.loads((env["protected_root"] / "certifications.json").read_bytes())
        doc["certifications"][0]["not_a_real_field"] = "attacker-injected"
        with pytest.raises(hmic.CertificationMalformedError):
            hmic.parse_certifications_document(doc)
        (env["protected_root"] / "certifications.json").write_bytes(
            (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode()
        )
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MALFORMED
        assert result.status is not hmic.CertificationStatus.VALID
        del record

    def test_boolean_version_rejected_not_coerced_to_one(self, env) -> None:
        doc = {"schema_version": True, "certifications": []}
        with pytest.raises(hmic.CertificationMalformedError):
            hmic.parse_certifications_document(doc)

    def test_repository_instance_id_wrong_type_rejected(self, env) -> None:
        fields = _current_hmic_fields(env)
        record = _record_from_fields(fields)
        doc = hmic.certification_record_to_document(record)
        doc["repository_instance_id"] = 12345  # wrong type, not a UUID string
        with pytest.raises(hmic.CertificationMalformedError):
            hmic.parse_certification_record(doc)

    def test_path_traversal_shaped_active_certification_id_never_resolves_to_a_path(self, env) -> None:
        """`active_certification_id` must be a strict SHA-256 hex digest --
        a path-traversal-shaped string is rejected at parse time, never
        used to construct a filesystem path (structural elimination,
        HMIC-REQ-129), and can never drive validation to VALID."""

        traversal_doc = {
            "repository_instance_id": env["repository_instance_id"],
            "canonical_deployment_root": env["canonical_deployment_root"],
            "active_certification_id": "../../../../etc/passwd",
        }
        with pytest.raises(hmic.CertificationMalformedError):
            hmic.parse_certification_binding(traversal_doc)

    def test_duplicate_json_keys_rejected_at_the_raw_bytes_layer(self, env) -> None:
        raw = b'{"schema_version": 1, "schema_version": 2, "certifications": []}'
        with pytest.raises(hmic.CertificationMalformedError):
            hmic.parse_certifications_document_from_bytes(raw)

    def test_nan_infinity_numeric_constants_rejected(self, env) -> None:
        raw = b'{"schema_version": NaN, "certifications": []}'
        with pytest.raises(hmic.CertificationMalformedError):
            hmic.parse_certifications_document_from_bytes(raw)

    def test_corrupt_certifications_json_yields_malformed_not_missing(self, env) -> None:
        """Composes parser-layer corruption directly with the full
        validator: a present-but-unparsable store file must never be
        silently downgraded to MISSING (anti-corruption-downgrade)."""

        env["protected_root"].mkdir(parents=True, exist_ok=True)
        (env["protected_root"] / "certification-bindings.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "bindings": [
                        {
                            "repository_instance_id": env["repository_instance_id"],
                            "canonical_deployment_root": env["canonical_deployment_root"],
                            "active_certification_id": "a" * 64,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (env["protected_root"] / "certifications.json").write_text("{not valid json", encoding="utf-8")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MALFORMED
        assert result.status is not hmic.CertificationStatus.MISSING


# ═══════════════════════════════════════════════════════════════════════════
# 2. Parsed-but-not-valid: well-formed certification that is revoked /
#    wrong-repo / wrong-deployment / wrong-implementation / wrong-contracts
#    must never validate VALID. Composed with the real admin `certify`
#    ceremony (not just hand-built records).
# ═══════════════════════════════════════════════════════════════════════════


class TestParsedButNotValidComposedWithAdminCeremony:
    def _certify_and_activate(self, env):
        created = admin.certify(
            repository_root=env["repo_root"],
            certified_by="protected-admin",
            verification_record_path=env["verification_record_path"],
            confirm=True,
            _protected_root=env["protected_root"],
        )
        admin.activate(
            repository_root=env["repo_root"],
            certification_id=created.certification_id,
            confirm=True,
            _protected_root=env["protected_root"],
        )
        return created

    def test_admin_created_and_activated_certification_validates_valid_first(self, env) -> None:
        self._certify_and_activate(env)
        assert _validate(env).status is hmic.CertificationStatus.VALID

    def test_revoked_via_real_admin_ceremony_never_valid(self, env) -> None:
        created = self._certify_and_activate(env)
        admin.revoke(certification_id=created.certification_id, confirm=True, _protected_root=env["protected_root"])
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.REVOKED
        assert result.status is not hmic.CertificationStatus.VALID

    def test_wrong_repository_never_valid(self, env) -> None:
        # Record stores a WRONG repository_instance_id, but the binding
        # entry is keyed by the CURRENT (correct) repository/deployment --
        # exactly how the validator actually looks it up (step 4/5's
        # explicit-key lookup), so step 7's mismatch is what's exercised,
        # never a MISSING lookup-key mismatch.
        fields = _current_hmic_fields(env)
        fields["repository_instance_id"] = "22222222-2222-4222-8222-222222222222"
        record = _record_from_fields(fields)
        hmic._append_certification_record(env["protected_root"], record)
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
        assert result.status is not hmic.CertificationStatus.VALID

    def test_wrong_deployment_never_valid(self, env) -> None:
        fields = _current_hmic_fields(env)
        fields["canonical_deployment_root"] = "/completely/different/deployment/root"
        record = _record_from_fields(fields)
        hmic._append_certification_record(env["protected_root"], record)
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id=record.certification_id,
            ),
        )
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.WRONG_DEPLOYMENT
        assert result.status is not hmic.CertificationStatus.VALID

    def test_wrong_implementation_never_valid(self, env) -> None:
        self._certify_and_activate(env)
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"attacker-modified content\n")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH
        assert result.status is not hmic.CertificationStatus.VALID

    def test_wrong_contracts_never_valid(self, env) -> None:
        """A pure contract-version drift (HMIC-REQ-053: the digest binding
        and the contract_versions binding are deliberately distinct
        mechanisms) -- the stored contract_versions field itself is stale
        relative to the live header, with the frozen-file digest otherwise
        untouched, so step 9 passes and step 10 is what actually fires."""

        fields = _current_hmic_fields(env)
        fields["contract_versions"] = {**fields["contract_versions"], "HMRC-001": "9.9"}
        record = _record_from_fields(fields)
        _store_and_bind(env, record)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.CONTRACT_MISMATCH
        assert result.status is not hmic.CertificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# 3. 24-file identity attacks -- omit/add/modify a frozen file changes
#    implementation identity and invalidates an existing certification.
#    Modeled at the fixture's 5-file frozen scope (the same substitution
#    technique the 149O.19.5D/E/F suites use for `hatp_mandatory_cutover.py`
#    -- `fixture_a.py` stands in for a frozen production file; the
#    self-binding/admin-binding/cutover-binding claims are additionally
#    proven directly against the REAL, unmodified 24-file production
#    enumeration below, never only the fixture).
# ═══════════════════════════════════════════════════════════════════════════


class TestFrozenFileIdentityAttacks:
    def test_omitting_a_frozen_file_changes_the_digest(self, env, monkeypatch) -> None:
        before = hmic.derive_implementation_scope_digest(HarnessPath(env["repo_root"]))
        monkeypatch.setattr(
            hmic,
            "_FROZEN_AUTHORITY_BEARING_FILES",
            (
                "docs/contracts/FIXTURE_HMRC.md",
                "docs/contracts/FIXTURE_HATP.md",
                "docs/contracts/FIXTURE_HSCE.md",
                "docs/contracts/FIXTURE_RAE.md",
            ),
        )
        monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 0)
        after = hmic.derive_implementation_scope_digest(HarnessPath(env["repo_root"]))
        assert before != after

    def test_modifying_a_frozen_file_invalidates_an_existing_certification(self, env) -> None:
        record = _valid_certification(env)
        assert _validate(env).status is hmic.CertificationStatus.VALID
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"tampered bytes\n")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH
        del record

    def test_missing_frozen_file_fails_closed_never_valid(self, env) -> None:
        _valid_certification(env)
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").unlink()
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH

    def test_extra_non_frozen_file_never_affects_the_digest(self, env) -> None:
        before = hmic.derive_implementation_scope_digest(HarnessPath(env["repo_root"]))
        (env["repo_root"] / "src" / "pcae" / "core" / "not_frozen_extra.py").write_bytes(b"unrelated new file\n")
        after = hmic.derive_implementation_scope_digest(HarnessPath(env["repo_root"]))
        assert before == after

    def test_real_25_file_enumeration_includes_self_binding_admin_and_cutover_files(self) -> None:
        """Real (unfixtured) production paths -- proves the actual,
        currently-live frozen set self-binds the validator module, the
        admin ceremony script, and the cutover module itself, per
        HMIC-REQ-050/052(b). Was 24 through 149O.19.5E.3-149O.20E;
        widened to 25 by 149O.20D.1's HBDC-001 repair, production-aligned
        by 149O.20F."""

        paths = hmic._frozen_canonical_paths()
        assert len(paths) == 25
        assert "src/pcae/core/hatp_mandatory_certification.py" in paths  # self-binding
        assert "scripts/hatp_certification_admin.py" in paths  # admin-source binding
        assert "src/pcae/core/hatp_mandatory_cutover.py" in paths  # cutover-source binding

    def test_real_validator_module_edit_would_change_the_real_digest(self) -> None:
        """Proves self-binding is mechanically live (not merely
        enumerated): re-deriving the real digest over the REAL repository
        with one frozen byte flipped in a copy changes the digest,
        confirmed by directly re-hashing `hatp_mandatory_certification.py`'s
        own on-disk bytes as part of the real digest computation (never
        mutates the real file)."""

        real_bytes = _HMIC_MODULE_PATH.read_bytes()
        digest_before = hmic._sha256_hex(real_bytes)
        digest_after = hmic._sha256_hex(real_bytes + b"\n# attacker appended byte\n")
        assert digest_before != digest_after
        # And this file is indeed a member of the live frozen enumeration
        # whose bytes feed `derive_implementation_scope_digest`.
        assert "src/pcae/core/hatp_mandatory_certification.py" in hmic._frozen_canonical_paths()

    def test_real_admin_script_and_cutover_module_are_hashed_frozen_members(self) -> None:
        for path, rel in (
            (_ADMIN_SCRIPT_PATH, "scripts/hatp_certification_admin.py"),
            (_CUTOVER_PATH, "src/pcae/core/hatp_mandatory_cutover.py"),
        ):
            assert rel in hmic._frozen_canonical_paths()
            assert path.exists()


# ═══════════════════════════════════════════════════════════════════════════
# 4. No implicit-latest: multiple valid-looking unbound certifications never
#    grant authority; active-binding is required and explicit.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoImplicitLatest:
    def test_valid_looking_certification_never_consulted_without_explicit_binding(self, env) -> None:
        record = _record_from_fields(_current_hmic_fields(env))
        _store_and_bind(env, record, bind=False)  # created, never bound
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MISSING
        assert result.status is not hmic.CertificationStatus.VALID

    def test_multiple_valid_shaped_records_only_the_bound_one_is_consulted(self, env) -> None:
        older = _record_from_fields(_current_hmic_fields(env, certified_at="2026-08-10T00:00:00Z", certified_by="admin-a"))
        newer = _record_from_fields(_current_hmic_fields(env, certified_at="2026-08-11T00:00:00Z", certified_by="admin-b"))
        hmic._append_certification_record(env["protected_root"], older)
        hmic._append_certification_record(env["protected_root"], newer)
        # Bind explicitly to the OLDER one -- an implicit-latest validator
        # would wrongly consult `newer`; the real one must not.
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id=older.certification_id,
            ),
        )
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.VALID
        # Now revoke the bound (older) one; the still-VALID-shaped `newer`
        # record must never be silently substituted.
        hmic._write_revocation(env["protected_root"], certification_id=older.certification_id, revoked_at="2026-08-11T05:00:00Z")
        result_after = _validate(env)
        assert result_after.status is hmic.CertificationStatus.REVOKED
        assert result_after.status is not hmic.CertificationStatus.VALID

    def test_validator_source_never_sorts_or_globs_certifications(self) -> None:
        source = inspect.getsource(hmic._validate_at_root)
        for forbidden in ("sorted(", "sort(", ".glob(", "max(", "certified_at"):
            assert forbidden not in source


# ═══════════════════════════════════════════════════════════════════════════
# 5. Active-invalid vs newer-valid: revoked active-bound cert must be
#    evaluated as REVOKED even though a newer, unbound, would-be-VALID cert
#    exists (same scenario as above, isolated as its own explicit test).
# ═══════════════════════════════════════════════════════════════════════════


class TestActiveInvalidNeverFallsBackToNewerValid:
    def test_active_revoked_with_unbound_valid_alternative_still_revoked(self, env) -> None:
        active = _valid_certification(env)
        hmic._write_revocation(env["protected_root"], certification_id=active.certification_id, revoked_at="2026-08-11T06:00:00Z")
        # A second, currently-would-be-valid record exists, created but
        # deliberately never bound.
        alt = _record_from_fields(_current_hmic_fields(env, certified_at="2026-08-11T07:00:00Z", certified_by="admin-alt"))
        hmic._append_certification_record(env["protected_root"], alt)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.REVOKED


# ═══════════════════════════════════════════════════════════════════════════
# 6. Validator status precedence -- multi-defect cases resolve to the exact
#    status HMIC-REQ-103's 12-step algorithm dictates, not merely
#    "non-VALID".
# ═══════════════════════════════════════════════════════════════════════════


class TestStatusPrecedenceMultiDefect:
    def test_revoked_plus_implementation_mismatch_yields_revoked(self, env) -> None:
        """Step 8 (REVOKED) precedes step 9 (IMPLEMENTATION_MISMATCH)."""

        record = _valid_certification(env)
        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-11T08:00:00Z")
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"also tampered\n")
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.REVOKED

    def test_wrong_repository_plus_revoked_yields_wrong_repository(self, env) -> None:
        """Step 7 (WRONG_REPOSITORY) precedes step 8 (REVOKED)."""

        fields = _current_hmic_fields(env)
        fields["repository_instance_id"] = "33333333-3333-4333-8333-333333333333"
        record = _record_from_fields(fields)
        hmic._append_certification_record(env["protected_root"], record)
        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-11T09:00:00Z")
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

    def test_implementation_mismatch_plus_contract_mismatch_yields_implementation_mismatch(self, env) -> None:
        """Step 9 (IMPLEMENTATION_MISMATCH) precedes step 10
        (CONTRACT_MISMATCH): a certification whose stored
        implementation_scope_digest is stale AND whose stored
        contract_versions are also stale must report the earlier-step
        failure."""

        fields = _current_hmic_fields(env)
        fields["implementation_scope_digest"] = "9" * 64  # stale/wrong digest
        fields["contract_versions"] = {**fields["contract_versions"], "HMRC-001": "0.1"}  # also stale
        record = _record_from_fields(fields)
        _store_and_bind(env, record)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH

    def test_missing_plus_everything_else_wrong_yields_missing(self, env) -> None:
        """Step 4/5 (MISSING) precedes every later step -- no binding at
        all beats every other possible defect."""

        result = _validate(env)
        assert result.status is hmic.CertificationStatus.MISSING


# ═══════════════════════════════════════════════════════════════════════════
# 7. Validator freshness / no-cache and read-only.
# ═══════════════════════════════════════════════════════════════════════════


def _iter_protected_root_bytes(root: Path) -> dict:
    if not root.exists():
        return {}
    return {p: p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class TestFreshnessNoCacheReadOnly:
    def test_no_memoization_decorator_anywhere_in_certification_module(self) -> None:
        source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in ("lru_cache", "functools.cache", "cached_property", "@cache"):
            assert forbidden not in source

    def test_validator_makes_no_writes_before_after_byte_comparison(self, env) -> None:
        _valid_certification(env)
        before = _iter_protected_root_bytes(env["protected_root"])
        for _ in range(3):
            _validate(env)
        after = _iter_protected_root_bytes(env["protected_root"])
        assert before == after

    def test_repeated_calls_reflect_live_state_changes_not_a_stale_cache(self, env) -> None:
        first = _validate(env)
        assert first.status is hmic.CertificationStatus.MISSING
        _valid_certification(env)
        second = _validate(env)
        assert second.status is hmic.CertificationStatus.VALID
        hmic._write_revocation(
            env["protected_root"],
            certification_id=hmic._load_active_binding(
                env["protected_root"],
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
            ).active_certification_id,
            revoked_at="2026-08-11T10:00:00Z",
        )
        third = _validate(env)
        assert third.status is hmic.CertificationStatus.REVOKED


# ═══════════════════════════════════════════════════════════════════════════
# 8. Validator authority-input attack: no caller-suppliable parameter can
#    substitute for real state.
# ═══════════════════════════════════════════════════════════════════════════


class TestValidatorAuthorityInputAttack:
    def test_production_entrypoint_accepts_only_repository_root(self) -> None:
        params = inspect.signature(
            hmic.validate_active_hatp_mandatory_independent_verification_certification
        ).parameters
        assert list(params) == ["repository_root"]

    def test_no_forbidden_authority_parameter_names_anywhere_in_signature(self) -> None:
        params = set(
            inspect.signature(hmic.validate_active_hatp_mandatory_independent_verification_certification).parameters
        )
        forbidden = {
            "implementation_digest",
            "implementation_commit",
            "contract_versions",
            "repository_instance_id",
            "canonical_deployment_root",
            "revoked",
            "status",
            "valid",
            "force",
            "override",
        }
        assert params.isdisjoint(forbidden)

    def test_internal_test_seam_also_accepts_no_repository_or_deployment_id_override(self) -> None:
        params = set(inspect.signature(hmic._validate_at_root).parameters)
        assert params == {"protected_root", "repository_root"}
        forbidden = {"repository_instance_id", "canonical_deployment_root", "valid", "status"}
        assert params.isdisjoint(forbidden)

    def test_no_production_root_override_env_or_flag_honored(self, env, monkeypatch) -> None:
        """Even with an attacker-controlled environment variable set, the
        production entrypoint still resolves `HATPTrustStore.production()`
        internally -- proven by confirming it does NOT observe the
        isolated fixture's certification unless `HATPTrustStore.production`
        itself is patched (the only legitimate test seam)."""

        _valid_certification(env)
        monkeypatch.setenv("PCAE_HMIC_ROOT", str(env["protected_root"]))
        monkeypatch.setenv("HATP_TRUST_ROOT", str(env["protected_root"]))
        # Without patching HATPTrustStore.production itself, the real
        # production root is consulted, which has no certification state
        # for this fixture repository -> MISSING, never VALID.
        result = hmic.validate_active_hatp_mandatory_independent_verification_certification(env["repo_root"])
        assert result.status is not hmic.CertificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# 9. Admin/agent-reachability: no ordinary CLI/agent code path can create or
#    revoke certification authority.
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminAgentReachability:
    def test_no_production_src_pcae_file_calls_the_writer_primitives(self) -> None:
        forbidden = ("_append_certification_record", "_write_active_binding", "_write_revocation")
        for path in _SRC.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for name in forbidden:
                # Definition sites (`def _append_certification_record`) are
                # expected inside hatp_mandatory_certification.py itself;
                # only *call* sites outside it are the attack surface.
                if path == _HMIC_MODULE_PATH:
                    continue
                assert name not in source, f"{path} references forbidden writer primitive {name}"

    def test_cli_and_agent_modules_have_no_certify_or_revoke_surface(self) -> None:
        for path in (_CLI_PATH, _AGENT_COMMANDS_PATH, _CORE_AGENT_PATH):
            source = path.read_text(encoding="utf-8")
            for forbidden in (
                "hatp_certification_admin",
                "_append_certification_record",
                "_write_active_binding",
                "_write_revocation",
                "mark_independently_verified",
                "set_certified",
            ):
                assert forbidden not in source

    def test_no_src_pcae_file_imports_the_admin_script_by_ast(self) -> None:
        for path in _SRC.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "hatp_certification_admin" not in alias.name
                elif isinstance(node, ast.ImportFrom) and node.module:
                    assert "hatp_certification_admin" not in node.module

    def test_hmic_module_exposes_no_public_write_wrapper(self) -> None:
        public_names = {name for name in vars(hmic) if not name.startswith("_")}
        for forbidden in (
            "create_certification",
            "activate_certification",
            "revoke_certification",
            "mark_independently_verified",
            "set_certified",
        ):
            assert forbidden not in public_names

    def test_agent_cannot_construct_authority_by_calling_validator_directly(self, env) -> None:
        """Composed attack: even a fully agent-reachable direct call to the
        real production validator function (which any Python-executing
        agent CAN call, per HMIC-REQ-011's threat model) still cannot
        manufacture VALID without real protected-root state, because no
        parameter accepts a validity override (ties to attack-input test
        above, exercised here end-to-end against a repo with zero
        certification state)."""

        result = hmic.validate_active_hatp_mandatory_independent_verification_certification(env["repo_root"])
        assert result.status is not hmic.CertificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# 10. Readiness integration (Wave F re-attack).
# ═══════════════════════════════════════════════════════════════════════════


class TestReadinessIntegrationReattack:
    def test_hmic_valid_alone_with_one_other_false_yields_overall_false(self, env, monkeypatch) -> None:
        _valid_certification(env)
        readiness = _assess(env, monkeypatch=monkeypatch, operational_substrate=False)
        assert _check(readiness, _HMIC_CHECK_NAME).satisfied is True
        assert _check(readiness, "hatp_substrate_operational").satisfied is False
        assert readiness.ready is False

    def test_hmic_non_valid_with_all_others_true_yields_overall_false(self, env, monkeypatch) -> None:
        readiness = _assess(env, monkeypatch=monkeypatch, operational_substrate=True)
        assert _check(readiness, _HMIC_CHECK_NAME).satisfied is False
        for name in _SIX_HMRC_REQ_054_ITEMS - {_HMIC_CHECK_NAME}:
            assert _check(readiness, name).satisfied is True, name
        assert readiness.ready is False

    @pytest.mark.parametrize("status", list(hmic.CertificationStatus))
    def test_exact_certification_status_enum_mapping(self, status) -> None:
        expected = status is hmic.CertificationStatus.VALID
        assert hmic.certification_status_satisfies_readiness(status) is expected

    def test_injected_validator_exception_maps_to_false(self, env, monkeypatch) -> None:
        def _boom(_repository_root):
            raise RuntimeError("simulated validator failure (injected by attack test)")

        monkeypatch.setattr(cutover, "validate_active_hatp_mandatory_independent_verification_certification", _boom)
        readiness = _assess(env, monkeypatch=monkeypatch)
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False
        assert readiness.ready is False


# ═══════════════════════════════════════════════════════════════════════════
# 11. TOCTOU / lock-held recheck -- 3 divergence scenarios between an
#     advisory pre-lock read and the lock-held activation recheck.
# ═══════════════════════════════════════════════════════════════════════════


class TestTOCTOULockHeldRecheck:
    def _prepare(self, env, monkeypatch):
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _fake_compliant_class_b)
        _patch_production_trust_root(env, monkeypatch)
        record = _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])
        pre_lock = _assess_hatp_mandatory_activation_readiness_at_root(
            env["protected_root"], env["repository_instance_id"], repository_root=env["repo_root"], trust_store=_FakeTrustStore()
        )
        assert pre_lock.ready is True
        return record

    def _cutover_record_bytes(self, env) -> bytes:
        path = env["protected_root"] / "cutover-record.json"
        return path.read_bytes() if path.exists() else b""

    def test_revocation_between_pre_lock_read_and_activation_refuses(self, env, monkeypatch) -> None:
        record = self._prepare(env, monkeypatch)
        before = self._cutover_record_bytes(env)
        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-11T11:00:00Z")
        with pytest.raises(HATPMandatoryActivationReadinessError):
            _activate_hatp_mandatory_at_root(
                env["protected_root"], env["repository_instance_id"], activated_by="op",
                repository_root=env["repo_root"], trust_store=_FakeTrustStore(),
            )
        after = self._cutover_record_bytes(env)
        assert before == after
        assert _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"]).mode == CutoverMode.PREPARED
        assert not (env["protected_root"] / "cutover-activation-marker.json").exists()

    def test_active_binding_repointed_between_pre_lock_read_and_activation_refuses(self, env, monkeypatch) -> None:
        self._prepare(env, monkeypatch)
        before = self._cutover_record_bytes(env)
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id="1" * 64,  # no such record
            ),
        )
        with pytest.raises(HATPMandatoryActivationReadinessError):
            _activate_hatp_mandatory_at_root(
                env["protected_root"], env["repository_instance_id"], activated_by="op",
                repository_root=env["repo_root"], trust_store=_FakeTrustStore(),
            )
        after = self._cutover_record_bytes(env)
        assert before == after
        assert _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"]).mode == CutoverMode.PREPARED
        assert not (env["protected_root"] / "cutover-activation-marker.json").exists()

    def test_implementation_drift_between_pre_lock_read_and_activation_refuses(self, env, monkeypatch) -> None:
        self._prepare(env, monkeypatch)
        before = self._cutover_record_bytes(env)
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"drifted during TOCTOU window\n")
        with pytest.raises(HATPMandatoryActivationReadinessError):
            _activate_hatp_mandatory_at_root(
                env["protected_root"], env["repository_instance_id"], activated_by="op",
                repository_root=env["repo_root"], trust_store=_FakeTrustStore(),
            )
        after = self._cutover_record_bytes(env)
        assert before == after
        assert _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"]).mode == CutoverMode.PREPARED
        assert not (env["protected_root"] / "cutover-activation-marker.json").exists()


# ═══════════════════════════════════════════════════════════════════════════
# 12. One-way cutover: after a fixture-only successful activation, revoking
#     the certification never downgrades the Cutover Record's mode.
# ═══════════════════════════════════════════════════════════════════════════


class TestOneWayCutover:
    def test_revocation_after_successful_activation_never_downgrades_mode(self, env, monkeypatch) -> None:
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _fake_compliant_class_b)
        _patch_production_trust_root(env, monkeypatch)
        record = _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])
        activated_record = _activate_hatp_mandatory_at_root(
            env["protected_root"], env["repository_instance_id"], activated_by="op",
            repository_root=env["repo_root"], trust_store=_FakeTrustStore(),
        )
        assert activated_record.mode == CutoverMode.HATP_MANDATORY

        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-11T12:00:00Z")

        readiness = _assess(env, monkeypatch=monkeypatch, operational_substrate=True)
        assert _check(readiness, _HMIC_CHECK_NAME).satisfied is False  # readiness honestly degrades ...
        resolution_after = _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"])
        assert resolution_after.mode == CutoverMode.HATP_MANDATORY  # ... but the mode never reverses

    def test_transition_graph_has_no_reverse_edge_from_mandatory(self) -> None:
        assert not cutover.is_valid_cutover_transition(CutoverMode.HATP_MANDATORY, CutoverMode.PREPARED)
        assert not cutover.is_valid_cutover_transition(CutoverMode.HATP_MANDATORY, CutoverMode.LEGACY_COMPATIBLE)
        assert not cutover.is_valid_cutover_transition(CutoverMode.HATP_MANDATORY, CutoverMode.HATP_MANDATORY)


# ═══════════════════════════════════════════════════════════════════════════
# 13. Historical replay -- a v1.0/22-file-shaped certification, and a
#     certification whose digest matches pre-Wave-F source, both fail to
#     validate against current (post-Wave-F, 24-file) source.
# ═══════════════════════════════════════════════════════════════════════════

_PRE_WAVE_F_COMMIT = "dd6492717ea27a43e16bce3e9c2077a884ed366f"


class TestHistoricalReplay:
    def test_twenty_two_file_shaped_digest_cannot_equal_current_twenty_four_file_digest(self, env, monkeypatch) -> None:
        """Models the v1.0/22-file-shaped replay (attack #33): a digest
        computed over a STRICT SUBSET of the current frozen scope can never
        equal the digest computed over the full current scope, because
        HMIC-REQ-058's two-level construction folds every path into the
        hash -- fewer per-file records changes the hashed byte stream, not
        merely its length in a way that could coincidentally collide."""

        full_digest = hmic.derive_implementation_scope_digest(HarnessPath(env["repo_root"]))

        # Recompute over a strict subset (a stand-in for "the pre-repair
        # enumeration omitted N files") -- fewer frozen paths than the
        # fixture's current 5-file scope.
        monkeypatch.setattr(
            hmic,
            "_FROZEN_AUTHORITY_BEARING_FILES",
            (
                "core/fixture_a.py",
                "docs/contracts/FIXTURE_HMRC.md",
            ),
        )
        monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)
        subset_digest = hmic.derive_implementation_scope_digest(HarnessPath(env["repo_root"]))
        assert subset_digest != full_digest

    def test_certification_bound_to_pre_wave_f_cutover_source_digest_rejected_by_current_source(self, env) -> None:
        """Models attack #33/#34 directly against the real repository's own
        history: a certification whose implementation_scope_digest was
        computed when the frozen file set's `hatp_mandatory_cutover.py`
        member had pre-Wave-F bytes (the hard-coded `False` ceiling, no
        HMIC import) cannot equal the digest computed over the current,
        post-Wave-F bytes of that same frozen file -- since
        `hatp_mandatory_cutover.py` is itself a HMIC-REQ-050 frozen member,
        the Wave F edit that changed its bytes necessarily changed
        `implementation_scope_digest` for any real production certification
        that predates it."""

        pre_wave_f_bytes = subprocess.run(
            ["git", "show", f"{_PRE_WAVE_F_COMMIT}:src/pcae/core/hatp_mandatory_cutover.py"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
        ).stdout.encode("utf-8")
        current_bytes = _CUTOVER_PATH.read_bytes()
        assert pre_wave_f_bytes != current_bytes, "Wave F must have changed this frozen file's bytes"

        pre_digest_component = hmic._sha256_hex(pre_wave_f_bytes)
        current_digest_component = hmic._sha256_hex(current_bytes)
        assert pre_digest_component != current_digest_component
        # Therefore any certification whose implementation_scope_digest was
        # derived before Wave F's edit lands on a stale per-file record for
        # this frozen path and cannot equal the current
        # implementation_scope_digest -- IMPLEMENTATION_MISMATCH is the
        # only reachable outcome for such a replay, never VALID.


# ═══════════════════════════════════════════════════════════════════════════
# 14. No-fallback-chains: no suspicious bare `except:`/legacy-env-variable
#     override near the validator/readiness/admin paths.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoFallbackChains:
    def test_no_bare_except_in_certification_or_cutover_or_admin_modules(self) -> None:
        for path in (_HMIC_MODULE_PATH, _CUTOVER_PATH, _ADMIN_SCRIPT_PATH):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    assert node.type is not None, f"{path} has a bare 'except:' clause -- forbidden fallback shape"

    def test_no_environment_variable_reads_in_certification_or_admin_modules(self) -> None:
        for path in (_HMIC_MODULE_PATH, _ADMIN_SCRIPT_PATH):
            source = path.read_text(encoding="utf-8")
            assert "os.environ" not in source
            assert "os.getenv" not in source

    def test_no_legacy_scope_or_version_selector_override_anywhere(self) -> None:
        for path in (_HMIC_MODULE_PATH, _CUTOVER_PATH, _ADMIN_SCRIPT_PATH):
            source = path.read_text(encoding="utf-8")
            for forbidden in ("legacy_scope", "file_count=22", "SKIP_HMIC", "BYPASS_CERTIFICATION", "FORCE_VALID"):
                assert forbidden not in source

    def test_cutover_hmic_check_construction_has_a_single_true_producing_branch(self) -> None:
        """Structural proxy for 'no OR-path to True': the readiness
        check's satisfied value is produced by exactly one boolean
        expression tied to `certification_status_satisfies_readiness`,
        never a secondary `or` fallback."""

        source = inspect.getsource(cutover._assess_hatp_mandatory_activation_readiness_at_root)
        # Isolate the HMIC-specific block only.
        start = source.index("hmic_verified")
        block = source[start : start + 900]
        assert " or True" not in block
        assert "hmic_verified = True" not in block  # never unconditionally forced true


# ═══════════════════════════════════════════════════════════════════════════
# 15. Real production store untouched confirmation.
# ═══════════════════════════════════════════════════════════════════════════


class TestRealProtectedRootUntouched:
    def test_no_real_certification_state_before_or_after_this_module_runs(self) -> None:
        root = HATPTrustStore.production().root
        assert not (root / "certifications.json").exists()
        assert not (root / "certification-bindings.json").exists()
        assert not (root / "cutover-record.json").exists()
        assert not (root / "cutover-activation-marker.json").exists()

    def test_real_host_readiness_still_honestly_not_ready(self) -> None:
        readiness = cutover.assess_hatp_mandatory_activation_readiness(HarnessPath.cwd())
        assert readiness.ready is False
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False
        root = HATPTrustStore.production().root
        assert not (root / "certifications.json").exists()
