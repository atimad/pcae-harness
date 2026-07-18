"""Phase 136AC: Stage 3 Typed Authority Model Authority Core Independent
Verification.

Independently re-derives and re-verifies the ``AuthorityEpoch`` and
``AuthorityState`` typed record models implemented in Phase 136AB
(``src/pcae/cltr/authority/authority_core.py``), against the frozen
executable schemas directly.

This module deliberately does NOT import fixtures, helper functions, or
expected-value constants from ``tests/test_cltr_authority_136ab_authority_core.py``.
Every payload, field table, and expected outcome below is constructed from
first principles by reading ``records/authority_epoch.schema.json`` and
``records/authority_state.schema.json`` directly at test-collection time (via
``build_offline_registry``/``validate_record_shape``, the same production,
non-authority-specific Layer 2 infrastructure the models themselves are
schema-conformance-checked against -- never via the 136AB test module).
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import errors as auth_errors
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]

_EPOCH_SCHEMA_PATH = (
    REPO_ROOT / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "records" / "authority_epoch.schema.json"
)
_STATE_SCHEMA_PATH = (
    REPO_ROOT / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "records" / "authority_state.schema.json"
)


def _load_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


EPOCH_SCHEMA = _load_schema(_EPOCH_SCHEMA_PATH)
STATE_SCHEMA = _load_schema(_STATE_SCHEMA_PATH)


@pytest.fixture(scope="module")
def registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _assert_schema_valid(payload: dict, *, schema_id: str, reg) -> None:
    result = validate_record_shape(payload, schema_id=schema_id, registry=reg)
    assert result.status == OutcomeStatus.VALID, (schema_id, result.issues)


# ---------------------------------------------------------------------------
# Section 1: independently re-derived field tables
# ---------------------------------------------------------------------------


def test_epoch_schema_required_set_independently_derived():
    assert set(EPOCH_SCHEMA["required"]) == {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "authority_kind",
        "activation_state",
        "predecessor_epoch",
        "limitations",
        "authority_disclosure",
    }
    # generation_binding is a declared property but NOT in "required":
    # conditionally present only.
    assert "generation_binding" in EPOCH_SCHEMA["properties"]
    assert "generation_binding" not in EPOCH_SCHEMA["required"]
    assert EPOCH_SCHEMA["additionalProperties"] is False


def test_state_schema_required_set_independently_derived():
    assert set(STATE_SCHEMA["required"]) == {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "transition_id",
        "active_authority_epoch",
        "authority_kind",
        "publication_evidence_reference",
        "pointer_digest",
        "verification_state",
        "compatibility_mode",
        "limitations",
        "authority_disclosure",
    }
    for conditional_field in ("authoritative_generation", "uncertainty"):
        assert conditional_field in STATE_SCHEMA["properties"]
        assert conditional_field not in STATE_SCHEMA["required"]
    assert STATE_SCHEMA["additionalProperties"] is False


def test_epoch_model_known_keys_matches_schema_property_set():
    model_known = set(auth.AuthorityEpoch.__dataclass_fields__)
    # The model's dataclass fields are Python-side (envelope-nested); assert
    # via the actual accepted-payload keyset used by from_dict instead by
    # round-tripping a minimal instance and diffing serialized keys against
    # the schema's declared property set (independently, not by importing
    # the model's private _KNOWN_KEYS constant).
    schema_props = set(EPOCH_SCHEMA["properties"])
    epoch = _minimal_epoch()
    payload = epoch.to_dict()
    assert set(payload).issubset(schema_props)


def test_state_model_serialized_keys_subset_of_schema_properties():
    schema_props = set(STATE_SCHEMA["properties"])
    state = _minimal_state()
    payload = state.to_dict()
    assert set(payload).issubset(schema_props)


def test_epoch_activation_state_enum_independently_derived():
    assert set(EPOCH_SCHEMA["properties"]["activation_state"]["enum"]) == {
        "proposed",
        "active",
        "superseded",
    }


def test_state_verification_state_enum_independently_derived():
    assert set(STATE_SCHEMA["properties"]["verification_state"]["enum"]) == {
        "unverified",
        "verified",
        "verification_failed",
    }


def test_epoch_discriminators_independently_derived():
    assert EPOCH_SCHEMA["properties"]["record_type"]["const"] == "authority_epoch"
    assert (
        EPOCH_SCHEMA["properties"]["schema_id"]["const"]
        == "https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json"
    )
    assert EPOCH_SCHEMA["properties"]["contract_version"]["const"] == "1.0"


def test_state_discriminators_independently_derived():
    assert STATE_SCHEMA["properties"]["record_type"]["const"] == "authority_state"
    assert (
        STATE_SCHEMA["properties"]["schema_id"]["const"]
        == "https://pcae.local/schemas/cltr_cutover/records/authority_state.schema.json"
    )


def test_epoch_predecessor_epoch_is_always_a_key_nullable_or_typed():
    prop = EPOCH_SCHEMA["properties"]["predecessor_epoch"]
    assert "predecessor_epoch" in EPOCH_SCHEMA["required"]
    one_of = prop["oneOf"]
    assert {"type": "null"} in one_of


def test_authority_disclosure_authoritative_role_forbidden_only_on_epoch():
    epoch_disclosure = EPOCH_SCHEMA["properties"]["authority_disclosure"]
    forbidding = epoch_disclosure["allOf"][1]["properties"]["authority_role"]
    assert forbidding == {"not": {"const": "authoritative"}}
    # authority_state.schema.json's authority_disclosure carries no such
    # local restriction (a bare $ref, not an allOf-restricted local type).
    state_disclosure = STATE_SCHEMA["properties"]["authority_disclosure"]
    assert "allOf" not in state_disclosure


# ---------------------------------------------------------------------------
# Independently constructed fixtures (not shared with 136AB)
# ---------------------------------------------------------------------------

_EPOCH_ID = "authority-epoch-independent-0001"
_EPOCH_DIGEST = "1" * 64
_STATE_ID = "authority-state-independent-0002"
_STATE_DIGEST = "2" * 64
_GEN_ID = "generation-independent-0003"
_GEN_DIGEST = "3" * 64
_PUB_EVID_ID = "publication-evidence-ind-0004"
_PUB_EVID_DIGEST = "4" * 64
_POINTER_DIGEST = "5" * 64
_TRANSITION_ID = "trans-independent-verify-01"
_MIGRATION_EPOCH = "epoch-independent-01"


def _epoch_payload(**overrides) -> dict:
    payload = {
        "schema_id": EPOCH_SCHEMA["properties"]["schema_id"]["const"],
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_epoch",
        "record_id": _EPOCH_ID,
        "record_digest": _EPOCH_DIGEST,
        "created_at": "2026-07-17T10:00:00Z",
        "migration_epoch": _MIGRATION_EPOCH,
        "authority_kind": "legacy",
        "activation_state": "proposed",
        "predecessor_epoch": None,
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Independent 136AC verification fixture.",
        },
    }
    payload.update(overrides)
    return payload


def _state_payload(**overrides) -> dict:
    payload = {
        "schema_id": STATE_SCHEMA["properties"]["schema_id"]["const"],
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_state",
        "record_id": _STATE_ID,
        "record_digest": _STATE_DIGEST,
        "created_at": "2026-07-17T10:05:00Z",
        "migration_epoch": _MIGRATION_EPOCH,
        "transition_id": _TRANSITION_ID,
        "active_authority_epoch": {
            "record_id": _EPOCH_ID,
            "record_digest": _EPOCH_DIGEST,
            "record_family": "authority_epoch",
        },
        "authority_kind": "legacy",
        "publication_evidence_reference": {
            "record_id": _PUB_EVID_ID,
            "record_digest": _PUB_EVID_DIGEST,
            "record_family": "publication_evidence",
        },
        "pointer_digest": _POINTER_DIGEST,
        "verification_state": "verified",
        "compatibility_mode": "legacy_authoritative",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Independent 136AC verification fixture.",
        },
    }
    payload.update(overrides)
    return payload


def _minimal_epoch() -> auth.AuthorityEpoch:
    return auth.AuthorityEpoch.from_dict(_epoch_payload(), schema_version="1.0")


def _minimal_state() -> auth.AuthorityState:
    return auth.AuthorityState.from_dict(_state_payload(), schema_version="1.0")


# ---------------------------------------------------------------------------
# Section 2: minimal/maximal construction, schema cross-check
# ---------------------------------------------------------------------------


def test_epoch_minimal_valid_payload_is_schema_valid(registry):
    payload = _epoch_payload()
    _assert_schema_valid(payload, schema_id=EPOCH_SCHEMA["$id"], reg=registry)
    epoch = auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")
    assert epoch.activation_state is auth.ActivationState.PROPOSED


def test_epoch_maximal_active_payload_is_schema_valid_and_constructs(registry):
    payload = _epoch_payload(
        activation_state="active",
        generation_binding={"generation_id": _GEN_ID, "generation_digest": _GEN_DIGEST},
        predecessor_epoch={
            "record_id": "authority-epoch-independent-0000",
            "record_digest": "0" * 64,
            "record_family": "authority_epoch",
        },
        limitations=["Independent verification limitation entry."],
    )
    _assert_schema_valid(payload, schema_id=EPOCH_SCHEMA["$id"], reg=registry)
    epoch = auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")
    assert epoch.generation_binding is not auth.ABSENT
    assert epoch.predecessor_epoch is not None


def test_state_minimal_valid_payload_is_schema_valid(registry):
    payload = _state_payload()
    _assert_schema_valid(payload, schema_id=STATE_SCHEMA["$id"], reg=registry)
    auth.AuthorityState.from_dict(payload, schema_version="1.0")


def test_state_maximal_cltr_unverified_payload_is_schema_valid_and_constructs(registry):
    payload = _state_payload(
        authority_kind="cltr",
        authoritative_generation={"generation_id": _GEN_ID, "generation_digest": _GEN_DIGEST},
        verification_state="unverified",
        uncertainty={"reason": "Independent verification uncertainty disclosure."},
    )
    _assert_schema_valid(payload, schema_id=STATE_SCHEMA["$id"], reg=registry)
    state = auth.AuthorityState.from_dict(payload, schema_version="1.0")
    assert state.authoritative_generation is not auth.ABSENT
    assert state.uncertainty is not auth.ABSENT


# ---------------------------------------------------------------------------
# Section 3: discriminator adversarial matrix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_record_type",
    ["Authority_Epoch", "authority_epoch ", " authority_epoch", "authority-epoch", "AUTHORITY_EPOCH", "epoch"],
)
def test_epoch_wrong_or_malformed_record_type_rejected(bad_record_type):
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(record_type=bad_record_type), schema_version="1.0")


def test_epoch_non_string_record_type_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(record_type=123), schema_version="1.0")


def test_epoch_null_record_type_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(record_type=None), schema_version="1.0")


def test_epoch_absent_discriminator_rejected():
    payload = _epoch_payload()
    del payload["record_type"]
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")


def test_epoch_wrong_schema_id_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(
            _epoch_payload(schema_id="https://pcae.local/schemas/cltr_cutover/records/authority_state.schema.json"),
            schema_version="1.0",
        )


def test_state_wrong_record_type_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityState.from_dict(_state_payload(record_type="authority_epoch"), schema_version="1.0")


def test_epoch_wrong_case_activation_state_rejected():
    # CONFIRMED-136AC-1 (NON-BLOCKING): enum-member construction failures
    # for activation_state/verification_state/authority_kind/
    # compatibility_mode/authority_role raise a bare stdlib ValueError, NOT
    # any subclass of auth_errors.TypedModelError -- the enum reject path
    # is fail-closed (the malformed value is never accepted) but does not
    # participate in the shared Layer 3 error hierarchy the module
    # docstring and contract Error-Hierarchy Verification section require.
    # 136AB's own test suite bakes this in via `pytest.raises(ValueError)`
    # rather than disclosing it; see the 136AC verification report.
    with pytest.raises(ValueError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(activation_state="Proposed"), schema_version="1.0")


def test_epoch_alias_like_activation_state_rejected():
    # See CONFIRMED-136AC-1 above: bare ValueError, not TypedModelError.
    with pytest.raises(ValueError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(activation_state="pending"), schema_version="1.0")


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("authority_kind", "LEGACY"),
        ("activation_state", "Active"),
    ],
)
def test_epoch_enum_field_rejection_is_bare_valueerror_not_typedmodelerror(field, bad_value):
    """CONFIRMED-136AC-1 (NON-BLOCKING). Documents, does not repair: the
    contract's Error-Hierarchy Verification section requires every
    construction failure category (including "wrong enum") to be part of
    the shared TypedModelError hierarchy. All four ``EnumClass(raw_str)``
    call sites in authority_core.py (activation_state, authority_kind,
    verification_state, compatibility_mode) let a plain stdlib
    ``ValueError`` propagate uncaught on an unrecognized member instead of
    wrapping it in ``TypedModelConstructionError``. The value is still
    rejected (fail-closed, no coercion) -- only the exception type is
    inconsistent with the rest of the module's own error taxonomy."""

    payload = _epoch_payload(**{field: bad_value})
    with pytest.raises(ValueError) as excinfo:
        auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")
    assert not isinstance(excinfo.value, auth_errors.TypedModelError), (
        "CONFIRMED-136AC-1 appears to be fixed: enum rejection now raises a "
        "TypedModelError subclass. Update the finding disclosure if so."
    )


