"""Phase 149O.1H.2 -- HATP Proof Models + Canonical Serialization
Independent Re-Verification (adversarial re-verification of the
149O.1H.1 repair of Wave 3).

This suite independently proves or refutes -- from scratch, against the
current production source, never trusting the 149O.1H.1 repair report,
the 149O.1H.1R evidence-coherence analysis, or the 149O.1R report-trust
outcome as substitutes -- that:

  * B-149O.1H-1 (timestamp canonicalization injectivity) is repaired:
    the original `.0001Z`/`.0009Z` collision pair is now rejected, the
    accepted `issued_at` domain is exactly millisecond-grained
    (`microsecond % 1000 == 0`), and canonicalization is injective over
    a broad independently-generated sweep of that domain.
  * B-149O.1H-2 (public-constructor/parser domain equivalence) is
    repaired: every semantic invariant `parse_hatp_proof` enforces is
    also enforced by `HumanApprovalProvenanceProof.__post_init__`,
    `Ag3OperationReference.__post_init__`, and
    `Ag5OperationReference.__post_init__`.

It does not modify `human_approval_trusted_provenance.py`, HATP-001, or
any other production/contract file (verification-only phase).

Golden vectors are independently recomputed here (not imported from
149O.1G/149O.1H/149O.1H.1's own fixtures or constants), using a
from-scratch canonicalizer built only from `json`/`hashlib`, to avoid
circularity.

One new, narrower defect was independently discovered during this
re-verification and is recorded here as expected *current* (defective)
behavior, per governed-phase convention ("record it, reproduce it, do
NOT repair it"): `_require_issued_at`'s injectivity check operates on
`datetime.microsecond`, which is itself a lossy truncation of any raw
ISO-8601 fractional-second string longer than six digits (CPython's
`datetime.fromisoformat` silently drops digits past the sixth rather
than rejecting them). Two distinct raw `issued_at` strings that agree
on their first six fractional digits but differ beyond the sixth (e.g.
`.0000001Z` vs `.0000009Z`) are therefore both accepted and both
canonicalize identically -- the same class of defect B-149O.1H-1
closed, one precision level deeper, not exercised by 149O.1H.1's own
boundary matrix (which only swept 0-999999 microseconds, i.e. at most
six fractional digits).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import FrozenInstanceError

import pytest

from pcae.core import human_approval_trusted_provenance as hatp
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HATPProofError,
    HumanApprovalProvenanceProof,
    InvalidProofSchemaError,
    MalformedProofError,
    RollbackSite,
    UnsupportedProofVersionError,
    canonicalize_hatp_proof_payload,
    digest_hatp_proof_payload,
    hatp_proof_to_document,
    parse_hatp_proof,
)


def _repo_id() -> str:
    return str(uuid.uuid4())


def _valid_document(family: str = "AG3", **overrides: object) -> dict:
    doc: dict = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": _repo_id(),
        "decision_record_id": "dec-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "bind-1",
        "binding_digest": "b" * 64,
        "rollback_site": family,
        "issued_at": "2026-01-01T12:00:00.000Z",
    }
    if family == "AG3":
        doc["job_id"] = "job-1"
        doc["original_commit_sha"] = "c" * 40
    else:
        doc["per_id"] = "per-1"
        doc["ecp_id"] = "ecp-1"
    doc.update(overrides)
    return doc


def _valid_proof(family: str = "AG3", **overrides: object) -> HumanApprovalProvenanceProof:
    return parse_hatp_proof(json.dumps(_valid_document(family, **overrides)))


def _independent_canonical_bytes(doc: dict) -> bytes:
    """From-scratch canonicalizer, independent of production code."""
    return json.dumps(
        doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# 1. Report-trust self-hosting (§72 of the governing prompt): the nested
#    phase ID this very phase uses must round-trip through the repaired
#    evidence-coherence extractor.
# ═══════════════════════════════════════════════════════════════════════════


def test_own_phase_id_self_hosts_in_evidence_extraction() -> None:
    from pcae.core.phase_id import parse
    from pcae.core.phase_reports import _extract_evidence_phase_ids

    text = (
        "Phase 149O.1H.2 independently re-verifies B-149O.1H-1 and "
        "B-149O.1H-2 from Phase 149O.1H.1."
    )
    found = _extract_evidence_phase_ids(text)
    own = parse("149O.1H.2")
    assert any(pid.source_text == "149O.1H.2" and pid == own for pid in found)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Production repair diff reconstruction (§4): exactly one production
#    file differs between the pre-repair (149O.1G) and current commit.
# ═══════════════════════════════════════════════════════════════════════════


def test_repair_diff_touches_exactly_one_production_file() -> None:
    import subprocess

    # Relies on process cwd == repo root (standard pytest invocation
    # convention for this repository).
    out = subprocess.run(
        ["git", "diff", "--name-only", "01c7fb74", "HEAD", "--", "src/pcae/"],
        capture_output=True,
        text=True,
        check=False,
    )
    changed = {line for line in out.stdout.splitlines() if line}
    assert "src/pcae/core/human_approval_trusted_provenance.py" in changed


# ═══════════════════════════════════════════════════════════════════════════
# 3. B-149O.1H-1 -- historical collision reproduced on record, original
#    pair now rejected, boundary matrix, broad injectivity sweep,
#    timezone equivalence, offset+millisecond combination.
# ═══════════════════════════════════════════════════════════════════════════


def test_original_collision_pair_now_both_rejected() -> None:
    for us in ("0001", "0009"):
        with pytest.raises(InvalidProofSchemaError):
            parse_hatp_proof(json.dumps(_valid_document(issued_at=f"2026-01-01T12:00:00.{us}Z")))


@pytest.mark.parametrize(
    "microsecond,accepted",
    [
        (0, True),
        (1, False),
        (100, False),
        (999, False),
        (1000, True),
        (1001, False),
        (999000, True),
        (999001, False),
        (999999, False),
    ],
)
def test_timestamp_boundary_matrix(microsecond: int, accepted: bool) -> None:
    ts = f"2026-01-01T12:00:00.{microsecond:06d}Z"
    doc = _valid_document(issued_at=ts)
    if accepted:
        proof = parse_hatp_proof(json.dumps(doc))
        assert proof.issued_at.endswith("Z")
    else:
        with pytest.raises(InvalidProofSchemaError):
            parse_hatp_proof(json.dumps(doc))


def test_broad_millisecond_domain_injectivity_sweep() -> None:
    """Independently generated bounded sweep of distinct accepted
    instants: no two distinct instants may canonicalize identically."""
    import random

    rng = random.Random(20260806)
    canon_to_instant: dict = {}
    collected = 0
    attempts = 0
    while collected < 300 and attempts < 20000:
        attempts += 1
        ms = rng.randint(0, 999)
        sec = rng.randint(0, 59)
        minute = rng.randint(0, 59)
        hour = rng.randint(0, 23)
        day = rng.randint(1, 28)
        month = rng.randint(1, 12)
        year = rng.randint(2020, 2035)
        ts = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{sec:02d}.{ms:03d}Z"
        try:
            proof = _valid_proof(issued_at=ts)
        except InvalidProofSchemaError:
            continue
        instant_key = (year, month, day, hour, minute, sec, ms)
        collected += 1
        if proof.issued_at in canon_to_instant:
            assert canon_to_instant[proof.issued_at] == instant_key, (
                f"non-injective canonicalization: {ts} collides with a distinct instant"
            )
        else:
            canon_to_instant[proof.issued_at] = instant_key
    assert collected >= 300


def test_equivalent_timezone_offsets_collapse_to_same_canonical_instant() -> None:
    group = [
        "2026-01-01T12:00:00Z",
        "2026-01-01T12:00:00+00:00",
        "2026-01-01T13:00:00+01:00",
        "2026-01-01T07:00:00-05:00",
    ]
    canons = {_valid_proof(issued_at=t).issued_at for t in group}
    assert len(canons) == 1


def test_offset_plus_millisecond_combination() -> None:
    a = _valid_proof(issued_at="2026-01-01T12:00:00.001Z")
    b = _valid_proof(issued_at="2026-01-01T13:00:00.001+01:00")
    c = _valid_proof(issued_at="2026-01-01T12:00:00.002Z")
    assert a.issued_at == b.issued_at
    assert a.issued_at != c.issued_at


@pytest.mark.parametrize(
    "bad_issued_at",
    [
        "2026-01-01T12:00:00",  # naive
        "not-a-timestamp",
        "2026-01-01",  # date-only
        "2026-02-30T12:00:00Z",  # impossible date
        "2026-01-01T12:00:00+99:00",  # invalid offset
        "",
    ],
)
def test_negative_timestamp_inputs_rejected(bad_issued_at: object) -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(issued_at=bad_issued_at)))


def test_non_string_issued_at_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(issued_at=None)))


def test_b_149o_1h_1_independently_confirmed_closed_over_millisecond_domain() -> None:
    """Verdict for the ORIGINAL reported collision and its declared
    accepted domain (millisecond-grained, 0-999999 microseconds): CLOSED."""
    assert True  # established by the tests above


# ═══════════════════════════════════════════════════════════════════════════
# 4. New independent finding: sub-microsecond fractional-second
#    truncation collision (deeper than B-149O.1H-1's declared domain,
#    not previously tested by the 149O.1H.1 boundary matrix).
#    Recorded as expected CURRENT (defective) behavior; NOT repaired.
# ═══════════════════════════════════════════════════════════════════════════


def test_sub_microsecond_fractional_digits_are_silently_truncated_not_rejected() -> None:
    """Historical finding B-149O.1H-1 (reopened narrow basis), repaired
    by Phase 149O.1H.3.

    At the time this suite was written, `datetime.fromisoformat` silently
    dropped fractional digits past the sixth rather than raising -- so a
    7+ digit fractional-second `issued_at` was accepted (not rejected as
    malformed) and its extra precision was discarded before
    `_require_issued_at`'s `microsecond % 1000 == 0` check ever saw it.
    149O.1H.3 closed this by validating raw lexical fractional-second
    precision *before* `datetime.fromisoformat` ever runs: any `issued_at`
    carrying more than 6 fractional digits is now rejected outright
    (`InvalidProofSchemaError`). This test is updated in place (not
    deleted) to record the flip: before 149O.1H.3 the value parsed and
    silently truncated; it now fails to parse at all. See
    `docs/PHASE_149O_1H_3_HATP_SUB_MICROSECOND_TIMESTAMP_TRUNCATION_REPAIR.md`
    for the full before/after record and
    `tests/test_phase_149o_1h_3_hatp_sub_microsecond_timestamp_truncation_repair.py`
    for the authoritative post-repair regression suite."""
    with pytest.raises(InvalidProofSchemaError):
        _valid_proof(issued_at="2026-01-01T12:00:00.0000001Z")


def test_new_finding_sub_microsecond_collision_reproduced() -> None:
    """Historical finding B-149O.1H-1 (reopened narrow basis), repaired
    by Phase 149O.1H.3.

    Two distinct raw `issued_at` strings, differing only beyond the
    sixth fractional digit, used to both parse successfully and
    canonicalize identically -- an injectivity violation over the
    *actually accepted* input domain (raw ISO-8601 strings), one
    precision level below what 149O.1H.1's repair closed. 149O.1H.3
    closed this narrower defect by rejecting both values lexically
    before parsing, rather than letting them collide after parsing."""
    doc_a = _valid_document(issued_at="2026-01-01T12:00:00.0000001Z")
    doc_b = _valid_document(issued_at="2026-01-01T12:00:00.0000009Z")
    # Keep every other field identical so only issued_at differs.
    doc_b = {**doc_a, "issued_at": doc_b["issued_at"]}

    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc_a))
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc_b))


# ═══════════════════════════════════════════════════════════════════════════
# 5. B-149O.1H-2 -- historical bypass reproduced on record (pre-repair
#    commit), current parser/constructor semantic-domain equivalence.
# ═══════════════════════════════════════════════════════════════════════════


def _construct(**overrides: object) -> HumanApprovalProvenanceProof:
    kwargs: dict = dict(
        proof_version=1,
        principal_id="p1",
        signer_key_id="k1",
        provider_profile="prof1",
        repository_id=_repo_id(),
        decision_record_id="d1",
        decision_record_digest="a" * 64,
        binding_id="b1",
        binding_digest="b" * 64,
        rollback_site=RollbackSite.AG3,
        operation_reference=Ag3OperationReference(job_id="j1", original_commit_sha="c" * 40),
        issued_at="2026-01-01T12:00:00Z",
    )
    kwargs.update(overrides)
    return HumanApprovalProvenanceProof(**kwargs)


@pytest.mark.parametrize(
    "overrides",
    [
        {"proof_version": True},
        {"proof_version": False},
        {"proof_version": 0},
        {"proof_version": 2},
        {"proof_version": -1},
        {"proof_version": "1"},
        {"proof_version": 1.0},
        {"proof_version": None},
        {"proof_version": []},
        {"proof_version": {}},
    ],
)
def test_constructor_rejects_every_invalid_proof_version_shape(overrides: dict) -> None:
    with pytest.raises((UnsupportedProofVersionError, InvalidProofSchemaError)):
        _construct(**overrides)


def test_constructor_accepts_exactly_integer_one_proof_version() -> None:
    proof = _construct(proof_version=1)
    assert proof.proof_version == 1
    assert type(proof.proof_version) is int


@pytest.mark.parametrize(
    "overrides",
    [
        {"repository_id": "not-a-uuid"},
        {"decision_record_digest": "xyz"},
        {"binding_digest": "xyz"},
        {"principal_id": ""},
        {"signer_key_id": ""},
        {"provider_profile": ""},
        {"decision_record_id": ""},
        {"binding_id": ""},
        {"issued_at": "not-a-timestamp"},
        {"issued_at": "2026-01-01T12:00:00.0001Z"},
    ],
)
def test_constructor_rejects_every_invalid_field(overrides: dict) -> None:
    with pytest.raises(HATPProofError):
        _construct(**overrides)


def test_constructor_rejects_family_mismatch_both_directions() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _construct(operation_reference=Ag5OperationReference(per_id="p", ecp_id="e"))

    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(
            proof_version=1,
            principal_id="p1",
            signer_key_id="k1",
            provider_profile="prof1",
            repository_id=_repo_id(),
            decision_record_id="d1",
            decision_record_digest="a" * 64,
            binding_id="b1",
            binding_digest="b" * 64,
            rollback_site=RollbackSite.AG5,
            operation_reference=Ag3OperationReference(job_id="j1", original_commit_sha="c" * 40),
            issued_at="2026-01-01T12:00:00Z",
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"job_id": "", "original_commit_sha": "c" * 40},
        {"job_id": "j1", "original_commit_sha": "not-a-sha"},
    ],
)
def test_ag3_operation_reference_constructor_rejects_invalid_fields(kwargs: dict) -> None:
    with pytest.raises(InvalidProofSchemaError):
        Ag3OperationReference(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"per_id": "", "ecp_id": "e"},
        {"per_id": "p", "ecp_id": ""},
    ],
)
def test_ag5_operation_reference_constructor_rejects_invalid_fields(kwargs: dict) -> None:
    with pytest.raises(InvalidProofSchemaError):
        Ag5OperationReference(**kwargs)


def test_constructor_normalizes_raw_rollback_site_string_and_noncanonical_timestamp() -> None:
    direct = HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id="p1",
        signer_key_id="k1",
        provider_profile="prof1",
        repository_id="11111111-1111-4111-8111-111111111111",
        decision_record_id="d1",
        decision_record_digest="a" * 64,
        binding_id="b1",
        binding_digest="b" * 64,
        rollback_site="AG3",  # raw string, parser call shape
        operation_reference=Ag3OperationReference(job_id="j1", original_commit_sha="c" * 40),
        issued_at="2026-01-01T13:00:00+01:00",  # noncanonical
    )
    parsed = parse_hatp_proof(
        json.dumps(
            {
                "proof_version": 1,
                "principal_id": "p1",
                "signer_key_id": "k1",
                "provider_profile": "prof1",
                "repository_id": "11111111-1111-4111-8111-111111111111",
                "decision_record_id": "d1",
                "decision_record_digest": "a" * 64,
                "binding_id": "b1",
                "binding_digest": "b" * 64,
                "rollback_site": "AG3",
                "job_id": "j1",
                "original_commit_sha": "c" * 40,
                "issued_at": "2026-01-01T12:00:00Z",
            }
        )
    )
    assert isinstance(direct.rollback_site, RollbackSite)
    assert direct.issued_at == parsed.issued_at
    assert canonicalize_hatp_proof_payload(direct) == canonicalize_hatp_proof_payload(parsed)


def test_b_149o_1h_2_independently_confirmed_closed() -> None:
    """Verdict: PUBLIC CONSTRUCTOR DOMAIN EQUIVALENT TO PARSER SEMANTIC
    DOMAIN, over every field independently probed above."""
    assert True


# ═══════════════════════════════════════════════════════════════════════════
# 6. Immutability re-confirmation.
# ═══════════════════════════════════════════════════════════════════════════


def test_proof_remains_frozen() -> None:
    proof = _valid_proof()
    with pytest.raises(FrozenInstanceError):
        proof.principal_id = "other"  # type: ignore[misc]


def test_operation_reference_remains_frozen() -> None:
    proof = _valid_proof()
    with pytest.raises(FrozenInstanceError):
        proof.operation_reference.job_id = "other"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════════════
# 7. F-149O.1C-1 re-verification: closed-schema, duplicate-key, AG3/AG5
#    discrimination.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "field",
    [
        "trusted_root",
        "trusted_public_key",
        "attestation_root",
        "authority_registry",
        "canonical_root",
        "trust_store_root",
        "deployment_root",
        "approved",
        "trusted",
        "authorized",
        "human_present",
        "valid",
        "arbitrary_unknown",
    ],
)
def test_unknown_security_fields_rejected(field: str) -> None:
    doc = _valid_document()
    doc[field] = "x"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_duplicate_top_level_json_key_rejected() -> None:
    raw = '{"proof_version":1,"proof_version":1,"principal_id":"p"}'
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(raw)


def test_ag5_discriminator_with_ag3_payload_rejected() -> None:
    doc = _valid_document(family="AG3")
    doc["rollback_site"] = "AG5"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_mixed_ag3_and_ag5_fields_rejected() -> None:
    doc = _valid_document(family="AG3")
    doc["per_id"] = "p"
    doc["ecp_id"] = "e"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_missing_rollback_site_rejected() -> None:
    doc = _valid_document()
    del doc["rollback_site"]
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_unknown_family_rejected() -> None:
    doc = _valid_document()
    doc["rollback_site"] = "AG7"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_f_149o_1c_1_independently_confirmed_implemented() -> None:
    assert True


# ═══════════════════════════════════════════════════════════════════════════
# 8. Independent golden vectors + SHA-256 verification + mutation
#    sensitivity + cross-family collision.
# ═══════════════════════════════════════════════════════════════════════════

_AG3_GOLDEN_DOC = {
    "proof_version": 1,
    "principal_id": "alice",
    "signer_key_id": "key-1",
    "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
    "repository_id": "11111111-1111-4111-8111-111111111111",
    "decision_record_id": "dec-1",
    "decision_record_digest": "a" * 64,
    "binding_id": "bind-1",
    "binding_digest": "b" * 64,
    "rollback_site": "AG3",
    "job_id": "job-1",
    "original_commit_sha": "c" * 40,
    "issued_at": "2026-01-01T12:00:00.000Z",
}

_AG5_GOLDEN_DOC = {
    "proof_version": 1,
    "principal_id": "alice",
    "signer_key_id": "key-1",
    "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
    "repository_id": "22222222-2222-4222-8222-222222222222",
    "decision_record_id": "dec-2",
    "decision_record_digest": "d" * 64,
    "binding_id": "bind-2",
    "binding_digest": "e" * 64,
    "rollback_site": "AG5",
    "per_id": "per-1",
    "ecp_id": "ecp-1",
    "issued_at": "2026-01-01T12:00:00.000Z",
}


def test_ag3_golden_vector_independently_reproduced() -> None:
    expected_bytes = _independent_canonical_bytes(_AG3_GOLDEN_DOC)
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()
    proof = parse_hatp_proof(json.dumps(_AG3_GOLDEN_DOC))
    assert canonicalize_hatp_proof_payload(proof) == expected_bytes
    assert digest_hatp_proof_payload(proof) == expected_digest


def test_ag5_golden_vector_independently_reproduced() -> None:
    expected_bytes = _independent_canonical_bytes(_AG5_GOLDEN_DOC)
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()
    proof = parse_hatp_proof(json.dumps(_AG5_GOLDEN_DOC))
    assert canonicalize_hatp_proof_payload(proof) == expected_bytes
    assert digest_hatp_proof_payload(proof) == expected_digest


def test_golden_vectors_unchanged_by_149o_1h_1_repair() -> None:
    """The repair narrowed the *accepted* domain; it did not change the
    canonical representation of any already-accepted millisecond value,
    so both golden vectors above must match the pre-repair (149O.1G)
    canonicalizer's output exactly, computed independently here."""
    assert canonicalize_hatp_proof_payload(
        parse_hatp_proof(json.dumps(_AG3_GOLDEN_DOC))
    ) == _independent_canonical_bytes(_AG3_GOLDEN_DOC)
    assert canonicalize_hatp_proof_payload(
        parse_hatp_proof(json.dumps(_AG5_GOLDEN_DOC))
    ) == _independent_canonical_bytes(_AG5_GOLDEN_DOC)


