from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.core.orchestration import (
    build_agent_registry_data,
    build_orchestration_data,
    load_agent_registry,
    load_orchestration_policy,
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
# helpers
# ---------------------------------------------------------------------------


def minimal_policy() -> str:
    return '[protected]\npatterns = [".env"]\n'


def write_policy(root: Path, content: str) -> None:
    policy_file = root / ".pcae" / "policy.toml"
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(content, encoding="utf-8")
