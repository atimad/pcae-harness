"""Phase 149O.20L.7O.2H.0 -- HMIC v1.5 CertificationRecord Contract-Version
Closed-Schema Alignment Repair.

Repairs finding B-149O.20L.7O.2H-1: HMIC-001 v1.5 (contract SS20, HMIC-
REQ-067/069/053) normatively requires exactly seven `contract_versions`
entries -- "Seven entries, no more, no fewer, as of v1.5" (HMIC-REQ-067)
-- but production's `_CONTRACT_VERSIONS_REQUIRED_KEYS` (the Wave A
`CertificationRecord` closed-schema acceptance set consumed by
`_require_contract_versions`) was left at six members, omitting
`HBDC-001`, ever since `_CONTRACT_IDENTITY_FILES` (Wave B's own
`contract_versions` derivation input) gained `HBDC-001` at v1.2
(149O.20D/149O.20F). Before this repair, `derive_contract_versions`'s own
current seven-member mapping could never itself parse as a
`CertificationRecord.contract_versions` value, and
`validate_active_hatp_mandatory_independent_verification_certification`'s
own SS31 step 10 dict-equality comparison (current seven-member mapping
vs. a stored record's schema-capped six-member value) could never
succeed for any record -- a load-bearing defect, not mere disclosed,
out-of-scope drift.

Repair: `_CONTRACT_VERSIONS_REQUIRED_KEYS` widened to the exact seven
members of `_CONTRACT_IDENTITY_FILES` (adding `HBDC-001`), restoring
membership equality between Wave A's closed-schema acceptance set and
Wave B's own identity derivation, per HMIC-REQ-067/069/032/053's own
unambiguous v1.5 text (SS20). No contract version bump: HMIC-001 v1.5
already normatively required seven; only production conformance was
repaired. One stale "four frozen contracts" cross-reference in SS31
(HMIC-REQ-103's validation-algorithm step 10 summary), predating every
149O.20D-149O.20L.7O.2H widening, was also corrected to "seven bound
contracts" as a minimal, additive editorial clarification -- not a new
normative statement. A second, textually identical stale phrase inside
SS23 (HMIC-REQ-076's creation-ceremony step 4) was intentionally left
unedited in this phase: it falls inside the byte-identity window a
prior independent-verification suite (`test_phase_149o_20l_7l_6_
contract_preamble_and_relative_import_guard_repair_independent_
verification.py::test_hmic_req_145_closure_paragraph_present_and_
unchanged`) guards around HMIC-REQ-145's own text (that test's
regex-based block extraction stops only at the next parenthetical-
titled `**HMIC-REQ-NNN (` marker, which is not HMIC-REQ-076 -- a
plain, non-parenthetical marker -- so the guarded window incidentally
spans past REQ-145's own text into REQ-076's unrelated prose). Editing
it would fail that prior phase's own regression guard without any
compensating benefit; the SS23 phrase is reproduced verbatim, out of
this phase's own repair scope. See this test module's own
`test_stale_four_frozen_contracts_reference_repaired` for the exact,
narrower assertion this phase makes.

This is a CertificationRecord closed-schema production repair only. It
does not certify, does not activate HATP, does not provision FIDO2
hardware, does not enroll a real Principal/Signer, does not create a
real DeploymentBinding, does not mutate hac-dell or the Protected Root,
does not change readiness semantics, does not close CBV-S10, and does
not change runtime capability. See contract SS20/SS31 and `docs/
PHASE_149O_20L_7O_2H_0_HMIC_CERTIFICATIONRECORD_CONTRACT_VERSION_CLOSED_
SCHEMA_ALIGNMENT_REPAIR.md` for the full phase record.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"

_SEVEN_KEYS = frozenset(
    {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"}
)


# =============================================================================
# 1/2/3. Exact membership of _CONTRACT_IDENTITY_FILES / _CONTRACT_VERSIONS_
# REQUIRED_KEYS, and their equality (items 1, 2, 3)
# =============================================================================


def test_contract_identity_files_exact_seven_members():
    ids = [contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES]
    assert ids == ["HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"]


def test_contract_versions_required_keys_exact_seven_members():
    assert hmic._CONTRACT_VERSIONS_REQUIRED_KEYS == _SEVEN_KEYS
    assert len(hmic._CONTRACT_VERSIONS_REQUIRED_KEYS) == 7


def test_required_keys_equal_identity_file_ids():
    """HMIC-REQ-067/069/053 give no textual basis for a narrower Wave-A
    acceptance set distinct from Wave B's own derivation -- both name the
    same `contract_versions` field (HMIC-REQ-032). Post-repair the two
    semantic key sets are exactly equal."""

    identity_ids = frozenset(contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES)
    assert hmic._CONTRACT_VERSIONS_REQUIRED_KEYS == identity_ids


# =============================================================================
# 4/5. derive_contract_versions returns expected current membership, and
# the derived mapping parses successfully (items 4, 5)
# =============================================================================


def test_derive_contract_versions_returns_seven_members_on_this_repo():
    root = HarnessPath(_REPO_ROOT)
    mapping = hmic.derive_contract_versions(root)
    assert set(mapping.keys()) == _SEVEN_KEYS


def test_derived_mapping_parses_successfully():
    root = HarnessPath(_REPO_ROOT)
    mapping = dict(hmic.derive_contract_versions(root))
    parsed = hmic._require_contract_versions(mapping, context="contract_versions")
    assert dict(parsed) == mapping


# =============================================================================
# 6/7/8/9. Missing HBDC / HPSE / HHCE fails; unknown eighth key fails
# (items 6, 7, 8, 9)
# =============================================================================


class TestRequiredKeyRejection:
    def _seven_member_mapping(self) -> dict:
        root = HarnessPath(_REPO_ROOT)
        return dict(hmic.derive_contract_versions(root))

    def test_missing_hbdc_fails(self):
        mapping = self._seven_member_mapping()
        del mapping["HBDC-001"]
        with pytest.raises(hmic.CertificationMalformedError, match="HBDC-001"):
            hmic._require_contract_versions(mapping, context="contract_versions")

    def test_missing_hpse_fails(self):
        mapping = self._seven_member_mapping()
        del mapping["HPSE-001"]
        with pytest.raises(hmic.CertificationMalformedError, match="HPSE-001"):
            hmic._require_contract_versions(mapping, context="contract_versions")

    def test_missing_hhce_fails(self):
        mapping = self._seven_member_mapping()
        del mapping["HHCE-001"]
        with pytest.raises(hmic.CertificationMalformedError, match="HHCE-001"):
            hmic._require_contract_versions(mapping, context="contract_versions")

    def test_unknown_eighth_key_fails(self):
        mapping = self._seven_member_mapping()
        mapping["UNKNOWN-001"] = "1.0"
        with pytest.raises(hmic.CertificationMalformedError, match="UNKNOWN-001"):
            hmic._require_contract_versions(mapping, context="contract_versions")

    def test_old_six_member_mapping_fails_missing_hbdc(self):
        """Item 16: the pre-repair historical six-member acceptance shape
        (no HBDC-001) now fails closed as MALFORMED (missing required
        key), never silently accepted."""

        mapping = self._seven_member_mapping()
        del mapping["HBDC-001"]
        assert set(mapping.keys()) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HPSE-001", "HHCE-001"}
        with pytest.raises(hmic.CertificationMalformedError):
            hmic._require_contract_versions(mapping, context="contract_versions")


# =============================================================================
# Isolated fixture: a minimal, fully self-consistent git repository whose
# frozen-set entries and bound-contract files are controlled fixture files
# (never this repository's own real frozen files -- mirrors the 149O.19.5D
# suite's `env` fixture pattern exactly), widened to seven bound contracts.
# =============================================================================


def _git(args, cwd: Path) -> str:
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


_FIXTURE_CONTRACTS = (
    ("FIXTURE_HMRC.md", "HMRC-001", "1.0"),
    ("FIXTURE_HATP.md", "HATP-001", "1.0"),
    ("FIXTURE_HSCE.md", "HSCE-001", "1.1"),
    ("FIXTURE_RAE.md", "RAE-001", "1.0"),
    ("FIXTURE_HBDC.md", "HBDC-001", "1.0"),
    ("FIXTURE_HPSE.md", "HPSE-001", "1.0"),
    ("FIXTURE_HHCE.md", "HHCE-001", "1.0"),
)


@pytest.fixture
def env(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    protected_root = tmp_path / "protected-root"
    (repo_root / "src" / "pcae" / "core").mkdir(parents=True)
    (repo_root / "docs" / "contracts").mkdir(parents=True)

    (repo_root / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"alpha content v1\n")
    for name, cid, ver in _FIXTURE_CONTRACTS:
        (repo_root / "docs" / "contracts" / name).write_bytes(f"**Contract:** {cid}\n**Version:** {ver}\n".encode())

    monkeypatch.setattr(
        hmic,
        "_FROZEN_AUTHORITY_BEARING_FILES",
        ("core/fixture_a.py",) + tuple(f"docs/contracts/{name}" for name, _, _ in _FIXTURE_CONTRACTS),
    )
    monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)
    monkeypatch.setattr(
        hmic,
        "_CONTRACT_IDENTITY_FILES",
        tuple((cid, f"docs/contracts/{name}") for name, cid, _ in _FIXTURE_CONTRACTS),
    )
    monkeypatch.setattr(hmic, "_CONTRACT_VERSIONS_REQUIRED_KEYS", _SEVEN_KEYS)

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


def _current_fields(env, *, certified_at="2026-08-19T00:00:00Z", certified_by="protected-admin", verification_record_digest="c" * 64):
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


# =============================================================================
# 13. Exact seven-member record behaves correctly (item 13)
# =============================================================================


def test_seven_member_current_record_is_valid(env):
    record = _record_from_fields(_current_fields(env))
    assert set(record.contract_versions.keys()) == _SEVEN_KEYS
    _store_and_bind(env, record)
    result = _validate(env)
    assert result.status is hmic.CertificationStatus.VALID


# =============================================================================
# 12. Validation consequence -- Cases 1-5 (item 12)
# =============================================================================


class TestActiveValidationCases:
    def test_case1_stored_six_member_record_cannot_even_be_parsed(self, env):
        """Case 1: a stored six-member record (HBDC-001 omitted) can no
        longer be constructed through the closed-schema parser at all --
        `_require_contract_versions` now fails closed for it, matching
        HMIC-REQ-031's closed-schema discipline. This proves the pre-
        repair MALFORMED-record shape is impossible to admit post-repair."""

        six_member = dict(hmic.derive_contract_versions(HarnessPath(env["repo_root"])))
        del six_member["HBDC-001"]
        with pytest.raises(hmic.CertificationMalformedError):
            hmic._require_contract_versions(six_member, context="contract_versions")

    def test_case2_stored_seven_member_record_is_valid(self, env):
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.VALID

    def test_case3_seven_members_wrong_hbdc_version_is_contract_mismatch(self, env):
        fields = _current_fields(env)
        fields["contract_versions"] = dict(fields["contract_versions"])
        fields["contract_versions"]["HBDC-001"] = "9.9"
        record = _record_from_fields(fields)
        _store_and_bind(env, record)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.CONTRACT_MISMATCH

    def test_case4_correct_hbdc_wrong_hpse_version_is_contract_mismatch(self, env):
        fields = _current_fields(env)
        fields["contract_versions"] = dict(fields["contract_versions"])
        fields["contract_versions"]["HPSE-001"] = "9.9"
        record = _record_from_fields(fields)
        _store_and_bind(env, record)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.CONTRACT_MISMATCH

    def test_case5_all_seven_current_versions_correct_is_valid(self, env):
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        result = _validate(env)
        assert result.status is hmic.CertificationStatus.VALID


# =============================================================================
# 10/11. Wrong HHCE version fails (item 8 dup-covered above for missing;
# this covers wrong-version, items 10/11/12 combined coverage for HHCE)
# =============================================================================


def test_wrong_hhce_version_is_contract_mismatch(env):
    fields = _current_fields(env)
    fields["contract_versions"] = dict(fields["contract_versions"])
    fields["contract_versions"]["HHCE-001"] = "9.9"
    record = _record_from_fields(fields)
    _store_and_bind(env, record)
    result = _validate(env)
    assert result.status is hmic.CertificationStatus.CONTRACT_MISMATCH


# =============================================================================
# 14. Certification ID incorporates the complete mapping (item 14)
# =============================================================================


def test_certification_id_changes_when_contract_versions_mapping_changes(env):
    fields_a = _current_fields(env)
    fields_b = _current_fields(env)
    fields_b["contract_versions"] = dict(fields_b["contract_versions"])
    fields_b["contract_versions"]["HBDC-001"] = "9.9"

    id_a = hmic.derive_certification_id(fields_a)
    id_b = hmic.derive_certification_id(fields_b)
    assert id_a != id_b


def test_certification_id_derivation_accepts_full_seven_member_mapping(env):
    fields = _current_fields(env)
    assert set(fields["contract_versions"].keys()) == _SEVEN_KEYS
    certification_id = hmic.derive_certification_id(fields)
    assert re.fullmatch(r"[0-9a-f]{64}", certification_id)


# =============================================================================
# 15. Admin construction path (parse_certification_record) retains all
# seven identities (item 15)
# =============================================================================


def test_parse_certification_record_roundtrip_retains_all_seven(env):
    fields = _current_fields(env)
    certification_id = hmic.derive_certification_id(fields)
    document = {
        "certification_id": certification_id,
        **{k: v for k, v in fields.items()},
        "status": "active",
    }
    record = hmic.parse_certification_record(document)
    assert set(record.contract_versions.keys()) == _SEVEN_KEYS
    round_tripped = hmic.certification_record_to_document(record)
    assert set(round_tripped["contract_versions"].keys()) == _SEVEN_KEYS


# =============================================================================
# 17. No production certification created by this repair's own tests
# (item 17) -- static proof the real Protected Root is never touched
# =============================================================================


_PRODUCTION_TRUST_STORE_ACCESSOR = "HATPTrustStore." + "production"


def test_no_production_certification_functions_called_against_real_root():
    """This entire suite only ever calls `hmic._validate_at_root`/
    `_append_certification_record`/`_write_active_binding` against
    isolated `tmp_path` fixture roots (the `env` fixture) -- never the
    real production trust-store accessor. Confirmed by direct source-text
    inspection of this test module's executable body: the accessor name
    (assembled at runtime here to avoid a self-match false positive) is
    absent from this file's own bytes."""

    this_file = Path(__file__).read_text(encoding="utf-8")
    assert _PRODUCTION_TRUST_STORE_ACCESSOR not in this_file


