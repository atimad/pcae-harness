"""Phase 136AG: Stage 3 Typed Authority Model Authorization and Candidate
Independent Verification.

Independently re-derives and verifies the ``HumanAuthorization``,
``CutoverCandidate``, and ``Certification`` typed record models implemented
by Phase 136AF (``src/pcae/cltr/authority/authorization_candidate.py``),
against:

- the frozen primary contracts (CLTR-001, CLTR-SCHEMA-001, CLTR-CUTOVER-001,
  CLTR-CUTOVER-SCHEMAS-001, CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 Sec.21/22/23,
  the Stage 3 Companion Schemas and Typed Authority Model Contract);
- the live executable schemas (``records/human_authorization.schema.json``,
  ``records/cutover_candidate.schema.json``,
  ``records/certification.schema.json``, and every shared ``$ref``);
- the verified 136Y implementation plan and verified typed-model foundation
  (136Z/136AA/136AB/136AC/136AD/136AE).

Deliberately does NOT import ``tests/test_cltr_authority_136af_
authorization_candidate.py`` (fixtures, helpers, or expected-value tables).
Every wire fixture and expected value below is authored directly from the
schema files and contract text cited above.

This module implements no record-family model. It performs no
authentication, no signature/credential verification, no authorization-
validity determination, no candidate eligibility or selection, no
certification verification, no reference resolution, no digest
computation, and no persistence.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import re
import socket
import sys
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import authorization_candidate as ac
from pcae.cltr.authority import errors as auth_errors
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
MODULE_UNDER_TEST = AUTHORITY_PACKAGE_DIR / "authorization_candidate.py"

HUMAN_AUTHORIZATION_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/human_authorization.schema.json"
)
CUTOVER_CANDIDATE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/cutover_candidate.schema.json"
)
CERTIFICATION_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/certification.schema.json"
CUTOVER_REQUEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json"
READINESS_PACKAGE_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/readiness_package.schema.json"

# The seven not-yet-implemented record-family class names (136Y plan Groups
# 6-11). Independently retyped here rather than imported from 136AF's test
# module. Narrowed by Phase 136AH: `PublicationAttempt`/
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
# still-forbidden list.
LATER_MODEL_CLASS_NAMES = (
    "FinalizationReceiptAuthorityBinding",
    "CompatibilityState",
    "QuarantineRecord",
)

FORBIDDEN_BEHAVIOR_SYMBOLS = (
    "authenticate",
    "verify_signature",
    "is_authorized",
    "authorization_valid",
    "verify_authorization",
    "validate_actor",
    "check_permission",
    "approve",
    "reject",
    "has_authority",
    "is_eligible",
    "calculate_eligibility",
    "can_cutover",
    "rank_candidate",
    "select_candidate",
    "ready_for_cutover",
    "is_certified",
    "verify_certification",
    "certification_valid",
    "validate_verifier",
    "verify_evidence",
    "resolve_reference",
    "persist",
    "publish",
    "execute",
)


def _hex(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


# ---------------------------------------------------------------------------
# Independently authored wire fixtures (derived from the schema files read
# directly in this phase, not copied from 136AF's fixtures).
# ---------------------------------------------------------------------------


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Independently constructed 136AG verification fixture.",
    }


def _record_ref(rid: str, fill: str, family: str, *, cross_family: bool = False, schema_id: str = "") -> dict:
    ref = {"record_id": rid, "record_digest": _hex(fill), "record_family": family}
    if cross_family:
        ref["schema_id"] = schema_id
        ref["schema_version"] = "1.0"
    return ref


def _epoch_ref(rid: str = "authepoch-9990001", fill: str = "a") -> dict:
    return _record_ref(rid, fill, "authority_epoch")


def _cas_expectation() -> dict:
    return {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _epoch_ref("authepoch-9990010", "1"),
        "expected_authoritative_generation": {
            "generation_id": "generatio-9990001",
            "generation_digest": _hex("2"),
        },
        "expected_authority_pointer_digest": _hex("3"),
        "expected_authority_state_digest": _hex("4"),
        "expected_migration_epoch": "epoch-136ag",
        "expected_source_lifecycle_state": "PROPOSED",
        "expected_compatibility_mode": "legacy_authoritative",
        "expected_journal_lock_state": "unlocked",
        "expected_request_reference": _record_ref("cutreq-9990020", "5", "cutover_request"),
        "expected_certification_reference": _record_ref("cert-99900030", "6", "certification"),
    }


def human_authorization_wire(**overrides) -> dict:
    wire = {
        "schema_id": HUMAN_AUTHORIZATION_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "human_authorization",
        "record_id": "humanauth-9990001",
        "record_digest": _hex("1"),
        "created_at": "2026-07-18T00:00:00Z",
        "phase_id": "136AG",
        "migration_epoch": "epoch-136ag",
        "principal": "operator@example.com",
        "method": "manual_review",
        "request_reference": _record_ref(
            "cutreq-9990001", "2", "cutover_request", cross_family=True, schema_id=CUTOVER_REQUEST_SCHEMA_ID
        ),
        "readiness_reference": _record_ref(
            "readypkg-9990001", "3", "readiness_package", cross_family=True, schema_id=READINESS_PACKAGE_SCHEMA_ID
        ),
        "target_reference": _record_ref(
            "authepoch-9990002", "4", "authority_epoch", cross_family=True,
            schema_id="https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json",
        ),
        "issued_at": "2026-07-18T00:00:00Z",
        "expires_at": "2026-07-19T00:00:00Z",
        "state": "issued",
        "replay_binding": "replay-token-9990001",
        "risk_acknowledgement": True,
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    wire.update(overrides)
    return wire


def cutover_candidate_wire(**overrides) -> dict:
    wire = {
        "schema_id": CUTOVER_CANDIDATE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "cutover_candidate",
        "record_id": "candidate-9990001",
        "record_digest": _hex("7"),
        "created_at": "2026-07-18T00:00:00Z",
        "migration_epoch": "epoch-136ag",
        "stage2_generation_reference": _record_ref("generatio-9990002", "8", "authority_epoch"),
        "cas_expectation": _cas_expectation(),
        "state": "proposed",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    wire.update(overrides)
    return wire


def certification_wire(**overrides) -> dict:
    wire = {
        "schema_id": CERTIFICATION_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "certification",
        "record_id": "cert-99900040",
        "record_digest": _hex("9"),
        "created_at": "2026-07-18T00:00:00Z",
        "phase_id": "136AG",
        "migration_epoch": "epoch-136ag",
        "candidate_reference": _record_ref(
            "candidate-9990001", "a", "cutover_candidate", cross_family=True, schema_id=CUTOVER_CANDIDATE_SCHEMA_ID
        ),
        "request_reference": _record_ref(
            "cutreq-9990001", "b", "cutover_request", cross_family=True, schema_id=CUTOVER_REQUEST_SCHEMA_ID
        ),
        "readiness_reference": _record_ref(
            "readypkg-9990001", "c", "readiness_package", cross_family=True, schema_id=READINESS_PACKAGE_SCHEMA_ID
        ),
        "authorization_reference": _record_ref(
            "humanauth-9990001", "d", "human_authorization", cross_family=True,
            schema_id=HUMAN_AUTHORIZATION_SCHEMA_ID,
        ),
        "source_authority_reference": _epoch_ref("authepoch-9990003", "e"),
        "target_epoch_reference": _epoch_ref("authepoch-9990004", "f"),
        "cas_expectation": _cas_expectation(),
        "verifier_evidence": [],
        "state": "pending",
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


def _load_schema(relative_path: str) -> dict:
    with cltr_cutover_root() as root:
        return json.loads((root / relative_path).read_text())


# ---------------------------------------------------------------------------
# 1. Independent schema re-derivation: field tables built directly from the
#    live schema files, independent of 136AF's field inventory.
# ---------------------------------------------------------------------------


def test_136ag_human_authorization_schema_required_fields_independently_enumerated():
    schema = _load_schema("records/human_authorization.schema.json")
    assert set(schema["required"]) == {
        "schema_id", "schema_version", "contract_version", "record_type", "record_id",
        "record_digest", "created_at", "phase_id", "migration_epoch", "principal", "method",
        "request_reference", "readiness_reference", "target_reference", "issued_at",
        "expires_at", "state", "replay_binding", "risk_acknowledgement", "limitations",
        "authority_disclosure",
    }
    assert schema["additionalProperties"] is False
    optional_keys = set(schema["properties"]) - set(schema["required"])
    assert optional_keys == {"revocation_metadata", "use_binding", "proof_reference"}
    # No standalone "scope" field anywhere in the schema.
    assert "scope" not in schema["properties"]


def test_136ag_cutover_candidate_schema_required_fields_independently_enumerated():
    schema = _load_schema("records/cutover_candidate.schema.json")
    assert set(schema["required"]) == {
        "schema_id", "schema_version", "contract_version", "record_type", "record_id",
        "record_digest", "created_at", "migration_epoch", "stage2_generation_reference",
        "cas_expectation", "state", "limitations", "authority_disclosure",
    }
    assert schema["additionalProperties"] is False
    optional_keys = set(schema["properties"]) - set(schema["required"])
    assert optional_keys == {"_extensions"}
    # No phase_id field anywhere on this record family.
    assert "phase_id" not in schema["properties"]
    # No direct top-level binding fields beyond the frozen Sec.22 three.
    for forbidden_top_level in (
        "request_reference", "readiness_reference", "authorization_reference",
        "source_authority_reference", "target_epoch_reference",
    ):
        assert forbidden_top_level not in schema["properties"]


def test_136ag_certification_schema_required_fields_independently_enumerated():
    schema = _load_schema("records/certification.schema.json")
    assert set(schema["required"]) == {
        "schema_id", "schema_version", "contract_version", "record_type", "record_id",
        "record_digest", "created_at", "phase_id", "migration_epoch", "candidate_reference",
        "request_reference", "readiness_reference", "authorization_reference",
        "source_authority_reference", "target_epoch_reference", "cas_expectation",
        "verifier_evidence", "state", "limitations", "authority_disclosure",
    }
    assert schema["additionalProperties"] is False
    optional_keys = set(schema["properties"]) - set(schema["required"])
    assert optional_keys == {"staleness", "invalidation"}
    # No certifier_principal field or _extensions escape hatch anywhere.
    assert "certifier_principal" not in schema["properties"]
    assert "_extensions" not in schema["properties"]


def test_136ag_human_authorization_state_enum_independently_enumerated():
    schema = _load_schema("records/human_authorization.schema.json")
    assert schema["properties"]["state"]["enum"] == ["issued", "used", "revoked", "expired"]


def test_136ag_human_authorization_method_enum_independently_enumerated():
    schema = _load_schema("records/human_authorization.schema.json")
    assert schema["properties"]["method"]["enum"] == ["manual_review", "signed_attestation"]


def test_136ag_cutover_candidate_state_enum_independently_enumerated():
    schema = _load_schema("records/cutover_candidate.schema.json")
    assert schema["properties"]["state"]["enum"] == [
        "proposed", "verified", "certifying", "certified", "superseded", "quarantined",
    ]


def test_136ag_certification_state_enum_independently_enumerated():
    schema = _load_schema("records/certification.schema.json")
    assert schema["properties"]["state"]["enum"] == ["pending", "certified", "stale", "invalidated"]


def test_136ag_human_authorization_risk_acknowledgement_is_const_true():
    schema = _load_schema("records/human_authorization.schema.json")
    assert schema["properties"]["risk_acknowledgement"]["const"] is True


def test_136ag_replay_binding_pattern_independently_confirmed():
    schema = _load_schema("records/human_authorization.schema.json")
    field = schema["properties"]["replay_binding"]
    assert field["pattern"] == r"^[A-Za-z0-9._-]{1,256}$"
    assert field["minLength"] == 1
    assert field["maxLength"] == 256


def test_136ag_certification_verifier_evidence_bounds_independently_confirmed():
    schema = _load_schema("records/certification.schema.json")
    field = schema["properties"]["verifier_evidence"]
    assert field["type"] == "array"
    assert field["maxItems"] == 64
    assert "minItems" not in field
    assert "uniqueItems" not in field
    assert field["items"] == {"$ref": "../shared/references.schema.json#/$defs/record_reference"}


def test_136ag_authority_role_authoritative_forbidden_on_all_three_schemas():
    for relpath in (
        "records/human_authorization.schema.json",
        "records/cutover_candidate.schema.json",
        "records/certification.schema.json",
    ):
        schema = _load_schema(relpath)
        disclosure = schema["properties"]["authority_disclosure"]["allOf"][1]
        assert disclosure["properties"]["authority_role"] == {"not": {"const": "authoritative"}}


# ---------------------------------------------------------------------------
# 2. Inventory / public API
# ---------------------------------------------------------------------------


def test_136ag_exactly_seven_record_family_models_in_authority_package():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    for expected in (
        "AuthorityEpoch", "AuthorityState", "CutoverRequest", "ReadinessPackage",
        "HumanAuthorization", "CutoverCandidate", "Certification",
    ):
        assert expected in class_names
    for later in LATER_MODEL_CLASS_NAMES:
        assert later not in class_names


def test_136ag_no_later_model_ast_or_dynamic_construction_in_module_under_test():
    tree = ast.parse(MODULE_UNDER_TEST.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    assigned_names = {
        t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
        for t in n.targets if isinstance(t, ast.Name)
    }
    called_or_referenced_names = {
        n.id for n in ast.walk(tree) if isinstance(n, ast.Name)
    } | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
    }
    for later in LATER_MODEL_CLASS_NAMES:
        assert later not in class_names
        assert later not in assigned_names
        assert later not in called_or_referenced_names


def test_136ag_public_exports_exact():
    assert set(ac.__all__) == {
        "AuthorizationMethod", "AuthorizationState", "CandidateState", "CertificationState",
        "RevocationMetadata", "Staleness", "Invalidation",
        "HumanAuthorization", "CutoverCandidate", "Certification",
    }
    for expected in ("HumanAuthorization", "CutoverCandidate", "Certification"):
        assert expected in auth.__all__
    for later in LATER_MODEL_CLASS_NAMES:
        assert later not in auth.__all__


def test_136ag_wildcard_import_matches_all():
    namespace: dict = {}
    exec("from pcae.cltr.authority.authorization_candidate import *", namespace)
    exported = {k for k in namespace if not k.startswith("_")}
    assert exported == set(ac.__all__)


def test_136ag_dataclasses_are_frozen():
    ha = ac.HumanAuthorization.from_dict(human_authorization_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        ha.principal = ac.PrincipalIdentifier("someone-else")  # type: ignore[attr-defined,misc]
    cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        cc.state = ac.CandidateState.CERTIFIED  # type: ignore[misc]
    cert = ac.Certification.from_dict(certification_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        cert.state = ac.CertificationState.CERTIFIED  # type: ignore[misc]


def test_136ag_no_unauthorized_public_methods_beyond_from_dict_to_dict():
    for cls in (ac.HumanAuthorization, ac.CutoverCandidate, ac.Certification):
        public_methods = {
            name for name in dir(cls)
            if not name.startswith("_") and callable(getattr(cls, name))
        }
        assert public_methods == {"from_dict", "to_dict"}


def test_136ag_no_mutable_module_level_state():
    for name, value in vars(ac).items():
        if name.startswith("_") or not isinstance(value, (list, dict, set)):
            continue
        pytest.fail(f"unexpected mutable module-level state: {name}={value!r}")


# ---------------------------------------------------------------------------
# 3. Discriminators
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("record_type", "cutover_candidate"),
        ("record_type", "Human_Authorization"),
        ("record_type", " human_authorization"),
        ("record_type", ""),
        ("schema_id", CUTOVER_CANDIDATE_SCHEMA_ID),
        ("schema_id", HUMAN_AUTHORIZATION_SCHEMA_ID + " "),
    ],
)
def test_136ag_human_authorization_rejects_wrong_discriminator(field, value):
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(human_authorization_wire(**{field: value}), schema_version="1.0")


def test_136ag_human_authorization_discriminator_absent_rejected():
    wire = human_authorization_wire()
    del wire["record_type"]
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136ag_human_authorization_discriminator_null_rejected():
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(human_authorization_wire(record_type=None), schema_version="1.0")


def test_136ag_human_authorization_discriminator_non_string_rejected():
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(human_authorization_wire(record_type=1), schema_version="1.0")


@pytest.mark.parametrize(
    "field,value",
    [
        ("record_type", "human_authorization"),
        ("schema_id", CUTOVER_CANDIDATE_SCHEMA_ID + "x"),
    ],
)
def test_136ag_cutover_candidate_rejects_wrong_discriminator(field, value):
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(cutover_candidate_wire(**{field: value}), schema_version="1.0")


@pytest.mark.parametrize(
    "field,value",
    [
        ("record_type", "cutover_candidate"),
        ("schema_id", HUMAN_AUTHORIZATION_SCHEMA_ID),
    ],
)
def test_136ag_certification_rejects_wrong_discriminator(field, value):
    with pytest.raises(Exception):
        ac.Certification.from_dict(certification_wire(**{field: value}), schema_version="1.0")


def test_136ag_unsupported_schema_version_rejected_for_all_three():
    for wire_factory, cls in (
        (human_authorization_wire, ac.HumanAuthorization),
        (cutover_candidate_wire, ac.CutoverCandidate),
        (certification_wire, ac.Certification),
    ):
        with pytest.raises(auth_errors.UnsupportedSchemaVersionError):
            cls.from_dict(wire_factory(), schema_version="2.0")


# ---------------------------------------------------------------------------
# 4. HumanAuthorization conditional pairs: independently derive direction
#    and strength (both directions are enforced by the schema's own
#    if/then/else "else: not required" branches, i.e. strict biconditional).
# ---------------------------------------------------------------------------


def _revocation_metadata() -> dict:
    return {
        "revoked_at": "2026-07-18T01:00:00Z",
        "revoked_by": "operator2@example.com",
        "reason_code": "stale_authorization",
    }


def test_136ag_revoked_state_without_revocation_metadata_rejected():
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(human_authorization_wire(state="revoked"), schema_version="1.0")


def test_136ag_revoked_state_with_revocation_metadata_accepted():
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(state="revoked", revocation_metadata=_revocation_metadata()),
        schema_version="1.0",
    )
    assert ha.state is ac.AuthorizationState.REVOKED
    assert ha.revocation_metadata.reason_code is auth.ReasonCode.STALE_AUTHORIZATION


def test_136ag_revocation_metadata_outside_revoked_state_rejected():
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(
            human_authorization_wire(state="issued", revocation_metadata=_revocation_metadata()),
            schema_version="1.0",
        )


def test_136ag_revocation_metadata_explicit_null_rejected_when_revoked():
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(
            human_authorization_wire(state="revoked", revocation_metadata=None), schema_version="1.0"
        )


def test_136ag_revocation_metadata_malformed_missing_reason_code_rejected():
    bad = _revocation_metadata()
    del bad["reason_code"]
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(
            human_authorization_wire(state="revoked", revocation_metadata=bad), schema_version="1.0"
        )


def _use_binding() -> dict:
    return {"record_id": "pubattem-9990001", "record_digest": _hex("5"), "record_family": "publication_attempt"}


def test_136ag_used_state_without_use_binding_rejected():
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(human_authorization_wire(state="used"), schema_version="1.0")


def test_136ag_used_state_with_use_binding_accepted():
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(state="used", use_binding=_use_binding()), schema_version="1.0"
    )
    assert ha.state is ac.AuthorizationState.USED
    assert ha.use_binding.record_family is auth.RecordFamily.PUBLICATION_ATTEMPT


def test_136ag_use_binding_outside_used_state_rejected():
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(
            human_authorization_wire(state="issued", use_binding=_use_binding()), schema_version="1.0"
        )


def test_136ag_use_binding_wrong_family_rejected():
    bad_binding = {"record_id": "cutreq-9990099", "record_digest": _hex("6"), "record_family": "cutover_request"}
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(
            human_authorization_wire(state="used", use_binding=bad_binding), schema_version="1.0"
        )


def test_136ag_use_binding_forward_reference_to_nonexistent_publication_attempt_accepted():
    """The live schema authorizes this as a shape-only forward reference:
    construction must succeed for a syntactically valid publication_attempt
    reference even though no PublicationAttempt class or record exists."""
    assert "PublicationAttempt" not in {
        n.name for n in ast.walk(ast.parse(MODULE_UNDER_TEST.read_text())) if isinstance(n, ast.ClassDef)
    }
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(state="used", use_binding=_use_binding()), schema_version="1.0"
    )
    assert ha.use_binding.record_id.value == "pubattem-9990001"
    # No lookup: the record_id is entirely fictitious and construction did
    # not fail or attempt any resolution.


def test_136ag_use_binding_does_not_require_cross_family_schema_identity():
    """Unlike request/readiness/target_reference, the schema's use_binding
    $def does not add a "required": ["schema_id", "schema_version"] clause
    beyond record_reference's own base required fields."""
    schema = _load_schema("records/human_authorization.schema.json")
    use_binding_def = schema["$defs"]["use_binding"]
    for sub in use_binding_def["allOf"]:
        assert "required" not in sub or set(sub.get("required", [])) <= {"record_id", "record_digest", "record_family"}
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(state="used", use_binding=_use_binding()), schema_version="1.0"
    )
    assert ha.use_binding.schema_id is auth.ABSENT
    assert ha.use_binding.schema_version is auth.ABSENT


