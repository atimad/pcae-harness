"""Phase 136AF: Stage 3 Typed Authority Model Authorization and Candidate
Implementation (Typed Model Implementation Group 4, per the 136Y plan
Sec.4/Sec.23, package layout Sec.7).

Implements exactly three record-family models: ``HumanAuthorization``,
``CutoverCandidate``, and ``Certification``, schema-backed by
``records/human_authorization.schema.json``,
``records/cutover_candidate.schema.json``, and
``records/certification.schema.json`` respectively.

A constructed instance of any of the three models asserts only "this JSON
was well-formed against schema X at version Y and can be represented
without loss" -- never operational truth. None of the three models
authenticates a human, verifies a signature, determines whether an
authorization is valid, approves or rejects cutover, calculates candidate
eligibility, certifies operational truth, selects current authority,
resolves a reference, verifies a digest, evaluates evidence, persists a
record, publishes an artifact, mutates lifecycle state, executes cutover,
or performs recovery. A ``HumanAuthorization`` is a representation of a
recorded decision, never proof a human made it or that it is valid; a
``CutoverCandidate`` is a representation of a proposed attempt, never proof
of eligibility; a ``Certification`` is a representation of an evidence-based
verification result, never proof of certification authenticity. Legacy
lifecycle remains the sole production authority; CLTR remains derivative.

No other record-family model (``PublicationAttempt``, ``PublicationEvidence``,
``ConcurrencyConflict``, ``RecoveryJournalEntry``,
``NotificationAuthorityBinding``, ``MarkerAuthorityBinding``,
``FinalizationReceiptAuthorityBinding``, ``CompatibilityState``,
``QuarantineRecord``) is implemented here; those belong to future,
separately governed implementation groups. Forward references to those
not-yet-implemented families (``HumanAuthorization.use_binding`` ->
``publication_attempt``) are shape-only, family-tagged pointers, matching
the ``AuthorityState.publication_evidence_reference`` precedent (136AB) --
they do not require the referenced family's own model class to exist.

Tier boundary: ``HumanAuthorization`` and ``Certification`` are Tier 1
(strict, no ``_extensions`` escape hatch). ``CutoverCandidate`` is Tier 2
(``_extensions`` permitted, string-valued map only, matching
``ReadinessPackage``'s existing Tier 2 precedent, 136AD).
"""

from __future__ import annotations

import dataclasses
import enum
import re
from collections.abc import Mapping
from typing import Any, Tuple

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
    ReasonCode,
    RecordFamily,
)
from pcae.cltr.authority.envelope import RecordEnvelope, SchemaVersionString, Timestamp
from pcae.cltr.authority.errors import (
    TypedModelConstructionError,
    TypedModelInternalInvariantError,
    UnsupportedSchemaVersionError,
)
from pcae.cltr.authority.extensions import ExtensionMapping
from pcae.cltr.authority.identity import (
    GenerationId,
    MigrationEpochToken,
    PhaseIdentity,
    PrincipalIdentifier,
    RecordId,
)
from pcae.cltr.authority.limitations import AuthorityDisclosure, Limitations
from pcae.cltr.authority.references import GenerationReference, RecordReference, require_family
from pcae.cltr.authority.sentinels import ABSENT, AbsentType
from pcae.cltr.authority.serialization import field_from_payload, serialize_value, to_dict_fields

# ---------------------------------------------------------------------------
# Record-local enums (family-scoped, not part of the shared cross-family
# enums in enums.py -- matching the schema layer's own non-centralization
# choice, same precedent as authority_core.py / request_readiness.py).
# ---------------------------------------------------------------------------


class AuthorizationMethod(str, enum.Enum):
    """``HumanAuthorization``'s ``method`` field (Sec.21, 2 values).
    ``proof_reference`` is required when this is 'signed_attestation' and
    forbidden when this is 'manual_review' (enforced below)."""

    MANUAL_REVIEW = "manual_review"
    SIGNED_ATTESTATION = "signed_attestation"


class AuthorizationState(str, enum.Enum):
    """``HumanAuthorization``'s record-local ``state`` field (Sec.8.8, 4
    values). 'used' requires ``use_binding``; 'revoked' requires
    ``revocation_metadata`` (both enforced below). A schema-valid state
    here never itself proves current freshness, actual revocation truth,
    or actual prior use (Layer 4/5)."""

    ISSUED = "issued"
    USED = "used"
    REVOKED = "revoked"
    EXPIRED = "expired"


