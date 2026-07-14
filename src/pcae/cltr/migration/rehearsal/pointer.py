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
from pcae.cltr.migration.persistence import PathContainmentError
from pcae.cltr.migration.rehearsal.models import RehearsalManifest, RehearsalPointer
from pcae.cltr.migration.rehearsal.persistence import generations_dir, pointer_path, read_json, write_pointer_atomic


class PointerRejectedError(ValueError):
    """Fail-closed: every rejection reason is explicit (135Q §23's
    dangling/wrong-epoch/wrong-transition/digest-mismatch/quarantined
    rejection list)."""


def _pointer_content(
    *, rehearsal_generation_id: str, migration_epoch: str, authority_epoch: str, transition_id: str, generation_digest: str
) -> dict:
    return {
        "rehearsal_generation_id": rehearsal_generation_id,
        "migration_epoch": migration_epoch,
        "authority_epoch": authority_epoch,
        "transition_id": transition_id,
        "generation_digest": generation_digest,
        "non_authority_disclosure": dict(NON_AUTHORITY_DISCLOSURE),
    }


def validate_generation_target(
    *,
    migration_root: Path,
    migration_epoch: str,
    transition_id: str,
    rehearsal_generation_id: str,
    generation_digest: str,
    is_quarantined: bool,
) -> dict:
    """Shared containment/verification check for any pointer write
    targeting a finalized generation -- used by both ordinary forward
    publication (``publish``) and rollback-rehearsal publication
    (``publish_generation``, 135U), so both paths reject a dangling,
    quarantined, or digest-mismatched target identically. Returns the
    verified on-disk manifest dict."""

    if is_quarantined:
        raise PointerRejectedError("refusing to publish a quarantined generation as current-rehearsal")
    generation_dir = generations_dir(migration_root, migration_epoch, transition_id, rehearsal_generation_id)
    if generation_dir.is_symlink():
        raise PathContainmentError(f"refusing to treat a symlinked path as a rehearsal generation: {generation_dir}")
    if not generation_dir.exists():
        raise PointerRejectedError(f"dangling target: generation directory does not exist: {generation_dir}")
    manifest_on_disk = read_json(generation_dir / "manifest.json")
    if manifest_on_disk is None:
        raise PointerRejectedError("dangling target: finalized generation has no manifest.json")
    if manifest_on_disk.get("generation_digest") != generation_digest:
        raise PointerRejectedError("digest mismatch between expected digest and on-disk finalized generation")
    if manifest_on_disk.get("migration_epoch") != migration_epoch or manifest_on_disk.get("transition_id") != transition_id:
        raise PointerRejectedError("target generation is bound to a different migration_epoch/transition_id")
    return manifest_on_disk


def validate_publication_target(
    *, migration_root: Path, manifest: RehearsalManifest, is_quarantined: bool
) -> None:
    validate_generation_target(
        migration_root=migration_root,
        migration_epoch=manifest.migration_epoch,
        transition_id=manifest.transition_id,
        rehearsal_generation_id=manifest.rehearsal_generation_id,
        generation_digest=manifest.generation_digest,
        is_quarantined=is_quarantined,
    )


def publish(*, migration_root: Path, manifest: RehearsalManifest, is_quarantined: bool = False) -> RehearsalPointer:
    validate_publication_target(migration_root=migration_root, manifest=manifest, is_quarantined=is_quarantined)
    path = pointer_path(migration_root, manifest.migration_epoch, manifest.transition_id)
    content = _pointer_content(
        rehearsal_generation_id=manifest.rehearsal_generation_id,
        migration_epoch=manifest.migration_epoch,
        authority_epoch=manifest.authority_epoch,
        transition_id=manifest.transition_id,
        generation_digest=manifest.generation_digest,
    )
    write_pointer_atomic(path, content)
    return RehearsalPointer(
        rehearsal_generation_id=manifest.rehearsal_generation_id,
        migration_epoch=manifest.migration_epoch,
        authority_epoch=manifest.authority_epoch,
        transition_id=manifest.transition_id,
        generation_digest=manifest.generation_digest,
        non_authority_disclosure=dict(NON_AUTHORITY_DISCLOSURE),
    )


def publish_generation(
    *,
    migration_root: Path,
    migration_epoch: str,
    authority_epoch: str,
    transition_id: str,
    rehearsal_generation_id: str,
    generation_digest: str,
    is_quarantined: bool = False,
) -> RehearsalPointer:
    """135U -- rollback-rehearsal atomic pointer replacement. Targets an
    *existing*, already-finalized generation by ID/digest rather than a
    freshly-built ``RehearsalManifest`` (135Q §36's "explicit, atomic
    replace targeting an older ``generations/<id>/`` entry, using the
    same §23 pointer contract"). Reuses ``validate_generation_target``,
    the identical containment/verification path ``publish`` uses, so a
    rollback target is held to exactly the same dangling/quarantined/
    digest-mismatch/wrong-epoch/wrong-transition rejection rules as an
    ordinary forward publication."""

    validate_generation_target(
        migration_root=migration_root,
        migration_epoch=migration_epoch,
        transition_id=transition_id,
        rehearsal_generation_id=rehearsal_generation_id,
        generation_digest=generation_digest,
        is_quarantined=is_quarantined,
    )
    path = pointer_path(migration_root, migration_epoch, transition_id)
    content = _pointer_content(
        rehearsal_generation_id=rehearsal_generation_id,
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        transition_id=transition_id,
        generation_digest=generation_digest,
    )
    write_pointer_atomic(path, content)
    return RehearsalPointer(
        rehearsal_generation_id=rehearsal_generation_id,
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        transition_id=transition_id,
        generation_digest=generation_digest,
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
