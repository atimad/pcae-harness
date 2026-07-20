"""``pcae authority inspect <path>`` — production Typed Authority Model consumer CLI.

Implements the CLI layer of TAMPC-001 v1.0. This module owns only: CLI
argument definition, the Stage 1 bounded artifact read (TAMPC-REQ-021's
ownership split), invocation of
``pcae.cltr.authority_inspection.inspect_artifact_at_path``, selection and
rendering of the frozen output format, stdout routing, and exit-code
translation. All business logic (parsing, resource resolution, schema/
model validation, provenance) lives in
``pcae.cltr.authority_inspection`` and is not duplicated here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.cltr.authority_inspection import (
    InspectionFailure,
    InspectionObservation,
    InspectionOutcome,
    inspect_artifact_at_path,
)
from pcae.schema_runtime import DEFAULT_MAX_INPUT_BYTES

_DISCLOSURE_LINE = (
    "[representation-only, non-authoritative — see disclosure]"
)

_HUMAN_FIELD_ORDER = (
    "outcome",
    "consumer_identity",
    "tamc_contract_version",
    "tampc_contract_version",
    "source_artifact_identity",
    "input_digest",
    "record_family",
    "record_identity",
    "schema_identity",
    "schema_version",
    "model_version",
    "declared_record_digest",
    "message",
    "disclosure",
)


def _read_artifact(path_arg: str) -> tuple[bytes, None] | tuple[None, InspectionFailure]:
    """Stage 1 bounded read (TAMPC-REQ-021's CLI-layer ownership split).

    Returns ``(bytes, None)`` on success or ``(None, InspectionFailure)`` on
    a classified read failure. Performs exactly one ``stat()`` and, if the
    size gate passes, one ``open()``/read — no re-stat, no re-read.
    """

    path = Path(path_arg)
    try:
        resolved_exists = path.exists()
    except OSError:
        resolved_exists = False
    if not resolved_exists:
        return None, InspectionFailure(
            outcome="input_not_found",
            message="The supplied path does not resolve to an existing file.",
            source_artifact_identity=path_arg,
            input_digest="unavailable",
        )

    try:
        is_file = path.is_file()
    except OSError:
        is_file = False
    if not is_file:
        return None, InspectionFailure(
            outcome="input_not_a_file",
            message="The supplied path is not a regular file.",
            source_artifact_identity=path_arg,
            input_digest="unavailable",
        )

    try:
        size = path.stat().st_size
    except OSError:
        return None, InspectionFailure(
            outcome="input_unreadable",
            message="The supplied path could not be read.",
            source_artifact_identity=path_arg,
            input_digest="unavailable",
        )
    if size == 0:
        return None, InspectionFailure(
            outcome="malformed_artifact",
            message="The supplied artifact is empty.",
            source_artifact_identity=path_arg,
            input_digest="unavailable",
        )
    if size > DEFAULT_MAX_INPUT_BYTES:
        return None, InspectionFailure(
            outcome="malformed_artifact",
            message="The supplied artifact exceeds the maximum permitted size.",
            source_artifact_identity=path_arg,
            input_digest="unavailable",
        )

    try:
        data = path.read_bytes()
    except OSError:
        return None, InspectionFailure(
            outcome="input_unreadable",
            message="The supplied path could not be read.",
            source_artifact_identity=path_arg,
            input_digest="unavailable",
        )
    return data, None


def _render(outcome: InspectionOutcome, *, as_json: bool) -> None:
    payload = outcome.to_dict()
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    print(_DISCLOSURE_LINE)
    for key in _HUMAN_FIELD_ORDER:
        if key in payload:
            print(f"  {key}: {payload[key]}")


def run_authority_inspect(args: argparse.Namespace) -> int:
    as_json = getattr(args, "json", False)
    artifact_bytes, read_failure = _read_artifact(args.path)
    if read_failure is not None:
        _render(read_failure, as_json=as_json)
        return 1

    outcome = inspect_artifact_at_path(
        Path(args.path), artifact_bytes=artifact_bytes, json_output=as_json
    )
    _render(outcome, as_json=as_json)
    return 0 if isinstance(outcome, InspectionObservation) else 1


__all__ = ["run_authority_inspect"]
