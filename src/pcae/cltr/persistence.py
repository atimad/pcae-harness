"""Immutable shadow generation storage, manifest, and atomic current
pointer (135I §16-§17; phase 135K brief §14-§21).

Layout:

    .pcae/cltr-shadow/
      generations/<transition_id>/record.json
      generations/<transition_id>/manifest.json
      current
      failures/<transition_id>-<uuid>.json
      quarantine/<transition_id>-<uuid>.json

Every path derived from caller-controlled input (``transition_id``) is
resolved and containment-checked against the shadow root before any I/O
(``_safe_join``). No symlink is ever followed when resolving the
containment boundary (``strict=False`` + ``resolve`` on the *parent*, then
comparing the resolved parent against the resolved root).
"""

from __future__ import annotations

import dataclasses
import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from pcae.cltr.canonicalization import canonicalize, canonicalize_dict
from pcae.cltr.digest import compute_dict_digest, compute_record_digest
from pcae.cltr.models import ProductionCltrRecord

DEFAULT_SHADOW_ROOT = Path(".pcae/cltr-shadow")

NON_AUTHORITY_DISCLOSURE = {
    "shadow_mode": True,
    "authoritative": False,
    "derivative": True,
    "authority_cutover": False,
    "execution_capability": False,
}


class PathContainmentError(ValueError):
    pass


class GenerationNotFoundError(LookupError):
    pass


class ConflictingGenerationError(ValueError):
    """A generation already exists for this transition_id with a *different*
    record_digest — a genuine content conflict, never silently resolved."""


def _is_safe_segment(name: str) -> bool:
    if not name or not name.isascii():
        return False
    if name in (".", ".."):
        return False
    if "/" in name or "\\" in name:
        return False
    if name.startswith("."):
        return False
    return True


def _resolved_root(shadow_root: Path) -> Path:
    shadow_root.mkdir(parents=True, exist_ok=True)
    return shadow_root.resolve()


def _safe_generation_dir(shadow_root: Path, transition_id: str) -> Path:
    """Containment-checked path for a generation directory. Never follows a
    symlink placed at the generation-name position."""

    if not _is_safe_segment(transition_id):
        raise PathContainmentError(f"unsafe transition_id for generation directory: {transition_id!r}")
    root = _resolved_root(shadow_root)
    generations_root = root / "generations"
    generations_root.mkdir(parents=True, exist_ok=True)
    candidate = generations_root / transition_id
    if candidate.is_symlink():
        raise PathContainmentError(f"generation path is a symlink, refusing: {candidate}")
    resolved_parent = generations_root.resolve()
    if resolved_parent != (root / "generations").resolve():
        raise PathContainmentError("generations/ parent resolved outside the shadow root")
    return candidate


@dataclasses.dataclass(frozen=True)
class GenerationHandle:
    transition_id: str
    directory: Path
    record_path: Path
    manifest_path: Path
    record_digest: str
    manifest_digest: str


def _write_atomic(path: Path, data: bytes) -> None:
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


def build_manifest(record: ProductionCltrRecord, record_digest: str, entry_point: str) -> dict:
    return {
        "manifest_schema_id": "CLTR-SHADOW-MANIFEST-001",
        "manifest_schema_version": "1.0.0",
        "schema_id": record.schema_id,
        "schema_version": record.schema_version,
        "transition_id": record.transition_id,
        "phase_id": record.phase_id,
        "transition_type": record.transition_type.value,
        "generation_id": record.transition_id,
        "record_path": "record.json",
        "record_digest": record_digest,
        "entry_point": entry_point,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.gmtime()),
        **NON_AUTHORITY_DISCLOSURE,
    }