def test_136ag_signed_attestation_without_proof_reference_rejected():
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(
            human_authorization_wire(method="signed_attestation"), schema_version="1.0"
        )


def test_136ag_signed_attestation_with_proof_reference_accepted():
    proof = {"record_id": "proofrec-9990001", "record_digest": _hex("7"), "record_family": "human_authorization"}
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(method="signed_attestation", proof_reference=proof), schema_version="1.0"
    )
    assert ha.method is ac.AuthorizationMethod.SIGNED_ATTESTATION
    assert ha.proof_reference.record_id.value == "proofrec-9990001"


def test_136ag_manual_review_with_proof_reference_rejected():
    proof = {"record_id": "proofrec-9990001", "record_digest": _hex("7"), "record_family": "human_authorization"}
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(
            human_authorization_wire(method="manual_review", proof_reference=proof), schema_version="1.0"
        )


def test_136ag_proof_reference_has_no_family_restriction():
    schema = _load_schema("records/human_authorization.schema.json")
    proof_field = schema["properties"]["proof_reference"]
    assert proof_field["$ref"] == "../shared/references.schema.json#/$defs/proof_reference"
    refs_schema = _load_schema("shared/references.schema.json")
    assert refs_schema["$defs"]["proof_reference"]["$ref"] == "#/$defs/record_reference"


