from __future__ import annotations

from pathlib import Path

from pcae.cli import main


def test_docs_commands_dry_run_prints_reference(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "commands", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Would write docs/COMMANDS.md:" in output
    assert "# PCAE Command Reference" in output
    assert "## health" in output
    assert "## ci" in output
    assert "`pcae ci repair --force`" in output
    assert not commands_path(tmp_path).exists()


def test_docs_commands_writes_reference_when_missing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "commands"])

    output = capsys.readouterr().out
    content = commands_path(tmp_path).read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Created: docs/COMMANDS.md" in output
    assert "# PCAE Command Reference" in content
    assert "## task" in content
    assert "## daemon" in content
    assert "## agent" in content


def test_docs_commands_does_not_overwrite_without_force(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = commands_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom docs\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "commands"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "docs/COMMANDS.md already exists. Use --force to overwrite." in output
    assert target.read_text(encoding="utf-8") == "custom docs\n"


def test_docs_commands_force_overwrites_existing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = commands_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom docs\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "commands", "--force"])

    output = capsys.readouterr().out
    content = target.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Overwritten: docs/COMMANDS.md" in output
    assert "custom docs" not in content
    assert "`pcae health --json`" in content


def test_docs_architecture_dry_run_prints_overview(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "architecture", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Would write docs/ARCHITECTURE.md:" in output
    assert "# PCAE Architecture Overview" in output
    assert "## Governance Runtime" in output
    assert "## CI Integration Layer" in output
    assert "health / CI / daemon / pipeline" in output
    assert not architecture_path(tmp_path).exists()


def test_docs_architecture_writes_overview_when_missing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "architecture"])

    output = capsys.readouterr().out
    content = architecture_path(tmp_path).read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Created: docs/ARCHITECTURE.md" in output
    assert "# PCAE Architecture Overview" in content
    assert "## Governance Runtime" in content
    assert "## Orchestration Layer" in content
    assert "## Analytics Layer" in content
    assert "## Fleet Layer" in content
    assert "## Agent Coordination Layer" in content
    assert "## CI Integration Layer" in content
    assert "## Daemon Monitoring Layer" in content
    assert "## Operational Artifact Hygiene" in content
    assert "policy.toml + task contract" in content
    assert "pcae ci generate github" in content


def test_docs_architecture_does_not_overwrite_without_force(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = architecture_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom architecture\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "architecture"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "docs/ARCHITECTURE.md already exists. Use --force to overwrite." in output
    assert target.read_text(encoding="utf-8") == "custom architecture\n"


def test_docs_architecture_force_overwrites_existing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = architecture_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom architecture\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "architecture", "--force"])

    output = capsys.readouterr().out
    content = target.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Overwritten: docs/ARCHITECTURE.md" in output
    assert "custom architecture" not in content
    assert "## Operational Artifact Hygiene" in content


def commands_path(root: Path) -> Path:
    return root / "docs" / "COMMANDS.md"


def architecture_path(root: Path) -> Path:
    return root / "docs" / "ARCHITECTURE.md"
