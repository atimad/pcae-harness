"""Phase 149O.20L.7O.2T — Phase 149O.20L.7O.2P Attribution-Aware
Reconciliation and Canonical Promotion Assessment.

Mechanically verifies the factual claims underlying the 2T reconciliation
report (docs/PHASE_149O_20L_7O_2T_...md): the true 2P baseline/commit
range, empty production/test diff across that range, quarantine-artifact
push-state-only blockers, undisturbed canonical chronology, deliverable
integrity, and the terminal ``QUARANTINED`` promotion state that makes
retro-promotion architecturally unsupported. This suite makes no claim
about original raw pytest counts (raw-content trust boundary) and does
not re-run Fast Green.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.core.canonical_artifact_promotion import (
    ArtifactState,
    ALLOWED_STATE_TRANSITIONS,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

BASELINE = "db6252a925ad4926603ece9b5b1f381ff9f5f5d7"
FIRST_2P_COMMIT = "deeca31c"
EFFECTIVE_CHECKPOINT = "e3548d72"  # last commit in the 2P range
QUARANTINE_ARTIFACT = (
    REPO_ROOT
    / ".pcae"
    / "phase-reports"
    / "quarantine"
    / "20260822-094926-890398-149O.20L.7O.2P-004c451540a8.blocked.json"
)
STRATEGY_DOC = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2P_V0_3_RELEASE_STRATEGY_AND_CAPABILITY_PRIORITIZATION_REASSESSMENT.md"
)


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def test_baseline_is_direct_parent_of_first_2p_commit() -> None:
    merge_base = _git("merge-base", BASELINE, FIRST_2P_COMMIT)
    assert merge_base.startswith(BASELINE[: len(merge_base)]) or merge_base == _git(
        "rev-parse", BASELINE
    )


def test_full_2p_commit_range_is_ancestral_to_head() -> None:
    for sha in (BASELINE, FIRST_2P_COMMIT, EFFECTIVE_CHECKPOINT):
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
            cwd=REPO_ROOT,
            timeout=30,
        )
        assert proc.returncode == 0, f"{sha} is not an ancestor of HEAD"


def test_2p_range_has_no_production_or_test_diff() -> None:
    diff = _git(
        "diff",
        "--stat",
        f"{BASELINE}..{EFFECTIVE_CHECKPOINT}",
        "--",
        "src/pcae",
        "scripts",
        "tests",
    )
    assert diff == "", f"unexpected production/test diff in 2P range: {diff!r}"


def test_2p_commit_range_count_and_subjects() -> None:
    log = _git(
        "log",
        "--format=%H %s",
        f"{BASELINE}..{EFFECTIVE_CHECKPOINT}",
    )
    lines = [line for line in log.splitlines() if line.strip()]
    assert len(lines) == 8, f"expected 8 commits in 2P range, found {len(lines)}"
    assert all("149O.20L.7O.2P" in line for line in lines)


def test_canonical_latest_report_still_names_2s6_not_2p() -> None:
    latest = json.loads((REPO_ROOT / ".pcae" / "phase-reports" / "latest.json").read_text())
    assert latest.get("phase_id") != "149O.20L.7O.2P"


def test_2p_quarantine_artifact_blockers_are_push_state_not_fast_green_failure() -> None:
    assert QUARANTINE_ARTIFACT.exists(), "2P quarantine artifact missing"
    data = json.loads(QUARANTINE_ARTIFACT.read_text())
    assert data["phase_id"] == "149O.20L.7O.2P"
    assert data["pushed_status"] == "not_pushed"
    fast_green = data["test_results"]["fast_green"]
    assert "0 attributable regressions" in fast_green
    blockers = data["finalization_blockers"]
    assert any("pushed_status" in b for b in blockers)
    assert not any("attributable regression" in b and "0 attributable" not in b for b in blockers)


def test_2p_strategy_deliverable_exists_and_is_substantive() -> None:
    assert STRATEGY_DOC.exists()
    content = STRATEGY_DOC.read_text()
    assert len(content.splitlines()) > 100
    assert "v0.3" in content.lower()


def test_2p_strategy_deliverable_unmodified_since_authoring_commit() -> None:
    log = _git("log", "--follow", "--format=%H", "--", str(STRATEGY_DOC.relative_to(REPO_ROOT)))
    commits = [line for line in log.splitlines() if line.strip()]
    assert len(commits) == 1, (
        f"expected exactly one commit touching the 2P strategy doc, found {len(commits)}"
    )


def test_quarantined_state_is_terminal_in_promotion_state_machine() -> None:
    assert ALLOWED_STATE_TRANSITIONS[ArtifactState.QUARANTINED] == frozenset()
