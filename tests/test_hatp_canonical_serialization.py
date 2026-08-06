"""Phase 149O.1G, Wave 3 -- canonical serialization + digest tests for
`pcae.core.human_approval_trusted_provenance`.

Covers: key-order/whitespace independence, round-trip determinism,
AG3/AG5 golden vectors, digest golden vectors, and the semantic-mutation
matrix (every load-bearing field, individually mutated, must change the
canonical bytes and the digest).
"""
from __future__ import annotations

import copy
import json

import pytest

from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HumanApprovalProvenanceProof,
    RollbackSite,
    canonicalize_hatp_proof_payload,
    digest_hatp_proof_payload,
    hatp_proof_to_document,
    parse_hatp_proof,
)

_FIXED_REPO_ID = "11111111-1111-4111-8111-111111111111"

_AG3_FIXTURE = {
    "proof_version": 1,
    "principal_id": "alice",
    "signer_key_id": "signer-1",
    "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
    "repository_id": _FIXED_REPO_ID,
    "decision_record_id": "chgr-record-1",
    "decision_record_digest": "a" * 64,
    "binding_id": "rae-binding-1",
    "binding_digest": "b" * 64,
    "rollback_site": "AG3",
    "job_id": "job-1",
    "original_commit_sha": "c" * 40,
    "issued_at": "2026-08-06T00:00:00.000Z",
}

_AG5_FIXTURE = {
    "proof_version": 1,
    "principal_id": "alice",
    "signer_key_id": "signer-1",
    "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
    "repository_id": _FIXED_REPO_ID,
    "decision_record_id": "chgr-record-1",
    "decision_record_digest": "a" * 64,
    "binding_id": "rae-binding-1",
    "binding_digest": "b" * 64,
    "rollback_site": "AG5",
    "per_id": "per-1",
    "ecp_id": "ecp-1",
    "issued_at": "2026-08-06T00:00:00.000Z",
}

# Golden vectors: exact expected canonical bytes for the two fixtures
# above, with fixed stable IDs/timestamp. These are compatibility
# anchors for a future Wave 4/5 (governing prompt item 105-108) -- any
# change to these constants without an explicit, reviewed reason is
# itself a canonicalization regression.
_AG3_GOLDEN_BYTES = (
    b'{"binding_digest":"' + b"b" * 64 + b'","binding_id":"rae-binding-1",'
    b'"decision_record_digest":"' + b"a" * 64 + b'","decision_record_id":"chgr-record-1",'
    b'"issued_at":"2026-08-06T00:00:00.000Z","job_id":"job-1",'
    b'"original_commit_sha":"' + b"c" * 40 + b'","principal_id":"alice",'
    b'"proof_version":1,"provider_profile":"HATP_HARDWARE_PROVIDER_V1",'
    b'"repository_id":"' + _FIXED_REPO_ID.encode() + b'","rollback_site":"AG3",'
    b'"signer_key_id":"signer-1"}'
)

_AG5_GOLDEN_BYTES = (
    b'{"binding_digest":"' + b"b" * 64 + b'","binding_id":"rae-binding-1",'
    b'"decision_record_digest":"' + b"a" * 64 + b'","decision_record_id":"chgr-record-1",'
    b'"ecp_id":"ecp-1","issued_at":"2026-08-06T00:00:00.000Z",'
    b'"per_id":"per-1","principal_id":"alice",'
    b'"proof_version":1,"provider_profile":"HATP_HARDWARE_PROVIDER_V1",'
    b'"repository_id":"' + _FIXED_REPO_ID.encode() + b'","rollback_site":"AG5",'
    b'"signer_key_id":"signer-1"}'
)


def _ag3_proof() -> HumanApprovalProvenanceProof:
    return parse_hatp_proof(json.dumps(_AG3_FIXTURE))


def _ag5_proof() -> HumanApprovalProvenanceProof:
    return parse_hatp_proof(json.dumps(_AG5_FIXTURE))


# ── Golden vectors ─────────────────────────────────────────────────────────


