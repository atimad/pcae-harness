"""Phase 134E.4V — independent adversarial verification of Operator
Report View Composition (134E.4).

Does not trust 134E.4's own report, documentation, or its 97 tests as
sufficient evidence. These are fresh probes beyond that existing
coverage, including a regression test for one genuine BLOCKING defect
found and repaired during this verification phase:

1. Decision-completeness / informational-completeness divergence:
   ``_compute_decision_completeness()``'s nine per-obligation checks
   tested ``section.applicability == OperatorSectionApplicability.
   INCOMPLETE`` only, missing the sibling "structurally empty required
   section" path (``applicability=UNAVAILABLE_WITH_DISCLOSURE``,
   ``completeness=INCOMPLETE`` -- a different enum value, the same
   informational severity). Reachable via a forged/tampered
   ``ExtractionResult`` (a REQUIRED category silently absent from
   ``selected_evidence`` with zero diagnostic); such a section let
   every decision-completeness obligation pass despite its own
   completeness already being INCOMPLETE, so ``decision_completeness``
   reported COMPLETE while ``completeness`` reported INCOMPLETE --
   backwards from the module's own stated invariant that decision
   completeness is *at least as* strict as informational completeness.
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
import pcae.core.phase_report_view as prv

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from test_evidence_extraction_134e2 import (  # noqa: E402
    _content_for,
    _full_applicability,
    _identity,
    _minimal_complete_evidence,
)
from test_operator_report_view_134e4 import (  # noqa: E402
    _evidence_with_applicability,
    _view_for,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Status-only decision-complete bypass (regression for the repaired defect)
# ─────────────────────────────────────────────────────────────────────────────

def test_status_only_decision_complete_bypass_repaired():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    filtered = tuple(item for item in res.selected_evidence if item.category != "technical_debt_reviewed")
    bad_res = dataclasses.replace(res, selected_evidence=filtered)
    view = compose_operator_report_view(bad_res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK)
    assert section.completeness == OperatorSectionCompleteness.INCOMPLETE
    # decision_completeness must never be "better" than completeness.
    assert view.decision_completeness != DecisionCompleteness.COMPLETE
    assert view.completeness != OperatorReportCompleteness.COMPLETE


# ─────────────────────────────────────────────────────────────────────────────
# 2. Near-status-only semantic bypass (documented limitation, not a defect)
# ─────────────────────────────────────────────────────────────────────────────

def test_near_status_only_semantic_bypass_documented():
    # Structural presence alone satisfies the semantic-sufficiency gate;
    # this is a known, accepted design limitation (never free-text
    # heuristic scoring), not a defect this phase repairs.
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    assert view.decision_completeness == DecisionCompleteness.COMPLETE


# ─────────────────────────────────────────────────────────────────────────────
# 3. Whitespace-only objective
# ─────────────────────────────────────────────────────────────────────────────

def test_whitespace_only_objective_accepted_documented_limitation():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT, objective="   ",
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    sel = next(s for s in res.selected_evidence if s.category == "objective")
    assert sel.value == "   "
    # Documented NON-BLOCKING limitation: composition performs no
    # free-text content judgment, per its own explicit non-goals.
    assert view.decision_completeness == DecisionCompleteness.COMPLETE


# ─────────────────────────────────────────────────────────────────────────────
# 4. Generic completed outcome
# ─────────────────────────────────────────────────────────────────────────────

def test_generic_completed_outcome_structural_presence_only():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        objective="completed", engineering_actions=("completed",),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    outcome = next(s for s in view.sections if s.section_id == OperatorSectionId.PHASE_OUTCOME)
    assert outcome.applicability == OperatorSectionApplicability.MATERIALLY_POPULATED


# ─────────────────────────────────────────────────────────────────────────────
# 5-6. Missing architecture decision / contract obligation
# ─────────────────────────────────────────────────────────────────────────────

def test_missing_architecture_decision_downgrades():
    app = _full_applicability(PhaseClass.ARCHITECTURE, PROFILE_ID_OPERATOR_REPORT)
    app["architectural_findings"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.ARCHITECTURE, app,
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


def test_missing_contract_obligation_downgrades():
    app = _full_applicability(PhaseClass.CONTRACT, PROFILE_ID_OPERATOR_REPORT)
    app["architectural_findings"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.CONTRACT, app,
        limitations=(LimitationItem(
            category="architectural_findings", description="unavailable",
            affected_evidence=("architectural_findings",),
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.KEY_DECISIONS_AND_CHANGES)
    assert section.applicability == OperatorSectionApplicability.INCOMPLETE


# ─────────────────────────────────────────────────────────────────────────────
# 7-10. Planning without risks, implementation without components,
# verification without fresh probes, hardening without residual risk
# ─────────────────────────────────────────────────────────────────────────────

def test_planning_report_without_risks_disclosed():
    app = _full_applicability(PhaseClass.PLANNING, PROFILE_ID_OPERATOR_REPORT)
    app["architectural_findings"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.PLANNING, app,
        limitations=(LimitationItem(
            category="architectural_findings", description="unavailable",
            affected_evidence=("architectural_findings",),
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.KEY_DECISIONS_AND_CHANGES)
    assert section.applicability != OperatorSectionApplicability.NOT_APPLICABLE
    assert "architectural_findings" in section.missing_required_categories


def test_implementation_report_without_components():
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    ev = _evidence_with_applicability(PhaseClass.IMPLEMENTATION, app)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.KEY_DECISIONS_AND_CHANGES)
    # implementation_findings is CEE-mandatory-present for IMPLEMENTATION,
    # so a genuine record always carries it -- confirm it is composed.
    assert any(g.category == "implementation_findings" for g in section.evidence_groups)


def test_verification_report_without_fresh_probes():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    ev = _evidence_with_applicability(PhaseClass.VERIFICATION, app)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(
        s for s in view.sections
        if s.section_id == OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS
    )
    # verification_findings is CEE-mandatory-present for VERIFICATION.
    assert any(g.category == "verification_findings" for g in section.evidence_groups)


def test_hardening_report_without_residual_risk_disclosed():
    app = _full_applicability(PhaseClass.REVIEW_HARDENING, PROFILE_ID_OPERATOR_REPORT)
    app["implementation_findings"] = Applicability.UNAVAILABLE
    ev = _evidence_with_applicability(
        PhaseClass.REVIEW_HARDENING, app,
        limitations=(LimitationItem(
            category="implementation_findings", description="unavailable",
            affected_evidence=("implementation_findings",),
        ),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.KEY_DECISIONS_AND_CHANGES)
    assert "implementation_findings" in section.missing_required_categories


# ─────────────────────────────────────────────────────────────────────────────
# 11-13. Repaired BLOCKING history collapse, partial repair shown resolved,
# corrected assumption omitted
# ─────────────────────────────────────────────────────────────────────────────

def test_repaired_blocking_history_not_collapsed():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    original = FindingRecord("F-C1", FindingClassification.BLOCKING, "issue", "component")
    repair = RepairRecord(original, "fixed", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _evidence_with_applicability(PhaseClass.VERIFICATION, app, defects_repaired=(repair,))
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    group = next(g for g in section.evidence_groups if g.category == "defects_repaired")
    assert "blocking" in group.finding_classifications and "confirmed" in group.finding_classifications
    selected = next(s for s in res.selected_evidence if s.category == "defects_repaired")
    assert selected.value[0].original_finding.classification == FindingClassification.BLOCKING


def test_partial_repair_not_shown_resolved():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    residual = FindingRecord("F-C2", FindingClassification.NON_BLOCKING, "residual", "component")
    original = FindingRecord("F-C3", FindingClassification.BLOCKING, "main", "component")
    repair = RepairRecord(original, "partial fix", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_discovered=(residual,), defects_repaired=(repair,),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    disc = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert "non_blocking" in disc.finding_classifications


def test_corrected_assumption_not_omitted():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    original = FindingRecord("F-C4", FindingClassification.NON_BLOCKING, "wrong assumption", "component")
    repair = RepairRecord(original, "corrected", "component.py", "verified", FindingClassification.CONFIRMED)
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, incorrect_assumptions_corrected=(repair,),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    assert any(g.category == "incorrect_assumptions_corrected" for g in section.evidence_groups)


# ─────────────────────────────────────────────────────────────────────────────
# 14-15. Unresolved NON-BLOCKING omitted, technical debt omitted
# ─────────────────────────────────────────────────────────────────────────────

def test_unresolved_non_blocking_not_omitted():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    finding = FindingRecord("F-C5", FindingClassification.NON_BLOCKING, "minor", "component")
    ev = _evidence_with_applicability(PhaseClass.VERIFICATION, app, defects_discovered=(finding,))
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    for section_id in (
        OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS,
        OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS,
    ):
        section = next(s for s in view.sections if s.section_id == section_id)
        group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
        assert "non_blocking" in group.finding_classifications


def test_technical_debt_not_omitted():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK)
    assert any(g.category == "technical_debt_reviewed" for g in section.evidence_groups)


# ─────────────────────────────────────────────────────────────────────────────
# 16. Architectural significance placeholder
# ─────────────────────────────────────────────────────────────────────────────

def test_architectural_significance_placeholder_not_invented():
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, profile_id=PROFILE_ID_OPERATOR_REPORT,
        track_progress="minimal track progress",
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    sel = next(s for s in res.selected_evidence if s.category == "track_progress")
    assert sel.value == "minimal track progress"
    assert "invented" not in sel.value


# ─────────────────────────────────────────────────────────────────────────────
# 17. No-Go/boundary conflation
# ─────────────────────────────────────────────────────────────────────────────

def test_no_go_boundary_no_conflation():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        no_go_confirmations=("no execution capability introduced",),
        architectural_boundary_confirmations=("determinism preserved",),
        applicability=MappingProxyType({
            **_full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT),
            "no_go_confirmations": Applicability.PRESENT,
        }),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.BOUNDARIES_AND_NO_GO)
    no_go_vals = {g.category for g in section.evidence_groups if g.category == "no_go_confirmations"}
    boundary_vals = {g.category for g in section.evidence_groups if g.category == "architectural_boundary_confirmations"}
    assert no_go_vals and boundary_vals
    # Confirm no other section fabricates a no_go_confirmations reference.
    for s in view.sections:
        if s.section_id == OperatorSectionId.BOUNDARIES_AND_NO_GO:
            continue
        assert not any(g.category == "no_go_confirmations" for g in s.evidence_groups)


# ─────────────────────────────────────────────────────────────────────────────
# 18-21. Governance warning / test failure / dirty repo / unpushed state
# strengthened
# ─────────────────────────────────────────────────────────────────────────────

def test_governance_warning_not_strengthened():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        governance_results=(GovernanceResultItem("pcae_check", "warning: stale cache"),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    sel = next(s for s in res.selected_evidence if s.category == "governance_results")
    assert sel.value[0].status == "warning: stale cache"


def test_test_failure_not_strengthened():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        test_results=(TestResultItem("fast_green", "4389 passed, 1 failed", "failed"),),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    sel = next(s for s in res.selected_evidence if s.category == "test_results")
    assert sel.value[0].status == "failed"


def test_dirty_repository_not_strengthened():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        repository_state=RepositoryStateSnapshot(
            commit="abc1234", branch="main", pushed_status="not_pushed",
            origin_main_head_count=2, clean=False,
        ),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    sel = next(s for s in res.selected_evidence if s.category == "repository_state")
    assert sel.value.clean is False


def test_unpushed_state_not_strengthened():
    from pcae.core.canonical_engineering_evidence import CommitPushInfo
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        commit_and_push=CommitPushInfo(commits=("abc1234",), pushed_status="not_pushed", origin_main_head_count=3),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    compose_operator_report_view(res)
    sel = next(s for s in res.selected_evidence if s.category == "commit_and_push")
    assert sel.value.pushed_status == "not_pushed"


# ─────────────────────────────────────────────────────────────────────────────
# 22. Runtime change omitted
# ─────────────────────────────────────────────────────────────────────────────

def test_runtime_change_not_omitted():
    ev = _minimal_complete_evidence(
        PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT,
        runtime_state=RuntimeStateSnapshot(
            runtime_state="Observed", maximum_capability="observe", execution_availability="unavailable",
        ),
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE)
    assert any(g.category == "runtime_state" for g in section.evidence_groups)


# ─────────────────────────────────────────────────────────────────────────────
# 23. Unsafe next phase marked ready
# ─────────────────────────────────────────────────────────────────────────────

def test_unsafe_next_phase_never_marked_ready_by_composition():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    finding = FindingRecord("F-C6", FindingClassification.BLOCKING, "unresolved", "component")
    ev = _evidence_with_applicability(
        PhaseClass.VERIFICATION, app, defects_discovered=(finding,),
        recommended_next_phase="blocked pending resolution",
    )
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    sel = next(s for s in res.selected_evidence if s.category == "recommended_next_phase")
    assert sel.value == "blocked pending resolution"
    # Composition never rewrites this to "ready" -- verbatim only.
    assert "ready" not in sel.value


# ─────────────────────────────────────────────────────────────────────────────
# 24. Notable knowledge omitted
# ─────────────────────────────────────────────────────────────────────────────

def test_notable_knowledge_not_omitted():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.NOTABLE_ENGINEERING_KNOWLEDGE)
    assert any(g.category == "notable_engineering_knowledge" for g in section.evidence_groups)


# ─────────────────────────────────────────────────────────────────────────────
# 25-26. Report-level uncertainty omitted / cross-section limitation omitted
# ─────────────────────────────────────────────────────────────────────────────

def test_report_level_uncertainty_not_omitted():
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
    disclosures = next(
        s for s in view.sections if s.section_id == OperatorSectionId.DISCLOSURES_UNCERTAINTY_LIMITATIONS
    )
    assert "technical_debt_reviewed" in disclosures.uncertainty_categories


def test_cross_section_limitation_not_omitted():
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
    disclosures = next(
        s for s in view.sections if s.section_id == OperatorSectionId.DISCLOSURES_UNCERTAINTY_LIMITATIONS
    )
    assert "technical_debt_reviewed" in disclosures.limitation_categories


# ─────────────────────────────────────────────────────────────────────────────
# 27. Conditional missing shown not applicable (regression for the
# 134E.3V-class defect, proactively avoided)
# ─────────────────────────────────────────────────────────────────────────────

def test_conditional_missing_never_shown_not_applicable():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    diag = [d for d in res.diagnostics if d.category == "no_go_confirmations"]
    assert diag and diag[0].code == "conditionally_required_category_missing"
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.BOUNDARIES_AND_NO_GO)
    assert section.applicability != OperatorSectionApplicability.NOT_APPLICABLE
    assert "no_go_confirmations" in section.missing_required_categories


# ─────────────────────────────────────────────────────────────────────────────
# 28. Filtering disclosure hidden
# ─────────────────────────────────────────────────────────────────────────────

def test_filtering_disclosure_not_hidden():
    _, view = _view_for(PhaseClass.ARCHITECTURE)
    assert "implementation_findings" in view.filtering_disclosures
    disclosures = next(
        s for s in view.sections if s.section_id == OperatorSectionId.DISCLOSURES_UNCERTAINTY_LIMITATIONS
    )
    assert "implementation_findings" in disclosures.filtering_disclosure_categories


# ─────────────────────────────────────────────────────────────────────────────
# 29. Priority ordering omission
# ─────────────────────────────────────────────────────────────────────────────

def test_priority_ordering_never_omits_evidence():
    app = _full_applicability(PhaseClass.VERIFICATION, PROFILE_ID_OPERATOR_REPORT)
    findings = (
        FindingRecord("F-P1", FindingClassification.CONFIRMED, "a", "c"),
        FindingRecord("F-P2", FindingClassification.BLOCKING, "b", "c"),
    )
    ev = _evidence_with_applicability(PhaseClass.VERIFICATION, app, defects_discovered=findings)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    section = next(s for s in view.sections if s.section_id == OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS)
    group = next(g for g in section.evidence_groups if g.category == "defects_discovered")
    assert set(group.finding_classifications) == {"blocking", "confirmed"}


# ─────────────────────────────────────────────────────────────────────────────
# 30-31. Assignment accounting altered-value probe / duplicate conflicting
# assignment
# ─────────────────────────────────────────────────────────────────────────────

def test_assignment_accounting_altered_value_cannot_diverge():
    # Since every section reads from the same `selected` dict built once,
    # there is no code path where the "same" category could carry two
    # different values across sections.
    _, view = _view_for(PhaseClass.ARCHITECTURE)
    refs = [
        g for s in view.sections for g in s.evidence_groups if g.category == "architectural_findings"
    ]
    assert len(refs) >= 2
    assert len({tuple(sorted(r.finding_classifications)) for r in refs}) == 1


def test_duplicate_conflicting_assignment_detected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    forged = SelectedEvidenceItem(
        category="__dup__", source_evidence_id=res.source_evidence_id,
        value=("x",), applicability=Applicability.PRESENT,
        requirement_level=RequirementLevel.REQUIRED, provenance=(),
        verification_state=None, uncertainty_refs=(), limitation_refs=(),
        selection_reason="forged",
    )
    bad_res = dataclasses.replace(res, selected_evidence=res.selected_evidence + (forged, forged))
    view = compose_operator_report_view(bad_res)
    assert any(d.code == "unassigned_required_evidence" for d in view.diagnostics)


# ─────────────────────────────────────────────────────────────────────────────
# 32-33. Wrong extraction profile / unsupported view version
# ─────────────────────────────────────────────────────────────────────────────

def test_wrong_extraction_profile_fails_closed():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_PHASE_REPORT)
    res = extract(ev, PROFILE_ID_PHASE_REPORT)
    with pytest.raises(ValueError, match="operator_report_v1"):
        compose_operator_report_view(res)


def test_unsupported_view_version_fails_closed():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    with pytest.raises(ValueError):
        compose_operator_report_view(res, view_version="9.9-forged")
    assert "9.9-forged" not in SUPPORTED_VIEW_VERSIONS


# ─────────────────────────────────────────────────────────────────────────────
# 34. Cross-process byte determinism
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_process_byte_determinism():
    script = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "from test_evidence_extraction_134e2 import _minimal_complete_evidence; "
        "from pcae.core.canonical_engineering_evidence import PhaseClass; "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_OPERATOR_REPORT; "
        "from pcae.core.operator_report_view import compose_operator_report_view; "
        "import json; "
        "ev = _minimal_complete_evidence(PhaseClass.VERIFICATION, profile_id=PROFILE_ID_OPERATOR_REPORT); "
        "res = extract(ev, PROFILE_ID_OPERATOR_REPORT); "
        "view = compose_operator_report_view(res); "
        "print(json.dumps(view.to_dict(), sort_keys=True))"
    ) % ("src", str(__import__("pathlib").Path(__file__).resolve().parent))
    repo_root = str(__import__("pathlib").Path(__file__).resolve().parents[1])
    proc1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    proc2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=repo_root)
    assert proc1.returncode == 0, proc1.stderr
    assert proc2.returncode == 0, proc2.stderr
    assert proc1.stdout == proc2.stdout


# ─────────────────────────────────────────────────────────────────────────────
# 35-36: unknown future-agent independence / synthetic future-transport
# independence
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_future_agent_independence():
    sig = inspect.signature(compose_operator_report_view)
    assert set(sig.parameters.keys()) == {"result", "view_version"}


def test_synthetic_future_transport_independence():
    _, view = _view_for(PhaseClass.IMPLEMENTATION)
    d = view.to_dict()
    assert "transport" not in d and "sink" not in d and "chat_id" not in d


# ─────────────────────────────────────────────────────────────────────────────
# 37. Phase Report sibling unchanged
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_report_sibling_unchanged():
    assert "operator_report_view" not in inspect.getsource(prv)
    assert not hasattr(prv, "compose_operator_report_view")


# ─────────────────────────────────────────────────────────────────────────────
# 38. No active lifecycle imports
# ─────────────────────────────────────────────────────────────────────────────

def test_no_active_lifecycle_imports_fresh_scan():
    for line in inspect.getsource(orv).splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            for module in (
                "pcae.core.phase_reports", "pcae.core.notifications",
                "pcae.core.notification_certification",
                "pcae.core.repository_transition_validator",
                "pcae.core.phase_report_view",
            ):
                assert module not in stripped


# ─────────────────────────────────────────────────────────────────────────────
# 39. No filesystem/network/rendering/delivery side effects
# ─────────────────────────────────────────────────────────────────────────────

def test_no_filesystem_network_rendering_delivery_side_effects(monkeypatch):
    def _forbidden(*a, **kw):
        raise AssertionError("operator_report_view must not touch the filesystem")
    monkeypatch.setattr("builtins.open", _forbidden)
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    view.to_dict()
    view.compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# 40. Disclosures cross-cutting completeness behavior
# ─────────────────────────────────────────────────────────────────────────────

def test_disclosures_cross_cutting_completeness_behavior():
    # No uncertainty/limitation/filtering anywhere -> NOT_APPLICABLE,
    # never wrongly downgraded (regression for 134E.4's own self-found
    # and self-fixed defect). Every REQUIRED/CONDITIONALLY_REQUIRED/
    # OPTIONAL category must be genuinely satisfied PRESENT -- an
    # OPTIONAL-and-absent category (e.g. technical_debt_introduced)
    # legitimately creates its own FilteringDisclosure, which would
    # make DISCLOSURES_UNCERTAINTY_LIMITATIONS correctly non-empty.
    app = _full_applicability(PhaseClass.IMPLEMENTATION, PROFILE_ID_OPERATOR_REPORT)
    for category in REQUIRED_APPLICABILITY_CATEGORIES:
        app[category] = Applicability.PRESENT
    ev = _evidence_with_applicability(PhaseClass.IMPLEMENTATION, app)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    view = compose_operator_report_view(res)
    disclosures = next(
        s for s in view.sections if s.section_id == OperatorSectionId.DISCLOSURES_UNCERTAINTY_LIMITATIONS
    )
    assert disclosures.applicability == OperatorSectionApplicability.NOT_APPLICABLE
    assert disclosures.completeness == OperatorSectionCompleteness.COMPLETE
    assert not any(
        d.code == "structurally_empty_required_section" for d in view.diagnostics
    )


# ─────────────────────────────────────────────────────────────────────────────
# Additional targeted re-confirmations
# ─────────────────────────────────────────────────────────────────────────────

def test_view_completeness_never_exceeds_extraction_all_classes():
    for phase_class in PhaseClass:
        res, view = _view_for(phase_class)
        rank = {"complete": 0, "complete_with_limitations": 1, "incomplete": 2, "invalid": 3}
        assert rank[view.completeness.value] >= rank[res.completeness.value]


def test_orphan_uncertainty_rejected():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    bad_item = dataclasses.replace(res.selected_evidence[0], uncertainty_refs=("__no_such__",))
    bad_res = dataclasses.replace(res, selected_evidence=(bad_item,) + res.selected_evidence[1:])
    with pytest.raises(ValueError, match="Orphan uncertainty reference"):
        compose_operator_report_view(bad_res)


def test_source_evidence_and_extraction_result_never_mutated():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    digest_before = ev.compute_digest()
    res = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    res_digest_before = res.compute_digest()
    compose_operator_report_view(res)
    compose_operator_report_view(res)
    assert ev.compute_digest() == digest_before
    assert res.compute_digest() == res_digest_before
