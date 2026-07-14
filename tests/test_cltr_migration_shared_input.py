"""Phase 135O — staged shared-input assembly and deep-immutability tests
(135M §8.4, repaired and verified by 135N)."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from pcae.cltr.migration.assembly import (
    SharedInputValidationError,
    assemble_pre_transaction,
    enrich_legacy_completion,
)
from pcae.cltr.migration.enums import InputStage


def _base_kwargs(**overrides):
    kwargs = dict(
        migration_epoch="e1",
        authority_epoch="legacy|dual_derivation_legacy_authority|e1",
        phase_id="135O-SI",
        entry_point="phase_complete",
        transition_id="11111111-1111-1111-1111-111111111111",
        predecessor_transition_id=None,
        fields={
            "phase_id": "135O-SI",
            "entry_point": "phase_complete",
            "source_revision": "rev-a",
            "staged_final_revision": "rev-a",
            "phase_commit_ownership": (),
            "intended_transition": "phase_complete",
            "predecessor_transition_id": None,
            "recovery_classification": "phase_complete_finalization",
        },
    )
    kwargs.update(overrides)
    return kwargs


def test_stage_a_valid_fields_assemble():
    package = assemble_pre_transaction(**_base_kwargs())
    assert package.latest.stage == InputStage.PRE_TRANSACTION
    assert package.latest.revision == 1
    assert package.latest.revision_digest is not None


def test_premature_terminal_fields_rejected():
    kwargs = _base_kwargs()
    kwargs["fields"] = dict(kwargs["fields"], report_digest="a" * 64)
    with pytest.raises(SharedInputValidationError):
        assemble_pre_transaction(**kwargs)


def test_missing_mandatory_stage_field_rejected():
    kwargs = _base_kwargs()
    fields = dict(kwargs["fields"])
    del fields["source_revision"]
    kwargs["fields"] = fields
    with pytest.raises(SharedInputValidationError):
        assemble_pre_transaction(**kwargs)


def test_stable_package_identity_across_revisions():
    package = assemble_pre_transaction(**_base_kwargs())
    package_id_before = package.package_id
    enriched = enrich_legacy_completion(package, fields={"report_id": "r1", "report_digest": "a" * 64})
    assert enriched.package_id == package_id_before


def test_predecessor_digest_binding():
    package = assemble_pre_transaction(**_base_kwargs())
    enriched = enrich_legacy_completion(package, fields={"report_id": "r1"})
    assert enriched.latest.predecessor_digest == package.latest.revision_digest


def test_prior_revision_untouched_after_enrichment():
    package = assemble_pre_transaction(**_base_kwargs())
    first_digest = package.latest.revision_digest
    enriched = enrich_legacy_completion(package, fields={"report_id": "r1"})
    # The original package's own revisions tuple is unaffected (new object
    # returned, not an in-place mutation).
    assert package.latest.revision_digest == first_digest
    assert len(package.revisions) == 1
    assert len(enriched.revisions) == 2


def test_revision_ordering_increments():
    package = assemble_pre_transaction(**_base_kwargs())
    enriched = enrich_legacy_completion(package, fields={"report_id": "r1"})
    assert [r.revision for r in enriched.revisions] == [1, 2]


def test_unknown_field_for_legacy_completion_rejected():
    package = assemble_pre_transaction(**_base_kwargs())
    with pytest.raises(SharedInputValidationError):
        enrich_legacy_completion(package, fields={"not_a_real_field": "x"})


def test_double_enrichment_rejected():
    package = assemble_pre_transaction(**_base_kwargs())
    enriched = enrich_legacy_completion(package, fields={"report_id": "r1"})
    with pytest.raises(SharedInputValidationError):
        enrich_legacy_completion(enriched, fields={"report_id": "r2"})


def test_missing_field_remains_absent_not_fabricated():
    package = assemble_pre_transaction(**_base_kwargs())
    assert package.field("report_digest") is None
    assert "report_digest" not in package.latest.fields


class TestDeepImmutability:
    def test_nested_dict_mutation_rejected(self):
        kwargs = _base_kwargs()
        kwargs["fields"] = dict(kwargs["fields"], phase_commit_ownership=({"nested": "dict"},))
        package = assemble_pre_transaction(**kwargs)
        nested = package.latest.fields["phase_commit_ownership"][0]
        assert isinstance(nested, MappingProxyType)
        with pytest.raises(TypeError):
            nested["nested"] = "mutated"

    def test_nested_list_mutation_rejected(self):
        package = assemble_pre_transaction(**_base_kwargs())
        assert isinstance(package.latest.fields["phase_commit_ownership"], tuple)
        with pytest.raises(AttributeError):
            package.latest.fields["phase_commit_ownership"].append("x")  # tuples have no append

    def test_top_level_fields_mapping_is_immutable(self):
        package = assemble_pre_transaction(**_base_kwargs())
        with pytest.raises(TypeError):
            package.latest.fields["phase_id"] = "tampered"

    def test_revision_dataclass_is_frozen(self):
        package = assemble_pre_transaction(**_base_kwargs())
        with pytest.raises(Exception):
            package.latest.revision = 99

    def test_alias_mutation_cannot_alter_record(self):
        kwargs = _base_kwargs()
        mutable_source = {"a": [1, 2, 3]}
        kwargs["fields"] = dict(kwargs["fields"], phase_commit_ownership=(mutable_source,))
        package = assemble_pre_transaction(**kwargs)
        digest_before = package.latest.revision_digest
        mutable_source["a"].append(4)  # mutate the caller's own original dict
        assert package.latest.revision_digest == digest_before
        assert list(package.latest.fields["phase_commit_ownership"][0]["a"]) == [1, 2, 3]

    def test_digest_stable_after_attempted_mutation(self):
        package = assemble_pre_transaction(**_base_kwargs())
        digest_before = package.latest.revision_digest
        try:
            package.latest.fields["phase_id"] = "tampered"
        except TypeError:
            pass
        assert package.latest.revision_digest == digest_before
