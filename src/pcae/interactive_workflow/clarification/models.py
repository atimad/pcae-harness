"""Immutable Clarification domain model (IWC-001 v1.1 §9, Phase 143M).

A ``Clarification`` records one request/response exchange and, optionally,
informational tags describing it. Every mutation returns a new frozen
instance (mirrors ``Session.with_state``, Phase 143K) -- nothing here is
ever mutated in place, so a caller holding an earlier reference always
sees the state as it was when that reference was produced (IWC-REQ-096:
every exchange is retained, never overwritten).

Tags are the sole mechanism this model exposes for classifying a
clarification, and every tag is checked against the four forbidden labels
IWC-001 v1.1 §9.1 names (Recommendation, Persuasion) plus the two
publication-adjacent labels a clarification must never be mistaken for
(Approval, Authorization/Decision) at construction time -- there is no
path to attach a forbidden label and inspect the result afterward; the
rejection is synchronous (IWC-REQ-093, IWC-REQ-094, IWC-REQ-095).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

from pcae.interactive_workflow.errors import InvalidClarificationError

CLARIFICATION_SCHEMA_VERSION = "interactive-workflow-clarification/0.1"

_FORBIDDEN_CLASSIFICATIONS = frozenset(
    {"recommendation", "persuasion", "approval", "authorization", "decision"}
)


class ClarificationState(str, Enum):
    """A clarification's lifecycle: requested, then (at most once)
    responded. No third state exists -- there is no "recommended,"
    "approved," or "decided" state for a clarification to reach
    (IWC-001 v1.1 §9.1's four-act boundary)."""

    REQUESTED = "Requested"
    RESPONDED = "Responded"


def validate_classification_tag(tag: str) -> str:
    """Raise ``InvalidClarificationError`` if ``tag``, case- and
    whitespace-normalized, names a forbidden classification
    (recommendation/persuasion/approval/authorization/decision).
    Returns ``tag`` unchanged on success."""

    if not isinstance(tag, str) or not tag.strip():
        raise InvalidClarificationError("A classification tag must be a non-empty string.")
    normalized = tag.strip().casefold()
    if normalized in _FORBIDDEN_CLASSIFICATIONS:
        raise InvalidClarificationError(
            f"Classification tag {tag!r} would classify a Clarification as a "
            "recommendation, persuasion, approval, authorization, or decision -- "
            "forbidden by IWC-001 v1.1 §9's informational-only boundary "
            "(IWC-REQ-093, IWC-REQ-094, IWC-REQ-095)."
        )
    return tag


@dataclass(frozen=True)
class Clarification:
    """A single clarification exchange, informational only."""

    clarification_id: str
    request_text: str
    requested_at: str
    lifecycle_state: ClarificationState = ClarificationState.REQUESTED
    response_text: Optional[str] = None
    responded_at: Optional[str] = None
    tags: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.clarification_id:
            raise ValueError("Clarification.clarification_id must be non-empty.")
        if not self.request_text:
            raise ValueError("Clarification.request_text must be non-empty.")
        if not self.requested_at:
            raise ValueError("Clarification.requested_at must be non-empty.")
        if not isinstance(self.lifecycle_state, ClarificationState):
            raise ValueError(
                f"Clarification.lifecycle_state must be a ClarificationState member, "
                f"got {self.lifecycle_state!r}."
            )
        if self.lifecycle_state is ClarificationState.RESPONDED:
            if not self.response_text:
                raise ValueError(
                    "Clarification.response_text must be non-empty when lifecycle_state "
                    "is Responded."
                )
            if not self.responded_at:
                raise ValueError(
                    "Clarification.responded_at must be non-empty when lifecycle_state "
                    "is Responded."
                )
        for tag in self.tags:
            validate_classification_tag(tag)
        object.__setattr__(self, "tags", tuple(self.tags))

    def with_response(self, response_text: str, responded_at: str) -> "Clarification":
        """Return a new, Responded ``Clarification``.

        Raises ``InvalidClarificationError`` if this clarification
        already has a response -- a response is never overwritten
        (IWC-REQ-096's verbatim-retention requirement, restated as a
        structural guard).
        """

        if self.lifecycle_state is ClarificationState.RESPONDED:
            raise InvalidClarificationError(
                f"Clarification {self.clarification_id!r} already has a response; "
                "a response is never overwritten."
            )
        return Clarification(
            clarification_id=self.clarification_id,
            request_text=self.request_text,
            requested_at=self.requested_at,
            lifecycle_state=ClarificationState.RESPONDED,
            response_text=response_text,
            responded_at=responded_at,
            tags=self.tags,
        )

    def with_tag(self, tag: str) -> "Clarification":
        """Return a new ``Clarification`` with ``tag`` appended.

        Raises ``InvalidClarificationError`` via
        ``validate_classification_tag`` if ``tag`` names a forbidden
        classification.
        """

        validate_classification_tag(tag)
        return Clarification(
            clarification_id=self.clarification_id,
            request_text=self.request_text,
            requested_at=self.requested_at,
            lifecycle_state=self.lifecycle_state,
            response_text=self.response_text,
            responded_at=self.responded_at,
            tags=self.tags + (tag,),
        )


__all__ = [
    "CLARIFICATION_SCHEMA_VERSION",
    "ClarificationState",
    "Clarification",
    "validate_classification_tag",
]
