"""Phase 136AF: Stage 3 Typed Authority Model Authorization and Candidate
Implementation (Typed Model Implementation Group 4).

Focused tests for ``src/pcae/cltr/authority/authorization_candidate.py``:
the ``HumanAuthorization``, ``CutoverCandidate``, and ``Certification``
typed record models. Covers exact field mapping, strict constructor
behavior, family-restriction enforcement, conditional branches, enum
fidelity, schema conformance, no-later-group-model inventory, no-
authorization/no-eligibility/no-certification semantics, no-side-effect,
and runtime-isolation.

This module implements only Typed Model Implementation Group 4
(``HumanAuthorization``, ``CutoverCandidate``, ``Certification``). No other
record-family model (``PublicationAttempt``, ``PublicationEvidence``,
``ConcurrencyConflict``, ``RecoveryJournalEntry``,
``NotificationAuthorityBinding``, ``MarkerAuthorityBinding``,
``FinalizationReceiptAuthorityBinding``, ``CompatibilityState``,
``QuarantineRecord``) is implemented or exercised here.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import socket
import subprocess
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import authorization_candidate as ac
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
AUTHORIZATION_CANDIDATE_MODULE = AUTHORITY_PACKAGE_DIR / "authorization_candidate.py"

PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "cltr",
    REPO_ROOT / "src" / "pcae" / "runtime",
)

FORBIDDEN_SYMBOLS = (
    "authenticate",
    "verify_signature",
    "is_valid",
    "approve_authorization",
    "reject_authorization",
    "calculate_eligibility",
    "is_eligible",
    "can_cutover",
    "certify",
    "verify_evidence",
    "select_authority",
    "resolve_reference",
    "verify_digest",
    "persist",
    "publish",
    "execute_cutover",
    "recover",
)

LATER_GROUP_MODEL_NAMES = (
    # Narrowed by Phase 136AH: `PublicationAttempt`/`PublicationEvidence`
    # (Group 5) are now authorized, legitimately-implemented record-family
    # models -- removed from this still-forbidden list. Narrowed further by
    # Phase 136AJ: `ConcurrencyConflict`/`RecoveryJournalEntry` (Group 6)
    # are now authorized, legitimately-implemented record-family models --
    # removed from this still-forbidden list. Narrowed further by Phase
    # 136AL: `NotificationAuthorityBinding` (Group 7) is now authorized,
    # legitimately-implemented record-family model -- removed from this
    # still-forbidden list.
    "MarkerAuthorityBinding",
    "FinalizationReceiptAuthorityBinding",
    "CompatibilityState",
    "QuarantineRecord",
)

HUMAN_AUTHORIZATION_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/human_authorization.schema.json"
)
CUTOVER_CANDIDATE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/cutover_candidate.schema.json"
)
CERTIFICATION_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/certification.schema.json"
CUTOVER_REQUEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json"
READINESS_PACKAGE_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/readiness_package.schema.json"


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
    assert result.status is not OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# Wire fixtures
# ---------------------------------------------------------------------------


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Non-authoritative schema-validated companion record.",
    }


def _ref(record_id: str, digest: str, family: str, *, with_schema: str | None = None) -> dict:
    out = {"record_id": record_id, "record_digest": _sha256_hex(digest), "record_family": family}
    if with_schema is not None:
        out["schema_id"] = with_schema
        out["schema_version"] = "1.0"
    return out


def _request_ref(record_id: str = "cutreq-00000001", digest: str = "a") -> dict:
    return _ref(record_id, digest, "cutover_request", with_schema=CUTOVER_REQUEST_SCHEMA_ID)


def _readiness_ref(record_id: str = "readypkg-0000001", digest: str = "b") -> dict:
    return _ref(record_id, digest, "readiness_package", with_schema=READINESS_PACKAGE_SCHEMA_ID)


def _epoch_ref(record_id: str = "authepoch-0000001", digest: str = "c") -> dict:
    return _ref(record_id, digest, "authority_epoch", with_schema=HUMAN_AUTHORIZATION_SCHEMA_ID)


def _epoch_ref_bare(record_id: str = "authepoch-0000001", digest: str = "c") -> dict:
    return _ref(record_id, digest, "authority_epoch")


def _candidate_ref(record_id: str = "cutcand-00000001", digest: str = "d") -> dict:
    return _ref(record_id, digest, "cutover_candidate", with_schema=CUTOVER_CANDIDATE_SCHEMA_ID)


def _authorization_ref(record_id: str = "humanauth-0000001", digest: str = "e") -> dict:
    return _ref(record_id, digest, "human_authorization", with_schema=HUMAN_AUTHORIZATION_SCHEMA_ID)


def _certification_ref(record_id: str = "certif-00000001", digest: str = "f") -> dict:
    return _ref(record_id, digest, "certification", with_schema=CERTIFICATION_SCHEMA_ID)


def _generation_ref(gen_id: str = "generatn-0000001", digest: str = "1") -> dict:
    return {"generation_id": gen_id, "generation_digest": _sha256_hex(digest)}


def _cas_expectation_wire(**overrides) -> dict:
    record = {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _epoch_ref_bare("authepoch-0000003", "2"),
        "expected_authoritative_generation": _generation_ref(),
        "expected_authority_pointer_digest": _sha256_hex("3"),
        "expected_authority_state_digest": _sha256_hex("4"),
        "expected_migration_epoch": "epoch-001",
        "expected_source_lifecycle_state": "CERTIFIED",
        "expected_compatibility_mode": "legacy_authoritative",
        "expected_journal_lock_state": "unlocked",
        "expected_request_reference": _request_ref(),
        "expected_certification_reference": _certification_ref(),
    }
    record.update(overrides)
    return record


def _valid_human_authorization_wire(**overrides) -> dict:
    record = {
        "schema_id": HUMAN_AUTHORIZATION_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "human_authorization",
        "record_id": "humanauth-0000001",
        "record_digest": _sha256_hex("e"),
        "created_at": "2026-07-17T12:00:00Z",
        "phase_id": "136AF",
        "migration_epoch": "epoch-001",
        "principal": "operator@example.com",
        "method": "manual_review",
        "request_reference": _request_ref(),
        "readiness_reference": _readiness_ref(),
        "target_reference": _epoch_ref(),
        "issued_at": "2026-07-17T12:00:00Z",
        "expires_at": "2026-07-18T12:00:00Z",
        "state": "issued",
        "replay_binding": "replay-token-0001",
        "risk_acknowledgement": True,
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _valid_cutover_candidate_wire(**overrides) -> dict:
    record = {
        "schema_id": CUTOVER_CANDIDATE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "cutover_candidate",
        "record_id": "cutcand-00000001",
        "record_digest": _sha256_hex("d"),
        "created_at": "2026-07-17T12:00:00Z",
        "migration_epoch": "epoch-001",
        "stage2_generation_reference": _ref("generatn-0000002", "5", "authority_epoch"),
        "cas_expectation": _cas_expectation_wire(),
        "state": "proposed",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _valid_certification_wire(**overrides) -> dict:
    record = {
        "schema_id": CERTIFICATION_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "certification",
        "record_id": "certif-00000001",
        "record_digest": _sha256_hex("f"),
        "created_at": "2026-07-17T12:00:00Z",
        "phase_id": "136AF",
        "migration_epoch": "epoch-001",
        "candidate_reference": _candidate_ref(),
        "request_reference": _request_ref(),
        "readiness_reference": _readiness_ref(),
        "authorization_reference": _authorization_ref(),
        "source_authority_reference": _epoch_ref_bare("authepoch-0000004", "6"),
        "target_epoch_reference": _epoch_ref_bare("authepoch-0000005", "7"),
        "cas_expectation": _cas_expectation_wire(),
        "verifier_evidence": [],
        "state": "pending",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# 1. Inventory
# ---------------------------------------------------------------------------


def test_136af_exactly_seven_record_family_models_exist_in_package():
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
    ):
        assert expected in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136af_no_later_group_model_class_exists_in_authorization_candidate_module():
    tree = ast.parse(AUTHORIZATION_CANDIDATE_MODULE.read_text())
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for expected in ("HumanAuthorization", "CutoverCandidate", "Certification"):
        assert expected in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136af_expected_public_exports_present():
    for name in (
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
    ):
        assert hasattr(auth, name)
        assert name in auth.__all__


def test_136af_models_are_frozen_dataclasses():
    for model in (auth.HumanAuthorization, auth.CutoverCandidate, auth.Certification):
        assert dataclasses.is_dataclass(model)
        assert model.__dataclass_params__.frozen


# ---------------------------------------------------------------------------
# 2. HumanAuthorization: construction / round trip
# ---------------------------------------------------------------------------


def test_136af_human_authorization_minimal_valid_construction(schema_registry):
    wire = _valid_human_authorization_wire()
    _assert_schema_valid(wire, HUMAN_AUTHORIZATION_SCHEMA_ID, schema_registry)
    model = auth.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert model.revocation_metadata is auth.ABSENT
    assert model.use_binding is auth.ABSENT
    assert model.proof_reference is auth.ABSENT
    assert model.to_dict() == wire


def test_136af_human_authorization_revoked_state_with_metadata(schema_registry):
    wire = _valid_human_authorization_wire(
        state="revoked",
        revocation_metadata={
            "revoked_at": "2026-07-17T13:00:00Z",
            "revoked_by": "supervisor@example.com",
            "reason_code": "stale_authorization",
        },
    )
    _assert_schema_valid(wire, HUMAN_AUTHORIZATION_SCHEMA_ID, schema_registry)
    model = auth.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert model.revocation_metadata.reason_code is auth.ReasonCode.STALE_AUTHORIZATION
    assert model.to_dict() == wire


def test_136af_human_authorization_used_state_with_binding(schema_registry):
    wire = _valid_human_authorization_wire(
        state="used",
        use_binding=_ref("pubattempt-000001", "9", "publication_attempt"),
    )
    _assert_schema_valid(wire, HUMAN_AUTHORIZATION_SCHEMA_ID, schema_registry)
    model = auth.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert model.use_binding.record_family is auth.RecordFamily.PUBLICATION_ATTEMPT
    assert model.to_dict() == wire


def test_136af_human_authorization_signed_attestation_requires_proof_reference(schema_registry):
    wire = _valid_human_authorization_wire(
        method="signed_attestation",
        proof_reference=_ref("proofrec-00000001", "8", "human_authorization"),
    )
    _assert_schema_valid(wire, HUMAN_AUTHORIZATION_SCHEMA_ID, schema_registry)
    model = auth.HumanAuthorization.from_dict(wire, schema_version="1.0")
    assert model.proof_reference is not auth.ABSENT
    assert model.to_dict() == wire


def test_136af_human_authorization_signed_attestation_missing_proof_reference_rejected():
    wire = _valid_human_authorization_wire(method="signed_attestation")
    with pytest.raises(Exception):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_manual_review_with_proof_reference_rejected():
    wire = _valid_human_authorization_wire(
        proof_reference=_ref("proofrec-00000001", "8", "human_authorization")
    )
    with pytest.raises(Exception):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_revoked_without_metadata_rejected():
    wire = _valid_human_authorization_wire(state="revoked")
    with pytest.raises(Exception):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_used_without_binding_rejected():
    wire = _valid_human_authorization_wire(state="used")
    with pytest.raises(Exception):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_non_revoked_with_metadata_rejected():
    wire = _valid_human_authorization_wire(
        revocation_metadata={
            "revoked_at": "2026-07-17T13:00:00Z",
            "revoked_by": "supervisor@example.com",
            "reason_code": "stale_authorization",
        }
    )
    with pytest.raises(Exception):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_unknown_field_rejected():
    wire = _valid_human_authorization_wire(scope="global")
    with pytest.raises(Exception):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_no_extensions_escape_hatch():
    wire = _valid_human_authorization_wire(_extensions={})
    with pytest.raises(Exception):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_unsupported_schema_version_rejected():
    wire = _valid_human_authorization_wire()
    with pytest.raises(auth.UnsupportedSchemaVersionError):
        auth.HumanAuthorization.from_dict(wire, schema_version="2.0")


def test_136af_human_authorization_wrong_schema_id_rejected():
    wire = _valid_human_authorization_wire(schema_id="https://pcae.local/wrong.json")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_wrong_record_type_rejected():
    wire = _valid_human_authorization_wire(record_type="cutover_candidate")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_missing_required_field_rejected():
    wire = _valid_human_authorization_wire()
    del wire["risk_acknowledgement"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_risk_acknowledgement_must_be_true():
    wire = _valid_human_authorization_wire(risk_acknowledgement=False)
    with pytest.raises(Exception):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_forbids_authoritative_role():
    wire = _valid_human_authorization_wire(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        }
    )
    with pytest.raises(Exception):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_wrong_family_request_reference_rejected():
    wire = _valid_human_authorization_wire(request_reference=_readiness_ref())
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_request_reference_requires_schema_id_and_version():
    ref = _request_ref()
    del ref["schema_id"]
    wire = _valid_human_authorization_wire(request_reference=ref)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_use_binding_wrong_family_rejected():
    wire = _valid_human_authorization_wire(
        state="used", use_binding=_ref("wrongfam-00000001", "9", "cutover_request")
    )
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_replay_binding_pattern_enforced():
    wire = _valid_human_authorization_wire(replay_binding="not a valid token!!")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_method_enum_strictness():
    wire = _valid_human_authorization_wire(method="MANUAL_REVIEW")
    with pytest.raises(ValueError):
        auth.HumanAuthorization.from_dict(wire, schema_version="1.0")


def test_136af_human_authorization_state_enum_members_match_schema():
    assert {m.value for m in auth.AuthorizationState} == {"issued", "used", "revoked", "expired"}


def test_136af_human_authorization_method_enum_members_match_schema():
    assert {m.value for m in auth.AuthorizationMethod} == {"manual_review", "signed_attestation"}


def test_136af_human_authorization_top_level_assignment_raises():
    wire = _valid_human_authorization_wire()
    model = auth.HumanAuthorization.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.state = auth.AuthorizationState.EXPIRED


# ---------------------------------------------------------------------------
# 3. CutoverCandidate: construction / round trip
# ---------------------------------------------------------------------------


def test_136af_cutover_candidate_minimal_valid_construction(schema_registry):
    wire = _valid_cutover_candidate_wire()
    _assert_schema_valid(wire, CUTOVER_CANDIDATE_SCHEMA_ID, schema_registry)
    model = auth.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert model._extensions is auth.ABSENT
    assert model.to_dict() == wire


def test_136af_cutover_candidate_with_extensions(schema_registry):
    wire = _valid_cutover_candidate_wire(_extensions={"note": "informational"})
    _assert_schema_valid(wire, CUTOVER_CANDIDATE_SCHEMA_ID, schema_registry)
    model = auth.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert model._extensions["note"] == "informational"
    assert model.to_dict() == wire


def test_136af_cutover_candidate_extensions_non_string_value_rejected():
    wire = _valid_cutover_candidate_wire(_extensions={"note": 5})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CutoverCandidate.from_dict(wire, schema_version="1.0")


def test_136af_cutover_candidate_extensions_reserved_key_collision_rejected():
    wire = _valid_cutover_candidate_wire(_extensions={"state": "override"})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CutoverCandidate.from_dict(wire, schema_version="1.0")


def test_136af_cutover_candidate_extensions_explicit_null_rejected():
    wire = _valid_cutover_candidate_wire(_extensions=None)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CutoverCandidate.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "state", ["proposed", "verified", "certifying", "certified", "superseded", "quarantined"]
)
def test_136af_cutover_candidate_all_states_construct(schema_registry, state):
    wire = _valid_cutover_candidate_wire(state=state)
    _assert_schema_valid(wire, CUTOVER_CANDIDATE_SCHEMA_ID, schema_registry)
    model = auth.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert model.state.value == state


def test_136af_cutover_candidate_certified_state_does_not_imply_authoritative_role():
    wire = _valid_cutover_candidate_wire(state="certified")
    model = auth.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.is_authoritative is False


def test_136af_cutover_candidate_forbids_authoritative_role_even_when_certified():
    wire = _valid_cutover_candidate_wire(
        state="certified",
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        },
    )
    with pytest.raises(Exception):
        auth.CutoverCandidate.from_dict(wire, schema_version="1.0")


def test_136af_cutover_candidate_unknown_field_rejected():
    wire = _valid_cutover_candidate_wire(readiness_reference=_readiness_ref())
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CutoverCandidate.from_dict(wire, schema_version="1.0")


def test_136af_cutover_candidate_missing_required_field_rejected():
    wire = _valid_cutover_candidate_wire()
    del wire["cas_expectation"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CutoverCandidate.from_dict(wire, schema_version="1.0")


def test_136af_cutover_candidate_no_phase_id_field():
    wire = _valid_cutover_candidate_wire()
    assert "phase_id" not in wire
    model = auth.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert not hasattr(model, "phase_id")


def test_136af_cutover_candidate_state_enum_members_match_schema():
    assert {m.value for m in auth.CandidateState} == {
        "proposed",
        "verified",
        "certifying",
        "certified",
        "superseded",
        "quarantined",
    }


def test_136af_cutover_candidate_top_level_assignment_raises():
    wire = _valid_cutover_candidate_wire()
    model = auth.CutoverCandidate.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.state = auth.CandidateState.CERTIFIED


def test_136af_cutover_candidate_extensions_mutation_does_not_affect_model():
    wire = _valid_cutover_candidate_wire(_extensions={"note": "x"})
    model = auth.CutoverCandidate.from_dict(wire, schema_version="1.0")
    out = model.to_dict()
    out["_extensions"]["note"] = "mutated"
    assert model.to_dict()["_extensions"]["note"] == "x"


# ---------------------------------------------------------------------------
# 4. Certification: construction / round trip
# ---------------------------------------------------------------------------


def test_136af_certification_minimal_valid_construction(schema_registry):
    wire = _valid_certification_wire()
    _assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    assert model.staleness is auth.ABSENT
    assert model.invalidation is auth.ABSENT
    assert model.to_dict() == wire


def test_136af_certification_stale_state_with_disclosure(schema_registry):
    wire = _valid_certification_wire(
        state="stale",
        staleness={"detected_at": "2026-07-18T00:00:00Z", "reason_code": "stale_certification"},
    )
    _assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    assert model.staleness.reason_code is auth.ReasonCode.STALE_CERTIFICATION
    assert model.to_dict() == wire


def test_136af_certification_invalidated_state_with_disclosure(schema_registry):
    wire = _valid_certification_wire(
        state="invalidated",
        invalidation={"invalidated_at": "2026-07-18T00:00:00Z", "reason_code": "digest_mismatch"},
    )
    _assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    assert model.invalidation.reason_code is auth.ReasonCode.DIGEST_MISMATCH
    assert model.to_dict() == wire


def test_136af_certification_stale_without_disclosure_rejected():
    wire = _valid_certification_wire(state="stale")
    with pytest.raises(Exception):
        auth.Certification.from_dict(wire, schema_version="1.0")


def test_136af_certification_invalidated_without_disclosure_rejected():
    wire = _valid_certification_wire(state="invalidated")
    with pytest.raises(Exception):
        auth.Certification.from_dict(wire, schema_version="1.0")


def test_136af_certification_non_stale_with_staleness_rejected():
    wire = _valid_certification_wire(
        staleness={"detected_at": "2026-07-18T00:00:00Z", "reason_code": "stale_certification"}
    )
    with pytest.raises(Exception):
        auth.Certification.from_dict(wire, schema_version="1.0")


def test_136af_certification_no_certifier_principal_field():
    wire = _valid_certification_wire()
    assert "principal" not in wire
    assert "certifier_principal" not in wire


def test_136af_certification_verifier_evidence_may_be_empty(schema_registry):
    wire = _valid_certification_wire(verifier_evidence=[])
    _assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    assert model.verifier_evidence == ()


def test_136af_certification_verifier_evidence_no_family_restriction(schema_registry):
    wire = _valid_certification_wire(
        verifier_evidence=[
            _ref("readypkg-0000009", "1", "readiness_package"),
            _ref("cutcand-00000009", "2", "cutover_candidate"),
        ]
    )
    _assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    assert len(model.verifier_evidence) == 2
    assert model.to_dict() == wire


def test_136af_certification_verifier_evidence_preserves_order(schema_registry):
    refs = [_ref(f"readypkg-{i:07d}", str(i % 9 + 1), "readiness_package") for i in range(5)]
    wire = _valid_certification_wire(verifier_evidence=refs)
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    assert [r.record_id.value for r in model.verifier_evidence] == [r["record_id"] for r in refs]


def test_136af_certification_verifier_evidence_exceeds_max_items_rejected():
    refs = [_ref(f"readypkg-{i:07d}", str(i % 9 + 1), "readiness_package") for i in range(65)]
    wire = _valid_certification_wire(verifier_evidence=refs)
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.Certification.from_dict(wire, schema_version="1.0")


def test_136af_certification_forbids_authoritative_role():
    wire = _valid_certification_wire(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        }
    )
    with pytest.raises(Exception):
        auth.Certification.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "field,family",
    [
        ("candidate_reference", "cutover_candidate"),
        ("request_reference", "cutover_request"),
        ("readiness_reference", "readiness_package"),
        ("authorization_reference", "human_authorization"),
        ("source_authority_reference", "authority_epoch"),
        ("target_epoch_reference", "authority_epoch"),
    ],
)
def test_136af_certification_reference_wrong_family_rejected(field, family):
    wrong_family = "cutover_request" if family != "cutover_request" else "readiness_package"
    schema_by_family = {
        "cutover_request": CUTOVER_REQUEST_SCHEMA_ID,
        "readiness_package": READINESS_PACKAGE_SCHEMA_ID,
    }
    wire = _valid_certification_wire(
        **{
            field: _ref(
                "wrongfam-000001", "1", wrong_family, with_schema=schema_by_family[wrong_family]
            )
        }
    )
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.Certification.from_dict(wire, schema_version="1.0")


def test_136af_certification_source_and_target_epoch_may_reference_same_epoch(schema_registry):
    same = _epoch_ref_bare("authepoch-0000009", "9")
    wire = _valid_certification_wire(source_authority_reference=same, target_epoch_reference=same)
    _assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    assert model.source_authority_reference == model.target_epoch_reference


def test_136af_certification_epoch_reference_does_not_require_schema_id():
    ref = _epoch_ref_bare("authepoch-0000004", "6")
    assert "schema_id" not in ref
    wire = _valid_certification_wire(source_authority_reference=ref)
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    assert model.source_authority_reference.schema_id is auth.ABSENT


def test_136af_certification_state_enum_members_match_schema():
    assert {m.value for m in auth.CertificationState} == {"pending", "certified", "stale", "invalidated"}


def test_136af_certification_top_level_assignment_raises():
    wire = _valid_certification_wire()
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.state = auth.CertificationState.CERTIFIED


# ---------------------------------------------------------------------------
# 5. CasExpectation embedding (shared across CutoverCandidate/Certification)
# ---------------------------------------------------------------------------


def test_136af_cutover_candidate_cas_expectation_every_field_required():
    wire = _valid_cutover_candidate_wire()
    cas = dict(wire["cas_expectation"])
    del cas["expected_authority_kind"]
    wire["cas_expectation"] = cas
    with pytest.raises(auth.TypedModelConstructionError):
        auth.CutoverCandidate.from_dict(wire, schema_version="1.0")


def test_136af_certification_cas_expectation_self_reference_permitted_structurally(schema_registry):
    # A certification's own cas_expectation.expected_certification_reference
    # may structurally point at any certification id/digest, including in
    # principle the enclosing document's own -- Layer 2 schema shape cannot
    # compare a nested reference against its own envelope (Sec.12N-3).
    wire = _valid_certification_wire()
    wire["cas_expectation"]["expected_certification_reference"] = _ref(
        wire["record_id"], "f", "certification", with_schema=CERTIFICATION_SCHEMA_ID
    )
    _assert_schema_valid(wire, CERTIFICATION_SCHEMA_ID, schema_registry)
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    assert model.cas_expectation.expected_certification_reference.record_id.value == wire["record_id"]


def test_136af_cas_expectation_returned_type_is_shared_cas_expectation_class():
    wire = _valid_cutover_candidate_wire()
    model = auth.CutoverCandidate.from_dict(wire, schema_version="1.0")
    assert isinstance(model.cas_expectation, auth.CasExpectation)


# ---------------------------------------------------------------------------
# 6. Schema field-set parity
# ---------------------------------------------------------------------------


def test_136af_human_authorization_schema_field_set_matches_model_known_keys(schema_registry):
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "human_authorization.schema.json").read_text())
    assert set(schema["properties"].keys()) == ac._HUMAN_AUTHORIZATION_KNOWN_KEYS


def test_136af_cutover_candidate_schema_field_set_matches_model_known_keys():
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "cutover_candidate.schema.json").read_text())
    assert set(schema["properties"].keys()) == ac._CUTOVER_CANDIDATE_KNOWN_KEYS


def test_136af_certification_schema_field_set_matches_model_known_keys():
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "certification.schema.json").read_text())
    assert set(schema["properties"].keys()) == ac._CERTIFICATION_KNOWN_KEYS


# ---------------------------------------------------------------------------
# 7. Equality / immutability
# ---------------------------------------------------------------------------


def test_136af_human_authorization_structural_equality():
    wire = _valid_human_authorization_wire()
    a = auth.HumanAuthorization.from_dict(wire, schema_version="1.0")
    b = auth.HumanAuthorization.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert a == b


def test_136af_cutover_candidate_extension_differences_participate_in_equality():
    a = auth.CutoverCandidate.from_dict(
        _valid_cutover_candidate_wire(_extensions={"note": "a"}), schema_version="1.0"
    )
    b = auth.CutoverCandidate.from_dict(
        _valid_cutover_candidate_wire(_extensions={"note": "b"}), schema_version="1.0"
    )
    assert a != b


def test_136af_certification_verifier_evidence_order_difference_is_observable():
    refs_forward = [
        _ref("readypkg-0000001", "1", "readiness_package"),
        _ref("readypkg-0000002", "2", "readiness_package"),
    ]
    refs_reversed = list(reversed(refs_forward))
    a = auth.Certification.from_dict(
        _valid_certification_wire(verifier_evidence=refs_forward), schema_version="1.0"
    )
    b = auth.Certification.from_dict(
        _valid_certification_wire(verifier_evidence=refs_reversed), schema_version="1.0"
    )
    assert a != b


# ---------------------------------------------------------------------------
# 8. No-authorization / no-eligibility / no-certification / no-later-model
# ---------------------------------------------------------------------------


def test_136af_no_forbidden_symbols_defined_in_source():
    tree = ast.parse(AUTHORIZATION_CANDIDATE_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_SYMBOLS:
        assert forbidden not in defined_names


def test_136af_no_repository_or_persistence_symbols_in_source():
    source = AUTHORIZATION_CANDIDATE_MODULE.read_text()
    for forbidden in ("Repository", "save(", "persist(", "def load(", "requests.", "urllib"):
        assert forbidden not in source


def test_136af_no_production_module_imports_authority_package():
    for root_dir in PRODUCTION_SCAN_ROOTS:
        if not root_dir.exists():
            continue
        for path in root_dir.rglob("*.py"):
            if AUTHORITY_PACKAGE_DIR in path.parents or path.parent == AUTHORITY_PACKAGE_DIR:
                continue
            source = path.read_text()
            assert "from pcae.cltr.authority" not in source, path
            assert "import pcae.cltr.authority" not in source, path


def test_136af_authorization_candidate_module_imports_no_production_lifecycle_module():
    source = AUTHORIZATION_CANDIDATE_MODULE.read_text()
    for forbidden_import in (
        "pcae.core.finalization",
        "pcae.core.notification",
        "pcae.commands",
        "pcae.runtime",
    ):
        assert forbidden_import not in source


def test_136af_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    wire = _valid_certification_wire()
    model = auth.Certification.from_dict(wire, schema_version="1.0")
    model.to_dict()


def test_136af_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    wire = _valid_human_authorization_wire()
    model = auth.HumanAuthorization.from_dict(wire, schema_version="1.0")
    model.to_dict()
    wire2 = _valid_cutover_candidate_wire()
    model2 = auth.CutoverCandidate.from_dict(wire2, schema_version="1.0")
    model2.to_dict()
