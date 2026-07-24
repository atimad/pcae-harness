"""``SessionRepository`` -- the persistence contract (Phase 143K).

Persistence contract (Phase 143J §5.2/§6.8, IWC-001 v1.1 §4.10):

- Read/write failures propagate to the caller as
  ``PersistenceUnavailableError`` without partial state mutation; no
  silent retry, no best-effort continuation.
- A repository implementation owns bytes; it never interprets session
  semantics (no transition legality, no ownership checks -- those are the
  State Machine's and Session Coordinator's responsibilities).
- A repository implementation must never write under
  ``.pcae/governance-records/`` (``CHGR_STORAGE_PREFIX`` below) or any
  path a manifest-driven CHGR consumer might mistake for a frozen CHGR
  schema instance (IWC-001 v1.1 §4.10, IWC-REQ-049).
- Every persisted record carries its own ``schema_version``
  (``pcae.interactive_workflow.serialization``), independent of template
  version and IWC-001 contract version. A repository never reinterprets
  an already-terminal session's persisted record on a later contract
  revision.

This module defines the interface only. No concrete storage backend
(filesystem, SQLite, PostgreSQL, cloud) is implemented or selected here --
that choice is deliberately deferred past Phase 143K.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from pcae.interactive_workflow.models.session import Session

CHGR_STORAGE_PREFIX = ".pcae/governance-records/"
"""Canonical CHGR storage path prefix. No ``SessionRepository``
implementation may write under this prefix (IWC-001 v1.1 §4.10)."""


class SessionRepository(ABC):
    """Abstract persistence boundary for ``Session`` records.

    Concrete implementations are out of scope for Phase 143K. Every
    method below must be implemented by a concrete subclass before it can
    be constructed; there is no default, storage-backed behavior here.
    """

    @abstractmethod
    def create(self, session: Session) -> None:
        """Persist a brand-new session record.

        Must raise if a record already exists for ``session.session_id``
        -- ``create`` never silently overwrites (that is ``persist``'s
        role for an already-existing record, and only via an explicit
        caller decision).
        """

        raise NotImplementedError

    @abstractmethod
    def load(self, session_id: str) -> Session:
        """Return the persisted ``Session`` for ``session_id``.

        Must raise ``SessionNotFoundError`` (see
        ``pcae.interactive_workflow.errors``) if no record exists.
        """

        raise NotImplementedError

    @abstractmethod
    def persist(self, session: Session) -> None:
        """Overwrite the persisted record for an existing session.

        Must raise ``SessionNotFoundError`` if no prior record exists for
        ``session.session_id`` -- ``persist`` never creates.
        """

        raise NotImplementedError

    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """Return whether a persisted record exists for ``session_id``."""

        raise NotImplementedError

    @abstractmethod
    def list_session_ids(self) -> Iterable[str]:
        """Return every persisted session identifier known to this
        repository. No ordering guarantee is made at this interface
        level."""

        raise NotImplementedError


__all__ = [
    "CHGR_STORAGE_PREFIX",
    "SessionRepository",
]
