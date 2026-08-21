"""Phase 149O.20L.7O.2M.1 -- HMIC v1.7 Trust-Enrollment Admin Entry-Point
Source-Scope Evolution INDEPENDENT VERIFICATION.

Freshly-authored test suite (not copied from 149O.20L.7O.2M's own
tests) re-deriving, from primary source only, the claims made by Phase
149O.20L.7O.2M: HMIC-001 v1.6 -> v1.7, frozen authority-bearing file set
36 -> 38 (exact delta: scripts/hatp_hardware_credential_admin.py,
scripts/hatp_principal_signer_admin.py), contract identity remains
exactly seven, CertificationRecord.contract_versions remains exactly
seven keys.

VERIFICATION ONLY. No real hac-dell connection, no FIDO2/PIV hardware
touch, no CertificationRecord/Principal/Signer/DeploymentBinding
creation against the real protected root, no HATP activation change.
All CertificationRecord/validator exercises below use fully isolated,
disposable `tmp_path` fixture repositories and fixture protected roots
-- mirroring the 149O.19.5D suite's own `env` fixture pattern -- never
this repository's own real frozen files and never `HATPTrustStore.
production().root`.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_PRE_2M_CHECKPOINT = "fd782695c90a8d6ac4e6dd6f985aaf3a9540101a"  # true pre-2M phase-entry commit


def _git(args, cwd=_REPO_ROOT):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


# ═══════════════════════════════════════════════════════════════════════
# §11-14: exact membership, contract vs production vs derived, exact delta
# ═══════════════════════════════════════════════════════════════════════

_EXPECTED_38 = (
    "core/hatp_mandatory_cutover.py", "core/hatp_ag_authority.py",
    "core/hatp_rollback_consumption.py", "core/hatp_bootstrap.py",
    "core/human_approval_trusted_provenance.py", "core/repository_identity.py",
    "core/rollback_approval_evidence.py", "core/hatp_evidence_store.py",
    "core/hatp_signed_evidence.py", "core/agent.py", "commands/agent.py",
    "cli.py", "core/permission_broker.py", "core/permission_broker_foundation.py",
    "core/hatp_providers.py", "core/hatp_fido2_provider.py", "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py", "core/hatp_mandatory_certification.py",
    "core/hatp_class_b_topology_verifier.py", "core/hatp_environment_lock_verifier.py",
    "core/hatp_class_b_conformance.py", "core/hatp_deployment_binding_admin.py",
    "core/hatp_signing_ceremony.py", "core/hatp_hardware_credential_admin.py",
    "core/hatp_principal_signer_admin.py", "core/paths.py",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
    "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
    "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
    "scripts/hatp_certification_admin.py", "scripts/hatp_deployment_binding_admin.py",
    "scripts/hatp_hardware_credential_admin.py", "scripts/hatp_principal_signer_admin.py",
)


def test_current_contract_text_enumerates_exactly_these_38_paths_in_order():
    text = _CONTRACT_PATH.read_text(encoding="utf-8")
    fence_start = text.index("```\ncore/hatp_mandatory_cutover.py")
    fence_end = text.index("```", fence_start + 3)
    block = text[fence_start + 4 : fence_end]
    lines = [ln.strip().split()[0] for ln in block.splitlines() if ln.strip()]
    assert tuple(lines) == _EXPECTED_38
    assert len(lines) == 38


def test_production_constants_match_contract_exactly():
    assert hmic._FROZEN_AUTHORITY_BEARING_FILES == _EXPECTED_38
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 38


def test_derived_runtime_membership_matches_contract_and_production():
    derived = hmic._frozen_canonical_paths()
    expected_canonical = sorted(
        (f"src/pcae/{p}" if p in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES else p) for p in _EXPECTED_38
    )
    assert sorted(derived) == expected_canonical
    assert len(derived) == 38


def test_pre_2m_checkpoint_had_exactly_36_and_lacked_both_new_scripts():
    text = _git(["show", f"{_PRE_2M_CHECKPOINT}:src/pcae/core/hatp_mandatory_certification.py"])
    assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36" in text
    assert "scripts/hatp_hardware_credential_admin.py" not in text
    assert "scripts/hatp_principal_signer_admin.py" not in text
    contract_text = _git(
        ["show", f"{_PRE_2M_CHECKPOINT}:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"]
    )
    assert "**Version:** 1.6" in contract_text


def test_exact_delta_is_addition_of_the_two_scripts_only_nothing_else():
    pre_text = _git(["show", f"{_PRE_2M_CHECKPOINT}:src/pcae/core/hatp_mandatory_certification.py"])
    pre_members = set()
    for line in pre_text.splitlines():
        s = line.strip().strip('",')
        if s.startswith('"') and s.endswith('"'):
            pre_members.add(s.strip('"'))
    # crude but sufficient: use production module's own pre-2M tuple sources instead
    # (direct AST-safe re-derivation)
    import ast

    tree = ast.parse(pre_text)
    pre_set = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_FROZEN_AUTHORITY_BEARING_FILES":
                    pass
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in ("_FROZEN_SRC_PCAE_RELATIVE_FILES", "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"):
                values = ast.literal_eval(node.value)
                if pre_set is None:
                    pre_set = set(values)
                else:
                    pre_set |= set(values)
    assert pre_set is not None
    assert len(pre_set) == 36
    current_set = set(hmic._FROZEN_AUTHORITY_BEARING_FILES)
    added = current_set - pre_set
    removed = pre_set - current_set
    assert added == {"scripts/hatp_hardware_credential_admin.py", "scripts/hatp_principal_signer_admin.py"}
    assert removed == set()


def test_both_new_members_are_repository_root_relative_not_src_pcae_relative():
    assert "scripts/hatp_hardware_credential_admin.py" in hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
    assert "scripts/hatp_principal_signer_admin.py" in hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
    assert "scripts/hatp_hardware_credential_admin.py" not in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES
    assert "scripts/hatp_principal_signer_admin.py" not in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES
    assert len(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES) == 27
    assert len(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 11


# ═══════════════════════════════════════════════════════════════════════
# §5: version bump consistency
# ═══════════════════════════════════════════════════════════════════════

def test_current_hmic_version_header_is_1_7():
    text = _CONTRACT_PATH.read_text(encoding="utf-8")
    assert text.splitlines()[3].strip() == "**Version:** 1.7"


# ═══════════════════════════════════════════════════════════════════════
# §8/§9: digest non-participation (pre-2M) / participation (current) --
# proven live in the phase's own bash investigation using disposable
# worktrees; re-asserted here structurally via membership (a digest
# derived purely as a hash over exactly the frozen-set files cannot be
# affected by a file outside that set, and must be affected by a file
# inside it, given non-degenerate file content -- this is a property of
# `derive_implementation_scope_digest`'s own construction, checked here
# against THIS repository's current, real (already-bound) membership
# using synthetic fixture content only, never real repo files).
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def fixture_env(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    protected_root = tmp_path / "protected-root"
    (repo_root / "src" / "pcae" / "core").mkdir(parents=True)
    (repo_root / "docs" / "contracts").mkdir(parents=True)
    (repo_root / "scripts").mkdir(parents=True)

    (repo_root / "src" / "pcae" / "core" / "fixture_core.py").write_bytes(b"core content v1\n")
    (repo_root / "scripts" / "fixture_admin.py").write_bytes(b"admin content v1\n")
    (repo_root / "scripts" / "not_bound_admin.py").write_bytes(b"unbound content v1\n")
    for name, cid, ver in (
        ("FIXTURE_HMRC.md", "HMRC-001", "1.0"),
        ("FIXTURE_HATP.md", "HATP-001", "1.0"),
        ("FIXTURE_HSCE.md", "HSCE-001", "1.1"),
        ("FIXTURE_RAE.md", "RAE-001", "1.0"),
    ):
        (repo_root / "docs" / "contracts" / name).write_bytes(f"**Contract:** {cid}\n**Version:** {ver}\n".encode())

    frozen_v_old = ("core/fixture_core.py",)  # analogous to pre-2M: admin script NOT bound
    frozen_v_new = ("core/fixture_core.py", "scripts/fixture_admin.py")  # analogous to v1.7: bound

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
    monkeypatch.setattr(hmic, "_CONTRACT_VERSIONS_REQUIRED_KEYS", frozenset({"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}))

    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Fixture"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo_root, check=True)

    return {
        "repo_root": repo_root,
        "protected_root": protected_root,
        "frozen_v_old": frozen_v_old,
        "frozen_v_new": frozen_v_new,
        "monkeypatch": monkeypatch,
    }


def test_pre_binding_digest_unaffected_by_admin_script_mutation(fixture_env):
    monkeypatch = fixture_env["monkeypatch"]
    monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", fixture_env["frozen_v_old"])
    root = HarnessPath(fixture_env["repo_root"])
    before = hmic.derive_implementation_scope_digest(root)
    (fixture_env["repo_root"] / "scripts" / "fixture_admin.py").write_bytes(b"MUTATED admin content\n")
    after = hmic.derive_implementation_scope_digest(root)
    assert before == after  # not yet bound -> mutation invisible (the 149O.20L.7O.2M gap)


def test_post_binding_digest_changes_on_admin_script_mutation(fixture_env):
    monkeypatch = fixture_env["monkeypatch"]
    monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", fixture_env["frozen_v_new"])
    root = HarnessPath(fixture_env["repo_root"])
    before = hmic.derive_implementation_scope_digest(root)
    (fixture_env["repo_root"] / "scripts" / "fixture_admin.py").write_bytes(b"MUTATED admin content\n")
    after = hmic.derive_implementation_scope_digest(root)
    assert before != after  # bound -> mutation detected


def test_negative_control_unbound_file_mutation_never_changes_digest(fixture_env):
    monkeypatch = fixture_env["monkeypatch"]
    monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", fixture_env["frozen_v_new"])
    root = HarnessPath(fixture_env["repo_root"])
    before = hmic.derive_implementation_scope_digest(root)
    (fixture_env["repo_root"] / "scripts" / "not_bound_admin.py").write_bytes(b"MUTATED unbound content\n")
    after = hmic.derive_implementation_scope_digest(root)
    assert before == after


def test_no_grandfathering_old_record_against_widened_source_is_mismatch(fixture_env, tmp_path):
    monkeypatch = fixture_env["monkeypatch"]
    repo_root = fixture_env["repo_root"]
    protected_root = fixture_env["protected_root"]

    # Certify under the OLD (pre-binding) frozen set.
    monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", fixture_env["frozen_v_old"])
    root = HarnessPath(repo_root)
    identity = ensure_repository_identity(root)
    fields = dict(
        repository_instance_id=identity.repository_instance_id,
        canonical_deployment_root=hmic.derive_canonical_deployment_root(root),
        implementation_commit=hmic.derive_implementation_commit(root),
        implementation_scope_digest=hmic.derive_implementation_scope_digest(root),
        contract_versions=dict(hmic.derive_contract_versions(root)),
        verification_record_digest="c" * 64,
        certified_at="2026-08-10T00:00:00Z",
        certified_by="protected-admin",
    )
    certification_id = hmic.derive_certification_id(fields)
    record = hmic.CertificationRecord(certification_id=certification_id, status="active", revoked_at=None, **fields)
    hmic._append_certification_record(protected_root, record)
    hmic._write_active_binding(
        protected_root,
        hmic.CertificationBinding(
            repository_instance_id=identity.repository_instance_id,
            canonical_deployment_root=hmic.derive_canonical_deployment_root(root),
            active_certification_id=record.certification_id,
        ),
    )

    result_before = hmic._validate_at_root(protected_root=protected_root, repository_root=repo_root)
    assert result_before.status == hmic.CertificationStatus.VALID

    # Now evolve the frozen set to bind the admin script (mirrors 149O.20L.7O.2M),
    # WITHOUT touching the original file (fixture_core.py) and WITHOUT creating
    # any new certification -- exactly the "grandfathering" scenario under test.
    monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", fixture_env["frozen_v_new"])
    result_after = hmic._validate_at_root(protected_root=protected_root, repository_root=repo_root)
    assert result_after.status == hmic.CertificationStatus.IMPLEMENTATION_MISMATCH


def test_fresh_v_new_record_is_valid_under_widened_source(fixture_env):
    monkeypatch = fixture_env["monkeypatch"]
    repo_root = fixture_env["repo_root"]
    protected_root = fixture_env["protected_root"]
    monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", fixture_env["frozen_v_new"])
    root = HarnessPath(repo_root)
    identity = ensure_repository_identity(root)
    fields = dict(
        repository_instance_id=identity.repository_instance_id,
        canonical_deployment_root=hmic.derive_canonical_deployment_root(root),
        implementation_commit=hmic.derive_implementation_commit(root),
        implementation_scope_digest=hmic.derive_implementation_scope_digest(root),
        contract_versions=dict(hmic.derive_contract_versions(root)),
        verification_record_digest="d" * 64,
        certified_at="2026-08-20T00:00:00Z",
        certified_by="protected-admin",
    )
    certification_id = hmic.derive_certification_id(fields)
    record = hmic.CertificationRecord(certification_id=certification_id, status="active", revoked_at=None, **fields)
    hmic._append_certification_record(protected_root, record)
    hmic._write_active_binding(
        protected_root,
        hmic.CertificationBinding(
            repository_instance_id=identity.repository_instance_id,
            canonical_deployment_root=hmic.derive_canonical_deployment_root(root),
            active_certification_id=record.certification_id,
        ),
    )
    result = hmic._validate_at_root(protected_root=protected_root, repository_root=repo_root)
    assert result.status == hmic.CertificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════
# §21: closed-schema parser re-test (fresh, not reusing 2M fixtures)
# ═══════════════════════════════════════════════════════════════════════

def _valid_doc():
    return {
        "certification_id": "a" * 64,
        "repository_instance_id": "12345678-1234-4123-8123-123456789abc",
        "canonical_deployment_root": "/some/deployment/root",
        "implementation_commit": "b" * 40,
        "implementation_scope_digest": "c" * 64,
        "contract_versions": {
            "HMRC-001": "1.1", "HATP-001": "1.0", "HSCE-001": "1.3",
            "RAE-001": "1.0", "HBDC-001": "1.2", "HPSE-001": "1.1", "HHCE-001": "1.1",
        },
        "verification_record_digest": "d" * 64,
        "certified_at": "2026-08-20T00:00:00Z",
        "certified_by": "protected-admin",
        "status": "active",
    }


def test_parser_accepts_valid_seven_member_contract_versions():
    doc = _valid_doc()
    record = hmic.parse_certification_record(doc)
    assert len(record.contract_versions) == 7


def test_parser_rejects_missing_member():
    doc = _valid_doc()
    del doc["contract_versions"]["HHCE-001"]
    with pytest.raises(hmic.HATPMandatoryCertificationError):
        hmic.parse_certification_record(doc)


def test_parser_rejects_extra_member():
    doc = _valid_doc()
    doc["contract_versions"]["EXTRA-001"] = "1.0"
    with pytest.raises(hmic.HATPMandatoryCertificationError):
        hmic.parse_certification_record(doc)


def test_parser_rejects_malformed_mapping_type():
    doc = _valid_doc()
    doc["contract_versions"] = "not-a-mapping"
    with pytest.raises(hmic.HATPMandatoryCertificationError):
        hmic.parse_certification_record(doc)


def test_parser_rejects_wrong_top_level_field_structure():
    doc = _valid_doc()
    del doc["status"]
    with pytest.raises(hmic.HATPMandatoryCertificationError):
        hmic.parse_certification_record(doc)


def test_parser_rejects_unknown_field():
    doc = _valid_doc()
    doc["unexpected_field"] = "x"
    with pytest.raises(hmic.HATPMandatoryCertificationError):
        hmic.parse_certification_record(doc)


# ═══════════════════════════════════════════════════════════════════════
# §19/§20: contract identity (7) and live contract_versions
# ═══════════════════════════════════════════════════════════════════════

def test_contract_identity_set_is_exactly_seven():
    assert len(hmic._CONTRACT_IDENTITY_FILES) == 7
    ids = {cid for cid, _ in hmic._CONTRACT_IDENTITY_FILES}
    assert ids == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"}


def test_live_contract_versions_has_seven_keys_hmic_at_v1_7():
    root = HarnessPath(_REPO_ROOT)
    versions = hmic.derive_contract_versions(root)
    assert len(versions) == 7
    assert set(versions) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"}
    contract_text = _CONTRACT_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.7" in contract_text.splitlines()[3]


# ═══════════════════════════════════════════════════════════════════════
# §30: admin script byte-immutability across the 2M phase boundary
# ═══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "path",
    [
        # "scripts/hatp_hardware_credential_admin.py" intentionally
        # excluded as of Phase 149O.20L.7O.2N.1: that phase repaired
        # Blocking finding B-149O.20L.7O.2N-1 (pre-hardware governance
        # confirmation ordering) by editing this file, which is expected
        # to change `implementation_scope_digest` on Mac development
        # source until a fresh HMIC certification binds the new bytes
        # (see `test_phase_149o_20l_7o_2n_1_...`'s own explicit-
        # divergence + all-other-files-unaffected pair of tests).
        "scripts/hatp_principal_signer_admin.py",
        "src/pcae/core/hatp_hardware_credential_admin.py",
        "src/pcae/core/hatp_principal_signer_admin.py",
        "src/pcae/core/hatp_fido2_provider.py",
        "src/pcae/core/hatp_piv_provider.py",
        "src/pcae/core/hatp_providers.py",
        "src/pcae/core/hatp_hardware_credentials.py",
    ],
)
def test_core_writer_and_admin_scripts_byte_identical_across_2m(path):
    pre = _git(["show", f"{_PRE_2M_CHECKPOINT}:{path}"])
    current = (_REPO_ROOT / path).read_text(encoding="utf-8")
    assert pre == current
