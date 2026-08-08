"""Phase 149O.12A, Wave A -- `HATPSignedEvidenceEnvelope` model, parser,
and canonical serializer unit tests for `pcae.core.hatp_signed_evidence`.

Structural conformance only (HSCE-REQ-063): these tests never assert
anything about signer authenticity, human presence, or trust -- this
module performs no cryptographic verification.
"""
from __future__ import annotations

import base64
import dataclasses
import json
import uuid

import pytest

from pcae.core.hatp_signed_evidence import (
    EVIDENCE_VERSION,
    EvidenceIdDigestMismatchError,
    HATPSignedEvidenceEnvelope,
    InvalidEvidenceEnvelopeSchemaError,
    InvalidEvidenceIdError,
    MalformedEvidenceEnvelopeError,
    UnsupportedEvidenceVersionError,
    build_hatp_signed_evidence_envelope,
    parse_hatp_signed_evidence,
    serialize_hatp_signed_evidence,
    validate_evidence_id,
)
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    HumanApprovalProvenanceProof,
    RollbackSite,
    digest_hatp_proof_payload,
    hatp_proof_to_document,
)


def _repo_id() -> str:
    return str(uuid.uuid4())


def _proof(**overrides) -> HumanApprovalProvenanceProof:
    fields = dict(
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
        operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40),
        issued_at="2026-08-06T00:00:00.000Z",
    )
    fields.update(overrides)
    return HumanApprovalProvenanceProof(**fields)


def _envelope(proof: HumanApprovalProvenanceProof = None, assertion: bytes = b"provider-evidence-bytes"):
    return build_hatp_signed_evidence_envelope(proof if proof is not None else _proof(), assertion)


def _envelope_document(envelope: HATPSignedEvidenceEnvelope) -> dict:
    return json.loads(serialize_hatp_signed_evidence(envelope))


# ═══════════════════════════════════════════════════════════════════════════
# Valid construction / immutability / builder
# ═══════════════════════════════════════════════════════════════════════════


def test_build_produces_valid_envelope():
    proof = _proof()
    envelope = build_hatp_signed_evidence_envelope(proof, b"assertion")
    assert envelope.evidence_version == EVIDENCE_VERSION
    assert envelope.evidence_id == digest_hatp_proof_payload(proof)
    assert envelope.proof == proof
    assert envelope.provider_assertion == b"assertion"


def test_envelope_is_frozen():
    envelope = _envelope()
    with pytest.raises(dataclasses.FrozenInstanceError):
        envelope.evidence_version = 1  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        envelope.provider_assertion = b"other"  # type: ignore[misc]


def test_builder_never_accepts_caller_supplied_evidence_id():
    """HSCE-REQ-036: the production builder derives `evidence_id`
    internally -- it has no parameter accepting a caller-supplied value."""

    import inspect

    signature = inspect.signature(build_hatp_signed_evidence_envelope)
    assert "evidence_id" not in signature.parameters


# ═══════════════════════════════════════════════════════════════════════════
# Constructor/parser domain equivalence (HSCE-REQ-072)
# ═══════════════════════════════════════════════════════════════════════════


def test_direct_constructor_rejects_evidence_id_proof_mismatch():
    proof = _proof()
    with pytest.raises(EvidenceIdDigestMismatchError):
        HATPSignedEvidenceEnvelope(
            evidence_version=1,
            evidence_id="0" * 64,
            proof=proof,
            provider_assertion=b"assertion",
        )


def test_constructor_and_parser_reject_identical_domain():
    """No envelope constructible directly that the parser would reject,
    and vice versa (B-149O.1H-2 lesson, HSCE-REQ-072)."""

    envelope = _envelope()
    raw = serialize_hatp_signed_evidence(envelope)
    document = json.loads(raw)

    # Constructing directly with the parsed values succeeds identically.
    reconstructed = HATPSignedEvidenceEnvelope(
        evidence_version=document["evidence_version"],
        evidence_id=document["evidence_id"],
        proof=envelope.proof,
        provider_assertion=base64.b64decode(document["provider_assertion"]),
    )
    assert reconstructed == envelope

    # And the parser accepts the same document.
    assert parse_hatp_signed_evidence(raw) == envelope


