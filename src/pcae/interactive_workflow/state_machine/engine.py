"""Transition Engine (Phase 143L).

The sole production owner of legal transition determination, illegal
transition rejection, terminal-state enforcement, transition invariant
enforcement, and deterministic transition errors (IWC-001 v1.1 §4.4,
Phase 143J §5.4). The Session Coordinator (``pcae.interactive_workflow.
session.coordinator``) remains responsible only for orchestration; it does
not, and after this phase must not, re-implement any transition rule.

``TransitionEngine.apply`` modifies only the in-memory ``Session`` model it
is given (``Session`` is a frozen dataclass, so "modify" means "return a
new instance" -- the original is never mutated). It performs no evidence
collection, no clarification, no confirmation, no publication, and no
persistence write; those remain the responsibility of components this
phase does not implement (Evidence Coordinator, Clarification Controller,
Confirmation Engine, Publication Handoff, Session Coordinator/
SessionRepository respectively).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from pcae.interactive_workflow.errors import InvalidTransitionError, TransitionError
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.state_machine.metadata import TransitionMetadata
from pcae.interactive_workflow.state_machine.policy import TransitionPolicy
from pcae.interactive_workflow.state_machine.registry import TransitionRegistry
from pcae.interactive_workflow.state_machine.validator import TransitionValidator

# ``pcae.interactive_workflow.validation.invariants`` itself imports
# ``pcae.interactive_workflow.state_machine.transitions`` (for
# ``is_valid_transition``), which -- because ``state_machine/__init__.py``
# eagerly re-exports this module's own ``TransitionEngine`` -- would create
# a circular import if this module imported ``validate_version`` at module
# load time. Deferred (function-scope) import breaks the cycle without
# weakening version enforcement: ``apply`` still calls ``validate_version``
# on every invocation, before any other check.


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class TransitionResult:
    """The outcome of a single successful ``TransitionEngine.apply`` call:
    the resulting ``Session`` (a new instance; identity and version
    preserved from the input) and the ``TransitionMetadata`` describing
    the change."""

    session: Session
    metadata: TransitionMetadata


class TransitionEngine:
    """Determines transition legality and applies legal transitions to an
    in-memory ``Session``.

    Constructed with an explicit registry/validator/policy (dependency
    injection, mirroring the Session Coordinator's own constructor-
    injected ``SessionRepository`` from Phase 143K) -- defaults are
    provided for convenience but every collaborator can be substituted,
    e.g. for test isolation.
    """

    def __init__(
        self,
        registry: Optional[TransitionRegistry] = None,
        validator: Optional[TransitionValidator] = None,
        policy: Optional[TransitionPolicy] = None,
    ) -> None:
        self._registry = registry or TransitionRegistry()
        self._validator = validator or TransitionValidator(self._registry)
        self._policy = policy or TransitionPolicy()

    def is_legal(self, session: Session, target_state: SessionState) -> bool:
        """Return whether ``target_state`` is a legal exit from
        ``session``'s current state. Never raises: any condition that
        would make ``apply`` raise a ``TransitionError`` here simply
        yields ``False``. Does not evaluate sequence-number policy, since
        legality here concerns state topology only, not call history."""

        try:
            self._validator.validate(session, target_state)
        except TransitionError:
            return False
        return True

    def apply(
        self,
        session: Session,
        target_state: SessionState,
        *,
        sequence_number: int,
        previous_sequence_number: Optional[int] = None,
        reason: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> TransitionResult:
        """Validate and apply a single transition.

        Raises a ``TransitionError`` subclass (deterministically, with no
        partial mutation -- ``session`` is never touched, and no
        ``TransitionResult`` is constructed) on any illegal input.
        Argument order of operations is fixed: malformed-session check,
        then version compatibility, then transition legality, then
        sequence-number policy -- so a given illegal input always raises
        the same error, satisfying the fail-closed/determinism
        requirements together.
        """

        from pcae.interactive_workflow.validation.invariants import validate_version

        current_state, schema_version, session_id = self._read_required_fields(session)

        validate_version(schema_version)
        self._validator.validate(session, target_state)
        self._policy.validate_sequence(previous_sequence_number, sequence_number)

        applied_at = timestamp or _now_iso()
        new_session = session.with_state(target_state, applied_at)

        if new_session.session_id != session_id:
            raise InvalidTransitionError(
                "Transition Engine invariant violated: session identity changed "
                "across a transition."
            )

        metadata = TransitionMetadata(
            session_id=session_id,
            previous_state=current_state,
            new_state=target_state,
            transition_timestamp=applied_at,
            transition_sequence_number=sequence_number,
            transition_reason=reason,
        )
        return TransitionResult(session=new_session, metadata=metadata)

    @staticmethod
    def _read_required_fields(session: Session):
        try:
            return session.session_state, session.schema_version, session.session_id
        except AttributeError as exc:
            raise InvalidTransitionError(f"Malformed session: {exc}") from exc


__all__ = ["TransitionEngine", "TransitionResult"]
