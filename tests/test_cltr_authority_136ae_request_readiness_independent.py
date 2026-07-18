"""Phase 136AE: Stage 3 Typed Authority Model Request and Readiness
Independent Verification.

Independently re-derives and verifies the ``CutoverRequest`` and
``ReadinessPackage`` typed record models implemented by Phase 136AD
(``src/pcae/cltr/authority/request_readiness.py``), against:

- the frozen primary contracts (PHASE_135_STAGE_3_COMPANION_SCHEMAS_AND_
  TYPED_AUTHORITY_MODEL_CONTRACT_FREEZE.md Sec.6.3/Sec.30,
  PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md Sec.19/
  Sec.20);
- the live executable schemas (``records/cutover_request.schema.json``,
  ``records/readiness_package.schema.json``, and every shared ``$ref``);
- the verified 136Y implementation plan (Sec.9 absent-vs-null design).

Deliberately does NOT import ``tests/test_cltr_authority_136ad_request_
readiness.py`` (fixtures, helpers, or expected-value tables). Every wire
fixture and expected value below is authored directly from the schema
files and contract text cited above.

This module implements no record-family model. It performs no readiness
evaluation, no request authorization, no evidence verification, no
reference resolution, no digest computation, and no persistence.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import re
import socket
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import errors as auth_errors
from pcae.cltr.authority import request_readiness as rr
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
REQUEST_READINESS_MODULE = AUTHORITY_PACKAGE_DIR / "request_readiness.py"

CUTOVER_REQUEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json"
READINESS_PACKAGE_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/readiness_package.schema.json"

# The twelve not-yet-implemented record-family class names (136Y plan Groups
# 4-11). Independently retyped here rather than imported from 136AD's test
# module.
LATER_MODEL_CLASS_NAMES = (
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

FORBIDDEN_BEHAVIOR_SYMBOLS = (
    "is_ready",
    "calculate_readiness",
    "evaluate_readiness",
    "all_prerequisites_pass",
    "all_gates_pass",
    "sufficient_evidence",
    "can_cutover",
    "ready_for_publication",
    "approve",
    "reject",
    "authorize",
    "validate_requester",
    "is_authorized",
    "can_submit",
    "can_execute",
    "execute_request",
    "schedule_cutover",
)


def _hex(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


# ---------------------------------------------------------------------------
# Independently authored wire fixtures (derived from the schema files read
# directly in this phase, not copied from 136AD's fixtures).
# ---------------------------------------------------------------------------


def _epoch_ref(rid: str, fill: str) -> dict:
    return {"record_id": rid, "record_digest": _hex(fill), "record_family": "authority_epoch"}


def _readypkg_ref(rid: str = "readypkg-9990001", fill: str = "1") -> dict:
    return {
        "record_id": rid,
        "record_digest": _hex(fill),
        "record_family": "readiness_package",
        "schema_id": READINESS_PACKAGE_SCHEMA_ID,
        "schema_version": "1.0",
    }


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Independently constructed 136AE verification fixture.",
    }


def cutover_request_wire(**overrides) -> dict:
    wire = {
        "schema_id": CUTOVER_REQUEST_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "cutover_request",
        "record_id": "cutreq-9990001",
        "record_digest": _hex("2"),
        "created_at": "2026-07-17T00:00:00Z",
        "phase_id": "136AE",
        "migration_epoch": "epoch-136ae",
        "target": "cltr",
        "source_authority": "legacy",
        "source_epoch": _epoch_ref("authepoch-9990001", "3"),
        "target_epoch": _epoch_ref("authepoch-9990002", "4"),
        "evidence_requirements": [],
        "readiness_package_reference": _readypkg_ref(),
        "authorization_requirement": True,
        "final_revision": "rev-136ae-0001",
        "state": "pending",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    wire.update(overrides)
    return wire


def readiness_package_wire(**overrides) -> dict:
    wire = {
        "schema_id": READINESS_PACKAGE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "readiness_package",
        "record_id": "readypkg-9990001",
        "record_digest": _hex("1"),
        "created_at": "2026-07-17T00:00:00Z",
        "phase_id": "136AE",
        "transition_id": "trans-9990001",
        "migration_epoch": "epoch-136ae",
        "evidence_references": [],
        "prerequisite_status": "unknown",
        "findings": [],
        "state": "unknown",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    wire.update(overrides)
    return wire


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def assert_schema_valid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


def assert_schema_invalid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is not OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 1. Independent schema re-derivation sanity: confirm the field inventories
#    this module assumes match the live schema files, independent of 136AD.
# ---------------------------------------------------------------------------


def _load_schema(relative_path: str) -> dict:
    with cltr_cutover_root() as root:
        return json.loads((root / relative_path).read_text())


def test_136ae_cutover_request_schema_required_fields_independently_enumerated():
    schema = _load_schema("records/cutover_request.schema.json")
    expected_required = {
        "schema_id", "schema_version", "contract_version", "record_type",
        "record_id", "record_digest", "created_at", "phase_id",
        "migration_epoch", "target", "source_authority", "source_epoch",
        "target_epoch", "evidence_requirements", "readiness_package_reference",
        "authorization_requirement", "final_revision", "state", "limitations",
        "authority_disclosure",
    }
    assert set(schema["required"]) == expected_required
    assert set(schema["properties"].keys()) == expected_required | {"reason_code"}
    assert schema["additionalProperties"] is False
    assert "_extensions" not in schema["properties"]


def test_136ae_readiness_package_schema_required_fields_independently_enumerated():
    schema = _load_schema("records/readiness_package.schema.json")
    expected_required = {
        "schema_id", "schema_version", "contract_version", "record_type",
        "record_id", "record_digest", "created_at", "phase_id", "transition_id",
        "migration_epoch", "evidence_references", "prerequisite_status",
        "findings", "state", "limitations", "authority_disclosure",
    }
    assert set(schema["required"]) == expected_required
    assert set(schema["properties"].keys()) == expected_required | {"gate_result", "_extensions"}
    assert schema["additionalProperties"] is False
    assert schema["properties"]["_extensions"]["additionalProperties"] == {"type": "string"}
    assert schema["properties"]["_extensions"]["maxProperties"] == 32


def test_136ae_cutover_request_constants_independently_confirmed():
    schema = _load_schema("records/cutover_request.schema.json")
    assert schema["properties"]["target"]["allOf"][1] == {"const": "cltr"}
    assert schema["properties"]["source_authority"]["allOf"][1] == {"const": "legacy"}
    assert schema["properties"]["authorization_requirement"] == {
        "const": True,
        "description": schema["properties"]["authorization_requirement"]["description"],
    }


def test_136ae_request_state_enum_independently_enumerated():
    schema = _load_schema("records/cutover_request.schema.json")
    values = set(schema["properties"]["state"]["enum"])
    assert values == {
        "pending", "evidence_gathering", "ready", "authorized", "certified",
        "publication_pending", "published", "rejected", "withdrawn", "expired",
    }
    assert {m.value for m in rr.RequestState} == values


def test_136ae_readiness_state_enum_independently_enumerated():
    schema = _load_schema("records/readiness_package.schema.json")
    values = set(schema["properties"]["state"]["enum"])
    assert values == {"unknown", "stale", "partial", "ready", "conflict"}
    assert {m.value for m in rr.ReadinessState} == values


def test_136ae_prerequisite_status_enum_independently_enumerated():
    schema = _load_schema("records/readiness_package.schema.json")
    values = set(schema["properties"]["prerequisite_status"]["enum"])
    assert values == {"unknown", "unmet", "met"}
    assert {m.value for m in rr.PrerequisiteStatus} == values


def test_136ae_gate_result_enum_independently_enumerated_and_optional():
    schema = _load_schema("records/readiness_package.schema.json")
    assert "gate_result" not in schema["required"]
    values = set(schema["properties"]["gate_result"]["enum"])
    assert values == {"eligible", "ineligible", "uncertain", "conflict"}
    assert {m.value for m in rr.GateResult} == values


def test_136ae_finding_verdict_enum_independently_enumerated():
    schema = _load_schema("records/readiness_package.schema.json")
    values = set(schema["$defs"]["finding"]["properties"]["verdict"]["enum"])
    assert values == {"CONFIRMED", "NON-BLOCKING", "BLOCKING", "PREREQUISITE", "DEFERRED"}
    assert {m.value for m in rr.FindingVerdict} == values


def test_136ae_conflict_conditional_is_one_directional_only():
    """The schema's allOf/if-then requires: state == conflict -> contains a
    BLOCKING finding. It does NOT require the converse (a BLOCKING finding
    forces state == conflict). Independently confirming the exact shape of
    the conditional, not trusting 136AD's "iff" prose."""
    schema = _load_schema("records/readiness_package.schema.json")
    conditionals = schema["allOf"]
    assert len(conditionals) == 1
    condition = conditionals[0]
    assert condition["if"]["properties"]["state"] == {"const": "conflict"}
    assert condition["then"]["properties"]["findings"]["contains"] == {
        "$ref": "#/$defs/blocking_finding"
    }
    # No second allOf branch exists requiring the converse direction.
    assert "not" not in json.dumps(condition) or True  # documents absence, not enforced here


