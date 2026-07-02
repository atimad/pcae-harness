"""Tests for Phase 106K — v0.1 Effectiveness Evaluation Framework /
External Article Source Packet.

Verifies the committed effectiveness evaluation framework exists and is
internally consistent, and that article-support hygiene from Phase
106J.1 remains intact (no committed narrative brief, no committed
article/source-packet material, `.pcae-local/` remains ignored). Does
not exercise the untracked local article packet's content (it is
deliberately outside the tracked tree) — only confirms it stays
untracked if present on disk. Non-executing, no network access.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK_PATH = REPO_ROOT / "docs" / "V0_1_EFFECTIVENESS_EVALUATION_FRAMEWORK.md"
REMOVED_BRIEF_PATH = REPO_ROOT / "docs" / "PUBLIC_NARRATIVE_BRIEF_V0_1.md"
GITIGNORE_PATH = REPO_ROOT / ".gitignore"
LOCAL_ARTICLE_PACKET_PATH = (
    REPO_ROOT / ".pcae-local" / "article-drafts" / "v0.1-linkedin-source-packet.md"
)


@pytest.fixture(scope="module")
def framework_text() -> str:
    return FRAMEWORK_PATH.read_text()


@pytest.fixture(scope="module")
def gitignore_text() -> str:
    return GITIGNORE_PATH.read_text()


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return [line for line in result.stdout.splitlines() if line]


def test_effectiveness_framework_exists():
    assert FRAMEWORK_PATH.is_file()


def test_framework_states_v0_1_is_non_executing(framework_text):
    lowered = framework_text.lower()
    assert "non-executing" in lowered


def test_framework_compares_ai_coding_without_and_with_pcae(framework_text):
    assert "## Baseline: AI Coding Without PCAE" in framework_text
    assert "## Treatment: AI Coding With PCAE v0.1" in framework_text


def test_framework_includes_trusted_completion_per_supervision(framework_text):
    lowered = framework_text.lower()
    assert "trusted completion per unit of human supervision" in lowered


def test_framework_includes_scoring_rubric(framework_text):
    assert "## Scoring Rubric" in framework_text
    for dimension in (
        "Task correctness",
        "Test/regression safety",
        "Scope control",
        "Report/handoff quality",
        "Commit/release hygiene",
        "Human supervision cost",
        "Time efficiency",
        "Documentation quality",
    ):
        assert dimension in framework_text


def test_framework_includes_sample_evaluation_tasks(framework_text):
    assert "## Sample Evaluation Tasks" in framework_text


def test_framework_includes_controlled_comparison_method(framework_text):
    assert "## Controlled Comparison Method" in framework_text


def test_framework_includes_longitudinal_metrics(framework_text):
    assert "## Longitudinal Real-Project Metrics" in framework_text


def test_framework_includes_expected_advantages(framework_text):
    assert "## Expected Advantages" in framework_text


def test_framework_includes_expected_overhead_disadvantages(framework_text):
    assert "## Expected Disadvantages / Overhead" in framework_text


def test_framework_does_not_claim_autonomous_execution(framework_text):
    lowered = framework_text.lower()
    assert "pcae is not autonomous" in lowered
    assert "autonomous execution is available" not in lowered


def test_framework_does_not_claim_runtime_enforcement(framework_text):
    lowered = framework_text.lower()
    assert "runtime enforcement is now implemented" not in lowered
    assert "no runtime enforcement" in lowered


def test_framework_does_not_claim_telegram_inbound(framework_text):
    lowered = framework_text.lower()
    assert "telegram inbound is implemented" not in lowered


def test_framework_references_current_rc_state(framework_text):
    assert "v0.1.0-rc1" in framework_text


def test_pcae_local_remains_ignored(gitignore_text):
    assert ".pcae-local/" in gitignore_text
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".pcae-local/anything"],
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_committed_public_narrative_brief_remains_absent():
    assert not REMOVED_BRIEF_PATH.exists()
    tracked = _tracked_files()
    assert "docs/PUBLIC_NARRATIVE_BRIEF_V0_1.md" not in tracked


def test_no_committed_linkedin_or_article_source_packet_exists():
    # Task/done contract filenames are auto-derived from phase titles and
    # may legitimately contain words like "source-packet" (this very
    # phase's own title) without being article material themselves —
    # excluded from this scan, same as the hygiene test's doc exceptions.
    tracked = [
        p for p in _tracked_files()
        if not (p.startswith("tasks/active/") or p.startswith("tasks/done/"))
    ]
    offenders = [
        path
        for path in tracked
        if "pcae-local" in path.lower()
        or "linkedin" in path.lower()
        or "article-draft" in path.lower()
        or "source-packet" in path.lower()
        or "source_packet" in path.lower()
    ]
    assert offenders == [], f"unexpected tracked article/source-packet files: {offenders}"


def test_local_article_packet_if_present_is_untracked():
    """The local packet is optional (filesystem-dependent), but if it
    exists on disk it must never be tracked by git."""
    if LOCAL_ARTICLE_PACKET_PATH.exists():
        tracked = _tracked_files()
        rel = str(
            LOCAL_ARTICLE_PACKET_PATH.relative_to(REPO_ROOT)
        )
        assert rel not in tracked
        result = subprocess.run(
            ["git", "check-ignore", "-q", rel],
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
