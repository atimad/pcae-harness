"""Tests for Phase 113X.5 — Architecture Status Canonicalization.

Repairs 113X (Cross-Agent Governance Verification) Finding 4. The
forensic review proved `_series_label()`'s hardcoded ``SERIES_MAP``
(e.g. ``"113": "Advisory Runtime (Architecture, Contract, Prototype)"``)
over-claimed completion: the label describes a series' *eventual, full*
scope the moment any one phase in that series completes, regardless of
which specific phases actually have. `_render_series_milestone_label()`
replaces it -- deriving each series' label from exactly the phases
whose own "## Phase X Complete" header exists in PROJECT_STATUS.md,
sorted deterministically, never inferring or extrapolating.

Non-executing, non-authorizing. No real network calls. No Advisory
Runtime, Runtime Snapshot, Runtime Context, Runtime Registry, Runtime
Inspect, Permission Broker, execution, authorization, plugin,
Telegram-inbound, REST, Web UI, or Dashboard changes (out of scope --
see PROJECT_STATUS.md Phase 113X.5). No changes to Canonical Phase
Identity, Finalization Gate, or Mobile Notification Guarantee.
"""

from __future__ import annotations

from pathlib import Path

from pcae.core.phase_reports import (
    build_architecture_status,
    make_phase_report,
    validate_phase_identity,
)


def _write_project_status(tmp_path: Path, body: str) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(body)


def _build(tmp_path: Path, monkeypatch) -> dict:
    monkeypatch.chdir(tmp_path)
    return build_architecture_status()


# ── Regression: reproduces Finding 4 exactly ────────────────────────────────


