"""Phase 136AS: Stage 3 Typed Authority Model CompatibilityState
Independent Verification.

Independent re-derivation and verification of Phase 136AR's Typed Model
Implementation Group 10 (``CompatibilityState``) against the frozen contract
and live executable schema
(``records/compatibility_state.schema.json``,
``shared/enums.schema.json``, ``shared/identity.schema.json``,
``shared/digest.schema.json``, ``shared/limitations.schema.json``,
``shared/envelope.schema.json``) -- independently, without trusting the
136AR implementation, its own test suite
(``test_cltr_authority_136ar_compatibility_state.py``), its report, its
comments, or any prior verification report. Every fixture and assertion
below was derived directly from the executable schema file
(``compatibility_state.schema.json``) and the frozen contract text quoted in
its ``description`` fields, then compared against
``src/pcae/cltr/authority/compatibility_quarantine.py``.

Independently re-derived CompatibilityState contract (from the live schema
only, then confirmed against the Python model with an exhaustive
schema-vs-model parity sweep, see the parametric tests below):

  discriminator      record_type const "compatibility_state"
  schema_id          const https://pcae.local/schemas/cltr_cutover/records/
                     compatibility_state.schema.json
  contract_version   const "1.0"
  schema_version     "MAJOR.MINOR" shape; only "1.0" supported by the model
  16 required fields  schema_id, schema_version, contract_version,
                     record_type, record_id, record_digest, created_at,
                     migration_epoch, component, role, allowed_reads,
                     forbidden_authority_use, fallback_disabled, mode,
                     limitations, authority_disclosure
  2 optional fields   retirement_state (CONDITIONAL, see below), _extensions
  role               local 2-value enum {compatibility, historical}
                     (distinct from authority_disclosure.authority_role)
  mode               shared CompatibilityMode, 6 values
                     {legacy_authoritative, legacy_adapter, legacy_read_only,
                      legacy_historical, legacy_disabled, legacy_retired}
  authority_role     shared 7-value enum, but "authoritative" locally
                     forbidden on this record family
  forbidden_authority_use  const true
  fallback_disabled  boolean
  component          string, minLen 1, maxLen 256, pattern ^[\\x20-\\x7E]*$
  allowed_reads      array, maxItems 64, item string minLen 1 maxLen 512,
                     forbidding literal '..' and C0/C1 control chars
  retirement_state   empty-object-only ({}) placeholder (DEFERRED-136V-1)
  _extensions        string-valued map, maxProperties 32
  conditional 1      mode==legacy_retired  => retirement_state REQUIRED;
                     any other mode        => retirement_state FORBIDDEN
  conditional 2      mode in {legacy_historical, legacy_disabled,
                     legacy_retired} => authority_disclosure.authority_role
                     restricted to {historical, compatibility}
  reference family   NONE (no record_reference / schema_id+schema_version
                     pinned nested reference object on this family)

Scope: Implementation Group 10 only (``CompatibilityState``). No later
record-family model (``QuarantineRecord``) is implemented or exercised here;
QuarantineRecord must remain absent.
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
from pcae.cltr.authority import compatibility_quarantine as cs_module
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
COMPAT_MODULE = AUTHORITY_PACKAGE_DIR / "compatibility_quarantine.py"
COMPAT_SCHEMA_FILE = (
    REPO_ROOT
    / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "records"
    / "compatibility_state.schema.json"
)

COMPATIBILITY_STATE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/compatibility_state.schema.json"
)
AUTHORITY_EPOCH_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json"
)

# The fifteen legitimately-implemented record-family models (Groups 2-10).
# Narrowed by Phase 136AT (Group 11, scope-guard evolution: 1 of 1 name
# moved): QuarantineRecord is now legitimately implemented too, so it has
# moved from MUST_NOT_EXIST_RECORD_FAMILIES into this tuple. No other name
# in either tuple changed.
FIFTEEN_IMPLEMENTED_RECORD_FAMILIES = (
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

# No sixteenth family remains to guard against; QuarantineRecord (formerly
# named here) is now implemented, per Phase 136AT.
MUST_NOT_EXIST_RECORD_FAMILIES = ()

# Independently derived from the schema; asserted equal to the live schema's
# own "required" list in test_136as_required_field_set_matches_live_schema.
REQUIRED_FIELDS = (
    "schema_id",
    "schema_version",
    "contract_version",
    "record_type",
    "record_id",
    "record_digest",
    "created_at",
    "migration_epoch",
    "component",
    "role",
    "allowed_reads",
    "forbidden_authority_use",
    "fallback_disabled",
    "mode",
    "limitations",
    "authority_disclosure",
)

COMPATIBILITY_MODE_MEMBERS = (
    "legacy_authoritative",
    "legacy_adapter",
    "legacy_read_only",
    "legacy_historical",
    "legacy_disabled",
    "legacy_retired",
)
MODES_RESTRICTING_AUTHORITY_ROLE = ("legacy_historical", "legacy_disabled", "legacy_retired")
MODES_UNRESTRICTED = ("legacy_authoritative", "legacy_adapter", "legacy_read_only")
ROLE_MEMBERS = ("compatibility", "historical")
AUTHORITY_ROLE_MEMBERS = (
    "authoritative",
    "derivative",
    "operational",
    "evidence",
    "compatibility",
    "historical",
    "quarantined",
)


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


@pytest.fixture(scope="module")
def live_schema():
    return json.loads(COMPAT_SCHEMA_FILE.read_text())


def _assert_schema_valid(record: dict, registry) -> None:
    result = validate_record_shape(record, schema_id=COMPATIBILITY_STATE_SCHEMA_ID, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


def _assert_schema_invalid(record: dict, registry) -> None:
    result = validate_record_shape(record, schema_id=COMPATIBILITY_STATE_SCHEMA_ID, registry=registry)
    assert result.status is not OutcomeStatus.VALID


def _sha256(fill: str = "0") -> str:
    assert len(fill) == 1
    return fill * 64


def _disclosure(role: str = "compatibility") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Independent-verification schema-validated non-authoritative record.",
    }


def _wire(**overrides) -> dict:
    """A schema-valid CompatibilityState wire document. Default mode is
    legacy_adapter (an *unrestricted* mode, so authority_role is free and no
    retirement_state is permitted) -- deliberately chosen so the base fixture
    exercises the else-branches of both conditionals."""

    record = {
        "schema_id": COMPATIBILITY_STATE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "compatibility_state",
        "record_id": "compstat-0000001",
        "record_digest": _sha256("0"),
        "created_at": "2026-07-19T00:00:00Z",
        "migration_epoch": "epoch-001",
        "component": "legacy.component.name",
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


def _retired_wire(**overrides) -> dict:
    """A schema-valid retired document: mode legacy_retired requires
    retirement_state and restricts authority_role to {historical,
    compatibility}."""

    base = {
        "mode": "legacy_retired",
        "role": "historical",
        "retirement_state": {},
        "authority_disclosure": _disclosure("historical"),
    }
    base.update(overrides)
    return _wire(**base)


def _model_valid(wire: dict) -> bool:
    try:
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")
        return True
    except Exception:  # noqa: BLE001
        return False


def _schema_valid(wire: dict, registry) -> bool:
    return validate_record_shape(
        wire, schema_id=COMPATIBILITY_STATE_SCHEMA_ID, registry=registry
    ).status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 1. Inventory verification (AST + runtime introspection + package export +
#    schema-registry discovery). Exactly fifteen families; QuarantineRecord
#    absent.
# ---------------------------------------------------------------------------


def test_136as_exactly_sixteen_record_family_classes_exist_via_ast():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        class_names |= {
            node.name for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, ast.ClassDef)
        }
    for expected in FIFTEEN_IMPLEMENTED_RECORD_FAMILIES:
        assert expected in class_names, f"missing expected record family class {expected!r}"
    for forbidden in MUST_NOT_EXIST_RECORD_FAMILIES:
        assert forbidden not in class_names, f"forbidden record family class {forbidden!r} exists"
    present = class_names & set(FIFTEEN_IMPLEMENTED_RECORD_FAMILIES + MUST_NOT_EXIST_RECORD_FAMILIES)
    assert present == set(FIFTEEN_IMPLEMENTED_RECORD_FAMILIES)


def test_136as_package_export_inventory_via_runtime_import():
    for expected in FIFTEEN_IMPLEMENTED_RECORD_FAMILIES:
        assert hasattr(auth, expected)
        assert isinstance(getattr(auth, expected), type)
        assert expected in auth.__all__
    for forbidden in MUST_NOT_EXIST_RECORD_FAMILIES:
        assert not hasattr(auth, forbidden)
        assert forbidden not in auth.__all__


def test_136as_group_10_module_defines_compatibility_state_and_quarantine_record_families():
    # Narrowed by Phase 136AT (Group 11): this module now legitimately
    # defines QuarantineRecord alongside this phase's own CompatibilityState.
    tree = ast.parse(COMPAT_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_names = class_names & set(
        FIFTEEN_IMPLEMENTED_RECORD_FAMILIES + MUST_NOT_EXIST_RECORD_FAMILIES
    )
    assert record_family_names == {"CompatibilityState", "QuarantineRecord"}
    # CompatibilityRole (the local role enum) is not a record-family model.
    assert "CompatibilityRole" in class_names


def test_136as_module_all_exports_role_enum_and_both_group_10_and_11_models():
    # Narrowed by Phase 136AT (Group 11): the module's public export
    # inventory now also includes QuarantineRecord/ObjectType/QuarantineState.
    assert set(cs_module.__all__) == {
        "CompatibilityRole",
        "CompatibilityState",
        "ObjectType",
        "QuarantineState",
        "QuarantineRecord",
    }


def test_136as_quarantine_record_now_defined_in_module():
    # Narrowed by Phase 136AT (Group 11): supersedes this test's prior
    # absence assertion. QuarantineRecord's own dedicated coverage lives
    # in test_cltr_authority_136at_quarantine_record.py.
    tree = ast.parse(COMPAT_MODULE.read_text())
    defined = {
        n.name for n in ast.walk(tree)
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "QuarantineRecord" in defined
    assert "QuarantineRecord" in cs_module.__all__
    assert hasattr(cs_module, "QuarantineRecord")


def test_136as_schema_registry_discovers_compatibility_state_schema(schema_registry):
    assert COMPATIBILITY_STATE_SCHEMA_ID in schema_registry.schema_ids
    assert schema_registry.document(COMPATIBILITY_STATE_SCHEMA_ID) is not None


# ---------------------------------------------------------------------------
# 2. Valid wire round-trips against the live executable schema registry.
# ---------------------------------------------------------------------------


def test_136as_minimal_valid_is_schema_valid_and_round_trips(schema_registry):
    wire = _wire()
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136as_retired_with_retirement_state_valid_and_round_trips(schema_registry):
    wire = _retired_wire()
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.mode.value == "legacy_retired"
    assert model.to_dict() == wire


def test_136as_all_optional_and_populated_fields_round_trip(schema_registry):
    wire = _wire(
        allowed_reads=["config/a.json", "state/b.txt"],
        fallback_disabled=True,
        limitations=["disclosure one", "disclosure two"],
        _extensions={"note": "independent-verification-tag"},
    )
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


# ---------------------------------------------------------------------------
# 3. Required-field re-derivation.
# ---------------------------------------------------------------------------


def test_136as_required_field_set_matches_live_schema(live_schema):
    assert set(live_schema["required"]) == set(REQUIRED_FIELDS)
    assert len(REQUIRED_FIELDS) == 16


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_136as_missing_required_field_rejected(field, schema_registry):
    wire = _wire()
    del wire[field]
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises((TypedModelConstructionError, TypedModelInternalInvariantError, KeyError)):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_unknown_field_rejected(schema_registry):
    wire = _wire(unexpected_field_xyz="nope")
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_additional_properties_false_confirmed_against_live_schema(live_schema):
    assert live_schema["additionalProperties"] is False


def test_136as_no_phase_id_or_transition_id_fields(live_schema):
    assert "phase_id" not in live_schema["properties"]
    assert "transition_id" not in live_schema["properties"]


def test_136as_migration_epoch_required_despite_cross_phase_family(live_schema):
    # NON-BLOCKING-136V-1: migration_epoch stays required even though this
    # family is exempted from phase_id/transition_id.
    assert "migration_epoch" in live_schema["required"]
    assert "migration_epoch" in live_schema["properties"]


# ---------------------------------------------------------------------------
# 4. Discriminator / schema identity fidelity.
# ---------------------------------------------------------------------------


def test_136as_wrong_record_type_rejected(schema_registry):
    wire = _wire(record_type="quarantine_record")
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_wrong_schema_id_rejected(schema_registry):
    wire = _wire(schema_id=AUTHORITY_EPOCH_SCHEMA_ID)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_wrong_contract_version_rejected(schema_registry):
    wire = _wire(contract_version="2.0")
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_schema_id_const_matches_module_constant(live_schema):
    assert live_schema["properties"]["schema_id"]["const"] == COMPATIBILITY_STATE_SCHEMA_ID
    assert cs_module._COMPATIBILITY_STATE_SCHEMA_ID == COMPATIBILITY_STATE_SCHEMA_ID
    assert live_schema["properties"]["record_type"]["const"] == "compatibility_state"


def test_136as_unsupported_schema_version_rejected_before_payload_inspection():
    wire = _wire()
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.CompatibilityState.from_dict(wire, schema_version="2.0")
    with pytest.raises(UnsupportedSchemaVersionError):
        auth.CompatibilityState.from_dict(wire, schema_version="9.9")


# ---------------------------------------------------------------------------
# 5. Enum verification -- role (local 2-value), mode (shared 6-value),
#    authority_role (shared 7-value minus locally-forbidden authoritative).
# ---------------------------------------------------------------------------


def test_136as_role_enum_members_match_live_schema(live_schema):
    schema_enum = set(live_schema["$defs"]["compatibility_role"]["enum"])
    assert schema_enum == set(ROLE_MEMBERS)
    assert {m.value for m in cs_module.CompatibilityRole} == set(ROLE_MEMBERS)


@pytest.mark.parametrize("member", ROLE_MEMBERS)
def test_136as_role_every_valid_member_accepted(member, schema_registry):
    wire = _wire(role=member)
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.role.value == member


@pytest.mark.parametrize(
    "bad_value",
    ["Compatibility", "COMPATIBILITY", "compatibility ", " historical", "operational",
     "authoritative", "derivative", "quarantined", "", None, 1, True],
)
def test_136as_role_invalid_values_rejected(bad_value, schema_registry):
    wire = _wire(role=bad_value)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_mode_enum_members_match_shared_schema(live_schema, schema_registry):
    shared = schema_registry.document(
        "https://pcae.local/schemas/cltr_cutover/shared/enums.schema.json"
    )
    schema_enum = set(shared["$defs"]["compatibility_mode"]["enum"])
    assert schema_enum == set(COMPATIBILITY_MODE_MEMBERS)
    assert {m.value for m in auth.CompatibilityMode} == set(COMPATIBILITY_MODE_MEMBERS)


@pytest.mark.parametrize("member", COMPATIBILITY_MODE_MEMBERS)
def test_136as_mode_every_valid_member_accepted_with_conditionals_satisfied(member, schema_registry):
    kwargs = {"mode": member}
    if member == "legacy_retired":
        kwargs["retirement_state"] = {}
    if member in MODES_RESTRICTING_AUTHORITY_ROLE:
        kwargs["authority_disclosure"] = _disclosure("historical")
    wire = _wire(**kwargs)
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.mode.value == member


@pytest.mark.parametrize("bad_value", ["Legacy_Adapter", "legacy_bogus", "adapter", "", None, 1])
def test_136as_mode_invalid_values_rejected(bad_value, schema_registry):
    wire = _wire(mode=bad_value)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises((TypedModelConstructionError, ValueError)):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_authority_role_authoritative_locally_forbidden(schema_registry):
    wire = _wire(authority_disclosure=_disclosure("authoritative"))
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "role", ["derivative", "operational", "evidence", "compatibility", "historical", "quarantined"]
)
def test_136as_authority_role_non_authoritative_accepted_under_unrestricted_mode(role, schema_registry):
    # legacy_adapter is unrestricted, so every non-authoritative role is valid.
    wire = _wire(authority_disclosure=_disclosure(role))
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.authority_role.value == role


def test_136as_is_authoritative_true_rejected():
    disclosure = _disclosure()
    disclosure["is_authoritative"] = True
    wire = _wire(authority_disclosure=disclosure)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_role_is_independent_of_authority_role(schema_registry):
    # The local 'role' field and authority_disclosure.authority_role are
    # distinct: role='historical' with authority_role='operational' is valid
    # under an unrestricted mode. No cross-field coupling is invented.
    wire = _wire(role="historical", authority_disclosure=_disclosure("operational"))
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.role.value == "historical"
    assert model.authority_disclosure.authority_role.value == "operational"


# ---------------------------------------------------------------------------
# 6. Conditional verification -- BOTH conditionals, BOTH directions, plus an
#    exhaustive schema-vs-model parity sweep over mode x authority_role x
#    retirement_state so no divergence (weakening OR strengthening) can hide.
# ---------------------------------------------------------------------------


def test_136as_conditional_definitions_present_in_live_schema(live_schema):
    all_of = live_schema["allOf"]
    assert len(all_of) == 2
    cond1, cond2 = all_of
    assert cond1["if"]["properties"]["mode"]["const"] == "legacy_retired"
    assert cond1["then"] == {"required": ["retirement_state"]}
    assert cond1["else"] == {"not": {"required": ["retirement_state"]}}
    assert set(cond2["if"]["properties"]["mode"]["enum"]) == set(MODES_RESTRICTING_AUTHORITY_ROLE)
    then_roles = cond2["then"]["properties"]["authority_disclosure"]["properties"]["authority_role"]["enum"]
    assert set(then_roles) == {"historical", "compatibility"}


def test_136as_retired_without_retirement_state_rejected(schema_registry):
    wire = _wire(mode="legacy_retired", role="historical", authority_disclosure=_disclosure("historical"))
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("non_retired", MODES_UNRESTRICTED + ("legacy_historical", "legacy_disabled"))
def test_136as_non_retired_forbids_retirement_state(non_retired, schema_registry):
    kwargs = {"mode": non_retired, "retirement_state": {}}
    if non_retired in MODES_RESTRICTING_AUTHORITY_ROLE:
        kwargs["authority_disclosure"] = _disclosure("historical")
    wire = _wire(**kwargs)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("restricted_mode", MODES_RESTRICTING_AUTHORITY_ROLE)
@pytest.mark.parametrize("forbidden_role", ["derivative", "operational", "evidence", "quarantined"])
def test_136as_restricted_mode_forbids_non_historical_compatibility_role(
    restricted_mode, forbidden_role, schema_registry
):
    kwargs = {"mode": restricted_mode, "authority_disclosure": _disclosure(forbidden_role)}
    if restricted_mode == "legacy_retired":
        kwargs["retirement_state"] = {}
    wire = _wire(**kwargs)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelInternalInvariantError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("restricted_mode", MODES_RESTRICTING_AUTHORITY_ROLE)
@pytest.mark.parametrize("permitted_role", ["historical", "compatibility"])
def test_136as_restricted_mode_permits_historical_compatibility_role(
    restricted_mode, permitted_role, schema_registry
):
    kwargs = {"mode": restricted_mode, "authority_disclosure": _disclosure(permitted_role)}
    if restricted_mode == "legacy_retired":
        kwargs["retirement_state"] = {}
    wire = _wire(**kwargs)
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.authority_role.value == permitted_role


@pytest.mark.parametrize("unrestricted_mode", MODES_UNRESTRICTED)
@pytest.mark.parametrize("role", ["derivative", "operational", "evidence", "quarantined"])
def test_136as_unrestricted_mode_permits_broader_authority_role(unrestricted_mode, role, schema_registry):
    # Guard against unauthorized *strengthening*: the mode-based restriction
    # applies ONLY to the three restricted modes; other modes accept any
    # non-authoritative role.
    wire = _wire(mode=unrestricted_mode, authority_disclosure=_disclosure(role))
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.authority_role.value == role


def test_136as_exhaustive_schema_vs_model_conditional_parity(schema_registry):
    """The decisive independence check: for every combination of mode,
    authority_role, and retirement_state presence/shape, the Python model's
    accept/reject decision must exactly equal the live executable schema's.
    Any mismatch is either an unauthorized weakening or strengthening."""

    mismatches = []
    checked = 0
    for mode in COMPATIBILITY_MODE_MEMBERS:
        for role in AUTHORITY_ROLE_MEMBERS:
            for retirement in (None, {}, {"unexpected_key": 1}):
                wire = _wire(mode=mode, authority_disclosure=_disclosure(role), role="historical")
                if retirement is not None:
                    wire["retirement_state"] = retirement
                s = _schema_valid(wire, schema_registry)
                m = _model_valid(wire)
                checked += 1
                if s != m:
                    mismatches.append((mode, role, retirement, s, m))
    assert not mismatches, mismatches
    assert checked == len(COMPATIBILITY_MODE_MEMBERS) * len(AUTHORITY_ROLE_MEMBERS) * 3


# ---------------------------------------------------------------------------
# 7. Field-specific shape verification -- retirement_state is wrapped in the
#    general-purpose OpaqueJsonValue type but the live schema pins it to an
#    empty-object-only placeholder (DEFERRED-136V-1). Wrapper validity alone
#    is not schema validity (precedent DEFERRED-136T-1). Verify at the field's
#    own construction boundary.
# ---------------------------------------------------------------------------


def test_136as_retirement_state_schema_pins_to_empty_object_only(live_schema):
    definition = live_schema["$defs"]["retirement_state"]
    assert definition["type"] == "object"
    assert definition["additionalProperties"] is False
    assert "properties" not in definition or definition["properties"] == {}


def test_136as_retirement_state_empty_object_valid_and_constructs(schema_registry):
    wire = _retired_wire(retirement_state={})
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.retirement_state.to_json() == {}
    assert model.to_dict()["retirement_state"] == {}


def test_136as_retirement_state_nonempty_object_schema_invalid(schema_registry):
    wire = _retired_wire(retirement_state={"retired_at": "2026-07-19T00:00:00Z"})
    _assert_schema_invalid(wire, schema_registry)


def test_136as_retirement_state_nonempty_object_rejected_by_model():
    """The model wraps retirement_state in general-purpose OpaqueJsonValue
    (opaque.py), which by design preserves any JSON value verbatim with no
    shape check. Independently confirmed schema-invalid above; a shape-only
    schema-backed model must reject at construction every payload the schema
    rejects. Accepting a populated retirement_state would be an unauthorized
    weakening of the field's contract-pinned empty-shape restriction
    (DEFERRED-136V-1)."""

    wire = _retired_wire(retirement_state={"retired_at": "2026-07-19T00:00:00Z"})
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("bad", ["not-an-object", 5, True, [], ["x"]])
def test_136as_retirement_state_non_object_rejected(bad, schema_registry):
    wire = _retired_wire(retirement_state=bad)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 8. component / allowed_reads field-shape verification.
# ---------------------------------------------------------------------------


def test_136as_component_bounds_confirmed_against_live_schema(live_schema):
    comp = live_schema["properties"]["component"]
    assert comp["type"] == "string"
    assert comp["minLength"] == 1
    assert comp["maxLength"] == 256
    assert comp["pattern"] == "^[\\x20-\\x7E]*$"


@pytest.mark.parametrize(
    "component,expected_valid",
    [
        ("a", True),
        ("a" * 256, True),
        ("legacy component with spaces and ~symbols!", True),
        ("", False),
        ("a" * 257, False),
        ("café", False),          # non-ASCII
        ("tab\there", False),          # control char
        ("newline\nhere", False),
    ],
)
def test_136as_component_boundaries(component, expected_valid, schema_registry):
    wire = _wire(component=component)
    assert _schema_valid(wire, schema_registry) is expected_valid
    assert _model_valid(wire) is expected_valid


def test_136as_component_non_string_rejected(schema_registry):
    wire = _wire(component=123)
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_allowed_reads_bounds_confirmed_against_live_schema(live_schema):
    ar = live_schema["properties"]["allowed_reads"]
    assert ar["type"] == "array"
    assert ar["maxItems"] == 64
    item = live_schema["$defs"]["allowed_read_path"]
    assert item["minLength"] == 1
    assert item["maxLength"] == 512
    assert ".." in item["pattern"] or "\\.\\." in item["pattern"]


def test_136as_allowed_reads_empty_is_valid(schema_registry):
    wire = _wire(allowed_reads=[])
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.allowed_reads == ()


@pytest.mark.parametrize(
    "reads,expected_valid",
    [
        (["a"], True),
        (["a" * 512], True),
        (["config/thing.json", "state/other"], True),
        (["p%d" % i for i in range(64)], True),
        (["p%d" % i for i in range(65)], False),   # maxItems
        (["a" * 513], False),                        # entry too long
        ([""], False),                               # empty entry
        (["../escape"], False),                      # traversal token
        (["path/../x"], False),                      # traversal mid-string
        (["ctrl\x00char"], False),                   # C0 control char
        (["del\x7fchar"], False),                    # DEL / C1 boundary
    ],
)
def test_136as_allowed_reads_boundaries(reads, expected_valid, schema_registry):
    wire = _wire(allowed_reads=reads)
    assert _schema_valid(wire, schema_registry) is expected_valid
    assert _model_valid(wire) is expected_valid


def test_136as_allowed_reads_non_list_rejected(schema_registry):
    wire = _wire(allowed_reads="not-a-list")
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_allowed_reads_non_string_entry_rejected(schema_registry):
    wire = _wire(allowed_reads=[123])
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_forbidden_authority_use_must_be_true(live_schema, schema_registry):
    assert live_schema["properties"]["forbidden_authority_use"]["const"] is True
    for bad in (False, "true", 1, None):
        wire = _wire(forbidden_authority_use=bad)
        _assert_schema_invalid(wire, schema_registry)
        with pytest.raises(TypedModelConstructionError):
            auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_fallback_disabled_must_be_boolean(schema_registry):
    for bad in ("yes", 1, None, {}):
        wire = _wire(fallback_disabled=bad)
        _assert_schema_invalid(wire, schema_registry)
        with pytest.raises(TypedModelConstructionError):
            auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    for good in (True, False):
        wire = _wire(fallback_disabled=good)
        _assert_schema_valid(wire, schema_registry)


# ---------------------------------------------------------------------------
# 9. Absent vs null verification; _extensions.
# ---------------------------------------------------------------------------


def test_136as_retirement_state_absent_by_default_under_non_retired():
    model = auth.CompatibilityState.from_dict(_wire(), schema_version="1.0")
    assert model.retirement_state is ABSENT
    assert "retirement_state" not in model.to_dict()


def test_136as_extensions_absent_by_default_and_explicit_null_rejected():
    model = auth.CompatibilityState.from_dict(_wire(), schema_version="1.0")
    assert model._extensions is ABSENT
    assert "_extensions" not in model.to_dict()
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(_wire(_extensions=None), schema_version="1.0")


def test_136as_extensions_populated_string_valued_map_round_trips(schema_registry):
    wire = _wire(_extensions={"note": "independent-verification-tag"})
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.to_dict()["_extensions"] == {"note": "independent-verification-tag"}


def test_136as_extensions_non_string_value_rejected(schema_registry):
    wire = _wire(_extensions={"note": 123})
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_extensions_reserved_key_collision_rejected():
    wire = _wire(_extensions={"migration_epoch": "shadowing-attempt"})
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_extensions_max_properties_bound(live_schema, schema_registry):
    assert live_schema["properties"]["_extensions"]["maxProperties"] == 32
    wire = _wire(_extensions={f"k{i}": "v" for i in range(33)})
    _assert_schema_invalid(wire, schema_registry)
    with pytest.raises(TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 10. Reference-family absence verification (Sec.34 / Sec.12).
# ---------------------------------------------------------------------------


def test_136as_no_reference_family_fields_present(live_schema):
    """CompatibilityState has no record_reference / generation_reference /
    epoch_reference field of its own -- confirm none was silently added."""

    props = live_schema["properties"]
    for suspect in (
        "record_reference",
        "generation_reference",
        "epoch_reference",
        "publication_evidence_reference",
        "marker_reference",
        "reference",
    ):
        assert suspect not in props
    # No nested schema_id/schema_version-pinned reference object anywhere.
    assert "record_family" not in props
    dumped = json.dumps(live_schema)
    assert "references.schema.json" not in dumped


def test_136as_model_defines_no_reference_wrapper_fields():
    field_names = {f.name for f in dataclasses.fields(auth.CompatibilityState)}
    assert not any("reference" in name for name in field_names)


# ---------------------------------------------------------------------------
# 11. Immutability verification (frozen, recursive, source-mutation isolation,
#     output-mutation isolation).
# ---------------------------------------------------------------------------


def test_136as_is_frozen_dataclass():
    model = auth.CompatibilityState.from_dict(_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.mode = auth.CompatibilityMode.LEGACY_DISABLED


def test_136as_mutating_source_allowed_reads_after_construction_does_not_affect_model():
    source = ["config/a.json"]
    wire = _wire(allowed_reads=source)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    source.append("state/b.txt")
    assert model.allowed_reads == ("config/a.json",)


def test_136as_mutating_source_limitations_after_construction_does_not_affect_model():
    source = ["limitation one"]
    wire = _wire(limitations=source)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    source.append("limitation two")
    assert len(model.limitations.entries) == 1


def test_136as_mutating_source_extensions_after_construction_does_not_affect_model():
    source = {"note": "original"}
    wire = _wire(_extensions=source)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    source["note"] = "tampered"
    source["new"] = "also"
    assert model.to_dict()["_extensions"] == {"note": "original"}


def test_136as_mutating_source_disclosure_after_construction_does_not_affect_model():
    source = _disclosure("compatibility")
    wire = _wire(authority_disclosure=source)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    source["disclosure_text"] = "tampered"
    assert model.authority_disclosure.disclosure_text != "tampered"


def test_136as_mutating_to_dict_output_does_not_affect_model():
    model = auth.CompatibilityState.from_dict(
        _wire(allowed_reads=["a/b"], _extensions={"k": "v"}), schema_version="1.0"
    )
    out = model.to_dict()
    out["allowed_reads"].append("tampered")
    out["_extensions"]["k"] = "tampered"
    out["component"] = "tampered"
    fresh = model.to_dict()
    assert fresh["allowed_reads"] == ["a/b"]
    assert fresh["_extensions"] == {"k": "v"}
    assert fresh["component"] == "legacy.component.name"


def test_136as_deep_copy_produces_structurally_equal_but_independent_object():
    model = auth.CompatibilityState.from_dict(_wire(), schema_version="1.0")
    duplicate = copy.deepcopy(model)
    assert duplicate == model
    assert duplicate is not model


# ---------------------------------------------------------------------------
# 12. Structural equality verification (not identifier-only / digest-only).
# ---------------------------------------------------------------------------


def test_136as_equality_is_structural_and_changes_when_any_field_changes():
    base = auth.CompatibilityState.from_dict(_wire(), schema_version="1.0")
    same = auth.CompatibilityState.from_dict(_wire(), schema_version="1.0")
    assert base == same

    for override in (
        {"role": "historical"},
        {"mode": "legacy_read_only"},
        {"component": "other.component"},
        {"fallback_disabled": True},
        {"allowed_reads": ["x/y"]},
        {"migration_epoch": "epoch-002"},
        {"limitations": ["disclosure"]},
        {"authority_disclosure": _disclosure("operational")},
        {"_extensions": {"k": "v"}},
    ):
        variant = auth.CompatibilityState.from_dict(_wire(**override), schema_version="1.0")
        assert base != variant, override


def test_136as_equality_rejects_identifier_only_and_digest_only_comparison():
    base = auth.CompatibilityState.from_dict(_wire(), schema_version="1.0")
    same_identity_diff_mode = auth.CompatibilityState.from_dict(
        _wire(mode="legacy_read_only"), schema_version="1.0"
    )
    assert base.envelope.record_id == same_identity_diff_mode.envelope.record_id
    assert base.envelope.record_digest == same_identity_diff_mode.envelope.record_digest
    assert base != same_identity_diff_mode


# ---------------------------------------------------------------------------
# 13. Deterministic serialization / round-trip / error determinism.
# ---------------------------------------------------------------------------


def test_136as_round_trip_is_deterministic_and_lossless():
    wire = _retired_wire(allowed_reads=["a", "b"], _extensions={"k": "v"})
    m1 = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    d1 = m1.to_dict()
    m2 = auth.CompatibilityState.from_dict(d1, schema_version="1.0")
    d2 = m2.to_dict()
    assert d1 == d2 == wire
    assert m1 == m2


def test_136as_construction_errors_deterministic_across_repeated_attempts():
    bad_wire = _wire(mode="not-a-real-mode")
    errors = []
    for _ in range(3):
        try:
            auth.CompatibilityState.from_dict(bad_wire, schema_version="1.0")
        except Exception as exc:  # noqa: BLE001
            errors.append(type(exc))
    assert len(errors) == 3
    assert len(set(errors)) == 1


def test_136as_invalid_digest_wrapper_rejected():
    with pytest.raises(Exception):
        auth.CompatibilityState.from_dict(_wire(record_digest="not-a-sha256"), schema_version="1.0")


def test_136as_invalid_identifier_wrapper_rejected():
    with pytest.raises(Exception):
        auth.CompatibilityState.from_dict(_wire(migration_epoch="a..b"), schema_version="1.0")


# ---------------------------------------------------------------------------
# 14. Anti-strengthening verification -- reasonable-sounding compatibility
#     assumptions the schema does NOT encode must NOT be enforced.
# ---------------------------------------------------------------------------


def test_136as_component_need_not_exist_or_be_installed(schema_registry):
    wire = _wire(component="a.component.that.does.not.exist.anywhere")
    _assert_schema_valid(wire, schema_registry)
    auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_allowed_reads_need_not_actually_be_readable(schema_registry):
    wire = _wire(allowed_reads=["/nonexistent/never/created/path"])
    _assert_schema_valid(wire, schema_registry)
    auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_fallback_disabled_true_does_not_require_any_other_field(schema_registry):
    # fallback_disabled is a free boolean; setting it true imposes no other
    # requirement (no coupling to mode/role invented).
    wire = _wire(fallback_disabled=True, mode="legacy_authoritative")
    _assert_schema_valid(wire, schema_registry)
    auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_legacy_does_not_imply_retired_or_disabled(schema_registry):
    # A legacy_authoritative document with role compatibility and an
    # operational disclosure is perfectly valid -- "legacy" carries no
    # deprecation/retirement obligation.
    wire = _wire(mode="legacy_authoritative", role="compatibility",
                 authority_disclosure=_disclosure("operational"))
    _assert_schema_valid(wire, schema_registry)
    auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136as_calendar_invalid_but_shape_valid_timestamp_accepted(schema_registry):
    # The timestamp definition validates SHAPE only, never calendar
    # semantics; month 13 is shape-valid and must be accepted (no invented
    # calendar strengthening).
    wire = _wire(created_at="2026-13-45T99:99:99Z")
    assert _schema_valid(wire, schema_registry) is True
    assert _model_valid(wire) is True


def test_136as_duplicate_allowed_reads_entries_accepted(schema_registry):
    # No uniqueItems constraint on allowed_reads; duplicates are valid.
    wire = _wire(allowed_reads=["same/path", "same/path"])
    _assert_schema_valid(wire, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.allowed_reads == ("same/path", "same/path")


def test_136as_duplicate_limitations_entries_accepted(schema_registry):
    wire = _wire(limitations=["dup", "dup"])
    _assert_schema_valid(wire, schema_registry)
    auth.CompatibilityState.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 15. Boundary verification -- no compatibility engine / quarantine /
#     authority activation / runtime behaviour anywhere in the module.
# ---------------------------------------------------------------------------


FORBIDDEN_COMPATIBILITY_ENGINE_SYMBOLS = (
    "determine_compatibility", "calculate_compatibility", "infer_compatibility",
    "compare_versions", "negotiate_version", "select_version", "is_compatible",
    "resolve_compatibility", "reconcile", "resolve_conflict", "select_fallback",
    "plan_migration", "execute_migration", "convert_schema", "convert_record",
    "transform_record", "activate_mode", "disable_mode", "determine_upgrade_readiness",
    "determine_downgrade_readiness", "authorize_cutover", "block_cutover",
    "inspect_installed_packages", "inspect_dependencies", "inspect_repository",
    "inspect_git", "discover_schemas",
)
FORBIDDEN_QUARANTINE_SYMBOLS = (
    "quarantine", "isolate_record", "classify_record", "release_record",
    "delete_record", "move_record", "evaluate_eligibility", "write_marker",
    "reconcile_quarantine",
)
FORBIDDEN_AUTHORITY_EXERCISE_SYMBOLS = (
    "activate_authority", "resolve_authority", "determine_current_authority",
    "compare_authorities", "transfer_authority", "mutate_authority_pointer",
    "demote_authority", "finalize_lifecycle", "advance_lifecycle_state",
    "authorize_publication",
)


def test_136as_module_defines_no_engine_quarantine_or_authority_exercise_symbols():
    tree = ast.parse(COMPAT_MODULE.read_text())
    defined = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(node.name)
    forbidden = (
        FORBIDDEN_COMPATIBILITY_ENGINE_SYMBOLS
        + FORBIDDEN_QUARANTINE_SYMBOLS
        + FORBIDDEN_AUTHORITY_EXERCISE_SYMBOLS
    )
    for name in forbidden:
        assert name not in defined, f"forbidden symbol {name!r} defined in module"


def test_136as_module_public_api_is_representation_only():
    # The only public methods on the model are from_dict / to_dict; no
    # engine/decision/activation method exists.
    public = {n for n in dir(auth.CompatibilityState) if not n.startswith("_")}
    # allow dataclass field names + from_dict/to_dict
    field_names = {f.name for f in dataclasses.fields(auth.CompatibilityState)}
    method_like = public - field_names
    assert method_like == {"from_dict", "to_dict"}


# ---------------------------------------------------------------------------
# 16. Scope-guard integrity -- the 136AQ sibling verification suite's own
#     scope guards must still forbid QuarantineRecord and must not have been
#     over-broadened to permit arbitrary later-group records.
# ---------------------------------------------------------------------------


def test_136as_sibling_136aq_scope_guard_no_longer_forbids_quarantine_record():
    """Narrowed by Phase 136AT (Group 11, scope-guard evolution): the
    136AQ sibling verification suite's own forbidden-family tuple has now
    been narrowed (in that file, by this same phase) to drop
    QuarantineRecord, since it is the sixteenth and final legitimately-
    implemented record-family model. Confirm that narrowing landed and
    that the tuple was not instead left stale or broadened to forbid an
    already-implemented family."""

    guard_file = REPO_ROOT / "tests" / (
        "test_cltr_authority_136aq_finalization_receipt_authority_binding_independent.py"
    )
    if not guard_file.exists():
        pytest.skip("136AQ sibling suite not present")
    tree = ast.parse(guard_file.read_text())
    forbidden_tuples: list[tuple[str, ...]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and "MUST_NOT_EXIST" in target.id:
                    values = tuple(
                        e.value for e in node.value.elts if isinstance(e, ast.Constant)
                    )
                    forbidden_tuples.append(values)
    assert forbidden_tuples, "136AQ forbidden-family tuple not found"
    for tup in forbidden_tuples:
        assert "QuarantineRecord" not in tup
        # The forbidden list must not forbid any currently-implemented family.
        assert not (set(tup) & set(FIFTEEN_IMPLEMENTED_RECORD_FAMILIES))


def test_136as_quarantine_record_family_slug_matches_implemented_class():
    # Narrowed by Phase 136AT (Group 11): the shared record_family enum's
    # quarantine_record slug now names an actually-implemented class too.
    assert hasattr(auth, "QuarantineRecord")
    from pcae.cltr.authority.enums import RecordFamily
    assert RecordFamily.QUARANTINE_RECORD.value == "quarantine_record"


# ---------------------------------------------------------------------------
# 17. Runtime isolation -- no production module imports the authority package;
#     the module imports no transport/filesystem/runtime code (transitive).
# ---------------------------------------------------------------------------


def test_136as_no_production_module_imports_authority_package():
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
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith(forbidden_prefix), (path, alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    assert not node.module.startswith(forbidden_prefix), (path, node.module)


def test_136as_module_source_imports_no_transport_or_filesystem_code():
    forbidden = (
        "socket", "subprocess", "shutil", "requests", "urllib", "smtplib",
        "telegram", "slack_sdk", "os", "pathlib", "pcae.commands", "pcae.core",
        "pcae.runtime", "pcae.cltr.notification", "pcae.cltr.marker",
    )
    tree = ast.parse(COMPAT_MODULE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(f) for f in forbidden), alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(f) for f in forbidden), node.module


def test_136as_module_source_never_references_environment_or_git():
    source = COMPAT_MODULE.read_text()
    for token in ("os.environ", "getenv", "os.getenv", "subprocess", "socket", "git "):
        assert token not in source


def test_136as_transitive_import_walk_finds_no_transport_or_filesystem_dependency():
    """Fresh, independent construction of the import graph from
    compatibility_quarantine.py through its authority-package siblings."""

    visited: set[Path] = set()
    to_visit = [COMPAT_MODULE]
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
    assert COMPAT_MODULE in visited


# ---------------------------------------------------------------------------
# 18. Side-effect verification -- construction/serialization/equality/repr
#     touch no filesystem, network, subprocess, or environment.
# ---------------------------------------------------------------------------


def test_136as_no_network_during_construction_serialization_equality_repr(monkeypatch):
    def _raise(*a, **k):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    model = auth.CompatibilityState.from_dict(_retired_wire(), schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136as_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*a, **k):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    model = auth.CompatibilityState.from_dict(_wire(), schema_version="1.0")
    model.to_dict()


def test_136as_no_filesystem_access_during_lifecycle(monkeypatch):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        raise AssertionError(f"unexpected filesystem access: {file!r} mode={mode!r}")

    monkeypatch.setattr("builtins.open", _guarded_open)
    model = auth.CompatibilityState.from_dict(_wire(_extensions={"k": "v"}), schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model
    # restore not strictly needed; monkeypatch auto-reverts
    assert real_open is not None


def test_136as_module_reimport_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    importlib.reload(cs_module)


# ---------------------------------------------------------------------------
# 19. Packaging verification (fresh wheel build, isolated install, exact
#     export inventory, QuarantineRecord absence).
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136as_wheel_build_contains_group_10_module_and_no_quarantine(tmp_path: Path):
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
    for forbidden in ("quarantine_record", "quarantine"):
        assert f"pcae/cltr/authority/{forbidden}.py" not in names


@pytest.mark.slow
def test_136as_isolated_install_all_fifteen_families_import_and_round_trip(tmp_path: Path):
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
        "for name in " + repr(FIFTEEN_IMPLEMENTED_RECORD_FAMILIES) + ":\n"
        "    assert hasattr(auth, name), name\n"
        "for name in " + repr(MUST_NOT_EXIST_RECORD_FAMILIES) + ":\n"
        "    assert not hasattr(auth, name), name\n"
        "wire = {\n"
        "    'schema_id': " + repr(COMPATIBILITY_STATE_SCHEMA_ID) + ",\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'compatibility_state', 'record_id': 'compstat-0000099',\n"
        "    'record_digest': '0'*64, 'created_at': '2026-07-19T00:00:00Z',\n"
        "    'migration_epoch': 'epoch-001', 'component': 'c', 'role': 'compatibility',\n"
        "    'allowed_reads': [], 'forbidden_authority_use': True, 'fallback_disabled': False,\n"
        "    'mode': 'legacy_adapter', 'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'compatibility',\n"
        "        'is_authoritative': False, 'disclosure_text': 'ok'},\n"
        "}\n"
        "model = auth.CompatibilityState.from_dict(wire, schema_version='1.0')\n"
        "assert model.to_dict() == wire\n"
        "print('ISOLATED_INSTALL_OK')\n"
    )
    result = subprocess.run(
        [str(venv_python), "-c", probe], check=True, capture_output=True, text=True,
    )
    assert "ISOLATED_INSTALL_OK" in result.stdout
