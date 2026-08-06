"""HATP Proof Models + Canonical Serialization -- Phase 149O.1G, Wave 3.

Implements HATP-REQ-067..077 and HATP-REQ-117: the
`HumanApprovalProvenanceProof` artifact's typed shape, `proof_version`
versioning, strict/closed structural parsing (F-149O.1C-1 hardening --
unknown fields fail closed), and deterministic canonical serialization +
digest of the canonical signed payload (HATP-REQ-075).

Mandatory boundary, restated verbatim from the governing phase prompt and
HATP-001 itself:

    Successful HATP proof parsing and canonicalization establish only
    structural conformance. They do not establish signer authenticity,
    human presence, device attestation, authorization, repository
    deployment validity, freshness, revocation status, or trusted
    approval provenance.

This module therefore:

- performs NO signature/assertion verification;
- performs NO attestation verification;
- performs NO trust-store/registry lookup (no import of
  `hatp_bootstrap.py`'s `HATPTrustStore` or any lookup/resolution
  function);
- defines NO verification-status vocabulary (`VALID`, `UNKNOWN_SIGNER`,
  ... -- HATP-REQ-078's closed 13-state vocabulary belongs to a future
  Wave 4 verifier, not this module);
- derives no `approval_present` value and sets no HATP-wide "trusted"/
  "operational" flag;
- has no filesystem, network, hardware, or wall-clock ("now") dependency
  -- proof parsing and canonicalization are pure, deterministic
  functions of their input.

Field set: HATP-REQ-069's canonical payload lists no signature/assertion/
envelope field, so this module models the *entire* signed payload with
no separate envelope-vs-payload split (there is nothing to split; a
future Wave 5 provider adapter is responsible for whatever
provider-specific envelope wraps this payload's bytes, per 149O.1D plan
§47). The payload is also flat -- HATP-REQ-069 defines no nested object
-- so "closed nested schema" enforcement has no separate nested layer to
apply beyond the top-level closed field set enforced here.

Dependency direction: this module imports only
`repository_identity.is_valid_repository_instance_id` (a pure format
check, no authority claim, per 149O.1D plan §6 "read-only dependency on
repository identity type/helper only if necessary"). It does not import
`hatp_bootstrap.py`, `rollback_approval_evidence.py`,
`permission_broker*.py`, `agent.py`, or `commands/agent.py`.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Union

from pcae.core.repository_identity import is_valid_repository_instance_id

#: HATP-REQ-068: this contract freezes `proof_version = 1` as the only
#: version HATP-001 v1.0 defines. An unknown/future version SHALL be
#: rejected outright (HATP-REQ-117), never best-effort parsed.
SUPPORTED_PROOF_VERSIONS = frozenset({1})

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class HATPProofError(Exception):
    """Base error for HATP proof parsing/canonicalization. Structural
    vocabulary only (§58 of the governing prompt) -- never a HATP
    verification-status name (`VALID`, `UNKNOWN_SIGNER`, ...), which
    belongs to a future verifier, not this module."""


class MalformedProofError(HATPProofError):
    """The input is not well-formed JSON, is not a JSON object, or
    contains a duplicate JSON object key at any nesting level."""


class UnsupportedProofVersionError(HATPProofError):
    """`proof_version` is absent, not an integer, or not a member of
    `SUPPORTED_PROOF_VERSIONS`. Never ignored for forward compatibility
    (HATP-REQ-117)."""


class InvalidProofSchemaError(HATPProofError):
    """The document is a well-formed JSON object with a supported
    `proof_version`, but fails HATP's closed structural schema: an
    unrecognized field, a missing required field, a field belonging to
    the wrong operation family, or a field that fails its own structural
    format check."""


class RollbackSite(str, Enum):
    """HATP-REQ-069's `rollback_site` discriminant. Family-locked per
    RAE-REQ-020/021: an AG3 proof MUST carry only AG3 operation fields,
    an AG5 proof MUST carry only AG5 operation fields -- enforced by
    `_build_proof_from_document` and `HumanApprovalProvenanceProof.__post_init__`,
    never by optional-field soup (§19 of the governing prompt)."""

    AG3 = "AG3"
    AG5 = "AG5"


@dataclass(frozen=True)
class Ag3OperationReference:
    """Required exactly when `rollback_site == AG3` (HATP-REQ-069),
    mirroring RAE-001's own `Ag3OperationReference` field names
    (`rollback_approval_evidence.py`) by reference, not by import."""

    job_id: str
    original_commit_sha: str


@dataclass(frozen=True)
class Ag5OperationReference:
    """Required exactly when `rollback_site == AG5` (HATP-REQ-069)."""

    per_id: str
    ecp_id: str


@dataclass(frozen=True)
class HumanApprovalProvenanceProof:
    """The HATP proof artifact (HATP-REQ-067), distinct from the CHGR
    Decision, the RAE Binding, and the Permission Broker decision.

    This type represents *structural* conformance only. An instance of
    this class asserts nothing about signer authenticity, human
    presence, device attestation, repository authorization, or
    freshness -- see the module docstring's mandatory boundary
    statement."""

    proof_version: int
    principal_id: str
    signer_key_id: str
    provider_profile: str
    repository_id: str
    decision_record_id: str
    decision_record_digest: str
    binding_id: str
    binding_digest: str
    rollback_site: RollbackSite
    operation_reference: Union[Ag3OperationReference, Ag5OperationReference]
    issued_at: str

    def __post_init__(self) -> None:
        if self.rollback_site is RollbackSite.AG3 and not isinstance(self.operation_reference, Ag3OperationReference):
            raise InvalidProofSchemaError(
                "HumanApprovalProvenanceProof.operation_reference must be an Ag3OperationReference "
                f"when rollback_site=AG3, got {type(self.operation_reference).__name__}"
            )
        if self.rollback_site is RollbackSite.AG5 and not isinstance(self.operation_reference, Ag5OperationReference):
            raise InvalidProofSchemaError(
                "HumanApprovalProvenanceProof.operation_reference must be an Ag5OperationReference "
                f"when rollback_site=AG5, got {type(self.operation_reference).__name__}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# Timestamp handling -- duplicated deliberately, not imported, from
# `repository_identity.py` / `hatp_bootstrap.py` / `rollback_approval_
# evidence.py::_parse_iso_timestamp` (149O.1D plan §5.13/§39), to avoid
# reintroducing the Python 3.9 `fromisoformat` Z-suffix portability
# defect and to keep this module's only upstream dependency
# `repository_identity.py` (§6 dependency-direction rule).
# ═══════════════════════════════════════════════════════════════════════════


def _parse_iso_timestamp(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        text = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _canonical_timestamp_string(parsed: datetime) -> str:
    """One canonical UTC rendering (§21/§79 of the governing prompt),
    millisecond precision, matching `repository_identity.py`'s own
    `_generate_repository_identity` format exactly. Applied at parse
    time so that two structurally-equivalent but differently-formatted
    input timestamps (e.g. explicit `+00:00` offset vs. `Z` suffix,
    differing fractional-second precision) canonicalize identically."""

    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ═══════════════════════════════════════════════════════════════════════════
# Duplicate-JSON-key-rejecting strict loader (§34/§104 of the governing
# prompt). Standard library `json.loads` silently accepts duplicate
# object keys ("last wins"); that ambiguity is rejected here rather than
# reused, at every nesting level, via `object_pairs_hook`.
# ═══════════════════════════════════════════════════════════════════════════


def _reject_duplicate_keys(pairs: list) -> dict:
    seen: set = set()
    result: dict = {}
    for key, value in pairs:
        if key in seen:
            raise MalformedProofError(f"duplicate JSON object key: {key!r}")
        seen.add(key)
        result[key] = value
    return result


def _load_json_no_duplicate_keys(raw: Union[str, bytes]) -> object:
    try:
        return json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise MalformedProofError(f"proof document is not valid JSON: {exc}") from exc


# ═══════════════════════════════════════════════════════════════════════════
# Field-level structural validators
# ═══════════════════════════════════════════════════════════════════════════


def _require_nonempty_str(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidProofSchemaError(f"{context}: expected a non-empty string, got {value!r}")
    return value


def _require_sha256_hex(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _SHA256_HEX_RE.fullmatch(value):
        raise InvalidProofSchemaError(f"{context}: expected a lowercase 64-character hex SHA-256 digest, got {value!r}")
    return value


def _require_commit_sha(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _COMMIT_SHA_RE.fullmatch(value):
        raise InvalidProofSchemaError(
            f"{context}: expected a 40- or 64-character lowercase hex Git commit SHA, got {value!r}"
        )
    return value


# ═══════════════════════════════════════════════════════════════════════════
# Closed field-set definitions (F-149O.1C-1 hardening: unknown fields,
# and fields belonging to the wrong operation family, are rejected --
# `additionalProperties: false`-equivalent strict typed parsing, mirroring
# the same pattern already used by the verified Wave-2 sibling module,
# `hatp_bootstrap.py`'s `_parse_*` functions).
# ═══════════════════════════════════════════════════════════════════════════

_COMMON_FIELDS = frozenset(
    {
        "proof_version",
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
    }
)
_AG3_ONLY_FIELDS = frozenset({"job_id", "original_commit_sha"})
_AG5_ONLY_FIELDS = frozenset({"per_id", "ecp_id"})


def _build_proof_from_document(document: object) -> HumanApprovalProvenanceProof:
    """Validate and construct a `HumanApprovalProvenanceProof` from an
    already-parsed JSON object (`dict`). Callers requiring duplicate-key
    rejection MUST go through `parse_hatp_proof`, which parses raw JSON
    text via `_load_json_no_duplicate_keys` before calling this
    function -- this function itself does not re-parse raw text, and
    does not, by itself, defend against duplicate keys already collapsed
    by an ordinary `json.loads` call upstream."""

    if not isinstance(document, dict):
        raise InvalidProofSchemaError("proof document is not a JSON object")

    proof_version = document.get("proof_version")
    if not isinstance(proof_version, int) or isinstance(proof_version, bool):
        raise UnsupportedProofVersionError(f"proof_version must be an integer, got {proof_version!r}")
    if proof_version not in SUPPORTED_PROOF_VERSIONS:
        raise UnsupportedProofVersionError(f"unsupported proof_version: {proof_version!r}")

    rollback_site_raw = document.get("rollback_site")
    if rollback_site_raw not in ("AG3", "AG5"):
        raise InvalidProofSchemaError(f"rollback_site must be 'AG3' or 'AG5', got {rollback_site_raw!r}")
    rollback_site = RollbackSite(rollback_site_raw)

    family_fields = _AG3_ONLY_FIELDS if rollback_site is RollbackSite.AG3 else _AG5_ONLY_FIELDS
    other_family_fields = _AG5_ONLY_FIELDS if rollback_site is RollbackSite.AG3 else _AG3_ONLY_FIELDS
    allowed = _COMMON_FIELDS | family_fields

    present = set(document.keys())

    wrong_family = present & other_family_fields
    if wrong_family:
        raise InvalidProofSchemaError(
            f"proof carries fields not valid for rollback_site={rollback_site.value}: {sorted(wrong_family)}"
        )

    unknown = present - allowed
    if unknown:
        raise InvalidProofSchemaError(f"proof document has unrecognized fields: {sorted(unknown)}")

    missing = allowed - present
    if missing:
        raise InvalidProofSchemaError(f"proof document is missing required fields: {sorted(missing)}")

    principal_id = _require_nonempty_str(document.get("principal_id"), context="principal_id")
    signer_key_id = _require_nonempty_str(document.get("signer_key_id"), context="signer_key_id")
    provider_profile = _require_nonempty_str(document.get("provider_profile"), context="provider_profile")

    repository_id = document.get("repository_id")
    if not is_valid_repository_instance_id(repository_id):
        raise InvalidProofSchemaError(f"repository_id is not a valid UUID4 string, got {repository_id!r}")

    decision_record_id = _require_nonempty_str(document.get("decision_record_id"), context="decision_record_id")
    decision_record_digest = _require_sha256_hex(document.get("decision_record_digest"), context="decision_record_digest")
    binding_id = _require_nonempty_str(document.get("binding_id"), context="binding_id")
    binding_digest = _require_sha256_hex(document.get("binding_digest"), context="binding_digest")

    issued_at_parsed = _parse_iso_timestamp(document.get("issued_at"))
    if issued_at_parsed is None:
        raise InvalidProofSchemaError(
            f"issued_at is not a valid timezone-aware ISO-8601 timestamp, got {document.get('issued_at')!r}"
        )
    issued_at = _canonical_timestamp_string(issued_at_parsed)

    operation_reference: Union[Ag3OperationReference, Ag5OperationReference]
    if rollback_site is RollbackSite.AG3:
        job_id = _require_nonempty_str(document.get("job_id"), context="job_id")
        original_commit_sha = _require_commit_sha(document.get("original_commit_sha"), context="original_commit_sha")
        operation_reference = Ag3OperationReference(job_id=job_id, original_commit_sha=original_commit_sha)
    else:
        per_id = _require_nonempty_str(document.get("per_id"), context="per_id")
        ecp_id = _require_nonempty_str(document.get("ecp_id"), context="ecp_id")
        operation_reference = Ag5OperationReference(per_id=per_id, ecp_id=ecp_id)

    return HumanApprovalProvenanceProof(
        proof_version=proof_version,
        principal_id=principal_id,
        signer_key_id=signer_key_id,
        provider_profile=provider_profile,
        repository_id=repository_id,
        decision_record_id=decision_record_id,
        decision_record_digest=decision_record_digest,
        binding_id=binding_id,
        binding_digest=binding_digest,
        rollback_site=rollback_site,
        operation_reference=operation_reference,
        issued_at=issued_at,
    )


def parse_hatp_proof(raw: Union[str, bytes]) -> HumanApprovalProvenanceProof:
    """Parse raw JSON text into a `HumanApprovalProvenanceProof`.

    Structural parsing only (§163 of the governing prompt): a successful
    return value means the input is well-formed, duplicate-key-free
    JSON conforming to HATP's closed proof schema for a supported
    `proof_version` -- nothing more. It does NOT mean the proof is
    signed, trusted, authorized, or otherwise `VALID` in HATP-REQ-078's
    sense."""

    document = _load_json_no_duplicate_keys(raw)
    return _build_proof_from_document(document)


# ═══════════════════════════════════════════════════════════════════════════
# Canonical serialization (HATP-REQ-075) + canonical digest
# ═══════════════════════════════════════════════════════════════════════════


def hatp_proof_to_document(proof: HumanApprovalProvenanceProof) -> dict:
    """The proof's plain-`dict` JSON representation, in HATP-REQ-069's
    field names. Used both by `canonicalize_hatp_proof_payload` and by
    callers who need an ordinary JSON-serializable object (e.g. for a
    future Wave 5 provider to sign over, or a future Wave 6 persistence
    layer -- neither implemented here, §33-34/§62 of the governing
    prompt)."""

    document: dict = {
        "proof_version": proof.proof_version,
        "principal_id": proof.principal_id,
        "signer_key_id": proof.signer_key_id,
        "provider_profile": proof.provider_profile,
        "repository_id": proof.repository_id,
        "decision_record_id": proof.decision_record_id,
        "decision_record_digest": proof.decision_record_digest,
        "binding_id": proof.binding_id,
        "binding_digest": proof.binding_digest,
        "rollback_site": proof.rollback_site.value,
        "issued_at": proof.issued_at,
    }
    if isinstance(proof.operation_reference, Ag3OperationReference):
        document["job_id"] = proof.operation_reference.job_id
        document["original_commit_sha"] = proof.operation_reference.original_commit_sha
    else:
        document["per_id"] = proof.operation_reference.per_id
        document["ecp_id"] = proof.operation_reference.ecp_id
    return document


def canonicalize_hatp_proof_payload(proof: HumanApprovalProvenanceProof) -> bytes:
    """Deterministic canonical bytes of the signed payload (HATP-REQ-075):
    UTF-8, sorted keys, fixed separators, no insignificant whitespace, no
    locale dependence. Given an equal model, always produces identical
    bytes -- no random ID, no wall-clock "now" is generated here (§114
    of the governing prompt). Mirrors the existing project convention
    (`cltr/canonicalization.py::_canonical_bytes`,
    `rollback_approval_evidence.py::_canonical_bytes`) rather than
    inventing a new one."""

    document = hatp_proof_to_document(proof)
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest_hatp_proof_payload(proof: HumanApprovalProvenanceProof) -> str:
    """SHA-256 hex digest of the canonical signed payload, matching this
    project's existing plain-hex digest convention (no algorithm
    prefix), as used by `rollback_approval_evidence.py::
    _compute_content_digest` and CHGR's `record_digest`."""

    return hashlib.sha256(canonicalize_hatp_proof_payload(proof)).hexdigest()
