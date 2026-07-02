"""Tests for Phase 106M — Repository Contribution Safety / Branch Protection Readiness.

Documentation-focused: verifies the contribution-safety doc, contributor
workflow doc, CONTRIBUTING.md, PR template, and CODEOWNERS make the
required (and only the required) claims. No live GitHub network access
is exercised here; branch protection itself was applied once,
out-of-band, via `gh api`. Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SAFETY_DOC_PATH = REPO_ROOT / "docs" / "PHASE_106_REPOSITORY_CONTRIBUTION_SAFETY_BRANCH_PROTECTION.md"
CONTRIBUTING_PATH = REPO_ROOT / "CONTRIBUTING.md"
WORKFLOW_DOC_PATH = REPO_ROOT / "docs" / "CONTRIBUTOR_WORKFLOW.md"
PR_TEMPLATE_PATH = REPO_ROOT / ".github" / "pull_request_template.md"
CODEOWNERS_PATH = REPO_ROOT / ".github" / "CODEOWNERS"


@pytest.fixture(scope="module")
def safety_text() -> str:
    return SAFETY_DOC_PATH.read_text()


@pytest.fixture(scope="module")
def contributing_text() -> str:
    return CONTRIBUTING_PATH.read_text()


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return WORKFLOW_DOC_PATH.read_text()


@pytest.fixture(scope="module")
def pr_template_text() -> str:
    return PR_TEMPLATE_PATH.read_text()


# --- existence -------------------------------------------------------------


def test_contribution_safety_doc_exists():
    assert SAFETY_DOC_PATH.is_file()


def test_contributing_md_exists():
    assert CONTRIBUTING_PATH.is_file()


def test_contributor_workflow_doc_exists():
    assert WORKFLOW_DOC_PATH.is_file()


def test_pr_template_exists():
    assert PR_TEMPLATE_PATH.is_file()


# --- required content across contributor-facing docs ------------------------


@pytest.mark.parametrize("fixture_name", ["safety_text", "contributing_text", "workflow_text"])
def test_docs_state_no_direct_pushes_to_main(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    assert "no direct push" in text


@pytest.mark.parametrize("fixture_name", ["safety_text", "contributing_text", "workflow_text"])
def test_docs_state_pr_first_workflow(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    assert "pull request" in text


@pytest.mark.parametrize("fixture_name", ["safety_text", "contributing_text", "workflow_text"])
def test_docs_mention_branch_protection(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    assert "branch protection" in text


@pytest.mark.parametrize("fixture_name", ["safety_text", "workflow_text"])
def test_docs_mention_force_push_and_deletion_protection(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    assert "force push" in text
    assert "deletion" in text


def test_workflow_doc_mentions_pcae_checks_before_pr(workflow_text):
    lowered = workflow_text.lower()
    for command in ["pcae health", "pcae check", "pcae doctor task-memory", "pcae push check"]:
        assert command in lowered


def test_docs_mention_v0_1_non_executing_boundary(safety_text, workflow_text):
    assert "non-executing" in safety_text.lower()
    assert "non-executing" in workflow_text.lower()


def test_docs_mention_autonomy_boundary_requires_maintainer_approval(workflow_text):
    lowered = workflow_text.lower()
    assert "explicit maintainer approval" in lowered


def test_docs_mention_pcae_local_remains_ignored(safety_text, workflow_text):
    assert ".pcae-local/" in safety_text
    assert ".pcae-local/" in workflow_text
    assert "ignored" in workflow_text.lower()


def test_docs_mention_github_release_exists_for_v0_1_0_rc1(safety_text, workflow_text):
    assert "v0.1.0-rc1" in safety_text
    assert "v0.1.0-rc1" in workflow_text
    assert "github release" in safety_text.lower()
    assert "github release" in workflow_text.lower()


def test_docs_mention_no_pypi_or_github_packages_publication(safety_text, workflow_text):
    for text in (safety_text, workflow_text):
        lowered = text.lower()
        assert "pypi" in lowered
        assert "github packages" in lowered


@pytest.mark.parametrize("fixture_name", ["safety_text", "workflow_text", "contributing_text"])
def test_docs_do_not_claim_execution_capabilities_exist(fixture_name, request):
    text = request.getfixturevalue(fixture_name).lower()
    forbidden_phrases = [
        "runtime enforcement is implemented",
        "pcae autonomously executes",
        "autonomous execution is available",
        "telegram inbound is available",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text


# --- CODEOWNERS (optional) --------------------------------------------------


def test_codeowners_references_owner_if_present():
    if not CODEOWNERS_PATH.is_file():
        pytest.skip("CODEOWNERS not created this phase")
    text = CODEOWNERS_PATH.read_text()
    assert "@atimad" in text


# --- PR template content -----------------------------------------------------


def test_pr_template_asks_required_questions(pr_template_text):
    lowered = pr_template_text.lower()
    required_phrases = [
        "task/phase",
        "scope",
        "files changed",
        "not changed",
        "tests were run",
        "pcae check",
        "pcae push check",
        "execution/autonomy",
        "non-executing",
        "documentation",
    ]
    for phrase in required_phrases:
        assert phrase in lowered


# --- recommended next phase --------------------------------------------------


def test_contribution_safety_doc_recommends_next_phase(safety_text):
    assert "107A" in safety_text
