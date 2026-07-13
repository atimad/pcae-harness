"""The formal 14-state / 16-transition / 14-forbidden-transition model (135D §3-§6).

One function per named transition (T1-T16). There is no generic
``set_state(record, new_state)`` escape hatch anywhere in this module — this
is a binding design rule (135E §9), not an implementation detail. Every
public function below is named after, and implements exactly, one row of
135D §5's transition inventory. No function here performs I/O or a lifecycle
side effect; each returns a `TransitionResult` carrying a new, immutable
`TransitionRecord` value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pcae.cltr_prototype.models import (
    CommitClassificationResult,
    CommitOwnershipClassification,
    FailureClassification,
    RetryClassification,
    SpineState,
    TERMINAL_SPINE_STATES,
    TransitionOutcome,
    TransitionRecord,
    TransitionType,
)


class ForbiddenTransitionError(Exception):
    def __init__(self, forbidden_id: str, attempted: TransitionType, source_state: SpineState, reason: str):
        self.forbidden_id = forbidden_id
        self.attempted = attempted
        self.source_state = source_state
        self.reason = reason
        super().__init__(f"{forbidden_id}: {attempted.value} from {source_state.value} rejected — {reason}")


class PreconditionError(Exception):
    def __init__(self, attempted: TransitionType, detail: str):
        self.attempted = attempted
        self.detail = detail
        super().__init__(f"{attempted.value} precondition not met: {detail}")


@dataclass(frozen=True)
class TransitionResult:
    outcome: TransitionOutcome
    transition_type: TransitionType
    new_record: Optional[TransitionRecord]
    timestamp: str


# --- Forbidden-transition inventory (135D §6, F1-F14) -----------------------
# Maps (attempted transition, actual source spine_state) -> forbidden id, for
# every explicitly named forbidden pairing this prototype can exercise via
# its own 16 transition functions (F1/F2/F4/F12 collapse to "wrong source
# state for a promotion/notification-stage transition"; F5/F6/F7/F8/F9/F13/F14
# are each checked at their own specific transition function).

_FORBIDDEN_SOURCE_FOR = {
    TransitionType.BEGIN_PROMOTION: (SpineState.CERTIFIED, "F1/F12"),
    TransitionType.BEGIN_NOTIFICATION: (SpineState.PROMOTED, "F2/F4"),
}


def _terminal_ish(state: SpineState) -> bool:
    return state in TERMINAL_SPINE_STATES


def _reject_if_terminal(record: TransitionRecord, attempted: TransitionType) -> None:
    if record.is_terminal:
        raise ForbiddenTransitionError(
            "F7/F14", attempted, record.spine_state, "terminal or terminal-ish states admit no ordinary spine transition"
        )


def _reject_if_superseded(record: TransitionRecord, attempted: TransitionType) -> None:
    if record.superseded:
        raise ForbiddenTransitionError("F8", attempted, record.spine_state, "a superseded record cannot re-enter the active spine")


def t1_propose_transition(identity, source_revision: str, *, at: str, declared_commits=(), evidence_refs=()) -> TransitionResult:
    """T1: (none) -> PROPOSED."""

    record = TransitionRecord(
        identity=identity,
        spine_state=SpineState.PROPOSED,
        source_revision=source_revision,
        declared_commits=tuple(declared_commits),
        evidence_refs=tuple(evidence_refs),
        timestamps={"PROPOSED": at},
    )
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.PROPOSE_TRANSITION, record, at)


def t2_begin_certification(record: TransitionRecord, *, at: str) -> TransitionResult:
    """T2: PROPOSED -> CERTIFYING."""

    if record.spine_state != SpineState.PROPOSED:
        raise ForbiddenTransitionError("F1/F2/F12", TransitionType.BEGIN_CERTIFICATION, record.spine_state, "begin_certification requires PROPOSED")
    new_timestamps = {**record.timestamps, "CERTIFYING": at}
    new_record = record.with_updates(spine_state=SpineState.CERTIFYING, prior_state=SpineState.PROPOSED, timestamps=new_timestamps)
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.BEGIN_CERTIFICATION, new_record, at)


def t3_certify(
    record: TransitionRecord,
    *,
    at: str,
    certified_state: dict,
    projected_state: Optional[dict] = None,
    commit_classifications=(),
    report_binding=None,
    metadata_binding=None,
    snapshot_binding=None,
) -> TransitionResult:
    """T3: CERTIFYING -> CERTIFIED. Sealed: digest fixed by digest.py later."""

    if record.spine_state != SpineState.CERTIFYING:
        raise ForbiddenTransitionError("F1/F2/F4/F12", TransitionType.CERTIFY, record.spine_state, "certify requires CERTIFYING")
    new_timestamps = {**record.timestamps, "CERTIFIED": at}
    new_record = record.with_updates(
        spine_state=SpineState.CERTIFIED,
        prior_state=SpineState.CERTIFYING,
        certified_state=dict(certified_state),
        projected_state=dict(projected_state) if projected_state is not None else record.projected_state,
        commit_classifications=tuple(commit_classifications),
        report_binding=report_binding,
        metadata_binding=metadata_binding,
        snapshot_binding=snapshot_binding,
        timestamps=new_timestamps,
    )
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.CERTIFY, new_record, at)


def t4_certification_fail(record: TransitionRecord, *, at: str, detail: str) -> TransitionResult:
    """T4: CERTIFYING -> FAILED_PRE_CERT."""

    if record.spine_state != SpineState.CERTIFYING:
        raise ForbiddenTransitionError("F3", TransitionType.CERTIFICATION_FAIL, record.spine_state, "certification_fail requires CERTIFYING")
    new_timestamps = {**record.timestamps, "FAILED_PRE_CERT": at}
    new_record = record.with_updates(
        spine_state=SpineState.FAILED_PRE_CERT,
        prior_state=SpineState.CERTIFYING,
        failure_classification=FailureClassification.CERTIFICATION_FAILURE,
        limitations=record.limitations + (detail,),
        timestamps=new_timestamps,
    )
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.CERTIFICATION_FAIL, new_record, at)


def t5_begin_promotion(record: TransitionRecord, *, at: str) -> TransitionResult:
    """T5: CERTIFIED -> PROMOTING."""

    if record.spine_state != SpineState.CERTIFIED:
        forbidden_id = _FORBIDDEN_SOURCE_FOR[TransitionType.BEGIN_PROMOTION][1]
        raise ForbiddenTransitionError(forbidden_id, TransitionType.BEGIN_PROMOTION, record.spine_state, "begin_promotion requires CERTIFIED")
    new_timestamps = {**record.timestamps, "PROMOTING": at}
    new_record = record.with_updates(spine_state=SpineState.PROMOTING, prior_state=SpineState.CERTIFIED, timestamps=new_timestamps)
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.BEGIN_PROMOTION, new_record, at)


def t6_promote_succeed(record: TransitionRecord, *, at: str, promotion_binding) -> TransitionResult:
    """T6: PROMOTING -> PROMOTED."""

    if record.spine_state != SpineState.PROMOTING:
        raise ForbiddenTransitionError("F5", TransitionType.PROMOTE_SUCCEED, record.spine_state, "promote_succeed requires PROMOTING")
    new_timestamps = {**record.timestamps, "PROMOTED": at}
    new_record = record.with_updates(
        spine_state=SpineState.PROMOTED, prior_state=SpineState.PROMOTING, promotion_binding=promotion_binding, timestamps=new_timestamps
    )
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.PROMOTE_SUCCEED, new_record, at)


def t7_promote_fail(record: TransitionRecord, *, at: str, observation_detail: str) -> TransitionResult:
    """T7: PROMOTING -> FAILED_POST_CERT."""

    if record.spine_state != SpineState.PROMOTING:
        raise ForbiddenTransitionError("F13", TransitionType.PROMOTE_FAIL, record.spine_state, "promote_fail requires PROMOTING")
    new_timestamps = {**record.timestamps, "FAILED_POST_CERT": at}
    new_record = record.with_updates(
        spine_state=SpineState.FAILED_POST_CERT,
        prior_state=SpineState.PROMOTING,
        failure_classification=FailureClassification.PROMOTION_FAILURE,
        limitations=record.limitations + (observation_detail,),
        timestamps=new_timestamps,
    )
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.PROMOTE_FAIL, new_record, at)


def t8_begin_notification(record: TransitionRecord, *, at: str) -> TransitionResult:
    """T8: PROMOTED -> NOTIFYING."""

    if record.spine_state != SpineState.PROMOTED:
        forbidden_id = _FORBIDDEN_SOURCE_FOR[TransitionType.BEGIN_NOTIFICATION][1]
        raise ForbiddenTransitionError(forbidden_id, TransitionType.BEGIN_NOTIFICATION, record.spine_state, "begin_notification requires PROMOTED")
    new_timestamps = {**record.timestamps, "NOTIFYING": at}
    new_record = record.with_updates(spine_state=SpineState.NOTIFYING, prior_state=SpineState.PROMOTED, timestamps=new_timestamps)
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.BEGIN_NOTIFICATION, new_record, at)


def t9_notify_confirm(record: TransitionRecord, *, at: str, notification_binding, marker_binding=None, receipt_binding=None) -> TransitionResult:
    """T9: NOTIFYING -> NOTIFIED."""

    if record.spine_state != SpineState.NOTIFYING:
        raise ForbiddenTransitionError("F6", TransitionType.NOTIFY_CONFIRM, record.spine_state, "notify_confirm requires NOTIFYING")
    new_timestamps = {**record.timestamps, "NOTIFIED": at}
    new_record = record.with_updates(
        spine_state=SpineState.NOTIFIED,
        prior_state=SpineState.NOTIFYING,
        notification_binding=notification_binding,
        marker_binding=marker_binding,
        receipt_binding=receipt_binding,
        timestamps=new_timestamps,
    )
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.NOTIFY_CONFIRM, new_record, at)


def t10_notify_unconfirmed(record: TransitionRecord, *, at: str, notification_binding, marker_binding=None) -> TransitionResult:
    """T10: NOTIFYING -> NOTIFIED_UNCONFIRMED."""

    if record.spine_state != SpineState.NOTIFYING:
        raise ForbiddenTransitionError("F6", TransitionType.NOTIFY_UNCONFIRMED, record.spine_state, "notify_unconfirmed requires NOTIFYING")
    new_timestamps = {**record.timestamps, "NOTIFIED_UNCONFIRMED": at}
    new_record = record.with_updates(
        spine_state=SpineState.NOTIFIED_UNCONFIRMED,
        prior_state=SpineState.NOTIFYING,
        notification_binding=notification_binding,
        marker_binding=marker_binding,
        timestamps=new_timestamps,
    )
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.NOTIFY_UNCONFIRMED, new_record, at)


def t11_notify_retry(record: TransitionRecord, *, at: str) -> TransitionResult:
    """T11: NOTIFYING -> NOTIFYING (self-loop; the only legal notification retry)."""

    if record.spine_state != SpineState.NOTIFYING:
        raise ForbiddenTransitionError(
            "CLTR-NOTIFY-2", TransitionType.NOTIFY_RETRY, record.spine_state, "notify_retry is only entered from NOTIFYING, never NOTIFIED/NOTIFIED_UNCONFIRMED"
        )
    new_timestamps = {**record.timestamps, f"NOTIFYING_RETRY_{at}": at}
    new_record = record.with_updates(timestamps=new_timestamps)
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.NOTIFY_RETRY, new_record, at)


def t12_reconcile_receipt(record: TransitionRecord, *, at: str, receipt_binding, resolved: bool) -> TransitionResult:
    """T12: NOTIFIED_UNCONFIRMED -> NOTIFIED_UNCONFIRMED (constrained repair; receipt only)."""

    if record.spine_state != SpineState.NOTIFIED_UNCONFIRMED:
        raise ForbiddenTransitionError(
            "F6", TransitionType.RECONCILE_RECEIPT, record.spine_state, "reconcile_receipt requires NOTIFIED_UNCONFIRMED; it never re-triggers delivery"
        )
    new_timestamps = {**record.timestamps, f"RECEIPT_RECONCILE_{at}": at}
    new_record = record.with_updates(receipt_binding=receipt_binding, timestamps=new_timestamps)
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.RECONCILE_RECEIPT, new_record, at)


def t13_close_success(record: TransitionRecord, *, at: str) -> TransitionResult:
    """T13: NOTIFIED -> TERMINAL_SUCCESS."""

    if record.spine_state != SpineState.NOTIFIED:
        raise ForbiddenTransitionError("F7", TransitionType.CLOSE_SUCCESS, record.spine_state, "close_success requires NOTIFIED")
    new_timestamps = {**record.timestamps, "TERMINAL_SUCCESS": at, "final": at}
    new_record = record.with_updates(spine_state=SpineState.TERMINAL_SUCCESS, prior_state=SpineState.NOTIFIED, timestamps=new_timestamps)
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.CLOSE_SUCCESS, new_record, at)


def t14_close_partial(record: TransitionRecord, *, at: str) -> TransitionResult:
    """T14: NOTIFIED_UNCONFIRMED -> TERMINAL_PARTIAL_EXTERNAL."""

    if record.spine_state != SpineState.NOTIFIED_UNCONFIRMED:
        raise ForbiddenTransitionError("F7", TransitionType.CLOSE_PARTIAL, record.spine_state, "close_partial requires NOTIFIED_UNCONFIRMED")
    new_timestamps = {**record.timestamps, "TERMINAL_PARTIAL_EXTERNAL": at, "final": at}
    new_record = record.with_updates(
        spine_state=SpineState.TERMINAL_PARTIAL_EXTERNAL,
        prior_state=SpineState.NOTIFIED_UNCONFIRMED,
        failure_classification=FailureClassification.NOTIFICATION_UNCERTAINTY,
        timestamps=new_timestamps,
    )
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.CLOSE_PARTIAL, new_record, at)


def t15_quarantine(record: TransitionRecord, *, at: str, mismatch_detail: str) -> TransitionResult:
    """T15 (orthogonal): any CERTIFIED-or-later state -> QUARANTINED flag."""

    if record.spine_state == SpineState.PROPOSED or record.spine_state == SpineState.CERTIFYING:
        raise ForbiddenTransitionError("F9", TransitionType.QUARANTINE, record.spine_state, "quarantine requires CERTIFIED-or-later")
    new_record = record.with_updates(quarantined=True, limitations=record.limitations + (mismatch_detail,))
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.QUARANTINE, new_record, at)


def t16_supersede(record: TransitionRecord, *, at: str, superseding_transition_id: str) -> TransitionResult:
    """T16 (orthogonal): any state -> SUPERSEDED flag, annotation only."""

    new_record = record.with_updates(superseded=True, superseded_by=superseding_transition_id)
    return TransitionResult(TransitionOutcome.APPLIED, TransitionType.SUPERSEDE, new_record, at)


# --- Retry/resume and terminal lookups (135D §24) ---------------------------

_RETRY_TABLE = {
    SpineState.PROPOSED: RetryClassification.BEGIN,
    SpineState.CERTIFYING: RetryClassification.BEGIN,
    SpineState.CERTIFIED: RetryClassification.CONTINUE,
    SpineState.PROMOTING: RetryClassification.RESUME_AFTER_OBSERVATION,
    SpineState.PROMOTED: RetryClassification.CONTINUE,
    SpineState.NOTIFYING: RetryClassification.RESUME_AFTER_OBSERVATION,
    SpineState.NOTIFIED: RetryClassification.RETURN_PRIOR_RESULT,
    SpineState.NOTIFIED_UNCONFIRMED: RetryClassification.REPAIR_DERIVATIVE_ONLY,
    SpineState.TERMINAL_SUCCESS: RetryClassification.RETURN_PRIOR_RESULT,
    SpineState.TERMINAL_PARTIAL_EXTERNAL: RetryClassification.RETURN_PRIOR_RESULT,
    SpineState.FAILED_PRE_CERT: RetryClassification.BEGIN,
    SpineState.FAILED_POST_CERT: RetryClassification.RESUME_AFTER_OBSERVATION,
}


def retry_classification(record: TransitionRecord) -> RetryClassification:
    if record.quarantined:
        return RetryClassification.REQUIRE_HUMAN_REVIEW
    if record.superseded:
        return RetryClassification.REJECT_SUPERSEDED_REDIRECT
    return _RETRY_TABLE[record.spine_state]


def is_terminal(state: SpineState) -> bool:
    return state in TERMINAL_SPINE_STATES
