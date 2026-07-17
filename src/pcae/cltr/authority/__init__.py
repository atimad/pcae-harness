"""Stage 3 Typed Authority Model shared core and record-family models
(Phase 136Z shared core; Phase 136AB Typed Model Implementation Group 2:
``AuthorityEpoch``, ``AuthorityState``; Phase 136AD Typed Model
Implementation Group 3: ``CutoverRequest``, ``ReadinessPackage``; Phase
136AF Typed Model Implementation Group 4: ``HumanAuthorization``,
``CutoverCandidate``, ``Certification``).

Provides lossless, immutable, offline, schema-aligned primitives shared by
every typed-authority record model, plus the seven Group 2/3/4
record-family models. No other record-family model (``PublicationAttempt``,
``PublicationEvidence``, ``ConcurrencyConflict``, ``RecoveryJournalEntry``,
``NotificationAuthorityBinding``, ``MarkerAuthorityBinding``,
``FinalizationReceiptAuthorityBinding``, ``CompatibilityState``,
``QuarantineRecord``) is implemented here; those belong to future,
separately governed implementation groups.

This package is sibling to, not merged into, the existing
``pcae.cltr`` flat module list (``digest.py``, ``canonicalization.py``,
``enums.py``, ``models.py``). No production runtime module (lifecycle,
finalization, notification dispatch, marker creation, receipt creation,
publication, recovery, authority selection, execution coordinator,
permission broker, runtime decision engine) may import this package.

Every construction/serialization primitive here is pure: no filesystem
reads beyond normal Python imports, no filesystem writes, no network
access, no environment-variable lookup, no subprocess execution. No
symbol in this package resolves, selects, or mutates authority.
"""

from __future__ import annotations

from pcae.cltr.authority.authority_core import (
    ActivationState,
    AuthorityEpoch,
    AuthorityState,
    Uncertainty,
    VerificationState,
)
from pcae.cltr.authority.request_readiness import (
    CutoverRequest,
    Finding,
    FindingVerdict,
    GateResult,
    PrerequisiteStatus,
    ReadinessPackage,
    ReadinessState,
    RequestState,
)
from pcae.cltr.authority.authorization_candidate import (
    AuthorizationMethod,
    AuthorizationState,
    CandidateState,
    Certification,
    CertificationState,
    CutoverCandidate,
    HumanAuthorization,
    Invalidation,
    RevocationMetadata,
    Staleness,
)
from pcae.cltr.authority.cas_expectation import CasExpectation
from pcae.cltr.authority.digest import (
    GenerationDigest,
    JournalEntryDigest,
    PointerDigest,
    RecordDigest,
    ReferencedRecordDigest,
    Sha256Digest,
)
from pcae.cltr.authority.enums import (
    AuthorityKind,
    AuthorityRole,
    CompatibilityMode,
    GenerationRole,
    JournalLockState,
    LegacyLifecycleStateWire,
    MigrationStage,
    PublicationState,
    ReasonCode,
    RecordFamily,
    RecoveryState,
)
from pcae.cltr.authority.envelope import RecordEnvelope, SchemaVersionString, Timestamp
from pcae.cltr.authority.extensions import ExtensionMapping
from pcae.cltr.authority.identity import (
    GenerationId,
    MigrationEpochToken,
    PhaseIdentity,
    PrincipalIdentifier,
    RecordId,
    TransitionId,
)
from pcae.cltr.authority.limitations import AuthorityDisclosure, Limitations
from pcae.cltr.authority.opaque import OpaqueJsonValue, verify_round_trip
from pcae.cltr.authority.references import (
    EpochReference,
    GenerationReference,
    RecordReference,
    require_family,
)
from pcae.cltr.authority.sentinels import ABSENT, AbsentType
from pcae.cltr.authority.serialization import (
    field_from_payload,
    serialize_value,
    to_canonical_bytes,
    to_dict_fields,
)
from pcae.cltr.authority.errors import (
    AbsentNullMismatchError,
    InvalidDigestError,
    InvalidIdentifierError,
    InvalidReferenceError,
    InvalidTimestampError,
    OpaqueValuePreservationError,
    RoundTripMismatchError,
    SerializationError,
    TypedModelConstructionError,
    TypedModelError,
    TypedModelInternalInvariantError,
    UnknownModelFamilyError,
    UnsupportedJsonValueError,
    UnsupportedSchemaVersionError,
    WrongFamilyReferenceError,
)

__all__ = [
    # Group 2 record-family models (Phase 136AB)
    "AuthorityEpoch",
    "AuthorityState",
    "ActivationState",
    "VerificationState",
    "Uncertainty",
    # Group 3 record-family models (Phase 136AD)
    "CutoverRequest",
    "ReadinessPackage",
    "RequestState",
    "ReadinessState",
    "PrerequisiteStatus",
    "GateResult",
    "FindingVerdict",
    "Finding",
    # Group 4 record-family models (Phase 136AF)
    "HumanAuthorization",
    "CutoverCandidate",
    "Certification",
    "AuthorizationMethod",
    "AuthorizationState",
    "CandidateState",
    "CertificationState",
    "RevocationMetadata",
    "Staleness",
    "Invalidation",
    # Sentinel
    "ABSENT",
    "AbsentType",
    # Opaque / extensions
    "OpaqueJsonValue",
    "verify_round_trip",
    "ExtensionMapping",
    # Enums
    "AuthorityKind",
    "AuthorityRole",
    "MigrationStage",
    "GenerationRole",
    "PublicationState",
    "RecoveryState",
    "CompatibilityMode",
    "RecordFamily",
    "ReasonCode",
    "LegacyLifecycleStateWire",
    "JournalLockState",
    # Identity
    "RecordId",
    "GenerationId",
    "MigrationEpochToken",
    "PhaseIdentity",
    "TransitionId",
    "PrincipalIdentifier",
    # Digest
    "Sha256Digest",
    "RecordDigest",
    "ReferencedRecordDigest",
    "GenerationDigest",
    "PointerDigest",
    "JournalEntryDigest",
    # References
    "RecordReference",
    "EpochReference",
    "GenerationReference",
    "require_family",
    # Cas expectation
    "CasExpectation",
    # Limitations / authority disclosure
    "Limitations",
    "AuthorityDisclosure",
    # Envelope
    "Timestamp",
    "SchemaVersionString",
    "RecordEnvelope",
    # Serialization
    "field_from_payload",
    "serialize_value",
    "to_dict_fields",
    "to_canonical_bytes",
    # Errors
    "TypedModelError",
    "TypedModelConstructionError",
    "InvalidIdentifierError",
    "InvalidDigestError",
    "InvalidReferenceError",
    "WrongFamilyReferenceError",
    "InvalidTimestampError",
    "UnsupportedJsonValueError",
    "AbsentNullMismatchError",
    "UnsupportedSchemaVersionError",
    "UnknownModelFamilyError",
    "OpaqueValuePreservationError",
    "SerializationError",
    "TypedModelInternalInvariantError",
    "RoundTripMismatchError",
]
