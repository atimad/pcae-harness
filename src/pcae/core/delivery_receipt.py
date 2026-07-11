"""Phase 134E.7: External Delivery Receipt Model.

Implements a deterministic, durable, transport-neutral External
Delivery Receipt model that records what delivery was intended, what
physical attempts occurred, what succeeded, what failed, and what the
authoritative delivery state is -- built entirely on top of the
verified Delivery Pipeline (134E.6, independently verified and
repaired by 134E.6V).

**This module is not yet active lifecycle authority.** Nothing in the
current governed reporting/finalization/notification path imports or
calls into this module. The current production Telegram delivery,
``pcae phase complete``, and PFN-001 dispatch remain entirely
unaffected and unchanged. No production receipt artifact is created by
this phase; persistence is exercised only against caller-supplied
(test) roots.

Architectural position (preserved, not merged):

    Canonical Engineering Evidence
            |
            v
    Derived Evidence Views
            |
            v
    RenderingResult
            |
            v
    Delivery Pipeline
            |
            v
    DeliveryExecutionResult
            |
            v
    External Delivery Receipt Model      <- this module
            |
            v
    Final Lifecycle Integration          (134E.10, not implemented)

This module consumes only ``DeliveryExecutionResult``, ``DeliveryPlan``,
and ``DeliveryRequest`` -- it never imports the canonical evidence
model, the extraction layer, either derived-view composition module,
or the rendering layer directly.

Authority boundary: receipts are authoritative only for delivery
history and delivery state. They are never authoritative for
engineering facts, report content, repository state, runtime state,
phase identity, phase completion, architectural findings, test
results, or governance results.

Logical versus physical exactly-once: this module guarantees one
logical delivery identity maps to exactly one receipt lineage and one
final logical state. It does **not** claim physically exactly-once
delivery -- a stateless pipeline layered on top of adapters that may
fail ambiguously can and does record multiple physical attempts, and
those attempts are preserved individually, never collapsed into a
single "it happened once" claim.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from pcae.core.delivery_pipeline import (
    DeliveryExecutionResult,
    DeliveryOutcome,
    DeliveryPlan,
    DeliveryRequest,
    RetryRecommendation,
    get_adapter,
)

# ═══════════════════════════════════════════════════════════════════════
# Storage layout convention (documented, not auto-instantiated)
# ═══════════════════════════════════════════════════════════════════════

#: Default storage root -- transport-neutral, grouped by logical
#: delivery identity, never by adapter/channel name (no ``telegram/``
#: directory). Nothing in this phase writes to this path automatically;
#: production activation is out of scope (134E.7's own non-goals).
DEFAULT_RECEIPT_STORE_ROOT = ".pcae/delivery-receipts"

RECEIPT_SCHEMA_VERSION = "1.0"


# ═══════════════════════════════════════════════════════════════════════
# Vocabulary
# ═══════════════════════════════════════════════════════════════════════


class LogicalDeliveryState(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    PARTIALLY_DELIVERED = "partially_delivered"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_NON_RETRYABLE = "failed_non_retryable"
    BLOCKED_BY_AUTHORIZATION = "blocked_by_authorization"
    DISABLED_BY_POLICY = "disabled_by_policy"
    INVALID = "invalid"
    SUPERSEDED = "superseded"
    CORRECTED = "corrected"


class UnitOutcomeState(str, Enum):
    DELIVERED = "delivered"
    FAILED = "failed"
    AMBIGUOUS = "ambiguous"
    NOT_ATTEMPTED = "not_attempted"


class OperatorCompletenessState(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    INVALID = "invalid"


class CorrectionDirection(str, Enum):
    CORRECTS = "corrects"
    SUPERSEDES = "supersedes"


_NEVER_DELIVERED_STATES = frozenset({
    LogicalDeliveryState.PENDING, LogicalDeliveryState.PARTIALLY_DELIVERED,
    LogicalDeliveryState.FAILED_RETRYABLE, LogicalDeliveryState.FAILED_NON_RETRYABLE,
    LogicalDeliveryState.BLOCKED_BY_AUTHORIZATION, LogicalDeliveryState.DISABLED_BY_POLICY,
    LogicalDeliveryState.INVALID,
})


# ═══════════════════════════════════════════════════════════════════════
# Secret / diagnostic redaction (134E.6V NON-BLOCKING observation)
# ═══════════════════════════════════════════════════════════════════════
#
# Bounded, defense-in-depth redaction of persisted diagnostic text.
# Not a universal secret scanner -- explicit known-sensitive shapes
# only, mirroring the conventions already established by
# ``canonical_engineering_evidence._contains_likely_secret`` (Telegram
# bot-token shape, ``PCAE_*_TOKEN=`` assignments) and
# ``shell_gate._redact_command_text`` (env-var assignments, ``--flag``
# secrets, ``Authorization: Bearer`` headers).

_SENSITIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\b(bot_?token|api[_-]?key|secret|password|passwd|access[_-]?key|"
               r"private[_-]?key|secret[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)authorization:\s*bearer\s+\S+"),
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{25,}\b"),  # Telegram bot-token shape
    re.compile(r"PCAE_[A-Z_]*(TOKEN|SECRET|KEY|PASSWORD|CHAT_ID)\s*[:=]\s*\S+"),
    re.compile(r"https?://\S+"),  # any URL -- may embed webhook secrets in query strings
)

_MAX_DIAGNOSTIC_LEN = 200

_EXCEPTION_ERROR_CLASS_MAP: dict[str, str] = {
    "TimeoutError": "timeout",
    "ConnectionError": "connection_error",
    "ConnectionResetError": "connection_error",
    "BrokenPipeError": "connection_error",
    "OSError": "transport_error",
    "RuntimeError": "adapter_runtime_error",
    "ValueError": "adapter_value_error",
}

_ADAPTER_EXCEPTION_PREFIX = re.compile(r"^adapter raised (\w+): (.*)$", re.DOTALL)


def _redact(text: str) -> str:
    redacted = text
    for pattern in _SENSITIVE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _sanitize_diagnostic(raw: str | None) -> tuple[str | None, str | None]:
    """Returns ``(bounded_sanitized_message, stable_diagnostic_code)``.

    Never persists the raw adapter/exception text verbatim. If the text
    matches the ``execute_delivery()``-normalized adapter-exception
    shape (``"adapter raised <ExceptionType>: <message>"``), only the
    exception's class-derived category and a bounded, redacted message
    are kept -- never the raw exception representation.
    """
    if raw is None:
        return None, None
    match = _ADAPTER_EXCEPTION_PREFIX.match(raw)
    if match:
        exc_name, msg = match.group(1), match.group(2)
        category = _EXCEPTION_ERROR_CLASS_MAP.get(exc_name, "adapter_exception")
        bounded = _redact(msg)[:_MAX_DIAGNOSTIC_LEN]
        code = f"adapter_exception:{category}"
        summary = f"{category}: {bounded}" if bounded else category
        return summary, code
    bounded = _redact(raw)[:_MAX_DIAGNOSTIC_LEN]
    return bounded, "adapter_reported_failure"


# ═══════════════════════════════════════════════════════════════════════
# Deterministic identity helpers
# ═══════════════════════════════════════════════════════════════════════


def compute_receipt_id(logical_delivery_id: str, receipt_version: str = RECEIPT_SCHEMA_VERSION) -> str:
    """Deterministic receipt identity derived only from the logical
    delivery identity and the receipt model version -- never from
    mutable attempt state (timestamps, attempt count, adapter response
    IDs). The same logical delivery always maps to the same receipt
    identity, spanning every attempt recorded against it.
    """
    payload = json.dumps([logical_delivery_id, receipt_version])
    return hashlib.sha256(payload.encode()).hexdigest()


def compute_attempt_id(logical_delivery_id: str, attempt_sequence: int) -> str:
    """Deterministic attempt identity from logical delivery identity
    and attempt sequence -- canonical structured serialization, never
    ambiguous delimiter concatenation (the exact class of defect
    134E.6V found and repaired in ``compute_logical_delivery_id``).
    """
    payload = json.dumps([logical_delivery_id, attempt_sequence])
    return hashlib.sha256(payload.encode()).hexdigest()


def _plan_digest(plan: DeliveryPlan) -> str:
    payload = json.dumps(plan.to_dict(), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _digest_excluding(data: dict[str, Any], exclude_key: str) -> str:
    trimmed = {k: v for k, v in data.items() if k != exclude_key}
    payload = json.dumps(trimmed, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _parse_ts(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid timestamp {value!r}: must be ISO 8601") from exc


# ═══════════════════════════════════════════════════════════════════════
# Per-unit outcome record
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class UnitOutcomeRecord:
    unit_id: str
    unit_index: int
    unit_total: int
    mode: str
    content_hash: str
    attempted: bool
    outcome: str  # UnitOutcomeState value
    retryable: bool
    adapter_response_ref: str | None
    error_classification: str | None
    diagnostic_summary: str | None
    uncertainty: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "uncertainty", tuple(self.uncertainty))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id, "unit_index": self.unit_index,
            "unit_total": self.unit_total, "mode": self.mode,
            "content_hash": self.content_hash, "attempted": self.attempted,
            "outcome": self.outcome, "retryable": self.retryable,
            "adapter_response_ref": self.adapter_response_ref,
            "error_classification": self.error_classification,
            "diagnostic_summary": self.diagnostic_summary,
            "uncertainty": list(self.uncertainty), "limitations": list(self.limitations),
        }


def _unit_outcome_from_dict(data: dict[str, Any]) -> UnitOutcomeRecord:
    return UnitOutcomeRecord(
        unit_id=data["unit_id"], unit_index=data["unit_index"], unit_total=data["unit_total"],
        mode=data["mode"], content_hash=data["content_hash"], attempted=data["attempted"],
        outcome=data["outcome"], retryable=data["retryable"],
        adapter_response_ref=data.get("adapter_response_ref"),
        error_classification=data.get("error_classification"),
        diagnostic_summary=data.get("diagnostic_summary"),
        uncertainty=tuple(data.get("uncertainty", ())),
        limitations=tuple(data.get("limitations", ())),
    )


# ═══════════════════════════════════════════════════════════════════════
# Physical delivery attempt
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DeliveryAttemptRecord:
    attempt_id: str
    logical_delivery_id: str
    attempt_sequence: int
    plan_digest: str
    rendering_digest: str
    adapter_id: str
    adapter_version: str
    destination_classification: str
    policy_version: str
    requested_unit_ids: tuple[str, ...]
    attempted_unit_ids: tuple[str, ...]
    unit_outcomes: tuple[UnitOutcomeRecord, ...]
    overall_outcome: str  # DeliveryOutcome value
    retryable: bool
    started_at: str
    completed_at: str
    retry_of: str | None
    retry_reason: str | None
    diagnostics: tuple[str, ...]
    uncertainty: tuple[str, ...]
    limitations: tuple[str, ...]
    attempt_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_unit_ids", tuple(self.requested_unit_ids))
        object.__setattr__(self, "attempted_unit_ids", tuple(self.attempted_unit_ids))
        object.__setattr__(self, "unit_outcomes", tuple(self.unit_outcomes))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
        object.__setattr__(self, "uncertainty", tuple(self.uncertainty))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id, "logical_delivery_id": self.logical_delivery_id,
            "attempt_sequence": self.attempt_sequence, "plan_digest": self.plan_digest,
            "rendering_digest": self.rendering_digest, "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "destination_classification": self.destination_classification,
            "policy_version": self.policy_version,
            "requested_unit_ids": list(self.requested_unit_ids),
            "attempted_unit_ids": list(self.attempted_unit_ids),
            "unit_outcomes": [u.to_dict() for u in self.unit_outcomes],
            "overall_outcome": self.overall_outcome, "retryable": self.retryable,
            "started_at": self.started_at, "completed_at": self.completed_at,
            "retry_of": self.retry_of, "retry_reason": self.retry_reason,
            "diagnostics": list(self.diagnostics), "uncertainty": list(self.uncertainty),
            "limitations": list(self.limitations), "attempt_digest": self.attempt_digest,
        }


def _attempt_from_dict(data: dict[str, Any]) -> DeliveryAttemptRecord:
    return DeliveryAttemptRecord(
        attempt_id=data["attempt_id"], logical_delivery_id=data["logical_delivery_id"],
        attempt_sequence=data["attempt_sequence"], plan_digest=data["plan_digest"],
        rendering_digest=data["rendering_digest"], adapter_id=data["adapter_id"],
        adapter_version=data["adapter_version"],
        destination_classification=data["destination_classification"],
        policy_version=data["policy_version"],
        requested_unit_ids=tuple(data.get("requested_unit_ids", ())),
        attempted_unit_ids=tuple(data.get("attempted_unit_ids", ())),
        unit_outcomes=tuple(_unit_outcome_from_dict(u) for u in data.get("unit_outcomes", ())),
        overall_outcome=data["overall_outcome"], retryable=data["retryable"],
        started_at=data["started_at"], completed_at=data["completed_at"],
        retry_of=data.get("retry_of"), retry_reason=data.get("retry_reason"),
        diagnostics=tuple(data.get("diagnostics", ())),
        uncertainty=tuple(data.get("uncertainty", ())),
        limitations=tuple(data.get("limitations", ())),
        attempt_digest=data["attempt_digest"],
    )


def build_attempt(
    execution_result: DeliveryExecutionResult, plan: DeliveryPlan, request: DeliveryRequest,
    *, sequence: int, started_at: str, completed_at: str,
    previous_attempt: DeliveryAttemptRecord | None = None,
    retry_reason: str | None = None,
    ambiguous_unit_ids: frozenset[str] = frozenset(),
) -> DeliveryAttemptRecord:
    """Build a ``DeliveryAttemptRecord`` from a validated
    ``DeliveryExecutionResult``/``DeliveryPlan``/``DeliveryRequest``
    triple. Fails closed on any identity or sequence inconsistency.

    ``ambiguous_unit_ids`` lets a caller with adapter-specific knowledge
    (e.g. a timeout that may have completed the external side effect
    before failing) mark specific units as ambiguous rather than
    failed -- ``execute_delivery()`` itself has no ambiguous vocabulary,
    so this distinction is made at the receipt layer, never invented
    inside the generic pipeline.
    """
    if not (execution_result.logical_delivery_id == plan.logical_delivery_id == request.logical_delivery_id):
        raise ValueError(
            "build_attempt: execution_result/plan/request reference different "
            "logical deliveries"
        )
    if not (plan.rendering_digest == request.rendering_digest == execution_result.rendering_digest):
        raise ValueError("build_attempt: rendering digest mismatch across pipeline inputs")
    if sequence < 1:
        raise ValueError("build_attempt: attempt_sequence must be >= 1")
    start_ts = _parse_ts(started_at)
    end_ts = _parse_ts(completed_at)
    if end_ts < start_ts:
        raise ValueError("build_attempt: completed_at cannot precede started_at")

    if previous_attempt is not None:
        if previous_attempt.logical_delivery_id != request.logical_delivery_id:
            raise ValueError(
                "build_attempt: previous_attempt belongs to a different logical delivery"
            )
        if sequence != previous_attempt.attempt_sequence + 1:
            raise ValueError(
                f"build_attempt: attempt_sequence must increment by exactly one from the "
                f"previous attempt ({previous_attempt.attempt_sequence} -> {sequence} rejected; "
                "duplicate and missing-intermediate sequence numbers are both rejected)"
            )
        if request.adapter_id != previous_attempt.adapter_id:
            raise ValueError("build_attempt: retry cannot change adapter under the same lineage")
        if request.destination_classification.value != previous_attempt.destination_classification:
            raise ValueError(
                "build_attempt: retry cannot change destination classification under the same lineage"
            )
        if request.policy_version != previous_attempt.policy_version:
            raise ValueError("build_attempt: retry cannot change policy version under the same lineage")
        if start_ts < _parse_ts(previous_attempt.completed_at):
            raise ValueError(
                "build_attempt: attempt cannot start before the previous attempt completed "
                "(attempt ordering contradiction)"
            )

    plan_unit_ids = {u.unit_id for u in plan.units}
    unknown_ambiguous = ambiguous_unit_ids - plan_unit_ids
    if unknown_ambiguous:
        raise ValueError(f"build_attempt: ambiguous_unit_ids not present in plan: {sorted(unknown_ambiguous)}")

    outcome_by_unit = {o.unit_id: o for o in execution_result.unit_outcomes}
    default_retryable = execution_result.retry_recommendation == RetryRecommendation.RETRY_RECOMMENDED

    unit_records: list[UnitOutcomeRecord] = []
    for unit in plan.units:
        adapter_outcome = outcome_by_unit.get(unit.unit_id)
        if adapter_outcome is None:
            state = UnitOutcomeState.NOT_ATTEMPTED
            retryable = default_retryable
            adapter_response_ref = None
            diagnostic_summary, error_classification = None, None
        elif unit.unit_id in ambiguous_unit_ids:
            state = UnitOutcomeState.AMBIGUOUS
            retryable = adapter_outcome.retryable
            adapter_response_ref = adapter_outcome.adapter_response_ref
            diagnostic_summary, error_classification = _sanitize_diagnostic(adapter_outcome.diagnostic)
        elif adapter_outcome.delivered:
            state = UnitOutcomeState.DELIVERED
            retryable = False
            adapter_response_ref = adapter_outcome.adapter_response_ref
            diagnostic_summary, error_classification = None, None
        else:
            state = UnitOutcomeState.FAILED
            retryable = adapter_outcome.retryable
            adapter_response_ref = adapter_outcome.adapter_response_ref
            diagnostic_summary, error_classification = _sanitize_diagnostic(adapter_outcome.diagnostic)

        unit_uncertainty = ("ambiguous_external_outcome",) if state == UnitOutcomeState.AMBIGUOUS else ()
        unit_records.append(UnitOutcomeRecord(
            unit_id=unit.unit_id, unit_index=unit.index, unit_total=unit.total,
            mode=plan.selected_mode.value, content_hash=unit.content_hash,
            attempted=state != UnitOutcomeState.NOT_ATTEMPTED, outcome=state.value,
            retryable=retryable, adapter_response_ref=adapter_response_ref,
            error_classification=error_classification, diagnostic_summary=diagnostic_summary,
            uncertainty=unit_uncertainty, limitations=(),
        ))

    diagnostics = tuple(_redact(f"{d.code}: {d.message}") for d in execution_result.diagnostics)
    uncertainty: list[str] = []
    if request.has_uncertainty:
        uncertainty.append("source_rendering_reported_uncertainty")
    uncertainty.extend(f"ambiguous_external_outcome:{uid}" for uid in sorted(ambiguous_unit_ids))
    limitations: list[str] = []
    if request.has_limitations:
        limitations.append("source_rendering_reported_limitations")

    attempted_ids = tuple(u.unit_id for u in unit_records if u.attempted)
    attempt_id = compute_attempt_id(request.logical_delivery_id, sequence)
    retryable = default_retryable

    base = {
        "attempt_id": attempt_id, "logical_delivery_id": request.logical_delivery_id,
        "attempt_sequence": sequence, "plan_digest": _plan_digest(plan),
        "rendering_digest": request.rendering_digest, "adapter_id": request.adapter_id,
        "adapter_version": request.adapter_version,
        "destination_classification": request.destination_classification.value,
        "policy_version": request.policy_version,
        "requested_unit_ids": [u.unit_id for u in plan.units],
        "attempted_unit_ids": list(attempted_ids),
        "unit_outcomes": [u.to_dict() for u in unit_records],
        "overall_outcome": execution_result.overall_outcome.value, "retryable": retryable,
        "started_at": started_at, "completed_at": completed_at,
        "retry_of": previous_attempt.attempt_id if previous_attempt else None,
        "retry_reason": retry_reason, "diagnostics": list(diagnostics),
        "uncertainty": uncertainty, "limitations": limitations,
    }
    digest = _digest_excluding(base, "attempt_digest")

    return DeliveryAttemptRecord(
        attempt_id=attempt_id, logical_delivery_id=request.logical_delivery_id,
        attempt_sequence=sequence, plan_digest=base["plan_digest"],
        rendering_digest=request.rendering_digest, adapter_id=request.adapter_id,
        adapter_version=request.adapter_version,
        destination_classification=request.destination_classification.value,
        policy_version=request.policy_version, requested_unit_ids=tuple(base["requested_unit_ids"]),
        attempted_unit_ids=attempted_ids, unit_outcomes=tuple(unit_records),
        overall_outcome=execution_result.overall_outcome.value, retryable=retryable,
        started_at=started_at, completed_at=completed_at,
        retry_of=base["retry_of"], retry_reason=retry_reason,
        diagnostics=diagnostics, uncertainty=tuple(uncertainty), limitations=tuple(limitations),
        attempt_digest=digest,
    )


# ═══════════════════════════════════════════════════════════════════════
# Correction / supersession
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CorrectionRecord:
    original_receipt_id: str
    reason: str
    correcting_receipt_id: str
    direction: str  # CorrectionDirection value
    affected_logical_delivery_id: str
    operator_followup_occurred: bool

    def __post_init__(self) -> None:
        if not self.original_receipt_id:
            raise ValueError("CorrectionRecord.original_receipt_id must be non-empty")
        if not self.correcting_receipt_id:
            raise ValueError("CorrectionRecord.correcting_receipt_id must be non-empty")
        if not self.reason:
            raise ValueError("CorrectionRecord.reason must be non-empty")
        if self.original_receipt_id == self.correcting_receipt_id:
            raise ValueError(
                "a receipt cannot correct/supersede itself (correction cycle rejected)"
            )
        if self.direction not in (CorrectionDirection.CORRECTS.value, CorrectionDirection.SUPERSEDES.value):
            raise ValueError(f"invalid correction direction: {self.direction!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_receipt_id": self.original_receipt_id, "reason": self.reason,
            "correcting_receipt_id": self.correcting_receipt_id, "direction": self.direction,
            "affected_logical_delivery_id": self.affected_logical_delivery_id,
            "operator_followup_occurred": self.operator_followup_occurred,
        }


def _correction_from_dict(data: dict[str, Any] | None) -> CorrectionRecord | None:
    if data is None:
        return None
    return CorrectionRecord(
        original_receipt_id=data["original_receipt_id"], reason=data["reason"],
        correcting_receipt_id=data["correcting_receipt_id"], direction=data["direction"],
        affected_logical_delivery_id=data["affected_logical_delivery_id"],
        operator_followup_occurred=data["operator_followup_occurred"],
    )


# ═══════════════════════════════════════════════════════════════════════
# Aggregate derivation
# ═══════════════════════════════════════════════════════════════════════


def _latest_unit_states(attempts: tuple[DeliveryAttemptRecord, ...]) -> dict[str, UnitOutcomeRecord]:
    """Last-attempt-wins per unit id -- a unit delivered on a later
    retry is counted once as delivered; earlier failed attempts remain
    visible in attempt history but never double-count the unit.
    """
    latest: dict[str, UnitOutcomeRecord] = {}
    for attempt in attempts:
        for u in attempt.unit_outcomes:
            latest[u.unit_id] = u
    return latest


def _derive_logical_state(
    attempts: tuple[DeliveryAttemptRecord, ...], correction: CorrectionRecord | None,
    delivered: int, failed_retryable: int, failed_non_retryable: int, ambiguous: int,
    total_planned_units: int,
) -> LogicalDeliveryState:
    if correction is not None:
        return (
            LogicalDeliveryState.CORRECTED if correction.direction == CorrectionDirection.CORRECTS.value
            else LogicalDeliveryState.SUPERSEDED
        )
    if not attempts:
        return LogicalDeliveryState.PENDING
    latest_outcome = attempts[-1].overall_outcome
    if latest_outcome == DeliveryOutcome.BLOCKED_BY_AUTHORIZATION.value:
        return LogicalDeliveryState.BLOCKED_BY_AUTHORIZATION
    if latest_outcome == DeliveryOutcome.DISABLED_BY_POLICY.value:
        return LogicalDeliveryState.DISABLED_BY_POLICY
    if latest_outcome in (DeliveryOutcome.INVALID_PLAN.value, DeliveryOutcome.UNSUPPORTED.value):
        return LogicalDeliveryState.INVALID
    if total_planned_units > 0 and delivered == total_planned_units:
        return LogicalDeliveryState.DELIVERED
    if delivered > 0:
        return LogicalDeliveryState.PARTIALLY_DELIVERED
    if ambiguous > 0 and failed_retryable == 0 and failed_non_retryable == 0:
        return LogicalDeliveryState.PENDING
    if failed_retryable > 0:
        return LogicalDeliveryState.FAILED_RETRYABLE
    if failed_non_retryable > 0:
        return LogicalDeliveryState.FAILED_NON_RETRYABLE
    return LogicalDeliveryState.PENDING


def _derive_operator_completeness(
    logical_state: LogicalDeliveryState, delivered: int, ambiguous: int,
) -> OperatorCompletenessState:
    if logical_state == LogicalDeliveryState.DELIVERED:
        return OperatorCompletenessState.COMPLETE
    if logical_state == LogicalDeliveryState.INVALID:
        return OperatorCompletenessState.INVALID
    if ambiguous > 0:
        return OperatorCompletenessState.UNKNOWN
    if logical_state == LogicalDeliveryState.PENDING:
        return OperatorCompletenessState.UNKNOWN
    # partially_delivered, failed_retryable, failed_non_retryable, blocked,
    # disabled, superseded, corrected: definite, but not complete.
    return OperatorCompletenessState.PARTIAL


@dataclass(frozen=True)
class _Aggregate:
    logical_state: LogicalDeliveryState
    delivered: int
    failed_retryable: int
    failed_non_retryable: int
    ambiguous: int
    not_attempted: int
    attempted_unit_count: int
    retry_pending: bool
    operator_completeness: OperatorCompletenessState
    first_attempt_at: str | None
    latest_attempt_at: str | None
    combined_uncertainty: tuple[str, ...]
    combined_limitations: tuple[str, ...]
    combined_diagnostics: tuple[str, ...]


def _aggregate(
    attempts: tuple[DeliveryAttemptRecord, ...], correction: CorrectionRecord | None,
    total_planned_units: int,
) -> _Aggregate:
    latest = _latest_unit_states(attempts)
    delivered = sum(1 for u in latest.values() if u.outcome == UnitOutcomeState.DELIVERED.value)
    failed_retryable = sum(
        1 for u in latest.values() if u.outcome == UnitOutcomeState.FAILED.value and u.retryable
    )
    failed_non_retryable = sum(
        1 for u in latest.values() if u.outcome == UnitOutcomeState.FAILED.value and not u.retryable
    )
    ambiguous = sum(1 for u in latest.values() if u.outcome == UnitOutcomeState.AMBIGUOUS.value)
    not_attempted = sum(1 for u in latest.values() if u.outcome == UnitOutcomeState.NOT_ATTEMPTED.value)
    attempted_unit_count = len(latest) - not_attempted

    logical_state = _derive_logical_state(
        attempts, correction, delivered, failed_retryable, failed_non_retryable, ambiguous,
        total_planned_units,
    )
    operator_completeness = _derive_operator_completeness(logical_state, delivered, ambiguous)
    retry_pending = correction is None and (failed_retryable > 0 or ambiguous > 0)

    uncertainty: list[str] = []
    limitations: list[str] = []
    diagnostics: list[str] = []
    for a in attempts:
        for item in a.uncertainty:
            if item not in uncertainty:
                uncertainty.append(item)
        for item in a.limitations:
            if item not in limitations:
                limitations.append(item)
        for item in a.diagnostics:
            if item not in diagnostics:
                diagnostics.append(item)

    return _Aggregate(
        logical_state=logical_state, delivered=delivered, failed_retryable=failed_retryable,
        failed_non_retryable=failed_non_retryable, ambiguous=ambiguous, not_attempted=not_attempted,
        attempted_unit_count=attempted_unit_count, retry_pending=retry_pending,
        operator_completeness=operator_completeness,
        first_attempt_at=attempts[0].started_at if attempts else None,
        latest_attempt_at=attempts[-1].completed_at if attempts else None,
        combined_uncertainty=tuple(uncertainty), combined_limitations=tuple(limitations),
        combined_diagnostics=tuple(diagnostics),
    )


def pending_retry_unit_ids(receipt: "ExternalDeliveryReceipt") -> tuple[str, ...]:
    """Read-only inspection: unit ids whose latest recorded state is a
    retryable failure (never automatically includes ambiguous units --
    those require explicit governed retry authorization, per this
    phase's own "do not automatically retry ambiguous units" rule).
    """
    latest = _latest_unit_states(receipt.attempts)
    return tuple(
        uid for uid, u in sorted(latest.items())
        if u.outcome == UnitOutcomeState.FAILED.value and u.retryable
    )


# ═══════════════════════════════════════════════════════════════════════
# External Delivery Receipt
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ExternalDeliveryReceipt:
    receipt_id: str
    receipt_version: str
    logical_delivery_id: str
    phase_id: str
    delivery_purpose: str
    rendering_view_id: str
    rendering_digest: str
    renderer_id: str
    renderer_version: str
    adapter_id: str
    adapter_version: str
    destination_classification: str
    safe_destination_alias: str
    policy_version: str
    delivery_mode: str
    logical_state: str
    attempts: tuple[DeliveryAttemptRecord, ...]
    total_planned_units: int
    attempted_unit_count: int
    delivered_unit_count: int
    failed_unit_count: int
    pending_unit_count: int
    retryable_failed_unit_count: int
    non_retryable_failed_unit_count: int
    ambiguous_unit_count: int
    partial_delivery: bool
    retry_pending: bool
    operator_completeness: str
    first_attempt_at: str | None
    latest_attempt_at: str | None
    finalized_at: str | None
    finalized: bool
    diagnostics: tuple[str, ...]
    uncertainty: tuple[str, ...]
    limitations: tuple[str, ...]
    correction: CorrectionRecord | None
    provenance: Mapping[str, Any]
    authorization_evidence: Mapping[str, Any]
    receipt_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempts", tuple(self.attempts))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
        object.__setattr__(self, "uncertainty", tuple(self.uncertainty))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        # Deep immutability: nested dicts become read-only views, not
        # merely relying on the outer frozen dataclass.
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))
        object.__setattr__(self, "authorization_evidence", MappingProxyType(dict(self.authorization_evidence)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id, "receipt_version": self.receipt_version,
            "logical_delivery_id": self.logical_delivery_id, "phase_id": self.phase_id,
            "delivery_purpose": self.delivery_purpose, "rendering_view_id": self.rendering_view_id,
            "rendering_digest": self.rendering_digest, "renderer_id": self.renderer_id,
            "renderer_version": self.renderer_version, "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "destination_classification": self.destination_classification,
            "safe_destination_alias": self.safe_destination_alias,
            "policy_version": self.policy_version, "delivery_mode": self.delivery_mode,
            "logical_state": self.logical_state,
            "attempts": [a.to_dict() for a in self.attempts],
            "total_planned_units": self.total_planned_units,
            "attempted_unit_count": self.attempted_unit_count,
            "delivered_unit_count": self.delivered_unit_count,
            "failed_unit_count": self.failed_unit_count,
            "pending_unit_count": self.pending_unit_count,
            "retryable_failed_unit_count": self.retryable_failed_unit_count,
            "non_retryable_failed_unit_count": self.non_retryable_failed_unit_count,
            "ambiguous_unit_count": self.ambiguous_unit_count,
            "partial_delivery": self.partial_delivery, "retry_pending": self.retry_pending,
            "operator_completeness": self.operator_completeness,
            "first_attempt_at": self.first_attempt_at, "latest_attempt_at": self.latest_attempt_at,
            "finalized_at": self.finalized_at, "finalized": self.finalized,
            "diagnostics": list(self.diagnostics), "uncertainty": list(self.uncertainty),
            "limitations": list(self.limitations),
            "correction": self.correction.to_dict() if self.correction else None,
            "provenance": dict(self.provenance),
            "authorization_evidence": dict(self.authorization_evidence),
            "receipt_digest": self.receipt_digest,
        }


def _receipt_from_dict(data: dict[str, Any], *, verify_digest: bool = True) -> ExternalDeliveryReceipt:
    version = data.get("receipt_version")
    if version != RECEIPT_SCHEMA_VERSION:
        raise ValueError(f"unsupported receipt schema version: {version!r}")
    receipt = ExternalDeliveryReceipt(
        receipt_id=data["receipt_id"], receipt_version=data["receipt_version"],
        logical_delivery_id=data["logical_delivery_id"], phase_id=data["phase_id"],
        delivery_purpose=data["delivery_purpose"], rendering_view_id=data["rendering_view_id"],
        rendering_digest=data["rendering_digest"], renderer_id=data["renderer_id"],
        renderer_version=data["renderer_version"], adapter_id=data["adapter_id"],
        adapter_version=data["adapter_version"],
        destination_classification=data["destination_classification"],
        safe_destination_alias=data["safe_destination_alias"], policy_version=data["policy_version"],
        delivery_mode=data["delivery_mode"], logical_state=data["logical_state"],
        attempts=tuple(_attempt_from_dict(a) for a in data.get("attempts", ())),
        total_planned_units=data["total_planned_units"],
        attempted_unit_count=data["attempted_unit_count"],
        delivered_unit_count=data["delivered_unit_count"], failed_unit_count=data["failed_unit_count"],
        pending_unit_count=data["pending_unit_count"],
        retryable_failed_unit_count=data["retryable_failed_unit_count"],
        non_retryable_failed_unit_count=data["non_retryable_failed_unit_count"],
        ambiguous_unit_count=data.get("ambiguous_unit_count", 0),
        partial_delivery=data["partial_delivery"], retry_pending=data["retry_pending"],
        operator_completeness=data["operator_completeness"],
        first_attempt_at=data.get("first_attempt_at"), latest_attempt_at=data.get("latest_attempt_at"),
        finalized_at=data.get("finalized_at"), finalized=data["finalized"],
        diagnostics=tuple(data.get("diagnostics", ())), uncertainty=tuple(data.get("uncertainty", ())),
        limitations=tuple(data.get("limitations", ())),
        correction=_correction_from_dict(data.get("correction")),
        provenance=data.get("provenance", {}), authorization_evidence=data.get("authorization_evidence", {}),
        receipt_digest=data["receipt_digest"],
    )
    if verify_digest:
        recomputed = _digest_excluding(receipt.to_dict(), "receipt_digest")
        if recomputed != receipt.receipt_digest:
            raise ValueError(
                f"corrupt receipt storage: digest mismatch (stored={receipt.receipt_digest[:16]}, "
                f"recomputed={recomputed[:16]})"
            )
    return receipt


def _with_recomputed_digest(receipt: ExternalDeliveryReceipt) -> ExternalDeliveryReceipt:
    digest = _digest_excluding(receipt.to_dict(), "receipt_digest")
    return dataclasses.replace(receipt, receipt_digest=digest)


def validate_receipt_digest(receipt: ExternalDeliveryReceipt) -> bool:
    return _digest_excluding(receipt.to_dict(), "receipt_digest") == receipt.receipt_digest


def _build_receipt(
    attempts: tuple[DeliveryAttemptRecord, ...], *, phase_id: str, delivery_purpose: str,
    rendering_view_id: str, rendering_digest: str, renderer_id: str, renderer_version: str,
    adapter_id: str, adapter_version: str, destination_classification: str,
    safe_destination_alias: str, policy_version: str, delivery_mode: str,
    total_planned_units: int, provenance: dict[str, Any], authorization_evidence: dict[str, Any],
    correction: CorrectionRecord | None, finalized: bool, finalized_at: str | None,
) -> ExternalDeliveryReceipt:
    logical_delivery_id = attempts[0].logical_delivery_id
    receipt_id = compute_receipt_id(logical_delivery_id)
    agg = _aggregate(attempts, correction, total_planned_units)
    base = ExternalDeliveryReceipt(
        receipt_id=receipt_id, receipt_version=RECEIPT_SCHEMA_VERSION,
        logical_delivery_id=logical_delivery_id, phase_id=phase_id,
        delivery_purpose=delivery_purpose, rendering_view_id=rendering_view_id,
        rendering_digest=rendering_digest, renderer_id=renderer_id, renderer_version=renderer_version,
        adapter_id=adapter_id, adapter_version=adapter_version,
        destination_classification=destination_classification,
        safe_destination_alias=safe_destination_alias, policy_version=policy_version,
        delivery_mode=delivery_mode, logical_state=agg.logical_state.value, attempts=attempts,
        total_planned_units=total_planned_units, attempted_unit_count=agg.attempted_unit_count,
        delivered_unit_count=agg.delivered,
        failed_unit_count=agg.failed_retryable + agg.failed_non_retryable,
        pending_unit_count=agg.not_attempted, retryable_failed_unit_count=agg.failed_retryable,
        non_retryable_failed_unit_count=agg.failed_non_retryable, ambiguous_unit_count=agg.ambiguous,
        partial_delivery=agg.logical_state == LogicalDeliveryState.PARTIALLY_DELIVERED,
        retry_pending=agg.retry_pending, operator_completeness=agg.operator_completeness.value,
        first_attempt_at=agg.first_attempt_at, latest_attempt_at=agg.latest_attempt_at,
        finalized_at=finalized_at, finalized=finalized, diagnostics=agg.combined_diagnostics,
        uncertainty=agg.combined_uncertainty, limitations=agg.combined_limitations,
        correction=correction, provenance=provenance, authorization_evidence=authorization_evidence,
        receipt_digest="",
    )
    return _with_recomputed_digest(base)


def open_receipt(
    execution_result: DeliveryExecutionResult, plan: DeliveryPlan, request: DeliveryRequest,
    *, started_at: str, completed_at: str,
) -> ExternalDeliveryReceipt:
    """Create the initial receipt (first attempt, sequence 1) from a
    validated delivery-pipeline execution triple. Not finalized -- call
    ``finalize_receipt()`` once no further attempt is expected.
    """
    attempt = build_attempt(
        execution_result, plan, request, sequence=1, started_at=started_at, completed_at=completed_at,
    )
    caps = get_adapter(request.adapter_id).capabilities
    provenance = {
        "phase_id": request.phase_id, "rendering_view_id": request.rendering_view_id,
        "rendering_digest": request.rendering_digest, "renderer_id": request.renderer_id,
        "renderer_version": request.renderer_version,
        "delivery_request_logical_id": request.logical_delivery_id,
        "plan_digest": attempt.plan_digest,
        "execution_overall_outcome": execution_result.overall_outcome.value,
        "policy_version": request.policy_version,
    }
    authorization_evidence = {
        "represents_external_delivery": caps.represents_external_delivery,
        "authorization_required": caps.represents_external_delivery,
        "authorization_outcome": (
            "not_required" if not caps.represents_external_delivery
            else (
                "denied" if execution_result.overall_outcome == DeliveryOutcome.BLOCKED_BY_AUTHORIZATION
                else "authorized"
            )
        ),
        "is_synthetic": request.is_synthetic,
        "destination_classification": request.destination_classification.value,
        "policy_version": request.policy_version,
        "denial_reason_code": (
            "external_delivery_unauthorized"
            if execution_result.overall_outcome == DeliveryOutcome.BLOCKED_BY_AUTHORIZATION else None
        ),
    }
    return _build_receipt(
        (attempt,), phase_id=request.phase_id, delivery_purpose=request.delivery_purpose.value,
        rendering_view_id=request.rendering_view_id, rendering_digest=request.rendering_digest,
        renderer_id=request.renderer_id, renderer_version=request.renderer_version,
        adapter_id=request.adapter_id, adapter_version=request.adapter_version,
        destination_classification=request.destination_classification.value,
        safe_destination_alias=caps.safe_destination_alias, policy_version=request.policy_version,
        delivery_mode=plan.selected_mode.value, total_planned_units=len(plan.units),
        provenance=provenance, authorization_evidence=authorization_evidence,
        correction=None, finalized=False, finalized_at=None,
    )


def append_attempt(
    receipt: ExternalDeliveryReceipt, execution_result: DeliveryExecutionResult,
    plan: DeliveryPlan, request: DeliveryRequest, *, started_at: str, completed_at: str,
    retry_reason: str | None = None, ambiguous_unit_ids: frozenset[str] = frozenset(),
) -> ExternalDeliveryReceipt:
    """Append a new physical attempt to an existing, not-yet-finalized
    receipt. Structurally rejects changed content/destination/adapter/
    purpose under the same lineage: ``compute_logical_delivery_id``
    already includes rendering digest, purpose, destination, adapter,
    and policy version, so any of those changing produces a different
    ``logical_delivery_id`` -- caught here as "different logical
    delivery", not merely detected after the fact.
    """
    if receipt.finalized:
        raise ValueError(
            f"receipt {receipt.receipt_id!r} is already finalized; corrections must create a "
            "new receipt lineage, not mutate a finalized one"
        )
    if request.logical_delivery_id != receipt.logical_delivery_id:
        raise ValueError(
            "append_attempt: request belongs to a different logical delivery than this receipt "
            "(changed rendering/destination/adapter/purpose/policy under the same lineage is "
            "structurally rejected)"
        )
    if request.delivery_purpose.value != receipt.delivery_purpose:
        raise ValueError("append_attempt: retry cannot change delivery purpose under the same lineage")
    previous = receipt.attempts[-1]
    attempt = build_attempt(
        execution_result, plan, request, sequence=previous.attempt_sequence + 1,
        started_at=started_at, completed_at=completed_at, previous_attempt=previous,
        retry_reason=retry_reason, ambiguous_unit_ids=ambiguous_unit_ids,
    )
    new_attempts = receipt.attempts + (attempt,)
    provenance = dict(receipt.provenance)
    provenance["execution_overall_outcome"] = execution_result.overall_outcome.value
    provenance["plan_digest"] = attempt.plan_digest
    return _build_receipt(
        new_attempts, phase_id=receipt.phase_id, delivery_purpose=receipt.delivery_purpose,
        rendering_view_id=receipt.rendering_view_id, rendering_digest=receipt.rendering_digest,
        renderer_id=receipt.renderer_id, renderer_version=receipt.renderer_version,
        adapter_id=receipt.adapter_id, adapter_version=receipt.adapter_version,
        destination_classification=receipt.destination_classification,
        safe_destination_alias=receipt.safe_destination_alias, policy_version=receipt.policy_version,
        delivery_mode=plan.selected_mode.value, total_planned_units=receipt.total_planned_units,
        provenance=provenance, authorization_evidence=dict(receipt.authorization_evidence),
        correction=None, finalized=False, finalized_at=None,
    )


def finalize_receipt(
    receipt: ExternalDeliveryReceipt, *, finalized_at: str,
    force_close: bool = False, close_reason: str | None = None,
) -> ExternalDeliveryReceipt:
    """Finalize a receipt. A retryable failure or unresolved ambiguity
    is not final unless explicitly, governedly closed via
    ``force_close=True`` with a disclosed ``close_reason``. Finalized
    receipts are immutable -- this function never mutates ``receipt``
    in place (impossible for a frozen dataclass); it returns a new
    value, and further attempts/finalization against the returned
    receipt are rejected.
    """
    if receipt.finalized:
        raise ValueError(f"receipt {receipt.receipt_id!r} is already finalized")
    if receipt.retry_pending and not force_close:
        raise ValueError(
            f"cannot finalize receipt {receipt.receipt_id!r}: retryable or ambiguous units remain "
            "pending; pass force_close=True with an explicit close_reason to govern this closure"
        )
    if force_close and not close_reason:
        raise ValueError("force_close=True requires an explicit close_reason")
    diagnostics = receipt.diagnostics
    if force_close:
        diagnostics = diagnostics + (f"force_closed: {close_reason}",)
    candidate = dataclasses.replace(
        receipt, finalized=True, finalized_at=finalized_at, diagnostics=diagnostics,
    )
    return _with_recomputed_digest(candidate)


def apply_correction(
    receipt: ExternalDeliveryReceipt, correction: CorrectionRecord, *, finalized_at: str,
) -> ExternalDeliveryReceipt:
    """Attach correction/supersession metadata to a finalized receipt,
    returning a *new* receipt value. Never mutates or overwrites the
    original -- persistence stores this result as an additive overlay
    (``DeliveryReceiptStore.save_correction``), the original file is
    never touched.
    """
    if not receipt.finalized:
        raise ValueError("only a finalized receipt may be corrected/superseded")
    if correction.original_receipt_id != receipt.receipt_id:
        raise ValueError("correction.original_receipt_id must match the receipt being corrected")
    if correction.affected_logical_delivery_id != receipt.logical_delivery_id:
        raise ValueError(
            "correction.affected_logical_delivery_id must match receipt.logical_delivery_id"
        )
    if receipt.correction is not None:
        raise ValueError(
            "receipt is already corrected/superseded; corrections must form a new lineage, "
            "not reapply to an already corrected receipt (cycle rejected)"
        )
    new_state = (
        LogicalDeliveryState.CORRECTED if correction.direction == CorrectionDirection.CORRECTS.value
        else LogicalDeliveryState.SUPERSEDED
    )
    # Correction/supersession identity is explicitly distinct from both
    # receipt identity and logical delivery identity -- the corrector
    # gets its own receipt_id (correction.correcting_receipt_id), never
    # colliding with the original's receipt_id.
    candidate = dataclasses.replace(
        receipt, receipt_id=correction.correcting_receipt_id, correction=correction,
        logical_state=new_state.value, finalized_at=finalized_at, retry_pending=False,
    )
    return _with_recomputed_digest(candidate)


# ═══════════════════════════════════════════════════════════════════════
# Persistence
# ═══════════════════════════════════════════════════════════════════════


class DeliveryReceiptStore:
    """Smallest durable, file-backed persistence layer consistent with
    existing PCAE atomic-write/digest-verification conventions
    (``shell_gate.persist_audit_record`` / ``verify_audit_records``).

    Storage layout (transport-neutral -- never an adapter-specific
    directory such as ``telegram/``):

        <root>/receipts/<logical_delivery_id>/receipt.json
        <root>/corrections/<original_receipt_id>/<correcting_receipt_id>.json

    A test MUST construct this against a temporary directory; nothing
    in this module instantiates a store against
    ``DEFAULT_RECEIPT_STORE_ROOT`` automatically.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)

    @staticmethod
    def _validate_store_identifier(value: str, field_name: str) -> None:
        """Fail-closed defense against path traversal: every identifier
        used in a persisted path must be a single safe path component.
        Mirrors the established ``phase_reports._safe_filename`` /
        ``notifications._safe_doc_filename`` convention (identifiers are
        safe single-segment names) but rejects rather than silently
        rewriting, so two distinct identifiers can never collide into the
        same storage slot. The public receipt API only ever produces hex
        identifiers (``compute_receipt_id`` / ``compute_logical_delivery_
        id``) or caller-supplied correction identifiers; all of these
        satisfy this contract. 134E.7V repair: without this check, a
        caller-supplied ``correcting_receipt_id`` (an arbitrary string,
        unlike ``shell_gate``'s safe-by-construction ``sg-<uuid>`` audit
        id) containing ``..`` / separators could write outside the store
        root, inconsistent with the repository's own filename-sanitization
        convention.
        """
        if not value or "/" in value or "\\" in value or ".." in value or os.path.isabs(value):
            raise ValueError(
                f"unsafe store identifier for {field_name}: {value!r} "
                "(path separators, parent references, and absolute paths are rejected)"
            )

    def _receipt_path(self, logical_delivery_id: str) -> Path:
        self._validate_store_identifier(logical_delivery_id, "logical_delivery_id")
        return self.root / "receipts" / logical_delivery_id / "receipt.json"

    def _corrections_dir(self, original_receipt_id: str) -> Path:
        self._validate_store_identifier(original_receipt_id, "original_receipt_id")
        return self.root / "corrections" / original_receipt_id

    @staticmethod
    def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.parent / f".{path.name}.tmp"
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        os.replace(str(tmp_path), str(path))

    def save(
        self, receipt: ExternalDeliveryReceipt, *, expected_previous_digest: str | None = None,
    ) -> dict[str, Any]:
        """Create or governedly update the primary receipt record.
        Fails closed once finalized, on identity mismatch, on a stale
        (fewer-attempts) write, and on a stale-read/concurrent-write
        mismatch when ``expected_previous_digest`` is supplied.
        """
        path = self._receipt_path(receipt.logical_delivery_id)
        if path.exists():
            existing = self.load(receipt.logical_delivery_id)
            if expected_previous_digest is not None and existing.receipt_digest != expected_previous_digest:
                raise ValueError(
                    "stale write rejected: on-disk receipt digest changed since read "
                    "(concurrent modification detected)"
                )
            if existing.finalized:
                raise ValueError(
                    f"receipt for logical delivery {receipt.logical_delivery_id!r} is already "
                    "finalized; the primary record is immutable -- use save_correction() instead"
                )
            if existing.receipt_id != receipt.receipt_id:
                raise ValueError(
                    "duplicate logical delivery with a different receipt identity "
                    "(duplicate logical receipt detection)"
                )
            if len(receipt.attempts) < len(existing.attempts):
                raise ValueError(
                    "cannot persist a receipt with fewer attempts than already stored "
                    "(stale write / attempt regression)"
                )
        self._atomic_write(path, receipt.to_dict())
        return {"status": "written", "path": str(path), "receipt_digest": receipt.receipt_digest}

    def load(self, logical_delivery_id: str) -> ExternalDeliveryReceipt:
        path = self._receipt_path(logical_delivery_id)
        if not path.exists():
            raise FileNotFoundError(f"no receipt found for logical delivery {logical_delivery_id!r}")
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"corrupt receipt storage at {path}: {exc}") from exc
        return _receipt_from_dict(data, verify_digest=True)

    def save_correction(self, corrected_receipt: ExternalDeliveryReceipt) -> dict[str, Any]:
        if corrected_receipt.correction is None:
            raise ValueError("save_correction requires a receipt carrying correction metadata")
        correction = corrected_receipt.correction
        self._validate_store_identifier(correction.correcting_receipt_id, "correcting_receipt_id")
        corr_dir = self._corrections_dir(correction.original_receipt_id)
        path = corr_dir / f"{correction.correcting_receipt_id}.json"
        if path.exists():
            raise ValueError("duplicate correction record for this original/correcting pair")
        self._atomic_write(path, corrected_receipt.to_dict())
        if not self._receipt_path(corrected_receipt.logical_delivery_id).exists():
            self.save(corrected_receipt)
        return {"status": "written", "path": str(path)}

    def list_corrections(self, original_receipt_id: str) -> tuple[ExternalDeliveryReceipt, ...]:
        corr_dir = self._corrections_dir(original_receipt_id)
        if not corr_dir.exists():
            return ()
        out = []
        for f in sorted(corr_dir.glob("*.json")):
            out.append(_receipt_from_dict(json.loads(f.read_text()), verify_digest=True))
        return tuple(out)

    def list_attempts(self, logical_delivery_id: str) -> tuple[DeliveryAttemptRecord, ...]:
        return self.load(logical_delivery_id).attempts
