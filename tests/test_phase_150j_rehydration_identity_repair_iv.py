"""Independent Phase 150J IV: isolated real artifacts and exploit witnesses.

Finding tests assert reproducible current defects, not security acceptance.
No fixture writes target the canonical repository.
"""
import copy
import hashlib
import json
import os
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path

import pytest

from pcae.commands.phase_reports import run_phase_report_reconcile
from pcae.core.phase_reports import PhaseReport, compute_finalization_snapshot_id, resolve_terminal_promoted_generation

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "841c61e13b20132896b4b9674e4add58544364ac"
# Actual governed closure, also Phase 150K's independently recorded entry.
PHASE_END = "c90254a2648e4afb263373fd4aff2afb48946e2e"
STEMS = ("20260922-203915-150G", "20260922-210046-150G")


@pytest.fixture
def record(tmp_path):
    reports = tmp_path / ".pcae/phase-reports"
    reports.mkdir(parents=True)
    for stem in STEMS:
        for ext in ("json", "md"):
            shutil.copyfile(ROOT / ".pcae/phase-reports" / f"{stem}.{ext}", reports / f"{stem}.{ext}")
    transactions = tmp_path / ".pcae/finalization-transactions"
    transactions.mkdir()
    cp = json.loads((ROOT / ".pcae/finalization-transactions/150G.json").read_text())
    receipt_source = ROOT / cp["receipt_path"]
    receipt_dest = tmp_path / cp["receipt_path"]
    receipt_dest.parent.mkdir(parents=True)
    shutil.copyfile(receipt_source, receipt_dest)
    cp["receipt_path"] = str(receipt_dest)
    (transactions / "150G.json").write_text(json.dumps(cp))
    return reports, transactions, cp


def resolve(record):
    reports, _, cp = record
    return resolve_terminal_promoted_generation(reports, "150G", cp)


def reconcile(record, capsys, marker=None):
    reports, transactions, _ = record
    rc = run_phase_report_reconcile(Namespace(phase_id="150G", reports_dir=str(reports),
        transaction_root=str(transactions), marker_path=str(marker or reports / "absent-marker.json"), json=True))
    return rc, json.loads(capsys.readouterr().out)


def terminal(record):
    return record[0] / f"{STEMS[1]}.json"


def historical(record):
    return record[0] / f"{STEMS[0]}.json"


def test_real_record_is_clean_and_inspection_preserves_all_bytes(record, capsys):
    files = list(record[0].parent.rglob("*"))
    before = {p: p.read_bytes() for p in files if p.is_file()}
    selected = resolve(record)
    assert selected.terminal.json_path == terminal(record)
    assert len(selected.historical) == 1
    rc, payload = reconcile(record, capsys)
    assert rc == 0 and payload["reconciliation_status"] == "reconciled"
    assert not payload["mutation_performed"]
    assert {p: p.read_bytes() for p in before} == before


