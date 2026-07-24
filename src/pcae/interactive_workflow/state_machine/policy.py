"""Transition Policy (Phase 143L).

Encodes the fail-closed policy the Transition Engine applies uniformly to
every proposed transition: no override, no bypass flag, no
configuration-driven relaxation. ``TransitionPolicy`` exists to give this
policy an explicit, inspectable, single home distinct from the Transition
Validator's per-transition legality checks -- not to introduce a
configuration surface. There is exactly one policy; a future phase that
needs a genuinely different policy must define a new, separately named
type rather than adding a mode flag here.
"""

from __future__ import annotations

from typing import Optional

from pcae.interactive_workflow.errors import InvalidTransitionSequenceError


class TransitionPolicy:
    """Stateless sequence-monotonicity policy.

    Sequence monotonicity is the one invariant that cannot be checked by
    the Transition Validator alone, since it depends on the transition
    *history* rather than only the proposed source/target pair.
    """

    def validate_sequence(
        self,
        previous_sequence_number: Optional[int],
        sequence_number: int,
    ) -> None:
        """Raise ``InvalidTransitionSequenceError`` unless
        ``sequence_number`` is a non-negative int, and (when
        ``previous_sequence_number`` is given) strictly greater than
        ``previous_sequence_number``. Fails closed: a malformed
        ``sequence_number`` is rejected outright, never coerced."""

        if isinstance(sequence_number, bool) or not isinstance(sequence_number, int):
            raise InvalidTransitionSequenceError(
                f"transition_sequence_number must be a non-negative int, got {sequence_number!r}."
            )
        if sequence_number < 0:
            raise InvalidTransitionSequenceError(
                f"transition_sequence_number must be non-negative, got {sequence_number!r}."
            )
        if previous_sequence_number is None:
            return
        if isinstance(previous_sequence_number, bool) or not isinstance(
            previous_sequence_number, int
        ):
            raise InvalidTransitionSequenceError(
                f"previous_sequence_number must be an int or None, got {previous_sequence_number!r}."
            )
        if sequence_number <= previous_sequence_number:
            raise InvalidTransitionSequenceError(
                f"transition_sequence_number {sequence_number!r} must be strictly greater than "
                f"previous_sequence_number {previous_sequence_number!r}."
            )


__all__ = ["TransitionPolicy"]
