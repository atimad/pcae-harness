"""SessionApplicationService (Phase 145F; extended Phase 145G.1).

Coordinates ``SessionCoordinator``/``SessionRepository`` for a future
transport adapter -- session lifecycle coordination (create, load,
persist, update, completion) plus deterministic translation of every
underlying exception into this boundary's own closed application-error
taxonomy (``application.errors``). This class establishes no authority,
performs no evidence/clarification/preview/confirmation logic itself, and
never constructs a CHGR (IWPC-REQ-011: session semantics remain
``SessionCoordinator``/``WorkflowOrchestrator``'s exclusively; this class
delegates every such decision, it does not reimplement any of them).

Phase 145G.1 adds ``submit_evidence``/``submit_clarification``/
``generate_preview``/``record_confirmation``/``cancel_session``/
``construct_readiness_package`` -- the missing application-boundary
operations Phase 145G's own report (F-145G-1) found no persisted domain
state to resume, blocking a CLI adapter from ever implementing
``evidence``/``clarify``/``preview``/``confirm``/``cancel`` across
separate process invocations. Each new method: loads the persisted
``Session``; loads (or creates) this session's persisted
``OrchestrationRecord`` (``interactive_workflow.persistence.
filesystem_orchestration_store``); rehydrates the six ``WorkflowOrchestrator``
collaborators from that record's own data via their own public
registration methods (never by reaching into a private attribute);
delegates every transition-legality and workflow-semantic decision to
``SessionCoordinator``/``WorkflowOrchestrator``/``TransitionEngine``
unchanged; and persists the resulting ``Session`` and
``OrchestrationRecord`` atomically before returning. See this phase's
canonical report for the full requirement-to-code traceability matrix,
including the one disclosed, unresolved architectural gap this phase
found and could not close within its own authorized scope (F-145G.1-1):
no command in IWPC-001 v1.1's frozen §5 command surface could transition
a session out of ``AwaitingDecision``, so ``DecisionSelected``/
``AwaitingConfirmation`` -- the precondition states ``preview``/
``confirm`` themselves require -- were unreachable through any real,
CLI-only invocation sequence.

Phase 145G.2 closes F-145G.1-1 with a new ``select_decision`` method (see
below), a repaired IWPC-001 v1.2 §5 command surface (new
``decision-session select`` command, IWPC-REQ-192-196), and the
corresponding CLI handler (``pcae.commands.decision_session``). A
sibling, separately-disclosed gap remains open and is deliberately not
closed by this phase (out of its own authorized "decision selection"
scope): no command transitions a session from ``AwaitingDecision`` into
``AwaitingClarification`` (``clarify`` itself only answers a
clarification already in progress, ``AwaitingClarification`` ->
``AwaitingDecision``), so the *clarification* path specifically remains
reachable only via the same test-fixture bridge Phase 145G.1's own test
suite already established (F-145G.2-1; see the Phase 145G.2 canonical
report).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Tuple

from pcae.interactive_workflow.application.errors import (
    InvalidSessionIdentifierApplicationError,
    ReadinessSessionNotConfirmedApplicationError,
    SessionAlreadyExistsApplicationError,
    SessionConfirmationConflictApplicationError,
    SessionCorruptApplicationError,
    SessionIdentityMismatchApplicationError,
    SessionInvalidTransitionApplicationError,
    SessionNotFoundApplicationError,
    SessionNotTerminalApplicationError,
    SessionOrchestrationCorruptApplicationError,
    SessionOrchestrationPersistenceUnavailableApplicationError,
    SessionPersistenceUnavailableApplicationError,
)
from pcae.aesic.records import Stage1EvaluationResult, aer_to_payload
from pcae.aesic.service import AuthorityEvaluationService
from pcae.interactive_workflow.confirmation.controller import ConfirmationController
from pcae.interactive_workflow.confirmation.models import (
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationResult,
)
from pcae.interactive_workflow.audit.recorder import AuditRecorder
from pcae.interactive_workflow.clarification.controller import ClarificationController
from pcae.interactive_workflow.errors import (
    DuplicateClarificationError,
    DuplicateConfirmationError,
    DuplicateEvidenceError,
    InvalidClarificationError,
    InvalidConfirmationError,
    InvalidIdentifierError,
    InvalidPreviewError,
    InvalidSelectionError,
    InvalidWorkflowSequenceError,
    MissingWorkflowComponentError,
    OrchestrationStoreCorruptError,
    PersistenceUnavailableError,
    PreviewDigestMismatchError,
    PublicationHandoffIncompleteError,
    ReplayDetectedError,
    SessionAlreadyExistsError,
    SessionNotFoundError,
    SessionStoreCorruptError,
    StalePreviewError,
    TransitionError,
    UnknownEvidenceError,
    WorkflowCompositionError,
    WorkflowInitializationError,
)
from pcae.interactive_workflow.evidence.coordinator import EvidenceCoordinator
from pcae.interactive_workflow.evidence.models import EvidenceAvailability, EvidenceItem
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.orchestration.coordinator import WorkflowOrchestrator
from pcae.interactive_workflow.orchestration.models import OrchestrationStage, OrchestrationState
from pcae.interactive_workflow.persistence.filesystem_orchestration_store import (
    FilesystemOrchestrationStore,
    OrchestrationRecord,
)
from pcae.interactive_workflow.preview.builder import PreviewBuilder
from pcae.interactive_workflow.preview.models import Preview
from pcae.interactive_workflow.publication_handoff.handoff import PublicationHandoff
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.coordinator import SessionCoordinator
from pcae.interactive_workflow.state_machine.engine import TransitionEngine

_PREVIEWABLE_STATES = frozenset(
    {SessionState.DECISION_SELECTED, SessionState.AWAITING_CONFIRMATION, SessionState.CONFIRMED}
)

_ORCHESTRATION_DOMAIN_ERRORS = (
    TransitionError,
    InvalidWorkflowSequenceError,
    MissingWorkflowComponentError,
    WorkflowCompositionError,
    WorkflowInitializationError,
    DuplicateEvidenceError,
    UnknownEvidenceError,
    DuplicateClarificationError,
    InvalidClarificationError,
    InvalidPreviewError,
    InvalidSelectionError,
)

_CONFIRMATION_CONFLICT_ERRORS = (
    PreviewDigestMismatchError,
    StalePreviewError,
    ReplayDetectedError,
    DuplicateConfirmationError,
    InvalidConfirmationError,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _preview_to_payload(preview: Preview) -> Dict[str, Any]:
    return {
        "preview_id": preview.preview_id,
        "session_id": preview.session_id,
        "preview_timestamp": preview.preview_timestamp,
        "transition_sequence_number": preview.transition_sequence_number,
        "evidence_refs": list(preview.evidence_refs),
        "clarification_refs": list(preview.clarification_refs),
        "audit_refs": list(preview.audit_refs),
        "transition_summary": preview.transition_summary,
        "rendered_content": preview.rendered_content,
        "metadata": dict(preview.metadata),
    }


def _preview_from_payload(payload: Dict[str, Any]) -> Preview:
    return Preview(
        preview_id=payload["preview_id"],
        session_id=payload["session_id"],
        preview_timestamp=payload["preview_timestamp"],
        transition_sequence_number=payload["transition_sequence_number"],
        evidence_refs=tuple(payload.get("evidence_refs") or ()),
        clarification_refs=tuple(payload.get("clarification_refs") or ()),
        audit_refs=tuple(payload.get("audit_refs") or ()),
        transition_summary=payload.get("transition_summary", ""),
        rendered_content=payload.get("rendered_content", ""),
        metadata=payload.get("metadata") or {},
    )


def _render_preview_content(
    session: Session, evidence_refs: Tuple[str, ...], clarification_refs: Tuple[str, ...]
) -> str:
    """Deterministic, minimal rendered Preview text.

    Captured exactly once by ``PreviewBuilder.build`` (IWC-REQ-188) --
    this function's own output is a pure function of its arguments, so
    two calls against unchanged input are byte-identical, matching
    IWPC-REQ-019's natural-idempotency requirement.
    """

    lines = [
        f"Decision Subject: {session.subject_ref}",
        f"Template: {session.template_ref}",
        f"Owner: {session.owner_identity}",
        f"Evidence: {', '.join(evidence_refs) if evidence_refs else '(none)'}",
        f"Clarifications: {', '.join(clarification_refs) if clarification_refs else '(none)'}",
    ]
    if session.human_selection_id:
        lines.append(f"Selected option: {session.human_selection_id}")
    if session.human_rationale_text:
        lines.append(f"Rationale: {session.human_rationale_text}")
    if session.human_conditions_text:
        lines.append(f"Conditions: {session.human_conditions_text}")
    return "\n".join(lines)


def _rehydrate_collaborators(session_id: str, record: OrchestrationRecord):
    """Reconstruct the six ``WorkflowOrchestrator`` collaborators plus a
    resumed orchestrator from a persisted ``OrchestrationRecord``.

    Every collaborator's internal state is rebuilt exclusively through
    that collaborator's own public registration methods (``register``,
    ``register_request``, ``register_response``) -- never by writing to a
    private attribute -- so this function can never construct a
    collaborator into a state its own class would have rejected.
    """

    evidence_coordinator = EvidenceCoordinator(session_id)
    for item in record.evidence:
        evidence_coordinator.register(
            EvidenceItem(
                evidence_id=item["evidence_id"],
                evidence_type=item["evidence_type"],
                provenance_ref=item["provenance_ref"],
                collected_at=item["collected_at"],
                availability=EvidenceAvailability(item["availability"]),
            )
        )

    clarification_controller = ClarificationController(session_id)
    for item in record.clarifications:
        clarification_controller.register_request(
            item["clarification_id"], item["request_text"], item["requested_at"]
        )
        if item.get("response_text") is not None:
            clarification_controller.register_response(
                item["clarification_id"], item["response_text"], item["responded_at"]
            )

    audit_recorder = AuditRecorder(session_id)
    preview_builder = PreviewBuilder()

    confirmation_controller = ConfirmationController(session_id)
    for item in record.confirmation_requests:
        confirmation_controller.register_request(
            ConfirmationRequest(
                request_id=item["request_id"],
                session_id=session_id,
                preview_id=item["preview_id"],
                preview_digest=item["preview_digest"],
                created_at=item["created_at"],
            )
        )
    if record.confirmation_responses and record.last_preview is not None:
        cached_preview = _preview_from_payload(record.last_preview)
        for item in record.confirmation_responses:
            response = ConfirmationResponse(
                response_id=item["response_id"],
                request_id=item["request_id"],
                confirmed_at=item["confirmed_at"],
                confirmation_result=ConfirmationResult(item["confirmation_result"]),
                preview_digest=item["preview_digest"],
                metadata=item.get("metadata") or {},
            )
            # Replay-safe: this response only exists in the persisted
            # record because ``detect_staleness`` already accepted it once
            # against exactly this preview content, so replaying with the
            # preview's own recorded transition_sequence_number as
            # "current" is guaranteed to match (it is not a bypass of the
            # staleness check -- it reconstructs the exact prior-accepted
            # state, never a new acceptance).
            confirmation_controller.register_response(
                item["request_id"], response, cached_preview, cached_preview.transition_sequence_number
            )

    transition_engine = TransitionEngine()
    initial_state = OrchestrationState(
        session_id=session_id,
        completed_stages=tuple(OrchestrationStage(value) for value in record.completed_stages),
    )
    orchestrator = WorkflowOrchestrator(
        session_id=session_id,
        evidence_coordinator=evidence_coordinator,
        clarification_controller=clarification_controller,
        audit_recorder=audit_recorder,
        preview_builder=preview_builder,
        confirmation_controller=confirmation_controller,
        transition_engine=transition_engine,
        initial_state=initial_state,
    )
    return orchestrator, evidence_coordinator, clarification_controller, confirmation_controller, preview_builder


class SessionApplicationService:
    """Application-layer coordination over ``SessionCoordinator``.

    Constructed with an explicit ``SessionCoordinator`` (dependency
    injection, mirroring ``SessionCoordinator``'s own constructor-injected
    ``SessionRepository`` boundary) -- this class never selects or
    constructs its own coordinator. ``orchestration_store`` (Phase 145G.1)
    follows the same discipline: an explicit, optional, constructor-
    injected collaborator with its own default-root convenience
    construction, mirroring every sibling store in this codebase.
    """

    def __init__(
        self,
        coordinator: SessionCoordinator,
        orchestration_store: Optional[FilesystemOrchestrationStore] = None,
        authority_evaluation_service: "Optional[AuthorityEvaluationService]" = None,
    ) -> None:
        self._coordinator = coordinator
        self._orchestration_store = orchestration_store or FilesystemOrchestrationStore()
        # AESIC-001 v1.3 §9.2/§19: optional, additive collaborator. When
        # absent (the default -- every pre-Phase-147M caller), Stage 1/
        # Stage 2 are never invoked and existing behavior is byte-for-byte
        # unchanged (AESIC-REQ-109).
        self._authority_evaluation_service = authority_evaluation_service

    def create_session(
        self,
        *,
        owner_identity: str,
        template_ref: str,
        subject_ref: str,
    ) -> Session:
        """Create and persist a new session in state ``Created``."""

        try:
            return self._coordinator.create_session(owner_identity, template_ref, subject_ref)
        except SessionAlreadyExistsError as exc:
            raise SessionAlreadyExistsApplicationError(str(exc)) from exc
        except InvalidIdentifierError as exc:
            raise InvalidSessionIdentifierApplicationError(str(exc)) from exc
        except PersistenceUnavailableError as exc:
            raise SessionPersistenceUnavailableApplicationError(str(exc)) from exc

    def load_session(self, session_id: str) -> Session:
        """Return the persisted session for ``session_id``."""

        try:
            return self._coordinator.load_session(session_id)
        except SessionNotFoundError as exc:
            raise SessionNotFoundApplicationError(str(exc), session_id=session_id) from exc
        except InvalidIdentifierError as exc:
            raise InvalidSessionIdentifierApplicationError(str(exc), session_id=session_id) from exc
        except SessionStoreCorruptError as exc:
            raise SessionCorruptApplicationError(str(exc), session_id=session_id) from exc
        except PersistenceUnavailableError as exc:
            raise SessionPersistenceUnavailableApplicationError(str(exc), session_id=session_id) from exc

    def find_session_by_subject_ref(self, subject_ref: str) -> Optional[Session]:
        """Return the most-recently-created persisted session whose
        ``subject_ref`` exactly equals ``subject_ref``, or ``None`` if
        none exists (Phase 149O.20L.7O.3C.2). Performs one full,
        deterministic scan of every session id via
        ``SessionCoordinator.list_session_ids``/``load_session`` -- no
        "most recent file" ordering, no narrowing by state before the
        scan. If more than one session shares the same ``subject_ref``
        (``--subject-ref`` remains free text at ``decision-session
        create``; this method does not prevent duplicates), the most
        recently created one is returned -- a disclosed limitation, not a
        silently-assumed impossibility."""

        candidates: list[Session] = []
        for session_id in self._coordinator.list_session_ids():
            try:
                session = self._coordinator.load_session(session_id)
            except SessionNotFoundError:
                continue
            if session.subject_ref == subject_ref:
                candidates.append(session)
        if not candidates:
            return None
        candidates.sort(key=lambda s: s.created_at)
        return candidates[-1]

    def persist_session(self, session: Session) -> None:
        """Persist an existing, already-validated session record."""

        try:
            self._coordinator.persist_session(session)
        except SessionNotFoundError as exc:
            raise SessionNotFoundApplicationError(str(exc), session_id=session.session_id) from exc
        except PersistenceUnavailableError as exc:
            raise SessionPersistenceUnavailableApplicationError(
                str(exc), session_id=session.session_id
            ) from exc

    def update_session(self, session: Session) -> None:
        """Persist an updated session record.

        Named distinctly from ``persist_session`` only because this
        phase's governing prompt lists "update" as its own
        lifecycle-coordination responsibility; ``SessionRepository``
        itself defines no separate update primitive (IWPC-REQ-066: exactly
        ``create``/``load``/``persist``/``exists``/``list_session_ids``),
        so this is deliberately an alias, not a second code path.
        """

        self.persist_session(session)

    def complete_session(self, session: Session) -> Session:
        """Mark session-lifecycle coordination complete for ``session``.

        Requires ``session`` to have already reached a terminal state
        (``Confirmed``/``Cancelled``/``Expired``/``Abandoned``) via the
        Interactive Workflow state machine -- this method performs no
        transition itself (IWPC-REQ-011); it only persists the
        already-terminal record and fails closed if the precondition does
        not hold.
        """

        if not session.is_terminal():
            raise SessionNotTerminalApplicationError(
                f"Session {session.session_id!r} is not in a terminal state "
                f"({session.session_state.value!r}); completion requires a "
                "terminal state already reached via the Interactive Workflow "
                "state machine.",
                session_id=session.session_id,
            )
        self.persist_session(session)
        return session

    # -- identity-bound resumption (Phase 145G.3, IWC-REQ-022/151) ----------

    def _require_bound_identity(self, session: Session, caller_identity: str) -> None:
        """Enforce that ``session`` is being resumed by the identity bound
        to it at creation (IWC-REQ-022/IWC-REQ-151), closing F-145G.2V-1.

        Sole validation owner for every resumed-session operation: every
        mutating method below calls this immediately after ``load_session``
        resolves the persisted record, before any state-precondition check,
        idempotent early-return, or orchestration logic -- so a mismatched
        identity can never slip through an idempotent code path (e.g.
        ``cancel_session`` against an already-``Cancelled`` session) and
        never becomes an idempotent success.

        Exact-string comparison only: no case-folding, no whitespace
        normalization, no prefix/partial matching. A near-miss claim is a
        mismatch, not a match -- this method infers nothing and repairs
        nothing on the caller's behalf. Structural well-formedness of the
        claim (non-empty, bounded length, no control characters) is the
        transport layer's own responsibility (IWPC-REQ-007); this method
        does not repeat that check -- a missing or malformed claim simply
        cannot equal a well-formed ``owner_identity`` and is rejected here
        as a mismatch, never silently accepted.
        """

        if not isinstance(caller_identity, str) or caller_identity != session.owner_identity:
            raise SessionIdentityMismatchApplicationError(
                f"Session {session.session_id!r} may be resumed only by the identity "
                "bound to it at creation; the supplied identity claim does not match "
                "(IWC-REQ-022, IWC-REQ-151).",
                session_id=session.session_id,
            )

    def require_bound_identity(self, session_id: str, caller_identity: str) -> Session:
        """Load ``session_id`` and enforce ``_require_bound_identity``
        against it, returning the session on success.

        Public so that sibling application services in this same bounded
        context -- namely ``PublicationApplicationService.
        ensure_readiness_package``, whose own idempotent-by-key cache hit
        would otherwise never re-check identity on a second ``readiness``
        call -- can reuse this exact validation path rather than
        duplicating the comparison (this phase's single-validation-owner
        requirement).
        """

        session = self.load_session(session_id)
        self._require_bound_identity(session, caller_identity)
        return session

    # -- orchestration bookkeeping (Phase 145G.1) --------------------------

    def _persist_orchestration(self, record: OrchestrationRecord) -> None:
        try:
            self._orchestration_store.persist(record)
        except OrchestrationStoreCorruptError as exc:
            raise SessionOrchestrationCorruptApplicationError(
                str(exc), session_id=record.session_id
            ) from exc
        except PersistenceUnavailableError as exc:
            raise SessionOrchestrationPersistenceUnavailableApplicationError(
                str(exc), session_id=record.session_id
            ) from exc

    def _load_orchestration(self, session_id: str) -> OrchestrationRecord:
        try:
            return self._orchestration_store.load_or_create(session_id)
        except OrchestrationStoreCorruptError as exc:
            raise SessionOrchestrationCorruptApplicationError(str(exc), session_id=session_id) from exc
        except PersistenceUnavailableError as exc:
            raise SessionOrchestrationPersistenceUnavailableApplicationError(
                str(exc), session_id=session_id
            ) from exc

    def _run_orchestration_body(self, session_id: str, body):
        """Run ``body()``, translating every raised orchestration/domain
        exception into this boundary's own closed application-error
        taxonomy (mirrors ``create_session``/``load_session``'s own
        per-call translation, generalized across the five new operations
        so each does not repeat an identical ``except`` chain)."""

        try:
            return body()
        except _CONFIRMATION_CONFLICT_ERRORS as exc:
            raise SessionConfirmationConflictApplicationError(str(exc), session_id=session_id) from exc
        except _ORCHESTRATION_DOMAIN_ERRORS as exc:
            raise SessionInvalidTransitionApplicationError(str(exc), session_id=session_id) from exc
        except PublicationHandoffIncompleteError as exc:
            raise ReadinessSessionNotConfirmedApplicationError(str(exc), session_id=session_id) from exc

    # -- decision-session evidence (IWPC-REQ-016) ---------------------------

    def submit_evidence(self, session_id: str, evidence_ids: Iterable[str], *, caller_identity: str) -> Session:
        """Declare evidence references against a session in ``Created``.

        Single-invocation design (disclosed judgment call, this phase's
        canonical report): because no template-declared "required
        evidence" list exists anywhere in this codebase to check
        completeness against, and ``EvidenceCoordinator.report_missing``
        can only ever report a declared identifier as missing if it was
        *not* just registered, every successful ``evidence`` call
        registers every one of its declared identifiers and therefore
        immediately satisfies "evidence complete," transitioning
        ``Created`` -> ``EvidenceReady`` in the same call (matching
        IWPC-REQ-016's own "session already past evidence-declaration
        stage" rejection for any *second* call).
        """

        session = self.load_session(session_id)
        self._require_bound_identity(session, caller_identity)
        if session.session_state is not SessionState.CREATED:
            raise SessionInvalidTransitionApplicationError(
                f"Session {session_id!r} is in state {session.session_state.value!r}; "
                "evidence may only be declared while a session is in state 'Created'.",
                session_id=session_id,
            )

        def body() -> Session:
            record = self._load_orchestration(session_id)
            orchestrator, evidence_coordinator, _, _, _ = _rehydrate_collaborators(session_id, record)

            if not record.completed_stages:
                orchestrator.stage_session_initialization(session)

            declared = tuple(dict.fromkeys(evidence_ids))
            now = _now_iso()
            existing_ids = {item["evidence_id"] for item in record.evidence}
            new_items = []
            for evidence_id in declared:
                if evidence_id in existing_ids:
                    continue
                item = EvidenceItem(
                    evidence_id=evidence_id,
                    evidence_type="cli-declared",
                    provenance_ref=evidence_id,
                    collected_at=now,
                    availability=EvidenceAvailability.AVAILABLE,
                )
                evidence_coordinator.register(item)
                new_items.append(
                    {
                        "evidence_id": item.evidence_id,
                        "evidence_type": item.evidence_type,
                        "provenance_ref": item.provenance_ref,
                        "collected_at": item.collected_at,
                        "availability": item.availability.value,
                    }
                )

            missing = orchestrator.stage_evidence_availability(declared)

            new_seq = record.transition_sequence_number
            updated_session = session
            if not missing:
                new_seq = record.transition_sequence_number + 1
                result = TransitionEngine().apply(
                    session,
                    SessionState.EVIDENCE_READY,
                    sequence_number=new_seq,
                    previous_sequence_number=record.transition_sequence_number or None,
                )
                updated_session = result.session

            new_record = OrchestrationRecord(
                session_id=session_id,
                completed_stages=tuple(stage.value for stage in orchestrator.state.completed_stages),
                transition_sequence_number=new_seq,
                evidence=record.evidence + tuple(new_items),
                clarifications=record.clarifications,
                confirmation_requests=record.confirmation_requests,
                confirmation_responses=record.confirmation_responses,
                last_preview=record.last_preview,
                cancellation=record.cancellation,
            )
            self._persist_orchestration(new_record)
            self.persist_session(updated_session)
            return updated_session

        return self._run_orchestration_body(session_id, body)

    # -- decision-session select (Phase 145G.2, IWPC-REQ-192-196) -----------

    def select_decision(
        self,
        session_id: str,
        *,
        option_id: str,
        options_presented: Iterable[str],
        template_version: str,
        caller_identity: str,
        rationale: Optional[str] = None,
        conditions: Optional[str] = None,
    ) -> Session:
        """Record a human decision selection against a session in
        ``EvidenceReady`` or ``AwaitingDecision``, transitioning it to
        ``DecisionSelected`` (IWPC-REQ-192; closes F-145G.1-1).

        Single-invocation design combining two hops (disclosed judgment
        call, this phase's canonical report, IWPC-REQ-196), exactly
        mirroring ``submit_evidence``'s own single-invocation precedent
        (Phase 145G.1): a session in ``EvidenceReady`` has no CLI-only
        path into ``AwaitingDecision`` other than through this command, so
        a session in either state is accepted, and the sequencing-only
        ``EvidenceReady`` -> ``AwaitingDecision`` hop (no orchestration
        stage governs it, mirroring ``generate_preview``'s own
        sequencing-only ``ClarificationLifecycle`` advance) is performed
        internally before the ``AwaitingDecision`` -> ``DecisionSelected``
        hop that actually records the selection. Fails closed, single-use
        (IWPC-REQ-193): once a session has left ``EvidenceReady``/
        ``AwaitingDecision`` (including into ``DecisionSelected`` itself),
        every subsequent ``select`` call is rejected by the precondition
        check below -- there is no idempotent-replay path, matching
        ``record_confirmation``'s own precedent for an irreversible human
        act rather than ``submit_evidence``/``cancel_session``'s
        idempotent-by-key precedent.

        Identity (IWPC-REQ-195, repaired Phase 145G.3 closing F-145G.2V-1):
        the selecting principal must equal the session's own bound
        ``owner_identity``, enforced via ``_require_bound_identity``
        immediately after ``load_session`` resolves the persisted record,
        before this method's own state-precondition check. ``caller_identity``
        is a required explicit claim (IWC-REQ-022/IWC-REQ-151) -- never
        inferred from OS user, git config, or the calling agent's own id.

        Option-presentation binding (IWPC-REQ-194): ``options_presented``
        is caller-declared, exactly like ``submit_evidence``'s own
        caller-declared evidence identifiers -- no production Decision
        Template loader/resolver exists anywhere in this codebase to
        validate against a real closed set (disclosed judgment call,
        mirroring ``submit_evidence``'s own precedent). This method still
        enforces that ``option_id`` is a genuine member of
        ``options_presented`` (``InvalidSelectionError`` otherwise); CLI-
        layer structural checks (non-empty, no duplicates) are the
        transport adapter's own responsibility (IWPC-REQ-036/041/055),
        not repeated here. ``template_version`` is captured here for the
        identical reason (Phase 145G.2 re-derivation finding: it too has
        no production setter and no template resolver to derive it from;
        it is required, not optional, because
        ``PublicationHandoff.validate_completeness`` already requires it
        non-empty, and leaving it unset here would silently strand a
        session that can never reach readiness/publication).
        """

        session = self.load_session(session_id)
        self._require_bound_identity(session, caller_identity)
        if session.session_state not in (
            SessionState.EVIDENCE_READY,
            SessionState.AWAITING_DECISION,
        ):
            raise SessionInvalidTransitionApplicationError(
                f"Session {session_id!r} is in state {session.session_state.value!r}; "
                "select requires a session in state 'EvidenceReady' or 'AwaitingDecision'.",
                session_id=session_id,
            )

        presented = tuple(options_presented)

        def body() -> Session:
            record = self._load_orchestration(session_id)

            if option_id not in presented:
                raise InvalidSelectionError(
                    f"Selected option {option_id!r} is not a member of the "
                    f"presented option set {presented!r} for session {session_id!r}."
                )

            working_session = session
            seq = record.transition_sequence_number
            if working_session.session_state is SessionState.EVIDENCE_READY:
                seq += 1
                result = TransitionEngine().apply(
                    working_session,
                    SessionState.AWAITING_DECISION,
                    sequence_number=seq,
                    previous_sequence_number=record.transition_sequence_number or None,
                )
                working_session = result.session

            seq += 1
            result = TransitionEngine().apply(
                working_session,
                SessionState.DECISION_SELECTED,
                sequence_number=seq,
                previous_sequence_number=seq - 1,
            )
            updated_session = result.session.with_decision_capture(
                new_state=SessionState.DECISION_SELECTED,
                updated_at=result.metadata.transition_timestamp,
                human_selection_id=option_id,
                options_presented=presented,
                template_version=template_version,
                human_rationale_text=rationale or None,
                human_conditions_text=conditions or None,
            )

            new_record = OrchestrationRecord(
                session_id=session_id,
                completed_stages=record.completed_stages,
                transition_sequence_number=seq,
                evidence=record.evidence,
                clarifications=record.clarifications,
                confirmation_requests=record.confirmation_requests,
                confirmation_responses=record.confirmation_responses,
                last_preview=record.last_preview,
                cancellation=record.cancellation,
            )
            self._persist_orchestration(new_record)
            self.persist_session(updated_session)
            return updated_session

        return self._run_orchestration_body(session_id, body)

    # -- decision-session clarify (IWPC-REQ-017) ----------------------------

    def submit_clarification(
        self, session_id: str, question: str, answer: str, *, caller_identity: str
    ) -> Session:
        """Record one clarification request/response pair against a
        session in ``AwaitingClarification``, transitioning it to
        ``AwaitingDecision`` (IWC-001-governed transition)."""

        session = self.load_session(session_id)
        self._require_bound_identity(session, caller_identity)
        if session.session_state is not SessionState.AWAITING_CLARIFICATION:
            raise SessionInvalidTransitionApplicationError(
                f"Session {session_id!r} is in state {session.session_state.value!r}; "
                "clarify requires a session in state 'AwaitingClarification'.",
                session_id=session_id,
            )

        def body() -> Session:
            record = self._load_orchestration(session_id)
            orchestrator, _, clarification_controller, _, _ = _rehydrate_collaborators(session_id, record)

            now = _now_iso()
            clarification_id = f"clr-{uuid.uuid4().hex}"
            clarification_controller.register_request(clarification_id, question, now)
            clarification_controller.register_response(clarification_id, answer, now)
            orchestrator.stage_clarification_lifecycle()

            new_seq = record.transition_sequence_number + 1
            result = TransitionEngine().apply(
                session,
                SessionState.AWAITING_DECISION,
                sequence_number=new_seq,
                previous_sequence_number=record.transition_sequence_number or None,
            )
            updated_session = result.session

            new_record = OrchestrationRecord(
                session_id=session_id,
                completed_stages=tuple(stage.value for stage in orchestrator.state.completed_stages),
                transition_sequence_number=new_seq,
                evidence=record.evidence,
                clarifications=record.clarifications
                + (
                    {
                        "clarification_id": clarification_id,
                        "request_text": question,
                        "requested_at": now,
                        "response_text": answer,
                        "responded_at": now,
                        "tags": [],
                    },
                ),
                confirmation_requests=record.confirmation_requests,
                confirmation_responses=record.confirmation_responses,
                last_preview=record.last_preview,
                cancellation=record.cancellation,
            )
            self._persist_orchestration(new_record)
            self.persist_session(updated_session)
            return updated_session

        return self._run_orchestration_body(session_id, body)

    # -- decision-session preview (IWPC-REQ-018/019) ------------------------

    def generate_preview(self, session_id: str, *, caller_identity: str) -> Tuple[Preview, str]:
        """Render the exact, unconditional Preview for a session in
        ``DecisionSelected`` or later, returning ``(preview,
        preview_digest)``. Naturally idempotent (IWPC-REQ-019): the
        orchestrator's own Preview Construction/Validation stages advance
        at most once; every subsequent call re-renders live via
        ``PreviewBuilder`` directly, reusing the cached Preview's own
        identity/timestamp so repeated calls against an unchanged session
        reproduce a byte-identical digest.

        On the first successful construction only, also performs the
        session-state transition ``DecisionSelected`` -> ``AwaitingConfirmation``
        (Phase 145G.2 re-derivation finding, disclosed in the Phase 145G.2
        canonical report): IWC-001's own frozen state table defines
        ``AwaitingConfirmation`` as "Preview generated, awaiting
        Confirmation," and IWPC-REQ-018 already conditions preview's "no
        transition" default on "unless IWC-001 defines otherwise" -- IWC-001
        does define otherwise here. Before this fix, first construction
        left the session in ``DecisionSelected`` indefinitely, so ``confirm``
        (which requires ``AwaitingConfirmation``) was unreachable via any
        real CLI-only sequence even after Phase 145G.2's own
        ``select`` command closed F-145G.1-1 -- a second, previously
        undisclosed instance of the same defect class one hop further down
        the chain. Idempotent re-renders (session already
        ``AwaitingConfirmation``/``Confirmed``) perform no further
        transition."""

        session = self.load_session(session_id)
        self._require_bound_identity(session, caller_identity)
        if session.session_state not in _PREVIEWABLE_STATES:
            raise SessionInvalidTransitionApplicationError(
                f"Session {session_id!r} is in state {session.session_state.value!r}; "
                "preview requires a session in state 'DecisionSelected' or later.",
                session_id=session_id,
            )

        def body() -> Tuple[Preview, str]:
            record = self._load_orchestration(session_id)
            orchestrator, evidence_coordinator, clarification_controller, _, preview_builder = (
                _rehydrate_collaborators(session_id, record)
            )

            # Sequencing-only advance (no domain decision made here): a
            # session that never needed `clarify` still must have the
            # orchestrator's CLARIFICATION_LIFECYCLE bookkeeping stage
            # marked complete before Preview Construction may run.
            if orchestrator.state.next_stage == OrchestrationStage.CLARIFICATION_LIFECYCLE:
                orchestrator.stage_clarification_lifecycle()

            evidence_refs = tuple(item.evidence_id for item in evidence_coordinator.ordered_view())
            clarification_refs = tuple(c.clarification_id for c in clarification_controller.history())

            new_seq = record.transition_sequence_number
            if orchestrator.state.next_stage == OrchestrationStage.PREVIEW_CONSTRUCTION:
                if session.session_state is SessionState.DECISION_SELECTED:
                    new_seq = record.transition_sequence_number + 1
                    result = TransitionEngine().apply(
                        session,
                        SessionState.AWAITING_CONFIRMATION,
                        sequence_number=new_seq,
                        previous_sequence_number=record.transition_sequence_number or None,
                    )
                    self.persist_session(result.session)

                preview, digest = orchestrator.stage_preview_construction(
                    preview_id=f"prev-{uuid.uuid4().hex}",
                    preview_timestamp=_now_iso(),
                    transition_sequence_number=new_seq,
                    evidence_refs=evidence_refs,
                    clarification_refs=clarification_refs,
                    audit_refs=(),
                    transition_summary=f"Preview for session {session_id}.",
                    rendered_content=_render_preview_content(session, evidence_refs, clarification_refs),
                )
                orchestrator.stage_preview_validation(preview)
            else:
                if record.last_preview is None:
                    raise SessionInvalidTransitionApplicationError(
                        f"Session {session_id!r}'s orchestration record has no cached "
                        "Preview to re-render, despite Preview Construction already "
                        "having completed; the orchestration record is corrupted.",
                        session_id=session_id,
                    )
                cached = _preview_from_payload(record.last_preview)
                preview, digest = preview_builder.build(
                    preview_id=cached.preview_id,
                    session_id=session_id,
                    preview_timestamp=cached.preview_timestamp,
                    transition_sequence_number=cached.transition_sequence_number,
                    evidence_refs=evidence_refs,
                    clarification_refs=clarification_refs,
                    audit_refs=(),
                    transition_summary=cached.transition_summary,
                    rendered_content=cached.rendered_content,
                )

            new_record = OrchestrationRecord(
                session_id=session_id,
                completed_stages=tuple(stage.value for stage in orchestrator.state.completed_stages),
                transition_sequence_number=new_seq,
                evidence=record.evidence,
                clarifications=record.clarifications,
                confirmation_requests=record.confirmation_requests,
                confirmation_responses=record.confirmation_responses,
                last_preview=_preview_to_payload(preview),
                cancellation=record.cancellation,
            )
            self._persist_orchestration(new_record)
            return preview, digest

        return self._run_orchestration_body(session_id, body)

    # -- decision-session confirm (IWPC-REQ-020/021) ------------------------

    def record_confirmation(
        self, session_id: str, preview_digest: str, statement: str, *, caller_identity: str
    ) -> Session:
        """Perform Confirmation for a session in ``AwaitingConfirmation``,
        transitioning it to ``Confirmed`` (single-use, IWPC-REQ-021)."""

        session = self.load_session(session_id)
        self._require_bound_identity(session, caller_identity)
        if session.session_state is not SessionState.AWAITING_CONFIRMATION:
            raise SessionInvalidTransitionApplicationError(
                f"Session {session_id!r} is in state {session.session_state.value!r}; "
                "confirm requires a session in state 'AwaitingConfirmation'.",
                session_id=session_id,
            )

        def body() -> Session:
            record = self._load_orchestration(session_id)
            if record.last_preview is None:
                raise SessionConfirmationConflictApplicationError(
                    f"No Preview has been generated yet for session {session_id!r}; "
                    "run 'decision-session preview' before 'confirm'.",
                    session_id=session_id,
                )
            if record.confirmation_responses:
                raise SessionConfirmationConflictApplicationError(
                    f"Session {session_id!r} already has an accepted Confirmation; "
                    "Confirmation is single-use.",
                    session_id=session_id,
                )

            (
                orchestrator,
                evidence_coordinator,
                clarification_controller,
                confirmation_controller,
                preview_builder,
            ) = _rehydrate_collaborators(session_id, record)

            cached = _preview_from_payload(record.last_preview)
            evidence_refs = tuple(item.evidence_id for item in evidence_coordinator.ordered_view())
            clarification_refs = tuple(c.clarification_id for c in clarification_controller.history())
            live_preview, live_digest = preview_builder.build(
                preview_id=cached.preview_id,
                session_id=session_id,
                preview_timestamp=cached.preview_timestamp,
                transition_sequence_number=cached.transition_sequence_number,
                evidence_refs=evidence_refs,
                clarification_refs=clarification_refs,
                audit_refs=(),
                transition_summary=cached.transition_summary,
                rendered_content=cached.rendered_content,
            )

            if preview_digest != live_digest:
                raise SessionConfirmationConflictApplicationError(
                    f"Supplied --preview-digest does not match session "
                    f"{session_id!r}'s current live Preview Digest.",
                    session_id=session_id,
                )

            now = _now_iso()
            request_id = f"cnf-req-{uuid.uuid4().hex}"
            response_id = f"cnf-res-{uuid.uuid4().hex}"
            request = ConfirmationRequest(
                request_id=request_id,
                session_id=session_id,
                preview_id=live_preview.preview_id,
                preview_digest=live_digest,
                created_at=now,
            )
            orchestrator.stage_confirmation_request(request)

            response = ConfirmationResponse(
                response_id=response_id,
                request_id=request_id,
                confirmed_at=now,
                confirmation_result=ConfirmationResult.ACCEPTED,
                preview_digest=live_digest,
                metadata={"statement": statement},
            )
            orchestrator.stage_confirmation_validation(
                request_id, response, live_preview, record.transition_sequence_number
            )

            new_seq = record.transition_sequence_number + 1
            result = TransitionEngine().apply(
                session,
                SessionState.CONFIRMED,
                sequence_number=new_seq,
                previous_sequence_number=record.transition_sequence_number or None,
            )
            updated_session = result.session

            if orchestrator.state.next_stage == OrchestrationStage.TERMINAL_COMPLETION:
                orchestrator.stage_terminal_completion(updated_session)

            new_record = OrchestrationRecord(
                session_id=session_id,
                completed_stages=tuple(stage.value for stage in orchestrator.state.completed_stages),
                transition_sequence_number=new_seq,
                evidence=record.evidence,
                clarifications=record.clarifications,
                confirmation_requests=record.confirmation_requests
                + (
                    {
                        "request_id": request_id,
                        "preview_id": live_preview.preview_id,
                        "preview_digest": live_digest,
                        "created_at": now,
                    },
                ),
                confirmation_responses=record.confirmation_responses
                + (
                    {
                        "response_id": response_id,
                        "request_id": request_id,
                        "confirmed_at": now,
                        "confirmation_result": ConfirmationResult.ACCEPTED.value,
                        "preview_digest": live_digest,
                        "metadata": {"statement": statement},
                    },
                ),
                last_preview=_preview_to_payload(live_preview),
                cancellation=record.cancellation,
            )
            self._persist_orchestration(new_record)
            self.persist_session(updated_session)
            return updated_session

        return self._run_orchestration_body(session_id, body)

    # -- decision-session cancel (IWPC-REQ-025) ------------------------------

    def cancel_session(self, session_id: str, reason: str, *, caller_identity: str) -> Session:
        """Terminate a session before Confirmation. Idempotent by key
        (IWPC-REQ-025): a second call against an already-``Cancelled``
        session returns the existing cancellation, rather than failing.

        Identity is enforced before this idempotent early-return (Phase
        145G.3): a mismatched identity is rejected even against an
        already-``Cancelled`` session, so identity mismatch can never
        present as an idempotent success."""

        session = self.load_session(session_id)
        self._require_bound_identity(session, caller_identity)
        if session.session_state is SessionState.CANCELLED:
            return session
        if session.is_terminal():
            raise SessionInvalidTransitionApplicationError(
                f"Session {session_id!r} is in a terminal state "
                f"({session.session_state.value!r}) other than 'Cancelled'; it "
                "cannot be cancelled.",
                session_id=session_id,
            )

        def body() -> Session:
            record = self._load_orchestration(session_id)
            new_seq = record.transition_sequence_number + 1
            result = TransitionEngine().apply(
                session,
                SessionState.CANCELLED,
                sequence_number=new_seq,
                previous_sequence_number=record.transition_sequence_number or None,
                reason=reason,
            )
            updated_session = result.session

            new_record = OrchestrationRecord(
                session_id=session_id,
                completed_stages=record.completed_stages,
                transition_sequence_number=new_seq,
                evidence=record.evidence,
                clarifications=record.clarifications,
                confirmation_requests=record.confirmation_requests,
                confirmation_responses=record.confirmation_responses,
                last_preview=record.last_preview,
                cancellation={"reason": reason, "cancelled_at": updated_session.updated_at},
            )
            self._persist_orchestration(new_record)
            self.persist_session(updated_session)
            return updated_session

        return self._run_orchestration_body(session_id, body)

    # -- decision-session readiness construction (IWPC-REQ-024) -------------

    def evaluate_authority_stage_1(self, session_id: str) -> Optional[Stage1EvaluationResult]:
        """Advisory-only Stage 1 Authority Evaluation (AESIC-001 v1.3 §9.1).

        Returns ``None``, performing no evaluation, when no Authority
        Evaluation Service collaborator was configured at construction
        time -- preserving existing workflow behavior when Authority
        Evaluation is absent (AESIC-001 §19). Never gates, blocks, or
        auto-selects a transition (AESIC-REQ-091): the caller decides how,
        or whether, to surface the returned advisory result, and MAY
        discard it (§9.1)."""

        if self._authority_evaluation_service is None:
            return None
        session = self.load_session(session_id)
        return self._authority_evaluation_service.evaluate_stage_1(session=session)

    def construct_readiness_package(
        self,
        session_id: str,
        *,
        caller_identity: str,
        stage_1_result: Optional[Stage1EvaluationResult] = None,
    ) -> PublicationReadinessPackage:
        """Construct (never persist -- that remains
        ``PublicationApplicationService.persist_readiness_package``'s own
        responsibility) an immutable ``PublicationReadinessPackage`` for a
        ``Confirmed`` session whose orchestration is complete, via the
        existing, unmodified ``PublicationHandoff.build_package``.

        Enforces identity-bound resumption (Phase 145G.3): ``readiness``
        continues the session's own workflow toward publication, so it is
        treated as "resumption" under IWC-REQ-022/IWC-REQ-151 exactly like
        the other mutating commands, even though it does not itself mutate
        ``Session`` (see ``run_decision_session_readiness`` for why the CLI
        also enforces this ahead of ``ensure_readiness_package``, which has
        no identity input of its own)."""

        session = self.load_session(session_id)
        self._require_bound_identity(session, caller_identity)
        if session.session_state is not SessionState.CONFIRMED:
            raise ReadinessSessionNotConfirmedApplicationError(
                f"Session {session_id!r} is not Confirmed "
                f"({session.session_state.value!r}); a readiness package can only "
                "be constructed for a Confirmed session.",
                session_id=session_id,
            )

        def body() -> PublicationReadinessPackage:
            record = self._load_orchestration(session_id)
            (
                orchestrator,
                evidence_coordinator,
                clarification_controller,
                confirmation_controller,
                _preview_builder,
            ) = _rehydrate_collaborators(session_id, record)

            if (
                not orchestrator.state.is_complete()
                or record.last_preview is None
                or not record.confirmation_requests
                or not record.confirmation_responses
            ):
                raise ReadinessSessionNotConfirmedApplicationError(
                    f"Session {session_id!r}'s orchestration is not yet complete "
                    f"(next stage: {orchestrator.state.next_stage!r}); a readiness "
                    "package cannot be constructed until 'confirm' has completed.",
                    session_id=session_id,
                )

            preview = _preview_from_payload(record.last_preview)
            confirmation_request = confirmation_controller.request_history()[-1]
            confirmation_response = confirmation_controller.response_history()[-1]
            evidence_refs = tuple(item.evidence_id for item in evidence_coordinator.ordered_view())
            clarification_refs = tuple(c.clarification_id for c in clarification_controller.history())

            package_id = f"prp-{uuid.uuid4().hex}"

            # AESIC-001 v1.3 §9.3/§21, AESIC-REQ-067: Stage 2 runs here,
            # immediately before CHGR construction and strictly outside
            # the Publication Coordinator's own execute() transaction --
            # never inside it. Absent a configured service, this is a
            # byte-for-byte no-op (both fields stay None, AESIC-REQ-109).
            authority_evaluation_ref = None
            citation_text = None
            if self._authority_evaluation_service is not None:
                aer = self._authority_evaluation_service.evaluate_stage_2(
                    session=session,
                    package_id=package_id,
                    stage_1_result=stage_1_result,
                )
                # Only the AER's own citation_text flows forward, verbatim,
                # into CHGR (AESIC-REQ-058); the reference names identity
                # only -- never the AER's payload inline (AESIC-REQ-059).
                if aer.outcome.citation_text:
                    authority_evaluation_ref = {
                        "record_id": aer.record_id,
                        "record_digest": aer_to_payload(aer)["record_digest"],
                        "record_family": aer.record_family,
                    }
                    citation_text = aer.outcome.citation_text

            return PublicationHandoff().build_package(
                package_id=package_id,
                session=session,
                orchestration_state=orchestrator.state,
                transition_sequence_number=record.transition_sequence_number,
                evidence_refs=evidence_refs,
                clarification_refs=clarification_refs,
                audit_refs=(),
                preview=preview,
                confirmation_request=confirmation_request,
                confirmation_response=confirmation_response,
                built_at=_now_iso(),
                authority_evaluation_ref=authority_evaluation_ref,
                citation_text=citation_text,
            )

        return self._run_orchestration_body(session_id, body)


__all__ = ["SessionApplicationService"]
