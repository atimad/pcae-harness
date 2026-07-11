"""Tests for Phase 134E.9 — Report Consistency / Derived Correctness Validation.

The 134D implementation plan's authoritative scope for 134E.9 (see
docs/PHASE_134_CANONICAL_PHASE_FINALIZATION_IMPLEMENTATION_PLAN.md
Section 3): "a reusable validation manifest comparing any derived
view/rendering back to its source canonical record, checking for
invented content, silent omission, or unauthorized strengthening of
uncertainty/classification", wired fail-closed into the existing
finalization gate (``validate_finalization_gate()``), never a second
competing gate.

Direct source inspection before this phase began confirmed neither
``validate_internal_report_coherence()`` nor ``validate_finalization_
gate()`` ever read ``architecture_status["freshness"]`` or
``["conflicts"]`` -- a report could be promoted/dispatched while
carrying a stale/invalid or conflicted sealed Architecture Status
snapshot. Only self-recommendation was rejected, not a recommendation
naming a *different* already-completed phase (the exact stale-132F
defect shape). ``validate_derived_correctness()`` closes both gaps,
checked only against the report's own sealed ``architecture_status``
snapshot -- never a freshly re-read/regenerated one.

No Canonical Engineering Evidence, Evidence Extraction, Phase Report
View, Operator Report View, Rendering Architecture, Delivery Pipeline,
or Delivery Receipt activation. No execution capability. No external
test delivery (no test in this file sets PCAE_NOTIFY_ENABLED or
exercises a live sink).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pcae.core.phase_reports import (
    ALLOWED_RUNTIME_TUPLES,
    COMPLETENESS_COMPLETE,
    COMPLETENESS_INCOMPLETE,
    compute_finalization_snapshot_id,
    compute_report_digest,
    make_phase_report,
    read_latest_report,
    validate_derived_correctness,
    validate_finalization_gate,
    validate_internal_report_coherence,
)


def _fresh_arch_status(**overrides) -> dict:
    base = {
        "schema_version": "1.0",
        "state_marker": "abc123",
        "repository_revision": "deadbeef",
        "completed": [],
        "completed_phase_ids": ["113A", "113B"],
        "completed_chapters": [],
        "in_progress": [],
        "current_phase_id": "999A",
        "planned": [],
        "planned_phase_ids": [],
        "current_runtime_state": "Observed",
        "current_maximum_capability": "observe",
        "execution_availability": "unavailable",
        "freshness": "fresh",
        "limitations": [],
        "conflicts": [],
        "source_provenance": {},
    }
    base.update(overrides)
    return base


def _report(**overrides):
    defaults = dict(
        phase_id="999A",
        phase_name="Test Phase",
        status="completed",
        summary="Phase 999A: test summary.",
        files_changed=3,
        tests_run=10,
        commits=["abc12345"],
        pushed_status="pushed",
        origin_main_head_count=0,
        recommended_next_phase="999B — Next Phase",
        explicit_no_go_confirmations=[f"No issue {i}." for i in range(11)],
        test_results={"fast_green": "10 passed"},
        governance_results={
            "pcae_health": "healthy", "pcae_check": "passed",
            "pcae_doctor_task_memory": "clean", "pcae_push_check": "clean",
        },
    )
    defaults.update(overrides)
    report = make_phase_report(**defaults)
    if "architecture_status" not in overrides:
        report.architecture_status = _fresh_arch_status()
    return report


# ═══════════════════════════════════════════════════════════════════════
# 1. Coherent report passes
# ═══════════════════════════════════════════════════════════════════════


class TestCoherentReportPasses:
    def test_complete_coherent_report_has_no_derived_correctness_issues(self):
        report = _report()
        assert validate_derived_correctness(report) == []

    def test_complete_coherent_report_has_no_internal_coherence_issues(self):
        report = _report()
        assert validate_internal_report_coherence(report) == []


# ═══════════════════════════════════════════════════════════════════════
# 2. Architecture Status freshness/conflicts must block
# ═══════════════════════════════════════════════════════════════════════


class TestArchitectureStatusFreshnessBlocks:
    def test_stale_architecture_status_fails(self):
        report = _report()
        report.architecture_status = _fresh_arch_status(freshness="stale")
        issues = validate_derived_correctness(report)
        assert any("stale" in i for i in issues)

    def test_invalid_architecture_status_fails(self):
        report = _report()
        report.architecture_status = _fresh_arch_status(freshness="invalid")
        issues = validate_derived_correctness(report)
        assert any("invalid" in i for i in issues)

    def test_fresh_architecture_status_with_stale_evidence_still_fails(self):
        """A 'fresh' Architecture Status classification must never
        override contradictory report evidence elsewhere."""
        report = _report(recommended_next_phase="999A — Self")
        report.architecture_status = _fresh_arch_status(freshness="fresh")
        issues = validate_internal_report_coherence(report)
        assert any("recommends itself" in i for i in issues)

    def test_conflicts_present_fails(self):
        report = _report()
        report.architecture_status = _fresh_arch_status(
            conflicts=["132F is both completed and planned"],
        )
        issues = validate_derived_correctness(report)
        assert any("conflicts" in i for i in issues)

    def test_fresh_with_limitations_does_not_block(self):
        report = _report()
        report.architecture_status = _fresh_arch_status(
            freshness="fresh_with_limitations", limitations=["no active phase"],
        )
        assert validate_derived_correctness(report) == []


# ═══════════════════════════════════════════════════════════════════════
# 3. Completed phase self-denial / self-recommendation
# ═══════════════════════════════════════════════════════════════════════


class TestCompletedPhaseDenialAndSelfRecommendation:
    def test_completed_phase_denying_itself_fails(self):
        report = _report(
            explicit_no_go_confirmations=["No 999A work began."] + [f"No issue {i}." for i in range(10)],
        )
        issues = validate_internal_report_coherence(report)
        assert any("denies" in i for i in issues)

    def test_completed_phase_recommending_itself_fails(self):
        report = _report(recommended_next_phase="999A — Self")
        issues = validate_internal_report_coherence(report)
        assert any("recommends itself" in i for i in issues)

    def test_self_recommendation_case_insensitive(self):
        """Phase 134E.9V — independent verification found direct
        adversarial proof that a lowercase self-recommendation
        ("999a — Self") previously bypassed this check entirely: the
        raw regex capture preserves input case, so a case-sensitive
        '==' against phase_id never matched."""
        report = _report(recommended_next_phase="999a — Self (lowercase)")
        issues = validate_internal_report_coherence(report)
        assert any("recommends itself" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════
# 4. Recommended-next-phase already completed (general, not just self)
# ═══════════════════════════════════════════════════════════════════════


class TestRecommendedNextAlreadyCompleted:
    def test_recommending_a_different_already_completed_phase_fails(self):
        report = _report(recommended_next_phase="113A — Advisory Runtime Architecture")
        # 113A is in completed_phase_ids per _fresh_arch_status()
        issues = validate_derived_correctness(report)
        assert any("113A" in i and "already" in i for i in issues)

    def test_recommending_already_completed_phase_case_insensitive(self):
        """Same case-normalization bypass class as self-recommendation
        above, independently found in validate_derived_correctness()'s
        own separate comparison."""
        report = _report(recommended_next_phase="113a — Advisory Runtime Architecture")
        issues = validate_derived_correctness(report)
        assert any("113a" in i and "already" in i for i in issues)

    def test_explicit_corrective_recovery_classification_permits_it(self):
        report = _report(recommended_next_phase="113A — Advisory Runtime Architecture")
        report.metadata["next_phase_classification"] = "corrective_recovery_transition"
        issues = validate_derived_correctness(report)
        assert not any("113A" in i for i in issues)

    def test_stale_132f_planning_not_reintroduced(self):
        report = _report()
        report.architecture_status = _fresh_arch_status(planned_phase_ids=["132F"])
        issues = validate_derived_correctness(report)
        assert any("132F" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════
# 5. Test evidence linked only to another phase
# ═══════════════════════════════════════════════════════════════════════


class TestTestEvidenceLinkedToOtherPhase:
    def test_tests_belonging_only_to_another_phase_fails(self):
        # 999B is same-series (999) as the report's own phase_id (999A)
        # but a different phase -- the exact shape this check catches.
        report = _report(test_results={"999b_tests": "48 passed"})
        issues = validate_internal_report_coherence(report)
        assert any("999B" in i for i in issues)

    def test_explicit_inherited_regression_classification_permits_it(self):
        report = _report(test_results={"999b_regression": "48 passed"})
        report.metadata["test_evidence_classification"] = "inherited_regression"
        issues = validate_internal_report_coherence(report)
        assert not any("999B" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════
# 6. Snapshot / metadata identity mismatch
# ═══════════════════════════════════════════════════════════════════════


class TestSnapshotMetadataIdentityMismatch:
    def test_metadata_identity_mismatch_fails(self):
        report = _report()
        report.metadata["phase_id"] = "999Z"
        issues = validate_internal_report_coherence(report)
        assert any("disagrees" in i for i in issues)

    def test_source_revision_mismatch_fails(self):
        report = _report()
        report.metadata["source_revision"] = "aaaa"
        report.architecture_status["repository_revision"] = "bbbb"
        issues = validate_internal_report_coherence(report)
        assert any("repository revision" in i for i in issues)

    def test_current_phase_snapshot_disagrees_with_report_identity(self):
        report = _report(phase_id="888Z", phase_name="Other")
        report.architecture_status = _fresh_arch_status(current_phase_id="999A")
        issues = validate_derived_correctness(report)
        assert any("888Z" in i and "999A" in i for i in issues)

    def test_sub_phase_current_identity_allowed(self):
        """Sub-phases are allowed to complete independently of the
        snapshot's own current_phase_id (matches validate_phase_identity's
        existing sub-phase allowance)."""
        report = _report(phase_id="999A.2", phase_name="Sub")
        report.architecture_status = _fresh_arch_status(current_phase_id="999A")
        issues = validate_derived_correctness(report)
        assert not any("disagrees" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════
# 7. Runtime tuple validity
# ═══════════════════════════════════════════════════════════════════════


class TestRuntimeTupleValidity:
    def test_allowed_tuple_passes(self):
        report = _report()
        assert ("Observed", "observe", "unavailable") in ALLOWED_RUNTIME_TUPLES
        assert validate_derived_correctness(report) == []

    def test_disallowed_tuple_fails(self):
        report = _report()
        report.architecture_status = _fresh_arch_status(
            current_runtime_state="Observed",
            current_maximum_capability="observe",
            execution_availability="available",
        )
        issues = validate_derived_correctness(report)
        assert any("runtime tuple" in i for i in issues)

    def test_partial_runtime_fields_not_checked(self):
        """Only fully-populated runtime triples are validated -- a
        legitimately-incomplete snapshot (best-effort runtime read) must
        not be treated as a violation."""
        report = _report()
        report.architecture_status = _fresh_arch_status(
            current_runtime_state="", current_maximum_capability="", execution_availability="",
        )
        issues = validate_derived_correctness(report)
        assert not any("runtime tuple" in i for i in issues)


# ═══════════════════════════════════════════════════════════════════════
# 8. Completeness derivation: coherence failure forces incomplete
# ═══════════════════════════════════════════════════════════════════════


class TestCompletenessCannotBeRestored:
    def test_report_completeness_downgraded_on_derived_correctness_failure(self):
        from pcae.core.phase_reports import _apply_derived_correctness

        report = _report()
        report.report_completeness = COMPLETENESS_COMPLETE
        report.architecture_status = _fresh_arch_status(freshness="invalid")
        _apply_derived_correctness(report)
        assert report.report_completeness == COMPLETENESS_INCOMPLETE
        assert "derived_correctness" in report.missing_trust_fields

    def test_all_fields_present_does_not_restore_completeness(self):
        """Presence of every required field must not by itself mark a
        semantically-contradictory report complete."""
        from pcae.core.phase_reports import _apply_derived_correctness

        report = _report()
        report.architecture_status = _fresh_arch_status(conflicts=["x vs y"])
        report.report_completeness = COMPLETENESS_COMPLETE
        report.missing_trust_fields = []
        _apply_derived_correctness(report)
        assert report.report_completeness == COMPLETENESS_INCOMPLETE


# ═══════════════════════════════════════════════════════════════════════
# 9. Finalization gate wiring (shared boundary)
# ═══════════════════════════════════════════════════════════════════════


class TestFinalizationGateWiring:
    def _gate_kwargs(self, report):
        return dict(
            phase_id=report.phase_id,
            report=report,
            metadata={
                "phase_commits": [{"hash": "abc12345"}],
                "commit_attribution": "phase_owned",
            },
            pushed_status="pushed",
            origin_main_head_count=0,
            governance_results=report.governance_results,
            test_results=report.test_results,
            no_go_confirmations=report.explicit_no_go_confirmations,
            recommended_next_phase=report.recommended_next_phase,
        )

    def test_gate_blocks_on_stale_architecture_status(self):
        report = _report()
        report.architecture_status = _fresh_arch_status(freshness="stale")
        from pcae.core.phase_reports import _apply_derived_correctness
        _apply_derived_correctness(report)
        gate = validate_finalization_gate(**self._gate_kwargs(report))
        assert gate["finalizable"] is False
        assert any("derived correctness" in b for b in gate["blockers"])

    def test_gate_allows_coherent_report(self):
        report = _report()
        from pcae.core.phase_reports import _apply_derived_correctness
        _apply_derived_correctness(report)
        report.report_completeness = COMPLETENESS_COMPLETE
        report.missing_trust_fields = []
        gate = validate_finalization_gate(**self._gate_kwargs(report))
        assert not any("derived correctness" in b for b in gate["blockers"])


# ═══════════════════════════════════════════════════════════════════════
# 10. Digest / snapshot determinism (retry preserves identity)
# ═══════════════════════════════════════════════════════════════════════


class TestDigestSnapshotDeterminism:
    def test_report_digest_deterministic_across_repeated_calls(self):
        report = _report()
        assert compute_report_digest(report) == compute_report_digest(report)

    def test_finalization_snapshot_id_deterministic_across_repeated_calls(self):
        report = _report()
        assert compute_finalization_snapshot_id(report) == compute_finalization_snapshot_id(report)

    def test_report_digest_stable_across_notification_result_change(self):
        """A retry that only records a new physical-attempt outcome must
        not change the logical payload digest -- notification_result is
        deliberately excluded from the certified bytes."""
        report = _report()
        digest_before = compute_report_digest(report)
        report.notification_result = {"telegram": "sent"}
        digest_after = compute_report_digest(report)
        assert digest_before == digest_after

    def test_finalization_snapshot_id_changes_on_semantic_field_change(self):
        report = _report()
        snap_before = compute_finalization_snapshot_id(report)
        report.summary = "A materially different summary."
        snap_after = compute_finalization_snapshot_id(report)
        assert snap_before != snap_after

    def test_finalization_snapshot_id_stable_across_volatile_field_change(self):
        report = _report()
        snap_before = compute_finalization_snapshot_id(report)
        report.notification_result = {"telegram": "sent"}
        report.created_at = "2099-01-01T00:00:00+00:00"
        snap_after = compute_finalization_snapshot_id(report)
        assert snap_before == snap_after


# ═══════════════════════════════════════════════════════════════════════
# 11. Repository Intelligence cannot become phase authority
# ═══════════════════════════════════════════════════════════════════════


class TestRepositoryIntelligenceIndependence:
    def test_derived_correctness_does_not_import_repository_intelligence(self):
        import inspect
        import pcae.core.phase_reports as pr_mod
        source = inspect.getsource(pr_mod.validate_derived_correctness)
        assert "repository_intelligence" not in source.lower()
        assert "unified_query" not in source.lower()


# ═══════════════════════════════════════════════════════════════════════
# 12. Inactive Track 134 subsystems remain inactive
# ═══════════════════════════════════════════════════════════════════════


class TestInactiveSubsystemsUnchanged:
    def test_no_delivery_receipt_or_pipeline_import(self):
        import inspect
        import pcae.core.phase_reports as pr_mod
        source = inspect.getsource(pr_mod.validate_derived_correctness)
        assert "delivery_receipt" not in source.lower()
        assert "delivery_pipeline" not in source.lower()
        assert "rendering" not in source.lower()


# ═══════════════════════════════════════════════════════════════════════
# 12.1. Fast-green value validation (Phase 134E.9.1)
# ═══════════════════════════════════════════════════════════════════════
#
# 134E.9's own report reached report_completeness="complete" while
# test_results["fast_green"] literally read "4389 passed, 1 pre-existing
# unrelated failure" -- because fast_green's mandatory-key check
# (_REQUIRED_BASE_TEST_RESULT_KEYS) verified only that the key was
# *present*, never that its free-text value actually reported zero
# failures. This is the exact "report-consistency implementation allowed
# a complete report despite unresolved contradictory test evidence" gap
# Phase 134E.9.1 was chartered to find and repair.


class TestFastGreenValueValidation:
    def test_reported_failure_count_blocks(self):
        report = _report()
        report.test_results = {"fast_green": "4389 passed, 1 pre-existing unrelated failure"}
        issues = validate_derived_correctness(report)
        assert any("fast_green" in i and "1 failure" in i for i in issues)

    def test_reported_failed_count_blocks(self):
        report = _report()
        report.test_results = {"fast_green": "4389 passed, 1 failed"}
        issues = validate_derived_correctness(report)
        assert any("fast_green" in i for i in issues)

    def test_zero_failures_passes(self):
        report = _report()
        report.test_results = {"fast_green": "4390 passed, 0 failed"}
        assert validate_derived_correctness(report) == []

    def test_no_failure_language_passes(self):
        report = _report()
        report.test_results = {"fast_green": "4391 passed"}
        assert validate_derived_correctness(report) == []

    def test_no_escape_hatch_for_narrated_failures(self):
        """Unlike the recommended-next-phase / test-evidence-linkage
        checks, no metadata classification can suppress a real fast_green
        failure -- narration ("pre-existing", "unrelated", "known") is
        not itself verified evidence and must never waive the check."""
        report = _report()
        report.test_results = {"fast_green": "4389 passed, 1 known pre-existing unrelated failure"}
        report.metadata["next_phase_classification"] = "corrective_recovery_transition"
        report.metadata["test_evidence_classification"] = "inherited_regression"
        issues = validate_derived_correctness(report)
        assert any("fast_green" in i for i in issues)

    def test_completeness_downgraded_on_fast_green_failure(self):
        from pcae.core.phase_reports import _apply_derived_correctness

        report = _report()
        report.test_results = {"fast_green": "4389 passed, 1 failed"}
        report.report_completeness = COMPLETENESS_COMPLETE
        _apply_derived_correctness(report)
        assert report.report_completeness == COMPLETENESS_INCOMPLETE

    def test_finalization_gate_blocks_on_fast_green_failure(self):
        report = _report()
        report.test_results = {"fast_green": "4389 passed, 1 failed"}
        gate = validate_finalization_gate(
            phase_id=report.phase_id,
            report=report,
            metadata={"phase_commits": [{"hash": "abc12345"}], "commit_attribution": "phase_owned"},
            pushed_status="pushed",
            origin_main_head_count=0,
            governance_results=report.governance_results,
            test_results=report.test_results,
            no_go_confirmations=report.explicit_no_go_confirmations,
            recommended_next_phase=report.recommended_next_phase,
        )
        assert gate["finalizable"] is False
        assert any("fast_green" in b for b in gate["blockers"])

    def test_missing_fast_green_key_not_flagged_by_this_check(self):
        """Absence is a separate, pre-existing trust-completeness concern
        (_REQUIRED_BASE_TEST_RESULT_KEYS); this check only interprets a
        *present* value."""
        report = _report()
        report.test_results = {}
        assert validate_derived_correctness(report) == []


# ═══════════════════════════════════════════════════════════════════════
# 12.1.1. Fast-green value type-robustness (Phase 134E.9V)
# ═══════════════════════════════════════════════════════════════════════
#
# Independent verification found the original proximity regex applied
# ``str(value)`` to *any* type, proven unsound by direct adversarial
# probing before any test was written:
#   {"passed": 0, "failed": 5}   -> [] (false negative: 5 real failures missed)
#   {"passed": 4390, "failed": 0} -> flagged as "4390 failures" (false positive)
#   True / False / -1 / 0 / None -> [] (silently accepted, no finding)
# ``_fast_green_failure_signal()`` replaces the single regex with
# type-aware structural interpretation: Mapping read by its own
# ``failed``/``failures`` key; bool/bare-int/None are malformed (fail
# closed); str is interpreted by natural-language failure-count,
# explicit "N passed", or this repository's "<passed>/<total>" fraction
# convention (verified widely used in existing fixtures, e.g. "100/100",
# "3305/3305", "1/1") -- anything else fails closed as malformed.


class TestFastGreenValueTypeRobustness:
    def test_mapping_with_failed_key_nonzero_blocks(self):
        report = _report()
        report.test_results = {"fast_green": {"passed": 0, "failed": 5}}
        issues = validate_derived_correctness(report)
        assert any("5 failure" in i for i in issues)

    def test_mapping_with_failed_key_zero_passes(self):
        report = _report()
        report.test_results = {"fast_green": {"passed": 4390, "failed": 0}}
        assert validate_derived_correctness(report) == []

    def test_mapping_without_recognized_key_is_malformed(self):
        report = _report()
        report.test_results = {"fast_green": {"result": "green"}}
        issues = validate_derived_correctness(report)
        assert any("malformed" in i for i in issues)

    def test_mapping_failed_key_non_int_value_is_malformed(self):
        report = _report()
        report.test_results = {"fast_green": {"failed": "none"}}
        issues = validate_derived_correctness(report)
        assert any("malformed" in i for i in issues)

    def test_boolean_true_is_malformed_not_accepted_as_one(self):
        report = _report()
        report.test_results = {"fast_green": True}
        issues = validate_derived_correctness(report)
        assert any("malformed" in i for i in issues)

    def test_boolean_false_is_malformed_not_accepted_as_zero(self):
        report = _report()
        report.test_results = {"fast_green": False}
        issues = validate_derived_correctness(report)
        assert any("malformed" in i for i in issues)

    def test_bare_negative_int_is_malformed(self):
        report = _report()
        report.test_results = {"fast_green": -1}
        issues = validate_derived_correctness(report)
        assert any("malformed" in i for i in issues)

    def test_bare_positive_int_is_malformed_no_unit(self):
        """A bare int has no unit -- it is never safe to guess whether
        it means 'N passed' or 'N failed'."""
        report = _report()
        report.test_results = {"fast_green": 4391}
        issues = validate_derived_correctness(report)
        assert any("malformed" in i for i in issues)

    def test_none_value_is_malformed(self):
        report = _report()
        report.test_results = {"fast_green": None}
        issues = validate_derived_correctness(report)
        assert any("malformed" in i for i in issues)

    def test_unparseable_string_is_malformed(self):
        report = _report()
        report.test_results = {"fast_green": "xyz status unknown"}
        issues = validate_derived_correctness(report)
        assert any("malformed" in i for i in issues)

    def test_fraction_format_all_passed(self):
        report = _report()
        report.test_results = {"fast_green": "4390/4390"}
        assert validate_derived_correctness(report) == []

    def test_fraction_format_widely_used_conventions_pass(self):
        for value in ("100/100", "3305/3305", "1/1"):
            report = _report()
            report.test_results = {"fast_green": value}
            assert validate_derived_correctness(report) == [], value

    def test_fraction_format_with_shortfall_blocks(self):
        report = _report()
        report.test_results = {"fast_green": "4389/4390"}
        issues = validate_derived_correctness(report)
        assert any("1 failure" in i for i in issues)

    def test_fraction_passed_exceeds_total_is_malformed(self):
        report = _report()
        report.test_results = {"fast_green": "10/5"}
        issues = validate_derived_correctness(report)
        assert any("malformed" in i for i in issues)

    def test_empty_string_treated_as_no_assertion_not_malformed(self):
        """An explicitly empty string is a distinct, pre-existing
        trust-completeness concern (empty required field), not this
        check's malformed-value finding."""
        report = _report()
        report.test_results = {"fast_green": ""}
        assert validate_derived_correctness(report) == []