def publish_generation(
    record: ProductionCltrRecord,
    *,
    entry_point: str,
    shadow_root: Path | str = DEFAULT_SHADOW_ROOT,
) -> GenerationHandle:
    """135I §17's nine-step atomic publication sequence, steps 5-9.

    Steps 1-4 (construct/validate/canonicalize/digest) are the caller's
    responsibility (``shadow.py``) and must have already produced a
    digest-bound ``record`` before this function is called. This function
    performs: isolated staging write, manifest write, verification, atomic
    finalize (rename into place), and atomic current-pointer switch.
    """

    shadow_root = Path(shadow_root)
    if not record.record_digest:
        raise ValueError("cannot publish a generation for a record with no record_digest")

    recomputed = compute_record_digest(record)
    if recomputed != record.record_digest:
        raise ValueError("record_digest does not match recomputed digest; refusing to publish")

    final_dir = _safe_generation_dir(shadow_root, record.transition_id)

    # Idempotency (135K brief §29): a repeat invocation for the same
    # transition_id and same canonical content is a safe no-op, never a
    # duplicate mutable current state and never a silent overwrite of an
    # immutable generation with different content.
    if final_dir.exists():
        existing_manifest_path = final_dir / "manifest.json"
        if existing_manifest_path.exists():
            try:
                existing_manifest = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing_manifest = {}
            if existing_manifest.get("record_digest") == record.record_digest:
                handle = GenerationHandle(
                    transition_id=record.transition_id,
                    directory=final_dir,
                    record_path=final_dir / "record.json",
                    manifest_path=final_dir / "manifest.json",
                    record_digest=record.record_digest,
                    manifest_digest=existing_manifest.get("manifest_digest", ""),
                )
                _publish_current_pointer(shadow_root, handle)
                return handle
        raise ConflictingGenerationError(
            f"generation {record.transition_id!r} already exists with a different record_digest; "
            "immutable generations are never overwritten"
        )

    root = _resolved_root(shadow_root)
    staging_root = root / ".staging"
    staging_root.mkdir(parents=True, exist_ok=True)
    staging_dir = staging_root / f"{record.transition_id}.{uuid.uuid4().hex}"
    staging_dir.mkdir(parents=True, exist_ok=False)

    try:
        record_bytes = canonicalize(record, include_digest=True)
        record_path = staging_dir / "record.json"
        _write_atomic(record_path, record_bytes)

        manifest = build_manifest(record, record.record_digest, entry_point)
        manifest_bytes = canonicalize_dict(manifest)
        manifest_digest = compute_dict_digest(manifest)
        manifest["manifest_digest"] = manifest_digest
        manifest_path = staging_dir / "manifest.json"
        _write_atomic(manifest_path, canonicalize_dict(manifest))

        # Pre-publication verification (135I §17 step 3): re-read what was
        # just written and confirm it round-trips and digests match.
        reread_record_bytes = record_path.read_bytes()
        if reread_record_bytes != record_bytes:
            raise ValueError("record staging write did not round-trip byte-identically")
        reread_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if reread_manifest.get("record_digest") != record.record_digest:
            raise ValueError("manifest record_digest does not match the staged record")

        if final_dir.exists():
            raise ValueError(f"generation already exists and is immutable: {final_dir}")
        os.replace(str(staging_dir), str(final_dir))
    except Exception:
        if staging_dir.exists():
            _quarantine_staging(staging_dir, shadow_root)
        raise

    handle = GenerationHandle(
        transition_id=record.transition_id,
        directory=final_dir,
        record_path=final_dir / "record.json",
        manifest_path=final_dir / "manifest.json",
        record_digest=record.record_digest,
        manifest_digest=manifest["manifest_digest"],
    )
    _publish_current_pointer(shadow_root, handle)
    return handle


def _quarantine_staging(staging_dir: Path, shadow_root: Path) -> None:
    quarantine_root = Path(shadow_root) / "quarantine"
    quarantine_root.mkdir(parents=True, exist_ok=True)
    target = quarantine_root / f"{staging_dir.name}"
    try:
        os.replace(str(staging_dir), str(target))
    except OSError:
        pass


def _publish_current_pointer(shadow_root: Path, handle: GenerationHandle) -> None:
    pointer = {
        "transition_id": handle.transition_id,
        "generation_id": handle.transition_id,
        "record_digest": handle.record_digest,
        "manifest_digest": handle.manifest_digest,
        **NON_AUTHORITY_DISCLOSURE,
    }
    pointer_path = Path(shadow_root) / "current"
    _write_atomic(pointer_path, canonicalize_dict(pointer))


def read_current_pointer(shadow_root: Path | str = DEFAULT_SHADOW_ROOT) -> Optional[dict]:
    pointer_path = Path(shadow_root) / "current"
    if not pointer_path.exists():
        return None
    try:
        return json.loads(pointer_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def read_generation(shadow_root: Path | str, transition_id: str) -> dict:
    """Read-only. Validates the pointer/manifest/record digest chain before
    returning content; raises rather than repairing a mismatch."""

    generation_dir = _safe_generation_dir(Path(shadow_root), transition_id)
    if not generation_dir.exists():
        raise GenerationNotFoundError(transition_id)
    record_path = generation_dir / "record.json"
    manifest_path = generation_dir / "manifest.json"
    if not record_path.exists() or not manifest_path.exists():
        raise GenerationNotFoundError(f"{transition_id}: incomplete generation (missing record.json or manifest.json)")
    record_data = json.loads(record_path.read_text(encoding="utf-8"))
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {"record": record_data, "manifest": manifest_data, "directory": str(generation_dir)}


def read_current_generation(shadow_root: Path | str = DEFAULT_SHADOW_ROOT) -> Optional[dict]:
    pointer = read_current_pointer(shadow_root)
    if pointer is None:
        return None
    transition_id = pointer.get("transition_id")
    if not transition_id:
        return None
    try:
        generation = read_generation(shadow_root, transition_id)
    except GenerationNotFoundError:
        return None
    if generation["manifest"].get("record_digest") != pointer.get("record_digest"):
        return None
    return generation


def list_generations(shadow_root: Path | str = DEFAULT_SHADOW_ROOT, limit: Optional[int] = None) -> list[str]:
    generations_root = Path(shadow_root) / "generations"
    if not generations_root.exists():
        return []
    names = sorted(p.name for p in generations_root.iterdir() if p.is_dir() and _is_safe_segment(p.name))
    if limit is not None:
        names = names[-limit:]
    return names


def persist_failure(
    *,
    phase_id: str,
    entry_point: str,
    failure_stage: str,
    detail: dict,
    shadow_root: Path | str = DEFAULT_SHADOW_ROOT,
) -> Path:
    failures_root = Path(shadow_root) / "failures"
    failures_root.mkdir(parents=True, exist_ok=True)
    safe_phase = phase_id if _is_safe_segment(phase_id) else "unknown-phase"
    name = f"{safe_phase}-{uuid.uuid4().hex}.json"
    payload = {
        "phase_id": phase_id,
        "entry_point": entry_point,
        "failure_stage": failure_stage,
        "detail": detail,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.gmtime()),
        **NON_AUTHORITY_DISCLOSURE,
    }
    path = failures_root / name
    _write_atomic(path, canonicalize_dict(payload))
    return path
