"""Stage 1 migration evidence persistence — dedicated non-authoritative
namespace, containment-checked, atomic, immutable (phase brief §23-§24).

Layout::

    .pcae/cltr-migration/
      epochs/<migration-epoch>/
        transitions/<transition-id>/
          inputs/<revision>.json
          derivations/legacy.json
          derivations/cltr.json
          comparisons/comparison.json
          evidence/evidence.json
          failures/<uuid>.json
      transition-ids/<phase_id>__<entry_point>.json
      status/current-evidence

This mirrors ``pcae.cltr.persistence``'s containment/atomicity discipline
(``_is_safe_segment``, ``_write_atomic``/``os.replace``) but lives in an
entirely separate root so migration evidence is never mixed with the
shadow generation store or any authoritative promoted-report storage.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

DEFAULT_MIGRATION_ROOT = Path(".pcae/cltr-migration")

NON_AUTHORITY_DISCLOSURE = {
    "migration_evidence_only": True,
    "authoritative": False,
    "authority_cutover": False,
    "execution_capability": False,
}


class PathContainmentError(ValueError):
    pass


def is_safe_segment(name: str) -> bool:
    if not name or not isinstance(name, str) or not name.isascii():
        return False
    if name in (".", ".."):
        return False
    if "/" in name or "\\" in name:
        return False
    if name.startswith("."):
        return False
    return True


def _resolved_root(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def safe_join(root: Path, *segments: str) -> Path:
    """Containment-checked path join. Never follows a symlink placed at
    any segment position; refuses any segment that resolves outside
    ``root``."""

    resolved_root = _resolved_root(root)
    candidate = resolved_root
    for segment in segments:
        if not is_safe_segment(segment):
            raise PathContainmentError(f"unsafe path segment: {segment!r}")
        candidate = candidate / segment
    for parent in [candidate, *candidate.parents]:
        if parent == resolved_root:
            break
        if parent.is_symlink():
            raise PathContainmentError(f"path component is a symlink, refusing: {parent}")
    return candidate


def write_atomic(path: Path, data: bytes) -> None:
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_immutable(path: Path, data: bytes) -> bool:
    """Writes only if the target does not already exist (or exists with
    byte-identical content). Returns True if written or already
    byte-identical; raises if the target exists with *different* content
    (never a silent overwrite of immutable evidence)."""

    if path.exists():
        if path.read_bytes() == data:
            return True
        raise ValueError(f"refusing to overwrite immutable evidence with different content: {path}")
    write_atomic(path, data)
    return True


def read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def transition_dir(migration_root: Path, migration_epoch: str, transition_id: str) -> Path:
    return safe_join(migration_root, "epochs", migration_epoch, "transitions", transition_id)


def transition_ids_registry_path(migration_root: Path, phase_id: str, entry_point: str) -> Path:
    root = _resolved_root(migration_root)
    registry_dir = root / "transition-ids"
    registry_dir.mkdir(parents=True, exist_ok=True)
    name = f"{phase_id}__{entry_point}.json"
    if not is_safe_segment(name):
        raise PathContainmentError(f"unsafe transition-id registry key: {name!r}")
    return registry_dir / name


def timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.gmtime())


def new_uuid() -> str:
    return uuid.uuid4().hex
