"""Phase 145H.3R.1 — Phase Completion Metadata Sequencing and Finalization
Repair.

Regression coverage for the recurring finalization defect documented at
Phase 145G.3, 145H.1, 145H.2, 145H.3, and recovered (without repair) at
145H.3R: ``complete_phase()`` (which releases the agent lock and records
the ``phase_completed``/``agent_released`` provenance events) used to run
*before* ``_finalize_report_and_notify()``'s validation (canonical
identity resolution, the finalization gate, the Repository Transition
Validator, cross-phase commit contamination detection). Every one of the
four historical recurrences was a *correctly* rejected completion attempt
(stale ``.pcae/phase-completion-metadata.json`` still naming the
predecessor phase) that nonetheless released the agent lock, forcing a
manual ``pcae session bootstrap --sync-lock`` before any retry.

These tests independently reproduce that failure shape against the real
``pcae phase complete`` CLI path (not a unit-level shortcut) and prove the
repaired sequencing: on rejection, the lock stays held, no
``phase_completed``/``agent_released`` provenance is recorded, and the
task remains active; a corrected retry succeeds through ordinary commands
alone.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.agent import acquire_agent_lock, read_agent_lock
from pcae.core.paths import HarnessPath
from pcae.core.provenance import read_provenance_history


def _init_repo(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n"
        "## Current Phase\n\n"
        "Phase 205D — Lock Sequencing Fixture.\n\n"
        "Recommended next repo phase: 205E — Next Phase.\n",
        encoding="utf-8",
    )


def _metadata(**overrides) -> dict:
    data = {
        "phase_id": "205D",
        "phase_name": "Lock Sequencing Fixture",
        "files_changed_count": 2,
        "tests_added_or_updated": "3 tests added",
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": "passed"},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "clean"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
        ],
        "no_go_confirmation": (
            "No validator bypass. No task finish integration. No notification enforcement. "
            "No push integration. No Permission Broker change. No execution. No REST. "
            "No Telegram inbound. No runtime invocation. No adapter execution. No automatic apply."
        ),
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": "205E — Next Phase",
        "phase_commits": [{"hash": "abc1234500000000"}],
        "commit_attribution": "phase_owned",
        "execution_availability": "unavailable",
    }
    data.update(overrides)
    return data


def _write_metadata(tmp_path: Path, **overrides) -> None:
    path = tmp_path / ".pcae" / "phase-completion-metadata.json"
    path.write_text(json.dumps(_metadata(**overrides), indent=2), encoding="utf-8")


def _complete(tmp_path: Path, monkeypatch, phase_id: str = "205D", phase_name: str = "Lock Sequencing Fixture") -> tuple[int, str]:
    monkeypatch.chdir(tmp_path)
    code = main([
        "phase", "complete", "--summary", f"Phase {phase_id} complete.",
        "--phase-id", phase_id, "--phase-name", phase_name,
    ])
    return code, ""


# ---------------------------------------------------------------------------
# 7.4 — Validation rejection preserves the agent lock (direct reproduction
# of the 145G.3/145H.1/145H.2/145H.3 recurrence shape).
# ---------------------------------------------------------------------------


def test_stale_metadata_rejection_preserves_lock_and_provenance(tmp_path, monkeypatch, capsys):
    """Independent reproduction: exactly the historical failure shape.

    ``.pcae/phase-completion-metadata.json`` still identifies a different
    phase id ("205X") than the one actually being completed ("205D") --
    the same stale-metadata shape the Repository Transition Validator
    correctly rejected four times in production (145G.3, 145H.1, 145H.2,
    145H.3). Before the repair, this rejection still released the agent
    lock. After the repair, a REJECT verdict must never mutate lock or
    provenance state.
    """
    _init_repo(tmp_path)
    _write_metadata(tmp_path, phase_id="205X")  # stale: doesn't match the completed phase
    root = HarnessPath(tmp_path)
    acquire_agent_lock(root, "claude-local")

    history_before = read_provenance_history(root)
    events_before = len(history_before.events)

    code, _ = _complete(tmp_path, monkeypatch)
    output = capsys.readouterr().out

    assert code == 1
    assert "Transition rejected" in output
    assert "Phase complete." not in output  # never claims completion on rejection

    lock = read_agent_lock(root)
    assert lock is not None, "agent lock must remain held after a rejected completion"
    assert lock.agent_id == "claude-local"

    history_after = read_provenance_history(root)
    event_types_after = [e.event_type for e in history_after.events]
    assert "phase_completed" not in event_types_after
    assert "agent_released" not in event_types_after
    assert len(history_after.events) == events_before


def test_quarantine_verdict_preserves_lock(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(
        tmp_path,
        validation_results=[
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": "passed"},
        ],
    )
    root = HarnessPath(tmp_path)
    acquire_agent_lock(root, "claude-local")

    code, _ = _complete(tmp_path, monkeypatch)
    output = capsys.readouterr().out

    assert code == 1
    assert "Transition quarantined" in output
    assert read_agent_lock(root) is not None


def test_human_review_verdict_preserves_lock(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(tmp_path, requires_human_review=True)
    root = HarnessPath(tmp_path)
    acquire_agent_lock(root, "claude-local")

    code, _ = _complete(tmp_path, monkeypatch)
    output = capsys.readouterr().out

    assert code == 1
    assert "Human review required" in output
    assert read_agent_lock(root) is not None


def test_cross_phase_contamination_rejection_preserves_lock(tmp_path, monkeypatch, capsys):
    """7.16 — the repair must not weaken cross-phase contamination
    detection. A commit whose own subject names a different phase must
    still fail closed, and that failure must preserve the lock."""
    _init_repo(tmp_path)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Phase 999Z: unrelated work"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    log = subprocess.run(
        ["git", "log", "-1", "--format=%H"], cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    contaminating_hash = log.stdout.strip()
    _write_metadata(tmp_path, phase_commits=[{"hash": contaminating_hash}], commit_attribution="")
    root = HarnessPath(tmp_path)
    acquire_agent_lock(root, "claude-local")

    code, _ = _complete(tmp_path, monkeypatch)
    output = capsys.readouterr().out

    assert code == 1
    assert "cross-phase commit contamination" in output
    lock = read_agent_lock(root)
    assert lock is not None, "cross-phase contamination rejection must still preserve the lock"


# ---------------------------------------------------------------------------
# 7.5 / 7.17 — Deterministic retry: correcting the problem and re-running
# `pcae phase complete` succeeds through ordinary commands only, with no
# manual lock reacquisition, no hand-authored metadata, no duplicate
# lifecycle records.
# ---------------------------------------------------------------------------


def test_retry_after_rejection_succeeds_without_manual_recovery(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(tmp_path, phase_id="205X")  # stale -- will be rejected
    root = HarnessPath(tmp_path)
    acquire_agent_lock(root, "claude-local")

    code1, _ = _complete(tmp_path, monkeypatch)
    capsys.readouterr()
    assert code1 == 1
    assert read_agent_lock(root) is not None

    # Correct the actual problem (the operator fixes the stale metadata) and
    # retry with *ordinary* supported commands only -- no pcae session
    # bootstrap --sync-lock, no direct .pcae/agent-locks edit.
    _write_metadata(tmp_path, phase_id="205D")
    code2, _ = _complete(tmp_path, monkeypatch)
    output2 = capsys.readouterr().out

    assert code2 == 0
    assert "Repository transition validator: Transition validated" in output2
    assert "Phase complete." in output2
    assert "Agent lock: released (by claude-local)" in output2
    assert read_agent_lock(root) is None

    history = read_provenance_history(root)
    event_types = [e.event_type for e in history.events]
    assert event_types.count("phase_completed") == 1
    assert event_types.count("agent_released") == 1


def test_retry_after_quarantine_succeeds_without_manual_recovery(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(
        tmp_path,
        validation_results=[
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
        ],
    )
    root = HarnessPath(tmp_path)
    acquire_agent_lock(root, "claude-local")

    code1, _ = _complete(tmp_path, monkeypatch)
    capsys.readouterr()
    assert code1 == 1
    assert read_agent_lock(root) is not None

    _write_metadata(tmp_path)  # fully valid metadata
    code2, _ = _complete(tmp_path, monkeypatch)
    output2 = capsys.readouterr().out

    assert code2 == 0
    assert read_agent_lock(root) is None
    history = read_provenance_history(root)
    event_types = [e.event_type for e in history.events]
    assert event_types.count("phase_completed") == 1
    assert event_types.count("agent_released") == 1


# ---------------------------------------------------------------------------
# 7.3 — Rehydrated existing lock: starting from a bootstrap session that
# rehydrates an already-held lock must not skip required validation.
# ---------------------------------------------------------------------------


def test_rehydrated_lock_still_enforces_validation(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(tmp_path, phase_id="205X")
    root = HarnessPath(tmp_path)
    acquire_agent_lock(root, "claude-local")

    # Simulate a rehydrated bootstrap session: reading the lock (as
    # `pcae session bootstrap --sync-lock` would) must not itself grant
    # any bypass of the finalization validator.
    rehydrated = read_agent_lock(root)
    assert rehydrated is not None
    assert rehydrated.agent_id == "claude-local"

    code, _ = _complete(tmp_path, monkeypatch)
    output = capsys.readouterr().out

    assert code == 1
    assert "Transition rejected" in output
    assert read_agent_lock(root) is not None


# ---------------------------------------------------------------------------
# 7.1 / accept-path parity — a genuinely valid completion still releases
# the lock exactly once and records exactly one phase_completed/
# agent_released pair (unchanged success-path behavior).
# ---------------------------------------------------------------------------


def test_accepted_completion_releases_lock_exactly_once(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(tmp_path)
    root = HarnessPath(tmp_path)
    acquire_agent_lock(root, "claude-local")

    code, _ = _complete(tmp_path, monkeypatch)
    output = capsys.readouterr().out

    assert code == 0
    assert "Phase complete." in output
    assert "Agent lock: released (by claude-local)" in output
    assert read_agent_lock(root) is None

    history = read_provenance_history(root)
    event_types = [e.event_type for e in history.events]
    assert event_types.count("phase_completed") == 1
    assert event_types.count("agent_released") == 1


def test_accepted_completion_without_lock_still_succeeds(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(tmp_path)
    monkeypatch.chdir(tmp_path)

    code = main([
        "phase", "complete", "--summary", "Phase 205D complete.",
        "--phase-id", "205D", "--phase-name", "Lock Sequencing Fixture",
    ])
    output = capsys.readouterr().out

    assert code == 0
    assert "Phase complete." in output
    assert "Agent lock: none" in output
