"""Stage 2 atomic rehearsal pointer (135Q §23/§24).

``current-rehearsal`` is a per-transition, non-authoritative pointer,
lexically distinct from every production/Stage-0/Stage-1 pointer
filename. It targets exactly one verified, finalized rehearsal
generation, validated before every atomic replace, and rejects a
dangling, wrong-epoch, wrong-transition, digest-mismatched, or
quarantined target.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pcae.cltr.migration.disclosure import NON_AUTHORITY_DISCLOSURE
from pcae.cltr.migration.rehearsal.models import RehearsalManifest, RehearsalPointer
from pcae.cltr.migration.rehearsal.persistence import generations_dir, pointer_path, read_json, write_pointer_atomic


class PointerRejectedError(ValueError):
    """Fail-closed: every rejection reason is explicit (135Q §23's
    dangling/wrong-epoch/wrong-transition/digest-mismatch/quarantined
    rejection list)."""


def _pointer_content(manifest: RehearsalManifest) -> dict:
    return {
        "rehearsal_generation_id": manifest.rehearsal_generation_id,
        "migration_epoch": manifest.migration_epoch,
        "authority_epoch": manifest.authority_epoch,
        "transition_id": manifest.transition_id,
        "generation_digest": manifest.generation_digest,
        "non_authority_disclosure": dict(NON_AUTHORITY_DISCLOSURE),
    }


def validate_publication_target(
    *, migration_root: Path, manifest: RehearsalManifest, is_quarantined: bool
) -> None:
    if is_quarantined:
        raise PointerRejectedError("refusing to publish a quarantined generation as current-rehearsal")
    generation_dir = generations_dir(
        migration_root, manifest.migration_epoch, manifest.transition_id, manifest.rehearsal_generation_id
    )
    if not generation_dir.exists():
        raise PointerRejectedError(f"dangling target: generation directory does not exist: {generation_dir}")
    manifest_on_disk = read_json(generation_dir / "manifest.json")
    if manifest_on_disk is None:
        raise PointerRejectedError("dangling target: finalized generation has no manifest.json")
    if manifest_on_disk.get("generation_digest") != manifest.generation_digest:
        raise PointerRejectedError("digest mismatch between manifest argument and on-disk finalized generation")


def publish(*, migration_root: Path, manifest: RehearsalManifest, is_quarantined: bool = False) -> RehearsalPointer:
    validate_publication_target(migration_root=migration_root, manifest=manifest, is_quarantined=is_quarantined)
    path = pointer_path(migration_root, manifest.migration_epoch, manifest.transition_id)
    content = _pointer_content(manifest)
    write_pointer_atomic(path, content)
    return RehearsalPointer(
        rehearsal_generation_id=manifest.rehearsal_generation_id,
        migration_epoch=manifest.migration_epoch,
        authority_epoch=manifest.authority_epoch,
        transition_id=manifest.transition_id,
        generation_digest=manifest.generation_digest,
        non_authority_disclosure=dict(NON_AUTHORITY_DISCLOSURE),
    )


def read_pointer(migration_root: Path, migration_epoch: str, transition_id: str) -> Optional[dict]:
    return read_json(pointer_path(migration_root, migration_epoch, transition_id))


def verify_published_target(migration_root: Path, migration_epoch: str, transition_id: str, expected_generation_id: str) -> bool:
    """135Q §20 step 17 -- post-publication readback: confirm the pointer
    resolves to the just-finalized generation. Returns ``True`` only on
    an unambiguous match; the caller treats any other outcome as
    uncertain (135Q §26/§27), never as a silent success."""

    content = read_pointer(migration_root, migration_epoch, transition_id)
    if content is None:
        return False
    return content.get("rehearsal_generation_id") == expected_generation_id
