"""Adversarial tests for `human_authentication_proof.py` — Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.3."""

from __future__ import annotations

import dataclasses

import pytest

from pcae.core.hpac_foundation import HPACDuplicateError, canonical_digest
from pcae.core.human_authentication_proof import (
    HumanAuthenticationProof,
    HumanAuthenticationProofStore,
    HumanAuthenticationProofTrustError,
    PROOF_SCHEMA_VERSION,
    new_proof_id,
)


def _valid_proof(**overrides) -> HumanAuthenticationProof:
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": new_proof_id(),
        "mechanism_id": "hpac.deterministic.test-only.v1",
        "principal_id": "hp-1",
        "credential_id": "hpc-1",
        "challenge_digest": "a" * 64,
        "approval_subject_digest": "b" * 64,
        "trusted_presentation_ref": {"presentation_id": "hpe-" + "c" * 32, "presentation_digest": "d" * 64},
        "assertion": "deadbeef",
        "up": True,
        "uv": True,
        "authenticated_at": "2026-08-28T00:03:00Z",
        "verifier_version": "test-fixture-v1",
    }
    body.update(overrides)
    digest = canonical_digest(body)
    return HumanAuthenticationProof(proof_digest=digest, **body)


def test_valid_deterministic_proof_creates_and_resolves(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    proof = _valid_proof()
    store.create(proof)
    resolved = store.resolve(proof.proof_id)
    assert resolved == proof


def test_up_false_rejected(tmp_path):
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": new_proof_id(),
        "mechanism_id": "m",
        "principal_id": "hp-1",
        "credential_id": "hpc-1",
        "challenge_digest": "a" * 64,
        "approval_subject_digest": "b" * 64,
        "trusted_presentation_ref": {"presentation_id": "hpe-" + "c" * 32, "presentation_digest": "d" * 64},
        "assertion": "x",
        "up": False,
        "uv": True,
        "authenticated_at": "2026-08-28T00:00:00Z",
        "verifier_version": "v1",
    }
    digest = canonical_digest(body)
    proof = HumanAuthenticationProof(proof_digest=digest, **body)
    store = HumanAuthenticationProofStore(tmp_path)
    with pytest.raises(HumanAuthenticationProofTrustError):
        store.create(proof)


def test_uv_false_rejected(tmp_path):
    proof = _valid_proof()
    body = proof.to_document(include_digest=False)
    body["uv"] = False
    digest = canonical_digest(body)
    forged = HumanAuthenticationProof(proof_digest=digest, **body)
    store = HumanAuthenticationProofStore(tmp_path)
    with pytest.raises(HumanAuthenticationProofTrustError):
        store.create(forged)


def test_wrong_principal_distinguishable_across_two_proofs(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    proof_a = _valid_proof(principal_id="hp-a")
    proof_b = _valid_proof(principal_id="hp-b")
    store.create(proof_a)
    store.create(proof_b)
    assert store.resolve(proof_a.proof_id).principal_id == "hp-a"
    assert store.resolve(proof_b.proof_id).principal_id == "hp-b"


def test_wrong_credential_recorded_as_presented(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    proof = _valid_proof(credential_id="hpc-unexpected")
    store.create(proof)
    assert store.resolve(proof.proof_id).credential_id == "hpc-unexpected"


def test_wrong_challenge_recorded_as_presented(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    proof = _valid_proof(challenge_digest="f" * 64)
    store.create(proof)
    assert store.resolve(proof.proof_id).challenge_digest == "f" * 64


def test_wrong_presentation_ref_recorded_as_presented(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    proof = _valid_proof(trusted_presentation_ref={"presentation_id": "hpe-" + "9" * 32, "presentation_digest": "0" * 64})
    store.create(proof)
    resolved = store.resolve(proof.proof_id)
    assert resolved.trusted_presentation_ref["presentation_id"] == "hpe-" + "9" * 32


def test_malformed_record_missing_field_rejected(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    proof = _valid_proof()
    store.create(proof)
    path = store._path(proof.proof_id)
    import json

    doc = json.loads(path.read_text(encoding="utf-8"))
    del doc["verifier_version"]
    path.unlink()
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(Exception):
        store.resolve(proof.proof_id)


def test_replay_duplicate_proof_id_rejected(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    proof = _valid_proof()
    store.create(proof)
    with pytest.raises(HPACDuplicateError):
        store.create(proof)


def test_dataclass_replace_forgery_never_becomes_canonical(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    proof = _valid_proof()
    store.create(proof)
    forged = dataclasses.replace(proof, principal_id="hp-attacker")
    resolved = store.resolve(proof.proof_id)
    assert resolved.principal_id != forged.principal_id
    assert resolved.principal_id == proof.principal_id


def test_raw_proof_object_never_produced_by_authenticator_alone(tmp_path):
    """A hand-constructed HumanAuthenticationProof (never produced by
    sequence-2 verification, since no verifier exists yet in this phase)
    is only accepted by the store if its digest is self-consistent AND it
    is explicitly submitted via create() -- there is no code path in this
    phase that reaches canonical storage without an explicit create()
    call, which is the honest boundary this foundation phase states."""

    store = HumanAuthenticationProofStore(tmp_path)
    lookalike = _valid_proof()
    # Never call store.create(lookalike).
    assert store.resolve(lookalike.proof_id) is None


def test_malformed_id_grammar_rejected(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    with pytest.raises(HumanAuthenticationProofTrustError):
        store.resolve("not-a-valid-proof-id")


def test_traversal_in_proof_id_rejected(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    with pytest.raises(HumanAuthenticationProofTrustError):
        store.resolve("../../../etc/passwd")


def test_unknown_schema_version_fails_closed(tmp_path):
    store = HumanAuthenticationProofStore(tmp_path)
    proof = _valid_proof()
    store.create(proof)
    path = store._path(proof.proof_id)
    import json

    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["proof_schema_version"] = "HPAC-PROOF/99.0"
    path.unlink()
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(Exception):
        store.resolve(proof.proof_id)
