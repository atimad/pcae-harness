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


def test_docs_glossary_dry_run_prints_glossary(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "glossary", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Would write docs/GLOSSARY.md:" in output
    assert "# PCAE Governance Glossary" in output
    assert "## governance runtime" in output
    assert "## task contract" in output
    assert "## agent lock" in output
    assert "## CI drift" in output
    assert not glossary_path(tmp_path).exists()


def test_docs_glossary_writes_glossary_when_missing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "glossary"])

    output = capsys.readouterr().out
    content = glossary_path(tmp_path).read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Created: docs/GLOSSARY.md" in output
    assert "# PCAE Governance Glossary" in content
    assert "## active task" in content
    assert "## allowed files" in content
    assert "## forbidden files" in content
    assert "## allowed zones" in content
    assert "## forbidden zones" in content
    assert "## architecture zones" in content
    assert "## architecture rules" in content
    assert "## enforcement mode" in content
    assert "## session continuity" in content
    assert "## architecture history" in content
    assert "## governance health" in content
    assert "## governance risk" in content
    assert "## fleet registry" in content
    assert "## fleet drift" in content
    assert "## governance bundle" in content
    assert "## agent lock" in content
    assert "## daemon dry-run" in content
    assert "## pipeline dry-run" in content
    assert "## CI drift" in content
    assert "## CI repair" in content


def test_docs_glossary_does_not_overwrite_without_force(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = glossary_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom glossary\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "glossary"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "docs/GLOSSARY.md already exists. Use --force to overwrite." in output
    assert target.read_text(encoding="utf-8") == "custom glossary\n"


def test_docs_glossary_force_overwrites_existing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = glossary_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom glossary\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "glossary", "--force"])

    output = capsys.readouterr().out
    content = target.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Overwritten: docs/GLOSSARY.md" in output
    assert "custom glossary" not in content
    assert "## governance runtime" in content


def test_docs_commands_dry_run_includes_phase(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["docs", "commands", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## phase" in output
    assert "`pcae phase start --agent-id <id>`" in output
    assert "`pcae phase complete --summary" in output
    assert "`pcae phase handoff" in output


def test_docs_commands_dry_run_includes_status(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["docs", "commands", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## status" in output
    assert "`pcae status coherence`" in output
    assert "`pcae status coherence --json`" in output


def test_docs_commands_dry_run_includes_governance(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["docs", "commands", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## governance" in output
    assert "`pcae governance audit`" in output
    assert "`pcae governance repair --dry-run`" in output


def test_docs_commands_dry_run_includes_runtime_snapshot(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["docs", "commands", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## runtime" in output
    assert "`pcae runtime snapshot --preview`" in output
    assert "`pcae runtime snapshot export`" in output
    assert "`pcae runtime snapshot lineage`" in output
    assert "`pcae runtime snapshot validate-restore <path>`" in output
    assert "`pcae runtime snapshot manifest`" in output
    assert "`pcae runtime snapshot retention --dry-run`" in output


def test_docs_commands_dry_run_includes_orchestration(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["docs", "commands", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## orchestration" in output
    assert "`pcae orchestration policy`" in output
    assert "`pcae orchestration agents`" in output
    assert "`pcae orchestration recommend --work-type <type>`" in output
    assert "`pcae orchestration plan --workflow <name>`" in output
    assert "`pcae orchestration simulate --workflow <name>`" in output
    assert "`pcae orchestration validate --workflow <name>`" in output
    assert "`pcae orchestration readiness --workflow <name>`" in output


def test_docs_commands_dry_run_includes_context(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["docs", "commands", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## context" in output
    assert "`pcae context pack --preview`" in output
    assert "`pcae context pack --preview --json`" in output


def test_docs_commands_dry_run_includes_session_bootstrap(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["docs", "commands", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "`pcae session bootstrap --agent-id <id>`" in output


def test_docs_commands_dry_run_includes_provenance(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["docs", "commands", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "## provenance" in output
    assert "`pcae provenance status`" in output
    assert "`pcae provenance record --event-type <type> --summary" in output


def test_docs_commands_force_writes_updated_content(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = commands_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("old content\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["docs", "commands", "--force"])

    content = target.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "old content" not in content
    assert "## phase" in content
    assert "## governance" in content
    assert "## runtime" in content
    assert "## orchestration" in content
    assert "## context" in content


def commands_path(root: Path) -> Path:
    return root / "docs" / "COMMANDS.md"


def architecture_path(root: Path) -> Path:
    return root / "docs" / "ARCHITECTURE.md"


def glossary_path(root: Path) -> Path:
    return root / "docs" / "GLOSSARY.md"
