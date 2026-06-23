"""Tests for lifecycle state machine model (Phase 80A)."""
from __future__ import annotations

from pcae.lifecycle import LIFECYCLE_STATES, detect_lifecycle_state, get_next_recommendation


def test_state_table_contains_expected_states():
    expected = {
        "idle", "backend_capture_attempted", "mutation_detected",
        "quarantined", "adoption_review_ready", "adoption_reviewed",
        "adoption_approved", "adoption_execution_ready", "staged_for_commit",
        "commit_approved", "committed_for_push", "hook_bypass_reconciled",
        "push_approved", "pushed", "final_verified", "closed", "blocked",
    }
    assert expected <= set(LIFECYCLE_STATES.keys())


def test_each_state_has_required_fields():
    for sid, state in LIFECYCLE_STATES.items():
        assert state.state_id == sid
        assert isinstance(state.label, str) and state.label
        assert isinstance(state.description, str) and state.description
        assert isinstance(state.approval_required, bool)
        assert isinstance(state.execution_boundary, bool)
        assert isinstance(state.allowed_next_actions, tuple)


def test_approval_and_execution_states_distinct():
    approval_states = {s for s, st in LIFECYCLE_STATES.items() if st.approval_required}
    execution_states = {s for s, st in LIFECYCLE_STATES.items() if st.execution_boundary}
    assert not (approval_states & execution_states), "Approval and execution must be separate"


def test_closed_state_has_no_dangerous_action():
    closed = LIFECYCLE_STATES["closed"]
    dangerous = {"commit_execution", "push_execution", "adoption_execution", "backend_capture"}
    assert not (set(closed.allowed_next_actions) & dangerous)


def test_blocked_state_recommends_no_execution():
    blocked = LIFECYCLE_STATES["blocked"]
    assert blocked.allowed_next_actions == ("resolve_blockers",)
    assert not blocked.execution_boundary
    assert not blocked.approval_required


def test_idle_state_detection_with_empty_dir(tmp_path):
    state_id, details = detect_lifecycle_state(tmp_path)
    assert state_id == "idle"


def test_next_recommendation_for_idle():
    rec = get_next_recommendation("idle")
    assert rec["recommended_next_action"] == "start_backend_capture"
    assert rec["required_approval"] is False


def test_next_recommendation_for_closed():
    rec = get_next_recommendation("closed")
    assert rec["recommended_next_action"] == "start_new_lifecycle"
    assert rec["required_approval"] is False


def test_next_recommendation_for_blocked():
    rec = get_next_recommendation("blocked")
    assert rec["recommended_next_action"] == "resolve_blockers"
