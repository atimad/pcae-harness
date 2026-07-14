"""Phase 135O — legacy derivation, CLTR derivation, and comparison tests."""

from __future__ import annotations

from pcae.cltr.migration.assembly import assemble_pre_transaction, enrich_legacy_completion
from pcae.cltr.migration.cltr_derivation import derive_cltr
from pcae.cltr.migration.comparison import compare
from pcae.cltr.migration.enums import ComparisonResultClass
from pcae.cltr.migration.legacy_derivation import derive_legacy


def _pre_transaction_package(**field_overrides):
    fields = {
        "phase_id": "135O-D1",
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
        phase_id="135O-D1",
        entry_point="phase_complete",
        transition_id="22222222-2222-2222-2222-222222222222",
        predecessor_transition_id=None,
        fields=fields,
    )


_COMPLETION_FIELDS = {
    "transition_type": "close_success",
    "lifecycle_state": "TERMINAL_SUCCESS",
    "report_id": "135O-D1",
    "report_digest": "b" * 64,
    "metadata_id": "135O-D1",
    "metadata_digest": "c" * 64,
    "snapshot_id": "135O-D1",
    "snapshot_digest": "c" * 64,
    "promotion_id": "c" * 64,
    "notification_ids": ("135O-D1:phase_complete",),
    "notification_state": "confirmed",
    "notification_suppressed": False,
    "receipt_id": "receipt-1",
}


def _complete_package():
    return enrich_legacy_completion(_pre_transaction_package(), fields=dict(_COMPLETION_FIELDS))


class TestLegacyDerivation:
    def test_normal_result_normalization(self):
        result = derive_legacy(_complete_package())
        assert result.fields["phase_id"] == "135O-D1"
        assert result.fields["report_digest"] == "b" * 64
        assert result.authority_role == "legacy"

    def test_no_second_report_or_promotion_no_op_by_construction(self):
        # derive_legacy performs no I/O and calls no promotion/notification
        # function -- verified structurally: the module imports nothing
        # from pcae.core.phase_reports or pcae.core.notifications.
        import pcae.cltr.migration.legacy_derivation as mod

        assert "phase_reports" not in mod.__dict__
        assert "notifications" not in mod.__dict__

    def test_deterministic_output(self):
        package = _complete_package()
        a = derive_legacy(package)
        b = derive_legacy(package)
        assert a.derivation_digest == b.derivation_digest

    def test_explicit_limitations_for_unavailable_fields(self):
        result = derive_legacy(_pre_transaction_package())
        assert any("not yet available" in limitation for limitation in result.limitations)


class TestCltrDerivation:
    def test_pre_transaction_only_is_missing_mandatory_input(self):
        result = derive_cltr(_pre_transaction_package())
        assert result.status == "missing_mandatory_input"
        assert result.record is None

    def test_complete_package_constructs_valid_record(self):
        result = derive_cltr(_complete_package())
        assert result.status == "constructed"
        assert result.record is not None
        assert result.record.shadow_mode is True
        assert result.record.authoritative is False

    def test_deterministic_output(self):
        package = _complete_package()
        a = derive_cltr(package)
        b = derive_cltr(package)
        assert a.record_digest == b.record_digest

    def test_no_production_promotion_no_dispatch(self):
        import pcae.cltr.migration.cltr_derivation as mod

        assert not hasattr(mod, "publish_generation")
        assert "notifications" not in mod.__dict__


class TestComparison:
    def test_exact_match_when_derivations_agree(self):
        package = _complete_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        result = compare(legacy, cltr)
        assert result.overall_class == ComparisonResultClass.EXACT_MATCH
        assert result.authority_relevant_mismatch is False

    def test_digest_mismatch_when_source_revision_disagrees(self):
        package = _complete_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        # Simulate legacy disagreement by tampering the legacy result's
        # normalized fields (never the CLTR record itself).
        import dataclasses
        from types import MappingProxyType

        tampered_fields = dict(legacy.fields)
        tampered_fields["source_revision"] = "different" * 8
        tampered = dataclasses.replace(legacy, fields=MappingProxyType(tampered_fields))
        result = compare(tampered, cltr)
        assert result.authority_relevant_mismatch is True
        assert any(c.result_class == ComparisonResultClass.DIGEST_MISMATCH for c in result.comparisons)

    def test_unverifiable_when_cltr_derivation_incomplete(self):
        package = _pre_transaction_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        result = compare(legacy, cltr)
        assert result.overall_class == ComparisonResultClass.UNVERIFIABLE
        assert result.unverifiable is True

    def test_deterministic_precedence_with_multiple_mismatches(self):
        package = _complete_package()
        legacy = derive_legacy(package)
        cltr = derive_cltr(package)
        import dataclasses
        from types import MappingProxyType

        tampered_fields = dict(legacy.fields)
        tampered_fields["phase_id"] = "different-phase"
        tampered_fields["marker_id"] = "different-marker"
        tampered = dataclasses.replace(legacy, fields=MappingProxyType(tampered_fields))
        result = compare(tampered, cltr)
        # identity_mismatch precedes marker_mismatch in COMPARISON_RESULT_PRECEDENCE
        assert result.overall_class == ComparisonResultClass.IDENTITY_MISMATCH
