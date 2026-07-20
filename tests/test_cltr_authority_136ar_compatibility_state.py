"""Phase 136AR: Stage 3 Typed Authority Model CompatibilityState
Implementation (Typed Model Implementation Group 10).

Focused tests for ``src/pcae/cltr/authority/compatibility_quarantine.py``:
the ``CompatibilityState`` typed record model. Covers exact field mapping,
strict constructor behavior, the ``mode``/``retirement_state`` conditional,
the ``mode``/``authority_disclosure.authority_role`` conditional (both
directions, anti-strengthening), enum fidelity, schema conformance,
no-later-group-model inventory, no-compatibility-engine / no-quarantine /
no-authority-activation semantics, no-side-effect, and runtime-isolation.

This module implements only Typed Model Implementation Group 10
(``CompatibilityState``). No other record-family model
(``QuarantineRecord``) is implemented or exercised here.

Independently fixtured: wire fixtures below are re-derived from the
authoritative schema (``records/compatibility_state.schema.json``), not
copied from any earlier record-family test module's own fixture helpers.
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
    "calculate_compatibility",
    "evaluate_compatibility",
    "determine_compatibility",
    "resolve_compatibility",
    "negotiate_version",
    "select_version",
    "migrate",
    "transform",
    "convert",
    "reconcile",
    "activate_compatibility",
    "enable_legacy",
    "disable_legacy",
    "inspect_runtime_version",
    "inspect_dependency_version",
    "lookup_schema",
    "load_reference",
    "quarantine",
    "release_quarantine",
    "mutate_lifecycle_state",
    "activate_authority",
    "transfer_authority",
)

# Phase 136AT (Group 11) implemented QuarantineRecord, the sixteenth and
# final Stage 3 record-family model; no later group remains to guard
# against, so this tuple is now empty (narrowed by 136AT, scope-guard
# evolution note: 1 of 1 name removed, no other family named here).
LATER_GROUP_MODEL_NAMES = ()

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


def _valid_compatibility_state_wire(**overrides) -> dict:
    record = {
        "schema_id": COMPATIBILITY_STATE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "compatibility_state",
        "record_id": "compatst-0000001",
        "record_digest": _sha256_hex("0"),
        "created_at": "2026-07-18T12:00:00Z",
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


def _retired_wire(**overrides) -> dict:
    base = _valid_compatibility_state_wire(
        mode="legacy_retired",
        retirement_state={},
        authority_disclosure=_disclosure("historical"),
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Inventory
# ---------------------------------------------------------------------------


def test_136ar_exactly_fifteen_record_family_models_exist_in_package():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for expected in (
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
    ):
        assert expected in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136ar_no_later_group_model_class_exists_in_compatibility_module():
    tree = ast.parse(COMPATIBILITY_MODULE.read_text())
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "CompatibilityState" in class_names
    # Phase 136AT (Group 11) added QuarantineRecord to this same module;
    # it is no longer a "later group" absence to guard against.
    assert "QuarantineRecord" in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136ar_expected_public_exports_present():
    for name in ("CompatibilityState", "CompatibilityRole"):
        assert hasattr(auth, name)
        assert name in auth.__all__


def test_136ar_public_exports_exact():
    # Narrowed by Phase 136AT (Group 11): compatibility_quarantine.py now
    # also exports QuarantineRecord/ObjectType/QuarantineState alongside
    # this phase's own CompatibilityRole/CompatibilityState.
    assert set(compatibility_quarantine.__all__) == {
        "CompatibilityRole",
        "CompatibilityState",
        "ObjectType",
        "QuarantineState",
        "QuarantineRecord",
    }


def test_136ar_wildcard_import_matches_all():
    namespace: dict = {}
    exec("from pcae.cltr.authority.compatibility_quarantine import *", namespace)
    exported = {k for k in namespace if not k.startswith("_")}
    assert exported == set(compatibility_quarantine.__all__)


def test_136ar_model_is_frozen_dataclass():
    assert dataclasses.is_dataclass(auth.CompatibilityState)
    assert auth.CompatibilityState.__dataclass_params__.frozen


# ---------------------------------------------------------------------------
# 2. CompatibilityState: construction / round trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mode",
    ["legacy_authoritative", "legacy_adapter", "legacy_read_only"],
)
def test_136ar_minimal_valid_construction_unrestricted_modes(schema_registry, mode):
    wire = _valid_compatibility_state_wire(mode=mode)
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.retirement_state is auth.ABSENT
    assert model.to_dict() == wire


@pytest.mark.parametrize("mode", ["legacy_historical", "legacy_disabled"])
def test_136ar_restricted_modes_require_restricted_role(schema_registry, mode):
    wire = _valid_compatibility_state_wire(mode=mode, authority_disclosure=_disclosure("compatibility"))
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136ar_legacy_retired_with_retirement_state(schema_registry):
    wire = _retired_wire()
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.retirement_state.to_json() == {}
    assert model.to_dict() == wire


def test_136ar_maximal_valid_construction_with_extensions(schema_registry):
    wire = _retired_wire(_extensions={"note": "annotation"}, allowed_reads=["/status/health"])
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model._extensions["note"] == "annotation"
    assert model.allowed_reads == ("/status/health",)
    assert model.to_dict() == wire


def test_136ar_legacy_retired_without_retirement_state_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(
        mode="legacy_retired", authority_disclosure=_disclosure("historical")
    )
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(Exception):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "mode",
    ["legacy_authoritative", "legacy_adapter", "legacy_read_only", "legacy_historical", "legacy_disabled"],
)
def test_136ar_non_retired_with_retirement_state_rejected(schema_registry, mode):
    disclosure = _disclosure("compatibility") if mode in ("legacy_historical", "legacy_disabled") else _disclosure()
    wire = _valid_compatibility_state_wire(mode=mode, retirement_state={}, authority_disclosure=disclosure)
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(Exception):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("mode", ["legacy_historical", "legacy_disabled", "legacy_retired"])
@pytest.mark.parametrize("bad_role", ["derivative", "operational", "evidence", "quarantined"])
def test_136ar_restricted_modes_reject_disallowed_roles(schema_registry, mode, bad_role):
    overrides = {"authority_disclosure": _disclosure(bad_role)}
    if mode == "legacy_retired":
        overrides["retirement_state"] = {}
    wire = _valid_compatibility_state_wire(mode=mode, **overrides)
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(Exception):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("mode", ["legacy_authoritative", "legacy_adapter", "legacy_read_only"])
@pytest.mark.parametrize("permitted_role", ["derivative", "operational", "evidence", "compatibility", "historical", "quarantined"])
def test_136ar_unrestricted_modes_permit_any_non_authoritative_role_anti_strengthening(
    schema_registry, mode, permitted_role
):
    wire = _valid_compatibility_state_wire(mode=mode, authority_disclosure=_disclosure(permitted_role))
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


def test_136ar_forbids_authoritative_role(schema_registry):
    wire = _valid_compatibility_state_wire(authority_disclosure=_disclosure("authoritative"))
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(Exception):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_forbidden_authority_use_false_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(forbidden_authority_use=False)
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_forbidden_authority_use_missing_rejected():
    wire = _valid_compatibility_state_wire()
    del wire["forbidden_authority_use"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_unknown_field_rejected():
    wire = _valid_compatibility_state_wire(scope="global")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_unsupported_schema_version_rejected():
    wire = _valid_compatibility_state_wire()
    with pytest.raises(auth.UnsupportedSchemaVersionError):
        auth.CompatibilityState.from_dict(wire, schema_version="2.0")


def test_136ar_missing_schema_id_rejected():
    wire = _valid_compatibility_state_wire()
    del wire["schema_id"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_wrong_schema_id_rejected():
    wire = _valid_compatibility_state_wire(schema_id="https://pcae.local/wrong.json")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_missing_schema_version_rejected():
    wire = _valid_compatibility_state_wire()
    del wire["schema_version"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_wrong_record_type_rejected():
    wire = _valid_compatibility_state_wire(record_type="authority_state")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "required_key",
    [
        "migration_epoch",
        "component",
        "role",
        "allowed_reads",
        "forbidden_authority_use",
        "fallback_disabled",
        "mode",
        "limitations",
        "authority_disclosure",
    ],
)
def test_136ar_missing_required_field_rejected(required_key):
    wire = _valid_compatibility_state_wire()
    del wire[required_key]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_malformed_migration_epoch_rejected():
    wire = _valid_compatibility_state_wire(migration_epoch="Invalid Epoch!")
    with pytest.raises(auth.InvalidIdentifierError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_malformed_record_digest_rejected():
    wire = _valid_compatibility_state_wire(record_digest="not-a-digest")
    with pytest.raises(auth.InvalidDigestError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_component_empty_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(component="")
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_component_too_long_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(component="x" * 257)
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_component_non_ascii_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(component="légacy")
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_allowed_reads_dotdot_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(allowed_reads=["a/../b"])
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_allowed_reads_control_char_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(allowed_reads=["a\x00b"])
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_allowed_reads_empty_string_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(allowed_reads=[""])
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_allowed_reads_too_many_items_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(allowed_reads=[f"/p{i}" for i in range(65)])
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_allowed_reads_may_be_empty(schema_registry):
    wire = _valid_compatibility_state_wire(allowed_reads=[])
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.allowed_reads == ()


def test_136ar_fallback_disabled_non_boolean_rejected(schema_registry):
    wire = _valid_compatibility_state_wire(fallback_disabled="yes")
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_retirement_state_non_empty_rejected(schema_registry):
    wire = _retired_wire(retirement_state={"note": "x"})
    _assert_schema_invalid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_role_enum_members_match_schema():
    assert {m.value for m in compatibility_quarantine.CompatibilityRole} == {"compatibility", "historical"}


def test_136ar_role_enum_strictness():
    wire = _valid_compatibility_state_wire(role="COMPATIBILITY")
    with pytest.raises(ValueError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_role_rejects_authoritative_value():
    wire = _valid_compatibility_state_wire(role="authoritative")
    with pytest.raises(ValueError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_mode_enum_members_match_schema():
    assert {m.value for m in auth.CompatibilityMode} == {
        "legacy_authoritative",
        "legacy_adapter",
        "legacy_read_only",
        "legacy_historical",
        "legacy_disabled",
        "legacy_retired",
    }


def test_136ar_mode_enum_strictness():
    wire = _valid_compatibility_state_wire(mode="LEGACY_ADAPTER")
    with pytest.raises(ValueError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_top_level_assignment_raises():
    wire = _valid_compatibility_state_wire()
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.mode = auth.CompatibilityMode.LEGACY_RETIRED


def test_136ar_extensions_permitted_empty(schema_registry):
    wire = _valid_compatibility_state_wire(_extensions={})
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model._extensions.to_dict() == {}


def test_136ar_extensions_reject_reserved_key_collision():
    wire = _valid_compatibility_state_wire(_extensions={"mode": "x"})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_extensions_reject_non_string_value():
    wire = _valid_compatibility_state_wire(_extensions={"note": 5})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_extensions_reject_explicit_null():
    wire = _valid_compatibility_state_wire(_extensions=None)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CompatibilityState.from_dict(wire, schema_version="1.0")


def test_136ar_extensions_absent_by_default():
    wire = _valid_compatibility_state_wire()
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model._extensions is auth.ABSENT
    assert "_extensions" not in model.to_dict()


def test_136ar_retirement_state_absent_by_default():
    wire = _valid_compatibility_state_wire()
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.retirement_state is auth.ABSENT
    assert "retirement_state" not in model.to_dict()


def test_136ar_retirement_state_round_trips_as_opaque_value(schema_registry):
    wire = _retired_wire()
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert isinstance(model.retirement_state, auth.OpaqueJsonValue)
    auth.verify_round_trip({}, model.retirement_state)
    assert model.to_dict() == wire


# ---------------------------------------------------------------------------
# 3. Schema field-set parity
# ---------------------------------------------------------------------------


def test_136ar_schema_field_set_matches_model_known_keys():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "compatibility_state.schema.json").read_text())
    assert set(schema["properties"].keys()) == compatibility_quarantine._COMPATIBILITY_STATE_KNOWN_KEYS


def test_136ar_required_set_matches_schema():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "compatibility_state.schema.json").read_text())
    wire = _valid_compatibility_state_wire()
    assert set(schema["required"]) <= set(wire.keys())
    assert set(schema["required"]) == {
        "schema_id", "schema_version", "contract_version", "record_type",
        "record_id", "record_digest", "created_at", "migration_epoch",
        "component", "role", "allowed_reads", "forbidden_authority_use",
        "fallback_disabled", "mode", "limitations", "authority_disclosure",
    }


def test_136ar_compatibility_role_enum_matches_schema_defs():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "compatibility_state.schema.json").read_text())
    assert set(schema["$defs"]["compatibility_role"]["enum"]) == {
        m.value for m in compatibility_quarantine.CompatibilityRole
    }


def test_136ar_schema_pins_forbidden_authority_use_const_true():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "compatibility_state.schema.json").read_text())
    assert schema["properties"]["forbidden_authority_use"]["const"] is True


def test_136ar_schema_pins_retirement_state_empty_shape():
    import json

    with cltr_cutover_root() as root:
        schema = json.loads((root / "records" / "compatibility_state.schema.json").read_text())
    retirement_def = schema["$defs"]["retirement_state"]
    assert retirement_def["additionalProperties"] is False
    assert "properties" not in retirement_def or retirement_def.get("properties") == {}


# ---------------------------------------------------------------------------
# 4. Equality / immutability
# ---------------------------------------------------------------------------


def test_136ar_structural_equality():
    wire = _valid_compatibility_state_wire()
    a = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    b = auth.CompatibilityState.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert a == b


def test_136ar_field_difference_breaks_equality():
    a = auth.CompatibilityState.from_dict(_valid_compatibility_state_wire(), schema_version="1.0")
    b = auth.CompatibilityState.from_dict(
        _valid_compatibility_state_wire(mode="legacy_read_only"), schema_version="1.0"
    )
    assert a != b


def test_136ar_no_identifier_only_equality():
    a = auth.CompatibilityState.from_dict(
        _valid_compatibility_state_wire(component="component-a"), schema_version="1.0"
    )
    b = auth.CompatibilityState.from_dict(
        _valid_compatibility_state_wire(component="component-b"), schema_version="1.0"
    )
    assert a != b


def test_136ar_construction_input_mutation_does_not_mutate_model():
    wire = _valid_compatibility_state_wire(limitations=["a limitation"], allowed_reads=["/a"])
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    wire["limitations"].append("mutated after construction")
    wire["allowed_reads"].append("/mutated")
    assert list(model.limitations) == ["a limitation"]
    assert model.allowed_reads == ("/a",)


def test_136ar_recursive_immutability_extensions():
    wire = _valid_compatibility_state_wire(_extensions={"note": "x"})
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    wire["_extensions"]["note"] = "mutated"
    assert model._extensions["note"] == "x"


# ---------------------------------------------------------------------------
# 5. No-compatibility-engine / no-quarantine / no-authority-activation /
#    no-later-model / no-reference-lookup
# ---------------------------------------------------------------------------


def test_136ar_no_forbidden_symbols_defined_in_source():
    tree = ast.parse(COMPATIBILITY_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_SYMBOLS:
        assert forbidden not in defined_names


def test_136ar_no_repository_or_persistence_symbols_in_source():
    source = COMPATIBILITY_MODULE.read_text()
    for forbidden in (
        "Repository", "save(", "persist(", "def load(", "requests.", "urllib",
        "socket.", "subprocess.", "shutil.", "os.remove", "os.rename",
        "pathlib.Path(", "open(",
    ):
        assert forbidden not in source


def test_136ar_quarantine_record_now_defined_in_module():
    # Narrowed by Phase 136AT (Group 11): QuarantineRecord is now the
    # authorized second class in this module (this phase's own
    # test_cltr_authority_136at_quarantine_record.py carries the full
    # QuarantineRecord-specific coverage). This guard's remaining purpose
    # -- confirming no *operational* quarantine symbol was introduced --
    # is preserved by test_136ar_no_forbidden_symbols_defined_in_source's
    # FORBIDDEN_SYMBOLS list (unchanged, still includes "quarantine",
    # "release_quarantine").
    tree = ast.parse(COMPATIBILITY_MODULE.read_text())
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "QuarantineRecord" in class_names


def test_136ar_no_production_module_imports_authority_package():
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


def test_136ar_compatibility_module_imports_no_production_lifecycle_module():
    source = COMPATIBILITY_MODULE.read_text()
    for forbidden_import in (
        "pcae.core.finalization",
        "pcae.core.notification",
        "pcae.commands",
        "pcae.runtime",
    ):
        assert forbidden_import not in source


def test_136ar_compatibility_module_does_not_import_production_lifecycle_modules_ast():
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


def test_136ar_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    wire = _valid_compatibility_state_wire()
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    model.to_dict()


def test_136ar_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    wire = _retired_wire()
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    model.to_dict()


def test_136ar_no_filesystem_write_during_construction_or_serialization(monkeypatch, tmp_path):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    wire = _valid_compatibility_state_wire()
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136ar_package_import_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(compatibility_quarantine)


def test_136ar_valid_nonexistent_reference_analog_no_lookup_component(schema_registry):
    # component is a bare shape-checked free-text field, not a reference;
    # a syntactically valid but nonexistent component name must construct
    # successfully (Sec.34: "does not verify the named component actually
    # exists").
    wire = _valid_compatibility_state_wire(component="nonexistent-component-xyz")
    _assert_schema_valid(wire, COMPATIBILITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.CompatibilityState.from_dict(wire, schema_version="1.0")
    assert model.component == "nonexistent-component-xyz"


# ---------------------------------------------------------------------------
# 6. Scope-guard verification (own module: exactly one new family; every
#    other later record family, i.e. QuarantineRecord, remains forbidden).
# ---------------------------------------------------------------------------


def test_136ar_own_module_scope_guard_matches_exactly_the_new_family():
    tree = ast.parse(COMPATIBILITY_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_models = class_names & {
        "CompatibilityState", "QuarantineRecord",
        "AuthorityEpoch", "AuthorityState", "CutoverRequest", "ReadinessPackage",
        "HumanAuthorization", "CutoverCandidate", "Certification",
        "PublicationAttempt", "PublicationEvidence",
        "ConcurrencyConflict", "RecoveryJournalEntry",
        "NotificationAuthorityBinding", "MarkerAuthorityBinding",
        "FinalizationReceiptAuthorityBinding",
    }
    # Narrowed by Phase 136AT (Group 11): QuarantineRecord is now the
    # authorized second family in this module; no other later-group
    # family has been added.
    assert record_family_models == {"CompatibilityState", "QuarantineRecord"}


def test_136ar_quarantine_record_now_present_in_package():
    # Narrowed by Phase 136AT (Group 11): superseded assertion (this test
    # previously proved QuarantineRecord absent). QuarantineRecord's own
    # dedicated coverage lives in test_cltr_authority_136at_quarantine_record.py.
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "QuarantineRecord" in class_names
    assert auth.QuarantineRecord is not None


# ---------------------------------------------------------------------------
# 7. Packaging verification
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136ar_wheel_contains_compatibility_module_with_quarantine_record(tmp_path: Path):
    # Narrowed by Phase 136AT (Group 11): the wheel now legitimately
    # contains QuarantineRecord in this module too.
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

    assert "pcae/cltr/authority/compatibility_quarantine.py" in names
    with zipfile.ZipFile(wheels[0]) as archive:
        source = archive.read("pcae/cltr/authority/compatibility_quarantine.py").decode()
    tree = ast.parse(source)
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "QuarantineRecord" in class_names
    assert "CompatibilityState" in class_names


@pytest.mark.slow
def test_136ar_sdist_includes_compatibility_module(tmp_path: Path):
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
def test_136ar_isolated_install_construct_and_round_trip(tmp_path: Path):
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
        "from pcae.cltr.authority import CompatibilityState\n"
        "wire = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/compatibility_state.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0',\n"
        "    'record_type': 'compatibility_state', 'record_id': 'compatst-0000001',\n"
        "    'record_digest': '0' * 64, 'created_at': '2026-07-18T12:00:00Z',\n"
        "    'migration_epoch': 'epoch-001', 'component': 'legacy-lifecycle',\n"
        "    'role': 'compatibility', 'allowed_reads': [], 'forbidden_authority_use': True,\n"
        "    'fallback_disabled': False, 'mode': 'legacy_adapter', 'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'derivative', 'is_authoritative': False, "
        "'disclosure_text': 'x'},\n"
        "}\n"
        "model = CompatibilityState.from_dict(wire, schema_version='1.0')\n"
        "assert model.to_dict() == wire\n"
        # Narrowed by Phase 136AT (Group 11): QuarantineRecord is now
        # legitimately importable; this phase's own
        # test_cltr_authority_136at_quarantine_record.py carries the
        # dedicated isolated-install construction/round-trip check for it.
        "from pcae.cltr.authority import QuarantineRecord\n"
        "assert QuarantineRecord is not None\n"
        "print('ISOLATED_OK')\n"
    )
    result = _subprocess.run(
        [str(env_python), str(script)],
        cwd=str(tmp_path), check=True, capture_output=True, text=True,
    )
    assert "ISOLATED_OK" in result.stdout
