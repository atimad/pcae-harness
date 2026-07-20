"""Phase 136Z: Stage 3 Typed Authority Model Shared Core Implementation
(Typed Model Implementation Group 1).

Focused tests for the new ``src/pcae/cltr/authority/`` package: the
``ABSENT`` sentinel, ``OpaqueJsonValue``, recursive immutable JSON
containers, ``ExtensionMapping``, the shared wire enums, identifier/digest/
reference wrapper types, ``CasExpectation``, ``Limitations``/
``AuthorityDisclosure``, ``RecordEnvelope``/``Timestamp``, the shared
serialization primitives, the typed-model error hierarchy, and the
no-authority/no-side-effect/runtime-isolation/packaging proofs.

This module implements only Typed Model Implementation Group 1 (shared
core). No record-family model (``AuthorityEpoch``, ``AuthorityState``,
``CutoverRequest``, ``ReadinessPackage``, ``HumanAuthorization``,
``CutoverCandidate``, ``Certification``, ``PublicationAttempt``,
``PublicationEvidence``, ``ConcurrencyConflict``, ``RecoveryJournalEntry``,
``NotificationAuthorityBinding``, ``MarkerAuthorityBinding``,
``FinalizationReceiptAuthorityBinding``, ``CompatibilityState``,
``QuarantineRecord``) is implemented or exercised here -- those belong to
future, separately governed implementation groups.

Narrowed by Phase 136AP: ``FinalizationReceiptAuthorityBinding`` (Group 9)
is now an authorized, legitimately-implemented record-family model; see
``authorized_groups_2_through_9`` below.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import os
import socket
import subprocess
import sys
import venv
from pathlib import Path
from types import MappingProxyType

import pytest

from pcae.cltr import authority as auth

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"

# Every production-runtime-relevant module directory that must not import
# pcae.cltr.authority (Sec.22 of the 136Y plan).
PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "cltr",  # excluding cltr/authority itself, filtered below
    REPO_ROOT / "src" / "pcae" / "runtime",
)

FORBIDDEN_AUTHORITY_SYMBOLS = (
    "resolve_authority",
    "current_authority",
    "activate_epoch",
    "demote_legacy",
    "retire_legacy",
    "authorize_cutover",
    "evaluate_readiness",
    "certify_candidate",
    "publish",
    "recover",
    "quarantine",
    "release",
    "execute",
)

RECORD_FAMILY_MODEL_NAMES = (
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


def _sha256_hex(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


def _make_record_reference(family: auth.RecordFamily, *, seed: str = "a") -> auth.RecordReference:
    prefix = {
        auth.RecordFamily.AUTHORITY_EPOCH: "authepoch-",
        auth.RecordFamily.CUTOVER_REQUEST: "cutoverrq-",
        auth.RecordFamily.CERTIFICATION: "certifica-",
    }.get(family, "recordabc-")
    return auth.RecordReference(
        record_id=auth.RecordId(f"{prefix}{seed}1234567"[:40]),
        record_digest=auth.ReferencedRecordDigest(_sha256_hex(seed if seed.isalnum() else "a")),
        record_family=family,
    )


def _make_cas_expectation() -> auth.CasExpectation:
    return auth.CasExpectation(
        expected_authority_kind=auth.AuthorityKind.LEGACY,
        expected_authority_epoch=_make_record_reference(auth.RecordFamily.AUTHORITY_EPOCH, seed="1"),
        expected_authoritative_generation=auth.GenerationReference(
            generation_id=auth.GenerationId("generatio-abc12345"),
            generation_digest=auth.GenerationDigest(_sha256_hex("2")),
        ),
        expected_authority_pointer_digest=auth.PointerDigest(_sha256_hex("3")),
        expected_authority_state_digest=auth.Sha256Digest(_sha256_hex("4")),
        expected_migration_epoch=auth.MigrationEpochToken("epoch-1"),
        expected_source_lifecycle_state=auth.LegacyLifecycleStateWire.CERTIFIED,
        expected_compatibility_mode=auth.CompatibilityMode.LEGACY_AUTHORITATIVE,
        expected_journal_lock_state=auth.JournalLockState.UNLOCKED,
        expected_request_reference=_make_record_reference(auth.RecordFamily.CUTOVER_REQUEST, seed="5"),
        expected_certification_reference=_make_record_reference(auth.RecordFamily.CERTIFICATION, seed="6"),
    )


# ---------------------------------------------------------------------------
# 1. Package boundary / exact inventory
# ---------------------------------------------------------------------------


def test_136z_package_exists_as_sibling_of_cltr():
    assert AUTHORITY_PACKAGE_DIR.is_dir()
    assert (AUTHORITY_PACKAGE_DIR / "__init__.py").is_file()


def test_136z_exact_module_inventory():
    # Narrowed by Phase 136AB (Typed Model Implementation Group 2):
    # `authority_core.py` is now a legitimate, authorized module
    # (`AuthorityEpoch`, `AuthorityState` only). Narrowed further by Phase
    # 136AD (Typed Model Implementation Group 3): `request_readiness.py`
    # (`CutoverRequest`, `ReadinessPackage` only) is now authorized too.
    # Narrowed further by Phase 136AF (Typed Model Implementation Group 4):
    # `authorization_candidate.py` (`HumanAuthorization`, `CutoverCandidate`,
    # `Certification` only) is now authorized too. Narrowed further by
    # Phase 136AH (Typed Model Implementation Group 5): `publication.py`
    # (`PublicationAttempt`, `PublicationEvidence` only) is now authorized
    # too. Narrowed further by Phase 136AJ (Typed Model Implementation
    # Group 6): `recovery_concurrency.py` (`ConcurrencyConflict`,
    # `RecoveryJournalEntry` only) is now authorized too. Narrowed further
    # by Phase 136AL (Typed Model Implementation Group 7): `bindings.py`
    # (`NotificationAuthorityBinding` only) is now authorized too. Narrowed
    # further by Phase 136AR (Typed Model Implementation Group 10):
    # `compatibility_quarantine.py` (`CompatibilityState` only) is now
    # authorized too -- every other later-group module name remains absent
    # and unauthorized, matching the 136U-guard narrowing precedent this
    # same package's 136Z phase itself used.
    expected = {
        "__init__.py",
        "sentinels.py",
        "opaque.py",
        "immutable.py",
        "enums.py",
        "identity.py",
        "digest.py",
        "references.py",
        "cas_expectation.py",
        "limitations.py",
        "envelope.py",
        "extensions.py",
        "errors.py",
        "serialization.py",
        "authority_core.py",
        "request_readiness.py",
        "authorization_candidate.py",
        "publication.py",
        "recovery_concurrency.py",
        "bindings.py",
        "compatibility_quarantine.py",
    }
    actual = {p.name for p in AUTHORITY_PACKAGE_DIR.glob("*.py")}
    assert actual == expected


def test_136z_init_has_no_wildcard_export():
    text = (AUTHORITY_PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
    assert "import *" not in text


def test_136z_no_record_family_model_class_defined_anywhere_in_package():
    # Narrowed by Phase 136AB: `AuthorityEpoch`/`AuthorityState` (Group 2)
    # are now authorized, legitimately-implemented record-family models.
    # Narrowed further by Phase 136AD: `CutoverRequest`/`ReadinessPackage`
    # (Group 3) are now authorized too. Narrowed further by Phase 136AF:
    # `HumanAuthorization`/`CutoverCandidate`/`Certification` (Group 4) are
    # now authorized too. Narrowed further by Phase 136AH:
    # `PublicationAttempt`/`PublicationEvidence` (Group 5) are now
    # authorized too. Narrowed further by Phase 136AJ:
    # `ConcurrencyConflict`/`RecoveryJournalEntry` (Group 6) are now
    # authorized too. Narrowed further by Phase 136AL:
    # `NotificationAuthorityBinding` (Group 7) is now authorized too.
    # Narrowed further by Phase 136AN: `MarkerAuthorityBinding` (Group 8)
    # is now authorized too. Narrowed further by Phase 136AP:
    # `FinalizationReceiptAuthorityBinding` (Group 9) is now authorized
    # too. Narrowed further by Phase 136AR: `CompatibilityState`
    # (Group 10) is now authorized too. Narrowed further by Phase 136AT:
    # `QuarantineRecord` (Group 11) is now authorized too -- the sixteenth
    # and final Stage 3 record-family model. No later-group name remains
    # to forbid.
    authorized_groups_2_through_11 = {
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
    still_forbidden = tuple(
        name for name in RECORD_FAMILY_MODEL_NAMES if name not in authorized_groups_2_through_11
    )
    assert set(still_forbidden) == set(RECORD_FAMILY_MODEL_NAMES) - authorized_groups_2_through_11
    for py_file in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        tree = ast.parse(text)
        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        for forbidden in still_forbidden:
            assert forbidden not in class_names, f"{forbidden} defined in {py_file}"


def test_136z_no_import_cycle_all_modules_import_cleanly():
    # Importing the package already exercises every submodule transitively;
    # a genuine cycle would raise ImportError/AttributeError at import time.
    import importlib

    for py_file in sorted(AUTHORITY_PACKAGE_DIR.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        module_name = f"pcae.cltr.authority.{py_file.stem}"
        importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# 2. ABSENT sentinel
# ---------------------------------------------------------------------------


def test_136z_absent_is_absent():
    assert auth.ABSENT is auth.ABSENT


def test_136z_absent_is_not_none():
    assert auth.ABSENT is not None
    assert auth.ABSENT != None  # noqa: E711 -- explicit identity-adjacent equality check


def test_136z_absent_distinct_from_falsy_values():
    assert auth.ABSENT is not None
    assert auth.ABSENT != ""
    assert auth.ABSENT != {}
    assert auth.ABSENT != []
    assert auth.ABSENT != False  # noqa: E712
    assert auth.ABSENT != 0


def test_136z_absent_has_no_truth_value():
    with pytest.raises(TypeError):
        bool(auth.ABSENT)


def test_136z_absent_copy_and_deepcopy_preserve_identity():
    assert copy.copy(auth.ABSENT) is auth.ABSENT
    assert copy.deepcopy(auth.ABSENT) is auth.ABSENT


def test_136z_absent_pickle_round_trip_preserves_identity():
    import pickle

    assert pickle.loads(pickle.dumps(auth.ABSENT)) is auth.ABSENT


def test_136z_absent_repr_is_visually_distinct():
    assert repr(auth.ABSENT) == "<absent>"


def test_136z_absent_not_json_serializable():
    import json

    with pytest.raises(TypeError):
        json.dumps({"x": auth.ABSENT})


def test_136z_absent_omitted_from_serialization_explicit_null_preserved():
    ref = auth.RecordReference(
        record_id=auth.RecordId("cutoverrq-1234567"),
        record_digest=auth.ReferencedRecordDigest(_sha256_hex("1")),
        record_family=auth.RecordFamily.CUTOVER_REQUEST,
    )
    d_absent = auth.to_dict_fields(ref)
    assert "schema_id" not in d_absent

    ref_null = dataclasses.replace(ref, schema_id=None)
    d_null = auth.to_dict_fields(ref_null)
    assert d_null["schema_id"] is None


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
        -7,
        3.5,
        "",
        "hello éè \U0001F600",
        [],
        {},
        [1, 2, 3],
        {"a": 1, "b": [1, {"c": None}]},
        {"deep": {"nesting": {"goes": {"very": {"far": [1, 2, [3, 4, {"x": None}]]}}}}},
    ],
)
def test_136z_opaque_json_value_round_trips_every_json_primitive_shape(value):
    wrapped = auth.OpaqueJsonValue.from_json(value)
    assert wrapped.to_json() == value


def test_136z_opaque_json_value_rejects_set():
    with pytest.raises(auth.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json({1, 2, 3})


def test_136z_opaque_json_value_rejects_bytes():
    with pytest.raises(auth.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json(b"raw bytes")


def test_136z_opaque_json_value_rejects_arbitrary_object():
    class Thing:
        pass

    with pytest.raises(auth.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json(Thing())


def test_136z_opaque_json_value_rejects_function():
    with pytest.raises(auth.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json(lambda: None)


def test_136z_opaque_json_value_rejects_nan_and_infinity():
    with pytest.raises(auth.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json(float("nan"))
    with pytest.raises(auth.UnsupportedJsonValueError):
        auth.OpaqueJsonValue.from_json(float("inf"))


def test_136z_opaque_json_value_does_not_share_mutable_input_reference():
    source = {"a": [1, 2, 3]}
    wrapped = auth.OpaqueJsonValue.from_json(source)
    source["a"].append(4)
    assert wrapped.to_json() == {"a": [1, 2, 3]}


def test_136z_opaque_json_value_output_is_independent_mutable_copy():
    wrapped = auth.OpaqueJsonValue.from_json({"a": [1, 2]})
    out1 = wrapped.to_json()
    out1["a"].append(999)
    out2 = wrapped.to_json()
    assert out2 == {"a": [1, 2]}


def test_136z_opaque_json_value_equality_is_structural():
    a = auth.OpaqueJsonValue.from_json({"x": [1, 2]})
    b = auth.OpaqueJsonValue.from_json({"x": [1, 2]})
    c = auth.OpaqueJsonValue.from_json({"x": [1, 3]})
    assert a == b
    assert a != c


def test_136z_opaque_json_value_currently_constrained_shape_empty_object():
    # DEFERRED-136T-1 / DEFERRED-136V-1: current wire shape is `{}` only.
    wrapped = auth.OpaqueJsonValue.from_json({})
    assert wrapped.to_json() == {}


def test_136z_verify_round_trip_helper_passes_for_correct_round_trip():
    original = {"a": 1}
    wrapped = auth.OpaqueJsonValue.from_json(original)
    auth.verify_round_trip(original, wrapped)  # must not raise


def test_136z_verify_round_trip_helper_raises_on_mismatch():
    wrapped = auth.OpaqueJsonValue.from_json({"a": 1})
    with pytest.raises(auth.OpaqueValuePreservationError):
        auth.verify_round_trip({"a": 2}, wrapped)


# ---------------------------------------------------------------------------
# 4. Immutable JSON containers (via OpaqueJsonValue and ExtensionMapping)
# ---------------------------------------------------------------------------


def test_136z_frozen_array_is_tuple_not_list():
    from pcae.cltr.authority.immutable import freeze_json_value

    frozen = freeze_json_value([1, 2, [3, 4]])
    assert isinstance(frozen, tuple)
    assert isinstance(frozen[2], tuple)


def test_136z_frozen_object_is_mappingproxytype():
    from pcae.cltr.authority.immutable import freeze_json_value

    frozen = freeze_json_value({"a": {"b": 1}})
    assert isinstance(frozen, MappingProxyType)
    assert isinstance(frozen["a"], MappingProxyType)


@pytest.mark.parametrize("depth", [1, 2, 5, 10])
def test_136z_recursive_immutability_at_every_nesting_depth(depth):
    from pcae.cltr.authority.immutable import freeze_json_value

    value = "leaf"
    for _ in range(depth):
        value = {"nested": value}
    frozen = freeze_json_value(value)
    node = frozen
    for _ in range(depth):
        assert isinstance(node, MappingProxyType)
        with pytest.raises(TypeError):
            node["nested"] = "mutated"  # MappingProxyType forbids item assignment
        node = node["nested"]
    assert node == "leaf"


def test_136z_frozen_tuple_rejects_item_assignment():
    from pcae.cltr.authority.immutable import freeze_json_value

    frozen = freeze_json_value([1, 2, 3])
    with pytest.raises(TypeError):
        frozen[0] = 99  # tuples do not support item assignment


def test_136z_thaw_produces_independent_mutable_copy():
    from pcae.cltr.authority.immutable import freeze_json_value, thaw_json_value

    frozen = freeze_json_value({"a": [1, 2]})
    thawed = thaw_json_value(frozen)
    thawed["a"].append(3)
    assert thaw_json_value(frozen) == {"a": [1, 2]}


# ---------------------------------------------------------------------------
# 5. ExtensionMapping
# ---------------------------------------------------------------------------


def test_136z_extension_mapping_round_trips_populated_mapping():
    em = auth.ExtensionMapping.from_mapping({"foo": "bar", "n": [1, {"k": None}]})
    assert em.to_dict() == {"foo": "bar", "n": [1, {"k": None}]}


def test_136z_extension_mapping_round_trips_empty_mapping():
    em = auth.ExtensionMapping.from_mapping({})
    assert em.to_dict() == {}
    assert len(em) == 0


def test_136z_extension_mapping_preserves_key_order():
    em = auth.ExtensionMapping.from_mapping({"z": 1, "a": 2, "m": 3})
    assert list(em.keys()) == ["z", "a", "m"]


def test_136z_extension_mapping_rejects_canonical_field_collision():
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ExtensionMapping.from_mapping(
            {"record_id": "should-not-shadow"}, reserved_keys={"record_id", "record_digest"}
        )


def test_136z_extension_mapping_enforces_max_properties():
    too_many = {f"k{i}": i for i in range(33)}
    with pytest.raises(auth.TypedModelConstructionError):
        auth.ExtensionMapping.from_mapping(too_many)


def test_136z_extension_mapping_at_max_properties_boundary_is_accepted():
    exactly_max = {f"k{i}": i for i in range(32)}
    em = auth.ExtensionMapping.from_mapping(exactly_max)
    assert len(em) == 32


def test_136z_extension_mapping_does_not_share_mutable_input_reference():
    source = {"a": [1, 2]}
    em = auth.ExtensionMapping.from_mapping(source)
    source["a"].append(3)
    assert em.to_dict() == {"a": [1, 2]}


def test_136z_extension_mapping_is_not_hashable():
    em = auth.ExtensionMapping.from_mapping({"a": 1})
    with pytest.raises(TypeError):
        hash(em)


def test_136z_extension_mapping_never_promotes_key_to_attribute():
    em = auth.ExtensionMapping.from_mapping({"record_id": "not-a-real-record-id"})
    assert not hasattr(em, "record_id")
    assert em["record_id"] == "not-a-real-record-id"


# ---------------------------------------------------------------------------
# 6. Enums -- fail-closed strictness
# ---------------------------------------------------------------------------


ENUM_MEMBER_CASES = [
    (auth.AuthorityKind, "legacy"),
    (auth.AuthorityKind, "cltr"),
    (auth.AuthorityRole, "authoritative"),
    (auth.AuthorityRole, "derivative"),
    (auth.AuthorityRole, "operational"),
    (auth.AuthorityRole, "evidence"),
    (auth.AuthorityRole, "compatibility"),
    (auth.AuthorityRole, "historical"),
    (auth.AuthorityRole, "quarantined"),
    (auth.MigrationStage, "shadow"),
    (auth.MigrationStage, "legacy_retired"),
    (auth.GenerationRole, "rehearsal_candidate"),
    (auth.GenerationRole, "quarantined_generation"),
    (auth.PublicationState, "not_requested"),
    (auth.PublicationState, "quarantined"),
    (auth.RecoveryState, "none_required"),
    (auth.RecoveryState, "terminal_unrecoverable"),
    (auth.CompatibilityMode, "legacy_authoritative"),
    (auth.CompatibilityMode, "legacy_retired"),
    (auth.RecordFamily, "authority_epoch"),
    (auth.RecordFamily, "compatibility_state"),
    (auth.ReasonCode, "invalid_schema"),
    (auth.ReasonCode, "receipt_conflict"),
    (auth.LegacyLifecycleStateWire, "PROPOSED"),
    (auth.LegacyLifecycleStateWire, "FAILED_POST_CERT"),
    (auth.JournalLockState, "unlocked"),
    (auth.JournalLockState, "locked"),
]


@pytest.mark.parametrize("enum_cls,member_value", ENUM_MEMBER_CASES)
def test_136z_enum_member_constructs_and_serializes_exact_wire_value(enum_cls, member_value):
    member = enum_cls(member_value)
    assert member.value == member_value


@pytest.mark.parametrize(
    "enum_cls", [auth.AuthorityKind, auth.AuthorityRole, auth.MigrationStage, auth.RecordFamily, auth.ReasonCode]
)
def test_136z_enum_rejects_unknown_value(enum_cls):
    with pytest.raises(ValueError):
        enum_cls("totally-unknown-value")


def test_136z_enum_rejects_case_mismatch():
    with pytest.raises(ValueError):
        auth.AuthorityKind("Legacy")
    with pytest.raises(ValueError):
        auth.AuthorityKind("LEGACY")


def test_136z_enum_does_not_trim_whitespace():
    with pytest.raises(ValueError):
        auth.AuthorityKind(" legacy")
    with pytest.raises(ValueError):
        auth.AuthorityKind("legacy ")


def test_136z_authority_role_stage3_and_legacy_are_distinct_types():
    from pcae.cltr.enums import AuthorityRole as LegacyAuthorityRole

    assert auth.AuthorityRole is not LegacyAuthorityRole
    # Stage-3 companion vocabulary values are disjoint from the legacy
    # single-letter S/R/D/E/V code vocabulary.
    legacy_values = {member.value for member in LegacyAuthorityRole}
    stage3_values = {member.value for member in auth.AuthorityRole}
    assert legacy_values.isdisjoint(stage3_values)


def test_136z_serialize_value_emits_plain_wire_string_not_enum_repr():
    serialized = auth.serialize_value(auth.AuthorityKind.LEGACY)
    assert serialized == "legacy"
    assert type(serialized) is str


# ---------------------------------------------------------------------------
# 7. Identifiers
# ---------------------------------------------------------------------------


def test_136z_record_id_accepts_well_formed_value():
    rid = auth.RecordId("authepoch-abc12345")
    assert str(rid) == "authepoch-abc12345"


@pytest.mark.parametrize(
    "bad_value",
    ["", "TOO-SHORT", "Has-Upper-Case", "has spaces here", "has/slash", "has\\backslash", "1starts-with-digit"],
)
def test_136z_record_id_rejects_malformed_value(bad_value):
    with pytest.raises(auth.InvalidIdentifierError):
        auth.RecordId(bad_value)


def test_136z_generation_id_and_record_id_are_distinct_types():
    assert auth.GenerationId is not auth.RecordId
    gid = auth.GenerationId("generatio-abc12345")
    rid = auth.RecordId("generatio-abc12345")
    assert gid != rid  # distinct dataclass types are never equal


def test_136z_migration_epoch_token_rejects_double_dot_traversal():
    with pytest.raises(auth.InvalidIdentifierError):
        auth.MigrationEpochToken("epoch..traversal")


def test_136z_migration_epoch_token_accepts_well_formed_value():
    token = auth.MigrationEpochToken("epoch-1.dev")
    assert str(token) == "epoch-1.dev"


def test_136z_phase_identity_boundary_lengths():
    auth.PhaseIdentity("A")  # 1 char, minimum
    auth.PhaseIdentity("136Z" * 4)  # 16 chars, maximum
    with pytest.raises(auth.InvalidIdentifierError):
        auth.PhaseIdentity("136Z" * 4 + "X")  # 17 chars, over maximum


def test_136z_transition_id_requires_trans_prefix():
    auth.TransitionId("trans-abcdefgh")
    with pytest.raises(auth.InvalidIdentifierError):
        auth.TransitionId("notrans-abcdefgh")


def test_136z_principal_identifier_accepts_email_shaped_value():
    principal = auth.PrincipalIdentifier("operator@example.com")
    assert str(principal) == "operator@example.com"


def test_136z_identifier_wrapper_never_performs_lookup_or_network(monkeypatch):
    def _forbidden_socket(*args, **kwargs):
        raise AssertionError("socket.socket must never be called during identifier construction")

    monkeypatch.setattr(socket, "socket", _forbidden_socket)
    auth.RecordId("authepoch-abc12345")


# ---------------------------------------------------------------------------
# 8. Digests
# ---------------------------------------------------------------------------


DIGEST_TYPES = [
    auth.Sha256Digest,
    auth.RecordDigest,
    auth.ReferencedRecordDigest,
    auth.GenerationDigest,
    auth.PointerDigest,
    auth.JournalEntryDigest,
]


@pytest.mark.parametrize("digest_cls", DIGEST_TYPES)
def test_136z_digest_wrapper_stores_exact_well_formed_value(digest_cls):
    value = _sha256_hex("a")
    digest = digest_cls(value)
    assert str(digest) == value


@pytest.mark.parametrize("digest_cls", DIGEST_TYPES)
@pytest.mark.parametrize(
    "bad_value",
    ["", "a" * 63, "a" * 65, "A" * 64, "g" * 64, "not-hex-at-all-000000000000000000000000000000000000000000000"],
)
def test_136z_digest_wrapper_rejects_malformed_value(digest_cls, bad_value):
    with pytest.raises(auth.InvalidDigestError):
        digest_cls(bad_value)


def test_136z_digest_types_are_distinct_even_with_identical_shape():
    value = _sha256_hex("a")
    assert auth.RecordDigest(value) != auth.GenerationDigest(value)


def test_136z_digest_never_computed_or_corrected_automatically():
    # Construction is pure storage: supplying an arbitrary (but well-formed)
    # digest never triggers a recompute-and-replace.
    digest = auth.RecordDigest(_sha256_hex("f"))
    assert digest.value == _sha256_hex("f")


# ---------------------------------------------------------------------------
# 9. References
# ---------------------------------------------------------------------------


def test_136z_record_reference_stores_id_digest_family_exactly():
    ref = _make_record_reference(auth.RecordFamily.CUTOVER_REQUEST, seed="5")
    assert ref.record_family is auth.RecordFamily.CUTOVER_REQUEST
    assert ref.schema_id is auth.ABSENT
    assert ref.schema_version is auth.ABSENT


def test_136z_record_reference_never_dereferences():
    ref = _make_record_reference(auth.RecordFamily.AUTHORITY_EPOCH, seed="1")
    # No method on RecordReference performs any lookup; the type has no
    # attribute that would fetch, dereference, or existence-check anything.
    forbidden_attrs = ("resolve", "fetch", "exists", "dereference", "lookup")
    for attr in forbidden_attrs:
        assert not hasattr(ref, attr)


def test_136z_require_family_accepts_matching_family():
    ref = _make_record_reference(auth.RecordFamily.CERTIFICATION, seed="6")
    result = auth.require_family(ref, auth.RecordFamily.CERTIFICATION)
    assert result is ref


def test_136z_require_family_fails_closed_on_mismatch():
    ref = _make_record_reference(auth.RecordFamily.CUTOVER_REQUEST, seed="5")
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.require_family(ref, auth.RecordFamily.CERTIFICATION)


def test_136z_epoch_reference_optional_digest_defaults_absent():
    epoch_ref = auth.EpochReference(migration_epoch=auth.MigrationEpochToken("epoch-1"))
    assert epoch_ref.epoch_digest is auth.ABSENT


def test_136z_epoch_reference_explicit_null_distinct_from_absent():
    epoch_ref = auth.EpochReference(migration_epoch=auth.MigrationEpochToken("epoch-1"), epoch_digest=None)
    assert epoch_ref.epoch_digest is None
    assert epoch_ref.epoch_digest is not auth.ABSENT


def test_136z_generation_reference_always_paired():
    gen_ref = auth.GenerationReference(
        generation_id=auth.GenerationId("generatio-abc12345"),
        generation_digest=auth.GenerationDigest(_sha256_hex("2")),
    )
    d = auth.to_dict_fields(gen_ref)
    assert set(d.keys()) == {"generation_id", "generation_digest"}


# ---------------------------------------------------------------------------
# 10. CasExpectation
# ---------------------------------------------------------------------------


def test_136z_cas_expectation_constructs_with_all_required_fields():
    cas = _make_cas_expectation()
    assert cas.expected_authority_kind is auth.AuthorityKind.LEGACY


def test_136z_cas_expectation_has_no_optional_fields():
    fields = dataclasses.fields(auth.CasExpectation)
    for f in fields:
        assert f.default is dataclasses.MISSING
        assert f.default_factory is dataclasses.MISSING  # type: ignore[comparison-overlap]


def test_136z_cas_expectation_rejects_wrong_family_authority_epoch():
    bad_ref = _make_record_reference(auth.RecordFamily.CUTOVER_REQUEST, seed="1")
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.CasExpectation(
            expected_authority_kind=auth.AuthorityKind.LEGACY,
            expected_authority_epoch=bad_ref,  # wrong family: should be authority_epoch
            expected_authoritative_generation=auth.GenerationReference(
                generation_id=auth.GenerationId("generatio-abc12345"),
                generation_digest=auth.GenerationDigest(_sha256_hex("2")),
            ),
            expected_authority_pointer_digest=auth.PointerDigest(_sha256_hex("3")),
            expected_authority_state_digest=auth.Sha256Digest(_sha256_hex("4")),
            expected_migration_epoch=auth.MigrationEpochToken("epoch-1"),
            expected_source_lifecycle_state=auth.LegacyLifecycleStateWire.CERTIFIED,
            expected_compatibility_mode=auth.CompatibilityMode.LEGACY_AUTHORITATIVE,
            expected_journal_lock_state=auth.JournalLockState.UNLOCKED,
            expected_request_reference=_make_record_reference(auth.RecordFamily.CUTOVER_REQUEST, seed="5"),
            expected_certification_reference=_make_record_reference(auth.RecordFamily.CERTIFICATION, seed="6"),
        )


def test_136z_cas_expectation_round_trips_through_serialization():
    cas = _make_cas_expectation()
    d = auth.to_dict_fields(cas)
    canonical = auth.to_canonical_bytes(d)
    assert isinstance(canonical, bytes)
    assert d["expected_authority_kind"] == "legacy"
    assert d["expected_journal_lock_state"] == "unlocked"


# ---------------------------------------------------------------------------
# 11. Limitations / AuthorityDisclosure
# ---------------------------------------------------------------------------


def test_136z_limitations_empty_is_permitted():
    lims = auth.Limitations()
    assert len(lims) == 0
    assert auth.serialize_value(lims) == []


def test_136z_limitations_serializes_as_plain_array_not_object():
    lims = auth.Limitations(("shape only", "no authority implied"))
    assert auth.serialize_value(lims) == ["shape only", "no authority implied"]


def test_136z_limitations_enforces_max_items():
    too_many = tuple(f"limitation {i}" for i in range(33))
    with pytest.raises(auth.TypedModelConstructionError):
        auth.Limitations(too_many)


def test_136z_limitations_rejects_control_characters():
    with pytest.raises(auth.TypedModelConstructionError):
        auth.Limitations(("bad\x00null-byte",))


def test_136z_limitations_rejects_empty_entry():
    with pytest.raises(auth.TypedModelConstructionError):
        auth.Limitations(("",))


def test_136z_authority_disclosure_is_authoritative_pinned_false():
    disclosure = auth.AuthorityDisclosure(
        authority_role=auth.AuthorityRole.DERIVATIVE, disclosure_text="Derived, non-authoritative view."
    )
    assert disclosure.is_authoritative is False
    d = auth.to_dict_fields(disclosure)
    assert d["is_authoritative"] is False


def test_136z_authority_disclosure_rejects_true_override():
    with pytest.raises(auth.TypedModelConstructionError):
        auth.AuthorityDisclosure(
            authority_role=auth.AuthorityRole.DERIVATIVE,
            disclosure_text="attempted override",
            is_authoritative=True,
        )


def test_136z_authority_disclosure_rejects_multiline_text():
    with pytest.raises(auth.TypedModelConstructionError):
        auth.AuthorityDisclosure(
            authority_role=auth.AuthorityRole.DERIVATIVE, disclosure_text="line one\nline two"
        )


# ---------------------------------------------------------------------------
# 12. Envelope / Timestamp
# ---------------------------------------------------------------------------


TIMESTAMP_FIXTURES = [
    "2026-07-17T14:52:12Z",
    "2026-07-17T14:52:12.5Z",
    "2026-07-17T14:52:12.123456Z",
    "2026-01-01T00:00:00Z",
]


@pytest.mark.parametrize("wire", TIMESTAMP_FIXTURES)
def test_136z_timestamp_preserves_exact_wire_string(wire):
    ts = auth.Timestamp(wire)
    assert ts.wire == wire
    assert auth.serialize_value(ts) == wire


@pytest.mark.parametrize(
    "bad_wire",
    [
        "2026-07-17T14:52:12+00:00",  # numeric offset, not 'Z'
        "2026-07-17 14:52:12Z",  # space instead of 'T'
        "2026-07-17T14:52:12.1234567Z",  # 7 fractional digits, over max
        "2026-07-17T14:52:12",  # missing 'Z'
        "not-a-timestamp",
    ],
)
def test_136z_timestamp_rejects_malformed_wire_string(bad_wire):
    with pytest.raises(auth.InvalidTimestampError):
        auth.Timestamp(bad_wire)


def test_136z_timestamp_derived_datetime_never_replaces_wire_string():
    ts = auth.Timestamp("2026-07-17T14:52:12Z")
    dt = ts.to_datetime()
    assert dt.year == 2026
    # Serialization always emits the original string, never a re-formatted datetime.
    assert auth.serialize_value(ts) == "2026-07-17T14:52:12Z"


def test_136z_record_envelope_round_trips_all_seven_fields():
    env = auth.RecordEnvelope(
        schema_id="cltr_cutover/records/authority_epoch.schema.json",
        schema_version=auth.SchemaVersionString("1.0"),
        record_type="authority_epoch",
        record_id=auth.RecordId("authepoch-abc12345"),
        record_digest=auth.RecordDigest(_sha256_hex("c")),
        created_at=auth.Timestamp("2026-07-17T14:52:12Z"),
    )
    d = auth.to_dict_fields(env)
    assert d == {
        "schema_id": "cltr_cutover/records/authority_epoch.schema.json",
        "schema_version": "1.0",
        "record_type": "authority_epoch",
        "record_id": "authepoch-abc12345",
        "record_digest": _sha256_hex("c"),
        "created_at": "2026-07-17T14:52:12Z",
        "contract_version": "1.0",
    }


def test_136z_record_envelope_contract_version_is_pinned_const():
    with pytest.raises(auth.TypedModelConstructionError):
        auth.RecordEnvelope(
            schema_id="x",
            schema_version=auth.SchemaVersionString("1.0"),
            record_type="authority_epoch",
            record_id=auth.RecordId("authepoch-abc12345"),
            record_digest=auth.RecordDigest(_sha256_hex("c")),
            created_at=auth.Timestamp("2026-07-17T14:52:12Z"),
            contract_version="2.0",
        )


def test_136z_schema_version_string_rejects_malformed_value():
    with pytest.raises(auth.TypedModelConstructionError):
        auth.SchemaVersionString("v1.0")


# ---------------------------------------------------------------------------
# 13. Immutability and equality
# ---------------------------------------------------------------------------


def test_136z_dataclasses_are_frozen_top_level():
    ref = _make_record_reference(auth.RecordFamily.CUTOVER_REQUEST, seed="5")
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.record_family = auth.RecordFamily.CERTIFICATION  # type: ignore[misc]


def test_136z_equality_is_structural_not_identity():
    a = auth.RecordId("authepoch-abc12345")
    b = auth.RecordId("authepoch-abc12345")
    assert a is not b
    assert a == b


def test_136z_extension_bearing_equality_considers_extensions():
    em1 = auth.ExtensionMapping.from_mapping({"a": 1})
    em2 = auth.ExtensionMapping.from_mapping({"a": 1})
    em3 = auth.ExtensionMapping.from_mapping({"a": 2})
    assert em1 == em2
    assert em1 != em3


def test_136z_dataclasses_without_extensions_are_hashable():
    a = auth.RecordId("authepoch-abc12345")
    assert hash(a) == hash(auth.RecordId("authepoch-abc12345"))


# ---------------------------------------------------------------------------
# 14. Serialization pipeline
# ---------------------------------------------------------------------------


def test_136z_field_from_payload_distinguishes_absent_from_null():
    payload = {"present": "value", "explicit_null": None}
    assert auth.field_from_payload(payload, "present") == "value"
    assert auth.field_from_payload(payload, "explicit_null") is None
    assert auth.field_from_payload(payload, "missing_key") is auth.ABSENT


def test_136z_to_dict_fields_omits_absent_and_keeps_null():
    ref_absent = auth.RecordReference(
        record_id=auth.RecordId("cutoverrq-1234567"),
        record_digest=auth.ReferencedRecordDigest(_sha256_hex("1")),
        record_family=auth.RecordFamily.CUTOVER_REQUEST,
    )
    ref_null = dataclasses.replace(ref_absent, schema_id=None, schema_version=None)
    d_absent = auth.to_dict_fields(ref_absent)
    d_null = auth.to_dict_fields(ref_null)
    assert "schema_id" not in d_absent
    assert d_null["schema_id"] is None
    assert d_null["schema_version"] is None


def test_136z_serialize_value_rejects_absent_directly():
    with pytest.raises(auth.SerializationError):
        auth.serialize_value(auth.ABSENT)


def test_136z_serialize_value_rejects_unsupported_python_type():
    class Thing:
        pass

    with pytest.raises(auth.SerializationError):
        auth.serialize_value(Thing())


def test_136z_to_canonical_bytes_reuses_existing_canonicalization_module():
    import pcae.cltr.authority.serialization as serialization_module
    import pcae.cltr.canonicalization as canonicalization_module

    assert serialization_module.to_canonical_bytes is not canonicalization_module.canonicalize_dict
    # Confirm delegation (not reimplementation) by identical output for identical input.
    payload = {"a": 1, "b": [1, 2, 3]}
    assert serialization_module.to_canonical_bytes(payload) == canonicalization_module.canonicalize_dict(payload)


def test_136z_no_coercion_boolean_string_not_accepted_by_enum():
    with pytest.raises(ValueError):
        auth.AuthorityKind(True)  # type: ignore[arg-type]


def test_136z_no_coercion_digest_int_not_accepted():
    with pytest.raises(auth.InvalidDigestError):
        auth.RecordDigest(123456)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 15. Error hierarchy
# ---------------------------------------------------------------------------


ERROR_HIERARCHY_CASES = [
    (auth.TypedModelConstructionError, auth.TypedModelError),
    (auth.InvalidIdentifierError, auth.TypedModelConstructionError),
    (auth.InvalidDigestError, auth.TypedModelConstructionError),
    (auth.InvalidReferenceError, auth.TypedModelConstructionError),
    (auth.WrongFamilyReferenceError, auth.InvalidReferenceError),
    (auth.InvalidTimestampError, auth.TypedModelConstructionError),
    (auth.UnsupportedJsonValueError, auth.TypedModelConstructionError),
    (auth.AbsentNullMismatchError, auth.TypedModelConstructionError),
    (auth.UnsupportedSchemaVersionError, auth.TypedModelError),
    (auth.UnknownModelFamilyError, auth.TypedModelError),
    (auth.OpaqueValuePreservationError, auth.TypedModelError),
    (auth.SerializationError, auth.TypedModelError),
    (auth.TypedModelInternalInvariantError, auth.TypedModelError),
    (auth.RoundTripMismatchError, auth.TypedModelError),
]


@pytest.mark.parametrize("child,parent", ERROR_HIERARCHY_CASES)
def test_136z_error_hierarchy_subclass_relationship(child, parent):
    assert issubclass(child, parent)


def test_136z_all_typed_model_errors_are_exceptions():
    assert issubclass(auth.TypedModelError, Exception)


def test_136z_error_message_never_echoes_full_extension_contents():
    # Constructing ExtensionMapping error paths never embed the full
    # colliding mapping contents in the exception text.
    try:
        auth.ExtensionMapping.from_mapping(
            {"secret-looking-key": "super-secret-value-should-not-leak"},
            reserved_keys={"secret-looking-key"},
        )
    except auth.TypedModelConstructionError as exc:
        assert "super-secret-value-should-not-leak" not in str(exc)
    else:
        pytest.fail("expected TypedModelConstructionError")


# ---------------------------------------------------------------------------
# 16. Runtime isolation -- no production module imports pcae.cltr.authority
# ---------------------------------------------------------------------------


def _iter_python_files(root: Path):
    if not root.exists():
        return
    for path in root.rglob("*.py"):
        if "authority" in path.relative_to(REPO_ROOT).parts:
            continue
        if path.name.startswith("test_"):
            continue
        yield path


# Phase 137K: the sole authorized production Typed Authority Model consumer
# is permitted to import pcae.cltr.authority (TAMPC-001 v1.0,
# docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md).
_AUTHORIZED_137K_IMPORTERS = frozenset({"authority_inspection.py", "authority_inspect.py"})


def test_136z_no_production_module_imports_authority_package():
    offending = []
    for scan_root in PRODUCTION_SCAN_ROOTS:
        for py_file in _iter_python_files(scan_root):
            if py_file.name in _AUTHORIZED_137K_IMPORTERS:
                continue
            text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("pcae.cltr.authority"):
                            offending.append(str(py_file))
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("pcae.cltr.authority"):
                        offending.append(str(py_file))
    assert offending == []


def test_136z_no_production_module_string_references_authority_import():
    # Defense in depth beyond the AST check: no lazy/dynamic
    # `importlib.import_module("pcae.cltr.authority...")`-style string
    # reference exists in production source either.
    offending = []
    for scan_root in PRODUCTION_SCAN_ROOTS:
        for py_file in _iter_python_files(scan_root):
            if py_file.name in _AUTHORIZED_137K_IMPORTERS:
                continue
            text = py_file.read_text(encoding="utf-8")
            if "pcae.cltr.authority" in text or "pcae/cltr/authority" in text:
                offending.append(str(py_file))
    assert offending == []


def test_136z_no_authority_module_imports_any_production_lifecycle_module():
    forbidden_prefixes = ("pcae.commands", "pcae.core.notifications", "pcae.core.phase_reports")
    for py_file in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(py_file))
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
            if module:
                for forbidden in forbidden_prefixes:
                    assert not module.startswith(forbidden), f"{py_file} imports {module}"


# ---------------------------------------------------------------------------
# 17. No-authority proof
# ---------------------------------------------------------------------------


def test_136z_no_authority_selection_symbols_exported():
    for symbol in FORBIDDEN_AUTHORITY_SYMBOLS:
        assert symbol not in auth.__all__, f"{symbol} must not be exported"
        assert not hasattr(auth, symbol), f"{symbol} must not exist on the package"


def test_136z_no_authority_selection_symbols_defined_in_source():
    for py_file in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(py_file))
        defined_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined_names.add(node.name)
        for forbidden in FORBIDDEN_AUTHORITY_SYMBOLS:
            assert forbidden not in defined_names, f"{forbidden} defined in {py_file}"


def test_136z_authority_disclosure_is_authoritative_always_false_never_settable_true():
    disclosure = auth.AuthorityDisclosure(
        authority_role=auth.AuthorityRole.AUTHORITATIVE, disclosure_text="claims authoritative role only"
    )
    # Even when authority_role itself is "authoritative", is_authoritative
    # remains pinned False -- the shared core never computes or grants truth.
    assert disclosure.is_authoritative is False


# ---------------------------------------------------------------------------
# 18. No-side-effect proof
# ---------------------------------------------------------------------------


def _build_every_fixture():
    """Exercise every shared-core component's construction and
    serialization path once, for use inside instrumented no-side-effect
    tests."""

    env = auth.RecordEnvelope(
        schema_id="x",
        schema_version=auth.SchemaVersionString("1.0"),
        record_type="authority_epoch",
        record_id=auth.RecordId("authepoch-abc12345"),
        record_digest=auth.RecordDigest(_sha256_hex("c")),
        created_at=auth.Timestamp("2026-07-17T14:52:12Z"),
    )
    cas = _make_cas_expectation()
    lims = auth.Limitations(("informational only",))
    disclosure = auth.AuthorityDisclosure(
        authority_role=auth.AuthorityRole.DERIVATIVE, disclosure_text="derived view"
    )
    opaque = auth.OpaqueJsonValue.from_json({})
    ext = auth.ExtensionMapping.from_mapping({"k": "v"})
    for value in (env, cas, lims, disclosure, opaque, ext):
        d = auth.serialize_value(value) if not dataclasses.is_dataclass(value) else auth.to_dict_fields(value)
        auth.to_canonical_bytes(d if isinstance(d, dict) else {"value": d})


def test_136z_no_network_during_construction_or_serialization(monkeypatch):
    def _forbidden(*args, **kwargs):
        raise AssertionError("socket must never be used by shared-core construction/serialization")

    monkeypatch.setattr(socket, "socket", _forbidden)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    _build_every_fixture()


def test_136z_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _forbidden(*args, **kwargs):
        raise AssertionError("subprocess must never be used by shared-core construction/serialization")

    monkeypatch.setattr(subprocess, "run", _forbidden)
    monkeypatch.setattr(subprocess, "Popen", _forbidden)
    _build_every_fixture()


def test_136z_no_filesystem_write_during_construction_or_serialization(monkeypatch, tmp_path):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"filesystem write attempted: open({file!r}, {mode!r})")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    _build_every_fixture()


def test_136z_no_environment_variable_lookup_during_construction():
    # Globally replacing os.environ (even via monkeypatch) is unsafe here:
    # pytest's own runtime (terminal width, color detection) reads it mid-test.
    # Environment-variable isolation is instead proven statically, below
    # (`test_136z_no_environ_reference_in_source`), by confirming no
    # `os.environ`/`os.getenv` token exists anywhere in the package source.
    _build_every_fixture()


def test_136z_no_subprocess_or_shell_reference_in_source():
    # Deliberately narrow tokens (e.g. "import subprocess", not the bare
    # word "subprocess") so this doesn't false-positive on this module's
    # own descriptive docstring prose (which mentions "no subprocess
    # execution" as a disclosed guarantee).
    for py_file in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for token in (
            "import subprocess",
            "os.system(",
            "shell=True",
            "socket.socket(",
            "urllib.request",
        ):
            assert token not in text, f"{token!r} found in {py_file}"


def test_136z_no_environ_reference_in_source():
    for py_file in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert "os.environ" not in text
        assert "os.getenv" not in text


# ---------------------------------------------------------------------------
# 19. Schema alignment -- shared component inventory sanity
# ---------------------------------------------------------------------------


def test_136z_seven_shared_schema_files_still_present_unchanged():
    shared_dir = REPO_ROOT / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "shared"
    expected = {
        "digest.schema.json",
        "enums.schema.json",
        "envelope.schema.json",
        "failures.schema.json",
        "identity.schema.json",
        "limitations.schema.json",
        "references.schema.json",
    }
    actual = {p.name for p in shared_dir.glob("*.schema.json")}
    assert actual == expected


def test_136z_no_record_family_schema_touched_by_this_phase():
    records_dir = REPO_ROOT / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "records"
    assert len(list(records_dir.glob("*.schema.json"))) == 16


# ---------------------------------------------------------------------------
# 20. Packaging -- wheel / sdist inclusion, installed-wheel smoke test
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136z_wheel_contains_authority_shared_core_no_record_family_module(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()

    expected_modules = (
        "sentinels",
        "opaque",
        "immutable",
        "enums",
        "identity",
        "digest",
        "references",
        "cas_expectation",
        "limitations",
        "envelope",
        "extensions",
        "errors",
        "serialization",
        "__init__",
    )
    for module in expected_modules:
        path = f"pcae/cltr/authority/{module}.py"
        assert path in names, f"{path} missing from wheel; sample: {names[:20]}"

    # Narrowed by Phase 136AB: `authority_core` (Group 2) is now
    # legitimately included in the wheel; every later-group module remains
    # forbidden by this same guard, unchanged.
    assert "pcae/cltr/authority/authority_core.py" in names
    forbidden_modules = ("request_readiness", "bindings", "compatibility_quarantine")
    for module in forbidden_modules:
        path = f"pcae/cltr/authority/{module}.py"
        assert path not in names


@pytest.mark.slow
def test_136z_sdist_includes_authority_shared_core(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(sdists) == 1

    import tarfile

    with tarfile.open(sdists[0]) as archive:
        names = archive.getnames()
    assert any(name.endswith("pcae/cltr/authority/__init__.py") for name in names)
    assert any(name.endswith("pcae/cltr/authority/sentinels.py") for name in names)


@pytest.mark.slow
def test_136z_installed_wheel_constructs_shared_core_fixtures_outside_repository(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv136z"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    venv_python = venv_dir / "bin" / "python"
    assert venv_python.exists()

    install = subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheels[0]), "jsonschema>=4.18,<5"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr

    outside_cwd = tmp_path / "elsewhere"
    outside_cwd.mkdir()
    probe_script = (
        "from pcae.cltr import authority as auth\n"
        "rid = auth.RecordId('authepoch-abc12345')\n"
        "digest = auth.RecordDigest('a' * 64)\n"
        "ts = auth.Timestamp('2026-07-17T14:52:12Z')\n"
        "env = auth.RecordEnvelope(\n"
        "    schema_id='x', schema_version=auth.SchemaVersionString('1.0'),\n"
        "    record_type='authority_epoch', record_id=rid, record_digest=digest, created_at=ts,\n"
        ")\n"
        "d = auth.to_dict_fields(env)\n"
        "assert d['record_id'] == 'authepoch-abc12345'\n"
        "assert d['contract_version'] == '1.0'\n"
        "canon = auth.to_canonical_bytes(d)\n"
        "assert isinstance(canon, bytes)\n"
        "assert auth.ABSENT is auth.ABSENT\n"
        "try:\n"
        "    auth.AuthorityKind('Legacy')\n"
        "    raise SystemExit('should have raised')\n"
        "except ValueError:\n"
        "    pass\n"
        "print('OK')\n"
    )
    probe = subprocess.run(
        [str(venv_python), "-c", probe_script],
        cwd=str(outside_cwd),
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr
    assert "OK" in probe.stdout
