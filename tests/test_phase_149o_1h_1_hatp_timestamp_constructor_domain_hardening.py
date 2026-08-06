"""Phase 149O.1H.1 -- HATP Timestamp Canonicalization + Constructor-
Domain Hardening: authoritative post-repair regression suite.

Repairs two Blocking findings from Phase 149O.1H's independent
verification of `pcae.core.human_approval_trusted_provenance` (Wave 3):

  * B-149O.1H-1 -- timestamp canonicalization was not injective: two
    distinct, individually-accepted `issued_at` instants differing only
    below one millisecond (e.g. `.0001Z` vs `.0009Z`) canonicalized to
    identical bytes/digest, because the renderer truncated (rather than
    rejected) sub-millisecond precision. Repaired by narrowing the
    *accepted* `issued_at` domain: any timestamp carrying non-zero
    fractional precision below one millisecond is now rejected outright,
    before model acceptance, so canonicalization is injective over the
    (now precisely millisecond-grained) accepted domain.

  * B-149O.1H-2 -- direct dataclass construction accepted a strict
    superset of what `parse_hatp_proof` accepted (no field-format
    validation in `__post_init__` beyond AG3/AG5 family agreement).
    Repaired by introducing a shared `_require_*` validator layer used
    by both the parser and every model's `__post_init__`, so direct
    construction now enforces the same structural security domain the
    parser enforces.

This suite does not modify, weaken, or duplicate the pre-existing
149O.1G/149O.1H suites; it adds focused repair coverage and the
required (per governing prompt items 104-107) timestamp boundary/
constructor-domain/equivalence-matrix tests.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HumanApprovalProvenanceProof,
    InvalidProofSchemaError,
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
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": family,
        "issued_at": "2026-08-06T00:00:00.000Z",
    }
    if family == "AG3":
        doc["job_id"] = "job-1"
        doc["original_commit_sha"] = "c" * 40
    else:
        doc["per_id"] = "per-1"
        doc["ecp_id"] = "ecp-1"
    doc.update(overrides)
    return doc


def _valid_kwargs(family: str = "AG3", **overrides: object) -> dict:
    common: dict = dict(
        proof_version=1,
        principal_id="alice",
        signer_key_id="signer-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=_repo_id(),
        decision_record_id="chgr-record-1",
        decision_record_digest="a" * 64,
        binding_id="rae-binding-1",
        binding_digest="b" * 64,
        issued_at="2026-08-06T00:00:00.000Z",
    )
    if family == "AG3":
        common["rollback_site"] = RollbackSite.AG3
        common["operation_reference"] = Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40)
    else:
        common["rollback_site"] = RollbackSite.AG5
        common["operation_reference"] = Ag5OperationReference(per_id="per-1", ecp_id="ecp-1")
    common.update(overrides)
    return common


def _construct(family: str = "AG3", **overrides: object) -> HumanApprovalProvenanceProof:
    return HumanApprovalProvenanceProof(**_valid_kwargs(family, **overrides))


# ═══════════════════════════════════════════════════════════════════════════
# B-149O.1H-1 closure -- historical collision pair
# ═══════════════════════════════════════════════════════════════════════════


def test_historical_collision_pair_both_rejected_not_collided() -> None:
    """The exact original 149O.1H reproduction pair: `.0001Z`/`.0009Z`,
    800 microseconds apart. Before repair both parsed and canonicalized
    to identical bytes/digest. After repair, both must fail to parse --
    never both accepted with colliding output, never one silently
    rounded into the other."""

    shared_repo = _repo_id()
    doc_a = _valid_document("AG3", repository_id=shared_repo, issued_at="2026-01-01T12:00:00.0001Z")
    doc_b = _valid_document("AG3", repository_id=shared_repo, issued_at="2026-01-01T12:00:00.0009Z")
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc_a))
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc_b))


# ═══════════════════════════════════════════════════════════════════════════
# Timestamp boundary matrix (governing prompt item 15)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "microseconds,accepted",
    [
        (0, True),
        (1, False),
        (100, False),
        (999, False),
        (1000, True),
        (1001, False),
        (999000, True),
        (999999, False),
    ],
)
def test_timestamp_boundary_matrix(microseconds: int, accepted: bool) -> None:
    base = datetime(2026, 1, 1, 12, 0, 0, microseconds, tzinfo=timezone.utc)
    raw = base.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    doc = _valid_document("AG3", issued_at=raw)
    if accepted:
        proof = parse_hatp_proof(json.dumps(doc))
        expected_ms = microseconds // 1000
        assert proof.issued_at == f"2026-01-01T12:00:00.{expected_ms:03d}Z"
    else:
        with pytest.raises(InvalidProofSchemaError):
            parse_hatp_proof(json.dumps(doc))


# ═══════════════════════════════════════════════════════════════════════════
# Distinct-instant property (governing prompt item 14/78): for any two
# accepted, distinct instants, canonical timestamps must differ.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("delta_ms", [1, 2, 500, 999, 1000, 60_000])
def test_distinct_accepted_instants_canonicalize_differently(delta_ms: int) -> None:
    base = datetime(2026, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    other = base + timedelta(milliseconds=delta_ms)
    doc_a = _valid_document("AG3", issued_at=base.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z")
    doc_b = _valid_document("AG3", issued_at=other.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z")
    proof_a = parse_hatp_proof(json.dumps(doc_a))
    proof_b = parse_hatp_proof(json.dumps(doc_b))
    assert proof_a.issued_at != proof_b.issued_at
    assert canonicalize_hatp_proof_payload(proof_a) != canonicalize_hatp_proof_payload(proof_b)
    assert digest_hatp_proof_payload(proof_a) != digest_hatp_proof_payload(proof_b)


def test_no_accepted_pair_collides_across_full_millisecond_sweep() -> None:
    """Property-style sweep (governing prompt item 78): every accepted
    millisecond value in a representative range canonicalizes to a
    distinct string; no two distinct accepted instants collide."""

    seen: set = set()
    for ms in range(0, 50):
        instant = datetime(2026, 1, 1, 0, 0, 0, ms * 1000, tzinfo=timezone.utc)
        raw = instant.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        proof = parse_hatp_proof(json.dumps(_valid_document("AG3", issued_at=raw)))
        assert proof.issued_at not in seen
        seen.add(proof.issued_at)
    assert len(seen) == 50


# ═══════════════════════════════════════════════════════════════════════════
# Equivalent-offset matrix (governing prompt item 16): same instant,
# different textual representation, must canonicalize identically.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00Z",
        "2026-01-01T12:00:00+00:00",
        "2026-01-01T13:00:00+01:00",
        "2026-01-01T07:00:00-05:00",
    ],
)
def test_equivalent_offsets_canonicalize_identically(raw: str) -> None:
    proof = parse_hatp_proof(json.dumps(_valid_document("AG3", issued_at=raw)))
    assert proof.issued_at == "2026-01-01T12:00:00.000Z"


# ═══════════════════════════════════════════════════════════════════════════
# Naive / invalid timestamp rejection (governing prompt item 17)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.000",  # naive, no timezone
        "not-a-timestamp",
        "",
        "2026-01-01",
    ],
)
def test_naive_or_malformed_timestamp_rejected(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", issued_at=raw)))
    with pytest.raises(InvalidProofSchemaError):
        _construct("AG3", issued_at=raw)


# ═══════════════════════════════════════════════════════════════════════════
# Round-trip canonical timestamp (governing prompt item 104)
# ═══════════════════════════════════════════════════════════════════════════


def test_round_trip_canonical_timestamp_is_stable() -> None:
    proof = parse_hatp_proof(json.dumps(_valid_document("AG3", issued_at="2026-03-04T05:06:07.008Z")))
    reparsed = parse_hatp_proof(json.dumps(hatp_proof_to_document(proof)))
    assert proof.issued_at == reparsed.issued_at == "2026-03-04T05:06:07.008Z"
    assert canonicalize_hatp_proof_payload(proof) == canonicalize_hatp_proof_payload(reparsed)


# ═══════════════════════════════════════════════════════════════════════════
# Constructor-domain hardening -- proof_version (governing prompt items
# 27, 105, 107: boolean trap)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("bad_version", [True, False, 0, 2, "1", None, 1.0])
def test_constructor_rejects_invalid_proof_version(bad_version: object) -> None:
    with pytest.raises(UnsupportedProofVersionError):
        _construct("AG3", proof_version=bad_version)


def test_parser_rejects_invalid_proof_version_boolean_true() -> None:
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", proof_version=True)))


def test_parser_rejects_invalid_proof_version_boolean_false() -> None:
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", proof_version=False)))


def test_constructor_accepts_the_one_supported_version() -> None:
    proof = _construct("AG3", proof_version=1)
    assert proof.proof_version == 1


# ═══════════════════════════════════════════════════════════════════════════
# Constructor-domain hardening -- other structural invariants (governing
# prompt item 105)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "overrides",
    [
        {"repository_id": "not-a-uuid"},
        {"repository_id": ""},
        {"decision_record_digest": "not-a-digest"},
        {"decision_record_digest": "a" * 63},
        {"binding_digest": "not-a-digest"},
        {"principal_id": ""},
        {"signer_key_id": ""},
        {"provider_profile": ""},
        {"decision_record_id": ""},
        {"binding_id": ""},
        {"issued_at": "not-a-timestamp"},
        {"issued_at": "2026-01-01T00:00:00.000"},
    ],
    ids=lambda v: str(v) if isinstance(v, dict) else "",
)
def test_constructor_rejects_invalid_common_fields(overrides: dict) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _construct("AG3", **overrides)


def test_constructor_rejects_invalid_ag3_commit_sha() -> None:
    with pytest.raises(InvalidProofSchemaError):
        Ag3OperationReference(job_id="job-1", original_commit_sha="not-a-sha")


def test_constructor_rejects_empty_ag3_job_id() -> None:
    with pytest.raises(InvalidProofSchemaError):
        Ag3OperationReference(job_id="", original_commit_sha="c" * 40)


def test_constructor_rejects_empty_ag5_per_id() -> None:
    with pytest.raises(InvalidProofSchemaError):
        Ag5OperationReference(per_id="", ecp_id="ecp-1")


def test_constructor_rejects_empty_ag5_ecp_id() -> None:
    with pytest.raises(InvalidProofSchemaError):
        Ag5OperationReference(per_id="per-1", ecp_id="")


def test_constructor_rejects_ag3_family_with_ag5_reference() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _construct("AG3", operation_reference=Ag5OperationReference(per_id="p", ecp_id="e"))


def test_constructor_rejects_ag5_family_with_ag3_reference() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _construct("AG5", operation_reference=Ag3OperationReference(job_id="j", original_commit_sha="c" * 40))


def test_constructor_rejects_unknown_rollback_site_string() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _construct("AG3", rollback_site="AG7")


def test_constructor_accepts_raw_rollback_site_string_and_normalizes() -> None:
    """A direct caller may pass the same raw string the JSON parser
    would ('AG3'/'AG5') -- accepted, and normalized to the `RollbackSite`
    enum member, matching parser output exactly."""

    proof = _construct("AG3", rollback_site="AG3")
    assert proof.rollback_site is RollbackSite.AG3


# ═══════════════════════════════════════════════════════════════════════════
# Parser/constructor equivalence matrix (governing prompt items 29-44,
# 80, 106)
# ═══════════════════════════════════════════════════════════════════════════


_EQUIVALENCE_CASES = {
    "invalid_repository_id": {"repository_id": "not-a-uuid"},
    "invalid_decision_digest": {"decision_record_digest": "not-a-digest"},
    "invalid_binding_digest": {"binding_digest": "not-a-digest"},
    "empty_principal": {"principal_id": ""},
    "empty_signer": {"signer_key_id": ""},
    "empty_provider_profile": {"provider_profile": ""},
    "empty_decision_id": {"decision_record_id": ""},
    "empty_binding_id": {"binding_id": ""},
    "malformed_timestamp": {"issued_at": "garbage"},
    "naive_timestamp": {"issued_at": "2026-01-01T00:00:00.000"},
    "submillisecond_timestamp": {"issued_at": "2026-01-01T00:00:00.0005Z"},
    "unsupported_version": {"proof_version": 2},
    "boolean_version_true": {"proof_version": True},
    "boolean_version_false": {"proof_version": False},
}


@pytest.mark.parametrize("case", sorted(_EQUIVALENCE_CASES), ids=sorted(_EQUIVALENCE_CASES))
def test_parser_and_constructor_equivalence_matrix(case: str) -> None:
    overrides = _EQUIVALENCE_CASES[case]
    doc = _valid_document("AG3", **overrides)
    with pytest.raises(Exception) as parser_exc_info:
        parse_hatp_proof(json.dumps(doc))
    with pytest.raises(Exception) as ctor_exc_info:
        _construct("AG3", **overrides)
    assert type(parser_exc_info.value) is type(ctor_exc_info.value)


@pytest.mark.parametrize("case", sorted(_EQUIVALENCE_CASES), ids=sorted(_EQUIVALENCE_CASES))
def test_ag5_parser_and_constructor_equivalence_matrix(case: str) -> None:
    overrides = _EQUIVALENCE_CASES[case]
    doc = _valid_document("AG5", **overrides)
    with pytest.raises(Exception) as parser_exc_info:
        parse_hatp_proof(json.dumps(doc))
    with pytest.raises(Exception) as ctor_exc_info:
        _construct("AG5", **overrides)
    assert type(parser_exc_info.value) is type(ctor_exc_info.value)


# ═══════════════════════════════════════════════════════════════════════════
# Positive controls (governing prompt items 81-82): valid construction
# and parsing must still succeed for both families.
# ═══════════════════════════════════════════════════════════════════════════


def test_positive_control_direct_construction_ag3() -> None:
    proof = _construct("AG3")
    assert proof.rollback_site is RollbackSite.AG3
    assert isinstance(proof.operation_reference, Ag3OperationReference)


def test_positive_control_direct_construction_ag5() -> None:
    proof = _construct("AG5")
    assert proof.rollback_site is RollbackSite.AG5
    assert isinstance(proof.operation_reference, Ag5OperationReference)


def test_positive_control_parser_ag3() -> None:
    proof = parse_hatp_proof(json.dumps(_valid_document("AG3")))
    assert proof.rollback_site is RollbackSite.AG3


def test_positive_control_parser_ag5() -> None:
    proof = parse_hatp_proof(json.dumps(_valid_document("AG5")))
    assert proof.rollback_site is RollbackSite.AG5


# ═══════════════════════════════════════════════════════════════════════════
# Round trip after constructor (governing prompt item 83)
# ═══════════════════════════════════════════════════════════════════════════


def test_round_trip_after_direct_constructor_ag3() -> None:
    proof = _construct("AG3")
    document = hatp_proof_to_document(proof)
    reparsed = parse_hatp_proof(json.dumps(document))
    assert reparsed == proof
    assert canonicalize_hatp_proof_payload(reparsed) == canonicalize_hatp_proof_payload(proof)


def test_round_trip_after_direct_constructor_ag5() -> None:
    proof = _construct("AG5")
    document = hatp_proof_to_document(proof)
    reparsed = parse_hatp_proof(json.dumps(document))
    assert reparsed == proof
    assert canonicalize_hatp_proof_payload(reparsed) == canonicalize_hatp_proof_payload(proof)


# ═══════════════════════════════════════════════════════════════════════════
# Golden vector preservation (governing prompt item 56): the repair must
# not have changed the canonical millisecond-timestamp representation,
# so the pre-existing 149O.1G golden digests are unaffected.
# ═══════════════════════════════════════════════════════════════════════════

_FIXED_REPO_ID = "11111111-1111-4111-8111-111111111111"

_AG3_GOLDEN_DOC = {
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

_AG5_GOLDEN_DOC = {
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


def test_ag3_golden_digest_unchanged_by_repair() -> None:
    """Cross-checked directly against `test_hatp_canonical_serialization.
    py`'s own `_AG3_GOLDEN_BYTES` constant (independently re-verified,
    not merely copied) -- confirms the millisecond-precision canonical
    timestamp format, and therefore this golden digest, is byte-
    unchanged by the 149O.1H.1 repair."""

    proof = parse_hatp_proof(json.dumps(_AG3_GOLDEN_DOC))
    assert digest_hatp_proof_payload(proof) == "bafc5bc9bf7865652be0dcdb47ca2906666d43fe963e7da7f593bac201efdc83"


def test_ag5_golden_digest_unchanged_by_repair() -> None:
    proof = parse_hatp_proof(json.dumps(_AG5_GOLDEN_DOC))
    assert digest_hatp_proof_payload(proof) == "480422914a8a8e90acf8ee1c4ed4dc0adb6b0a3ef294266bb2fcf8a479b6aeaf"


# ═══════════════════════════════════════════════════════════════════════════
# Immutability / frozen-model regression (governing prompt item 46)
# ═══════════════════════════════════════════════════════════════════════════


def test_proof_still_frozen_after_hardening() -> None:
    from dataclasses import FrozenInstanceError

    proof = _construct("AG3")
    with pytest.raises(FrozenInstanceError):
        proof.principal_id = "mallory"  # type: ignore[misc]


def test_operation_references_still_frozen_after_hardening() -> None:
    from dataclasses import FrozenInstanceError

    op3 = Ag3OperationReference(job_id="j", original_commit_sha="c" * 40)
    with pytest.raises(FrozenInstanceError):
        op3.job_id = "hacked"  # type: ignore[misc]
    op5 = Ag5OperationReference(per_id="p", ecp_id="e")
    with pytest.raises(FrozenInstanceError):
        op5.per_id = "hacked"  # type: ignore[misc]
