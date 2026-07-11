"""Phase 134E.8.1 incident regressions: logical delivery and coherence."""

from __future__ import annotations

import json

import pytest

from pcae.core.phase_reports import (
    COMPLETENESS_COMPLETE,
    compute_finalization_snapshot_id,
    compute_report_digest,
    make_phase_report,
    phase_already_notified,
    read_notification_dispatch_marker,
    validate_internal_report_coherence,
    write_notification_dispatch_marker,
)


def _report(**overrides):
    values = {
        "phase_id": "134E.8",
        "phase_name": "Architecture Status Generation Repair",
        "status": "completed",
        "summary": "Implemented the Architecture Status repair. Recommended next phase: 134E.8V.",
        "files_changed": 10,
        "tests_run": 51,
        "test_results": {"architecture_status_generation_repair_134e8": "51 passed"},
        "governance_results": {"pcae_check": "passed"},
        "commits": ["160f91bf"],
        "pushed_status": "pushed",
        "explicit_no_go_confirmations": ["No 134E.8V work began."],
        "recommended_next_phase": "134E.8V - Independent Verification",
        "created_at": "2026-07-11T14:37:46+00:00",
    }
    values.update(overrides)
    report = make_phase_report(**values)
    report.report_completeness = COMPLETENESS_COMPLETE
    return report


def test_first_terminal_delivery_marks_phase_level_identity(tmp_path):
    marker = tmp_path / "marker.json"
    write_notification_dispatch_marker("134E.8", "160f91bf", marker)
    assert phase_already_notified("134E.8", "160f91bf", marker)


def test_bookkeeping_commit_cannot_create_second_ordinary_delivery(tmp_path):
    marker = tmp_path / "marker.json"
    write_notification_dispatch_marker("134E.8", "160f91bf", marker)
    assert phase_already_notified("134E.8", "de506304", marker)


def test_other_phase_remains_distinct(tmp_path):
    marker = tmp_path / "marker.json"
    write_notification_dispatch_marker("134E.8", "160f91bf", marker)
    assert not phase_already_notified("134E.8V", "de506304", marker)


def test_explicit_correction_marker_is_not_ordinary_completion(tmp_path):
    marker = tmp_path / "marker.json"
    write_notification_dispatch_marker(
        "134E.8", "fix12345", marker, delivery_purpose="correction"
    )
    assert not phase_already_notified("134E.8", "fix12345", marker)


def test_marker_binds_payload_and_snapshot(tmp_path):
    marker = tmp_path / "marker.json"
    report = _report()
    digest = compute_report_digest(report)
    snapshot = compute_finalization_snapshot_id(report)
    write_notification_dispatch_marker(
        report.phase_id, report.commits[0], marker,
        report_digest=digest, finalization_snapshot_id=snapshot,
    )
    stored = read_notification_dispatch_marker(marker)
    assert stored["report_digest"] == digest
    assert stored["finalization_snapshot_id"] == snapshot
    assert stored["delivery_purpose"] == "ordinary_completion"


def test_snapshot_ignores_creation_time_only():
    assert compute_finalization_snapshot_id(_report()) == compute_finalization_snapshot_id(
        _report(created_at="later")
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("summary", "different summary"),
        ("test_results", {"architecture_status_generation_repair_134e8": "50 passed"}),
        ("commits", ["different"]),
        ("recommended_next_phase", "134E.9"),
        ("architecture_status", {"current_phase_id": "134E.7V"}),
    ],
)
def test_snapshot_changes_when_evidence_changes(field, value):
    assert compute_finalization_snapshot_id(_report()) != compute_finalization_snapshot_id(
        _report(**{field: value})
    )


def test_no_go_denial_of_completed_phase_is_rejected():
    report = _report(explicit_no_go_confirmations=["No 134E.8 work began."])
    assert any("denies" in issue for issue in validate_internal_report_coherence(report))


def test_completed_phase_recommending_itself_is_rejected():
    report = _report(recommended_next_phase="134E.8 - Architecture Status Generation Repair")
    assert any("recommends itself" in issue for issue in validate_internal_report_coherence(report))


def test_prior_phase_test_evidence_is_rejected():
    report = _report(test_results={"delivery_receipt_134e7v_adversarial_tests": "48 passed"})
    assert any("other phase identities" in issue for issue in validate_internal_report_coherence(report))


def test_incident_mixed_metadata_is_rejected():
    report = _report(
        test_results={
            "delivery_receipt_134e7v_adversarial_tests": "48 passed",
            "delivery_receipt_134e7_focused_tests": "110 passed",
        },
        explicit_no_go_confirmations=[
            "No Architecture Status repair occurred. No 134E.8 work began."
        ],
        recommended_next_phase="Phase 134E.8 - Architecture Status Generation Repair",
    )
    issues = validate_internal_report_coherence(report)
    assert len(issues) == 4


def test_report_digest_binds_exact_rendered_payload():
    assert compute_report_digest(_report()) != compute_report_digest(
        _report(summary="changed rendered payload")
    )


def test_architecture_inspection_source_has_no_report_write_calls():
    source = __import__("inspect").getsource(
        __import__("pcae.commands.architecture_status", fromlist=["run_architecture_status_inspect"])
    )
    assert "write_phase_report" not in source
    assert "finalize_phase_report" not in source
    assert "dispatch(" not in source


def test_track_134_delivery_subsystems_remain_inactive():
    from pathlib import Path

    for path in (Path("src/pcae/core/delivery_pipeline.py"), Path("src/pcae/core/delivery_receipt.py")):
        text = path.read_text()
        assert "commands.phase" not in text
        assert "commands.task" not in text
