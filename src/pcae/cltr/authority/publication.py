"""Phase 136AH: Stage 3 Typed Authority Model Publication Implementation
(Typed Model Implementation Group 5, per the 136Y plan Sec.4/Sec.23,
package layout Sec.7).

Implements exactly two record-family models: ``PublicationAttempt`` and
``PublicationEvidence``, schema-backed by
``records/publication_attempt.schema.json`` and
``records/publication_evidence.schema.json`` respectively.

A constructed instance of either model asserts only "this JSON was
well-formed against schema X at version Y and can be represented without
loss" -- never operational truth. Neither model publishes an artifact,
writes lifecycle state, promotes a candidate, updates an authority
pointer, executes compare-and-swap, verifies publication success,
verifies evidence, resolves a reference, retries publication, recovers a
failed publication, dispatches a notification, or creates a marker or
receipt. A ``PublicationAttempt`` is a representation of an attempted
publication operation, never proof one was performed or succeeded; a
``PublicationEvidence`` is a representation of a claimed publication
outcome, never proof that outcome is true. Legacy lifecycle remains the
sole production authority; CLTR remains derivative.

No other record-family model (``ConcurrencyConflict``,
``RecoveryJournalEntry``, ``NotificationAuthorityBinding``,
``MarkerAuthorityBinding``, ``FinalizationReceiptAuthorityBinding``,
``CompatibilityState``, ``QuarantineRecord``) is implemented here; those
belong to future, separately governed implementation groups. Forward
references to those not-yet-implemented families are shape-only,
family-tagged pointers and do not require the referenced family's own
model class to exist.

Tier boundary: both ``PublicationAttempt`` and ``PublicationEvidence`` are
Tier 1 (strict, no ``_extensions`` escape hatch).
"""

from __future__ import annotations

import dataclasses
import enum
import re
from collections.abc import Mapping
from typing import Any

from pcae.cltr.authority.cas_expectation import CasExpectation
from pcae.cltr.authority.digest import (
    GenerationDigest,
    PointerDigest,
    RecordDigest,
    ReferencedRecordDigest,
    Sha256Digest,
)
from pcae.cltr.authority.enums import (
    AuthorityKind,
    AuthorityRole,
    CompatibilityMode,
    JournalLockState,
    LegacyLifecycleStateWire,
    PublicationState,
    ReasonCode,
    RecordFamily,
)
from pcae.cltr.authority.envelope import RecordEnvelope, SchemaVersionString, Timestamp
from pcae.cltr.authority.errors import (
    TypedModelConstructionError,
    TypedModelInternalInvariantError,
    UnsupportedSchemaVersionError,
)
from pcae.cltr.authority.identity import GenerationId, MigrationEpochToken, RecordId, TransitionId
from pcae.cltr.authority.limitations import AuthorityDisclosure, Limitations
from pcae.cltr.authority.references import GenerationReference, RecordReference, require_family
from pcae.cltr.authority.sentinels import ABSENT, AbsentType
from pcae.cltr.authority.serialization import field_from_payload, serialize_value, to_dict_fields

# ---------------------------------------------------------------------------
# Record-local enums (family-scoped, not part of the shared cross-family
# enums in enums.py -- matching the schema layer's own non-centralization
# choice, same precedent as authority_core.py / request_readiness.py /
# authorization_candidate.py).
# ---------------------------------------------------------------------------


class PublicationOutcome(str, enum.Enum):
    """``PublicationEvidence``'s record-local ``outcome`` field (Sec.8.8, 8
    values, home schema ``publication_evidence.schema.json``).
    'publication_uncertain' requires ``uncertainty_detail``;
    'published_and_verified' requires ``target_readback`` and
    ``authoritative_generation`` (all enforced below). A schema-valid
    outcome here never itself proves the claimed publication result is
    true (Layer 4/5/6)."""

    NOT_ATTEMPTED = "not_attempted"
    CAS_REJECTED = "cas_rejected"
    FAILED_BEFORE_REPLACEMENT = "failed_before_replacement"
    PUBLICATION_UNCERTAIN = "publication_uncertain"
    PUBLISHED_AND_VERIFIED = "published_and_verified"
    POST_PUBLICATION_VERIFICATION_FAILED = "post_publication_verification_failed"
    CONFLICT = "conflict"
    QUARANTINED = "quarantined"


