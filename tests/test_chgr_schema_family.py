"""Phase 143E: CHGR schema family shape tests.

Covers: every implemented schema validates a correct synthetic fixture;
malformed artifacts fail closed; required fields/enums/formats are
enforced; unknown schema versions are structurally permitted at Layer 2
(version *support* is a verification-layer concern, per
schema_runtime's own layering) but shape-checked; schema references
resolve fully offline.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.schema_resources import chgr_root
from pcae.schema_runtime import (
    OutcomeStatus,
    build_offline_registry,
    load_and_verify_manifest,
    validate_record_shape,
)

FIXTURES = Path(__file__).parent / "fixtures" / "chgr"
_MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/chgr/manifest.schema.json"


def _registry():
    with chgr_root() as root:
        return build_offline_registry(root), root


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


VALID_FIXTURES = sorted(p.name for p in FIXTURES.glob("valid_*.json"))
INVALID_FIXTURES = sorted(p.name for p in FIXTURES.glob("invalid_*.json") if p.name != "invalid_phase_report_substitution.json")


def test_143e_registry_loads_all_six_record_schemas_offline():
    registry, _ = _registry()
    record_schema_ids = [sid for sid in registry.schema_ids if "/records/" in sid]
    assert len(record_schema_ids) == 6


def test_143e_manifest_verifies_completely():
    registry, root = _registry()
    manifest = load_and_verify_manifest(
        root / "manifest.json",
        package_root=root,
        registry=registry,
        manifest_schema_id=_MANIFEST_SCHEMA_ID,
        excluded_relative_paths=frozenset({"manifest.schema.json"}),
    )
    assert len(manifest.entries) == 12


@pytest.mark.parametrize("fixture_name", VALID_FIXTURES)
def test_143e_valid_fixture_validates(fixture_name):
    registry, _ = _registry()
    doc = _load(fixture_name)
    result = validate_record_shape(doc, schema_id=doc["schema_id"], registry=registry)
    assert result.status is OutcomeStatus.VALID, (fixture_name, result.issues)


@pytest.mark.parametrize("fixture_name", INVALID_FIXTURES)
def test_143e_invalid_fixture_fails_closed(fixture_name):
    registry, _ = _registry()
    doc = _load(fixture_name)
    schema_id = doc.get("schema_id", "https://pcae.local/schemas/chgr/records/human_governance_record.schema.json")
    result = validate_record_shape(doc, schema_id=schema_id, registry=registry)
    assert result.status is not OutcomeStatus.VALID, fixture_name


def test_143e_no_schema_permits_is_authoritative_field():
    """No CHGR schema may accept a bare is_authoritative field anywhere
    (structural prevention of automatic-authority-by-flag)."""
    registry, root = _registry()
    for schema_file in sorted((root / "records").glob("*.schema.json")):
        text = schema_file.read_text()
        assert '"is_authoritative"' not in text, schema_file.name


def test_143e_no_decision_template_option_permits_default_or_preferred_field():
    doc = _load("valid_template.json")
    registry, _ = _registry()
    for forbidden in ("default", "preferred", "recommended"):
        mutated = json.loads(json.dumps(doc))
        mutated["options"][0][forbidden] = True
        result = validate_record_shape(mutated, schema_id=doc["schema_id"], registry=registry)
        assert result.status is not OutcomeStatus.VALID, forbidden


def test_143e_empty_options_array_rejected():
    doc = _load("valid_template.json")
    doc["options"] = []
    registry, _ = _registry()
    result = validate_record_shape(doc, schema_id=doc["schema_id"], registry=registry)
    assert result.status is not OutcomeStatus.VALID


def test_143e_missing_eligible_authority_rejected():
    doc = _load("valid_template.json")
    del doc["eligible_authority"]
    registry, _ = _registry()
    result = validate_record_shape(doc, schema_id=doc["schema_id"], registry=registry)
    assert result.status is not OutcomeStatus.VALID


def test_143e_lifecycle_state_enum_accepts_exactly_eight_frozen_states():
    doc = _load("valid_record_published.json")
    registry, _ = _registry()
    states = [
        "draft",
        "awaiting-human-confirmation",
        "confirmed",
        "published",
        "suspended",
        "superseded",
        "revoked",
        "invalidated",
    ]
    for state in states:
        mutated = json.loads(json.dumps(doc))
        mutated["lifecycle_state"] = state
        # suspended/revoked need their evidence refs to remain schema-legal
        # under this package's own additionalProperties:false closure --
        # they're optional fields, so omitting them is still schema-valid
        # here (structural legality is a verification-layer, not schema,
        # concern, per governance/verification.py's LIFECYCLE_INCONSISTENT).
        result = validate_record_shape(mutated, schema_id=doc["schema_id"], registry=registry)
        assert result.status is OutcomeStatus.VALID, state

    mutated = json.loads(json.dumps(doc))
    mutated["lifecycle_state"] = "not_a_real_state"
    result = validate_record_shape(mutated, schema_id=doc["schema_id"], registry=registry)
    assert result.status is not OutcomeStatus.VALID


def test_143e_assurance_level_enum_accepts_l0_through_l5_and_rejects_unknown():
    doc = _load("valid_confirmation_evidence.json")
    registry, _ = _registry()
    for level in ("L0", "L1", "L2", "L3", "L4", "L5"):
        mutated = json.loads(json.dumps(doc))
        mutated["achieved_assurance_level"] = level
        result = validate_record_shape(mutated, schema_id=doc["schema_id"], registry=registry)
        assert result.status is OutcomeStatus.VALID, level

    mutated = json.loads(json.dumps(doc))
    mutated["achieved_assurance_level"] = "L9"
    result = validate_record_shape(mutated, schema_id=doc["schema_id"], registry=registry)
    assert result.status is not OutcomeStatus.VALID
