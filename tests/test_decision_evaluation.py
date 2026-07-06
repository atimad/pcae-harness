"""Phase 115E: Repository Decision Evaluation Prototype.

Tests the deterministic evaluation layer implemented in
``src/pcae/core/decision_evaluation.py``: ``EvaluationContext``,
``InvariantResult``, ``EvaluationResult``, and the six evidence-only
invariant families. Evidence never decides; nothing here produces a
``TransitionVerdict`` or is called by the Repository Transition
Validator, any lifecycle command, or any notification path. These tests
call the module directly.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from pcae.core.evidence import (
    Evidence,
    EvidenceCategory,
    EvidenceCollection,
    EvidenceConfidence,
    EvidenceDeterminism,
    EvidenceFreshness,
    EvidenceProvenance,
    EvidenceReference,
)
from pcae.core.decision_evaluation import (
    EvaluationContext,
    EvaluationResult,
    INVARIANT_EVALUATORS,
    InvariantResult,
    InvariantStatus,
    evaluate,
    evaluate_canonical_promotion_eligibility,
    evaluate_metadata_consistency,
    evaluate_phase_identity_consistency,
    evaluate_push_state_consistency,
    evaluate_report_completeness,
    evaluate_runtime_execution_unavailable,
)


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        producer="test-provider", produced_from="unit-test",
        timestamp="2026-07-06T00:00:00Z", deterministic_origin=True,
    )


def _ev(
    evidence_id: str,
    category: EvidenceCategory,
    value,
    *,
    freshness: EvidenceFreshness = EvidenceFreshness.CURRENT,
    confidence: EvidenceConfidence = EvidenceConfidence.HIGH,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source="test",
        category=category,
        producer="test-provider",
        timestamp_utc="2026-07-06T00:00:00Z",
        freshness=freshness,
        confidence=confidence,
        determinism=EvidenceDeterminism.DETERMINISTIC,
        scope="test scope",
        references=(),
        observed_value=value,
        explanation="test evidence",
        provenance=_provenance(),
    )


def _unknown_ev(evidence_id: str, category: EvidenceCategory) -> Evidence:
    return _ev(
        evidence_id, category, "unavailable",
        freshness=EvidenceFreshness.UNKNOWN, confidence=EvidenceConfidence.UNKNOWN,
    )


def _context(*items: Evidence) -> EvaluationContext:
    return EvaluationContext(
        evidence=EvidenceCollection(items),
        evaluation_id="eval-001",
        evaluation_timestamp="2026-07-06T00:00:00Z",
        repository_snapshot_reference="HEAD",
        evaluation_version="1.0",
    )


class TestEvaluationContext:
    def test_constructs_with_required_fields(self):
        ctx = _context()
        assert ctx.evaluation_id == "eval-001"
        assert ctx.evaluation_timestamp == "2026-07-06T00:00:00Z"
        assert ctx.repository_snapshot_reference == "HEAD"
        assert ctx.evaluation_version == "1.0"
        assert isinstance(ctx.evidence, EvidenceCollection)

    def test_is_frozen(self):
        ctx = _context()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ctx.evaluation_id = "other"

    def test_rejects_non_evidence_collection(self):
        with pytest.raises(ValueError, match="EvidenceCollection"):
            EvaluationContext(
                evidence="not a collection",
                evaluation_id="e1", evaluation_timestamp="t",
                repository_snapshot_reference="HEAD", evaluation_version="1.0",
            )

    @pytest.mark.parametrize(
        "field_name",
        ["evaluation_id", "evaluation_timestamp", "repository_snapshot_reference", "evaluation_version"],
    )
    def test_rejects_empty_required_field(self, field_name):
        kwargs = dict(
            evidence=EvidenceCollection(),
            evaluation_id="e1", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        kwargs[field_name] = ""
        with pytest.raises(ValueError, match=field_name):
            EvaluationContext(**kwargs)


class TestInvariantResult:
    def test_constructs_with_required_fields(self):
        result = InvariantResult(
            invariant_id="test_invariant",
            status=InvariantStatus.PASS,
            severity="blocking",
            supporting_evidence=(EvidenceReference(evidence_id="E-1"),),
            conflicting_evidence=(),
            explanation="all good",
        )
        assert result.invariant_id == "test_invariant"
        assert result.status is InvariantStatus.PASS
        assert result.severity == "blocking"
        assert result.suggested_repair is None

    def test_is_frozen(self):
        result = InvariantResult(
            invariant_id="x", status=InvariantStatus.PASS, severity="blocking",
            supporting_evidence=(), conflicting_evidence=(), explanation="e",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.status = InvariantStatus.FAIL

    def test_rejects_empty_invariant_id(self):
        with pytest.raises(ValueError, match="invariant_id"):
            InvariantResult(
                invariant_id="", status=InvariantStatus.PASS, severity="blocking",
                supporting_evidence=(), conflicting_evidence=(), explanation="e",
            )

    def test_rejects_invalid_severity(self):
        with pytest.raises(ValueError, match="severity"):
            InvariantResult(
                invariant_id="x", status=InvariantStatus.PASS, severity="catastrophic",
                supporting_evidence=(), conflicting_evidence=(), explanation="e",
            )

    def test_rejects_empty_explanation(self):
        with pytest.raises(ValueError, match="explanation"):
            InvariantResult(
                invariant_id="x", status=InvariantStatus.PASS, severity="blocking",
                supporting_evidence=(), conflicting_evidence=(), explanation="",
            )

    def test_accepts_raw_string_status(self):
        result = InvariantResult(
            invariant_id="x", status="pass", severity="blocking",
            supporting_evidence=(), conflicting_evidence=(), explanation="e",
        )
        assert result.status is InvariantStatus.PASS

    def test_all_referenced_evidence_combines_both(self):
        result = InvariantResult(
            invariant_id="x", status=InvariantStatus.FAIL, severity="blocking",
            supporting_evidence=(EvidenceReference(evidence_id="E-1"),),
            conflicting_evidence=(EvidenceReference(evidence_id="E-2"),),
            explanation="e",
        )
        ids = [r.evidence_id for r in result.all_referenced_evidence]
        assert ids == ["E-1", "E-2"]

    def test_all_four_statuses_are_frozen(self):
        values = {s.value for s in InvariantStatus}
        assert values == {"pass", "fail", "unknown", "not_applicable"}


class TestEvaluationResult:
    def test_constructs_with_required_fields(self):
        result = EvaluationResult(
            invariant_results=(), summary="0 invariants",
            blocking_failures=(), warnings=(), informational=(),
            explanation_reference=(),
        )
        assert result.summary == "0 invariants"
        assert result.has_blocking_failure is False

    def test_is_frozen(self):
        result = EvaluationResult(
            invariant_results=(), summary="s", blocking_failures=(),
            warnings=(), informational=(), explanation_reference=(),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.summary = "other"

    def test_has_blocking_failure_true_when_present(self):
        result = EvaluationResult(
            invariant_results=(), summary="s", blocking_failures=("x",),
            warnings=(), informational=(), explanation_reference=(),
        )
        assert result.has_blocking_failure is True

    def test_produces_no_transition_verdict_field(self):
        result = EvaluationResult(
            invariant_results=(), summary="s", blocking_failures=(),
            warnings=(), informational=(), explanation_reference=(),
        )
        field_names = {f.name for f in dataclasses.fields(result)}
        assert "verdict" not in field_names


class TestPhaseIdentityConsistency:
    def test_pass_when_ids_match(self):
        ctx = _context(
            _ev("E-report-002", EvidenceCategory.REPORT, "115E"),
            _ev("E-metadata-002", EvidenceCategory.METADATA, "115E"),
        )
        result = evaluate_phase_identity_consistency(ctx.evidence)
        assert result.status is InvariantStatus.PASS

    def test_fail_when_ids_disagree(self):
        ctx = _context(
            _ev("E-report-002", EvidenceCategory.REPORT, "115D"),
            _ev("E-metadata-002", EvidenceCategory.METADATA, "115E"),
        )
        result = evaluate_phase_identity_consistency(ctx.evidence)
        assert result.status is InvariantStatus.FAIL
        assert result.severity == "blocking"
        assert len(result.conflicting_evidence) == 2

    def test_not_applicable_when_no_evidence(self):
        ctx = _context()
        result = evaluate_phase_identity_consistency(ctx.evidence)
        assert result.status is InvariantStatus.NOT_APPLICABLE

    def test_unknown_when_evidence_unknown(self):
        ctx = _context(
            _unknown_ev("E-report-002", EvidenceCategory.REPORT),
            _ev("E-metadata-002", EvidenceCategory.METADATA, "115E"),
        )
        result = evaluate_phase_identity_consistency(ctx.evidence)
        assert result.status is InvariantStatus.UNKNOWN


class TestPushStateConsistency:
    def test_pass_when_agree(self):
        ctx = _context(
            _ev("E-git-005", EvidenceCategory.PUSH_STATE, "pushed"),
            _ev("E-metadata-003", EvidenceCategory.METADATA, "pushed"),
        )
        result = evaluate_push_state_consistency(ctx.evidence)
        assert result.status is InvariantStatus.PASS

    def test_fail_and_preserves_conflict_when_disagree(self):
        """115B's own literal conflict example: declared metadata
        disagrees with live push state."""
        ctx = _context(
            _ev("E-git-005", EvidenceCategory.PUSH_STATE, "pushed"),
            _ev("E-metadata-003", EvidenceCategory.METADATA, "not_pushed"),
        )
        result = evaluate_push_state_consistency(ctx.evidence)
        assert result.status is InvariantStatus.FAIL
        conflict_ids = {r.evidence_id for r in result.conflicting_evidence}
        assert conflict_ids == {"E-git-005", "E-metadata-003"}
        assert result.supporting_evidence == ()

    def test_unknown_when_git_evidence_unknown(self):
        ctx = _context(
            _unknown_ev("E-git-005", EvidenceCategory.PUSH_STATE),
            _ev("E-metadata-003", EvidenceCategory.METADATA, "pushed"),
        )
        result = evaluate_push_state_consistency(ctx.evidence)
        assert result.status is InvariantStatus.UNKNOWN

    def test_not_applicable_when_no_evidence(self):
        result = evaluate_push_state_consistency(EvidenceCollection())
        assert result.status is InvariantStatus.NOT_APPLICABLE


class TestMetadataConsistency:
    def test_pass_when_pushed_and_zero_count(self):
        ctx = _context(
            _ev("E-metadata-003", EvidenceCategory.METADATA, "pushed"),
            _ev("E-metadata-004", EvidenceCategory.METADATA, 0),
        )
        result = evaluate_metadata_consistency(ctx.evidence)
        assert result.status is InvariantStatus.PASS

    def test_pass_when_not_pushed_and_nonzero_count(self):
        ctx = _context(
            _ev("E-metadata-003", EvidenceCategory.METADATA, "not_pushed"),
            _ev("E-metadata-004", EvidenceCategory.METADATA, 3),
        )
        result = evaluate_metadata_consistency(ctx.evidence)
        assert result.status is InvariantStatus.PASS

    def test_fail_when_pushed_but_nonzero_count(self):
        ctx = _context(
            _ev("E-metadata-003", EvidenceCategory.METADATA, "pushed"),
            _ev("E-metadata-004", EvidenceCategory.METADATA, 2),
        )
        result = evaluate_metadata_consistency(ctx.evidence)
        assert result.status is InvariantStatus.FAIL
        assert len(result.conflicting_evidence) == 2

    def test_fail_when_not_pushed_but_zero_count(self):
        ctx = _context(
            _ev("E-metadata-003", EvidenceCategory.METADATA, "not_pushed"),
            _ev("E-metadata-004", EvidenceCategory.METADATA, 0),
        )
        result = evaluate_metadata_consistency(ctx.evidence)
        assert result.status is InvariantStatus.FAIL


class TestReportCompleteness:
    def test_pass_when_complete(self):
        ctx = _context(_ev("E-report-003", EvidenceCategory.REPORT, "complete"))
        result = evaluate_report_completeness(ctx.evidence)
        assert result.status is InvariantStatus.PASS
        assert result.severity == "blocking"

    def test_fail_warning_when_partial(self):
        ctx = _context(_ev("E-report-003", EvidenceCategory.REPORT, "partial"))
        result = evaluate_report_completeness(ctx.evidence)
        assert result.status is InvariantStatus.FAIL
        assert result.severity == "warning"

    def test_fail_blocking_when_missing_value(self):
        ctx = _context(_ev("E-report-003", EvidenceCategory.REPORT, ""))
        result = evaluate_report_completeness(ctx.evidence)
        assert result.status is InvariantStatus.FAIL
        assert result.severity == "blocking"

    def test_not_applicable_when_no_evidence(self):
        result = evaluate_report_completeness(EvidenceCollection())
        assert result.status is InvariantStatus.NOT_APPLICABLE

    def test_unknown_when_evidence_unknown(self):
        ctx = _context(_unknown_ev("E-report-003", EvidenceCategory.REPORT))
        result = evaluate_report_completeness(ctx.evidence)
        assert result.status is InvariantStatus.UNKNOWN


class TestRuntimeExecutionUnavailable:
    def test_pass_when_unavailable(self):
        ctx = _context(_ev("E-runtime-002", EvidenceCategory.RUNTIME, "unavailable"))
        result = evaluate_runtime_execution_unavailable(ctx.evidence)
        assert result.status is InvariantStatus.PASS

    def test_fail_when_available(self):
        ctx = _context(_ev("E-runtime-002", EvidenceCategory.RUNTIME, "available"))
        result = evaluate_runtime_execution_unavailable(ctx.evidence)
        assert result.status is InvariantStatus.FAIL

    def test_not_applicable_when_no_evidence(self):
        result = evaluate_runtime_execution_unavailable(EvidenceCollection())
        assert result.status is InvariantStatus.NOT_APPLICABLE

    def test_unknown_when_evidence_freshness_unknown(self):
        """Regression: observed_value=='unavailable' is *itself* the
        correct domain value here -- unknown-ness must be detected via
        freshness, never by matching that string."""
        ctx = _context(_unknown_ev("E-runtime-002", EvidenceCategory.RUNTIME))
        result = evaluate_runtime_execution_unavailable(ctx.evidence)
        assert result.status is InvariantStatus.UNKNOWN

    def test_genuine_unavailable_value_is_pass_not_unknown(self):
        ctx = _context(_ev(
            "E-runtime-002", EvidenceCategory.RUNTIME, "unavailable",
            freshness=EvidenceFreshness.CURRENT, confidence=EvidenceConfidence.HIGH,
        ))
        result = evaluate_runtime_execution_unavailable(ctx.evidence)
        assert result.status is InvariantStatus.PASS


class TestCanonicalPromotionEligibility:
    def test_pass_when_complete_and_consistent(self):
        ctx = _context(
            _ev("E-report-003", EvidenceCategory.REPORT, "complete"),
            _ev("E-report-005", EvidenceCategory.REPORT, "consistent"),
        )
        result = evaluate_canonical_promotion_eligibility(ctx.evidence)
        assert result.status is InvariantStatus.PASS

    def test_fail_when_partial(self):
        ctx = _context(
            _ev("E-report-003", EvidenceCategory.REPORT, "partial"),
            _ev("E-report-005", EvidenceCategory.REPORT, "consistent"),
        )
        result = evaluate_canonical_promotion_eligibility(ctx.evidence)
        assert result.status is InvariantStatus.FAIL

    def test_fail_when_inconsistent(self):
        ctx = _context(
            _ev("E-report-003", EvidenceCategory.REPORT, "complete"),
            _ev("E-report-005", EvidenceCategory.REPORT, "inconsistent"),
        )
        result = evaluate_canonical_promotion_eligibility(ctx.evidence)
        assert result.status is InvariantStatus.FAIL

    def test_not_applicable_when_no_evidence(self):
        result = evaluate_canonical_promotion_eligibility(EvidenceCollection())
        assert result.status is InvariantStatus.NOT_APPLICABLE


class TestEvidenceReferences:
    def test_every_result_carries_evidence_references_or_is_not_applicable(self):
        ctx = _context(
            _ev("E-report-002", EvidenceCategory.REPORT, "115E"),
            _ev("E-metadata-002", EvidenceCategory.METADATA, "115E"),
            _ev("E-git-005", EvidenceCategory.PUSH_STATE, "pushed"),
            _ev("E-metadata-003", EvidenceCategory.METADATA, "pushed"),
            _ev("E-metadata-004", EvidenceCategory.METADATA, 0),
            _ev("E-report-003", EvidenceCategory.REPORT, "complete"),
            _ev("E-runtime-002", EvidenceCategory.RUNTIME, "unavailable"),
            _ev("E-report-005", EvidenceCategory.REPORT, "consistent"),
        )
        result = evaluate(ctx)
        for r in result.invariant_results:
            if r.status is not InvariantStatus.NOT_APPLICABLE:
                assert len(r.all_referenced_evidence) > 0

    def test_explanation_reference_deduplicates_by_evidence_id(self):
        ctx = _context(
            _ev("E-report-002", EvidenceCategory.REPORT, "115E"),
            _ev("E-metadata-002", EvidenceCategory.METADATA, "115E"),
            _ev("E-report-003", EvidenceCategory.REPORT, "complete"),
            _ev("E-report-005", EvidenceCategory.REPORT, "consistent"),
        )
        result = evaluate(ctx)
        ids = [r.evidence_id for r in result.explanation_reference]
        assert len(ids) == len(set(ids))


class TestDeterministicExplanations:
    def test_same_input_produces_identical_result_twice(self):
        ctx = _context(
            _ev("E-report-002", EvidenceCategory.REPORT, "115D"),
            _ev("E-metadata-002", EvidenceCategory.METADATA, "115E"),
        )
        first = evaluate(ctx)
        second = evaluate(ctx)
        assert first == second

    def test_no_conversational_or_random_content_in_explanations(self):
        ctx = _context(
            _ev("E-report-003", EvidenceCategory.REPORT, "partial"),
        )
        result = evaluate(ctx)
        for r in result.invariant_results:
            assert "I think" not in r.explanation
            assert "probably" not in r.explanation


class TestFullEvaluationBucketing:
    def test_blocking_fail_lands_in_blocking_failures(self):
        ctx = _context(
            _ev("E-report-002", EvidenceCategory.REPORT, "115D"),
            _ev("E-metadata-002", EvidenceCategory.METADATA, "115E"),
        )
        result = evaluate(ctx)
        assert "phase_identity_consistency" in result.blocking_failures

    def test_warning_fail_lands_in_warnings_not_blocking(self):
        ctx = _context(_ev("E-report-003", EvidenceCategory.REPORT, "partial"))
        result = evaluate(ctx)
        assert "report_completeness" in result.warnings
        assert "report_completeness" not in result.blocking_failures

    def test_unknown_blocking_invariant_lands_in_blocking_failures(self):
        """Objective 7: UNKNOWN evidence shall never silently PASS."""
        ctx = _context(_unknown_ev("E-runtime-002", EvidenceCategory.RUNTIME))
        result = evaluate(ctx)
        assert "runtime_execution_unavailable" in result.blocking_failures

    def test_pass_lands_in_informational(self):
        ctx = _context(_ev("E-report-003", EvidenceCategory.REPORT, "complete"))
        result = evaluate(ctx)
        assert "report_completeness" in result.informational

    def test_evaluate_runs_all_six_families(self):
        ctx = _context()
        result = evaluate(ctx)
        assert len(result.invariant_results) == 6
        assert len(INVARIANT_EVALUATORS) == 6

    def test_summary_is_deterministic_string(self):
        ctx = _context()
        result = evaluate(ctx)
        assert "6 invariants evaluated" in result.summary


class TestImmutableEvaluationObjects:
    def test_invariant_result_frozen(self):
        ctx = _context(_ev("E-report-003", EvidenceCategory.REPORT, "complete"))
        result = evaluate(ctx)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.invariant_results[0].status = InvariantStatus.FAIL

    def test_evaluation_result_frozen(self):
        ctx = _context()
        result = evaluate(ctx)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.blocking_failures = ("x",)

    def test_evaluation_context_frozen(self):
        ctx = _context()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ctx.evidence = EvidenceCollection()


class TestNoRuntimeDependencies:
    """Objective 5/9: consumes only Evidence. No Git, filesystem,
    subprocess, runtime inspection, or lifecycle command access."""

    def test_module_imports_only_evidence_and_stdlib(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.startswith("from ") or line.startswith("import ")
        ]
        for line in import_lines:
            assert "pcae." not in line or "pcae.core.evidence" in line

    def test_module_never_imports_subprocess(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "import subprocess" not in source

    def test_module_never_imports_evidence_providers(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("evidence_providers" in line for line in import_lines)

    def test_module_never_imports_os_path_for_filesystem_access(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "import os" not in source
        assert "open(" not in source


class TestNoValidatorIntegration:
    """Objective 9 (115E): this module (``decision_evaluation.py``)
    remains unaware of the Repository Transition Validator -- it must
    never import it, regardless of what the validator does.

    As of 115F, the dependency runs the other way: the validator
    imports this module (one-directional only) to attach an optional
    explanation to its ``TransitionResult``, without this module ever
    importing the validator back or gaining any knowledge of
    ``RepositoryState``/``TransitionVerdict``."""

    def test_decision_evaluation_never_imports_validator(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("repository_transition_validator" in line for line in import_lines)

    def test_validator_imports_decision_evaluation_one_way_only(self):
        """115F: the validator is now allowed (and expected) to import
        this module for explanation enrichment -- but never the
        reverse, proven by ``test_decision_evaluation_never_imports_validator``
        above."""
        import pcae.core.repository_transition_validator as validator_module
        source = Path(validator_module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert any("decision_evaluation" in line for line in import_lines)

    def test_decision_evaluation_never_gains_repository_state_knowledge(self):
        """115F must not make this module aware of RepositoryState/
        TransitionVerdict/TransitionResult -- the adapter and any
        RepositoryState-shaped types belong to the validator side of
        the integration, never here."""
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("RepositoryState" in line or "TransitionVerdict" in line for line in import_lines)

    def test_evaluation_result_is_not_a_transition_result(self):
        from pcae.core.repository_transition_validator import TransitionResult
        assert EvaluationResult is not TransitionResult
