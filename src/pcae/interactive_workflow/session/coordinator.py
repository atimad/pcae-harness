"""Session Coordinator skeleton (Phase 143K; Phase 143J §4/§5.1).

Responsibilities in scope for this skeleton: create a session object,
load a persisted session, persist a session, validate session state, and
expose lifecycle hooks. Dependencies (``SessionRepository``) are supplied
via constructor injection -- no module-level singleton, no global
registry.

Explicitly not this class's responsibility, now or ever (Phase 143J §4
Responsibility Matrix, "Prohibited" column): orchestrating evidence,
driving workflow, creating a CHGR, performing confirmation, or performing
publication. Methods for those concerns are not merely unimplemented --
they do not exist on this class. Every method that *does* exist but whose
full behavior is out of Phase 143K's scope raises ``NotImplementedError``
deterministically rather than silently no-op-ing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, List, Optional

from pcae.interactive_workflow.errors import SessionNotFoundError
from pcae.interactive_workflow.models.session import SCHEMA_VERSION, Session, SessionState
from pcae.interactive_workflow.persistence.repository import SessionRepository
from pcae.interactive_workflow.session.identity import generate_session_id
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

    def orchestrate_evidence(self, *args, **kwargs):
        """Not implemented in Phase 143K.

        Evidence orchestration is the Evidence Coordinator's
        responsibility (Phase 143J §3, component 5), deferred to a later
        phase. This method exists only to fail deterministically rather
        than silently be absent, so a caller that reaches for it gets an
        explicit, typed refusal instead of an ``AttributeError``.
        """

        raise NotImplementedError(
            "SessionCoordinator.orchestrate_evidence is out of scope for Phase 143K "
            "(deferred to the Evidence Coordinator component)."
        )

    def perform_confirmation(self, *args, **kwargs):
        """Not implemented in Phase 143K. Deferred to the Confirmation
        Engine component (Phase 143J §3, component 3)."""

        raise NotImplementedError(
            "SessionCoordinator.perform_confirmation is out of scope for Phase 143K "
            "(deferred to the Confirmation Engine component)."
        )

    def perform_publication(self, *args, **kwargs):
        """Not implemented in Phase 143K, and never will be on this
        class -- Publication Handoff is interface-only per IWC §18.4
        (Phase 143J), with no callee assigned yet."""

        raise NotImplementedError(
            "SessionCoordinator.perform_publication is out of scope for Phase 143K "
            "(Publication Handoff has no assigned callee -- IWC-001 v1.1 §18.4)."
        )


__all__ = [
    "LifecycleHook",
    "SessionCoordinator",
]
