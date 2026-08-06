"""Phase 149O.1H -- HATP Proof Models + Canonical Serialization
Independent Verification (adversarial re-verification of Wave 3).

This suite does NOT accept the 149O.1G implementation report's claims.
Every assertion here is independently derived from HATP-001
(`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`,
HATP-REQ-067..077 + HATP-REQ-117) and from direct adversarial exercise
of the public surface of `pcae.core.human_approval_trusted_provenance`.
It imports the module under test but does not import or reuse the
149O.1G test files' fixtures, constants, or golden-vector values --
golden vectors here are independently recomputed from first principles
(sorted-key, compact-separator, `ensure_ascii=False` JSON + SHA-256) to
avoid the circularity of "verifying implementation output equals a
constant copied from the implementation's own test file".

Two BLOCKING findings are reproduced and asserted as *expected current
behavior* (not repaired -- 149O.1H is verification-only and MUST NOT
modify `human_approval_trusted_provenance.py`):

  * B-149O.1H-1 -- timestamp canonicalization is NOT injective over the
    accepted input domain: two distinct ISO-8601 instants that differ
    only below one millisecond (e.g. `.0001Z` vs `.0009Z`) both parse
    successfully and canonicalize to identical bytes/digest.
  * B-149O.1H-2 -- the public dataclass constructors enforce strictly
    less than the parser: `HumanApprovalProvenanceProof.__post_init__`
    only checks AG3/AG5 family-vs-operation-reference-type agreement.
    It performs no field-format validation, so direct construction with
    an invalid `repository_id`, invalid digest, unsupported/boolean
    `proof_version`, or a non-canonical `issued_at` string succeeds and
    survives canonicalization/digesting unchanged.

These tests assert the *current* (defective) behavior so that any
future repair phase has a red/green marker to flip, per governed-phase
convention of "record it, reproduce it, do NOT repair it".
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

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

REPO_ROOT = Path(__file__).resolve().parents[1]


# ── shared helpers (independent of the 149O.1G test files) ────────────────


def _valid_document(family: str = "AG3", **overrides: object) -> dict:
    doc: dict = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "key-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": str(uuid.uuid4()),
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


def _independent_canonical_bytes(document: dict) -> bytes:
    """Reconstruct canonical bytes independently: sorted keys, compact
    separators, UTF-8, no ASCII escaping -- derived from HATP-REQ-075's
    determinism requirement, not by calling the implementation's own
    `canonicalize_hatp_proof_payload`."""

    parts = []
    for key in sorted(document.keys()):
        parts.append(json.dumps(key) + ":" + json.dumps(document[key], ensure_ascii=False))
    return ("{" + ",".join(parts) + "}").encode("utf-8")


def _make_proof(family: str = "AG3", **kwargs: object) -> HumanApprovalProvenanceProof:
    common = dict(
        proof_version=1,
        principal_id="alice",
        signer_key_id="key-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=str(uuid.uuid4()),
        decision_record_id="dec-1",
        decision_record_digest="a" * 64,
        binding_id="bind-1",
        binding_digest="b" * 64,
        issued_at="2026-01-01T12:00:00.000Z",
    )
    if family == "AG3":
        common["rollback_site"] = RollbackSite.AG3
        common["operation_reference"] = Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40)
    else:
        common["rollback_site"] = RollbackSite.AG5
        common["operation_reference"] = Ag5OperationReference(per_id="per-1", ecp_id="ecp-1")
    common.update(kwargs)
    return HumanApprovalProvenanceProof(**common)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Required-field removal, independently, both families
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("field", sorted(_valid_document("AG3").keys()))
def test_ag3_required_field_removal_is_rejected(field: str) -> None:
    doc = _valid_document("AG3")
    del doc[field]
    with pytest.raises(HATPProofError):
        parse_hatp_proof(json.dumps(doc))


@pytest.mark.parametrize("field", sorted(_valid_document("AG5").keys()))
def test_ag5_required_field_removal_is_rejected(field: str) -> None:
    doc = _valid_document("AG5")
    del doc[field]
    with pytest.raises(HATPProofError):
        parse_hatp_proof(json.dumps(doc))


@pytest.mark.parametrize("field", sorted(_valid_document("AG3").keys()))
def test_ag3_null_field_is_rejected(field: str) -> None:
    doc = _valid_document("AG3")
    doc[field] = None
    with pytest.raises(HATPProofError):
        parse_hatp_proof(json.dumps(doc))


@pytest.mark.parametrize("field", sorted(_valid_document("AG5").keys()))
def test_ag5_null_field_is_rejected(field: str) -> None:
    doc = _valid_document("AG5")
    doc[field] = None
    with pytest.raises(HATPProofError):
        parse_hatp_proof(json.dumps(doc))


# ═══════════════════════════════════════════════════════════════════════════
# 2. Closed-schema / self-selected-trust / authority-boolean attacks
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "field",
    [
        "harmless_unknown",
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
    ],
)
def test_unknown_and_self_selected_trust_field_rejected(field: str) -> None:
    doc = _valid_document("AG3")
    doc[field] = True
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_wrong_family_fields_on_ag3_rejected() -> None:
    doc = _valid_document("AG3")
    doc["per_id"] = "x"
    doc["ecp_id"] = "y"
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


def test_wrong_family_fields_on_ag5_rejected() -> None:
    doc = _valid_document("AG5")
    doc["job_id"] = "x"
    doc["original_commit_sha"] = "c" * 40
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


# ═══════════════════════════════════════════════════════════════════════════
# 3. Proof version attacks (bool-is-int-subclass trap)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("version", [0, 2, -1, "1", 1.0, True, False, None])
def test_unsupported_proof_version_rejected(version: object) -> None:
    doc = _valid_document("AG3")
    doc["proof_version"] = version
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(json.dumps(doc))


def test_missing_proof_version_rejected() -> None:
    doc = _valid_document("AG3")
    del doc["proof_version"]
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(json.dumps(doc))


# ═══════════════════════════════════════════════════════════════════════════
# 4. Non-object top-level / NaN-Infinity
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("raw", ["[]", '"string"', "1", "true", "null"])
def test_non_object_top_level_rejected(raw: str) -> None:
    with pytest.raises(HATPProofError):
        parse_hatp_proof(raw)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_nan_infinity_proof_version_rejected(token: str) -> None:
    doc = _valid_document("AG3")
    raw = json.dumps(doc, separators=(",", ":")).replace('"proof_version":1', f'"proof_version":{token}')
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(raw)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Duplicate JSON keys -- top level and nested, recursively
# ═══════════════════════════════════════════════════════════════════════════


def test_duplicate_minimal_top_level_key_rejected() -> None:
    with pytest.raises(MalformedProofError):
        parse_hatp_proof('{"principal_id":"a","principal_id":"b"}')


@pytest.mark.parametrize(
    "field,value",
    [
        ("repository_id", str(uuid.uuid4())),
        ("decision_record_digest", "z" * 64),
        ("binding_digest", "z" * 64),
        ("rollback_site", "AG5"),
    ],
)
def test_duplicate_full_document_field_rejected(field: str, value: object) -> None:
    doc = _valid_document("AG3")
    raw = json.dumps(doc)[:-1] + f", {json.dumps(field)}: {json.dumps(value)}}}"
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(raw)


def test_duplicate_ag3_operation_field_rejected() -> None:
    doc = _valid_document("AG3")
    raw = json.dumps(doc)[:-1] + ', "job_id": "job-2"}'
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(raw)


def test_duplicate_ag5_operation_field_rejected() -> None:
    doc = _valid_document("AG5")
    raw = json.dumps(doc)[:-1] + ', "per_id": "per-2"}'
    with pytest.raises(MalformedProofError):
        parse_hatp_proof(raw)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Lexical field validation (independently derived accepted sets)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "value,should_pass",
    [
        ("a" * 64, True),
        ("A" * 64, False),
        ("a" * 63, False),
        ("a" * 65, False),
        ("g" * 64, False),
        ("sha256:" + "a" * 64, False),
    ],
)
def test_digest_lexical_validation(value: str, should_pass: bool) -> None:
    doc = _valid_document("AG3", decision_record_digest=value)
    if should_pass:
        parse_hatp_proof(json.dumps(doc))
    else:
        with pytest.raises(InvalidProofSchemaError):
            parse_hatp_proof(json.dumps(doc))


@pytest.mark.parametrize(
    "value,should_pass",
    [
        ("c" * 40, True),
        ("C" * 40, False),
        ("c" * 64, True),
        ("c" * 7, False),
        ("c" * 39, False),
        ("c" * 41, False),
        ("g" * 40, False),
    ],
)
def test_commit_sha_lexical_validation(value: str, should_pass: bool) -> None:
    doc = _valid_document("AG3", original_commit_sha=value)
    if should_pass:
        parse_hatp_proof(json.dumps(doc))
    else:
        with pytest.raises(InvalidProofSchemaError):
            parse_hatp_proof(json.dumps(doc))


def test_repository_id_uuid_validation_accepted_and_rejected_forms() -> None:
    u = uuid.uuid4()
    parse_hatp_proof(json.dumps(_valid_document("AG3", repository_id=str(u))))
    # NOTE (OBSERVATION, non-blocking): uppercase is accepted (not one
    # canonical form) because `is_valid_repository_instance_id` compares
    # `str(parsed) == value.lower()`. The accepted value is then stored
    # verbatim (not normalized), so an uppercase-vs-lowercase UUID for
    # the *same* repository canonicalizes to different bytes.
    parse_hatp_proof(json.dumps(_valid_document("AG3", repository_id=str(u).upper())))
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", repository_id="{" + str(u) + "}")))
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", repository_id=str(u).replace("-", ""))))
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", repository_id="0" * 8 + "-0000-0000-0000-" + "0" * 12)))


def test_uppercase_repository_id_not_normalized_to_one_canonical_form() -> None:
    """OBSERVATION / non-blocking: same semantic repository_id (case
    difference) canonicalizes to *different* bytes -- accepted-and-NOT-
    normalized, the failure mode explicitly warned about in the governing
    verification brief item 58-62 ("uppercase ... accepted-and-normalized
    (must be deterministic)")."""

    u = str(uuid.uuid4())
    p_lower = parse_hatp_proof(json.dumps(_valid_document("AG3", repository_id=u)))
    p_upper = parse_hatp_proof(json.dumps(_valid_document("AG3", repository_id=u.upper())))
    assert canonicalize_hatp_proof_payload(p_lower) != canonicalize_hatp_proof_payload(p_upper)


@pytest.mark.parametrize("value", [" ", "\t", "\n", " alice "])
def test_whitespace_identifiers_are_retained_verbatim_not_trimmed(value: str) -> None:
    """Whitespace-only/padded opaque identifiers are accepted (the
    module has no charset restriction beyond non-empty) and -- critically
    -- retained exactly, with no silent trimming that would change
    signed-payload semantics."""

    doc = _valid_document("AG3", principal_id=value)
    proof = parse_hatp_proof(json.dumps(doc))
    assert proof.principal_id == value


# ═══════════════════════════════════════════════════════════════════════════
# 7. Unicode canonicalization
# ═══════════════════════════════════════════════════════════════════════════


def test_unicode_bmp_and_non_bmp_round_trip_and_distinct_bytes() -> None:
    p_ascii = parse_hatp_proof(json.dumps(_valid_document("AG3", principal_id="alice")))
    p_bmp = parse_hatp_proof(json.dumps(_valid_document("AG3", principal_id="élodie")))
    p_emoji = parse_hatp_proof(json.dumps(_valid_document("AG3", principal_id="\U0001F600emoji")))
    b_ascii = canonicalize_hatp_proof_payload(p_ascii)
    b_bmp = canonicalize_hatp_proof_payload(p_bmp)
    b_emoji = canonicalize_hatp_proof_payload(p_emoji)
    assert b_ascii != b_bmp != b_emoji
    # ensure_ascii=False: canonical bytes contain literal UTF-8, not \uXXXX escapes
    assert b"\\u00e9" not in b_bmp
    assert "é".encode("utf-8") in b_bmp


def test_precomposed_vs_combining_unicode_forms_not_silently_collapsed() -> None:
    precomposed = "é"  # single codepoint e-acute
    combining = "é"  # 'e' + combining acute accent
    p1 = parse_hatp_proof(json.dumps(_valid_document("AG3", principal_id=precomposed)))
    p2 = parse_hatp_proof(json.dumps(_valid_document("AG3", principal_id=combining)))
    assert canonicalize_hatp_proof_payload(p1) != canonicalize_hatp_proof_payload(p2)


def test_lone_surrogate_fails_canonicalization_deterministically() -> None:
    """Python permits constructing a `str` containing an unpaired UTF-16
    surrogate. `json.loads` will happily parse `\\ud800` into such a
    string. UTF-8 has no representation for lone surrogates, so
    canonicalization (which encodes to UTF-8) must fail deterministically
    rather than produce inconsistent bytes."""

    doc = _valid_document("AG3", principal_id="\ud800")
    proof = parse_hatp_proof(json.dumps(doc))
    with pytest.raises(UnicodeEncodeError):
        canonicalize_hatp_proof_payload(proof)


# ═══════════════════════════════════════════════════════════════════════════
# 8. Determinism: key order, whitespace, JSON escape equivalence
# ═══════════════════════════════════════════════════════════════════════════


def test_key_order_independence() -> None:
    doc = _valid_document("AG3")
    reordered = dict(reversed(list(doc.items())))
    p1 = parse_hatp_proof(json.dumps(doc))
    p2 = parse_hatp_proof(json.dumps(reordered))
    assert canonicalize_hatp_proof_payload(p1) == canonicalize_hatp_proof_payload(p2)


def test_whitespace_independence() -> None:
    doc = _valid_document("AG3")
    compact = json.dumps(doc, separators=(",", ":"))
    pretty = json.dumps(doc, indent=4)
    p1 = parse_hatp_proof(compact)
    p2 = parse_hatp_proof(pretty)
    assert canonicalize_hatp_proof_payload(p1) == canonicalize_hatp_proof_payload(p2)


def test_json_escape_equivalence() -> None:
    doc = _valid_document("AG3", principal_id="a/b")
    raw_literal = json.dumps(doc)
    raw_escaped = raw_literal.replace("a/b", "a\\/b")
    p1 = parse_hatp_proof(raw_literal)
    p2 = parse_hatp_proof(raw_escaped)
    assert canonicalize_hatp_proof_payload(p1) == canonicalize_hatp_proof_payload(p2)


def test_cross_call_and_round_trip_stability() -> None:
    proof = parse_hatp_proof(json.dumps(_valid_document("AG3")))
    b1 = canonicalize_hatp_proof_payload(proof)
    b2 = canonicalize_hatp_proof_payload(proof)
    assert b1 == b2
    round_tripped = parse_hatp_proof(json.dumps(hatp_proof_to_document(proof)))
    assert canonicalize_hatp_proof_payload(round_tripped) == b1


def test_tz_environment_independence() -> None:
    doc = _valid_document("AG3")
    proof_default = parse_hatp_proof(json.dumps(doc))
    baseline = canonicalize_hatp_proof_payload(proof_default)
    old_tz = os.environ.get("TZ")
    try:
        os.environ["TZ"] = "America/New_York"
        proof_ny = parse_hatp_proof(json.dumps(doc))
        assert canonicalize_hatp_proof_payload(proof_ny) == baseline
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz


# ═══════════════════════════════════════════════════════════════════════════
# 9. Timestamp semantics -- HIGH PRIORITY, includes BLOCKING finding
# ═══════════════════════════════════════════════════════════════════════════


def test_timezone_equivalent_instants_canonicalize_identically() -> None:
    doc_z = _valid_document("AG3", issued_at="2026-01-01T12:00:00Z")
    doc_offset = _valid_document("AG3", issued_at="2026-01-01T13:00:00+01:00")
    p_z = parse_hatp_proof(json.dumps(doc_z))
    p_offset = parse_hatp_proof(json.dumps(doc_offset))
    assert p_z.issued_at == p_offset.issued_at == "2026-01-01T12:00:00.000Z"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2026-01-01T12:00:00", None),  # missing timezone -> rejected
        ("2026-01-01 12:00:00Z", "2026-01-01T12:00:00.000Z"),  # space separator accepted
        ("2026-01-01T12:00:00z", None),  # lowercase z -> rejected
        ("2026-01-01T12:00:00+0100", "2026-01-01T11:00:00.000Z"),  # colonless offset accepted (3.11+)
        ("2026-01-01", None),  # date only -> rejected
        ("2026-01-01T24:00:00Z", "2026-01-02T00:00:00.000Z"),  # 24:00:00 accepted, rolls to next day
        ("2026-01-01T23:59:60Z", None),  # leap second -> rejected
        ("not-a-date", None),
    ],
)
def test_exotic_iso_forms_documented_accept_reject_set(raw: str, expected) -> None:
    doc = _valid_document("AG3", issued_at=raw)
    if expected is None:
        with pytest.raises(InvalidProofSchemaError):
            parse_hatp_proof(json.dumps(doc))
    else:
        proof = parse_hatp_proof(json.dumps(doc))
        assert proof.issued_at == expected


