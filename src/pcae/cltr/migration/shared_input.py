"""One shared, immutable transition-input package (phase brief §6-§9).

Deeply immutable: nested dict/list values are frozen the same way
``pcae.cltr.models`` freezes ``ProductionCltrRecord`` (``MappingProxyType``
+ tuple recursively), so a caller cannot mutate a revision's ``fields``
or ``provenance`` mapping after construction, after digesting, after
derivation, or after persistence.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType
from typing import Any, Optional

from pcae.cltr.digest import compute_dict_digest
from pcae.cltr.migration.enums import InputStage


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({k: _deep_freeze(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_deep_freeze(v) for v in value)
    return value


@dataclasses.dataclass(frozen=True)
class FieldProvenance:
    source_component: str
    source_authority: str
    observation_stage: InputStage
    verification_state: str
    source_artifact_identity: Optional[str] = None
    source_field: Optional[str] = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "limitations", tuple(self.limitations))


@dataclasses.dataclass(frozen=True)
class SharedInputRevision:
    package_id: str
    stage: InputStage
    revision: int
    predecessor_digest: Optional[str]
    fields: MappingProxyType
    provenance: MappingProxyType  # field name -> FieldProvenance
    newly_available_fields: tuple[str, ...]
    created_reason: str
    limitations: tuple[str, ...] = ()
    revision_digest: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "fields", _deep_freeze(dict(self.fields)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))
        object.__setattr__(self, "newly_available_fields", tuple(self.newly_available_fields))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def with_digest(self, digest: str) -> "SharedInputRevision":
        return dataclasses.replace(self, revision_digest=digest)

    def digestible_payload(self) -> dict:
        return {
            "package_id": self.package_id,
            "stage": self.stage.value,
            "revision": self.revision,
            "predecessor_digest": self.predecessor_digest,
            "fields": dict(self.fields),
            "newly_available_fields": list(self.newly_available_fields),
            "created_reason": self.created_reason,
            "limitations": list(self.limitations),
        }


def compute_revision_digest(revision: SharedInputRevision) -> str:
    return compute_dict_digest(revision.digestible_payload())


@dataclasses.dataclass(frozen=True)
class SharedTransitionInputPackage:
    package_id: str
    migration_epoch: str
    authority_epoch: str
    phase_id: str
    entry_point: str
    transition_id: str
    predecessor_transition_id: Optional[str]
    revisions: tuple[SharedInputRevision, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "revisions", tuple(self.revisions))

    @property
    def latest(self) -> SharedInputRevision:
        return self.revisions[-1]

    def field(self, name: str, default: Any = None) -> Any:
        for revision in reversed(self.revisions):
            if name in revision.fields:
                return revision.fields[name]
        return default

    def with_revision(self, revision: SharedInputRevision) -> "SharedTransitionInputPackage":
        return dataclasses.replace(self, revisions=(*self.revisions, revision))


def compute_package_id(
    *, migration_epoch: str, authority_epoch: str, phase_id: str, transition_id: str, entry_point: str,
    predecessor_transition_id: Optional[str],
) -> str:
    return compute_dict_digest(
        {
            "migration_epoch": migration_epoch,
            "authority_epoch": authority_epoch,
            "phase_id": phase_id,
            "transition_id": transition_id,
            "entry_point": entry_point,
            "predecessor_transition_id": predecessor_transition_id,
        }
    )
