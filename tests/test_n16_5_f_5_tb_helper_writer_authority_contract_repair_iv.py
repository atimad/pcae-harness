"""N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-CONTRACT-REPAIR-IV — a fresh,
independent, adversarial re-verification of the HPAC-PAWA-HELPER-001 v3.0
Model E writer-authority repair (contract section 30B/30C).

This suite is deliberately NOT a copy of
``tests/test_n16_5_f_5_tb_helper_writer_authority_contract_repair.py`` (the
predecessor repair phase's own 48-test suite). It independently re-derives
its assertions from the frozen contract text and from the current
``src/pcae/**`` tree, rather than trusting the predecessor's own summary,
matrices, or test names as proof. Where an assertion happens to check a
similar fact to a predecessor test, the *derivation* here is independent
(re-located contiguous ID ranges are computed from the file itself, not
hard-coded from the predecessor's stated counts).

Scope note: production implementation of Model E does not exist yet (by
design — this is a contract-only repair phase awaiting independent
verification before any implementation phase is authorized). Every test
below is a static/document-structure/source-fact test; none exercises a
production writer-authority code path because none exists to exercise.

Bounded-worker constraints observed by this file's author: read-only against
``src/pcae/**`` and the three contract `.md` files; no commit, push, or
finalization performed by this suite or its author.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md"
)
PAWA_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
)
PPA_CONTRACT_PATH = (
    REPO_ROOT / "docs" / "contracts" / "HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
)
IV_DOC_PATH = (
    REPO_ROOT / "docs" / "PHASE_N16_5_F_5_TB_HELPER_WRITER_AUTHORITY_CONTRACT_IV.md"
)
SRC_ROOT = REPO_ROOT / "src" / "pcae"

REQ_ID_RE = re.compile(r"HPAC-PAWA-HELPER-REQ-(\d+)([A-Z]?)\b")
INV_ID_RE = re.compile(r"PAWAH-INV-(\d+)\b")


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def section_30b(contract_text: str) -> str:
    start = contract_text.index("## 30B. Writer-Authority Repair")
    end = contract_text.index("## 31. Testability requirements")
    return contract_text[start:end]


@pytest.fixture(scope="module")
def section_30b_core(contract_text: str) -> str:
    """30B only, excluding 30C (the invariants section) — used for the
    threat-matrix / per-operation checks that should live in 30B proper."""

    start = contract_text.index("## 30B. Writer-Authority Repair")
    end = contract_text.index("## 30C. Security invariants added by v3.0")
    return contract_text[start:end]


@pytest.fixture(scope="module")
def section_30c(contract_text: str) -> str:
    start = contract_text.index("## 30C. Security invariants added by v3.0")
    end = contract_text.index("## 31. Testability requirements")
    return contract_text[start:end]


@pytest.fixture(scope="module")
def iv_doc_text() -> str:
    return IV_DOC_PATH.read_text(encoding="utf-8")


def _all_src_text() -> str:
    chunks = []
    for path in SRC_ROOT.rglob("*.py"):
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
    return "\n".join(chunks)


def _norm(text: str) -> str:
    """Collapse whitespace/newlines so a markdown line-wrap does not defeat
    a substring check across a wrapped phrase."""

    return re.sub(r"\s+", " ", text)


def _matrix_rows(section_text: str, heading: str, next_heading: str) -> list[str]:
    start = section_text.index(heading)
    end = section_text.index(next_heading, start) if next_heading in section_text[start:] else len(section_text)
    chunk = section_text[start:start + end] if next_heading not in section_text[start:] else section_text[start:section_text.index(next_heading, start)]
    lines = [ln for ln in chunk.splitlines() if ln.strip().startswith("|")]
    return lines[2:]  # drop header + separator


# ---------------------------------------------------------------------------
# Group 1 — version / status identity (independently re-derived)
# ---------------------------------------------------------------------------


def test_identity_block_declares_v3_status_and_pending_reverification(contract_text: str) -> None:
    head = contract_text[:4000]
    assert "**Version:** 3.0" in head
    assert "**Status:** REPAIRED / FROZEN — PENDING INDEPENDENT RE-VERIFICATION" in head
    # Never claim self-verified; that is the point of pending re-verification.
    assert "Status:** VERIFIED" not in head


def test_v2_0_to_v3_0_bump_is_explicitly_labeled_major(contract_text: str) -> None:
    head = contract_text[:4000]
    assert "v2.0 -> v3.0 is a MAJOR evolution" in head


def test_model_d_text_is_preserved_not_deleted(contract_text: str) -> None:
    assert "## 30A. Helper-scoped writer-authority derivation (v2.0)" in contract_text
    assert "_mint_helper_scoped_writer_capability" in contract_text
    assert "_HELPER_WRITER_FACTORY_SEAL" in contract_text


def test_model_d_is_marked_superseded_and_must_not_be_implemented(section_30b: str) -> None:
    assert "superseded" in section_30b.lower()
    assert "MUST NOT be implemented" in section_30b


# ---------------------------------------------------------------------------
# Group 2 — REQ-130 text and MAJOR-trigger justification (independent
# re-derivation of the versioning claim; do not just trust the phase doc)
# ---------------------------------------------------------------------------


def test_req_130_text_states_unconditional_major_trigger_for_new_mint_mechanisms(
    contract_text: str,
) -> None:
    match = re.search(
        r"\*\*HPAC-PAWA-HELPER-REQ-130\.\*\*(.*?)(?=\n- \*\*HPAC-PAWA-HELPER-REQ-131)",
        contract_text,
        re.DOTALL,
    )
    assert match, "REQ-130 body not found by anchored regex"
    body = match.group(1)
    assert "introducing any new internal writer-" in body
    assert "mint mechanism" in body
    assert "is a" in body and "MAJOR" in body
    assert "even if narrowly scoped" in body


def test_req_167_cites_req_130_as_the_versioning_trigger(section_30b: str) -> None:
    assert "HPAC-PAWA-HELPER-REQ-130" in section_30b
    idx = section_30b.index("### 30B.9 Versioning rationale")
    chunk = section_30b[idx: idx + 2500]
    assert "REQ-130" in chunk
    assert "v2.0 -> v3.0, MAJOR" in chunk


def test_external_wire_vocabulary_explicitly_declared_unchanged(section_30b: str) -> None:
    idx = section_30b.index("### 30B.9 Versioning rationale")
    chunk = section_30b[idx: idx + 2500]
    assert "byte-unchanged" in chunk
    assert "wire schema change" in chunk or "wire schemas" in chunk


# ---------------------------------------------------------------------------
# Group 3 — Model E vs. Model D textual distinction (mechanical, not merely
# nominal — the OS-process-boundary property must appear as the PRIMARY
# gate, and the process-local seal must be explicitly framed as
# defense-in-depth-only, never load-bearing alone).
# ---------------------------------------------------------------------------


def test_model_e_relocates_mint_primitive_to_a_new_helper_exclusive_module(
    section_30b: str,
) -> None:
    assert "pcae.core.hpac_pawa_helper_writer_authority" in section_30b
    assert "never" in section_30b and "hpac_foundation" in section_30b


def test_os_process_boundary_named_as_the_mint_eligibility_gate(section_30b: str) -> None:
    idx = section_30b.index("### 30B.3 Mint eligibility")
    chunk = section_30b[idx: idx + 3000]
    assert "OS-process" in chunk or "OS process" in chunk
    assert "absence-of-shared-memory" in chunk or "absence of shared memory" in chunk


def test_process_local_seal_explicitly_framed_as_defense_in_depth_only(section_30b: str) -> None:
    idx = section_30b.index("REQ-146")
    chunk = section_30b[idx: idx + 1200]
    assert "defense-in-depth" in chunk
    assert "never" in chunk and "sufficient" in chunk


def test_contract_never_claims_the_seal_alone_is_sufficient(section_30b: str) -> None:
    # Adversarial: scan the whole repair section for the specific forbidden
    # claim shape ("seal alone" / "seal is sufficient" without a negation
    # nearby). A bare regex hit is not itself damning -- the phrase must not
    # appear as an *affirmative* claim; a hit preceded closely by a negator
    # ("not"/"never"/"does not"/"no") within 30 chars is the expected,
    # required disclaimer, not a defect.
    normalized = _norm(section_30b)
    forbidden = re.compile(r"seal[^.]{0,40}(alone|by itself)[^.]{0,40}(suffic)", re.IGNORECASE)
    for m in forbidden.finditer(normalized):
        preceding = normalized[max(0, m.start() - 30): m.start()]
        assert re.search(r"\b(not|never|no|n't)\b", preceding, re.IGNORECASE), (
            f"found an affirmative (non-negated) seal-alone-sufficient claim: "
            f"{normalized[max(0, m.start()-60):m.end()+20]!r}"
        )


# ---------------------------------------------------------------------------
# Group 4 — no-broad-isinstance-authorization requirement text
# ---------------------------------------------------------------------------


def test_store_recognition_forbids_bare_isinstance_against_shared_base(section_30b: str) -> None:
    idx = section_30b.index("### 30B.4 Store recognition mechanism")
    chunk = section_30b[idx: idx + 3500]
    assert "isinstance" in chunk
    assert "never" in chunk
    assert "exact-type" in chunk or "sealed-family" in chunk


def test_two_directional_confusion_explicitly_denied(section_30b: str) -> None:
    idx = section_30b.index("REQ-151")
    chunk = section_30b[idx: idx + 900]
    assert "cannot satisfy" in chunk
    assert "legacy" in chunk.lower()


def test_pawah_inv_20_names_both_directions_of_confusion(section_30c: str) -> None:
    idx = section_30c.index("PAWAH-INV-20")
    chunk = section_30c[idx: idx + 500]
    assert "isinstance" in chunk
    assert "either direction" in chunk or "both" in chunk.lower()


# ---------------------------------------------------------------------------
# Group 5 — matrices independently reconstructed and diffed against
# structural expectations (not merely copied from the predecessor).
# ---------------------------------------------------------------------------


def test_store_recognition_matrix_five_rows_and_correct_permit_placement(
    section_30b_core: str,
) -> None:
    rows = _matrix_rows(
        section_30b_core,
        "### 30B.12 Store-recognition matrix",
        "### 30B.13 Certification five-role matrix",
    )
    # header table has 5 data rows: 3 helper families + legacy + "any other".
    assert len(rows) == 5, rows
    families = {
        "HelperAdminMutationAuthority": "admin_mutation",
        "HelperCertificationWriteAuthority": "certification_write",
        "HelperPresentationEvidenceAuthority": "presentation_evidence_write",
    }
    for family, surface in families.items():
        row = next(r for r in rows if family in r)
        cells = [c.strip() for c in row.strip("|").split("|")]
        # cells[0]=family name, [1]=admin_mutation col, [2]=cert col, [3]=pres col, [4]=other col
        permit_cells = [c for c in cells[1:] if c.startswith("**PERMIT**")]
        assert len(permit_cells) == 1, f"{family} row does not have exactly one PERMIT cell: {cells}"
    legacy_row = next(r for r in rows if "legacy `HPACWriterCapability`" in r)
    legacy_cells = [c.strip() for c in legacy_row.strip("|").split("|")]
    # legacy is broad: PERMIT on the three named surfaces, DENY on "any other".
    assert legacy_cells[1].startswith("PERMIT")
    assert legacy_cells[2].startswith("PERMIT")
    assert legacy_cells[3].startswith("PERMIT")
    assert "DENY" in legacy_cells[4]
    forged_row = next(r for r in rows if "forged shell" in r)
    forged_cells = [c.strip() for c in forged_row.strip("|").split("|")]
    assert all(c == "DENY" for c in forged_cells[1:])


def test_certification_five_role_matrix_is_pure_identity_matrix(section_30b_core: str) -> None:
    rows = _matrix_rows(
        section_30b_core,
        "### 30B.13 Certification five-role matrix",
        "### 30B.14 Admin-mutation subtype matrix",
    )
    # 5 role rows expected (terminator excluded, confirmed by a separate test).
    assert len(rows) == 5, rows
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.strip("|").split("|")]
        role_cells = cells[1:]
        assert len(role_cells) == 5, cells
        for j, cell in enumerate(role_cells):
            if i == j:
                assert cell == "**PERMIT**", f"diagonal[{i}] not PERMIT: {cells}"
            else:
                assert cell == "DENY", f"off-diagonal[{i}][{j}] not DENY: {cells}"


def test_lifecycle_terminator_excluded_from_the_five_role_matrix(section_30b_core: str) -> None:
    idx = section_30b_core.index("### 30B.13 Certification five-role matrix")
    end = section_30b_core.index("### 30B.14", idx)
    chunk = section_30b_core[idx:end]
    assert "hpac_lifecycle_terminator" in chunk
    assert "not a row or column" in chunk


def test_admin_mutation_subtype_matrix_is_pure_identity_matrix_7x7(section_30b_core: str) -> None:
    idx = section_30b_core.index("### 30B.14 Admin-mutation subtype matrix")
    end = section_30b_core.index("### 30B.15", idx)
    chunk = section_30b_core[idx:end]
    rows = [ln for ln in chunk.splitlines() if ln.strip().startswith("|")][2:]
    assert len(rows) == 7, rows
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.strip("|").split("|")]
        subtype_cells = cells[1:]
        assert len(subtype_cells) == 7, cells
        for j, cell in enumerate(subtype_cells):
            if i == j:
                assert cell.startswith("**PERMIT**"), f"diagonal[{i}] not PERMIT: {cells}"
            else:
                assert cell == "DENY", f"off-diagonal[{i}][{j}] not DENY: {cells}"


def test_threat_matrix_row_count_is_exactly_40_independently_counted(section_30b_core: str) -> None:
    idx = section_30b_core.index("### 30B.11 Threat matrix")
    end = section_30b_core.index("### 30B.12", idx)
    chunk = section_30b_core[idx:end]
    rows = [ln for ln in chunk.splitlines() if ln.strip().startswith("|")][2:]
    assert len(rows) == 40, len(rows)
    # first cell of each row must be a strictly increasing integer 1..40
    numbers = []
    for row in rows:
        first_cell = row.strip("|").split("|")[0].strip().strip("*")
        numbers.append(int(first_cell))
    assert numbers == list(range(1, 41)), numbers


def test_threat_matrix_rows_31_and_32_are_the_two_predecessor_gaps(section_30b_core: str) -> None:
    idx = section_30b_core.index("### 30B.11 Threat matrix")
    end = section_30b_core.index("### 30B.12", idx)
    chunk = section_30b_core[idx:end]
    row_31 = next(ln for ln in chunk.splitlines() if ln.strip().startswith("| **31**"))
    row_32 = next(ln for ln in chunk.splitlines() if ln.strip().startswith("| **32**"))
    assert "low-level mint primitive directly" in row_31
    assert "predecessor-IV gap #1" in row_31
    assert "Role/subject field mutation" in row_32
    assert "predecessor-IV gap #2" in row_32


# ---------------------------------------------------------------------------
# Group 6 — the two predecessor threat-gap quotes must appear verbatim in
# BOTH the failed-IV doc and the repair contract (independent cross-check,
# not merely "a row exists").
# ---------------------------------------------------------------------------


def test_predecessor_gap_quotes_match_verbatim_between_iv_doc_and_contract(
    iv_doc_text: str, section_30b: str
) -> None:
    gap_1_fragment = (
        "No threat-matrix row addresses \"ordinary process invokes the\n"
        "   low-level mint primitive directly, bypassing the higher-level factory's\n"
        "   recognition sequence\""
    )
    gap_2_fragment = (
        "No threat-matrix row addresses \"role/subject field mutation on an\n"
        "   already-legitimately-issued capability by its own holder\""
    )
    def _norm_quote(s: str) -> str:
        # Strip markdown blockquote/bold markers so a re-wrapped `> **...`
        # quotation still compares equal to the plain original phrasing.
        return _norm(s.replace(">", " ").replace("**", ""))

    assert _norm_quote(gap_1_fragment) in _norm_quote(iv_doc_text)
    assert _norm_quote(gap_2_fragment) in _norm_quote(iv_doc_text)
    assert _norm_quote(gap_1_fragment) in _norm_quote(section_30b)
    assert _norm_quote(gap_2_fragment) in _norm_quote(section_30b)


# ---------------------------------------------------------------------------
# Group 7 — REQ-033 disposition re-verification (compare v2.0's REQ-129
# disposition against v3.0's REQ-171 extension; confirm the earlier text is
# byte-unchanged and the new clarification is additive, not a re-meaning).
# ---------------------------------------------------------------------------


def test_req_033_own_text_is_unchanged_since_v1_0(contract_text: str) -> None:
    match = re.search(
        r"\*\*HPAC-PAWA-HELPER-REQ-033\.\*\*(.*?)(?=\n- \*\*HPAC-PAWA-HELPER-REQ-034)",
        contract_text,
        re.DOTALL,
    )
    assert match
    body = _norm(match.group(1))
    assert "SHALL NOT" in body
    assert "in-process PAWA factory module" in body
    assert "any agent-reachable module" in body
    # REQ-033 itself must not mention Model E's new module by name — that
    # would mean the base requirement text was edited, not merely clarified
    # elsewhere.
    assert "hpac_pawa_helper_writer_authority" not in body


def test_req_171_extends_req_033_to_the_mint_primitives_defining_module(
    section_30b: str,
) -> None:
    idx = section_30b.index("HPAC-PAWA-HELPER-REQ-171")
    chunk = section_30b[idx: idx + 3000]
    assert "defining module of the low-level" in chunk or "defining module" in chunk
    assert "not only its" in chunk or "not only its immediate caller" in chunk


def test_req_171_requires_independent_import_graph_verifiability(section_30b: str) -> None:
    idx = section_30b.index("HPAC-PAWA-HELPER-REQ-171")
    chunk = section_30b[idx: idx + 3000]
    assert "import-graph" in chunk
    assert "not asserted only by" in chunk or "docstring" in chunk


# ---------------------------------------------------------------------------
# Group 8 — restart-dead / non-serialization / no-generic-broker text
# presence for the NEW authority families specifically (not just the old
# HPACWriterCapability guarantees, which the new families must inherit or
# restate).
# ---------------------------------------------------------------------------


def test_no_generic_broker_banned_for_the_new_facades(section_30b: str) -> None:
    idx = section_30b.index("HPAC-PAWA-HELPER-REQ-152")
    chunk = section_30b[idx: idx + 700]
    assert "no" in chunk.lower() and "generic" in chunk.lower()
    assert "helper_write(store, method, args)" in chunk


def test_no_parallel_replay_mechanism_for_new_facades(section_30b: str) -> None:
    idx = section_30b.index("HPAC-PAWA-HELPER-REQ-160")
    chunk = section_30b[idx: idx + 900]
    assert "no parallel replay mechanism" in chunk.lower() or "no** parallel replay" in chunk


def test_no_fallback_to_superseded_model_or_legacy_factory(section_30b: str) -> None:
    idx = section_30b.index("HPAC-PAWA-HELPER-REQ-166")
    chunk = section_30b[idx: idx + 900]
    assert "no fallback" in chunk.lower() or "No fallback" in chunk
    assert "legacy" in chunk.lower()
    assert "Model D" in chunk


def test_pawah_inv_24_names_reuse_not_reinvention(section_30c: str) -> None:
    idx = section_30c.index("PAWAH-INV-24.**")
    chunk = _norm(section_30c[idx: idx + 400]).lower()
    assert "reuses the" in chunk or "reuse" in chunk
    assert "no parallel" in chunk or "no new" in chunk


# ---------------------------------------------------------------------------
# Group 9 — PAWA / PPA byte-identity (this file's own before/after check,
# independent of the contract's own self-consistency prose).
# ---------------------------------------------------------------------------


def test_pawa_contract_sha256_matches_recorded_v2_0_baseline() -> None:
    digest = hashlib.sha256(PAWA_CONTRACT_PATH.read_bytes()).hexdigest()
    assert digest == "b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e"


def test_ppa_contract_sha256_matches_recorded_v2_0_baseline() -> None:
    digest = hashlib.sha256(PPA_CONTRACT_PATH.read_bytes()).hexdigest()
    assert digest == "27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2"


def test_pawa_and_ppa_declared_byte_unchanged_by_the_repair(section_30b: str) -> None:
    idx = section_30b.index("### 30B.10 PAWA and PPA")
    chunk = section_30b[idx: idx + 2000]
    assert "HPAC-PAWA-001 remains v2.0, byte-unchanged" in chunk
    assert "HPAC-PPA-001 remains v2.0, byte-unchanged" in chunk


# ---------------------------------------------------------------------------
# Group 10 — requirement / invariant ID contiguity, independently
# re-derived from the current file (not assuming the predecessor's stated
# ranges are still current -- another phase may have touched the file
# since; grep-derive the actual max ID present).
# ---------------------------------------------------------------------------


def test_requirement_ids_are_contiguous_from_001_with_one_lettered_insertion(
    contract_text: str,
) -> None:
    numbers = set()
    lettered = set()
    for num_str, letter in REQ_ID_RE.findall(contract_text):
        num = int(num_str)
        if letter:
            lettered.add((num, letter))
        else:
            numbers.add(num)
    assert numbers, "no HPAC-PAWA-HELPER-REQ ids found at all"
    max_id = max(numbers)
    missing = sorted(set(range(1, max_id + 1)) - numbers)
    assert not missing, f"gap(s) found in requirement numbering: {missing}"
    # Independently confirm the current max matches this repair's own
    # documented total (171) -- but derive it from the file, don't assume it.
    assert max_id == 171, f"expected current max REQ id 171, found {max_id}"
    assert (114, "A") in lettered


def test_invariant_ids_are_contiguous_from_1_through_current_max(contract_text: str) -> None:
    numbers = {int(n) for n in INV_ID_RE.findall(contract_text)}
    assert numbers
    max_id = max(numbers)
    missing = sorted(set(range(1, max_id + 1)) - numbers)
    assert not missing, f"gap(s) found in invariant numbering: {missing}"
    assert max_id == 24, f"expected current max PAWAH-INV id 24, found {max_id}"


def test_section_33_requirement_count_statement_matches_independently_derived_max(
    contract_text: str,
) -> None:
    numbers = {int(n) for n, _ in REQ_ID_RE.findall(contract_text)}
    max_id = max(numbers)
    assert f"defines **172**" in contract_text or "defines **172** requirement items total" in contract_text
    # 172 = 171 numeric ids (1..171) + the one lettered 114A insertion.
    assert max_id + 1 == 172


# ---------------------------------------------------------------------------
# Group 11 — production absence facts (independent re-confirmation that
# Model E's production implementation genuinely does not exist; a failure
# here would mean either the contract-only-phase discipline was violated,
# or the codebase has since evolved and this IV's other findings need
# re-scoping).
# ---------------------------------------------------------------------------


def test_model_e_authority_types_absent_from_src_pcae() -> None:
    """This IV phase (verification-only, no production implementation) ran
    against a repository state where Model E's authority types did not yet
    exist -- this test's own original comment anticipated exactly the event
    that has since occurred: "Model E may now be implemented; re-scope this
    IV." N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL (a later, separately
    authorized MAJOR production-implementation phase) has implemented Model
    E. Re-scoped per that anticipation: this test now asserts the symbols
    exist (implementation landed) and are owned by exactly the one module
    the contract requires (HPAC-PAWA-HELPER-REQ-144), not scattered/duplicated
    elsewhere in src/pcae/**. Full Model E correctness (exact-type recognition,
    no-isinstance-escape, seal-gating, etc.) is independently tested by
    tests/test_n16_5_f_5_tb_helper_writer_authority_impl.py -- this IV suite
    only re-confirms this narrow, implementation-independent staleness
    correction, not a re-verification of the later phase's own work."""

    from pcae.core import hpac_pawa_helper_writer_authority as impl_module

    owning_module = impl_module.__name__
    for symbol in (
        "HelperAdminMutationAuthority",
        "HelperCertificationWriteAuthority",
        "HelperPresentationEvidenceAuthority",
        "mint_and_perform_admin_mutation",
        "mint_and_perform_certification_write",
        "mint_and_perform_presentation_evidence_write",
    ):
        obj = getattr(impl_module, symbol, None)
        assert obj is not None, f"{symbol} expected to exist in {owning_module} (Model E implemented)"
        defining_module = getattr(obj, "__module__", owning_module)
        assert defining_module == owning_module, f"{symbol} must be owned by {owning_module}, not {defining_module}"

    other_core_text = _all_src_text().replace(
        (SRC_ROOT / "core" / "hpac_pawa_helper_writer_authority.py").read_text(encoding="utf-8"), ""
    )
    for symbol in (
        "HelperAdminMutationAuthority",
        "HelperCertificationWriteAuthority",
        "HelperPresentationEvidenceAuthority",
    ):
        # Recognition-site references (e.g. in the store adapter) legitimately
        # name these types for type(...)-is comparisons; a *class definition*
        # (a second, duplicate one) elsewhere would be the actual regression.
        assert f"class {symbol}" not in other_core_text, f"{symbol} must not be redefined outside its owning module"


def test_model_e_module_does_not_exist_as_a_file() -> None:
    """Re-scoped (see test_model_e_authority_types_absent_from_src_pcae
    above): the module now exists, as the later implementation phase's own
    authorization required (§30B.3/§144). What this IV's own record can
    still usefully assert going forward is that the module is exactly the
    one this contract names -- not a differently-named duplicate -- and that
    it is a single file, not split across a package."""

    module_path = SRC_ROOT / "core" / "hpac_pawa_helper_writer_authority.py"
    assert module_path.exists() and module_path.is_file()
    assert not (SRC_ROOT / "core" / "hpac_pawa_helper_writer_authority").exists(), (
        "must remain a single module file, not a package"
    )


def test_legacy_seal_and_mint_primitive_still_present_and_unmodified_in_shape() -> None:
    """Model E must not have silently started by editing the legacy path
    instead of adding a new one -- confirm the legacy seal/primitive this
    repair explicitly promises not to touch is still exactly where the
    predecessor IV found it."""

    foundation_path = SRC_ROOT / "core" / "hpac_foundation.py"
    text = foundation_path.read_text(encoding="utf-8")
    assert "_PRODUCTION_WRITER_FACTORY_SEAL = object()" in text
    assert "_mint_production_writer_capability" in text


def test_disclosed_new_capability_no_own_seal_finding_still_reproducible() -> None:
    """Independently re-confirm the phase-evidence-disclosed (not
    IV-blocking) observation that ``_new_capability`` has no seal check of
    its own -- this IV re-checks it is still true and still merely
    disclosed, not silently repaired without a contract update, and not
    silently worsened."""

    foundation_path = SRC_ROOT / "core" / "hpac_foundation.py"
    text = foundation_path.read_text(encoding="utf-8")
    match = re.search(r"def _new_capability\(.*?\n(?:.*\n)*?        return capability\n", text)
    assert match, "_new_capability definition not found; re-scope this finding"
    body = match.group(0)
    assert "_factory_seal" not in body, (
        "_new_capability now appears to check a factory seal of its own -- "
        "the disclosed gap may have been silently repaired; if so this "
        "should be reflected in a contract update, not a silent source change"
    )


# ---------------------------------------------------------------------------
# Group 12 — no-second-trust-root / no-generic-broker for the three-family
# cluster in aggregate (row 39's specific concern), independently checked.
# ---------------------------------------------------------------------------


def test_three_family_cluster_not_framed_as_a_second_broad_trust_root(section_30b_core: str) -> None:
    idx = section_30b_core.index("| 39 |")
    end = section_30b_core.index("\n", idx + 1)
    # find the full row (it may wrap across the pipe-delimited single line)
    row_end = section_30b_core.index("\n", idx)
    row = section_30b_core[idx:row_end]
    assert "second trust root" in row.lower() or "second general-purpose" in row.lower()
    assert "strict subset" in row or "never a union" in row


def test_req_147_reaffirms_single_trust_root_for_model_e(section_30b: str) -> None:
    idx = section_30b.index("HPAC-PAWA-HELPER-REQ-147")
    chunk = _norm(section_30b[idx: idx + 700])
    assert "trust root remains" in chunk
    assert "no independent root" in chunk or "introduces no independent" in chunk
