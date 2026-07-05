"""Phase 113Z: task-finish Repository Transition Validator integration."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.repository_transition_validator import STRUCTURAL_INVARIANTS
from pcae.core.tasks import create_task_contract


def _init_repo(tmp_path: Path) -> HarnessPath:
    root = HarnessPath(tmp_path)
    init_harness(root)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
    return root


def _new_task(root: HarnessPath, title: str = "Phase 205Z: Task Finish Validator Fixture") -> None:
    create_task_contract(
        root,
        title=title,
        goal="verify task-finish validator integration",
        mode="implementation",
        allowed_files=[".pcae/**", "tasks/active/**", "tasks/done/**"],
        allowed_zones=["config", "tasks"],
    )


def _write_metadata(tmp_path: Path, **overrides) -> dict:
    meta = {
        "phase_id": "205Z",
        "phase_name": "Task Finish Validator Fixture",
        "status": "completed",
        "summary": "Task finish validator integration fixture.",
        "files_changed_count": 2,
        "tests_added_or_updated": "4 tests added",
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "clean"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
        ],
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": "passed"},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "no_go_confirmation": (
            "No notification integration. No push-check integration. No execution. "
            "No authorization. No Permission Broker enforcement. No Telegram inbound. "
            "No REST. No Web UI. No Dashboard. No package publication. "
            "No lifecycle command beyond task finish."
        ),
        "commit_attribution": "phase_owned",
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": "206A - Next Phase",
        "execution_availability": "unavailable",
    }
    meta.update(overrides)
    path = tmp_path / ".pcae" / "phase-completion-metadata.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def _finish(tmp_path: Path, monkeypatch, *, json_output: bool = False) -> int:
    monkeypatch.chdir(tmp_path)
    args = ["task", "finish", "--staged-file-aware", "--commit", "Smoke finish commit"]
    if json_output:
        args.append("--json")
    return main(args)


def _seed_latest(tmp_path: Path) -> tuple[str, str]:
    reports = tmp_path / ".pcae" / "phase-reports"
    reports.mkdir(parents=True, exist_ok=True)
    old_json = '{"phase_id": "old"}'
    old_md = "# Old\n"
    (reports / "latest.json").write_text(old_json, encoding="utf-8")
    (reports / "latest.md").write_text(old_md, encoding="utf-8")
    return old_json, old_md


def test_task_finish_invokes_repository_transition_validator(tmp_path, monkeypatch, capsys):
    import pcae.core.repository_transition_integration as integration

    root = _init_repo(tmp_path)
    _new_task(root)
    _write_metadata(tmp_path)
    calls = []
    original = integration.validate_transition

    def wrapped(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(integration, "validate_transition", wrapped)

    code = _finish(tmp_path, monkeypatch)
    output = capsys.readouterr().out

    assert code == 0
    assert len(calls) == 1
    transition = calls[0][0][1]
    assert transition.kind.value == "finish_task"
    assert "Repository transition validator: Transition accepted" in output


def test_task_finish_accept_path_writes_latest_and_remains_compatible(tmp_path, monkeypatch, capsys):
    root = _init_repo(tmp_path)
    _new_task(root)
    _write_metadata(tmp_path)

    code = _finish(tmp_path, monkeypatch)
    output = capsys.readouterr().out
    latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text(encoding="utf-8"))

    assert code == 0
    assert "Finished task:" in output
    assert "Report trust: complete" in output
    assert latest["phase_id"] == "205Z"
    assert latest["recommended_next_phase"] == "206A - Next Phase"


def test_task_finish_reject_blocks_latest_when_recommended_next_missing(tmp_path, monkeypatch, capsys):
    root = _init_repo(tmp_path)
    _new_task(root)
    old_json, old_md = _seed_latest(tmp_path)
    _write_metadata(tmp_path, recommended_next_phase="")

    code = _finish(tmp_path, monkeypatch)
    output = capsys.readouterr().out
    reports = tmp_path / ".pcae" / "phase-reports"

    assert code == 1
    assert "Repository transition validator: Transition rejected" in output
    assert "recommended_next_phase_presence" in output
    assert (reports / "latest.json").read_text(encoding="utf-8") == old_json
    assert (reports / "latest.md").read_text(encoding="utf-8") == old_md


def test_task_finish_blocks_stale_phase_completion_metadata(tmp_path, monkeypatch, capsys):
    root = _init_repo(tmp_path)
    _new_task(root, title="Phase 205Z: Task Finish Validator Fixture")
    old_json, old_md = _seed_latest(tmp_path)
    _write_metadata(tmp_path, phase_id="205Y", phase_name="Stale Metadata")

    code = _finish(tmp_path, monkeypatch)
    output = capsys.readouterr().out
    reports = tmp_path / ".pcae" / "phase-reports"

    assert code == 1
    assert "metadata_consistency" in output
    assert "phase_identity_consistency" in output
    assert (reports / "latest.json").read_text(encoding="utf-8") == old_json
    assert (reports / "latest.md").read_text(encoding="utf-8") == old_md


def test_task_finish_quarantine_writes_quarantine_only_for_partial_report(tmp_path, monkeypatch, capsys):
    root = _init_repo(tmp_path)
    _new_task(root)
    old_json, old_md = _seed_latest(tmp_path)
    _write_metadata(
        tmp_path,
        validation_results=[
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": "passed"},
        ],
    )

    code = _finish(tmp_path, monkeypatch)
    output = capsys.readouterr().out
    reports = tmp_path / ".pcae" / "phase-reports"

    assert code == 1
    assert "Repository transition validator: Transition quarantined" in output
    assert "report_completeness" in output
    assert (reports / "latest.json").read_text(encoding="utf-8") == old_json
    assert (reports / "latest.md").read_text(encoding="utf-8") == old_md
    assert list((reports / "quarantine").glob("*.json"))
    assert list((reports / "quarantine").glob("*.md"))


def test_task_finish_human_review_blocks_promotion(tmp_path, monkeypatch, capsys):
    root = _init_repo(tmp_path)
    _new_task(root)
    _write_metadata(tmp_path, requires_human_review=True)

    code = _finish(tmp_path, monkeypatch)
    output = capsys.readouterr().out

    assert code == 1
    assert "Repository transition validator: Human review required" in output
    assert "human_review_required" in output
    assert not (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()


def test_task_finish_rejects_execution_availability_violation(tmp_path, monkeypatch, capsys):
    root = _init_repo(tmp_path)
    _new_task(root)
    _write_metadata(tmp_path, execution_availability="available")

    code = _finish(tmp_path, monkeypatch)
    output = capsys.readouterr().out

    assert code == 1
    assert "no_execution_availability_unless_contracted" in output
    assert "Transition rejected" in output


def test_task_finish_json_exposes_validator_rejection(tmp_path, monkeypatch, capsys):
    root = _init_repo(tmp_path)
    _new_task(root)
    _seed_latest(tmp_path)
    _write_metadata(tmp_path, recommended_next_phase="")

    code = _finish(tmp_path, monkeypatch, json_output=True)
    data = json.loads(capsys.readouterr().out)

    assert code == 1
    assert data["repository_transition_validator"]["verdict"] == "reject"
    assert "recommended_next_phase_presence" in data["repository_transition_validator"]["violations"]
    assert data["notification_dispatch"]["status"] == "skipped_validator"


def test_phase_complete_and_task_finish_use_same_shared_transition_adapter():
    phase_command = Path("src/pcae/commands/phase.py").read_text(encoding="utf-8")
    task_command = Path("src/pcae/commands/task.py").read_text(encoding="utf-8")
    assert "validate_phase_report_transition" in phase_command
    assert "validate_phase_report_transition" in task_command
    assert "resolve_canonical_phase_identity" in phase_command
    assert "resolve_canonical_phase_identity" in task_command


def test_no_notification_or_push_check_command_integration_added():
    notifications_command = Path("src/pcae/commands/notifications.py").read_text(encoding="utf-8")
    push_command = Path("src/pcae/commands/push.py").read_text(encoding="utf-8")
    assert "repository_transition_validator" not in notifications_command
    assert "validate_phase_report_transition" not in notifications_command
    assert "repository_transition_validator" not in push_command
    assert "validate_phase_report_transition" not in push_command


def test_stale_commit_lineage_remains_outside_current_invariant_set():
    invariant_names = {invariant.name for invariant in STRUCTURAL_INVARIANTS}
    assert "commit_lineage" not in invariant_names
