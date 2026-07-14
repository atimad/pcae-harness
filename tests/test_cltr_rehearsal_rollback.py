"""Phase 135U — Rollback rehearsal implementation tests (135Q §33/§36/§37/
§38, implemented here for the first time). Covers request model,
deterministic identity, target validation, atomic pointer rollback,
immutable history, evidence, idempotency, conflicting replay, crash
injection, quarantine, containment, CLI wiring, production/notification
isolation, and no-execution.

Mirrors ``tests/test_cltr_rehearsal_coordinator.py``'s hermetic,
low-level fixture pattern (``assemble_pre_transaction`` +
``enrich_legacy_completion`` directly, bypassing the full finalization
transaction) so two distinct, finalized rehearsal generations can be
produced under the *same* ``transition_id`` -- required to have a real
rollback target.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from pcae.cltr.migration.assembly import assemble_pre_transaction, enrich_legacy_completion
from pcae.cltr.migration.cltr_derivation import derive_cltr
from pcae.cltr.migration.comparison import compare
from pcae.cltr.migration.legacy_derivation import derive_legacy
from pcae.cltr.migration.persistence import PathContainmentError
from pcae.cltr.migration.rehearsal import rollback as rb
from pcae.cltr.migration.rehearsal.coordinator import run_stage2_rehearsal
from pcae.cltr.migration.rehearsal.enums import RollbackOutcome
from pcae.cltr.migration.rehearsal.persistence import (
    DEFAULT_MIGRATION_ROOT,
    generations_dir,
    quarantine_dir,
    read_json,
    rollbacks_dir,
)
from pcae.cltr.migration.rehearsal.pointer import read_pointer

TRANSITION_ID = "135u-transition-1"
EPOCH = "epoch-135u"
AUTHORITY_EPOCH = "legacy|epoch-135u"


def _make_package(phase_id: str, transition_id: str, revision: str):
    package = assemble_pre_transaction(
        migration_epoch=EPOCH,
        authority_epoch=AUTHORITY_EPOCH,
        phase_id=phase_id,
        entry_point="phase_complete",
        transition_id=transition_id,
        predecessor_transition_id=None,
        fields={
            "phase_id": phase_id, "task_id": None, "entry_point": "phase_complete",
            "source_revision": revision, "staged_final_revision": revision,
            "phase_commit_ownership": (), "intended_transition": "phase_complete",
            "predecessor_transition_id": None, "recovery_classification": "phase_complete_finalization",
        },
    )
    return enrich_legacy_completion(
        package,
        fields={
            "transition_type": "close_success", "lifecycle_state": "TERMINAL_SUCCESS",
            "report_id": phase_id, "report_digest": "b" * 64, "metadata_id": phase_id,
            "metadata_digest": "c" * 64, "snapshot_id": phase_id, "snapshot_digest": "c" * 64,
            "promotion_id": "d" * 64, "notification_ids": (f"{phase_id}:phase_complete",),
            "notification_state": "confirmed", "notification_suppressed": False, "receipt_id": "receipt-1",
        },
    )


def _finalize_generation(phase_id: str, transition_id: str, revision: str, migration_root: Path) -> str:
    package = _make_package(phase_id, transition_id, revision)
    legacy = derive_legacy(package)
    cltr = derive_cltr(package)
    comparison = compare(legacy, cltr)
    result = run_stage2_rehearsal(
        package=package, stage1_status="completed", stage1_evidence_digest="e" * 64,
        cltr_result=cltr, legacy_result=legacy, stage1_comparison_result=comparison,
        runtime_snapshot={"current_runtime_state": "Observed"}, migration_root=migration_root,
    )
    assert result.outcome.value == "successful_rehearsal", result
    return result.rehearsal_generation_id


@pytest.fixture()
def two_generations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", EPOCH)
    monkeypatch.setenv("PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED", "1")
    migration_root = tmp_path / ".pcae" / "cltr-migration"
    gen0 = _finalize_generation("999X.3-135u-gen0", TRANSITION_ID, "a" * 40, migration_root)
    gen1 = _finalize_generation("999X.3-135u-gen1", TRANSITION_ID, "b" * 40, migration_root)
    return migration_root, gen0, gen1


def _request(migration_root, target, reason="rollback test", phase_id="999X.3-135u-gen1"):
    return rb.build_rollback_request(
        phase_id=phase_id, transition_id=TRANSITION_ID, migration_epoch=EPOCH,
        authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=target, reason=reason,
        migration_root=migration_root,
    )


# ---------------------------------------------------------------------------
# Request model / identity
# ---------------------------------------------------------------------------


class TestRequestModelAndIdentity:
    def test_request_binds_expected_fields(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        assert request.transition_id == TRANSITION_ID
        assert request.migration_epoch == EPOCH
        assert request.authority_epoch == AUTHORITY_EPOCH
        assert request.current_rehearsal_generation_id == gen1
        assert request.target_rehearsal_generation_id == gen0
        assert request.expected_pointer_generation_id == gen1
        assert request.non_authority_disclosure["authoritative"] is False

    def test_identity_deterministic_same_inputs(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        r1 = _request(migration_root, gen0, reason="same reason")
        r2 = _request(migration_root, gen0, reason="same reason")
        assert r1.rollback_request_id == r2.rollback_request_id

    def test_identity_changes_with_target(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        r_to_gen0 = _request(migration_root, gen0)
        r_to_gen1 = _request(migration_root, gen1)
        assert r_to_gen0.rollback_request_id != r_to_gen1.rollback_request_id

    def test_identity_changes_with_reason(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        r1 = _request(migration_root, gen0, reason="reason A")
        r2 = _request(migration_root, gen0, reason="reason B")
        assert r1.rollback_request_id != r2.rollback_request_id

    def test_identity_not_random_or_timestamp_derived(self, two_generations):
        import time

        migration_root, gen0, gen1 = two_generations
        r1 = _request(migration_root, gen0)
        time.sleep(0.01)
        r2 = _request(migration_root, gen0)
        assert r1.rollback_request_id == r2.rollback_request_id

    def test_identity_stable_across_fresh_subprocess(self, two_generations):
        import subprocess
        import sys

        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        script = f"""
