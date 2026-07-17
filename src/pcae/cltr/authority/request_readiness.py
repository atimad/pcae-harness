"""Phase 136AD: Stage 3 Typed Authority Model Request and Readiness
Implementation (Typed Model Implementation Group 3, per the 136Y plan
Sec.4/Sec.23, package layout Sec.7).

Implements exactly two record-family models: ``CutoverRequest`` and
``ReadinessPackage``, schema-backed by ``records/cutover_request.schema.json``
and ``records/readiness_package.schema.json`` respectively.

A constructed instance of either model asserts only "this JSON was
well-formed against schema X at version Y and can be represented without
loss" -- never operational truth. Neither model authorizes a cutover,
determines or calculates readiness, evaluates evidence, resolves a
reference, verifies a digest, selects authority, persists a record,
triggers publication, mutates lifecycle state, executes recovery, or
produces any other operational decision. A ``CutoverRequest`` is a
representation of a request, never an authorization; a ``ReadinessPackage``
is a representation of reported evidence, never a readiness verdict.
Legacy lifecycle remains the sole production authority; CLTR remains
derivative.

No other record-family model (``HumanAuthorization``, ``CutoverCandidate``,
``Certification``, ``PublicationAttempt``, ``PublicationEvidence``,
``ConcurrencyConflict``, ``RecoveryJournalEntry``,
``NotificationAuthorityBinding``, ``MarkerAuthorityBinding``,
``FinalizationReceiptAuthorityBinding``, ``CompatibilityState``,
``QuarantineRecord``) is implemented here; those belong to future,
separately governed implementation groups.

Absent-versus-null: per contract Sec.6.3/Sec.30 (135Z), the **one**
contractually named absent-vs-null relaxation applies to ``CutoverRequest``'s
own optional fields (its only such field being ``reason_code``) -- that
field uses ordinary ``Optional[T] = None`` rather than the ``ABSENT``
sentinel, since the contract itself permits the wire-level collapse of
"absent" and "explicit null" for this one family's optional fields only.
``ReadinessPackage``'s optional fields (``gate_result``, ``_extensions``)
follow the generic ``ABSENT``-sentinel rule used elsewhere in this package,
since no such relaxation is named for this family.
"""

from __future__ import annotations

import dataclasses
import enum
import re
from collections.abc import Mapping
from typing import Any, Optional, Tuple

from pcae.cltr.authority.digest import RecordDigest, ReferencedRecordDigest
from pcae.cltr.authority.enums import AuthorityKind, AuthorityRole, ReasonCode, RecordFamily
from pcae.cltr.authority.envelope import RecordEnvelope, SchemaVersionString, Timestamp
from pcae.cltr.authority.errors import (
    TypedModelConstructionError,
    TypedModelInternalInvariantError,
    UnsupportedSchemaVersionError,
)
from pcae.cltr.authority.extensions import ExtensionMapping
from pcae.cltr.authority.identity import MigrationEpochToken, PhaseIdentity, RecordId, TransitionId
from pcae.cltr.authority.limitations import AuthorityDisclosure, Limitations
from pcae.cltr.authority.references import RecordReference, require_family
from pcae.cltr.authority.sentinels import ABSENT, AbsentType
from pcae.cltr.authority.serialization import field_from_payload, serialize_value, to_dict_fields

# ---------------------------------------------------------------------------
# Record-local enums (family-scoped, not part of the 7 shared cross-family
# enums in enums.py -- matching the schema layer's own non-centralization
# choice, 136Y plan Sec.5/Sec.12; same precedent as authority_core.py's
# ActivationState/VerificationState).
# ---------------------------------------------------------------------------


class RequestState(str, enum.Enum):
    """``CutoverRequest``'s record-local ``state`` field (Sec.8.8, 10
    values; wire field name is ``state``, not ``request_state`` --
    Sec.19's own field table does not literally spell this field's name,
    disclosed as NON-BLOCKING-136L-1, see docs). Reaching "authorized",
    "certified", "publication_pending", or "published" here is a local
    status label only -- it never itself proves human authorization,
    certification, or publication occurred (Layer 4/6)."""

    PENDING = "pending"
    EVIDENCE_GATHERING = "evidence_gathering"
    READY = "ready"
    AUTHORIZED = "authorized"
    CERTIFIED = "certified"
    PUBLICATION_PENDING = "publication_pending"
    PUBLISHED = "published"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class ReadinessState(str, enum.Enum):
    """``ReadinessPackage``'s record-local ``state`` field (Sec.8.8, 5
    values). "conflict" requires ``findings`` to contain at least one
    BLOCKING-verdict entry (Sec.20, enforced by
    ``ReadinessPackage.__post_init__``). A "ready" value here never itself
    proves cutover eligibility, evidence freshness, or cross-record
    consistency (Layer 4)."""

    UNKNOWN = "unknown"
    STALE = "stale"
    PARTIAL = "partial"
    READY = "ready"
    CONFLICT = "conflict"


