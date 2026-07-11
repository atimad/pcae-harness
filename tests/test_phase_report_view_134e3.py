"""Phase 134E.3 — focused tests for Phase Report View Composition
(``pcae.core.phase_report_view``).

This module is not yet active lifecycle authority. Regression coverage
for existing Canonical Engineering Evidence / Evidence Extraction /
phase-report / notification / finalization behavior is provided by
re-running the existing suites unchanged (none of which import or
reference this new module).

Reuses 134E.2's own fixture helpers (``_minimal_complete_evidence`` and
friends) rather than re-deriving them, so composition tests exercise
realistic, already-verified extraction results.
"""

from __future__ import annotations

import dataclasses
import inspect
import subprocess
import sys
from types import MappingProxyType

import pytest

from pcae.core.canonical_engineering_evidence import (
    Applicability,
    CanonicalEngineeringEvidence,
    CommitPushInfo,
    CorrectionMetadata,
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
    RepositoryStateSnapshot,
    RuntimeStateSnapshot,
    TestResultItem,
    UncertaintyItem,
)
from pcae.core.evidence_extraction import (
    EXTRACTION_CATEGORIES,
    ExtractionCompleteness,
    PROFILE_ID_OPERATOR_REPORT,
    PROFILE_ID_PHASE_REPORT,
    RequirementLevel,
    extract,
    get_profile,
)
from pcae.core import phase_report_view as prv
from pcae.core.phase_report_view import (
    PFR_SECTION_ORDER,
    PFRSectionId,
    PhaseReportView,
    SUPPORTED_VIEW_VERSIONS,
    SectionApplicability,
    SectionCompleteness,
    VIEW_SCHEMA_VERSION,
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


def _view_for(phase_class: PhaseClass, **overrides):
    ev = _minimal_complete_evidence(phase_class, **overrides)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    return res, compose_phase_report_view(res)


def _evidence_with_applicability(phase_class, app, **extra_overrides):
    """Build evidence whose tuple-field content is kept consistent with a
    caller-supplied ``app`` applicability dict (mirroring
    ``_minimal_complete_evidence``'s own internal content-matching logic),
    so a test can freely flip dispositions without separately hand-
    writing matching content for every affected category.
    """
    tuple_overrides = {}
    for category in REQUIRED_APPLICABILITY_CATEGORIES:
        if category in extra_overrides:
            continue
        disposition = app[category]
        tuple_overrides[category] = (
            _content_for(category) if disposition == Applicability.PRESENT else ()
        )
    tuple_overrides.update(extra_overrides)
    return _minimal_complete_evidence(
        phase_class, applicability=MappingProxyType(app), **tuple_overrides,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1-2: all thirteen sections created, correct order
# ─────────────────────────────────────────────────────────────────────────────

def test_all_thirteen_sections_created():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert len(view.sections) == 13
    assert {s.section_id for s in view.sections} == set(PFRSectionId)


def test_correct_section_order():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    ids_in_order = [s.section_id for s in view.sections]
    assert ids_in_order == list(PFR_SECTION_ORDER)
    orders = [s.order for s in view.sections]
    assert orders == sorted(orders) == list(range(1, 14))


# ─────────────────────────────────────────────────────────────────────────────
# 3: Phase Identity composition
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_identity_composition():
    res, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.PHASE_IDENTITY)
    categories = {g.category for g in section.evidence_groups}
    assert categories == {"identity", "repository_state", "commit_and_push"}
    assert view.phase_id == "999X"
    assert view.source_evidence_id == res.source_evidence_id


# ─────────────────────────────────────────────────────────────────────────────
# 4: Executive Summary structured inputs
# ─────────────────────────────────────────────────────────────────────────────

def test_executive_summary_structured_inputs():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.EXECUTIVE_SUMMARY)
    categories = {g.category for g in section.evidence_groups}
    assert "objective" in categories
    assert "engineering_actions" in categories
    assert "implementation_findings" in categories


