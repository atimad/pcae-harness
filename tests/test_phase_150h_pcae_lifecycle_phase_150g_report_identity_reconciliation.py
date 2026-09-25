"""Phase 150H: independent evidence for the Phase 150G report-identity conflict.

These tests do not repair or reinterpret Phase 150G.  They reconstruct the
two promoted generations and prove why the read-only reconciler reports a
false payload conflict against an otherwise matching checkpoint/marker.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
from pathlib import Path

from pcae.commands import phase as phase_command
from pcae.commands import phase_reports as phase_report_commands
from pcae.core import phase_reports
from pcae.core.phase_reports import (
    PhaseReport,
    compute_finalization_snapshot_id,
    compute_report_digest,
)


ROOT = Path(__file__).resolve().parents[1]
ENTRY_COMMIT = "a6d475ef474514533e0144952d4f2f89374c3d2e"
GEN_A = ROOT / ".pcae/phase-reports/20260922-203915-150G.json"
GEN_B = ROOT / ".pcae/phase-reports/20260922-210046-150G.json"
GEN_B_MD = ROOT / ".pcae/phase-reports/20260922-210046-150G.md"
CHECKPOINT = ROOT / ".pcae/finalization-transactions/150G.json"
MARKER = ROOT / ".pcae/phase-reports/.last-notified.json"
EXPECTED_TERMINAL_REPORT_DIGEST = (
    "5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1"
)
EXPECTED_SNAPSHOT_ID = (
    "232104b62f1c78b24732735cf1185f62790e0b0555a141d6d348d70fe5c078e8"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _report(path: Path) -> PhaseReport:
    return PhaseReport(**_json(path))


def test_exactly_two_promoted_phase_150g_generations_are_preserved() -> None:
    generations = sorted(
        path.name
        for path in (ROOT / ".pcae/phase-reports").glob("*-150G.json")
    )
    assert generations == [GEN_A.name, GEN_B.name]


def test_generation_a_is_the_expected_non_authoritative_pending_push_stage() -> None:
    report = _json(GEN_A)
    assert report["phase_id"] == "150G"
    assert report["report_completeness"] == "pending_push"
    assert report["pushed_status"] == "not_pushed"
    assert report["origin_main_head_count"] == 3
    assert report["metadata"]["source_revision"] == (
        "4b56c18fe1918fccd04244adf927509e6c5b066b"
    )
    assert report["commits"] == ["31ebe985", "40efd807", "4b56c18f"]


def test_generation_b_is_the_unambiguous_terminal_pushed_generation() -> None:
    report = _json(GEN_B)
    assert report["phase_id"] == "150G"
    assert report["report_completeness"] == "complete"
    assert report["pushed_status"] == "pushed"
    assert report["origin_main_head_count"] == 0
    assert report["metadata"]["source_revision"] == (
        "2969be8eb6d0a98781c0ef757781096b67101f4a"
    )
    assert report["commits"] == [
        "31ebe985",
        "40efd807",
        "4b56c18f",
        "3300cd81",
        "2969be8e",
    ]


def test_terminal_markdown_digest_matches_checkpoint_and_marker_is_global_latest() -> None:
    checkpoint = _json(CHECKPOINT)
    marker = _json(MARKER)
    assert _sha256(GEN_B_MD) == EXPECTED_TERMINAL_REPORT_DIGEST
    assert checkpoint["report_digest"] == EXPECTED_TERMINAL_REPORT_DIGEST
    # At Phase 150H preflight this global marker still named 150G and matched
    # the digest above.  Normal 150H notification legitimately rotates the
    # global latest marker; it is not immutable per-phase evidence.
    if marker["phase_id"] == "150G":
        assert marker["report_digest"] == EXPECTED_TERMINAL_REPORT_DIGEST
    else:
        assert marker["phase_id"] == "150H"
        assert marker["report_digest"] != EXPECTED_TERMINAL_REPORT_DIGEST


def test_terminal_semantic_snapshot_matches_checkpoint_and_global_marker_rotates() -> None:
    report = _report(GEN_B)
    checkpoint = _json(CHECKPOINT)
    marker = _json(MARKER)
    assert compute_finalization_snapshot_id(report) == EXPECTED_SNAPSHOT_ID
    assert checkpoint["finalization_snapshot_id"] == EXPECTED_SNAPSHOT_ID
    if marker["phase_id"] == "150G":
        assert marker["finalization_snapshot_id"] == EXPECTED_SNAPSHOT_ID
    else:
        assert marker["phase_id"] == "150H"
        assert marker["finalization_snapshot_id"] != EXPECTED_SNAPSHOT_ID


def test_json_round_trip_cannot_reproduce_the_certified_markdown_digest() -> None:
    report = _report(GEN_B)
    assert compute_report_digest(report) == (
        "59dda6c6f0ab09ed465a021a80eaf101c60254c872a4c39cd07d375213b2775f"
    )
    assert compute_report_digest(report) != EXPECTED_TERMINAL_REPORT_DIGEST


def test_lossy_json_round_trip_is_the_specific_digest_divergence() -> None:
    persisted_markdown = GEN_B_MD.read_text(encoding="utf-8")
    report = _report(GEN_B)
    report.notification_result = {}
    round_trip_markdown = report.render_markdown()
    assert "## Report Consistency" in persisted_markdown
    assert "- **Canonical report:** present" in persisted_markdown
    assert "## Report Consistency" not in round_trip_markdown
    assert _json(GEN_B)["canonical_report_used"] is False
    # canonical_report_content influenced the certified Markdown but is
    # intentionally absent from PhaseReport.to_dict()/the persisted JSON.
    assert "canonical_report_content" not in _json(GEN_B)


def test_reconciler_is_read_only_and_no_longer_recomputes_from_lossy_json() -> None:
    source = inspect.getsource(phase_report_commands.run_phase_report_reconcile)
    assert "resolve_terminal_promoted_generation" in source
    assert "generation.report_digest" in source
    assert "compute_report_digest(report)" not in source
    assert '"mutation_performed": False' in source
    assert "never promotes, dispatches, writes a marker" in source


def test_staged_then_terminal_generations_are_explicit_lifecycle_behavior() -> None:
    source = inspect.getsource(phase_reports.finalize_phase_report)
    assert "COMPLETENESS_PENDING_PUSH" in source
    assert "a normal re-finalization after" in source
    assert "the push promotes the report to COMPLETE" in source
    assert "never notified" in source


def test_finalization_transaction_certifies_trial_then_callback_regenerates_report() -> None:
    command_source = inspect.getsource(phase_command._finalize_report_and_notify)
    finalize_source = inspect.getsource(phase_reports.finalize_phase_report)
    assert "report=trial_report" in command_source
    assert "promote_and_dispatch=_promote_and_dispatch" in command_source
    assert "return finalize_phase_report(" in command_source
    assert "report = make_phase_report(" in finalize_source


def test_consistency_command_isolates_construction_time_validation_mutation() -> None:
    source = inspect.getsource(phase_report_commands.run_phase_report_consistency)
    assert "inspection_report = copy.deepcopy(report)" in source
    assert "validate_derived_correctness(inspection_report)" in source
    assert 'compute_finalization_snapshot_id(report)' in source


def test_phase_150g_technical_and_runtime_truth_is_unchanged() -> None:
    report = _json(GEN_B)
    joined = " ".join(
        [report["summary"], *report["explicit_no_go_confirmations"]]
    )
    assert "shared recognition core implemented" in joined
    assert "No helper admission wiring" in joined
    assert "No helper step 9-prime" in joined
    assert "No foundation boundary repair" in joined
    assert "No N-16-6 or N-16-7 work" in joined
    architecture = report["architecture_status"]
    assert architecture["current_runtime_state"] == "Observed"
    assert architecture["current_maximum_capability"] == "observe"
    assert architecture["execution_availability"] == "unavailable"


def test_phase_150h_has_no_production_or_contract_delta() -> None:
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            f"{ENTRY_COMMIT}..HEAD",
            "--",
            "src/pcae",
            "docs/contracts",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert changed == []