class PrerequisiteStatus(str, enum.Enum):
    """``ReadinessPackage``'s record-local, package-wide
    ``prerequisite_status`` summary (Sec.20, 3 values). A "met" value here
    never itself proves the underlying prerequisites were actually
    verified (Layer 4)."""

    UNKNOWN = "unknown"
    UNMET = "unmet"
    MET = "met"


class GateResult(str, enum.Enum):
    """``ReadinessPackage``'s optional ``gate_result`` field, restating
    CLTR-CUTOVER-001 Sec.10's frozen four-value gate outcome (Sec.8.8).
    A schema-valid value here never itself resolves cutover eligibility
    (Layer 4/6)."""

    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    UNCERTAIN = "uncertain"
    CONFLICT = "conflict"


class FindingVerdict(str, enum.Enum):
    """The closed finding-classification vocabulary used by
    ``ReadinessPackage``'s lightweight embedded ``Finding`` objects
    (Sec.20), matching this repository's existing phase-report finding
    taxonomy. A finding's verdict never itself makes an authority or
    lifecycle decision -- it is a disclosure only."""

    CONFIRMED = "CONFIRMED"
    NON_BLOCKING = "NON-BLOCKING"
    BLOCKING = "BLOCKING"
    PREREQUISITE = "PREREQUISITE"
    DEFERRED = "DEFERRED"


# ---------------------------------------------------------------------------
# Nested value objects
# ---------------------------------------------------------------------------

_FINAL_REVISION_MIN_LENGTH = 1
_FINAL_REVISION_MAX_LENGTH = 256
_DISCLOSURE_TEXT_MAX_LENGTH = 500
_FINDING_ID_MIN_LENGTH = 1
_FINDING_ID_MAX_LENGTH = 64

_EVIDENCE_REQUIREMENTS_MAX_ITEMS = 24
_EVIDENCE_REFERENCES_MAX_ITEMS = 64
_FINDINGS_MAX_ITEMS = 128


def _validate_ascii_single_line(value: Any, *, min_length: int, max_length: int, type_name: str) -> str:
    if not isinstance(value, str) or not (min_length <= len(value) <= max_length):
        raise TypedModelConstructionError(
            f"{type_name} must be a string of length {min_length}-{max_length}"
        )
    if any(ord(ch) < 0x20 or ord(ch) > 0x7E for ch in value):
        raise TypedModelConstructionError(
            f"{type_name} must be single-line printable ASCII only"
        )
    return value


_FINDING_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _validate_finding_id(value: Any) -> str:
    if not isinstance(value, str) or not _FINDING_ID_PATTERN.fullmatch(value):
        raise TypedModelConstructionError(
            "Finding.id must match the required opaque ASCII-only shape"
        )
    return value


@dataclasses.dataclass(frozen=True)
class Finding:
    """A lightweight local finding object
    (``records/readiness_package.schema.json#/$defs/finding``) -- explicitly
    not the full findings-table format used in phase documentation. A
    finding's verdict is a disclosure only; it never itself verifies
    evidence, ranks trust, or makes an authority decision."""

    id: str
    verdict: FindingVerdict
    title: str

    def __post_init__(self) -> None:
        _validate_finding_id(self.id)
        _validate_ascii_single_line(
            self.title,
            min_length=1,
            max_length=_DISCLOSURE_TEXT_MAX_LENGTH,
            type_name="Finding.title",
        )


_FINDING_KNOWN_KEYS = frozenset({"id", "verdict", "title"})


