"""Standalone offline verifier (135E §3, §13, §26 Stage 5).

Re-checks a persisted candidate record independently of the process that
generated it: digest integrity, state validity, invariant outcomes,
conformance classification. Never repairs the record — a verification
failure is reported, never silently fixed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.cltr_prototype import persistence
from pcae.cltr_prototype.canonicalization import record_from_dict
from pcae.cltr_prototype.digest import verify_self
from pcae.cltr_prototype.invariants import InvariantResult, InvariantResultOutcome, evaluate_invariants
from pcae.cltr_prototype.models import (
    ALL_LIFECYCLE_STATE_NAMES,
    ConformanceClassification,
    SpineState,
    TransitionRecord,
)


class DigestFailureError(Exception):
    pass


@dataclass(frozen=True)
class VerificationReport:
    transition_id: str
    phase_id: str
    lifecycle_state: str
    manifest_consistent: bool
    digest_valid: bool
    state_valid: bool
    invariant_results: tuple
    conformance: str
    terminal: bool
    limitations: tuple


def _state_valid(record: TransitionRecord) -> bool:
    return record.spine_state.value in {s.value for s in SpineState}


def classify_conformance(record: TransitionRecord, invariant_results: list, *, digest_valid: bool, manifest_consistent: bool) -> ConformanceClassification:
    if record.superseded:
        return ConformanceClassification.SUPERSEDED
    if record.quarantined or not digest_valid:
        return ConformanceClassification.QUARANTINED
    blocking_fail = [r for r in invariant_results if r.outcome == InvariantResultOutcome.FAIL]
    if blocking_fail:
        conflict_like = [r for r in blocking_fail if "mismatch" in r.detail or "disagree" in r.detail or "conflict" in (r.failure_reason or "")]
        if conflict_like:
            return ConformanceClassification.CONFLICTING
        return ConformanceClassification.QUARANTINED
    unverifiable = [
        c for c in record.commit_classifications
        if c.classification.value == "unverifiable"
    ]
    if unverifiable:
        return ConformanceClassification.UNVERIFIABLE
    if record.compatibility_metadata.get("legacy_adapter_used"):
        return ConformanceClassification.CONFORMANT_WITH_LEGACY_ADAPTER
    incomplete_states = {SpineState.PROPOSED, SpineState.CERTIFYING}
    if record.spine_state in incomplete_states:
        return ConformanceClassification.INCOMPLETE
    return ConformanceClassification.CONFORMANT


def verify_record_object(record: TransitionRecord, *, manifest_consistent: bool = True) -> VerificationReport:
    """Verify an in-memory `TransitionRecord` value directly (no filesystem read)."""

    digest_valid = verify_self(record) if record.record_digest is not None else False
    state_valid = _state_valid(record)
    invariant_results = evaluate_invariants(record)
    conformance = classify_conformance(record, invariant_results, digest_valid=digest_valid, manifest_consistent=manifest_consistent)

    return VerificationReport(
        transition_id=record.identity.transition_id,
        phase_id=record.identity.phase_id,
        lifecycle_state=record.spine_state.value + ("+QUARANTINED" if record.quarantined else "") + ("+SUPERSEDED" if record.superseded else ""),
        manifest_consistent=manifest_consistent,
        digest_valid=digest_valid,
        state_valid=state_valid,
        invariant_results=tuple(invariant_results),
        conformance=conformance.value,
        terminal=record.is_terminal,
        limitations=record.limitations,
    )


def verify_record(transition_id: str, *, base_dir: Optional[Path] = None) -> VerificationReport:
    """Verify a persisted generation by transition_id, reading only from
    `.pcae/cltr-prototypes/generations/<transition_id>/` (never a live scan
    of anything else)."""

    manifest_consistent = persistence._manifest_is_consistent(persistence._generations_dir(base_dir) / transition_id)  # noqa: SLF001
    record_dict = persistence.read_generation(transition_id, base_dir=base_dir)
    if record_dict is None:
        return VerificationReport(
            transition_id=transition_id,
            phase_id="",
            lifecycle_state="UNKNOWN",
            manifest_consistent=False,
            digest_valid=False,
            state_valid=False,
            invariant_results=(),
            conformance=ConformanceClassification.UNVERIFIABLE.value,
            terminal=False,
            limitations=("generation directory missing or incomplete",),
        )
    record = record_from_dict(record_dict)
    return verify_record_object(record, manifest_consistent=manifest_consistent)
