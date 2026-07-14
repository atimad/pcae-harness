"""Stage 1 deterministic cross-derivation comparison (phase brief §18-§20).

Compares the legacy derivation's normalized fields against the CLTR
derivation's constructed record, field by field, classifying every
comparison into one of 135M §12's exact wire-identifier result classes
(``enums.ComparisonResultClass``). Never compares narrative wording as
semantic equality -- every compared field is an explicit identifier,
digest, enum value, or structured tuple.
"""

from __future__ import annotations

import dataclasses

from pcae.cltr.migration.cltr_derivation import CltrDerivationResult
from pcae.cltr.migration.enums import AUTHORITY_RELEVANT_CLASSES, COMPARISON_RESULT_PRECEDENCE, ComparisonResultClass
from pcae.cltr.migration.legacy_derivation import LegacyDerivationResult

#: Maps a compared field name to the mismatch class it produces when
#: legacy and CLTR disagree. Fields not listed here fall back to
#: ``NON_AUTHORITY_MISMATCH`` (never silently collapsed to a stronger
#: class, and never absent from the comparison).
_MISMATCH_CLASS_FOR_FIELD = {
    "phase_id": ComparisonResultClass.IDENTITY_MISMATCH,
    "task_id": ComparisonResultClass.IDENTITY_MISMATCH,
    "transition_id": ComparisonResultClass.IDENTITY_MISMATCH,
    "predecessor_transition_id": ComparisonResultClass.IDENTITY_MISMATCH,
    "report_id": ComparisonResultClass.IDENTITY_MISMATCH,
    "metadata_id": ComparisonResultClass.IDENTITY_MISMATCH,
    "promotion_id": ComparisonResultClass.IDENTITY_MISMATCH,
    "checkpoint_id": ComparisonResultClass.IDENTITY_MISMATCH,
    "intended_transition": ComparisonResultClass.TRANSITION_MISMATCH,
    "transition_type": ComparisonResultClass.TRANSITION_MISMATCH,
    "lifecycle_state": ComparisonResultClass.STATE_MISMATCH,
    "recovery_classification": ComparisonResultClass.RECOVERY_CLASSIFICATION_MISMATCH,
    "source_revision": ComparisonResultClass.DIGEST_MISMATCH,
    "staged_final_revision": ComparisonResultClass.DIGEST_MISMATCH,
    "report_digest": ComparisonResultClass.DIGEST_MISMATCH,
    "phase_commit_ownership": ComparisonResultClass.COMMIT_OWNERSHIP_MISMATCH,
    "notification_ids": ComparisonResultClass.NOTIFICATION_MISMATCH,
    "notification_state": ComparisonResultClass.NOTIFICATION_MISMATCH,
    "notification_suppressed": ComparisonResultClass.NOTIFICATION_MISMATCH,
    "marker_id": ComparisonResultClass.MARKER_MISMATCH,
    "receipt_id": ComparisonResultClass.RECEIPT_MISMATCH,
}

#: field name -> ProductionCltrRecord attribute path, and whether that
#: attribute is an enum (compared by ``.value``).
#:
#: ``intended_transition`` (a pre-transaction, entry-point-derived label)
#: and ``recovery_classification`` (this package's own richer §25-style
#: vocabulary) are deliberately excluded: neither has a 1:1 counterpart on
#: ``ProductionCltrRecord`` (whose ``transition_type``/``recovery_
#: classification`` are drawn from CLTR-SCHEMA-001's distinct, narrower
#: vocabularies -- the same vocabulary gap 135N's inherited finding
#: F-135N-2-adjacent note already discloses). Comparing them directly
#: would manufacture a spurious ``authority_relevant_mismatch`` for two
#: fields that were never meant to be byte-equal. They remain present in
#: the legacy derivation's fields for evidence/inspection purposes; they
#: are simply not cross-derivation-compared at Stage 1.
_CLTR_FIELD_ACCESSORS = {
    "phase_id": ("phase_id", False),
    "task_id": ("task_id", False),
    "transition_id": ("transition_id", False),
    "predecessor_transition_id": ("predecessor_transition_id", False),
    "report_id": ("report_id", False),
    "metadata_id": ("metadata_id", False),
    "promotion_id": ("promotion_id", False),
    "checkpoint_id": ("checkpoint_id", False),
    "transition_type": ("transition_type", True),
    "lifecycle_state": ("lifecycle_state", True),
    "source_revision": ("source_revision", False),
    "staged_final_revision": ("final_revision", False),
    "report_digest": ("report_digest", False),
    "phase_commit_ownership": ("phase_commit_ownership", False),
    "notification_ids": ("notification_ids", False),
    "notification_state": ("notification_state", True),
    "notification_suppressed": ("notification_suppressed", False),
    "marker_id": ("marker_id", False),
    "receipt_id": ("receipt_id", False),
}