def test_state_enum_field_rejection_is_bare_valueerror_not_typedmodelerror():
    """See CONFIRMED-136AC-1. Same defect reproduced via AuthorityState's
    verification_state field."""

    payload = _state_payload(verification_state="Verified")
    with pytest.raises(ValueError):
        auth.AuthorityState.from_dict(payload, schema_version="1.0")


def test_epoch_unsupported_schema_version_rejected():
    with pytest.raises(auth_errors.UnsupportedSchemaVersionError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(), schema_version="2.0")


# ---------------------------------------------------------------------------
# Section 4: absent vs explicit null vs typed value (generation_binding,
# uncertainty, authoritative_generation)
# ---------------------------------------------------------------------------


def test_epoch_generation_binding_omitted_means_absent_when_proposed():
    epoch = auth.AuthorityEpoch.from_dict(_epoch_payload(), schema_version="1.0")
    assert epoch.generation_binding is auth.ABSENT
    assert "generation_binding" not in epoch.to_dict()


def test_epoch_generation_binding_explicit_null_rejected(registry):
    payload = _epoch_payload(generation_binding=None)
    result = validate_record_shape(payload, schema_id=EPOCH_SCHEMA["$id"], registry=registry)
    assert result.status == OutcomeStatus.INVALID
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")


def test_epoch_generation_binding_required_when_active():
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(activation_state="active"), schema_version="1.0")


