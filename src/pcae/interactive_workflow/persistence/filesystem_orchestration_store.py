"""Filesystem Orchestration Record store (Phase 145G.1).

Phase 145G disclosed a Blocking finding (F-145G-1): ``WorkflowOrchestrator``
and its six collaborators (Evidence Coordinator, Clarification Controller,
Audit Recorder, Preview Builder, Confirmation Controller, Transition
Engine) are in-memory-only; ``SessionRepository`` (IWPC-001 v1.1 §13)
persists only the ``Session`` record itself, never orchestration-stage
progress, registered evidence, clarification exchanges, or confirmation
artifacts. Because every ``pcae`` invocation is a separate OS process,
``evidence``/``clarify``/``preview``/``confirm``/``readiness`` construction
could not resume across invocations.

This module closes that gap with the narrowest persistence design that
satisfies IWPC-001 v1.1 §13's own precedent (``FilesystemSessionRepository``,
Phase 145D) without modifying ``SessionRepository`` itself: IWPC-REQ-066
freezes that ABC's surface to exactly ``create``/``load``/``persist``/
``exists``/``list_session_ids``, so orchestration bookkeeping is not
smuggled in as a sixth method there. Instead, following IWPC-REQ-067's own
precedent ("the Session Repository implementation is owned by the
CLI/transport layer, not by SessionCoordinator"), this store is a second,
narrowly-scoped, CLI/transport-layer-owned artifact -- exactly the kind of
"dedicated persisted orchestration record" Phase 145G's own report
recommended a future phase design.

Storage layout mirrors ``FilesystemSessionRepository`` exactly: a single
flat directory (``.pcae/decision-sessions/orchestration/``), one file per
session (``<session_id>.json``), atomic ``tempfile.mkstemp`` -> write ->
flush -> ``fsync`` -> ``os.replace`` writes, a dedicated store-level
``schema_version``, and the same path-safety/symlink-refusal discipline
(IWPC-REQ-072, IWPC-REQ-155, IWPC-REQ-161, IWPC-REQ-162, IWPC-REQ-163).

What is persisted, and why (see this phase's canonical report for the
full requirement matrix): completed orchestration stages (so
``WorkflowOrchestrator`` can resume via its new ``initial_state``
constructor parameter, Phase 145G.1); a running transition-sequence
counter (so ``TransitionEngine.apply``'s monotonicity policy and
``Preview``'s staleness check have a durable value to compare against);
every registered evidence item, clarification exchange, confirmation
request, and confirmation response (so each collaborator's own dedup/
replay/duplicate checks still see the full history on a fresh process);
one cached, fully-rendered ``Preview`` (so ``confirm`` and readiness
construction can bind to the *exact* Preview a caller last saw, without
this store ever becoming a second Preview-content authority -- Preview
Builder's own determinism, IWPC-REQ-019, is what makes re-deriving that
exact content safe to cache); and, where applicable, cancellation
metadata (``Session`` itself carries no cancellation-reason field).

Nothing here evaluates workflow semantics, evaluates transition
legality, or constructs a ``PublicationReadinessPackage`` -- this module
owns bytes only, exactly like its ``FilesystemSessionRepository`` sibling.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pcae.interactive_workflow.errors import (
    InvalidIdentifierError,
    OrchestrationStoreCorruptError,
    PersistenceUnavailableError,
)
from pcae.interactive_workflow.session.identity import validate_session_id

ORCHESTRATION_STORE_SCHEMA_VERSION = "decision-session-orchestration/1.0"

DEFAULT_STORAGE_ROOT = Path(".pcae") / "decision-sessions" / "orchestration"

_TEMP_PREFIX = ".tmp-"


@dataclass(frozen=True)
class OrchestrationRecord:
    """Persisted orchestration bookkeeping for exactly one Decision
    Session. Every field is plain JSON-serializable data (dict/list/str/
    int) -- never a live domain object -- so this dataclass has no
    dependency on ``interactive_workflow.orchestration``,
    ``.evidence``, ``.clarification``, ``.confirmation``, or
    ``.preview``; the application layer (Phase 145G.1's
    ``session_service`` extensions) is solely responsible for
    translating between this record and those live domain objects.
    """

    session_id: str
    completed_stages: Tuple[str, ...] = field(default_factory=tuple)
    transition_sequence_number: int = 0
    evidence: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    clarifications: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    confirmation_requests: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    confirmation_responses: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    last_preview: Optional[Dict[str, Any]] = None
    cancellation: Optional[Dict[str, Any]] = None
    schema_version: str = ORCHESTRATION_STORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_session_id(self.session_id)
        object.__setattr__(self, "completed_stages", tuple(self.completed_stages))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "clarifications", tuple(self.clarifications))
        object.__setattr__(self, "confirmation_requests", tuple(self.confirmation_requests))
        object.__setattr__(self, "confirmation_responses", tuple(self.confirmation_responses))


class FilesystemOrchestrationStore:
    """Concrete filesystem-backed store for ``OrchestrationRecord``.

    Owns bytes only. Depends only on stdlib filesystem primitives and
    ``session.identity.validate_session_id`` -- never on the CLI, a
    transport adapter, ``WorkflowOrchestrator``, or any of the six
    orchestration collaborators.
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self._root = Path(root) if root is not None else DEFAULT_STORAGE_ROOT

    @property
    def root(self) -> Path:
        return self._root

    def _validated_path(self, session_id: str) -> Path:
        validate_session_id(session_id)
        if "/" in session_id or "\\" in session_id or ".." in session_id:
            raise InvalidIdentifierError(
                f"Session identifier {session_id!r} is not a safe path component."
            )
        candidate = self._root / f"{session_id}.json"
        if candidate.parent.absolute() != self._root.absolute():
            raise InvalidIdentifierError(
                f"Session identifier {session_id!r} does not resolve within the "
                "orchestration store's storage root."
            )
        return candidate

    def _reject_symlink(self, path: Path) -> None:
        if path.exists() and path.is_symlink():
            raise PersistenceUnavailableError(
                "Refusing to operate on a symlinked orchestration record."
            )

    def _ensure_root(self) -> None:
        if self._root.exists() and self._root.is_symlink():
            raise PersistenceUnavailableError(
                "Refusing to operate through a symlinked orchestration storage root."
            )
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to prepare the orchestration store storage root."
            ) from exc

    @staticmethod
    def _wrap(record: OrchestrationRecord) -> Dict[str, Any]:
        return {
            "schema_version": ORCHESTRATION_STORE_SCHEMA_VERSION,
            "session_id": record.session_id,
            "completed_stages": list(record.completed_stages),
            "transition_sequence_number": record.transition_sequence_number,
            "evidence": list(record.evidence),
            "clarifications": list(record.clarifications),
            "confirmation_requests": list(record.confirmation_requests),
            "confirmation_responses": list(record.confirmation_responses),
            "last_preview": record.last_preview,
            "cancellation": record.cancellation,
        }

    @staticmethod
    def _unwrap(session_id: str, payload: Any) -> OrchestrationRecord:
        if not isinstance(payload, dict):
            raise OrchestrationStoreCorruptError(
                f"Orchestration record for {session_id!r} is not a JSON object."
            )
        if payload.get("schema_version") != ORCHESTRATION_STORE_SCHEMA_VERSION:
            raise OrchestrationStoreCorruptError(
                f"Orchestration record for {session_id!r} carries an unsupported "
                "store schema_version."
            )
        if payload.get("session_id") != session_id:
            raise OrchestrationStoreCorruptError(
                f"Orchestration record for {session_id!r} does not carry the "
                "expected session identifier."
            )
        try:
            return OrchestrationRecord(
                session_id=session_id,
                completed_stages=tuple(payload.get("completed_stages") or ()),
                transition_sequence_number=int(payload.get("transition_sequence_number") or 0),
                evidence=tuple(payload.get("evidence") or ()),
                clarifications=tuple(payload.get("clarifications") or ()),
                confirmation_requests=tuple(payload.get("confirmation_requests") or ()),
                confirmation_responses=tuple(payload.get("confirmation_responses") or ()),
                last_preview=payload.get("last_preview"),
                cancellation=payload.get("cancellation"),
            )
        except (TypeError, ValueError) as exc:
            raise OrchestrationStoreCorruptError(
                f"Orchestration record for {session_id!r} is malformed."
            ) from exc

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
                "Failed to persist the orchestration record."
            ) from exc
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def exists(self, session_id: str) -> bool:
        path = self._validated_path(session_id)
        return path.exists() and not path.is_symlink()

    def load(self, session_id: str) -> OrchestrationRecord:
        path = self._validated_path(session_id)
        self._reject_symlink(path)
        if not path.exists():
            raise OrchestrationStoreCorruptError(
                f"No orchestration record exists for {session_id!r}."
            )
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to read the orchestration record."
            ) from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OrchestrationStoreCorruptError(
                f"Orchestration record for {session_id!r} is not valid JSON."
            ) from exc
        return self._unwrap(session_id, payload)

    def load_or_create(self, session_id: str) -> OrchestrationRecord:
        """Return the persisted record for ``session_id``, or a fresh,
        empty, unpersisted ``OrchestrationRecord`` if none exists yet.
        Creating a fresh record here does not itself write anything --
        the caller must still call ``persist`` to durably record it."""

        if self.exists(session_id):
            return self.load(session_id)
        return OrchestrationRecord(session_id=session_id)

    def persist(self, record: OrchestrationRecord) -> None:
        path = self._validated_path(record.session_id)
        self._write_atomic(path, self._wrap(record))


__all__ = [
    "ORCHESTRATION_STORE_SCHEMA_VERSION",
    "DEFAULT_STORAGE_ROOT",
    "OrchestrationRecord",
    "FilesystemOrchestrationStore",
]
