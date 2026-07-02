"""Tests for Phase 107A — v0.2 Full Autonomy Roadmap / Execution Capability Gap Analysis.

Documentation-focused: verifies the v0.2 roadmap and gap-analysis docs
exist and make the required (and only the required) claims. No live
GitHub/network access is exercised here. Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP_PATH = REPO_ROOT / "docs" / "V0_2_AUTONOMY_ROADMAP.md"
GAP_ANALYSIS_PATH = REPO_ROOT / "docs" / "PHASE_107_V0_2_EXECUTION_CAPABILITY_GAP_ANALYSIS.md"


@pytest.fixture(scope="module")
def roadmap_text() -> str:
    return ROADMAP_PATH.read_text()


@pytest.fixture(scope="module")
def gap_analysis_text() -> str:
    return GAP_ANALYSIS_PATH.read_text()


# --- existence ---------------------------------------------------------------


def test_roadmap_doc_exists():
    assert ROADMAP_PATH.is_file()


def test_gap_analysis_doc_exists():
    assert GAP_ANALYSIS_PATH.is_file()


# --- autonomy level / execution-availability claims ---------------------------


def test_roadmap_states_v0_1_is_level_0(roadmap_text):
    assert "Level 0" in roadmap_text
    lowered = roadmap_text.lower()
    assert "v0.1 is level 0" in lowered


def test_roadmap_states_v0_2_autonomy_target(roadmap_text):
    assert "v0.2" in roadmap_text
    assert "Level 3" in roadmap_text


def test_roadmap_states_execution_remains_unavailable_now(roadmap_text):
    lowered = roadmap_text.lower()
    assert "execution remains unavailable" in lowered


# --- already-present v0.1 capabilities ----------------------------------------


def test_roadmap_lists_already_present_v0_1_capabilities(roadmap_text):
    lowered = roadmap_text.lower()
    for phrase in [
        "governed task/phase lifecycle",
        "report-trust",
        "golden workflow",
        "fast_green",
    ]:
        assert phrase in lowered


def test_roadmap_lists_github_release_and_branch_protection(roadmap_text):
    lowered = roadmap_text.lower()
    assert "github release" in lowered
    assert "branch protection" in lowered


# --- missing autonomy capabilities ---------------------------------------------


@pytest.mark.parametrize(
    "phrase",
    [
        "permission broker",
        "shell/subprocess",
        "backend invocation",
        "adapter invocation",
        "human approval enforcement",
        "durable audit persistence",
        "rollback",
        "emergency stop",
    ],
)
def test_roadmap_lists_missing_autonomy_capability(roadmap_text, phrase):
    assert phrase in roadmap_text.lower()


def test_roadmap_includes_hard_no_go_conditions(roadmap_text):
    assert "Hard No-Go Conditions" in roadmap_text


def test_roadmap_mentions_pr_compatible_workflow_impact(roadmap_text):
    lowered = roadmap_text.lower()
    assert "pr-compatible" in lowered or "pr compatible" in lowered


# --- no overclaiming -----------------------------------------------------------


@pytest.mark.parametrize("fixture_name", ["roadmap_text", "gap_analysis_text"])
def test_docs_do_not_claim_execution_capabilities_exist(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    forbidden_phrases = [
        "runtime enforcement is implemented",
        "pcae autonomously executes",
        "autonomous execution is available",
        "telegram inbound is available",
        "telegram inbound exists",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text


# --- gap analysis specifics ----------------------------------------------------


def test_gap_analysis_references_v0_1_0_rc1(gap_analysis_text):
    assert "v0.1.0-rc1" in gap_analysis_text


def test_gap_analysis_references_github_release_prerelease_state(gap_analysis_text):
    lowered = gap_analysis_text.lower()
    assert "prerelease" in lowered


def test_gap_analysis_references_branch_protection_state(gap_analysis_text):
    assert "branch protection" in gap_analysis_text.lower()


def test_gap_analysis_references_fast_green_4390(gap_analysis_text):
    assert "4390/4390" in gap_analysis_text


def test_gap_analysis_recommends_next_phase(gap_analysis_text):
    assert "107B" in gap_analysis_text