class CandidateState(str, enum.Enum):
    """``CutoverCandidate``'s record-local ``state`` field (Sec.8.8, 6
    values). No Sec.16 conditional row exists for this family's state
    branches; reaching 'certified' here is a local status label only and
    never itself proves certification, publication, or cutover occurred
    (Layer 4/6)."""

    PROPOSED = "proposed"
    VERIFIED = "verified"
    CERTIFYING = "certifying"
    CERTIFIED = "certified"
    SUPERSEDED = "superseded"
    QUARANTINED = "quarantined"


class CertificationState(str, enum.Enum):
    """``Certification``'s record-local ``state`` field (Sec.8.8, 4
    values). 'stale' requires ``staleness``; 'invalidated' requires
    ``invalidation`` (both enforced below). A 'certified' value here never
    itself proves certification authenticity (Layer 4)."""

    PENDING = "pending"
    CERTIFIED = "certified"
    STALE = "stale"
    INVALIDATED = "invalidated"


# ---------------------------------------------------------------------------
# Nested value objects
# ---------------------------------------------------------------------------

_REPLAY_BINDING_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,256}$")


def _validate_replay_binding(value: Any) -> str:
    if not isinstance(value, str) or not _REPLAY_BINDING_PATTERN.fullmatch(value):
        raise TypedModelConstructionError(
            "HumanAuthorization.replay_binding must be a string of 1-256 "
            "characters matching the required opaque token-reference shape"
        )
    return value


@dataclasses.dataclass(frozen=True)
class RevocationMetadata:
    """``HumanAuthorization``'s bounded local ``revocation_metadata``
    object (Sec.16 row 4). Present only when ``state`` is 'revoked'. A
    disclosure only -- never itself a verification that revocation was
    properly authorized."""

    revoked_at: Timestamp
    revoked_by: PrincipalIdentifier
    reason_code: ReasonCode


@dataclasses.dataclass(frozen=True)
class Staleness:
    """``Certification``'s bounded local ``staleness`` disclosure object.
    Present only when ``state`` is 'stale'."""

    detected_at: Timestamp
    reason_code: ReasonCode


@dataclasses.dataclass(frozen=True)
class Invalidation:
    """``Certification``'s bounded local ``invalidation`` disclosure
    object. Present only when ``state`` is 'invalidated'."""

    invalidated_at: Timestamp
    reason_code: ReasonCode


# ---------------------------------------------------------------------------
# Shared field-extraction helpers (Layer 3 construction pipeline, 136Y plan
# Sec.16). Deliberately self-contained within this module rather than
# importing another group module's private helpers -- each group module
# owns its own Layer 3 construction boilerplate, matching authority_core.py
# and request_readiness.py's own precedent-setting structure.
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
# HumanAuthorization
# ---------------------------------------------------------------------------

_HUMAN_AUTHORIZATION_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/human_authorization.schema.json"
)
_HUMAN_AUTHORIZATION_RECORD_TYPE = "human_authorization"
_HUMAN_AUTHORIZATION_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_HUMAN_AUTHORIZATION_KNOWN_KEYS = frozenset(
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
        "principal",
        "method",
        "request_reference",
        "readiness_reference",
        "target_reference",
        "issued_at",
        "expires_at",
        "state",
        "revocation_metadata",
        "use_binding",
        "replay_binding",
        "risk_acknowledgement",
        "proof_reference",
        "limitations",
        "authority_disclosure",
    }
)

_REVOCATION_METADATA_KNOWN_KEYS = frozenset({"revoked_at", "revoked_by", "reason_code"})