# ---------------------------------------------------------------------------
# 5. Cross-family schema-identity requirement (three references on
#    HumanAuthorization).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["request_reference", "readiness_reference", "target_reference"])
def test_136ag_human_authorization_reference_requires_schema_id_and_version(field):
    schema = _load_schema("records/human_authorization.schema.json")
    def_name = field
    ref_def = schema["$defs"][def_name]
    required_fields = ref_def["allOf"][1]["required"]
    assert set(required_fields) == {"schema_id", "schema_version"}

    base_wire = human_authorization_wire()
    ref = dict(base_wire[field])
    del ref["schema_id"]
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(human_authorization_wire(**{field: ref}), schema_version="1.0")

    ref2 = dict(base_wire[field])
    del ref2["schema_version"]
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(human_authorization_wire(**{field: ref2}), schema_version="1.0")


@pytest.mark.parametrize(
    "field,expected_family",
    [
        ("request_reference", "cutover_request"),
        ("readiness_reference", "readiness_package"),
        ("target_reference", "authority_epoch"),
    ],
)
def test_136ag_human_authorization_reference_family_exact(field, expected_family):
    schema = _load_schema("records/human_authorization.schema.json")
    ref_def = schema["$defs"][field]
    assert ref_def["allOf"][1]["properties"]["record_family"] == {"const": expected_family}

    base_wire = human_authorization_wire()
    ref = dict(base_wire[field])
    ref["record_family"] = "certification"
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(human_authorization_wire(**{field: ref}), schema_version="1.0")


def test_136ag_human_authorization_wrong_schema_id_on_reference_still_accepted_at_layer2():
    """Schema shape validity does not verify the referenced schema_id
    string points at any real, matching schema (Layer 4) -- construction
    must succeed for a schema-shape-valid but semantically implausible
    cross-family schema_id, since this model performs no resolution."""
    wire = human_authorization_wire()
    wire["request_reference"]["schema_id"] = "https://pcae.local/schemas/cltr_cutover/records/does-not-exist.json"
    ha = ac.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert ha.request_reference.schema_id == "https://pcae.local/schemas/cltr_cutover/records/does-not-exist.json"


def test_136ag_human_authorization_construction_succeeds_with_nonexistent_but_syntactically_valid_targets():
    wire = human_authorization_wire(
        request_reference=_record_ref(
            "cutreq-0000000z", "0", "cutover_request", cross_family=True, schema_id=CUTOVER_REQUEST_SCHEMA_ID
        ),
    )
    ha = ac.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert ha.request_reference.record_id.value == "cutreq-0000000z"


# ---------------------------------------------------------------------------
# 6. Human/actor representation
# ---------------------------------------------------------------------------


def test_136ag_human_authorization_principal_field_present_and_exact_wire_preserved():
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(principal="jane.doe@example.org"), schema_version="1.0"
    )
    assert ha.principal.value == "jane.doe@example.org"
    assert ha.to_dict()["principal"] == "jane.doe@example.org"


def test_136ag_human_authorization_principal_not_authenticated_syntactically_valid_but_fictitious():
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(principal="totally-fictitious-user-never-existed"), schema_version="1.0"
    )
    assert ha.principal.value == "totally-fictitious-user-never-existed"


def test_136ag_human_authorization_has_no_role_or_declared_authority_field():
    schema = _load_schema("records/human_authorization.schema.json")
    for absent_field in ("role", "declared_authority", "actor_reference"):
        assert absent_field not in schema["properties"]


