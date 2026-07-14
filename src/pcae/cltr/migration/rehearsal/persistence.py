"""Stage 2 rehearsal namespace and atomic persistence (135Q §7/§24/§25).

Nested under the existing Stage 1 ``.pcae/cltr-migration/`` root, never a
new top-level directory::

    .pcae/cltr-migration/epochs/<epoch>/
      transitions/<transition-id>/...        # existing Stage 1 evidence, untouched
      rehearsals/<transition-id>/
        candidates/<rehearsal-generation-id>/    # in-progress, pre-finalization
        generations/<rehearsal-generation-id>/   # finalized, immutable
        failures/<rehearsal-generation-id>-<n>/
        quarantine/<rehearsal-generation-id>/
        current-rehearsal                        # atomic, non-authoritative pointer
    .pcae/cltr-migration/status/current-rehearsal-evidence

Reuses Stage 1's own containment/atomicity primitives
(``is_safe_segment``/``safe_join``/``write_atomic``/``write_immutable``,
``pcae.cltr.migration.persistence``, independently corrected by 135R's
F-135R-1 citation repair) rather than reimplementing them. Generation
finalization (candidate directory -> generation directory) uses
directory-level ``os.replace`` -- 135R's F-135R-1 finding discloses this
is a new primitive (POSIX-atomic, but with no prior file-level-only
precedent in this codebase), so it is implemented here explicitly,
with the disclosed Windows-transient-``PermissionError`` retry this
module performs before failing closed.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from pcae.cltr.canonicalization import canonicalize_dict
from pcae.cltr.migration.persistence import (
    DEFAULT_MIGRATION_ROOT,
    PathContainmentError,
    is_safe_segment,
    safe_join,
    write_atomic,
)

#: 135R §26 -- Windows directory rename can transiently fail with
#: PermissionError from an open handle held by another process. Retry a
#: small, bounded number of times before failing closed with a clear
#: diagnostic, distinct from a permanent failure.
_RENAME_RETRY_ATTEMPTS = 3
_RENAME_RETRY_DELAY_SECONDS = 0.05


class RehearsalPersistenceError(ValueError):
    pass


def rehearsals_root(migration_root: Path, migration_epoch: str, transition_id: str) -> Path:
    return safe_join(migration_root, "epochs", migration_epoch, "rehearsals", transition_id)


def candidates_dir(migration_root: Path, migration_epoch: str, transition_id: str, rehearsal_generation_id: str) -> Path:
    root = rehearsals_root(migration_root, migration_epoch, transition_id)
    return safe_join(root, "candidates", rehearsal_generation_id)


def generations_dir(migration_root: Path, migration_epoch: str, transition_id: str, rehearsal_generation_id: str) -> Path:
    root = rehearsals_root(migration_root, migration_epoch, transition_id)
    return safe_join(root, "generations", rehearsal_generation_id)


def failures_dir(migration_root: Path, migration_epoch: str, transition_id: str) -> Path:
    root = rehearsals_root(migration_root, migration_epoch, transition_id)
    return safe_join(root, "failures")


def quarantine_dir(migration_root: Path, migration_epoch: str, transition_id: str, rehearsal_generation_id: str) -> Path:
    root = rehearsals_root(migration_root, migration_epoch, transition_id)
    return safe_join(root, "quarantine", rehearsal_generation_id)


def pointer_path(migration_root: Path, migration_epoch: str, transition_id: str) -> Path:
    root = rehearsals_root(migration_root, migration_epoch, transition_id)
    return root / "current-rehearsal"


def rehearsal_evidence_pointer_path(migration_root: Path) -> Path:
    return migration_root / "status" / "current-rehearsal-evidence"


def write_candidate_artifact(directory: Path, filename: str, content: dict) -> None:
    if not is_safe_segment(filename):
        raise PathContainmentError(f"unsafe artifact filename: {filename!r}")
    target = directory / filename
    if target.is_symlink():
        raise PathContainmentError(f"refusing to write through pre-existing symlink: {target}")
    write_atomic(target, canonicalize_dict(content))


def finalize_generation(candidate_dir: Path, generation_dir: Path) -> None:
    """135Q §20 step 15 -- atomic rename from ``candidates/`` to
    ``generations/``. Directory-level ``os.replace``: rejects (raises,
    never silently overwrites) if the target already exists and is
    non-empty, matching 135R §29's independently-confirmed directory
    semantics (distinct from the file-level atomic-overwrite behavior
    Stage 1's ``write_atomic`` relies on)."""

    generation_dir.parent.mkdir(parents=True, exist_ok=True)
    if generation_dir.exists():
        if any(generation_dir.iterdir()):
            # Idempotent-replay short-circuit is handled by the caller
            # (coordinator) before this is reached in the ordinary path;
            # reaching here with an already-populated target is a
            # conflict, never silently accepted.
            raise RehearsalPersistenceError(
                f"refusing to finalize over an already-populated generation directory: {generation_dir}"
            )
        generation_dir.rmdir()

    last_exc: Optional[OSError] = None
    for attempt in range(_RENAME_RETRY_ATTEMPTS):
        try:
            os.replace(candidate_dir, generation_dir)
            return
        except OSError as exc:  # pragma: no cover - platform-dependent transient failure
            last_exc = exc
            if attempt < _RENAME_RETRY_ATTEMPTS - 1:
                time.sleep(_RENAME_RETRY_DELAY_SECONDS)
    raise RehearsalPersistenceError(
        f"generation finalization rename failed after {_RENAME_RETRY_ATTEMPTS} attempts: {last_exc}"
    )


def read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_pointer_atomic(path: Path, content: dict) -> None:
    write_atomic(path, canonicalize_dict(content))


def read_generation_artifacts(generation_dir: Path) -> dict:
    """Reads every ``*.json`` artifact file (including ``manifest.json``)
    from a finalized generation directory back into memory, for
    verification/reconciliation."""

    out = {}
    if not generation_dir.exists():
        return out
    for path in sorted(generation_dir.glob("*.json")):
        payload = read_json(path)
        if payload is not None:
            out[path.stem] = payload
    return out


__all__ = [
    "DEFAULT_MIGRATION_ROOT",
    "RehearsalPersistenceError",
    "rehearsals_root",
    "candidates_dir",
    "generations_dir",
    "failures_dir",
    "quarantine_dir",
    "pointer_path",
    "rehearsal_evidence_pointer_path",
    "write_candidate_artifact",
    "finalize_generation",
    "read_json",
    "write_pointer_atomic",
    "read_generation_artifacts",
]
