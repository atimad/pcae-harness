"""Fifteen representation adapters and cross-representation comparison
(135I §5/§21, 135J §21.4; phase 135K brief §21-§22).

Each adapter receives the constructed shadow record plus an explicit
``AdapterSources`` bundle (the only place live production artifacts are
read from) and returns an ``AdapterResult``. An adapter never infers
equivalence when its declared ``comparison_mode`` cannot be evaluated from
the sources it was given — it returns ``conformance_state=unverifiable``
with an explicit limitation instead (135I §21.2: "never strengthens
authority... never a silent upgrade from unverifiable to a stronger
result").
"""

from __future__ import annotations

import dataclasses
from typing import Callable, Optional

from pcae.cltr.enums import (
    REPRESENTATION_COMPARISON_MODE,
    AdapterComparisonMode,
    ComparisonOutcome,
    ConformanceState,
    RepresentationKind,
)
from pcae.cltr.models import ProductionCltrRecord


@dataclasses.dataclass(frozen=True)
class AdapterSources:
    """Explicit, caller-supplied pointers to the live artifacts an adapter
    may compare against. Every field is optional; an absent field simply
    means that adapter cannot compare (returns unverifiable), never that it
    guesses a substitute."""

    live_report_digest: Optional[str] = None
    live_metadata_digest: Optional[str] = None
    live_snapshot_digest: Optional[str] = None
    live_promoted_report_digest: Optional[str] = None
    live_promoted_metadata_digest: Optional[str] = None
    live_architecture_status: Optional[dict] = None
    live_checkpoint: Optional[dict] = None
    live_notification_result: Optional[dict] = None
    live_marker: Optional[dict] = None
    live_receipt: Optional[dict] = None
    #: Pre-observed live facts, supplied explicitly by the caller (this
    #: package never invokes git/subprocess itself — 135K brief's
    #: no-execution-boundary requirement). The caller (the shared shadow
    #: integration service) may source these from values production
    #: already computed for its own certification/reporting purposes.
    live_head_revision: Optional[str] = None
    live_resolved_commit_hashes: Optional[frozenset] = None


@dataclasses.dataclass(frozen=True)
class AdapterResult:
    representation_kind: RepresentationKind
    comparison_mode: AdapterComparisonMode
    conformance_state: ConformanceState
    outcome: ComparisonOutcome
    detail: str
    limitations: tuple[str, ...] = ()
    source_identity: Optional[str] = None
    authority_role: str = "V"


def _unverifiable(kind: RepresentationKind, detail: str, limitation: str) -> AdapterResult:
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=REPRESENTATION_COMPARISON_MODE[kind],
        conformance_state=ConformanceState.UNVERIFIABLE,
        outcome=ComparisonOutcome.UNVERIFIABLE,
        detail=detail,
        limitations=(limitation,),
    )


def _digest_compare(
    kind: RepresentationKind,
    record_digest: Optional[str],
    live_digest: Optional[str],
    identity: Optional[str],
) -> AdapterResult:
    if not record_digest or not live_digest:
        return _unverifiable(kind, "digest comparison requires both record-side and live-side digests", "one or both digests unavailable")
    conformant = record_digest == live_digest
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.EXACT_IDENTITY_DIGEST,
        conformance_state=ConformanceState.CONFORMANT if conformant else ConformanceState.CONFLICTING,
        outcome=ComparisonOutcome.CONFORMANT if conformant else ComparisonOutcome.INCOMPATIBLE,
        detail="digests match" if conformant else f"digest mismatch: record={record_digest!r} live={live_digest!r}",
        source_identity=identity,
        authority_role="R",
    )


