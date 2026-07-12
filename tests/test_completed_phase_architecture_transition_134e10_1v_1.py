"""Phase 134E.10.1V.1 completed-phase Architecture Status transition repair."""

from __future__ import annotations

from copy import deepcopy

import pytest

from pcae.core.architecture_status import parse_phase_id, validate_architecture_status
from pcae.core.finalization_transaction import run_finalization_transaction
from pcae.core.repository_transition_integration import parse_phase_id_from_text
from pcae.core.phase_reports import (
    build_architecture_status,
    detect_cross_phase_commit_contamination,
    make_phase_report,
    validate_derived_correctness,
)


PROJECT_STATUS = """# Project Status

## Current Phase

Phase 134E.10.1V.1 — Completed-Phase Architecture Status Transition Repair.

Recommended next phase: 134F — Whole-Lifecycle Independent Verification.

## Phase 134E.10.1V Complete

Phase 134E.10.1V — Final Lifecycle Integration Transaction-Span Repair Independent Verification (completed).
"""


def _write_state(tmp_path, monkeypatch, text=PROJECT_STATUS):
    (tmp_path / "PROJECT_STATUS.md").write_text(text)
    monkeypatch.chdir(tmp_path)


def _projected(tmp_path, monkeypatch):
    _write_state(tmp_path, monkeypatch)
    return build_architecture_status(
        completing_phase_id="134E.10.1V.1",
        completing_phase_name="Completed-Phase Architecture Status Transition Repair",
        report_status="completed",
        recommended_next_phase="134F — Whole-Lifecycle Independent Verification",
    )


def _report(status):
    report = make_phase_report(
        phase_id="134E.10.1V.1",
        phase_name="Completed-Phase Architecture Status Transition Repair",
        status="completed",
        summary="narrow repair",
        recommended_next_phase="134F — Whole-Lifecycle Independent Verification",
    )
    report.architecture_status = status
    report.report_completeness = "complete"
    return report


def test_projected_post_completion_state_is_deterministic(tmp_path, monkeypatch):
    first = _projected(tmp_path, monkeypatch)
    second = build_architecture_status(
        completing_phase_id="134E.10.1V.1",
        completing_phase_name="Completed-Phase Architecture Status Transition Repair",
        report_status="completed",
        recommended_next_phase="134F — Whole-Lifecycle Independent Verification",
    )
    assert first == second
    assert "134E.10.1V.1" in first["completed_phase_ids"]
    assert first["current_phase_id"] == ""
    assert not first["in_progress"]
    assert first["planned_phase_ids"] == ["134F"]
    assert first["source_provenance"]["lifecycle_projection"] == "completed:134E.10.1V.1"


def test_active_phase_remains_in_progress_without_completion_projection(tmp_path, monkeypatch):
    _write_state(tmp_path, monkeypatch)
    status = build_architecture_status()
    assert status["current_phase_id"] == "134E.10.1V.1"
    assert status["in_progress"]


def test_long_completed_current_title_is_not_in_progress(tmp_path, monkeypatch):
    _write_state(
        tmp_path,
        monkeypatch,
        PROJECT_STATUS.replace(
            "Transition Repair.",
            "Transition Repair With A Deliberately Very Long Title That Exceeds The Old Arbitrary Boundary (completed).",
        ),
    )
    status = build_architecture_status()
    assert status["in_progress"] == []


@pytest.mark.parametrize(
    "mutate,fragment",
    [
        (lambda s: s.update(current_phase_id="134E.10.1V.1"), "current/in-progress"),
        (lambda s: s["in_progress"].append("Repair (134E.10.1V.1)"), "current/in-progress"),
        (lambda s: s["in_progress"].append("Repair (completed) (134E.10.1V.1)"), "completed state"),
    ],
)
def test_completed_report_rejects_current_or_in_progress(tmp_path, monkeypatch, mutate, fragment):
    status = _projected(tmp_path, monkeypatch)
    mutate(status)
    issues = validate_derived_correctness(_report(status))
    assert any(fragment in issue for issue in issues)


def test_architecture_validator_rejects_in_progress_planned_overlap():
    status = {
        "schema_version": "1.0",
        "completed_phase_ids": [],
        "planned_phase_ids": ["134F"],
        "current_phase_id": "134F",
        "in_progress": ["Whole Lifecycle (134F)"],
        "completed_chapters": [],
    }
    assert any("in-progress and planned" in issue for issue in validate_architecture_status(status))


def test_architecture_validator_rejects_completed_in_progress_overlap():
    status = {
        "schema_version": "1.0",
        "completed_phase_ids": ["134E.10.1V.1"],
        "planned_phase_ids": [],
        "current_phase_id": "",
        "in_progress": ["Repair (134E.10.1V.1)"],
        "completed_chapters": [],
    }
    assert any("Completed and In Progress" in issue for issue in validate_architecture_status(status))


def test_projected_completed_phase_cannot_be_omitted(tmp_path, monkeypatch):
    status = _projected(tmp_path, monkeypatch)
    status["completed_phase_ids"].remove("134E.10.1V.1")
    issues = validate_derived_correctness(_report(status))
    assert any("absent" in issue and "completed_phase_ids" in issue for issue in issues)


def test_transaction_contradiction_never_invokes_callback_or_writes_checkpoint(tmp_path, monkeypatch):
    status = _projected(tmp_path, monkeypatch)
    status["current_phase_id"] = "134E.10.1V.1"
    status["in_progress"] = ["Repair (134E.10.1V.1)"]
    called = []
    transaction_root = tmp_path / "transactions"
    result = run_finalization_transaction(
        phase_id="134E.10.1V.1",
        phase_name="Completed-Phase Architecture Status Transition Repair",
        report=_report(status),
        gate={"finalizable": True},
        promote_and_dispatch=lambda: called.append(True) or {},
        transaction_root=transaction_root,
        receipt_root=tmp_path / "receipts",
    )
    assert result.status == "pre_promotion_certification_failed"
    assert called == []
    assert not transaction_root.exists()
    assert not (tmp_path / "receipts").exists()


@pytest.mark.parametrize(
    "phase_id",
    ["134E.10", "134E.10V", "134E.10.1", "134E.10.1V", "134E.10.1V.1", "134F"],
)
def test_corrective_and_verification_identities_parse_without_truncation(phase_id):
    parsed = parse_phase_id(phase_id)
    assert parsed is not None


def test_projection_does_not_mutate_pre_transition_snapshot(tmp_path, monkeypatch):
    _write_state(tmp_path, monkeypatch)
    before = build_architecture_status()
    frozen = deepcopy(before)
    build_architecture_status(
        completing_phase_id="134E.10.1V.1",
        completing_phase_name="Repair",
        report_status="completed",
        recommended_next_phase="134F — Verification",
    )
    assert before == frozen
    assert "132F" not in before["planned_phase_ids"]


def test_commit_subject_parser_preserves_triply_dotted_identity(monkeypatch):
    class Result:
        returncode = 0
        stdout = "Phase 134E.10.1V.1: repair transition\n"

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Result())
    assert detect_cross_phase_commit_contamination(["5d02165c"], "134E.10.1V.1") == []
    warnings = detect_cross_phase_commit_contamination(["5d02165c"], "134E.10.1V")
    assert warnings and "134E.10.1V.1" in warnings[0]


def test_transition_adapter_preserves_triply_dotted_active_task_identity():
    text = "Phase 134E.10.1V.1: Completed-Phase Architecture Status Transition Repair"
    assert parse_phase_id_from_text(text) == "134E.10.1V.1"
