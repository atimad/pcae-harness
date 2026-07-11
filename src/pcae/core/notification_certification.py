"""Phase 114B: Notification Certification & Idempotency.

The Repository Transition Validator (113U/113Y/113Z) has always specified
notification governance -- ``TransitionKind.NOTIFY``,
``notification_eligible()``, and the ``RepositoryState.notification_
already_dispatched`` / ``notification_transport_enabled`` fields -- but
until this phase nothing on the real dispatch path (``pcae phase
complete``, ``pcae task finish --commit``) ever constructed a ``NOTIFY``
transition and asked the validator. Each caller independently decided
whether to suppress dispatch, using two slightly different ad hoc
conditions built directly on the Phase 113V.N marker file.

This module is the single notification authority both callers now consume:
one function turns "should this transition be allowed to notify" into a
:class:`NotificationCertification`, backed by ``validate_transition()``
itself. Nothing here talks to a transport (no Telegram calls, no sink
construction) and nothing here writes the idempotency marker -- both
remain exactly where they already lived (``pcae.core.notifications``,
``pcae.core.phase_reports.write_notification_dispatch_marker``). This
module only decides eligibility before the caller acts on it. See
``docs/PCAE_NOTIFICATION_CERTIFICATION.md``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from pcae.core.phase_reports import (
    compute_finalization_snapshot_id,
    compute_report_digest,
    notification_dispatch_state,
)
from pcae.core.repository_transition_integration import (
    parse_lifecycle_phase_identity,
    parse_phase_id_from_text,
)
from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    ProposedTransition,
    RepositoryState,
    TransitionKind,
    TransitionVerdict,
    validate_transition,
)

class NotificationCertificationOutcome(str, Enum):
    """Diagnostic label for why a NOTIFY transition was (not) certified.

    ``eligible`` is the only outcome that permits dispatch. The other four
    are mutually exclusive, checked in the order listed, so exactly one
    describes any given certification.
    """

    ELIGIBLE = "eligible"
    ALREADY_DISPATCHED = "already_dispatched"
    PAYLOAD_CONFLICT = "payload_conflict"
    DISABLED = "disabled"
    TRANSPORT_UNAVAILABLE = "transport_unavailable"
    NOT_CERTIFIED = "not_certified"


@dataclass(frozen=True)
class NotificationCertification:
    """The single, shared notification decision for one lifecycle finalization."""

    eligible: bool
    outcome: NotificationCertificationOutcome
    reasons: tuple[str, ...]
    transition_verdict: TransitionVerdict


def notification_transport_status() -> tuple[bool, bool, list[str]]:
    """Read the same ``PCAE_NOTIFY_ENABLED`` / ``PCAE_NOTIFY_SINKS``
    environment contract ``finalize_phase_report()`` uses for the actual
    dispatch attempt, and classify readiness from it.

    Returns ``(notify_enabled, transport_configured, sink_names)``.
    ``transport_configured`` is True whenever notifications are enabled
    and at least one sink name is configured -- deliberately mechanical
    (mirrors ``finalize_phase_report()``'s own ``if not sinks: skip``
    check) rather than probing individual sink readiness, so this module
    stays decoupled from any one sink's configuration interface. Whether a
    specific sink (e.g. Telegram) is actually reachable is still decided,
    as before, by that sink's own ``send()`` at dispatch time -- surfaced
    as ``dispatch failed``, not as a certification-time rejection.
    """
    notify_enabled = os.environ.get("PCAE_NOTIFY_ENABLED", "").lower() in ("1", "true", "yes")
    sink_names_raw = os.environ.get("PCAE_NOTIFY_SINKS", "filesystem")
    sink_names = [s.strip() for s in sink_names_raw.split(",") if s.strip()]
    transport_configured = notify_enabled and bool(sink_names)
    return notify_enabled, transport_configured, sink_names


def certify_notification_transition(
    *,
    phase_id: str,
    requested_phase_id: str,
    active_task_title: str | None,
    metadata: dict[str, Any],
    lifecycle_current_phase_line: str | None,
    trial_report: Any,
    recommended_next_phase: str,
    origin_main_head_count: int,
    commit_hash: str,
    source_transition_kind: TransitionKind,
    allow_partial_report: bool = False,
    marker_path: Path | None = None,
) -> NotificationCertification:
    """Certify a ``NOTIFY`` transition for one finalization attempt.

    Called only after the caller's own ``COMPLETE_PHASE``/``FINISH_TASK``
    transition already reached ACCEPT and the report has been (or is about
    to be) written -- so ``artifact_state=Canonical`` here reflects a
    promotion that is guaranteed, not assumed. Every other input mirrors
    ``validate_phase_report_transition()`` exactly so this evaluates the
    identical phase-identity/report-completeness/execution-availability
    invariants against the same facts, plus the notification-specific
    ones (``notification_eligibility``) that call never triggers.
    """
    metadata_phase_id = metadata.get("phase_id") if isinstance(metadata.get("phase_id"), str) else None
    lifecycle_phase_id, lifecycle_completed = parse_lifecycle_phase_identity(lifecycle_current_phase_line)
    active_task_phase_id = parse_phase_id_from_text(active_task_title)
    report_completeness = "complete" if allow_partial_report else trial_report.report_completeness

    report_digest = compute_report_digest(trial_report)
    snapshot_id = compute_finalization_snapshot_id(trial_report)
    dispatch_state = notification_dispatch_state(
        phase_id,
        marker_path=marker_path,
        report_digest=report_digest,
        finalization_snapshot_id=snapshot_id,
    )
    already_dispatched = dispatch_state in ("already_dispatched", "payload_conflict")
    notify_enabled, transport_configured, sink_names = notification_transport_status()

    state = RepositoryState(
        phase_id=phase_id,
        active_task_phase_id=active_task_phase_id,
        metadata_phase_id=metadata_phase_id,
        lifecycle_current_phase_id=lifecycle_phase_id,
        lifecycle_current_phase_completed=lifecycle_completed,
        commits=tuple(str(c) for c in trial_report.commits),
        files_changed=trial_report.files_changed,
        test_results=dict(trial_report.test_results),
        recommended_next_phase=recommended_next_phase,
        report_completeness=report_completeness,
        pushed_status=trial_report.pushed_status,
        origin_main_head_count=origin_main_head_count,
        notification_already_dispatched=already_dispatched,
        notification_transport_enabled=transport_configured,
        artifact_state=ArtifactState.CANONICAL,
        execution_availability=str(metadata.get("execution_availability", "unavailable")),
    )
    proposed_transition = ProposedTransition(
        kind=TransitionKind.NOTIFY,
        payload={
            "phase_id": phase_id,
            "commit": commit_hash,
            "source_transition": source_transition_kind.value,
            "sinks": tuple(sink_names),
        },
    )
    # Deliberately no `artifact_state` on the expected target: NOTIFY never
    # requests further promotion, and `canonical_promotion_eligibility`
    # only fires when the target *is* Canonical -- that invariant belongs
    # to the promotion transition already evaluated upstream, not to this
    # one.
    expected_target = ExpectedTargetState(phase_id=requested_phase_id)

    result = validate_transition(state, proposed_transition, expected_target)

    if result.accepted:
        return NotificationCertification(
            eligible=True,
            outcome=NotificationCertificationOutcome.ELIGIBLE,
            reasons=(),
            transition_verdict=result.verdict,
        )

    reasons = tuple(v.reason for v in result.violations)
    if dispatch_state == "payload_conflict":
        outcome = NotificationCertificationOutcome.PAYLOAD_CONFLICT
        reasons = reasons + (
            "ordinary completion payload conflicts with the bound report digest or finalization snapshot",
        )
    elif already_dispatched:
        outcome = NotificationCertificationOutcome.ALREADY_DISPATCHED
    elif not notify_enabled:
        outcome = NotificationCertificationOutcome.DISABLED
    elif not transport_configured:
        outcome = NotificationCertificationOutcome.TRANSPORT_UNAVAILABLE
    else:
        outcome = NotificationCertificationOutcome.NOT_CERTIFIED
    return NotificationCertification(
        eligible=False,
        outcome=outcome,
        reasons=reasons,
        transition_verdict=result.verdict,
    )