def adapt_canonical_report(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    return _digest_compare(RepresentationKind.CANONICAL_REPORT, record.report_digest, sources.live_report_digest, record.report_id)


def adapt_completion_metadata(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    return _digest_compare(RepresentationKind.COMPLETION_METADATA, record.metadata_digest, sources.live_metadata_digest, record.metadata_id)


def adapt_architecture_status(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.ARCHITECTURE_STATUS
    if sources.live_architecture_status is None:
        return _unverifiable(kind, "no live Architecture Status projection supplied", "architecture_status source not wired")
    expected_state = record.lifecycle_state.value
    observed_state = sources.live_architecture_status.get("lifecycle_state")
    conformant = observed_state == expected_state
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.NORMALIZED_SEMANTIC,
        conformance_state=ConformanceState.CONFORMANT if conformant else ConformanceState.CONFLICTING,
        outcome=ComparisonOutcome.CONFORMANT if conformant else ComparisonOutcome.PARTIALLY_CONFORMANT,
        detail=f"expected lifecycle_state={expected_state!r}, observed={observed_state!r}",
        authority_role="D",
    )


def adapt_immutable_snapshot(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    return _digest_compare(RepresentationKind.IMMUTABLE_SNAPSHOT, record.snapshot_digest, sources.live_snapshot_digest, record.snapshot_id)


def adapt_checkpoint(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.CHECKPOINT
    if sources.live_checkpoint is None:
        return _unverifiable(kind, "no live checkpoint supplied", "checkpoint source not wired")
    observed_phase = sources.live_checkpoint.get("phase_id")
    conformant = observed_phase == record.phase_id
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.NORMALIZED_SEMANTIC,
        conformance_state=ConformanceState.CONFORMANT if conformant else ConformanceState.CONFLICTING,
        outcome=ComparisonOutcome.CONFORMANT if conformant else ComparisonOutcome.INCOMPATIBLE,
        detail=f"expected phase_id={record.phase_id!r}, observed={observed_phase!r}",
        source_identity=record.checkpoint_id,
        authority_role="E",
    )


def adapt_promoted_report(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    return _digest_compare(RepresentationKind.PROMOTED_REPORT, record.report_digest, sources.live_promoted_report_digest, record.report_id)


def adapt_promoted_metadata(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    return _digest_compare(RepresentationKind.PROMOTED_METADATA, record.metadata_digest, sources.live_promoted_metadata_digest, record.metadata_id)


def adapt_notification_payload(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.NOTIFICATION_PAYLOAD
    if sources.live_notification_result is None:
        return _unverifiable(kind, "no live notification_result supplied", "notification_result source not wired")
    observed_success = bool(sources.live_notification_result.get("success"))
    expected_success = record.notification_state.value in ("confirmed",)
    conformant = observed_success == expected_success
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.NORMALIZED_SEMANTIC,
        conformance_state=ConformanceState.CONFORMANT if conformant else ConformanceState.CONFLICTING,
        outcome=ComparisonOutcome.CONFORMANT if conformant else ComparisonOutcome.PARTIALLY_CONFORMANT,
        detail=f"expected success={expected_success}, observed success={observed_success}",
        source_identity=",".join(record.notification_ids) or None,
        authority_role="R",
    )


def adapt_marker(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.MARKER
    if not record.marker_id:
        return AdapterResult(
            representation_kind=kind,
            comparison_mode=AdapterComparisonMode.NORMALIZED_SEMANTIC,
            conformance_state=ConformanceState.INCOMPLETE,
            outcome=ComparisonOutcome.UNVERIFIABLE,
            detail="record declares no marker_id (marker is optional per 135I §5 row 9)",
            limitations=("no marker was ever generated for this transition",),
        )
    if sources.live_marker is None:
        return _unverifiable(kind, "no live marker supplied", "marker source not wired")
    observed_phase = sources.live_marker.get("phase_id")
    conformant = observed_phase == record.phase_id
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.NORMALIZED_SEMANTIC,
        conformance_state=ConformanceState.CONFORMANT if conformant else ConformanceState.CONFLICTING,
        outcome=ComparisonOutcome.CONFORMANT if conformant else ComparisonOutcome.INCOMPATIBLE,
        detail=f"expected phase_id={record.phase_id!r}, observed={observed_phase!r}",
        source_identity=record.marker_id,
        authority_role="D",
    )


def adapt_receipt(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.RECEIPT
    if sources.live_receipt is None:
        return _unverifiable(kind, "no live receipt supplied", "receipt source not wired")
    observed_id = sources.live_receipt.get("logical_delivery_id")
    conformant = bool(observed_id) and observed_id == record.receipt_id
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.NORMALIZED_SEMANTIC,
        conformance_state=ConformanceState.CONFORMANT if conformant else ConformanceState.CONFLICTING,
        outcome=ComparisonOutcome.CONFORMANT if conformant else ComparisonOutcome.INCOMPATIBLE,
        detail=f"expected receipt_id={record.receipt_id!r}, observed={observed_id!r}",
        source_identity=record.receipt_id,
        authority_role="E",
    )


def adapt_repository_transition_view(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.REPOSITORY_TRANSITION_VIEW
    head = sources.live_head_revision
    if head is None:
        return _unverifiable(kind, "no live_head_revision supplied for observation", "repository HEAD observation not wired")
    conformant = record.source_revision == head or record.final_revision == head
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.OBSERVATIONAL,
        conformance_state=ConformanceState.CONFORMANT if conformant else ConformanceState.UNVERIFIABLE,
        outcome=ComparisonOutcome.CONFORMANT if conformant else ComparisonOutcome.UNVERIFIABLE,
        detail=f"live HEAD={head!r}; record source_revision={record.source_revision!r} final_revision={record.final_revision!r} "
        "(a mismatch is expected once further commits land after the transition; this is observational, never retroactively binding)",
        authority_role="V",
    )


def adapt_git_attribution_view(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.GIT_ATTRIBUTION_VIEW
    if sources.live_resolved_commit_hashes is None:
        return _unverifiable(kind, "no live_resolved_commit_hashes supplied for observation", "commit-resolution observation not wired")
    resolved = sources.live_resolved_commit_hashes
    unresolved = [c.commit_hash for c in record.phase_commit_ownership if c.commit_hash not in resolved]
    conformant = not unresolved
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.OBSERVATIONAL,
        conformance_state=ConformanceState.CONFORMANT if conformant else ConformanceState.UNVERIFIABLE,
        outcome=ComparisonOutcome.CONFORMANT if conformant else ComparisonOutcome.UNVERIFIABLE,
        detail="all declared commit hashes resolve in the live repository" if conformant else f"unresolved declared hash(es): {unresolved}",
        authority_role="V",
    )


def adapt_compatibility_view(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.COMPATIBILITY_VIEW
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.NORMALIZED_SEMANTIC,
        conformance_state=ConformanceState.CONFORMANT_WITH_LEGACY_ADAPTER,
        outcome=ComparisonOutcome.UNVERIFIABLE,
        detail="no compatibility/legacy-format adapter invocation occurred for this transition",
        limitations=("compatibility adapter only produced when explicitly invoked; not applicable to ordinary shadow observation (135I §5 row 13)",),
        authority_role="D",
    )


def adapt_diagnostic_envelope(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.DIAGNOSTIC_ENVELOPE
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.PRESENTATION_ONLY,
        conformance_state=ConformanceState.CONFORMANT,
        outcome=ComparisonOutcome.CONFORMANT,
        detail="presentation-only: no independently checkable content per 135I §21.1's own definition",
        authority_role="D",
    )


def adapt_reconciliation_view(record: ProductionCltrRecord, sources: AdapterSources) -> AdapterResult:
    kind = RepresentationKind.RECONCILIATION_VIEW
    have_marker = bool(record.marker_id)
    have_receipt = bool(record.receipt_id)
    if have_receipt and have_marker:
        outcome_detail = "marker and receipt both present and bound to the same transition_id"
        conformance = ConformanceState.CONFORMANT
    elif have_receipt and not have_marker:
        outcome_detail = "receipt present without marker (never blocks correctness per CLTR-001 §19)"
        conformance = ConformanceState.CONFORMANT
    elif not have_receipt and record.notification_state.value == "confirmed":
        outcome_detail = "notification confirmed but no receipt recorded"
        conformance = ConformanceState.INCOMPLETE
    else:
        outcome_detail = "no delivery evidence recorded for this transition"
        conformance = ConformanceState.UNVERIFIABLE
    return AdapterResult(
        representation_kind=kind,
        comparison_mode=AdapterComparisonMode.OBSERVATIONAL,
        conformance_state=conformance,
        outcome=ComparisonOutcome.CONFORMANT if conformance == ConformanceState.CONFORMANT else ComparisonOutcome.PARTIALLY_CONFORMANT,
        detail=outcome_detail,
        authority_role="V",
    )


_ADAPTERS: tuple[Callable[[ProductionCltrRecord, AdapterSources], AdapterResult], ...] = (
    adapt_canonical_report,
    adapt_completion_metadata,
    adapt_architecture_status,
    adapt_immutable_snapshot,
    adapt_checkpoint,
    adapt_promoted_report,
    adapt_promoted_metadata,
    adapt_notification_payload,
    adapt_marker,
    adapt_receipt,
    adapt_repository_transition_view,
    adapt_git_attribution_view,
    adapt_compatibility_view,
    adapt_diagnostic_envelope,
    adapt_reconciliation_view,
)


def run_all_adapters(record: ProductionCltrRecord, sources: AdapterSources) -> tuple[AdapterResult, ...]:
    results = tuple(fn(record, sources) for fn in _ADAPTERS)
    kinds = [r.representation_kind for r in results]
    assert len(kinds) == 15
    assert len(set(kinds)) == 15
    assert set(kinds) == set(RepresentationKind)
    for result in results:
        assert result.comparison_mode == REPRESENTATION_COMPARISON_MODE[result.representation_kind]
    return results
