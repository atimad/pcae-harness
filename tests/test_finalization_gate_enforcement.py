"""Tests for Phase 113X.1 — Finalization Gate Enforcement Repair.

Repairs 113X Finding 1 (Cross-Agent Governance Verification forensic
review): `validate_finalization_gate()` correctly detects phase-identity
and trust blockers, but `finalize_phase_report()` wrote `latest.md`/
`latest.json` unconditionally regardless of the gate result — a blocked
report could still become the canonical "latest" artifact, with no
persisted record of why it was blocked, and `pcae push check`/report
trust had no way to know the artifact had been refused.

Non-executing, non-authorizing. No real network calls. No Advisory
Runtime, execution, authorization, or plugin changes (out of scope --
see PROJECT_STATUS.md Phase 113X.1).
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import (
    finalize_phase_report,
    read_latest_report,
    write_quarantined_report,
    make_phase_report,
    _apply_canonical_and_trust,
    validate_finalization_gate,
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


# ── Group A: finalize_phase_report() unit-level gate enforcement ───────────


class TestFinalizeGateEnforcement:
    def test_blocked_gate_does_not_write_latest(self):
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)
            blocked_gate = {"finalizable": False, "blockers": ["synthetic blocker"]}

            fin = finalize_phase_report(
                phase_id="900A", phase_name="Blocked Test", status="completed",
                summary="Blocked.", reports_dir=reports_dir, gate=blocked_gate,
            )

            assert fin["blocked"] is True
            assert not (reports_dir / "latest.md").exists()
            assert not (reports_dir / "latest.json").exists()

    def test_blocked_gate_does_not_write_timestamped_canonical_file(self):
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)
            blocked_gate = {"finalizable": False, "blockers": ["synthetic blocker"]}

            finalize_phase_report(
                phase_id="900B", phase_name="Blocked Test", status="completed",
                summary="Blocked.", reports_dir=reports_dir, gate=blocked_gate,
            )

            non_quarantine_files = [
                p for p in reports_dir.glob("*") if p.name != "quarantine"
            ]
            assert non_quarantine_files == []

    def test_blocked_gate_writes_quarantine_artifact_with_blockers(self):
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)
            blockers = ["Report phase_id='900C' does not match PROJECT_STATUS.md current phase '901A'"]
            blocked_gate = {"finalizable": False, "blockers": blockers}

            fin = finalize_phase_report(
                phase_id="900C", phase_name="Blocked Test", status="completed",
                summary="Blocked.", reports_dir=reports_dir, gate=blocked_gate,
            )

            qmd = Path(fin["paths"]["quarantine_markdown"])
            qjson = Path(fin["paths"]["quarantine_json"])
            assert qmd.exists()
            assert qjson.exists()
            assert qmd.is_relative_to(reports_dir / "quarantine")
            assert qjson.is_relative_to(reports_dir / "quarantine")

            md_content = qmd.read_text()
            assert "BLOCKED" in md_content
            assert blockers[0] in md_content

            json_content = json.loads(qjson.read_text())
            assert json_content["finalization_blockers"] == blockers
            assert json_content["report_completeness"] == "blocked"
            assert json_content["phase_id"] == "900C"

    def test_blocked_gate_never_overwrites_existing_valid_latest(self):
        """A blocked finalization must never clobber a prior *valid* latest
        report -- the exact failure mode of 113X Finding 1/2."""
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)

            valid = finalize_phase_report(
                phase_id="900D", phase_name="Valid Phase", status="completed",
                summary="Valid.", reports_dir=reports_dir,
            )
            valid_latest_json = Path(valid["paths"]["latest_json"]).read_text()

            blocked_gate = {"finalizable": False, "blockers": ["synthetic blocker"]}
            finalize_phase_report(
                phase_id="900E", phase_name="Blocked Phase", status="completed",
                summary="Blocked.", reports_dir=reports_dir, gate=blocked_gate,
            )

            # latest.json/md must be untouched -- still the valid 900D report.
            assert (reports_dir / "latest.json").read_text() == valid_latest_json
            still_latest = read_latest_report(reports_dir)
            assert still_latest.phase_id == "900D"

    def test_finalizable_gate_writes_normally(self):
        """A gate with no blockers must not change behavior at all."""
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)
            ok_gate = {"finalizable": True, "blockers": []}

            fin = finalize_phase_report(
                phase_id="900F", phase_name="OK Test", status="completed",
                summary="OK.", reports_dir=reports_dir, gate=ok_gate,
            )

            assert not fin.get("blocked")
            assert Path(fin["paths"]["latest_markdown"]).exists()
            assert Path(fin["paths"]["latest_json"]).exists()

    def test_gate_none_preserves_prior_unconditional_write_behavior(self):
        """Existing callers/tests that never pass `gate=` (the default)
        must see byte-for-byte the same behavior as before this repair."""
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)
            fin = finalize_phase_report(
                phase_id="900G", phase_name="Legacy Caller", status="completed",
                summary="Legacy.", reports_dir=reports_dir,
            )
            assert not fin.get("blocked")
            assert Path(fin["paths"]["latest_markdown"]).exists()
            assert Path(fin["paths"]["latest_json"]).exists()
            assert Path(fin["paths"]["markdown"]).exists()
            assert Path(fin["paths"]["json"]).exists()


class TestWriteQuarantinedReportDirect:
    def test_quarantine_path_is_never_named_latest(self):
        with tempfile.TemporaryDirectory() as td:
            reports_dir = Path(td)
            report = make_phase_report(
                phase_id="901A", phase_name="X", status="completed", summary="Y",
            )
            paths = write_quarantined_report(report, reports_dir, ["blocker one"])
            assert "latest" not in Path(paths["quarantine_markdown"]).name
            assert "latest" not in Path(paths["quarantine_json"]).name


# ── Group B: `pcae phase complete` CLI-level enforcement ────────────────────


class TestPhaseCompleteEnforcement:
    def test_identity_blocked_report_does_not_overwrite_latest(self, tmp_path, monkeypatch, capsys):
        """Reproduces 113X Finding 2 directly: complete a *valid* phase
        first (establishing a trustworthy latest.json), then attempt a
        phase-identity-mismatched completion and confirm latest.json is
        left untouched."""
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        assert exit_code == 0
        first_latest = (tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text()

        # PROJECT_STATUS.md doesn't exist in this fixture repo, so the
        # identity check's PROJECT_STATUS.md branch is a no-op there;
        # exercise the other blocker classes instead (files_changed=0),
        # which is the same enforcement path (blockers -> quarantine).
        _write_metadata(tmp_path, phase_id="205E", files_changed_count=0)
        exit_code2 = main(["phase", "complete", "--summary", "Phase 205E: done."])
        output = capsys.readouterr().out

        assert exit_code2 == 1
        assert "BLOCKED by finalization gate" in output
        assert "Report quarantined" in output
        # The previously-written, valid latest.json must be unchanged.
        assert (tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text() == first_latest

    def test_blocked_completion_exits_non_zero(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        assert exit_code == 1

    def test_blocked_completion_writes_quarantine_artifact(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert "Quarantine markdown:" in output
        assert "Quarantine json:" in output
        quarantine_dir = tmp_path / ".pcae" / "phase-reports" / "quarantine"
        assert quarantine_dir.exists()
        assert list(quarantine_dir.glob("*.blocked.json"))

    def test_blocked_completion_never_creates_latest(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 205D: done."])

        assert not (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()
        assert not (tmp_path / ".pcae" / "phase-reports" / "latest.md").exists()

    def test_valid_completion_unaffected_by_repair(self, tmp_path, monkeypatch, capsys):
        """Existing valid phase finalization must remain unchanged."""
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path)
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Trust gate (105D): complete" in output
        assert "Phase report: created" in output
        assert (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()
        assert (tmp_path / ".pcae" / "phase-reports" / "latest.md").exists()

    def test_allow_partial_report_still_bypasses_as_before(self, tmp_path, monkeypatch, capsys):
        """The pre-existing --allow-partial-report override (105D) is
        unrelated scope to 113X.1 and must keep writing canonically."""
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

    def test_blocked_completion_suppresses_notification_dispatch(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, files_changed_count=0)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "filesystem")

        main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert "Notification dispatch: skipped" in output
        assert not (tmp_path / ".pcae" / "notifications").exists()


# ── Group C: push check / report trust must not trust a blocked artifact ───


class TestPushCheckDoesNotTrustBlockedArtifact:
    def test_push_check_reads_prior_valid_report_not_blocked_one(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 205D: done."])
        capsys.readouterr()

        _write_metadata(tmp_path, phase_id="205E", files_changed_count=0)
        main(["phase", "complete", "--summary", "Phase 205E: done."])
        capsys.readouterr()

        # read_latest_report() -- what pcae push check's report-trust path
        # consults -- must still see the last *valid* report (205D), never
        # the blocked 205E attempt.
        latest = read_latest_report(Path(tmp_path) / ".pcae" / "phase-reports")
        assert latest is not None
        assert latest.phase_id == "205D"
        assert latest.report_completeness != "blocked"
