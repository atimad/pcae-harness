"""HATP Evidence Store — Exclusive-Publication Evidence Store
(Phase 149O.12A, Wave B of the 149O.11 implementation plan).

Implements HSCE-REQ-007, HSCE-REQ-041..045, HSCE-REQ-052, HSCE-REQ-054..055,
HSCE-REQ-057..058, HSCE-REQ-060..061, HSCE-REQ-064 (`docs/contracts/
HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`, HSCE-001 v1.1 §20,
§24-25, §27-28), including the repaired HSCE-REQ-052 atomic hard-link
exclusive-publication algorithm (Phase 149O.10.1 §44), and the
149O.10.2-Obs-3 implementation-level mapping selected by the 149O.11 plan
(§8, §10.5): an unsafe existing-final-object comparison (unreadable,
directory, or other non-regular object) fails closed as
`evidence_persistence_failure`, never `evidence_conflict`.

`.pcae/hatp-evidence/` is agent-writable, repository-local, **untrusted**
storage -- not an authority root (HSCE-REQ-060). This module grants no
approval: no method here reports, derives, or implies `approval_present`,
and no method treats file existence alone as approval (HSCE-REQ-061) --
there is deliberately no `exists()`, `latest()`, `list_latest()`,
`overwrite()`, `update()`, `delete_authority()`, or `approve()` method on
`HATPEvidenceStore`. Security comes exclusively from the embedded proof's
own signature and protected trust-store state, verified elsewhere
(`human_approval_trusted_provenance.verify_hatp_proof`), never from this
store's own write/read success.

This module performs no cryptographic verification and calls neither
`verify_hatp_proof` nor any Permission Broker/RAE authority function --
it is the lowest-level storage substrate only (governing-prompt §73-75).
"""
from __future__ import annotations

import contextlib
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pcae.core.hatp_signed_evidence import (
    HATPSignedEvidenceEnvelope,
    parse_hatp_signed_evidence,
    serialize_hatp_signed_evidence,
    validate_evidence_id,
)
from pcae.core.paths import HarnessPath

#: HSCE-REQ-041/042: the evidence store root and layout, relative to the
#: repository root -- never resolved relative to an arbitrary CWD.
_STORE_ROOT_COMPONENTS = (".pcae", "hatp-evidence", "envelopes")


class HATPEvidenceStoreError(Exception):
    """Base error for `HATPEvidenceStore` operations. Distinct from
    `hatp_signed_evidence.HATPSignedEvidenceError` (envelope structural
    errors) -- this module's errors concern storage/publication only."""


class EvidenceNotFoundError(HATPEvidenceStoreError):
    """`evidence_id` has no corresponding file in the store
    (HSCE-REQ-064's load-path `evidence_not_found` category -- distinct
    from the write-path's 12-member `error_type` table, §21 of the
    149O.11 implementation plan)."""


class EvidenceConflictError(HATPEvidenceStoreError):
    """A differing envelope already exists under this `evidence_id`
    (HSCE-REQ-039(B)/HSCE-REQ-047 `evidence_conflict`). The persisted
    winner is never overwritten."""


class EvidencePersistenceFailureError(HATPEvidenceStoreError):
    """The atomic write/publish (or a load-path filesystem operation)
    failed at the filesystem layer (HSCE-REQ-047 `evidence_persistence_
    failure`) -- includes the 149O.10.2-Obs-3 unsafe-loser-comparison
    mapping (§10.5 of the 149O.11 plan) and any non-`FileExistsError`
    `os.link` failure (`EXDEV`, `EPERM`, unsupported filesystem, ...).
    No fallback to `os.replace` or any other overwrite-capable primitive
    is ever attempted."""


@dataclass(frozen=True)
class HATPEvidencePublicationResult:
    """`publish()`'s sole return type. Never a bare boolean, never an
    `approved`/`permission`/`executed` field (HSCE-REQ-065/066's success-
    output discipline extended here at the storage layer)."""

    evidence_id: str
    path: Path
    idempotent: bool


def _resolve_no_strict(path: Path) -> Path:
    try:
        return path.resolve(strict=False)
    except OSError as exc:
        raise EvidencePersistenceFailureError(f"failed to resolve path {path}: {exc}") from exc


