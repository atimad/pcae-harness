"""Stage 1 legacy derivation adapter (phase brief §13).

Normalizes the shared transition-input package's already-known fields
into a deterministic migration-comparison representation. Never
re-invokes report promotion, notification, checkpoint creation, marker
creation, receipt finalization, or task completion -- it only reads
values legacy's own already-completed finalization path put into the
shared input package.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType
from typing import Optional

from pcae.cltr.digest import compute_dict_digest
from pcae.cltr.migration.enums import InputStage
from pcae.cltr.migration.shared_input import SharedTransitionInputPackage

_COMPARABLE_FIELDS = (
    "phase_id",
    "task_id",
    "entry_point",
    "transition_id",
    "predecessor_transition_id",
    "source_revision",
    "staged_final_revision",
    "phase_commit_ownership",
    "intended_transition",
    "recovery_classification",
    "transition_type",
    "lifecycle_state",
    "report_id",
    "report_digest",
    "metadata_id",
    "checkpoint_id",
    "promotion_id",
    "notification_ids",
    "notification_state",
    "notification_suppressed",
    "marker_id",
    "receipt_id",
)


@dataclasses.dataclass(frozen=True)
class LegacyDerivationResult:
    transition_id: str
    input_revision_digest: Optional[str]
    fields: MappingProxyType
    authority_role: str
    limitations: tuple[str, ...]
    derivation_digest: Optional[str] = None

    def with_digest(self, digest: str) -> "LegacyDerivationResult":
        return dataclasses.replace(self, derivation_digest=digest)


#: Fields that live on the package/identity object itself rather than in
#: any revision's ``fields`` dict.
_PACKAGE_LEVEL_FIELDS = {"transition_id", "predecessor_transition_id"}


def derive_legacy(package: SharedTransitionInputPackage) -> LegacyDerivationResult:
    fields: dict = {}
    limitations: list[str] = []
    for name in _COMPARABLE_FIELDS:
        if name in _PACKAGE_LEVEL_FIELDS:
            fields[name] = getattr(package, name)
            continue
        if any(name in revision.fields for revision in package.revisions):
            fields[name] = package.field(name)
        else:
            limitations.append(f"field {name!r} not yet available at this revision")

    consumed_completion = any(r.stage == InputStage.LEGACY_COMPLETION for r in package.revisions)
    if not consumed_completion:
        limitations.append("legacy-completion revision not yet enriched: terminal fields are unresolved")

    result = LegacyDerivationResult(
        transition_id=package.transition_id,
        input_revision_digest=package.latest.revision_digest,
        fields=MappingProxyType(dict(sorted(fields.items()))),
        authority_role="legacy",
        limitations=tuple(limitations),
    )
    digest = compute_dict_digest(
        {
            "transition_id": result.transition_id,
            "input_revision_digest": result.input_revision_digest,
            "fields": dict(result.fields),
            "authority_role": result.authority_role,
        }
    )
    return result.with_digest(digest)
