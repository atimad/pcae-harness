"""Tests for Phase 106E — v0.1 Release Candidate.

Documentation-focused: verifies the release candidate checklist, release
notes draft, and readiness review exist and make the required (and only
the required) safety/release claims. Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKLIST_PATH = REPO_ROOT / "docs" / "RELEASE_CANDIDATE_V0_1_CHECKLIST.md"
NOTES_PATH = REPO_ROOT / "docs" / "RELEASE_NOTES_V0_1_DRAFT.md"
READINESS_PATH = REPO_ROOT / "docs" / "PHASE_106_V0_1_RELEASE_CANDIDATE_READINESS.md"


@pytest.fixture(scope="module")
def checklist_text() -> str:
    return CHECKLIST_PATH.read_text()


@pytest.fixture(scope="module")
def notes_text() -> str:
    return NOTES_PATH.read_text()


@pytest.fixture(scope="module")
def readiness_text() -> str:
    return READINESS_PATH.read_text()


# --- existence ---------------------------------------------------------


def test_release_candidate_checklist_exists():
    assert CHECKLIST_PATH.is_file()


def test_release_notes_draft_exists():
    assert NOTES_PATH.is_file()


def test_release_readiness_review_exists():
    assert READINESS_PATH.is_file()


# --- checklist content ---------------------------------------------------


def test_checklist_states_non_executing_by_design(checklist_text):
    assert "non-executing by design" in checklist_text.lower()


def test_checklist_states_v0_2_is_autonomy_target(checklist_text):
    assert "v0.2" in checklist_text
    assert "autonomy" in checklist_text.lower()
    assert "v0.2 Autonomy Boundary" in checklist_text


def test_checklist_includes_golden_workflow(checklist_text):
    assert "Golden Workflow" in checklist_text
    assert "V0_1_GOLDEN_WORKFLOW.md" in checklist_text


def test_checklist_includes_installation_build_smoke_status(checklist_text):
    assert "Installation / Packaging Status" in checklist_text
    assert "Editable install" in checklist_text
    assert "python -m build" in checklist_text


def test_checklist_includes_fast_green_4390(checklist_text):
    assert "4390/4390" in checklist_text
    assert "fully green" in checklist_text.lower()


def test_checklist_includes_task_memory_clean(checklist_text):
    assert "doctor task-memory" in checklist_text
    assert "clean" in checklist_text.lower()


def test_checklist_includes_push_check_clean(checklist_text):
    assert "push check" in checklist_text.lower()


def test_checklist_includes_telegram_outbound_only(checklist_text):
    assert "outbound" in checklist_text.lower()
    assert "Telegram" in checklist_text


def test_checklist_includes_go_no_go_status(checklist_text):
    assert "Final Go/No-Go Status" in checklist_text
    assert "GO" in checklist_text


def test_checklist_reflects_tag_state(checklist_text):
    # As of Phase 106F, the tag has been created and pushed; the checklist
    # is updated to reflect that rather than asserting it is not created.
    assert "v0.1.0-rc1" in checklist_text
    assert (
        "Tag created and pushed in Phase 106F" in checklist_text
        or "Tag is not created in this phase" in checklist_text
    )


def test_checklist_names_recommended_tag(checklist_text):
    assert "v0.1.0-rc1" in checklist_text


# --- release notes content ------------------------------------------------


def test_release_notes_state_candidate_draft(notes_text):
    assert "candidate draft" in notes_text.lower()


def test_release_notes_do_not_claim_autonomous_execution(notes_text):
    lowered = notes_text.lower()
    forbidden_phrases = [
        "pcae autonomously executes",
        "autonomous coding is production",
        "fully autonomous execution is available",
        "autonomous execution of agent-authored code or commands.\n\n##",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lowered
    assert "autonomous execution of agent-authored code or commands" in lowered
    assert "## what is not included" in lowered


def test_release_notes_do_not_claim_runtime_enforcement_implemented(notes_text):
    lowered = notes_text.lower()
    assert "runtime enforcement is implemented" not in lowered
    assert "permission broker / shell gate remain evidence-only" in lowered


def test_release_notes_do_not_claim_telegram_inbound(notes_text):
    lowered = notes_text.lower()
    assert "telegram is outbound-only" in lowered
    assert "there is no inbound handler" in lowered
    assert "telegram inbound / polling / remote command reception" in lowered


def test_release_notes_state_non_executing(notes_text):
    assert "non-executing by design" in notes_text.lower()


def test_release_notes_state_v0_2_autonomy_preview(notes_text):
    assert "v0.2 Autonomy Preview" in notes_text


def test_release_notes_include_installation_summary(notes_text):
    assert "Installation Summary" in notes_text


def test_release_notes_name_recommended_tag(notes_text):
    assert "v0.1.0-rc1" in notes_text


# --- readiness review content ---------------------------------------------


def test_readiness_review_includes_go_no_go_decision(readiness_text):
    assert "Go/No-Go Decision" in readiness_text
    assert "Ready to tag v0.1.0-rc1 after operator approval" in readiness_text


def test_readiness_review_recommends_tag_only_after_operator_approval(readiness_text):
    assert "after operator approval" in readiness_text.lower()
    assert "No tag is created in 106E" in readiness_text


def test_readiness_review_names_recommended_rc_tag(readiness_text):
    assert "v0.1.0-rc1" in readiness_text


def test_readiness_review_states_non_goals(readiness_text):
    assert "## Non-Goals" in readiness_text
    assert "No runtime enforcement" in readiness_text
    assert "No autonomous execution" in readiness_text


def test_readiness_review_includes_release_evidence(readiness_text):
    assert "Release Evidence From 106A Through 106D" in readiness_text
    for phase in ("106A", "106B", "106C", "106D"):
        assert phase in readiness_text


def test_readiness_review_includes_validation_baseline(readiness_text):
    assert "Current Validation Baseline" in readiness_text
    assert "4390/4390" in readiness_text


def test_readiness_review_recommends_next_phase_106f(readiness_text):
    assert "106F" in readiness_text
