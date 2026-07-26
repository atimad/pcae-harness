"""SessionApplicationService (Phase 145F).

Coordinates ``SessionCoordinator``/``SessionRepository`` for a future
transport adapter -- session lifecycle coordination (create, load,
persist, update, completion) plus deterministic translation of every
underlying exception into this boundary's own closed application-error
taxonomy (``application.errors``). This class establishes no authority,
performs no evidence/clarification/preview/confirmation logic itself, and
never constructs a CHGR (IWPC-REQ-011: session semantics remain
``SessionCoordinator``/``WorkflowOrchestrator``'s exclusively; this class
delegates every such decision, it does not reimplement any of them).
"""
from __future__ import annotations

from pcae.interactive_workflow.application.errors import (
    InvalidSessionIdentifierApplicationError,
    SessionAlreadyExistsApplicationError,
    SessionCorruptApplicationError,
    SessionNotFoundApplicationError,
    SessionNotTerminalApplicationError,
    SessionPersistenceUnavailableApplicationError,
)
from pcae.interactive_workflow.errors import (
    InvalidIdentifierError,
    PersistenceUnavailableError,
    SessionAlreadyExistsError,
    SessionNotFoundError,
    SessionStoreCorruptError,
)
from pcae.interactive_workflow.models.session import Session
from pcae.interactive_workflow.session.coordinator import SessionCoordinator


class SessionApplicationService:
    """Application-layer coordination over ``SessionCoordinator``.

    Constructed with an explicit ``SessionCoordinator`` (dependency
    injection, mirroring ``SessionCoordinator``'s own constructor-injected
    ``SessionRepository`` boundary) -- this class never selects or
    constructs its own coordinator.
    """

    def __init__(self, coordinator: SessionCoordinator) -> None:
        self._coordinator = coordinator

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


__all__ = ["SessionApplicationService"]
