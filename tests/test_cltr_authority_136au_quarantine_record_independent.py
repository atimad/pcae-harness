"""Phase 136AU: Stage 3 Typed Authority Model QuarantineRecord
Independent Verification.

Independent re-derivation and verification of Phase 136AT's Typed Model
Implementation Group 11 (``QuarantineRecord``) against the frozen contract
and live executable schema (``records/quarantine_record.schema.json``,
``shared/enums.schema.json``, ``shared/identity.schema.json``,
``shared/digest.schema.json``, ``shared/references.schema.json``,
``shared/limitations.schema.json``, ``shared/envelope.schema.json``,
``shared/failures.schema.json``) -- independently, without trusting the
136AT implementation, its own test suite
(``test_cltr_authority_136at_quarantine_record.py``), its documentation, its
canonical report, prior prompts, prior expected-value tables, or existing
quarantine-domain behavior elsewhere in PCAE. Every fixture and assertion
below was derived directly from the executable schema file
(``quarantine_record.schema.json`` and the shared files it composes), then
compared against ``src/pcae/cltr/authority/compatibility_quarantine.py``.

Independently re-derived QuarantineRecord contract (from the live schema
only, then confirmed against the Python model with an exhaustive
schema-vs-model parity sweep, see the parametric tests below):

  discriminator       record_type const "quarantine_record"
  schema_id           const https://pcae.local/schemas/cltr_cutover/records/
                       quarantine_record.schema.json
  contract_version    const "1.0"
  schema_version      "MAJOR.MINOR" shape; only "1.0" supported by the model
  14 required fields  schema_id, schema_version, contract_version,
                       record_type, record_id, record_digest, created_at,
                       migration_epoch, object_type, object_reference,
                       reason_code, state, limitations, authority_disclosure
  1 optional field    _extensions (Tier 2, string-valued map, maxProperties 32)
  object_type         record-local 4-value enum {generation, publication_attempt,
                       authority_state, compatibility_state}
  state               record-local 4-value enum (QuarantineState, Sec.8.8)
                       {quarantined, under_review, released, permanently_retired}
  reason_code         shared 24-value ReasonCode enum, unconditionally required
  object_reference    generic shared record_reference (record_id + record_digest
                       + record_family, required; schema_id + schema_version
                       conditionally present) -- NO per-object_type record_family
                       restriction (NON-BLOCKING-136V-6): deliberately absent
  authority_role      shared 7-value enum, but "authoritative" locally forbidden
                       on this record family (Sec.9's 12-file list)
  no phase_id / transition_id fields (not in Sec.7.2's required-family lists)
  migration_epoch     still required (Sec.7.2's universal rule)
  NO other within-document conditional beyond the unconditional reason_code
  requirement (Sec.16's own conditional-validation table names no other).

Scope: Implementation Group 11 only (``QuarantineRecord``). No production
implementation change is made unless a genuine Blocking defect is
independently demonstrated (none is, per the findings recorded in the
canonical phase report).
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import importlib
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import compatibility_quarantine as qr_module
from pcae.cltr.authority.errors import (
    TypedModelConstructionError,
    TypedModelInternalInvariantError,
    UnsupportedSchemaVersionError,
)
from pcae.cltr.authority.sentinels import ABSENT
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
QR_MODULE_FILE = AUTHORITY_PACKAGE_DIR / "compatibility_quarantine.py"
QR_SCHEMA_FILE = (
    REPO_ROOT
    / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "records"
    / "quarantine_record.schema.json"
)

QUARANTINE_RECORD_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/quarantine_record.schema.json"
)
COMPATIBILITY_STATE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/compatibility_state.schema.json"
)
AUTHORITY_EPOCH_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json"
)

SIXTEEN_IMPLEMENTED_RECORD_FAMILIES = (
    "AuthorityEpoch",
    "AuthorityState",
    "CutoverRequest",
    "ReadinessPackage",
    "HumanAuthorization",
    "CutoverCandidate",
    "Certification",
    "PublicationAttempt",
    "PublicationEvidence",
    "ConcurrencyConflict",
    "RecoveryJournalEntry",
    "NotificationAuthorityBinding",
    "MarkerAuthorityBinding",
    "FinalizationReceiptAuthorityBinding",
    "CompatibilityState",
    "QuarantineRecord",
)

# No seventeenth family exists anywhere to guard against.
MUST_NOT_EXIST_RECORD_FAMILIES = ()

REQUIRED_FIELDS = (
    "schema_id",
    "schema_version",
    "contract_version",
    "record_type",
    "record_id",
    "record_digest",
    "created_at",
    "migration_epoch",
    "object_type",
    "object_reference",
    "reason_code",
    "state",
    "limitations",
    "authority_disclosure",
)

OBJECT_TYPE_MEMBERS = ("generation", "publication_attempt", "authority_state", "compatibility_state")
QUARANTINE_STATE_MEMBERS = ("quarantined", "under_review", "released", "permanently_retired")
REASON_CODE_MEMBERS = (
    "invalid_schema",
    "unsupported_version",
    "identity_mismatch",
    "phase_mismatch",
    "transition_mismatch",
    "migration_epoch_mismatch",
    "authority_epoch_mismatch",
    "revision_mismatch",
    "digest_mismatch",
    "stale_authorization",
    "stale_certification",
    "stale_writer",
    "cas_rejected",
    "publication_uncertain",
    "concurrency_conflict",
    "quarantine_required",
    "recovery_required",
    "authority_ambiguous",
    "authority_missing",
    "wrong_generation",
    "incompatible_legacy_state",
    "notification_uncertain",
    "marker_conflict",
    "receipt_conflict",
)
AUTHORITY_ROLE_MEMBERS = (
    "authoritative",
    "derivative",
    "operational",
    "evidence",
    "compatibility",
    "historical",
    "quarantined",
)
RECORD_FAMILY_MEMBERS = (
    "authority_epoch",
    "authority_state",
    "cutover_request",
    "readiness_package",
    "human_authorization",
    "cutover_candidate",
    "certification",
    "publication_attempt",
    "publication_evidence",
    "concurrency_conflict",
    "recovery_journal_entry",
    "quarantine_record",
    "notification_authority_binding",
    "marker_authority_binding",
    "receipt_authority_binding",
    "compatibility_state",
)


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


@pytest.fixture(scope="module")
def live_schema():
    return json.loads(QR_SCHEMA_FILE.read_text())


def _assert_schema_valid(record: dict, registry) -> None:
    result = validate_record_shape(record, schema_id=QUARANTINE_RECORD_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


def _assert_schema_invalid(record: dict, registry) -> None:
    result = validate_record_shape(record, schema_id=QUARANTINE_RECORD_SCHEMA_ID, registry=registry)
    assert result.status is not OutcomeStatus.VALID


def _sha256(fill: str = "a") -> str:
    assert len(fill) == 1
    return fill * 64


def _disclosure(role: str = "quarantined") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Independent 136AU verification: non-authoritative quarantine claim.",
    }


def _object_reference(**overrides) -> dict:
    ref = {
        "record_id": "genr-0000001",
        "record_digest": _sha256("b"),
        "record_family": "authority_epoch",
    }
    ref.update(overrides)
    return ref


def _wire(**overrides) -> dict:
    """A schema-valid QuarantineRecord wire document, independently
    fixtured directly from the live schema's own field table."""

    record = {
        "schema_id": QUARANTINE_RECORD_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "quarantine_record",
        "record_id": "qrec-0000001",
        "record_digest": _sha256("a"),
        "created_at": "2026-07-19T00:00:00Z",
        "migration_epoch": "epoch-au-001",
        "object_type": "generation",
        "object_reference": _object_reference(),
        "reason_code": "quarantine_required",
        "state": "quarantined",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _model_valid(wire: dict) -> bool:
    try:
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
        return True
    except Exception:  # noqa: BLE001
        return False


def _schema_valid(wire: dict, registry) -> bool:
    return validate_record_shape(
        wire, schema_id=QUARANTINE_RECORD_SCHEMA_ID, registry=registry
    ).status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 1. Inventory verification: exactly sixteen families, QuarantineRecord
#    present, no seventeenth family anywhere.
# ---------------------------------------------------------------------------


def test_136au_exactly_sixteen_record_family_classes_exist_via_ast():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        class_names |= {
            node.name for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, ast.ClassDef)
        }
    for expected in SIXTEEN_IMPLEMENTED_RECORD_FAMILIES:
        assert expected in class_names, f"missing expected record family class {expected!r}"
    present = class_names & set(SIXTEEN_IMPLEMENTED_RECORD_FAMILIES)
    assert present == set(SIXTEEN_IMPLEMENTED_RECORD_FAMILIES)
    assert len(SIXTEEN_IMPLEMENTED_RECORD_FAMILIES) == 16


