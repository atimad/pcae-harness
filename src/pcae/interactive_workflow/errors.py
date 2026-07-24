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


__all__ = [
    "InteractiveWorkflowError",
    "SessionNotFoundError",
    "InvalidSessionStateError",
    "InvalidIdentifierError",
    "UnsupportedVersionError",
    "PersistenceUnavailableError",
    "SerializationFailureError",
    "InvariantViolationError",
]
