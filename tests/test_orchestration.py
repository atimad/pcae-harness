from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.core.orchestration import (
    build_agent_registry_data,
    build_orchestration_data,
    build_workflow_plan,
    build_workflow_simulation,
    build_workflow_validation,
    load_agent_registry,
    load_orchestration_policy,
    recommend_agent,
)
from pcae.core.paths import HarnessPath
from pcae.core.policy import (
    DEFAULT_AGENT_REGISTRY,
    DEFAULT_ORCHESTRATION_DEFAULT_AGENT,
    DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT,
    DEFAULT_ORCHESTRATION_RUNTIME_AGENT,
    DEFAULT_ORCHESTRATION_VALIDATION_AGENT,
)


# ---------------------------------------------------------------------------
# core helpers
# ---------------------------------------------------------------------------


def test_load_orchestration_policy_defaults_when_no_policy_file(tmp_path: Path) -> None:
    result = load_orchestration_policy(HarnessPath(tmp_path))
    assert result.default_agent == DEFAULT_ORCHESTRATION_DEFAULT_AGENT
    assert result.documentation_agent == DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT
    assert result.runtime_agent == DEFAULT_ORCHESTRATION_RUNTIME_AGENT
    assert result.validation_agent == DEFAULT_ORCHESTRATION_VALIDATION_AGENT


def test_load_orchestration_policy_defaults_when_section_missing(tmp_path: Path) -> None:
    write_policy(tmp_path, minimal_policy())
    result = load_orchestration_policy(HarnessPath(tmp_path))
    assert result.default_agent == DEFAULT_ORCHESTRATION_DEFAULT_AGENT
    assert result.documentation_agent == DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT
    assert result.runtime_agent == DEFAULT_ORCHESTRATION_RUNTIME_AGENT
    assert result.validation_agent == DEFAULT_ORCHESTRATION_VALIDATION_AGENT


def test_load_orchestration_policy_reads_overrides(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[orchestration]\ndefault_agent = "my-agent"\ndocumentation_agent = "doc-agent"\nruntime_agent = "run-agent"\nvalidation_agent = "val-agent"\n',
    )
    result = load_orchestration_policy(HarnessPath(tmp_path))
    assert result.default_agent == "my-agent"
    assert result.documentation_agent == "doc-agent"
    assert result.runtime_agent == "run-agent"
    assert result.validation_agent == "val-agent"


def test_load_orchestration_policy_partial_override_applies_defaults(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        minimal_policy() + '\n[orchestration]\nruntime_agent = "fast-agent"\n',
    )
    result = load_orchestration_policy(HarnessPath(tmp_path))
    assert result.runtime_agent == "fast-agent"
    assert result.default_agent == DEFAULT_ORCHESTRATION_DEFAULT_AGENT
    assert result.documentation_agent == DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT
    assert result.validation_agent == DEFAULT_ORCHESTRATION_VALIDATION_AGENT


def test_load_orchestration_policy_raises_on_invalid_policy(tmp_path: Path) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    with pytest.raises(ValueError):
        load_orchestration_policy(HarnessPath(tmp_path))


def test_build_orchestration_data_returns_dict(tmp_path: Path) -> None:
    write_policy(tmp_path, minimal_policy())
    data = build_orchestration_data(HarnessPath(tmp_path))
    assert set(data.keys()) == {
        "default_agent",
        "documentation_agent",
        "runtime_agent",
        "validation_agent",
    }
    assert data["default_agent"] == DEFAULT_ORCHESTRATION_DEFAULT_AGENT


# ---------------------------------------------------------------------------
# CLI: pcae orchestration policy
# ---------------------------------------------------------------------------


def test_cli_orchestration_policy_human(tmp_path: Path, monkeypatch, capsys) -> None:
    write_policy(tmp_path, minimal_policy())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "policy"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Orchestration policy" in output
    assert f"Default agent: {DEFAULT_ORCHESTRATION_DEFAULT_AGENT}" in output
    assert f"Documentation agent: {DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT}" in output
    assert f"Runtime agent: {DEFAULT_ORCHESTRATION_RUNTIME_AGENT}" in output
    assert f"Validation agent: {DEFAULT_ORCHESTRATION_VALIDATION_AGENT}" in output


