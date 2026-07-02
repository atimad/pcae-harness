"""Tests for Phase 106J.1 — Public Narrative Artifact Hygiene Repair.

Verifies that article-support/public-narrative scratch material was
removed from tracked docs, that `.pcae-local/` is established as the
ignored local workspace for future article artifacts, and that the
durable product/release documentation the removed brief drew facts from
remains intact and accurate. Non-executing, no network access.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HYGIENE_DOC_PATH = (
    REPO_ROOT / "docs" / "PHASE_106_PUBLIC_NARRATIVE_ARTIFACT_HYGIENE_REPAIR.md"
)
REMOVED_BRIEF_PATH = REPO_ROOT / "docs" / "PUBLIC_NARRATIVE_BRIEF_V0_1.md"
GITIGNORE_PATH = REPO_ROOT / ".gitignore"
README_PATH = REPO_ROOT / "README.md"
RELEASE_SCOPE_PATH = REPO_ROOT / "docs" / "RELEASE_SCOPE_V0_1.md"
RELEASE_HANDOFF_PATH = REPO_ROOT / "docs" / "RELEASE_HANDOFF_V0_1_RC1.md"
RELEASE_NOTES_PATH = REPO_ROOT / "docs" / "RELEASE_NOTES_V0_1_DRAFT.md"
GOLDEN_WORKFLOW_PATH = REPO_ROOT / "docs" / "V0_1_GOLDEN_WORKFLOW.md"

# Filenames that would indicate committed article-support scratch material.
# The hygiene doc itself intentionally mentions these words to explain
# policy, so it is excluded from this filename scan.
_ARTICLE_NAME_PATTERN = re.compile(
    r"(linkedin|article.?draft|talking.?points|narrative.?brief)", re.IGNORECASE
)


@pytest.fixture(scope="module")
def hygiene_text() -> str:
    return HYGIENE_DOC_PATH.read_text()


@pytest.fixture(scope="module")
def gitignore_text() -> str:
    return GITIGNORE_PATH.read_text()


@pytest.fixture(scope="module")
def readme_text() -> str:
    return README_PATH.read_text()


@pytest.fixture(scope="module")
def release_scope_text() -> str:
    return RELEASE_SCOPE_PATH.read_text()


@pytest.fixture(scope="module")
def release_handoff_text() -> str:
    return RELEASE_HANDOFF_PATH.read_text()


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return [line for line in result.stdout.splitlines() if line]


def test_hygiene_repair_doc_exists():
    assert HYGIENE_DOC_PATH.is_file()


def test_public_narrative_brief_is_absent():
    assert not REMOVED_BRIEF_PATH.exists()


def test_gitignore_contains_pcae_local(gitignore_text):
    assert ".pcae-local/" in gitignore_text


def test_pcae_local_is_actually_ignored():
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".pcae-local/anything"],
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_no_tracked_article_draft_files_except_hygiene_docs():
    tracked = _tracked_files()
    allowed_exceptions = {
        "docs/PHASE_106_PUBLIC_NARRATIVE_ARTIFACT_HYGIENE_REPAIR.md",
        "docs/PHASE_106_DOCUMENTATION_ALIGNMENT_PUBLIC_NARRATIVE_PREP.md",
        "tests/test_public_narrative_artifact_hygiene.py",
        "tests/test_documentation_alignment_public_narrative_v0_1.py",
        ".gitignore",
    }
    offenders = [
        path
        for path in tracked
        if _ARTICLE_NAME_PATTERN.search(Path(path).name)
        and path not in allowed_exceptions
    ]
    assert offenders == [], f"unexpected tracked article-support files: {offenders}"


def test_release_notes_still_exist():
    assert RELEASE_NOTES_PATH.is_file()


def test_release_handoff_still_exists():
    assert RELEASE_HANDOFF_PATH.is_file()


def test_release_scope_still_exists():
    assert RELEASE_SCOPE_PATH.is_file()


def test_readme_or_release_docs_reference_current_rc_state(readme_text, release_handoff_text):
    assert "v0.1.0-rc1" in readme_text
    assert "v0.1.0-rc1" in release_handoff_text


def test_docs_state_v0_1_non_executing_by_design(readme_text, release_scope_text):
    assert "non-executing" in readme_text.lower()
    assert "non-executing" in release_scope_text.lower()


def test_docs_state_v0_2_is_autonomy_target(readme_text, release_scope_text):
    combined = (readme_text + release_scope_text).lower()
    assert "v0.2" in combined
    assert "autonomy" in combined


def test_docs_do_not_claim_autonomous_execution_or_runtime_enforcement_exists(
    hygiene_text, readme_text, release_scope_text, release_handoff_text
):
    for text in (hygiene_text, readme_text, release_scope_text, release_handoff_text):
        lowered = text.lower()
        assert "runtime enforcement is now implemented" not in lowered
        assert "pcae now autonomously executes" not in lowered
        assert "telegram inbound is implemented" not in lowered


def test_hygiene_doc_recommends_next_phase(hygiene_text):
    assert "## Recommended Next Phase" in hygiene_text
    assert "106K" in hygiene_text


def test_hygiene_doc_documents_ignored_local_workspace(hygiene_text):
    assert ".pcae-local/" in hygiene_text


def test_hygiene_doc_states_what_was_removed(hygiene_text):
    assert "## What Was Removed" in hygiene_text
    assert "PUBLIC_NARRATIVE_BRIEF_V0_1.md" in hygiene_text
