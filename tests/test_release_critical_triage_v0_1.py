"""Tests for Phase 106B — Release-Critical Warning / Fast-Green Triage.

Documentation-focused: verifies the triage document and the updated
release-scope document reflect the fast-green disposition accurately.
Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TRIAGE_DOC = ROOT / "docs" / "PHASE_106_RELEASE_CRITICAL_WARNING_FAST_GREEN_TRIAGE.md"
RELEASE_SCOPE_DOC = ROOT / "docs" / "RELEASE_SCOPE_V0_1.md"

_KNOWN_FAILURES = (
    "Test94UPreflightArtifact",
    "Test94UPreflightArtifactCLI",
    "TestBackendShow",
)


@pytest.fixture(scope="module")
def triage_text() -> str:
    return TRIAGE_DOC.read_text()


@pytest.fixture(scope="module")
def release_scope_text() -> str:
    return RELEASE_SCOPE_DOC.read_text()


def test_triage_doc_exists():
    assert TRIAGE_DOC.is_file()


def test_triage_doc_names_all_three_known_failures(triage_text):
    for name in _KNOWN_FAILURES:
        assert name in triage_text


def test_triage_doc_classifies_each_failure(triage_text):
    # Each failure must have an explicit status verdict, not be left as an
    # unexplained "pre-existing failure."
    assert triage_text.count("**Status:**") >= 2
    assert "Fixed" in triage_text


def test_triage_doc_documents_root_cause(triage_text):
    assert "Root cause" in triage_text
    assert "VALID_PREFLIGHT_STATUSES" in triage_text
    assert "backend-invocations" in triage_text


def test_triage_doc_confirms_task_memory_clean(triage_text):
    assert "Task-Memory Warning Status" in triage_text
    assert "clean" in triage_text.lower()


def test_triage_doc_states_release_disposition(triage_text):
    assert "## Release Disposition" in triage_text


def test_triage_doc_recommends_next_phase(triage_text):
    assert "106C" in triage_text


def test_release_scope_doc_includes_triage_disposition(release_scope_text):
    assert "106B" in release_scope_text
    assert "PHASE_106_RELEASE_CRITICAL_WARNING_FAST_GREEN_TRIAGE" in release_scope_text


def test_release_scope_doc_does_not_hide_original_failures(release_scope_text):
    # The doc must still name the three original failures somewhere, even
    # though they are now resolved -- history should not be erased.
    for name in _KNOWN_FAILURES:
        assert name in release_scope_text


def test_release_scope_doc_states_fully_green(release_scope_text):
    assert "4390/4390" in release_scope_text


def test_release_scope_doc_states_task_memory_status(release_scope_text):
    assert "doctor task-memory" in release_scope_text
    assert "clean" in release_scope_text


def test_no_runtime_enforcement_or_execution_claim_added(triage_text, release_scope_text):
    for text in (triage_text, release_scope_text):
        assert "runtime enforcement is implemented" not in text.lower()
        assert "execution is available" not in text.lower()
