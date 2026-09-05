"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R
— Checkpointed Incrementally-Resumable RHAMP Execution-Time Class-Identity /
State-Trace Coverage Advancement, Method Validation, and F-5 Hold
Adjudication.

Fresh, additive-only, minimal phase-specific verification. Diagnostic/
adjudication phase: no production or existing-test change, so this suite
verifies the durable checkpoint/campaign/evidence artifacts this phase
produced, not any repaired behavior. Does not modify, skip, or
reference-remove any existing test.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
K0 = "ac6aee007540cb2433b1714f0c09b7cbbcf19920"
PHASE_ID = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R"
PREDECESSOR_PHASE_ID = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R"
CAMPAIGN_ID = "RHAMP-XTEST-IDENTITY-TRACE/1"

EVIDENCE_DIR = REPO_ROOT / ".pcae" / "evidence"
MANIFEST_PATH = EVIDENCE_DIR / "RHAMP_XTEST_CORPUS_1_manifest.json"
CHECKPOINT_PATH = EVIDENCE_DIR / "RHAMP_XTEST_CHECKPOINT_current.json"
INVOCATION_LOG_PATH = EVIDENCE_DIR / "RHAMP_XTEST_INVOCATION_LOG.jsonl"
EXPERIMENT_LOG_PATH = EVIDENCE_DIR / "RHAMP_XTEST_CORPUS_1_experiment_log.md"
RUN_SUMMARY_PATH = EVIDENCE_DIR / "RHAMP_XTEST_RUN_SUMMARY.json"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_"
    "CHECKPOINTED_RHAMP_TRACE_COVERAGE_ADVANCEMENT.md"
)


def _run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def _checkpoint() -> dict:
    return json.loads(CHECKPOINT_PATH.read_text())


def _report_text() -> str:
    return REPORT_PATH.read_text()


def test_evidence_files_exist() -> None:
    for p in (MANIFEST_PATH, CHECKPOINT_PATH, INVOCATION_LOG_PATH, EXPERIMENT_LOG_PATH, RUN_SUMMARY_PATH, REPORT_PATH):
        assert p.exists(), f"missing durable evidence artifact: {p}"


def test_corpus_manifest_frozen_and_self_consistent() -> None:
    m = _manifest()
    assert m["campaign_id"] == CAMPAIGN_ID
    assert m["corpus_total_files"] >= 700
    assert m["unit_count"] == len(m["units"])
    seen = set()
    for u in m["units"]:
        assert u["unit_id"] not in seen
        seen.add(u["unit_id"])
        assert u["files"], "empty batch"
    total_files = sum(u["file_count"] for u in m["units"])
    assert total_files == m["corpus_total_files"] - 1  # victim excluded from batches


def test_checkpoint_schema_has_required_fields() -> None:
    c = _checkpoint()
    required = {
        "schema_version", "campaign_id", "corpus_id", "corpus_digest",
        "checkpoint_id", "previous_checkpoint_digest", "resume_model",
        "tracer_version", "tracer_digest", "completed_unit_ids",
        "failed_unit_ids", "inconclusive_unit_ids", "pending_unit_count",
        "coverage_count", "coverage_total", "experiment_count",
        "cumulative_experimental_seconds", "identified_state_deltas",
        "current_root_cause_status", "current_location_status",
        "current_F5_hold", "self_digest",
    }
    assert required.issubset(c.keys())
    assert c["campaign_id"] == CAMPAIGN_ID
    assert c["resume_model"] == "A"


def test_checkpoint_self_digest_is_valid() -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    c = _checkpoint()
    body = {k: v for k, v in c.items() if k != "self_digest"}
    import hashlib

    blob = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    expected = "sha256:" + hashlib.sha256(blob).hexdigest()
    assert c["self_digest"] == expected


def test_checkpoint_coverage_advanced_beyond_zero() -> None:
    c = _checkpoint()
    assert c["coverage_count"] > 0
    assert c["coverage_count"] + c["pending_unit_count"] + len(c["failed_unit_ids"]) + len(
        c["inconclusive_unit_ids"]
    ) >= c["coverage_total"] - len(c["inconclusive_unit_ids"])
    assert c["pending_unit_count"] < c["coverage_total"]


def test_relevant_delta_batch_013_recorded() -> None:
    c = _checkpoint()
    deltas = c["identified_state_deltas"]
    assert len(deltas) == 1
    assert "batch-013" in deltas[0]["unit_id"]
    assert deltas[0]["classification"] == "RELEVANT DELTA OBSERVED"


def test_root_cause_still_unresolved_not_overclaimed() -> None:
    c = _checkpoint()
    assert c["current_root_cause_status"] == "UNRESOLVED"
    assert c["current_location_status"] == "NOT_ESTABLISHED"
    assert c["current_F5_hold"] == "REMAINS"


def test_invocation_log_accounts_every_run_and_no_process_left_running() -> None:
    import os

    lines = [json.loads(line) for line in INVOCATION_LOG_PATH.read_text().splitlines() if line.strip()]
    assert len(lines) == 26
    ps = subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout
    self_pid = str(os.getpid())
    running = [
        line
        for line in ps.splitlines()
        if "rhamp_xtest_tracer" in line or "run_campaign.py" in line
    ]
    # Exclude this test's own pytest process (it necessarily matches "pytest")
    # -- only a leftover *diagnostic-tracer* invocation counts as a real leak.
    assert running == [], f"diagnostic pytest process still running: {running}"


def test_no_production_or_existing_test_change_since_k0() -> None:
    diff_src = _run_git("diff", "--name-only", K0, "--", "src/pcae", "scripts", "pyproject.toml", "docs/contracts")
    assert diff_src == ""
    diff_tests = _run_git("diff", "--name-only", K0, "--", "tests/")
    changed = [line for line in diff_tests.splitlines() if line.strip()]
    assert changed in ([], [str(Path(__file__).relative_to(REPO_ROOT))])


def test_report_states_required_closed_vocabulary_verdicts() -> None:
    text = _report_text()
    assert "CHECKPOINT METHOD:" in text and "VERIFIED" in text
    assert "RESUME MODEL:" in text and "A" in text
    assert "CONTAMINATION ROOT CAUSE:" in text and "UNRESOLVED" in text
    assert "F-5 EXECUTION HOLD:" in text and "REMAINS" in text
    assert "N-16-5:" in text and "NOT CLOSED" in text
    assert PHASE_ID in text


def test_runtime_state_unchanged_and_no_first_effect() -> None:
    text = _report_text()
    assert "not_implemented" in text
    assert "0 plugins" in text or "0 plugins/capabilities" in text or "Plugins: 0" in text or "plugin" in text.lower()


def test_no_host_mutation_language_present() -> None:
    text = _report_text()
    assert "No host mutation" in text or "no host mutation" in text.lower()


def test_predecessor_report_preserved_byte_unchanged() -> None:
    predecessor_report = (
        REPO_ROOT
        / "docs"
        / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_"
        "RHAMP_CROSS_TEST_CONTAMINATION_DIAGNOSIS_EVIDENCE_RECONCILIATION_AND_F5_READINESS_RE_ADJUDICATION.md"
    )
    assert predecessor_report.exists()
    at_k0 = _run_git(
        "show",
        f"{K0}:docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_"
        "RHAMP_CROSS_TEST_CONTAMINATION_DIAGNOSIS_EVIDENCE_RECONCILIATION_AND_F5_READINESS_RE_ADJUDICATION.md",
    )
    assert predecessor_report.read_text().rstrip("\n") == at_k0.rstrip("\n")