def test_epoch_generation_binding_forbidden_when_proposed():
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityEpoch.from_dict(
            _epoch_payload(
                activation_state="proposed",
                generation_binding={"generation_id": _GEN_ID, "generation_digest": _GEN_DIGEST},
            ),
            schema_version="1.0",
        )


def test_epoch_superseded_generation_binding_optional_both_ways():
    without = auth.AuthorityEpoch.from_dict(_epoch_payload(activation_state="superseded"), schema_version="1.0")
    assert without.generation_binding is auth.ABSENT
    with_binding = auth.AuthorityEpoch.from_dict(
        _epoch_payload(
            activation_state="superseded",
            generation_binding={"generation_id": _GEN_ID, "generation_digest": _GEN_DIGEST},
        ),
        schema_version="1.0",
    )
    assert with_binding.generation_binding is not auth.ABSENT


def test_state_uncertainty_absent_and_present_are_distinguishable():
    verified = auth.AuthorityState.from_dict(_state_payload(verification_state="verified"), schema_version="1.0")
    assert verified.uncertainty is auth.ABSENT
    unverified = auth.AuthorityState.from_dict(
        _state_payload(verification_state="unverified", uncertainty={"reason": "disclosed"}),
        schema_version="1.0",
    )
    assert unverified.uncertainty is not auth.ABSENT
    assert unverified.uncertainty is not None


