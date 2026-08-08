"""HATP Signed Evidence Envelope — Model, Parser, Canonical Serializer
(Phase 149O.12A, Wave A of the 149O.11 implementation plan).

Implements HSCE-REQ-031..040, HSCE-REQ-053, HSCE-REQ-056, HSCE-REQ-059,
HSCE-REQ-062..064, HSCE-REQ-072..073 (`docs/contracts/
HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`, HSCE-001 v1.1).

This module owns exactly the `HATPSignedEvidenceEnvelope` type -- the
closed four-field storage/transport artifact this contract's signing
command persists -- distinct from and never a modification of
`human_approval_trusted_provenance.HumanApprovalProvenanceProof`
(HSCE-REQ-031). It performs NO cryptographic verification (`parse` !=
`verify`, HSCE-REQ-063): a successful parse or construction means only
that the envelope is structurally well-formed and that its `evidence_id`
is the correct digest of its embedded `proof`'s canonical payload --
nothing about signer authenticity, human presence, or trust-store state.
That remains exclusively `human_approval_trusted_provenance.
verify_hatp_proof`'s responsibility, never reimplemented or shortcut
here.

Dependency direction: this module imports only `human_approval_trusted_
provenance.py` (`HumanApprovalProvenanceProof`, `HATPProofError`,
`parse_hatp_proof`, `hatp_proof_to_document`, `digest_hatp_proof_payload`)
-- it reuses that module's own proof parser rather than duplicating a
weaker one (HSCE-REQ-006, governing-prompt §10). It does not import
`hatp_bootstrap.py`, `hatp_providers.py`, `hatp_evidence_store.py`,
`rollback_approval_evidence.py`, `permission_broker*.py`, or `agent.py`.

No production code path in this module treats evidence-file existence,
or a valid-looking `evidence_id` string alone, as approval -- this module
does not touch a filesystem at all (that is `hatp_evidence_store.py`'s
concern).
"""
from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass
from typing import Union

from pcae.core.human_approval_trusted_provenance import (
    HATPProofError,
    HumanApprovalProvenanceProof,
    digest_hatp_proof_payload,
    hatp_proof_to_document,
    parse_hatp_proof,
)

#: HSCE-REQ-033: the only supported `evidence_version`. A future contract
#: amendment, not a silent best-effort acceptance, is required to add a
#: second value.
EVIDENCE_VERSION = 1

#: HSCE-REQ-056/059: lowercase, 64-character hex only -- no normalization,
#: no case-insensitive alias, matching `human_approval_trusted_
#: provenance.py::_SHA256_HEX_RE`'s identical pattern.
_EVIDENCE_ID_RE = re.compile(r"^[0-9a-f]{64}$")

#: HSCE-REQ-032: the envelope's exact closed field set. No fifth field.
_ENVELOPE_FIELDS = frozenset({"evidence_version", "evidence_id", "proof", "provider_assertion"})


class HATPSignedEvidenceError(Exception):
    """Base error for `HATPSignedEvidenceEnvelope` construction/parsing.
    Structural vocabulary only -- never a HATP verification-status name
    and never one of `hatp_evidence_store.py`'s own storage `error_type`
    values, which belong to that module, not this one."""


class MalformedEvidenceEnvelopeError(HATPSignedEvidenceError):
    """The input is not well-formed JSON, is not a JSON object, or
    contains a duplicate JSON object key at any nesting level."""


class UnsupportedEvidenceVersionError(HATPSignedEvidenceError):
    """`evidence_version` is absent, not an integer, a `bool`, or not
    exactly `1` (HSCE-REQ-033). Never best-effort accepted."""


class InvalidEvidenceIdError(HATPSignedEvidenceError):
    """`evidence_id` is not a lowercase, 64-character hexadecimal string
    (HSCE-REQ-056/059). Rejected before any path is constructed from it;
    never sanitized-and-retried."""


