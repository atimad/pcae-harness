"""Phase 134E.3: Phase Report View Composition.

Implements the deterministic, structured Phase Report View Composition
layer over the verified ``phase_report_v1`` Evidence Extraction result
(134E.2, independently verified and repaired by 134E.2V). Composition
answers exactly one question: "how shall the extracted canonical
evidence be organized into the thirteen PFR-001 Phase Report sections?"
It never creates engineering evidence, never re-runs extraction, never
queries Canonical Engineering Evidence directly, never infers missing
facts, never strengthens conclusions, and never generates rendered
prose (Markdown/plain-text/HTML) or delivers anything.

**This module is not yet active lifecycle authority**, exactly like
``canonical_engineering_evidence.py`` and ``evidence_extraction.py``
before it. Nothing in the current governed reporting/finalization/
notification path imports or calls into this module, and this module
imports only ``evidence_extraction``, ``canonical_engineering_evidence``,
and the standard library. The current governed reporting and
finalization path (``pcae.core.phase_reports``) remains the sole active
authority and is completely unaffected by this phase.

Architectural position (preserved, not merged):

    Canonical Engineering Evidence
            |
            v
    Evidence Extraction
            |
            v
    Phase Report View Composition        <- this module
            |
            v
    Rendering                             (not implemented)
            |
            v
    Delivery                              (not implemented)

Composition consumes only an already-produced ``ExtractionResult`` for
the ``phase_report_v1`` profile. It decides section assignment,
grouping, ordering, structured labels, phase-class-specific section
treatment, explicit not-applicable treatment, structured completeness
presentation, and disclosed-filtering placement. It never decides
Markdown syntax, plain-text layout, HTML layout, line wrapping, or any
other channel-specific formatting concern -- those remain entirely a
future Rendering phase's responsibility.

Only Phase Report View Composition is implemented here.
``operator_report_v1`` composition is explicitly out of scope for this
phase (a Strict Non-Goal) and is left for a later, dedicated phase.
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
    PROFILE_ID_PHASE_REPORT,
    RequirementLevel,
    SelectedEvidenceItem,
)


VIEW_SCHEMA_VERSION = "1.0"

#: Versions this module can compose from. A single supported version
#: today; unsupported versions are rejected fail-closed, mirroring the
#: identical convention 134E.1/134E.2 already established.
SUPPORTED_VIEW_VERSIONS: frozenset[str] = frozenset({VIEW_SCHEMA_VERSION})


# ═══════════════════════════════════════════════════════════════════════
# PFR-001 section identity — thirteen sections, frozen order (133B §3)
# ═══════════════════════════════════════════════════════════════════════


class PFRSectionId(str, Enum):
    """The thirteen mandatory PFR-001 sections, in PFR-001's own
    recommended default order (133B Section 3). This ordering is the
    single source of truth for deterministic section ordering in a
    composed view -- never dictionary/registry insertion order.
    """

    PHASE_IDENTITY = "phase_identity"
    EXECUTIVE_SUMMARY = "executive_summary"
    ARCHITECTURAL_FINDINGS = "architectural_findings"
    IMPLEMENTATION_FINDINGS = "implementation_findings"
    VERIFICATION_FINDINGS = "verification_findings"
    TECHNICAL_DEBT_REVIEW = "technical_debt_review"
    NOTABLE_ENGINEERING_KNOWLEDGE = "notable_engineering_knowledge"
    GOVERNANCE_RESULTS = "governance_results"
    TEST_RESULTS = "test_results"
    NO_GO_CONFIRMATION = "no_go_confirmation"
    ARCHITECTURAL_BOUNDARY_CONFIRMATION = "architectural_boundary_confirmation"
    TRACK_PROGRESS = "track_progress"
    NEXT_PHASE = "next_phase"


#: The frozen PFR-001 order (133B Section 3's numbered list) as a tuple,
#: doubling as both the canonical ordering and the completeness roster --
#: every one of these thirteen identities must appear exactly once in
#: every composed view.
PFR_SECTION_ORDER: tuple[PFRSectionId, ...] = (
    PFRSectionId.PHASE_IDENTITY,
    PFRSectionId.EXECUTIVE_SUMMARY,
    PFRSectionId.ARCHITECTURAL_FINDINGS,
    PFRSectionId.IMPLEMENTATION_FINDINGS,
    PFRSectionId.VERIFICATION_FINDINGS,
    PFRSectionId.TECHNICAL_DEBT_REVIEW,
    PFRSectionId.NOTABLE_ENGINEERING_KNOWLEDGE,
    PFRSectionId.GOVERNANCE_RESULTS,
    PFRSectionId.TEST_RESULTS,
    PFRSectionId.NO_GO_CONFIRMATION,
    PFRSectionId.ARCHITECTURAL_BOUNDARY_CONFIRMATION,
    PFRSectionId.TRACK_PROGRESS,
    PFRSectionId.NEXT_PHASE,
)

#: Extraction categories assigned to each section, in the deterministic
#: order they are placed within the section's ``evidence_refs``. A
#: category may be reused across sections only where explicitly listed
#: here (e.g. ``engineering_actions`` supports both the Executive
#: Summary and, indirectly, no other section) -- cross-section reuse is
#: never inferred, always named.
_SECTION_CATEGORY_MAP: dict[PFRSectionId, tuple[str, ...]] = {
    PFRSectionId.PHASE_IDENTITY: (
        "identity", "repository_state", "commit_and_push",
    ),
    PFRSectionId.EXECUTIVE_SUMMARY: (
        "objective", "engineering_actions", "architectural_findings",
        "implementation_findings", "verification_findings",
        "defects_discovered", "defects_repaired", "runtime_state",
        "recommended_next_phase",
    ),
    PFRSectionId.ARCHITECTURAL_FINDINGS: (
        "architectural_findings",
    ),
    PFRSectionId.IMPLEMENTATION_FINDINGS: (
        "implementation_findings",
    ),
    PFRSectionId.VERIFICATION_FINDINGS: (
        "verification_findings", "defects_discovered", "defects_repaired",
        "incorrect_assumptions_corrected",
    ),
    PFRSectionId.TECHNICAL_DEBT_REVIEW: (
        "technical_debt_reviewed", "technical_debt_introduced",
    ),
    PFRSectionId.NOTABLE_ENGINEERING_KNOWLEDGE: (
        "notable_engineering_knowledge",
    ),
    PFRSectionId.GOVERNANCE_RESULTS: (
        "governance_results",
    ),
    PFRSectionId.TEST_RESULTS: (
        "test_results",
    ),
    PFRSectionId.NO_GO_CONFIRMATION: (
        "no_go_confirmations",
    ),
    PFRSectionId.ARCHITECTURAL_BOUNDARY_CONFIRMATION: (
        "architectural_boundary_confirmations", "runtime_state",
    ),
    PFRSectionId.TRACK_PROGRESS: (
        "track_progress",
    ),
    PFRSectionId.NEXT_PHASE: (
        "recommended_next_phase",
    ),
}

#: The primary (non-cross-referenced) section that owns the full history
#: for a given category -- used by the accounting mechanism below to
#: assert every selected category is owned by exactly one section, even
#: when it is *referenced* by others. This mirrors the phase brief's own
#: worked example: a repaired BLOCKING defect's full history belongs in
#: Verification Findings; Executive Summary only cross-references it.
_CATEGORY_PRIMARY_SECTION: dict[str, PFRSectionId] = {
    "identity": PFRSectionId.PHASE_IDENTITY,
    "repository_state": PFRSectionId.PHASE_IDENTITY,
    "commit_and_push": PFRSectionId.PHASE_IDENTITY,
    "objective": PFRSectionId.EXECUTIVE_SUMMARY,
    "engineering_actions": PFRSectionId.EXECUTIVE_SUMMARY,
    "architectural_findings": PFRSectionId.ARCHITECTURAL_FINDINGS,
    "implementation_findings": PFRSectionId.IMPLEMENTATION_FINDINGS,
    "verification_findings": PFRSectionId.VERIFICATION_FINDINGS,
    "defects_discovered": PFRSectionId.VERIFICATION_FINDINGS,
    "defects_repaired": PFRSectionId.VERIFICATION_FINDINGS,
    "incorrect_assumptions_corrected": PFRSectionId.VERIFICATION_FINDINGS,
    "technical_debt_reviewed": PFRSectionId.TECHNICAL_DEBT_REVIEW,
    "technical_debt_introduced": PFRSectionId.TECHNICAL_DEBT_REVIEW,
    "notable_engineering_knowledge": PFRSectionId.NOTABLE_ENGINEERING_KNOWLEDGE,
    "governance_results": PFRSectionId.GOVERNANCE_RESULTS,
    "test_results": PFRSectionId.TEST_RESULTS,
    "no_go_confirmations": PFRSectionId.NO_GO_CONFIRMATION,
    "architectural_boundary_confirmations": (
        PFRSectionId.ARCHITECTURAL_BOUNDARY_CONFIRMATION
    ),
    "track_progress": PFRSectionId.TRACK_PROGRESS,
    "recommended_next_phase": PFRSectionId.NEXT_PHASE,
    "runtime_state": PFRSectionId.ARCHITECTURAL_BOUNDARY_CONFIRMATION,
}

#: Sections whose *absence of REQUIRED-and-selected content* is normal
#: for some phase classes/profiles, satisfied instead by an explicit
#: not-applicable/none-occurred disposition rather than populated
#: evidence (133B Section 6's own disambiguation for Implementation
#: Findings / Verification Findings). Composition never invents content
#: here; it records the disposition the extraction result already
#: carries.
_CONDITIONAL_SECTIONS: frozenset[PFRSectionId] = frozenset({
    PFRSectionId.ARCHITECTURAL_FINDINGS,
    PFRSectionId.IMPLEMENTATION_FINDINGS,
    PFRSectionId.VERIFICATION_FINDINGS,
    PFRSectionId.NO_GO_CONFIRMATION,
})


class SectionApplicability(str, Enum):
    """Structural disposition of one composed section -- distinct from,
    and composed from, the underlying extraction categories'
    ``RequirementLevel``/``Applicability`` values. A section is never
    silently absent; this enum is always populated.
    """

    MATERIALLY_POPULATED = "materially_populated"
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE_WITH_DISCLOSURE = "unavailable_with_disclosure"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


class SectionCompleteness(str, Enum):
    """Informational completeness of one composed section. Distinct from
    view-level completeness (below), which aggregates all thirteen.
    """

    COMPLETE = "complete"
    COMPLETE_WITH_LIMITATIONS = "complete_with_limitations"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


class ViewCompleteness(str, Enum):
    """View-level informational completeness. Composition may only ever
    equal or *downgrade* the source extraction's own
    ``ExtractionCompleteness`` (Non-Strengthening) -- never upgrade it.
    """

    COMPLETE = "complete"
    COMPLETE_WITH_LIMITATIONS = "complete_with_limitations"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


#: Total ordering used to compare/aggregate completeness values across
#: both the section and view scopes -- lower rank is "better." Composition
#: never moves a value to a *lower* rank than its most severe input
#: (Non-Strengthening); it may only preserve or raise the rank
#: (i.e. downgrade informational quality).
_COMPLETENESS_RANK: dict[str, int] = {
    "complete": 0,
    "complete_with_limitations": 1,
    "incomplete": 2,
    "invalid": 3,
}


def _worse(a: str, b: str) -> str:
    return a if _COMPLETENESS_RANK[a] >= _COMPLETENESS_RANK[b] else b


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
            "code": self.code,
            "message": self.message,
            "section_id": self.section_id,
            "blocking": self.blocking,
        }


@dataclass(frozen=True)
class EvidenceGroupRef:
    """A structured, deterministic reference to one selected extraction
    category's content, as placed into a section. Never a copy of the
    underlying value -- ``category`` plus the shared ``ExtractionResult``
    is sufficient for a caller (or a future renderer) to look up the
    exact, untouched canonical value.
    """

    category: str
    requirement_level: str
    applicability: str
    is_primary: bool
    finding_classifications: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "requirement_level": self.requirement_level,
            "applicability": self.applicability,
            "is_primary": self.is_primary,
            "finding_classifications": list(self.finding_classifications),
        }


@dataclass(frozen=True)
class SectionRecord:
    """One composed PFR-001 section. Every field is a structured
    reference into the source ``ExtractionResult`` -- never rendered
    prose, never a duplicated copy of canonical evidence.
    """

    section_id: PFRSectionId
    order: int
    applicability: SectionApplicability
    completeness: SectionCompleteness
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
        object.__setattr__(
            self, "uncertainty_categories", tuple(self.uncertainty_categories),
        )
        object.__setattr__(
            self, "limitation_categories", tuple(self.limitation_categories),
        )
        object.__setattr__(
            self, "filtering_disclosure_categories",
            tuple(self.filtering_disclosure_categories),
        )
        object.__setattr__(
            self, "provenance_categories", tuple(self.provenance_categories),
        )
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
        if (
            self.applicability == SectionApplicability.NOT_APPLICABLE
            and not self.not_applicable_reason
        ):
            raise ValueError(
                f"SectionRecord {self.section_id.value!r}: NOT_APPLICABLE "
                "requires an explicit not_applicable_reason"
            )
        if (
            self.applicability != SectionApplicability.NOT_APPLICABLE
            and self.not_applicable_reason is not None
        ):
            raise ValueError(
                f"SectionRecord {self.section_id.value!r}: "
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
            "filtering_disclosure_categories": list(
                self.filtering_disclosure_categories
            ),
            "provenance_categories": list(self.provenance_categories),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "not_applicable_reason": self.not_applicable_reason,
        }


# ═══════════════════════════════════════════════════════════════════════
# Composed view model
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PhaseReportView:
    """The deterministic, structured Phase Report View: all thirteen
    PFR-001 sections composed from one ``phase_report_v1`` extraction
    result. Suitable as input to a future Markdown/plain-text/HTML/JSON
    renderer -- never itself rendered prose.
    """

    view_id: str
    view_version: str
    source_evidence_id: str
    source_record_digest: str
    source_extraction_digest: str
    profile_id: str
    profile_version: str
    phase_id: str
    phase_class: PhaseClass
    report_status: str
    completeness: ViewCompleteness
    sections: tuple[SectionRecord, ...]
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
        object.__setattr__(
            self, "filtering_disclosures", tuple(self.filtering_disclosures),
        )
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
            "phase_class": self.phase_class.value,
            "report_status": self.report_status,
            "completeness": self.completeness.value,
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
        identical convention 134E.1/134E.2 established. Contains no
        renderer or delivery state by construction (this model has no
        such field), so neither can leak into the digest. Changes
        whenever section assignments, completeness, uncertainty, or
        limitations materially change; stable under equivalent input
        ordering because every collection here is already placed in a
        fixed, deterministic order at construction time.
        """
        d = self.to_dict(include_digest=False)
        canonical = json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# Composition entry point