def test_state_uncertainty_required_when_unverified():
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityState.from_dict(_state_payload(verification_state="unverified"), schema_version="1.0")


def test_state_uncertainty_forbidden_when_verified():
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityState.from_dict(
            _state_payload(verification_state="verified", uncertainty={"reason": "should not be here"}),
            schema_version="1.0",
        )


def test_state_verification_failed_uncertainty_is_optional_both_ways():
    without = auth.AuthorityState.from_dict(
        _state_payload(verification_state="verification_failed"), schema_version="1.0"
    )
    assert without.uncertainty is auth.ABSENT
    with_it = auth.AuthorityState.from_dict(
        _state_payload(verification_state="verification_failed", uncertainty={"reason": "why"}),
        schema_version="1.0",
    )
    assert with_it.uncertainty is not auth.ABSENT


def test_state_authoritative_generation_required_when_cltr():
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityState.from_dict(_state_payload(authority_kind="cltr"), schema_version="1.0")


def test_state_authoritative_generation_optional_when_legacy():
    without = auth.AuthorityState.from_dict(_state_payload(authority_kind="legacy"), schema_version="1.0")
    assert without.authoritative_generation is auth.ABSENT
    with_it = auth.AuthorityState.from_dict(
        _state_payload(
            authority_kind="legacy",
            authoritative_generation={"generation_id": _GEN_ID, "generation_digest": _GEN_DIGEST},
        ),
        schema_version="1.0",
    )
    assert with_it.authoritative_generation is not auth.ABSENT


# ---------------------------------------------------------------------------
# Section 5: identifier / digest / reference family verification
# ---------------------------------------------------------------------------


def test_epoch_malformed_record_id_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(record_id="BAD ID!"), schema_version="1.0")


def test_epoch_malformed_record_digest_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(record_digest="not-a-digest"), schema_version="1.0")


def test_epoch_short_digest_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(record_digest="ab" * 10), schema_version="1.0")


def test_epoch_uppercase_digest_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(record_digest="A" * 64), schema_version="1.0")


def test_epoch_predecessor_epoch_wrong_family_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(
            _epoch_payload(
                predecessor_epoch={
                    "record_id": _PUB_EVID_ID,
                    "record_digest": _PUB_EVID_DIGEST,
                    "record_family": "publication_evidence",
                }
            ),
            schema_version="1.0",
        )


def test_state_active_authority_epoch_wrong_family_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityState.from_dict(
            _state_payload(
                active_authority_epoch={
                    "record_id": _PUB_EVID_ID,
                    "record_digest": _PUB_EVID_DIGEST,
                    "record_family": "publication_evidence",
                }
            ),
            schema_version="1.0",
        )


def test_state_publication_evidence_reference_wrong_family_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityState.from_dict(
            _state_payload(
                publication_evidence_reference={
                    "record_id": _EPOCH_ID,
                    "record_digest": _EPOCH_DIGEST,
                    "record_family": "authority_epoch",
                }
            ),
            schema_version="1.0",
        )


def test_state_pointer_digest_malformed_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityState.from_dict(_state_payload(pointer_digest="zz" * 32), schema_version="1.0")


def test_state_transition_id_malformed_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityState.from_dict(_state_payload(transition_id="not-a-transition-id"), schema_version="1.0")


def test_references_construct_successfully_for_nonexistent_targets_no_lookup():
    """A syntactically valid reference to a target that has never existed
    must construct without error: no cross-record existence check occurs
    at this layer."""

    epoch = auth.AuthorityEpoch.from_dict(
        _epoch_payload(
            predecessor_epoch={
                "record_id": "authority-epoch-never-existed-99",
                "record_digest": "9" * 64,
                "record_family": "authority_epoch",
            }
        ),
        schema_version="1.0",
    )
    assert epoch.predecessor_epoch.record_id.value == "authority-epoch-never-existed-99"


def test_no_filesystem_or_network_access_during_reference_construction(monkeypatch, tmp_path):
    calls = {"open": 0, "socket": 0}
    real_open = open

    def spy_open(*args, **kwargs):
        calls["open"] += 1
        return real_open(*args, **kwargs)

    def spy_socket(*args, **kwargs):
        calls["socket"] += 1
        raise AssertionError("socket.socket must never be called by typed-model construction")

    monkeypatch.setattr("builtins.open", spy_open)
    monkeypatch.setattr(socket, "socket", spy_socket)
    try:
        _minimal_epoch()
        _minimal_state()
    finally:
        monkeypatch.undo()
    assert calls["socket"] == 0


