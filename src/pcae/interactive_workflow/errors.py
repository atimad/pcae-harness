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


class DuplicateEvidenceError(InteractiveWorkflowError):
    """A proposed ``evidence_id`` is already registered with the Evidence
    Coordinator (Phase 143M, ``pcae.interactive_workflow.evidence``).
    Registration is rejected outright; the existing entry is never
    silently overwritten."""


class UnknownEvidenceError(InteractiveWorkflowError):
    """No evidence record exists for the requested ``evidence_id``."""


class DuplicateClarificationError(InteractiveWorkflowError):
    """A proposed ``clarification_id`` is already registered with the
    Clarification Controller (Phase 143M,
    ``pcae.interactive_workflow.clarification``)."""


class InvalidClarificationError(InteractiveWorkflowError):
    """A clarification operation is structurally invalid: an unknown
    ``clarification_id``, a response registered against a clarification
    that already has one, or an attempted classification tag
    (``recommendation``/``approval``/``authorization``/``decision``) that
    would breach IWC-001 v1.1 §9's informational-only boundary
    (IWC-REQ-093, IWC-REQ-094, IWC-REQ-095)."""


class DuplicateAuditEventError(InteractiveWorkflowError):
    """A proposed ``event_id`` is already present in the Audit Recorder's
    append-only log (Phase 143M, ``pcae.interactive_workflow.audit``)."""


class AuditSerializationFailureError(InteractiveWorkflowError):
    """An ``AuditEvent`` could not be serialized to, or deserialized
    from, its wire representation. Distinct from
    ``SerializationFailureError`` (the 143K ``Session`` serialization
    failure) so a caller can distinguish which artifact class failed to
    round-trip."""


class InvalidPreviewError(InteractiveWorkflowError):
    """A ``Preview`` is structurally invalid: an unrecognized
    ``schema_version``, a missing declared reference, a duplicate
    reference within one reference collection, or any other malformed
    condition the Preview Builder (Phase 143N,
    ``pcae.interactive_workflow.preview``) detects. Fails closed --
    never repaired or defaulted on the caller's behalf."""


class PreviewDigestMismatchError(InteractiveWorkflowError):
    """A supplied Preview Digest does not match the digest recomputed
    from the exact Preview content it claims to bind to (IWC-001 v1.1
    §10.2, §10.3 -- the single most safety-critical property the
    contract freezes). Raised both by Preview validation (digest
    consistency) and by Confirmation Controller's pre-acceptance
    recheck."""


class StalePreviewError(InteractiveWorkflowError):
    """A ``Preview`` was built against session state that has since
    changed -- its bound transition sequence number, or session
    identity, no longer matches the current value supplied at check time
    (IWC-001 v1.1 §10.2, §12 "stale evidence"/"stale preview"). No
    automatic refresh is ever performed; the caller must build a fresh
    Preview."""


class InvalidConfirmationError(InteractiveWorkflowError):
    """A confirmation operation is structurally invalid: an unknown
    ``request_id``, a response whose ``request_id`` does not match the
    request it is being registered against, a request or response bound
    to a session identifier other than the Confirmation Controller's own
    scope, or a response whose ``preview_id`` does not match its
    request's ``preview_id``."""


class DuplicateConfirmationError(InteractiveWorkflowError):
    """A proposed ``request_id`` or ``response_id`` is already registered
    with the Confirmation Controller (Phase 143N,
    ``pcae.interactive_workflow.confirmation``), or the targeted request
    already has a response -- a response, once registered, is never
    overwritten or re-accepted (fail closed)."""


class ReplayDetectedError(InteractiveWorkflowError):
    """A confirming action attempted to reuse a Preview Digest that has
    already been successfully bound to a completed Confirmation
    elsewhere in this Confirmation Controller's scope (IWC-001 v1.1
    §10.4). Distinct from ``DuplicateConfirmationError`` (an identifier
    collision) -- this is a content-reuse rejection."""


class ConfirmationSerializationFailureError(InteractiveWorkflowError):
    """A ``ConfirmationRequest`` or ``ConfirmationResponse`` could not be
    serialized to, or deserialized from, its wire representation.
    Distinct from ``SerializationFailureError`` so a caller can
    distinguish which artifact class failed to round-trip."""


class WorkflowInitializationError(InteractiveWorkflowError):
    """The Session Initialization orchestration stage
    (``pcae.interactive_workflow.orchestration.coordinator.
    WorkflowOrchestrator.stage_session_initialization``, Phase 143O) was
    invoked with a ``Session`` whose identifier does not match the
    orchestrator's own scope, or otherwise cannot begin orchestration.
    Raised before any ``OrchestrationState`` mutation."""


class MissingWorkflowComponentError(InteractiveWorkflowError):
    """A ``WorkflowOrchestrator`` (Phase 143O) was constructed without
    one of its six required collaborators (Evidence Coordinator,
    Clarification Controller, Audit Recorder, Preview Builder,
    Confirmation Controller, Transition Engine), or with a value that is
    not an instance of the expected collaborator type. Raised at
    construction time, before any stage can be invoked."""


class InvalidWorkflowSequenceError(InteractiveWorkflowError):
    """A ``WorkflowOrchestrator`` (Phase 143O) stage method was invoked
    out of the fixed eight-stage order, or a stage already marked
    complete in the current ``OrchestrationState`` was invoked again
    (duplicate orchestration). Fails closed: no stage is ever skipped,
    reordered, or re-applied on the caller's behalf."""


class PublicationHandoffIncompleteError(InteractiveWorkflowError):
    """A ``PublicationHandoff`` (Phase 143O) was asked to build or
    validate a ``PublicationReadinessPackage`` from inputs that are
    missing a required reference (session, transition state, evidence,
    clarification, audit, preview, or confirmation), whose session is not
    in state ``Confirmed``, or whose orchestration sequencing is not yet
    complete. Raised instead of constructing a partial package."""


class WorkflowCompositionError(InteractiveWorkflowError):
    """A ``WorkflowOrchestrator`` (Phase 143O) was constructed from
    collaborators scoped to inconsistent session identifiers -- e.g. an
    ``EvidenceCoordinator`` and a ``ConfirmationController`` bound to two
    different sessions. Raised at construction time; no orchestration
    stage may run across a composition this inconsistent."""


class PublicationHandoffSerializationError(InteractiveWorkflowError):
    """A ``PublicationReadinessPackage`` could not be serialized to, or
    deserialized from, its wire representation. Distinct from
    ``SerializationFailureError`` so a caller can distinguish which
    artifact class failed to round-trip. Never raised for, and never
    covers, CHGR, publication-result, or lifecycle-authority content --
    no such field exists on ``PublicationReadinessPackage``."""


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
    "DuplicateEvidenceError",
    "UnknownEvidenceError",
    "DuplicateClarificationError",
    "InvalidClarificationError",
    "DuplicateAuditEventError",
    "AuditSerializationFailureError",
    "InvalidPreviewError",
    "PreviewDigestMismatchError",
    "StalePreviewError",
    "InvalidConfirmationError",
    "DuplicateConfirmationError",
    "ReplayDetectedError",
    "ConfirmationSerializationFailureError",
    "WorkflowInitializationError",
    "MissingWorkflowComponentError",
    "InvalidWorkflowSequenceError",
    "PublicationHandoffIncompleteError",
    "WorkflowCompositionError",
    "PublicationHandoffSerializationError",
]