# ---------------------------------------------------------------------------
# Nested value objects
# ---------------------------------------------------------------------------

_DISCLOSURE_TEXT_MAX_LENGTH = 500
_DISCLOSURE_TEXT_PATTERN = re.compile(r"^[\x20-\x7E]*$")


def _validate_disclosure_text(value: Any, owner: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= _DISCLOSURE_TEXT_MAX_LENGTH):
        raise TypedModelConstructionError(
            f"{owner} must be a non-empty string of at most "
            f"{_DISCLOSURE_TEXT_MAX_LENGTH} characters"
        )
    if not _DISCLOSURE_TEXT_PATTERN.fullmatch(value):
        raise TypedModelConstructionError(f"{owner} must be single-line printable ASCII only")
    return value


@dataclasses.dataclass(frozen=True)
class PublicationAttemptUncertainty:
    """``PublicationAttempt``'s bounded local ``uncertainty`` disclosure
    object (mirrors ``authority_state.schema.json``'s ``uncertainty``
    $def). Present only when ``state`` is 'publication_uncertain'. A
    disclosure only -- never itself a resolution of the uncertainty it
    names."""

    reason: str

    def __post_init__(self) -> None:
        _validate_disclosure_text(self.reason, "PublicationAttemptUncertainty.reason")


@dataclasses.dataclass(frozen=True)
class PublicationEvidenceUncertaintyDetail:
    """``PublicationEvidence``'s bounded local ``uncertainty_detail``
    object (Sec.16 row 2). Present only when ``outcome`` is
    'publication_uncertain'. ``retry_recommended`` is a structural
    recommendation flag only -- never itself authorizes, schedules, or
    performs a retry (Layer 6)."""

    last_known_state: PublicationState
    retry_recommended: bool


# ---------------------------------------------------------------------------
# Shared field-extraction helpers (Layer 3 construction pipeline, 136Y plan
# Sec.16). Deliberately self-contained within this module rather than
# importing another group module's private helpers -- each group module
# owns its own Layer 3 construction boilerplate, matching authority_core.py,
# request_readiness.py, and authorization_candidate.py's own
# precedent-setting structure.
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


def _require_cross_family_reference_fields(value: Mapping[str, Any], *, owner: str) -> None:
    for required_key in ("schema_id", "schema_version"):
        if required_key not in value:
            raise TypedModelConstructionError(
                f"{owner}.{required_key} is unconditionally required (Sec.12 "
                "cross-family reference rule)"
            )


_GENERATION_REFERENCE_KNOWN_KEYS = frozenset({"generation_id", "generation_digest"})