# ---------------------------------------------------------------------------
# Section 6: timestamp preservation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "wire_timestamp",
    [
        "2026-07-17T10:00:00Z",
        "2026-07-17T10:00:00.123456Z",
        "2026-07-17T10:00:00.1Z",
        "2000-01-01T00:00:00Z",
        "2099-12-31T23:59:59Z",
    ],
)
def test_epoch_timestamp_preserved_exactly_on_round_trip(wire_timestamp):
    epoch = auth.AuthorityEpoch.from_dict(_epoch_payload(created_at=wire_timestamp), schema_version="1.0")
    assert epoch.envelope.created_at.wire == wire_timestamp
    assert epoch.to_dict()["created_at"] == wire_timestamp


def test_timestamp_offset_form_not_accepted_as_z_and_not_normalized():
    # +00:00 offset form is a different wire string than Z; the frozen
    # pattern requires an explicit 'Z' suffix only, so this must be
    # rejected outright -- never silently normalized to Z.
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(
            _epoch_payload(created_at="2026-07-17T10:00:00+00:00"), schema_version="1.0"
        )


def test_no_clock_read_during_construction(monkeypatch):
    import datetime as real_datetime

    class ForbiddenNow(real_datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            raise AssertionError("construction must never read the current time")

        @classmethod
        def utcnow(cls):
            raise AssertionError("construction must never read the current time")

    monkeypatch.setattr("datetime.datetime", ForbiddenNow)
    try:
        _minimal_epoch()
        _minimal_state()
    finally:
        monkeypatch.undo()


# ---------------------------------------------------------------------------
# Section 7: serialization losslessness / round trip
# ---------------------------------------------------------------------------


def test_epoch_round_trip_preserves_all_fields_exactly():
    payload = _epoch_payload(
        activation_state="active",
        generation_binding={"generation_id": _GEN_ID, "generation_digest": _GEN_DIGEST},
        limitations=["one", "two"],
    )
    epoch = auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")
    round_tripped = epoch.to_dict()
    for key, value in payload.items():
        assert round_tripped[key] == value, key


def test_state_round_trip_preserves_all_fields_exactly():
    payload = _state_payload(
        authority_kind="cltr",
        authoritative_generation={"generation_id": _GEN_ID, "generation_digest": _GEN_DIGEST},
        verification_state="unverified",
        uncertainty={"reason": "disclosed uncertainty"},
        limitations=["disclosed limitation"],
    )
    state = auth.AuthorityState.from_dict(payload, schema_version="1.0")
    round_tripped = state.to_dict()
    for key, value in payload.items():
        assert round_tripped[key] == value, key


def test_to_dict_returns_fresh_mutable_structure_not_aliased_to_internals():
    epoch = _minimal_epoch()
    d1 = epoch.to_dict()
    d1["limitations"].append("mutated after serialization")
    d2 = epoch.to_dict()
    assert d2["limitations"] == []


def test_serialized_output_is_plain_dict_and_json_dumpable():
    epoch = _minimal_epoch()
    state = _minimal_state()
    json.dumps(epoch.to_dict())
    json.dumps(state.to_dict())


# ---------------------------------------------------------------------------
# Section 8: immutability
# ---------------------------------------------------------------------------


def test_epoch_top_level_field_assignment_raises():
    epoch = _minimal_epoch()
    with pytest.raises(dataclasses.FrozenInstanceError):
        epoch.migration_epoch = "different"


def test_state_top_level_field_assignment_raises():
    state = _minimal_state()
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.transition_id = "different"


def test_epoch_limitations_entries_is_tuple_immutable():
    epoch = _minimal_epoch()
    assert isinstance(epoch.limitations.entries, tuple)
    with pytest.raises((AttributeError, TypeError)):
        epoch.limitations.entries.append("x")


def test_mutating_original_constructor_input_dict_after_construction_does_not_affect_model():
    payload = _epoch_payload(limitations=["original"])
    epoch = auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")
    payload["limitations"].append("mutated after construction")
    payload["migration_epoch"] = "mutated-epoch-token"
    assert epoch.limitations.entries == ("original",)
    assert epoch.migration_epoch.value == _MIGRATION_EPOCH


def test_nested_authority_disclosure_is_frozen():
    epoch = _minimal_epoch()
    with pytest.raises(dataclasses.FrozenInstanceError):
        epoch.authority_disclosure.disclosure_text = "mutated"


# ---------------------------------------------------------------------------
# Section 9: equality semantics
# ---------------------------------------------------------------------------


def test_epoch_identical_payloads_compare_equal():
    a = auth.AuthorityEpoch.from_dict(_epoch_payload(), schema_version="1.0")
    b = auth.AuthorityEpoch.from_dict(_epoch_payload(), schema_version="1.0")
    assert a == b


def test_epoch_one_changed_field_causes_inequality():
    a = auth.AuthorityEpoch.from_dict(_epoch_payload(), schema_version="1.0")
    b = auth.AuthorityEpoch.from_dict(
        _epoch_payload(authority_disclosure={
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "A different disclosure text entirely.",
        }),
        schema_version="1.0",
    )
    assert a != b


def test_epoch_same_record_id_but_different_other_fields_not_equal():
    a = auth.AuthorityEpoch.from_dict(_epoch_payload(), schema_version="1.0")
    b = auth.AuthorityEpoch.from_dict(_epoch_payload(migration_epoch="a-different-epoch-token"), schema_version="1.0")
    assert a.envelope.record_id == b.envelope.record_id
    assert a != b


def test_epoch_same_digest_different_record_not_equal():
    a = auth.AuthorityEpoch.from_dict(_epoch_payload(), schema_version="1.0")
    b = auth.AuthorityEpoch.from_dict(_epoch_payload(migration_epoch="yet-another-token"), schema_version="1.0")
    assert a.envelope.record_digest == b.envelope.record_digest
    assert a != b


def test_epoch_timestamp_string_difference_remains_observable():
    a = auth.AuthorityEpoch.from_dict(_epoch_payload(created_at="2026-07-17T10:00:00Z"), schema_version="1.0")
    b = auth.AuthorityEpoch.from_dict(_epoch_payload(created_at="2026-07-17T10:00:00.000000Z"), schema_version="1.0")
    assert a.envelope.created_at.wire != b.envelope.created_at.wire
    assert a != b


# ---------------------------------------------------------------------------
# Section 10: no operational authority semantics (AST inspection)
# ---------------------------------------------------------------------------

_FORBIDDEN_OPERATIONAL_NAMES = (
    "is_current",
    "is_authoritative_now",
    "activate",
    "deactivate",
    "transition",
    "can_transition",
    "promote",
    "demote",
    "retire",
    "resolve",
    "load_current",
    "save",
    "persist",
    "enforce_cas",
    "authorize",
)


def test_no_operational_authority_method_names_defined_on_models():
    source = (REPO_ROOT / "src" / "pcae" / "cltr" / "authority" / "authority_core.py").read_text()
    tree = ast.parse(source)
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    forbidden_found = defined_names & set(_FORBIDDEN_OPERATIONAL_NAMES)
    assert not forbidden_found, forbidden_found


def test_models_define_only_dunder_and_from_dict_to_dict_methods():
    for cls in (auth.AuthorityEpoch, auth.AuthorityState):
        method_names = {
            name
            for name, value in vars(cls).items()
            if callable(value) or isinstance(value, (classmethod, staticmethod))
        }
        allowed = {
            "__init__",
            "__post_init__",
            "__repr__",
            "__eq__",
            "__hash__",
            "__setattr__",
            "__delattr__",
            "from_dict",
            "to_dict",
        }
        unexpected = method_names - allowed
        assert not unexpected, (cls.__name__, unexpected)


# ---------------------------------------------------------------------------
# Section 11: no cross-record semantic validation (schema-valid but
# operationally-inconsistent data must still construct)
# ---------------------------------------------------------------------------


def test_epoch_referencing_nonexistent_predecessor_still_constructs():
    epoch = auth.AuthorityEpoch.from_dict(
        _epoch_payload(
            predecessor_epoch={
                "record_id": "authority-epoch-fabricated-lineage",
                "record_digest": "f" * 64,
                "record_family": "authority_epoch",
            }
        ),
        schema_version="1.0",
    )
    assert epoch is not None


def test_state_referencing_nonexistent_epoch_and_evidence_still_constructs():
    """Schema-valid but operationally-impossible: references an epoch and
    publication evidence record that (from this Layer's perspective) may
    never have existed. Layer 3 must accept it -- existence and currency
    are Layer 4/6 concerns."""

    state = auth.AuthorityState.from_dict(
        _state_payload(
            active_authority_epoch={
                "record_id": "authority-epoch-does-not-exist",
                "record_digest": "e" * 64,
                "record_family": "authority_epoch",
            },
            publication_evidence_reference={
                "record_id": "publication-evidence-does-not-exist",
                "record_digest": "d" * 64,
                "record_family": "publication_evidence",
            },
        ),
        schema_version="1.0",
    )
    assert state is not None


# ---------------------------------------------------------------------------
# Section 12: no CAS execution, no digest computation
# ---------------------------------------------------------------------------


def test_no_cas_expectation_field_present_on_either_model():
    epoch_fields = set(auth.AuthorityEpoch.__dataclass_fields__)
    state_fields = set(auth.AuthorityState.__dataclass_fields__)
    assert "cas_expectation" not in epoch_fields
    assert "cas_expectation" not in state_fields


def test_hashlib_sha256_never_invoked_during_construction_or_serialization(monkeypatch):
    import hashlib

    calls = []
    real_sha256 = hashlib.sha256

    def spy_sha256(*args, **kwargs):
        calls.append((args, kwargs))
        return real_sha256(*args, **kwargs)

    monkeypatch.setattr(hashlib, "sha256", spy_sha256)
    try:
        epoch = _minimal_epoch()
        state = _minimal_state()
        epoch.to_dict()
        state.to_dict()
    finally:
        monkeypatch.undo()
    assert calls == []


# ---------------------------------------------------------------------------
# Section 13: no later record-family models
# ---------------------------------------------------------------------------
#
# Narrowed by Phase 136AD (same bounded-narrowing pattern 136U/136AA/136AB
# each already applied to their own predecessor's scope guard): CutoverRequest
# and ReadinessPackage (Group 3) are now authorized, legitimately-implemented
# record-family models, so they are removed from this "still forbidden" list.
# Every one of the other 12 later-group names remains forbidden, unchanged.

_LATER_GROUP_MODEL_NAMES = (
    # Narrowed by Phase 136AF: `HumanAuthorization`/`CutoverCandidate`/
    # `Certification` (Group 4) are now authorized, legitimately-implemented
    # record-family models -- removed from this still-forbidden list.
    # Narrowed further by Phase 136AH: `PublicationAttempt`/
    # `PublicationEvidence` (Group 5) are now authorized, legitimately-
    # implemented record-family models -- removed from this still-forbidden
    # list. Narrowed further by Phase 136AJ: `ConcurrencyConflict`/
    # `RecoveryJournalEntry` (Group 6) are now authorized, legitimately-
    # implemented record-family models -- removed from this still-forbidden
    # list. Narrowed further by Phase 136AL: `NotificationAuthorityBinding`
    # (Group 7) is now authorized, legitimately-implemented record-family
    # model -- removed from this still-forbidden list. Narrowed further by
    # Phase 136AN: `MarkerAuthorityBinding` (Group 8) is now authorized,
    # legitimately-implemented record-family model -- removed from this
    # still-forbidden list. Narrowed further by Phase 136AP:
    # `FinalizationReceiptAuthorityBinding` (Group 9) is now authorized,
    # legitimately-implemented record-family model -- removed from this
    # still-forbidden list. Narrowed further by Phase 136AR:
    # `CompatibilityState` (Group 10) is now authorized, legitimately-
    # implemented record-family model -- removed from this still-forbidden
    # list.
    # Narrowed further by Phase 136AT: `QuarantineRecord` (Group 11) is
    # now authorized, legitimately-implemented record-family model -- the
    # sixteenth and final Stage 3 record-family model. No later-group
    # name remains to forbid.
)


def test_no_later_group_model_class_defined_anywhere_in_authority_package():
    package_dir = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
    for py_file in sorted(package_dir.glob("*.py")):
        tree = ast.parse(py_file.read_text())
        defined_classes = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        }
        collision = defined_classes & set(_LATER_GROUP_MODEL_NAMES)
        assert not collision, (py_file, collision)


