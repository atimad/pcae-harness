"""``pcae governance-record ...`` — read-only CHGR artifact CLI (Phase 143E).

Implements only the CLI layer: argument definition, bounded local file
reads, invocation of ``pcae.governance.inspection``/``pcae.governance.verification``,
output rendering, and exit-code translation. All business logic lives in
those two modules and is not duplicated here.

Every command in this module is read-only: it performs no publication, no
mutation, no lifecycle transition, and no authority resolution. There is no
``create``/``confirm``/``publish``/``suspend``/``supersede``/``revoke``/
``import`` command in this module, and none is planned for this increment.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

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


__all__ = [
    "run_governance_record_template_inspect",
    "run_governance_record_inspect",
    "run_governance_record_verify",
]