def test_136ag_certification_has_no_named_certifier_field():
    schema = _load_schema("records/certification.schema.json")
    for absent_field in ("certifier_principal", "certifier", "verifier_principal"):
        assert absent_field not in schema["properties"]
    with pytest.raises(Exception):
        wire = certification_wire()
        wire["certifier_principal"] = "someone@example.com"
        ac.Certification.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 7. CutoverCandidate: no phase_id, CAS descriptive-only, authoritative role
#    forbidden at every state, binding references, _extensions.
# ---------------------------------------------------------------------------


def test_136ag_cutover_candidate_injected_phase_id_rejected():
    wire = cutover_candidate_wire()
    wire["phase_id"] = "136AG"
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(wire, schema_version="1.0")


def test_136ag_cutover_candidate_cas_expectation_component_reused_without_semantic_execution(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected filesystem/network access during CAS construction")

    monkeypatch.setattr(socket, "socket", _boom)
    cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(), schema_version="1.0")
    assert cc.cas_expectation.expected_authority_kind is auth.AuthorityKind.LEGACY
    # Construction does not compare expected vs. actual, lock, retry, or
    # persist -- it only holds the declared expected-state tuple verbatim.


def test_136ag_cutover_candidate_cas_expectation_malformed_missing_field_rejected():
    bad_cas = _cas_expectation()
    del bad_cas["expected_authority_kind"]
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(cutover_candidate_wire(cas_expectation=bad_cas), schema_version="1.0")


@pytest.mark.parametrize("state", ["proposed", "verified", "certifying", "certified", "superseded", "quarantined"])
def test_136ag_cutover_candidate_authoritative_role_forbidden_at_every_state(state):
    wire = cutover_candidate_wire(state=state, authority_disclosure=_disclosure(role="authoritative"))
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("state", ["proposed", "verified", "certifying", "certified", "superseded", "quarantined"])
def test_136ag_cutover_candidate_permitted_roles_accepted_at_every_state(state):
    for role in ("derivative", "operational", "evidence", "compatibility", "historical", "quarantined"):
        cc = ac.CutoverCandidate.from_dict(
            cutover_candidate_wire(state=state, authority_disclosure=_disclosure(role=role)), schema_version="1.0"
        )
        assert cc.state.value == state


def test_136ag_cutover_candidate_wrong_case_authoritative_role_rejected():
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(
            cutover_candidate_wire(authority_disclosure=_disclosure(role="Authoritative")), schema_version="1.0"
        )


def test_136ag_cutover_candidate_binding_reference_no_family_const_restriction():
    """stage2_generation_reference cannot be locally closed to a specific
    record_family value because 'generation' is not one of the 16
    record_family enum members -- independently confirmed against the
    live schema, which applies no allOf/const restriction here."""
    schema = _load_schema("records/cutover_candidate.schema.json")
    field = schema["properties"]["stage2_generation_reference"]
    assert field == {
        "$ref": "../shared/references.schema.json#/$defs/record_reference",
        "description": field["description"],
    }
    wire = cutover_candidate_wire(
        stage2_generation_reference=_record_ref("cutreq-9990099", "1", "cutover_request")
    )
    cc = ac.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert cc.stage2_generation_reference.record_family is auth.RecordFamily.CUTOVER_REQUEST


def test_136ag_cutover_candidate_binding_reference_valid_nonexistent_target_accepted():
    wire = cutover_candidate_wire(
        stage2_generation_reference=_record_ref("generatio-0000000z", "0", "authority_epoch")
    )
    cc = ac.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert cc.stage2_generation_reference.record_id.value == "generatio-0000000z"


def test_136ag_cutover_candidate_state_is_descriptive_only_no_transition_check():
    """No state ordering rule exists; a state jump directly to 'certified'
    or 'quarantined' from a fresh construction must succeed with no
    lifecycle-order check."""
    for state in ("certified", "quarantined", "superseded"):
        cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(state=state), schema_version="1.0")
        assert cc.state.value == state


def test_136ag_cutover_candidate_extensions_field_exists_optional_nullable_string_only():
    schema = _load_schema("records/cutover_candidate.schema.json")
    ext_field = schema["properties"]["_extensions"]
    assert ext_field["type"] == "object"
    assert ext_field["additionalProperties"] == {"type": "string"}
    assert ext_field["maxProperties"] == 32

    cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(), schema_version="1.0")
    assert cc._extensions is auth.ABSENT

    cc2 = ac.CutoverCandidate.from_dict(
        cutover_candidate_wire(_extensions={"annotation": "value", "unicode": "café", "empty": ""}),
        schema_version="1.0",
    )
    assert cc2._extensions["annotation"] == "value"
    assert cc2._extensions["unicode"] == "café"
    assert cc2._extensions["empty"] == ""


def test_136ag_cutover_candidate_extensions_explicit_null_rejected():
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(cutover_candidate_wire(_extensions=None), schema_version="1.0")


@pytest.mark.parametrize("bad_value", [1, True, [], {}, None])
def test_136ag_cutover_candidate_extensions_non_string_values_rejected(bad_value):
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(
            cutover_candidate_wire(_extensions={"key": bad_value}), schema_version="1.0"
        )


def test_136ag_cutover_candidate_extensions_empty_mapping_accepted():
    cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(_extensions={}), schema_version="1.0")
    assert len(cc._extensions) == 0


def test_136ag_cutover_candidate_extensions_key_colliding_with_canonical_field_rejected():
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(cutover_candidate_wire(_extensions={"state": "x"}), schema_version="1.0")


def test_136ag_cutover_candidate_extensions_over_max_properties_rejected():
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(
            cutover_candidate_wire(_extensions={f"k{i}": "v" for i in range(33)}), schema_version="1.0"
        )


# ---------------------------------------------------------------------------
# 8. Certification: verifier_evidence, epoch references, staleness/
#    invalidation conditionals.
# ---------------------------------------------------------------------------


def _evidence_item(rid: str, fill: str, family: str = "readiness_package") -> dict:
    return {"record_id": rid, "record_digest": _hex(fill), "record_family": family}


def test_136ag_certification_verifier_evidence_empty_accepted():
    cert = ac.Certification.from_dict(certification_wire(verifier_evidence=[]), schema_version="1.0")
    assert cert.verifier_evidence == ()


def test_136ag_certification_verifier_evidence_one_item_accepted():
    items = [_evidence_item("readypkg-0000001a", "1")]
    cert = ac.Certification.from_dict(certification_wire(verifier_evidence=items), schema_version="1.0")
    assert len(cert.verifier_evidence) == 1


def test_136ag_certification_verifier_evidence_64_items_accepted():
    items = [_evidence_item(f"readypkg-{i:08x}", "1") for i in range(64)]
    cert = ac.Certification.from_dict(certification_wire(verifier_evidence=items), schema_version="1.0")
    assert len(cert.verifier_evidence) == 64


def test_136ag_certification_verifier_evidence_65_items_rejected():
    items = [_evidence_item(f"readypkg-{i:08x}", "1") for i in range(65)]
    with pytest.raises(Exception):
        ac.Certification.from_dict(certification_wire(verifier_evidence=items), schema_version="1.0")


def test_136ag_certification_verifier_evidence_duplicate_identical_references_preserved():
    item = _evidence_item("readypkg-0000001a", "1")
    cert = ac.Certification.from_dict(
        certification_wire(verifier_evidence=[item, dict(item)]), schema_version="1.0"
    )
    assert len(cert.verifier_evidence) == 2
    assert cert.verifier_evidence[0] == cert.verifier_evidence[1]


def test_136ag_certification_verifier_evidence_same_target_different_digest_preserved():
    item_a = _evidence_item("readypkg-0000001a", "1")
    item_b = _evidence_item("readypkg-0000001a", "2")
    cert = ac.Certification.from_dict(
        certification_wire(verifier_evidence=[item_a, item_b]), schema_version="1.0"
    )
    assert cert.verifier_evidence[0].record_digest != cert.verifier_evidence[1].record_digest


def test_136ag_certification_verifier_evidence_mixed_record_families_accepted():
    items = [
        _evidence_item("readypkg-0000001a", "1", "readiness_package"),
        _evidence_item("humanauth-0000001a", "2", "human_authorization"),
        _evidence_item("candidate-0000001a", "3", "cutover_candidate"),
    ]
    cert = ac.Certification.from_dict(certification_wire(verifier_evidence=items), schema_version="1.0")
    assert {e.record_family for e in cert.verifier_evidence} == {
        auth.RecordFamily.READINESS_PACKAGE, auth.RecordFamily.HUMAN_AUTHORIZATION,
        auth.RecordFamily.CUTOVER_CANDIDATE,
    }