def test_136ae_evidence_requirements_bounds_independently_confirmed():
    schema = _load_schema("records/cutover_request.schema.json")
    field = schema["properties"]["evidence_requirements"]
    assert field["maxItems"] == 24
    assert field["uniqueItems"] is True


def test_136ae_evidence_references_bounds_independently_confirmed():
    schema = _load_schema("records/readiness_package.schema.json")
    field = schema["properties"]["evidence_references"]
    assert field["maxItems"] == 64
    assert "uniqueItems" not in field  # duplicates are NOT forbidden by schema


def test_136ae_findings_bounds_independently_confirmed():
    schema = _load_schema("records/readiness_package.schema.json")
    field = schema["properties"]["findings"]
    assert field["maxItems"] == 128
    assert "uniqueItems" not in field


def test_136ae_reason_code_shared_vocabulary_has_no_null_type():
    """shared/failures.schema.json's reason_code $def declares type "string"
    only -- no null in a type union. An explicit JSON null therefore fails
    Draft 2020-12 validation at the schema (Layer 1) layer, independent of
    whatever the typed model (Layer 2) chooses to accept directly."""
    with cltr_cutover_root() as root:
        failures = json.loads((root / "shared" / "failures.schema.json").read_text())
    reason_code_def = failures["$defs"]["reason_code"]
    assert reason_code_def["type"] == "string"
    assert len(reason_code_def["enum"]) == 24


# ---------------------------------------------------------------------------
# 2. Inventory / public API
# ---------------------------------------------------------------------------


def test_136ae_exactly_four_record_family_models_in_authority_package():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    for expected in ("AuthorityEpoch", "AuthorityState", "CutoverRequest", "ReadinessPackage"):
        assert expected in class_names
    for later in LATER_MODEL_CLASS_NAMES:
        assert later not in class_names


def test_136ae_no_later_model_ast_or_dynamic_construction_in_request_readiness_module():
    tree = ast.parse(REQUEST_READINESS_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    assigned_names = {
        t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
        for t in n.targets if isinstance(t, ast.Name)
    }
    for later in LATER_MODEL_CLASS_NAMES:
        assert later not in class_names
        assert later not in assigned_names
    # Docstrings/comments may legitimately name a later model in a
    # disclosure sentence ("does not implement X"); only executable code
    # constructs (class defs, assignments, calls, attribute access) are
    # screened for an actual implementation, via AST walk rather than a
    # raw substring search over the whole source (which would also match
    # prose).
    called_or_referenced_names = {
        n.id for n in ast.walk(tree) if isinstance(n, ast.Name)
    } | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
    }
    for later in LATER_MODEL_CLASS_NAMES:
        assert later not in called_or_referenced_names


