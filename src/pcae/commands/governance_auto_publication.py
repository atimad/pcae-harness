"""Governed Capability Consumption Integration -- Interactive Workflow
auto-detect + route, Publication Execution Ownership auto-invocation, and
CHGR downstream automatic consumption (Phase 149O.20L.7O.3C.2).

This module is a thin, additive production-service seam over the already-
existing, already-frozen application-service layer (Phase 145F's
``SessionApplicationService``/``PublicationApplicationService``, composed
by ``pcae.commands.decision_session.build_application_context``). It
constructs no ``SessionCoordinator``, ``WorkflowOrchestrator``, or
``PublicationCoordinator`` of its own -- it consumes the identical
composition root the ``decision-session``/``governance-record`` CLI
commands already use, so a caller invoking this module and a human typing
the equivalent CLI sequence by hand reach the exact same production
service state.

**What this module removes:** the requirement that a PCAE production
workflow (today: ``pcae phase complete``) know or perform, by hand, the
internal command choreography of ``decision-session readiness`` followed
by ``governance-record publish`` once a human has already driven a
Confirmable Decision Session through to ``Confirmed`` for that workflow's
subject. **What this module never does:** confirm a session, select a
decision, answer a clarification, or otherwise stand in for the human
authority boundary (IWC-001 v1.1's session-state model, unchanged) -- see
``AutoPublicationOutcome`` for the full closed vocabulary of non-terminal
outcomes this module reports rather than silently working around.

**Detection is not a new heuristic.** ``find_confirmed_session`` performs
a full-scan, exact-identity match over every persisted session's
``subject_ref`` field (via ``SessionRepository.list_session_ids`` +
``load``) -- deterministic and order-independent, never a "most recent
file" or timestamp-based guess (3C.2 phase brief §13's discovery
prohibition applies identically to the session lookup that feeds CHGR
discovery, not only to a hypothetical direct CHGR index). The convention
this module establishes -- ``subject_ref == <the PCAE task_id a governed
operation is scoped to>`` -- is additive: it does not require every
session to follow it (a session created with an unrelated ``subject_ref``
is simply never matched, exactly as if this module did not exist), and it
does not change ``decision-session create``'s existing free-text
``--subject-ref`` contract in any way.

**Zone placement:** this module lives in the ``commands`` zone, not
``interactive_workflow``, even though its subject is Interactive
Workflow/Publication orchestration. ``.pcae/policy.toml``'s frozen
``interactive_workflow`` zone rule (Phase 143K) forbids that zone from
depending on ``core`` in either direction, and this module must call the
Permission Broker adapter (``pcae.core.mutation_permission``, via
``pcae.commands.publication_permission_gate``) to close the CHGR/
publication-path gap (3C.1 §7.3/§10) -- exactly the dependency shape
``commands`` already exists for (see ``commands/decision_session.py``,
which combines ``core``/``interactive_workflow`` the same way).
"""
from __future__ import annotations

import dataclasses
from typing import Optional

from pcae.commands.publication_permission_gate import publish_with_permission_gate
from pcae.core.paths import HarnessPath
from pcae.governance.publication.models import PublicationExecutionResult
from pcae.interactive_workflow.application.errors import (
    ApplicationServiceError,
    PublicationAlreadyCompletedApplicationError,
    PublicationPermissionDeniedApplicationError,
    ReadinessSessionNotConfirmedApplicationError,
)
from pcae.interactive_workflow.models.session import Session, SessionState

# -- Closed outcome-status vocabulary (uses existing Session/State names,
# invents no alias per phase brief §8) -------------------------------------

STATUS_NO_SESSION = "no_session_bound"
"""No session exists whose ``subject_ref`` matches the requested subject.
Not a failure: most PCAE operations have no bound governance decision at
all, and this module must be a safe no-op for every one of them."""

STATUS_AWAITING_HUMAN_DECISION = "awaiting_human_decision"
"""A session exists, but its ``session_state`` is one of the seven
non-terminal, non-``Confirmed`` states (``Created``, ``EvidenceReady``,
``AwaitingDecision``, ``AwaitingClarification``, ``DecisionSelected``,
``AwaitingConfirmation``) -- the human has not yet finished driving the
existing Interactive Workflow CLI through to confirmation. The exact
``session_state`` is surfaced verbatim (no PCAE-invented alias) so a
calling workflow can disclose precisely what remains."""

STATUS_HUMAN_REJECTED = "human_rejected"
"""The bound session reached ``Cancelled``. No CHGR is created; the
calling PCAE workflow must not treat this as ``no_session_bound``."""

STATUS_HUMAN_DEFERRED = "human_deferred"
"""The bound session reached ``Abandoned``. No CHGR is created."""

STATUS_READINESS_UNAVAILABLE = "readiness_unavailable"
"""The bound session reached ``Expired`` before a readiness package could
be built/consumed. No CHGR is created; a fresh session is required."""

