"""Phase 136AA: Stage 3 Typed Authority Model Shared Core Independent
Verification.

Independently re-derives the expected shared-core inventory and behavior
from the frozen Stage 3 contracts and executable schemas -- NOT from
Phase 136Z's implementation prose, tests, fixtures, helpers, or claimed
counts. Every expected value below (enum members, identifier regexes,
digest shape, envelope fields, limitations bounds) is read directly from
``src/pcae/schema_resources/cltr_cutover/shared/*.schema.json`` or quoted
verbatim from
``docs/PHASE_135_STAGE_3_COMPANION_SCHEMAS_AND_TYPED_AUTHORITY_MODEL_CONTRACT_FREEZE.md``.

This module imports the implementation under test
(``pcae.cltr.authority``) -- that is expected, since the implementation is
the target under verification. It does not import
``tests/test_cltr_authority_136z_shared_core.py`` or reuse any fixture,
helper, or constant defined there.

Scope: Typed Model Implementation Group 1 (shared core) only. No
record-family model (``AuthorityEpoch``, ``AuthorityState``,
``CutoverRequest``, ``ReadinessPackage``, ``HumanAuthorization``,
``CutoverCandidate``, ``Certification``, ``PublicationAttempt``,
``PublicationEvidence``, ``ConcurrencyConflict``, ``RecoveryJournalEntry``,
``NotificationAuthorityBinding``, ``MarkerAuthorityBinding``,
``FinalizationReceiptAuthorityBinding``, ``CompatibilityState``,
``QuarantineRecord``) is implemented or exercised here.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import math
import pickle
import socket
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import errors as auth_errors

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
SHARED_SCHEMA_DIR = (
    REPO_ROOT / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "shared"
)

PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "runtime",
)
CLTR_ROOT = REPO_ROOT / "src" / "pcae" / "cltr"

# The sixteen closed record-family slugs from shared/enums.schema.json's
# record_family enum, read independently below and re-asserted as a
# hard-coded expectation so a schema-file tamper cannot silently widen
# what "record-family model absence" means for this test module.
EXPECTED_RECORD_FAMILY_VALUES = [
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
]

# Class-name fragments that would indicate a record-family model exists.
# Distinct from RecordFamily *enum member* names (which are authorized
# wire-vocabulary values, not classes).
FORBIDDEN_MODEL_CLASS_NAMES = {
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
}

FORBIDDEN_AUTHORITY_BEHAVIOR_SYMBOLS = (
    "resolve_authority",
    "current_authority",
    "activate_epoch",
    "demote_legacy",
    "retire_legacy",
    "authorize_cutover",
    "evaluate_readiness",
    "certify_candidate",
    "publish_generation",
    "recover_journal",
    "quarantine_object",
    "current_authority_pointer",
    "select_authority",
)


def _load_schema_defs(filename: str) -> dict:
    with open(SHARED_SCHEMA_DIR / filename, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc.get("$defs", doc.get("definitions", {}))


# ---------------------------------------------------------------------------
# 1. Independently re-derived inventory / public API verification
# ---------------------------------------------------------------------------


def test_public_api_matches_independently_derived_inventory():
    expected_public_names = {
        "ABSENT",
        "AbsentType",
        "OpaqueJsonValue",
        "verify_round_trip",
        "ExtensionMapping",
        "AuthorityKind",
        "AuthorityRole",
        "MigrationStage",
        "GenerationRole",
        "PublicationState",
        "RecoveryState",
        "CompatibilityMode",
        "RecordFamily",
        "ReasonCode",
        "LegacyLifecycleStateWire",
        "JournalLockState",
        "RecordId",
        "GenerationId",
        "MigrationEpochToken",
        "PhaseIdentity",
        "TransitionId",
        "PrincipalIdentifier",
        "Sha256Digest",
        "RecordDigest",
        "ReferencedRecordDigest",
        "GenerationDigest",
        "PointerDigest",
        "JournalEntryDigest",
        "RecordReference",
        "EpochReference",
        "GenerationReference",
        "require_family",
        "CasExpectation",
        "Limitations",
        "AuthorityDisclosure",
        "Timestamp",
        "SchemaVersionString",
        "RecordEnvelope",
        "field_from_payload",
        "serialize_value",
        "to_dict_fields",
        "to_canonical_bytes",
        "TypedModelError",
        "TypedModelConstructionError",
        "InvalidIdentifierError",
        "InvalidDigestError",
        "InvalidReferenceError",
        "WrongFamilyReferenceError",
        "InvalidTimestampError",
        "UnsupportedJsonValueError",
        "AbsentNullMismatchError",
        "UnsupportedSchemaVersionError",
        "UnknownModelFamilyError",
        "OpaqueValuePreservationError",
        "SerializationError",
        "TypedModelInternalInvariantError",
        "RoundTripMismatchError",
        # Narrowed by Phase 136AB (Typed Model Implementation Group 2):
        # `AuthorityEpoch`/`AuthorityState` and their two small local value
        # types are now legitimate, authorized public exports.
        "AuthorityEpoch",
        "AuthorityState",
        "ActivationState",
        "VerificationState",
        "Uncertainty",
        # Narrowed by Phase 136AD (Typed Model Implementation Group 3):
        # `CutoverRequest`/`ReadinessPackage` and their record-local value
        # types are now legitimate, authorized public exports.
        "CutoverRequest",
        "ReadinessPackage",
        "RequestState",
        "ReadinessState",
        "PrerequisiteStatus",
        "GateResult",
        "FindingVerdict",
        "Finding",
        # Narrowed by Phase 136AF (Typed Model Implementation Group 4):
        # `HumanAuthorization`/`CutoverCandidate`/`Certification` and their
        # record-local value types are now legitimate, authorized public
        # exports.
        "HumanAuthorization",
        "CutoverCandidate",
        "Certification",
        "AuthorizationMethod",
        "AuthorizationState",
        "CandidateState",
        "CertificationState",
        "RevocationMetadata",
        "Staleness",
        "Invalidation",
    }
    assert set(auth.__all__) == expected_public_names
    # No unintended export: every name in __all__ resolves, and nothing
    # beyond documented "private" (underscore) names appears on the module
    # besides intended exports and normal module machinery.
    for name in auth.__all__:
        assert hasattr(auth, name), f"declared export {name!r} missing from module"
    # Submodule attributes (e.g. `auth.enums`, `auth.digest`) are ordinary
    # Python package machinery from the `from .x import Y` statements in
    # __init__.py, not data leakage -- `__all__` is what governs
    # `from pcae.cltr.authority import *` wildcard behavior, checked below.
    non_dunder_non_submodule_extra = {
        n
        for n in dir(auth)
        if not n.startswith("_")
        and n not in expected_public_names
        and n != "annotations"  # `from __future__ import annotations` machinery
        and not isinstance(getattr(auth, n), type(auth))
    }
    assert non_dunder_non_submodule_extra == set(), (
        f"unintended public leakage: {non_dunder_non_submodule_extra}"
    )


def test_wildcard_import_exposes_exactly_declared_all():
    namespace: dict = {}
    exec("from pcae.cltr.authority import *", namespace)
    exported = {k for k in namespace if not k.startswith("_") and k != "__builtins__"}
    assert exported == set(auth.__all__)


def test_no_record_family_model_class_exists_anywhere_in_package():
    # Narrowed by Phase 136AB: `AuthorityEpoch`/`AuthorityState` (Group 2)
    # are now authorized, legitimately-implemented record-family models.
    # Narrowed further by Phase 136AD: `CutoverRequest`/`ReadinessPackage`
    # (Group 3) are now authorized too. Narrowed further by Phase 136AF:
    # `HumanAuthorization`/`CutoverCandidate`/`Certification` (Group 4) are
    # now authorized too. Every one of the other 9 later-group names remains
    # forbidden by this same guard, unchanged.
    authorized_groups_2_3_and_4 = {
        "AuthorityEpoch",
        "AuthorityState",
        "CutoverRequest",
        "ReadinessPackage",
        "HumanAuthorization",
        "CutoverCandidate",
        "Certification",
    }
    still_forbidden = FORBIDDEN_MODEL_CLASS_NAMES - authorized_groups_2_3_and_4
    for path in sorted(AUTHORITY_PACKAGE_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in still_forbidden, (
                    f"forbidden record-family class {node.name!r} found in {path}"
                )
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assert target.id not in still_forbidden


def test_record_family_enum_matches_schema_exactly_no_class_authorization():
    """RecordFamily naming a family is not the same as implementing it."""
    defs = _load_schema_defs("enums.schema.json")
    assert defs["record_family"]["enum"] == EXPECTED_RECORD_FAMILY_VALUES
    assert [m.value for m in auth.RecordFamily] == EXPECTED_RECORD_FAMILY_VALUES
    assert len(auth.RecordFamily) == 16


def test_package_import_has_no_side_effects(monkeypatch):
    """Fresh subprocess import with instrumented socket/subprocess/file-write
    primitives -- any call is Blocking."""
    probe = r"""
