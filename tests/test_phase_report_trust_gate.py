"""Tests for Phase 105A — Phase Report Trust Gate Implementation. Non-executing."""
from __future__ import annotations
import pytest, json, pathlib, inspect
from pcae.core.phase_report_trust import (
    validate_phase_report_trust, select_active_phase_report,
    PhaseReportTrustResult, PhaseReportTrustIssue,
    REQUIRED_REPORT_FIELDS, REQUIRED_GOVERNANCE_FIELDS, REQUIRED_TEST_FIELDS,
    DISALLOWED_PLACEHOLDER_VALUES,
    COMPLETENESS_COMPLETE, COMPLETENESS_PARTIAL, COMPLETENESS_INVALID,
)


def _complete_report(**overrides) -> dict:
    """Build a minimal complete report for testing."""
    r = {
        "phase_id": "105A",
        "status": "completed",
        "files_changed": 7,
        "tests_run": 25,
        "commits": ["abc123def456"],
        "pushed": "pushed",
        "summary": "Test phase 105A",
        "recommended_next_phase": "105B — Next Phase",
        "governance_results": {
            "pcae_health": "healthy",
            "pcae_check": "passed",
            "pcae_doctor_task_memory": "warnings",
            "pcae_push_check": "clean",
            "telegram_runtime": "loaded, configured, enabled",
        },
        "test_results": {
            "report_notification_tests": "219/219 (passed)",
            "bootstrap_session_reporting_tests": "present_in_canonical_metadata",
            "fast_green": "4387/4390 (passed_with_pre_existing)",
        },
    }
    r.update(overrides)
    return r


class TestRequiredFieldDetection:
    def test_complete_passes(self):
        v = validate_phase_report_trust(_complete_report())
        assert v.complete is True
        assert v.status == COMPLETENESS_COMPLETE
        assert v.repair_required is False
        assert v.can_be_active_latest is True

    def test_missing_phase_id_fails(self):
        v = validate_phase_report_trust(_complete_report(phase_id=""))
        assert v.complete is False
        assert any("phase_id" in f for f in v.missing_fields)

    def test_missing_files_changed_fails(self):
        v = validate_phase_report_trust(_complete_report(files_changed=None))
        assert v.complete is False

    def test_missing_tests_run_fails(self):
        v = validate_phase_report_trust(_complete_report(tests_run=None))
        assert v.complete is False

    def test_missing_summary_fails(self):
        v = validate_phase_report_trust(_complete_report(summary=""))
        assert v.complete is False

    def test_missing_recommended_next_phase_fails(self):
        v = validate_phase_report_trust(_complete_report(recommended_next_phase=""))
        assert v.complete is False


class TestGovernanceFieldDetection:
    def test_missing_pcae_health_fails(self):
        r = _complete_report(); r["governance_results"] = dict(r["governance_results"]); del r["governance_results"]["pcae_health"]
        v = validate_phase_report_trust(r)
        assert v.complete is False

    def test_missing_pcae_check_fails(self):
        r = _complete_report(); r["governance_results"] = dict(r["governance_results"]); del r["governance_results"]["pcae_check"]
        assert not validate_phase_report_trust(r).complete

    def test_missing_telegram_runtime_fails(self):
        r = _complete_report(); r["governance_results"] = dict(r["governance_results"]); del r["governance_results"]["telegram_runtime"]
        assert not validate_phase_report_trust(r).complete

    def test_governance_results_missing_entirely(self):
        r = _complete_report(); del r["governance_results"]
        assert not validate_phase_report_trust(r).complete


class TestTestFieldDetection:
    def test_missing_report_notification_fails(self):
        r = _complete_report(); r["test_results"] = dict(r["test_results"]); del r["test_results"]["report_notification_tests"]
        assert not validate_phase_report_trust(r).complete

    def test_missing_bootstrap_fails(self):
        r = _complete_report(); r["test_results"] = dict(r["test_results"]); del r["test_results"]["bootstrap_session_reporting_tests"]
        assert not validate_phase_report_trust(r).complete

    def test_missing_fast_green_fails(self):
        r = _complete_report(); r["test_results"] = dict(r["test_results"]); del r["test_results"]["fast_green"]
        assert not validate_phase_report_trust(r).complete

    def test_test_results_missing_entirely(self):
        r = _complete_report(); del r["test_results"]
        assert not validate_phase_report_trust(r).complete


