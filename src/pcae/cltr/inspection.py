"""Read-only shadow inspection and reconciliation (phase 135K brief §30-§31).

Every function here is strictly read-only: no generation is created, no
pointer is repaired, no shadow integration is replayed, no lifecycle state
is mutated, no report is promoted, no notification is dispatched, no
marker or receipt is created. ``mutation: "none"`` is included in every
returned payload as a machine-readable disclosure.
"""

from __future__ import annotations

from pcae.cltr.persistence import (
    DEFAULT_SHADOW_ROOT,
    GenerationNotFoundError,
    list_generations,
    read_current_generation,
    read_current_pointer,
    read_generation,
)

NON_AUTHORITY_DISCLOSURE = {
    "shadow_mode": True,
    "authoritative": False,
    "mutation": "none",
    "authority_cutover": False,
}


def show_latest(shadow_root=DEFAULT_SHADOW_ROOT) -> dict:
    generation = read_current_generation(shadow_root)
    if generation is None:
        return {"found": False, **NON_AUTHORITY_DISCLOSURE}
    return {"found": True, **generation, **NON_AUTHORITY_DISCLOSURE}


def show_phase(phase_id: str, shadow_root=DEFAULT_SHADOW_ROOT) -> dict:
    try:
        generation = read_generation(shadow_root, phase_id)
    except GenerationNotFoundError:
        return {"found": False, "phase_id": phase_id, **NON_AUTHORITY_DISCLOSURE}
    return {"found": True, **generation, **NON_AUTHORITY_DISCLOSURE}


def verify_latest(shadow_root=DEFAULT_SHADOW_ROOT) -> dict:
    from pcae.cltr.digest import compute_dict_digest

    pointer = read_current_pointer(shadow_root)
    if pointer is None:
        return {"verified": False, "reason": "no current pointer", **NON_AUTHORITY_DISCLOSURE}
    generation = read_current_generation(shadow_root)
    if generation is None:
        return {"verified": False, "reason": "pointer does not resolve to a complete, digest-matching generation", **NON_AUTHORITY_DISCLOSURE}
    manifest = dict(generation["manifest"])
    stored_manifest_digest = manifest.pop("manifest_digest", None)
    recomputed = compute_dict_digest(manifest)
    manifest_ok = recomputed == stored_manifest_digest
    return {
        "verified": manifest_ok,
        "transition_id": generation["manifest"].get("transition_id"),
        "record_digest": generation["manifest"].get("record_digest"),
        "manifest_digest_matches": manifest_ok,
        **NON_AUTHORITY_DISCLOSURE,
    }


def list_shadow_generations(limit: int | None = None, shadow_root=DEFAULT_SHADOW_ROOT) -> dict:
    names = list_generations(shadow_root, limit=limit)
    return {"generations": names, "count": len(names), **NON_AUTHORITY_DISCLOSURE}


def reconcile(phase_id: str, shadow_root=DEFAULT_SHADOW_ROOT) -> dict:
    """135K brief §30 — inspects and reports; never repairs, replays,
    mutates, promotes, dispatches, or creates markers/receipts."""

    try:
        generation = read_generation(shadow_root, phase_id)
    except GenerationNotFoundError:
        return {
            "phase_id": phase_id,
            "generation_found": False,
            "blockers": ["no shadow generation exists for this phase_id"],
            **NON_AUTHORITY_DISCLOSURE,
        }

    record = generation["record"]
    manifest = generation["manifest"]
    pointer = read_current_pointer(shadow_root)
    pointer_matches = bool(pointer) and pointer.get("transition_id") == phase_id

    blockers = []
    if record.get("record_digest") != manifest.get("record_digest"):
        blockers.append("record.record_digest disagrees with manifest.record_digest")
    if not pointer:
        blockers.append("no current pointer is published")
    elif not pointer_matches:
        blockers.append("current pointer references a different generation")

    return {
        "phase_id": phase_id,
        "generation_found": True,
        "lifecycle_state": record.get("lifecycle_state"),
        "transition_type": record.get("transition_type"),
        "record_digest": record.get("record_digest"),
        "manifest_valid": manifest.get("record_digest") == record.get("record_digest"),
        "pointer_valid": pointer_matches,
        "blockers": blockers,
        "generation_count": len(list_generations(shadow_root)),
        **NON_AUTHORITY_DISCLOSURE,
    }
