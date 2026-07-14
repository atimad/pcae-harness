"""``transition_id`` design B (135M §8.3, resolved by 135N; verbatim
quote reproduced below for implementation fidelity).

135N's resolution (135M §8.3, "Resolved by Phase 135N"):

    "design (b) is selected -- an independently generated transition_id
    (e.g., a UUID4 or another opaque, sortable identifier; the exact
    generation function is 135O's implementation choice), with phase_id
    remaining a permanently separate, always-present field. Design (a)
    was rejected because it requires a new durable per-(phase_id,
    entry_point) attempt-sequence counter as additional migration state
    whose own consistency would itself need protecting [...]"

Binding guarantee (135M §8.3, still-binding paragraph): "two distinct
finalization attempts for the same phase_id never produce colliding
transition_id values, and a superseding correction is always modeled as
predecessor_transition_id/successor_transition_id [...], never as an
overwrite."

This module generates a UUID4 ``transition_id`` (never derived from
title, git, timestamp alone, or repository HEAD), and keeps it *stable*
across ordinary retries of the same logical transition (same
``phase_id``/``entry_point``/``migration_epoch``/``source_revision``) via
a durable per-``(phase_id, entry_point)`` registry entry -- satisfying
retry stability and replay detection without the rejected design (a)'s
attempt-sequence counter: the registry stores only the *current* key and
id for that (phase_id, entry_point) pair, and a changed logical key
(different ``source_revision`` -- a genuinely new attempt) produces a new
id explicitly linked via ``predecessor_transition_id``, never an
overwrite of the prior id's own evidence.
"""

from __future__ import annotations

import dataclasses
import uuid

from pcae.cltr.digest import compute_dict_digest
from pcae.cltr.migration.persistence import (
    DEFAULT_MIGRATION_ROOT,
    read_json,
    transition_ids_registry_path,
    write_atomic,
)


@dataclasses.dataclass(frozen=True)
class TransitionIdentity:
    transition_id: str
    predecessor_transition_id: str | None
    replay: bool  # True when this call returned a previously-resolved id for an unchanged key


def _logical_key(*, phase_id: str, entry_point: str, migration_epoch: str, source_revision: str) -> str:
    return compute_dict_digest(
        {
            "phase_id": phase_id,
            "entry_point": entry_point,
            "migration_epoch": migration_epoch,
            "source_revision": source_revision,
        }
    )


def resolve_transition_id(
    *,
    phase_id: str,
    entry_point: str,
    migration_epoch: str,
    source_revision: str,
    migration_root=DEFAULT_MIGRATION_ROOT,
) -> TransitionIdentity:
    if not phase_id or not entry_point or not migration_epoch or not source_revision:
        raise ValueError(
            "resolve_transition_id requires non-empty phase_id, entry_point, migration_epoch, "
            "and source_revision -- no field is inferred from title, git, or repository HEAD"
        )

    key = _logical_key(
        phase_id=phase_id, entry_point=entry_point, migration_epoch=migration_epoch, source_revision=source_revision
    )
    registry_path = transition_ids_registry_path(migration_root, phase_id, entry_point)
    existing = read_json(registry_path)

    if existing is not None and existing.get("logical_key") == key:
        return TransitionIdentity(
            transition_id=existing["transition_id"],
            predecessor_transition_id=existing.get("predecessor_transition_id"),
            replay=True,
        )

    predecessor = existing.get("transition_id") if existing is not None else None
    new_id = str(uuid.uuid4())
    payload = {
        "logical_key": key,
        "transition_id": new_id,
        "predecessor_transition_id": predecessor,
        "phase_id": phase_id,
        "entry_point": entry_point,
        "migration_epoch": migration_epoch,
    }
    write_atomic(registry_path, _canonical(payload))
    return TransitionIdentity(transition_id=new_id, predecessor_transition_id=predecessor, replay=False)


def _canonical(payload: dict) -> bytes:
    from pcae.cltr.canonicalization import canonicalize_dict

    return canonicalize_dict(payload)