def test_BLOCKING_submillisecond_timestamps_collapse_to_identical_canonical_bytes() -> None:
    """Historical finding B-149O.1H-1, repaired by Phase 149O.1H.1.

    At the time this suite was written, the canonical timestamp renderer
    truncated (did not round) to millisecond precision via
    `strftime('%f')[:-3]`. Two distinct, individually ISO-8601-valid,
    individually-accepted instants 800 microseconds apart within the
    same millisecond bucket canonicalized to identical bytes and
    therefore an identical digest -- a many-to-one collision in the
    intended future cryptographic signing boundary. 149O.1H.1 closed
    this by narrowing the *accepted* `issued_at` domain instead of
    rounding: any timestamp carrying non-zero fractional precision
    below one millisecond is now rejected outright (`InvalidProofSchemaError`),
    before model acceptance, so every value that survives validation
    maps to a distinct canonical string. This test is updated in place
    (not deleted) to record the flip: before 149O.1H.1 both instants
    parsed and collided; they now both fail to parse at all. See
    `docs/PHASE_149O_1H_1_HATP_TIMESTAMP_CANONICALIZATION_CONSTRUCTOR_DOMAIN_HARDENING.md`
    for the full before/after record and
    `tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py`
    for the authoritative post-repair regression suite."""

    shared_repo = str(uuid.uuid4())
    doc_a = _valid_document("AG3", repository_id=shared_repo, issued_at="2026-01-01T12:00:00.0001Z")
    doc_b = _valid_document("AG3", repository_id=shared_repo, issued_at="2026-01-01T12:00:00.0009Z")
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc_a))
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc_b))


