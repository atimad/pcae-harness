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
"""

from __future__ import annotations

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
]
