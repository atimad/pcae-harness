"""PublicationApplicationService (Phase 145F).

Coordinates the Pending-Readiness Store, the Session Repository (via
``SessionApplicationService``), and ``PublicationCoordinator`` for a
future transport adapter -- readiness-package persistence, publication
request preparation, the publication boundary hand-off, publication
result processing, replay/stale detection, and recovery. This class never
authorizes, executes, or decides a publication outcome itself
(IWPC-REQ-010): every authority-bearing decision is delegated verbatim to
``PublicationCoordinator``; this boundary only prepares validated inputs
and records the already-decided outcome back into the Pending-Readiness
Store's own non-authoritative bookkeeping (IWPC-REQ-079).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.governance.publication.errors import (
    AtomicPublicationFailure,
    AuthorizationReplayError,
    InvalidAuthorizationError,
    InvalidPublicationPackageError,
    MissingAuthorizationError,
    PublicationRollbackError,
    PublicationStorageError,
    StaleAuthorizationError,
)
from pcae.governance.publication.models import PublicationAuthorizationEvent, PublicationExecutionResult
from pcae.interactive_workflow.application.errors import (
    PublicationAlreadyCompletedApplicationError,
    PublicationAttemptConflictApplicationError,
    PublicationAuthorizationFailedApplicationError,
    PublicationExecutionFailedApplicationError,
    PublicationReconciliationIncompleteApplicationError,
    ReadinessDigestMismatchApplicationError,
    ReadinessPackageAlreadyExistsApplicationError,
    ReadinessPackageNotFoundApplicationError,
    ReadinessPackageStaleApplicationError,
    ReadinessPersistenceUnavailableApplicationError,
    ReadinessSessionNotConfirmedApplicationError,
    ReadinessStoreCorruptApplicationError,
)
from pcae.interactive_workflow.application.models import PreparedPublicationRequest
from pcae.interactive_workflow.application.session_service import SessionApplicationService
from pcae.interactive_workflow.errors import (
    InvalidIdentifierError,
    PendingReadinessAlreadyConsumedError,
    PendingReadinessAttemptConflictError,
    PendingReadinessDigestMismatchError,
    PendingReadinessPackageAlreadyExistsError,
    PendingReadinessPackageNotFoundError,
    PendingReadinessStoreCorruptError,
    PersistenceUnavailableError,
)
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    DISPOSITION_CONSUMED,
    FilesystemPendingReadinessStore,
    PendingReadinessRecord,
)
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PublicationApplicationService:
    """Application-layer coordination over the Pending-Readiness Store and
    ``PublicationCoordinator``.

    Constructed with explicit collaborators (dependency injection): a
    ``FilesystemPendingReadinessStore``, a ``SessionApplicationService``
    (never a raw ``SessionRepository`` -- session-state re-checks are
    coordinated through the same session boundary this module's sibling
    exposes, not a second, parallel path into the repository), and a
    ``PublicationCoordinator``. This class never selects or constructs any
    of them.
    """

    def __init__(
        self,
        readiness_store: FilesystemPendingReadinessStore,
        session_service: SessionApplicationService,
        coordinator: PublicationCoordinator,
    ) -> None:
        self._store = readiness_store
        self._sessions = session_service
        self._coordinator = coordinator

    # -- Readiness coordination -------------------------------------------

    def persist_readiness_package(
        self,
        package: PublicationReadinessPackage,
        *,
        persisted_at: Optional[str] = None,
    ) -> PendingReadinessRecord:
        """Persist a caller-supplied, already-built ``PublicationReadinessPackage``.

        Package *construction* remains exclusively
        ``PublicationHandoff.build_package``'s (IWPC-REQ-011); this method
        only persists an already-constructed package. Idempotent by key
        (``session_id``, IWPC-REQ-024): if a pending package already
        exists for ``package.session_id``, that existing record is
        returned unchanged rather than constructing a duplicate.
        """

        session = self._sessions.load_session(package.session_id)
        if session.session_state is not SessionState.CONFIRMED:
            raise ReadinessSessionNotConfirmedApplicationError(
                f"Session {package.session_id!r} is not Confirmed "
                f"({session.session_state.value!r}); a readiness package can "
                "only be persisted for a Confirmed session.",
                session_id=package.session_id,
                package_id=package.package_id,
            )

        existing = self.find_readiness_package_for_session(package.session_id)
        if existing is not None:
            return existing

        timestamp = persisted_at if persisted_at is not None else _now_iso()
        try:
            self._store.create(package, persisted_at=timestamp)
        except PendingReadinessPackageAlreadyExistsError as exc:
            raise ReadinessPackageAlreadyExistsApplicationError(
                str(exc), session_id=package.session_id, package_id=package.package_id
            ) from exc
        except InvalidIdentifierError as exc:
            raise ReadinessPackageNotFoundApplicationError(
                str(exc), session_id=package.session_id, package_id=package.package_id
            ) from exc
        except PersistenceUnavailableError as exc:
            raise ReadinessPersistenceUnavailableApplicationError(
                str(exc), session_id=package.session_id, package_id=package.package_id
            ) from exc

        return self.get_readiness_package(package.package_id)

    def get_readiness_package(self, package_id: str) -> PendingReadinessRecord:
        """Return the persisted readiness record for ``package_id``."""

        try:
            return self._store.load(package_id)
        except PendingReadinessPackageNotFoundError as exc:
            raise ReadinessPackageNotFoundApplicationError(str(exc), package_id=package_id) from exc
        except PendingReadinessDigestMismatchError as exc:
            raise ReadinessDigestMismatchApplicationError(str(exc), package_id=package_id) from exc
        except PendingReadinessStoreCorruptError as exc:
            raise ReadinessStoreCorruptApplicationError(str(exc), package_id=package_id) from exc
        except PersistenceUnavailableError as exc:
            raise ReadinessPersistenceUnavailableApplicationError(str(exc), package_id=package_id) from exc

    def find_readiness_package_for_session(self, session_id: str) -> Optional[PendingReadinessRecord]:
        """Return the pending (not yet consumed) package bound to
        ``session_id``, or ``None`` if none exists."""

        try:
            return self._store.find_by_session_id(session_id)
        except PendingReadinessDigestMismatchError as exc:
            raise ReadinessDigestMismatchApplicationError(str(exc), session_id=session_id) from exc
        except PendingReadinessStoreCorruptError as exc:
            raise ReadinessStoreCorruptApplicationError(str(exc), session_id=session_id) from exc
        except PersistenceUnavailableError as exc:
            raise ReadinessPersistenceUnavailableApplicationError(str(exc), session_id=session_id) from exc

    # -- Publication request construction ----------------------------------

    def prepare_publication_request(self, package_id: str) -> PreparedPublicationRequest:
        """Validate a persisted readiness package and prepare it for
        hand-off. Prepares; does not publish (IWPC-REQ-012).

        Verifies: the package exists with a matching digest (delegated to
        the store's own ``load``, IWPC-REQ-165); its disposition is still
        pending, not already consumed (IWPC-REQ-113); and its bound
        session has not since reached ``Expired`` (IWPC-REQ-085/114).
        """

        record = self.get_readiness_package(package_id)
        if record.disposition == DISPOSITION_CONSUMED:
            raise PublicationAlreadyCompletedApplicationError(
                f"Package {package_id!r} has already been published.",
                package_id=package_id,
                session_id=record.session_id,
                record_id=record.record_id,
            )

        session = self._sessions.load_session(record.session_id)
        if session.session_state is SessionState.EXPIRED:
            raise ReadinessPackageStaleApplicationError(
                f"Session {record.session_id!r} bound to package {package_id!r} has "
                "reached Expired since the package was built; publication requires a "
                "fresh readiness package.",
                session_id=record.session_id,
                package_id=package_id,
            )

        return PreparedPublicationRequest(
            package=record.package,
            package_id=record.package_id,
            session_id=record.session_id,
            package_digest=record.package_digest,
            confirmation_request_id=record.package.confirmation_request_id,
            confirmation_response_id=record.package.confirmation_response_id,
        )

    # -- Publication boundary / results -------------------------------------

    def hand_off(
        self,
        prepared: PreparedPublicationRequest,
        *,
        operator_id: str,
    ) -> PublicationExecutionResult:
        """Hand a prepared request to ``PublicationCoordinator`` and
        process its result.

        Never authorizes, executes, or decides on its own behalf
        (IWPC-REQ-010, IWPC-REQ-127/128): constructs the
        ``PublicationAuthorizationEvent`` from ``operator_id`` exactly as
        ``PublicationCoordinator.authorize`` requires and invokes
        ``PublicationCoordinator.execute`` unchanged. Coordinates the
        Pending-Readiness Store's own attempt-linkage/disposition update
        to reflect whatever the Coordinator already decided
        (IWPC-REQ-087/088/089) -- it never re-derives that decision.
        """

        if not operator_id:
            raise ValueError("operator_id must be non-empty.")

        record = self.get_readiness_package(prepared.package_id)
        if record.disposition == DISPOSITION_CONSUMED:
            raise PublicationAlreadyCompletedApplicationError(
                f"Package {prepared.package_id!r} has already been published.",
                package_id=prepared.package_id,
                session_id=record.session_id,
                record_id=record.record_id,
            )

        event = self._coordinator.authorize(operator_id=operator_id, package_id=prepared.package_id)

        try:
            result = self._coordinator.execute(prepared.package, event)
        except AuthorizationReplayError as exc:
            raise PublicationAlreadyCompletedApplicationError(
                str(exc), package_id=prepared.package_id, session_id=prepared.session_id
            ) from exc
        except (MissingAuthorizationError, InvalidAuthorizationError, StaleAuthorizationError) as exc:
            self._record_failed_attempt(prepared.package_id, event)
            raise PublicationAuthorizationFailedApplicationError(
                str(exc), package_id=prepared.package_id, session_id=prepared.session_id
            ) from exc
        except (InvalidPublicationPackageError, PublicationStorageError, PublicationRollbackError,
                AtomicPublicationFailure) as exc:
            self._record_failed_attempt(prepared.package_id, event)
            raise PublicationExecutionFailedApplicationError(
                str(exc), package_id=prepared.package_id, session_id=prepared.session_id
            ) from exc

        self._record_succeeded_attempt(prepared.package_id, event, result)
        return result

    def resume_publication(self, package_id: str, *, operator_id: str) -> PublicationExecutionResult:
        """Recovery entry point (IWPC-REQ-148-156).

        Determines the correct action solely by re-reading persisted
        state -- never by a caller-supplied "resume" flag: re-preparing
        raises ``PublicationAlreadyCompletedApplicationError`` if the
        store already shows the package consumed (restart after success,
        or a prior interrupted disposition update since reconciled),
        raises ``ReadinessPackageStaleApplicationError`` if the bound
        session has since expired, and otherwise performs a fresh
        authorize/execute hand-off (restart after failure, or an
        interrupted publication that never reached the Coordinator's
        commit step at all). Never reconstructs authority: a fresh,
        genuine ``PublicationAuthorizationEvent`` is always constructed
        from the caller-supplied ``operator_id``, never replayed from a
        cached prior attempt (IWPC-REQ-033/152).
        """

        prepared = self.prepare_publication_request(package_id)
        return self.hand_off(prepared, operator_id=operator_id)

    # -- internal helpers ----------------------------------------------------

    def _record_succeeded_attempt(
        self,
        package_id: str,
        event: PublicationAuthorizationEvent,
        result: PublicationExecutionResult,
    ) -> None:
        try:
            self._store.record_publication_attempt(
                package_id,
                attempt_id=result.attempt_id,
                outcome="succeeded",
                timestamp=result.completed_at,
                record_id=result.record_id,
                publication_attempt_id=event.event_id,
            )
        except PendingReadinessAlreadyConsumedError:
            # Already reconciled (e.g. a concurrent/prior recovery attempt
            # reached this same disposition update first); publication
            # itself unambiguously succeeded, so this is not an error.
            return
        except PendingReadinessAttemptConflictError as exc:
            raise PublicationAttemptConflictApplicationError(
                str(exc), package_id=package_id, record_id=result.record_id
            ) from exc
        except (PendingReadinessPackageNotFoundError, PendingReadinessStoreCorruptError,
                PersistenceUnavailableError) as exc:
            # Publication already succeeded (the CHGR exists); a failure to
            # record that fact into this boundary's own non-authoritative
            # bookkeeping is surfaced loudly rather than silently dropped,
            # mirroring PublicationCoordinator._record_attempt's own
            # identical precedent for its successful-attempt audit write.
            raise PublicationReconciliationIncompleteApplicationError(
                str(exc), package_id=package_id, record_id=result.record_id
            ) from exc

    def _record_failed_attempt(self, package_id: str, event: PublicationAuthorizationEvent) -> None:
        attempt_id = f"pubapp-{uuid.uuid4().hex}"
        try:
            self._store.record_publication_attempt(
                package_id,
                attempt_id=attempt_id,
                outcome="failed",
                timestamp=_now_iso(),
                publication_attempt_id=event.event_id,
            )
        except (PendingReadinessAlreadyConsumedError, PendingReadinessAttemptConflictError,
                PendingReadinessPackageNotFoundError, PendingReadinessStoreCorruptError,
                PersistenceUnavailableError):
            # Best-effort linkage only: PublicationCoordinator's own
            # PublicationRecordStore attempts/ audit trail (IWPC-REQ-087)
            # already durably recorded this failure independent of this
            # store's own linkage succeeding, so a failure here is not
            # itself surfaced -- the original failure exception, raised by
            # the caller immediately after this call returns, remains
            # authoritative.
            return


__all__ = ["PublicationApplicationService"]
