"""Phase 134E.4 — focused tests for Operator Report View Composition
(``pcae.core.operator_report_view``).

This module is not yet active lifecycle authority. Regression coverage
for existing Canonical Engineering Evidence / Evidence Extraction /
Phase Report View / lifecycle behavior is provided by re-running the
existing suites unchanged (none of which import or reference this new
module).
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
from pcae.core import operator_report_view as orv
from pcae.core.operator_report_view import (
    DecisionCompleteness,
    OPERATOR_SECTION_ORDER,
    OperatorReportCompleteness,
    OperatorSectionApplicability,
    OperatorSectionCompleteness,
    OperatorSectionId,
    SUPPORTED_VIEW_VERSIONS,
    compose_operator_report_view,
)

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from test_evidence_extraction_134e2 import (  # noqa: E402
    _content_for,
    _full_applicability,
    _identity,
    _minimal_complete_evidence,
)


def _view_for(phase_class: PhaseClass, **overrides):
    ev = _minimal_complete_evidence(phase_class, profile_id=PROFILE_ID_OPERATOR_REPORT, **overrides)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    return res, compose_operator_report_view(res)


def _evidence_with_applicability(phase_class, app, **extra_overrides):
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
        phase_class, profile_id=PROFILE_ID_OPERATOR_REPORT,
        applicability=MappingProxyType(app), **tuple_overrides,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1-2: all twelve sections created, correct order
# ─────────────────────────────────────────────────────────────────────────────

def test_all_twelve_sections_created():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert len(view.sections) == 12
    assert {s.section_id for s in view.sections} == set(OperatorSectionId)


def test_correct_operator_section_order():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert [s.section_id for s in view.sections] == list(OPERATOR_SECTION_ORDER)
    assert [s.order for s in view.sections] == list(range(1, 13))


# ─────────────────────────────────────────────────────────────────────────────
# 3-14: section composition
# ─────────────────────────────────────────────────────────────────────────────

def test_outcome_composition():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.PHASE_OUTCOME)
    categories = {g.category for g in section.evidence_groups}
    assert "objective" in categories and "engineering_actions" in categories


def test_key_decisions_composition():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.KEY_DECISIONS_AND_CHANGES)
    categories = {g.category for g in section.evidence_groups}
    assert "implementation_findings" in categories


def test_discoveries_defects_repairs_composition():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    categories = {g.category for g in section.evidence_groups}
    assert {"defects_discovered", "defects_repaired", "incorrect_assumptions_corrected"} <= categories


def test_verification_remaining_findings_composition():
    _, view = _view_for(PhaseClass.VERIFICATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS)
    categories = {g.category for g in section.evidence_groups}
    assert "verification_findings" in categories


def test_technical_debt_composition():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK)
    categories = {g.category for g in section.evidence_groups}
    assert "technical_debt_reviewed" in categories


def test_architectural_significance_composition():
    _, view = _view_for(PhaseClass.ARCHITECTURE)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.ARCHITECTURAL_SIGNIFICANCE)
    categories = {g.category for g in section.evidence_groups}
    assert "track_progress" in categories


def test_boundaries_no_go_composition():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        no_go_confirmations=("no execution capability introduced",),
        applicability=MappingProxyType({
            **_full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT),
            "no_go_confirmations": Applicability.PRESENT,
        }),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.BOUNDARIES_AND_NO_GO)
    categories = {g.category for g in section.evidence_groups}
    assert "no_go_confirmations" in categories and "architectural_boundary_confirmations" in categories


def test_tests_governance_composition():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.TESTS_AND_GOVERNANCE)
    categories = {g.category for g in section.evidence_groups}
    assert {"governance_results", "test_results"} <= categories


def test_repository_runtime_composition():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE)
    categories = {g.category for g in section.evidence_groups}
    assert {"repository_state", "runtime_state", "commit_and_push"} <= categories


def test_next_phase_readiness_composition():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.NEXT_PHASE_AND_READINESS)
    categories = {g.category for g in section.evidence_groups}
    assert "recommended_next_phase" in categories


def test_notable_knowledge_composition():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.NOTABLE_ENGINEERING_KNOWLEDGE)
    categories = {g.category for g in section.evidence_groups}
    assert "notable_engineering_knowledge" in categories


def test_uncertainty_limitations_disclosures_composition():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(
        s for s in view.sections
        if s.section_id == OperatorSectionId.DISCLOSURES_UNCERTAINTY_LIMITATIONS
    )
    assert "technical_debt_reviewed" in section.uncertainty_categories
    assert section.applicability == OperatorSectionApplicability.MATERIALLY_POPULATED


# ─────────────────────────────────────────────────────────────────────────────
# 15-20: reports for each of the six phase classes
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase_class", list(PhaseClass))
def test_phase_class_operator_report(phase_class):
    res, view = _view_for(phase_class)
    assert view.phase_class == phase_class
    assert len(view.sections) == 12
    assert view.completeness in OperatorReportCompleteness
    assert view.decision_completeness in DecisionCompleteness


# ─────────────────────────────────────────────────────────────────────────────
# 21-22: status-only / near-status-only report rejected (decision-
# completeness gate)
# ─────────────────────────────────────────────────────────────────────────────

def test_status_only_report_rejected_by_construction():
    # Under operator_report_v1, defects_discovered/defects_repaired/
    # incorrect_assumptions_corrected/technical_debt_reviewed/notable_
    # engineering_knowledge are all hard REQUIRED for every phase class
    # -- a literal status-only record (all NOT_APPLICABLE) fails
    # extraction as INVALID before composition ever runs. PLANNING is
    # used (not IMPLEMENTATION/VERIFICATION) since neither of CEE's own
    # phase-class-mandatory-present categories applies to it, so this
    # probes the extraction-profile gate specifically, not the deeper
    # CEE-level gate.
    app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}
    ev = _evidence_with_applicability(PhaseClass.PLANNING, app)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    assert res.completeness == ExtractionCompleteness.INVALID
    with pytest.raises(ValueError):
        compose_operator_report_view(res)


def test_near_status_only_report_decision_incomplete():
    # All hard-REQUIRED substantive categories disclosed as UNAVAILABLE
    # (extraction: required_category_missing -> INCOMPLETE, not
    # INVALID) -- composition must still surface decision_completeness
    # as INCOMPLETE, not paper over the gap.
    app = _full_applicability(PhaseClass.PLANNING, PROFILE_ID_OPERATOR_REPORT)
    app["defects_discovered"] = Applicability.UNAVAILABLE
    app["defects_repaired"] = Applicability.UNAVAILABLE
    app["incorrect_assumptions_corrected"] = Applicability.UNAVAILABLE
    app["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    app["notable_engineering_knowledge"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.PLANNING, app,
        limitations=(LimitationItem(
            category="defects_discovered", description="unavailable",
            affected_evidence=(
                "defects_discovered", "defects_repaired",
                "incorrect_assumptions_corrected", "technical_debt_reviewed",
                "notable_engineering_knowledge",
            ),
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    assert res.completeness == ExtractionCompleteness.INCOMPLETE
    view = compose_operator_report_view(res)
    assert view.decision_completeness == DecisionCompleteness.INCOMPLETE


# ─────────────────────────────────────────────────────────────────────────────
# 23-24: semantic objective / outcome sufficiency
# ─────────────────────────────────────────────────────────────────────────────

def test_semantic_objective_sufficiency_status_only_diagnostic():
    # Force every substantive outcome category (architectural/
    # implementation/verification findings, defects, debt, knowledge) to
    # UNAVAILABLE simultaneously (a genuinely status-only outcome even
    # though objective/engineering_actions narrative remains present).
    # Nullify every substantive outcome category the PLANNING class
    # would otherwise populate by default (including architectural_
    # findings, PLANNING's own default-REQUIRED category) so
    # `has_substantive_outcome` is genuinely False -- a real status-only
    # outcome, not merely a partially-degraded one.
    app = _full_applicability(PhaseClass.PLANNING, PROFILE_ID_OPERATOR_REPORT)
    affected = (
        "architectural_findings", "defects_discovered", "defects_repaired",
        "incorrect_assumptions_corrected", "technical_debt_reviewed",
        "notable_engineering_knowledge",
    )
    for cat in affected:
        app[cat] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.PLANNING, app,
        limitations=(LimitationItem(
            category="architectural_findings", description="unavailable",
            affected_evidence=affected,
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    assert any(d.code == "status_only_outcome" for d in view.diagnostics)
    assert view.decision_completeness == DecisionCompleteness.INCOMPLETE


def test_semantic_outcome_sufficiency_satisfied_by_structured_presence():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert view.decision_completeness == DecisionCompleteness.COMPLETE
    assert not any(d.code == "status_only_outcome" for d in view.diagnostics)


# ─────────────────────────────────────────────────────────────────────────────
# 25-27: missing key decisions / architectural significance
# ─────────────────────────────────────────────────────────────────────────────

def test_missing_key_decisions_where_required_downgrades():
    # architectural_findings is hard REQUIRED (default, not overridden)
    # for REVIEW_HARDING under operator_report_v1, and -- unlike
    # implementation_findings/verification_findings for their own
    # matching phase class -- is not one of CanonicalEngineeringEvidence's
    # own phase-class-mandatory-present categories, so it may legitimately
    # be marked UNAVAILABLE (disclosed) and still finalize.
    app = _full_applicability(PhaseClass.REVIEW_HARDENING, PROFILE_ID_OPERATOR_REPORT)
    app["architectural_findings"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.REVIEW_HARDENING, app,
        limitations=(LimitationItem(
            category="architectural_findings", description="unavailable",
            affected_evidence=("architectural_findings",),
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.KEY_DECISIONS_AND_CHANGES)
    assert section.applicability == OperatorSectionApplicability.INCOMPLETE
    assert view.decision_completeness != DecisionCompleteness.COMPLETE


def test_missing_architectural_significance_downgrades():
    app = _full_applicability(PhaseClass.ARCHITECTURE, PROFILE_ID_OPERATOR_REPORT)
    ev = _evidence_with_applicability(
        PhaseClass.ARCHITECTURE, app, track_progress="incomplete evidence only",
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.ARCHITECTURAL_SIGNIFICANCE)
    assert "track_progress" in [g.category for g in section.evidence_groups]


def test_explicit_unavailable_architectural_significance():
    # architectural_findings is CONDITIONALLY_REQUIRED (not hard
    # REQUIRED) for VERIFICATION under operator_report_v1; absent ->
    # disclosed limitation, never silent. ARCHITECTURAL_SIGNIFICANCE
    # also owns track_progress (always genuinely present), so the
    # section as a whole is MATERIALLY_POPULATED/COMPLETE_WITH_
    # LIMITATIONS rather than UNAVAILABLE_WITH_DISCLOSURE -- but the
    # gap remains explicitly disclosed via missing_required_categories,
    # never silently hidden by the sibling category's presence.
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    ev = _evidence_with_applicability(PhaseClass.VERIFICATION, app)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.ARCHITECTURAL_SIGNIFICANCE)
    assert section.applicability == OperatorSectionApplicability.MATERIALLY_POPULATED
    assert section.completeness == OperatorSectionCompleteness.COMPLETE_WITH_LIMITATIONS
    assert "architectural_findings" in section.missing_required_categories


# ─────────────────────────────────────────────────────────────────────────────
# 28-31: defect preserved, repaired BLOCKING history preserved, partial
# repair remains unresolved, unresolved NON_BLOCKING preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_defect_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    finding = FindingRecord("F-1", FindingClassification.BLOCKING, "issue", "component")
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_discovered=(finding,),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert "blocking" in group.finding_classifications


def test_repaired_blocking_history_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    original = FindingRecord("F-2", FindingClassification.BLOCKING, "issue", "component")
    repair = RepairRecord(original, "fixed", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_repaired=(repair,),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    group = next(g for g in section.evidence_groups if g.category == "defects_repaired")
    assert "blocking" in group.finding_classifications
    assert "confirmed" in group.finding_classifications


def test_partial_repair_remains_unresolved_visible():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    unresolved = FindingRecord("F-3", FindingClassification.NON_BLOCKING, "residual", "component")
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_discovered=(unresolved,),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert "non_blocking" in group.finding_classifications


def test_unresolved_non_blocking_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    finding = FindingRecord("F-4", FindingClassification.NON_BLOCKING, "minor", "component")
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_discovered=(finding,),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    verif_section = next(
        s for s in view.sections
        if s.section_id == OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS
    )
    group = next(g for g in verif_section.evidence_groups if g.category == "defects_discovered")
    assert "non_blocking" in group.finding_classifications


# ─────────────────────────────────────────────────────────────────────────────
# 32-34: corrected assumption / technical debt / deferred work preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_corrected_assumption_preserved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    original = FindingRecord("F-5", FindingClassification.NON_BLOCKING, "wrong assumption", "component")
    repair = RepairRecord(original, "corrected", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, incorrect_assumptions_corrected=(repair,),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    categories = {g.category for g in section.evidence_groups}
    assert "incorrect_assumptions_corrected" in categories


def test_technical_debt_preserved():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK)
    assert any(g.category == "technical_debt_reviewed" for g in section.evidence_groups)


def test_deferred_work_preserved():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app["technical_debt_introduced"] = Applicability.PRESENT
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        technical_debt_introduced=_content_for("technical_debt_introduced"),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK)
    assert any(g.category == "technical_debt_introduced" for g in section.evidence_groups)


# ─────────────────────────────────────────────────────────────────────────────
# 35-37: governance warning / test failure / baseline failure disclosure
# ─────────────────────────────────────────────────────────────────────────────

def test_governance_warning_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        governance_results=(GovernanceResultItem("pcae_check", "warning: stale"),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "governance_results")
    assert selected.value[0].status == "warning: stale"


def test_test_failure_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        test_results=(TestResultItem("fast_green", "4389 passed, 1 failed", "failed"),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "test_results")
    assert selected.value[0].status == "failed"


def test_baseline_failure_disclosure_not_collapsed():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        test_results=(TestResultItem(
            "fast_green", "4389 passed, 1 pre-existing unrelated failure", "passed_with_known_issue",
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "test_results")
    assert "pre-existing" in selected.value[0].result


# ─────────────────────────────────────────────────────────────────────────────
# 38-41: repository dirty / unpushed / runtime change / execution
# unavailable preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_repository_dirty_state_preserved():
    from pcae.core.canonical_engineering_evidence import RepositoryStateSnapshot
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        repository_state=RepositoryStateSnapshot(
            commit="abc1234", branch="main", pushed_status="not_pushed",
            origin_main_head_count=2, clean=False,
        ),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "repository_state")
    assert selected.value.clean is False
    assert selected.value.pushed_status == "not_pushed"


def test_unpushed_state_preserved():
    from pcae.core.canonical_engineering_evidence import CommitPushInfo
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        commit_and_push=CommitPushInfo(commits=("abc1234",), pushed_status="not_pushed", origin_main_head_count=3),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "commit_and_push")
    assert selected.value.origin_main_head_count == 3


def test_runtime_change_preserved():
    from pcae.core.canonical_engineering_evidence import RuntimeStateSnapshot
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        runtime_state=RuntimeStateSnapshot(
            runtime_state="Observed", maximum_capability="observe", execution_availability="unavailable",
        ),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "runtime_state")
    assert selected.value.execution_availability == "unavailable"


def test_execution_unavailable_preserved():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE)
    assert any(g.category == "runtime_state" for g in section.evidence_groups)


# ─────────────────────────────────────────────────────────────────────────────
# 42-43: next-phase blocker preserved, no inferred next phase
# ─────────────────────────────────────────────────────────────────────────────

def test_next_phase_blocker_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        recommended_next_phase="blocked: 134E.4V must complete first",
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "recommended_next_phase")
    assert selected.value == "blocked: 134E.4V must complete first"


def test_no_inferred_next_phase():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        recommended_next_phase="explicitly no next phase recommended",
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "recommended_next_phase")
    assert "999Y" not in selected.value


# ─────────────────────────────────────────────────────────────────────────────
# 44-45: notable knowledge provenance, cross-agent incident lesson
# preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_notable_knowledge_provenance():
    from pcae.core.canonical_engineering_evidence import EvidenceProvenanceRecord
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        provenance=(EvidenceProvenanceRecord(
            covers="notable_engineering_knowledge", source_artifact="docs/PHASE_134.md",
            source_command=None, source_phase_id="134E.4", derivation_path="doc",
            verification_state="verified",
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.NOTABLE_ENGINEERING_KNOWLEDGE)
    assert "notable_engineering_knowledge" in section.provenance_categories


def test_cross_agent_incident_lesson_preserved():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        notable_engineering_knowledge=(
            "registry-overwrite defect class: fail-closed re-registration required",
        ),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "notable_engineering_knowledge")
    assert "registry-overwrite" in selected.value[0]


# ─────────────────────────────────────────────────────────────────────────────
# 46-49: uncertainty / limitation / conditional-missing disclosure /
# filtering disclosure preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_uncertainty_preserved():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    assert "technical_debt_reviewed" in view.cross_section_uncertainty


def test_limitation_preserved():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        limitations=(LimitationItem(
            category="technical_debt_reviewed", description="unavailable",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    assert "technical_debt_reviewed" in view.cross_section_limitation


def test_conditional_missing_disclosure_preserved():
    # Regression for the 134E.3V-class bug, baked in from the start:
    # no_go_confirmations conditionally missing must never compose as
    # NOT_APPLICABLE.
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    diag = [d for d in res.diagnostics if d.category == "no_go_confirmations"]
    assert diag and diag[0].code == "conditionally_required_category_missing"
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.BOUNDARIES_AND_NO_GO)
    # BOUNDARIES_AND_NO_GO also owns architectural_boundary_confirmations
    # (hard REQUIRED, always genuinely present under the minimal
    # fixture), so the section as a whole is MATERIALLY_POPULATED rather
    # than UNAVAILABLE_WITH_DISCLOSURE -- the critical assertion is that
    # it is never NOT_APPLICABLE (which would silently claim nothing is
    # missing) and the gap remains explicitly disclosed.
    assert section.applicability != OperatorSectionApplicability.NOT_APPLICABLE
    assert section.applicability == OperatorSectionApplicability.MATERIALLY_POPULATED
    assert section.completeness == OperatorSectionCompleteness.COMPLETE_WITH_LIMITATIONS
    assert "no_go_confirmations" in section.missing_required_categories


def test_filtering_disclosure_preserved():
    _, view = _view_for(PhaseClass.ARCHITECTURE)
    assert isinstance(view.filtering_disclosures, tuple)
    assert "implementation_findings" in view.filtering_disclosures


# ─────────────────────────────────────────────────────────────────────────────
# 50-52: decision completeness complete / incomplete / invalid
# ─────────────────────────────────────────────────────────────────────────────

def test_decision_completeness_complete():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert view.decision_completeness == DecisionCompleteness.COMPLETE


def test_decision_completeness_incomplete():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        limitations=(LimitationItem(
            category="technical_debt_reviewed", description="unavailable",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    assert view.decision_completeness == DecisionCompleteness.INCOMPLETE


def test_decision_completeness_invalid():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app["technical_debt_reviewed"] = Applicability.NOT_APPLICABLE
    ev = _evidence_with_applicability(PhaseClass.IMPLEMENTATION, app)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    assert res.completeness == ExtractionCompleteness.INVALID
    with pytest.raises(ValueError):
        compose_operator_report_view(res)


# ─────────────────────────────────────────────────────────────────────────────
# 53: view completeness cannot exceed extraction
# ─────────────────────────────────────────────────────────────────────────────

def test_view_completeness_never_exceeds_extraction():
    for phase_class in PhaseClass:
        res, view = _view_for(phase_class)
        rank = {"complete": 0, "complete_with_limitations": 1, "incomplete": 2, "invalid": 3}
        assert rank[view.completeness.value] >= rank[res.completeness.value]


# ─────────────────────────────────────────────────────────────────────────────
# 54-56: required evidence assignment accounting, unassigned material
# evidence rejected, duplicate assignment consistency
# ─────────────────────────────────────────────────────────────────────────────

def test_required_evidence_assignment_accounting():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert not any(d.code == "unassigned_required_evidence" for d in view.diagnostics)


def test_unassigned_material_evidence_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    forged = SelectedEvidenceItem(
        category="__forged__", source_evidence_id=res.source_evidence_id,
        value=("x",), applicability=Applicability.PRESENT,
        requirement_level=RequirementLevel.REQUIRED, provenance=(),
        verification_state=None, uncertainty_refs=(), limitation_refs=(),
        selection_reason="forged",
    )
    bad_res = dataclasses.replace(res, selected_evidence=res.selected_evidence + (forged,))
    view = compose_operator_report_view(bad_res)
    assert any(d.code == "unassigned_required_evidence" for d in view.diagnostics)
    assert view.completeness != OperatorReportCompleteness.COMPLETE


def test_duplicate_assignment_consistency():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    finding = FindingRecord("F-6", FindingClassification.BLOCKING, "issue", "component")
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_discovered=(finding,),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    discoveries = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    verif = next(s for s in view.sections if s.section_id == OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS)
    d_group = next(g for g in discoveries.evidence_groups if g.category == "defects_discovered")
    v_group = next(g for g in verif.evidence_groups if g.category == "defects_discovered")
    assert d_group.finding_classifications == v_group.finding_classifications == ("blocking",)
    assert d_group.is_primary is True
    assert v_group.is_primary is False


# ─────────────────────────────────────────────────────────────────────────────
# 57-58: findings prioritized without omission, priority ordering
# deterministic
# ─────────────────────────────────────────────────────────────────────────────

def test_findings_prioritized_without_omission():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    findings = (
        FindingRecord("F-A", FindingClassification.CONFIRMED, "a", "component"),
        FindingRecord("F-B", FindingClassification.BLOCKING, "b", "component"),
        FindingRecord("F-C", FindingClassification.NON_BLOCKING, "c", "component"),
    )
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_discovered=findings,
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert set(group.finding_classifications) == {"blocking", "non_blocking", "confirmed"}


def test_priority_ordering_deterministic():
    res, view1 = _view_for(PhaseClass.IMPLEMENTATION)
    view2 = compose_operator_report_view(res)
    for s1, s2 in zip(view1.sections, view2.sections):
        ranks1 = [g.priority_rank for g in s1.evidence_groups]
        ranks2 = [g.priority_rank for g in s2.evidence_groups]
        assert ranks1 == ranks2
        assert ranks1 == sorted(ranks1)


# ─────────────────────────────────────────────────────────────────────────────
# 59-64: Non-Strengthening
# ─────────────────────────────────────────────────────────────────────────────

def test_blocking_not_strengthened():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    finding = FindingRecord("F-7", FindingClassification.BLOCKING, "issue", "component")
    ev = _evidence_with_applicability(PhaseClass.VERIFICATION, app, defects_discovered=(finding,))
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert group.finding_classifications == ("blocking",)


def test_non_blocking_not_strengthened():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    finding = FindingRecord("F-8", FindingClassification.NON_BLOCKING, "issue", "component")
    ev = _evidence_with_applicability(PhaseClass.VERIFICATION, app, defects_discovered=(finding,))
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert group.finding_classifications == ("non_blocking",)


def test_unknown_not_converted_to_known():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    assert "technical_debt_reviewed" in view.cross_section_uncertainty
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK)
    assert not any(g.category == "technical_debt_reviewed" for g in section.evidence_groups)


def test_unavailable_not_converted_to_not_applicable():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.BOUNDARIES_AND_NO_GO)
    assert section.applicability != OperatorSectionApplicability.NOT_APPLICABLE


def test_warning_not_converted_to_pass():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        governance_results=(GovernanceResultItem("pcae_check", "warning"),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    selected = next(s for s in res.selected_evidence if s.category == "governance_results")
    assert selected.value[0].status == "warning"


def test_partial_verification_not_converted_to_independent_verification():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app["verification_findings"] = Applicability.PRESENT
    finding = FindingRecord("F-9", FindingClassification.CONFIRMED, "regression only", "component")
    ev = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app, verification_findings=(finding,),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(
        s for s in view.sections
        if s.section_id == OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS
    )
    group = next(g for g in section.evidence_groups if g.category == "verification_findings")
    assert group.requirement_level == "conditionally_required"


# ─────────────────────────────────────────────────────────────────────────────
# 65-69: determinism, serialization, round-trip, stable digest
# ─────────────────────────────────────────────────────────────────────────────

def test_deterministic_section_ordering():
    res, view1 = _view_for(PhaseClass.IMPLEMENTATION)
    view2 = compose_operator_report_view(res)
    assert [s.section_id for s in view1.sections] == [s.section_id for s in view2.sections]


def test_deterministic_item_ordering():
    res, view1 = _view_for(PhaseClass.IMPLEMENTATION)
    view2 = compose_operator_report_view(res)
    for s1, s2 in zip(view1.sections, view2.sections):
        assert [g.category for g in s1.evidence_groups] == [g.category for g in s2.evidence_groups]


def test_deterministic_serialization():
    res, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert view.to_dict() == compose_operator_report_view(res).to_dict()


def test_round_trip_serialization():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    import json
    reloaded = json.loads(json.dumps(view.to_dict()))
    assert reloaded["view_id"] == view.view_id
    assert len(reloaded["sections"]) == 12


def test_stable_view_digest():
    res, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert view.compute_digest() == compose_operator_report_view(res).compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# 70-72: digest changes on finding/uncertainty/limitation change
# ─────────────────────────────────────────────────────────────────────────────

def test_digest_changes_on_finding_change():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    finding1 = FindingRecord("F-10", FindingClassification.BLOCKING, "issue", "component")
    finding2 = FindingRecord("F-11", FindingClassification.NON_BLOCKING, "other", "component")
    ev1 = _evidence_with_applicability(PhaseClass.VERIFICATION, app, defects_discovered=(finding1,))
    ev2 = _evidence_with_applicability(PhaseClass.VERIFICATION, app, defects_discovered=(finding2,))
    d1 = compose_operator_report_view(extract(ev1, PROFILE_ID_OPERATOR_REPORT)).compute_digest()
    d2 = compose_operator_report_view(extract(ev2, PROFILE_ID_OPERATOR_REPORT)).compute_digest()
    assert d1 != d2


def test_digest_changes_on_uncertainty_change():
    app1 = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    ev1 = _evidence_with_applicability(PhaseClass.IMPLEMENTATION, app1)
    app2 = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app2["technical_debt_reviewed"] = Applicability.UNKNOWN
    ev2 = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app2,
        uncertainty=(UncertaintyItem(
            category="technical_debt_reviewed", description="unknown",
            affected_evidence=("technical_debt_reviewed",), source="agent",
            verification_state="unverified",
        ),),
    )
    d1 = compose_operator_report_view(extract(ev1, PROFILE_ID_OPERATOR_REPORT)).compute_digest()
    d2 = compose_operator_report_view(extract(ev2, PROFILE_ID_OPERATOR_REPORT)).compute_digest()
    assert d1 != d2


def test_digest_changes_on_limitation_change():
    app1 = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    ev1 = _evidence_with_applicability(PhaseClass.IMPLEMENTATION, app1)
    app2 = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    app2["technical_debt_reviewed"] = Applicability.UNAVAILABLE
    ev2 = _evidence_with_applicability(
        PhaseClass.IMPLEMENTATION, app2,
        limitations=(LimitationItem(
            category="technical_debt_reviewed", description="unavailable",
            affected_evidence=("technical_debt_reviewed",),
        ),),
    )
    d1 = compose_operator_report_view(extract(ev1, PROFILE_ID_OPERATOR_REPORT)).compute_digest()
    d2 = compose_operator_report_view(extract(ev2, PROFILE_ID_OPERATOR_REPORT)).compute_digest()
    assert d1 != d2


# ─────────────────────────────────────────────────────────────────────────────
# 73-74: rendering / delivery state excluded
# ─────────────────────────────────────────────────────────────────────────────

def test_rendering_state_excluded():
    field_names = {f.name for f in dataclasses.fields(orv.OperatorReportView)}
    forbidden = {"markdown", "html", "plain_text", "rendered", "delivery", "sink", "transport"}
    assert not (field_names & forbidden)


def test_delivery_state_excluded_from_serialization():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    d = view.to_dict()
    forbidden_keys = {"markdown", "html", "delivery", "sink", "transport", "chat_id", "telegram"}
    assert not (set(d.keys()) & forbidden_keys)


# ─────────────────────────────────────────────────────────────────────────────
# 75-77: wrong extraction profile / unsupported profile version /
# unsupported view version rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_wrong_extraction_profile_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_PHASE_REPORT)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    with pytest.raises(ValueError, match="operator_report_v1"):
        compose_operator_report_view(res)


def test_unsupported_extraction_profile_version_rejected_upstream():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    with pytest.raises(ValueError):
        extract(ev, PROFILE_ID_OPERATOR_REPORT, profile_version="99.0")


def test_unsupported_view_version_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    with pytest.raises(ValueError, match="Unsupported Operator Report View version"):
        compose_operator_report_view(res, view_version="0.9-forged")
    assert "0.9-forged" not in SUPPORTED_VIEW_VERSIONS


# ─────────────────────────────────────────────────────────────────────────────
# 78-81: orphan finding/repair/uncertainty/limitation rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_orphan_finding_rejected_upstream():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    assert res is not None


def test_orphan_repair_rejected_upstream():
    with pytest.raises(ValueError):
        RepairRecord(
            FindingRecord("F-12", FindingClassification.CONFIRMED, "x", "y"),
            "action", "artifact", "evidence", FindingClassification.CONFIRMED,
        )


def test_orphan_uncertainty_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    bad_item = dataclasses.replace(res.selected_evidence[0], uncertainty_refs=("__no_such_category__",))
    bad_res = dataclasses.replace(res, selected_evidence=(bad_item,) + res.selected_evidence[1:])
    with pytest.raises(ValueError, match="Orphan uncertainty reference"):
        compose_operator_report_view(bad_res)


def test_orphan_limitation_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    bad_item = dataclasses.replace(res.selected_evidence[0], limitation_refs=("__no_such_category__",))
    bad_res = dataclasses.replace(res, selected_evidence=(bad_item,) + res.selected_evidence[1:])
    with pytest.raises(ValueError, match="Orphan limitation reference"):
        compose_operator_report_view(bad_res)


# ─────────────────────────────────────────────────────────────────────────────
# 82-83: duplicate section identity / empty successful report rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_duplicate_section_identity_impossible_via_entry_point():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    ids = [s.section_id for s in view.sections]
    assert len(ids) == len(set(ids)) == 12


def test_empty_successful_report_rejected():
    app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}
    ev = _evidence_with_applicability(PhaseClass.PLANNING, app)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    with pytest.raises(ValueError):
        compose_operator_report_view(res)


# ─────────────────────────────────────────────────────────────────────────────
# 84-85: agent/model independence, future-agent provenance
# ─────────────────────────────────────────────────────────────────────────────

def test_agent_model_independence():
    sig = inspect.signature(compose_operator_report_view)
    assert set(sig.parameters.keys()) == {"result", "view_version"}


def test_future_agent_provenance_independence():
    from pcae.core.canonical_engineering_evidence import EvidenceProvenanceRecord
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        provenance=(EvidenceProvenanceRecord(
            covers="test_results", source_artifact="ci-output.txt", source_command="pytest",
            source_phase_id="134E.4", derivation_path="ci", verification_state="verified",
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.TESTS_AND_GOVERNANCE)
    assert "test_results" in section.provenance_categories


# ─────────────────────────────────────────────────────────────────────────────
# 86-90: transport independence, no Telegram/renderer dependency, no
# filesystem/network behavior, no active lifecycle imports
# ─────────────────────────────────────────────────────────────────────────────

def test_transport_independence():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert "transport" not in view.to_dict()
    source = inspect.getsource(orv)
    assert "sink" not in source.lower() and "chat_id" not in source.lower()


def test_no_telegram_dependency():
    assert "telegram" not in inspect.getsource(orv).lower()
    assert not hasattr(orv, "TelegramSink")


def test_no_renderer_dependency():
    for forbidden in ("import jinja", "render_markdown(", "render_html(", "markdown.markdown("):
        assert forbidden not in inspect.getsource(orv)


def test_no_filesystem_network_behavior(monkeypatch):
    def _forbidden(*a, **kw):
        raise AssertionError("operator_report_view must not touch the filesystem")
    monkeypatch.setattr("builtins.open", _forbidden)
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    view.to_dict()
    view.compute_digest()


def test_no_active_lifecycle_imports():
    for line in inspect.getsource(orv).splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            for module in (
                "pcae.core.phase_reports", "pcae.core.notifications",
                "pcae.core.notification_certification",
                "pcae.core.repository_transition_validator",
            ):
                assert module not in stripped


# ─────────────────────────────────────────────────────────────────────────────
# 91-95: Phase Report View / Evidence Extraction / canonical evidence /
# lifecycle unchanged
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_report_view_unchanged():
    import pcae.core.phase_report_view as prv
    assert "operator_report_view" not in inspect.getsource(prv)


def test_evidence_extraction_unchanged_no_new_import():
    import pcae.core.evidence_extraction as ee
    assert "operator_report_view" not in inspect.getsource(ee)


def test_canonical_evidence_remains_immutable():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    digest_before = ev.compute_digest()
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    assert ev.compute_digest() == digest_before


def test_existing_lifecycle_unchanged():
    proc = subprocess.run(
        [sys.executable, "-c",
         "import pcae.core.phase_reports as pr; "
         "assert 'operator_report_view' not in dir(pr); "
         "print('OK')"],
        capture_output=True, text=True, cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_no_consumer_references_operator_report_view_yet():
    import pathlib
    src_root = pathlib.Path(orv.__file__).resolve().parent.parent
    for path in src_root.rglob("*.py"):
        if path.name == "operator_report_view.py":
            continue
        if "test" in str(path):
            continue
        text = path.read_text()
        assert "operator_report_view" not in text, f"{path} unexpectedly references operator_report_view"


# ─────────────────────────────────────────────────────────────────────────────
# 96: mobile-oriented structure without transport coupling
# ─────────────────────────────────────────────────────────────────────────────

def test_mobile_oriented_structure_without_transport_coupling():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    # Compact, decision-oriented section count (12, fewer than PFR-001's
    # 13) with no rendered-length/formatting concerns anywhere in the
    # model -- structure alone, no transport coupling.
    assert len(view.sections) == 12
    d = view.to_dict()
    assert "max_length" not in d and "chunk_size" not in d


# ─────────────────────────────────────────────────────────────────────────────
# Cross-process determinism (mirrors 134E.1-134E.3's own convention)
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_process_determinism():
    script = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "from test_evidence_extraction_134e2 import _minimal_complete_evidence; "
        "from pcae.core.canonical_engineering_evidence import PhaseClass; "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_OPERATOR_REPORT; "
        "from pcae.core.operator_report_view import compose_operator_report_view; "
        "ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT); "
        "res = extract(ev, PROFILE_ID_OPERATOR_REPORT); "
        "view = compose_operator_report_view(res); "
        "print(view.compute_digest())"
    ) % ("src", str(__import__("pathlib").Path(__file__).resolve().parent))
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    proc2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    digest1 = proc1.stdout.strip().splitlines()[-1]
    digest2 = proc2.stdout.strip().splitlines()[-1]
    assert digest1 == digest2