def test_136ag_certification_verifier_evidence_order_preserved():
    items = [_evidence_item(f"readypkg-{i:08x}", "1") for i in range(5)]
    cert = ac.Certification.from_dict(certification_wire(verifier_evidence=items), schema_version="1.0")
    assert [e.record_id.value for e in cert.verifier_evidence] == [it["record_id"] for it in items]
    serialized = cert.to_dict()["verifier_evidence"]
    assert [e["record_id"] for e in serialized] == [it["record_id"] for it in items]


def test_136ag_certification_verifier_evidence_malformed_entry_rejected():
    bad_item = {"record_id": "readypkg-0000001a", "record_family": "readiness_package"}  # missing digest
    with pytest.raises(Exception):
        ac.Certification.from_dict(certification_wire(verifier_evidence=[bad_item]), schema_version="1.0")


def test_136ag_certification_verifier_evidence_no_family_restriction_applied():
    schema = _load_schema("records/certification.schema.json")
    field = schema["properties"]["verifier_evidence"]
    assert field["items"] == {"$ref": "../shared/references.schema.json#/$defs/record_reference"}
    assert "record_family" not in json.dumps(field["items"])


def test_136ag_certification_source_and_target_epoch_reference_names_and_family_exact():
    schema = _load_schema("records/certification.schema.json")
    epoch_def = schema["$defs"]["epoch_reference"]
    assert epoch_def["allOf"][1]["properties"]["record_family"] == {"const": "authority_epoch"}
    assert "required" not in epoch_def["allOf"][1]
    assert schema["properties"]["source_authority_reference"]["$ref"] == "#/$defs/epoch_reference"
    assert schema["properties"]["target_epoch_reference"]["$ref"] == "#/$defs/epoch_reference"


def test_136ag_certification_epoch_references_do_not_require_cross_family_schema_identity():
    wire = certification_wire()
    assert "schema_id" not in wire["source_authority_reference"]
    assert "schema_version" not in wire["source_authority_reference"]
    cert = ac.Certification.from_dict(wire, schema_version="1.0")
    assert cert.source_authority_reference.schema_id is auth.ABSENT


def test_136ag_certification_identical_source_and_target_epoch_references_accepted():
    same_ref = _epoch_ref("authepoch-9990005", "1")
    cert = ac.Certification.from_dict(
        certification_wire(
            source_authority_reference=dict(same_ref), target_epoch_reference=dict(same_ref)
        ),
        schema_version="1.0",
    )
    assert cert.source_authority_reference.record_id == cert.target_epoch_reference.record_id
    assert cert.source_authority_reference.record_digest == cert.target_epoch_reference.record_digest
    # No "source must differ from target" invariant is invented here.


def test_136ag_certification_epoch_reference_wrong_family_rejected():
    bad = {"record_id": "cutreq-9990099", "record_digest": _hex("1"), "record_family": "cutover_request"}
    with pytest.raises(Exception):
        ac.Certification.from_dict(certification_wire(source_authority_reference=bad), schema_version="1.0")


def _staleness() -> dict:
    return {"detected_at": "2026-07-18T02:00:00Z", "reason_code": "stale_certification"}


def _invalidation() -> dict:
    return {"invalidated_at": "2026-07-18T03:00:00Z", "reason_code": "digest_mismatch"}


def test_136ag_certification_stale_state_without_staleness_rejected():
    with pytest.raises(Exception):
        ac.Certification.from_dict(certification_wire(state="stale"), schema_version="1.0")


def test_136ag_certification_stale_state_with_staleness_accepted():
    cert = ac.Certification.from_dict(
        certification_wire(state="stale", staleness=_staleness()), schema_version="1.0"
    )
    assert cert.staleness.reason_code is auth.ReasonCode.STALE_CERTIFICATION


def test_136ag_certification_staleness_outside_stale_state_rejected():
    with pytest.raises(Exception):
        ac.Certification.from_dict(
            certification_wire(state="pending", staleness=_staleness()), schema_version="1.0"
        )


def test_136ag_certification_invalidated_state_without_invalidation_rejected():
    with pytest.raises(Exception):
        ac.Certification.from_dict(certification_wire(state="invalidated"), schema_version="1.0")


def test_136ag_certification_invalidated_state_with_invalidation_accepted():
    cert = ac.Certification.from_dict(
        certification_wire(state="invalidated", invalidation=_invalidation()), schema_version="1.0"
    )
    assert cert.invalidation.reason_code is auth.ReasonCode.DIGEST_MISMATCH


def test_136ag_certification_invalidation_outside_invalidated_state_rejected():
    with pytest.raises(Exception):
        ac.Certification.from_dict(
            certification_wire(state="pending", invalidation=_invalidation()), schema_version="1.0"
        )


def test_136ag_certification_does_not_infer_current_time_staleness():
    """A 'pending' or 'certified' state with an old created_at must not be
    reinterpreted as stale; only the explicit state field controls this."""
    cert = ac.Certification.from_dict(
        certification_wire(state="certified", created_at="2020-01-01T00:00:00Z"), schema_version="1.0"
    )
    assert cert.state is ac.CertificationState.CERTIFIED
    assert cert.staleness is auth.ABSENT


# ---------------------------------------------------------------------------
# 9. No authentication / no cryptographic verification
# ---------------------------------------------------------------------------


def test_136ag_no_authentication_or_identity_provider_symbols_in_source():
    text = MODULE_UNDER_TEST.read_text()
    for banned in ("oauth", "ldap", "keychain", "google.contacts", "sso"):
        assert banned not in text.lower()


def test_136ag_construction_succeeds_with_syntactically_valid_but_nonexistent_actor():
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(principal="ghost.user.never.enrolled@example.test"), schema_version="1.0"
    )
    assert ha.principal.value == "ghost.user.never.enrolled@example.test"


def test_136ag_no_hashlib_or_signature_library_use_in_module_source():
    tree = ast.parse(MODULE_UNDER_TEST.read_text())
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".")[0])
    for banned in ("hashlib", "cryptography", "rsa", "ecdsa", "Crypto"):
        assert banned not in imported_modules


def test_136ag_digest_and_proof_fields_are_not_recomputed_or_verified(monkeypatch):
    import hashlib

    original_sha256 = hashlib.sha256

    def _boom(*a, **k):
        raise AssertionError("unexpected hashlib.sha256 call during construction")

    monkeypatch.setattr(hashlib, "sha256", _boom)
    try:
        ha = ac.HumanAuthorization.from_dict(
            human_authorization_wire(
                method="signed_attestation",
                proof_reference={
                    "record_id": "proofrec-9990001", "record_digest": _hex("7"),
                    "record_family": "human_authorization",
                },
            ),
            schema_version="1.0",
        )
        assert ha.proof_reference.record_digest.value == _hex("7")
    finally:
        monkeypatch.setattr(hashlib, "sha256", original_sha256)


# ---------------------------------------------------------------------------
# 10. No authorization evaluation / candidate eligibility / certification
#     verification -- symbol absence via AST inspection of actual code
#     constructs (not prose comments, which legitimately name these terms
#     to disclose what is NOT implemented).
# ---------------------------------------------------------------------------


def test_136ag_no_forbidden_behavior_symbols_as_actual_code_constructs():
    tree = ast.parse(MODULE_UNDER_TEST.read_text())
    defined_names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    called_names = {
        n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    } | {
        n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    for forbidden in FORBIDDEN_BEHAVIOR_SYMBOLS:
        assert forbidden not in defined_names, f"forbidden symbol defined: {forbidden}"
        assert forbidden not in called_names, f"forbidden symbol called: {forbidden}"


def test_136ag_no_forbidden_methods_on_any_of_the_three_classes():
    for cls in (ac.HumanAuthorization, ac.CutoverCandidate, ac.Certification):
        for forbidden in FORBIDDEN_BEHAVIOR_SYMBOLS:
            assert not hasattr(cls, forbidden)


def test_136ag_certification_reaching_certified_state_does_not_verify_anything():
    """A schema-valid but operationally implausible/false certification
    (verifier_evidence pointing at fictitious records) must still
    construct -- the model performs no evidence evaluation."""
    items = [_evidence_item("readypkg-9999999a", "0")]
    cert = ac.Certification.from_dict(
        certification_wire(state="certified", verifier_evidence=items), schema_version="1.0"
    )
    assert cert.state is ac.CertificationState.CERTIFIED


def test_136ag_candidate_reaching_certified_state_does_not_prove_eligibility():
    cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(state="certified"), schema_version="1.0")
    assert cc.state is ac.CandidateState.CERTIFIED


# ---------------------------------------------------------------------------
# 11. Reference non-resolution
# ---------------------------------------------------------------------------