# ═══════════════════════════════════════════════════════════════════════════
# 10. AG3/AG5 discrimination, immutability, alias/mutation attacks
# ═══════════════════════════════════════════════════════════════════════════


def test_ag3_family_with_ag5_object_rejected_via_constructor() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _make_proof("AG3", operation_reference=Ag5OperationReference(per_id="x", ecp_id="y"))


def test_ag5_family_with_ag3_object_rejected_via_constructor() -> None:
    with pytest.raises(InvalidProofSchemaError):
        _make_proof("AG5", operation_reference=Ag3OperationReference(job_id="x", original_commit_sha="c" * 40))


def test_proof_dataclass_is_frozen() -> None:
    proof = _make_proof("AG3")
    with pytest.raises(FrozenInstanceError):
        proof.principal_id = "mallory"  # type: ignore[misc]


def test_ag3_operation_reference_is_frozen() -> None:
    op = Ag3OperationReference(job_id="j", original_commit_sha="c" * 40)
    with pytest.raises(FrozenInstanceError):
        op.job_id = "hacked"  # type: ignore[misc]


def test_ag5_operation_reference_is_frozen() -> None:
    op = Ag5OperationReference(per_id="p", ecp_id="e")
    with pytest.raises(FrozenInstanceError):
        op.per_id = "hacked"  # type: ignore[misc]


