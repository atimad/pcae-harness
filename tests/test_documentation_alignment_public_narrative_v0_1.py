"""Tests for Phase 106J — v0.1 Documentation Alignment / Public Narrative
Prep. Documentation-focused: verifies the alignment document and public
narrative brief exist, are internally consistent, and make only the
allowed safety claims. No network/GitHub access; no LinkedIn article
content is exercised or expected here (deliberately not written in this
repository). Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ALIGNMENT_DOC_PATH = (
    REPO_ROOT / "docs" / "PHASE_106_DOCUMENTATION_ALIGNMENT_PUBLIC_NARRATIVE_PREP.md"
)
NARRATIVE_BRIEF_PATH = REPO_ROOT / "docs" / "PUBLIC_NARRATIVE_BRIEF_V0_1.md"
README_PATH = REPO_ROOT / "README.md"
GOLDEN_WORKFLOW_PATH = REPO_ROOT / "docs" / "V0_1_GOLDEN_WORKFLOW.md"
RELEASE_SCOPE_PATH = REPO_ROOT / "docs" / "RELEASE_SCOPE_V0_1.md"
RELEASE_HANDOFF_PATH = REPO_ROOT / "docs" / "RELEASE_HANDOFF_V0_1_RC1.md"


@pytest.fixture(scope="module")
def alignment_text() -> str:
    return ALIGNMENT_DOC_PATH.read_text()


@pytest.fixture(scope="module")
def brief_text() -> str:
    return NARRATIVE_BRIEF_PATH.read_text()


@pytest.fixture(scope="module")
def readme_text() -> str:
    return README_PATH.read_text()


@pytest.fixture(scope="module")
def golden_workflow_text() -> str:
    return GOLDEN_WORKFLOW_PATH.read_text()


@pytest.fixture(scope="module")
def release_scope_text() -> str:
    return RELEASE_SCOPE_PATH.read_text()


@pytest.fixture(scope="module")
def release_handoff_text() -> str:
    return RELEASE_HANDOFF_PATH.read_text()


def test_documentation_alignment_doc_exists():
    assert ALIGNMENT_DOC_PATH.is_file()


def test_public_narrative_brief_exists():
    assert NARRATIVE_BRIEF_PATH.is_file()


def test_brief_states_v0_1_non_executing_by_design(brief_text):
    lowered = brief_text.lower()
    assert "non-executing" in lowered


def test_brief_states_v0_2_is_autonomy_target(brief_text):
    assert "v0.2" in brief_text
    assert "autonomy" in brief_text.lower()


def test_brief_states_v0_1_0_rc1_was_tagged(brief_text):
    assert "v0.1.0-rc1" in brief_text
    assert "tagged" in brief_text.lower()


def test_brief_mentions_fast_green_4390(brief_text):
    assert "4390/4390" in brief_text


def test_brief_mentions_report_trust_hard_fail_gates(brief_text):
    lowered = brief_text.lower()
    assert "report-trust hard-fail gates" in lowered


def test_brief_mentions_golden_workflow(brief_text):
    assert "golden workflow" in brief_text.lower()


def test_brief_mentions_telegram_outbound_only(brief_text):
    lowered = brief_text.lower()
    assert "telegram" in lowered
    assert "outbound" in lowered


def test_brief_has_no_claims_avoid_list(brief_text):
    assert "No-Claims / Avoid List" in brief_text


def test_brief_does_not_claim_autonomous_execution(brief_text):
    lowered = brief_text.lower()
    assert "say pcae is autonomous" in lowered
    forbidden = [
        "pcae is autonomous.\n\n",
        "pcae autonomously executes code",
    ]
    for phrase in forbidden:
        assert phrase not in lowered


def test_brief_does_not_claim_runtime_enforcement_implemented(brief_text):
    lowered = brief_text.lower()
    assert "no runtime enforcement" in lowered
    assert "runtime enforcement is implemented" not in lowered


def test_brief_does_not_claim_shell_mediation_exists(brief_text):
    lowered = brief_text.lower()
    assert "no shell mediation" in lowered
    assert "safely controls shell commands" in lowered  # part of avoid list


def test_brief_does_not_claim_telegram_inbound_exists(brief_text):
    normalized = " ".join(brief_text.split()).lower()
    assert "no telegram inbound" in normalized
    assert "there is no inbound handler" in normalized


def test_readme_or_release_docs_reference_v0_1_0_rc1(readme_text, release_handoff_text):
    assert "v0.1.0-rc1" in readme_text
    assert "v0.1.0-rc1" in release_handoff_text


def test_golden_workflow_doc_states_preferred_completion_path(golden_workflow_text):
    assert "task finish --commit" in golden_workflow_text
    assert "phase complete" in golden_workflow_text


def test_release_docs_state_no_final_v0_1_0_tag_yet(release_scope_text, release_handoff_text):
    combined = release_scope_text + release_handoff_text
    lowered = combined.lower()
    assert "no final `v0.1.0` tag" in lowered or "does not exist" in lowered


def test_documentation_alignment_doc_recommends_next_phase(alignment_text):
    assert "## Recommended Next Phase" in alignment_text
    assert "106K" in alignment_text


def test_alignment_doc_does_not_claim_linkedin_article_written(alignment_text):
    normalized = " ".join(alignment_text.split()).lower()
    assert "no linkedin article written or committed" in normalized