def test_136ag_no_filesystem_or_network_access_during_construction(monkeypatch):
    def _boom_socket(*a, **k):
        raise AssertionError("unexpected socket use during construction")

    monkeypatch.setattr(socket, "socket", _boom_socket)
    ac.HumanAuthorization.from_dict(human_authorization_wire(), schema_version="1.0")
    ac.CutoverCandidate.from_dict(cutover_candidate_wire(), schema_version="1.0")
    ac.Certification.from_dict(certification_wire(), schema_version="1.0")


def test_136ag_all_three_construct_with_valid_references_to_nonexistent_targets():
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(
            request_reference=_record_ref(
                "cutreq-0000000a", "0", "cutover_request", cross_family=True, schema_id=CUTOVER_REQUEST_SCHEMA_ID
            )
        ),
        schema_version="1.0",
    )
    cc = ac.CutoverCandidate.from_dict(
        cutover_candidate_wire(stage2_generation_reference=_record_ref("generatio-0000000a", "0", "authority_epoch")),
        schema_version="1.0",
    )
    cert = ac.Certification.from_dict(
        certification_wire(
            candidate_reference=_record_ref(
                "candidate-0000000a", "0", "cutover_candidate", cross_family=True,
                schema_id=CUTOVER_CANDIDATE_SCHEMA_ID,
            )
        ),
        schema_version="1.0",
    )
    assert ha.request_reference.record_id.value == "cutreq-0000000a"
    assert cc.stage2_generation_reference.record_id.value == "generatio-0000000a"
    assert cert.candidate_reference.record_id.value == "candidate-0000000a"


# ---------------------------------------------------------------------------
# 12. Timestamp preservation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ts",
    [
        "2026-07-18T00:00:00Z",
        "2026-07-18T00:00:00.5Z",
        "2026-07-18T00:00:00.123456Z",
        "2026-12-31T23:59:59Z",
        "2026-01-01T00:00:00.000001Z",
    ],
)
def test_136ag_timestamp_exact_wire_string_preserved(ts, schema_registry):
    wire = human_authorization_wire(created_at=ts, issued_at=ts)
    assert_schema_valid(wire, HUMAN_AUTHORIZATION_SCHEMA_ID, schema_registry)
    ha = ac.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert ha.envelope.created_at.wire == ts
    assert ha.issued_at.wire == ts
    assert ha.to_dict()["created_at"] == ts
    assert ha.to_dict()["issued_at"] == ts


@pytest.mark.parametrize("ts", ["2026-07-18T00:00:00+00:00", "2026-07-18T00:00:00+02:00", "2026-07-18T00:00:00-05:00"])
def test_136ag_timestamp_offset_forms_rejected_not_normalized(ts):
    with pytest.raises(Exception):
        ac.HumanAuthorization.from_dict(human_authorization_wire(created_at=ts), schema_version="1.0")


def test_136ag_timestamp_never_compared_against_now_or_each_other():
    """issued_at after expires_at (a nonsensical but schema-shape-valid
    combination) must still construct: no freshness comparison occurs at
    this layer."""
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(issued_at="2030-01-01T00:00:00Z", expires_at="2020-01-01T00:00:00Z"),
        schema_version="1.0",
    )
    assert ha.issued_at.wire == "2030-01-01T00:00:00Z"
    assert ha.expires_at.wire == "2020-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# 13. Immutability
# ---------------------------------------------------------------------------


def test_136ag_mutating_input_list_after_construction_does_not_affect_model():
    limitations = ["initial"]
    ha = ac.HumanAuthorization.from_dict(human_authorization_wire(limitations=limitations), schema_version="1.0")
    limitations.append("mutated-after")
    assert ha.limitations.entries == ("initial",)


def test_136ag_verifier_evidence_field_is_a_tuple_not_a_list():
    cert = ac.Certification.from_dict(
        certification_wire(verifier_evidence=[_evidence_item("readypkg-0000001a", "1")]), schema_version="1.0"
    )
    assert isinstance(cert.verifier_evidence, tuple)


def test_136ag_serialized_output_mutation_does_not_affect_model():
    cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(), schema_version="1.0")
    serialized = cc.to_dict()
    serialized["state"] = "certified"
    serialized["limitations"].append("mutated")
    assert cc.state is ac.CandidateState.PROPOSED
    assert cc.limitations.entries == ()


def test_136ag_extensions_mapping_is_frozen_and_deep_copied():
    source = {"key": "value"}
    cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(_extensions=source), schema_version="1.0")
    source["key"] = "mutated"
    assert cc._extensions["key"] == "value"
    with pytest.raises(Exception):
        cc._extensions["key"] = "direct-mutation"  # type: ignore[index]


def test_136ag_cas_expectation_is_immutable():
    cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(), schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        cc.cas_expectation.expected_authority_kind = auth.AuthorityKind.CLTR  # type: ignore[misc]


