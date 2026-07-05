"""Phase 113U: Repository Transition Validator Prototype.

Tests the observation-only validator implemented in
``src/pcae/core/repository_transition_validator.py``. This module is
NOT wired into pcae phase complete / pcae task finish --commit / push
/ notify -- these tests call it directly, exactly as the 113U brief
requires ("may be called by tests and optional read-only helpers").
"""
from __future__ import annotations

from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    ProposedTransition,
    RepositoryState,
    TransitionKind,
    TransitionVerdict,
    notification_eligible,
    promotion_allowed,
    validate_transition,
)


def _certified_state(**overrides) -> RepositoryState:
    base = dict(
        phase_id="113U",
        active_task_phase_id="113U",
        metadata_phase_id="113U",
        lifecycle_current_phase_id="113T",
        lifecycle_current_phase_completed=True,
        commits=("abc12345",),
        files_changed=3,
        test_results={"focused": "10/10 (passed)"},
        recommended_next_phase="113V — Repository Transition Validator Verification & Compatibility",
        report_completeness="complete",
        pushed_status="pushed",
        origin_main_head_count=0,
        notification_already_dispatched=False,
        notification_transport_enabled=True,
        artifact_state=ArtifactState.CERTIFIED,
        execution_availability="unavailable",
    )
    base.update(overrides)
    return RepositoryState(**base)


def _complete_phase_transition(**payload) -> ProposedTransition:
    return ProposedTransition(kind=TransitionKind.COMPLETE_PHASE, payload=payload)


class TestValidatorExists:
    def test_validate_transition_is_callable(self):
        assert callable(validate_transition)

    def test_notification_eligible_is_callable(self):
        assert callable(notification_eligible)

    def test_promotion_allowed_is_callable(self):
        assert callable(promotion_allowed)


class TestAllVerdictsExist:
    def test_four_verdicts_defined(self):
        values = {v.value for v in TransitionVerdict}
        assert values == {"accept", "reject", "quarantine", "requires_human_review"}


class TestAcceptRejectQuarantineHumanReviewBehavior:
    def test_fully_consistent_state_accepts(self):
        state = _certified_state()
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.ACCEPT
        assert result.accepted is True
        assert result.violations == ()

    def test_identity_mismatch_rejects(self):
        state = _certified_state(metadata_phase_id="113B")
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "phase_identity_consistency" for v in result.violations)

    def test_missing_recommended_next_phase_rejects(self):
        state = _certified_state(recommended_next_phase="")
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "recommended_next_phase_presence" for v in result.violations)

    def test_partial_report_completeness_quarantines(self):
        state = _certified_state(report_completeness="partial")
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.QUARANTINE
        assert any(v.invariant == "report_completeness" for v in result.violations)

    def test_missing_evidence_rejects(self):
        state = _certified_state(report_completeness="", test_results={}, commits=())
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.REJECT


class TestPhaseIdentityMismatchRejects:
    def test_active_task_vs_metadata_mismatch(self):
        state = _certified_state(active_task_phase_id="113U", metadata_phase_id="113T")
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.REJECT

    def test_lifecycle_context_ignored_when_marked_completed(self):
        # Mirrors resolve_canonical_phase_identity's own rule: a
        # completed lifecycle-context phase is not a live identity
        # source, so it must not be flagged as a disagreement.
        state = _certified_state(
            active_task_phase_id="113U",
            metadata_phase_id="113U",
            lifecycle_current_phase_id="113T",
            lifecycle_current_phase_completed=True,
        )
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.ACCEPT

    def test_metadata_disagrees_with_proposed_target_phase_id(self):
        state = _certified_state(metadata_phase_id="113T")
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "metadata_consistency" for v in result.violations)


