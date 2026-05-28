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
    RESTORE_SAFETY_VALIDATION_ADVISORY,
    RUNTIME_SNAPSHOT_ADVISORY,
    RUNTIME_SNAPSHOT_COMPATIBILITY_ADVISORY,
    RUNTIME_SNAPSHOT_INSPECTION_ADVISORY,
    RUNTIME_SNAPSHOT_LINEAGE_ADVISORY,
    RUNTIME_SNAPSHOT_MANIFEST_ADVISORY,
    RUNTIME_SNAPSHOT_RETENTION_ADVISORY,
    RUNTIME_SNAPSHOT_RESTORE_ADVISORY,
    analyze_runtime_snapshot_compatibility,
    audit_governance_coherence,
    build_runtime_snapshot_lineage,
    build_runtime_snapshot_manifest,
    check_project_status_coherence,
    export_runtime_snapshot,
    inspect_runtime_snapshot,
    plan_governance_repairs,
    plan_runtime_snapshot_retention,
    preview_runtime_snapshot,
    preview_runtime_snapshot_restore,
    validate_runtime_snapshot_restore_safety,
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
        "artifact_sync_drift",
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
    assert data["snapshot_schema_version"] == 1
    assert data["snapshot_kind"] == "pcae-runtime-snapshot"
    assert data["exported_by_version"].startswith("0.")
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
    assert "Schema version: 1" in output
    assert "Snapshot kind: pcae-runtime-snapshot" in output
    assert "Compatibility status: compatible" in output
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
    assert data["snapshot_schema_version"] == 1
    assert data["snapshot_kind"] == "pcae-runtime-snapshot"
    assert data["exported_by_version"].startswith("0.")
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
    assert result.snapshot_schema_version == 1
    assert result.snapshot_kind == "pcae-runtime-snapshot"
    assert result.compatibility_status == "compatible"
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
    result = inspect_runtime_snapshot(HarnessPath(tmp_path), export.export_path)
    assert "snapshot schema/version metadata" in result.included_sections
    assert result.runtime_summary["snapshot_schema_version"] == 1
    assert result.runtime_summary["snapshot_kind"] == "pcae-runtime-snapshot"


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
    assert "Schema version: 1" in output
    assert "Snapshot kind: pcae-runtime-snapshot" in output
    assert "Compatibility status: compatible" in output
    assert "Compatibility notes:" in output
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
    assert data["snapshot_schema_version"] == 1
    assert data["snapshot_kind"] == "pcae-runtime-snapshot"
    assert data["compatibility_status"] == "compatible"
    assert data["compatibility_notes"]
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
    assert result.snapshot_schema_version == 1
    assert result.snapshot_kind == "pcae-runtime-snapshot"
    assert result.compatibility_status == "compatible"
    assert result.compatibility_notes
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
    assert "Schema version: 1" in output
    assert "Snapshot kind: pcae-runtime-snapshot" in output
    assert "Compatibility status: compatible" in output
    assert "Compatibility notes:" in output
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
    assert data["snapshot_schema_version"] == 1
    assert data["snapshot_kind"] == "pcae-runtime-snapshot"
    assert data["compatibility_status"] == "compatible"
    assert data["compatibility_notes"]
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


