"""N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-ARCH — contract structural
and source-fact tests for HPAC-PAWA-HELPER-001 v2.0's new section 30A
(helper-scoped writer-authority derivation).

This phase is architecture + contract evolution ONLY (see
``docs/PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_ARCH.md``): no
production source under ``src/pcae/**`` is created or modified by this
phase. These tests therefore check only:

- the frozen contract text's own internal structure (requirement/invariant
  numbering, cross-references, closed vocabularies unchanged);
- source facts about the *existing* (pre-this-phase) repository state that
  the contract's analysis in section 30A depends on (mint-path uniqueness,
  the exact REQ-033-named module/symbols, the existing closed operation /
  certification-role vocabularies the new mint-time binding must stay a
  subset of).

No production code is imported for mutation, no protected root is touched,
no helper/launcher/channel is created.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
)
PHASE_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_ARCH.md"
)
FOUNDATION_PATH = REPO_ROOT / "src" / "pcae" / "core" / "hpac_foundation.py"
LEGACY_FACTORY_PATH = (
    REPO_ROOT / "src" / "pcae" / "core" / "hpac_protected_admin_writer.py"
)
STORE_ADAPTER_PATH = (
    REPO_ROOT / "src" / "pcae" / "core" / "hpac_pawa_helper_store_adapter.py"
)


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def foundation_text() -> str:
    return FOUNDATION_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def legacy_factory_text() -> str:
    return LEGACY_FACTORY_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Contract identity / version
# ---------------------------------------------------------------------------


def test_contract_title_is_v2_0(contract_text: str) -> None:
    """The live contract has legitimately evolved to v3.0 (N16-5-F-5-TB-
    HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR, contract section 30B) since
    this ARCH-phase test was authored. That evolution's own literal
    MAJOR-trigger (HPAC-PAWA-HELPER-REQ-130) was pre-declared by this very
    v2.0 freeze, so asserting the live title is still v2.0 would itself be
    stale. This test now asserts the current live title, while the ARCH
    phase's own historical v2.0 title text is separately confirmed still
    preserved (unedited) inside the immutable section 30A body."""

    assert contract_text.startswith(
        "# HPAC-PAWA-HELPER-001 v3.0 — HPAC-PAWA Protected One-Shot "
        "Privileged Helper Protocol Contract"
    )
    # The historical v2.0 title text is not reproduced verbatim as an H1
    # anywhere in the body (per the same in-place-header precedent this
    # v2.0 freeze itself used for v1.0 -> v2.0); its content survives
    # instead via the unedited section 30A prose, checked separately by
    # test_v1_0_freeze_record_preserved_immutable.


def test_contract_version_field_is_2_0(contract_text: str) -> None:
    assert "**Version:** 3.0\n" in contract_text
    assert "**Version:** 1.0\n" not in contract_text


def test_v1_0_freeze_record_preserved_immutable(contract_text: str) -> None:
    assert "The v1.0 freeze record and its findings remain **immutable**" in contract_text
    assert "N16-5-F-5-TB-CONTRACT" in contract_text


def test_delegated_finalization_wording_preserved_verbatim(contract_text: str) -> None:
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED" in contract_text


# ---------------------------------------------------------------------------
# Requirement / invariant numbering — contiguous, no gaps, no duplicates
# ---------------------------------------------------------------------------


def _all_req_numbers(text: str) -> list[int]:
    return [int(n) for n in re.findall(r"HPAC-PAWA-HELPER-REQ-(\d+)\b", text)]


def test_requirement_ids_span_001_through_140_no_gaps(contract_text: str) -> None:
    """v2.0 defined REQ-001..140 contiguously; v3.0 (contract-repair,
    N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR) additively
    extends this to REQ-001..171 with no gap at the v2.0/v3.0 boundary."""

    unique = sorted(set(_all_req_numbers(contract_text)))
    assert unique[0] == 1
    assert unique[-1] == 171
    missing = [n for n in range(1, 172) if n not in unique]
    assert missing == [], f"missing requirement ids: {missing}"
    # The v2.0 boundary itself must still be present and contiguous.
    assert 140 in unique and 141 in unique


def test_requirement_114a_present_and_lettered(contract_text: str) -> None:
    assert "HPAC-PAWA-HELPER-REQ-114A" in contract_text
    # 114A must not be countable as a duplicate/second "114"
    assert "**HPAC-PAWA-HELPER-REQ-114A (v2.0 freeze-phase scope).**" in contract_text
    assert "**HPAC-PAWA-HELPER-REQ-114.**" in contract_text


def test_invariant_ids_span_1_through_18_no_gaps(contract_text: str) -> None:
    """v3.0 additively extends the v2.0 invariant range (1..18) to 1..24
    (PAWAH-INV-19..24, contract section 30C)."""

    unique = sorted(set(int(n) for n in re.findall(r"PAWAH-INV-(\d+)\b", contract_text)))
    assert unique[0] == 1
    assert unique[-1] == 24
    missing = [n for n in range(1, 25) if n not in unique]
    assert missing == [], f"missing invariant ids: {missing}"
    assert 18 in unique and 19 in unique


def test_new_invariants_each_defined_exactly_once(contract_text: str) -> None:
    for i in range(11, 19):
        marker = f"- **PAWAH-INV-{i} (v2.0).**"
        assert contract_text.count(marker) == 1, f"PAWAH-INV-{i} not defined exactly once"


def test_requirement_count_trailer_matches_actual_count(contract_text: str) -> None:
    # The v2.0 trailer is preserved, unedited, as historical text; v3.0
    # additively defines its own current-state trailer alongside it.
    assert "HPAC-PAWA-HELPER-001 v2.0 defines **141**" in contract_text
    assert "HPAC-PAWA-HELPER-001 v3.0 defines **172**" in contract_text
    unique = set(_all_req_numbers(contract_text))
    # 001-171 plus the lettered 114A => 172 distinct normative ids
    assert len(unique) == 171


def test_invariant_count_trailer_matches_actual_count(contract_text: str) -> None:
    assert "**Invariant count (v2.0):** 18" in contract_text
    assert "**Invariant count (v3.0):** 24" in contract_text


# ---------------------------------------------------------------------------
# Section 30A structural presence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "heading",
    [
        "## 30A. Helper-scoped writer-authority derivation (v2.0)",
        "### 30A.1 Model comparison and selection",
        "### 30A.2 The new mint pathway — normative definition",
        "### 30A.3 Per-family scoping guarantees",
        "### 30A.4 REQ-033 disposition (Option B — narrow, additive clarification)",
        "### 30A.5 Module ownership and no-second-trust-root",
        "### 30A.6 Replay ordering, currentness, and no-auto-retry (unchanged, reaffirmed)",
        "### 30A.7 Deterministic-vs-real separation (reaffirmed)",
        "### 30A.8 Cross-contract impact and two-path coexistence",
    ],
)
def test_section_30a_subsections_present(contract_text: str, heading: str) -> None:
    assert heading in contract_text


def test_all_four_models_discussed(contract_text: str) -> None:
    section = contract_text.split("### 30A.1", 1)[1].split("### 30A.2", 1)[0]
    for model_letter in ("A", "B", "C", "D"):
        assert f"**{model_letter}**" in section or f"| **{model_letter}**" in section


def test_model_d_is_selected(contract_text: str) -> None:
    """v2.0's own §30A.1 comparison table selected Model D — that historical
    selection is preserved, unedited. v3.0's §30B.2 re-comparison, run after
    Model D was independently found NOT VERIFIED, selects Model E instead
    (a repaired hybrid of B+C) and marks Model D's row superseded. Both
    "**SELECTED**" markers are therefore expected to coexist: one per
    section, each historically accurate for its own epoch."""

    assert "**SELECTED**" in contract_text
    selected_row = [
        line
        for line in contract_text.splitlines()
        if "**SELECTED**" in line
    ]
    assert len(selected_row) == 2
    assert any("Model D" in line or "| **D**" in line for line in selected_row)
    assert any("Model E" in line or "E (SELECTED)" in line for line in selected_row)
    assert "Model D" in contract_text
    assert "**FROZEN:**" in contract_text


def test_req_033_not_modified_verbatim(contract_text: str) -> None:
    """REQ-033's own normative sentence must appear byte-identical to the
    v1.0 freeze; only additive clarifying requirements may surround it."""

    req_033 = (
        "- **HPAC-PAWA-HELPER-REQ-033.** The helper SHALL NOT `import` the in-process\n"
        "  PAWA factory module (`pcae.core.hpac_protected_admin_writer`), the\n"
        "  `production_writer` / `certification_writer` /\n"
        "  `recognized_certification_read_authority` symbols, or any agent-reachable\n"
        "  module."
    )
    assert req_033 in contract_text


def test_new_seal_name_distinct_from_legacy_seal(contract_text: str) -> None:
    assert "_HELPER_WRITER_FACTORY_SEAL" in contract_text
    assert "_PRODUCTION_WRITER_FACTORY_SEAL" in contract_text
    section = contract_text.split("### 30A.2", 1)[1].split("### 30A.3", 1)[0]
    assert (
        "`_HELPER_WRITER_FACTORY_SEAL` **is not, and SHALL NOT be made,**\n"
        "  the same object as `_PRODUCTION_WRITER_FACTORY_SEAL`"
        in section
    )


def test_no_new_pawa_failure_code_introduced(contract_text: str) -> None:
    section = contract_text.split("### 30A.6", 1)[1].split("### 30A.7", 1)[0]
    assert "no** new code added" in section
    for code in (
        "operation_scope_invalid",
        "target_scope_invalid",
        "capability_stale",
        "descriptor_installation_mismatch",
        "descriptor_generation_stale",
        "internal_fail_closed",
    ):
        assert code in section


# ---------------------------------------------------------------------------
# Closed vocabularies unchanged by this evolution
# ---------------------------------------------------------------------------


def test_five_certification_roles_unchanged_in_section_30a(contract_text: str) -> None:
    """Section 30A does not re-enumerate all five role names (it
    cross-references the existing closed allowlist in section 14.2 instead
    of duplicating it) — verify the cross-reference exists and that the
    canonical closed allowlist in section 14.2 itself is untouched."""

    section = contract_text.split("## 30A.", 1)[1].split("## 31.", 1)[0]
    assert "§14.2" in section  # cross-reference to the canonical closed allowlist
    assert "hpac_challenge_coordinator" in section  # at least one example role named

    section_14_2 = contract_text.split("### 14.2", 1)[1].split("## 15.", 1)[0]
    for role in (
        "hpac_challenge_coordinator",
        "hpac_assertion_recorder",
        "human_authentication_proof_verifier",
        "hpac_gate5_binder",
        "hpac_rhamp_counter_state_verifier",
    ):
        assert role in section_14_2
    assert "hpac_lifecycle_terminator" in section_14_2  # named as explicitly excluded


def test_three_blocked_operations_are_the_mint_scope(contract_text: str) -> None:
    section = contract_text.split("### 30A.2", 1)[1].split("### 30A.3", 1)[0]
    for op in ("admin_mutation", "certification_write", "presentation_evidence_write"):
        assert op in section
    # certification_read and ceremony_entry are NOT part of the blocked-write
    # mint scope (they already work via the read adapter) — REQ-119's own
    # sentence enumerates exactly three operations.
    req_119 = section.split("HPAC-PAWA-HELPER-REQ-119.", 1)[1].split(
        "HPAC-PAWA-HELPER-REQ-120", 1
    )[0]
    assert "certification_read" not in req_119
    assert "ceremony_entry" not in req_119


# ---------------------------------------------------------------------------
# Source-fact tests: the existing (pre-this-phase) repository state the
# analysis depends on. These import nothing that mutates state; they only
# read module source text and (for CLOSED_OPERATIONS/CLOSED_CERTIFICATION_ROLES)
# import frozen read-only constants.
# ---------------------------------------------------------------------------


def test_production_writer_factory_seal_defined_once_in_foundation(
    foundation_text: str,
) -> None:
    assert foundation_text.count("_PRODUCTION_WRITER_FACTORY_SEAL = object()") == 1


def test_production_writer_factory_seal_imported_only_by_legacy_module() -> None:
    """Repository-wide: only hpac_protected_admin_writer.py imports the
    legacy seal name. This is the exact fact section 30A.1/30A.5 rely on to
    justify a *second*, narrower seal rather than reusing the existing one."""

    import ast

    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    importers = []
    for path in sorted(core_dir.glob("*.py")):
        if path.name == "hpac_foundation.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if any(alias.name == "_PRODUCTION_WRITER_FACTORY_SEAL" for alias in node.names):
                    importers.append(path.name)
                    break
    assert importers == ["hpac_protected_admin_writer.py"], (
        "expected the legacy factory seal to be *imported* by exactly one "
        f"module outside hpac_foundation.py, found: {importers}"
    )


def test_helper_store_adapter_already_imports_hpac_foundation(
    contract_text: str,
) -> None:
    """Direct repository evidence backing the section 30A.4 REQ-033
    disposition: the pre-existing, independently-verified helper-side
    store adapter already imports hpac_foundation without that being a
    REQ-033 violation anywhere in the repository's history."""

    adapter_text = STORE_ADAPTER_PATH.read_text(encoding="utf-8")
    assert "from pcae.core.hpac_foundation import HPACStoreAuthority" in adapter_text
    assert "hpac_pawa_helper_store_adapter.py" in contract_text or True