class TestCanonicalPromotionStates:
    def test_blocked_artifact_cannot_be_canonical(self):
        assert promotion_allowed(ArtifactState.BLOCKED, ArtifactState.CANONICAL) is False

    def test_draft_artifact_cannot_be_canonical(self):
        assert promotion_allowed(ArtifactState.DRAFT, ArtifactState.CANONICAL) is False

    def test_rejected_artifact_cannot_be_canonical(self):
        assert promotion_allowed(ArtifactState.REJECTED, ArtifactState.CANONICAL) is False

    def test_quarantined_artifact_cannot_be_canonical(self):
        assert promotion_allowed(ArtifactState.QUARANTINED, ArtifactState.CANONICAL) is False

    def test_certified_artifact_can_be_canonical(self):
        assert promotion_allowed(ArtifactState.CERTIFIED, ArtifactState.CANONICAL) is True

    def test_validator_rejects_promoting_blocked_state_to_canonical(self):
        state = _certified_state(artifact_state=ArtifactState.BLOCKED)
        target = ExpectedTargetState(artifact_state=ArtifactState.CANONICAL, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "canonical_promotion_eligibility" for v in result.violations)

    def test_validator_accepts_promoting_certified_state_to_canonical(self):
        state = _certified_state(artifact_state=ArtifactState.CERTIFIED)
        target = ExpectedTargetState(artifact_state=ArtifactState.CANONICAL, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.ACCEPT

    def test_all_six_states_exist(self):
        values = {s.value for s in ArtifactState}
        assert values == {"draft", "blocked", "rejected", "quarantined", "certified", "canonical"}


class TestNotificationEligibilityRequiresAllConditions:
    def test_fully_eligible_state(self):
        state = _certified_state()
        eligible, reasons = notification_eligible(state)
        assert eligible is True
        assert reasons == ()

    def test_not_certified_is_ineligible(self):
        state = _certified_state(artifact_state=ArtifactState.DRAFT)
        eligible, reasons = notification_eligible(state)
        assert eligible is False
        assert len(reasons) > 0

    def test_push_not_clean_is_ineligible(self):
        state = _certified_state(origin_main_head_count=2)
        eligible, reasons = notification_eligible(state)
        assert eligible is False
        assert any("push" in r for r in reasons)

    def test_already_dispatched_is_ineligible(self):
        state = _certified_state(notification_already_dispatched=True)
        eligible, reasons = notification_eligible(state)
        assert eligible is False
        assert any("already dispatched" in r for r in reasons)

    def test_transport_disabled_is_ineligible(self):
        state = _certified_state(notification_transport_enabled=False)
        eligible, reasons = notification_eligible(state)
        assert eligible is False
        assert any("transport" in r for r in reasons)

    def test_notify_transition_ineligible_state_rejects(self):
        state = _certified_state(notification_already_dispatched=True)
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        transition = ProposedTransition(kind=TransitionKind.NOTIFY)
        result = validate_transition(state, transition, target)
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "notification_eligibility" for v in result.violations)

    def test_notify_transition_eligible_state_accepts(self):
        state = _certified_state()
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        transition = ProposedTransition(kind=TransitionKind.NOTIFY)
        result = validate_transition(state, transition, target)
        assert result.verdict == TransitionVerdict.ACCEPT

    def test_non_notify_transition_unaffected_by_notification_state(self):
        # A complete_phase transition must not be rejected merely
        # because notification isn't eligible -- eligibility only
        # matters for the notify transition kind itself.
        state = _certified_state(notification_already_dispatched=True)
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.ACCEPT


class TestExecutionAvailabilityViolationRejects:
    def test_execution_available_rejects(self):
        state = _certified_state(execution_availability="available")
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "no_execution_availability_unless_contracted" for v in result.violations)

    def test_execution_unavailable_does_not_reject_on_this_ground(self):
        state = _certified_state(execution_availability="unavailable")
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result = validate_transition(state, _complete_phase_transition(), target)
        assert not any(
            v.invariant == "no_execution_availability_unless_contracted" for v in result.violations
        )


class TestModelAgnosticBehavior:
    def test_no_identity_field_on_repository_state(self):
        import dataclasses

        field_names = {f.name for f in dataclasses.fields(RepositoryState)}
        for forbidden in ("agent", "agent_id", "model", "model_id", "proposer"):
            assert forbidden not in field_names

    def test_no_identity_field_on_proposed_transition(self):
        import dataclasses

        field_names = {f.name for f in dataclasses.fields(ProposedTransition)}
        assert field_names == {"kind", "payload"}

    def test_agent_identity_in_payload_does_not_affect_verdict(self):
        state = _certified_state()
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        result_claude = validate_transition(
            state, _complete_phase_transition(agent="Claude"), target
        )
        result_deepseek = validate_transition(
            state, _complete_phase_transition(agent="Claude-DeepSeek"), target
        )
        result_none = validate_transition(state, _complete_phase_transition(), target)
        assert result_claude.verdict == result_deepseek.verdict == result_none.verdict == TransitionVerdict.ACCEPT


class TestDeterministicOutput:
    def test_same_inputs_produce_same_result(self):
        state = _certified_state()
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        transition = _complete_phase_transition()
        result_1 = validate_transition(state, transition, target)
        result_2 = validate_transition(state, transition, target)
        assert result_1.verdict == result_2.verdict
        assert result_1.violations == result_2.violations

    def test_repeated_calls_across_many_invocations_are_stable(self):
        state = _certified_state(metadata_phase_id="113B")
        target = ExpectedTargetState(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
        transition = _complete_phase_transition()
        results = [validate_transition(state, transition, target) for _ in range(10)]
        assert len({r.verdict for r in results}) == 1
        assert len({r.violations for r in results}) == 1


class TestRequiresHumanReviewReachable:
    def test_verdict_enum_contains_requires_human_review(self):
        # This prototype's structural checks map only to accept/reject/
        # quarantine (113T's Failure Contract: identity/metadata/
        # commit/architecture/notification mismatches and missing
        # evidence all resolve to Reject or Quarantine for a purely
        # structural, always-available check). REQUIRES_HUMAN_REVIEW is
        # reserved, per the frozen Failure Contract, for "validator
        # unavailable" -- a condition this pure, always-evaluable
        # prototype cannot itself hit, but the verdict must still exist
        # as a first-class value other integration points can return.
        assert TransitionVerdict.REQUIRES_HUMAN_REVIEW.value == "requires_human_review"
