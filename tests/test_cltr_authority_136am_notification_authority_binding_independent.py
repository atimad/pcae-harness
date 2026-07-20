"""Phase 136AM: Stage 3 Typed Authority Model Notification Authority
Binding Independent Verification.

Independent re-derivation and verification of Phase 136AL's Typed Model
Implementation Group 7 (``NotificationAuthorityBinding``) against the
frozen contract and live executable schema
(``records/notification_authority_binding.schema.json``,
``shared/references.schema.json``, ``shared/digest.schema.json``,
``shared/identity.schema.json``, ``shared/limitations.schema.json``,
``shared/enums.schema.json``) -- independently, without trusting the
136AL implementation, its own test suite, its report, its comments, or
any prior verification report. Every fixture and assertion below was
derived directly from the executable schema file and the frozen contract
text quoted in its ``description`` fields, then compared against
``src/pcae/cltr/authority/bindings.py``.

Scope: Implementation Group 7 only (``NotificationAuthorityBinding``). No
later record-family model (``MarkerAuthorityBinding``,
``FinalizationReceiptAuthorityBinding``, ``CompatibilityState``,
``QuarantineRecord``) is implemented or exercised here.
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
from pcae.cltr.authority import bindings as nab_module
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

NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/notification_authority_binding.schema.json"
)
AUTHORITY_EPOCH_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json"
MARKER_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/marker_authority_binding.schema.json"
)
RECEIPT_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/receipt_authority_binding.schema.json"
)

TWELVE_IMPLEMENTED_RECORD_FAMILIES = (
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
)

# Narrowed by Phase 136AN (Typed Model Implementation Group 8):
# `MarkerAuthorityBinding` is now authorized, legitimately-implemented
# record-family model -- removed from this still-forbidden list. Narrowed
# further by Phase 136AP (Typed Model Implementation Group 9):
# `FinalizationReceiptAuthorityBinding` is now authorized, legitimately-
# implemented record-family model -- removed from this still-forbidden
# list.
# Narrowed further by Phase 136AR (Typed Model Implementation Group
# 10): `CompatibilityState` is now authorized, legitimately-
# implemented record-family model -- removed from this
# still-forbidden list.
FOUR_MUST_NOT_EXIST_RECORD_FAMILIES = ()  # Narrowed by Phase 136AT: QuarantineRecord (Group 11) now authorized; none remain.


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


def _epoch_ref(record_id: str = "authepch-0000001", digest: str = "1") -> dict:
    return _ref(record_id, digest, "authority_epoch")


def _marker_ref(record_id: str = "markrbnd-0000001", digest: str = "2") -> dict:
    return _ref(record_id, digest, "marker_authority_binding", with_schema=MARKER_AUTHORITY_BINDING_SCHEMA_ID)


def _receipt_ref(record_id: str = "rcptbnd-00000001", digest: str = "3") -> dict:
    return _ref(record_id, digest, "receipt_authority_binding", with_schema=RECEIPT_AUTHORITY_BINDING_SCHEMA_ID)


def _generation_ref(gen_id: str = "generatn-0000001", digest: str = "4") -> dict:
    return {"generation_id": gen_id, "generation_digest": _sha256(digest)}


def _nab_wire(**overrides) -> dict:
    record = {
        "schema_id": NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "notification_authority_binding",
        "record_id": "notifbnd-0000001",
        "record_digest": _sha256("0"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "authoritative_generation_reference": _generation_ref(),
        "authority_epoch_reference": _epoch_ref(),
        "payload_digest": _sha256("5"),
        "attempt_identity": "attempt-00000001",
        "pfn001_classification": "notify.cutover.promoted",
        "delivery_state": "not_dispatched",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# 1. Inventory verification (independent AST + runtime introspection,
#    package export, and registry discovery)
# ---------------------------------------------------------------------------


def test_136am_exactly_twelve_record_family_classes_exist_via_ast():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        class_names |= {
            node.name for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, ast.ClassDef)
        }
    for expected in TWELVE_IMPLEMENTED_RECORD_FAMILIES:
        assert expected in class_names, f"missing expected record family class {expected!r}"
    for forbidden in FOUR_MUST_NOT_EXIST_RECORD_FAMILIES:
        assert forbidden not in class_names, f"forbidden record family class {forbidden!r} exists"
    present_record_families = class_names & set(
        TWELVE_IMPLEMENTED_RECORD_FAMILIES + FOUR_MUST_NOT_EXIST_RECORD_FAMILIES
    )
    assert present_record_families == set(TWELVE_IMPLEMENTED_RECORD_FAMILIES)


def test_136am_package_export_inventory_via_runtime_import():
    for expected in TWELVE_IMPLEMENTED_RECORD_FAMILIES:
        assert hasattr(auth, expected)
        assert isinstance(getattr(auth, expected), type)
        assert expected in auth.__all__
    for forbidden in FOUR_MUST_NOT_EXIST_RECORD_FAMILIES:
        assert not hasattr(auth, forbidden)
        assert forbidden not in auth.__all__


def test_136am_group_7_module_defines_exactly_its_own_one_family():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_names = class_names & set(
        TWELVE_IMPLEMENTED_RECORD_FAMILIES + FOUR_MUST_NOT_EXIST_RECORD_FAMILIES
    )
    assert record_family_names == {"NotificationAuthorityBinding"}


def test_136am_no_forbidden_family_source_file_exists():
    # Narrowed by Phase 136AR: `compatibility_quarantine.py` (Group 10,
    # `CompatibilityState` only) is now a legitimate, authorized module;
    # removed from this still-forbidden list. No other later-group source
    # file (i.e. one containing `QuarantineRecord`) exists.
    for forbidden_file in ():
        assert not (AUTHORITY_PACKAGE_DIR / forbidden_file).exists()
    assert (AUTHORITY_PACKAGE_DIR / "compatibility_quarantine.py").exists()


def test_136am_schema_registry_discovers_notification_authority_binding_schema(schema_registry):
    assert NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID in schema_registry.schema_ids
    assert schema_registry.document(NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID) is not None


# ---------------------------------------------------------------------------
# 2. Independent schema re-derivation: valid wire round-trips against the
#    live executable schema registry (not the Python model's own opinion)
# ---------------------------------------------------------------------------


def test_136am_minimal_valid_not_dispatched_is_schema_valid_and_constructs(schema_registry):
    wire = _nab_wire()
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136am_already_dispatched_with_marker_and_receipt_valid(schema_registry):
    wire = _nab_wire(
        delivery_state="already_dispatched",
        marker_reference=_marker_ref(),
        receipt_reference=_receipt_ref(),
    )
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.marker_reference.record_id.value == "markrbnd-0000001"
    assert model.receipt_reference.record_id.value == "rcptbnd-00000001"


def test_136am_payload_conflict_with_marker_and_uncertainty_valid(schema_registry):
    wire = _nab_wire(
        delivery_state="payload_conflict",
        marker_reference=_marker_ref(),
        uncertainty={"reason": "Conflicting payload observed for this attempt."},
    )
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.uncertainty.reason == "Conflicting payload observed for this attempt."


def test_136am_all_optional_fields_populated_round_trips(schema_registry):
    wire = _nab_wire(
        delivery_state="already_dispatched",
        marker_reference=_marker_ref(),
        receipt_reference=_receipt_ref(),
        _extensions={"note": "independent-verification-tag"},
    )
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


# ---------------------------------------------------------------------------
# 3. Required-field re-derivation: dropping any required key must be
#    rejected both by the live schema and by the model
# ---------------------------------------------------------------------------


NOTIFICATION_AUTHORITY_BINDING_REQUIRED_FIELDS = (
    "schema_id", "schema_version", "contract_version", "record_type", "record_id",
    "record_digest", "created_at", "migration_epoch", "authoritative_generation_reference",
    "authority_epoch_reference", "payload_digest", "attempt_identity", "pfn001_classification",
    "delivery_state", "limitations", "authority_disclosure",
)


@pytest.mark.parametrize("field", NOTIFICATION_AUTHORITY_BINDING_REQUIRED_FIELDS)
def test_136am_missing_required_field_rejected(field, schema_registry):
    wire = _nab_wire()
    del wire[field]
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, KeyError, TypedModelInternalInvariantError)):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_unknown_field_rejected(schema_registry):
    wire = _nab_wire(unknown_field_xyz="nope")
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_exactly_sixteen_required_fields_confirmed_against_live_schema(schema_registry):
    document = schema_registry.document(NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID)
    assert set(document["required"]) == set(NOTIFICATION_AUTHORITY_BINDING_REQUIRED_FIELDS)
    assert len(NOTIFICATION_AUTHORITY_BINDING_REQUIRED_FIELDS) == 16


# ---------------------------------------------------------------------------
# 4. Discriminator / schema_id / schema_version / contract_version fidelity
# ---------------------------------------------------------------------------


def test_136am_wrong_record_type_rejected(schema_registry):
    wire = _nab_wire(record_type="marker_authority_binding")
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_wrong_schema_id_rejected(schema_registry):
    wire = _nab_wire(schema_id=AUTHORITY_EPOCH_SCHEMA_ID)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_wrong_contract_version_rejected(schema_registry):
    wire = _nab_wire(contract_version="2.0")
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_unsupported_schema_version_rejected_before_payload_inspection():
    wire = _nab_wire()
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="2.0")
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="9.9")


# ---------------------------------------------------------------------------
# 5. Enum verification -- every valid member, plus invalid/case/whitespace/
#    null/omission/int/bool.
# ---------------------------------------------------------------------------


DELIVERY_STATE_MEMBERS = ("not_dispatched", "already_dispatched", "payload_conflict")


@pytest.mark.parametrize("member", DELIVERY_STATE_MEMBERS)
def test_136am_delivery_state_every_valid_member_accepted_with_conditionals_satisfied(member, schema_registry):
    kwargs = {"delivery_state": member}
    if member in ("already_dispatched", "payload_conflict"):
        kwargs["marker_reference"] = _marker_ref()
    if member == "already_dispatched":
        kwargs["receipt_reference"] = _receipt_ref()
    if member == "payload_conflict":
        kwargs["uncertainty"] = {"reason": "Independent-verification uncertainty disclosure."}
    wire = _nab_wire(**kwargs)
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.delivery_state.value == member


@pytest.mark.parametrize(
    "bad_value",
    ["NOT_DISPATCHED", "not dispatched", " already_dispatched", "already_dispatched ", "unknown", "", None, 1, True],
)
def test_136am_delivery_state_invalid_values_rejected(bad_value, schema_registry):
    wire = _nab_wire(delivery_state=bad_value)
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_delivery_state_field_omission_rejected(schema_registry):
    wire = _nab_wire()
    del wire["delivery_state"]
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_delivery_state_has_exactly_three_members_confirmed_against_live_schema(schema_registry):
    document = schema_registry.document(NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID)
    schema_enum = set(document["$defs"]["delivery_state"]["enum"])
    assert schema_enum == set(DELIVERY_STATE_MEMBERS)
    assert {m.value for m in nab_module.DeliveryState} == set(DELIVERY_STATE_MEMBERS)


# ---------------------------------------------------------------------------
# 6. Conditional-rule verification: both positive and negative cases for
#    all three delivery_state-gated conditionals, guarding against
#    unauthorized strengthening/weakening/broadening/narrowing.
# ---------------------------------------------------------------------------


# 6.1 uncertainty <-> delivery_state == payload_conflict (strict biconditional)


def test_136am_payload_conflict_without_uncertainty_rejected(schema_registry):
    wire = _nab_wire(delivery_state="payload_conflict", marker_reference=_marker_ref())
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_conflict_state", ["not_dispatched", "already_dispatched"])
def test_136am_non_payload_conflict_forbids_uncertainty(non_conflict_state, schema_registry):
    kwargs = {"delivery_state": non_conflict_state}
    if non_conflict_state == "already_dispatched":
        kwargs["marker_reference"] = _marker_ref()
        kwargs["receipt_reference"] = _receipt_ref()
    kwargs["uncertainty"] = {"reason": "Should not be present here."}
    wire = _nab_wire(**kwargs)
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


# 6.2 marker_reference <-> delivery_state != not_dispatched (strict biconditional)


def test_136am_not_dispatched_forbids_marker_reference(schema_registry):
    wire = _nab_wire(delivery_state="not_dispatched", marker_reference=_marker_ref())
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_already_dispatched_without_marker_reference_rejected(schema_registry):
    wire = _nab_wire(delivery_state="already_dispatched", receipt_reference=_receipt_ref())
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_payload_conflict_without_marker_reference_rejected(schema_registry):
    wire = _nab_wire(
        delivery_state="payload_conflict",
        uncertainty={"reason": "Conflict without a marker reference."},
    )
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


# 6.3 receipt_reference <-> delivery_state == already_dispatched (strict biconditional)


def test_136am_already_dispatched_without_receipt_reference_rejected(schema_registry):
    wire = _nab_wire(delivery_state="already_dispatched", marker_reference=_marker_ref())
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_dispatched_state", ["not_dispatched", "payload_conflict"])
def test_136am_non_already_dispatched_forbids_receipt_reference(non_dispatched_state, schema_registry):
    kwargs = {"delivery_state": non_dispatched_state, "receipt_reference": _receipt_ref()}
    if non_dispatched_state == "payload_conflict":
        kwargs["marker_reference"] = _marker_ref()
        kwargs["uncertainty"] = {"reason": "Independent-verification uncertainty disclosure."}
    else:
        # not_dispatched additionally forbids marker_reference; omit it, but
        # supplying a receipt_reference alone must already be rejected.
        pass
    wire = _nab_wire(**kwargs)
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_no_unauthorized_conditional_linking_uncertainty_to_marker_or_receipt(schema_registry):
    """The schema links uncertainty only to delivery_state=='payload_conflict'
    -- never to marker_reference or receipt_reference presence directly.
    An 'already_dispatched' record (which requires both marker_reference
    and receipt_reference) must remain valid with no uncertainty object,
    proving the implementation does not invent an uncertainty-requires-
    marker or uncertainty-requires-receipt link."""

    wire = _nab_wire(
        delivery_state="already_dispatched",
        marker_reference=_marker_ref(),
        receipt_reference=_receipt_ref(),
    )
    assert "uncertainty" not in wire
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.uncertainty is ABSENT


def test_136am_conditionals_do_not_cross_reference_each_others_reference_family(schema_registry):
    """marker_reference and receipt_reference are independently
    family-restricted; the schema never requires marker_reference to
    equal or relate to receipt_reference's target -- two structurally
    unrelated references must both independently validate."""

    wire = _nab_wire(
        delivery_state="already_dispatched",
        marker_reference=_marker_ref("markrbnd-0000009", "8"),
        receipt_reference=_receipt_ref("rcptbnd-00000009", "9"),
    )
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.marker_reference.record_id.value != model.receipt_reference.record_id.value


# ---------------------------------------------------------------------------
# 7. Reference verification: target family, schema_id/schema_version
#    cross-family requirement, wrapper type, nullability, no lookup.
# ---------------------------------------------------------------------------


def test_136am_authority_epoch_reference_wrong_family_rejected(schema_registry):
    wire = _nab_wire(
        authority_epoch_reference=_ref("markrbnd-0000002", "6", "marker_authority_binding")
    )
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, WrongFamilyReferenceError)):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_authority_epoch_reference_does_not_require_schema_id_or_version(schema_registry):
    wire = _nab_wire()
    assert "schema_id" not in wire["authority_epoch_reference"]
    assert "schema_version" not in wire["authority_epoch_reference"]
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.authority_epoch_reference.schema_id is ABSENT
    assert model.authority_epoch_reference.schema_version is ABSENT


def test_136am_marker_reference_wrong_family_rejected(schema_registry):
    wire = _nab_wire(
        delivery_state="payload_conflict",
        marker_reference=_ref(
            "rcptbnd-00000002", "7", "receipt_authority_binding", with_schema=RECEIPT_AUTHORITY_BINDING_SCHEMA_ID
        ),
        uncertainty={"reason": "Wrong-family marker reference test."},
    )
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, WrongFamilyReferenceError)):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_receipt_reference_wrong_family_rejected(schema_registry):
    wire = _nab_wire(
        delivery_state="already_dispatched",
        marker_reference=_marker_ref(),
        receipt_reference=_ref(
            "markrbnd-0000003", "8", "marker_authority_binding", with_schema=MARKER_AUTHORITY_BINDING_SCHEMA_ID
        ),
    )
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises((TypedModelConstructionError, WrongFamilyReferenceError)):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_marker_reference_missing_schema_id_rejected(schema_registry):
    bare_marker = {"record_id": "markrbnd-0000004", "record_digest": _sha256("1"), "record_family": "marker_authority_binding"}
    wire = _nab_wire(delivery_state="payload_conflict", marker_reference=bare_marker, uncertainty={"reason": "x"})
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_receipt_reference_missing_schema_version_rejected(schema_registry):
    bare_receipt = {
        "record_id": "rcptbnd-00000003",
        "record_digest": _sha256("2"),
        "record_family": "receipt_authority_binding",
        "schema_id": RECEIPT_AUTHORITY_BINDING_SCHEMA_ID,
    }
    wire = _nab_wire(
        delivery_state="already_dispatched",
        marker_reference=_marker_ref(),
        receipt_reference=bare_receipt,
    )
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_generation_reference_wrapper_type_and_pairing(schema_registry):
    wire = _nab_wire()
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert type(model.authoritative_generation_reference).__name__ == "GenerationReference"
    assert model.authoritative_generation_reference.generation_id.value == "generatn-0000001"
    assert model.authoritative_generation_reference.generation_digest.value == _sha256("4")


def test_136am_generation_reference_has_no_schema_id_or_version_fields(schema_registry):
    document = schema_registry.document(NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID)
    # Resolved indirectly via shared/references.schema.json; confirm the
    # wire fixture itself carries no schema_id/schema_version on this field
    # (generation_reference's own additionalProperties:false forbids them).
    wire = _nab_wire()
    assert set(wire["authoritative_generation_reference"].keys()) == {"generation_id", "generation_digest"}
    assert document["properties"]["authoritative_generation_reference"]["$ref"].endswith(
        "generation_reference"
    )


def test_136am_valid_but_nonexistent_reference_succeeds_no_lookup_performed(schema_registry, monkeypatch):
    """A reference naming a plausible-but-never-registered record_id must
    construct successfully -- no filesystem/registry lookup may be
    performed to check existence."""

    def _boom(*a, **k):
        raise AssertionError("unexpected filesystem access during reference construction")

    monkeypatch.setattr("builtins.open", _boom)
    wire = _nab_wire(authority_epoch_reference=_epoch_ref("authepch-9999999", "f"))
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.authority_epoch_reference.record_id.value == "authepch-9999999"


def test_136am_no_lookup_or_authority_resolution_symbols_defined():
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


def test_136am_uncertainty_marker_receipt_absent_by_default():
    wire = _nab_wire()
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.uncertainty is ABSENT
    assert model.marker_reference is ABSENT
    assert model.receipt_reference is ABSENT
    serialized = model.to_dict()
    assert "uncertainty" not in serialized
    assert "marker_reference" not in serialized
    assert "receipt_reference" not in serialized


def test_136am_uncertainty_explicit_null_rejected_not_collapsed_to_absent(schema_registry):
    wire = _nab_wire()
    wire["uncertainty"] = None
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_marker_reference_explicit_null_rejected_not_collapsed_to_absent(schema_registry):
    wire = _nab_wire()
    wire["marker_reference"] = None
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_extensions_absent_by_default_and_explicit_null_rejected(schema_registry):
    wire = _nab_wire()
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model._extensions is ABSENT
    wire_with_null_ext = _nab_wire(_extensions=None)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire_with_null_ext, schema_version="1.0")


def test_136am_extensions_populated_string_valued_map_round_trips(schema_registry):
    wire = _nab_wire(_extensions={"note": "independent-verification-tag"})
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.to_dict()["_extensions"] == {"note": "independent-verification-tag"}


def test_136am_extensions_non_string_value_rejected(schema_registry):
    wire = _nab_wire(_extensions={"note": 123})
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_extensions_reserved_key_collision_rejected():
    wire = _nab_wire(_extensions={"migration_epoch": "shadowing-attempt"})
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_extensions_max_properties_bound_confirmed_against_live_schema(schema_registry):
    document = schema_registry.document(NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID)
    assert document["properties"]["_extensions"]["maxProperties"] == 32
    from pcae.cltr.authority.extensions import MAX_EXTENSION_PROPERTIES

    assert MAX_EXTENSION_PROPERTIES == 32


# ---------------------------------------------------------------------------
# 9. Authority-role locally-forbidden 'authoritative' verification
# ---------------------------------------------------------------------------


def test_136am_authoritative_role_rejected(schema_registry):
    wire = _nab_wire(authority_disclosure=_disclosure(role="authoritative"))
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "role", ["derivative", "operational", "evidence", "compatibility", "historical", "quarantined"]
)
def test_136am_every_non_authoritative_role_accepted(role, schema_registry):
    wire = _nab_wire(authority_disclosure=_disclosure(role=role))
    _assert_schema_valid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.authority_role.value == role


def test_136am_is_authoritative_true_rejected():
    disclosure = _disclosure()
    disclosure["is_authoritative"] = True
    wire = _nab_wire(authority_disclosure=disclosure)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 10. Immutability verification (recursive; mutating source after
#     construction must never affect the model)
# ---------------------------------------------------------------------------


def test_136am_is_frozen_dataclass():
    model = auth.NotificationAuthorityBinding.from_dict(_nab_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.delivery_state = nab_module.DeliveryState.ALREADY_DISPATCHED


def test_136am_uncertainty_value_object_is_frozen_dataclass():
    wire = _nab_wire(
        delivery_state="payload_conflict",
        marker_reference=_marker_ref(),
        uncertainty={"reason": "x"},
    )
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.uncertainty.reason = "tampered"


def test_136am_mutating_source_limitations_list_after_construction_does_not_affect_model():
    source_limitations = ["limitation one"]
    wire = _nab_wire(limitations=source_limitations)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_limitations.append("limitation two (added after construction)")
    assert len(model.limitations.entries) == 1


def test_136am_mutating_source_extensions_mapping_after_construction_does_not_affect_model(schema_registry):
    source_extensions = {"note": "original"}
    wire = _nab_wire(_extensions=source_extensions)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_extensions["note"] = "tampered"
    source_extensions["new_key"] = "also tampered"
    assert model.to_dict()["_extensions"] == {"note": "original"}


def test_136am_mutating_source_reference_dict_after_construction_does_not_affect_model():
    source_epoch_ref = _epoch_ref()
    wire = _nab_wire(authority_epoch_reference=source_epoch_ref)
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    source_epoch_ref["record_id"] = "tampered-0000001"
    assert model.authority_epoch_reference.record_id.value == "authepch-0000001"


def test_136am_deep_copy_of_model_produces_structurally_equal_but_independent_object():
    model = auth.NotificationAuthorityBinding.from_dict(_nab_wire(), schema_version="1.0")
    duplicate = copy.deepcopy(model)
    assert duplicate == model
    assert duplicate is not model


# ---------------------------------------------------------------------------
# 11. Equality verification: structural, not identifier-only/digest-only
# ---------------------------------------------------------------------------


def test_136am_equality_changes_when_any_field_changes():
    base = auth.NotificationAuthorityBinding.from_dict(_nab_wire(), schema_version="1.0")
    same = auth.NotificationAuthorityBinding.from_dict(_nab_wire(), schema_version="1.0")
    assert base == same

    different_classification = auth.NotificationAuthorityBinding.from_dict(
        _nab_wire(pfn001_classification="notify.other.classification"), schema_version="1.0"
    )
    assert base != different_classification

    different_epoch = auth.NotificationAuthorityBinding.from_dict(
        _nab_wire(migration_epoch="epoch-002"), schema_version="1.0"
    )
    assert base != different_epoch


def test_136am_equality_rejects_identifier_only_and_digest_only_comparison():
    base = auth.NotificationAuthorityBinding.from_dict(_nab_wire(), schema_version="1.0")
    same_identity_different_payload_digest = auth.NotificationAuthorityBinding.from_dict(
        _nab_wire(payload_digest=_sha256("9")), schema_version="1.0"
    )
    assert base.envelope.record_id == same_identity_different_payload_digest.envelope.record_id
    assert base.envelope.record_digest == same_identity_different_payload_digest.envelope.record_digest
    assert base != same_identity_different_payload_digest


def test_136am_reference_equality_is_structural_not_family_only():
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


def test_136am_invalid_digest_wrapper_rejected():
    with pytest.raises(Exception):
        auth.NotificationAuthorityBinding.from_dict(
            _nab_wire(record_digest="not-a-valid-sha256-hex"), schema_version="1.0"
        )


def test_136am_invalid_identifier_wrapper_rejected():
    with pytest.raises(Exception):
        auth.NotificationAuthorityBinding.from_dict(
            _nab_wire(migration_epoch="/../invalid"), schema_version="1.0"
        )


def test_136am_malformed_reference_missing_record_family_rejected(schema_registry):
    malformed = {"record_id": "authepch-0000009", "record_digest": _sha256("1")}
    wire = _nab_wire(authority_epoch_reference=malformed)
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_invalid_shape_limitations_not_a_list_rejected(schema_registry):
    wire = _nab_wire(limitations="not-a-list")
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136am_construction_errors_are_deterministic_across_repeated_attempts():
    bad_wire = _nab_wire(delivery_state="not-a-real-state")
    errors = []
    for _ in range(3):
        try:
            auth.NotificationAuthorityBinding.from_dict(bad_wire, schema_version="1.0")
        except Exception as exc:  # noqa: BLE001
            errors.append(type(exc))
    assert len(errors) == 3
    assert len(set(errors)) == 1


def test_136am_pfn001_classification_bounds_and_charset(schema_registry):
    too_long = "x" * 257
    wire = _nab_wire(pfn001_classification=too_long)
    _assert_schema_invalid(wire, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")

    empty = ""
    wire2 = _nab_wire(pfn001_classification=empty)
    _assert_schema_invalid(wire2, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire2, schema_version="1.0")

    non_ascii = "classification\nwith\nnewlines"
    wire3 = _nab_wire(pfn001_classification=non_ascii)
    _assert_schema_invalid(wire3, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.NotificationAuthorityBinding.from_dict(wire3, schema_version="1.0")

    exactly_256 = "x" * 256
    wire4 = _nab_wire(pfn001_classification=exactly_256)
    _assert_schema_valid(wire4, NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    auth.NotificationAuthorityBinding.from_dict(wire4, schema_version="1.0")


# ---------------------------------------------------------------------------
# 13. Purely-representational behavior: reject any operational capability
# ---------------------------------------------------------------------------


FORBIDDEN_OPERATIONAL_SYMBOLS = (
    "send_notification", "dispatch_notification", "dispatch_telegram", "dispatch_email",
    "dispatch_slack", "resolve_provider", "resolve_delivery_channel", "inspect_runtime_config",
    "inspect_environment", "determine_success", "determine_failure", "build_payload",
    "queue_notification", "schedule_notification", "retry_notification", "mutate_notification_state",
    "activate_authority", "resolve_authority", "determine_current_authority", "compare_authorities",
    "transfer_authority", "mutate_authority_pointer", "modify_lifecycle_state",
)


def test_136am_module_defines_no_operational_function_or_method():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_OPERATIONAL_SYMBOLS:
        assert forbidden not in defined_names, f"forbidden operational symbol {forbidden!r} defined"


def test_136am_module_source_never_imports_filesystem_socket_or_subprocess():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    forbidden_modules = ("socket", "subprocess", "os.path", "shutil", "requests", "urllib")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(f) for f in forbidden_modules)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(f) for f in forbidden_modules)


def test_136am_module_source_never_references_environment_variables():
    source = BINDINGS_MODULE.read_text()
    for forbidden_token in ("os.environ", "getenv", "os.getenv"):
        assert forbidden_token not in source


def test_136am_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    wire = _nab_wire(delivery_state="already_dispatched", marker_reference=_marker_ref(), receipt_reference=_receipt_ref())
    model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version="1.0")
    model.to_dict()
    repr(model)


def test_136am_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    model = auth.NotificationAuthorityBinding.from_dict(_nab_wire(), schema_version="1.0")
    model.to_dict()


def test_136am_no_filesystem_write_during_construction_serialization_equality_repr(monkeypatch):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    model = auth.NotificationAuthorityBinding.from_dict(_nab_wire(), schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136am_package_reimport_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(nab_module)


# ---------------------------------------------------------------------------
# 14. Runtime isolation: no production import of pcae.cltr.authority
# ---------------------------------------------------------------------------


def test_136am_no_production_module_imports_authority_package():
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


def test_136am_authority_bindings_module_does_not_import_notification_transport_or_runtime():
    forbidden_modules = (
        "pcae.cltr.notification", "pcae.cltr.marker", "pcae.cltr.receipt",
        "pcae.commands", "pcae.core", "pcae.runtime", "telegram", "smtplib", "slack_sdk",
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


def test_136am_authority_models_module_imports_no_transport_code_via_full_dependency_walk():
    """Independent re-walk of every module transitively imported by
    bindings.py within the authority package, confirming none imports a
    transport/runtime module either."""

    visited: set[Path] = set()
    to_visit = [BINDINGS_MODULE]
    forbidden_modules = ("socket", "subprocess", "telegram", "smtplib", "requests", "urllib.request")
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
def test_136am_wheel_build_contains_group_7_module_and_no_later_family(tmp_path: Path):
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
def test_136am_isolated_install_all_twelve_families_import_and_round_trip(tmp_path: Path):
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
        "for name in " + repr(TWELVE_IMPLEMENTED_RECORD_FAMILIES) + ":\n"
        "    assert hasattr(auth, name), name\n"
        "for name in " + repr(FOUR_MUST_NOT_EXIST_RECORD_FAMILIES) + ":\n"
        "    assert not hasattr(auth, name), name\n"
        "wire = {\n"
        "    'schema_id': " + repr(NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID) + ",\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'notification_authority_binding', 'record_id': 'notifbnd-0000099',\n"
        "    'record_digest': '0'*64, 'created_at': '2026-07-18T12:00:00Z',\n"
        "    'migration_epoch': 'epoch-001',\n"
        "    'authoritative_generation_reference': {'generation_id': 'generatn-0000099',\n"
        "        'generation_digest': 'a'*64},\n"
        "    'authority_epoch_reference': {'record_id': 'authepch-0000099', 'record_digest': 'b'*64,\n"
        "                                  'record_family': 'authority_epoch'},\n"
        "    'payload_digest': 'c'*64, 'attempt_identity': 'attempt-00000099',\n"
        "    'pfn001_classification': 'notify.cutover.promoted',\n"
        "    'delivery_state': 'not_dispatched',\n"
        "    'limitations': [], 'authority_disclosure': {'authority_role': 'derivative',\n"
        "        'is_authoritative': False, 'disclosure_text': 'ok'},\n"
        "}\n"
        "model = auth.NotificationAuthorityBinding.from_dict(wire, schema_version='1.0')\n"
        "assert model.to_dict() == wire\n"
        "print('ISOLATED_INSTALL_OK')\n"
    )
    result = subprocess.run(
        [str(venv_python), "-c", probe], check=True, capture_output=True, text=True,
    )
    assert "ISOLATED_INSTALL_OK" in result.stdout
