"""Read-only cross-representation comparator (135E §14, §26 Stage 5).

Compares a candidate record against the 15 comparison targets named by
135D §9 rows 2-16. Strictly read-only: never writes to any compared target,
returns a `ComparisonReport` value object only.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from pcae.cltr_prototype import compatibility
from pcae.cltr_prototype.models import ConformanceClassification, RepresentationKind, TransitionRecord


class MixedGenerationError(Exception):
    pass


@dataclass(frozen=True)
class TargetComparisonResult:
    kind: str
    source: str
    classification: str
    disclosed_identity: dict
    missing_fields: tuple
    limitation: Optional[str]
    quarantine_recommended: bool


@dataclass(frozen=True)
class ComparisonReport:
    transition_id: str
    phase_id: str
    target_results: tuple
    mixed_generation_detected: bool
    mixed_generation_detail: Optional[str]


_FILE_BACKED_KINDS = {
    RepresentationKind.CANONICAL_REPORT.value: "canonical_report",
    RepresentationKind.COMPLETION_METADATA.value: "completion_metadata",
    RepresentationKind.CHECKPOINT.value: "checkpoint",
    RepresentationKind.COMPLETION_MARKER.value: "marker",
    RepresentationKind.FINALIZATION_RECEIPT.value: "receipt",
    RepresentationKind.PROMOTED_REPORT.value: "canonical_report",
    RepresentationKind.PROMOTED_METADATA.value: "completion_metadata",
}


def compare(record: TransitionRecord, targets: dict) -> ComparisonReport:
    """Compare `record` against `targets`, a dict of
    `{RepresentationKind.value: <path-or-dict>}`.

    A path value is read via `compatibility.classify_legacy_artifact`
    (file-backed targets). A dict value is compared directly against the
    record's identity fields (in-memory targets — e.g. a fixture-supplied
    Architecture Status projection or notification payload). Never writes
    to any target; never scans a directory for targets not explicitly named.
    """

    declared_identity = dataclasses.asdict(record.identity)
    results = []
    seen_transition_ids = set()

    for kind, target in targets.items():
        if kind in _FILE_BACKED_KINDS and isinstance(target, (str, Path)):
            compat = compatibility.classify_legacy_artifact(Path(target), _FILE_BACKED_KINDS[kind], declared_identity=declared_identity)
            results.append(
                TargetComparisonResult(
                    kind=kind,
                    source=str(target),
                    classification=compat.classification,
                    disclosed_identity=compat.disclosed_identity,
                    missing_fields=compat.missing_fields,
                    limitation=compat.limitation,
                    quarantine_recommended=compat.classification == ConformanceClassification.CONFLICTING.value,
                )
            )
            if "transition_id" in compat.disclosed_identity:
                seen_transition_ids.add(compat.disclosed_identity["transition_id"])
            continue

        if isinstance(target, dict):
            target_transition_id = target.get("transition_id")
            if target_transition_id is not None:
                seen_transition_ids.add(target_transition_id)
            if target_transition_id is not None and target_transition_id != record.identity.transition_id:
                results.append(
                    TargetComparisonResult(
                        kind=kind,
                        source="<inline>",
                        classification=ConformanceClassification.CONFLICTING.value,
                        disclosed_identity={"transition_id": target_transition_id},
                        missing_fields=(),
                        limitation=f"target transition_id={target_transition_id!r} disagrees with record transition_id={record.identity.transition_id!r}",
                        quarantine_recommended=True,
                    )
                )
                continue
            results.append(
                TargetComparisonResult(
                    kind=kind,
                    source="<inline>",
                    classification=ConformanceClassification.CONFORMANT.value,
                    disclosed_identity={k: v for k, v in target.items() if k in ("transition_id", "phase_id")},
                    missing_fields=(),
                    limitation=None,
                    quarantine_recommended=False,
                )
            )
            continue

        results.append(
            TargetComparisonResult(
                kind=kind,
                source=str(target),
                classification=ConformanceClassification.UNVERIFIABLE.value,
                disclosed_identity={},
                missing_fields=(),
                limitation="target is neither a recognized file path nor an inline dict",
                quarantine_recommended=False,
            )
        )

    mixed = len(seen_transition_ids) > 1
    mixed_detail = None
    if mixed:
        mixed_detail = f"comparison targets disagree on transition_id: {sorted(seen_transition_ids)}"

    return ComparisonReport(
        transition_id=record.identity.transition_id,
        phase_id=record.identity.phase_id,
        target_results=tuple(results),
        mixed_generation_detected=mixed,
        mixed_generation_detail=mixed_detail,
    )