class InvalidEvidenceEnvelopeSchemaError(HATPSignedEvidenceError):
    """The document fails the envelope's closed structural schema: an
    unknown top-level field, a missing required field, or a field of the
    wrong type (HSCE-REQ-032, HSCE-REQ-062)."""


class EvidenceIdDigestMismatchError(HATPSignedEvidenceError):
    """`evidence_id` does not equal `digest_hatp_proof_payload(proof)`
    for the embedded `proof` (HSCE-REQ-036, HSCE-REQ-062). Treated as an
    invalid envelope, never trusted, never repaired in place."""


def validate_evidence_id(value: object) -> str:
    """Shared validator (HSCE-REQ-056): exported so `hatp_evidence_store.py`
    reuses the identical domain for its own path-construction guard,
    rather than defining a second, potentially-drifting regex. Any value
    containing `../`, `/`, `\\`, whitespace, uppercase hex characters, a
    partial-length digest, or any other non-conforming character is
    rejected here, before any path or digest comparison ever uses it."""

    if not isinstance(value, str) or not _EVIDENCE_ID_RE.fullmatch(value):
        raise InvalidEvidenceIdError(
            f"evidence_id must be a lowercase 64-character hexadecimal string, got {value!r}"
        )
    return value


def _require_evidence_version(value: object) -> int:
    """Mirrors `human_approval_trusted_provenance.py::_require_proof_version`'s
    explicit, independent `isinstance(value, bool)` pre-check -- `bool`
    is an `int` subclass in Python, so `isinstance(True, int)` is `True`
    and must not be allowed to satisfy `evidence_version == 1` by
    accident (HSCE-REQ-033)."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise UnsupportedEvidenceVersionError(f"evidence_version must be an integer, got {value!r}")
    if value != EVIDENCE_VERSION:
        raise UnsupportedEvidenceVersionError(f"unsupported evidence_version: {value!r}")
    return value


def _require_proof(value: object) -> HumanApprovalProvenanceProof:
    if not isinstance(value, HumanApprovalProvenanceProof):
        raise InvalidEvidenceEnvelopeSchemaError(
            f"proof must be a HumanApprovalProvenanceProof, got {type(value).__name__}"
        )
    return value


def _require_provider_assertion(value: object) -> bytes:
    """HSCE-REQ-034: stored on the model as decoded, opaque `bytes` --
    never re-interpreted or re-parsed by this module. Base64 encoding
    exists only at the JSON serialize/parse boundary (`serialize_hatp_
    signed_evidence`/`parse_hatp_signed_evidence`), never on the typed
    model itself. Empty bytes are structurally accepted (governing-
    prompt §13); this module never performs cryptographic verification
    of the assertion's content (HSCE-REQ-063)."""

    if not isinstance(value, bytes):
        raise InvalidEvidenceEnvelopeSchemaError(
            f"provider_assertion must be bytes, got {type(value).__name__}"
        )
    return value


def _validate_envelope_fields(
    evidence_version: object,
    evidence_id: object,
    proof: object,
    provider_assertion: object,
) -> None:
    """The single shared validation function called both from `__post_init__`
    and from the parser's document-to-model step (HSCE-REQ-072,
    constructor/parser domain equivalence -- the B-149O.1H-2 lesson: no
    envelope constructible directly that the parser would reject, and
    vice versa). Raises on the first violation found; callers that need
    a specific field's error should validate that field independently
    before construction if a different ordering is required."""

    _require_evidence_version(evidence_version)
    validated_evidence_id = validate_evidence_id(evidence_id)
    validated_proof = _require_proof(proof)
    _require_provider_assertion(provider_assertion)

    expected_evidence_id = digest_hatp_proof_payload(validated_proof)
    if validated_evidence_id != expected_evidence_id:
        raise EvidenceIdDigestMismatchError(
            f"evidence_id {validated_evidence_id!r} does not match "
            f"digest_hatp_proof_payload(proof) {expected_evidence_id!r}"
        )