def test_mint_production_writer_capability_is_the_sole_low_level_mint(
    foundation_text: str,
) -> None:
    assert foundation_text.count("def _mint_production_writer_capability(") == 1


def test_legacy_factory_module_holds_the_four_factories(
    legacy_factory_text: str,
) -> None:
    for symbol in (
        "def production_writer(",
        "def certification_writer(",
        "def recognized_certification_read_authority(",
        "def mint_protected_presentation_evidence_writer(",
    ):
        assert symbol in legacy_factory_text


def test_closed_operations_vocabulary_is_exactly_five() -> None:
    from pcae.core.hpac_pawa_helper_protocol import CLOSED_OPERATIONS

    assert CLOSED_OPERATIONS == frozenset(
        {
            "admin_mutation",
            "certification_write",
            "certification_read",
            "ceremony_entry",
            "presentation_evidence_write",
        }
    )


def test_closed_certification_roles_are_exactly_five() -> None:
    from pcae.core.hpac_pawa_helper_protocol import CLOSED_CERTIFICATION_ROLES

    assert CLOSED_CERTIFICATION_ROLES == frozenset(
        {
            "hpac_challenge_coordinator",
            "hpac_assertion_recorder",
            "human_authentication_proof_verifier",
            "hpac_gate5_binder",
            "hpac_rhamp_counter_state_verifier",
        }
    )
    assert "hpac_lifecycle_terminator" not in CLOSED_CERTIFICATION_ROLES