@dataclasses.dataclass(frozen=True)
class FieldComparison:
    field: str
    result_class: ComparisonResultClass
    legacy_value: str | None
    cltr_value: str | None
    detail: str = ""


@dataclasses.dataclass(frozen=True)
class ComparisonResult:
    comparisons: tuple[FieldComparison, ...]
    overall_class: ComparisonResultClass
    authority_relevant_mismatch: bool
    unverifiable: bool


def _normalize(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "value"):
        return str(value.value)
    if isinstance(value, (list, tuple)):
        return str(sorted(str(v) for v in value))
    return str(value)


def compare(legacy: LegacyDerivationResult, cltr: CltrDerivationResult) -> ComparisonResult:
    comparisons: list[FieldComparison] = []

    if cltr.status != "constructed" or cltr.record is None:
        for field_name in legacy.fields:
            comparisons.append(
                FieldComparison(
                    field=field_name,
                    result_class=ComparisonResultClass.UNVERIFIABLE,
                    legacy_value=_normalize(legacy.fields.get(field_name)),
                    cltr_value=None,
                    detail=f"CLTR derivation status={cltr.status!r}: comparison not evaluable",
                )
            )
        return ComparisonResult(
            comparisons=tuple(comparisons),
            overall_class=ComparisonResultClass.UNVERIFIABLE,
            authority_relevant_mismatch=False,
            unverifiable=True,
        )

    record = cltr.record
    for field_name, legacy_value in legacy.fields.items():
        if field_name not in _CLTR_FIELD_ACCESSORS:
            continue
        attr_name, _is_enum = _CLTR_FIELD_ACCESSORS[field_name]
        cltr_value = getattr(record, attr_name, None)

        legacy_norm = _normalize(legacy_value)
        cltr_norm = _normalize(cltr_value)

        if legacy_norm is None and cltr_norm is None:
            result_class = ComparisonResultClass.EXACT_MATCH
        elif legacy_norm is None:
            result_class = ComparisonResultClass.LEGACY_MISSING
        elif cltr_norm is None:
            result_class = ComparisonResultClass.CLTR_MISSING
        elif legacy_norm == cltr_norm:
            result_class = ComparisonResultClass.EXACT_MATCH
        else:
            result_class = _MISMATCH_CLASS_FOR_FIELD.get(field_name, ComparisonResultClass.NON_AUTHORITY_MISMATCH)

        comparisons.append(
            FieldComparison(
                field=field_name,
                result_class=result_class,
                legacy_value=legacy_norm,
                cltr_value=cltr_norm,
                detail="" if result_class == ComparisonResultClass.EXACT_MATCH else "values disagree",
            )
        )

    authority_relevant = any(c.result_class in AUTHORITY_RELEVANT_CLASSES for c in comparisons)
    any_unverifiable = any(c.result_class == ComparisonResultClass.UNVERIFIABLE for c in comparisons)

    if authority_relevant:
        overall = min(
            (c.result_class for c in comparisons if c.result_class in AUTHORITY_RELEVANT_CLASSES),
            key=lambda cls: COMPARISON_RESULT_PRECEDENCE.index(cls),
        )
    elif any_unverifiable:
        overall = ComparisonResultClass.UNVERIFIABLE
    elif any(c.result_class != ComparisonResultClass.EXACT_MATCH for c in comparisons):
        overall = ComparisonResultClass.SEMANTIC_MATCH
    else:
        overall = ComparisonResultClass.EXACT_MATCH

    return ComparisonResult(
        comparisons=tuple(comparisons),
        overall_class=overall,
        authority_relevant_mismatch=authority_relevant,
        unverifiable=any_unverifiable,
    )
