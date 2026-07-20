"""Phase 136AQ: Stage 3 Typed Authority Model Finalization Receipt Authority
Binding Independent Verification.

Independent re-derivation and verification of Phase 136AP's Typed Model
Implementation Group 9 (``FinalizationReceiptAuthorityBinding``) against the
frozen contract and live executable schema
(``records/receipt_authority_binding.schema.json``,
``shared/references.schema.json``, ``shared/digest.schema.json``,
``shared/identity.schema.json``, ``shared/limitations.schema.json``,
``shared/envelope.schema.json``, ``shared/enums.schema.json``) --
independently, without trusting the 136AP implementation, its own test
suite, its report, its comments, or any prior verification report. Every
fixture and assertion below was derived directly from the executable schema
file (``receipt_authority_binding.schema.json``) and the frozen contract
text quoted in its ``description`` fields, then compared against
``src/pcae/cltr/authority/bindings.py``.

Scope: Implementation Group 9 only (``FinalizationReceiptAuthorityBinding``).
No later record-family model (``CompatibilityState``, ``QuarantineRecord``)
is implemented or exercised here.
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
from pcae.cltr.authority import bindings as rab_module
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

RECEIPT_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/receipt_authority_binding.schema.json"
)
MARKER_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/marker_authority_binding.schema.json"
)
PUBLICATION_EVIDENCE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/publication_evidence.schema.json"
)
AUTHORITY_EPOCH_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json"

FOURTEEN_IMPLEMENTED_RECORD_FAMILIES = (
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
)

# Narrowed further by Phase 136AR (Typed Model Implementation Group
# 10): `CompatibilityState` is now authorized, legitimately-
# implemented record-family model -- removed from this
# still-forbidden list. Narrowed further by Phase 136AT (Typed Model
# Implementation Group 11): `QuarantineRecord` is now the sixteenth and
# final authorized, legitimately-implemented record-family model --
# removed from this still-forbidden list, which is now empty.
TWO_MUST_NOT_EXIST_RECORD_FAMILIES = ()


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


def _publication_evidence_ref(record_id: str = "pubevdnc-0000002", digest: str = "2") -> dict:
    return _ref(record_id, digest, "publication_evidence", with_schema=PUBLICATION_EVIDENCE_SCHEMA_ID)


def _marker_ref(record_id: str = "markrbnd-0000003", digest: str = "3") -> dict:
    return _ref(record_id, digest, "marker_authority_binding", with_schema=MARKER_AUTHORITY_BINDING_SCHEMA_ID)


def _generation_ref(gen_id: str = "generatn-0000001", digest: str = "4") -> dict:
    return {"generation_id": gen_id, "generation_digest": _sha256(digest)}


def _rab_wire(**overrides) -> dict:
    record = {
        "schema_id": RECEIPT_AUTHORITY_BINDING_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "receipt_authority_binding",
        "record_id": "rcptbnd-0000001",
        "record_digest": _sha256("0"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "generation_reference": _generation_ref(),
        "receipt_state": "absent",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _finalized_rab_wire(**overrides) -> dict:
    base = {
        "receipt_state": "finalized",
        "publication_evidence_reference": _publication_evidence_ref(),
        "marker_reference": _marker_ref(),
    }
    base.update(overrides)
    return _rab_wire(**base)


# ---------------------------------------------------------------------------
# 1. Inventory verification (independent AST + runtime introspection,
#    package export, and registry discovery)
# ---------------------------------------------------------------------------


def test_136aq_exactly_fourteen_record_family_classes_exist_via_ast():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        class_names |= {
            node.name for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, ast.ClassDef)
        }
    for expected in FOURTEEN_IMPLEMENTED_RECORD_FAMILIES:
        assert expected in class_names, f"missing expected record family class {expected!r}"
    for forbidden in TWO_MUST_NOT_EXIST_RECORD_FAMILIES:
        assert forbidden not in class_names, f"forbidden record family class {forbidden!r} exists"
    present_record_families = class_names & set(
        FOURTEEN_IMPLEMENTED_RECORD_FAMILIES + TWO_MUST_NOT_EXIST_RECORD_FAMILIES
    )
    assert present_record_families == set(FOURTEEN_IMPLEMENTED_RECORD_FAMILIES)


def test_136aq_package_export_inventory_via_runtime_import():
    for expected in FOURTEEN_IMPLEMENTED_RECORD_FAMILIES:
        assert hasattr(auth, expected)
        assert isinstance(getattr(auth, expected), type)
        assert expected in auth.__all__
    for forbidden in TWO_MUST_NOT_EXIST_RECORD_FAMILIES:
        assert not hasattr(auth, forbidden)
        assert forbidden not in auth.__all__


def test_136aq_group_9_module_defines_exactly_its_three_own_families():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_names = class_names & set(
        FOURTEEN_IMPLEMENTED_RECORD_FAMILIES + TWO_MUST_NOT_EXIST_RECORD_FAMILIES
    )
    assert record_family_names == {
        "NotificationAuthorityBinding",
        "MarkerAuthorityBinding",
        "FinalizationReceiptAuthorityBinding",
    }


def test_136aq_no_forbidden_family_source_file_exists():
    # Narrowed by Phase 136AR: `compatibility_quarantine.py` (Group 10,
    # `CompatibilityState` only) is now a legitimate, authorized module;
    # removed from this still-forbidden list. No other later-group source
    # file (i.e. one containing `QuarantineRecord`) exists.
    for forbidden_file in ():
        assert not (AUTHORITY_PACKAGE_DIR / forbidden_file).exists()
    assert (AUTHORITY_PACKAGE_DIR / "compatibility_quarantine.py").exists()


def test_136aq_schema_registry_discovers_receipt_authority_binding_schema(schema_registry):
    assert RECEIPT_AUTHORITY_BINDING_SCHEMA_ID in schema_registry.schema_ids
    assert schema_registry.document(RECEIPT_AUTHORITY_BINDING_SCHEMA_ID) is not None


# ---------------------------------------------------------------------------
# 2. Independent schema re-derivation: valid wire round-trips against the
#    live executable schema registry (not the Python model's own opinion)
# ---------------------------------------------------------------------------


def test_136aq_minimal_valid_absent_state_is_schema_valid_and_constructs(schema_registry):
    wire = _rab_wire()
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136aq_finalized_state_with_both_references_valid(schema_registry):
    wire = _finalized_rab_wire()
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.publication_evidence_reference.record_id.value == "pubevdnc-0000002"
    assert model.marker_reference.record_id.value == "markrbnd-0000003"
    assert model.to_dict() == wire


def test_136aq_all_optional_fields_populated_round_trips(schema_registry):
    wire = _finalized_rab_wire(
        staleness_check={},
        _extensions={"note": "independent-verification-tag"},
    )
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


# ---------------------------------------------------------------------------
# 3. Required-field re-derivation: dropping any required key must be
#    rejected both by the live schema and by the model
# ---------------------------------------------------------------------------


RECEIPT_AUTHORITY_BINDING_REQUIRED_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch", "generation_reference", "receipt_state",
    "limitations", "authority_disclosure",
)


@pytest.mark.parametrize("field", RECEIPT_AUTHORITY_BINDING_REQUIRED_FIELDS)
def test_136aq_missing_required_field_rejected(field, schema_registry):
    wire = _rab_wire()
    del wire[field]
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, KeyError, TypedModelInternalInvariantError)):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_unknown_field_rejected(schema_registry):
    wire = _rab_wire(unknown_field_xyz="nope")
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_exactly_twelve_required_fields_confirmed_against_live_schema(schema_registry):
    document = schema_registry.document(RECEIPT_AUTHORITY_BINDING_SCHEMA_ID)
    assert set(document["required"]) == set(RECEIPT_AUTHORITY_BINDING_REQUIRED_FIELDS)
    assert len(RECEIPT_AUTHORITY_BINDING_REQUIRED_FIELDS) == 12


def test_136aq_no_phase_id_or_transition_id_fields(schema_registry):
    document = schema_registry.document(RECEIPT_AUTHORITY_BINDING_SCHEMA_ID)
    assert "phase_id" not in document["properties"]
    assert "transition_id" not in document["properties"]


# ---------------------------------------------------------------------------
# 4. Discriminator / schema_id / schema_version / contract_version fidelity
# ---------------------------------------------------------------------------


def test_136aq_wrong_record_type_rejected(schema_registry):
    wire = _rab_wire(record_type="marker_authority_binding")
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_wrong_schema_id_rejected(schema_registry):
    wire = _rab_wire(schema_id=AUTHORITY_EPOCH_SCHEMA_ID)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_wrong_contract_version_rejected(schema_registry):
    wire = _rab_wire(contract_version="2.0")
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_unsupported_schema_version_rejected_before_payload_inspection():
    wire = _rab_wire()
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="2.0")
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="9.9")


# ---------------------------------------------------------------------------
# 5. Enum verification -- every valid member, plus invalid/case/whitespace/
#    null/omission/int/bool.
# ---------------------------------------------------------------------------


RECEIPT_STATE_MEMBERS = ("absent", "finalized", "stale", "conflict")


@pytest.mark.parametrize("member", RECEIPT_STATE_MEMBERS)
def test_136aq_receipt_state_every_valid_member_accepted_with_conditionals_satisfied(member, schema_registry):
    kwargs = {"receipt_state": member}
    if member == "finalized":
        kwargs["publication_evidence_reference"] = _publication_evidence_ref()
        kwargs["marker_reference"] = _marker_ref()
    wire = _rab_wire(**kwargs)
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.receipt_state.value == member


@pytest.mark.parametrize(
    "bad_value",
    ["ABSENT", "finalized ", " stale", "unknown", "", None, 1, True],
)
def test_136aq_receipt_state_invalid_values_rejected(bad_value, schema_registry):
    wire = _rab_wire(receipt_state=bad_value)
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_receipt_state_field_omission_rejected(schema_registry):
    wire = _rab_wire()
    del wire["receipt_state"]
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_receipt_state_has_exactly_four_members_confirmed_against_live_schema(schema_registry):
    document = schema_registry.document(RECEIPT_AUTHORITY_BINDING_SCHEMA_ID)
    schema_enum = set(document["$defs"]["receipt_state"]["enum"])
    assert schema_enum == set(RECEIPT_STATE_MEMBERS)
    assert {m.value for m in rab_module.ReceiptState} == set(RECEIPT_STATE_MEMBERS)


# ---------------------------------------------------------------------------
# 6. Conditional-rule verification: receipt_state <-> (publication_evidence_
#    reference, marker_reference), guarding against unauthorized strengthening
#    or weakening. This is a *pair* conditional -- both references travel
#    together, unlike the single-reference conditionals of prior groups.
# ---------------------------------------------------------------------------


def test_136aq_finalized_without_either_reference_rejected(schema_registry):
    wire = _rab_wire(receipt_state="finalized")
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_finalized_with_only_publication_evidence_reference_rejected(schema_registry):
    """Guard against unauthorized weakening: the schema requires BOTH
    references together when finalized, not merely one of the two."""

    wire = _rab_wire(receipt_state="finalized", publication_evidence_reference=_publication_evidence_ref())
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_finalized_with_only_marker_reference_rejected(schema_registry):
    wire = _rab_wire(receipt_state="finalized", marker_reference=_marker_ref())
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_finalized_state", ["absent", "stale", "conflict"])
def test_136aq_non_finalized_forbids_publication_evidence_reference(non_finalized_state, schema_registry):
    wire = _rab_wire(receipt_state=non_finalized_state, publication_evidence_reference=_publication_evidence_ref())
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_finalized_state", ["absent", "stale", "conflict"])
def test_136aq_non_finalized_forbids_marker_reference(non_finalized_state, schema_registry):
    wire = _rab_wire(receipt_state=non_finalized_state, marker_reference=_marker_ref())
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_finalized_state", ["absent", "stale", "conflict"])
def test_136aq_non_finalized_forbids_both_references_together(non_finalized_state, schema_registry):
    wire = _rab_wire(
        receipt_state=non_finalized_state,
        publication_evidence_reference=_publication_evidence_ref(),
        marker_reference=_marker_ref(),
    )
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_no_unauthorized_semantics_receipt_state_never_proves_production_outcome(schema_registry):
    """Guard against inventing semantics the schema does not state: a
    schema-valid 'finalized' receipt with plausible-but-never-registered
    references must construct successfully -- the shape alone never proves
    delivery, verification, or actual finalization occurred."""

    wire = _finalized_rab_wire(
        publication_evidence_reference=_publication_evidence_ref("pubevdnc-9999999", "e"),
        marker_reference=_marker_ref("markrbnd-9999999", "f"),
    )
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.receipt_state.value == "finalized"


# ---------------------------------------------------------------------------
# 7. Reference verification: target family, schema_id/schema_version
#    cross-family requirement, wrapper type, no lookup.
# ---------------------------------------------------------------------------


def test_136aq_publication_evidence_reference_wrong_family_rejected(schema_registry):
    wire = _finalized_rab_wire(
        publication_evidence_reference=_ref(
            "markrbnd-0000004", "5", "marker_authority_binding", with_schema=MARKER_AUTHORITY_BINDING_SCHEMA_ID
        )
    )
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, WrongFamilyReferenceError)):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_marker_reference_wrong_family_rejected(schema_registry):
    wire = _finalized_rab_wire(
        marker_reference=_ref(
            "pubevdnc-0000005", "6", "publication_evidence", with_schema=PUBLICATION_EVIDENCE_SCHEMA_ID
        )
    )
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, WrongFamilyReferenceError)):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_publication_evidence_reference_missing_schema_id_rejected(schema_registry):
    bare = {"record_id": "pubevdnc-0000006", "record_digest": _sha256("1"), "record_family": "publication_evidence"}
    wire = _finalized_rab_wire(publication_evidence_reference=bare)
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_marker_reference_missing_schema_version_rejected(schema_registry):
    bare = {
        "record_id": "markrbnd-0000007",
        "record_digest": _sha256("2"),
        "record_family": "marker_authority_binding",
        "schema_id": MARKER_AUTHORITY_BINDING_SCHEMA_ID,
    }
    wire = _finalized_rab_wire(marker_reference=bare)
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_generation_reference_wrapper_type_and_pairing():
    wire = _rab_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert type(model.generation_reference).__name__ == "GenerationReference"
    assert model.generation_reference.generation_id.value == "generatn-0000001"
    assert model.generation_reference.generation_digest.value == _sha256("4")


def test_136aq_generation_reference_unconditionally_required_regardless_of_receipt_state(schema_registry):
    """NON-BLOCKING-136T-6: generation_reference is required for every
    receipt_state, not merely 'finalized' -- unlike publication_evidence_
    reference/marker_reference which are conditionally required."""

    for state in RECEIPT_STATE_MEMBERS:
        kwargs = {"receipt_state": state}
        if state == "finalized":
            kwargs["publication_evidence_reference"] = _publication_evidence_ref()
            kwargs["marker_reference"] = _marker_ref()
        wire = _rab_wire(**kwargs)
        del wire["generation_reference"]
        _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
        with pytest.raises((TypedModelConstructionError, KeyError)):
            auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_valid_but_nonexistent_references_succeed_no_lookup_performed(monkeypatch):
    """Both publication_evidence_reference and marker_reference naming
    plausible-but-never-registered record_ids must construct successfully
    -- no filesystem/registry lookup may be performed to check existence."""

    def _boom(*a, **k):
        raise AssertionError("unexpected filesystem access during reference construction")

    monkeypatch.setattr("builtins.open", _boom)
    wire = _finalized_rab_wire(
        publication_evidence_reference=_publication_evidence_ref("pubevdnc-9999998", "c"),
        marker_reference=_marker_ref("markrbnd-9999998", "d"),
    )
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.publication_evidence_reference.record_id.value == "pubevdnc-9999998"
    assert model.marker_reference.record_id.value == "markrbnd-9999998"


def test_136aq_no_lookup_or_authority_resolution_symbols_defined():
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


def test_136aq_publication_evidence_and_marker_reference_absent_by_default():
    wire = _rab_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.publication_evidence_reference is ABSENT
    assert model.marker_reference is ABSENT
    serialized = model.to_dict()
    assert "publication_evidence_reference" not in serialized
    assert "marker_reference" not in serialized


def test_136aq_staleness_check_absent_by_default():
    wire = _rab_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.staleness_check is ABSENT
    assert "staleness_check" not in model.to_dict()


def test_136aq_extensions_absent_by_default_and_explicit_null_rejected():
    wire = _rab_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model._extensions is ABSENT
    wire_with_null_ext = _rab_wire(_extensions=None)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire_with_null_ext, schema_version="1.0")


def test_136aq_extensions_populated_string_valued_map_round_trips(schema_registry):
    wire = _rab_wire(_extensions={"note": "independent-verification-tag"})
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.to_dict()["_extensions"] == {"note": "independent-verification-tag"}


def test_136aq_extensions_non_string_value_rejected(schema_registry):
    wire = _rab_wire(_extensions={"note": 123})
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_extensions_reserved_key_collision_rejected():
    wire = _rab_wire(_extensions={"migration_epoch": "shadowing-attempt"})
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_extensions_max_properties_bound_confirmed_against_live_schema(schema_registry):
    document = schema_registry.document(RECEIPT_AUTHORITY_BINDING_SCHEMA_ID)
    assert document["properties"]["_extensions"]["maxProperties"] == 32
    from pcae.cltr.authority.extensions import MAX_EXTENSION_PROPERTIES

    assert MAX_EXTENSION_PROPERTIES == 32


# ---------------------------------------------------------------------------
# 8.1. staleness_check independent shape verification (DEFERRED-136T-1):
#      the live schema pins this field to an empty-shape placeholder object
#      (additionalProperties: false, no properties) -- only `{}` is a
#      schema-valid value. This is the field this phase's independent
#      re-derivation focuses on most closely, since it is wrapped in the
#      general-purpose OpaqueJsonValue type rather than a field-specific
#      wrapper.
# ---------------------------------------------------------------------------


def test_136aq_staleness_check_schema_pins_to_empty_object_only(schema_registry):
    document = schema_registry.document(RECEIPT_AUTHORITY_BINDING_SCHEMA_ID)
    staleness_def = document["$defs"]["staleness_check"]
    assert staleness_def["type"] == "object"
    assert staleness_def["additionalProperties"] is False
    assert "properties" not in staleness_def or staleness_def["properties"] == {}


def test_136aq_staleness_check_empty_object_is_schema_valid_and_constructs(schema_registry):
    wire = _rab_wire(staleness_check={})
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.staleness_check.to_json() == {}


def test_136aq_staleness_check_nonempty_object_is_schema_invalid(schema_registry):
    """Independently confirms the live schema rejects a populated
    staleness_check object (additionalProperties: false forbids any key)."""

    wire = _rab_wire(staleness_check={"checked_at": "2026-07-18T00:00:00Z"})
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)


def test_136aq_staleness_check_wrong_type_is_schema_invalid(schema_registry):
    wire = _rab_wire(staleness_check="not-an-object")
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)


def test_136aq_staleness_check_nonempty_object_rejected_by_model(schema_registry):
    """The model wraps staleness_check in the general-purpose
    OpaqueJsonValue type (``opaque.py``), which by design preserves any
    JSON value verbatim with no shape check. Independently confirmed
    against the live schema oracle above
    (test_136aq_staleness_check_nonempty_object_is_schema_invalid): a
    populated staleness_check is schema-invalid. A shape-only,
    schema-backed typed model must reject at construction time every
    payload the schema itself rejects; accepting a schema-invalid
    staleness_check would be an unauthorized weakening of the field's
    contract-pinned empty-shape restriction (DEFERRED-136T-1)."""

    wire = _rab_wire(staleness_check={"checked_at": "2026-07-18T00:00:00Z"})
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_staleness_check_wrong_type_rejected_by_model(schema_registry):
    wire = _rab_wire(staleness_check="not-an-object")
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 9. authority_role locally-forbidden 'authoritative' verification
# ---------------------------------------------------------------------------


def test_136aq_authoritative_role_rejected(schema_registry):
    wire = _rab_wire(authority_disclosure=_disclosure(role="authoritative"))
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "role", ["derivative", "operational", "evidence", "compatibility", "historical", "quarantined"]
)
def test_136aq_every_non_authoritative_role_accepted(role, schema_registry):
    wire = _rab_wire(authority_disclosure=_disclosure(role=role))
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.authority_role.value == role


def test_136aq_is_authoritative_true_rejected():
    disclosure = _disclosure()
    disclosure["is_authoritative"] = True
    wire = _rab_wire(authority_disclosure=disclosure)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_no_compatibility_fallback_forbidden_field(schema_registry):
    """Unlike MarkerAuthorityBinding, this record family has no
    compatibility_fallback_forbidden field at all -- confirmed against the
    live schema's own property list, not assumed by cross-family analogy."""

    document = schema_registry.document(RECEIPT_AUTHORITY_BINDING_SCHEMA_ID)
    assert "compatibility_fallback_forbidden" not in document["properties"]
    wire = _rab_wire(compatibility_fallback_forbidden=True)
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)


