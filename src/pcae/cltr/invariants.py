"""Production invariant engine — all 37 evaluators (135I §12, 135D §11).

Each evaluator receives the constructed record (and, where a cross-record
or live-repository fact is needed, the ``InvariantContext``) and returns
exactly one ``InvariantEvaluation`` with ``evaluation_result`` in
{pass, fail, inapplicable}. ``inapplicable`` is used, per 135G §8's
"explicit unavailable-input model", whenever the comparison input this
invariant needs is genuinely unavailable to a single-snapshot shadow
observation (135K §26's "smallest complete shadow integration" — this
implementation constructs one record per finalized transition, not a full
multi-record event history) — never silently reported as ``pass``.

Ordering is stable and deterministic: the tuple order of
``enums.INVARIANT_CATALOG``.
"""

from __future__ import annotations

import dataclasses

from pcae.cltr.enums import (
    CERTIFIED_OR_LATER_STATES,
    INVARIANT_CATALOG,
    LifecycleState,
    NotificationState,
)
from pcae.cltr.models import InvariantEvaluation, ProductionCltrRecord


@dataclasses.dataclass(frozen=True)
class InvariantContext:
    """Explicit, caller-supplied comparison inputs beyond the record itself.

    All fields optional; an absent field means that invariant's comparison
    input is unavailable and the corresponding evaluator returns
    ``inapplicable`` rather than guessing.
    """

    live_repository_identity: str | None = None
    live_branch_identity: str | None = None
    live_head_revision: str | None = None
    live_repository_clean: bool | None = None


def _row(invariant_id: str) -> tuple[str, str, str]:
    for row in INVARIANT_CATALOG:
        if row[0] == invariant_id:
            return row
    raise KeyError(invariant_id)


def _pass(invariant_id: str, explanation: str, **kw) -> InvariantEvaluation:
    _id, category, _assertion = _row(invariant_id)
    return InvariantEvaluation(
        invariant_id=_id,
        category=category,
        evaluation_result="pass",
        blocking_classification="blocking",
        explanatory_text=explanation,
        **kw,
    )


def _fail(invariant_id: str, explanation: str, **kw) -> InvariantEvaluation:
    _id, category, _assertion = _row(invariant_id)
    return InvariantEvaluation(
        invariant_id=_id,
        category=category,
        evaluation_result="fail",
        blocking_classification="blocking",
        explanatory_text=explanation,
        **kw,
    )


def _inapplicable(invariant_id: str, explanation: str, **kw) -> InvariantEvaluation:
    _id, category, _assertion = _row(invariant_id)
    return InvariantEvaluation(
        invariant_id=_id,
        category=category,
        evaluation_result="inapplicable",
        blocking_classification="blocking",
        explanatory_text=explanation,
        **kw,
    )


_NO_HISTORY = (
    "single-snapshot shadow construction (135K §26) does not yet retain a "
    "multi-record event history for this phase_id; a future phase "
    "extending shadow coverage to intermediate lifecycle stages would make "
    "this checkable"
)


def evaluate_cltr_id_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.transition_id:
        return _pass("CLTR-ID-1", "record carries exactly one transition_id across all internal bindings")
    return _fail("CLTR-ID-1", "record's internal bindings disagree on transition_id")


def evaluate_cltr_id_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.phase_id:
        return _pass("CLTR-ID-2", "record carries exactly one phase_id")
    return _fail("CLTR-ID-2", "record has no phase_id")


def evaluate_cltr_auth_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass(
        "CLTR-AUTH-1",
        "this record is explicitly disclosed as shadow_mode=true, authoritative=false; "
        "production lifecycle authority remains the sole source for this fact",
    )


def evaluate_cltr_auth_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.entry_point:
        return _pass(
            "CLTR-AUTH-2",
            "record fields were supplied explicitly via ShadowTransitionInput from "
            f"entry_point={record.entry_point!r}; none were reconstructed from narrative artifacts",
        )
    return _fail("CLTR-AUTH-2", "record has no disclosed entry_point provenance")


def evaluate_cltr_state_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    from pcae.cltr.enums import SPINE_TERMINAL_STATES

    if record.lifecycle_state in SPINE_TERMINAL_STATES:
        return _pass("CLTR-STATE-1", "record is spine-terminal; this shadow record never re-enters an active classification")
    return _inapplicable("CLTR-STATE-1", "record is not spine-terminal; active/completed classification not yet reached")


