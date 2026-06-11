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
    assert "python -m pytest -n auto" in result.validation_commands
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
    assert "strategic_continuity" in d


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
        "architecture_memory",
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


# ---------------------------------------------------------------------------
# Phase 35H: Continuity pack inspection
# ---------------------------------------------------------------------------

from pcae.core.context import (
    CONTINUITY_PACK_INSPECTION_ADVISORY,
    CONTINUITY_PACK_REQUIRED_KEYS,
    ContinuityPackInspection,
    inspect_continuity_pack,
)


def _export_pack_for_inspection(tmp_path: Path, profile_name: str | None = None) -> Path:
    """Helper: export a continuity pack and return its absolute path."""
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(profile_name)
    ts = datetime(2026, 5, 28, 9, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    relative_path, _ = export_continuity_pack(root, pack)
    return tmp_path / relative_path


# ---------------------------------------------------------------------------
# Core: inspect_continuity_pack — valid pack
# ---------------------------------------------------------------------------


def test_inspect_continuity_pack_returns_inspection(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert isinstance(result, ContinuityPackInspection)


def test_inspect_continuity_pack_valid_true(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert result.valid is True


def test_inspect_continuity_pack_exported_at(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert result.exported_at == datetime(2026, 5, 28, 9, 0, 0, tzinfo=timezone.utc).isoformat()


def test_inspect_continuity_pack_profile_type(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path, profile_name=PROFILE_IMPLEMENTATION)
    result = inspect_continuity_pack(pack_path)
    assert result.profile_type == PROFILE_IMPLEMENTATION


def test_inspect_continuity_pack_included_sections_complete(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    for section in CONTINUITY_PACK_INCLUDED_SECTIONS:
        assert section in result.included_sections


def test_inspect_continuity_pack_continuity_summary_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    cs = result.continuity_summary
    assert "active_task" in cs
    assert "governance_health" in cs
    assert "governance_check" in cs
    assert "provenance_event_count" in cs
    assert "orchestration_default_agent" in cs
    assert "compact_context_pack_present" in cs
    assert "compact_bootstrap_prompt_present" in cs
    assert "stale_context_suppression_present" in cs
    assert "vendor_neutral_note_present" in cs


def test_inspect_continuity_pack_active_task_present(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    at = result.continuity_summary["active_task"]
    assert at is not None
    assert at["id"] == "20260527-1200-test"
    assert at["title"] == "Test task"


def test_inspect_continuity_pack_active_task_none_when_no_task(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path, include_task=False)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert result.continuity_summary["active_task"] is None


def test_inspect_continuity_pack_compact_presence_flags(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    cs = result.continuity_summary
    assert cs["compact_context_pack_present"] is True
    assert cs["compact_bootstrap_prompt_present"] is True


def test_inspect_continuity_pack_stale_context_suppression_present(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert result.continuity_summary["stale_context_suppression_present"] is True


def test_inspect_continuity_pack_vendor_neutral_note_present(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert result.continuity_summary["vendor_neutral_note_present"] is True


def test_inspect_continuity_pack_portability_notes(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert len(result.portability_notes) > 0
    combined = " ".join(result.portability_notes).lower()
    assert "inspection only" in combined or "read for inspection" in combined


def test_inspect_continuity_pack_safety_notes(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert len(result.safety_notes) > 0
    combined = " ".join(result.safety_notes).lower()
    assert "runtime state" in combined or "read-only" in combined


def test_inspect_continuity_pack_advisory(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert result.advisory == CONTINUITY_PACK_INSPECTION_ADVISORY


def test_inspect_continuity_pack_to_dict_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    d = result.to_dict()
    assert "valid" in d
    assert "exported_at" in d
    assert "profile_type" in d
    assert "included_sections" in d
    assert "continuity_summary" in d
    assert "portability_notes" in d
    assert "safety_notes" in d
    assert "advisory" in d


def test_inspect_continuity_pack_is_read_only(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    mtime_before = pack_path.stat().st_mtime
    inspect_continuity_pack(pack_path)
    assert pack_path.stat().st_mtime == mtime_before
    # No new files created at runtime
    runtime_snapshots = tmp_path / ".pcae" / "runtime-snapshots"
    assert not runtime_snapshots.exists()


# ---------------------------------------------------------------------------
# Core: inspect_continuity_pack — error cases
# ---------------------------------------------------------------------------


def test_inspect_continuity_pack_file_not_found_raises() -> None:
    with pytest.raises(ValueError, match="not found"):
        inspect_continuity_pack(Path("/nonexistent/continuity-pack.json"))


def test_inspect_continuity_pack_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid continuity pack JSON"):
        inspect_continuity_pack(bad)


def test_inspect_continuity_pack_non_object_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('["a", "b"]', encoding="utf-8")
    with pytest.raises(ValueError, match="top-level JSON value must be an object"):
        inspect_continuity_pack(bad)


def test_inspect_continuity_pack_missing_keys_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"exported_at": "2026-05-28T00:00:00+00:00"}', encoding="utf-8")
    with pytest.raises(ValueError, match="missing required field"):
        inspect_continuity_pack(bad)


def test_inspect_continuity_pack_empty_exported_at_raises(tmp_path: Path) -> None:
    import json as _json
    data = {k: "placeholder" for k in CONTINUITY_PACK_REQUIRED_KEYS}
    data["exported_at"] = ""
    bad = tmp_path / "bad.json"
    bad.write_text(_json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="exported_at"):
        inspect_continuity_pack(bad)


def test_inspect_continuity_pack_required_keys_constant() -> None:
    assert "exported_at" in CONTINUITY_PACK_REQUIRED_KEYS
    assert "profile_type" in CONTINUITY_PACK_REQUIRED_KEYS
    assert "governance_state" in CONTINUITY_PACK_REQUIRED_KEYS
    assert "compact_bootstrap_prompt" in CONTINUITY_PACK_REQUIRED_KEYS
    assert "stale_context_suppression_rules" in CONTINUITY_PACK_REQUIRED_KEYS
    assert "vendor_neutral_note" in CONTINUITY_PACK_REQUIRED_KEYS


# ---------------------------------------------------------------------------
# CLI: pcae continuity inspect
# ---------------------------------------------------------------------------


def test_cli_continuity_inspect_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    result = main(["continuity", "inspect", str(pack_path)])
    assert result == 0


def test_cli_continuity_inspect_prints_validity(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path)])
    captured = capsys.readouterr()
    assert "Pack validity:" in captured.out
    assert "valid" in captured.out


def test_cli_continuity_inspect_prints_exported_at(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path)])
    captured = capsys.readouterr()
    assert "Exported:" in captured.out


def test_cli_continuity_inspect_prints_profile(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path)])
    captured = capsys.readouterr()
    assert "Profile:" in captured.out
    assert PROFILE_UNIVERSAL in captured.out


def test_cli_continuity_inspect_prints_included_sections(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path)])
    captured = capsys.readouterr()
    assert "Included sections:" in captured.out
    assert "active task summary" in captured.out


def test_cli_continuity_inspect_prints_continuity_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path)])
    captured = capsys.readouterr()
    assert "Continuity summary:" in captured.out
    assert "Governance health:" in captured.out
    assert "Governance check:" in captured.out


def test_cli_continuity_inspect_prints_portability_notes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path)])
    captured = capsys.readouterr()
    assert "Portability notes:" in captured.out