def test_no_mutable_container_fields_exist_on_any_model() -> None:
    """No list/dict/set field exists anywhere in the model graph, so
    there is no alias-mutation surface (a caller mutating an
    externally-owned nested value after construction cannot silently
    change proof semantics, because there is no nested mutable value)."""

    for cls in (HumanApprovalProvenanceProof, Ag3OperationReference, Ag5OperationReference):
        for f in fields(cls):
            assert f.type not in ("list", "dict", "set"), f"{cls.__name__}.{f.name} is a mutable-typed field"


def test_ag3_ag5_canonical_bytes_never_collide_even_with_shared_opaque_ids() -> None:
    shared_repo = str(uuid.uuid4())
    doc_ag3 = _valid_document(
        "AG3",
        repository_id=shared_repo,
        principal_id="same",
        signer_key_id="same",
        provider_profile="same",
        decision_record_id="same",
        decision_record_digest="a" * 64,
        binding_id="same",
        binding_digest="b" * 64,
        issued_at="2026-01-01T12:00:00.000Z",
        job_id="same",
        original_commit_sha="c" * 40,
    )
    doc_ag5 = {k: v for k, v in doc_ag3.items() if k not in ("rollback_site", "job_id", "original_commit_sha")}
    doc_ag5["rollback_site"] = "AG5"
    doc_ag5["per_id"] = "same"
    doc_ag5["ecp_id"] = "same"
    p3 = parse_hatp_proof(json.dumps(doc_ag3))
    p5 = parse_hatp_proof(json.dumps(doc_ag5))
    assert canonicalize_hatp_proof_payload(p3) != canonicalize_hatp_proof_payload(p5)


