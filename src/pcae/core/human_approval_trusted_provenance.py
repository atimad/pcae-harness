"""HATP Proof Models + Canonical Serialization (Phase 149O.1G, Wave 3) +
Verification Engine (Phase 149O.1I, Wave 4).

Wave 4 addendum (read this before the Wave-3 boundary statement below,
which described this module's state *before* Wave 4 and is retained
verbatim for history): per the 149O.1D implementation plan's Module
Ownership Proposal (§7 -- "human_approval_trusted_provenance.py (G, H,
I, J -- proof model, serialization, verifier, readiness gate)"), the
verification engine (`verify_hatp_proof`, subsystem I) and the
substrate-readiness inspector (`inspect_hatp_verification_substrate_readiness`,
subsystem J) are co-located in this same module by explicit plan
decision, not organic scope creep. This is the one plan-sanctioned
exception to the otherwise-frozen Wave-3 boundary: this module now DOES
import `hatp_bootstrap.HATPTrustStore` (read-only; HATP-REQ-094) and
`hatp_providers.HATPProofVerifierProvider`. No Wave-3 symbol, field, or
behavior defined below this point is modified by Wave 4 -- every Wave-4
addition is new code appended after the Wave-3 content, per the
"HATP Verification Engine (Wave 4)" section marker further down.

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
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Tuple, Union

from pcae.core.hatp_bootstrap import HATPTrustStore, HATPTrustStoreError, deployment_binding_matches
from pcae.core.hatp_providers import HATPProofVerifierProvider, HATPProviderVerificationOutcome
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

    def __post_init__(self) -> None:
        _require_nonempty_str(self.job_id, context="job_id")
        _require_commit_sha(self.original_commit_sha, context="original_commit_sha")


@dataclass(frozen=True)
class Ag5OperationReference:
    """Required exactly when `rollback_site == AG5` (HATP-REQ-069)."""

    per_id: str
    ecp_id: str

    def __post_init__(self) -> None:
        _require_nonempty_str(self.per_id, context="per_id")
        _require_nonempty_str(self.ecp_id, context="ecp_id")


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
        """B-149O.1H-2 repair: direct construction now enforces the same
        structural security domain `parse_hatp_proof` enforces. This is
        the *only* place that domain is defined for typed construction --
        `parse_hatp_proof`/`_build_proof_from_document` calls the same
        shared `_require_*` validators (never a second, drifting
        semantic-validation path, per §22 of the governing prompt) before
        constructing this dataclass, so the check here is a redundant-
        but-authoritative gate for parser-built instances and the *only*
        gate for any other public construction path."""

        _require_proof_version(self.proof_version)
        _require_nonempty_str(self.principal_id, context="principal_id")
        _require_nonempty_str(self.signer_key_id, context="signer_key_id")
        _require_nonempty_str(self.provider_profile, context="provider_profile")
        _require_repository_instance_id(self.repository_id)
        _require_nonempty_str(self.decision_record_id, context="decision_record_id")
        _require_sha256_hex(self.decision_record_digest, context="decision_record_digest")
        _require_nonempty_str(self.binding_id, context="binding_id")
        _require_sha256_hex(self.binding_digest, context="binding_digest")
        rollback_site = _require_rollback_site(self.rollback_site)
        issued_at = _require_issued_at(self.issued_at, context="issued_at")

        if rollback_site is RollbackSite.AG3 and not isinstance(self.operation_reference, Ag3OperationReference):
            raise InvalidProofSchemaError(
                "HumanApprovalProvenanceProof.operation_reference must be an Ag3OperationReference "
                f"when rollback_site=AG3, got {type(self.operation_reference).__name__}"
            )
        if rollback_site is RollbackSite.AG5 and not isinstance(self.operation_reference, Ag5OperationReference):
            raise InvalidProofSchemaError(
                "HumanApprovalProvenanceProof.operation_reference must be an Ag5OperationReference "
                f"when rollback_site=AG5, got {type(self.operation_reference).__name__}"
            )

        # Frozen dataclass: normalize via `object.__setattr__` so that a
        # directly-constructed instance given the same value shapes the
        # parser accepts (a raw `"AG3"`/`"AG5"` string; a valid but
        # non-canonical `issued_at`, e.g. a `+01:00` offset form) stores
        # the identical canonical form the parser would have produced --
        # not a second, differently-shaped "valid" representation.
        object.__setattr__(self, "rollback_site", rollback_site)
        object.__setattr__(self, "issued_at", issued_at)


# ═══════════════════════════════════════════════════════════════════════════
# Timestamp handling -- duplicated deliberately, not imported, from
# `repository_identity.py` / `hatp_bootstrap.py` / `rollback_approval_
# evidence.py::_parse_iso_timestamp` (149O.1D plan §5.13/§39), to avoid
# reintroducing the Python 3.9 `fromisoformat` Z-suffix portability
# defect and to keep this module's only upstream dependency
# `repository_identity.py` (§6 dependency-direction rule).
# ═══════════════════════════════════════════════════════════════════════════


#: 149O.1H.5 repair (B-149O.1H.4-1): matches a fractional-seconds group
#: by locating the `.`/`,` that immediately follows the two-digit
#: `SS` seconds field (itself identified by the preceding `:`), rather
#: than by anchoring on which timezone-offset spelling follows the
#: fraction. The 149O.1H.3 predecessor of this regex anchored on `Z$`
#: or a colon-separated `[+-]\d{2}:\d{2}$` suffix; `datetime.
#: fromisoformat` on this interpreter also accepts non-colon offsets
#: (`+00`, `+0000`), a bare space date/time separator, and a `,`
#: decimal separator, none of which the old anchor covered -- each was
#: an independent bypass of the >6-fractional-digit rejection below.
#: Anchoring on the seconds field itself (`(?<=:\d{2})[.,]`) instead of
#: on the suffix makes fraction detection suffix-syntax-independent:
#: it matches regardless of what (if anything) follows the fraction,
#: and does not match at all when there is no `.`/`,` directly after
#: `SS` (so bare offset digits, e.g. `+0000`, are never miscounted as
#: fractional digits -- there is no separator character before them).
#: Used to reject raw lexical fractional-second precision that
#: `datetime.fromisoformat` cannot faithfully preserve (it silently
#: truncates to microseconds, i.e. 6 fractional digits) *before* that
#: lossy conversion ever runs -- inspecting `datetime.microsecond`
#: afterward is too late, the discarded digits are already gone by then.
_FRACTIONAL_SECONDS_RE = re.compile(r"(?<=:\d{2})[.,](\d+)")


def _reject_excess_fractional_precision(value: str, *, context: str) -> None:
    match = _FRACTIONAL_SECONDS_RE.search(value)
    if match is not None and len(match.group(1)) > 6:
        raise InvalidProofSchemaError(
            f"{context}: fractional-second precision exceeds 6 digits "
            f"(the most Python's datetime can represent without silent "
            f"truncation), got {value!r}"
        )


def _parse_iso_timestamp(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    _reject_excess_fractional_precision(value, context="issued_at")
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
    differing fractional-second precision) canonicalize identically.

    Only ever called on a `datetime` already accepted by
    `_require_issued_at` (`microsecond % 1000 == 0`), so slicing `%f`
    (six digits) down to three is exact truncation of trailing zeros,
    never a lossy rounding/collision -- see Phase 149O.1H.1's repair of
    B-149O.1H-1, which closed the sub-millisecond collision this
    function used to produce when called on unfiltered input."""

    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _require_issued_at(value: object, *, context: str = "issued_at") -> str:
    """Validate and canonicalize an `issued_at` value. Shared by
    `parse_hatp_proof` and `HumanApprovalProvenanceProof.__post_init__`
    (B-149O.1H-2 parser/constructor domain unification) so that no
    public construction path can produce a proof carrying a timestamp
    the parser would reject.

    HATP-001 (HATP-REQ-075) requires a *deterministic* canonical
    rendering; it does not mandate millisecond precision specifically.
    This module's canonical renderer emits exactly millisecond
    precision (matching `repository_identity.py`'s convention).
    Historically, `_parse_iso_timestamp` accepted -- and the renderer
    then silently truncated -- finer-grained (sub-millisecond) input,
    which made canonicalization many-to-one over the accepted domain
    (B-149O.1H-1: `.0001Z` and `.0009Z` both truncated to `.000Z`).
    Rather than round or otherwise collapse distinct instants, this
    validator narrows the *accepted* domain instead: any `issued_at`
    carrying non-zero fractional precision below one millisecond is
    rejected outright, before model acceptance, so canonicalization
    remains injective (distinct accepted instants -> distinct canonical
    strings) over the (now precisely millisecond-grained) accepted
    domain."""

    parsed = _parse_iso_timestamp(value)
    if parsed is None:
        raise InvalidProofSchemaError(
            f"{context}: not a valid timezone-aware ISO-8601 timestamp, got {value!r}"
        )
    if parsed.microsecond % 1000 != 0:
        raise InvalidProofSchemaError(
            f"{context}: sub-millisecond fractional-second precision is not accepted "
            f"(HATP v1 canonical timestamps are millisecond-precision), got {value!r}"
        )
    return _canonical_timestamp_string(parsed)


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