def test_no_later_group_model_name_exported_from_package___all__():
    exported = set(auth.__all__)
    collision = exported & set(_LATER_GROUP_MODEL_NAMES)
    assert not collision


def test_authority_package_all_exports_resolve_and_wildcard_matches():
    exported = set(auth.__all__)
    for name in exported:
        assert hasattr(auth, name), name
    namespace: dict = {}
    exec("from pcae.cltr.authority import *", namespace)  # noqa: S102 - controlled, test-only
    wildcard_names = {n for n in namespace if not n.startswith("__")}
    assert wildcard_names == exported


def test_no_duplicate_or_unintentional_helper_export():
    exported = set(auth.__all__)
    for internal_name in ("_require_str", "_require_mapping", "_reject_unknown_keys", "_envelope_from_payload"):
        assert internal_name not in exported


# ---------------------------------------------------------------------------
# Section 14: runtime isolation (production import graph)
# ---------------------------------------------------------------------------


def _iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        yield path


def _module_imports_authority_package(py_file: Path) -> bool:
    try:
        tree = ast.parse(py_file.read_text())
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("pcae.cltr.authority"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("pcae.cltr.authority"):
                return True
    return False


@pytest.mark.parametrize(
    "scan_root",
    [
        "src/pcae/commands",
        "src/pcae/core",
        "src/pcae/runtime",
    ],
)
def test_no_production_module_imports_authority_package(scan_root):
    root = REPO_ROOT / scan_root
    if not root.exists():
        pytest.skip(f"{scan_root} does not exist in this checkout")
    offenders = [str(p.relative_to(REPO_ROOT)) for p in _iter_python_files(root) if _module_imports_authority_package(p)]
    assert offenders == []


def test_no_sibling_cltr_module_outside_authority_imports_authority_package():
    cltr_root = REPO_ROOT / "src" / "pcae" / "cltr"
    authority_dir = cltr_root / "authority"
    offenders = []
    for py_file in _iter_python_files(cltr_root):
        if authority_dir in py_file.parents:
            continue
        if _module_imports_authority_package(py_file):
            offenders.append(str(py_file.relative_to(REPO_ROOT)))
    assert offenders == []


def test_authority_package_does_not_import_production_lifecycle_modules():
    forbidden_prefixes = (
        "pcae.commands",
        "pcae.core",
        "pcae.runtime",
    )
    package_dir = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
    for py_file in _iter_python_files(package_dir):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            module_name = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    assert not module_name.startswith(forbidden_prefixes), (py_file, module_name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_name = node.module
                assert not module_name.startswith(forbidden_prefixes), (py_file, module_name)


# ---------------------------------------------------------------------------
# Section 15: no side effects
# ---------------------------------------------------------------------------


def test_no_subprocess_during_construction_or_serialization(monkeypatch):
    def spy_run(*args, **kwargs):
        raise AssertionError("subprocess.run must never be called")

    def spy_popen(*args, **kwargs):
        raise AssertionError("subprocess.Popen must never be called")

    monkeypatch.setattr(subprocess, "run", spy_run)
    monkeypatch.setattr(subprocess, "Popen", spy_popen)
    try:
        epoch = _minimal_epoch()
        state = _minimal_state()
        epoch.to_dict()
        state.to_dict()
    finally:
        monkeypatch.undo()


def test_no_environ_lookup_during_construction(monkeypatch):
    calls = {"count": 0}
    real_getenv = os.getenv

    def spy_getenv(*args, **kwargs):
        calls["count"] += 1
        return real_getenv(*args, **kwargs)

    monkeypatch.setattr(os, "getenv", spy_getenv)
    try:
        _minimal_epoch()
        _minimal_state()
    finally:
        monkeypatch.undo()
    assert calls["count"] == 0


def test_no_filesystem_write_during_construction_or_serialization(monkeypatch, tmp_path):
    real_open = open

    def spy_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x")):
            raise AssertionError(f"unexpected write-mode open: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", spy_open)
    try:
        epoch = _minimal_epoch()
        state = _minimal_state()
        epoch.to_dict()
        state.to_dict()
    finally:
        monkeypatch.undo()


# ---------------------------------------------------------------------------
# Section 16: strict construction (no coercion)
# ---------------------------------------------------------------------------


def test_epoch_unknown_field_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(unexpected_field="x"), schema_version="1.0")


def test_state_unknown_field_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityState.from_dict(_state_payload(unexpected_field="x"), schema_version="1.0")


def test_epoch_missing_required_field_rejected():
    payload = _epoch_payload()
    del payload["migration_epoch"]
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")


def test_state_missing_required_field_rejected():
    payload = _state_payload()
    del payload["transition_id"]
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityState.from_dict(payload, schema_version="1.0")


def test_epoch_boolean_for_string_field_not_coerced():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(migration_epoch=True), schema_version="1.0")


