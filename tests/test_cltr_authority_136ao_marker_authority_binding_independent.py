"""Phase 136AO: Stage 3 Typed Authority Model Marker Authority Binding
Independent Verification.

Independent re-derivation and verification of Phase 136AN's Typed Model
Implementation Group 8 (``MarkerAuthorityBinding``) against the frozen
contract and live executable schema
(``records/marker_authority_binding.schema.json``,
``shared/references.schema.json``, ``shared/digest.schema.json``,
``shared/identity.schema.json``, ``shared/limitations.schema.json``,
``shared/envelope.schema.json``, ``shared/enums.schema.json``) --
independently, without trusting the 136AN implementation, its own test
suite, its report, its comments, or any prior verification report. Every
fixture and assertion below was derived directly from the executable
schema file and the frozen contract text quoted in its ``description``
fields, then compared against ``src/pcae/cltr/authority/bindings.py``.

Scope: Implementation Group 8 only (``MarkerAuthorityBinding``). No later
record-family model (``FinalizationReceiptAuthorityBinding``,
``CompatibilityState``, ``QuarantineRecord``) is implemented or exercised
here.
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
from pcae.cltr.authority import bindings as mab_module
from pcae.cltr.authority.errors import (
    TypedModelConstructionError,
    TypedModelInternalInvariantError,
    UnsupportedSchemaVersionError,
    WrongFamilyReferenceError,
)
from pcae.cltr.authority.sentinels import ABSENT
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
BINDINGS_MODULE = AUTHORITY_PACKAGE_DIR / "bindings.py"

MARKER_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/marker_authority_binding.schema.json"
)
AUTHORITY_EPOCH_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json"
RECEIPT_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/receipt_authority_binding.schema.json"
)

THIRTEEN_IMPLEMENTED_RECORD_FAMILIES = (
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
)

THREE_MUST_NOT_EXIST_RECORD_FAMILIES = (
    "FinalizationReceiptAuthorityBinding",
    "CompatibilityState",
    "QuarantineRecord",
)


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _assert_schema_valid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


def _assert_schema_invalid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is not OutcomeStatus.VALID


def _sha256(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Independent-verification schema-validated non-authoritative record.",
    }


def _ref(record_id: str, digest_fill: str, family: str, *, with_schema: str | None = None) -> dict:
    out = {"record_id": record_id, "record_digest": _sha256(digest_fill), "record_family": family}
    if with_schema is not None:
        out["schema_id"] = with_schema
        out["schema_version"] = "1.0"
    return out


def _duplicate_ref(record_id: str = "markrbnd-0000002", digest: str = "2") -> dict:
    return _ref(record_id, digest, "marker_authority_binding", with_schema=MARKER_AUTHORITY_BINDING_SCHEMA_ID)


def _generation_ref(gen_id: str = "generatn-0000001", digest: str = "4") -> dict:
    return {"generation_id": gen_id, "generation_digest": _sha256(digest)}


def _mab_wire(**overrides) -> dict:
    record = {
        "schema_id": MARKER_AUTHORITY_BINDING_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "marker_authority_binding",
        "record_id": "markrbnd-0000001",
        "record_digest": _sha256("0"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "generation_reference": _generation_ref(),
        "state": "absent",
        "compatibility_fallback_forbidden": True,
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# 1. Inventory verification (independent AST + runtime introspection,
#    package export, and registry discovery)
# ---------------------------------------------------------------------------


def test_136ao_exactly_thirteen_record_family_classes_exist_via_ast():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        class_names |= {
            node.name for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, ast.ClassDef)
        }
    for expected in THIRTEEN_IMPLEMENTED_RECORD_FAMILIES:
        assert expected in class_names, f"missing expected record family class {expected!r}"
    for forbidden in THREE_MUST_NOT_EXIST_RECORD_FAMILIES:
        assert forbidden not in class_names, f"forbidden record family class {forbidden!r} exists"
    present_record_families = class_names & set(
        THIRTEEN_IMPLEMENTED_RECORD_FAMILIES + THREE_MUST_NOT_EXIST_RECORD_FAMILIES
    )
    assert present_record_families == set(THIRTEEN_IMPLEMENTED_RECORD_FAMILIES)


def test_136ao_package_export_inventory_via_runtime_import():
    for expected in THIRTEEN_IMPLEMENTED_RECORD_FAMILIES:
        assert hasattr(auth, expected)
        assert isinstance(getattr(auth, expected), type)
        assert expected in auth.__all__
    for forbidden in THREE_MUST_NOT_EXIST_RECORD_FAMILIES:
        assert not hasattr(auth, forbidden)
        assert forbidden not in auth.__all__


def test_136ao_group_8_module_defines_exactly_its_two_own_families():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_names = class_names & set(
        THIRTEEN_IMPLEMENTED_RECORD_FAMILIES + THREE_MUST_NOT_EXIST_RECORD_FAMILIES
    )
    assert record_family_names == {"NotificationAuthorityBinding", "MarkerAuthorityBinding"}


def test_136ao_no_forbidden_family_source_file_exists():
    for forbidden_file in ("compatibility_quarantine.py",):
        assert not (AUTHORITY_PACKAGE_DIR / forbidden_file).exists()


def test_136ao_schema_registry_discovers_marker_authority_binding_schema(schema_registry):
    assert MARKER_AUTHORITY_BINDING_SCHEMA_ID in schema_registry.schema_ids
    assert schema_registry.document(MARKER_AUTHORITY_BINDING_SCHEMA_ID) is not None


# ---------------------------------------------------------------------------
# 2. Independent schema re-derivation: valid wire round-trips against the
#    live executable schema registry (not the Python model's own opinion)
# ---------------------------------------------------------------------------


def test_136ao_minimal_valid_absent_state_is_schema_valid_and_constructs(schema_registry):
    wire = _mab_wire()
    _assert_schema_valid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136ao_conflict_state_with_null_duplicate_of_valid(schema_registry):
    wire = _mab_wire(state="conflict", duplicate_of=None)
    _assert_schema_valid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.duplicate_of is None
    assert model.to_dict() == wire


def test_136ao_conflict_state_with_reference_duplicate_of_valid(schema_registry):
    wire = _mab_wire(state="conflict", duplicate_of=_duplicate_ref())
    _assert_schema_valid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.duplicate_of.record_id.value == "markrbnd-0000002"
    assert model.to_dict() == wire


def test_136ao_all_optional_fields_populated_round_trips(schema_registry):
    wire = _mab_wire(
        state="conflict",
        duplicate_of=_duplicate_ref(),
        _extensions={"note": "independent-verification-tag"},
    )
    _assert_schema_valid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


# ---------------------------------------------------------------------------
# 3. Required-field re-derivation: dropping any required key must be
#    rejected both by the live schema and by the model
# ---------------------------------------------------------------------------


MARKER_AUTHORITY_BINDING_REQUIRED_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch", "generation_reference", "state",
    "compatibility_fallback_forbidden", "limitations", "authority_disclosure",
)


@pytest.mark.parametrize("field", MARKER_AUTHORITY_BINDING_REQUIRED_FIELDS)
def test_136ao_missing_required_field_rejected(field, schema_registry):
    wire = _mab_wire()
    del wire[field]
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, KeyError, TypedModelInternalInvariantError)):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_unknown_field_rejected(schema_registry):
    wire = _mab_wire(unknown_field_xyz="nope")
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_exactly_thirteen_required_fields_confirmed_against_live_schema(schema_registry):
    document = schema_registry.document(MARKER_AUTHORITY_BINDING_SCHEMA_ID)
    assert set(document["required"]) == set(MARKER_AUTHORITY_BINDING_REQUIRED_FIELDS)
    assert len(MARKER_AUTHORITY_BINDING_REQUIRED_FIELDS) == 13


# ---------------------------------------------------------------------------
# 4. Discriminator / schema_id / schema_version / contract_version fidelity
# ---------------------------------------------------------------------------


def test_136ao_wrong_record_type_rejected(schema_registry):
    wire = _mab_wire(record_type="notification_authority_binding")
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_wrong_schema_id_rejected(schema_registry):
    wire = _mab_wire(schema_id=AUTHORITY_EPOCH_SCHEMA_ID)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_wrong_contract_version_rejected(schema_registry):
    wire = _mab_wire(contract_version="2.0")
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_unsupported_schema_version_rejected_before_payload_inspection():
    wire = _mab_wire()
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="2.0")
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="9.9")


# ---------------------------------------------------------------------------
# 5. Enum verification -- every valid member, plus invalid/case/whitespace/
#    null/omission/int/bool.
# ---------------------------------------------------------------------------


MARKER_STATE_MEMBERS = ("absent", "written", "stale", "conflict")


@pytest.mark.parametrize("member", MARKER_STATE_MEMBERS)
def test_136ao_state_every_valid_member_accepted_with_conditionals_satisfied(member, schema_registry):
    kwargs = {"state": member}
    if member == "conflict":
        kwargs["duplicate_of"] = _duplicate_ref()
    wire = _mab_wire(**kwargs)
    _assert_schema_valid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.state.value == member


@pytest.mark.parametrize(
    "bad_value",
    ["ABSENT", "written ", " stale", "unknown", "", None, 1, True],
)
def test_136ao_state_invalid_values_rejected(bad_value, schema_registry):
    wire = _mab_wire(state=bad_value)
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_state_field_omission_rejected(schema_registry):
    wire = _mab_wire()
    del wire["state"]
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_state_has_exactly_four_members_confirmed_against_live_schema(schema_registry):
    document = schema_registry.document(MARKER_AUTHORITY_BINDING_SCHEMA_ID)
    schema_enum = set(document["$defs"]["marker_state"]["enum"])
    assert schema_enum == set(MARKER_STATE_MEMBERS)
    assert {m.value for m in mab_module.MarkerState} == set(MARKER_STATE_MEMBERS)


# ---------------------------------------------------------------------------
# 6. Conditional-rule verification: state <-> duplicate_of, guarding
#    against unauthorized strengthening/weakening.
# ---------------------------------------------------------------------------


def test_136ao_conflict_without_duplicate_of_rejected(schema_registry):
    wire = _mab_wire(state="conflict")
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_conflict_state", ["absent", "written", "stale"])
def test_136ao_non_conflict_forbids_duplicate_of_reference(non_conflict_state, schema_registry):
    wire = _mab_wire(state=non_conflict_state, duplicate_of=_duplicate_ref())
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_conflict_state", ["absent", "written", "stale"])
def test_136ao_non_conflict_forbids_duplicate_of_explicit_null(non_conflict_state, schema_registry):
    """The 'else' branch of the schema's allOf conditional forbids the key
    being *present at all* when state != conflict -- not merely forbidding
    a non-null value. An explicit null must still be rejected."""

    wire = _mab_wire(state=non_conflict_state, duplicate_of=None)
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_conflict_permits_both_null_and_reference_duplicate_of(schema_registry):
    """Guard against unauthorized narrowing: the schema's duplicate_of
    $def is `oneOf [null, self_family_reference]` -- both values must be
    independently accepted when state == 'conflict', not just one."""

    null_wire = _mab_wire(state="conflict", duplicate_of=None)
    ref_wire = _mab_wire(state="conflict", duplicate_of=_duplicate_ref())
    _assert_schema_valid(null_wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    _assert_schema_valid(ref_wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    auth.MarkerAuthorityBinding.from_dict(null_wire, schema_version="1.0")
    auth.MarkerAuthorityBinding.from_dict(ref_wire, schema_version="1.0")


def test_136ao_no_unauthorized_semantics_duplicate_identity_may_equal_self_or_anything_shape_only(schema_registry):
    """Guard against inventing semantics the schema does not state (per
    operator prompt): the schema never requires the duplicate marker's
    identity to differ from this record's own record_id, nor that the
    referenced marker actually exists, is older, or has matching
    metadata -- shape only."""

    wire = _mab_wire(
        record_id="markrbnd-0000007",
        state="conflict",
        duplicate_of=_ref(
            "markrbnd-0000007", "9", "marker_authority_binding", with_schema=MARKER_AUTHORITY_BINDING_SCHEMA_ID
        ),
    )
    _assert_schema_valid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.duplicate_of.record_id.value == model.envelope.record_id.value


# ---------------------------------------------------------------------------
# 7. Reference verification: target family, schema_id/schema_version
#    cross-family requirement, wrapper type, nullability, no lookup.
# ---------------------------------------------------------------------------


def test_136ao_duplicate_of_wrong_family_rejected(schema_registry):
    wire = _mab_wire(
        state="conflict",
        duplicate_of=_ref(
            "rcptbnd-00000002", "7", "receipt_authority_binding", with_schema=RECEIPT_AUTHORITY_BINDING_SCHEMA_ID
        ),
    )
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, WrongFamilyReferenceError)):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_duplicate_of_missing_schema_id_rejected(schema_registry):
    bare = {"record_id": "markrbnd-0000004", "record_digest": _sha256("1"), "record_family": "marker_authority_binding"}
    wire = _mab_wire(state="conflict", duplicate_of=bare)
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_duplicate_of_missing_schema_version_rejected(schema_registry):
    bare = {
        "record_id": "markrbnd-0000005",
        "record_digest": _sha256("2"),
        "record_family": "marker_authority_binding",
        "schema_id": MARKER_AUTHORITY_BINDING_SCHEMA_ID,
    }
    wire = _mab_wire(state="conflict", duplicate_of=bare)
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_generation_reference_wrapper_type_and_pairing(schema_registry):
    wire = _mab_wire()
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert type(model.generation_reference).__name__ == "GenerationReference"
    assert model.generation_reference.generation_id.value == "generatn-0000001"
    assert model.generation_reference.generation_digest.value == _sha256("4")


def test_136ao_generation_reference_has_no_schema_id_or_version_fields(schema_registry):
    document = schema_registry.document(MARKER_AUTHORITY_BINDING_SCHEMA_ID)
    wire = _mab_wire()
    assert set(wire["generation_reference"].keys()) == {"generation_id", "generation_digest"}
    assert document["properties"]["generation_reference"]["$ref"].endswith("generation_reference")


def test_136ao_valid_but_nonexistent_reference_succeeds_no_lookup_performed(schema_registry, monkeypatch):
    """A duplicate_of reference naming a plausible-but-never-registered
    record_id must construct successfully -- no filesystem/registry
    lookup may be performed to check existence."""

    def _boom(*a, **k):
        raise AssertionError("unexpected filesystem access during reference construction")

    monkeypatch.setattr("builtins.open", _boom)
    wire = _mab_wire(state="conflict", duplicate_of=_duplicate_ref("markrbnd-9999999", "f"))
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.duplicate_of.record_id.value == "markrbnd-9999999"


def test_136ao_no_lookup_or_authority_resolution_symbols_defined():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    forbidden = ("resolve_reference", "lookup_record", "resolve_authority", "activate_authority")
    for name in forbidden:
        assert name not in defined_names


# ---------------------------------------------------------------------------
# 8. Absent vs null verification for every optional field
# ---------------------------------------------------------------------------


def test_136ao_duplicate_of_absent_by_default():
    wire = _mab_wire()
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.duplicate_of is ABSENT
    serialized = model.to_dict()
    assert "duplicate_of" not in serialized


def test_136ao_extensions_absent_by_default_and_explicit_null_rejected(schema_registry):
    wire = _mab_wire()
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model._extensions is ABSENT
    wire_with_null_ext = _mab_wire(_extensions=None)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire_with_null_ext, schema_version="1.0")


def test_136ao_extensions_populated_string_valued_map_round_trips(schema_registry):
    wire = _mab_wire(_extensions={"note": "independent-verification-tag"})
    _assert_schema_valid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.to_dict()["_extensions"] == {"note": "independent-verification-tag"}


def test_136ao_extensions_non_string_value_rejected(schema_registry):
    wire = _mab_wire(_extensions={"note": 123})
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_extensions_reserved_key_collision_rejected():
    wire = _mab_wire(_extensions={"migration_epoch": "shadowing-attempt"})
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_extensions_max_properties_bound_confirmed_against_live_schema(schema_registry):
    document = schema_registry.document(MARKER_AUTHORITY_BINDING_SCHEMA_ID)
    assert document["properties"]["_extensions"]["maxProperties"] == 32
    from pcae.cltr.authority.extensions import MAX_EXTENSION_PROPERTIES

    assert MAX_EXTENSION_PROPERTIES == 32


# ---------------------------------------------------------------------------
# 9. compatibility_fallback_forbidden const-true + authority-role
#    locally-forbidden 'authoritative' verification
# ---------------------------------------------------------------------------


def test_136ao_compatibility_fallback_forbidden_must_be_true(schema_registry):
    wire = _mab_wire(compatibility_fallback_forbidden=False)
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_authoritative_role_rejected(schema_registry):
    wire = _mab_wire(authority_disclosure=_disclosure(role="authoritative"))
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "role", ["derivative", "operational", "evidence", "compatibility", "historical", "quarantined"]
)
def test_136ao_every_non_authoritative_role_accepted(role, schema_registry):
    wire = _mab_wire(authority_disclosure=_disclosure(role=role))
    _assert_schema_valid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.authority_role.value == role


def test_136ao_is_authoritative_true_rejected():
    disclosure = _disclosure()
    disclosure["is_authoritative"] = True
    wire = _mab_wire(authority_disclosure=disclosure)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 10. Immutability verification (recursive; mutating source after
#     construction must never affect the model)
# ---------------------------------------------------------------------------


def test_136ao_is_frozen_dataclass():
    model = auth.MarkerAuthorityBinding.from_dict(_mab_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.state = mab_module.MarkerState.WRITTEN


def test_136ao_mutating_source_limitations_list_after_construction_does_not_affect_model():
    source_limitations = ["limitation one"]
    wire = _mab_wire(limitations=source_limitations)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_limitations.append("limitation two (added after construction)")
    assert len(model.limitations.entries) == 1


def test_136ao_mutating_source_extensions_mapping_after_construction_does_not_affect_model(schema_registry):
    source_extensions = {"note": "original"}
    wire = _mab_wire(_extensions=source_extensions)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_extensions["note"] = "tampered"
    source_extensions["new_key"] = "also tampered"
    assert model.to_dict()["_extensions"] == {"note": "original"}


def test_136ao_mutating_source_reference_dict_after_construction_does_not_affect_model():
    source_gen_ref = _generation_ref()
    wire = _mab_wire(generation_reference=source_gen_ref)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_gen_ref["generation_id"] = "tampered-0000001"
    assert model.generation_reference.generation_id.value == "generatn-0000001"


def test_136ao_mutating_source_duplicate_of_dict_after_construction_does_not_affect_model():
    source_dup_ref = _duplicate_ref()
    wire = _mab_wire(state="conflict", duplicate_of=source_dup_ref)
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_dup_ref["record_id"] = "tampered-0000002"
    assert model.duplicate_of.record_id.value == "markrbnd-0000002"


def test_136ao_deep_copy_of_model_produces_structurally_equal_but_independent_object():
    model = auth.MarkerAuthorityBinding.from_dict(_mab_wire(), schema_version="1.0")
    duplicate = copy.deepcopy(model)
    assert duplicate == model
    assert duplicate is not model


# ---------------------------------------------------------------------------
# 11. Equality verification: structural, not identifier-only/digest-only
# ---------------------------------------------------------------------------


def test_136ao_equality_changes_when_any_field_changes():
    base = auth.MarkerAuthorityBinding.from_dict(_mab_wire(), schema_version="1.0")
    same = auth.MarkerAuthorityBinding.from_dict(_mab_wire(), schema_version="1.0")
    assert base == same

    different_state = auth.MarkerAuthorityBinding.from_dict(
        _mab_wire(state="written"), schema_version="1.0"
    )
    assert base != different_state

    different_epoch = auth.MarkerAuthorityBinding.from_dict(
        _mab_wire(migration_epoch="epoch-002"), schema_version="1.0"
    )
    assert base != different_epoch

    with_duplicate = auth.MarkerAuthorityBinding.from_dict(
        _mab_wire(state="conflict", duplicate_of=_duplicate_ref()), schema_version="1.0"
    )
    with_null_duplicate = auth.MarkerAuthorityBinding.from_dict(
        _mab_wire(state="conflict", duplicate_of=None), schema_version="1.0"
    )
    assert with_duplicate != with_null_duplicate


def test_136ao_equality_rejects_identifier_only_and_digest_only_comparison():
    base = auth.MarkerAuthorityBinding.from_dict(_mab_wire(), schema_version="1.0")
    same_identity_different_state = auth.MarkerAuthorityBinding.from_dict(
        _mab_wire(state="stale"), schema_version="1.0"
    )
    assert base.envelope.record_id == same_identity_different_state.envelope.record_id
    assert base.envelope.record_digest == same_identity_different_state.envelope.record_digest
    assert base != same_identity_different_state


def test_136ao_reference_equality_is_structural_not_family_only():
    ref_a = auth.RecordReference(
        record_id=auth.RecordId("markrbnd-0000005"),
        record_digest=auth.ReferencedRecordDigest(_sha256("a")),
        record_family=auth.RecordFamily.MARKER_AUTHORITY_BINDING,
    )
    ref_b = auth.RecordReference(
        record_id=auth.RecordId("markrbnd-0000006"),
        record_digest=auth.ReferencedRecordDigest(_sha256("b")),
        record_family=auth.RecordFamily.MARKER_AUTHORITY_BINDING,
    )
    assert ref_a != ref_b


# ---------------------------------------------------------------------------
# 12. Error-behavior determinism verification
# ---------------------------------------------------------------------------


def test_136ao_invalid_digest_wrapper_rejected():
    with pytest.raises(Exception):
        auth.MarkerAuthorityBinding.from_dict(
            _mab_wire(record_digest="not-a-valid-sha256-hex"), schema_version="1.0"
        )


def test_136ao_invalid_identifier_wrapper_rejected():
    with pytest.raises(Exception):
        auth.MarkerAuthorityBinding.from_dict(
            _mab_wire(migration_epoch="/../invalid"), schema_version="1.0"
        )


def test_136ao_malformed_reference_missing_record_family_rejected(schema_registry):
    malformed = {"record_id": "markrbnd-0000009", "record_digest": _sha256("1")}
    wire = _mab_wire(state="conflict", duplicate_of=malformed)
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_invalid_shape_limitations_not_a_list_rejected(schema_registry):
    wire = _mab_wire(limitations="not-a-list")
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ao_construction_errors_are_deterministic_across_repeated_attempts():
    bad_wire = _mab_wire(state="not-a-real-state")
    errors = []
    for _ in range(3):
        try:
            auth.MarkerAuthorityBinding.from_dict(bad_wire, schema_version="1.0")
        except Exception as exc:  # noqa: BLE001
            errors.append(type(exc))
    assert len(errors) == 3
    assert len(set(errors)) == 1


def test_136ao_compatibility_fallback_forbidden_wrong_type_rejected(schema_registry):
    wire = _mab_wire(compatibility_fallback_forbidden="true")
    _assert_schema_invalid(wire, MARKER_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 13. Purely-representational behavior: reject any marker-management or
#     authority-exercising capability
# ---------------------------------------------------------------------------


FORBIDDEN_MARKER_MANAGEMENT_SYMBOLS = (
    "create_marker", "write_marker", "update_marker", "delete_marker", "rename_marker",
    "publish_marker", "discover_marker", "enumerate_markers", "resolve_marker_location",
    "inspect_marker_file", "validate_marker_existence", "compare_marker_freshness",
    "reconcile_marker_state", "read_marker_contents", "write_marker_contents",
    "modify_marker_metadata", "synchronize_markers",
)

FORBIDDEN_AUTHORITY_EXERCISE_SYMBOLS = (
    "activate_authority", "resolve_authority", "determine_current_authority",
    "compare_authorities", "transfer_authority", "mutate_authority_pointer",
    "modify_lifecycle_state",
)


def test_136ao_module_defines_no_marker_management_function_or_method():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_MARKER_MANAGEMENT_SYMBOLS:
        assert forbidden not in defined_names, f"forbidden marker-management symbol {forbidden!r} defined"
    for forbidden in FORBIDDEN_AUTHORITY_EXERCISE_SYMBOLS:
        assert forbidden not in defined_names, f"forbidden authority-exercise symbol {forbidden!r} defined"


def test_136ao_module_source_never_imports_filesystem_socket_or_subprocess():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    forbidden_modules = ("socket", "subprocess", "os.path", "shutil", "requests", "urllib")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(f) for f in forbidden_modules)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(f) for f in forbidden_modules)


def test_136ao_module_source_never_references_environment_variables():
    source = BINDINGS_MODULE.read_text()
    for forbidden_token in ("os.environ", "getenv", "os.getenv"):
        assert forbidden_token not in source


def test_136ao_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    wire = _mab_wire(state="conflict", duplicate_of=_duplicate_ref())
    model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version="1.0")
    model.to_dict()
    repr(model)


def test_136ao_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    model = auth.MarkerAuthorityBinding.from_dict(_mab_wire(), schema_version="1.0")
    model.to_dict()


def test_136ao_no_filesystem_write_during_construction_serialization_equality_repr(monkeypatch):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    model = auth.MarkerAuthorityBinding.from_dict(_mab_wire(), schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136ao_package_reimport_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(mab_module)


# ---------------------------------------------------------------------------
# 14. Runtime isolation: no production import of pcae.cltr.authority
# ---------------------------------------------------------------------------


def test_136ao_no_production_module_imports_authority_package():
    forbidden_prefixes = ("pcae.cltr.authority",)
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
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in forbidden_prefixes:
                            assert not alias.name.startswith(forbidden), (path, alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    for forbidden in forbidden_prefixes:
                        assert not node.module.startswith(forbidden), (path, node.module)


def test_136ao_authority_bindings_module_does_not_import_marker_management_or_runtime():
    forbidden_modules = (
        "pcae.cltr.notification", "pcae.cltr.marker", "pcae.cltr.receipt",
        "pcae.commands", "pcae.core", "pcae.runtime", "telegram", "smtplib", "slack_sdk",
        "pathlib", "os",
    )
    tree = ast.parse(BINDINGS_MODULE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in forbidden_modules:
                    assert not alias.name.startswith(forbidden)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in forbidden_modules:
                assert not node.module.startswith(forbidden)


def test_136ao_authority_models_module_imports_no_transport_or_filesystem_code_via_full_dependency_walk():
    """Independent re-walk of every module transitively imported by
    bindings.py within the authority package, confirming none imports a
    transport/filesystem-lifecycle module either."""

    visited: set[Path] = set()
    to_visit = [BINDINGS_MODULE]
    forbidden_modules = (
        "socket", "subprocess", "telegram", "smtplib", "requests", "urllib.request",
        "pathlib", "shutil",
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
            if module_name:
                for forbidden in forbidden_modules:
                    assert not module_name.startswith(forbidden), (path, module_name)
                if module_name.startswith("pcae.cltr.authority."):
                    sibling = AUTHORITY_PACKAGE_DIR / (module_name.rsplit(".", 1)[-1] + ".py")
                    to_visit.append(sibling)
    assert BINDINGS_MODULE in visited


# ---------------------------------------------------------------------------
# 15. Packaging verification (fresh wheel/sdist build, isolated install)
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136ao_wheel_build_contains_group_8_module_and_no_later_family(tmp_path: Path):
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
    assert "pcae/cltr/authority/bindings.py" in names
    for forbidden in ("compatibility_quarantine",):
        assert f"pcae/cltr/authority/{forbidden}.py" not in names


@pytest.mark.slow
def test_136ao_isolated_install_all_thirteen_families_import_and_round_trip(tmp_path: Path):
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
        "for name in " + repr(THIRTEEN_IMPLEMENTED_RECORD_FAMILIES) + ":\n"
        "    assert hasattr(auth, name), name\n"
        "for name in " + repr(THREE_MUST_NOT_EXIST_RECORD_FAMILIES) + ":\n"
        "    assert not hasattr(auth, name), name\n"
        "wire = {\n"
        "    'schema_id': " + repr(MARKER_AUTHORITY_BINDING_SCHEMA_ID) + ",\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'marker_authority_binding', 'record_id': 'markrbnd-0000099',\n"
        "    'record_digest': '0'*64, 'created_at': '2026-07-18T12:00:00Z',\n"
        "    'migration_epoch': 'epoch-001',\n"
        "    'generation_reference': {'generation_id': 'generatn-0000099',\n"
        "        'generation_digest': 'a'*64},\n"
        "    'state': 'absent',\n"
        "    'compatibility_fallback_forbidden': True,\n"
        "    'limitations': [], 'authority_disclosure': {'authority_role': 'derivative',\n"
        "        'is_authoritative': False, 'disclosure_text': 'ok'},\n"
        "}\n"
        "model = auth.MarkerAuthorityBinding.from_dict(wire, schema_version='1.0')\n"
        "assert model.to_dict() == wire\n"
        "print('ISOLATED_INSTALL_OK')\n"
    )
    result = subprocess.run(
        [str(venv_python), "-c", probe], check=True, capture_output=True, text=True,
    )
    assert "ISOLATED_INSTALL_OK" in result.stdout
