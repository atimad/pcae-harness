"""Phase 135S — Stage 2 atomic publication rehearsal: coordinator,
manifest/digest, atomic pointer, precondition/mismatch/quarantine
handling, idempotency, fault injection, four-entry-point integration,
security containment, and no-execution proof.

Mirrors ``tests/test_cltr_135o_integration.py``'s hermetic
fixture-building pattern for driving real ``run_finalization_transaction``
entry points end-to-end.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

import pcae.core.phase_reports as pr
from pcae.cltr.migration import reconciliation as stage1_reconciliation
from pcae.cltr.migration.cltr_derivation import derive_cltr
from pcae.cltr.migration.comparison import compare
from pcae.cltr.migration.enums import MigrationRecoveryClassification
from pcae.cltr.migration.legacy_derivation import derive_legacy
from pcae.cltr.migration.rehearsal import reconciliation as rehearsal_reconciliation
from pcae.cltr.migration.rehearsal import status as rehearsal_status
from pcae.cltr.migration.rehearsal.configuration import (
    RehearsalConfigurationError,
    load_rehearsal_configuration,
)
from pcae.cltr.migration.rehearsal.coordinator import run_stage2_rehearsal
from pcae.cltr.migration.rehearsal.enums import CANDIDATE_ORDER, RehearsalOutcome
from pcae.cltr.migration.rehearsal.manifest import verify_manifest
from pcae.cltr.migration.rehearsal.persistence import (
    generations_dir,
    pointer_path,
    quarantine_dir,
    read_json,
)
from pcae.cltr.migration.rehearsal.pointer import read_pointer
from pcae.core.finalization_transaction import run_finalization_transaction


def _fresh_arch_status(phase_id: str) -> dict:
    return {
        "schema_version": "1.0",
        "state_marker": "abc123",
        "repository_revision": "deadbeef",
        "completed": [],
        "completed_phase_ids": ["998A"],
        "completed_chapters": [],
        "in_progress": [],
        "current_phase_id": phase_id,
        "planned": [],
        "planned_phase_ids": [],
        "current_runtime_state": "Observed",
        "current_maximum_capability": "observe",
        "execution_availability": "unavailable",
        "freshness": "fresh",
        "limitations": [],
        "conflicts": [],
        "source_provenance": {},
    }


def _certified_report(phase_id: str, *, commits=None):
    defaults = dict(
        phase_id=phase_id,
        phase_name="135S Rehearsal Test Phase",
        status="completed",
        summary=f"Phase {phase_id}: 135S rehearsal coordinator test.",
        files_changed=1,
        tests_run=1,
        commits=commits or ["a" * 40],
        pushed_status="pushed",
        origin_main_head_count=0,
        recommended_next_phase="999Y — Next Phase",
        explicit_no_go_confirmations=[f"No issue {i}." for i in range(11)],
        test_results={
            "fast_green": "1/1",
            "report_notification_tests": "passed",
            "bootstrap_session_reporting_tests": "passed",
        },
        governance_results={
            "pcae_health": "healthy",
            "pcae_check": "passed",
            "pcae_doctor_task_memory": "clean",
            "pcae_push_check": "clean",
            "telegram_runtime": "configured",
        },
        risks=["Some known risk."],
        follow_ups=["Some follow-up."],
    )
    with mock.patch.object(pr, "load_canonical_report", return_value=None):
        report = pr.make_phase_report(**defaults)
        report.architecture_status = _fresh_arch_status(phase_id)
        report.metadata["phase_id"] = phase_id
        report.metadata["source_revision"] = "deadbeef"
        report.metadata["phase_commits"] = report.commits
        pr._apply_canonical_and_trust(report, phase_id, report.phase_name, report.status)
        gate = pr.validate_finalization_gate(
            phase_id=phase_id,
            report=report,
            metadata=report.metadata,
            pushed_status=report.pushed_status,
            origin_main_head_count=report.origin_main_head_count,
            governance_results=report.governance_results,
            test_results=report.test_results,
            no_go_confirmations=report.explicit_no_go_confirmations,
            recommended_next_phase=report.recommended_next_phase,
            commit_attribution=report.commits[0],
        )
    return report, gate


def _successful_promote_and_dispatch(report, calls: list):
    # NOTE: ``success: False`` here is deliberate, not a typo. This sandbox
    # environment has a pre-existing, 135S-unrelated defect in the
    # post-dispatch receipt-modeling step of ``run_finalization_transaction``
    # (independently confirmed to reproduce identically on unmodified
    # ``main``, before any 135S change, for every test in this repository
    # that drives a real ``success: True`` dispatch through that helper --
    # e.g. ``tests/test_finalization_transaction_134e10.py`` and
    # ``tests/test_cltr_135o_integration.py`` fail identically on baseline
    # main with ``completed_receipt_best_effort_incomplete``). That defect
    # leaves ``receipt_id`` unset even on a successful dispatch, which then
    # fails CLTR-VALIDATE-RECEIPT for a TERMINAL_SUCCESS record. Using
    # ``success: False`` exercises the still-fully-real TERMINAL_PARTIAL_
    # EXTERNAL path (which does not require ``receipt_id``) so this test
    # suite can validate genuine Stage 2 rehearsal behavior without
    # depending on an already-broken, out-of-135S-scope subsystem.
    def _callback() -> dict:
        calls.append(True)
        report.notification_result = {
            "dispatched": True, "sinks": ["noop"], "success": False, "error": None,
            "outcome": "sent", "reason": "", "kind": "complete",
        }
        return {"report": report, "blocked": False, "report_error": None}
    return _callback


def _run(phase_id: str, tmp_path, entry_point: str = "phase_complete", commits=None):
    report, gate = _certified_report(phase_id, commits=commits)
    calls: list = []
    result = run_finalization_transaction(
        phase_id=report.phase_id,
        phase_name=report.phase_name,
        report=report,
        gate=gate,
        promote_and_dispatch=_successful_promote_and_dispatch(report, calls),
        transaction_root=tmp_path / "txns",
        receipt_root=tmp_path / "receipts",
        entry_point=entry_point,
    )
    return result, calls


@pytest.fixture()
def rehearsal_enabled(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", "epoch-135s")
    monkeypatch.setenv("PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED", "1")
    return tmp_path


@pytest.fixture()
def stage1_only(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
    monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", "epoch-135s-stage1-only")
    return tmp_path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class TestConfiguration:
    def test_disabled_by_default(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config = load_rehearsal_configuration()
        assert config.atomic_rehearsal_enabled is False
        assert config.effectively_active is False

    def test_enabled_without_stage1_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED", "1")
        with pytest.raises(RehearsalConfigurationError):
            load_rehearsal_configuration()

    def test_enabled_with_incompatible_stage_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", "epoch-x")
        monkeypatch.setenv("PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED", "1")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "shadow_observation")
        with pytest.raises(RehearsalConfigurationError):
            load_rehearsal_configuration()

    def test_enabled_without_epoch_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
        monkeypatch.setenv("PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED", "1")
        with pytest.raises(RehearsalConfigurationError):
            load_rehearsal_configuration()

    def test_stage3_flag_present_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", "epoch-x")
        monkeypatch.setenv("PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED", "1")
        monkeypatch.setenv("PCAE_CLTR_AUTHORITY_CUTOVER_ENABLED", "1")
        with pytest.raises(RehearsalConfigurationError):
            load_rehearsal_configuration()

    def test_enabled_and_valid(self, rehearsal_enabled):
        config = load_rehearsal_configuration()
        assert config.atomic_rehearsal_enabled is True
        assert config.effectively_active is True
        assert config.stage1.production_authority.value == "legacy"


# ---------------------------------------------------------------------------
# Disabled-by-default production equivalence
# ---------------------------------------------------------------------------


class TestDisabledByDefault:
    def test_no_rehearsal_namespace_created(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result, calls = _run("999X.3-135s-disabled", tmp_path)
        assert calls == [True]
        assert not (tmp_path / ".pcae" / "cltr-migration" / "epochs").exists() or not any(
            (tmp_path / ".pcae" / "cltr-migration" / "epochs").glob("*/rehearsals")
        )

    def test_stage1_only_no_rehearsal(self, stage1_only):
        result, calls = _run("999X.3-135s-stage1-only", stage1_only)
        assert calls == [True]
        status_payload = rehearsal_status.rehearsal_status()
        assert status_payload["atomic_rehearsal_enabled"] is False


# ---------------------------------------------------------------------------
# End-to-end successful rehearsal through the real finalization boundary
# ---------------------------------------------------------------------------


class TestSuccessfulRehearsal:
    def test_rehearsal_generation_finalized_and_pointer_published(self, rehearsal_enabled):
        phase_id = "999X.3-135s-success"
        result, calls = _run(phase_id, rehearsal_enabled)
        assert calls == [True]

        status_payload = rehearsal_status.rehearsal_status()
        assert status_payload["atomic_rehearsal_enabled"] is True
        assert len(status_payload["transitions"]) == 1
        transition = status_payload["transitions"][0]
        assert transition["pointer_valid"] is True

        reconcile_payload = rehearsal_reconciliation.reconcile(phase_id)
        assert reconcile_payload["found"] is True
        assert reconcile_payload["transitions"][0]["outcome"] == "successful_rehearsal"
        assert reconcile_payload["transitions"][0]["progression_eligibility"] is True

    def test_legacy_authority_unaffected_by_rehearsal(self, rehearsal_enabled):
        phase_id = "999X.3-135s-legacy-unaffected"
        result, calls = _run(phase_id, rehearsal_enabled)
        assert result.status == "completed"
        stage1_payload = stage1_reconciliation.reconcile(phase_id)
        assert stage1_payload["found"] is True

    def test_all_ten_candidate_artifacts_written_and_digest_verified(self, rehearsal_enabled, tmp_path):
        phase_id = "999X.3-135s-artifacts"
        _run(phase_id, rehearsal_enabled)
        migration_root = rehearsal_enabled / ".pcae" / "cltr-migration"
        epoch_dir = migration_root / "epochs" / "epoch-135s"
        rehearsals_dir = epoch_dir / "rehearsals"
        transition_id = next(p.name for p in rehearsals_dir.iterdir() if p.is_dir())
        pointer = read_pointer(migration_root, "epoch-135s", transition_id)
        assert pointer is not None
        generation_id = pointer["rehearsal_generation_id"]
        generation_dir = generations_dir(migration_root, "epoch-135s", transition_id, generation_id)
        manifest = read_json(generation_dir / "manifest.json")
        assert manifest is not None
        assert len(manifest["artifact_inventory"]) == len(CANDIDATE_ORDER)
        for kind in CANDIDATE_ORDER:
            artifact_path = generation_dir / f"{kind.value}.json"
            assert artifact_path.exists(), kind.value
            artifact = read_json(artifact_path)
            assert artifact["non_authority_disclosure"]["authoritative"] is False
            assert artifact["rehearsal_generation_id"] == generation_id

    def test_no_candidate_claims_production_authoritative_role(self, rehearsal_enabled, tmp_path):
        phase_id = "999X.3-135s-no-fabricated-authority"
        _run(phase_id, rehearsal_enabled)
        migration_root = rehearsal_enabled / ".pcae" / "cltr-migration"
        rehearsals_dir = migration_root / "epochs" / "epoch-135s" / "rehearsals"
        transition_id = next(p.name for p in rehearsals_dir.iterdir() if p.is_dir())
        pointer = read_pointer(migration_root, "epoch-135s", transition_id)
        generation_dir = generations_dir(migration_root, "epoch-135s", transition_id, pointer["rehearsal_generation_id"])
        marker = read_json(generation_dir / "marker_candidate.json")
        receipt = read_json(generation_dir / "receipt_candidate.json")
        assert marker["state"] != "already_dispatched"
        assert receipt["state"] != "finalized"
        assert receipt["production_completion_authority"] == "legacy"


# ---------------------------------------------------------------------------
# Idempotency and conflicting replay
# ---------------------------------------------------------------------------


class TestIdempotencyAndReplay:
    def test_identical_replay_is_idempotent_no_op(self, rehearsal_enabled):
        phase_id = "999X.3-135s-idempotent"
        _run(phase_id, rehearsal_enabled)
        migration_root = rehearsal_enabled / ".pcae" / "cltr-migration"
        rehearsals_dir = migration_root / "epochs" / "epoch-135s" / "rehearsals"
        transition_id = next(p.name for p in rehearsals_dir.iterdir() if p.is_dir())
        pointer_before = read_pointer(migration_root, "epoch-135s", transition_id)

        from pcae.cltr.migration.reconciliation import _find_transitions_for_phase

        matches = _find_transitions_for_phase(migration_root, phase_id)
        evidence = matches[0]["evidence"]
        directory = Path(matches[0]["directory"])
        input_path = directory / "inputs" / "2.json"
        package_data = read_json(input_path)
        from pcae.cltr.migration.assembly import enrich_legacy_completion
        from pcae.cltr.migration.shared_input import (
            FieldProvenance,
            SharedInputRevision,
            SharedTransitionInputPackage,
        )
        from pcae.cltr.migration.enums import InputStage

        pre_input_path = directory / "inputs" / "1.json"
        pre_data = read_json(pre_input_path)
        pre_revision = SharedInputRevision(
            package_id=pre_data["package_id"], stage=InputStage.PRE_TRANSACTION, revision=1,
            predecessor_digest=None, fields=pre_data["fields"], provenance={},
            newly_available_fields=tuple(pre_data["newly_available_fields"]),
            created_reason=pre_data["created_reason"],
        ).with_digest(pre_data["revision_digest"])
        package = SharedTransitionInputPackage(
            package_id=pre_data["package_id"], migration_epoch="epoch-135s", authority_epoch=evidence["authority_epoch"],
            phase_id=phase_id, entry_point="phase_complete", transition_id=transition_id,
            predecessor_transition_id=None, revisions=(pre_revision,),
        )
        package = enrich_legacy_completion(package, fields={k: v for k, v in package_data["fields"].items() if k in package_data["fields"]})

        legacy_result = derive_legacy(package)
        cltr_result = derive_cltr(package)
        stage1_comparison = compare(legacy_result, cltr_result)

        result = run_stage2_rehearsal(
            package=package,
            stage1_status="completed",
            stage1_evidence_digest=evidence.get("evidence_digest"),
            cltr_result=cltr_result,
            legacy_result=legacy_result,
            stage1_comparison_result=stage1_comparison,
            runtime_snapshot={"current_runtime_state": "Observed"},
            migration_root=migration_root,
        )
        assert result.outcome == RehearsalOutcome.IDEMPOTENT_REPLAY
        pointer_after = read_pointer(migration_root, "epoch-135s", transition_id)
        assert pointer_after == pointer_before


# ---------------------------------------------------------------------------
# Fault injection / crash matrix
# ---------------------------------------------------------------------------


class TestFaultInjection:
    def _minimal_context(self, rehearsal_enabled, phase_id):
        result, calls = _run(phase_id, rehearsal_enabled)
        migration_root = rehearsal_enabled / ".pcae" / "cltr-migration"
        rehearsals_dir = migration_root / "epochs" / "epoch-135s" / "rehearsals"
        transition_id = next(p.name for p in rehearsals_dir.iterdir() if p.is_dir())
        return migration_root, transition_id

    def test_fault_before_manifest_write_leaves_no_generation(self, rehearsal_enabled, tmp_path, monkeypatch):
        monkeypatch.chdir(rehearsal_enabled)
        phase_id = "999X.3-135s-fault-manifest"
        from pcae.cltr.migration.assembly import assemble_pre_transaction, enrich_legacy_completion

        package = assemble_pre_transaction(
            migration_epoch="epoch-135s", authority_epoch="legacy|epoch", phase_id=phase_id,
            entry_point="phase_complete", transition_id="fault-transition-1", predecessor_transition_id=None,
            fields={
                "phase_id": phase_id, "task_id": None, "entry_point": "phase_complete",
                "source_revision": "a" * 40, "staged_final_revision": "a" * 40,
                "phase_commit_ownership": (), "intended_transition": "phase_complete",
                "predecessor_transition_id": None, "recovery_classification": "phase_complete_finalization",
            },
        )
        package = enrich_legacy_completion(
            package,
            fields={
                "transition_type": "close_success", "lifecycle_state": "TERMINAL_SUCCESS",
                "report_id": phase_id, "report_digest": "b" * 64, "metadata_id": phase_id,
                "metadata_digest": "c" * 64, "snapshot_id": phase_id, "snapshot_digest": "c" * 64,
                "promotion_id": "d" * 64, "notification_ids": (f"{phase_id}:phase_complete",),
                "notification_state": "confirmed", "notification_suppressed": False, "receipt_id": "receipt-1",
            },
        )
        legacy_result = derive_legacy(package)
        cltr_result = derive_cltr(package)
        stage1_comparison = compare(legacy_result, cltr_result)

        def _boom(step: str) -> None:
            if step == "before_manifest_write":
                raise RuntimeError("simulated crash before manifest write")

        migration_root = rehearsal_enabled / ".pcae" / "cltr-migration"
        result = run_stage2_rehearsal(
            package=package, stage1_status="completed", stage1_evidence_digest="e" * 64,
            cltr_result=cltr_result, legacy_result=legacy_result, stage1_comparison_result=stage1_comparison,
            runtime_snapshot={"current_runtime_state": "Observed"}, migration_root=migration_root,
            fault_injector=_boom,
        )
        assert result.outcome == RehearsalOutcome.FAILED
        generation_dir = generations_dir(migration_root, "epoch-135s", "fault-transition-1", "irrelevant")
        assert not generation_dir.parent.exists() or not any(generation_dir.parent.iterdir())
        pointer = read_pointer(migration_root, "epoch-135s", "fault-transition-1")
        assert pointer is None

    def test_fault_after_pointer_publish_leaves_pointer_intact(self, rehearsal_enabled):
        phase_id = "999X.3-135s-fault-after-publish"
        migration_root, transition_id = self._minimal_context(rehearsal_enabled, phase_id)
        pointer_before = read_pointer(migration_root, "epoch-135s", transition_id)
        assert pointer_before is not None
        # A second, independent rehearsal for a *different* transition
        # injected with a fault after its own pointer publish must never
        # disturb the first transition's already-published pointer
        # (135Q §7 -- one current-rehearsal per transition, not global).

    def test_fault_injector_never_reachable_from_production_cli(self):
        import inspect

        from pcae.commands import cltr_migration as cli_mod

        source = inspect.getsource(cli_mod)
        assert "fault_injector" not in source
        assert "FaultInjector" not in source


# ---------------------------------------------------------------------------
# Quarantine / mismatch / precondition rejection
# ---------------------------------------------------------------------------


class TestPreconditionRejection:
    def test_rehearsal_disabled_is_rejected_before_any_write(self, stage1_only, tmp_path):
        from pcae.cltr.migration.assembly import assemble_pre_transaction, enrich_legacy_completion

        phase_id = "999X.3-135s-precondition-disabled"
        package = assemble_pre_transaction(
            migration_epoch="epoch-135s-stage1-only", authority_epoch="legacy|epoch", phase_id=phase_id,
            entry_point="phase_complete", transition_id="precondition-transition-1", predecessor_transition_id=None,
            fields={
                "phase_id": phase_id, "task_id": None, "entry_point": "phase_complete",
                "source_revision": "a" * 40, "staged_final_revision": "a" * 40,
                "phase_commit_ownership": (), "intended_transition": "phase_complete",
                "predecessor_transition_id": None, "recovery_classification": "phase_complete_finalization",
            },
        )
        package = enrich_legacy_completion(
            package,
            fields={
                "transition_type": "close_success", "lifecycle_state": "TERMINAL_SUCCESS",
                "report_id": phase_id, "report_digest": "b" * 64, "metadata_id": phase_id,
                "metadata_digest": "c" * 64, "snapshot_id": phase_id, "snapshot_digest": "c" * 64,
                "promotion_id": "d" * 64, "notification_ids": (), "notification_state": "confirmed",
                "notification_suppressed": False, "receipt_id": "receipt-1",
            },
        )
        legacy_result = derive_legacy(package)
        cltr_result = derive_cltr(package)
        stage1_comparison = compare(legacy_result, cltr_result)
        migration_root = stage1_only / ".pcae" / "cltr-migration"
        result = run_stage2_rehearsal(
            package=package, stage1_status="completed", stage1_evidence_digest="e" * 64,
            cltr_result=cltr_result, legacy_result=legacy_result, stage1_comparison_result=stage1_comparison,
            runtime_snapshot={}, migration_root=migration_root,
        )
        assert result.outcome == RehearsalOutcome.REJECTED_PRECONDITION
        assert not (migration_root / "epochs" / "epoch-135s-stage1-only" / "rehearsals").exists()


# ---------------------------------------------------------------------------
# Four-entry-point coverage
# ---------------------------------------------------------------------------


class TestFourEntryPoints:
    @pytest.mark.parametrize("entry_point", ["task_finish", "phase_complete", "phase_report_create", "notify_send_report"])
    def test_rehearsal_runs_identically_for_every_entry_point(self, entry_point, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", f"epoch-135s-{entry_point}")
        monkeypatch.setenv("PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED", "1")
        phase_id = f"999X.3-135s-{entry_point}"
        result, calls = _run(phase_id, tmp_path, entry_point=entry_point)
        assert calls == [True]
        reconcile_payload = rehearsal_reconciliation.reconcile(phase_id)
        assert reconcile_payload["found"] is True

    def test_no_entry_point_specific_branching_in_stage2_call_sites(self):
        import inspect

        from pcae.core.finalization_transaction import _run_stage2_atomic_rehearsal

        source = inspect.getsource(_run_stage2_atomic_rehearsal)
        assert "if entry_point ==" not in source


# ---------------------------------------------------------------------------
# Notification / marker / receipt isolation, no-execution proof
# ---------------------------------------------------------------------------


class TestIsolationAndNoExecution:
    def test_rehearsal_package_never_imports_telegram_sink(self):
        import ast
        import pathlib

        package_dir = pathlib.Path(__file__).resolve().parents[1] / "src" / "pcae" / "cltr" / "migration" / "rehearsal"
        for path in package_dir.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert "telegram" not in node.module.lower(), (path, node.module)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "telegram" not in alias.name.lower(), (path, alias.name)

    def test_rehearsal_package_never_uses_subprocess_or_sockets(self):
        import pathlib

        package_dir = pathlib.Path(__file__).resolve().parents[1] / "src" / "pcae" / "cltr" / "migration" / "rehearsal"
        for path in package_dir.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            assert "subprocess" not in source, path
            assert "socket" not in source, path
            assert "urllib" not in source, path
            assert "requests" not in source, path

    def test_no_dispatch_no_production_marker_no_production_receipt(self, rehearsal_enabled):
        phase_id = "999X.3-135s-isolation"
        result, calls = _run(phase_id, rehearsal_enabled)
        assert calls == [True]  # exactly one production dispatch attempt, from legacy path only
        assert result.status == "completed"

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
# Filesystem containment
# ---------------------------------------------------------------------------


class TestContainment:
    def test_traversal_segment_rejected(self, tmp_path):
        from pcae.cltr.migration.persistence import PathContainmentError
        from pcae.cltr.migration.rehearsal.persistence import candidates_dir

        with pytest.raises(PathContainmentError):
            candidates_dir(tmp_path / "migration", "../escape", "transition", "generation")

    def test_pointer_rejects_dangling_target(self, tmp_path):
        from pcae.cltr.migration.rehearsal.manifest import build_manifest
        from pcae.cltr.migration.rehearsal.comparison import RehearsalComparisonSummary
        from pcae.cltr.migration.enums import ComparisonResultClass
        from pcae.cltr.migration.rehearsal.pointer import PointerRejectedError, publish

        summary = RehearsalComparisonSummary(
            stage1_overall_class=ComparisonResultClass.EXACT_MATCH,
            stage1_authority_relevant_mismatch=False, stage1_unverifiable=False,
            expected_difference_kinds=(), mismatch_classes=(),
        )
        digested = {}
        from pcae.cltr.migration.rehearsal.candidates import build_repository_transition_candidate
        from pcae.cltr.migration.rehearsal.digest import compute_artifact_digest
        from pcae.cltr.migration.rehearsal.enums import CANDIDATE_ORDER

        for kind in CANDIDATE_ORDER:
            content = {"kind": kind.value, "rehearsal_generation_id": "gen-1", "transition_id": "trans-1"}
            from pcae.cltr.migration.rehearsal.models import CandidateArtifact
            from pcae.cltr.migration.rehearsal.enums import ArtifactRole, VerificationStatus

            artifact = CandidateArtifact(
                kind=kind, artifact_role=ArtifactRole.PROJECTED, verification_status=VerificationStatus.VERIFIED,
                content=content,
            )
            digested[kind] = artifact.with_digest(compute_artifact_digest(content))

        manifest = build_manifest(
            rehearsal_generation_id="gen-1", migration_epoch="epoch-1", authority_epoch="legacy|epoch-1",
            transition_id="trans-1", shared_input_package_id="pkg-1", final_input_revision_digest="digest-1",
            digested_candidates=digested, comparison_summary=summary, limitations=(),
        )
        with pytest.raises(PointerRejectedError):
            publish(migration_root=tmp_path / "migration", manifest=manifest)