def _generation_reference_from_dict(value: Mapping[str, Any], *, owner: str) -> GenerationReference:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _GENERATION_REFERENCE_KNOWN_KEYS, owner)
    for required_key in ("generation_id", "generation_digest"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    return GenerationReference(
        generation_id=GenerationId(_require_str(payload["generation_id"], f"{owner}.generation_id")),
        generation_digest=GenerationDigest(
            _require_str(payload["generation_digest"], f"{owner}.generation_digest")
        ),
    )


_CAS_EXPECTATION_KNOWN_KEYS = frozenset(
    {
        "expected_authority_kind",
        "expected_authority_epoch",
        "expected_authoritative_generation",
        "expected_authority_pointer_digest",
        "expected_authority_state_digest",
        "expected_migration_epoch",
        "expected_source_lifecycle_state",
        "expected_compatibility_mode",
        "expected_journal_lock_state",
        "expected_request_reference",
        "expected_certification_reference",
    }
)


def _cas_expectation_from_dict(value: Mapping[str, Any], *, owner: str) -> CasExpectation:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _CAS_EXPECTATION_KNOWN_KEYS, owner)
    for required_key in _CAS_EXPECTATION_KNOWN_KEYS:
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    return CasExpectation(
        expected_authority_kind=AuthorityKind(
            _require_str(payload["expected_authority_kind"], f"{owner}.expected_authority_kind")
        ),
        expected_authority_epoch=_record_reference_from_dict(
            payload["expected_authority_epoch"],
            required_family=RecordFamily.AUTHORITY_EPOCH,
            owner=f"{owner}.expected_authority_epoch",
        ),
        expected_authoritative_generation=_generation_reference_from_dict(
            payload["expected_authoritative_generation"],
            owner=f"{owner}.expected_authoritative_generation",
        ),
        expected_authority_pointer_digest=PointerDigest(
            _require_str(
                payload["expected_authority_pointer_digest"],
                f"{owner}.expected_authority_pointer_digest",
            )
        ),
        expected_authority_state_digest=Sha256Digest(
            _require_str(
                payload["expected_authority_state_digest"], f"{owner}.expected_authority_state_digest"
            )
        ),
        expected_migration_epoch=MigrationEpochToken(
            _require_str(payload["expected_migration_epoch"], f"{owner}.expected_migration_epoch")
        ),
        expected_source_lifecycle_state=LegacyLifecycleStateWire(
            _require_str(
                payload["expected_source_lifecycle_state"], f"{owner}.expected_source_lifecycle_state"
            )
        ),
        expected_compatibility_mode=CompatibilityMode(
            _require_str(payload["expected_compatibility_mode"], f"{owner}.expected_compatibility_mode")
        ),
        expected_journal_lock_state=JournalLockState(
            _require_str(payload["expected_journal_lock_state"], f"{owner}.expected_journal_lock_state")
        ),
        expected_request_reference=_record_reference_from_dict(
            payload["expected_request_reference"],
            required_family=RecordFamily.CUTOVER_REQUEST,
            owner=f"{owner}.expected_request_reference",
        ),
        expected_certification_reference=_record_reference_from_dict(
            payload["expected_certification_reference"],
            required_family=RecordFamily.CERTIFICATION,
            owner=f"{owner}.expected_certification_reference",
        ),
    )


_AUTHORITY_DISCLOSURE_KNOWN_KEYS = frozenset({"authority_role", "is_authoritative", "disclosure_text"})


def _authority_disclosure_from_dict(value: Mapping[str, Any], *, owner: str) -> AuthorityDisclosure:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _AUTHORITY_DISCLOSURE_KNOWN_KEYS, owner)
    for required_key in ("authority_role", "is_authoritative", "disclosure_text"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    if payload["is_authoritative"] is not False:
        raise TypedModelConstructionError(f"{owner}.is_authoritative must be the frozen const false")
    return AuthorityDisclosure(
        authority_role=AuthorityRole(_require_str(payload["authority_role"], f"{owner}.authority_role")),
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
# PublicationAttempt
# ---------------------------------------------------------------------------

_PUBLICATION_ATTEMPT_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/publication_attempt.schema.json"
)
_PUBLICATION_ATTEMPT_RECORD_TYPE = "publication_attempt"
_PUBLICATION_ATTEMPT_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})
_PUBLICATION_ATTEMPT_FAILURE_STATES = frozenset({PublicationState.GATE_REJECTED, PublicationState.CONFLICT})

_PUBLICATION_ATTEMPT_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "transition_id",
        "attempt_id",
        "request_reference",
        "candidate_reference",
        "certification_reference",
        "cas_expectation",
        "source_authority_reference",
        "target_authority_reference",
        "attempt_sequence",
        "temporary_pointer_reference",
        "state",
        "uncertainty",
        "failure_classification",
        "limitations",
        "authority_disclosure",
    }
)