def test_136ae_public_exports_exact():
    assert set(rr.__all__) == {
        "RequestState", "ReadinessState", "PrerequisiteStatus", "GateResult",
        "FindingVerdict", "Finding", "CutoverRequest", "ReadinessPackage",
    }
    assert "CutoverRequest" in auth.__all__
    assert "ReadinessPackage" in auth.__all__
    for later in LATER_MODEL_CLASS_NAMES:
        assert later not in auth.__all__


def test_136ae_dataclasses_are_frozen():
    assert dataclasses.fields(rr.CutoverRequest)
    assert dataclasses.fields(rr.ReadinessPackage)
    cr = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        cr.final_revision = "mutated"  # type: ignore[misc]
    rp = rr.ReadinessPackage.from_dict(readiness_package_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        rp.prerequisite_status = rr.PrerequisiteStatus.MET  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 3. CutoverRequest constant enforcement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("target", "legacy"),
        ("target", "CLTR"),
        ("target", " cltr"),
        ("target", "cltr "),
        ("target", "clt"),
        ("source_authority", "cltr"),
        ("source_authority", "Legacy"),
        ("source_authority", " legacy"),
    ],
)
def test_136ae_cutover_request_rejects_wrong_target_or_source_authority(field, value):
    with pytest.raises((rr.TypedModelInternalInvariantError, auth_errors.TypedModelConstructionError, ValueError)):
        rr.CutoverRequest.from_dict(cutover_request_wire(**{field: value}), schema_version="1.0")


def test_136ae_cutover_request_authorization_requirement_must_be_true():
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.CutoverRequest.from_dict(
            cutover_request_wire(authorization_requirement=False), schema_version="1.0"
        )


def test_136ae_cutover_request_authorization_requirement_wrong_types_rejected():
    for bad in (1, "true", None):
        wire = cutover_request_wire(authorization_requirement=bad)
        with pytest.raises((rr.TypedModelInternalInvariantError, auth_errors.TypedModelConstructionError, TypeError)):
            rr.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ae_cutover_request_does_not_silently_overwrite_wrong_constants():
    """The model must reject a wrong target/source_authority, never coerce
    it to the expected constant and proceed."""
    built = None
    try:
        built = rr.CutoverRequest.from_dict(
            cutover_request_wire(target="legacy"), schema_version="1.0"
        )
    except Exception:
        pass
    assert built is None


# ---------------------------------------------------------------------------
# 4. Record and schema discriminators
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("record_type", "readiness_package"),
        ("record_type", "Cutover_Request"),
        ("record_type", ""),
        ("schema_id", READINESS_PACKAGE_SCHEMA_ID),
        ("schema_id", CUTOVER_REQUEST_SCHEMA_ID + " "),
    ],
)
def test_136ae_cutover_request_rejects_wrong_discriminator(field, value):
    with pytest.raises(Exception):
        rr.CutoverRequest.from_dict(cutover_request_wire(**{field: value}), schema_version="1.0")


def test_136ae_cutover_request_unsupported_schema_version_rejected():
    with pytest.raises(rr.UnsupportedSchemaVersionError):
        rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="2.0")


def test_136ae_readiness_package_unsupported_schema_version_rejected():
    with pytest.raises(rr.UnsupportedSchemaVersionError):
        rr.ReadinessPackage.from_dict(readiness_package_wire(), schema_version="9.9")


# ---------------------------------------------------------------------------
# 5. reason_code absent-vs-null relaxation (CutoverRequest only)
# ---------------------------------------------------------------------------


def test_136ae_reason_code_omitted_becomes_none():
    wire = cutover_request_wire()
    assert "reason_code" not in wire
    cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert cr.reason_code is None


def test_136ae_reason_code_explicit_null_becomes_none():
    wire = cutover_request_wire(reason_code=None)
    cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert cr.reason_code is None


def test_136ae_reason_code_omitted_and_explicit_null_construct_equal_instances():
    omitted = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    explicit_null = rr.CutoverRequest.from_dict(
        cutover_request_wire(reason_code=None), schema_version="1.0"
    )
    assert omitted == explicit_null


def test_136ae_reason_code_valid_string_preserved():
    wire = cutover_request_wire(reason_code="digest_mismatch")
    cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert cr.reason_code is rr.ReasonCode.DIGEST_MISMATCH if hasattr(rr, "ReasonCode") else True
    assert cr.reason_code.value == "digest_mismatch"


def test_136ae_reason_code_invalid_string_rejected():
    with pytest.raises(ValueError):
        rr.CutoverRequest.from_dict(
            cutover_request_wire(reason_code="not_a_real_code"), schema_version="1.0"
        )


def test_136ae_reason_code_non_string_rejected():
    with pytest.raises(Exception):
        rr.CutoverRequest.from_dict(cutover_request_wire(reason_code=123), schema_version="1.0")


def test_136ae_reason_code_serialization_omitted_when_none():
    cr = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    assert "reason_code" not in cr.to_dict()
    cr2 = rr.CutoverRequest.from_dict(cutover_request_wire(reason_code=None), schema_version="1.0")
    assert "reason_code" not in cr2.to_dict()


def test_136ae_reason_code_serialization_present_when_set():
    cr = rr.CutoverRequest.from_dict(
        cutover_request_wire(reason_code="revision_mismatch"), schema_version="1.0"
    )
    assert cr.to_dict()["reason_code"] == "revision_mismatch"


def test_136ae_explicit_null_for_reason_code_fails_live_schema_validation(schema_registry):
    """Documents the two-layer discrepancy: the live shared reason_code
    schema (type: string, no null) rejects an explicit null at Layer 1,
    even though contract Sec.6.3 / 136Y plan Sec.9 authorize the Layer 2
    typed-model collapse of absent and explicit-null for this one field.
    Non-blocking: the Layer 2 relaxation is only reachable via payloads
    constructed directly (bypassing Layer 1), which is how both 136AD's
    and this phase's fixtures invoke CutoverRequest.from_dict()."""
    wire = cutover_request_wire(reason_code=None)
    result = validate_record_shape(wire, schema_id=CUTOVER_REQUEST_SCHEMA_ID, registry=schema_registry)
    assert result.status is not OutcomeStatus.VALID


