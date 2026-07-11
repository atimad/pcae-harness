"""Phase 134E.4: Operator Report View Composition.

Implements a deterministic, structured, mobile-oriented, transport-
independent Operator Report View Composition layer over the verified
``operator_report_v1`` Evidence Extraction result (134E.2, independently
verified and repaired by 134E.2V). The Operator Report View answers:
"how shall extracted canonical engineering evidence be organized so an
operator can understand the completed phase and safely decide what
happens next?"

**This module is not yet active lifecycle authority**, exactly like
``canonical_engineering_evidence.py``, ``evidence_extraction.py``, and
the Phase Report View Composition module (134E.3) before it. Nothing in the current governed
reporting/finalization/notification path imports or calls into this
module, and this module imports only ``evidence_extraction`` and three
shared enums from ``canonical_engineering_evidence``
(``Applicability``, ``FindingClassification``, ``PhaseClass``) --
otherwise stdlib-only. The current governed reporting and finalization
path remains fully operational and unaffected.

Architectural position (preserved, not merged):

    Canonical Engineering Evidence
            |
            v
    Evidence Extraction
            |
            +-- phase_report_v1 --> Phase Report View Composition (134E.3)
            |
            +-- operator_report_v1 --> Operator Report View Composition (this module)
                    |
                    v
                Rendering (not implemented)
                    |
                    v
                Delivery (not implemented)

The Phase Report View and Operator Report View are sibling derivatives.
Neither derives from the other; both consume their own verified
extraction profile independently. This module does not import the
Phase Report View Composition module -- the two compositions share no
code beyond the common ``evidence_extraction``/
``canonical_engineering_evidence`` layer they both sit on, deliberately
avoiding a premature shared abstraction.

The Operator Report is not required to mirror PFR-001's thirteen-
section layout; it is a distinct, twelve-section, audience-specific
view with its own decision-completeness and semantic-sufficiency gates
(Sections below) addressing the near-status-only-report observation
134E.3V carried forward as NON-BLOCKING for the Phase Report View.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pcae.core.canonical_engineering_evidence import (
    Applicability,
    FindingClassification,
    PhaseClass,
)
from pcae.core.evidence_extraction import (
    ExtractionCompleteness,
    ExtractionResult,
    PROFILE_ID_OPERATOR_REPORT,
    SelectedEvidenceItem,
)


VIEW_SCHEMA_VERSION = "1.0"

#: Versions this module can compose from. A single supported version
#: today; unsupported versions are rejected fail-closed, mirroring the
#: identical convention 134E.1/134E.2/134E.3 already established.
SUPPORTED_VIEW_VERSIONS: frozenset[str] = frozenset({VIEW_SCHEMA_VERSION})


# ═══════════════════════════════════════════════════════════════════════
# Operator section identity — twelve sections, fixed order
# ═══════════════════════════════════════════════════════════════════════


class OperatorSectionId(str, Enum):
    """The twelve operator-oriented sections this phase defines. Names
    and order are derived from repository convention (mirrors the
    Phase Report View Composition module's own equivalent shape) but
    this is a distinct, sibling section model -- not PFR-001's thirteen
    sections.
    """

    PHASE_OUTCOME = "phase_outcome"
    KEY_DECISIONS_AND_CHANGES = "key_decisions_and_changes"
    DISCOVERIES_DEFECTS_REPAIRS = "discoveries_defects_repairs"
    VERIFICATION_AND_REMAINING_FINDINGS = "verification_and_remaining_findings"
    TECHNICAL_DEBT_AND_DEFERRED_WORK = "technical_debt_and_deferred_work"
    ARCHITECTURAL_SIGNIFICANCE = "architectural_significance"
    BOUNDARIES_AND_NO_GO = "boundaries_and_no_go"
    TESTS_AND_GOVERNANCE = "tests_and_governance"
    REPOSITORY_AND_RUNTIME_STATE = "repository_and_runtime_state"
    NEXT_PHASE_AND_READINESS = "next_phase_and_readiness"
    NOTABLE_ENGINEERING_KNOWLEDGE = "notable_engineering_knowledge"
    DISCLOSURES_UNCERTAINTY_LIMITATIONS = "disclosures_uncertainty_limitations"


#: The frozen operator-report order, doubling as the canonical ordering
#: and the completeness roster -- every one of these twelve identities
#: must appear exactly once in every composed view.
OPERATOR_SECTION_ORDER: tuple[OperatorSectionId, ...] = (
    OperatorSectionId.PHASE_OUTCOME,
    OperatorSectionId.KEY_DECISIONS_AND_CHANGES,
    OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS,
    OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS,
    OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK,
    OperatorSectionId.ARCHITECTURAL_SIGNIFICANCE,
    OperatorSectionId.BOUNDARIES_AND_NO_GO,
    OperatorSectionId.TESTS_AND_GOVERNANCE,
    OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE,
    OperatorSectionId.NEXT_PHASE_AND_READINESS,
    OperatorSectionId.NOTABLE_ENGINEERING_KNOWLEDGE,
    OperatorSectionId.DISCLOSURES_UNCERTAINTY_LIMITATIONS,
)

#: Extraction categories assigned to each operator section, in
#: deterministic order. A category may be referenced by more than one
#: section (cross-section reuse), but only one section is ever its
#: primary owner (``_CATEGORY_PRIMARY_SECTION`` below) -- never
#: inferred, always named, mirroring the Phase Report View Composition
#: module's own convention.
_SECTION_CATEGORY_MAP: dict[OperatorSectionId, tuple[str, ...]] = {
    OperatorSectionId.PHASE_OUTCOME: (
        "identity", "objective", "engineering_actions",
        "architectural_findings", "implementation_findings",
        "verification_findings", "defects_discovered", "defects_repaired",
        "technical_debt_reviewed", "notable_engineering_knowledge",
        "runtime_state", "recommended_next_phase",
    ),
    OperatorSectionId.KEY_DECISIONS_AND_CHANGES: (
        "architectural_findings", "implementation_findings",
        "technical_debt_introduced",
    ),
    OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS: (
        "defects_discovered", "defects_repaired",
        "incorrect_assumptions_corrected",
    ),
    OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS: (
        "verification_findings", "defects_discovered", "defects_repaired",
    ),
    OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK: (
        "technical_debt_reviewed", "technical_debt_introduced",
    ),
    OperatorSectionId.ARCHITECTURAL_SIGNIFICANCE: (
        "track_progress", "architectural_findings",
    ),
    OperatorSectionId.BOUNDARIES_AND_NO_GO: (
        "no_go_confirmations", "architectural_boundary_confirmations",
    ),
    OperatorSectionId.TESTS_AND_GOVERNANCE: (
        "governance_results", "test_results",
    ),
    OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE: (
        "repository_state", "runtime_state", "commit_and_push",
    ),
    OperatorSectionId.NEXT_PHASE_AND_READINESS: (
        "recommended_next_phase",
    ),
    OperatorSectionId.NOTABLE_ENGINEERING_KNOWLEDGE: (
        "notable_engineering_knowledge",
    ),
    OperatorSectionId.DISCLOSURES_UNCERTAINTY_LIMITATIONS: (),
}

#: The primary (non-cross-referenced) section that owns the full
#: history for a given extraction category -- used by the accounting
#: mechanism to assert every selected category is owned by exactly one
#: section, even when it is *referenced* by others.
_CATEGORY_PRIMARY_SECTION: dict[str, OperatorSectionId] = {
    "identity": OperatorSectionId.PHASE_OUTCOME,
    "objective": OperatorSectionId.PHASE_OUTCOME,
    "engineering_actions": OperatorSectionId.PHASE_OUTCOME,
    "architectural_findings": OperatorSectionId.KEY_DECISIONS_AND_CHANGES,
    "implementation_findings": OperatorSectionId.KEY_DECISIONS_AND_CHANGES,
    "verification_findings": OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS,
    "defects_discovered": OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS,
    "defects_repaired": OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS,
    "incorrect_assumptions_corrected": OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS,
    "technical_debt_reviewed": OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK,
    "technical_debt_introduced": OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK,
    "notable_engineering_knowledge": OperatorSectionId.NOTABLE_ENGINEERING_KNOWLEDGE,
    "governance_results": OperatorSectionId.TESTS_AND_GOVERNANCE,
    "test_results": OperatorSectionId.TESTS_AND_GOVERNANCE,
    "repository_state": OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE,
    "runtime_state": OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE,
    "no_go_confirmations": OperatorSectionId.BOUNDARIES_AND_NO_GO,
    "architectural_boundary_confirmations": OperatorSectionId.BOUNDARIES_AND_NO_GO,
    "track_progress": OperatorSectionId.ARCHITECTURAL_SIGNIFICANCE,
    "recommended_next_phase": OperatorSectionId.NEXT_PHASE_AND_READINESS,
    "commit_and_push": OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE,
}

#: Sections whose absence of REQUIRED-and-selected content is expected
#: for some phase classes/profiles -- satisfied by an explicit
#: not-applicable disposition rather than populated evidence.
_CONDITIONAL_SECTIONS: frozenset[OperatorSectionId] = frozenset({
    OperatorSectionId.KEY_DECISIONS_AND_CHANGES,
    OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS,
    OperatorSectionId.BOUNDARIES_AND_NO_GO,
})

#: Categories whose genuine presence signals a substantive ("more than
#: status-only") phase outcome -- used by the semantic-sufficiency gate
#: (Section: Semantic Sufficiency). Deliberately excludes purely
#: procedural categories (objective/engineering_actions narrative,
#: governance/test results, repository/runtime state, next-phase text)
#: which alone would make *any* phase look "substantive."
_SUBSTANTIVE_OUTCOME_CATEGORIES: frozenset[str] = frozenset({
    "architectural_findings", "implementation_findings",
    "verification_findings", "defects_discovered", "defects_repaired",
    "incorrect_assumptions_corrected", "technical_debt_reviewed",
    "technical_debt_introduced", "notable_engineering_knowledge",
})


class OperatorSectionApplicability(str, Enum):
    MATERIALLY_POPULATED = "materially_populated"
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE_WITH_DISCLOSURE = "unavailable_with_disclosure"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


class OperatorSectionCompleteness(str, Enum):
    COMPLETE = "complete"
    COMPLETE_WITH_LIMITATIONS = "complete_with_limitations"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


class OperatorReportCompleteness(str, Enum):
    """View-level informational completeness. Composition may only ever
    equal or *downgrade* the source extraction's own completeness rank
    (Non-Strengthening) -- never upgrade it.
    """

    COMPLETE = "complete"
    COMPLETE_WITH_LIMITATIONS = "complete_with_limitations"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


class DecisionCompleteness(str, Enum):
    """Whether the operator can, from this view alone, determine each
    of the ten decision-completeness obligations (module docstring /
    phase brief's own numbered list). Strictly stronger than category
    presence: a category being present but semantically empty (e.g. no
    substantive outcome category selected at all) does not satisfy this.
    """

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


_COMPLETENESS_RANK: dict[str, int] = {
    "complete": 0,
    "complete_with_limitations": 1,
    "incomplete": 2,
    "invalid": 3,
}


def _worse(a: str, b: str) -> str:
    return a if _COMPLETENESS_RANK[a] >= _COMPLETENESS_RANK[b] else b


#: Deterministic priority rank for finding/repair classification, used
#: only to *order* evidence within DISCOVERIES_DEFECTS_REPAIRS /
#: VERIFICATION_AND_REMAINING_FINDINGS -- never to decide inclusion.
_CLASSIFICATION_PRIORITY_RANK: dict[str, int] = {
    "blocking": 0,
    "non_blocking": 1,
    "confirmed": 2,
}


# ═══════════════════════════════════════════════════════════════════════
# Section record model
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CompositionDiagnostic:
    code: str
    message: str
    section_id: str | None
    blocking: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code, "message": self.message,
            "section_id": self.section_id, "blocking": self.blocking,
        }


@dataclass(frozen=True)
class EvidenceGroupRef:
    """A structured, deterministic reference to one selected extraction
    category's content, as placed into an operator section. Never a
    copy of the underlying value.
    """

    category: str
    requirement_level: str
    applicability: str
    is_primary: bool
    finding_classifications: tuple[str, ...]
    priority_rank: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "requirement_level": self.requirement_level,
            "applicability": self.applicability,
            "is_primary": self.is_primary,
            "finding_classifications": list(self.finding_classifications),
            "priority_rank": self.priority_rank,
        }


@dataclass(frozen=True)
class OperatorSectionRecord:
    """One composed operator section. Every field is a structured
    reference into the source ``ExtractionResult`` -- never rendered
    prose, never a duplicated copy of canonical evidence.
    """

    section_id: OperatorSectionId
    order: int
    applicability: OperatorSectionApplicability
    completeness: OperatorSectionCompleteness
    evidence_groups: tuple[EvidenceGroupRef, ...]
    missing_required_categories: tuple[str, ...]
    uncertainty_categories: tuple[str, ...]
    limitation_categories: tuple[str, ...]
    filtering_disclosure_categories: tuple[str, ...]
    provenance_categories: tuple[str, ...]
    diagnostics: tuple[CompositionDiagnostic, ...]
    not_applicable_reason: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_groups", tuple(self.evidence_groups))
        object.__setattr__(
            self, "missing_required_categories", tuple(self.missing_required_categories),
        )
        object.__setattr__(self, "uncertainty_categories", tuple(self.uncertainty_categories))
        object.__setattr__(self, "limitation_categories", tuple(self.limitation_categories))
        object.__setattr__(
            self, "filtering_disclosure_categories",
            tuple(self.filtering_disclosure_categories),
        )
        object.__setattr__(self, "provenance_categories", tuple(self.provenance_categories))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
        if (
            self.applicability == OperatorSectionApplicability.NOT_APPLICABLE
            and not self.not_applicable_reason
        ):
            raise ValueError(
                f"OperatorSectionRecord {self.section_id.value!r}: NOT_APPLICABLE "
                "requires an explicit not_applicable_reason"
            )
        if (
            self.applicability != OperatorSectionApplicability.NOT_APPLICABLE
            and self.not_applicable_reason is not None
        ):
            raise ValueError(
                f"OperatorSectionRecord {self.section_id.value!r}: "
                "not_applicable_reason set without NOT_APPLICABLE applicability"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id.value,
            "order": self.order,
            "applicability": self.applicability.value,
            "completeness": self.completeness.value,
            "evidence_groups": [g.to_dict() for g in self.evidence_groups],
            "missing_required_categories": list(self.missing_required_categories),
            "uncertainty_categories": list(self.uncertainty_categories),
            "limitation_categories": list(self.limitation_categories),
            "filtering_disclosure_categories": list(self.filtering_disclosure_categories),
            "provenance_categories": list(self.provenance_categories),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "not_applicable_reason": self.not_applicable_reason,
        }


# ═══════════════════════════════════════════════════════════════════════
# Composed view model
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class OperatorReportView:
    """The deterministic, structured Operator Report View: all twelve
    operator sections composed from one ``operator_report_v1``
    extraction result. Mobile-oriented but channel-neutral -- suitable
    as input to a future renderer, never itself rendered prose.
    """

    view_id: str
    view_version: str
    source_evidence_id: str
    source_record_digest: str
    source_extraction_digest: str
    profile_id: str
    profile_version: str
    phase_id: str
    phase_title: str
    phase_class: PhaseClass
    terminal_status: str
    completeness: OperatorReportCompleteness
    decision_completeness: DecisionCompleteness
    sections: tuple[OperatorSectionRecord, ...]
    cross_section_uncertainty: tuple[str, ...]
    cross_section_limitation: tuple[str, ...]
    filtering_disclosures: tuple[str, ...]
    diagnostics: tuple[CompositionDiagnostic, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "sections", tuple(self.sections))
        object.__setattr__(
            self, "cross_section_uncertainty", tuple(self.cross_section_uncertainty),
        )
        object.__setattr__(
            self, "cross_section_limitation", tuple(self.cross_section_limitation),
        )
        object.__setattr__(self, "filtering_disclosures", tuple(self.filtering_disclosures))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d: dict[str, Any] = {
            "view_id": self.view_id,
            "view_version": self.view_version,
            "source_evidence_id": self.source_evidence_id,
            "source_record_digest": self.source_record_digest,
            "source_extraction_digest": self.source_extraction_digest,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "phase_id": self.phase_id,
            "phase_title": self.phase_title,
            "phase_class": self.phase_class.value,
            "terminal_status": self.terminal_status,
            "completeness": self.completeness.value,
            "decision_completeness": self.decision_completeness.value,
            "sections": [s.to_dict() for s in self.sections],
            "cross_section_uncertainty": list(self.cross_section_uncertainty),
            "cross_section_limitation": list(self.cross_section_limitation),
            "filtering_disclosures": list(self.filtering_disclosures),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }
        if include_digest:
            d["view_digest"] = self.compute_digest()
        return d

    def compute_digest(self) -> str:
        """Deterministic SHA-256 digest over the canonical structured
        serialization, excluding the digest field itself. Follows the
        identical convention 134E.1/134E.2/134E.3 established. Contains
        no renderer or delivery state by construction, so neither can
        leak into the digest.
        """
        d = self.to_dict(include_digest=False)
        canonical = json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# Composition entry point
# ═══════════════════════════════════════════════════════════════════════


def _selected_by_category(result: ExtractionResult) -> dict[str, SelectedEvidenceItem]:
    return {item.category: item for item in result.selected_evidence}


def _finding_classifications(value: Any) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        return ()
    classifications: list[str] = []
    for item in value:
        classification = getattr(item, "classification", None)
        if isinstance(classification, FindingClassification):
            classifications.append(classification.value)
            continue
        original = getattr(item, "original_finding", None)
        if original is not None:
            original_classification = getattr(original, "classification", None)
            if isinstance(original_classification, FindingClassification):
                classifications.append(original_classification.value)
        resulting = getattr(item, "resulting_status", None)
        if isinstance(resulting, FindingClassification):
            classifications.append(resulting.value)
    return tuple(sorted(set(classifications)))


def _priority_rank_for(classifications: tuple[str, ...]) -> int:
    """Deterministic priority rank for one evidence group, derived
    solely from structured classification values (never free text).
    Lower rank sorts first (more operator-urgent). Ties are broken by
    category name at the call site for full determinism.
    """
    if not classifications:
        return len(_CLASSIFICATION_PRIORITY_RANK)
    return min(
        _CLASSIFICATION_PRIORITY_RANK.get(c, len(_CLASSIFICATION_PRIORITY_RANK))
        for c in classifications
    )


def _compose_section(
    section_id: OperatorSectionId,
    order: int,
    result: ExtractionResult,
    selected: dict[str, SelectedEvidenceItem],
    missing_by_category: dict[str, str],
    filtering_categories: frozenset[str],
    diagnostics_out: list[CompositionDiagnostic],
) -> OperatorSectionRecord:
    categories = _SECTION_CATEGORY_MAP[section_id]
    evidence_groups: list[EvidenceGroupRef] = []
    missing_required: list[str] = []
    uncertainty_categories: list[str] = []
    limitation_categories: list[str] = []
    filtering_here: list[str] = []
    provenance_here: list[str] = []
    section_diagnostics: list[CompositionDiagnostic] = []

    any_present = False
    any_conditionally_missing = False
    any_required_missing = False
    any_invalid = False

    for category in categories:
        is_primary = _CATEGORY_PRIMARY_SECTION.get(category) == section_id
        item = selected.get(category)
        if item is not None:
            any_present = True
            classifications = _finding_classifications(item.value)
            evidence_groups.append(EvidenceGroupRef(
                category=category,
                requirement_level=item.requirement_level.value,
                applicability=item.applicability.value,
                is_primary=is_primary,
                finding_classifications=classifications,
                priority_rank=_priority_rank_for(classifications),
            ))
            if item.uncertainty_refs:
                uncertainty_categories.append(category)
            if item.limitation_refs:
                limitation_categories.append(category)
            if item.provenance:
                provenance_here.append(category)
            continue

        if category in missing_by_category:
            reason = missing_by_category[category]
            missing_required.append(category)
            if reason == "required":
                any_required_missing = True
            elif reason == "invalid":
                any_invalid = True
            else:
                any_conditionally_missing = True

        if category in filtering_categories:
            filtering_here.append(category)

    # Deterministic ordering by priority rank, tie-broken by category
    # name (never insertion order) -- affects presentation order only,
    # never inclusion (Evidence Prioritization).
    evidence_groups.sort(key=lambda g: (g.priority_rank, g.category))

    if any_invalid:
        applicability = OperatorSectionApplicability.INVALID
        completeness = OperatorSectionCompleteness.INVALID
        not_applicable_reason = None
    elif any_required_missing:
        applicability = OperatorSectionApplicability.INCOMPLETE
        completeness = OperatorSectionCompleteness.INCOMPLETE
        not_applicable_reason = None
    elif not any_present and any_conditionally_missing:
        # 134E.3V lesson (baked in from the start, not repaired after
        # the fact): a conditionally-required-and-missing category is a
        # real, disclosed limitation and must never be composed
        # identically to a genuinely not-applicable category.
        applicability = OperatorSectionApplicability.UNAVAILABLE_WITH_DISCLOSURE
        completeness = OperatorSectionCompleteness.COMPLETE_WITH_LIMITATIONS
        not_applicable_reason = None
    elif not any_present and section_id in _CONDITIONAL_SECTIONS:
        applicability = OperatorSectionApplicability.NOT_APPLICABLE
        completeness = OperatorSectionCompleteness.COMPLETE
        not_applicable_reason = (
            f"no category in {list(categories)} was selected for phase class "
            f"{result.phase_class.value!r} under profile {result.profile_id!r}; "
            "extraction disposed of every source category as not_applicable "
            "or optional-and-absent for this phase class"
        )
    elif not any_present:
        applicability = OperatorSectionApplicability.UNAVAILABLE_WITH_DISCLOSURE
        completeness = OperatorSectionCompleteness.INCOMPLETE
        not_applicable_reason = None
        section_diagnostics.append(CompositionDiagnostic(
            code="structurally_empty_required_section",
            message=(
                f"section {section_id.value!r} has no selected evidence and "
                "is not a conditionally-not-applicable section"
            ),
            section_id=section_id.value, blocking=True,
        ))
    elif any_conditionally_missing:
        applicability = OperatorSectionApplicability.MATERIALLY_POPULATED
        completeness = OperatorSectionCompleteness.COMPLETE_WITH_LIMITATIONS
        not_applicable_reason = None
    else:
        applicability = OperatorSectionApplicability.MATERIALLY_POPULATED
        completeness = OperatorSectionCompleteness.COMPLETE
        not_applicable_reason = None

    diagnostics_out.extend(section_diagnostics)

    return OperatorSectionRecord(
        section_id=section_id, order=order, applicability=applicability,
        completeness=completeness, evidence_groups=tuple(evidence_groups),
        missing_required_categories=tuple(missing_required),
        uncertainty_categories=tuple(sorted(set(uncertainty_categories))),
        limitation_categories=tuple(sorted(set(limitation_categories))),
        filtering_disclosure_categories=tuple(sorted(set(filtering_here))),
        provenance_categories=tuple(sorted(set(provenance_here))),
        diagnostics=tuple(section_diagnostics),
        not_applicable_reason=not_applicable_reason,
    )


def _compute_decision_completeness(
    result: ExtractionResult,
    sections: tuple[OperatorSectionRecord, ...],
    selected: dict[str, SelectedEvidenceItem],
) -> tuple[DecisionCompleteness, list[CompositionDiagnostic]]:
    """Independently, structurally evaluate the ten decision-
    completeness obligations. Strictly stronger than category presence:
    a category being present but semantically empty (no substantive
    outcome category selected anywhere) still fails obligation 1.
    """
    diagnostics: list[CompositionDiagnostic] = []
    by_id = {s.section_id: s for s in sections}

    if any(s.applicability == OperatorSectionApplicability.INVALID for s in sections):
        return DecisionCompleteness.INVALID, diagnostics

    incomplete = False

    # Obligation 1: objective achieved -- requires PHASE_OUTCOME
    # determinate AND at least one substantive (non-procedural) outcome
    # category genuinely selected anywhere in the record (the semantic-
    # sufficiency gate: never satisfied by objective/engineering_actions
    # narrative alone, addressing the 134E.3V near-status-only
    # observation via structured presence, not free-text scoring).
    outcome_section = by_id[OperatorSectionId.PHASE_OUTCOME]
    has_substantive_outcome = any(
        cat in selected for cat in _SUBSTANTIVE_OUTCOME_CATEGORIES
    )
    if outcome_section.applicability == OperatorSectionApplicability.INCOMPLETE:
        incomplete = True
    if not has_substantive_outcome:
        incomplete = True
        diagnostics.append(CompositionDiagnostic(
            code="status_only_outcome",
            message=(
                "no substantive outcome category "
                f"({sorted(_SUBSTANTIVE_OUTCOME_CATEGORIES)}) was selected; "
                "outcome would be status-only (objective/engineering_actions "
                "narrative alone is insufficient)"
            ),
            section_id=OperatorSectionId.PHASE_OUTCOME.value, blocking=True,
        ))

    # Obligations 2-3: defects/repairs determinate (never silently
    # un-disclosed).
    discoveries = by_id[OperatorSectionId.DISCOVERIES_DEFECTS_REPAIRS]
    if discoveries.applicability == OperatorSectionApplicability.INCOMPLETE:
        incomplete = True

    # Obligation 4: unresolved findings visible -- verification section
    # determinate.
    verification = by_id[OperatorSectionId.VERIFICATION_AND_REMAINING_FINDINGS]
    if verification.applicability == OperatorSectionApplicability.INCOMPLETE:
        incomplete = True

    # Obligation 5: technical debt status determinate.
    debt = by_id[OperatorSectionId.TECHNICAL_DEBT_AND_DEFERRED_WORK]
    if debt.applicability == OperatorSectionApplicability.INCOMPLETE:
        incomplete = True

    # Obligation 6: boundaries preserved -- determinate.
    boundaries = by_id[OperatorSectionId.BOUNDARIES_AND_NO_GO]
    if boundaries.applicability == OperatorSectionApplicability.INCOMPLETE:
        incomplete = True

    # Obligation 7: tests/governance support the claim -- determinate.
    tests_gov = by_id[OperatorSectionId.TESTS_AND_GOVERNANCE]
    if tests_gov.applicability == OperatorSectionApplicability.INCOMPLETE:
        incomplete = True

    # Obligations 8-9: repository/runtime state determinate.
    repo_runtime = by_id[OperatorSectionId.REPOSITORY_AND_RUNTIME_STATE]
    if repo_runtime.applicability == OperatorSectionApplicability.INCOMPLETE:
        incomplete = True

    # Obligation 10: next phase identified/safe -- determinate.
    next_phase = by_id[OperatorSectionId.NEXT_PHASE_AND_READINESS]
    if next_phase.applicability == OperatorSectionApplicability.INCOMPLETE:
        incomplete = True

    if incomplete:
        return DecisionCompleteness.INCOMPLETE, diagnostics
    return DecisionCompleteness.COMPLETE, diagnostics


def compose_operator_report_view(
    result: ExtractionResult,
    *,
    view_version: str = VIEW_SCHEMA_VERSION,
) -> OperatorReportView:
    """Compose a deterministic ``OperatorReportView`` from an
    already-produced ``operator_report_v1`` extraction result.

    Fail-closed (raises ``ValueError``) for: an unsupported view
    version, an extraction result produced under the wrong profile
    (``phase_report_v1`` or any other non-``operator_report_v1`` profile
    is rejected), an ``ExtractionCompleteness.INVALID`` extraction
    result, a missing source identity/digest, or an orphan uncertainty/
    limitation reference this module can independently detect.

    Returns normally (never raises) for every other extraction-
    completeness outcome. ``decision_completeness`` is a distinct,
    additional dimension (never used to raise) that is stricter than
    category presence -- it can be INCOMPLETE even when
    ``completeness`` is COMPLETE, precisely to catch the near-status-
    only-report class 134E.3V carried forward as an observation on the
    Phase Report View.
    """

    if view_version not in SUPPORTED_VIEW_VERSIONS:
        raise ValueError(
            f"Unsupported Operator Report View version {view_version!r}; "
            f"supported: {sorted(SUPPORTED_VIEW_VERSIONS)}"
        )

    if result.profile_id != PROFILE_ID_OPERATOR_REPORT:
        raise ValueError(
            "Operator Report View Composition requires an extraction "
            f"result produced under profile {PROFILE_ID_OPERATOR_REPORT!r}; "
            f"got {result.profile_id!r}"
        )

    if result.completeness == ExtractionCompleteness.INVALID:
        raise ValueError(
            "Cannot compose an Operator Report View from an INVALID "
            "extraction result -- extraction reported a genuine "
            f"contradiction (diagnostics: {[d.to_dict() for d in result.diagnostics]})"
        )

    if not result.source_evidence_id:
        raise ValueError("ExtractionResult.source_evidence_id must be non-empty")
    if not result.source_record_digest:
        raise ValueError("ExtractionResult.source_record_digest must be non-empty")

    selected = _selected_by_category(result)

    known_categories = set(_CATEGORY_PRIMARY_SECTION.keys())
    for item in result.selected_evidence:
        for ref in item.uncertainty_refs:
            if ref not in known_categories and ref != item.category:
                raise ValueError(
                    f"Orphan uncertainty reference to unknown category {ref!r} "
                    f"on selected item {item.category!r}"
                )
        for ref in item.limitation_refs:
            if ref not in known_categories and ref != item.category:
                raise ValueError(
                    f"Orphan limitation reference to unknown category {ref!r} "
                    f"on selected item {item.category!r}"
                )

    missing_by_category: dict[str, str] = {}
    for diag in result.diagnostics:
        if diag.category is None:
            continue
        if diag.code == "required_category_marked_not_applicable":
            missing_by_category[diag.category] = "invalid"
        elif diag.code == "required_category_missing":
            missing_by_category[diag.category] = "required"
        elif diag.code == "conditionally_required_category_missing":
            missing_by_category.setdefault(diag.category, "conditional")
    for category in result.missing_required:
        missing_by_category.setdefault(category, "conditional")

    filtering_categories = frozenset(
        fd.excluded_category for fd in result.filtering_disclosures
    )

    all_uncertainty_categories = tuple(sorted({u.category for u in result.uncertainty}))
    all_limitation_categories = tuple(sorted({l.category for l in result.limitations}))
    all_filtering_categories = tuple(sorted(filtering_categories))

    diagnostics: list[CompositionDiagnostic] = []
    sections: list[OperatorSectionRecord] = []
    assigned_categories: set[str] = set()

    for order, section_id in enumerate(OPERATOR_SECTION_ORDER, start=1):
        if section_id == OperatorSectionId.DISCLOSURES_UNCERTAINTY_LIMITATIONS:
            # Cross-cutting section: owns no extraction category by
            # design (_SECTION_CATEGORY_MAP maps it to an empty tuple),
            # so it must never be judged by the generic per-category
            # empty-section logic (which would wrongly treat "nothing to
            # disclose" as "structurally empty required section" --
            # exactly the class of bug 134E.3V found and repaired
            # elsewhere, avoided here by construction). Its own
            # materiality comes from whether any uncertainty/limitation/
            # filtering disclosure exists anywhere in the record.
            has_disclosures = bool(
                all_uncertainty_categories or all_limitation_categories
                or all_filtering_categories
            )
            if has_disclosures:
                section = OperatorSectionRecord(
                    section_id=section_id, order=order,
                    applicability=OperatorSectionApplicability.MATERIALLY_POPULATED,
                    completeness=OperatorSectionCompleteness.COMPLETE_WITH_LIMITATIONS,
                    evidence_groups=(), missing_required_categories=(),
                    uncertainty_categories=all_uncertainty_categories,
                    limitation_categories=all_limitation_categories,
                    filtering_disclosure_categories=all_filtering_categories,
                    provenance_categories=(), diagnostics=(),
                    not_applicable_reason=None,
                )
            else:
                section = OperatorSectionRecord(
                    section_id=section_id, order=order,
                    applicability=OperatorSectionApplicability.NOT_APPLICABLE,
                    completeness=OperatorSectionCompleteness.COMPLETE,
                    evidence_groups=(), missing_required_categories=(),
                    uncertainty_categories=(), limitation_categories=(),
                    filtering_disclosure_categories=(), provenance_categories=(),
                    diagnostics=(),
                    not_applicable_reason=(
                        "no uncertainty, limitation, or filtering disclosure "
                        "exists anywhere in the source extraction result"
                    ),
                )
            sections.append(section)
            continue
        section = _compose_section(
            section_id, order, result, selected, missing_by_category,
            filtering_categories, diagnostics,
        )
        sections.append(section)
        for group in section.evidence_groups:
            if group.is_primary:
                assigned_categories.add(group.category)

    unassigned = set(selected.keys()) - assigned_categories
    if unassigned:
        diagnostics.append(CompositionDiagnostic(
            code="unassigned_required_evidence",
            message=f"selected categories with no owning primary section: {sorted(unassigned)}",
            section_id=None, blocking=True,
        ))

    section_blocking = any(
        d.blocking for section in sections for d in section.diagnostics
    ) or any(d.blocking for d in diagnostics)

    view_rank_floor = result.completeness.value
    if section_blocking:
        view_rank_floor = _worse(view_rank_floor, "incomplete")
    any_section_incomplete = any(
        s.completeness in (
            OperatorSectionCompleteness.INCOMPLETE, OperatorSectionCompleteness.INVALID,
        )
        for s in sections
    )
    if any_section_incomplete:
        worst_section = "invalid" if any(
            s.completeness == OperatorSectionCompleteness.INVALID for s in sections
        ) else "incomplete"
        view_rank_floor = _worse(view_rank_floor, worst_section)

    view_completeness = OperatorReportCompleteness(view_rank_floor)

    decision_completeness, decision_diagnostics = _compute_decision_completeness(
        result, tuple(sections), selected,
    )
    diagnostics.extend(decision_diagnostics)

    cross_section_uncertainty = all_uncertainty_categories
    cross_section_limitation = all_limitation_categories
    filtering_summary = all_filtering_categories

    identity_item = selected.get("identity")
    phase_title = ""
    terminal_status = "composed"
    if identity_item is not None and hasattr(identity_item.value, "phase"):
        phase_title = getattr(identity_item.value.phase, "phase_name", "")

    view_id = f"operator-report-view:{result.source_evidence_id}:{result.profile_id}"

    view = OperatorReportView(
        view_id=view_id, view_version=view_version,
        source_evidence_id=result.source_evidence_id,
        source_record_digest=result.source_record_digest,
        source_extraction_digest=result.compute_digest(),
        profile_id=result.profile_id, profile_version=result.profile_version,
        phase_id=result.source_evidence_id.split("#", 1)[0],
        phase_title=phase_title,
        phase_class=result.phase_class,
        terminal_status=terminal_status,
        completeness=view_completeness,
        decision_completeness=decision_completeness,
        sections=tuple(sections),
        cross_section_uncertainty=cross_section_uncertainty,
        cross_section_limitation=cross_section_limitation,
        filtering_disclosures=filtering_summary,
        diagnostics=tuple(diagnostics),
    )

    if len(view.sections) != len(OPERATOR_SECTION_ORDER):
        raise ValueError(  # pragma: no cover — structurally unreachable
            "Composed view does not contain all twelve operator sections"
        )

    if all(
        s.applicability in (
            OperatorSectionApplicability.NOT_APPLICABLE,
            OperatorSectionApplicability.UNAVAILABLE_WITH_DISCLOSURE,
        )
        for s in view.sections
    ):
        raise ValueError(
            "Composition produced a structurally empty successful report -- "
            "every section is not_applicable/unavailable; refusing to "
            "return a silent empty success"
        )

    return view