class HATPEvidenceStore:
    """Filesystem-backed evidence store for `HATPSignedEvidenceEnvelope`
    (HSCE-REQ-007: a distinct, separately-rooted directory from RAE's own
    `.pcae/rollback-approval-evidence/`, never merged or cross-addressed).

    The constructor accepts an explicit `repository_root` (mirroring
    `RollbackApprovalEvidenceStore`'s own explicit-root convention)
    rather than deriving it implicitly from CWD -- callers resolve
    `HarnessPath.cwd()` once and pass it in. Construction alone performs
    no filesystem mutation: `.pcae/hatp-evidence/envelopes/` is created,
    if absent, only by `publish()`'s first call (HSCE-REQ-055)."""

    def __init__(self, repository_root: HarnessPath) -> None:
        self._repository_root = Path(repository_root.path)
        self._envelopes_dir = self._repository_root.joinpath(*_STORE_ROOT_COMPONENTS)

    @property
    def repository_root(self) -> Path:
        return self._repository_root

    @property
    def envelopes_dir(self) -> Path:
        return self._envelopes_dir

    def path_for(self, evidence_id: str) -> Path:
        """Pure path computation (HSCE-REQ-056): validates `evidence_id`
        before any path is constructed from it, performs no I/O."""

        validated = validate_evidence_id(evidence_id)
        return self._envelopes_dir / f"{validated}.json"

    def _check_no_escaping_symlink_components(self) -> None:
        """HSCE-REQ-058: if any path component of `.pcae/hatp-evidence/`
        or `envelopes/` is a symlink escaping the repository root, fail
        closed rather than follow it. Only existing components are
        checked -- a component that does not yet exist cannot yet be a
        symlink, and `publish()`'s own `mkdir` creates fresh, ordinary
        directories strictly under the repository root."""

        resolved_root = _resolve_no_strict(self._repository_root)
        current = self._repository_root
        for component in _STORE_ROOT_COMPONENTS:
            current = current / component
            if not current.is_symlink():
                continue
            resolved_current = _resolve_no_strict(current)
            if resolved_current != resolved_root and resolved_root not in resolved_current.parents:
                raise EvidencePersistenceFailureError(
                    f"path component {current} is a symlink escaping the repository root"
                )

    def load(self, evidence_id: str) -> HATPSignedEvidenceEnvelope:
        """Explicit-`evidence_id`-only loader (HSCE-REQ-044/HSCE-REQ-021,
        SC-6). No `latest`/`newest`/glob/single-file-fallback mode exists
        here. Missing evidence raises `EvidenceNotFoundError`; a corrupt
        or digest-mismatched file raises the specific structural error
        `hatp_signed_evidence.parse_hatp_signed_evidence` itself raises
        (no fallback to another evidence file, no repair-in-place)."""

        path = self.path_for(evidence_id)
        self._check_no_escaping_symlink_components()

        if path.is_symlink():
            raise EvidencePersistenceFailureError(
                f"evidence path {path} is a symlink; refusing to load through it"
            )
        if not path.exists():
            raise EvidenceNotFoundError(f"no evidence found for evidence_id={evidence_id!r}")
        if not path.is_file():
            raise EvidencePersistenceFailureError(f"evidence path {path} is not a regular file")

        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise EvidencePersistenceFailureError(f"failed to read evidence at {path}: {exc}") from exc

        return parse_hatp_signed_evidence(raw)

    def _resolve_publication_race_loss(
        self,
        evidence_id: str,
        final_path: Path,
        candidate_bytes: bytes,
    ) -> HATPEvidencePublicationResult:
        """HSCE-REQ-052 step 6/9, §10.5 of the 149O.11 plan (149O.10.2-Obs-3
        mapping): this writer lost the exclusive-publication race. Before
        reading anything, re-validate that `final_path` is a safe,
        readable, regular file -- an unsafe object (symlink that appeared
        during the race window, directory, FIFO, socket, device file, or
        otherwise unreadable) fails closed as `evidence_persistence_
        failure`, never `evidence_conflict` and never overwritten/deleted.
        Only a completed, safe, byte-for-byte comparison against readable
        canonical bytes decides idempotent-success vs. conflict."""

        if os.path.islink(final_path):
            raise EvidencePersistenceFailureError(
                f"evidence destination {final_path} became a symlink during publication; refusing"
            )

        try:
            stat_result = os.lstat(final_path)
        except OSError as exc:
            raise EvidencePersistenceFailureError(
                f"failed to inspect existing evidence at {final_path}: {exc}"
            ) from exc

        if not stat.S_ISREG(stat_result.st_mode):
            raise EvidencePersistenceFailureError(
                f"evidence destination {final_path} is occupied by a non-regular-file object; "
                f"refusing to compare or overwrite"
            )

        try:
            existing_bytes = final_path.read_bytes()
        except OSError as exc:
            raise EvidencePersistenceFailureError(
                f"failed to read existing evidence at {final_path}: {exc}"
            ) from exc

        if existing_bytes == candidate_bytes:
            return HATPEvidencePublicationResult(evidence_id=evidence_id, path=final_path, idempotent=True)

        raise EvidenceConflictError(
            f"evidence_id {evidence_id!r} already has a differing persisted envelope at {final_path}"
        )

    def publish(self, envelope: HATPSignedEvidenceEnvelope) -> HATPEvidencePublicationResult:
        """HSCE-REQ-052: exclusive hard-link publication, exactly per the
        repaired algorithm (Phase 149O.10.1 §44). CREATE-ONCE / NO-CLOBBER
        / FIRST-WRITE-CANONICAL: existing evidence is never overwritten,
        under any condition, by any writer, winning or losing.

        Order of operations (no write occurs after the temp file's
        `os.fsync`+close -- the post-link-FD-safety invariant, HSCE-REQ-052
        step 5):

        1. Validate `evidence_id` / compute `final_path` (`path_for`).
        2. Compute canonical bytes (`serialize_hatp_signed_evidence`).
        3. `mkdir(parents=True, exist_ok=True)` on first publish only.
        4. Create a uniquely-named temp file in the same directory.
        5. Write the complete bytes, `fsync`, close -- no writable
           descriptor referencing the temp inode survives past this line.
        6. Check `final_path` is not already a symlink (HSCE-REQ-057).
        7. Attempt `os.link(temp_path, final_path)`.
        8. Success -> exclusive-publication winner.
        9. `FileExistsError` -> lost the race; resolve via
           `_resolve_publication_race_loss`.
        10. Any other `OSError` -> fail closed, `evidence_persistence_
            failure`. No fallback to `os.replace` or any other
            overwrite-capable primitive, ever.
        11. `finally`: temp file unlink attempted on every exit path; a
            failure to remove it is never authoritative.
        """

        evidence_id = envelope.evidence_id
        final_path = self.path_for(evidence_id)
        self._check_no_escaping_symlink_components()

        candidate_bytes = serialize_hatp_signed_evidence(envelope)

        try:
            self._envelopes_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise EvidencePersistenceFailureError(
                f"failed to create evidence directory {self._envelopes_dir}: {exc}"
            ) from exc

        try:
            fd, temp_name = tempfile.mkstemp(
                dir=str(self._envelopes_dir), prefix=f".{evidence_id}.", suffix=".tmp"
            )
        except OSError as exc:
            raise EvidencePersistenceFailureError(f"failed to create temporary evidence file: {exc}") from exc

        temp_path = Path(temp_name)
        try:
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(candidate_bytes)
                    handle.flush()
                    os.fsync(handle.fileno())
            except OSError as exc:
                raise EvidencePersistenceFailureError(
                    f"failed to durably write candidate evidence bytes: {exc}"
                ) from exc
            # `handle`'s `with` block has closed the fd -- no writable
            # descriptor referencing the temp inode survives past this
            # point, satisfying the close-before-link invariant.

            if os.path.islink(final_path):
                raise EvidencePersistenceFailureError(
                    f"evidence destination {final_path} is a symlink; refusing to write through it"
                )

            try:
                os.link(str(temp_path), str(final_path))
            except FileExistsError:
                return self._resolve_publication_race_loss(evidence_id, final_path, candidate_bytes)
            except OSError as exc:
                raise EvidencePersistenceFailureError(
                    f"failed to publish evidence at {final_path}: {exc}"
                ) from exc

            return HATPEvidencePublicationResult(evidence_id=evidence_id, path=final_path, idempotent=False)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(str(temp_path))
