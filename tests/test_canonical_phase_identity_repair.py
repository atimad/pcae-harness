"""Tests for Phase 113X.2 — Canonical Phase Identity Source Repair.

Closes the one remaining 113X (Cross-Agent Governance Verification)
forensic divergence gap: in `pcae phase complete`, a mismatch between
the CLI/summary-derived phase_id and the `.pcae/phase-completion-
metadata.json` file's own declared phase_id was resolved silently
(metadata discarded, a console-only warning printed, finalization
proceeded on git-derived fallback data) without ever becoming a
`validate_finalization_gate()` blocker. `resolve_finalization_phase_
identity()` is the single canonical resolution point for these two
identity sources; a genuine conflict is now threaded into the gate as
a blocker, enforced through the same 113X.1 quarantine path as every
other phase-identity mismatch.

Non-executing, non-authorizing. No real network calls. No Advisory
Runtime, execution, authorization, Runtime Snapshot, Telegram inbound,
REST, web UI, or plugin changes (out of scope -- see PROJECT_STATUS.md
Phase 113X.2).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import (
    read_latest_report,
    resolve_finalization_phase_identity,
)


def _init_repo(tmp_path: Path) -> HarnessPath:
    root = HarnessPath(tmp_path)
    init_harness(root)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
    return root


def _complete_metadata(**overrides) -> dict:
    meta = {
        "phase_id": "205D",
        "files_changed_count": 2,
        "tests_added_or_updated": "5 tests added",
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "clean"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
        ],
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": ""},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "no_go_confirmation": (
            "No runtime enforcement. No execution. No subprocess. No shell. "
            "No network. No Telegram inbound. No apply. No commit authorization. "
            "No push authorization. No rollback. No adapter execution."
        ),
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": "205E — Next Phase",
        "phase_commits": [{"hash": "abc1234500000000"}],
        "commit_attribution": "phase_owned",
    }
    meta.update(overrides)
    return meta


def _write_metadata(tmp_path: Path, **overrides) -> dict:
    meta = _complete_metadata(**overrides)
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))
    return meta


# ── Group A: resolve_finalization_phase_identity() unit-level ──────────────


class TestResolveFinalizationPhaseIdentity:
    def test_matching_ids_no_conflict(self):
        meta_id, conflict = resolve_finalization_phase_identity("205D", {"phase_id": "205D"})
        assert meta_id == "205D"
        assert conflict is None

    def test_mismatched_ids_conflict(self):
        meta_id, conflict = resolve_finalization_phase_identity("205E", {"phase_id": "205D"})
        assert meta_id == ""
        assert conflict is not None
        assert "205E" in conflict
        assert "205D" in conflict

    def test_no_metadata_phase_id_no_conflict(self):
        meta_id, conflict = resolve_finalization_phase_identity("205D", {})
        assert meta_id == ""
        assert conflict is None

    def test_derived_unknown_uses_metadata(self):
        """When the summary has no 'Phase X' reference at all, there is
        nothing for the metadata's declared phase_id to disagree with."""
        meta_id, conflict = resolve_finalization_phase_identity("unknown", {"phase_id": "205D"})
        assert meta_id == "205D"
        assert conflict is None

    def test_derived_empty_uses_metadata(self):
        meta_id, conflict = resolve_finalization_phase_identity("", {"phase_id": "205D"})
        assert meta_id == "205D"
        assert conflict is None

    def test_no_metadata_at_all(self):
        meta_id, conflict = resolve_finalization_phase_identity("205D", None)
        assert meta_id == ""
        assert conflict is None


# ── Group B: matching identities finalize normally (regression) ────────────


class TestMatchingIdentityUnaffected:
    def test_matching_phase_id_completes_normally(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Trust gate (105D): complete" in output
        assert "BLOCKED" not in output
        assert (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()
        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_id"] == "205D"


# ── Group C: mismatched CLI/metadata identity fails closed ──────────────────


class TestMismatchedIdentityFailsClosed:
    def test_mismatched_identity_exits_non_zero(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        # Summary claims a different phase than the metadata file does.
        exit_code = main(["phase", "complete", "--summary", "Phase 205E: done."])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "BLOCKED by finalization gate" in output
        assert "phase identity" in output
        assert "205E" in output and "205D" in output

    def test_mismatched_identity_prints_conflict_warning(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 205E: done."])
        output = capsys.readouterr().out

        assert "Warning:" in output
        assert "does not match" in output


# ── Group D: mismatched identity never overwrites latest.md/latest.json ────


class TestMismatchedIdentityNeverOverwritesLatest:
    def test_mismatch_after_valid_leaves_latest_untouched(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        assert exit_code == 0
        capsys.readouterr()
        valid_latest = (tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text()

        _write_metadata(tmp_path, phase_id="205D")  # metadata still says 205D
        exit_code2 = main(["phase", "complete", "--summary", "Phase 205E: done."])  # summary disagrees
        capsys.readouterr()

        assert exit_code2 == 1
        # latest.json/md must be untouched -- still the valid 205D report.
        assert (tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text() == valid_latest
        still_latest = read_latest_report(tmp_path / ".pcae" / "phase-reports")
        assert still_latest.phase_id == "205D"

    def test_mismatch_never_creates_latest_from_scratch(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 205E: done."])

        assert not (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()
        assert not (tmp_path / ".pcae" / "phase-reports" / "latest.md").exists()


# ── Group E: mismatch evidence preserved in quarantine ──────────────────────


class TestMismatchedIdentityPreservedInQuarantine:
    def test_quarantine_artifact_contains_both_conflicting_ids(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 205E: done."])
        output = capsys.readouterr().out

        quarantine_dir = tmp_path / ".pcae" / "phase-reports" / "quarantine"
        assert quarantine_dir.exists()
        json_files = list(quarantine_dir.glob("*.blocked.json"))
        assert json_files

        data = json.loads(json_files[0].read_text())
        blockers = data["finalization_blockers"]
        assert any("205E" in b and "205D" in b for b in blockers)
        assert data["report_completeness"] == "blocked"
        # The report's own phase_id is the single, canonical (summary-derived)
        # identity -- not left ambiguous between the two conflicting sources.
        assert data["phase_id"] == "205E"

        assert "Quarantine json:" in output


# ── Group F: status/report consistency reflects the canonical identity ─────


class TestStatusReflectsCanonicalIdentity:
    def test_blocked_report_has_single_unambiguous_phase_id(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="900Z")
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 205E: done."])

        quarantine_dir = tmp_path / ".pcae" / "phase-reports" / "quarantine"
        data = json.loads(next(quarantine_dir.glob("*.blocked.json")).read_text())
        # Exactly one canonical phase_id on the artifact -- the CLI/summary
        # side -- never the (conflicting, untrusted) metadata's value.
        assert data["phase_id"] == "205E"
        assert data["phase_id"] != "900Z"

    def test_valid_report_metadata_and_body_agree(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 205D: done."])

        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_id"] == "205D"


# ── Group G: 113X.1 blocked-finalization behavior remains intact ───────────


class TestPriorBlockedFinalizationBehaviorIntact:
    def test_files_changed_zero_still_blocks_and_quarantines(self, tmp_path, monkeypatch, capsys):
        """Regression guard for 113X.1: a non-identity blocker (files_changed=0)
        must still quarantine exactly as before this phase's change."""
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "BLOCKED by finalization gate" in output
        assert "Report quarantined" in output
        assert not (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()

    def test_allow_partial_report_still_bypasses_as_before(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)

        exit_code = main([
            "phase", "complete", "--summary", "Phase 205D: done.", "--allow-partial-report",
        ])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "--allow-partial-report" in output
        assert (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()
