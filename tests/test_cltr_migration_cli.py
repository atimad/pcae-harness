"""Phase 135O — read-only `pcae cltr migration ...` CLI tests."""

from __future__ import annotations

import json

import pytest

from pcae.cli import build_parser
from pcae.cltr.migration.coordinator import capture_pre_transaction, complete
from pcae.cltr.migration.enums import MigrationRecoveryClassification


@pytest.fixture()
def isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _enable(monkeypatch, epoch="epoch-cli-1"):
    monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", epoch)


def _produce_evidence(phase_id="135O-CLI"):
    # Uses the default migration root (".pcae/cltr-migration", relative to
    # cwd) so the CLI handlers under test (which also use the default)
    # see it.
    package = capture_pre_transaction(
        phase_id=phase_id, entry_point="phase_complete", source_revision="a" * 64,
        staged_final_revision="a" * 64, phase_commit_ownership=(), intended_transition="phase_complete",
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
    )
    return complete(
        package,
        legacy_completion_fields={
            "transition_type": "close_success", "lifecycle_state": "TERMINAL_SUCCESS",
            "report_id": phase_id, "report_digest": "b" * 64, "metadata_id": phase_id,
            "metadata_digest": "c" * 64, "snapshot_id": phase_id, "snapshot_digest": "c" * 64,
            "promotion_id": "c" * 64, "notification_ids": (f"{phase_id}:phase_complete",),
            "notification_state": "confirmed", "notification_suppressed": False, "receipt_id": "receipt-1",
        },
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
        production_completion_continued=True,
    )


def test_parser_registers_cltr_migration_commands():
    parser = build_parser()
    args = parser.parse_args(["cltr", "migration", "status"])
    assert args.command == "cltr"
    assert args.cltr_command == "migration"
    assert args.cltr_migration_command == "status"


def test_status_disabled_by_default(isolated_cwd, capsys):
    parser = build_parser()
    args = parser.parse_args(["cltr", "migration", "status", "--json"])
    exit_code = args.handler(args)
    payload = json.loads(capsys.readouterr().out)
    assert payload["dual_derivation_enabled"] is False
    assert payload["mutation"] == "none"
    assert exit_code == 0


def test_status_text_mode_discloses_non_authority(isolated_cwd, capsys):
    parser = build_parser()
    args = parser.parse_args(["cltr", "migration", "status"])
    args.handler(args)
    out = capsys.readouterr().out
    assert "non-authoritative" in out
    assert "legacy" in out


def test_status_reflects_evidence_after_enabling(isolated_cwd, monkeypatch, capsys):
    _enable(monkeypatch)
    _produce_evidence()
    parser = build_parser()
    args = parser.parse_args(["cltr", "migration", "status", "--json"])
    args.handler(args)
    payload = json.loads(capsys.readouterr().out)
    assert payload["dual_derivation_enabled"] is True
    assert payload["transition_evidence_count"] == 1
    assert payload["migration_progression_eligible_count"] == 1


def test_reconcile_missing_phase(isolated_cwd, capsys):
    parser = build_parser()
    args = parser.parse_args(["cltr", "migration", "reconcile", "--phase-id", "NOPE", "--json"])
    exit_code = args.handler(args)
    payload = json.loads(capsys.readouterr().out)
    assert payload["found"] is False
    assert exit_code == 1


def test_reconcile_found_phase(isolated_cwd, monkeypatch, capsys):
    _enable(monkeypatch)
    _produce_evidence(phase_id="135O-RECON")
    parser = build_parser()
    args = parser.parse_args(["cltr", "migration", "reconcile", "--phase-id", "135O-RECON", "--json"])
    exit_code = args.handler(args)
    payload = json.loads(capsys.readouterr().out)
    assert payload["found"] is True
    assert payload["transitions"][0]["migration_progression_eligible"] is True
    assert exit_code == 0


def test_reconcile_never_mutates_filesystem(isolated_cwd, monkeypatch, capsys):
    import hashlib

    _enable(monkeypatch)
    _produce_evidence(phase_id="135O-NOMUTATE")

    root = isolated_cwd / ".pcae" / "cltr-migration"

    def _tree_digest():
        h = hashlib.sha256()
        for path in sorted(root.rglob("*")):
            if path.is_file():
                h.update(str(path.relative_to(root)).encode())
                h.update(path.read_bytes())
        return h.hexdigest()

    before = _tree_digest()
    parser = build_parser()
    args = parser.parse_args(["cltr", "migration", "reconcile", "--phase-id", "135O-NOMUTATE", "--json"])
    args.handler(args)
    args2 = parser.parse_args(["cltr", "migration", "status", "--json"])
    args2.handler(args2)
    capsys.readouterr()
    after = _tree_digest()
    assert before == after