_PUBLICATION_ATTEMPT_UNCERTAINTY_KNOWN_KEYS = frozenset({"reason"})


def _publication_attempt_uncertainty_from_dict(
    value: Mapping[str, Any], *, owner: str
) -> PublicationAttemptUncertainty:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _PUBLICATION_ATTEMPT_UNCERTAINTY_KNOWN_KEYS, owner)
    if "reason" not in payload:
        raise TypedModelConstructionError(f"{owner}: missing required field 'reason'")
    return PublicationAttemptUncertainty(
        reason=_validate_disclosure_text(payload["reason"], f"{owner}.reason")
    )


@dataclasses.dataclass(frozen=True)
class PublicationAttempt:
    """Shape-only wire contract for a ``PublicationAttempt`` companion
    record (``records/publication_attempt.schema.json``, contract Sec.25).
    A ``PublicationAttempt`` document describes an attempted publication
    operation bound to a specific candidate, certification, and CAS
    expectation; it never itself performs publication, invokes
    compare-and-swap, mutates an authority pointer, establishes current
    authority, proves a publication occurred, proves a CAS succeeded,
    activates CLTR authority, demotes or retires legacy authority,
    triggers notification, or creates production markers or receipts
    (Sec.1, Sec.40). Legacy lifecycle remains the sole production
    authority; CLTR remains derivative. Tier 1 (strict): no
    ``_extensions`` escape hatch exists on this family.

    This model does not: publish anything, execute CAS, compare expected
    and current generation, acquire locks, retry, update pointers, write
    manifests, promote artifacts, resolve any referenced record, inspect
    runtime state, or persist itself. A publication attempt record
    describes an attempt; it does not perform one.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    transition_id: TransitionId
    attempt_id: RecordId
    request_reference: RecordReference
    candidate_reference: RecordReference
    certification_reference: RecordReference
    cas_expectation: CasExpectation
    source_authority_reference: RecordReference
    target_authority_reference: RecordReference
    attempt_sequence: int
    state: PublicationState
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    temporary_pointer_reference: RecordReference | AbsentType = ABSENT
    uncertainty: PublicationAttemptUncertainty | AbsentType = ABSENT
    failure_classification: ReasonCode | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _PUBLICATION_ATTEMPT_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"PublicationAttempt.envelope.record_type must be "
                f"{_PUBLICATION_ATTEMPT_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _PUBLICATION_ATTEMPT_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"PublicationAttempt.envelope.schema_id must be the frozen "
                f"const {_PUBLICATION_ATTEMPT_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family (Sec.9's 12-file list, schema description).
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "PublicationAttempt.authority_disclosure.authority_role must "
                "not be 'authoritative': an attempt record is never itself a "
                "resolved live-authority claim, even when state is "
                "'published' or 'verified'"
            )
        require_family(self.request_reference, RecordFamily.CUTOVER_REQUEST)
        require_family(self.candidate_reference, RecordFamily.CUTOVER_CANDIDATE)
        require_family(self.certification_reference, RecordFamily.CERTIFICATION)
        require_family(self.source_authority_reference, RecordFamily.AUTHORITY_EPOCH)
        require_family(self.target_authority_reference, RecordFamily.AUTHORITY_EPOCH)
        if not isinstance(self.attempt_sequence, int) or isinstance(self.attempt_sequence, bool):
            raise TypedModelInternalInvariantError(
                "PublicationAttempt.attempt_sequence must be a non-negative integer"
            )
        if self.attempt_sequence < 0:
            raise TypedModelInternalInvariantError(
                "PublicationAttempt.attempt_sequence must be a non-negative integer"
            )
        # state <-> uncertainty conditional (Sec.25).
        if self.state is PublicationState.PUBLICATION_UNCERTAIN and self.uncertainty is ABSENT:
            raise TypedModelInternalInvariantError(
                "PublicationAttempt.uncertainty is required when state is "
                "'publication_uncertain'"
            )
        if self.state is not PublicationState.PUBLICATION_UNCERTAIN and self.uncertainty is not ABSENT:
            raise TypedModelInternalInvariantError(
                "PublicationAttempt.uncertainty is forbidden unless state is "
                "'publication_uncertain'"
            )
        # state <-> failure_classification conditional (Sec.25).
        if self.state in _PUBLICATION_ATTEMPT_FAILURE_STATES and self.failure_classification is ABSENT:
            raise TypedModelInternalInvariantError(
                "PublicationAttempt.failure_classification is required when "
                "state is 'gate_rejected' or 'conflict'"
            )
        if (
            self.state not in _PUBLICATION_ATTEMPT_FAILURE_STATES
            and self.failure_classification is not ABSENT
        ):
            raise TypedModelInternalInvariantError(
                "PublicationAttempt.failure_classification is forbidden "
                "unless state is 'gate_rejected' or 'conflict'"
            )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "PublicationAttempt":
        if schema_version not in _PUBLICATION_ATTEMPT_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"PublicationAttempt does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "PublicationAttempt")
        _reject_unknown_keys(payload, _PUBLICATION_ATTEMPT_KNOWN_KEYS, "PublicationAttempt")

        envelope = _envelope_from_payload(
            payload,
            record_type=_PUBLICATION_ATTEMPT_RECORD_TYPE,
            schema_id=_PUBLICATION_ATTEMPT_SCHEMA_ID,
        )

        for required_key in (
            "migration_epoch",
            "transition_id",
            "attempt_id",
            "request_reference",
            "candidate_reference",
            "certification_reference",
            "cas_expectation",
            "source_authority_reference",
            "target_authority_reference",
            "attempt_sequence",
            "state",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"PublicationAttempt: missing required field {required_key!r}"
                )

        request_reference_raw = _require_mapping(
            payload["request_reference"], "PublicationAttempt.request_reference"
        )
        _require_cross_family_reference_fields(
            request_reference_raw, owner="PublicationAttempt.request_reference"
        )
        candidate_reference_raw = _require_mapping(
            payload["candidate_reference"], "PublicationAttempt.candidate_reference"
        )
        _require_cross_family_reference_fields(
            candidate_reference_raw, owner="PublicationAttempt.candidate_reference"
        )
        certification_reference_raw = _require_mapping(
            payload["certification_reference"], "PublicationAttempt.certification_reference"
        )
        _require_cross_family_reference_fields(
            certification_reference_raw, owner="PublicationAttempt.certification_reference"
        )

        raw_temporary_pointer_reference = field_from_payload(payload, "temporary_pointer_reference")
        temporary_pointer_reference: RecordReference | AbsentType
        if raw_temporary_pointer_reference is ABSENT:
            temporary_pointer_reference = ABSENT
        else:
            temporary_pointer_reference = _record_reference_from_dict(
                raw_temporary_pointer_reference,
                required_family=None,
                owner="PublicationAttempt.temporary_pointer_reference",
            )

        raw_uncertainty = field_from_payload(payload, "uncertainty")
        uncertainty: PublicationAttemptUncertainty | AbsentType
        if raw_uncertainty is ABSENT:
            uncertainty = ABSENT
        else:
            uncertainty = _publication_attempt_uncertainty_from_dict(
                raw_uncertainty, owner="PublicationAttempt.uncertainty"
            )

        raw_failure_classification = field_from_payload(payload, "failure_classification")
        failure_classification: ReasonCode | AbsentType
        if raw_failure_classification is ABSENT:
            failure_classification = ABSENT
        else:
            failure_classification = ReasonCode(
                _require_str(raw_failure_classification, "PublicationAttempt.failure_classification")
            )

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "PublicationAttempt.migration_epoch")
            ),
            transition_id=TransitionId(
                _require_str(payload["transition_id"], "PublicationAttempt.transition_id")
            ),
            attempt_id=RecordId(_require_str(payload["attempt_id"], "PublicationAttempt.attempt_id")),
            request_reference=_record_reference_from_dict(
                request_reference_raw,
                required_family=RecordFamily.CUTOVER_REQUEST,
                owner="PublicationAttempt.request_reference",
            ),
            candidate_reference=_record_reference_from_dict(
                candidate_reference_raw,
                required_family=RecordFamily.CUTOVER_CANDIDATE,
                owner="PublicationAttempt.candidate_reference",
            ),
            certification_reference=_record_reference_from_dict(
                certification_reference_raw,
                required_family=RecordFamily.CERTIFICATION,
                owner="PublicationAttempt.certification_reference",
            ),
            cas_expectation=_cas_expectation_from_dict(
                payload["cas_expectation"], owner="PublicationAttempt.cas_expectation"
            ),
            source_authority_reference=_record_reference_from_dict(
                payload["source_authority_reference"],
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="PublicationAttempt.source_authority_reference",
            ),
            target_authority_reference=_record_reference_from_dict(
                payload["target_authority_reference"],
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="PublicationAttempt.target_authority_reference",
            ),
            attempt_sequence=payload["attempt_sequence"],
            temporary_pointer_reference=temporary_pointer_reference,
            state=PublicationState(_require_str(payload["state"], "PublicationAttempt.state")),
            uncertainty=uncertainty,
            failure_classification=failure_classification,
            limitations=_limitations_from_list(
                payload["limitations"], owner="PublicationAttempt.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="PublicationAttempt.authority_disclosure"
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["transition_id"] = serialize_value(self.transition_id)
        result["attempt_id"] = serialize_value(self.attempt_id)
        result["request_reference"] = serialize_value(self.request_reference)
        result["candidate_reference"] = serialize_value(self.candidate_reference)
        result["certification_reference"] = serialize_value(self.certification_reference)
        result["cas_expectation"] = serialize_value(self.cas_expectation)
        result["source_authority_reference"] = serialize_value(self.source_authority_reference)
        result["target_authority_reference"] = serialize_value(self.target_authority_reference)
        result["attempt_sequence"] = self.attempt_sequence
        if self.temporary_pointer_reference is not ABSENT:
            result["temporary_pointer_reference"] = serialize_value(self.temporary_pointer_reference)
        result["state"] = serialize_value(self.state)
        if self.uncertainty is not ABSENT:
            result["uncertainty"] = serialize_value(self.uncertainty)
        if self.failure_classification is not ABSENT:
            result["failure_classification"] = serialize_value(self.failure_classification)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        return result


# ---------------------------------------------------------------------------
# PublicationEvidence
# ---------------------------------------------------------------------------

_PUBLICATION_EVIDENCE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/publication_evidence.schema.json"
)
_PUBLICATION_EVIDENCE_RECORD_TYPE = "publication_evidence"
_PUBLICATION_EVIDENCE_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_PUBLICATION_EVIDENCE_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "transition_id",
        "attempt_reference",
        "outcome",
        "uncertainty_detail",
        "target_readback",
        "authoritative_generation",
        "limitations",
        "authority_disclosure",
    }
)

_PUBLICATION_EVIDENCE_UNCERTAINTY_DETAIL_KNOWN_KEYS = frozenset({"last_known_state", "retry_recommended"})


def _publication_evidence_uncertainty_detail_from_dict(
    value: Mapping[str, Any], *, owner: str
) -> PublicationEvidenceUncertaintyDetail:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _PUBLICATION_EVIDENCE_UNCERTAINTY_DETAIL_KNOWN_KEYS, owner)
    for required_key in ("last_known_state", "retry_recommended"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    retry_recommended = payload["retry_recommended"]
    if not isinstance(retry_recommended, bool):
        raise TypedModelConstructionError(f"{owner}.retry_recommended must be a boolean")
    return PublicationEvidenceUncertaintyDetail(
        last_known_state=PublicationState(
            _require_str(payload["last_known_state"], f"{owner}.last_known_state")
        ),
        retry_recommended=retry_recommended,
    )


@dataclasses.dataclass(frozen=True)
class PublicationEvidence:
    """Shape-only wire contract for a ``PublicationEvidence`` companion
    record (``records/publication_evidence.schema.json``, contract
    Sec.26). A ``PublicationEvidence`` document describes a claimed
    publication outcome for a specific ``PublicationAttempt``; it never
    itself publishes, activates authority, establishes that an external
    system is truthful, establishes current authority, cryptographically
    verifies evidence, replaces semantic verification, replaces recovery
    evidence, replaces lifecycle authority, dispatches notifications, or
    creates authoritative markers or receipts (Sec.1, Sec.40). Schema
    validity does not prove publication success. Legacy lifecycle remains
    the sole production authority; CLTR remains derivative. Tier 1
    (strict): no ``_extensions`` escape hatch exists on this family.

    ``authority_role`` 'authoritative' is a structurally permitted value on
    this record family (alongside ``AuthorityState``, Sec.9), only in the
    terminal 'published_and_verified' outcome alongside a non-null
    ``authoritative_generation`` reference; ``is_authoritative``
    nonetheless remains the frozen const ``False`` unconditionally per the
    shared ``AuthorityDisclosure`` definition (mirrors
    ``AuthorityState``'s own disclosed limitation, NON-BLOCKING-136J-1).

    This model does not: verify evidence, validate a manifest, check an
    artifact, confirm publication, evaluate provider success, or validate
    a receipt. A publication evidence record preserves declared evidence
    only.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    transition_id: TransitionId
    attempt_reference: RecordReference
    outcome: PublicationOutcome
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    uncertainty_detail: PublicationEvidenceUncertaintyDetail | AbsentType = ABSENT
    target_readback: RecordReference | AbsentType = ABSENT
    authoritative_generation: GenerationReference | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _PUBLICATION_EVIDENCE_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"PublicationEvidence.envelope.record_type must be "
                f"{_PUBLICATION_EVIDENCE_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _PUBLICATION_EVIDENCE_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"PublicationEvidence.envelope.schema_id must be the frozen "
                f"const {_PUBLICATION_EVIDENCE_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        require_family(self.attempt_reference, RecordFamily.PUBLICATION_ATTEMPT)
        # outcome <-> uncertainty_detail conditional (Sec.16, Sec.26).
        if self.outcome is PublicationOutcome.PUBLICATION_UNCERTAIN and self.uncertainty_detail is ABSENT:
            raise TypedModelInternalInvariantError(
                "PublicationEvidence.uncertainty_detail is required when "
                "outcome is 'publication_uncertain'"
            )
        if (
            self.outcome is not PublicationOutcome.PUBLICATION_UNCERTAIN
            and self.uncertainty_detail is not ABSENT
        ):
            raise TypedModelInternalInvariantError(
                "PublicationEvidence.uncertainty_detail is forbidden unless "
                "outcome is 'publication_uncertain'"
            )
        # outcome <-> target_readback / authoritative_generation conditionals
        # (Sec.16, Sec.26).
        if self.outcome is PublicationOutcome.PUBLISHED_AND_VERIFIED:
            if self.target_readback is ABSENT:
                raise TypedModelInternalInvariantError(
                    "PublicationEvidence.target_readback is required when "
                    "outcome is 'published_and_verified'"
                )
            if self.authoritative_generation is ABSENT:
                raise TypedModelInternalInvariantError(
                    "PublicationEvidence.authoritative_generation is required "
                    "when outcome is 'published_and_verified'"
                )
        else:
            if self.target_readback is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "PublicationEvidence.target_readback is forbidden unless "
                    "outcome is 'published_and_verified'"
                )
            if self.authoritative_generation is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "PublicationEvidence.authoritative_generation is "
                    "forbidden unless outcome is 'published_and_verified'"
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "PublicationEvidence":
        if schema_version not in _PUBLICATION_EVIDENCE_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"PublicationEvidence does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "PublicationEvidence")
        _reject_unknown_keys(payload, _PUBLICATION_EVIDENCE_KNOWN_KEYS, "PublicationEvidence")

        envelope = _envelope_from_payload(
            payload,
            record_type=_PUBLICATION_EVIDENCE_RECORD_TYPE,
            schema_id=_PUBLICATION_EVIDENCE_SCHEMA_ID,
        )

        for required_key in (
            "migration_epoch",
            "transition_id",
            "attempt_reference",
            "outcome",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"PublicationEvidence: missing required field {required_key!r}"
                )

        attempt_reference_raw = _require_mapping(
            payload["attempt_reference"], "PublicationEvidence.attempt_reference"
        )
        _require_cross_family_reference_fields(
            attempt_reference_raw, owner="PublicationEvidence.attempt_reference"
        )

        raw_uncertainty_detail = field_from_payload(payload, "uncertainty_detail")
        uncertainty_detail: PublicationEvidenceUncertaintyDetail | AbsentType
        if raw_uncertainty_detail is ABSENT:
            uncertainty_detail = ABSENT
        else:
            uncertainty_detail = _publication_evidence_uncertainty_detail_from_dict(
                raw_uncertainty_detail, owner="PublicationEvidence.uncertainty_detail"
            )

        raw_target_readback = field_from_payload(payload, "target_readback")
        target_readback: RecordReference | AbsentType
        if raw_target_readback is ABSENT:
            target_readback = ABSENT
        else:
            target_readback = _record_reference_from_dict(
                raw_target_readback,
                required_family=None,
                owner="PublicationEvidence.target_readback",
            )

        raw_authoritative_generation = field_from_payload(payload, "authoritative_generation")
        authoritative_generation: GenerationReference | AbsentType
        if raw_authoritative_generation is ABSENT:
            authoritative_generation = ABSENT
        else:
            authoritative_generation = _generation_reference_from_dict(
                raw_authoritative_generation, owner="PublicationEvidence.authoritative_generation"
            )

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "PublicationEvidence.migration_epoch")
            ),
            transition_id=TransitionId(
                _require_str(payload["transition_id"], "PublicationEvidence.transition_id")
            ),
            attempt_reference=_record_reference_from_dict(
                attempt_reference_raw,
                required_family=RecordFamily.PUBLICATION_ATTEMPT,
                owner="PublicationEvidence.attempt_reference",
            ),
            outcome=PublicationOutcome(_require_str(payload["outcome"], "PublicationEvidence.outcome")),
            uncertainty_detail=uncertainty_detail,
            target_readback=target_readback,
            authoritative_generation=authoritative_generation,
            limitations=_limitations_from_list(
                payload["limitations"], owner="PublicationEvidence.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="PublicationEvidence.authority_disclosure"
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["transition_id"] = serialize_value(self.transition_id)
        result["attempt_reference"] = serialize_value(self.attempt_reference)
        result["outcome"] = serialize_value(self.outcome)
        if self.uncertainty_detail is not ABSENT:
            result["uncertainty_detail"] = serialize_value(self.uncertainty_detail)
        if self.target_readback is not ABSENT:
            result["target_readback"] = serialize_value(self.target_readback)
        if self.authoritative_generation is not ABSENT:
            result["authoritative_generation"] = serialize_value(self.authoritative_generation)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        return result


__all__ = [
    "PublicationOutcome",
    "PublicationAttemptUncertainty",
    "PublicationEvidenceUncertaintyDetail",
    "PublicationAttempt",
    "PublicationEvidence",
]
