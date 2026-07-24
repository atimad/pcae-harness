"""Interactive Workflow infrastructure error hierarchy (Phase 143K).

Infrastructure errors only -- IWC-001 v1.1 workflow-semantic errors
(invalid transition attempted mid-workflow, ownership mismatch on resume,
confirmation digest mismatch, etc.) are deferred to the phases that
implement the behavior they guard (143L onward, per Phase 143J §12). Every
error here is deterministic and fails closed: none of them repair input,
invent a default, retry silently, or mutate state on the caller's behalf.
"""

from __future__ import annotations


class InteractiveWorkflowError(Exception):
    """Base class for every Interactive Workflow infrastructure error."""


class SessionNotFoundError(InteractiveWorkflowError):
    """No session record exists for the given session identifier."""


class InvalidSessionStateError(InteractiveWorkflowError):
    """A session's ``session_state`` value is not one of the ten states
    defined by IWC-001 v1.1 §4.4, or a proposed transition is not present
    in the widened transition table."""


class InvalidIdentifierError(InteractiveWorkflowError):
    """A value does not match the ``CDS-<uuid4>`` session identifier
    syntax (IWC-001 v1.1 §4.1)."""


class UnsupportedVersionError(InteractiveWorkflowError):
    """A persisted or serialized record declares a ``schema_version`` this
    package does not explicitly recognize. No fallback to "latest
    assumed" is ever performed."""


class PersistenceUnavailableError(InteractiveWorkflowError):
    """The configured ``SessionRepository`` implementation could not
    complete a read or write. Raised without partial state mutation."""


class SerializationFailureError(InteractiveWorkflowError):
    """A session record could not be serialized to, or deserialized from,
    its wire representation."""


class InvariantViolationError(InteractiveWorkflowError):
    """A structural invariant enforced by
    ``pcae.interactive_workflow.validation`` failed on an otherwise
    well-typed ``Session`` (e.g. a required metadata key is absent).
    Distinct from ``InvalidSessionStateError``/``InvalidIdentifierError``,
    which cover the state and identifier invariants specifically."""


class TransitionError(InteractiveWorkflowError):
    """Base class for every Transition Engine error (Phase 143L,
    ``pcae.interactive_workflow.state_machine``). Distinct from
    ``InvalidSessionStateError`` (the 143K structural invariant, still
    used standalone by ``validate_terminal_integrity``) -- every error
    the Transition Engine itself raises is a ``TransitionError``
    subclass, so callers can catch the whole family with one type. All
    subclasses fail closed: none of them repair input, invent a default,
    retry silently, or partially apply a transition."""


class UnknownStateError(TransitionError):
    """A proposed transition's source or target state is not one of the
    ten canonical ``SessionState`` members (IWC-REQ-042)."""


class DuplicateTransitionError(TransitionError):
    """The proposed target state is identical to the session's current
    state -- a no-op transition, rejected rather than silently
    accepted."""


class TerminalStateViolationError(TransitionError):
    """The session's current state is one of the four terminal states
    (``Confirmed``/``Cancelled``/``Expired``/``Abandoned``), which admit
    no exit (IWC-001 v1.1 §4.4)."""


class UnsupportedTransitionError(TransitionError):
    """The proposed source -> target transition is structurally
    well-formed (both states are known, source is non-terminal, source
    and target differ) but is not present in the canonical Transition
    Registry (IWC-001 v1.1 §4.4, widened by Phase 143I.1)."""


class InvalidTransitionSequenceError(TransitionError):
    """The proposed ``transition_sequence_number`` is not a non-negative
    integer strictly greater than the session's previous sequence
    number -- sequence monotonicity is a Transition Engine invariant,
    not an optional check."""


class InvalidTransitionError(TransitionError):
    """General-purpose Transition Engine failure: either a malformed
    ``Session`` (missing/wrong-typed required attributes) that prevents
    any of the more specific checks from running, or any other
    fail-closed rejection not covered by a more specific
    ``TransitionError`` subclass."""


__all__ = [
    "InteractiveWorkflowError",
    "SessionNotFoundError",
    "InvalidSessionStateError",
    "InvalidIdentifierError",
    "UnsupportedVersionError",
    "PersistenceUnavailableError",
    "SerializationFailureError",
    "InvariantViolationError",
    "TransitionError",
    "UnknownStateError",
    "DuplicateTransitionError",
    "TerminalStateViolationError",
    "UnsupportedTransitionError",
    "InvalidTransitionSequenceError",
    "InvalidTransitionError",
]
