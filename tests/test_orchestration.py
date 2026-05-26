from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.core.orchestration import build_orchestration_data, load_orchestration_policy
from pcae.core.paths import HarnessPath
from pcae.core.policy import (
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
# helpers
# ---------------------------------------------------------------------------


def minimal_policy() -> str:
    return '[protected]\npatterns = [".env"]\n'


def write_policy(root: Path, content: str) -> None:
    policy_file = root / ".pcae" / "policy.toml"
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(content, encoding="utf-8")
