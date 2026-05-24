from __future__ import annotations

import json
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.inspect import inspect_harness
from pcae.core.manifest import MANIFEST_ENTRIES
from pcae.core.paths import HarnessPath
from pcae.core.reporting import format_inspection


def test_inspect_reports_all_manifest_paths_present_after_init(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))

    result = inspect_harness(HarnessPath(tmp_path))

    assert all(path.present for path in result.paths)
    assert {path.relative_path for path in result.paths} == {
        entry.relative_path for entry in MANIFEST_ENTRIES
    }


def test_inspect_reports_missing_paths(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "tasks" / "DONE.md").unlink()
    (tmp_path / "scripts" / "check-docs-updated.ps1").unlink()

    result = inspect_harness(HarnessPath(tmp_path))
    missing = {path.relative_path for path in result.missing_paths}

    assert Path("tasks/DONE.md") in missing
    assert Path("scripts/check-docs-updated.ps1") in missing
    assert Path("tasks/TODO.md") not in missing


def test_inspection_report_includes_required_categories(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    (tmp_path / ".githooks" / "pre-commit").unlink()

    report = format_inspection(inspect_harness(HarnessPath(tmp_path)))

    assert "[present] tasks/TODO.md" in report
    assert "[present] tasks/DONE.md" in report
    assert "[present] tasks/DECISIONS.md" in report
    assert "[missing] .githooks/pre-commit" in report
    assert "[present] scripts/check-docs-updated.sh" in report
    assert "[present] scripts/check-docs-updated.ps1" in report


def test_inspection_report_includes_repo_policy_status(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))

    report = format_inspection(inspect_harness(HarnessPath(tmp_path)))

    assert "Policy:" in report
    assert "[present] .pcae/policy.toml" in report
    assert "source: repo config" in report
    assert "validation: valid" in report
    assert "protected patterns: 18" in report
    assert "architecture zones:" in report
    assert "core: 1 patterns" in report
    assert "cli: 3 patterns" in report
    assert "docs: 2 patterns" in report
    assert "scripts: 1 patterns" in report
    assert "hooks: 1 patterns" in report
    assert "package: 1 patterns" in report
    assert "session: 1 patterns" in report
    assert "policy: 1 patterns" in report
    assert "architecture rules: 12" in report


def test_inspection_report_includes_default_policy_status_when_missing(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    (tmp_path / ".pcae" / "policy.toml").unlink()

    report = format_inspection(inspect_harness(HarnessPath(tmp_path)))

    assert "Policy:" in report
    assert "[missing] .pcae/policy.toml" in report
    assert "source: built-in defaults" in report
    assert "validation: valid" in report
    assert "protected patterns: 18" in report
    assert "architecture zones:\n    none" in report
    assert "architecture rules: 0" in report


def test_inspection_report_includes_invalid_policy_reason(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    (tmp_path / ".pcae" / "policy.toml").write_text(
        "[protected\npatterns = []\n",
        encoding="utf-8",
    )

    report = format_inspection(inspect_harness(HarnessPath(tmp_path)))

    assert "[present] .pcae/policy.toml" in report
    assert "validation: invalid" in report
    assert "error: Invalid TOML: malformed table header." in report


def test_inspection_report_includes_invalid_architecture_zone_reason(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    (tmp_path / ".pcae" / "policy.toml").write_text(
        """[protected]
patterns = [".env"]

[architecture.zones]
core = ""
""",
        encoding="utf-8",
    )

    report = format_inspection(inspect_harness(HarnessPath(tmp_path)))

    assert "validation: invalid" in report
    assert "error: Invalid policy: architecture zone 'core' patterns must be a list." in report


def test_inspection_report_includes_invalid_architecture_rule_reason(
    tmp_path: Path,
) -> None:
    init_harness(HarnessPath(tmp_path))
    (tmp_path / ".pcae" / "policy.toml").write_text(
        """[protected]
patterns = [".env"]

[architecture.zones]
core = ["src/pcae/core/**"]

[architecture.rules]
core = ["commands"]
""",
        encoding="utf-8",
    )

    report = format_inspection(inspect_harness(HarnessPath(tmp_path)))

    assert "validation: invalid" in report
    assert (
        "error: Invalid policy: architecture rule 'core' references "
        "unknown target zone 'commands'."
    ) in report


def test_inspect_command_runs_from_current_directory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["inspect"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert f"PCAE inspection for {tmp_path}" in output
    assert "Policy:" in output
    assert "All required PCAE paths are present." in output


def test_inspect_json_command_reports_machine_readable_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["inspect", "--json"])

    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["root"] == str(tmp_path)
    assert data["overall_status"] == "ok"
    assert data["required_files"]["missing"] == []
    assert "AGENTS.md" in data["required_files"]["present"]
    assert data["task_files"]["missing"] == []
    assert "tasks/TODO.md" in data["task_files"]["present"]
    assert data["hooks"]["missing"] == []
    assert ".githooks/pre-commit" in data["hooks"]["present"]
    assert data["check_scripts"]["missing"] == []
    assert "scripts/check-docs-updated.sh" in data["check_scripts"]["present"]
    assert "scripts/check-docs-updated.ps1" in data["check_scripts"]["present"]
    assert data["policy"]["present"] is True
    assert data["policy"]["source"] == "repo config"
    assert data["policy"]["valid"] is True
    assert data["policy"]["protected_pattern_count"] == 18
    assert data["architecture"]["zones"]["core"] == 1
    assert data["architecture"]["rules_count"] == 12


def test_inspect_json_reports_missing_paths_and_attention_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    (tmp_path / "tasks" / "DONE.md").unlink()
    (tmp_path / ".githooks" / "pre-commit").unlink()
    monkeypatch.chdir(tmp_path)

    exit_code = main(["inspect", "--json"])

    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["overall_status"] == "attention_required"
    assert data["task_files"]["missing"] == ["tasks/DONE.md"]
    assert data["hooks"]["missing"] == [".githooks/pre-commit"]


def test_inspect_json_reports_invalid_policy_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    (tmp_path / ".pcae" / "policy.toml").write_text(
        "[protected\npatterns = []\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["inspect", "--json"])

    output = capsys.readouterr().out
    data = json.loads(output)
    assert exit_code == 0
    assert data["overall_status"] == "attention_required"
    assert data["policy"]["present"] is True
    assert data["policy"]["valid"] is False
    assert data["policy"]["error"] == "Invalid TOML: malformed table header."


def test_inspect_does_not_modify_files(tmp_path: Path) -> None:
    init_harness(HarnessPath(tmp_path))
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    inspect_harness(HarnessPath(tmp_path))

    after = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before