import socket, subprocess, sys, builtins

_orig_write_modes = {"w", "a", "x", "w+", "a+", "x+", "wb", "ab", "xb"}
_orig_open = builtins.open


def _guarded_open(file, mode="r", *args, **kwargs):
    if any(m in mode for m in ("w", "a", "x")):
        raise AssertionError(f"unexpected filesystem write during import: {file!r} mode={mode!r}")
    return _orig_open(file, mode, *args, **kwargs)


builtins.open = _guarded_open


def _blocked_socket(*a, **k):
    raise AssertionError("unexpected socket construction during import")


def _blocked_subprocess(*a, **k):
    raise AssertionError("unexpected subprocess spawn during import")


socket.socket = _blocked_socket
socket.create_connection = _blocked_subprocess
subprocess.Popen = _blocked_subprocess

import pcae.cltr.authority as auth  # noqa: E402

assert auth.ABSENT is auth.ABSENT
print("OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_no_production_runtime_module_imports_authority_package():
    pattern_a = "from pcae.cltr.authority"
    pattern_b = "import pcae.cltr.authority"
    scan_dirs = list(PRODUCTION_SCAN_ROOTS) + [
        p for p in CLTR_ROOT.iterdir() if p.is_dir() and p.name != "authority"
    ]
    scan_files = [CLTR_ROOT / "canonicalization.py", CLTR_ROOT / "digest.py"]
    for f in CLTR_ROOT.glob("*.py"):
        if f.name not in {"canonicalization.py"}:
            scan_files.append(f)
    offenders = []
    for root in scan_dirs:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if pattern_a in text or pattern_b in text:
                offenders.append(path)
    for path in set(scan_files):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if pattern_a in text or pattern_b in text:
            offenders.append(path)
    assert offenders == [], f"production import of authority package found: {offenders}"


def test_authority_package_does_not_import_production_lifecycle_modules():
    forbidden_import_fragments = (
        "pcae.commands",
        "pcae.core",
        "pcae.runtime",
        "pcae.cltr.finalization",
        "pcae.cltr.notification",
    )
    for path in sorted(AUTHORITY_PACKAGE_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for fragment in forbidden_import_fragments:
            assert fragment not in text, f"{path} references forbidden {fragment!r}"


def test_no_authority_or_execution_behavior_symbols_present():
    for path in sorted(AUTHORITY_PACKAGE_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for symbol in FORBIDDEN_AUTHORITY_BEHAVIOR_SYMBOLS:
            assert symbol not in text, f"forbidden symbol {symbol!r} found in {path}"


# ---------------------------------------------------------------------------
# 2. ABSENT sentinel
# ---------------------------------------------------------------------------


def test_absent_is_singleton_across_copy_deepcopy_and_reimport():
    a1 = auth.ABSENT
    a2 = copy.copy(auth.ABSENT)
    a3 = copy.deepcopy(auth.ABSENT)
    assert a1 is a2 is a3
    import importlib

    reloaded = importlib.import_module("pcae.cltr.authority.sentinels")
    assert reloaded.ABSENT is auth.ABSENT


def test_absent_distinct_from_falsy_and_none_values():
    assert auth.ABSENT is not None
    assert auth.ABSENT != None  # noqa: E711 -- explicit __eq__ exercise
    assert auth.ABSENT != 0
    assert auth.ABSENT != False  # noqa: E712
    assert auth.ABSENT != ""
    assert auth.ABSENT != ()
    assert auth.ABSENT != {}
    assert auth.ABSENT != []
    with pytest.raises(TypeError):
        bool(auth.ABSENT)


def test_absent_equality_is_identity_only_not_structural():
    class _Empty:
        def __eq__(self, other):
            return True

    assert auth.ABSENT != _Empty()
    assert (auth.ABSENT == auth.ABSENT) is True


def test_absent_repr_and_hash_stable():
    assert repr(auth.ABSENT) == "<absent>"
    assert hash(auth.ABSENT) == hash(auth.ABSENT)


def test_absent_pickle_round_trip_preserves_identity():
    restored = pickle.loads(pickle.dumps(auth.ABSENT))
    assert restored is auth.ABSENT


def test_absent_cannot_be_reconstructed_to_a_second_instance_via_public_api():
    assert auth.AbsentType() is auth.ABSENT


def test_absent_omitted_from_serialization():
    payload = auth.to_dict_fields(
        auth.EpochReference(migration_epoch=auth.MigrationEpochToken("epoch-1"))
    )
    assert "epoch_digest" not in payload


# ---------------------------------------------------------------------------
# 3. OpaqueJsonValue
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        0,
        -1,
        123456789012345,
        0.5,
        -0.5,
        "",
        "héllo wörld ☃",
        [],
        [1, [2, [3, [4]]]],
        {},
        {"a": {"b": {"c": [1, 2, {"d": None}]}}},
        [1, "two", 3.0, None, True, {"x": [False]}],
    ],
)
def test_opaque_json_value_exact_round_trip(value):
    wrapped = auth.OpaqueJsonValue.from_json(value)
    assert wrapped.to_json() == value
    auth.verify_round_trip(value, wrapped)


@pytest.mark.parametrize(
    "bad_value",
    [
        b"bytes",
        bytearray(b"x"),
        {1, 2, 3},
        frozenset({1}),
        object(),
        lambda: None,
        Path("."),
    ],
)
def test_opaque_json_value_rejects_non_json_python_types(bad_value):
    with pytest.raises(auth_errors.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json(bad_value)


def test_opaque_json_value_rejects_non_string_object_keys():
    with pytest.raises(auth_errors.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json({1: "a"})


@pytest.mark.parametrize("bad_float", [float("nan"), float("inf"), float("-inf")])
def test_opaque_json_value_rejects_non_finite_floats(bad_float):
    with pytest.raises(auth_errors.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json(bad_float)
    with pytest.raises(auth_errors.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json([bad_float])


def test_opaque_json_value_to_json_returns_independent_mutable_copy():
    wrapped = auth.OpaqueJsonValue.from_json({"a": [1, 2]})
    out1 = wrapped.to_json()
    out1["a"].append(3)
    out1["b"] = "mutated"
    out2 = wrapped.to_json()
    assert out2 == {"a": [1, 2]}


def test_opaque_json_value_equality_and_hash_are_structural():
    v1 = auth.OpaqueJsonValue.from_json({"a": 1, "b": [1, 2]})
    v2 = auth.OpaqueJsonValue.from_json({"a": 1, "b": [1, 2]})
    assert v1 == v2

    # Hashability is only defined when the frozen tree contains no
    # MappingProxyType/dict node (a nested object makes the whole tuple
    # tree unhashable, by design -- see opaque.py's __hash__ docstring).
    # Array-of-scalars values are hashable; equal inputs hash equal.
    h1 = auth.OpaqueJsonValue.from_json([1, "two", None, True])
    h2 = auth.OpaqueJsonValue.from_json([1, "two", None, True])
    assert h1 == h2
    assert hash(h1) == hash(h2)

    with pytest.raises(TypeError):
        hash(v1)


# ---------------------------------------------------------------------------
# 4. Recursive immutability
# ---------------------------------------------------------------------------


def test_mutable_input_is_defensively_copied_and_original_mutation_has_no_effect():
    original_list = [1, {"k": "v"}]
    wrapped = auth.OpaqueJsonValue.from_json(original_list)
    original_list.append("mutated-after-construction")
    original_list[1]["k"] = "mutated-nested"
    assert wrapped.to_json() == [1, {"k": "v"}]


def test_frozen_container_types_reject_direct_mutation():
    wrapped = auth.OpaqueJsonValue.from_json({"a": [1, 2], "b": {"c": 3}})
    frozen = wrapped._frozen_value
    assert isinstance(frozen, MappingProxyType)
    with pytest.raises(TypeError):
        frozen["a"] = "nope"
    nested_tuple = frozen["a"]
    assert isinstance(nested_tuple, tuple)
    with pytest.raises(TypeError):
        nested_tuple[0] = "nope"
    nested_map = frozen["b"]
    assert isinstance(nested_map, MappingProxyType)
    with pytest.raises(TypeError):
        nested_map["c"] = "nope"


def test_deeply_nested_mutation_does_not_leak_through_repeated_to_json_calls():
    wrapped = auth.OpaqueJsonValue.from_json({"outer": {"inner": [1, [2, 3]]}})
    first = wrapped.to_json()
    first["outer"]["inner"][1].append(4)
    second = wrapped.to_json()
    assert second == {"outer": {"inner": [1, [2, 3]]}}


# ---------------------------------------------------------------------------
# 5. ExtensionMapping
# ---------------------------------------------------------------------------


def test_extension_mapping_preserves_keys_values_order_and_unicode():
    src = {"z_last": 1, "a_first": "héllo☃", "nested": {"deep": [1, None, True]}}
    ext = auth.ExtensionMapping.from_mapping(src)
    # keys()/items() iterate the frozen (order-preserving) representation
    # directly -- nested values there are the frozen (tuple/MappingProxyType)
    # forms, not thawed plain dict/list; to_dict() is the thawed accessor.
    assert list(ext.keys()) == list(src.keys())
    assert ext.to_dict() == src
    assert ext.to_dict() == dict(zip(src.keys(), (ext[k] for k in src)))


def test_extension_mapping_empty_allowed():
    ext = auth.ExtensionMapping.from_mapping({})
    assert len(ext) == 0
    assert ext.to_dict() == {}


def test_extension_mapping_explicit_null_preserved():
    ext = auth.ExtensionMapping.from_mapping({"k": None})
    assert ext["k"] is None
    assert ext.to_dict() == {"k": None}


def test_extension_mapping_rejects_reserved_key_collision():
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ExtensionMapping.from_mapping(
            {"schema_id": "collide"}, reserved_keys={"schema_id"}
        )


def test_extension_mapping_does_not_reject_canonical_lookalike_without_reserved_keys_declared():
    """Documents the shared-core boundary: collision prevention requires
    the embedding record model to supply its own reserved-key set;
    shared core alone has no canonical-field knowledge to protect."""
    ext = auth.ExtensionMapping.from_mapping({"schema_id": "not actually reserved here"})
    assert ext["schema_id"] == "not actually reserved here"


def test_extension_mapping_enforces_max_properties_bound():
    too_many = {f"k{i}": i for i in range(auth.ExtensionMapping.__mro__[0] and 33)}
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ExtensionMapping.from_mapping(too_many)


def test_extension_mapping_is_immutable_and_deep_copied_on_construction():
    src = {"list": [1, 2, 3]}
    ext = auth.ExtensionMapping.from_mapping(src)
    src["list"].append(4)
    src["new_key"] = "added-after"
    assert ext.to_dict() == {"list": [1, 2, 3]}
    with pytest.raises(TypeError):
        ext._frozen_mapping["list"] = "nope"  # type: ignore[index]


def test_extension_mapping_is_unhashable():
    ext = auth.ExtensionMapping.from_mapping({"a": 1})
    with pytest.raises(TypeError):
        hash(ext)


def test_extension_mapping_serializes_deterministically_via_to_dict_fields():
    epoch_ref = auth.EpochReference(migration_epoch=auth.MigrationEpochToken("epoch-1"))
    bytes1 = auth.to_canonical_bytes(auth.to_dict_fields(epoch_ref))
    bytes2 = auth.to_canonical_bytes(auth.to_dict_fields(epoch_ref))
    assert bytes1 == bytes2


# ---------------------------------------------------------------------------
# 6. Enums -- independently derived from shared/enums.schema.json and
#    shared/failures.schema.json
# ---------------------------------------------------------------------------


_ENUM_SCHEMA_MAP = {
    "AuthorityKind": ("enums.schema.json", "authority_kind"),
    "AuthorityRole": ("enums.schema.json", "authority_role"),
    "MigrationStage": ("enums.schema.json", "migration_stage"),
    "GenerationRole": ("enums.schema.json", "generation_role"),
    "PublicationState": ("enums.schema.json", "publication_state"),
    "RecoveryState": ("enums.schema.json", "recovery_state"),
    "CompatibilityMode": ("enums.schema.json", "compatibility_mode"),
    "RecordFamily": ("enums.schema.json", "record_family"),
    "ReasonCode": ("failures.schema.json", "reason_code"),
}


@pytest.mark.parametrize("enum_name", sorted(_ENUM_SCHEMA_MAP))
def test_shared_enum_exact_member_values_from_schema(enum_name):
    filename, defs_key = _ENUM_SCHEMA_MAP[enum_name]
    expected_values = _load_schema_defs(filename)[defs_key]["enum"]
    enum_cls = getattr(auth, enum_name)
    actual_values = [m.value for m in enum_cls]
    assert actual_values == expected_values, (
        f"{enum_name} member values diverge from {filename}#/$defs/{defs_key}"
    )
    assert len(enum_cls) == len(expected_values)


@pytest.mark.parametrize("enum_name", sorted(_ENUM_SCHEMA_MAP))
def test_shared_enum_fail_closed_on_bad_variants(enum_name):
    filename, defs_key = _ENUM_SCHEMA_MAP[enum_name]
    valid_value = _load_schema_defs(filename)[defs_key]["enum"][0]
    enum_cls = getattr(auth, enum_name)
    bad_variants = [
        valid_value.upper(),
        valid_value.title(),
        f" {valid_value}",
        f"{valid_value} ",
        valid_value.replace("_", "-") if "_" in valid_value else valid_value + "-x",
        "totally_unknown_value_xyz",
    ]
    for bad in bad_variants:
        if bad == valid_value:
            continue
        with pytest.raises(ValueError):
            enum_cls(bad)
    with pytest.raises(ValueError):
        enum_cls(None)
    with pytest.raises(ValueError):
        enum_cls(12345)


def test_embedded_local_enums_from_cas_expectation_schema_definition():
    cas_def = _load_schema_defs("references.schema.json")["cas_expectation"]
    lifecycle_values = cas_def["properties"]["expected_source_lifecycle_state"]["enum"]
    lock_values = cas_def["properties"]["expected_journal_lock_state"]["enum"]
    assert [m.value for m in auth.LegacyLifecycleStateWire] == lifecycle_values
    assert [m.value for m in auth.JournalLockState] == lock_values
    assert len(auth.LegacyLifecycleStateWire) == 12
    assert len(auth.JournalLockState) == 2


def test_enum_serialization_emits_plain_wire_string_not_member_name():
    ref = auth.EpochReference(migration_epoch=auth.MigrationEpochToken("epoch-1"))
    assert auth.serialize_value(auth.AuthorityKind.LEGACY) == "legacy"
    assert auth.serialize_value(auth.AuthorityKind.LEGACY) != "LEGACY"
    assert isinstance(auth.serialize_value(auth.AuthorityKind.LEGACY), str)
    del ref  # unused beyond sanity import check


def test_enum_no_boolean_lifecycle_method_exists():
    for enum_name in _ENUM_SCHEMA_MAP:
        enum_cls = getattr(auth, enum_name)
        member = next(iter(enum_cls))
        assert not hasattr(member, "is_authoritative")
        assert not hasattr(member, "is_legal_transition")


# ---------------------------------------------------------------------------
# 7. Identifiers -- independently derived from shared/identity.schema.json
# ---------------------------------------------------------------------------


_IDENTITY_SCHEMA_MAP = {
    "RecordId": "record_identity",
    "GenerationId": "generation_identity",
    "MigrationEpochToken": "migration_epoch",
    "PhaseIdentity": "phase_identity",
    "TransitionId": "transition_identity",
    "PrincipalIdentifier": "principal_identifier",
}


@pytest.mark.parametrize("wrapper_name", sorted(_IDENTITY_SCHEMA_MAP))
def test_identifier_wrapper_pattern_matches_schema_exactly(wrapper_name):
    import re

    defs_key = _IDENTITY_SCHEMA_MAP[wrapper_name]
    expected_pattern = _load_schema_defs("identity.schema.json")[defs_key]["pattern"]
    wrapper_cls = getattr(auth, wrapper_name)

    # Independently probe the wrapper's accepted-language boundary using
    # the expected pattern's own compiled regex, rather than trusting the
    # implementation's internal pattern object.
    compiled = re.compile(expected_pattern)
    candidates = [
        "a" * 8,
        "a1234567",
        "a" * 200,
        "",
        "A" * 8,
        "trans-ab",
        "user@example.com",
        "136C",
        "with space",
        "epoch..bad",
    ]
    for candidate in candidates:
        should_pass = bool(compiled.fullmatch(candidate))
        if should_pass:
            instance = wrapper_cls(candidate)
            assert instance.to_wire() == candidate
            assert str(instance) == candidate
        else:
            with pytest.raises(auth_errors.InvalidIdentifierError):
                wrapper_cls(candidate)


def test_identifier_families_do_not_auto_convert_across_types():
    """A RecordId instance is not itself a valid GenerationId.value (must
    be a plain str matching GenerationId's own pattern) -- the wrapper
    types are the validation boundary, not the field's static annotation
    (frozen stdlib dataclasses do not runtime-enforce annotations)."""
    record_id = auth.RecordId("authority-epoch-1")
    with pytest.raises(auth_errors.InvalidIdentifierError):
        auth.GenerationId(record_id)  # type: ignore[arg-type]
    assert type(record_id) is not auth.GenerationId


def test_identifier_rejects_none_and_non_string():
    for wrapper_name in _IDENTITY_SCHEMA_MAP:
        wrapper_cls = getattr(auth, wrapper_name)
        with pytest.raises(auth_errors.InvalidIdentifierError):
            wrapper_cls(None)  # type: ignore[arg-type]
        with pytest.raises(auth_errors.InvalidIdentifierError):
            wrapper_cls(12345)  # type: ignore[arg-type]


def test_identifier_preserves_exact_wire_string_no_normalization():
    value = "trans-ABCxyz-1"
    lowered = value.lower()
    normalized = auth.TransitionId(lowered)
    assert normalized.value == lowered
    assert normalized.value != value


# ---------------------------------------------------------------------------
# 8. Digests -- independently derived from shared/digest.schema.json
# ---------------------------------------------------------------------------


_DIGEST_WRAPPER_NAMES = (
    "Sha256Digest",
    "RecordDigest",
    "ReferencedRecordDigest",
    "GenerationDigest",
    "PointerDigest",
    "JournalEntryDigest",
)

VALID_SHA256_HEX = "a" * 64
VALID_SHA256_HEX_MIXED = "0123456789abcdef" * 4


@pytest.mark.parametrize("wrapper_name", _DIGEST_WRAPPER_NAMES)
def test_digest_wrapper_accepts_exact_shape_only(wrapper_name):
    defs = _load_schema_defs("digest.schema.json")
    expected_pattern = defs["sha256_hex"]["pattern"]
    assert expected_pattern == r"^[0-9a-f]{64}$"
    wrapper_cls = getattr(auth, wrapper_name)
    instance = wrapper_cls(VALID_SHA256_HEX_MIXED)
    assert instance.to_wire() == VALID_SHA256_HEX_MIXED


@pytest.mark.parametrize("wrapper_name", _DIGEST_WRAPPER_NAMES)
@pytest.mark.parametrize(
    "bad_value",
    [
        "A" * 64,  # uppercase
        "g" * 64,  # invalid hex char
        "a" * 63,  # too short
        "a" * 65,  # too long
        "",
        "sha256:" + "a" * 64,  # extraneous prefix
        " " + "a" * 63,  # whitespace
        "a" * 64 + " ",
    ],
)
def test_digest_wrapper_rejects_malformed_values(wrapper_name, bad_value):
    wrapper_cls = getattr(auth, wrapper_name)
    with pytest.raises(auth_errors.InvalidDigestError):
        wrapper_cls(bad_value)


def test_digest_wrapper_cross_family_substitution_is_type_distinct_not_forbidden_at_runtime():
    """Digest wrapper types are distinct dataclasses (a RecordDigest is not
    a ReferencedRecordDigest at the type level) even though both accept the
    same wire shape -- shape validation does not imply cross-type identity."""
    record_digest = auth.RecordDigest(VALID_SHA256_HEX)
    referenced_digest = auth.ReferencedRecordDigest(VALID_SHA256_HEX)
    assert type(record_digest) is not type(referenced_digest)
    assert record_digest != referenced_digest


def test_digest_wrapper_does_not_compute_or_normalize(monkeypatch):
    """Instrument hashlib to prove no wrapper computes a digest."""
    import hashlib

    calls = []
    original_sha256 = hashlib.sha256

    def _tracking_sha256(*args, **kwargs):
        calls.append((args, kwargs))
        return original_sha256(*args, **kwargs)

    monkeypatch.setattr(hashlib, "sha256", _tracking_sha256)
    for wrapper_name in _DIGEST_WRAPPER_NAMES:
        getattr(auth, wrapper_name)(VALID_SHA256_HEX_MIXED)
    assert calls == [], "a digest wrapper called hashlib.sha256 during construction"


# ---------------------------------------------------------------------------
# 9. References
# ---------------------------------------------------------------------------


def _make_record_ref(family: auth.RecordFamily) -> auth.RecordReference:
    return auth.RecordReference(
        record_id=auth.RecordId("record-abcdefgh"),
        record_digest=auth.ReferencedRecordDigest(VALID_SHA256_HEX),
        record_family=family,
    )


def test_record_reference_required_and_conditional_fields():
    ref = _make_record_ref(auth.RecordFamily.AUTHORITY_EPOCH)
    assert ref.schema_id is auth.ABSENT
    assert ref.schema_version is auth.ABSENT
    payload = auth.to_dict_fields(ref)
    assert "schema_id" not in payload
    assert "schema_version" not in payload
    assert payload["record_family"] == "authority_epoch"


def test_record_reference_does_not_dereference_or_check_existence():
    """A reference to a record_id that (by construction) cannot exist
    anywhere on disk must still construct successfully -- shape only."""
    ref = auth.RecordReference(
        record_id=auth.RecordId("nonexistent-record-zzz"),
        record_digest=auth.ReferencedRecordDigest("f" * 64),
        record_family=auth.RecordFamily.QUARANTINE_RECORD,
    )
    assert ref.record_id.value == "nonexistent-record-zzz"


def test_record_family_enum_itself_is_the_strict_validation_boundary():
    with pytest.raises(ValueError):
        auth.RecordFamily("not_a_real_family")


def test_record_reference_does_not_re_validate_enum_membership_of_raw_values():
    """NON-BLOCKING finding (documented, not silently accepted as
    intended): ``RecordReference`` has no ``__post_init__``, so
    constructing it directly with a raw (non-``RecordFamily``) string for
    ``record_family`` succeeds and that raw string round-trips through
    ``to_dict_fields`` verbatim -- frozen stdlib dataclasses never
    runtime-enforce field type annotations by themselves. The strict,
    fail-closed boundary is ``RecordFamily(raw_str)`` itself (proven
    above); a future record-family model's own ``from_dict`` (136Y plan
    Sec.16, not yet implemented -- Group 2+) is responsible for calling
    ``RecordFamily(raw_str)`` before constructing a ``RecordReference``,
    never passing a payload's raw string straight through unchecked."""
    ref = auth.RecordReference(
        record_id=auth.RecordId("record-abcdefgh"),
        record_digest=auth.ReferencedRecordDigest(VALID_SHA256_HEX),
        record_family="not_a_real_family",  # type: ignore[arg-type]
    )
    assert ref.record_family == "not_a_real_family"
    assert auth.to_dict_fields(ref)["record_family"] == "not_a_real_family"


def test_record_reference_omitted_required_field_raises():
    with pytest.raises(TypeError):
        auth.RecordReference(  # type: ignore[call-arg]
            record_digest=auth.ReferencedRecordDigest(VALID_SHA256_HEX),
            record_family=auth.RecordFamily.AUTHORITY_EPOCH,
        )


def test_generation_reference_always_paired():
    with pytest.raises(TypeError):
        auth.GenerationReference(generation_id=auth.GenerationId("gen-abcdefgh"))  # type: ignore[call-arg]
    ref = auth.GenerationReference(
        generation_id=auth.GenerationId("gen-abcdefgh"),
        generation_digest=auth.GenerationDigest(VALID_SHA256_HEX),
    )
    assert ref.generation_id.value == "gen-abcdefgh"


def test_epoch_reference_epoch_digest_defaults_absent_distinct_from_null():
    ref_absent = auth.EpochReference(migration_epoch=auth.MigrationEpochToken("epoch-1"))
    ref_null = auth.EpochReference(
        migration_epoch=auth.MigrationEpochToken("epoch-1"), epoch_digest=None
    )
    assert ref_absent.epoch_digest is auth.ABSENT
    assert ref_null.epoch_digest is None
    assert "epoch_digest" not in auth.to_dict_fields(ref_absent)
    assert auth.to_dict_fields(ref_null)["epoch_digest"] is None


def test_reference_immutable():
    ref = _make_record_ref(auth.RecordFamily.CERTIFICATION)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.record_id = auth.RecordId("other-record")  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 10. require_family
# ---------------------------------------------------------------------------


def test_require_family_accepts_exact_match_only():
    ref = _make_record_ref(auth.RecordFamily.CUTOVER_REQUEST)
    result = auth.require_family(ref, auth.RecordFamily.CUTOVER_REQUEST)
    assert result is ref


def test_require_family_rejects_other_families_and_does_not_mutate():
    ref = _make_record_ref(auth.RecordFamily.CUTOVER_REQUEST)
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.require_family(ref, auth.RecordFamily.CERTIFICATION)
    assert ref.record_family is auth.RecordFamily.CUTOVER_REQUEST


def test_require_family_error_deterministic_and_family_case_sensitive():
    ref = _make_record_ref(auth.RecordFamily.CUTOVER_REQUEST)
    with pytest.raises(auth_errors.WrongFamilyReferenceError) as exc_info:
        auth.require_family(ref, auth.RecordFamily.CERTIFICATION)
    message = str(exc_info.value)
    assert "cutover_request" in message
    assert "certification" in message


def test_require_family_is_public_per_declared_all():
    assert "require_family" in auth.__all__


# ---------------------------------------------------------------------------
# 11. CasExpectation -- independently derived from
#     shared/references.schema.json#/$defs/cas_expectation
# ---------------------------------------------------------------------------


def _valid_cas_kwargs():
    return dict(
        expected_authority_kind=auth.AuthorityKind.LEGACY,
        expected_authority_epoch=_make_record_ref(auth.RecordFamily.AUTHORITY_EPOCH),
        expected_authoritative_generation=auth.GenerationReference(
            generation_id=auth.GenerationId("gen-abcdefgh"),
            generation_digest=auth.GenerationDigest(VALID_SHA256_HEX),
        ),
        expected_authority_pointer_digest=auth.PointerDigest(VALID_SHA256_HEX),
        expected_authority_state_digest=auth.Sha256Digest(VALID_SHA256_HEX),
        expected_migration_epoch=auth.MigrationEpochToken("epoch-1"),
        expected_source_lifecycle_state=auth.LegacyLifecycleStateWire.CERTIFIED,
        expected_compatibility_mode=auth.CompatibilityMode.LEGACY_AUTHORITATIVE,
        expected_journal_lock_state=auth.JournalLockState.UNLOCKED,
        expected_request_reference=_make_record_ref(auth.RecordFamily.CUTOVER_REQUEST),
        expected_certification_reference=_make_record_ref(auth.RecordFamily.CERTIFICATION),
    )


def test_cas_expectation_field_inventory_matches_executable_schema_exactly():
    schema_required = _load_schema_defs("references.schema.json")["cas_expectation"][
        "required"
    ]
    dataclass_fields = [f.name for f in dataclasses.fields(auth.CasExpectation)]
    assert set(dataclass_fields) == set(schema_required)
    assert len(dataclass_fields) == 11
    cas = auth.CasExpectation(**_valid_cas_kwargs())
    for name in dataclass_fields:
        assert getattr(cas, name) is not auth.ABSENT, f"{name} must not default to ABSENT"


def test_cas_expectation_all_fields_mandatory_none_optional():
    kwargs = _valid_cas_kwargs()
    for missing_field in kwargs:
        partial = dict(kwargs)
        del partial[missing_field]
        with pytest.raises(TypeError):
            auth.CasExpectation(**partial)


def test_cas_expectation_enforces_family_restricted_reference_fields():
    kwargs = _valid_cas_kwargs()
    kwargs["expected_authority_epoch"] = _make_record_ref(auth.RecordFamily.CERTIFICATION)
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.CasExpectation(**kwargs)

    kwargs = _valid_cas_kwargs()
    kwargs["expected_request_reference"] = _make_record_ref(auth.RecordFamily.AUTHORITY_EPOCH)
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.CasExpectation(**kwargs)

    kwargs = _valid_cas_kwargs()
    kwargs["expected_certification_reference"] = _make_record_ref(
        auth.RecordFamily.CUTOVER_REQUEST
    )
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.CasExpectation(**kwargs)


def test_cas_expectation_does_not_evaluate_or_read_current_state():
    """Constructing a CasExpectation must never touch the filesystem, since
    it represents an *expected* state, never an observed one."""
    import builtins

    original_open = builtins.open
    calls = []

    def _tracking_open(*args, **kwargs):
        calls.append(args)
        return original_open(*args, **kwargs)

    builtins.open = _tracking_open
    try:
        auth.CasExpectation(**_valid_cas_kwargs())
    finally:
        builtins.open = original_open
    assert calls == []


def test_cas_expectation_round_trip_preserves_wire_shape():
    cas = auth.CasExpectation(**_valid_cas_kwargs())
    payload = auth.to_dict_fields(cas)
    assert payload["expected_authority_kind"] == "legacy"
    assert payload["expected_journal_lock_state"] == "unlocked"
    assert payload["expected_authority_epoch"]["record_family"] == "authority_epoch"


def test_cas_expectation_immutable():
    cas = auth.CasExpectation(**_valid_cas_kwargs())
    with pytest.raises(dataclasses.FrozenInstanceError):
        cas.expected_authority_kind = auth.AuthorityKind.CLTR  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 12. Limitations / AuthorityDisclosure -- independently derived from
#     shared/limitations.schema.json
# ---------------------------------------------------------------------------


def test_limitations_bounds_match_schema():
    defs = _load_schema_defs("limitations.schema.json")
    assert defs["limitations_array"]["maxItems"] == 32
    assert defs["limitation_entry"]["maxLength"] == 2000
    assert auth.Limitations().entries == ()
    long_entry = "x" * 2000
    lim = auth.Limitations(entries=(long_entry,))
    assert lim.entries == (long_entry,)
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.Limitations(entries=("x" * 2001,))
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.Limitations(entries=tuple(f"entry-{i}" for i in range(33)))


def test_limitations_rejects_control_characters_and_excess_newlines():
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.Limitations(entries=("bad\x00char",))
    ok_newlines = "line\n" * 8 + "tail"
    auth.Limitations(entries=(ok_newlines,))
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.Limitations(entries=("line\n" * 9 + "tail",))


def test_limitations_never_downgrades_or_suppresses_errors():
    """A Limitations disclosure cannot make an otherwise-invalid
    CasExpectation valid -- there is no code path linking the two."""
    lim = auth.Limitations(entries=("known gap: X is not verified",))
    assert not hasattr(lim, "suppress")
    assert not hasattr(lim, "authorize")


def test_limitations_to_wire_is_plain_array():
    lim = auth.Limitations(entries=("a", "b"))
    assert lim.to_wire() == ["a", "b"]


def test_authority_disclosure_is_authoritative_pinned_false():
    defs = _load_schema_defs("limitations.schema.json")
    assert defs["authority_disclosure"]["properties"]["is_authoritative"]["const"] is False
    disclosure = auth.AuthorityDisclosure(
        authority_role=auth.AuthorityRole.DERIVATIVE,
        disclosure_text="Derived from legacy pointer, not itself authoritative.",
    )
    assert disclosure.is_authoritative is False
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityDisclosure(
            authority_role=auth.AuthorityRole.DERIVATIVE,
            disclosure_text="attempt to override",
            is_authoritative=True,
        )


def test_authority_disclosure_text_bounds_and_charset():
    defs = _load_schema_defs("limitations.schema.json")
    assert defs["disclosure_text"]["maxLength"] == 500
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityDisclosure(
            authority_role=auth.AuthorityRole.EVIDENCE, disclosure_text="x" * 501
        )
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityDisclosure(
            authority_role=auth.AuthorityRole.EVIDENCE, disclosure_text="multi\nline"
        )
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityDisclosure(authority_role=auth.AuthorityRole.EVIDENCE, disclosure_text="")


# ---------------------------------------------------------------------------
# 13. RecordEnvelope / Timestamp -- independently derived from
#     shared/envelope.schema.json
# ---------------------------------------------------------------------------


def test_record_envelope_field_inventory_matches_schema_exactly():
    schema_required = _load_schema_defs("envelope.schema.json")["companion_envelope"][
        "required"
    ]
    dataclass_fields = {f.name for f in dataclasses.fields(auth.RecordEnvelope)}
    assert dataclass_fields == set(schema_required)
    assert len(dataclass_fields) == 7


def _make_envelope(**overrides) -> auth.RecordEnvelope:
    kwargs = dict(
        schema_id="records/authority_epoch.schema.json",
        schema_version=auth.SchemaVersionString("1.0"),
        record_type="authority_epoch",
        record_id=auth.RecordId("authority-epoch1"),
        record_digest=auth.RecordDigest(VALID_SHA256_HEX),
        created_at=auth.Timestamp("2026-07-17T10:00:00Z"),
    )
    kwargs.update(overrides)
    return auth.RecordEnvelope(**kwargs)


def test_record_envelope_contract_version_frozen_const():
    env = _make_envelope()
    assert env.contract_version == "1.0"
    with pytest.raises(auth_errors.TypedModelConstructionError):
        _make_envelope(contract_version="2.0")


def test_record_envelope_is_not_itself_a_record_family_model():
    assert auth.RecordEnvelope.__name__ not in FORBIDDEN_MODEL_CLASS_NAMES
    env = _make_envelope()
    assert not hasattr(env, "record_family")


def test_record_envelope_schema_id_and_record_type_length_bounds():
    with pytest.raises(auth_errors.TypedModelConstructionError):
        _make_envelope(schema_id="")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        _make_envelope(record_type="")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        _make_envelope(schema_id="x" * 513)
    with pytest.raises(auth_errors.TypedModelConstructionError):
        _make_envelope(record_type="x" * 129)


@pytest.mark.parametrize(
    "wire",
    [
        "2026-07-17T10:00:00Z",
        "2026-07-17T10:00:00.5Z",
        "2026-07-17T10:00:00.123456Z",
        "2026-01-01T00:00:00Z",
        "2026-12-31T23:59:59.999999Z",
    ],
)
def test_timestamp_preserves_exact_wire_string(wire):
    ts = auth.Timestamp(wire)
    assert ts.to_wire() == wire
    assert str(ts) == wire
    assert auth.serialize_value(ts) == wire


def test_timestamp_does_not_normalize_z_suffix_to_numeric_offset():
    ts = auth.Timestamp("2026-07-17T10:00:00Z")
    assert ts.wire == "2026-07-17T10:00:00Z"
    assert ts.wire != "2026-07-17T10:00:00+00:00"


@pytest.mark.parametrize(
    "bad_wire",
    [
        "2026-07-17T10:00:00+00:00",  # numeric offset, forbidden by pattern
        "2026-07-17T10:00:00-05:00",
        "2026-07-17 10:00:00Z",  # missing 'T'
        "2026-07-17T10:00:00",  # missing 'Z'
        "2026-07-17T10:00:00.1234567Z",  # 7 fractional digits, too many
        "not-a-timestamp",
        "",
        None,
    ],
)
def test_timestamp_rejects_malformed_wire_strings(bad_wire):
    with pytest.raises(auth_errors.InvalidTimestampError):
        auth.Timestamp(bad_wire)  # type: ignore[arg-type]


def test_timestamp_pattern_matches_schema_exactly():
    schema_pattern = _load_schema_defs("envelope.schema.json")["timestamp"]["pattern"]
    assert schema_pattern == r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$"


def test_timestamp_never_reads_clock_or_defaults_to_now():
    sig = dataclasses.fields(auth.Timestamp)
    assert len(sig) == 1
    assert sig[0].default is dataclasses.MISSING


def test_timestamp_to_datetime_is_derived_convenience_never_serialization_source():
    ts = auth.Timestamp("2026-07-17T10:00:00.123456Z")
    dt = ts.to_datetime()
    assert dt.year == 2026 and dt.month == 7 and dt.day == 17
    # Serialization must still emit the original wire string, not a
    # re-derived datetime.isoformat() rendering.
    assert auth.serialize_value(ts) == "2026-07-17T10:00:00.123456Z"
    assert auth.serialize_value(ts) != dt.isoformat()


@pytest.mark.parametrize(
    "wire",
    [
        "2026-07-17T10:00:00.5Z",
        "2026-07-17T10:00:00.50Z",
        "2026-07-17T10:00:00.5000Z",
        "2026-07-17T10:00:00.50000Z",
    ],
)
def test_finding_to_datetime_crashes_on_valid_non_3_or_6_digit_fractional_wire_under_py39_floor(
    wire,
):
    """CONFIRMED, NON-BLOCKING finding: the wire pattern
    (``\\.\\d{1,6}``, matching shared/envelope.schema.json#/$defs/timestamp
    exactly) permits 1, 2, 4, or 5 fractional digits, and ``Timestamp``
    construction correctly accepts such wire strings (proven above,
    ``test_timestamp_preserves_exact_wire_string``). But
    ``Timestamp.to_datetime()`` builds ``wire[:-1] + "+00:00"`` and calls
    ``datetime.datetime.fromisoformat`` on it, which requires exactly 3 or
    6 fractional digits on the project's declared Python floor
    (``pyproject.toml``'s ``requires-python = ">=3.9"``) -- Python 3.9-3.10
    ``fromisoformat`` does not accept arbitrary microsecond-digit counts
    (that relaxation landed in Python 3.11). A schema-valid, correctly
    constructed ``Timestamp`` therefore raises ``ValueError`` from this
    *derived convenience* method alone on the declared floor. Wire
    fidelity, construction, and serialization (``to_wire``/
    ``serialize_value``) are all unaffected -- this is scoped to
    ``to_datetime()`` only, which contract/plan text explicitly describes
    as non-authoritative and never used internally by this package's own
    serialization path (grep-verified: no other module in
    ``src/pcae/cltr/authority`` calls ``to_datetime``)."""
    ts = auth.Timestamp(wire)
    with pytest.raises(ValueError):
        ts.to_datetime()
    # Wire fidelity remains intact regardless of the convenience-method gap.
    assert ts.to_wire() == wire
    assert auth.serialize_value(ts) == wire


# ---------------------------------------------------------------------------
# 14. Error hierarchy
# ---------------------------------------------------------------------------


_EXPECTED_ERROR_HIERARCHY = {
    "TypedModelError": "Exception",
    "TypedModelConstructionError": "TypedModelError",
    "InvalidIdentifierError": "TypedModelConstructionError",
    "InvalidDigestError": "TypedModelConstructionError",
    "InvalidReferenceError": "TypedModelConstructionError",
    "WrongFamilyReferenceError": "InvalidReferenceError",
    "InvalidTimestampError": "TypedModelConstructionError",
    "UnsupportedJsonValueError": "TypedModelConstructionError",
    "AbsentNullMismatchError": "TypedModelConstructionError",
    "UnsupportedSchemaVersionError": "TypedModelError",
    "UnknownModelFamilyError": "TypedModelError",
    "OpaqueValuePreservationError": "TypedModelError",
    "SerializationError": "TypedModelError",
    "TypedModelInternalInvariantError": "TypedModelError",
    "RoundTripMismatchError": "TypedModelError",
}


def test_error_hierarchy_exact_inheritance():
    for name, parent_name in _EXPECTED_ERROR_HIERARCHY.items():
        cls = getattr(auth_errors, name)
        assert issubclass(cls, Exception)
        if parent_name != "Exception":
            parent_cls = getattr(auth_errors, parent_name)
            assert issubclass(cls, parent_cls), f"{name} must subclass {parent_name}"


def test_error_hierarchy_count_matches_plan_disclosed_fourteen_plus_base():
    # 136Z's own docstring claims 14 concrete error classes; independently
    # count them here rather than trusting that claim.
    all_error_names = [n for n in auth.__all__ if n.endswith("Error")]
    assert len(all_error_names) == 15  # 14 concrete + TypedModelError base
    assert "TypedModelError" in all_error_names


def test_error_messages_do_not_leak_field_values_beyond_type_names():
    with pytest.raises(auth_errors.InvalidDigestError) as exc_info:
        auth.RecordDigest("not-a-real-digest-value-that-could-look-secret-ish")
    message = str(exc_info.value)
    assert "not-a-real-digest-value-that-could-look-secret-ish" not in message


def test_error_repr_is_safe_and_deterministic():
    err = auth_errors.InvalidIdentifierError("boundary message")
    assert repr(err) == "InvalidIdentifierError('boundary message')"


# ---------------------------------------------------------------------------
# 15. Serialization primitives
# ---------------------------------------------------------------------------


def test_field_from_payload_distinguishes_absent_from_explicit_null():
    payload_with_null = {"k": None}
    payload_without_key = {}
    assert auth.field_from_payload(payload_with_null, "k") is None
    assert auth.field_from_payload(payload_without_key, "k") is auth.ABSENT


def test_serialize_value_rejects_bare_absent():
    with pytest.raises(auth_errors.SerializationError):
        auth.serialize_value(auth.ABSENT)


def test_serialize_value_rejects_unsupported_python_object():
    class _Arbitrary:
        pass

    with pytest.raises(auth_errors.SerializationError):
        auth.serialize_value(_Arbitrary())


def test_to_dict_fields_omits_absent_and_serializes_present_fields():
    ref = auth.EpochReference(migration_epoch=auth.MigrationEpochToken("epoch-1"))
    result = auth.to_dict_fields(ref)
    assert result == {"migration_epoch": "epoch-1"}


def test_to_dict_fields_preserves_nested_opaque_and_extension_values():
    ref = _make_record_ref(auth.RecordFamily.AUTHORITY_EPOCH)
    cas = auth.CasExpectation(**{**_valid_cas_kwargs(), "expected_authority_epoch": ref})
    result = auth.to_dict_fields(cas)
    assert isinstance(result, dict)
    assert result["expected_authority_epoch"]["record_id"] == ref.record_id.value
    assert all(not dataclasses.is_dataclass(v) for v in result.values())


def test_to_canonical_bytes_deterministic_across_equal_dicts():
    d1 = {"b": 1, "a": 2}
    d2 = {"a": 2, "b": 1}
    assert auth.to_canonical_bytes(d1) == auth.to_canonical_bytes(d2)


def test_to_canonical_bytes_delegates_to_existing_canonicalization_module():
    from pcae.cltr import canonicalization

    payload = {"x": 1}
    assert auth.to_canonical_bytes(payload) == canonicalization.canonicalize_dict(payload)


def test_no_competing_canonicalization_implementation_in_authority_package():
    text = (AUTHORITY_PACKAGE_DIR / "serialization.py").read_text(encoding="utf-8")
    assert "from pcae.cltr.canonicalization import canonicalize_dict" in text
    for path in AUTHORITY_PACKAGE_DIR.rglob("*.py"):
        if path.name == "serialization.py":
            continue
        content = path.read_text(encoding="utf-8")
        assert "canonicalize" not in content.lower() or "canonicalization" not in content


# ---------------------------------------------------------------------------
# 16. Adversarial round-trip matrix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label,build,expected_wire_check",
    [
        (
            "absent-field",
            lambda: auth.EpochReference(migration_epoch=auth.MigrationEpochToken("e1")),
            lambda value: "epoch_digest" not in auth.to_dict_fields(value),
        ),
        (
            "explicit-null-field",
            lambda: auth.EpochReference(
                migration_epoch=auth.MigrationEpochToken("e1"), epoch_digest=None
            ),
            lambda value: auth.to_dict_fields(value)["epoch_digest"] is None,
        ),
        (
            "opaque-scalar",
            lambda: auth.OpaqueJsonValue.from_json(42),
            lambda value: value.to_json() == 42,
        ),
        (
            "opaque-array",
            lambda: auth.OpaqueJsonValue.from_json([1, "two", None]),
            lambda value: value.to_json() == [1, "two", None],
        ),
        (
            "opaque-object",
            lambda: auth.OpaqueJsonValue.from_json({"k": [1, {"nested": True}]}),
            lambda value: value.to_json() == {"k": [1, {"nested": True}]},
        ),
        (
            "extension-mapping",
            lambda: auth.ExtensionMapping.from_mapping({"note": "value"}),
            lambda value: value.to_dict() == {"note": "value"},
        ),
        (
            "enum",
            lambda: auth.AuthorityKind.CLTR,
            lambda value: auth.serialize_value(value) == "cltr",
        ),
        (
            "identifier",
            lambda: auth.RecordId("record-abcdefgh"),
            lambda value: value.to_wire() == "record-abcdefgh",
        ),
        (
            "digest",
            lambda: auth.RecordDigest(VALID_SHA256_HEX),
            lambda value: value.to_wire() == VALID_SHA256_HEX,
        ),
        (
            "reference",
            lambda: _make_record_ref(auth.RecordFamily.AUTHORITY_EPOCH),
            lambda value: auth.to_dict_fields(value)["record_family"] == "authority_epoch",
        ),
        (
            "cas-expectation",
            lambda: auth.CasExpectation(**_valid_cas_kwargs()),
            lambda value: auth.to_dict_fields(value)["expected_journal_lock_state"]
            == "unlocked",
        ),
        (
            "limitation",
            lambda: auth.Limitations(entries=("gap",)),
            lambda value: value.to_wire() == ["gap"],
        ),
        (
            "authority-disclosure",
            lambda: auth.AuthorityDisclosure(
                authority_role=auth.AuthorityRole.EVIDENCE, disclosure_text="evidence only"
            ),
            lambda value: value.is_authoritative is False,
        ),
        (
            "envelope",
            lambda: _make_envelope(),
            lambda value: auth.to_dict_fields(value)["created_at"] == "2026-07-17T10:00:00Z",
        ),
        (
            "timestamp",
            lambda: auth.Timestamp("2026-07-17T10:00:00Z"),
            lambda value: value.to_wire() == "2026-07-17T10:00:00Z",
        ),
    ],
)
def test_adversarial_round_trip_matrix(label, build, expected_wire_check):
    value = build()
    assert expected_wire_check(value), f"round-trip check failed for {label}"


# ---------------------------------------------------------------------------
# 17. Packaging / installed-wheel isolation (bounded, not a full rebuild
#     matrix -- see docs for the fuller packaging verification narrative)
# ---------------------------------------------------------------------------


def test_authority_package_files_present_on_disk_for_packaging():
    # Narrowed by Phase 136AB: `authority_core.py` (Group 2) is now a
    # legitimate, authorized module. Narrowed further by Phase 136AD:
    # `request_readiness.py` (Group 3) is now authorized too. Narrowed
    # further by Phase 136AF: `authorization_candidate.py` (Group 4) is now
    # authorized too -- every other later-group module name remains absent
    # and unauthorized.
    expected_modules = {
        "__init__.py",
        "cas_expectation.py",
        "digest.py",
        "enums.py",
        "envelope.py",
        "errors.py",
        "extensions.py",
        "identity.py",
        "immutable.py",
        "limitations.py",
        "opaque.py",
        "references.py",
        "sentinels.py",
        "serialization.py",
        "authority_core.py",
        "authorization_candidate.py",
        "request_readiness.py",
    }
    actual_modules = {
        p.name for p in AUTHORITY_PACKAGE_DIR.glob("*.py") if not p.name.startswith("test_")
    }
    assert actual_modules == expected_modules


def test_pyproject_declares_zero_new_dependency():
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "jsonschema" in pyproject_text
    for forbidden_dep in ("pydantic", "attrs>=", "attrs ==", "cattrs"):
        assert forbidden_dep not in pyproject_text
