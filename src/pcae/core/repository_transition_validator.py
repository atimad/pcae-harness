"""Phase 113U: Repository Transition Validator Prototype (Observation-Only).

Implements the interface frozen in Phase 113T
(``docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR_CONTRACT.md``): a single,
deterministic, model-agnostic function that evaluates a proposed
repository state transition against a fixed set of structural
invariants and returns one of four verdicts.

Observation-only: nothing in this module is called by ``pcae phase
complete``, ``pcae task finish --commit``, ``pcae push``, or any
notification path. It exists to be called directly -- by tests today,
by a future integration phase once this prototype is verified. Calling
it has no effect on canonical repository state; it only classifies a
transition that has already been described to it.

No field on any type in this module carries the identity of the
proposing agent. The validator evaluates repository state, never
"which model/human proposed this" -- this is what makes it
model-agnostic (113T Non-Goals; 113S Section 9).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TransitionKind(str, Enum):
    """The 12 transition kinds frozen in 113T Section 4."""

    START_TASK = "start_task"
    MODIFY_FILES = "modify_files"
    RUN_VALIDATION = "run_validation"
    COMMIT = "commit"
    FINISH_TASK = "finish_task"
    COMPLETE_PHASE = "complete_phase"
    REPORT_GENERATION = "report_generation"
    REPORT_PROMOTION = "report_promotion"
    PUSH = "push"
    NOTIFY = "notify"
    STATUS_UPDATE = "status_update"
    ROADMAP_UPDATE = "roadmap_update"


class ArtifactState(str, Enum):
    """The 6 canonical promotion states frozen in 113T Section 5.

    Only CERTIFIED may become CANONICAL.
    """

    DRAFT = "draft"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    CERTIFIED = "certified"
    CANONICAL = "canonical"


class TransitionVerdict(str, Enum):
    """The 4 verdicts frozen in 113T Section 2. No fifth value."""

    ACCEPT = "accept"
    REJECT = "reject"
    QUARANTINE = "quarantine"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


@dataclass(frozen=True)
class RepositoryState:
    """A structural snapshot of canonical repository state (113T Section 3).

    Deliberately contains no agent/model identity field: the validator
    is a pure function of repository state, not of who is proposing a
    transition.
    """

    phase_id: str | None = None
    active_task_phase_id: str | None = None
    metadata_phase_id: str | None = None
    lifecycle_current_phase_id: str | None = None
    lifecycle_current_phase_completed: bool = False
    commits: tuple[str, ...] = ()
    files_changed: int = 0
    test_results: dict[str, Any] = field(default_factory=dict)
    recommended_next_phase: str = ""
    report_completeness: str = ""
    pushed_status: str = ""
    origin_main_head_count: int = 0
    notification_already_dispatched: bool = False
    notification_transport_enabled: bool = False
    artifact_state: ArtifactState = ArtifactState.DRAFT
    execution_availability: str = "unavailable"


@dataclass(frozen=True)
class ProposedTransition:
    """A requested repository state transition (113T Section 4).

    ``payload`` is an open bag for transition-specific data. It may
    contain anything a caller likes (including, harmlessly, an "agent"
    key for its own bookkeeping) -- ``validate_transition`` never reads
    an identity field from it, by construction.
    """

    kind: TransitionKind
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExpectedTargetState:
    """What the caller expects repository state to become if accepted."""

    artifact_state: ArtifactState = ArtifactState.DRAFT
    phase_id: str | None = None


@dataclass(frozen=True)
class TransitionInvariant:
    """One entry from the frozen Invariant Contract (113T Section 8)."""

    name: str
    classification: str  # mandatory | derived | optional | future
    force: str  # blocking | warning | informational


@dataclass(frozen=True)
class InvariantViolation:
    invariant: str
    reason: str
    force: str  # blocking | warning | informational


@dataclass(frozen=True)
class TransitionResult:
    verdict: TransitionVerdict
    violations: tuple[InvariantViolation, ...] = ()

    @property
    def accepted(self) -> bool:
        return self.verdict == TransitionVerdict.ACCEPT


#: The structural invariant families implemented by this prototype.
#: This is a subset of 113T Section 8's full frozen list -- only the
#: ones this observation-only prototype can evaluate purely from
#: ``RepositoryState`` without any live filesystem/git access are
#: implemented here.
STRUCTURAL_INVARIANTS: tuple[TransitionInvariant, ...] = (
    TransitionInvariant("phase_identity_consistency", "mandatory", "blocking"),
    TransitionInvariant("metadata_consistency", "mandatory", "blocking"),
    TransitionInvariant("report_completeness", "mandatory", "blocking"),
    TransitionInvariant("recommended_next_phase_presence", "mandatory", "blocking"),
    TransitionInvariant("canonical_promotion_eligibility", "mandatory", "blocking"),
    TransitionInvariant("notification_eligibility", "mandatory", "blocking"),
    TransitionInvariant("no_execution_availability_unless_contracted", "mandatory", "blocking"),
)

_COMPLETENESS_VALUES_MISSING = {"", "missing", "unknown"}
_COMPLETENESS_VALUES_PARTIAL = {"partial"}


def _check_phase_identity_consistency(state: RepositoryState) -> InvariantViolation | None:
    """113T Section 3/8: phase identity must agree across every source
    that can independently derive one. A lifecycle-context phase_id is
    only a candidate source if PROJECT_STATUS.md hasn't marked it
    completed (mirrors ``resolve_canonical_phase_identity``'s own rule)."""
    sources = {s for s in (state.active_task_phase_id, state.metadata_phase_id) if s}
    if state.lifecycle_current_phase_id and not state.lifecycle_current_phase_completed:
        sources.add(state.lifecycle_current_phase_id)
    if len(sources) > 1:
        return InvariantViolation(
            "phase_identity_consistency",
            f"Disagreeing phase identity sources: {sorted(sources)}",
            "blocking",
        )
    return None


def _check_metadata_consistency(state: RepositoryState, target: ExpectedTargetState) -> InvariantViolation | None:
    """113T Section 6: the metadata-declared phase_id must match the
    target phase_id being proposed -- closes the 113S asymmetry class
    of defect (metadata silently disagreeing with resolved identity)."""
    if target.phase_id is not None and state.metadata_phase_id is not None:
        if state.metadata_phase_id != target.phase_id:
            return InvariantViolation(
                "metadata_consistency",
                f"metadata phase_id {state.metadata_phase_id!r} does not match "
                f"proposed target phase_id {target.phase_id!r}",
                "blocking",
            )
    return None


def _check_report_completeness(state: RepositoryState) -> InvariantViolation | None:
    """113T Section 9: missing evidence resolves to Reject; partial
    evidence resolves to Quarantine (handled by caller via force/reason)."""
    if state.report_completeness in _COMPLETENESS_VALUES_MISSING:
        return InvariantViolation(
            "report_completeness",
            f"report_completeness is {state.report_completeness!r} (missing evidence)",
            "blocking",
        )
    if state.report_completeness in _COMPLETENESS_VALUES_PARTIAL:
        return InvariantViolation(
            "report_completeness",
            "report_completeness is 'partial' (partial validation)",
            "warning",
        )
    if not state.test_results and not state.commits:
        return InvariantViolation(
            "report_completeness",
            "no test_results and no commits recorded (missing evidence)",
            "blocking",
        )
    return None


def _check_recommended_next_phase_presence(state: RepositoryState) -> InvariantViolation | None:
    """113T Section 8: mandatory, blocking -- mirrors the exact 113D
    defect (empty structured recommended_next_phase field)."""
    if not state.recommended_next_phase.strip():
        return InvariantViolation(
            "recommended_next_phase_presence",
            "recommended_next_phase is empty",
            "blocking",
        )
    return None


def _check_canonical_promotion_eligibility(
    state: RepositoryState, target: ExpectedTargetState
) -> InvariantViolation | None:
    """113T Section 5: only Certified may become Canonical."""
    if target.artifact_state == ArtifactState.CANONICAL and state.artifact_state != ArtifactState.CERTIFIED:
        return InvariantViolation(
            "canonical_promotion_eligibility",
            f"target state is Canonical but current artifact_state is "
            f"{state.artifact_state.value!r}, not Certified",
            "blocking",
        )
    return None


def notification_eligible(state: RepositoryState) -> tuple[bool, tuple[str, ...]]:
    """113T Section 7 / 113S Section 7: notification eligibility --
    finalized, certified, push clean, not already dispatched, transport
    enabled. All five required simultaneously. Returns
    ``(eligible, reasons_if_not)``.
    """
    reasons: list[str] = []
    finalized = state.artifact_state in (ArtifactState.CERTIFIED, ArtifactState.CANONICAL)
    if not finalized:
        reasons.append("not finalized (artifact_state is not Certified/Canonical)")
    certified = state.artifact_state in (ArtifactState.CERTIFIED, ArtifactState.CANONICAL)
    if not certified:
        reasons.append("report is not Certified")
    push_clean = state.origin_main_head_count == 0
    if not push_clean:
        reasons.append(f"push state not clean (origin_main_head_count={state.origin_main_head_count})")
    if state.notification_already_dispatched:
        reasons.append("notification already dispatched for this phase")
    if not state.notification_transport_enabled:
        reasons.append("notification transport not configured/enabled")
    return (len(reasons) == 0, tuple(reasons))


def _check_notification_eligibility(
    state: RepositoryState, transition: ProposedTransition
) -> InvariantViolation | None:
    if transition.kind != TransitionKind.NOTIFY:
        return None
    eligible, reasons = notification_eligible(state)
    if not eligible:
        return InvariantViolation(
            "notification_eligibility",
            "; ".join(reasons),
            "blocking",
        )
    return None


def _check_no_execution_availability_unless_contracted(state: RepositoryState) -> InvariantViolation | None:
    """113T Section 8: mandatory, blocking. No future execution-enablement
    contract exists yet, so any state claiming execution is available
    is a violation, unconditionally."""
    if state.execution_availability != "unavailable":
        return InvariantViolation(
            "no_execution_availability_unless_contracted",
            f"execution_availability is {state.execution_availability!r}, "
            "expected 'unavailable' (no execution-enablement contract exists)",
            "blocking",
        )
    return None


def validate_transition(
    current_state: RepositoryState,
    proposed_transition: ProposedTransition,
    expected_target_state: ExpectedTargetState,
    invariants: tuple[TransitionInvariant, ...] = STRUCTURAL_INVARIANTS,
) -> TransitionResult:
    """Evaluate a proposed repository state transition.

    Pure function: same inputs always produce the same
    :class:`TransitionResult`. Contains no branch on any agent/model
    identity -- there is no such field on any input type.

    Maps to a verdict per the Failure Contract (113T Section 9):
    any blocking violation on identity/metadata/canonical-promotion/
    notification/execution-availability rejects; a report-completeness
    violation classified as a warning (partial validation) quarantines
    instead of rejecting; no violations accepts.
    """
    checks = (
        _check_phase_identity_consistency(current_state),
        _check_metadata_consistency(current_state, expected_target_state),
        _check_report_completeness(current_state),
        _check_recommended_next_phase_presence(current_state),
        _check_canonical_promotion_eligibility(current_state, expected_target_state),
        _check_notification_eligibility(current_state, proposed_transition),
        _check_no_execution_availability_unless_contracted(current_state),
    )
    violations = tuple(v for v in checks if v is not None)

    if not violations:
        return TransitionResult(verdict=TransitionVerdict.ACCEPT, violations=())

    blocking = tuple(v for v in violations if v.force == "blocking")
    if blocking:
        return TransitionResult(verdict=TransitionVerdict.REJECT, violations=violations)

    # Only non-blocking (warning-classified, e.g. partial report
    # completeness) violations remain -- quarantine, never reject.
    return TransitionResult(verdict=TransitionVerdict.QUARANTINE, violations=violations)


def promotion_allowed(current: ArtifactState, target: ArtifactState) -> bool:
    """113T Section 5: only Certified may become Canonical. All other
    same-state or non-canonical transitions are structurally allowed
    by this helper; ``validate_transition`` is the authority for
    whether a given transition should actually occur."""
    if target == ArtifactState.CANONICAL:
        return current == ArtifactState.CERTIFIED
    return True
