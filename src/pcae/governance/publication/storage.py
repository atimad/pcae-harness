"""Publication Coordinator storage (Phase 144C; PEC-001 §7, §11, §15).

Owns exactly three durable artifact classes, each atomically written
(temp file + ``fsync`` + ``os.replace``, mirroring
``src/pcae/cltr/persistence.py``'s ``_write_atomic``, the codebase's
strongest existing precedent for a durable, irrevocable write):

- ``records/<record_id>.json`` -- the immutable CHGR record itself,
  written exactly once per ``record_id``.
- ``published/<package_id>.json`` -- the idempotency marker, created via
  an exclusive (``O_CREAT | O_EXCL``) filesystem create so a genuine
  concurrent race is detected deterministically rather than silently
  overwritten (PEC-REQ-080).
- ``attempts/<attempt_id>.json`` -- one audit record per Publication
  Execution attempt, accepted or refused, independently retrievable
  (PEC-REQ-043, PEC-REQ-106) and structurally separate from Session
  Audit Evidence and CHGR provenance (PEC-REQ-107).

No component in this module infers, checks, or evaluates authorization or
readiness; it persists exactly what the Coordinator hands it.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict

from pcae.governance.publication.errors import PublicationStorageError

_DEFAULT_ROOT = Path(".pcae") / "publication-execution"
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def _safe_name(value: str) -> str:
    return _UNSAFE_CHARS.sub("_", value)


def _write_atomic_json(path: Path, payload: Dict[str, Any]) -> None:
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, str(path))
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


class PublicationRecordStore:
    """Filesystem-backed durable store for Publication Coordinator
    artifacts. All public methods are safe for concurrent invocation
    across processes: the idempotency commit uses an exclusive create,
    never a read-then-write race."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root) if root is not None else _DEFAULT_ROOT
        self._records_dir = self._root / "records"
        self._published_dir = self._root / "published"
        self._attempts_dir = self._root / "attempts"

    @property
    def root(self) -> Path:
        return self._root

    def _record_path(self, record_id: str) -> Path:
        return self._records_dir / f"{_safe_name(record_id)}.json"

    def _marker_path(self, package_id: str) -> Path:
        return self._published_dir / f"{_safe_name(package_id)}.json"

    def _attempt_path(self, attempt_id: str) -> Path:
        return self._attempts_dir / f"{_safe_name(attempt_id)}.json"

    def is_published(self, package_id: str) -> bool:
        """Idempotency check (PEC-REQ-008): has ``package_id`` already
        been consumed by a completed Publication Execution."""

        return self._marker_path(package_id).exists()

    def write_record(self, record_id: str, payload: Dict[str, Any]) -> Path:
        """Atomically write the immutable CHGR record. Refuses to
        overwrite an existing record (a published record's substantive
        fields are never edited in place, CHGR-001 §13.3)."""

        path = self._record_path(record_id)
        if path.exists():
            raise PublicationStorageError(
                f"CHGR record {record_id!r} already exists at {path}; refusing to "
                "overwrite an immutable record."
            )
        try:
            _write_atomic_json(path, payload)
        except OSError as exc:
            raise PublicationStorageError(
                f"Failed to durably persist CHGR record {record_id!r}: {exc}"
            ) from exc
        return path

    def remove_record(self, record_id: str) -> None:
        """Rollback helper: remove a just-written record whose
        publication could not be durably committed. No-op if the record
        does not exist."""

        with contextlib.suppress(FileNotFoundError):
            self._record_path(record_id).unlink()

    def commit_publication(self, package_id: str, record_id: str, marker_payload: Dict[str, Any]) -> None:
        """Durably and exclusively commit ``package_id`` as published.

        Raises ``FileExistsError`` if a marker already exists (a
        concurrent attempt won the race) -- the caller is responsible for
        rolling back the just-written record and reporting Replay.
        """

        path = self._marker_path(package_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            with os.fdopen(fd, "wb") as fh:
                data = (json.dumps(marker_payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
        except OSError:
            with contextlib.suppress(OSError):
                os.unlink(str(path))
            raise

    def record_attempt(self, attempt_id: str, payload: Dict[str, Any]) -> Path:
        """Persist one attempt's audit evidence, accepted or refused
        (PEC-REQ-043, PEC-REQ-106)."""

        path = self._attempt_path(attempt_id)
        try:
            _write_atomic_json(path, payload)
        except OSError as exc:
            raise PublicationStorageError(
                f"Failed to durably persist attempt record {attempt_id!r}: {exc}"
            ) from exc
        return path


__all__ = ["PublicationRecordStore"]
