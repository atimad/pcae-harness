"""Filesystem ``SessionRepository`` implementation (Phase 145D; IWPC-001
v1.1 §13, IWPC-REQ-066-077, §19.1, §21, §22, §23).

Concrete storage backend for the ``SessionRepository`` ABC (Phase 143K,
``pcae.interactive_workflow.persistence.repository``). Implements exactly
the ABC's five abstract methods -- ``create``, ``load``, ``persist``,
``exists``, ``list_session_ids`` -- and nothing else: no CLI command, no
transport adapter, no Pending-Readiness Store, no higher-level workflow
behavior (IWPC-REQ-066).

Storage layout (IWPC-REQ-068-071): a single flat directory,
``.pcae/decision-sessions/<session_id>.json``, one file per session,
default umask-governed permissions, no locking primitive (IWPC-REQ-073;
§21 accepts last-write-wins as a disclosed, non-authority-relevant race).

Every write is atomic: ``tempfile.mkstemp`` in the same directory, write,
flush, ``os.fsync``, ``os.replace``, with ``finally``-block temp-file
cleanup (IWPC-REQ-072), mirroring this repository's strongest existing
durable-write precedent (``cltr/persistence.py``'s ``_write_atomic``,
``governance/publication/storage.py``'s ``_write_atomic_json``).

Every persisted file carries its own store-level ``schema_version``
(``STORE_SCHEMA_VERSION``), independent of and in addition to ``Session``'s
own ``schema_version`` nested inside it (IWPC-REQ-074).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from pcae.interactive_workflow.errors import (
    InvalidIdentifierError,
    PersistenceUnavailableError,
    SerializationFailureError,
    SessionAlreadyExistsError,
    SessionNotFoundError,
    SessionStoreCorruptError,
)
from pcae.interactive_workflow.models.session import Session
from pcae.interactive_workflow.persistence.repository import (
    CHGR_STORAGE_PREFIX,
    SessionRepository,
)
from pcae.interactive_workflow.serialization.schema import from_payload, to_payload
from pcae.interactive_workflow.session.identity import is_valid_session_id, validate_session_id

STORE_SCHEMA_VERSION = "decision-session-store/1.0"
"""Store-level schema version (IWPC-REQ-074), independent of ``Session``'s
own ``schema_version`` (``interactive_workflow.models.session.SCHEMA_VERSION``)."""

DEFAULT_STORAGE_ROOT = Path(".pcae") / "decision-sessions"
"""Default storage root (IWPC-REQ-068, IWPC-REQ-070)."""

_TEMP_PREFIX = ".tmp-"


def _paths_overlap(a: Path, b: Path) -> bool:
    """Return whether ``a`` and ``b`` name the same location, or one is an
    ancestor directory of the other, without requiring either to exist."""

    a_parts = Path(os.path.normpath(str(a.absolute())))
    b_parts = Path(os.path.normpath(str(b.absolute())))
    if a_parts == b_parts:
        return True
    return a_parts in b_parts.parents or b_parts in a_parts.parents


class FilesystemSessionRepository(SessionRepository):
    """Concrete filesystem-backed ``SessionRepository`` (IWPC-001 v1.1 §13).

    Owns bytes only; never interprets session semantics (no transition
    legality, no ownership checks), per the ABC's own class-level
    contract. Depends only on serialization
    (``interactive_workflow.serialization.schema``) and stdlib filesystem
    primitives -- never on the CLI, a transport adapter, the Publication
    Coordinator, lifecycle, the Permission Broker, or a governance-record
    implementation.
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        resolved_root = Path(root) if root is not None else DEFAULT_STORAGE_ROOT
        if _paths_overlap(resolved_root, Path(CHGR_STORAGE_PREFIX)):
            raise ValueError(
                "FilesystemSessionRepository root must not overlap "
                f"{CHGR_STORAGE_PREFIX!r} (IWC-001 v1.1 §4.10, IWC-REQ-049)."
            )
        self._root = resolved_root

    @property
    def root(self) -> Path:
        return self._root

    # -- path safety (IWPC-REQ-162, IWPC-REQ-163) ---------------------------

    def _validated_path(self, session_id: str) -> Path:
        try:
            validate_session_id(session_id)
        except InvalidIdentifierError:
            raise
        if "/" in session_id or "\\" in session_id or ".." in session_id:
            # Unreachable given the CDS-<uuid4> regex above, but kept as an
            # explicit, independent guard per IWPC-REQ-162/163's own wording.
            raise InvalidIdentifierError(
                f"Session identifier {session_id!r} is not a safe path component."
            )
        candidate = self._root / f"{session_id}.json"
        if candidate.parent.absolute() != self._root.absolute():
            raise InvalidIdentifierError(
                f"Session identifier {session_id!r} does not resolve within the "
                "repository's storage root."
            )
        return candidate

    def _reject_symlink(self, path: Path) -> None:
        if path.exists() and path.is_symlink():
            raise PersistenceUnavailableError(
                "Refusing to operate on a symlinked session artifact."
            )

    def _ensure_root(self) -> None:
        if self._root.exists() and self._root.is_symlink():
            raise PersistenceUnavailableError(
                "Refusing to operate through a symlinked storage root."
            )
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to prepare the session repository storage root."
            ) from exc

    # -- wire format ----------------------------------------------------

    @staticmethod
    def _wrap(session: Session) -> Dict[str, Any]:
        return {
            "schema_version": STORE_SCHEMA_VERSION,
            "session_id": session.session_id,
            "session": to_payload(session),
        }

    @staticmethod
    def _unwrap(session_id: str, payload: Any) -> Session:
        if not isinstance(payload, dict):
            raise SessionStoreCorruptError(
                f"Session file for {session_id!r} is not a JSON object."
            )
        if payload.get("schema_version") != STORE_SCHEMA_VERSION:
            raise SessionStoreCorruptError(
                f"Session file for {session_id!r} carries an unsupported store "
                "schema_version."
            )
        if payload.get("session_id") != session_id:
            raise SessionStoreCorruptError(
                f"Session file for {session_id!r} does not carry the expected "
                "session identifier."
            )
        session_payload = payload.get("session")
        if not isinstance(session_payload, dict):
            raise SessionStoreCorruptError(
                f"Session file for {session_id!r} is missing its nested session "
                "payload."
            )
        try:
            session = from_payload(session_payload)
        except SerializationFailureError as exc:
            raise SessionStoreCorruptError(
                f"Session file for {session_id!r} is malformed."
            ) from exc
        if session.session_id != session_id:
            raise SessionStoreCorruptError(
                f"Session file for {session_id!r} carries a mismatched nested "
                "session identifier."
            )
        return session

    # -- atomic write (IWPC-REQ-072, IWPC-REQ-155, IWPC-REQ-161) ---------

    def _write_atomic(self, path: Path, payload: Dict[str, Any]) -> None:
        self._ensure_root()
        self._reject_symlink(path)
        data = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        fd, tmp_name = tempfile.mkstemp(prefix=_TEMP_PREFIX, dir=str(self._root))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, str(path))
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to persist the session record."
            ) from exc
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    # -- SessionRepository interface -------------------------------------

    def create(self, session: Session) -> None:
        path = self._validated_path(session.session_id)
        self._ensure_root()
        self._reject_symlink(path)
        if path.exists():
            raise SessionAlreadyExistsError(
                f"A session record already exists for {session.session_id!r}."
            )
        self._write_atomic(path, self._wrap(session))

    def load(self, session_id: str) -> Session:
        path = self._validated_path(session_id)
        self._reject_symlink(path)
        if not path.exists():
            raise SessionNotFoundError(
                f"No session record exists for {session_id!r}."
            )
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to read the session record."
            ) from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SessionStoreCorruptError(
                f"Session file for {session_id!r} is not valid JSON."
            ) from exc
        return self._unwrap(session_id, payload)

    def persist(self, session: Session) -> None:
        path = self._validated_path(session.session_id)
        self._reject_symlink(path)
        if not path.exists():
            raise SessionNotFoundError(
                f"No session record exists for {session.session_id!r}."
            )
        self._write_atomic(path, self._wrap(session))

    def exists(self, session_id: str) -> bool:
        path = self._validated_path(session_id)
        return path.exists() and not path.is_symlink()

    def list_session_ids(self) -> List[str]:
        if not self._root.exists():
            return []
        if self._root.is_symlink():
            raise PersistenceUnavailableError(
                "Refusing to operate through a symlinked storage root."
            )
        ids: List[str] = []
        try:
            entries = list(self._root.iterdir())
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to enumerate the session repository storage root."
            ) from exc
        for entry in entries:
            name = entry.name
            if not name.endswith(".json") or name.startswith("."):
                continue
            if entry.is_dir() or entry.is_symlink():
                continue
            candidate_id = name[: -len(".json")]
            if not is_valid_session_id(candidate_id):
                continue
            ids.append(candidate_id)
        return sorted(ids)


__all__ = [
    "STORE_SCHEMA_VERSION",
    "DEFAULT_STORAGE_ROOT",
    "FilesystemSessionRepository",
]
