"""Phase 135O — Stage 1 dual derivation integration through the shared
``run_finalization_transaction`` boundary all four production entry
points (``phase_complete``, ``task_finish``, ``phase_report_create``,
``notify_send_report``) funnel through (134H).

Mirrors ``tests/test_finalization_transaction_134e10.py``'s hermetic
fixture-building pattern: a synthetic gate-passing report, and a
synthetic ``promote_and_dispatch`` callback that performs no real I/O.
"""

from __future__ import annotations

from unittest import mock

import pytest

import pcae.core.phase_reports as pr
from pcae.cltr.migration import reconciliation
from pcae.core.finalization_transaction import run_finalization_transaction


def _fresh_arch_status(phase_id: str) -> dict:
    return {
        "schema_version": "1.0",
        "state_marker": "abc123",
        "repository_revision": "deadbeef",
        "completed": [],
        "completed_phase_ids": ["998A"],
        "completed_chapters": [],
        "in_progress": [],
        "current_phase_id": phase_id,
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


def _certified_report(phase_id: str):
    defaults = dict(
        phase_id=phase_id,
        phase_name="135O Integration Test Phase",
        status="completed",
        summary=f"Phase {phase_id}: 135O dual-derivation integration test.",
        files_changed=1,
        tests_run=1,
        commits=["a" * 40],
        pushed_status="pushed",
        origin_main_head_count=0,
        recommended_next_phase="999Y — Next Phase",
        explicit_no_go_confirmations=[f"No issue {i}." for i in range(11)],
        test_results={
            "fast_green": "1/1",
            "report_notification_tests": "passed",
            "bootstrap_session_reporting_tests": "passed",
        },
        governance_results={
            "pcae_health": "healthy",
            "pcae_check": "passed",
            "pcae_doctor_task_memory": "clean",
            "pcae_push_check": "clean",
            "telegram_runtime": "configured",
        },
        risks=["Some known risk."],
        follow_ups=["Some follow-up."],
    )
    with mock.patch.object(pr, "load_canonical_report", return_value=None):
        report = pr.make_phase_report(**defaults)
        report.architecture_status = _fresh_arch_status(phase_id)
        report.metadata["phase_id"] = phase_id
        report.metadata["source_revision"] = "deadbeef"
        report.metadata["phase_commits"] = report.commits
        pr._apply_canonical_and_trust(report, phase_id, report.phase_name, report.status)
        gate = pr.validate_finalization_gate(
            phase_id=phase_id,
            report=report,
            metadata=report.metadata,
            pushed_status=report.pushed_status,
            origin_main_head_count=report.origin_main_head_count,
            governance_results=report.governance_results,
            test_results=report.test_results,
            no_go_confirmations=report.explicit_no_go_confirmations,
            recommended_next_phase=report.recommended_next_phase,
            commit_attribution=report.commits[0],
        )
    return report, gate


def _successful_promote_and_dispatch(report, calls: list):
    def _callback() -> dict:
        calls.append(True)
        report.notification_result = {
            "dispatched": True, "sinks": ["noop"], "success": True, "error": None,
            "outcome": "sent", "reason": "", "kind": "complete",
        }
        return {"report": report, "blocked": False, "report_error": None}
    return _callback


@pytest.fixture()
def dual_derivation_enabled(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", "epoch-135o-integration")
    return tmp_path


def _run(phase_id: str, tmp_path):
    report, gate = _certified_report(phase_id)
    calls: list = []
    result = run_finalization_transaction(
        phase_id=report.phase_id,
        phase_name=report.phase_name,
        report=report,
        gate=gate,
        promote_and_dispatch=_successful_promote_and_dispatch(report, calls),
        transaction_root=tmp_path / "txns",
        receipt_root=tmp_path / "receipts",
        entry_point="phase_complete",
    )
    return result, calls


class TestDisabledByDefault:
    def test_no_migration_evidence_directory_created(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result, calls = _run("999X.1-135o-disabled", tmp_path)
        assert result.status == "completed"
        assert calls == [True]
        assert not (tmp_path / ".pcae" / "cltr-migration").exists()


class TestEnabledStage1:
    def test_migration_evidence_produced_for_phase_complete(self, dual_derivation_enabled):
        result, calls = _run("999X.1-135o-pc", dual_derivation_enabled)
        assert result.status == "completed"
        payload = reconciliation.reconcile("999X.1-135o-pc")
        assert payload["found"] is True
        assert payload["transitions"][0]["migration_progression_eligible"] is True

    def test_legacy_authority_still_completed_transaction(self, dual_derivation_enabled):
        result, calls = _run("999X.1-135o-legacy-authority", dual_derivation_enabled)
        assert result.status == "completed"
        assert result.receipt_logical_delivery_id is not None
        assert result.promotion_and_dispatch is not None

    def test_four_entry_points_share_the_same_coordinator_call_site(self, dual_derivation_enabled):
        import inspect

        from pcae.core.finalization_transaction import (
            _capture_stage1_migration_pre_transaction,
            _complete_stage1_migration,
        )

        source = inspect.getsource(_capture_stage1_migration_pre_transaction) + inspect.getsource(
            _complete_stage1_migration
        )
        # Both helpers are entry-point-agnostic (parametrized by
        # `entry_point`, called once from the one shared
        # `run_finalization_transaction` boundary) -- never branch on a
        # specific entry point string to pick different migration logic.
        assert "if entry_point ==" not in source

    def test_migration_failure_does_not_block_production_completion(self, dual_derivation_enabled, monkeypatch):
        import pcae.cltr.migration.coordinator as coordinator_mod

        def _boom(**kwargs):
            raise RuntimeError("simulated migration coordinator failure")

        # Patches the function *inside* the containment boundary
        # (`_capture_stage1_migration_pre_transaction`'s own try/except),
        # proving the containment itself works rather than bypassing it.
        monkeypatch.setattr(coordinator_mod, "run_stage1_best_effort_pre_transaction", _boom)
        result, calls = _run("999X.1-135o-migration-boom", dual_derivation_enabled)
        assert result.status == "completed"
        assert calls == [True]
