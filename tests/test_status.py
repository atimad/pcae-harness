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
    PREDICTED_PHASES_OPTION_B,
    PREDICTED_PHASES_OPTION_C,
    ROADMAP_RECOMMENDATION_ADVISORY,
    ROADMAP_SEQUENCE,
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
    recommend_next_roadmap_phase,
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
        "architecture_memory",
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


def _setup_roadmap_recommendation_repo(tmp_path: Path) -> None:
    from pcae.commands.init import init_harness

    initialize_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n"
        "## Current Phase\n\n"
        "Phase 36A: Governed roadmap recommendation.\n\n"
        "## Current State\n\n"
        "PCAE can recommend the next governed roadmap phase.\n\n"
        "## Next\n\n"
        "- Continue governed roadmap work.\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "TODO.md").write_text(
        "# TODO\n\n"
        "## Pending\n\n"
        "- Implement `pcae orchestration select`: given a task type, return the recommended agent from policy.\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# DONE\n\n- Added previous governed roadmap work.\n",
        encoding="utf-8",
    )
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "20260527-1200-test.md").write_text(
        "# Task Contract\n\n"
        "## Task ID\n\n20260527-1200-test\n\n"
        "## Title\n\nTest task\n\n"
        "## Status\n\nactive\n\n"
        "## Mode\n\nimplementation\n\n"
        "## Goal\n\nImplement governed roadmap recommendations.\n",
        encoding="utf-8",
    )
    pcae_dir = tmp_path / ".pcae"
    (pcae_dir / "session.json").write_text(
        json.dumps(
            {
                "active_task": {"id": "20260527-1200-test", "title": "Test task"},
                "current_objective": "Implement governed roadmap recommendations.",
                "next_recommended_step": "Run validation.",
            }
        ),
        encoding="utf-8",
    )
    (pcae_dir / "provenance-history.json").write_text("[]\n", encoding="utf-8")
    commit_governance_baseline(tmp_path)


def test_roadmap_next_recommendation_ready_uses_first_pending_todo(
    tmp_path: Path,
) -> None:
    _setup_roadmap_recommendation_repo(tmp_path)
    result = recommend_next_roadmap_phase(HarnessPath(tmp_path))
    assert result.recommendation_status == "ready"
    assert result.recommended_phase.startswith("Implement `pcae orchestration select`")
    assert result.blockers == ()


def test_roadmap_next_recommendation_advisory(tmp_path: Path) -> None:
    _setup_roadmap_recommendation_repo(tmp_path)
    result = recommend_next_roadmap_phase(HarnessPath(tmp_path))
    assert result.advisory == ROADMAP_RECOMMENDATION_ADVISORY


def test_roadmap_next_recommendation_to_dict_shape(tmp_path: Path) -> None:
    _setup_roadmap_recommendation_repo(tmp_path)
    data = recommend_next_roadmap_phase(HarnessPath(tmp_path)).to_dict()
    assert set(data) == {
        "recommendation_status",
        "recommended_phase",
        "rationale",
        "readiness_factors",
        "blockers",
        "roadmap_sequence",
        "predicted_phases",
        "advisory",
    }
    assert isinstance(data["readiness_factors"], list)
    assert isinstance(data["blockers"], list)
    assert isinstance(data["roadmap_sequence"], list)
    assert isinstance(data["predicted_phases"], list)


def test_roadmap_next_always_includes_roadmap_sequence(tmp_path: Path) -> None:
    _setup_roadmap_recommendation_repo(tmp_path)
    result = recommend_next_roadmap_phase(HarnessPath(tmp_path))
    assert result.roadmap_sequence == ROADMAP_SEQUENCE
    assert "Option B — Architecture Memory" in result.roadmap_sequence
    assert "Option C — Multi-Agent Collaboration" in result.roadmap_sequence
    assert "Remote Coding" in result.roadmap_sequence


def _setup_roadmap_no_todos_repo(tmp_path: Path) -> None:
    from pcae.commands.init import init_harness

    initialize_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n"
        "## Current Phase\n\n"
        "Phase 36E: Roadmap awareness for predicted phases.\n\n"
        "## Current State\n\n"
        "PCAE is aware of the agreed high-level roadmap.\n\n"
        "## Next\n\n"
        "- Continue governed roadmap work.\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "DONE.md").write_text(
        "# DONE\n\n- Added previous governed roadmap work.\n",
        encoding="utf-8",
    )
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "20260527-1200-test.md").write_text(
        "# Task Contract\n\n"
        "## Task ID\n\n20260527-1200-test\n\n"
        "## Title\n\nTest task\n\n"
        "## Status\n\nactive\n\n"
        "## Mode\n\nimplementation\n\n"
        "## Goal\n\nImplement roadmap awareness.\n",
        encoding="utf-8",
    )
    pcae_dir = tmp_path / ".pcae"
    (pcae_dir / "session.json").write_text(
        json.dumps(
            {
                "active_task": {"id": "20260527-1200-test", "title": "Test task"},
                "current_objective": "Implement roadmap awareness.",
                "next_recommended_step": "Run validation.",
            }
        ),
        encoding="utf-8",
    )
    (pcae_dir / "provenance-history.json").write_text("[]\n", encoding="utf-8")
    commit_governance_baseline(tmp_path)


def test_roadmap_next_no_todos_references_option_c(tmp_path: Path) -> None:
    _setup_roadmap_no_todos_repo(tmp_path)
    result = recommend_next_roadmap_phase(HarnessPath(tmp_path))
    assert result.recommendation_status == "ready"
    assert result.recommended_phase == PREDICTED_PHASES_OPTION_C[0]
    assert result.predicted_phases == PREDICTED_PHASES_OPTION_C
    assert "Remote Coding" in result.rationale


def test_roadmap_next_with_todos_has_empty_predicted_phases(tmp_path: Path) -> None:
    _setup_roadmap_recommendation_repo(tmp_path)
    result = recommend_next_roadmap_phase(HarnessPath(tmp_path))
    assert result.recommendation_status == "ready"
    assert result.predicted_phases == ()


