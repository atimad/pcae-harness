"""Tests for Phase 113V.N — Phase Finalization Notification Repair.

Covers the two concrete defects the forensic investigation found:

1. `pcae skill invoke phase-finalization <phase-id>` resolved targets only
   against the frozen `_CRI_KNOWN_PHASES` roadmap registry snapshot (last
   extended around Phase 69P/64B.6E), so it failed for *any* later phase --
   ordinary or "special" -- with a generic `target_type_unresolved`/
   `target_unresolved` blocker, unrelated to real Telegram dispatch state.

2. `pcae phase complete` (the authoritative finalization path) had no
   notification-dispatch idempotency guard, unlike `pcae task finish
   --commit`, which already carried a marker-file workaround. Re-running
   `pcae phase complete` for the same phase_id + commit could dispatch a
   duplicate Telegram final report.

Does not re-test pre-existing, unchanged trust/push/gate behavior already
covered by test_phase_report_trust_gate*.py and test_telegram_notifications.py.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.agent import build_skill_invocation_targeting
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import (
    phase_already_notified,
    read_notification_dispatch_marker,
    write_notification_dispatch_marker,
)


def _run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_git_repo(root: Path) -> None:
    _run_git(root, "init")
    _run_git(root, "config", "user.email", "test@example.com")
    _run_git(root, "config", "user.name", "Test User")


def _write_report(reports_dir: Path, phase_id: str, *, status: str = "completed", quarantine: bool = False) -> None:
    target_dir = reports_dir / "quarantine" if quarantine else reports_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".blocked" if quarantine else ""
    payload = {
        "phase_id": phase_id,
        "phase_name": f"Phase {phase_id}",
        "status": status,
        "report_completeness": "blocked" if quarantine else status,
    }
    (target_dir / f"20260101-000000-{phase_id}{suffix}.json").write_text(json.dumps(payload))


# ── Target resolution: live fallback beyond the frozen roadmap registry ──────


def test_resolves_normal_phase_via_history_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_report(tmp_path / ".pcae" / "phase-reports", "150D")

    data = build_skill_invocation_targeting(
        HarnessPath.cwd(), invoke_skill_id="phase-finalization", target_id="150D",
    )
    assert data["target_type"] == "phase"
    assert data["resolution"]["resolved"] is True
    assert data["target"]["target_source"] == "phase_reports_history"


def test_resolves_multiletter_suffix_phase(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_report(tmp_path / ".pcae" / "phase-reports", "150XR")

    data = build_skill_invocation_targeting(
        HarnessPath.cwd(), invoke_skill_id="phase-finalization", target_id="150XR",
    )
    assert data["resolution"]["resolved"] is True


def test_resolves_dotted_subphase_phase(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_report(tmp_path / ".pcae" / "phase-reports", "150X.2")

    data = build_skill_invocation_targeting(
        HarnessPath.cwd(), invoke_skill_id="phase-finalization", target_id="150X.2",
    )
    assert data["resolution"]["resolved"] is True


def test_resolves_dotted_letter_repair_phase(tmp_path, monkeypatch):
    """113D.R / 113V.N-style repair-phase IDs are supported by the grammar."""
    monkeypatch.chdir(tmp_path)
    _write_report(tmp_path / ".pcae" / "phase-reports", "150D.R")

    data = build_skill_invocation_targeting(
        HarnessPath.cwd(), invoke_skill_id="phase-finalization", target_id="150D.R",
    )
    assert data["target_type"] == "phase"
    assert data["resolution"]["resolved"] is True


def test_quarantined_only_phase_resolves_as_blocked_not_valid(tmp_path, monkeypatch):
    """A phase that was only ever quarantined must not read as a clean target."""
    monkeypatch.chdir(tmp_path)
    _write_report(tmp_path / ".pcae" / "phase-reports", "150XQ", quarantine=True)

    data = build_skill_invocation_targeting(
        HarnessPath.cwd(), invoke_skill_id="phase-finalization", target_id="150XQ",
    )
    assert data["resolution"]["resolved"] is True
    assert data["target"]["target_status"] == "blocked"


def test_grammar_valid_but_nowhere_found_is_unresolved_with_clear_reason(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    data = build_skill_invocation_targeting(
        HarnessPath.cwd(), invoke_skill_id="phase-finalization", target_id="150ZZ.9",
    )
    assert data["target_type"] == "phase"
    assert data["resolution"]["resolved"] is False
    signal = data["signals"][0]
    assert signal["signal_type"] == "target_unresolved"
    assert "roadmap registry" in signal["detected_state"]
    assert "phase reports archive" in signal["detected_state"]


def test_invalid_phase_id_form_rejected_distinctly(tmp_path, monkeypatch):
    """A non-phase-shaped ID is rejected as an invalid form, not a generic
    'target_unresolved' -- the two have different remedies."""
    monkeypatch.chdir(tmp_path)

    data = build_skill_invocation_targeting(
        HarnessPath.cwd(),
        invoke_skill_id="phase-finalization",
        target_id="not-a-phase!!",
        target_type="phase",
    )
    assert data["resolution"]["resolved"] is False
    signal = data["signals"][0]
    assert signal["signal_type"] == "invalid_phase_id_form"


def test_notification_dispatch_note_present_for_phase_finalization(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_report(tmp_path / ".pcae" / "phase-reports", "150D")

    data = build_skill_invocation_targeting(
        HarnessPath.cwd(), invoke_skill_id="phase-finalization", target_id="150D",
    )
    note = data["notification_dispatch_note"]
    assert note is not None
    assert "never sends" in note or "never send" in note


def test_notification_dispatch_note_absent_for_other_skills(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tasks" / "active").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    _write_report(tmp_path / ".pcae" / "phase-reports", "150D")

    data = build_skill_invocation_targeting(
        HarnessPath.cwd(), invoke_skill_id="phase-implementation", target_id="150D",
    )
    assert data["notification_dispatch_note"] is None


def test_skill_invoke_preview_has_no_dispatch_side_effects(tmp_path, monkeypatch):
    """The read-only targeting preview must never create/alter the shared
    notification-dispatch marker -- it does not gate or perform dispatch."""
    monkeypatch.chdir(tmp_path)
    _write_report(tmp_path / ".pcae" / "phase-reports", "150D")

    build_skill_invocation_targeting(
        HarnessPath.cwd(), invoke_skill_id="phase-finalization", target_id="150D",
    )
    assert not (tmp_path / ".pcae" / "phase-reports" / ".last-notified.json").exists()


# ── Shared notification-dispatch idempotency marker ──────────────────────────


def test_phase_already_notified_false_when_marker_absent(tmp_path):
    marker_path = tmp_path / ".last-notified.json"
    assert phase_already_notified("150D", "abc12345", marker_path=marker_path) is False
    assert read_notification_dispatch_marker(marker_path) == {}


def test_phase_already_notified_true_same_phase_and_commit(tmp_path):
    marker_path = tmp_path / ".last-notified.json"
    write_notification_dispatch_marker("150D", "abc12345", marker_path=marker_path)
    assert phase_already_notified("150D", "abc12345", marker_path=marker_path) is True


def test_phase_already_notified_true_when_bookkeeping_commit_differs(tmp_path):
    """A later commit does not manufacture a second ordinary completion."""
    marker_path = tmp_path / ".last-notified.json"
    write_notification_dispatch_marker("150D", "abc12345", marker_path=marker_path)
    assert phase_already_notified("150D", "def67890", marker_path=marker_path) is True


def test_phase_already_notified_matches_phase_id_alone_without_commit(tmp_path):
    marker_path = tmp_path / ".last-notified.json"
    write_notification_dispatch_marker("150D", "abc12345", marker_path=marker_path)
    assert phase_already_notified("150D", marker_path=marker_path) is True
    assert phase_already_notified("150E", marker_path=marker_path) is False


# ── `pcae phase complete` idempotency (closes the 113T/U/V asymmetry) ────────


def _write_metadata(root: Path, phase_id: str, commit_hash: str) -> None:
    meta = {
        "phase_id": phase_id,
        "phase_name": f"Test {phase_id}",
        "status": "completed",
        "phase_commits": [{"hash": commit_hash}],
        "recommended_next_phase": "150E",
    }
    (root / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))


def test_phase_complete_dispatches_and_writes_marker(tmp_path, monkeypatch, capsys):
    root = HarnessPath(tmp_path)
    init_harness(root)
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
    monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
    _write_metadata(tmp_path, "150D", "abc1234567890")

    exit_code = main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "Notification dispatch: sent" in out
    marker = read_notification_dispatch_marker(tmp_path / ".pcae" / "phase-reports" / ".last-notified.json")
    assert marker["phase_id"] == "150D"
    assert marker["commit"] == "abc12345"
    assert marker["delivery_purpose"] == "ordinary_completion"
    assert marker["report_digest"]
    assert marker["finalization_snapshot_id"]


def test_phase_complete_second_call_is_idempotent(tmp_path, monkeypatch, capsys):
    """Re-running `pcae phase complete` for the same phase_id + commit must
    not dispatch a second Telegram final report."""
    root = HarnessPath(tmp_path)
    init_harness(root)
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
    monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
    _write_metadata(tmp_path, "150D", "abc1234567890")

    main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
    capsys.readouterr()

    exit_code = main(["phase", "complete", "--summary", "Finished 150D again", "--allow-partial-report"])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "Notification dispatch: sent" not in out
    assert "payload_conflict" in out
    assert "already dispatched" in out


def test_phase_complete_new_commit_same_phase_suppresses_ordinary_resend(tmp_path, monkeypatch, capsys):
    """A report-repair commit requires correction purpose, not another ordinary send."""
    root = HarnessPath(tmp_path)
    init_harness(root)
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
    monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
    _write_metadata(tmp_path, "150D", "abc1234567890")

    main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
    capsys.readouterr()

    _write_metadata(tmp_path, "150D", "def0987654321")
    exit_code = main(["phase", "complete", "--summary", "Finished 150D repaired", "--allow-partial-report"])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "Notification dispatch: sent" not in out
    assert "payload_conflict" in out


def test_phase_complete_missing_notify_enabled_reason_is_accurate(tmp_path, monkeypatch, capsys):
    """Absence of PCAE_NOTIFY_ENABLED must be reported as exactly that --
    never conflated with the unrelated skill-invoke 'target_unresolved'
    concept."""
    root = HarnessPath(tmp_path)
    init_harness(root)
    _init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    _write_metadata(tmp_path, "150D", "abc1234567890")

    exit_code = main(["phase", "complete", "--summary", "Finished 150D", "--allow-partial-report"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "Notification dispatch: skipped" in out
    assert "PCAE_NOTIFY_ENABLED is not set" in out
    assert "target_unresolved" not in out
