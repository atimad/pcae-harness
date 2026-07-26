"""Session persistence abstraction (Phase 143K) and its first concrete
filesystem implementation (Phase 145D; IWPC-001 v1.1 §13).

``SessionRepository`` (Phase 143K) is the storage-agnostic interface.
Session storage is operational, ephemeral, and structurally distinct from
CHGR's canonical storage under ``.pcae/governance-records/records/``
(IWC-001 v1.1 §4.10, IWC-REQ-049): no implementation of
``SessionRepository`` may write there.

``FilesystemSessionRepository`` (Phase 145D) is the first concrete
storage backend, frozen by IWPC-001 v1.1 §13 (IWPC-REQ-066-077). Other
storage technologies remain unselected/deferred.

``FilesystemPendingReadinessStore`` (Phase 145E) is the second concrete
persistence component, frozen by IWPC-001 v1.1 §14 (IWPC-REQ-078-092):
durable, repository-local persistence of a constructed
``PublicationReadinessPackage`` between construction and a later
publication invocation. No abstract base class governs it (§14 defines
no separate interface, unlike §13's ``SessionRepository`` ABC).
"""

from __future__ import annotations

from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    CONSUMED_SUBDIRECTORY,
    DEFAULT_SESSIONS_ROOT,
    DISPOSITION_CONSUMED,
    DISPOSITION_PENDING,
    OUTCOME_FAILED,
    OUTCOME_SUCCEEDED,
    FilesystemPendingReadinessStore,
    PendingReadinessRecord,
    PublicationAttemptRecord,
)
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    DEFAULT_STORAGE_ROOT as PENDING_READINESS_DEFAULT_STORAGE_ROOT,
)
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    STORE_SCHEMA_VERSION as PENDING_READINESS_STORE_SCHEMA_VERSION,
)
from pcae.interactive_workflow.persistence.filesystem_repository import (
    DEFAULT_STORAGE_ROOT,
    STORE_SCHEMA_VERSION,
    FilesystemSessionRepository,
)
from pcae.interactive_workflow.persistence.repository import (
    CHGR_STORAGE_PREFIX,
    SessionRepository,
)

__all__ = [
    "CHGR_STORAGE_PREFIX",
    "SessionRepository",
    "DEFAULT_STORAGE_ROOT",
    "STORE_SCHEMA_VERSION",
    "FilesystemSessionRepository",
    "DEFAULT_SESSIONS_ROOT",
    "PENDING_READINESS_DEFAULT_STORAGE_ROOT",
    "PENDING_READINESS_STORE_SCHEMA_VERSION",
    "CONSUMED_SUBDIRECTORY",
    "DISPOSITION_PENDING",
    "DISPOSITION_CONSUMED",
    "OUTCOME_SUCCEEDED",
    "OUTCOME_FAILED",
    "PublicationAttemptRecord",
    "PendingReadinessRecord",
    "FilesystemPendingReadinessStore",
]
