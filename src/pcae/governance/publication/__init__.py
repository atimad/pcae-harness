"""Publication Coordinator (Phase 144C; PEC-001 v1.0).

Implements PEC-001's ``PublicationCoordinator``: the sole production owner
of Publication Execution (PEC-REQ-001, PEC-REQ-021), external to
``pcae.interactive_workflow.**`` (PEC-REQ-018), the PCAE phase/task
lifecycle tree (PEC-REQ-019), and ``pcae.cltr.**`` (PEC-REQ-020), placed as
a sibling package to ``pcae.governance`` per PEC-REQ-027.

This package consumes exactly two inputs -- an immutable
``PublicationReadinessPackage`` (``pcae.interactive_workflow.publication_handoff.models``)
and an explicit ``PublicationAuthorizationEvent`` -- and performs no act
without both (PEC-REQ-009-017, PEC-REQ-028-033). It never infers
authorization from readiness, never publishes automatically, and never
originates its own Authorization Event; that remains a human-operator
responsibility this package's own CLI-facing future phase would supply
(PEC-REQ-034-046) -- no CLI command exists in this phase (144C's explicit
No-Go: "No CLI").

Runtime posture remains Observed/observe/unavailable throughout every
operation this package performs; nothing here is, or is evidence of, a
Publication Authorization Event.
"""
from __future__ import annotations

from pcae.governance.publication.errors import (
    AtomicPublicationFailure,
    AuthorizationReplayError,
    InvalidAuthorizationError,
    InvalidPublicationPackageError,
    MissingAuthorizationError,
    PublicationExecutionError,
    PublicationRollbackError,
    PublicationStorageError,
    StaleAuthorizationError,
)
from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.governance.publication.models import (
    PUBLICATION_EXECUTION_SCHEMA_VERSION,
    PublicationAuthorizationEvent,
    PublicationExecutionContext,
    PublicationExecutionResult,
)
from pcae.governance.publication.storage import PublicationRecordStore

__all__ = [
    "PUBLICATION_EXECUTION_SCHEMA_VERSION",
    "AtomicPublicationFailure",
    "AuthorizationReplayError",
    "InvalidAuthorizationError",
    "InvalidPublicationPackageError",
    "MissingAuthorizationError",
    "PublicationAuthorizationEvent",
    "PublicationCoordinator",
    "PublicationExecutionContext",
    "PublicationExecutionError",
    "PublicationExecutionResult",
    "PublicationRecordStore",
    "PublicationRollbackError",
    "PublicationStorageError",
    "StaleAuthorizationError",
]
