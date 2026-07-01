"""Tests for Phase 106H — v0.1 RC Audit Findings Repair.

Reproduces and verifies the fix for the trust-gate asymmetry between
`pcae task finish --commit` and `pcae phase complete` found by Phase
106G's audit: `task finish --commit`'s dispatch decision previously used
only the 105A/105B trust schema plus push-state fields, while `phase
complete`'s gate (since Phase 105D) additionally required the OLD
(95M.1) schema's full completeness check. Both now share
`apply_old_schema_gate()` (Phase 106H) and enforce the same combined
gate. Non-executing, non-authorizing — no real backend/network calls.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract
from pcae.core.phase_reports import (
    make_phase_report,
    _apply_canonical_and_trust,
    validate_finalization_gate,
)
from pcae.core.phase_report_trust import (
    adapt_report_for_trust_check,
    apply_old_schema_gate,
    apply_push_state_gate,
    compute_final_trust,
    validate_phase_report_trust,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
REPAIR_DOC_PATH = REPO_ROOT / "docs" / "PHASE_106_RC_AUDIT_FINDINGS_REPAIR.md"
GOLDEN_WORKFLOW_PATH = REPO_ROOT / "docs" / "V0_1_GOLDEN_WORKFLOW.md"


@pytest.fixture(scope="module")
def repair_doc_text() -> str:
    return REPAIR_DOC_PATH.read_text()


@pytest.fixture(scope="module")
def golden_workflow_text() -> str:
    return GOLDEN_WORKFLOW_PATH.read_text()


def _synthetic_report(**overrides):
    common = dict(
        phase_id="999Z",
        phase_name="test_phase",
        status="completed",
        summary="test summary",
        files_changed=0,
        tests_run=5,
        test_results={
            "report_notification_tests": "1/1 (passed)",
            "bootstrap_session_reporting_tests": "present",
            "fast_green": "1/1",
        },
        governance_results={
            "pcae_health": "healthy",
            "pcae_check": "passed",
            "pcae_doctor_task_memory": "clean",
            "pcae_push_check": "clean",
            "telegram_runtime": "loaded",
        },
        commits=["abc12345"],
        pushed_status="pushed",
        origin_main_head_count=0,
        explicit_no_go_confirmations=["no-go text present"],
        recommended_next_phase="1000A",
    )
    common.update(overrides)
    report = make_phase_report(**common)
    _apply_canonical_and_trust(report, common["phase_id"], common["phase_name"], common["status"])
    return report, common


def _gate_for(report, common):
    return validate_finalization_gate(
        phase_id=common["phase_id"],
        report=report,
        metadata={},
        pushed_status=common["pushed_status"],
        origin_main_head_count=common["origin_main_head_count"],
        governance_results=common["governance_results"],
        test_results=common["test_results"],
        no_go_confirmations=common["explicit_no_go_confirmations"],
        recommended_next_phase=common["recommended_next_phase"],
        commit_attribution="phase_owned",
    )


class TestAsymmetryReproduction:
    """Reproduces the exact 106G-documented asymmetry, then confirms the
    repair closes it — using the real functions both commands call."""

    def test_files_changed_zero_gate_is_not_finalizable(self):
        report, common = _synthetic_report(files_changed=0)
        gate = _gate_for(report, common)
        assert gate["finalizable"] is False
        assert any("files_changed" in b for b in gate["blockers"])

    def test_task_finish_style_dispatch_now_matches_phase_complete(self):
        """Pre-106H, this trust computation (mirroring
        `_finalize_task_report_and_notify`) would report `complete=True`
        for `files_changed=0`, diverging from `phase complete`. Post-106H,
        applying `apply_old_schema_gate` closes the gap."""
        report, common = _synthetic_report(files_changed=0)
        gate = _gate_for(report, common)

        trial_trust = validate_phase_report_trust(
            adapt_report_for_trust_check(report.to_dict())
        )
        apply_push_state_gate(trial_trust, report.missing_trust_fields)
        # Before repair: dispatch would be allowed here (asymmetry).
        assert trial_trust.complete is True

        apply_old_schema_gate(trial_trust, gate)
        # After repair: the shared helper closes the gap.
        assert trial_trust.complete is False
        assert trial_trust.repair_required is True

    def test_phase_complete_style_dispatch_unchanged(self):
        report, common = _synthetic_report(files_changed=0)
        gate = _gate_for(report, common)
        trust_result = compute_final_trust(
            report.to_dict(), old_schema_missing_fields=report.missing_trust_fields
        )
        apply_old_schema_gate(trust_result, gate)
        assert trust_result.complete is False

    def test_both_paths_agree_on_incomplete_report(self):
        report, common = _synthetic_report(files_changed=0)
        gate = _gate_for(report, common)

        task_trust = validate_phase_report_trust(
            adapt_report_for_trust_check(report.to_dict())
        )
        apply_push_state_gate(task_trust, report.missing_trust_fields)
        apply_old_schema_gate(task_trust, gate)

        phase_trust = compute_final_trust(
            report.to_dict(), old_schema_missing_fields=report.missing_trust_fields
        )
        apply_old_schema_gate(phase_trust, gate)

        assert task_trust.complete == phase_trust.complete == False

    def test_both_paths_agree_on_complete_report(self):
        no_go_11 = [
            "No runtime enforcement.", "No autonomous execution.",
            "No real backend invocation.", "No adapter execution.",
            "No shell mediation.", "No rollback execution.",
            "No Telegram inbound.", "No Telegram polling.",
            "No remote shell.", "No automatic apply.",
            "No execution enablement flag.",
        ]
        report, common = _synthetic_report(
            files_changed=5, explicit_no_go_confirmations=no_go_11
        )
        gate = _gate_for(report, common)
        assert gate["finalizable"] is True

        task_trust = validate_phase_report_trust(
            adapt_report_for_trust_check(report.to_dict())
        )
        apply_push_state_gate(task_trust, report.missing_trust_fields)
        apply_old_schema_gate(task_trust, gate)

        phase_trust = compute_final_trust(
            report.to_dict(), old_schema_missing_fields=report.missing_trust_fields
        )
        apply_old_schema_gate(phase_trust, gate)

        assert task_trust.complete == phase_trust.complete == True

    def test_apply_old_schema_gate_is_noop_when_gate_is_none(self):
        report, common = _synthetic_report(files_changed=5)
        trust = validate_phase_report_trust(adapt_report_for_trust_check(report.to_dict()))
        before = trust.complete
        apply_old_schema_gate(trust, None)
        assert trust.complete == before

    def test_apply_old_schema_gate_records_blockers_in_missing_fields(self):
        report, common = _synthetic_report(files_changed=0)
        gate = _gate_for(report, common)
        trust = validate_phase_report_trust(adapt_report_for_trust_check(report.to_dict()))
        apply_old_schema_gate(trust, gate)
        assert any(f.startswith("old_schema_gate:") for f in trust.missing_fields)


class TestCliIntegration:
    """Direct CLI-level tests using `pcae task finish --commit` and
    `pcae phase complete`, proving the repair end-to-end."""

    def _init_repo(self, tmp_path: Path) -> HarnessPath:
        root = HarnessPath(tmp_path)
        init_harness(root)
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
        return root

    def _new_task(self, root: HarnessPath, **overrides) -> None:
        kwargs: dict[str, Any] = {
            "title": "Smoke task",
            "goal": "smoke",
            "mode": "implementation",
            "allowed_files": [".pcae/**", "tasks/active/**", "tasks/done/**"],
            "allowed_zones": ["config", "tasks"],
        }
        kwargs.update(overrides)
        create_task_contract(root, **kwargs)

    def _write_incomplete_metadata(self, tmp_path: Path) -> None:
        meta = {
            "phase_id": "106H-T",
            "phase_name": "Repair Test",
            "status": "completed",
            "summary": "Test phase for 106H repair.",
            "files_changed_count": 0,
            "tests_added_or_updated": "5 tests added",
            "governance_results": [
                {"name": "pcae_health", "status": "healthy"},
                {"name": "pcae_check", "status": "passed"},
                {"name": "pcae_doctor_task_memory", "status": "clean"},
                {"name": "pcae_push_check", "status": "clean"},
                {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
            ],
            "validation_results": [
                {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
                {"name": "bootstrap_session_reporting_tests", "result": "present", "status": ""},
                {"name": "fast_green", "result": "1/1", "status": "passed"},
            ],
            "no_go_confirmation": (
                "No runtime enforcement. No execution. No subprocess. No shell. "
                "No network. No Telegram inbound. No apply. No commit authorization. "
                "No push authorization. No rollback. No adapter execution."
            ),
            "commit_attribution": "phase_owned",
            "pushed_status": "pushed",
            "origin_main_head_count": 0,
            "recommended_next_phase": "106H-T2 — Next Phase",
        }
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))

    def test_task_finish_incomplete_report_path_skips_dispatch(self, tmp_path, monkeypatch, capsys):
        from pcae.cli import main

        root = self._init_repo(tmp_path)
        self._new_task(root)
        self._write_incomplete_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        exit_code = main(["task", "finish", "--staged-file-aware", "--commit", "Repair test finish"])
        output = capsys.readouterr().out

        assert exit_code == 0  # task finish itself never hard-fails
        assert "Report notification: skipped_incomplete" in output
        assert "old_schema_gate" in output

    def test_phase_complete_incomplete_report_path_hard_fails(self, tmp_path, monkeypatch, capsys):
        from pcae.cli import main

        root = self._init_repo(tmp_path)
        self._new_task(root)
        self._write_incomplete_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

        exit_code = main(["phase", "complete", "--summary", "Phase 106H-T repair test"])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "refused" in output.lower()

    def test_phase_complete_cannot_bypass_final_trust_requirements(self, tmp_path, monkeypatch, capsys):
        """Even without --allow-partial-report, an incomplete report never
        dispatches — confirming the hard-fail gate cannot be silently
        bypassed."""
        from pcae.cli import main

        root = self._init_repo(tmp_path)
        self._new_task(root)
        self._write_incomplete_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        exit_code = main(["phase", "complete", "--summary", "Phase 106H-T repair test"])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "Notification dispatch: skipped" in output


class TestRepairDoc:
    def test_repair_doc_exists(self):
        assert REPAIR_DOC_PATH.is_file()

    def test_doc_describes_106g_trust_gate_asymmetry(self, repair_doc_text):
        assert "Exact Asymmetry Observed" in repair_doc_text
        assert "106G" in repair_doc_text

    def test_doc_states_preferred_v0_1_completion_path(self, repair_doc_text):
        normalized = " ".join(repair_doc_text.split())
        assert "preferred v0.1 golden-workflow completion command" in normalized

    def test_doc_states_trust_behavior_after_repair(self, repair_doc_text):
        assert "Task Finish Behavior After Repair" in repair_doc_text
        assert "Phase Complete Behavior After Repair" in repair_doc_text

    def test_doc_states_telegram_outbound_only(self, repair_doc_text):
        assert "outbound-only" in repair_doc_text.lower()

    def test_doc_states_partial_reports_not_final_trusted(self, repair_doc_text):
        lowered = repair_doc_text.lower()
        assert "partial/incomplete reports remain suppressed" in lowered


class TestGoldenWorkflowAlignment:
    def test_golden_workflow_states_preferred_completion_path(self, golden_workflow_text):
        assert "task finish --commit" in golden_workflow_text

    def test_no_docs_claim_autonomous_execution_or_runtime_enforcement(
        self, repair_doc_text, golden_workflow_text
    ):
        for text in (repair_doc_text, golden_workflow_text):
            lowered = text.lower()
            assert "runtime enforcement is now implemented" not in lowered
            assert "autonomous execution is available" not in lowered