STATUS_PERMISSION_DENIED = "permission_denied"
"""Permission Broker (via ``PublicationApplicationService.hand_off``'s
own gate, Phase 149O.20L.7O.3C.2) did not authorize this publication
attempt -- policy ``DENY`` or a broker construction/evaluation failure.
No CHGR is created."""

STATUS_ALREADY_PUBLISHED = "already_published"
"""The session's readiness package was already consumed by a prior,
successful Publication Execution -- this attempt performed no new
publication and created no new CHGR. ``record_id``/``package_id`` name
the *original* CHGR (duplicate-CHGR prevention, IWPC-001's own existing
idempotency-by-key invariant, consumed here rather than reimplemented)."""

STATUS_PUBLISHED = "published"
"""This attempt itself performed the Publication Execution and a new CHGR
now exists in canonical storage. ``record_id`` names it."""

STATUS_APPLICATION_ERROR = "application_error"
"""An ``ApplicationServiceError`` not covered by a more specific status
above was raised (e.g. a corrupt persisted store). The calling workflow
must not silently continue; ``diagnostic`` carries the sanitized message
the application-service boundary already produced."""

CLOSED_STATUS_VOCABULARY = frozenset(
    {
        STATUS_NO_SESSION,
        STATUS_AWAITING_HUMAN_DECISION,
        STATUS_HUMAN_REJECTED,
        STATUS_HUMAN_DEFERRED,
        STATUS_READINESS_UNAVAILABLE,
        STATUS_PERMISSION_DENIED,
        STATUS_ALREADY_PUBLISHED,
        STATUS_PUBLISHED,
        STATUS_APPLICATION_ERROR,
    }
)

_NON_TERMINAL_STATES = (
    SessionState.CREATED,
    SessionState.EVIDENCE_READY,
    SessionState.AWAITING_DECISION,
    SessionState.AWAITING_CLARIFICATION,
    SessionState.DECISION_SELECTED,
    SessionState.AWAITING_CONFIRMATION,
)


@dataclasses.dataclass(frozen=True)
class AutoPublicationOutcome:
    """The structured, typed result of one auto-routing attempt
    (§38/§39 of the governing phase brief: never a text-parsed result,
    never a status the calling workflow can mistake for success by
    accident -- ``status`` is always one of ``CLOSED_STATUS_VOCABULARY``,
    and only ``already_published``/``published`` carry a real
    ``record_id``)."""

    status: str
    subject_ref: str
    session_id: Optional[str] = None
    session_state: Optional[str] = None
    package_id: Optional[str] = None
    record_id: Optional[str] = None
    diagnostic: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status not in CLOSED_STATUS_VOCABULARY:
            raise ValueError(f"Unknown AutoPublicationOutcome.status {self.status!r}.")


def find_confirmed_session(session_service, subject_ref: str) -> Optional[Session]:
    """Thin alias for ``SessionApplicationService.find_session_by_subject_ref``
    (which owns the actual deterministic full-scan-by-identity lookup --
    see its docstring), kept as a module-level function here so callers
    of this module do not need to know the application-service method
    name changed across phases."""

    return session_service.find_session_by_subject_ref(subject_ref)