def test_runtime_snapshot_inspect_unsupported_schema_warns_clearly(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    data["snapshot_schema_version"] = 999
    target.write_text(json.dumps(data), encoding="utf-8")
    result = inspect_runtime_snapshot(HarnessPath(tmp_path), export.export_path)
    assert result.valid
    assert result.compatibility_status == "incompatible"
    assert any("Unsupported runtime snapshot schema version" in note for note in result.compatibility_notes)


def test_runtime_snapshot_restore_preview_blocks_incompatible_schema(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    data["snapshot_schema_version"] = 999
    target.write_text(json.dumps(data), encoding="utf-8")
    result = preview_runtime_snapshot_restore(HarnessPath(tmp_path), export.export_path)
    assert not result.valid
    assert result.compatibility_status == "incompatible"
    assert result.would_restore == ()
    assert "all runtime state because the snapshot is not compatible" in result.would_not_restore


def test_runtime_snapshot_inspect_unknown_kind_warns_clearly(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    data["snapshot_kind"] = "unknown-kind"
    target.write_text(json.dumps(data), encoding="utf-8")
    result = inspect_runtime_snapshot(HarnessPath(tmp_path), export.export_path)
    assert result.compatibility_status == "incompatible"
    assert any("Unknown snapshot kind" in note for note in result.compatibility_notes)


def test_runtime_snapshot_compatibility_reports_supported_matrix(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    result = analyze_runtime_snapshot_compatibility(HarnessPath(tmp_path), export.export_path)
    assert result.compatible
    assert result.support_level == "supported"
    assert result.snapshot_kind == "pcae-runtime-snapshot"
    assert result.snapshot_schema_version == 1
    assert result.exported_by_version.startswith("0.")
    assert {check.name for check in result.compatibility_checks} == {
        "exported_by_version_visibility",
        "future_version_warning_support",
        "required_runtime_sections_presence",
        "schema_version_compatibility",
        "snapshot_kind_compatibility",
        "unknown_snapshot_kind_handling",
    }
    assert result.compatibility_warnings == ()
    assert result.advisory == RUNTIME_SNAPSHOT_COMPATIBILITY_ADVISORY


def test_cli_runtime_snapshot_compatibility_human(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "compatibility", export.export_path.as_posix()])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance runtime snapshot compatibility" in output
    assert "Compatibility status: compatible" in output
    assert "Snapshot kind: pcae-runtime-snapshot" in output
    assert "Schema version: 1" in output
    assert "Exported by version:" in output
    assert "Compatibility checks:" in output
    assert "Compatibility warnings:" in output
    assert "Support level: supported" in output
    assert RUNTIME_SNAPSHOT_COMPATIBILITY_ADVISORY in output


def test_cli_runtime_snapshot_compatibility_json(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)
    exit_code = main(
        ["runtime", "snapshot", "compatibility", export.export_path.as_posix(), "--json"]
    )
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["compatible"] is True
    assert data["support_level"] == "supported"
    assert data["snapshot_kind"] == "pcae-runtime-snapshot"
    assert data["snapshot_schema_version"] == 1
    assert data["exported_by_version"].startswith("0.")
    assert data["compatibility_checks"]
    assert data["compatibility_warnings"] == []
    assert data["advisory"] == RUNTIME_SNAPSHOT_COMPATIBILITY_ADVISORY


def test_runtime_snapshot_compatibility_warns_on_future_exporter(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    data["exported_by_version"] = "999.0.0"
    target.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_runtime_snapshot_compatibility(HarnessPath(tmp_path), export.export_path)
    assert not result.compatible
    assert result.support_level == "partially-supported"
    assert any("newer than current PCAE runtime" in warning for warning in result.compatibility_warnings)


def test_runtime_snapshot_compatibility_unsupported_schema_is_deterministic(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    data["snapshot_schema_version"] = 999
    target.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_runtime_snapshot_compatibility(HarnessPath(tmp_path), export.export_path)
    assert not result.compatible
    assert result.support_level == "unsupported"
    assert any("Unsupported runtime snapshot schema version" in warning for warning in result.compatibility_warnings)


def test_runtime_snapshot_compatibility_unknown_kind_is_unsupported(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    data["snapshot_kind"] = "unknown-kind"
    target.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_runtime_snapshot_compatibility(HarnessPath(tmp_path), export.export_path)
    assert not result.compatible
    assert result.support_level == "unsupported"
    assert any("Unknown snapshot kind" in warning for warning in result.compatibility_warnings)


def test_runtime_snapshot_compatibility_missing_sections_is_partial(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    del data["active_task"]
    target.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_runtime_snapshot_compatibility(HarnessPath(tmp_path), export.export_path)
    assert not result.compatible
    assert result.support_level == "partially-supported"
    assert any("Missing required runtime section" in warning for warning in result.compatibility_warnings)


def test_runtime_snapshot_compatibility_is_read_only(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    before = target.read_text(encoding="utf-8")
    analyze_runtime_snapshot_compatibility(HarnessPath(tmp_path), export.export_path)
    after = target.read_text(encoding="utf-8")
    assert after == before


def test_runtime_snapshot_manifest_empty_directory_reports_zero(tmp_path: Path) -> None:
    result = build_runtime_snapshot_manifest(HarnessPath(tmp_path))
    assert result.snapshot_count == 0
    assert result.latest_snapshot is None
    assert result.manifest_entries == ()
    assert result.compatibility_summary == {
        "compatible": 0,
        "incompatible": 0,
        "supported": 0,
        "partially-supported": 0,
        "unsupported": 0,
    }
    assert result.advisory == RUNTIME_SNAPSHOT_MANIFEST_ADVISORY


def test_runtime_snapshot_manifest_indexes_snapshots_deterministically(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    older = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 8, 0, 0, tzinfo=timezone.utc),
    )
    newer = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 9, 0, 0, tzinfo=timezone.utc),
    )
    result = build_runtime_snapshot_manifest(HarnessPath(tmp_path))
    assert result.snapshot_count == 2
    assert [entry.filename for entry in result.manifest_entries] == [
        newer.export_path.name,
        older.export_path.name,
    ]
    assert result.latest_snapshot is not None
    assert result.latest_snapshot["filename"] == newer.export_path.name
    assert all(entry.compatibility_status == "compatible" for entry in result.manifest_entries)
    assert all(entry.support_level == "supported" for entry in result.manifest_entries)
    assert result.compatibility_summary["compatible"] == 2
    assert result.compatibility_summary["supported"] == 2


def test_runtime_snapshot_manifest_includes_compatibility_metadata(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    data["snapshot_schema_version"] = 999
    target.write_text(json.dumps(data), encoding="utf-8")
    result = build_runtime_snapshot_manifest(HarnessPath(tmp_path))
    assert result.snapshot_count == 1
    entry = result.manifest_entries[0]
    assert entry.filename == export.export_path.name
    assert entry.exported_at == export.exported_at
    assert entry.snapshot_kind == "pcae-runtime-snapshot"
    assert entry.snapshot_schema_version == 999
    assert entry.exported_by_version.startswith("0.")
    assert entry.compatibility_status == "incompatible"
    assert entry.support_level == "unsupported"
    assert result.compatibility_summary["incompatible"] == 1
    assert result.compatibility_summary["unsupported"] == 1


def test_cli_runtime_snapshot_manifest_human(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export_runtime_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "manifest"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance runtime snapshot manifest" in output
    assert "Snapshot count: 1" in output
    assert "Latest snapshot: runtime-snapshot-" in output
    assert "Manifest entries:" in output
    assert "Compatibility summary:" in output
    assert "supported: 1" in output
    assert RUNTIME_SNAPSHOT_MANIFEST_ADVISORY in output


def test_cli_runtime_snapshot_manifest_json(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "manifest", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["snapshot_count"] == 1
    assert data["latest_snapshot"]["filename"] == export.export_path.name
    assert data["manifest_entries"][0]["filename"] == export.export_path.name
    assert data["manifest_entries"][0]["compatibility_status"] == "compatible"
    assert data["manifest_entries"][0]["support_level"] == "supported"
    assert data["compatibility_summary"]["compatible"] == 1
    assert data["compatibility_summary"]["supported"] == 1
    assert data["advisory"] == RUNTIME_SNAPSHOT_MANIFEST_ADVISORY


def test_runtime_snapshot_manifest_is_read_only(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(HarnessPath(tmp_path))
    target = tmp_path / export.export_path
    before = target.read_text(encoding="utf-8")
    build_runtime_snapshot_manifest(HarnessPath(tmp_path))
    after = target.read_text(encoding="utf-8")
    assert after == before


def test_runtime_snapshot_retention_keeps_latest_five_by_default(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    exports = [
        export_runtime_snapshot(
            HarnessPath(tmp_path),
            exported_at=datetime(2026, 5, 27, hour, 0, 0, tzinfo=timezone.utc),
        )
        for hour in range(1, 8)
    ]
    result = plan_runtime_snapshot_retention(HarnessPath(tmp_path))
    assert result.snapshot_count == 7
    assert result.keep_count == 5
    assert result.prune_candidate_count == 2
    assert [entry.filename for entry in result.keep] == [
        export.export_path.name for export in reversed(exports[2:])
    ]
    assert [entry.filename for entry in result.prune_candidates] == [
        exports[1].export_path.name,
        exports[0].export_path.name,
    ]
    assert result.advisory == RUNTIME_SNAPSHOT_RETENTION_ADVISORY


def test_runtime_snapshot_retention_with_fewer_than_five_has_no_candidates(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    for hour in range(1, 4):
        export_runtime_snapshot(
            HarnessPath(tmp_path),
            exported_at=datetime(2026, 5, 27, hour, 0, 0, tzinfo=timezone.utc),
        )
    result = plan_runtime_snapshot_retention(HarnessPath(tmp_path))
    assert result.snapshot_count == 3
    assert result.keep_count == 3
    assert result.prune_candidate_count == 0
    assert len(result.keep) == 3
    assert result.prune_candidates == ()


def test_cli_runtime_snapshot_retention_human(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    for hour in range(1, 7):
        export_runtime_snapshot(
            HarnessPath(tmp_path),
            exported_at=datetime(2026, 5, 27, hour, 0, 0, tzinfo=timezone.utc),
        )
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "retention", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance runtime snapshot retention preview" in output
    assert "Snapshot count: 6" in output
    assert "Keep count: 5" in output
    assert "Prune candidate count: 1" in output
    assert "Snapshots to keep:" in output
    assert "Prune candidates:" in output
    assert RUNTIME_SNAPSHOT_RETENTION_ADVISORY in output


def test_cli_runtime_snapshot_retention_json(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    exports = [
        export_runtime_snapshot(
            HarnessPath(tmp_path),
            exported_at=datetime(2026, 5, 27, hour, 0, 0, tzinfo=timezone.utc),
        )
        for hour in range(1, 7)
    ]
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "retention", "--dry-run", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["snapshot_count"] == 6
    assert data["keep_count"] == 5
    assert data["prune_candidate_count"] == 1
    assert [entry["filename"] for entry in data["keep"]] == [
        export.export_path.name for export in reversed(exports[1:])
    ]
    assert data["prune_candidates"][0]["filename"] == exports[0].export_path.name
    assert data["advisory"] == RUNTIME_SNAPSHOT_RETENTION_ADVISORY


def test_runtime_snapshot_retention_is_read_only(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    exports = [
        export_runtime_snapshot(
            HarnessPath(tmp_path),
            exported_at=datetime(2026, 5, 27, hour, 0, 0, tzinfo=timezone.utc),
        )
        for hour in range(1, 7)
    ]
    before = {
        export.export_path.name: (tmp_path / export.export_path).read_text(encoding="utf-8")
        for export in exports
    }
    plan_runtime_snapshot_retention(HarnessPath(tmp_path))
    after = {
        export.export_path.name: (tmp_path / export.export_path).read_text(encoding="utf-8")
        for export in exports
    }
    assert after == before
    assert sorted(path.name for path in (tmp_path / ".pcae" / "runtime-snapshots").glob("*.json")) == sorted(before)


# ── Phase 34K: runtime snapshot lineage ──────────────────────────────────────


def test_runtime_snapshot_lineage_empty_returns_no_chains(tmp_path: Path) -> None:
    result = build_runtime_snapshot_lineage(HarnessPath(tmp_path))
    assert result.lineage_chains == ()
    assert result.lineage_breaks == ()
    assert result.latest_head is None
    assert result.advisory == RUNTIME_SNAPSHOT_LINEAGE_ADVISORY


def test_runtime_snapshot_lineage_single_compatible_snapshot(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
    )
    result = build_runtime_snapshot_lineage(HarnessPath(tmp_path))
    assert len(result.lineage_chains) == 1
    assert result.lineage_breaks == ()
    chain = result.lineage_chains[0]
    assert chain.chain_index == 0
    assert len(chain.entries) == 1
    assert chain.entries[0].filename == export.export_path.name
    assert chain.entries[0].previous_filename is None
    assert chain.entries[0].compatibility_status == "compatible"
    assert result.latest_head is not None
    assert result.latest_head.filename == export.export_path.name


def test_runtime_snapshot_lineage_two_compatible_form_one_chain(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    first = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
    )
    second = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 11, 0, 0, tzinfo=timezone.utc),
    )
    result = build_runtime_snapshot_lineage(HarnessPath(tmp_path))
    assert len(result.lineage_chains) == 1
    assert result.lineage_breaks == ()
    chain = result.lineage_chains[0]
    assert len(chain.entries) == 2
    assert chain.entries[0].filename == first.export_path.name
    assert chain.entries[0].previous_filename is None
    assert chain.entries[1].filename == second.export_path.name
    assert chain.entries[1].previous_filename == first.export_path.name
    assert result.latest_head.filename == second.export_path.name


def test_runtime_snapshot_lineage_incompatible_breaks_chain(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    before = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
    )
    write_incompatible_snapshot(
        tmp_path,
        "runtime-snapshot-20260527-110000.json",
        "2026-05-27T11:00:00+00:00",
    )
    after = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc),
    )
    result = build_runtime_snapshot_lineage(HarnessPath(tmp_path))
    assert len(result.lineage_chains) == 2
    assert len(result.lineage_breaks) == 1
    assert result.lineage_breaks[0].filename == "runtime-snapshot-20260527-110000.json"
    assert result.lineage_breaks[0].reason == "incompatible snapshot breaks lineage continuity"
    chain0 = result.lineage_chains[0]
    assert chain0.chain_index == 0
    assert chain0.entries[0].filename == before.export_path.name
    chain1 = result.lineage_chains[1]
    assert chain1.chain_index == 1
    assert chain1.entries[0].filename == after.export_path.name
    assert chain1.entries[0].previous_filename is None
    assert result.latest_head.filename == after.export_path.name


def test_runtime_snapshot_lineage_ordering_is_deterministic(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    exports = [
        export_runtime_snapshot(
            HarnessPath(tmp_path),
            exported_at=datetime(2026, 5, 27, hour, 0, 0, tzinfo=timezone.utc),
        )
        for hour in range(1, 4)
    ]
    result1 = build_runtime_snapshot_lineage(HarnessPath(tmp_path))
    result2 = build_runtime_snapshot_lineage(HarnessPath(tmp_path))
    filenames1 = [e.filename for e in result1.lineage_chains[0].entries]
    filenames2 = [e.filename for e in result2.lineage_chains[0].entries]
    assert filenames1 == filenames2
    assert filenames1 == [export.export_path.name for export in exports]


def test_runtime_snapshot_lineage_latest_head_is_most_recent_compatible(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    write_incompatible_snapshot(
        tmp_path,
        "runtime-snapshot-20260527-090000.json",
        "2026-05-27T09:00:00+00:00",
    )
    last = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc),
    )
    result = build_runtime_snapshot_lineage(HarnessPath(tmp_path))
    assert result.latest_head is not None
    assert result.latest_head.filename == last.export_path.name


def test_runtime_snapshot_lineage_is_read_only(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    exports = [
        export_runtime_snapshot(
            HarnessPath(tmp_path),
            exported_at=datetime(2026, 5, 27, hour, 0, 0, tzinfo=timezone.utc),
        )
        for hour in range(1, 3)
    ]
    before = {
        export.export_path.name: (tmp_path / export.export_path).read_text(encoding="utf-8")
        for export in exports
    }
    build_runtime_snapshot_lineage(HarnessPath(tmp_path))
    after = {
        export.export_path.name: (tmp_path / export.export_path).read_text(encoding="utf-8")
        for export in exports
    }
    assert after == before


def test_cli_runtime_snapshot_lineage_human(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "lineage"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance runtime snapshot lineage" in output
    assert "Lineage chains: 1" in output
    assert "Lineage breaks: 0" in output
    assert "Chain 1 (1 snapshot):" in output
    assert "[head]" in output
    assert "Latest lineage head: runtime-snapshot-" in output
    assert RUNTIME_SNAPSHOT_LINEAGE_ADVISORY in output


def test_cli_runtime_snapshot_lineage_human_empty(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "lineage"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Lineage chains: 0" in output
    assert "Lineage breaks: 0" in output
    assert "Latest lineage head: none" in output
    assert RUNTIME_SNAPSHOT_LINEAGE_ADVISORY in output


def test_cli_runtime_snapshot_lineage_json(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    first = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
    )
    second = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 11, 0, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "lineage", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert len(data["lineage_chains"]) == 1
    assert data["lineage_breaks"] == []
    assert data["lineage_chains"][0]["chain_index"] == 0
    assert data["lineage_chains"][0]["length"] == 2
    entries = data["lineage_chains"][0]["entries"]
    assert entries[0]["filename"] == first.export_path.name
    assert entries[0]["previous_filename"] is None
    assert entries[1]["filename"] == second.export_path.name
    assert entries[1]["previous_filename"] == first.export_path.name
    assert data["latest_head"]["filename"] == second.export_path.name
    assert data["advisory"] == RUNTIME_SNAPSHOT_LINEAGE_ADVISORY


def test_cli_runtime_snapshot_lineage_json_with_break(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    before = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
    )
    write_incompatible_snapshot(
        tmp_path,
        "runtime-snapshot-20260527-110000.json",
        "2026-05-27T11:00:00+00:00",
    )
    after = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc),
    )
    monkeypatch.chdir(tmp_path)
    exit_code = main(["runtime", "snapshot", "lineage", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert len(data["lineage_chains"]) == 2
    assert len(data["lineage_breaks"]) == 1
    assert data["lineage_breaks"][0]["filename"] == "runtime-snapshot-20260527-110000.json"
    assert data["lineage_breaks"][0]["reason"] == "incompatible snapshot breaks lineage continuity"
    assert data["lineage_chains"][0]["entries"][0]["filename"] == before.export_path.name
    assert data["lineage_chains"][1]["entries"][0]["filename"] == after.export_path.name
    assert data["latest_head"]["filename"] == after.export_path.name


# ── Phase 34L: restore safety validation ────────────────────────────────────

PCAE_GITIGNORE_CONTENT = (
    "agent-lock.json\n"
    "architecture-history.json\n"
    "provenance-exports/\n"
    "provenance-history.json\n"
    "runtime-snapshots/\n"
    "session.json\n"
)


def commit_governance_baseline(tmp_path: Path) -> None:
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)


def setup_clean_governed_snapshot(tmp_path: Path):
    """Return export for a clean committed repo with one compatible snapshot.

    Uses init_harness to create all required PCAE files so run_checks passes,
    then writes session.json with matching task title for continuity verification.
    A .pcae/.gitignore excludes runtime files so the repo stays clean after
    writing agent locks or exporting snapshots.
    """
    from pcae.commands.init import init_harness

    initialize_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    # Write task and matching session
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "20260527-1200-test.md").write_text(
        "# Task Contract\n\n"
        "## Task ID\n\n20260527-1200-test\n\n"
        "## Title\n\nTest task\n\n"
        "## Status\n\nactive\n",
        encoding="utf-8",
    )
    pcae_dir = tmp_path / ".pcae"
    (pcae_dir / "session.json").write_text(
        json.dumps({
            "active_task": {"id": "20260527-1200-test", "title": "Test task"},
            "current_objective": "Validate restore safety.",
            "next_recommended_step": "Run governance checks.",
        }),
        encoding="utf-8",
    )
    (pcae_dir / "provenance-history.json").write_text(json.dumps([]), encoding="utf-8")
    (pcae_dir / ".gitignore").write_text(PCAE_GITIGNORE_CONTENT, encoding="utf-8")
    commit_governance_baseline(tmp_path)
    return export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
    )


def test_validate_restore_safe_on_clean_committed_repo(tmp_path: Path) -> None:
    export = setup_clean_governed_snapshot(tmp_path)
    result = validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path), tmp_path / export.export_path
    )
    assert result.safe_to_restore is True
    assert result.blocking_issues == ()
    assert result.advisory == RESTORE_SAFETY_VALIDATION_ADVISORY
    names = [c.name for c in result.validation_checks]
    for expected in (
        "snapshot_compatibility",
        "snapshot_support_level",
        "repo_cleanliness",
        "session_continuity",
        "active_task_presence",
        "policy_configuration",
        "agent_lock_safety",
        "lineage_continuity",
        "governance_health",
    ):
        assert expected in names
    assert all(c.passed for c in result.validation_checks)


def test_validate_restore_blocked_by_missing_file(tmp_path: Path) -> None:
    result = validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path),
        Path("nonexistent-snapshot.json"),
    )
    assert result.safe_to_restore is False
    assert len(result.validation_checks) == 1
    assert result.validation_checks[0].name == "snapshot_compatibility"
    assert result.validation_checks[0].blocking is True
    assert any("not found" in issue for issue in result.blocking_issues)


def test_validate_restore_blocked_by_incompatible_snapshot(tmp_path: Path) -> None:
    export = setup_clean_governed_snapshot(tmp_path)
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    data["snapshot_schema_version"] = 999
    target.write_text(json.dumps(data), encoding="utf-8")

    result = validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path), tmp_path / export.export_path
    )
    assert result.safe_to_restore is False
    compat = next(c for c in result.validation_checks if c.name == "snapshot_compatibility")
    assert not compat.passed and compat.blocking
    support = next(c for c in result.validation_checks if c.name == "snapshot_support_level")
    assert not support.passed and support.blocking
    assert len(result.blocking_issues) >= 1


def test_validate_restore_blocked_by_dirty_repo(tmp_path: Path) -> None:
    export = setup_clean_governed_snapshot(tmp_path)
    # Add an uncommitted tracked file after the baseline commit
    (tmp_path / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")
    subprocess.run(["git", "add", "dirty.txt"], cwd=tmp_path, check=True, capture_output=True)

    result = validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path), tmp_path / export.export_path
    )
    assert result.safe_to_restore is False
    check = next(c for c in result.validation_checks if c.name == "repo_cleanliness")
    assert not check.passed and check.blocking
    assert any("uncommitted" in issue for issue in result.blocking_issues)


def test_validate_restore_warns_on_session_continuity_mismatch(
    tmp_path: Path,
) -> None:
    initialize_git_repo(tmp_path)
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n## Next\n\n- Next.\n",
        encoding="utf-8",
    )
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True)
    (active_dir / "20260527-1200-test.md").write_text(
        "# Task Contract\n\n## Task ID\n\n20260527-1200-test\n\n## Title\n\nTest task\n\n## Status\n\nactive\n",
        encoding="utf-8",
    )
    pcae_dir = tmp_path / ".pcae"
    pcae_dir.mkdir()
    # Session references a different task {id+title} — triggers mismatch violation
    (pcae_dir / "session.json").write_text(
        json.dumps({"active_task": {"id": "different-task", "title": "Different task"}}),
        encoding="utf-8",
    )
    (pcae_dir / "provenance-history.json").write_text(json.dumps([]), encoding="utf-8")
    (pcae_dir / ".gitignore").write_text(PCAE_GITIGNORE_CONTENT, encoding="utf-8")
    commit_governance_baseline(tmp_path)
    export = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
    )

    result = validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path), tmp_path / export.export_path
    )
    check = next(c for c in result.validation_checks if c.name == "session_continuity")
    assert not check.passed
    assert not check.blocking
    assert any("continuity" in w.lower() or "session" in w.lower() for w in result.warnings)


