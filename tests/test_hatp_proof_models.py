"""Phase 149O.1G, Wave 3 -- HATP proof model + strict closed-schema unit
tests for `pcae.core.human_approval_trusted_provenance`.

Structural conformance only (module docstring's mandatory boundary):
these tests never assert anything about signature validity, human
presence, attestation, or trust -- there is no such vocabulary in this
module to test.
"""
from __future__ import annotations

import json
import uuid

import pytest

from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HumanApprovalProvenanceProof,
    InvalidProofSchemaError,
    MalformedProofError,
    RollbackSite,
    UnsupportedProofVersionError,
    parse_hatp_proof,
)


def _repo_id() -> str:
    return str(uuid.uuid4())


def _ag3_doc(**overrides) -> dict:
    doc = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": _repo_id(),
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": "AG3",
        "job_id": "job-1",
        "original_commit_sha": "c" * 40,
        "issued_at": "2026-08-06T00:00:00.000Z",
    }
    doc.update(overrides)
    return doc


def _ag5_doc(**overrides) -> dict:
    doc = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": _repo_id(),
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": "AG5",
        "per_id": "per-1",
        "ecp_id": "ecp-1",
        "issued_at": "2026-08-06T00:00:00.000Z",
    }
    doc.update(overrides)
    return doc


def _dump(doc: dict) -> str:
    return json.dumps(doc)


# ── Valid construction ────────────────────────────────────────────────────


def test_ag3_valid_proof_parses() -> None:
    proof = parse_hatp_proof(_dump(_ag3_doc()))
    assert proof.rollback_site is RollbackSite.AG3
    assert isinstance(proof.operation_reference, Ag3OperationReference)
    assert proof.operation_reference.job_id == "job-1"


def test_ag5_valid_proof_parses() -> None:
    proof = parse_hatp_proof(_dump(_ag5_doc()))
    assert proof.rollback_site is RollbackSite.AG5
    assert isinstance(proof.operation_reference, Ag5OperationReference)
    assert proof.operation_reference.ecp_id == "ecp-1"


# ── Missing required fields (each individually) ──────────────────────────


@pytest.mark.parametrize(
    "field",
    [
        "principal_id",
        "signer_key_id",
        "provider_profile",
        "repository_id",
        "decision_record_id",
        "decision_record_digest",
        "binding_id",
        "binding_digest",
        "rollback_site",
        "issued_at",
        "job_id",
        "original_commit_sha",
    ],
)
def test_ag3_missing_required_field_rejected(field: str) -> None:
    doc = _ag3_doc()
    del doc[field]
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


@pytest.mark.parametrize("field", ["per_id", "ecp_id"])
def test_ag5_missing_required_field_rejected(field: str) -> None:
    doc = _ag5_doc()
    del doc[field]
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


# ── Empty / malformed identifiers ─────────────────────────────────────────


def test_empty_principal_id_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(_ag3_doc(principal_id="")))


def test_bad_repository_id_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(_ag3_doc(repository_id="not-a-uuid")))


def test_bad_decision_record_digest_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(_ag3_doc(decision_record_digest="not-hex")))


def test_bad_binding_digest_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(_ag3_doc(binding_digest="short")))


def test_bad_commit_sha_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(_ag3_doc(original_commit_sha="not-a-sha")))


def test_commit_sha_sha256_length_accepted() -> None:
    proof = parse_hatp_proof(_dump(_ag3_doc(original_commit_sha="d" * 64)))
    assert proof.operation_reference.original_commit_sha == "d" * 64


def test_bad_timestamp_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(_ag3_doc(issued_at="not-a-timestamp")))


def test_naive_timestamp_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(_ag3_doc(issued_at="2026-08-06T00:00:00.000")))


# ── proof_version ─────────────────────────────────────────────────────────


def test_unsupported_proof_version_rejected() -> None:
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(_dump(_ag3_doc(proof_version=2)))


def test_missing_proof_version_rejected() -> None:
    doc = _ag3_doc()
    del doc["proof_version"]
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(_dump(doc))


def test_non_integer_proof_version_rejected() -> None:
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(_dump(_ag3_doc(proof_version="1")))


def test_boolean_proof_version_rejected() -> None:
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(_dump(_ag3_doc(proof_version=True)))


# ── Operation-family discriminant correctness ─────────────────────────────


def test_unknown_rollback_site_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(_ag3_doc(rollback_site="AG7")))


def test_missing_rollback_site_rejected() -> None:
    doc = _ag3_doc()
    del doc["rollback_site"]
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


