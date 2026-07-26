"""``pcae decision-session ...`` -- IWPC-001 v1.1 CLI/transport adapter
(Phase 145G).

Implements exactly the three ``decision-session`` sub-commands this phase
can correctly implement against the Phase 145F application-service
boundary: ``create``, ``status``, ``readiness``. ``evidence``, ``clarify``,
``preview``, ``confirm``, and ``cancel`` are frozen by IWPC-001 v1.1 §5 but
are NOT implemented by this phase -- see "Disclosed limitation" below.

This module is the transport adapter (IWPC-REQ-006): it parses CLI
arguments, constructs the frozen application request inputs, invokes
``SessionApplicationService``/``PublicationApplicationService`` (Phase
145F, unmodified), renders deterministic output, and maps every
application-layer error to the closed exit-code/``error_type`` taxonomy
(IWPC-001 v1.1 §9, §19). It never imports ``SessionCoordinator``,
``WorkflowOrchestrator``, or ``PublicationCoordinator`` outside this
module's own narrow composition root (``build_application_context``),
never reads/writes session or pending-readiness JSON directly, and never
evaluates authority or reimplements a workflow decision.

Disclosed limitation (documented per this phase's own governing prompt,
"fail closed and document the conflict rather than silently choosing a
new semantic interpretation"): IWPC-REQ-016/017/018/020/025 name
``evidence``/``clarify``/``preview``/``confirm``/``cancel`` as commands
this contract requires. Direct inspection of
``pcae.interactive_workflow.orchestration.coordinator.WorkflowOrchestrator``
and ``pcae.interactive_workflow.orchestration.models.OrchestrationState``
shows orchestration-stage progress is an in-memory-only dataclass, never
persisted by ``SessionRepository`` or any other store; the ``Session``
domain model itself carries no evidence/clarification/audit-ref fields and
no cancellation-reason field; and ``SessionCoordinator`` exposes no
``cancel`` method at all. Because every ``pcae`` CLI invocation is a
separate OS process, there is no way to run those five commands as
independent invocations against a session created by an earlier
invocation without first persisting new orchestration/evidence/
clarification/cancellation state in the Interactive Workflow domain
layer -- and this phase's own governing prompt explicitly forbids
"modify[ing] Phase 145D, 145E, or 145F semantics to accommodate the CLI"
or "modify[ing] persistence or domain behavior merely to make CLI
implementation easier." This is therefore not a CLI adapter gap this
phase can close; it is named here, in the phase report, and in the
requirement-traceability matrix as a Blocking finding for those five
commands specifically, with a recommendation that a future phase add the
missing persisted state to the Interactive Workflow domain layer under
its own separately-governed authorization before a later CLI phase
implements them.

A second, narrower disclosed limitation affects ``decision-session
readiness``'s *construction* path (IWPC-REQ-024): constructing a
``PublicationReadinessPackage`` requires a completed ``OrchestrationState``,
a live ``Preview``, a ``ConfirmationRequest``, and an accepted
``ConfirmationResponse`` -- none of which this CLI has any way to obtain,
for the same reason above. ``readiness`` therefore only implements the
read/inspect path (IWPC-REQ-023): if a pending package already exists it
is reported verbatim; if none exists, ``readiness_incomplete`` is
reported (a value the closed taxonomy already defines for exactly this
case: "session not yet confirmed, or ``PublicationHandoff.build_package``
has not yet been invoked").
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Optional

from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.interactive_workflow.application.errors import (
    ApplicationServiceError,
    InvalidSessionIdentifierApplicationError,
    PublicationAlreadyCompletedApplicationError,
    PublicationAttemptConflictApplicationError,
    PublicationAuthorizationFailedApplicationError,
    PublicationExecutionFailedApplicationError,
    PublicationReconciliationIncompleteApplicationError,
    ReadinessDigestMismatchApplicationError,
    ReadinessPackageNotFoundApplicationError,
    ReadinessPackageStaleApplicationError,
    ReadinessPersistenceUnavailableApplicationError,
    ReadinessSessionNotConfirmedApplicationError,
    ReadinessStoreCorruptApplicationError,
    SessionAlreadyExistsApplicationError,
    SessionCorruptApplicationError,
    SessionNotFoundApplicationError,
    SessionPersistenceUnavailableApplicationError,
)
from pcae.interactive_workflow.application.publication_service import PublicationApplicationService
from pcae.interactive_workflow.application.session_service import SessionApplicationService
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    DISPOSITION_CONSUMED,
    FilesystemPendingReadinessStore,
)
from pcae.interactive_workflow.persistence.filesystem_repository import FilesystemSessionRepository
from pcae.interactive_workflow.serialization.schema import to_payload
from pcae.interactive_workflow.session.coordinator import SessionCoordinator

SCHEMA_VERSION = "iwpc-transport/1.0"

# -- Exit-code contract (IWPC-001 v1.1 §9, IWPC-REQ-050) ---------------------

EXIT_SUCCESS = 0
EXIT_GENERIC_DOMAIN_FAILURE = 1
EXIT_INVALID_STATE_TRANSITION = 2
EXIT_CONFIRMATION_CONFLICT = 3
EXIT_AUTHORIZATION_REPLAY = 4
EXIT_STALE_AUTHORIZATION = 5

# -- Error taxonomy (IWPC-001 v1.1 §19.1, IWPC-REQ-134) ----------------------
# Every error_type this phase's implemented commands can produce, plus the
# full closed set (IWPC-REQ-052 requires every taxonomy member map to
# exactly one exit class, even members unreachable by this phase's three
# implemented commands).

_EXIT_CODE_BY_ERROR_TYPE = {
    "invalid_request": EXIT_GENERIC_DOMAIN_FAILURE,
    "invalid_state_transition": EXIT_INVALID_STATE_TRANSITION,
    "malformed_artifact": EXIT_GENERIC_DOMAIN_FAILURE,
    "unsupported_version": EXIT_GENERIC_DOMAIN_FAILURE,
    "artifact_not_found": EXIT_GENERIC_DOMAIN_FAILURE,
    "artifact_stale": EXIT_STALE_AUTHORIZATION,
    "artifact_binding_mismatch": EXIT_CONFIRMATION_CONFLICT,
    "confirmation_required": EXIT_INVALID_STATE_TRANSITION,
    "confirmation_conflict": EXIT_CONFIRMATION_CONFLICT,
    "authorization_required": EXIT_GENERIC_DOMAIN_FAILURE,
    "authorization_invalid": EXIT_GENERIC_DOMAIN_FAILURE,
    "authority_not_established": EXIT_GENERIC_DOMAIN_FAILURE,
    "publication_conflict": EXIT_GENERIC_DOMAIN_FAILURE,
    "publication_already_completed": EXIT_AUTHORIZATION_REPLAY,
    "persistence_conflict": EXIT_GENERIC_DOMAIN_FAILURE,
    "persistence_corrupt": EXIT_GENERIC_DOMAIN_FAILURE,
    "internal_error": EXIT_GENERIC_DOMAIN_FAILURE,
    "readiness_incomplete": EXIT_GENERIC_DOMAIN_FAILURE,
    "session_not_found": EXIT_GENERIC_DOMAIN_FAILURE,
    "template_not_found": EXIT_GENERIC_DOMAIN_FAILURE,
    "subject_not_found": EXIT_GENERIC_DOMAIN_FAILURE,
    "stale_authorization": EXIT_STALE_AUTHORIZATION,
    "authorization_replay": EXIT_AUTHORIZATION_REPLAY,
    "invalid_package": EXIT_GENERIC_DOMAIN_FAILURE,
    "domain_error": EXIT_GENERIC_DOMAIN_FAILURE,
}


@dataclass(frozen=True)
class ApplicationContext:
    """The narrow composition root (IWPC-001 v1.1 "Dependency Injection
    and Composition"). Constructed fresh per CLI invocation; no module-
    level singleton, no hidden global state, no side effect at import
    time. Uses each store/coordinator's own existing default repository-
    root resolution (relative to the process's current working
    directory) -- this module invents no second repository-root
    discovery algorithm.
    """

    session_service: SessionApplicationService
    publication_service: PublicationApplicationService


def build_application_context() -> ApplicationContext:
    """Construct and connect this phase's application services.

    Only this function (and its sibling in ``governance_record.py``,
    which calls it) may construct ``SessionCoordinator``/
    ``PublicationCoordinator`` -- every CLI command handler below reaches
    them exclusively through ``SessionApplicationService``/
    ``PublicationApplicationService``.
    """

    session_repository = FilesystemSessionRepository()
    session_coordinator = SessionCoordinator(session_repository)
    session_service = SessionApplicationService(session_coordinator)

    readiness_store = FilesystemPendingReadinessStore()
    publication_coordinator = PublicationCoordinator()
    publication_service = PublicationApplicationService(
        readiness_store, session_service, publication_coordinator
    )

    return ApplicationContext(session_service=session_service, publication_service=publication_service)


# -- Output rendering (IWPC-001 v1.1 §8, IWPC-REQ-042-049) -------------------


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def _error_payload(
    error_type: str,
    message: str,
    *,
    session_id: Optional[str] = None,
    package_id: Optional[str] = None,
    record_id: Optional[str] = None,
) -> dict:
    payload = {
        "status": "error",
        "error_type": error_type,
        "message": message,
        "session_id": session_id,
        "package_id": package_id,
    }
    if record_id is not None:
        payload["record_id"] = record_id
    return payload


def _emit_error(
    args: argparse.Namespace,
    error_type: str,
    message: str,
    *,
    session_id: Optional[str] = None,
    package_id: Optional[str] = None,
    record_id: Optional[str] = None,
) -> int:
    payload = _error_payload(
        error_type, message, session_id=session_id, package_id=package_id, record_id=record_id
    )
    if getattr(args, "json", False):
        _print_json(payload)
    else:
        print(f"error: {message}")
        print(f"  error_type: {error_type}")
        if session_id is not None:
            print(f"  session_id: {session_id}")
        if package_id is not None:
            print(f"  package_id: {package_id}")
        if record_id is not None:
            print(f"  record_id: {record_id}")
    return _EXIT_CODE_BY_ERROR_TYPE[error_type]


def _require_nonempty(args: argparse.Namespace, field_name: str, value: str) -> Optional[int]:
    """Structural-completeness validation only (IWPC-REQ-036/041/055):
    non-empty/well-formed. Returns an exit code if invalid, else
    ``None``. Never duplicates or weakens domain validation -- semantic
    validation (does this session exist, is it in the right state)
    remains the application/domain layers' own.
    """

    if value is None or not str(value).strip():
        return _emit_error(args, "invalid_request", f"--{field_name} must be non-empty.")
    return None


# -- Application-error -> taxonomy mapping (shared by every handler) --------

_SESSION_ERROR_MAP = {
    SessionNotFoundApplicationError: "session_not_found",
    InvalidSessionIdentifierApplicationError: "invalid_request",
    SessionCorruptApplicationError: "persistence_corrupt",
    SessionPersistenceUnavailableApplicationError: "internal_error",
    SessionAlreadyExistsApplicationError: "persistence_conflict",
}

_READINESS_ERROR_MAP = {
    ReadinessPackageNotFoundApplicationError: "artifact_not_found",
    ReadinessStoreCorruptApplicationError: "persistence_corrupt",
    ReadinessDigestMismatchApplicationError: "artifact_binding_mismatch",
    ReadinessPackageStaleApplicationError: "artifact_stale",
    ReadinessPersistenceUnavailableApplicationError: "internal_error",
    ReadinessSessionNotConfirmedApplicationError: "readiness_incomplete",
}

# Disclosed limitation (see module docstring): PublicationApplicationService
# (Phase 145F) collapses MissingAuthorizationError/InvalidAuthorizationError/
# StaleAuthorizationError into a single PublicationAuthorizationFailedApplicationError,
# and InvalidPublicationPackageError/PublicationStorageError/
# PublicationRollbackError/AtomicPublicationFailure into a single
# PublicationExecutionFailedApplicationError. This phase's own Error Mapping
# rules forbid the CLI from reaching beneath the application-error boundary
# to interpret the wrapped coordinator exception (even via __cause__) to
# recover the lost distinction, so a single, safe, exit-1 error_type is used
# for each collapsed class rather than guessing. A future phase narrowly
# widening PublicationApplicationService's own error taxonomy (not this
# phase's authorized scope) would let the CLI regain full §19 granularity.
_PUBLICATION_ERROR_MAP = {
    PublicationAlreadyCompletedApplicationError: "publication_already_completed",
    PublicationAttemptConflictApplicationError: "persistence_conflict",
    PublicationAuthorizationFailedApplicationError: "authorization_invalid",
    PublicationExecutionFailedApplicationError: "publication_conflict",
    PublicationReconciliationIncompleteApplicationError: "internal_error",
}

_ALL_ERROR_MAPS = {**_SESSION_ERROR_MAP, **_READINESS_ERROR_MAP, **_PUBLICATION_ERROR_MAP}


def _handle_application_error(args: argparse.Namespace, exc: ApplicationServiceError) -> int:
    error_type = _ALL_ERROR_MAPS.get(type(exc), "internal_error")
    return _emit_error(
        args,
        error_type,
        str(exc),
        session_id=exc.session_id,
        package_id=exc.package_id,
        record_id=exc.record_id,
    )


def run_with_error_mapping(args: argparse.Namespace, body) -> int:
    """Shared handler wrapper: run ``body()``, mapping every raised
    exception through the closed taxonomy before it can reach the
    caller (IWPC-REQ-034/134/137) -- never a raw traceback in either
    output mode.
    """

    try:
        return body()
    except ApplicationServiceError as exc:
        return _handle_application_error(args, exc)
    except ValueError as exc:
        # Structural/path-safety rejections raised beneath the
        # application-error boundary (e.g. an unsafe package_id) are
        # re-expressed as invalid_request rather than propagated raw
        # (IWPC-REQ-135/163).
        return _emit_error(args, "invalid_request", "The supplied identifier is not valid.")
    except Exception:
        return _emit_error(args, "internal_error", "An unexpected internal error occurred.")


# -- decision-session create (IWPC-REQ-014, IWPC-REQ-015) --------------------


def run_decision_session_create(args: argparse.Namespace) -> int:
    for field_name, value in (
        ("template-ref", args.template_ref),
        ("subject-ref", args.subject_ref),
        ("owner-id", args.owner_id),
    ):
        exit_code = _require_nonempty(args, field_name, value)
        if exit_code is not None:
            return exit_code

    def body() -> int:
        context = build_application_context()
        session = context.session_service.create_session(
            owner_identity=args.owner_id,
            template_ref=args.template_ref,
            subject_ref=args.subject_ref,
        )
        payload = {"status": "success", "schema_version": SCHEMA_VERSION, "session": to_payload(session)}
        if getattr(args, "json", False):
            _print_json(payload)
        else:
            print(f"session_id: {session.session_id}")
            print(f"session_state: {session.session_state.value}")
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


# -- decision-session status (IWPC-REQ-022) ----------------------------------


def run_decision_session_status(args: argparse.Namespace) -> int:
    exit_code = _require_nonempty(args, "session-id (positional)", args.session_id)
    if exit_code is not None:
        return exit_code

    def body() -> int:
        context = build_application_context()
        session = context.session_service.load_session(args.session_id)

        # Disclosed limitation: FilesystemPendingReadinessStore.find_by_session_id
        # (Phase 145E, unmodified) deliberately never returns a consumed/
        # record for a session_id-keyed lookup (only a package_id-keyed
        # `load` sees it, IWPC-REQ-090) -- so once a package is published,
        # this reports "none", not "consumed". Reported here unchanged
        # rather than worked around, since resolving it would require a
        # new store-layer enumeration method this phase's scope forbids
        # adding merely to make the CLI more convenient.
        pending_record = context.publication_service.find_readiness_package_for_session(args.session_id)
        readiness_status = "none"
        if pending_record is not None:
            readiness_status = (
                "consumed" if pending_record.disposition == DISPOSITION_CONSUMED else "pending"
            )

        payload = {
            "status": "success",
            "schema_version": SCHEMA_VERSION,
            "session": to_payload(session),
            "readiness_package_status": readiness_status,
        }
        if getattr(args, "json", False):
            _print_json(payload)
        else:
            print(f"session_id: {session.session_id}")
            print(f"session_state: {session.session_state.value}")
            print(f"readiness_package_status: {readiness_status}")
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


# -- decision-session readiness (IWPC-REQ-023) -------------------------------
#
# Read/inspect path only -- see module docstring for the disclosed
# construction-path (IWPC-REQ-024) limitation.


def run_decision_session_readiness(args: argparse.Namespace) -> int:
    exit_code = _require_nonempty(args, "session-id (positional)", args.session_id)
    if exit_code is not None:
        return exit_code

    def body() -> int:
        context = build_application_context()
        # Resolves/validates the session first so a malformed session_id
        # is rejected via the already-established, already-tested
        # SessionApplicationService.load_session path rather than a
        # second, independent identifier-validation call.
        context.session_service.load_session(args.session_id)

        record = context.publication_service.find_readiness_package_for_session(args.session_id)
        if record is None:
            return _emit_error(
                args,
                "readiness_incomplete",
                f"No pending readiness package exists yet for session {args.session_id!r}.",
                session_id=args.session_id,
            )

        payload = {
            "status": "success",
            "schema_version": SCHEMA_VERSION,
            "package_id": record.package_id,
            "session_id": record.session_id,
            "package_digest": record.package_digest,
            "persisted_at": record.persisted_at,
            "disposition": record.disposition,
            "record_id": record.record_id,
            "consumed_at": record.consumed_at,
        }
        if getattr(args, "json", False):
            _print_json(payload)
        else:
            print(f"package_id: {record.package_id}")
            print(f"disposition: {record.disposition}")
            print(f"persisted_at: {record.persisted_at}")
            if record.record_id is not None:
                print(f"record_id: {record.record_id}")
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


# Public alias: this phase's other transport adapter
# (``pcae.commands.governance_record``'s ``publish`` command) reuses this
# module's error-envelope rendering rather than duplicating it.
emit_error = _emit_error


__all__ = [
    "ApplicationContext",
    "build_application_context",
    "run_with_error_mapping",
    "run_decision_session_create",
    "run_decision_session_status",
    "run_decision_session_readiness",
    "emit_error",
    "EXIT_SUCCESS",
    "EXIT_GENERIC_DOMAIN_FAILURE",
    "EXIT_INVALID_STATE_TRANSITION",
    "EXIT_CONFIRMATION_CONFLICT",
    "EXIT_AUTHORIZATION_REPLAY",
    "EXIT_STALE_AUTHORIZATION",
]
