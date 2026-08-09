"""HMIC-001 v1.0 Certification Data Models + Canonical Parsing (Phase
149O.19.5A, Wave A of the HMIC-001 v1.0 implementation, `docs/
PHASE_149O_19_4_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_
IMPLEMENTATION_PLAN.md` §9.3).

Owns, and only owns: the pure, authority-neutral data representation
layer for HMIC-001's protected certification model -- the closed
`CertificationRecord`/`CertificationBinding` schemas and their whole-file
document wrappers (HMIC-REQ-031, HMIC-REQ-032, HMIC-REQ-036), strict
closed-schema parsing
with duplicate-JSON-key rejection (HMIC-REQ-031), the closed 9-value
Validation Status vocabulary and its readiness mapping
(HMIC-REQ-106, HMIC-REQ-107),
and canonical serialization (HMIC-REQ-041, HMIC-REQ-042).

It owns **no** filesystem I/O, **no** Git access, **no** identity
derivation (repository/deployment/commit/implementation-scope-digest/
contract-version derivation -- Wave B), **no** protected storage/locking
(Wave C), **no** validation algorithm (Wave D), **no** admin writer
(Wave E), and **no** activation-readiness wiring (Wave F). See
`docs/PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md` §9.3 and
`docs/PHASE_149O_19_5A_HMIC_CERTIFICATION_DATA_MODELS_CANONICAL_PARSING.md`
for the full wave boundary.

Semantic wall (HMIC-REQ-009, restated for this module specifically):
successfully parsing a `CertificationRecord`, `CertificationBinding`, or
either whole-file document establishes only that the input is well-formed
under HMIC-001's closed schema. It never means the record is currently
active, unrevoked, implementation-matched, or contract-matched -- i.e.
never means `VALID` (HMIC-REQ-103's 12-step algorithm, Wave D, alone
decides that). No function in this module returns, computes, or can be
mistaken for that boolean; `CertificationStatus` below is the closed
*vocabulary* a future validator's outcome is drawn from, not a judgment
this module makes.

This module performs no filesystem I/O, no Git access, no network access,
and no hardware access; importing it has no side effect. It never reads
`PROJECT_STATUS.md`, `tasks/TODO.md`, `CHANGELOG.md`, a phase report, a
test result, or any environment variable (HMIC-REQ-074).

Immutability (HMIC-REQ-035, restated): `CertificationRecord` and
`CertificationBinding` are fully immutable Python objects --
`dataclass(frozen=True)`, every field, including `status`/`revoked_at`.
HMIC-REQ-035's carve-out ("every field ... other than `status`/
`revoked_at` is immutable") describes *storage-level* field mutation --
Wave C's admin-tool-driven writer rewriting the on-disk JSON record with
those two keys changed and every other byte-for-byte identical -- never
in-place Python attribute mutation of an already-constructed object.
Revocation, at this module's layer, is always expressed as constructing a
*new* `CertificationRecord` value; no field of either type is ever
mutated in place.

Dependency direction: this module imports only
`repository_identity.is_valid_repository_instance_id` (a pure format
check, no authority claim, no filesystem I/O -- the identical narrow
dependency `human_approval_trusted_provenance.py`/`hatp_signed_evidence.py`
already take on the same function). It does not import `hatp_bootstrap.py`,
`hatp_mandatory_cutover.py`, `permission_broker*.py`,
`rollback_approval_evidence.py`, `agent.py`, `commands/agent.py`, or any
AG3/AG5 execution path -- this module never constructs or evaluates a
Permission Broker request (HMIC-REQ-122) and never writes, derives, or
influences a RAE-001 Decision/Binding artifact (HMIC-REQ-123) or any
runtime execution capability (HMIC-REQ-124).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional

from pcae.core.repository_identity import is_valid_repository_instance_id

# ═══════════════════════════════════════════════════════════════════════════
# Schema version constants
# ═══════════════════════════════════════════════════════════════════════════

#: HMIC-REQ-031: `certifications.json`'s own document-level schema
#: version. Only version 1 is defined by HMIC-001 v1.0; an unrecognized
#: future value fails closed (HMIC-REQ-140), never optimistically parsed.
CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION = 1

#: HMIC-REQ-036: `certification-bindings.json`'s own document-level
#: schema version. Same fail-closed discipline as above.
CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION = 1

# ═══════════════════════════════════════════════════════════════════════════
# Strict lexical grammars (HMIC-REQ-032, reusing existing repository
# precedent exactly rather than inventing new grammar)
# ═══════════════════════════════════════════════════════════════════════════

#: HMIC-REQ-032: `certified_at`/`revoked_at` reuse
#: `hatp_mandatory_cutover.py::_TIMESTAMP_PATTERN` exactly -- `Z`-suffix
#: only, fully anchored, 1-6 digit fractional seconds. Duplicated locally
#: rather than imported, mirroring this repository's existing convention
#: of local duplication for small, authority-bearing lexical patterns
#: (`hatp_mandatory_cutover.py::_reject_symlink` vs.
#: `hatp_bootstrap.py::_reject_symlink`).
_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")

#: HMIC-REQ-038: `certification_id` is "a SHA-256 hex digest (lowercase,
#: 64 characters)" -- stated explicitly in the contract. The same pattern
#: governs `implementation_scope_digest` and `verification_record_digest`
#: (both SHA-256 digests) and `active_certification_id` (an exact
#: `certification_id` value, HMIC-REQ-037).
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

#: HMIC-REQ-046: `implementation_commit` is "the git commit SHA of HEAD
#: ... obtained via `git rev-parse HEAD` (or equivalent)". Mirrors
#: `human_approval_trusted_provenance.py::_COMMIT_SHA_RE` exactly (40-hex
#: SHA-1 or 64-hex SHA-256 Git object IDs).
_COMMIT_SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")

#: HMIC-REQ-032: `CertificationRecord.status` is exactly one of these two
#: string values -- mirrors `hatp_bootstrap.py::_STATUS_VALUES` exactly.
_CERTIFICATION_RECORD_STATUS_VALUES = frozenset({"active", "revoked"})

#: HMIC-REQ-067: the minimal sufficient `contract_versions` key set.
_CONTRACT_VERSIONS_REQUIRED_KEYS = frozenset({"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"})


# ═══════════════════════════════════════════════════════════════════════════
# Errors
# ═══════════════════════════════════════════════════════════════════════════


class HATPMandatoryCertificationError(Exception):
    """Base error for HMIC-001 certification model/parsing operations."""


class CertificationMalformedError(HATPMandatoryCertificationError):
    """A certification document, binding document, or individual record
    exists but fails strict validation (HMIC-REQ-031, HMIC-REQ-036). Never
    partially accepted -- the first failing check raises immediately."""


# ═══════════════════════════════════════════════════════════════════════════
# Duplicate-JSON-key-rejecting, non-finite-constant-rejecting strict
# loader (HMIC-REQ-031, mirroring
# `hatp_mandatory_cutover.py::_load_json_no_duplicate_keys` exactly, plus
# an explicit NaN/Infinity guard for HMIC-REQ-027's "Strict JSON numeric
# domain" requirement)
# ═══════════════════════════════════════════════════════════════════════════


def _reject_duplicate_keys(pairs: list) -> dict:
    seen: set = set()
    result: dict = {}
    for key, value in pairs:
        if key in seen:
            raise CertificationMalformedError(f"duplicate JSON object key: {key!r}")
        seen.add(key)
        result[key] = value
    return result


def _reject_json_constant(name: str) -> None:
    raise CertificationMalformedError(f"document contains a non-finite JSON numeric constant: {name!r}")


def _load_json_no_duplicate_keys(raw) -> object:
    """Accepts either `bytes` or `str`. Rejects malformed JSON, duplicate
    object keys at any nesting level, and non-finite numeric constants
    (`NaN`, `Infinity`, `-Infinity`, which `json.loads` otherwise accepts
    by default)."""

    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CertificationMalformedError(f"document is not valid UTF-8: {exc}") from exc
    else:
        text = raw
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_json_constant)
    except json.JSONDecodeError as exc:
        raise CertificationMalformedError(f"document is not valid JSON: {exc}") from exc


# ═══════════════════════════════════════════════════════════════════════════
# Field-level structural validators
# ═══════════════════════════════════════════════════════════════════════════


def _validate_timestamp(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP_PATTERN.fullmatch(value):
        raise CertificationMalformedError(
            f"{context}: expected a strict 'YYYY-MM-DDTHH:MM:SS[.ffffff]Z' timestamp, got {value!r}"
        )
    normalized = value[:-1] + "+00:00"
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CertificationMalformedError(f"{context}: not a calendar-valid timestamp: {value!r}") from exc
    return value


def _require_nonempty_str(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise CertificationMalformedError(f"{context}: expected a non-empty string, got {value!r}")
    return value


def _require_sha256_hex(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _SHA256_HEX_RE.fullmatch(value):
        raise CertificationMalformedError(f"{context}: expected a lowercase 64-character hex SHA-256 digest, got {value!r}")
    return value


def _require_commit_sha(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _COMMIT_SHA_RE.fullmatch(value):
        raise CertificationMalformedError(
            f"{context}: expected a 40- or 64-character lowercase hex Git commit SHA, got {value!r}"
        )
    return value


def _require_repository_instance_id(value: object, *, context: str) -> str:
    if not is_valid_repository_instance_id(value):
        raise CertificationMalformedError(f"{context}: expected a valid UUID4 repository_instance_id string, got {value!r}")
    return value  # type: ignore[return-value]


def _require_contract_versions(value: object, *, context: str) -> Mapping[str, str]:
    if not isinstance(value, dict):
        raise CertificationMalformedError(f"{context}: expected a JSON object, got {value!r}")
    present = set(value.keys())
    unknown = present - _CONTRACT_VERSIONS_REQUIRED_KEYS
    if unknown:
        raise CertificationMalformedError(f"{context}: has unrecognized contract entries: {sorted(unknown)}")
    missing = _CONTRACT_VERSIONS_REQUIRED_KEYS - present
    if missing:
        raise CertificationMalformedError(f"{context}: is missing required contract entries: {sorted(missing)}")
    return {key: _require_nonempty_str(value[key], context=f"{context}[{key!r}]") for key in _CONTRACT_VERSIONS_REQUIRED_KEYS}


def _require_certification_record_status_consistency(
    status: object, revoked_at: object, *, context: str
) -> "tuple[str, Optional[str]]":
    """Mirrors `hatp_bootstrap.py::_require_revoked_at_consistency` exactly
    (HMIC-REQ-034): `status`/`revoked_at` are validated together, never
    independently."""

    if status not in _CERTIFICATION_RECORD_STATUS_VALUES:
        raise CertificationMalformedError(
            f"{context}: status must be one of {sorted(_CERTIFICATION_RECORD_STATUS_VALUES)}, got {status!r}"
        )
    if status == "revoked":
        if revoked_at is None:
            raise CertificationMalformedError(f"{context}: status is 'revoked' but revoked_at is missing")
        validated_revoked_at = _validate_timestamp(revoked_at, context=f"{context}.revoked_at")
        return status, validated_revoked_at
    if revoked_at is not None:
        raise CertificationMalformedError(f"{context}: status is 'active' but revoked_at is set")
    return status, None


# ═══════════════════════════════════════════════════════════════════════════
# Closed Validation Status vocabulary (HMIC-REQ-106) and readiness mapping
# (HMIC-REQ-107)
# ═══════════════════════════════════════════════════════════════════════════


class CertificationStatus(str, Enum):
    """The closed Validation Status vocabulary (HMIC-REQ-106), matching
    HMIC-REQ-103's future 12-step validation algorithm one-to-one, 9
    members exactly. Distinct from `CertificationRecord.status`
    ("active"/"revoked", HMIC-REQ-032) -- that field marks one record's
    own lifecycle state; this enum is the closed set of *outcomes* a
    future Wave D validator returns, not implemented by this module. No
    `VALID_WITH_WARNING` or other partial-credit member exists, and none
    may ever be added without amending HMIC-001 itself (HMIC-REQ-010,
    HMIC-REQ-106)."""

    MISSING = "MISSING"
    MALFORMED = "MALFORMED"
    WRONG_REPOSITORY = "WRONG_REPOSITORY"
    WRONG_DEPLOYMENT = "WRONG_DEPLOYMENT"
    IMPLEMENTATION_MISMATCH = "IMPLEMENTATION_MISMATCH"
    CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
    REVOKED = "REVOKED"
    ACCESS_ERROR = "ACCESS_ERROR"
    VALID = "VALID"


def certification_status_satisfies_readiness(status: "CertificationStatus") -> bool:
    """HMIC-REQ-107: `mandatory_consumption_implementation_independently_
    verified` is `True` if and only if `status` is exactly
    `CertificationStatus.VALID`; every other member -- and any value that
    is not a `CertificationStatus` member at all -- maps to `False`. The
    Validation Status boundary is binary, never partial (HMIC-REQ-108: no
    non-blocking diagnostic detail may ever substitute for, or be
    conflated with, this binary outcome); no partial-credit member exists
    in the vocabulary itself either (HMIC-REQ-010). This function is
    never wired into `hatp_mandatory_cutover.py` by this phase (Wave F
    only, gated by Stop Condition W-1)."""

    return status is CertificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# `CertificationRecord` (HMIC-REQ-032)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CertificationRecord:
    """One immutable entry of `certifications.json` (HMIC-REQ-032).
    Successfully constructing one of these establishes only that the
    field set is well-formed under HMIC-001's closed schema -- never that
    the record is the currently active, unrevoked, implementation-matched
    certification (HMIC-REQ-009: `parsed record` != `VALID certification`;
    Wave D alone decides that).

    No signature field exists (HMIC-REQ-029: v1.0 adds no cryptographic
    signature -- the Protected Root's OS-permission boundary is this
    repository's entire trust boundary for identically-shaped artifacts).
    `verification_record_digest` (HMIC-REQ-071) and any co-located phase
    identifier (HMIC-REQ-073) are audit/traceability metadata only, never
    a validity condition; `certified_at`/`certified_by` are likewise
    informational/audit metadata only (HMIC-REQ-130), and `certified_by`
    is never cryptographic proof of identity (HMIC-REQ-131). No field
    here holds private key material, PINs, or credential secrets
    (HMIC-REQ-133)."""

    certification_id: str
    repository_instance_id: str
    canonical_deployment_root: str
    implementation_commit: str
    implementation_scope_digest: str
    contract_versions: Mapping[str, str]
    verification_record_digest: str  # HMIC-REQ-071, HMIC-REQ-073: evidentiary only
    certified_at: str
    certified_by: str  # HMIC-REQ-130, HMIC-REQ-131: audit metadata, not proof of identity
    status: str
    revoked_at: Optional[str] = None

    def __post_init__(self) -> None:
        # Deep immutability (HMIC-REQ-133 "no secret material" aside, this
        # is HMIC-REQ-035's own field-immutability requirement extended to
        # the nested mapping): the outer `frozen=True` alone would still
        # permit `record.contract_versions["HMRC-001"] = "9.9"` in place.
        object.__setattr__(self, "contract_versions", MappingProxyType(dict(self.contract_versions)))


_CERTIFICATION_RECORD_ALLOWED_FIELDS = frozenset(
    {
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
)
#: HMIC-REQ-032: `revoked_at` is present if and only if `status ==
#: "revoked"` -- it is the one field that may be legitimately absent from
#: a well-formed document (never required-and-missing).
_CERTIFICATION_RECORD_REQUIRED_FIELDS = _CERTIFICATION_RECORD_ALLOWED_FIELDS - {"revoked_at"}


def parse_certification_record(document: object) -> CertificationRecord:
    """Strict, closed-schema parser (HMIC-REQ-031, HMIC-REQ-032, frozen
    terminology HMIC-REQ-007). Constructor and
    parser share one validation domain -- every field this module ever
    constructs a `CertificationRecord` from passes through this function
    first; no state is directly constructible that this parser would
    reject."""

    if not isinstance(document, dict):
        raise CertificationMalformedError("certification record is not a JSON object")

    present = set(document.keys())
    unknown = present - _CERTIFICATION_RECORD_ALLOWED_FIELDS
    if unknown:
        raise CertificationMalformedError(f"certification record has unrecognized fields: {sorted(unknown)}")
    missing = _CERTIFICATION_RECORD_REQUIRED_FIELDS - present
    if missing:
        raise CertificationMalformedError(f"certification record is missing fields: {sorted(missing)}")

    certification_id = _require_sha256_hex(document["certification_id"], context="certification_id")
    repository_instance_id = _require_repository_instance_id(
        document["repository_instance_id"], context="repository_instance_id"
    )
    canonical_deployment_root = _require_nonempty_str(
        document["canonical_deployment_root"], context="canonical_deployment_root"
    )
    implementation_commit = _require_commit_sha(document["implementation_commit"], context="implementation_commit")
    implementation_scope_digest = _require_sha256_hex(
        document["implementation_scope_digest"], context="implementation_scope_digest"
    )
    contract_versions = _require_contract_versions(document["contract_versions"], context="contract_versions")
    verification_record_digest = _require_sha256_hex(
        document["verification_record_digest"], context="verification_record_digest"
    )
    certified_at = _validate_timestamp(document["certified_at"], context="certified_at")
    certified_by = _require_nonempty_str(document["certified_by"], context="certified_by")
    status, revoked_at = _require_certification_record_status_consistency(
        document["status"], document.get("revoked_at"), context="certification record"
    )

    return CertificationRecord(
        certification_id=certification_id,
        repository_instance_id=repository_instance_id,
        canonical_deployment_root=canonical_deployment_root,
        implementation_commit=implementation_commit,
        implementation_scope_digest=implementation_scope_digest,
        contract_versions=contract_versions,
        verification_record_digest=verification_record_digest,
        certified_at=certified_at,
        certified_by=certified_by,
        status=status,
        revoked_at=revoked_at,
    )


def certification_record_to_document(record: CertificationRecord) -> dict:
    """Inverse of `parse_certification_record`. `revoked_at` is emitted
    only when present (never `"revoked_at": null`), mirroring
    HMIC-REQ-032's "present if and only if status == 'revoked'" exactly."""

    document = {
        "certification_id": record.certification_id,
        "repository_instance_id": record.repository_instance_id,
        "canonical_deployment_root": record.canonical_deployment_root,
        "implementation_commit": record.implementation_commit,
        "implementation_scope_digest": record.implementation_scope_digest,
        "contract_versions": dict(record.contract_versions),
        "verification_record_digest": record.verification_record_digest,
        "certified_at": record.certified_at,
        "certified_by": record.certified_by,
        "status": record.status,
    }
    if record.revoked_at is not None:
        document["revoked_at"] = record.revoked_at
    return document


# ═══════════════════════════════════════════════════════════════════════════
# `CertificationBinding` -- the Active-Certification Pointer (HMIC-REQ-036)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CertificationBinding:
    """The Active-Certification Pointer (HMIC-REQ-036): the single,
    explicit entry naming which `CertificationRecord`, if any, is
    currently active for one `(repository_instance_id,
    canonical_deployment_root)` key. `active_certification_id is None`
    means explicitly "no active certification for this key" -- never
    "look up the latest" (HMIC-REQ-085: no implicit-latest selection is
    ever performed by this module or any future consumer of it)."""

    repository_instance_id: str
    canonical_deployment_root: str
    active_certification_id: Optional[str] = None


_CERTIFICATION_BINDING_ALLOWED_FIELDS = frozenset(
    {"repository_instance_id", "canonical_deployment_root", "active_certification_id"}
)
_CERTIFICATION_BINDING_REQUIRED_FIELDS = _CERTIFICATION_BINDING_ALLOWED_FIELDS - {"active_certification_id"}


def parse_certification_binding(document: object) -> CertificationBinding:
    """Strict, closed-schema parser (HMIC-REQ-036, HMIC-REQ-037, frozen
    terminology HMIC-REQ-007)."""

    if not isinstance(document, dict):
        raise CertificationMalformedError("certification binding is not a JSON object")

    present = set(document.keys())
    unknown = present - _CERTIFICATION_BINDING_ALLOWED_FIELDS
    if unknown:
        raise CertificationMalformedError(f"certification binding has unrecognized fields: {sorted(unknown)}")
    missing = _CERTIFICATION_BINDING_REQUIRED_FIELDS - present
    if missing:
        raise CertificationMalformedError(f"certification binding is missing fields: {sorted(missing)}")

    repository_instance_id = _require_repository_instance_id(
        document["repository_instance_id"], context="binding.repository_instance_id"
    )
    canonical_deployment_root = _require_nonempty_str(
        document["canonical_deployment_root"], context="binding.canonical_deployment_root"
    )
    active_certification_id_raw = document.get("active_certification_id")
    active_certification_id: Optional[str]
    if active_certification_id_raw is None:
        active_certification_id = None
    else:
        # HMIC-REQ-037: the exact `certification_id` string, never a file
        # path, a partial identifier, or any value requiring further
        # resolution -- the identical SHA-256-hex grammar as the record's
        # own `certification_id` field.
        active_certification_id = _require_sha256_hex(
            active_certification_id_raw, context="binding.active_certification_id"
        )

    return CertificationBinding(
        repository_instance_id=repository_instance_id,
        canonical_deployment_root=canonical_deployment_root,
        active_certification_id=active_certification_id,
    )


def certification_binding_to_document(binding: CertificationBinding) -> dict:
    """Inverse of `parse_certification_binding`. `active_certification_id`
    is emitted only when set (never `"active_certification_id": null`)."""

    document = {
        "repository_instance_id": binding.repository_instance_id,
        "canonical_deployment_root": binding.canonical_deployment_root,
    }
    if binding.active_certification_id is not None:
        document["active_certification_id"] = binding.active_certification_id
    return document


# ═══════════════════════════════════════════════════════════════════════════
# Whole-file document wrappers (HMIC-REQ-024, HMIC-REQ-025, HMIC-REQ-031,
# HMIC-REQ-036)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CertificationsDocument:
    """The whole-file structure of `certifications.json` (HMIC-REQ-025):
    a document-level schema version plus the append-only list of
    `CertificationRecord` entries (HMIC-REQ-031). Uniqueness of
    `certification_id` across entries is a structural document property
    this parser enforces; storage-level create-once *write* safety
    (HMIC-REQ-084) is a separate, Wave C (STORE) concern this module does
    not implement."""

    schema_version: int
    certifications: "tuple[CertificationRecord, ...]"

    def __post_init__(self) -> None:
        object.__setattr__(self, "certifications", tuple(self.certifications))


@dataclass(frozen=True)
class CertificationBindingsDocument:
    """The whole-file structure of `certification-bindings.json`
    (HMIC-REQ-025): a document-level schema version plus the list of
    `CertificationBinding` entries, each uniquely keyed by
    `(repository_instance_id, canonical_deployment_root)` (HMIC-REQ-026)."""

    schema_version: int
    bindings: "tuple[CertificationBinding, ...]"

    def __post_init__(self) -> None:
        object.__setattr__(self, "bindings", tuple(self.bindings))


_CERTIFICATIONS_DOCUMENT_ALLOWED_TOP_FIELDS = frozenset({"schema_version", "certifications"})
_CERTIFICATION_BINDINGS_DOCUMENT_ALLOWED_TOP_FIELDS = frozenset({"schema_version", "bindings"})


def _require_schema_version(value: object, *, supported: int, context: str) -> int:
    """HMIC-REQ-033: `version` (here, the document-level `schema_version`)
    is a strict positive integer; a JSON boolean is explicitly rejected
    (`isinstance(True, int)` is `True` in Python, so the `bool` exclusion
    must be independent of the `int` check)."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise CertificationMalformedError(f"{context}: schema_version must be a strict integer, got {value!r}")
    if value != supported:
        raise CertificationMalformedError(
            f"{context}: schema_version {value!r} is not supported (expected {supported!r}); failing closed"
        )
    return value


def parse_certifications_document(document: object) -> CertificationsDocument:
    """Strict, closed-schema parser for the whole `certifications.json`
    document (HMIC-REQ-031)."""

    if not isinstance(document, dict):
        raise CertificationMalformedError("certifications document is not a JSON object")

    present = set(document.keys())
    unknown = present - _CERTIFICATIONS_DOCUMENT_ALLOWED_TOP_FIELDS
    if unknown:
        raise CertificationMalformedError(f"certifications document has unrecognized top-level fields: {sorted(unknown)}")
    missing = _CERTIFICATIONS_DOCUMENT_ALLOWED_TOP_FIELDS - present
    if missing:
        raise CertificationMalformedError(f"certifications document is missing top-level fields: {sorted(missing)}")

    schema_version = _require_schema_version(
        document["schema_version"],
        supported=CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION,
        context="certifications document",
    )

    raw_entries = document["certifications"]
    if not isinstance(raw_entries, list):
        raise CertificationMalformedError("certifications document 'certifications' field must be a JSON array")

    seen_ids: set = set()
    records = []
    for raw_entry in raw_entries:
        record = parse_certification_record(raw_entry)
        if record.certification_id in seen_ids:
            raise CertificationMalformedError(
                f"certifications document contains duplicate certification_id: {record.certification_id!r}"
            )
        seen_ids.add(record.certification_id)
        records.append(record)

    return CertificationsDocument(schema_version=schema_version, certifications=tuple(records))


def parse_certification_bindings_document(document: object) -> CertificationBindingsDocument:
    """Strict, closed-schema parser for the whole
    `certification-bindings.json` document (HMIC-REQ-036)."""

    if not isinstance(document, dict):
        raise CertificationMalformedError("certification-bindings document is not a JSON object")

    present = set(document.keys())
    unknown = present - _CERTIFICATION_BINDINGS_DOCUMENT_ALLOWED_TOP_FIELDS
    if unknown:
        raise CertificationMalformedError(
            f"certification-bindings document has unrecognized top-level fields: {sorted(unknown)}"
        )
    missing = _CERTIFICATION_BINDINGS_DOCUMENT_ALLOWED_TOP_FIELDS - present
    if missing:
        raise CertificationMalformedError(f"certification-bindings document is missing top-level fields: {sorted(missing)}")

    schema_version = _require_schema_version(
        document["schema_version"],
        supported=CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION,
        context="certification-bindings document",
    )

    raw_entries = document["bindings"]
    if not isinstance(raw_entries, list):
        raise CertificationMalformedError("certification-bindings document 'bindings' field must be a JSON array")

    seen_keys: set = set()
    bindings = []
    for raw_entry in raw_entries:
        binding = parse_certification_binding(raw_entry)
        key = (binding.repository_instance_id, binding.canonical_deployment_root)
        if key in seen_keys:
            raise CertificationMalformedError(
                f"certification-bindings document contains duplicate "
                f"(repository_instance_id, canonical_deployment_root) key: {key!r}"
            )
        seen_keys.add(key)
        bindings.append(binding)

    return CertificationBindingsDocument(schema_version=schema_version, bindings=tuple(bindings))


def certifications_document_to_document(doc: CertificationsDocument) -> dict:
    return {
        "schema_version": doc.schema_version,
        "certifications": [certification_record_to_document(record) for record in doc.certifications],
    }


def certification_bindings_document_to_document(doc: CertificationBindingsDocument) -> dict:
    return {
        "schema_version": doc.schema_version,
        "bindings": [certification_binding_to_document(binding) for binding in doc.bindings],
    }


# ═══════════════════════════════════════════════════════════════════════════
# `bytes -> typed object` entry points (Primary Objective)
# ═══════════════════════════════════════════════════════════════════════════


def parse_certifications_document_from_bytes(raw) -> CertificationsDocument:
    """The `bytes -> strict parser -> typed object` entry point for
    `certifications.json`. Accepts `bytes` or `str`; never touches the
    filesystem itself -- Wave C (STORE) is responsible for reading the
    file's bytes and calling this function."""

    return parse_certifications_document(_load_json_no_duplicate_keys(raw))


def parse_certification_bindings_document_from_bytes(raw) -> CertificationBindingsDocument:
    """As above, for `certification-bindings.json`."""

    return parse_certification_bindings_document(_load_json_no_duplicate_keys(raw))


# ═══════════════════════════════════════════════════════════════════════════
# Canonical serialization (HMIC-REQ-041, HMIC-REQ-042)
# ═══════════════════════════════════════════════════════════════════════════


def canonical_serialize(document: dict) -> bytes:
    """HMIC-REQ-041, HMIC-REQ-042: every write to either certification file, and
    every digest input derived from this serialization, uses exactly this
    canonical form -- `json.dumps(document, indent=2, sort_keys=True) +
    "\\n"`, UTF-8 encoded -- identical to
    `hatp_mandatory_cutover.py::_atomic_write_json` and
    `repository_identity.py`'s own write convention. No alternate
    whitespace, key-ordering, or separator convention is permitted
    anywhere in this module or any future consumer of it. Deliberately
    the plain `json.dumps` default for non-ASCII escaping (no
    `ensure_ascii=False` override) -- the contract's own cited precedent
    (`_atomic_write_json`) uses none, so this function does not either.
    `allow_nan=False` hardens the strict-JSON-numeric-domain requirement
    (no `NaN`/`Infinity`/`-Infinity`) on the write path, matching the
    equivalent `parse_constant` guard already enforced on the read path
    by `_load_json_no_duplicate_keys`."""

    return (json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def canonicalize_certifications_document(doc: CertificationsDocument) -> bytes:
    return canonical_serialize(certifications_document_to_document(doc))


def canonicalize_certification_bindings_document(doc: CertificationBindingsDocument) -> bytes:
    return canonical_serialize(certification_bindings_document_to_document(doc))