def test_independent_artifact_digests_match_archived_phase_150h_inventory():
    expected = ("da5a678cbf6e88eb6d37a8bad3fead8217aa92dd30709fab52edabbe5c308551",
                "5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1")
    for stem, digest in zip(STEMS, expected):
        assert hashlib.sha256((ROOT / ".pcae/phase-reports" / f"{stem}.md").read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("attack", ["missing-terminal", "malformed-terminal", "duplicate-terminal",
    "terminal-md-tamper", "terminal-json-tamper", "symlink-json", "symlink-md", "wrong-phase",
    "forged-complete", "ordinal", "stale-latest", "forged-latest", "missing-checkpoint",
    "malformed-checkpoint", "checkpoint-history"])
def test_attacks_that_current_implementation_rejects(record, attack):
    reports, _, cp = record
    t = terminal(record)
    data = json.loads(t.read_text())
    if attack == "missing-terminal":
        t.unlink()
    elif attack == "malformed-terminal":
        t.write_text("{")
    elif attack == "duplicate-terminal":
        for ext in ("json", "md"):
            shutil.copyfile(t.with_suffix("." + ext), reports / f"duplicate-150G.{ext}")
    elif attack == "terminal-md-tamper":
        t.with_suffix(".md").write_text(t.with_suffix(".md").read_text() + "\nunauthorized technical conclusion")
    elif attack == "terminal-json-tamper":
        data["summary"] = "unauthorized technical conclusion"
        t.write_text(json.dumps(data))
    elif attack.startswith("symlink"):
        p = t if attack == "symlink-json" else t.with_suffix(".md")
        outside = reports.parent / ("outside" + p.suffix)
        shutil.copyfile(p, outside)
        p.unlink()
        p.symlink_to(outside)
    elif attack == "wrong-phase":
        data["phase_id"] = "150F"
        t.write_text(json.dumps(data))
    elif attack in ("forged-complete", "ordinal"):
        data["summary"] = "unrelated complete generation"
        if attack == "ordinal":
            data["generation_ordinal"] = 999999
        extra = reports / "zzzz-150G.json"
        extra.write_text(json.dumps(data))
        extra.with_suffix(".md").write_bytes(t.with_suffix(".md").read_bytes())
    elif attack in ("stale-latest", "forged-latest"):
        src = historical(record) if attack == "stale-latest" else t
        shutil.copyfile(src, reports / "latest.json")
        shutil.copyfile(src.with_suffix(".md"), reports / "latest.md")
        if attack == "forged-latest":
            (reports / "latest.md").write_text("forged")
    elif attack == "missing-checkpoint":
        cp.clear()
    elif attack == "malformed-checkpoint":
        cp["report_digest"] = "malformed"
    elif attack == "checkpoint-history":
        p = historical(record)
        cp["report_digest"] = hashlib.sha256(p.with_suffix(".md").read_bytes()).hexdigest()
        cp["finalization_snapshot_id"] = compute_finalization_snapshot_id(PhaseReport(**json.loads(p.read_text())))
    assert resolve(record).terminal is None


@pytest.mark.parametrize("manipulation", ["mtime", "lexical-name", "delete-history"])
def test_non_authoritative_ordering_does_not_change_terminal(record, manipulation):
    p = historical(record)
    if manipulation == "mtime":
        os.utime(p, (4_000_000_000, 4_000_000_000))
    elif manipulation == "lexical-name":
        p.rename(p.parent / "zzzz-150G.json")
        p.with_suffix(".md").rename(p.parent / "zzzz-150G.md")
    else:
        p.unlink()
        p.with_suffix(".md").unlink()
    assert resolve(record).terminal.json_path == terminal(record)


def test_finding_f1_forged_pending_history_is_accepted_without_provenance(record, capsys):
    p = historical(record)
    data = json.loads(p.read_text())
    data["summary"] = "ATTACKER: unrelated technical report never promoted by governed lifecycle"
    data["commits"] = []
    data["metadata"]["source_revision"] = "not-a-repository-commit"
    data["created_at"] = "2000-01-01T00:00:00+00:00"
    forged = p.parent / "attacker-150G.json"
    forged.write_text(json.dumps(data))
    forged.with_suffix(".md").write_text(PhaseReport(**data).render_markdown())
    result = resolve(record)
    assert result.blockers == () and len(result.historical) == 2
    assert forged in [g.json_path for g in result.historical]
    rc, payload = reconcile(record, capsys)
    assert rc == 0 and payload["reconciliation_status"] == "reconciled"


def test_finding_f2_forged_checkpoint_and_report_select_attacker_terminal(record, capsys):
    reports, transactions, cp = record
    p = terminal(record)
    data = json.loads(p.read_text())
    data["summary"] = "ATTACKER: invented technical conclusion"
    data["commits"] = ["f" * 8]
    data["metadata"]["source_revision"] = "f" * 40
    p.write_text(json.dumps(data))
    p.with_suffix(".md").write_text(PhaseReport(**data).render_markdown())
    cp["report_digest"] = hashlib.sha256(p.with_suffix(".md").read_bytes()).hexdigest()
    cp["finalization_snapshot_id"] = compute_finalization_snapshot_id(PhaseReport(**data))
    # Original receipt remains unchanged: reconciler does not bind it to this report.
    (transactions / "150G.json").write_text(json.dumps(cp))
    # Older generation's self-declared commit subset is attacker-controlled too.
    h = historical(record)
    old = json.loads(h.read_text())
    old["commits"] = []
    h.write_text(json.dumps(old))
    assert resolve(record).terminal.report.summary.startswith("ATTACKER")
    rc, payload = reconcile(record, capsys)
    assert rc == 0 and payload["reconciliation_status"] == "reconciled"


def test_finding_f3_incomplete_report_claiming_complete_is_selected(record):
    p = terminal(record)
    data = json.loads(p.read_text())
    data["test_results"] = {}
    data["governance_results"] = {}
    data["commits"] = []
    data["metadata"]["source_revision"] = ""
    p.write_text(json.dumps(data))
    p.with_suffix(".md").write_text(PhaseReport(**data).render_markdown())
    cp = record[2]
    cp["report_digest"] = hashlib.sha256(p.with_suffix(".md").read_bytes()).hexdigest()
    cp["finalization_snapshot_id"] = compute_finalization_snapshot_id(PhaseReport(**data))
    historical(record).unlink()
    historical(record).with_suffix(".md").unlink()
    assert resolve(record).terminal is not None
    completeness, missing, _ = PhaseReport(**data).assess_completeness()
    assert completeness != "complete" and missing


@pytest.mark.parametrize("marker_data", ["{", {"phase_id": "150G", "report_digest": "f" * 64,
    "delivery_purpose": "ordinary_completion", "finalization_snapshot_id": "e" * 64}])
def test_notification_malformed_or_wrong_identity_does_not_establish_provenance(record, capsys, marker_data):
    p = record[0] / "marker.json"
    p.write_text(marker_data if isinstance(marker_data, str) else json.dumps(marker_data))
    rc, payload = reconcile(record, capsys, p)
    # A malformed marker is currently treated as absent (separate disclosed limitation).
    assert payload["marker_state"] in ("not_dispatched", "payload_conflict")
    if isinstance(marker_data, dict):
        assert rc == 1


def test_snapshot_inspection_is_pure(record):
    data = PhaseReport(**json.loads(terminal(record).read_text()))
    data.metadata["fgsc_lifecycle_state"] = "original"
    before = copy.deepcopy(data.to_dict())
    compute_finalization_snapshot_id(data)
    assert data.to_dict() == before


def test_finding_f4_latest_pointer_nonobject_is_not_rejected(record):
    (record[0] / "latest.json").write_text("[]")
    assert resolve(record).terminal is not None


def test_three_generations_supported_but_third_has_no_authenticated_origin(record):
    p = historical(record)
    shutil.copyfile(p, p.parent / "third-150G.json")
    shutil.copyfile(p.with_suffix(".md"), p.parent / "third-150G.md")
    result = resolve(record)
    assert len(result.historical) == 2 and result.terminal is not None


def test_traversal_phase_cannot_select_terminal(record):
    assert resolve_terminal_promoted_generation(record[0], "../150G", record[2]).terminal is None


def test_unrelated_historical_phase_is_rejected(record):
    p = historical(record)
    data = json.loads(p.read_text())
    data["phase_id"] = "150F"
    p.write_text(json.dumps(data))
    assert resolve(record).terminal is None


def test_receipt_digest_tampering_conflicts(record, capsys):
    p = Path(record[2]["receipt_path"])
    data = json.loads(p.read_text())
    data["phase_id"] = "150F"
    p.write_text(json.dumps(data))
    rc, payload = reconcile(record, capsys)
    assert rc == 1 and payload["receipt_state"] == "corrupt"


def test_finding_f5_unbound_notification_marker_claim_is_accepted(record, capsys):
    p = record[0] / "marker.json"
    p.write_text(json.dumps({"phase_id": "150G", "authority": True}))
    rc, payload = reconcile(record, capsys, p)
    assert rc == 0 and payload["marker_state"] == "already_dispatched"


def test_checkpoint_wrong_name_and_fake_certification_evidence_are_ignored(record):
    record[2]["phase_name"] = "ATTACKER DIFFERENT PHASE"
    record[2]["evidence_id"] = "nonexistent"
    record[2]["extraction_digests"] = {}
    assert resolve(record).terminal is not None


def test_phase_150i_production_diff_has_exactly_two_lifecycle_files():
    paths = subprocess.check_output(["git", "diff", "--name-only", "93424bea", ENTRY, "--", "src/pcae"], cwd=ROOT, text=True).splitlines()
    assert paths == ["src/pcae/commands/phase_reports.py", "src/pcae/core/phase_reports.py"]


def test_this_iv_has_zero_production_and_contract_delta():
    assert subprocess.check_output(["git", "diff", "--name-only", "--no-renames", ENTRY, PHASE_END, "--", "src/pcae", "docs/contracts"], cwd=ROOT, text=True) == ""
