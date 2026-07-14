"""Phase 135U — independent adversarial verification of the rollback-
rehearsal implementation.

Deliberately separate from ``tests/test_cltr_rehearsal_rollback.py``
(the primary implementation test module). Re-derives expectations from
135Q §33/§36/§37/§38's frozen contract text and 135U's own phase brief
rather than importing implementation constants as expected truth --
e.g. this module hardcodes its own copies of "must never happen"
strings and re-walks the source rather than asserting against
``rollback.py``'s own internal helper return values.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from pcae.cltr.migration.assembly import assemble_pre_transaction, enrich_legacy_completion
from pcae.cltr.migration.cltr_derivation import derive_cltr
from pcae.cltr.migration.comparison import compare
from pcae.cltr.migration.legacy_derivation import derive_legacy
from pcae.cltr.migration.rehearsal import rollback as rb
from pcae.cltr.migration.rehearsal.coordinator import run_stage2_rehearsal
from pcae.cltr.migration.rehearsal.persistence import (
    generations_dir,
    quarantine_dir,
    read_json,
)
from pcae.cltr.migration.rehearsal.pointer import read_pointer

TRANSITION_ID = "135u-verify-transition"
EPOCH = "epoch-135u-verify"
AUTHORITY_EPOCH = "legacy|epoch-135u-verify"


def _make_package(phase_id: str, transition_id: str, revision: str, epoch: str = EPOCH):
    package = assemble_pre_transaction(
        migration_epoch=epoch,
        authority_epoch=f"legacy|{epoch}",
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


def _finalize(phase_id, transition_id, revision, migration_root, epoch=EPOCH):
    package = _make_package(phase_id, transition_id, revision, epoch=epoch)
    legacy = derive_legacy(package)
    cltr = derive_cltr(package)
    comparison = compare(legacy, cltr)
    result = run_stage2_rehearsal(
        package=package, stage1_status="completed", stage1_evidence_digest="e" * 64,
        cltr_result=cltr, legacy_result=legacy, stage1_comparison_result=comparison,
        runtime_snapshot={"current_runtime_state": "Observed"}, migration_root=migration_root,
    )
    assert result.outcome.value == "successful_rehearsal"
    return result.rehearsal_generation_id


@pytest.fixture()
def rollback_enabled(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", EPOCH)
    monkeypatch.setenv("PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED", "1")
    return tmp_path


@pytest.fixture()
def two_generations(rollback_enabled):
    migration_root = rollback_enabled / ".pcae" / "cltr-migration"
    gen0 = _finalize("999X.3-135u-verify-gen0", TRANSITION_ID, "a" * 40, migration_root)
    gen1 = _finalize("999X.3-135u-verify-gen1", TRANSITION_ID, "b" * 40, migration_root)
    return migration_root, gen0, gen1


# ---------------------------------------------------------------------------
# 1. Deterministic identity -- re-derived independently
# ---------------------------------------------------------------------------


class TestIndependentIdentityDeterminism:
    def test_identity_is_pure_function_of_bound_fields(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        r1 = rb.build_rollback_request(
            phase_id="p1", transition_id=TRANSITION_ID, migration_epoch=EPOCH, authority_epoch=AUTHORITY_EPOCH,
            target_rehearsal_generation_id=gen0, reason="r", migration_root=migration_root,
        )
        r2 = rb.build_rollback_request(
            phase_id="p1", transition_id=TRANSITION_ID, migration_epoch=EPOCH, authority_epoch=AUTHORITY_EPOCH,
            target_rehearsal_generation_id=gen0, reason="r", migration_root=migration_root,
        )
        assert r1.rollback_request_id == r2.rollback_request_id

    @pytest.mark.parametrize(
        "field,value",
        [
            ("phase_id", "different-phase"),
            ("transition_id", "different-transition"),
            ("migration_epoch", "different-epoch"),
            ("authority_epoch", "legacy|different-epoch"),
            ("target_rehearsal_generation_id", "different-target"),
            ("reason", "different-reason"),
        ],
    )
    def test_identity_changes_when_any_bound_field_changes(self, two_generations, field, value):
        migration_root, gen0, gen1 = two_generations
        baseline = rb.build_rollback_request(
            phase_id="p1", transition_id=TRANSITION_ID, migration_epoch=EPOCH, authority_epoch=AUTHORITY_EPOCH,
            target_rehearsal_generation_id=gen0, reason="r", migration_root=migration_root,
        )
        mutated_kwargs = dict(
            phase_id="p1", transition_id=TRANSITION_ID, migration_epoch=EPOCH, authority_epoch=AUTHORITY_EPOCH,
            target_rehearsal_generation_id=gen0, reason="r",
        )
        mutated_kwargs[field] = value
        from pcae.cltr.migration.rehearsal.identity import compute_rollback_request_id

        mutated_id = compute_rollback_request_id(
            phase_id=mutated_kwargs["phase_id"], transition_id=mutated_kwargs["transition_id"],
            migration_epoch=mutated_kwargs["migration_epoch"], authority_epoch=mutated_kwargs["authority_epoch"],
            source_rehearsal_generation_id=baseline.current_rehearsal_generation_id,
            target_rehearsal_generation_id=mutated_kwargs["target_rehearsal_generation_id"],
            reason=mutated_kwargs["reason"],
        )
        assert mutated_id != baseline.rollback_request_id

    def test_no_uuid_or_wallclock_module_used_for_identity(self):
        source = (
            Path(__file__).resolve().parents[1] / "src" / "pcae" / "cltr" / "migration" / "rehearsal" / "identity.py"
        ).read_text(encoding="utf-8")
        assert "import uuid" not in source
        assert "time.time" not in source
        assert "datetime.now" not in source


# ---------------------------------------------------------------------------
# 2. Target validation re-derived from 135Q §36/§38 and the 135U brief's
#    "at minimum verify" list
# ---------------------------------------------------------------------------


class TestIndependentTargetValidation:
    def test_target_in_another_epoch_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        other_epoch_transition = "135u-verify-other-epoch-transition"
        other_gen = _finalize(
            "999X.3-135u-verify-other-epoch", other_epoch_transition, "c" * 40, migration_root, epoch="epoch-135u-other"
        )
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=other_gen, reason="cross-epoch attack",
            migration_root=migration_root,
        )
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome.value == "rollback_rejected"
        pointer = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer["rehearsal_generation_id"] == gen1

    def test_target_in_another_transition_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        other_transition = "135u-verify-other-transition"
        other_gen = _finalize("999X.3-135u-verify-other-transition", other_transition, "d" * 40, migration_root)
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=other_gen, reason="cross-transition attack",
            migration_root=migration_root,
        )
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome.value == "rollback_rejected"

    def test_target_in_candidates_directory_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        from pcae.cltr.migration.rehearsal.persistence import candidates_dir

        fake_id = "fake-candidate-generation"
        cdir = candidates_dir(migration_root, EPOCH, TRANSITION_ID, fake_id)
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "manifest.json").write_text(json.dumps({"generation_digest": "x"}), encoding="utf-8")
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=fake_id, reason="candidate-as-target attack",
            migration_root=migration_root,
        )
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome.value == "rollback_rejected"
        pointer = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer["rehearsal_generation_id"] == gen1

    def test_target_in_failures_directory_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        from pcae.cltr.migration.rehearsal.persistence import failures_dir

        fdir = failures_dir(migration_root, EPOCH, TRANSITION_ID)
        fdir.mkdir(parents=True, exist_ok=True)
        fake_id = "fake-failure-generation"
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=fake_id, reason="failure-as-target attack",
            migration_root=migration_root,
        )
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome.value == "rollback_rejected"

    def test_target_referencing_production_storage_rejected(self, two_generations, tmp_path):
        migration_root, gen0, gen1 = two_generations
        production_dir = tmp_path / ".pcae" / "phase-reports"
        production_dir.mkdir(parents=True, exist_ok=True)
        (production_dir / "canonical.json").write_text("{}", encoding="utf-8")
        # A target id cannot itself point outside the rehearsal namespace
        # (path segments are always joined under generations_dir(), never
        # taken as a raw filesystem path) -- verify no traversal segment
        # can reach the production directory.
        traversal_attempts = [
            "../../../phase-reports/canonical",
            "..%2Fphase-reports",
        ]
        for attempt in traversal_attempts:
            with pytest.raises(rb.RollbackRejectedError):
                rb.build_rollback_request(
                    phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
                    authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=attempt, reason="prod escape attempt",
                    migration_root=migration_root,
                )

    def test_unsupported_schema_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        gen_dir = generations_dir(migration_root, EPOCH, TRANSITION_ID, gen0)
        manifest = read_json(gen_dir / "manifest.json")
        manifest["manifest_schema_version"] = "99.0.0"
        (gen_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=gen0, reason="schema attack",
            migration_root=migration_root,
        )
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome.value == "rollback_rejected"

    def test_wrong_authority_epoch_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch="cltr|not-legacy", target_rehearsal_generation_id=gen0, reason="authority escalation attempt",
            migration_root=migration_root,
        )
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome.value == "rollback_rejected"
        assert any("legacy" in lim for lim in result.limitations)

    def test_target_digest_substitution_rejected(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        gen_dir = generations_dir(migration_root, EPOCH, TRANSITION_ID, gen0)
        manifest = read_json(gen_dir / "manifest.json")
        manifest["generation_digest"] = "0" * 64
        (gen_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=gen0, reason="digest substitution attack",
            migration_root=migration_root,
        )
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome.value == "rollback_rejected"


# ---------------------------------------------------------------------------
# 3. Split-brain / substitution attacks
# ---------------------------------------------------------------------------


class TestIndependentSplitBrainAttacks:
    def test_pointer_file_substitution_after_rollback_detected_on_readback(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=gen0, reason="ordinary rollback",
            migration_root=migration_root,
        )
        result = rb.execute_rollback(request=request, migration_root=migration_root)
        assert result.outcome.value == "rollback_published"

        from pcae.cltr.migration.rehearsal.persistence import pointer_path

        p_path = pointer_path(migration_root, EPOCH, TRANSITION_ID)
        forged = json.loads(p_path.read_text(encoding="utf-8"))
        forged["rehearsal_generation_id"] = gen1
        p_path.write_text(json.dumps(forged), encoding="utf-8")

        pointer = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer["rehearsal_generation_id"] == gen1  # confirms substitution is externally observable
        # rollback-status must report the substituted (current, on-disk)
        # value -- never a cached/trusted stale value -- proving status
        # always re-reads rather than trusting its own prior evidence.
        status = rb.rollback_status("999X.3-135u-verify-gen1", migration_root=migration_root)
        assert status["transitions"][0]["current_rehearsal_generation_id"] == gen1


# ---------------------------------------------------------------------------
# 4. Progression eligibility re-derivation
# ---------------------------------------------------------------------------


class TestIndependentProgressionEligibility:
    def test_rollback_never_sets_progression_eligibility_true_via_side_channel(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=gen0, reason="progression check",
            migration_root=migration_root,
        )
        rb.execute_rollback(request=request, migration_root=migration_root)
        # 135Q §36's "invalidate progression for the generation rolled back
        # from" -- the rolled-back-from generation's own forward-rehearsal
        # evidence (persisted at finalization time) is never mutated by
        # rollback; rollback evidence never claims progression_eligibility
        # for a rehearsal outcome, which has no such field at all (only
        # forward-rehearsal evidence does), independently confirmed here.
        records = rb.list_rollback_evidence(migration_root, EPOCH, TRANSITION_ID)
        published = [r for r in records if r["outcome"] == "rollback_published"]
        assert published
        assert "progression_eligibility" not in published[0]


# ---------------------------------------------------------------------------
# 5. Production / notification / marker / receipt isolation -- re-derived
# ---------------------------------------------------------------------------


class TestIndependentProductionIsolation:
    def test_no_production_namespace_exists_before_or_after_rollback(self, two_generations, tmp_path):
        migration_root, gen0, gen1 = two_generations
        pcae_dir = tmp_path / ".pcae"
        production_paths = [
            pcae_dir / "phase-reports",
            pcae_dir / "phase-completion-metadata.json",
            pcae_dir / "architecture-status.json",
            pcae_dir / "checkpoints",
            pcae_dir / "notifications",
            pcae_dir / "markers",
            pcae_dir / "receipts",
        ]
        before = {p: (p.exists(), sorted(p.rglob("*")) if p.is_dir() else None) for p in production_paths}
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=gen0, reason="isolation check",
            migration_root=migration_root,
        )
        rb.execute_rollback(request=request, migration_root=migration_root)
        after = {p: (p.exists(), sorted(p.rglob("*")) if p.is_dir() else None) for p in production_paths}
        assert before == after

    def test_rollback_source_never_calls_finalization_transaction(self):
        source = (
            Path(__file__).resolve().parents[1] / "src" / "pcae" / "cltr" / "migration" / "rehearsal" / "rollback.py"
        ).read_text(encoding="utf-8")
        assert "finalization_transaction" not in source
        assert "run_finalization_transaction" not in source

    def test_rollback_source_never_references_telegram_or_network_terms(self):
        source = (
            Path(__file__).resolve().parents[1] / "src" / "pcae" / "cltr" / "migration" / "rehearsal" / "rollback.py"
        ).read_text(encoding="utf-8")
        for forbidden in ("telegram", "smtp", "http://", "https://"):
            assert forbidden not in source.lower()


# ---------------------------------------------------------------------------
# 6. Roll-forward -- explicit deferral re-derived
# ---------------------------------------------------------------------------


class TestIndependentRollForwardDeferral:
    def test_no_dedicated_roll_forward_function_exists(self):
        assert not hasattr(rb, "roll_forward")
        assert not hasattr(rb, "execute_roll_forward")

    def test_rolling_forward_again_requires_a_new_explicit_request(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        back = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=gen0, reason="roll back",
            migration_root=migration_root,
        )
        rb.execute_rollback(request=back, migration_root=migration_root)
        forward = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=gen1, reason="roll forward again",
            migration_root=migration_root,
        )
        assert forward.rollback_request_id != back.rollback_request_id
        result = rb.execute_rollback(request=forward, migration_root=migration_root)
        assert result.outcome.value == "rollback_published"
        pointer = read_pointer(migration_root, EPOCH, TRANSITION_ID)
        assert pointer["rehearsal_generation_id"] == gen1


# ---------------------------------------------------------------------------
# 7. No-execution / read-only status-reconcile re-verification
# ---------------------------------------------------------------------------


class TestIndependentNoExecutionAndReadOnly:
    def test_rollback_package_has_no_execution_primitives(self):
        rehearsal_dir = Path(__file__).resolve().parents[1] / "src" / "pcae" / "cltr" / "migration" / "rehearsal"
        for path in rehearsal_dir.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            for forbidden in ("subprocess", "os.system", "socket.socket", "importlib.import_module"):
                assert forbidden not in source, (path, forbidden)

    def test_reconcile_reflects_rollback_without_mutating(self, two_generations):
        migration_root, gen0, gen1 = two_generations
        request = rb.build_rollback_request(
            phase_id="999X.3-135u-verify-gen1", transition_id=TRANSITION_ID, migration_epoch=EPOCH,
            authority_epoch=AUTHORITY_EPOCH, target_rehearsal_generation_id=gen0, reason="reconcile check",
            migration_root=migration_root,
        )
        rb.execute_rollback(request=request, migration_root=migration_root)

        from pcae.cltr.migration.rehearsal import reconciliation

        before = sorted(migration_root.rglob("*"))
        payload = reconciliation.reconcile("999X.3-135u-verify-gen1", migration_root=migration_root)
        after = sorted(migration_root.rglob("*"))
        assert before == after
        transition = payload["transitions"][0]
        assert transition["rehearsal_generation_id"] == gen0
        assert len(transition["rollback_history"]) >= 1

    def test_runtime_capability_unchanged_by_rollback_module_import(self):
        import importlib

        import pcae.core.runtime_introspection as ri

        importlib.reload(ri)
        assert ri.CURRENT_RUNTIME_STATE == "Observed"
        assert ri.EXECUTION_AVAILABILITY == "unavailable"
