"""Orchestration sequencing bookkeeping model (Phase 143O).

``OrchestrationState`` records which of the Interactive Workflow's eight
fixed orchestration stages (this phase's governing prompt, "Workflow
Sequencing") have been completed for one Decision Session, and in what
order. It is deliberately a distinct, minimal type from
``pcae.interactive_workflow.models.session.SessionState``: session state
is the ten-state IWC-001 v1.1 §4.4 lifecycle a session itself occupies
(``Created``, ``EvidenceReady``, ... ``Confirmed``); orchestration stage
is purely "how far has this phase's own sequencing progressed through
the fixed eight-step order," a bookkeeping concern this phase introduces
to satisfy its own "no missing components, no invalid sequencing, no
duplicate orchestration" validation requirement. Nothing here re-derives,
duplicates, or overrides ``SessionState``, and nothing here is a second
lifecycle -- there is exactly one canonical session lifecycle
(``SessionState``), and this model never substitutes for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple

from pcae.interactive_workflow.errors import InvalidWorkflowSequenceError
from pcae.interactive_workflow.session.identity import validate_session_id

ORCHESTRATION_SCHEMA_VERSION = "interactive-workflow-orchestration/0.1"


class OrchestrationStage(str, Enum):
    """The eight fixed Interactive Workflow orchestration stages, in the
    single order this phase's governing prompt names them ("Workflow
    Sequencing"). No stage may be skipped, reordered, or repeated."""

    SESSION_INITIALIZATION = "SessionInitialization"
    EVIDENCE_AVAILABILITY = "EvidenceAvailability"
    CLARIFICATION_LIFECYCLE = "ClarificationLifecycle"
    PREVIEW_CONSTRUCTION = "PreviewConstruction"
    PREVIEW_VALIDATION = "PreviewValidation"
    CONFIRMATION_REQUEST = "ConfirmationRequest"
    CONFIRMATION_VALIDATION = "ConfirmationValidation"
    TERMINAL_COMPLETION = "TerminalCompletion"


STAGE_ORDER: Tuple[OrchestrationStage, ...] = (
    OrchestrationStage.SESSION_INITIALIZATION,
    OrchestrationStage.EVIDENCE_AVAILABILITY,
    OrchestrationStage.CLARIFICATION_LIFECYCLE,
    OrchestrationStage.PREVIEW_CONSTRUCTION,
    OrchestrationStage.PREVIEW_VALIDATION,
    OrchestrationStage.CONFIRMATION_REQUEST,
    OrchestrationStage.CONFIRMATION_VALIDATION,
    OrchestrationStage.TERMINAL_COMPLETION,
)
"""The single canonical stage order. ``OrchestrationState`` validates
every transition against this tuple; nothing in this package ever
consults a second ordering."""


@dataclass(frozen=True)
class OrchestrationState:
    """Immutable record of orchestration progress for one Decision
    Session. ``completed_stages`` is always a strict, gapless, ordered
    prefix of ``STAGE_ORDER`` -- constructed only via ``with_stage_
    completed``, which is the sole mutation path (returns a new
    instance; the original is untouched, matching ``Session.with_state``
    and ``Clarification.with_response``'s precedent).
    """

    session_id: str
    completed_stages: Tuple[OrchestrationStage, ...] = field(default_factory=tuple)
    schema_version: str = ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_session_id(self.session_id)
        if not self.schema_version:
            raise ValueError("OrchestrationState.schema_version must be non-empty.")
        completed = tuple(self.completed_stages)
        expected_prefix = STAGE_ORDER[: len(completed)]
        if completed != expected_prefix:
            raise InvalidWorkflowSequenceError(
                f"OrchestrationState.completed_stages {completed!r} is not a valid, "
                f"gapless, ordered prefix of the fixed stage order {STAGE_ORDER!r}."
            )
        object.__setattr__(self, "completed_stages", completed)

    @property
    def next_stage(self):
        """The single stage that may legally be completed next, or
        ``None`` if every stage is already complete."""

        if len(self.completed_stages) == len(STAGE_ORDER):
            return None
        return STAGE_ORDER[len(self.completed_stages)]

    def is_complete(self) -> bool:
        return self.completed_stages == STAGE_ORDER

    def with_stage_completed(self, stage: OrchestrationStage) -> "OrchestrationState":
        """Return a new ``OrchestrationState`` with ``stage`` marked
        complete.

        Raises ``InvalidWorkflowSequenceError`` unless ``stage`` is
        exactly ``self.next_stage`` -- rejects both out-of-order
        sequencing and duplicate (already-completed) orchestration of
        the same stage, with no distinction needed between the two: both
        are "the proposed stage is not the single legal next stage."
        """

        if stage != self.next_stage:
            raise InvalidWorkflowSequenceError(
                f"Stage {stage!r} is not the next legal orchestration stage for "
                f"session {self.session_id!r}; expected {self.next_stage!r}. "
                f"Already completed: {self.completed_stages!r}."
            )
        return OrchestrationState(
            session_id=self.session_id,
            completed_stages=self.completed_stages + (stage,),
            schema_version=self.schema_version,
        )


__all__ = [
    "ORCHESTRATION_SCHEMA_VERSION",
    "OrchestrationStage",
    "STAGE_ORDER",
    "OrchestrationState",
]