# ═══════════════════════════════════════════════════════════════════════
# 12.2. `pcae phase-report create` shares the coherence/derived-correctness
# boundary (Phase 134E.9.1)
# ═══════════════════════════════════════════════════════════════════════
#
# Direct inspection during 134E.9.1 confirmed `run_phase_report_create()`
# called only `report.apply_trust_assessment()` -- never `_apply_
# canonical_and_trust()`, the function that additionally runs
# `validate_internal_report_coherence()` and `validate_derived_
# correctness()`. `pcae phase complete` (`phase.py`) and `pcae task
# finish` (`task.py`) both already called the shared helper; `phase-
# report create` silently did not, so a report built through this
# specific governed command could reach `report_completeness: complete`
# with contradictory evidence (self-recommendation, a stale Architecture
# Status snapshot, a failing fast_green value) with no check ever
# running -- exactly the gap that let 134E.9's own report through.


class TestPhaseReportCreateSharesCoherenceBoundary:
    def _args(self, tmp_path, **overrides):
        from argparse import Namespace
        defaults = dict(
            phase_id="999A", phase_name="Test Phase", status="completed",
            summary="Test.", started_at=None, completed_at="",
            files_changed=3, tests_run=10, pushed_status="pushed",
            origin_main_head_count=0, recommended_next_phase="999A — Self",
            commit=["abc12345"],
            governance_result=[
                "pcae_check=passed", "pcae_health=healthy",
                "pcae_doctor_task_memory=clean", "pcae_push_check=clean",
                "telegram_runtime=configured",
            ],
            test_result=[
                "fast_green=100 passed",
                "bootstrap_session_reporting_tests=not_applicable",
                "report_notification_tests=not_applicable",
            ],
            no_go_confirmation=[f"No issue {i}." for i in range(11)],
            reports_dir=str(tmp_path), json=True,
        )
        defaults.update(overrides)
        return Namespace(**defaults)

    def test_self_recommendation_downgrades_completeness(self, tmp_path, monkeypatch):
        """A self-recommending report (the exact 134E.8.1 defect shape)
        must never reach complete through this command."""
        from pcae.commands.phase_reports import run_phase_report_create

        monkeypatch.chdir(tmp_path)
        (tmp_path / "PROJECT_STATUS.md").write_text(
            "# Project Status\n\n## Current Phase\n\n"
            "Phase 999A — Test Phase (completed).\n\n"
            "Recommended next phase: 999B — Next.\n\n"
            "## Phase 999A Complete\n\nPhase 999A — Test Phase.\n"
        )
        args = self._args(tmp_path)
        run_phase_report_create(args)
        report = read_latest_report(tmp_path)
        assert report.report_completeness != "complete"
        assert any("recommends itself" in w for w in report.trust_warnings)

    def test_failing_fast_green_downgrades_completeness(self, tmp_path, monkeypatch):
        """The exact 134E.9 defect shape: a report whose own fast_green
        value states a failure must never reach complete through this
        command either."""
        from pcae.commands.phase_reports import run_phase_report_create

        monkeypatch.chdir(tmp_path)
        (tmp_path / "PROJECT_STATUS.md").write_text(
            "# Project Status\n\n## Current Phase\n\n"
            "Phase 999A — Test Phase (completed).\n\n"
            "Recommended next phase: 999B — Next.\n\n"
            "## Phase 999A Complete\n\nPhase 999A — Test Phase.\n"
        )
        args = self._args(
            tmp_path,
            recommended_next_phase="999B — Next",
            test_result=["fast_green=4389 passed, 1 failed"],
        )
        run_phase_report_create(args)
        report = read_latest_report(tmp_path)
        assert report.report_completeness != "complete"
        assert any("fast_green" in w for w in report.trust_warnings)

    def test_coherent_report_still_reaches_complete(self, tmp_path, monkeypatch):
        """The wiring fix must not make every report incomplete -- a
        genuinely coherent report still reaches complete."""
        from pcae.commands.phase_reports import run_phase_report_create

        monkeypatch.chdir(tmp_path)
        (tmp_path / "PROJECT_STATUS.md").write_text(
            "# Project Status\n\n## Current Phase\n\n"
            "Phase 999A — Test Phase (completed).\n\n"
            "Recommended next phase: 999B — Next.\n\n"
            "## Phase 999A Complete\n\nPhase 999A — Test Phase.\n"
        )
        args = self._args(tmp_path, recommended_next_phase="999B — Next")
        rc = run_phase_report_create(args)
        assert rc == 0
        report = read_latest_report(tmp_path)
        assert report.report_completeness == "complete"