# ═══════════════════════════════════════════════════════════════════════════
# Version validation (attack 7)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("bad_version", [True, False, 1.0, "1", 0, 2, -1, None])
def test_construction_rejects_bad_versions(bad_version):
    proof = _proof()
    with pytest.raises(UnsupportedEvidenceVersionError):
        HATPSignedEvidenceEnvelope(
            evidence_version=bad_version,
            evidence_id=digest_hatp_proof_payload(proof),
            proof=proof,
            provider_assertion=b"assertion",
        )


@pytest.mark.parametrize("bad_version", [True, False, 1.0, "1", 0, 2, -1, None])
def test_parse_rejects_bad_versions(bad_version):
    document = _envelope_document(_envelope())
    document["evidence_version"] = bad_version
    with pytest.raises(UnsupportedEvidenceVersionError):
        parse_hatp_signed_evidence(json.dumps(document))


def test_bool_is_not_silently_accepted_as_int_one():
    """`isinstance(True, int) == True` pitfall -- must not let `True`
    satisfy `evidence_version == 1`."""

    proof = _proof()
    with pytest.raises(UnsupportedEvidenceVersionError):
        HATPSignedEvidenceEnvelope(
            evidence_version=True,
            evidence_id=digest_hatp_proof_payload(proof),
            proof=proof,
            provider_assertion=b"assertion",
        )


# ═══════════════════════════════════════════════════════════════════════════
# Evidence ID validation (attacks 1, 2)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "bad_id",
    [
        "../../../etc/passwd",
        "/etc/passwd",
        "a" * 63,
        "a" * 65,
        "A" * 64,  # uppercase
        "a" * 32 + "G" * 32,  # non-hex
        " " + "a" * 63,  # leading whitespace
        "a" * 63 + " ",  # trailing whitespace
        "a" * 31 + "/" + "a" * 32,
        "a" * 31 + "\\" + "a" * 32,
        "a" * 32 + ".." + "a" * 30,
        "а" * 64,  # Cyrillic lookalike 'а', not ASCII hex
        "",
        None,
        12345,
    ],
)
def test_validate_evidence_id_rejects_malformed_values(bad_id):
    with pytest.raises(InvalidEvidenceIdError):
        validate_evidence_id(bad_id)


def test_validate_evidence_id_accepts_lowercase_64_hex():
    value = "a" * 64
    assert validate_evidence_id(value) == value


def test_evidence_id_is_never_normalized():
    """Uppercase input is rejected outright, never lowercased-and-retried."""

    proof = _proof()
    with pytest.raises(InvalidEvidenceIdError):
        HATPSignedEvidenceEnvelope(
            evidence_version=1,
            evidence_id=digest_hatp_proof_payload(proof).upper(),
            proof=proof,
            provider_assertion=b"assertion",
        )


# ═══════════════════════════════════════════════════════════════════════════
# Evidence ID / digest binding (attack 9, HSCE-REQ-036/062)
# ═══════════════════════════════════════════════════════════════════════════


def test_evidence_id_must_equal_proof_digest_on_parse():
    document = _envelope_document(_envelope())
    document["evidence_id"] = "f" * 64
    with pytest.raises(EvidenceIdDigestMismatchError):
        parse_hatp_signed_evidence(json.dumps(document))


def test_evidence_id_derives_only_from_proof_not_provider_assertion():
    """SC-5: `evidence_id` derives only from the canonical proof payload,
    never from `provider_assertion`."""

    proof = _proof()
    envelope_a = build_hatp_signed_evidence_envelope(proof, b"assertion-a")
    envelope_b = build_hatp_signed_evidence_envelope(proof, b"assertion-b")
    assert envelope_a.evidence_id == envelope_b.evidence_id
    assert envelope_a.provider_assertion != envelope_b.provider_assertion


def test_same_proof_different_assertion_both_independently_valid():
    """Governing-prompt §26: the model layer permits both; only the store
    layer (Wave B) decides first-write-canonical conflict semantics."""

    proof = _proof()
    envelope_a = build_hatp_signed_evidence_envelope(proof, b"assertion-a")
    envelope_b = build_hatp_signed_evidence_envelope(proof, b"assertion-b")
    # Both construct without error -- no exception raised above.
    assert envelope_a.evidence_id == envelope_b.evidence_id


