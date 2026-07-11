"""Phase 134E.2 — focused tests for Evidence Extraction
(``pcae.core.evidence_extraction``).

This module is not yet active lifecycle authority. Regression coverage
for existing Canonical Engineering Evidence / phase-report / notification
/ finalization behavior is provided by re-running the existing suites
unchanged (none of which import or reference this new module).
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import subprocess
import sys
from types import MappingProxyType

import pytest

from pcae.core import evidence_extraction as ee
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


# ─────────────────────────────────────────────────────────────────────────────
# Fixture builder — supplies every required category PRESENT for a given
# phase class under the Phase Report profile, so tests can start from a
# genuinely COMPLETE baseline and then selectively degrade it.
# ─────────────────────────────────────────────────────────────────────────────

def _identity(phase_id: str = "999X") -> EvidenceIdentity:
    return EvidenceIdentity(phase=EvidencePhaseIdentity(phase_id=phase_id, phase_name="Test", source="cli_argument"))


def _full_applicability(phase_class: PhaseClass, profile_id: str = PROFILE_ID_PHASE_REPORT) -> dict:
    """PRESENT for every category the given profile strictly REQUIREs for
    this phase class; NOT_APPLICABLE elsewhere (including CONDITIONALLY_
    REQUIRED and OPTIONAL categories, which are deliberately left absent
    by default so tests can distinguish "hard required and satisfied"
    from "conditionally required and absent" from "optional and absent").
    """
    profile = get_profile(profile_id)
    app = {}
    for category in REQUIRED_APPLICABILITY_CATEGORIES:
        requirement = profile.requirement_for(category, phase_class)
        if requirement == RequirementLevel.REQUIRED:
            app[category] = Applicability.PRESENT
        else:
            app[category] = Applicability.NOT_APPLICABLE
    return app


def _content_for(category: str):
    """A minimal, valid non-empty tuple value for an applicability-tracked
    category, so marking it PRESENT satisfies CEE's own contradictory-
    status check.
    """
    if category in ("architectural_findings", "implementation_findings",
                     "verification_findings", "defects_discovered",
                     "technical_debt_reviewed", "technical_debt_introduced"):
        return (FindingRecord(f"F-{category}", FindingClassification.CONFIRMED, "finding", "component"),)
    if category in ("defects_repaired", "incorrect_assumptions_corrected"):
        original = FindingRecord(f"F-{category}", FindingClassification.BLOCKING, "issue", "component")
        return (RepairRecord(original, "fixed it", "component.py", "verified", FindingClassification.CONFIRMED),)
    if category == "engineering_actions":
        return ("did the engineering work",)
    if category == "notable_engineering_knowledge":
        return ("a durable lesson",)
    if category in ("no_go_confirmations", "architectural_boundary_confirmations"):
        return ("confirmed boundary",)
    raise AssertionError(f"unhandled category {category}")  # pragma: no cover


def _minimal_complete_evidence(
    phase_class: PhaseClass, profile_id: str = PROFILE_ID_PHASE_REPORT, **overrides,
) -> CanonicalEngineeringEvidence:
    app = _full_applicability(phase_class, profile_id)
    tuple_fields = {}
    for category, disposition in app.items():
        tuple_fields[category] = _content_for(category) if disposition == Applicability.PRESENT else ()

    kwargs = dict(
        identity=_identity(),
        phase_class=phase_class,
        task_id=None,
        objective="minimal complete objective",
        engineering_actions=tuple_fields["engineering_actions"],
        architectural_findings=tuple_fields["architectural_findings"],
        implementation_findings=tuple_fields["implementation_findings"],
        verification_findings=tuple_fields["verification_findings"],
        defects_discovered=tuple_fields["defects_discovered"],
        defects_repaired=tuple_fields["defects_repaired"],
        incorrect_assumptions_corrected=tuple_fields["incorrect_assumptions_corrected"],
        technical_debt_reviewed=tuple_fields["technical_debt_reviewed"],
        technical_debt_introduced=tuple_fields["technical_debt_introduced"],
        notable_engineering_knowledge=tuple_fields["notable_engineering_knowledge"],
        governance_results=(GovernanceResultItem("pcae_check", "passed"),),
        test_results=(TestResultItem("fast_green", "1/1", "passed"),),
        repository_state=RepositoryStateSnapshot(commit="abc1234", branch="main", pushed_status="pushed", origin_main_head_count=0, clean=True),
        runtime_state=RuntimeStateSnapshot(runtime_state="Observed", maximum_capability="observe", execution_availability="unavailable"),
        no_go_confirmations=tuple_fields["no_go_confirmations"],
        architectural_boundary_confirmations=tuple_fields["architectural_boundary_confirmations"],
        track_progress="minimal track progress",
        recommended_next_phase="999Y",
        commit_and_push=CommitPushInfo(commits=("abc1234",), pushed_status="pushed", origin_main_head_count=0),
        provenance=(),
        uncertainty=(),
        limitations=(),
        correction=CorrectionMetadata(),
        applicability=MappingProxyType(app),
        created_at="2026-01-01T00:00:00+00:00",
    )
    kwargs.update(overrides)
    return CanonicalEngineeringEvidence(**kwargs).finalize()


# ─────────────────────────────────────────────────────────────────────────────
# 1-4: profile registration and fail-closed profile/version lookup
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_report_profile_registration():
    profile = get_profile(PROFILE_ID_PHASE_REPORT)
    assert profile.profile_id == PROFILE_ID_PHASE_REPORT
    assert set(profile.supported_phase_classes) == set(PhaseClass)


def test_operator_report_profile_registration():
    profile = get_profile(PROFILE_ID_OPERATOR_REPORT)
    assert profile.profile_id == PROFILE_ID_OPERATOR_REPORT
    assert set(profile.supported_phase_classes) == set(PhaseClass)


def test_unknown_profile_fails_closed():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    with pytest.raises(ValueError):
        extract(ev, "not_a_real_profile")


def test_unsupported_profile_version_fails_closed():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    with pytest.raises(ValueError):
        extract(ev, PROFILE_ID_PHASE_REPORT, profile_version="99.9")


# ─────────────────────────────────────────────────────────────────────────────
# 5-10: Phase Report profile extraction per phase class
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase_class", list(PhaseClass))
def test_phase_report_extraction_per_phase_class(phase_class):
    ev = _minimal_complete_evidence(phase_class)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    # COMPLETE_WITH_LIMITATIONS is expected here: the fixture intentionally
    # leaves conditionally-required categories (e.g. defects_discovered)
    # absent, which softly degrades completeness without ever reaching
    # INCOMPLETE/INVALID (no hard-REQUIRED category is missing).
    assert result.completeness in (
        ExtractionCompleteness.COMPLETE, ExtractionCompleteness.COMPLETE_WITH_LIMITATIONS,
    )
    assert len(result.selected_evidence) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 11-13: Operator Report profile extraction per phase class (subset)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase_class", [PhaseClass.ARCHITECTURE, PhaseClass.IMPLEMENTATION, PhaseClass.VERIFICATION])
def test_operator_report_extraction_per_phase_class(phase_class):
    ev = _minimal_complete_evidence(phase_class, profile_id=PROFILE_ID_OPERATOR_REPORT)
    result = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    # Only no_go_confirmations is conditionally-required (not hard-REQUIRED)
    # under the Operator Report profile too -- COMPLETE_WITH_LIMITATIONS
    # is an expected, non-degraded-below-that outcome.
    assert result.completeness in (
        ExtractionCompleteness.COMPLETE, ExtractionCompleteness.COMPLETE_WITH_LIMITATIONS,
    )
    assert set(result.missing_required) <= {
        "no_go_confirmations", "architectural_findings", "implementation_findings",
        "verification_findings",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 14: all thirteen PFR categories represented
# ─────────────────────────────────────────────────────────────────────────────

def test_all_pfr_categories_represented_in_phase_report_extraction():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    selected_categories = {item.category for item in result.selected_evidence}
    disclosed_categories = {d.excluded_category for d in result.filtering_disclosures}
    covered = selected_categories | disclosed_categories | set(result.missing_required)
    # PFR-001's thirteen sections all trace to at least one extraction category.
    pfr_source_categories = {
        "identity", "repository_state", "commit_and_push",  # Phase Identity
        "objective", "engineering_actions",  # Executive Summary
        "architectural_findings",  # Architectural Findings
        "implementation_findings",  # Implementation Findings
        "verification_findings",  # Verification Findings
        "technical_debt_reviewed", "technical_debt_introduced",  # Technical Debt Review
        "governance_results",  # Governance Results
        "test_results",  # Test Results
        "no_go_confirmations",  # No-Go Confirmation
        "architectural_boundary_confirmations",  # Architectural Boundary Confirmation
        "track_progress",  # Track Progress
        "recommended_next_phase",  # Next Phase
        "notable_engineering_knowledge",  # Notable Engineering Knowledge
    }
    assert pfr_source_categories <= covered


# ─────────────────────────────────────────────────────────────────────────────
# 15: operator decision-completeness categories represented
# ─────────────────────────────────────────────────────────────────────────────

def test_operator_decision_completeness_categories_represented():
    ev = _minimal_complete_evidence(PhaseClass.IMPLEMENTATION, profile_id=PROFILE_ID_OPERATOR_REPORT)
    result = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    selected_categories = {item.category for item in result.selected_evidence}
    required_for_decisions = {
        # architectural_findings is only CONDITIONALLY_REQUIRED for
        # implementation/verification classes under this profile (an
        # implementation phase may or may not touch architecture) --
        # excluded from this strict "always selected" set deliberately.
        "defects_discovered", "defects_repaired", "incorrect_assumptions_corrected",
        "technical_debt_reviewed", "implementation_findings",
        "governance_results", "test_results", "repository_state", "runtime_state",
        "recommended_next_phase", "notable_engineering_knowledge",
    }
    assert required_for_decisions <= selected_categories


def test_operator_report_status_only_extraction_is_invalid():
    """A minimal status/tests/next-phase-only disposition is invalid for
    the Operator Report profile -- confirmed by marking everything else
    NOT_APPLICABLE and observing INCOMPLETE/INVALID, not COMPLETE.
    """
    app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}
    ev = CanonicalEngineeringEvidence(
        identity=_identity(), phase_class=PhaseClass.ARCHITECTURE, task_id=None,
        objective="status only", engineering_actions=(),
        architectural_findings=(), implementation_findings=(), verification_findings=(),
        defects_discovered=(), defects_repaired=(), incorrect_assumptions_corrected=(),
        technical_debt_reviewed=(), technical_debt_introduced=(),
        notable_engineering_knowledge=(),
        governance_results=(GovernanceResultItem("pcae_check", "passed"),),
        test_results=(TestResultItem("fast_green", "1/1", "passed"),),
        repository_state=RepositoryStateSnapshot(commit="abc1234", branch="main", pushed_status="pushed", origin_main_head_count=0, clean=True),
        runtime_state=RuntimeStateSnapshot(runtime_state="Observed", maximum_capability="observe", execution_availability="unavailable"),
        no_go_confirmations=(), architectural_boundary_confirmations=(),
        track_progress="x", recommended_next_phase="999Y",
        commit_and_push=CommitPushInfo(commits=("abc1234",), pushed_status="pushed", origin_main_head_count=0),
        provenance=(), uncertainty=(), limitations=(), correction=CorrectionMetadata(),
        applicability=MappingProxyType(app), created_at="2026-01-01T00:00:00+00:00",
    ).finalize()
    result = extract(ev, PROFILE_ID_OPERATOR_REPORT)
    assert result.completeness != ExtractionCompleteness.COMPLETE
    assert len(result.missing_required) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 16-19: required missing, conditionally required, optional filtering,
# explicit not-applicable
# ─────────────────────────────────────────────────────────────────────────────

def test_required_category_missing_recorded():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["governance_results"] = Applicability.PRESENT  # scalar; unaffected
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "technical_debt_reviewed": Applicability.UNKNOWN}),
        technical_debt_reviewed=(),
        uncertainty=(UncertaintyItem(category="technical_debt_reviewed", description="unresolved",
                                      affected_evidence=("technical_debt_reviewed",),
                                      source="s", verification_state="unresolved"),),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert "technical_debt_reviewed" in result.missing_required
    assert result.completeness == ExtractionCompleteness.INCOMPLETE


def test_conditionally_required_category_missing_softens_to_limitations():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)  # defects_* are CONDITIONALLY_REQUIRED, absent
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert "defects_discovered" in result.missing_required
    assert result.completeness == ExtractionCompleteness.COMPLETE_WITH_LIMITATIONS


def test_optional_category_filtering_disclosed():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)  # technical_debt_introduced OPTIONAL, absent
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    disclosed = {d.excluded_category for d in result.filtering_disclosures}
    assert "technical_debt_introduced" in disclosed


def test_explicit_not_applicable_handling():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)  # implementation_findings NOT_APPLICABLE for architecture
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    disclosed = {d.excluded_category: d for d in result.filtering_disclosures}
    assert "implementation_findings" in disclosed
    assert "not applicable" in disclosed["implementation_findings"].profile_rule


# ─────────────────────────────────────────────────────────────────────────────
# 20-22: unknown/unavailable required evidence, invalid applicability
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_required_evidence_recorded_incomplete():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["governance_results"] = Applicability.PRESENT
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "notable_engineering_knowledge": Applicability.UNKNOWN}),
        notable_engineering_knowledge=(),
        uncertainty=(UncertaintyItem(category="notable_engineering_knowledge", description="unresolved",
                                      affected_evidence=("notable_engineering_knowledge",),
                                      source="s", verification_state="unresolved"),),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert "notable_engineering_knowledge" in result.missing_required
    assert result.completeness == ExtractionCompleteness.INCOMPLETE


def test_unavailable_required_evidence_recorded_incomplete():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "governance_results" if False else "engineering_actions": Applicability.UNAVAILABLE}),
        engineering_actions=(),
        limitations=(LimitationItem(category="engineering_actions", description="data unavailable",
                                     affected_evidence=("engineering_actions",)),),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert "engineering_actions" in result.missing_required
    assert result.completeness == ExtractionCompleteness.INCOMPLETE


def test_invalid_applicability_fails_closed():
    """A required category the evidence author explicitly marked
    NOT_APPLICABLE, while the profile requires PRESENT for this phase
    class, is a genuine contradiction -- extraction returns INVALID, not
    a silently-accepted partial success.
    """
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "architectural_findings": Applicability.NOT_APPLICABLE}),
        architectural_findings=(),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert result.completeness == ExtractionCompleteness.INVALID
    assert any(d.code == "required_category_marked_not_applicable" for d in result.diagnostics)


# ─────────────────────────────────────────────────────────────────────────────
# 23: empty successful extraction prohibited
# ─────────────────────────────────────────────────────────────────────────────

def test_empty_successful_extraction_prohibited():
    src = inspect.getsource(ee.extract)
    assert "silent empty success" in src.lower() or "zero selected" in src.lower()
    # Behaviorally: a genuinely minimal-but-complete record always
    # selects at least identity/governance/test/repository/runtime.
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert len(result.selected_evidence) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 24-30: findings/repairs/knowledge preservation
# ─────────────────────────────────────────────────────────────────────────────

def test_findings_preserved_verbatim():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "architectural_findings")
    assert item.value == ev.architectural_findings


def test_repaired_finding_history_preserved():
    original = FindingRecord("F1", FindingClassification.BLOCKING, "bug", "module_x")
    repair = RepairRecord(original, "fixed", "module_x.py", "verified", FindingClassification.CONFIRMED)
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["defects_repaired"] = Applicability.PRESENT
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app), defects_repaired=(repair,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "defects_repaired")
    assert item.value[0].original_finding.classification == FindingClassification.BLOCKING
    assert item.value[0].resulting_status == FindingClassification.CONFIRMED


def test_blocking_finding_preserved():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F1", FindingClassification.BLOCKING, "bug", "x")
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app), defects_discovered=(finding,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "defects_discovered")
    assert item.value[0].classification == FindingClassification.BLOCKING


def test_non_blocking_finding_preserved():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F1", FindingClassification.NON_BLOCKING, "minor", "x")
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app), defects_discovered=(finding,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "defects_discovered")
    assert item.value[0].classification == FindingClassification.NON_BLOCKING


def test_corrected_assumption_preserved():
    original = FindingRecord("A1", FindingClassification.NON_BLOCKING, "wrong assumption", "x")
    repair = RepairRecord(original, "corrected", "x.py", "verified", FindingClassification.CONFIRMED)
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["incorrect_assumptions_corrected"] = Applicability.PRESENT
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app), incorrect_assumptions_corrected=(repair,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "incorrect_assumptions_corrected")
    assert item.value[0].original_finding.description == "wrong assumption"


def test_technical_debt_preserved():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "technical_debt_reviewed")
    assert len(item.value) > 0


def test_notable_knowledge_preserved():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "notable_engineering_knowledge")
    assert item.value == ev.notable_engineering_knowledge


# ─────────────────────────────────────────────────────────────────────────────
# 31-34: uncertainty/limitations automatic preservation, orphan rejection
# ─────────────────────────────────────────────────────────────────────────────

def test_uncertainty_automatically_preserved():
    u = UncertaintyItem(category="c", description="d", affected_evidence=("engineering_actions",),
                         source="s", verification_state="unresolved")
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE, uncertainty=(u,))
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert u in result.uncertainty
    item = next(i for i in result.selected_evidence if i.category == "engineering_actions")
    assert "c" in item.uncertainty_refs or "engineering_actions" in [x for x in item.uncertainty_refs]


def test_limitations_automatically_preserved():
    lim = LimitationItem(category="c", description="d", affected_evidence=("engineering_actions",))
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE, limitations=(lim,))
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert lim in result.limitations


def test_orphan_uncertainty_rejected():
    """CEE's own construction only requires affected_evidence non-empty,
    not that it names a real category -- extraction defensively rejects
    an uncertainty entry naming a category outside the known set.
    """
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    bad_uncertainty = UncertaintyItem(category="c", description="d",
                                       affected_evidence=("not_a_real_category",),
                                       source="s", verification_state="unresolved")
    import dataclasses as dc
    ev_bad = dc.replace(ev, uncertainty=(bad_uncertainty,))
    with pytest.raises(ValueError):
        extract(ev_bad, PROFILE_ID_PHASE_REPORT)


def test_orphan_limitation_rejected():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    bad_limitation = LimitationItem(category="c", description="d", affected_evidence=("not_a_real_category",))
    import dataclasses as dc
    ev_bad = dc.replace(ev, limitations=(bad_limitation,))
    with pytest.raises(ValueError):
        extract(ev_bad, PROFILE_ID_PHASE_REPORT)


# ─────────────────────────────────────────────────────────────────────────────
# 35-37: provenance, repository/runtime state, no-go boundaries preserved
# ─────────────────────────────────────────────────────────────────────────────

def test_provenance_preserved():
    prov = EvidenceProvenanceRecord(covers="engineering_actions", source_artifact="log",
                                     source_command=None, source_phase_id="999X",
                                     derivation_path="direct", verification_state="verified")
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE, provenance=(prov,))
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert prov in result.provenance
    item = next(i for i in result.selected_evidence if i.category == "engineering_actions")
    assert prov in item.provenance


def test_repository_and_runtime_state_preserved():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    repo_item = next(i for i in result.selected_evidence if i.category == "repository_state")
    runtime_item = next(i for i in result.selected_evidence if i.category == "runtime_state")
    assert repo_item.value == ev.repository_state
    assert runtime_item.value == ev.runtime_state


def test_no_go_boundaries_preserved():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["no_go_confirmations"] = Applicability.PRESENT
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app),
        no_go_confirmations=("no execution capability introduced",),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "no_go_confirmations")
    assert item.value == ("no execution capability introduced",)


# ─────────────────────────────────────────────────────────────────────────────
# 38-39: filtering disclosure, no strengthening
# ─────────────────────────────────────────────────────────────────────────────

def test_filtering_disclosure_shape():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    for d in result.filtering_disclosures:
        assert d.excluded_category in EXTRACTION_CATEGORIES
        assert isinstance(d.material, bool)
        assert isinstance(d.still_available_in_canonical_record, bool)


def test_no_strengthening_classifications_unchanged():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["defects_discovered"] = Applicability.PRESENT
    finding = FindingRecord("F1", FindingClassification.BLOCKING, "bug", "x")
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app), defects_discovered=(finding,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "defects_discovered")
    assert item.value[0].classification == FindingClassification.BLOCKING  # never upgraded to CONFIRMED


def test_no_strengthening_unknown_not_promoted_to_present():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "engineering_actions": Applicability.UNAVAILABLE}),
        engineering_actions=(),
        limitations=(LimitationItem(category="engineering_actions", description="x",
                                     affected_evidence=("engineering_actions",)),),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert "engineering_actions" in result.missing_required
    assert not any(i.category == "engineering_actions" for i in result.selected_evidence)


# ─────────────────────────────────────────────────────────────────────────────
# 40-43: determinism, serialization, digest
# ─────────────────────────────────────────────────────────────────────────────

def test_deterministic_ordering():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    r1 = extract(ev, PROFILE_ID_PHASE_REPORT)
    r2 = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert [i.category for i in r1.selected_evidence] == [i.category for i in r2.selected_evidence]


def test_deterministic_serialization():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    s1 = json.dumps(result.to_dict(include_digest=False), sort_keys=True)
    s2 = json.dumps(result.to_dict(include_digest=False), sort_keys=True)
    assert s1 == s2


def test_stable_source_identity_and_digest():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert result.source_evidence_id == ev.identity.evidence_id
    assert result.source_record_digest == ev.compute_digest()


def test_stable_extraction_digest():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    r1 = extract(ev, PROFILE_ID_PHASE_REPORT)
    r2 = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert r1.compute_digest() == r2.compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# 44-48: agent/model/transport independence, no filesystem/network
# ─────────────────────────────────────────────────────────────────────────────

def test_agent_model_independence():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    for caller in ("deepseek-agent", "claude-agent", "codex-agent", "unknown-future-agent"):
        prov = EvidenceProvenanceRecord(covers="engineering_actions", source_artifact="cli",
                                         source_command=f"invoked-by:{caller}", source_phase_id="999X",
                                         derivation_path="direct", verification_state="verified")
        import dataclasses as dc
        ev_with_prov = dc.replace(ev, provenance=(prov,))
        result = extract(ev_with_prov, PROFILE_ID_PHASE_REPORT)
        assert result.completeness in (ExtractionCompleteness.COMPLETE, ExtractionCompleteness.COMPLETE_WITH_LIMITATIONS)


def test_no_transport_or_telegram_dependency():
    # Prose in the module docstring legitimately explains *why* this
    # module is disconnected from notification/delivery (mirroring
    # canonical_engineering_evidence.py's own convention). What matters
    # is that no concrete transport/adapter symbol is actually used.
    src = inspect.getsource(ee)
    for marker in ("TelegramSink(", "dispatch(", "NotificationSink", "import notifications"):
        assert marker not in src


def test_no_rendering_dependency():
    # Same convention: the module docstring's architectural-position
    # diagram legitimately names "Rendering" as the *next* stage it is
    # deliberately not implementing. No renderer symbol is used or
    # imported.
    src = inspect.getsource(ee)
    for marker in ("import rendering", "Renderer(", "render_markdown", "to_markdown", "to_html"):
        assert marker not in src


def test_no_filesystem_or_network_behavior():
    src = inspect.getsource(ee)
    for marker in ("open(", "subprocess", "socket.", "urllib", "requests."):
        assert marker not in src


def test_module_has_only_cee_and_stdlib_imports():
    import ast
    tree = ast.parse(inspect.getsource(ee))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module == "pcae.core.canonical_engineering_evidence" or not node.module.startswith("pcae")


# ─────────────────────────────────────────────────────────────────────────────
# 49-50: existing evidence model immutable; existing lifecycle unchanged
# ─────────────────────────────────────────────────────────────────────────────

def test_existing_evidence_model_remains_immutable_after_extraction():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    digest_before = ev.compute_digest()
    extract(ev, PROFILE_ID_PHASE_REPORT)
    extract(ev, PROFILE_ID_OPERATOR_REPORT)
    assert ev.compute_digest() == digest_before


def test_no_existing_lifecycle_module_imports_evidence_extraction():
    import pathlib
    src_root = pathlib.Path(ee.__file__).resolve().parent.parent
    lifecycle_modules = [
        src_root / "core" / "phase_reports.py",
        src_root / "core" / "notifications.py",
        src_root / "core" / "notification_certification.py",
        src_root / "core" / "notification_config.py",
        src_root / "core" / "repository_transition_validator.py",
        src_root / "commands" / "phase.py",
    ]
    for path in lifecycle_modules:
        assert "evidence_extraction" not in path.read_text()


# ─────────────────────────────────────────────────────────────────────────────
# 51-52: byte determinism, cross-process determinism
# ─────────────────────────────────────────────────────────────────────────────

def test_byte_determinism():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    b1 = json.dumps(result.to_dict(include_digest=False), sort_keys=True).encode()
    b2 = json.dumps(result.to_dict(include_digest=False), sort_keys=True).encode()
    assert b1 == b2


def test_cross_process_determinism():
    src_dir = str(__import__("pathlib").Path(ee.__file__).resolve().parent.parent)
    code = (
        "import sys; sys.path.insert(0, %r); "
        "from types import MappingProxyType; "
        "from pcae.core.canonical_engineering_evidence import ("
        "CanonicalEngineeringEvidence, EvidenceIdentity, EvidencePhaseIdentity, PhaseClass, "
        "Applicability, RepositoryStateSnapshot, RuntimeStateSnapshot, CommitPushInfo, "
        "CorrectionMetadata, REQUIRED_APPLICABILITY_CATEGORIES); "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_PHASE_REPORT; "
        "app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}; "
        "app['engineering_actions'] = Applicability.PRESENT; "
        "app['notable_engineering_knowledge'] = Applicability.PRESENT; "
        "app['technical_debt_reviewed'] = Applicability.PRESENT; "
        "app['architectural_boundary_confirmations'] = Applicability.PRESENT; "
        "from pcae.core.canonical_engineering_evidence import FindingRecord, FindingClassification, "
        "GovernanceResultItem, TestResultItem; "
        "ev = CanonicalEngineeringEvidence("
        "identity=EvidenceIdentity(phase=EvidencePhaseIdentity(phase_id='999X', phase_name='X', source='cli_argument')), "
        "phase_class=PhaseClass.ARCHITECTURE, task_id=None, objective='cross-process', "
        "engineering_actions=('did it',), architectural_findings=(), implementation_findings=(), verification_findings=(), "
        "defects_discovered=(), defects_repaired=(), incorrect_assumptions_corrected=(), "
        "technical_debt_reviewed=(FindingRecord('D1', FindingClassification.CONFIRMED, 'x', 'y'),), technical_debt_introduced=(), "
        "notable_engineering_knowledge=('lesson',), "
        "governance_results=(GovernanceResultItem('pcae_check', 'passed'),), "
        "test_results=(TestResultItem('fast_green', '1/1', 'passed'),), "
        "repository_state=RepositoryStateSnapshot(commit='abc1234', branch='main', pushed_status='pushed', origin_main_head_count=0, clean=True), "
        "runtime_state=RuntimeStateSnapshot(runtime_state='Observed', maximum_capability='observe', execution_availability='unavailable'), "
        "no_go_confirmations=(), architectural_boundary_confirmations=('x',), "
        "track_progress='x', recommended_next_phase='999Y', "
        "commit_and_push=CommitPushInfo(commits=('abc1234',), pushed_status='pushed', origin_main_head_count=0), "
        "provenance=(), uncertainty=(), limitations=(), correction=CorrectionMetadata(), "
        "applicability=MappingProxyType(app), created_at='2026-01-01T00:00:00+00:00').finalize(); "
        "print(extract(ev, PROFILE_ID_PHASE_REPORT).compute_digest())"
    ) % src_dir
    r1 = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    r2 = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert r1.stdout.strip() == r2.stdout.strip()
    assert len(r1.stdout.strip()) == 64


# ─────────────────────────────────────────────────────────────────────────────
# 53-55: duplicate normalization, invalid canonical evidence rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_duplicate_category_normalization_not_applicable():
    """Extraction categories map 1:1 to CEE fields; there is no duplicate
    category to normalize across profiles -- confirmed structurally.
    """
    assert len(EXTRACTION_CATEGORIES) == len(set(EXTRACTION_CATEGORIES))


def test_duplicate_finding_handling_preserved_from_source():
    """Extraction does not deduplicate findings -- it selects exactly
    what the canonical record contains, preserving CEE's own duplicate-
    identifier validation as the sole authority on that question.
    """
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "technical_debt_reviewed")
    assert item.value == ev.technical_debt_reviewed


def test_invalid_canonical_evidence_rejected():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    import dataclasses as dc
    draft = dc.replace(ev, state=__import__("pcae.core.canonical_engineering_evidence", fromlist=["EvidenceRecordState"]).EvidenceRecordState.DRAFT, finalized_at=None)
    with pytest.raises(ValueError):
        extract(draft, PROFILE_ID_PHASE_REPORT)


# ─────────────────────────────────────────────────────────────────────────────
# 56-59: completeness result classification
# ─────────────────────────────────────────────────────────────────────────────

def test_complete_result():
    """Every category the profile could possibly ask for -- required or
    conditionally-required -- is filled with real content and carries no
    uncertainty/limitation: the strict COMPLETE outcome.
    """
    app = {c: Applicability.PRESENT for c in REQUIRED_APPLICABILITY_CATEGORIES}
    app["implementation_findings"] = Applicability.NOT_APPLICABLE  # genuinely N/A for architecture
    app["verification_findings"] = Applicability.NOT_APPLICABLE
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType(app),
        defects_discovered=_content_for("defects_discovered"),
        defects_repaired=_content_for("defects_repaired"),
        incorrect_assumptions_corrected=_content_for("incorrect_assumptions_corrected"),
        technical_debt_introduced=_content_for("technical_debt_introduced"),
        no_go_confirmations=_content_for("no_go_confirmations"),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert result.completeness == ExtractionCompleteness.COMPLETE


def test_complete_with_limitations_result():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)  # conditional defects_* categories absent
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert result.completeness == ExtractionCompleteness.COMPLETE_WITH_LIMITATIONS


def test_incomplete_result():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "governance_results" if False else "notable_engineering_knowledge": Applicability.UNKNOWN}),
        notable_engineering_knowledge=(),
        uncertainty=(UncertaintyItem(category="notable_engineering_knowledge", description="x",
                                      affected_evidence=("notable_engineering_knowledge",),
                                      source="s", verification_state="unresolved"),),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert result.completeness == ExtractionCompleteness.INCOMPLETE


def test_invalid_result():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "architectural_findings": Applicability.NOT_APPLICABLE}),
        architectural_findings=(),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert result.completeness == ExtractionCompleteness.INVALID


# ─────────────────────────────────────────────────────────────────────────────
# 60: future-profile extensibility without existing-profile change
# ─────────────────────────────────────────────────────────────────────────────

def test_future_profile_extensibility_without_existing_profile_change():
    from pcae.core.evidence_extraction import (
        CategoryRule, ExtractionProfile, register_profile, _all_required,
        EXTRACTION_CATEGORIES as CATS,
    )
    before = get_profile(PROFILE_ID_PHASE_REPORT)
    before_digest_source = json.dumps(
        [(r.category, {k.value: v.value for k, v in r.requirement_by_phase_class.items()})
         for r in before.category_rules],
        sort_keys=True,
    )

    future_rules = tuple(CategoryRule(cat, _all_required(RequirementLevel.OPTIONAL)) for cat in CATS)
    future_profile = ExtractionProfile(
        profile_id="future_changelog_v1", profile_version="1.0",
        supported_phase_classes=frozenset(PhaseClass), category_rules=future_rules,
    )
    register_profile(future_profile)

    after = get_profile(PROFILE_ID_PHASE_REPORT)
    after_digest_source = json.dumps(
        [(r.category, {k.value: v.value for k, v in r.requirement_by_phase_class.items()})
         for r in after.category_rules],
        sort_keys=True,
    )
    assert before_digest_source == after_digest_source
    assert get_profile("future_changelog_v1").profile_id == "future_changelog_v1"


# ─────────────────────────────────────────────────────────────────────────────
# CategoryRule / ExtractionProfile construction-time validation
# ─────────────────────────────────────────────────────────────────────────────

def test_category_rule_requires_all_phase_classes_explicit():
    from pcae.core.evidence_extraction import CategoryRule
    with pytest.raises(ValueError):
        CategoryRule("objective", MappingProxyType({PhaseClass.ARCHITECTURE: RequirementLevel.REQUIRED}))


def test_extraction_profile_requires_all_categories_covered():
    from pcae.core.evidence_extraction import CategoryRule, ExtractionProfile, _all_required
    with pytest.raises(ValueError):
        ExtractionProfile(
            profile_id="incomplete_profile", profile_version="1.0",
            supported_phase_classes=frozenset(PhaseClass),
            category_rules=(CategoryRule("objective", _all_required(RequirementLevel.REQUIRED)),),
        )
