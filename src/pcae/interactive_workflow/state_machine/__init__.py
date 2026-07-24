"""State Machine skeleton (Phase 143K; full transition engine is Phase 143L).

Phase 143J's own recommended decomposition (§17) assigns the transition
*engine* -- executing a transition, persisting the result, driving
resumability/timeout evaluation -- to Phase 143L. This module implements
only the *structural* half explicitly required by the governing 143K
prompt: the ten-state definitions and the widened transition table as
data, plus a structural transition-legality check with no orchestration,
no persistence side effect, and no workflow reasoning about *why* a
transition is desirable. This is a disclosed, deliberate narrowing of
"State Machine skeleton" to table-as-data plus a pure legality predicate --
consistent with the governing prompt's own instruction: "Do not implement
transition execution logic beyond the minimum needed to construct valid
session objects."
"""

from __future__ import annotations

from pcae.interactive_workflow.state_machine.transitions import (
    TRANSITION_TABLE,
    is_valid_transition,
    permitted_exits,
)

__all__ = [
    "TRANSITION_TABLE",
    "is_valid_transition",
    "permitted_exits",
]
