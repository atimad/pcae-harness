"""HMIC-001 v1.0 Certification Data Models + Canonical Parsing (Wave A,
Phase 149O.19.5A) and Implementation/Contract Identity Derivation (Wave
B, Phase 149O.19.5B) of the HMIC-001 v1.0 implementation, `docs/
PHASE_149O_19_4_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_
IMPLEMENTATION_PLAN.md` §9.3.

Wave A owns, and only owns: the pure, authority-neutral data
representation layer for HMIC-001's protected certification model --
the closed `CertificationRecord`/`CertificationBinding` schemas and
their whole-file document wrappers (HMIC-REQ-031, HMIC-REQ-032,
HMIC-REQ-036), strict closed-schema parsing with duplicate-JSON-key
rejection (HMIC-REQ-031), the closed 9-value Validation Status
vocabulary and its readiness mapping (HMIC-REQ-106, HMIC-REQ-107), and
canonical serialization (HMIC-REQ-041, HMIC-REQ-042).

Wave B owns, and only owns: pure identity *derivation* -- answering
"what is the current implementation identity?" and "what are the
current bound contract identities?", never "is a protected
certification valid?" (HMIC-REQ-009's semantic wall, restated below,
applies identically to Wave B's functions). Specifically:
`_FROZEN_AUTHORITY_BEARING_FILES` (HMIC-REQ-050's literal 36-path
enumeration, v1.6), `derive_repository_instance_id`,
`derive_canonical_deployment_root`, `derive_implementation_commit`
(HMIC-REQ-046), `derive_implementation_scope_digest`
(HMIC-REQ-054-062), `derive_contract_versions` (HMIC-REQ-067),
and `derive_certification_id` (HMIC-REQ-038). Wave B does NOT
implement a runtime/executed-source-binding check: HMIC-REQ-063 names
this an explicit, out-of-scope-for-v1.0 residual limitation ("v1.0 of
this contract does NOT implement an executed-code/runtime-module-
resolution check"), and the 149O.19.4 plan's own Wave B API surface
(§9.3) names no such function -- adding one here would be undocumented
scope creep beyond the frozen, independently-verified plan, not a
Wave-B-owned requirement.

Wave C (Phase 149O.19.5C) owns, and only owns: protected certification
*storage* -- the `.certification-transition.lock` primitive
(HMIC-REQ-097/101/102), read primitives for `certifications.json`/
`certification-bindings.json` (HMIC-REQ-025/031/036), explicit-ID load
APIs (HMIC-REQ-019/037/090), and internal, admin-only-caller write
primitives (`_append_certification_record`/`_write_active_binding`/
`_write_revocation`, HMIC-REQ-076 step 6, HMIC-REQ-086/088,
HMIC-REQ-091-093) using the same `mkstemp`+`fsync`+`os.replace` atomic
idiom every other protected-record writer in this codebase already uses
(HMIC-REQ-083). Wave C answers only "does artifact ID X exist / what
bytes are stored / which ID is bound / is ID X recorded as revoked?" --
it never answers "is X a VALID certification?" or "may activation
proceed?" (Wave D, not implemented by this module yet). Storage
existing ≠ active-valid ≠ independently verified ≠ readiness ≠
activation authority (the strict wall this wave preserves). Wave C does
not implement a validation algorithm, an admin ceremony, an ordinary
`pcae` CLI command, or readiness wiring; it does not replace the
hardcoded `False` readiness ceiling in `hatp_mandatory_cutover.py`, and
it does not import that module. See `docs/PHASE_149O_19_5C_HMIC_
PROTECTED_CERTIFICATION_STATE_STORE.md` for the full wave record.

Wave D (Phase 149O.19.5D) owns, and only owns: the read-only Active-
Certification Validation Engine -- `validate_active_hatp_mandatory_
independent_verification_certification` (the sole production entrypoint,
HMIC-REQ-109) and `_validate_at_root` (its internal, non-production-
reachable test seam, HMIC-REQ-112), implementing exactly HMIC-REQ-103's
12-step validation algorithm in exact order (HMIC-REQ-104: the first
failing step determines the returned `CertificationStatus`; no later
step is ever evaluated once an earlier one fails) and returning the
immutable `HMICValidationResult` typed result. Wave D reuses Wave A's
closed `CertificationStatus` vocabulary and `certification_status_
satisfies_readiness` mapping, Wave B's `derive_*` identity functions, and
Wave C's `_load_active_binding`/`_load_certification_record` readers
unmodified -- it implements no second filesystem parser, no second
identity-derivation scheme, and no second protected-root resolution.
Wave D never acquires `.certification-transition.lock` (HMIC-REQ-101:
only certification *writes* do) and never calls `_append_certification_
record`/`_write_active_binding`/`_write_revocation`. This module has
zero production callers of the Wave D validator at phase exit: it is not
imported by `hatp_mandatory_cutover.py`, and the hard-coded `mandatory_
consumption_implementation_independently_verified = False` ceiling
there is unchanged. Wiring the validator into that ceiling is Wave F,
gated by Stop Condition W-1 (a future HMIC-001 v1.1 contract amendment
binding this module's own bytes into the certified 22-file scope,
independently verified, before Wave F may begin -- `docs/
PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md` §10.3). See `docs/
PHASE_149O_19_5D_HMIC_ACTIVE_CERTIFICATION_VALIDATION_ENGINE.md` for the
full wave record, including this wave's documented interpretation of
steps 2-3's failure mapping (`ACCESS_ERROR`, HMIC-REQ-105 extended by
analogy) and its deliberate divergence from the 149O.19.4 plan's own
illustrative (non-binding) `_validate_at_root(protected_root,
repository_instance_id, canonical_deployment_root)` shorthand signature
in favor of one that never accepts `repository_instance_id`/
`canonical_deployment_root` as caller input on any path, production or
test (HMIC-REQ-045/110, and this phase's own governing-prompt §6).

Neither wave owns: the admin writer (Wave E) or activation-readiness
wiring (Wave F). See `docs/PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md`
§9.3, `docs/PHASE_149O_19_5A_HMIC_CERTIFICATION_DATA_MODELS_CANONICAL_
PARSING.md`, `docs/PHASE_149O_19_5B_HMIC_IMPLEMENTATION_CONTRACT_
IDENTITY_DERIVATION.md`, `docs/PHASE_149O_19_5C_HMIC_PROTECTED_
CERTIFICATION_STATE_STORE.md`, and `docs/PHASE_149O_19_5D_HMIC_ACTIVE_
CERTIFICATION_VALIDATION_ENGINE.md` for the full wave boundary.

Semantic wall (HMIC-REQ-009, restated for this module specifically):
successfully parsing a `CertificationRecord`, `CertificationBinding`, or
either whole-file document establishes only that the input is well-formed
under HMIC-001's closed schema. Likewise, successfully deriving an
implementation or contract identity (Wave B) establishes only what the
current on-disk/Git/contract state *is*, never that any certification
referencing it is currently active, unrevoked, or matched (i.e. never
`VALID` -- HMIC-REQ-103's 12-step algorithm, Wave D, alone decides
that). No function in this module returns, computes, or can be
mistaken for that boolean, an `is_certified`/`verified`/`valid` flag,
or a `CertificationStatus` value; `CertificationStatus` below is the
closed *vocabulary* a future validator's outcome is drawn from, not a
judgment this module makes.

Wave A performs no filesystem I/O, no Git access, no network access,
and no hardware access; importing this module has no side effect for
either wave -- Wave B's `derive_*` functions perform filesystem/Git
reads only when *called*, never at import time, and every frozen
constant below (the 36-path tuple, the 7-contract-path mapping) is a
literal, embedded at module load with no computation. Wave B reads no
certification state (no `certifications.json`, no
`certification-bindings.json`, no active-pointer, no revocation
record) and writes nothing; it never reads `PROJECT_STATUS.md`,
`tasks/TODO.md`, `CHANGELOG.md`, a phase report, a test result, or any
environment variable (HMIC-REQ-074).

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

Dependency direction: Wave A imports only
`repository_identity.is_valid_repository_instance_id` (a pure format
check, no authority claim, no filesystem I/O -- the identical narrow
dependency `human_approval_trusted_provenance.py`/`hatp_signed_evidence.py`
already take on the same function). Wave B additionally imports
`repository_identity.read_repository_identity` (read-only Layer-1
identity lookup, the identical dependency
`hatp_mandatory_cutover.py`/`hatp_ag_authority.py`/
`hatp_rollback_consumption.py` already take on) and
`hatp_bootstrap.resolve_canonical_deployment_root` (pure path
canonicalization, no protected-root access -- the 149O.19.4 plan §9.3
explicitly assigns Wave B this exact call). Neither wave imports
`hatp_mandatory_cutover.py`, `permission_broker*.py`,
`rollback_approval_evidence.py`, `agent.py`, `commands/agent.py`, or any
AG3/AG5 execution path -- this module never constructs or evaluates a
Permission Broker request (HMIC-REQ-122) and never writes, derives, or
influences a RAE-001 Decision/Binding artifact (HMIC-REQ-123) or any
runtime execution capability (HMIC-REQ-124).
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Iterator, Mapping, Optional

from pcae.core.hatp_bootstrap import HATPTrustStore, HATPTrustStoreError, resolve_canonical_deployment_root
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import (
    RepositoryIdentityError,
    is_valid_repository_instance_id,
    read_repository_identity,
)

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

#: HMIC-REQ-067/069/032/053: the exact, closed `contract_versions` key
#: set, as used by the Wave A `CertificationRecord` closed-schema
#: validator (`_require_contract_versions`, below). Repaired at v1.5
#: (149O.20L.7O.2H.0, finding B-149O.20L.7O.2H-1) to add `HBDC-001`,
#: bringing this constant into exact membership equality with
#: `_CONTRACT_IDENTITY_FILES` below (Wave B's own `contract_versions`
#: derivation input) and with `derive_contract_versions`'s own live
#: seven-member return value. HMIC-001 §20's own text is unambiguous:
#: HMIC-REQ-067 states "Seven entries, no more, no fewer, as of v1.5";
#: HMIC-REQ-069 states validation "SHALL compare each `contract_versions`
#: entry -- seven entries as of v1.5 -- against the named contract's own
#: current, live version header," and explicitly classes "a required
#: contract key absent from a stored record" as a mismatch; HMIC-REQ-053
#: states "every `contract_versions` member (HMIC-REQ-067, seven
#: entries) receives both bindings uniformly -- no `contract_versions`
#: member is exempted." There is no HMIC-001 textual basis for a
#: narrower "Wave A closed-schema acceptance set" distinct from Wave B's
#: derivation -- both terms name the same `contract_versions` field
#: (HMIC-REQ-032). Before this repair, the pre-existing `HBDC-001` gap
#: (introduced 149O.20D/149O.20F, when `_CONTRACT_IDENTITY_FILES` was
#: widened to include `HBDC-001` but this constant was not) meant no
#: `CertificationRecord` produced from `derive_contract_versions`'s own
#: current seven-member output could ever parse, and `validate_active_
#: hatp_mandatory_independent_verification_certification`'s step-10
#: dict-equality comparison (current seven-member mapping vs. a stored
#: record's schema-capped six-member `contract_versions`) could never
#: succeed for any record -- a load-bearing defect, not mere
#: out-of-scope drift, once 149O.20L.7O.2H's own v1.5 amendment made the
#: seven-member requirement explicit contract text.
_CONTRACT_VERSIONS_REQUIRED_KEYS = frozenset(
    {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"}
)


# ═══════════════════════════════════════════════════════════════════════════
# Errors
# ═══════════════════════════════════════════════════════════════════════════


class HATPMandatoryCertificationError(Exception):
    """Base error for HMIC-001 certification model/parsing operations."""


class CertificationMalformedError(HATPMandatoryCertificationError):
    """A certification document, binding document, or individual record
    exists but fails strict validation (HMIC-REQ-031, HMIC-REQ-036). Never
    partially accepted -- the first failing check raises immediately."""


class HMICIdentityDerivationError(HATPMandatoryCertificationError):
    """Base error for Wave B identity-derivation failures (implementation
    identity or contract identity). Distinct in kind from
    `CertificationMalformedError` (a Wave A parsing/schema failure of an
    already-written document) and from `CertificationStatus` (a Wave D
    validation *outcome*, not implemented by this module): this signals
    that a `derive_*` function could not produce a value at all --
    derivation failure, never a validation judgment. Fails closed; no
    `derive_*` function below ever returns a partial, default, or
    best-effort identity value in place of raising one of these."""


class FrozenFileDerivationError(HMICIdentityDerivationError):
    """A HMIC-REQ-050 frozen file (or one of the seven contract files
    within it) could not be safely read for digest/version-header
    derivation: missing (HMIC-REQ-059), a symlink at the file itself or
    any parent path component up to the repository root (HMIC-REQ-061),
    or not a regular file (HMIC-REQ-062)."""


class GitIdentityDerivationError(HMICIdentityDerivationError):
    """`derive_implementation_commit` could not obtain a valid `git
    rev-parse HEAD` result (HMIC-REQ-046) -- not a Git repository, `HEAD`
    unavailable, or a non-SHA result. Never substituted with a fake or
    zero-valued commit SHA."""


class ContractIdentityDerivationError(HMICIdentityDerivationError):
    """`derive_contract_versions` could not derive a version for one of
    the seven HMIC-REQ-067 bound contracts: the contract file could not
    be safely read (see `FrozenFileDerivationError`), or its `**Contract
    ID:**`/`**Version:**` header is missing or does not match the
    expected contract ID."""


class RepositoryIdentityUnavailableError(HMICIdentityDerivationError):
    """`derive_repository_instance_id` found no established Layer-1
    `repository_instance_id` for this repository
    (`repository_identity.py`'s identity file is absent). Wave B fails
    closed here rather than silently creating one as a side effect of a
    read-only identity derivation -- identity creation, if ever wanted,
    is a caller decision (`ensure_repository_identity`), never implicit
    inside certification-identity derivation."""


class CertificationStorageSymlinkError(HATPMandatoryCertificationError):
    """A certification-store path -- the Protected Root itself, any
    parent directory component, `certifications.json`,
    `certification-bindings.json`, or the `.certification-transition.
    lock` file -- is a symlink (HMIC-REQ-128). Rejected, never followed,
    identically to Wave B's frozen-file symlink discipline."""


class CertificationRecordNotFoundError(HATPMandatoryCertificationError):
    """No stored `CertificationRecord` exists for an explicitly-requested
    `certification_id` (HMIC-REQ-037's explicit-ID-only lookup
    discipline -- never `load_latest`/`get_current_valid`). Distinct
    from `CertificationMalformedError` (a record or document that exists
    but fails strict parsing) -- this module's readers preserve the
    missing/malformed distinction so a future Wave D validator can map
    each to its own `CertificationStatus` member."""


class CertificationConflictError(HATPMandatoryCertificationError):
    """A create-once write (HMIC-REQ-084/098) or a revocation write
    (HMIC-REQ-091/100) found existing stored content that conflicts with
    the candidate write -- a different authority-sensitive field value
    at the same `certification_id`, or a differing `revoked_at` for an
    already-revoked record. The existing stored state is never
    overwritten or replaced; only an exact byte-identical replay is
    treated as an idempotent no-op (HMIC-REQ-098)."""


class CertificationIdentityMismatchError(HATPMandatoryCertificationError):
    """A candidate `CertificationRecord` passed to `_append_certification_
    record` is not self-consistent: re-deriving `certification_id`
    (Wave B's pure `derive_certification_id`) from the record's own
    already-stated eight authority-sensitive fields does not match the
    record's own stated `certification_id`. This is a structural
    self-consistency check on the candidate record's own bytes only --
    it never reads Git, the frozen file set, or contract state, and is
    not the Wave D validation algorithm's own re-derivation-against-
    current-state check (HMIC-REQ-040); it exists so this module never
    persists a record whose stated identity does not match its own
    content, regardless of who or what constructed it."""


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


# ═══════════════════════════════════════════════════════════════════════════
# Wave B: Implementation Identity -- Frozen Authority-Bearing File Set
# (HMIC-REQ-050, §17)
# ═══════════════════════════════════════════════════════════════════════════

#: HMIC-REQ-050 (Exact Enumeration, No Prose Substitute): the frozen
#: authority-bearing file set for `implementation_scope_digest`, string-
#: for-string identical to the contract's literal enumeration (§17) --
#: the first `_FROZEN_SRC_PCAE_RELATIVE_COUNT` entries exactly as given
#: relative to `src/pcae/`, the remaining entries exactly as given
#: relative to the repository root (the nine bound repository-root-
#: relative entries: the seven bound contract files plus the two
#: Protected Admin ceremony scripts). Embedded directly here
#: (HMIC-REQ-051): not an
#: external, agent-editable manifest, not a config file, not an
#: environment override, not discovered by directory glob or "all
#: imported files" inference. This constant is never mutated, never
#: appended to at runtime, and carries no caller-suppliable "legacy"
#: 22-file scope selector -- as of HMIC-001 v1.1 (Phase 149O.19.5E.3,
#: resolving Stop Condition W-1's production-alignment half), this
#: module (`hatp_mandatory_certification.py`) IS itself a member: its
#: own post-edit bytes participate in the digest it computes
#: (HMIC-REQ-050/052(b), §50 of the contract). The final three entries,
#: `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_
#: verifier.py`, and `hatp_class_b_conformance.py`, were added at v1.3
#: by Phase 149O.20K's newly-added closure limb (c) (contract §53) and
#: aligned into this production constant by Phase 149O.20K.2, using the
#: identical `src/pcae/`-relative binding mechanism already applied to
#: every other entry in this tuple -- no new mechanism, no Class-B-
#: specific branch. The final entry, `hatp_deployment_binding_admin.py`,
#: was added at v1.4 by Phase 149O.20L.7K under limb (c)'s newly-widened
#: third anchor (contract §55), binding the `DeploymentBinding` producer
#: whose write output the already-bound `hatp_class_b_conformance.py`
#: reads (via already-bound `hatp_bootstrap.py`) to help compute the
#: same Class-B verdict -- aligned into this production constant in the
#: same phase as the contract amendment, unlike the split
#: contract-then-alignment sequencing 149O.20K/149O.20K.2 used. The
#: final three entries, `hatp_signing_ceremony.py`, `hatp_hardware_
#: credential_admin.py`, and `hatp_principal_signer_admin.py`, were
#: added at v1.5 by Phase 149O.20L.7O.2H under newly-added closure limb
#: (d) (contract §59), binding the Trust-Enrollment/signing authority
#: surface -- the production signing ceremony's own entry point,
#: `production_sign_rollback_evidence`, plus the hardware-credential and
#: principal/signer administrative writers as a non-reachability second
#: anchor (mirroring limb (c)'s own dual-anchor construction) -- aligned
#: into this production constant in the same phase as the contract
#: amendment, per the 149O.20L.7K precedent. `paths.py` was added at
#: v1.6 by Phase 149O.20L.7O.2H.2 after independent verification proved
#: that its reached `HarnessPath.join`/`.path` behavior selects the live
#: AG3/AG5 operation records whose `original_commit_sha`/`ecp_id` become
#: signing-authority inputs. It is bound unchanged; this module does not
#: special-case its digest treatment.
_FROZEN_SRC_PCAE_RELATIVE_FILES: "tuple[str, ...]" = (
    "core/hatp_mandatory_cutover.py",
    "core/hatp_ag_authority.py",
    "core/hatp_rollback_consumption.py",
    "core/hatp_bootstrap.py",
    "core/human_approval_trusted_provenance.py",
    "core/repository_identity.py",
    "core/rollback_approval_evidence.py",
    "core/hatp_evidence_store.py",
    "core/hatp_signed_evidence.py",
    "core/agent.py",
    "commands/agent.py",
    "cli.py",
    "core/permission_broker.py",
    "core/permission_broker_foundation.py",
    "core/hatp_providers.py",
    "core/hatp_fido2_provider.py",
    "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py",
    "core/hatp_mandatory_certification.py",
    "core/hatp_class_b_topology_verifier.py",
    "core/hatp_environment_lock_verifier.py",
    "core/hatp_class_b_conformance.py",
    "core/hatp_deployment_binding_admin.py",
    "core/hatp_signing_ceremony.py",
    "core/hatp_hardware_credential_admin.py",
    "core/hatp_principal_signer_admin.py",
    "core/paths.py",
)

#: HMIC-REQ-050's last nine entries: the seven bound contract files
#: (HMIC-REQ-053 -- their bytes participate in `implementation_scope_
#: digest` directly, a distinct binding from `contract_versions` below)
#: plus, as of v1.1, the Protected Admin ceremony script
#: (`scripts/hatp_certification_admin.py`, HMIC-REQ-052(b)), plus, as of
#: v1.4, the DeploymentBinding admin ceremony script (`scripts/hatp_
#: deployment_binding_admin.py`, HMIC-REQ-052(c)'s third anchor,
#: contract §55). Repository-root-relative exactly as the contract
#: states; neither script's path needs `src/pcae/`-prefix special-casing
#: (HMIC-REQ-055). The fifth contract entry, `HATP_CLASS_B_DEPLOYMENT_
#: CONTRACT.md` (HBDC-001), was added at v1.2 by the 149O.20D.1
#: content-identity binding repair (finding B-149O.20D-1, contract §52)
#: and aligned into this production constant by Phase 149O.20F -- no new
#: mechanism, the identical mechanism already applied to the other four
#: bound contracts. The sixth and seventh contract entries,
#: `HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` (HPSE-001) and
#: `HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` (HHCE-001), were
#: added at v1.5 by Phase 149O.20L.7O.2H (contract §59) -- bound the
#: moment both contracts joined `contract_versions` below, per
#: HMIC-REQ-053's uniform no-exemption rule, not via closure limb (d)'s
#: call-graph logic.
_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES: "tuple[str, ...]" = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
    "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
    "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
    "scripts/hatp_certification_admin.py",
    "scripts/hatp_deployment_binding_admin.py",
)