# ---------------------------------------------------------------------------
# 10. Immutability verification (recursive; mutating source after
#     construction must never affect the model)
# ---------------------------------------------------------------------------


def test_136aq_is_frozen_dataclass():
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(_rab_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.receipt_state = rab_module.ReceiptState.STALE


def test_136aq_mutating_source_limitations_list_after_construction_does_not_affect_model():
    source_limitations = ["limitation one"]
    wire = _rab_wire(limitations=source_limitations)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_limitations.append("limitation two (added after construction)")
    assert len(model.limitations.entries) == 1


def test_136aq_mutating_source_extensions_mapping_after_construction_does_not_affect_model():
    source_extensions = {"note": "original"}
    wire = _rab_wire(_extensions=source_extensions)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_extensions["note"] = "tampered"
    source_extensions["new_key"] = "also tampered"
    assert model.to_dict()["_extensions"] == {"note": "original"}


def test_136aq_mutating_source_reference_dict_after_construction_does_not_affect_model():
    source_gen_ref = _generation_ref()
    wire = _rab_wire(generation_reference=source_gen_ref)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_gen_ref["generation_id"] = "tampered-0000001"
    assert model.generation_reference.generation_id.value == "generatn-0000001"


def test_136aq_mutating_source_publication_evidence_and_marker_reference_dicts_after_construction_does_not_affect_model():
    source_pub_ref = _publication_evidence_ref()
    source_marker_ref = _marker_ref()
    wire = _finalized_rab_wire(publication_evidence_reference=source_pub_ref, marker_reference=source_marker_ref)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_pub_ref["record_id"] = "tampered-0000002"
    source_marker_ref["record_id"] = "tampered-0000003"
    assert model.publication_evidence_reference.record_id.value == "pubevdnc-0000002"
    assert model.marker_reference.record_id.value == "markrbnd-0000003"


def test_136aq_deep_copy_of_model_produces_structurally_equal_but_independent_object():
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(_rab_wire(), schema_version="1.0")
    duplicate = copy.deepcopy(model)
    assert duplicate == model
    assert duplicate is not model


# ---------------------------------------------------------------------------
# 11. Equality verification: structural, not identifier-only/digest-only
# ---------------------------------------------------------------------------


def test_136aq_equality_changes_when_any_field_changes():
    base = auth.FinalizationReceiptAuthorityBinding.from_dict(_rab_wire(), schema_version="1.0")
    same = auth.FinalizationReceiptAuthorityBinding.from_dict(_rab_wire(), schema_version="1.0")
    assert base == same

    different_state = auth.FinalizationReceiptAuthorityBinding.from_dict(
        _rab_wire(receipt_state="stale"), schema_version="1.0"
    )
    assert base != different_state

    different_epoch = auth.FinalizationReceiptAuthorityBinding.from_dict(
        _rab_wire(migration_epoch="epoch-002"), schema_version="1.0"
    )
    assert base != different_epoch

    finalized = auth.FinalizationReceiptAuthorityBinding.from_dict(_finalized_rab_wire(), schema_version="1.0")
    finalized_with_staleness = auth.FinalizationReceiptAuthorityBinding.from_dict(
        _finalized_rab_wire(staleness_check={}), schema_version="1.0"
    )
    assert finalized != finalized_with_staleness


def test_136aq_equality_rejects_identifier_only_and_digest_only_comparison():
    base = auth.FinalizationReceiptAuthorityBinding.from_dict(_rab_wire(), schema_version="1.0")
    same_identity_different_state = auth.FinalizationReceiptAuthorityBinding.from_dict(
        _rab_wire(receipt_state="stale"), schema_version="1.0"
    )
    assert base.envelope.record_id == same_identity_different_state.envelope.record_id
    assert base.envelope.record_digest == same_identity_different_state.envelope.record_digest
    assert base != same_identity_different_state


# ---------------------------------------------------------------------------
# 12. Error-behavior determinism verification
# ---------------------------------------------------------------------------


def test_136aq_invalid_digest_wrapper_rejected():
    with pytest.raises(Exception):
        auth.FinalizationReceiptAuthorityBinding.from_dict(
            _rab_wire(record_digest="not-a-valid-sha256-hex"), schema_version="1.0"
        )


def test_136aq_invalid_identifier_wrapper_rejected():
    with pytest.raises(Exception):
        auth.FinalizationReceiptAuthorityBinding.from_dict(
            _rab_wire(migration_epoch="/../invalid"), schema_version="1.0"
        )


def test_136aq_malformed_reference_missing_record_family_rejected(schema_registry):
    malformed = {"record_id": "pubevdnc-0000009", "record_digest": _sha256("1")}
    wire = _finalized_rab_wire(publication_evidence_reference=malformed)
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_invalid_shape_limitations_not_a_list_rejected(schema_registry):
    wire = _rab_wire(limitations="not-a-list")
    _assert_schema_invalid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136aq_construction_errors_are_deterministic_across_repeated_attempts():
    bad_wire = _rab_wire(receipt_state="not-a-real-state")
    errors = []
    for _ in range(3):
        try:
            auth.FinalizationReceiptAuthorityBinding.from_dict(bad_wire, schema_version="1.0")
        except Exception as exc:  # noqa: BLE001
            errors.append(type(exc))
    assert len(errors) == 3
    assert len(set(errors)) == 1


# ---------------------------------------------------------------------------
# 13. Purely-representational behavior: reject any receipt-management,
#     lifecycle-finalization, or authority-exercising capability
# ---------------------------------------------------------------------------


FORBIDDEN_RECEIPT_MANAGEMENT_SYMBOLS = (
    "create_receipt", "generate_receipt", "publish_receipt", "acknowledge_completion",
    "determine_successful_completion", "determine_failed_completion",
    "validate_receipt_authenticity", "validate_signatures", "verify_hashes",
    "compare_receipt_timestamps", "reconcile_receipt_history", "inspect_receipt_files",
    "discover_receipts", "enumerate_receipts", "locate_receipts", "archive_receipts",
    "promote_receipts", "retire_receipts",
)

FORBIDDEN_LIFECYCLE_SYMBOLS = (
    "finalize_lifecycle", "close_task", "promote_report", "update_metadata",
    "write_completion_marker", "write_project_status", "advance_lifecycle_state",
    "authorize_publication", "mutate_transition",
)

FORBIDDEN_AUTHORITY_EXERCISE_SYMBOLS = (
    "activate_authority", "resolve_authority", "determine_current_authority",
    "compare_authorities", "transfer_authority", "mutate_authority_pointer",
)


def test_136aq_module_defines_no_receipt_management_lifecycle_or_authority_exercise_function_or_method():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_RECEIPT_MANAGEMENT_SYMBOLS:
        assert forbidden not in defined_names, f"forbidden receipt-management symbol {forbidden!r} defined"
    for forbidden in FORBIDDEN_LIFECYCLE_SYMBOLS:
        assert forbidden not in defined_names, f"forbidden lifecycle symbol {forbidden!r} defined"
    for forbidden in FORBIDDEN_AUTHORITY_EXERCISE_SYMBOLS:
        assert forbidden not in defined_names, f"forbidden authority-exercise symbol {forbidden!r} defined"


def test_136aq_module_source_never_imports_filesystem_socket_or_subprocess():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    forbidden_modules = ("socket", "subprocess", "os.path", "shutil", "requests", "urllib")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(f) for f in forbidden_modules)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(f) for f in forbidden_modules)


