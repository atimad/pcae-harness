"""Shared wire-enum vocabularies (136Y plan Sec.12; schema source:
``shared/enums.schema.json``, ``shared/failures.schema.json``).

Every enum below is a Python ``Enum`` (``str`` mixin) with exact wire-value
members only. Construction is ``EnumClass(raw_str)``: exact ``ValueError``
on any mismatch, including case mismatch -- no ``.lower()``/``.upper()``
normalization, no permissive "unknown/other" fallback member, matching the
contract's fail-closed rule without exception.

These are wire vocabularies only: no member carries lifecycle-transition
legality, authority truth, or a boolean "is this authoritative" meaning.
Transition-legality (e.g. ``AuthorityKind``'s "legacy -> cltr once-only"
rule) is a Layer 4/5 cross-record concern, never enforced here.

The 14 family-local enums (``RequestState``, ``ReadinessState``, etc.) are
deliberately NOT centralized here, matching the schema layer's own
non-centralization choice -- each remains scoped to its own owning
record-family module, implemented in a future group.
"""

from __future__ import annotations

import enum


class AuthorityKind(str, enum.Enum):
    """Sec.8.1, 2 values."""

    LEGACY = "legacy"
    CLTR = "cltr"


class AuthorityRole(str, enum.Enum):
    """Sec.8.2, the Stage-3 companion 7-value vocabulary. Shares zero code
    points with ``pcae.cltr.enums.AuthorityRole``'s legacy 5-code
    (S/R/D/E/V) vocabulary -- the two are distinct types in distinct
    modules and must never be conflated or substituted for one another."""

    AUTHORITATIVE = "authoritative"
    DERIVATIVE = "derivative"
    OPERATIONAL = "operational"
    EVIDENCE = "evidence"
    COMPATIBILITY = "compatibility"
    HISTORICAL = "historical"
    QUARANTINED = "quarantined"


class MigrationStage(str, enum.Enum):
    """Sec.8.3, the Stage-3 typed 11-value migration stage. Distinct from
    ``pcae.cltr.migration.enums``'s existing 6-value ``MigrationStage``."""

    SHADOW = "shadow"
    DUAL_DERIVATION = "dual_derivation"
    ATOMIC_REHEARSAL = "atomic_rehearsal"
    ROLLBACK_REHEARSAL = "rollback_rehearsal"
    CUTOVER_READINESS = "cutover_readiness"
    CUTOVER_CANDIDATE = "cutover_candidate"
    CERTIFIED = "certified"
    PUBLICATION_PENDING = "publication_pending"
    CLTR_AUTHORITATIVE = "cltr_authoritative"
    LEGACY_COMPATIBILITY = "legacy_compatibility"
    LEGACY_RETIRED = "legacy_retired"


class GenerationRole(str, enum.Enum):
    """Sec.8.4, 8 values."""

    REHEARSAL_CANDIDATE = "rehearsal_candidate"
    REHEARSAL_GENERATION = "rehearsal_generation"
    CUTOVER_CANDIDATE = "cutover_candidate"
    CERTIFIED_GENERATION = "certified_generation"
    AUTHORITATIVE_GENERATION = "authoritative_generation"
    HISTORICAL_GENERATION = "historical_generation"
    SUPERSEDED_GENERATION = "superseded_generation"
    QUARANTINED_GENERATION = "quarantined_generation"


class PublicationState(str, enum.Enum):
    """Sec.8.5, 12 values."""

    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    GATE_REJECTED = "gate_rejected"
    GATE_UNCERTAIN = "gate_uncertain"
    CERTIFIED = "certified"
    PUBLICATION_PREPARED = "publication_prepared"
    PUBLICATION_ATTEMPTED = "publication_attempted"
    PUBLICATION_UNCERTAIN = "publication_uncertain"
    PUBLISHED = "published"
    VERIFIED = "verified"
    CONFLICT = "conflict"
    QUARANTINED = "quarantined"


class RecoveryState(str, enum.Enum):
    """Sec.8.6, the Stage-3 typed 10-value recovery state -- a distinct
    type from both ``pcae.cltr.enums.RecoveryClassification`` (4 values)
    and ``pcae.cltr.migration.rehearsal.enums.RecoveryState`` (Stage 2,
    11 values). All three are real and simultaneously valid in this
    codebase; no code substitutes one for another."""

    NONE_REQUIRED = "none_required"
    RESUME_SAFE = "resume_safe"
    RETRY_REQUIRED = "retry_required"
    OPERATOR_REVIEW_REQUIRED = "operator_review_required"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    QUARANTINE_REQUIRED = "quarantine_required"
    CONFLICT_UNRESOLVED = "conflict_unresolved"
    PUBLICATION_UNCERTAIN_UNRESOLVED = "publication_uncertain_unresolved"
    TERMINAL_RECOVERED = "terminal_recovered"
    TERMINAL_UNRECOVERABLE = "terminal_unrecoverable"


