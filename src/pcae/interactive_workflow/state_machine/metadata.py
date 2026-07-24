"""Transition metadata model (Phase 143L).

Records the facts of a single applied transition: previous state, new
state, timestamp, an optional human-readable reason, and a strictly
monotonic sequence number. Carries the session identifier for
traceability and nothing else identity- or authority-related (Phase 143L
governing prompt, "Transition Metadata": "No authority or identity
information beyond the session identifier"). No evidence, confirmation,
or CHGR field exists on this type, now or ever, for that reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pcae.interactive_workflow.errors import InvalidTransitionError
from pcae.interactive_workflow.models.session import SessionState


@dataclass(frozen=True)
class TransitionMetadata:
    """Immutable record describing one applied transition.

    Construction-time checks are limited to structural well-formedness
    (matching ``Session``'s own ``__post_init__`` discipline); transition
    *legality* is the Transition Validator's responsibility, not this
    model's.
    """

    session_id: str
    previous_state: SessionState
    new_state: SessionState
    transition_timestamp: str
    transition_sequence_number: int
    transition_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.session_id:
            raise InvalidTransitionError("TransitionMetadata.session_id must be non-empty.")
        if not isinstance(self.previous_state, SessionState):
            raise InvalidTransitionError(
                f"TransitionMetadata.previous_state must be a SessionState member, "
                f"got {self.previous_state!r}."
            )
        if not isinstance(self.new_state, SessionState):
            raise InvalidTransitionError(
                f"TransitionMetadata.new_state must be a SessionState member, "
                f"got {self.new_state!r}."
            )
        if not self.transition_timestamp:
            raise InvalidTransitionError("TransitionMetadata.transition_timestamp must be non-empty.")
        if isinstance(self.transition_sequence_number, bool) or not isinstance(
            self.transition_sequence_number, int
        ):
            raise InvalidTransitionError(
                "TransitionMetadata.transition_sequence_number must be an int, "
                f"got {self.transition_sequence_number!r}."
            )
        if self.transition_sequence_number < 0:
            raise InvalidTransitionError(
                "TransitionMetadata.transition_sequence_number must be non-negative, "
                f"got {self.transition_sequence_number!r}."
            )
        if self.transition_reason is not None and not isinstance(self.transition_reason, str):
            raise InvalidTransitionError(
                f"TransitionMetadata.transition_reason must be a string or None, "
                f"got {self.transition_reason!r}."
            )


__all__ = ["TransitionMetadata"]