def _revocation_metadata_from_dict(value: Mapping[str, Any], *, owner: str) -> RevocationMetadata:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _REVOCATION_METADATA_KNOWN_KEYS, owner)
    for required_key in ("revoked_at", "revoked_by", "reason_code"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    return RevocationMetadata(
        revoked_at=Timestamp(_require_str(payload["revoked_at"], f"{owner}.revoked_at")),
        revoked_by=PrincipalIdentifier(_require_str(payload["revoked_by"], f"{owner}.revoked_by")),
        reason_code=ReasonCode(_require_str(payload["reason_code"], f"{owner}.reason_code")),
    )


@dataclasses.dataclass(frozen=True)
class HumanAuthorization:
    """Shape-only wire contract for a ``HumanAuthorization`` companion
    record (``records/human_authorization.schema.json``, contract Sec.21).
    A ``HumanAuthorization`` document represents a principal's decision to
    permit a specific, scoped cutover attempt to proceed; it never itself
    proves a real human actually made that decision, proves signer
    identity, proves proof/signature validity, establishes replay/freshness
    truth, certifies anything, publishes authority, executes cutover, or
    establishes current authority (Sec.1, Sec.40). Tier 1 (strict): no
    ``_extensions`` escape hatch exists on this family.

    This model does not: authenticate the principal, verify a signature,
    determine authorization validity, check replay/freshness, resolve any
    referenced record, verify a digest, authorize a cutover, or persist
    anything. A ``HumanAuthorization`` is a representation of a recorded
    decision, never proof that decision is currently valid.
    """

    envelope: RecordEnvelope
    phase_id: PhaseIdentity
    migration_epoch: MigrationEpochToken
    principal: PrincipalIdentifier
    method: AuthorizationMethod
    request_reference: RecordReference
    readiness_reference: RecordReference
    target_reference: RecordReference
    issued_at: Timestamp
    expires_at: Timestamp
    state: AuthorizationState
    replay_binding: str
    risk_acknowledgement: bool
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    revocation_metadata: RevocationMetadata | AbsentType = ABSENT
    use_binding: RecordReference | AbsentType = ABSENT
    proof_reference: RecordReference | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _HUMAN_AUTHORIZATION_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"HumanAuthorization.envelope.record_type must be "
                f"{_HUMAN_AUTHORIZATION_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _HUMAN_AUTHORIZATION_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"HumanAuthorization.envelope.schema_id must be the frozen "
                f"const {_HUMAN_AUTHORIZATION_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family (Sec.9's 12-file list, schema description).
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "HumanAuthorization.authority_disclosure.authority_role must "
                "not be 'authoritative': an authorization is governance "
                "evidence of a recorded decision only, never a resolved "
                "live-authority claim"
            )
        require_family(self.request_reference, RecordFamily.CUTOVER_REQUEST)
        require_family(self.readiness_reference, RecordFamily.READINESS_PACKAGE)
        require_family(self.target_reference, RecordFamily.AUTHORITY_EPOCH)
        if self.risk_acknowledgement is not True:
            raise TypedModelInternalInvariantError(
                "HumanAuthorization.risk_acknowledgement must be the frozen "
                "const true"
            )
        _validate_replay_binding(self.replay_binding)
        # state <-> revocation_metadata conditional (Sec.16 row 4).
        if self.state is AuthorizationState.REVOKED and self.revocation_metadata is ABSENT:
            raise TypedModelInternalInvariantError(
                "HumanAuthorization.revocation_metadata is required when "
                "state is 'revoked'"
            )
        if self.state is not AuthorizationState.REVOKED and self.revocation_metadata is not ABSENT:
            raise TypedModelInternalInvariantError(
                "HumanAuthorization.revocation_metadata is forbidden unless "
                "state is 'revoked'"
            )
        # state <-> use_binding conditional (Sec.16 row 5).
        if self.state is AuthorizationState.USED and self.use_binding is ABSENT:
            raise TypedModelInternalInvariantError(
                "HumanAuthorization.use_binding is required when state is "
                "'used'"
            )
        if self.state is not AuthorizationState.USED and self.use_binding is not ABSENT:
            raise TypedModelInternalInvariantError(
                "HumanAuthorization.use_binding is forbidden unless state is "
                "'used'"
            )
        if self.use_binding is not ABSENT:
            require_family(self.use_binding, RecordFamily.PUBLICATION_ATTEMPT)
        # method <-> proof_reference conditional.
        if self.method is AuthorizationMethod.SIGNED_ATTESTATION and self.proof_reference is ABSENT:
            raise TypedModelInternalInvariantError(
                "HumanAuthorization.proof_reference is required when method "
                "is 'signed_attestation'"
            )
        if self.method is AuthorizationMethod.MANUAL_REVIEW and self.proof_reference is not ABSENT:
            raise TypedModelInternalInvariantError(
                "HumanAuthorization.proof_reference is forbidden when method "
                "is 'manual_review'"
            )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "HumanAuthorization":
        if schema_version not in _HUMAN_AUTHORIZATION_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"HumanAuthorization does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "HumanAuthorization")
        _reject_unknown_keys(payload, _HUMAN_AUTHORIZATION_KNOWN_KEYS, "HumanAuthorization")

        envelope = _envelope_from_payload(
            payload,
            record_type=_HUMAN_AUTHORIZATION_RECORD_TYPE,
            schema_id=_HUMAN_AUTHORIZATION_SCHEMA_ID,
        )

        for required_key in (
            "phase_id",
            "migration_epoch",
            "principal",
            "method",
            "request_reference",
            "readiness_reference",
            "target_reference",
            "issued_at",
            "expires_at",
            "state",
            "replay_binding",
            "risk_acknowledgement",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"HumanAuthorization: missing required field {required_key!r}"
                )

        request_reference_raw = _require_mapping(
            payload["request_reference"], "HumanAuthorization.request_reference"
        )
        _require_cross_family_reference_fields(
            request_reference_raw, owner="HumanAuthorization.request_reference"
        )
        readiness_reference_raw = _require_mapping(
            payload["readiness_reference"], "HumanAuthorization.readiness_reference"
        )
        _require_cross_family_reference_fields(
            readiness_reference_raw, owner="HumanAuthorization.readiness_reference"
        )
        target_reference_raw = _require_mapping(
            payload["target_reference"], "HumanAuthorization.target_reference"
        )
        _require_cross_family_reference_fields(
            target_reference_raw, owner="HumanAuthorization.target_reference"
        )

        raw_revocation_metadata = field_from_payload(payload, "revocation_metadata")
        revocation_metadata: RevocationMetadata | AbsentType
        if raw_revocation_metadata is ABSENT:
            revocation_metadata = ABSENT
        else:
            revocation_metadata = _revocation_metadata_from_dict(
                raw_revocation_metadata, owner="HumanAuthorization.revocation_metadata"
            )

        raw_use_binding = field_from_payload(payload, "use_binding")
        use_binding: RecordReference | AbsentType
        if raw_use_binding is ABSENT:
            use_binding = ABSENT
        else:
            use_binding = _record_reference_from_dict(
                raw_use_binding,
                required_family=RecordFamily.PUBLICATION_ATTEMPT,
                owner="HumanAuthorization.use_binding",
            )

        raw_proof_reference = field_from_payload(payload, "proof_reference")
        proof_reference: RecordReference | AbsentType
        if raw_proof_reference is ABSENT:
            proof_reference = ABSENT
        else:
            proof_reference = _record_reference_from_dict(
                raw_proof_reference,
                required_family=None,
                owner="HumanAuthorization.proof_reference",
            )

        return cls(
            envelope=envelope,
            phase_id=PhaseIdentity(_require_str(payload["phase_id"], "HumanAuthorization.phase_id")),
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "HumanAuthorization.migration_epoch")
            ),
            principal=PrincipalIdentifier(
                _require_str(payload["principal"], "HumanAuthorization.principal")
            ),
            method=AuthorizationMethod(_require_str(payload["method"], "HumanAuthorization.method")),
            request_reference=_record_reference_from_dict(
                request_reference_raw,
                required_family=RecordFamily.CUTOVER_REQUEST,
                owner="HumanAuthorization.request_reference",
            ),
            readiness_reference=_record_reference_from_dict(
                readiness_reference_raw,
                required_family=RecordFamily.READINESS_PACKAGE,
                owner="HumanAuthorization.readiness_reference",
            ),
            target_reference=_record_reference_from_dict(
                target_reference_raw,
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="HumanAuthorization.target_reference",
            ),
            issued_at=Timestamp(_require_str(payload["issued_at"], "HumanAuthorization.issued_at")),
            expires_at=Timestamp(_require_str(payload["expires_at"], "HumanAuthorization.expires_at")),
            state=AuthorizationState(_require_str(payload["state"], "HumanAuthorization.state")),
            revocation_metadata=revocation_metadata,
            use_binding=use_binding,
            replay_binding=_validate_replay_binding(payload["replay_binding"]),
            risk_acknowledgement=payload["risk_acknowledgement"],
            proof_reference=proof_reference,
            limitations=_limitations_from_list(
                payload["limitations"], owner="HumanAuthorization.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="HumanAuthorization.authority_disclosure"
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["phase_id"] = serialize_value(self.phase_id)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["principal"] = serialize_value(self.principal)
        result["method"] = serialize_value(self.method)
        result["request_reference"] = serialize_value(self.request_reference)
        result["readiness_reference"] = serialize_value(self.readiness_reference)
        result["target_reference"] = serialize_value(self.target_reference)
        result["issued_at"] = serialize_value(self.issued_at)
        result["expires_at"] = serialize_value(self.expires_at)
        result["state"] = serialize_value(self.state)
        if self.revocation_metadata is not ABSENT:
            result["revocation_metadata"] = serialize_value(self.revocation_metadata)
        if self.use_binding is not ABSENT:
            result["use_binding"] = serialize_value(self.use_binding)
        result["replay_binding"] = self.replay_binding
        result["risk_acknowledgement"] = self.risk_acknowledgement
        if self.proof_reference is not ABSENT:
            result["proof_reference"] = serialize_value(self.proof_reference)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        return result


# ---------------------------------------------------------------------------
# CutoverCandidate
# ---------------------------------------------------------------------------

_CUTOVER_CANDIDATE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/cutover_candidate.schema.json"
)
_CUTOVER_CANDIDATE_RECORD_TYPE = "cutover_candidate"
_CUTOVER_CANDIDATE_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_CUTOVER_CANDIDATE_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "stage2_generation_reference",
        "cas_expectation",
        "state",
        "limitations",
        "authority_disclosure",
        "_extensions",
    }
)

