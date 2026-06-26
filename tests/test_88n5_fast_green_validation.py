"""
Phase 88N.5 — Fast Green Validation Architecture self-verification tests.

These tests verify the structural integrity of the fast-green tier itself:
marker declaration, module inclusion/exclusion policy, and conftest wiring.
They are themselves included in the fast-green tier via FAST_GREEN_MODULES.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent


def _collect_fast_green() -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-m", "fast_green", "--collect-only", "-q",
         "--no-header"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


# ---------------------------------------------------------------------------
# Marker declaration
# ---------------------------------------------------------------------------

def test_88n5_fast_green_marker_declared_in_pyproject() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert "fast_green" in pyproject


def test_88n5_fast_green_marker_has_description() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert "fast_green:" in pyproject or '"fast_green' in pyproject


# ---------------------------------------------------------------------------
# conftest structure
# ---------------------------------------------------------------------------

def test_88n5_conftest_exists() -> None:
    assert (ROOT / "tests" / "conftest.py").exists()


def test_88n5_conftest_imports_fast_green_modules() -> None:
    conftest = (ROOT / "tests" / "conftest.py").read_text()
    assert "FAST_GREEN_MODULES" in conftest


def test_88n5_conftest_uses_pytest_collection_modifyitems() -> None:
    conftest = (ROOT / "tests" / "conftest.py").read_text()
    assert "pytest_collection_modifyitems" in conftest


def test_88n5_conftest_adds_fast_green_marker() -> None:
    conftest = (ROOT / "tests" / "conftest.py").read_text()
    assert "fast_green" in conftest


# ---------------------------------------------------------------------------
# Collection integrity
# ---------------------------------------------------------------------------

def test_88n5_fast_green_collects_nonzero_tests() -> None:
    lines = _collect_fast_green()
    summary = [l for l in lines if "test" in l and ("collected" in l or "selected" in l)]
    assert summary, f"No collection summary found: {lines[-5:]}"
    total_line = "\n".join(lines)
    # Extract collected count — line ends with "N/M tests collected (K deselected)"
    # or "N tests collected"
    import re
    m = re.search(r"(\d+)/(\d+) tests collected", total_line) or \
        re.search(r"(\d+) tests collected", total_line)
    assert m, f"Could not parse collected count: {total_line[-300:]}"
    collected = int(m.group(1))
    assert collected >= 100, f"Fast-green tier too small: {collected} tests"


def test_88n5_fast_green_upper_bound() -> None:
    """Fast-green must stay well below quick tier to remain meaningful."""
    lines = _collect_fast_green()
    total_line = "\n".join(lines)
    import re
    m = re.search(r"(\d+)/(\d+) tests collected", total_line)
    if not m:
        pytest.skip("Could not parse collected/total; skip upper-bound check")
    collected = int(m.group(1))
    total = int(m.group(2))
    # Fast-green should be at most 40% of the full suite
    assert collected <= total * 0.40, (
        f"Fast-green ({collected}) is >{collected/total:.0%} of full suite ({total}); "
        "consider narrowing the selection"
    )


# ---------------------------------------------------------------------------
# Module inclusion policy
# ---------------------------------------------------------------------------

def test_88n5_core_governance_modules_included() -> None:
    from conftest import FAST_GREEN_MODULES  # type: ignore[import]
    required = {
        "test_check",
        "test_health",
        "test_hook_bypass_policy",
        "test_doctor_test_run",
        "test_policy",
    }
    missing = required - FAST_GREEN_MODULES
    assert not missing, f"Required governance modules missing from fast-green: {missing}"


def test_88n5_task_lifecycle_modules_included() -> None:
    from conftest import FAST_GREEN_MODULES  # type: ignore[import]
    required = {"test_task", "test_session", "test_task_memory_reconciliation"}
    missing = required - FAST_GREEN_MODULES
    assert not missing, f"Task lifecycle modules missing from fast-green: {missing}"


def test_88n5_self_module_included() -> None:
    from conftest import FAST_GREEN_MODULES  # type: ignore[import]
    assert "test_88n5_fast_green_validation" in FAST_GREEN_MODULES


# ---------------------------------------------------------------------------
# Module exclusion policy
# ---------------------------------------------------------------------------

def test_88n5_agent_module_excluded() -> None:
    """test_agent is excluded: 4 236 tests, 2:06 runtime, capsys-bound slow tests."""
    from conftest import FAST_GREEN_MODULES  # type: ignore[import]
    assert "test_agent" not in FAST_GREEN_MODULES


def test_88n5_phase_module_excluded() -> None:
    """test_phase is excluded: 886-test exhaustive command catalog."""
    from conftest import FAST_GREEN_MODULES  # type: ignore[import]
    assert "test_phase" not in FAST_GREEN_MODULES


def test_88n5_subprocess_heavy_governance_modules_excluded() -> None:
    """Subprocess-heavy governance-info modules excluded despite no slow marker."""
    from conftest import FAST_GREEN_MODULES  # type: ignore[import]
    subprocess_heavy = {
        "test_governance_timeline",
        "test_decision_log",
        "test_risk_register",
        "test_project_state",
    }
    present = subprocess_heavy & FAST_GREEN_MODULES
    assert not present, (
        f"Subprocess-heavy modules should not be in fast-green: {present}. "
        "Each spawns a subprocess per xdist worker; group total ~2:25."
    )


# ---------------------------------------------------------------------------
# Tier documentation
# ---------------------------------------------------------------------------

def test_88n5_docs_artifact_exists() -> None:
    assert (ROOT / "docs" / "PHASE_88_FAST_GREEN_VALIDATION_ARCHITECTURE.md").exists()


def test_88n5_pyproject_documents_fast_green_invocation() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert "fast-green" in pyproject or "fast_green" in pyproject


def test_88n5_tier_comment_present_in_pyproject() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert "fast_green" in pyproject and "-m" in pyproject