def test_136ag_revocation_metadata_is_immutable():
    ha = ac.HumanAuthorization.from_dict(
        human_authorization_wire(state="revoked", revocation_metadata=_revocation_metadata()),
        schema_version="1.0",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        ha.revocation_metadata.reason_code = auth.ReasonCode.DIGEST_MISMATCH  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 14. Equality and hashing
# ---------------------------------------------------------------------------


def test_136ag_identical_human_authorization_records_compare_equal():
    wire = human_authorization_wire()
    a = ac.HumanAuthorization.from_dict(wire, schema_version="1.0")
    b = ac.HumanAuthorization.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert a == b


def test_136ag_one_changed_field_causes_inequality():
    a = ac.HumanAuthorization.from_dict(human_authorization_wire(principal="alice@example.com"), schema_version="1.0")
    b = ac.HumanAuthorization.from_dict(human_authorization_wire(principal="bob@example.com"), schema_version="1.0")
    assert a != b


def test_136ag_same_record_id_different_content_not_equal():
    a = ac.HumanAuthorization.from_dict(
        human_authorization_wire(record_id="humanauth-9990099", state="issued"), schema_version="1.0"
    )
    b = ac.HumanAuthorization.from_dict(
        human_authorization_wire(
            record_id="humanauth-9990099", state="revoked", revocation_metadata=_revocation_metadata()
        ),
        schema_version="1.0",
    )
    assert a != b


def test_136ag_same_digest_does_not_imply_equality():
    a = ac.HumanAuthorization.from_dict(
        human_authorization_wire(record_id="humanauth-1000001", record_digest=_hex("1")), schema_version="1.0"
    )
    b = ac.HumanAuthorization.from_dict(
        human_authorization_wire(record_id="humanauth-1000002", record_digest=_hex("1")), schema_version="1.0"
    )
    assert a != b


def test_136ag_evidence_order_is_equality_significant():
    item_a = _evidence_item("readypkg-0000001a", "1")
    item_b = _evidence_item("readypkg-0000002a", "2")
    cert1 = ac.Certification.from_dict(certification_wire(verifier_evidence=[item_a, item_b]), schema_version="1.0")
    cert2 = ac.Certification.from_dict(certification_wire(verifier_evidence=[item_b, item_a]), schema_version="1.0")
    assert cert1 != cert2


def test_136ag_cas_change_remains_observable_in_equality():
    cas_a = _cas_expectation()
    cas_b = _cas_expectation()
    cas_b["expected_authority_kind"] = "cltr"
    a = ac.CutoverCandidate.from_dict(cutover_candidate_wire(cas_expectation=cas_a), schema_version="1.0")
    b = ac.CutoverCandidate.from_dict(cutover_candidate_wire(cas_expectation=cas_b), schema_version="1.0")
    assert a != b


def test_136ag_timestamp_string_differences_remain_observable():
    a = ac.HumanAuthorization.from_dict(human_authorization_wire(created_at="2026-07-18T00:00:00Z"), schema_version="1.0")
    b = ac.HumanAuthorization.from_dict(human_authorization_wire(created_at="2026-07-18T00:00:00.0Z"), schema_version="1.0")
    assert a != b


def test_136ag_cutover_candidate_not_hashable_when_extensions_present():
    cc = ac.CutoverCandidate.from_dict(cutover_candidate_wire(_extensions={"a": "b"}), schema_version="1.0")
    with pytest.raises(TypeError):
        hash(cc)


# ---------------------------------------------------------------------------
# 15. Error behavior
# ---------------------------------------------------------------------------


def test_136ag_unknown_field_rejected_and_fails_closed():
    for wire_factory, cls in (
        (human_authorization_wire, ac.HumanAuthorization),
        (cutover_candidate_wire, ac.CutoverCandidate),
        (certification_wire, ac.Certification),
    ):
        wire = wire_factory()
        wire["totally_unknown_field"] = "value"
        with pytest.raises(auth_errors.TypedModelConstructionError):
            cls.from_dict(wire, schema_version="1.0")


def test_136ag_missing_required_field_rejected():
    for wire_factory, cls in (
        (human_authorization_wire, ac.HumanAuthorization),
        (cutover_candidate_wire, ac.CutoverCandidate),
        (certification_wire, ac.Certification),
    ):
        wire = wire_factory()
        del wire["state"]
        with pytest.raises(auth_errors.TypedModelConstructionError):
            cls.from_dict(wire, schema_version="1.0")


def test_136ag_enum_construction_raises_bare_value_error_not_typed_model_error():
    """CONFIRMED-136AC-1, re-derived independently: enum construction on a
    bad wire value raises bare ValueError, not a TypedModelError subclass.
    Remains fail-closed (construction still fails) -- Non-Blocking unless a
    concrete correctness/safety consequence is shown, which is not
    observed here: the payload is still rejected, just via a different
    exception type."""
    wire = human_authorization_wire(state="not-a-real-state")
    with pytest.raises(ValueError) as excinfo:
        ac.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert not issubclass(excinfo.type, auth_errors.TypedModelError)


def test_136ag_errors_do_not_leak_full_evidence_payload():
    bad_item = {"record_id": "SECRET-LOOKING-VALUE-DO-NOT-LEAK", "record_family": "readiness_package"}
    with pytest.raises(Exception) as excinfo:
        ac.Certification.from_dict(certification_wire(verifier_evidence=[bad_item]), schema_version="1.0")
    assert "SECRET-LOOKING-VALUE-DO-NOT-LEAK" not in str(excinfo.value)


def test_136ag_authority_role_authoritative_forbidden_on_all_three_records():
    for wire_factory, cls in (
        (human_authorization_wire, ac.HumanAuthorization),
        (cutover_candidate_wire, ac.CutoverCandidate),
        (certification_wire, ac.Certification),
    ):
        wire = wire_factory(authority_disclosure=_disclosure(role="authoritative"))
        with pytest.raises(auth_errors.TypedModelInternalInvariantError):
            cls.from_dict(wire, schema_version="1.0")


def test_136ag_invalid_cas_expectation_wrong_enum_rejected():
    bad_cas = _cas_expectation()
    bad_cas["expected_journal_lock_state"] = "half-locked"
    with pytest.raises(Exception):
        ac.CutoverCandidate.from_dict(cutover_candidate_wire(cas_expectation=bad_cas), schema_version="1.0")


# ---------------------------------------------------------------------------
# 16. Round trip
# ---------------------------------------------------------------------------


def test_136ag_human_authorization_minimal_round_trip(schema_registry):
    wire = human_authorization_wire()
    assert_schema_valid(wire, HUMAN_AUTHORIZATION_SCHEMA_ID, schema_registry)
    ha = ac.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert ha.to_dict() == wire


def test_136ag_human_authorization_revoked_round_trip(schema_registry):
    wire = human_authorization_wire(state="revoked", revocation_metadata=_revocation_metadata())
    assert_schema_valid(wire, HUMAN_AUTHORIZATION_SCHEMA_ID, schema_registry)
    ha = ac.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert ha.to_dict() == wire


def test_136ag_human_authorization_used_round_trip(schema_registry):
    wire = human_authorization_wire(state="used", use_binding=_use_binding())
    assert_schema_valid(wire, HUMAN_AUTHORIZATION_SCHEMA_ID, schema_registry)
    ha = ac.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert ha.to_dict() == wire


def test_136ag_human_authorization_signed_attestation_round_trip(schema_registry):
    wire = human_authorization_wire(
        method="signed_attestation",
        proof_reference={
            "record_id": "proofrec-9990001", "record_digest": _hex("7"), "record_family": "human_authorization",
        },
        limitations=["a limitation"],
    )
    assert_schema_valid(wire, HUMAN_AUTHORIZATION_SCHEMA_ID, schema_registry)
    ha = ac.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert ha.to_dict() == wire


def test_136ag_cutover_candidate_minimal_round_trip(schema_registry):
    wire = cutover_candidate_wire()
    assert_schema_valid(wire, CUTOVER_CANDIDATE_SCHEMA_ID, schema_registry)
    cc = ac.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert cc.to_dict() == wire


def test_136ag_cutover_candidate_maximal_round_trip(schema_registry):
    wire = cutover_candidate_wire(
        state="certified", limitations=["l1", "l2"], _extensions={"note": "annotation"}
    )
    assert_schema_valid(wire, CUTOVER_CANDIDATE_SCHEMA_ID, schema_registry)
    cc = ac.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert cc.to_dict() == wire


def test_136ag_certification_minimal_round_trip(schema_registry):
    wire = certification_wire()
    assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    cert = ac.Certification.from_dict(wire, schema_version="1.0")
    assert cert.to_dict() == wire


def test_136ag_certification_evidence_rich_round_trip(schema_registry):
    items = [_evidence_item(f"readypkg-{i:08x}", "1") for i in range(10)]
    wire = certification_wire(verifier_evidence=items)
    assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    cert = ac.Certification.from_dict(wire, schema_version="1.0")
    assert cert.to_dict() == wire


def test_136ag_certification_same_epoch_round_trip(schema_registry):
    same_ref = _epoch_ref("authepoch-9990006", "5")
    wire = certification_wire(
        source_authority_reference=dict(same_ref), target_epoch_reference=dict(same_ref)
    )
    assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    cert = ac.Certification.from_dict(wire, schema_version="1.0")
    assert cert.to_dict() == wire


def test_136ag_certification_stale_round_trip(schema_registry):
    wire = certification_wire(state="stale", staleness=_staleness())
    assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    cert = ac.Certification.from_dict(wire, schema_version="1.0")
    assert cert.to_dict() == wire


def test_136ag_certification_invalidated_round_trip(schema_registry):
    wire = certification_wire(state="invalidated", invalidation=_invalidation())
    assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    cert = ac.Certification.from_dict(wire, schema_version="1.0")
    assert cert.to_dict() == wire


# ---------------------------------------------------------------------------
# 17. Runtime isolation / no side effects
# ---------------------------------------------------------------------------


PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "runtime",
)


def test_136ag_no_production_module_imports_authority_package():
    pattern = re.compile(r"^\s*(?:from|import)\s+pcae\.cltr\.authority\b")
    offenders = []
    for root in PRODUCTION_SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if pattern.search(path.read_text()):
                offenders.append(str(path))
    cltr_root = REPO_ROOT / "src" / "pcae" / "cltr"
    for path in cltr_root.glob("*.py"):
        if pattern.search(path.read_text()):
            offenders.append(str(path))
    assert offenders == []