_CUTOVER_CANDIDATE_RESERVED_FIELD_NAMES = frozenset(_CUTOVER_CANDIDATE_KNOWN_KEYS - {"_extensions"})


@dataclasses.dataclass(frozen=True)
class CutoverCandidate:
    """Shape-only wire contract for a ``CutoverCandidate`` companion record
    (``records/cutover_candidate.schema.json``, contract Sec.22). A
    ``CutoverCandidate`` document proposes a specific, bounded cutover
    attempt; it never itself proves eligibility, human authorization,
    certification, CAS success, publication success, cutover completion, or
    current authority (Sec.1, Sec.40). Tier 2 (``_extensions`` only,
    Sec.14).

    This model does not: calculate eligibility, verify authorization,
    certify anything, enforce CAS, resolve stage2_generation_reference,
    persist anything, or execute cutover. A field that says 'certified'
    remains descriptive data only.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    stage2_generation_reference: RecordReference
    cas_expectation: CasExpectation
    state: CandidateState
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    _extensions: ExtensionMapping | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _CUTOVER_CANDIDATE_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"CutoverCandidate.envelope.record_type must be "
                f"{_CUTOVER_CANDIDATE_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _CUTOVER_CANDIDATE_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"CutoverCandidate.envelope.schema_id must be the frozen "
                f"const {_CUTOVER_CANDIDATE_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family, at every state including 'certified' (Sec.9's
        # 12-file list, Sec.22).
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "CutoverCandidate.authority_disclosure.authority_role must "
                "not be 'authoritative': a candidate is never itself a "
                "resolved live-authority claim, even when state is "
                "'certified'"
            )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "CutoverCandidate":
        if schema_version not in _CUTOVER_CANDIDATE_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"CutoverCandidate does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "CutoverCandidate")
        _reject_unknown_keys(payload, _CUTOVER_CANDIDATE_KNOWN_KEYS, "CutoverCandidate")

        envelope = _envelope_from_payload(
            payload, record_type=_CUTOVER_CANDIDATE_RECORD_TYPE, schema_id=_CUTOVER_CANDIDATE_SCHEMA_ID
        )

        for required_key in (
            "migration_epoch",
            "stage2_generation_reference",
            "cas_expectation",
            "state",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"CutoverCandidate: missing required field {required_key!r}"
                )

        raw_extensions = field_from_payload(payload, "_extensions")
        parsed_extensions: ExtensionMapping | AbsentType
        if raw_extensions is ABSENT:
            parsed_extensions = ABSENT
        elif raw_extensions is None:
            raise TypedModelConstructionError(
                "CutoverCandidate._extensions does not permit explicit null"
            )
        else:
            extensions_payload = _require_mapping(raw_extensions, "CutoverCandidate._extensions")
            for extension_value in extensions_payload.values():
                if not isinstance(extension_value, str):
                    raise TypedModelConstructionError(
                        "CutoverCandidate._extensions values must be strings "
                        "only (Sec.14 Tier 2 string-valued map), got "
                        f"{type(extension_value)!r}"
                    )
            parsed_extensions = ExtensionMapping.from_mapping(
                extensions_payload,
                reserved_keys=_CUTOVER_CANDIDATE_RESERVED_FIELD_NAMES,
            )

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "CutoverCandidate.migration_epoch")
            ),
            stage2_generation_reference=_record_reference_from_dict(
                payload["stage2_generation_reference"],
                required_family=None,
                owner="CutoverCandidate.stage2_generation_reference",
            ),
            cas_expectation=_cas_expectation_from_dict(
                payload["cas_expectation"], owner="CutoverCandidate.cas_expectation"
            ),
            state=CandidateState(_require_str(payload["state"], "CutoverCandidate.state")),
            limitations=_limitations_from_list(
                payload["limitations"], owner="CutoverCandidate.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="CutoverCandidate.authority_disclosure"
            ),
            _extensions=parsed_extensions,
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["stage2_generation_reference"] = serialize_value(self.stage2_generation_reference)
        result["cas_expectation"] = serialize_value(self.cas_expectation)
        result["state"] = serialize_value(self.state)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        if self._extensions is not ABSENT:
            result["_extensions"] = self._extensions.to_dict()
        return result


# ---------------------------------------------------------------------------
# Certification
# ---------------------------------------------------------------------------

_CERTIFICATION_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/certification.schema.json"
_CERTIFICATION_RECORD_TYPE = "certification"
_CERTIFICATION_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})
_VERIFIER_EVIDENCE_MAX_ITEMS = 64

_CERTIFICATION_KNOWN_KEYS = frozenset(
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
        "candidate_reference",
        "request_reference",
        "readiness_reference",
        "authorization_reference",
        "source_authority_reference",
        "target_epoch_reference",
        "cas_expectation",
        "verifier_evidence",
        "state",
        "staleness",
        "invalidation",
        "limitations",
        "authority_disclosure",
    }
)

_STALENESS_KNOWN_KEYS = frozenset({"detected_at", "reason_code"})
_INVALIDATION_KNOWN_KEYS = frozenset({"invalidated_at", "reason_code"})


def _staleness_from_dict(value: Mapping[str, Any], *, owner: str) -> Staleness:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _STALENESS_KNOWN_KEYS, owner)
    for required_key in ("detected_at", "reason_code"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    return Staleness(
        detected_at=Timestamp(_require_str(payload["detected_at"], f"{owner}.detected_at")),
        reason_code=ReasonCode(_require_str(payload["reason_code"], f"{owner}.reason_code")),
    )


def _invalidation_from_dict(value: Mapping[str, Any], *, owner: str) -> Invalidation:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _INVALIDATION_KNOWN_KEYS, owner)
    for required_key in ("invalidated_at", "reason_code"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    return Invalidation(
        invalidated_at=Timestamp(_require_str(payload["invalidated_at"], f"{owner}.invalidated_at")),
        reason_code=ReasonCode(_require_str(payload["reason_code"], f"{owner}.reason_code")),
    )


@dataclasses.dataclass(frozen=True)
class Certification:
    """Shape-only wire contract for a ``Certification`` companion record
    (``records/certification.schema.json``, contract Sec.23). A
    ``Certification`` document is evidence-based verification of a specific
    ``CutoverCandidate``; it never itself proves certification authenticity,
    publishes authority, activates cutover, or establishes current
    authority (Sec.1, Sec.40). Tier 1 (strict): no ``_extensions`` escape
    hatch exists on this family. Deliberately carries no named
    certifier-principal field (unlike ``HumanAuthorization.principal``):
    certification is evidence-based verification (``verifier_evidence``, an
    array of record_reference) rather than a single named human decision.

    This model does not: verify evidence, evaluate a candidate's
    eligibility, authenticate a certifier, determine certification
    authenticity, enforce CAS, resolve any referenced record, publish
    authority, or activate cutover. A 'certified' state here remains a
    disclosure only.
    """

    envelope: RecordEnvelope
    phase_id: PhaseIdentity
    migration_epoch: MigrationEpochToken
    candidate_reference: RecordReference
    request_reference: RecordReference
    readiness_reference: RecordReference
    authorization_reference: RecordReference
    source_authority_reference: RecordReference
    target_epoch_reference: RecordReference
    cas_expectation: CasExpectation
    verifier_evidence: Tuple[RecordReference, ...]
    state: CertificationState
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    staleness: Staleness | AbsentType = ABSENT
    invalidation: Invalidation | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _CERTIFICATION_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"Certification.envelope.record_type must be "
                f"{_CERTIFICATION_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _CERTIFICATION_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"Certification.envelope.schema_id must be the frozen const "
                f"{_CERTIFICATION_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "Certification.authority_disclosure.authority_role must not "
                "be 'authoritative': a certification record never itself "
                "publishes or activates authority"
            )
        require_family(self.candidate_reference, RecordFamily.CUTOVER_CANDIDATE)
        require_family(self.request_reference, RecordFamily.CUTOVER_REQUEST)
        require_family(self.readiness_reference, RecordFamily.READINESS_PACKAGE)
        require_family(self.authorization_reference, RecordFamily.HUMAN_AUTHORIZATION)
        require_family(self.source_authority_reference, RecordFamily.AUTHORITY_EPOCH)
        require_family(self.target_epoch_reference, RecordFamily.AUTHORITY_EPOCH)
        verifier_evidence = tuple(self.verifier_evidence)
        if len(verifier_evidence) > _VERIFIER_EVIDENCE_MAX_ITEMS:
            raise TypedModelInternalInvariantError(
                f"Certification.verifier_evidence has {len(verifier_evidence)} "
                f"entries, exceeding the maximum of {_VERIFIER_EVIDENCE_MAX_ITEMS}"
            )
        object.__setattr__(self, "verifier_evidence", verifier_evidence)
        # state <-> staleness conditional.
        if self.state is CertificationState.STALE and self.staleness is ABSENT:
            raise TypedModelInternalInvariantError(
                "Certification.staleness is required when state is 'stale'"
            )
        if self.state is not CertificationState.STALE and self.staleness is not ABSENT:
            raise TypedModelInternalInvariantError(
                "Certification.staleness is forbidden unless state is 'stale'"
            )
        # state <-> invalidation conditional.
        if self.state is CertificationState.INVALIDATED and self.invalidation is ABSENT:
            raise TypedModelInternalInvariantError(
                "Certification.invalidation is required when state is "
                "'invalidated'"
            )
        if self.state is not CertificationState.INVALIDATED and self.invalidation is not ABSENT:
            raise TypedModelInternalInvariantError(
                "Certification.invalidation is forbidden unless state is "
                "'invalidated'"
            )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "Certification":
        if schema_version not in _CERTIFICATION_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"Certification does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "Certification")
        _reject_unknown_keys(payload, _CERTIFICATION_KNOWN_KEYS, "Certification")

        envelope = _envelope_from_payload(
            payload, record_type=_CERTIFICATION_RECORD_TYPE, schema_id=_CERTIFICATION_SCHEMA_ID
        )

        for required_key in (
            "phase_id",
            "migration_epoch",
            "candidate_reference",
            "request_reference",
            "readiness_reference",
            "authorization_reference",
            "source_authority_reference",
            "target_epoch_reference",
            "cas_expectation",
            "verifier_evidence",
            "state",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"Certification: missing required field {required_key!r}"
                )

        candidate_reference_raw = _require_mapping(
            payload["candidate_reference"], "Certification.candidate_reference"
        )
        _require_cross_family_reference_fields(
            candidate_reference_raw, owner="Certification.candidate_reference"
        )
        request_reference_raw = _require_mapping(
            payload["request_reference"], "Certification.request_reference"
        )
        _require_cross_family_reference_fields(
            request_reference_raw, owner="Certification.request_reference"
        )
        readiness_reference_raw = _require_mapping(
            payload["readiness_reference"], "Certification.readiness_reference"
        )
        _require_cross_family_reference_fields(
            readiness_reference_raw, owner="Certification.readiness_reference"
        )
        authorization_reference_raw = _require_mapping(
            payload["authorization_reference"], "Certification.authorization_reference"
        )
        _require_cross_family_reference_fields(
            authorization_reference_raw, owner="Certification.authorization_reference"
        )

        raw_verifier_evidence = payload["verifier_evidence"]
        if not isinstance(raw_verifier_evidence, list):
            raise TypedModelConstructionError("Certification.verifier_evidence must be a JSON array")
        verifier_evidence = tuple(
            _record_reference_from_dict(
                entry, required_family=None, owner="Certification.verifier_evidence[]"
            )
            for entry in raw_verifier_evidence
        )

        raw_staleness = field_from_payload(payload, "staleness")
        staleness: Staleness | AbsentType
        if raw_staleness is ABSENT:
            staleness = ABSENT
        else:
            staleness = _staleness_from_dict(raw_staleness, owner="Certification.staleness")

        raw_invalidation = field_from_payload(payload, "invalidation")
        invalidation: Invalidation | AbsentType
        if raw_invalidation is ABSENT:
            invalidation = ABSENT
        else:
            invalidation = _invalidation_from_dict(raw_invalidation, owner="Certification.invalidation")

        return cls(
            envelope=envelope,
            phase_id=PhaseIdentity(_require_str(payload["phase_id"], "Certification.phase_id")),
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "Certification.migration_epoch")
            ),
            candidate_reference=_record_reference_from_dict(
                candidate_reference_raw,
                required_family=RecordFamily.CUTOVER_CANDIDATE,
                owner="Certification.candidate_reference",
            ),
            request_reference=_record_reference_from_dict(
                request_reference_raw,
                required_family=RecordFamily.CUTOVER_REQUEST,
                owner="Certification.request_reference",
            ),
            readiness_reference=_record_reference_from_dict(
                readiness_reference_raw,
                required_family=RecordFamily.READINESS_PACKAGE,
                owner="Certification.readiness_reference",
            ),
            authorization_reference=_record_reference_from_dict(
                authorization_reference_raw,
                required_family=RecordFamily.HUMAN_AUTHORIZATION,
                owner="Certification.authorization_reference",
            ),
            source_authority_reference=_record_reference_from_dict(
                payload["source_authority_reference"],
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="Certification.source_authority_reference",
            ),
            target_epoch_reference=_record_reference_from_dict(
                payload["target_epoch_reference"],
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="Certification.target_epoch_reference",
            ),
            cas_expectation=_cas_expectation_from_dict(
                payload["cas_expectation"], owner="Certification.cas_expectation"
            ),
            verifier_evidence=verifier_evidence,
            state=CertificationState(_require_str(payload["state"], "Certification.state")),
            staleness=staleness,
            invalidation=invalidation,
            limitations=_limitations_from_list(
                payload["limitations"], owner="Certification.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="Certification.authority_disclosure"
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["phase_id"] = serialize_value(self.phase_id)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["candidate_reference"] = serialize_value(self.candidate_reference)
        result["request_reference"] = serialize_value(self.request_reference)
        result["readiness_reference"] = serialize_value(self.readiness_reference)
        result["authorization_reference"] = serialize_value(self.authorization_reference)
        result["source_authority_reference"] = serialize_value(self.source_authority_reference)
        result["target_epoch_reference"] = serialize_value(self.target_epoch_reference)
        result["cas_expectation"] = serialize_value(self.cas_expectation)
        result["verifier_evidence"] = [serialize_value(v) for v in self.verifier_evidence]
        result["state"] = serialize_value(self.state)
        if self.staleness is not ABSENT:
            result["staleness"] = serialize_value(self.staleness)
        if self.invalidation is not ABSENT:
            result["invalidation"] = serialize_value(self.invalidation)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        return result


__all__ = [
    "AuthorizationMethod",
    "AuthorizationState",
    "CandidateState",
    "CertificationState",
    "RevocationMetadata",
    "Staleness",
    "Invalidation",
    "HumanAuthorization",
    "CutoverCandidate",
    "Certification",
]
