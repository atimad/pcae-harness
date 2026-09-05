"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R
— RHAMP Cross-Test Contamination Diagnosis, Evidence Reconciliation, and
F-5 Readiness Re-Adjudication.

Fresh, additive-only, minimal phase-specific verification. This is a
DIAGNOSTIC/ADJUDICATION phase: it makes no production or existing-test
change, so this suite verifies the durable *evidence and adjudication
artifacts* this phase produced, not any repaired behavior.

Does not modify, skip, or reference-remove any existing test.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
D0 = "e6bd2c718eca485104da8638ed8122035f692ed3"
PHASE_ID = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R"
PREDECESSOR_PHASE_ID = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R"

REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_"
    "RHAMP_CROSS_TEST_CONTAMINATION_DIAGNOSIS_EVIDENCE_RECONCILIATION_AND_F5_"
    "READINESS_RE_ADJUDICATION.md"
)
EVIDENCE_DIR = REPO_ROOT / ".pcae" / "evidence"
EVIDENCE_PREFIX = "149O_1R1R2R1R1R1R1_1R1R1R1R"

EXPECTED_MANIFEST = {
    f"{EVIDENCE_PREFIX}_full_sweep_reproduction_at_head.log": (
        "31fdef417a84240d8ac760cc66658bcff17070dd8292ffd97d28d9039496c144"
    ),
    f"{EVIDENCE_PREFIX}_isolated_results.tsv": (
        "02182885f29d822d55a90acaf684de7d9f0f5b05972703163d9fdb2cd51b529c"
    ),
    f"{EVIDENCE_PREFIX}_failing_files.txt": (
        "6a1acdc594678a05fbfcf8a70f7ee0bb8f4df19bbc7ba502b6a4e691e23cff91"
    ),
    f"{EVIDENCE_PREFIX}_short_summary.txt": (
        "b4774b643a71d741e4ed604f3b4a6e6e0a41f0e604d94f57517458078ea1f949"
    ),
}


def _run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


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
    text = _report_text()
    assert "No discrepancy" in text


# ---------------------------------------------------------------------------
# 2. D0 and evidence-manifest integrity
# ---------------------------------------------------------------------------


def test_report_records_d0():
    assert D0 in _report_text()


@pytest.mark.parametrize("filename,expected_sha", sorted(EXPECTED_MANIFEST.items()))
def test_durable_evidence_copy_hash_matches_recorded_manifest(filename, expected_sha):
    path = EVIDENCE_DIR / filename
    assert path.is_file(), f"missing durable evidence copy: {path}"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == expected_sha
    assert expected_sha in _report_text()


def test_durable_full_sweep_log_final_summary_line_present():
    log_path = EVIDENCE_DIR / f"{EVIDENCE_PREFIX}_full_sweep_reproduction_at_head.log"
    text = log_path.read_text(encoding="utf-8", errors="replace")
    assert "1092 failed, 40538 passed, 24 skipped, 9 warnings, 117 errors in 8831.59s" in text


def test_experiment_log_present_and_records_budget_accounting():
    exp_log = EVIDENCE_DIR / f"{EVIDENCE_PREFIX}_experiment_log.md"
    assert exp_log.is_file()
    text = exp_log.read_text(encoding="utf-8")
    assert "CONTAMINATION ROOT CAUSE: UNRESOLVED" in text
    assert "Budget used" in text


# ---------------------------------------------------------------------------
# 3. Victim-alone baseline and candidate compositions are recorded honestly
# ---------------------------------------------------------------------------


def test_report_records_victim_alone_baseline_clean():
    text = _report_text()
    assert "125 passed in 2.82s" in text


def test_report_records_both_candidate_compositions_falsified():
    text = _report_text()
    assert "Falsified" in text
    assert "2148 passed, 1 skipped in 370.64s" in text


def test_report_records_third_composition_as_infeasible_not_disguised_as_clean():
    text = _report_text()
    assert "infeasible" in text.lower()
    assert "aborted" in text.lower()


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


def test_no_production_scripts_contracts_or_dependency_diff_from_d0():
    diff = _run_git(
        "diff", "--name-only", D0, "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts"
    )
    assert diff == ""


def test_no_existing_test_file_modified_from_d0():
    diff = _run_git("diff", "--name-only", D0, "--", "tests/")
    changed = [line for line in diff.splitlines() if line.strip()]
    this_file = "tests/" + Path(__file__).name
    assert changed == [this_file] or changed == [], changed


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
    assert "Plugin count:            0" in out.replace("  ", " ") or "Plugin count:              0" in out
    assert "Capability count:          0" in out
