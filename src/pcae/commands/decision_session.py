"""``pcae decision-session ...`` -- IWPC-001 v1.2 CLI/transport adapter
(Phase 145G; command surface completed and readiness construction
repaired by Phase 145G.1; decision-selection command and
``AwaitingDecision`` reachability repaired by Phase 145G.2).

Implements every ``decision-session`` sub-command IWPC-001 v1.2 §5 names:
``create``, ``evidence``, ``select``, ``clarify``, ``preview``,
``confirm``, ``status``, ``readiness``, and ``cancel``.

This module is the transport adapter (IWPC-REQ-006): it parses CLI
arguments, constructs the frozen application request inputs, invokes
``SessionApplicationService``/``PublicationApplicationService`` (Phase
145F, extended narrowly by Phase 145G.1 and Phase 145G.2 -- see
``pcae.interactive_workflow.application.session_service``), renders
deterministic output, and maps every application-layer error to the
closed exit-code/``error_type`` taxonomy (IWPC-001 §9, §19). It never
imports ``SessionCoordinator``, ``WorkflowOrchestrator``, or
``PublicationCoordinator`` outside this module's own narrow composition
root (``build_application_context``), never reads/writes session or
pending-readiness JSON directly, and never evaluates authority or
reimplements a workflow decision.

Phase 145G disclosed Blocking finding F-145G-1: ``evidence``/``clarify``/
``preview``/``confirm``/``cancel`` could not be implemented because no
store anywhere in this repository persisted orchestration-stage progress,
registered evidence, clarification exchanges, or confirmation artifacts
across separate CLI process invocations. Phase 145G.1 closed that gap --
see ``pcae.interactive_workflow.persistence.filesystem_orchestration_store``
and ``pcae.interactive_workflow.application.session_service`` for the
persisted orchestration-record design and the six rehydrated
``WorkflowOrchestrator`` collaborators. Phase 145G.1 then disclosed
Blocking finding F-145G.1-1: no command in IWPC-001 v1.1's frozen §5
command surface transitioned a session out of ``AwaitingDecision``, so
``clarify``/``preview``/``confirm``/readiness were all implemented
correctly but reachable only via direct session-state bridging, never a
real CLI-only invocation sequence.

**Phase 145G.2 closes F-145G.1-1.** IWPC-001 v1.2 §5 adds
``decision-session select`` (IWPC-REQ-192-196, see
``run_decision_session_select`` below), which drives both the
``EvidenceReady`` -> ``AwaitingDecision`` sequencing hop and the
``AwaitingDecision`` -> ``DecisionSelected`` decision-capture hop in one
call (a disclosed single-invocation design choice mirroring
``evidence``'s own Phase 145G.1 precedent -- see
``SessionApplicationService.select_decision``'s docstring). ``preview``
and ``confirm`` are now reachable through a genuine CLI-only path:
``create`` -> ``evidence`` -> ``select`` -> ``preview`` -> ``confirm`` ->
``readiness`` -> ``governance-record publish``.

**Residual, disclosed gap Phase 145G.2 found and did NOT close, out of
its own authorized "decision selection" scope (F-145G.2-1):** no command
transitions a session from ``AwaitingDecision`` into
``AwaitingClarification`` -- ``clarify`` itself only answers a
clarification already in progress (``AwaitingClarification`` ->
``AwaitingDecision``), it does not open one. This is a structurally
identical, but distinct, reachability gap from F-145G.1-1: the
*clarification* path specifically remains reachable only via the same
test-fixture session-state bridge Phase 145G.1's own test suite already
used for this exact reason (see
``tests/test_phase_145g1_decision_session_cli_repair.py``'s
``_bridge_session_state`` calls, preserved unchanged by this phase).
Closing F-145G.2-1 would require a further, separately-authorized
contract revision adding a "request clarification" command -- a
genuinely different operation from decision selection, which this
phase's own governing prompt forbids inventing under this phase's
authorization. See the Phase 145G.2 canonical report for full
reproduction evidence and disposition.
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
    SessionConfirmationConflictApplicationError,
    SessionCorruptApplicationError,
    SessionInvalidTransitionApplicationError,
    SessionNotFoundApplicationError,
    SessionOrchestrationCorruptApplicationError,
    SessionOrchestrationPersistenceUnavailableApplicationError,
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
    SessionInvalidTransitionApplicationError: "invalid_state_transition",
    SessionConfirmationConflictApplicationError: "confirmation_conflict",
    SessionOrchestrationCorruptApplicationError: "persistence_corrupt",
    SessionOrchestrationPersistenceUnavailableApplicationError: "internal_error",
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


# -- decision-session evidence (IWPC-REQ-016) --------------------------------


def run_decision_session_evidence(args: argparse.Namespace) -> int:
    exit_code = _require_nonempty(args, "session-id (positional)", args.session_id)
    if exit_code is not None:
        return exit_code
    declared = list(args.declare or [])
    if not declared:
        return _emit_error(args, "invalid_request", "At least one --declare value is required.")
    for value in declared:
        exit_code = _require_nonempty(args, "declare", value)
        if exit_code is not None:
            return exit_code

    def body() -> int:
        context = build_application_context()
        session = context.session_service.submit_evidence(args.session_id, declared)
        payload = {"status": "success", "schema_version": SCHEMA_VERSION, "session": to_payload(session)}
        if getattr(args, "json", False):
            _print_json(payload)
        else:
            print(f"session_id: {session.session_id}")
            print(f"session_state: {session.session_state.value}")
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


# -- decision-session select (IWPC-REQ-192-196, Phase 145G.2) ----------------


def run_decision_session_select(args: argparse.Namespace) -> int:
    exit_code = _require_nonempty(args, "session-id (positional)", args.session_id)
    if exit_code is not None:
        return exit_code
    exit_code = _require_nonempty(args, "option-id", args.option_id)
    if exit_code is not None:
        return exit_code
    exit_code = _require_nonempty(args, "template-version", args.template_version)
    if exit_code is not None:
        return exit_code

    presented = list(args.options_presented or [])
    if not presented:
        return _emit_error(args, "invalid_request", "At least one --options-presented value is required.")
    for value in presented:
        exit_code = _require_nonempty(args, "options-presented", value)
        if exit_code is not None:
            return exit_code
    if len(set(presented)) != len(presented):
        return _emit_error(args, "invalid_request", "--options-presented must not contain duplicates.")
    if args.option_id not in presented:
        return _emit_error(
            args, "invalid_request", "--option-id must be a member of the declared --options-presented set."
        )

    rationale = args.rationale if args.rationale else None
    conditions = args.conditions if args.conditions else None

    def body() -> int:
        context = build_application_context()
        session = context.session_service.select_decision(
            args.session_id,
            option_id=args.option_id,
            options_presented=tuple(presented),
            template_version=args.template_version,
            rationale=rationale,
            conditions=conditions,
        )
        payload = {"status": "success", "schema_version": SCHEMA_VERSION, "session": to_payload(session)}
        if getattr(args, "json", False):
            _print_json(payload)
        else:
            print(f"session_id: {session.session_id}")
            print(f"session_state: {session.session_state.value}")
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


# -- decision-session clarify (IWPC-REQ-017) ----------------------------------


def run_decision_session_clarify(args: argparse.Namespace) -> int:
    exit_code = _require_nonempty(args, "session-id (positional)", args.session_id)
    if exit_code is not None:
        return exit_code
    for field_name, value in (("question", args.question), ("answer", args.answer)):
        exit_code = _require_nonempty(args, field_name, value)
        if exit_code is not None:
            return exit_code

    def body() -> int:
        context = build_application_context()
        session = context.session_service.submit_clarification(args.session_id, args.question, args.answer)
        payload = {"status": "success", "schema_version": SCHEMA_VERSION, "session": to_payload(session)}
        if getattr(args, "json", False):
            _print_json(payload)
        else:
            print(f"session_id: {session.session_id}")
            print(f"session_state: {session.session_state.value}")
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


# -- decision-session preview (IWPC-REQ-018/019) -------------------------------


def run_decision_session_preview(args: argparse.Namespace) -> int:
    exit_code = _require_nonempty(args, "session-id (positional)", args.session_id)
    if exit_code is not None:
        return exit_code

    def body() -> int:
        context = build_application_context()
        preview, preview_digest = context.session_service.generate_preview(args.session_id)
        payload = {
            "status": "success",
            "schema_version": SCHEMA_VERSION,
            "preview_id": preview.preview_id,
            "session_id": preview.session_id,
            "preview_digest": preview_digest,
            "preview_timestamp": preview.preview_timestamp,
            "evidence_refs": list(preview.evidence_refs),
            "clarification_refs": list(preview.clarification_refs),
            "audit_refs": list(preview.audit_refs),
            "rendered_content": preview.rendered_content,
        }
        if getattr(args, "json", False):
            _print_json(payload)
        else:
            print(f"preview_id: {preview.preview_id}")
            print(f"preview_digest: {preview_digest}")
            print(preview.rendered_content)
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


# -- decision-session confirm (IWPC-REQ-020/021) -------------------------------


def run_decision_session_confirm(args: argparse.Namespace) -> int:
    exit_code = _require_nonempty(args, "session-id (positional)", args.session_id)
    if exit_code is not None:
        return exit_code
    for field_name, value in (
        ("preview-digest", args.preview_digest),
        ("statement", args.statement),
    ):
        exit_code = _require_nonempty(args, field_name, value)
        if exit_code is not None:
            return exit_code

    def body() -> int:
        context = build_application_context()
        session = context.session_service.record_confirmation(
            args.session_id, args.preview_digest, args.statement
        )
        payload = {"status": "success", "schema_version": SCHEMA_VERSION, "session": to_payload(session)}
        if getattr(args, "json", False):
            _print_json(payload)
        else:
            print(f"session_id: {session.session_id}")
            print(f"session_state: {session.session_state.value}")
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


# -- decision-session cancel (IWPC-REQ-025) ------------------------------------


def run_decision_session_cancel(args: argparse.Namespace) -> int:
    exit_code = _require_nonempty(args, "session-id (positional)", args.session_id)
    if exit_code is not None:
        return exit_code
    exit_code = _require_nonempty(args, "reason", args.reason)
    if exit_code is not None:
        return exit_code

    def body() -> int:
        context = build_application_context()
        session = context.session_service.cancel_session(args.session_id, args.reason)
        payload = {"status": "success", "schema_version": SCHEMA_VERSION, "session": to_payload(session)}
        if getattr(args, "json", False):
            _print_json(payload)
        else:
            print(f"session_id: {session.session_id}")
            print(f"session_state: {session.session_state.value}")
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


# -- decision-session readiness (IWPC-REQ-023/024) -----------------------------
#
# Repaired by Phase 145G.1: the first invocation against a Confirmed
# session with no existing pending package now constructs the
# PublicationReadinessPackage (via SessionApplicationService.
# construct_readiness_package -> the unmodified PublicationHandoff.
# build_package) and persists it (via PublicationApplicationService.
# persist_readiness_package), through
# PublicationApplicationService.ensure_readiness_package's own
# idempotent-by-key sequencing -- this handler never constructs or
# persists a package itself.


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

        record = context.publication_service.ensure_readiness_package(args.session_id)

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
    "run_decision_session_evidence",
    "run_decision_session_select",
    "run_decision_session_clarify",
    "run_decision_session_preview",
    "run_decision_session_confirm",
    "run_decision_session_status",
    "run_decision_session_readiness",
    "run_decision_session_cancel",
    "emit_error",
    "EXIT_SUCCESS",
    "EXIT_GENERIC_DOMAIN_FAILURE",
    "EXIT_INVALID_STATE_TRANSITION",
    "EXIT_CONFIRMATION_CONFLICT",
    "EXIT_AUTHORIZATION_REPLAY",
    "EXIT_STALE_AUTHORIZATION",
]
