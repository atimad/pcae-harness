"""Read-only Authority Evaluation diagnostic/inspection surface
(AESIC-001 v1.3 §16, AESIC-REQ-097).

Every function here is read-only: none is a control surface, none exposes
a mechanism by which an observer could cause AES to skip resolution, skip
evaluation, or fabricate an outcome (AESIC-REQ-095).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pcae.authority_evaluation.models import EvaluationResult
from pcae.aesic.records import AuthorityEvaluationRecord
from pcae.aesic.storage import AuthorityEvaluationRecordStore


@dataclass(frozen=True)
class AuthorityEvaluationDiagnosticSummary:
    package_id: str
    canonical_record_id: Optional[str]
    canonical_evaluation_result: Optional[str]
    total_attempts: int
    canonical_pointer_ok: bool


def show_evaluations_for_package(
    store: AuthorityEvaluationRecordStore, package_id: str
) -> List[AuthorityEvaluationRecord]:
    """"Show every Stage 2 evaluation for package X" (AESIC-REQ-097)."""

    records = []
    for evaluation_id in store.list_evaluation_ids(package_id):
        record = store.read_record(package_id, evaluation_id)
        if record is not None:
            records.append(record)
    return sorted(records, key=lambda r: r.evaluated_at)


def summarize_package(store: AuthorityEvaluationRecordStore, package_id: str) -> AuthorityEvaluationDiagnosticSummary:
    try:
        attempts = show_evaluations_for_package(store, package_id)
    except Exception:  # noqa: BLE001 -- diagnostics never raise, e.g. an invalid
        # package_id (147P persistence-boundary hardening) is rejected by the
        # store rather than traversed; surfaced here as an empty attempt list.
        attempts = []

    try:
        canonical = store.read_canonical(package_id)
        pointer_ok = True
    except Exception:  # noqa: BLE001 -- diagnostics never raise; surfaced as pointer_ok=False
        canonical = None
        pointer_ok = False

    return AuthorityEvaluationDiagnosticSummary(
        package_id=package_id,
        canonical_record_id=canonical.record_id if canonical is not None else None,
        canonical_evaluation_result=(
            canonical.outcome.evaluation_result.value if canonical is not None else None
        ),
        total_attempts=len(attempts),
        canonical_pointer_ok=pointer_ok,
    )


def show_ineligible_outcomes(
    records: List[AuthorityEvaluationRecord], limit: int
) -> List[AuthorityEvaluationRecord]:
    """"Show every INELIGIBLE outcome in the last N attempts" (AESIC-REQ-097).

    ``records`` is caller-supplied (e.g. the result of iterating multiple
    ``show_evaluations_for_package`` calls) -- this function performs no
    store access of its own beyond what the AER's own already-loaded shape
    (§8.5) provides."""

    recent = records[-limit:] if limit > 0 else records
    return [r for r in recent if r.outcome.evaluation_result is EvaluationResult.INELIGIBLE]


__all__ = [
    "AuthorityEvaluationDiagnosticSummary",
    "show_evaluations_for_package",
    "summarize_package",
    "show_ineligible_outcomes",
]
