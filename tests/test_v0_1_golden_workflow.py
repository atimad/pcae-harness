"""Tests for Phase 106C — Golden Workflow Stabilization.

Documentation-focused, plus lightweight CLI availability checks (--help
only, no side effects). Non-executing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = ROOT / "docs" / "V0_1_GOLDEN_WORKFLOW.md"


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DOC_PATH.read_text()


def test_golden_workflow_doc_exists():
    assert DOC_PATH.is_file()


def test_states_non_executing_by_design(doc_text):
    assert "without ever\nexecuting code" in doc_text or "non-executing" in doc_text.lower()


def test_includes_start_of_phase_checklist(doc_text):
    assert "### 1. Start-of-session / start-of-phase" in doc_text


def test_includes_pre_finalization_checklist(doc_text):
    assert "### 4. Pre-finalization" in doc_text


def test_includes_finalization_checklist(doc_text):
    assert "### 5. Finalization: report, notify, commit, push" in doc_text


def test_includes_post_push_verification_checklist(doc_text):
    assert "### 6. Post-completion verification" in doc_text


def test_includes_pcae_health(doc_text):
    assert "pcae health" in doc_text


def test_includes_pcae_check(doc_text):
    assert "pcae check" in doc_text


def test_includes_pcae_doctor_task_memory(doc_text):
    assert "pcae doctor task-memory" in doc_text


def test_includes_pcae_push_check(doc_text):
    assert "pcae push check" in doc_text


def test_includes_pcae_phase_report_trust(doc_text):
    assert "pcae phase-report trust" in doc_text


def test_includes_pcae_phase_report_show_latest_trust(doc_text):
    assert "pcae phase-report show --latest --trust" in doc_text


def test_includes_pcae_skill_invoke_phase_finalization(doc_text):
    assert "pcae skill invoke phase-finalization <PHASE_ID>" in doc_text


def test_includes_pcae_task_finish_commit(doc_text):
    assert "pcae task finish --staged-file-aware --commit" in doc_text
    assert "pcae task finish --commit" in doc_text


def test_states_telegram_outbound_only(doc_text):
    assert "outbound-only" in doc_text.lower() or "entirely outbound" in doc_text.lower()
    assert "no inbound handler" in doc_text.lower()


def test_states_raw_git_commit_push_unsupported(doc_text):
    section = doc_text.split("## Unsupported for v0.1 Production Workflow")[1]
    assert "git commit" in section
    assert "git push" in section


def test_states_no_runtime_enforcement_or_autonomous_execution(doc_text):
    assert "autonomous backend execution" in doc_text.lower() or "autonomous execution" in doc_text.lower()


def test_references_v0_2_autonomy_as_future_target(doc_text):
    assert "## Relationship to v0.2 Autonomy" in doc_text
    assert "v0.2" in doc_text


def test_includes_recommended_next_phase(doc_text):
    assert "106D" in doc_text


def test_required_vs_optional_commands_defined(doc_text):
    assert "### Required" in doc_text
    assert "### Optional diagnostics" in doc_text


def test_release_scope_doc_references_golden_workflow():
    release_scope = (ROOT / "docs" / "RELEASE_SCOPE_V0_1.md").read_text()
    assert "V0_1_GOLDEN_WORKFLOW" in release_scope


def test_release_scope_doc_states_fully_green_baseline():
    release_scope = (ROOT / "docs" / "RELEASE_SCOPE_V0_1.md").read_text()
    assert "4390/4390" in release_scope


# ── Lightweight command availability checks (--help only, no side effects) ──


def _help(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pcae"] + args + ["--help"],
        capture_output=True, text=True, cwd=ROOT, timeout=15,
    )


class TestGoldenWorkflowCommandAvailability:
    def test_phase_report_trust_help(self):
        r = _help(["phase-report", "trust"])
        assert r.returncode == 0
        assert "--metadata" in r.stdout

    def test_phase_report_show_help(self):
        r = _help(["phase-report", "show"])
        assert r.returncode == 0
        assert "--trust" in r.stdout

    def test_notify_status_help(self):
        r = _help(["notify", "status"])
        assert r.returncode == 0

    def test_push_check_help(self):
        r = _help(["push", "check"])
        assert r.returncode == 0

    def test_doctor_task_memory_help(self):
        r = _help(["doctor", "task-memory"])
        assert r.returncode == 0

    def test_task_finish_help(self):
        r = _help(["task", "finish"])
        assert r.returncode == 0
        assert "--commit" in r.stdout

    def test_commit_implementation_help(self):
        r = _help(["commit", "implementation"])
        assert r.returncode == 0
        assert "--message" in r.stdout

    def test_health_help(self):
        r = _help(["health"])
        assert r.returncode == 0

    def test_check_help(self):
        r = _help(["check"])
        assert r.returncode == 0

    def test_skill_invoke_help(self):
        r = _help(["skill", "invoke"])
        assert r.returncode == 0
