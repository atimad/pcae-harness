"""Phase 115E: Repository Decision Evaluation Prototype.

Implements the deterministic evaluation layer between 115D's Evidence
Providers and the Repository Transition Validator
(``core/repository_transition_validator.py``): ``EvaluationContext``,
``InvariantResult``, ``EvaluationResult``, and six evidence-only
deterministic invariant families.

Core principle (115A/115B, restated here): Evidence never decides.
Evaluation is deterministic. The Repository Transition Validator remains
the only authority capable of determining repository state transitions
-- nothing in this module produces a ``TransitionVerdict``.

Consumes only ``Evidence``/``EvidenceCollection`` (115C). No Git access,
no filesystem access, no subprocesses, no runtime inspection, no
lifecycle commands -- this module's only import is
``pcae.core.evidence``; it never imports ``evidence_providers.py`` or
``repository_transition_validator.py``, and performs no I/O itself.
Callers assemble an ``EvidenceCollection`` (e.g. via 115D's providers,
or 115F's ``RepositoryState``-to-``Evidence`` adapter) and pass it in;
this module only reasons about the evidence it is given.

The six invariant families implemented here share their names with
``repository_transition_validator.py``'s ``STRUCTURAL_INVARIANTS``
(``phase_identity_consistency``, ``metadata_consistency``,
``report_completeness``, ``canonical_promotion_eligibility``) plus two
new evidence-only families (``push_state_consistency``,
``runtime_execution_unavailable``) -- deliberately, since this module is
the evidence-based analogue the validator's own structural checks are
expected to integrate with. The two implementations remain independent
at the code level: this module still shares no code and no import with
the validator's own checks (which operate on ``RepositoryState`` fields,
never on ``Evidence``); the dependency runs in one direction only, as of
115F, from ``repository_transition_validator.py`` calling into this
module (never the reverse) to attach an optional, additive explanation
to its ``TransitionResult`` -- verdict authority remains entirely with
the validator's own unchanged invariant checks.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from pcae.core.evidence import (
    Evidence,
    EvidenceCollection,
    EvidenceFreshness,
    EvidenceReference,
)

SEVERITIES: tuple[str, ...] = ("blocking", "warning", "informational")


class InvariantStatus(str, Enum):
    """The 4 frozen invariant evaluation statuses (Objective 3). No
    fifth status exists -- an invariant that cannot be evaluated safely
    is ``UNKNOWN``, never silently ``PASS``."""

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class InvariantResult:
    """One evaluated invariant (Objective 3). ``supporting_evidence``
    and ``conflicting_evidence`` are ``EvidenceReference`` tuples --
    stable Evidence ID citations, never inlined evidence copies, so a
    result can be reproduced by re-resolving the same IDs against the
    same ``EvaluationContext``. ``explanation`` is deterministic,
    template-generated text -- never AI-generated prose (Objective 6)."""

    invariant_id: str
    status: InvariantStatus
    severity: str
    supporting_evidence: tuple[EvidenceReference, ...]
    conflicting_evidence: tuple[EvidenceReference, ...]
    explanation: str
    suggested_repair: str | None = None

    def __post_init__(self) -> None:
        if not self.invariant_id:
            raise ValueError("InvariantResult invariant_id must be non-empty")
        object.__setattr__(self, "status", InvariantStatus(self.status))
        if self.severity not in SEVERITIES:
            raise ValueError(
                f"InvariantResult severity must be one of {SEVERITIES}, got {self.severity!r}"
            )
        object.__setattr__(self, "supporting_evidence", tuple(self.supporting_evidence))
        object.__setattr__(self, "conflicting_evidence", tuple(self.conflicting_evidence))
        if not self.explanation:
            raise ValueError("InvariantResult explanation must be non-empty")

    @property
    def all_referenced_evidence(self) -> tuple[EvidenceReference, ...]:
        return self.supporting_evidence + self.conflicting_evidence


@dataclass(frozen=True)
class EvaluationContext:
    """Immutable input to invariant evaluation (Objective 2). Carries
    the ``EvidenceCollection`` to evaluate plus identity/provenance
    metadata for the evaluation run itself -- never repository state,
    never a live handle to anything that could be re-queried (that
    would reintroduce Git/filesystem/subprocess access this module must
    not have)."""

    evidence: EvidenceCollection
    evaluation_id: str
    evaluation_timestamp: str
    repository_snapshot_reference: str
    evaluation_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, EvidenceCollection):
            raise ValueError(
                f"EvaluationContext evidence must be an EvidenceCollection, got {self.evidence!r}"
            )
        for field_name in (
            "evaluation_id", "evaluation_timestamp",
            "repository_snapshot_reference", "evaluation_version",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"EvaluationContext {field_name} must be non-empty")


@dataclass(frozen=True)
class EvaluationResult:
    """The deterministic outcome of one evaluation run (Objective 4).

    Bucketing rule (Objective 7, "UNKNOWN evidence shall never silently
    PASS"): an invariant whose status is ``UNKNOWN`` is bucketed exactly
    as if it had ``FAIL``ed, by severity -- a ``blocking`` invariant
    that could not be evaluated lands in ``blocking_failures``, a
    ``warning`` invariant that could not be evaluated lands in
    ``warnings``. Only ``PASS``/``NOT_APPLICABLE`` results, or results
    whose invariant is declared ``informational`` severity, land in
    ``informational``. This is a bucketing convention only -- it never
    mutates the underlying ``InvariantResult.status``, which always
    still reports the true ``UNKNOWN``.

    This is not a verdict. No ``TransitionVerdict`` is produced here --
    that remains the Repository Transition Validator's sole authority.
    """

    invariant_results: tuple[InvariantResult, ...]
    summary: str
    blocking_failures: tuple[str, ...]
    warnings: tuple[str, ...]
    informational: tuple[str, ...]
    explanation_reference: tuple[EvidenceReference, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "invariant_results", tuple(self.invariant_results))
        object.__setattr__(self, "blocking_failures", tuple(self.blocking_failures))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "informational", tuple(self.informational))
        object.__setattr__(self, "explanation_reference", tuple(self.explanation_reference))

    @property
    def has_blocking_failure(self) -> bool:
        return len(self.blocking_failures) > 0


def _by_id(evidence: EvidenceCollection, evidence_id: str) -> Evidence | None:
    return evidence.by_id(evidence_id)


def _is_unknown(item: Evidence) -> bool:
    """Detects "the provider could not determine this" evidence.

    Relies solely on ``freshness`` (115D's providers always set
    ``freshness=UNKNOWN`` alongside their unavailable-sentinel
    ``observed_value``). Deliberately does NOT check
    ``observed_value == "unavailable"`` -- that string is also a valid,
    correct domain value for execution-availability evidence (execution
    genuinely being unavailable is the desired, passing state), so
    checking it here would misclassify genuine evidence as unknown.
    """
    return item.freshness == EvidenceFreshness.UNKNOWN


def _ref(item: Evidence, note: str | None = None) -> EvidenceReference:
    return EvidenceReference(evidence_id=item.evidence_id, note=note)


def _unknown_result(
    invariant_id: str, severity: str, present: tuple[Evidence, ...], explanation: str,
) -> InvariantResult:
    return InvariantResult(
        invariant_id=invariant_id,
        status=InvariantStatus.UNKNOWN,
        severity=severity,
        supporting_evidence=tuple(_ref(e) for e in present),
        conflicting_evidence=(),
        explanation=explanation,
        suggested_repair="Re-collect evidence once the underlying input becomes available.",
    )


def _not_applicable_result(invariant_id: str, severity: str, explanation: str) -> InvariantResult:
    return InvariantResult(
        invariant_id=invariant_id,
        status=InvariantStatus.NOT_APPLICABLE,
        severity=severity,
        supporting_evidence=(),
        conflicting_evidence=(),
        explanation=explanation,
        suggested_repair=None,
    )


# ═══════════════════════════════════════════════════════════════════════
# Invariant family: phase_identity_consistency
# ═══════════════════════════════════════════════════════════════════════

def evaluate_phase_identity_consistency(evidence: EvidenceCollection) -> InvariantResult:
    """Compares the Report Provider's ``E-report-002`` (canonical report
    phase_id) against the Metadata Provider's ``E-metadata-002``
    (declared metadata phase_id). Independent of
    ``repository_transition_validator.py``'s own
    ``_check_phase_identity_consistency`` (which compares
    ``RepositoryState`` fields, not Evidence)."""
    invariant_id = "phase_identity_consistency"
    severity = "blocking"
    report_id = _by_id(evidence, "E-report-002")
    metadata_id = _by_id(evidence, "E-metadata-002")
    present = tuple(e for e in (report_id, metadata_id) if e is not None)

    if not present:
        return _not_applicable_result(
            invariant_id, severity,
            "No phase identity evidence (E-report-002, E-metadata-002) present in this evaluation.",
        )
    if any(_is_unknown(e) for e in present):
        return _unknown_result(
            invariant_id, severity, present,
            "Phase identity evidence is present but unknown/unavailable.",
        )
    if report_id is not None and metadata_id is not None:
        if report_id.observed_value != metadata_id.observed_value:
            return InvariantResult(
                invariant_id=invariant_id,
                status=InvariantStatus.FAIL,
                severity=severity,
                supporting_evidence=(),
                conflicting_evidence=(_ref(report_id), _ref(metadata_id)),
                explanation=(
                    f"Disagreeing phase identity sources: report={report_id.observed_value!r}, "
                    f"metadata={metadata_id.observed_value!r}."
                ),
                suggested_repair="Reconcile the declared metadata phase_id with the canonical report phase_id.",
            )
    return InvariantResult(
        invariant_id=invariant_id,
        status=InvariantStatus.PASS,
        severity=severity,
        supporting_evidence=tuple(_ref(e) for e in present),
        conflicting_evidence=(),
        explanation="Phase identity evidence agrees (or only one source was available).",
    )


# ═══════════════════════════════════════════════════════════════════════
# Invariant family: push_state_consistency
# ═══════════════════════════════════════════════════════════════════════

def evaluate_push_state_consistency(evidence: EvidenceCollection) -> InvariantResult:
    """Compares the Git Provider's derived ``E-git-005`` pushed status
    against the Metadata Provider's declared ``E-metadata-003`` pushed
    status -- the exact conflict example from 115B's own "Conflict
    Semantics" section (declared metadata disagreeing with live git
    state). Both items are preserved as conflicting evidence when they
    disagree; this function never picks one over the other by provider
    priority (Objective 8)."""
    invariant_id = "push_state_consistency"
    severity = "blocking"
    git_pushed = _by_id(evidence, "E-git-005")
    metadata_pushed = _by_id(evidence, "E-metadata-003")
    present = tuple(e for e in (git_pushed, metadata_pushed) if e is not None)

    if not present:
        return _not_applicable_result(
            invariant_id, severity,
            "No push-state evidence (E-git-005, E-metadata-003) present in this evaluation.",
        )
    if any(_is_unknown(e) for e in present):
        return _unknown_result(
            invariant_id, severity, present,
            "Push-state evidence is present but unknown/unavailable.",
        )
    if git_pushed is not None and metadata_pushed is not None:
        git_value = str(git_pushed.observed_value)
        metadata_value = str(metadata_pushed.observed_value)
        if git_value != metadata_value:
            return InvariantResult(
                invariant_id=invariant_id,
                status=InvariantStatus.FAIL,
                severity=severity,
                supporting_evidence=(),
                conflicting_evidence=(_ref(git_pushed), _ref(metadata_pushed)),
                explanation=(
                    f"Declared push state disagrees with live push state: "
                    f"git={git_value!r}, metadata={metadata_value!r}."
                ),
                suggested_repair="Reconcile declared metadata pushed_status against live git state.",
            )
    return InvariantResult(
        invariant_id=invariant_id,
        status=InvariantStatus.PASS,
        severity=severity,
        supporting_evidence=tuple(_ref(e) for e in present),
        conflicting_evidence=(),
        explanation="Push-state evidence agrees (or only one source was available).",
    )


# ═══════════════════════════════════════════════════════════════════════
# Invariant family: metadata_consistency
# ═══════════════════════════════════════════════════════════════════════

def evaluate_metadata_consistency(evidence: EvidenceCollection) -> InvariantResult:
    """Internal self-consistency of the Metadata Provider's own
    declared fields: ``E-metadata-003`` (pushed_status) must agree with
    ``E-metadata-004`` (origin_main_head_count) -- ``pushed`` implies a
    zero count, a nonzero count implies ``not_pushed``. Independent of
    ``push_state_consistency`` above, which compares metadata against
    git, not metadata against itself."""
    invariant_id = "metadata_consistency"
    severity = "blocking"
    pushed_status = _by_id(evidence, "E-metadata-003")
    head_count = _by_id(evidence, "E-metadata-004")
    present = tuple(e for e in (pushed_status, head_count) if e is not None)

    if not present:
        return _not_applicable_result(
            invariant_id, severity,
            "No metadata push-state fields (E-metadata-003, E-metadata-004) present in this evaluation.",
        )
    if any(_is_unknown(e) for e in present):
        return _unknown_result(
            invariant_id, severity, present,
            "Metadata push-state fields are present but unknown/unavailable.",
        )
    if pushed_status is not None and head_count is not None:
        status_value = str(pushed_status.observed_value)
        count_value = head_count.observed_value
        inconsistent = (
            (status_value == "pushed" and count_value != 0)
            or (status_value == "not_pushed" and count_value == 0)
        )
        if inconsistent:
            return InvariantResult(
                invariant_id=invariant_id,
                status=InvariantStatus.FAIL,
                severity=severity,
                supporting_evidence=(),
                conflicting_evidence=(_ref(pushed_status), _ref(head_count)),
                explanation=(
                    f"Declared metadata is internally inconsistent: pushed_status="
                    f"{status_value!r}, origin_main_head_count={count_value!r}."
                ),
                suggested_repair="Correct the declared metadata's pushed_status or origin_main_head_count.",
            )
    return InvariantResult(
        invariant_id=invariant_id,
        status=InvariantStatus.PASS,
        severity=severity,
        supporting_evidence=tuple(_ref(e) for e in present),
        conflicting_evidence=(),
        explanation="Declared metadata push-state fields are internally consistent.",
    )


# ═══════════════════════════════════════════════════════════════════════
# Invariant family: report_completeness
# ═══════════════════════════════════════════════════════════════════════

def evaluate_report_completeness(evidence: EvidenceCollection) -> InvariantResult:
    """Reads the Report Provider's ``E-report-003``
    (report_completeness). ``complete`` passes; ``partial`` fails at
    ``warning`` severity; anything else (missing/empty/unrecognized)
    fails at ``blocking`` severity."""
    invariant_id = "report_completeness"
    completeness_ev = _by_id(evidence, "E-report-003")

    if completeness_ev is None:
        return _not_applicable_result(
            invariant_id, "blocking",
            "No report_completeness evidence (E-report-003) present in this evaluation.",
        )
    if _is_unknown(completeness_ev):
        return _unknown_result(
            invariant_id, "blocking", (completeness_ev,),
            "report_completeness evidence is present but unknown/unavailable.",
        )
    value = str(completeness_ev.observed_value)
    if value == "complete":
        return InvariantResult(
            invariant_id=invariant_id,
            status=InvariantStatus.PASS,
            severity="blocking",
            supporting_evidence=(_ref(completeness_ev),),
            conflicting_evidence=(),
            explanation="report_completeness is 'complete'.",
        )
    if value == "partial":
        return InvariantResult(
            invariant_id=invariant_id,
            status=InvariantStatus.FAIL,
            severity="warning",
            supporting_evidence=(_ref(completeness_ev),),
            conflicting_evidence=(),
            explanation="report_completeness is 'partial'.",
            suggested_repair="Repair the partial phase-completion report before canonical promotion.",
        )
    return InvariantResult(
        invariant_id=invariant_id,
        status=InvariantStatus.FAIL,
        severity="blocking",
        supporting_evidence=(_ref(completeness_ev),),
        conflicting_evidence=(),
        explanation=f"report_completeness is {value!r} (missing or unrecognized evidence).",
        suggested_repair="Produce a canonical phase report with report_completeness set to 'complete'.",
    )


# ═══════════════════════════════════════════════════════════════════════
# Invariant family: runtime_execution_unavailable
# ═══════════════════════════════════════════════════════════════════════

def evaluate_runtime_execution_unavailable(evidence: EvidenceCollection) -> InvariantResult:
    """Reads the Runtime Provider's ``E-runtime-002``
    (execution_availability). Independent of
    ``repository_transition_validator.py``'s own
    ``_check_no_execution_availability_unless_contracted`` (which reads
    ``RepositoryState.execution_availability`` directly, not Evidence)."""
    invariant_id = "runtime_execution_unavailable"
    severity = "blocking"
    exec_ev = _by_id(evidence, "E-runtime-002")

    if exec_ev is None:
        return _not_applicable_result(
            invariant_id, severity,
            "No execution_availability evidence (E-runtime-002) present in this evaluation.",
        )
    if _is_unknown(exec_ev):
        return _unknown_result(
            invariant_id, severity, (exec_ev,),
            "execution_availability evidence is present but unknown/unavailable.",
        )
    value = str(exec_ev.observed_value)
    if value == "unavailable":
        return InvariantResult(
            invariant_id=invariant_id,
            status=InvariantStatus.PASS,
            severity=severity,
            supporting_evidence=(_ref(exec_ev),),
            conflicting_evidence=(),
            explanation="execution_availability is 'unavailable', as required.",
        )
    return InvariantResult(
        invariant_id=invariant_id,
        status=InvariantStatus.FAIL,
        severity=severity,
        supporting_evidence=(_ref(exec_ev),),
        conflicting_evidence=(),
        explanation=f"execution_availability is {value!r}, expected 'unavailable'.",
        suggested_repair="No execution-enablement contract exists; execution_availability must remain 'unavailable'.",
    )


# ═══════════════════════════════════════════════════════════════════════
# Invariant family: canonical_promotion_eligibility
# ═══════════════════════════════════════════════════════════════════════

def evaluate_canonical_promotion_eligibility(evidence: EvidenceCollection) -> InvariantResult:
    """Eligibility for canonical promotion, evaluated purely from
    Report Provider evidence: ``E-report-003`` (report_completeness)
    must be ``complete`` and ``E-report-005`` (derived report
    consistency) must be ``consistent``. Independent of
    ``repository_transition_validator.py``'s own
    ``_check_canonical_promotion_eligibility`` (which compares
    ``ArtifactState``/``ExpectedTargetState``, concepts this
    evidence-only module does not have)."""
    invariant_id = "canonical_promotion_eligibility"
    severity = "blocking"
    completeness_ev = _by_id(evidence, "E-report-003")
    consistency_ev = _by_id(evidence, "E-report-005")
    present = tuple(e for e in (completeness_ev, consistency_ev) if e is not None)

    if len(present) < 2:
        return _not_applicable_result(
            invariant_id, severity,
            "Both report completeness (E-report-003) and consistency (E-report-005) evidence "
            "are required to jointly evaluate this invariant; at least one is not present in "
            "this evaluation.",
        )
    if any(_is_unknown(e) for e in present):
        return _unknown_result(
            invariant_id, severity, present,
            "Report completeness/consistency evidence is present but unknown/unavailable.",
        )

    completeness_ok = completeness_ev is not None and completeness_ev.observed_value == "complete"
    consistency_ok = consistency_ev is not None and consistency_ev.observed_value == "consistent"

    if completeness_ok and consistency_ok:
        return InvariantResult(
            invariant_id=invariant_id,
            status=InvariantStatus.PASS,
            severity=severity,
            supporting_evidence=tuple(_ref(e) for e in present),
            conflicting_evidence=(),
            explanation="Report is complete and consistent; eligible for canonical promotion.",
        )
    return InvariantResult(
        invariant_id=invariant_id,
        status=InvariantStatus.FAIL,
        severity=severity,
        supporting_evidence=tuple(_ref(e) for e in present),
        conflicting_evidence=(),
        explanation=(
            f"Not eligible for canonical promotion: "
            f"completeness={(completeness_ev.observed_value if completeness_ev else 'missing')!r}, "
            f"consistency={(consistency_ev.observed_value if consistency_ev else 'missing')!r}."
        ),
        suggested_repair="Resolve report completeness/consistency before canonical promotion.",
    )


#: The six deterministic, evidence-only invariant families this
#: prototype implements (Objective 5), in evaluation order.
INVARIANT_EVALUATORS: tuple[Callable[[EvidenceCollection], InvariantResult], ...] = (
    evaluate_phase_identity_consistency,
    evaluate_push_state_consistency,
    evaluate_metadata_consistency,
    evaluate_report_completeness,
    evaluate_runtime_execution_unavailable,
    evaluate_canonical_promotion_eligibility,
)


def evaluate(context: EvaluationContext) -> EvaluationResult:
    """Run all six invariant families against ``context.evidence`` and
    aggregate into one deterministic ``EvaluationResult``. Produces no
    ``TransitionVerdict`` -- that remains the Repository Transition
    Validator's sole authority (Objective 9)."""
    results = tuple(evaluator(context.evidence) for evaluator in INVARIANT_EVALUATORS)

    blocking_failures: list[str] = []
    warnings: list[str] = []
    informational: list[str] = []
    all_refs: list[EvidenceReference] = []

    for result in results:
        all_refs.extend(result.all_referenced_evidence)
        elevated = result.status in (InvariantStatus.FAIL, InvariantStatus.UNKNOWN)
        if elevated and result.severity == "blocking":
            blocking_failures.append(result.invariant_id)
        elif elevated and result.severity == "warning":
            warnings.append(result.invariant_id)
        else:
            informational.append(result.invariant_id)

    pass_count = sum(1 for r in results if r.status == InvariantStatus.PASS)
    fail_count = sum(1 for r in results if r.status == InvariantStatus.FAIL)
    unknown_count = sum(1 for r in results if r.status == InvariantStatus.UNKNOWN)
    not_applicable_count = sum(1 for r in results if r.status == InvariantStatus.NOT_APPLICABLE)
    summary = (
        f"{len(results)} invariants evaluated: {pass_count} pass, {fail_count} fail, "
        f"{unknown_count} unknown, {not_applicable_count} not_applicable."
    )

    # Deduplicate evidence references by evidence_id, preserving first occurrence order.
    seen_ids: set[str] = set()
    deduped_refs: list[EvidenceReference] = []
    for ref in all_refs:
        if ref.evidence_id not in seen_ids:
            seen_ids.add(ref.evidence_id)
            deduped_refs.append(ref)

    return EvaluationResult(
        invariant_results=results,
        summary=summary,
        blocking_failures=tuple(blocking_failures),
        warnings=tuple(warnings),
        informational=tuple(informational),
        explanation_reference=tuple(deduped_refs),
    )
