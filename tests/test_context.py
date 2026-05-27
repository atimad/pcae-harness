from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from pcae.cli import main
from datetime import datetime, timezone

from pcae.core.context import (
    BOOTSTRAP_COMPACT_ADVISORY,
    CONTEXT_PACK_ADVISORY,
    CONTEXT_PACK_BOOTSTRAP_HANDOFF_NOTES,
    CONTEXT_PACK_EXPORT_RELATIVE_DIR,
    CONTEXT_PACK_OPERATIONAL_RULES,
    CONTEXT_PACK_UNIVERSAL_AGENT_NOTE,
    CONTEXT_PACK_VALIDATION_COMMANDS,
    PROFILE_DOCUMENTATION,
    PROFILE_HANDOFF,
    PROFILE_IMPLEMENTATION,
    PROFILE_UNIVERSAL,
    PROFILE_VALIDATION,
    WORK_MODE_PROFILES,
    WorkModeProfile,
    build_bootstrap_prompt,
    build_context_pack,
    export_context_pack,
    resolve_profile,
)
from pcae.core.paths import HarnessPath


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def initialize_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)


def write_minimal_context_artifacts(
    tmp_path: Path,
    *,
    current_phase: str = "Phase Test.",
    next_item: str = "Implement next governed phase.",
    include_task: bool = True,
    event_summary: str = "Test provenance event.",
) -> None:
    initialize_git_repo(tmp_path)
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n"
        "## Current Phase\n\n"
        f"{current_phase}\n\n"
        "## Next\n\n"
        f"- {next_item}\n",
        encoding="utf-8",
    )
    if include_task:
        active_dir = tmp_path / "tasks" / "active"
        active_dir.mkdir(parents=True)
        (active_dir / "20260527-1200-test.md").write_text(
            "# Task Contract\n\n"
            "## Task ID\n\n20260527-1200-test\n\n"
            "## Title\n\nTest task\n\n"
            "## Status\n\nactive\n\n"
            "## Allowed Files\n\n- src/pcae/**\n- tests/**\n",
            encoding="utf-8",
        )
    pcae_dir = tmp_path / ".pcae"
    pcae_dir.mkdir(exist_ok=True)
    (pcae_dir / "session.json").write_text(
        json.dumps({
            "active_task": {"id": "20260527-1200-test"},
            "current_objective": "Test context pack.",
            "next_recommended_step": "Run governance checks.",
        }),
        encoding="utf-8",
    )
    (pcae_dir / "provenance-history.json").write_text(
        json.dumps([
            {
                "active_task": {"id": "20260527-1200-test", "title": "Test task"},
                "agent_id": "claude-local",
                "event_type": "phase_completed",
                "git_branch": "main",
                "summary": event_summary,
                "timestamp": "2026-05-27T12:00:00+00:00",
            }
        ]),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Core: ContextPack dataclass
# ---------------------------------------------------------------------------


def test_build_context_pack_returns_active_task(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.active_task is not None
    assert result.active_task["id"] == "20260527-1200-test"
    assert result.active_task["title"] == "Test task"


def test_build_context_pack_active_task_none_when_no_task_file(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path, include_task=False)
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.active_task is None


def test_build_context_pack_governance_state_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    gs = result.governance_state
    assert "health_status" in gs
    assert "check_status" in gs
    assert "session_continuity" in gs
    assert "agent_lock_state" in gs


def test_build_context_pack_governance_state_values(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    gs = result.governance_state
    assert gs["health_status"] in ("healthy", "unhealthy")
    assert gs["check_status"] in ("passed", "failed")
    assert gs["session_continuity"] in (
        "verified", "missing", "mismatch", "invalid", "unknown"
    )


def test_build_context_pack_orchestration_state_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    os_ = result.orchestration_state
    assert "orchestration_policy_summary" in os_
    assert "registered_agents" in os_
    assert "default_agent" in os_


def test_build_context_pack_orchestration_state_default_agent(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.orchestration_state["default_agent"] is not None


def test_build_context_pack_orchestration_state_has_agents(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    agents = result.orchestration_state["registered_agents"]
    assert isinstance(agents, list)
    assert len(agents) > 0
    for agent in agents:
        assert "agent_id" in agent
        assert "kind" in agent
        assert "roles" in agent


def test_build_context_pack_provenance_summary_event_count(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.provenance_summary["event_count"] == 1


def test_build_context_pack_provenance_summary_latest_event(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path, event_summary="Phase 35A completed.")
    result = build_context_pack(HarnessPath(tmp_path))
    le = result.provenance_summary["latest_event"]
    assert le is not None
    assert le["event_type"] == "phase_completed"
    assert le["summary"] == "Phase 35A completed."
    assert "timestamp" in le


def test_build_context_pack_provenance_summary_none_when_empty(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pcae_dir = tmp_path / ".pcae"
    (pcae_dir / "provenance-history.json").write_text("[]", encoding="utf-8")
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.provenance_summary["event_count"] == 0
    assert result.provenance_summary["latest_event"] is None


def test_build_context_pack_roadmap_summary_current_phase(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path, current_phase="Phase 35A: Context pack.")
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.roadmap_summary["current_phase"] == "Phase 35A: Context pack."


def test_build_context_pack_roadmap_summary_next_items(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path, next_item="Update pcae docs commands.")
    result = build_context_pack(HarnessPath(tmp_path))
    assert "- Update pcae docs commands." in result.roadmap_summary["next"]


def test_build_context_pack_roadmap_unknown_when_no_file(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    (tmp_path / "PROJECT_STATUS.md").unlink()
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.roadmap_summary["current_phase"] == "unknown"
    assert result.roadmap_summary["next"] == []


def test_build_context_pack_operational_rules(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.operational_rules == CONTEXT_PACK_OPERATIONAL_RULES
    # Phase authority rule is explicitly present
    assert any("Phase prompt is authoritative" in rule for rule in result.operational_rules)
    assert any("PROJECT_STATUS.md" in rule for rule in result.operational_rules)
    assert any("stale tasks" in rule for rule in result.operational_rules)
    assert any("active task scope" in rule for rule in result.operational_rules)


def test_build_context_pack_validation_commands(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.validation_commands == CONTEXT_PACK_VALIDATION_COMMANDS
    assert "pcae health" in result.validation_commands
    assert "pcae check" in result.validation_commands
    assert "python -m pytest" in result.validation_commands
    assert "git status" in result.validation_commands


def test_build_context_pack_advisory(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.advisory == CONTEXT_PACK_ADVISORY
    assert "reduces context size" in result.advisory
    assert "relaxing governance constraints" in result.advisory


# ---------------------------------------------------------------------------
# Core: to_dict
# ---------------------------------------------------------------------------


def test_to_dict_has_all_required_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    d = result.to_dict()
    assert "active_task" in d
    assert "governance_state" in d
    assert "orchestration_state" in d
    assert "provenance_summary" in d
    assert "roadmap_summary" in d
    assert "operational_rules" in d
    assert "validation_commands" in d
    assert "advisory" in d
    assert "scope_boundaries" in d
    assert "bootstrap_handoff_notes" in d


def test_to_dict_operational_rules_is_list(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    d = build_context_pack(HarnessPath(tmp_path)).to_dict()
    assert isinstance(d["operational_rules"], list)
    assert len(d["operational_rules"]) > 0


def test_to_dict_validation_commands_is_list(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    d = build_context_pack(HarnessPath(tmp_path)).to_dict()
    assert isinstance(d["validation_commands"], list)
    assert "pcae check" in d["validation_commands"]


def test_to_dict_is_json_serializable(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    d = build_context_pack(HarnessPath(tmp_path)).to_dict()
    serialized = json.dumps(d)
    parsed = json.loads(serialized)
    assert parsed["advisory"] == CONTEXT_PACK_ADVISORY
    assert isinstance(parsed["scope_boundaries"], dict)
    assert isinstance(parsed["bootstrap_handoff_notes"], list)


# ---------------------------------------------------------------------------
# CLI: human-readable output
# ---------------------------------------------------------------------------


def test_cli_context_pack_preview_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["context", "pack", "--preview"])
    assert exit_code == 0


def test_cli_context_pack_preview_header(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Governance context pack" in output


def test_cli_context_pack_preview_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Active task:" in output
    assert "20260527-1200-test" in output
    assert "Test task" in output


def test_cli_context_pack_preview_governance_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Governance state:" in output
    assert "Health:" in output
    assert "Check:" in output
    assert "Session continuity:" in output
    assert "Agent lock:" in output


def test_cli_context_pack_preview_orchestration_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Orchestration state:" in output
    assert "Default agent:" in output
    assert "Registered agents:" in output


def test_cli_context_pack_preview_provenance_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Provenance summary:" in output
    assert "Event count:" in output
    assert "Latest event:" in output


def test_cli_context_pack_preview_roadmap_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path, current_phase="Phase 35A: Context pack.")
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Roadmap summary:" in output
    assert "Current phase: Phase 35A: Context pack." in output


def test_cli_context_pack_preview_operational_rules(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Operational rules:" in output
    assert "Phase prompt is authoritative" in output


def test_cli_context_pack_preview_validation_commands(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Validation commands:" in output
    assert "pcae health" in output
    assert "pcae check" in output
    assert "python -m pytest" in output
    assert "git status" in output


def test_cli_context_pack_preview_quality_preservation_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Quality preservation note:" in output
    assert "relaxing governance constraints" in output


def test_cli_context_pack_preview_token_optimization_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Token optimization note:" in output


# ---------------------------------------------------------------------------
# CLI: JSON output
# ---------------------------------------------------------------------------


def test_cli_context_pack_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["context", "pack", "--preview", "--json"])
    assert exit_code == 0


def test_cli_context_pack_json_is_valid_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    output = capsys.readouterr().out
    data = json.loads(output)
    assert isinstance(data, dict)


def test_cli_context_pack_json_top_level_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "active_task" in data
    assert "governance_state" in data
    assert "orchestration_state" in data
    assert "provenance_summary" in data
    assert "roadmap_summary" in data
    assert "operational_rules" in data
    assert "validation_commands" in data
    assert "advisory" in data
    assert "scope_boundaries" in data
    assert "bootstrap_handoff_notes" in data


def test_cli_context_pack_json_active_task_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["active_task"]["id"] == "20260527-1200-test"
    assert data["active_task"]["title"] == "Test task"


def test_cli_context_pack_json_governance_state_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    gs = data["governance_state"]
    assert "health_status" in gs
    assert "check_status" in gs
    assert "session_continuity" in gs
    assert "agent_lock_state" in gs


def test_cli_context_pack_json_orchestration_state_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    os_ = data["orchestration_state"]
    assert "orchestration_policy_summary" in os_
    assert "registered_agents" in os_
    assert "default_agent" in os_


def test_cli_context_pack_json_provenance_summary_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    ps = data["provenance_summary"]
    assert ps["event_count"] == 1
    assert ps["latest_event"] is not None
    assert ps["latest_event"]["event_type"] == "phase_completed"


def test_cli_context_pack_json_roadmap_summary_fields(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path, current_phase="Phase 35A: Context pack.")
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    rs = data["roadmap_summary"]
    assert rs["current_phase"] == "Phase 35A: Context pack."
    assert isinstance(rs["next"], list)


def test_cli_context_pack_json_operational_rules_list(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    rules = data["operational_rules"]
    assert isinstance(rules, list)
    assert any("Phase prompt is authoritative" in r for r in rules)


def test_cli_context_pack_json_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "relaxing governance constraints" in data["advisory"]


# ---------------------------------------------------------------------------
# Core: scope_boundaries
# ---------------------------------------------------------------------------


def test_build_context_pack_scope_boundaries_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    sb = result.scope_boundaries
    assert "allowed_files" in sb
    assert "forbidden_files" in sb


def test_build_context_pack_scope_boundaries_with_task(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    assert isinstance(result.scope_boundaries["allowed_files"], list)
    assert isinstance(result.scope_boundaries["forbidden_files"], list)


def test_build_context_pack_scope_boundaries_no_task(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path, include_task=False)
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.scope_boundaries["allowed_files"] == []
    assert result.scope_boundaries["forbidden_files"] == []


# ---------------------------------------------------------------------------
# Core: bootstrap_handoff_notes
# ---------------------------------------------------------------------------


def test_build_context_pack_bootstrap_handoff_notes(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    assert result.bootstrap_handoff_notes == CONTEXT_PACK_BOOTSTRAP_HANDOFF_NOTES
    assert any("session bootstrap" in note for note in result.bootstrap_handoff_notes)
    assert any("phase handoff" in note for note in result.bootstrap_handoff_notes)


def test_to_dict_scope_boundaries_is_dict(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    d = build_context_pack(HarnessPath(tmp_path)).to_dict()
    assert isinstance(d["scope_boundaries"], dict)
    assert "allowed_files" in d["scope_boundaries"]
    assert "forbidden_files" in d["scope_boundaries"]


def test_to_dict_bootstrap_handoff_notes_is_list(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    d = build_context_pack(HarnessPath(tmp_path)).to_dict()
    notes = d["bootstrap_handoff_notes"]
    assert isinstance(notes, list)
    assert len(notes) > 0


# ---------------------------------------------------------------------------
# Core: orchestration advisory semantics
# ---------------------------------------------------------------------------


def test_build_context_pack_orchestration_advisory_semantics(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    os_ = result.orchestration_state
    assert "advisory_recommendation_semantics" in os_
    assert "user" in os_["advisory_recommendation_semantics"].lower()
    assert "authoritative" in os_["advisory_recommendation_semantics"].lower()


# ---------------------------------------------------------------------------
# CLI: human-readable — new sections
# ---------------------------------------------------------------------------


def test_cli_context_pack_preview_universal_agent_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Universal agent note:" in output
    assert CONTEXT_PACK_UNIVERSAL_AGENT_NOTE in output


def test_cli_context_pack_preview_bootstrap_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Bootstrap/handoff:" in output
    assert "session bootstrap" in output
    assert "phase handoff" in output


def test_cli_context_pack_preview_scope_boundaries(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Scope boundaries:" in output
    assert "Allowed files:" in output


def test_cli_context_pack_preview_orchestration_policy_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Policy summary:" in output


def test_cli_context_pack_preview_orchestration_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Advisory:" in output
    assert "authoritative" in output


# ---------------------------------------------------------------------------
# CLI: JSON — new fields
# ---------------------------------------------------------------------------


def test_cli_context_pack_json_scope_boundaries(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    sb = data["scope_boundaries"]
    assert isinstance(sb, dict)
    assert "allowed_files" in sb
    assert "forbidden_files" in sb


def test_cli_context_pack_json_bootstrap_handoff_notes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    notes = data["bootstrap_handoff_notes"]
    assert isinstance(notes, list)
    assert any("session bootstrap" in n for n in notes)
    assert any("phase handoff" in n for n in notes)


def test_cli_context_pack_json_orchestration_advisory_semantics(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    os_ = data["orchestration_state"]
    assert "advisory_recommendation_semantics" in os_
    assert "authoritative" in os_["advisory_recommendation_semantics"].lower()


# ---------------------------------------------------------------------------
# Work-mode profiles: resolve_profile
# ---------------------------------------------------------------------------


def test_resolve_profile_none_returns_universal() -> None:
    profile, is_unknown = resolve_profile(None)
    assert profile.profile_type == PROFILE_UNIVERSAL
    assert is_unknown is False


def test_resolve_profile_universal_explicit() -> None:
    profile, is_unknown = resolve_profile(PROFILE_UNIVERSAL)
    assert profile.profile_type == PROFILE_UNIVERSAL
    assert is_unknown is False


def test_resolve_profile_implementation() -> None:
    profile, is_unknown = resolve_profile(PROFILE_IMPLEMENTATION)
    assert profile.profile_type == PROFILE_IMPLEMENTATION
    assert is_unknown is False
    assert "active_task" in profile.emphasized_sections
    assert "scope_boundaries" in profile.emphasized_sections
    assert "validation_commands" in profile.emphasized_sections


def test_resolve_profile_documentation() -> None:
    profile, is_unknown = resolve_profile(PROFILE_DOCUMENTATION)
    assert profile.profile_type == PROFILE_DOCUMENTATION
    assert is_unknown is False
    assert "roadmap_summary" in profile.emphasized_sections
    assert "operational_rules" in profile.emphasized_sections


def test_resolve_profile_validation() -> None:
    profile, is_unknown = resolve_profile(PROFILE_VALIDATION)
    assert profile.profile_type == PROFILE_VALIDATION
    assert is_unknown is False
    assert "governance_state" in profile.emphasized_sections
    assert "validation_commands" in profile.emphasized_sections


def test_resolve_profile_handoff() -> None:
    profile, is_unknown = resolve_profile(PROFILE_HANDOFF)
    assert profile.profile_type == PROFILE_HANDOFF
    assert is_unknown is False
    assert "governance_state" in profile.emphasized_sections
    assert "provenance_summary" in profile.emphasized_sections
    assert "bootstrap_handoff_notes" in profile.emphasized_sections
    assert "orchestration_state" in profile.emphasized_sections


def test_resolve_profile_unknown_falls_back_to_universal() -> None:
    profile, is_unknown = resolve_profile("nonexistent-profile")
    assert profile.profile_type == PROFILE_UNIVERSAL
    assert is_unknown is True


def test_work_mode_profiles_has_all_known_profiles() -> None:
    assert PROFILE_UNIVERSAL in WORK_MODE_PROFILES
    assert PROFILE_IMPLEMENTATION in WORK_MODE_PROFILES
    assert PROFILE_DOCUMENTATION in WORK_MODE_PROFILES
    assert PROFILE_VALIDATION in WORK_MODE_PROFILES
    assert PROFILE_HANDOFF in WORK_MODE_PROFILES


def test_all_profiles_have_non_empty_emphasized_sections() -> None:
    for name, profile in WORK_MODE_PROFILES.items():
        assert isinstance(profile, WorkModeProfile), name
        assert len(profile.emphasized_sections) > 0, name


# ---------------------------------------------------------------------------
# CLI: profile human-readable output
# ---------------------------------------------------------------------------


def test_cli_context_pack_no_profile_shows_universal(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Profile: universal" in output
    assert "Emphasized sections:" in output


def test_cli_context_pack_profile_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "implementation"])
    output = capsys.readouterr().out
    assert "Profile: implementation" in output
    assert "scope_boundaries" in output
    assert "validation_commands" in output


def test_cli_context_pack_profile_documentation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "documentation"])
    output = capsys.readouterr().out
    assert "Profile: documentation" in output
    assert "roadmap_summary" in output
    assert "operational_rules" in output


def test_cli_context_pack_profile_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "validation"])
    output = capsys.readouterr().out
    assert "Profile: validation" in output
    assert "governance_state" in output
    assert "validation_commands" in output


def test_cli_context_pack_profile_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "handoff"])
    output = capsys.readouterr().out
    assert "Profile: handoff" in output
    assert "provenance_summary" in output
    assert "bootstrap_handoff_notes" in output


def test_cli_context_pack_unknown_profile_warns_and_falls_back(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "no-such-profile"])
    output = capsys.readouterr().out
    assert "Warning:" in output
    assert "no-such-profile" in output
    assert "universal" in output
    assert "Profile: universal" in output


def test_cli_context_pack_profiles_preserve_governance_rules(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    for profile in (
        PROFILE_IMPLEMENTATION,
        PROFILE_DOCUMENTATION,
        PROFILE_VALIDATION,
        PROFILE_HANDOFF,
    ):
        main(["context", "pack", "--preview", "--profile", profile])
        output = capsys.readouterr().out
        assert "Phase prompt is authoritative" in output, profile
        assert "Governance context pack" in output, profile
        assert "Quality preservation note:" in output, profile


def test_cli_context_pack_profiles_preserve_vendor_neutral_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    for profile in (
        PROFILE_IMPLEMENTATION,
        PROFILE_DOCUMENTATION,
        PROFILE_VALIDATION,
        PROFILE_HANDOFF,
    ):
        main(["context", "pack", "--preview", "--profile", profile])
        output = capsys.readouterr().out
        assert CONTEXT_PACK_UNIVERSAL_AGENT_NOTE in output, profile


# ---------------------------------------------------------------------------
# CLI: profile JSON output
# ---------------------------------------------------------------------------


def test_cli_context_pack_json_profile_type_universal(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["profile_type"] == PROFILE_UNIVERSAL
    assert isinstance(data["emphasized_sections"], list)
    assert len(data["emphasized_sections"]) > 0


def test_cli_context_pack_json_profile_type_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "implementation", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["profile_type"] == PROFILE_IMPLEMENTATION
    assert "scope_boundaries" in data["emphasized_sections"]
    assert "validation_commands" in data["emphasized_sections"]


def test_cli_context_pack_json_profile_type_documentation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "documentation", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["profile_type"] == PROFILE_DOCUMENTATION
    assert "roadmap_summary" in data["emphasized_sections"]


def test_cli_context_pack_json_profile_type_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "validation", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["profile_type"] == PROFILE_VALIDATION
    assert "governance_state" in data["emphasized_sections"]


def test_cli_context_pack_json_profile_type_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "handoff", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["profile_type"] == PROFILE_HANDOFF
    assert "bootstrap_handoff_notes" in data["emphasized_sections"]
    assert "orchestration_state" in data["emphasized_sections"]


def test_cli_context_pack_json_unknown_profile_fallback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "bad-profile", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["profile_type"] == PROFILE_UNIVERSAL
    assert "profile_warning" in data
    assert "bad-profile" in data["profile_warning"]


def test_cli_context_pack_json_profile_preserves_all_governance_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--profile", "implementation", "--json"])
    data = json.loads(capsys.readouterr().out)
    for key in (
        "active_task",
        "governance_state",
        "orchestration_state",
        "provenance_summary",
        "roadmap_summary",
        "operational_rules",
        "validation_commands",
        "bootstrap_handoff_notes",
        "advisory",
        "scope_boundaries",
        "profile_type",
        "emphasized_sections",
    ):
        assert key in data, key


# ---------------------------------------------------------------------------
# Core: build_bootstrap_prompt
# ---------------------------------------------------------------------------


def test_build_bootstrap_prompt_returns_string(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert isinstance(result, str)
    assert len(result) > 0


def test_build_bootstrap_prompt_contains_profile_header(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_IMPLEMENTATION)
    result = build_bootstrap_prompt(pack, profile)
    assert "[PCAE Bootstrap | implementation profile]" in result


def test_build_bootstrap_prompt_contains_active_task(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "20260527-1200-test" in result
    assert "Test task" in result


def test_build_bootstrap_prompt_active_task_none(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path, include_task=False)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "Active task: none" in result


def test_build_bootstrap_prompt_contains_governance_state(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "health=" in result
    assert "check=" in result
    assert "session=" in result
    assert "lock=" in result


def test_build_bootstrap_prompt_contains_phase(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path, current_phase="Phase 35E: Compact bootstrap.")
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "Phase 35E: Compact bootstrap." in result


def test_build_bootstrap_prompt_contains_emphasized_sections(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_HANDOFF)
    result = build_bootstrap_prompt(pack, profile)
    assert "Emphasized:" in result
    assert "bootstrap_handoff_notes" in result


def test_build_bootstrap_prompt_contains_operational_rules(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "Rules:" in result
    assert "Phase prompt is authoritative" in result
    assert "active task scope" in result


def test_build_bootstrap_prompt_contains_validation_commands(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "Validate:" in result
    assert "pcae check" in result
    assert "python -m pytest" in result


def test_build_bootstrap_prompt_contains_stale_context_suppression(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "Stale-context:" in result
    assert "Phase prompt is authoritative" in result
    assert "PROJECT_STATUS.md is background" in result
    assert "stale work" in result


def test_build_bootstrap_prompt_contains_bootstrap_and_handoff(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "Bootstrap: pcae session bootstrap" in result
    assert "Handoff: pcae phase handoff" in result


def test_build_bootstrap_prompt_contains_vendor_neutral_note(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "Vendor-neutral:" in result
    assert "not tailored to any specific AI agent" in result


def test_build_bootstrap_prompt_contains_orchestration_advisory(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    result = build_bootstrap_prompt(pack, profile)
    assert "Orchestration:" in result
    assert "authoritative" in result


def test_build_bootstrap_prompt_implementation_emphasizes_scope(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_IMPLEMENTATION)
    result = build_bootstrap_prompt(pack, profile)
    assert "implementation profile" in result
    assert "scope_boundaries" in result
    assert "validation_commands" in result


def test_build_bootstrap_prompt_handoff_emphasizes_handoff_sections(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_HANDOFF)
    result = build_bootstrap_prompt(pack, profile)
    assert "handoff profile" in result
    assert "bootstrap_handoff_notes" in result
    assert "orchestration_state" in result


def test_bootstrap_compact_advisory_content() -> None:
    assert "Bootstrap compression" in BOOTSTRAP_COMPACT_ADVISORY
    assert "relaxing governance constraints" in BOOTSTRAP_COMPACT_ADVISORY


# ---------------------------------------------------------------------------
# Core: export_context_pack
# ---------------------------------------------------------------------------


def test_export_context_pack_relative_dir_constant() -> None:
    from pathlib import Path as _Path
    assert CONTEXT_PACK_EXPORT_RELATIVE_DIR == _Path(".pcae") / "context-packs"


def test_export_context_pack_creates_file(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)

    relative_path, _ = export_context_pack(HarnessPath(tmp_path), pack, profile, exported_at=ts)

    assert (tmp_path / relative_path).is_file()


def test_export_context_pack_filename_uses_timestamp(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    ts = datetime(2026, 5, 27, 14, 30, 59, tzinfo=timezone.utc)

    relative_path, _ = export_context_pack(HarnessPath(tmp_path), pack, profile, exported_at=ts)

    assert relative_path.name == "context-pack-20260527-143059.txt"


def test_export_context_pack_path_under_context_packs_dir(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)

    relative_path, _ = export_context_pack(HarnessPath(tmp_path), pack, profile)

    assert relative_path.as_posix().startswith(".pcae/context-packs/")
    assert relative_path.suffix == ".txt"


def test_export_context_pack_returns_iso_timestamp(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)

    _, exported_at = export_context_pack(HarnessPath(tmp_path), pack, profile, exported_at=ts)

    assert exported_at == "2026-05-27T12:00:00+00:00"


def test_export_context_pack_content_contains_bootstrap_prompt(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)

    relative_path, _ = export_context_pack(HarnessPath(tmp_path), pack, profile)

    content = (tmp_path / relative_path).read_text(encoding="utf-8")
    assert "[PCAE Bootstrap" in content
    assert "Governance:" in content
    assert "Rules:" in content


def test_export_context_pack_content_contains_stale_context_suppression(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_UNIVERSAL)

    relative_path, _ = export_context_pack(HarnessPath(tmp_path), pack, profile)

    content = (tmp_path / relative_path).read_text(encoding="utf-8")
    assert "Stale-context:" in content
    assert "PROJECT_STATUS.md is background" in content


def test_export_context_pack_with_implementation_profile(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_IMPLEMENTATION)

    relative_path, _ = export_context_pack(HarnessPath(tmp_path), pack, profile)

    content = (tmp_path / relative_path).read_text(encoding="utf-8")
    assert "implementation profile" in content
    assert "scope_boundaries" in content


def test_export_context_pack_with_handoff_profile(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(PROFILE_HANDOFF)

    relative_path, _ = export_context_pack(HarnessPath(tmp_path), pack, profile)

    content = (tmp_path / relative_path).read_text(encoding="utf-8")
    assert "handoff profile" in content
    assert "bootstrap_handoff_notes" in content


# ---------------------------------------------------------------------------
# CLI: context export
# ---------------------------------------------------------------------------


def test_cli_context_export_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["context", "export"])
    capsys.readouterr()
    assert exit_code == 0


def test_cli_context_export_prints_exported_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export"])
    output = capsys.readouterr().out
    assert "Exported:" in output
    assert ".pcae/context-packs/" in output
    assert ".txt" in output


def test_cli_context_export_prints_profile(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export"])
    output = capsys.readouterr().out
    assert "Profile: universal" in output


def test_cli_context_export_creates_file_on_disk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export"])
    capsys.readouterr()
    export_dir = tmp_path / ".pcae" / "context-packs"
    assert export_dir.is_dir()
    files = list(export_dir.glob("context-pack-*.txt"))
    assert len(files) == 1


def test_cli_context_export_file_content(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export"])
    capsys.readouterr()
    export_dir = tmp_path / ".pcae" / "context-packs"
    content = next(export_dir.glob("context-pack-*.txt")).read_text(encoding="utf-8")
    assert "[PCAE Bootstrap" in content
    assert "Phase prompt is authoritative" in content


def test_cli_context_export_profile_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export", "--profile", "implementation"])
    output = capsys.readouterr().out
    assert "Profile: implementation" in output
    export_dir = tmp_path / ".pcae" / "context-packs"
    content = next(export_dir.glob("context-pack-*.txt")).read_text(encoding="utf-8")
    assert "implementation profile" in content


def test_cli_context_export_profile_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export", "--profile", "handoff"])
    output = capsys.readouterr().out
    assert "Profile: handoff" in output


def test_cli_context_export_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["context", "export", "--json"])
    capsys.readouterr()
    assert exit_code == 0


def test_cli_context_export_json_is_valid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, dict)


def test_cli_context_export_json_required_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "path" in data
    assert "profile_type" in data
    assert "exported_at" in data


def test_cli_context_export_json_path_under_context_packs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["path"].startswith(".pcae/context-packs/")
    assert data["path"].endswith(".txt")


def test_cli_context_export_json_profile_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export", "--profile", "implementation", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["profile_type"] == "implementation"


def test_cli_context_export_json_exported_at_is_iso(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "export", "--json"])
    data = json.loads(capsys.readouterr().out)
    # Must be parseable as an ISO datetime
    from datetime import datetime as _dt
    parsed = _dt.fromisoformat(data["exported_at"])
    assert parsed is not None


def test_cli_context_pack_preview_unchanged_by_export(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Governance context pack" in output
    assert "Profile: universal" in output
    assert "Operational rules:" in output


def test_context_export_gitignore_contains_context_packs() -> None:
    gitignore = Path(__file__).parent.parent / ".pcae" / ".gitignore"
    assert gitignore.is_file()
    content = gitignore.read_text(encoding="utf-8")
    assert "context-packs/" in content


# ---------------------------------------------------------------------------
# CLI: --preview required
# ---------------------------------------------------------------------------


def test_cli_context_pack_requires_preview_flag(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        main(["context", "pack"])
    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# Phase 35G: Continuity restore packs
# ---------------------------------------------------------------------------

from pcae.core.context import (
    CONTINUITY_PACK_GOVERNANCE_CONTINUITY_NOTE,
    CONTINUITY_PACK_INCLUDED_SECTIONS,
    CONTINUITY_PACK_RELATIVE_DIR,
    CONTINUITY_PACK_STALE_CONTEXT_SUPPRESSION_RULES,
    CONTINUITY_PACK_VENDOR_NEUTRAL_NOTE,
    ContinuityPack,
    build_continuity_pack,
    export_continuity_pack,
)


# ---------------------------------------------------------------------------
# Core: build_continuity_pack
# ---------------------------------------------------------------------------


def test_build_continuity_pack_returns_continuity_pack(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert isinstance(result, ContinuityPack)


def test_build_continuity_pack_exported_at_is_iso(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)
    result = build_continuity_pack(HarnessPath(tmp_path), profile, exported_at=ts)
    assert result.exported_at == ts.isoformat()


def test_build_continuity_pack_profile_type(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(PROFILE_IMPLEMENTATION)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert result.profile_type == PROFILE_IMPLEMENTATION


def test_build_continuity_pack_active_task_summary(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert result.active_task_summary is not None
    assert result.active_task_summary["id"] == "20260527-1200-test"
    assert result.active_task_summary["title"] == "Test task"


def test_build_continuity_pack_active_task_summary_none_when_no_task(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path, include_task=False)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert result.active_task_summary is None


def test_build_continuity_pack_governance_state_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    gs = result.governance_state
    assert "health_status" in gs
    assert "check_status" in gs
    assert "session_continuity" in gs


def test_build_continuity_pack_orchestration_state_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    os_ = result.orchestration_state
    assert "registered_agents" in os_
    assert "default_agent" in os_


def test_build_continuity_pack_provenance_summary_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    ps = result.provenance_summary
    assert "event_count" in ps
    assert "latest_event" in ps


def test_build_continuity_pack_runtime_snapshot_metadata_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    meta = result.runtime_snapshot_metadata
    assert "governance_health_status" in meta
    assert "governance_check_status" in meta
    assert "active_task" in meta


def test_build_continuity_pack_compact_context_pack_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    cp = result.compact_context_pack
    assert "governance_state" in cp
    assert "orchestration_state" in cp
    assert "operational_rules" in cp
    assert "validation_commands" in cp


def test_build_continuity_pack_compact_bootstrap_prompt_is_string(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert isinstance(result.compact_bootstrap_prompt, str)
    assert len(result.compact_bootstrap_prompt) > 0


def test_build_continuity_pack_bootstrap_prompt_contains_profile(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(PROFILE_HANDOFF)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert PROFILE_HANDOFF in result.compact_bootstrap_prompt


def test_build_continuity_pack_operational_rules(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert result.operational_rules == CONTEXT_PACK_OPERATIONAL_RULES


def test_build_continuity_pack_validation_commands(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert result.validation_commands == CONTEXT_PACK_VALIDATION_COMMANDS


def test_build_continuity_pack_stale_context_suppression_rules(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert result.stale_context_suppression_rules == CONTINUITY_PACK_STALE_CONTEXT_SUPPRESSION_RULES
    assert len(result.stale_context_suppression_rules) > 0


def test_build_continuity_pack_vendor_neutral_note(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert result.vendor_neutral_note == CONTINUITY_PACK_VENDOR_NEUTRAL_NOTE
    assert "vendor-neutral" in result.vendor_neutral_note


def test_build_continuity_pack_bootstrap_continuity(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert result.bootstrap_continuity == CONTEXT_PACK_BOOTSTRAP_HANDOFF_NOTES
    assert len(result.bootstrap_continuity) > 0


def test_build_continuity_pack_to_dict_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    d = result.to_dict()
    expected_keys = {
        "active_task_summary",
        "bootstrap_continuity",
        "compact_bootstrap_prompt",
        "compact_context_pack",
        "exported_at",
        "governance_state",
        "operational_rules",
        "orchestration_state",
        "profile_type",
        "provenance_summary",
        "runtime_snapshot_metadata",
        "stale_context_suppression_rules",
        "validation_commands",
        "vendor_neutral_note",
    }
    assert set(d.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Core: export_continuity_pack
# ---------------------------------------------------------------------------


def test_export_continuity_pack_relative_dir_constant() -> None:
    assert CONTINUITY_PACK_RELATIVE_DIR == Path(".pcae") / "continuity-packs"


def test_export_continuity_pack_creates_file(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    relative_path, _ = export_continuity_pack(root, pack)
    assert (tmp_path / relative_path).is_file()


def test_export_continuity_pack_filename_uses_timestamp(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 30, 45, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    relative_path, _ = export_continuity_pack(root, pack)
    assert "continuity-pack-20260527-123045" in relative_path.name


def test_export_continuity_pack_path_under_continuity_packs_dir(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    relative_path, _ = export_continuity_pack(root, pack)
    assert relative_path.parts[0] == ".pcae"
    assert relative_path.parts[1] == "continuity-packs"


def test_export_continuity_pack_returns_iso_timestamp(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    _, exported_at = export_continuity_pack(root, pack)
    assert exported_at == ts.isoformat()


def test_export_continuity_pack_file_is_valid_json(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    relative_path, _ = export_continuity_pack(root, pack)
    data = json.loads((tmp_path / relative_path).read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_export_continuity_pack_json_has_required_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    relative_path, _ = export_continuity_pack(root, pack)
    data = json.loads((tmp_path / relative_path).read_text(encoding="utf-8"))
    assert "exported_at" in data
    assert "governance_state" in data
    assert "compact_bootstrap_prompt" in data
    assert "stale_context_suppression_rules" in data
    assert "vendor_neutral_note" in data
    assert "bootstrap_continuity" in data


def test_export_continuity_pack_json_stale_context_rules(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    relative_path, _ = export_continuity_pack(root, pack)
    data = json.loads((tmp_path / relative_path).read_text(encoding="utf-8"))
    assert len(data["stale_context_suppression_rules"]) > 0


def test_export_continuity_pack_json_vendor_neutral(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    relative_path, _ = export_continuity_pack(root, pack)
    data = json.loads((tmp_path / relative_path).read_text(encoding="utf-8"))
    assert "vendor-neutral" in data["vendor_neutral_note"]


def test_export_continuity_pack_is_read_only_no_side_effects(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    export_continuity_pack(root, pack)
    # No runtime-snapshots directory should be created as a side effect
    runtime_snapshots_dir = tmp_path / ".pcae" / "runtime-snapshots"
    assert not runtime_snapshots_dir.exists()


# ---------------------------------------------------------------------------
# CLI: pcae continuity export
# ---------------------------------------------------------------------------


def test_cli_continuity_export_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["continuity", "export"])
    assert result == 0


def test_cli_continuity_export_prints_export_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    captured = capsys.readouterr()
    assert "Export path:" in captured.out
    assert ".pcae/continuity-packs/" in captured.out


def test_cli_continuity_export_prints_profile(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    captured = capsys.readouterr()
    assert "Profile:" in captured.out
    assert PROFILE_UNIVERSAL in captured.out


def test_cli_continuity_export_prints_included_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    captured = capsys.readouterr()
    assert "Included continuity sections:" in captured.out
    assert "active task summary" in captured.out
    assert "stale-context suppression rules" in captured.out
    assert "bootstrap continuity" in captured.out


def test_cli_continuity_export_prints_token_optimization_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    captured = capsys.readouterr()
    assert "Token optimization note" in captured.out


def test_cli_continuity_export_prints_governance_continuity_note(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    captured = capsys.readouterr()
    assert "Governance continuity note" in captured.out


def test_cli_continuity_export_creates_file_on_disk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    files = list(packs_dir.glob("continuity-pack-*.json"))
    assert len(files) == 1


def test_cli_continuity_export_profile_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--profile", "implementation"])
    captured = capsys.readouterr()
    assert PROFILE_IMPLEMENTATION in captured.out


def test_cli_continuity_export_profile_handoff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--profile", "handoff"])
    captured = capsys.readouterr()
    assert PROFILE_HANDOFF in captured.out


def test_cli_continuity_export_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["continuity", "export", "--json"])
    assert result == 0


def test_cli_continuity_export_json_is_valid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_cli_continuity_export_json_required_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "path" in data
    assert "profile_type" in data
    assert "exported_at" in data
    assert "included_sections" in data
    assert "continuity_summary" in data


def test_cli_continuity_export_json_path_under_continuity_packs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert ".pcae/continuity-packs/" in data["path"]


def test_cli_continuity_export_json_profile_type(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["profile_type"] == PROFILE_UNIVERSAL


def test_cli_continuity_export_json_exported_at_is_iso(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    datetime.fromisoformat(data["exported_at"])


def test_cli_continuity_export_json_included_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    sections = data["included_sections"]
    assert "active task summary" in sections
    assert "compact bootstrap prompt" in sections
    assert "stale-context suppression rules" in sections
    assert "bootstrap continuity" in sections
    assert "vendor-neutral note" in sections


def test_cli_continuity_export_json_continuity_summary_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    summary = data["continuity_summary"]
    assert "active_task" in summary
    assert "governance_health" in summary
    assert "governance_check" in summary


def test_cli_continuity_export_file_content_is_valid_json(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_file = next(packs_dir.glob("continuity-pack-*.json"))
    content = json.loads(pack_file.read_text(encoding="utf-8"))
    assert isinstance(content, dict)
    assert "compact_bootstrap_prompt" in content
    assert "stale_context_suppression_rules" in content
    assert "vendor_neutral_note" in content
    assert "bootstrap_continuity" in content


def test_continuity_export_gitignore_contains_continuity_packs() -> None:
    gitignore = Path(__file__).parent.parent / ".pcae" / ".gitignore"
    assert gitignore.is_file()
    content = gitignore.read_text(encoding="utf-8")
    assert "continuity-packs/" in content