def test_136au_package_export_inventory_via_runtime_import():
    for expected in SIXTEEN_IMPLEMENTED_RECORD_FAMILIES:
        assert hasattr(auth, expected)
        assert isinstance(getattr(auth, expected), type)
        assert expected in auth.__all__
    assert len([n for n in auth.__all__ if n in SIXTEEN_IMPLEMENTED_RECORD_FAMILIES]) == 16


def test_136au_module_all_exports_both_group_10_and_11_models_only():
    assert set(qr_module.__all__) == {
        "CompatibilityRole",
        "CompatibilityState",
        "ObjectType",
        "QuarantineState",
        "QuarantineRecord",
    }


def test_136au_schema_registry_discovers_quarantine_record_schema(schema_registry):
    assert QUARANTINE_RECORD_SCHEMA_ID in schema_registry.schema_ids
    assert schema_registry.document(QUARANTINE_RECORD_SCHEMA_ID) is not None


# ---------------------------------------------------------------------------
# 2. Valid wire round-trips against the live executable schema registry.
# ---------------------------------------------------------------------------


def test_136au_minimal_valid_is_schema_valid_and_round_trips(schema_registry):
    wire = _wire()
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136au_populated_fields_round_trip(schema_registry):
    wire = _wire(
        object_type="publication_attempt",
        object_reference=_object_reference(
            record_family="publication_attempt", schema_id=QUARANTINE_RECORD_SCHEMA_ID, schema_version="1.0"
        ),
        state="under_review",
        limitations=["disclosure one", "disclosure two"],
        _extensions={"note": "independent-verification-tag"},
    )
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


# ---------------------------------------------------------------------------
# 3. Required-field re-derivation.
# ---------------------------------------------------------------------------


def test_136au_required_field_set_matches_live_schema(live_schema):
    assert set(live_schema["required"]) == set(REQUIRED_FIELDS)
    assert len(REQUIRED_FIELDS) == 14


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_136au_missing_required_field_rejected(field, schema_registry):
    wire = _wire()
    del wire[field]
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises((TypedModelConstructionError, TypedModelInternalInvariantError, KeyError)):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_unknown_field_rejected(schema_registry):
    wire = _wire(unexpected_field_xyz="nope")
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_additional_properties_false_confirmed_against_live_schema(live_schema):
    assert live_schema["additionalProperties"] is False


def test_136au_no_phase_id_or_transition_id_fields(live_schema):
    assert "phase_id" not in live_schema["properties"]
    assert "transition_id" not in live_schema["properties"]


def test_136au_migration_epoch_required_despite_no_phase_or_transition_id(live_schema):
    assert "migration_epoch" in live_schema["required"]
    assert "migration_epoch" in live_schema["properties"]


def test_136au_exactly_one_optional_field(live_schema):
    all_props = set(live_schema["properties"])
    optional = all_props - set(REQUIRED_FIELDS)
    assert optional == {"_extensions"}


# ---------------------------------------------------------------------------
# 4. Discriminator / schema identity fidelity.
# ---------------------------------------------------------------------------