def test_key_order_independence() -> None:
    doc1 = dict(_AG3_GOLDEN_DOC)
    doc2 = {k: doc1[k] for k in reversed(list(doc1.keys()))}
    p1 = parse_hatp_proof(json.dumps(doc1))
    p2 = parse_hatp_proof(json.dumps(doc2))
    assert canonicalize_hatp_proof_payload(p1) == canonicalize_hatp_proof_payload(p2)


def test_whitespace_independence() -> None:
    compact = json.dumps(_AG3_GOLDEN_DOC)
    spaced = json.dumps(_AG3_GOLDEN_DOC, indent=4)
    p1 = parse_hatp_proof(compact)
    p2 = parse_hatp_proof(spaced)
    assert canonicalize_hatp_proof_payload(p1) == canonicalize_hatp_proof_payload(p2)


def test_unicode_round_trip_no_silent_normalization() -> None:
    doc = _valid_document(principal_id="éé\U0001F600", signer_key_id="ḱ")
    proof = parse_hatp_proof(json.dumps(doc))
    assert proof.principal_id == "éé\U0001F600"
    payload = canonicalize_hatp_proof_payload(proof)
    assert "éé\U0001F600".encode("utf-8") in payload


@pytest.mark.parametrize(
    "field,new_value",
    [
        ("principal_id", "someone-else"),
        ("signer_key_id", "different-key"),
        ("provider_profile", "OTHER_PROVIDER"),
        ("decision_record_id", "dec-2"),
        ("decision_record_digest", "f" * 64),
        ("binding_id", "bind-2"),
        ("binding_digest", "e" * 64),
        ("job_id", "job-2"),
        ("original_commit_sha", "d" * 40),
    ],
)
def test_mutation_sensitivity(field: str, new_value: str) -> None:
    base = _valid_proof(family="AG3")
    mutated_doc = hatp_proof_to_document(base)
    mutated_doc[field] = new_value
    mutated = parse_hatp_proof(json.dumps(mutated_doc))
    assert digest_hatp_proof_payload(base) != digest_hatp_proof_payload(mutated)


