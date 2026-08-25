"""Session Coordinator (Phase 143K skeleton; Phase 143J §4/§5.1; Phase
143O orchestration integration).

Responsibilities: create a session object, load a persisted session,
persist a session, validate session state, expose lifecycle hooks, and
(as of Phase 143O) assemble and delegate to a
``pcae.interactive_workflow.orchestration.coordinator.WorkflowOrchestrator``
-- satisfying this phase's "Session Coordinator shall become the sole
owner of ... workflow sequencing, component invocation order, lifecycle
orchestration, session progression, orchestration state" by composing the
dedicated orchestration module rather than inlining sequencing logic into
this file (see this class's own docstring below and Phase 143O's report
§0, "Judgment call: composition over inlining"). Dependencies
(``SessionRepository``) are supplied via constructor injection -- no
module-level singleton, no global registry.

Explicitly not this class's responsibility, now or ever (Phase 143J §4
Responsibility Matrix, "Prohibited" column): determining transition
legality, validating evidence, evaluating clarification, generating a
Preview Digest directly, serializing audit content, creating a CHGR, or
performing publication (this phase's governing prompt, "Responsibility
Preservation"). Methods for those concerns are not merely unimplemented
-- they do not exist on this class. ``perform_publication`` remains a
permanent ``NotImplementedError`` (see its own docstring): IWC-REQ-171
leaves Publication Handoff *execution* ownership an explicitly open
question for a future, separately governed phase, and Phase 143O's own
governing prompt's No-Go list forbids this phase from performing
publication -- so there is no scope under which this method could ever
legitimately return normally on this class.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable, List, Optional

from pcae.interactive_workflow.audit.recorder import AuditRecorder
from pcae.interactive_workflow.clarification.controller import ClarificationController
from pcae.interactive_workflow.confirmation.controller import ConfirmationController
from pcae.interactive_workflow.confirmation.models import ConfirmationResponse
from pcae.interactive_workflow.errors import SessionNotFoundError
from pcae.interactive_workflow.evidence.coordinator import EvidenceCoordinator
from pcae.interactive_workflow.models.session import SCHEMA_VERSION, Session, SessionState
from pcae.interactive_workflow.orchestration.coordinator import WorkflowOrchestrator
from pcae.interactive_workflow.persistence.repository import SessionRepository
from pcae.interactive_workflow.preview.builder import PreviewBuilder
from pcae.interactive_workflow.preview.models import Preview
from pcae.interactive_workflow.session.identity import generate_session_id
from pcae.interactive_workflow.state_machine.engine import TransitionEngine
from pcae.interactive_workflow.validation.invariants import (
    validate_session,
    validate_terminal_integrity,
)

LifecycleHook = Callable[[Session], None]
"""A lifecycle hook observes a session transition; it must not mutate or
replace the ``Session`` it receives, and must not raise to abort a
transition that has already been committed to the repository."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionCoordinator:
    """Owns session creation, load, persist, and state validation.

    Constructed with an explicit ``SessionRepository`` (dependency
    injection boundary, Phase 143J §16) -- this class never selects or
    constructs its own repository implementation.
    """

    def __init__(self, repository: SessionRepository) -> None:
        self._repository = repository
        self._lifecycle_hooks: List[LifecycleHook] = []

    def register_lifecycle_hook(self, hook: LifecycleHook) -> None:
        """Register an observer invoked after a successful state change.

        Registration only -- Phase 143K implements no code path that
        actually drives a transition and invokes registered hooks, since
        that is transition *execution*, deferred to Phase 143L
        (``pcae.interactive_workflow.state_machine`` transition engine).
        """

        self._lifecycle_hooks.append(hook)

    def create_session(
        self,
        owner_identity: str,
        template_ref: str,
        subject_ref: str,
    ) -> Session:
        """Create and persist a new session in state ``Created``.

        This is Session Coordinator territory only: identity generation,
        ownership binding, template/subject binding. It performs no
        evidence acquisition, no decision presentation, and creates no
        CHGR.
        """

        timestamp = _now_iso()
        session = Session(
            session_id=generate_session_id(),
            owner_identity=owner_identity,
            template_ref=template_ref,
            subject_ref=subject_ref,
            session_state=SessionState.CREATED,
            schema_version=SCHEMA_VERSION,
            created_at=timestamp,
            updated_at=timestamp,
        )
        validate_session(session)
        self._repository.create(session)
        return session

    def list_session_ids(self) -> List[str]:
        """Return every persisted session id (Phase 149O.20L.7O.3C.2:
        Interactive Workflow auto-detect + route needs a deterministic,
        full-scan-by-identity lookup -- never a "most recent file"
        heuristic -- to find the session bound to a given subject; this
        is a thin delegation to the injected ``SessionRepository``'s own
        existing ``list_session_ids``, exactly like every other method on
        this class delegates to a collaborator it does not reimplement)."""

        return list(self._repository.list_session_ids())

    def load_session(self, session_id: str) -> Session:
        """Return the persisted session for ``session_id``.

        Raises ``SessionNotFoundError`` if no record exists. Performs no
        ownership re-check here -- ownership re-verification on resume is
        a resumability concern (IWC-001 v1.1 §4.5), deferred to the
        transition engine (Phase 143L) that actually drives resumption.
        """

        if not self._repository.exists(session_id):
            raise SessionNotFoundError(f"No session found for {session_id!r}.")
        return self._repository.load(session_id)

    def persist_session(self, session: Session) -> None:
        """Persist an existing, already-validated session record."""

        validate_session(session)
        self._repository.persist(session)

    def validate_state(self, session: Session, proposed_state: Optional[SessionState] = None) -> None:
        """Validate ``session``'s current state, and optionally a
        proposed next state, against the structural invariants.

        Does not itself decide whether a transition *should* occur --
        only whether it structurally *could*.
        """

        validate_session(session)
        if proposed_state is not None:
            validate_terminal_integrity(session.session_state, proposed_state)

    def build_orchestrator(
        self,
        session_id: str,
        evidence_coordinator: EvidenceCoordinator,
        clarification_controller: ClarificationController,
        audit_recorder: AuditRecorder,
        preview_builder: PreviewBuilder,
        confirmation_controller: ConfirmationController,
        transition_engine: TransitionEngine,
    ) -> WorkflowOrchestrator:
        """Assemble a ``WorkflowOrchestrator`` for ``session_id`` from
        its six already-constructed collaborators (Phase 143O).

        This is the assembly point through which Session Coordinator
        satisfies "sole owner of ... orchestration state": it constructs
        no collaborator itself (every one is supplied by the caller,
        exactly like this class's own constructor-injected
        ``SessionRepository``), and it re-implements no sequencing rule
        -- ``WorkflowOrchestrator`` (``pcae.interactive_workflow.
        orchestration.coordinator``) owns every stage's actual logic.
        """

        return WorkflowOrchestrator(
            session_id=session_id,
            evidence_coordinator=evidence_coordinator,
            clarification_controller=clarification_controller,
            audit_recorder=audit_recorder,
            preview_builder=preview_builder,
            confirmation_controller=confirmation_controller,
            transition_engine=transition_engine,
        )

    def orchestrate_evidence(
        self, orchestrator: WorkflowOrchestrator, declared_evidence_ids: Iterable[str]
    ):
        """Drive the Evidence Availability orchestration stage.

        Implemented as of Phase 143O -- this is exactly the sequencing
        responsibility this phase's "Session Coordinator Integration"
        section authorizes (unlike ``perform_publication`` below,
        nothing in IWC-001 v1.1 leaves evidence-orchestration ownership
        an open question). Thin delegation only: this method performs no
        evidence validation, scoring, or registration itself --
        ``WorkflowOrchestrator.stage_evidence_availability`` delegates in
        turn to the Evidence Coordinator's own ``report_missing``.
        """

        return orchestrator.stage_evidence_availability(declared_evidence_ids)

    def perform_confirmation(
        self,
        orchestrator: WorkflowOrchestrator,
        request_id: str,
        response: ConfirmationResponse,
        preview: Preview,
        current_transition_sequence_number: int,
    ):
        """Drive the Confirmation Validation orchestration stage.

        Implemented as of Phase 143O, narrowly: this method sequences
        the *stage* (invoking ``WorkflowOrchestrator.
        stage_confirmation_validation``, which itself delegates to
        ``ConfirmationController.register_response``); it never performs
        the confirming act itself -- the deliberate, non-defaultable
        confirming act remains the eligible Human Authority's own act
        (IWC-001 v1.1 §10.7), captured in the ``ConfirmationResponse``
        the caller must already have constructed and supplied. This
        method's name is inherited unchanged from Phase 143K's original
        stub; it was already a request/response *sequencing* concern
        under Phase 143J §16's original Confirmation Engine row, not a
        proposal to grant this class confirmation *authority* -- see
        Phase 143O's report §0 for the full judgment call.
        """

        return orchestrator.stage_confirmation_validation(
            request_id, response, preview, current_transition_sequence_number
        )

    def perform_publication(self, *args, **kwargs):
        """Not implemented on this class, and never will be.

        IWC-REQ-171 (IWC-001 v1.1 §21.18) leaves Publication Handoff
        *execution* ownership an explicitly open question for a future,
        separately governed phase; §18.4's judgment call reaches the
        same conclusion independently. Phase 143O's own governing
        prompt's Explicit No-Go list forbids this phase from performing
        publication. Phase 143O does add a Publication Handoff
        *interface* and an immutable *readiness package*
        (``pcae.interactive_workflow.publication_handoff``), but neither
        publishes, and neither is wired to this method -- there is no
        scope under which ``perform_publication`` could return normally
        on this class without this phase (or some other single phase)
        informally claiming an ownership question every governing
        contract has deliberately left open.
        """

        raise NotImplementedError(
            "SessionCoordinator.perform_publication is permanently out of scope "
            "(Publication Handoff execution ownership is an explicitly open "
            "question -- IWC-REQ-171, IWC-001 v1.1 §18.4). See "
            "pcae.interactive_workflow.publication_handoff.PublicationHandoff for "
            "this phase's readiness-package-only interface, which does not "
            "publish."
        )


__all__ = [
    "LifecycleHook",
    "SessionCoordinator",
]
