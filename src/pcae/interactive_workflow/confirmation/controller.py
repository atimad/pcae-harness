"""Confirmation Controller (IWC-001 v1.1 §10, Phase 143J §16, Phase 143N).

The sole production owner of confirmation-request lifecycle,
confirmation-response lifecycle, replay detection, and stale-preview
rejection for a single Decision Session (this phase's governing prompt,
"Architectural Ownership"). No other production component may register a
confirmation request or response.

Integration with the Session Infrastructure (143K) and Transition Engine
(143L) is structural and passive only, identical in discipline to
``pcae.interactive_workflow.evidence.coordinator.EvidenceCoordinator``: a
controller is scoped to one session identifier, validated with the same
``CDS-<uuid4>`` syntax check the Session Coordinator uses, but this
module never calls ``SessionCoordinator`` or ``TransitionEngine`` -- it
cannot drive a transition, and it does not try to. It depends on
``pcae.interactive_workflow.preview.builder.PreviewBuilder`` only for
digest recomputation and stale-preview detection -- composition with the
component IWC-001 v1.1 §10.2 requires those checks be delegated to
("Preview Builder shall become the sole owner of ... preview integrity
verification"), never a reimplementation of that logic here.

This controller does not, and per its governing phase prompt never will,
perform publication, transition a session, create a CHGR, or invoke
Session Coordinator. Those methods do not exist on this class.
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from pcae.interactive_workflow.confirmation.models import ConfirmationRequest, ConfirmationResponse
from pcae.interactive_workflow.errors import (
    DuplicateConfirmationError,
    InvalidConfirmationError,
    PreviewDigestMismatchError,
    ReplayDetectedError,
)
from pcae.interactive_workflow.preview.builder import PreviewBuilder
from pcae.interactive_workflow.preview.models import Preview
from pcae.interactive_workflow.session.identity import validate_session_id


class ConfirmationController:
    """Registers requests/responses and enforces digest, replay, and
    staleness discipline for exactly one Decision Session's confirmation
    lifecycle."""

    def __init__(self, session_id: str) -> None:
        self._session_id = validate_session_id(session_id)
        self._preview_builder = PreviewBuilder()
        self._requests: Dict[str, ConfirmationRequest] = {}
        self._request_order: List[str] = []
        self._responses: Dict[str, ConfirmationResponse] = {}
        self._response_order: List[str] = []
        self._responded_request_ids: Set[str] = set()
        self._confirmed_digests: Set[str] = set()

    @property
    def session_id(self) -> str:
        return self._session_id

    def register_request(self, request: ConfirmationRequest) -> ConfirmationRequest:
        """Register a new confirmation request.

        Raises ``DuplicateConfirmationError`` if ``request.request_id``
        is already registered (duplicate request identifiers, rejected
        rather than silently accepted). Raises
        ``InvalidConfirmationError`` if ``request.session_id`` does not
        match this controller's own scope.
        """

        if request.session_id != self._session_id:
            raise InvalidConfirmationError(
                f"ConfirmationRequest {request.request_id!r} is scoped to session "
                f"{request.session_id!r}, not this controller's session "
                f"{self._session_id!r}."
            )
        if request.request_id in self._requests:
            raise DuplicateConfirmationError(
                f"Confirmation request identifier {request.request_id!r} is already "
                f"registered for session {self._session_id!r}."
            )
        self._requests[request.request_id] = request
        self._request_order.append(request.request_id)
        return request

    def register_response(
        self,
        request_id: str,
        response: ConfirmationResponse,
        preview: Preview,
        current_transition_sequence_number: int,
    ) -> ConfirmationResponse:
        """Accept a confirming act against the request identified by
        ``request_id``, recomputing and verifying the Preview Digest and
        the underlying Preview's freshness immediately before acceptance
        (IWC-001 v1.1 §10.2), exactly mirroring the moment "Confirmation
        SHALL recompute the Preview Digest against current session
        content immediately before accepting a confirming action."

        Raises, in order of check:

        - ``InvalidConfirmationError`` -- unknown ``request_id``, a
          response whose own ``request_id`` does not match, or a
          ``preview.preview_id`` that does not match the request's own
          bound ``preview_id``.
        - ``DuplicateConfirmationError`` -- the request already has a
          response, or ``response.response_id`` is already registered.
        - ``StalePreviewError`` / ``PreviewDigestMismatchError`` --
          delegated to ``PreviewBuilder.detect_staleness``.
        - ``PreviewDigestMismatchError`` -- ``response.preview_digest``
          does not match the request's own bound digest (IWC-REQ-102/103
          exact-content binding).
        - ``ReplayDetectedError`` -- the request's Preview Digest has
          already been successfully bound to a completed confirmation
          elsewhere in this controller's scope.
        """

        request = self._requests.get(request_id)
        if request is None:
            raise InvalidConfirmationError(
                f"No confirmation request registered for identifier {request_id!r}."
            )
        if response.request_id != request_id:
            raise InvalidConfirmationError(
                f"ConfirmationResponse {response.response_id!r} names request_id "
                f"{response.request_id!r}, which does not match the targeted request "
                f"{request_id!r}."
            )
        if preview.preview_id != request.preview_id:
            raise InvalidConfirmationError(
                f"Preview {preview.preview_id!r} does not match confirmation request "
                f"{request_id!r}'s bound preview {request.preview_id!r}."
            )
        if request_id in self._responded_request_ids:
            raise DuplicateConfirmationError(
                f"Confirmation request {request_id!r} already has a response; a "
                "response is never overwritten or re-accepted."
            )
        if response.response_id in self._responses:
            raise DuplicateConfirmationError(
                f"Confirmation response identifier {response.response_id!r} is already "
                f"registered for session {self._session_id!r}."
            )

        # IWC-001 v1.1 §10.2: recompute the Preview Digest against current
        # content, and detect staleness, immediately before acceptance.
        self._preview_builder.detect_staleness(
            preview=preview,
            preview_digest=request.preview_digest,
            current_session_id=self._session_id,
            current_transition_sequence_number=current_transition_sequence_number,
        )

        if response.preview_digest != request.preview_digest:
            raise PreviewDigestMismatchError(
                f"ConfirmationResponse {response.response_id!r} carries digest "
                f"{response.preview_digest!r}, which does not match confirmation "
                f"request {request_id!r}'s bound digest {request.preview_digest!r}."
            )

        if request.preview_digest in self._confirmed_digests:
            raise ReplayDetectedError(
                f"Preview Digest {request.preview_digest!r} has already been bound to "
                f"a completed confirmation in session {self._session_id!r}; it cannot "
                "be reused for a new confirming act."
            )

        self._responses[response.response_id] = response
        self._response_order.append(response.response_id)
        self._responded_request_ids.add(request_id)
        self._confirmed_digests.add(request.preview_digest)
        return response

    def get_request(self, request_id: str) -> ConfirmationRequest:
        try:
            return self._requests[request_id]
        except KeyError as exc:
            raise InvalidConfirmationError(
                f"No confirmation request registered for identifier {request_id!r}."
            ) from exc

    def get_response(self, response_id: str) -> ConfirmationResponse:
        try:
            return self._responses[response_id]
        except KeyError as exc:
            raise InvalidConfirmationError(
                f"No confirmation response registered for identifier {response_id!r}."
            ) from exc

    def request_history(self) -> Tuple[ConfirmationRequest, ...]:
        """Return every registered request, in registration order."""

        return tuple(self._requests[request_id] for request_id in self._request_order)

    def response_history(self) -> Tuple[ConfirmationResponse, ...]:
        """Return every accepted response, in acceptance order."""

        return tuple(self._responses[response_id] for response_id in self._response_order)


__all__ = ["ConfirmationController"]
