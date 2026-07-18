"""Phase 136AB: Stage 3 Typed Authority Model Authority Core Implementation
(Typed Model Implementation Group 2).

Focused tests for ``src/pcae/cltr/authority/authority_core.py``: the
``AuthorityEpoch`` and ``AuthorityState`` typed record models. Covers exact
field mapping, strict constructor behavior, absent-versus-null handling,
enum fidelity, identifier/digest/reference family preservation, conditional
branches, immutability, equality, serialization round-trip, schema
conformance, no-record-family-model-beyond-scope, no-authority-semantics,
no-side-effect, runtime-isolation, and packaging proofs.

This module implements only Typed Model Implementation Group 2
(``AuthorityEpoch``, ``AuthorityState``). No other record-family model
(``CutoverRequest``, ``ReadinessPackage``, ``HumanAuthorization``,
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
import socket
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import errors as auth_errors
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import build_offline_registry, validate_record_shape, OutcomeStatus

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"

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
    "is_current",
    "is_authoritative_now",
    "can_transition",
    "should_activate",
    "is_ready",
    "publish",
    "recover",
    "quarantine",
    "release",
    "execute",
)

# Narrowed by Phase 136AD: CutoverRequest/ReadinessPackage (Group 3) are now
# authorized, legitimately-implemented record-family models, so they are
# removed from this "still forbidden" list. Every other later-group name
# remains forbidden, unchanged.
LATER_GROUP_MODEL_NAMES = (
    # Narrowed by Phase 136AF: `HumanAuthorization`/`CutoverCandidate`/
    # `Certification` (Group 4) are now authorized, legitimately-implemented
    # record-family models -- removed from this still-forbidden list.
    # Narrowed further by Phase 136AH: `PublicationAttempt`/
    # `PublicationEvidence` (Group 5) are now authorized, legitimately-
    # implemented record-family models -- removed from this still-forbidden
    # list.
    "ConcurrencyConflict",
    "RecoveryJournalEntry",
    "NotificationAuthorityBinding",
    "MarkerAuthorityBinding",
    "FinalizationReceiptAuthorityBinding",
    "CompatibilityState",
    "QuarantineRecord",
)

AUTHORITY_EPOCH_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json"
AUTHORITY_STATE_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/authority_state.schema.json"


def _sha256_hex(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


# ---------------------------------------------------------------------------
# Wire fixtures (independently authored from the executable schema files,
# not copied from 136Y plan prose)
# ---------------------------------------------------------------------------


def _valid_epoch_wire(**overrides) -> dict:
    record = {
        "schema_id": AUTHORITY_EPOCH_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_epoch",
        "record_id": "authepoch-0000001",
        "record_digest": _sha256_hex("a"),
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "authority_kind": "legacy",
        "activation_state": "active",
        "predecessor_epoch": None,
        "generation_binding": {"generation_id": "gen-0000001", "generation_digest": _sha256_hex("b")},
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_state_wire(**overrides) -> dict:
    record = {
        "schema_id": AUTHORITY_STATE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_state",
        "record_id": "authstate-0000001",
        "record_digest": _sha256_hex("a"),
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "transition_id": "trans-00000001",
        "active_authority_epoch": {
            "record_id": "authepoch-0000001",
            "record_digest": _sha256_hex("a"),
            "record_family": "authority_epoch",
        },
        "authority_kind": "cltr",
        "authoritative_generation": {"generation_id": "gen-0000001", "generation_digest": _sha256_hex("b")},
        "publication_evidence_reference": {
            "record_id": "pubevidence-0000001",
            "record_digest": _sha256_hex("c"),
            "record_family": "publication_evidence",
        },
        "pointer_digest": _sha256_hex("d"),
        "verification_state": "verified",
        "compatibility_mode": "legacy_adapter",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "Resolved-authority claim; schema validity does not itself establish current authority.",
        },
    }
    record.update(overrides)
    return record


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _assert_schema_valid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


# ---------------------------------------------------------------------------
# 1. Inventory
# ---------------------------------------------------------------------------


def test_136ab_exactly_two_record_family_models_in_authority_core_module():
    tree = ast.parse(AUTHORITY_PACKAGE_DIR.joinpath("authority_core.py").read_text())
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "AuthorityEpoch" in class_names
    assert "AuthorityState" in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136ab_no_later_group_model_class_exists_anywhere_in_package():
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        for later_name in LATER_GROUP_MODEL_NAMES:
            assert later_name not in class_names, f"{later_name} found in {path}"


def test_136ab_expected_public_exports_present():
    for name in ("AuthorityEpoch", "AuthorityState", "ActivationState", "VerificationState", "Uncertainty"):
        assert hasattr(auth, name)
        assert name in auth.__all__


def test_136ab_authority_epoch_and_state_are_frozen_dataclasses():
    assert dataclasses.is_dataclass(auth.AuthorityEpoch)
    assert dataclasses.is_dataclass(auth.AuthorityState)
    assert auth.AuthorityEpoch.__dataclass_params__.frozen
    assert auth.AuthorityState.__dataclass_params__.frozen


# ---------------------------------------------------------------------------
# 2. AuthorityEpoch: construction / round trip
# ---------------------------------------------------------------------------


def test_136ab_authority_epoch_minimal_valid_construction_proposed(schema_registry):
    wire = _valid_epoch_wire(activation_state="proposed", generation_binding=None)
    del wire["generation_binding"]
    _assert_schema_valid(wire, AUTHORITY_EPOCH_SCHEMA_ID, schema_registry)
    model = auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")
    assert model.activation_state is auth.ActivationState.PROPOSED
    assert model.generation_binding is auth.ABSENT
    assert model.predecessor_epoch is None


def test_136ab_authority_epoch_maximal_valid_construction_active(schema_registry):
    wire = _valid_epoch_wire(
        predecessor_epoch={
            "record_id": "authepoch-0000000",
            "record_digest": _sha256_hex("e"),
            "record_family": "authority_epoch",
        },
        limitations=["a disclosed limitation"],
    )
    _assert_schema_valid(wire, AUTHORITY_EPOCH_SCHEMA_ID, schema_registry)
    model = auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")
    assert model.activation_state is auth.ActivationState.ACTIVE
    assert model.generation_binding.generation_id.value == "gen-0000001"
    assert model.predecessor_epoch.record_id.value == "authepoch-0000000"
    assert list(model.limitations) == ["a disclosed limitation"]


def test_136ab_authority_epoch_exact_field_mapping(schema_registry):
    wire = _valid_epoch_wire()
    model = auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")
    assert model.envelope.schema_id == wire["schema_id"]
    assert model.envelope.record_type == "authority_epoch"
    assert model.envelope.record_id.value == wire["record_id"]
    assert model.envelope.record_digest.value == wire["record_digest"]
    assert model.envelope.created_at.wire == wire["created_at"]
    assert model.migration_epoch.value == wire["migration_epoch"]
    assert model.authority_kind is auth.AuthorityKind.LEGACY
    assert model.authority_disclosure.authority_role is auth.AuthorityRole.DERIVATIVE


def test_136ab_authority_epoch_round_trip_all_variants(schema_registry):
    for wire in (
        _valid_epoch_wire(),
        _valid_epoch_wire(activation_state="proposed"),
        _valid_epoch_wire(activation_state="superseded"),
    ):
        wire = dict(wire)
        if wire.get("activation_state") == "proposed":
            wire.pop("generation_binding", None)
        _assert_schema_valid(wire, AUTHORITY_EPOCH_SCHEMA_ID, schema_registry)
        model = auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")
        round_tripped = auth.AuthorityEpoch.from_dict(model.to_dict(), schema_version="1.0")
        assert model == round_tripped
        assert model.to_dict() == round_tripped.to_dict()


def test_136ab_authority_epoch_predecessor_epoch_always_present_as_key_but_nullable(schema_registry):
    wire = _valid_epoch_wire()
    del wire["predecessor_epoch"]
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_epoch_unknown_field_rejected():
    wire = _valid_epoch_wire(unexpected_field="nope")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_epoch_unknown_enum_value_rejected():
    wire = _valid_epoch_wire(authority_kind="not_a_real_kind")
    with pytest.raises(ValueError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_epoch_unknown_activation_state_rejected():
    wire = _valid_epoch_wire(activation_state="not_a_real_state")
    with pytest.raises(ValueError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_epoch_unsupported_schema_version_rejected():
    wire = _valid_epoch_wire()
    with pytest.raises(auth_errors.UnsupportedSchemaVersionError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="9.9")


def test_136ab_authority_epoch_wrong_schema_id_rejected():
    wire = _valid_epoch_wire(schema_id="https://pcae.local/schemas/cltr_cutover/records/wrong.schema.json")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_epoch_wrong_record_type_rejected():
    wire = _valid_epoch_wire(record_type="authority_state")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 3. AuthorityEpoch: conditional branches (activation_state <-> generation_binding)
# ---------------------------------------------------------------------------


def test_136ab_authority_epoch_active_requires_generation_binding(schema_registry):
    wire = _valid_epoch_wire(activation_state="active")
    del wire["generation_binding"]
    schema_result = validate_record_shape(wire, schema_id=AUTHORITY_EPOCH_SCHEMA_ID, registry=schema_registry)
    assert schema_result.status is not OutcomeStatus.VALID
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_epoch_active_missing_generation_binding_rejected_by_typed_model_directly():
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityEpoch(
            envelope=auth.RecordEnvelope(
                schema_id=AUTHORITY_EPOCH_SCHEMA_ID,
                schema_version=auth.SchemaVersionString("1.0"),
                record_type="authority_epoch",
                record_id=auth.RecordId("authepoch-0000001"),
                record_digest=auth.RecordDigest(_sha256_hex("a")),
                created_at=auth.Timestamp("2026-07-17T12:00:00Z"),
            ),
            migration_epoch=auth.MigrationEpochToken("epoch-001"),
            authority_kind=auth.AuthorityKind.LEGACY,
            activation_state=auth.ActivationState.ACTIVE,
            predecessor_epoch=None,
            limitations=auth.Limitations(()),
            authority_disclosure=auth.AuthorityDisclosure(
                authority_role=auth.AuthorityRole.DERIVATIVE, disclosure_text="x"
            ),
        )


def test_136ab_authority_epoch_proposed_forbids_generation_binding():
    valid_binding = auth.GenerationReference(
        generation_id=auth.GenerationId("gen-0000001"),
        generation_digest=auth.GenerationDigest(_sha256_hex("b")),
    )
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityEpoch(
            envelope=auth.RecordEnvelope(
                schema_id=AUTHORITY_EPOCH_SCHEMA_ID,
                schema_version=auth.SchemaVersionString("1.0"),
                record_type="authority_epoch",
                record_id=auth.RecordId("authepoch-0000001"),
                record_digest=auth.RecordDigest(_sha256_hex("a")),
                created_at=auth.Timestamp("2026-07-17T12:00:00Z"),
            ),
            migration_epoch=auth.MigrationEpochToken("epoch-001"),
            authority_kind=auth.AuthorityKind.LEGACY,
            activation_state=auth.ActivationState.PROPOSED,
            predecessor_epoch=None,
            generation_binding=valid_binding,
            limitations=auth.Limitations(()),
            authority_disclosure=auth.AuthorityDisclosure(
                authority_role=auth.AuthorityRole.DERIVATIVE, disclosure_text="x"
            ),
        )


def test_136ab_authority_epoch_superseded_generation_binding_is_optional():
    wire_with = _valid_epoch_wire(activation_state="superseded")
    wire_without = _valid_epoch_wire(activation_state="superseded")
    del wire_without["generation_binding"]
    auth.AuthorityEpoch.from_dict(wire_with, schema_version="1.0")
    auth.AuthorityEpoch.from_dict(wire_without, schema_version="1.0")


def test_136ab_authority_epoch_forbids_authoritative_role():
    wire = _valid_epoch_wire(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        }
    )
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_epoch_predecessor_epoch_wrong_family_rejected():
    wire = _valid_epoch_wire(
        predecessor_epoch={
            "record_id": "authstate-0000001",
            "record_digest": _sha256_hex("a"),
            "record_family": "authority_state",
        }
    )
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 4. AuthorityState: construction / round trip
# ---------------------------------------------------------------------------


def test_136ab_authority_state_minimal_valid_construction_legacy_verified(schema_registry):
    wire = _valid_state_wire(authority_kind="legacy", verification_state="verified")
    del wire["authoritative_generation"]
    _assert_schema_valid(wire, AUTHORITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.AuthorityState.from_dict(wire, schema_version="1.0")
    assert model.authoritative_generation is auth.ABSENT
    assert model.uncertainty is auth.ABSENT


def test_136ab_authority_state_maximal_valid_construction_cltr_unverified(schema_registry):
    wire = _valid_state_wire(verification_state="unverified", uncertainty={"reason": "pending confirmation"})
    _assert_schema_valid(wire, AUTHORITY_STATE_SCHEMA_ID, schema_registry)
    model = auth.AuthorityState.from_dict(wire, schema_version="1.0")
    assert model.uncertainty.reason == "pending confirmation"
    assert model.authoritative_generation.generation_id.value == "gen-0000001"


def test_136ab_authority_state_exact_field_mapping(schema_registry):
    wire = _valid_state_wire()
    model = auth.AuthorityState.from_dict(wire, schema_version="1.0")
    assert model.transition_id.value == wire["transition_id"]
    assert model.active_authority_epoch.record_id.value == "authepoch-0000001"
    assert model.publication_evidence_reference.record_id.value == "pubevidence-0000001"
    assert model.pointer_digest.value == wire["pointer_digest"]
    assert model.compatibility_mode is auth.CompatibilityMode.LEGACY_ADAPTER
    assert model.verification_state is auth.VerificationState.VERIFIED


def test_136ab_authority_state_round_trip_all_variants(schema_registry):
    variants = [
        _valid_state_wire(authority_kind="cltr", verification_state="verified"),
        _valid_state_wire(authority_kind="legacy", verification_state="verification_failed"),
        _valid_state_wire(verification_state="unverified", uncertainty={"reason": "pending"}),
    ]
    variants[1] = dict(variants[1])
    del variants[1]["authoritative_generation"]
    for wire in variants:
        _assert_schema_valid(wire, AUTHORITY_STATE_SCHEMA_ID, schema_registry)
        model = auth.AuthorityState.from_dict(wire, schema_version="1.0")
        round_tripped = auth.AuthorityState.from_dict(model.to_dict(), schema_version="1.0")
        assert model == round_tripped
        assert model.to_dict() == round_tripped.to_dict()


def test_136ab_authority_state_unknown_field_rejected():
    wire = _valid_state_wire(unexpected_field="nope")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_unknown_enum_value_rejected():
    wire = _valid_state_wire(compatibility_mode="not_a_real_mode")
    with pytest.raises(ValueError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_unsupported_schema_version_rejected():
    wire = _valid_state_wire()
    with pytest.raises(auth_errors.UnsupportedSchemaVersionError):
        auth.AuthorityState.from_dict(wire, schema_version="0.1")


def test_136ab_authority_state_wrong_schema_id_rejected():
    wire = _valid_state_wire(schema_id="https://pcae.local/schemas/cltr_cutover/records/wrong.schema.json")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 5. AuthorityState: conditional branches
# ---------------------------------------------------------------------------


def test_136ab_authority_state_cltr_requires_authoritative_generation():
    wire = _valid_state_wire(authority_kind="cltr")
    del wire["authoritative_generation"]
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_legacy_authoritative_generation_optional():
    wire_with = _valid_state_wire(authority_kind="legacy")
    wire_without = _valid_state_wire(authority_kind="legacy")
    del wire_without["authoritative_generation"]
    auth.AuthorityState.from_dict(wire_with, schema_version="1.0")
    auth.AuthorityState.from_dict(wire_without, schema_version="1.0")


def test_136ab_authority_state_unverified_requires_uncertainty():
    wire = _valid_state_wire(verification_state="unverified")
    wire.pop("uncertainty", None)
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_verified_forbids_uncertainty():
    wire = _valid_state_wire(verification_state="verified", uncertainty={"reason": "should not be here"})
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_verification_failed_uncertainty_optional():
    wire_with = _valid_state_wire(verification_state="verification_failed", uncertainty={"reason": "x"})
    wire_without = _valid_state_wire(verification_state="verification_failed")
    auth.AuthorityState.from_dict(wire_with, schema_version="1.0")
    auth.AuthorityState.from_dict(wire_without, schema_version="1.0")


def test_136ab_authority_state_active_authority_epoch_wrong_family_rejected():
    wire = _valid_state_wire(
        active_authority_epoch={
            "record_id": "authstate-0000002",
            "record_digest": _sha256_hex("a"),
            "record_family": "authority_state",
        }
    )
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_publication_evidence_reference_wrong_family_rejected():
    wire = _valid_state_wire(
        publication_evidence_reference={
            "record_id": "authepoch-0000009",
            "record_digest": _sha256_hex("a"),
            "record_family": "authority_epoch",
        }
    )
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_authoritative_role_permitted_but_never_authoritative():
    wire = _valid_state_wire(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "z",
        }
    )
    model = auth.AuthorityState.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.authority_role is auth.AuthorityRole.AUTHORITATIVE
    assert model.authority_disclosure.is_authoritative is False


# ---------------------------------------------------------------------------
# 6. Immutability
# ---------------------------------------------------------------------------


def test_136ab_authority_epoch_top_level_assignment_raises():
    model = auth.AuthorityEpoch.from_dict(_valid_epoch_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.migration_epoch = auth.MigrationEpochToken("epoch-002")


def test_136ab_authority_state_top_level_assignment_raises():
    model = auth.AuthorityState.from_dict(_valid_state_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.verification_state = auth.VerificationState.VERIFIED


def test_136ab_authority_epoch_limitations_is_tuple_not_list():
    model = auth.AuthorityEpoch.from_dict(_valid_epoch_wire(limitations=["a"]), schema_version="1.0")
    assert isinstance(model.limitations.entries, tuple)


def test_136ab_to_dict_output_mutation_does_not_affect_model():
    model = auth.AuthorityEpoch.from_dict(_valid_epoch_wire(), schema_version="1.0")
    output = model.to_dict()
    output["migration_epoch"] = "mutated"
    output["authority_disclosure"]["disclosure_text"] = "mutated"
    assert model.migration_epoch.value == "epoch-001"
    assert model.authority_disclosure.disclosure_text != "mutated"


# ---------------------------------------------------------------------------
# 7. Equality
# ---------------------------------------------------------------------------


def test_136ab_authority_epoch_structural_equality():
    a = auth.AuthorityEpoch.from_dict(_valid_epoch_wire(), schema_version="1.0")
    b = auth.AuthorityEpoch.from_dict(_valid_epoch_wire(), schema_version="1.0")
    assert a == b
    c = auth.AuthorityEpoch.from_dict(_valid_epoch_wire(migration_epoch="epoch-002"), schema_version="1.0")
    assert a != c


def test_136ab_authority_state_record_id_equality_does_not_imply_record_equality():
    a = auth.AuthorityState.from_dict(_valid_state_wire(), schema_version="1.0")
    b = auth.AuthorityState.from_dict(
        _valid_state_wire(authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "different text entirely",
        }),
        schema_version="1.0",
    )
    assert a.envelope.record_id == b.envelope.record_id
    assert a != b


# ---------------------------------------------------------------------------
# 8. Digest / identifier family preservation
# ---------------------------------------------------------------------------


def test_136ab_authority_epoch_malformed_digest_rejected():
    wire = _valid_epoch_wire(record_digest="not-a-valid-digest")
    with pytest.raises(auth_errors.InvalidDigestError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_malformed_pointer_digest_rejected():
    wire = _valid_state_wire(pointer_digest="short")
    with pytest.raises(auth_errors.InvalidDigestError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


def test_136ab_authority_epoch_malformed_record_id_rejected():
    wire = _valid_epoch_wire(record_id="BAD ID!!")
    with pytest.raises(auth_errors.InvalidIdentifierError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_malformed_transition_id_rejected():
    wire = _valid_state_wire(transition_id="not-trans-prefixed")
    with pytest.raises(auth_errors.InvalidIdentifierError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


def test_136ab_digest_never_computed_during_construction(monkeypatch):
    import hashlib

    called = []
    monkeypatch.setattr(hashlib, "sha256", lambda *a, **k: called.append(1) or hashlib.sha256(*a, **k))
    auth.AuthorityEpoch.from_dict(_valid_epoch_wire(), schema_version="1.0")
    auth.AuthorityState.from_dict(_valid_state_wire(), schema_version="1.0")
    assert not called


# ---------------------------------------------------------------------------
# 9. No coercion / no default inference
# ---------------------------------------------------------------------------


def test_136ab_authority_epoch_boolean_string_not_coerced():
    wire = _valid_epoch_wire(
        authority_disclosure={"authority_role": "derivative", "is_authoritative": "false", "disclosure_text": "x"}
    )
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_epoch_missing_required_field_rejected():
    wire = _valid_epoch_wire()
    del wire["migration_epoch"]
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityEpoch.from_dict(wire, schema_version="1.0")


def test_136ab_authority_state_missing_required_field_rejected():
    wire = _valid_state_wire()
    del wire["compatibility_mode"]
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.AuthorityState.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 10. Schema-to-model conformance (drift detection)
# ---------------------------------------------------------------------------


def _load_schema(relative_path: str) -> dict:
    with cltr_cutover_root() as root:
        return json.loads((root / relative_path).read_text())


def test_136ab_authority_epoch_schema_field_set_matches_model_known_keys():
    schema = _load_schema("records/authority_epoch.schema.json")
    schema_fields = set(schema["properties"].keys())
    from pcae.cltr.authority.authority_core import _AUTHORITY_EPOCH_KNOWN_KEYS

    assert schema_fields == _AUTHORITY_EPOCH_KNOWN_KEYS


def test_136ab_authority_epoch_schema_required_set_matches_model_required_handling():
    schema = _load_schema("records/authority_epoch.schema.json")
    required = set(schema["required"])
    # generation_binding is conditionally required (not in schema's own
    # unconditional `required` list); every other field is unconditional.
    unconditional = set(auth.AuthorityEpoch.__dataclass_fields__.keys()) - {"generation_binding"}
    # envelope is a composed field standing in for 6 flattened wire keys;
    # expand it for the comparison.
    expanded = (unconditional - {"envelope"}) | {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
    }
    assert expanded == required


def test_136ab_authority_state_schema_field_set_matches_model_known_keys():
    schema = _load_schema("records/authority_state.schema.json")
    schema_fields = set(schema["properties"].keys())
    from pcae.cltr.authority.authority_core import _AUTHORITY_STATE_KNOWN_KEYS

    assert schema_fields == _AUTHORITY_STATE_KNOWN_KEYS


def test_136ab_authority_state_schema_required_set_matches_model_required_handling():
    schema = _load_schema("records/authority_state.schema.json")
    required = set(schema["required"])
    unconditional = set(auth.AuthorityState.__dataclass_fields__.keys()) - {
        "authoritative_generation",
        "uncertainty",
    }
    expanded = (unconditional - {"envelope"}) | {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
    }
    assert expanded == required


def test_136ab_authority_epoch_activation_state_enum_members_match_schema():
    schema = _load_schema("records/authority_epoch.schema.json")
    schema_values = set(schema["properties"]["activation_state"]["enum"])
    model_values = {member.value for member in auth.ActivationState}
    assert schema_values == model_values


def test_136ab_authority_state_verification_state_enum_members_match_schema():
    schema = _load_schema("records/authority_state.schema.json")
    schema_values = set(schema["properties"]["verification_state"]["enum"])
    model_values = {member.value for member in auth.VerificationState}
    assert schema_values == model_values


# ---------------------------------------------------------------------------
# 11. No-authority-semantics / no-later-scope
# ---------------------------------------------------------------------------


def test_136ab_no_authority_selection_symbols_defined_in_source():
    source = AUTHORITY_PACKAGE_DIR.joinpath("authority_core.py").read_text()
    tree = ast.parse(source)
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_AUTHORITY_SYMBOLS:
        assert forbidden not in defined_names


def test_136ab_no_cas_expectation_used_by_either_model():
    source = AUTHORITY_PACKAGE_DIR.joinpath("authority_core.py").read_text()
    assert "CasExpectation" not in source


def test_136ab_no_extension_mapping_used_by_either_model():
    source = AUTHORITY_PACKAGE_DIR.joinpath("authority_core.py").read_text()
    assert "ExtensionMapping" not in source


def test_136ab_no_opaque_json_value_used_by_either_model():
    source = AUTHORITY_PACKAGE_DIR.joinpath("authority_core.py").read_text()
    assert "OpaqueJsonValue" not in source


# ---------------------------------------------------------------------------
# 12. Runtime isolation / no-side-effect
# ---------------------------------------------------------------------------


def test_136ab_no_production_module_imports_authority_package():
    for root_dir in PRODUCTION_SCAN_ROOTS:
        if not root_dir.exists():
            continue
        for path in root_dir.rglob("*.py"):
            if AUTHORITY_PACKAGE_DIR in path.parents or path.parent == AUTHORITY_PACKAGE_DIR:
                continue
            source = path.read_text()
            assert "from pcae.cltr.authority" not in source, path
            assert "import pcae.cltr.authority" not in source, path


def test_136ab_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    model = auth.AuthorityEpoch.from_dict(_valid_epoch_wire(), schema_version="1.0")
    model.to_dict()
    state = auth.AuthorityState.from_dict(_valid_state_wire(), schema_version="1.0")
    state.to_dict()


def test_136ab_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "Popen", _raise)
    auth.AuthorityEpoch.from_dict(_valid_epoch_wire(), schema_version="1.0").to_dict()
    auth.AuthorityState.from_dict(_valid_state_wire(), schema_version="1.0").to_dict()


def test_136ab_no_filesystem_write_during_construction_or_serialization(monkeypatch, tmp_path):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in ("w", "a", "x")):
            raise AssertionError(f"filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    auth.AuthorityEpoch.from_dict(_valid_epoch_wire(), schema_version="1.0").to_dict()
    auth.AuthorityState.from_dict(_valid_state_wire(), schema_version="1.0").to_dict()


def test_136ab_no_environment_variable_lookup_during_construction(monkeypatch):
    import os

    def _raise(*args, **kwargs):
        raise AssertionError("environment variable lookup attempted")

    monkeypatch.setattr(os.environ, "get", _raise)
    auth.AuthorityEpoch.from_dict(_valid_epoch_wire(), schema_version="1.0")
    auth.AuthorityState.from_dict(_valid_state_wire(), schema_version="1.0")


# ---------------------------------------------------------------------------
# 13. Packaging
# ---------------------------------------------------------------------------


def test_136ab_wheel_contains_authority_core_module(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()

    assert any(name.endswith("pcae/cltr/authority/authority_core.py") for name in names)
    # request_readiness.py narrowed off this list by Phase 136AD: it is now
    # an authorized, legitimately-implemented module (Group 3). Narrowed
    # further by Phase 136AF: authorization_candidate.py (Group 4) is now
    # authorized too. Narrowed further by Phase 136AH: publication.py
    # (Group 5) is now authorized too, so its presence in the wheel is
    # expected rather than forbidden.
    for later_module in (
        "recovery.py",
        "bindings.py",
        "compatibility_quarantine.py",
    ):
        assert not any(name.endswith(f"pcae/cltr/authority/{later_module}") for name in names)


def test_136ab_sdist_includes_authority_core_module(tmp_path: Path):
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
    assert any(name.endswith("pcae/cltr/authority/authority_core.py") for name in names)


@pytest.mark.slow
def test_136ab_installed_wheel_constructs_authority_core_fixtures_outside_repository(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv136ab"
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
        "wire = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0', 'record_type': 'authority_epoch',\n"
        "    'record_id': 'authepoch-0000001', 'record_digest': 'a' * 64,\n"
        "    'created_at': '2026-07-17T12:00:00Z', 'migration_epoch': 'epoch-001',\n"
        "    'authority_kind': 'legacy', 'activation_state': 'proposed', 'predecessor_epoch': None,\n"
        "    'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'derivative', 'is_authoritative': False, 'disclosure_text': 'x'},\n"
        "}\n"
        "model = auth.AuthorityEpoch.from_dict(wire, schema_version='1.0')\n"
        "assert model.to_dict()['record_id'] == 'authepoch-0000001'\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [str(venv_python), "-c", probe_script],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(outside_cwd),
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
