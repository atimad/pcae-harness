"""Phase 137I.1 — Finalization Ordering Deadlock Repair.

These tests pin the two code changes that eliminate the finalization-ordering
deadlock (a completed-but-unpushed phase whose canonical report could not be
written because the finalization gate hard-blocks on ``origin/main..HEAD > 0``,
while ``pcae push`` refused because the phase-report-identity gate (137F.1)
requires a canonical report identifying that same phase):

  1. ``blockers_are_push_state_only`` — the closed classifier that decides
     whether the ONLY obstacle to finalization is "not pushed yet."
  2. ``finalize_phase_report(..., allow_pending_push=True)`` — writes a
     NON-AUTHORITATIVE ``pending_push`` canonical report (identity-correct,
     never notified) instead of quarantining, but ONLY for push-state-only
     blockers; every genuine integrity blocker still quarantines.
  3. Case-insensitive phase-identity consistency in the transition validator.

Non-executing, non-authorizing. No real network. Runtime unchanged
(Observed / observe / unavailable).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pcae.core.phase_reports import (
    COMPLETENESS_PENDING_PUSH,
    blockers_are_push_state_only,
    finalize_phase_report,
    read_latest_report,
)
from pcae.core.repository_transition_validator import (
    RepositoryState,
    _check_phase_identity_consistency,
)


PUSH_ONLY_BLOCKERS = [
    "pushed_status is 'not_pushed', not pushed/clean",
    "origin/main..HEAD is 5, not 0",
    "report completeness is 'partial', not complete",
    "missing trust fields: pushed_status, origin_main_head",
]
PUSH_ONLY_MISSING = ["pushed_status", "origin_main_head"]


class TestBlockersArePushStateOnly:
    def test_pure_push_state_blockers_recognized(self):
        assert blockers_are_push_state_only(PUSH_ONLY_BLOCKERS, PUSH_ONLY_MISSING) is True

    def test_pcae_push_check_blocker_recognized(self):
        assert blockers_are_push_state_only(
            ["pcae_push_check is 'pending', not clean"], []
        ) is True

    def test_integrity_blocker_disqualifies(self):
        blockers = PUSH_ONLY_BLOCKERS + ["phase identity: report phase_id mismatch"]
        assert blockers_are_push_state_only(blockers, PUSH_ONLY_MISSING) is False

    def test_non_push_missing_field_disqualifies(self):
        assert blockers_are_push_state_only(
            ["origin/main..HEAD is 5, not 0"], ["files_changed"]
        ) is False

    def test_missing_trust_fields_with_non_push_field_disqualifies(self):
        assert blockers_are_push_state_only(
            ["missing trust fields: pushed_status, governance_results.pcae_check"], []
        ) is False

    def test_empty_blockers_is_not_push_state_only(self):
        # No blockers at all is a finalizable gate, not a pending-eligible one.
        assert blockers_are_push_state_only([], []) is False


def _complete_except_push_kwargs():
    """Report content that is complete in every dimension EXCEPT that the
    phase is not pushed yet (pushed_status/origin_main_head)."""
    return dict(
        files_changed=2, tests_run=3,
        test_results={
            "report_notification_tests": "20/20 passed",
            "bootstrap_session_reporting_tests": "present",
            "fast_green": "4391 passed, 0 failed",
        },
        commit_attribution="phase_owned",
        architecture_status_snapshot={},
        governance_results={
            "pcae_health": "healthy",
            "pcae_check": "passed",
            "pcae_doctor_task_memory": "clean",
            "pcae_push_check": "clean",
            "telegram_runtime": "configured, enabled",
        },
        commits=["abc12345"],
        explicit_no_go_confirmations=["No X", "No Y", "No Z"],
        recommended_next_phase="900Z — Next",
    )


class TestFinalizePendingPush:
    def _gate(self):
        return {"finalizable": False, "blockers": list(PUSH_ONLY_BLOCKERS)}

    def test_pending_push_writes_canonical_latest_non_authoritative(self):
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)
            fin = finalize_phase_report(
                phase_id="900P", phase_name="Pending Test", status="completed",
                summary="Pending push staging.", reports_dir=reports_dir,
                pushed_status="not_pushed", origin_main_head_count=5,
                gate=self._gate(),
                allow_pending_push=True,
                **_complete_except_push_kwargs(),
            )
            assert fin.get("pending_push") is True
            assert fin.get("blocked") is False
            # Canonical latest.* written (so push readiness identity can pass).
            assert (reports_dir / "latest.json").exists()
            assert (reports_dir / "latest.md").exists()
            data = json.loads((reports_dir / "latest.json").read_text())
            assert data["phase_id"] == "900P"
            # NON-authoritative: pending, never complete.
            assert data["report_completeness"] == COMPLETENESS_PENDING_PUSH
            # Never notified.
            assert fin["notification_skipped"] is True
            assert fin["notification_kind"] == "pending"

    def test_pending_push_requires_opt_in(self):
        # Without allow_pending_push, a push-state-only blocked gate still
        # quarantines (unchanged pre-137I.1 behavior).
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)
            fin = finalize_phase_report(
                phase_id="900Q", phase_name="No Optin", status="completed",
                summary="Quarantine expected.", reports_dir=reports_dir,
                pushed_status="not_pushed", origin_main_head_count=5,
                gate=self._gate(),
            )
            assert fin["blocked"] is True
            assert not (reports_dir / "latest.json").exists()

    def test_integrity_blocker_never_staged_even_with_opt_in(self):
        # A genuine integrity blocker must quarantine even when the operator
        # asked to stage pending — the escape is ONLY for "not pushed yet."
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)
            gate = {
                "finalizable": False,
                "blockers": PUSH_ONLY_BLOCKERS + ["phase identity: mismatch"],
            }
            fin = finalize_phase_report(
                phase_id="900R", phase_name="Integrity", status="completed",
                summary="Quarantine expected.", reports_dir=reports_dir,
                pushed_status="not_pushed", origin_main_head_count=5,
                gate=gate, allow_pending_push=True,
            )
            assert fin["blocked"] is True
            assert fin.get("pending_push") is not True
            assert not (reports_dir / "latest.json").exists()


class TestCaseInsensitivePhaseIdentity:
    def test_case_variant_ids_do_not_disagree(self):
        state = RepositoryState(
            phase_id="137I",
            active_task_phase_id="137i",
            metadata_phase_id="137I",
        )
        assert _check_phase_identity_consistency(state) is None

    def test_genuinely_distinct_ids_still_disagree(self):
        state = RepositoryState(
            phase_id="137I",
            active_task_phase_id="137I.1",
            metadata_phase_id="137I",
        )
        violation = _check_phase_identity_consistency(state)
        assert violation is not None
        assert violation.invariant == "phase_identity_consistency"
