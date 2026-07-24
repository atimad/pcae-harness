"""Immutable Confirmation domain models (IWC-001 v1.1 §10, Phase 143N).

A ``ConfirmationRequest`` records the intent to confirm a specific,
already-built Preview, bound by identifier and digest (IWC-001 v1.1
§10.3's exact-content-binding discipline: a confirming action must carry
evidence tied to "this specific, currently-valid Preview Digest," never
merely "the current state of the session"). A ``ConfirmationResponse``
records the distinct, deliberate confirming act itself, re-asserting the
same Preview Digest so the Confirmation Controller
(``pcae.interactive_workflow.confirmation.controller``) can verify it
still matches the request it answers immediately before acceptance
(IWC-001 v1.1 §10.2).

Neither model carries an authority token, a publication-state field, or a
CHGR identifier -- this phase implements confirmation-readiness
infrastructure only, never authorization, execution, or Publication
(this phase's governing prompt, "Confirmation Infrastructure").

``ConfirmationResult`` intentionally has exactly one member,
``ACCEPTED``: a confirming action that fails any Confirmation Controller
check (digest mismatch, staleness, replay, duplicate) is rejected via a
raised error and never becomes a stored ``ConfirmationResponse`` --
mirroring IWC-001 v1.1 §10's fail-closed discipline, there is no
"Rejected" record to construct, since a rejected attempt produces no
artifact at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional

from pcae.interactive_workflow.session.identity import validate_session_id

CONFIRMATION_SCHEMA_VERSION = "interactive-workflow-confirmation/0.1"


def _frozen_metadata(value: Optional[Mapping[str, object]]) -> Mapping[str, object]:
    if value is None:
        return MappingProxyType({})
    return MappingProxyType(dict(value))


class ConfirmationResult(str, Enum):
    """The outcome a stored ``ConfirmationResponse`` records. See module
    docstring for why only one member exists."""

    ACCEPTED = "Accepted"


@dataclass(frozen=True)
class ConfirmationRequest:
    """A single, immutable request to confirm one Preview."""

    request_id: str
    session_id: str
    preview_id: str
    preview_digest: str
    created_at: str
    schema_version: str = CONFIRMATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.request_id:
            raise ValueError("ConfirmationRequest.request_id must be non-empty.")
        validate_session_id(self.session_id)
        if not self.preview_id:
            raise ValueError("ConfirmationRequest.preview_id must be non-empty.")
        if not self.preview_digest:
            raise ValueError("ConfirmationRequest.preview_digest must be non-empty.")
        if not self.created_at:
            raise ValueError("ConfirmationRequest.created_at must be non-empty.")
        if not self.schema_version:
            raise ValueError("ConfirmationRequest.schema_version must be non-empty.")


@dataclass(frozen=True)
class ConfirmationResponse:
    """A single, immutable record of a completed confirming act.

    ``request_id`` binds this response to the exact
    ``ConfirmationRequest`` it answers -- necessary for the Confirmation
    Controller to attribute a response to one request and verify digest
    match, even though it is not itself a governance-authority field.
    """

    response_id: str
    request_id: str
    confirmed_at: str
    confirmation_result: ConfirmationResult
    preview_digest: str
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    schema_version: str = CONFIRMATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.response_id:
            raise ValueError("ConfirmationResponse.response_id must be non-empty.")
        if not self.request_id:
            raise ValueError("ConfirmationResponse.request_id must be non-empty.")
        if not self.confirmed_at:
            raise ValueError("ConfirmationResponse.confirmed_at must be non-empty.")
        if not isinstance(self.confirmation_result, ConfirmationResult):
            raise ValueError(
                "ConfirmationResponse.confirmation_result must be a ConfirmationResult "
                f"member, got {self.confirmation_result!r}."
            )
        if not self.preview_digest:
            raise ValueError("ConfirmationResponse.preview_digest must be non-empty.")
        if not self.schema_version:
            raise ValueError("ConfirmationResponse.schema_version must be non-empty.")
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))


__all__ = [
    "CONFIRMATION_SCHEMA_VERSION",
    "ConfirmationResult",
    "ConfirmationRequest",
    "ConfirmationResponse",
]
