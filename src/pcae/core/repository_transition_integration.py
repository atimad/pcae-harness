"""Shared Repository Transition Validator integration helpers.

Phase 113Z moves the first live validator adapter out of
``commands.phase`` so ``pcae phase complete`` and ``pcae task finish
--commit`` cannot drift into separate canonical-validation flows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pcae.core import phase_id as canonical_phase_id
from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    InvariantViolation,
    ProposedTransition,
    RepositoryState,
    TransitionKind,
    TransitionResult,
    TransitionVerdict,
    validate_transition,
)


def validate_phase_report_transition(
    *,
    phase_id: str,
    requested_phase_id: str,
    phase_name: str,
    active_task_title: str | None,
    metadata: dict[str, Any],
    lifecycle_current_phase_line: str | None,
    trial_report: Any,
    recommended_next_phase: str,
    origin_main_head_count: int,
    transition_kind: TransitionKind,
    allow_partial_report: bool = False,
) -> TransitionResult:
    """Validate a phase-report canonical-promotion request.

    This is the shared Repository State Kernel / Model Containment Layer
    adapter used by both ``pcae phase complete`` and ``pcae task finish
    --commit``. It constructs the frozen 113T validator inputs from the
    caller's already-built trial report and metadata before any canonical
    ``latest.*`` write occurs.
    """
    metadata_phase_id = metadata.get("phase_id") if isinstance(metadata.get("phase_id"), str) else None
    lifecycle_phase_id, lifecycle_completed = parse_lifecycle_phase_identity(lifecycle_current_phase_line)
    active_task_phase_id = parse_phase_id_from_text(active_task_title)
    report_completeness = "complete" if allow_partial_report else trial_report.report_completeness

    current_state = RepositoryState(
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
        artifact_state=ArtifactState.CERTIFIED,
        execution_availability=str(metadata.get("execution_availability", "unavailable")),
    )
    proposed_transition = ProposedTransition(
        kind=transition_kind,
        payload={
            "phase_id": phase_id,
            "phase_name": phase_name,
            "report_completeness": report_completeness,
            "requested_canonical_artifacts": ("latest.md", "latest.json"),
        },
    )
    expected_target = ExpectedTargetState(
        artifact_state=ArtifactState.CANONICAL,
        phase_id=requested_phase_id,
    )

    result = validate_transition(current_state, proposed_transition, expected_target)
    if result.accepted and metadata_requires_human_review(metadata):
        return TransitionResult(
            verdict=TransitionVerdict.REQUIRES_HUMAN_REVIEW,
            violations=(
                InvariantViolation(
                    "human_review_required",
                    "phase-completion metadata explicitly requires human review",
                    "blocking",
                ),
            ),
        )
    return result


def handle_phase_report_transition_result(
    result: TransitionResult,
    trial_report: Any,
    gate: dict[str, Any],
    *,
    command_label: str,
    accepted_message: str,
    rejected_message: str,
    refused_message: str,
    notification_skip_message: str | None = None,
    reports_dir: Path | None = None,
    emit_diagnostics: bool = True,
) -> bool:
    """Print diagnostics, write quarantine when appropriate, and return
    whether canonical promotion may continue."""
    if result.verdict == TransitionVerdict.ACCEPT:
        if emit_diagnostics:
            print(f"Repository transition validator: {accepted_message}")
            print("  Verdict: accept")
            print(f"  Certified transition: {command_label} -> canonical phase report")
        return True

    if emit_diagnostics:
        print(f"Repository transition validator: {validator_verdict_label(result.verdict)}")
        print(f"  Verdict: {result.verdict.value}")
        for violation in result.violations:
            print(f"  Violation: {violation.invariant} - {validator_violation_reason(violation)}")

        print("Phase report: BLOCKED by finalization gate")
        for blocker in gate.get("blockers", []):
            print(f"  Blocker: {blocker}")
    if result.verdict == TransitionVerdict.QUARANTINE:
        from pcae.core.phase_reports import write_quarantined_report

        blockers = [
            f"{violation.invariant}: {validator_violation_reason(violation)}"
            for violation in result.violations
        ] or ["repository transition validator quarantined the phase report transition"]
        paths = write_quarantined_report(trial_report, reports_dir or Path(".pcae/phase-reports"), blockers)
        if emit_diagnostics:
            print("  Report quarantined -- latest.md/latest.json were NOT written or overwritten.")
            if paths.get("quarantine_markdown"):
                print(f"  Quarantine markdown: {paths['quarantine_markdown']}")
            if paths.get("quarantine_json"):
                print(f"  Quarantine json:     {paths['quarantine_json']}")
    elif result.verdict == TransitionVerdict.REQUIRES_HUMAN_REVIEW:
        if emit_diagnostics:
            print("  Human review required -- latest.md/latest.json were NOT written or overwritten.")
    else:
        if emit_diagnostics:
            print("  Report quarantined: no -- reject writes no report artifact.")
            print(f"  {rejected_message}")
    if emit_diagnostics:
        print(f"  {refused_message}")
        if notification_skip_message:
            print(notification_skip_message)
    return False


def validator_verdict_label(verdict: TransitionVerdict) -> str:
    if verdict == TransitionVerdict.REJECT:
        return "Transition rejected"
    if verdict == TransitionVerdict.QUARANTINE:
        return "Transition quarantined"
    if verdict == TransitionVerdict.REQUIRES_HUMAN_REVIEW:
        return "Human review required"
    return "Transition validated"


def validator_violation_reason(violation: InvariantViolation) -> str:
    if violation.invariant == "recommended_next_phase_presence":
        return "recommended_next_phase missing as structured metadata"
    return violation.reason


def metadata_requires_human_review(metadata: dict[str, Any]) -> bool:
    raw = metadata.get("requires_human_review", metadata.get("human_review_required", False))
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "required"}
    return False


def parse_lifecycle_phase_identity(line: str | None) -> tuple[str | None, bool]:
    if not line:
        return None, False
    return parse_phase_id_from_text(line), "(completed)" in line.lower()


def parse_phase_id_from_text(text: str | None) -> str | None:
    # Phase 137R — this was the one inventoried consumer still carrying
    # the unrepaired exactly-one-letter-branch truncation defect at
    # CPIPC-001 freeze time (CPIPC-REQ-056). Recognition and token
    # scanning are now owned exclusively by the canonical parser
    # (``pcae.core.phase_id``, CPIPC-001 §6, §8).
    token = canonical_phase_id.find_first_token(text or "")
    return token.normalized_text if token is not None else None
