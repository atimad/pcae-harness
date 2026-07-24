"""Publication Coordinator (Phase 144C; PEC-001 §4, §6, §7, §8).

``PublicationCoordinator`` is the single, named component that performs
Publication Execution (PEC-REQ-001): given one already-built,
already-validated ``PublicationReadinessPackage`` and one valid
Publication Authorization Event, it performs CHGR-001 §8's atomic write,
canonical identity assignment, and provenance/integrity capture in the
same atomic operation, and nothing else (PEC-REQ-021, PEC-REQ-022).

Execution ordering follows PEC-REQ-051 exactly: the idempotency/replay
check runs first, then package validation, then authorization validation,
then the atomic write, then completion reporting. Every attempt --
accepted or refused -- is durably recorded (PEC-REQ-043, PEC-REQ-105,
PEC-REQ-106).

This module deliberately imports nothing from
``pcae.interactive_workflow.session``, ``...orchestration``,
``...evidence``, ``...clarification``, ``...preview``, or
``...confirmation`` -- the Integration section's explicit exclusion list.
Its only ``interactive_workflow`` dependency is
``PublicationHandoff.is_ready``/``validate_completeness``, called as a
pure, stateless, side-effect-free delegation to the readiness authority
IWC-001/143O already owns (PEC-REQ-068: "readiness is established
exclusively by PublicationHandoff... already owned inside
interactive_workflow/**") -- never a reimplementation of that logic
(PEC-REQ-022's "shall not determine... evidence sufficiency" prohibition
would be violated by duplicating, not by delegating to, that check).
"""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timezone
from typing import Optional

from pcae.governance.publication.errors import (
    AtomicPublicationFailure,
    AuthorizationReplayError,
    InvalidAuthorizationError,
    InvalidPublicationPackageError,
    MissingAuthorizationError,
    PublicationExecutionError,
    PublicationRollbackError,
    PublicationStorageError,
    StaleAuthorizationError,
)
from pcae.governance.publication.models import PublicationAuthorizationEvent, PublicationExecutionResult
from pcae.governance.publication.record import build_publication_record
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.interactive_workflow.errors import PublicationHandoffIncompleteError
from pcae.interactive_workflow.publication_handoff.handoff import PublicationHandoff
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage

