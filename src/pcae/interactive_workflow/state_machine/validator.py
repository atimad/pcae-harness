"""Transition Validator (Phase 143L).

The sole place production code determines whether a single proposed
``source -> target`` transition is legal. Every check fails closed: the
first violated rule raises immediately, no partial acceptance, no
best-effort continuation. The Transition Engine (``engine.py``) is this
validator's only production caller -- no other module re-implements these
checks (Phase 143L governing prompt, "Architectural Ownership": "No
transition rules may exist outside the Transition Engine").
"""

from __future__ import annotations

from typing import Optional

from pcae.interactive_workflow.errors import (
    DuplicateTransitionError,
    TerminalStateViolationError,
    UnknownStateError,
    UnsupportedTransitionError,
)
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.state_machine.registry import TransitionRegistry


class TransitionValidator:
    """Validates a single proposed transition against the Transition
    Registry. Stateless aside from its (shared, read-only) registry
    reference."""

    def __init__(self, registry: Optional[TransitionRegistry] = None) -> None:
        self._registry = registry or TransitionRegistry()

    def validate(self, session: Session, target_state: SessionState) -> None:
        """Raise a ``TransitionError`` subclass unless
        ``session.session_state -> target_state`` is legal. Checks run in
        a fixed order so the same illegal input always raises the same
        error type (determinism, Phase 143L "Determinism"):

        1. unknown source/target state (``UnknownStateError``)
        2. duplicate/no-op transition (``DuplicateTransitionError``)
        3. exit from a terminal state (``TerminalStateViolationError``)
        4. any other transition absent from the registry
           (``UnsupportedTransitionError``)
        """

        current_state = session.session_state
        self._require_known_state(current_state, "current")
        self._require_known_state(target_state, "target")

        if target_state == current_state:
            raise DuplicateTransitionError(
                f"{current_state.value} -> {target_state.value} is a duplicate "
                "transition (target equals current state)."
            )

        if self._registry.is_terminal(current_state):
            raise TerminalStateViolationError(
                f"{current_state.value} is terminal and admits no exit "
                f"(attempted transition to {target_state.value})."
            )

        if not self._registry.is_registered(current_state, target_state):
            raise UnsupportedTransitionError(
                f"{current_state.value} -> {target_state.value} is not a permitted "
                "transition (IWC-001 v1.1 §4.4)."
            )

    @staticmethod
    def _require_known_state(state: object, label: str) -> None:
        if not isinstance(state, SessionState):
            raise UnknownStateError(f"{label} state {state!r} is not a known SessionState.")


__all__ = ["TransitionValidator"]