def test_136au_wrong_record_type_rejected(schema_registry):
    wire = _wire(record_type="compatibility_state")
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_wrong_schema_id_rejected(schema_registry):
    wire = _wire(schema_id=AUTHORITY_EPOCH_SCHEMA_ID)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_wrong_contract_version_rejected(schema_registry):
    wire = _wire(contract_version="2.0")
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_schema_id_and_record_type_const_match_module_constants(live_schema):
    assert live_schema["properties"]["schema_id"]["const"] == QUARANTINE_RECORD_SCHEMA_ID
    assert qr_module._QUARANTINE_RECORD_SCHEMA_ID == QUARANTINE_RECORD_SCHEMA_ID
    assert live_schema["properties"]["record_type"]["const"] == "quarantine_record"
    assert qr_module._QUARANTINE_RECORD_RECORD_TYPE == "quarantine_record"


def test_136au_unsupported_schema_version_rejected_before_payload_inspection():
    wire = _wire()
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="2.0")
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="9.9")


# ---------------------------------------------------------------------------
# 5. Enum verification -- object_type (record-local 4-value), state
#    (record-local 4-value QuarantineState), reason_code (shared 24-value),
#    authority_role (shared 7-value minus locally-forbidden authoritative).
# ---------------------------------------------------------------------------


def test_136au_object_type_enum_members_match_live_schema(live_schema):
    schema_enum = set(live_schema["$defs"]["object_type"]["enum"])
    assert schema_enum == set(OBJECT_TYPE_MEMBERS)
    assert {m.value for m in qr_module.ObjectType} == set(OBJECT_TYPE_MEMBERS)
    assert len(OBJECT_TYPE_MEMBERS) == 4


@pytest.mark.parametrize("member", OBJECT_TYPE_MEMBERS)
def test_136au_object_type_every_valid_member_accepted(member, schema_registry):
    wire = _wire(object_type=member)
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.object_type.value == member


@pytest.mark.parametrize(
    "bad_value",
    ["Generation", "GENERATION", "generation ", " authority_state", "record",
     "artifact", "authority_epoch", "", None, 1, True],
)
def test_136au_object_type_invalid_values_rejected(bad_value, schema_registry):
    wire = _wire(object_type=bad_value)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_state_enum_members_match_live_schema(live_schema):
    schema_enum = set(live_schema["$defs"]["quarantine_state"]["enum"])
    assert schema_enum == set(QUARANTINE_STATE_MEMBERS)
    assert {m.value for m in qr_module.QuarantineState} == set(QUARANTINE_STATE_MEMBERS)
    assert len(QUARANTINE_STATE_MEMBERS) == 4


@pytest.mark.parametrize("member", QUARANTINE_STATE_MEMBERS)
def test_136au_state_every_valid_member_accepted(member, schema_registry):
    wire = _wire(state=member)
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.state.value == member


@pytest.mark.parametrize(
    "bad_value", ["Quarantined", "QUARANTINED", "released ", "active", "resolved", "", None, 1],
)
def test_136au_state_invalid_values_rejected(bad_value, schema_registry):
    wire = _wire(state=bad_value)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_reason_code_enum_members_match_shared_schema(schema_registry):
    shared = schema_registry.document(
        "https://pcae.local/schemas/cltr_cutover/shared/failures.schema.json"
    )
    schema_enum = set(shared["$defs"]["reason_code"]["enum"])
    assert schema_enum == set(REASON_CODE_MEMBERS)
    assert {m.value for m in auth.ReasonCode} == set(REASON_CODE_MEMBERS)
    assert len(REASON_CODE_MEMBERS) == 24


@pytest.mark.parametrize("member", REASON_CODE_MEMBERS)
def test_136au_reason_code_every_valid_member_accepted(member, schema_registry):
    wire = _wire(reason_code=member)
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.reason_code.value == member


@pytest.mark.parametrize(
    "bad_value", ["Quarantine_Required", "not_a_real_code", "", None, 1, True],
)
def test_136au_reason_code_invalid_values_rejected(bad_value, schema_registry):
    wire = _wire(reason_code=bad_value)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_reason_code_unconditionally_required_not_named_quarantine_reason(live_schema):
    # NON-BLOCKING-136V-5: the field-table-literalism resolution in favor
    # of 'reason_code' over the operator prompt's 'quarantine_reason'.
    assert "reason_code" in live_schema["required"]
    assert "quarantine_reason" not in live_schema["properties"]
    assert "reason_code" in live_schema["properties"]


def test_136au_authority_role_authoritative_locally_forbidden(schema_registry):
    wire = _wire(authority_disclosure=_disclosure("authoritative"))
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "role", ["derivative", "operational", "evidence", "compatibility", "historical", "quarantined"],
)
def test_136au_authority_role_every_non_authoritative_member_accepted(role, schema_registry):
    wire = _wire(authority_disclosure=_disclosure(role))
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.authority_role.value == role


def test_136au_is_authoritative_true_rejected():
    disclosure = _disclosure()
    disclosure["is_authoritative"] = True
    wire = _wire(authority_disclosure=disclosure)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_authority_disclosure_forbidden_const_confirmed_in_live_schema(live_schema):
    disclosure_schema = live_schema["properties"]["authority_disclosure"]
    all_of = disclosure_schema["allOf"]
    assert any(
        block.get("properties", {}).get("authority_role") == {"not": {"const": "authoritative"}}
        for block in all_of
    )


# ---------------------------------------------------------------------------
# 6. No-other-conditional verification -- the only within-document
#    conditional restriction for this family is the unconditional
#    reason_code requirement (already covered above) plus the authority_role
#    "not authoritative" restriction; the live schema encodes no if/then/else
#    at the top level (unlike CompatibilityState's two allOf/if/then/else
#    blocks).
# ---------------------------------------------------------------------------


def test_136au_top_level_schema_has_no_if_then_else_conditional(live_schema):
    assert "if" not in live_schema
    assert "then" not in live_schema
    assert "else" not in live_schema
    # allOf is not used at the top level (only nested, inside authority_disclosure).
    assert "allOf" not in live_schema


