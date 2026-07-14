"""Phase 135P — independent adversarial verification of the 135O Stage 1
shared transition-input and dual-derivation implementation.

These tests are deliberately *not* written from the implementation's own
assumptions: each one targets a specific gap independently derived from
reading CLTR-001, CLTR-SCHEMA-001 v1.0.1, the 135M contract (as repaired
by 135N), and the actual production source -- not from the 135O report's
claims. Findings this file locks in behavior for are documented in
``docs/PHASE_135_SHARED_TRANSITION_INPUT_AND_DUAL_DERIVATION_INDEPENDENT_VERIFICATION.md``.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType

import pytest

from pcae.cltr.migration import (
    coordinator as coordinator_mod,
    evidence as evidence_mod,
    persistence as persistence_mod,
    reconciliation as reconciliation_mod,
    status as status_mod,
)
from pcae.cltr.migration.assembly import assemble_pre_transaction, enrich_legacy_completion
from pcae.cltr.migration.cltr_derivation import derive_cltr
from pcae.cltr.migration.comparison import _MISMATCH_CLASS_FOR_FIELD, compare
from pcae.cltr.migration.coordinator import capture_pre_transaction, complete
from pcae.cltr.migration.enums import ComparisonResultClass, MigrationRecoveryClassification
from pcae.cltr.migration.legacy_derivation import derive_legacy
from pcae.cltr.migration.persistence import write_atomic
from pcae.cltr.migration.transition_identity import resolve_transition_id
from pcae.core.finalization_transaction import _ENTRY_POINT_RECOVERY_CLASSIFICATION, _recovery_classification_for


# ---------------------------------------------------------------------------
# 1. Entry-point recovery-classification wiring (F-135P-1, NON-BLOCKING)
# ---------------------------------------------------------------------------
# All four production entry points (task.py, phase.py, phase_reports.py,
# notifications.py) call into the shared finalization boundary with a
# distinct ``entry_point`` string. ``_ENTRY_POINT_RECOVERY_CLASSIFICATION``
# only maps two of the four; the other two silently fall back to
# ``"ordinary_finalization"`` rather than their dedicated
# ``MigrationRecoveryClassification.REPORT_CREATE_RECOVERY`` /
# ``.MANUAL_RECOVERY`` values, which exist in enums.py but are never
# referenced from src/. This does not affect comparison (recovery_
# classification is deliberately excluded from cross-derivation
# comparison, comparison.py:50-60) or progression eligibility (neither
# ORDINARY nor the correct classes are in NON_PROGRESSABLE_RECOVERY_
# CLASSIFICATIONS) -- it is an evidence-truthfulness gap, not an
# authority or safety gap. This test locks in the *actual* (currently
# incorrect) behavior so any accidental further drift is caught, and
# documents the exact entry points affected.

_REAL_ENTRY_POINTS = {
    "task_finish": "task.py",
    "phase_complete": "phase.py",
    "phase_report_create": "phase_reports.py",
    "notify_send_report": "notifications.py",
}


class TestEntryPointRecoveryClassificationWiring:
    def test_all_four_real_entry_points_are_present_in_source(self):
        # Sanity: confirm the four entry-point strings this test targets
        # still match the real call sites (not stale/rediscovered names).
        import inspect

        import pcae.commands.notifications as notifications_mod
        import pcae.commands.phase as phase_mod
        import pcae.commands.phase_reports as phase_reports_mod
        import pcae.commands.task as task_mod

        assert 'entry_point="task_finish"' in inspect.getsource(task_mod)
        assert 'entry_point="phase_complete"' in inspect.getsource(phase_mod)
        assert 'entry_point="phase_report_create"' in inspect.getsource(phase_reports_mod)
        assert 'entry_point="notify_send_report"' in inspect.getsource(notifications_mod)

    def test_task_finish_and_phase_complete_map_correctly(self):
        assert _recovery_classification_for("task_finish") == MigrationRecoveryClassification.TASK_FINISH
        assert _recovery_classification_for("phase_complete") == MigrationRecoveryClassification.PHASE_COMPLETE

    def test_report_create_and_manual_recovery_are_correctly_mapped(self):
        # F-135P-1 repair (Phase 135S): these now resolve to their
        # dedicated classifications (enums.py:146,148) instead of
        # silently collapsing to ORDINARY -- required so Stage 2's
        # four-entry-point/recovery-path guarantees (135Q §36/§39) rest
        # on a truthful classification field.
        assert (
            _recovery_classification_for("phase_report_create")
            == MigrationRecoveryClassification.REPORT_CREATE_RECOVERY
        )
        assert (
            _recovery_classification_for("notify_send_report")
            == MigrationRecoveryClassification.MANUAL_RECOVERY
        )
        assert "phase_report_create" in _ENTRY_POINT_RECOVERY_CLASSIFICATION
        assert "notify_send_report" in _ENTRY_POINT_RECOVERY_CLASSIFICATION

    def test_misclassification_does_not_leak_into_comparison_or_eligibility(self):
        # Prove the gap is evidence-only: recovery_classification is never
        # compared cross-derivation (so no false match/mismatch can result)
        # and ordinary_finalization is not in the non-progressable set (so
        # no false eligibility flip results either).
        from pcae.cltr.migration.comparison import _CLTR_FIELD_ACCESSORS
        from pcae.cltr.migration.enums import NON_PROGRESSABLE_RECOVERY_CLASSIFICATIONS

        assert "recovery_classification" not in _CLTR_FIELD_ACCESSORS
        assert MigrationRecoveryClassification.ORDINARY not in NON_PROGRESSABLE_RECOVERY_CLASSIFICATIONS
        assert MigrationRecoveryClassification.REPORT_CREATE_RECOVERY not in NON_PROGRESSABLE_RECOVERY_CLASSIFICATIONS
        assert MigrationRecoveryClassification.MANUAL_RECOVERY not in NON_PROGRESSABLE_RECOVERY_CLASSIFICATIONS


# ---------------------------------------------------------------------------
# 2. NON_AUTHORITY_DISCLOSURE consistency across 5 independent copies
# ---------------------------------------------------------------------------


class TestNonAuthorityDisclosureConsistency:
    _MODULES = {
        "evidence": evidence_mod.NON_AUTHORITY_DISCLOSURE,
        "coordinator": coordinator_mod.NON_AUTHORITY_DISCLOSURE,
        "persistence": persistence_mod.NON_AUTHORITY_DISCLOSURE,
        "status": status_mod.NON_AUTHORITY_DISCLOSURE,
        "reconciliation": reconciliation_mod.NON_AUTHORITY_DISCLOSURE,
    }

    def test_five_copies_now_share_one_source_of_truth(self):
        # F-135P-4 repair (Phase 135S): all five modules now build their
        # (possibly module-extended) dict from
        # ``pcae.cltr.migration.disclosure.NON_AUTHORITY_DISCLOSURE``
        # instead of independently hardcoding it. The five module-level
        # dict objects remain distinct objects (persistence/evidence are
        # direct re-exports so may share identity; coordinator/status/
        # reconciliation build extended copies), but their shared keys
        # must trace to, and agree with, the one shared constant.
        import pcae.cltr.migration.disclosure as disclosure_mod

        for name, disclosure in self._MODULES.items():
            for key, value in disclosure_mod.NON_AUTHORITY_DISCLOSURE.items():
                if key in disclosure:
                    assert disclosure[key] == value, (name, key)

    def test_universal_keys_agree_across_all_five(self):
        for name, disclosure in self._MODULES.items():
            assert disclosure["migration_evidence_only"] is True, name
            assert disclosure["authoritative"] is False, name

    def test_no_copy_contradicts_another_on_shared_keys(self):
        all_keys = set()
        for disclosure in self._MODULES.values():
            all_keys.update(disclosure.keys())
        for key in all_keys:
            values = {name: d[key] for name, d in self._MODULES.items() if key in d}
            if key == "production_authority":
                # evidence/coordinator store the enum value string
                # ("legacy"); status/reconciliation omit it from the
                # disclosure constant (status.py sets it separately in
                # its return dict). No module that declares it may
                # disagree on the value.
                assert len(set(values.values())) == 1, values
            elif len(values) > 1:
                assert len(set(values.values())) == 1, (key, values)


# ---------------------------------------------------------------------------
# 3. transition_id collision resistance at scale
# ---------------------------------------------------------------------------


class TestTransitionIdCollisionResistanceAtScale:
    def test_no_collision_across_many_distinct_dimension_combinations(self, tmp_path):
        root = tmp_path / "migration"
        seen: dict[str, tuple] = {}
        combos = [
            (phase, entry, epoch, rev)
            for phase in (f"P{i}" for i in range(6))
            for entry in ("phase_complete", "task_finish")
            for epoch in ("e1", "e2")
            for rev in (f"rev-{i}" for i in range(6))
        ]
        assert len(combos) == 6 * 2 * 2 * 6  # 144 distinct logical transitions
        for phase, entry, epoch, rev in combos:
            result = resolve_transition_id(
                phase_id=phase, entry_point=entry, migration_epoch=epoch, source_revision=rev, migration_root=root
            )
            key = result.transition_id
            assert key not in seen, f"collision: {(phase, entry, epoch, rev)} vs {seen.get(key)}"
            seen[key] = (phase, entry, epoch, rev)
        assert len(seen) == len(combos)

    def test_replay_stability_across_many_combinations(self, tmp_path):
        root = tmp_path / "migration"
        first_pass = {}
        combos = [(f"P{i}", "phase_complete", "e1", f"rev-{i}") for i in range(50)]
        for phase, entry, epoch, rev in combos:
            first_pass[phase] = resolve_transition_id(
                phase_id=phase, entry_point=entry, migration_epoch=epoch, source_revision=rev, migration_root=root
            ).transition_id
        for phase, entry, epoch, rev in combos:
            replay = resolve_transition_id(
                phase_id=phase, entry_point=entry, migration_epoch=epoch, source_revision=rev, migration_root=root
            )
            assert replay.transition_id == first_pass[phase]
            assert replay.replay is True


# ---------------------------------------------------------------------------
# 4. Unreachable / undisclosed comparison classes (F-135P-2, NON-BLOCKING)
# ---------------------------------------------------------------------------
# 135M's §12 comparison-class table (docs/PHASE_135_PRODUCTION_CLTR_DUAL_
# DERIVATION_AND_ATOMIC_PUBLICATION_MIGRATION_PLAN.md:369) contractually
# requires temporal_order_mismatch detection ("blocks progression if it
# indicates a causality violation, e.g. notification recorded before
# promotion"). No per-completion-event timestamp is captured anywhere in
# the shared-input schema (shared_input.py has no promoted_at/notified_at
# style fields), so comparison.py has no field-to-class mapping capable of
# ever producing TEMPORAL_ORDER_MISMATCH or EXPECTED_REPRESENTATION_
# DIFFERENCE. Unlike recovery_classification_mismatch's exclusion (which
# is explicitly documented in comparison.py's module docstring and the
# 135O implementation doc §19), these two exclusions are undisclosed
# anywhere in code or docs.


class TestUnreachableComparisonClasses:
    def _maximally_mismatched_comparison(self):
        package = _complete_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        tampered_fields = dict(legacy.fields)
        for field_name in tampered_fields:
            if field_name in _MISMATCH_CLASS_FOR_FIELD:
                tampered_fields[field_name] = f"deliberately-tampered-{field_name}"
        tampered = dataclasses.replace(legacy, fields=MappingProxyType(tampered_fields))
        return compare(tampered, cltr)

    def test_temporal_order_mismatch_is_never_producible(self):
        result = self._maximally_mismatched_comparison()
        produced_classes = {c.result_class for c in result.comparisons}
        assert ComparisonResultClass.TEMPORAL_ORDER_MISMATCH not in produced_classes
        # Confirm structurally: no field maps to it at all.
        assert ComparisonResultClass.TEMPORAL_ORDER_MISMATCH not in _MISMATCH_CLASS_FOR_FIELD.values()

    def test_expected_representation_difference_is_never_producible(self):
        result = self._maximally_mismatched_comparison()
        produced_classes = {c.result_class for c in result.comparisons}
        assert ComparisonResultClass.EXPECTED_REPRESENTATION_DIFFERENCE not in produced_classes
        assert ComparisonResultClass.EXPECTED_REPRESENTATION_DIFFERENCE not in _MISMATCH_CLASS_FOR_FIELD.values()

    def test_recovery_classification_mismatch_exclusion_is_documented(self):
        # Unlike the two classes above, this exclusion IS disclosed in
        # comparison.py's own source (module docstring / inline comment)
        # -- confirm the disclosure text is still present so this test
        # fails loudly if it is ever silently removed.
        import pcae.cltr.migration.comparison as comparison_mod

        source = open(comparison_mod.__file__, encoding="utf-8").read()
        assert "deliberately excluded" in source
        # recovery_classification IS mapped to a mismatch class (for
        # legacy-side evidence bookkeeping) but is never reached because
        # it is absent from _CLTR_FIELD_ACCESSORS -- the exclusion point.
        assert "recovery_classification" in _MISMATCH_CLASS_FOR_FIELD
        from pcae.cltr.migration.comparison import _CLTR_FIELD_ACCESSORS

        assert "recovery_classification" not in _CLTR_FIELD_ACCESSORS


# ---------------------------------------------------------------------------
# 5. Comparison-class field coverage (objective #22)
# ---------------------------------------------------------------------------


def _pre_transaction_package(**field_overrides):
    fields = {
        "phase_id": "135P-D1",
        "entry_point": "phase_complete",
        "source_revision": "a" * 64,
        "staged_final_revision": "a" * 64,
        "phase_commit_ownership": (),
        "intended_transition": "phase_complete",
        "predecessor_transition_id": None,
        "recovery_classification": "phase_complete_finalization",
    }
    fields.update(field_overrides)
    return assemble_pre_transaction(
        migration_epoch="e1",
        authority_epoch="legacy|dual_derivation_legacy_authority|e1",
        phase_id="135P-D1",
        entry_point="phase_complete",
        transition_id="33333333-3333-3333-3333-333333333333",
        predecessor_transition_id=None,
        fields=fields,
    )


_COMPLETION_FIELDS = {
    "transition_type": "close_success",
    "lifecycle_state": "TERMINAL_SUCCESS",
    "report_id": "135P-D1",
    "report_digest": "b" * 64,
    "metadata_id": "135P-D1",
    "metadata_digest": "c" * 64,
    "snapshot_id": "135P-D1",
    "snapshot_digest": "c" * 64,
    "promotion_id": "c" * 64,
    "notification_ids": ("135P-D1:phase_complete",),
    "notification_state": "confirmed",
    "notification_suppressed": False,
    "receipt_id": "receipt-1",
}


def _complete_package():
    return enrich_legacy_completion(_pre_transaction_package(), fields=dict(_COMPLETION_FIELDS))


def _tamper(legacy_result, **overrides):
    tampered_fields = dict(legacy_result.fields)
    tampered_fields.update(overrides)
    return dataclasses.replace(legacy_result, fields=MappingProxyType(tampered_fields))


class TestComparisonClassFieldCoverage:
    def test_notification_mismatch_from_notification_ids(self):
        package = _complete_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        tampered = _tamper(legacy, notification_ids=("different:notification",))
        result = compare(tampered, cltr)
        assert ComparisonResultClass.NOTIFICATION_MISMATCH in {c.result_class for c in result.comparisons}
        assert result.authority_relevant_mismatch is True

    def test_notification_mismatch_from_notification_state(self):
        package = _complete_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        tampered = _tamper(legacy, notification_state="unconfirmed")
        result = compare(tampered, cltr)
        assert ComparisonResultClass.NOTIFICATION_MISMATCH in {c.result_class for c in result.comparisons}

    def test_marker_mismatch(self):
        package = _complete_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        tampered = _tamper(legacy, marker_id="different-marker") if "marker_id" in legacy.fields else legacy
        # marker_id may not be a populated field on the legacy side for
        # this fixture; if absent, synthesize it explicitly to exercise
        # the mapping regardless of upstream field population.
        if "marker_id" not in legacy.fields:
            tampered_fields = dict(legacy.fields)
            tampered_fields["marker_id"] = "different-marker"
            tampered = dataclasses.replace(legacy, fields=MappingProxyType(tampered_fields))
        result = compare(tampered, cltr)
        classes = {c.result_class for c in result.comparisons}
        assert ComparisonResultClass.MARKER_MISMATCH in classes or ComparisonResultClass.CLTR_MISSING in classes

    def test_receipt_mismatch(self):
        package = _complete_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        tampered = _tamper(legacy, receipt_id="different-receipt")
        result = compare(tampered, cltr)
        assert ComparisonResultClass.RECEIPT_MISMATCH in {c.result_class for c in result.comparisons}

    def test_commit_ownership_no_longer_crashes_derivation(self, tmp_path, monkeypatch):
        # F-135P-3 repair (Phase 135S): cltr_derivation.py now normalizes
        # raw commit-hash strings into typed ``CommitOwnershipEntry``
        # values (``_normalize_commit_ownership``, mirroring the Stage-0
        # shadow observer's own CertificationState.UNVERIFIABLE pattern)
        # before constructing ``ProductionCltrRecord``, so CLTR-COMMIT-2's
        # ``.certification_state`` dereference no longer raises
        # ``AttributeError`` for a non-empty ``phase_commit_ownership``.
        from pcae.cltr.enums import CertificationState

        package = _pre_transaction_package(phase_commit_ownership=("a" * 40,))
        package = enrich_legacy_completion(package, fields=dict(_COMPLETION_FIELDS))
        result = derive_cltr(package)
        assert result.status == "constructed"
        assert len(result.record.phase_commit_ownership) == 1
        entry = result.record.phase_commit_ownership[0]
        assert entry.commit_hash == "a" * 40
        assert entry.certification_state == CertificationState.UNVERIFIABLE

        # Confirm the fix holds end-to-end through the coordinator's
        # public best-effort entrypoint too. ``complete()`` performs its
        # own legacy-completion enrichment internally, so it is given a
        # fresh pre-transaction-only package here (passing the
        # already-enriched ``package`` above would itself be an invalid,
        # double-enrichment call per ``assembly.enrich_legacy_completion``'s
        # own "cannot enrich a package whose latest revision is already
        # ...LEGACY_COMPLETION" guard, an unrelated failure mode).
        monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", "epoch-commit-ownership")
        pre_transaction_package = _pre_transaction_package(phase_commit_ownership=("a" * 40,))
        result = complete(
            pre_transaction_package,
            legacy_completion_fields=dict(_COMPLETION_FIELDS),
            recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
            production_completion_continued=True,
            migration_root=tmp_path / "migration",
        )
        assert result.status == "completed"

    def test_production_call_site_always_passes_empty_commit_ownership_today(self):
        # Confirms the dormancy claim above directly from source: the
        # only production call site hardcodes an empty tuple, so F-135P-3
        # cannot currently fire from real finalization traffic.
        import inspect

        import pcae.core.finalization_transaction as ft_mod

        source = inspect.getsource(ft_mod._capture_stage1_migration_pre_transaction)
        assert "phase_commit_ownership=()" in source

    def test_state_mismatch(self):
        package = _complete_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        tampered = _tamper(legacy, lifecycle_state="TERMINAL_PARTIAL_EXTERNAL")
        result = compare(tampered, cltr)
        assert ComparisonResultClass.STATE_MISMATCH in {c.result_class for c in result.comparisons}
        assert result.overall_class in (ComparisonResultClass.STATE_MISMATCH, ComparisonResultClass.IDENTITY_MISMATCH)


# ---------------------------------------------------------------------------
# 6. Persistence crash mid-sequence
# ---------------------------------------------------------------------------


class TestPersistenceCrashMidSequence:
    def test_evidence_write_failure_leaves_prior_valid_revision_intact_and_reports_failed(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", "epoch-crash")
        root = tmp_path / "migration"

        package = capture_pre_transaction(
            phase_id="135P-CRASH",
            entry_point="phase_complete",
            source_revision="a" * 64,
            staged_final_revision="a" * 64,
            phase_commit_ownership=(),
            intended_transition="phase_complete",
            recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
            migration_root=root,
        )
        assert package is not None
        pre_txn_revision_path = root / "epochs" / "epoch-crash" / "transitions" / package.transition_id / "inputs" / "1.json"
        assert pre_txn_revision_path.exists()
        original_bytes = pre_txn_revision_path.read_bytes()

        _real_write_immutable = coordinator_mod.write_immutable

        def _boom_write_immutable(path, data):
            if path.name == "evidence.json":
                raise OSError("simulated disk failure during evidence write")
            return _real_write_immutable(path, data)

        monkeypatch.setattr(coordinator_mod, "write_immutable", _boom_write_immutable)

        result = complete(
            package,
            legacy_completion_fields=dict(_COMPLETION_FIELDS, report_id="135P-CRASH", metadata_id="135P-CRASH",
                                           snapshot_id="135P-CRASH", notification_ids=("135P-CRASH:phase_complete",)),
            recovery_classification=MigrationRecoveryClassification.PHASE_COMPLETE,
            production_completion_continued=True,
            migration_root=root,
        )

        assert result.status == "failed"
        assert result.stage_failed == "persistence"
        assert result.migration_progression_eligible is False

        # The pre-transaction revision persisted before the crash must be
        # completely untouched.
        assert pre_txn_revision_path.read_bytes() == original_bytes

        # No evidence file was ever created (no partial-evidence claim).
        evidence_path = root / "epochs" / "epoch-crash" / "transitions" / package.transition_id / "evidence" / "evidence.json"
        assert not evidence_path.exists()

        # A failure record was persisted for auditability.
        failures_dir = root / "epochs" / "epoch-crash" / "transitions" / package.transition_id / "failures"
        assert failures_dir.exists()
        assert len(list(failures_dir.iterdir())) == 1


# ---------------------------------------------------------------------------
# 7. Four real entry points driven through the finalization boundary
# ---------------------------------------------------------------------------
# test_cltr_135o_integration.py's ``_run`` helper hardcodes
# ``entry_point="phase_complete"`` in all 5 of its tests -- no test in the
# 135O suite actually drives ``task_finish``, ``phase_report_create``, or
# ``notify_send_report`` through the real finalization boundary. This
# closes that gap directly, and independently confirms the F-135P-1
# recovery-classification result end-to-end (not just at the internal
# helper-function level tested above).


class TestFourEntryPointsThroughRealFinalizationBoundary:
    @pytest.mark.parametrize("entry_point", ["task_finish", "phase_complete", "phase_report_create", "notify_send_report"])
    def test_migration_evidence_recovery_classification_for_each_entry_point(self, entry_point, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", "1")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_STAGE", "dual_derivation_legacy_authority")
        monkeypatch.setenv("PCAE_CLTR_MIGRATION_EPOCH", f"epoch-{entry_point}")

        from unittest import mock

        import pcae.core.phase_reports as pr
        from pcae.cltr.migration import reconciliation
        from pcae.core.finalization_transaction import run_finalization_transaction

        phase_id = f"999X.2-135p-{entry_point}"
        defaults = dict(
            phase_id=phase_id,
            phase_name="135P Entry Point Test",
            status="completed",
            summary=f"Phase {phase_id}: 135P entry-point coverage test.",
            files_changed=1,
            tests_run=1,
            commits=["a" * 40],
            pushed_status="pushed",
            origin_main_head_count=0,
            recommended_next_phase="999Y — Next Phase",
            explicit_no_go_confirmations=[f"No issue {i}." for i in range(11)],
            test_results={"fast_green": "1/1", "report_notification_tests": "passed",
                          "bootstrap_session_reporting_tests": "passed"},
            governance_results={"pcae_health": "healthy", "pcae_check": "passed", "pcae_doctor_task_memory": "clean",
                                 "pcae_push_check": "clean", "telegram_runtime": "configured"},
            risks=["Some known risk."],
            follow_ups=["Some follow-up."],
        )
        with mock.patch.object(pr, "load_canonical_report", return_value=None):
            report = pr.make_phase_report(**defaults)
            report.architecture_status = {
                "schema_version": "1.0", "state_marker": "abc123", "repository_revision": "deadbeef",
                "completed": [], "completed_phase_ids": ["998A"], "completed_chapters": [], "in_progress": [],
                "current_phase_id": phase_id, "planned": [], "planned_phase_ids": [],
                "current_runtime_state": "Observed", "current_maximum_capability": "observe",
                "execution_availability": "unavailable", "freshness": "fresh", "limitations": [], "conflicts": [],
                "source_provenance": {},
            }
            report.metadata["phase_id"] = phase_id
            report.metadata["source_revision"] = "deadbeef"
            report.metadata["phase_commits"] = report.commits
            pr._apply_canonical_and_trust(report, phase_id, report.phase_name, report.status)
            gate = pr.validate_finalization_gate(
                phase_id=phase_id, report=report, metadata=report.metadata, pushed_status=report.pushed_status,
                origin_main_head_count=report.origin_main_head_count, governance_results=report.governance_results,
                test_results=report.test_results, no_go_confirmations=report.explicit_no_go_confirmations,
                recommended_next_phase=report.recommended_next_phase, commit_attribution=report.commits[0],
            )

        calls: list = []

        def _callback():
            calls.append(True)
            report.notification_result = {"dispatched": True, "sinks": ["noop"], "success": True, "error": None,
                                           "outcome": "sent", "reason": "", "kind": "complete"}
            return {"report": report, "blocked": False, "report_error": None}

        result = run_finalization_transaction(
            phase_id=report.phase_id, phase_name=report.phase_name, report=report, gate=gate,
            promote_and_dispatch=_callback, transaction_root=tmp_path / "txns", receipt_root=tmp_path / "receipts",
            entry_point=entry_point,
        )
        assert result.status == "completed"
        assert calls == [True]

        payload = reconciliation.reconcile(phase_id)
        assert payload["found"] is True
        transition = payload["transitions"][0]
        assert transition["production_authority"] == "legacy"

        # This is the live, end-to-end confirmation of F-135P-1's repair
        # (Phase 135S, finalization_transaction.py's
        # _ENTRY_POINT_RECOVERY_CLASSIFICATION): all four entry points now
        # get their own dedicated, truthful classification -- none falls
        # back to ordinary_finalization. Read directly from persisted
        # evidence, not from the internal helper function.
        evidence_dir = tmp_path / ".pcae" / "cltr-migration" / "epochs" / f"epoch-{entry_point}" / "transitions"
        transition_dirs = list(evidence_dir.iterdir())
        assert len(transition_dirs) == 1
        import json

        evidence_json = json.loads((transition_dirs[0] / "evidence" / "evidence.json").read_text())
        expected = {
            "task_finish": "task_finish_finalization",
            "phase_complete": "phase_complete_finalization",
            "phase_report_create": "report_create_recovery",
            "notify_send_report": "manual_governed_recovery",
        }[entry_point]
        assert evidence_json["recovery_classification"] == expected
        # Regardless of the classification gap, production authority and
        # progression eligibility remain unaffected (proven in
        # TestEntryPointRecoveryClassificationWiring above).
        assert evidence_json["migration_progression_eligible"] is True