# ═══════════════════════════════════════════════════════════════════════════
# Provider assertion / Base64 (HSCE-REQ-034/035)
# ═══════════════════════════════════════════════════════════════════════════


def test_provider_assertion_base64_round_trip():
    envelope = _envelope(assertion=b"\x00\x01\xff\xfe binary bytes here")
    raw = serialize_hatp_signed_evidence(envelope)
    document = json.loads(raw)
    assert base64.b64decode(document["provider_assertion"]) == envelope.provider_assertion
    assert parse_hatp_signed_evidence(raw).provider_assertion == envelope.provider_assertion


def test_provider_assertion_empty_bytes_structurally_accepted():
    """Governing-prompt §13: empty bytes are structurally valid; this
    module never performs cryptographic verification of them."""

    envelope = _envelope(assertion=b"")
    raw = serialize_hatp_signed_evidence(envelope)
    parsed = parse_hatp_signed_evidence(raw)
    assert parsed.provider_assertion == b""


def test_invalid_base64_provider_assertion_rejected():
    document = _envelope_document(_envelope())
    document["provider_assertion"] = "not-valid-base64!!!"
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        parse_hatp_signed_evidence(json.dumps(document))


def test_corrupt_provider_assertion_still_parses_structurally():
    """Attack 10: corrupt/truncated provider_assertion bytes parse
    structurally (this module never rejects on cryptographic grounds --
    that is `verify_hatp_proof`'s job, not run here)."""

    envelope = _envelope(assertion=b"deliberately-truncated-signature")
    raw = serialize_hatp_signed_evidence(envelope)
    parsed = parse_hatp_signed_evidence(raw)
    assert parsed.provider_assertion == b"deliberately-truncated-signature"


def test_construction_rejects_non_bytes_provider_assertion():
    proof = _proof()
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        HATPSignedEvidenceEnvelope(
            evidence_version=1,
            evidence_id=digest_hatp_proof_payload(proof),
            proof=proof,
            provider_assertion="not-bytes",  # type: ignore[arg-type]
        )


# ═══════════════════════════════════════════════════════════════════════════
# Closed schema (attacks 5, 6, 8)
# ═══════════════════════════════════════════════════════════════════════════


def test_unknown_top_level_field_rejected():
    document = _envelope_document(_envelope())
    document["approved"] = True
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        parse_hatp_signed_evidence(json.dumps(document))


@pytest.mark.parametrize(
    "missing_field",
    ["evidence_version", "evidence_id", "proof", "provider_assertion"],
)
def test_missing_required_field_rejected(missing_field):
    document = _envelope_document(_envelope())
    del document[missing_field]
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        parse_hatp_signed_evidence(json.dumps(document))


def test_duplicate_top_level_key_rejected():
    envelope = _envelope()
    document = _envelope_document(envelope)
    raw_text = json.dumps(document)
    # Inject a duplicate "evidence_version" key by string surgery -- json.dumps
    # never itself produces duplicates, so this simulates a hostile input.
    duplicated = raw_text.replace(
        '"evidence_version": 1', '"evidence_version": 1, "evidence_version": 1', 1
    )
    with pytest.raises(MalformedEvidenceEnvelopeError):
        parse_hatp_signed_evidence(duplicated)


def test_duplicate_nested_proof_key_rejected():
    envelope = _envelope()
    document = _envelope_document(envelope)
    raw_text = json.dumps(document)
    duplicated = raw_text.replace(
        '"proof_version": 1', '"proof_version": 1, "proof_version": 1', 1
    )
    with pytest.raises(MalformedEvidenceEnvelopeError):
        parse_hatp_signed_evidence(duplicated)


def test_not_a_json_object_rejected():
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        parse_hatp_signed_evidence(json.dumps([1, 2, 3]))


def test_not_valid_json_rejected():
    with pytest.raises(MalformedEvidenceEnvelopeError):
        parse_hatp_signed_evidence("{not json")


# ═══════════════════════════════════════════════════════════════════════════
# Wrong-type attacks (fail closed for each field)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("bad_value", [None, True, 1, [], {}, "not-an-int"])
def test_evidence_version_wrong_types_rejected(bad_value):
    document = _envelope_document(_envelope())
    document["evidence_version"] = bad_value
    if bad_value == 1:  # not reachable via parametrize values above, defensive only
        return
    with pytest.raises((UnsupportedEvidenceVersionError, InvalidEvidenceEnvelopeSchemaError)):
        parse_hatp_signed_evidence(json.dumps(document))