# ═══════════════════════════════════════════════════════════════════════════
# 11. Direct-construction matrix vs. parser domain -- historical finding
# B-149O.1H-2, repaired by Phase 149O.1H.1
#
# At the time this suite was written, `HumanApprovalProvenanceProof.
# __post_init__` checked only AG3/AG5 family-vs-operation-reference-type
# agreement, so direct construction with an invalid `repository_id`,
# invalid digest, unsupported/boolean `proof_version`, non-canonical
# `issued_at`, or empty required identifier succeeded and survived
# canonicalization/digesting unchanged -- a strict superset of what the
# parser accepted. 149O.1H.1 introduced a shared `_require_*` validator
# layer used by both `parse_hatp_proof` and `__post_init__`, so direct
# construction now rejects exactly what the parser rejects for every
# load-bearing structural invariant. The tests below are updated in
# place (not deleted) to record the flip: before 149O.1H.1 the
# constructor calls below succeeded; they now raise the same error class
# the parser raises. See
# `docs/PHASE_149O_1H_1_HATP_TIMESTAMP_CANONICALIZATION_CONSTRUCTOR_DOMAIN_HARDENING.md`
# for the full before/after record and
# `tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py`
# for the authoritative post-repair regression suite.
# ═══════════════════════════════════════════════════════════════════════════