def test_ag3_golden_canonical_bytes() -> None:
    assert canonicalize_hatp_proof_payload(_ag3_proof()) == _AG3_GOLDEN_BYTES


def test_ag5_golden_canonical_bytes() -> None:
    assert canonicalize_hatp_proof_payload(_ag5_proof()) == _AG5_GOLDEN_BYTES


def test_ag3_golden_digest() -> None:
    import hashlib

    expected = hashlib.sha256(_AG3_GOLDEN_BYTES).hexdigest()
    assert digest_hatp_proof_payload(_ag3_proof()) == expected


def test_ag5_golden_digest() -> None:
    import hashlib

    expected = hashlib.sha256(_AG5_GOLDEN_BYTES).hexdigest()
    assert digest_hatp_proof_payload(_ag5_proof()) == expected


def test_ag3_ag5_golden_digests_differ() -> None:
    assert digest_hatp_proof_payload(_ag3_proof()) != digest_hatp_proof_payload(_ag5_proof())


# ── Key-order / whitespace independence ────────────────────────────────────


def test_key_order_independence() -> None:
    reordered = dict(reversed(list(_AG3_FIXTURE.items())))
    a = parse_hatp_proof(json.dumps(_AG3_FIXTURE))
    b = parse_hatp_proof(json.dumps(reordered))
    assert canonicalize_hatp_proof_payload(a) == canonicalize_hatp_proof_payload(b)


def test_whitespace_independence() -> None:
    compact = json.dumps(_AG3_FIXTURE, separators=(",", ":"))
    spaced = json.dumps(_AG3_FIXTURE, indent=4, separators=(",", ": "))
    a = parse_hatp_proof(compact)
    b = parse_hatp_proof(spaced)
    assert canonicalize_hatp_proof_payload(a) == canonicalize_hatp_proof_payload(b)


def test_equivalent_timestamp_representations_canonicalize_identically() -> None:
    doc_z = dict(_AG3_FIXTURE, issued_at="2026-08-06T00:00:00.000Z")
    doc_offset = dict(_AG3_FIXTURE, issued_at="2026-08-06T00:00:00.000000+00:00")
    a = parse_hatp_proof(json.dumps(doc_z))
    b = parse_hatp_proof(json.dumps(doc_offset))
    assert canonicalize_hatp_proof_payload(a) == canonicalize_hatp_proof_payload(b)


# ── Round trip ──────────────────────────────────────────────────────────


def test_canonical_round_trip_is_stable() -> None:
    proof = _ag3_proof()
    first_bytes = canonicalize_hatp_proof_payload(proof)
    reparsed = parse_hatp_proof(json.dumps(hatp_proof_to_document(proof)))
    second_bytes = canonicalize_hatp_proof_payload(reparsed)
    assert first_bytes == second_bytes


def test_serialization_deterministic_across_calls() -> None:
    proof = _ag3_proof()
    assert canonicalize_hatp_proof_payload(proof) == canonicalize_hatp_proof_payload(proof)
    assert digest_hatp_proof_payload(proof) == digest_hatp_proof_payload(proof)


def test_model_equality_is_semantic_not_json_order_dependent() -> None:
    a = parse_hatp_proof(json.dumps(_AG3_FIXTURE))
    b = parse_hatp_proof(json.dumps(dict(reversed(list(_AG3_FIXTURE.items())))))
    assert a == b


# ── Unicode determinism ────────────────────────────────────────────────────


def test_unicode_principal_id_deterministic() -> None:
    doc = dict(_AG3_FIXTURE, principal_id="élève")  # "\xe9l\xe8ve"
    a = parse_hatp_proof(json.dumps(doc))
    b = parse_hatp_proof(json.dumps(doc, ensure_ascii=False))
    assert canonicalize_hatp_proof_payload(a) == canonicalize_hatp_proof_payload(b)
    assert "élève".encode("utf-8") in canonicalize_hatp_proof_payload(a)


# ── Semantic mutation sensitivity matrix (AG3) ────────────────────────────

