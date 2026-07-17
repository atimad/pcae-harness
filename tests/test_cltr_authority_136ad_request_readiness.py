"""Phase 136AD: Stage 3 Typed Authority Model Request and Readiness
Implementation (Typed Model Implementation Group 3).

Focused tests for ``src/pcae/cltr/authority/request_readiness.py``: the
``CutoverRequest`` and ``ReadinessPackage`` typed record models. Covers
exact field mapping, strict constructor behavior, absent-versus-null
handling (including the one contractually named Sec.6.3 relaxation),
enum fidelity, identifier/digest/reference family preservation,
conditional branches, immutability, equality, serialization round-trip,
schema conformance, no-record-family-model-beyond-scope, no-readiness/
no-authorization semantics, no-side-effect, runtime-isolation, and
packaging proofs.

This module implements only Typed Model Implementation Group 3
(``CutoverRequest``, ``ReadinessPackage``). No other record-family model
(``AuthorityEpoch``, ``AuthorityState``, ``HumanAuthorization``,
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
from pcae.cltr.authority import request_readiness as rr
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import build_offline_registry, validate_record_shape, OutcomeStatus

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
REQUEST_READINESS_MODULE = AUTHORITY_PACKAGE_DIR / "request_readiness.py"

PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "cltr",  # excluding cltr/authority itself, filtered below
    REPO_ROOT / "src" / "pcae" / "runtime",
)

FORBIDDEN_READINESS_SYMBOLS = (
    "is_ready",
    "calculate_readiness",
    "evaluate_readiness",
    "all_checks_pass",
    "sufficient_evidence",
    "can_cutover",
    "approve",
    "authorize",
    "eligible",
    "approve_request",
    "reject_request",
    "validate_requester",
    "is_authorized",
    "can_submit",
    "execute_request",
    "schedule_cutover",
)

LATER_GROUP_MODEL_NAMES = (
    "AuthorityEpoch",
    "AuthorityState",
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

CUTOVER_REQUEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json"
READINESS_PACKAGE_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/readiness_package.schema.json"


def _sha256_hex(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


# ---------------------------------------------------------------------------
# Wire fixtures (independently authored from the executable schema files,
# not copied from 136Y plan prose)
# ---------------------------------------------------------------------------


def _epoch_ref(record_id: str = "authepoch-0000001", digest: str = "a") -> dict:
    return {
        "record_id": record_id,
        "record_digest": _sha256_hex(digest),
        "record_family": "authority_epoch",
    }


def _readiness_ref(record_id: str = "readypkg-0000001", digest: str = "b") -> dict:
    return {
        "record_id": record_id,
        "record_digest": _sha256_hex(digest),
        "record_family": "readiness_package",
        "schema_id": READINESS_PACKAGE_SCHEMA_ID,
        "schema_version": "1.0",
    }


def _valid_cutover_request_wire(**overrides) -> dict:
    record = {
        "schema_id": CUTOVER_REQUEST_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "cutover_request",
        "record_id": "cutreq-00000001",
        "record_digest": _sha256_hex("a"),
        "created_at": "2026-07-17T12:00:00Z",
        "phase_id": "136AD",
        "migration_epoch": "epoch-001",
        "target": "cltr",
        "source_authority": "legacy",
        "source_epoch": _epoch_ref("authepoch-0000001", "a"),
        "target_epoch": _epoch_ref("authepoch-0000002", "c"),
        "evidence_requirements": [],
        "readiness_package_reference": _readiness_ref(),
        "authorization_requirement": True,
        "final_revision": "rev-0001",
        "state": "pending",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_readiness_package_wire(**overrides) -> dict:
    record = {
        "schema_id": READINESS_PACKAGE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "readiness_package",
        "record_id": "readypkg-0000001",
        "record_digest": _sha256_hex("b"),
        "created_at": "2026-07-17T12:00:00Z",
        "phase_id": "136AD",
        "transition_id": "trans-00000001",
        "migration_epoch": "epoch-001",
        "evidence_references": [],
        "prerequisite_status": "unknown",
        "findings": [],
        "state": "unknown",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
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


def _load_schema(relative_path: str) -> dict:
    with cltr_cutover_root() as root:
        return json.loads((root / relative_path).read_text())


# ---------------------------------------------------------------------------
# 1. Inventory
# ---------------------------------------------------------------------------


def test_136ad_exactly_four_record_family_models_exist_in_package():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for expected in ("AuthorityEpoch", "AuthorityState", "CutoverRequest", "ReadinessPackage"):
        assert expected in class_names
    for later_name in (
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
        assert later_name not in class_names


def test_136ad_no_later_group_model_class_exists_in_request_readiness_module():
    tree = ast.parse(REQUEST_READINESS_MODULE.read_text())
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "CutoverRequest" in class_names
    assert "ReadinessPackage" in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136ad_expected_public_exports_present():
    for name in (
        "CutoverRequest",
        "ReadinessPackage",
        "RequestState",
        "ReadinessState",
        "PrerequisiteStatus",
        "GateResult",
        "FindingVerdict",
        "Finding",
    ):
        assert hasattr(auth, name)
        assert name in auth.__all__


def test_136ad_cutover_request_and_readiness_package_are_frozen_dataclasses():
    assert dataclasses.is_dataclass(auth.CutoverRequest)
    assert dataclasses.is_dataclass(auth.ReadinessPackage)
    assert auth.CutoverRequest.__dataclass_params__.frozen
    assert auth.ReadinessPackage.__dataclass_params__.frozen


# ---------------------------------------------------------------------------
# 2. CutoverRequest: construction / round trip
# ---------------------------------------------------------------------------


def test_136ad_cutover_request_minimal_valid_construction(schema_registry):
    wire = _valid_cutover_request_wire()
    _assert_schema_valid(wire, CUTOVER_REQUEST_SCHEMA_ID, schema_registry)
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert model.reason_code is None
    assert model.to_dict() == wire


def test_136ad_cutover_request_maximal_valid_construction_with_reason_code(schema_registry):
    wire = _valid_cutover_request_wire(
        state="rejected",
        reason_code="digest_mismatch",
        evidence_requirements=["cas_rejected", "concurrency_conflict"],
        limitations=["Evidence gathered from a rehearsal migration epoch only."],
    )
    _assert_schema_valid(wire, CUTOVER_REQUEST_SCHEMA_ID, schema_registry)
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert model.reason_code is rr.ReasonCode.DIGEST_MISMATCH
    assert model.to_dict() == wire


def test_136ad_cutover_request_exact_field_mapping():
    wire = _valid_cutover_request_wire()
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert model.envelope.record_id.value == wire["record_id"]
    assert model.phase_id.value == wire["phase_id"]
    assert model.migration_epoch.value == wire["migration_epoch"]
    assert model.target.value == "cltr"
    assert model.source_authority.value == "legacy"
    assert model.final_revision == wire["final_revision"]
    assert model.state is rr.RequestState.PENDING


def test_136ad_cutover_request_round_trip_all_variants(schema_registry):
    variants = [
        _valid_cutover_request_wire(),
        _valid_cutover_request_wire(state="withdrawn", reason_code="stale_writer"),
        _valid_cutover_request_wire(evidence_requirements=["cas_rejected"]),
    ]
    for wire in variants:
        _assert_schema_valid(wire, CUTOVER_REQUEST_SCHEMA_ID, schema_registry)
        model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
        assert model.to_dict() == wire


def test_136ad_cutover_request_reason_code_key_always_optional():
    wire = _valid_cutover_request_wire()
    assert "reason_code" not in wire
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert "reason_code" not in model.to_dict()


def test_136ad_cutover_request_unknown_field_rejected():
    wire = _valid_cutover_request_wire(unexpected_field="x")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_no_extensions_escape_hatch():
    wire = _valid_cutover_request_wire(_extensions={"k": "v"})
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_unsupported_schema_version_rejected():
    with pytest.raises(auth_errors.UnsupportedSchemaVersionError):
        auth.CutoverRequest.from_dict(_valid_cutover_request_wire(), schema_version="2.0")


def test_136ad_cutover_request_wrong_schema_id_rejected():
    wire = _valid_cutover_request_wire(schema_id="https://pcae.local/schemas/cltr_cutover/records/readiness_package.schema.json")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_wrong_record_type_rejected():
    wire = _valid_cutover_request_wire(record_type="readiness_package")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_missing_required_field_rejected():
    wire = _valid_cutover_request_wire()
    del wire["final_revision"]
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 3. CutoverRequest: discriminators / consts
# ---------------------------------------------------------------------------


def test_136ad_cutover_request_target_must_be_cltr():
    wire = _valid_cutover_request_wire(target="legacy")
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_source_authority_must_be_legacy():
    wire = _valid_cutover_request_wire(source_authority="cltr")
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_authorization_requirement_must_be_true():
    wire = _valid_cutover_request_wire(authorization_requirement=False)
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_forbids_authoritative_role():
    wire = _valid_cutover_request_wire(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        }
    )
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 4. CutoverRequest: absent/null matrix (Sec.6.3 relaxation) + enum strictness
# ---------------------------------------------------------------------------


def test_136ad_cutover_request_reason_code_omitted_key_yields_none():
    wire = _valid_cutover_request_wire()
    assert "reason_code" not in wire
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert model.reason_code is None


def test_136ad_cutover_request_reason_code_explicit_null_collapses_to_none_per_sec_6_3():
    wire = _valid_cutover_request_wire()
    wire["reason_code"] = None
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert model.reason_code is None
    # Sec.6.3: the model's own to_dict() still omits the key when None,
    # matching the ABSENT-field wire shape for the relaxed field.
    assert "reason_code" not in model.to_dict()


def test_136ad_cutover_request_reason_code_valid_value():
    wire = _valid_cutover_request_wire(reason_code="cas_rejected")
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert model.reason_code is rr.ReasonCode.CAS_REJECTED


def test_136ad_cutover_request_reason_code_invalid_value_rejected():
    wire = _valid_cutover_request_wire(reason_code="not_a_real_code")
    with pytest.raises(ValueError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("bad_value", ["CLTR", " cltr", "cltr ", "unknown", 1, True, None])
def test_136ad_cutover_request_target_enum_strictness(bad_value):
    wire = _valid_cutover_request_wire(target=bad_value)
    with pytest.raises((ValueError, auth_errors.TypedModelConstructionError)):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("bad_value", ["Pending", "PENDING", " pending", "pending ", "unknown", 1, None])
def test_136ad_cutover_request_state_enum_strictness(bad_value):
    wire = _valid_cutover_request_wire(state=bad_value)
    with pytest.raises((ValueError, auth_errors.TypedModelConstructionError)):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_state_enum_members_match_schema():
    schema = _load_schema("records/cutover_request.schema.json")
    schema_values = set(schema["properties"]["state"]["enum"])
    model_values = {member.value for member in rr.RequestState}
    assert schema_values == model_values


# ---------------------------------------------------------------------------
# 5. CutoverRequest: identifiers / digests / references
# ---------------------------------------------------------------------------


def test_136ad_cutover_request_source_epoch_wrong_family_rejected():
    wire = _valid_cutover_request_wire(
        source_epoch={"record_id": "cutreq-00000099", "record_digest": _sha256_hex("a"), "record_family": "cutover_request"}
    )
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_target_epoch_wrong_family_rejected():
    wire = _valid_cutover_request_wire(
        target_epoch={"record_id": "cutreq-00000099", "record_digest": _sha256_hex("a"), "record_family": "cutover_request"}
    )
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_readiness_package_reference_wrong_family_rejected():
    wire = _valid_cutover_request_wire(
        readiness_package_reference={
            "record_id": "authepoch-0000009",
            "record_digest": _sha256_hex("a"),
            "record_family": "authority_epoch",
            "schema_id": "x",
            "schema_version": "1.0",
        }
    )
    with pytest.raises(auth_errors.WrongFamilyReferenceError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_readiness_package_reference_requires_schema_id_and_version():
    wire = _valid_cutover_request_wire()
    wire["readiness_package_reference"] = {
        "record_id": "readypkg-0000001",
        "record_digest": _sha256_hex("b"),
        "record_family": "readiness_package",
    }
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_malformed_record_digest_rejected():
    wire = _valid_cutover_request_wire(record_digest="not-a-digest")
    with pytest.raises(auth_errors.InvalidDigestError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_malformed_record_id_rejected():
    wire = _valid_cutover_request_wire(record_id="BADID")
    with pytest.raises(auth_errors.InvalidIdentifierError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_valid_reference_to_nonexistent_target_constructs_without_lookup():
    # A syntactically valid epoch reference to a record that (as far as
    # this test can ever know) does not exist must construct successfully
    # -- no repository/filesystem/network lookup occurs.
    wire = _valid_cutover_request_wire(
        source_epoch=_epoch_ref("authepoch-9999999", "f"),
    )
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert model.source_epoch.record_id.value == "authepoch-9999999"


# ---------------------------------------------------------------------------
# 6. CutoverRequest: evidence_requirements array
# ---------------------------------------------------------------------------


def test_136ad_cutover_request_evidence_requirements_may_be_empty():
    wire = _valid_cutover_request_wire(evidence_requirements=[])
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert model.evidence_requirements == ()


def test_136ad_cutover_request_evidence_requirements_preserves_order():
    wire = _valid_cutover_request_wire(evidence_requirements=["cas_rejected", "digest_mismatch"])
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert [v.value for v in model.evidence_requirements] == ["cas_rejected", "digest_mismatch"]


def test_136ad_cutover_request_evidence_requirements_duplicate_rejected():
    wire = _valid_cutover_request_wire(evidence_requirements=["cas_rejected", "cas_rejected"])
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


def test_136ad_cutover_request_evidence_requirements_at_max_items_boundary_constructs():
    # Exactly 24 members exist in the closed ReasonCode vocabulary, matching
    # the schema's own maxItems: 24 bound exactly -- the boundary itself is
    # reachable with real, unique values.
    codes = [c.value for c in list(rr.ReasonCode)]
    assert len(codes) == 24
    wire = _valid_cutover_request_wire(evidence_requirements=codes)
    model = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    assert len(model.evidence_requirements) == 24


def test_136ad_cutover_request_evidence_requirements_exceeds_max_items_rejected():
    # The closed ReasonCode vocabulary has exactly 24 members, coinciding
    # with the schema's own maxItems: 24 bound (uniqueItems: true), so no
    # real, schema-valid payload can independently exercise "more than 24
    # unique entries." The maxItems bound is proven directly against the
    # model constructor instead (bypassing from_dict, whose own payload
    # would first fail JSON-Schema validation before ever reaching here) --
    # this exercises the same __post_init__ length check from_dict relies on.
    base_wire = _valid_cutover_request_wire()
    model = auth.CutoverRequest.from_dict(base_wire, schema_version="1.0")
    oversized = tuple(rr.ReasonCode.CAS_REJECTED for _ in range(25))
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        dataclasses.replace(model, evidence_requirements=oversized)


def test_136ad_cutover_request_final_revision_ascii_boundary():
    wire = _valid_cutover_request_wire(final_revision="a" * 256)
    auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    wire_too_long = _valid_cutover_request_wire(final_revision="a" * 257)
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.CutoverRequest.from_dict(wire_too_long, schema_version="1.0")


def test_136ad_cutover_request_final_revision_rejects_newline():
    wire = _valid_cutover_request_wire(final_revision="line1\nline2")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.CutoverRequest.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 7. ReadinessPackage: construction / round trip
# ---------------------------------------------------------------------------


def test_136ad_readiness_package_minimal_valid_construction(schema_registry):
    wire = _valid_readiness_package_wire()
    _assert_schema_valid(wire, READINESS_PACKAGE_SCHEMA_ID, schema_registry)
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model.gate_result is auth.ABSENT
    assert model._extensions is auth.ABSENT
    assert model.to_dict() == wire


def test_136ad_readiness_package_maximal_valid_construction(schema_registry):
    wire = _valid_readiness_package_wire(
        evidence_references=[_epoch_ref("authepoch-0000001", "a"), _readiness_ref("readypkg-0000002", "d")],
        prerequisite_status="met",
        findings=[
            {"id": "f1", "verdict": "CONFIRMED", "title": "Evidence gathered."},
            {"id": "f2", "verdict": "NON-BLOCKING", "title": "Minor gap disclosed."},
        ],
        state="ready",
        gate_result="eligible",
        limitations=["Evidence freshness not independently re-verified this phase."],
        _extensions={"note": "forward-compatible annotation only"},
    )
    _assert_schema_valid(wire, READINESS_PACKAGE_SCHEMA_ID, schema_registry)
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model.gate_result is rr.GateResult.ELIGIBLE
    assert model._extensions.to_dict() == {"note": "forward-compatible annotation only"}
    assert model.to_dict() == wire


def test_136ad_readiness_package_exact_field_mapping():
    wire = _valid_readiness_package_wire()
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model.transition_id.value == wire["transition_id"]
    assert model.prerequisite_status is rr.PrerequisiteStatus.UNKNOWN
    assert model.state is rr.ReadinessState.UNKNOWN


def test_136ad_readiness_package_round_trip_all_variants(schema_registry):
    variants = [
        _valid_readiness_package_wire(),
        _valid_readiness_package_wire(gate_result="uncertain"),
        _valid_readiness_package_wire(_extensions={"a": "1", "b": "2"}),
        _valid_readiness_package_wire(
            state="conflict",
            findings=[{"id": "f1", "verdict": "BLOCKING", "title": "Missing certification evidence."}],
        ),
    ]
    for wire in variants:
        _assert_schema_valid(wire, READINESS_PACKAGE_SCHEMA_ID, schema_registry)
        model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
        assert model.to_dict() == wire


def test_136ad_readiness_package_unknown_field_rejected():
    wire = _valid_readiness_package_wire(unexpected_field="x")
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_unsupported_schema_version_rejected():
    with pytest.raises(auth_errors.UnsupportedSchemaVersionError):
        auth.ReadinessPackage.from_dict(_valid_readiness_package_wire(), schema_version="9.9")


def test_136ad_readiness_package_wrong_schema_id_rejected():
    wire = _valid_readiness_package_wire(schema_id=CUTOVER_REQUEST_SCHEMA_ID)
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_missing_required_field_rejected():
    wire = _valid_readiness_package_wire()
    del wire["prerequisite_status"]
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_forbids_authoritative_role():
    wire = _valid_readiness_package_wire(
        authority_disclosure={"authority_role": "authoritative", "is_authoritative": False, "disclosure_text": "x"}
    )
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 8. ReadinessPackage: absent/null matrix + enum strictness
# ---------------------------------------------------------------------------


def test_136ad_readiness_package_gate_result_omitted_key_is_absent():
    wire = _valid_readiness_package_wire()
    assert "gate_result" not in wire
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model.gate_result is auth.ABSENT
    assert "gate_result" not in model.to_dict()


def test_136ad_readiness_package_gate_result_explicit_null_rejected():
    wire = _valid_readiness_package_wire()
    wire["gate_result"] = None
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_gate_result_valid_value():
    wire = _valid_readiness_package_wire(gate_result="conflict")
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model.gate_result is rr.GateResult.CONFLICT


def test_136ad_readiness_package_gate_result_invalid_value_rejected():
    wire = _valid_readiness_package_wire(gate_result="maybe")
    with pytest.raises(ValueError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_extensions_omitted_key_is_absent():
    wire = _valid_readiness_package_wire()
    assert "_extensions" not in wire
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model._extensions is auth.ABSENT
    assert "_extensions" not in model.to_dict()


def test_136ad_readiness_package_extensions_explicit_null_rejected():
    wire = _valid_readiness_package_wire()
    wire["_extensions"] = None
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_extensions_empty_object_permitted():
    wire = _valid_readiness_package_wire(_extensions={})
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert dict(model._extensions.items()) == {}


def test_136ad_readiness_package_extensions_non_string_value_rejected():
    wire = _valid_readiness_package_wire(_extensions={"k": 1})
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_extensions_reserved_key_collision_rejected():
    wire = _valid_readiness_package_wire(_extensions={"state": "should not shadow canonical field"})
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("bad_value", ["Unknown", "UNKNOWN", " unknown", "unknown ", "bogus", 1, None])
def test_136ad_readiness_package_state_enum_strictness(bad_value):
    wire = _valid_readiness_package_wire(state=bad_value)
    with pytest.raises((ValueError, auth_errors.TypedModelConstructionError)):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_state_enum_members_match_schema():
    schema = _load_schema("records/readiness_package.schema.json")
    schema_values = set(schema["properties"]["state"]["enum"])
    model_values = {member.value for member in rr.ReadinessState}
    assert schema_values == model_values


def test_136ad_readiness_package_prerequisite_status_enum_members_match_schema():
    schema = _load_schema("records/readiness_package.schema.json")
    schema_values = set(schema["properties"]["prerequisite_status"]["enum"])
    model_values = {member.value for member in rr.PrerequisiteStatus}
    assert schema_values == model_values


def test_136ad_readiness_package_gate_result_enum_members_match_schema():
    schema = _load_schema("records/readiness_package.schema.json")
    schema_values = set(schema["properties"]["gate_result"]["enum"])
    model_values = {member.value for member in rr.GateResult}
    assert schema_values == model_values


def test_136ad_finding_verdict_enum_members_match_schema():
    schema = _load_schema("records/readiness_package.schema.json")
    schema_values = set(schema["$defs"]["finding"]["properties"]["verdict"]["enum"])
    model_values = {member.value for member in rr.FindingVerdict}
    assert schema_values == model_values


# ---------------------------------------------------------------------------
# 9. ReadinessPackage: evidence_references / findings / conditional branch
# ---------------------------------------------------------------------------


def test_136ad_readiness_package_evidence_references_may_be_empty():
    wire = _valid_readiness_package_wire(evidence_references=[])
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model.evidence_references == ()


def test_136ad_readiness_package_evidence_references_no_family_restriction():
    wire = _valid_readiness_package_wire(
        evidence_references=[_epoch_ref(), _readiness_ref(digest="c")]
    )
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    families = {ref.record_family.value for ref in model.evidence_references}
    assert families == {"authority_epoch", "readiness_package"}


def test_136ad_readiness_package_evidence_references_preserves_exact_order():
    refs = [_epoch_ref("authepoch-0000001", "a"), _epoch_ref("authepoch-0000002", "c")]
    wire = _valid_readiness_package_wire(evidence_references=refs)
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert [r.record_id.value for r in model.evidence_references] == [
        "authepoch-0000001",
        "authepoch-0000002",
    ]
    # Reversed input must round-trip in the reversed order too -- no
    # semantic re-sort is ever applied.
    wire_reversed = _valid_readiness_package_wire(evidence_references=list(reversed(refs)))
    model_reversed = auth.ReadinessPackage.from_dict(wire_reversed, schema_version="1.0")
    assert [r.record_id.value for r in model_reversed.evidence_references] == [
        "authepoch-0000002",
        "authepoch-0000001",
    ]


def test_136ad_readiness_package_findings_may_be_empty():
    wire = _valid_readiness_package_wire(findings=[])
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model.findings == ()


def test_136ad_readiness_package_findings_preserves_duplicates_and_order():
    findings = [
        {"id": "f1", "verdict": "CONFIRMED", "title": "a"},
        {"id": "f1", "verdict": "CONFIRMED", "title": "a"},
    ]
    wire = _valid_readiness_package_wire(findings=findings)
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert len(model.findings) == 2
    assert model.findings[0] == model.findings[1]


def test_136ad_readiness_package_finding_unknown_key_rejected():
    wire = _valid_readiness_package_wire(findings=[{"id": "f1", "verdict": "CONFIRMED", "title": "a", "extra": 1}])
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_finding_id_pattern_enforced():
    wire = _valid_readiness_package_wire(findings=[{"id": "bad id with spaces", "verdict": "CONFIRMED", "title": "a"}])
    with pytest.raises(auth_errors.TypedModelConstructionError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_conflict_state_requires_blocking_finding():
    wire = _valid_readiness_package_wire(
        state="conflict",
        findings=[{"id": "f1", "verdict": "NON-BLOCKING", "title": "no blocking finding here"}],
    )
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_conflict_state_with_no_findings_rejected():
    wire = _valid_readiness_package_wire(state="conflict", findings=[])
    with pytest.raises(auth_errors.TypedModelInternalInvariantError):
        auth.ReadinessPackage.from_dict(wire, schema_version="1.0")


def test_136ad_readiness_package_conflict_state_with_blocking_finding_constructs():
    wire = _valid_readiness_package_wire(
        state="conflict",
        findings=[{"id": "f1", "verdict": "BLOCKING", "title": "Missing certification evidence."}],
    )
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model.state is rr.ReadinessState.CONFLICT


def test_136ad_readiness_package_non_conflict_state_does_not_require_blocking_finding():
    wire = _valid_readiness_package_wire(state="stale", findings=[])
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    assert model.state is rr.ReadinessState.STALE


# ---------------------------------------------------------------------------
# 10. Schema conformance (drift detection)
# ---------------------------------------------------------------------------


def test_136ad_cutover_request_schema_field_set_matches_model_known_keys():
    schema = _load_schema("records/cutover_request.schema.json")
    schema_fields = set(schema["properties"].keys())
    assert schema_fields == rr._CUTOVER_REQUEST_KNOWN_KEYS


def test_136ad_cutover_request_schema_required_set_matches_model_required_handling():
    schema = _load_schema("records/cutover_request.schema.json")
    required = set(schema["required"])
    unconditional = set(auth.CutoverRequest.__dataclass_fields__.keys()) - {"reason_code"}
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


def test_136ad_readiness_package_schema_field_set_matches_model_known_keys():
    schema = _load_schema("records/readiness_package.schema.json")
    schema_fields = set(schema["properties"].keys())
    assert schema_fields == rr._READINESS_PACKAGE_KNOWN_KEYS


def test_136ad_readiness_package_schema_required_set_matches_model_required_handling():
    schema = _load_schema("records/readiness_package.schema.json")
    required = set(schema["required"])
    unconditional = set(auth.ReadinessPackage.__dataclass_fields__.keys()) - {"gate_result", "_extensions"}
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


# ---------------------------------------------------------------------------
# 11. Immutability / equality
# ---------------------------------------------------------------------------


def test_136ad_cutover_request_top_level_assignment_raises():
    model = auth.CutoverRequest.from_dict(_valid_cutover_request_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.state = rr.RequestState.PUBLISHED


def test_136ad_readiness_package_top_level_assignment_raises():
    model = auth.ReadinessPackage.from_dict(_valid_readiness_package_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.state = rr.ReadinessState.READY


def test_136ad_cutover_request_evidence_requirements_is_tuple_not_list():
    model = auth.CutoverRequest.from_dict(
        _valid_cutover_request_wire(evidence_requirements=["cas_rejected"]), schema_version="1.0"
    )
    assert isinstance(model.evidence_requirements, tuple)
    with pytest.raises(AttributeError):
        model.evidence_requirements.append(rr.ReasonCode.CAS_REJECTED)


def test_136ad_readiness_package_findings_is_tuple_not_list():
    model = auth.ReadinessPackage.from_dict(
        _valid_readiness_package_wire(findings=[{"id": "f1", "verdict": "CONFIRMED", "title": "a"}]),
        schema_version="1.0",
    )
    assert isinstance(model.findings, tuple)


def test_136ad_readiness_package_extensions_mutation_does_not_affect_model():
    wire = _valid_readiness_package_wire(_extensions={"k": "v"})
    model = auth.ReadinessPackage.from_dict(wire, schema_version="1.0")
    exported = model._extensions.to_dict()
    exported["k"] = "mutated"
    assert model._extensions.to_dict() == {"k": "v"}


def test_136ad_to_dict_output_mutation_does_not_affect_model():
    model = auth.CutoverRequest.from_dict(_valid_cutover_request_wire(), schema_version="1.0")
    exported = model.to_dict()
    exported["state"] = "published"
    exported["limitations"].append("mutated")
    assert model.state is rr.RequestState.PENDING
    assert model.limitations.entries == ()


def test_136ad_cutover_request_structural_equality():
    wire = _valid_cutover_request_wire()
    model_a = auth.CutoverRequest.from_dict(wire, schema_version="1.0")
    model_b = auth.CutoverRequest.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert model_a == model_b


def test_136ad_readiness_package_record_id_equality_does_not_imply_record_equality():
    wire_a = _valid_readiness_package_wire()
    wire_b = _valid_readiness_package_wire(state="stale")
    model_a = auth.ReadinessPackage.from_dict(wire_a, schema_version="1.0")
    model_b = auth.ReadinessPackage.from_dict(wire_b, schema_version="1.0")
    assert model_a.envelope.record_id == model_b.envelope.record_id
    assert model_a != model_b


def test_136ad_readiness_package_extension_differences_participate_in_equality():
    model_a = auth.ReadinessPackage.from_dict(
        _valid_readiness_package_wire(_extensions={"k": "v1"}), schema_version="1.0"
    )
    model_b = auth.ReadinessPackage.from_dict(
        _valid_readiness_package_wire(_extensions={"k": "v2"}), schema_version="1.0"
    )
    assert model_a != model_b


def test_136ad_readiness_package_evidence_reference_order_difference_is_observable():
    refs = [_epoch_ref("authepoch-0000001", "a"), _epoch_ref("authepoch-0000002", "c")]
    model_forward = auth.ReadinessPackage.from_dict(
        _valid_readiness_package_wire(evidence_references=refs), schema_version="1.0"
    )
    model_reversed = auth.ReadinessPackage.from_dict(
        _valid_readiness_package_wire(evidence_references=list(reversed(refs))), schema_version="1.0"
    )
    assert model_forward != model_reversed


# ---------------------------------------------------------------------------
# 12. No-readiness / no-authorization semantics; no-later-scope
# ---------------------------------------------------------------------------


def test_136ad_no_forbidden_readiness_or_request_symbols_defined_in_source():
    source = REQUEST_READINESS_MODULE.read_text()
    tree = ast.parse(source)
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_READINESS_SYMBOLS:
        assert forbidden not in defined_names


def test_136ad_no_cas_expectation_used_by_either_model():
    source = REQUEST_READINESS_MODULE.read_text()
    assert "CasExpectation" not in source


def test_136ad_no_opaque_json_value_used_by_either_model():
    source = REQUEST_READINESS_MODULE.read_text()
    assert "OpaqueJsonValue" not in source


def test_136ad_no_repository_or_persistence_symbols_in_source():
    source = REQUEST_READINESS_MODULE.read_text()
    for forbidden in ("Repository", "save(", "persist(", "def load(", "requests.", "urllib"):
        assert forbidden not in source


# ---------------------------------------------------------------------------
# 13. Runtime isolation / no-side-effect
# ---------------------------------------------------------------------------


def test_136ad_no_production_module_imports_authority_package():
    for root_dir in PRODUCTION_SCAN_ROOTS:
        if not root_dir.exists():
            continue
        for path in root_dir.rglob("*.py"):
            if AUTHORITY_PACKAGE_DIR in path.parents or path.parent == AUTHORITY_PACKAGE_DIR:
                continue
            source = path.read_text()
            assert "from pcae.cltr.authority" not in source, path
            assert "import pcae.cltr.authority" not in source, path


def test_136ad_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    auth.CutoverRequest.from_dict(_valid_cutover_request_wire(), schema_version="1.0").to_dict()
    auth.ReadinessPackage.from_dict(_valid_readiness_package_wire(), schema_version="1.0").to_dict()


def test_136ad_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "Popen", _raise)
    auth.CutoverRequest.from_dict(_valid_cutover_request_wire(), schema_version="1.0").to_dict()
    auth.ReadinessPackage.from_dict(_valid_readiness_package_wire(), schema_version="1.0").to_dict()


def test_136ad_no_filesystem_write_during_construction_or_serialization(monkeypatch, tmp_path):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in ("w", "a", "x")):
            raise AssertionError(f"filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    auth.CutoverRequest.from_dict(_valid_cutover_request_wire(), schema_version="1.0").to_dict()
    auth.ReadinessPackage.from_dict(_valid_readiness_package_wire(), schema_version="1.0").to_dict()


def test_136ad_no_environment_variable_lookup_during_construction(monkeypatch):
    import os

    def _raise(*args, **kwargs):
        raise AssertionError("environment variable lookup attempted")

    monkeypatch.setattr(os.environ, "get", _raise)
    auth.CutoverRequest.from_dict(_valid_cutover_request_wire(), schema_version="1.0")
    auth.ReadinessPackage.from_dict(_valid_readiness_package_wire(), schema_version="1.0")


def test_136ad_no_hashlib_sha256_during_construction_or_serialization(monkeypatch):
    import hashlib

    def _raise(*args, **kwargs):
        raise AssertionError("digest computation attempted")

    monkeypatch.setattr(hashlib, "sha256", _raise)
    auth.CutoverRequest.from_dict(_valid_cutover_request_wire(), schema_version="1.0").to_dict()
    auth.ReadinessPackage.from_dict(_valid_readiness_package_wire(), schema_version="1.0").to_dict()


# ---------------------------------------------------------------------------
# 14. Packaging
# ---------------------------------------------------------------------------


def test_136ad_wheel_contains_request_readiness_module(tmp_path: Path):
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

    assert any(name.endswith("pcae/cltr/authority/request_readiness.py") for name in names)
    for later_module in (
        "authorization_candidate.py",
        "publication.py",
        "recovery.py",
        "bindings.py",
        "compatibility_quarantine.py",
    ):
        assert not any(name.endswith(f"pcae/cltr/authority/{later_module}") for name in names)


def test_136ad_sdist_includes_request_readiness_module(tmp_path: Path):
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
    assert any(name.endswith("pcae/cltr/authority/request_readiness.py") for name in names)


@pytest.mark.slow
def test_136ad_installed_wheel_constructs_request_readiness_fixtures_outside_repository(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv136ad"
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
        "epoch_ref = lambda rid: {'record_id': rid, 'record_digest': 'a' * 64, 'record_family': 'authority_epoch'}\n"
        "wire = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0', 'record_type': 'cutover_request',\n"
        "    'record_id': 'cutreq-00000001', 'record_digest': 'a' * 64,\n"
        "    'created_at': '2026-07-17T12:00:00Z', 'phase_id': '136AD', 'migration_epoch': 'epoch-001',\n"
        "    'target': 'cltr', 'source_authority': 'legacy',\n"
        "    'source_epoch': epoch_ref('authepoch-0000001'), 'target_epoch': epoch_ref('authepoch-0000002'),\n"
        "    'evidence_requirements': [],\n"
        "    'readiness_package_reference': {\n"
        "        'record_id': 'readypkg-0000001', 'record_digest': 'b' * 64, 'record_family': 'readiness_package',\n"
        "        'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/readiness_package.schema.json',\n"
        "        'schema_version': '1.0',\n"
        "    },\n"
        "    'authorization_requirement': True, 'final_revision': 'rev-0001', 'state': 'pending',\n"
        "    'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'derivative', 'is_authoritative': False, 'disclosure_text': 'x'},\n"
        "}\n"
        "model = auth.CutoverRequest.from_dict(wire, schema_version='1.0')\n"
        "assert model.to_dict()['record_id'] == 'cutreq-00000001'\n"
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