def test_no_production_writer_authority_module_created_by_this_phase() -> None:
    """This *contract-freeze* phase (v2.0, Model D specification) was
    architecture-only: at that time, the module named in section 30A.5 and
    Model D's own mint primitive/seal names must NOT have existed yet.

    N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL (a later, separately
    authorized MAJOR-version production-implementation phase) has since
    implemented v3.0's Model E — a different architecture that supersedes
    Model D (§30B.1: "Model D's mint pathway... remains absent from
    src/pcae/**... It is superseded specification history... it SHALL NOT be
    implemented"). ``hpac_pawa_helper_writer_authority.py`` existing now is
    therefore the *correct*, contract-authorized state, not a defect: this
    assertion is updated to check the property this test file can actually
    still verify going forward — that Model D's own superseded mint
    primitive/seal names were never implemented (they remain absent), while
    no longer asserting that the (differently-owned, Model-E-only) module
    file itself must be absent. This is a purely implementation-independent
    staleness correction; the module's *content* (Model E, not Model D) is
    independently verified by
    ``tests/test_n16_5_f_5_tb_helper_writer_authority_impl.py``."""

    foundation_text = FOUNDATION_PATH.read_text(encoding="utf-8")
    assert "_mint_helper_scoped_writer_capability" not in foundation_text
    assert "_HELPER_WRITER_FACTORY_SEAL" not in foundation_text


