"""Clarification Controller (IWC-001 v1.1 §9, Phase 143J §16, Phase 143M).

The sole production owner of clarification request registration,
clarification response registration, clarification ordering, and
clarification history for a single Decision Session (Phase 143J §16
Clarification Controller row). No other production component may
register a clarification request or response.

This controller does not, and per its governing phase prompt never will,
recommend, persuade, prioritize, make a decision, or transition a
session. Those methods do not exist on this class. The informational-only
boundary (IWC-001 v1.1 §9.2's objectively testable line: "could the
output be true or useful regardless of which option the human ultimately
picks") is enforced structurally by ``Clarification.with_tag`` /
``validate_classification_tag`` rejecting any attempt to label an
exchange as a recommendation, persuasion, approval, authorization, or
decision (IWC-REQ-093 through IWC-REQ-095).

Integration with the Session Infrastructure (143K) is structural and
passive only, identical in discipline to
``pcae.interactive_workflow.evidence.coordinator.EvidenceCoordinator``: a
controller is scoped to one session identifier, validated with the same
``CDS-<uuid4>`` syntax check the Session Coordinator uses, but this
module never calls ``SessionCoordinator`` or ``TransitionEngine``.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from pcae.interactive_workflow.clarification.models import Clarification
from pcae.interactive_workflow.errors import (
    DuplicateClarificationError,
    InvalidClarificationError,
)
from pcae.interactive_workflow.session.identity import validate_session_id


class ClarificationController:
    """Registers requests/responses and preserves ordering and history
    for exactly one Decision Session's clarification exchanges."""

    def __init__(self, session_id: str) -> None:
        self._session_id = validate_session_id(session_id)
        self._log: Dict[str, Clarification] = {}
        self._order: List[str] = []

    @property
    def session_id(self) -> str:
        return self._session_id

    def register_request(
        self, clarification_id: str, request_text: str, requested_at: str
    ) -> Clarification:
        """Register a new clarification request.

        Raises ``DuplicateClarificationError`` if ``clarification_id`` is
        already registered.
        """

        if clarification_id in self._log:
            raise DuplicateClarificationError(
                f"Clarification identifier {clarification_id!r} is already registered "
                f"for session {self._session_id!r}."
            )
        clarification = Clarification(
            clarification_id=clarification_id,
            request_text=request_text,
            requested_at=requested_at,
        )
        self._log[clarification_id] = clarification
        self._order.append(clarification_id)
        return clarification

    def register_response(
        self, clarification_id: str, response_text: str, responded_at: str
    ) -> Clarification:
        """Register the response to an already-requested clarification.

        Raises ``InvalidClarificationError`` if ``clarification_id`` is
        unknown, or if it already has a response.
        """

        existing = self._log.get(clarification_id)
        if existing is None:
            raise InvalidClarificationError(
                f"No clarification request registered for identifier "
                f"{clarification_id!r}."
            )
        updated = existing.with_response(response_text, responded_at)
        self._log[clarification_id] = updated
        return updated

    def tag(self, clarification_id: str, label: str) -> Clarification:
        """Attach an informational tag to a clarification.

        Raises ``InvalidClarificationError`` if ``clarification_id`` is
        unknown, or if ``label`` names a forbidden classification
        (recommendation/persuasion/approval/authorization/decision).
        """

        existing = self._log.get(clarification_id)
        if existing is None:
            raise InvalidClarificationError(
                f"No clarification registered for identifier {clarification_id!r}."
            )
        updated = existing.with_tag(label)
        self._log[clarification_id] = updated
        return updated

    def get(self, clarification_id: str) -> Clarification:
        existing = self._log.get(clarification_id)
        if existing is None:
            raise InvalidClarificationError(
                f"No clarification registered for identifier {clarification_id!r}."
            )
        return existing

    def history(self) -> Tuple[Clarification, ...]:
        """Return every registered clarification in request order,
        immutable and preserved verbatim (IWC-REQ-096)."""

        return tuple(self._log[cid] for cid in self._order)


__all__ = ["ClarificationController"]
