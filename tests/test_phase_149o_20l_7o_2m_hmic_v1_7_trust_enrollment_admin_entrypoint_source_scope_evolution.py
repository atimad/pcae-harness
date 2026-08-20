"""Focused implementation evidence for Phase 149O.20L.7O.2M.

HMIC-001 v1.6 -> v1.7: widens HMIC-REQ-050's frozen authority-bearing
source/content identity from 36 to 38 members by binding the two
standalone Trust-Enrollment administrative CLI entry points,
`scripts/hatp_hardware_credential_admin.py` and
`scripts/hatp_principal_signer_admin.py`, under HMIC-REQ-052(d)'s
existing dual-anchor construction.

This is implementation-phase evidence, not independent verification.
All fixtures are disposable (`tmp_path` copies); no real Trust-Enrollment,
certification, or Protected Root state is ever touched. Verdict this
phase targets: IMPLEMENTED -- INDEPENDENT VERIFICATION PENDING.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_REL = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
SOURCE_REL = "src/pcae/core/hatp_mandatory_certification.py"
NEW_SCRIPTS = (
    "scripts/hatp_hardware_credential_admin.py",
    "scripts/hatp_principal_signer_admin.py",
)
SEVEN_IDS = {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"}

pytestmark = pytest.mark.fast_green


def _contract_text() -> str:
    return (ROOT / CONTRACT_REL).read_text(encoding="utf-8")


def _req050_paths(text: str) -> tuple[str, ...]:
    start = text.index("**HMIC-REQ-050")
    match = re.search(r"\n\*\*HMIC-REQ-\d{3}", text[start + 1 :])
    section = text[start:] if match is None else text[start : start + 1 + match.start()]
    block = re.search(r"```\n(.*?)\n```", section, re.S)
    assert block is not None
    return tuple(line.strip().split()[0] for line in block.group(1).splitlines() if line.strip())


def _canonical_production_paths() -> tuple[str, ...]:
    src = tuple(f"src/pcae/{p}" for p in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES)
    return src + tuple(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES)


def _copy_frozen_tree(destination: Path) -> None:
    for relative in _canonical_production_paths():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def _record_fields(versions: dict[str, str], *, digest: str = "b" * 64) -> dict[str, object]:
    return {
        "repository_instance_id": "123e4567-e89b-42d3-a456-426614174000",
        "canonical_deployment_root": "/deployment",
        "implementation_commit": "a" * 40,
        "implementation_scope_digest": digest,
        "contract_versions": versions,
        "verification_record_digest": "c" * 64,
        "certified_at": "2026-08-20T00:00:00Z",
        "certified_by": "independent-verifier",
    }


def _record_document(versions: dict[str, str], *, digest: str = "b" * 64) -> dict[str, object]:
    fields = _record_fields(versions, digest=digest)
    return {
        "certification_id": hmic.derive_certification_id(fields),
        **fields,
        "status": "active",
    }


# ═══════════════════════════════════════════════════════════════════════════
# §17: exact 38-member frozen set, +2 delta, no extra delta, no duplicates
# ═══════════════════════════════════════════════════════════════════════════


class TestExactMembership:
    def test_production_frozen_set_is_exactly_38(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 38

    def test_exact_plus_two_delta_from_36(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) - 36 == 2

    def test_both_new_scripts_are_bound(self) -> None:
        for path in NEW_SCRIPTS:
            assert path in hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES

    def test_no_third_unexpected_file_added(self) -> None:
        expected_root = {
            "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
            "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
            "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
            "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
            "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
            "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
            "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
            "scripts/hatp_certification_admin.py",
            "scripts/hatp_deployment_binding_admin.py",
            *NEW_SCRIPTS,
        }
        assert set(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == expected_root
        assert len(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES) == 27

    def test_no_duplicate_membership(self) -> None:
        assert len(set(hmic._FROZEN_AUTHORITY_BEARING_FILES)) == len(hmic._FROZEN_AUTHORITY_BEARING_FILES)

    def test_all_38_members_exist_on_disk(self) -> None:
        for relative in _canonical_production_paths():
            assert (ROOT / relative).is_file(), f"missing frozen member: {relative}"

    def test_source_ordering_canonicalization_deterministic(self) -> None:
        first = hmic._frozen_canonical_paths()
        second = hmic._frozen_canonical_paths()
        assert first == second
        assert first == tuple(sorted(first))

    def test_both_script_paths_resolve_correctly(self) -> None:
        canonical = set(hmic._frozen_canonical_paths())
        for path in NEW_SCRIPTS:
            assert path in canonical


# ═══════════════════════════════════════════════════════════════════════════
# Contract text: exact 38-member enumeration, matches production exactly
# ═══════════════════════════════════════════════════════════════════════════


class TestContractProductionMembershipEquality:
    def test_contract_enumerates_exactly_38_paths(self) -> None:
        assert len(_req050_paths(_contract_text())) == 38

    def test_contract_and_production_membership_are_exactly_equal(self) -> None:
        req050 = set(_req050_paths(_contract_text()))
        production = set(hmic._FROZEN_AUTHORITY_BEARING_FILES)
        assert req050 == production

    def test_contract_declares_v1_7(self) -> None:
        text = _contract_text()
        assert "**Version:** 1.7" in text

    def test_new_scripts_appear_in_contract_fence(self) -> None:
        paths = _req050_paths(_contract_text())
        for path in NEW_SCRIPTS:
            assert path in paths


# ═══════════════════════════════════════════════════════════════════════════
# §18/§19: digest-participation regression -- script mutation changes
# implementation_scope_digest; non-bound file mutation does not.
# ═══════════════════════════════════════════════════════════════════════════


class TestDigestParticipation:
    @pytest.mark.parametrize("relative", list(NEW_SCRIPTS))
    def test_new_script_byte_mutation_changes_digest(self, tmp_path: Path, relative: str) -> None:
        _copy_frozen_tree(tmp_path)
        root = HarnessPath(tmp_path)
        before = hmic.derive_implementation_scope_digest(root)
        target = tmp_path / relative
        target.write_bytes(target.read_bytes() + b"\nindependent-drift-probe\n")
        after = hmic.derive_implementation_scope_digest(root)
        assert after != before

    def test_non_bound_documentation_file_mutation_does_not_change_digest(self, tmp_path: Path) -> None:
        _copy_frozen_tree(tmp_path)
        (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
        report = tmp_path / "docs" / "PHASE_149O_20L_7O_2M_SCRATCH_REPORT.md"
        report.write_text("not an HMIC-bound file\n", encoding="utf-8")
        root = HarnessPath(tmp_path)
        before = hmic.derive_implementation_scope_digest(root)
        report.write_text("mutated non-bound report content\n", encoding="utf-8")
        after = hmic.derive_implementation_scope_digest(root)
        assert after == before

    def test_digest_is_deterministic_across_repeated_derivation(self, tmp_path: Path) -> None:
        _copy_frozen_tree(tmp_path)
        root = HarnessPath(tmp_path)
        first = hmic.derive_implementation_scope_digest(root)
        second = hmic.derive_implementation_scope_digest(root)
        assert first == second


# ═══════════════════════════════════════════════════════════════════════════
# §21: contract_versions -- exactly seven members, HMIC-001 unchanged shape
# ═══════════════════════════════════════════════════════════════════════════


class TestContractVersionsExactness:
    def test_contract_identity_files_constant_is_exactly_seven(self) -> None:
        assert len(hmic._CONTRACT_IDENTITY_FILES) == 7
        assert {cid for cid, _ in hmic._CONTRACT_IDENTITY_FILES} == SEVEN_IDS

    def test_live_contract_versions_derivation_has_exactly_seven_members(self) -> None:
        versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
        assert set(versions.keys()) == SEVEN_IDS
        assert len(versions) == 7

    def test_hmic_001_itself_is_not_a_contract_versions_member(self) -> None:
        versions = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
        assert "HMIC-001" not in versions

    def test_no_unknown_or_missing_key(self, tmp_path: Path) -> None:
        _copy_frozen_tree(tmp_path)
        versions = dict(hmic.derive_contract_versions(HarnessPath(tmp_path)))
        assert set(versions.keys()) == SEVEN_IDS


# ═══════════════════════════════════════════════════════════════════════════
# §22: CertificationRecord parser compatibility -- accepts seven-member
# contract_versions containing an HMIC-001-unrelated shape; still rejects
# malformed mappings.
# ═══════════════════════════════════════════════════════════════════════════


class TestParserCompatibility:
    def test_parser_accepts_well_formed_seven_member_record(self) -> None:
        versions = {cid: "1.1" for cid in SEVEN_IDS}
        versions["HMRC-001"] = "1.1"
        record = hmic.parse_certification_record(_record_document(versions))
        assert set(record.contract_versions.keys()) == SEVEN_IDS

    def test_parser_rejects_missing_key(self) -> None:
        versions = {cid: "1.1" for cid in SEVEN_IDS}
        versions.pop("HHCE-001")
        with pytest.raises(hmic.HATPMandatoryCertificationError):
            hmic.parse_certification_record(_record_document(versions))

    def test_parser_rejects_extra_key(self) -> None:
        versions = {cid: "1.1" for cid in SEVEN_IDS}
        versions["HMIC-001"] = "1.7"
        with pytest.raises(hmic.HATPMandatoryCertificationError):
            hmic.parse_certification_record(_record_document(versions))

    def test_parser_rejects_malformed_mapping_shape(self) -> None:
        fields = _record_fields({cid: "1.1" for cid in SEVEN_IDS})
        fields["contract_versions"] = ["HMRC-001", "1.1"]
        document = dict(fields)
        document["certification_id"] = "d" * 64
        document["status"] = "active"
        with pytest.raises(hmic.HATPMandatoryCertificationError):
            hmic.parse_certification_record(document)


# ═══════════════════════════════════════════════════════════════════════════
# §23: old v1.6/36-member certification evaluated against new v1.7/38-member
# source -- must not be VALID.
# ═══════════════════════════════════════════════════════════════════════════


class TestOldCertificationAgainstNewSource:
    def test_old_36_member_digest_mismatches_new_38_member_source(self, tmp_path: Path) -> None:
        # Disposable copy of the CURRENT (v1.7 / 38-member) tree.
        _copy_frozen_tree(tmp_path)
        root = HarnessPath(tmp_path)
        current_digest = hmic.derive_implementation_scope_digest(root)

        # Simulate the OLD v1.6/36-member digest by removing the two new
        # scripts from the disposable copy before deriving a "historical"
        # digest over the remaining 36 files using the same construction.
        old_canonical = tuple(p for p in _canonical_production_paths() if p not in NEW_SCRIPTS)
        assert len(old_canonical) == 36
        import hashlib

        hasher = hashlib.sha256()
        for canonical_path in sorted(old_canonical):
            file_bytes = (tmp_path / canonical_path).read_bytes()
            file_digest = hashlib.sha256(file_bytes).hexdigest()
            hasher.update(f"{canonical_path}\0{file_digest}\n".encode("utf-8"))
        old_digest = hasher.hexdigest()

        assert old_digest != current_digest

    def test_validate_active_rejects_old_v1_6_digest_as_implementation_mismatch(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A stored `CertificationRecord` carrying the old v1.6/36-member
        digest, evaluated against the live v1.7/38-member source (real
        `derive_implementation_scope_digest`, unmocked), fails closed at
        step 9 as IMPLEMENTATION_MISMATCH -- never silently VALID. Uses
        the disposable-fixture `_validate_at_root` seam (mirrors the
        149O.20L.7O.2H.1 precedent); no real Protected Root, binding, or
        certifications.json is ever touched."""

        current = dict(hmic.derive_contract_versions(HarnessPath(ROOT)))
        old_v1_6_digest = "f" * 64  # stands in for the real old v1.6/36-member digest
        record = hmic.parse_certification_record(_record_document(current, digest=old_v1_6_digest))

        monkeypatch.setattr(hmic, "derive_repository_instance_id", lambda _root: record.repository_instance_id)
        monkeypatch.setattr(hmic, "derive_canonical_deployment_root", lambda _root: record.canonical_deployment_root)
        monkeypatch.setattr(hmic, "derive_implementation_commit", lambda _root: record.implementation_commit)
        # derive_implementation_scope_digest is left REAL/unmocked: this is
        # exactly the live v1.7/38-member digest the current tree computes.
        binding = hmic.CertificationBinding(
            record.repository_instance_id, record.canonical_deployment_root, record.certification_id
        )
        monkeypatch.setattr(hmic, "_load_active_binding", lambda *_a, **_k: binding)
        monkeypatch.setattr(hmic, "_load_certification_record", lambda *_a, **_k: record)

        result = hmic._validate_at_root(protected_root=tmp_path / "protected", repository_root=ROOT)
        assert result.status is hmic.CertificationStatus.IMPLEMENTATION_MISMATCH
        assert result.status is not hmic.CertificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# §24: historical snapshot preservation -- prior phases' own fixed-count
# assertions against FIXED historical commits (not live production import)
# remain untouched by this phase.
# ═══════════════════════════════════════════════════════════════════════════


class TestHistoricalSnapshotPreservation:
    def test_prior_phase_fixed_commit_literal_state_unaffected(self) -> None:
        import subprocess

        text = subprocess.check_output(
            ["git", "show", "fd782695c90a8d6ac4e6dd6f985aaf3a9540101a:" + SOURCE_REL],
            cwd=ROOT,
            text=True,
        )
        assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36" in text

    def test_contract_v1_6_history_section_60_preserved(self) -> None:
        text = _contract_text()
        assert "## 60. Contract Amendment and Consistency Repair History" in text
        assert "35 → 36 with no removal" in text
