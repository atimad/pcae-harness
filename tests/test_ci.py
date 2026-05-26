from __future__ import annotations

import json
from pathlib import Path

from pcae.cli import main


def test_ci_generate_github_dry_run_prints_workflow(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["ci", "generate", "github", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Would write .github/workflows/pcae-governance.yml:" in output
    assert "name: PCAE Governance" in output
    assert "uses: actions/checkout@v4" in output
    assert "uses: actions/setup-python@v5" in output
    assert "python -m pip install -e ." in output
    assert "pcae health --json" in output
    assert "pcae check --json" in output
    assert "pcae analytics risk --json" in output
    assert not workflow_path(tmp_path).exists()


def test_ci_generate_github_writes_workflow_when_missing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["ci", "generate", "github"])

    output = capsys.readouterr().out
    content = workflow_path(tmp_path).read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Created: .github/workflows/pcae-governance.yml" in output
    assert "name: PCAE Governance" in content
    assert "pcae health --json" in content
    assert "pcae check --json" in content
    assert "pcae analytics risk --json" in content


def test_ci_generate_github_does_not_overwrite_existing_without_force(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = workflow_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom workflow\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["ci", "generate", "github"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert (
        ".github/workflows/pcae-governance.yml already exists. Use --force to overwrite."
        in output
    )
    assert target.read_text(encoding="utf-8") == "custom workflow\n"


def test_ci_generate_github_force_overwrites_existing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = workflow_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("custom workflow\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["ci", "generate", "github", "--force"])

    output = capsys.readouterr().out
    content = target.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Overwritten: .github/workflows/pcae-governance.yml" in output
    assert "custom workflow" not in content
    assert "pcae analytics risk --json" in content


def test_ci_status_reports_missing_workflow(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["ci", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PCAE CI status" in output
    assert "Workflow exists: false" in output
    assert "Workflow path: .github/workflows/pcae-governance.yml" in output
    assert "Health step: false" in output
    assert "Check step: false" in output
    assert "Risk step: false" in output
    assert "Overall status: missing" in output


def test_ci_status_reports_incomplete_workflow(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    target = workflow_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "name: partial\njobs:\n  governance:\n    steps:\n"
        "      - run: pcae health --json\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["ci", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Workflow exists: true" in output
    assert "Health step: true" in output
    assert "Check step: false" in output
    assert "Risk step: false" in output
    assert "Overall status: incomplete" in output


def test_ci_status_reports_configured_workflow(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["ci", "generate", "github"]) == 0
    capsys.readouterr()

    exit_code = main(["ci", "status"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Workflow exists: true" in output
    assert "Health step: true" in output
    assert "Check step: true" in output
    assert "Risk step: true" in output
    assert "Overall status: configured" in output


def test_ci_status_json_reports_configured_workflow(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["ci", "generate", "github"]) == 0
    capsys.readouterr()

    exit_code = main(["ci", "status", "--json"])

    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data == {
        "has_check_step": True,
        "has_health_step": True,
        "has_risk_step": True,
        "overall_status": "configured",
        "workflow_exists": True,
        "workflow_path": ".github/workflows/pcae-governance.yml",
    }


def workflow_path(root: Path) -> Path:
    return root / ".github" / "workflows" / "pcae-governance.yml"