_PROHIBITED_PACKAGE_FIELDS = frozenset(
    {
        "chgr_id",
        "publication_state",
        "publication_result",
        "authority_token",
        "execution_state",
    }
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class PublicationCoordinator:
    """The sole owner of Publication Execution (PEC-REQ-013). Stateless
    apart from the durable store it delegates all persistence to; every
    method's outcome is a deterministic function of its arguments plus
    the store's own already-recorded attempts (PEC-REQ-047, PEC-REQ-090).
    """

    def __init__(
        self,
        store: Optional[PublicationRecordStore] = None,
        handoff: Optional[PublicationHandoff] = None,
    ) -> None:
        self._store = store if store is not None else PublicationRecordStore()
        self._handoff = handoff if handoff is not None else PublicationHandoff()

    def authorize(
        self,
        *,
        operator_id: str,
        package_id: str,
        invoked_at: Optional[str] = None,
    ) -> PublicationAuthorizationEvent:
        """Construct a ``PublicationAuthorizationEvent`` from the required
        evidence (PEC-REQ-038): operator identity, timestamp, and exact
        ``package_id``. This method does not itself constitute a
        Publication Authorization Event -- per PEC-REQ-034/PEC-REQ-045
        that requires an explicit, human-operated invocation of a
        dedicated CLI command, which this phase does not implement (no
        CLI is in scope for 144C). Callers standing in for that future
        CLI layer supply ``operator_id`` from their own already-verified
        human-operator identity."""

        return PublicationAuthorizationEvent(
            event_id=f"pubauth-{uuid.uuid4().hex}",
            operator_id=operator_id,
            package_id=package_id,
            invoked_at=invoked_at if invoked_at is not None else _now_iso(),
        )

    def execute(
        self,
        package: PublicationReadinessPackage,
        event: Optional[PublicationAuthorizationEvent],
    ) -> PublicationExecutionResult:
        """Perform one Publication Execution attempt.

        Raises a ``PublicationExecutionError`` subclass and creates no
        CHGR on any failure (PEC-REQ-052, PEC-REQ-075). Returns a
        ``PublicationExecutionResult`` with ``success=True`` and a
        ``record_id`` only once the CHGR exists in canonical storage with
        its identity assigned and its provenance/integrity evidence
        captured (PEC-REQ-055).
        """

        attempt_id = f"pubexec-{uuid.uuid4().hex}"
        evaluated_at = _now_iso()

        try:
            self._validate_authorization_presence(package, event)
            self._check_replay(package)
            self._validate_package(package)
            self._validate_authorization_applicability(package, event)
            self._validate_authorization_freshness(package, event)
        except PublicationExecutionError as exc:
            result = self._failure_result(attempt_id, package, event, evaluated_at, exc)
            self._record_attempt(attempt_id, event, result)
            raise

        record_id = f"chgr-{uuid.uuid4().hex}"
        created_at = _now_iso()
        payload = build_publication_record(package, event, record_id, created_at)

        try:
            self._store.write_record(record_id, payload)
        except PublicationStorageError as exc:
            result = self._failure_result(attempt_id, package, event, evaluated_at, exc)
            self._record_attempt(attempt_id, event, result)
            raise

        marker = {
            "package_id": package.package_id,
            "session_id": package.session_id,
            "record_id": record_id,
            "attempt_id": attempt_id,
            "operator_id": event.operator_id,
            "authorization_event_id": event.event_id,
            "completed_at": _now_iso(),
        }
        try:
            self._store.commit_publication(package.package_id, record_id, marker)
        except FileExistsError as exc:
            self._store.remove_record(record_id)
            error = AuthorizationReplayError(
                f"Publication for package {package.package_id!r} was already committed "
                "by a concurrent attempt; this attempt's CHGR record has been rolled back."
            )
            result = self._failure_result(attempt_id, package, event, evaluated_at, error)
            self._record_attempt(attempt_id, event, result)
            raise error from exc
        except OSError as exc:
            self._store.remove_record(record_id)
            error = PublicationRollbackError(
                f"Failed to durably commit publication for package "
                f"{package.package_id!r}: {exc}. The CHGR record has been rolled back; "
                "no CHGR exists in canonical storage."
            )
            result = self._failure_result(attempt_id, package, event, evaluated_at, error)
            self._record_attempt(attempt_id, event, result)
            raise error from exc

        result = PublicationExecutionResult(
            attempt_id=attempt_id,
            success=True,
            package_id=package.package_id,
            session_id=package.session_id,
            record_id=record_id,
            diagnostics=(),
            evaluated_at=evaluated_at,
            completed_at=_now_iso(),
        )
        self._record_attempt(attempt_id, event, result)
        return result

    # -- internal validation steps, in PEC-REQ-051's fixed order --------

    def _validate_authorization_presence(
        self, package: PublicationReadinessPackage, event: Optional[PublicationAuthorizationEvent]
    ) -> None:
        if not isinstance(package, PublicationReadinessPackage):
            raise InvalidPublicationPackageError(
                f"Publication Execution requires a PublicationReadinessPackage instance, "
                f"got {type(package).__name__}."
            )
        if event is None:
            raise MissingAuthorizationError(
                f"No Publication Authorization Event was supplied for package "
                f"{package.package_id!r}; the Coordinator never infers authorization "
                "from readiness (PEC-REQ-010)."
            )
        if not isinstance(event, PublicationAuthorizationEvent):
            raise InvalidAuthorizationError(
                f"Publication Execution requires a PublicationAuthorizationEvent "
                f"instance, got {type(event).__name__}."
            )

    def _check_replay(self, package: PublicationReadinessPackage) -> None:
        if self._store.is_published(package.package_id):
            raise AuthorizationReplayError(
                f"Package {package.package_id!r} has already been consumed by a "
                "completed Publication Execution; refusing as Replay (PEC-REQ-007, "
                "PEC-REQ-041)."
            )

    def _validate_package(self, package: PublicationReadinessPackage) -> None:
        present_fields = {field.name for field in dataclasses.fields(package)}
        prohibited = present_fields & _PROHIBITED_PACKAGE_FIELDS
        if prohibited:
            raise InvalidPublicationPackageError(
                f"PublicationReadinessPackage {package.package_id!r} carries prohibited "
                f"field(s) {sorted(prohibited)!r} (PEC-REQ-061-064)."
            )
        try:
            self._handoff.validate_completeness(package)
        except PublicationHandoffIncompleteError as exc:
            raise InvalidPublicationPackageError(
                f"PublicationReadinessPackage {package.package_id!r} is not ready: {exc}"
            ) from exc

    def _validate_authorization_applicability(
        self, package: PublicationReadinessPackage, event: PublicationAuthorizationEvent
    ) -> None:
        if event.package_id != package.package_id:
            raise InvalidAuthorizationError(
                f"Publication Authorization Event {event.event_id!r} names package "
                f"{event.package_id!r}, not the supplied package {package.package_id!r} "
                "(PEC-REQ-040)."
            )

    def _validate_authorization_freshness(
        self, package: PublicationReadinessPackage, event: PublicationAuthorizationEvent
    ) -> None:
        try:
            built_at = _parse_timestamp(package.built_at)
            invoked_at = _parse_timestamp(event.invoked_at)
        except ValueError as exc:
            raise StaleAuthorizationError(
                f"Could not evaluate timestamp ordering for package "
                f"{package.package_id!r} against event {event.event_id!r}: {exc}"
            ) from exc
        if invoked_at < built_at:
            raise StaleAuthorizationError(
                f"Publication Authorization Event {event.event_id!r} (invoked_at="
                f"{event.invoked_at!r}) predates package {package.package_id!r}'s own "
                f"construction (built_at={package.built_at!r}); refusing as stale "
                "(PEC-REQ-079)."
            )

    # -- reporting --------------------------------------------------------

    def _failure_result(
        self,
        attempt_id: str,
        package: PublicationReadinessPackage,
        event: Optional[PublicationAuthorizationEvent],
        evaluated_at: str,
        error: Exception,
    ) -> PublicationExecutionResult:
        package_id = getattr(package, "package_id", "") or (
            event.package_id if isinstance(event, PublicationAuthorizationEvent) else ""
        )
        session_id = getattr(package, "session_id", "")
        return PublicationExecutionResult(
            attempt_id=attempt_id,
            success=False,
            package_id=package_id,
            session_id=session_id,
            record_id=None,
            diagnostics=(str(error),),
            evaluated_at=evaluated_at,
            completed_at=_now_iso(),
            error_type=type(error).__name__,
            failure_reason=str(error),
        )

    def _record_attempt(
        self,
        attempt_id: str,
        event: Optional[PublicationAuthorizationEvent],
        result: PublicationExecutionResult,
    ) -> None:
        from pcae.governance.publication.serialization import result_to_payload

        payload = {
            "attempt_id": attempt_id,
            "authorization": {
                "event_id": event.event_id,
                "operator_id": event.operator_id,
                "package_id": event.package_id,
                "invoked_at": event.invoked_at,
            }
            if isinstance(event, PublicationAuthorizationEvent)
            else None,
            "result": result_to_payload(result),
        }
        try:
            self._store.record_attempt(attempt_id, payload)
        except PublicationStorageError:
            # A refusal's audit-trail persistence failing never masks or
            # replaces the refusal's own, already-determined error
            # (PEC-REQ-083): the caller's original exception, raised right
            # after this call returns, remains authoritative. A
            # *successful* publication's audit-trail failure is different
            # -- the CHGR was actually created, so silently swallowing the
            # audit-write failure would misrepresent a real, if degraded,
            # success as a clean one; that case is surfaced loudly instead.
            if not result.success:
                return
            raise AtomicPublicationFailure(
                f"Publication of {result.record_id!r} succeeded but its audit attempt "
                f"record {attempt_id!r} could not be durably persisted."
            ) from None


__all__ = ["PublicationCoordinator"]
