"""Phase 115C: Repository Evidence Framework Prototype.

Tests JSON-compatible ``to_dict()``/``from_dict()`` serialization for
``Evidence``, ``EvidenceCollection``, ``EvidenceReference``, and
``EvidenceProvenance`` implemented in ``src/pcae/core/evidence.py``. No
persistence layer is implemented -- these tests only verify the in-memory
dict shape is JSON round-trippable.
"""
from __future__ import annotations

import json

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


def _provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        producer="git_provider@v1",
        produced_from="git status --porcelain",
        timestamp="2026-07-06T00:00:00Z",
        deterministic_origin=True,
    )


def _evidence(evidence_id: str = "E-git-001", **overrides) -> Evidence:
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
        references=("abc1234", "def5678"),
        observed_value={"dirty": False, "files": ["a.py", "b.py"]},
        expected_value=None,
        explanation="Working tree is clean.",
        limitations="No CI signal available.",
        provenance=_provenance(),
    )
    base.update(overrides)
    return Evidence(**base)


class TestEvidenceReferenceSerialization:
    def test_to_dict_shape(self):
        ref = EvidenceReference(evidence_id="E-git-001", note="cited")
        assert ref.to_dict() == {"evidence_id": "E-git-001", "note": "cited"}

    def test_round_trip(self):
        ref = EvidenceReference(evidence_id="E-git-001", note="cited")
        restored = EvidenceReference.from_dict(ref.to_dict())
        assert restored == ref

    def test_round_trip_without_note(self):
        ref = EvidenceReference(evidence_id="E-git-001")
        restored = EvidenceReference.from_dict(ref.to_dict())
        assert restored == ref
        assert restored.note is None

    def test_json_compatible(self):
        ref = EvidenceReference(evidence_id="E-git-001", note="cited")
        text = json.dumps(ref.to_dict())
        restored = EvidenceReference.from_dict(json.loads(text))
        assert restored == ref


class TestEvidenceProvenanceSerialization:
    def test_to_dict_shape(self):
        prov = _provenance()
        assert prov.to_dict() == {
            "producer": "git_provider@v1",
            "produced_from": "git status --porcelain",
            "timestamp": "2026-07-06T00:00:00Z",
            "deterministic_origin": True,
        }

    def test_round_trip(self):
        prov = _provenance()
        restored = EvidenceProvenance.from_dict(prov.to_dict())
        assert restored == prov

    def test_json_compatible(self):
        prov = _provenance()
        text = json.dumps(prov.to_dict())
        restored = EvidenceProvenance.from_dict(json.loads(text))
        assert restored == prov


class TestEvidenceSerialization:
    def test_to_dict_contains_all_frozen_fields(self):
        ev = _evidence()
        d = ev.to_dict()
        for key in (
            "evidence_id", "source", "category", "producer", "timestamp_utc",
            "freshness", "confidence", "determinism", "scope", "references",
            "observed_value", "expected_value", "explanation", "limitations",
        ):
            assert key in d

    def test_enum_fields_serialize_to_plain_strings(self):
        ev = _evidence()
        d = ev.to_dict()
        assert d["category"] == "git"
        assert d["freshness"] == "current"
        assert d["confidence"] == "high"
        assert d["determinism"] == "deterministic"
        assert all(isinstance(v, str) for v in (d["category"], d["freshness"], d["confidence"], d["determinism"]))

    def test_references_serialize_to_list(self):
        ev = _evidence()
        d = ev.to_dict()
        assert d["references"] == ["abc1234", "def5678"]
        assert isinstance(d["references"], list)

    def test_observed_value_serializes_to_plain_dict_and_list(self):
        ev = _evidence()
        d = ev.to_dict()
        assert d["observed_value"] == {"dirty": False, "files": ["a.py", "b.py"]}
        assert isinstance(d["observed_value"], dict)
        assert isinstance(d["observed_value"]["files"], list)

    def test_provenance_nested_dict(self):
        ev = _evidence()
        d = ev.to_dict()
        assert d["provenance"]["producer"] == "git_provider@v1"

    def test_round_trip_equal(self):
        ev = _evidence()
        restored = Evidence.from_dict(ev.to_dict())
        assert restored == ev

    def test_round_trip_preserves_enum_types(self):
        ev = _evidence()
        restored = Evidence.from_dict(ev.to_dict())
        assert restored.category is EvidenceCategory.GIT
        assert restored.freshness is EvidenceFreshness.CURRENT
        assert restored.confidence is EvidenceConfidence.HIGH
        assert restored.determinism is EvidenceDeterminism.DETERMINISTIC

    def test_json_dumps_and_loads_round_trip(self):
        ev = _evidence()
        text = json.dumps(ev.to_dict())
        restored = Evidence.from_dict(json.loads(text))
        assert restored == ev

    def test_json_compatible_with_expected_value_set(self):
        ev = _evidence(expected_value={"dirty": True})
        text = json.dumps(ev.to_dict())
        restored = Evidence.from_dict(json.loads(text))
        assert restored.expected_value == {"dirty": True}


class TestEvidenceCollectionSerialization:
    def test_to_dict_shape(self):
        collection = EvidenceCollection((_evidence("E-1"), _evidence("E-2")))
        d = collection.to_dict()
        assert list(d.keys()) == ["items"]
        assert len(d["items"]) == 2

    def test_round_trip_equal(self):
        collection = EvidenceCollection((_evidence("E-1"), _evidence("E-2")))
        restored = EvidenceCollection.from_dict(collection.to_dict())
        assert restored == collection

    def test_round_trip_preserves_order(self):
        collection = EvidenceCollection((_evidence("E-1"), _evidence("E-2"), _evidence("E-3")))
        restored = EvidenceCollection.from_dict(collection.to_dict())
        assert [e.evidence_id for e in restored] == ["E-1", "E-2", "E-3"]

    def test_json_dumps_and_loads_round_trip(self):
        collection = EvidenceCollection((_evidence("E-1"), _evidence("E-2")))
        text = json.dumps(collection.to_dict())
        restored = EvidenceCollection.from_dict(json.loads(text))
        assert restored == collection

    def test_empty_collection_round_trip(self):
        collection = EvidenceCollection()
        restored = EvidenceCollection.from_dict(collection.to_dict())
        assert restored == collection
        assert len(restored) == 0
