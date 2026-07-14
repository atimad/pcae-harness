"""Phase 135O — dual-derivation coordinator: idempotency, failure isolation,
persistence containment, and no-go/execution-boundary tests."""

from __future__ import annotations

import subprocess

import pytest

from pcae.cltr.migration.coordinator import capture_pre_transaction, complete
from pcae.cltr.migration.enums import MigrationRecoveryClassification


def _enable(monkeypatch, epoch="epoch-1"):
    monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", epoch)


def _completion_fields(**overrides):
    fields = dict(
        transition_type="close_success",
        lifecycle_state="TERMINAL_SUCCESS",
        report_id="135O-C1", report_digest="a" * 64,
        metadata_id="135O-C1", metadata_digest="b" * 64,
        snapshot_id="135O-C1", snapshot_digest="b" * 64,
        promotion_id="b" * 64,
        notification_ids=("135O-C1:phase_complete",),
        notification_state="confirmed",
        notification_suppressed=False,
        receipt_id="receipt-1",
    )
    fields.update(overrides)
    return fields


def _run_full_cycle(tmp_path, monkeypatch, *, phase_id="135O-C1", source_revision="a" * 64):
    _enable(monkeypatch)
    root = tmp_path / "migration"
    package = capture_pre_transaction(
        phase_id=phase_id, entry_point="phase_complete", source_revision=source_revision,
        staged_final_revision=source_revision, phase_commit_ownership=(), intended_transition="phase_complete",
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE, migration_root=root,
    )
    result = complete(
        package, legacy_completion_fields=_completion_fields(report_id=phase_id, metadata_id=phase_id, snapshot_id=phase_id,
                                                              notification_ids=(f"{phase_id}:phase_complete",)),
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
        production_completion_continued=True, migration_root=root,
    )
    return root, package, result


def test_disabled_returns_none(tmp_path, monkeypatch):
    monkeypatch.delenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", raising=False)
    package = capture_pre_transaction(
        phase_id="X", entry_point="phase_complete", source_revision="a" * 64,
        staged_final_revision="a" * 64, phase_commit_ownership=(), intended_transition="phase_complete",
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE, migration_root=tmp_path / "migration",
    )
    assert package is None


def test_full_cycle_completes_and_is_eligible(tmp_path, monkeypatch):
    root, package, result = _run_full_cycle(tmp_path, monkeypatch)
    assert result.status == "completed"
    assert result.migration_progression_eligible is True
    assert result.evidence.production_authority.value == "legacy"


def test_idempotent_duplicate_pre_transaction_invocation(tmp_path, monkeypatch):
    _enable(monkeypatch)
    root = tmp_path / "migration"
    p1 = capture_pre_transaction(
        phase_id="X", entry_point="phase_complete", source_revision="a" * 64,
        staged_final_revision="a" * 64, phase_commit_ownership=(), intended_transition="phase_complete",
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE, migration_root=root,
    )
    p2 = capture_pre_transaction(
        phase_id="X", entry_point="phase_complete", source_revision="a" * 64,
        staged_final_revision="a" * 64, phase_commit_ownership=(), intended_transition="phase_complete",
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE, migration_root=root,
    )
    assert p1.transition_id == p2.transition_id
    assert p1.package_id == p2.package_id


def test_idempotent_duplicate_completion_invocation_no_immutable_overwrite_error(tmp_path, monkeypatch):
    root, package, result1 = _run_full_cycle(tmp_path, monkeypatch)
    result2 = complete(
        package, legacy_completion_fields=_completion_fields(), recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
        production_completion_continued=True, migration_root=root,
    )
    assert result2.status == "completed"
    assert result1.evidence.evidence_digest == result2.evidence.evidence_digest


def test_conflicting_replay_raises_on_content_mismatch(tmp_path, monkeypatch):
    root, package, result1 = _run_full_cycle(tmp_path, monkeypatch)
    conflicting = complete(
        package, legacy_completion_fields=_completion_fields(report_digest="different" * 8),
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
        production_completion_continued=True, migration_root=root,
    )
    # A genuine content conflict on an immutable artifact is a disclosed
    # failure, never a silent overwrite. The conflict surfaces as soon as
    # the differently-enriched revision is (re-)persisted.
    assert conflicting.status == "failed"
    assert conflicting.stage_failed == "input_assembly"


