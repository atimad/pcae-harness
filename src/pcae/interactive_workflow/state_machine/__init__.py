"""State Machine (Phase 143K structural skeleton + Phase 143L Transition
Engine).

Phase 143K implemented the *structural* half: the ten-state definitions
and the widened transition table as data (``transitions.py``), plus a
pure transition-legality predicate, with no orchestration and no
persistence side effect. Phase 143L adds the transition *engine* itself
(``engine.py``) -- executing a transition against an in-memory ``Session``
and producing a ``TransitionResult`` -- plus its supporting Transition
Registry (``registry.py``, an inspectable wrapper over the same table),
Transition Validator (``validator.py``), Transition Policy
(``policy.py``, sequence monotonicity), and transition metadata model
(``metadata.py``). Persisting the result, driving resumability/timeout
evaluation, and all other workflow orchestration remain out of scope for
this package (deferred to the Session Coordinator and later phases,
Phase 143J §17).
"""

from __future__ import annotations

from pcae.interactive_workflow.state_machine.engine import TransitionEngine, TransitionResult
from pcae.interactive_workflow.state_machine.metadata import TransitionMetadata
from pcae.interactive_workflow.state_machine.policy import TransitionPolicy
from pcae.interactive_workflow.state_machine.registry import TransitionRegistry
from pcae.interactive_workflow.state_machine.transitions import (
    TRANSITION_TABLE,
    is_valid_transition,
    permitted_exits,
)
from pcae.interactive_workflow.state_machine.validator import TransitionValidator

__all__ = [
    "TRANSITION_TABLE",
    "is_valid_transition",
    "permitted_exits",
    "TransitionEngine",
    "TransitionResult",
    "TransitionMetadata",
    "TransitionPolicy",
    "TransitionRegistry",
    "TransitionValidator",
]
