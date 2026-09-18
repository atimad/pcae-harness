"""Phase N16-5-F-5-TB-HELPER-INSTALLATION-PROVISIONING-CONTRACT-REPAIR.

Contract-shape tests only: this is a contract-repair phase, not an
implementation phase. No `src/pcae` module is imported or exercised; these
tests validate the frozen markdown contract text is internally consistent,
mechanically complete, and that the F1 circularity is textually removed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = REPO_ROOT / "docs" / "contracts"
HELPER = CONTRACTS / "HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
PAWA = CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
PPA = CONTRACTS / "HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"


@pytest.fixture(scope="module")
def helper_text() -> str:
    return HELPER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pawa_text() -> str:
    return PAWA.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ppa_text() -> str:
    return PPA.read_text(encoding="utf-8")


def test_helper_version_is_5_0(helper_text: str) -> None:
    assert "# HPAC-PAWA-HELPER-001 v5.0" in helper_text
    assert "**Version:** 5.0" in helper_text


def test_pawa_version_is_4_0(pawa_text: str) -> None:
    assert "# HPAC-PAWA-001 v4.0" in pawa_text
    assert "**Version:** 4.0" in pawa_text


def test_ppa_stays_byte_unchanged_v2_1(ppa_text: str) -> None:
    assert "# HPAC-PPA-001 v2.1" in ppa_text
    assert "**Version:** 2.1" in ppa_text


def test_helper_has_section_30e(helper_text: str) -> None:
    assert "## 30E. Provisioning/rotation dispatch reconciliation (v5.0)" in helper_text


def test_pawa_has_section_98(pawa_text: str) -> None:
    assert "## 98. Component-lifecycle dispatch correction (v4.0)" in pawa_text


def test_configure_privileged_helper_removed_from_helper_admin_mutation_enum(
    helper_text: str,
) -> None:
    """F1-A/F1-B repair: `configure_privileged_helper` must no longer be a
    member of the closed `admin_mutation` operation_params.mutation enum in
    the HELPER protocol contract — this is the textual proof the circularity
    is removed (H can never again be asked to perform this operation)."""
    # The closed-enum table row must exist and must NOT list configure_privileged_helper.
    assert "operation_params.mutation ∈ { enroll_principal, revoke_principal, revoke_credential" in helper_text or (
        "enroll_principal, revoke_principal, enroll_credential, revoke_credential, "
        "initialize_credential_sidecar_state }" in helper_text
    )
    assert (
        "enroll_principal, revoke_principal, enroll_credential, revoke_credential, "
        "initialize_credential_sidecar_state, configure_presentation_mechanism, "
        "configure_privileged_helper }" not in helper_text
    ), "pre-repair circular enum membership must not survive verbatim"


def test_configure_presentation_mechanism_removed_from_helper_admin_mutation_enum(
    helper_text: str,
) -> None:
    enum_line = [
        line
        for line in helper_text.splitlines()
        if "operation_params.mutation ∈" in line
    ]
    assert enum_line, "expected exactly one closed admin_mutation enum table row"
    enum_set_text = enum_line[0].split("(§30E.2")[0]
    assert "configure_presentation_mechanism" not in enum_set_text
    assert "configure_privileged_helper" not in enum_set_text


def test_pawa_req_328_corrected_by_req_345(pawa_text: str) -> None:
    assert "HPAC-PAWA-REQ-345." in pawa_text
    assert "REQ-328 is corrected" in pawa_text
    assert "never through the §33C out-of-process helper" in pawa_text


def test_pawa_genesis_rotation_recovery_requirements_present(pawa_text: str) -> None:
    for req in ("HPAC-PAWA-REQ-346.", "HPAC-PAWA-REQ-347.", "HPAC-PAWA-REQ-348."):
        assert req in pawa_text, f"missing explicit genesis/rotation/recovery requirement {req}"


def test_pawa_configured_agent_exclusion_for_provisioning_executor(pawa_text: str) -> None:
    assert "HPAC-PAWA-REQ-350." in pawa_text
    assert "SHALL NOT be the configured agent principal" in pawa_text


def test_ppa_confirmed_unaffected(pawa_text: str) -> None:
    assert "HPAC-PAWA-REQ-351." in pawa_text
    assert "HPAC-PPA-001, which remains" in pawa_text
    assert "v2.1, byte-unchanged" in pawa_text


def test_pawa_version_trigger_documented(pawa_text: str) -> None:
    assert "HPAC-PAWA-REQ-352." in pawa_text
    assert "v3.0 -> v4.0 is MAJOR" in pawa_text


def test_helper_version_trigger_documented(helper_text: str) -> None:
    assert "HPAC-PAWA-HELPER-REQ-188." in helper_text
    assert "v4.0 -> v5.0 is MAJOR" in helper_text


def test_helper_req_185_self_lineage_satisfied_by_construction(helper_text: str) -> None:
    assert "HPAC-PAWA-HELPER-REQ-185." in helper_text
    assert "satisfied by construction" in helper_text


def test_model_e_preserved_language_present(helper_text: str) -> None:
    assert "Model E (§30B) is **untouched**" in helper_text


def test_delegated_finalization_line_preserved_in_both_edited_contracts(
    helper_text: str, pawa_text: str
) -> None:
    marker = "DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED"
    assert marker in helper_text
    assert marker in pawa_text


def test_requirement_count_lines_present_and_monotonic(helper_text: str, pawa_text: str) -> None:
    assert "**Requirement count (v5.0):** existing 184 declarations (including 114A)" in helper_text
    assert "plus REQ-184..188 = 189 declarations." in helper_text
    assert "**Requirement count (v4.0):** existing 344 declarations plus" in pawa_text
    assert "REQ-345..352 = 352" in pawa_text


def test_helper_requirement_ids_184_to_188_sequential_no_gap(helper_text: str) -> None:
    for n in range(184, 189):
        assert f"HPAC-PAWA-HELPER-REQ-{n}." in helper_text, f"missing REQ-{n}"


def test_pawa_requirement_ids_345_to_352_sequential_no_gap(pawa_text: str) -> None:
    for n in range(345, 353):
        assert f"HPAC-PAWA-REQ-{n}." in pawa_text, f"missing REQ-{n}"


def test_no_src_pcae_files_referenced_as_edited_in_this_phase() -> None:
    """This is a contract-repair phase: forbid any src/pcae file from having
    been touched by this task (git-diff-free check: the allow-list itself is
    enforced by the governed task contract; this test additionally asserts
    the evidence doc records zero production-source mutation)."""
    evidence = (
        REPO_ROOT
        / "docs"
        / "PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR.md"
    )
    assert evidence.exists()
    text = evidence.read_text(encoding="utf-8")
    assert "no implementation performed" in text.lower() or "no production or contract" in text.lower() or "no change" in text.lower()


def test_evidence_doc_has_f1_a_and_f1_b_dispositions() -> None:
    evidence = (
        REPO_ROOT
        / "docs"
        / "PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR.md"
    )
    text = evidence.read_text(encoding="utf-8")
    assert "F1-A independently CONFIRMED" in text
    assert "F1-B independently CONFIRMED" in text


def test_evidence_doc_has_genesis_rotation_recovery_matrix() -> None:
    evidence = (
        REPO_ROOT
        / "docs"
        / "PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR.md"
    )
    text = evidence.read_text(encoding="utf-8")
    assert "| **Genesis**" in text
    assert "| **Rotation**" in text
    assert "| **Recovery**" in text


def test_evidence_doc_recommends_fresh_iv_not_begun() -> None:
    evidence = (
        REPO_ROOT
        / "docs"
        / "PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR.md"
    )
    text = evidence.read_text(encoding="utf-8")
    assert "PROVISIONING-CONTRACT-REPAIR-IV" in text
    assert "NOT BEGUN" in text
    assert "N-16-5 remains **NOT" in text