def test_validate_restore_warns_on_no_active_task(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n## Next\n\n- Next.\n",
        encoding="utf-8",
    )
    pcae_dir = tmp_path / ".pcae"
    pcae_dir.mkdir()
    (pcae_dir / "session.json").write_text(json.dumps({}), encoding="utf-8")
    (pcae_dir / "provenance-history.json").write_text(json.dumps([]), encoding="utf-8")
    (pcae_dir / ".gitignore").write_text(PCAE_GITIGNORE_CONTENT, encoding="utf-8")
    commit_governance_baseline(tmp_path)
    export = export_runtime_snapshot(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
    )

    result = validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path), tmp_path / export.export_path
    )
    check = next(c for c in result.validation_checks if c.name == "active_task_presence")
    assert not check.passed
    assert not check.blocking
    assert any("active task" in w.lower() for w in result.warnings)


def test_validate_restore_warns_on_active_agent_lock(tmp_path: Path) -> None:
    export = setup_clean_governed_snapshot(tmp_path)
    # Write a fresh (non-stale) agent lock — gitignored, repo stays clean
    (tmp_path / ".pcae" / "agent-lock.json").write_text(
        json.dumps({
            "agent_id": "other-agent",
            "acquired_at": datetime.now(timezone.utc).isoformat(),
            "active_task": None,
            "git_branch": "main",
        }),
        encoding="utf-8",
    )

    result = validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path), tmp_path / export.export_path
    )
    check = next(c for c in result.validation_checks if c.name == "agent_lock_safety")
    assert not check.passed
    assert not check.blocking
    assert any("other-agent" in w for w in result.warnings)


