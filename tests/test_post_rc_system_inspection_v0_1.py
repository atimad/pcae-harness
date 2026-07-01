"""Tests for Phase 106G — v0.1 Post-RC System Inspection / Lifecycle
Connectivity Audit.

Documentation-focused: verifies the post-RC inspection document exists,
covers all required review sections, and makes only the allowed safety
claims. No network/GitHub access; no tag creation is exercised here.
Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_106_POST_RC_SYSTEM_INSPECTION_LIFECYCLE_CONNECTIVITY_AUDIT.md"
)


@pytest.fixture(scope="module")
def audit_text() -> str:
    return AUDIT_PATH.read_text()


def test_post_rc_inspection_doc_exists():
    assert AUDIT_PATH.is_file()


def test_doc_references_v0_1_0_rc1(audit_text):
    assert "v0.1.0-rc1" in audit_text


def test_doc_includes_bootstrap_command_inventory(audit_text):
    assert "## Bootstrap Command Inventory" in audit_text
    assert "pcae session bootstrap" in audit_text


def test_doc_includes_bootstrap_session_reporting_review(audit_text):
    assert "## Bootstrap-Session Reporting Review" in audit_text
    assert "bootstrap_session_reporting_tests" in audit_text


def test_doc_includes_task_lifecycle_review(audit_text):
    assert "## Task Lifecycle Review" in audit_text


def test_doc_includes_phase_lifecycle_review(audit_text):
    assert "## Phase Lifecycle Review" in audit_text


def test_doc_includes_phase_report_trust_review(audit_text):
    assert "## Phase-Report Trust Review" in audit_text


def test_doc_includes_push_check_release_gate_review(audit_text):
    assert "## Push-Check / Release Gate Review" in audit_text


def test_doc_includes_telegram_outbound_review(audit_text):
    assert "## Telegram Outbound Notification Review" in audit_text
    assert "outbound" in audit_text.lower()


def test_doc_includes_lifecycle_connectivity_map(audit_text):
    assert "## Lifecycle Connectivity Map" in audit_text


def test_doc_includes_automation_coverage_map(audit_text):
    assert "## Automation Coverage Map" in audit_text


def test_doc_includes_manual_ritual_inventory(audit_text):
    assert "## Manual Ritual Inventory" in audit_text


def test_doc_includes_duplicate_overlapping_command_inventory(audit_text):
    assert "## Duplicate / Overlapping Command Inventory" in audit_text


def test_doc_states_v0_1_remains_non_executing(audit_text):
    lowered = audit_text.lower()
    assert "non-execution boundary" in lowered or "non-executing" in lowered


def test_doc_states_v0_2_is_deferred(audit_text):
    assert "Deferred Improvements for v0.2" in audit_text


def test_doc_does_not_claim_runtime_enforcement_or_autonomous_execution_exists(
    audit_text,
):
    lowered = audit_text.lower()
    forbidden_phrases = [
        "runtime enforcement is now implemented",
        "autonomous execution is available",
        "pcae now autonomously executes",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lowered
    assert "no runtime enforcement" in lowered or "non-executing" in lowered


def test_doc_recommends_next_phase(audit_text):
    assert "## Recommended Next Phase" in audit_text
    assert "106H" in audit_text


def test_doc_includes_release_impact_section(audit_text):
    assert "## Release Impact" in audit_text


def test_doc_includes_findings_section(audit_text):
    assert "## Findings" in audit_text


def test_doc_includes_recommended_fixes_before_final_release(audit_text):
    assert "Recommended Fixes Before Final v0.1.0" in audit_text
