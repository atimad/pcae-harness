"""Phase 150K architectural-stop evidence, not a security acceptance suite.

Synthetic files live only in tmp_path. Passing defect witnesses means the
missing provenance primitive is reproduced; no repair is claimed.
"""
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from pcae.core.phase_reports import PhaseReport, compute_finalization_snapshot_id, resolve_terminal_promoted_generation
from pcae.core.finalization_transaction import _build_pre_promotion_artifacts

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "c90254a2648e4afb263373fd4aff2afb48946e2e"
# Actual governed closure, independently recorded as Phase 150L's entry.
PHASE_END = "8c998d2b2654e45e189bc3bfda57c7b6ecd71d7f"


def write_pair(path, data):
    path.write_text(json.dumps(data))
    path.with_suffix(".md").write_text(PhaseReport(**data).render_markdown())


@pytest.fixture
def synthetic(tmp_path):
    """Arbitrary phase identity, deliberately no governed event behind it."""
    reports = tmp_path / "reports"
    reports.mkdir()
    data = json.loads((ROOT / ".pcae/phase-reports/20260922-210046-150G.json").read_text())
    data["phase_id"] = "181Q"
    data["phase_name"] = "SYNTHETIC-PROVENANCE-DIAGNOSTIC"
    data["metadata"]["phase_id"] = "181Q"
    data["metadata"]["source_revision"] = "a" * 40
    data["commits"] = ["a" * 8]
    data["summary"] = "Synthetic content never emitted by governed lifecycle"
    terminal = reports / "terminal-181Q.json"
    write_pair(terminal, data)
    cp = {"phase_id": "181Q", "phase_name": data["phase_name"], "status": "completed",
          "started_at": "2026-09-22T21:00:46Z", "completed_at": "2026-09-22T21:00:48Z",
          "steps": {"pre_promotion_certification": "completed", "promotion_and_dispatch": "completed"}}
    cp["report_digest"] = hashlib.sha256(terminal.with_suffix(".md").read_bytes()).hexdigest()
    cp["finalization_snapshot_id"] = compute_finalization_snapshot_id(PhaseReport(**data))
    historical_data = copy.deepcopy(data)
    historical_data.update(report_completeness="pending_push", pushed_status="not_pushed",
                           origin_main_head_count=1, created_at="2026-09-22T20:39:15+00:00")
    historical = reports / "historical-181Q.json"
    write_pair(historical, historical_data)
    return reports, terminal, historical, cp


def resolve(record):
    return resolve_terminal_promoted_generation(record[0], "181Q", record[3])


@pytest.mark.parametrize("attack", ["forged-pending", "fabricated-same-phase", "valid-digest-invalid-origin",
    "wrong-task", "broken-predecessor", "chain-cycle", "future-predecessor", "forged-metadata",
    "missing-provenance-edge", "unproven-three-generation-chain"])
def test_missing_history_root_witnesses(synthetic, attack):
    reports, _, h, _ = synthetic
    data = json.loads(h.read_text())
    data["metadata"]["task_id"] = "attacker-task"
    data["metadata"]["generation_predecessor"] = {
        "broken-predecessor": "unknown", "chain-cycle": "self", "future-predecessor": "future"
    }.get(attack, "unproven")
    data["summary"] = "Forged history without a governed generation event"
    if attack in ("forged-pending", "fabricated-same-phase", "valid-digest-invalid-origin"):
        data["commits"] = []
        data["metadata"]["source_revision"] = "not-a-repository-commit"
    write_pair(h, data)
    if attack == "unproven-three-generation-chain":
        write_pair(reports / "extra-181Q.json", data)
    result = resolve(synthetic)
    assert result.terminal is not None and h in [x.json_path for x in result.historical]
    # Acceptance is the architectural blocker, NOT the required security result.


@pytest.mark.parametrize("attack", ["coordinated-checkpoint", "forged-completion-metadata",
    "unchanged-receipt-reference", "copied-receipt-reference", "checkpoint-replay", "receipt-replay"])
def test_terminal_identity_and_adjacent_claims_are_not_a_root(synthetic, attack):
    _, t, _, cp = synthetic
    data = json.loads(t.read_text())
    data["summary"] = "Coordinated forged terminal, not produced by lifecycle"
    data["metadata"]["completion_metadata_digest"] = "f" * 64
    write_pair(t, data)
    cp["report_digest"] = hashlib.sha256(t.with_suffix(".md").read_bytes()).hexdigest()
    cp["finalization_snapshot_id"] = compute_finalization_snapshot_id(PhaseReport(**data))
    cp["receipt_path"] = "unchanged-or-copied-receipt.json"
    cp["receipt_logical_delivery_id"] = "unrelated-delivery"
    cp["evidence_id"] = "nonexistent"
    cp["extraction_digests"] = {"phase_report": "f" * 64}
    assert resolve(synthetic).terminal.report.summary.startswith("Coordinated forged")
    # This proves selector non-consumption, not CLI receipt acceptance; real CLI
    # unchanged-receipt acceptance is independently reproduced by the 150J suite.


