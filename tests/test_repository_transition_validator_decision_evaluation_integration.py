"""Phase 115F: Repository Decision Evaluation Integration.

Regression tests proving the 115F integration is behavior-preserving:
"same decisions, better explanations." The Repository Transition
Validator (``core/repository_transition_validator.py``) remains the
sole verdict authority; 115E's Decision Evaluation
(``core/decision_evaluation.py``) is wired in as optional,
backward-compatible explanation enrichment only.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

from pcae.core.decision_evaluation import EvaluationResult, InvariantStatus
from pcae.core.evidence import EvidenceCollection
from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    ProposedTransition,
    RepositoryState,
    TransitionKind,
    TransitionResult,
    TransitionVerdict,
    build_evidence_from_repository_state,
    notification_eligible,
    promotion_allowed,
    validate_transition,
)


def _certified_state(**overrides) -> RepositoryState:
    """Mirrors test_repository_transition_validator.py's own fixture
    exactly, so the regression scenarios below are a faithful
    reproduction of the pre-115F test suite's inputs."""
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


def _target(**overrides) -> ExpectedTargetState:
    base = dict(artifact_state=ArtifactState.CERTIFIED, phase_id="113U")
    base.update(overrides)
    return ExpectedTargetState(**base)


class TestVerdictsUnchangedForExistingScenarios:
    """Re-runs representative 113U scenarios verbatim and asserts the
    exact same verdicts the pre-115F test suite already established --
    proving the enrichment never influences verdict computation."""

    def test_fully_consistent_state_still_accepts(self):
        result = validate_transition(_certified_state(), _complete_phase_transition(), _target())
        assert result.verdict == TransitionVerdict.ACCEPT
        assert result.violations == ()

    def test_identity_mismatch_still_rejects(self):
        result = validate_transition(
            _certified_state(metadata_phase_id="113B"), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "phase_identity_consistency" for v in result.violations)

    def test_missing_recommended_next_phase_still_rejects(self):
        result = validate_transition(
            _certified_state(recommended_next_phase=""), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "recommended_next_phase_presence" for v in result.violations)

    def test_partial_report_completeness_still_quarantines(self):
        result = validate_transition(
            _certified_state(report_completeness="partial"), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.QUARANTINE
        assert any(v.invariant == "report_completeness" for v in result.violations)

    def test_missing_evidence_still_rejects(self):
        result = validate_transition(
            _certified_state(report_completeness="", test_results={}, commits=()),
            _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.REJECT

    def test_blocked_artifact_to_canonical_still_rejects(self):
        result = validate_transition(
            _certified_state(artifact_state=ArtifactState.BLOCKED),
            _complete_phase_transition(),
            _target(artifact_state=ArtifactState.CANONICAL),
        )
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "canonical_promotion_eligibility" for v in result.violations)

    def test_certified_artifact_to_canonical_still_accepts(self):
        result = validate_transition(
            _certified_state(artifact_state=ArtifactState.CERTIFIED),
            _complete_phase_transition(),
            _target(artifact_state=ArtifactState.CANONICAL),
        )
        assert result.verdict == TransitionVerdict.ACCEPT

    def test_notify_ineligible_state_still_rejects(self):
        state = _certified_state(notification_already_dispatched=True)
        transition = ProposedTransition(kind=TransitionKind.NOTIFY)
        result = validate_transition(state, transition, _target())
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "notification_eligibility" for v in result.violations)

    def test_execution_available_still_rejects(self):
        result = validate_transition(
            _certified_state(execution_availability="available"), _complete_phase_transition(), _target(),
        )
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "no_execution_availability_unless_contracted" for v in result.violations)

    def test_agent_identity_in_payload_still_does_not_affect_verdict(self):
        state = _certified_state()
        result_claude = validate_transition(state, _complete_phase_transition(agent="Claude"), _target())
        result_deepseek = validate_transition(state, _complete_phase_transition(agent="DeepSeek"), _target())
        result_none = validate_transition(state, _complete_phase_transition(), _target())
        assert result_claude.verdict == result_deepseek.verdict == result_none.verdict == TransitionVerdict.ACCEPT

    def test_determinism_unchanged_verdict_and_violations_stable_across_calls(self):
        state = _certified_state(metadata_phase_id="113B")
        transition = _complete_phase_transition()
        target = _target()
        results = [validate_transition(state, transition, target) for _ in range(5)]
        assert len({r.verdict for r in results}) == 1
        assert len({r.violations for r in results}) == 1

    def test_notification_eligible_helper_unaffected(self):
        state = _certified_state()
        eligible, reasons = notification_eligible(state)
        assert eligible is True
        assert reasons == ()

    def test_promotion_allowed_helper_unaffected(self):
        assert promotion_allowed(ArtifactState.CERTIFIED, ArtifactState.CANONICAL) is True
        assert promotion_allowed(ArtifactState.DRAFT, ArtifactState.CANONICAL) is False


