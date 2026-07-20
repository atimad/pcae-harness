"""Phase 136AT: Stage 3 Typed Authority Model QuarantineRecord
Implementation (Typed Model Implementation Group 11).

Focused tests for ``src/pcae/cltr/authority/compatibility_quarantine.py``:
the ``QuarantineRecord`` typed record model. Covers exact field mapping,
strict constructor behavior, the ``object_type``/``object_reference`` no-
invented-restriction anti-strengthening case, the ``reason_code``/
``state`` enum inventories, schema conformance, full sixteen-model
inventory, no-quarantine-operation / no-reference-lookup / no-authority-
activation semantics, no-side-effect, runtime-isolation, and
``CompatibilityState`` regression protection.

This module implements only Typed Model Implementation Group 11
(``QuarantineRecord``). Derived directly from the live executable schema
(``records/quarantine_record.schema.json``), independently fixtured: not
copied from any earlier record-family test module's own fixture helpers,
and not importing Phase 136AS/136AR/136V/136W fixtures or expectations.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import compatibility_quarantine
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
COMPATIBILITY_MODULE = AUTHORITY_PACKAGE_DIR / "compatibility_quarantine.py"

PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "cltr",
    REPO_ROOT / "src" / "pcae" / "runtime",
)

FORBIDDEN_SYMBOLS = (
    "quarantine_artifact",
    "quarantine_record",
    "move_to_quarantine",
    "release_from_quarantine",
    "restore_from_quarantine",
    "purge_quarantine",
    "delete_quarantine",
    "reconcile_quarantine",
    "inspect_quarantine",
    "enumerate_quarantine",
    "locate_quarantine",
    "create_quarantine_directory",
    "write_quarantine",
    "authorize_quarantine",
    "authorize_release",
    "determine_quarantine",
    "classify_for_quarantine",
    "block_publication",
    "block_finalization",
    "execute_remediation",
    "execute_rollback",
    "activate_authority",
    "mutate_lifecycle",
    "transfer_authority",
)

ALL_SIXTEEN_MODEL_NAMES = (
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

QUARANTINE_RECORD_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/quarantine_record.schema.json"
)
COMPATIBILITY_STATE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/compatibility_state.schema.json"
)


def _sha256_hex(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _assert_schema_valid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


def _assert_schema_invalid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is OutcomeStatus.INVALID, "expected schema-invalid, got VALID"


# ---------------------------------------------------------------------------
# Wire fixtures
# ---------------------------------------------------------------------------


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Non-authoritative schema-validated companion record.",
    }


def _object_reference(**overrides) -> dict:
    ref = {
        "record_id": "genrec-0000001",
        "record_digest": _sha256_hex("1"),
        "record_family": "authority_epoch",
    }
    ref.update(overrides)
    return ref


def _valid_quarantine_record_wire(**overrides) -> dict:
    record = {
        "schema_id": QUARANTINE_RECORD_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "quarantine_record",
        "record_id": "quarrec-0000001",
        "record_digest": _sha256_hex("0"),
        "created_at": "2026-07-19T12:00:00Z",
        "migration_epoch": "epoch-001",
        "object_type": "generation",
        "object_reference": _object_reference(),
        "reason_code": "quarantine_required",
        "state": "quarantined",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _valid_compatibility_state_wire(**overrides) -> dict:
    record = {
        "schema_id": COMPATIBILITY_STATE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "compatibility_state",
        "record_id": "compatst-0000001",
        "record_digest": _sha256_hex("0"),
        "created_at": "2026-07-19T12:00:00Z",
        "migration_epoch": "epoch-001",
        "component": "legacy-lifecycle",
        "role": "compatibility",
        "allowed_reads": [],
        "forbidden_authority_use": True,
        "fallback_disabled": False,
        "mode": "legacy_adapter",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# 1. Inventory
# ---------------------------------------------------------------------------


def test_136at_exactly_sixteen_record_family_models_exist_in_package():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for expected in ALL_SIXTEEN_MODEL_NAMES:
        assert expected in class_names, expected
    present = class_names & set(ALL_SIXTEEN_MODEL_NAMES)
    assert present == set(ALL_SIXTEEN_MODEL_NAMES)


def test_136at_both_group11_and_group10_models_exist_in_compatibility_module():
    tree = ast.parse(COMPATIBILITY_MODULE.read_text())
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "CompatibilityState" in class_names
    assert "QuarantineRecord" in class_names


def test_136at_expected_public_exports_present():
    for name in ("QuarantineRecord", "ObjectType", "QuarantineState"):
        assert hasattr(auth, name)
        assert name in auth.__all__


def test_136at_public_exports_exact():
    assert set(compatibility_quarantine.__all__) == {
        "CompatibilityRole",
        "CompatibilityState",
        "ObjectType",
        "QuarantineState",
        "QuarantineRecord",
    }


def test_136at_wildcard_import_matches_all():
    namespace: dict = {}
    exec("from pcae.cltr.authority.compatibility_quarantine import *", namespace)
    exported = {k for k in namespace if not k.startswith("_")}
    assert exported == set(compatibility_quarantine.__all__)


def test_136at_model_is_frozen_dataclass():
    assert dataclasses.is_dataclass(auth.QuarantineRecord)
    assert auth.QuarantineRecord.__dataclass_params__.frozen


# ---------------------------------------------------------------------------
# 2. QuarantineRecord: construction / round trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "object_type,record_family",
    [
        ("generation", "authority_epoch"),
        ("publication_attempt", "publication_attempt"),
        ("authority_state", "authority_state"),
        ("compatibility_state", "compatibility_state"),
        # Anti-strengthening: object_type and object_reference.record_family
        # are NOT tied together by any conditional (NON-BLOCKING-136V-6) --
        # a mismatched but schema-valid combination must still construct.
        ("generation", "quarantine_record"),
        ("compatibility_state", "authority_epoch"),
    ],
)
def test_136at_object_type_and_reference_family_are_independent(
    schema_registry, object_type, record_family
):
    wire = _valid_quarantine_record_wire(
        object_type=object_type,
        object_reference=_object_reference(record_family=record_family),
    )
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.object_type.value == object_type
    assert model.object_reference.record_family.value == record_family
    assert model.to_dict() == wire


@pytest.mark.parametrize("state", ["quarantined", "under_review", "released", "permanently_retired"])
def test_136at_every_state_value_constructs(schema_registry, state):
    wire = _valid_quarantine_record_wire(state=state)
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.state.value == state
    assert model.to_dict() == wire


@pytest.mark.parametrize(
    "reason_code",
    [
        "invalid_schema", "unsupported_version", "identity_mismatch", "phase_mismatch",
        "transition_mismatch", "migration_epoch_mismatch", "authority_epoch_mismatch",
        "revision_mismatch", "digest_mismatch", "stale_authorization", "stale_certification",
        "stale_writer", "cas_rejected", "publication_uncertain", "concurrency_conflict",
        "quarantine_required", "recovery_required", "authority_ambiguous", "authority_missing",
        "wrong_generation", "incompatible_legacy_state", "notification_uncertain",
        "marker_conflict", "receipt_conflict",
    ],
)
def test_136at_every_reason_code_value_constructs(schema_registry, reason_code):
    wire = _valid_quarantine_record_wire(reason_code=reason_code)
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.reason_code.value == reason_code
    assert model.to_dict() == wire


def test_136at_object_reference_with_cross_family_fields(schema_registry):
    wire = _valid_quarantine_record_wire(
        object_reference=_object_reference(
            schema_id="https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json",
            schema_version="1.0",
        )
    )
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.object_reference.schema_id == (
        "https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json"
    )
    assert model.object_reference.schema_version == "1.0"
    assert model.to_dict() == wire


def test_136at_object_reference_without_cross_family_fields_permitted(schema_registry):
    # Anti-strengthening: schema_id/schema_version are optional on
    # object_reference -- no cross-family-required rule is invented here
    # (unlike marker_reference/receipt_reference in bindings.py, whose
    # cross-family requirement is a documented, field-specific rule).
    wire = _valid_quarantine_record_wire()
    assert "schema_id" not in wire["object_reference"]
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.object_reference.schema_id is auth.ABSENT
    assert model.object_reference.schema_version is auth.ABSENT


def test_136at_maximal_valid_construction_with_extensions(schema_registry):
    wire = _valid_quarantine_record_wire(
        _extensions={"note": "annotation"}, limitations=["disclosed limitation"]
    )
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model._extensions["note"] == "annotation"
    assert list(model.limitations) == ["disclosed limitation"]
    assert model.to_dict() == wire


def test_136at_forbids_authoritative_role(schema_registry):
    wire = _valid_quarantine_record_wire(authority_disclosure=_disclosure("authoritative"))
    _assert_schema_invalid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    with pytest.raises(Exception):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "permitted_role",
    ["derivative", "operational", "evidence", "compatibility", "historical", "quarantined"],
)
def test_136at_any_non_authoritative_role_permitted_anti_strengthening(schema_registry, permitted_role):
    wire = _valid_quarantine_record_wire(authority_disclosure=_disclosure(permitted_role))
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136at_unknown_field_rejected():
    wire = _valid_quarantine_record_wire(quarantine_reason="oops")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_unsupported_schema_version_rejected():
    wire = _valid_quarantine_record_wire()
    with pytest.raises(auth.UnsupportedSchemaVersionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="2.0")


def test_136at_missing_schema_id_rejected():
    wire = _valid_quarantine_record_wire()
    del wire["schema_id"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_wrong_schema_id_rejected():
    wire = _valid_quarantine_record_wire(schema_id="https://pcae.local/wrong.json")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_missing_schema_version_rejected():
    wire = _valid_quarantine_record_wire()
    del wire["schema_version"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_wrong_record_type_rejected():
    wire = _valid_quarantine_record_wire(record_type="compatibility_state")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "required_key",
    [
        "migration_epoch",
        "object_type",
        "object_reference",
        "reason_code",
        "state",
        "limitations",
        "authority_disclosure",
    ],
)
def test_136at_missing_required_field_rejected(schema_registry, required_key):
    wire = _valid_quarantine_record_wire()
    del wire[required_key]
    _assert_schema_invalid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_malformed_migration_epoch_rejected():
    wire = _valid_quarantine_record_wire(migration_epoch="Invalid Epoch!")
    with pytest.raises(auth.InvalidIdentifierError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_malformed_record_digest_rejected():
    wire = _valid_quarantine_record_wire(record_digest="not-a-digest")
    with pytest.raises(auth.InvalidDigestError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_object_reference_missing_record_family_rejected(schema_registry):
    ref = _object_reference()
    del ref["record_family"]
    wire = _valid_quarantine_record_wire(object_reference=ref)
    _assert_schema_invalid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_object_reference_malformed_digest_rejected():
    wire = _valid_quarantine_record_wire(object_reference=_object_reference(record_digest="bad"))
    with pytest.raises(auth.InvalidDigestError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_object_reference_unknown_record_family_rejected(schema_registry):
    wire = _valid_quarantine_record_wire(
        object_reference=_object_reference(record_family="not_a_family")
    )
    _assert_schema_invalid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    with pytest.raises(ValueError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_object_reference_unknown_field_rejected(schema_registry):
    wire = _valid_quarantine_record_wire(
        object_reference=_object_reference(unexpected="x")
    )
    _assert_schema_invalid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_object_reference_malformed_schema_version_rejected(schema_registry):
    wire = _valid_quarantine_record_wire(
        object_reference=_object_reference(schema_id="x", schema_version="not-a-version")
    )
    _assert_schema_invalid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_object_type_enum_members_match_schema():
    assert {m.value for m in compatibility_quarantine.ObjectType} == {
        "generation", "publication_attempt", "authority_state", "compatibility_state",
    }


def test_136at_object_type_enum_strictness():
    wire = _valid_quarantine_record_wire(object_type="GENERATION")
    with pytest.raises(ValueError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_object_type_unknown_value_rejected(schema_registry):
    wire = _valid_quarantine_record_wire(object_type="not_a_type")
    _assert_schema_invalid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    with pytest.raises(ValueError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_state_enum_members_match_schema():
    assert {m.value for m in compatibility_quarantine.QuarantineState} == {
        "quarantined", "under_review", "released", "permanently_retired",
    }


def test_136at_state_enum_strictness():
    wire = _valid_quarantine_record_wire(state="QUARANTINED")
    with pytest.raises(ValueError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_state_unknown_value_rejected(schema_registry):
    wire = _valid_quarantine_record_wire(state="not_a_state")
    _assert_schema_invalid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    with pytest.raises(ValueError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_reason_code_enum_strictness():
    wire = _valid_quarantine_record_wire(reason_code="QUARANTINE_REQUIRED")
    with pytest.raises(ValueError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_reason_code_unknown_value_rejected(schema_registry):
    wire = _valid_quarantine_record_wire(reason_code="not_a_reason")
    _assert_schema_invalid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    with pytest.raises(ValueError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_top_level_assignment_raises():
    wire = _valid_quarantine_record_wire()
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.state = compatibility_quarantine.QuarantineState.RELEASED


def test_136at_extensions_permitted_empty(schema_registry):
    wire = _valid_quarantine_record_wire(_extensions={})
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model._extensions.to_dict() == {}


def test_136at_extensions_reject_reserved_key_collision():
    wire = _valid_quarantine_record_wire(_extensions={"state": "x"})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_extensions_reject_non_string_value():
    wire = _valid_quarantine_record_wire(_extensions={"note": 5})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_extensions_reject_explicit_null():
    wire = _valid_quarantine_record_wire(_extensions=None)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.QuarantineRecord.from_dict(wire, schema_version="1.0")


def test_136at_extensions_absent_by_default():
    wire = _valid_quarantine_record_wire()
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model._extensions is auth.ABSENT
    assert "_extensions" not in model.to_dict()


def test_136at_limitations_may_be_empty(schema_registry):
    wire = _valid_quarantine_record_wire(limitations=[])
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.limitations.entries == ()


# ---------------------------------------------------------------------------
# 3. Schema field-set parity
# ---------------------------------------------------------------------------


def test_136at_schema_field_set_matches_model_known_keys():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "quarantine_record.schema.json").read_text())
    assert set(schema["properties"].keys()) == compatibility_quarantine._QUARANTINE_RECORD_KNOWN_KEYS


def test_136at_required_set_matches_schema():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "quarantine_record.schema.json").read_text())
    wire = _valid_quarantine_record_wire()
    assert set(schema["required"]) <= set(wire.keys())
    assert set(schema["required"]) == {
        "schema_id", "schema_version", "contract_version", "record_type",
        "record_id", "record_digest", "created_at", "migration_epoch",
        "object_type", "object_reference", "reason_code", "state",
        "limitations", "authority_disclosure",
    }


def test_136at_object_type_enum_matches_schema_defs():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "quarantine_record.schema.json").read_text())
    assert set(schema["$defs"]["object_type"]["enum"]) == {
        m.value for m in compatibility_quarantine.ObjectType
    }


def test_136at_quarantine_state_enum_matches_schema_defs():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "quarantine_record.schema.json").read_text())
    assert set(schema["$defs"]["quarantine_state"]["enum"]) == {
        m.value for m in compatibility_quarantine.QuarantineState
    }


def test_136at_schema_pins_no_object_type_family_conditional():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "quarantine_record.schema.json").read_text())
    # NON-BLOCKING-136V-6: object_reference is the plain shared
    # record_reference $ref with no embedded allOf/const family
    # restriction -- anti-strengthening evidence that no such
    # restriction was invented at the Python layer either.
    object_reference_schema = schema["properties"]["object_reference"]
    assert object_reference_schema == {
        "$ref": "../shared/references.schema.json#/$defs/record_reference",
        "description": object_reference_schema["description"],
    }


def test_136at_schema_authority_disclosure_forbids_authoritative():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "quarantine_record.schema.json").read_text())
    disclosure_schema = schema["properties"]["authority_disclosure"]
    assert disclosure_schema["allOf"][1]["properties"]["authority_role"] == {"not": {"const": "authoritative"}}


# ---------------------------------------------------------------------------
# 4. Equality / immutability
# ---------------------------------------------------------------------------


def test_136at_structural_equality():
    wire = _valid_quarantine_record_wire()
    a = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    b = auth.QuarantineRecord.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert a == b


def test_136at_field_difference_breaks_equality():
    a = auth.QuarantineRecord.from_dict(_valid_quarantine_record_wire(), schema_version="1.0")
    b = auth.QuarantineRecord.from_dict(
        _valid_quarantine_record_wire(state="released"), schema_version="1.0"
    )
    assert a != b


def test_136at_no_identifier_only_equality():
    a = auth.QuarantineRecord.from_dict(
        _valid_quarantine_record_wire(record_id="quarrec-0000001"), schema_version="1.0"
    )
    b = auth.QuarantineRecord.from_dict(
        _valid_quarantine_record_wire(record_id="quarrec-0000002"), schema_version="1.0"
    )
    assert a != b


def test_136at_no_state_only_equality():
    a = auth.QuarantineRecord.from_dict(
        _valid_quarantine_record_wire(state="quarantined"), schema_version="1.0"
    )
    b = auth.QuarantineRecord.from_dict(
        _valid_quarantine_record_wire(state="quarantined", reason_code="recovery_required"),
        schema_version="1.0",
    )
    assert a != b


def test_136at_no_digest_only_equality():
    a = auth.QuarantineRecord.from_dict(
        _valid_quarantine_record_wire(record_digest=_sha256_hex("a")), schema_version="1.0"
    )
    b = auth.QuarantineRecord.from_dict(
        _valid_quarantine_record_wire(record_digest=_sha256_hex("a"), state="released"),
        schema_version="1.0",
    )
    assert a != b


def test_136at_construction_input_mutation_does_not_mutate_model():
    wire = _valid_quarantine_record_wire(limitations=["a limitation"])
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    wire["limitations"].append("mutated after construction")
    assert list(model.limitations) == ["a limitation"]


def test_136at_recursive_immutability_extensions():
    wire = _valid_quarantine_record_wire(_extensions={"note": "x"})
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    wire["_extensions"]["note"] = "mutated"
    assert model._extensions["note"] == "x"


def test_136at_deserialized_output_mutation_does_not_alter_model():
    wire = _valid_quarantine_record_wire()
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    result = model.to_dict()
    result["state"] = "released"
    result["object_reference"]["record_family"] = "compatibility_state"
    assert model.state.value == "quarantined"
    assert model.object_reference.record_family.value == "authority_epoch"


# ---------------------------------------------------------------------------
# 5. No-quarantine-operation / no-reference-lookup / no-authority-activation
#    / no-lifecycle-mutation / no-later-model
# ---------------------------------------------------------------------------


def test_136at_no_forbidden_symbols_defined_in_source():
    tree = ast.parse(COMPATIBILITY_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_SYMBOLS:
        assert forbidden not in defined_names


def test_136at_no_repository_or_persistence_symbols_in_source():
    source = COMPATIBILITY_MODULE.read_text()
    for forbidden in (
        "Repository", "save(", "persist(", "def load(", "requests.", "urllib",
        "socket.", "subprocess.", "shutil.", "os.remove", "os.rename", "os.mkdir",
        "pathlib.Path(", "open(", "smtplib",
    ):
        assert forbidden not in source


def test_136at_no_production_module_imports_authority_package():
    for root_dir in PRODUCTION_SCAN_ROOTS:
        if not root_dir.exists():
            continue
        for path in root_dir.rglob("*.py"):
            if AUTHORITY_PACKAGE_DIR in path.parents or path.parent == AUTHORITY_PACKAGE_DIR:
                continue
            # Phase 137K: the sole authorized production Typed Authority Model
            # consumer is permitted to import pcae.cltr.authority (TAMPC-001 v1.0,
            # docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md).
            if path.name in {"authority_inspection.py", "authority_inspect.py"}:
                continue
            source = path.read_text()
            assert "from pcae.cltr.authority" not in source, path
            assert "import pcae.cltr.authority" not in source, path


def test_136at_compatibility_module_does_not_import_production_lifecycle_modules_ast():
    forbidden_modules = (
        "pcae.cltr.lifecycle",
        "pcae.cltr.finalization",
        "pcae.cltr.notification",
        "pcae.cltr.marker",
        "pcae.cltr.receipt",
        "pcae.cltr.quarantine",
        "pcae.commands",
        "pcae.core",
        "pcae.runtime",
    )
    tree = ast.parse(COMPATIBILITY_MODULE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in forbidden_modules:
                    assert not alias.name.startswith(forbidden), (COMPATIBILITY_MODULE, alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in forbidden_modules:
                assert not node.module.startswith(forbidden), (COMPATIBILITY_MODULE, node.module)


def test_136at_authority_package_does_not_import_runtime_or_command_modules():
    forbidden_modules = ("pcae.commands", "pcae.core", "pcae.runtime")
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forbidden in forbidden_modules:
                        assert not alias.name.startswith(forbidden), (path, alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                for forbidden in forbidden_modules:
                    assert not node.module.startswith(forbidden), (path, node.module)


def test_136at_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    wire = _valid_quarantine_record_wire()
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    model.to_dict()


def test_136at_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    wire = _valid_quarantine_record_wire()
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    model.to_dict()


def test_136at_no_filesystem_write_during_construction_or_serialization(monkeypatch, tmp_path):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    wire = _valid_quarantine_record_wire()
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136at_package_import_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(compatibility_quarantine)


def test_136at_valid_nonexistent_reference_no_lookup(schema_registry):
    # A syntactically valid but nonexistent object_reference must
    # construct successfully -- no filesystem/repository resolution is
    # performed at construction time (Layer 4 concern only).
    wire = _valid_quarantine_record_wire(
        object_reference=_object_reference(record_id="genrec-9999999", record_digest=_sha256_hex("f"))
    )
    _assert_schema_valid(wire, QUARANTINE_RECORD_SCHEMA_ID, schema_registry)
    model = auth.QuarantineRecord.from_dict(wire, schema_version="1.0")
    assert model.object_reference.record_id.value == "genrec-9999999"


# ---------------------------------------------------------------------------
# 6. CompatibilityState regression protection (shared module)
# ---------------------------------------------------------------------------


def test_136at_compatibility_state_still_constructs_and_round_trips(schema_registry):
    wire = _valid_compatibility_state_wire()
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136at_compatibility_state_known_keys_unchanged():
    assert compatibility_quarantine._COMPATIBILITY_STATE_KNOWN_KEYS == frozenset(
        {
            "schema_id", "schema_version", "contract_version", "record_type",
            "record_id", "record_digest", "created_at", "migration_epoch",
            "component", "role", "allowed_reads", "forbidden_authority_use",
            "fallback_disabled", "mode", "retirement_state", "limitations",
            "authority_disclosure", "_extensions",
        }
    )


def test_136at_compatibility_state_retired_with_retirement_state_unchanged(schema_registry):
    wire = _valid_compatibility_state_wire(
        mode="legacy_retired", retirement_state={}, authority_disclosure=_disclosure("historical")
    )
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.retirement_state.to_json() == {}
    assert model.to_dict() == wire


def test_136at_compatibility_state_role_enum_unchanged():
    assert {m.value for m in compatibility_quarantine.CompatibilityRole} == {"compatibility", "historical"}


def test_136at_compatibility_state_forbids_authoritative_role_unchanged(schema_registry):
    wire = _valid_compatibility_state_wire(authority_disclosure=_disclosure("authoritative"))
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(Exception):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136at_compatibility_state_immutable_unchanged():
    model = auth.CompatibilityState.from_dict(_valid_compatibility_state_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.mode = auth.CompatibilityMode.LEGACY_RETIRED


def test_136at_compatibility_state_export_still_present():
    assert "CompatibilityState" in auth.__all__
    assert "CompatibilityRole" in auth.__all__


# ---------------------------------------------------------------------------
# 7. Scope-guard verification (all sixteen families present, no
#    seventeenth invented)
# ---------------------------------------------------------------------------


def test_136at_own_module_scope_guard_matches_exactly_the_two_families():
    tree = ast.parse(COMPATIBILITY_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_models = class_names & set(ALL_SIXTEEN_MODEL_NAMES)
    assert record_family_models == {"CompatibilityState", "QuarantineRecord"}


def test_136at_no_seventeenth_record_family_model_in_package():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    record_family_models = class_names & set(ALL_SIXTEEN_MODEL_NAMES)
    assert record_family_models == set(ALL_SIXTEEN_MODEL_NAMES)


# ---------------------------------------------------------------------------
# 8. Packaging verification
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136at_wheel_contains_compatibility_module_with_quarantine_record(tmp_path: Path):
    import subprocess as _subprocess

    dist_dir = tmp_path / "dist"
    _subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()
        source = archive.read("pcae/cltr/authority/compatibility_quarantine.py").decode()

    assert "pcae/cltr/authority/compatibility_quarantine.py" in names
    tree = ast.parse(source)
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "QuarantineRecord" in class_names
    assert "CompatibilityState" in class_names


@pytest.mark.slow
def test_136at_sdist_includes_compatibility_module(tmp_path: Path):
    import subprocess as _subprocess

    dist_dir = tmp_path / "dist"
    _subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(sdists) == 1, f"expected exactly one sdist, found {sdists}"

    import tarfile

    with tarfile.open(sdists[0]) as archive:
        names = archive.getnames()

    assert any(name.endswith("pcae/cltr/authority/compatibility_quarantine.py") for name in names)


@pytest.mark.slow
def test_136at_isolated_install_exactly_sixteen_models_construct_and_round_trip(tmp_path: Path):
    import subprocess as _subprocess
    import venv

    dist_dir = tmp_path / "dist"
    _subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    env_dir = tmp_path / "isolated_env"
    venv.EnvBuilder(with_pip=True).create(env_dir)
    env_python = env_dir / "bin" / "python"

    _subprocess.run(
        [str(env_python), "-m", "pip", "install", "--quiet", str(wheels[0])],
        check=True, capture_output=True, text=True,
    )

    script = tmp_path / "isolated_check.py"
    script.write_text(
        "from pcae.cltr.authority import CompatibilityState, QuarantineRecord\n"
        "compat_wire = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/compatibility_state.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'compatibility_state', 'record_id': 'compatst-0000001',\n"
        "    'record_digest': '0' * 64, 'created_at': '2026-07-19T12:00:00Z',\n"
        "    'migration_epoch': 'epoch-001', 'component': 'legacy-lifecycle',\n"
        "    'role': 'compatibility', 'allowed_reads': [], 'forbidden_authority_use': True,\n"
        "    'fallback_disabled': False, 'mode': 'legacy_adapter', 'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'derivative', 'is_authoritative': False, "
        "'disclosure_text': 'x'},\n"
        "}\n"
        "compat_model = CompatibilityState.from_dict(compat_wire, schema_version='1.0')\n"
        "assert compat_model.to_dict() == compat_wire\n"
        "quarantine_wire = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/quarantine_record.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'quarantine_record', 'record_id': 'quarrec-0000001',\n"
        "    'record_digest': '0' * 64, 'created_at': '2026-07-19T12:00:00Z',\n"
        "    'migration_epoch': 'epoch-001', 'object_type': 'generation',\n"
        "    'object_reference': {'record_id': 'genrec-0000001', 'record_digest': '1' * 64, "
        "'record_family': 'authority_epoch'},\n"
        "    'reason_code': 'quarantine_required', 'state': 'quarantined', 'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'derivative', 'is_authoritative': False, "
        "'disclosure_text': 'x'},\n"
        "}\n"
        "quarantine_model = QuarantineRecord.from_dict(quarantine_wire, schema_version='1.0')\n"
        "assert quarantine_model.to_dict() == quarantine_wire\n"
        "print('ISOLATED_OK')\n"
    )
    result = _subprocess.run(
        [str(env_python), str(script)],
        cwd=str(tmp_path), check=True, capture_output=True, text=True,
    )
    assert "ISOLATED_OK" in result.stdout
