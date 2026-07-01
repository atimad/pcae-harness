"""Tests for Phase 106D — Packaging / Installation / Clean-Smoke Test.

Documentation/metadata-focused. Real install/build testing (editable,
non-editable, python -m build) was performed manually in temporary
environments during this phase and recorded in
docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md; it is not
re-run here as a slow subprocess test, per the phase's own guidance to
keep install validation documented rather than a slow CI-only test.
Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
PACKAGING_DOC = ROOT / "docs" / "PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md"
CLEAN_SMOKE_DOC = ROOT / "docs" / "V0_1_CLEAN_SMOKE_TEST.md"
GOLDEN_WORKFLOW_DOC = ROOT / "docs" / "V0_1_GOLDEN_WORKFLOW.md"
RELEASE_SCOPE_DOC = ROOT / "docs" / "RELEASE_SCOPE_V0_1.md"


# Plain text checks against pyproject.toml, not a TOML parser: `tomllib`
# requires Python 3.11+, but this project (and this test file) targets the
# project's own `requires-python = ">=3.9"`.


@pytest.fixture(scope="module")
def pyproject_text() -> str:
    return PYPROJECT.read_text()


@pytest.fixture(scope="module")
def packaging_text() -> str:
    return PACKAGING_DOC.read_text()


def test_pyproject_toml_exists():
    assert PYPROJECT.is_file()


def test_project_defines_console_script_for_pcae(pyproject_text):
    assert '[project.scripts]' in pyproject_text
    assert 'pcae = "pcae.cli:main"' in pyproject_text


def test_package_source_directory_exists():
    assert (ROOT / "src" / "pcae").is_dir()
    assert (ROOT / "src" / "pcae" / "cli.py").is_file()


def test_sdist_scope_is_explicit(pyproject_text):
    # Phase 106D fix: without this, hatchling's default sdist swept in the
    # entire repository checkout (44,399 files, including local .claude/
    # settings and .pcae/ runtime state).
    assert "[tool.hatch.build.targets.sdist]" in pyproject_text
    sdist_section = pyproject_text.split("[tool.hatch.build.targets.sdist]")[1]
    assert "src/pcae" in sdist_section
    assert ".pcae" not in sdist_section.split("\n\n")[0]
    assert ".claude" not in sdist_section.split("\n\n")[0]


def test_wheel_scope_unchanged(pyproject_text):
    assert "[tool.hatch.build.targets.wheel]" in pyproject_text
    wheel_section = pyproject_text.split("[tool.hatch.build.targets.wheel]")[1].split("\n\n")[0]
    assert 'packages = ["src/pcae"]' in wheel_section


def test_release_scope_doc_references_packaging_status():
    text = RELEASE_SCOPE_DOC.read_text()
    assert "106D" in text


def test_golden_workflow_doc_exists():
    assert GOLDEN_WORKFLOW_DOC.is_file()


def test_packaging_smoke_doc_exists():
    assert PACKAGING_DOC.is_file()


def test_packaging_smoke_doc_includes_editable_install(packaging_text):
    assert "Editable Install Result" in packaging_text
    assert "pip install -e" in packaging_text


def test_packaging_smoke_doc_includes_non_editable_install(packaging_text):
    assert "Non-Editable Local Install Result" in packaging_text


def test_packaging_smoke_doc_includes_pcae_help(packaging_text):
    assert "pcae --help" in packaging_text


def test_packaging_smoke_doc_includes_phase_report_trust(packaging_text):
    assert "phase-report trust" in packaging_text


def test_packaging_smoke_doc_includes_phase_report_show_trust(packaging_text):
    assert "phase-report show" in packaging_text
    assert "--trust" in packaging_text


def test_packaging_smoke_doc_states_telegram_optional(packaging_text):
    assert "Telegram" in packaging_text
    assert "optional" in packaging_text.lower() or "safely skippable" in packaging_text.lower()


def test_packaging_smoke_doc_states_no_autonomous_execution(packaging_text):
    assert "autonomous execution" in packaging_text.lower() or "runtime enforcement" in packaging_text.lower()


def test_packaging_smoke_doc_references_fast_green_baseline(packaging_text):
    assert "4390/4390" in packaging_text


def test_clean_smoke_test_doc_exists():
    assert CLEAN_SMOKE_DOC.is_file()


def test_clean_smoke_test_doc_includes_venv_creation():
    text = CLEAN_SMOKE_DOC.read_text()
    assert "python -m venv" in text


def test_clean_smoke_test_doc_includes_pcae_help():
    text = CLEAN_SMOKE_DOC.read_text()
    assert "pcae --help" in text or '"$tmpdir/venv/bin/pcae" --help' in text


def test_installation_doc_mentions_v0_1_and_telegram_optional():
    install_doc = (ROOT / "docs" / "INSTALLATION.md").read_text()
    assert "v0.1" in install_doc
    assert "optional" in install_doc.lower()
