"""The ten-state transition table as data (IWC-001 v1.1 §4.4, widened by
Phase 143I.1; independently verified by Phase 143I.2).

The table is the code -- rows exist as a plain mapping, not an ``if``/
``elif`` chain, so a state-machine test suite can enumerate every row
programmatically instead of hand-duplicating it (Phase 143J §15, and the
same principle applied to IWC-001 itself in Phase 143I.1's own repair,
which widened the table specifically because a prose/table divergence had
gone undetected).

No state may be added, removed, merged, or renamed here (IWC-REQ-042).
Terminal states carry an explicitly empty exit set, checked structurally
below -- not inferred by absence of a table row.
"""

from __future__ import annotations

from types import MappingProxyType

from pcae.interactive_workflow.models.session import SessionState, TERMINAL_STATES

TRANSITION_TABLE: "MappingProxyType[SessionState, frozenset[SessionState]]" = MappingProxyType(
    {
        SessionState.CREATED: frozenset(
            {
                SessionState.EVIDENCE_READY,
                SessionState.CANCELLED,
                SessionState.EXPIRED,
                SessionState.ABANDONED,
            }
        ),
        SessionState.EVIDENCE_READY: frozenset(
            {
                SessionState.AWAITING_DECISION,
                SessionState.CANCELLED,
                SessionState.EXPIRED,
                SessionState.ABANDONED,
            }
        ),
        SessionState.AWAITING_DECISION: frozenset(
            {
                SessionState.AWAITING_CLARIFICATION,
                SessionState.DECISION_SELECTED,
                SessionState.EXPIRED,
                SessionState.CANCELLED,
                SessionState.ABANDONED,
            }
        ),
        SessionState.AWAITING_CLARIFICATION: frozenset(
            {
                SessionState.AWAITING_DECISION,
                SessionState.CANCELLED,
                SessionState.EXPIRED,
                SessionState.ABANDONED,
            }
        ),
        SessionState.DECISION_SELECTED: frozenset(
            {
                SessionState.AWAITING_CONFIRMATION,
                SessionState.AWAITING_DECISION,
                SessionState.CANCELLED,
                SessionState.EXPIRED,
                SessionState.ABANDONED,
            }
        ),
        SessionState.AWAITING_CONFIRMATION: frozenset(
            {
                SessionState.CONFIRMED,
                SessionState.DECISION_SELECTED,
                SessionState.CANCELLED,
                SessionState.EXPIRED,
                SessionState.ABANDONED,
            }
        ),
        SessionState.CONFIRMED: frozenset(),
        SessionState.CANCELLED: frozenset(),
        SessionState.EXPIRED: frozenset(),
        SessionState.ABANDONED: frozenset(),
    }
)

assert frozenset(TRANSITION_TABLE.keys()) == frozenset(SessionState)
assert all(
    TRANSITION_TABLE[state] == frozenset() for state in TERMINAL_STATES
), "terminal states must carry an empty exit set (IWC-001 v1.1 §4.4)"


def permitted_exits(state: SessionState) -> frozenset[SessionState]:
    """Return the set of states ``state`` may transition into.

    Pure table lookup -- no I/O, no orchestration.
    """

    return TRANSITION_TABLE[state]


def is_valid_transition(current: SessionState, target: SessionState) -> bool:
    """Structural legality check only (IWC-001 v1.1 §4.4 rule (a)/(b)).

    True iff ``target`` is a member of the ten-state model and is present
    in ``current``'s permitted-exit set. This function performs none of
    the additional invariant checks Phase 143J §5.4 assigns to the full
    transition *engine* (e.g. requiring the Confirmation Engine's
    affirmative result before accepting a transition into ``Confirmed``)
    -- those require workflow orchestration deferred to Phase 143L.
    """

    if not isinstance(current, SessionState) or not isinstance(target, SessionState):
        return False
    return target in permitted_exits(current)


__all__ = [
    "TRANSITION_TABLE",
    "permitted_exits",
    "is_valid_transition",
]