def test_validate_restore_warns_on_lineage_break(tmp_path: Path) -> None:
    initialize_git_repo(tmp_path)
    write_minimal_governance_artifacts(tmp_path)
    (tmp_path / ".pcae" / ".gitignore").write_text(PCAE_GITIGNORE_CONTENT, encoding="utf-8")
    commit_governance_baseline(tmp_path)
    write_incompatible_snapshot(
        tmp_path,
        "runtime-snapshot-20260527-100000.json",
        "2026-05-27T10:00:00+00:00",
    )

    result = validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path),
        tmp_path / ".pcae" / "runtime-snapshots" / "runtime-snapshot-20260527-100000.json",
    )
    check = next(c for c in result.validation_checks if c.name == "lineage_continuity")
    assert not check.passed
    assert not check.blocking
    assert result.lineage_status == "lineage_break"
    assert any("lineage" in w.lower() for w in result.warnings)


def test_validate_restore_warns_on_unknown_lineage(tmp_path: Path) -> None:
    """Snapshot file outside the manifest dir has unknown lineage status."""
    export = setup_clean_governed_snapshot(tmp_path)
    target = tmp_path / export.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    # Remove from standard dir; write to non-standard location
    target.unlink()
    orphan = tmp_path / "orphan-snapshot.json"
    orphan.write_text(json.dumps(data), encoding="utf-8")

    result = validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path), orphan
    )
    check = next(c for c in result.validation_checks if c.name == "lineage_continuity")
    assert not check.passed
    assert not check.blocking
    assert result.lineage_status == "unknown"
    assert any("lineage" in w.lower() for w in result.warnings)


def test_validate_restore_is_read_only(tmp_path: Path) -> None:
    export = setup_clean_governed_snapshot(tmp_path)
    target = tmp_path / export.export_path
    before = target.read_text(encoding="utf-8")
    validate_runtime_snapshot_restore_safety(
        HarnessPath(tmp_path), tmp_path / export.export_path
    )
    assert target.read_text(encoding="utf-8") == before
    snapshots = sorted(p.name for p in (tmp_path / ".pcae" / "runtime-snapshots").glob("*.json"))
    assert snapshots == [export.export_path.name]


