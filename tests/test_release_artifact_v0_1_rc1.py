"""Tests for Phase 106F — v0.1 RC Tag / Release Artifact Finalization.

Documentation-focused: verifies the RC handoff document and the release
artifact finalization document exist and make the required (and only the
required) safety/release claims. No network/GitHub access; no tag
creation is exercised here. Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HANDOFF_PATH = REPO_ROOT / "docs" / "RELEASE_HANDOFF_V0_1_RC1.md"
FINALIZATION_PATH = REPO_ROOT / "docs" / "PHASE_106_V0_1_RC_TAG_ARTIFACT_FINALIZATION.md"
NOTES_PATH = REPO_ROOT / "docs" / "RELEASE_NOTES_V0_1_DRAFT.md"
CHECKLIST_PATH = REPO_ROOT / "docs" / "RELEASE_CANDIDATE_V0_1_CHECKLIST.md"


@pytest.fixture(scope="module")
def handoff_text() -> str:
    return HANDOFF_PATH.read_text()


@pytest.fixture(scope="module")
def finalization_text() -> str:
    return FINALIZATION_PATH.read_text()


@pytest.fixture(scope="module")
def notes_text() -> str:
    return NOTES_PATH.read_text()


@pytest.fixture(scope="module")
def checklist_text() -> str:
    return CHECKLIST_PATH.read_text()


# --- RC handoff doc --------------------------------------------------------


def test_rc_handoff_doc_exists():
    assert HANDOFF_PATH.is_file()


def test_rc_handoff_names_v0_1_0_rc1(handoff_text):
    assert "v0.1.0-rc1" in handoff_text


def test_rc_handoff_states_non_executing_by_design(handoff_text):
    assert "non-executing by design" in handoff_text.lower()


def test_rc_handoff_states_telegram_outbound_only(handoff_text):
    assert "outbound-only" in handoff_text.lower()
    assert "Telegram" in handoff_text


def test_rc_handoff_states_v0_2_autonomy_target(handoff_text):
    assert "v0.2 Autonomy Boundary" in handoff_text
    assert "v0.2" in handoff_text


def test_rc_handoff_references_release_notes(handoff_text):
    assert "RELEASE_NOTES_V0_1_DRAFT.md" in handoff_text


def test_rc_handoff_references_golden_workflow(handoff_text):
    assert "V0_1_GOLDEN_WORKFLOW.md" in handoff_text


def test_rc_handoff_references_install_build_smoke_status(handoff_text):
    assert "Install/Build/Smoke Status" in handoff_text


def test_rc_handoff_references_fast_green_4390(handoff_text):
    assert "4390/4390" in handoff_text


def test_rc_handoff_does_not_claim_final_v0_1_0_tag(handoff_text):
    assert "No `v0.1.0` tag exists" in handoff_text or "no `v0.1.0` tag" in handoff_text.lower()


# --- release artifact finalization doc -------------------------------------


def test_release_artifact_finalization_doc_exists():
    assert FINALIZATION_PATH.is_file()


def test_finalization_doc_includes_pre_tag_gate_results(finalization_text):
    assert "Pre-Tag Gate Results" in finalization_text
    assert "All gates passed" in finalization_text


def test_finalization_doc_includes_tag_creation_result(finalization_text):
    assert "Tag Creation Result" in finalization_text


def test_finalization_doc_includes_tag_push_result(finalization_text):
    assert "Tag Push Result" in finalization_text


def test_finalization_doc_documents_governed_tag_command_gap(finalization_text):
    assert "Governed Tag Command Gap" in finalization_text
    assert "No governed PCAE tag or release command exists" in finalization_text


def test_finalization_doc_names_v0_1_0_rc1(finalization_text):
    assert "v0.1.0-rc1" in finalization_text


def test_finalization_doc_does_not_create_final_tag(finalization_text):
    lowered = finalization_text.lower()
    assert "no `v0.1.0` final tag created" in lowered or "no other tag was created" in lowered


# --- release notes / checklist consistency ---------------------------------


def test_release_notes_do_not_claim_autonomous_execution(notes_text):
    lowered = notes_text.lower()
    forbidden_phrases = [
        "pcae autonomously executes",
        "autonomous coding is production",
        "fully autonomous execution is available",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lowered


def test_release_notes_do_not_claim_runtime_enforcement_implemented(notes_text):
    lowered = notes_text.lower()
    assert "runtime enforcement is implemented" not in lowered
    assert "permission broker / shell gate remain evidence-only" in lowered


def test_release_checklist_references_v0_1_0_rc1(checklist_text):
    assert "v0.1.0-rc1" in checklist_text