class TestPlaceholderDetection:
    def test_tbd_fast_green_fails(self):
        r = _complete_report(); r["test_results"] = dict(r["test_results"]); r["test_results"]["fast_green"] = "TBD"
        v = validate_phase_report_trust(r)
        assert not v.complete
        assert any("test_results.fast_green" in f for f in v.placeholder_fields)

    def test_pending_fast_green_fails(self):
        r = _complete_report(); r["test_results"] = dict(r["test_results"]); r["test_results"]["fast_green"] = "pending"
        v = validate_phase_report_trust(r)
        assert not v.complete

    def test_commits_tbd_fails(self):
        r = _complete_report(commits="TBD")
        v = validate_phase_report_trust(r)
        assert not v.complete

    def test_commits_empty_list_fails(self):
        r = _complete_report(commits=[])
        v = validate_phase_report_trust(r)
        assert not v.complete

    def test_files_changed_not_captured(self):
        r = _complete_report(files_changed="not captured")
        v = validate_phase_report_trust(r)
        assert not v.complete

    def test_null_phase_id(self):
        v = validate_phase_report_trust(_complete_report(phase_id=None))
        assert not v.complete


class TestCompletenessClassification:
    def test_complete_status(self):
        v = validate_phase_report_trust(_complete_report())
        assert v.status == COMPLETENESS_COMPLETE

    def test_partial_status(self):
        r = _complete_report(); r["test_results"] = dict(r["test_results"]); r["test_results"]["fast_green"] = "TBD"
        v = validate_phase_report_trust(r)
        assert v.status == COMPLETENESS_PARTIAL

    def test_invalid_status(self):
        v = validate_phase_report_trust({})
        assert v.status == COMPLETENESS_INVALID

    def test_repair_required_missing(self):
        v = validate_phase_report_trust({})
        assert v.repair_required is True

    def test_can_be_active_latest_complete(self):
        v = validate_phase_report_trust(_complete_report())
        assert v.can_be_active_latest is True

    def test_can_be_active_latest_partial(self):
        r = _complete_report(); r["test_results"] = dict(r["test_results"]); r["test_results"]["fast_green"] = "TBD"
        v = validate_phase_report_trust(r)
        assert v.can_be_active_latest is False


class TestActiveLatestSelection:
    def test_complete_over_partial(self):
        partial = _complete_report(phase_id="105A")
        partial["test_results"] = dict(partial["test_results"]); partial["test_results"]["fast_green"] = "TBD"
        complete = _complete_report(phase_id="105A")
        selected, v = select_active_phase_report([partial, complete], "105A")
        assert selected is not None
        assert v.complete is True

    def test_phase_id_filter(self):
        selected, v = select_active_phase_report([_complete_report(phase_id="105A")], "105B")
        assert selected is None

    def test_partial_only_returns_repair_guidance(self):
        partial = _complete_report(phase_id="105A")
        partial["test_results"] = dict(partial["test_results"]); partial["test_results"]["fast_green"] = "TBD"
        selected, v = select_active_phase_report([partial], "105A")
        assert v is not None
        assert v.can_be_active_latest is False
        assert v.repair_required is True

    def test_empty_returns_none(self):
        selected, v = select_active_phase_report([], "105A")
        assert selected is None


class TestNoExecGuards:
    def test_validator_no_subprocess(self):
        src = inspect.getsource(validate_phase_report_trust)
        assert "subprocess" not in src
        assert "os.system" not in src

    def test_module_no_network(self):
        text = pathlib.Path("src/pcae/core/phase_report_trust.py").read_text()
        assert "requests." not in text
        assert "urllib" not in text

    def test_result_to_dict_non_executing(self):
        r = PhaseReportTrustResult(complete=True, status=COMPLETENESS_COMPLETE)
        d = r.to_dict()
        assert d["complete"] is True
        assert d["status"] == COMPLETENESS_COMPLETE


class TestModuleConstants:
    def test_required_report_fields(self): assert len(REQUIRED_REPORT_FIELDS) == 8
    def test_required_governance_fields(self): assert len(REQUIRED_GOVERNANCE_FIELDS) == 5
    def test_required_test_fields(self): assert len(REQUIRED_TEST_FIELDS) == 3
    def test_disallowed_placeholders(self): assert "TBD" in DISALLOWED_PLACEHOLDER_VALUES