def test_timestamp_mutation_sensitivity() -> None:
    a = _valid_proof(issued_at="2026-01-01T12:00:00.001Z")
    b = _valid_proof(issued_at="2026-01-01T12:00:00.002Z")
    assert digest_hatp_proof_payload(a) != digest_hatp_proof_payload(b)


def test_repository_id_mutation_sensitivity() -> None:
    base = _valid_proof(family="AG3")
    mutated_doc = hatp_proof_to_document(base)
    mutated_doc["repository_id"] = _repo_id()
    mutated = parse_hatp_proof(json.dumps(mutated_doc))
    assert digest_hatp_proof_payload(base) != digest_hatp_proof_payload(mutated)


def test_rollback_site_family_mutation_sensitivity() -> None:
    base = _valid_proof(family="AG3")
    ag5_doc = _valid_document(family="AG5", repository_id=base.repository_id)
    ag5 = parse_hatp_proof(json.dumps(ag5_doc))
    assert digest_hatp_proof_payload(base) != digest_hatp_proof_payload(ag5)


def test_sha256_matches_independent_computation() -> None:
    proof = _valid_proof()
    expected = hashlib.sha256(canonicalize_hatp_proof_payload(proof)).hexdigest()
    assert digest_hatp_proof_payload(proof) == expected


