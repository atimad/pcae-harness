"""Phase 149O.19.5A, Wave A -- `CertificationRecord`/`CertificationBinding`
model, closed-schema parser, and canonical serializer unit tests for
`pcae.core.hatp_mandatory_certification`.

Structural conformance only (HMIC-REQ-009): these tests never assert that
a well-formed record is currently active, unrevoked, or otherwise `VALID`
-- this module performs no validation-algorithm, identity-derivation, or
storage logic (Waves B-D own those).
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from pcae.core.hatp_mandatory_certification import (
    CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION,
    CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION,
    CertificationBinding,
    CertificationBindingsDocument,
    CertificationMalformedError,
    CertificationRecord,
    CertificationStatus,
    CertificationsDocument,
    canonical_serialize,
    canonicalize_certification_bindings_document,
    canonicalize_certifications_document,
    certification_binding_to_document,
    certification_bindings_document_to_document,
    certification_record_to_document,
    certification_status_satisfies_readiness,
    certifications_document_to_document,
    parse_certification_binding,
    parse_certification_bindings_document,
    parse_certification_bindings_document_from_bytes,
    parse_certification_record,
    parse_certifications_document,
    parse_certifications_document_from_bytes,
)

_VALID_UUID4 = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
_VALID_UUID4_2 = "9c858901-8a57-4791-81fe-4c455b099bc9"
_SHA256_A = "a" * 64
_SHA256_B = "b" * 64
_SHA256_C = "c" * 64
_SHA256_D = "d" * 64
_COMMIT_SHA1 = "f" * 40
_COMMIT_SHA256 = "e" * 64
_CONTRACT_VERSIONS = {
    "HMRC-001": "1.0",
    "HATP-001": "1.0",
    "HSCE-001": "1.1",
    "RAE-001": "1.0",
    "HBDC-001": "1.0",
    "HPSE-001": "1.1",
    "HHCE-001": "1.1",
}
_TIMESTAMP = "2026-08-09T12:00:00Z"


def _record_document(**overrides) -> dict:
    document = {
        "certification_id": _SHA256_A,
        "repository_instance_id": _VALID_UUID4,
        "canonical_deployment_root": "/opt/deployments/repo-1",
        "implementation_commit": _COMMIT_SHA1,
        "implementation_scope_digest": _SHA256_B,
        "contract_versions": dict(_CONTRACT_VERSIONS),
        "verification_record_digest": _SHA256_C,
        "certified_at": _TIMESTAMP,
        "certified_by": "admin-operator",
        "status": "active",
    }
    document.update(overrides)
    return document


def _binding_document(**overrides) -> dict:
    document = {
        "repository_instance_id": _VALID_UUID4,
        "canonical_deployment_root": "/opt/deployments/repo-1",
        "active_certification_id": _SHA256_A,
    }
    document.update(overrides)
    return document


def _record(**overrides) -> CertificationRecord:
    return parse_certification_record(_record_document(**overrides))


def _binding(**overrides) -> CertificationBinding:
    return parse_certification_binding(_binding_document(**overrides))


# ═══════════════════════════════════════════════════════════════════════════
# No side effects on import (item 72-73 of the governing prompt)
# ═══════════════════════════════════════════════════════════════════════════


def test_module_has_no_hardware_or_permission_broker_import():
    """Renamed from `test_module_has_no_filesystem_git_or_hardware_
    import`: Phase 149O.19.5B (Wave B, plan §9.3) plan-authorizes
    `subprocess` (`git rev-parse HEAD`, HMIC-REQ-046) and
    `hatp_bootstrap` (`resolve_canonical_deployment_root`) imports that
    Wave A's original assertion forbade -- both removed from the
    forbidden list below, a deliberate plan-traced widening. The
    hardware-provider and Permission Broker prohibitions remain exactly
    as strict: Wave B never imports either, at any wave."""

    import ast

    import pcae.core.hatp_mandatory_certification as module

    with open(module.__file__, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())

    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module)

    forbidden_substrings = ("hatp_providers", "hatp_fido2_provider", "hatp_piv_provider", "hatp_hardware_credentials", "permission_broker", "hatp_mandatory_cutover")
    for name in imported_names:
        for forbidden in forbidden_substrings:
            assert forbidden not in name, f"unexpected import: {name}"


# ═══════════════════════════════════════════════════════════════════════════
# `CertificationRecord` -- closed schema (attacks 16, 17, 18)
# ═══════════════════════════════════════════════════════════════════════════


def test_valid_record_parses():
    record = _record()
    assert record.certification_id == _SHA256_A
    assert record.status == "active"
    assert record.revoked_at is None


def test_record_rejects_unknown_field():
    with pytest.raises(CertificationMalformedError, match="unrecognized fields"):
        parse_certification_record(_record_document(unexpected_field="x"))


@pytest.mark.parametrize(
    "missing_field",
    [
        "certification_id",
        "repository_instance_id",
        "canonical_deployment_root",
        "implementation_commit",
        "implementation_scope_digest",
        "contract_versions",
        "verification_record_digest",
        "certified_at",
        "certified_by",
        "status",
    ],
)
def test_record_rejects_missing_required_field(missing_field):
    document = _record_document()
    del document[missing_field]
    with pytest.raises(CertificationMalformedError, match="missing fields"):
        parse_certification_record(document)


def test_record_non_object_top_level_rejected():
    for bad in ([], "a string", 1, True, None):
        with pytest.raises(CertificationMalformedError, match="is not a JSON object"):
            parse_certification_record(bad)


def test_record_duplicate_json_keys_rejected_via_raw_json():
    raw = (
        '{"certifications": [{'
        '"certification_id": "%s", "certification_id": "%s",'
        '"repository_instance_id": "%s", "canonical_deployment_root": "/x",'
        '"implementation_commit": "%s", "implementation_scope_digest": "%s",'
        '"contract_versions": {"HMRC-001":"1.0","HATP-001":"1.0","HSCE-001":"1.1","RAE-001":"1.0"},'
        '"verification_record_digest": "%s", "certified_at": "%s",'
        '"certified_by": "a", "status": "active"'
        '}], "schema_version": 1}'
    ) % (_SHA256_A, _SHA256_B, _VALID_UUID4, _COMMIT_SHA1, _SHA256_B, _SHA256_C, _TIMESTAMP)
    with pytest.raises(CertificationMalformedError, match="duplicate JSON object key"):
        parse_certifications_document_from_bytes(raw)


def test_record_unknown_schema_version_rejected():
    with pytest.raises(CertificationMalformedError, match="not supported"):
        parse_certifications_document({"schema_version": 2, "certifications": []})


@pytest.mark.parametrize("bad_version", [True, False, "1", 1.0, None, 0, -1])
def test_document_schema_version_boolean_and_type_strictness(bad_version):
    with pytest.raises(CertificationMalformedError):
        parse_certifications_document({"schema_version": bad_version, "certifications": []})


def test_malformed_document_top_level_not_object():
    with pytest.raises(CertificationMalformedError, match="is not a JSON object"):
        parse_certifications_document(["not", "an", "object"])


def test_malformed_document_certifications_not_array():
    with pytest.raises(CertificationMalformedError, match="must be a JSON array"):
        parse_certifications_document({"schema_version": 1, "certifications": {}})


def test_certifications_document_rejects_duplicate_certification_id():
    document = {
        "schema_version": CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION,
        "certifications": [_record_document(), _record_document(certified_by="someone-else")],
    }
    with pytest.raises(CertificationMalformedError, match="duplicate certification_id"):
        parse_certifications_document(document)


def test_certifications_document_top_level_unknown_field_rejected():
    with pytest.raises(CertificationMalformedError, match="unrecognized top-level fields"):
        parse_certifications_document({"schema_version": 1, "certifications": [], "extra": True})


def test_certifications_document_top_level_missing_field_rejected():
    with pytest.raises(CertificationMalformedError, match="missing top-level fields"):
        parse_certifications_document({"schema_version": 1})


# ═══════════════════════════════════════════════════════════════════════════
# Type strictness (items 12-13 of the governing prompt)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("bad_status", [True, False, 1, None, "ACTIVE", "Active", " active", "active ", ""])
def test_record_status_type_and_case_strictness(bad_status):
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(status=bad_status))


def test_record_revoked_status_requires_revoked_at():
    with pytest.raises(CertificationMalformedError, match="revoked_at is missing"):
        parse_certification_record(_record_document(status="revoked"))


def test_record_active_status_forbids_revoked_at():
    with pytest.raises(CertificationMalformedError, match="revoked_at is set"):
        parse_certification_record(_record_document(status="active", revoked_at=_TIMESTAMP))


def test_record_revoked_status_with_revoked_at_accepted():
    record = _record(status="revoked", revoked_at=_TIMESTAMP)
    assert record.status == "revoked"
    assert record.revoked_at == _TIMESTAMP


@pytest.mark.parametrize(
    "field",
    ["certification_id", "implementation_scope_digest", "verification_record_digest"],
)
@pytest.mark.parametrize(
    "bad_value",
    [
        "../../../etc/passwd",
        "/etc/passwd",
        "a" * 63,
        "a" * 65,
        "A" * 64,
        "a" * 32 + "G" * 32,
        " " + "a" * 63,
        "a" * 63 + " ",
        "a" * 31 + "/" + "a" * 32,
        "a" * 31 + "\\" + "a" * 32,
        "a" * 32 + ".." + "a" * 30,
        "а" * 64,  # Cyrillic lookalike 'а', not ASCII hex
        "",
        None,
        True,
        12345,
        "a" * 63 + "\x00",
    ],
)
def test_sha256_hex_fields_reject_id_attack_matrix(field, bad_value):
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(**{field: bad_value}))


@pytest.mark.parametrize(
    "bad_commit",
    ["a" * 39, "a" * 41, "A" * 40, "a" * 39 + "G", "", None, True, "../etc/passwd", " " + "a" * 39],
)
def test_implementation_commit_rejects_bad_grammar(bad_commit):
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(implementation_commit=bad_commit))


def test_implementation_commit_accepts_sha1_and_sha256_length():
    assert _record(implementation_commit=_COMMIT_SHA1).implementation_commit == _COMMIT_SHA1
    assert _record(implementation_commit=_COMMIT_SHA256).implementation_commit == _COMMIT_SHA256


@pytest.mark.parametrize("bad_repo_id", ["not-a-uuid", "", None, 123, True, "  " + _VALID_UUID4])
def test_repository_instance_id_rejects_non_uuid4(bad_repo_id):
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(repository_instance_id=bad_repo_id))


def test_repository_instance_id_uppercase_lexical_variant_accepted_verbatim():
    """Matches `repository_identity.is_valid_repository_instance_id`'s own
    documented behavior (reused here, not reimplemented): an uppercase
    lexical variant of a valid UUID4 is accepted, and retained verbatim --
    never opportunistically lowercased (item 19 of the governing prompt:
    no automatic case-folding of an authority-bearing identifier)."""

    record = _record(repository_instance_id=_VALID_UUID4.upper())
    assert record.repository_instance_id == _VALID_UUID4.upper()


@pytest.mark.parametrize("bad_root", ["", None, 123, True, [], {}])
def test_canonical_deployment_root_rejects_non_string(bad_root):
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(canonical_deployment_root=bad_root))


def test_canonical_deployment_root_no_normalization_no_trim():
    root = "/opt/deployments/repo-1/"
    record = _record(canonical_deployment_root=root)
    assert record.canonical_deployment_root == root  # not trimmed of trailing slash


@pytest.mark.parametrize("bad_by", ["", None, 123, True, [], {}])
def test_certified_by_rejects_non_string(bad_by):
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(certified_by=bad_by))


def test_certified_by_no_whitespace_trim_no_case_fold():
    record = _record(certified_by=" Admin-Operator ")
    assert record.certified_by == " Admin-Operator "


# ═══════════════════════════════════════════════════════════════════════════
# `contract_versions` closed schema (HMIC-REQ-067/068)
# ═══════════════════════════════════════════════════════════════════════════


def test_contract_versions_rejects_unknown_key():
    bad = dict(_CONTRACT_VERSIONS, **{"PBPA-001": "1.0"})
    with pytest.raises(CertificationMalformedError, match="unrecognized contract entries"):
        parse_certification_record(_record_document(contract_versions=bad))


def test_contract_versions_rejects_missing_key():
    bad = dict(_CONTRACT_VERSIONS)
    del bad["RAE-001"]
    with pytest.raises(CertificationMalformedError, match="missing required contract entries"):
        parse_certification_record(_record_document(contract_versions=bad))


@pytest.mark.parametrize("bad_value", [123, True, None, [], {}])
def test_contract_versions_rejects_non_string_value(bad_value):
    bad = dict(_CONTRACT_VERSIONS, **{"HMRC-001": bad_value})
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(contract_versions=bad))


def test_contract_versions_rejects_non_object():
    with pytest.raises(CertificationMalformedError, match="expected a JSON object"):
        parse_certification_record(_record_document(contract_versions=["HMRC-001"]))


def test_contract_versions_stored_as_immutable_mapping():
    record = _record()
    with pytest.raises(TypeError):
        record.contract_versions["HMRC-001"] = "9.9"  # type: ignore[index]


# ═══════════════════════════════════════════════════════════════════════════
# Timestamp grammar and attack matrix (items 20-22, 62)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "bad_ts",
    [
        "2026-08-09T12:00:00ZZ",
        "2026-08-09T12:00:00z",
        "2026-08-09T12:00:00Z+00:00",
        "2026-08-09T12:00:00garbage+00:00",
        "2026-08-09T12:00:00",
        "2026-08-09T12:00:00+00:00",
        " 2026-08-09T12:00:00Z",
        "2026-08-09T12:00:00Z ",
        "2026-08-09T12:00:00.1234567Z",  # 7-digit fraction, grammar allows 1-6
        "2026-13-01T12:00:00Z",  # invalid month, calendar check
        "2026-08-32T12:00:00Z",  # invalid day
        "2026-08-09T25:00:00Z",  # invalid hour
        "",
        None,
        True,
        123,
    ],
)
def test_certified_at_rejects_timestamp_attack_matrix(bad_ts):
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(certified_at=bad_ts))


def test_certified_at_accepts_three_and_six_digit_fractional_seconds():
    """The lexical grammar (`_TIMESTAMP_PATTERN`) admits 1-6 fraction
    digits, but the calendar check that follows it
    (`datetime.fromisoformat`, inherited verbatim from
    `hatp_mandatory_cutover.py::_validate_timestamp`) accepts only
    exactly-3-digit (millisecond) or exactly-6-digit (microsecond)
    fractions on this interpreter -- 1, 2, 4, and 5-digit fractions are
    lexically well-formed but fail the calendar check and are rejected.
    This is the identical, already-battle-tested behavior of the reused
    precedent function, not a new defect introduced here."""

    for fraction_digits in (3, 6):
        ts = "2026-08-09T12:00:00." + ("1" * fraction_digits) + "Z"
        record = _record(certified_at=ts)
        assert record.certified_at == ts


@pytest.mark.parametrize("fraction_digits", [1, 2, 4, 5])
def test_certified_at_rejects_non_three_non_six_digit_fractions(fraction_digits):
    ts = "2026-08-09T12:00:00." + ("1" * fraction_digits) + "Z"
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(certified_at=ts))


def test_certified_at_accepts_no_fraction():
    record = _record(certified_at="2026-08-09T12:00:00Z")
    assert record.certified_at == "2026-08-09T12:00:00Z"


def test_revoked_at_uses_same_strict_grammar():
    with pytest.raises(CertificationMalformedError):
        parse_certification_record(_record_document(status="revoked", revoked_at="2026-08-09T12:00:00z"))


# ═══════════════════════════════════════════════════════════════════════════
# `CertificationBinding` -- closed schema (attack 21)
# ═══════════════════════════════════════════════════════════════════════════


def test_valid_binding_parses():
    binding = _binding()
    assert binding.active_certification_id == _SHA256_A


def test_binding_active_certification_id_absent_means_no_active_cert():
    binding = parse_certification_binding(
        {"repository_instance_id": _VALID_UUID4, "canonical_deployment_root": "/x"}
    )
    assert binding.active_certification_id is None


def test_binding_rejects_unknown_field():
    with pytest.raises(CertificationMalformedError, match="unrecognized fields"):
        parse_certification_binding(_binding_document(unexpected="x"))


@pytest.mark.parametrize("missing_field", ["repository_instance_id", "canonical_deployment_root"])
def test_binding_rejects_missing_required_field(missing_field):
    document = _binding_document()
    del document[missing_field]
    with pytest.raises(CertificationMalformedError, match="missing fields"):
        parse_certification_binding(document)


def test_binding_non_object_top_level_rejected():
    for bad in ([], "x", 1, None):
        with pytest.raises(CertificationMalformedError, match="is not a JSON object"):
            parse_certification_binding(bad)


@pytest.mark.parametrize(
    "bad_pointer",
    [
        "not-a-digest",
        "A" * 64,
        "a" * 63,
        "../certifications.json",
        "certifications.json#" + _SHA256_A,
        "",
        123,
        True,
    ],
)
def test_binding_active_certification_id_never_a_path_or_partial_value(bad_pointer):
    with pytest.raises(CertificationMalformedError):
        parse_certification_binding(_binding_document(active_certification_id=bad_pointer))


def test_certification_bindings_document_rejects_duplicate_key():
    document = {
        "schema_version": CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION,
        "bindings": [_binding_document(), _binding_document(active_certification_id=_SHA256_B)],
    }
    with pytest.raises(CertificationMalformedError, match="duplicate"):
        parse_certification_bindings_document(document)


def test_certification_bindings_document_two_different_keys_both_accepted():
    document = {
        "schema_version": CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION,
        "bindings": [
            _binding_document(),
            _binding_document(repository_instance_id=_VALID_UUID4_2),
        ],
    }
    parsed = parse_certification_bindings_document(document)
    assert len(parsed.bindings) == 2


def test_certification_bindings_document_bindings_not_array_rejected():
    with pytest.raises(CertificationMalformedError, match="must be a JSON array"):
        parse_certification_bindings_document({"schema_version": 1, "bindings": {}})


# ═══════════════════════════════════════════════════════════════════════════
# `CertificationStatus` -- closed 9-value vocabulary (HMIC-REQ-106/107)
# ═══════════════════════════════════════════════════════════════════════════


def test_certification_status_has_exactly_nine_members():
    assert len(list(CertificationStatus)) == 9


def test_certification_status_exact_vocabulary():
    assert {member.value for member in CertificationStatus} == {
        "MISSING",
        "MALFORMED",
        "WRONG_REPOSITORY",
        "WRONG_DEPLOYMENT",
        "IMPLEMENTATION_MISMATCH",
        "CONTRACT_MISMATCH",
        "REVOKED",
        "ACCESS_ERROR",
        "VALID",
    }


def test_no_valid_with_warning_or_partial_credit_member():
    for member in CertificationStatus:
        assert "WARNING" not in member.value
        assert "PARTIAL" not in member.value


@pytest.mark.parametrize("status", list(CertificationStatus))
def test_readiness_mapping_is_true_only_for_valid(status):
    expected = status is CertificationStatus.VALID
    assert certification_status_satisfies_readiness(status) is expected


def test_readiness_mapping_never_true_for_non_member_value():
    assert certification_status_satisfies_readiness("VALID") is False  # type: ignore[arg-type]
    assert certification_status_satisfies_readiness(None) is False  # type: ignore[arg-type]


# ═══════════════════════════════════════════════════════════════════════════
# Canonical serialization (items 23-27, 63-66)
# ═══════════════════════════════════════════════════════════════════════════


def test_canonical_serialize_exact_bytes_golden():
    document = {"b": 2, "a": 1}
    assert canonical_serialize(document) == b'{\n  "a": 1,\n  "b": 2\n}\n'


def test_canonical_serialize_is_utf8_encoded_bytes():
    assert isinstance(canonical_serialize({"a": 1}), bytes)


def test_canonical_serialize_key_order_always_sorted():
    doc1 = canonical_serialize({"z": 1, "a": 2, "m": 3})
    doc2 = canonical_serialize({"a": 2, "m": 3, "z": 1})
    assert doc1 == doc2
    assert doc1 == b'{\n  "a": 2,\n  "m": 3,\n  "z": 1\n}\n'


def test_canonical_serialize_no_nan_or_infinity_round_trippable():
    with pytest.raises(ValueError):
        canonical_serialize({"a": float("nan")})


def test_canonical_serialize_unicode_default_ascii_escaping():
    payload = canonical_serialize({"name": "café"})
    assert b"caf\\u00e9" in payload
    assert "café".encode("utf-8") not in payload


def test_certification_record_canonical_roundtrip():
    record = _record()
    document = certification_record_to_document(record)
    reparsed = parse_certification_record(document)
    assert reparsed == record


def test_certifications_document_canonical_roundtrip_parse_of_canonical_bytes():
    doc = CertificationsDocument(schema_version=1, certifications=(_record(),))
    canonical_bytes = canonicalize_certifications_document(doc)
    reparsed = parse_certifications_document_from_bytes(canonical_bytes)
    assert reparsed == doc


def test_certification_bindings_document_canonical_roundtrip():
    doc = CertificationBindingsDocument(schema_version=1, bindings=(_binding(),))
    canonical_bytes = canonicalize_certification_bindings_document(doc)
    reparsed = parse_certification_bindings_document_from_bytes(canonical_bytes)
    assert reparsed == doc


def test_noncanonical_input_serializes_to_canonical_bytes():
    """serialize(parse(valid_noncanonical_input)) -> canonical bytes."""

    record_doc = _record_document()
    noncanonical_text = json.dumps({"certifications": [record_doc], "schema_version": 1}, indent=4)
    doc = parse_certifications_document_from_bytes(noncanonical_text)
    canonical_bytes = canonicalize_certifications_document(doc)
    expected = canonical_serialize(certifications_document_to_document(
        CertificationsDocument(schema_version=1, certifications=(parse_certification_record(record_doc),))
    ))
    assert canonical_bytes == expected


def test_revoked_at_omitted_from_serialized_document_when_active():
    record = _record()
    document = certification_record_to_document(record)
    assert "revoked_at" not in document


def test_revoked_at_present_in_serialized_document_when_revoked():
    record = _record(status="revoked", revoked_at=_TIMESTAMP)
    document = certification_record_to_document(record)
    assert document["revoked_at"] == _TIMESTAMP


def test_active_certification_id_omitted_when_absent():
    binding = parse_certification_binding(
        {"repository_instance_id": _VALID_UUID4, "canonical_deployment_root": "/x"}
    )
    document = certification_binding_to_document(binding)
    assert "active_certification_id" not in document


def test_certification_bindings_document_to_document_roundtrip_dict_shape():
    doc = CertificationBindingsDocument(schema_version=1, bindings=(_binding(),))
    raw = certification_bindings_document_to_document(doc)
    assert raw == {
        "schema_version": 1,
        "bindings": [certification_binding_to_document(_binding())],
    }


# ═══════════════════════════════════════════════════════════════════════════
# Immutability (item 67)
# ═══════════════════════════════════════════════════════════════════════════


def test_certification_record_is_frozen():
    record = _record()
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.status = "revoked"  # type: ignore[misc]


def test_certification_binding_is_frozen():
    binding = _binding()
    with pytest.raises(dataclasses.FrozenInstanceError):
        binding.active_certification_id = _SHA256_B  # type: ignore[misc]


def test_certifications_document_certifications_is_a_tuple_not_a_list():
    doc = CertificationsDocument(schema_version=1, certifications=[_record()])  # type: ignore[arg-type]
    assert isinstance(doc.certifications, tuple)


def test_certification_bindings_document_bindings_is_a_tuple_not_a_list():
    doc = CertificationBindingsDocument(schema_version=1, bindings=[_binding()])  # type: ignore[arg-type]
    assert isinstance(doc.bindings, tuple)


# ═══════════════════════════════════════════════════════════════════════════
# Equality -- structural, not identity (item 69)
# ═══════════════════════════════════════════════════════════════════════════


def test_certification_record_equality_is_structural():
    a = _record()
    b = _record()
    assert a is not b
    assert a == b


def test_certification_record_inequality_on_differing_field():
    a = _record()
    b = _record(certified_by="different-operator")
    assert a != b


# ═══════════════════════════════════════════════════════════════════════════
# Semantic wall: parsed record != valid certification (item 48)
# ═══════════════════════════════════════════════════════════════════════════


def test_parsing_success_never_implies_validity():
    """A structurally well-formed `CertificationRecord` carries no
    validity signal of its own -- there is no boolean anywhere on this
    type or the parser's return path that could be mistaken for
    HMIC-REQ-107's readiness fact. Only a future Wave D validator, given
    a fresh filesystem/Git/contract-header comparison, may ever compute
    that fact."""

    record = _record(status="active")
    field_names = {f.name for f in dataclasses.fields(record)}
    assert field_names == {
        "certification_id",
        "repository_instance_id",
        "canonical_deployment_root",
        "implementation_commit",
        "implementation_scope_digest",
        "contract_versions",
        "verification_record_digest",
        "certified_at",
        "certified_by",
        "status",
        "revoked_at",
    }
    # No derived approved/allowed/trusted/valid/executed/capable field.
    for forbidden in ("approved", "allowed", "trusted", "valid", "executed", "capable", "ready"):
        assert forbidden not in field_names


def test_module_defines_no_filesystem_reading_function():
    import pcae.core.hatp_mandatory_certification as module

    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        assert not (callable(obj) and "read" in name.lower() and "root" in name.lower())