class CompatibilityMode(str, enum.Enum):
    """Sec.8.7, 6 values. Forward-only documented ordering (advisory only,
    never enforced by this type): legacy_authoritative -> legacy_adapter ->
    legacy_read_only -> legacy_historical -> legacy_disabled ->
    legacy_retired."""

    LEGACY_AUTHORITATIVE = "legacy_authoritative"
    LEGACY_ADAPTER = "legacy_adapter"
    LEGACY_READ_ONLY = "legacy_read_only"
    LEGACY_HISTORICAL = "legacy_historical"
    LEGACY_DISABLED = "legacy_disabled"
    LEGACY_RETIRED = "legacy_retired"


class RecordFamily(str, enum.Enum):
    """Closed nomenclature for the ``record_family`` tag on
    ``shared/references.schema.json#/$defs/record_reference``. Exactly the
    16 standalone companion family slugs. Naming a family here does not
    create, instantiate, or authorize its schema file or model class."""

    AUTHORITY_EPOCH = "authority_epoch"
    AUTHORITY_STATE = "authority_state"
    CUTOVER_REQUEST = "cutover_request"
    READINESS_PACKAGE = "readiness_package"
    HUMAN_AUTHORIZATION = "human_authorization"
    CUTOVER_CANDIDATE = "cutover_candidate"
    CERTIFICATION = "certification"
    PUBLICATION_ATTEMPT = "publication_attempt"
    PUBLICATION_EVIDENCE = "publication_evidence"
    CONCURRENCY_CONFLICT = "concurrency_conflict"
    RECOVERY_JOURNAL_ENTRY = "recovery_journal_entry"
    QUARANTINE_RECORD = "quarantine_record"
    NOTIFICATION_AUTHORITY_BINDING = "notification_authority_binding"
    MARKER_AUTHORITY_BINDING = "marker_authority_binding"
    RECEIPT_AUTHORITY_BINDING = "receipt_authority_binding"
    COMPATIBILITY_STATE = "compatibility_state"


class ReasonCode(str, enum.Enum):
    """The shared, closed 24-value ``reason_code`` vocabulary
    (``shared/failures.schema.json``). Informational only: a reason code
    never itself establishes authority, and this type does not verify that
    a code was correctly assigned for the failure that actually occurred
    (Layer 4)."""

    INVALID_SCHEMA = "invalid_schema"
    UNSUPPORTED_VERSION = "unsupported_version"
    IDENTITY_MISMATCH = "identity_mismatch"
    PHASE_MISMATCH = "phase_mismatch"
    TRANSITION_MISMATCH = "transition_mismatch"
    MIGRATION_EPOCH_MISMATCH = "migration_epoch_mismatch"
    AUTHORITY_EPOCH_MISMATCH = "authority_epoch_mismatch"
    REVISION_MISMATCH = "revision_mismatch"
    DIGEST_MISMATCH = "digest_mismatch"
    STALE_AUTHORIZATION = "stale_authorization"
    STALE_CERTIFICATION = "stale_certification"
    STALE_WRITER = "stale_writer"
    CAS_REJECTED = "cas_rejected"
    PUBLICATION_UNCERTAIN = "publication_uncertain"
    CONCURRENCY_CONFLICT = "concurrency_conflict"
    QUARANTINE_REQUIRED = "quarantine_required"
    RECOVERY_REQUIRED = "recovery_required"
    AUTHORITY_AMBIGUOUS = "authority_ambiguous"
    AUTHORITY_MISSING = "authority_missing"
    WRONG_GENERATION = "wrong_generation"
    INCOMPATIBLE_LEGACY_STATE = "incompatible_legacy_state"
    NOTIFICATION_UNCERTAIN = "notification_uncertain"
    MARKER_CONFLICT = "marker_conflict"
    RECEIPT_CONFLICT = "receipt_conflict"


class LegacyLifecycleStateWire(str, enum.Enum):
    """Restates, by wire value only, the 12-value legacy ``LifecycleState``
    enum already implemented at ``pcae.cltr.enums`` -- this type does not
    import or depend on that Python enum; it independently re-declares the
    same closed vocabulary as plain wire-string values. Used by the
    embedded ``CasExpectation`` component's
    ``expected_source_lifecycle_state`` field."""

    PROPOSED = "PROPOSED"
    CERTIFYING = "CERTIFYING"
    CERTIFIED = "CERTIFIED"
    PROMOTING = "PROMOTING"
    PROMOTED = "PROMOTED"
    NOTIFYING = "NOTIFYING"
    NOTIFIED = "NOTIFIED"
    NOTIFIED_UNCONFIRMED = "NOTIFIED_UNCONFIRMED"
    TERMINAL_SUCCESS = "TERMINAL_SUCCESS"
    TERMINAL_PARTIAL_EXTERNAL = "TERMINAL_PARTIAL_EXTERNAL"
    FAILED_PRE_CERT = "FAILED_PRE_CERT"
    FAILED_POST_CERT = "FAILED_POST_CERT"


class JournalLockState(str, enum.Enum):
    """The embedded ``CasExpectation`` component's
    ``expected_journal_lock_state`` 2-value local vocabulary."""

    UNLOCKED = "unlocked"
    LOCKED = "locked"


__all__ = [
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
]