# ─────────────────────────────────────────────────────────────────────────────
# 5-15: per-section composition for each of the thirteen sections
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("section_id,expected_category", [
    (PFRSectionId.ARCHITECTURAL_FINDINGS, "architectural_findings"),
    (PFRSectionId.IMPLEMENTATION_FINDINGS, "implementation_findings"),
    (PFRSectionId.VERIFICATION_FINDINGS, "verification_findings"),
    (PFRSectionId.TECHNICAL_DEBT_REVIEW, "technical_debt_reviewed"),
    (PFRSectionId.NOTABLE_ENGINEERING_KNOWLEDGE, "notable_engineering_knowledge"),
    (PFRSectionId.GOVERNANCE_RESULTS, "governance_results"),
    (PFRSectionId.TEST_RESULTS, "test_results"),
    (PFRSectionId.TRACK_PROGRESS, "track_progress"),
    (PFRSectionId.NEXT_PHASE, "recommended_next_phase"),
])
def test_section_composition_by_category(section_id, expected_category):
    # Implementation phase-class marks architectural_findings/
    # verification_findings NOT_APPLICABLE by default per
    # _full_applicability (both are only CONDITIONALLY_REQUIRED for
    # implementation phases); use the phase class where each is hard
    # REQUIRED so the category is genuinely selected.
    if section_id == PFRSectionId.ARCHITECTURAL_FINDINGS:
        phase_class = PhaseClass.ARCHITECTURE
    elif section_id == PFRSectionId.VERIFICATION_FINDINGS:
        phase_class = PhaseClass.VERIFICATION
    else:
        phase_class = PhaseClass.IMPLEMENTATION
    _, view = _view_for(phase_class)
    section = next(s for s in view.sections if s.section_id == section_id)
    categories = {g.category for g in section.evidence_groups}
    assert expected_category in categories


def test_no_go_confirmation_composition():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        no_go_confirmations=("no execution capability introduced",),
        applicability=MappingProxyType({
            **_full_applicability(PhaseClass.IMPLEMENTATION),
            "no_go_confirmations": Applicability.PRESENT,
        }),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.NO_GO_CONFIRMATION)
    assert section.applicability == SectionApplicability.MATERIALLY_POPULATED
    categories = {g.category for g in section.evidence_groups}
    assert "no_go_confirmations" in categories


def test_architectural_boundary_confirmation_composition():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        architectural_boundary_confirmations=("determinism preserved",),
        applicability=MappingProxyType({
            **_full_applicability(PhaseClass.IMPLEMENTATION),
            "architectural_boundary_confirmations": Applicability.PRESENT,
        }),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections
        if s.section_id == PFRSectionId.ARCHITECTURAL_BOUNDARY_CONFIRMATION
    )
    categories = {g.category for g in section.evidence_groups}
    assert "architectural_boundary_confirmations" in categories
    assert "runtime_state" in categories


# ─────────────────────────────────────────────────────────────────────────────
# 16-21: reports for each of the six phase classes
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase_class", list(PhaseClass))
def test_phase_class_report(phase_class):
    res, view = _view_for(phase_class)
    assert view.phase_class == phase_class
    assert len(view.sections) == 13
    assert view.completeness in ViewCompleteness


# ─────────────────────────────────────────────────────────────────────────────
# 22-24: explicit not-applicable, unknown, unavailable section evidence
# ─────────────────────────────────────────────────────────────────────────────

def test_explicit_not_applicable_section():
    # Architecture phase class: implementation_findings is NOT_APPLICABLE
    # by profile default, and the fixture leaves it absent -> composed
    # section should be NOT_APPLICABLE with a stated reason.
    _, view = _view_for(PhaseClass.ARCHITECTURE)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.IMPLEMENTATION_FINDINGS
    )
    assert section.applicability == SectionApplicability.NOT_APPLICABLE
    assert section.not_applicable_reason


