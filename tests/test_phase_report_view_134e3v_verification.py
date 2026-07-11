"""Phase 134E.3V — independent adversarial verification of Phase Report
View Composition (134E.3).

Does not trust 134E.3's own report, documentation, or its 88 tests as
sufficient evidence. These are fresh probes beyond that existing
coverage, including a regression test for one genuine BLOCKING defect
found and repaired during this verification phase:

1. Conditionally-missing-vs-not-applicable conflation: a category the
   extraction profile marks CONDITIONALLY_REQUIRED, and which the
   evidence record genuinely lacks (extraction diagnostic
   "conditionally_required_category_missing"), was composed identically
   to a category the profile marks NOT_APPLICABLE for the phase class
   (zero diagnostic, a mere FilteringDisclosure) -- both produced
   `applicability=NOT_APPLICABLE, completeness=COMPLETE`, silently
   discarding a real, disclosed extraction-level limitation (a
   Non-Strengthening violation: "conditionally missing" strengthened
   into "not applicable"). `missing_required_categories` remained
   non-empty in that state, directly self-contradicting an applicability
   claiming nothing was missing.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import subprocess
import sys
from types import MappingProxyType

import pytest

from pcae.core.canonical_engineering_evidence import (
    Applicability,
    CommitPushInfo,
    EvidenceIdentity,
    EvidencePhaseIdentity,
    EvidenceProvenanceRecord,
    FindingClassification,
    FindingRecord,
    GovernanceResultItem,
    LimitationItem,
    PhaseClass,
    REQUIRED_APPLICABILITY_CATEGORIES,
    RepairRecord,
    TestResultItem,
    UncertaintyItem,
)
from pcae.core.evidence_extraction import (
    EXTRACTION_CATEGORIES,
    ExtractionCompleteness,
    PROFILE_ID_OPERATOR_REPORT,
    PROFILE_ID_PHASE_REPORT,
    RequirementLevel,
    SelectedEvidenceItem,
    extract,
    get_profile,
)
from pcae.core import phase_report_view as prv
from pcae.core.phase_report_view import (
    PFR_SECTION_ORDER,
    PFRSectionId,
    SUPPORTED_VIEW_VERSIONS,
    SectionApplicability,
    SectionCompleteness,
    ViewCompleteness,
    compose_phase_report_view,
)

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from test_evidence_extraction_134e2 import (  # noqa: E402
    _content_for,
    _full_applicability,
    _identity,
    _minimal_complete_evidence,
)
from test_phase_report_view_134e3 import (  # noqa: E402
    _evidence_with_applicability,
    _view_for,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Assignment accounting with same ID but altered value
# ─────────────────────────────────────────────────────────────────────────────

def test_assignment_accounting_same_category_never_diverges_across_sections():
    # architectural_findings appears (by reference) in both Executive
    # Summary and Architectural Findings. Confirm both sections resolve
    # to the exact same underlying object -- there is no code path that
    # could let the "same" category diverge in value between sections,
    # since both sections read from the identical `selected` dict built
    # once per composition.
    _, view = _view_for(PhaseClass.ARCHITECTURE)
    exec_summary = next(s for s in view.sections if s.section_id == PFRSectionId.EXECUTIVE_SUMMARY)
    arch = next(s for s in view.sections if s.section_id == PFRSectionId.ARCHITECTURAL_FINDINGS)
    exec_group = next(g for g in exec_summary.evidence_groups if g.category == "architectural_findings")
    arch_group = next(g for g in arch.evidence_groups if g.category == "architectural_findings")
    assert exec_group.applicability == arch_group.applicability
    assert exec_group.finding_classifications == arch_group.finding_classifications
    assert exec_group.requirement_level == arch_group.requirement_level


# ─────────────────────────────────────────────────────────────────────────────
# 2. Unassigned required evidence hidden by duplicate reference
# ─────────────────────────────────────────────────────────────────────────────

def test_unassigned_required_evidence_not_hidden_by_duplicate_reference():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    forged = SelectedEvidenceItem(
        category="__forged__", source_evidence_id=res.source_evidence_id,
        value=("smuggled",), applicability=Applicability.PRESENT,
        requirement_level=RequirementLevel.REQUIRED, provenance=(),
        verification_state=None, uncertainty_refs=(), limitation_refs=(),
        selection_reason="forged",
    )
    bad_res = dataclasses.replace(
        res, selected_evidence=res.selected_evidence + (forged, forged),
    )
    view = compose_phase_report_view(bad_res)
    assert any(d.code == "unassigned_required_evidence" for d in view.diagnostics)
    all_categories = {g.category for s in view.sections for g in s.evidence_groups}
    assert "__forged__" not in all_categories
    assert view.completeness != ViewCompleteness.COMPLETE


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cross-section reuse with conflicting copies
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_section_reuse_no_conflicting_copies():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F-X", FindingClassification.BLOCKING, "issue", "component")
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_discovered=(finding,),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    exec_summary = next(s for s in view.sections if s.section_id == PFRSectionId.EXECUTIVE_SUMMARY)
    verif = next(s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS)
    exec_group = next(g for g in exec_summary.evidence_groups if g.category == "defects_discovered")
    verif_group = next(g for g in verif.evidence_groups if g.category == "defects_discovered")
    assert exec_group.finding_classifications == verif_group.finding_classifications == ("blocking",)
    assert exec_group.is_primary is False
    assert verif_group.is_primary is True


# ─────────────────────────────────────────────────────────────────────────────
# 4-5. Status-only / near-status-only summary marked complete attempt
# ─────────────────────────────────────────────────────────────────────────────

def test_status_only_summary_rejected_by_construction():
    # A literal status-only record (missing objective/engineering_actions
    # entirely) cannot even be constructed -- CanonicalEngineeringEvidence
    # requires both non-empty, and engineering_actions is REQUIRED at
    # profile level for every phase class (a NOT_APPLICABLE disposition
    # there fails extraction as INVALID, never reaching a composed view).
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["engineering_actions"] = Applicability.NOT_APPLICABLE
    ev = _evidence_with_applicability(PhaseClass.IMPLEMENTATION, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res.completeness == ExtractionCompleteness.INVALID
    with pytest.raises(ValueError):
        compose_phase_report_view(res)


def test_near_status_only_summary_completeness_documented():
    # NON-BLOCKING observation (documented, not repaired): every REQUIRED/
    # CONDITIONALLY_REQUIRED category can be satisfied with genuinely
    # trivial, boilerplate free-text content (a one-word objective, a
    # single generic finding) and the Executive Summary section still
    # reports COMPLETE. Composition proves category *coverage*, never
    # semantic *substance* -- judging substance would require inventing
    # a narrative/semantic conclusion, which composition's own Non-Goals
    # explicitly forbid. This is an inherent structural limitation of a
    # category-level completeness model, not a composition defect.
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    profile = get_profile(PROFILE_ID_PHASE_REPORT)
    for category in REQUIRED_APPLICABILITY_CATEGORIES:
        requirement = profile.requirement_for(category, PhaseClass.IMPLEMENTATION)
        if requirement in (RequirementLevel.REQUIRED, RequirementLevel.CONDITIONALLY_REQUIRED):
            app[category] = Applicability.PRESENT
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        objective="minimal complete objective", engineering_actions=("did the work",),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res.completeness == ExtractionCompleteness.COMPLETE
    view = compose_phase_report_view(res)
    exec_summary = next(s for s in view.sections if s.section_id == PFRSectionId.EXECUTIVE_SUMMARY)
    # Documented, not asserted-as-bug: category coverage alone drives
    # completeness, exactly as designed.
    assert exec_summary.completeness == SectionCompleteness.COMPLETE
    assert len(exec_summary.evidence_groups) >= 4


# ─────────────────────────────────────────────────────────────────────────────
# 6-7. Empty architectural/verification findings in the matching phase class
# ─────────────────────────────────────────────────────────────────────────────

def test_empty_architectural_findings_in_architecture_phase_rejected():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["architectural_findings"] = Applicability.NOT_APPLICABLE
    ev = _evidence_with_applicability(PhaseClass.ARCHITECTURE, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res.completeness == ExtractionCompleteness.INVALID
    with pytest.raises(ValueError):
        compose_phase_report_view(res)


def test_empty_verification_findings_in_verification_phase_rejected():
    # verification_findings is one of CanonicalEngineeringEvidence's own
    # phase-class-mandatory-present categories for VERIFICATION -- even
    # stronger than the architectural_findings case above, CEE itself
    # refuses to finalize such a record, so composition never even sees
    # it (fail-closed one layer earlier than extraction).
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["verification_findings"] = Applicability.NOT_APPLICABLE
    with pytest.raises(ValueError, match="verification_findings"):
        _evidence_with_applicability(PhaseClass.VERIFICATION, app)


# ─────────────────────────────────────────────────────────────────────────────
# 8-9. Repaired BLOCKING history collapse attempt / partial repair
# represented as resolved attempt
# ─────────────────────────────────────────────────────────────────────────────

def test_repaired_blocking_history_not_collapsed():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["defects_repaired"] = Applicability.PRESENT
    original = FindingRecord("F-B1", FindingClassification.BLOCKING, "issue", "component")
    repair = RepairRecord(original, "fixed", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_repaired=(repair,),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS)
    group = next(g for g in section.evidence_groups if g.category == "defects_repaired")
    # Both the original BLOCKING state and the resulting CONFIRMED status
    # must remain visible -- collapsing to only "confirmed" would hide
    # that a BLOCKING defect ever existed.
    assert "blocking" in group.finding_classifications
    assert "confirmed" in group.finding_classifications
    assert len(group.finding_classifications) == 2


def test_partial_repair_not_represented_as_fully_resolved():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["defects_discovered"] = Applicability.PRESENT
    app["defects_repaired"] = Applicability.PRESENT
    unresolved = FindingRecord("F-B2", FindingClassification.NON_BLOCKING, "residual", "component")
    original = FindingRecord("F-B3", FindingClassification.BLOCKING, "main issue", "component")
    repair = RepairRecord(original, "partially fixed", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app,
        defects_discovered=(unresolved,), defects_repaired=(repair,),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS)
    discovered_group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    repaired_group = next(g for g in section.evidence_groups if g.category == "defects_repaired")
    # The residual NON_BLOCKING finding must remain visible alongside the
    # repaired BLOCKING one -- a reader must see the repair is partial.
    assert "non_blocking" in discovered_group.finding_classifications
    assert "blocking" in repaired_group.finding_classifications
    assert "confirmed" in repaired_group.finding_classifications


# ─────────────────────────────────────────────────────────────────────────────
# 10. Governance warning converted to pass attempt
# ─────────────────────────────────────────────────────────────────────────────

def test_governance_warning_never_converted_to_pass():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        governance_results=(GovernanceResultItem("pcae_check", "warning: stale"),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    compose_phase_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "governance_results")
    assert selected.value[0].status == "warning: stale"
    assert selected.value[0].status != "passed"


# ─────────────────────────────────────────────────────────────────────────────
# 11. One-failure test suite converted to pass attempt
# ─────────────────────────────────────────────────────────────────────────────

def test_one_failure_suite_never_converted_to_pass():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        test_results=(TestResultItem("fast_green", "4389 passed, 1 failed", "failed"),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    compose_phase_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "test_results")
    assert selected.value[0].status == "failed"
    assert "1 failed" in selected.value[0].result


# ─────────────────────────────────────────────────────────────────────────────
# 12-13. Missing no-go evidence / boundary-no-go conflation (regression for
# the BLOCKING defect this phase repaired)
# ─────────────────────────────────────────────────────────────────────────────

def test_missing_no_go_evidence_not_composed_as_not_applicable():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    diag = [d for d in res.diagnostics if d.category == "no_go_confirmations"]
    assert diag and diag[0].code == "conditionally_required_category_missing"
    view = compose_phase_report_view(res)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.NO_GO_CONFIRMATION)
    assert section.applicability != SectionApplicability.NOT_APPLICABLE
    assert section.applicability == SectionApplicability.UNAVAILABLE_WITH_DISCLOSURE
    assert section.completeness == SectionCompleteness.COMPLETE_WITH_LIMITATIONS
    assert "no_go_confirmations" in section.missing_required_categories


def test_boundary_confirmation_distinct_from_no_go():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        no_go_confirmations=("no execution capability introduced",),
        architectural_boundary_confirmations=("determinism preserved",),
        applicability=MappingProxyType({
            **_full_applicability(PhaseClass.IMPLEMENTATION),
            "no_go_confirmations": Applicability.PRESENT,
            "architectural_boundary_confirmations": Applicability.PRESENT,
        }),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    no_go = next(s for s in view.sections if s.section_id == PFRSectionId.NO_GO_CONFIRMATION)
    boundary = next(
        s for s in view.sections
        if s.section_id == PFRSectionId.ARCHITECTURAL_BOUNDARY_CONFIRMATION
    )
    no_go_cats = {g.category for g in no_go.evidence_groups}
    boundary_cats = {g.category for g in boundary.evidence_groups}
    assert no_go_cats == {"no_go_confirmations"}
    assert "architectural_boundary_confirmations" in boundary_cats
    assert "no_go_confirmations" not in boundary_cats


# ─────────────────────────────────────────────────────────────────────────────
# 14. Stale track-progress evidence
# ─────────────────────────────────────────────────────────────────────────────

def test_stale_track_progress_disclosed_not_invented():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, track_progress="incomplete/stale evidence only",
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.TRACK_PROGRESS)
    sel = next(s for s in res.selected_evidence if s.category == "track_progress")
    assert sel.value == "incomplete/stale evidence only"
    # No roadmap invention: composition carries only the extracted string,
    # never generates its own track-progress text.
    assert "track_progress" in [g.category for g in section.evidence_groups]


# ─────────────────────────────────────────────────────────────────────────────
# 15. Next-phase inference attempt
# ─────────────────────────────────────────────────────────────────────────────

def test_next_phase_never_inferred_from_numbering():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        recommended_next_phase="explicitly no next phase recommended",
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    sel = next(s for s in res.selected_evidence if s.category == "recommended_next_phase")
    assert sel.value == "explicitly no next phase recommended"
    assert "999Y" not in sel.value  # composition invents nothing beyond the extracted string


# ─────────────────────────────────────────────────────────────────────────────
# 16. Planning-phase substantive completeness (revisit)
# ─────────────────────────────────────────────────────────────────────────────

def test_planning_phase_substantive_completeness_revisited():
    app = _full_applicability(PhaseClass.PLANNING)
    profile = get_profile(PROFILE_ID_PHASE_REPORT)
    for category in REQUIRED_APPLICABILITY_CATEGORIES:
        requirement = profile.requirement_for(category, PhaseClass.PLANNING)
        if requirement in (RequirementLevel.REQUIRED, RequirementLevel.CONDITIONALLY_REQUIRED):
            app[category] = Applicability.PRESENT
    ev = _evidence_with_applicability(PhaseClass.PLANNING, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res.completeness == ExtractionCompleteness.COMPLETE
    view = compose_phase_report_view(res)
    assert view.completeness == ViewCompleteness.COMPLETE
    arch = next(s for s in view.sections if s.section_id == PFRSectionId.ARCHITECTURAL_FINDINGS)
    # PFR-001/133B: Architectural Findings is mandatory ("plan rationale")
    # for Prototype Plan phases -- confirm it is genuinely populated, not
    # silently not-applicable, using only the existing category model.
    assert arch.applicability == SectionApplicability.MATERIALLY_POPULATED
    impl = next(s for s in view.sections if s.section_id == PFRSectionId.IMPLEMENTATION_FINDINGS)
    assert impl.applicability == SectionApplicability.NOT_APPLICABLE


# ─────────────────────────────────────────────────────────────────────────────
# 17-18. View completeness higher than extraction / incomplete mandatory
# section with complete view attempt
# ─────────────────────────────────────────────────────────────────────────────

def test_view_completeness_never_exceeds_extraction():
    for phase_class in PhaseClass:
        res, view = _view_for(phase_class)
        rank = {"complete": 0, "complete_with_limitations": 1, "incomplete": 2, "invalid": 3}
        assert rank[view.completeness.value] >= rank[res.completeness.value]


def test_incomplete_mandatory_section_prevents_complete_view():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.TECHNICAL_DEBT_REVIEW)
    assert section.completeness == SectionCompleteness.INCOMPLETE
    assert view.completeness != ViewCompleteness.COMPLETE


# ─────────────────────────────────────────────────────────────────────────────
# 19-20. Cross-section uncertainty loss / global limitation loss
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_section_uncertainty_not_lost():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert "technical_debt_reviewed" in view.cross_section_uncertainty
    section = next(s for s in view.sections if s.section_id == PFRSectionId.TECHNICAL_DEBT_REVIEW)
    assert "technical_debt_reviewed" in section.uncertainty_categories or section.missing_required_categories


def test_global_limitation_not_lost():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["notable_engineering_knowledge"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        limitations=(LimitationItem(
            category="notable_engineering_knowledge", description="unavailable this phase",
            affected_evidence=("notable_engineering_knowledge",),
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert "notable_engineering_knowledge" in view.cross_section_limitation


# ─────────────────────────────────────────────────────────────────────────────
# 21. Filtering disclosure masking a required omission
# ─────────────────────────────────────────────────────────────────────────────

def test_filtering_disclosure_does_not_mask_required_omission():
    # technical_debt_reviewed is REQUIRED (never OPTIONAL/NOT_APPLICABLE)
    # at profile level for every phase class -- confirm a genuinely
    # missing required category never shows up as a mere (non-material)
    # filtering disclosure, which would wrongly suggest the absence was
    # an intentional, low-stakes exclusion rather than a real gap.
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["technical_debt_reviewed"] = Applicability.NOT_APPLICABLE
    ev = _evidence_with_applicability(PhaseClass.IMPLEMENTATION, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res.completeness == ExtractionCompleteness.INVALID
    assert "technical_debt_reviewed" not in [
        fd.excluded_category for fd in res.filtering_disclosures
    ]
    with pytest.raises(ValueError):
        compose_phase_report_view(res)


# ─────────────────────────────────────────────────────────────────────────────
# 22. Provenance detachment
# ─────────────────────────────────────────────────────────────────────────────

def test_provenance_remains_attached_not_detached():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        provenance=(EvidenceProvenanceRecord(
            covers="test_results", source_artifact="pytest-output.txt",
            source_command="pytest", source_phase_id="134E.3",
            derivation_path="ci", verification_state="verified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.TEST_RESULTS)
    assert "test_results" in section.provenance_categories
    sel = next(s for s in res.selected_evidence if s.category == "test_results")
    assert sel.provenance and sel.provenance[0].source_artifact == "pytest-output.txt"


# ─────────────────────────────────────────────────────────────────────────────
# 23-24. Duplicate section identity / invalid section order (structural
# guarantee re-derived independently)
# ─────────────────────────────────────────────────────────────────────────────

def test_duplicate_section_identity_impossible_via_entry_point():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    ids = [s.section_id for s in view.sections]
    assert len(ids) == len(set(ids)) == 13


def test_invalid_section_order_impossible_via_entry_point():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert [s.section_id for s in view.sections] == list(PFR_SECTION_ORDER)
    assert [s.order for s in view.sections] == list(range(1, 14))


def test_direct_dataclass_bypass_documented_not_a_composition_defect():
    # NON-BLOCKING observation: PhaseReportView/SectionRecord, like
    # ExtractionResult and CanonicalEngineeringEvidence before them,
    # perform no self-validation against direct dataclass construction
    # bypassing the sole entry point (compose_phase_report_view). This
    # matches the established convention throughout this lineage
    # (invariants enforced by the entry-point function, not the raw
    # dataclass constructor) -- not a new defect introduced by 134E.3.
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    sec = view.sections[0]
    bypassed = prv.PhaseReportView(**{**view.__dict__, "sections": (sec, sec)})
    assert len(bypassed.sections) == 2  # documented, not fixed


# ─────────────────────────────────────────────────────────────────────────────
# 25-26. Wrong extraction profile / unsupported view version
# ─────────────────────────────────────────────────────────────────────────────

def test_wrong_extraction_profile_fails_closed():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    with pytest.raises(ValueError, match=PROFILE_ID_PHASE_REPORT):
        compose_phase_report_view(res)


def test_unsupported_view_version_fails_closed():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    with pytest.raises(ValueError):
        compose_phase_report_view(res, view_version="0.9-forged")
    assert "0.9-forged" not in SUPPORTED_VIEW_VERSIONS


# ─────────────────────────────────────────────────────────────────────────────
# 27. Cross-process byte determinism
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_process_byte_determinism():
    script = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "from test_evidence_extraction_134e2 import _minimal_complete_evidence; "
        "from pcae.core.canonical_engineering_evidence import PhaseClass; "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_PHASE_REPORT; "
        "from pcae.core.phase_report_view import compose_phase_report_view; "
        "import json; "
        "ev = _minimal_complete_evidence(PhaseClass.VERIFICATION); "
        "res = extract(ev, PROFILE_ID_PHASE_REPORT); "
        "view = compose_phase_report_view(res); "
        "print(json.dumps(view.to_dict(), sort_keys=True))"
    ) % ("src", str(__import__("pathlib").Path(__file__).resolve().parent))
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    proc2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    assert proc1.stdout == proc2.stdout


# ─────────────────────────────────────────────────────────────────────────────
# 28-29. Unknown future-agent independence / synthetic future-transport
# independence
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_future_agent_independence():
    # Composition takes no agent/model identity parameter at all --
    # confirm the function signature itself has no such parameter, so a
    # hypothetical future agent identity cannot even be threaded through.
    sig = inspect.signature(compose_phase_report_view)
    assert set(sig.parameters.keys()) == {"result", "view_version"}


def test_synthetic_future_transport_independence():
    # Compose successfully with zero transport-related environment state
    # and zero transport imports anywhere reachable from this module.
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert "transport" not in view.to_dict()
    source = inspect.getsource(prv)
    assert "sink" not in source.lower() and "chat_id" not in source.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 30. No active lifecycle, filesystem, network, rendering, or delivery
# side effects
# ─────────────────────────────────────────────────────────────────────────────

def test_no_filesystem_network_rendering_delivery_side_effects(monkeypatch):
    def _forbidden(*a, **kw):
        raise AssertionError("phase_report_view must not touch the filesystem")
    monkeypatch.setattr("builtins.open", _forbidden)
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    view.to_dict()
    view.compute_digest()


def test_no_active_lifecycle_fresh_full_tree_scan():
    # 134E.5 note: Rendering (``pcae.core.rendering``) is an expected,
    # deliberately isolated *new* consumer of this module -- the next
    # layer in the same disconnected architecture (View Composition ->
    # Rendering), not an active-lifecycle one.
    import pathlib
    src_root = pathlib.Path(prv.__file__).resolve().parent.parent
    _EXPECTED_ISOLATED_CONSUMERS = frozenset({"phase_report_view.py", "rendering.py"})
    for path in src_root.rglob("*.py"):
        if path.name in _EXPECTED_ISOLATED_CONSUMERS:
            continue
        if "test" in str(path):
            continue
        text = path.read_text()
        assert "phase_report_view" not in text, f"{path} unexpectedly references phase_report_view"


# ─────────────────────────────────────────────────────────────────────────────
# Additional authority-boundary re-confirmations
# ─────────────────────────────────────────────────────────────────────────────

def test_composition_never_mutates_extraction_result():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    digest_before = res.compute_digest()
    compose_phase_report_view(res)
    compose_phase_report_view(res)
    assert res.compute_digest() == digest_before


def test_composition_never_mutates_source_evidence():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    digest_before = ev.compute_digest()
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    compose_phase_report_view(res)
    assert ev.compute_digest() == digest_before


def test_no_phase_completion_or_delivery_authority_claimed():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    field_names = {f.name for f in dataclasses.fields(type(view))}
    assert "delivery_status" not in field_names
    assert "phase_completion_authority" not in field_names
    assert view.report_status == "composed"


def test_digest_excludes_rendering_and_delivery_state():
    res, view1 = _view_for(PhaseClass.IMPLEMENTATION)
    view2 = compose_phase_report_view(res)
    assert view1.compute_digest() == view2.compute_digest()
    d = view1.to_dict()
    for forbidden_key in ("delivery", "rendered", "markdown", "html", "sink"):
        assert forbidden_key not in d
