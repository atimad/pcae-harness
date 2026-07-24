"""Session persistence abstraction (Phase 143K).

Interfaces only. Storage technology (SQLite, JSON files, PostgreSQL,
filesystem, cloud storage) is deliberately not selected here -- Phase 143J
§6.8 explicitly defers that choice past 143K, and the governing 143K
prompt forbids selecting one. Session storage is operational, ephemeral,
and structurally distinct from CHGR's canonical storage under
``.pcae/governance-records/records/`` (IWC-001 v1.1 §4.10, IWC-REQ-049):
no implementation of ``SessionRepository`` may write there.
"""

from __future__ import annotations

from pcae.interactive_workflow.persistence.repository import (
    CHGR_STORAGE_PREFIX,
    SessionRepository,
)

__all__ = [
    "CHGR_STORAGE_PREFIX",
    "SessionRepository",
]