_FROZEN_SRC_PCAE_RELATIVE_COUNT = len(_FROZEN_SRC_PCAE_RELATIVE_FILES)

#: The full 36-entry literal enumeration (v1.6, aligned by Phase
#: 149O.20L.7O.2H.2), in exactly the contract's presentation order
#: (HMIC-REQ-050) -- the 36-file manifest test compares this, entry for
#: entry, against a fresh extraction of the live contract text. `_frozen_
#: canonical_paths()` below derives the repository-relative canonical
#: path string HMIC-REQ-055 requires for digest computation; this
#: constant intentionally preserves the contract's own literal
#: (non-prefixed, non-sorted) strings.
_FROZEN_AUTHORITY_BEARING_FILES: "tuple[str, ...]" = (
    _FROZEN_SRC_PCAE_RELATIVE_FILES + _FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
)

assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 36  # HMIC-REQ-050 (v1.6): exactly 36, no more, no fewer.


def _validate_frozen_path_literal(canonical_path: str) -> None:
    """HMIC-REQ-055 (Path Canonicalization), applied to this module's own
    trusted literal constants (never to caller input -- there is no
    caller-supplied path list, HMIC-REQ-051): repository-relative,
    POSIX-separator, no `..` segment, no absolute component, no empty
    component, no backslash. A failure here indicates a defect in this
    module's own frozen constant, not an attacker-controlled input."""

    if not canonical_path or canonical_path.startswith("/"):
        raise HMICIdentityDerivationError(f"frozen path constant is not repository-relative: {canonical_path!r}")
    if "\\" in canonical_path:
        raise HMICIdentityDerivationError(f"frozen path constant contains a backslash: {canonical_path!r}")
    segments = canonical_path.split("/")
    if any(segment in ("", ".", "..") for segment in segments):
        raise HMICIdentityDerivationError(f"frozen path constant has an unsafe path segment: {canonical_path!r}")


