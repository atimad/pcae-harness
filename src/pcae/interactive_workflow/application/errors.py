"""Application-service error taxonomy (Phase 145F).

Every error raised across the Interactive Workflow + Publication
application-service boundary (``session_service``, ``publication_service``)
is one of the classes defined here -- never a raw
``InteractiveWorkflowError``/``PublicationExecutionError`` subtype and
never an unwrapped Python exception. Each carries a human-readable
message and, where known, the ``session_id``/``package_id``/``record_id``
identifiers already established as safe to surface (IWPC-001 v1.1
IWPC-REQ-135-137's discipline, applied here even though no CLI/transport
layer exists yet to enforce it): no raw filesystem path, exception class
name, or traceback is ever embedded. This is possible without additional
sanitization work because every wrapped store/coordinator-layer exception
already guarantees a pre-sanitized message (Phase 145D/145E/144C's own
error-message discipline) -- wrapping here never re-introduces what those
layers already stripped out.
"""
from __future__ import annotations

from typing import Optional


class ApplicationServiceError(Exception):
    """Base class for every error the application-service boundary raises."""

    def __init__(
        self,
        message: str,
        *,
        session_id: Optional[str] = None,
        package_id: Optional[str] = None,
        record_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.session_id = session_id
        self.package_id = package_id
        self.record_id = record_id


class SessionCoordinationError(ApplicationServiceError):
    """Base class for session-lifecycle-coordination failures."""


class SessionNotFoundApplicationError(SessionCoordinationError):
    """No persisted session exists for the requested identifier."""


class InvalidSessionIdentifierApplicationError(SessionCoordinationError):
    """A supplied session identifier failed structural/path validation."""


class SessionAlreadyExistsApplicationError(SessionCoordinationError):
    """A session already exists for the identifier a create attempted to use."""


class SessionCorruptApplicationError(SessionCoordinationError):
    """The persisted session record failed corruption/version validation."""


class SessionPersistenceUnavailableApplicationError(SessionCoordinationError):
    """The Session Repository could not durably complete an operation."""


class SessionNotTerminalApplicationError(SessionCoordinationError):
    """Session completion was requested for a non-terminal session."""


class SessionInvalidTransitionApplicationError(SessionCoordinationError):
    """An orchestration operation (evidence/clarify/confirm/cancel) was
    requested against a session not in the precondition state that
    operation's IWPC-001 v1.1 §5 subsection requires (Phase 145G.1)."""


class SessionConfirmationConflictApplicationError(SessionCoordinationError):
    """A ``confirm`` operation's ``--preview-digest`` did not match the
    session's current live Preview Digest, or the session already has an
    accepted Confirmation (Phase 145G.1, IWPC-REQ-020/021)."""


class SessionIdentityMismatchApplicationError(SessionCoordinationError):
    """A resumed-session operation's caller-supplied identity claim does
    not equal the session's bound ``owner_identity`` (Phase 145G.3,
    IWC-REQ-022/IWC-REQ-151). Raised before any state-precondition or
    orchestration logic runs, including ahead of an otherwise-idempotent
    early return (e.g. ``cancel_session`` against an already-``Cancelled``
    session), so a mismatched identity can never become an idempotent
    success."""


class SessionOrchestrationCorruptApplicationError(SessionCoordinationError):
    """The persisted orchestration record failed corruption/version
    validation (Phase 145G.1)."""


class SessionOrchestrationPersistenceUnavailableApplicationError(SessionCoordinationError):
    """The orchestration record store could not durably complete an
    operation (Phase 145G.1)."""


class ReadinessCoordinationError(ApplicationServiceError):
    """Base class for readiness-package-coordination failures."""


class ReadinessPackageNotFoundApplicationError(ReadinessCoordinationError):
    """No persisted pending-readiness package exists for the identifier."""


class ReadinessPackageAlreadyExistsApplicationError(ReadinessCoordinationError):
    """A pending-readiness package already exists for the identifier."""


class ReadinessStoreCorruptApplicationError(ReadinessCoordinationError):
    """The persisted readiness record failed corruption/version validation."""


class ReadinessDigestMismatchApplicationError(ReadinessCoordinationError):
    """The persisted readiness package failed whole-package digest verification."""


class ReadinessSessionNotConfirmedApplicationError(ReadinessCoordinationError):
    """Readiness-package persistence was attempted for a non-Confirmed session."""


class ReadinessPackageStaleApplicationError(ReadinessCoordinationError):
    """The readiness package's bound session has since reached Expired."""


class ReadinessPersistenceUnavailableApplicationError(ReadinessCoordinationError):
    """The Pending-Readiness Store could not durably complete an operation."""


class PublicationCoordinationError(ApplicationServiceError):
    """Base class for publication-boundary-coordination failures."""


class PublicationAlreadyCompletedApplicationError(PublicationCoordinationError):
    """The named package has already been successfully published (replay)."""


class PublicationAttemptConflictApplicationError(PublicationCoordinationError):
    """A conflicting attempt-linkage replay was detected at the readiness store."""


class PublicationAuthorizationFailedApplicationError(PublicationCoordinationError):
    """Publication Coordinator rejected the supplied authorization."""


class PublicationExecutionFailedApplicationError(PublicationCoordinationError):
    """Publication Coordinator failed to execute publication."""


class PublicationReconciliationIncompleteApplicationError(PublicationCoordinationError):
    """Publication succeeded, but the Pending-Readiness Store's own attempt
    linkage/disposition could not be durably updated to reflect it. The
    CHGR named by ``record_id`` is genuine and already exists in canonical
    storage; this error signals a bookkeeping gap in this boundary's own
    non-authoritative store only, requiring reconciliation, not a
    publication failure to retry."""


class PublicationPermissionDeniedApplicationError(PublicationCoordinationError):
    """Phase 149O.20L.7O.3C.2: the Permission Broker's publication-path
    adapter (``pcae.core.mutation_permission.evaluate_publication_permission``)
    did not return ``authorized=True`` for this hand-off attempt -- either
    a policy ``DENY``/non-``ALLOW`` decision, or a broker construction/
    evaluation failure (fails closed identically either way, RWMPC-001's
    existing "construction failure is diagnostically identical to an
    evaluation failure" precedent). No CHGR is created and no readiness-
    store attempt-linkage update occurs; the caller may retry once the
    underlying condition is resolved -- this is a machine-checked gate
    added in front of ``PublicationCoordinator.execute()``, never a
    replacement for the human confirmation boundary that already produced
    the ``Confirmed`` session this package was built from."""


__all__ = [
    "ApplicationServiceError",
    "SessionCoordinationError",
    "SessionNotFoundApplicationError",
    "InvalidSessionIdentifierApplicationError",
    "SessionAlreadyExistsApplicationError",
    "SessionCorruptApplicationError",
    "SessionPersistenceUnavailableApplicationError",
    "SessionNotTerminalApplicationError",
    "SessionInvalidTransitionApplicationError",
    "SessionConfirmationConflictApplicationError",
    "SessionIdentityMismatchApplicationError",
    "SessionOrchestrationCorruptApplicationError",
    "SessionOrchestrationPersistenceUnavailableApplicationError",
    "ReadinessCoordinationError",
    "ReadinessPackageNotFoundApplicationError",
    "ReadinessPackageAlreadyExistsApplicationError",
    "ReadinessStoreCorruptApplicationError",
    "ReadinessDigestMismatchApplicationError",
    "ReadinessSessionNotConfirmedApplicationError",
    "ReadinessPackageStaleApplicationError",
    "ReadinessPersistenceUnavailableApplicationError",
    "PublicationCoordinationError",
    "PublicationAlreadyCompletedApplicationError",
    "PublicationAttemptConflictApplicationError",
    "PublicationAuthorizationFailedApplicationError",
    "PublicationExecutionFailedApplicationError",
    "PublicationReconciliationIncompleteApplicationError",
    "PublicationPermissionDeniedApplicationError",
]