# ═══════════════════════════════════════════════════════════════════════
# 13. CLI inspection is side-effect-free
# ═══════════════════════════════════════════════════════════════════════


class TestConsistencyInspectionSideEffectFree:
    def test_inspection_does_not_mutate_latest_or_marker(self, tmp_path, monkeypatch):
        from argparse import Namespace
        from pcae.commands.phase_reports import run_phase_report_consistency
        from pcae.core.phase_reports import write_phase_report

        monkeypatch.chdir(tmp_path)
        reports_dir = tmp_path / "reports"
        report = _report()
        write_phase_report(report, reports_dir)

        latest_before = (reports_dir / "latest.json").read_text()
        marker_path = tmp_path / ".pcae" / "phase-reports" / ".last-notified.json"
        marker_existed_before = marker_path.exists()

        args = Namespace(reports_dir=str(reports_dir), json=True)
        rc = run_phase_report_consistency(args)

        assert rc in (0, 1)
        assert (reports_dir / "latest.json").read_text() == latest_before
        assert marker_path.exists() == marker_existed_before

    def test_inspection_with_no_report_returns_error_code(self, tmp_path, monkeypatch):
        from argparse import Namespace
        from pcae.commands.phase_reports import run_phase_report_consistency

        monkeypatch.chdir(tmp_path)
        args = Namespace(reports_dir=str(tmp_path / "reports"), json=True)
        rc = run_phase_report_consistency(args)
        assert rc == 2


# ═══════════════════════════════════════════════════════════════════════
# 14. Real repository: current terminal report is consistent
# ═══════════════════════════════════════════════════════════════════════


class TestRealRepositoryConsistency:
    """Phase 134E.9.1 — this class previously asserted the live
    ``.pcae/phase-reports/latest.json`` artifact is always fully
    consistent. That artifact is mutable operational state, not code
    under test: as soon as a later phase's own persisted report becomes
    "latest", or a later phase adds a stricter validator (exactly what
    134E.9.1 itself does -- see ``TestFastGreenValueValidation`` below,
    added by this same corrective phase), the assertion can legitimately
    flip without any code regression -- the same live-repository-state
    coupling this corrective phase found and repaired in
    ``test_dry_run_simulation.py::test_pytest_dry_run_not_blocked``.
    Removed rather than weakened: the validators themselves remain
    exhaustively covered by the 34+ fixture-based tests above, which
    construct explicit, deterministic report state rather than reading
    whatever happens to be on disk. Ad hoc inspection of the real latest
    report remains available, side-effect-free, via
    ``pcae phase-report consistency``."""
