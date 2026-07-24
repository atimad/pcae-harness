"""Transition Registry (Phase 143L).

An inspectable, deterministic object view over the canonical widened
transition table (``pcae.interactive_workflow.state_machine.transitions``,
IWC-001 v1.1 §4.4, widened by Phase 143I.1, independently verified by
Phase 143I.2). ``TRANSITION_TABLE`` itself remains the single source of
truth -- this module adds an inspection surface for the Transition
Validator and Transition Engine to depend on, not new transition data. No
transition contractually permitted or forbidden by IWC-001 v1.1 is added,
removed, or reinterpreted here (IWC-REQ-042).
"""

from __future__ import annotations

from typing import Iterator, Tuple

from pcae.interactive_workflow.models.session import SessionState, TERMINAL_STATES
from pcae.interactive_workflow.state_machine.transitions import (
    TRANSITION_TABLE,
    is_valid_transition,
    permitted_exits,
)


class TransitionRegistry:
    """Deterministic, read-only view over the canonical transition table.

    Every method is a pure lookup against ``TRANSITION_TABLE``/
    ``TERMINAL_STATES`` -- no I/O, no mutable state, no caching that could
    diverge from the table it wraps.
    """

    def all_states(self) -> frozenset:
        """Return every state the registry knows about."""

        return frozenset(TRANSITION_TABLE.keys())

    def permitted_targets(self, source: SessionState) -> frozenset:
        """Return the set of states ``source`` may legally transition
        into. Raises ``KeyError`` if ``source`` is not a registered
        state -- callers that must not raise on unknown input should
        check membership via ``all_states()`` first (the Transition
        Validator does this)."""

        return permitted_exits(source)

    def is_registered(self, source: SessionState, target: SessionState) -> bool:
        """Return whether ``source -> target`` is a contractually
        permitted transition. ``False`` (never an exception) for any
        input outside the ten-state model."""

        return is_valid_transition(source, target)

    def is_terminal(self, state: SessionState) -> bool:
        """Return whether ``state`` is one of the four terminal states
        (no exit, IWC-001 v1.1 §4.4)."""

        return state in TERMINAL_STATES

    def all_transitions(self) -> Iterator[Tuple[SessionState, SessionState]]:
        """Yield every ``(source, target)`` pair the registry permits, in
        a deterministic order (table insertion order, then set iteration
        order per row -- stable within a single interpreter run since
        each row is a ``frozenset`` rebuilt identically every import)."""

        for source, targets in TRANSITION_TABLE.items():
            for target in sorted(targets, key=lambda state: state.value):
                yield (source, target)


__all__ = ["TransitionRegistry"]
