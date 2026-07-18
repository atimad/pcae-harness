"""Phase 136AH: Stage 3 Typed Authority Model Publication Implementation
(Typed Model Implementation Group 5).

Focused tests for ``src/pcae/cltr/authority/publication.py``: the
``PublicationAttempt`` and ``PublicationEvidence`` typed record models.
Covers exact field mapping, strict constructor behavior, family-
restriction enforcement, conditional branches, enum fidelity, schema
conformance, no-later-group-model inventory, no-publication/no-CAS-
execution/no-evidence-verification semantics, no-side-effect, and
runtime-isolation.

This module implements only Typed Model Implementation Group 5
(``PublicationAttempt``, ``PublicationEvidence``). No other record-family
model (``ConcurrencyConflict``, ``RecoveryJournalEntry``,
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
import sys
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import publication as pub
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
PUBLICATION_MODULE = AUTHORITY_PACKAGE_DIR / "publication.py"

PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "cltr",
    REPO_ROOT / "src" / "pcae" / "runtime",
)

FORBIDDEN_SYMBOLS = (
    "publish",
    "execute_publication",
    "promote",
    "write_manifest",
    "write_pointer",
    "activate_authority",
    "commit_publication",
    "finalize_publication",
    "compare_and_swap",
    "execute_cas",
    "check_current_generation",
    "retry_on_conflict",
    "lock",
    "atomic_replace",
    "verify_evidence",
    "validate_manifest",
    "check_artifact",
    "confirm_publication",
    "provider_success",
    "receipt_valid",
)

LATER_GROUP_MODEL_NAMES = (
    "ConcurrencyConflict",
    "RecoveryJournalEntry",
    "NotificationAuthorityBinding",
    "MarkerAuthorityBinding",
    "FinalizationReceiptAuthorityBinding",
    "CompatibilityState",
    "QuarantineRecord",
)

PUBLICATION_ATTEMPT_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/publication_attempt.schema.json"
)
PUBLICATION_EVIDENCE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/publication_evidence.schema.json"
)
CUTOVER_REQUEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json"
CUTOVER_CANDIDATE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/cutover_candidate.schema.json"
)
CERTIFICATION_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/certification.schema.json"


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


def _candidate_ref(record_id: str = "cutcand-00000001", digest: str = "d") -> dict:
    return _ref(record_id, digest, "cutover_candidate", with_schema=CUTOVER_CANDIDATE_SCHEMA_ID)


def _certification_ref(record_id: str = "certif-00000001", digest: str = "f") -> dict:
    return _ref(record_id, digest, "certification", with_schema=CERTIFICATION_SCHEMA_ID)


def _epoch_ref_bare(record_id: str = "authepoch-0000001", digest: str = "c") -> dict:
    return _ref(record_id, digest, "authority_epoch")


def _attempt_ref(record_id: str = "pubattem-0000001", digest: str = "0") -> dict:
    return _ref(record_id, digest, "publication_attempt", with_schema=PUBLICATION_ATTEMPT_SCHEMA_ID)


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


def _valid_publication_attempt_wire(**overrides) -> dict:
    record = {
        "schema_id": PUBLICATION_ATTEMPT_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "publication_attempt",
        "record_id": "pubattem-0000001",
        "record_digest": _sha256_hex("0"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "transition_id": "trans-0000001",
        "attempt_id": "pubattem-0000001",
        "request_reference": _request_ref(),
        "candidate_reference": _candidate_ref(),
        "certification_reference": _certification_ref(),
        "cas_expectation": _cas_expectation_wire(),
        "source_authority_reference": _epoch_ref_bare("authepoch-0000004", "6"),
        "target_authority_reference": _epoch_ref_bare("authepoch-0000005", "7"),
        "attempt_sequence": 0,
        "state": "publication_attempted",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _valid_publication_evidence_wire(**overrides) -> dict:
    record = {
        "schema_id": PUBLICATION_EVIDENCE_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "publication_evidence",
        "record_id": "pubevid-0000001",
        "record_digest": _sha256_hex("1"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "transition_id": "trans-0000001",
        "attempt_reference": _attempt_ref(),
        "outcome": "not_attempted",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# 1. Inventory
# ---------------------------------------------------------------------------


def test_136ah_exactly_nine_record_family_models_exist_in_package():
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
    ):
        assert expected in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136ah_no_later_group_model_class_exists_in_publication_module():
    tree = ast.parse(PUBLICATION_MODULE.read_text())
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert class_names & {"PublicationAttempt", "PublicationEvidence"} == {
        "PublicationAttempt",
        "PublicationEvidence",
    }
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136ah_expected_public_exports_present():
    for name in (
        "PublicationAttempt",
        "PublicationEvidence",
        "PublicationOutcome",
        "PublicationAttemptUncertainty",
        "PublicationEvidenceUncertaintyDetail",
    ):
        assert hasattr(auth, name)
        assert name in auth.__all__


def test_136ah_public_exports_exact():
    assert set(pub.__all__) == {
        "PublicationOutcome",
        "PublicationAttemptUncertainty",
        "PublicationEvidenceUncertaintyDetail",
        "PublicationAttempt",
        "PublicationEvidence",
    }


def test_136ah_wildcard_import_matches_all():
    namespace: dict = {}
    exec("from pcae.cltr.authority.publication import *", namespace)
    exported = {k for k in namespace if not k.startswith("_")}
    assert exported == set(pub.__all__)


def test_136ah_models_are_frozen_dataclasses():
    for model in (auth.PublicationAttempt, auth.PublicationEvidence):
        assert dataclasses.is_dataclass(model)
        assert model.__dataclass_params__.frozen


# ---------------------------------------------------------------------------
# 2. PublicationAttempt: construction / round trip
# ---------------------------------------------------------------------------


def test_136ah_publication_attempt_minimal_valid_construction(schema_registry):
    wire = _valid_publication_attempt_wire()
    _assert_schema_valid(wire, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
    model = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    assert model.temporary_pointer_reference is auth.ABSENT
    assert model.uncertainty is auth.ABSENT
    assert model.failure_classification is auth.ABSENT
    assert model.to_dict() == wire


def test_136ah_publication_attempt_maximal_valid_construction_uncertain(schema_registry):
    wire = _valid_publication_attempt_wire(
        state="publication_uncertain",
        uncertainty={"reason": "provider response timed out"},
        temporary_pointer_reference=_ref("temppoin-0000001", "9", "authority_state"),
    )
    _assert_schema_valid(wire, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
    model = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    assert model.uncertainty.reason == "provider response timed out"
    assert model.temporary_pointer_reference.record_id.value == "temppoin-0000001"
    assert model.to_dict() == wire


@pytest.mark.parametrize("state", ["gate_rejected", "conflict"])
def test_136ah_publication_attempt_failure_states_with_classification(schema_registry, state):
    wire = _valid_publication_attempt_wire(state=state, failure_classification="cas_rejected")
    _assert_schema_valid(wire, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
    model = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    assert model.failure_classification is auth.ReasonCode.CAS_REJECTED
    assert model.to_dict() == wire


def test_136ah_publication_attempt_uncertain_without_uncertainty_rejected():
    wire = _valid_publication_attempt_wire(state="publication_uncertain")
    with pytest.raises(Exception):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_non_uncertain_with_uncertainty_rejected():
    wire = _valid_publication_attempt_wire(uncertainty={"reason": "x"})
    with pytest.raises(Exception):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("state", ["gate_rejected", "conflict"])
def test_136ah_publication_attempt_failure_state_without_classification_rejected(state):
    wire = _valid_publication_attempt_wire(state=state)
    with pytest.raises(Exception):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_non_failure_state_with_classification_rejected():
    wire = _valid_publication_attempt_wire(failure_classification="cas_rejected")
    with pytest.raises(Exception):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_unknown_field_rejected():
    wire = _valid_publication_attempt_wire(scope="global")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_no_extensions_escape_hatch():
    wire = _valid_publication_attempt_wire(_extensions={})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_unsupported_schema_version_rejected():
    wire = _valid_publication_attempt_wire()
    with pytest.raises(auth.UnsupportedSchemaVersionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="2.0")


def test_136ah_publication_attempt_wrong_schema_id_rejected():
    wire = _valid_publication_attempt_wire(schema_id="https://pcae.local/wrong.json")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_wrong_record_type_rejected():
    wire = _valid_publication_attempt_wire(record_type="publication_evidence")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_missing_required_field_rejected():
    wire = _valid_publication_attempt_wire()
    del wire["attempt_sequence"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_forbids_authoritative_role():
    wire = _valid_publication_attempt_wire(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        }
    )
    with pytest.raises(Exception):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "field,family",
    [
        ("request_reference", "cutover_request"),
        ("candidate_reference", "cutover_candidate"),
        ("certification_reference", "certification"),
        ("source_authority_reference", "authority_epoch"),
        ("target_authority_reference", "authority_epoch"),
    ],
)
def test_136ah_publication_attempt_reference_wrong_family_rejected(field, family):
    wrong_family = "cutover_request" if family != "cutover_request" else "certification"
    schema_by_family = {
        "cutover_request": CUTOVER_REQUEST_SCHEMA_ID,
        "certification": CERTIFICATION_SCHEMA_ID,
    }
    wire = _valid_publication_attempt_wire(
        **{
            field: _ref(
                "wrongfam-000001", "1", wrong_family, with_schema=schema_by_family[wrong_family]
            )
        }
    )
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_request_reference_requires_schema_id_and_version():
    ref = _request_ref()
    del ref["schema_id"]
    wire = _valid_publication_attempt_wire(request_reference=ref)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_epoch_reference_does_not_require_schema_id(schema_registry):
    ref = _epoch_ref_bare("authepoch-0000004", "6")
    assert "schema_id" not in ref
    wire = _valid_publication_attempt_wire(source_authority_reference=ref)
    _assert_schema_valid(wire, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
    model = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    assert model.source_authority_reference.schema_id is auth.ABSENT


def test_136ah_publication_attempt_source_and_target_may_reference_same_epoch(schema_registry):
    same = _epoch_ref_bare("authepoch-0000009", "9")
    wire = _valid_publication_attempt_wire(
        source_authority_reference=same, target_authority_reference=same
    )
    _assert_schema_valid(wire, PUBLICATION_ATTEMPT_SCHEMA_ID, schema_registry)
    model = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    assert model.source_authority_reference == model.target_authority_reference


def test_136ah_publication_attempt_negative_sequence_rejected():
    wire = _valid_publication_attempt_wire(attempt_sequence=-1)
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_boolean_sequence_rejected():
    wire = _valid_publication_attempt_wire(attempt_sequence=True)
    with pytest.raises(auth.TypedModelInternalInvariantError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_state_enum_members_match_schema():
    assert {m.value for m in auth.PublicationState} == {
        "not_requested",
        "requested",
        "gate_rejected",
        "gate_uncertain",
        "certified",
        "publication_prepared",
        "publication_attempted",
        "publication_uncertain",
        "published",
        "verified",
        "conflict",
        "quarantined",
    }


def test_136ah_publication_attempt_state_enum_strictness():
    wire = _valid_publication_attempt_wire(state="PUBLISHED")
    with pytest.raises(ValueError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_top_level_assignment_raises():
    wire = _valid_publication_attempt_wire()
    model = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.attempt_sequence = 99


def test_136ah_publication_attempt_cas_expectation_returned_type_is_shared_class():
    wire = _valid_publication_attempt_wire()
    model = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    assert isinstance(model.cas_expectation, auth.CasExpectation)


def test_136ah_publication_attempt_cas_expectation_every_field_required():
    wire = _valid_publication_attempt_wire()
    cas = dict(wire["cas_expectation"])
    del cas["expected_authority_kind"]
    wire["cas_expectation"] = cas
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_uncertainty_reason_bounds_enforced():
    wire = _valid_publication_attempt_wire(
        state="publication_uncertain", uncertainty={"reason": ""}
    )
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


def test_136ah_publication_attempt_uncertainty_rejects_unknown_field():
    wire = _valid_publication_attempt_wire(
        state="publication_uncertain", uncertainty={"reason": "x", "extra": "y"}
    )
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationAttempt.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 3. PublicationEvidence: construction / round trip
# ---------------------------------------------------------------------------


def test_136ah_publication_evidence_minimal_valid_construction(schema_registry):
    wire = _valid_publication_evidence_wire()
    _assert_schema_valid(wire, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
    model = auth.PublicationEvidence.from_dict(wire, schema_version="1.0")
    assert model.uncertainty_detail is auth.ABSENT
    assert model.target_readback is auth.ABSENT
    assert model.authoritative_generation is auth.ABSENT
    assert model.to_dict() == wire


def test_136ah_publication_evidence_published_and_verified_maximal(schema_registry):
    wire = _valid_publication_evidence_wire(
        outcome="published_and_verified",
        target_readback=_ref("authstat-0000001", "9", "authority_state"),
        authoritative_generation=_generation_ref("generatn-0000009", "8"),
    )
    _assert_schema_valid(wire, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
    model = auth.PublicationEvidence.from_dict(wire, schema_version="1.0")
    assert model.target_readback.record_id.value == "authstat-0000001"
    assert model.authoritative_generation.generation_id.value == "generatn-0000009"
    assert model.to_dict() == wire


def test_136ah_publication_evidence_published_and_verified_permits_authoritative_role(
    schema_registry,
):
    wire = _valid_publication_evidence_wire(
        outcome="published_and_verified",
        target_readback=_ref("authstat-0000001", "9", "authority_state"),
        authoritative_generation=_generation_ref("generatn-0000009", "8"),
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        },
    )
    _assert_schema_valid(wire, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
    model = auth.PublicationEvidence.from_dict(wire, schema_version="1.0")
    assert model.authority_disclosure.authority_role is auth.AuthorityRole.AUTHORITATIVE
    assert model.authority_disclosure.is_authoritative is False


def test_136ah_publication_evidence_uncertain_with_detail(schema_registry):
    wire = _valid_publication_evidence_wire(
        outcome="publication_uncertain",
        uncertainty_detail={"last_known_state": "publication_attempted", "retry_recommended": True},
    )
    _assert_schema_valid(wire, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
    model = auth.PublicationEvidence.from_dict(wire, schema_version="1.0")
    assert model.uncertainty_detail.last_known_state is auth.PublicationState.PUBLICATION_ATTEMPTED
    assert model.uncertainty_detail.retry_recommended is True
    assert model.to_dict() == wire


def test_136ah_publication_evidence_uncertain_without_detail_rejected():
    wire = _valid_publication_evidence_wire(outcome="publication_uncertain")
    with pytest.raises(Exception):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_non_uncertain_with_detail_rejected():
    wire = _valid_publication_evidence_wire(
        uncertainty_detail={"last_known_state": "requested", "retry_recommended": False}
    )
    with pytest.raises(Exception):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_published_without_target_readback_rejected():
    wire = _valid_publication_evidence_wire(
        outcome="published_and_verified",
        authoritative_generation=_generation_ref("generatn-0000009", "8"),
    )
    with pytest.raises(Exception):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_published_without_authoritative_generation_rejected():
    wire = _valid_publication_evidence_wire(
        outcome="published_and_verified",
        target_readback=_ref("authstat-0000001", "9", "authority_state"),
    )
    with pytest.raises(Exception):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_non_published_with_target_readback_rejected():
    wire = _valid_publication_evidence_wire(
        target_readback=_ref("authstat-0000001", "9", "authority_state")
    )
    with pytest.raises(Exception):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_non_published_with_authoritative_generation_rejected():
    wire = _valid_publication_evidence_wire(
        authoritative_generation=_generation_ref("generatn-0000009", "8")
    )
    with pytest.raises(Exception):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_target_readback_no_family_restriction(schema_registry):
    wire = _valid_publication_evidence_wire(
        outcome="published_and_verified",
        target_readback=_ref("cutcand-00000001", "1", "cutover_candidate"),
        authoritative_generation=_generation_ref("generatn-0000009", "8"),
    )
    _assert_schema_valid(wire, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
    model = auth.PublicationEvidence.from_dict(wire, schema_version="1.0")
    assert model.target_readback.record_family is auth.RecordFamily.CUTOVER_CANDIDATE


def test_136ah_publication_evidence_unknown_field_rejected():
    wire = _valid_publication_evidence_wire(scope="global")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_no_extensions_escape_hatch():
    wire = _valid_publication_evidence_wire(_extensions={})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_missing_required_field_rejected():
    wire = _valid_publication_evidence_wire()
    del wire["outcome"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_attempt_reference_wrong_family_rejected():
    wire = _valid_publication_evidence_wire(
        attempt_reference=_ref(
            "wrongfam-000001", "1", "cutover_request", with_schema=CUTOVER_REQUEST_SCHEMA_ID
        )
    )
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_attempt_reference_requires_schema_id_and_version():
    ref = _attempt_ref()
    del ref["schema_id"]
    wire = _valid_publication_evidence_wire(attempt_reference=ref)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


def test_136ah_publication_evidence_outcome_enum_members_match_schema():
    assert {m.value for m in pub.PublicationOutcome} == {
        "not_attempted",
        "cas_rejected",
        "failed_before_replacement",
        "publication_uncertain",
        "published_and_verified",
        "post_publication_verification_failed",
        "conflict",
        "quarantined",
    }


def test_136ah_publication_evidence_outcome_enum_strictness():
    wire = _valid_publication_evidence_wire(outcome="NOT_ATTEMPTED")
    with pytest.raises(ValueError):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize(
    "outcome",
    [
        "not_attempted",
        "cas_rejected",
        "failed_before_replacement",
        "post_publication_verification_failed",
        "conflict",
        "quarantined",
    ],
)
def test_136ah_publication_evidence_all_bare_outcomes_construct(schema_registry, outcome):
    wire = _valid_publication_evidence_wire(outcome=outcome)
    _assert_schema_valid(wire, PUBLICATION_EVIDENCE_SCHEMA_ID, schema_registry)
    model = auth.PublicationEvidence.from_dict(wire, schema_version="1.0")
    assert model.outcome.value == outcome


def test_136ah_publication_evidence_top_level_assignment_raises():
    wire = _valid_publication_evidence_wire()
    model = auth.PublicationEvidence.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.outcome = pub.PublicationOutcome.CONFLICT


def test_136ah_publication_evidence_retry_recommended_must_be_boolean():
    wire = _valid_publication_evidence_wire(
        outcome="publication_uncertain",
        uncertainty_detail={"last_known_state": "requested", "retry_recommended": "yes"},
    )
    with pytest.raises(auth.TypedModelConstructionError):
        auth.PublicationEvidence.from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 4. Schema field-set parity
# ---------------------------------------------------------------------------


def test_136ah_publication_attempt_schema_field_set_matches_model_known_keys():
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "publication_attempt.schema.json").read_text())
    assert set(schema["properties"].keys()) == pub._PUBLICATION_ATTEMPT_KNOWN_KEYS


def test_136ah_publication_evidence_schema_field_set_matches_model_known_keys():
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "publication_evidence.schema.json").read_text())
    assert set(schema["properties"].keys()) == pub._PUBLICATION_EVIDENCE_KNOWN_KEYS


def test_136ah_publication_attempt_required_set_matches_schema():
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "publication_attempt.schema.json").read_text())
    wire = _valid_publication_attempt_wire()
    assert set(schema["required"]) <= set(wire.keys())


def test_136ah_publication_evidence_required_set_matches_schema():
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "publication_evidence.schema.json").read_text())
    wire = _valid_publication_evidence_wire()
    assert set(schema["required"]) <= set(wire.keys())


# ---------------------------------------------------------------------------
# 5. Equality / immutability
# ---------------------------------------------------------------------------


def test_136ah_publication_attempt_structural_equality():
    wire = _valid_publication_attempt_wire()
    a = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    b = auth.PublicationAttempt.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert a == b


def test_136ah_publication_attempt_field_difference_breaks_equality():
    a = auth.PublicationAttempt.from_dict(_valid_publication_attempt_wire(), schema_version="1.0")
    b = auth.PublicationAttempt.from_dict(
        _valid_publication_attempt_wire(attempt_sequence=1), schema_version="1.0"
    )
    assert a != b


def test_136ah_publication_evidence_structural_equality():
    wire = _valid_publication_evidence_wire()
    a = auth.PublicationEvidence.from_dict(wire, schema_version="1.0")
    b = auth.PublicationEvidence.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert a == b


def test_136ah_publication_attempt_and_evidence_same_id_not_equal_across_types():
    attempt = auth.PublicationAttempt.from_dict(
        _valid_publication_attempt_wire(), schema_version="1.0"
    )
    evidence = auth.PublicationEvidence.from_dict(
        _valid_publication_evidence_wire(), schema_version="1.0"
    )
    assert attempt != evidence


def test_136ah_publication_attempt_hashable():
    model = auth.PublicationAttempt.from_dict(_valid_publication_attempt_wire(), schema_version="1.0")
    hash(model)


# ---------------------------------------------------------------------------
# 6. No-publication / no-CAS-execution / no-evidence-verification / no-later-model
# ---------------------------------------------------------------------------


def test_136ah_no_forbidden_symbols_defined_in_source():
    tree = ast.parse(PUBLICATION_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_SYMBOLS:
        assert forbidden not in defined_names


def test_136ah_no_repository_or_persistence_symbols_in_source():
    source = PUBLICATION_MODULE.read_text()
    for forbidden in ("Repository", "save(", "persist(", "def load(", "requests.", "urllib"):
        assert forbidden not in source


def test_136ah_no_production_module_imports_authority_package():
    for root_dir in PRODUCTION_SCAN_ROOTS:
        if not root_dir.exists():
            continue
        for path in root_dir.rglob("*.py"):
            if AUTHORITY_PACKAGE_DIR in path.parents or path.parent == AUTHORITY_PACKAGE_DIR:
                continue
            source = path.read_text()
            assert "from pcae.cltr.authority" not in source, path
            assert "import pcae.cltr.authority" not in source, path


def test_136ah_publication_module_imports_no_production_lifecycle_module():
    source = PUBLICATION_MODULE.read_text()
    for forbidden_import in (
        "pcae.core.finalization",
        "pcae.core.notification",
        "pcae.commands",
        "pcae.runtime",
    ):
        assert forbidden_import not in source


def test_136ah_publication_module_does_not_import_production_lifecycle_modules_ast():
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
    tree = ast.parse(PUBLICATION_MODULE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in forbidden_modules:
                    assert not alias.name.startswith(forbidden), (PUBLICATION_MODULE, alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in forbidden_modules:
                assert not node.module.startswith(forbidden), (PUBLICATION_MODULE, node.module)


def test_136ah_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    wire = _valid_publication_evidence_wire()
    model = auth.PublicationEvidence.from_dict(wire, schema_version="1.0")
    model.to_dict()


def test_136ah_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    wire = _valid_publication_attempt_wire()
    model = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    model.to_dict()
    wire2 = _valid_publication_evidence_wire()
    model2 = auth.PublicationEvidence.from_dict(wire2, schema_version="1.0")
    model2.to_dict()


def test_136ah_no_filesystem_write_during_construction_or_serialization(monkeypatch, tmp_path):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    wire = _valid_publication_attempt_wire()
    model = auth.PublicationAttempt.from_dict(wire, schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136ah_package_import_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(pub)


# ---------------------------------------------------------------------------
# 7. Scope-guard verification (narrowed by 136AH; must still forbid the
#    remaining seven later record families and permit only this group's
#    two new families).
# ---------------------------------------------------------------------------


SCOPE_GUARDED_TEST_FILES = (
    REPO_ROOT / "tests" / "test_cltr_authority_136z_shared_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136aa_shared_core_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ab_authority_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ac_authority_core_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ad_request_readiness.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ae_request_readiness_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136af_authorization_candidate.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ag_authorization_candidate_independent.py",
)


def test_136ah_adjacent_scope_guard_test_files_still_forbid_all_later_models():
    still_forbidden_after_136ah = (
        "ConcurrencyConflict",
        "RecoveryJournalEntry",
        "NotificationAuthorityBinding",
        "MarkerAuthorityBinding",
        "FinalizationReceiptAuthorityBinding",
        "CompatibilityState",
        "QuarantineRecord",
    )
    for path in SCOPE_GUARDED_TEST_FILES:
        if not path.exists():
            continue
        text = path.read_text()
        if "LATER_MODEL_CLASS_NAMES" not in text and "LATER_GROUP_MODEL_NAMES" not in text:
            continue
        for later in still_forbidden_after_136ah:
            assert later in text, f"{path} no longer names {later} as forbidden"


def test_136ah_own_module_scope_guard_matches_exactly_the_two_new_families():
    tree = ast.parse(PUBLICATION_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_models = class_names & {
        "PublicationAttempt", "PublicationEvidence", *LATER_GROUP_MODEL_NAMES,
        "AuthorityEpoch", "AuthorityState", "CutoverRequest", "ReadinessPackage",
        "HumanAuthorization", "CutoverCandidate", "Certification",
    }
    assert record_family_models == {"PublicationAttempt", "PublicationEvidence"}


# ---------------------------------------------------------------------------
# 8. Packaging verification
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136ah_wheel_contains_publication_module_no_later_family(tmp_path: Path):
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

    assert "pcae/cltr/authority/publication.py" in names
    for forbidden in ("recovery", "bindings", "compatibility_quarantine"):
        assert f"pcae/cltr/authority/{forbidden}.py" not in names


@pytest.mark.slow
def test_136ah_sdist_includes_publication_module(tmp_path: Path):
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

    assert any(name.endswith("pcae/cltr/authority/publication.py") for name in names)
