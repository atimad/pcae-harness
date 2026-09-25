"""Phase 150I adversarial tests for promoted-generation rehydration."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
from argparse import Namespace
from pathlib import Path

import pytest

from pcae.commands.phase_reports import run_phase_report_reconcile
from pcae.core.phase_reports import (
    COMPLETENESS_COMPLETE,
    COMPLETENESS_PENDING_PUSH,
    PhaseReport,
    compute_finalization_snapshot_id,
    resolve_terminal_promoted_generation,
)


ROOT = Path(__file__).resolve().parents[1]
REAL_150G_GENERATIONS = (
    ROOT / ".pcae/phase-reports/20260922-203915-150G.json",
    ROOT / ".pcae/phase-reports/20260922-210046-150G.json",
)


def _report(*, created_at: str, completeness: str = COMPLETENESS_COMPLETE) -> PhaseReport:
    pushed = completeness == COMPLETENESS_COMPLETE
    commits = ["a" * 8, "b" * 8] if pushed else ["a" * 8]
    return PhaseReport(
        phase_id="999Z",
        phase_name="SYNTHETIC-REHYDRATION-TEST",
        status="completed",
        summary="synthetic lifecycle evidence",
        created_at=created_at,
        files_changed=1,
        tests_run=1,
        test_results={"suite": "passed"},
        governance_results={"pcae_check": "passed"},
        commits=commits,
        pushed_status="pushed" if pushed else "not_pushed",
        origin_main_head_count=0 if pushed else 1,
        metadata={"phase_id": "999Z", "source_revision": ("b" * 40) if pushed else ("a" * 40)},
        report_completeness=completeness,
    )


def _write_generation(root: Path, stem: str, report: PhaseReport) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"{stem}-999Z.json"
    md_path = root / f"{stem}-999Z.md"
    json_path.write_text(report.render_json(), encoding="utf-8")
    md_path.write_text(report.render_markdown(), encoding="utf-8")
    return json_path, md_path


def _checkpoint(report: PhaseReport, md_path: Path) -> dict:
    return {
        "phase_id": report.phase_id,
        "phase_name": report.phase_name,
        "status": "completed",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:02Z",
        "report_digest": hashlib.sha256(md_path.read_bytes()).hexdigest(),
        "finalization_snapshot_id": compute_finalization_snapshot_id(report),
        "steps": {
            "pre_promotion_certification": "completed",
            "promotion_and_dispatch": "completed",
        },
    }


def _terminal_fixture(tmp_path: Path):
    reports = tmp_path / "reports"
    terminal = _report(created_at="2026-01-01T00:00:01+00:00")
    terminal_json, terminal_md = _write_generation(reports, "20260101-000001", terminal)
    return reports, terminal, terminal_json, terminal_md, _checkpoint(terminal, terminal_md)


def test_real_phase_150g_selects_checkpoint_bound_terminal_and_preserves_history() -> None:
    checkpoint = json.loads((ROOT / ".pcae/finalization-transactions/150G.json").read_text())
    result = resolve_terminal_promoted_generation(ROOT / ".pcae/phase-reports", "150G", checkpoint)
    assert result.blockers == ()
    assert result.terminal is not None
    assert result.terminal.json_path == REAL_150G_GENERATIONS[1]
    assert [item.json_path for item in result.historical] == [REAL_150G_GENERATIONS[0]]
    assert result.terminal.report_digest == checkpoint["report_digest"]


def test_real_phase_150g_reconcile_is_clean_and_read_only(capsys: pytest.CaptureFixture[str]) -> None:
    before = {path: path.read_bytes() for path in REAL_150G_GENERATIONS}
    before.update({path.with_suffix(".md"): path.with_suffix(".md").read_bytes() for path in REAL_150G_GENERATIONS})
    rc = run_phase_report_reconcile(Namespace(
        phase_id="150G", reports_dir=str(ROOT / ".pcae/phase-reports"),
        transaction_root=str(ROOT / ".pcae/finalization-transactions"),
        marker_path=str(ROOT / ".pcae/phase-reports/.last-notified.json"), json=True,
    ))
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["reconciliation_status"] == "reconciled"
    assert payload["terminal_selection_provenance"] == "completed_checkpoint_report_digest_and_finalization_snapshot_id"
    assert payload["historical_generation_count"] == 1
    assert payload["mutation_performed"] is False
    assert {path: path.read_bytes() for path in before} == before


def test_single_generation_happy_path_uses_checkpoint_not_filename_or_mtime(tmp_path: Path) -> None:
    reports, _, terminal_json, _, checkpoint = _terminal_fixture(tmp_path)
    os.utime(terminal_json, (1, 1))
    result = resolve_terminal_promoted_generation(reports, "999Z", checkpoint)
    assert result.blockers == ()
    assert result.terminal and result.terminal.json_path == terminal_json


def test_snapshot_computation_is_read_only() -> None:
    report = _report(created_at="2026-01-01T00:00:01+00:00")
    report.metadata["promotion_diagnostics"] = [{"status": "allowed"}]
    before = copy.deepcopy(report.to_dict())
    compute_finalization_snapshot_id(report)
    assert report.to_dict() == before


def test_legitimate_pending_generation_is_historical_regardless_of_lexical_order_or_mtime(tmp_path: Path) -> None:
    reports, _, terminal_json, _, checkpoint = _terminal_fixture(tmp_path)
    pending = _report(created_at="2026-01-01T00:00:00.500000+00:00", completeness=COMPLETENESS_PENDING_PUSH)
    pending_json, _ = _write_generation(reports, "99991231-235959", pending)
    os.utime(pending_json, (4_000_000_000, 4_000_000_000))
    result = resolve_terminal_promoted_generation(reports, "999Z", checkpoint)
    assert result.blockers == ()
    assert result.terminal and result.terminal.json_path == terminal_json
    assert [item.json_path for item in result.historical] == [pending_json]


def test_extra_forged_complete_generation_is_rejected_never_selected(tmp_path: Path) -> None:
    reports, _, _, _, checkpoint = _terminal_fixture(tmp_path)
    forged = _report(created_at="2026-01-01T00:00:01.500000+00:00")
    forged_json, _ = _write_generation(reports, "99991231-235959", forged)
    result = resolve_terminal_promoted_generation(reports, "999Z", checkpoint)
    assert result.terminal is None
    assert str(forged_json) in result.rejected_paths
    assert any("missing or ambiguous" in blocker for blocker in result.blockers)


def test_forged_generation_ordinal_is_not_a_selection_primitive(tmp_path: Path) -> None:
    reports, _, _, _, checkpoint = _terminal_fixture(tmp_path)
    forged = _report(created_at="2026-01-01T00:00:01.500000+00:00")
    data = forged.to_dict()
    data["generation_ordinal"] = 999999
    path = reports / "99991231-235959-999Z.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    path.with_suffix(".md").write_text(forged.render_markdown(), encoding="utf-8")
    result = resolve_terminal_promoted_generation(reports, "999Z", checkpoint)
    assert result.terminal is None
    assert str(path) in result.rejected_paths


def test_forged_latest_pointer_fails_closed(tmp_path: Path) -> None:
    reports, _, _, _, checkpoint = _terminal_fixture(tmp_path)
    forged = _report(created_at="2026-01-01T00:00:01+00:00")
    (reports / "latest.json").write_text(forged.render_json(), encoding="utf-8")
    (reports / "latest.md").write_text(forged.render_markdown() + "\nforged", encoding="utf-8")
    result = resolve_terminal_promoted_generation(reports, "999Z", checkpoint)
    assert result.terminal is None
    assert any("latest report pointer disagrees" in blocker for blocker in result.blockers)


def test_checkpoint_cannot_select_pending_historical_generation(tmp_path: Path) -> None:
    reports, terminal, _, terminal_md, _ = _terminal_fixture(tmp_path)
    pending = _report(created_at="2026-01-01T00:00:00.500000+00:00", completeness=COMPLETENESS_PENDING_PUSH)
    _, pending_md = _write_generation(reports, "20260101-000000", pending)
    forged_checkpoint = _checkpoint(pending, pending_md)
    result = resolve_terminal_promoted_generation(reports, "999Z", forged_checkpoint)
    assert result.terminal is None
    assert any("not trust-complete" in blocker for blocker in result.blockers)
    assert hashlib.sha256(terminal_md.read_bytes()).hexdigest() != forged_checkpoint["report_digest"]


def test_forged_checkpoint_cannot_reclassify_an_older_complete_generation(tmp_path: Path) -> None:
    reports, _, _, _, _ = _terminal_fixture(tmp_path)
    older = _report(created_at="2026-01-01T00:00:00.500000+00:00")
    older.summary = "different earlier complete payload"
    older.commits = ["a" * 8]
    older.metadata["source_revision"] = "a" * 40
    _, older_md = _write_generation(reports, "20260101-000000", older)
    forged_checkpoint = _checkpoint(older, older_md)
    result = resolve_terminal_promoted_generation(reports, "999Z", forged_checkpoint)
    assert result.terminal is None
    assert any("unbound promoted generation" in blocker for blocker in result.blockers)


def test_missing_or_malformed_terminal_fails_closed(tmp_path: Path) -> None:
    reports, _, terminal_json, _, checkpoint = _terminal_fixture(tmp_path)
    terminal_json.unlink()
    assert resolve_terminal_promoted_generation(reports, "999Z", checkpoint).terminal is None
    terminal_json.write_text("{", encoding="utf-8")
    result = resolve_terminal_promoted_generation(reports, "999Z", checkpoint)
    assert result.terminal is None
    assert str(terminal_json) in result.rejected_paths


def test_duplicate_checkpoint_identity_is_ambiguous_and_fails_closed(tmp_path: Path) -> None:
    reports, terminal, _, _, checkpoint = _terminal_fixture(tmp_path)
    _write_generation(reports, "20260101-000002", terminal)
    result = resolve_terminal_promoted_generation(reports, "999Z", checkpoint)
    assert result.terminal is None
    assert any("missing or ambiguous" in blocker for blocker in result.blockers)


def test_symlink_generation_is_rejected(tmp_path: Path) -> None:
    reports, _, terminal_json, _, checkpoint = _terminal_fixture(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_bytes(terminal_json.read_bytes())
    link = reports / "99991231-235959-999Z.json"
    link.symlink_to(outside)
    link.with_suffix(".md").write_text("forged", encoding="utf-8")
    result = resolve_terminal_promoted_generation(reports, "999Z", checkpoint)
    assert result.terminal is None
    assert str(link) in result.rejected_paths


def test_malformed_checkpoint_identity_fails_closed(tmp_path: Path) -> None:
    reports, _, _, _, checkpoint = _terminal_fixture(tmp_path)
    checkpoint["report_digest"] = "not-a-digest"
    result = resolve_terminal_promoted_generation(reports, "999Z", checkpoint)
    assert result.terminal is None
    assert any("digest is malformed" in blocker for blocker in result.blockers)


def test_notification_marker_for_arbitrary_historical_digest_conflicts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    reports, terminal, _, terminal_md, checkpoint = _terminal_fixture(tmp_path)
    pending = _report(created_at="2026-01-01T00:00:00.500000+00:00", completeness=COMPLETENESS_PENDING_PUSH)
    _, pending_md = _write_generation(reports, "20260101-000000", pending)
    transactions = tmp_path / "transactions"
    transactions.mkdir()
    (transactions / "999Z.json").write_text(json.dumps(checkpoint), encoding="utf-8")
    marker = tmp_path / "marker.json"
    marker.write_text(json.dumps({
        "phase_id": "999Z", "delivery_purpose": "ordinary_completion",
        "report_digest": hashlib.sha256(pending_md.read_bytes()).hexdigest(),
        "finalization_snapshot_id": compute_finalization_snapshot_id(pending),
    }), encoding="utf-8")
    rc = run_phase_report_reconcile(Namespace(
        phase_id="999Z", reports_dir=str(reports), transaction_root=str(transactions),
        marker_path=str(marker), json=True,
    ))
    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert payload["marker_state"] == "payload_conflict"
    assert "notification marker payload conflicts" in " ".join(payload["blockers"])
    assert hashlib.sha256(terminal_md.read_bytes()).hexdigest() == checkpoint["report_digest"]


def test_runtime_and_product_boundaries_are_untouched() -> None:
    changed = subprocess.check_output(
        [
            "git", "diff", "--name-only",
            "93424bea862aab27fcb2401a5e83e28481b1929a", "--",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    prohibited = [
        path for path in changed
        if path in {
            "src/pcae/core/hpac_pawa_recognition_core.py",
            "src/pcae/core/hpac_protected_admin_writer.py",
            "src/pcae/core/hpac_foundation.py",
        }
        or path.startswith("src/pcae/core/hpac_pawa_helper_")
        or path.startswith(("src/pcae/runtime/", "src/pcae/permission_broker/", "docs/contracts/"))
    ]
    assert prohibited == []
