from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess

import pytest

from pcae.cli import main
from pcae.core.paths import HarnessPath
from pcae.core.status import (
    GOVERNANCE_REPAIR_ADVISORY,
    KNOWN_STALE_PHRASES,
    RUNTIME_SNAPSHOT_ADVISORY,
    RUNTIME_SNAPSHOT_INSPECTION_ADVISORY,
    RUNTIME_SNAPSHOT_RESTORE_ADVISORY,
    audit_governance_coherence,
    check_project_status_coherence,
    export_runtime_snapshot,
    inspect_runtime_snapshot,
    plan_governance_repairs,
    preview_runtime_snapshot,
    preview_runtime_snapshot_restore,
)


def test_coherent_when_no_stale_phrases(tmp_path: Path) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Next\n- Add governance audit.\n"
    )
    result = check_project_status_coherence(HarnessPath(tmp_path))
    assert result.coherent
    assert result.warnings == ()


def test_warns_on_stale_pcae_end_phrase(tmp_path: Path) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Next\n- Implement `pcae end`.\n"
    )
    result = check_project_status_coherence(HarnessPath(tmp_path))
    assert not result.coherent
    assert len(result.warnings) == 1
    assert "pcae end" in result.warnings[0].message
    assert result.warnings[0].document == "PROJECT_STATUS.md"


def test_warns_on_all_known_stale_phrases(tmp_path: Path) -> None:
    content = "# Status\n" + "\n".join(f"- {p}" for p in KNOWN_STALE_PHRASES)
    (tmp_path / "PROJECT_STATUS.md").write_text(content)
    result = check_project_status_coherence(HarnessPath(tmp_path))
    assert len(result.warnings) == len(KNOWN_STALE_PHRASES)


def test_missing_file_returns_warning(tmp_path: Path) -> None:
    result = check_project_status_coherence(HarnessPath(tmp_path))
    assert not result.coherent
    assert any("not found" in w.message for w in result.warnings)


def test_to_dict_coherent(tmp_path: Path) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text("# Clean status\n")
    result = check_project_status_coherence(HarnessPath(tmp_path))
    d = result.to_dict()
    assert d["coherent"] is True
    assert d["warning_count"] == 0
    assert d["warnings"] == []


def test_to_dict_with_warnings(tmp_path: Path) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text("- Implement `pcae end`\n")
    result = check_project_status_coherence(HarnessPath(tmp_path))
    d = result.to_dict()
    assert d["coherent"] is False
    assert d["warning_count"] >= 1
    assert all("document" in w and "message" in w for w in d["warnings"])


