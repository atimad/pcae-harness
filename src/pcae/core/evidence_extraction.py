"""Phase 134E.2: Evidence Extraction.

Implements the deterministic, audience-aware, transport-independent
Evidence Extraction layer over the Canonical Engineering Evidence
executable model (134E.1, independently verified and repaired by
134E.1V). Evidence Extraction answers exactly one question: "which
canonical engineering facts are required for a particular derived
view?" It selects and preserves evidence; it never composes report
prose, summarizes findings, renders content, delivers notifications,
creates new engineering evidence, infers importance through model
reasoning, or ranks findings subjectively.

**This module is not yet active lifecycle authority**, exactly like
`canonical_engineering_evidence.py` before it. Nothing in the current
governed reporting/finalization/notification path imports or calls into
this module, and this module imports only `canonical_engineering_
evidence` and the standard library. The current governed reporting and
finalization path remains fully operational and unaffected.

Architectural position (preserved, not merged):

    Canonical Engineering Evidence
            |
            v
    Evidence Extraction              <- this module
            |
            v
    Derived Evidence View Composition   (134E.3/134E.4, not implemented)
            |
            v
    Rendering                            (134E.5, not implemented)
            |
            v
    Delivery                             (134E.6, not implemented)

Extraction decides which canonical facts are required, optional,
conditionally required, or not applicable for a given (profile,
phase_class) pair, and preserves full traceability (provenance,
uncertainty, limitations, original finding history) for whatever it
selects. View Composition -- a later, separate phase -- decides section
organization, headings, grouping, and presentation sequence. This module
implements none of that.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any

from pcae.core.canonical_engineering_evidence import (
    Applicability,
    CanonicalEngineeringEvidence,
    EvidenceProvenanceRecord,
    EvidenceRecordState,
    LimitationItem,
    PhaseClass,
    UncertaintyItem,
)


# ═══════════════════════════════════════════════════════════════════════
# Requirement vocabulary and completeness vocabulary
# ═══════════════════════════════════════════════════════════════════════


class RequirementLevel(str, Enum):
    """How mandatory one extraction category is for a given (profile,
    phase_class) pair. A REQUIRED category missing from the selected
    evidence set never disappears silently -- it is always recorded in
    ``ExtractionResult.missing_required`` with a diagnostic.
    """

    REQUIRED = "required"
    CONDITIONALLY_REQUIRED = "conditionally_required"
    OPTIONAL = "optional"
    NOT_APPLICABLE = "not_applicable"


class ExtractionCompleteness(str, Enum):
    """Extraction-level informational completeness -- distinct from, and
    strictly more demanding than, the source evidence record's own
    validity. A valid, finalized CanonicalEngineeringEvidence record may
    still extract as INCOMPLETE for a specific profile that requires more
    than the evidence record's own author disclosed as applicable.
    """

    COMPLETE = "complete"
    COMPLETE_WITH_LIMITATIONS = "complete_with_limitations"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


# ═══════════════════════════════════════════════════════════════════════
# The fixed set of extraction categories
# ═══════════════════════════════════════════════════════════════════════

#: Every extraction category maps 1:1 to a CanonicalEngineeringEvidence
#: field. No pseudo-categories, no invented groupings -- direct
#: traceability from an extraction category name back to its exact
#: canonical source field.
EXTRACTION_CATEGORIES: tuple[str, ...] = (
    "identity",
    "objective",
    "engineering_actions",
    "architectural_findings",
    "implementation_findings",
    "verification_findings",
    "defects_discovered",
    "defects_repaired",
    "incorrect_assumptions_corrected",
    "technical_debt_reviewed",
    "technical_debt_introduced",
    "notable_engineering_knowledge",
    "governance_results",
    "test_results",
    "repository_state",
    "runtime_state",
    "no_go_confirmations",
    "architectural_boundary_confirmations",
    "track_progress",
    "recommended_next_phase",
    "commit_and_push",
)

#: Categories whose canonical value is a tuple tracked by CEE's own
#: ``applicability`` mapping (134E.1's REQUIRED_APPLICABILITY_CATEGORIES).
#: For these, applicability comes from the source record. All other
#: categories are scalar/always-populated fields on a finalized record
#: (identity, objective, governance_results, test_results,
#: repository_state, runtime_state, track_progress,
#: recommended_next_phase, commit_and_push) and are treated as PRESENT
#: by construction -- a FINALIZED CanonicalEngineeringEvidence record
#: cannot exist without them (134E.1's own __post_init__ requires
#: objective/track_progress non-empty; the others are non-optional
#: constructor arguments).
_APPLICABILITY_TRACKED_CATEGORIES: frozenset[str] = frozenset({
    "engineering_actions", "architectural_findings", "implementation_findings",
    "verification_findings", "defects_discovered", "defects_repaired",
    "incorrect_assumptions_corrected", "technical_debt_reviewed",
    "technical_debt_introduced", "notable_engineering_knowledge",
    "no_go_confirmations", "architectural_boundary_confirmations",
})


def _category_value(evidence: CanonicalEngineeringEvidence, category: str) -> Any:
    return getattr(evidence, category)


def _category_applicability(
    evidence: CanonicalEngineeringEvidence, category: str,
) -> Applicability:
    if category in _APPLICABILITY_TRACKED_CATEGORIES:
        return evidence.applicability[category]
    return Applicability.PRESENT


# ═══════════════════════════════════════════════════════════════════════
# Extraction profile model
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CategoryRule:
    """The requirement level for one category, per phase class. Every
    entry is explicit -- no phase class is left to an implicit default,
    per the phase brief's determinism requirement.
    """

    category: str
    requirement_by_phase_class: MappingProxyType  # PhaseClass -> RequirementLevel

    def __post_init__(self) -> None:
        if self.category not in EXTRACTION_CATEGORIES:
            raise ValueError(f"Unknown extraction category: {self.category!r}")
        missing = set(PhaseClass) - set(self.requirement_by_phase_class.keys())
        if missing:
            raise ValueError(
                f"CategoryRule for {self.category!r} is missing an explicit "
                f"requirement level for phase classes: "
                f"{sorted(m.value for m in missing)}"
            )
        object.__setattr__(
            self, "requirement_by_phase_class",
            MappingProxyType(dict(self.requirement_by_phase_class)),
        )

    def requirement_for(self, phase_class: PhaseClass) -> RequirementLevel:
        return self.requirement_by_phase_class[phase_class]


@dataclass(frozen=True)
class ExtractionProfile:
    """A named, versioned extraction policy. Never renders or composes;
    only decides which canonical categories are required/optional/
    conditionally-required/not-applicable for a given phase class.

    Contains no field referencing agent identity, model identity,
    transport, rendering format, or network state -- extraction behavior
    is a pure function of (evidence, profile, phase_class).
    """

    profile_id: str
    profile_version: str
    supported_phase_classes: frozenset  # frozenset[PhaseClass]
    category_rules: tuple  # tuple[CategoryRule, ...], deterministic order

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise ValueError("ExtractionProfile.profile_id must be non-empty")
        if not self.profile_version:
            raise ValueError("ExtractionProfile.profile_version must be non-empty")
        seen = {rule.category for rule in self.category_rules}
        missing = set(EXTRACTION_CATEGORIES) - seen
        if missing:
            raise ValueError(
                f"ExtractionProfile {self.profile_id!r} is missing category "
                f"rules for: {sorted(missing)}"
            )
        object.__setattr__(self, "category_rules", tuple(self.category_rules))
        object.__setattr__(
            self, "supported_phase_classes", frozenset(self.supported_phase_classes),
        )

    def requirement_for(self, category: str, phase_class: PhaseClass) -> RequirementLevel:
        for rule in self.category_rules:
            if rule.category == category:
                return rule.requirement_for(phase_class)
        raise ValueError(f"No rule for category {category!r}")  # pragma: no cover


# ── Profile registry — a small explicit dict, not a plugin framework ──

_PROFILE_REGISTRY: dict[str, ExtractionProfile] = {}


def register_profile(profile: ExtractionProfile) -> None:
    """Register an extraction profile. Registration order never affects
    extraction output for any individual profile -- each profile's own
    ``category_rules`` order is fixed at profile-construction time, not
    at registration time, so registering profiles in a different order
    (or registering a brand-new future profile) cannot change any
    existing profile's behavior.
    """
    _PROFILE_REGISTRY[profile.profile_id] = profile


def get_profile(profile_id: str) -> ExtractionProfile:
    if profile_id not in _PROFILE_REGISTRY:
        raise ValueError(f"Unsupported extraction profile: {profile_id!r}")
    return _PROFILE_REGISTRY[profile_id]


def _all_required(level: RequirementLevel) -> MappingProxyType:
    return MappingProxyType({pc: level for pc in PhaseClass})


def _by_phase_class(**overrides: RequirementLevel) -> MappingProxyType:
    """Build a per-phase-class requirement map. ``overrides`` keys are
    PhaseClass *values* (e.g. "architecture"); every PhaseClass not named
    defaults to RequirementLevel.REQUIRED, matching PFR-001 Section 6's
    own default ("all other sections mandatory across all six phase
    classes with no class-dependent variation") -- callers only need to
    name the *exceptions*.
    """
    result = {pc: RequirementLevel.REQUIRED for pc in PhaseClass}
    for key, level in overrides.items():
        result[PhaseClass(key)] = level
    return MappingProxyType(result)


# ═══════════════════════════════════════════════════════════════════════
# Phase Report extraction profile — PFR-001's thirteen sections
# ═══════════════════════════════════════════════════════════════════════

PROFILE_ID_PHASE_REPORT = "phase_report_v1"
_PHASE_REPORT_VERSION = "1.0"

_PHASE_REPORT_RULES: tuple[CategoryRule, ...] = (
    # Section 1 (Phase Identity) sources — mandatory every class.
    CategoryRule("identity", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("repository_state", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("commit_and_push", _all_required(RequirementLevel.REQUIRED)),
    # Section 2 (Executive Summary) source.
    CategoryRule("objective", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("engineering_actions", _all_required(RequirementLevel.REQUIRED)),
    # Section 3 (Architectural Findings) — 133B §6: mandatory by default;
    # architecture/contract/planning/review_hardening phases centrally
    # concern architecture, implementation/verification phases may or may
    # not touch it.
    CategoryRule("architectural_findings", _by_phase_class(
        implementation=RequirementLevel.CONDITIONALLY_REQUIRED,
        verification=RequirementLevel.CONDITIONALLY_REQUIRED,
    )),
    # Section 4 (Implementation Findings) — 133B §6 named exception:
    # mandatory only for implementation phases; all other classes state
    # explicitly none (NOT_APPLICABLE), except review/hardening which may
    # legitimately include implementation work.
    CategoryRule("implementation_findings", _by_phase_class(
        architecture=RequirementLevel.NOT_APPLICABLE,
        contract=RequirementLevel.NOT_APPLICABLE,
        planning=RequirementLevel.NOT_APPLICABLE,
        verification=RequirementLevel.NOT_APPLICABLE,
        review_hardening=RequirementLevel.CONDITIONALLY_REQUIRED,
    )),
    # Section 5 (Verification Findings) — 133B §6 named exception:
    # mandatory (full re-derivation) only for verification phases;
    # implementation phases get a regression summary only
    # (conditionally required); all other classes state explicitly none.
    CategoryRule("verification_findings", _by_phase_class(
        architecture=RequirementLevel.NOT_APPLICABLE,
        contract=RequirementLevel.NOT_APPLICABLE,
        planning=RequirementLevel.NOT_APPLICABLE,
        implementation=RequirementLevel.CONDITIONALLY_REQUIRED,
        review_hardening=RequirementLevel.CONDITIONALLY_REQUIRED,
    )),
    # Defects/repairs/corrected-assumptions: not every phase discovers or
    # repairs a defect -- conditionally required everywhere (must be
    # represented with an explicit disposition, need not be non-empty).
    CategoryRule("defects_discovered", _all_required(RequirementLevel.CONDITIONALLY_REQUIRED)),
    CategoryRule("defects_repaired", _all_required(RequirementLevel.CONDITIONALLY_REQUIRED)),
    CategoryRule("incorrect_assumptions_corrected", _all_required(RequirementLevel.CONDITIONALLY_REQUIRED)),
    # Section 6 (Technical Debt Review) — 133B §5: at least one explicit
    # pass over inherited debt is always required, even if "no change".
    CategoryRule("technical_debt_reviewed", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("technical_debt_introduced", _all_required(RequirementLevel.OPTIONAL)),
    # Section 13 (Notable Engineering Knowledge) — mandatory every class
    # (133B §4: "or explicit 'no new durable lesson'" is still a required
    # disposition, not silence).
    CategoryRule("notable_engineering_knowledge", _all_required(RequirementLevel.REQUIRED)),
    # Section 7 (Governance Results), Section 8 (Test Results) — mandatory.
    CategoryRule("governance_results", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("test_results", _all_required(RequirementLevel.REQUIRED)),
    # Section 10 (Architectural Boundary Confirmation) — mandatory.
    CategoryRule("architectural_boundary_confirmations", _all_required(RequirementLevel.REQUIRED)),
    # Section 9 (No-Go Confirmation) — mandatory whenever the phase named
    # non-goals; conditionally required rather than hard-required since
    # not every phase class necessarily declares one.
    CategoryRule("no_go_confirmations", _all_required(RequirementLevel.CONDITIONALLY_REQUIRED)),
    # Section 11 (Track Progress), Section 12 (Next Phase) — mandatory.
    CategoryRule("track_progress", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("recommended_next_phase", _all_required(RequirementLevel.REQUIRED)),
    # Runtime state — supports Phase Identity / Architectural Boundary
    # sections' runtime confirmations; mandatory every class.
    CategoryRule("runtime_state", _all_required(RequirementLevel.REQUIRED)),
)


def _build_phase_report_profile() -> ExtractionProfile:
    return ExtractionProfile(
        profile_id=PROFILE_ID_PHASE_REPORT,
        profile_version=_PHASE_REPORT_VERSION,
        supported_phase_classes=frozenset(PhaseClass),
        category_rules=_PHASE_REPORT_RULES,
    )


# ═══════════════════════════════════════════════════════════════════════
# Operator Report extraction profile — decision-completeness for a
# mobile-first operator audience. Broader than a status-only summary by
# design (a minimal status/tests/next-phase-only extraction is invalid
# for this profile).
# ═══════════════════════════════════════════════════════════════════════

PROFILE_ID_OPERATOR_REPORT = "operator_report_v1"
_OPERATOR_REPORT_VERSION = "1.0"

_OPERATOR_REPORT_RULES: tuple[CategoryRule, ...] = (
    CategoryRule("identity", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("repository_state", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("commit_and_push", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("objective", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("engineering_actions", _all_required(RequirementLevel.REQUIRED)),
    # Architectural significance: required so the operator can judge
    # engineering importance, not just completion status.
    CategoryRule("architectural_findings", _by_phase_class(
        implementation=RequirementLevel.CONDITIONALLY_REQUIRED,
        verification=RequirementLevel.CONDITIONALLY_REQUIRED,
    )),
    CategoryRule("implementation_findings", _by_phase_class(
        architecture=RequirementLevel.NOT_APPLICABLE,
        contract=RequirementLevel.NOT_APPLICABLE,
        planning=RequirementLevel.NOT_APPLICABLE,
        verification=RequirementLevel.NOT_APPLICABLE,
        review_hardening=RequirementLevel.CONDITIONALLY_REQUIRED,
    )),
    CategoryRule("verification_findings", _by_phase_class(
        architecture=RequirementLevel.NOT_APPLICABLE,
        contract=RequirementLevel.NOT_APPLICABLE,
        planning=RequirementLevel.NOT_APPLICABLE,
        implementation=RequirementLevel.CONDITIONALLY_REQUIRED,
        review_hardening=RequirementLevel.CONDITIONALLY_REQUIRED,
    )),
    # An operator must be able to see defects/repairs/corrected
    # assumptions whenever they exist -- required (must be explicitly
    # represented), same disposition-not-content distinction as above.
    CategoryRule("defects_discovered", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("defects_repaired", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("incorrect_assumptions_corrected", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("technical_debt_reviewed", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("technical_debt_introduced", _all_required(RequirementLevel.OPTIONAL)),
    CategoryRule("notable_engineering_knowledge", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("governance_results", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("test_results", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("architectural_boundary_confirmations", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("no_go_confirmations", _all_required(RequirementLevel.CONDITIONALLY_REQUIRED)),
    CategoryRule("track_progress", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("recommended_next_phase", _all_required(RequirementLevel.REQUIRED)),
    CategoryRule("runtime_state", _all_required(RequirementLevel.REQUIRED)),
)


def _build_operator_report_profile() -> ExtractionProfile:
    return ExtractionProfile(
        profile_id=PROFILE_ID_OPERATOR_REPORT,
        profile_version=_OPERATOR_REPORT_VERSION,
        supported_phase_classes=frozenset(PhaseClass),
        category_rules=_OPERATOR_REPORT_RULES,
    )


register_profile(_build_phase_report_profile())
register_profile(_build_operator_report_profile())

#: Note (Non-Omission / Non-Strengthening, Track 133 §10/§18-19; PFN-001
#: authority split): "notification/finalization result" is deliberately
#: absent from EXTRACTION_CATEGORIES and from both profiles above.
#: CanonicalEngineeringEvidence itself carries no such field -- Track
#: 133F confirmed this exclusion directly ("notification dispatch result
#: ... correctly outside the Canonical Engineering Evidence model,"
#: owned by PFN-001 instead). Extraction cannot select a fact the
#: canonical record does not carry, and must not invent one: it does not
#: query notification/delivery state, does not import
#: pcae.core.notifications, and produces no such category. This is the
#: same authority split 134E.1's own module docstring already commits to
#: (delivery is not engineering evidence).


# ═══════════════════════════════════════════════════════════════════════
# Extraction result model
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SelectedEvidenceItem:
    """One selected, fully-traceable evidence item. ``value`` is always
    the exact, untouched canonical value (never a copy that strengthens,
    weakens, or re-derives it) -- extraction selects, it never rewrites.
    """

    category: str
    source_evidence_id: str
    value: Any
    applicability: Applicability
    requirement_level: RequirementLevel
    provenance: tuple  # tuple[EvidenceProvenanceRecord, ...]
    verification_state: str | None
    uncertainty_refs: tuple  # tuple[str, ...] -- categories of matching UncertaintyItem entries
    limitation_refs: tuple  # tuple[str, ...]
    selection_reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "uncertainty_refs", tuple(self.uncertainty_refs))
        object.__setattr__(self, "limitation_refs", tuple(self.limitation_refs))
        if not self.category:
            raise ValueError("SelectedEvidenceItem.category must be non-empty")
        if not self.source_evidence_id:
            raise ValueError("SelectedEvidenceItem.source_evidence_id must be non-empty")
        if not self.selection_reason:
            raise ValueError("SelectedEvidenceItem.selection_reason must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "source_evidence_id": self.source_evidence_id,
            "value": _jsonable(self.value),
            "applicability": self.applicability.value,
            "requirement_level": self.requirement_level.value,
            "provenance": [p.to_dict() for p in self.provenance],
            "verification_state": self.verification_state,
            "uncertainty_refs": list(self.uncertainty_refs),
            "limitation_refs": list(self.limitation_refs),
            "selection_reason": self.selection_reason,
        }


@dataclass(frozen=True)
class FilteringDisclosure:
    """Records that a profile intentionally excluded optional canonical
    evidence -- so a later View Composition stage never needs to guess
    whether an absence was deliberate or a bug.
    """

    excluded_category: str
    profile_rule: str
    material: bool
    still_available_in_canonical_record: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "excluded_category": self.excluded_category,
            "profile_rule": self.profile_rule,
            "material": self.material,
            "still_available_in_canonical_record": self.still_available_in_canonical_record,
        }


@dataclass(frozen=True)
class ExtractionDiagnostic:
    code: str
    message: str
    category: str | None
    blocking: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code, "message": self.message,
            "category": self.category, "blocking": self.blocking,
        }


@dataclass(frozen=True)
class ExtractionResult:
    """The deterministic, structured output of one extraction. Suitable
    as input to a later View Composition stage -- never free text.
    """

    source_evidence_id: str
    source_record_digest: str
    profile_id: str
    profile_version: str
    phase_class: PhaseClass
    selected_evidence: tuple  # tuple[SelectedEvidenceItem, ...]
    missing_required: tuple  # tuple[str, ...]
    uncertainty: tuple  # tuple[UncertaintyItem, ...]
    limitations: tuple  # tuple[LimitationItem, ...]
    provenance: tuple  # tuple[EvidenceProvenanceRecord, ...]
    filtering_disclosures: tuple  # tuple[FilteringDisclosure, ...]
    completeness: ExtractionCompleteness
    diagnostics: tuple  # tuple[ExtractionDiagnostic, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "selected_evidence", tuple(self.selected_evidence))
        object.__setattr__(self, "missing_required", tuple(self.missing_required))
        object.__setattr__(self, "uncertainty", tuple(self.uncertainty))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "filtering_disclosures", tuple(self.filtering_disclosures))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        d: dict[str, Any] = {
            "source_evidence_id": self.source_evidence_id,
            "source_record_digest": self.source_record_digest,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "phase_class": self.phase_class.value,
            "selected_evidence": [s.to_dict() for s in self.selected_evidence],
            "missing_required": list(self.missing_required),
            "uncertainty": [u.to_dict() for u in self.uncertainty],
            "limitations": [l.to_dict() for l in self.limitations],
            "provenance": [p.to_dict() for p in self.provenance],
            "filtering_disclosures": [f.to_dict() for f in self.filtering_disclosures],
            "completeness": self.completeness.value,
            "diagnostics": [d_.to_dict() for d_ in self.diagnostics],
        }
        if include_digest:
            d["extraction_digest"] = self.compute_digest()
        return d

    def compute_digest(self) -> str:
        """Deterministic SHA-256 digest over the canonical serialized
        representation, following the identical convention 134E.1
        established for ``CanonicalEngineeringEvidence.compute_digest()``
        (sorted-key JSON, digest field itself excluded). No approved
        timestamp exists on this result to exclude -- extraction carries
        no timestamp of its own; it inherits determinism entirely from
        its source evidence's own digest.
        """
        d = self.to_dict(include_digest=False)
        canonical = json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


def _jsonable(value: Any) -> Any:
    """Best-effort conversion of a selected canonical value (which may be
    a tuple of frozen dataclasses, a single frozen dataclass, or a plain
    scalar) into a JSON-serializable structure, reusing each type's own
    ``to_dict()`` where available -- never re-deriving or summarizing
    content.
    """
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    return value


# ═══════════════════════════════════════════════════════════════════════
# Extraction entry point
# ═══════════════════════════════════════════════════════════════════════


def extract(
    evidence: CanonicalEngineeringEvidence,
    profile_id: str,
    *,
    profile_version: str | None = None,
) -> ExtractionResult:
    """Extract evidence for one derived-view profile.

    ``profile_version``, if given, must match the registered profile's
    own version exactly -- an explicit, fail-closed check distinct from
    ``profile_id`` lookup, so a caller pinned to a specific profile
    version (e.g. a future View Composition stage built against
    ``phase_report_v1``) never silently receives output from an
    incompatible future version. Omitting it uses whatever version is
    currently registered.

    Fail-closed (raises ``ValueError``) for structural/API misuse:
    unsupported profile, unsupported profile version, unsupported phase
    class, a non-FINALIZED (or otherwise invalid) source evidence record,
    or an uncertainty/limitation entry referencing a category outside
    the known category set (an orphan reference CanonicalEngineeringEvidence's
    own construction-time validation should already have prevented --
    this is a defensive re-check, not a new authority).

    Returns normally (never raises) for every *evidence-completeness*
    outcome relative to the profile's own requirements -- COMPLETE,
    COMPLETE_WITH_LIMITATIONS, INCOMPLETE, or INVALID are all ordinary,
    inspectable results a caller reads from ``ExtractionResult.
    completeness`` and ``.diagnostics``, never hidden behind an exception.
    """
    profile = get_profile(profile_id)

    if profile_version is not None and profile_version != profile.profile_version:
        raise ValueError(
            f"Unsupported profile version {profile_version!r} for profile "
            f"{profile_id!r}; registered version is {profile.profile_version!r}"
        )

    if evidence.phase_class not in profile.supported_phase_classes:
        raise ValueError(
            f"Profile {profile_id!r} does not support phase class "
            f"{evidence.phase_class.value!r}"
        )

    if evidence.state != EvidenceRecordState.FINALIZED:
        raise ValueError(
            "Evidence Extraction requires a FINALIZED canonical evidence "
            f"record; got state={evidence.state.value!r}"
        )

    validation_issues = evidence.validate()
    if validation_issues:
        raise ValueError(
            "Invalid canonical evidence record: "
            + "; ".join(f"{i.code}: {i.message}" for i in validation_issues)
        )

    if not evidence.identity.evidence_id:
        raise ValueError("Missing source evidence identity")  # pragma: no cover

    # Orphan uncertainty/limitation reference check (defense in depth).
    for item in evidence.uncertainty:
        for ref in item.affected_evidence:
            if ref not in EXTRACTION_CATEGORIES:
                raise ValueError(
                    f"Orphan uncertainty reference to unknown category {ref!r}"
                )
    for item in evidence.limitations:
        for ref in item.affected_evidence:
            if ref not in EXTRACTION_CATEGORIES:
                raise ValueError(
                    f"Orphan limitation reference to unknown category {ref!r}"
                )

    phase_class = evidence.phase_class
    selected: list[SelectedEvidenceItem] = []
    missing_required: list[str] = []
    filtering_disclosures: list[FilteringDisclosure] = []
    diagnostics: list[ExtractionDiagnostic] = []
    has_incomplete = False
    has_invalid = False
    has_limitation_on_selected = False

    for category in EXTRACTION_CATEGORIES:
        requirement = profile.requirement_for(category, phase_class)
        applicability = _category_applicability(evidence, category)
        value = _category_value(evidence, category)

        category_uncertainty = tuple(
            u for u in evidence.uncertainty
            if u.category == category or category in u.affected_evidence
        )
        category_limitations = tuple(
            l for l in evidence.limitations
            if l.category == category or category in l.affected_evidence
        )
        category_provenance = tuple(
            p for p in evidence.provenance if p.covers == category
        )

        if requirement == RequirementLevel.NOT_APPLICABLE:
            if applicability == Applicability.PRESENT:
                # Profile says not applicable; evidence disagrees by
                # having real content -- select it anyway (never discard
                # real evidence), flagged optional-beyond-profile-scope.
                selected.append(SelectedEvidenceItem(
                    category=category, source_evidence_id=evidence.identity.evidence_id,
                    value=value, applicability=applicability,
                    requirement_level=RequirementLevel.OPTIONAL,
                    provenance=category_provenance, verification_state=None,
                    uncertainty_refs=tuple(u.category for u in category_uncertainty),
                    limitation_refs=tuple(l.category for l in category_limitations),
                    selection_reason=(
                        f"present in canonical record despite profile "
                        f"{profile_id!r} marking it not-applicable for "
                        f"phase class {phase_class.value!r}; selected, not discarded"
                    ),
                ))
            else:
                filtering_disclosures.append(FilteringDisclosure(
                    excluded_category=category,
                    profile_rule=f"{profile_id} v{profile.profile_version}: "
                                 f"not applicable for {phase_class.value}",
                    material=False,
                    still_available_in_canonical_record=False,
                ))
            continue

        is_present = applicability == Applicability.PRESENT
        if not is_present:
            if requirement == RequirementLevel.REQUIRED:
                missing_required.append(category)
                if applicability == Applicability.NOT_APPLICABLE:
                    # Genuine contradiction: profile requires it for this
                    # phase class, evidence author declared inapplicable.
                    has_invalid = True
                    diagnostics.append(ExtractionDiagnostic(
                        code="required_category_marked_not_applicable",
                        message=(
                            f"{category} is required by profile {profile_id!r} "
                            f"for phase class {phase_class.value!r}, but the "
                            f"evidence record marks it not_applicable"
                        ),
                        category=category, blocking=True,
                    ))
                else:
                    has_incomplete = True
                    diagnostics.append(ExtractionDiagnostic(
                        code="required_category_missing",
                        message=(
                            f"{category} is required by profile {profile_id!r} "
                            f"for phase class {phase_class.value!r}; disposition="
                            f"{applicability.value}"
                        ),
                        category=category, blocking=True,
                    ))
            elif requirement == RequirementLevel.CONDITIONALLY_REQUIRED:
                missing_required.append(category)
                has_limitation_on_selected = True
                diagnostics.append(ExtractionDiagnostic(
                    code="conditionally_required_category_missing",
                    message=(
                        f"{category} is conditionally required by profile "
                        f"{profile_id!r}; disposition={applicability.value}"
                    ),
                    category=category, blocking=False,
                ))
            else:  # OPTIONAL, not present
                filtering_disclosures.append(FilteringDisclosure(
                    excluded_category=category,
                    profile_rule=f"{profile_id} v{profile.profile_version}: optional, not present",
                    material=False,
                    still_available_in_canonical_record=False,
                ))
            continue

        # Present: select it.
        if category_uncertainty or category_limitations:
            has_limitation_on_selected = True
        verification_state = (
            category_provenance[0].verification_state if category_provenance else None
        )
        selected.append(SelectedEvidenceItem(
            category=category, source_evidence_id=evidence.identity.evidence_id,
            value=value, applicability=applicability, requirement_level=requirement,
            provenance=category_provenance, verification_state=verification_state,
            uncertainty_refs=tuple(u.category for u in category_uncertainty),
            limitation_refs=tuple(l.category for l in category_limitations),
            selection_reason=(
                f"{requirement.value} for profile {profile_id!r}, "
                f"phase class {phase_class.value!r}"
            ),
        ))

    if has_invalid:
        completeness = ExtractionCompleteness.INVALID
    elif has_incomplete:
        completeness = ExtractionCompleteness.INCOMPLETE
    elif has_limitation_on_selected:
        completeness = ExtractionCompleteness.COMPLETE_WITH_LIMITATIONS
    else:
        completeness = ExtractionCompleteness.COMPLETE

    if not selected and completeness == ExtractionCompleteness.COMPLETE:
        # Silent-empty-success is prohibited by construction: this should
        # be structurally unreachable (every finalized evidence record
        # has at least identity/governance_results/test_results/
        # repository_state/runtime_state selected), but guarded
        # explicitly per the phase brief's own instruction.
        raise ValueError(
            "Extraction produced zero selected evidence items while "
            "reporting COMPLETE -- refusing to return a silent empty success"
        )

    return ExtractionResult(
        source_evidence_id=evidence.identity.evidence_id,
        source_record_digest=evidence.compute_digest(),
        profile_id=profile_id,
        profile_version=profile.profile_version,
        phase_class=phase_class,
        selected_evidence=tuple(selected),
        missing_required=tuple(missing_required),
        uncertainty=evidence.uncertainty,
        limitations=evidence.limitations,
        provenance=evidence.provenance,
        filtering_disclosures=tuple(filtering_disclosures),
        completeness=completeness,
        diagnostics=tuple(diagnostics),
    )