def _canonical_frozen_path(entry: str, index: int) -> str:
    """Combines a literal `_FROZEN_AUTHORITY_BEARING_FILES` entry with
    its implied root (HMIC-REQ-050's own prefix note: the first
    `_FROZEN_SRC_PCAE_RELATIVE_COUNT` entries are `src/pcae/`-relative,
    the rest are repository-root-relative) to produce the repository-
    relative canonical path string HMIC-REQ-055 requires."""

    _validate_frozen_path_literal(entry)
    if index < _FROZEN_SRC_PCAE_RELATIVE_COUNT:
        return f"src/pcae/{entry}"
    return entry


def _frozen_canonical_paths() -> "tuple[str, ...]":
    """HMIC-REQ-056 (File Order): the canonical, repository-relative
    paths of the frozen file set, in exact lexicographic order --
    never filesystem enumeration order, never this module's own literal
    presentation order (which is not itself lexicographic)."""

    paths = [
        _canonical_frozen_path(entry, index) for index, entry in enumerate(_FROZEN_AUTHORITY_BEARING_FILES)
    ]
    return tuple(sorted(paths))


# ═══════════════════════════════════════════════════════════════════════════
# Wave B: frozen-file safety (HMIC-REQ-059, HMIC-REQ-061, HMIC-REQ-062)
# and TOCTOU-resistant read
# ═══════════════════════════════════════════════════════════════════════════


def _resolve_and_reject_unsafe_frozen_file(repository_root: Path, canonical_path: str) -> Path:
    """Resolves one HMIC-REQ-050 canonical path to an on-disk target,
    rejecting it (`FrozenFileDerivationError`) if the path itself or any
    parent directory component up to (but not including)
    `repository_root` is a symlink (HMIC-REQ-061), if it does not exist
    (HMIC-REQ-059), or if it is not a regular file (HMIC-REQ-062). No
    attacker-controlled external symlink target is ever resolved."""

    target = repository_root / canonical_path
    current = target
    while current != repository_root:
        if current.is_symlink():
            raise FrozenFileDerivationError(
                f"frozen file path component is a symlink, refusing: {current} (frozen path: {canonical_path})"
            )
        parent = current.parent
        if parent == current:
            break  # reached filesystem root without finding repository_root -- stop, do not loop forever.
        current = parent
    if not target.exists():
        raise FrozenFileDerivationError(f"frozen file does not exist: {canonical_path}")
    if not target.is_file():
        raise FrozenFileDerivationError(f"frozen file is not a regular file: {canonical_path}")
    return target