def test_cli_status_coherence_clean(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text("# Status\n\n## Next\n- Governance audit.\n")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["status", "coherence"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "coherent" in output


def test_cli_status_coherence_warns(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text("## Next\n- Implement `pcae end`.\n")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["status", "coherence"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "warning" in output


def test_cli_status_coherence_json(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text("# Clean\n")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["status", "coherence", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["coherent"] is True
    assert data["warning_count"] == 0
    assert data["warnings"] == []


def test_governance_audit_valid_when_governance_artifacts_align(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    assert result.valid
    assert result.summary.status == "valid"
    assert result.summary.failed_count == 0
    assert result.summary.warning_count == 0
    assert {check.name for check in result.checks} == {
        "active_task",
        "agent_registry",
        "policy_configuration",
        "project_status_current_phase",
        "project_status_next",
        "provenance_history",
        "session_continuity",
    }


def test_governance_audit_warns_on_stale_roadmap_references(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(
        tmp_path,
        next_item="Full governance audit: `pcae governance audit` command.",
    )
    result = audit_governance_coherence(HarnessPath(tmp_path))
    assert not result.valid
    assert result.summary.status == "warnings"
    assert result.summary.failed_count == 0
    assert result.summary.warning_count == 1
    assert result.warnings[0].document == "PROJECT_STATUS.md"


def test_governance_audit_reports_missing_required_artifacts(tmp_path: Path) -> None:
    result = audit_governance_coherence(HarnessPath(tmp_path))
    assert not result.valid
    assert result.summary.status == "invalid"
    failed = {check.name for check in result.checks if not check.passed}
    assert "project_status_current_phase" in failed
    assert "project_status_next" in failed
    assert "active_task" in failed
    assert "session_continuity" in failed
    assert "provenance_history" in failed


def test_cli_governance_audit_human(tmp_path: Path, monkeypatch, capsys) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "audit"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance coherence audit" in output
    assert "Overall status: valid" in output
    assert "Audit checks:" in output
    assert "Governance coherence summary:" in output


def test_cli_governance_audit_json(tmp_path: Path, monkeypatch, capsys) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "audit", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["summary"]["status"] == "valid"
    assert data["warnings"] == []
    assert all("name" in check and "passed" in check for check in data["checks"])


def test_governance_repair_plan_clean_repo_has_no_repairs(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = plan_governance_repairs(HarnessPath(tmp_path))
    assert result.repairable
    assert result.detected_issues == ()
    assert result.proposed_repairs == ()
    assert result.advisory == GOVERNANCE_REPAIR_ADVISORY
    assert any("Dry-run only" in note for note in result.safety_notes)


def test_governance_repair_plan_recommends_repairs_for_stale_roadmap(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(
        tmp_path,
        next_item="Full governance audit: `pcae governance audit` command.",
    )
    result = plan_governance_repairs(HarnessPath(tmp_path))
    assert result.repairable
    assert len(result.detected_issues) == 1
    assert "synchronize PROJECT_STATUS.md roadmap guidance" in result.proposed_repairs
    assert 'refresh stale "Next" references' in result.proposed_repairs
    assert "refresh governance summaries" in result.proposed_repairs


def test_governance_repair_plan_recommends_repairs_for_failed_checks(
    tmp_path: Path,
) -> None:
    result = plan_governance_repairs(HarnessPath(tmp_path))
    assert result.repairable
    assert any("project_status_current_phase" in issue for issue in result.detected_issues)
    assert "synchronize PROJECT_STATUS.md roadmap guidance" in result.proposed_repairs
    assert "refresh governance summaries" in result.proposed_repairs


def test_cli_governance_repair_human(tmp_path: Path, monkeypatch, capsys) -> None:
    write_minimal_governance_artifacts(
        tmp_path,
        next_item="Full governance audit: `pcae governance audit` command.",
    )
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "repair", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance repair planning preview" in output
    assert "Overall repairability status: repairable" in output
    assert "Detected issues:" in output
    assert "Proposed repairs:" in output
    assert "Repair safety notes:" in output
    assert GOVERNANCE_REPAIR_ADVISORY in output


def test_cli_governance_repair_json(tmp_path: Path, monkeypatch, capsys) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "repair", "--dry-run", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["repairable"] is True
    assert data["detected_issues"] == []
    assert data["proposed_repairs"] == []
    assert data["safety_notes"]
    assert data["advisory"] == GOVERNANCE_REPAIR_ADVISORY


def test_runtime_snapshot_preview_includes_governed_runtime_sections(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    result = preview_runtime_snapshot(HarnessPath(tmp_path))
    assert "active task" in result.included_sections
    assert "agent lock state" in result.included_sections
    assert "orchestration policy summary" in result.included_sections
    assert result.advisory == RUNTIME_SNAPSHOT_ADVISORY
    assert result.runtime_summary["active_task"]["id"] == "20260527-1200-test"
    assert result.runtime_summary["provenance_event_count"] == 1
    assert result.runtime_summary["latest_provenance_event"]["event_type"] == "test_event"
    assert result.runtime_summary["registered_agents"]
    assert result.runtime_summary["workflow_orchestration_metadata"]["available"] is True


def test_runtime_snapshot_preview_json_shape(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    result = preview_runtime_snapshot(HarnessPath(tmp_path)).to_dict()
    assert "snapshot_ready" in result
    assert "included_sections" in result
    assert "portability_notes" in result
    assert "safety_notes" in result
    assert result["advisory"] == RUNTIME_SNAPSHOT_ADVISORY
    assert "runtime_summary" in result


def test_cli_runtime_snapshot_human(tmp_path: Path, monkeypatch, capsys) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "--preview"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance runtime snapshot preview" in output
    assert "Snapshot readiness:" in output
    assert "Included runtime sections:" in output
    assert "Portability notes:" in output
    assert "Safety notes:" in output
    assert RUNTIME_SNAPSHOT_ADVISORY in output


def test_cli_runtime_snapshot_json(tmp_path: Path, monkeypatch, capsys) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "--preview", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert "snapshot_ready" in data
    assert data["included_sections"]
    assert data["portability_notes"]
    assert data["safety_notes"]
    assert data["advisory"] == RUNTIME_SNAPSHOT_ADVISORY
    assert data["runtime_summary"]["provenance_event_count"] == 1


def test_runtime_snapshot_export_writes_portable_json(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    result = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 12, 30, 45, tzinfo=timezone.utc),
    )
    assert result.export_path == Path(".pcae/runtime-snapshots/runtime-snapshot-20260527-123045.json")
    target = tmp_path / result.export_path
    assert target.is_file()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["exported_at"] == "2026-05-27T12:30:45+00:00"
    assert data["active_task"]["id"] == "20260527-1200-test"
    assert data["provenance_event_count"] == 1
    assert data["latest_provenance_event"]["event_type"] == "test_event"
    assert data["governance_check_status"] in {"passed", "failed"}


def test_cli_runtime_snapshot_export_human(tmp_path: Path, monkeypatch, capsys) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "export"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance runtime snapshot export" in output
    assert "Export path: .pcae/runtime-snapshots/runtime-snapshot-" in output
    assert "Snapshot readiness:" in output
    assert list((tmp_path / ".pcae" / "runtime-snapshots").glob("runtime-snapshot-*.json"))


def test_cli_runtime_snapshot_export_json(tmp_path: Path, monkeypatch, capsys) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "export", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["export_path"].startswith(".pcae/runtime-snapshots/runtime-snapshot-")
    assert "exported_at" in data
    assert "snapshot_ready" in data
    assert data["snapshot"]["active_task"]["id"] == "20260527-1200-test"
    assert (tmp_path / data["export_path"]).is_file()


def test_runtime_snapshot_exports_are_git_ignored(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    (tmp_path / ".pcae" / ".gitignore").write_text(
        "runtime-snapshots/\n",
        encoding="utf-8",
    )
    result = export_runtime_snapshot(HarnessPath(tmp_path))
    completed = subprocess.run(
        ["git", "check-ignore", result.export_path.as_posix()],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == result.export_path.as_posix()


def test_runtime_snapshot_inspect_reads_exported_snapshot(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 13, 15, 0, tzinfo=timezone.utc),
    )
    result = inspect_runtime_snapshot(HarnessPath(tmp_path), export.export_path)
    assert result.valid
    assert result.exported_at == "2026-05-27T13:15:00+00:00"
    assert "active task" in result.included_sections
    assert "latest provenance event" in result.included_sections
    assert result.runtime_summary["active_task"]["id"] == "20260527-1200-test"
    assert result.runtime_summary["provenance_event_count"] == 1
    assert result.advisory == RUNTIME_SNAPSHOT_INSPECTION_ADVISORY


def test_runtime_snapshot_inspect_reports_schema_metadata_when_available(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    data["schema_version"] = "runtime-snapshot.v1"
    target.write_text(json.dumps(data), encoding="utf-8")
    result = inspect_runtime_snapshot(HarnessPath(tmp_path), export.export_path)
    assert "snapshot schema/version metadata" in result.included_sections
    assert result.runtime_summary["schema_version"] == "runtime-snapshot.v1"


def test_runtime_snapshot_inspect_is_read_only(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    before = target.read_text(encoding="utf-8")
    inspect_runtime_snapshot(HarnessPath(tmp_path), export.export_path)
    after = target.read_text(encoding="utf-8")
    assert after == before


def test_cli_runtime_snapshot_inspect_human(tmp_path: Path, monkeypatch, capsys) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "inspect", export.export_path.as_posix()])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance runtime snapshot inspection" in output
    assert "Snapshot validity: valid" in output
    assert "Exported timestamp:" in output
    assert "Included sections:" in output
    assert "Portability notes:" in output
    assert "Safety notes:" in output
    assert RUNTIME_SNAPSHOT_INSPECTION_ADVISORY in output


def test_cli_runtime_snapshot_inspect_json(tmp_path: Path, monkeypatch, capsys) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)
    exit_code = main(
        ["runtime", "snapshot", "inspect", export.export_path.as_posix(), "--json"]
    )
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["exported_at"] == export.exported_at
    assert data["included_sections"]
    assert data["runtime_summary"]["active_task"]["id"] == "20260527-1200-test"
    assert data["portability_notes"]
    assert data["safety_notes"]
    assert data["advisory"] == RUNTIME_SNAPSHOT_INSPECTION_ADVISORY


def test_cli_runtime_snapshot_inspect_invalid_json_fails(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not-json", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "inspect", "invalid.json"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Invalid runtime snapshot JSON" in output


def test_cli_runtime_snapshot_inspect_missing_fields_fails(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"exported_at": "2026-05-27T00:00:00+00:00"}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "inspect", "invalid.json"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "missing required field" in output


def test_runtime_snapshot_restore_preview_summarizes_would_restore(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    result = preview_runtime_snapshot_restore(HarnessPath(tmp_path), export.export_path)
    assert result.valid
    assert result.restore_preview["active_task"]["id"] == "20260527-1200-test"
    assert result.restore_preview["provenance_summary"]["event_count"] == 1
    assert "active task metadata" in result.would_restore
    assert "agent lock file" in result.would_not_restore
    assert result.advisory == RUNTIME_SNAPSHOT_RESTORE_ADVISORY


def test_runtime_snapshot_restore_preview_is_read_only(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    before = target.read_text(encoding="utf-8")
    preview_runtime_snapshot_restore(HarnessPath(tmp_path), export.export_path)
    after = target.read_text(encoding="utf-8")
    assert after == before


def test_cli_runtime_snapshot_restore_human(tmp_path: Path, monkeypatch, capsys) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)
    exit_code = main(
        ["runtime", "snapshot", "restore", export.export_path.as_posix(), "--dry-run"]
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance runtime snapshot restore preview" in output
    assert "Restore preview status: ready" in output
    assert "Snapshot validity: valid" in output
    assert "Sections that would be restored:" in output
    assert "Sections that would NOT be restored yet:" in output
    assert "Safety notes:" in output
    assert RUNTIME_SNAPSHOT_RESTORE_ADVISORY in output


def test_cli_runtime_snapshot_restore_json(tmp_path: Path, monkeypatch, capsys) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)
    exit_code = main(
        [
            "runtime",
            "snapshot",
            "restore",
            export.export_path.as_posix(),
            "--dry-run",
            "--json",
        ]
    )
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["restore_preview"]["active_task"]["id"] == "20260527-1200-test"
    assert "active task metadata" in data["would_restore"]
    assert "agent lock file" in data["would_not_restore"]
    assert data["safety_notes"]
    assert data["advisory"] == RUNTIME_SNAPSHOT_RESTORE_ADVISORY


def test_cli_runtime_snapshot_restore_invalid_snapshot_fails(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "restore", "invalid.json", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Invalid runtime snapshot" in output


def initialize_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)


def write_minimal_governance_artifacts(
    tmp_path: Path,
    next_item: str = "Implement next governed phase.",
) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n"
        "## Current Phase\n\n"
        "Phase Test.\n\n"
        "## Next\n\n"
        f"- {next_item}\n",
        encoding="utf-8",
    )
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True)
    (active_dir / "20260527-1200-test.md").write_text(
        "# Task Contract\n\n"
        "## Task ID\n\n"
        "20260527-1200-test\n\n"
        "## Title\n\n"
        "Test task\n\n"
        "## Status\n\n"
        "active\n",
        encoding="utf-8",
    )
    pcae_dir = tmp_path / ".pcae"
    pcae_dir.mkdir()
    (pcae_dir / "session.json").write_text(
        json.dumps(
            {
                "active_task": {"id": "20260527-1200-test"},
                "current_objective": "Preview governed runtime snapshot.",
                "next_recommended_step": "Run governance checks.",
            }
        ),
        encoding="utf-8",
    )
    (pcae_dir / "provenance-history.json").write_text(
        json.dumps(
            [
                {
                    "active_task": {"id": "20260527-1200-test", "title": "Test task"},
                    "agent_id": "codex-local",
                    "event_type": "test_event",
                    "git_branch": "main",
                    "summary": "Test provenance event.",
                    "timestamp": "2026-05-27T12:00:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )
