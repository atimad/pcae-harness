"""Phase 149O.20L.7O.2G.1 -- HMIC Trust-Enrollment / Signing Target-Set
Reconciliation.

Mechanically re-validates the reconciliation in `docs/PHASE_149O_20L_7O_
2G_1_HMIC_TRUST_ENROLLMENT_SIGNING_TARGET_SET_RECONCILIATION.md`: 2G's
own report recommended binding both content and version for HPSE-001/
HHCE-001 (mirroring the HBDC-001 precedent) but its total future
source/content-set arithmetic (30 -> 33) only reflected the 3 new
Python source files, omitting the 2 new contract-content files its own
recommendation requires. This phase corrects the arithmetic to 30 -> 35
and re-derives the full future membership, without modifying any
production HMIC constant.

No production change. No signing, enrollment, or certification code
path is exercised for a decision -- only static analysis, constant
comparison, and file-existence/header checks.
"""
from __future__ import annotations

from pathlib import Path

from pcae.core import hatp_mandatory_certification as hmic_impl

REPO_ROOT = Path(__file__).resolve().parent.parent

_NEW_SRC_PCAE_RELATIVE = (
    "core/hatp_signing_ceremony.py",
    "core/hatp_hardware_credential_admin.py",
    "core/hatp_principal_signer_admin.py",
)

_NEW_CONTRACT_ROOT_RELATIVE = (
    "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
    "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
)

_NEW_CONTRACT_IDENTITY = (
    ("HPSE-001", "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"),
    ("HHCE-001", "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"),
)


