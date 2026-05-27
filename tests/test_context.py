from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from pcae.cli import main
from pcae.core.context import (
    CONTEXT_PACK_ADVISORY,
    CONTEXT_PACK_BOOTSTRAP_HANDOFF_NOTES,
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
    build_context_pack,
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
# CLI: --preview required
# ---------------------------------------------------------------------------


def test_cli_context_pack_requires_preview_flag(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        main(["context", "pack"])
    assert exc_info.value.code != 0