def _read_frozen_file_bytes(target: Path, *, canonical_path: str) -> bytes:
    """TOCTOU-resistant read of an already-safety-checked frozen file:
    opens with `O_NOFOLLOW` where the platform supports it (so a
    symlink swapped in between the `_resolve_and_reject_unsafe_frozen_
    file` check and this open fails closed rather than silently
    following it), re-checks the open file descriptor's own `fstat`
    mode is a regular file, then reads its raw bytes (HMIC-REQ-054:
    working-tree bytes, never `git show HEAD:<path>`)."""

    open_flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        open_flags |= os.O_NOFOLLOW
    try:
        fd = os.open(str(target), open_flags)
    except OSError as exc:
        raise FrozenFileDerivationError(f"frozen file could not be opened: {canonical_path}: {exc}") from exc
    try:
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            raise FrozenFileDerivationError(f"frozen file is not a regular file: {canonical_path}")
        with os.fdopen(fd, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise FrozenFileDerivationError(f"frozen file could not be read: {canonical_path}: {exc}") from exc


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# Wave B: `derive_repository_instance_id`, `derive_canonical_deployment_
# root` (HMIC-REQ-043, HMIC-REQ-044)
# ═══════════════════════════════════════════════════════════════════════════


def derive_repository_instance_id(root: HarnessPath) -> str:
    """HMIC-REQ-043: derived exactly as `repository_identity.py`'s
    existing CRI Model A Layer 1 identity -- never a new identity
    system, never path-only identity, and never a caller-supplied
    override. `root` is a neutral repository locator only (the identical
    pattern `hatp_mandatory_cutover.py::_resolve_current_repository_
    instance_id` already uses). Fails closed
    (`RepositoryIdentityUnavailableError`) if no identity has been
    established yet -- this function never creates one as a read
    side effect."""

    identity = read_repository_identity(root)
    if identity is None:
        raise RepositoryIdentityUnavailableError(
            "no repository_instance_id is established for this repository "
            "(repository-identity.json is absent)"
        )
    return identity.repository_instance_id


def derive_canonical_deployment_root(root: HarnessPath) -> str:
    """HMIC-REQ-044: derived exactly as `hatp_bootstrap.py::resolve_
    canonical_deployment_root`/`DeploymentBinding` already define it --
    no new canonicalization scheme."""

    try:
        return resolve_canonical_deployment_root(root.path)
    except OSError as exc:
        raise HMICIdentityDerivationError(f"could not resolve canonical deployment root: {exc}") from exc


# ═══════════════════════════════════════════════════════════════════════════
# Wave B: `derive_implementation_commit` (HMIC-REQ-046)
# ═══════════════════════════════════════════════════════════════════════════

_GIT_COMMAND_TIMEOUT_SECONDS = 10


def _run_git(root: HarnessPath, args: "list[str]") -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=str(root.path),
            timeout=_GIT_COMMAND_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def derive_implementation_commit(root: HarnessPath) -> str:
    """HMIC-REQ-046: `implementation_commit` is the git commit SHA of
    `HEAD`, obtained via `git rev-parse HEAD`. Fails closed
    (`GitIdentityDerivationError`) -- never a fake or zero-valued SHA --
    if `root` is not a Git repository, `HEAD` is unavailable, or the
    result is not a well-formed commit SHA."""

    sha = _run_git(root, ["rev-parse", "HEAD"])
    if not sha or not _COMMIT_SHA_RE.fullmatch(sha):
        raise GitIdentityDerivationError(
            "could not determine a valid git HEAD commit SHA (git rev-parse HEAD failed, "
            "returned a non-SHA value, or is not a Git repository)"
        )
    return sha


# ═══════════════════════════════════════════════════════════════════════════
# Wave B: `derive_implementation_scope_digest` (HMIC-REQ-054-062)
# ═══════════════════════════════════════════════════════════════════════════


def derive_implementation_scope_digest(root: HarnessPath) -> str:
    """HMIC-REQ-058: the SHA-256 hex digest of the concatenation, in
    HMIC-REQ-056's lexicographic order, of every HMIC-REQ-057 per-file
    record (`<canonical_path> + "\\0" + <sha256_hex_of_file_bytes> +
    "\\n"`, UTF-8) for every path in HMIC-REQ-050 -- a two-level
    construction (hash each file's bytes first, then hash the ordered,
    delimited list of path+digest records), never a single-level "hash
    all file bytes concatenated" scheme. HMIC-REQ-054: SHA-256 of raw
    working-tree bytes, never a Git blob. Fails closed
    (`FrozenFileDerivationError`) on the first missing, symlinked, or
    non-regular frozen file -- no partial digest is ever returned."""

    repository_root = root.path
    hasher = hashlib.sha256()
    for canonical_path in _frozen_canonical_paths():
        target = _resolve_and_reject_unsafe_frozen_file(repository_root, canonical_path)
        file_bytes = _read_frozen_file_bytes(target, canonical_path=canonical_path)
        file_digest = _sha256_hex(file_bytes)
        record = f"{canonical_path}\0{file_digest}\n".encode("utf-8")
        hasher.update(record)
    return hasher.hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# Wave B: `derive_contract_versions` (HMIC-REQ-067, HMIC-REQ-069)
# ═══════════════════════════════════════════════════════════════════════════

#: HMIC-REQ-067 (v1.5): the minimal sufficient `contract_versions` set --
#: exactly these seven, in this fixed, deliberate order (never dict-hash
#: order, never filesystem/glob order). `RWMPC-001`, `PBPA-001`,
#: `PBPC-001` are explicitly excluded (HMIC-REQ-068) -- their module
#: *bytes* still participate in `implementation_scope_digest` above via
#: `permission_broker.py`/`permission_broker_foundation.py`'s frozen-set
#: membership, but their *contract version* is not part of this binding.
#: `HBDC-001` was added at v1.2 (149O.20D, HMIC-REQ-067) and aligned into
#: this production constant by Phase 149O.20F, using the identical
#: path/version-header derivation mechanism as the other four members --
#: no HBDC-specific parsing branch. `HPSE-001`/`HHCE-001` were added at
#: v1.5 (149O.20L.7O.2H, HMIC-REQ-067/053, contract §59) and aligned into
#: this production constant in the same phase as the contract amendment
#: -- content- and version-bound from admission, using the identical
#: mechanism already applied to the other five members.
_CONTRACT_IDENTITY_FILES: "tuple[tuple[str, str], ...]" = (
    ("HMRC-001", "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"),
    ("HATP-001", "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"),
    ("HSCE-001", "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"),
    ("RAE-001", "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"),
    ("HBDC-001", "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"),
    ("HPSE-001", "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"),
    ("HHCE-001", "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"),
)

#: HMIC-001 itself, and every contract examined in this repository,
#: begins with a `**Version:** <version>` metadata line, and a contract-
#: ID label line -- but HMIC-001's text never gives an explicit parsing
#: grammar for this header (a documented ambiguity, not an inferred
#: one), and the seven bound contracts are not even byte-consistent with
#: each other about the label: HMRC-001 uses `**Contract ID:**` while
#: HATP-001/HSCE-001/RAE-001/HBDC-001/HPSE-001/HHCE-001 use
#: `**Contract:**` (confirmed by direct inspection of all seven live
#: files). Both label spellings are
#: matched -- this is convention-matching against the contracts' own
#: observed, live text, not a guessed grammar; nothing here treats any
#: other label variant as equivalent.
_CONTRACT_ID_HEADER_RE = re.compile(r"^\*\*Contract(?: ID)?:\*\*\s*(\S+)\s*$", re.MULTILINE)
_CONTRACT_VERSION_HEADER_RE = re.compile(r"^\*\*Version:\*\*\s*(\S+)\s*$", re.MULTILINE)


def derive_contract_versions(root: HarnessPath) -> Mapping[str, str]:
    """HMIC-REQ-067: reads the seven bound contracts' own `**Version:**`
    header, by contract ID, from their exact canonical paths (never a
    dynamic search by title, never "first matching file" -- HMIC-REQ-
    069's drift comparison requires each contract's own live header).
    Each of the seven files is safety-checked identically to the frozen-
    file-set files above (HMIC-REQ-061/062 apply equally to contract
    files, since they are also HMIC-REQ-050 members). Fails closed
    (`ContractIdentityDerivationError`) if a file is unreadable, or its
    header is missing or names an unexpected contract ID -- never a
    silently-inferred version."""

    repository_root = root.path
    versions: "dict[str, str]" = {}
    for contract_id, canonical_path in _CONTRACT_IDENTITY_FILES:
        try:
            target = _resolve_and_reject_unsafe_frozen_file(repository_root, canonical_path)
            data = _read_frozen_file_bytes(target, canonical_path=canonical_path)
        except FrozenFileDerivationError as exc:
            raise ContractIdentityDerivationError(f"{contract_id}: {exc}") from exc
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContractIdentityDerivationError(f"{contract_id}: contract file is not valid UTF-8: {exc}") from exc

        id_match = _CONTRACT_ID_HEADER_RE.search(text)
        version_match = _CONTRACT_VERSION_HEADER_RE.search(text)
        if id_match is None or version_match is None:
            raise ContractIdentityDerivationError(
                f"{contract_id}: missing or malformed 'Contract ID'/'Version' header in {canonical_path}"
            )
        parsed_id = id_match.group(1)
        if parsed_id != contract_id:
            raise ContractIdentityDerivationError(
                f"{canonical_path}: header Contract ID {parsed_id!r} does not match expected {contract_id!r}"
            )
        versions[contract_id] = version_match.group(1)
    return MappingProxyType(versions)


# ═══════════════════════════════════════════════════════════════════════════
# Wave B: `derive_certification_id` (HMIC-REQ-038) -- pure, no I/O
# ═══════════════════════════════════════════════════════════════════════════

#: HMIC-REQ-038: `certification_id` is a SHA-256 hex digest computed over
#: the canonical serialization (HMIC-REQ-041/042) of exactly these eight
#: authority-sensitive fields -- excluding `certification_id` itself
#: (computed before it is assigned) and excluding `status`/`revoked_at`
#: (mutable fields never participate in the identity digest).
_CERTIFICATION_ID_INPUT_FIELDS: "tuple[str, ...]" = (
    "repository_instance_id",
    "canonical_deployment_root",
    "implementation_commit",
    "implementation_scope_digest",
    "contract_versions",
    "verification_record_digest",
    "certified_at",
    "certified_by",
)
_CERTIFICATION_ID_INPUT_FIELDS_SET = frozenset(_CERTIFICATION_ID_INPUT_FIELDS)


def derive_certification_id(record_fields: Mapping[str, object]) -> str:
    """HMIC-REQ-038: pure function, no filesystem/Git/network I/O --
    `record_fields` must already contain exactly the eight HMIC-REQ-038
    input fields (typically produced by calling the other `derive_*`
    functions above and combining their results with the caller's own
    `verification_record_digest`/`certified_at`/`certified_by` values).
    This function performs no certification-validity judgment and
    accepts no caller-supplied override of the digest inputs beyond the
    values the caller itself already assembled -- it does not read, and
    has no access to, certification state."""

    present = set(record_fields.keys())
    missing = _CERTIFICATION_ID_INPUT_FIELDS_SET - present
    if missing:
        raise HMICIdentityDerivationError(f"certification_id derivation is missing required fields: {sorted(missing)}")
    unknown = present - _CERTIFICATION_ID_INPUT_FIELDS_SET
    if unknown:
        raise HMICIdentityDerivationError(f"certification_id derivation received unexpected fields: {sorted(unknown)}")

    payload: dict = {}
    for key in _CERTIFICATION_ID_INPUT_FIELDS:
        value = record_fields[key]
        if key == "contract_versions":
            if not isinstance(value, Mapping):
                raise HMICIdentityDerivationError(
                    f"certification_id derivation: contract_versions must be a mapping, got {value!r}"
                )
            value = dict(value)
        payload[key] = value

    serialized = canonical_serialize(payload)
    return _sha256_hex(serialized)


# ═══════════════════════════════════════════════════════════════════════════
# Wave C: Protected Certification State Store (Phase 149O.19.5C)
#
# HMIC-REQ-021-027 (topology), HMIC-REQ-083-084 (write safety),
# HMIC-REQ-085-090 (active binding / no implicit latest), HMIC-REQ-091-100
# (revocation / concurrency), HMIC-REQ-097-102 (locking), HMIC-REQ-128-129
# (path safety). Wave C never evaluates certification VALID-ity, never
# compares stored state against current implementation/contract identity
# (that is Wave D, HMIC-REQ-103's 12-step algorithm, not implemented here),
# and never wires into `hatp_mandatory_cutover.py`. The two on-disk files
# below live directly under `HATPTrustStore.production().root` -- never a
# second root, never `.pcae/**` (HMIC-REQ-021-023) -- and both files are
# single, shared documents whose *entries* are keyed by
# `(repository_instance_id, canonical_deployment_root)` (HMIC-REQ-026): no
# directory-per-repository layout, no per-certification filesystem path is
# ever derived from `certification_id` (HMIC-REQ-129).
# ═══════════════════════════════════════════════════════════════════════════

#: HMIC-REQ-025: exactly two files, frozen names, both directly under the
#: Protected Root. No third certification-related file exists in v1.0.
_CERTIFICATIONS_FILE_NAME = "certifications.json"
_CERTIFICATION_BINDINGS_FILE_NAME = "certification-bindings.json"

#: HMIC-REQ-097/102: a dedicated lock file, fixed under the Protected Root,
#: distinct from HMRC-001's own `.cutover-transition.lock`
#: (`hatp_mandatory_cutover.py::_CUTOVER_TRANSITION_LOCK_FILE_NAME`) -- the
#: two concerns never serialize on each other (HMIC-REQ-101).
_CERTIFICATION_TRANSITION_LOCK_FILE_NAME = ".certification-transition.lock"


# ═══════════════════════════════════════════════════════════════════════════
# Wave C: protected path safety (HMIC-REQ-128), generalized from Wave B's
# `_resolve_and_reject_unsafe_frozen_file` walk-to-root discipline to
# storage paths that may not yet exist (a certification file that has
# simply never been written is not itself unsafe -- only an existing
# symlink anywhere in the chain from the Protected Root down is).
# ═══════════════════════════════════════════════════════════════════════════


def _reject_unsafe_protected_path(protected_root: Path, target: Path) -> None:
    """HMIC-REQ-128: reject the Protected Root itself, or any existing path
    component from `target` up to (and including) `protected_root`, that
    is a symlink. Never resolves or follows the rejected symlink's target
    -- refuses outright, mirroring `hatp_mandatory_cutover.py::_reject_
    symlink` and Wave B's `_resolve_and_reject_unsafe_frozen_file` exactly,
    generalized to cover the full parent chain (HMIC-REQ-128 explicitly
    extends this to "every parent directory component", not merely the
    immediate parent `_reject_symlink` checks elsewhere in this
    codebase)."""

    if protected_root.is_symlink():
        raise CertificationStorageSymlinkError(f"HMIC protected root is a symlink, refusing: {protected_root}")
    protected_root_parent = protected_root.parent
    if protected_root_parent.exists() and protected_root_parent.is_symlink():
        raise CertificationStorageSymlinkError(
            f"HMIC protected root's parent directory is a symlink, refusing: {protected_root_parent}"
        )
    current = target
    while current != protected_root:
        if current.is_symlink():
            raise CertificationStorageSymlinkError(
                f"HMIC protected-storage path component is a symlink, refusing: {current}"
            )
        parent = current.parent
        if parent == current:
            break  # reached filesystem root without finding protected_root -- stop, do not loop forever.
        current = parent


# ═══════════════════════════════════════════════════════════════════════════
# Wave C: atomic write idiom (HMIC-REQ-083) -- `mkstemp` + `fsync` +
# `os.replace`, identical to `hatp_mandatory_cutover.py::_atomic_write_
# json`/`repository_identity.py::_write_atomic`, reusing this module's own
# `canonical_serialize` (HMIC-REQ-041/042) rather than an ad hoc `json.
# dumps` call -- every certification-file write and every digest input
# share exactly one canonical form.
# ═══════════════════════════════════════════════════════════════════════════


def _atomic_write_protected_json(protected_root: Path, path: Path, document: dict) -> None:
    _reject_unsafe_protected_path(protected_root, path)
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    payload = canonical_serialize(document)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-hmic-", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        # Re-check immediately before the replace (TOCTOU discipline,
        # mirroring `_atomic_write_json`'s own pre-replace re-check): a
        # symlink swapped in during the write window is still refused.
        _reject_unsafe_protected_path(protected_root, path)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


# ═══════════════════════════════════════════════════════════════════════════
# Wave C: `.certification-transition.lock` (HMIC-REQ-097/101/102)
# ═══════════════════════════════════════════════════════════════════════════


@contextmanager
def _certification_transition_lock(protected_root: Path) -> Iterator[None]:
    """HMIC-REQ-097: exclusive `fcntl.flock` on a dedicated lock file
    directly under the Protected Root -- fixed path (HMIC-REQ-102: no
    caller-suppliable lock-file path exists), distinct from HMRC-001's own
    `.cutover-transition.lock` (HMIC-REQ-097/101, so certification writes
    never serialize against Cutover Record writes, and no certification
    write is ever performed from inside `activate_hatp_mandatory`'s own
    lock). Only certification *writes* (`_append_certification_record`/
    `_write_active_binding`/`_write_revocation`) acquire this lock; every
    read function in this module is lock-free (HMIC-REQ-101: a read-only
    certification-file read performed from inside HMRC-001's own
    activation-lock-held recheck must not itself acquire this lock).

    Creates the Protected Root directory (`mkdir(parents=True,
    exist_ok=True)`) if absent -- but only on this write path, never from
    any read function (HMIC-REQ-per phase-scope 'no auto-provisioning on
    ordinary read'; mirrors `_write_cutover_transition`'s identical
    root-creation-on-write-only discipline)."""

    protected_root.mkdir(parents=True, exist_ok=True)
    lock_path = protected_root / _CERTIFICATION_TRANSITION_LOCK_FILE_NAME
    _reject_unsafe_protected_path(protected_root, lock_path)
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


# ═══════════════════════════════════════════════════════════════════════════
# Wave C: document-level readers (HMIC-REQ-025/031/036) -- tri-state
# (OK / ABSENT / MALFORMED), mirroring `hatp_mandatory_cutover.py`'s own
# `_ReadStatus`/`_read_cutover_record` shape exactly. Never acquire the
# transition lock (HMIC-REQ-101); never create the Protected Root or
# either file (no auto-provisioning on read).
# ═══════════════════════════════════════════════════════════════════════════


class _ReadStatus(str, Enum):
    OK = "ok"
    ABSENT = "absent"
    MALFORMED = "malformed"


@dataclass(frozen=True)
class _CertificationsReadResult:
    status: _ReadStatus
    document: Optional[CertificationsDocument] = None


@dataclass(frozen=True)
class _CertificationBindingsReadResult:
    status: _ReadStatus
    document: Optional[CertificationBindingsDocument] = None


def _read_raw_protected_file(protected_root: Path, path: Path) -> "tuple[_ReadStatus, Optional[bytes]]":
    try:
        _reject_unsafe_protected_path(protected_root, path)
    except CertificationStorageSymlinkError:
        # HMIC-REQ-128/HMIC-REQ item-25 (symlink rejected): folded into
        # MALFORMED at this layer -- rejected, never followed, and never
        # confused with a genuinely absent file (HMIC-REQ item-84,
        # missing-vs-malformed preserved).
        return _ReadStatus.MALFORMED, None
    if not path.exists():
        return _ReadStatus.ABSENT, None
    if not path.is_file():
        # Non-regular object -- directory, FIFO, socket, device -- rejected
        # identically to a symlink (HMIC-REQ item-26).
        return _ReadStatus.MALFORMED, None
    try:
        return _ReadStatus.OK, path.read_bytes()
    except OSError:
        return _ReadStatus.MALFORMED, None


def _read_certifications(protected_root: Path) -> _CertificationsReadResult:
    """HMIC-REQ-025/031: reads `certifications.json` fresh, no cache. A
    missing file is `ABSENT` (no certifications have ever been created for
    this Protected Root); a present-but-unparsable file is `MALFORMED`
    (never silently treated as `ABSENT` -- HMIC-REQ item-84's
    anti-corruption-downgrade discipline, mirroring `hatp_mandatory_
    cutover.py::_read_cutover_activation_marker`'s identical reasoning)."""

    path = protected_root / _CERTIFICATIONS_FILE_NAME
    status, raw = _read_raw_protected_file(protected_root, path)
    if status != _ReadStatus.OK:
        return _CertificationsReadResult(status)
    try:
        document = parse_certifications_document_from_bytes(raw)
    except CertificationMalformedError:
        return _CertificationsReadResult(_ReadStatus.MALFORMED)
    return _CertificationsReadResult(_ReadStatus.OK, document)


def _read_certification_bindings(protected_root: Path) -> _CertificationBindingsReadResult:
    """As `_read_certifications`, for `certification-bindings.json`
    (HMIC-REQ-025/036). A missing file means "no binding entry exists for
    any repository/deployment key yet" -- never "look up the latest
    certification instead" (HMIC-REQ-085/HMIC-REQ item-36)."""

    path = protected_root / _CERTIFICATION_BINDINGS_FILE_NAME
    status, raw = _read_raw_protected_file(protected_root, path)
    if status != _ReadStatus.OK:
        return _CertificationBindingsReadResult(status)
    try:
        document = parse_certification_bindings_document_from_bytes(raw)
    except CertificationMalformedError:
        return _CertificationBindingsReadResult(_ReadStatus.MALFORMED)
    return _CertificationBindingsReadResult(_ReadStatus.OK, document)


# ═══════════════════════════════════════════════════════════════════════════
# Wave C: explicit-ID load APIs (HMIC-REQ-019/037/090) -- no
# `load_latest`/`get_current_valid` form exists anywhere in this module.
# ═══════════════════════════════════════════════════════════════════════════


def _load_certification_record(protected_root: Path, certification_id: str) -> CertificationRecord:
    """Internal, explicit-ID-only test/production seam (HMIC-REQ-037): no
    `certified_at`-sorted "latest" fallback exists. Distinguishes "no
    certifications.json at all" from "certifications.json exists but does
    not contain this ID" from "certifications.json is malformed" -- all
    three fail closed as typed errors, never silently returning a
    different record."""

    result = _read_certifications(protected_root)
    if result.status == _ReadStatus.ABSENT:
        raise CertificationRecordNotFoundError(
            f"no certifications.json exists under the protected root; certification_id={certification_id!r} not found"
        )
    if result.status == _ReadStatus.MALFORMED:
        raise CertificationMalformedError("certifications.json exists but is malformed")
    for record in result.document.certifications:
        if record.certification_id == certification_id:
            return record
    raise CertificationRecordNotFoundError(f"no certification record found for certification_id={certification_id!r}")


def _load_active_binding(
    protected_root: Path, *, repository_instance_id: str, canonical_deployment_root: str
) -> Optional[CertificationBinding]:
    """Internal, explicit repository/deployment-keyed lookup (HMIC-REQ-026,
    HMIC-REQ-085): returns the `CertificationBinding` for this exact key if
    a binding entry exists for it, or `None` -- meaning explicitly "no
    active certification is bound for this key" -- if no entry exists.
    Never resolved by scanning, sorting, or globbing `certifications.json`
    itself (HMIC-REQ-085's implicit-latest prohibition); never rewrites or
    clears a binding merely because its pointed-to record is later revoked
    (that remains storable and loadable exactly as bound -- Wave D alone
    interprets it)."""

    result = _read_certification_bindings(protected_root)
    if result.status == _ReadStatus.ABSENT:
        return None
    if result.status == _ReadStatus.MALFORMED:
        raise CertificationMalformedError("certification-bindings.json exists but is malformed")
    for binding in result.document.bindings:
        if binding.repository_instance_id == repository_instance_id and binding.canonical_deployment_root == canonical_deployment_root:
            return binding
    return None


def load_certification(certification_id: str, root: HarnessPath) -> CertificationRecord:
    """The sole production, agent-readable explicit-ID load entrypoint
    (HMIC-REQ-019: read access to certification state is not write
    authority). Resolves the Protected Root internally via `HATPTrustStore.
    production().root` -- no caller-suppliable root override
    (HMIC-REQ-023). `root` is a neutral parameter accepted for API-shape
    symmetry with this module's other production entrypoints only; it is
    not consulted to resolve the Protected Root. Establishes only that a
    well-formed `CertificationRecord` with this exact `certification_id`
    is currently stored -- never that it is active, unrevoked, or
    implementation-matched (HMIC-REQ-009's semantic wall; Wave D alone
    decides `VALID`)."""

    protected_root = HATPTrustStore.production().root
    return _load_certification_record(protected_root, certification_id)


def load_active_binding(root: HarnessPath) -> Optional[CertificationBinding]:
    """The sole production, agent-readable Active-Certification-Pointer
    load entrypoint (HMIC-REQ-085). Resolves the Protected Root and the
    repository/deployment key internally -- no caller-suppliable root,
    `repository_instance_id`, or `canonical_deployment_root` override
    (HMIC-REQ-023, mirroring Wave B's `derive_repository_instance_id`/
    `derive_canonical_deployment_root`, which this function calls
    unmodified). Returns `None` if no binding entry exists yet for this
    repository/deployment key -- never an implicit "look up any
    certification" fallback (HMIC-REQ-085/036)."""

    protected_root = HATPTrustStore.production().root
    repository_instance_id = derive_repository_instance_id(root)
    canonical_deployment_root = derive_canonical_deployment_root(root)
    return _load_active_binding(
        protected_root,
        repository_instance_id=repository_instance_id,
        canonical_deployment_root=canonical_deployment_root,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Wave C: internal, admin-only-caller write primitives (HMIC-REQ-076 step
# 6, HMIC-REQ-083-084, HMIC-REQ-086/088, HMIC-REQ-091-093/097-100). No
# production, agent-reachable API in this module calls these -- the only
# intended caller is a future Wave E `scripts/hatp_certification_admin.py`
# (outside `src/pcae/**`, never imported by `cli.py`/`commands/agent.py`),
# gated by real OS file permissions on the Protected Root, not by any
# in-process authority check here (HMIC-REQ-079's precedent, restated from
# `hatp_mandatory_cutover.py`'s own module docstring). Every writer below
# accepts an explicit `protected_root: Path` and is never called anywhere
# in this module with `HATPTrustStore.production().root`.
# ═══════════════════════════════════════════════════════════════════════════


def _recompute_certification_id(record: CertificationRecord) -> str:
    return derive_certification_id(
        {
            "repository_instance_id": record.repository_instance_id,
            "canonical_deployment_root": record.canonical_deployment_root,
            "implementation_commit": record.implementation_commit,
            "implementation_scope_digest": record.implementation_scope_digest,
            "contract_versions": record.contract_versions,
            "verification_record_digest": record.verification_record_digest,
            "certified_at": record.certified_at,
            "certified_by": record.certified_by,
        }
    )


@dataclass(frozen=True)
class CertificationAppendResult:
    """`_append_certification_record`'s sole return type. Never a bare
    boolean -- `idempotent=True` means an exact byte-identical record was
    already stored and no write occurred; `idempotent=False` means this
    call performed the append."""

    record: CertificationRecord
    idempotent: bool


def _append_certification_record(protected_root: Path, record: CertificationRecord) -> CertificationAppendResult:
    """HMIC-REQ-076 step 6 / HMIC-REQ-083-084/098: atomically appends
    `record` to `certifications.json` under the certification-transition
    lock. `record` must already be freshly constructed by the caller (a
    future Wave E admin tool, or this phase's own tests) with `status ==
    "active"` -- a record is never created pre-revoked; revocation is
    always the separate `_write_revocation` operation (HMIC-REQ-091).

    Self-consistency (HMIC-REQ item-16): before persisting, re-derives
    `certification_id` from the record's own eight stated fields and
    refuses (`CertificationIdentityMismatchError`) if it does not match
    the record's own stated `certification_id` -- a structural check of
    the candidate's own bytes only, never a comparison against current
    Git/contract state (that remains Wave D's job).

    Create-once (HMIC-REQ-084/098): if a record with the same
    `certification_id` already exists, an exact canonical-byte match is
    idempotent (no write, no duplicate entry); any byte difference --
    including a differing `status`/`revoked_at`, which this function never
    itself changes -- is rejected as `CertificationConflictError`. Never
    silently overwrites, and never mutates any other stored record."""

    if record.status != "active":
        raise ValueError(
            f"a freshly appended certification record must have status='active', got {record.status!r} "
            "-- revocation is a separate _write_revocation operation"
        )
    if _recompute_certification_id(record) != record.certification_id:
        raise CertificationIdentityMismatchError(
            f"record's certification_id {record.certification_id!r} does not match a fresh derivation "
            "from its own stated fields; refusing to persist a self-inconsistent record"
        )
    # Round-trip through the strict parser (HMIC-REQ-031/032) -- the same
    # validation domain the Wave A docstring's "constructor and parser
    # share one validation domain" principle promises for every record
    # this module ever persists, even one constructed directly via the
    # dataclass rather than via `parse_certification_record`.
    validated_record = parse_certification_record(certification_record_to_document(record))
    candidate_bytes = canonical_serialize(certification_record_to_document(validated_record))

    with _certification_transition_lock(protected_root):
        read_result = _read_certifications(protected_root)
        if read_result.status == _ReadStatus.MALFORMED:
            raise CertificationMalformedError("cannot append: certifications.json exists but is malformed")
        existing_doc = (
            read_result.document
            if read_result.status == _ReadStatus.OK
            else CertificationsDocument(schema_version=CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION, certifications=())
        )
        for existing in existing_doc.certifications:
            if existing.certification_id == validated_record.certification_id:
                existing_bytes = canonical_serialize(certification_record_to_document(existing))
                if existing_bytes == candidate_bytes:
                    return CertificationAppendResult(record=existing, idempotent=True)
                raise CertificationConflictError(
                    f"certification_id {validated_record.certification_id!r} already exists with differing "
                    "stored field values; refusing to overwrite"
                )
        new_doc = CertificationsDocument(
            schema_version=existing_doc.schema_version,
            certifications=existing_doc.certifications + (validated_record,),
        )
        _atomic_write_protected_json(
            protected_root,
            protected_root / _CERTIFICATIONS_FILE_NAME,
            certifications_document_to_document(new_doc),
        )
        return CertificationAppendResult(record=validated_record, idempotent=False)


def _write_active_binding(protected_root: Path, binding: CertificationBinding) -> CertificationBinding:
    """HMIC-REQ-086/088/099: sets (or replaces) the Active-Certification
    Pointer entry for `binding`'s exact `(repository_instance_id,
    canonical_deployment_root)` key, atomically, under the certification-
    transition lock. Binding entries for every other key are preserved
    unchanged (HMIC-REQ-026 multi-repository/multi-deployment isolation).

    Plain locked replacement, never compare-and-swap (HMIC-REQ-099:
    "whichever write completes second is the one that determines the
    final active pointer" -- no expected-old-value precondition is
    required or invented here). Never verifies that `binding.active_
    certification_id` names a record that actually exists in
    `certifications.json` -- HMIC-REQ item-57/-109: storage does not
    cross-check current implementation, and a binding may legitimately
    point at an as-yet-uncreated or already-revoked record; only Wave D's
    validator interprets that (`MISSING`/`REVOKED`)."""

    validated_binding = parse_certification_binding(certification_binding_to_document(binding))
    key = (validated_binding.repository_instance_id, validated_binding.canonical_deployment_root)

    with _certification_transition_lock(protected_root):
        read_result = _read_certification_bindings(protected_root)
        if read_result.status == _ReadStatus.MALFORMED:
            raise CertificationMalformedError("cannot update active binding: certification-bindings.json is malformed")
        existing_doc = (
            read_result.document
            if read_result.status == _ReadStatus.OK
            else CertificationBindingsDocument(
                schema_version=CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION, bindings=()
            )
        )
        remaining = tuple(
            existing
            for existing in existing_doc.bindings
            if (existing.repository_instance_id, existing.canonical_deployment_root) != key
        )
        new_doc = CertificationBindingsDocument(
            schema_version=existing_doc.schema_version, bindings=remaining + (validated_binding,)
        )
        _atomic_write_protected_json(
            protected_root,
            protected_root / _CERTIFICATION_BINDINGS_FILE_NAME,
            certification_bindings_document_to_document(new_doc),
        )
        return validated_binding


def _write_revocation(protected_root: Path, *, certification_id: str, revoked_at: str) -> CertificationRecord:
    """HMIC-REQ-091-093/100: revokes the existing `CertificationRecord`
    named by `certification_id` -- a field mutation (`status: "revoked"`,
    `revoked_at: <timestamp>`) on the existing record under the
    certification-transition lock, never a deletion and never a separate
    revocation-record file (HMIC-REQ-091's "mechanism -- field mutation,
    not deletion"). Every other field of the record, and every other
    record in the document, is left byte-for-byte unchanged.

    Monotonic (HMIC-REQ item-41/-94): no code path in this module ever
    writes `status: "active"` onto a record that is already `"revoked"`.
    Re-revoking with the identical `revoked_at` is idempotent (no write);
    re-revoking with a *different* `revoked_at` is rejected as
    `CertificationConflictError` -- the first-recorded revocation always
    wins (HMIC-REQ-100's fail-safe ordering)."""

    validated_revoked_at = _validate_timestamp(revoked_at, context="_write_revocation.revoked_at")

    with _certification_transition_lock(protected_root):
        read_result = _read_certifications(protected_root)
        if read_result.status == _ReadStatus.ABSENT:
            raise CertificationRecordNotFoundError(
                f"no certifications.json exists under the protected root; cannot revoke certification_id="
                f"{certification_id!r}"
            )
        if read_result.status == _ReadStatus.MALFORMED:
            raise CertificationMalformedError("cannot revoke: certifications.json exists but is malformed")
        document = read_result.document

        target: Optional[CertificationRecord] = None
        for existing in document.certifications:
            if existing.certification_id == certification_id:
                target = existing
                break
        if target is None:
            raise CertificationRecordNotFoundError(f"no certification record found for certification_id={certification_id!r}")

        if target.status == "revoked":
            if target.revoked_at == validated_revoked_at:
                return target  # HMIC-REQ item-40: identical-content replay is idempotent.
            raise CertificationConflictError(
                f"certification_id {certification_id!r} is already revoked at {target.revoked_at!r}; "
                f"refusing to re-revoke at a different timestamp {validated_revoked_at!r}"
            )

        revoked_record = parse_certification_record(
            certification_record_to_document(replace(target, status="revoked", revoked_at=validated_revoked_at))
        )
        new_records = tuple(
            revoked_record if existing.certification_id == certification_id else existing
            for existing in document.certifications
        )
        new_doc = CertificationsDocument(schema_version=document.schema_version, certifications=new_records)
        _atomic_write_protected_json(
            protected_root,
            protected_root / _CERTIFICATIONS_FILE_NAME,
            certifications_document_to_document(new_doc),
        )
        return revoked_record


# ═══════════════════════════════════════════════════════════════════════════
# Wave D: Active-Certification Validation Engine (Phase 149O.19.5D)
#
# Implements exactly HMIC-REQ-103's 12-step validation algorithm and
# HMIC-REQ-106's closed, 9-value `CertificationStatus` vocabulary (Wave A,
# reused unmodified above). Read-only: no function below writes
# `certifications.json`/`certification-bindings.json`, acquires
# `.certification-transition.lock` (HMIC-REQ-101), or calls any Wave C
# writer. No caller-suppliable authority input exists on any path,
# production or test (HMIC-REQ-045/110): `repository_instance_id` and
# `canonical_deployment_root` are always derived fresh, internally, by
# this module's own Wave B functions -- never accepted as a parameter
# here, including by the internal test seam (a deliberate, documented
# divergence from the 149O.19.4 plan's own illustrative §9.3 shorthand
# signature for `_validate_at_root`; see the module docstring). No
# result of this algorithm is ever cached (HMIC-REQ-113): every call
# re-runs all 12 steps from scratch.
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class HMICValidationResult:
    """The immutable typed outcome of one HMIC-REQ-103 validation attempt.
    `status` is the sole authority-bearing field -- readiness is a pure
    function of it alone, via Wave A's `certification_status_satisfies_
    readiness(result.status)`. `reason` is non-blocking diagnostic text
    only (HMIC-REQ-108): nothing in this module, or any future consumer,
    may branch on `reason` to change the authority outcome independently
    of `status`. No `approved`/`permitted`/`executed`/`capable`/`ready`/
    `readiness`/`activation`-named field exists here, or ever will (§5's
    semantic walls: `VALID` != readiness, != activation, != PB ALLOW, !=
    HATP rollback approval, != runtime capability, != execution, != HATP
    production READY)."""

    status: CertificationStatus
    reason: str


def _validate_at_root(*, protected_root: Path, repository_root: Path) -> HMICValidationResult:
    """Internal, non-production-reachable validation seam (HMIC-REQ-112):
    accepts an explicit `protected_root`, used only by tests constructing
    isolated fixture protected roots -- mirroring `HATPTrustStore.
    __init__`'s own `_test_only_root` pattern exactly. `repository_root`
    locates the working tree whose *current* implementation/contract
    identity is freshly recomputed at steps 2-3 and 9-10 below; it is
    never itself an authority-bearing value and is never compared
    directly against anything -- `repository_instance_id` and
    `canonical_deployment_root` are always derived fresh from it inside
    this function (HMIC-REQ-045/110: never caller-supplied on any path).
    The production wrapper below always calls this with
    `protected_root=HATPTrustStore.production().root`; no other caller in
    this module does.

    Implements HMIC-REQ-103's 12 steps in exact order (HMIC-REQ-104): the
    first failing step's `CertificationStatus` is returned immediately: no
    later step is ever evaluated once an earlier one fails, and no status
    not defined by the failing step is ever returned."""

    harness_root = HarnessPath(repository_root)

    # Steps 2-3: resolve current repository/deployment identity fresh,
    # read-only (HMIC-REQ-043-045). A derivation failure here (e.g. no
    # repository_instance_id has ever been established for this
    # repository, or the deployment root cannot be resolved) is a genuine
    # environment/derivation failure distinct in kind from "no
    # certification exists yet" (steps 4-5's own MISSING outcome): this
    # module maps it to ACCESS_ERROR, extending HMIC-REQ-105's "root/file
    # access failure -> MISSING (absence) or ACCESS_ERROR (genuine I/O
    # error)" pairing by documented analogy, since this failure occurs
    # before any certification file is even consulted (`docs/
    # PHASE_149O_19_5D_...md` records this as an explicit interpretation,
    # not an improvised default).
    try:
        repository_instance_id = derive_repository_instance_id(harness_root)
        canonical_deployment_root = derive_canonical_deployment_root(harness_root)
    except (HMICIdentityDerivationError, RepositoryIdentityError) as exc:
        return HMICValidationResult(
            CertificationStatus.ACCESS_ERROR,
            f"could not derive current repository/deployment identity: {exc}",
        )

    # Step 4 (active-certification binding) / step 6 (strict-parse,
    # folded into `_load_active_binding`'s reuse of Wave C's strict
    # parser -- HMIC-REQ-031/036).
    try:
        binding = _load_active_binding(
            protected_root,
            repository_instance_id=repository_instance_id,
            canonical_deployment_root=canonical_deployment_root,
        )
    except CertificationMalformedError as exc:
        return HMICValidationResult(
            CertificationStatus.MALFORMED, f"active-certification binding is malformed: {exc}"
        )

    if binding is None or binding.active_certification_id is None:
        # HMIC-REQ-085: no active-binding entry for this exact key is
        # MISSING -- never "scan certifications.json and pick something."
        return HMICValidationResult(
            CertificationStatus.MISSING,
            "no active-certification binding exists for this repository/deployment",
        )

    certification_id = binding.active_certification_id

    # Step 5 (certification record) / step 6 (strict-parse).
    try:
        record = _load_certification_record(protected_root, certification_id)
    except CertificationRecordNotFoundError:
        # The binding names a certification_id with no corresponding
        # record -- MISSING, never a search for another (HMIC-REQ-090).
        return HMICValidationResult(
            CertificationStatus.MISSING,
            f"active binding names certification_id={certification_id!r} but no such record is stored",
        )
    except CertificationMalformedError as exc:
        return HMICValidationResult(CertificationStatus.MALFORMED, f"certifications.json is malformed: {exc}")

    # Step 7: repository/deployment binding match (§31 step 7 names both
    # checks under one step; this module evaluates repository before
    # deployment as a stable, deterministic sub-order for the
    # wrong-repository-and-wrong-deployment double-defect case, since the
    # contract does not further split step 7 into two numbered steps).
    if record.repository_instance_id != repository_instance_id:
        return HMICValidationResult(
            CertificationStatus.WRONG_REPOSITORY,
            "certification's repository_instance_id does not match the current repository",
        )
    if record.canonical_deployment_root != canonical_deployment_root:
        return HMICValidationResult(
            CertificationStatus.WRONG_DEPLOYMENT,
            "certification's canonical_deployment_root does not match the current deployment",
        )

    # Step 8: status == "active" (HMIC-REQ-094: a revoked active-pointed
    # certification is REVOKED -- never falls back to another record).
    if record.status != "active":
        return HMICValidationResult(
            CertificationStatus.REVOKED,
            f"active-pointed certification_id={certification_id!r} is revoked (revoked_at={record.revoked_at!r})",
        )

    # Step 9: fresh implementation identity, both terms (HMIC-REQ-048/049:
    # a mismatch in either term is a mismatch of the whole; a missing/
    # symlinked/non-regular frozen file at recompute time also fails
    # closed here, HMIC-REQ-059/061/062).
    try:
        current_commit = derive_implementation_commit(harness_root)
        current_scope_digest = derive_implementation_scope_digest(harness_root)
    except HMICIdentityDerivationError as exc:
        return HMICValidationResult(
            CertificationStatus.IMPLEMENTATION_MISMATCH,
            f"current implementation identity could not be derived: {exc}",
        )
    if current_commit != record.implementation_commit or current_scope_digest != record.implementation_scope_digest:
        return HMICValidationResult(
            CertificationStatus.IMPLEMENTATION_MISMATCH,
            "current implementation_commit/implementation_scope_digest does not match the certified value",
        )

    # Step 10: fresh contract-version comparison (HMIC-REQ-069: any
    # difference -- including a contract revised to a new version since
    # certification -- is a mismatch; no compatibility table exists).
    try:
        current_contract_versions = derive_contract_versions(harness_root)
    except HMICIdentityDerivationError as exc:
        return HMICValidationResult(
            CertificationStatus.CONTRACT_MISMATCH,
            f"current contract versions could not be derived: {exc}",
        )
    if dict(current_contract_versions) != dict(record.contract_versions):
        return HMICValidationResult(
            CertificationStatus.CONTRACT_MISMATCH,
            "current bound-contract versions do not match the certified contract_versions",
        )

    # Step 11: certification_id self-consistency (HMIC-REQ-040): re-derive
    # from the record's own stored fields; a mismatch means the on-disk
    # record was tampered with in place.
    if _recompute_certification_id(record) != record.certification_id:
        return HMICValidationResult(
            CertificationStatus.MALFORMED,
            "certification_id does not re-derive from the record's own stored fields (tamper-detection failure)",
        )

    # Step 12: every prior step passed.
    return HMICValidationResult(
        CertificationStatus.VALID,
        "certification is valid: repository, deployment, implementation, contract, and revocation checks all passed",
    )


def validate_active_hatp_mandatory_independent_verification_certification(
    repository_root: Path,
) -> HMICValidationResult:
    """The sole production validation entrypoint (HMIC-REQ-109). Resolves
    the Protected Root internally via `HATPTrustStore.production().root`
    -- no caller-suppliable root override exists (HMIC-REQ-111,
    HMIC-REQ-023). Accepts no caller-provided `implementation_digest=`,
    `implementation_commit=`, `contract_versions=`, `repository_
    instance_id=`, `canonical_deployment_root=`, `revoked=`, or `status=`
    -- every authority-sensitive value is derived fresh, internally
    (HMIC-REQ-045/110). Re-runs the full HMIC-REQ-103 algorithm on every
    call; no cache of any kind exists anywhere in this module
    (HMIC-REQ-113). Read-only: never acquires `.certification-transition.
    lock` (HMIC-REQ-101 -- only certification *writes* acquire that lock)
    and never calls `_append_certification_record`/`_write_active_
    binding`/`_write_revocation`. `repository_root` is a neutral
    repository locator only (HMIC-REQ-109) -- `repository_instance_id` is
    still independently re-derived from it and cross-checked at step 7,
    never accepted as this parameter's value directly.

    A `VALID` result satisfies only this one HMRC-001 readiness term
    (HMIC-REQ-107, HMIC-REQ-120); it never activates `HATP_MANDATORY`,
    evaluates a Permission Broker request, derives HATP/RAE rollback
    approval, or grants any runtime execution capability (HMIC-REQ-
    122-124, §5's semantic walls).

    Zero production callers exist as of this phase (149O.19.5D): this
    function is never imported by `hatp_mandatory_cutover.py` or any
    other existing production file. Wiring it into the hard-coded
    `mandatory_consumption_implementation_independently_verified = False`
    readiness ceiling is Wave F, gated by Stop Condition W-1 -- a future
    HMIC-001 v1.1 contract amendment binding this module's own bytes into
    the certified 22-file scope, independently verified, before Wave F
    may begin (`docs/PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md` §10.3)."""

    try:
        protected_root = HATPTrustStore.production().root
    except HATPTrustStoreError as exc:
        return HMICValidationResult(CertificationStatus.ACCESS_ERROR, f"could not resolve the Protected Root: {exc}")

    return _validate_at_root(protected_root=protected_root, repository_root=repository_root)