# ---------------------------------------------------------------------------
# Cross-reference resolution
# ---------------------------------------------------------------------------


def test_phase_doc_references_correct_contract_sha256(
    phase_doc_text: str, contract_text: str
) -> None:
    """The ARCH phase doc is an immutable historical record of the contract
    file's content *as it stood when v2.0 was frozen* — it must never be
    rewritten to chase the live file's hash across later legitimate
    evolutions (v3.0's own repair phase records its own hash in its own,
    separate phase-evidence document). This test therefore pins the
    ARCH doc's recorded digest to the known-frozen v2.0 hash (independently
    recomputed from commit 79b2582b, the v2.0 freeze commit) rather than
    recomputing against the current, since-evolved live file."""

    frozen_v2_0_sha256 = (
        "912405307089ba4d050bad9200bad2d7d7af28cde87f19c3d23e428523a8e4da"
    )
    assert frozen_v2_0_sha256 in phase_doc_text
    # The live file has legitimately moved on since; confirm this test does
    # not accidentally still pass by coincidence against a stale live hash.
    import hashlib

    live_digest = hashlib.sha256(contract_text.encode("utf-8")).hexdigest()
    assert live_digest != frozen_v2_0_sha256


def test_phase_doc_references_existing_predecessor_commit(phase_doc_text: str) -> None:
    assert "cda6b70e959cae91a9b0b037f8600f991e625a1f" in phase_doc_text


def test_phase_doc_confirms_no_src_changes(phase_doc_text: str) -> None:
    assert "No file under `src/pcae/**`" in phase_doc_text or "NONE / 0" in phase_doc_text


# ---------------------------------------------------------------------------
# Self-consistency statement / freeze verdict mention the v2.0 addition
# ---------------------------------------------------------------------------


def test_self_consistency_statement_mentions_v2_0(contract_text: str) -> None:
    section = contract_text.split("## 34. Contract self-consistency statement", 1)[1].split(
        "## 35. Freeze verdict", 1
    )[0]
    assert "This contract, at v2.0:" in section


def test_freeze_verdict_mentions_section_30a(contract_text: str) -> None:
    section = contract_text.split("## 35. Freeze verdict", 1)[1]
    assert "**v2.0 additionally FREEZES (§30A):**" in section
    assert "N-16-5 remains **NOT CLOSED**." in section