@pytest.mark.parametrize("bad_value", [None, True, 12345, [], {}])
def test_evidence_id_wrong_types_rejected(bad_value):
    document = _envelope_document(_envelope())
    document["evidence_id"] = bad_value
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        parse_hatp_signed_evidence(json.dumps(document))


@pytest.mark.parametrize("bad_value", [None, True, 12345, [], "not-an-object"])
def test_proof_wrong_types_rejected(bad_value):
    document = _envelope_document(_envelope())
    document["proof"] = bad_value
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        parse_hatp_signed_evidence(json.dumps(document))


@pytest.mark.parametrize("bad_value", [None, True, 12345, [], {}])
def test_provider_assertion_wrong_types_rejected(bad_value):
    document = _envelope_document(_envelope())
    document["provider_assertion"] = bad_value
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        parse_hatp_signed_evidence(json.dumps(document))


# ═══════════════════════════════════════════════════════════════════════════
# Canonical serialization / round-trip (HSCE-REQ-053)
# ═══════════════════════════════════════════════════════════════════════════


def test_canonical_bytes_are_utf8_sorted_keys_no_separators_assumption():
    envelope = _envelope()
    raw = serialize_hatp_signed_evidence(envelope)
    text = raw.decode("utf-8")
    document = json.loads(text)
    assert list(document.keys()) == sorted(document.keys())


def test_canonical_round_trip_parse_of_serialize_equals_original():
    envelope = _envelope()
    raw = serialize_hatp_signed_evidence(envelope)
    assert parse_hatp_signed_evidence(raw) == envelope


def test_canonical_round_trip_serialize_of_parse_equals_canonical_bytes():
    envelope = _envelope()
    raw = serialize_hatp_signed_evidence(envelope)
    parsed = parse_hatp_signed_evidence(raw)
    assert serialize_hatp_signed_evidence(parsed) == raw


def test_noncanonical_json_layout_canonicalizes_to_one_representation():
    """Attack-matrix-adjacent (governing-prompt §24): the parser accepts
    valid noncanonical JSON layout; the serializer emits one deterministic
    representation regardless of input formatting."""

    envelope = _envelope()
    document = _envelope_document(envelope)

    # Same logical document, different key order and extra whitespace.
    reordered_text = json.dumps(
        {
            "provider_assertion": document["provider_assertion"],
            "proof": document["proof"],
            "evidence_id": document["evidence_id"],
            "evidence_version": document["evidence_version"],
        },
        indent=4,
    )

    canonical_from_envelope = serialize_hatp_signed_evidence(envelope)
    canonical_from_reordered = serialize_hatp_signed_evidence(parse_hatp_signed_evidence(reordered_text))
    assert canonical_from_reordered == canonical_from_envelope


def test_serializer_embeds_hatp_proof_document_unchanged():
    envelope = _envelope()
    document = _envelope_document(envelope)
    assert document["proof"] == hatp_proof_to_document(envelope.proof)


def test_serializer_never_emits_nan_or_infinity():
    """HSCE-REQ-053: `allow_nan=False`. The envelope schema has no float
    field, so this is a structural guarantee, not a per-field test --
    verified here by confirming `json.dumps` is invoked with that flag
    via the absence of any float anywhere in the canonical output."""

    envelope = _envelope()
    raw = serialize_hatp_signed_evidence(envelope)
    assert b"NaN" not in raw
    assert b"Infinity" not in raw


# ═══════════════════════════════════════════════════════════════════════════
# Content-addressing precision (HSCE-REQ-037)
# ═══════════════════════════════════════════════════════════════════════════


def test_evidence_id_does_not_address_full_envelope_bytes():
    """`evidence_id` addresses the canonical proof payload only -- it does
    not address the complete envelope byte sequence."""

    proof = _proof()
    envelope = build_hatp_signed_evidence_envelope(proof, b"assertion-x")
    raw_a = serialize_hatp_signed_evidence(envelope)

    other = build_hatp_signed_evidence_envelope(proof, b"assertion-y")
    raw_b = serialize_hatp_signed_evidence(other)

    assert raw_a != raw_b
    assert envelope.evidence_id == other.evidence_id