class TestExplanationPresence:
    def test_explanation_present_on_accept(self):
        result = validate_transition(_certified_state(), _complete_phase_transition(), _target())
        assert result.explanation is not None
        assert isinstance(result.explanation, EvaluationResult)

    def test_explanation_present_on_reject(self):
        result = validate_transition(
            _certified_state(metadata_phase_id="113B"), _complete_phase_transition(), _target(),
        )
        assert result.explanation is not None

    def test_explanation_present_on_quarantine(self):
        result = validate_transition(
            _certified_state(report_completeness="partial"), _complete_phase_transition(), _target(),
        )
        assert result.explanation is not None

    def test_explanation_is_deterministic(self):
        state = _certified_state()
        transition = _complete_phase_transition()
        target = _target()
        first = validate_transition(state, transition, target)
        second = validate_transition(state, transition, target)
        assert first.explanation == second.explanation
        assert first == second


class TestEvidenceReferencesAttached:
    def test_explanation_reference_non_empty_for_accept(self):
        result = validate_transition(_certified_state(), _complete_phase_transition(), _target())
        assert len(result.explanation.explanation_reference) > 0

    def test_evidence_ids_reused_from_115d_scheme(self):
        result = validate_transition(_certified_state(), _complete_phase_transition(), _target())
        ids = {r.evidence_id for r in result.explanation.explanation_reference}
        assert ids <= {"E-report-002", "E-metadata-002", "E-report-003", "E-runtime-002"}
        assert "E-report-003" in ids

    def test_build_evidence_from_repository_state_returns_evidence_collection(self):
        collection = build_evidence_from_repository_state(_certified_state())
        assert isinstance(collection, EvidenceCollection)
        assert collection.by_id("E-report-003") is not None
        assert collection.by_id("E-runtime-002") is not None

    def test_adapter_never_populates_dual_source_evidence(self):
        """push_state_consistency/metadata_consistency require two
        independently sourced evidence items -- RepositoryState only
        ever carries one reconciled pushed_status, so the adapter must
        never fabricate a second source."""
        collection = build_evidence_from_repository_state(_certified_state())
        for missing_id in ("E-git-005", "E-metadata-003", "E-metadata-004", "E-report-005"):
            assert collection.by_id(missing_id) is None


