"""Prototype-only atomic persistence under `.pcae/cltr-prototypes/` (135E §15).

Layout:
    .pcae/cltr-prototypes/
      generations/
        <transition-id>/
          record.json
          verification.json
          manifest.json
      latest.json          # {"<phase_id>": {"transition_id", "digest", "written_at"}}

This module is the *only* module in this package with write capability, and
its write path is hardcoded to the prototype prefix above — no caller can
supply a different output path. No production canonical path
(`.pcae/canonical-reports/`, `.pcae/phase-completion-metadata.json`,
`.pcae/finalization-transactions/`, `.pcae/delivery-receipts/`,
`.pcae/phase-completion-report.md`) is ever written by this module.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from pcae.cltr_prototype.canonicalization import record_to_dict
from pcae.cltr_prototype.digest import verify_self
from pcae.cltr_prototype.invariants import InvariantResult
from pcae.cltr_prototype.models import TransitionRecord

PROTOTYPE_DIR_NAME = ".pcae/cltr-prototypes"


class PointerCorruptError(Exception):
    pass


class PartialWriteError(Exception):
    pass


class ImmutableGenerationExistsError(Exception):
    pass


def _prototype_root(base_dir: Optional[Path] = None) -> Path:
    if base_dir is not None:
        return Path(base_dir)
    return Path.cwd() / PROTOTYPE_DIR_NAME


def _generations_dir(base_dir: Optional[Path] = None) -> Path:
    return _prototype_root(base_dir) / "generations"


def _latest_path(base_dir: Optional[Path] = None) -> Path:
    return _prototype_root(base_dir) / "latest.json"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _invariant_result_to_dict(r: InvariantResult) -> dict:
    d = asdict(r)
    d["outcome"] = r.outcome.value
    return d


def persist(
    record: TransitionRecord,
    invariant_results: list,
    *,
    base_dir: Optional[Path] = None,
    written_at: Optional[str] = None,
) -> Path:
    """Atomically write one immutable generation directory and update the
    per-phase `latest.json` pointer. Returns the generation directory path.

    A re-run for the same `transition_id` either no-ops (if content is
    identical, idempotent per 135E §9) or raises `ImmutableGenerationExistsError`
    (conflicting replay — different content for the same transition_id,
    never silently overwritten in place, 135E §15).
    """

    transition_id = record.identity.transition_id
    phase_id = record.identity.phase_id
    gen_dir = _generations_dir(base_dir) / transition_id

    record_bytes = json.dumps(record_to_dict(record), sort_keys=True, separators=(",", ":")).encode("utf-8")

    if gen_dir.exists():
        existing_record_path = gen_dir / "record.json"
        if existing_record_path.exists():
            existing_bytes = existing_record_path.read_bytes()
            if existing_bytes == record_bytes:
                return gen_dir  # idempotent no-op re-run
            raise ImmutableGenerationExistsError(
                f"generation directory for transition_id={transition_id!r} already exists with different content (conflicting replay)"
            )

    verification_bytes = json.dumps(
        {"invariant_results": [_invariant_result_to_dict(r) for r in invariant_results]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    # Write into a temp staging directory first, then publish record.json and
    # verification.json, then a manifest that references their digests, so a
    # crash between any two files leaves an incomplete (never partial-visible
    # single file) directory a reader can detect via manifest mismatch.
    _atomic_write(gen_dir / "record.json", record_bytes)
    _atomic_write(gen_dir / "verification.json", verification_bytes)

    manifest = {
        "transition_id": transition_id,
        "phase_id": phase_id,
        "written_at": written_at or record.timestamps.get("final") or max(record.timestamps.values(), default=""),
        "files": {
            "record.json": {"digest": _sha256_bytes(record_bytes), "size": len(record_bytes)},
            "verification.json": {"digest": _sha256_bytes(verification_bytes), "size": len(verification_bytes)},
        },
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    _atomic_write(gen_dir / "manifest.json", manifest_bytes)

    _update_latest_pointer(phase_id, transition_id, record.record_digest, manifest["written_at"], base_dir=base_dir)

    return gen_dir


def _update_latest_pointer(phase_id: str, transition_id: str, digest: Optional[str], written_at: str, *, base_dir: Optional[Path] = None) -> None:
    latest_path = _latest_path(base_dir)
    pointer_map = {}
    if latest_path.exists():
        try:
            pointer_map = json.loads(latest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pointer_map = {}
    pointer_map[phase_id] = {"transition_id": transition_id, "digest": digest, "written_at": written_at}
    data = json.dumps(pointer_map, sort_keys=True, separators=(",", ":")).encode("utf-8")
    _atomic_write(latest_path, data)


def _manifest_is_consistent(gen_dir: Path) -> bool:
    manifest_path = gen_dir / "manifest.json"
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    for filename, meta in manifest.get("files", {}).items():
        file_path = gen_dir / filename
        if not file_path.exists():
            return False
        if _sha256_bytes(file_path.read_bytes()) != meta.get("digest"):
            return False
    return True


def _load_record_dict(gen_dir: Path) -> Optional[dict]:
    record_path = gen_dir / "record.json"
    if not record_path.exists():
        return None
    try:
        return json.loads(record_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def list_generations(*, base_dir: Optional[Path] = None) -> list[str]:
    """List transition_ids under `generations/`, complete or not."""

    gens_dir = _generations_dir(base_dir)
    if not gens_dir.exists():
        return []
    return sorted(p.name for p in gens_dir.iterdir() if p.is_dir())


def read_latest(phase_id: str, *, base_dir: Optional[Path] = None) -> Optional[dict]:
    """Read the most recent *complete* generation's record dict for `phase_id`.

    First tries `latest.json`. If it is missing, corrupt, or points at an
    incomplete generation, falls back to scanning `generations/` for the
    most recently written *complete* (manifest-consistent) generation for
    this phase — never a live directory scan of anything outside
    `.pcae/cltr-prototypes/`.
    """

    latest_path = _latest_path(base_dir)
    if latest_path.exists():
        try:
            pointer_map = json.loads(latest_path.read_text(encoding="utf-8"))
            entry = pointer_map.get(phase_id)
            if entry is not None:
                gen_dir = _generations_dir(base_dir) / entry["transition_id"]
                if _manifest_is_consistent(gen_dir):
                    return _load_record_dict(gen_dir)
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    # Fallback: scan generations/ for the most recent complete generation
    # belonging to this phase_id (crash recovery, 135E §15).
    candidates = []
    for transition_id in list_generations(base_dir=base_dir):
        gen_dir = _generations_dir(base_dir) / transition_id
        if not _manifest_is_consistent(gen_dir):
            continue
        record_dict = _load_record_dict(gen_dir)
        if record_dict is None:
            continue
        if record_dict.get("identity", {}).get("phase_id") != phase_id:
            continue
        manifest = json.loads((gen_dir / "manifest.json").read_text(encoding="utf-8"))
        candidates.append((manifest.get("written_at", ""), record_dict))

    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    return candidates[-1][1]


def read_generation(transition_id: str, *, base_dir: Optional[Path] = None) -> Optional[dict]:
    """Read one generation's record dict by transition_id, verifying manifest completeness first."""

    gen_dir = _generations_dir(base_dir) / transition_id
    if not _manifest_is_consistent(gen_dir):
        return None
    return _load_record_dict(gen_dir)
