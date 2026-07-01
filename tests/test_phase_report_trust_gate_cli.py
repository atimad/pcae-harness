"""CLI tests for Phase 105B — Phase Report Trust Gate CLI / Finalization
Integration. Read-only except explicit local test fixtures. Non-executing,
non-authorizing.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "pcae", "phase-report"] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or REPO_ROOT)


def _complete_metadata(**overrides) -> dict:
    r = {
        "phase_id": "205X",
        "status": "completed",
        "files_changed": 4,
        "tests_run": 12,
        "commits": ["abc12345"],
        "pushed": "pushed",
        "summary": "Test report for trust CLI.",
        "recommended_next_phase": "205Y — Next Phase",
        "governance_results": {
            "pcae_health": "healthy",
            "pcae_check": "passed",
            "pcae_doctor_task_memory": "warnings",
            "pcae_push_check": "clean",
            "telegram_runtime": "loaded, configured, enabled",
        },
        "test_results": {
            "report_notification_tests": "1/1 (passed)",
            "bootstrap_session_reporting_tests": "present",
            "fast_green": "10/10 (passed)",
        },
    }
    r.update(overrides)
    return r


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, indent=2))
    return path


# ── Group A: CLI JSON validation ────────────────────────────────────────────


class TestCliJsonValidation:
    def test_complete_metadata_returns_complete_true(self, tmp_path: Path):
        meta = _write_json(tmp_path / "meta.json", _complete_metadata())
        result = _run(["trust", "--metadata", str(meta), "--json"])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["complete"] is True
        assert data["status"] == "complete"

    def test_partial_metadata_returns_complete_false(self, tmp_path: Path):
        raw = _complete_metadata()
        raw["test_results"] = dict(raw["test_results"])
        raw["test_results"]["fast_green"] = "TBD"
        meta = _write_json(tmp_path / "meta.json", raw)
        result = _run(["trust", "--metadata", str(meta), "--json"])
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["complete"] is False
        assert data["status"] == "partial"

    def test_missing_fields_listed(self, tmp_path: Path):
        raw = _complete_metadata()
        del raw["summary"]
        meta = _write_json(tmp_path / "meta.json", raw)
        data = json.loads(_run(["trust", "--metadata", str(meta), "--json"]).stdout)
        assert "summary" in data["missing_fields"]

    def test_placeholder_fields_listed(self, tmp_path: Path):
        raw = _complete_metadata()
        raw["test_results"] = dict(raw["test_results"])
        raw["test_results"]["fast_green"] = "pending"
        meta = _write_json(tmp_path / "meta.json", raw)
        data = json.loads(_run(["trust", "--metadata", str(meta), "--json"]).stdout)
        assert any("fast_green" in f for f in data["placeholder_fields"])

    def test_repair_required_true_for_partial(self, tmp_path: Path):
        raw = _complete_metadata(commits="TBD")
        meta = _write_json(tmp_path / "meta.json", raw)
        data = json.loads(_run(["trust", "--metadata", str(meta), "--json"]).stdout)
        assert data["repair_required"] is True

    def test_can_be_active_latest_false_for_partial(self, tmp_path: Path):
        raw = _complete_metadata(commits=[])
        meta = _write_json(tmp_path / "meta.json", raw)
        data = json.loads(_run(["trust", "--metadata", str(meta), "--json"]).stdout)
        assert data["can_be_active_latest"] is False

    def test_phase_id_included(self, tmp_path: Path):
        meta = _write_json(tmp_path / "meta.json", _complete_metadata(phase_id="205Z"))
        data = json.loads(_run(["trust", "--metadata", str(meta), "--json"]).stdout)
        assert data["phase_id"] == "205Z"


# ── Group B: CLI human validation ───────────────────────────────────────────


class TestCliHumanValidation:
    def test_complete_report_says_complete(self, tmp_path: Path):
        meta = _write_json(tmp_path / "meta.json", _complete_metadata())
        result = _run(["trust", "--metadata", str(meta)])
        assert result.returncode == 0
        assert "complete" in result.stdout.lower()

    def test_partial_report_says_partial(self, tmp_path: Path):
        raw = _complete_metadata()
        raw["test_results"] = dict(raw["test_results"])
        raw["test_results"]["fast_green"] = "TBD"
        meta = _write_json(tmp_path / "meta.json", raw)
        result = _run(["trust", "--metadata", str(meta)])
        assert result.returncode == 1
        assert "partial" in result.stdout.lower()

    def test_missing_fields_visible(self, tmp_path: Path):
        raw = _complete_metadata()
        del raw["phase_id"]
        meta = _write_json(tmp_path / "meta.json", raw)
        result = _run(["trust", "--metadata", str(meta)])
        assert "phase_id" in result.stdout

    def test_placeholder_fields_visible(self, tmp_path: Path):
        raw = _complete_metadata(files_changed="not captured")
        meta = _write_json(tmp_path / "meta.json", raw)
        result = _run(["trust", "--metadata", str(meta)])
        assert "files_changed" in result.stdout

    def test_repair_guidance_visible(self, tmp_path: Path):
        raw = _complete_metadata(commits="TBD")
        meta = _write_json(tmp_path / "meta.json", raw)
        result = _run(["trust", "--metadata", str(meta)])
        assert "Repair guidance" in result.stdout


# ── Group C: File options ───────────────────────────────────────────────────


class TestFileOptions:
    def test_metadata_path_validates(self, tmp_path: Path):
        meta = _write_json(tmp_path / "meta.json", _complete_metadata())
        result = _run(["trust", "--metadata", str(meta)])
        assert result.returncode == 0

    def test_missing_metadata_path_fails_clearly(self, tmp_path: Path):
        result = _run(["trust", "--metadata", str(tmp_path / "nope.json")])
        assert result.returncode == 2
        assert "not found" in result.stdout.lower()

    def test_invalid_json_fails_clearly(self, tmp_path: Path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json")
        result = _run(["trust", "--metadata", str(path)])
        assert result.returncode == 2
        assert "invalid json" in result.stdout.lower()

    def test_unsupported_markdown_report_fails_clearly(self, tmp_path: Path):
        path = tmp_path / "report.md"
        path.write_text("# Phase Report\n")
        result = _run(["trust", "--report", str(path)])
        assert result.returncode == 2
        assert "not supported" in result.stdout.lower()

    def test_report_json_path_validates(self, tmp_path: Path):
        report = _write_json(tmp_path / "report.json", _complete_metadata())
        result = _run(["trust", "--report", str(report)])
        assert result.returncode == 0

    def test_missing_report_path_fails_clearly(self, tmp_path: Path):
        result = _run(["trust", "--report", str(tmp_path / "nope.json")])
        assert result.returncode == 2
        assert "not found" in result.stdout.lower()


# ── Group D: Latest canonical behavior ──────────────────────────────────────


class TestLatestCanonicalBehavior:
    def test_default_reads_latest_json_if_present(self, tmp_path: Path):
        reports_dir = tmp_path / "phase-reports"
        reports_dir.mkdir()
        _write_json(reports_dir / "latest.json", _complete_metadata(phase_id="LATEST1"))
        result = _run(["trust", "--reports-dir", str(reports_dir), "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["phase_id"] == "LATEST1"

    def test_complete_latest_passes(self, tmp_path: Path):
        reports_dir = tmp_path / "phase-reports"
        reports_dir.mkdir()
        _write_json(reports_dir / "latest.json", _complete_metadata())
        result = _run(["trust", "--reports-dir", str(reports_dir)])
        assert result.returncode == 0

    def test_partial_latest_fails(self, tmp_path: Path):
        reports_dir = tmp_path / "phase-reports"
        reports_dir.mkdir()
        raw = _complete_metadata()
        raw["test_results"] = dict(raw["test_results"])
        raw["test_results"]["fast_green"] = "TBD"
        _write_json(reports_dir / "latest.json", raw)
        result = _run(["trust", "--reports-dir", str(reports_dir)])
        assert result.returncode == 1

    def test_complete_selected_over_earlier_partial_same_phase(self, tmp_path: Path):
        reports_dir = tmp_path / "phase-reports"
        reports_dir.mkdir()
        partial = _complete_metadata(phase_id="105SEL")
        partial["test_results"] = dict(partial["test_results"])
        partial["test_results"]["fast_green"] = "TBD"
        _write_json(reports_dir / "20260101-000000-105SEL.json", partial)
        _write_json(
            reports_dir / "20260101-000100-105SEL.json",
            _complete_metadata(phase_id="105SEL"),
        )
        result = _run([
            "trust", "--reports-dir", str(reports_dir), "--phase-id", "105SEL", "--json",
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["complete"] is True

    def test_no_report_for_phase_id_fails_clearly(self, tmp_path: Path):
        reports_dir = tmp_path / "phase-reports"
        reports_dir.mkdir()
        _write_json(reports_dir / "latest.json", _complete_metadata(phase_id="OTHER"))
        result = _run([
            "trust", "--reports-dir", str(reports_dir), "--phase-id", "NOPE",
        ])
        assert result.returncode == 2


# ── Group E: Exit codes ──────────────────────────────────────────────────────


class TestExitCodes:
    def test_complete_returns_success(self, tmp_path: Path):
        meta = _write_json(tmp_path / "meta.json", _complete_metadata())
        assert _run(["trust", "--metadata", str(meta)]).returncode == 0

    def test_partial_returns_nonzero(self, tmp_path: Path):
        raw = _complete_metadata()
        raw["test_results"] = dict(raw["test_results"])
        raw["test_results"]["fast_green"] = "TBD"
        meta = _write_json(tmp_path / "meta.json", raw)
        assert _run(["trust", "--metadata", str(meta)]).returncode == 1

    def test_invalid_returns_nonzero(self, tmp_path: Path):
        meta = _write_json(tmp_path / "meta.json", {})
        assert _run(["trust", "--metadata", str(meta)]).returncode == 1

    def test_usage_error_returns_two(self, tmp_path: Path):
        assert _run(["trust", "--metadata", str(tmp_path / "nope.json")]).returncode == 2


# ── Group F: Finalization integration (warning-only) ────────────────────────


def _finalizable_metadata(**overrides) -> dict:
    meta = {
        "phase_id": "205A",
        "files_changed_count": 1,
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "warnings"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
        ],
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": ""},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "tests_added_or_updated": "1 tests added",
        "no_go_confirmation": (
            "No runtime enforcement. No execution. No subprocess. No shell. "
            "No network. No Telegram inbound. No apply. No commit authorization. "
            "No push authorization. No rollback. No adapter execution."
        ),
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": "205B — Next Phase",
        "phase_commits": [{"hash": "abc1234500000000"}],
        "commit_attribution": "phase_owned",
    }
    meta.update(overrides)
    return meta


def _init_repo(tmp_path: Path) -> HarnessPath:
    root = HarnessPath(tmp_path)
    init_harness(root)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    return root


class TestFinalizationIntegration:
    def test_finalization_emits_trust_validation_result(
        self, tmp_path: Path, monkeypatch, capsys,
    ) -> None:
        _init_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
            json.dumps(_finalizable_metadata())
        )

        exit_code = main(["phase", "complete", "--summary", "Phase 205A: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Phase report: BLOCKED" not in output
        assert "Trust gate (105B, advisory): complete" in output

    def test_finalization_warns_on_partial_without_blocking(
        self, tmp_path: Path, monkeypatch, capsys,
    ) -> None:
        _init_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        meta = _finalizable_metadata()
        meta["validation_results"] = [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": ""},
            {"name": "fast_green", "result": "TBD", "status": ""},
        ]
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
            json.dumps(meta)
        )

        exit_code = main(["phase", "complete", "--summary", "Phase 205A: done."])
        output = capsys.readouterr().out

        # Old (95M.1) gate only checks field presence, not placeholder
        # content, so completion is not blocked by the new advisory gate.
        assert exit_code == 0
        assert "Phase report: BLOCKED" not in output
        assert "Trust gate (105B, advisory): partial" in output


# ── Group G: No-execution guards ────────────────────────────────────────────


class TestNoExecGuards:
    def test_cli_module_no_subprocess(self):
        text = Path("src/pcae/commands/phase_reports.py").read_text()
        assert "subprocess" not in text
        assert "os.system" not in text

    def test_cli_module_no_network(self):
        text = Path("src/pcae/commands/phase_reports.py").read_text()
        assert "requests." not in text
        assert "urllib" not in text
        assert "socket." not in text

    def test_cli_module_no_telegram_inbound_or_polling(self):
        text = Path("src/pcae/commands/phase_reports.py").read_text()
        assert "getUpdates" not in text
        assert "poll" not in text.lower()

    def test_adapter_pure_no_io(self):
        from pcae.core.phase_report_trust import adapt_report_for_trust_check
        src = inspect.getsource(adapt_report_for_trust_check)
        assert "open(" not in src
        assert "Path(" not in src
        assert "subprocess" not in src

    def test_trust_command_does_not_mutate_filesystem(self, tmp_path: Path):
        reports_dir = tmp_path / "phase-reports"
        reports_dir.mkdir()
        latest = _write_json(reports_dir / "latest.json", _complete_metadata())
        before = latest.read_text()
        before_listing = sorted(p.name for p in reports_dir.iterdir())

        _run(["trust", "--reports-dir", str(reports_dir), "--json"])

        after_listing = sorted(p.name for p in reports_dir.iterdir())
        assert after_listing == before_listing
        assert latest.read_text() == before
