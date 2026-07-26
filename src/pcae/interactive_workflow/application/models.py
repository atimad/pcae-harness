"""Transport-neutral application-layer value objects (Phase 145F).

``PreparedPublicationRequest`` is this boundary's own internal handoff
shape -- distinct from IWPC-001 v1.1's ``PublicationRequest`` transport
object (§10, IWPC-REQ-053), which does not exist yet (no CLI/transport
layer has been implemented). It carries exactly the fields
``PublicationApplicationService.prepare_publication_request`` has already
verified, so ``hand_off`` never has to re-derive them from a raw
``package_id`` string.
"""
from __future__ import annotations

from dataclasses import dataclass

from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage


@dataclass(frozen=True)
class PreparedPublicationRequest:
    """A validated, ready-to-hand-off publication request.

    Construction (``PublicationApplicationService.prepare_publication_request``)
    already verified: the package exists in the Pending-Readiness Store
    with a matching digest (store-layer, IWPC-REQ-165), its disposition is
    still ``pending`` (not already consumed), and its bound session has
    not since reached ``Expired`` (IWPC-REQ-085/114). This object itself
    grants no authority and does not publish (IWPC-REQ-012's
    Confirmation/Publication-readiness/Authorization/Publication
    separation).
    """

    package: PublicationReadinessPackage
    package_id: str
    session_id: str
    package_digest: str
    confirmation_request_id: str
    confirmation_response_id: str


__all__ = ["PreparedPublicationRequest"]
