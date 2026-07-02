"""Tests for Phase 106I — v0.1 RC End-to-End Verification / Full Phase
Check. Documentation-focused: verifies the end-to-end verification
document exists, covers all required review sections, and makes only the
allowed safety claims. No network/GitHub access; no tag creation
exercised here. Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFICATION_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_106_RC_END_TO_END_VERIFICATION_FULL_PHASE_CHECK.md"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return VERIFICATION_PATH.read_text()


def test_end_to_end_verification_doc_exists():
    assert VERIFICATION_PATH.is_file()


def test_doc_references_v0_1_0_rc1(doc_text):
    assert "v0.1.0-rc1" in doc_text


def test_doc_includes_release_tag_state_verification(doc_text):
    assert "## Release/Tag State Verification" in doc_text


def test_doc_includes_bootstrap_session_reporting_verification(doc_text):
    assert "## Bootstrap / Session Reporting Verification" in doc_text
    assert "bootstrap_session_reporting_tests" in doc_text


def test_doc_includes_task_lifecycle_verification(doc_text):
    assert "## Task Lifecycle Verification" in doc_text


def test_doc_includes_phase_lifecycle_verification(doc_text):
    assert "## Phase Lifecycle Verification" in doc_text


def test_doc_includes_trust_gate_symmetry_verification(doc_text):
    assert "## Trust-Gate Symmetry Verification" in doc_text


def test_doc_includes_phase_report_trust_verification(doc_text):
    assert "## Phase-Report Trust Verification" in doc_text


def test_doc_includes_push_check_release_gate_review(doc_text):
    assert "## Push-Check / Release Gate Review" in doc_text


def test_doc_includes_telegram_outbound_verification(doc_text):
    assert "## Telegram Outbound Notification Verification" in doc_text
    assert "outbound" in doc_text.lower()


def test_doc_includes_golden_workflow_verification(doc_text):
    assert "## Golden Workflow Verification" in doc_text


def test_doc_includes_packaging_release_artifact_verification(doc_text):
    assert "## Packaging / Release Artifact Verification" in doc_text


def test_doc_states_v0_1_remains_non_executing(doc_text):
    lowered = doc_text.lower()
    assert "non-executing" in lowered or "non-execution" in lowered


def test_doc_states_no_final_v0_1_0_tag_exists(doc_text):
    lowered = doc_text.lower()
    assert "final `v0.1.0` tag exists | no" in lowered or "no final `v0.1.0` tag" in lowered


def test_doc_states_v0_2_remains_deferred(doc_text):
    assert "Deferred Improvements for v0.2" in doc_text


def test_doc_does_not_claim_runtime_enforcement_or_autonomous_execution_exists(
    doc_text,
):
    lowered = doc_text.lower()
    forbidden_phrases = [
        "runtime enforcement is now implemented",
        "autonomous execution is available",
        "pcae now autonomously executes",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lowered


def test_doc_recommends_next_phase(doc_text):
    assert "## Recommended Next Phase" in doc_text
    assert "106J" in doc_text


def test_doc_includes_remaining_findings_section(doc_text):
    assert "## Remaining Findings" in doc_text


def test_doc_includes_release_impact_section(doc_text):
    assert "## Release Impact" in doc_text


def test_doc_includes_documentation_alignment_observations(doc_text):
    assert "## Documentation Alignment Observations" in doc_text