def test_ag3_discriminator_with_ag5_fields_rejected() -> None:
    doc = _ag3_doc()
    doc["per_id"] = "per-1"
    doc["ecp_id"] = "ecp-1"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


def test_ag5_discriminator_with_ag3_fields_rejected() -> None:
    doc = _ag5_doc()
    doc["job_id"] = "job-1"
    doc["original_commit_sha"] = "c" * 40
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


def test_ag3_discriminator_with_ag5_payload_only_rejected() -> None:
    """AG3 discriminator + AG5 fields, AG3 fields entirely absent --
    still rejected (missing AG3 fields), never silently reinterpreted as
    AG5."""

    doc = _ag3_doc()
    del doc["job_id"]
    del doc["original_commit_sha"]
    doc["per_id"] = "per-1"
    doc["ecp_id"] = "ecp-1"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


def test_mixed_family_fields_rejected() -> None:
    doc = _ag3_doc()
    doc["per_id"] = "per-1"
    doc["ecp_id"] = "ecp-1"
    doc["rollback_site"] = "AG3"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


def test_missing_operation_family_and_fields_rejected() -> None:
    doc = _ag3_doc()
    for key in ("rollback_site", "job_id", "original_commit_sha"):
        del doc[key]
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


# ── Direct dataclass construction defense-in-depth ────────────────────────


def test_direct_construction_family_mismatch_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(
            proof_version=1,
            principal_id="alice",
            signer_key_id="signer-1",
            provider_profile="HATP_HARDWARE_PROVIDER_V1",
            repository_id=_repo_id(),
            decision_record_id="chgr-record-1",
            decision_record_digest="a" * 64,
            binding_id="rae-binding-1",
            binding_digest="b" * 64,
            rollback_site=RollbackSite.AG3,
            operation_reference=Ag5OperationReference(per_id="per-1", ecp_id="ecp-1"),
            issued_at="2026-08-06T00:00:00.000Z",
        )


# ── F-149O.1C-1: unknown top-level field rejection ────────────────────────


def test_unknown_top_level_field_rejected() -> None:
    """This is the primary F-149O.1C-1 implementation proof (governing
    prompt item 101): an otherwise-valid proof carrying one extra,
    unrecognized field SHALL be rejected outright, never ignored."""

    doc = _ag3_doc()
    doc["trusted_root"] = "attacker-supplied"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


@pytest.mark.parametrize(
    "field",
    [
        "approved",
        "trusted",
        "authorized",
        "human_present",
        "valid",
        "trusted_public_key",
        "attestation_root",
        "authority_registry",
        "canonical_root",
        "trust_store_root",
    ],
)
def test_self_selected_authority_fields_rejected(field: str) -> None:
    """Self-selected trust/authority fields (governing prompt items
    28/83-86) are unknown to this schema and therefore rejected exactly
    like any other unrecognized field -- there is no special-case
    allowance for them."""

    doc = _ag3_doc()
    doc[field] = True
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


def test_no_raw_deployment_path_field_in_schema() -> None:
    """HATP-REQ-070: the proof payload SHALL NOT include the raw
    canonical local deployment path."""

    doc = _ag3_doc()
    doc["deployment_root"] = "/some/path"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(_dump(doc))


# ── Duplicate JSON key rejection ──────────────────────────────────────────


def test_duplicate_top_level_key_rejected() -> None:
    raw = '{"principal_id": "alice", "principal_id": "mallory"}'
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(raw)


def test_duplicate_key_full_document_rejected() -> None:
    base = _ag3_doc()
    raw = _dump(base)
    # Inject a duplicate of an existing key just before the closing brace.
    tampered = raw[:-1] + ', "principal_id": "mallory"}'
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(tampered)


# ── Non-object / malformed JSON ────────────────────────────────────────────


def test_top_level_array_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof("[1, 2, 3]")


def test_invalid_json_rejected() -> None:
    with pytest.raises(MalformedProofError):
        parse_hatp_proof("{not valid json")


def test_bytes_input_accepted() -> None:
    proof = parse_hatp_proof(_dump(_ag3_doc()).encode("utf-8"))
    assert proof.rollback_site is RollbackSite.AG3


# ── Whitespace preservation (no silent trimming) ──────────────────────────


def test_identifier_whitespace_not_silently_trimmed() -> None:
    proof = parse_hatp_proof(_dump(_ag3_doc(principal_id=" alice ")))
    assert proof.principal_id == " alice "


def test_identifier_case_not_silently_changed() -> None:
    proof = parse_hatp_proof(_dump(_ag3_doc(principal_id="Alice")))
    assert proof.principal_id == "Alice"