def test_current_baseline_unchanged_thirty_files_five_contracts() -> None:
    assert len(hmic_impl._FROZEN_SRC_PCAE_RELATIVE_FILES) == 23
    assert len(hmic_impl._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 7
    assert len(hmic_impl._FROZEN_AUTHORITY_BEARING_FILES) == 30
    assert len(hmic_impl._CONTRACT_IDENTITY_FILES) == 5


def test_every_current_contract_versions_member_is_also_content_bound() -> None:
    """HMIC-REQ-053's own current text: 'every contract_versions member
    ... receives both bindings uniformly -- no contract_versions member
    is exempted from the digest binding.' Mechanically verified against
    live production state: this is the decisive fact that forces
    content binding for any contract added to contract_versions,
    HPSE-001/HHCE-001 included."""

    current_canonical = set(hmic_impl._frozen_canonical_paths())
    for _contract_id, relative_path in hmic_impl._CONTRACT_IDENTITY_FILES:
        assert relative_path in current_canonical, (
            f"{relative_path} is a contract_versions member but is not content-bound -- "
            "contradicts HMIC-REQ-053's current uniform-coverage rule"
        )


def test_two_candidate_contracts_exist_and_are_not_currently_bound() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    bound_contract_paths = {path for _, path in hmic_impl._CONTRACT_IDENTITY_FILES}
    for relative in _NEW_CONTRACT_ROOT_RELATIVE:
        on_disk = REPO_ROOT / relative
        assert on_disk.is_file(), f"candidate contract missing: {relative}"
        assert relative not in current_canonical, f"{relative} unexpectedly already content-bound"
        assert relative not in bound_contract_paths, f"{relative} unexpectedly already version-bound"


def test_three_candidate_sources_exist_and_are_not_currently_bound() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    for relative in _NEW_SRC_PCAE_RELATIVE:
        on_disk = REPO_ROOT / "src" / "pcae" / relative
        assert on_disk.is_file(), f"candidate source missing: {relative}"
        canonical = f"src/pcae/{relative}"
        assert canonical not in current_canonical, f"{relative} unexpectedly already HMIC-bound"


def test_hpse_hhce_headers_parse_as_version_1_1() -> None:
    for contract_id, relative_path in _NEW_CONTRACT_IDENTITY:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        id_match = hmic_impl._CONTRACT_ID_HEADER_RE.search(text)
        version_match = hmic_impl._CONTRACT_VERSION_HEADER_RE.search(text)
        assert id_match is not None and id_match.group(1) == contract_id
        assert version_match is not None and version_match.group(1) == "1.1"


def test_reconciled_future_source_set_is_twenty_six_entries() -> None:
    future_src = hmic_impl._FROZEN_SRC_PCAE_RELATIVE_FILES + _NEW_SRC_PCAE_RELATIVE
    assert len(future_src) == 26
    assert len(set(future_src)) == len(future_src), "duplicate entries in reconciled source set"
    for relative in future_src:
        assert (REPO_ROOT / "src" / "pcae" / relative).is_file(), f"missing on disk: {relative}"


def test_reconciled_future_root_relative_set_is_nine_entries() -> None:
    # Contract-content additions are appended after HBDC-001 (index 4), the
    # two scripts entries stay last -- mirroring the existing presentation
    # order convention (contracts grouped, then scripts).
    current = hmic_impl._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
    contracts, scripts = current[:5], current[5:]
    future_root = contracts + _NEW_CONTRACT_ROOT_RELATIVE + scripts
    assert len(future_root) == 9
    assert len(set(future_root)) == len(future_root), "duplicate entries in reconciled root-relative set"
    for relative in future_root:
        assert (REPO_ROOT / relative).is_file(), f"missing on disk: {relative}"


def test_reconciled_future_frozen_set_is_exactly_thirty_five_not_thirty_three() -> None:
    """The load-bearing reconciliation result. 2G's own report concluded
    (in its own text, not merely by analogy) that HPSE-001/HHCE-001
    require both content and version binding, but its total-count
    arithmetic (33) only reflected the 3 source additions. This test
    would fail if someone accidentally implements the 2H amendment
    against 2G's uncorrected 33-entry figure instead of the reconciled
    35-entry figure derived in this phase."""

    future_src = hmic_impl._FROZEN_SRC_PCAE_RELATIVE_FILES + _NEW_SRC_PCAE_RELATIVE
    current_root = hmic_impl._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
    future_root = current_root[:5] + _NEW_CONTRACT_ROOT_RELATIVE + current_root[5:]
    future_total = future_src + future_root

    assert len(future_total) == 35
    assert len(future_total) != 33, "reconciled target regressed to 2G's uncorrected source-only count"
    assert len(future_total) == len(set(future_total)), "duplicate entries in reconciled total frozen set"

    current_total_count = len(hmic_impl._FROZEN_AUTHORITY_BEARING_FILES)
    assert current_total_count == 30
    assert len(future_total) - current_total_count == 5, "delta must be +5 (+3 source, +2 contract-content)"


def test_reconciled_future_contract_identity_set_is_seven_members() -> None:
    future_identity = hmic_impl._CONTRACT_IDENTITY_FILES + _NEW_CONTRACT_IDENTITY
    assert len(future_identity) == 7
    future_ids = {contract_id for contract_id, _ in future_identity}
    assert future_ids == {
        "HMRC-001",
        "HATP-001",
        "HSCE-001",
        "RAE-001",
        "HBDC-001",
        "HPSE-001",
        "HHCE-001",
    }
    assert len(future_ids) == len(future_identity), "duplicate contract_versions member"


def test_hsce_001_already_fully_current_unaffected_by_reconciliation() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    assert "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md" in current_canonical
    bound_ids = {c for c, _ in hmic_impl._CONTRACT_IDENTITY_FILES}
    assert "HSCE-001" in bound_ids


def test_class_b_and_deploymentbinding_members_remain_bound_unchanged() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    for relative in (
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hatp_deployment_binding_admin.py",
        "scripts/hatp_deployment_binding_admin.py",
    ):
        assert relative in current_canonical


def test_no_production_hmic_constant_modified_by_this_phase() -> None:
    assert len(hmic_impl._FROZEN_SRC_PCAE_RELATIVE_FILES) == 23
    assert len(hmic_impl._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 7
    assert len(hmic_impl._FROZEN_AUTHORITY_BEARING_FILES) == 30
    assert len(hmic_impl._CONTRACT_IDENTITY_FILES) == 5
    contract_ids = {contract_id for contract_id, _ in hmic_impl._CONTRACT_IDENTITY_FILES}
    assert contract_ids == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"}