# ═══════════════════════════════════════════════════════════════════════


def _selected_by_category(
    result: ExtractionResult,
) -> dict[str, SelectedEvidenceItem]:
    return {item.category: item for item in result.selected_evidence}


def _finding_classifications(value: Any) -> tuple[str, ...]:
    """Extract a deterministic, sorted tuple of FindingClassification
    values present in a selected category's value, if any. Handles
    tuples of FindingRecord/RepairRecord (via ``.classification`` or
    ``.original_finding.classification``) and passes through anything
    else as empty -- never guesses at structure it does not recognize.
    """
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


def _compose_section(
    section_id: PFRSectionId,
    order: int,
    result: ExtractionResult,
    selected: dict[str, SelectedEvidenceItem],
    missing_by_category: dict[str, str],
    filtering_categories: frozenset[str],
    diagnostics_out: list[CompositionDiagnostic],
) -> SectionRecord:
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
            evidence_groups.append(EvidenceGroupRef(
                category=category,
                requirement_level=item.requirement_level.value,
                applicability=item.applicability.value,
                is_primary=is_primary,
                finding_classifications=_finding_classifications(item.value),
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

    if any_invalid:
        applicability = SectionApplicability.INVALID
        completeness = SectionCompleteness.INVALID
        not_applicable_reason = None
    elif any_required_missing:
        applicability = SectionApplicability.INCOMPLETE
        completeness = SectionCompleteness.INCOMPLETE
        not_applicable_reason = None
    elif not any_present and any_conditionally_missing:
        # 134E.3V finding (BLOCKING, repaired): a conditionally-required-
        # and-missing category (extraction diagnostic code
        # "conditionally_required_category_missing") was previously
        # indistinguishable, at this point, from a category the profile
        # genuinely marks not-applicable for this phase class (which
        # produces zero diagnostic, only a FilteringDisclosure). Both
        # left `any_present=False`, so the old condition below
        # (`section_id in _CONDITIONAL_SECTIONS`) fired for either case,
        # composing a real, disclosed extraction-level limitation as
        # NOT_APPLICABLE + COMPLETE -- silently discarding the limitation
        # extraction itself recorded (a Non-Strengthening violation:
        # "conditionally missing" strengthened into "not applicable").
        # `missing_required_categories` remained non-empty in that state,
        # directly contradicting an applicability that claims nothing is
        # missing. A conditionally-missing category must never be
        # composed as NOT_APPLICABLE, regardless of `any_present`.
        applicability = SectionApplicability.UNAVAILABLE_WITH_DISCLOSURE
        completeness = SectionCompleteness.COMPLETE_WITH_LIMITATIONS
        not_applicable_reason = None
    elif not any_present and section_id in _CONDITIONAL_SECTIONS:
        applicability = SectionApplicability.NOT_APPLICABLE
        completeness = SectionCompleteness.COMPLETE
        not_applicable_reason = (
            f"no category in {list(categories)} was selected for phase class "
            f"{result.phase_class.value!r} under profile {result.profile_id!r}; "
            "extraction disposed of every source category as not_applicable "
            "or optional-and-absent for this phase class"
        )
    elif not any_present:
        applicability = SectionApplicability.UNAVAILABLE_WITH_DISCLOSURE
        completeness = SectionCompleteness.INCOMPLETE
        not_applicable_reason = None
        section_diagnostics.append(CompositionDiagnostic(
            code="structurally_empty_required_section",
            message=(
                f"section {section_id.value!r} has no selected evidence and "
                "is not a conditionally-not-applicable section"
            ),
            section_id=section_id.value,
            blocking=True,
        ))
    elif any_conditionally_missing:
        applicability = SectionApplicability.MATERIALLY_POPULATED
        completeness = SectionCompleteness.COMPLETE_WITH_LIMITATIONS
        not_applicable_reason = None
    else:
        applicability = SectionApplicability.MATERIALLY_POPULATED
        completeness = SectionCompleteness.COMPLETE
        not_applicable_reason = None

    diagnostics_out.extend(section_diagnostics)

    return SectionRecord(
        section_id=section_id,
        order=order,
        applicability=applicability,
        completeness=completeness,
        evidence_groups=tuple(evidence_groups),
        missing_required_categories=tuple(missing_required),
        uncertainty_categories=tuple(sorted(set(uncertainty_categories))),
        limitation_categories=tuple(sorted(set(limitation_categories))),
        filtering_disclosure_categories=tuple(sorted(set(filtering_here))),
        provenance_categories=tuple(sorted(set(provenance_here))),
        diagnostics=tuple(section_diagnostics),
        not_applicable_reason=not_applicable_reason,
    )


def compose_phase_report_view(
    result: ExtractionResult,
    *,
    view_version: str = VIEW_SCHEMA_VERSION,
) -> PhaseReportView:
    """Compose a deterministic ``PhaseReportView`` from an already-produced
    ``phase_report_v1`` extraction result.

    Fail-closed (raises ``ValueError``) for: an unsupported view version,
    an extraction result produced under the wrong profile
    (``operator_report_v1`` or any other non-``phase_report_v1`` profile
    is rejected -- Phase Report View Composition never silently accepts
    a result built for a different audience), an
    :class:`~pcae.core.evidence_extraction.ExtractionCompleteness.INVALID`
    extraction result (nothing safe to compose), a missing source
    identity/digest, or an orphan finding/repair/uncertainty/limitation
    reference this module can independently detect.

    Returns normally (never raises) for every other extraction
    completeness outcome -- composition classifies the resulting view as
    COMPLETE, COMPLETE_WITH_LIMITATIONS, or INCOMPLETE and never upgrades
    the source extraction's own completeness (Non-Strengthening); it may
    only preserve or downgrade it, and independently detects additional
    composition-only defects (unassigned required evidence, missing
    mandatory section content, structurally empty required sections) that
    can downgrade completeness even when the source extraction itself
    reported COMPLETE.
    """

    if view_version not in SUPPORTED_VIEW_VERSIONS:
        raise ValueError(
            f"Unsupported Phase Report View version {view_version!r}; "
            f"supported: {sorted(SUPPORTED_VIEW_VERSIONS)}"
        )

    if result.profile_id != PROFILE_ID_PHASE_REPORT:
        raise ValueError(
            "Phase Report View Composition requires an extraction result "
            f"produced under profile {PROFILE_ID_PHASE_REPORT!r}; got "
            f"{result.profile_id!r}"
        )

    if result.completeness == ExtractionCompleteness.INVALID:
        raise ValueError(
            "Cannot compose a Phase Report View from an INVALID extraction "
            "result -- extraction reported a genuine contradiction "
            f"(diagnostics: {[d.to_dict() for d in result.diagnostics]})"
        )

    if not result.source_evidence_id:
        raise ValueError("ExtractionResult.source_evidence_id must be non-empty")
    if not result.source_record_digest:
        raise ValueError("ExtractionResult.source_record_digest must be non-empty")

    selected = _selected_by_category(result)

    # Orphan reference re-check (defense in depth, mirroring 134E.2's own
    # posture): every uncertainty/limitation category referenced by a
    # selected item must exist among the known section-mapped categories.
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

    diagnostics: list[CompositionDiagnostic] = []
    sections: list[SectionRecord] = []
    assigned_categories: set[str] = set()

    for order, section_id in enumerate(PFR_SECTION_ORDER, start=1):
        section = _compose_section(
            section_id, order, result, selected, missing_by_category,
            filtering_categories, diagnostics,
        )
        sections.append(section)
        for group in section.evidence_groups:
            if group.is_primary:
                assigned_categories.add(group.category)

    # Non-Omission accounting: every category selected by extraction must
    # be owned by exactly one primary section. An unassigned selected
    # category is a composition-defeating BLOCKING defect -- this should
    # be structurally unreachable given `_CATEGORY_PRIMARY_SECTION` covers
    # every `EXTRACTION_CATEGORIES` entry, but is asserted explicitly per
    # the phase brief's own instruction ("implement an assignment-
    # accounting mechanism").
    unassigned = set(selected.keys()) - assigned_categories
    if unassigned:
        diagnostics.append(CompositionDiagnostic(
            code="unassigned_required_evidence",
            message=f"selected categories with no owning primary section: {sorted(unassigned)}",
            section_id=None,
            blocking=True,
        ))

    section_blocking = any(
        d.blocking for section in sections for d in section.diagnostics
    ) or any(d.blocking for d in diagnostics)

    # View-level completeness: never better than the source extraction's
    # own completeness (Non-Strengthening); may be worse if composition
    # independently found a structural defect.
    view_rank_floor = result.completeness.value
    if section_blocking:
        view_rank_floor = _worse(view_rank_floor, "incomplete")
    any_section_incomplete = any(
        s.completeness in (SectionCompleteness.INCOMPLETE, SectionCompleteness.INVALID)
        for s in sections
    )
    if any_section_incomplete:
        worst_section = "invalid" if any(
            s.completeness == SectionCompleteness.INVALID for s in sections
        ) else "incomplete"
        view_rank_floor = _worse(view_rank_floor, worst_section)

    view_completeness = ViewCompleteness(view_rank_floor)

    cross_section_uncertainty = tuple(sorted({
        u.category for u in result.uncertainty
    }))
    cross_section_limitation = tuple(sorted({
        l.category for l in result.limitations
    }))
    filtering_summary = tuple(sorted(
        fd.excluded_category for fd in result.filtering_disclosures
    ))

    view_id = f"phase-report-view:{result.source_evidence_id}:{result.profile_id}"

    view = PhaseReportView(
        view_id=view_id,
        view_version=view_version,
        source_evidence_id=result.source_evidence_id,
        source_record_digest=result.source_record_digest,
        source_extraction_digest=result.compute_digest(),
        profile_id=result.profile_id,
        profile_version=result.profile_version,
        phase_id=result.source_evidence_id.split("#", 1)[0],
        phase_class=result.phase_class,
        report_status="composed",
        completeness=view_completeness,
        sections=tuple(sections),
        cross_section_uncertainty=cross_section_uncertainty,
        cross_section_limitation=cross_section_limitation,
        filtering_disclosures=filtering_summary,
        diagnostics=tuple(diagnostics),
    )

    if not view.sections or len(view.sections) != len(PFR_SECTION_ORDER):
        raise ValueError(  # pragma: no cover — structurally unreachable
            "Composed view does not contain all thirteen PFR-001 sections"
        )

    if all(
        s.applicability in (
            SectionApplicability.NOT_APPLICABLE,
            SectionApplicability.UNAVAILABLE_WITH_DISCLOSURE,
        )
        for s in view.sections
    ):
        raise ValueError(
            "Composition produced a structurally empty successful report -- "
            "every section is not_applicable/unavailable; refusing to "
            "return a silent empty success"
        )

    return view