def test_BLOCKING_constructor_accepts_invalid_repository_id_parser_rejects() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", repository_id="not-a-uuid")))
    with pytest.raises(InvalidProofSchemaError):
        _make_proof("AG3", repository_id="not-a-uuid")


def test_BLOCKING_constructor_accepts_invalid_digest_parser_rejects() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", decision_record_digest="not-a-digest")))
    with pytest.raises(InvalidProofSchemaError):
        _make_proof("AG3", decision_record_digest="not-a-digest")


def test_BLOCKING_constructor_accepts_unsupported_version_parser_rejects() -> None:
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", proof_version=99)))
    with pytest.raises(UnsupportedProofVersionError):
        _make_proof("AG3", proof_version=99)


def test_BLOCKING_constructor_accepts_boolean_version_parser_rejects() -> None:
    with pytest.raises(UnsupportedProofVersionError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", proof_version=True)))
    with pytest.raises(UnsupportedProofVersionError):
        _make_proof("AG3", proof_version=True)


def test_BLOCKING_constructor_accepts_noncanonical_timestamp_parser_rejects() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", issued_at="not-a-timestamp")))
    with pytest.raises(InvalidProofSchemaError):
        _make_proof("AG3", issued_at="not-a-timestamp")


def test_BLOCKING_constructor_accepts_empty_principal_id_parser_rejects() -> None:
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(_valid_document("AG3", principal_id="")))
    with pytest.raises(InvalidProofSchemaError):
        _make_proof("AG3", principal_id="")


def test_public_constructor_domain_verdict_is_bypass_not_equivalent() -> None:
    """Historical finding B-149O.1H-2, repaired by Phase 149O.1H.1: named
    verdict test. Before 149O.1H.1 this collected at least one field
    where direct construction bypassed parser invariants (a strict
    superset domain). After 149O.1H.1's shared-validator unification, no
    such field remains -- the constructor domain is equivalent to the
    parser's structural domain for every case exercised here."""

    bypassed = []
    for kwargs in (
        {"repository_id": "not-a-uuid"},
        {"decision_record_digest": "not-a-digest"},
        {"proof_version": 99},
        {"proof_version": True},
        {"issued_at": "garbage"},
        {"principal_id": ""},
    ):
        doc = _valid_document("AG3", **kwargs)
        parser_rejects = False
        try:
            parse_hatp_proof(json.dumps(doc))
        except HATPProofError:
            parser_rejects = True
        assert parser_rejects
        try:
            _make_proof("AG3", **kwargs)
            bypassed.append(kwargs)
        except HATPProofError:
            pass
    assert not bypassed, f"constructor still bypasses parser invariants for: {bypassed}"


# ═══════════════════════════════════════════════════════════════════════════
# 12. Signed-payload completeness (independent reconstruction)
# ═══════════════════════════════════════════════════════════════════════════