def test_136aq_module_source_never_references_environment_variables():
    source = BINDINGS_MODULE.read_text()
    for forbidden_token in ("os.environ", "getenv", "os.getenv"):
        assert forbidden_token not in source


def test_136aq_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    wire = _finalized_rab_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    model.to_dict()
    repr(model)


def test_136aq_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(_rab_wire(), schema_version="1.0")
    model.to_dict()


def test_136aq_no_filesystem_write_during_construction_serialization_equality_repr(monkeypatch):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(_rab_wire(), schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136aq_package_reimport_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(rab_module)


# ---------------------------------------------------------------------------
# 14. Runtime isolation: no production import of pcae.cltr.authority
# ---------------------------------------------------------------------------


def test_136aq_no_production_module_imports_authority_package():
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
            # Phase 137K: the sole authorized production Typed Authority Model
            # consumer is permitted to import pcae.cltr.authority (TAMPC-001
            # v1.0, docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md).
            if path.name in {"authority_inspection.py", "authority_inspect.py"}:
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


def test_136aq_authority_bindings_module_does_not_import_receipt_management_or_runtime():
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


def test_136aq_authority_models_module_imports_no_transport_or_filesystem_code_via_full_dependency_walk():
    """Independent re-walk of every module transitively imported by
    bindings.py within the authority package, confirming none imports a
    transport/filesystem-lifecycle module either. A fresh construction of
    the import graph -- not a reuse of any prior phase's scan."""

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
def test_136aq_wheel_build_contains_group_9_module_and_no_later_family(tmp_path: Path):
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
def test_136aq_isolated_install_all_fourteen_families_import_and_round_trip(tmp_path: Path):
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
        "for name in " + repr(FOURTEEN_IMPLEMENTED_RECORD_FAMILIES) + ":\n"
        "    assert hasattr(auth, name), name\n"
        "for name in " + repr(TWO_MUST_NOT_EXIST_RECORD_FAMILIES) + ":\n"
        "    assert not hasattr(auth, name), name\n"
        "wire = {\n"
        "    'schema_id': " + repr(RECEIPT_AUTHORITY_BINDING_SCHEMA_ID) + ",\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'receipt_authority_binding', 'record_id': 'rcptbnd-0000099',\n"
        "    'record_digest': '0'*64, 'created_at': '2026-07-18T12:00:00Z',\n"
        "    'migration_epoch': 'epoch-001',\n"
        "    'generation_reference': {'generation_id': 'generatn-0000099',\n"
        "        'generation_digest': 'a'*64},\n"
        "    'receipt_state': 'absent',\n"
        "    'limitations': [], 'authority_disclosure': {'authority_role': 'derivative',\n"
        "        'is_authoritative': False, 'disclosure_text': 'ok'},\n"
        "}\n"
        "model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version='1.0')\n"
        "assert model.to_dict() == wire\n"
        "print('ISOLATED_INSTALL_OK')\n"
    )
    result = subprocess.run(
        [str(venv_python), "-c", probe], check=True, capture_output=True, text=True,
    )
    assert "ISOLATED_INSTALL_OK" in result.stdout
