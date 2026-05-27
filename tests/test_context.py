from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from pcae.cli import main
from pcae.core.context import (
    CONTEXT_PACK_ADVISORY,
    CONTEXT_PACK_OPERATIONAL_RULES,
    CONTEXT_PACK_VALIDATION_COMMANDS,
    build_context_pack,
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
            "## Status\n\nactive\n",
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
    assert "does not relax governance constraints" in result.advisory


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
    assert "does not relax governance constraints" in output


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
    assert "does not relax governance constraints" in data["advisory"]


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
