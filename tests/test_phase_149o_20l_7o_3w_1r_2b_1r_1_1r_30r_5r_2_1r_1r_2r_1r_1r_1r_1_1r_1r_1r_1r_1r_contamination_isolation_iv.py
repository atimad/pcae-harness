"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R
— Further-Bounded RHAMP Cross-Test Contamination Trigger Isolation,
Production-Reachability Determination, and F-5 Hold Re-Adjudication.

Fresh, additive-only, minimal phase-specific verification. This is a
DIAGNOSTIC/ADJUDICATION phase: it makes no production or existing-test
change, so this suite verifies the durable *evidence and adjudication
artifacts* this phase produced, not any repaired behavior.

Does not modify, skip, or reference-remove any existing test.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
B0 = "346a409853b2ac7f6ac9efa90c77d03068f64705"
PHASE_ID = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R"
PREDECESSOR_PHASE_ID = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R"

REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_"
    "CONTAMINATION_TRIGGER_ISOLATION_AND_F5_READADJUDICATION.md"
)
EVIDENCE_DIR = REPO_ROOT / ".pcae" / "evidence"
EXPERIMENT_LOG = EVIDENCE_DIR / "149O_1R1R1R1R1R_experiment_log.md"


def _run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def _experiment_log_text() -> str:
    return EXPERIMENT_LOG.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Phase lineage / CPIPC
# ---------------------------------------------------------------------------


def test_phase_id_is_cpipc_valid_successor_of_predecessor():
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from pcae.core import phase_id as pid

    pred = pid.parse(PREDECESSOR_PHASE_ID)
    succ = pid.parse(PHASE_ID)
    assert pid.same_series(pred, succ)
    assert pid.same_branch(pred, succ)
    assert pid.compare(pred, succ) == "less"


def test_report_declares_no_cpipc_discrepancy():
    normalized = " ".join(_report_text().split())
    assert "No discrepancy" in normalized


# ---------------------------------------------------------------------------
# 2. B0 and durable evidence presence
# ---------------------------------------------------------------------------


def test_report_records_b0():
    assert B0 in _report_text()


def test_experiment_log_present_and_records_budget_accounting():
    assert EXPERIMENT_LOG.is_file()
    text = _experiment_log_text()
    assert "CONTAMINATION ROOT CAUSE: UNRESOLVED" in text or "UNRESOLVED" in text
    assert "Budget consumed" in text or "Budget accounting" in text


# ---------------------------------------------------------------------------
# 3. New findings this phase are honestly recorded
# ---------------------------------------------------------------------------


def test_experiment_log_records_collection_time_invocation_and_conclusion():
    text = _experiment_log_text()
    assert "41791 tests collected in 5.10s" in text
    assert "CONTAMINATION STAGE IS NOT COLLECTION/IMPORT" in text


def test_experiment_log_records_multiprocessing_cluster_falsified():
    text = _experiment_log_text()
    assert "15 failed, 1348 passed in 88.19s" in text
    assert "FALSIFIED" in text


def test_experiment_log_records_reload_sys_modules_mechanism_ruled_out():
    text = _experiment_log_text()
    assert "Zero" in text and "importlib.reload(" in text
    assert "canonical" in text.lower() and "sys.modules" in text


def test_report_records_stage_verdict():
    text = _report_text()
    assert "CONTAMINATION STAGE: TEST-EXECUTION" in text


# ---------------------------------------------------------------------------
# 4. Required closed-vocabulary verdicts
# ---------------------------------------------------------------------------


def test_report_contains_exactly_the_required_verdict_vocabulary():
    text = _report_text()
    assert "CONTAMINATION ROOT CAUSE: UNRESOLVED." in text
    assert "CONTAMINATION LOCATION: NOT ESTABLISHED." in text
    assert "CURRENT F-5 READINESS: NOT YET ESTABLISHED." in text
    assert "F-5 EXECUTION HOLD: REMAINS." in text


def test_report_does_not_claim_hold_cleared():
    text = _report_text()
    assert "F-5 EXECUTION HOLD: CLEARED" not in text


def test_report_preserves_n16_5_not_closed_and_n16_6_7_untouched():
    text = _report_text()
    assert "N-16-5: NOT CLOSED." in text
    assert "N-16-6/N-16-7 remain open/untouched" in text


def test_report_preserves_delegated_finalization_incident_language():
    assert "DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED" in _report_text()


# ---------------------------------------------------------------------------
# 5. No production / existing-test / contract / dependency modification
# ---------------------------------------------------------------------------


def test_no_production_scripts_contracts_or_dependency_diff_from_b0():
    diff = _run_git(
        "diff", "--name-only", B0, "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts"
    )
    assert diff == ""


def test_no_existing_test_file_modified_from_b0():
    diff = _run_git("diff", "--name-only", B0, "--", "tests/")
    changed = [line for line in diff.splitlines() if line.strip()]
    this_file = "tests/" + Path(__file__).name
    assert set(changed) <= {this_file}, changed


# ---------------------------------------------------------------------------
# 6. No host mutation, no F-5 action, runtime unchanged
# ---------------------------------------------------------------------------


def test_report_declares_no_host_mutation_and_no_f5_action():
    normalized = " ".join(_report_text().split())
    assert "No `scripts/hpac_protected_root_admin.py provision`" in normalized
    assert "scripts/hpac_protected_presentation_admin.py install`" in normalized


def test_runtime_inspect_reports_unchanged_non_executing_baseline():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "runtime", "inspect"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    out = result.stdout
    assert "not_implemented" in out
    assert "Observed" in out
    assert "unavailable" in out
    assert "0" in out