import sys
sys.path.insert(0, {str(Path(__file__).resolve().parents[1] / "src")!r})
from pcae.cltr.migration.rehearsal.identity import compute_rollback_request_id
print(compute_rollback_request_id(
    phase_id={request.phase_id!r}, transition_id={request.transition_id!r},
    migration_epoch={request.migration_epoch!r}, authority_epoch={request.authority_epoch!r},
    source_rehearsal_generation_id={request.current_rehearsal_generation_id!r},
    target_rehearsal_generation_id={request.target_rehearsal_generation_id!r},
    reason={request.reason!r},
))
"""
        out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
        assert out.stdout.strip() == request.rollback_request_id


# ---------------------------------------------------------------------------
# Target validation
# ---------------------------------------------------------------------------


class TestTargetValidation:
    def test_rejects_nonexistent_target(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, "does-not-exist")
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.REJECTED

    def test_rejects_quarantined_target(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        qdir = quarantine_dir(migration_root, EPOCH, TRANSITION_ID, gen0)
        qdir.mkdir(parents=True, exist_ok=True)
        (qdir / "quarantine_record.json").write_text("{}", encoding="utf-8")
        request = _request(migration_root, gen0)
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.REJECTED
        assert any("quarantine" in lim for lim in result.limitations)

    def test_rejects_digest_tampered_target(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        artifact_path = generations_dir(migration_root, EPOCH, TRANSITION_ID, gen0) / "cltr_record.json"
        payload = read_json(artifact_path)
        payload["tampered"] = True
        artifact_path.write_text(__import__("json").dumps(payload), encoding="utf-8")
        request = _request(migration_root, gen0)
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.REJECTED
        assert any("digest mismatch" in lim for lim in result.limitations)

    def test_rejects_wrong_epoch_target(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        request = dataclasses.replace(request, migration_epoch="some-other-epoch")
        with pytest.raises(rb.RollbackRejectedError):
            rb.validate_rollback_target(migration_root=migration_root, request=request)

    def test_no_op_retain_when_target_is_current(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen1)  # gen1 is already current
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.VERIFIED
        pointer = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer["rehearsal_generation_id"] == gen1


# ---------------------------------------------------------------------------
# Atomic pointer rollback / readback / immutable history
# ---------------------------------------------------------------------------


class TestAtomicRollback:
    def test_successful_rollback_moves_pointer(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.PUBLISHED
        pointer = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer["rehearsal_generation_id"] == gen0

    def test_both_generations_remain_after_rollback(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root)
        assert (generations_dir(migration_root, EPOCH, TRANSITION_ID, gen0) / "manifest.json").exists()
        assert (generations_dir(migration_root, EPOCH, TRANSITION_ID, gen1) / "manifest.json").exists()

    def test_generation_bytes_unchanged_by_rollback(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        gen1_manifest_before = read_json(generations_dir(migration_root, EPOCH, TRANSITION_ID, gen1) / "manifest.json")
        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root)
        gen1_manifest_after = read_json(generations_dir(migration_root, EPOCH, TRANSITION_ID, gen1) / "manifest.json")
        assert gen1_manifest_before == gen1_manifest_after

    def test_evidence_persisted_and_binds_source_and_target(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root)
        records = rb.list_rollback_evidence(migration_root, EPOCH, TRANSITION_ID)
        published = [r for r in records if r["outcome"] == "rollback_published"]
        assert len(published) == 1
        record = published[0]
        assert record["source_rehearsal_generation_id"] == gen1
        assert record["target_rehearsal_generation_id"] == gen0
        assert record["non_authority_disclosure"]["authoritative"] is False


# ---------------------------------------------------------------------------
# Idempotency and conflicting replay
# ---------------------------------------------------------------------------


class TestIdempotencyAndConflict:
    def test_identical_replay_after_success_is_idempotent(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root)
        pointer_before = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.IDEMPOTENT_REPLAY
        pointer_after = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer_before == pointer_after

    def test_idempotent_replay_does_not_duplicate_evidence(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root)
        before_count = len(rb.list_rollback_evidence(migration_root, EPOCH, TRANSITION_ID))
        rb.execute_rollback(request=request, migration_root=migration_root)
        after_count = len(rb.list_rollback_evidence(migration_root, EPOCH, TRANSITION_ID))
        assert before_count == after_count

    def test_same_id_different_target_is_conflict(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root)
        forged = dataclasses.replace(request, target_rehearsal_generation_id=gen1)
        result = rb.execute_rollback(request=forged, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.CONFLICT
        pointer = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer["rehearsal_generation_id"] == gen0  # unchanged by the conflict

    def test_conflicting_replay_never_becomes_current_and_is_auditable(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root)
        forged = dataclasses.replace(request, reason="a forged different reason")
        rb.execute_rollback(request=forged, migration_root=migration_root)
        from pcae.cltr.migration.rehearsal.persistence import rollback_conflicts_dir

        conflicts = list(rollback_conflicts_dir(migration_root, EPOCH, TRANSITION_ID).glob("*.json"))
        assert len(conflicts) == 1

    def test_stale_pointer_expectation_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        stale_request = _request(migration_root, gen0)  # expects live pointer == gen1
        other_request = _request(migration_root, gen0, reason="a concurrent, different rollback")
        rb.execute_rollback(request=other_request, migration_root=migration_root)  # moves pointer to gen0
        result = rb.execute_rollback(request=stale_request, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.REJECTED
        assert any("stale current-pointer expectation" in lim for lim in result.limitations)


# ---------------------------------------------------------------------------
# Crash injection / recovery
# ---------------------------------------------------------------------------


class TestCrashInjection:
    @pytest.mark.parametrize(
        "step",
        [
            "load_current_pointer",
            "request_identity_conflict_check",
            "idempotency_check",
            "verify_current_generation",
            "validate_target",
            "write_intent_evidence",
            "before_pointer_replace",
        ],
    )
    def test_fault_before_pointer_replace_leaves_pointer_unchanged(self, two_generations, step):
        migration_root, gen0, gen1 = two_generations
        pointer_before = read_pointer(migration_root, EPOCH, TRANSITION_ID)

        def _boom(s: str) -> None:
            if s == step:
                raise RuntimeError(f"simulated crash at {step}")

        request = _request(migration_root, gen0)
        result = rb.execute_rollback(request=request, migration_root=migration_root, fault_injector=_boom)
        assert result.outcome == RollbackOutcome.RECOVERY_REQUIRED
        pointer_after = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer_after == pointer_before

    def test_fault_after_pointer_replace_records_published_pointer_intact(self, two_generations):
        migration_root, gen0, gen1 = two_generations

        def _boom(s: str) -> None:
            if s == "after_pointer_replace":
                raise RuntimeError("simulated crash after pointer replace")

        request = _request(migration_root, gen0)
        result = rb.execute_rollback(request=request, migration_root=migration_root, fault_injector=_boom)
        assert result.outcome == RollbackOutcome.RECOVERY_REQUIRED
        # The pointer replace itself already committed (135Q §23's os.replace
        # atomicity) even though the *coordinator* crashed afterward --
        # production is untouched either way, and the rehearsal pointer
        # reflects the real, already-durable outcome, not a rollback of it.
        pointer_after = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer_after["rehearsal_generation_id"] == gen0

    def test_recovery_after_crash_can_complete_via_replay(self, two_generations):
        migration_root, gen0, gen1 = two_generations

        def _boom(s: str) -> None:
            if s == "after_pointer_replace":
                raise RuntimeError("simulated crash after pointer replace")

        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root, fault_injector=_boom)
        # Recovery replay: same request, no fault injector this time.
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome in (RollbackOutcome.PUBLISHED, RollbackOutcome.IDEMPOTENT_REPLAY)
        pointer_after = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer_after["rehearsal_generation_id"] == gen0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCLI:
    def test_rollback_status_read_only(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        before = sorted(migration_root.rglob("*"))
        payload = rb.rollback_status("999X.3-135u-gen1")
        after = sorted(migration_root.rglob("*"))
        assert before == after
        assert payload["found"] is True
        targets = payload["transitions"][0]["rollback_targets"]
        assert {t["rehearsal_generation_id"] for t in targets} == {gen0, gen1}

    def test_rollback_cli_end_to_end(self, two_generations, capsys):
        migration_root, gen0, gen1 = two_generations
        import argparse

        from pcae.commands.cltr_migration import run_cltr_migration_rehearsal_rollback

        args = argparse.Namespace(phase_id="999X.3-135u-gen1", target_generation=gen0, reason=None, json=True)
        code = run_cltr_migration_rehearsal_rollback(args)
        assert code == 0
        pointer = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer["rehearsal_generation_id"] == gen0

    def test_rollback_cli_ambiguous_phase_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import argparse

        from pcae.commands.cltr_migration import run_cltr_migration_rehearsal_rollback

        args = argparse.Namespace(phase_id="no-such-phase", target_generation="whatever", reason=None, json=True)
        code = run_cltr_migration_rehearsal_rollback(args)
        assert code == 1

    def test_no_generic_repair_command_exists(self):
        import inspect

        from pcae.commands import cltr_migration as cli_mod

        source = inspect.getsource(cli_mod)
        assert "def run_cltr_migration_rehearsal_repair" not in source

    def test_status_and_reconcile_never_trigger_rollback(self):
        import inspect

        from pcae.cltr.migration.rehearsal import reconciliation, status

        assert "execute_rollback" not in inspect.getsource(status)
        assert "execute_rollback" not in inspect.getsource(reconciliation)


# ---------------------------------------------------------------------------
# Production, notification, marker, receipt isolation; no-execution
# ---------------------------------------------------------------------------


class TestIsolationAndNoExecution:
    def test_rollback_module_never_imports_telegram(self):
        import ast

        source_path = Path(__file__).resolve().parents[1] / "src" / "pcae" / "cltr" / "migration" / "rehearsal" / "rollback.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "telegram" not in node.module.lower()
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "telegram" not in alias.name.lower()

    def test_rollback_module_never_uses_subprocess_or_network(self):
        source_path = Path(__file__).resolve().parents[1] / "src" / "pcae" / "cltr" / "migration" / "rehearsal" / "rollback.py"
        source = source_path.read_text(encoding="utf-8")
        for forbidden in ("subprocess", "socket", "urllib", "requests"):
            assert forbidden not in source

    def test_rollback_never_touches_production_cltr_migration_evidence(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        stage1_dir = migration_root / "epochs" / EPOCH / "transitions"
        before = sorted(stage1_dir.rglob("*")) if stage1_dir.exists() else []
        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root)
        after = sorted(stage1_dir.rglob("*")) if stage1_dir.exists() else []
        assert before == after

    def test_rollback_never_creates_pcae_phase_reports(self, two_generations, tmp_path):
        migration_root, gen0, gen1 = two_generations
        reports_dir = tmp_path / ".pcae" / "phase-reports"
        request = _request(migration_root, gen0)
        rb.execute_rollback(request=request, migration_root=migration_root)
        assert not reports_dir.exists()

    def test_runtime_remains_observed_and_execution_unavailable(self):
        from pcae.core.runtime_introspection import (
            CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
            CURRENT_RUNTIME_STATE,
            EXECUTION_AVAILABILITY,
        )

        assert CURRENT_RUNTIME_STATE == "Observed"
        assert CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
        assert EXECUTION_AVAILABILITY == "unavailable"


# ---------------------------------------------------------------------------
# Containment / symlink attacks
# ---------------------------------------------------------------------------


class TestContainment:
    def test_traversal_target_generation_id_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        with pytest.raises(rb.RollbackRejectedError, match="unsafe target generation id"):
            _request(migration_root, "../../etc/passwd")

    def test_absolute_path_target_generation_id_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        with pytest.raises(rb.RollbackRejectedError, match="unsafe target generation id"):
            _request(migration_root, "/etc/passwd")

    def test_symlinked_generation_directory_rejected(self, two_generations, tmp_path):
        migration_root, gen0, gen1 = two_generations
        outside = tmp_path / "outside-generation"
        outside.mkdir()
        gen_dir = generations_dir(migration_root, EPOCH, TRANSITION_ID, gen0)
        real_gen_dir = gen_dir.parent / f"{gen0}-real"
        gen_dir.rename(real_gen_dir)
        gen_dir.symlink_to(real_gen_dir)
        request = _request(migration_root, gen0)
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.REJECTED
        assert any("symlink" in lim for lim in result.limitations)

    def test_symlinked_artifact_inside_target_rejected(self, two_generations, tmp_path):
        migration_root, gen0, gen1 = two_generations
        gen_dir = generations_dir(migration_root, EPOCH, TRANSITION_ID, gen0)
        outside_file = tmp_path / "outside-artifact.json"
        outside_file.write_text("{}", encoding="utf-8")
        artifact_path = gen_dir / "cltr_record.json"
        artifact_path.unlink()
        artifact_path.symlink_to(outside_file)
        request = _request(migration_root, gen0)
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome == RollbackOutcome.REJECTED
        assert any("symlink" in lim for lim in result.limitations)
