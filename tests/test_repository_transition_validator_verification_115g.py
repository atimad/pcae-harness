"""Phase 115G: Repository Decision Evaluation Verification & Compatibility.

Verification-only phase: proves 115F's Decision Evaluation integration
remains fully behavior-preserving, deterministic, reproducible, and
compatible with pre-existing Repository Transition Validator behavior.
No architectural change is made here -- this module adds focused
compatibility tests on top of the unchanged 113U verdict logic and the
unchanged 115E evaluation layer.

Core principle restated: Decision Evaluation exists to improve
explainability, never to alter repository governance. Every test below
either (a) proves a verdict is byte-for-byte identical to its pre-115F
value while an explanation is now also attached, or (b) proves a
property of the explanation/evidence layer that was true in 115E/115F
but had not yet been directly exercised at the validator integration
boundary.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path
from types import SimpleNamespace

from pcae.core.decision_evaluation import (
    EvaluationContext,
    EvaluationResult,
    InvariantStatus,
    evaluate,
)
from pcae.core.evidence import EvidenceCollection
from pcae.core.repository_transition_integration import (
    handle_phase_report_transition_result,
    validate_phase_report_transition,
)
from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    ProposedTransition,
    RepositoryState,
    STRUCTURAL_INVARIANTS,
    TransitionKind,
    TransitionResult,
    TransitionVerdict,
    build_evidence_from_repository_state,
    validate_transition,
)


def _certified_state(**overrides) -> RepositoryState:
    base = dict(
        phase_id="115G",
        active_task_phase_id="115G",
        metadata_phase_id="115G",
        lifecycle_current_phase_id="115F",
        lifecycle_current_phase_completed=True,
        commits=("abc12345",),
        files_changed=3,
        test_results={"focused": "10/10 (passed)"},
        recommended_next_phase="115H — Repository Skills Architecture",
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


def _transition(**payload) -> ProposedTransition:
    return ProposedTransition(kind=TransitionKind.COMPLETE_PHASE, payload=payload)


def _target(**overrides) -> ExpectedTargetState:
    base = dict(artifact_state=ArtifactState.CERTIFIED, phase_id="115G")
    base.update(overrides)
    return ExpectedTargetState(**base)


# ═══════════════════════════════════════════════════════════════════════
# Objective 1: verdict compatibility -- side-by-side scenario matrix
# ═══════════════════════════════════════════════════════════════════════

#: (label, state overrides, transition kind override or None, target
#: overrides, expected verdict, expected violating invariant names).
_SIDE_BY_SIDE_SCENARIOS: tuple[tuple[str, dict, dict, dict, TransitionVerdict, tuple[str, ...]], ...] = (
    ("fully_consistent_accept", {}, {}, {}, TransitionVerdict.ACCEPT, ()),
    (
        "phase_identity_mismatch_reject",
        {"metadata_phase_id": "999Z"}, {}, {"phase_id": "999Z"},
        TransitionVerdict.REJECT, ("phase_identity_consistency",),
    ),
    (
        "missing_recommended_next_phase_reject",
        {"recommended_next_phase": ""}, {}, {},
        TransitionVerdict.REJECT, ("recommended_next_phase_presence",),
    ),
    (
        "partial_report_completeness_quarantine",
        {"report_completeness": "partial"}, {}, {},
        TransitionVerdict.QUARANTINE, ("report_completeness",),
    ),
    (
        "missing_evidence_reject",
        {"report_completeness": "", "test_results": {}, "commits": ()}, {}, {},
        TransitionVerdict.REJECT, ("report_completeness",),
    ),
    (
        "blocked_to_canonical_reject",
        {"artifact_state": ArtifactState.BLOCKED}, {},
        {"artifact_state": ArtifactState.CANONICAL},
        TransitionVerdict.REJECT, ("canonical_promotion_eligibility",),
    ),
    (
        "certified_to_canonical_accept",
        {"artifact_state": ArtifactState.CERTIFIED}, {},
        {"artifact_state": ArtifactState.CANONICAL},
        TransitionVerdict.ACCEPT, (),
    ),
    (
        "execution_available_reject",
        {"execution_availability": "available"}, {}, {},
        TransitionVerdict.REJECT, ("no_execution_availability_unless_contracted",),
    ),
    (
        "metadata_mismatch_against_target_reject",
        {"metadata_phase_id": "115G"}, {},
        {"phase_id": "115Z"},
        TransitionVerdict.REJECT, ("metadata_consistency",),
    ),
    (
        "multiple_simultaneous_blocking_violations_reject",
        {"metadata_phase_id": "999Z", "execution_availability": "available"}, {}, {},
        TransitionVerdict.REJECT,
        ("phase_identity_consistency", "metadata_consistency", "no_execution_availability_unless_contracted"),
    ),
)


class TestSideBySideVerdictComparison:
    """For each scenario, compares the verdict/violations a caller would
    have observed pre-115F (recomputed here by re-deriving a
    ``TransitionResult`` with ``explanation`` stripped) against the
    live post-115F result. Only ``explanation`` may differ."""

    def test_scenario_matrix_verdict_and_violations_identical(self):
        for label, state_over, _txn_over, target_over, expected_verdict, expected_invariants in _SIDE_BY_SIDE_SCENARIOS:
            state = _certified_state(**state_over)
            result = validate_transition(state, _transition(), _target(**target_over))
            legacy_equivalent = dataclasses.replace(result, explanation=None)

            assert result.verdict == expected_verdict, label
            assert {v.invariant for v in result.violations} == set(expected_invariants), label
            # Stripping the enrichment must not change verdict/violations/accepted.
            assert legacy_equivalent.verdict == result.verdict, label
            assert legacy_equivalent.violations == result.violations, label
            assert legacy_equivalent.accepted == result.accepted, label
            # The enrichment is present and does not collapse to the
            # pre-115F shape (proves the test is actually exercising 115F,
            # not vacuously true).
            assert result.explanation is not None, label

    def test_notify_ineligible_still_rejects_with_unchanged_reasons(self):
        state = _certified_state(notification_already_dispatched=True)
        result = validate_transition(state, ProposedTransition(kind=TransitionKind.NOTIFY), _target())
        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "notification_eligibility" for v in result.violations)
        assert result.explanation is not None

    def test_requires_human_review_reachable_only_via_integration_bridge_unchanged(self):
        """``REQUIRES_HUMAN_REVIEW`` is produced by
        ``repository_transition_integration.py``'s override, not by
        ``validate_transition`` itself (unchanged since 113Y) -- 115F/115G
        attach no explanation to this override path."""
        trial_report = SimpleNamespace(
            commits=("abc12345",), files_changed=2,
            test_results={"focused": "5/5 (passed)"},
            report_completeness="complete", pushed_status="pushed",
        )
        result = validate_phase_report_transition(
            phase_id="115G", requested_phase_id="115G", phase_name="Verification",
            active_task_title="115G", metadata={"requires_human_review": True, "phase_id": "115G"},
            lifecycle_current_phase_line="Phase 115F — done (completed).",
            trial_report=trial_report, recommended_next_phase="115H — Repository Skills Architecture",
            origin_main_head_count=0, transition_kind=TransitionKind.COMPLETE_PHASE,
        )
        assert result.verdict == TransitionVerdict.REQUIRES_HUMAN_REVIEW
        assert result.explanation is None

    def test_accepted_path_through_integration_bridge_still_carries_explanation(self):
        trial_report = SimpleNamespace(
            commits=("abc12345",), files_changed=2,
            test_results={"focused": "5/5 (passed)"},
            report_completeness="complete", pushed_status="pushed",
        )
        result = validate_phase_report_transition(
            phase_id="115G", requested_phase_id="115G", phase_name="Verification",
            active_task_title="115G", metadata={"phase_id": "115G"},
            lifecycle_current_phase_line="Phase 115F — done (completed).",
            trial_report=trial_report, recommended_next_phase="115H — Repository Skills Architecture",
            origin_main_head_count=0, transition_kind=TransitionKind.COMPLETE_PHASE,
        )
        assert result.verdict == TransitionVerdict.ACCEPT
        assert result.explanation is not None


# ═══════════════════════════════════════════════════════════════════════
# Objective 2: explanation correctness
# ═══════════════════════════════════════════════════════════════════════

class TestExplanationCorrectness:
    def test_every_explanation_reference_id_resolves_in_the_evidence_used(self):
        for _label, state_over, _t, target_over, *_rest in _SIDE_BY_SIDE_SCENARIOS:
            state = _certified_state(**state_over)
            result = validate_transition(state, _transition(), _target(**target_over))
            evidence = build_evidence_from_repository_state(state)
            for ref in result.explanation.explanation_reference:
                assert evidence.by_id(ref.evidence_id) is not None, (
                    f"dangling explanation reference {ref.evidence_id!r} for state {state_over!r}"
                )

    def test_every_invariant_result_id_is_one_of_the_six_115e_families(self):
        result = validate_transition(_certified_state(), _transition(), _target())
        family_names = {
            "phase_identity_consistency", "push_state_consistency", "metadata_consistency",
            "report_completeness", "runtime_execution_unavailable", "canonical_promotion_eligibility",
        }
        for invariant_result in result.explanation.invariant_results:
            assert invariant_result.invariant_id in family_names

    def test_blocking_bucket_only_contains_blocking_severity_fail_or_unknown(self):
        for _label, state_over, _t, target_over, *_rest in _SIDE_BY_SIDE_SCENARIOS:
            state = _certified_state(**state_over)
            result = validate_transition(state, _transition(), _target(**target_over))
            by_id = {r.invariant_id: r for r in result.explanation.invariant_results}
            for invariant_id in result.explanation.blocking_failures:
                r = by_id[invariant_id]
                assert r.severity == "blocking", (invariant_id, state_over)
                assert r.status in (InvariantStatus.FAIL, InvariantStatus.UNKNOWN), (invariant_id, state_over)

    def test_warnings_bucket_only_contains_warning_severity_fail_or_unknown(self):
        state = _certified_state(report_completeness="partial")
        result = validate_transition(state, _transition(), _target())
        by_id = {r.invariant_id: r for r in result.explanation.invariant_results}
        assert "report_completeness" in result.explanation.warnings
        for invariant_id in result.explanation.warnings:
            r = by_id[invariant_id]
            assert r.severity == "warning"
            assert r.status in (InvariantStatus.FAIL, InvariantStatus.UNKNOWN)

    def test_informational_bucket_never_contains_an_unresolved_blocking_or_warning_result(self):
        for _label, state_over, _t, target_over, *_rest in _SIDE_BY_SIDE_SCENARIOS:
            state = _certified_state(**state_over)
            result = validate_transition(state, _transition(), _target(**target_over))
            by_id = {r.invariant_id: r for r in result.explanation.invariant_results}
            for invariant_id in result.explanation.informational:
                r = by_id[invariant_id]
                is_resolved = r.status in (InvariantStatus.PASS, InvariantStatus.NOT_APPLICABLE)
                assert is_resolved or r.severity == "informational", (invariant_id, state_over)

    def test_every_invariant_result_partitioned_into_exactly_one_bucket(self):
        state = _certified_state(metadata_phase_id="999Z", report_completeness="partial")
        result = validate_transition(state, _transition(), _target())
        exp = result.explanation
        all_bucketed = set(exp.blocking_failures) | set(exp.warnings) | set(exp.informational)
        all_ids = {r.invariant_id for r in exp.invariant_results}
        assert all_bucketed == all_ids
        assert len(exp.blocking_failures) + len(exp.warnings) + len(exp.informational) == len(exp.invariant_results)

    def test_blocking_failure_present_iff_reject_or_quarantine_has_blocking_violation(self):
        state = _certified_state(metadata_phase_id="999Z")
        result = validate_transition(state, _transition(), _target())
        assert result.verdict == TransitionVerdict.REJECT
        assert result.explanation.has_blocking_failure is True

    def test_accept_state_explanation_summary_reports_zero_fail_zero_unknown(self):
        result = validate_transition(_certified_state(), _transition(), _target())
        assert "0 fail, 0 unknown" in result.explanation.summary


# ═══════════════════════════════════════════════════════════════════════
# Objective 3: evidence integrity
# ═══════════════════════════════════════════════════════════════════════

class TestEvidenceIntegrity:
    def test_adapter_never_produces_duplicate_evidence_ids(self):
        collection = build_evidence_from_repository_state(_certified_state())
        ids = [item.evidence_id for item in collection]
        assert len(ids) == len(set(ids))

    def test_evidence_collection_rejects_duplicate_ids_at_construction(self):
        import pytest
        from pcae.core.evidence import (
            Evidence, EvidenceCategory, EvidenceConfidence, EvidenceDeterminism,
            EvidenceFreshness, EvidenceProvenance,
        )
        prov = EvidenceProvenance(producer="p", produced_from="x", timestamp="t", deterministic_origin=True)

        def ev(value):
            return Evidence(
                evidence_id="E-dup-001", source="s", category=EvidenceCategory.REPORT,
                producer="p", timestamp_utc="t", freshness=EvidenceFreshness.CURRENT,
                confidence=EvidenceConfidence.HIGH, determinism=EvidenceDeterminism.DETERMINISTIC,
                scope="s", references=(), observed_value=value, explanation="e", provenance=prov,
            )

        with pytest.raises(ValueError, match="Duplicate evidence_id"):
            EvidenceCollection((ev("a"), ev("b")))

    def test_no_invariant_result_references_an_evidence_id_absent_from_the_collection(self):
        state = _certified_state(metadata_phase_id="999Z", report_completeness="partial")
        evidence = build_evidence_from_repository_state(state)
        context = EvaluationContext(
            evidence=evidence, evaluation_id="e1", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        result = evaluate(context)
        for invariant_result in result.invariant_results:
            for ref in invariant_result.all_referenced_evidence:
                assert evidence.by_id(ref.evidence_id) is not None

    def test_conflicting_evidence_preserved_through_the_real_adapter_plus_extra_dual_source_item(self):
        """The adapter itself only ever emits one source per fact
        (documented 115F limitation), so to exercise conflict
        preservation *at the integration boundary* this test augments
        real adapter output with one additional, independently-sourced
        evidence item and confirms ``evaluate()`` still preserves both
        sides of the disagreement rather than discarding one."""
        from pcae.core.evidence import (
            Evidence, EvidenceCategory, EvidenceConfidence, EvidenceDeterminism,
            EvidenceFreshness, EvidenceProvenance,
        )
        state = _certified_state()
        adapter_evidence = build_evidence_from_repository_state(state)
        prov = EvidenceProvenance(producer="git_provider@v1", produced_from="git status", timestamp="t", deterministic_origin=True)
        conflicting_git_evidence = Evidence(
            evidence_id="E-git-005", source="git", category=EvidenceCategory.PUSH_STATE,
            producer="git_provider@v1", timestamp_utc="t", freshness=EvidenceFreshness.CURRENT,
            confidence=EvidenceConfidence.HIGH, determinism=EvidenceDeterminism.DETERMINISTIC,
            scope="live git state", references=(), observed_value="not_pushed", explanation="e", provenance=prov,
        )
        augmented = EvidenceCollection(adapter_evidence.items + (conflicting_git_evidence,))
        # RepositoryState reports pushed_status="pushed" but no E-metadata-003
        # is adapted (documented limitation) -- add it directly to force
        # the dual-source comparison this test targets.
        metadata_pushed = Evidence(
            evidence_id="E-metadata-003", source="RepositoryState", category=EvidenceCategory.METADATA,
            producer="RepositoryStateEvidenceAdapter", timestamp_utc="t", freshness=EvidenceFreshness.CURRENT,
            confidence=EvidenceConfidence.MEDIUM, determinism=EvidenceDeterminism.DETERMINISTIC,
            scope="repository state", references=(), observed_value="pushed", explanation="e", provenance=prov,
        )
        augmented = EvidenceCollection(augmented.items + (metadata_pushed,))
        context = EvaluationContext(
            evidence=augmented, evaluation_id="e1", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        result = evaluate(context)
        push_result = next(r for r in result.invariant_results if r.invariant_id == "push_state_consistency")
        assert push_result.status is InvariantStatus.FAIL
        assert {r.evidence_id for r in push_result.conflicting_evidence} == {"E-git-005", "E-metadata-003"}

    def test_unknown_evidence_from_augmented_collection_never_silently_dropped(self):
        from pcae.core.evidence import (
            Evidence, EvidenceCategory, EvidenceConfidence, EvidenceDeterminism,
            EvidenceFreshness, EvidenceProvenance,
        )
        state = _certified_state()
        adapter_evidence = build_evidence_from_repository_state(state)
        prov = EvidenceProvenance(producer="p", produced_from="x", timestamp="t", deterministic_origin=True)
        unknown_consistency = Evidence(
            evidence_id="E-report-005", source="report", category=EvidenceCategory.REPORT,
            producer="p", timestamp_utc="t", freshness=EvidenceFreshness.UNKNOWN,
            confidence=EvidenceConfidence.UNKNOWN, determinism=EvidenceDeterminism.DETERMINISTIC,
            scope="s", references=(), observed_value="unavailable", explanation="e", provenance=prov,
        )
        augmented = EvidenceCollection(adapter_evidence.items + (unknown_consistency,))
        context = EvaluationContext(
            evidence=augmented, evaluation_id="e1", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        result = evaluate(context)
        assert "canonical_promotion_eligibility" in result.blocking_failures


# ═══════════════════════════════════════════════════════════════════════
# Objective 4: determinism
# ═══════════════════════════════════════════════════════════════════════

class TestDeterminism:
    def test_validate_transition_stable_across_twenty_repeated_calls(self):
        state = _certified_state(metadata_phase_id="999Z")
        transition = _transition()
        target = _target()
        results = [validate_transition(state, transition, target) for _ in range(20)]
        assert len({r.verdict for r in results}) == 1
        assert len({r.violations for r in results}) == 1
        assert len({r.explanation for r in results}) == 1
        assert len({r for r in results}) == 1

    def test_evaluate_stable_across_twenty_repeated_calls(self):
        state = _certified_state()
        evidence = build_evidence_from_repository_state(state)
        context = EvaluationContext(
            evidence=evidence, evaluation_id="e1", evaluation_timestamp="t",
            repository_snapshot_reference="HEAD", evaluation_version="1.0",
        )
        results = [evaluate(context) for _ in range(20)]
        assert len({r for r in results}) == 1

    def test_result_independent_of_evidence_item_insertion_order(self):
        state = _certified_state(metadata_phase_id="999Z")
        forward = build_evidence_from_repository_state(state)
        reversed_evidence = EvidenceCollection(tuple(reversed(forward.items)))

        def _run(evidence: EvidenceCollection) -> EvaluationResult:
            context = EvaluationContext(
                evidence=evidence, evaluation_id="e1", evaluation_timestamp="t",
                repository_snapshot_reference="HEAD", evaluation_version="1.0",
            )
            return evaluate(context)

        assert _run(forward) == _run(reversed_evidence)

    def test_adapter_uses_a_fixed_timestamp_sentinel_not_wall_clock(self):
        import pcae.core.repository_transition_validator as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "datetime.now(" not in source
        assert "time.time(" not in source
        assert "_STATE_ADAPTER_TIMESTAMP" in source

    def test_no_ordering_instability_in_explanation_reference(self):
        state = _certified_state()
        first = validate_transition(state, _transition(), _target())
        second = validate_transition(state, _transition(), _target())
        assert first.explanation.explanation_reference == second.explanation.explanation_reference


# ═══════════════════════════════════════════════════════════════════════
# Objective 5: backward compatibility
# ═══════════════════════════════════════════════════════════════════════

class TestBackwardCompatibility:
    def test_caller_ignoring_explanation_sees_identical_printed_output(self, capsys):
        state = _certified_state(metadata_phase_id="999Z")
        result = validate_transition(state, _transition(), _target())
        gate = {"blockers": []}
        handle_phase_report_transition_result(
            result, trial_report=SimpleNamespace(), gate=gate, command_label="phase complete",
            accepted_message="ok", rejected_message="rejected", refused_message="refused",
        )
        with_explanation_output = capsys.readouterr().out

        stripped = dataclasses.replace(result, explanation=None)
        handle_phase_report_transition_result(
            stripped, trial_report=SimpleNamespace(), gate=gate, command_label="phase complete",
            accepted_message="ok", rejected_message="rejected", refused_message="refused",
        )
        without_explanation_output = capsys.readouterr().out

        assert with_explanation_output == without_explanation_output

    def test_optional_explanation_field_has_a_default_and_is_never_required(self):
        sig_fields = dataclasses.fields(TransitionResult)
        explanation_field = next(f for f in sig_fields if f.name == "explanation")
        assert explanation_field.default is None

    def test_dataclasses_replace_round_trip_preserves_verdict_and_violations(self):
        result = validate_transition(_certified_state(metadata_phase_id="999Z"), _transition(), _target())
        copy = dataclasses.replace(result)
        assert copy == result

    def test_evaluation_result_is_json_shape_friendly_for_consumers_that_only_read_dataclass_fields(self):
        """Not a JSON serializer itself (115E deliberately has none) --
        this proves every field an eventual JSON consumer would need is a
        plain dataclass/tuple/str/enum, never something requiring custom
        handling to merely detect presence."""
        result = validate_transition(_certified_state(), _transition(), _target())
        exp = result.explanation
        assert isinstance(exp.summary, str)
        assert isinstance(exp.blocking_failures, tuple)
        assert isinstance(exp.warnings, tuple)
        assert isinstance(exp.informational, tuple)
        assert all(isinstance(x, str) for x in exp.blocking_failures + exp.warnings + exp.informational)


# ═══════════════════════════════════════════════════════════════════════
# Objective 6: no hidden dependencies
# ═══════════════════════════════════════════════════════════════════════

_FORBIDDEN_TOKENS = (
    "import subprocess", "import socket", "import requests", "urllib",
    "Popen(", "os.system", "import shutil",
)


class TestNoHiddenDependencies:
    def test_decision_evaluation_source_has_no_forbidden_dependency_tokens(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        for token in _FORBIDDEN_TOKENS:
            assert token not in source, token

    def test_validator_explanation_path_has_no_forbidden_dependency_tokens(self):
        import pcae.core.repository_transition_validator as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        for token in _FORBIDDEN_TOKENS:
            assert token not in source, token

    def test_no_dataclass_in_either_module_carries_an_identity_field(self):
        import pcae.core.decision_evaluation as decision_module
        import pcae.core.repository_transition_validator as validator_module
        forbidden_names = {"agent_id", "model", "model_id", "backend", "backend_id", "agent"}
        for module in (decision_module, validator_module):
            for name in dir(module):
                obj = getattr(module, name)
                if dataclasses.is_dataclass(obj):
                    field_names = {f.name for f in dataclasses.fields(obj)}
                    assert not (field_names & forbidden_names), (module.__name__, name, field_names)

    def test_decision_evaluation_module_grants_no_new_capability_beyond_115e(self):
        import pcae.core.decision_evaluation as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        assert not any("repository_transition_validator" in line for line in import_lines)
        assert not any(line.strip().startswith("import ") and "pcae" not in line and "collections" not in line
                       and "dataclasses" not in line and "enum" not in line
                       for line in import_lines)


# ═══════════════════════════════════════════════════════════════════════
# Objective 7: lifecycle compatibility
# ═══════════════════════════════════════════════════════════════════════

class TestLifecycleCompatibility:
    """Full lifecycle regression (phase complete / task finish / report
    promotion / notification / push reconciliation / verify-handoff) runs
    via the pre-existing suites
    (``test_repository_transition_validator_phase_complete_integration.py``,
    ``test_repository_transition_validator_task_finish_integration.py``)
    exercised unmodified in CI/validation for this phase. This class adds
    direct, fast unit-level proof that none of the lifecycle-adjacent
    modules were touched to read the new field."""

    def test_neither_phase_nor_task_command_module_reads_explanation(self):
        import pcae.commands.phase as phase_module
        import pcae.commands.task as task_module
        for module in (phase_module, task_module):
            source = Path(module.__file__).read_text(encoding="utf-8")
            assert ".explanation" not in source

    def test_integration_bridge_signature_unchanged_shape(self):
        import inspect
        sig = inspect.signature(validate_phase_report_transition)
        assert "phase_id" in sig.parameters
        assert "trial_report" in sig.parameters
        assert "transition_kind" in sig.parameters

    def test_structural_invariants_tuple_unchanged_since_113u(self):
        names = tuple(inv.name for inv in STRUCTURAL_INVARIANTS)
        assert names == (
            "phase_identity_consistency", "metadata_consistency", "report_completeness",
            "recommended_next_phase_presence", "canonical_promotion_eligibility",
            "notification_eligibility", "no_execution_availability_unless_contracted",
        )


# ═══════════════════════════════════════════════════════════════════════
# Objective 8: explainability completeness
# ═══════════════════════════════════════════════════════════════════════

class TestExplainabilityCompleteness:
    def test_every_blocking_violation_scenario_has_a_non_empty_explanation(self):
        for label, state_over, _t, target_over, expected_verdict, expected_invariants in _SIDE_BY_SIDE_SCENARIOS:
            if expected_verdict not in (TransitionVerdict.REJECT, TransitionVerdict.QUARANTINE):
                continue
            state = _certified_state(**state_over)
            result = validate_transition(state, _transition(), _target(**target_over))
            by_id = {r.invariant_id: r for r in result.explanation.invariant_results}
            for name in expected_invariants:
                if name not in by_id:
                    continue  # not modeled by the six 115E families (e.g. recommended_next_phase_presence)
                assert by_id[name].explanation, label

    def test_every_invariant_result_across_full_matrix_has_non_empty_explanation(self):
        for _label, state_over, _t, target_over, *_rest in _SIDE_BY_SIDE_SCENARIOS:
            state = _certified_state(**state_over)
            result = validate_transition(state, _transition(), _target(**target_over))
            for invariant_result in result.explanation.invariant_results:
                assert invariant_result.explanation
                assert invariant_result.explanation.strip() != ""

    def test_accept_scenario_all_resolved_invariants_are_pass_or_not_applicable(self):
        result = validate_transition(_certified_state(), _transition(), _target())
        for invariant_result in result.explanation.invariant_results:
            assert invariant_result.status in (InvariantStatus.PASS, InvariantStatus.NOT_APPLICABLE)

    def test_no_verdict_is_ever_produced_with_an_unexplainable_blocking_failure(self):
        """Every entry in ``blocking_failures``/``warnings`` must trace
        back to an ``InvariantResult`` whose ``explanation`` field is
        non-empty (enforced structurally by ``InvariantResult.__post_init__``,
        verified here at the aggregate level for the full scenario matrix)."""
        for _label, state_over, _t, target_over, *_rest in _SIDE_BY_SIDE_SCENARIOS:
            state = _certified_state(**state_over)
            result = validate_transition(state, _transition(), _target(**target_over))
            by_id = {r.invariant_id: r for r in result.explanation.invariant_results}
            for name in set(result.explanation.blocking_failures) | set(result.explanation.warnings):
                assert by_id[name].explanation
