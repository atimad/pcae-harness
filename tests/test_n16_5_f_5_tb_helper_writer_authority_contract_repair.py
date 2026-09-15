"""N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR — structural /
documentary tests for the HPAC-PAWA-HELPER-001 v2.0 -> v3.0 writer-authority
repair (contract section 30B: Model E, a hybrid of Model B and Model C
helper-process-isolated mutation facades).

This is contract-repair only. There is no production implementation to test
(none of the three new facades, their three authority-family types, or their
defining module exist anywhere under ``src/pcae``). Every test here checks
the *shape* of the frozen contract document and its vocabulary — never
production code behaviour. Bounded worker constraints: read-only against
``src/pcae/**``; no commit/push/finalization performed by this suite or its
author.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
)
PHASE_EVIDENCE_PATH = REPO_ROOT / "docs" / "PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_REPAIR.md"
PAWA_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
)
PPA_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
)
SRC_ROOT = REPO_ROOT / "src" / "pcae"


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def section_30b(contract_text: str) -> str:
    """Isolate the new v3.0 section (30B + 30C), from its heading through
    the start of section 31 (unchanged, pre-existing section)."""

    start = contract_text.index("## 30B. Writer-Authority Repair")
    end = contract_text.index("## 31. Testability requirements")
    return contract_text[start:end]


@pytest.fixture(scope="module")
def phase_evidence_text() -> str:
    return PHASE_EVIDENCE_PATH.read_text(encoding="utf-8")


def _all_src_text() -> str:
    chunks = []
    for path in SRC_ROOT.rglob("*.py"):
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
    return "\n".join(chunks)


def _matrix_data_rows(section_text: str, heading: str, next_heading: str) -> list[str]:
    """Return the markdown-table data rows (excluding header + separator)
    of the first table found between ``heading`` and ``next_heading``."""

    start = section_text.index(heading)
    end = section_text.index(next_heading, start)
    chunk = section_text[start:end]
    lines = [ln for ln in chunk.splitlines() if ln.strip().startswith("|")]
    # Drop header row and the "---" separator row.
    data_rows = [ln for ln in lines[2:]]
    return data_rows


# ---------------------------------------------------------------------------
# Group 1 — version / status identity
# ---------------------------------------------------------------------------


def test_contract_title_and_version_field_are_v3(contract_text: str) -> None:
    assert "HPAC-PAWA-HELPER-001 v3.0" in contract_text
    assert "**Version:** 3.0" in contract_text


def test_contract_status_is_repaired_pending_reverification(contract_text: str) -> None:
    assert "**Status:** REPAIRED / FROZEN — PENDING INDEPENDENT RE-VERIFICATION" in contract_text


def test_v2_0_historical_text_preserved_immutably(contract_text: str) -> None:
    """The v1.0/v2.0 freeze record, requirement text, and threat matrix
    (section 30A and its threat matrix in the companion ARCH doc reference)
    must remain present, unedited — append-only evolution discipline."""

    assert "## 30A. Helper-scoped writer-authority derivation (v2.0)" in contract_text
    assert "HPAC-PAWA-HELPER-REQ-117." in contract_text
    assert "HPAC-PAWA-HELPER-REQ-033." in contract_text
    # The historical v2.0 requirement count statement is untouched.
    assert "**Requirement count (v2.0):** HPAC-PAWA-HELPER-001 v2.0 defines **141**" in contract_text
    assert "**Invariant count (v2.0):** 18" in contract_text


def test_no_stray_verified_claim_about_the_repaired_model(section_30b: str) -> None:
    """Every occurrence of the substring "VERIFIED" inside the new v3.0
    section must be part of "NOT VERIFIED" (predecessor's historical
    finding) — the repaired model itself must never be asserted VERIFIED."""

    all_occurrences = [m.start() for m in re.finditer(r"VERIFIED", section_30b)]
    not_verified_occurrences = [m.start() + 4 for m in re.finditer(r"NOT VERIFIED", section_30b)]
    assert all_occurrences, "expected at least the predecessor's NOT VERIFIED finding to be quoted"
    assert set(all_occurrences) == set(not_verified_occurrences)


def test_model_d_marked_superseded_not_implemented(section_30b: str) -> None:
    assert "superseded" in section_30b.lower()
    assert "MUST NOT be implemented" in section_30b or "SHALL NOT be implemented" in section_30b.upper() or "MUST NOT" in section_30b


# ---------------------------------------------------------------------------
# Group 2 — operation vocabulary / role / subtype vocabulary unchanged
# ---------------------------------------------------------------------------


#: The repair section (30B) concerns only the three v1.0-blocked mutating
#: operations the mint pathway serves (§119/§150); ``certification_read``
#: and ``ceremony_entry`` are non-mutating and out of this repair's scope
#: (unaffected, unchanged) so are not expected to recur in the new section.
EXPECTED_OPERATIONS = [
    "admin_mutation",
    "certification_write",
    "presentation_evidence_write",
]

EXPECTED_ROLES = [
    "hpac_challenge_coordinator",
    "hpac_assertion_recorder",
    "human_authentication_proof_verifier",
    "hpac_gate5_binder",
    "hpac_rhamp_counter_state_verifier",
]

EXPECTED_ADMIN_SUBTYPES = [
    "enroll_principal",
    "revoke_principal",
    "enroll_credential",
    "revoke_credential",
    "initialize_credential_sidecar_state",
    "configure_presentation_mechanism",
    "configure_privileged_helper",
]


@pytest.mark.parametrize("operation", EXPECTED_OPERATIONS)
def test_operation_vocabulary_present_in_repair_section(section_30b: str, operation: str) -> None:
    assert operation in section_30b


@pytest.mark.parametrize("role", EXPECTED_ROLES)
def test_five_certification_roles_present_in_repair_section(section_30b: str, role: str) -> None:
    assert role in section_30b


@pytest.mark.parametrize("subtype", EXPECTED_ADMIN_SUBTYPES)
def test_admin_mutation_subtypes_present_in_repair_section(section_30b: str, subtype: str) -> None:
    assert subtype in section_30b


def test_lifecycle_terminator_still_excluded(section_30b: str) -> None:
    assert "hpac_lifecycle_terminator" in section_30b
    assert "not a member" in section_30b or "not a row" in section_30b


# ---------------------------------------------------------------------------
# Group 3 — new authority-family type names and non-isinstance recognition
# ---------------------------------------------------------------------------


NEW_AUTHORITY_TYPES = [
    "HelperAdminMutationAuthority",
    "HelperCertificationWriteAuthority",
    "HelperPresentationEvidenceAuthority",
]


@pytest.mark.parametrize("type_name", NEW_AUTHORITY_TYPES)
def test_new_authority_family_types_named(section_30b: str, type_name: str) -> None:
    assert type_name in section_30b


def test_recognition_is_explicitly_not_bare_isinstance(section_30b: str) -> None:
    assert "isinstance" in section_30b
    assert "exact-type" in section_30b or "exact type" in section_30b


def test_new_authority_types_do_not_exist_in_repository_yet() -> None:
    """This is contract-repair only — no production implementation."""

    src_text = _all_src_text()
    for type_name in NEW_AUTHORITY_TYPES:
        assert type_name not in src_text
    assert "hpac_pawa_helper_writer_authority" not in src_text


# ---------------------------------------------------------------------------
# Group 4 — requirement / invariant inventory contiguity
# ---------------------------------------------------------------------------


def test_new_requirements_141_through_171_contiguous_no_gaps(contract_text: str) -> None:
    found = sorted(
        {
            int(n)
            for n in re.findall(r"HPAC-PAWA-HELPER-REQ-(\d{3})\b", contract_text)
            if 141 <= int(n) <= 171
        }
    )
    expected = list(range(141, 172))
    assert found == expected, f"expected contiguous 141..171, got {found}"


def test_new_invariants_19_through_24_present_exactly_once(section_30b: str) -> None:
    for n in range(19, 25):
        label = f"PAWAH-INV-{n}."
        assert section_30b.count(label) == 1, f"{label} should appear exactly once"


def test_requirement_count_statement_v3_0(contract_text: str) -> None:
    assert "**Requirement count (v3.0):** HPAC-PAWA-HELPER-001 v3.0 defines **172**" in contract_text


def test_invariant_count_statement_v3_0(contract_text: str) -> None:
    assert "**Invariant count (v3.0):** 24" in contract_text


# ---------------------------------------------------------------------------
# Group 5 — matrices: row/column counts by parsing markdown tables
# ---------------------------------------------------------------------------


def test_threat_matrix_has_exactly_40_rows(section_30b: str) -> None:
    rows = _matrix_data_rows(
        section_30b,
        "### 30B.11 Threat matrix",
        "### 30B.12 Store-recognition matrix",
    )
    # Each data row starts with "| <n> |"; filter to numbered rows only.
    numbered = [r for r in rows if re.match(r"^\|\s*\*?\*?\d+\*?\*?\s*\|", r)]
    assert len(numbered) == 40, f"expected 40 threat-matrix rows, found {len(numbered)}"


def test_threat_matrix_includes_both_predecessor_gap_rows(section_30b: str) -> None:
    rows = _matrix_data_rows(
        section_30b,
        "### 30B.11 Threat matrix",
        "### 30B.12 Store-recognition matrix",
    )
    joined = "\n".join(rows)
    assert "predecessor-IV gap #1" in joined
    assert "predecessor-IV gap #2" in joined


def test_store_recognition_matrix_has_four_authority_family_rows(section_30b: str) -> None:
    rows = _matrix_data_rows(
        section_30b,
        "### 30B.12 Store-recognition matrix",
        "### 30B.13 Certification five-role matrix",
    )
    assert len(rows) == 5  # 4 authority-family rows + 1 "any other object" row


def test_certification_five_role_matrix_is_5x5(section_30b: str) -> None:
    rows = _matrix_data_rows(
        section_30b,
        "### 30B.13 Certification five-role matrix",
        "### 30B.14 Admin-mutation subtype matrix",
    )
    assert len(rows) == 5
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        assert len(cells) == 6  # row label + 5 role columns


def test_certification_five_role_matrix_diagonal_permit_off_diagonal_deny(section_30b: str) -> None:
    rows = _matrix_data_rows(
        section_30b,
        "### 30B.13 Certification five-role matrix",
        "### 30B.14 Admin-mutation subtype matrix",
    )
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.strip().strip("|").split("|")][1:]
        for j, cell in enumerate(cells):
            if i == j:
                assert "PERMIT" in cell
            else:
                assert cell == "DENY"


def test_admin_mutation_subtype_matrix_is_7x7(section_30b: str) -> None:
    rows = _matrix_data_rows(
        section_30b,
        "### 30B.14 Admin-mutation subtype matrix",
        "### 30B.15 REQ-033 disposition",
    )
    assert len(rows) == 7
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        assert len(cells) == 8  # row label + 7 subtype columns


def test_admin_mutation_subtype_matrix_diagonal_permit_off_diagonal_deny(section_30b: str) -> None:
    rows = _matrix_data_rows(
        section_30b,
        "### 30B.14 Admin-mutation subtype matrix",
        "### 30B.15 REQ-033 disposition",
    )
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.strip().strip("|").split("|")][1:]
        for j, cell in enumerate(cells):
            if i == j:
                assert "PERMIT" in cell
            else:
                assert cell == "DENY"


# ---------------------------------------------------------------------------
# Group 6 — REQ-033 disposition and module-boundary discipline
# ---------------------------------------------------------------------------


def test_req_033_own_text_unchanged(contract_text: str) -> None:
    assert (
        "HPAC-PAWA-HELPER-REQ-033.** The helper SHALL NOT `import` the in-process"
        in contract_text
    )


def test_req_033_disposition_v3_present(section_30b: str) -> None:
    assert "HPAC-PAWA-HELPER-REQ-171" in section_30b
    assert "REQ-033's own text (§7) and" in section_30b
    assert "import-graph" in section_30b


def test_process_boundary_is_primary_not_seal_alone(section_30b: str) -> None:
    assert "defense-in-depth" in section_30b
    assert "never the sole boundary" in section_30b or "never the sole gate" in section_30b


# ---------------------------------------------------------------------------
# Group 7 — versioning rationale and PAWA/PPA impact adjudication
# ---------------------------------------------------------------------------


def test_versioning_rationale_cites_req_130(section_30b: str) -> None:
    assert "HPAC-PAWA-HELPER-REQ-130" in section_30b
    assert "v2.0 -> v3.0, MAJOR" in section_30b


def test_pawa_and_ppa_declared_byte_unchanged(section_30b: str) -> None:
    assert "HPAC-PAWA-001 remains v2.0, byte-unchanged" in section_30b
    assert "HPAC-PPA-001 remains v2.0, byte-unchanged" in section_30b


def test_pawa_and_ppa_files_not_modified() -> None:
    """This repair explicitly must not touch these two contract files."""

    assert PAWA_CONTRACT_PATH.exists()
    assert PPA_CONTRACT_PATH.exists()
    pawa_text = PAWA_CONTRACT_PATH.read_text(encoding="utf-8")
    ppa_text = PPA_CONTRACT_PATH.read_text(encoding="utf-8")
    assert "# HPAC-PAWA-001 v2.0" in pawa_text
    assert "# HPAC-PPA-001 v2.0" in ppa_text


# ---------------------------------------------------------------------------
# Group 8 — phase-evidence document shape
# ---------------------------------------------------------------------------


def test_phase_evidence_file_exists_and_has_result_line(phase_evidence_text: str) -> None:
    assert "COMPLETE — REPAIRED / FROZEN — PENDING INDEPENDENT RE-VERIFICATION" in phase_evidence_text


def test_phase_evidence_quotes_both_predecessor_gaps_verbatim(phase_evidence_text: str) -> None:
    assert "ordinary process invokes the" in phase_evidence_text
    assert "role/subject field mutation on an" in phase_evidence_text


def test_phase_evidence_declares_no_source_change_and_not_begun_items(phase_evidence_text: str) -> None:
    assert "**NONE**" in phase_evidence_text
    assert "**NOT BEGUN**" in phase_evidence_text
    assert "Live host writes: **0**." in phase_evidence_text
    assert "N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR-IV" in phase_evidence_text


def test_phase_evidence_preserves_delegated_finalization_unauthorized_wording(
    phase_evidence_text: str,
) -> None:
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED" in phase_evidence_text


# ---------------------------------------------------------------------------
# Group 9 — no production source touched by this repair
# ---------------------------------------------------------------------------


def test_no_facade_functions_exist_yet() -> None:
    src_text = _all_src_text()
    for name in (
        "mint_and_perform_admin_mutation",
        "mint_and_perform_certification_write",
        "mint_and_perform_presentation_evidence_write",
    ):
        assert name not in src_text