def test_signed_payload_field_set_matches_hatp_req_069_independently_derived() -> None:
    """Independently derived from HATP-REQ-069's field list (contract
    §20), not from the implementation's own field-name constants."""

    expected_common = {
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
    proof = parse_hatp_proof(json.dumps(_valid_document("AG3")))
    document = json.loads(canonicalize_hatp_proof_payload(proof))
    assert expected_common <= set(document.keys())
    assert {"job_id", "original_commit_sha"} <= set(document.keys())

    proof5 = parse_hatp_proof(json.dumps(_valid_document("AG5")))
    document5 = json.loads(canonicalize_hatp_proof_payload(proof5))
    assert expected_common <= set(document5.keys())
    assert {"per_id", "ecp_id"} <= set(document5.keys())


def test_no_signature_or_trust_field_present_in_signed_payload() -> None:
    proof = parse_hatp_proof(json.dumps(_valid_document("AG3")))
    document = json.loads(canonicalize_hatp_proof_payload(proof))
    forbidden = {
        "signature",
        "assertion",
        "approved",
        "trusted",
        "authorized",
        "human_present",
        "valid",
        "trusted_root",
        "attestation_root",
    }
    assert forbidden.isdisjoint(document.keys())


# ═══════════════════════════════════════════════════════════════════════════
# 13. Golden vectors -- independently derived (avoiding circularity)
# ═══════════════════════════════════════════════════════════════════════════


def test_ag3_golden_vector_independently_reproduced() -> None:
    doc = {
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
    expected_bytes = _independent_canonical_bytes(doc)
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()
    proof = parse_hatp_proof(json.dumps(doc))
    assert canonicalize_hatp_proof_payload(proof) == expected_bytes
    assert digest_hatp_proof_payload(proof) == expected_digest


def test_ag5_golden_vector_independently_reproduced() -> None:
    doc = {
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
    expected_bytes = _independent_canonical_bytes(doc)
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()
    proof = parse_hatp_proof(json.dumps(doc))
    assert canonicalize_hatp_proof_payload(proof) == expected_bytes
    assert digest_hatp_proof_payload(proof) == expected_digest


def test_digest_algorithm_is_sha256_lowercase_hex() -> None:
    proof = parse_hatp_proof(json.dumps(_valid_document("AG3")))
    digest = digest_hatp_proof_payload(proof)
    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(c in "0123456789abcdef" for c in digest)
    assert digest == hashlib.sha256(canonicalize_hatp_proof_payload(proof)).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# 14. Mutation sensitivity matrix
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "field,new_value",
    [
        ("principal_id", "bob"),
        ("signer_key_id", "key-2"),
        ("provider_profile", "HATP_HARDWARE_PROVIDER_V2"),
        ("repository_id", str(uuid.uuid4())),
        ("decision_record_id", "dec-9"),
        ("decision_record_digest", "f" * 64),
        ("binding_id", "bind-9"),
        ("binding_digest", "9" * 64),
        ("job_id", "job-9"),
        ("original_commit_sha", "9" * 40),
        ("issued_at", "2026-06-01T00:00:00.000Z"),
    ],
)
def test_every_ag3_semantic_field_mutation_changes_digest(field: str, new_value: object) -> None:
    base = _valid_document("AG3")
    base_proof = parse_hatp_proof(json.dumps(base))
    base_digest = digest_hatp_proof_payload(base_proof)

    mutated = dict(base)
    mutated[field] = new_value
    mutated_proof = parse_hatp_proof(json.dumps(mutated))
    mutated_digest = digest_hatp_proof_payload(mutated_proof)

    assert mutated_digest != base_digest


def test_ag5_semantic_field_mutations_change_digest() -> None:
    base = _valid_document("AG5")
    base_proof = parse_hatp_proof(json.dumps(base))
    base_digest = digest_hatp_proof_payload(base_proof)
    for field, new_value in (("per_id", "per-9"), ("ecp_id", "ecp-9")):
        mutated = dict(base)
        mutated[field] = new_value
        mutated_proof = parse_hatp_proof(json.dumps(mutated))
        assert digest_hatp_proof_payload(mutated_proof) != base_digest


def test_rollback_site_family_change_changes_digest_even_with_shared_common_fields() -> None:
    ag3 = _valid_document("AG3")
    base_digest = digest_hatp_proof_payload(parse_hatp_proof(json.dumps(ag3)))
    ag5 = {k: v for k, v in ag3.items() if k not in ("rollback_site", "job_id", "original_commit_sha")}
    ag5["rollback_site"] = "AG5"
    ag5["per_id"] = "job-1"
    ag5["ecp_id"] = "c" * 40
    other_digest = digest_hatp_proof_payload(parse_hatp_proof(json.dumps(ag5)))
    assert base_digest != other_digest


# ═══════════════════════════════════════════════════════════════════════════
# 15. Structural/trust separation and public-API purity audits
# ═══════════════════════════════════════════════════════════════════════════


def test_successful_parse_and_canonicalization_implies_no_trust_verdict() -> None:
    """A successful `parse_hatp_proof` + `canonicalize_hatp_proof_payload`
    + `digest_hatp_proof_payload` call chain returns only structural
    types (`HumanApprovalProvenanceProof`, `bytes`, `str` hex digest).
    None of these values is or contains a HATP-REQ-078 verification
    verdict, an `approval_present` boolean, or any other trust
    assertion."""

    proof = parse_hatp_proof(json.dumps(_valid_document("AG3")))
    assert not hasattr(proof, "approval_present")
    assert not hasattr(proof, "valid")
    assert not hasattr(proof, "verification_status")
    document = json.loads(canonicalize_hatp_proof_payload(proof))
    trust_vocabulary = {
        "VALID", "MISSING", "MALFORMED", "INVALID_SIGNATURE", "UNKNOWN_SIGNER",
        "UNAUTHORIZED_SIGNER", "REVOKED_SIGNER", "INVALID_ATTESTATION",
        "USER_PRESENCE_NOT_PROVEN", "WRONG_OPERATION", "WRONG_REPOSITORY",
        "WRONG_DEPLOYMENT", "EXPIRED",
    }
    assert trust_vocabulary.isdisjoint(str(v) for v in document.values())


def test_module_public_api_has_no_trust_or_verification_named_callable() -> None:
    """Phase 149O.1I, Wave 4 legitimately adds exactly one verifier
    callable (`verify_hatp_proof`, §7 of the 149O.1D plan) -- every other
    imported/defined public name does not literally contain "verify"
    (e.g. "verifier"/"verification" do not contain it as a substring)."""
    forbidden_substrings = ("verify", "trusted", "authoriz", "approval_present", "hatp_valid")
    wave_4_expected = {"verify_hatp_proof"}
    public_names = [n for n in dir(hatp) if not n.startswith("_")]
    for name in public_names:
        if name in wave_4_expected:
            continue
        lowered = name.lower()
        for bad in forbidden_substrings:
            assert bad not in lowered, f"public name {name!r} implies authority ({bad!r})"


def test_module_has_no_forbidden_dependency_imports() -> None:
    """"pcae.core.hatp_bootstrap" deliberately removed from the forbidden
    set here (Phase 149O.1I, Wave 4): the 149O.1D plan explicitly
    co-locates the verifier in this module, requiring a read-only
    `HATPTrustStore` import (HATP-REQ-094). "pcae.core.hatp_providers"
    (the new provider-neutral interface module) is the other newly
    expected import; RAE/Permission-Broker/agent coupling remains
    forbidden."""
    import ast
    import inspect

    src = inspect.getsource(hatp)
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(n.name for n in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_modules = {
        "pcae.core.rollback_approval_evidence",
        "pcae.core.permission_broker",
        "pcae.core.permission_broker_foundation",
        "pcae.core.mutation_permission",
        "pcae.core.agent",
        "pcae.commands.agent",
    }
    assert imported.isdisjoint(forbidden_modules)
    assert imported == {
        "__future__",
        "hashlib",
        "json",
        "re",
        "dataclasses",
        "datetime",
        "enum",
        "typing",
        "pcae.core.repository_identity",
        # Phase 149O.1I, Wave 4 additions (§7 of the 149O.1D plan):
        "pcae.core.hatp_bootstrap",
        "pcae.core.hatp_providers",
    }


def test_no_wallclock_filesystem_or_random_dependency_in_source() -> None:
    """Checks executable code only -- excludes docstrings/comments, which
    (in Wave 4) discuss the no-hidden-wall-clock discipline in prose."""
    import inspect
    import re

    src = inspect.getsource(hatp)
    without_docstrings = re.sub(r'""".*?"""', "", src, flags=re.DOTALL)
    code_only = "\n".join(line.split("#", 1)[0] for line in without_docstrings.splitlines())
    for forbidden in ("datetime.now(", ".utcnow(", "open(", "os.getcwd", "os.chdir", "random.", "socket.", "requests.", "urllib."):
        assert forbidden not in code_only


def test_proof_survives_deleted_cwd(tmp_path, monkeypatch) -> None:
    scratch = tmp_path / "cwd-to-delete"
    scratch.mkdir()
    monkeypatch.chdir(scratch)
    doc = _valid_document("AG3")
    proof = parse_hatp_proof(json.dumps(doc))
    scratch_parent = tmp_path
    os.chdir(scratch_parent)
    scratch.rmdir()
    # Re-canonicalize an already-parsed proof and parse a fresh document,
    # both while cwd no longer resolves to the original directory.
    canonicalize_hatp_proof_payload(proof)
    parse_hatp_proof(json.dumps(_valid_document("AG5")))


# ═══════════════════════════════════════════════════════════════════════════
# 16. Boundary confirmation: byte-unchanged files
# ═══════════════════════════════════════════════════════════════════════════


def test_hatp_contract_and_wave_1_2_files_byte_unchanged_since_149o_1g() -> None:
    import subprocess

    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "01c7fb74..HEAD",
            "--",
            "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
            "src/pcae/core/repository_identity.py",
            "src/pcae/core/hatp_bootstrap.py",
            "src/pcae/core/rollback_approval_evidence.py",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