def test_cli_roadmap_next_no_todos_json_includes_roadmap_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _setup_roadmap_no_todos_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["roadmap", "next", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "recommendation_status" in data
    assert "recommended_phase" in data
    assert "current_track" in data
    assert "recommendation_source" in data
    assert "41C" not in data["recommended_phase"]


def test_cli_roadmap_next_no_todos_human_output_includes_sequence(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _setup_roadmap_no_todos_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["roadmap", "next"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governed roadmap recommendation" in output
    assert "Current phase:" in output
    assert "41C" not in output


def test_cli_roadmap_next_human_output(tmp_path: Path, monkeypatch, capsys) -> None:
    _setup_roadmap_recommendation_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["roadmap", "next"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governed roadmap recommendation" in output
    assert "Current phase:" in output
    assert "41C" not in output


def test_cli_roadmap_next_json_output(tmp_path: Path, monkeypatch, capsys) -> None:
    _setup_roadmap_recommendation_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["roadmap", "next", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "recommendation_status" in data
    assert "recommended_phase" in data
    assert "current_track" in data
    assert "roadmap_evolution" in data
    assert "41C" not in data["recommended_phase"]


def test_cli_roadmap_next_does_not_modify_artifacts(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _setup_roadmap_recommendation_repo(tmp_path)
    watched = [
        tmp_path / "PROJECT_STATUS.md",
        tmp_path / "tasks" / "TODO.md",
        tmp_path / "tasks" / "DONE.md",
        tmp_path / ".pcae" / "session.json",
        tmp_path / ".pcae" / "provenance-history.json",
    ]
    before = {path: path.read_text(encoding="utf-8") for path in watched}
    monkeypatch.chdir(tmp_path)
    assert main(["roadmap", "next"]) == 0
    capsys.readouterr()
    after = {path: path.read_text(encoding="utf-8") for path in watched}
    assert after == before


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
    assert result.operational_stale_references == ()
    assert result.preserved_historical_references == ()


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
    assert len(result.operational_stale_references) >= 1
    assert any("Implement `pcae end`" in ref for ref in result.operational_stale_references)


def test_stale_references_detected_in_todo(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Implement `pcae end` command."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    stale_in_todo = [r for r in result.operational_stale_references if "tasks/TODO.md" in r]
    assert len(stale_in_todo) >= 1


def test_stale_references_detected_in_changelog(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    stale_in_changelog = [r for r in result.preserved_historical_references if "CHANGELOG.md" in r]
    assert len(stale_in_changelog) >= 1


def test_stale_references_detected_in_done(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        done_entries=["Implement `pcae end` was added."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    stale_in_done = [r for r in result.preserved_historical_references if "tasks/DONE.md" in r]
    assert len(stale_in_done) >= 1


# ---------------------------------------------------------------------------
# Core: historical artifact awareness — synchronized semantics
# ---------------------------------------------------------------------------


def test_historical_stale_ref_does_not_make_out_of_sync(tmp_path: Path) -> None:
    # CHANGELOG.md stale reference should NOT cause out-of-sync
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.synchronized is True


def test_done_stale_ref_does_not_make_out_of_sync(tmp_path: Path) -> None:
    # tasks/DONE.md stale reference should NOT cause out-of-sync
    _write_sync_artifacts(
        tmp_path,
        done_entries=["Implement `pcae end` was added."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert result.synchronized is True


def test_operational_stale_ref_makes_out_of_sync(tmp_path: Path) -> None:
    # PROJECT_STATUS.md stale reference SHOULD cause out-of-sync
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
    assert result.synchronized is False


def test_historical_stale_ref_goes_to_preserved_field(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
        done_entries=["Implement `pcae end` was added."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert len(result.preserved_historical_references) >= 1
    assert result.operational_stale_references == ()


def test_operational_stale_ref_goes_to_operational_field(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Implement `pcae end` command."],
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert len(result.operational_stale_references) >= 1


def test_mixed_stale_refs_split_correctly(tmp_path: Path) -> None:
    # PROJECT_STATUS.md + CHANGELOG.md both have stale phrases
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n"
        "## Next\n\n- Implement `pcae end`.\n",
        encoding="utf-8",
    )
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TODO.md").write_text("# TODO\n\n## Pending\n", encoding="utf-8")
    (tasks_dir / "DONE.md").write_text("# DONE\n\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## Unreleased\n\n- Implement `pcae end` released.\n",
        encoding="utf-8",
    )
    result = check_governance_sync(HarnessPath(tmp_path))
    assert len(result.operational_stale_references) >= 1
    assert len(result.preserved_historical_references) >= 1
    assert result.synchronized is False  # operational ref present


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
        "operational_stale_references",
        "preserved_historical_references",
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
    assert isinstance(d["operational_stale_references"], list)
    assert isinstance(d["preserved_historical_references"], list)
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
    assert result.operational_stale_references == ()
    assert result.preserved_historical_references == ()
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
    assert "Operational stale references:" in captured.out
    assert "Preserved historical references:" in captured.out


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
        "operational_stale_references",
        "preserved_historical_references",
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
    assert data["operational_stale_references"] == []
    assert data["preserved_historical_references"] == []
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
    assert len(data["operational_stale_references"]) >= 1


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
# CLI: Phase 35Q — historical artifact awareness in sync-check output
# ---------------------------------------------------------------------------


def test_cli_sync_check_historical_ref_shows_synchronized(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    assert "synchronized" in captured.out.lower()
    assert "out of sync" not in captured.out.lower()


def test_cli_sync_check_historical_ref_appears_in_preserved_section(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    assert "Preserved historical references:" in captured.out
    assert "Implement `pcae end`" in captured.out


def test_cli_sync_check_historical_ref_not_in_operational_section(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check"])
    captured = capsys.readouterr()
    # Operational section should be empty
    lines = captured.out.splitlines()
    op_section_idx = next(
        (i for i, l in enumerate(lines) if "Operational stale references:" in l), -1
    )
    assert op_section_idx >= 0
    next_section_idx = next(
        (i for i, l in enumerate(lines) if i > op_section_idx and l.startswith(("P", "C", "I", "G", "S"))),
        len(lines),
    )
    op_content = lines[op_section_idx + 1 : next_section_idx]
    assert any("none" in line.lower() for line in op_content)


def test_cli_sync_check_json_historical_ref_synchronized(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["synchronized"] is True


def test_cli_sync_check_json_historical_ref_in_preserved_field(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data["preserved_historical_references"]) >= 1
    assert any("Implement `pcae end`" in r for r in data["preserved_historical_references"])


def test_cli_sync_check_json_historical_ref_not_in_operational_field(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["operational_stale_references"] == []


def test_cli_sync_check_json_operational_ref_not_synchronized(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # PROJECT_STATUS.md is operational — should still make out of sync
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
    assert len(data["operational_stale_references"]) >= 1


def test_cli_sync_check_json_no_stale_refs_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # Old key 'stale_references' must not appear in JSON output
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-check", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "stale_references" not in data


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
    ArtifactClassification,
    GovernanceSyncRepairPreview,
    SyncRepairEntry,
    classify_governance_artifact,
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
    assert repair.proposed_action == "remove"
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
    # PROJECT_STATUS.md is operational → proposed_action is "update" (not "remove")
    stale_repairs = [
        r for r in result.proposed_repairs
        if r.proposed_action == "update" and r.artifact == "PROJECT_STATUS.md"
    ]
    assert len(stale_repairs) >= 1
    assert any("pcae end" in r.stale_entry for r in stale_repairs)


def test_plan_governance_sync_repairs_proposed_actions_are_valid(
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
    valid_actions = {"remove", "update", "relocate", "preserve", "mark_superseded"}
    for repair in result.proposed_repairs:
        assert repair.proposed_action in valid_actions


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
    assert repair.proposed_action == "update"
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
    for key in ("artifact", "artifact_type", "stale_entry", "proposed_action", "rationale"):
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
    assert "update" in output


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


def test_cli_governance_sync_repair_no_flags_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "sync-repair"])
    assert result != 0


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
    assert repair["proposed_action"] == "remove"
    assert repair["artifact_type"] == "operational"
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
    # PROJECT_STATUS.md is operational → action is "update", not "remove"
    ps_repairs = [r for r in data["proposed_repairs"] if r["artifact"] == "PROJECT_STATUS.md"]
    assert len(ps_repairs) >= 1
    assert all(r["proposed_action"] == "update" for r in ps_repairs)
    assert all(r["artifact_type"] == "operational" for r in ps_repairs)


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
    for key in ("artifact", "artifact_type", "stale_entry", "proposed_action", "rationale"):
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


# ---------------------------------------------------------------------------
# Phase 35O: artifact-type-aware governance sync repair semantics
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Core: artifact type classification
# ---------------------------------------------------------------------------


def test_classify_changelog_is_historical(tmp_path: Path) -> None:
    assert classify_governance_artifact("CHANGELOG.md").artifact_class == "historical"


def test_classify_done_is_historical(tmp_path: Path) -> None:
    assert classify_governance_artifact("tasks/DONE.md").artifact_class == "historical"


def test_classify_todo_is_operational(tmp_path: Path) -> None:
    assert classify_governance_artifact("tasks/TODO.md").artifact_class == "operational"


def test_classify_project_status_is_operational(tmp_path: Path) -> None:
    assert classify_governance_artifact("PROJECT_STATUS.md").artifact_class == "operational"


# ---------------------------------------------------------------------------
# Phase 35R: governance artifact lifecycle classification
# ---------------------------------------------------------------------------


def test_classify_returns_artifact_classification(tmp_path: Path) -> None:
    result = classify_governance_artifact("PROJECT_STATUS.md")
    assert isinstance(result, ArtifactClassification)


def test_classify_provenance_history_is_runtime(tmp_path: Path) -> None:
    result = classify_governance_artifact(".pcae/provenance-history.json")
    assert result.artifact_class == "runtime"


def test_classify_agent_lock_is_runtime(tmp_path: Path) -> None:
    result = classify_governance_artifact(".pcae/agent-lock.json")
    assert result.artifact_class == "runtime"


def test_classify_session_json_is_runtime(tmp_path: Path) -> None:
    result = classify_governance_artifact(".pcae/session.json")
    assert result.artifact_class == "runtime"


def test_classify_runtime_snapshot_is_generated(tmp_path: Path) -> None:
    result = classify_governance_artifact(".pcae/runtime-snapshots/foo.json")
    assert result.artifact_class == "generated"


def test_classify_context_pack_is_generated(tmp_path: Path) -> None:
    result = classify_governance_artifact(".pcae/context-packs/bar.json")
    assert result.artifact_class == "generated"


def test_classify_continuity_pack_is_generated(tmp_path: Path) -> None:
    result = classify_governance_artifact(".pcae/continuity-packs/baz.json")
    assert result.artifact_class == "generated"


def test_classify_unknown_artifact_defaults_to_operational(tmp_path: Path) -> None:
    result = classify_governance_artifact("unknown/artifact.md")
    assert result.artifact_class == "operational"


def test_classify_preserves_artifact_type_path(tmp_path: Path) -> None:
    result = classify_governance_artifact("tasks/TODO.md")
    assert result.artifact_type == "tasks/TODO.md"


def test_classify_all_known_artifacts_have_governance_role(tmp_path: Path) -> None:
    known = [
        "PROJECT_STATUS.md",
        "tasks/TODO.md",
        "CHANGELOG.md",
        "tasks/DONE.md",
        ".pcae/provenance-history.json",
        ".pcae/agent-lock.json",
        ".pcae/session.json",
        ".pcae/runtime-snapshots/snap.json",
        ".pcae/context-packs/ctx.json",
        ".pcae/continuity-packs/cont.json",
    ]
    for artifact in known:
        result = classify_governance_artifact(artifact)
        assert result.governance_role, f"governance_role empty for {artifact}"


def test_classify_to_dict_has_required_keys(tmp_path: Path) -> None:
    result = classify_governance_artifact("CHANGELOG.md")
    d = result.to_dict()
    assert "artifact_type" in d
    assert "artifact_class" in d
    assert "governance_role" in d


def test_classify_historical_governance_role_mentions_preserved(tmp_path: Path) -> None:
    for artifact in ("CHANGELOG.md", "tasks/DONE.md"):
        result = classify_governance_artifact(artifact)
        assert "preserved" in result.governance_role


def test_classify_runtime_governance_role_mentions_not_proposed(tmp_path: Path) -> None:
    for artifact in (
        ".pcae/provenance-history.json",
        ".pcae/agent-lock.json",
        ".pcae/session.json",
    ):
        result = classify_governance_artifact(artifact)
        assert "not proposed" in result.governance_role


def test_sync_repair_entry_to_dict_includes_artifact_class(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae class field` command."],
        done_entries=["Added `pcae class field`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    todo_repairs = [r for r in result.proposed_repairs if r.artifact == "tasks/TODO.md"]
    assert todo_repairs
    d = todo_repairs[0].to_dict()
    assert "artifact_class" in d
    assert d["artifact_class"] == "operational"


def test_sync_repair_entry_to_dict_includes_governance_role(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae role field` command."],
        done_entries=["Added `pcae role field`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    todo_repairs = [r for r in result.proposed_repairs if r.artifact == "tasks/TODO.md"]
    assert todo_repairs
    d = todo_repairs[0].to_dict()
    assert "governance_role" in d
    assert d["governance_role"]


def test_sync_repair_historical_artifact_class_is_historical(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    changelog_repairs = [r for r in result.proposed_repairs if r.artifact == "CHANGELOG.md"]
    assert changelog_repairs
    d = changelog_repairs[0].to_dict()
    assert d["artifact_class"] == "historical"
    assert d["governance_role"]


def test_sync_repair_runtime_artifacts_not_proposed_for_repair(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    runtime_repairs = [
        r for r in result.proposed_repairs
        if r.artifact in (
            ".pcae/provenance-history.json",
            ".pcae/agent-lock.json",
            ".pcae/session.json",
        )
    ]
    assert runtime_repairs == []


def test_sync_repair_generated_artifacts_not_proposed_for_repair(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    generated_repairs = [
        r for r in result.proposed_repairs
        if r.artifact.startswith(".pcae/runtime-snapshots/")
        or r.artifact.startswith(".pcae/context-packs/")
        or r.artifact.startswith(".pcae/continuity-packs/")
    ]
    assert generated_repairs == []


def test_cli_governance_sync_repair_human_mentions_runtime_generated(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "runtime" in output.lower() or "generated" in output.lower()


def test_cli_governance_sync_repair_json_includes_artifact_class_in_repairs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae json class` command."],
        done_entries=["Added `pcae json class`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["proposed_repairs"]
    for repair in data["proposed_repairs"]:
        assert "artifact_class" in repair


def test_cli_governance_sync_repair_json_includes_governance_role_in_repairs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae json role` command."],
        done_entries=["Added `pcae json role`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["proposed_repairs"]
    for repair in data["proposed_repairs"]:
        assert "governance_role" in repair
        assert repair["governance_role"]


# ---------------------------------------------------------------------------
# Core: SyncRepairEntry has artifact_type field
# ---------------------------------------------------------------------------


def test_sync_repair_entry_has_artifact_type_field(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae field test` command."],
        done_entries=["Added `pcae field test`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    for repair in result.proposed_repairs:
        assert hasattr(repair, "artifact_type")


def test_sync_repair_entry_artifact_type_is_string(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae type str` command."],
        done_entries=["Added `pcae type str`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    for repair in result.proposed_repairs:
        assert isinstance(repair.artifact_type, str)


def test_sync_repair_entry_artifact_type_values_are_known(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae type val` command."],
        done_entries=["Added `pcae type val`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    for repair in result.proposed_repairs:
        assert repair.artifact_type in ("operational", "historical")


# ---------------------------------------------------------------------------
# Core: TODO entries — operational, action: remove
# ---------------------------------------------------------------------------


def test_plan_sync_repairs_todo_entry_is_operational(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae oper type` command."],
        done_entries=["Added `pcae oper type`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    todo_repairs = [r for r in result.proposed_repairs if r.artifact == "tasks/TODO.md"]
    assert todo_repairs
    for repair in todo_repairs:
        assert repair.artifact_type == "operational"


def test_plan_sync_repairs_todo_entry_action_is_remove(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae todo remove` command."],
        done_entries=["Added `pcae todo remove`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    todo_repairs = [r for r in result.proposed_repairs if r.artifact == "tasks/TODO.md"]
    assert todo_repairs
    for repair in todo_repairs:
        assert repair.proposed_action == "remove"


# ---------------------------------------------------------------------------
# Core: PROJECT_STATUS.md — operational, stale refs action: update
# ---------------------------------------------------------------------------


def test_plan_sync_repairs_project_status_stale_ref_is_update(
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
    ps_stale = [
        r for r in result.proposed_repairs
        if r.artifact == "PROJECT_STATUS.md"
    ]
    assert ps_stale
    for repair in ps_stale:
        assert repair.proposed_action == "update"
        assert repair.artifact_type == "operational"


def test_plan_sync_repairs_inconsistent_roadmap_is_update(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        next_items=["Add `pcae roadmap update` feature."],
        done_entries=["Added `pcae roadmap update`."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    ps_repairs = [r for r in result.proposed_repairs if r.artifact == "PROJECT_STATUS.md"]
    assert ps_repairs
    for repair in ps_repairs:
        assert repair.proposed_action == "update"
        assert repair.artifact_type == "operational"


# ---------------------------------------------------------------------------
# Core: CHANGELOG.md — historical, action: preserve (never remove)
# ---------------------------------------------------------------------------


def test_plan_sync_repairs_changelog_stale_ref_is_preserve(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    changelog_repairs = [
        r for r in result.proposed_repairs if r.artifact == "CHANGELOG.md"
    ]
    assert changelog_repairs
    for repair in changelog_repairs:
        assert repair.proposed_action == "preserve"
        assert repair.artifact_type == "historical"


def test_plan_sync_repairs_changelog_action_is_never_remove(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    changelog_repairs = [
        r for r in result.proposed_repairs if r.artifact == "CHANGELOG.md"
    ]
    assert changelog_repairs
    for repair in changelog_repairs:
        assert repair.proposed_action != "remove"


# ---------------------------------------------------------------------------
# Core: tasks/DONE.md — historical, action: preserve (never remove)
# ---------------------------------------------------------------------------


def test_plan_sync_repairs_done_stale_ref_is_preserve(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        done_entries=["Implement `pcae end` was added."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    done_repairs = [r for r in result.proposed_repairs if r.artifact == "tasks/DONE.md"]
    assert done_repairs
    for repair in done_repairs:
        assert repair.proposed_action == "preserve"
        assert repair.artifact_type == "historical"


def test_plan_sync_repairs_done_action_is_never_remove(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        done_entries=["Implement `pcae end` was added."],
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    done_repairs = [r for r in result.proposed_repairs if r.artifact == "tasks/DONE.md"]
    assert done_repairs
    for repair in done_repairs:
        assert repair.proposed_action != "remove"


# ---------------------------------------------------------------------------
# Core: mixed scenario — correct types assigned per artifact
# ---------------------------------------------------------------------------


def test_plan_sync_repairs_mixed_scenario_types(tmp_path: Path) -> None:
    """
    Stale phrase in CHANGELOG.md → preserve/historical.
    Completed TODO entry → remove/operational.
    Stale phrase in PROJECT_STATUS.md → update/operational.
    """
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase Test.\n\n"
        "## Next\n\n- Implement `pcae end`.\n",
        encoding="utf-8",
    )
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TODO.md").write_text(
        "# TODO\n\n## Pending\n\n- Add `pcae mixed cmd` command.\n",
        encoding="utf-8",
    )
    (tasks_dir / "DONE.md").write_text(
        "# DONE\n\n- Added `pcae mixed cmd`.\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n- Implement `pcae end` was done.\n",
        encoding="utf-8",
    )
    result = plan_governance_sync_repairs(HarnessPath(tmp_path))
    by_artifact = {r.artifact: r for r in result.proposed_repairs}

    assert "tasks/TODO.md" in by_artifact
    assert by_artifact["tasks/TODO.md"].proposed_action == "remove"
    assert by_artifact["tasks/TODO.md"].artifact_type == "operational"

    assert "PROJECT_STATUS.md" in by_artifact
    assert by_artifact["PROJECT_STATUS.md"].proposed_action == "update"
    assert by_artifact["PROJECT_STATUS.md"].artifact_type == "operational"

    assert "CHANGELOG.md" in by_artifact
    assert by_artifact["CHANGELOG.md"].proposed_action == "preserve"
    assert by_artifact["CHANGELOG.md"].artifact_type == "historical"


# ---------------------------------------------------------------------------
# CLI human: repair semantics section and user authority
# ---------------------------------------------------------------------------


def test_cli_governance_sync_repair_human_shows_repair_semantics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "Repair semantics:" in output


def test_cli_governance_sync_repair_human_mentions_operational(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "operational" in output.lower()


def test_cli_governance_sync_repair_human_mentions_historical(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "historical" in output.lower()


def test_cli_governance_sync_repair_human_mentions_user_authority(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "authoritative" in output.lower()


def test_cli_governance_sync_repair_human_shows_proposed_action_label(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae proposed label` command."],
        done_entries=["Added `pcae proposed label`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "Proposed action:" in output


def test_cli_governance_sync_repair_human_shows_artifact_type_in_repair(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae type display` command."],
        done_entries=["Added `pcae type display`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    # Artifact line shows artifact type in parentheses
    assert "operational" in output


def test_cli_governance_sync_repair_human_historical_shows_preserve(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "preserve" in output
    assert "historical" in output


# ---------------------------------------------------------------------------
# CLI JSON: artifact_type field in each repair entry
# ---------------------------------------------------------------------------


def test_cli_governance_sync_repair_json_includes_artifact_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae json art` command."],
        done_entries=["Added `pcae json art`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    for repair in data["proposed_repairs"]:
        assert "artifact_type" in repair


def test_cli_governance_sync_repair_json_todo_is_operational_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae json oper` command."],
        done_entries=["Added `pcae json oper`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    todo_repairs = [r for r in data["proposed_repairs"] if r["artifact"] == "tasks/TODO.md"]
    assert todo_repairs
    for repair in todo_repairs:
        assert repair["artifact_type"] == "operational"


def test_cli_governance_sync_repair_json_changelog_is_historical_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    changelog_repairs = [
        r for r in data["proposed_repairs"] if r["artifact"] == "CHANGELOG.md"
    ]
    assert changelog_repairs
    for repair in changelog_repairs:
        assert repair["artifact_type"] == "historical"
        assert repair["proposed_action"] == "preserve"


def test_cli_governance_sync_repair_json_done_is_historical_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        done_entries=["Implement `pcae end` was added."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    done_repairs = [
        r for r in data["proposed_repairs"] if r["artifact"] == "tasks/DONE.md"
    ]
    assert done_repairs
    for repair in done_repairs:
        assert repair["artifact_type"] == "historical"
        assert repair["proposed_action"] == "preserve"


def test_cli_governance_sync_repair_json_historical_artifacts_never_remove(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Old entry mentioning Implement `pcae end` feature."],
        done_entries=["Implement `pcae end` was added."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    historical_repairs = [
        r for r in data["proposed_repairs"] if r["artifact_type"] == "historical"
    ]
    assert historical_repairs
    for repair in historical_repairs:
        assert repair["proposed_action"] != "remove"


def test_cli_governance_sync_repair_json_uses_proposed_action_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae key name` command."],
        done_entries=["Added `pcae key name`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["proposed_repairs"]
    repair = data["proposed_repairs"][0]
    assert "proposed_action" in repair
    assert "action" not in repair


# ---------------------------------------------------------------------------
# Core: apply_governance_sync_repairs — imports
# ---------------------------------------------------------------------------

from pcae.core.status import (
    AppliedSyncRepairResult,
    apply_governance_sync_repairs,
)


# ---------------------------------------------------------------------------
# Core: apply_governance_sync_repairs — return type
# ---------------------------------------------------------------------------


def test_apply_governance_sync_repairs_returns_result(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = apply_governance_sync_repairs(HarnessPath(tmp_path))
    assert isinstance(result, AppliedSyncRepairResult)


# ---------------------------------------------------------------------------
# Core: apply_governance_sync_repairs — no-op when no applicable repairs
# ---------------------------------------------------------------------------


def test_apply_governance_sync_repairs_noop_when_no_repairs(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = apply_governance_sync_repairs(HarnessPath(tmp_path))
    assert result.no_op is True
    assert result.applied_repairs == ()


def test_apply_governance_sync_repairs_noop_when_only_historical(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        changelog_entries=["Implement `pcae end`."],
    )
    result = apply_governance_sync_repairs(HarnessPath(tmp_path))
    assert result.no_op is True
    assert result.applied_repairs == ()


# ---------------------------------------------------------------------------
# Core: apply_governance_sync_repairs — removes completed TODO entry
# ---------------------------------------------------------------------------


def test_apply_governance_sync_repairs_removes_completed_todo(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae rm check` command.", "Add `pcae keep` command."],
        done_entries=["Added `pcae rm check`."],
    )
    apply_governance_sync_repairs(HarnessPath(tmp_path))
    todo_text = (tmp_path / "tasks" / "TODO.md").read_text(encoding="utf-8")
    assert "pcae rm check" not in todo_text
    assert "pcae keep" in todo_text


def test_apply_governance_sync_repairs_applied_repairs_nonempty(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae rm check` command."],
        done_entries=["Added `pcae rm check`."],
    )
    result = apply_governance_sync_repairs(HarnessPath(tmp_path))
    assert result.no_op is False
    assert len(result.applied_repairs) == 1


def test_apply_governance_sync_repairs_no_op_is_false_when_applied(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae noop flag` command."],
        done_entries=["Added `pcae noop flag`."],
    )
    result = apply_governance_sync_repairs(HarnessPath(tmp_path))
    assert result.no_op is False


# ---------------------------------------------------------------------------
# Core: apply_governance_sync_repairs — historical artifacts not modified
# ---------------------------------------------------------------------------


def test_apply_governance_sync_repairs_preserves_changelog(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae hist check` command."],
        done_entries=["Added `pcae hist check`."],
        changelog_entries=["Added `pcae hist check`."],
    )
    changelog_before = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    apply_governance_sync_repairs(HarnessPath(tmp_path))
    changelog_after = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog_before == changelog_after


def test_apply_governance_sync_repairs_preserves_done(tmp_path: Path) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae hist done` command."],
        done_entries=["Added `pcae hist done`."],
    )
    done_before = (tmp_path / "tasks" / "DONE.md").read_text(encoding="utf-8")
    apply_governance_sync_repairs(HarnessPath(tmp_path))
    done_after = (tmp_path / "tasks" / "DONE.md").read_text(encoding="utf-8")
    assert done_before == done_after


# ---------------------------------------------------------------------------
# Core: apply_governance_sync_repairs — sync-check convergence
# ---------------------------------------------------------------------------


def test_apply_governance_sync_repairs_sync_check_no_longer_reports_entry(
    tmp_path: Path,
) -> None:
    from pcae.core.status import check_governance_sync

    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae conv check` command."],
        done_entries=["Added `pcae conv check`."],
    )
    before = check_governance_sync(HarnessPath(tmp_path))
    assert len(before.completed_todo_entries) == 1

    apply_governance_sync_repairs(HarnessPath(tmp_path))

    after = check_governance_sync(HarnessPath(tmp_path))
    assert len(after.completed_todo_entries) == 0


# ---------------------------------------------------------------------------
# Core: apply_governance_sync_repairs — to_dict shape
# ---------------------------------------------------------------------------


def test_apply_governance_sync_repairs_to_dict_keys(tmp_path: Path) -> None:
    _write_sync_artifacts(tmp_path)
    result = apply_governance_sync_repairs(HarnessPath(tmp_path))
    d = result.to_dict()
    assert "applied_repairs" in d
    assert "no_op" in d


# ---------------------------------------------------------------------------
# CLI: pcae governance sync-repair (no flags) — fails clearly
# ---------------------------------------------------------------------------


def test_cli_governance_sync_repair_no_flags_exits_nonzero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "sync-repair"])
    assert result != 0


def test_cli_governance_sync_repair_no_flags_prints_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair"])
    output = capsys.readouterr().out
    assert "Error" in output or "error" in output.lower()


def test_cli_governance_sync_repair_no_flags_mentions_dry_run(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair"])
    output = capsys.readouterr().out
    assert "--dry-run" in output


def test_cli_governance_sync_repair_no_flags_mentions_force(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair"])
    output = capsys.readouterr().out
    assert "--force" in output


# ---------------------------------------------------------------------------
# CLI: pcae governance sync-repair --force — applies repairs
# ---------------------------------------------------------------------------


def test_cli_governance_sync_repair_force_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "sync-repair", "--force"])
    assert result == 0


def test_cli_governance_sync_repair_force_removes_stale_todo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae force cmd` command."],
        done_entries=["Added `pcae force cmd`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--force"])
    todo_text = (tmp_path / "tasks" / "TODO.md").read_text(encoding="utf-8")
    assert "pcae force cmd" not in todo_text


def test_cli_governance_sync_repair_force_prints_applied(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae force print` command."],
        done_entries=["Added `pcae force print`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--force"])
    output = capsys.readouterr().out
    assert "Applied" in output or "applied" in output.lower()


def test_cli_governance_sync_repair_force_noop_message_when_no_repairs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--force"])
    output = capsys.readouterr().out
    assert "no operational repairs" in output.lower() or "no-op" in output.lower() or "no op" in output.lower()


def test_cli_governance_sync_repair_force_noop_preserves_historical_message(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--force"])
    output = capsys.readouterr().out
    assert "historical" in output.lower()


def test_cli_governance_sync_repair_force_json_has_applied_repairs_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae force json` command."],
        done_entries=["Added `pcae force json`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--force", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "applied_repairs" in data
    assert "no_op" in data


def test_cli_governance_sync_repair_force_json_applied_repairs_nonempty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae force json2` command."],
        done_entries=["Added `pcae force json2`."],
    )
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--force", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["applied_repairs"]
    assert data["no_op"] is False


# ---------------------------------------------------------------------------
# CLI: pcae governance sync-repair --dry-run — unchanged behavior
# ---------------------------------------------------------------------------


def test_cli_governance_sync_repair_dry_run_still_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "sync-repair", "--dry-run"])
    assert result == 0


def test_cli_governance_sync_repair_dry_run_still_shows_preview_header(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    output = capsys.readouterr().out
    assert "Governance synchronization repair preview" in output


def test_cli_governance_sync_repair_dry_run_does_not_modify_todo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_sync_artifacts(
        tmp_path,
        todo_pending=["Add `pcae dry check` command."],
        done_entries=["Added `pcae dry check`."],
    )
    todo_path = tmp_path / "tasks" / "TODO.md"
    mtime_before = todo_path.stat().st_mtime
    monkeypatch.chdir(tmp_path)
    main(["governance", "sync-repair", "--dry-run"])
    assert todo_path.stat().st_mtime == mtime_before


# ---------------------------------------------------------------------------
# Phase 35S: governance artifact classification registry
# ---------------------------------------------------------------------------

from pcae.core.status import (
    ARTIFACT_CLASSIFICATION_ADVISORY,
    GOVERNANCE_ARTIFACT_REGISTRY,
    GovernanceArtifactEntry,
    GovernanceArtifactReport,
    build_governance_artifact_registry,
)


# ---------------------------------------------------------------------------
# Core: build_governance_artifact_registry — return type and shape
# ---------------------------------------------------------------------------


def test_build_governance_artifact_registry_returns_report(tmp_path: Path) -> None:
    result = build_governance_artifact_registry()
    assert isinstance(result, GovernanceArtifactReport)


def test_build_governance_artifact_registry_advisory(tmp_path: Path) -> None:
    result = build_governance_artifact_registry()
    assert result.advisory == ARTIFACT_CLASSIFICATION_ADVISORY


def test_build_governance_artifact_registry_has_artifacts(tmp_path: Path) -> None:
    result = build_governance_artifact_registry()
    assert len(result.artifacts) == 11


def test_build_governance_artifact_registry_has_four_classes(tmp_path: Path) -> None:
    result = build_governance_artifact_registry()
    assert set(result.classes) == {"operational", "historical", "runtime", "generated"}


def test_build_governance_artifact_registry_classes_ordered_by_first_appearance(
    tmp_path: Path,
) -> None:
    result = build_governance_artifact_registry()
    assert list(result.classes) == ["operational", "historical", "runtime", "generated"]


# ---------------------------------------------------------------------------
# Core: GOVERNANCE_ARTIFACT_REGISTRY — all 11 entries present
# ---------------------------------------------------------------------------


def test_governance_registry_contains_project_status(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert "PROJECT_STATUS.md" in paths


def test_governance_registry_contains_todo(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert "tasks/TODO.md" in paths


def test_governance_registry_contains_changelog(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert "CHANGELOG.md" in paths


def test_governance_registry_contains_done(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert "tasks/DONE.md" in paths


def test_governance_registry_contains_provenance_history(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert ".pcae/provenance-history.json" in paths


def test_governance_registry_contains_agent_lock(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert ".pcae/agent-lock.json" in paths


def test_governance_registry_contains_session_json(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert ".pcae/session.json" in paths


def test_governance_registry_contains_runtime_snapshots_pattern(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert ".pcae/runtime-snapshots/**" in paths


def test_governance_registry_contains_context_packs_pattern(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert ".pcae/context-packs/**" in paths


def test_governance_registry_contains_continuity_packs_pattern(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert ".pcae/continuity-packs/**" in paths


def test_governance_registry_contains_governance_exports_pattern(tmp_path: Path) -> None:
    paths = {e.path for e in GOVERNANCE_ARTIFACT_REGISTRY}
    assert ".pcae/governance-exports/**" in paths


# ---------------------------------------------------------------------------
# Core: GovernanceArtifactEntry — field semantics
# ---------------------------------------------------------------------------


def test_governance_registry_entry_is_dataclass(tmp_path: Path) -> None:
    entry = GOVERNANCE_ARTIFACT_REGISTRY[0]
    assert isinstance(entry, GovernanceArtifactEntry)


def test_governance_registry_operational_entries_have_actionable_repair(
    tmp_path: Path,
) -> None:
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        if entry.artifact_class == "operational":
            assert entry.repair_policy == "actionable"


def test_governance_registry_historical_entries_have_preserve_repair(
    tmp_path: Path,
) -> None:
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        if entry.artifact_class == "historical":
            assert entry.repair_policy == "preserve"


def test_governance_registry_runtime_entries_have_ignore_repair(
    tmp_path: Path,
) -> None:
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        if entry.artifact_class == "runtime":
            assert entry.repair_policy == "ignore"


def test_governance_registry_generated_entries_have_ignore_repair(
    tmp_path: Path,
) -> None:
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        if entry.artifact_class == "generated":
            assert entry.repair_policy == "ignore"


def test_governance_registry_operational_entries_are_tracked(tmp_path: Path) -> None:
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        if entry.artifact_class == "operational":
            assert entry.source_control_role == "tracked"


def test_governance_registry_historical_entries_are_tracked(tmp_path: Path) -> None:
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        if entry.artifact_class == "historical":
            assert entry.source_control_role == "tracked"


def test_governance_registry_runtime_entries_are_ignored(tmp_path: Path) -> None:
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        if entry.artifact_class == "runtime":
            assert entry.source_control_role == "ignored"


def test_governance_registry_generated_entries_are_generated_ignored(
    tmp_path: Path,
) -> None:
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        if entry.artifact_class == "generated":
            assert entry.source_control_role == "generated_ignored"


def test_governance_registry_all_entries_have_nonempty_governance_role(
    tmp_path: Path,
) -> None:
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        assert entry.governance_role, f"governance_role empty for {entry.path}"


# ---------------------------------------------------------------------------
# Core: GovernanceArtifactEntry.to_dict — shape
# ---------------------------------------------------------------------------


def test_governance_artifact_entry_to_dict_keys(tmp_path: Path) -> None:
    entry = GOVERNANCE_ARTIFACT_REGISTRY[0]
    d = entry.to_dict()
    assert "path" in d
    assert "artifact_class" in d
    assert "governance_role" in d
    assert "repair_policy" in d
    assert "source_control_role" in d


# ---------------------------------------------------------------------------
# Core: GovernanceArtifactReport.to_dict — shape
# ---------------------------------------------------------------------------


def test_governance_artifact_report_to_dict_keys(tmp_path: Path) -> None:
    result = build_governance_artifact_registry()
    d = result.to_dict()
    assert "artifacts" in d
    assert "classes" in d
    assert "advisory" in d


def test_governance_artifact_report_to_dict_artifacts_is_list(tmp_path: Path) -> None:
    result = build_governance_artifact_registry()
    d = result.to_dict()
    assert isinstance(d["artifacts"], list)
    assert len(d["artifacts"]) == 11


def test_governance_artifact_report_to_dict_classes_is_list(tmp_path: Path) -> None:
    result = build_governance_artifact_registry()
    d = result.to_dict()
    assert isinstance(d["classes"], list)
    assert set(d["classes"]) == {"operational", "historical", "runtime", "generated"}


# ---------------------------------------------------------------------------
# CLI: pcae governance artifacts — human output
# ---------------------------------------------------------------------------


def test_cli_governance_artifacts_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "artifacts"])
    assert result == 0


def test_cli_governance_artifacts_shows_registry_header(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts"])
    output = capsys.readouterr().out
    assert "Governance artifact registry" in output


def test_cli_governance_artifacts_shows_artifact_classes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts"])
    output = capsys.readouterr().out
    assert "operational" in output
    assert "historical" in output
    assert "runtime" in output
    assert "generated" in output


def test_cli_governance_artifacts_shows_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts"])
    output = capsys.readouterr().out
    assert ARTIFACT_CLASSIFICATION_ADVISORY in output


def test_cli_governance_artifacts_shows_repair_semantics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts"])
    output = capsys.readouterr().out
    assert "actionable" in output
    assert "preserve" in output
    assert "ignore" in output


def test_cli_governance_artifacts_shows_all_known_paths(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts"])
    output = capsys.readouterr().out
    for entry in GOVERNANCE_ARTIFACT_REGISTRY:
        assert entry.path in output


# ---------------------------------------------------------------------------
# CLI: pcae governance artifacts --json — JSON output
# ---------------------------------------------------------------------------


def test_cli_governance_artifacts_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    result = main(["governance", "artifacts", "--json"])
    assert result == 0


def test_cli_governance_artifacts_json_has_artifacts_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "artifacts" in data


def test_cli_governance_artifacts_json_has_classes_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "classes" in data


def test_cli_governance_artifacts_json_has_advisory_key(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "advisory" in data


def test_cli_governance_artifacts_json_artifacts_count(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert len(data["artifacts"]) == 11


def test_cli_governance_artifacts_json_each_artifact_has_required_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    for artifact in data["artifacts"]:
        assert "path" in artifact
        assert "artifact_class" in artifact
        assert "governance_role" in artifact
        assert "repair_policy" in artifact
        assert "source_control_role" in artifact


def test_cli_governance_artifacts_json_classes_has_four_values(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert set(data["classes"]) == {"operational", "historical", "runtime", "generated"}


def test_cli_governance_artifacts_json_historical_artifacts_have_preserve_repair(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    historical = [a for a in data["artifacts"] if a["artifact_class"] == "historical"]
    assert historical
    for artifact in historical:
        assert artifact["repair_policy"] == "preserve"


def test_cli_governance_artifacts_json_runtime_artifacts_have_ignore_repair(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    runtime = [a for a in data["artifacts"] if a["artifact_class"] == "runtime"]
    assert runtime
    for artifact in runtime:
        assert artifact["repair_policy"] == "ignore"


def test_cli_governance_artifacts_json_generated_artifacts_have_generated_ignored_scr(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    generated = [a for a in data["artifacts"] if a["artifact_class"] == "generated"]
    assert generated
    for artifact in generated:
        assert artifact["source_control_role"] == "generated_ignored"


def test_cli_governance_artifacts_json_advisory_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["advisory"] == ARTIFACT_CLASSIFICATION_ADVISORY


# ---------------------------------------------------------------------------
# Phase 35T: Governance registry consumers audit
# ---------------------------------------------------------------------------

from pcae.core.status import REGISTRY_AUDIT_ADVISORY, audit_registry_consumers


def test_registry_audit_returns_pass_status() -> None:
    result = audit_registry_consumers()
    assert result.registry_audit_status == "pass"


def test_registry_audit_reports_four_consumers() -> None:
    result = audit_registry_consumers()
    assert len(result.consumers) == 4


def test_registry_audit_all_consumers_are_registry_backed() -> None:
    result = audit_registry_consumers()
    for consumer in result.consumers:
        assert consumer.registry_backed, f"{consumer.name} is not registry-backed"


def test_registry_audit_reports_sync_check_consumer() -> None:
    result = audit_registry_consumers()
    names = {c.name for c in result.consumers}
    assert "sync-check" in names


def test_registry_audit_reports_sync_repair_consumer() -> None:
    result = audit_registry_consumers()
    names = {c.name for c in result.consumers}
    assert "sync-repair" in names


def test_registry_audit_reports_governance_audit_consumer() -> None:
    result = audit_registry_consumers()
    names = {c.name for c in result.consumers}
    assert "governance audit" in names


def test_registry_audit_reports_artifact_registry_consumer() -> None:
    result = audit_registry_consumers()
    names = {c.name for c in result.consumers}
    assert "artifact registry" in names


def test_registry_audit_no_warnings_when_all_backed() -> None:
    result = audit_registry_consumers()
    assert result.warnings == ()


def test_registry_audit_advisory_text() -> None:
    result = audit_registry_consumers()
    assert result.advisory == REGISTRY_AUDIT_ADVISORY


def test_registry_audit_to_dict_shape() -> None:
    result = audit_registry_consumers()
    d = result.to_dict()
    assert "registry_audit_status" in d
    assert "consumers" in d
    assert "warnings" in d
    assert "advisory" in d
    assert isinstance(d["consumers"], list)
    assert isinstance(d["warnings"], list)


def test_registry_audit_consumer_to_dict_has_required_keys() -> None:
    result = audit_registry_consumers()
    for consumer in result.consumers:
        d = consumer.to_dict()
        assert "name" in d
        assert "registry_backed" in d
        assert "note" in d


def test_registry_audit_is_read_only(tmp_path: Path) -> None:
    before = list(tmp_path.iterdir())
    audit_registry_consumers()
    after = list(tmp_path.iterdir())
    assert before == after


def test_cli_governance_registry_audit_human(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "registry-audit"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance registry consumers audit" in output
    assert "Registry audit status: pass" in output
    assert "Consumers checked: 4" in output
    assert "sync-check" in output
    assert "sync-repair" in output
    assert "governance audit" in output
    assert "artifact registry" in output
    assert "Warnings:" in output
    assert "none" in output
    assert REGISTRY_AUDIT_ADVISORY in output


def test_cli_governance_registry_audit_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "registry-audit", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["registry_audit_status"] == "pass"
    assert len(data["consumers"]) == 4
    assert data["warnings"] == []
    assert data["advisory"] == REGISTRY_AUDIT_ADVISORY
    consumer_names = {c["name"] for c in data["consumers"]}
    assert "sync-check" in consumer_names
    assert "sync-repair" in consumer_names
    assert "governance audit" in consumer_names
    assert "artifact registry" in consumer_names
    for consumer in data["consumers"]:
        assert consumer["registry_backed"] is True
        assert consumer["note"]


# ---------------------------------------------------------------------------
# Phase 35U: Governance artifact registry export
# ---------------------------------------------------------------------------

from pcae.core.status import (
    GOVERNANCE_ARTIFACT_EXPORT_RELATIVE_PATH,
    GovernanceArtifactExport,
    export_governance_artifact_registry,
)


def test_export_governance_artifact_registry_writes_file(tmp_path: Path) -> None:
    result = export_governance_artifact_registry(HarnessPath(tmp_path))
    target = tmp_path / result.export_path
    assert target.is_file()


def test_export_governance_artifact_registry_path_format(tmp_path: Path) -> None:
    result = export_governance_artifact_registry(
        HarnessPath(tmp_path),
        exported_at=datetime(2026, 5, 28, 10, 0, 0, tzinfo=timezone.utc),
    )
    assert result.export_path == Path(
        ".pcae/governance-exports/artifact-registry-20260528-100000.json"
    )


def test_export_governance_artifact_registry_json_parses(tmp_path: Path) -> None:
    result = export_governance_artifact_registry(HarnessPath(tmp_path))
    target = tmp_path / result.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "exported_at" in data
    assert "artifact_count" in data
    assert "classes" in data
    assert "artifacts" in data
    assert "advisory" in data
    assert "exported_by_version" in data


def test_export_governance_artifact_registry_artifact_count(tmp_path: Path) -> None:
    result = export_governance_artifact_registry(HarnessPath(tmp_path))
    target = tmp_path / result.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["artifact_count"] == 11
    assert len(data["artifacts"]) == 11


def test_export_governance_artifact_registry_classes(tmp_path: Path) -> None:
    result = export_governance_artifact_registry(HarnessPath(tmp_path))
    target = tmp_path / result.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    assert set(data["classes"]) == {"operational", "historical", "runtime", "generated"}


def test_export_governance_artifact_registry_artifacts_have_required_fields(
    tmp_path: Path,
) -> None:
    result = export_governance_artifact_registry(HarnessPath(tmp_path))
    target = tmp_path / result.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    for artifact in data["artifacts"]:
        assert "path" in artifact
        assert "artifact_class" in artifact
        assert "governance_role" in artifact
        assert "repair_policy" in artifact
        assert "source_control_role" in artifact


def test_export_governance_artifact_registry_repair_policies(tmp_path: Path) -> None:
    result = export_governance_artifact_registry(HarnessPath(tmp_path))
    target = tmp_path / result.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    repair_policies = {a["repair_policy"] for a in data["artifacts"]}
    assert repair_policies == {"actionable", "preserve", "ignore"}


def test_export_governance_artifact_registry_source_control_roles(
    tmp_path: Path,
) -> None:
    result = export_governance_artifact_registry(HarnessPath(tmp_path))
    target = tmp_path / result.export_path
    data = json.loads(target.read_text(encoding="utf-8"))
    scr = {a["source_control_role"] for a in data["artifacts"]}
    assert "tracked" in scr
    assert "ignored" in scr
    assert "generated_ignored" in scr


def test_export_governance_artifact_registry_result_shape(tmp_path: Path) -> None:
    result = export_governance_artifact_registry(HarnessPath(tmp_path))
    assert isinstance(result, GovernanceArtifactExport)
    assert result.artifact_count == 11
    assert result.exported_at
    assert result.classes


def test_export_governance_artifact_registry_to_dict_shape(tmp_path: Path) -> None:
    result = export_governance_artifact_registry(HarnessPath(tmp_path))
    d = result.to_dict()
    assert "export_path" in d
    assert "exported_at" in d
    assert "artifact_count" in d
    assert "classes" in d
    assert "advisory" in d


def test_export_governance_artifact_registry_creates_export_dir(
    tmp_path: Path,
) -> None:
    export_governance_artifact_registry(HarnessPath(tmp_path))
    assert (tmp_path / ".pcae" / "governance-exports").is_dir()


def test_export_governance_artifact_registry_does_not_modify_governance_artifacts(
    tmp_path: Path,
) -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text("# Status\n")
    before = (tmp_path / "PROJECT_STATUS.md").read_text()
    export_governance_artifact_registry(HarnessPath(tmp_path))
    after = (tmp_path / "PROJECT_STATUS.md").read_text()
    assert before == after


def test_cli_governance_artifacts_export_human(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "artifacts", "export"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance artifact registry export" in output
    assert ".pcae/governance-exports/artifact-registry-" in output
    assert "Artifact count: 11" in output
    assert list((tmp_path / ".pcae" / "governance-exports").glob("artifact-registry-*.json"))


def test_cli_governance_artifacts_export_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "artifacts", "export", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert "export_path" in data
    assert "exported_at" in data
    assert "artifact_count" in data
    assert data["artifact_count"] == 11
    assert data["export_path"].startswith(".pcae/governance-exports/artifact-registry-")


def test_cli_governance_artifacts_export_json_file_parses(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["governance", "artifacts", "export", "--json"])
    data = json.loads(capsys.readouterr().out)
    export_path = tmp_path / data["export_path"]
    file_data = json.loads(export_path.read_text(encoding="utf-8"))
    assert file_data["artifact_count"] == 11
    assert len(file_data["artifacts"]) == 11
    assert file_data["exported_by_version"]


def test_cli_governance_artifacts_still_works_after_export_subparser(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "artifacts"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Governance artifact registry" in output


# ---------------------------------------------------------------------------
# Phase 36M: Architecture governance audit integration
# ---------------------------------------------------------------------------

from pcae.core.architecture import (
    add_architecture_decision,
    count_adr_parse_failures,
)


def test_governance_audit_includes_architecture_memory_check(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    check_names = {check.name for check in result.checks}
    assert "architecture_memory" in check_names


def test_governance_audit_architecture_memory_check_passes_with_sample_registry(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    arch_check = next(c for c in result.checks if c.name == "architecture_memory")
    assert arch_check.passed is True


def test_governance_audit_architecture_memory_check_message_includes_counts(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    arch_check = next(c for c in result.checks if c.name == "architecture_memory")
    assert "decisions readable" in arch_check.message
    assert "accepted" in arch_check.message


def test_governance_audit_result_has_architecture_memory_summary(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    assert hasattr(result, "architecture_memory_summary")
    assert isinstance(result.architecture_memory_summary, dict)


def test_architecture_memory_summary_has_required_keys(tmp_path: Path) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    mem = result.architecture_memory_summary
    assert "decision_count" in mem
    assert "accepted_count" in mem
    assert "latest_decision" in mem
    assert "warnings" in mem
    assert "errors" in mem


def test_architecture_memory_summary_decision_count_at_least_sample(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    mem = result.architecture_memory_summary
    assert mem["decision_count"] >= 2  # sample registry has 2


def test_architecture_memory_summary_accepted_count_positive(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    mem = result.architecture_memory_summary
    assert mem["accepted_count"] >= 1  # sample ADRs are accepted


def test_architecture_memory_summary_latest_decision_is_dict(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    latest = result.architecture_memory_summary["latest_decision"]
    assert isinstance(latest, dict)
    assert "id" in latest
    assert "title" in latest
    assert "status" in latest


def test_architecture_memory_summary_no_warnings_when_valid(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    mem = result.architecture_memory_summary
    assert mem["warnings"] == []
    assert mem["errors"] == []


def test_governance_audit_to_dict_includes_architecture_memory_summary(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    d = audit_governance_coherence(HarnessPath(tmp_path)).to_dict()
    assert "architecture_memory_summary" in d
    mem = d["architecture_memory_summary"]
    assert "decision_count" in mem
    assert "accepted_count" in mem
    assert "latest_decision" in mem
    assert "warnings" in mem
    assert "errors" in mem


def test_governance_audit_check_fails_on_malformed_adr_file(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    adr_dir = tmp_path / ".pcae" / "architecture"
    adr_dir.mkdir(parents=True)
    (adr_dir / "ADR-20260529-000000.json").write_text(
        "{not valid json}", encoding="utf-8"
    )
    result = audit_governance_coherence(HarnessPath(tmp_path))
    arch_check = next(c for c in result.checks if c.name == "architecture_memory")
    assert arch_check.passed is False
    assert "could not be parsed" in arch_check.message


def test_architecture_memory_summary_errors_on_parse_failure(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    adr_dir = tmp_path / ".pcae" / "architecture"
    adr_dir.mkdir(parents=True)
    (adr_dir / "ADR-20260529-000000.json").write_text("{bad}", encoding="utf-8")
    result = audit_governance_coherence(HarnessPath(tmp_path))
    mem = result.architecture_memory_summary
    assert len(mem["errors"]) >= 1
    assert "could not be parsed" in mem["errors"][0]


def test_count_adr_parse_failures_zero_when_no_directory(
    tmp_path: Path,
) -> None:
    assert count_adr_parse_failures(HarnessPath(tmp_path)) == 0


def test_count_adr_parse_failures_zero_when_all_valid(tmp_path: Path) -> None:
    from datetime import datetime, timezone
    fixed = datetime(2026, 5, 29, 12, 0, tzinfo=timezone.utc)
    add_architecture_decision(
        HarnessPath(tmp_path),
        title="Valid ADR",
        rationale="R.",
        author="alice",
        created_at=fixed,
    )
    assert count_adr_parse_failures(HarnessPath(tmp_path)) == 0


def test_count_adr_parse_failures_counts_malformed(tmp_path: Path) -> None:
    adr_dir = tmp_path / ".pcae" / "architecture"
    adr_dir.mkdir(parents=True)
    (adr_dir / "ADR-bad-1.json").write_text("{broken}", encoding="utf-8")
    (adr_dir / "ADR-bad-2.json").write_text("{also broken}", encoding="utf-8")
    assert count_adr_parse_failures(HarnessPath(tmp_path)) == 2


def test_count_adr_parse_failures_mixed(tmp_path: Path) -> None:
    from datetime import datetime, timezone
    fixed = datetime(2026, 5, 29, 12, 0, tzinfo=timezone.utc)
    add_architecture_decision(
        HarnessPath(tmp_path),
        title="Valid",
        rationale="R.",
        author="alice",
        created_at=fixed,
    )
    adr_dir = tmp_path / ".pcae" / "architecture"
    (adr_dir / "ADR-broken.json").write_text("{bad}", encoding="utf-8")
    assert count_adr_parse_failures(HarnessPath(tmp_path)) == 1


def test_cli_governance_audit_human_includes_architecture_memory_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "audit"])
    output = capsys.readouterr().out
    assert "Architecture memory summary:" in output
    assert "Decision count:" in output
    assert "Accepted:" in output
    assert "Latest:" in output


def test_cli_governance_audit_json_includes_architecture_memory_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["governance", "audit", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "architecture_memory_summary" in data
    mem = data["architecture_memory_summary"]
    assert "decision_count" in mem
    assert "accepted_count" in mem
    assert "latest_decision" in mem
    assert "warnings" in mem
    assert "errors" in mem


def test_cli_governance_audit_json_architecture_memory_check_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["governance", "audit", "--json"])
    data = json.loads(capsys.readouterr().out)
    check_names = [c["name"] for c in data["checks"]]
    assert "architecture_memory" in check_names


def test_governance_audit_valid_still_passes_with_architecture_memory(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    result = audit_governance_coherence(HarnessPath(tmp_path))
    assert result.valid
    assert result.summary.status == "valid"


def test_governance_audit_architecture_memory_check_is_read_only(
    tmp_path: Path,
) -> None:
    write_minimal_governance_artifacts(tmp_path)
    before = list((tmp_path / ".pcae").iterdir()) if (tmp_path / ".pcae").is_dir() else []
    audit_governance_coherence(HarnessPath(tmp_path))
    after = list((tmp_path / ".pcae").iterdir()) if (tmp_path / ".pcae").is_dir() else []
    assert len(after) == len(before)