def test_cli_orchestration_policy_json(tmp_path: Path, monkeypatch, capsys) -> None:
    write_policy(tmp_path, minimal_policy())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "policy", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert set(data.keys()) == {
        "default_agent",
        "documentation_agent",
        "runtime_agent",
        "validation_agent",
    }
    assert data["default_agent"] == DEFAULT_ORCHESTRATION_DEFAULT_AGENT


def test_cli_orchestration_policy_json_overrides(tmp_path: Path, monkeypatch, capsys) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[orchestration]\ndefault_agent = "opus"\nruntime_agent = "codex-turbo"\n',
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "policy", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["default_agent"] == "opus"
    assert data["runtime_agent"] == "codex-turbo"
    assert data["documentation_agent"] == DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT


def test_cli_orchestration_policy_fails_on_invalid_policy(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "policy"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert output.strip()


def test_cli_orchestration_policy_no_file_uses_defaults(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "policy"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert f"Default agent: {DEFAULT_ORCHESTRATION_DEFAULT_AGENT}" in output


# ---------------------------------------------------------------------------
# core helpers: agent registry
# ---------------------------------------------------------------------------


def test_load_agent_registry_defaults_when_no_policy_file(tmp_path: Path) -> None:
    registry = load_agent_registry(HarnessPath(tmp_path))
    assert registry == DEFAULT_AGENT_REGISTRY


def test_load_agent_registry_defaults_when_section_missing(tmp_path: Path) -> None:
    write_policy(tmp_path, minimal_policy())
    registry = load_agent_registry(HarnessPath(tmp_path))
    assert registry == DEFAULT_AGENT_REGISTRY


def test_load_agent_registry_reads_configured_agents(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[agents.my-agent]\nkind = "custom"\nroles = ["analysis"]\n',
    )
    registry = load_agent_registry(HarnessPath(tmp_path))
    assert len(registry) == 1
    assert registry[0].agent_id == "my-agent"
    assert registry[0].kind == "custom"
    assert registry[0].roles == ("analysis",)


def test_load_agent_registry_multiple_agents(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[agents.a]\nkind = "ka"\nroles = ["r1"]\n\n[agents.b]\nkind = "kb"\nroles = ["r2", "r3"]\n',
    )
    registry = load_agent_registry(HarnessPath(tmp_path))
    assert len(registry) == 2
    assert registry[0].agent_id == "a"
    assert registry[1].agent_id == "b"
    assert registry[1].roles == ("r2", "r3")


def test_load_agent_registry_raises_on_invalid_policy(tmp_path: Path) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    with pytest.raises(ValueError):
        load_agent_registry(HarnessPath(tmp_path))


def test_build_agent_registry_data_returns_list_of_dicts(tmp_path: Path) -> None:
    write_policy(tmp_path, minimal_policy())
    data = build_agent_registry_data(HarnessPath(tmp_path))
    assert isinstance(data, list)
    assert len(data) == len(DEFAULT_AGENT_REGISTRY)
    for entry in data:
        assert set(entry.keys()) == {"agent_id", "kind", "roles"}
        assert isinstance(entry["roles"], list)


# ---------------------------------------------------------------------------
# CLI: pcae orchestration agents
# ---------------------------------------------------------------------------


def test_cli_orchestration_agents_human(tmp_path: Path, monkeypatch, capsys) -> None:
    write_policy(tmp_path, minimal_policy())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "agents"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Agent registry" in output
    assert "claude-local" in output
    assert "codex-local" in output
    assert "pcae-native" in output


def test_cli_orchestration_agents_shows_kind_and_roles(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy(tmp_path, minimal_policy())
    monkeypatch.chdir(tmp_path)

    main(["orchestration", "agents"])

    output = capsys.readouterr().out
    assert "claude" in output
    assert "documentation" in output
    assert "codex" in output
    assert "runtime" in output


def test_cli_orchestration_agents_json(tmp_path: Path, monkeypatch, capsys) -> None:
    write_policy(tmp_path, minimal_policy())
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "agents", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert isinstance(data, list)
    assert len(data) == len(DEFAULT_AGENT_REGISTRY)
    for entry in data:
        assert set(entry.keys()) == {"agent_id", "kind", "roles"}


def test_cli_orchestration_agents_json_configured(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[agents.custom]\nkind = "mymodel"\nroles = ["analysis", "tests"]\n',
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "agents", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert len(data) == 1
    assert data[0]["agent_id"] == "custom"
    assert data[0]["kind"] == "mymodel"
    assert data[0]["roles"] == ["analysis", "tests"]


def test_cli_orchestration_agents_fails_on_invalid_policy(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "agents"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert output.strip()


def test_cli_orchestration_agents_no_file_uses_defaults(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["orchestration", "agents"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "claude-local" in output


# ---------------------------------------------------------------------------
# core: recommend_agent
# ---------------------------------------------------------------------------


def test_recommend_agent_documentation_returns_claude_local(tmp_path: Path) -> None:
    result = recommend_agent(HarnessPath(tmp_path), "documentation")
    assert result["recommended_agent"] == "claude-local"
    assert result["work_type"] == "documentation"
    assert result["matched_role"] == "documentation"
    assert result["fallback_used"] is False


def test_recommend_agent_implementation_returns_codex_local(tmp_path: Path) -> None:
    result = recommend_agent(HarnessPath(tmp_path), "implementation")
    assert result["recommended_agent"] == "codex-local"
    assert result["matched_role"] == "implementation"
    assert result["fallback_used"] is False


def test_recommend_agent_validation_returns_pcae_native(tmp_path: Path) -> None:
    result = recommend_agent(HarnessPath(tmp_path), "validation")
    assert result["recommended_agent"] == "pcae-native"
    assert result["matched_role"] == "validation"
    assert result["fallback_used"] is False


def test_recommend_agent_unknown_falls_back_to_default(tmp_path: Path) -> None:
    result = recommend_agent(HarnessPath(tmp_path), "unknown-work-type")
    assert result["recommended_agent"] == "claude-local"
    assert result["matched_role"] is None
    assert result["fallback_used"] is True
    assert "unknown-work-type" in result["reason"]


def test_recommend_agent_result_keys(tmp_path: Path) -> None:
    result = recommend_agent(HarnessPath(tmp_path), "architecture")
    assert set(result.keys()) == {
        "work_type",
        "recommended_agent",
        "reason",
        "matched_role",
        "fallback_used",
    }


def test_recommend_agent_multiple_matches_prefers_default_agent(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[orchestration]\ndefault_agent = "agent-b"\n'
        + '\n[agents.agent-a]\nkind = "ka"\nroles = ["shared-role"]\n'
        + '\n[agents.agent-b]\nkind = "kb"\nroles = ["shared-role"]\n',
    )
    result = recommend_agent(HarnessPath(tmp_path), "shared-role")
    assert result["recommended_agent"] == "agent-b"
    assert result["fallback_used"] is False


def test_recommend_agent_multiple_matches_first_when_default_not_matching(
    tmp_path: Path,
) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[orchestration]\ndefault_agent = "agent-c"\n'
        + '\n[agents.agent-a]\nkind = "ka"\nroles = ["shared-role"]\n'
        + '\n[agents.agent-b]\nkind = "kb"\nroles = ["shared-role"]\n',
    )
    result = recommend_agent(HarnessPath(tmp_path), "shared-role")
    assert result["recommended_agent"] == "agent-a"
    assert result["fallback_used"] is False


def test_recommend_agent_raises_on_invalid_policy(tmp_path: Path) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    with pytest.raises(ValueError):
        recommend_agent(HarnessPath(tmp_path), "documentation")


# ---------------------------------------------------------------------------
# CLI: pcae orchestration recommend
# ---------------------------------------------------------------------------


def test_cli_orchestration_recommend_human_documentation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "recommend", "--work-type", "documentation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Work type: documentation" in output
    assert "claude-local" in output
    assert "Reason:" in output


def test_cli_orchestration_recommend_human_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "recommend", "--work-type", "implementation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "codex-local" in output


def test_cli_orchestration_recommend_human_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "recommend", "--work-type", "validation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "pcae-native" in output


def test_cli_orchestration_recommend_human_fallback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "recommend", "--work-type", "no-such-role"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "claude-local" in output


def test_cli_orchestration_recommend_json(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "recommend", "--work-type", "documentation", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert set(data.keys()) == {
        "work_type",
        "recommended_agent",
        "reason",
        "matched_role",
        "fallback_used",
    }
    assert data["recommended_agent"] == "claude-local"
    assert data["matched_role"] == "documentation"
    assert data["fallback_used"] is False


def test_cli_orchestration_recommend_json_fallback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "recommend", "--work-type", "unknown", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["fallback_used"] is True
    assert data["matched_role"] is None
    assert data["recommended_agent"] == "claude-local"


def test_cli_orchestration_recommend_fails_on_invalid_policy(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "recommend", "--work-type", "documentation"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert output.strip()


# ---------------------------------------------------------------------------
# core: build_workflow_plan
# ---------------------------------------------------------------------------


def test_build_workflow_plan_documentation_steps(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "documentation")
    assert result["workflow"] == "documentation"
    steps = result["steps"]
    assert len(steps) == 3
    assert steps[0]["assigned_agent"] == "claude-local"
    assert steps[1]["assigned_agent"] == "claude-local"
    assert steps[2]["assigned_agent"] == "pcae-native"


def test_build_workflow_plan_documentation_work_types(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "documentation")
    labels = [s["work_type"] for s in result["steps"]]
    assert labels == ["architecture review", "documentation", "governance validation"]


def test_build_workflow_plan_implementation_steps(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "implementation")
    assert result["workflow"] == "implementation"
    steps = result["steps"]
    assert len(steps) == 3
    assert steps[0]["assigned_agent"] == "codex-local"
    assert steps[1]["assigned_agent"] == "codex-local"
    assert steps[2]["assigned_agent"] == "pcae-native"


def test_build_workflow_plan_implementation_work_types(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "implementation")
    labels = [s["work_type"] for s in result["steps"]]
    assert labels == ["implementation", "tests", "governance validation"]


def test_build_workflow_plan_validation_steps(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "validation")
    assert result["workflow"] == "validation"
    steps = result["steps"]
    assert len(steps) == 3
    assert steps[0]["assigned_agent"] == "pcae-native"
    assert steps[1]["assigned_agent"] == "pcae-native"
    assert steps[2]["assigned_agent"] == "claude-local"


def test_build_workflow_plan_release_steps(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "release")
    assert result["workflow"] == "release"
    steps = result["steps"]
    assert len(steps) == 3
    assert steps[0]["assigned_agent"] == "pcae-native"
    assert steps[1]["assigned_agent"] == "pcae-native"
    assert steps[2]["assigned_agent"] == "claude-local"


def test_build_workflow_plan_release_work_types(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "release")
    labels = [s["work_type"] for s in result["steps"]]
    assert labels == [
        "governance validation",
        "provenance verification",
        "release notes/documentation",
    ]


def test_build_workflow_plan_steps_are_ordered(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "implementation")
    step_numbers = [s["step"] for s in result["steps"]]
    assert step_numbers == list(range(1, len(step_numbers) + 1))


def test_build_workflow_plan_step_keys(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "documentation")
    for step in result["steps"]:
        assert set(step.keys()) == {
            "step",
            "work_type",
            "assigned_agent",
            "recommended_agent",
            "reason",
        }


def test_build_workflow_plan_steps_include_reasons(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "documentation")
    for step in result["steps"]:
        assert step["reason"]


def test_build_workflow_plan_unknown_workflow_fallback(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "no-such-workflow")
    assert result["workflow"] == "no-such-workflow"
    steps = result["steps"]
    assert len(steps) == 1
    assert steps[0]["assigned_agent"] == "claude-local"
    assert "no-such-workflow" in steps[0]["reason"]
    assert steps[0]["work_type"] == "no-such-workflow"


def test_build_workflow_plan_unknown_uses_default_agent_from_policy(
    tmp_path: Path,
) -> None:
    write_policy(
        tmp_path,
        minimal_policy() + '\n[orchestration]\ndefault_agent = "my-default"\n',
    )
    result = build_workflow_plan(HarnessPath(tmp_path), "unknown")
    assert result["steps"][0]["assigned_agent"] == "my-default"


def test_build_workflow_plan_result_top_level_keys(tmp_path: Path) -> None:
    result = build_workflow_plan(HarnessPath(tmp_path), "documentation")
    assert set(result.keys()) == {"workflow", "recommendation_note", "steps"}


def test_build_workflow_plan_raises_on_invalid_policy(tmp_path: Path) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    with pytest.raises(ValueError):
        build_workflow_plan(HarnessPath(tmp_path), "documentation")


def test_build_workflow_plan_respects_custom_agent_registry(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[agents.custom-impl]\nkind = "custom"\nroles = ["implementation", "tests", "governance"]\n',
    )
    result = build_workflow_plan(HarnessPath(tmp_path), "implementation")
    for step in result["steps"]:
        assert step["assigned_agent"] == "custom-impl"


# ---------------------------------------------------------------------------
# core: build_workflow_simulation
# ---------------------------------------------------------------------------


def test_build_workflow_simulation_documentation(tmp_path: Path) -> None:
    result = build_workflow_simulation(HarnessPath(tmp_path), "documentation")
    assert result["workflow"] == "documentation"
    assert result["status"] == "planned"
    assert result["execution_mode"] == "simulation"
    assert "advisory" in result["recommendation_note"]
    assert len(result["steps"]) == 3
    assert result["steps"][2]["governance_checkpoint"] == "pcae check"


def test_build_workflow_simulation_implementation(tmp_path: Path) -> None:
    result = build_workflow_simulation(HarnessPath(tmp_path), "implementation")
    assert result["workflow"] == "implementation"
    assert [step["work_type"] for step in result["steps"]] == [
        "implementation",
        "tests",
        "governance validation",
    ]


def test_build_workflow_simulation_release(tmp_path: Path) -> None:
    result = build_workflow_simulation(HarnessPath(tmp_path), "release")
    assert result["workflow"] == "release"
    assert result["steps"][0]["governance_checkpoint"] == "pcae check"
    assert (
        result["steps"][1]["governance_checkpoint"]
        == "pcae provenance session current"
    )


def test_build_workflow_simulation_unknown_fallback(tmp_path: Path) -> None:
    result = build_workflow_simulation(HarnessPath(tmp_path), "unknown-workflow")
    assert result["workflow"] == "unknown-workflow"
    assert result["status"] == "planned"
    assert len(result["steps"]) == 1
    assert result["steps"][0]["assigned_agent"] == "claude-local"
    assert result["steps"][0]["governance_checkpoint"] is None


def test_build_workflow_simulation_step_keys(tmp_path: Path) -> None:
    result = build_workflow_simulation(HarnessPath(tmp_path), "documentation")
    for step in result["steps"]:
        assert set(step.keys()) == {
            "step",
            "assigned_agent",
            "recommended_agent",
            "work_type",
            "reason",
            "governance_checkpoint",
        }


# ---------------------------------------------------------------------------
# core: build_workflow_validation
# ---------------------------------------------------------------------------


def test_build_workflow_validation_documentation(tmp_path: Path) -> None:
    result = build_workflow_validation(HarnessPath(tmp_path), "documentation")
    assert result["workflow"] == "documentation"
    assert result["valid"] is True
    assert result["fallback_used"] is False
    assert result["warnings"] == []
    assert len(result["validated_steps"]) == 3
    assert result["governance_checkpoints"][0]["checkpoint"] == "pcae check"


def test_build_workflow_validation_implementation(tmp_path: Path) -> None:
    result = build_workflow_validation(HarnessPath(tmp_path), "implementation")
    assert result["valid"] is True
    assert [step["recommended_agent"] for step in result["validated_steps"]] == [
        "codex-local",
        "codex-local",
        "pcae-native",
    ]


def test_build_workflow_validation_release(tmp_path: Path) -> None:
    result = build_workflow_validation(HarnessPath(tmp_path), "release")
    assert result["valid"] is True
    checkpoints = [entry["checkpoint"] for entry in result["governance_checkpoints"]]
    assert "pcae check" in checkpoints
    assert "pcae provenance session current" in checkpoints


def test_build_workflow_validation_unknown_fallback(tmp_path: Path) -> None:
    result = build_workflow_validation(HarnessPath(tmp_path), "unknown-workflow")
    assert result["workflow"] == "unknown-workflow"
    assert result["valid"] is True
    assert result["fallback_used"] is True
    assert result["warnings"] == [
        "Unknown workflow 'unknown-workflow' uses deterministic default-agent fallback."
    ]
    assert result["validated_steps"][0]["recommended_role"] is None


def test_build_workflow_validation_result_keys(tmp_path: Path) -> None:
    result = build_workflow_validation(HarnessPath(tmp_path), "documentation")
    assert set(result.keys()) == {
        "workflow",
        "valid",
        "warnings",
        "validated_steps",
        "governance_checkpoints",
        "fallback_used",
    }


def test_build_workflow_validation_step_keys(tmp_path: Path) -> None:
    result = build_workflow_validation(HarnessPath(tmp_path), "documentation")
    for step in result["validated_steps"]:
        assert set(step.keys()) == {
            "step",
            "work_type",
            "recommended_agent",
            "agent_exists",
            "recommended_role",
            "role_matched",
        }


def test_build_workflow_validation_flags_missing_role(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[agents.custom]\nkind = "custom"\nroles = ["implementation"]\n',
    )
    result = build_workflow_validation(HarnessPath(tmp_path), "implementation")
    assert result["valid"] is False
    assert any("no registered agent role 'tests'" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# CLI: pcae orchestration plan
# ---------------------------------------------------------------------------


def test_cli_orchestration_plan_human_documentation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "documentation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Suggested workflow plan: documentation" in output
    assert "Recommendations are advisory; the user may override them." in output
    assert "Recommended agent:" in output
    assert "claude-local" in output
    assert "pcae-native" in output
    assert "architecture review" in output
    assert "governance validation" in output


def test_cli_orchestration_plan_human_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "implementation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Suggested workflow plan: implementation" in output
    assert "codex-local" in output
    assert "implementation" in output
    assert "tests" in output


def test_cli_orchestration_plan_human_validation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "validation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Suggested workflow plan: validation" in output
    assert "pcae-native" in output
    assert "claude-local" in output


def test_cli_orchestration_plan_human_release(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "release"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Suggested workflow plan: release" in output
    assert "pcae-native" in output
    assert "claude-local" in output
    assert "governance validation" in output
    assert "release notes/documentation" in output


def test_cli_orchestration_plan_human_unknown_fallback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "no-such-wf"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Suggested workflow plan: no-such-wf" in output
    assert "claude-local" in output
    assert "no-such-wf" in output


def test_cli_orchestration_plan_human_shows_reasons(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["orchestration", "plan", "--workflow", "implementation"])
    output = capsys.readouterr().out
    assert "Reason:" in output


def test_cli_orchestration_plan_human_shows_step_numbers(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    main(["orchestration", "plan", "--workflow", "implementation"])
    output = capsys.readouterr().out
    assert "1." in output
    assert "2." in output
    assert "3." in output


def test_cli_orchestration_plan_json_documentation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "documentation", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["workflow"] == "documentation"
    assert "recommendation_note" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) == 3
    assert data["steps"][0]["assigned_agent"] == "claude-local"
    assert data["steps"][2]["assigned_agent"] == "pcae-native"


def test_cli_orchestration_plan_json_step_keys(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "implementation", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert set(data.keys()) == {"workflow", "recommendation_note", "steps"}
    for step in data["steps"]:
        assert set(step.keys()) == {
            "step",
            "work_type",
            "assigned_agent",
            "recommended_agent",
            "reason",
        }


def test_cli_orchestration_plan_json_unknown_fallback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "unknown-wf", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["workflow"] == "unknown-wf"
    assert len(data["steps"]) == 1
    assert data["steps"][0]["assigned_agent"] == "claude-local"


def test_cli_orchestration_plan_fails_on_invalid_policy(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "documentation"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert output.strip()


def test_cli_orchestration_plan_no_file_uses_defaults(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "plan", "--workflow", "release"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "pcae-native" in output
    assert "claude-local" in output


# ---------------------------------------------------------------------------
# CLI: pcae orchestration simulate
# ---------------------------------------------------------------------------


def test_cli_orchestration_simulate_human_documentation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "simulate", "--workflow", "documentation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Suggested workflow simulation: documentation" in output
    assert "Simulation mode: simulation" in output
    assert "Recommendations are advisory; the user may override them." in output
    assert "Recommended agent:" in output
    assert "Ordered steps:" in output
    assert "Final result: planned" in output
    assert "Governance checkpoint: pcae check" in output


def test_cli_orchestration_simulate_human_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "simulate", "--workflow", "implementation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Suggested workflow simulation: implementation" in output
    assert "codex-local -> implementation" in output
    assert "codex-local -> tests" in output


def test_cli_orchestration_simulate_human_release(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "simulate", "--workflow", "release"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Suggested workflow simulation: release" in output
    assert "Governance checkpoint: pcae provenance session current" in output


def test_cli_orchestration_simulate_human_unknown_fallback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "simulate", "--workflow", "unknown-wf"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Suggested workflow simulation: unknown-wf" in output
    assert "claude-local" in output
    assert "Final result: planned" in output


def test_cli_orchestration_simulate_json(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "simulate", "--workflow", "documentation", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert set(data.keys()) == {
        "workflow",
        "status",
        "execution_mode",
        "recommendation_note",
        "steps",
    }
    assert data["workflow"] == "documentation"
    assert data["status"] == "planned"
    assert data["execution_mode"] == "simulation"
    assert data["steps"][2]["governance_checkpoint"] == "pcae check"


def test_cli_orchestration_simulate_fails_on_invalid_policy(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "simulate", "--workflow", "documentation"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert output.strip()


# ---------------------------------------------------------------------------
# CLI: pcae orchestration validate
# ---------------------------------------------------------------------------


def test_cli_orchestration_validate_human_documentation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "validate", "--workflow", "documentation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Orchestration workflow validation: documentation" in output
    assert "Recommendations remain advisory" in output
    assert "Validation result: valid" in output
    assert "Warnings:" in output
    assert "Validated steps:" in output
    assert "Governance checkpoints:" in output


def test_cli_orchestration_validate_human_implementation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "validate", "--workflow", "implementation"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Orchestration workflow validation: implementation" in output
    assert "codex-local" in output
    assert "governance validation" in output


def test_cli_orchestration_validate_human_release(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "validate", "--workflow", "release"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Orchestration workflow validation: release" in output
    assert "pcae provenance session current" in output


def test_cli_orchestration_validate_human_unknown_fallback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "validate", "--workflow", "unknown-wf"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Orchestration workflow validation: unknown-wf" in output
    assert "deterministic default-agent fallback" in output
    assert "Validation result: valid" in output


def test_cli_orchestration_validate_json(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "validate", "--workflow", "documentation", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert set(data.keys()) == {
        "workflow",
        "valid",
        "warnings",
        "validated_steps",
        "governance_checkpoints",
        "fallback_used",
    }
    assert data["workflow"] == "documentation"
    assert data["valid"] is True
    assert data["fallback_used"] is False
    assert data["governance_checkpoints"][0]["checkpoint"] == "pcae check"


def test_cli_orchestration_validate_json_unknown_fallback(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "validate", "--workflow", "unknown-wf", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert data["fallback_used"] is True
    assert data["warnings"]


def test_cli_orchestration_validate_fails_on_invalid_policy(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy(tmp_path, "[protected]\npatterns = []\n")
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "validate", "--workflow", "documentation"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert output.strip()


def test_cli_orchestration_validate_returns_nonzero_on_incoherent_registry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    write_policy(
        tmp_path,
        minimal_policy()
        + '\n[agents.custom]\nkind = "custom"\nroles = ["implementation"]\n',
    )
    monkeypatch.chdir(tmp_path)
    exit_code = main(["orchestration", "validate", "--workflow", "implementation"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Validation result: invalid" in output


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def minimal_policy() -> str:
    return '[protected]\npatterns = [".env"]\n'


def write_policy(root: Path, content: str) -> None:
    policy_file = root / ".pcae" / "policy.toml"
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(content, encoding="utf-8")
