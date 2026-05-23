from __future__ import annotations

from pathlib import Path

from pcae.core.architecture import analyze_changed_python_dependencies
from pcae.core.git_status import GitChange
from pcae.core.paths import HarnessPath


ZONES = {
    "core": ("src/pcae/core/**",),
    "commands": ("src/pcae/commands/**",),
    "tests": ("tests/**",),
}


def test_architecture_analysis_allows_configured_dependency(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "core" / "check.py", "import json\n")
    write_file(tmp_path / "src" / "pcae" / "core" / "tasks.py", "VALUE = 1\n")
    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.core.tasks\n",
    )

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {"core": ("core",)},
    )

    assert result.dependency_warnings == ()
    assert result.parse_warnings == ()


def test_architecture_analysis_reports_forbidden_dependency(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {"core": ("core",), "commands": ("core", "commands")},
    )

    assert len(result.dependency_warnings) == 1
    assert result.dependency_warnings[0].text == (
        "src/pcae/core/changed.py: core -> commands is not allowed by policy"
    )
    assert result.parse_warnings == ()


def test_architecture_analysis_ignores_external_imports(tmp_path: Path) -> None:
    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import argparse\nfrom pathlib import Path\n",
    )

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {"core": ("core",)},
    )

    assert result.dependency_warnings == ()
    assert result.parse_warnings == ()


def test_architecture_analysis_warns_on_parse_error(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "core" / "changed.py", "def broken(:\n")

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {"core": ("core",)},
    )

    assert result.dependency_warnings == ()
    assert len(result.parse_warnings) == 1
    assert result.parse_warnings[0].path == Path("src/pcae/core/changed.py")
    assert "Could not parse Python imports:" in result.parse_warnings[0].text


def test_architecture_analysis_skips_when_rules_are_missing(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_file(
        tmp_path / "src" / "pcae" / "core" / "changed.py",
        "import pcae.commands.task\n",
    )

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("src/pcae/core/changed.py"), " M"),),
        ZONES,
        {},
    )

    assert result.dependency_warnings == ()
    assert result.parse_warnings == ()


def test_architecture_analysis_skips_unclassified_source(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pcae" / "commands" / "task.py", "VALUE = 1\n")
    write_file(tmp_path / "scratch.py", "import pcae.commands.task\n")

    result = analyze_changed_python_dependencies(
        HarnessPath(tmp_path),
        (GitChange(Path("scratch.py"), " M"),),
        ZONES,
        {"core": ("core",), "commands": ("core", "commands")},
    )

    assert result.dependency_warnings == ()
    assert result.parse_warnings == ()


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
