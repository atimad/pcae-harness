"""Tests for Phase 106A — v0.1 Release Scope Freeze.

Documentation-focused: verifies docs/RELEASE_SCOPE_V0_1.md exists and makes
the required, and only the required, safety claims. Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

DOC_PATH = Path(__file__).resolve().parent.parent / "docs" / "RELEASE_SCOPE_V0_1.md"


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DOC_PATH.read_text()


def test_release_scope_doc_exists():
    assert DOC_PATH.is_file()


def test_names_pcae_v0_1(doc_text):
    assert "PCAE v0.1" in doc_text


def test_states_non_executing_by_design(doc_text):
    assert "non-executing by design" in doc_text.lower() or "Non-executing by design" in doc_text


def test_states_no_autonomous_execution(doc_text):
    assert "does not autonomously execute code" in doc_text.lower()


def test_lists_included_capabilities(doc_text):
    assert "## Included v0.1 Capabilities" in doc_text
    assert "Phase report trust validator" in doc_text
    assert "Report trust CLI" in doc_text
    assert "Hard-fail trust gates" in doc_text
    assert "Task-finish report/notification integration" in doc_text


def test_lists_excluded_capabilities(doc_text):
    assert "## Excluded v0.1 Capabilities" in doc_text
    assert "Autonomous execution" in doc_text
    assert "Runtime enforcement" in doc_text
    assert "Telegram inbound" in doc_text


def test_lists_supported_golden_workflow(doc_text):
    assert "## Supported Golden Workflow" in doc_text
    assert "pcae task finish --commit" in doc_text
    assert "pcae push check" in doc_text


def test_includes_validation_baseline(doc_text):
    assert "## Validation Baseline" in doc_text
    assert "4387/4390" in doc_text


def test_includes_three_pre_existing_fast_green_failures(doc_text):
    for name in (
        "Test94UPreflightArtifact",
        "Test94UPreflightArtifactCLI",
        "TestBackendShow",
    ):
        assert name in doc_text


def test_mentions_task_memory_clean_state(doc_text):
    assert "doctor task-memory" in doc_text
    assert "clean" in doc_text


def test_defines_release_blockers(doc_text):
    assert "## Release Blockers" in doc_text


def test_defines_v0_2_autonomy_boundary(doc_text):
    assert "## v0.2 Full-Autonomy Roadmap Boundary" in doc_text
    assert "out of scope for v0.1" in doc_text


def test_does_not_claim_runtime_enforcement_is_implemented(doc_text):
    # The doc must discuss runtime enforcement only as excluded/future, never
    # as an implemented v0.1 capability.
    assert "runtime enforcement implementation" in doc_text.lower()
    included_section = doc_text.split("## Included v0.1 Capabilities")[1].split(
        "## Excluded v0.1 Capabilities"
    )[0]
    assert "runtime enforcement" not in included_section.lower()


def test_does_not_claim_execution_is_available(doc_text):
    assert "Execution remains unavailable" in doc_text or "execution unavailable" in doc_text.lower() or "Autonomous execution" in doc_text
    included_section = doc_text.split("## Included v0.1 Capabilities")[1].split(
        "## Excluded v0.1 Capabilities"
    )[0]
    assert "autonomous execution" not in included_section.lower()


def test_does_not_claim_telegram_inbound_exists(doc_text):
    assert "does not provide telegram inbound control" in doc_text.lower()
    included_section = doc_text.split("## Included v0.1 Capabilities")[1].split(
        "## Excluded v0.1 Capabilities"
    )[0]
    assert "telegram inbound" not in included_section.lower()


def test_includes_recommended_next_phase(doc_text):
    assert "106B" in doc_text