def test_rejected_candidate_never_gets_progression_credit(tmp_path, monkeypatch):
    _enable(monkeypatch)
    root = tmp_path / "migration"
    package = capture_pre_transaction(
        phase_id="REJ1", entry_point="phase_complete", source_revision="a" * 64,
        staged_final_revision="a" * 64, phase_commit_ownership=(), intended_transition="phase_complete",
        recovery_classification=MigrationRecoveryClassification.REJECTED_CANDIDATE, migration_root=root,
    )
    result = complete(
        package, legacy_completion_fields=_completion_fields(report_id="REJ1", metadata_id="REJ1", snapshot_id="REJ1",
                                                              notification_ids=("REJ1:phase_complete",)),
        recovery_classification=MigrationRecoveryClassification.REJECTED_CANDIDATE,
        production_completion_continued=True, migration_root=root,
    )
    assert result.status == "completed"
    assert result.migration_progression_eligible is False


def test_failure_isolation_never_raises_to_caller(tmp_path, monkeypatch):
    _enable(monkeypatch)
    root = tmp_path / "migration"
    package = capture_pre_transaction(
        phase_id="F1", entry_point="phase_complete", source_revision="a" * 64,
        staged_final_revision="a" * 64, phase_commit_ownership=(), intended_transition="phase_complete",
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE, migration_root=root,
    )
    # Malformed lifecycle_state triggers a derivation-stage failure, not an
    # unhandled exception.
    result = complete(
        package, legacy_completion_fields=_completion_fields(lifecycle_state="NOT_A_REAL_STATE"),
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
        production_completion_continued=True, migration_root=root,
    )
    assert result.status == "completed"  # cltr_derivation contains the error internally, status disclosed via evidence
    assert result.migration_progression_eligible is False


def test_failures_directory_populated_on_conflict(tmp_path, monkeypatch):
    root, package, _result1 = _run_full_cycle(tmp_path, monkeypatch)
    complete(
        package, legacy_completion_fields=_completion_fields(report_digest="different" * 8),
        recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
        production_completion_continued=True, migration_root=root,
    )
    failures_dir = root / "epochs" / "epoch-1" / "transitions" / package.transition_id / "failures"
    assert failures_dir.exists()
    assert list(failures_dir.iterdir())


class TestPersistenceContainment:
    def test_traversal_rejected(self, tmp_path):
        from pcae.cltr.migration.persistence import PathContainmentError, safe_join

        root = tmp_path / "migration"
        with pytest.raises(PathContainmentError):
            safe_join(root, "..", "escaped")

    def test_symlink_escape_rejected(self, tmp_path):
        from pcae.cltr.migration.persistence import PathContainmentError, safe_join

        root = tmp_path / "migration"
        root.mkdir(parents=True)
        outside = tmp_path / "outside"
        outside.mkdir()
        link = root / "epochs"
        link.symlink_to(outside)
        with pytest.raises(PathContainmentError):
            safe_join(root, "epochs", "e1")

    def test_immutable_evidence_never_silently_overwritten(self, tmp_path):
        from pcae.cltr.migration.persistence import write_immutable

        path = tmp_path / "evidence.json"
        write_immutable(path, b'{"a": 1}')
        write_immutable(path, b'{"a": 1}')  # identical content: no-op success
        with pytest.raises(ValueError):
            write_immutable(path, b'{"a": 2}')


class TestNoGoExecutionBoundary:
    def test_no_subprocess_in_coordinator_module(self):
        import pcae.cltr.migration.coordinator as mod

        assert "subprocess" not in mod.__dict__

    def test_no_subprocess_call_during_full_cycle(self, tmp_path, monkeypatch):
        def _boom(*args, **kwargs):
            raise AssertionError("migration coordinator must never invoke subprocess")

        monkeypatch.setattr(subprocess, "run", _boom)
        monkeypatch.setattr(subprocess, "Popen", _boom)
        monkeypatch.setattr(subprocess, "call", _boom)
        _run_full_cycle(tmp_path, monkeypatch)

    def test_no_socket_module_imported(self):
        import pcae.cltr.migration.coordinator as mod

        assert "socket" not in mod.__dict__

    def test_no_network_calls(self, tmp_path, monkeypatch):
        import socket

        def _boom(*args, **kwargs):
            raise AssertionError("migration coordinator must never open a socket")

        monkeypatch.setattr(socket, "socket", _boom)
        _run_full_cycle(tmp_path, monkeypatch)

    def test_no_notification_dispatch_module_referenced(self):
        import pcae.cltr.migration.coordinator as mod
        import pcae.cltr.migration.cltr_derivation as cltr_mod
        import pcae.cltr.migration.legacy_derivation as legacy_mod

        for module in (mod, cltr_mod, legacy_mod):
            assert "notifications" not in module.__dict__
