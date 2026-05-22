from __future__ import annotations

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


def test_inspect_command_runs_from_current_directory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["inspect"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert f"PCAE inspection for {tmp_path}" in output
    assert "All required PCAE paths are present." in output


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
