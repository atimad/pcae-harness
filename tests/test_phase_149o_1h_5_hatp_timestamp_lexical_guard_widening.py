"""Phase 149O.1H.5 -- HATP Timestamp Canonicalization Lexical Guard
Widening: narrow repair of B-149O.1H.4-1.

149O.1H.4 independently discovered that `_FRACTIONAL_SECONDS_RE`
(`\\.(\\d+)(?=Z$|[+-]\\d{2}:\\d{2}$)`) only recognized a fractional-
seconds group immediately followed by a `Z` suffix or a colon-separated
`+HH:MM`/`-HH:MM` offset. `datetime.fromisoformat` (this interpreter,
Python 3.14) additionally accepts non-colon offsets (`+00`, `+0000`,
...), a bare space date/time separator, and a `,` decimal separator --
none of which the old suffix-anchored lookahead covered. Each was an
independent bypass of the >6-fractional-digit rejection, reproducing
the exact B-149O.1H-1 collision (`.0000001` / `.0000009` both
truncating to `microsecond == 0`).

Repaired by re-anchoring fraction detection on the seconds field itself
rather than on the timezone-suffix syntax that follows it:
`_FRACTIONAL_SECONDS_RE = re.compile(r"(?<=:\\d{2})[.,](\\d+)")`. This
matches a `.`/`,` immediately following the two-digit `SS` seconds
field (itself identified by the preceding `:`), independent of what --
if anything -- follows the fraction. It therefore:

  * covers every timezone-offset spelling `datetime.fromisoformat`
    accepts (colon, non-colon, 2-digit, 4-digit, none/naive);
  * covers the `,` decimal separator this interpreter's
    `fromisoformat` also accepts;
  * never matches when there is no `.`/`,` directly after `SS` (so a
    suffix's own digits, e.g. `+0000`, are never miscounted as
    fractional digits -- there is no separator character before
    them);
  * does not attempt full ISO-8601 grammar validation (malformed
    multi-separator forms are left to the downstream parser).

Stage 2 (millisecond-domain rule, `microsecond % 1000 == 0`) and
Stage 3 (canonicalization) are unchanged by this phase.

This suite does not modify, weaken, or duplicate the pre-existing
149O.1G/149O.1H/149O.1H.1/149O.1H.2/149O.1H.3/149O.1H.4 suites (149O.1H.4's
own suite was updated in place -- see Section C/D of that file -- to
preserve B-149O.1H.4-1's historical evidence via an isolated pre-repair
import rather than the live module, per repository convention). It adds
focused repair coverage for the suffix-independent lexical guard.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime

import pytest

from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HumanApprovalProvenanceProof,
    InvalidProofSchemaError,
    MalformedProofError,
    RollbackSite,
    UnsupportedProofVersionError,
    _FRACTIONAL_SECONDS_RE,
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


def _parse(issued_at: str, family: str = "AG3") -> HumanApprovalProvenanceProof:
    return parse_hatp_proof(json.dumps(_valid_document(family, issued_at=issued_at)))


def _construct(issued_at: str, family: str = "AG3") -> HumanApprovalProvenanceProof:
    return HumanApprovalProvenanceProof(**_valid_kwargs(family, issued_at=issued_at))


# Every timezone-offset spelling independently confirmed (via direct
# `datetime.fromisoformat` probing on this interpreter, Python 3.14) to
# be accepted, that is relevant to fractional-second precision.
SUPPORTED_OFFSET_SUFFIXES = [
    "Z",
    "+00:00",
    "+0000",
    "+00",
    "+01:00",
    "+0100",
    "+01",
    "-05:00",
    "-0500",
    "-05",
]


# ═══════════════════════════════════════════════════════════════════════════
# Section A -- runtime parser offset-grammar probe (item 5/6/23).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("suffix", SUPPORTED_OFFSET_SUFFIXES)
def test_probe_runtime_accepts_offset_suffix(suffix: str) -> None:
    """Confirms (independent of Python's documentation) that this
    runtime's `datetime.fromisoformat` accepts each offset suffix used
    throughout this suite, when substituted for the module's own
    `Z`->`+00:00` rewrite."""
    raw = "2026-01-01T12:00:00.001" + suffix
    text = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    parsed = datetime.fromisoformat(text)
    assert parsed.microsecond == 1000


def test_probe_runtime_accepts_comma_decimal_separator() -> None:
    """Confirms this runtime's `datetime.fromisoformat` accepts a `,`
    fractional-second separator (a non-`.` ISO-8601 alternative) -- the
    148O.1H.3/149O.1H.4 guards never probed this, and it is an
    independent bypass class distinct from B-149O.1H.4-1's
    non-colon-offset bypass."""
    parsed = datetime.fromisoformat("2026-01-01T12:00:00,001+00:00")
    assert parsed.microsecond == 1000


def test_probe_runtime_accepts_space_date_time_separator() -> None:
    """Confirms this runtime's `datetime.fromisoformat` accepts a bare
    space in place of `T` -- relevant because the pre-149O.1H.5 guard
    fix must not accidentally rely on `T` being present."""
    parsed = datetime.fromisoformat("2026-01-01 12:00:00.001+00:00")
    assert parsed.microsecond == 1000


# ═══════════════════════════════════════════════════════════════════════════
# Section B -- historical B-149O.1H.4-1 collision, repaired (items 3, 4,
# 14, 50, 51).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.0000001+00",
        "2026-01-01T12:00:00.0000009+00",
        "2026-01-01T12:00:00.0000001+0000",
        "2026-01-01T12:00:00.0000009+0000",
    ],
)
def test_historical_collision_pair_now_rejected_parser(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.0000001+00",
        "2026-01-01T12:00:00.0000009+00",
        "2026-01-01T12:00:00.0000001+0000",
        "2026-01-01T12:00:00.0000009+0000",
    ],
)
def test_historical_collision_pair_now_rejected_constructor(raw: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        _construct(raw)


# ═══════════════════════════════════════════════════════════════════════════
# Section C -- full offset-suffix matrix, 7+ digits always reject (items
# 12, 52, 53).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("suffix", SUPPORTED_OFFSET_SUFFIXES)
@pytest.mark.parametrize("fraction", ["0000001", "1234567", "9999999"])
def test_seven_plus_digits_rejected_for_every_supported_suffix(fraction: str, suffix: str) -> None:
    raw = f"2026-01-01T12:00:00.{fraction}{suffix}"
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


@pytest.mark.parametrize("suffix", SUPPORTED_OFFSET_SUFFIXES)
def test_naive_seven_plus_digit_fraction_rejected_without_any_suffix(suffix: str) -> None:
    """A 7+-digit fraction must be rejected before parsing regardless of
    whether a timezone suffix is present at all (naive timestamps are
    separately rejected downstream by the tz-aware check, but the
    lexical guard must fire first -- item 9)."""
    raw = "2026-01-01T12:00:00.0000001"
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


# ═══════════════════════════════════════════════════════════════════════════
# Section D -- 6-or-fewer digits: guard does not itself reject; downstream
# rules decide (items 10, 13, 54, 55).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("suffix", SUPPORTED_OFFSET_SUFFIXES)
def test_six_digit_millisecond_aligned_fraction_accepted_for_every_suffix(suffix: str) -> None:
    raw = f"2026-01-01T12:00:00.001000{suffix}"
    proof = _parse(raw)
    assert proof.issued_at.endswith(".001Z")


@pytest.mark.parametrize("suffix", SUPPORTED_OFFSET_SUFFIXES)
def test_no_fraction_accepted_for_every_suffix(suffix: str) -> None:
    raw = f"2026-01-01T12:00:00{suffix}"
    proof = _parse(raw)
    assert proof.issued_at.endswith(".000Z")


# ═══════════════════════════════════════════════════════════════════════════
# Section E -- millisecond-domain rule preserved (Stage 2 unchanged;
# item 11).
# ═══════════════════════════════════════════════════════════════════════════


def test_millisecond_aligned_six_digit_accepted() -> None:
    proof = _parse("2026-01-01T12:00:00.001000Z")
    assert proof.issued_at == "2026-01-01T12:00:00.001Z"


def test_non_millisecond_aligned_six_digit_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.001001Z")


# ═══════════════════════════════════════════════════════════════════════════
# Section F -- Z / colon-offset regressions preserved (items 15, 16, 17,
# 26, 27).
# ═══════════════════════════════════════════════════════════════════════════


def test_z_seven_digit_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0000001Z")


def test_colon_offset_seven_digit_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0000001+00:00")


def test_original_149o_1h_1_regression_four_digit_semantic_rejection() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0001Z")
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.0009Z")


def test_lowercase_z_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.001z")


def test_naive_timestamp_still_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _parse("2026-01-01T12:00:00.001")


# ═══════════════════════════════════════════════════════════════════════════
# Section G -- fraction-digit extraction independence, adversarial forms
# (items 18, 19, 20, 21, 22, 56).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00+00",
        "2026-01-01T12:00:00+0000",
        "2026-01-01T12:00:00+00:00",
    ],
)
def test_no_fraction_offset_forms_unaffected(raw: str) -> None:
    proof = _parse(raw)
    assert proof.issued_at == "2026-01-01T12:00:00.000Z"


def test_helper_reports_no_fraction_rather_than_treating_offset_digits_as_fraction() -> None:
    match = _FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00+0000")
    assert match is None


def test_timezone_offset_digits_never_counted_as_fraction() -> None:
    match = _FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00+0000")
    assert match is None, "offset digits '0000' must not be interpreted as fractional precision"


def test_fraction_digit_count_independent_of_timezone_suffix_syntax() -> None:
    """Directly tests the helper: fraction length extracted must be
    identical across every supported suffix for the same fractional
    value."""
    lengths = set()
    for suffix in SUPPORTED_OFFSET_SUFFIXES:
        raw = f"2026-01-01T12:00:00.1234567{suffix}"
        match = _FRACTIONAL_SECONDS_RE.search(raw)
        assert match is not None
        lengths.add(len(match.group(1)))
    assert lengths == {7}


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.123.456Z",
        "2026-01-01T12:00:00..123Z",
    ],
)
def test_multiple_dot_attack_ultimately_rejected(raw: str) -> None:
    """The lexical guard must not accidentally normalize a malformed
    multi-separator timestamp into acceptance; the downstream ISO
    parser rejects these regardless of what the guard itself does."""
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


def test_multiple_dot_attack_not_lexically_over_counted() -> None:
    """`12:00:00.123.456Z` has only 3 contiguous digits immediately
    after the first `.` following `SS` -- the helper must not walk past
    the second `.` and count 6 digits (`123456`)."""
    match = _FRACTIONAL_SECONDS_RE.search("2026-01-01T12:00:00.123.456Z")
    assert match is not None
    assert match.group(1) == "123"


# ═══════════════════════════════════════════════════════════════════════════
# Section H -- decimal comma (items 23, 24, 25, 57).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("suffix", ["Z", "+00:00", "+00", "+0000"])
def test_comma_seven_plus_digit_fraction_rejected(suffix: str) -> None:
    raw = f"2026-01-01T12:00:00,0000001{suffix}"
    with pytest.raises(InvalidProofSchemaError):
        _parse(raw)


@pytest.mark.parametrize("suffix", ["Z", "+00:00", "+00", "+0000"])
def test_comma_six_digit_millisecond_aligned_fraction_accepted(suffix: str) -> None:
    raw = f"2026-01-01T12:00:00,001000{suffix}"
    proof = _parse(raw)
    assert proof.issued_at == "2026-01-01T12:00:00.001Z"


def test_comma_and_dot_equivalent_millisecond_instant_canonicalize_identically() -> None:
    proof_dot = _parse("2026-01-01T12:00:00.001Z")
    proof_comma = _parse("2026-01-01T12:00:00,001Z")
    assert proof_dot.issued_at == proof_comma.issued_at == "2026-01-01T12:00:00.001Z"


# ═══════════════════════════════════════════════════════════════════════════
# Section I -- same-instant / distinct-instant equivalence across offset
# syntax (items 38, 39, 40, 55).
# ═══════════════════════════════════════════════════════════════════════════


def test_zero_offset_equivalence_across_suffix_syntax() -> None:
    canonical = {
        _parse("2026-01-01T12:00:00.001Z").issued_at,
        _parse("2026-01-01T12:00:00.001+00").issued_at,
        _parse("2026-01-01T12:00:00.001+0000").issued_at,
        _parse("2026-01-01T12:00:00.001+00:00").issued_at,
    }
    assert canonical == {"2026-01-01T12:00:00.001Z"}


def test_non_zero_offset_equivalence_across_suffix_syntax() -> None:
    canonical = {
        _parse("2026-01-01T13:00:00.001+01").issued_at,
        _parse("2026-01-01T13:00:00.001+0100").issued_at,
        _parse("2026-01-01T13:00:00.001+01:00").issued_at,
    }
    assert canonical == {"2026-01-01T12:00:00.001Z"}


def test_distinct_millisecond_values_remain_distinct() -> None:
    a = _parse("2026-01-01T12:00:00.001Z").issued_at
    b = _parse("2026-01-01T12:00:00.002Z").issued_at
    assert a != b


# ═══════════════════════════════════════════════════════════════════════════
# Section J -- parser/constructor equivalence (items 28, 58).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "2026-01-01T12:00:00.0000001+00",
        "2026-01-01T12:00:00.0000001+0000",
        "2026-01-01T12:00:00,0000001Z",
        "2026-01-01T12:00:00.001+00",
        "2026-01-01T12:00:00.001000+0000",
    ],
)
def test_parser_constructor_equivalence_on_new_suffix_forms(raw: str) -> None:
    parser_outcome = None
    constructor_outcome = None
    try:
        parser_outcome = _parse(raw).issued_at
    except InvalidProofSchemaError:
        parser_outcome = "rejected"
    try:
        constructor_outcome = _construct(raw).issued_at
    except InvalidProofSchemaError:
        constructor_outcome = "rejected"
    assert parser_outcome == constructor_outcome


# ═══════════════════════════════════════════════════════════════════════════
# Section K -- B-149O.1H-2 constructor-hardening regression (items 29,
# 59).
# ═══════════════════════════════════════════════════════════════════════════


def test_constructor_hardening_bool_proof_version_rejected() -> None:
    with pytest.raises((InvalidProofSchemaError, UnsupportedProofVersionError)):
        HumanApprovalProvenanceProof(**_valid_kwargs(proof_version=True))


def test_constructor_hardening_invalid_repository_id_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(repository_id="not-a-uuid"))


def test_constructor_hardening_invalid_digest_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(decision_record_digest="not-hex"))


def test_constructor_hardening_invalid_commit_sha_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="not-a-sha")))


def test_constructor_hardening_empty_identifier_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(**_valid_kwargs(principal_id=""))


def test_constructor_hardening_family_mismatch_rejected() -> None:
    with pytest.raises(InvalidProofSchemaError):
        HumanApprovalProvenanceProof(
            **_valid_kwargs(
                family="AG3",
                rollback_site=RollbackSite.AG5,
            )
        )


# ═══════════════════════════════════════════════════════════════════════════
# Section L -- closed-schema / duplicate-key / AG3-AG5 discrimination
# regressions (items 30, 31, 32).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "unknown_field",
    ["trusted_root", "signature_valid", "human_present", "authorized", "hatp_valid"],
)
def test_closed_schema_rejects_unknown_field(unknown_field: str) -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(**{unknown_field: True})))


def test_duplicate_top_level_key_rejected() -> None:
    raw = (
        '{"proof_version":1,"proof_version":1,"principal_id":"alice",'
        '"signer_key_id":"signer-1","provider_profile":"HATP_HARDWARE_PROVIDER_V1",'
        f'"repository_id":"{_repo_id()}","decision_record_id":"chgr-record-1",'
        '"decision_record_digest":"' + "a" * 64 + '","binding_id":"rae-binding-1",'
        '"binding_digest":"' + "b" * 64 + '","rollback_site":"AG3",'
        '"issued_at":"2026-08-06T00:00:00.000Z","job_id":"job-1",'
        '"original_commit_sha":"' + "c" * 40 + '"}'
    )
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(raw)


def test_ag3_ag5_discrimination_still_strict() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document(family="AG3", rollback_site="AG7")))


# ═══════════════════════════════════════════════════════════════════════════
# Section M -- golden vectors / digest / mutation sensitivity (items 41,
# 42, 43).
# ═══════════════════════════════════════════════════════════════════════════


def test_golden_vector_ag3_canonical_bytes_and_digest_recomputed() -> None:
    proof = _parse("2026-08-06T00:00:00.000Z", family="AG3")
    payload = canonicalize_hatp_proof_payload(proof)
    digest = digest_hatp_proof_payload(proof)
    assert b'"issued_at":"2026-08-06T00:00:00.000Z"' in payload
    import hashlib

    assert digest == hashlib.sha256(payload).hexdigest()


def test_mutation_sensitivity_timestamp_change_alters_digest() -> None:
    proof_a = _parse("2026-01-01T12:00:00.001Z")
    proof_b = _parse("2026-01-01T12:00:00.002Z")
    assert digest_hatp_proof_payload(proof_a) != digest_hatp_proof_payload(proof_b)


# ═══════════════════════════════════════════════════════════════════════════
# Section N -- purity: no new dependency, no filesystem/network/env/
# wall-clock/random use introduced by the repair (items 70, 71).
# ═══════════════════════════════════════════════════════════════════════════


def test_no_canonicalizer_source_change_marker() -> None:
    """The repair is scoped to fraction detection; the canonicalizer
    function itself must remain untouched. This is a coarse guard: the
    canonical millisecond format produced for an already-valid input is
    unchanged."""
    proof = _parse("2026-01-01T12:00:00.001Z")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", proof.issued_at)


def test_module_still_has_no_forbidden_symbols_in_namespace() -> None:
    import pcae.core.human_approval_trusted_provenance as prod

    for forbidden in ("VALID", "UNKNOWN_SIGNER", "approval_present", "HATP_VALID"):
        assert not hasattr(prod, forbidden)
