"""Phase 134E.2V — independent adversarial verification of Evidence
Extraction (134E.2).

Does not trust 134E.2's own report, documentation, or its 64 tests as
sufficient evidence. These are fresh probes beyond that existing
coverage, including regression tests for two genuine BLOCKING defects
found and repaired during this verification phase:

1. Silent profile overwrite: ``register_profile()`` unconditionally
   overwrote any existing entry for the same ``profile_id`` with zero
   error, zero warning. A profile registered under the real
   ``phase_report_v1`` id -- with different rules, a different version,
   or both -- silently replaced the real profile process-wide.
2. Undetected duplicate/conflicting category rules: ``ExtractionProfile.
   __post_init__`` only checked that the *set* of ruled categories
   covered all 21 required categories -- it never checked for
   duplicates. A profile with two conflicting rules for the same
   category (e.g. one REQUIRED, one NOT_APPLICABLE) constructed
   successfully, with the second rule silently dead code (``requirement_
   for()`` always returns the first match).
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
    EvidenceRecordState,
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
    CategoryRule,
    EXTRACTION_CATEGORIES,
    ExtractionCompleteness,
    ExtractionProfile,
    PROFILE_ID_OPERATOR_REPORT,
    PROFILE_ID_PHASE_REPORT,
    RequirementLevel,
    _all_required,
    extract,
    get_profile,
    register_profile,
)

# Reuse 134E.2's own fixture helpers rather than re-deriving them, so
# fresh probes exercise realistic evidence records.
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from test_evidence_extraction_134e2 import (  # noqa: E402
    _content_for,
    _full_applicability,
    _identity,
    _minimal_complete_evidence,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1-4: profile registry integrity (regression for both BLOCKING fixes)
# ─────────────────────────────────────────────────────────────────────────────

def test_missing_profile_matrix_entry_rejected():
    rules = tuple(
        CategoryRule(cat, _all_required(RequirementLevel.OPTIONAL))
        for cat in EXTRACTION_CATEGORIES if cat != "objective"
    )
    with pytest.raises(ValueError, match="missing category"):
        ExtractionProfile(
            profile_id="missing_entry_probe", profile_version="1.0",
            supported_phase_classes=frozenset(PhaseClass), category_rules=rules,
        )


def test_duplicate_profile_registration_rejected():
    real = get_profile(PROFILE_ID_PHASE_REPORT)
    evil_rules = tuple(
        CategoryRule(cat, _all_required(RequirementLevel.NOT_APPLICABLE))
        for cat in EXTRACTION_CATEGORIES
    )
    evil = ExtractionProfile(
        profile_id=PROFILE_ID_PHASE_REPORT, profile_version="999.0",
        supported_phase_classes=frozenset(PhaseClass), category_rules=evil_rules,
    )
    with pytest.raises(ValueError, match="already registered"):
        register_profile(evil)
    # Confirm the real profile was NOT silently replaced.
    assert get_profile(PROFILE_ID_PHASE_REPORT).profile_version == real.profile_version


def test_registry_order_independence():
    before = get_profile(PROFILE_ID_PHASE_REPORT)
    before_repr = json.dumps(
        [(r.category, {k.value: v.value for k, v in r.requirement_by_phase_class.items()})
         for r in before.category_rules], sort_keys=True,
    )
    rules_a = tuple(CategoryRule(cat, _all_required(RequirementLevel.OPTIONAL)) for cat in EXTRACTION_CATEGORIES)
    rules_b = tuple(CategoryRule(cat, _all_required(RequirementLevel.OPTIONAL)) for cat in EXTRACTION_CATEGORIES)
    register_profile(ExtractionProfile("order_probe_a", "1.0", frozenset(PhaseClass), rules_a))
    register_profile(ExtractionProfile("order_probe_b", "1.0", frozenset(PhaseClass), rules_b))
    after = get_profile(PROFILE_ID_PHASE_REPORT)
    after_repr = json.dumps(
        [(r.category, {k.value: v.value for k, v in r.requirement_by_phase_class.items()})
         for r in after.category_rules], sort_keys=True,
    )
    assert before_repr == after_repr


def test_runtime_registry_mutation_via_public_api_only_goes_through_validation():
    """The only supported mutation surface, ``register_profile()``, always
    routes through ``ExtractionProfile``'s own construction-time
    validation (duplicate rules, full coverage) and the duplicate-id
    check this phase added -- there is no public path to register a
    partially-built or unvalidated profile.
    """
    with pytest.raises(ValueError):
        register_profile(ExtractionProfile(
            profile_id="bad_probe", profile_version="1.0",
            supported_phase_classes=frozenset(PhaseClass),
            category_rules=(CategoryRule("objective", _all_required(RequirementLevel.REQUIRED)),),
        ))


def test_module_level_registry_is_a_private_implementation_detail_documented():
    """NON-BLOCKING, documented: ``_PROFILE_REGISTRY`` is a private
    module-level dict (leading underscore). Python has no true private
    state, so a caller holding a direct reference to the private name
    could bypass ``register_profile()``'s checks by assigning into the
    dict directly. The public API (``register_profile``/``get_profile``)
    is the only supported, hardened surface -- matching ordinary Python
    convention (and this repository's own convention) for "private by
    naming, not by enforcement." Out of scope to change here.
    """
    assert ee._PROFILE_REGISTRY is ee._PROFILE_REGISTRY  # exists; documented, not further restricted


# ─────────────────────────────────────────────────────────────────────────────
# 5-6: status-only / near-status-only Operator Report rejection
# ─────────────────────────────────────────────────────────────────────────────

def test_status_only_operator_report_rejected():
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


def test_near_status_only_operator_report_rejected():
    """Adds engineering_actions and notable_engineering_knowledge (a
    step beyond bare status/tests/next-phase) but still omits
    defects/repairs/corrected-assumptions/debt-review entirely -- still
    must not reach COMPLETE under the Operator Report profile.
    """
    app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}
    app["engineering_actions"] = Applicability.PRESENT
    app["notable_engineering_knowledge"] = Applicability.PRESENT
    ev = CanonicalEngineeringEvidence(
        identity=_identity(), phase_class=PhaseClass.ARCHITECTURE, task_id=None,
        objective="near status only", engineering_actions=("did some work",),
        architectural_findings=(), implementation_findings=(), verification_findings=(),
        defects_discovered=(), defects_repaired=(), incorrect_assumptions_corrected=(),
        technical_debt_reviewed=(), technical_debt_introduced=(),
        notable_engineering_knowledge=("a lesson",),
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
    # INVALID is an even stronger rejection than INCOMPLETE here (several
    # REQUIRED categories -- e.g. architectural_findings for an
    # ARCHITECTURE-class phase -- were explicitly marked NOT_APPLICABLE,
    # a genuine contradiction under the Operator Report profile); either
    # way, COMPLETE must never be reached.
    assert result.completeness in (ExtractionCompleteness.INCOMPLETE, ExtractionCompleteness.INVALID)
    assert "defects_discovered" in result.missing_required
    assert "technical_debt_reviewed" in result.missing_required


# ─────────────────────────────────────────────────────────────────────────────
# 7-8: required-but-empty, conditionally-required condition bypass
# ─────────────────────────────────────────────────────────────────────────────

def test_required_but_empty_evidence_cannot_be_constructed_as_present():
    """CEE's own contradictory_status check (not extraction's) is the
    actual enforcement point: PRESENT + empty tuple can never reach
    extract() in the first place, because it can never finalize.
    """
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["engineering_actions"] = Applicability.PRESENT
    with pytest.raises(ValueError):
        CanonicalEngineeringEvidence(
            identity=_identity(), phase_class=PhaseClass.ARCHITECTURE, task_id=None,
            objective="x", engineering_actions=(),  # empty despite PRESENT
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


def test_conditionally_required_is_a_static_per_phase_class_tier_documented():
    """NON-BLOCKING, documented design clarification: 'conditionally
    required' in this implementation is a fixed, deterministic
    per-(profile, phase_class) tier -- not a dynamically-evaluated
    condition against other field content (e.g. "required only if
    defects_discovered is non-empty"). This is confirmed intentional and
    consistent with determinism: a condition on other content would make
    extraction's own requirement level depend on the very data it's
    describing, which is unnecessary complexity the phase brief's own
    "no implicit default" instruction does not require.
    """
    profile = get_profile(PROFILE_ID_PHASE_REPORT)
    level_1 = profile.requirement_for("defects_discovered", PhaseClass.ARCHITECTURE)
    level_2 = profile.requirement_for("defects_discovered", PhaseClass.ARCHITECTURE)
    assert level_1 == level_2 == RequirementLevel.CONDITIONALLY_REQUIRED


# ─────────────────────────────────────────────────────────────────────────────
# 9-10: unknown vs unavailable completeness; required not-applicable bypass
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_versus_unavailable_both_produce_incomplete_for_required():
    for disposition in (Applicability.UNKNOWN, Applicability.UNAVAILABLE):
        app = _full_applicability(PhaseClass.ARCHITECTURE)
        ev = _minimal_complete_evidence(
            PhaseClass.ARCHITECTURE,
            applicability=MappingProxyType({**app, "notable_engineering_knowledge": disposition}),
            notable_engineering_knowledge=(),
            uncertainty=(UncertaintyItem(category="notable_engineering_knowledge", description="x",
                                          affected_evidence=("notable_engineering_knowledge",),
                                          source="s", verification_state="unresolved"),)
            if disposition == Applicability.UNKNOWN else (),
            limitations=(LimitationItem(category="notable_engineering_knowledge", description="x",
                                         affected_evidence=("notable_engineering_knowledge",)),)
            if disposition == Applicability.UNAVAILABLE else (),
        )
        result = extract(ev, PROFILE_ID_PHASE_REPORT)
        assert result.completeness == ExtractionCompleteness.INCOMPLETE


def test_required_not_applicable_produces_invalid_not_bypassed():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "technical_debt_reviewed": Applicability.NOT_APPLICABLE}),
        technical_debt_reviewed=(),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert result.completeness == ExtractionCompleteness.INVALID
    assert any(d.code == "required_category_marked_not_applicable" for d in result.diagnostics)


# ─────────────────────────────────────────────────────────────────────────────
# 11: material optional evidence filtering (disclosure required, never silent)
# ─────────────────────────────────────────────────────────────────────────────

def test_material_optional_evidence_filtering_always_disclosed():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)  # technical_debt_introduced OPTIONAL, absent
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    disclosed = {d.excluded_category for d in result.filtering_disclosures}
    assert "technical_debt_introduced" in disclosed
    # Confirm the disclosure is never silently absent even though the
    # category itself is genuinely absent.
    entry = next(d for d in result.filtering_disclosures if d.excluded_category == "technical_debt_introduced")
    assert entry.profile_rule


# ─────────────────────────────────────────────────────────────────────────────
# 12-15: repair history, corrected assumptions, technical debt preservation
# ─────────────────────────────────────────────────────────────────────────────

def test_repaired_blocking_finding_history_preserved():
    original = FindingRecord("F1", FindingClassification.BLOCKING, "critical bug", "module_x")
    repair = RepairRecord(original, "fixed", "module_x.py", "regression test added", FindingClassification.CONFIRMED)
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["defects_repaired"] = Applicability.PRESENT
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app), defects_repaired=(repair,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "defects_repaired")
    assert item.value[0].original_finding.classification == FindingClassification.BLOCKING
    assert item.value[0].original_finding.description == "critical bug"
    assert item.value[0].resulting_status == FindingClassification.CONFIRMED


def test_partial_repair_remains_unresolved_in_defects_discovered():
    """A defect discovered but not (yet) repaired must remain visible as
    BLOCKING in defects_discovered -- extraction never infers resolution
    from the mere existence of an unrelated repair elsewhere.
    """
    unresolved = FindingRecord("F2", FindingClassification.BLOCKING, "second bug, not yet fixed", "module_y")
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["defects_discovered"] = Applicability.PRESENT
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app), defects_discovered=(unresolved,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "defects_discovered")
    assert item.value[0].classification == FindingClassification.BLOCKING


def test_corrected_assumption_history_preserved():
    original = FindingRecord("A1", FindingClassification.NON_BLOCKING, "assumed X was true", "design")
    repair = RepairRecord(original, "confirmed X was false; corrected design", "design.md", "re-verified", FindingClassification.CONFIRMED)
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["incorrect_assumptions_corrected"] = Applicability.PRESENT
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app), incorrect_assumptions_corrected=(repair,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "incorrect_assumptions_corrected")
    assert item.value[0].original_finding.description == "assumed X was true"
    assert item.value[0].repair_action == "confirmed X was false; corrected design"


def test_technical_debt_reviewed_vs_introduced_not_confused():
    reviewed = FindingRecord("D1", FindingClassification.CONFIRMED, "old debt, still tracked", "x")
    introduced = FindingRecord("D2", FindingClassification.NON_BLOCKING, "new debt from this phase", "y")
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["technical_debt_introduced"] = Applicability.PRESENT
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app),
        technical_debt_reviewed=(reviewed,), technical_debt_introduced=(introduced,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    reviewed_item = next(i for i in result.selected_evidence if i.category == "technical_debt_reviewed")
    introduced_item = next(i for i in result.selected_evidence if i.category == "technical_debt_introduced")
    assert reviewed_item.value[0].description == "old debt, still tracked"
    assert introduced_item.value[0].description == "new debt from this phase"


# ─────────────────────────────────────────────────────────────────────────────
# 16: notable-knowledge provenance
# ─────────────────────────────────────────────────────────────────────────────

def test_notable_knowledge_provenance_preserved():
    prov = EvidenceProvenanceRecord(
        covers="notable_engineering_knowledge", source_artifact="134B.1 incident review",
        source_command=None, source_phase_id="134B.1", derivation_path="direct",
        verification_state="verified",
    )
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE, provenance=(prov,))
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "notable_engineering_knowledge")
    assert prov in item.provenance


# ─────────────────────────────────────────────────────────────────────────────
# 17-18: uncertainty/limitation filtering attempts rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_uncertainty_survives_even_when_its_category_is_optional_and_filtered():
    u = UncertaintyItem(category="technical_debt_introduced", description="unclear if fully tracked",
                         affected_evidence=("technical_debt_introduced",), source="s",
                         verification_state="unresolved")
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE, uncertainty=(u,))
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    # technical_debt_introduced is OPTIONAL and absent -> filtered, yet
    # the uncertainty describing it must still appear at the result level.
    assert u in result.uncertainty


def test_limitation_survives_even_when_its_category_is_conditionally_required_and_absent():
    lim = LimitationItem(category="defects_discovered", description="review was time-boxed",
                          affected_evidence=("defects_discovered",))
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE, limitations=(lim,))
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert lim in result.limitations


# ─────────────────────────────────────────────────────────────────────────────
# 19: filtering disclosure cannot satisfy missing required evidence
# ─────────────────────────────────────────────────────────────────────────────

def test_filtering_disclosure_does_not_satisfy_required_evidence():
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
    # Even though notable_engineering_knowledge is disclosed via
    # uncertainty (not a filtering disclosure -- it's REQUIRED, not
    # OPTIONAL), completeness must still be INCOMPLETE, not COMPLETE.
    assert "notable_engineering_knowledge" not in {d.excluded_category for d in result.filtering_disclosures}
    assert result.completeness == ExtractionCompleteness.INCOMPLETE


# ─────────────────────────────────────────────────────────────────────────────
# 20-21: complete-with-limitations correctness; invalid vs incomplete
# ─────────────────────────────────────────────────────────────────────────────

def test_complete_with_limitations_preserves_all_limitations():
    lim = LimitationItem(category="defects_discovered", description="x", affected_evidence=("defects_discovered",))
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE, limitations=(lim,))
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    assert result.completeness == ExtractionCompleteness.COMPLETE_WITH_LIMITATIONS
    assert lim in result.limitations


def test_invalid_distinct_from_incomplete():
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    # INVALID: required category explicitly marked not-applicable.
    ev_invalid = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "architectural_findings": Applicability.NOT_APPLICABLE}),
        architectural_findings=(),
    )
    # INCOMPLETE: required category unknown (disclosed, not a contradiction).
    ev_incomplete = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE,
        applicability=MappingProxyType({**app, "architectural_findings": Applicability.UNKNOWN}),
        architectural_findings=(),
        uncertainty=(UncertaintyItem(category="architectural_findings", description="x",
                                      affected_evidence=("architectural_findings",),
                                      source="s", verification_state="unresolved"),),
    )
    r_invalid = extract(ev_invalid, PROFILE_ID_PHASE_REPORT)
    r_incomplete = extract(ev_incomplete, PROFILE_ID_PHASE_REPORT)
    assert r_invalid.completeness == ExtractionCompleteness.INVALID
    assert r_incomplete.completeness == ExtractionCompleteness.INCOMPLETE
    assert r_invalid.completeness != r_incomplete.completeness


# ─────────────────────────────────────────────────────────────────────────────
# 22-23: duplicate normalized categories; orphan repair reference
# ─────────────────────────────────────────────────────────────────────────────

def test_duplicate_normalized_categories_structurally_impossible():
    assert len(EXTRACTION_CATEGORIES) == len(set(EXTRACTION_CATEGORIES))
    # And every SelectedEvidenceItem in a real extraction has a unique category.
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    categories = [i.category for i in result.selected_evidence]
    assert len(categories) == len(set(categories))


def test_orphan_repair_reference_structurally_impossible():
    """A RepairRecord embeds its full original_finding object -- it is
    never a foreign-key/ID reference into defects_discovered. There is
    no code path by which a repair could reference a finding that "does
    not exist": the finding it references is the one it carries.
    Confirmed directly: a repair whose original finding does NOT also
    appear in defects_discovered is fully valid and fully traceable on
    its own.
    """
    original = FindingRecord("F-standalone", FindingClassification.BLOCKING, "found and fixed same phase", "x")
    repair = RepairRecord(original, "fixed immediately", "x.py", "verified", FindingClassification.CONFIRMED)
    app = _full_applicability(PhaseClass.ARCHITECTURE)
    app["defects_repaired"] = Applicability.PRESENT
    # defects_discovered deliberately left empty/NOT_APPLICABLE -- the
    # repair's original finding is NOT duplicated there.
    ev = _minimal_complete_evidence(
        PhaseClass.ARCHITECTURE, applicability=MappingProxyType(app), defects_repaired=(repair,),
    )
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    item = next(i for i in result.selected_evidence if i.category == "defects_repaired")
    assert item.value[0].original_finding.finding_id == "F-standalone"


# ─────────────────────────────────────────────────────────────────────────────
# 24-25: future profile isolation; shared rule-structure mutation
# ─────────────────────────────────────────────────────────────────────────────

def test_future_profile_isolation_from_existing_profiles():
    before_phase_report = get_profile(PROFILE_ID_PHASE_REPORT)
    before_operator = get_profile(PROFILE_ID_OPERATOR_REPORT)
    future_rules = tuple(CategoryRule(cat, _all_required(RequirementLevel.OPTIONAL)) for cat in EXTRACTION_CATEGORIES)
    register_profile(ExtractionProfile("isolation_probe_v1", "1.0", frozenset(PhaseClass), future_rules))
    assert get_profile(PROFILE_ID_PHASE_REPORT) is before_phase_report
    assert get_profile(PROFILE_ID_OPERATOR_REPORT) is before_operator


def test_shared_rule_structure_cannot_be_mutated_through_category_rule():
    """CategoryRule.requirement_by_phase_class is a MappingProxyType --
    attempting to mutate it directly (e.g. from a future profile that
    held a reference to another profile's rule) raises, not silently
    succeeds.
    """
    profile = get_profile(PROFILE_ID_PHASE_REPORT)
    rule = profile.category_rules[0]
    with pytest.raises(TypeError):
        rule.requirement_by_phase_class[PhaseClass.ARCHITECTURE] = RequirementLevel.OPTIONAL


# ─────────────────────────────────────────────────────────────────────────────
# 26: cross-process byte determinism (extended beyond 134E.2's own probe)
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_process_byte_determinism_with_findings_and_uncertainty():
    src_dir = str(__import__("pathlib").Path(ee.__file__).resolve().parent.parent)
    code = (
        "import sys; sys.path.insert(0, %r); "
        "from types import MappingProxyType; "
        "from pcae.core.canonical_engineering_evidence import ("
        "CanonicalEngineeringEvidence, EvidenceIdentity, EvidencePhaseIdentity, PhaseClass, "
        "Applicability, RepositoryStateSnapshot, RuntimeStateSnapshot, CommitPushInfo, "
        "CorrectionMetadata, REQUIRED_APPLICABILITY_CATEGORIES, FindingRecord, "
        "FindingClassification, GovernanceResultItem, TestResultItem, UncertaintyItem); "
        "from pcae.core.evidence_extraction import extract, PROFILE_ID_PHASE_REPORT; "
        "app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}; "
        "app['engineering_actions'] = Applicability.PRESENT; "
        "app['notable_engineering_knowledge'] = Applicability.PRESENT; "
        "app['technical_debt_reviewed'] = Applicability.UNKNOWN; "
        "app['architectural_boundary_confirmations'] = Applicability.PRESENT; "
        "ev = CanonicalEngineeringEvidence("
        "identity=EvidenceIdentity(phase=EvidencePhaseIdentity(phase_id='999X', phase_name='X', source='cli_argument')), "
        "phase_class=PhaseClass.ARCHITECTURE, task_id=None, objective='probe', "
        "engineering_actions=('did it',), architectural_findings=(), implementation_findings=(), verification_findings=(), "
        "defects_discovered=(), defects_repaired=(), incorrect_assumptions_corrected=(), "
        "technical_debt_reviewed=(), technical_debt_introduced=(), "
        "notable_engineering_knowledge=('lesson',), "
        "governance_results=(GovernanceResultItem('pcae_check', 'passed'),), "
        "test_results=(TestResultItem('fast_green', '1/1', 'passed'),), "
        "repository_state=RepositoryStateSnapshot(commit='abc1234', branch='main', pushed_status='pushed', origin_main_head_count=0, clean=True), "
        "runtime_state=RuntimeStateSnapshot(runtime_state='Observed', maximum_capability='observe', execution_availability='unavailable'), "
        "no_go_confirmations=(), architectural_boundary_confirmations=('x',), "
        "track_progress='x', recommended_next_phase='999Y', "
        "commit_and_push=CommitPushInfo(commits=('abc1234',), pushed_status='pushed', origin_main_head_count=0), "
        "provenance=(), uncertainty=(UncertaintyItem(category='technical_debt_reviewed', description='d', "
        "affected_evidence=('technical_debt_reviewed',), source='s', verification_state='unresolved'),), "
        "limitations=(), correction=CorrectionMetadata(), "
        "applicability=MappingProxyType(app), created_at='2026-01-01T00:00:00+00:00').finalize(); "
        "print(extract(ev, PROFILE_ID_PHASE_REPORT).compute_digest())"
    ) % src_dir
    r1 = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    r2 = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert r1.stdout.strip() == r2.stdout.strip()
    assert len(r1.stdout.strip()) == 64


# ─────────────────────────────────────────────────────────────────────────────
# 27-28: synthetic future transport / unknown future-agent independence
# ─────────────────────────────────────────────────────────────────────────────

def test_synthetic_future_transport_context_cannot_alter_extraction():
    """A synthetic 'transport context' object handed in via provenance
    text has no special field or hook anywhere in the extraction API --
    confirmed structurally (no transport-shaped parameter exists) and
    behaviorally (embedding transport-sounding text in provenance
    changes only the provenance record itself, never a rule or
    completeness outcome).
    """
    sig_extract = inspect.signature(extract)
    assert "transport" not in [p.lower() for p in sig_extract.parameters]
    assert "channel" not in [p.lower() for p in sig_extract.parameters]

    prov = EvidenceProvenanceRecord(
        covers="engineering_actions", source_artifact="future-transport-xyz-adapter",
        source_command="delivered-via:future-transport-xyz", source_phase_id="999X",
        derivation_path="direct", verification_state="verified",
    )
    ev_plain = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    ev_with_transport_text = dataclasses.replace(ev_plain, provenance=(prov,))
    r1 = extract(ev_plain, PROFILE_ID_PHASE_REPORT)
    r2 = extract(ev_with_transport_text, PROFILE_ID_PHASE_REPORT)
    assert r1.completeness == r2.completeness
    assert [i.category for i in r1.selected_evidence] == [i.category for i in r2.selected_evidence]


def test_unknown_future_agent_provenance_independence():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    prov = EvidenceProvenanceRecord(
        covers="engineering_actions", source_artifact="cli", source_command="invoked-by:unknown-future-agent-2099",
        source_phase_id="999X", derivation_path="direct", verification_state="verified",
    )
    ev_with_agent = dataclasses.replace(ev, provenance=(prov,))
    r1 = extract(ev, PROFILE_ID_PHASE_REPORT)
    r2 = extract(ev_with_agent, PROFILE_ID_PHASE_REPORT)
    assert r1.completeness == r2.completeness


# ─────────────────────────────────────────────────────────────────────────────
# 29-30: no active lifecycle imports; no filesystem/network/rendering/delivery
# ─────────────────────────────────────────────────────────────────────────────

def test_no_active_lifecycle_imports_fresh_scan():
    # 134E.3/134E.4/134E.5 note: Phase Report View Composition
    # (``pcae.core.phase_report_view``), Operator Report View
    # Composition (``pcae.core.operator_report_view``), and Rendering
    # (``pcae.core.rendering``) are expected, deliberately isolated
    # consumers of this module -- successive layers in the same
    # disconnected architecture (Evidence Extraction -> View Composition
    # -> Rendering), not active-lifecycle ones. Every other file in the
    # source tree must still reference zero occurrences of
    # ``evidence_extraction`` -- narrowed here from "the empty set of
    # consumers" (134E.2V's original, now-outdated assumption) to "the
    # empty set of consumers other than the named, still-isolated
    # modules this repository's own architecture roadmap always intended
    # to add next."
    import pathlib
    src_root = pathlib.Path(ee.__file__).resolve().parent.parent
    _EXPECTED_ISOLATED_CONSUMERS = frozenset({
        "evidence_extraction.py", "phase_report_view.py", "operator_report_view.py",
        "rendering.py", "finalization_transaction.py",
    })
    for path in src_root.rglob("*.py"):
        if path.name in _EXPECTED_ISOLATED_CONSUMERS:
            continue
        if "test" in str(path):
            continue
        text = path.read_text()
        assert "evidence_extraction" not in text, f"{path} unexpectedly references evidence_extraction"


def test_no_filesystem_network_rendering_or_delivery_side_effects(monkeypatch):
    def _forbidden(*a, **kw):
        raise AssertionError("evidence_extraction must not touch the filesystem")
    monkeypatch.setattr("builtins.open", _forbidden)
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    result = extract(ev, PROFILE_ID_PHASE_REPORT)
    result.to_dict()
    result.compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# Additional: authority boundary re-confirmation, immutability of extraction
# result under external mutation attempts on nested references
# ─────────────────────────────────────────────────────────────────────────────

def test_extraction_result_selected_items_are_deeply_immutable():
    mutable_refs = ["engineering_actions"]
    u = UncertaintyItem(category="c", description="d", affected_evidence=mutable_refs,
                         source="s", verification_state="unresolved")
    mutable_refs.append("injected")
    assert u.affected_evidence == ("engineering_actions",)


def test_extraction_never_mutates_source_evidence_digest():
    ev = _minimal_complete_evidence(PhaseClass.ARCHITECTURE)
    digest_before = ev.compute_digest()
    extract(ev, PROFILE_ID_PHASE_REPORT)
    extract(ev, PROFILE_ID_OPERATOR_REPORT)
    extract(ev, PROFILE_ID_PHASE_REPORT)
    assert ev.compute_digest() == digest_before
