"""Interactive Workflow + Publication application-service boundary
(Phase 145F).

Introduces the internal, non-transport application-service layer Phase
145A's Architecture named "Model D" and IWPC-001 v1.1 rejected as
*required* for v1.0 (IWPC-REQ-006: "No transport-neutral
application-service class SHALL be required by v1.0... a future,
separately governed contract revision MAY introduce Model D... without
this contract needing retraction"). This package does not implement a
CLI command, a transport adapter, or any second, competing invocation
surface -- no CLI/transport package exists in this repository yet
(``decision-session``/``governance-record publish`` remain unimplemented,
145G+ territory), so nothing here becomes "a second, informal,
unauthorized boundary" athwart an existing transport (145A §4's stated
risk for introducing Model D prematurely does not apply: there is, as yet,
no competing transport for this to duplicate or diverge from). It exists
solely so a future CLI/transport phase has a single, already-tested
coordination point to call into rather than wiring
``SessionCoordinator``/``PublicationCoordinator`` directly from CLI
command bodies.

``session_service.SessionApplicationService`` coordinates
``SessionCoordinator``/``SessionRepository`` (session lifecycle: create,
load, persist, update, completion). ``publication_service.
PublicationApplicationService`` coordinates the Pending-Readiness Store,
the Session Repository (via ``SessionApplicationService``), and
``PublicationCoordinator`` (readiness-package persistence, publication
request preparation, the publication boundary hand-off, and recovery).
Neither class establishes governance authority, evaluates authorization,
creates a CHGR, or invokes transport (IWPC-REQ-002/003/009/010/013);
every authority-bearing decision remains delegated, verbatim, to the
existing Interactive Workflow and Publication subsystem classes this
package coordinates but does not replace.
"""
from __future__ import annotations

from pcae.interactive_workflow.application.errors import ApplicationServiceError
from pcae.interactive_workflow.application.models import PreparedPublicationRequest
from pcae.interactive_workflow.application.publication_service import PublicationApplicationService
from pcae.interactive_workflow.application.session_service import SessionApplicationService

__all__ = [
    "ApplicationServiceError",
    "PreparedPublicationRequest",
    "SessionApplicationService",
    "PublicationApplicationService",
]