def _finding_from_dict(value: Mapping[str, Any], *, owner: str) -> Finding:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _FINDING_KNOWN_KEYS, owner)
    for required_key in ("id", "verdict", "title"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    return Finding(
        id=_validate_finding_id(payload["id"]),
        verdict=FindingVerdict(_require_str(payload["verdict"], f"{owner}.verdict")),
        title=_validate_ascii_single_line(
            payload["title"], min_length=1, max_length=_DISCLOSURE_TEXT_MAX_LENGTH, type_name=f"{owner}.title"
        ),
    )


def _finding_to_dict(finding: Finding) -> dict:
    return {
        "id": finding.id,
        "verdict": serialize_value(finding.verdict),
        "title": finding.title,
    }


# ---------------------------------------------------------------------------
# Shared field-extraction helpers (Layer 3 construction pipeline, 136Y plan
# Sec.16). Deliberately self-contained within this module rather than
# importing authority_core.py's private helpers -- each group module owns
# its own Layer 3 construction boilerplate, matching that module's own
# precedent-setting structure without coupling two group modules through
# underscore-prefixed private symbols.
# ---------------------------------------------------------------------------


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypedModelConstructionError(f"{field_name} must be a string, got {type(value)!r}")
    return value


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise TypedModelConstructionError(f"{field_name} must be a JSON object, got {type(value)!r}")
    return value


def _reject_unknown_keys(payload: Mapping[str, Any], known: frozenset, owner: str) -> None:
    unknown = set(payload.keys()) - known
    if unknown:
        raise TypedModelConstructionError(
            f"{owner}: unknown field(s) not permitted by the schema: {sorted(unknown)!r}"
        )


_RECORD_REFERENCE_KNOWN_KEYS = frozenset(
    {"record_id", "record_digest", "record_family", "schema_id", "schema_version"}
)


def _record_reference_from_dict(
    value: Mapping[str, Any], *, required_family: RecordFamily | None, owner: str
) -> RecordReference:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _RECORD_REFERENCE_KNOWN_KEYS, owner)
    for required_key in ("record_id", "record_digest", "record_family"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    reference = RecordReference(
        record_id=RecordId(_require_str(payload["record_id"], f"{owner}.record_id")),
        record_digest=ReferencedRecordDigest(
            _require_str(payload["record_digest"], f"{owner}.record_digest")
        ),
        record_family=RecordFamily(_require_str(payload["record_family"], f"{owner}.record_family")),
        schema_id=field_from_payload(payload, "schema_id"),
        schema_version=field_from_payload(payload, "schema_version"),
    )
    if required_family is not None:
        require_family(reference, required_family)
    return reference


_AUTHORITY_DISCLOSURE_KNOWN_KEYS = frozenset({"authority_role", "is_authoritative", "disclosure_text"})


def _authority_disclosure_from_dict(value: Mapping[str, Any], *, owner: str) -> AuthorityDisclosure:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _AUTHORITY_DISCLOSURE_KNOWN_KEYS, owner)
    for required_key in ("authority_role", "is_authoritative", "disclosure_text"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    if payload["is_authoritative"] is not False:
        raise TypedModelConstructionError(
            f"{owner}.is_authoritative must be the frozen const false"
        )
    return AuthorityDisclosure(
        authority_role=AuthorityRole(
            _require_str(payload["authority_role"], f"{owner}.authority_role")
        ),
        disclosure_text=_require_str(payload["disclosure_text"], f"{owner}.disclosure_text"),
        is_authoritative=False,
    )


def _limitations_from_list(value: Any, *, owner: str) -> Limitations:
    if not isinstance(value, list):
        raise TypedModelConstructionError(f"{owner} must be a JSON array of strings")
    for entry in value:
        if not isinstance(entry, str):
            raise TypedModelConstructionError(f"{owner}: every entry must be a string")
    return Limitations(entries=tuple(value))


def _envelope_from_payload(payload: Mapping[str, Any], *, record_type: str, schema_id: str) -> RecordEnvelope:
    for required_key in (
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
    ):
        if required_key not in payload:
            raise TypedModelConstructionError(f"missing required envelope field {required_key!r}")

    actual_schema_id = _require_str(payload["schema_id"], "schema_id")
    if actual_schema_id != schema_id:
        raise TypedModelConstructionError(
            f"schema_id must be the frozen const {schema_id!r}, got {actual_schema_id!r}"
        )
    actual_record_type = _require_str(payload["record_type"], "record_type")
    if actual_record_type != record_type:
        raise TypedModelConstructionError(
            f"record_type must be the frozen const {record_type!r}, got {actual_record_type!r}"
        )
    contract_version = _require_str(payload["contract_version"], "contract_version")

    return RecordEnvelope(
        schema_id=actual_schema_id,
        schema_version=SchemaVersionString(_require_str(payload["schema_version"], "schema_version")),
        record_type=actual_record_type,
        record_id=RecordId(_require_str(payload["record_id"], "record_id")),
        record_digest=RecordDigest(_require_str(payload["record_digest"], "record_digest")),
        created_at=Timestamp(_require_str(payload["created_at"], "created_at")),
        contract_version=contract_version,
    )


def _envelope_to_dict(envelope: RecordEnvelope) -> dict:
    return to_dict_fields(envelope)


# ---------------------------------------------------------------------------
# CutoverRequest
# ---------------------------------------------------------------------------

_CUTOVER_REQUEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/cutover_request.schema.json"
_CUTOVER_REQUEST_RECORD_TYPE = "cutover_request"
_CUTOVER_REQUEST_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_CUTOVER_REQUEST_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "phase_id",
        "migration_epoch",
        "target",
        "source_authority",
        "source_epoch",
        "target_epoch",
        "evidence_requirements",
        "readiness_package_reference",
        "authorization_requirement",
        "final_revision",
        "state",
        "reason_code",
        "limitations",
        "authority_disclosure",
    }
)