def test_136ag_authority_package_does_not_import_production_lifecycle_modules():
    forbidden_modules = (
        "pcae.cltr.lifecycle", "pcae.cltr.finalization", "pcae.cltr.notification",
        "pcae.cltr.marker", "pcae.cltr.receipt", "pcae.commands", "pcae.core", "pcae.runtime",
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


def test_136ag_package_import_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(ac)


def test_136ag_no_side_effects_during_serialization_or_equality(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during serialization/equality")

    monkeypatch.setattr(socket, "socket", _boom)
    ha = ac.HumanAuthorization.from_dict(human_authorization_wire(), schema_version="1.0")
    ha.to_dict()
    _ = (ha == ha)
    repr(ha)


# ---------------------------------------------------------------------------
# 18. Scope-guard verification (narrowed by 136AF; must still forbid all
#     nine later record families and permit only this group's three).
# ---------------------------------------------------------------------------


SCOPE_GUARDED_TEST_FILES = (
    REPO_ROOT / "tests" / "test_cltr_authority_136z_shared_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136aa_shared_core_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ab_authority_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ac_authority_core_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ad_request_readiness.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ae_request_readiness_independent.py",
)


def test_136ag_adjacent_scope_guard_test_files_still_forbid_all_later_models():
    """Every adjacent guarded test file must still textually name all nine
    not-yet-implemented record families as forbidden -- narrowing removes
    a just-authorized family from a "still forbidden" list, it never
    replaces the list with a wildcard allowance."""
    still_forbidden_after_136af = (
        "PublicationAttempt", "PublicationEvidence", "ConcurrencyConflict",
        "RecoveryJournalEntry", "NotificationAuthorityBinding", "MarkerAuthorityBinding",
        "FinalizationReceiptAuthorityBinding", "CompatibilityState", "QuarantineRecord",
    )
    for path in SCOPE_GUARDED_TEST_FILES:
        if not path.exists():
            continue
        text = path.read_text()
        if "LATER_MODEL_CLASS_NAMES" not in text:
            continue
        for later in still_forbidden_after_136af:
            assert later in text, f"{path} no longer names {later} as forbidden"


def test_136ag_own_module_scope_guard_matches_exactly_the_three_new_families():
    tree = ast.parse(MODULE_UNDER_TEST.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_models = class_names & {
        "HumanAuthorization", "CutoverCandidate", "Certification", *LATER_MODEL_CLASS_NAMES,
        "AuthorityEpoch", "AuthorityState", "CutoverRequest", "ReadinessPackage",
    }
    assert record_family_models == {"HumanAuthorization", "CutoverCandidate", "Certification"}


# ---------------------------------------------------------------------------
# 19. Packaging verification
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136ag_wheel_contains_authorization_candidate_module_no_later_family(tmp_path: Path):
    import subprocess

    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()

    assert "pcae/cltr/authority/authorization_candidate.py" in names
    # publication.py narrowed off this list by Phase 136AH: it is now an
    # authorized, legitimately-implemented module (Group 5).
    for forbidden in ("recovery", "bindings", "compatibility_quarantine"):
        assert f"pcae/cltr/authority/{forbidden}.py" not in names


@pytest.mark.slow
def test_136ag_sdist_includes_authorization_candidate_module(tmp_path: Path):
    import subprocess

    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(sdists) == 1

    import tarfile

    with tarfile.open(sdists[0]) as archive:
        names = archive.getnames()
    assert any(name.endswith("pcae/cltr/authority/authorization_candidate.py") for name in names)


@pytest.mark.slow
def test_136ag_installed_wheel_constructs_all_three_new_models_outside_repository(tmp_path: Path):
    import subprocess
    import venv

    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv136ag"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    venv_python = venv_dir / "bin" / "python"
    assert venv_python.exists()

    install = subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheels[0]), "jsonschema>=4.18,<5"],
        check=False, capture_output=True, text=True,
    )
    assert install.returncode == 0, install.stderr

    outside_cwd = tmp_path / "elsewhere"
    outside_cwd.mkdir()
    probe_script = (
        "from pcae.cltr import authority as auth\n"
        "wire = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/human_authorization.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0', 'record_type': 'human_authorization',\n"
        "    'record_id': 'humanauth-9990001', 'record_digest': 'a' * 64,\n"
        "    'created_at': '2026-07-18T00:00:00Z', 'phase_id': '136AG', 'migration_epoch': 'epoch-136ag',\n"
        "    'principal': 'operator@example.com', 'method': 'manual_review',\n"
        "    'request_reference': {'record_id': 'cutreq-9990001', 'record_digest': 'b' * 64,\n"
        "        'record_family': 'cutover_request',\n"
        "        'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json',\n"
        "        'schema_version': '1.0'},\n"
        "    'readiness_reference': {'record_id': 'readypkg-9990001', 'record_digest': 'c' * 64,\n"
        "        'record_family': 'readiness_package',\n"
        "        'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/readiness_package.schema.json',\n"
        "        'schema_version': '1.0'},\n"
        "    'target_reference': {'record_id': 'authepoch-9990002', 'record_digest': 'd' * 64,\n"
        "        'record_family': 'authority_epoch',\n"
        "        'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json',\n"
        "        'schema_version': '1.0'},\n"
        "    'issued_at': '2026-07-18T00:00:00Z', 'expires_at': '2026-07-19T00:00:00Z',\n"
        "    'state': 'used', 'use_binding': {'record_id': 'pubattem-9990001', 'record_digest': 'e' * 64,\n"
        "        'record_family': 'publication_attempt'},\n"
        "    'replay_binding': 'replay-token-9990001', 'risk_acknowledgement': True,\n"
        "    'limitations': [], 'authority_disclosure': {'authority_role': 'derivative',\n"
        "        'is_authoritative': False, 'disclosure_text': 'probe'},\n"
        "}\n"
        "ha = auth.HumanAuthorization.from_dict(wire, schema_version='1.0')\n"
        "assert ha.to_dict() == wire\n"
        "assert ha.use_binding.record_family.value == 'publication_attempt'\n"
        "print('OK')\n"
    )
    probe = subprocess.run(
        [str(venv_python), "-c", probe_script], cwd=str(outside_cwd), capture_output=True, text=True,
    )
    assert probe.returncode == 0, probe.stderr
    assert "OK" in probe.stdout


# ---------------------------------------------------------------------------
# 20. Adversarial matrix (consolidated table-driven pass)
# ---------------------------------------------------------------------------


ADVERSARIAL_CASES = [
    ("human_authorization_minimal_valid", lambda: human_authorization_wire(), True, ac.HumanAuthorization),
    (
        "human_authorization_revoked_without_metadata",
        lambda: human_authorization_wire(state="revoked"),
        False,
        ac.HumanAuthorization,
    ),
    (
        "human_authorization_metadata_outside_revoked",
        lambda: human_authorization_wire(revocation_metadata=_revocation_metadata()),
        False,
        ac.HumanAuthorization,
    ),
    (
        "human_authorization_used_without_use_binding",
        lambda: human_authorization_wire(state="used"),
        False,
        ac.HumanAuthorization,
    ),
    (
        "human_authorization_future_publication_attempt_reference",
        lambda: human_authorization_wire(state="used", use_binding=_use_binding()),
        True,
        ac.HumanAuthorization,
    ),
    (
        "human_authorization_signed_attestation_without_proof",
        lambda: human_authorization_wire(method="signed_attestation"),
        False,
        ac.HumanAuthorization,
    ),
    (
        "human_authorization_wrong_cross_family_schema_identity",
        lambda: human_authorization_wire(
            request_reference={"record_id": "cutreq-9990001", "record_digest": _hex("2"), "record_family": "cutover_request"}
        ),
        False,
        ac.HumanAuthorization,
    ),
    ("cutover_candidate_minimal_valid", lambda: cutover_candidate_wire(), True, ac.CutoverCandidate),
    (
        "cutover_candidate_authoritative_role_in_initial_state",
        lambda: cutover_candidate_wire(state="proposed", authority_disclosure=_disclosure(role="authoritative")),
        False,
        ac.CutoverCandidate,
    ),
    (
        "cutover_candidate_authoritative_role_in_certified_state",
        lambda: cutover_candidate_wire(state="certified", authority_disclosure=_disclosure(role="authoritative")),
        False,
        ac.CutoverCandidate,
    ),
    (
        "cutover_candidate_malformed_cas_expectation",
        lambda: cutover_candidate_wire(cas_expectation={"expected_authority_kind": "legacy"}),
        False,
        ac.CutoverCandidate,
    ),
    (
        "cutover_candidate_semantically_stale_but_schema_valid_cas",
        lambda: cutover_candidate_wire(
            cas_expectation=_cas_expectation(), state="proposed"
        ),
        True,
        ac.CutoverCandidate,
    ),
    (
        "cutover_candidate_injected_phase_id",
        lambda: {**cutover_candidate_wire(), "phase_id": "136AG"},
        False,
        ac.CutoverCandidate,
    ),
    ("certification_minimal_valid", lambda: certification_wire(), True, ac.Certification),
    (
        "certification_source_and_target_same_epoch",
        lambda: certification_wire(
            source_authority_reference=_epoch_ref("authepoch-9990007", "9"),
            target_epoch_reference=_epoch_ref("authepoch-9990007", "9"),
        ),
        True,
        ac.Certification,
    ),
    (
        "certification_64_verifier_evidence_items",
        lambda: certification_wire(
            verifier_evidence=[_evidence_item(f"readypkg-{i:08x}", "1") for i in range(64)]
        ),
        True,
        ac.Certification,
    ),
    (
        "certification_65_verifier_evidence_items",
        lambda: certification_wire(
            verifier_evidence=[_evidence_item(f"readypkg-{i:08x}", "1") for i in range(65)]
        ),
        False,
        ac.Certification,
    ),
    (
        "certification_mixed_family_evidence",
        lambda: certification_wire(
            verifier_evidence=[
                _evidence_item("readypkg-0000001a", "1", "readiness_package"),
                _evidence_item("humanauth-0000001a", "2", "human_authorization"),
            ]
        ),
        True,
        ac.Certification,
    ),
    (
        "certification_injected_certifier_principal",
        lambda: {**certification_wire(), "certifier_principal": "someone@example.com"},
        False,
        ac.Certification,
    ),
    (
        "certification_schema_valid_but_operationally_false_evidence",
        lambda: certification_wire(
            state="certified", verifier_evidence=[_evidence_item("readypkg-9999999a", "0")]
        ),
        True,
        ac.Certification,
    ),
]


@pytest.mark.parametrize("name,wire_factory,expected_accepted,model_cls", ADVERSARIAL_CASES, ids=[c[0] for c in ADVERSARIAL_CASES])
def test_136ag_adversarial_matrix(name, wire_factory, expected_accepted, model_cls):
    wire = wire_factory()
    if expected_accepted:
        model_cls.from_dict(wire, schema_version="1.0")
    else:
        with pytest.raises(Exception):
            model_cls.from_dict(wire, schema_version="1.0")