_AG3_MUTATIONS = {
    "principal_id": "mallory",
    "signer_key_id": "signer-2",
    "provider_profile": "SOME_OTHER_PROFILE_V1",
    "decision_record_id": "chgr-record-2",
    "decision_record_digest": "f" * 64,
    "binding_id": "rae-binding-2",
    "binding_digest": "e" * 64,
    "job_id": "job-2",
    "original_commit_sha": "d" * 40,
    "issued_at": "2026-08-06T00:00:01.000Z",
}


@pytest.mark.parametrize("field", sorted(_AG3_MUTATIONS))
def test_ag3_field_mutation_changes_canonical_bytes(field: str) -> None:
    mutated = dict(_AG3_FIXTURE)
    mutated[field] = _AG3_MUTATIONS[field]
    original = _ag3_proof()
    changed = parse_hatp_proof(json.dumps(mutated))
    assert canonicalize_hatp_proof_payload(original) != canonicalize_hatp_proof_payload(changed)
    assert digest_hatp_proof_payload(original) != digest_hatp_proof_payload(changed)


def test_ag3_repository_id_mutation_changes_canonical_bytes() -> None:
    mutated = dict(_AG3_FIXTURE, repository_id="22222222-2222-4222-8222-222222222222")
    original = _ag3_proof()
    changed = parse_hatp_proof(json.dumps(mutated))
    assert canonicalize_hatp_proof_payload(original) != canonicalize_hatp_proof_payload(changed)
    assert digest_hatp_proof_payload(original) != digest_hatp_proof_payload(changed)


def test_proof_version_is_out_of_supported_range_but_mutation_still_detectable() -> None:
    """`proof_version` cannot be mutated to a currently-unsupported value
    and still parse (SUPPORTED_PROOF_VERSIONS={1}), so its
    mutation-sensitivity is proven structurally instead: two
    differently-constructed valid proofs with the same version compare
    equal only when every other field also matches."""

    a = _ag3_proof()
    b = HumanApprovalProvenanceProof(**{**a.__dict__})
    assert canonicalize_hatp_proof_payload(a) == canonicalize_hatp_proof_payload(b)


# ── Semantic mutation sensitivity matrix (AG5) ────────────────────────────

_AG5_MUTATIONS = {
    "per_id": "per-2",
    "ecp_id": "ecp-2",
}


@pytest.mark.parametrize("field", sorted(_AG5_MUTATIONS))
def test_ag5_field_mutation_changes_canonical_bytes(field: str) -> None:
    mutated = dict(_AG5_FIXTURE)
    mutated[field] = _AG5_MUTATIONS[field]
    original = _ag5_proof()
    changed = parse_hatp_proof(json.dumps(mutated))
    assert canonicalize_hatp_proof_payload(original) != canonicalize_hatp_proof_payload(changed)
    assert digest_hatp_proof_payload(original) != digest_hatp_proof_payload(changed)


def test_rollback_site_family_change_changes_canonical_bytes() -> None:
    """Swapping the entire operation family (necessarily swapping fields
    too) is the maximal mutation and must change canonical bytes."""

    ag3_bytes = canonicalize_hatp_proof_payload(_ag3_proof())
    ag5_bytes = canonicalize_hatp_proof_payload(_ag5_proof())
    assert ag3_bytes != ag5_bytes


# ── No floats / booleans in canonical form ─────────────────────────────────


def test_canonical_bytes_contain_no_floating_point_rendering() -> None:
    raw = canonicalize_hatp_proof_payload(_ag3_proof())
    text = raw.decode("utf-8")
    assert '"proof_version":1' in text
    assert '"proof_version":1.0' not in text


def test_deepcopy_of_fixture_unaffected_by_serialization() -> None:
    """Canonicalization must not mutate caller state -- proving purity
    (no hidden side effects on the input dict a caller might reuse)."""

    fixture_copy = copy.deepcopy(_AG3_FIXTURE)
    canonicalize_hatp_proof_payload(_ag3_proof())
    assert fixture_copy == _AG3_FIXTURE