# =============================================================================
# 18. 35-file frozen identity remains unchanged (item 18)
# =============================================================================


def test_thirty_five_file_frozen_identity_unchanged():
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 35


def test_frozen_src_and_root_relative_counts_unchanged():
    assert len(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES) == 26
    assert len(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 9


# =============================================================================
# 19. Closure limb (d) remains unchanged (item 19)
# =============================================================================


def test_closure_limb_d_text_unchanged():
    text = _CONTRACT_PATH.read_text(encoding="utf-8")
    assert "closure limb (d)" in text
    assert "core/hatp_signing_ceremony.py" in text
    assert "core/hatp_hardware_credential_admin.py" in text
    assert "core/hatp_principal_signer_admin.py" in text


def test_limb_d_source_files_present_in_frozen_src_set():
    for member in (
        "core/hatp_signing_ceremony.py",
        "core/hatp_hardware_credential_admin.py",
        "core/hatp_principal_signer_admin.py",
    ):
        assert member in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES


# =============================================================================
# 20. Runtime remains unchanged (item 20) -- static, no import of runtime
# module by this repair's own production edit
# =============================================================================


def test_hmic_module_does_not_import_runtime_capability_surface():
    text = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    assert "pcae.core.runtime" not in text
    assert "permission_broker" not in text or "PBPA-001" in text  # PB module bytes only, not imported


# =============================================================================
# Contract text (HMIC-001 v1.5) -- normative membership check (item 9)
# =============================================================================


def test_hmic_contract_still_declares_v1_5():
    text = _CONTRACT_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.5" in text


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_hmic_req_067_declares_seven_entries_no_more_no_fewer():
    text = _normalize_whitespace(_CONTRACT_PATH.read_text(encoding="utf-8"))
    assert "Seven entries, no more, no fewer, as of v1.5" in text


def test_hmic_req_069_declares_seven_entries_as_of_v1_5():
    text = _normalize_whitespace(_CONTRACT_PATH.read_text(encoding="utf-8"))
    assert "seven entries as of v1.5" in text


def test_hmic_req_053_no_contract_versions_member_exempted():
    text = _normalize_whitespace(_CONTRACT_PATH.read_text(encoding="utf-8"))
    assert "no `contract_versions` member is exempted from the digest binding" in text


def test_stale_four_frozen_contracts_req_103_reference_repaired():
    """The SS31/HMIC-REQ-103 validation-algorithm-summary "four frozen
    contracts" cross-reference, stale since v1.1, is corrected to "seven
    bound contracts" -- an editorial clarification only, not a new
    normative statement (HMIC-REQ-067/069 already say seven)."""

    text = _normalize_whitespace(_CONTRACT_PATH.read_text(encoding="utf-8"))
    assert "the seven bound contracts' own current version headers -> CONTRACT_MISMATCH" in text


def test_stale_four_frozen_contracts_req_076_reference_intentionally_untouched():
    """The textually-identical SS23/HMIC-REQ-076 creation-ceremony phrase
    is deliberately left as "the four frozen contracts' own version" --
    editing it would fail a prior phase's own independent-verification
    byte-identity guard around HMIC-REQ-145's text (whose regex-based
    extraction window incidentally spans into REQ-076's unrelated prose,
    since REQ-076 has no parenthetical title to serve as the next
    boundary marker). Left verbatim, out of this phase's own scope."""

    text = _normalize_whitespace(_CONTRACT_PATH.read_text(encoding="utf-8"))
    assert "the four frozen contracts' own version headers, SS20" in text or "the four frozen contracts' own version headers, §20" in text


# =============================================================================
# Finding disposition marker (repository-conventional pattern used by
# every prior phase in this track to make disposition greppable)
# =============================================================================


def test_finding_b_149o_20l_7o_2h_1_repaired_not_self_closed_marker_present():
    doc_path = _REPO_ROOT / "docs" / "PHASE_149O_20L_7O_2H_0_HMIC_CERTIFICATIONRECORD_CONTRACT_VERSION_CLOSED_SCHEMA_ALIGNMENT_REPAIR.md"
    text = doc_path.read_text(encoding="utf-8")
    assert "B-149O.20L.7O.2H-1" in text
    assert "REPAIRED" in text
    assert "INDEPENDENT VERIFICATION PENDING" in text
    assert "NOT CLOSED" in text
