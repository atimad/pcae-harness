"""Tests for Phase 106J — v0.1 Documentation Alignment / Public Narrative
Prep. Documentation-focused: verifies the alignment document exists and
is internally consistent, and that the durable release docs it aligned
remain accurate. No network/GitHub access; no LinkedIn article content
is exercised or expected here (deliberately not written in this
repository).

Phase 106J.1 note: this file originally also tested
`docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md`'s content. That file was removed
in Phase 106J.1 as a documentation-hygiene repair (article-support
source material does not belong in tracked product docs — see
`docs/PHASE_106_PUBLIC_NARRATIVE_ARTIFACT_HYGIENE_REPAIR.md` and
`tests/test_public_narrative_artifact_hygiene.py`, which now covers its
absence). The brief-content tests were removed accordingly; this file
now covers only the alignment document and the durable docs it touched.
Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ALIGNMENT_DOC_PATH = (
    REPO_ROOT / "docs" / "PHASE_106_DOCUMENTATION_ALIGNMENT_PUBLIC_NARRATIVE_PREP.md"
)
README_PATH = REPO_ROOT / "README.md"
GOLDEN_WORKFLOW_PATH = REPO_ROOT / "docs" / "V0_1_GOLDEN_WORKFLOW.md"
RELEASE_SCOPE_PATH = REPO_ROOT / "docs" / "RELEASE_SCOPE_V0_1.md"
RELEASE_HANDOFF_PATH = REPO_ROOT / "docs" / "RELEASE_HANDOFF_V0_1_RC1.md"


@pytest.fixture(scope="module")
def alignment_text() -> str:
    return ALIGNMENT_DOC_PATH.read_text()


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


def test_alignment_doc_documents_106j1_amendment(alignment_text):
    assert "106J.1" in alignment_text


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