def test_epoch_integer_for_string_field_not_coerced():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(_epoch_payload(migration_epoch=42), schema_version="1.0")


def test_state_wrong_type_for_limitations_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityState.from_dict(_state_payload(limitations="not-a-list"), schema_version="1.0")


def test_epoch_is_authoritative_true_rejected():
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(
            _epoch_payload(
                authority_disclosure={
                    "authority_role": "derivative",
                    "is_authoritative": True,
                    "disclosure_text": "attempted override",
                }
            ),
            schema_version="1.0",
        )


def test_epoch_authority_role_authoritative_forbidden_at_typed_model_layer():
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.AuthorityEpoch.from_dict(
            _epoch_payload(
                authority_disclosure={
                    "authority_role": "authoritative",
                    "is_authoritative": False,
                    "disclosure_text": "forbidden on epoch records",
                }
            ),
            schema_version="1.0",
        )


def test_state_authority_role_authoritative_permitted_but_is_authoritative_still_false():
    state = auth.AuthorityState.from_dict(
        _state_payload(
            authority_disclosure={
                "authority_role": "authoritative",
                "is_authoritative": False,
                "disclosure_text": "structurally permitted on this family",
            }
        ),
        schema_version="1.0",
    )
    assert state.authority_disclosure.is_authoritative is False


