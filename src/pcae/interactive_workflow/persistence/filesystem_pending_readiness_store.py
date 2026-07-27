"""Filesystem-backed Pending-Readiness Store (Phase 145E; IWPC-001 v1.1
§14, IWPC-REQ-078-092; §15 Artifact Binding; §19.1; §21; §22; §23).

Durable, repository-local persistence of a constructed
``PublicationReadinessPackage`` between a decision session reaching
``readiness`` construction and a later publication invocation
(IWPC-REQ-078). Explicitly non-authoritative (IWPC-REQ-079): this store
holds a copy of an already-immutable package; it never evaluates
authority, decides publication success, or generates canonical governance
records (PEC-001's own ``PublicationRecordStore`` remains the sole
authoritative record of what was actually published).

No abstract base class governs this store -- unlike
``FilesystemSessionRepository`` (Phase 145D), which implements the
pre-existing ``SessionRepository`` ABC (Phase 143K), IWPC-001 v1.1 §14
defines no separate interface for the Pending-Readiness Store, and none
exists elsewhere in this repository. ``FilesystemPendingReadinessStore``
is therefore the sole concrete class, not an ABC implementation.

Storage layout (IWPC-REQ-088): two sibling directories under the same
parent ``SessionRepository`` uses for its own flat session-file layout
(IWPC-REQ-070) --

- ``.pcae/decision-sessions/pending-packages/<package_id>.json`` --
  packages not yet successfully published.
- ``.pcae/decision-sessions/pending-packages/consumed/<package_id>.json``
  -- packages moved here (``os.replace``, never deleted) after a
  successful publication (IWPC-REQ-088).

This nesting is explicitly frozen by IWPC-REQ-088's own path and does not
violate the "must not overlap ... SessionRepository storage" rule this
phase's governing prompt states, because ``FilesystemSessionRepository.
list_session_ids`` already skips directory entries -- ``pending-packages/``
is invisible to session enumeration by construction, not by a new guard
added here.

Every persisted package is preserved exactly as given at creation
(IWPC-REQ-091): the store never reconstructs a package from session
state, never mutates package-content fields after creation, and only its
own store-level metadata wrapper (attempt linkage, consumption
disposition) is ever updated in place. A whole-package SHA-256 content
digest (IWPC-REQ-081, canonical serialization per IWPC-REQ-057) is
computed at write time and recomputed at every read, so tampering is
detected independent of trusting the filesystem alone (IWPC-REQ-165) --
the store fails closed (``PendingReadinessDigestMismatchError``) on
mismatch rather than trusting a persisted digest.

Package-identifier format decision (disclosed): unlike ``session_id``
(the frozen ``CDS-<uuid4>`` syntax, IWC-001 v1.1 §4.1), no canonical
``package_id`` generation scheme exists anywhere in this repository as of
Phase 145E -- ``PublicationHandoff.build_package`` accepts ``package_id``
as a caller-supplied string with no fixed shape (only "non-empty",
enforced by ``PublicationReadinessPackage.__post_init__``). IWPC-REQ-163
anticipates validating against "the package-id format
``PublicationHandoff.build_package`` produces", but no such format is
implemented yet (deferred to a future CLI/transport phase that assigns
package ids). This store therefore validates ``package_id`` as a generic
safe path component (non-empty, bounded length, restricted character
set, no path separators, no ``.``/``..`` components) rather than against
a specific generated-id regex -- the strictest validation possible given
the current, still-open upstream format decision. This is a disclosed
implementation decision, not a silent reinterpretation of the contract:
it satisfies IWPC-REQ-162/163's filesystem-security intent (reject
anything that isn't a safe path component before it is ever joined into
a path) without inventing a specific id-shape the contract does not yet
define.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pcae.interactive_workflow.errors import (
    PendingReadinessAlreadyConsumedError,
    PendingReadinessAttemptConflictError,
    PendingReadinessDigestMismatchError,
    PendingReadinessPackageAlreadyExistsError,
    PendingReadinessPackageNotFoundError,
    PendingReadinessStoreCorruptError,
    PersistenceUnavailableError,
    PublicationHandoffSerializationError,
    UnsupportedVersionError,
)
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.serialization.publication_handoff_schema import (
    from_payload as _package_from_payload,
)
from pcae.interactive_workflow.serialization.publication_handoff_schema import (
    to_payload as _package_to_payload,
)
from pcae.interactive_workflow.session.identity import validate_session_id

STORE_SCHEMA_VERSION = "pending-readiness-store/1.0"
"""Store-level schema version (IWPC-REQ-111's own example value),
independent of ``PublicationReadinessPackage.schema_version`` nested
inside it."""

DEFAULT_SESSIONS_ROOT = Path(".pcae") / "decision-sessions"
DEFAULT_STORAGE_ROOT = DEFAULT_SESSIONS_ROOT / "pending-packages"
"""Default pending-package storage root (IWPC-REQ-088)."""

CONSUMED_SUBDIRECTORY = "consumed"
"""Sub-directory name packages move into on successful publication
(IWPC-REQ-088)."""

DISPOSITION_PENDING = "pending"
DISPOSITION_CONSUMED = "consumed"

OUTCOME_SUCCEEDED = "succeeded"
OUTCOME_FAILED = "failed"
_VALID_OUTCOMES = frozenset({OUTCOME_SUCCEEDED, OUTCOME_FAILED})

_TEMP_PREFIX = ".tmp-"
_PACKAGE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")


def is_valid_package_id(value: object) -> bool:
    """Return whether ``value`` is a safe pending-readiness package
    identifier: a non-empty, bounded-length string built only from
    letters, digits, ``.``, ``_``, ``-``, containing no path separator
    and no ``.``/``..`` path component (IWPC-REQ-162/163)."""

    if not isinstance(value, str) or not value:
        return False
    if not _PACKAGE_ID_PATTERN.match(value):
        return False
    if value in (".", ".."):
        return False
    return True


def _paths_overlap(a: Path, b: Path) -> bool:
    a_parts = Path(os.path.normpath(str(a.absolute())))
    b_parts = Path(os.path.normpath(str(b.absolute())))
    if a_parts == b_parts:
        return True
    return a_parts in b_parts.parents or b_parts in a_parts.parents


@dataclass(frozen=True)
class PublicationAttemptRecord:
    """One append-only publication-attempt-linkage entry (IWPC-REQ-087):
    a lightweight back-reference only, distinct from, and never
    substituting for, PEC-001's own ``PublicationRecordStore.attempts/``
    audit."""

    attempt_id: str
    outcome: str
    timestamp: str


@dataclass(frozen=True)
class PendingReadinessRecord:
    """A loaded pending-readiness store record: the exact, immutable
    ``PublicationReadinessPackage`` (IWPC-REQ-091) plus the store's own
    mutable metadata wrapper (disposition, attempt linkage, and
    post-success record binding, IWPC-REQ-086/087)."""

    package: PublicationReadinessPackage
    package_id: str
    session_id: str
    package_digest: str
    persisted_at: str
    disposition: str
    attempts: Tuple[PublicationAttemptRecord, ...]
    record_id: Optional[str] = None
    publication_attempt_id: Optional[str] = None
    consumed_at: Optional[str] = None


class FilesystemPendingReadinessStore:
    """Concrete filesystem-backed Pending-Readiness Store (IWPC-001 v1.1
    §14).

    Owns bytes and store-level metadata only; never evaluates
    authorization, never decides publication success, never invokes
    publication, and never reconstructs a package from session state
    (IWPC-REQ-079, IWPC-REQ-091). Depends only on
    ``PublicationReadinessPackage``/its existing serialization, stdlib
    filesystem primitives, and ``session.identity`` (for validating an
    embedded ``session_id`` -- never on the CLI, a transport adapter,
    ``SessionCoordinator`` orchestration, the Publication Coordinator,
    lifecycle, the Permission Broker, or a governance-record
    implementation.
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        resolved_root = Path(root) if root is not None else DEFAULT_STORAGE_ROOT
        chgr_prefix = Path(".pcae") / "governance-records"
        if _paths_overlap(resolved_root, chgr_prefix):
            raise ValueError(
                "FilesystemPendingReadinessStore root must not overlap "
                f"{str(chgr_prefix) + '/'!r} (IWC-001 v1.1 §4.10, IWC-REQ-049)."
            )
        self._root = resolved_root
        self._consumed_root = resolved_root / CONSUMED_SUBDIRECTORY

    @property
    def root(self) -> Path:
        return self._root

    @property
    def consumed_root(self) -> Path:
        return self._consumed_root

    # -- path safety (IWPC-REQ-162, IWPC-REQ-163) ---------------------------

    def _pending_path(self, package_id: str) -> Path:
        self._require_valid_package_id(package_id)
        candidate = self._root / f"{package_id}.json"
        if candidate.parent.absolute() != self._root.absolute():
            raise ValueError(
                f"Package identifier {package_id!r} does not resolve within the "
                "store's pending storage root."
            )
        return candidate

    def _consumed_path(self, package_id: str) -> Path:
        self._require_valid_package_id(package_id)
        candidate = self._consumed_root / f"{package_id}.json"
        if candidate.parent.absolute() != self._consumed_root.absolute():
            raise ValueError(
                f"Package identifier {package_id!r} does not resolve within the "
                "store's consumed storage root."
            )
        return candidate

    @staticmethod
    def _require_valid_package_id(package_id: str) -> None:
        if not is_valid_package_id(package_id):
            raise ValueError(
                f"Package identifier {package_id!r} is not a safe path component "
                "(IWPC-REQ-162, IWPC-REQ-163)."
            )

    def _reject_symlink(self, path: Path) -> None:
        if path.exists() and path.is_symlink():
            raise PersistenceUnavailableError(
                "Refusing to operate on a symlinked pending-readiness artifact."
            )

    def _ensure_dir(self, path: Path) -> None:
        if path.exists() and path.is_symlink():
            raise PersistenceUnavailableError(
                "Refusing to operate through a symlinked storage root."
            )
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to prepare the pending-readiness store storage root."
            ) from exc

    # -- digest (IWPC-REQ-081, IWPC-REQ-057, IWPC-REQ-165) -------------------

    @staticmethod
    def _compute_digest(package: PublicationReadinessPackage) -> str:
        canonical = json.dumps(_package_to_payload(package), sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # -- wire format ----------------------------------------------------

    @staticmethod
    def _wrap(
        *,
        package: PublicationReadinessPackage,
        package_digest: str,
        persisted_at: str,
        disposition: str,
        attempts: Tuple[PublicationAttemptRecord, ...],
        record_id: Optional[str],
        publication_attempt_id: Optional[str],
        consumed_at: Optional[str],
    ) -> Dict[str, Any]:
        return {
            "schema_version": STORE_SCHEMA_VERSION,
            "package_id": package.package_id,
            "session_id": package.session_id,
            "package_digest": package_digest,
            "persisted_at": persisted_at,
            "disposition": disposition,
            "record_id": record_id,
            "publication_attempt_id": publication_attempt_id,
            "consumed_at": consumed_at,
            "attempts": [
                {"attempt_id": a.attempt_id, "outcome": a.outcome, "timestamp": a.timestamp}
                for a in attempts
            ],
            "package": _package_to_payload(package),
        }

    @staticmethod
    def _unwrap(package_id: str, payload: Any) -> PendingReadinessRecord:
        if not isinstance(payload, dict):
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} is not a JSON object."
            )
        if payload.get("schema_version") != STORE_SCHEMA_VERSION:
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} carries an unsupported "
                "store schema_version."
            )
        if payload.get("package_id") != package_id:
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} does not carry the "
                "expected package identifier."
            )
        package_payload = payload.get("package")
        if not isinstance(package_payload, dict):
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} is missing its nested "
                "package payload."
            )
        try:
            package = _package_from_payload(package_payload)
        except (PublicationHandoffSerializationError, UnsupportedVersionError) as exc:
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} is malformed."
            ) from exc
        if package.package_id != package_id:
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} carries a mismatched "
                "nested package identifier."
            )
        if payload.get("session_id") != package.session_id:
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} carries a session "
                "binding that does not match its nested package (IWPC-REQ-082)."
            )
        digest = payload.get("package_digest")
        if not isinstance(digest, str) or not digest:
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} is missing its "
                "package digest."
            )
        recomputed = FilesystemPendingReadinessStore._compute_digest(package)
        if recomputed != digest:
            raise PendingReadinessDigestMismatchError(
                f"Pending-readiness package {package_id!r}: stored digest "
                f"{digest!r} does not match the digest recomputed from its exact "
                f"content ({recomputed!r})."
            )
        disposition = payload.get("disposition")
        if disposition not in (DISPOSITION_PENDING, DISPOSITION_CONSUMED):
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} carries an "
                "unrecognized disposition."
            )
        persisted_at = payload.get("persisted_at")
        if not isinstance(persisted_at, str) or not persisted_at:
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} is missing "
                "persisted_at."
            )
        raw_attempts = payload.get("attempts", [])
        if not isinstance(raw_attempts, list):
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} carries malformed "
                "attempt-linkage metadata."
            )
        attempts = []
        for entry in raw_attempts:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("attempt_id"), str)
                or entry.get("outcome") not in _VALID_OUTCOMES
                or not isinstance(entry.get("timestamp"), str)
            ):
                raise PendingReadinessStoreCorruptError(
                    f"Pending-readiness file for {package_id!r} carries malformed "
                    "attempt-linkage metadata."
                )
            attempts.append(
                PublicationAttemptRecord(
                    attempt_id=entry["attempt_id"],
                    outcome=entry["outcome"],
                    timestamp=entry["timestamp"],
                )
            )
        return PendingReadinessRecord(
            package=package,
            package_id=package_id,
            session_id=package.session_id,
            package_digest=digest,
            persisted_at=persisted_at,
            disposition=disposition,
            attempts=tuple(attempts),
            record_id=payload.get("record_id"),
            publication_attempt_id=payload.get("publication_attempt_id"),
            consumed_at=payload.get("consumed_at"),
        )

    # -- atomic write (IWPC-REQ-072 pattern, IWPC-REQ-155, IWPC-REQ-161) ----

    def _write_atomic(self, directory: Path, path: Path, payload: Dict[str, Any]) -> None:
        self._ensure_dir(directory)
        self._reject_symlink(path)
        data = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        fd, tmp_name = tempfile.mkstemp(prefix=_TEMP_PREFIX, dir=str(directory))
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, str(path))
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to persist the pending-readiness package record."
            ) from exc
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    # -- public interface -------------------------------------------------

    def create(self, package: PublicationReadinessPackage, *, persisted_at: str) -> None:
        """Persist a brand-new pending package (IWPC-REQ-078/091).

        Raises ``PendingReadinessPackageAlreadyExistsError`` if a record
        already exists for ``package.package_id`` in either the pending
        or ``consumed/`` location -- ``create`` never silently
        overwrites.
        """

        validate_session_id(package.session_id)
        pending_path = self._pending_path(package.package_id)
        consumed_path = self._consumed_path(package.package_id)
        self._ensure_dir(self._root)
        self._reject_symlink(pending_path)
        self._reject_symlink(consumed_path)
        if pending_path.exists() or consumed_path.exists():
            raise PendingReadinessPackageAlreadyExistsError(
                f"A pending-readiness package record already exists for "
                f"{package.package_id!r}."
            )
        digest = self._compute_digest(package)
        payload = self._wrap(
            package=package,
            package_digest=digest,
            persisted_at=persisted_at,
            disposition=DISPOSITION_PENDING,
            attempts=(),
            record_id=None,
            publication_attempt_id=None,
            consumed_at=None,
        )
        self._write_atomic(self._root, pending_path, payload)

    def load(self, package_id: str) -> PendingReadinessRecord:
        """Return the persisted record for ``package_id``.

        Checks the ``consumed/`` location first, then the pending
        location (IWPC-REQ-090): once a package is durably consumed, its
        consumed record is authoritative even if a stale pending-side
        copy also happens to remain on disk after an interrupted
        disposition move (IWPC-REQ-154) -- the store never re-derives or
        prefers a stale pending duplicate over a confirmed consumed
        record. Raises ``PendingReadinessPackageNotFoundError`` if no
        record exists in either location.
        """

        consumed_path = self._consumed_path(package_id)
        self._reject_symlink(consumed_path)
        if consumed_path.exists():
            return self._load_from(package_id, consumed_path)
        pending_path = self._pending_path(package_id)
        self._reject_symlink(pending_path)
        if pending_path.exists():
            return self._load_from(package_id, pending_path)
        raise PendingReadinessPackageNotFoundError(
            f"No pending-readiness package record exists for {package_id!r}."
        )

    def _load_from(self, package_id: str, path: Path) -> PendingReadinessRecord:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to read the pending-readiness package record."
            ) from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PendingReadinessStoreCorruptError(
                f"Pending-readiness file for {package_id!r} is not valid JSON."
            ) from exc
        return self._unwrap(package_id, payload)

    def exists(self, package_id: str) -> bool:
        if not is_valid_package_id(package_id):
            return False
        consumed_path = self._consumed_path(package_id)
        pending_path = self._pending_path(package_id)
        return (consumed_path.exists() and not consumed_path.is_symlink()) or (
            pending_path.exists() and not pending_path.is_symlink()
        )

    def find_by_session_id(self, session_id: str) -> Optional[PendingReadinessRecord]:
        """Return the package bound to ``session_id``, searching both the
        pending and ``consumed/`` locations, or ``None`` if none exists
        (IWPC-001 v1.4 §35, IWPC-REQ-082/107/198: ``session_id`` remains
        the sole readiness uniqueness key for a session's *entire*
        lifecycle, not merely while a package is pending). A package's
        disposition moving from ``pending`` to ``consumed`` never makes it
        invisible to this lookup (IWPC-REQ-198).

        Raises ``PendingReadinessStoreCorruptError`` (``persistence_corrupt``)
        if more than one record matches ``session_id`` across the two
        locations -- a historical inconsistency predating IWPC-REQ-197
        that this method fails closed on rather than silently resolving
        (IWPC-REQ-204)."""

        validate_session_id(session_id)
        matches: List[PendingReadinessRecord] = []
        for package_id in self.list_package_ids():
            record = self.load(package_id)
            if record.session_id == session_id:
                matches.append(record)
        for package_id in self._list_consumed_package_ids():
            record = self.load(package_id)
            if record.session_id == session_id:
                matches.append(record)
        if len(matches) > 1:
            raise PendingReadinessStoreCorruptError(
                f"More than one pending-readiness package record exists for "
                f"session_id {session_id!r} ({len(matches)} matching records); "
                "this is a historical inconsistency and cannot be silently "
                "resolved (IWPC-001 v1.4 IWPC-REQ-204)."
            )
        return matches[0] if matches else None

    def list_package_ids(self) -> List[str]:
        """Return every pending (not yet consumed) package identifier,
        sorted deterministically. Filters by filename shape only --
        never loads full package content merely to enumerate (per this
        phase's Enumeration guidance)."""

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
                "Failed to enumerate the pending-readiness store storage root."
            ) from exc
        for entry in entries:
            name = entry.name
            if not name.endswith(".json") or name.startswith("."):
                continue
            if entry.is_dir() or entry.is_symlink():
                continue
            candidate_id = name[: -len(".json")]
            if not is_valid_package_id(candidate_id):
                continue
            # A package already moved to consumed/ is no longer pending,
            # even if a stale copy also lingers here post-interruption
            # (IWPC-REQ-154) -- exclude it deterministically.
            if self._consumed_path(candidate_id).exists():
                continue
            ids.append(candidate_id)
        return sorted(ids)

    def _list_consumed_package_ids(self) -> List[str]:
        """Return every consumed package identifier, sorted
        deterministically -- mirrors ``list_package_ids``'s enumeration
        discipline (filename shape only, no full-content load merely to
        enumerate) for the ``consumed/`` location (IWPC-REQ-198)."""

        if not self._consumed_root.exists():
            return []
        if self._consumed_root.is_symlink():
            raise PersistenceUnavailableError(
                "Refusing to operate through a symlinked storage root."
            )
        ids: List[str] = []
        try:
            entries = list(self._consumed_root.iterdir())
        except OSError as exc:
            raise PersistenceUnavailableError(
                "Failed to enumerate the pending-readiness store consumed "
                "storage root."
            ) from exc
        for entry in entries:
            name = entry.name
            if not name.endswith(".json") or name.startswith("."):
                continue
            if entry.is_dir() or entry.is_symlink():
                continue
            candidate_id = name[: -len(".json")]
            if not is_valid_package_id(candidate_id):
                continue
            ids.append(candidate_id)
        return sorted(ids)

    def record_publication_attempt(
        self,
        package_id: str,
        *,
        attempt_id: str,
        outcome: str,
        timestamp: str,
        record_id: Optional[str] = None,
        publication_attempt_id: Optional[str] = None,
    ) -> PendingReadinessRecord:
        """Append a publication-attempt-linkage record (IWPC-REQ-087).

        On ``outcome="succeeded"``, additionally moves the package's
        disposition to ``consumed`` and records ``record_id``/
        ``publication_attempt_id`` (IWPC-REQ-086, IWPC-REQ-088); the
        package remains in the pending location, unmoved, on
        ``outcome="failed"`` (IWPC-REQ-089). Idempotent by
        ``attempt_id``: replaying the exact same ``(attempt_id,
        outcome)`` pair is a no-op returning the existing record
        unchanged. A conflicting replay (same ``attempt_id``, different
        ``outcome``) raises ``PendingReadinessAttemptConflictError``.
        Raises ``PendingReadinessAlreadyConsumedError`` if a *new*
        attempt is proposed against a package whose disposition is
        already ``consumed`` -- a consumed package's disposition is
        terminal (IWPC-REQ-088's own "moved, not deleted" retention
        guarantee).
        """

        if outcome not in _VALID_OUTCOMES:
            raise ValueError(
                f"outcome must be one of {sorted(_VALID_OUTCOMES)!r}, got {outcome!r}."
            )
        if outcome == OUTCOME_SUCCEEDED and not record_id:
            raise ValueError("record_id is required when outcome='succeeded'.")

        record = self.load(package_id)
        existing = next((a for a in record.attempts if a.attempt_id == attempt_id), None)
        if existing is not None:
            if existing.outcome != outcome:
                raise PendingReadinessAttemptConflictError(
                    f"Publication attempt {attempt_id!r} for package {package_id!r} "
                    f"was already recorded with outcome {existing.outcome!r}; a "
                    f"conflicting outcome {outcome!r} was proposed."
                )
            return record

        if record.disposition == DISPOSITION_CONSUMED:
            raise PendingReadinessAlreadyConsumedError(
                f"Package {package_id!r} is already consumed; no new publication "
                "attempt may be recorded against it."
            )

        new_attempts = record.attempts + (
            PublicationAttemptRecord(attempt_id=attempt_id, outcome=outcome, timestamp=timestamp),
        )

        if outcome == OUTCOME_SUCCEEDED:
            payload = self._wrap(
                package=record.package,
                package_digest=record.package_digest,
                persisted_at=record.persisted_at,
                disposition=DISPOSITION_CONSUMED,
                attempts=new_attempts,
                record_id=record_id,
                publication_attempt_id=publication_attempt_id,
                consumed_at=timestamp,
            )
            consumed_path = self._consumed_path(package_id)
            self._write_atomic(self._consumed_root, consumed_path, payload)
            pending_path = self._pending_path(package_id)
            if pending_path.exists() and not pending_path.is_symlink():
                try:
                    os.unlink(pending_path)
                except OSError as exc:
                    raise PersistenceUnavailableError(
                        "Failed to remove the superseded pending-readiness copy "
                        "after a successful disposition move."
                    ) from exc
            return self.load(package_id)

        payload = self._wrap(
            package=record.package,
            package_digest=record.package_digest,
            persisted_at=record.persisted_at,
            disposition=DISPOSITION_PENDING,
            attempts=new_attempts,
            record_id=record.record_id,
            publication_attempt_id=record.publication_attempt_id,
            consumed_at=record.consumed_at,
        )
        pending_path = self._pending_path(package_id)
        self._write_atomic(self._root, pending_path, payload)
        return self.load(package_id)


__all__ = [
    "STORE_SCHEMA_VERSION",
    "DEFAULT_STORAGE_ROOT",
    "DEFAULT_SESSIONS_ROOT",
    "CONSUMED_SUBDIRECTORY",
    "DISPOSITION_PENDING",
    "DISPOSITION_CONSUMED",
    "OUTCOME_SUCCEEDED",
    "OUTCOME_FAILED",
    "PublicationAttemptRecord",
    "PendingReadinessRecord",
    "FilesystemPendingReadinessStore",
    "is_valid_package_id",
]
