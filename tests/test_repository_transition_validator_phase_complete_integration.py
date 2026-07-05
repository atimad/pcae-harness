"""Phase 113Y: phase-complete Repository Transition Validator integration."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath


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
        "Phase 205D — Validator Integration Fixture.\n\n"
        "Recommended next repo phase: 205E — Next Phase.\n",
        encoding="utf-8",
    )


def _metadata(**overrides) -> dict:
    data = {
        "phase_id": "205D",
        "phase_name": "Validator Integration Fixture",
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


def _complete(tmp_path: Path, monkeypatch) -> tuple[int, str]:
    monkeypatch.chdir(tmp_path)
    code = main([
        "phase",
        "complete",
        "--summary",
        "Phase 205D complete.",
        "--phase-id",
        "205D",
        "--phase-name",
        "Validator Integration Fixture",
    ])
    return code, (tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text(encoding="utf-8") if (
        tmp_path / ".pcae" / "phase-reports" / "latest.json"
    ).exists() else ""


def test_phase_complete_invokes_validator(tmp_path, monkeypatch, capsys):
    import pcae.commands.phase as phase_commands

    _init_repo(tmp_path)
    _write_metadata(tmp_path)
    calls = []
    original = phase_commands.validate_transition

    def wrapped(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(phase_commands, "validate_transition", wrapped)

    code, _ = _complete(tmp_path, monkeypatch)

    output = capsys.readouterr().out
    assert code == 0
    assert len(calls) == 1
    assert "Repository transition validator: Transition validated" in output


def test_accept_path_writes_latest_and_keeps_phase_complete_compatible(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(tmp_path)

    code, latest_json = _complete(tmp_path, monkeypatch)

    output = capsys.readouterr().out
    latest = json.loads(latest_json)
    assert code == 0
    assert "Phase report: created" in output
    assert latest["phase_id"] == "205D"
    assert latest["recommended_next_phase"] == "205E — Next Phase"


def test_reject_blocks_canonical_report_and_preserves_latest(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    reports = tmp_path / ".pcae" / "phase-reports"
    reports.mkdir(parents=True)
    old_latest = '{"phase_id": "old"}'
    (reports / "latest.json").write_text(old_latest, encoding="utf-8")
    (reports / "latest.md").write_text("# Old\n", encoding="utf-8")
    _write_metadata(tmp_path, recommended_next_phase="")

    code, _ = _complete(tmp_path, monkeypatch)

    output = capsys.readouterr().out
    assert code == 1
    assert "Repository transition validator: Transition rejected" in output
    assert "recommended_next_phase_presence" in output
    assert (reports / "latest.json").read_text(encoding="utf-8") == old_latest
    assert (reports / "latest.md").read_text(encoding="utf-8") == "# Old\n"


def test_quarantine_writes_quarantine_only_and_preserves_latest(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    reports = tmp_path / ".pcae" / "phase-reports"
    reports.mkdir(parents=True)
    old_latest = '{"phase_id": "old"}'
    (reports / "latest.json").write_text(old_latest, encoding="utf-8")
    (reports / "latest.md").write_text("# Old\n", encoding="utf-8")
    _write_metadata(
        tmp_path,
        validation_results=[
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": "passed"},
        ],
    )

    code, _ = _complete(tmp_path, monkeypatch)

    output = capsys.readouterr().out
    quarantine = reports / "quarantine"
    assert code == 1
    assert "Repository transition validator: Transition quarantined" in output
    assert "report_completeness" in output
    assert (reports / "latest.json").read_text(encoding="utf-8") == old_latest
    assert list(quarantine.glob("*.json"))
    assert list(quarantine.glob("*.md"))


def test_human_review_blocks_promotion(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(tmp_path, requires_human_review=True)

    code, _ = _complete(tmp_path, monkeypatch)

    output = capsys.readouterr().out
    assert code == 1
    assert "Repository transition validator: Human review required" in output
    assert "human_review_required" in output
    assert not (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()


def test_metadata_mismatch_rejects_deterministically(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(tmp_path, phase_id="205X")

    code, _ = _complete(tmp_path, monkeypatch)

    output = capsys.readouterr().out
    assert code == 1
    assert "metadata_consistency" in output
    assert "Transition rejected" in output


def test_execution_availability_violation_rejects(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_metadata(tmp_path, execution_availability="available")

    code, _ = _complete(tmp_path, monkeypatch)

    output = capsys.readouterr().out
    assert code == 1
    assert "no_execution_availability_unless_contracted" in output
    assert "Transition rejected" in output


def test_task_finish_command_has_no_validator_integration():
    task_command = Path("src/pcae/commands/task.py").read_text(encoding="utf-8")
    assert "repository_transition_validator" not in task_command
    assert "validate_transition" not in task_command