def test_cli_continuity_inspect_prints_safety_notes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path)])
    captured = capsys.readouterr()
    assert "Safety notes:" in captured.out


def test_cli_continuity_inspect_prints_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path)])
    captured = capsys.readouterr()
    assert CONTINUITY_PACK_INSPECTION_ADVISORY in captured.out


def test_cli_continuity_inspect_invalid_path_exits_nonzero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["continuity", "inspect", "/no/such/file.json"])
    assert result != 0


def test_cli_continuity_inspect_invalid_path_prints_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "inspect", "/no/such/file.json"])
    captured = capsys.readouterr()
    assert "not found" in captured.out.lower()


def test_cli_continuity_inspect_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    result = main(["continuity", "inspect", str(pack_path), "--json"])
    assert result == 0


def test_cli_continuity_inspect_json_is_valid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_cli_continuity_inspect_json_required_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "valid" in data
    assert "exported_at" in data
    assert "profile_type" in data
    assert "included_sections" in data
    assert "continuity_summary" in data
    assert "portability_notes" in data
    assert "safety_notes" in data
    assert "advisory" in data


def test_cli_continuity_inspect_json_valid_true(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is True


def test_cli_continuity_inspect_json_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["advisory"] == CONTINUITY_PACK_INSPECTION_ADVISORY


def test_cli_continuity_inspect_json_continuity_summary_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    capsys.readouterr()
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    main(["continuity", "inspect", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    cs = data["continuity_summary"]
    assert "active_task" in cs
    assert "governance_health" in cs
    assert "governance_check" in cs
    assert "compact_bootstrap_prompt_present" in cs
    assert "stale_context_suppression_present" in cs
    assert "vendor_neutral_note_present" in cs


def test_cli_continuity_inspect_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    mtime_before = pack_path.stat().st_mtime
    main(["continuity", "inspect", str(pack_path)])
    assert pack_path.stat().st_mtime == mtime_before
    # inspect must not create runtime-snapshots as a side effect
    assert not (tmp_path / ".pcae" / "runtime-snapshots").exists()


# ---------------------------------------------------------------------------
# Phase 35I: Continuity pack compatibility analysis
# ---------------------------------------------------------------------------

from pcae.core.context import (
    CONTINUITY_PACK_COMPATIBILITY_ADVISORY,
    CONTINUITY_PACK_REQUIRED_KEYS,
    ContinuityCompatibilityCheck,
    ContinuityCompatibilityReport,
    analyze_continuity_pack_compatibility,
)


# ---------------------------------------------------------------------------
# Core: analyze_continuity_pack_compatibility — valid pack
# ---------------------------------------------------------------------------


def test_analyze_continuity_compatibility_returns_report(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    assert isinstance(result, ContinuityCompatibilityReport)


def test_analyze_continuity_compatibility_compatible_true(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    assert result.compatible is True


def test_analyze_continuity_compatibility_support_level_supported(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    assert result.support_level == "supported"


def test_analyze_continuity_compatibility_no_warnings_on_valid_pack(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    assert len(result.warnings) == 0


def test_analyze_continuity_compatibility_ten_checks(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    assert len(result.compatibility_checks) == 10


def test_analyze_continuity_compatibility_all_checks_pass(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    for check in result.compatibility_checks:
        assert check.passed, f"Check failed: {check.name}: {check.message}"


def test_analyze_continuity_compatibility_check_names(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    names = {c.name for c in result.compatibility_checks}
    assert "continuity_pack_structure_validity" in names
    assert "required_continuity_sections_presence" in names
    assert "governance_state_presence" in names
    assert "compact_bootstrap_presence" in names
    assert "operational_rules_presence" in names
    assert "stale_context_suppression_presence" in names
    assert "vendor_neutral_note_presence" in names
    assert "runtime_snapshot_metadata_compatibility" in names
    assert "future_version_warning_support" in names


def test_analyze_continuity_compatibility_advisory(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    assert result.advisory == CONTINUITY_PACK_COMPATIBILITY_ADVISORY


def test_analyze_continuity_compatibility_continuity_summary_keys(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    cs = result.continuity_summary
    assert "active_task_id" in cs
    assert "active_task_title" in cs
    assert "exported_at" in cs
    assert "governance_health" in cs
    assert "governance_check" in cs
    assert "profile_type" in cs


def test_analyze_continuity_compatibility_continuity_summary_values(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    cs = result.continuity_summary
    assert cs["active_task_id"] == "20260527-1200-test"
    assert cs["active_task_title"] == "Test task"
    assert cs["profile_type"] == PROFILE_UNIVERSAL


def test_analyze_continuity_compatibility_to_dict_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    d = result.to_dict()
    assert "compatible" in d
    assert "support_level" in d
    assert "compatibility_checks" in d
    assert "warnings" in d
    assert "continuity_summary" in d
    assert "advisory" in d


def test_analyze_continuity_compatibility_check_to_dict(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    for check in result.compatibility_checks:
        d = check.to_dict()
        assert "name" in d
        assert "passed" in d
        assert "message" in d


def test_analyze_continuity_compatibility_is_read_only(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    mtime_before = pack_path.stat().st_mtime
    analyze_continuity_pack_compatibility(pack_path)
    assert pack_path.stat().st_mtime == mtime_before
    assert not (tmp_path / ".pcae" / "runtime-snapshots").exists()


# ---------------------------------------------------------------------------
# Core: analyze_continuity_pack_compatibility — degraded packs
# ---------------------------------------------------------------------------


def test_analyze_continuity_compatibility_missing_required_key_unsupported(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    data = json.loads(pack_path.read_text(encoding="utf-8"))
    del data["compact_bootstrap_prompt"]
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_continuity_pack_compatibility(pack_path)
    # missing required key → sections check fails → unsupported
    assert result.support_level == "unsupported"
    assert result.compatible is False


def test_analyze_continuity_compatibility_missing_required_key_warns(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    data = json.loads(pack_path.read_text(encoding="utf-8"))
    del data["vendor_neutral_note"]
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_continuity_pack_compatibility(pack_path)
    assert len(result.warnings) > 0


def test_analyze_continuity_compatibility_empty_bootstrap_partially_supported(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    data = json.loads(pack_path.read_text(encoding="utf-8"))
    data["compact_bootstrap_prompt"] = ""
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_continuity_pack_compatibility(pack_path)
    assert result.support_level in ("partially-supported", "unsupported")
    assert result.compatible is False


def test_analyze_continuity_compatibility_empty_stale_context_rules_warns(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    data = json.loads(pack_path.read_text(encoding="utf-8"))
    data["stale_context_suppression_rules"] = []
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_continuity_pack_compatibility(pack_path)
    check = next(
        c for c in result.compatibility_checks
        if c.name == "stale_context_suppression_presence"
    )
    assert not check.passed
    assert len(result.warnings) > 0


def test_analyze_continuity_compatibility_missing_vendor_neutral_note_warns(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    data = json.loads(pack_path.read_text(encoding="utf-8"))
    data["vendor_neutral_note"] = ""
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_continuity_pack_compatibility(pack_path)
    check = next(
        c for c in result.compatibility_checks
        if c.name == "vendor_neutral_note_presence"
    )
    assert not check.passed


def test_analyze_continuity_compatibility_extra_key_warns_future_version(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    data = json.loads(pack_path.read_text(encoding="utf-8"))
    data["future_field"] = "from_newer_pcae"
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_continuity_pack_compatibility(pack_path)
    check = next(
        c for c in result.compatibility_checks
        if c.name == "future_version_warning_support"
    )
    assert not check.passed
    assert "future_field" in check.message
    assert len(result.warnings) > 0


def test_analyze_continuity_compatibility_missing_rsm_keys_warns(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    data = json.loads(pack_path.read_text(encoding="utf-8"))
    data["runtime_snapshot_metadata"] = {"only_one_key": True}
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_continuity_pack_compatibility(pack_path)
    check = next(
        c for c in result.compatibility_checks
        if c.name == "runtime_snapshot_metadata_compatibility"
    )
    assert not check.passed


def test_analyze_continuity_compatibility_warnings_deduped(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    assert len(result.warnings) == len(set(result.warnings))


# ---------------------------------------------------------------------------
# Core: analyze_continuity_pack_compatibility — error cases
# ---------------------------------------------------------------------------


def test_analyze_continuity_compatibility_file_not_found_raises() -> None:
    with pytest.raises(ValueError, match="not found"):
        analyze_continuity_pack_compatibility(Path("/no/such/file.json"))


def test_analyze_continuity_compatibility_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid continuity pack JSON"):
        analyze_continuity_pack_compatibility(bad)


def test_analyze_continuity_compatibility_non_object_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('["a"]', encoding="utf-8")
    with pytest.raises(ValueError, match="top-level JSON value must be an object"):
        analyze_continuity_pack_compatibility(bad)


# ---------------------------------------------------------------------------
# CLI: pcae continuity compatibility
# ---------------------------------------------------------------------------


def _export_and_get_pack_path(tmp_path: Path) -> Path:
    monkeypatch_chdir = tmp_path  # used inline; export via subprocess not needed
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(None)
    ts = datetime(2026, 5, 28, 10, 0, 0, tzinfo=timezone.utc)
    pack = build_continuity_pack(root, profile, exported_at=ts)
    relative_path, _ = export_continuity_pack(root, pack)
    return tmp_path / relative_path


def test_cli_continuity_compatibility_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    result = main(["continuity", "compatibility", str(pack_path)])
    assert result == 0


def test_cli_continuity_compatibility_prints_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path)])
    captured = capsys.readouterr()
    assert "Compatibility status:" in captured.out
    assert "compatible" in captured.out


def test_cli_continuity_compatibility_prints_support_level(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path)])
    captured = capsys.readouterr()
    assert "Support level:" in captured.out
    assert "supported" in captured.out


def test_cli_continuity_compatibility_prints_checks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path)])
    captured = capsys.readouterr()
    assert "Compatibility checks:" in captured.out
    assert "continuity_pack_structure_validity" in captured.out
    assert "stale_context_suppression_presence" in captured.out
    assert "vendor_neutral_note_presence" in captured.out
    assert "future_version_warning_support" in captured.out


def test_cli_continuity_compatibility_prints_warnings_none(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path)])
    captured = capsys.readouterr()
    assert "Warnings:" in captured.out
    assert "none" in captured.out


def test_cli_continuity_compatibility_prints_governance_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path)])
    captured = capsys.readouterr()
    assert "Governance continuity summary:" in captured.out
    assert "Active task:" in captured.out
    assert "Profile:" in captured.out
    assert "Governance health:" in captured.out


def test_cli_continuity_compatibility_prints_portability_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path)])
    captured = capsys.readouterr()
    assert "Portability summary:" in captured.out


def test_cli_continuity_compatibility_prints_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path)])
    captured = capsys.readouterr()
    assert CONTINUITY_PACK_COMPATIBILITY_ADVISORY in captured.out


def test_cli_continuity_compatibility_invalid_path_exits_nonzero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["continuity", "compatibility", "/no/such/file.json"])
    assert result != 0


def test_cli_continuity_compatibility_invalid_path_prints_error(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "compatibility", "/no/such/file.json"])
    captured = capsys.readouterr()
    assert "not found" in captured.out.lower()


def test_cli_continuity_compatibility_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    result = main(["continuity", "compatibility", str(pack_path), "--json"])
    assert result == 0


def test_cli_continuity_compatibility_json_is_valid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_cli_continuity_compatibility_json_required_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "compatible" in data
    assert "support_level" in data
    assert "compatibility_checks" in data
    assert "warnings" in data
    assert "continuity_summary" in data
    assert "advisory" in data


def test_cli_continuity_compatibility_json_compatible_true(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["compatible"] is True
    assert data["support_level"] == "supported"


def test_cli_continuity_compatibility_json_ten_checks(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data["compatibility_checks"]) == 10


def test_cli_continuity_compatibility_json_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    main(["continuity", "compatibility", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["advisory"] == CONTINUITY_PACK_COMPATIBILITY_ADVISORY


def test_cli_continuity_compatibility_json_degraded_pack(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    pack_data = json.loads(pack_path.read_text(encoding="utf-8"))
    del pack_data["compact_bootstrap_prompt"]
    pack_path.write_text(json.dumps(pack_data), encoding="utf-8")
    main(["continuity", "compatibility", str(pack_path), "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["compatible"] is False
    assert data["support_level"] == "unsupported"
    assert len(data["warnings"]) > 0


def test_cli_continuity_compatibility_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    pack_path = _export_and_get_pack_path(tmp_path)
    mtime_before = pack_path.stat().st_mtime
    main(["continuity", "compatibility", str(pack_path)])
    assert pack_path.stat().st_mtime == mtime_before
    assert not (tmp_path / ".pcae" / "runtime-snapshots").exists()


# ---------------------------------------------------------------------------
# Phase 35J: Continuity pack manifest indexing
# ---------------------------------------------------------------------------

from pcae.core.context import (
    CONTINUITY_MANIFEST_ADVISORY,
    ContinuityManifest,
    ContinuityManifestEntry,
    build_continuity_manifest,
)


def _export_n_packs(
    tmp_path: Path, n: int, profile_name: str | None = None
) -> list[Path]:
    """Export n continuity packs with distinct timestamps; return paths newest-first."""
    root = HarnessPath(tmp_path)
    profile, _ = resolve_profile(profile_name)
    paths: list[Path] = []
    for i in range(n):
        ts = datetime(2026, 5, 28, 10, i, 0, tzinfo=timezone.utc)
        pack = build_continuity_pack(root, profile, exported_at=ts)
        relative_path, _ = export_continuity_pack(root, pack)
        paths.append(tmp_path / relative_path)
    return list(reversed(paths))  # newest-first


# ---------------------------------------------------------------------------
# Core: build_continuity_manifest — empty directory
# ---------------------------------------------------------------------------


def test_build_continuity_manifest_empty_returns_manifest(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert isinstance(result, ContinuityManifest)


def test_build_continuity_manifest_empty_no_packs_dir(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert result.pack_count == 0
    assert result.latest_pack is None
    assert result.manifest_entries == ()


def test_build_continuity_manifest_empty_summary_zeros(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    for key in ("compatible", "incompatible", "supported", "partially-supported", "unsupported"):
        assert result.compatibility_summary[key] == 0


def test_build_continuity_manifest_empty_advisory(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert result.advisory == CONTINUITY_MANIFEST_ADVISORY


# ---------------------------------------------------------------------------
# Core: build_continuity_manifest — with packs
# ---------------------------------------------------------------------------


def test_build_continuity_manifest_pack_count(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 3)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert result.pack_count == 3


def test_build_continuity_manifest_returns_manifest_entries(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 2)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert len(result.manifest_entries) == 2
    for entry in result.manifest_entries:
        assert isinstance(entry, ContinuityManifestEntry)


def test_build_continuity_manifest_entry_fields(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 1)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    entry = result.manifest_entries[0]
    assert entry.filename.startswith("continuity-pack-")
    assert entry.filename.endswith(".json")
    assert isinstance(entry.exported_at, str)
    assert entry.profile_type == PROFILE_UNIVERSAL
    assert entry.compatibility_status == "compatible"
    assert entry.support_level == "supported"
    assert entry.vendor_neutral is True
    assert entry.stale_context_suppression_present is True
    assert entry.compact_bootstrap_present is True


def test_build_continuity_manifest_entry_active_task(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 1)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert result.manifest_entries[0].active_task_id == "20260527-1200-test"


def test_build_continuity_manifest_entry_no_task(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path, include_task=False)
    _export_n_packs(tmp_path, 1)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert result.manifest_entries[0].active_task_id is None


def test_build_continuity_manifest_latest_pack_is_newest(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 3)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert result.latest_pack is not None
    latest_filename = result.latest_pack["filename"]
    assert latest_filename == result.manifest_entries[0].filename


def test_build_continuity_manifest_sorted_newest_first(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 3)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    exported_ats = [
        e.exported_at for e in result.manifest_entries
        if isinstance(e.exported_at, str)
    ]
    assert exported_ats == sorted(exported_ats, reverse=True)


def test_build_continuity_manifest_ordering_is_deterministic(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 3)
    result1 = build_continuity_manifest(HarnessPath(tmp_path))
    result2 = build_continuity_manifest(HarnessPath(tmp_path))
    assert [e.filename for e in result1.manifest_entries] == [
        e.filename for e in result2.manifest_entries
    ]


def test_build_continuity_manifest_compatibility_summary_counts(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 2)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    cs = result.compatibility_summary
    assert cs["compatible"] == 2
    assert cs["incompatible"] == 0
    assert cs["supported"] == 2
    assert cs["partially-supported"] == 0
    assert cs["unsupported"] == 0


def test_build_continuity_manifest_incompatible_entry_counted(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 1)
    # inject a broken pack
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    broken = packs_dir / "continuity-pack-20260101-000000.json"
    broken.write_text('{"only": "key"}', encoding="utf-8")
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert result.pack_count == 2
    incompatible = [e for e in result.manifest_entries if e.compatibility_status == "incompatible"]
    assert len(incompatible) == 1


def test_build_continuity_manifest_profile_implementation(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 1, profile_name=PROFILE_IMPLEMENTATION)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    assert result.manifest_entries[0].profile_type == PROFILE_IMPLEMENTATION


def test_build_continuity_manifest_to_dict_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 1)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    d = result.to_dict()
    assert "pack_count" in d
    assert "latest_pack" in d
    assert "manifest_entries" in d
    assert "compatibility_summary" in d
    assert "advisory" in d


def test_build_continuity_manifest_entry_to_dict_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 1)
    result = build_continuity_manifest(HarnessPath(tmp_path))
    d = result.manifest_entries[0].to_dict()
    for key in (
        "filename",
        "exported_at",
        "profile_type",
        "governance_health",
        "governance_check",
        "active_task_id",
        "compatibility_status",
        "support_level",
        "vendor_neutral",
        "stale_context_suppression_present",
        "compact_bootstrap_present",
    ):
        assert key in d, f"missing key: {key}"


def test_build_continuity_manifest_is_read_only(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    paths = _export_n_packs(tmp_path, 2)
    mtimes = {p: p.stat().st_mtime for p in paths}
    build_continuity_manifest(HarnessPath(tmp_path))
    for p, mtime in mtimes.items():
        assert p.stat().st_mtime == mtime
    assert not (tmp_path / ".pcae" / "runtime-snapshots").exists()


# ---------------------------------------------------------------------------
# CLI: pcae continuity manifest
# ---------------------------------------------------------------------------


def test_cli_continuity_manifest_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["continuity", "manifest"])
    assert result == 0


def test_cli_continuity_manifest_prints_pack_count(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 2)
    main(["continuity", "manifest"])
    captured = capsys.readouterr()
    assert "Pack count:" in captured.out
    assert "2" in captured.out


def test_cli_continuity_manifest_prints_latest_pack(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 1)
    main(["continuity", "manifest"])
    captured = capsys.readouterr()
    assert "Latest continuity pack:" in captured.out
    assert "continuity-pack-" in captured.out


def test_cli_continuity_manifest_no_packs_prints_none(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "manifest"])
    captured = capsys.readouterr()
    assert "Pack count: 0" in captured.out
    assert "none" in captured.out.lower()


def test_cli_continuity_manifest_prints_manifest_entries(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 2)
    main(["continuity", "manifest"])
    captured = capsys.readouterr()
    assert "Manifest entries:" in captured.out
    assert "compatibility=" in captured.out
    assert "vendor_neutral=" in captured.out
    assert "bootstrap=" in captured.out


def test_cli_continuity_manifest_prints_compatibility_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 1)
    main(["continuity", "manifest"])
    captured = capsys.readouterr()
    assert "Compatibility summary:" in captured.out
    assert "compatible:" in captured.out
    assert "supported:" in captured.out


def test_cli_continuity_manifest_prints_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "manifest"])
    captured = capsys.readouterr()
    assert CONTINUITY_MANIFEST_ADVISORY in captured.out


def test_cli_continuity_manifest_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["continuity", "manifest", "--json"])
    assert result == 0


def test_cli_continuity_manifest_json_is_valid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "manifest", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_cli_continuity_manifest_json_required_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "manifest", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "pack_count" in data
    assert "latest_pack" in data
    assert "manifest_entries" in data
    assert "compatibility_summary" in data
    assert "advisory" in data


def test_cli_continuity_manifest_json_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "manifest", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["pack_count"] == 0
    assert data["latest_pack"] is None
    assert data["manifest_entries"] == []


def test_cli_continuity_manifest_json_with_packs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 2)
    main(["continuity", "manifest", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["pack_count"] == 2
    assert data["latest_pack"] is not None
    assert len(data["manifest_entries"]) == 2


def test_cli_continuity_manifest_json_entry_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 1)
    main(["continuity", "manifest", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    entry = data["manifest_entries"][0]
    for key in (
        "filename",
        "exported_at",
        "profile_type",
        "governance_health",
        "governance_check",
        "active_task_id",
        "compatibility_status",
        "support_level",
        "vendor_neutral",
        "stale_context_suppression_present",
        "compact_bootstrap_present",
    ):
        assert key in entry, f"missing entry key: {key}"


def test_cli_continuity_manifest_json_newest_first(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 3)
    main(["continuity", "manifest", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    exported_ats = [e["exported_at"] for e in data["manifest_entries"]]
    assert exported_ats == sorted(exported_ats, reverse=True)


def test_cli_continuity_manifest_json_compatibility_summary_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 1)
    main(["continuity", "manifest", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    cs = data["compatibility_summary"]
    for key in ("compatible", "incompatible", "supported", "partially-supported", "unsupported"):
        assert key in cs


def test_cli_continuity_manifest_json_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "manifest", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["advisory"] == CONTINUITY_MANIFEST_ADVISORY


def test_cli_continuity_manifest_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    paths = _export_n_packs(tmp_path, 2)
    mtimes = {p: p.stat().st_mtime for p in paths}
    main(["continuity", "manifest"])
    for p, mtime in mtimes.items():
        assert p.stat().st_mtime == mtime
    assert not (tmp_path / ".pcae" / "runtime-snapshots").exists()


# ---------------------------------------------------------------------------
# Phase 35K: Continuity pack retention planning
# ---------------------------------------------------------------------------

from pcae.core.context import (
    CONTINUITY_RETENTION_ADVISORY,
    ContinuityRetentionPlan,
    plan_continuity_retention,
)


# ---------------------------------------------------------------------------
# Core: plan_continuity_retention — empty
# ---------------------------------------------------------------------------


def test_plan_continuity_retention_returns_plan(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = plan_continuity_retention(HarnessPath(tmp_path))
    assert isinstance(result, ContinuityRetentionPlan)


def test_plan_continuity_retention_empty_zero_counts(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = plan_continuity_retention(HarnessPath(tmp_path))
    assert result.pack_count == 0
    assert result.keep_count == 0
    assert result.prune_candidate_count == 0
    assert result.keep == ()
    assert result.prune_candidates == ()


def test_plan_continuity_retention_empty_advisory(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = plan_continuity_retention(HarnessPath(tmp_path))
    assert result.advisory == CONTINUITY_RETENTION_ADVISORY


# ---------------------------------------------------------------------------
# Core: plan_continuity_retention — fewer than 5 packs
# ---------------------------------------------------------------------------


def test_plan_continuity_retention_three_packs_all_kept(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 3)
    result = plan_continuity_retention(HarnessPath(tmp_path))
    assert result.pack_count == 3
    assert result.keep_count == 3
    assert result.prune_candidate_count == 0
    assert len(result.keep) == 3
    assert result.prune_candidates == ()


def test_plan_continuity_retention_five_packs_all_kept(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 5)
    result = plan_continuity_retention(HarnessPath(tmp_path))
    assert result.keep_count == 5
    assert result.prune_candidate_count == 0


# ---------------------------------------------------------------------------
# Core: plan_continuity_retention — more than 5 packs
# ---------------------------------------------------------------------------


def test_plan_continuity_retention_seven_packs_two_pruned(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 7)
    result = plan_continuity_retention(HarnessPath(tmp_path))
    assert result.pack_count == 7
    assert result.keep_count == 5
    assert result.prune_candidate_count == 2
    assert len(result.keep) == 5
    assert len(result.prune_candidates) == 2


def test_plan_continuity_retention_keep_newest_five(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    paths = _export_n_packs(tmp_path, 7)  # newest-first
    result = plan_continuity_retention(HarnessPath(tmp_path))
    newest_five = [p.name for p in paths[:5]]
    oldest_two = [p.name for p in paths[5:]]
    assert list(result.keep) == newest_five
    assert list(result.prune_candidates) == oldest_two


def test_plan_continuity_retention_counts_consistent(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 8)
    result = plan_continuity_retention(HarnessPath(tmp_path))
    assert result.keep_count + result.prune_candidate_count == result.pack_count


def test_plan_continuity_retention_to_dict_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 2)
    result = plan_continuity_retention(HarnessPath(tmp_path))
    d = result.to_dict()
    for key in (
        "pack_count",
        "keep_count",
        "prune_candidate_count",
        "keep",
        "prune_candidates",
        "advisory",
    ):
        assert key in d, f"missing key: {key}"


def test_plan_continuity_retention_to_dict_types(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    _export_n_packs(tmp_path, 3)
    result = plan_continuity_retention(HarnessPath(tmp_path))
    d = result.to_dict()
    assert isinstance(d["keep"], list)
    assert isinstance(d["prune_candidates"], list)
    assert isinstance(d["pack_count"], int)
    assert isinstance(d["keep_count"], int)
    assert isinstance(d["prune_candidate_count"], int)
    assert isinstance(d["advisory"], str)


def test_plan_continuity_retention_is_read_only(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    paths = _export_n_packs(tmp_path, 6)
    mtimes = {p: p.stat().st_mtime for p in paths}
    plan_continuity_retention(HarnessPath(tmp_path))
    for p, mtime in mtimes.items():
        assert p.stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# CLI: pcae continuity retention --dry-run
# ---------------------------------------------------------------------------


def test_cli_continuity_retention_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["continuity", "retention", "--dry-run"])
    assert result == 0


def test_cli_continuity_retention_prints_pack_count(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 3)
    main(["continuity", "retention", "--dry-run"])
    captured = capsys.readouterr()
    assert "Pack count: 3" in captured.out


def test_cli_continuity_retention_prints_keep_count(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 3)
    main(["continuity", "retention", "--dry-run"])
    captured = capsys.readouterr()
    assert "Keep count: 3" in captured.out


def test_cli_continuity_retention_prints_prune_candidate_count(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 7)
    main(["continuity", "retention", "--dry-run"])
    captured = capsys.readouterr()
    assert "Prune candidate count: 2" in captured.out


def test_cli_continuity_retention_prints_packs_to_keep(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 2)
    main(["continuity", "retention", "--dry-run"])
    captured = capsys.readouterr()
    assert "Packs to keep:" in captured.out
    assert "continuity-pack-" in captured.out


def test_cli_continuity_retention_prints_prune_candidates(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 7)
    main(["continuity", "retention", "--dry-run"])
    captured = capsys.readouterr()
    assert "Prune candidates:" in captured.out


def test_cli_continuity_retention_no_packs_none_label(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "retention", "--dry-run"])
    captured = capsys.readouterr()
    assert "Pack count: 0" in captured.out
    assert "none" in captured.out.lower()


def test_cli_continuity_retention_prints_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "retention", "--dry-run"])
    captured = capsys.readouterr()
    assert CONTINUITY_RETENTION_ADVISORY in captured.out


def test_cli_continuity_retention_does_not_delete_files(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    paths = _export_n_packs(tmp_path, 7)
    main(["continuity", "retention", "--dry-run"])
    for p in paths:
        assert p.exists(), f"file was deleted: {p.name}"


# ---------------------------------------------------------------------------
# CLI: pcae continuity retention --dry-run --json
# ---------------------------------------------------------------------------


def test_cli_continuity_retention_json_exits_zero(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = main(["continuity", "retention", "--dry-run", "--json"])
    assert result == 0


def test_cli_continuity_retention_json_is_valid(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "retention", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_cli_continuity_retention_json_required_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "retention", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    for key in (
        "pack_count",
        "keep_count",
        "prune_candidate_count",
        "keep",
        "prune_candidates",
        "advisory",
    ):
        assert key in data, f"missing JSON key: {key}"


def test_cli_continuity_retention_json_empty(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "retention", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["pack_count"] == 0
    assert data["keep_count"] == 0
    assert data["prune_candidate_count"] == 0
    assert data["keep"] == []
    assert data["prune_candidates"] == []


def test_cli_continuity_retention_json_with_packs(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    _export_n_packs(tmp_path, 7)
    main(["continuity", "retention", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["pack_count"] == 7
    assert data["keep_count"] == 5
    assert data["prune_candidate_count"] == 2
    assert len(data["keep"]) == 5
    assert len(data["prune_candidates"]) == 2


def test_cli_continuity_retention_json_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "retention", "--dry-run", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["advisory"] == CONTINUITY_RETENTION_ADVISORY


def test_cli_continuity_retention_json_is_read_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    paths = _export_n_packs(tmp_path, 7)
    main(["continuity", "retention", "--dry-run", "--json"])
    for p in paths:
        assert p.exists(), f"file was deleted: {p.name}"


# ---------------------------------------------------------------------------
# Phase 36L: Architecture memory continuity integration
# ---------------------------------------------------------------------------

from pcae.core.context import (
    ARCHITECTURE_MEMORY_ADVISORY,
    analyze_continuity_pack_compatibility,
)


def test_build_context_pack_has_architecture_memory_field(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    result = build_context_pack(HarnessPath(tmp_path))
    assert hasattr(result, "architecture_memory")
    assert isinstance(result.architecture_memory, dict)


def test_architecture_memory_summary_has_required_keys(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    mem = build_context_pack(HarnessPath(tmp_path)).architecture_memory
    assert "decision_count" in mem
    assert "accepted_count" in mem
    assert "latest_decision" in mem
    assert "advisory" in mem


def test_architecture_memory_decision_count_at_least_sample(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    mem = build_context_pack(HarnessPath(tmp_path)).architecture_memory
    assert mem["decision_count"] >= 2


def test_architecture_memory_accepted_count_is_int(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    mem = build_context_pack(HarnessPath(tmp_path)).architecture_memory
    assert isinstance(mem["accepted_count"], int)
    assert mem["accepted_count"] >= 0


def test_architecture_memory_latest_decision_has_fields(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    latest = build_context_pack(HarnessPath(tmp_path)).architecture_memory["latest_decision"]
    assert latest is not None
    assert "id" in latest
    assert "title" in latest
    assert "status" in latest


def test_architecture_memory_advisory_matches_constant(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    mem = build_context_pack(HarnessPath(tmp_path)).architecture_memory
    assert mem["advisory"] == ARCHITECTURE_MEMORY_ADVISORY


def test_context_pack_to_dict_includes_architecture_memory(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    d = build_context_pack(HarnessPath(tmp_path)).to_dict()
    assert "architecture_memory" in d
    assert isinstance(d["architecture_memory"], dict)
    assert "decision_count" in d["architecture_memory"]


def test_bootstrap_prompt_includes_architecture_memory_line(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack = build_context_pack(HarnessPath(tmp_path))
    profile, _ = resolve_profile(None)
    prompt = build_bootstrap_prompt(pack, profile)
    assert "Architecture memory:" in prompt
    assert "decisions" in prompt
    assert "accepted" in prompt
    assert "latest:" in prompt


def test_build_continuity_pack_has_architecture_memory(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    result = build_continuity_pack(HarnessPath(tmp_path), profile)
    assert hasattr(result, "architecture_memory")
    assert isinstance(result.architecture_memory, dict)
    assert "decision_count" in result.architecture_memory


def test_continuity_pack_to_dict_includes_architecture_memory(tmp_path: Path) -> None:
    write_minimal_context_artifacts(tmp_path)
    profile, _ = resolve_profile(None)
    d = build_continuity_pack(HarnessPath(tmp_path), profile).to_dict()
    assert "architecture_memory" in d
    assert isinstance(d["architecture_memory"], dict)


def test_inspect_continuity_pack_architecture_memory_present_true(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert "architecture_memory_present" in result.continuity_summary
    assert result.continuity_summary["architecture_memory_present"] is True


def test_inspect_continuity_pack_architecture_memory_section_in_included(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = inspect_continuity_pack(pack_path)
    assert "architecture memory" in result.included_sections


def test_inspect_continuity_pack_architecture_memory_absent(
    tmp_path: Path,
) -> None:
    data: dict = {k: None for k in CONTINUITY_PACK_REQUIRED_KEYS}
    data["exported_at"] = "2026-01-01T00:00:00+00:00"
    data["profile_type"] = "universal"
    data["governance_state"] = {"health_status": "healthy", "check_status": "passed"}
    data["orchestration_state"] = {}
    data["provenance_summary"] = {"event_count": 0}
    pack_path = tmp_path / "old-pack.json"
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = inspect_continuity_pack(pack_path)
    assert result.continuity_summary["architecture_memory_present"] is False


def test_continuity_compatibility_has_architecture_memory_check(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    check_names = [c.name for c in result.compatibility_checks]
    assert "architecture_memory_presence" in check_names


def test_continuity_compatibility_architecture_memory_passes_when_present(
    tmp_path: Path,
) -> None:
    write_minimal_context_artifacts(tmp_path)
    pack_path = _export_pack_for_inspection(tmp_path)
    result = analyze_continuity_pack_compatibility(pack_path)
    arch_check = next(
        c for c in result.compatibility_checks if c.name == "architecture_memory_presence"
    )
    assert arch_check.passed is True


def test_continuity_compatibility_architecture_memory_check_fails_when_absent(
    tmp_path: Path,
) -> None:
    data: dict = {k: None for k in CONTINUITY_PACK_REQUIRED_KEYS}
    data["exported_at"] = "2026-01-01T00:00:00+00:00"
    data["profile_type"] = "universal"
    data["governance_state"] = {"health_status": "healthy", "check_status": "passed"}
    pack_path = tmp_path / "old-pack.json"
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_continuity_pack_compatibility(pack_path)
    arch_check = next(
        c for c in result.compatibility_checks if c.name == "architecture_memory_presence"
    )
    assert arch_check.passed is False


def test_continuity_compatibility_architecture_memory_absence_does_not_break_compat(
    tmp_path: Path,
) -> None:
    data: dict = {k: "placeholder" for k in CONTINUITY_PACK_REQUIRED_KEYS}
    data["exported_at"] = "2026-01-01T00:00:00+00:00"
    data["profile_type"] = "universal"
    data["governance_state"] = {"health_status": "healthy", "check_status": "passed"}
    data["compact_bootstrap_prompt"] = "bootstrap text"
    data["operational_rules"] = ["rule"]
    data["stale_context_suppression_rules"] = ["rule"]
    data["vendor_neutral_note"] = "note"
    data["runtime_snapshot_metadata"] = {
        "governance_health_status": "healthy",
        "governance_check_status": "passed",
        "active_task": None,
        "agent_lock_state": None,
        "session_continuity_status": "verified",
        "provenance_event_count": 0,
    }
    pack_path = tmp_path / "old-pack.json"
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_continuity_pack_compatibility(pack_path)
    assert result.compatible is True


def test_cli_context_pack_preview_includes_architecture_memory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview"])
    output = capsys.readouterr().out
    assert "Architecture memory:" in output
    assert "Decision count:" in output
    assert "Accepted:" in output
    assert "Latest:" in output


def test_cli_context_pack_json_includes_architecture_memory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["context", "pack", "--preview", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "architecture_memory" in data
    mem = data["architecture_memory"]
    assert "decision_count" in mem
    assert "accepted_count" in mem
    assert "latest_decision" in mem


def test_cli_continuity_inspect_shows_architecture_memory_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export"])
    packs_dir = tmp_path / ".pcae" / "continuity-packs"
    pack_path = next(packs_dir.glob("continuity-pack-*.json"))
    capsys.readouterr()
    main(["continuity", "inspect", str(pack_path)])
    output = capsys.readouterr().out
    assert "Architecture memory present:" in output
    assert "True" in output


def test_cli_continuity_export_json_includes_architecture_memory_present(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_minimal_context_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)
    main(["continuity", "export", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert "architecture_memory_present" in data["continuity_summary"]
    assert data["continuity_summary"]["architecture_memory_present"] is True


def test_continuity_included_sections_has_architecture_memory() -> None:
    assert "architecture memory" in CONTINUITY_PACK_INCLUDED_SECTIONS