def auto_publish_confirmed_session(
    context,
    *,
    subject_ref: str,
    operator_id: str,
) -> AutoPublicationOutcome:
    """The single production entry point Interactive Workflow auto-
    detect + route and Publication Execution Ownership auto-invocation
    both consume (3C.1 §16: "same work, not a separate dependency").

    ``context`` is an ``ApplicationContext`` from
    ``pcae.commands.decision_session.build_application_context()`` --
    supplied by the caller (constructor injection, matching every other
    collaborator in this codebase) rather than constructed here, so a
    calling production workflow and the CLI commands share exactly one
    composition root per process, and a test can supply an isolated one.

    Idempotent and safe to call repeatedly (§10/§45 "repeated invocation
    idempotent"): a second call after a first successful ``published``
    outcome returns ``already_published`` with the same ``record_id``,
    never a second CHGR. A call when no session is bound is a pure no-op
    (``no_session_bound``) -- this is what makes it safe to invoke
    unconditionally from a production workflow that does not know in
    advance whether a governance decision applies to it.
    """

    try:
        session = find_confirmed_session(context.session_service, subject_ref)
    except ApplicationServiceError as exc:
        # Phase 149O.20L.7O.3C.3.1: a corrupt/unreadable session record
        # anywhere in the store (translated by
        # ``SessionApplicationService.find_session_by_subject_ref`` into
        # this already-existing application-error taxonomy) must not
        # crash this caller -- surfaced as `application_error`, the same
        # closed status the publish path below already uses for every
        # other ``ApplicationServiceError``, never silently treated as
        # `no_session_bound` (that would launder possibly-relevant
        # corruption into "no governance state exists").
        return AutoPublicationOutcome(
            status=STATUS_APPLICATION_ERROR,
            subject_ref=subject_ref,
            diagnostic=str(exc),
        )
    if session is None:
        return AutoPublicationOutcome(status=STATUS_NO_SESSION, subject_ref=subject_ref)

    if session.session_state in _NON_TERMINAL_STATES:
        return AutoPublicationOutcome(
            status=STATUS_AWAITING_HUMAN_DECISION,
            subject_ref=subject_ref,
            session_id=session.session_id,
            session_state=session.session_state.value,
        )
    if session.session_state is SessionState.CANCELLED:
        return AutoPublicationOutcome(
            status=STATUS_HUMAN_REJECTED,
            subject_ref=subject_ref,
            session_id=session.session_id,
            session_state=session.session_state.value,
        )
    if session.session_state is SessionState.ABANDONED:
        return AutoPublicationOutcome(
            status=STATUS_HUMAN_DEFERRED,
            subject_ref=subject_ref,
            session_id=session.session_id,
            session_state=session.session_state.value,
        )
    if session.session_state is SessionState.EXPIRED:
        return AutoPublicationOutcome(
            status=STATUS_READINESS_UNAVAILABLE,
            subject_ref=subject_ref,
            session_id=session.session_id,
            session_state=session.session_state.value,
        )

    # SessionState.CONFIRMED -- the one state in which readiness
    # construction/publication may proceed (mirrors
    # `PublicationApplicationService.persist_readiness_package`'s own,
    # unmodified precondition check).
    try:
        record = context.publication_service.ensure_readiness_package(
            session.session_id, caller_identity=operator_id
        )
        result: PublicationExecutionResult = publish_with_permission_gate(
            context.publication_service,
            HarnessPath.cwd(),
            record.package_id,
            operator_id=operator_id,
        )
    except PublicationAlreadyCompletedApplicationError as exc:
        return AutoPublicationOutcome(
            status=STATUS_ALREADY_PUBLISHED,
            subject_ref=subject_ref,
            session_id=session.session_id,
            session_state=session.session_state.value,
            package_id=exc.package_id,
            record_id=exc.record_id,
        )
    except PublicationPermissionDeniedApplicationError as exc:
        return AutoPublicationOutcome(
            status=STATUS_PERMISSION_DENIED,
            subject_ref=subject_ref,
            session_id=session.session_id,
            session_state=session.session_state.value,
            package_id=exc.package_id,
            diagnostic=str(exc),
        )
    except ReadinessSessionNotConfirmedApplicationError as exc:
        # Defensive only: the state check above already restricts this
        # branch to `CONFIRMED` sessions, so this should be unreachable
        # in practice; surfaced as `application_error` (never silently
        # swallowed) rather than assumed impossible, per the phase
        # brief's own "must not silently continue" rule (§39).
        return AutoPublicationOutcome(
            status=STATUS_APPLICATION_ERROR,
            subject_ref=subject_ref,
            session_id=session.session_id,
            session_state=session.session_state.value,
            diagnostic=str(exc),
        )
    except ApplicationServiceError as exc:
        return AutoPublicationOutcome(
            status=STATUS_APPLICATION_ERROR,
            subject_ref=subject_ref,
            session_id=session.session_id,
            session_state=session.session_state.value,
            package_id=exc.package_id,
            diagnostic=str(exc),
        )

    if not result.success:
        # `resume_publication`/`hand_off` raise on every other failure
        # path already handled above; a structurally unsuccessful result
        # reaching here without a raised exception would itself be a
        # contract violation of the existing `PublicationExecutionResult`
        # shape, so it is surfaced rather than assumed impossible.
        return AutoPublicationOutcome(
            status=STATUS_APPLICATION_ERROR,
            subject_ref=subject_ref,
            session_id=session.session_id,
            session_state=session.session_state.value,
            package_id=result.package_id,
            diagnostic="; ".join(result.diagnostics) or "Publication execution reported failure.",
        )

    return AutoPublicationOutcome(
        status=STATUS_PUBLISHED,
        subject_ref=subject_ref,
        session_id=session.session_id,
        session_state=SessionState.CONFIRMED.value,
        package_id=result.package_id,
        record_id=result.record_id,
    )


__all__ = [
    "STATUS_NO_SESSION",
    "STATUS_AWAITING_HUMAN_DECISION",
    "STATUS_HUMAN_REJECTED",
    "STATUS_HUMAN_DEFERRED",
    "STATUS_READINESS_UNAVAILABLE",
    "STATUS_PERMISSION_DENIED",
    "STATUS_ALREADY_PUBLISHED",
    "STATUS_PUBLISHED",
    "STATUS_APPLICATION_ERROR",
    "CLOSED_STATUS_VOCABULARY",
    "AutoPublicationOutcome",
    "find_confirmed_session",
    "auto_publish_confirmed_session",
]