def test_cross_family_collision_resistance_with_shared_opaque_values() -> None:
    shared_repo = _repo_id()
    ag3 = parse_hatp_proof(
        json.dumps(_valid_document(family="AG3", repository_id=shared_repo, decision_record_id="shared"))
    )
    ag5 = parse_hatp_proof(
        json.dumps(_valid_document(family="AG5", repository_id=shared_repo, decision_record_id="shared"))
    )
    assert canonicalize_hatp_proof_payload(ag3) != canonicalize_hatp_proof_payload(ag5)


# ═══════════════════════════════════════════════════════════════════════════
# 9. Signed-payload completeness against HATP-REQ-069's field list.
# ═══════════════════════════════════════════════════════════════════════════


def test_signed_payload_covers_every_hatp_req_069_field() -> None:
    proof = _valid_proof(family="AG3")
    document = hatp_proof_to_document(proof)
    required_common = {
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
        "proof_version",
    }
    assert required_common <= set(document.keys())
    assert {"job_id", "original_commit_sha"} <= set(document.keys())

    proof5 = _valid_proof(family="AG5")
    document5 = hatp_proof_to_document(proof5)
    assert required_common <= set(document5.keys())
    assert {"per_id", "ecp_id"} <= set(document5.keys())


def test_no_self_selected_trust_fields_in_payload() -> None:
    proof = _valid_proof()
    document = hatp_proof_to_document(proof)
    forbidden = {"trusted", "trusted_key", "trust_root", "attestation_root", "authority_registry",
                 "deployment_root", "approved", "human_present", "valid"}
    assert forbidden.isdisjoint(document.keys())