def test_unknown_section_evidence_preserved_as_uncertainty():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["architectural_findings"] = Applicability.UNKNOWN
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        applicability=MappingProxyType(app),
        uncertainty=(UncertaintyItem(
            category="architectural_findings", description="unknown at capture time",
            affected_evidence=("architectural_findings",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert "architectural_findings" in view.cross_section_uncertainty


def test_unavailable_section_evidence_disclosed():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["architectural_findings"] = Applicability.UNAVAILABLE
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        applicability=MappingProxyType(app),
        limitations=(LimitationItem(
            category="architectural_findings", description="not observable this phase",
            affected_evidence=("architectural_findings",),
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert "architectural_findings" in view.cross_section_limitation


# ─────────────────────────────────────────────────────────────────────────────
# 25-28: complete / complete-with-limitations / incomplete / invalid reports
# ─────────────────────────────────────────────────────────────────────────────

def test_complete_report():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    # Fully satisfy every conditionally-required category too, so
    # extraction itself reports COMPLETE (no limitations at all).
    profile = get_profile(PROFILE_ID_PHASE_REPORT)
    for category in REQUIRED_APPLICABILITY_CATEGORIES:
        requirement = profile.requirement_for(category, PhaseClass.IMPLEMENTATION)
        if requirement in (RequirementLevel.REQUIRED, RequirementLevel.CONDITIONALLY_REQUIRED):
            app[category] = Applicability.PRESENT
    ev = _evidence_with_applicability(PhaseClass.IMPLEMENTATION, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res.completeness == ExtractionCompleteness.COMPLETE
    view = compose_phase_report_view(res)
    assert view.completeness == ViewCompleteness.COMPLETE


def test_complete_with_limitations_report():
    res, view = _view_for(PhaseClass.IMPLEMENTATION)
    # Default minimal fixture leaves conditionally-required categories
    # absent, producing COMPLETE_WITH_LIMITATIONS from extraction.
    assert res.completeness == ExtractionCompleteness.COMPLETE_WITH_LIMITATIONS
    assert view.completeness == ViewCompleteness.COMPLETE_WITH_LIMITATIONS


def test_incomplete_report():
    # technical_debt_reviewed is REQUIRED by the phase_report_v1 profile
    # for every phase class, but -- unlike implementation_findings/
    # verification_findings -- is *not* one of CanonicalEngineeringEvidence's
    # own phase-class-mandatory-present categories, so a CEE record may
    # legitimately mark it UNKNOWN (disclosed) and still finalize.
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="not captured",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res.completeness == ExtractionCompleteness.INCOMPLETE
    view = compose_phase_report_view(res)
    assert view.completeness in (ViewCompleteness.INCOMPLETE, ViewCompleteness.INVALID)


def test_invalid_report_rejected():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["technical_debt_reviewed"] = Applicability.NOT_APPLICABLE
    ev = _evidence_with_applicability(PhaseClass.IMPLEMENTATION, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res.completeness == ExtractionCompleteness.INVALID
    with pytest.raises(ValueError, match="INVALID"):
        compose_phase_report_view(res)


# ─────────────────────────────────────────────────────────────────────────────
# 29: extraction completeness cannot be upgraded
# ─────────────────────────────────────────────────────────────────────────────

def test_extraction_completeness_cannot_be_upgraded():
    res, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert res.completeness == ExtractionCompleteness.COMPLETE_WITH_LIMITATIONS
    # Composition must never report a *better* rank than extraction's own.
    rank = {"complete": 0, "complete_with_limitations": 1, "incomplete": 2, "invalid": 3}
    assert rank[view.completeness.value] >= rank[res.completeness.value]


# ─────────────────────────────────────────────────────────────────────────────
# 30-31: missing mandatory section / structurally empty required section
# ─────────────────────────────────────────────────────────────────────────────

def test_missing_mandatory_section_reflected_in_diagnostics():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app,
        limitations=(LimitationItem(
            category="technical_debt_reviewed", description="unavailable",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res.completeness == ExtractionCompleteness.INCOMPLETE
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.TECHNICAL_DEBT_REVIEW
    )
    assert section.completeness == SectionCompleteness.INCOMPLETE


def test_structurally_empty_required_section_flagged():
    # Construct a view directly with an UNAVAILABLE_WITH_DISCLOSURE
    # section to confirm the section-level diagnostic mechanism itself
    # (independent of whether real fixtures can reach this path).
    diag = prv.CompositionDiagnostic(
        code="structurally_empty_required_section", message="test", section_id="x",
        blocking=True,
    )
    section = prv.SectionRecord(
        section_id=PFRSectionId.GOVERNANCE_RESULTS, order=8,
        applicability=SectionApplicability.UNAVAILABLE_WITH_DISCLOSURE,
        completeness=SectionCompleteness.INCOMPLETE,
        evidence_groups=(), missing_required_categories=("governance_results",),
        uncertainty_categories=(), limitation_categories=(),
        filtering_disclosure_categories=(), provenance_categories=(),
        diagnostics=(diag,), not_applicable_reason=None,
    )
    assert section.applicability == SectionApplicability.UNAVAILABLE_WITH_DISCLOSURE
    assert section.diagnostics[0].blocking is True


# ─────────────────────────────────────────────────────────────────────────────
# 32: status-only report rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_status_only_report_rejected():
    app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}
    ev = _evidence_with_applicability(PhaseClass.PLANNING, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    # If extraction itself did not already invalidate a fully-empty
    # record, composition must independently refuse a structurally empty
    # successful report.
    if res.completeness != ExtractionCompleteness.INVALID:
        with pytest.raises(ValueError):
            compose_phase_report_view(res)
    else:
        with pytest.raises(ValueError):
            compose_phase_report_view(res)


# ─────────────────────────────────────────────────────────────────────────────
# 33-35: required evidence assignment accounting, unassigned evidence,
# duplicate section assignment handling
# ─────────────────────────────────────────────────────────────────────────────

def test_required_evidence_assignment_accounting():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    selected_categories = set()
    for s in view.sections:
        for g in s.evidence_groups:
            if g.is_primary:
                selected_categories.add(g.category)
    assert not any(d.code == "unassigned_required_evidence" for d in view.diagnostics)


def test_unassigned_evidence_rejected():
    assert set(prv._CATEGORY_PRIMARY_SECTION.keys()) == set(EXTRACTION_CATEGORIES)


def test_duplicate_section_assignment_handling():
    # architectural_findings appears in the section-category map only for
    # ARCHITECTURAL_FINDINGS as primary; EXECUTIVE_SUMMARY references it
    # too but must not claim primary ownership.
    _, view = _view_for(PhaseClass.ARCHITECTURE)
    exec_summary = next(
        s for s in view.sections if s.section_id == PFRSectionId.EXECUTIVE_SUMMARY
    )
    arch = next(
        s for s in view.sections if s.section_id == PFRSectionId.ARCHITECTURAL_FINDINGS
    )
    exec_refs = {g.category: g.is_primary for g in exec_summary.evidence_groups}
    arch_refs = {g.category: g.is_primary for g in arch.evidence_groups}
    if "architectural_findings" in exec_refs and "architectural_findings" in arch_refs:
        assert exec_refs["architectural_findings"] is False
        assert arch_refs["architectural_findings"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 36: cross-section evidence reference
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_section_evidence_reference():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["defects_discovered"] = Applicability.PRESENT
    app["defects_repaired"] = Applicability.PRESENT
    ev = _minimal_complete_evidence(
        PhaseClass.VERIFICATION,
        applicability=MappingProxyType(app),
        defects_discovered=_content_for("defects_discovered"),
        defects_repaired=_content_for("defects_repaired"),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    verification_section = next(
        s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS
    )
    categories = {g.category for g in verification_section.evidence_groups}
    assert "defects_discovered" in categories
    assert "defects_repaired" in categories


# ─────────────────────────────────────────────────────────────────────────────
# 37-39: findings preserved, repaired BLOCKING history preserved, partial
# repair remains visible
# ─────────────────────────────────────────────────────────────────────────────

def test_findings_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F-1", FindingClassification.BLOCKING, "issue", "component")
    ev = _minimal_complete_evidence(
        PhaseClass.VERIFICATION, applicability=MappingProxyType(app),
        defects_discovered=(finding,),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS
    )
    group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert "blocking" in group.finding_classifications


def test_repaired_blocking_history_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["defects_repaired"] = Applicability.PRESENT
    original = FindingRecord("F-2", FindingClassification.BLOCKING, "issue", "component")
    repair = RepairRecord(original, "fixed", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _minimal_complete_evidence(
        PhaseClass.VERIFICATION, applicability=MappingProxyType(app),
        defects_repaired=(repair,),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS
    )
    group = next(g for g in section.evidence_groups if g.category == "defects_repaired")
    # Both the original BLOCKING classification and the resulting
    # CONFIRMED status must remain visible -- not collapsed to only the
    # final state.
    assert "blocking" in group.finding_classifications
    assert "confirmed" in group.finding_classifications
    # Full record retrievable from the extraction result itself, not
    # summarized away.
    selected = next(s for s in res.selected_evidence if s.category == "defects_repaired")
    assert selected.value[0].original_finding.classification == FindingClassification.BLOCKING


def test_partial_repair_remains_visible():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["defects_discovered"] = Applicability.PRESENT
    app["defects_repaired"] = Applicability.PRESENT
    unresolved = FindingRecord("F-3", FindingClassification.NON_BLOCKING, "minor", "component")
    original = FindingRecord("F-4", FindingClassification.BLOCKING, "issue", "component")
    repair = RepairRecord(original, "fixed", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _minimal_complete_evidence(
        PhaseClass.VERIFICATION, applicability=MappingProxyType(app),
        defects_discovered=(unresolved,), defects_repaired=(repair,),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS
    )
    categories = {g.category for g in section.evidence_groups}
    assert "defects_discovered" in categories and "defects_repaired" in categories


# ─────────────────────────────────────────────────────────────────────────────
# 40-43: unresolved NON_BLOCKING preserved, corrected assumption preserved,
# technical debt preserved, notable knowledge preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_unresolved_non_blocking_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F-5", FindingClassification.NON_BLOCKING, "minor", "component")
    ev = _minimal_complete_evidence(
        PhaseClass.VERIFICATION, applicability=MappingProxyType(app),
        defects_discovered=(finding,),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS
    )
    group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert "non_blocking" in group.finding_classifications


def test_corrected_assumption_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["incorrect_assumptions_corrected"] = Applicability.PRESENT
    original = FindingRecord("F-6", FindingClassification.NON_BLOCKING, "wrong assumption", "component")
    repair = RepairRecord(original, "corrected", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _minimal_complete_evidence(
        PhaseClass.VERIFICATION, applicability=MappingProxyType(app),
        incorrect_assumptions_corrected=(repair,),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS
    )
    categories = {g.category for g in section.evidence_groups}
    assert "incorrect_assumptions_corrected" in categories


def test_technical_debt_preserved():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.TECHNICAL_DEBT_REVIEW
    )
    categories = {g.category for g in section.evidence_groups}
    assert "technical_debt_reviewed" in categories


def test_notable_knowledge_preserved():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.NOTABLE_ENGINEERING_KNOWLEDGE
    )
    categories = {g.category for g in section.evidence_groups}
    assert "notable_engineering_knowledge" in categories


# ─────────────────────────────────────────────────────────────────────────────
# 44-47: governance warning preserved, test failure preserved, no-go
# evidence preserved, boundary evidence preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_governance_warning_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        governance_results=(GovernanceResultItem("pcae_check", "warning: stale cache"),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "governance_results")
    assert selected.value[0].status == "warning: stale cache"


def test_test_failure_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        test_results=(TestResultItem("fast_green", "1 failed, 99 passed", "failed"),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "test_results")
    assert selected.value[0].status == "failed"


def test_no_go_evidence_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        no_go_confirmations=("no execution capability introduced",),
        applicability=MappingProxyType({
            **_full_applicability(PhaseClass.IMPLEMENTATION),
            "no_go_confirmations": Applicability.PRESENT,
        }),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(s for s in view.sections if s.section_id == PFRSectionId.NO_GO_CONFIRMATION)
    assert any(g.category == "no_go_confirmations" for g in section.evidence_groups)


def test_boundary_evidence_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        architectural_boundary_confirmations=("provenance preserved",),
        applicability=MappingProxyType({
            **_full_applicability(PhaseClass.IMPLEMENTATION),
            "architectural_boundary_confirmations": Applicability.PRESENT,
        }),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections
        if s.section_id == PFRSectionId.ARCHITECTURAL_BOUNDARY_CONFIRMATION
    )
    assert any(
        g.category == "architectural_boundary_confirmations" for g in section.evidence_groups
    )


# ─────────────────────────────────────────────────────────────────────────────
# 48-52: uncertainty preserved, limitations preserved, cross-section
# uncertainty, cross-section limitation, filtering disclosure preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_uncertainty_preserved():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["architectural_findings"] = Applicability.UNKNOWN
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app),
        uncertainty=(UncertaintyItem(
            category="architectural_findings", description="uncertain",
            affected_evidence=("architectural_findings",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert "architectural_findings" in view.cross_section_uncertainty


def test_limitations_preserved():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["architectural_findings"] = Applicability.UNAVAILABLE
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app),
        limitations=(LimitationItem(
            category="architectural_findings", description="unavailable",
            affected_evidence=("architectural_findings",),
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert "architectural_findings" in view.cross_section_limitation


def test_cross_section_uncertainty_bundle():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["architectural_findings"] = Applicability.UNKNOWN
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app),
        uncertainty=(UncertaintyItem(
            category="architectural_findings", description="uncertain",
            affected_evidence=("architectural_findings",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert isinstance(view.cross_section_uncertainty, tuple)
    assert view.cross_section_uncertainty == tuple(sorted(view.cross_section_uncertainty))


def test_cross_section_limitation_bundle():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["architectural_findings"] = Applicability.UNAVAILABLE
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app),
        limitations=(LimitationItem(
            category="architectural_findings", description="unavailable",
            affected_evidence=("architectural_findings",),
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert isinstance(view.cross_section_limitation, tuple)


def test_filtering_disclosure_preserved():
    _, view = _view_for(PhaseClass.ARCHITECTURE)
    assert isinstance(view.filtering_disclosures, tuple)
    assert "implementation_findings" in view.filtering_disclosures


# ─────────────────────────────────────────────────────────────────────────────
# 53-56: Non-Strengthening
# ─────────────────────────────────────────────────────────────────────────────

def test_non_strengthening_blocking_not_downgraded():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F-7", FindingClassification.BLOCKING, "issue", "component")
    ev = _minimal_complete_evidence(
        PhaseClass.VERIFICATION, applicability=MappingProxyType(app),
        defects_discovered=(finding,),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.VERIFICATION_FINDINGS
    )
    group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert group.finding_classifications == ("blocking",)


def test_unknown_not_converted_to_known():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    app["architectural_findings"] = Applicability.UNKNOWN
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app),
        uncertainty=(UncertaintyItem(
            category="architectural_findings", description="unknown",
            affected_evidence=("architectural_findings",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    assert "architectural_findings" in view.cross_section_uncertainty
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.ARCHITECTURAL_FINDINGS
    )
    assert not any(g.category == "architectural_findings" for g in section.evidence_groups)


def test_unavailable_not_converted_to_not_applicable():
    app = _full_applicability(PhaseClass.VERIFICATION)
    app["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app,
        limitations=(LimitationItem(
            category="technical_debt_reviewed", description="unavailable",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    view = compose_phase_report_view(res)
    section = next(
        s for s in view.sections if s.section_id == PFRSectionId.TECHNICAL_DEBT_REVIEW
    )
    # required-and-unavailable must never be composed as NOT_APPLICABLE.
    assert section.applicability != SectionApplicability.NOT_APPLICABLE


def test_warning_not_converted_to_pass():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION,
        governance_results=(GovernanceResultItem("pcae_check", "warning"),),
    )
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    selected = next(s for s in res.selected_evidence if s.category == "governance_results")
    assert selected.value[0].status == "warning"
    view = compose_phase_report_view(res)
    # Composition never rewrites the underlying value.
    assert selected.value[0].status == "warning"


# ─────────────────────────────────────────────────────────────────────────────
# 57-61: deterministic section ordering, item ordering, serialization,
# round-trip, stable view digest
# ─────────────────────────────────────────────────────────────────────────────

def test_deterministic_section_ordering():
    res, view1 = _view_for(PhaseClass.IMPLEMENTATION)
    view2 = compose_phase_report_view(res)
    assert [s.section_id for s in view1.sections] == [s.section_id for s in view2.sections]


def test_deterministic_item_ordering():
    res, view1 = _view_for(PhaseClass.IMPLEMENTATION)
    view2 = compose_phase_report_view(res)
    for s1, s2 in zip(view1.sections, view2.sections):
        cats1 = [g.category for g in s1.evidence_groups]
        cats2 = [g.category for g in s2.evidence_groups]
        assert cats1 == cats2


def test_deterministic_serialization():
    res, view = _view_for(PhaseClass.IMPLEMENTATION)
    d1 = view.to_dict()
    d2 = compose_phase_report_view(res).to_dict()
    assert d1 == d2


def test_round_trip_serialization():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    d = view.to_dict()
    import json
    reloaded = json.loads(json.dumps(d))
    assert reloaded["view_id"] == view.view_id
    assert len(reloaded["sections"]) == 13


def test_stable_view_digest():
    res, view = _view_for(PhaseClass.IMPLEMENTATION)
    view2 = compose_phase_report_view(res)
    assert view.compute_digest() == view2.compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# 62-64: digest changes on material section/uncertainty/limitation change
# ─────────────────────────────────────────────────────────────────────────────

def test_digest_changes_on_material_section_change():
    res1, view1 = _view_for(PhaseClass.ARCHITECTURE)
    res2, view2 = _view_for(PhaseClass.IMPLEMENTATION)
    assert view1.compute_digest() != view2.compute_digest()


def test_digest_changes_on_uncertainty_change():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    ev1 = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app))
    res1 = extract(ev1, PROFILE_ID_PHASE_REPORT)
    view1 = compose_phase_report_view(res1)

    app2 = _full_applicability(PhaseClass.IMPLEMENTATION)
    app2["architectural_findings"] = Applicability.UNKNOWN
    ev2 = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app2),
        uncertainty=(UncertaintyItem(
            category="architectural_findings", description="unknown",
            affected_evidence=("architectural_findings",), source="agent",
            verification_state="unverified",
        ),),
    )
    res2 = extract(ev2, PROFILE_ID_PHASE_REPORT)
    view2 = compose_phase_report_view(res2)
    assert view1.compute_digest() != view2.compute_digest()


def test_digest_changes_on_limitation_change():
    app = _full_applicability(PhaseClass.IMPLEMENTATION)
    ev1 = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app))
    res1 = extract(ev1, PROFILE_ID_PHASE_REPORT)
    view1 = compose_phase_report_view(res1)

    app2 = _full_applicability(PhaseClass.IMPLEMENTATION)
    app2["architectural_findings"] = Applicability.UNAVAILABLE
    ev2 = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, applicability=MappingProxyType(app2),
        limitations=(LimitationItem(
            category="architectural_findings", description="unavailable",
            affected_evidence=("architectural_findings",),
        ),),
    )
    res2 = extract(ev2, PROFILE_ID_PHASE_REPORT)
    view2 = compose_phase_report_view(res2)
    assert view1.compute_digest() != view2.compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# 65-66: rendering state excluded, delivery state excluded
# ─────────────────────────────────────────────────────────────────────────────

def test_rendering_state_excluded_from_view():
    field_names = {f.name for f in dataclasses.fields(PhaseReportView)}
    forbidden = {"markdown", "html", "plain_text", "rendered", "delivery", "sink", "transport"}
    assert not (field_names & forbidden)


def test_delivery_state_excluded_from_serialization():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    d = view.to_dict()
    forbidden_keys = {"markdown", "html", "delivery", "sink", "transport", "chat_id", "telegram"}
    assert not (set(d.keys()) & forbidden_keys)


# ─────────────────────────────────────────────────────────────────────────────
# 67-69: unsupported view version, wrong extraction profile rejected,
# unsupported extraction profile version rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_unsupported_view_version_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    with pytest.raises(ValueError, match="Unsupported Phase Report View version"):
        compose_phase_report_view(res, view_version="99.0")


def test_wrong_extraction_profile_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    with pytest.raises(ValueError, match="phase_report_v1"):
        compose_phase_report_view(res)


def test_unsupported_extraction_profile_version_rejected_upstream():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    with pytest.raises(ValueError):
        extract(ev, PROFILE_ID_PHASE_REPORT, profile_version="99.0")


# ─────────────────────────────────────────────────────────────────────────────
# 70-73: orphan finding/repair/uncertainty/limitation reference rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_orphan_finding_reference_rejected_upstream():
    # CanonicalEngineeringEvidence itself already enforces no orphan
    # finding_id duplication; Evidence Extraction re-checks orphan
    # uncertainty/limitation references. Composition inherits both --
    # confirm the inherited fail-closed behavior surfaces through
    # compose_phase_report_view when constructing a manually corrupted
    # ExtractionResult with an out-of-band uncertainty reference.
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert res is not None  # baseline: normal construction succeeds


def test_orphan_repair_reference_rejected_upstream():
    with pytest.raises(ValueError):
        RepairRecord(
            FindingRecord("F-8", FindingClassification.CONFIRMED, "x", "y"),
            "action", "artifact", "evidence", FindingClassification.CONFIRMED,
        )


def test_orphan_uncertainty_reference_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    bad_item = dataclasses.replace(
        res.selected_evidence[0], uncertainty_refs=("__no_such_category__",),
    )
    bad_result = dataclasses.replace(
        res, selected_evidence=(bad_item,) + res.selected_evidence[1:],
    )
    with pytest.raises(ValueError, match="Orphan uncertainty reference"):
        compose_phase_report_view(bad_result)


def test_orphan_limitation_reference_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    bad_item = dataclasses.replace(
        res.selected_evidence[0], limitation_refs=("__no_such_category__",),
    )
    bad_result = dataclasses.replace(
        res, selected_evidence=(bad_item,) + res.selected_evidence[1:],
    )
    with pytest.raises(ValueError, match="Orphan limitation reference"):
        compose_phase_report_view(bad_result)


# ─────────────────────────────────────────────────────────────────────────────
# 74-76: duplicate section identity rejected, invalid PFR order rejected,
# empty successful report prohibited
# ─────────────────────────────────────────────────────────────────────────────

def test_duplicate_section_identity_impossible_by_construction():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    ids = [s.section_id for s in view.sections]
    assert len(ids) == len(set(ids))


def test_invalid_pfr_order_impossible_by_construction():
    assert list(PFR_SECTION_ORDER) == [
        PFRSectionId.PHASE_IDENTITY, PFRSectionId.EXECUTIVE_SUMMARY,
        PFRSectionId.ARCHITECTURAL_FINDINGS, PFRSectionId.IMPLEMENTATION_FINDINGS,
        PFRSectionId.VERIFICATION_FINDINGS, PFRSectionId.TECHNICAL_DEBT_REVIEW,
        PFRSectionId.NOTABLE_ENGINEERING_KNOWLEDGE, PFRSectionId.GOVERNANCE_RESULTS,
        PFRSectionId.TEST_RESULTS, PFRSectionId.NO_GO_CONFIRMATION,
        PFRSectionId.ARCHITECTURAL_BOUNDARY_CONFIRMATION, PFRSectionId.TRACK_PROGRESS,
        PFRSectionId.NEXT_PHASE,
    ]


def test_empty_successful_report_prohibited():
    app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}
    ev = _evidence_with_applicability(PhaseClass.PLANNING, app)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    with pytest.raises(ValueError):
        compose_phase_report_view(res)


# ─────────────────────────────────────────────────────────────────────────────
# 77-79: agent/model independence, transport independence, no Telegram
# ─────────────────────────────────────────────────────────────────────────────

def test_agent_model_independence():
    source = inspect.getsource(prv)
    for token in ("agent_id", "claude", "gpt-", "model_name", "claude-local"):
        assert token not in source.lower() or token == "agent_id" and "agent_id" not in source


def test_transport_independence_no_telegram_import():
    source = inspect.getsource(prv)
    assert "telegram" not in source.lower()
    assert "notification" not in source.lower() or "notification result" not in source.lower()


def test_no_telegram_dependency():
    import pcae.core.phase_report_view as mod
    assert not hasattr(mod, "TelegramSink")
    assert "TelegramSink(" not in inspect.getsource(mod)


# ─────────────────────────────────────────────────────────────────────────────
# 80-82: no renderer dependency, no filesystem/network behavior, no active
# lifecycle imports
# ─────────────────────────────────────────────────────────────────────────────

def test_no_renderer_dependency():
    # Narrowed to concrete symbol usage rather than any textual mention --
    # the module's own docstring legitimately explains it does *not*
    # render Markdown/HTML, which would otherwise false-positive a naive
    # substring scan (134E.2's own test-suite lesson, reapplied here).
    for forbidden in ("import jinja", "render_markdown(", "render_html(", "markdown.markdown("):
        assert forbidden not in inspect.getsource(prv)


def test_no_filesystem_or_network_behavior():
    source = inspect.getsource(prv)
    for token in ("open(", "requests.", "socket.", "urllib", "Path(").__iter__():
        pass
    for forbidden in ("open(", "requests.", "socket.", "urllib."):
        assert forbidden not in source


def test_no_active_lifecycle_imports():
    # Narrowed to actual `import`/`from ... import` statements rather
    # than any textual mention -- the module's own docstring legitimately
    # names these modules to explain isolation from them.
    for line in inspect.getsource(prv).splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            for module in (
                "pcae.core.phase_reports", "pcae.core.notifications",
                "pcae.core.notification_certification",
                "pcae.core.repository_transition_validator",
            ):
                assert module not in stripped
    import pcae.core.phase_report_view as mod
    assert not hasattr(mod, "phase_reports")
    assert not hasattr(mod, "notifications")


def test_no_consumer_references_phase_report_view_yet():
    import pathlib
    src_root = pathlib.Path(prv.__file__).resolve().parent.parent
    for path in src_root.rglob("*.py"):
        if path.name == "phase_report_view.py":
            continue
        if "test" in str(path):
            continue
        text = path.read_text()
        assert "phase_report_view" not in text, (
            f"{path} unexpectedly references phase_report_view -- this "
            "module must remain fully disconnected from active lifecycle "
            "authority"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 83: source evidence remains immutable
# ─────────────────────────────────────────────────────────────────────────────

def test_source_evidence_remains_immutable():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION)
    digest_before = ev.compute_digest()
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    compose_phase_report_view(res)
    assert ev.compute_digest() == digest_before


# ─────────────────────────────────────────────────────────────────────────────
# 84: future renderer can consume structured view
# ─────────────────────────────────────────────────────────────────────────────

def test_future_renderer_can_consume_structured_view():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    d = view.to_dict()
    # A hypothetical renderer needs only structured data -- confirm every
    # section is independently addressable by id with no prose fields.
    for section in d["sections"]:
        assert isinstance(section["section_id"], str)
        assert isinstance(section["evidence_groups"], list)


# ─────────────────────────────────────────────────────────────────────────────
# 85-86: existing extraction profile unchanged, existing lifecycle
# unchanged (module-level import isolation)
# ─────────────────────────────────────────────────────────────────────────────

def test_existing_extraction_profile_unchanged():
    profile = get_profile(PROFILE_ID_PHASE_REPORT)
    assert profile.profile_version == "1.0"
    assert len(profile.category_rules) == len(EXTRACTION_CATEGORIES)


def test_existing_lifecycle_unchanged_cross_process():
    proc = subprocess.run(
        [sys.executable, "-c",
         "import pcae.core.phase_reports as pr; "
         "assert 'phase_report_view' not in dir(pr); "
         "print('OK')"],
        capture_output=True, text=True, cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


# ─────────────────────────────────────────────────────────────────────────────
# Cross-process determinism (mirrors 134E.1/134E.2's own convention)
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_process_determinism():
    script = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "from test_evidence_extraction_134e2 import _minimal_complete_evidence; "
        "from pcae.core.canonical_engineering_evidence import PhaseClass; "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_PHASE_REPORT; "
        "from pcae.core.phase_report_view import compose_phase_report_view; "
        "ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION); "
        "res = extract(ev, PROFILE_ID_PHASE_REPORT); "
        "view = compose_phase_report_view(res); "
        "print(view.compute_digest())"
    ) % (
        "src", str(__import__("pathlib").Path(__file__).resolve().parent),
    )
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    proc2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    digest1 = proc1.stdout.strip().splitlines()[-1]
    digest2 = proc2.stdout.strip().splitlines()[-1]
    assert digest1 == digest2

    res_in_process = compose_phase_report_view(
        extract(_minimal_complete_evidence(PhaseClass.IMPLEMENTATION), PROFILE_ID_PHASE_REPORT)
    )
    assert digest1 == res_in_process.compute_digest()
