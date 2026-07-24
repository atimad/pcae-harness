"""Deterministic wire representation of ``ConfirmationRequest`` and
``ConfirmationResponse`` (Phase 143N).

Raises ``ConfirmationSerializationFailureError`` (not the generic
``SerializationFailureError``) on any round-trip failure, so a caller can
distinguish which artifact class failed to serialize -- mirroring Phase
143M's ``AuditSerializationFailureError`` split. Round-trips fully or
raises -- no partial write, no silent fallback for an unrecognized
``schema_version``. Does not serialize CHGR, publication, or execution
state -- none of those fields exist on either model (see
``pcae.interactive_workflow.confirmation.models``).
"""

from __future__ import annotations

from typing import Any, Dict

from pcae.interactive_workflow.confirmation.models import (
    CONFIRMATION_SCHEMA_VERSION,
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationResult,
)
from pcae.interactive_workflow.errors import (
    ConfirmationSerializationFailureError,
    UnsupportedVersionError,
)

_KNOWN_SCHEMA_VERSIONS = frozenset({CONFIRMATION_SCHEMA_VERSION})


def request_to_payload(request: ConfirmationRequest) -> Dict[str, Any]:
    try:
        return {
            "schema_version": request.schema_version,
            "request_id": request.request_id,
            "session_id": request.session_id,
            "preview_id": request.preview_id,
            "preview_digest": request.preview_digest,
            "created_at": request.created_at,
        }
    except AttributeError as exc:
        raise ConfirmationSerializationFailureError(
            f"ConfirmationRequest could not be serialized: {exc}"
        ) from exc


def request_from_payload(payload: Dict[str, Any]) -> ConfirmationRequest:
    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(
            f"Unsupported ConfirmationRequest schema_version: {schema_version!r}."
        )
    try:
        return ConfirmationRequest(
            request_id=payload["request_id"],
            session_id=payload["session_id"],
            preview_id=payload["preview_id"],
            preview_digest=payload["preview_digest"],
            created_at=payload["created_at"],
            schema_version=schema_version,
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise ConfirmationSerializationFailureError(
            f"ConfirmationRequest payload malformed: {exc}"
        ) from exc


def response_to_payload(response: ConfirmationResponse) -> Dict[str, Any]:
    try:
        return {
            "schema_version": response.schema_version,
            "response_id": response.response_id,
            "request_id": response.request_id,
            "confirmed_at": response.confirmed_at,
            "confirmation_result": response.confirmation_result.value,
            "preview_digest": response.preview_digest,
            "metadata": dict(response.metadata),
        }
    except AttributeError as exc:
        raise ConfirmationSerializationFailureError(
            f"ConfirmationResponse could not be serialized: {exc}"
        ) from exc


def response_from_payload(payload: Dict[str, Any]) -> ConfirmationResponse:
    schema_version = payload.get("schema_version")
    if schema_version not in _KNOWN_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(
            f"Unsupported ConfirmationResponse schema_version: {schema_version!r}."
        )
    try:
        return ConfirmationResponse(
            response_id=payload["response_id"],
            request_id=payload["request_id"],
            confirmed_at=payload["confirmed_at"],
            confirmation_result=ConfirmationResult(payload["confirmation_result"]),
            preview_digest=payload["preview_digest"],
            metadata=payload.get("metadata", {}),
            schema_version=schema_version,
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise ConfirmationSerializationFailureError(
            f"ConfirmationResponse payload malformed: {exc}"
        ) from exc


__all__ = [
    "CONFIRMATION_SCHEMA_VERSION",
    "request_to_payload",
    "request_from_payload",
    "response_to_payload",
    "response_from_payload",
]
