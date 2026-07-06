"""Phase 115C: Repository Evidence Framework Prototype.

Tests ``EvidenceCollection`` implemented in ``src/pcae/core/evidence.py``:
ordering, lookup, iteration, duplicate detection, and category/source/
determinism/confidence filtering. No decision logic and no evaluation
live in ``EvidenceCollection`` -- these tests only exercise structural
container behavior.
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
)


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        producer="test-provider",
        produced_from="unit-test",
        timestamp="2026-07-06T00:00:00Z",
        deterministic_origin=True,
    )


def _evidence(evidence_id: str, **overrides) -> Evidence:
    base = dict(
        evidence_id=evidence_id,
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
    return Evidence(**base)


class TestEmptyCollection:
    def test_empty_collection_has_zero_length(self):
        assert len(EvidenceCollection()) == 0

    def test_empty_collection_iterates_to_nothing(self):
        assert list(EvidenceCollection()) == []

    def test_by_id_on_empty_collection_returns_none(self):
        assert EvidenceCollection().by_id("E-1") is None


class TestOrderingAndIteration:
    def test_preserves_insertion_order(self):
        items = (_evidence("E-1"), _evidence("E-2"), _evidence("E-3"))
        collection = EvidenceCollection(items)
        assert [e.evidence_id for e in collection] == ["E-1", "E-2", "E-3"]

    def test_len_matches_item_count(self):
        collection = EvidenceCollection((_evidence("E-1"), _evidence("E-2")))
        assert len(collection) == 2

    def test_iteration_yields_evidence_instances(self):
        collection = EvidenceCollection((_evidence("E-1"),))
        for item in collection:
            assert isinstance(item, Evidence)


class TestLookupById:
    def test_by_id_finds_existing_item(self):
        ev = _evidence("E-1")
        collection = EvidenceCollection((ev, _evidence("E-2")))
        assert collection.by_id("E-1") is ev

    def test_by_id_returns_none_for_missing_item(self):
        collection = EvidenceCollection((_evidence("E-1"),))
        assert collection.by_id("E-missing") is None

    def test_contains_checks_by_evidence_id(self):
        collection = EvidenceCollection((_evidence("E-1"),))
        assert "E-1" in collection
        assert "E-missing" not in collection


class TestDuplicateDetection:
    def test_construction_rejects_duplicate_evidence_ids(self):
        with pytest.raises(ValueError, match="Duplicate evidence_id"):
            EvidenceCollection((_evidence("E-1"), _evidence("E-1")))

    def test_add_rejects_duplicate_evidence_id(self):
        collection = EvidenceCollection((_evidence("E-1"),))
        with pytest.raises(ValueError, match="Duplicate evidence_id"):
            collection.add(_evidence("E-1"))

    def test_add_returns_new_collection_without_mutating_original(self):
        original = EvidenceCollection((_evidence("E-1"),))
        expanded = original.add(_evidence("E-2"))
        assert len(original) == 1
        assert len(expanded) == 2
        assert original is not expanded

    def test_add_preserves_original_order_and_appends(self):
        original = EvidenceCollection((_evidence("E-1"), _evidence("E-2")))
        expanded = original.add(_evidence("E-3"))
        assert [e.evidence_id for e in expanded] == ["E-1", "E-2", "E-3"]


class TestCategoryFiltering:
    def test_by_category_returns_only_matching_items(self):
        collection = EvidenceCollection((
            _evidence("E-1", category=EvidenceCategory.GIT),
            _evidence("E-2", category=EvidenceCategory.TASK),
            _evidence("E-3", category=EvidenceCategory.GIT),
        ))
        filtered = collection.by_category(EvidenceCategory.GIT)
        assert [e.evidence_id for e in filtered] == ["E-1", "E-3"]

    def test_by_category_accepts_raw_string(self):
        collection = EvidenceCollection((
            _evidence("E-1", category=EvidenceCategory.GIT),
            _evidence("E-2", category=EvidenceCategory.TASK),
        ))
        filtered = collection.by_category("task")
        assert [e.evidence_id for e in filtered] == ["E-2"]

    def test_by_category_returns_evidence_collection(self):
        collection = EvidenceCollection((_evidence("E-1"),))
        assert isinstance(collection.by_category(EvidenceCategory.GIT), EvidenceCollection)


class TestSourceFiltering:
    def test_by_source_returns_only_matching_items(self):
        collection = EvidenceCollection((
            _evidence("E-1", source="Git"),
            _evidence("E-2", source="Runtime Inspect"),
            _evidence("E-3", source="Git"),
        ))
        filtered = collection.by_source("Git")
        assert [e.evidence_id for e in filtered] == ["E-1", "E-3"]


class TestDeterminismFiltering:
    def test_by_determinism_returns_only_matching_items(self):
        collection = EvidenceCollection((
            _evidence("E-1", determinism=EvidenceDeterminism.DETERMINISTIC),
            _evidence("E-2", determinism=EvidenceDeterminism.PROBABILISTIC),
        ))
        filtered = collection.by_determinism(EvidenceDeterminism.PROBABILISTIC)
        assert [e.evidence_id for e in filtered] == ["E-2"]

    def test_by_determinism_accepts_raw_string(self):
        collection = EvidenceCollection((
            _evidence("E-1", determinism=EvidenceDeterminism.HUMAN_ASSERTED),
        ))
        filtered = collection.by_determinism("human_asserted")
        assert len(filtered) == 1


class TestConfidenceFiltering:
    def test_by_confidence_returns_only_matching_items(self):
        collection = EvidenceCollection((
            _evidence("E-1", confidence=EvidenceConfidence.HIGH),
            _evidence("E-2", confidence=EvidenceConfidence.LOW),
            _evidence("E-3", confidence=EvidenceConfidence.HIGH),
        ))
        filtered = collection.by_confidence(EvidenceConfidence.HIGH)
        assert [e.evidence_id for e in filtered] == ["E-1", "E-3"]

    def test_by_confidence_accepts_raw_string(self):
        collection = EvidenceCollection((_evidence("E-1", confidence=EvidenceConfidence.LOW),))
        filtered = collection.by_confidence("low")
        assert len(filtered) == 1


class TestConflictingEvidencePreserved:
    def test_conflicting_evidence_both_preserved_no_resolution(self):
        conflict_a = _evidence(
            "E-metadata-002", category=EvidenceCategory.METADATA,
            observed_value="not_pushed",
        )
        conflict_b = _evidence(
            "E-git-001", category=EvidenceCategory.GIT,
            observed_value="origin/main..HEAD=0",
        )
        collection = EvidenceCollection((conflict_a, conflict_b))
        assert len(collection) == 2
        assert collection.by_id("E-metadata-002").observed_value == "not_pushed"
        assert collection.by_id("E-git-001").observed_value == "origin/main..HEAD=0"
