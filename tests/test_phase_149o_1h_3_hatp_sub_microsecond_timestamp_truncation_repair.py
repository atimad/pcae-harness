"""Phase 149O.1H.3 -- HATP Sub-Microsecond Timestamp Truncation Narrow
Repair: authoritative post-repair regression suite.

Repairs the narrow basis on which Phase 149O.1H.2 independently reopened
B-149O.1H-1: `datetime.fromisoformat` silently truncates (rather than
rejecting) any ISO-8601 fractional-second string carrying more than six
digits, so two distinct raw `issued_at` strings agreeing on their first
six fractional digits but differing beyond the sixth (e.g. `.0000001Z`
vs `.0000009Z`) both parsed successfully and canonicalized identically.

Repaired by validating raw lexical fractional-second precision *before*
`datetime.fromisoformat` ever runs: any `issued_at` whose fractional-
second group (immediately preceding its `Z`/offset suffix) carries more
than 6 digits is rejected outright (`InvalidProofSchemaError`), via a
new `_reject_excess_fractional_precision` helper called from
`_parse_iso_timestamp`, shared by both the parser
(`_build_proof_from_document` -> `_require_issued_at`) and every
model's `__post_init__` (`_require_issued_at`, unchanged call site) --
no second, drifting timestamp-validation path.

The already-repaired millisecond-domain rule
(`microsecond % 1000 == 0`, Phase 149O.1H.1) is unchanged: a <= 6-digit
fractional value that is lexically representable may still be rejected
by that existing semantic rule. This suite exercises both layers
together and independently.

This suite does not modify, weaken, or duplicate the pre-existing
149O.1G/149O.1H/149O.1H.1/149O.1H.2 suites; it adds focused repair
coverage for the new lexical-precision boundary.
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
    RollbackSite,
    canonicalize_hatp_proof_payload,
    digest_hatp_proof_payload,
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


def _parse(issued_at: str) -> HumanApprovalProvenanceProof:
    return parse_hatp_proof(json.dumps(_valid_document(issued_at=issued_at)))


def _construct(issued_at: str) -> HumanApprovalProvenanceProof:
    return HumanApprovalProvenanceProof(**_valid_kwargs(issued_at=issued_at))


# ═══════════════════════════════════════════════════════════════════════════
# 1. Historical defect pair -- must now be rejected, both paths.
# ═══════════════════════════════════════════════════════════════════════════


def test_historical_sub_microsecond_collision_pair_now_rejected_parser() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0000001Z")
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0000009Z")


def test_historical_sub_microsecond_collision_pair_now_rejected_constructor() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _construct("2026-01-01T12:00:00.0000001Z")
    with pytest.raises(InvalidProofSchemaError):
        _construct("2026-01-01T12:00:00.0000009Z")


# ═══════════════════════════════════════════════════════════════════════════
# 2. Original B-149O.1H-1 millisecond-domain collision pair -- must
#    remain rejected (repair must not weaken 149O.1H.1's fix).
# ═══════════════════════════════════════════════════════════════════════════


def test_original_millisecond_collision_pair_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0001Z")
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0009Z")


# ═══════════════════════════════════════════════════════════════════════════
# 3. Fractional-digit-length matrix: 0..9 and 12 digits.
#    > 6 digits must be rejected before lossy parsing; <= 6 digits
#    proceeds to the existing millisecond-domain rule.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("fraction", "expect_accepted"),
    [
        ("", True),  # 0 digits (no fractional part at all)
        ("0", True),  # 1 digit, .0 -> 0us, millisecond-aligned
        ("00", True),  # 2 digits
        ("000", True),  # 3 digits, exact millisecond form
        ("0000", True),  # 4 digits
        ("00000", True),  # 5 digits
        ("000000", True),  # 6 digits, exact microsecond form, 0us
        ("0000000", False),  # 7 digits -- lexically rejected
        ("00000000", False),  # 8 digits
        ("000000000000", False),  # 12 digits
    ],
)
def test_fractional_digit_length_matrix(fraction: str, expect_accepted: bool) -> None:
    raw = f"2026-01-01T12:00:00{'.' + fraction if fraction else ''}Z"
    if expect_accepted:
        proof = _parse(raw)
        assert proof.issued_at == "2026-01-01T12:00:00.000Z"
    else:
        with pytest.raises(InvalidProofSchemaError):
            _parse(raw)


# ═══════════════════════════════════════════════════════════════════════════
# 4. <= 6-digit fractional values: lexical guard must not itself reject
#    them; the pre-existing millisecond-domain rule decides admissibility.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("fraction", "millisecond_admissible"),
    [
        ("000000", True),
        ("000001", False),
        ("000999", False),
        ("001000", True),
        ("001001", False),
        ("123000", True),
        ("123456", False),
        ("999000", True),
        ("999999", False),
    ],
)
def test_six_digit_or_fewer_values_governed_by_millisecond_domain_rule(
    fraction: str, millisecond_admissible: bool
) -> None:
    raw = f"2026-01-01T12:00:00.{fraction}Z"
    if millisecond_admissible:
        proof = _parse(raw)
        expected_ms = int(fraction[:3]) if len(fraction) >= 3 else int(fraction.ljust(3, "0"))
        assert proof.issued_at == f"2026-01-01T12:00:00.{expected_ms:03d}Z"
    else:
        with pytest.raises(InvalidProofSchemaError):
            _parse(raw)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Fewer-than-six-digit values that legitimately represent the same
#    millisecond instant must canonicalize identically.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("fraction", [".123", ".1230", ".12300", ".123000"])
def test_short_fractional_forms_of_same_instant_canonicalize_identically(fraction: str) -> None:
    proof = _parse(f"2026-01-01T12:00:00{fraction}Z")
    assert proof.issued_at == "2026-01-01T12:00:00.123Z"


# ═══════════════════════════════════════════════════════════════════════════
# 6. Seven-or-more-digit collision matrix -- all pairs must be rejected
#    lexically, not merely collide after lossy parsing.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("fraction_a", "fraction_b"),
    [
        ("0000001", "0000009"),
        ("0010001", "0010009"),
        ("1234561", "1234569"),
        ("9999991", "9999999"),
    ],
)
def test_seven_plus_digit_collision_matrix_all_rejected(fraction_a: str, fraction_b: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse(f"2026-01-01T12:00:00.{fraction_a}Z")
    with pytest.raises(InvalidProofSchemaError):
        _parse(f"2026-01-01T12:00:00.{fraction_b}Z")


# ═══════════════════════════════════════════════════════════════════════════
# 7. Timezone-suffix coverage: offset forms must also be rejected, not
#    only the `Z` form.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T13:00:00.0000001+01:00",
        "2026-01-01T07:00:00.1234567-05:00",
        "2026-01-01T12:00:00.0000001+00:00",
    ],
)
def test_offset_forms_with_excess_precision_rejected(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


# ═══════════════════════════════════════════════════════════════════════════
# 8. Timezone equivalence for accepted values must remain intact.
# ═══════════════════════════════════════════════════════════════════════════


def test_timezone_equivalence_preserved_for_accepted_values() -> None:
    a = _parse("2026-01-01T12:00:00.001Z")
    b = _parse("2026-01-01T13:00:00.001+01:00")
    c = _parse("2026-01-01T07:00:00.001-05:00")
    d = _parse("2026-01-01T12:00:00.002Z")
    assert a.issued_at == b.issued_at == c.issued_at
    assert a.issued_at != d.issued_at


# ═══════════════════════════════════════════════════════════════════════════
# 9. Parser/constructor equivalence across the whole precision matrix.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00Z",
        "2026-01-01T12:00:00.001Z",
        "2026-01-01T12:00:00.000001Z",
        "2026-01-01T12:00:00.0000001Z",
        "2026-01-01T12:00:00.1234567Z",
        "2026-01-01T12:00:00.123456789Z",
    ],
)
def test_parser_constructor_equivalence_across_precision_matrix(raw: str) -> None:
    parser_outcome = None
    constructor_outcome = None
    try:
        parser_outcome = _parse(raw).issued_at
    except InvalidProofSchemaError:
        parser_outcome = "REJECTED"
    try:
        constructor_outcome = _construct(raw).issued_at
    except InvalidProofSchemaError:
        constructor_outcome = "REJECTED"
    assert parser_outcome == constructor_outcome


# ═══════════════════════════════════════════════════════════════════════════
# 10. Canonical-bytes / digest stability for already-accepted millisecond
#     fixtures (repair must not touch canonical rendering for valid input).
# ═══════════════════════════════════════════════════════════════════════════


def test_canonical_bytes_stable_for_accepted_millisecond_fixture() -> None:
    doc = _valid_document(issued_at="2026-03-04T05:06:07.008Z")
    proof_a = parse_hatp_proof(json.dumps(doc))
    proof_b = parse_hatp_proof(json.dumps(doc))
    payload = canonicalize_hatp_proof_payload(proof_a)
    assert b'"issued_at":"2026-03-04T05:06:07.008Z"' in payload
    assert digest_hatp_proof_payload(proof_a) == digest_hatp_proof_payload(proof_b)


# ═══════════════════════════════════════════════════════════════════════════
# 11. Injectivity: a bounded set of distinct accepted millisecond
#     instants must produce zero canonical collisions.
# ═══════════════════════════════════════════════════════════════════════════


def test_injectivity_over_accepted_millisecond_instants() -> None:
    canon = {_parse(f"2026-01-01T12:00:00.{ms:03d}Z").issued_at for ms in range(0, 1000, 7)}
    assert len(canon) == len(range(0, 1000, 7))


# ═══════════════════════════════════════════════════════════════════════════
# 12. Raw-losslessness: no accepted raw timestamp discards a non-zero
#     fractional digit before the semantic-domain check.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00Z",
        "2026-01-01T12:00:00.000Z",
        "2026-01-01T12:00:00.001Z",
        "2026-01-01T12:00:00.100Z",
        "2026-01-01T12:00:00.999Z",
        "2026-01-01T12:00:00.000000Z",
        "2026-01-01T12:00:00.001000Z",
    ],
)
def test_accepted_values_lose_no_significant_fractional_digit(raw: str) -> None:
    proof = _parse(raw)
    # Reconstruct the millisecond value directly from the raw string and
    # compare against the canonical rendering -- if any significant digit
    # had been silently discarded, this would diverge.
    if "." in raw:
        frac = raw.split(".", 1)[1].rstrip("Z")
        ms = int(frac[:3].ljust(3, "0")) if frac else 0
    else:
        ms = 0
    assert proof.issued_at == f"2026-01-01T12:00:00.{ms:03d}Z"


# ═══════════════════════════════════════════════════════════════════════════
# 13. Regressions this phase must not disturb.
# ═══════════════════════════════════════════════════════════════════════════


def test_boolean_proof_version_still_rejected() -> None:
    from pcae.core.human_approval_trusted_provenance import UnsupportedProofVersionError

    true_kwargs = _valid_kwargs()
    true_kwargs["proof_version"] = True
    with pytest.raises(UnsupportedProofVersionError):
        HumanApprovalProvenanceProof(**true_kwargs)

    false_kwargs = _valid_kwargs()
    false_kwargs["proof_version"] = False
    with pytest.raises(UnsupportedProofVersionError):
        HumanApprovalProvenanceProof(**false_kwargs)


def test_invalid_repository_id_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(repository_id="not-a-uuid")))


def test_invalid_digest_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(decision_record_digest="not-hex")))
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(binding_digest="not-hex")))


def test_malformed_commit_sha_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", original_commit_sha="not-a-sha")))


def test_empty_identifier_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(principal_id="")))


def test_family_mismatch_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(
            **_valid_kwargs(
                "AG3",
                rollback_site=RollbackSite.AG5,
                operation_reference=Ag3OperationReference(job_id="j", original_commit_sha="c" * 40),
            )
        )


def test_closed_schema_unknown_field_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(extra_field="nope")))


def test_duplicate_json_key_still_rejected() -> None:
    from pcae.core.human_approval_trusted_provenance import MalformedProofError

    raw = (
        '{"proof_version": 1, "proof_version": 1, "principal_id": "alice", '
        '"signer_key_id": "signer-1", "provider_profile": "HATP_HARDWARE_PROVIDER_V1", '
        f'"repository_id": "{_repo_id()}", "decision_record_id": "chgr-record-1", '
        f'"decision_record_digest": "{"a" * 64}", "binding_id": "rae-binding-1", '
        f'"binding_digest": "{"b" * 64}", "rollback_site": "AG3", '
        '"issued_at": "2026-01-01T12:00:00.000Z", "job_id": "job-1", '
        f'"original_commit_sha": "{"c" * 40}"}}'
    )
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(raw)