def _validate_final_revision(value: Any) -> str:
    return _validate_ascii_single_line(
        value,
        min_length=_FINAL_REVISION_MIN_LENGTH,
        max_length=_FINAL_REVISION_MAX_LENGTH,
        type_name="CutoverRequest.final_revision",
    )


@dataclasses.dataclass(frozen=True)
class CutoverRequest:
    """Shape-only wire contract for a ``CutoverRequest`` companion record
    (``records/cutover_request.schema.json``, contract Sec.19, field table
    repaired by Phase 136D Sec.19.1). A ``CutoverRequest`` document proposes
    a legacy-to-cltr authority transition; it never itself establishes
    readiness truth, human authorization, certification, CAS success,
    publication success, or current authority (Sec.1, Sec.40). Tier 1
    (strict): no ``_extensions`` escape hatch exists on this family.

    This model does not: approve the request, determine requester
    authority, check whether cutover is allowed, verify evidence, resolve
    referenced epochs, compare current state, persist the request, dispatch
    notification, or initiate cutover. A ``CutoverRequest`` is a
    representation of a request, never an authorization.
    """

    envelope: RecordEnvelope
    phase_id: PhaseIdentity
    migration_epoch: MigrationEpochToken
    target: AuthorityKind
    source_authority: AuthorityKind
    source_epoch: RecordReference
    target_epoch: RecordReference
    evidence_requirements: Tuple[ReasonCode, ...]
    readiness_package_reference: RecordReference
    authorization_requirement: bool
    final_revision: str
    state: RequestState
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    # Sec.6.3 absent-vs-null relaxation: the contract's one explicitly named
    # exception applies to this field -- ordinary Optional[T] = None, not
    # the ABSENT sentinel used everywhere else in this package.
    reason_code: Optional[ReasonCode] = None

    def __post_init__(self) -> None:
        if self.envelope.record_type != _CUTOVER_REQUEST_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"CutoverRequest.envelope.record_type must be "
                f"{_CUTOVER_REQUEST_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _CUTOVER_REQUEST_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"CutoverRequest.envelope.schema_id must be the frozen const "
                f"{_CUTOVER_REQUEST_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family (schema description, contract Sec.9).
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "CutoverRequest.authority_disclosure.authority_role must not be "
                "'authoritative': a request is never itself a resolved "
                "live-authority claim"
            )
        if self.target is not AuthorityKind.CLTR:
            raise TypedModelInternalInvariantError(
                "CutoverRequest.target must be the frozen const 'cltr' -- a "
                "request targeting 'legacy' is not a cutover"
            )
        if self.source_authority is not AuthorityKind.LEGACY:
            raise TypedModelInternalInvariantError(
                "CutoverRequest.source_authority must be the frozen const "
                "'legacy' at v1.0"
            )
        if self.authorization_requirement is not True:
            raise TypedModelInternalInvariantError(
                "CutoverRequest.authorization_requirement must be the frozen "
                "const true -- human authorization is always required for a "
                "cutover"
            )
        require_family(self.source_epoch, RecordFamily.AUTHORITY_EPOCH)
        require_family(self.target_epoch, RecordFamily.AUTHORITY_EPOCH)
        require_family(self.readiness_package_reference, RecordFamily.READINESS_PACKAGE)
        if (
            self.readiness_package_reference.schema_id is ABSENT
            or self.readiness_package_reference.schema_version is ABSENT
        ):
            raise TypedModelInternalInvariantError(
                "CutoverRequest.readiness_package_reference.schema_id/"
                "schema_version are unconditionally required (Sec.12 "
                "cross-family reference rule, Phase 136D Sec.19.1 repair)"
            )
        evidence_requirements = tuple(self.evidence_requirements)
        if len(evidence_requirements) > _EVIDENCE_REQUIREMENTS_MAX_ITEMS:
            raise TypedModelInternalInvariantError(
                f"CutoverRequest.evidence_requirements has "
                f"{len(evidence_requirements)} entries, exceeding the maximum "
                f"of {_EVIDENCE_REQUIREMENTS_MAX_ITEMS}"
            )
        if len(set(evidence_requirements)) != len(evidence_requirements):
            raise TypedModelInternalInvariantError(
                "CutoverRequest.evidence_requirements must not contain "
                "duplicate entries (uniqueItems)"
            )
        object.__setattr__(self, "evidence_requirements", evidence_requirements)
        _validate_final_revision(self.final_revision)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "CutoverRequest":
        if schema_version not in _CUTOVER_REQUEST_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"CutoverRequest does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "CutoverRequest")
        _reject_unknown_keys(payload, _CUTOVER_REQUEST_KNOWN_KEYS, "CutoverRequest")

        envelope = _envelope_from_payload(
            payload, record_type=_CUTOVER_REQUEST_RECORD_TYPE, schema_id=_CUTOVER_REQUEST_SCHEMA_ID
        )

        for required_key in (
            "phase_id",
            "migration_epoch",
            "target",
            "source_authority",
            "source_epoch",
            "target_epoch",
            "evidence_requirements",
            "readiness_package_reference",
            "authorization_requirement",
            "final_revision",
            "state",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"CutoverRequest: missing required field {required_key!r}"
                )

        raw_evidence_requirements = payload["evidence_requirements"]
        if not isinstance(raw_evidence_requirements, list):
            raise TypedModelConstructionError(
                "CutoverRequest.evidence_requirements must be a JSON array"
            )
        evidence_requirements = tuple(
            ReasonCode(_require_str(entry, "CutoverRequest.evidence_requirements[]"))
            for entry in raw_evidence_requirements
        )

        # Sec.6.3 relaxation: ``.get()`` deliberately collapses "key absent"
        # and "key present with explicit null" to the same Python ``None``
        # for this one contractually named field only.
        raw_reason_code = payload.get("reason_code")
        reason_code = (
            None
            if raw_reason_code is None
            else ReasonCode(_require_str(raw_reason_code, "CutoverRequest.reason_code"))
        )

        return cls(
            envelope=envelope,
            phase_id=PhaseIdentity(_require_str(payload["phase_id"], "CutoverRequest.phase_id")),
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "CutoverRequest.migration_epoch")
            ),
            target=AuthorityKind(_require_str(payload["target"], "CutoverRequest.target")),
            source_authority=AuthorityKind(
                _require_str(payload["source_authority"], "CutoverRequest.source_authority")
            ),
            source_epoch=_record_reference_from_dict(
                payload["source_epoch"],
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="CutoverRequest.source_epoch",
            ),
            target_epoch=_record_reference_from_dict(
                payload["target_epoch"],
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="CutoverRequest.target_epoch",
            ),
            evidence_requirements=evidence_requirements,
            readiness_package_reference=_record_reference_from_dict(
                payload["readiness_package_reference"],
                required_family=RecordFamily.READINESS_PACKAGE,
                owner="CutoverRequest.readiness_package_reference",
            ),
            authorization_requirement=payload["authorization_requirement"],
            final_revision=_validate_final_revision(payload["final_revision"]),
            state=RequestState(_require_str(payload["state"], "CutoverRequest.state")),
            reason_code=reason_code,
            limitations=_limitations_from_list(payload["limitations"], owner="CutoverRequest.limitations"),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="CutoverRequest.authority_disclosure"
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["phase_id"] = serialize_value(self.phase_id)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["target"] = serialize_value(self.target)
        result["source_authority"] = serialize_value(self.source_authority)
        result["source_epoch"] = serialize_value(self.source_epoch)
        result["target_epoch"] = serialize_value(self.target_epoch)
        result["evidence_requirements"] = [serialize_value(v) for v in self.evidence_requirements]
        result["readiness_package_reference"] = serialize_value(self.readiness_package_reference)
        result["authorization_requirement"] = self.authorization_requirement
        result["final_revision"] = self.final_revision
        result["state"] = serialize_value(self.state)
        if self.reason_code is not None:
            result["reason_code"] = serialize_value(self.reason_code)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        return result