def _require_proof_version(value: object) -> int:
    """Shared by `parse_hatp_proof` and `HumanApprovalProvenanceProof.
    __post_init__` (B-149O.1H-2). `isinstance(value, int)` alone is
    insufficient -- `bool` is an `int` subclass in Python, so
    `isinstance(True, int)` is `True` -- hence the explicit,
    independent `isinstance(value, bool)` exclusion (HATP-REQ-068/117:
    an unsupported/malformed version is never best-effort accepted)."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise UnsupportedProofVersionError(f"proof_version must be an integer, got {value!r}")
    if value not in SUPPORTED_PROOF_VERSIONS:
        raise UnsupportedProofVersionError(f"unsupported proof_version: {value!r}")
    return value


def _require_repository_instance_id(value: object) -> str:
    """Shared by `parse_hatp_proof` and `HumanApprovalProvenanceProof.
    __post_init__` (B-149O.1H-2). Format-only check (no normalization --
    §57 of the governing prompt: an accepted uppercase-lexical-variant
    UUID string is retained verbatim, not opportunistically
    canonicalized, since that is a separate, non-blocking observation
    out of this phase's narrow scope)."""

    if not is_valid_repository_instance_id(value):
        raise InvalidProofSchemaError(f"repository_id is not a valid UUID4 string, got {value!r}")
    return value


def _require_rollback_site(value: object) -> RollbackSite:
    """Shared by `parse_hatp_proof` and `HumanApprovalProvenanceProof.
    __post_init__` (B-149O.1H-2). Accepts either an already-typed
    `RollbackSite` member (the parser's own call shape) or its exact
    string value (`"AG3"`/`"AG5"`, the shape a direct caller building a
    proof from untyped input might reasonably pass); anything else,
    including an unrecognized family string, is rejected."""

    if isinstance(value, RollbackSite):
        return value
    if isinstance(value, str):
        try:
            return RollbackSite(value)
        except ValueError:
            pass
    raise InvalidProofSchemaError(f"rollback_site must be 'AG3' or 'AG5', got {value!r}")


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

    proof_version = _require_proof_version(document.get("proof_version"))

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

    repository_id = _require_repository_instance_id(document.get("repository_id"))

    decision_record_id = _require_nonempty_str(document.get("decision_record_id"), context="decision_record_id")
    decision_record_digest = _require_sha256_hex(document.get("decision_record_digest"), context="decision_record_digest")
    binding_id = _require_nonempty_str(document.get("binding_id"), context="binding_id")
    binding_digest = _require_sha256_hex(document.get("binding_digest"), context="binding_digest")

    issued_at = _require_issued_at(document.get("issued_at"), context="issued_at")

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


# ═══════════════════════════════════════════════════════════════════════════
# HATP Verification Engine (Phase 149O.1I, Wave 4)
#
# Mandatory boundary, restated verbatim from the governing phase prompt
# and HATP-001 itself:
#
#     A HATP verification status answers only "is this evidence
#     authentic, trusted, and bound to the exact claimed operation?". It
#     is not an approval, not a permission decision, not an execution
#     authorization, and never itself sets `approval_present=True`. No
#     call site in this phase wires this engine's output into RAE, the
#     Permission Broker, rollback execution, or agent invocation.
#
# This section:
#
# - defines HATP-REQ-078's closed 13-state verification-status vocabulary
#   (`HATPVerificationStatus`) verbatim from the frozen contract text --
#   no status added, omitted, renamed, or aliased;
# - defines an immutable `HATPVerificationResult` carrying only `status`
#   and non-secret diagnostic `reasons` -- no `approved`/`authorized`/
#   `valid`/`can_execute`/`permission` field exists anywhere in this
#   section;
# - defines `verify_hatp_proof`, which consumes a Wave-3
#   `HumanApprovalProvenanceProof`, the Wave-3 canonical payload (via
#   `canonicalize_hatp_proof_payload` -- never rebuilt independently), a
#   provider-neutral `HATPProofVerifierProvider` (`hatp_providers.py`),
#   and the read-only Wave-2 `HATPTrustStore`, and returns exactly one
#   `HATPVerificationResult`;
# - defines `inspect_hatp_verification_substrate_readiness`, which
#   reports on the software substrate this wave can mechanically observe
#   -- explicitly and permanently unable to report "operational", because
#   Wave 5 (real hardware provider) and Wave 6 (RAE integration) do not
#   exist yet.
#
# Scope deliberately excluded from this wave (documented, not silently
# omitted): live re-fetch of the current CHGR Decision / RAE Binding
# content to freshly recompute `decision_record_digest`/`binding_digest`
# against post-signing mutation (HATP-REQ-072/073). Those digests are
# already part of the *signed* canonical payload (HATP-REQ-069, Wave 3),
# so any post-signing mutation of the *proof's own* digest fields is
# already caught by signature verification below (§ mutation-sensitivity
# tests). Comparing against a freshly-recomputed digest of the *live*
# Decision/Binding record requires importing `rollback_approval_evidence.py`
# / CHGR, which the 149O.1D plan assigns to Wave 6 (RAE Integration,
# HATP-REQ-095/096's AND-conjunction) -- not Wave 4. This module still
# imports neither module (dependency-direction audit, § in the phase
# report).
# ═══════════════════════════════════════════════════════════════════════════


class HATPVerificationStatus(str, Enum):
    """HATP-REQ-078's closed verification-status vocabulary, reproduced
    verbatim from the frozen contract text (HATP-001 §22). This
    vocabulary SHALL NOT be extended informally, and SHALL NOT reuse
    Permission Broker (`ALLOW`/`DENY`/`HUMAN_REVIEW`) or RAE-001
    (`VALID | MISSING | INVALID | STALE | REVOKED | UNAUTHORIZED_APPROVER
    | WRONG_SCOPE | SUPERSEDED`) vocabulary -- the three vocabularies are
    structurally distinct types and MUST NOT be conflated."""

    VALID = "VALID"
    MISSING = "MISSING"
    MALFORMED = "MALFORMED"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    UNKNOWN_SIGNER = "UNKNOWN_SIGNER"
    UNAUTHORIZED_SIGNER = "UNAUTHORIZED_SIGNER"
    REVOKED_SIGNER = "REVOKED_SIGNER"
    INVALID_ATTESTATION = "INVALID_ATTESTATION"
    USER_PRESENCE_NOT_PROVEN = "USER_PRESENCE_NOT_PROVEN"
    WRONG_OPERATION = "WRONG_OPERATION"
    WRONG_REPOSITORY = "WRONG_REPOSITORY"
    WRONG_DEPLOYMENT = "WRONG_DEPLOYMENT"
    EXPIRED = "EXPIRED"


#: The complete frozen vocabulary, for exhaustiveness testing (§54 of the
#: governing prompt) without relying on `Enum.__members__` ordering.
HATP_VERIFICATION_STATUS_VALUES = frozenset(status.value for status in HATPVerificationStatus)


@dataclass(frozen=True)
class HATPVerificationResult:
    """The sole output of `verify_hatp_proof`. Immutable, and carries
    only evidence-authenticity/trust facts (HATP-REQ-079) -- never an
    approval, permission, or execution-authorization field. A caller
    wanting to act on `status == HATPVerificationStatus.VALID` still
    needs independent RAE-001 evidence and a fresh Permission Broker
    `ALLOW` (HATP-REQ-005, HATP-REQ-104); this type supplies none of
    those."""

    status: HATPVerificationStatus
    #: Non-secret diagnostic reason codes (never private-key material,
    #: raw protected trust-store content, or credential secrets --
    #: HATP-REQ-094 verifier-side read-only discipline extends to what
    #: this result is permitted to disclose).
    reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class HATPVerificationEvidence:
    """The outer evidence envelope Wave 4 verifies against the Wave-3
    canonical signed payload (§31-32 of the governing prompt). Binds
    provider-specific assertion bytes to a proof without modifying
    `HumanApprovalProvenanceProof`'s own shape or `canonicalize_hatp_proof_payload`'s
    signed-payload semantics. Deliberately carries exactly one
    `assertion` field (never a list) -- HATP-001 defines no multi-
    signature semantics, so ambiguous/duplicate evidence is fail-closed
    *by construction*, not by a runtime "pick first valid" branch."""

    assertion: bytes


@dataclass(frozen=True)
class HATPExpectedOperation:
    """The concrete operation a caller is currently attempting to
    authorize (HATP-REQ-069/071/083): a valid proof produced for a
    *different* operation must verify as `WRONG_OPERATION` even though
    its signature remains internally valid over its own original
    payload. Comparison is by value against the proof's own operation
    fields -- never re-derived from the proof itself (that would make
    `WRONG_OPERATION` unreachable by construction)."""

    decision_record_id: str
    binding_id: str
    rollback_site: RollbackSite
    operation_reference: Union[Ag3OperationReference, Ag5OperationReference]


#: HATP-REQ-085: a future-dated `issued_at` beyond an implementation-
#: defined clock-skew tolerance is `EXPIRED`. HATP-001 does not freeze an
#: exact tolerance value; 60 seconds is this implementation's documented,
#: non-normative choice (recorded as an OBSERVATION in the phase report,
#: not claimed as contract-mandated).
HATP_CLOCK_SKEW_TOLERANCE = timedelta(seconds=60)


def _verification_result(status: HATPVerificationStatus, *reasons: str) -> HATPVerificationResult:
    return HATPVerificationResult(status=status, reasons=tuple(reasons))


def _operation_matches(proof: HumanApprovalProvenanceProof, expected: HATPExpectedOperation) -> bool:
    if proof.decision_record_id != expected.decision_record_id:
        return False
    if proof.binding_id != expected.binding_id:
        return False
    if proof.rollback_site != expected.rollback_site:
        return False
    return proof.operation_reference == expected.operation_reference


def verify_hatp_proof(
    proof: Optional[HumanApprovalProvenanceProof],
    *,
    evidence: HATPVerificationEvidence,
    provider: HATPProofVerifierProvider,
    trust_store: HATPTrustStore,
    expected_operation: HATPExpectedOperation,
    current_repository_id: str,
    canonical_deployment_root: str,
    evaluation_time: datetime,
) -> HATPVerificationResult:
    """Verify a `HumanApprovalProvenanceProof` against provider-supplied
    cryptographic evidence and protected Wave-2 trust-store state
    (HATP-REQ-077..085, HATP-REQ-094).

    Fail-closed discipline (HATP-REQ-090-093): every unexpected
    exception, unknown/malformed provider result, missing trust
    binding, or ambiguous input resolves to an explicit non-`VALID`
    `HATPVerificationResult` -- never to a `VALID` result and never to a
    propagated exception. `evaluation_time` MUST be supplied explicitly
    by the caller (never `datetime.now()` internally, § no-hidden-wall-
    clock discipline) so verification remains a pure, replayable function
    of its inputs (HATP-REQ-042 determinism).

    Ordering note: HATP-REQ-079 states the full success conjunction as an
    unordered AND-list ("every applicable term succeeds, conjunctively,
    with no partial success") -- it does not mandate a specific failure
    *precedence* when multiple terms fail simultaneously. The order below
    is this implementation's deterministic, documented, non-normative
    choice (recorded as an OBSERVATION in the phase report, not claimed
    as contract-mandated), structured to fail closed as early as possible
    on the cheapest / most fundamental checks first.
    """

    if proof is None:
        return _verification_result(HATPVerificationStatus.MISSING, "no_proof_supplied")
    if not isinstance(proof, HumanApprovalProvenanceProof):
        return _verification_result(HATPVerificationStatus.MALFORMED, "not_a_hatp_proof_instance")
    if proof.proof_version not in SUPPORTED_PROOF_VERSIONS:
        # Structurally unreachable through normal construction (Wave-3
        # `__post_init__` already rejects this) -- defensive fail-closed
        # only, per § malformed-typed-object-assumption.
        return _verification_result(HATPVerificationStatus.MALFORMED, "unsupported_proof_version")

    # HATP-REQ-042: bootstrap state genuinely absent (never merely
    # "signer not enrolled in an existing registry") is `MISSING`, not
    # `UNKNOWN_SIGNER` -- checked via `environment_status()` specifically
    # for its `UNAVAILABLE` case, which fires only when the registry file
    # itself does not exist. This is deliberately narrower than checking
    # for `READY`: `UNSAFE_CONFIGURATION` (e.g. this development machine's
    # same-OS-principal topology) is a *substrate-readiness* concern
    # (`inspect_hatp_verification_substrate_readiness`, below), not a
    # per-proof verification concern -- HATP-001's own 20-attack matrix
    # (attack #20) requires a legitimate proof to be able to reach
    # `VALID` in a controlled test/verification context even when the
    # broader deployment is not production-safe (§52 of the governing
    # prompt: "a cryptographically valid proof under a test context does
    # not override unsafe deployment topology" -- for the *readiness*
    # question, not the *per-proof* question).
    try:
        environment = trust_store.environment_status()
    except HATPTrustStoreError:
        return _verification_result(HATPVerificationStatus.MISSING, "trust_store_unavailable")
    if environment.status.value == "UNAVAILABLE":
        return _verification_result(HATPVerificationStatus.MISSING, "trust_store_missing")

    try:
        signer = trust_store.lookup_signer(proof.signer_key_id)
    except HATPTrustStoreError:
        return _verification_result(HATPVerificationStatus.MISSING, "trust_store_unavailable")

    if signer is None:
        return _verification_result(HATPVerificationStatus.UNKNOWN_SIGNER, "signer_key_id_not_enrolled")

    # HATP-REQ-088: authority MUST remain valid at proof-*consumption*
    # time, not merely at proof-creation time -- checked here, as early
    # as possible, so a revoked signer never reaches signature/presence/
    # attestation evaluation below.
    if signer.status == "revoked":
        return _verification_result(HATPVerificationStatus.REVOKED_SIGNER, "signer_key_revoked")

    # HATP-REQ-077: signer trust resolves through the protected registry,
    # never through the proof's own claim. `proof.principal_id` and
    # `proof.provider_profile` are self-asserted (§25-28 self-selection
    # attacks) -- they are cross-checked against the registry's binding
    # for this exact `signer_key_id`, never trusted on their own.
    if signer.principal_id != proof.principal_id:
        return _verification_result(HATPVerificationStatus.UNKNOWN_SIGNER, "principal_id_does_not_match_registered_signer")
    if signer.provider_profile != proof.provider_profile:
        return _verification_result(HATPVerificationStatus.UNAUTHORIZED_SIGNER, "provider_profile_does_not_match_registered_signer")

    try:
        canonical_payload = canonicalize_hatp_proof_payload(proof)
        outcome = provider.verify(
            canonical_payload=canonical_payload,
            signer_key_id=proof.signer_key_id,
            provider_profile=proof.provider_profile,
            assertion=evidence.assertion,
        )
    except Exception:  # noqa: BLE001 -- provider failure MUST fail closed, never propagate/pass
        return _verification_result(HATPVerificationStatus.INVALID_SIGNATURE, "provider_verification_raised")

    if not isinstance(outcome, HATPProviderVerificationOutcome):
        return _verification_result(HATPVerificationStatus.INVALID_SIGNATURE, "provider_returned_unrecognized_result")

    if not outcome.signature_valid:
        return _verification_result(HATPVerificationStatus.INVALID_SIGNATURE, "signature_assertion_invalid")

    # HATP-REQ-016..018: fresh human presence is required per proof; a
    # cryptographically valid signature without proven presence is never
    # promoted to VALID.
    if not outcome.human_presence_proven:
        return _verification_result(HATPVerificationStatus.USER_PRESENCE_NOT_PROVEN, "human_presence_not_proven")

    # HATP-REQ-023-025: attestation, where the provider evaluates it,
    # establishes device/provider class only -- but a `False` result is
    # still fail-closed. `None` means this provider profile performs no
    # attestation check (real vendor attestation binding is Wave 5).
    if outcome.attestation_valid is False:
        return _verification_result(HATPVerificationStatus.INVALID_ATTESTATION, "attestation_invalid")

    try:
        principal = trust_store.lookup_principal(signer.principal_id)
        authority = trust_store.lookup_authority(signer.principal_id, proof.repository_id)
    except HATPTrustStoreError:
        return _verification_result(HATPVerificationStatus.MISSING, "trust_store_unavailable")

    if principal is None or principal.status != "active":
        return _verification_result(HATPVerificationStatus.UNAUTHORIZED_SIGNER, "principal_not_active")
    if authority is None or authority.status != "active":
        return _verification_result(HATPVerificationStatus.UNAUTHORIZED_SIGNER, "authority_not_active_for_repository")

    # HATP-REQ-081/082: cross-repository / same-ID-wrong-deployment replay.
    if proof.repository_id != current_repository_id:
        return _verification_result(HATPVerificationStatus.WRONG_REPOSITORY, "repository_id_mismatch")

    try:
        binding = trust_store.resolve_deployment_authorization(
            repository_id=proof.repository_id,
            canonical_deployment_root=canonical_deployment_root,
        )
    except HATPTrustStoreError:
        return _verification_result(HATPVerificationStatus.MISSING, "trust_store_unavailable")

    if binding is None:
        return _verification_result(HATPVerificationStatus.WRONG_DEPLOYMENT, "no_matching_deployment_binding")
    if not deployment_binding_matches(
        binding, repository_id=proof.repository_id, canonical_deployment_root=canonical_deployment_root
    ):
        return _verification_result(HATPVerificationStatus.WRONG_DEPLOYMENT, "deployment_binding_mismatch")
    if binding.principal_id != signer.principal_id or binding.signer_key_id != proof.signer_key_id or binding.provider_profile != proof.provider_profile:
        return _verification_result(HATPVerificationStatus.WRONG_DEPLOYMENT, "deployment_binding_does_not_authorize_this_signer")

    # HATP-REQ-069/071/083: exact operation identity binding.
    if not _operation_matches(proof, expected_operation):
        return _verification_result(HATPVerificationStatus.WRONG_OPERATION, "operation_identity_mismatch")

    # HATP-REQ-085: future-dated proof, beyond clock-skew tolerance.
    issued_at_parsed = _parse_iso_timestamp(proof.issued_at)
    if issued_at_parsed is None:
        return _verification_result(HATPVerificationStatus.MALFORMED, "issued_at_unparseable")
    if issued_at_parsed > evaluation_time + HATP_CLOCK_SKEW_TOLERANCE:
        return _verification_result(HATPVerificationStatus.EXPIRED, "issued_at_future_dated")

    return _verification_result(HATPVerificationStatus.VALID)


# ═══════════════════════════════════════════════════════════════════════════
# Verification-Substrate Readiness (Phase 149O.1I, Wave 4, subsystem J)
# ═══════════════════════════════════════════════════════════════════════════


class HATPVerificationSubstrateStatus(str, Enum):
    """Deliberately distinct vocabulary from `HATPVerificationStatus`
    (per-proof result) and from `hatp_bootstrap.BootstrapEnvironmentStatus`
    (Wave-2 registry/OS-permission facts alone). This status answers a
    different question: "could this deployment, as observed right now,
    ever produce a `VALID` `HATPVerificationResult` for a real production
    proof?" -- and always answers `NOT_READY` in this phase, because two
    of the 149O.1D plan §9 activation-conjunction terms
    (`provider_profile_available`, `provider_attestation_trusted`) have
    no Wave-4 implementation; only Wave 5 (real hardware provider) can
    make them true. There is deliberately no `READY` member defined by
    this wave -- see the module docstring and HATP-REQ-108/§37's frozen
    current-deployment-readiness statement."""

    NOT_READY = "NOT_READY"


@dataclass(frozen=True)
class HATPVerificationSubstrateReadiness:
    """Read-only inspection result. `operational` is always `False` in
    this phase -- it exists as a named field (rather than being
    hardcoded away entirely) so that a *future* Wave 5/6 change is
    mechanically forced to touch this one function's conjunction logic,
    rather than a caller silently assuming readiness once a provider
    happens to exist."""

    status: HATPVerificationSubstrateStatus
    operational: bool
    #: The 149O.1D plan §9 activation conjunction, term-by-term, as
    #: observed by this wave. `provider_profile_available` and
    #: `provider_attestation_trusted` are permanently `False` here --
    #: Wave 4 implements no real provider (HATP-REQ-021, no software-key
    #: downgrade; real providers are Wave 5 scope).
    terms: Tuple[Tuple[str, bool], ...]
    reasons: Tuple[str, ...]


def inspect_hatp_verification_substrate_readiness(
    trust_store: HATPTrustStore,
    *,
    current_repository_id: str,
) -> HATPVerificationSubstrateReadiness:
    """Inspect the software substrate this wave can mechanically observe
    (149O.1D plan §9's activation conjunction). This function NEVER
    returns `operational=True` -- Wave 5 (real hardware provider) and
    Wave 6 (RAE integration) do not exist yet, so
    `provider_profile_available` and `provider_attestation_trusted` are
    unconditionally `False`, which alone makes the conjunction fail
    regardless of trust-store state. This mechanically enforces
    HATP-REQ-108/§37 ("HATP production remains NOT READY") rather than
    merely asserting it in prose -- there is no parameter on this
    function, and no code path anywhere in this module, capable of
    forcing `operational=True`.
    """

    reasons: list = []

    repository_identity_valid = is_valid_repository_instance_id(current_repository_id)
    if not repository_identity_valid:
        reasons.append("current_repository_id_invalid")

    try:
        environment = trust_store.environment_status()
    except HATPTrustStoreError:
        environment = None
        reasons.append("trust_store_environment_status_unavailable")

    class_b_bootstrap_environment_safe = environment is not None and environment.status.value == "READY"
    if not class_b_bootstrap_environment_safe:
        reasons.append("class_b_bootstrap_environment_not_safe")
        if environment is not None:
            reasons.extend(f"bootstrap:{reason}" for reason in environment.reasons)

    protected_deployment_enrollment_valid = False
    trusted_approver_mapping_valid = False
    if repository_identity_valid:
        try:
            binding = trust_store.load_repository_enrollment(current_repository_id)
        except HATPTrustStoreError:
            binding = None
            reasons.append("trust_store_enrollment_lookup_unavailable")
        if binding is not None and binding.status == "active":
            protected_deployment_enrollment_valid = True
            try:
                authority = trust_store.lookup_authority(binding.principal_id, current_repository_id)
            except HATPTrustStoreError:
                authority = None
                reasons.append("trust_store_authority_lookup_unavailable")
            trusted_approver_mapping_valid = authority is not None and authority.status == "active"
    if not protected_deployment_enrollment_valid:
        reasons.append("protected_deployment_enrollment_not_valid")
    if not trusted_approver_mapping_valid:
        reasons.append("trusted_approver_mapping_not_valid")

    # Permanently unimplemented until Wave 5/6 (documented above, not a
    # silent omission).
    provider_profile_available = False
    provider_attestation_trusted = False
    reasons.append("no_production_verification_provider_implemented_until_wave_5")

    proof_verifier_available = True  # this wave

    terms = (
        ("repository_identity_valid", repository_identity_valid),
        ("protected_deployment_enrollment_valid", protected_deployment_enrollment_valid),
        ("class_b_bootstrap_environment_safe", class_b_bootstrap_environment_safe),
        ("trusted_approver_mapping_valid", trusted_approver_mapping_valid),
        ("provider_profile_available", provider_profile_available),
        ("provider_attestation_trusted", provider_attestation_trusted),
        ("proof_verifier_available", proof_verifier_available),
    )
    operational = all(value for _name, value in terms)
    assert operational is False, "HATP_TRUSTED_OPERATIONAL must never be reachable in Wave 4"

    return HATPVerificationSubstrateReadiness(
        status=HATPVerificationSubstrateStatus.NOT_READY,
        operational=operational,
        terms=terms,
        reasons=tuple(reasons),
    )
