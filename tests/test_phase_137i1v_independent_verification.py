"""Phase 137I.1V — Finalization Ordering Deadlock Independent Verification.

Fresh adversarial tests, independently constructed (not copied from 137I.1's
own suite), that re-derive and attack the 137I.1 pending-report escape and
its supporting fail-closed classifier. Includes a regression test for a
residual instance of the regex-truncation bug class 137I.1 fixed elsewhere
(``_check_canonical_metadata_consistency``'s summary-parsing patterns at
``phase_reports.py`` lines ~1224/1225 still used the old truncating
``(?:\\.[\\d]+)*`` pattern, producing a false "recommended_next_phase
mismatch" for any legitimate report whose free-text summary names a
dotted-and-lettered next-phase id such as "137I.1V" -- ironically including
this very phase), found and repaired during this independent verification.

Non-executing, non-authorizing. No real network. Runtime unchanged
(Observed / observe / unavailable).
"""

from __future__ import annotations

from pcae.core.phase_reports import (
    PhaseReport,
    _check_canonical_metadata_consistency,
    blockers_are_push_state_only,
)


class TestClassifierFailsClosedOnUnknownBlockers:
    """Section 5 of the 137I.1V brief: the closed push-only classifier must
    default to rejection for anything it does not explicitly recognize."""

    def test_unknown_blocker_rejected(self):
        assert (
            blockers_are_push_state_only(["a completely novel blocker string"], [])
            is False
        )

    def test_malformed_missing_trust_field_rejected(self):
        # A missing-trust-fields blocker naming a field outside the closed
        # PUSH_STATE_FIELDS set must disqualify, even mixed with real
        # push-state blockers.
        assert (
            blockers_are_push_state_only(
                [
                    "pushed_status is 'not_pushed', not pushed/clean",
                    "missing trust fields: pushed_status, metadata_consistency",
                ],
                [],
            )
            is False
        )

    def test_case_sensitive_blocker_prefixes_not_accidentally_matched(self):
        # The classifier matches literal blocker-message prefixes emitted by
        # validate_finalization_gate(); a differently-cased or reworded
        # variant must NOT be silently accepted (a naive case-insensitive or
        # substring match would be a fail-open regression).
        assert (
            blockers_are_push_state_only(["PUSHED_STATUS IS 'not_pushed'"], [])
            is False
        )

    def test_duplicate_push_blockers_still_accepted(self):
        assert (
            blockers_are_push_state_only(
                [
                    "pushed_status is 'not_pushed', not pushed/clean",
                    "pushed_status is 'not_pushed', not pushed/clean",
                    "origin/main..HEAD is 5, not 0",
                ],
                [],
            )
            is True
        )


class TestResidualRecommendedNextPhaseTruncation:
    """Regression for the residual regex-truncation instance found during
    137I.1V (phase_reports.py:1224-1225), the same bug class the rest of
    Phase 137I.1 fixed at its sibling patterns."""

    def _report(self, summary: str, recommended_next_phase: str) -> PhaseReport:
        report = PhaseReport(
            phase_id="137I.1",
            phase_name="Test",
            status="completed",
            summary=summary,
        )
        report.recommended_next_phase = recommended_next_phase
        report.canonical_report_content = "# Phase 137I.1 Complete — Test\ncontent"
        report.trust_warnings = []
        report.missing_trust_fields = []
        report.report_completeness = "complete"
        return report

    def test_dotted_lettered_next_phase_no_longer_falsely_mismatches(self):
        report = self._report(
            "Work done. Recommended next phase: 137I.1V — Independent Verification.",
            "137I.1V — Independent Verification",
        )
        _check_canonical_metadata_consistency(report)
        assert report.report_completeness == "complete"
        assert report.missing_trust_fields == []
        assert report.trust_warnings == []

    def test_genuine_next_phase_mismatch_still_detected(self):
        report = self._report(
            "Work done. Recommended next phase: 137J — Something Else.",
            "137I.1V — Independent Verification",
        )
        _check_canonical_metadata_consistency(report)
        assert report.report_completeness == "partial"
        assert "metadata_consistency" in report.missing_trust_fields

    def test_next_phase_form_also_repaired(self):
        report = self._report(
            "Work done. Next phase: 137X.2Y — Some Title.",
            "137X.2Y — Some Title",
        )
        _check_canonical_metadata_consistency(report)
        assert report.report_completeness == "complete"
        assert report.missing_trust_fields == []