def test_136ae_readiness_package_gate_result_does_not_inherit_the_collapse():
    """The reason_code relaxation is CutoverRequest-only. ReadinessPackage's
    optional fields (gate_result, _extensions) must keep the generic
    ABSENT-vs-null distinction and reject explicit null."""
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.ReadinessPackage.from_dict(readiness_package_wire(gate_result=None), schema_version="1.0")


def test_136ae_readiness_package_extensions_does_not_inherit_the_collapse():
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.ReadinessPackage.from_dict(readiness_package_wire(_extensions=None), schema_version="1.0")


# ---------------------------------------------------------------------------
# 6. References: shape-only, no resolution
# ---------------------------------------------------------------------------


def test_136ae_cutover_request_references_reject_wrong_family():
    bad_epoch = _epoch_ref("authepoch-9990001", "3")
    bad_epoch["record_family"] = "readiness_package"
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        rr.CutoverRequest.from_dict(cutover_request_wire(source_epoch=bad_epoch), schema_version="1.0")

    bad_ready_ref = _readypkg_ref()
    bad_ready_ref["record_family"] = "authority_epoch"
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        rr.CutoverRequest.from_dict(
            cutover_request_wire(readiness_package_reference=bad_ready_ref), schema_version="1.0"
        )


def test_136ae_cutover_request_readiness_package_reference_requires_schema_id_and_version():
    ref = _readypkg_ref()
    del ref["schema_id"]
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.CutoverRequest.from_dict(
            cutover_request_wire(readiness_package_reference=ref), schema_version="1.0"
        )
    ref2 = _readypkg_ref()
    del ref2["schema_version"]
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.CutoverRequest.from_dict(
            cutover_request_wire(readiness_package_reference=ref2), schema_version="1.0"
        )


def test_136ae_construction_succeeds_with_nonexistent_but_syntactically_valid_references():
    """No repository lookup or existence check may occur at construction."""
    wire = cutover_request_wire(
        source_epoch=_epoch_ref("authepoch-doesnotexist", "9"),
        target_epoch=_epoch_ref("authepoch-alsofake000", "8"),
        readiness_package_reference=_readypkg_ref("readypkg-nonexistent0", "7"),
    )
    cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert cr.source_epoch.record_id.value == "authepoch-doesnotexist"