class TestFinding4Regression:
    """Only 113A complete must never claim Contract or Prototype are
    also done -- the exact defect the 113X forensic audit found."""

    def test_only_architecture_complete_does_not_overclaim(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

No automatic next repo phase implementation started. Recommended next
repo phase: 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert len(status["completed"]) == 1
        label = status["completed"][0]
        assert "Contract" not in label
        assert "Prototype" not in label
        assert status["completed_phase_ids"] == ["113A"]


# ── Objective 4: progressive partial completion ─────────────────────────────


class TestProgressivePartialCompletion:
    def test_only_architecture_complete(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["completed"] == ["Advisory Runtime Architecture"]
        assert status["completed_phase_ids"] == ["113A"]

    def test_architecture_and_contract_complete(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113B — Advisory Runtime Contract Freeze (completed).

## Phase 113B Complete

Phase 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert len(status["completed"]) == 1
        label = status["completed"][0]
        assert "Architecture" in label
        assert "Contract" in label
        assert "Prototype" not in label
        assert status["completed_phase_ids"] == ["113A", "113B"]

    def test_architecture_contract_and_prototype_complete(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113C — Advisory Runtime Prototype (Observation-Only) (completed).

## Phase 113C Complete

Phase 113C — Advisory Runtime Prototype (Observation-Only).

## Phase 113B Complete

Phase 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert len(status["completed"]) == 1
        label = status["completed"][0]
        assert "Architecture" in label
        assert "Contract" in label
        assert "Prototype" in label
        assert status["completed_phase_ids"] == ["113A", "113B", "113C"]


# ── Objective 4: mixed / incomplete phase series ────────────────────────────


class TestMixedAndIncompletePhaseSeries:
    def test_mixed_phase_series_each_gets_own_line(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 112B — Runtime Context Contract Freeze (completed).

## Phase 112B Complete

Phase 112B — Runtime Context Contract Freeze.

## Phase 112A Complete

Phase 112A — Runtime Context Architecture.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        assert len(status["completed"]) == 2
        assert set(status["completed_phase_ids"]) == {"112A", "112B", "113A"}

    def test_incomplete_series_only_shows_actually_completed(self, tmp_path, monkeypatch):
        """113B/113C are not yet complete -- must not appear anywhere,
        not even implied by the label."""
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        full_text = " ".join(status["completed"])
        assert "113B" not in str(status["completed_phase_ids"])
        assert "113C" not in str(status["completed_phase_ids"])
        assert status["completed_phase_ids"] == ["113A"]

    def test_all_series_with_genuine_evidence_included(self, tmp_path, monkeypatch):
        """Phase 134E.8: Architecture Status is no longer hard-scoped to
        the 110-113 series -- that restriction is exactly what made
        later completed tracks (125-134) permanently invisible even
        after the "planned" stale-132F regex was fixed. Every series
        with its own genuine "## Phase X Complete" header evidence is
        now included; there is no other gate on series membership."""
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.

## Phase 107C Complete

Phase 107C — Execution Readiness No-Go Gate Freeze.
""")
        status = _build(tmp_path, monkeypatch)
        assert set(status["completed_phase_ids"]) == {"113A", "107C"}

    def test_phase_with_no_header_not_swept_in(self, tmp_path, monkeypatch):
        """A phase merely *mentioned* in prose, with no "## Phase X
        Complete" header of its own, is never treated as completed --
        document existence/mention alone is not completion evidence."""
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

Recommended next phase: 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture. Mentions 999Z in passing.
""")
        status = _build(tmp_path, monkeypatch)
        assert status["completed_phase_ids"] == ["113A"]
        assert "999Z" not in status["completed_phase_ids"]


# ── Objective 7: deterministic, order-independent output ───────────────────


class TestDeterministicOutput:
    def test_repeated_calls_produce_identical_output(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113C — Advisory Runtime Prototype (Observation-Only) (completed).

## Phase 113C Complete

Phase 113C — Advisory Runtime Prototype (Observation-Only).

## Phase 113B Complete

Phase 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        monkeypatch.chdir(tmp_path)
        first = build_architecture_status()
        second = build_architecture_status()
        assert first == second

    def test_out_of_order_documentation_does_not_change_output(self, tmp_path, monkeypatch):
        """113X audit Finding 6: section order in the file must not
        change the derived result -- headers appearing in a scrambled
        (non-chronological, non-alphabetical) order must still produce
        the same sorted, deterministic label."""
        scrambled = """\
# Project Status

## Current Phase

Phase 113C — Advisory Runtime Prototype (Observation-Only) (completed).

## Phase 113B Complete

Phase 113B — Advisory Runtime Contract Freeze.

## Phase 113C Complete

Phase 113C — Advisory Runtime Prototype (Observation-Only).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
"""
        ordered = """\
# Project Status

## Current Phase

Phase 113C — Advisory Runtime Prototype (Observation-Only) (completed).

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.

## Phase 113B Complete

Phase 113B — Advisory Runtime Contract Freeze.

## Phase 113C Complete

Phase 113C — Advisory Runtime Prototype (Observation-Only).
"""
        _write_project_status(tmp_path, scrambled)
        scrambled_result = _build(tmp_path, monkeypatch)

        _write_project_status(tmp_path, ordered)
        ordered_result = _build(tmp_path, monkeypatch)

        assert scrambled_result["completed"] == ordered_result["completed"]
        assert scrambled_result["completed_phase_ids"] == ordered_result["completed_phase_ids"]


# ── Objective 6: consistency validation ─────────────────────────────────────


class TestConsistencyValidation:
    def test_recommendation_consistency_planned_not_already_completed(self, tmp_path, monkeypatch):
        _write_project_status(tmp_path, """\
# Project Status

## Current Phase

Phase 113A — Advisory Runtime Architecture (completed).

No automatic next repo phase implementation started. Recommended next
repo phase: 113B — Advisory Runtime Contract Freeze.

## Phase 113A Complete

Phase 113A — Advisory Runtime Architecture.
""")
        status = _build(tmp_path, monkeypatch)
        report = make_phase_report(
            phase_id="113A", phase_name="Test", status="completed", summary="Phase 113A: Test.",
            recommended_next_phase="113B — Advisory Runtime Contract Freeze",
        )
        report.architecture_status = status
        issues = validate_phase_identity(report, "113A", {})
        assert issues == []

    def test_impossible_combination_completed_and_planned_same_phase(self):
        """The exact Finding 4 scenario: a phase both completed and
        still recommended as the planned next phase."""
        report = make_phase_report(
            phase_id="113D", phase_name="Test", status="completed", summary="Phase 113D: Test.",
        )
        report.architecture_status = {
            "completed": ["Advisory Runtime: Architecture + Contract + Prototype"],
            "completed_phase_ids": ["113A", "113B", "113C"],
            "in_progress": [],
            "planned": ["113C — Advisory Runtime Prototype (Observation-Only)"],
            "current_runtime_state": "Observed",
            "current_maximum_capability": "observe",
            "execution_availability": "unavailable",
        }
        issues = validate_phase_identity(report, "113D", {})
        assert any("113C" in i and "completed" in i and "planned" in i for i in issues)

    def test_impossible_combination_in_progress_and_planned_same_phase(self):
        report = make_phase_report(
            phase_id="113D", phase_name="Test", status="completed", summary="Phase 113D: Test.",
        )
        report.architecture_status = {
            "completed": [],
            "completed_phase_ids": [],
            "in_progress": ["Advisory Runtime Verification (113D)"],
            "planned": ["113D — Advisory Runtime Verification"],
            "current_runtime_state": "Observed",
            "current_maximum_capability": "observe",
            "execution_availability": "unavailable",
        }
        issues = validate_phase_identity(report, "113D", {})
        assert any("113D" in i and "in-progress" in i and "planned" in i for i in issues)

    def test_runtime_state_consistency_observed_and_unavailable_is_fine(self):
        report = make_phase_report(
            phase_id="113D", phase_name="Test", status="completed", summary="Phase 113D: Test.",
        )
        report.architecture_status = {
            "completed": [], "completed_phase_ids": [], "in_progress": [], "planned": [],
            "current_runtime_state": "Observed",
            "current_maximum_capability": "observe",
            "execution_availability": "unavailable",
        }
        issues = validate_phase_identity(report, "113D", {})
        assert not any("execution_availability" in i for i in issues)

    def test_runtime_state_consistency_impossible_combination_rejected(self):
        """"Execution available while Runtime state is Observed" must
        be flagged -- Observed is this codebase's non-executing ceiling."""
        report = make_phase_report(
            phase_id="113D", phase_name="Test", status="completed", summary="Phase 113D: Test.",
        )
        report.architecture_status = {
            "completed": [], "completed_phase_ids": [], "in_progress": [], "planned": [],
            "current_runtime_state": "Observed",
            "current_maximum_capability": "observe",
            "execution_availability": "available",
        }
        issues = validate_phase_identity(report, "113D", {})
        assert any("execution_availability" in i for i in issues)

    def test_capability_consistency_metadata_mismatch_still_flagged(self):
        """Pre-existing check (unchanged): metadata's execution
        integration status vs Architecture Status's own fields."""
        report = make_phase_report(
            phase_id="113D", phase_name="Test", status="completed", summary="Phase 113D: Test.",
        )
        report.architecture_status = {
            "completed": [], "completed_phase_ids": [], "in_progress": [], "planned": [],
            "current_runtime_state": "Observed",
            "current_maximum_capability": "observe",
            "execution_availability": "unavailable",
        }
        md = {
            "execution_integration_status": {
                "current_maximum_runtime_state": "Executing",
                "current_maximum_plugin_capability": "enforce",
            },
        }
        issues = validate_phase_identity(report, "113D", md)
        assert len(issues) >= 2