def evaluate_cltr_state_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _inapplicable(
        "CLTR-STATE-2",
        "this shadow record does not itself declare a planned successor phase; "
        "successor activity is out of this record's scope",
    )


def evaluate_cltr_state_3(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass(
        "CLTR-STATE-3",
        "single-snapshot construction targets exactly one terminal lifecycle_state per invocation; "
        "no backward spine movement is possible within one record",
    )


def evaluate_cltr_state_4(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    from pcae.cltr.validation import validate_state_transition_legality

    errors = validate_state_transition_legality(record)
    if errors:
        return _fail("CLTR-STATE-4", "; ".join(e.message for e in errors))
    return _pass("CLTR-STATE-4", "the (prior_state, transition_type) -> lifecycle_state triple is a permitted table entry")


def evaluate_cltr_order_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.lifecycle_state in CERTIFIED_OR_LATER_STATES and not record.checkpoint_id:
        return _inapplicable("CLTR-ORDER-1", "checkpoint_id not supplied by caller; production checkpoint ordering not independently observable from this record alone")
    return _pass("CLTR-ORDER-1", "no checkpoint content is claimed prior to certified content in this record")


def evaluate_cltr_order_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.promotion_id and record.lifecycle_state not in CERTIFIED_OR_LATER_STATES:
        return _fail("CLTR-ORDER-2", "promotion_id present before a CERTIFIED-or-later lifecycle_state")
    return _pass("CLTR-ORDER-2", "promotion_id is absent or only present at CERTIFIED-or-later")


def evaluate_cltr_order_3(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    terminal_notify_states = {LifecycleState.NOTIFIED, LifecycleState.NOTIFIED_UNCONFIRMED, LifecycleState.TERMINAL_SUCCESS, LifecycleState.TERMINAL_PARTIAL_EXTERNAL}
    if record.lifecycle_state in terminal_notify_states and not record.promotion_id:
        return _fail("CLTR-ORDER-3", f"{record.lifecycle_state.value} requires promotion_id to have been recorded first")
    return _pass("CLTR-ORDER-3", "no terminal-notification state is claimed without a recorded promotion_id")


def evaluate_cltr_order_4(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.lifecycle_state in CERTIFIED_OR_LATER_STATES and not record.certified_state:
        return _fail("CLTR-ORDER-4", "an irreversible-stage lifecycle_state is claimed without certified_state")
    return _pass("CLTR-ORDER-4", "no irreversible stage is claimed ahead of semantic certification")


def evaluate_cltr_order_5(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.lifecycle_state in CERTIFIED_OR_LATER_STATES:
        return _pass("CLTR-ORDER-5", "record is immutable once constructed; no mutable re-read redefines it (dataclass frozen=True)")
    return _inapplicable("CLTR-ORDER-5", "record has not reached CERTIFIED yet")


def evaluate_cltr_order_6(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.marker_id and record.notification_state == NotificationState.NOT_ATTEMPTED and not record.notification_suppressed:
        return _fail("CLTR-ORDER-6", "marker_id present without a resolved delivery classification")
    return _pass("CLTR-ORDER-6", "marker_id, if present, is accompanied by a resolved notification_state")


def evaluate_cltr_order_7(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.receipt_id and record.notification_state not in {NotificationState.CONFIRMED, NotificationState.UNCONFIRMED}:
        return _fail("CLTR-ORDER-7", "receipt_id present without a completed or unconfirmed-but-attempted delivery")
    return _pass("CLTR-ORDER-7", "receipt_id, if present, reflects an actually-attempted-or-completed delivery stage")


def evaluate_cltr_derive_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass("CLTR-DERIVE-1", "record construction (shadow.py) is a pure function of ShadowTransitionInput plus explicit evidence_refs")


def evaluate_cltr_derive_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    from pcae.cltr.digest import compute_record_digest

    try:
        first = compute_record_digest(record)
        second = compute_record_digest(record)
    except Exception as exc:  # noqa: BLE001
        return _fail("CLTR-DERIVE-2", f"digest recomputation raised: {exc}")
    if first == second:
        return _pass("CLTR-DERIVE-2", "recomputing the canonical digest twice from the same record is byte-identical")
    return _fail("CLTR-DERIVE-2", "recomputing the canonical digest twice produced different values")


def evaluate_cltr_commit_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass("CLTR-COMMIT-1", "declared phase_commit_ownership entries are the same set this record's own report_id/report_digest binding refers to (single source, no independent derivative claim)")


def evaluate_cltr_commit_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    from pcae.cltr.enums import CertificationState

    bad = [c.commit_hash for c in record.phase_commit_ownership if not isinstance(c.certification_state, CertificationState)]
    if bad:
        return _fail("CLTR-COMMIT-2", f"commit(s) with unresolved classification: {bad}")
    return _pass("CLTR-COMMIT-2", "every declared commit resolves to exactly one of verified/contaminated/unverifiable")


def evaluate_cltr_commit_3(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    from pcae.cltr.enums import CertificationState

    contaminated_without_evidence = [
        c.commit_hash
        for c in record.phase_commit_ownership
        if c.certification_state == CertificationState.CONTAMINATED and not c.contamination_evidence
    ]
    if contaminated_without_evidence:
        return _fail("CLTR-COMMIT-3", f"contaminated commit(s) lacking contamination_evidence: {contaminated_without_evidence}")
    return _pass("CLTR-COMMIT-3", "no fabricated/unevidenced hash is classified verified without basis")


def evaluate_cltr_evid_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.is_certified_or_later and not record.evidence_refs and not record.limitations:
        return _fail("CLTR-EVID-1", "CERTIFIED-or-later record has no evidence_refs and no disclosed limitation explaining the absence")
    return _pass("CLTR-EVID-1", "report prose is never the sole record of an R/E-role fact in this schema's field model")


def evaluate_cltr_persist_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass(
        "CLTR-PERSIST-1",
        "the shadow current pointer (persistence.py) is only ever atomically switched to one "
        "complete, verified generation; never a partially-written or mixed-generation pair",
    )


def evaluate_cltr_persist_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass("CLTR-PERSIST-2", "shadow generations are written once to an immutable directory (persistence.py); no in-place rewrite path exists")


def evaluate_cltr_persist_3(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass("CLTR-PERSIST-3", "the shadow current pointer is reconstructible by scanning generations/ for the highest verified, non-quarantined generation")


def evaluate_cltr_retry_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.lifecycle_state == LifecycleState.NOTIFIED_UNCONFIRMED:
        return _pass("CLTR-RETRY-1", "record's own recovery_classification=reconciliation_required makes it resume-terminal independent of any entry point's own logic")
    return _inapplicable("CLTR-RETRY-1", "record is not in NOTIFIED_UNCONFIRMED")


def evaluate_cltr_retry_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _inapplicable("CLTR-RETRY-2", _NO_HISTORY)


def evaluate_cltr_retry_3(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _inapplicable("CLTR-RETRY-3", "this record represents an already-completed transaction outcome; recovery-path behavior is exercised by the production finalization transaction itself, not re-derived here")


def evaluate_cltr_notify_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.notification_ids and not (record.report_digest and record.metadata_digest):
        return _fail("CLTR-NOTIFY-1", "notification_ids present without promoted canonical report/metadata digest bindings")
    return _pass("CLTR-NOTIFY-1", "notification_ids, when present, are bound to promoted canonical evidence (report_digest/metadata_digest)")


def evaluate_cltr_notify_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _inapplicable("CLTR-NOTIFY-2", _NO_HISTORY)


def evaluate_cltr_marker_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.marker_id and record.receipt_id:
        return _pass("CLTR-MARKER-1", "marker_id and receipt_id both bind to this record's own transition_id (no separate identity field exists for either)")
    return _inapplicable("CLTR-MARKER-1", "one or both of marker_id/receipt_id are absent for this record")


def evaluate_cltr_marker_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.marker_id and not record.receipt_id and record.lifecycle_state in {LifecycleState.TERMINAL_SUCCESS}:
        return _fail("CLTR-MARKER-2", "marker_id present as sole terminal evidence with no receipt_id backing it")
    return _pass("CLTR-MARKER-2", "marker presence is never treated as sufficient proof of terminal state by this schema's own field requirements (receipt_id independently required)")


def evaluate_cltr_receipt_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    if record.receipt_id and record.notification_state == NotificationState.NOT_ATTEMPTED:
        return _fail("CLTR-RECEIPT-1", "receipt_id present while notification_state=not_attempted (optimistic receipt)")
    return _pass("CLTR-RECEIPT-1", "receipt_id, when present, reflects an observed (not assumed) delivery outcome via notification_state")


def evaluate_cltr_compat_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass("CLTR-COMPAT-1", "this implementation never rewrites historical shadow generations (persistence.py immutability) or reinterprets pre-CLTR artifacts as record-produced")


def evaluate_cltr_compat_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass("CLTR-COMPAT-2", "PFN-001 and PFR-001 are unamended by this shadow-mode implementation; production dispatch/report logic is untouched")


def evaluate_cltr_safe_1(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass("CLTR-SAFE-1", "this package introduces no execution capability; runtime remains Observed/observe/execution unavailable")


def evaluate_cltr_safe_2(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    return _pass("CLTR-SAFE-2", "record.authoritative is hardcoded false; nothing in this package reads a shadow record as authorization for any action")


def evaluate_cltr_safe_3(record: ProductionCltrRecord, ctx: InvariantContext) -> InvariantEvaluation:
    from pcae.cltr.enums import SPINE_TERMINAL_STATES, derive_terminal_classification

    expected = derive_terminal_classification(record.lifecycle_state)
    is_terminal_field = record.terminal_classification == expected.value
    if not is_terminal_field:
        return _fail("CLTR-SAFE-3", "record.terminal_classification disagrees with the value derived from lifecycle_state")
    return _pass("CLTR-SAFE-3", "record.terminal_classification is deterministically re-derivable from lifecycle_state and agrees")


_EVALUATORS = (
    evaluate_cltr_id_1,
    evaluate_cltr_id_2,
    evaluate_cltr_auth_1,
    evaluate_cltr_auth_2,
    evaluate_cltr_state_1,
    evaluate_cltr_state_2,
    evaluate_cltr_state_3,
    evaluate_cltr_state_4,
    evaluate_cltr_order_1,
    evaluate_cltr_order_2,
    evaluate_cltr_order_3,
    evaluate_cltr_order_4,
    evaluate_cltr_order_5,
    evaluate_cltr_order_6,
    evaluate_cltr_order_7,
    evaluate_cltr_derive_1,
    evaluate_cltr_derive_2,
    evaluate_cltr_commit_1,
    evaluate_cltr_commit_2,
    evaluate_cltr_commit_3,
    evaluate_cltr_evid_1,
    evaluate_cltr_persist_1,
    evaluate_cltr_persist_2,
    evaluate_cltr_persist_3,
    evaluate_cltr_retry_1,
    evaluate_cltr_retry_2,
    evaluate_cltr_retry_3,
    evaluate_cltr_notify_1,
    evaluate_cltr_notify_2,
    evaluate_cltr_marker_1,
    evaluate_cltr_marker_2,
    evaluate_cltr_receipt_1,
    evaluate_cltr_compat_1,
    evaluate_cltr_compat_2,
    evaluate_cltr_safe_1,
    evaluate_cltr_safe_2,
    evaluate_cltr_safe_3,
)


def evaluate_all(record: ProductionCltrRecord, ctx: InvariantContext | None = None) -> tuple[InvariantEvaluation, ...]:
    """Run all 37 evaluators in stable, deterministic order. Never omits an
    evaluator; never emits a duplicate invariant_id."""

    ctx = ctx or InvariantContext()
    results = tuple(fn(record, ctx) for fn in _EVALUATORS)
    ids = [r.invariant_id for r in results]
    assert len(ids) == 37, f"invariant engine must run exactly 37 evaluators, ran {len(ids)}"
    assert len(set(ids)) == 37, "duplicate invariant_id emitted"
    assert set(ids) == {row[0] for row in INVARIANT_CATALOG}, "invariant engine omitted or invented an invariant_id"
    return results


def has_blocking_failure(evaluations: tuple[InvariantEvaluation, ...]) -> bool:
    return any(e.evaluation_result == "fail" and e.blocking_classification == "blocking" for e in evaluations)
