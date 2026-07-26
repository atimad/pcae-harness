"""Workflow Orchestrator (IWC-001 v1.1, Phase 143O).

The sole production owner of workflow sequencing, component invocation
order, and orchestration state for a single Decision Session (this
phase's governing prompt, "Architectural Ownership": "Session Coordinator
shall become the sole owner of ... workflow sequencing, component
invocation order, lifecycle orchestration, session progression,
orchestration state"). ``SessionCoordinator``
(``pcae.interactive_workflow.session.coordinator``) satisfies that
ownership by composing this module rather than inlining sequencing logic
into itself -- see that module's own docstring and this phase's report,
§0 ("Judgment call"), for why composition rather than a monolithic
rewrite of ``SessionCoordinator`` was chosen.

``WorkflowOrchestrator`` invokes only existing infrastructure's own
public methods -- one call per stage, never a reimplementation of the
callee's logic (this phase's governing prompt, "Workflow Sequencing": "The
coordinator shall invoke only existing infrastructure. No new business
rules."). It never determines transition legality, never validates
evidence, never evaluates a clarification, never generates a Preview
Digest directly, never serializes audit content, and never performs
publication -- those methods do not exist on this class ("Responsibility
Preservation").

Constructed with all six 143K-143N/143L collaborators via constructor
injection (mirrors ``SessionCoordinator.__init__``'s own
``SessionRepository`` injection, and ``ConfirmationController``'s
``PreviewBuilder`` injection): an ``EvidenceCoordinator``, a
``ClarificationController``, an ``AuditRecorder``, a ``PreviewBuilder``, a
``ConfirmationController``, and a ``TransitionEngine``, all scoped (where
applicable) to the same session identifier. No component is looked up
from a registry or constructed by this class itself.

This orchestrator never calls another component laterally on this
class's behalf beyond the one call each stage method makes into its own
named collaborator -- e.g. it never asks the Evidence Coordinator to
validate a Preview, and never asks the Preview Builder to register a
clarification. All orchestration flows through this class's own stage
methods, in the fixed order ``pcae.interactive_workflow.orchestration.
models.STAGE_ORDER`` defines.

Phase 145G.1 adds one narrow, additive constructor parameter,
``initial_state`` (default ``None``, fully backward compatible): it lets
a caller resume an orchestrator from an already-persisted
``OrchestrationState`` instead of always starting fresh at
``SessionInitialization``. This is bookkeeping-resumption only -- it does
not change stage sequencing rules, does not skip a legality check, and
does not let a caller fabricate progress: ``OrchestrationState.__post_init__``
still enforces that ``completed_stages`` is a valid, gapless, ordered
prefix of ``STAGE_ORDER``, exactly as it always has.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Optional, Tuple

from pcae.interactive_workflow.audit.recorder import AuditRecorder
from pcae.interactive_workflow.clarification.controller import ClarificationController
from pcae.interactive_workflow.clarification.models import Clarification
from pcae.interactive_workflow.confirmation.controller import ConfirmationController
from pcae.interactive_workflow.confirmation.models import ConfirmationRequest, ConfirmationResponse
from pcae.interactive_workflow.errors import (
    InvalidWorkflowSequenceError,
    MissingWorkflowComponentError,
    WorkflowCompositionError,
    WorkflowInitializationError,
)
from pcae.interactive_workflow.evidence.coordinator import EvidenceCoordinator
from pcae.interactive_workflow.models.session import Session
from pcae.interactive_workflow.orchestration.models import OrchestrationStage, OrchestrationState
from pcae.interactive_workflow.preview.builder import PreviewBuilder
from pcae.interactive_workflow.preview.models import Preview
from pcae.interactive_workflow.session.identity import validate_session_id
from pcae.interactive_workflow.state_machine.engine import TransitionEngine


def _require_type(label: str, value: object, expected_type: type) -> None:
    if value is None or not isinstance(value, expected_type):
        raise MissingWorkflowComponentError(
            f"WorkflowOrchestrator requires a {expected_type.__name__!r} for "
            f"{label!r}, got {value!r}."
        )


def _require_same_session(label: str, component_session_id: str, session_id: str) -> None:
    if component_session_id != session_id:
        raise WorkflowCompositionError(
            f"{label} is scoped to session {component_session_id!r}, which does not "
            f"match this orchestrator's session {session_id!r}. One-owner-per-"
            "responsibility composition requires every injected collaborator to be "
            "scoped to the same Decision Session."
        )


class WorkflowOrchestrator:
    """Drives the eight-stage Interactive Workflow orchestration
    sequence for exactly one Decision Session, by delegating each stage
    to exactly one existing collaborator's own public method."""

    def __init__(
        self,
        session_id: str,
        evidence_coordinator: EvidenceCoordinator,
        clarification_controller: ClarificationController,
        audit_recorder: AuditRecorder,
        preview_builder: PreviewBuilder,
        confirmation_controller: ConfirmationController,
        transition_engine: TransitionEngine,
        initial_state: Optional[OrchestrationState] = None,
    ) -> None:
        self._session_id = validate_session_id(session_id)

        _require_type("evidence_coordinator", evidence_coordinator, EvidenceCoordinator)
        _require_type("clarification_controller", clarification_controller, ClarificationController)
        _require_type("audit_recorder", audit_recorder, AuditRecorder)
        _require_type("preview_builder", preview_builder, PreviewBuilder)
        _require_type("confirmation_controller", confirmation_controller, ConfirmationController)
        _require_type("transition_engine", transition_engine, TransitionEngine)

        _require_same_session(
            "EvidenceCoordinator", evidence_coordinator.session_id, self._session_id
        )
        _require_same_session(
            "ClarificationController", clarification_controller.session_id, self._session_id
        )
        _require_same_session("AuditRecorder", audit_recorder.session_id, self._session_id)
        _require_same_session(
            "ConfirmationController", confirmation_controller.session_id, self._session_id
        )

        self._evidence_coordinator = evidence_coordinator
        self._clarification_controller = clarification_controller
        self._audit_recorder = audit_recorder
        self._preview_builder = preview_builder
        self._confirmation_controller = confirmation_controller
        # Stored for structural composition only (this phase's governing
        # prompt requires 143L integration); never invoked by this class
        # -- transition legality determination remains the Transition
        # Engine's sole responsibility, never re-implemented or called
        # here ("Responsibility Preservation": "The Session Coordinator
        # shall never: determine transition legality").
        self._transition_engine = transition_engine

        if initial_state is not None:
            _require_same_session("initial_state", initial_state.session_id, self._session_id)
            self._state = initial_state
        else:
            self._state = OrchestrationState(session_id=self._session_id)

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def state(self) -> OrchestrationState:
        """The current, immutable orchestration sequencing state."""

        return self._state

    def _require_next(self, stage: OrchestrationStage) -> None:
        """Raise ``InvalidWorkflowSequenceError`` unless ``stage`` is the
        single legal next stage, checked *before* this class delegates to
        any collaborator -- so an out-of-order or duplicate stage
        invocation never reaches, and never causes a side effect on, the
        underlying component (fail closed on sequencing before any
        mutation, not merely before this orchestrator's own bookkeeping
        update)."""

        if stage != self._state.next_stage:
            raise InvalidWorkflowSequenceError(
                f"Stage {stage!r} is not the next legal orchestration stage for "
                f"session {self._session_id!r}; expected {self._state.next_stage!r}. "
                f"Already completed: {self._state.completed_stages!r}."
            )

    def _advance(self, stage: OrchestrationStage) -> None:
        self._state = self._state.with_stage_completed(stage)

    def stage_session_initialization(self, session: Session) -> OrchestrationState:
        """Mark the Session Initialization stage complete.

        Raises ``WorkflowInitializationError`` if ``session.session_id``
        does not match this orchestrator's own scope. Performs no
        session creation, load, or persistence itself -- those remain
        ``SessionCoordinator``'s own responsibility (Phase 143K); this
        stage only records that an already-initialized session has
        entered orchestration.
        """

        self._require_next(OrchestrationStage.SESSION_INITIALIZATION)
        if session.session_id != self._session_id:
            raise WorkflowInitializationError(
                f"Session {session.session_id!r} does not match this orchestrator's "
                f"scope {self._session_id!r}."
            )
        self._advance(OrchestrationStage.SESSION_INITIALIZATION)
        return self._state

    def stage_evidence_availability(
        self, declared_evidence_ids: Iterable[str]
    ) -> Tuple[str, ...]:
        """Mark the Evidence Availability stage complete.

        Delegates entirely to ``EvidenceCoordinator.report_missing`` --
        returns the declared evidence identifiers not yet registered.
        Performs no evidence validation, scoring, or registration itself.
        """

        self._require_next(OrchestrationStage.EVIDENCE_AVAILABILITY)
        missing = self._evidence_coordinator.report_missing(declared_evidence_ids)
        self._advance(OrchestrationStage.EVIDENCE_AVAILABILITY)
        return missing

    def stage_clarification_lifecycle(self) -> Tuple[Clarification, ...]:
        """Mark the Clarification Lifecycle stage complete.

        Delegates entirely to ``ClarificationController.history`` --
        returns every registered clarification exchange, verbatim.
        Performs no clarification evaluation, tagging, or registration
        itself.
        """

        self._require_next(OrchestrationStage.CLARIFICATION_LIFECYCLE)
        history = self._clarification_controller.history()
        self._advance(OrchestrationStage.CLARIFICATION_LIFECYCLE)
        return history

    def stage_preview_construction(
        self,
        preview_id: str,
        preview_timestamp: str,
        transition_sequence_number: int,
        evidence_refs: Iterable[str] = (),
        clarification_refs: Iterable[str] = (),
        audit_refs: Iterable[str] = (),
        transition_summary: str = "",
        rendered_content: str = "",
        metadata: Optional[Mapping[str, object]] = None,
    ) -> Tuple[Preview, str]:
        """Mark the Preview Construction stage complete.

        Delegates entirely to ``PreviewBuilder.build``. Performs no
        Preview Digest generation itself -- the returned digest is
        exactly the one ``PreviewBuilder.compute_digest`` produced.
        """

        self._require_next(OrchestrationStage.PREVIEW_CONSTRUCTION)
        preview, preview_digest = self._preview_builder.build(
            preview_id=preview_id,
            session_id=self._session_id,
            preview_timestamp=preview_timestamp,
            transition_sequence_number=transition_sequence_number,
            evidence_refs=evidence_refs,
            clarification_refs=clarification_refs,
            audit_refs=audit_refs,
            transition_summary=transition_summary,
            rendered_content=rendered_content,
            metadata=metadata,
        )
        self._advance(OrchestrationStage.PREVIEW_CONSTRUCTION)
        return preview, preview_digest

    def stage_preview_validation(
        self,
        preview: Preview,
        preview_digest: Optional[str] = None,
        required_evidence_refs: Iterable[str] = (),
        required_clarification_refs: Iterable[str] = (),
        required_audit_refs: Iterable[str] = (),
    ) -> None:
        """Mark the Preview Validation stage complete.

        Delegates entirely to ``PreviewBuilder.validate``, which raises
        (``InvalidPreviewError``/``PreviewDigestMismatchError``) before
        this stage is ever marked complete -- a validation failure never
        silently advances orchestration.
        """

        self._require_next(OrchestrationStage.PREVIEW_VALIDATION)
        self._preview_builder.validate(
            preview,
            preview_digest=preview_digest,
            required_evidence_refs=required_evidence_refs,
            required_clarification_refs=required_clarification_refs,
            required_audit_refs=required_audit_refs,
        )
        self._advance(OrchestrationStage.PREVIEW_VALIDATION)

    def stage_confirmation_request(
        self, request: ConfirmationRequest
    ) -> ConfirmationRequest:
        """Mark the Confirmation Request stage complete.

        Delegates entirely to ``ConfirmationController.register_request``.
        """

        self._require_next(OrchestrationStage.CONFIRMATION_REQUEST)
        registered = self._confirmation_controller.register_request(request)
        self._advance(OrchestrationStage.CONFIRMATION_REQUEST)
        return registered

    def stage_confirmation_validation(
        self,
        request_id: str,
        response: ConfirmationResponse,
        preview: Preview,
        current_transition_sequence_number: int,
    ) -> ConfirmationResponse:
        """Mark the Confirmation Validation stage complete.

        Delegates entirely to ``ConfirmationController.register_response``,
        which itself delegates staleness/replay/digest checks to
        ``PreviewBuilder`` and its own state -- this stage never repeats
        or bypasses any of those checks; a raised
        ``PreviewDigestMismatchError``/``StalePreviewError``/
        ``ReplayDetectedError``/``DuplicateConfirmationError``/
        ``InvalidConfirmationError`` propagates unchanged, and this stage
        is never marked complete when one is raised.
        """

        self._require_next(OrchestrationStage.CONFIRMATION_VALIDATION)
        accepted = self._confirmation_controller.register_response(
            request_id, response, preview, current_transition_sequence_number
        )
        self._advance(OrchestrationStage.CONFIRMATION_VALIDATION)
        return accepted

    def stage_terminal_completion(self, session: Session) -> Session:
        """Mark the Terminal Workflow Completion stage complete.

        Raises ``InvalidWorkflowSequenceError`` (via ``OrchestrationState.
        with_stage_completed``, since this must be the eighth and final
        stage) if the prior seven stages are not already complete, or if
        ``session`` is not scoped to this orchestrator or is not itself
        in a terminal ``SessionState`` (IWC-001 v1.1 §4.4). Performs no
        transition itself -- the session must already be terminal,
        exactly as this phase's Session Coordinator/Transition Engine
        boundary requires.
        """

        self._require_next(OrchestrationStage.TERMINAL_COMPLETION)
        if session.session_id != self._session_id or not session.is_terminal():
            raise InvalidWorkflowSequenceError(
                f"Session {session.session_id!r} (state "
                f"{getattr(session, 'session_state', None)!r}) is not a terminal "
                f"session scoped to orchestrator session {self._session_id!r}; "
                "Terminal Workflow Completion requires an already-terminal session."
            )
        self._advance(OrchestrationStage.TERMINAL_COMPLETION)
        return session


__all__ = ["WorkflowOrchestrator"]
