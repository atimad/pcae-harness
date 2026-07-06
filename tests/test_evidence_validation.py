"""Phase 115C: Repository Evidence Framework Prototype.

Tests structural validation implemented in ``src/pcae/core/evidence.py``:
required fields, enum values, and duplicate evidence IDs. Per 115B/115C,
this module validates structure only -- it never validates repository
semantics (e.g. whether a referenced commit hash actually exists, or
whether a scope path is real).
"""
from __future__ import annotations

import pytest

from pcae.core.evidence import (
    Evidence,
    EvidenceCategory,
    EvidenceCollection,
    EvidenceConfidence,
    EvidenceDeterminism,
    EvidenceFreshness,
    EvidenceProvenance,
    EvidenceReference,
)


def _provenance(**overrides) -> EvidenceProvenance:
    base = dict(
        producer="git_provider@v1",
        produced_from="git status --porcelain",
        timestamp="2026-07-06T00:00:00Z",
        deterministic_origin=True,
    )
    base.update(overrides)
    return EvidenceProvenance(**base)


def _evidence_kwargs(**overrides) -> dict:
    base = dict(
        evidence_id="E-git-001",
        source="Git",
        category=EvidenceCategory.GIT,
        producer="git_provider",
        timestamp_utc="2026-07-06T00:00:00Z",
        freshness=EvidenceFreshness.CURRENT,
        confidence=EvidenceConfidence.HIGH,
        determinism=EvidenceDeterminism.DETERMINISTIC,
        scope="repo",
        references=(),
        observed_value=None,
        explanation="evidence item",
        provenance=_provenance(),
    )
    base.update(overrides)
    return base


class TestRequiredFieldValidation:
    @pytest.mark.parametrize(
        "field_name",
        ["evidence_id", "source", "producer", "timestamp_utc", "scope", "explanation"],
    )
    def test_empty_required_field_raises(self, field_name):
        kwargs = _evidence_kwargs(**{field_name: ""})
        with pytest.raises(ValueError, match=field_name):
            Evidence(**kwargs)

    def test_missing_provenance_type_raises(self):
        kwargs = _evidence_kwargs(provenance="not-a-provenance")
        with pytest.raises(ValueError, match="provenance"):
            Evidence(**kwargs)

    def test_evidence_reference_requires_non_empty_id(self):
        with pytest.raises(ValueError, match="evidence_id"):
            EvidenceReference(evidence_id="")

    @pytest.mark.parametrize(
        "field_name",
        ["producer", "produced_from", "timestamp"],
    )
    def test_provenance_empty_required_field_raises(self, field_name):
        with pytest.raises(ValueError, match=field_name):
            _provenance(**{field_name: ""})

    def test_provenance_deterministic_origin_must_be_bool(self):
        with pytest.raises(ValueError, match="deterministic_origin"):
            _provenance(deterministic_origin="yes")


class TestEnumValidation:
    def test_valid_category_string_accepted(self):
        ev = Evidence(**_evidence_kwargs(category="task"))
        assert ev.category is EvidenceCategory.TASK

    def test_invalid_category_string_raises(self):
        with pytest.raises(ValueError, match="EvidenceCategory"):
            Evidence(**_evidence_kwargs(category="not-a-real-category"))

    def test_invalid_freshness_string_raises(self):
        with pytest.raises(ValueError, match="EvidenceFreshness"):
            Evidence(**_evidence_kwargs(freshness="ancient"))

    def test_invalid_confidence_string_raises(self):
        with pytest.raises(ValueError, match="EvidenceConfidence"):
            Evidence(**_evidence_kwargs(confidence="certain"))

    def test_invalid_determinism_string_raises(self):
        with pytest.raises(ValueError, match="EvidenceDeterminism"):
            Evidence(**_evidence_kwargs(determinism="magic"))

    def test_all_fifteen_categories_are_frozen(self):
        values = {c.value for c in EvidenceCategory}
        assert values == {
            "git", "task", "phase", "report", "metadata", "architecture",
            "runtime", "push_state", "notification", "governance",
            "test_result", "security", "documentation", "ai_review", "unknown",
        }

    def test_all_five_determinism_levels_are_frozen(self):
        values = {d.value for d in EvidenceDeterminism}
        assert values == {
            "deterministic", "reproducible_external", "probabilistic",
            "human_asserted", "unknown",
        }

    def test_all_four_confidence_levels_are_frozen(self):
        values = {c.value for c in EvidenceConfidence}
        assert values == {"high", "medium", "low", "unknown"}

    def test_all_four_freshness_levels_are_frozen(self):
        values = {f.value for f in EvidenceFreshness}
        assert values == {"current", "stale", "expired", "unknown"}


class TestDuplicateEvidenceIdValidation:
    def test_collection_construction_rejects_duplicates(self):
        ev1 = Evidence(**_evidence_kwargs(evidence_id="E-1"))
        ev2 = Evidence(**_evidence_kwargs(evidence_id="E-1", source="Runtime Inspect"))
        with pytest.raises(ValueError, match="Duplicate evidence_id"):
            EvidenceCollection((ev1, ev2))

    def test_add_rejects_duplicate_against_existing_collection(self):
        ev1 = Evidence(**_evidence_kwargs(evidence_id="E-1"))
        collection = EvidenceCollection((ev1,))
        duplicate = Evidence(**_evidence_kwargs(evidence_id="E-1", source="Runtime Inspect"))
        with pytest.raises(ValueError, match="Duplicate evidence_id"):
            collection.add(duplicate)

    def test_distinct_ids_do_not_raise(self):
        ev1 = Evidence(**_evidence_kwargs(evidence_id="E-1"))
        ev2 = Evidence(**_evidence_kwargs(evidence_id="E-2"))
        collection = EvidenceCollection((ev1, ev2))
        assert len(collection) == 2


class TestNoRepositorySemanticsValidation:
    """115B/115C freeze structural validation only -- no repository fact
    checking. These items would be semantically nonsensical in a real
    repository but are structurally valid Evidence, and construction must
    not attempt to verify them.
    """

    def test_nonexistent_commit_hash_in_references_is_accepted(self):
        ev = Evidence(**_evidence_kwargs(references=("0000000000000000000000000000000000dead",)))
        assert ev.references == ("0000000000000000000000000000000000dead",)

    def test_arbitrary_scope_string_is_accepted(self):
        ev = Evidence(**_evidence_kwargs(scope="not/a/real/path/in/this/repo"))
        assert ev.scope == "not/a/real/path/in/this/repo"

    def test_arbitrary_source_string_is_accepted(self):
        ev = Evidence(**_evidence_kwargs(source="Some Future Provider Nobody Registered"))
        assert ev.source == "Some Future Provider Nobody Registered"

    def test_unknown_category_is_a_valid_containment_value(self):
        ev = Evidence(**_evidence_kwargs(category=EvidenceCategory.UNKNOWN))
        assert ev.category is EvidenceCategory.UNKNOWN