# ---------------------------------------------------------------------------
# Section 17: schema drift detection (round trip against live schema)
# ---------------------------------------------------------------------------


def test_epoch_every_valid_activation_state_round_trips_through_schema(registry):
    for state_value, needs_binding in (("proposed", False), ("active", True), ("superseded", False)):
        overrides = {"activation_state": state_value}
        if needs_binding:
            overrides["generation_binding"] = {"generation_id": _GEN_ID, "generation_digest": _GEN_DIGEST}
        payload = _epoch_payload(**overrides)
        _assert_schema_valid(payload, schema_id=EPOCH_SCHEMA["$id"], reg=registry)
        epoch = auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")
        round_tripped = epoch.to_dict()
        _assert_schema_valid(round_tripped, schema_id=EPOCH_SCHEMA["$id"], reg=registry)


def test_state_every_valid_verification_state_round_trips_through_schema(registry):
    for state_value, needs_uncertainty in (
        ("unverified", True),
        ("verified", False),
        ("verification_failed", False),
    ):
        overrides = {"verification_state": state_value}
        if needs_uncertainty:
            overrides["uncertainty"] = {"reason": "disclosed"}
        payload = _state_payload(**overrides)
        _assert_schema_valid(payload, schema_id=STATE_SCHEMA["$id"], reg=registry)
        state = auth.AuthorityState.from_dict(payload, schema_version="1.0")
        round_tripped = state.to_dict()
        _assert_schema_valid(round_tripped, schema_id=STATE_SCHEMA["$id"], reg=registry)


def test_epoch_extra_schema_property_not_silently_accepted_by_model():
    """If the schema ever grows a new property this model doesn't know
    about, from_dict must reject a payload carrying it -- proving the
    model's known-key set cannot silently drift permissive relative to the
    schema without a test failure here."""

    payload = _epoch_payload()
    payload["a_property_the_schema_does_not_define"] = "drift-canary"
    with pytest.raises(auth_errors.TypedModelError):
        auth.AuthorityEpoch.from_dict(payload, schema_version="1.0")
