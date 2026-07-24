"""Deterministic serialization for Publication Coordinator models (Phase
144C; governing prompt, "Serialization").

Serializes only ``PublicationExecutionResult`` and
``PublicationExecutionContext``. Never serializes authorization secrets
(there are none on either model -- ``operator_id`` is an identity
reference, not a credential), runtime state, or Interactive Workflow
state, mirroring the same exclusion discipline
``interactive_workflow/serialization/publication_handoff_schema.py``
already applies to ``PublicationReadinessPackage``.
"""
from __future__ import annotations

from typing import Any, Dict

from pcae.governance.publication.models import (
    PUBLICATION_EXECUTION_SCHEMA_VERSION,
    PublicationExecutionContext,
    PublicationExecutionResult,
)

_KNOWN_SCHEMA_VERSIONS = frozenset({PUBLICATION_EXECUTION_SCHEMA_VERSION})


class PublicationExecutionSerializationError(Exception):
    """A payload could not be deserialized into a Publication Coordinator
    model: missing/malformed field, or an unrecognized schema version."""


def context_to_payload(context: PublicationExecutionContext) -> Dict[str, Any]:
    return {
        "schema_version": context.schema_version,
        "attempt_id": context.attempt_id,
        "package_id": context.package_id,
        "session_id": context.session_id,
        "operator_id": context.operator_id,
        "authorization_event_id": context.authorization_event_id,
        "authorization_invoked_at": context.authorization_invoked_at,
        "evaluated_at": context.evaluated_at,
    }


def context_from_payload(payload: Dict[str, Any]) -> PublicationExecutionContext:
    try:
        schema_version = payload["schema_version"]
        if schema_version not in _KNOWN_SCHEMA_VERSIONS:
            raise PublicationExecutionSerializationError(
                f"Unsupported PublicationExecutionContext schema_version {schema_version!r}."
            )
        return PublicationExecutionContext(
            attempt_id=payload["attempt_id"],
            package_id=payload["package_id"],
            session_id=payload["session_id"],
            operator_id=payload["operator_id"],
            authorization_event_id=payload["authorization_event_id"],
            authorization_invoked_at=payload["authorization_invoked_at"],
            evaluated_at=payload["evaluated_at"],
            schema_version=schema_version,
        )
    except PublicationExecutionSerializationError:
        raise
    except (KeyError, ValueError, TypeError) as exc:
        raise PublicationExecutionSerializationError(
            f"Malformed PublicationExecutionContext payload: {exc}"
        ) from exc


def result_to_payload(result: PublicationExecutionResult) -> Dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "attempt_id": result.attempt_id,
        "success": result.success,
        "package_id": result.package_id,
        "session_id": result.session_id,
        "record_id": result.record_id,
        "diagnostics": list(result.diagnostics),
        "evaluated_at": result.evaluated_at,
        "completed_at": result.completed_at,
        "error_type": result.error_type,
        "failure_reason": result.failure_reason,
    }


def result_from_payload(payload: Dict[str, Any]) -> PublicationExecutionResult:
    try:
        schema_version = payload["schema_version"]
        if schema_version not in _KNOWN_SCHEMA_VERSIONS:
            raise PublicationExecutionSerializationError(
                f"Unsupported PublicationExecutionResult schema_version {schema_version!r}."
            )
        return PublicationExecutionResult(
            attempt_id=payload["attempt_id"],
            success=payload["success"],
            package_id=payload["package_id"],
            session_id=payload["session_id"],
            record_id=payload["record_id"],
            diagnostics=tuple(payload["diagnostics"]),
            evaluated_at=payload["evaluated_at"],
            completed_at=payload["completed_at"],
            error_type=payload["error_type"],
            failure_reason=payload["failure_reason"],
            schema_version=schema_version,
        )
    except PublicationExecutionSerializationError:
        raise
    except (KeyError, ValueError, TypeError) as exc:
        raise PublicationExecutionSerializationError(
            f"Malformed PublicationExecutionResult payload: {exc}"
        ) from exc


__all__ = [
    "PublicationExecutionSerializationError",
    "context_from_payload",
    "context_to_payload",
    "result_from_payload",
    "result_to_payload",
]