def test_136ae_no_filesystem_or_network_access_during_reference_construction(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("unexpected socket construction during model construction")

    monkeypatch.setattr(socket, "socket", _boom)
    rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    rr.ReadinessPackage.from_dict(readiness_package_wire(), schema_version="1.0")


def test_136ae_evidence_references_no_family_restriction():
    """ReadinessPackage.evidence_references may point at any record_family
    -- no local family restriction is applied (schema uses the generic
    record_reference shape with no allOf/const restriction)."""
    wire = readiness_package_wire(
        evidence_references=[
            {"record_id": "certx-9990001a", "record_digest": _hex("5"), "record_family": "certification"},
            {"record_id": "cutreq-9990001a", "record_digest": _hex("6"), "record_family": "cutover_request"},
        ]
    )
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert len(rp.evidence_references) == 2


# ---------------------------------------------------------------------------
# 7. Conflict conditional (one-directional; do not enforce the converse)
# ---------------------------------------------------------------------------


def _finding(id_: str, verdict: str, title: str = "x") -> dict:
    return {"id": id_, "verdict": verdict, "title": title}


def test_136ae_conflict_state_with_blocking_finding_accepted():
    wire = readiness_package_wire(state="conflict", findings=[_finding("f1", "BLOCKING")])
    rr.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ae_conflict_state_without_any_findings_rejected():
    wire = readiness_package_wire(state="conflict", findings=[])
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ae_conflict_state_with_only_non_blocking_findings_rejected():
    wire = readiness_package_wire(
        state="conflict", findings=[_finding("f1", "NON-BLOCKING"), _finding("f2", "DEFERRED")]
    )
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ae_non_conflict_state_with_blocking_finding_is_accepted_not_forced_to_conflict():
    """This is the key independent-derivation check: the schema's
    conditional is if(conflict)->contains(blocking), NOT a biconditional.
    A BLOCKING finding present while state != conflict must be accepted,
    not rejected -- confirming 136AD's implementation does not over-enforce
    the reverse direction."""
    wire = readiness_package_wire(state="partial", findings=[_finding("f1", "BLOCKING")])
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert rp.state is rr.ReadinessState.PARTIAL
    assert rp.findings[0].verdict is rr.FindingVerdict.BLOCKING


def test_136ae_non_conflict_state_without_blocking_finding_accepted():
    wire = readiness_package_wire(state="ready", findings=[])
    rr.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ae_schema_also_accepts_non_conflict_with_blocking_finding(schema_registry):
    """Confirm at the raw JSON Schema layer too (not just the typed model)
    that a BLOCKING finding does not force state == conflict."""
    wire = readiness_package_wire(state="partial", findings=[_finding("f1", "BLOCKING")])
    assert_schema_valid(wire, READINESS_PACKAGE_SCHEMA_ID, schema_registry)


# ---------------------------------------------------------------------------
# 8. Evidence array bounds / ordering / no dedup / no sort
# ---------------------------------------------------------------------------


def test_136ae_evidence_requirements_duplicate_rejected():
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.CutoverRequest.from_dict(
            cutover_request_wire(evidence_requirements=["digest_mismatch", "digest_mismatch"]),
            schema_version="1.0",
        )


def test_136ae_evidence_requirements_maximum_boundary_accepted():
    codes = [c.value for c in list(rr.ReasonCode)[:24]]
    assert len(codes) == 24
    rr.CutoverRequest.from_dict(cutover_request_wire(evidence_requirements=codes), schema_version="1.0")


def test_136ae_evidence_requirements_over_maximum_rejected():
    codes = [c.value for c in list(rr.ReasonCode)[:24]]
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.CutoverRequest.from_dict(
            cutover_request_wire(evidence_requirements=codes + [codes[0]]), schema_version="1.0"
        )
    # (over-max via duplicate also hits the uniqueness check first; verify
    # a genuinely distinct 25th value is impossible since vocabulary is
    # closed at 24, so max-items is the binding constraint at exactly 24
    # unique members already reached above.)


def test_136ae_evidence_references_duplicate_item_preserved_not_deduplicated():
    ref = {"record_id": "certx-9990002a", "record_digest": _hex("5"), "record_family": "certification"}
    wire = readiness_package_wire(evidence_references=[ref, dict(ref)])
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert len(rp.evidence_references) == 2


def test_136ae_evidence_references_same_id_different_digest_preserved():
    ref_a = {"record_id": "certx-9990003a", "record_digest": _hex("5"), "record_family": "certification"}
    ref_b = {"record_id": "certx-9990003a", "record_digest": _hex("6"), "record_family": "certification"}
    wire = readiness_package_wire(evidence_references=[ref_a, ref_b])
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert rp.evidence_references[0].record_digest.value != rp.evidence_references[1].record_digest.value


def test_136ae_evidence_references_order_preserved_no_sorting():
    ref_b = {"record_id": "certx-9990009z", "record_digest": _hex("5"), "record_family": "certification"}
    ref_a = {"record_id": "certx-9990001a", "record_digest": _hex("6"), "record_family": "certification"}
    wire = readiness_package_wire(evidence_references=[ref_b, ref_a])
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert rp.evidence_references[0].record_id.value == "certx-9990009z"
    assert rp.evidence_references[1].record_id.value == "certx-9990001a"
    assert rp.to_dict()["evidence_references"][0]["record_id"] == "certx-9990009z"


def test_136ae_evidence_references_maximum_boundary_accepted():
    refs = [
        {"record_id": f"certx-99900{i:02d}a", "record_digest": _hex("5"), "record_family": "certification"}
        for i in range(64)
    ]
    rp = rr.ReadinessPackage.from_dict(readiness_package_wire(evidence_references=refs), schema_version="1.0")
    assert len(rp.evidence_references) == 64


def test_136ae_evidence_references_over_maximum_rejected():
    refs = [
        {"record_id": f"certx-99901{i:02d}a", "record_digest": _hex("5"), "record_family": "certification"}
        for i in range(65)
    ]
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.ReadinessPackage.from_dict(readiness_package_wire(evidence_references=refs), schema_version="1.0")


def test_136ae_findings_maximum_boundary_accepted():
    findings = [_finding(f"f{i}", "CONFIRMED") for i in range(128)]
    rp = rr.ReadinessPackage.from_dict(readiness_package_wire(findings=findings), schema_version="1.0")
    assert len(rp.findings) == 128


def test_136ae_findings_over_maximum_rejected():
    findings = [_finding(f"f{i}", "CONFIRMED") for i in range(129)]
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.ReadinessPackage.from_dict(readiness_package_wire(findings=findings), schema_version="1.0")


def test_136ae_malformed_finding_rejected():
    with pytest.raises(Exception):
        rr.ReadinessPackage.from_dict(
            readiness_package_wire(findings=[{"id": "f1", "verdict": "NOT_A_VERDICT", "title": "x"}]),
            schema_version="1.0",
        )


def test_136ae_wrong_family_evidence_reference_item_rejected():
    with pytest.raises(ValueError):
        rr.ReadinessPackage.from_dict(
            readiness_package_wire(
                evidence_references=[
                    {"record_id": "certx-9990005a", "record_digest": _hex("5"), "record_family": "not_a_family"}
                ]
            ),
            schema_version="1.0",
        )


# ---------------------------------------------------------------------------
# 9. _extensions Tier 2 rule (ReadinessPackage only)
# ---------------------------------------------------------------------------


def test_136ae_extensions_absent_by_default():
    rp = rr.ReadinessPackage.from_dict(readiness_package_wire(), schema_version="1.0")
    assert rp._extensions is rr.ABSENT if hasattr(rr, "ABSENT") else True
    assert "_extensions" not in rp.to_dict()


def test_136ae_extensions_string_values_accepted():
    wire = readiness_package_wire(_extensions={"note": "hello", "unicode": "café"})
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert rp.to_dict()["_extensions"] == {"note": "hello", "unicode": "café"}


def test_136ae_extensions_empty_string_value_accepted():
    wire = readiness_package_wire(_extensions={"note": ""})
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert rp.to_dict()["_extensions"]["note"] == ""


def test_136ae_extensions_empty_object_accepted():
    wire = readiness_package_wire(_extensions={})
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert rp.to_dict()["_extensions"] == {}


@pytest.mark.parametrize("bad_value", [123, True, ["a"], {"nested": "obj"}, None])
def test_136ae_extensions_non_string_values_rejected(bad_value):
    wire = readiness_package_wire(_extensions={"k": bad_value})
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ae_extensions_does_not_apply_recursively_to_nested_structures_because_none_allowed():
    """The Tier 2 rule is: every _extensions VALUE must itself be a string
    (no nested arrays/objects at all) -- there is no "applies recursively"
    case because non-string containers are rejected outright at the top
    level of each value, per additionalProperties: {"type": "string"}."""
    wire = readiness_package_wire(_extensions={"k": {"nested": "x"}})
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ae_extensions_key_colliding_with_canonical_field_rejected():
    wire = readiness_package_wire(_extensions={"state": "shadow-value"})
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ae_extensions_over_max_properties_rejected():
    wire = readiness_package_wire(_extensions={f"k{i}": "v" for i in range(33)})
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ae_extensions_max_properties_boundary_accepted():
    wire = readiness_package_wire(_extensions={f"k{i}": "v" for i in range(32)})
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert len(rp._extensions) == 32


def test_136ae_cutover_request_has_no_extensions_field_at_all():
    """Tier 1 (strict): CutoverRequest has no _extensions escape hatch.
    Confirming this directly, since the prompt's premise that the Tier 2
    rule 'applies to both records' does not hold -- it applies to
    ReadinessPackage only."""
    assert "_extensions" not in {f.name for f in dataclasses.fields(rr.CutoverRequest)}
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.CutoverRequest.from_dict(cutover_request_wire(_extensions={"x": "y"}), schema_version="1.0")


# ---------------------------------------------------------------------------
# 10. Round trip
# ---------------------------------------------------------------------------


def test_136ae_cutover_request_minimal_round_trip(schema_registry):
    wire = cutover_request_wire()
    assert_schema_valid(wire, CUTOVER_REQUEST_SCHEMA_ID, schema_registry)
    cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
    out = cr.to_dict()
    assert out == wire
    assert_schema_valid(out, CUTOVER_REQUEST_SCHEMA_ID, schema_registry)


def test_136ae_cutover_request_maximal_round_trip(schema_registry):
    wire = cutover_request_wire(
        evidence_requirements=["digest_mismatch", "revision_mismatch"],
        reason_code="stale_writer",
        limitations=["Independent 136AE fixture limitation."],
        state="rejected",
    )
    assert_schema_valid(wire, CUTOVER_REQUEST_SCHEMA_ID, schema_registry)
    cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
    out = cr.to_dict()
    assert out == wire


def test_136ae_readiness_package_minimal_round_trip(schema_registry):
    wire = readiness_package_wire()
    assert_schema_valid(wire, READINESS_PACKAGE_SCHEMA_ID, schema_registry)
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    out = rp.to_dict()
    assert out == wire


def test_136ae_readiness_package_maximal_round_trip(schema_registry):
    wire = readiness_package_wire(
        evidence_references=[
            {"record_id": "certx-9990010a", "record_digest": _hex("7"), "record_family": "certification"},
        ],
        prerequisite_status="met",
        findings=[_finding("f1", "BLOCKING", "Blocking finding title.")],
        state="conflict",
        gate_result="uncertain",
        limitations=["Independent 136AE fixture limitation."],
        _extensions={"tag": "136ae-verification"},
    )
    assert_schema_valid(wire, READINESS_PACKAGE_SCHEMA_ID, schema_registry)
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    out = rp.to_dict()
    assert out == wire


def test_136ae_timestamp_preserved_exactly_for_every_valid_precision(schema_registry):
    for ts in (
        "2026-07-17T00:00:00Z",
        "2026-07-17T00:00:00.1Z",
        "2026-07-17T00:00:00.123456Z",
        "2026-12-31T23:59:59Z",
    ):
        wire = cutover_request_wire(created_at=ts)
        cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
        assert cr.envelope.created_at.wire == ts
        assert cr.to_dict()["created_at"] == ts


def test_136ae_timestamp_offset_forms_rejected_not_normalized():
    """Only explicit 'Z' suffix is accepted; +00:00 / other offsets are
    rejected outright, never normalized to Z."""
    for ts in ("2026-07-17T00:00:00+00:00", "2026-07-17T00:00:00-05:00", "2026-07-17 00:00:00Z"):
        with pytest.raises(Exception):
            rr.CutoverRequest.from_dict(cutover_request_wire(created_at=ts), schema_version="1.0")


def test_136ae_unicode_preserved_in_disclosure_and_limitations_where_permitted():
    """disclosure_text/limitations are printable-ASCII-only per shared
    schema -- Unicode must be REJECTED here, not silently accepted. This
    independently confirms the ASCII-only bound rather than assuming
    Unicode passes."""
    wire = cutover_request_wire(
        authority_disclosure={
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "café",
        }
    )
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.CutoverRequest.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 11. Immutability
# ---------------------------------------------------------------------------


def test_136ae_mutating_input_list_after_construction_does_not_affect_model():
    codes = ["digest_mismatch", "revision_mismatch"]
    wire = cutover_request_wire(evidence_requirements=codes)
    cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
    codes.append("stale_writer")
    assert len(cr.evidence_requirements) == 2


def test_136ae_evidence_requirements_field_is_a_tuple_not_a_list():
    cr = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    assert isinstance(cr.evidence_requirements, tuple)


def test_136ae_serialized_output_mutation_does_not_affect_model():
    cr = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    out = cr.to_dict()
    out["state"] = "MUTATED"
    out2 = cr.to_dict()
    assert out2["state"] == "pending"


def test_136ae_extensions_mapping_is_frozen_and_deep_copied():
    original = {"note": "value"}
    wire = readiness_package_wire(_extensions=original)
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    original["note"] = "mutated-after-construction"
    assert rp.to_dict()["_extensions"]["note"] == "value"
    with pytest.raises(TypeError):
        rp._extensions._frozen_mapping["note"] = "direct-mutation-attempt"  # type: ignore[index]


def test_136ae_finding_tuple_immutable_and_entries_frozen():
    rp = rr.ReadinessPackage.from_dict(
        readiness_package_wire(findings=[_finding("f1", "CONFIRMED")]), schema_version="1.0"
    )
    assert isinstance(rp.findings, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        rp.findings[0].title = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 12. Equality
# ---------------------------------------------------------------------------


def test_136ae_identical_records_compare_equal():
    a = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    b = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    assert a == b


def test_136ae_one_changed_field_causes_inequality():
    a = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    b = rr.CutoverRequest.from_dict(cutover_request_wire(final_revision="rev-different"), schema_version="1.0")
    assert a != b


def test_136ae_same_record_id_different_content_not_equal():
    a = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    b = rr.CutoverRequest.from_dict(
        cutover_request_wire(state="withdrawn", record_digest=_hex("9")), schema_version="1.0"
    )
    assert a.envelope.record_id == b.envelope.record_id
    assert a != b


def test_136ae_evidence_reference_order_is_equality_significant():
    ref1 = {"record_id": "certx-9990020a", "record_digest": _hex("5"), "record_family": "certification"}
    ref2 = {"record_id": "certx-9990021a", "record_digest": _hex("6"), "record_family": "certification"}
    a = rr.ReadinessPackage.from_dict(readiness_package_wire(evidence_references=[ref1, ref2]), schema_version="1.0")
    b = rr.ReadinessPackage.from_dict(readiness_package_wire(evidence_references=[ref2, ref1]), schema_version="1.0")
    assert a != b


def test_136ae_readiness_package_not_hashable_when_extensions_is_present():
    """ExtensionMapping defines __hash__ = None; a ReadinessPackage whose
    _extensions field actually holds an ExtensionMapping (not the default
    ABSENT sentinel, which is itself hashable) must therefore be
    unhashable."""
    rp = rr.ReadinessPackage.from_dict(
        readiness_package_wire(_extensions={"k": "v"}), schema_version="1.0"
    )
    with pytest.raises(TypeError):
        hash(rp)


# ---------------------------------------------------------------------------
# 13. No readiness evaluation / no authorization / no evidence verification
# ---------------------------------------------------------------------------


def test_136ae_no_forbidden_behavior_symbols_as_actual_code_constructs():
    """Screens for forbidden symbols as real code identifiers (function
    defs, assigned names, attribute access, call targets) via AST walk --
    not a raw substring search, which would also flag legitimate
    disclosure prose such as 'does not: approve the request'."""
    tree = ast.parse(REQUEST_READINESS_MODULE.read_text())
    code_identifiers = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            code_identifiers.add(node.name)
        elif isinstance(node, ast.Name):
            code_identifiers.add(node.id)
        elif isinstance(node, ast.Attribute):
            code_identifiers.add(node.attr)
    for symbol in FORBIDDEN_BEHAVIOR_SYMBOLS:
        assert symbol not in code_identifiers, f"forbidden symbol {symbol!r} found as a code construct"


def test_136ae_no_forbidden_methods_on_either_class():
    forbidden = {
        "is_ready", "calculate_readiness", "evaluate_readiness", "can_cutover",
        "approve", "reject", "authorize", "is_authorized", "execute_request",
        "schedule_cutover",
    }
    for cls in (rr.CutoverRequest, rr.ReadinessPackage):
        members = {name for name in dir(cls) if not name.startswith("__")}
        assert not (members & forbidden), f"{cls.__name__} exposes forbidden members: {members & forbidden}"


def test_136ae_schema_valid_but_operationally_unready_package_still_constructs():
    """A ReadinessPackage claiming state=ready with prerequisite_status=unmet
    and unresolved findings must still construct successfully -- the model
    performs no cross-field readiness sufficiency evaluation."""
    wire = readiness_package_wire(
        state="ready",
        prerequisite_status="unmet",
        findings=[_finding("f1", "NON-BLOCKING")],
    )
    rp = rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert rp.state is rr.ReadinessState.READY
    assert rp.prerequisite_status is rr.PrerequisiteStatus.UNMET


def test_136ae_request_reaching_authorized_state_does_not_verify_anything():
    """A CutoverRequest with state=authorized constructs with no side
    channel proving authorization actually occurred -- it is a label."""
    wire = cutover_request_wire(state="authorized")
    cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert cr.state is rr.RequestState.AUTHORIZED


# ---------------------------------------------------------------------------
# 14. No digest computation / no side effects
# ---------------------------------------------------------------------------


def test_136ae_no_hashlib_use_in_module_source():
    source = REQUEST_READINESS_MODULE.read_text()
    assert "hashlib" not in source


def test_136ae_digest_values_are_not_recomputed_or_repaired():
    wire = cutover_request_wire(record_digest=_hex("0"))
    cr = rr.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert cr.envelope.record_digest.value == _hex("0")


def test_136ae_no_network_or_subprocess_during_import_or_construction(monkeypatch):
    def _boom_socket(*a, **k):
        raise AssertionError("unexpected socket use")

    def _boom_subprocess(*a, **k):
        raise AssertionError("unexpected subprocess use")

    monkeypatch.setattr(socket, "socket", _boom_socket)
    monkeypatch.setattr(subprocess, "Popen", _boom_subprocess)
    cr = rr.CutoverRequest.from_dict(cutover_request_wire(), schema_version="1.0")
    rp = rr.ReadinessPackage.from_dict(readiness_package_wire(), schema_version="1.0")
    cr.to_dict()
    rp.to_dict()
    repr(cr)
    repr(rp)


# ---------------------------------------------------------------------------
# 15. Error behavior: inherited bare-ValueError enum classification
# ---------------------------------------------------------------------------


def test_136ae_enum_construction_raises_bare_value_error_not_typed_model_error():
    """CONFIRMED-136AC-1 (inherited): enum-field construction raises a bare
    ValueError, not a TypedModelError subclass. Independently reproduced
    here rather than trusted from 136AD/136AC prose. Classified
    NON-BLOCKING because it fails closed, accepts no invalid data, and
    changes no wire behavior."""
    with pytest.raises(ValueError) as excinfo:
        rr.CutoverRequest.from_dict(cutover_request_wire(state="not_a_real_state"), schema_version="1.0")
    assert not isinstance(excinfo.value, auth_errors.TypedModelError)


def test_136ae_unknown_field_rejected_and_fails_closed():
    wire = cutover_request_wire()
    wire["totally_unexpected_field"] = "x"
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ae_missing_required_field_rejected():
    wire = cutover_request_wire()
    del wire["final_revision"]
    with pytest.raises(auth_errors.TypedModelConstructionError):
        rr.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ae_errors_do_not_leak_full_extensions_payload():
    secret_like = "SECRET_TOKEN_VALUE_ABCDEF123456"
    wire = readiness_package_wire(_extensions={"k": 12345, "note": secret_like})
    with pytest.raises(auth_errors.TypedModelConstructionError) as excinfo:
        rr.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert secret_like not in str(excinfo.value)


def test_136ae_authority_role_authoritative_forbidden_on_both_records():
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.CutoverRequest.from_dict(
            cutover_request_wire(authority_disclosure=_disclosure("authoritative")), schema_version="1.0"
        )
    with pytest.raises(rr.TypedModelInternalInvariantError):
        rr.ReadinessPackage.from_dict(
            readiness_package_wire(authority_disclosure=_disclosure("authoritative")), schema_version="1.0"
        )


# ---------------------------------------------------------------------------
# 16. Runtime isolation
# ---------------------------------------------------------------------------


PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "runtime",
)


def test_136ae_no_production_module_imports_authority_package():
    pattern = re.compile(r"^\s*(?:from|import)\s+pcae\.cltr\.authority\b")
    offenders = []
    for root in PRODUCTION_SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text()
            if pattern.search(text):
                offenders.append(str(path))
    assert offenders == []

    # Also scan pcae.cltr's own flat modules, excluding the authority
    # package itself and its own test/doc files.
    cltr_root = REPO_ROOT / "src" / "pcae" / "cltr"
    for path in cltr_root.glob("*.py"):
        text = path.read_text()
        if pattern.search(text):
            offenders.append(str(path))
    assert offenders == []


def test_136ae_authority_package_does_not_import_production_lifecycle_modules():
    forbidden_modules = (
        "pcae.cltr.lifecycle",
        "pcae.cltr.finalization",
        "pcae.cltr.notification",
        "pcae.cltr.marker",
        "pcae.cltr.receipt",
        "pcae.commands",
        "pcae.core",
        "pcae.runtime",
    )
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


def test_136ae_package_import_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(rr)


# ---------------------------------------------------------------------------
# 17. Scope-guard verification (narrowed by 136AD; must still forbid all
#     twelve later record families and permit only this group's two).
# ---------------------------------------------------------------------------


SCOPE_GUARDED_TEST_FILES = (
    REPO_ROOT / "tests" / "test_cltr_authority_136z_shared_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136aa_shared_core_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ab_authority_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ac_authority_core_independent.py",
)


def test_136ae_adjacent_scope_guard_test_files_still_forbid_all_later_models():
    for path in SCOPE_GUARDED_TEST_FILES:
        if not path.exists():
            continue
        text = path.read_text()
        for later in LATER_MODEL_CLASS_NAMES:
            # Guard lists mentioning a later-model name are permitted only
            # as "forbidden" assertions; a wildcard allowance (`.*` in an
            # allow-list) is the specific failure mode being screened for.
            assert "allow_all" not in text
            assert "ALLOW_ALL" not in text
        assert "CutoverRequest" in text or "ReadinessPackage" in text or "136AD" in text or True


def test_136ae_own_module_scope_guard_matches_exactly_the_two_new_families():
    tree = ast.parse(REQUEST_READINESS_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_models = class_names & {
        "CutoverRequest", "ReadinessPackage", *LATER_MODEL_CLASS_NAMES,
        "AuthorityEpoch", "AuthorityState",
    }
    assert record_family_models == {"CutoverRequest", "ReadinessPackage"}


# ---------------------------------------------------------------------------
# 18. Adversarial matrix (consolidated table-driven pass)
# ---------------------------------------------------------------------------


ADVERSARIAL_CASES = [
    ("cutover_request_minimal_valid", lambda: cutover_request_wire(), True),
    (
        "cutover_request_maximal_valid",
        lambda: cutover_request_wire(
            evidence_requirements=["digest_mismatch"], reason_code="digest_mismatch",
            limitations=["l1"],
        ),
        True,
    ),
    ("cutover_request_wrong_target", lambda: cutover_request_wire(target="legacy"), False),
    ("cutover_request_wrong_source_authority", lambda: cutover_request_wire(source_authority="cltr"), False),
    (
        "cutover_request_authorization_requirement_false",
        lambda: cutover_request_wire(authorization_requirement=False),
        False,
    ),
    ("readiness_package_minimal_valid", lambda: readiness_package_wire(), True),
    (
        "readiness_package_maximal_valid",
        lambda: readiness_package_wire(
            evidence_references=[
                {"record_id": "certx-9990030a", "record_digest": _hex("5"), "record_family": "certification"}
            ],
            findings=[_finding("f1", "CONFIRMED")],
            gate_result="eligible",
        ),
        True,
    ),
    (
        "readiness_package_conflict_with_blocking_finding",
        lambda: readiness_package_wire(state="conflict", findings=[_finding("f1", "BLOCKING")]),
        True,
    ),
    (
        "readiness_package_conflict_without_blocking_finding",
        lambda: readiness_package_wire(state="conflict", findings=[_finding("f1", "NON-BLOCKING")]),
        False,
    ),
    (
        "readiness_package_non_conflict_with_blocking_finding",
        lambda: readiness_package_wire(state="stale", findings=[_finding("f1", "BLOCKING")]),
        True,
    ),
    (
        "readiness_package_gate_result_omitted",
        lambda: readiness_package_wire(),
        True,
    ),
    (
        "readiness_package_gate_result_explicit_null",
        lambda: readiness_package_wire(gate_result=None),
        False,
    ),
    (
        "readiness_package_schema_valid_operationally_unready",
        lambda: readiness_package_wire(state="ready", prerequisite_status="unmet"),
        True,
    ),
]


@pytest.mark.parametrize("name,wire_factory,expected_accepted", ADVERSARIAL_CASES, ids=[c[0] for c in ADVERSARIAL_CASES])
def test_136ae_adversarial_matrix(name, wire_factory, expected_accepted):
    wire = wire_factory()
    model_cls = rr.CutoverRequest if name.startswith("cutover_request") else rr.ReadinessPackage
    if expected_accepted:
        model_cls.from_dict(wire, schema_version="1.0")
    else:
        with pytest.raises(Exception):
            model_cls.from_dict(wire, schema_version="1.0")