@pytest.mark.parametrize("attack", ["other-phase", "wrong-phase-history", "ordinal", "symlink",
    "duplicate-terminal", "stale-latest", "forged-latest", "missing-checkpoint", "malformed-terminal"])
def test_existing_structural_defenses_remain(synthetic, attack):
    reports, t, h, cp = synthetic
    if attack in ("other-phase", "wrong-phase-history"):
        data = json.loads(h.read_text()); data["phase_id"] = "181R"; write_pair(h, data)
    elif attack == "ordinal":
        data = json.loads(h.read_text()); data["generation_ordinal"] = 999999; h.write_text(json.dumps(data))
    elif attack == "symlink":
        target = reports.parent / "outside.json"; target.write_bytes(t.read_bytes()); t.unlink(); t.symlink_to(target)
    elif attack == "duplicate-terminal":
        (reports / "duplicate-181Q.json").write_bytes(t.read_bytes())
        (reports / "duplicate-181Q.md").write_bytes(t.with_suffix(".md").read_bytes())
    elif attack in ("stale-latest", "forged-latest"):
        source = h if attack == "stale-latest" else t
        (reports / "latest.json").write_bytes(source.read_bytes())
        (reports / "latest.md").write_text("forged" if attack == "forged-latest" else source.with_suffix(".md").read_text())
    elif attack == "missing-checkpoint":
        cp.clear()
    else:
        t.write_text("{")
    assert resolve(synthetic).terminal is None


@pytest.mark.parametrize("attack", ["mtime", "filename", "single-generation", "two-generations", "no-notification"])
def test_structural_compatibility_not_provenance(synthetic, attack):
    reports, t, h, cp = synthetic
    if attack == "mtime":
        os.utime(h, (4_000_000_000, 4_000_000_000))
    elif attack == "filename":
        h.rename(reports / "zzzz-181Q.json"); h.with_suffix(".md").rename(reports / "zzzz-181Q.md")
    elif attack == "single-generation":
        h.unlink(); h.with_suffix(".md").unlink()
    elif attack == "no-notification":
        data = json.loads(t.read_text()); data["notification_result"] = {}; write_pair(t, data)
        cp["report_digest"] = hashlib.sha256(t.with_suffix(".md").read_bytes()).hexdigest()
    assert resolve(synthetic).terminal is not None


def test_nonobject_latest_pointer_witness(synthetic):
    (synthetic[0] / "latest.json").write_text("[]")
    assert resolve(synthetic).terminal is not None


def test_full_trust_incomplete_despite_stored_complete_claim(synthetic):
    _, t, h, cp = synthetic
    data = json.loads(t.read_text())
    data.update(test_results={}, governance_results={}, commits=[])
    data["metadata"]["source_revision"] = ""
    write_pair(t, data)
    cp["report_digest"] = hashlib.sha256(t.with_suffix(".md").read_bytes()).hexdigest()
    cp["finalization_snapshot_id"] = compute_finalization_snapshot_id(PhaseReport(**data))
    h.unlink(); h.with_suffix(".md").unlink()
    assert resolve(synthetic).terminal is not None
    state, missing, _ = PhaseReport(**data).assess_completeness()
    assert state != "complete" and missing


def test_traversal_does_not_find_a_terminal(synthetic):
    assert resolve_terminal_promoted_generation(synthetic[0], "../181Q", synthetic[3]).terminal is None


def test_certification_derivation_is_reproducible_from_supplied_report_without_origin():
    report = PhaseReport(**json.loads((ROOT / ".pcae/phase-reports/20260922-210046-150G.json").read_text()))
    report.summary = "Invented conclusion supplied to pure certification derivation"
    a = _build_pre_promotion_artifacts(report, report.phase_id, report.phase_name)
    b = _build_pre_promotion_artifacts(report, report.phase_id, report.phase_name)
    assert a[1].compute_digest() == b[1].compute_digest()
    assert a[-1].compute_digest() == b[-1].compute_digest()
    # Recomputable deterministic extraction is not an authenticated origin event.


def test_committed_completion_metadata_has_no_generation_chain_anchor():
    raw = subprocess.check_output(["git", "show", "a6d475ef:.pcae/phase-completion-metadata.json"], cwd=ROOT, text=True)
    data = json.loads(raw)
    assert data["phase_id"] == "150G"
    assert not {"report_generation_certificates", "promoted_generation_index", "generation_predecessors", "terminal_generation_digest"}.intersection(data)


def test_runtime_artifact_sets_are_not_repository_committed_root():
    paths = subprocess.check_output(["git", "ls-files", ".pcae/phase-reports", ".pcae/finalization-transactions", ".pcae/delivery-receipts", ".pcae/provenance-history.json"], cwd=ROOT, text=True)
    assert not paths


def test_architectural_stop_changes_no_production_or_contracts():
    assert not subprocess.check_output(["git", "diff", "--name-only", "--no-renames", ENTRY, PHASE_END, "--", "src/pcae", "docs/contracts"], cwd=ROOT, text=True)