class TestUnknownEvidenceNeverSilentlyPasses:
    """The adapter itself never produces UNKNOWN evidence (RepositoryState
    fields are always concrete values) -- this property is inherited
    unmodified from 115E's decision_evaluation.py, proven here by
    constructing evidence the same shape the integration produces and
    confirming the invariant behavior is unchanged."""

    def test_missing_report_completeness_evidence_is_not_applicable_not_pass(self):
        from pcae.core.decision_evaluation import evaluate_report_completeness
        result = evaluate_report_completeness(EvidenceCollection())
        assert result.status is not InvariantStatus.PASS
        assert result.status is InvariantStatus.NOT_APPLICABLE

    def test_unknown_freshness_evidence_never_becomes_pass_through_evaluate(self):
        from pcae.core.decision_evaluation import EvaluationContext, evaluate
        from pcae.core.evidence import (
            Evidence, EvidenceCategory, EvidenceConfidence, EvidenceDeterminism,
            EvidenceFreshness, EvidenceProvenance,
        )
        prov = EvidenceProvenance(producer="p", produced_from="x", timestamp="t", deterministic_origin=True)
        unknown_item = Evidence(
            evidence_id="E-report-003", source="s", category=EvidenceCategory.REPORT,
            producer="p", timestamp_utc="t", freshness=EvidenceFreshness.UNKNOWN,
            confidence=EvidenceConfidence.UNKNOWN, determinism=EvidenceDeterminism.DETERMINISTIC,
            scope="s", references=(), observed_value="unavailable", explanation="e", provenance=prov,
        )
        context = EvaluationContext(
            evidence=EvidenceCollection((unknown_item,)), evaluation_id="e1",
            evaluation_timestamp="t", repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        result = evaluate(context)
        assert "report_completeness" in result.blocking_failures


class TestConflictingEvidencePreserved:
    """The adapter itself cannot produce conflicts (only one source per
    fact) -- this test proves the integration path (evaluate(), called
    identically whether fed adapter output or real provider output)
    still preserves conflicting evidence exactly as 115E established,
    i.e. the integration introduces no new conflict-resolution logic."""

    def test_disagreeing_push_state_evidence_preserved_as_conflict(self):
        from pcae.core.decision_evaluation import EvaluationContext, evaluate
        from pcae.core.evidence import (
            Evidence, EvidenceCategory, EvidenceConfidence, EvidenceDeterminism,
            EvidenceFreshness, EvidenceProvenance,
        )
        prov = EvidenceProvenance(producer="p", produced_from="x", timestamp="t", deterministic_origin=True)

        def ev(evidence_id, value):
            return Evidence(
                evidence_id=evidence_id, source="s", category=EvidenceCategory.PUSH_STATE,
                producer="p", timestamp_utc="t", freshness=EvidenceFreshness.CURRENT,
                confidence=EvidenceConfidence.HIGH, determinism=EvidenceDeterminism.DETERMINISTIC,
                scope="s", references=(), observed_value=value, explanation="e", provenance=prov,
            )

        collection = EvidenceCollection((ev("E-git-005", "pushed"), ev("E-metadata-003", "not_pushed")))
        context = EvaluationContext(
            evidence=collection, evaluation_id="e1", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        result = evaluate(context)
        push_result = next(r for r in result.invariant_results if r.invariant_id == "push_state_consistency")
        assert push_result.status is InvariantStatus.FAIL
        conflict_ids = {r.evidence_id for r in push_result.conflicting_evidence}
        assert conflict_ids == {"E-git-005", "E-metadata-003"}


class TestBackwardCompatibility:
    def test_transition_result_constructs_without_explanation(self):
        result = TransitionResult(verdict=TransitionVerdict.ACCEPT)
        assert result.explanation is None
        assert result.accepted is True

    def test_transition_result_constructs_positionally_as_before(self):
        result = TransitionResult(TransitionVerdict.ACCEPT, ())
        assert result.verdict == TransitionVerdict.ACCEPT
        assert result.violations == ()
        assert result.explanation is None

    def test_verdict_and_violations_fields_unchanged(self):
        field_names = [f.name for f in dataclasses.fields(TransitionResult)]
        assert field_names[0] == "verdict"
        assert field_names[1] == "violations"

    def test_no_required_field_was_removed(self):
        field_names = {f.name for f in dataclasses.fields(TransitionResult)}
        assert {"verdict", "violations", "explanation"} <= field_names

    def test_accepted_property_still_works_regardless_of_explanation(self):
        result = validate_transition(_certified_state(), _complete_phase_transition(), _target())
        assert result.accepted is True
        assert result.explanation is not None


class TestLifecycleCommandBehaviorUnchanged:
    """This module (repository_transition_validator.py) is the only
    file changed for 115F's verdict/explanation logic -- lifecycle
    commands, repository_transition_integration.py, and notification
    code are untouched. This is proven primarily by the existing
    lifecycle integration test suites (test_repository_transition_
    validator_phase_complete_integration.py,
    test_repository_transition_validator_task_finish_integration.py)
    passing completely unmodified; this test adds a direct assertion
    that the integration bridge's own printed-output helper never reads
    the new field."""

    def test_integration_bridge_never_reads_explanation_field(self):
        import pcae.core.repository_transition_integration as bridge
        source = Path(bridge.__file__).read_text(encoding="utf-8")
        assert "result.explanation" not in source
        assert ".explanation" not in source


class TestNoExecutionCapabilityIntroduced:
    def test_execution_unavailable_check_unaffected(self):
        result = validate_transition(
            _certified_state(execution_availability="unavailable"), _complete_phase_transition(), _target(),
        )
        assert not any(
            v.invariant == "no_execution_availability_unless_contracted" for v in result.violations
        )
        runtime_result = next(
            r for r in result.explanation.invariant_results
            if r.invariant_id == "runtime_execution_unavailable"
        )
        assert runtime_result.status is InvariantStatus.PASS

    def test_no_subprocess_or_execution_import_added(self):
        import pcae.core.repository_transition_validator as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("subprocess" in line for line in import_lines)
        assert not any("evidence_providers" in line for line in import_lines)