# ---------------------------------------------------------------------------
# ReadinessPackage
# ---------------------------------------------------------------------------

_READINESS_PACKAGE_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/readiness_package.schema.json"
_READINESS_PACKAGE_RECORD_TYPE = "readiness_package"
_READINESS_PACKAGE_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_READINESS_PACKAGE_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "phase_id",
        "transition_id",
        "migration_epoch",
        "evidence_references",
        "prerequisite_status",
        "findings",
        "state",
        "gate_result",
        "limitations",
        "authority_disclosure",
        "_extensions",
    }
)

_READINESS_PACKAGE_RESERVED_FIELD_NAMES = frozenset(_READINESS_PACKAGE_KNOWN_KEYS - {"_extensions"})


@dataclasses.dataclass(frozen=True)
class ReadinessPackage:
    """Shape-only wire contract for a ``ReadinessPackage`` companion record
    (``records/readiness_package.schema.json``, contract Sec.20). A
    ``ReadinessPackage`` document reports evidence toward a proposed
    cutover; it never itself establishes readiness truth, cutover
    eligibility, human authorization, certification, CAS success,
    publication success, or current authority (Sec.1, Sec.40). Tier 2
    (``_extensions`` only, Sec.14).

    This model does not: calculate readiness, infer completeness, decide
    whether criteria pass, verify evidence, check referenced records,
    authorize cutover, create a candidate, issue certification, or persist
    anything. A field that says "ready" remains descriptive data only.
    """

    envelope: RecordEnvelope
    phase_id: PhaseIdentity
    transition_id: TransitionId
    migration_epoch: MigrationEpochToken
    evidence_references: Tuple[RecordReference, ...]
    prerequisite_status: PrerequisiteStatus
    findings: Tuple[Finding, ...]
    state: ReadinessState
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    gate_result: GateResult | AbsentType = ABSENT
    _extensions: ExtensionMapping | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _READINESS_PACKAGE_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"ReadinessPackage.envelope.record_type must be "
                f"{_READINESS_PACKAGE_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _READINESS_PACKAGE_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"ReadinessPackage.envelope.schema_id must be the frozen "
                f"const {_READINESS_PACKAGE_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "ReadinessPackage.authority_disclosure.authority_role must "
                "not be 'authoritative': a readiness package is never itself "
                "a resolved live-authority claim"
            )
        evidence_references = tuple(self.evidence_references)
        if len(evidence_references) > _EVIDENCE_REFERENCES_MAX_ITEMS:
            raise TypedModelInternalInvariantError(
                f"ReadinessPackage.evidence_references has "
                f"{len(evidence_references)} entries, exceeding the maximum "
                f"of {_EVIDENCE_REFERENCES_MAX_ITEMS}"
            )
        object.__setattr__(self, "evidence_references", evidence_references)
        findings = tuple(self.findings)
        if len(findings) > _FINDINGS_MAX_ITEMS:
            raise TypedModelInternalInvariantError(
                f"ReadinessPackage.findings has {len(findings)} entries, "
                f"exceeding the maximum of {_FINDINGS_MAX_ITEMS}"
            )
        object.__setattr__(self, "findings", findings)
        # state == "conflict" <-> findings conditional (schema allOf/if-then,
        # restated here as the single-document Layer 3 invariant it already
        # is -- not a new Layer 4/5 readiness rule).
        if self.state is ReadinessState.CONFLICT:
            if not any(f.verdict is FindingVerdict.BLOCKING for f in findings):
                raise TypedModelInternalInvariantError(
                    "ReadinessPackage.findings must contain at least one "
                    "BLOCKING-verdict entry when state is 'conflict'"
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "ReadinessPackage":
        if schema_version not in _READINESS_PACKAGE_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"ReadinessPackage does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "ReadinessPackage")
        _reject_unknown_keys(payload, _READINESS_PACKAGE_KNOWN_KEYS, "ReadinessPackage")

        envelope = _envelope_from_payload(
            payload, record_type=_READINESS_PACKAGE_RECORD_TYPE, schema_id=_READINESS_PACKAGE_SCHEMA_ID
        )

        for required_key in (
            "phase_id",
            "transition_id",
            "migration_epoch",
            "evidence_references",
            "prerequisite_status",
            "findings",
            "state",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"ReadinessPackage: missing required field {required_key!r}"
                )

        raw_evidence_references = payload["evidence_references"]
        if not isinstance(raw_evidence_references, list):
            raise TypedModelConstructionError(
                "ReadinessPackage.evidence_references must be a JSON array"
            )
        evidence_references = tuple(
            _record_reference_from_dict(
                entry, required_family=None, owner="ReadinessPackage.evidence_references[]"
            )
            for entry in raw_evidence_references
        )

        raw_findings = payload["findings"]
        if not isinstance(raw_findings, list):
            raise TypedModelConstructionError("ReadinessPackage.findings must be a JSON array")
        findings = tuple(
            _finding_from_dict(entry, owner="ReadinessPackage.findings[]") for entry in raw_findings
        )

        raw_gate_result = field_from_payload(payload, "gate_result")
        gate_result: GateResult | AbsentType
        if raw_gate_result is ABSENT:
            gate_result = ABSENT
        elif raw_gate_result is None:
            raise TypedModelConstructionError(
                "ReadinessPackage.gate_result does not permit explicit null "
                "(schema allows absence only, no generic absent-vs-null "
                "relaxation applies to this family)"
            )
        else:
            gate_result = GateResult(_require_str(raw_gate_result, "ReadinessPackage.gate_result"))

        raw_extensions = field_from_payload(payload, "_extensions")
        parsed_extensions: ExtensionMapping | AbsentType
        if raw_extensions is ABSENT:
            parsed_extensions = ABSENT
        elif raw_extensions is None:
            raise TypedModelConstructionError(
                "ReadinessPackage._extensions does not permit explicit null"
            )
        else:
            extensions_payload = _require_mapping(raw_extensions, "ReadinessPackage._extensions")
            for extension_value in extensions_payload.values():
                if not isinstance(extension_value, str):
                    raise TypedModelConstructionError(
                        "ReadinessPackage._extensions values must be strings only "
                        "(Sec.14 Tier 2 string-valued map), got "
                        f"{type(extension_value)!r}"
                    )
            parsed_extensions = ExtensionMapping.from_mapping(
                extensions_payload,
                reserved_keys=_READINESS_PACKAGE_RESERVED_FIELD_NAMES,
            )

        return cls(
            envelope=envelope,
            phase_id=PhaseIdentity(_require_str(payload["phase_id"], "ReadinessPackage.phase_id")),
            transition_id=TransitionId(
                _require_str(payload["transition_id"], "ReadinessPackage.transition_id")
            ),
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "ReadinessPackage.migration_epoch")
            ),
            evidence_references=evidence_references,
            prerequisite_status=PrerequisiteStatus(
                _require_str(payload["prerequisite_status"], "ReadinessPackage.prerequisite_status")
            ),
            findings=findings,
            state=ReadinessState(_require_str(payload["state"], "ReadinessPackage.state")),
            gate_result=gate_result,
            limitations=_limitations_from_list(payload["limitations"], owner="ReadinessPackage.limitations"),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="ReadinessPackage.authority_disclosure"
            ),
            _extensions=parsed_extensions,
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["phase_id"] = serialize_value(self.phase_id)
        result["transition_id"] = serialize_value(self.transition_id)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["evidence_references"] = [serialize_value(v) for v in self.evidence_references]
        result["prerequisite_status"] = serialize_value(self.prerequisite_status)
        result["findings"] = [_finding_to_dict(f) for f in self.findings]
        result["state"] = serialize_value(self.state)
        if self.gate_result is not ABSENT:
            result["gate_result"] = serialize_value(self.gate_result)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        if self._extensions is not ABSENT:
            result["_extensions"] = self._extensions.to_dict()
        return result


__all__ = [
    "RequestState",
    "ReadinessState",
    "PrerequisiteStatus",
    "GateResult",
    "FindingVerdict",
    "Finding",
    "CutoverRequest",
    "ReadinessPackage",
]