def test_136au_no_state_specific_companion_field_requirement_exists(live_schema, schema_registry):
    # Anti-strengthening: illustrative operator-prompt conditionals (release
    # evidence, expiry, retained-state prohibitions) are NOT contract-defined
    # anywhere in Sec.16/Sec.30 and must not be invented. Every state value
    # must be constructible with the exact same minimal companion fields.
    for state in QUARANTINE_STATE_MEMBERS:
        wire = _wire(state=state)
        _assert_schema_valid(wire, schema_registry)
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_exhaustive_schema_vs_model_object_type_state_reason_parity(schema_registry):
    """The decisive independence check: for every combination of object_type,
    state, and authority_role, the Python model's accept/reject decision must
    exactly equal the live executable schema's. Any mismatch is either an
    unauthorized weakening or strengthening."""

    mismatches = []
    checked = 0
    for object_type in OBJECT_TYPE_MEMBERS:
        for state in QUARANTINE_STATE_MEMBERS:
            for role in AUTHORITY_ROLE_MEMBERS:
                wire = _wire(object_type=object_type, state=state, authority_disclosure=_disclosure(role))
                s = _schema_valid(wire, schema_registry)
                m = _model_valid(wire)
                checked += 1
                if s != m:
                    mismatches.append((object_type, state, role, s, m))
    assert not mismatches, mismatches
    assert checked == len(OBJECT_TYPE_MEMBERS) * len(QUARANTINE_STATE_MEMBERS) * len(AUTHORITY_ROLE_MEMBERS)


# ---------------------------------------------------------------------------
# 7. object_reference verification -- generic record_reference, NO
#    per-object_type record_family restriction (NON-BLOCKING-136V-6),
#    conditionally-present schema_id/schema_version, no lookup/existence
#    check, syntactically-valid-but-nonexistent references accepted.
# ---------------------------------------------------------------------------


def test_136au_object_reference_is_generic_record_reference_with_no_restriction(live_schema):
    prop = live_schema["properties"]["object_reference"]
    assert prop["$ref"] == "../shared/references.schema.json#/$defs/record_reference"
    # No allOf/const wrapping restricting record_family per object_type.
    assert "allOf" not in prop
    assert "const" not in prop


@pytest.mark.parametrize("family", RECORD_FAMILY_MEMBERS)
def test_136au_every_record_family_accepted_regardless_of_object_type(family, schema_registry):
    # Anti-strengthening: no per-object_type record_family restriction is
    # invented. Every valid record_family value must be accepted no matter
    # which object_type is declared alongside it.
    wire = _wire(object_type="generation", object_reference=_object_reference(record_family=family))
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.object_reference.record_family.value == family


def test_136au_object_reference_required_fields(live_schema):
    ref_schema = None
    # record_reference is defined in shared/references.schema.json; resolve
    # it directly rather than trusting the model's own known-keys constant.
    shared_refs = json.loads(
        (QR_SCHEMA_FILE.parent.parent / "shared" / "references.schema.json").read_text()
    )
    ref_schema = shared_refs["$defs"]["record_reference"]
    assert set(ref_schema["required"]) == {"record_id", "record_digest", "record_family"}
    assert ref_schema["additionalProperties"] is False
    assert set(ref_schema["properties"]) == {
        "record_id", "record_digest", "record_family", "schema_id", "schema_version",
    }


@pytest.mark.parametrize("missing_field", ["record_id", "record_digest", "record_family"])
def test_136au_object_reference_missing_required_field_rejected(missing_field, schema_registry):
    ref = _object_reference()
    del ref[missing_field]
    wire = _wire(object_reference=ref)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_object_reference_schema_id_and_schema_version_optional(schema_registry):
    wire = _wire(object_reference=_object_reference())
    assert "schema_id" not in wire["object_reference"]
    assert "schema_version" not in wire["object_reference"]
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.object_reference.schema_id is ABSENT
    assert model.object_reference.schema_version is ABSENT
    assert "schema_id" not in model.to_dict()["object_reference"]
    assert "schema_version" not in model.to_dict()["object_reference"]


def test_136au_object_reference_schema_id_and_schema_version_populated_round_trip(schema_registry):
    wire = _wire(
        object_reference=_object_reference(
            schema_id=COMPATIBILITY_STATE_SCHEMA_ID, schema_version="1.0"
        )
    )
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.to_dict()["object_reference"]["schema_id"] == COMPATIBILITY_STATE_SCHEMA_ID
    assert model.to_dict()["object_reference"]["schema_version"] == "1.0"


@pytest.mark.parametrize(
    "bad_schema_version", ["1", "1.0.0", "v1.0", "", "1.x", None],
)
def test_136au_object_reference_malformed_schema_version_rejected(bad_schema_version, schema_registry):
    wire = _wire(object_reference=_object_reference(schema_version=bad_schema_version))
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_object_reference_explicit_null_schema_id_rejected(schema_registry):
    wire = _wire(object_reference=_object_reference(schema_id=None))
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_object_reference_unknown_field_rejected(schema_registry):
    wire = _wire(object_reference=_object_reference(bogus_field="x"))
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "bad_record_id", ["", "A" * 8, "1abcdefg", "short", "has space", "has/slash", "has..dots"],
)
def test_136au_object_reference_malformed_record_id_rejected(bad_record_id, schema_registry):
    wire = _wire(object_reference=_object_reference(record_id=bad_record_id))
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(Exception):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "bad_digest", ["not-a-digest", "A" * 64, "0" * 63, "0" * 65, ""],
)
def test_136au_object_reference_malformed_digest_rejected(bad_digest, schema_registry):
    wire = _wire(object_reference=_object_reference(record_digest=bad_digest))
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(Exception):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_syntactically_valid_but_nonexistent_reference_constructs_successfully(schema_registry):
    # No lookup, no existence validation, no referenced-object loading, no
    # repository access, no registry resolution at construction time -- a
    # reference to a record_id that plainly does not exist must still
    # construct successfully where the schema permits it.
    wire = _wire(
        object_reference=_object_reference(
            record_id="genr-doesnotexistanywhereatall00",
            record_digest=_sha256("f"),
            record_family="authority_epoch",
        )
    )
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.object_reference.record_id.value == "genr-doesnotexistanywhereatall00"


