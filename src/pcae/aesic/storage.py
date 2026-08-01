"""Two-tier Authority Evaluation Record (AER) storage (AESIC-001 v1.3
§12.1, AESIC-REQ-119): an immutable, compound-keyed primary store plus a
mutable, ``package_id``-keyed canonical pointer index.

Atomic write mechanics mirror ``src/pcae/cltr/persistence.py``'s
``_write_atomic`` / ``src/pcae/governance/publication/storage.py``'s
``_write_atomic_json`` and ``O_CREAT | O_EXCL`` idempotency-marker
discipline (AESIC-REQ-086, AESIC-REQ-019), applied here to the AER's own
compound storage key ``(package_id, evaluation_id)``.

Layout under ``root`` (default ``.pcae/authority-evaluation/records``)::

    records/<package_id>/<evaluation_id>.json   # primary, immutable, exclusive-create
    pointers/<package_id>.json                  # canonical pointer, atomic replace
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from pcae.aesic.errors import (
    AuthorityEvaluationRecordConflictError,
    AuthorityEvaluationRecordCorruptError,
    AuthorityEvaluationStorageIdentifierError,
    CanonicalPointerCorruptError,
)
from pcae.aesic.records import (
    AuthorityEvaluationRecord,
    CanonicalPointer,
    aer_from_payload,
    aer_to_payload,
    pointer_from_payload,
    pointer_to_payload,
    verify_aer_digest,
    verify_pointer_digest,
)

DEFAULT_STORAGE_ROOT = Path(".pcae/authority-evaluation/records")
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")
_PATH_SEPARATORS = {"/", os.sep}
if os.altsep:
    _PATH_SEPARATORS.add(os.altsep)


def _safe_name(value: str) -> str:
    return _UNSAFE_CHARS.sub("_", value)


def _validate_identifier_component(value: str, field_name: str) -> str:
    """Reject ``value`` unless it is safe to use, verbatim, as exactly one
    filesystem path component (147O.2-F-1 persistence-boundary hardening).
    Checked against the *raw* value, before ``_safe_name``'s character
    substitution -- an invalid identifier is rejected, never silently
    rewritten into a safe-looking one."""

    if not isinstance(value, str) or value == "":
        raise AuthorityEvaluationStorageIdentifierError(
            f"{field_name} must be a non-empty str, got {value!r}."
        )
    if value in (".", ".."):
        raise AuthorityEvaluationStorageIdentifierError(
            f"{field_name} must not be {value!r} -- not a valid single storage path component."
        )
    if any(sep in value for sep in _PATH_SEPARATORS):
        raise AuthorityEvaluationStorageIdentifierError(
            f"{field_name} must not contain a path separator, got {value!r}."
        )
    if "\x00" in value:
        raise AuthorityEvaluationStorageIdentifierError(
            f"{field_name} must not contain a NUL byte."
        )
    if os.path.isabs(value):
        raise AuthorityEvaluationStorageIdentifierError(
            f"{field_name} must not be an absolute path, got {value!r}."
        )
    return value


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


def _write_exclusive_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
    except OSError:
        with _suppress_missing(path):
            os.unlink(str(path))
        raise


class _suppress_missing:
    def __init__(self, path: Path) -> None:
        self._path = path

    def __enter__(self) -> "_suppress_missing":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return exc_type is FileNotFoundError


class AuthorityEvaluationRecordStore:
    """Filesystem-backed durable store for AERs and their canonical
    pointer index. Every public method is a single, self-contained
    filesystem operation -- no in-memory cache, no cross-call state
    (AESIC-REQ-017's statelessness requirement, mirrored here)."""

    def __init__(self, root: Path = DEFAULT_STORAGE_ROOT) -> None:
        self._root = Path(root)

    def _ensure_within_root(self, path: Path, field_name: str) -> Path:
        """Defense-in-depth root-containment check (147O.2-F-1), in
        addition to (never instead of) ``_validate_identifier_component``:
        the resolved path must remain inside the configured AES storage
        root, accounting for symlinks in already-existing parent
        directories."""

        resolved_root = self._root.resolve()
        resolved_path = path.resolve()
        if resolved_path != resolved_root and resolved_root not in resolved_path.parents:
            raise AuthorityEvaluationStorageIdentifierError(
                f"{field_name} {resolved_path} resolves outside the AER storage root "
                f"{resolved_root}."
            )
        return path

    def _record_path(self, package_id: str, evaluation_id: str) -> Path:
        _validate_identifier_component(package_id, "package_id")
        _validate_identifier_component(evaluation_id, "evaluation_id")
        path = self._root / "records" / _safe_name(package_id) / f"{_safe_name(evaluation_id)}.json"
        return self._ensure_within_root(path, "record path")

    def _pointer_path(self, package_id: str) -> Path:
        _validate_identifier_component(package_id, "package_id")
        path = self._root / "pointers" / f"{_safe_name(package_id)}.json"
        return self._ensure_within_root(path, "pointer path")

    def _records_directory(self, package_id: str) -> Path:
        _validate_identifier_component(package_id, "package_id")
        path = self._root / "records" / _safe_name(package_id)
        return self._ensure_within_root(path, "records directory")

    # -- Primary store: immutable, compound-keyed --------------------------

    def write_record(self, record: AuthorityEvaluationRecord) -> None:
        """Exclusive-create write under ``(package_id, evaluation_id)``
        (AESIC-REQ-019). A collision is only reachable if two attempts
        somehow presented the identical ``evaluation_id``
        (AESIC-REQ-098's own uniqueness guarantee excludes this by
        construction); an identical-content collision is treated as a
        safe no-op (idempotent retry of the same write), a differing-
        content collision raises ``AuthorityEvaluationRecordConflictError``
        -- this store never silently overwrites an existing AER
        (AESIC-REQ-054/082)."""

        path = self._record_path(record.package_id, record.evaluation_id)
        payload = aer_to_payload(record)
        try:
            _write_exclusive_json(path, payload)
            return
        except FileExistsError:
            pass

        existing = self._read_record_payload(record.package_id, record.evaluation_id)
        if existing.get("record_digest") != payload.get("record_digest"):
            raise AuthorityEvaluationRecordConflictError(
                f"AER already exists for compound key "
                f"({record.package_id!r}, {record.evaluation_id!r}) with a different "
                "record_digest; immutable AERs are never overwritten."
            )
        # Identical content already durably persisted -- idempotent no-op.

    def _read_record_payload(self, package_id: str, evaluation_id: str) -> Dict[str, Any]:
        path = self._record_path(package_id, evaluation_id)
        try:
            raw = path.read_text(encoding="utf-8")
            return json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise AuthorityEvaluationRecordCorruptError(
                f"AER for ({package_id!r}, {evaluation_id!r}) could not be read/parsed: {exc}."
            ) from exc

    def read_record(self, package_id: str, evaluation_id: str) -> Optional[AuthorityEvaluationRecord]:
        path = self._record_path(package_id, evaluation_id)
        if not path.exists():
            return None
        payload = self._read_record_payload(package_id, evaluation_id)
        if not verify_aer_digest(payload):
            raise AuthorityEvaluationRecordCorruptError(
                f"AER for ({package_id!r}, {evaluation_id!r}) failed digest verification."
            )
        return aer_from_payload(payload)

    def list_evaluation_ids(self, package_id: str) -> tuple:
        directory = self._records_directory(package_id)
        if not directory.exists():
            return ()
        return tuple(sorted(p.stem for p in directory.glob("*.json")))

    # -- Canonical pointer index: mutable, package_id-keyed -----------------

    def read_canonical(self, package_id: str) -> Optional[AuthorityEvaluationRecord]:
        """Read the canonical AER for ``package_id`` via the pointer's own
        read-indirection (AESIC-REQ-119 item 2). Returns ``None`` if no
        canonical pointer has ever been established. Raises
        ``CanonicalPointerCorruptError`` (fail-closed, AESIC-REQ-126/127)
        on any digest mismatch -- never silently returns mismatched
        content."""

        pointer = self.read_pointer(package_id)
        if pointer is None:
            return None

        # AESIC-N-01: the *requested* storage key is authoritative -- a
        # pointer must never be allowed to redirect a lookup to a namespace
        # of its own choosing. A pointer physically stored under
        # `pointers/<package_id>.json` whose own embedded `package_id`
        # names a different key is corrupt/tampered; fail closed with no
        # fallback lookup under the embedded key.
        if pointer.package_id != package_id:
            raise CanonicalPointerCorruptError(
                f"Canonical pointer stored under package_id {package_id!r} carries an "
                f"embedded package_id of {pointer.package_id!r}; the requested storage key "
                "is authoritative and a pointer must not choose its own lookup namespace."
            )

        record = self.read_record(package_id, pointer.evaluation_id)
        if record is None:
            raise CanonicalPointerCorruptError(
                f"Canonical pointer for {package_id!r} names "
                f"({package_id!r}, {pointer.evaluation_id!r}), which does not exist "
                "in the primary AER store."
            )
        if record.package_id != package_id:
            raise CanonicalPointerCorruptError(
                f"Canonical pointer for {package_id!r} resolved to an AER whose own "
                f"compound-key package_id is {record.package_id!r}, not {package_id!r}."
            )
        if record.record_id != pointer.record_id:
            raise CanonicalPointerCorruptError(
                f"Canonical pointer for {package_id!r} names record_id {pointer.record_id!r}, "
                f"but the referenced compound-keyed AER carries record_id {record.record_id!r}."
            )
        recomputed_digest = aer_to_payload(record)["record_digest"]
        if recomputed_digest != pointer.record_digest:
            raise CanonicalPointerCorruptError(
                f"Canonical pointer for {package_id!r} carries record_digest "
                f"{pointer.record_digest!r}, which disagrees with the referenced AER's own "
                f"self-carried digest {recomputed_digest!r}."
            )
        return record

    def read_pointer(self, package_id: str) -> Optional[CanonicalPointer]:
        path = self._pointer_path(package_id)
        if not path.exists():
            return None
        try:
            raw = path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise CanonicalPointerCorruptError(
                f"Canonical pointer for {package_id!r} could not be read/parsed: {exc}."
            ) from exc
        if not verify_pointer_digest(payload):
            raise CanonicalPointerCorruptError(
                f"Canonical pointer for {package_id!r} failed pointer_digest verification."
            )
        return pointer_from_payload(payload)

    def write_pointer(self, pointer: CanonicalPointer) -> None:
        """Atomic-replace write (AESIC-REQ-119 item 2, AESIC-REQ-086).
        Disclosed last-write-wins under concurrency (AESIC-REQ-120) -- no
        conditional/compare-and-swap semantics, mirroring IWPC-REQ-144/147's
        own precedent for everything upstream of Publication's true commit
        point. May raise ``OSError`` on a genuine storage-layer failure;
        the caller (AES) is responsible for translating that into
        ``CanonicalPointerUpdateFailedError`` (AESIC-REQ-130 item 7,
        AESIC-REQ-131)."""

        path = self._pointer_path(pointer.package_id)
        _write_atomic_json(path, pointer_to_payload(pointer))


__all__ = ["DEFAULT_STORAGE_ROOT", "AuthorityEvaluationRecordStore"]