@dataclass(frozen=True)
class HATPSignedEvidenceEnvelope:
    """HSCE-REQ-031/032: the frozen four-field envelope. No authority-
    bearing field exists anywhere on this type -- no `approved`,
    `verified`, `valid`, `permission`, `allow`, `operational`, `executed`,
    or `human_present` field, by design (governing-prompt §5). Immutable
    by construction (HSCE-REQ-040/073): because `evidence_id` is a pure
    function of `proof` alone, any mutation of `proof` after construction
    would be both prevented by `frozen=True` and, were it possible, would
    yield a different `evidence_id` -- never an in-place edit of an
    existing evidence record."""

    evidence_version: int
    evidence_id: str
    proof: HumanApprovalProvenanceProof
    provider_assertion: bytes

    def __post_init__(self) -> None:
        _validate_envelope_fields(self.evidence_version, self.evidence_id, self.proof, self.provider_assertion)


def build_hatp_signed_evidence_envelope(
    proof: HumanApprovalProvenanceProof,
    provider_assertion: bytes,
) -> HATPSignedEvidenceEnvelope:
    """The production builder (HSCE-REQ-036): derives `evidence_id =
    digest_hatp_proof_payload(proof)` internally -- it does not accept an
    externally supplied `evidence_id` at all. This is the only envelope
    construction path `hatp_signing_ceremony.py` (149O.12B) is expected
    to use; the typed constructor above still accepts an explicit
    `evidence_id` argument because the parser (below) must recompute-
    and-compare rather than blindly trust one, but this builder never
    exposes that as a caller-selectable value."""

    evidence_id = digest_hatp_proof_payload(proof)
    return HATPSignedEvidenceEnvelope(
        evidence_version=EVIDENCE_VERSION,
        evidence_id=evidence_id,
        proof=proof,
        provider_assertion=provider_assertion,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Duplicate-JSON-key-rejecting strict loader -- module-local, matching the
# HATP-family's own per-module duplication convention (`human_approval_
# trusted_provenance.py::_reject_duplicate_keys`, `hatp_bootstrap.py`),
# not `pcae.schema_runtime.json_parser`, per HSCE-REQ-053's explicit
# instruction to reuse "the object_pairs_hook technique." `object_pairs_
# hook` is invoked by `json.loads` for every JSON object at every nesting
# level, so this single top-level parse already rejects a duplicate key
# anywhere in the document, including inside the nested `proof` object --
# no separate nested-duplicate-key pass is needed here.
# ═══════════════════════════════════════════════════════════════════════════


def _reject_duplicate_keys(pairs: list) -> dict:
    seen: set = set()
    result: dict = {}
    for key, value in pairs:
        if key in seen:
            raise MalformedEvidenceEnvelopeError(f"duplicate JSON object key: {key!r}")
        seen.add(key)
        result[key] = value
    return result


def _load_json_no_duplicate_keys(raw: Union[str, bytes]) -> object:
    try:
        return json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise MalformedEvidenceEnvelopeError(f"evidence envelope is not valid JSON: {exc}") from exc


def _envelope_from_document(document: object) -> HATPSignedEvidenceEnvelope:
    """Validate and construct a `HATPSignedEvidenceEnvelope` from an
    already-parsed JSON object. Callers requiring duplicate-key rejection
    MUST go through `parse_hatp_signed_evidence`, which parses raw JSON
    text via `_load_json_no_duplicate_keys` first -- this function does
    not itself re-parse raw text."""

    if not isinstance(document, dict):
        raise InvalidEvidenceEnvelopeSchemaError("evidence envelope document is not a JSON object")

    present = set(document.keys())
    unknown = present - _ENVELOPE_FIELDS
    if unknown:
        raise InvalidEvidenceEnvelopeSchemaError(
            f"evidence envelope has unrecognized fields: {sorted(unknown)}"
        )
    missing = _ENVELOPE_FIELDS - present
    if missing:
        raise InvalidEvidenceEnvelopeSchemaError(
            f"evidence envelope is missing required fields: {sorted(missing)}"
        )

    evidence_version = _require_evidence_version(document.get("evidence_version"))

    evidence_id_raw = document.get("evidence_id")
    if not isinstance(evidence_id_raw, str):
        raise InvalidEvidenceEnvelopeSchemaError(
            f"evidence_id must be a string, got {type(evidence_id_raw).__name__}"
        )
    evidence_id = validate_evidence_id(evidence_id_raw)

    proof_document = document.get("proof")
    if not isinstance(proof_document, dict):
        raise InvalidEvidenceEnvelopeSchemaError(
            f"proof must be a JSON object, got {type(proof_document).__name__}"
        )
    # Delegate to HATP-001's own proof parser (HSCE-REQ-006, governing-
    # prompt §10) -- never a second, weaker structural parser copied into
    # this module. `proof_document` is already duplicate-key-safe (its
    # duplicates, if any, were already rejected by the outer parse's own
    # `object_pairs_hook`), so re-serializing it to JSON text for
    # `parse_hatp_proof` cannot reintroduce a duplicate that survives.
    try:
        proof = parse_hatp_proof(json.dumps(proof_document))
    except HATPProofError as exc:
        raise InvalidEvidenceEnvelopeSchemaError(
            f"proof failed HATP-001 structural validation: {exc}"
        ) from exc

    provider_assertion_raw = document.get("provider_assertion")
    if not isinstance(provider_assertion_raw, str):
        raise InvalidEvidenceEnvelopeSchemaError(
            f"provider_assertion must be a base64-encoded string, got {type(provider_assertion_raw).__name__}"
        )
    try:
        provider_assertion = base64.b64decode(provider_assertion_raw, validate=True)
    except binascii.Error as exc:
        raise InvalidEvidenceEnvelopeSchemaError(f"provider_assertion is not valid base64: {exc}") from exc

    return HATPSignedEvidenceEnvelope(
        evidence_version=evidence_version,
        evidence_id=evidence_id,
        proof=proof,
        provider_assertion=provider_assertion,
    )


def parse_hatp_signed_evidence(raw: Union[str, bytes]) -> HATPSignedEvidenceEnvelope:
    """Parse raw JSON text/bytes into a `HATPSignedEvidenceEnvelope`
    (HSCE-REQ-062). A successful return establishes structural validity
    only (HSCE-REQ-063) -- closed schema (unknown/missing/duplicate keys
    rejected), supported `evidence_version`, and `evidence_id ==
    digest_hatp_proof_payload(proof)`. It does NOT establish provider-
    assertion validity or proof trust; only a subsequent `verify_hatp_
    proof` call (owned by `human_approval_trusted_provenance.py`,
    consumed by a future phase) establishes trust."""

    document = _load_json_no_duplicate_keys(raw)
    return _envelope_from_document(document)


# ═══════════════════════════════════════════════════════════════════════════
# Canonical serialization (HSCE-REQ-053) -- the one function all of
# winner-write, loser-byte-comparison, and idempotency checks in
# `hatp_evidence_store.py` use. Distinct from and never confused with
# HATP-001's own signed canonical payload serialization
# (`canonicalize_hatp_proof_payload`), which remains solely what the
# hardware provider signs.
# ═══════════════════════════════════════════════════════════════════════════


def serialize_hatp_signed_evidence(envelope: HATPSignedEvidenceEnvelope) -> bytes:
    """HSCE-REQ-053: UTF-8, `sort_keys=True`, no `NaN`/`Infinity`
    (`allow_nan=False`). REQ-053's text lists exactly these properties
    and no compact-separator requirement (unlike `canonicalize_hatp_
    proof_payload`'s signed-payload serializer) -- this function does not
    invent one; standard `json.dumps` default separators are used."""

    document = {
        "evidence_version": envelope.evidence_version,
        "evidence_id": envelope.evidence_id,
        "proof": hatp_proof_to_document(envelope.proof),
        "provider_assertion": base64.b64encode(envelope.provider_assertion).decode("ascii"),
    }
    return json.dumps(
        document,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