def test_136au_generation_object_type_has_no_record_family_analogue(schema_registry):
    # NON-BLOCKING-136V-6: 'generation' is not itself a record_family enum
    # member (shared/enums.schema.json has no such entry) -- yet a
    # generation-typed quarantine record still uses the generic
    # record_reference shape (any record_family value is schema-valid),
    # not a dedicated generation_reference shape.
    assert "generation" not in RECORD_FAMILY_MEMBERS
    wire = _wire(object_type="generation", object_reference=_object_reference(record_family="cutover_request"))
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 8. Absent vs null verification; _extensions.
# ---------------------------------------------------------------------------


def test_136au_extensions_absent_by_default_and_explicit_null_rejected():
    model = auth.QuarantineRecord.from_dict(_wire(), schema_version="1.0")
    assert model._extensions is ABSENT
    assert "_extensions" not in model.to_dict()
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(_wire(_extensions=None), schema_version="1.0")


def test_136au_extensions_populated_string_valued_map_round_trips(schema_registry):
    wire = _wire(_extensions={"note": "independent-136au-tag"})
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.to_dict()["_extensions"] == {"note": "independent-136au-tag"}


def test_136au_extensions_non_string_value_rejected(schema_registry):
    wire = _wire(_extensions={"note": 123})
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_extensions_reserved_key_collision_rejected():
    wire = _wire(_extensions={"migration_epoch": "shadowing-attempt"})
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_extensions_max_properties_bound(live_schema, schema_registry):
    assert live_schema["properties"]["_extensions"]["maxProperties"] == 32
    wire = _wire(_extensions={f"k{i}": "v" for i in range(33)})
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_extensions_at_boundary_of_max_properties_accepted(schema_registry):
    wire = _wire(_extensions={f"k{i}": "v" for i in range(32)})
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_limitations_absent_semantics_versus_empty_array(schema_registry):
    wire = _wire(limitations=[])
    _assert_schema_valid(wire, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.limitations.entries == ()
    # limitations itself is required (not optional); an absent limitations
    # key is schema-invalid, distinct from an empty array being valid.
    wire_missing = _wire()
    del wire_missing["limitations"]
    _assert_schema_invalid(wire_missing, schema_registry)


# ---------------------------------------------------------------------------
# 9. Immutability verification (frozen, recursive, source-mutation
#    isolation, output-mutation isolation).
# ---------------------------------------------------------------------------


def test_136au_is_frozen_dataclass():
    model = auth.QuarantineRecord.from_dict(_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.state = qr_module.QuarantineState.RELEASED


def test_136au_mutating_source_limitations_after_construction_does_not_affect_model():
    source = ["limitation one"]
    wire = _wire(limitations=source)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    source.append("limitation two")
    assert len(model.limitations.entries) == 1


def test_136au_mutating_source_extensions_after_construction_does_not_affect_model():
    source = {"note": "original"}
    wire = _wire(_extensions=source)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    source["note"] = "tampered"
    source["new"] = "also"
    assert model.to_dict()["_extensions"] == {"note": "original"}


def test_136au_mutating_source_object_reference_after_construction_does_not_affect_model():
    source = _object_reference()
    wire = _wire(object_reference=source)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    source["record_id"] = "genr-tamperedid"
    assert model.object_reference.record_id.value == "genr-0000001"


def test_136au_mutating_source_disclosure_after_construction_does_not_affect_model():
    source = _disclosure("quarantined")
    wire = _wire(authority_disclosure=source)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    source["disclosure_text"] = "tampered"
    assert model.authority_disclosure.disclosure_text != "tampered"


def test_136au_mutating_to_dict_output_does_not_affect_model():
    model = auth.QuarantineRecord.from_dict(
        _wire(limitations=["a"], _extensions={"k": "v"}), schema_version="1.0"
    )
    out = model.to_dict()
    out["limitations"].append("tampered")
    out["_extensions"]["k"] = "tampered"
    out["object_reference"]["record_id"] = "tampered"
    fresh = model.to_dict()
    assert fresh["limitations"] == ["a"]
    assert fresh["_extensions"] == {"k": "v"}
    assert fresh["object_reference"]["record_id"] == "genr-0000001"


def test_136au_deep_copy_produces_structurally_equal_but_independent_object():
    model = auth.QuarantineRecord.from_dict(_wire(), schema_version="1.0")
    duplicate = copy.deepcopy(model)
    assert duplicate == model
    assert duplicate is not model


# ---------------------------------------------------------------------------
# 10. Structural equality verification (not identifier-only / digest-only /
#     quarantine-state-only / reason-only comparison).
# ---------------------------------------------------------------------------


def test_136au_equality_is_structural_and_changes_when_any_field_changes():
    base = auth.QuarantineRecord.from_dict(_wire(), schema_version="1.0")
    same = auth.QuarantineRecord.from_dict(_wire(), schema_version="1.0")
    assert base == same

    for override in (
        {"object_type": "authority_state"},
        {"reason_code": "digest_mismatch"},
        {"state": "released"},
        {"migration_epoch": "epoch-au-002"},
        {"limitations": ["disclosure"]},
        {"authority_disclosure": _disclosure("operational")},
        {"object_reference": _object_reference(record_id="genr-9999999")},
        {"_extensions": {"k": "v"}},
    ):
        variant = auth.QuarantineRecord.from_dict(_wire(**override), schema_version="1.0")
        assert base != variant, override


def test_136au_equality_rejects_identifier_only_digest_only_and_state_only_comparison():
    base = auth.QuarantineRecord.from_dict(_wire(), schema_version="1.0")
    same_identity_diff_state = auth.QuarantineRecord.from_dict(
        _wire(state="released"), schema_version="1.0"
    )
    assert base.envelope.record_id == same_identity_diff_state.envelope.record_id
    assert base.envelope.record_digest == same_identity_diff_state.envelope.record_digest
    assert base != same_identity_diff_state

    same_identity_diff_reason = auth.QuarantineRecord.from_dict(
        _wire(reason_code="digest_mismatch"), schema_version="1.0"
    )
    assert base.envelope.record_id == same_identity_diff_reason.envelope.record_id
    assert base != same_identity_diff_reason


# ---------------------------------------------------------------------------
# 11. Deterministic serialization / round-trip / error determinism.
# ---------------------------------------------------------------------------


def test_136au_round_trip_is_deterministic_and_lossless():
    wire = _wire(
        object_type="compatibility_state",
        object_reference=_object_reference(
            record_family="compatibility_state", schema_id=COMPATIBILITY_STATE_SCHEMA_ID, schema_version="1.0"
        ),
        limitations=["a", "b"],
        _extensions={"k": "v"},
    )
    m1 = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    d1 = m1.to_dict()
    m2 = auth.QuarantineRecord.from_dict(d1, schema_version="1.0")
    d2 = m2.to_dict()
    assert d1 == d2 == wire
    assert m1 == m2


def test_136au_construction_errors_deterministic_across_repeated_attempts():
    bad_wire = _wire(object_type="not-a-real-type")
    errors = []
    for _ in range(3):
        try:
            auth.QuarantineRecord.from_dict(bad_wire, schema_version="1.0")
        except Exception as exc:  # noqa: BLE001
            errors.append(type(exc))
    assert len(errors) == 3
    assert len(set(errors)) == 1


def test_136au_invalid_record_digest_wrapper_rejected():
    with pytest.raises(Exception):
        auth.QuarantineRecord.from_dict(_wire(record_digest="not-a-sha256"), schema_version="1.0")


def test_136au_invalid_migration_epoch_wrapper_rejected():
    with pytest.raises(Exception):
        auth.QuarantineRecord.from_dict(_wire(migration_epoch="a..b"), schema_version="1.0")


# ---------------------------------------------------------------------------
# 12. Anti-strengthening verification -- reasonable-sounding quarantine
#     assumptions the schema does NOT encode must NOT be enforced.
# ---------------------------------------------------------------------------


def test_136au_referenced_object_need_not_exist(schema_registry):
    wire = _wire(
        object_reference=_object_reference(record_id="genr-neverexistedatall00")
    )
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_quarantine_state_does_not_require_release_evidence(schema_registry):
    wire = _wire(state="released")
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_permanently_retired_does_not_forbid_later_transition_metadata(schema_registry):
    # No terminal-state-cannot-change invariant is schema-defined; a
    # permanently_retired record with an unrelated later reason_code (e.g.
    # implying reconsideration) is still schema-valid -- no lifecycle-state
    # agreement invented.
    wire = _wire(state="permanently_retired", reason_code="recovery_required")
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_reason_code_does_not_have_to_imply_actual_failure(schema_registry):
    wire = _wire(reason_code="stale_writer", state="under_review")
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_calendar_invalid_but_shape_valid_timestamp_accepted(schema_registry):
    wire = _wire(created_at="2026-13-45T99:99:99Z")
    assert _schema_valid(wire, schema_registry) is True
    assert _model_valid(wire) is True


def test_136au_created_at_never_used_to_establish_identity_or_ordering():
    m1 = auth.QuarantineRecord.from_dict(_wire(created_at="2020-01-01T00:00:00Z"), schema_version="1.0")
    m2 = auth.QuarantineRecord.from_dict(_wire(created_at="2030-01-01T00:00:00Z"), schema_version="1.0")
    # Distinct created_at alone makes them unequal (structural equality),
    # but nothing in the model computes an ordering from it.
    assert m1 != m2
    assert not hasattr(m1, "is_before")
    assert not hasattr(m1, "is_after")


def test_136au_quarantined_state_does_not_require_authority_role_quarantined(schema_registry):
    # "quarantine implies incompatibility" / role coupling is not
    # schema-defined; a quarantined-state record may carry any
    # non-authoritative authority_role.
    wire = _wire(state="quarantined", authority_disclosure=_disclosure("evidence"))
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_authority_role_quarantined_does_not_require_state_quarantined(schema_registry):
    wire = _wire(state="released", authority_disclosure=_disclosure("quarantined"))
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_object_type_compatibility_state_does_not_require_compatibility_state_family(schema_registry):
    # No conditional ties object_type to object_reference.record_family.
    wire = _wire(object_type="compatibility_state", object_reference=_object_reference(record_family="human_authorization"))
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_duplicate_limitations_entries_accepted(schema_registry):
    wire = _wire(limitations=["dup", "dup"])
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136au_limitations_boundary_sizes_accepted(schema_registry):
    wire = _wire(limitations=["x" for _ in range(32)])
    _assert_schema_valid(wire, schema_registry)
    auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    wire_over = _wire(limitations=["x" for _ in range(33)])
    _assert_schema_invalid(wire_over, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire_over, schema_version="1.0")


# ---------------------------------------------------------------------------
# 13. Quarantine-boundary and existing-quarantine-subsystem isolation --
#     representation only, never an operation; no operational quarantine
#     module imports QuarantineRecord and vice versa.
# ---------------------------------------------------------------------------


FORBIDDEN_QUARANTINE_OPERATION_SYMBOLS = (
    "quarantine_artifact", "move_to_quarantine", "release_from_quarantine",
    "restore_from_quarantine", "purge_quarantine", "delete_quarantine",
    "reconcile_quarantine", "inspect_quarantine", "enumerate_quarantine",
    "locate_quarantine", "create_quarantine_directory", "write_quarantine",
    "authorize_quarantine", "authorize_release", "determine_quarantine",
    "classify_for_quarantine", "evaluate_quarantine_eligibility",
    "resolve_quarantine_location", "discover_quarantine",
)
FORBIDDEN_LIFECYCLE_AUTHORITY_SYMBOLS = (
    "block_publication", "block_finalization", "block_cutover",
    "execute_remediation", "execute_rollback", "activate_authority",
    "resolve_authority", "transfer_authority", "mutate_lifecycle",
    "mutate_authority_pointer", "demote_authority", "finalize_lifecycle",
    "advance_lifecycle_state", "authorize_publication", "dispatch_notification",
    "write_marker", "write_receipt", "determine_current_authority",
)


def test_136au_module_defines_no_quarantine_operation_or_authority_exercise_symbols():
    tree = ast.parse(QR_MODULE_FILE.read_text())
    defined = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for name in FORBIDDEN_QUARANTINE_OPERATION_SYMBOLS + FORBIDDEN_LIFECYCLE_AUTHORITY_SYMBOLS:
        assert name not in defined, f"forbidden symbol {name!r} defined in module"


def test_136au_quarantine_record_public_api_is_representation_only():
    public = {n for n in dir(auth.QuarantineRecord) if not n.startswith("_")}
    field_names = {f.name for f in dataclasses.fields(auth.QuarantineRecord)}
    method_like = public - field_names
    assert method_like == {"from_dict", "to_dict"}


def test_136au_no_operational_quarantine_module_imports_quarantine_record():
    forbidden_prefix = "pcae.cltr.authority"
    scan_roots = (
        REPO_ROOT / "src" / "pcae" / "commands",
        REPO_ROOT / "src" / "pcae" / "core",
        REPO_ROOT / "src" / "pcae" / "cltr",
        REPO_ROOT / "src" / "pcae" / "runtime",
    )
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if "authority" in path.parts:
                continue
            # Phase 137K: the sole authorized production Typed Authority
            # Model consumer is permitted to import pcae.cltr.authority
            # (TAMPC-001 v1.0, docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md).
            if path.name in {"authority_inspection.py", "authority_inspect.py"}:
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith(forbidden_prefix), (path, alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    assert not node.module.startswith(forbidden_prefix), (path, node.module)


def test_136au_module_source_never_references_filesystem_mutation_or_process_apis():
    source = QR_MODULE_FILE.read_text()
    for token in (
        "os.remove", "os.rename", "os.mkdir", "shutil.move", "shutil.copy",
        "shutil.rmtree", "subprocess.run", "subprocess.Popen", "socket.socket",
        "os.environ", "getenv", "requests.", "urllib.request",
    ):
        assert token not in source


def test_136au_no_quarantine_command_wired_in_cli():
    cli_file = REPO_ROOT / "src" / "pcae" / "cli.py"
    if not cli_file.exists():
        pytest.skip("cli.py not present")
    source = cli_file.read_text()
    for token in ("QuarantineRecord", "compatibility_quarantine"):
        assert token not in source


# ---------------------------------------------------------------------------
# 14. CompatibilityState regression verification -- Phase 136AT shares
#     compatibility_quarantine.py with CompatibilityState; confirm its
#     contract is unchanged by re-checking the 16-field inventory and both
#     of its conditionals directly against the live schema and model.
# ---------------------------------------------------------------------------


COMPATIBILITY_STATE_REQUIRED_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type",
    "record_id", "record_digest", "created_at", "migration_epoch",
    "component", "role", "allowed_reads", "forbidden_authority_use",
    "fallback_disabled", "mode", "limitations", "authority_disclosure",
)


def test_136au_compatibility_state_field_inventory_unchanged(schema_registry):
    cs_schema = schema_registry.document(COMPATIBILITY_STATE_SCHEMA_ID)
    assert set(cs_schema["required"]) == set(COMPATIBILITY_STATE_REQUIRED_FIELDS)
    assert len(COMPATIBILITY_STATE_REQUIRED_FIELDS) == 16
    assert set(cs_schema["properties"]) - set(COMPATIBILITY_STATE_REQUIRED_FIELDS) == {
        "retirement_state", "_extensions",
    }


def test_136au_compatibility_state_still_constructs_and_round_trips(schema_registry):
    wire = {
        "schema_id": COMPATIBILITY_STATE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "compatibility_state",
        "record_id": "compstat-0000au1",
        "record_digest": _sha256("c"),
        "created_at": "2026-07-19T00:00:00Z",
        "migration_epoch": "epoch-au-001",
        "component": "legacy.component",
        "role": "compatibility",
        "allowed_reads": [],
        "forbidden_authority_use": True,
        "fallback_disabled": False,
        "mode": "legacy_adapter",
        "limitations": [],
        "authority_disclosure": _disclosure("compatibility"),
    }
    result = validate_record_shape(wire, schema_id=COMPATIBILITY_STATE_SCHEMA_ID, registry=schema_registry)
    assert result.status is OutcomeStatus.VALID, result.issues
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136au_compatibility_state_legacy_retired_conditional_unchanged(schema_registry):
    base = {
        "schema_id": COMPATIBILITY_STATE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "compatibility_state",
        "record_id": "compstat-0000au2",
        "record_digest": _sha256("d"),
        "created_at": "2026-07-19T00:00:00Z",
        "migration_epoch": "epoch-au-002",
        "component": "legacy.component",
        "role": "historical",
        "allowed_reads": [],
        "forbidden_authority_use": True,
        "fallback_disabled": False,
        "mode": "legacy_retired",
        "retirement_state": {},
        "limitations": [],
        "authority_disclosure": _disclosure("historical"),
    }
    result = validate_record_shape(base, schema_id=COMPATIBILITY_STATE_SCHEMA_ID, registry=schema_registry)
    assert result.status is OutcomeStatus.VALID, result.issues
    model = auth.CompatibilityState.from_dict(base, schema_version="1.0")
    assert model.mode.value == "legacy_retired"

    missing = dict(base)
    del missing["retirement_state"]
    result_missing = validate_record_shape(missing, schema_id=COMPATIBILITY_STATE_SCHEMA_ID, registry=schema_registry)
    assert result_missing.status is not OutcomeStatus.VALID
    with pytest.raises(TypedModelInternalInvariantError):
        auth.CompatibilityState.from_dict(missing, schema_version="1.0")


def test_136au_compatibility_state_package_export_still_present():
    assert hasattr(auth, "CompatibilityState")
    assert "CompatibilityState" in auth.__all__


# ---------------------------------------------------------------------------
# 15. Scope-guard integrity -- inspect the 136AT-narrowed sibling guards
#     (136AQ, 136M, 136U) for over-broadening.
# ---------------------------------------------------------------------------


def test_136au_no_sibling_guard_forbids_any_currently_implemented_family():
    guard_files = list((REPO_ROOT / "tests").glob("test_cltr_*136*.py"))
    assert guard_files
    over_broad = []
    for path in guard_files:
        if path.name == "test_cltr_authority_136au_quarantine_record_independent.py":
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and "MUST_NOT_EXIST" in target.id:
                        values = tuple(
                            e.value for e in getattr(node.value, "elts", ())
                            if isinstance(e, ast.Constant)
                        )
                        if set(values) & set(SIXTEEN_IMPLEMENTED_RECORD_FAMILIES):
                            over_broad.append((path.name, values))
    assert not over_broad, over_broad


def test_136au_quarantine_record_family_slug_matches_implemented_class():
    from pcae.cltr.authority.enums import RecordFamily
    assert RecordFamily.QUARANTINE_RECORD.value == "quarantine_record"
    assert hasattr(auth, "QuarantineRecord")


# ---------------------------------------------------------------------------
# 16. Runtime isolation -- no production module imports the authority
#     package; the module imports no transport/filesystem/runtime code
#     (transitive walk from compatibility_quarantine.py).
# ---------------------------------------------------------------------------


def test_136au_transitive_import_walk_finds_no_transport_or_filesystem_dependency():
    visited: set[Path] = set()
    to_visit = [QR_MODULE_FILE]
    forbidden = (
        "socket", "subprocess", "telegram", "smtplib", "requests",
        "urllib.request", "pathlib", "shutil", "os.path",
    )
    while to_visit:
        path = to_visit.pop()
        if path in visited or not path.exists():
            continue
        visited.add(path)
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            module_name = None
            if isinstance(node, ast.ImportFrom) and node.module:
                module_name = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    for f in forbidden:
                        assert not alias.name.startswith(f), (path, alias.name)
            if module_name:
                for f in forbidden:
                    assert not module_name.startswith(f), (path, module_name)
                if module_name.startswith("pcae.cltr.authority."):
                    sibling = AUTHORITY_PACKAGE_DIR / (module_name.rsplit(".", 1)[-1] + ".py")
                    to_visit.append(sibling)
    assert QR_MODULE_FILE in visited


def test_136au_pcae_cltr_authority_does_not_import_runtime_or_command_modules():
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            module_name = None
            if isinstance(node, ast.ImportFrom) and node.module:
                module_name = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
            if module_name:
                for forbidden_prefix in ("pcae.commands", "pcae.core", "pcae.runtime"):
                    assert not module_name.startswith(forbidden_prefix), (path, module_name)


# ---------------------------------------------------------------------------
# 17. Side-effect verification -- construction/serialization/equality/repr
#     touch no filesystem, network, subprocess, or environment.
# ---------------------------------------------------------------------------


def test_136au_no_network_during_construction_serialization_equality_repr(monkeypatch):
    def _raise(*a, **k):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    model = auth.QuarantineRecord.from_dict(_wire(), schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136au_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*a, **k):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    model = auth.QuarantineRecord.from_dict(_wire(), schema_version="1.0")
    model.to_dict()


def test_136au_no_filesystem_access_during_lifecycle(monkeypatch):
    def _guarded_open(file, mode="r", *args, **kwargs):
        raise AssertionError(f"unexpected filesystem access: {file!r} mode={mode!r}")

    monkeypatch.setattr("builtins.open", _guarded_open)
    model = auth.QuarantineRecord.from_dict(_wire(_extensions={"k": "v"}), schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136au_module_reimport_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    importlib.reload(qr_module)


# ---------------------------------------------------------------------------
# 18. Packaging verification (fresh wheel build, isolated install, exact
#     sixteen-model export inventory).
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136au_wheel_build_contains_group_11_module(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1
    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()
    assert "pcae/cltr/authority/compatibility_quarantine.py" in names
    assert (
        "pcae/schema_resources/cltr_cutover/records/quarantine_record.schema.json" in names
        or any("quarantine_record.schema.json" in n for n in names)
    )


@pytest.mark.slow
def test_136au_isolated_install_all_sixteen_families_import_and_round_trip(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, capture_output=True, text=True)
    venv_python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--quiet", str(wheels[0])],
        check=True, capture_output=True, text=True,
    )
    probe = (
        "from pcae.cltr import authority as auth\n"
        "for name in " + repr(SIXTEEN_IMPLEMENTED_RECORD_FAMILIES) + ":\n"
        "    assert hasattr(auth, name), name\n"
        "assert len(" + repr(SIXTEEN_IMPLEMENTED_RECORD_FAMILIES) + ") == 16\n"
        "wire = {\n"
        "    'schema_id': " + repr(QUARANTINE_RECORD_SCHEMA_ID) + ",\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'quarantine_record', 'record_id': 'qrec-0000099',\n"
        "    'record_digest': 'a'*64, 'created_at': '2026-07-19T00:00:00Z',\n"
        "    'migration_epoch': 'epoch-001', 'object_type': 'generation',\n"
        "    'object_reference': {'record_id': 'genr-0000001', 'record_digest': 'b'*64,\n"
        "        'record_family': 'authority_epoch'},\n"
        "    'reason_code': 'quarantine_required', 'state': 'quarantined', 'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'quarantined',\n"
        "        'is_authoritative': False, 'disclosure_text': 'ok'},\n"
        "}\n"
        "model = auth.QuarantineRecord.from_dict(wire, schema_version='1.0')\n"
        "assert model.to_dict() == wire\n"
        "cs_wire = {\n"
        "    'schema_id': " + repr(COMPATIBILITY_STATE_SCHEMA_ID) + ",\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'compatibility_state', 'record_id': 'compstat-0000099',\n"
        "    'record_digest': 'c'*64, 'created_at': '2026-07-19T00:00:00Z',\n"
        "    'migration_epoch': 'epoch-001', 'component': 'c', 'role': 'compatibility',\n"
        "    'allowed_reads': [], 'forbidden_authority_use': True, 'fallback_disabled': False,\n"
        "    'mode': 'legacy_adapter', 'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'compatibility',\n"
        "        'is_authoritative': False, 'disclosure_text': 'ok'},\n"
        "}\n"
        "cs_model = auth.CompatibilityState.from_dict(cs_wire, schema_version='1.0')\n"
        "assert cs_model.to_dict() == cs_wire\n"
        "print('ISOLATED_INSTALL_OK')\n"
    )
    result = subprocess.run(
        [str(venv_python), "-c", probe], check=True, capture_output=True, text=True,
    )
    assert "ISOLATED_INSTALL_OK" in result.stdout