def test_cli_validate_restore_human(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    export = setup_clean_governed_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(
        ["runtime", "snapshot", "validate-restore", str(tmp_path / export.export_path)]
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance runtime snapshot restore safety validation" in output
    assert "Restore safety status: safe" in output
    assert "Validation checks:" in output
    assert "snapshot_compatibility: pass" in output
    assert "repo_cleanliness: pass" in output
    assert "Blocking issues:" in output
    assert "  - none" in output
    assert "Lineage continuity status:" in output
    assert RESTORE_SAFETY_VALIDATION_ADVISORY in output


def test_cli_validate_restore_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    export = setup_clean_governed_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(
        ["runtime", "snapshot", "validate-restore",
         str(tmp_path / export.export_path), "--json"]
    )
    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["safe_to_restore"] is True
    assert data["blocking_issues"] == []
    assert data["warnings"] == []
    names = [c["name"] for c in data["validation_checks"]]
    assert names == [
        "snapshot_compatibility",
        "snapshot_support_level",
        "repo_cleanliness",
        "session_continuity",
        "active_task_presence",
        "policy_configuration",
        "agent_lock_safety",
        "lineage_continuity",
        "governance_health",
    ]
    assert all(c["passed"] for c in data["validation_checks"])
    assert all(not c["blocking"] for c in data["validation_checks"])
    assert data["advisory"] == RESTORE_SAFETY_VALIDATION_ADVISORY


def write_incompatible_snapshot(
    tmp_path: Path,
    filename: str,
    exported_at: str,
) -> None:
    snapshot_dir = tmp_path / ".pcae" / "runtime-snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / filename).write_text(
        json.dumps({
            "snapshot_schema_version": 999,
            "snapshot_kind": "pcae-runtime-snapshot",
            "exported_by_version": "0.1.0",
            "exported_at": exported_at,
            "active_task": None,
            "agent_lock_state": None,
            "session_continuity_status": "unknown",
            "provenance_event_count": 0,
            "latest_provenance_event": None,
            "orchestration_policy_summary": {},
            "registered_agents": [],
            "governance_health_status": "unknown",
            "governance_check_status": "unknown",
            "workflow_orchestration_metadata": {},
        }),
        encoding="utf-8",
    )


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


# ---------------------------------------------------------------------------
# Phase 35L: Governance artifact synchronization validation
# ---------------------------------------------------------------------------

from pcae.core.status import (
    GOVERNANCE_SYNC_CHECK_ADVISORY,
    GovernanceSyncCheckResult,
    check_governance_sync,
)


def _write_sync_artifacts(
    tmp_path: Path,
    todo_pending: list[str] | None = None,
    done_entries: list[str] | None = None,
    changelog_entries: list[str] | None = None,
    next_items: list[str] | None = None,
) -> None:
    """Write the four governance artifacts for sync-check tests."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    pending = todo_pending or []
    todo_lines = ["# TODO\n\n## Pending\n"]
    for item in pending:
        todo_lines.append(f"- {item}\n")
    (tasks_dir / "TODO.md").write_text("".join(todo_lines), encoding="utf-8")

    done = done_entries or []
    done_lines = ["# DONE\n\n"]
    for item in done:
        done_lines.append(f"- {item}\n")
    (tasks_dir / "DONE.md").write_text("".join(done_lines), encoding="utf-8")

    changelog = changelog_entries or []
    changelog_lines = ["# Changelog\n\n## Unreleased\n\n"]
    for item in changelog:
        changelog_lines.append(f"- {item}\n")
    (tmp_path / "CHANGELOG.md").write_text("".join(changelog_lines), encoding="utf-8")

    next_bullets = next_items or ["No pending governed phases."]
    next_lines = [
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n## Next\n\n"
    ]
    for item in next_bullets:
        next_lines.append(f"- {item}\n")
    (tmp_path / "PROJECT_STATUS.md").write_text("".join(next_lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Core: check_governance_sync — return type and advisory
# ---------------------------------------------------------------------------


def test_check_governance_sync_returns_result(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = check_governance_sync(HarnessPath(tmp_path))
    assert isinstance(result, GovernanceSyncCheckResult)


def test_check_governance_sync_advisory(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.advisory == GOVERNANCE_SYNC_CHECK_ADVISORY


# ---------------------------------------------------------------------------
# Core: check_governance_sync — synchronized flag
# ---------------------------------------------------------------------------


def test_check_governance_sync_synchronized_when_clean(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = check_governance_sync(HarnessPath(tmp_path))
    # No stale refs, no completed todos, no inconsistent entries → synchronized
    assert result.synchronized is True


def test_check_governance_sync_not_synchronized_on_stale_ref(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path, next_items=["Implement `pcae end`."])
    # KNOWN_STALE_PHRASES includes "Implement `pcae end`"
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n"
        "## Next\n\n- Implement `pcae end`.\n",
        encoding="utf-8",
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.synchronized is False


def test_check_governance_sync_not_synchronized_on_completed_todo(
    tmp_path: Path,
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae foo bar` command."],
        done_entries=["Added `pcae foo bar` for testing."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.synchronized is False


def test_check_governance_sync_not_synchronized_on_inconsistent_entry(
    tmp_path: Path,
) -> None:
    _write_sync_artifacts(
        tmp_path,
        next_items=["Implement `pcae baz qux`."],
        done_entries=["Added `pcae baz qux` command."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.synchronized is False


# ---------------------------------------------------------------------------
# Core: stale_references
# ---------------------------------------------------------------------------


def test_stale_references_empty_when_no_stale_phrases(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.stale_references == ()


def test_stale_references_detected_in_project_status(tmp_path: Path) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n"
        "## Next\n\n- Implement `pcae end`.\n",
        encoding="utf-8",
    )
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TODO.md").write_text("# TODO\n\n## Pending\n", encoding="utf-8")
    (tasks_dir / "DONE.md").write_text("# DONE\n\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n", encoding="utf-8")
    result = check_governance_sync(HarnessPath(tmp_path))
    assert len(result.stale_references) >= 1
    assert any("Implement `pcae end`" in ref for ref in result.stale_references)


def test_stale_references_detected_in_todo(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Implement `pcae end` command."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    stale_in_todo = [r for r in result.stale_references if "tasks/TODO.md" in r]
    assert len(stale_in_todo) >= 1


def test_stale_references_detected_in_changelog(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    stale_in_changelog = [r for r in result.stale_references if "CHANGELOG.md" in r]
    assert len(stale_in_changelog) >= 1


def test_stale_references_detected_in_done(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        done_entries=["Implement `pcae end` was added."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    stale_in_done = [r for r in result.stale_references if "tasks/DONE.md" in r]
    assert len(stale_in_done) >= 1


# ---------------------------------------------------------------------------
# Core: completed_todo_entries
# ---------------------------------------------------------------------------


def test_completed_todo_empty_when_no_pending(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.completed_todo_entries == ()


def test_completed_todo_detected_via_done(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Implement `pcae alpha beta` command."],
        done_entries=["Added `pcae alpha beta` for governance."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert len(result.completed_todo_entries) == 1
    assert "pcae alpha beta" in result.completed_todo_entries[0]


def test_completed_todo_detected_via_changelog(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Update `pcae docs commands` to include phase group."],
        changelog_entries=["Refreshed `pcae docs commands` generated output."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert len(result.completed_todo_entries) == 1
    assert "pcae docs commands" in result.completed_todo_entries[0]


def test_completed_todo_not_flagged_when_command_absent(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Implement `pcae orchestration select` for routing."],
        done_entries=["Added `pcae orchestration recommend` for routing."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    # "pcae orchestration select" is NOT in done/changelog → not flagged
    assert result.completed_todo_entries == ()


def test_completed_todo_not_flagged_when_no_pcae_command(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Write documentation for governance workflows."],
        done_entries=["Updated docs with governance workflow guide."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    # No `pcae ...` command in the item → not flagged
    assert result.completed_todo_entries == ()


def test_completed_todo_multiple_items(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=[
            "Add `pcae feature one` command.",
            "Add `pcae feature two` command.",
            "Add `pcae feature three` command.",
        ],
        done_entries=[
            "Added `pcae feature one` to the CLI.",
            "Added `pcae feature two` to the CLI.",
        ],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert len(result.completed_todo_entries) == 2
    # feature three is NOT in done → only two flagged
    assert all(
        "pcae feature one" in e or "pcae feature two" in e
        for e in result.completed_todo_entries
    )


# ---------------------------------------------------------------------------
# Core: inconsistent_entries
# ---------------------------------------------------------------------------


def test_inconsistent_entries_empty_when_no_next_commands(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path, next_items=["No pending governed phases."])
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.inconsistent_entries == ()


def test_inconsistent_entry_detected_when_next_command_in_done(
    tmp_path: Path,
) -> None:
    _write_sync_artifacts(
        tmp_path,
        next_items=["Implement `pcae next feature` command."],
        done_entries=["Added `pcae next feature` for governance."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert len(result.inconsistent_entries) == 1
    assert "pcae next feature" in result.inconsistent_entries[0]


def test_inconsistent_entry_not_flagged_when_command_absent_from_done(
    tmp_path: Path,
) -> None:
    _write_sync_artifacts(
        tmp_path,
        next_items=["Implement `pcae future command` for routing."],
        done_entries=["Added `pcae other command`."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.inconsistent_entries == ()


def test_inconsistent_entry_label_mentions_roadmap(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        next_items=["Add `pcae roadmap item` feature."],
        done_entries=["Added `pcae roadmap item` to CLI."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.inconsistent_entries
    assert "roadmap" in result.inconsistent_entries[0].lower()


# ---------------------------------------------------------------------------
# Core: governance_drift_warnings
# ---------------------------------------------------------------------------


def test_governance_drift_warning_empty_when_gap_closed(tmp_path: Path) -> None:
    # Phase 35M added artifact_sync_drift to the audit; the gap is now closed.
    _write_sync_artifacts(tmp_path)
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.governance_drift_warnings == ()


def test_governance_drift_warning_field_is_list_in_dict(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = check_governance_sync(HarnessPath(tmp_path))
    assert isinstance(result.to_dict()["governance_drift_warnings"], list)


# ---------------------------------------------------------------------------
# Core: to_dict
# ---------------------------------------------------------------------------


def test_check_governance_sync_to_dict_keys(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = check_governance_sync(HarnessPath(tmp_path))
    d = result.to_dict()
    for key in (
        "synchronized",
        "stale_references",
        "completed_todo_entries",
        "inconsistent_entries",
        "governance_drift_warnings",
        "advisory",
    ):
        assert key in d, f"missing key: {key}"


def test_check_governance_sync_to_dict_types(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = check_governance_sync(HarnessPath(tmp_path))
    d = result.to_dict()
    assert isinstance(d["synchronized"], bool)
    assert isinstance(d["stale_references"], list)
    assert isinstance(d["completed_todo_entries"], list)
    assert isinstance(d["inconsistent_entries"], list)
    assert isinstance(d["governance_drift_warnings"], list)
    assert isinstance(d["advisory"], str)


def test_check_governance_sync_is_read_only(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    todo_path = tmp_path / "tasks" / "TODO.md"
    mtime = todo_path.stat().st_mtime
    check_governance_sync(HarnessPath(tmp_path))
    assert todo_path.stat().st_mtime == mtime


def test_check_governance_sync_missing_artifacts(tmp_path: Path) -> None:
    # Missing all four artifacts → should not raise, returns result with empty fields
    result = check_governance_sync(HarnessPath(tmp_path))
    assert isinstance(result, GovernanceSyncCheckResult)
    assert result.stale_references == ()
    assert result.completed_todo_entries == ()
    assert result.inconsistent_entries == ()


# ---------------------------------------------------------------------------
# CLI: pcae governance sync-check (human-readable)
# ---------------------------------------------------------------------------


def test_cli_governance_sync_check_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "sync-check"])
    assert result == 0


def test_cli_governance_sync_check_prints_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    assert "Synchronization status:" in captured.out


def test_cli_governance_sync_check_prints_stale_references(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    assert "Stale references:" in captured.out


def test_cli_governance_sync_check_prints_completed_todo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae x y` command."],
        done_entries=["Added `pcae x y` for governance."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    assert "Completed TODO entries:" in captured.out
    assert "pcae x y" in captured.out


def test_cli_governance_sync_check_prints_inconsistent_entries(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    assert "Inconsistent roadmap entries:" in captured.out


def test_cli_governance_sync_check_prints_drift_warnings_section(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # The section header always appears; content is "none" when gap is closed.
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    assert "Governance drift warnings:" in captured.out


def test_cli_governance_sync_check_prints_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    assert GOVERNANCE_SYNC_CHECK_ADVISORY in captured.out


def test_cli_governance_sync_check_none_label_when_clean(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    # Stale refs and completed todos are empty → "none" label appears
    assert "none" in captured.out.lower()


# ---------------------------------------------------------------------------
# CLI: pcae governance sync-check --json
# ---------------------------------------------------------------------------


def test_cli_governance_sync_check_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "sync-check", "--json"])
    assert result == 0


def test_cli_governance_sync_check_json_is_valid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_cli_governance_sync_check_json_required_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    for key in (
        "synchronized",
        "stale_references",
        "completed_todo_entries",
        "inconsistent_entries",
        "governance_drift_warnings",
        "advisory",
    ):
        assert key in data, f"missing JSON key: {key}"


def test_cli_governance_sync_check_json_synchronized_clean(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["synchronized"] is True
    assert data["stale_references"] == []
    assert data["completed_todo_entries"] == []
    assert data["inconsistent_entries"] == []


def test_cli_governance_sync_check_json_detects_completed_todo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Implement `pcae zeta eta` command."],
        done_entries=["Added `pcae zeta eta` for governance."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["synchronized"] is False
    assert len(data["completed_todo_entries"]) == 1
    assert "pcae zeta eta" in data["completed_todo_entries"][0]


def test_cli_governance_sync_check_json_detects_stale_ref(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n"
        "## Next\n\n- Implement `pcae end`.\n",
        encoding="utf-8",
    )
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TODO.md").write_text("# TODO\n\n## Pending\n", encoding="utf-8")
    (tasks_dir / "DONE.md").write_text("# DONE\n\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["synchronized"] is False
    assert len(data["stale_references"]) >= 1


def test_cli_governance_sync_check_json_drift_warnings_empty_when_gap_closed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # Phase 35M closed the artifact_sync_drift gap; clean scenario has no drift warnings.
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data["governance_drift_warnings"], list)
    assert data["governance_drift_warnings"] == []


def test_cli_governance_sync_check_json_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["advisory"] == GOVERNANCE_SYNC_CHECK_ADVISORY


def test_cli_governance_sync_check_json_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    todo_path = tmp_path / "tasks" / "TODO.md"
    mtime = todo_path.stat().st_mtime
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    assert todo_path.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# Phase 35M: artifact_sync_drift integrated into governance audit
# ---------------------------------------------------------------------------

from pcae.core.status import (
    check_artifact_sync_drift,
    find_artifact_sync_drift_warnings,
    GovernanceAuditCheck,
    CoherenceWarning,
)


# ---------------------------------------------------------------------------
# Core: check_artifact_sync_drift
# ---------------------------------------------------------------------------


def test_check_artifact_sync_drift_returns_audit_check(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = check_artifact_sync_drift(HarnessPath(tmp_path))
    assert isinstance(result, GovernanceAuditCheck)


def test_check_artifact_sync_drift_name(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = check_artifact_sync_drift(HarnessPath(tmp_path))
    assert result.name == "artifact_sync_drift"


def test_check_artifact_sync_drift_passes_when_clean(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = check_artifact_sync_drift(HarnessPath(tmp_path))
    assert result.passed is True
    assert "synchronized" in result.message.lower()


def test_check_artifact_sync_drift_passes_with_completed_todo(tmp_path: Path) -> None:
    # Even when drift is detected the check still passes; issues go to warnings.
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae drift cmd` command.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae drift cmd` for governance.\n",
        encoding="utf-8",
    )
    result = check_artifact_sync_drift(HarnessPath(tmp_path))
    assert result.passed is True
    assert result.name == "artifact_sync_drift"


def test_check_artifact_sync_drift_message_reports_issue_count(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae count test` command.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae count test` command.\n",
        encoding="utf-8",
    )
    result = check_artifact_sync_drift(HarnessPath(tmp_path))
    assert "1" in result.message


def test_check_artifact_sync_drift_is_read_only(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    ps_path = tmp_path / "PROJECT_STATUS.md"
    mtime = ps_path.stat().st_mtime
    check_artifact_sync_drift(HarnessPath(tmp_path))
    assert ps_path.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# Core: find_artifact_sync_drift_warnings
# ---------------------------------------------------------------------------


def test_find_artifact_sync_drift_warnings_empty_when_clean(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    warnings = find_artifact_sync_drift_warnings(HarnessPath(tmp_path))
    assert warnings == ()


def test_find_artifact_sync_drift_warnings_for_completed_todo(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae warn cmd` command.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae warn cmd` for governance.\n",
        encoding="utf-8",
    )
    warnings = find_artifact_sync_drift_warnings(HarnessPath(tmp_path))
    assert len(warnings) == 1
    assert warnings[0].document == "tasks/TODO.md"
    assert "pcae warn cmd" in warnings[0].message


def test_find_artifact_sync_drift_warnings_for_inconsistent_roadmap(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(
        tmp_path,
        next_item="Add `pcae roadmap cmd` feature.",
    )
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae roadmap cmd` command.\n",
        encoding="utf-8",
    )
    warnings = find_artifact_sync_drift_warnings(HarnessPath(tmp_path))
    assert len(warnings) == 1
    assert warnings[0].document == "PROJECT_STATUS.md"


def test_find_artifact_sync_drift_warnings_excludes_stale_phrases(
    tmp_path: Path,
) -> None:
    # Stale KNOWN_STALE_PHRASES are handled by find_stale_roadmap_references;
    # they must NOT be double-counted in find_artifact_sync_drift_warnings.
    write_minimal_governance_artifacts(
        tmp_path,
        next_item="Full governance audit: `pcae governance audit` command.",
    )
    warnings = find_artifact_sync_drift_warnings(HarnessPath(tmp_path))
    # The stale phrase in PROJECT_STATUS.md should NOT appear in these warnings.
    assert not any("Full governance audit" in w.message for w in warnings)


def test_find_artifact_sync_drift_warnings_is_read_only(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae ro cmd` command.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae ro cmd`.\n",
        encoding="utf-8",
    )
    done_path = tasks_dir / "DONE.md"
    mtime = done_path.stat().st_mtime
    find_artifact_sync_drift_warnings(HarnessPath(tmp_path))
    assert done_path.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# Core: audit_governance_coherence includes artifact_sync_drift
# ---------------------------------------------------------------------------


def test_audit_includes_artifact_sync_drift_check(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    check_names = {c.name for c in result.checks}
    assert "artifact_sync_drift" in check_names


def test_audit_artifact_sync_drift_passes_when_clean(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    sync_check = next(c for c in result.checks if c.name == "artifact_sync_drift")
    assert sync_check.passed is True


def test_audit_warns_on_completed_todo_drift(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae audit drift` command.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae audit drift` for governance.\n",
        encoding="utf-8",
    )
    result = audit_governance_coherence(HarnessPath(tmp_path))
    assert result.summary.warning_count >= 1
    assert any("tasks/TODO.md" in w.document for w in result.warnings)


def test_audit_warns_on_inconsistent_roadmap_drift(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(
        tmp_path,
        next_item="Implement `pcae inconsistent cmd` feature.",
    )
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae inconsistent cmd`.\n",
        encoding="utf-8",
    )
    result = audit_governance_coherence(HarnessPath(tmp_path))
    assert result.summary.warning_count >= 1
    assert any("PROJECT_STATUS.md" in w.document for w in result.warnings)


def test_audit_does_not_double_count_stale_phrases(tmp_path: Path) -> None:
    # Stale phrases already surface through find_stale_roadmap_references;
    # find_artifact_sync_drift_warnings must not add them again.
    write_minimal_governance_artifacts(
        tmp_path,
        next_item="Full governance audit: `pcae governance audit` command.",
    )
    result = audit_governance_coherence(HarnessPath(tmp_path))
    # Expect exactly 1 warning (the stale roadmap ref, not doubled).
    assert result.summary.warning_count == 1


def test_audit_status_warnings_when_drift_found(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae status warn` feature.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae status warn` command.\n",
        encoding="utf-8",
    )
    result = audit_governance_coherence(HarnessPath(tmp_path))
    assert result.summary.status == "warnings"
    assert result.summary.failed_count == 0


def test_audit_failed_count_unchanged_by_drift(tmp_path: Path) -> None:
    # artifact_sync_drift always passes; drift issues go to warnings, not failures.
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae no fail` feature.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae no fail`.\n",
        encoding="utf-8",
    )
    result = audit_governance_coherence(HarnessPath(tmp_path))
    assert result.summary.failed_count == 0


def test_audit_is_read_only_with_drift(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    todo_path = tasks_dir / "TODO.md"
    todo_path.write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae read only` feature.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae read only`.\n",
        encoding="utf-8",
    )
    mtime = todo_path.stat().st_mtime
    audit_governance_coherence(HarnessPath(tmp_path))
    assert todo_path.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# CLI: pcae governance audit with artifact_sync_drift (human-readable)
# ---------------------------------------------------------------------------


def test_cli_audit_human_shows_artifact_sync_drift_check(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "audit"])
    captured = capsys.readouterr()
    assert "artifact_sync_drift" in captured.out


def test_cli_audit_human_drift_check_passes_when_clean(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "audit"])
    captured = capsys.readouterr()
    assert "artifact_sync_drift: pass" in captured.out


def test_cli_audit_human_shows_drift_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae cli human` feature.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae cli human`.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "audit"])
    captured = capsys.readouterr()
    assert "tasks/TODO.md" in captured.out
    assert "Completed TODO" in captured.out


# ---------------------------------------------------------------------------
# CLI: pcae governance audit --json with artifact_sync_drift
# ---------------------------------------------------------------------------


def test_cli_audit_json_includes_artifact_sync_drift(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "audit", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    check_names = [c["name"] for c in data["checks"]]
    assert "artifact_sync_drift" in check_names


def test_cli_audit_json_artifact_sync_drift_passes_when_clean(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "audit", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    drift_check = next(c for c in data["checks"] if c["name"] == "artifact_sync_drift")
    assert drift_check["passed"] is True


def test_cli_audit_json_includes_drift_warning(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae json warn` feature.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae json warn`.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "audit", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data["warnings"]) >= 1
    warning_docs = [w["document"] for w in data["warnings"]]
    assert "tasks/TODO.md" in warning_docs


def test_cli_audit_json_valid_false_on_drift(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae valid false` feature.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae valid false`.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "audit", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is False
    assert data["summary"]["status"] == "warnings"
    assert data["summary"]["failed_count"] == 0


# ---------------------------------------------------------------------------
# Phase 35N: governance synchronization repair preview
# ---------------------------------------------------------------------------

from pcae.core.status import (
    GOVERNANCE_SYNC_REPAIR_ADVISORY,
    GovernanceSyncRepairPreview,
    SyncRepairEntry,
    plan_governance_sync_repairs,
)


# ---------------------------------------------------------------------------
# Core: plan_governance_sync_repairs — return type and advisory
# ---------------------------------------------------------------------------


def test_plan_governance_sync_repairs_returns_preview(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    assert isinstance(result, GovernanceSyncRepairPreview)


def test_plan_governance_sync_repairs_advisory(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    assert result.advisory == GOVERNANCE_SYNC_REPAIR_ADVISORY


def test_plan_governance_sync_repairs_repairable_always_true(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    assert result.repairable is True


# ---------------------------------------------------------------------------
# Core: plan_governance_sync_repairs — clean repo has no repairs
# ---------------------------------------------------------------------------


def test_plan_governance_sync_repairs_no_repairs_when_clean(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    assert result.proposed_repairs == ()


# ---------------------------------------------------------------------------
# Core: plan_governance_sync_repairs — completed TODO entries
# ---------------------------------------------------------------------------


def test_plan_governance_sync_repairs_repair_for_completed_todo(
    tmp_path: Path,
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae repair todo` command."],
        done_entries=["Added `pcae repair todo` for governance."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    todo_repairs = [r for r in result.proposed_repairs if r.artifact == "tasks/TODO.md"]
    assert len(todo_repairs) == 1
    repair = todo_repairs[0]
    assert "pcae repair todo" in repair.stale_entry
    assert repair.action == "remove"
    assert repair.rationale


def test_plan_governance_sync_repairs_repair_entry_is_sync_repair_entry(
    tmp_path: Path,
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae entry type` command."],
        done_entries=["Added `pcae entry type`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    for repair in result.proposed_repairs:
        assert isinstance(repair, SyncRepairEntry)


# ---------------------------------------------------------------------------
# Core: plan_governance_sync_repairs — stale roadmap/command references
# ---------------------------------------------------------------------------


def test_plan_governance_sync_repairs_repair_for_stale_reference(
    tmp_path: Path,
) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n"
        "## Next\n\n- Implement `pcae end`.\n",
        encoding="utf-8",
    )
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TODO.md").write_text("# TODO\n\n## Pending\n", encoding="utf-8")
    (tasks_dir / "DONE.md").write_text("# DONE\n\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n", encoding="utf-8")
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    stale_repairs = [
        r for r in result.proposed_repairs if r.action == "remove" and "PROJECT_STATUS.md" in r.artifact
    ]
    assert len(stale_repairs) >= 1
    assert any("pcae end" in r.stale_entry or "pcae end" in r.stale_entry for r in stale_repairs)


def test_plan_governance_sync_repairs_stale_reference_action_is_remove(
    tmp_path: Path,
) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n"
        "## Next\n\n- Implement `pcae end`.\n",
        encoding="utf-8",
    )
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TODO.md").write_text("# TODO\n\n## Pending\n", encoding="utf-8")
    (tasks_dir / "DONE.md").write_text("# DONE\n\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n", encoding="utf-8")
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    for repair in result.proposed_repairs:
        assert repair.action in ("remove", "update", "relocate")


# ---------------------------------------------------------------------------
# Core: plan_governance_sync_repairs — inconsistent roadmap entries
# ---------------------------------------------------------------------------


def test_plan_governance_sync_repairs_repair_for_inconsistent_roadmap(
    tmp_path: Path,
) -> None:
    _write_sync_artifacts(
        tmp_path,
        next_items=["Add `pcae roadmap fix` feature."],
        done_entries=["Added `pcae roadmap fix` command."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    roadmap_repairs = [
        r for r in result.proposed_repairs if r.artifact == "PROJECT_STATUS.md"
    ]
    assert len(roadmap_repairs) >= 1
    repair = roadmap_repairs[0]
    assert repair.action == "remove"
    assert "pcae roadmap fix" in repair.stale_entry


# ---------------------------------------------------------------------------
# Core: plan_governance_sync_repairs — to_dict shape
# ---------------------------------------------------------------------------


def test_plan_governance_sync_repairs_to_dict_keys(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    d = result.to_dict()
    assert "repairable" in d
    assert "proposed_repairs" in d
    assert "advisory" in d


def test_plan_governance_sync_repairs_to_dict_types(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    d = result.to_dict()
    assert isinstance(d["repairable"], bool)
    assert isinstance(d["proposed_repairs"], list)
    assert isinstance(d["advisory"], str)


def test_plan_governance_sync_repairs_repair_to_dict_keys(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae dict key` command."],
        done_entries=["Added `pcae dict key`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    d = result.to_dict()
    assert d["proposed_repairs"]
    repair_dict = d["proposed_repairs"][0]
    for key in ("artifact", "stale_entry", "action", "rationale"):
        assert key in repair_dict, f"missing key: {key}"


# ---------------------------------------------------------------------------
# Core: plan_governance_sync_repairs — read-only guarantee
# ---------------------------------------------------------------------------


def test_plan_governance_sync_repairs_is_read_only(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae ro check` command."],
        done_entries=["Added `pcae ro check`."],
    )
    todo_path = tmp_path / "tasks" / "TODO.md"
    mtime = todo_path.stat().st_mtime
    plan_governance_sync_repairs(HarnessPath(tmp_path))
    assert todo_path.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# CLI: pcae governance sync-repair --dry-run (human-readable)
# ---------------------------------------------------------------------------


def test_cli_governance_sync_repair_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "sync-repair", "--dry-run"])
    assert result == 0


def test_cli_governance_sync_repair_prints_header(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "Governance synchronization repair preview" in output


def test_cli_governance_sync_repair_prints_proposed_repairs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "Proposed repairs:" in output


def test_cli_governance_sync_repair_prints_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert GOVERNANCE_SYNC_REPAIR_ADVISORY in output


def test_cli_governance_sync_repair_none_when_clean(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "none" in output.lower()


def test_cli_governance_sync_repair_shows_todo_repair(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae cli show` command."],
        done_entries=["Added `pcae cli show` for governance."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "tasks/TODO.md" in output
    assert "pcae cli show" in output
    assert "remove" in output


def test_cli_governance_sync_repair_shows_stale_reference_repair(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n"
        "## Next\n\n- Implement `pcae end`.\n",
        encoding="utf-8",
    )
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TODO.md").write_text("# TODO\n\n## Pending\n", encoding="utf-8")
    (tasks_dir / "DONE.md").write_text("# DONE\n\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "PROJECT_STATUS.md" in output
    assert "remove" in output


def test_cli_governance_sync_repair_shows_rationale(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae rationale test` command."],
        done_entries=["Added `pcae rationale test`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "Rationale:" in output


def test_cli_governance_sync_repair_requires_dry_run_flag(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        main(["governance", "sync-repair"])


def test_cli_governance_sync_repair_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae cli ro` command."],
        done_entries=["Added `pcae cli ro`."],
    )
    todo_path = tmp_path / "tasks" / "TODO.md"
    mtime = todo_path.stat().st_mtime
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    assert todo_path.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# CLI: pcae governance sync-repair --dry-run --json
# ---------------------------------------------------------------------------


def test_cli_governance_sync_repair_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "sync-repair", "--dry-run", "--json"])
    assert result == 0


def test_cli_governance_sync_repair_json_is_valid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_cli_governance_sync_repair_json_required_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    for key in ("repairable", "proposed_repairs", "advisory"):
        assert key in data, f"missing JSON key: {key}"


def test_cli_governance_sync_repair_json_clean_has_no_repairs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["repairable"] is True
    assert data["proposed_repairs"] == []
    assert data["advisory"] == GOVERNANCE_SYNC_REPAIR_ADVISORY


def test_cli_governance_sync_repair_json_detects_completed_todo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae json todo` command."],
        done_entries=["Added `pcae json todo` for governance."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    todo_repairs = [r for r in data["proposed_repairs"] if r["artifact"] == "tasks/TODO.md"]
    assert len(todo_repairs) == 1
    repair = todo_repairs[0]
    assert "pcae json todo" in repair["stale_entry"]
    assert repair["action"] == "remove"
    assert repair["rationale"]


def test_cli_governance_sync_repair_json_detects_stale_reference(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n"
        "## Next\n\n- Implement `pcae end`.\n",
        encoding="utf-8",
    )
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TODO.md").write_text("# TODO\n\n## Pending\n", encoding="utf-8")
    (tasks_dir / "DONE.md").write_text("# DONE\n\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data["proposed_repairs"]) >= 1
    actions = [r["action"] for r in data["proposed_repairs"]]
    assert "remove" in actions


def test_cli_governance_sync_repair_json_repair_entry_shape(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae shape check` command."],
        done_entries=["Added `pcae shape check`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["proposed_repairs"]
    repair = data["proposed_repairs"][0]
    for key in ("artifact", "stale_entry", "action", "rationale"):
        assert key in repair, f"missing key: {key}"


def test_cli_governance_sync_repair_json_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["advisory"] == GOVERNANCE_SYNC_REPAIR_ADVISORY


def test_cli_governance_sync_repair_json_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae json ro` command."],
        done_entries=["Added `pcae json ro`."],
    )
    todo_path = tmp_path / "tasks" / "TODO.md"
    mtime = todo_path.stat().st_mtime
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    assert todo_path.stat().st_mtime == mtime
