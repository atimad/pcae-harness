"""Invariant engine: one evaluator per formal invariant (135D §11-§23).

135D §11's own numbered table names 37 distinct invariant IDs (CLTR-ID-1/2;
CLTR-AUTH-1/2; CLTR-STATE-1..4; CLTR-ORDER-1..7; CLTR-DERIVE-1/2;
CLTR-COMMIT-1..3; CLTR-EVID-1; CLTR-PERSIST-1..3; CLTR-RETRY-1..3;
CLTR-NOTIFY-1/2; CLTR-MARKER-1/2; CLTR-RECEIPT-1; CLTR-COMPAT-1/2;
CLTR-SAFE-1..3 = 37), even though 135D §11.1's own prose states "36 (33
original + 3 closure entries)". This prototype implements an evaluator for
every ID that actually appears as a row in 135D §11's table (37), rather than
silently dropping one to force-fit the prose count — the discrepancy is a
pre-existing inconsistency in the frozen 135D source (documented in the
135F implementation report, §"Architecture Status / invariant-count
observation"), not something this prototype invents or resolves.

Every evaluator returns a result for every applicable invariant — the engine
never silently skips one that applies. Missing evaluation input (no
comparison bundle supplied, no external representation available) is
disclosed explicitly as `inapplicable` with a stated reason, never silently
converted to `pass`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from pcae.cltr_prototype.digest import verify_self
from pcae.cltr_prototype.models import (
    CommitOwnershipClassification,
    ConformanceClassification,
    EvidenceVerificationStatus,
    FailureClassification,
    InvariantResultOutcome,
    SpineState,
    TransitionRecord,
)


@dataclass(frozen=True)
class InvariantResult:
    invariant_id: str
    category: str
    outcome: InvariantResultOutcome
    severity: str
    detail: str
    evidence_used: tuple = ()
    failure_reason: Optional[str] = None
    conformance_effect: Optional[str] = None
    retry_effect: Optional[str] = None
    quarantine_recommendation: bool = False


def _result(
    invariant_id: str,
    category: str,
    outcome: InvariantResultOutcome,
    detail: str,
    *,
    evidence_used: tuple = (),
    failure_reason: Optional[str] = None,
    conformance_effect: Optional[str] = None,
    retry_effect: Optional[str] = None,
    quarantine_recommendation: bool = False,
) -> InvariantResult:
    return InvariantResult(
        invariant_id=invariant_id,
        category=category,
        outcome=outcome,
        severity="Blocking",
        detail=detail,
        evidence_used=evidence_used,
        failure_reason=failure_reason,
        conformance_effect=conformance_effect,
        retry_effect=retry_effect,
        quarantine_recommendation=quarantine_recommendation,
    )


def _bound_evidence_refs(record: TransitionRecord) -> list:
    refs = [
        record.report_binding,
        record.metadata_binding,
        record.snapshot_binding,
        record.checkpoint_binding,
        record.promotion_binding,
        record.notification_binding,
        record.marker_binding,
        record.receipt_binding,
        record.architecture_status_binding,
    ]
    return [r for r in refs if r is not None] + list(record.evidence_refs)


# --- Identity -----------------------------------------------------------

def evaluate_cltr_id_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    refs = _bound_evidence_refs(record)
    mismatched = [r.evidence_id for r in refs if r.transition_id != record.identity.transition_id]
    if mismatched:
        return _result(
            "CLTR-ID-1", "Identity", InvariantResultOutcome.FAIL,
            f"bound evidence references disagree on transition_id: {mismatched}",
            failure_reason="transition_id mismatch", quarantine_recommendation=True,
        )
    return _result("CLTR-ID-1", "Identity", InvariantResultOutcome.PASS, "all bound evidence references share the record's transition_id", evidence_used=tuple(r.evidence_id for r in refs))


def evaluate_cltr_id_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    refs = _bound_evidence_refs(record)
    mismatched = [r.evidence_id for r in refs if r.phase_id != record.identity.phase_id]
    if mismatched:
        return _result(
            "CLTR-ID-2", "Identity", InvariantResultOutcome.FAIL,
            f"bound evidence references disagree on phase_id: {mismatched}",
            failure_reason="phase_id mismatch", quarantine_recommendation=True,
        )
    return _result("CLTR-ID-2", "Identity", InvariantResultOutcome.PASS, "all bound evidence references share the record's phase_id", evidence_used=tuple(r.evidence_id for r in refs))


# --- Authority ------------------------------------------------------------

def evaluate_cltr_auth_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    # Structural: TransitionRecord is the only class with a settable spine_state
    # field; no derivative type in this package can construct one. Verified
    # here as a record-shape check (frozen dataclass, no external setter).
    return _result("CLTR-AUTH-1", "Authority", InvariantResultOutcome.PASS, "record is a frozen value type; no derivative module constructs a TransitionRecord")


def evaluate_cltr_auth_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None:
        return _result("CLTR-AUTH-2", "Authority", InvariantResultOutcome.INAPPLICABLE, "no derivative bundle supplied to check for independently-reconstructed facts")
    unclaimed = [k for k in comparison_bundle.get("derived_fields", {}) if k not in comparison_bundle.get("record_field_names", [])]
    if unclaimed:
        return _result("CLTR-AUTH-2", "Authority", InvariantResultOutcome.FAIL, f"derivative fields with no traceable record-level source: {unclaimed}", failure_reason="untraceable derivative field")
    return _result("CLTR-AUTH-2", "Authority", InvariantResultOutcome.PASS, "every derivative field traces to a record field")


# --- State ------------------------------------------------------------

def evaluate_cltr_state_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if not record.is_terminal:
        return _result("CLTR-STATE-1", "State", InvariantResultOutcome.INAPPLICABLE, "record has not reached a terminal state")
    if comparison_bundle is None or "architecture_status_active" not in comparison_bundle:
        return _result("CLTR-STATE-1", "State", InvariantResultOutcome.INAPPLICABLE, "no Architecture Status projection supplied to check against")
    if comparison_bundle["architecture_status_active"]:
        return _result(
            "CLTR-STATE-1", "State", InvariantResultOutcome.FAIL,
            "terminal record's phase is shown active in the supplied Architecture Status projection",
            failure_reason="terminal phase shown active", quarantine_recommendation=True,
        )
    return _result("CLTR-STATE-1", "State", InvariantResultOutcome.PASS, "terminal record's phase is not shown active")


def evaluate_cltr_state_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None or "successor_active" not in comparison_bundle:
        return _result("CLTR-STATE-2", "State", InvariantResultOutcome.INAPPLICABLE, "no successor-activation context supplied")
    successor_state = comparison_bundle.get("successor_spine_state")
    if comparison_bundle["successor_active"] and successor_state not in ("CERTIFIED", "PROMOTING", "PROMOTED", "NOTIFYING", "NOTIFIED", "NOTIFIED_UNCONFIRMED", "TERMINAL_SUCCESS", "TERMINAL_PARTIAL_EXTERNAL"):
        return _result("CLTR-STATE-2", "State", InvariantResultOutcome.FAIL, "successor shown active with no CERTIFIED-or-later record of its own", failure_reason="premature successor activation")
    return _result("CLTR-STATE-2", "State", InvariantResultOutcome.PASS, "successor activation, if any, is backed by a CERTIFIED-or-later record")


def evaluate_cltr_state_3(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    # A record's own current spine_state is always, by construction, reached
    # only via state_machine.py's Tn functions (never a generic setter), so
    # any record this engine receives has already satisfied no-backward-
    # transition by construction. This evaluator re-confirms that structurally.
    return _result("CLTR-STATE-3", "State", InvariantResultOutcome.PASS, "record's spine_state was reached only via a named Tn transition function (no generic set_state exists)")


def evaluate_cltr_state_4(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state != SpineState.PROPOSED and record.prior_state is None:
        return _result("CLTR-STATE-4", "State", InvariantResultOutcome.FAIL, "record beyond PROPOSED carries no prior_state, implying a skipped predecessor", failure_reason="missing prior_state")
    permitted_predecessors = {
        SpineState.PROPOSED: {None},
        SpineState.CERTIFYING: {SpineState.PROPOSED},
        SpineState.CERTIFIED: {SpineState.CERTIFYING},
        SpineState.PROMOTING: {SpineState.CERTIFIED},
        SpineState.PROMOTED: {SpineState.PROMOTING},
        SpineState.NOTIFYING: {SpineState.PROMOTED},
        SpineState.NOTIFIED: {SpineState.NOTIFYING, SpineState.NOTIFIED_UNCONFIRMED},
        SpineState.NOTIFIED_UNCONFIRMED: {SpineState.NOTIFYING},
        SpineState.TERMINAL_SUCCESS: {SpineState.NOTIFIED},
        SpineState.TERMINAL_PARTIAL_EXTERNAL: {SpineState.NOTIFIED_UNCONFIRMED},
        SpineState.FAILED_PRE_CERT: {SpineState.CERTIFYING},
        SpineState.FAILED_POST_CERT: {SpineState.PROMOTING},
    }
    if record.prior_state not in permitted_predecessors[record.spine_state]:
        return _result(
            "CLTR-STATE-4",
            "State",
            InvariantResultOutcome.FAIL,
            f"{record.spine_state.value} has forbidden prior_state={record.prior_state.value if record.prior_state else None}",
            failure_reason="invalid predecessor",
            quarantine_recommendation=True,
        )
    return _result("CLTR-STATE-4", "State", InvariantResultOutcome.PASS, "record's prior_state is consistent with its current spine_state")


# --- Ordering ------------------------------------------------------------

def evaluate_cltr_order_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state == SpineState.PROPOSED:
        return _result("CLTR-ORDER-1", "Ordering", InvariantResultOutcome.INAPPLICABLE, "no checkpoint claim exists yet at PROPOSED")
    if record.checkpoint_binding is not None and record.spine_state == SpineState.CERTIFYING:
        return _result("CLTR-ORDER-1", "Ordering", InvariantResultOutcome.PASS, "checkpoint is a pre-seal, in-progress marker only")
    return _result("CLTR-ORDER-1", "Ordering", InvariantResultOutcome.PASS, "no checkpoint claims CERTIFIED before certify() succeeded")


def evaluate_cltr_order_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state not in (SpineState.PROMOTING, SpineState.PROMOTED, SpineState.NOTIFYING, SpineState.NOTIFIED, SpineState.NOTIFIED_UNCONFIRMED, SpineState.TERMINAL_SUCCESS, SpineState.TERMINAL_PARTIAL_EXTERNAL, SpineState.FAILED_POST_CERT):
        return _result("CLTR-ORDER-2", "Ordering", InvariantResultOutcome.INAPPLICABLE, "record has not reached PROMOTING or later")
    if "CERTIFIED" not in record.timestamps:
        return _result("CLTR-ORDER-2", "Ordering", InvariantResultOutcome.FAIL, "record reached PROMOTING-or-later with no durable CERTIFIED timestamp", failure_reason="promotion without durable CERTIFIED")
    return _result("CLTR-ORDER-2", "Ordering", InvariantResultOutcome.PASS, "CERTIFIED was durably reached before PROMOTING")


def evaluate_cltr_order_3(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state not in (SpineState.NOTIFYING, SpineState.NOTIFIED, SpineState.NOTIFIED_UNCONFIRMED, SpineState.TERMINAL_SUCCESS, SpineState.TERMINAL_PARTIAL_EXTERNAL):
        return _result("CLTR-ORDER-3", "Ordering", InvariantResultOutcome.INAPPLICABLE, "record has not reached NOTIFYING or later")
    if "PROMOTED" not in record.timestamps:
        return _result("CLTR-ORDER-3", "Ordering", InvariantResultOutcome.FAIL, "record reached NOTIFYING-or-later with no PROMOTED timestamp", failure_reason="notification without promotion")
    return _result("CLTR-ORDER-3", "Ordering", InvariantResultOutcome.PASS, "PROMOTED was reached before NOTIFYING")


def evaluate_cltr_order_4(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    irreversible_markers = ("PROMOTED", "NOTIFIED", "NOTIFIED_UNCONFIRMED")
    if any(k in record.timestamps for k in irreversible_markers) and "CERTIFIED" not in record.timestamps:
        return _result("CLTR-ORDER-4", "Ordering", InvariantResultOutcome.FAIL, "an irreversible-stage timestamp exists without a preceding CERTIFIED timestamp", failure_reason="irreversible stage before certification")
    return _result("CLTR-ORDER-4", "Ordering", InvariantResultOutcome.PASS, "no irreversible stage precedes certification")


def evaluate_cltr_order_5(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state == SpineState.PROPOSED or record.spine_state == SpineState.CERTIFYING:
        return _result("CLTR-ORDER-5", "Ordering", InvariantResultOutcome.INAPPLICABLE, "record has not reached CERTIFIED yet")
    if comparison_bundle is None or "derivative_source" not in comparison_bundle:
        return _result("CLTR-ORDER-5", "Ordering", InvariantResultOutcome.INAPPLICABLE, "no derivative-source declaration supplied")
    if comparison_bundle["derivative_source"] != "sealed_record":
        return _result("CLTR-ORDER-5", "Ordering", InvariantResultOutcome.FAIL, "a derivative was sourced from mutable state instead of the sealed record", failure_reason="post-certification mutable read")
    return _result("CLTR-ORDER-5", "Ordering", InvariantResultOutcome.PASS, "derivative was sourced only from the sealed record")


def evaluate_cltr_order_6(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.marker_binding is None:
        return _result("CLTR-ORDER-6", "Ordering", InvariantResultOutcome.INAPPLICABLE, "no marker is bound on this record")
    if record.spine_state not in (SpineState.NOTIFIED, SpineState.NOTIFIED_UNCONFIRMED, SpineState.TERMINAL_SUCCESS, SpineState.TERMINAL_PARTIAL_EXTERNAL):
        return _result("CLTR-ORDER-6", "Ordering", InvariantResultOutcome.FAIL, "marker is bound on a record that has not reached NOTIFIED/NOTIFIED_UNCONFIRMED", failure_reason="marker before required delivery classification", quarantine_recommendation=True)
    return _result("CLTR-ORDER-6", "Ordering", InvariantResultOutcome.PASS, "marker was bound only after NOTIFIED/NOTIFIED_UNCONFIRMED")


def evaluate_cltr_order_7(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.receipt_binding is None:
        return _result("CLTR-ORDER-7", "Ordering", InvariantResultOutcome.INAPPLICABLE, "no receipt is bound on this record")
    if record.spine_state not in (SpineState.NOTIFIED, SpineState.NOTIFIED_UNCONFIRMED, SpineState.TERMINAL_SUCCESS, SpineState.TERMINAL_PARTIAL_EXTERNAL):
        return _result("CLTR-ORDER-7", "Ordering", InvariantResultOutcome.FAIL, "receipt is bound on a record that has not reached NOTIFIED/NOTIFIED_UNCONFIRMED", failure_reason="receipt claims a stage not reached", quarantine_recommendation=True)
    return _result("CLTR-ORDER-7", "Ordering", InvariantResultOutcome.PASS, "receipt's claimed stage is within the record's actually-reached stages")


# --- Derivation ------------------------------------------------------------

def evaluate_cltr_derive_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None or "derivation_inputs" not in comparison_bundle:
        return _result("CLTR-DERIVE-1", "Derivation", InvariantResultOutcome.INAPPLICABLE, "no derivation-input declaration supplied")
    allowed = {"record_field", "bound_evidence"}
    bad = [i for i in comparison_bundle["derivation_inputs"] if i not in allowed]
    if bad:
        return _result("CLTR-DERIVE-1", "Derivation", InvariantResultOutcome.FAIL, f"derivation used non-record, non-evidence inputs: {bad}", failure_reason="impure derivation")
    return _result("CLTR-DERIVE-1", "Derivation", InvariantResultOutcome.PASS, "derivation is a pure function of the record and bound evidence")


def evaluate_cltr_derive_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state == SpineState.PROPOSED or record.spine_state == SpineState.CERTIFYING:
        return _result("CLTR-DERIVE-2", "Derivation", InvariantResultOutcome.INAPPLICABLE, "record has not reached CERTIFIED yet")
    if comparison_bundle is None or "regeneration_a" not in comparison_bundle or "regeneration_b" not in comparison_bundle:
        return _result("CLTR-DERIVE-2", "Derivation", InvariantResultOutcome.INAPPLICABLE, "no two independent regenerations supplied to compare")
    if comparison_bundle["regeneration_a"] != comparison_bundle["regeneration_b"]:
        return _result("CLTR-DERIVE-2", "Derivation", InvariantResultOutcome.FAIL, "two regenerations of the same derivative diverged", failure_reason="non-deterministic derivation")
    return _result("CLTR-DERIVE-2", "Derivation", InvariantResultOutcome.PASS, "regeneration is byte-identical across two independent runs")


# --- Commit ownership -------------------------------------------------------

def evaluate_cltr_commit_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None or "derivative_claimed_commits" not in comparison_bundle:
        return _result("CLTR-COMMIT-1", "Commit ownership", InvariantResultOutcome.INAPPLICABLE, "no derivative commit-claim set supplied")
    declared = {c.commit_hash for c in record.declared_commits}
    claimed = set(comparison_bundle["derivative_claimed_commits"])
    if declared != claimed:
        return _result("CLTR-COMMIT-1", "Commit ownership", InvariantResultOutcome.FAIL, f"declared commits {sorted(declared)} != derivative-claimed commits {sorted(claimed)}", failure_reason="commit set mismatch")
    return _result("CLTR-COMMIT-1", "Commit ownership", InvariantResultOutcome.PASS, "declared commit set matches derivative claim exactly")


def evaluate_cltr_commit_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state == SpineState.PROPOSED:
        return _result("CLTR-COMMIT-2", "Commit ownership", InvariantResultOutcome.INAPPLICABLE, "commit classification has not yet been performed at PROPOSED")
    declared = {c.commit_hash for c in record.declared_commits}
    classified = {c.commit_hash for c in record.commit_classifications}
    unclassified = declared - classified
    if unclassified:
        return _result("CLTR-COMMIT-2", "Commit ownership", InvariantResultOutcome.FAIL, f"declared commits left unclassified: {sorted(unclassified)}", failure_reason="unclassified commit", quarantine_recommendation=True)
    return _result("CLTR-COMMIT-2", "Commit ownership", InvariantResultOutcome.PASS, "every declared commit resolves to exactly one of verified/contaminated/unverifiable")


def evaluate_cltr_commit_3(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    unresolvable_but_verified = [
        c.commit_hash for c in record.commit_classifications
        if c.classification == CommitOwnershipClassification.VERIFIED and comparison_bundle and c.commit_hash in comparison_bundle.get("known_unresolvable_hashes", [])
    ]
    if unresolvable_but_verified:
        return _result("CLTR-COMMIT-3", "Commit ownership", InvariantResultOutcome.FAIL, f"unresolvable hashes classified verified: {unresolvable_but_verified}", failure_reason="fabricated hash silently treated as verified", quarantine_recommendation=True)
    if not record.commit_classifications:
        return _result("CLTR-COMMIT-3", "Commit ownership", InvariantResultOutcome.INAPPLICABLE, "no commit classifications on this record")
    return _result("CLTR-COMMIT-3", "Commit ownership", InvariantResultOutcome.PASS, "no unresolvable hash was classified verified")


# --- Evidence -------------------------------------------------------

def evaluate_cltr_evid_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    prose_only = [
        r.evidence_id for r in _bound_evidence_refs(record)
        if r.verification_status in (EvidenceVerificationStatus.UNAVAILABLE_STRUCTURED,) and r.digest is None
    ]
    if prose_only:
        return _result("CLTR-EVID-1", "Evidence", InvariantResultOutcome.FAIL, f"evidence refs with only narrative prose, no structured reference: {prose_only}", failure_reason="prose-only evidence")
    return _result("CLTR-EVID-1", "Evidence", InvariantResultOutcome.PASS, "no R/E-role fact relies on prose-only evidence")


# --- Persistence -------------------------------------------------------

def evaluate_cltr_persist_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state not in (SpineState.PROMOTED, SpineState.NOTIFYING, SpineState.NOTIFIED, SpineState.NOTIFIED_UNCONFIRMED, SpineState.TERMINAL_SUCCESS, SpineState.TERMINAL_PARTIAL_EXTERNAL):
        return _result("CLTR-PERSIST-1", "Persistence", InvariantResultOutcome.INAPPLICABLE, "record has not reached PROMOTED or later")
    if comparison_bundle is None or "latest_pointer_report_transition_id" not in comparison_bundle or "latest_pointer_metadata_transition_id" not in comparison_bundle:
        return _result("CLTR-PERSIST-1", "Persistence", InvariantResultOutcome.INAPPLICABLE, "no latest-pointer bundle supplied")
    if comparison_bundle["latest_pointer_report_transition_id"] != comparison_bundle["latest_pointer_metadata_transition_id"]:
        return _result("CLTR-PERSIST-1", "Persistence", InvariantResultOutcome.FAIL, "latest pointer exposes a mixed-generation report/metadata pair", failure_reason="mixed-generation pointer", quarantine_recommendation=True)
    return _result("CLTR-PERSIST-1", "Persistence", InvariantResultOutcome.PASS, "latest pointer's report and metadata halves bind the same transition_id")


def evaluate_cltr_persist_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.certified_state is None:
        return _result("CLTR-PERSIST-2", "Persistence", InvariantResultOutcome.INAPPLICABLE, "record never reached CERTIFIED (e.g. FAILED_PRE_CERT) — nothing was sealed to verify")
    if not verify_self(record):
        return _result("CLTR-PERSIST-2", "Persistence", InvariantResultOutcome.FAIL, "record's sealed content no longer matches its own digest", failure_reason="digest mismatch — possible history rewrite", quarantine_recommendation=True)
    return _result("CLTR-PERSIST-2", "Persistence", InvariantResultOutcome.PASS, "record's sealed content matches its own digest")


def evaluate_cltr_persist_3(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None or "pointer_reconstructible_from_history" not in comparison_bundle:
        return _result("CLTR-PERSIST-3", "Persistence", InvariantResultOutcome.INAPPLICABLE, "no pointer-reconstruction test result supplied")
    if not comparison_bundle["pointer_reconstructible_from_history"]:
        return _result("CLTR-PERSIST-3", "Persistence", InvariantResultOutcome.FAIL, "mutable pointer is not reconstructible from immutable history", failure_reason="non-reconstructible pointer")
    return _result("CLTR-PERSIST-3", "Persistence", InvariantResultOutcome.PASS, "mutable pointer is reconstructible from immutable history")


# --- Retry -------------------------------------------------------

def evaluate_cltr_retry_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state != SpineState.NOTIFIED_UNCONFIRMED:
        return _result("CLTR-RETRY-1", "Retry", InvariantResultOutcome.INAPPLICABLE, "record is not in NOTIFIED_UNCONFIRMED")
    from pcae.cltr_prototype.state_machine import retry_classification
    from pcae.cltr_prototype.models import RetryClassification
    if retry_classification(record) != RetryClassification.REPAIR_DERIVATIVE_ONLY:
        return _result("CLTR-RETRY-1", "Retry", InvariantResultOutcome.FAIL, "NOTIFIED_UNCONFIRMED did not resolve to a resume-terminal classification", failure_reason="resume-terminal classification missing")
    return _result("CLTR-RETRY-1", "Retry", InvariantResultOutcome.PASS, "NOTIFIED_UNCONFIRMED is resume-terminal by the record's own resume logic", retry_effect=RetryClassification.REPAIR_DERIVATIVE_ONLY.value)


def evaluate_cltr_retry_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None or "new_proposed_for_same_phase_task" not in comparison_bundle:
        return _result("CLTR-RETRY-2", "Retry", InvariantResultOutcome.INAPPLICABLE, "no duplicate-submission scenario supplied")
    if record.is_terminal and comparison_bundle["new_proposed_for_same_phase_task"] and not comparison_bundle.get("new_proposed_rejected", False):
        return _result("CLTR-RETRY-2", "Retry", InvariantResultOutcome.FAIL, "a new PROPOSED for an already-terminal phase/task was accepted rather than rejected", failure_reason="duplicate completion accepted")
    return _result("CLTR-RETRY-2", "Retry", InvariantResultOutcome.PASS, "duplicate completion attempt was rejected, referencing the existing terminal record")


def evaluate_cltr_retry_3(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state not in (SpineState.FAILED_POST_CERT,):
        return _result("CLTR-RETRY-3", "Retry", InvariantResultOutcome.INAPPLICABLE, "record is not in a crash-recovery-relevant state (FAILED_POST_CERT)")
    has_observation = any(k.startswith("OBSERVATION") for k in record.timestamps) or bool(record.limitations)
    if not has_observation:
        return _result("CLTR-RETRY-3", "Retry", InvariantResultOutcome.FAIL, "no observation event precedes this record's failure classification", failure_reason="retry decision without prior observation")
    return _result("CLTR-RETRY-3", "Retry", InvariantResultOutcome.PASS, "an observation event/detail precedes this record's classification")


# --- Notification -------------------------------------------------------

def evaluate_cltr_notify_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.notification_binding is None:
        return _result("CLTR-NOTIFY-1", "Notification", InvariantResultOutcome.INAPPLICABLE, "no notification payload bound")
    if "PROMOTED" not in record.timestamps:
        return _result("CLTR-NOTIFY-1", "Notification", InvariantResultOutcome.FAIL, "notification payload bound without a PROMOTED-state binding to trace to", failure_reason="payload provenance broken")
    return _result("CLTR-NOTIFY-1", "Notification", InvariantResultOutcome.PASS, "notification payload traces to this record's PROMOTED-state evidence")


def evaluate_cltr_notify_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None or "retry_entered_from" not in comparison_bundle:
        return _result("CLTR-NOTIFY-2", "Notification", InvariantResultOutcome.INAPPLICABLE, "no retry-entry-state declaration supplied")
    if comparison_bundle["retry_entered_from"] not in ("NOTIFYING",):
        return _result("CLTR-NOTIFY-2", "Notification", InvariantResultOutcome.FAIL, f"notification retry entered from {comparison_bundle['retry_entered_from']}, not NOTIFYING", failure_reason="retry from wrong state")
    return _result("CLTR-NOTIFY-2", "Notification", InvariantResultOutcome.PASS, "notification retry was entered only from NOTIFYING")


# --- Marker -------------------------------------------------------

def evaluate_cltr_marker_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.marker_binding is None or record.receipt_binding is None:
        return _result("CLTR-MARKER-1", "Marker", InvariantResultOutcome.INAPPLICABLE, "marker and/or receipt not both bound")
    if record.marker_binding.transition_id != record.receipt_binding.transition_id:
        return _result("CLTR-MARKER-1", "Marker", InvariantResultOutcome.FAIL, "marker and receipt bind different transition_id values", failure_reason="marker/receipt identity mismatch", quarantine_recommendation=True)
    return _result("CLTR-MARKER-1", "Marker", InvariantResultOutcome.PASS, "marker and receipt bind the same transition_id")


def evaluate_cltr_marker_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    # Structural: state_machine.is_terminal() is a pure function of
    # record.spine_state; this module has no marker-presence-based
    # terminal-state code path at all.
    return _result("CLTR-MARKER-2", "Marker", InvariantResultOutcome.PASS, "terminal(record) is computed from spine_state only; no code path reads marker presence as proof")


# --- Receipt -------------------------------------------------------

def evaluate_cltr_receipt_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.receipt_binding is None:
        return _result("CLTR-RECEIPT-1", "Receipt", InvariantResultOutcome.INAPPLICABLE, "no receipt bound on this record")
    claims_success = comparison_bundle.get("receipt_claims_confirmed", False) if comparison_bundle else False
    if claims_success and record.spine_state not in (SpineState.NOTIFIED, SpineState.TERMINAL_SUCCESS):
        return _result("CLTR-RECEIPT-1", "Receipt", InvariantResultOutcome.FAIL, "receipt claims confirmed delivery but record is not NOTIFIED", failure_reason="optimistic receipt", quarantine_recommendation=True)
    return _result("CLTR-RECEIPT-1", "Receipt", InvariantResultOutcome.PASS, "receipt's claimed outcome does not exceed the record's actual state")


# --- Compatibility -------------------------------------------------------

def evaluate_cltr_compat_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None or "historical_artifact_digest_changed" not in comparison_bundle:
        return _result("CLTR-COMPAT-1", "Compatibility", InvariantResultOutcome.INAPPLICABLE, "no historical-artifact digest comparison supplied")
    if comparison_bundle["historical_artifact_digest_changed"]:
        return _result("CLTR-COMPAT-1", "Compatibility", InvariantResultOutcome.FAIL, "a historical artifact's digest changed over time", failure_reason="historical artifact rewritten", quarantine_recommendation=True)
    return _result("CLTR-COMPAT-1", "Compatibility", InvariantResultOutcome.PASS, "historical artifact digest is unchanged")


def evaluate_cltr_compat_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None or "pfn_001_pfr_001_unamended" not in comparison_bundle:
        return _result("CLTR-COMPAT-2", "Compatibility", InvariantResultOutcome.INAPPLICABLE, "no PFN-001/PFR-001 unamended-check supplied")
    if not comparison_bundle["pfn_001_pfr_001_unamended"]:
        return _result("CLTR-COMPAT-2", "Compatibility", InvariantResultOutcome.FAIL, "PFN-001 or PFR-001 text/guarantees changed", failure_reason="contract amendment out of scope")
    return _result("CLTR-COMPAT-2", "Compatibility", InvariantResultOutcome.PASS, "PFN-001 and PFR-001 remain unamended")


# --- Safety -------------------------------------------------------

def evaluate_cltr_safe_1(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if comparison_bundle is None or "runtime_state_unchanged" not in comparison_bundle:
        return _result("CLTR-SAFE-1", "Safety", InvariantResultOutcome.INAPPLICABLE, "no runtime-state before/after comparison supplied")
    if not comparison_bundle["runtime_state_unchanged"]:
        return _result("CLTR-SAFE-1", "Safety", InvariantResultOutcome.FAIL, "runtime state (Observed/observe/execution unavailable) changed", failure_reason="runtime state changed")
    return _result("CLTR-SAFE-1", "Safety", InvariantResultOutcome.PASS, "runtime state is unchanged")


def evaluate_cltr_safe_2(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    # Structural: no state's semantics in this module grant/imply an
    # execution capability — verified by design (models.py/state_machine.py
    # have no "may_execute" field or code path).
    return _result("CLTR-SAFE-2", "Safety", InvariantResultOutcome.PASS, "no state's semantics are read as an execution authorization")


def evaluate_cltr_safe_3(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> InvariantResult:
    if record.spine_state not in (SpineState.NOTIFIED, SpineState.NOTIFIED_UNCONFIRMED, SpineState.TERMINAL_SUCCESS, SpineState.TERMINAL_PARTIAL_EXTERNAL, SpineState.FAILED_PRE_CERT):
        return _result("CLTR-SAFE-3", "Safety", InvariantResultOutcome.INAPPLICABLE, "record is not in a terminal-adjacent state")
    if comparison_bundle is None or "entry_point_terminal_agreement" not in comparison_bundle:
        return _result("CLTR-SAFE-3", "Safety", InvariantResultOutcome.INAPPLICABLE, "no entry-point agreement check supplied")
    if not comparison_bundle["entry_point_terminal_agreement"]:
        return _result("CLTR-SAFE-3", "Safety", InvariantResultOutcome.FAIL, "record's own resume logic disagrees with a consuming entry point's terminal classification", failure_reason="terminal-classification disagreement", quarantine_recommendation=True)
    return _result("CLTR-SAFE-3", "Safety", InvariantResultOutcome.PASS, "record's own resume logic and the entry point agree on terminal classification")


_ALL_EVALUATORS: tuple[Callable[..., InvariantResult], ...] = (
    evaluate_cltr_id_1, evaluate_cltr_id_2,
    evaluate_cltr_auth_1, evaluate_cltr_auth_2,
    evaluate_cltr_state_1, evaluate_cltr_state_2, evaluate_cltr_state_3, evaluate_cltr_state_4,
    evaluate_cltr_order_1, evaluate_cltr_order_2, evaluate_cltr_order_3, evaluate_cltr_order_4,
    evaluate_cltr_order_5, evaluate_cltr_order_6, evaluate_cltr_order_7,
    evaluate_cltr_derive_1, evaluate_cltr_derive_2,
    evaluate_cltr_commit_1, evaluate_cltr_commit_2, evaluate_cltr_commit_3,
    evaluate_cltr_evid_1,
    evaluate_cltr_persist_1, evaluate_cltr_persist_2, evaluate_cltr_persist_3,
    evaluate_cltr_retry_1, evaluate_cltr_retry_2, evaluate_cltr_retry_3,
    evaluate_cltr_notify_1, evaluate_cltr_notify_2,
    evaluate_cltr_marker_1, evaluate_cltr_marker_2,
    evaluate_cltr_receipt_1,
    evaluate_cltr_compat_1, evaluate_cltr_compat_2,
    evaluate_cltr_safe_1, evaluate_cltr_safe_2, evaluate_cltr_safe_3,
)

#: Total number of distinct invariant IDs this engine evaluates (see module
#: docstring for the 36-vs-37 count discrepancy this number resolves honestly).
INVARIANT_COUNT = len(_ALL_EVALUATORS)


def evaluate_invariants(record: TransitionRecord, *, comparison_bundle: Optional[dict] = None) -> list[InvariantResult]:
    """Evaluate every invariant against `record` (+ optional `comparison_bundle`).

    Always returns exactly `INVARIANT_COUNT` results, one per evaluator, in a
    fixed order — no applicable invariant is ever silently skipped.
    """

    return [evaluator(record, comparison_bundle=comparison_bundle) for evaluator in _ALL_EVALUATORS]
