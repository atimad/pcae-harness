"""``pcae governance-record ...`` — CHGR artifact CLI (Phase 143E read-only
inspect/verify; Phase 145G adds ``publish``).

``inspect``/``verify``/``template inspect`` implement only the CLI layer:
argument definition, bounded local file reads, invocation of
``pcae.governance.inspection``/``pcae.governance.verification``, output
rendering, and exit-code translation -- all business logic lives in those
two modules and is not duplicated here. There is no ``create``/
``confirm``/``suspend``/``supersede``/``revoke``/``import`` command in
this module, and none is planned for this increment.

``publish`` (IWPC-001 v1.1 §6, IWPC-REQ-026) is the one mutating command in
this module: the frozen addition exposing
``PublicationApplicationService`` (Phase 145F) to a human caller. It
performs no publication itself -- it constructs the transport-neutral
input, delegates authorization/execution to
``PublicationCoordinator.authorize``/``.execute`` unchanged via that
application service, and renders the verbatim result. See
``pcae.commands.decision_session`` for this phase's shared composition
root and error-taxonomy mapping, reused here rather than duplicated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.commands.decision_session import (
    EXIT_SUCCESS,
    SCHEMA_VERSION as _IWPC_SCHEMA_VERSION,
    build_application_context,
    emit_error,
    run_with_error_mapping,
)
from pcae.commands.publication_permission_gate import publish_with_permission_gate
from pcae.core.paths import HarnessPath
from pcae.governance.inspection import (
    InspectionFailure,
    InspectionObservation,
    inspect_artifact_at_path,
)
from pcae.governance.verification import (
    VerificationFailure,
    VerificationObservation,
    verify_artifact_at_path,
)
from pcae.schema_runtime import DEFAULT_MAX_INPUT_BYTES

_DISCLOSURE_LINE = "[representation-only, non-authoritative -- see disclosure]"

_INSPECT_FIELD_ORDER = (
    "outcome",
    "consumer_identity",
    "chgr_contract_version",
    "source_artifact_identity",
    "input_digest",
    "record_family",
    "record_identity",
    "schema_identity",
    "schema_version",
    "declared_record_digest",
    "message",
    "disclosure",
)

_VERIFY_FIELD_ORDER = (
    "outcome",
    "error_code",
    "consumer_identity",
    "chgr_contract_version",
    "source_artifact_identity",
    "input_digest",
    "record_family",
    "record_identity",
    "message",
    "disclosure",
)


def _read_artifact(path_arg: str) -> tuple[bytes | None, str | None]:
    """Bounded local read: one ``stat()``, one size-gated ``read_bytes()``.

    Returns ``(bytes, None)`` on success or ``(None, message)`` on a
    classified read failure.
    """
    path = Path(path_arg)
    try:
        exists = path.exists()
    except OSError:
        exists = False
    if not exists:
        return None, "The supplied path does not resolve to an existing file."

    try:
        is_file = path.is_file()
    except OSError:
        is_file = False
    if not is_file:
        return None, "The supplied path is not a regular file."

    try:
        size = path.stat().st_size
    except OSError:
        return None, "The supplied path could not be read."
    if size == 0:
        return None, "The supplied artifact is empty."
    if size > DEFAULT_MAX_INPUT_BYTES:
        return None, "The supplied artifact exceeds the maximum permitted size."

    try:
        return path.read_bytes(), None
    except OSError:
        return None, "The supplied path could not be read."


def _render_inspect(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    print(_DISCLOSURE_LINE)
    for key in _INSPECT_FIELD_ORDER:
        if key in payload:
            print(f"  {key}: {payload[key]}")


def _render_verify(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    print(_DISCLOSURE_LINE)
    for key in _VERIFY_FIELD_ORDER:
        if key in payload:
            print(f"  {key}: {payload[key]}")
    for check in payload.get("checks", []):
        print(f"    check: {check['name']:28s} {check['status']:8s} {check['detail']}")


def run_governance_record_template_inspect(args: argparse.Namespace) -> int:
    as_json = getattr(args, "json", False)
    data, read_error = _read_artifact(args.path)
    if read_error is not None:
        _render_inspect(
            {"outcome": "input_unreadable", "message": read_error, "source_artifact_identity": args.path},
            as_json=as_json,
        )
        return 1
    outcome = inspect_artifact_at_path(Path(args.path), artifact_bytes=data, json_output=as_json)
    _render_inspect(outcome.to_dict(), as_json=as_json)
    if isinstance(outcome, InspectionObservation):
        if outcome.record_family != "decision_template":
            print(f"  warning: artifact declares record_family={outcome.record_family!r}, not decision_template")
            return 1
        return 0
    return 1


def run_governance_record_inspect(args: argparse.Namespace) -> int:
    as_json = getattr(args, "json", False)
    data, read_error = _read_artifact(args.path)
    if read_error is not None:
        _render_inspect(
            {"outcome": "input_unreadable", "message": read_error, "source_artifact_identity": args.path},
            as_json=as_json,
        )
        return 1
    outcome = inspect_artifact_at_path(Path(args.path), artifact_bytes=data, json_output=as_json)
    _render_inspect(outcome.to_dict(), as_json=as_json)
    return 0 if isinstance(outcome, InspectionObservation) else 1


def run_governance_record_verify(args: argparse.Namespace) -> int:
    as_json = getattr(args, "json", False)
    data, read_error = _read_artifact(args.path)
    if read_error is not None:
        _render_verify(
            {"outcome": "rejected", "error_code": "SCHEMA_INVALID", "message": read_error, "source_artifact_identity": args.path},
            as_json=as_json,
        )
        return 1

    related_bytes = []
    for related_path in getattr(args, "related", None) or []:
        related_data, related_error = _read_artifact(related_path)
        if related_error is not None:
            _render_verify(
                {
                    "outcome": "rejected",
                    "error_code": "SCHEMA_INVALID",
                    "message": f"Related artifact {related_path!r} could not be read: {related_error}",
                    "source_artifact_identity": args.path,
                },
                as_json=as_json,
            )
            return 1
        related_bytes.append(related_data)

    outcome = verify_artifact_at_path(Path(args.path), artifact_bytes=data, related_bytes=tuple(related_bytes))
    _render_verify(outcome.to_dict(), as_json=as_json)
    return 0 if isinstance(outcome, VerificationObservation) else 1


# -- governance-record publish (IWPC-001 v1.1 §6, IWPC-REQ-026-035) --------


def run_governance_record_publish(args: argparse.Namespace) -> int:
    """``pcae governance-record publish <package-id> --operator-id <id>``.

    Non-interactive (IWPC-REQ-030): accepts only the explicit CLI
    arguments below; no ``--force``/``--assume-authorized``-equivalent
    bypass exists (IWPC-REQ-027/124). Delegates the entire authorize/
    execute sequence to ``PublicationApplicationService.resume_publication``
    unchanged (IWPC-REQ-127/128) -- that single method already implements
    both a first-attempt publish and a post-failure retry/post-restart
    resume identically, by re-reading persisted state rather than trusting
    a caller-supplied "resume" flag (IWPC-REQ-156), so this handler adds no
    second code path for "fresh" vs. "resumed" publication.
    """

    package_id = args.package_id
    operator_id = args.operator_id
    as_json = getattr(args, "json", False)

    if not package_id or not str(package_id).strip():
        return emit_error(args, "invalid_request", "<package-id> must be non-empty.")
    if not operator_id or not str(operator_id).strip():
        return emit_error(args, "invalid_request", "--operator-id must be non-empty.")

    def body() -> int:
        context = build_application_context()
        result = publish_with_permission_gate(
            context.publication_service,
            HarnessPath.cwd(),
            package_id,
            operator_id=operator_id,
        )

        payload = {
            "status": "success",
            "schema_version": _IWPC_SCHEMA_VERSION,
            "attempt_id": result.attempt_id,
            "success": result.success,
            "package_id": result.package_id,
            "session_id": result.session_id,
            "record_id": result.record_id,
            "diagnostics": list(result.diagnostics),
            "evaluated_at": result.evaluated_at,
            "completed_at": result.completed_at,
            "publication_result_schema_version": result.schema_version,
        }
        if as_json:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        else:
            print(f"record_id: {result.record_id}")
            print(f"package_id: {result.package_id}")
            print(f"session_id: {result.session_id}")
            print("status: success")
        return EXIT_SUCCESS

    return run_with_error_mapping(args, body)


__all__ = [
    "run_governance_record_template_inspect",
    "run_governance_record_inspect",
    "run_governance_record_verify",
    "run_governance_record_publish",
]
