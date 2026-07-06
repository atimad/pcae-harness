"""Phase 115C: Repository Evidence Framework Prototype.

Tests immutable ``Evidence`` construction, field access, provenance
exposure, and reference handling implemented in
``src/pcae/core/evidence.py``. This module is disconnected by design --
not called by the Repository Transition Validator, any Decision
Framework, lifecycle command, or notification path. These tests call it
directly.
"""
from __future__ import annotations

import dataclasses

import pytest

from pcae.core.evidence import (
    Evidence,
    EvidenceCategory,
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


def _evidence(**overrides) -> Evidence:
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
        references=("abc1234",),
        observed_value={"dirty": False},
        explanation="Working tree is clean.",
        provenance=_provenance(),
    )
    base.update(overrides)
    return Evidence(**base)


class TestEvidenceConstruction:
    def test_constructs_with_all_required_fields(self):
        ev = _evidence()
        assert ev.evidence_id == "E-git-001"
        assert ev.source == "Git"
        assert ev.category == EvidenceCategory.GIT
        assert ev.producer == "git_provider"
        assert ev.timestamp_utc == "2026-07-06T00:00:00Z"
        assert ev.freshness == EvidenceFreshness.CURRENT
        assert ev.confidence == EvidenceConfidence.HIGH
        assert ev.determinism == EvidenceDeterminism.DETERMINISTIC
        assert ev.scope == "repo"
        assert ev.references == ("abc1234",)
        assert ev.observed_value == {"dirty": False}
        assert ev.explanation == "Working tree is clean."

    def test_expected_value_defaults_to_none(self):
        ev = _evidence()
        assert ev.expected_value is None

    def test_limitations_defaults_to_empty_string(self):
        ev = _evidence()
        assert ev.limitations == ""

    def test_expected_value_and_limitations_can_be_set(self):
        ev = _evidence(expected_value={"dirty": True}, limitations="No CI signal available.")
        assert ev.expected_value == {"dirty": True}
        assert ev.limitations == "No CI signal available."

    def test_accepts_raw_string_enum_values(self):
        ev = _evidence(
            category="git",
            freshness="current",
            confidence="high",
            determinism="deterministic",
        )
        assert ev.category is EvidenceCategory.GIT
        assert ev.freshness is EvidenceFreshness.CURRENT
        assert ev.confidence is EvidenceConfidence.HIGH
        assert ev.determinism is EvidenceDeterminism.DETERMINISTIC

    def test_references_coerced_to_tuple(self):
        ev = _evidence(references=["a", "b", "c"])
        assert ev.references == ("a", "b", "c")
        assert isinstance(ev.references, tuple)


class TestEvidenceImmutability:
    def test_field_reassignment_raises(self):
        ev = _evidence()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ev.evidence_id = "E-other"

    def test_explanation_reassignment_raises(self):
        ev = _evidence()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ev.explanation = "changed"

    def test_observed_value_dict_is_read_only(self):
        ev = _evidence(observed_value={"dirty": False})
        with pytest.raises(TypeError):
            ev.observed_value["dirty"] = True

    def test_expected_value_dict_is_read_only(self):
        ev = _evidence(expected_value={"dirty": True})
        with pytest.raises(TypeError):
            ev.expected_value["dirty"] = False

    def test_mutating_caller_supplied_dict_after_construction_does_not_alias(self):
        source = {"dirty": False}
        ev = _evidence(observed_value=source)
        source["dirty"] = True
        assert ev.observed_value["dirty"] is False

    def test_mutating_caller_supplied_references_list_after_construction_does_not_alias(self):
        source = ["a", "b"]
        ev = _evidence(references=source)
        source.append("c")
        assert ev.references == ("a", "b")

    def test_nested_list_inside_observed_value_is_frozen(self):
        ev = _evidence(observed_value={"files": ["a.py", "b.py"]})
        assert ev.observed_value["files"] == ("a.py", "b.py")
        with pytest.raises(AttributeError):
            ev.observed_value["files"].append("c.py")


class TestEvidenceProvenance:
    def test_provenance_exposed_on_evidence(self):
        ev = _evidence()
        assert isinstance(ev.provenance, EvidenceProvenance)
        assert ev.provenance.producer == "git_provider@v1"
        assert ev.provenance.produced_from == "git status --porcelain"
        assert ev.provenance.timestamp == "2026-07-06T00:00:00Z"
        assert ev.provenance.deterministic_origin is True

    def test_provenance_is_frozen(self):
        ev = _evidence()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ev.provenance.producer = "other"

    def test_deterministic_origin_can_be_false(self):
        prov = _provenance(deterministic_origin=False)
        assert prov.deterministic_origin is False


class TestEvidenceReference:
    def test_constructs_with_evidence_id_only(self):
        ref = EvidenceReference(evidence_id="E-git-001")
        assert ref.evidence_id == "E-git-001"
        assert ref.note is None

    def test_constructs_with_optional_note(self):
        ref = EvidenceReference(evidence_id="E-git-001", note="cited by phase_identity_consistency")
        assert ref.note == "cited by phase_identity_consistency"

    def test_is_frozen(self):
        ref = EvidenceReference(evidence_id="E-git-001")
        with pytest.raises(dataclasses.FrozenInstanceError):
            ref.evidence_id = "E-other"