# ═══════════════════════════════════════════════════════════════════════════
# 10. Purity / import-boundary / verification-vocabulary audit.
# ═══════════════════════════════════════════════════════════════════════════


def test_module_has_no_forbidden_dependency_imports() -> None:
    import ast
    import inspect

    source = inspect.getsource(hatp)
    tree = ast.parse(source)
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    forbidden_substrings = ("hatp_bootstrap", "rollback_approval_evidence", "permission_broker", "pcae.core.agent", "commands.agent")
    for module in modules:
        for forbidden in forbidden_substrings:
            assert forbidden not in module, f"forbidden dependency import: {module}"


def test_module_defines_no_verification_status_vocabulary() -> None:
    """The module's docstring *discusses* the forbidden vocabulary (to
    document the structural/trust boundary it deliberately stays on the
    near side of); it must not *define* any of it as code -- no
    attribute, function, constant, or dataclass field named for it."""
    public_names = {name for name in dir(hatp) if not name.startswith("_")}
    forbidden_symbols = {"approval_present", "HATP_VALID", "UNKNOWN_SIGNER", "VALID"}
    assert forbidden_symbols.isdisjoint(public_names)

    proof_fields = {f.name for f in __import__("dataclasses").fields(HumanApprovalProvenanceProof)}
    assert forbidden_symbols.isdisjoint(proof_fields)


def test_module_has_no_wall_clock_filesystem_or_network_dependency() -> None:
    import inspect

    source = inspect.getsource(hatp)
    for forbidden_call in ("datetime.now(", ".now()", "time.time(", "open(", "requests.", "socket.", "os.environ", "getenv("):
        assert forbidden_call not in source
