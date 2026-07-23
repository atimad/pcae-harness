"""Phase 143E: pcae.governance.inspection tests.

Covers the read-only inspection pipeline: positive fixtures inspect
successfully (including schema-legal adversarial fixtures, since
inspection is representation-only and never itself rejects a semantic
attack -- that is verification's job); malformed/non-CHGR artifacts fail
closed; inspection performs no mutation and no network access; results are
deterministic across repeated runs.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.governance.inspection import (
    InspectionFailure,
    InspectionObservation,
    inspect_artifact_at_path,
)

FIXTURES = Path(__file__).parent / "fixtures" / "chgr"


def _inspect(name: str):
    path = FIXTURES / name
    return inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())


@pytest.mark.parametrize("fixture_name", sorted(p.name for p in FIXTURES.glob("valid_*.json")))
def test_143e_valid_fixture_inspects_successfully(fixture_name):
    outcome = _inspect(fixture_name)
    assert isinstance(outcome, InspectionObservation), fixture_name


@pytest.mark.parametrize(
    "fixture_name",
    sorted(p.name for p in FIXTURES.glob("adversarial_*.json") if not p.name.endswith("_confirmation.json")),
)
def test_143e_adversarial_fixture_still_inspects_since_inspection_is_representation_only(fixture_name):
    outcome = _inspect(fixture_name)
    assert isinstance(outcome, InspectionObservation), fixture_name
    assert "does not establish" in outcome.disclosure


@pytest.mark.parametrize(
    "fixture_name",
    sorted(p.name for p in FIXTURES.glob("invalid_*.json")),
)
def test_143e_invalid_fixture_fails_inspection_closed(fixture_name):
    outcome = _inspect(fixture_name)
    assert isinstance(outcome, InspectionFailure), fixture_name


def test_143e_inspection_is_deterministic():
    a = _inspect("valid_record_published.json")
    b = _inspect("valid_record_published.json")
    assert a.to_dict() == b.to_dict()


def test_143e_inspection_never_mutates_input_bytes():
    path = FIXTURES / "valid_record_published.json"
    original = path.read_bytes()
    inspect_artifact_at_path(path, artifact_bytes=original)
    assert path.read_bytes() == original


def test_143e_inspection_never_mutates_repository(tmp_path, monkeypatch):
    before = sorted(FIXTURES.glob("*"))
    path = FIXTURES / "valid_record_published.json"
    inspect_artifact_at_path(path, artifact_bytes=path.read_bytes())
    after = sorted(FIXTURES.glob("*"))
    assert before == after


def test_143e_malformed_json_fails_closed():
    outcome = inspect_artifact_at_path(Path("nonexistent.json"), artifact_bytes=b"{not json")
    assert isinstance(outcome, InspectionFailure)
    assert outcome.outcome == "malformed_artifact"


def test_143e_non_chgr_json_fails_closed():
    outcome = inspect_artifact_at_path(Path("nonexistent.json"), artifact_bytes=b'{"foo": "bar"}')
    assert isinstance(outcome, InspectionFailure)


def test_143e_declared_fields_distinct_from_verified_status():
    """Inspection's own output must never claim a semantic fact was
    verified -- its 'validation' block must say verification: not_performed."""
    outcome = _inspect("valid_record_published.json")
    payload = outcome.to_dict()
    assert payload["validation"]["verification"] == "not_performed"
    assert payload["validation"]["authority"] == "not_performed"
