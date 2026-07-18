"""Phase 136AJ: Stage 3 Typed Authority Model Recovery and Concurrency
Implementation (Typed Model Implementation Group 6, per the 136Y plan
Sec.4/Sec.27-28, package layout Sec.7).

Implements exactly two record-family models: ``ConcurrencyConflict`` and
``RecoveryJournalEntry``, schema-backed by
``records/concurrency_conflict.schema.json`` and
``records/recovery_journal_entry.schema.json`` respectively.

A constructed instance of either model asserts only "this JSON was
well-formed against schema X at version Y and can be represented without
loss" -- never operational truth. Neither model detects a live
concurrency conflict, compares current and expected authority state,
executes compare-and-swap, acquires a lock, retries publication, performs
recovery, resumes execution, replays a lifecycle operation, mutates a
record, repairs authority state, selects a recovery action, persists a
journal entry, resolves a reference, verifies evidence, inspects
repository or runtime state, activates CLTR authority, or demotes/retires
legacy authority. A ``ConcurrencyConflict`` is a representation of an
already-declared conflict, never a discovery of one; a
``RecoveryJournalEntry`` is a representation of a declared historical or
intended recovery record, never a plan for or execution of recovery.
Legacy lifecycle remains the sole production authority; CLTR remains
derivative.

No other record-family model (``NotificationAuthorityBinding``,
``MarkerAuthorityBinding``, ``FinalizationReceiptAuthorityBinding``,
``CompatibilityState``, ``QuarantineRecord``) is implemented here; those
belong to future, separately governed implementation groups. Forward
references to those not-yet-implemented families are shape-only,
family-tagged pointers and do not require the referenced family's own
model class to exist.

Tier boundary: both ``ConcurrencyConflict`` and ``RecoveryJournalEntry``
are Tier 2 (``_extensions`` permitted, string-valued map only).
"""

from __future__ import annotations

import dataclasses
import enum
import re
from collections.abc import Mapping
from typing import Any, Tuple, Union

from pcae.cltr.authority.digest import (
    GenerationDigest,
    JournalEntryDigest,
    RecordDigest,
    ReferencedRecordDigest,
)
from pcae.cltr.authority.enums import AuthorityRole, RecordFamily, RecoveryState
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
    PrincipalIdentifier,
    RecordId,
    TransitionId,
)
from pcae.cltr.authority.limitations import AuthorityDisclosure, Limitations
from pcae.cltr.authority.references import GenerationReference, RecordReference, require_family
from pcae.cltr.authority.sentinels import ABSENT, AbsentType
from pcae.cltr.authority.serialization import field_from_payload, serialize_value, to_dict_fields

# ---------------------------------------------------------------------------
# Record-local enums (family-scoped, not part of the shared cross-family
# enums in enums.py -- matching the schema layer's own non-centralization
# choice, same precedent as authority_core.py / request_readiness.py /
# authorization_candidate.py / publication.py).
# ---------------------------------------------------------------------------


class ConflictType(str, enum.Enum):
    """``ConcurrencyConflict``'s record-local ``type`` field (Sec.8.8, 4
    values, home schema ``concurrency_conflict.schema.json``).
    'cas_mismatch' requires ``expected_state`` and ``observed_state``
    (enforced below); a schema-valid value here never itself proves the
    conflict was correctly classified (Layer 4)."""

    CAS_MISMATCH = "cas_mismatch"
    DUAL_WRITER = "dual_writer"
    STALE_EXPECTATION = "stale_expectation"
    UNKNOWN_WINNER = "unknown_winner"


class ExternalEffectState(str, enum.Enum):
    """``RecoveryJournalEntry``'s record-local ``external_effect_state``
    field (Sec.28, 4 values). A schema-valid value here never itself
    proves the described external effect actually occurred (Layer 4/5)."""

    NONE = "none"
    PENDING = "pending"
    APPLIED = "applied"
    UNKNOWN = "unknown"


class RetryReplayClassification(str, enum.Enum):
    """``RecoveryJournalEntry``'s record-local
    ``retry_replay_classification`` field (Sec.28, 3 values). A
    schema-valid value here never itself authorizes a retry or proves
    replay safety (Layer 4/6)."""

    ORIGINAL = "original"
    RETRY = "retry"
    REPLAY = "replay"


class JournalState(str, enum.Enum):
    """``RecoveryJournalEntry``'s record-local ``state`` field (Sec.8.8, 4
    values, home schema ``recovery_journal_entry.schema.json``).
    'reviewed', 'actioned', and 'superseded' each require
    ``operator_review``; 'actioned' additionally requires
    ``recovery_action`` (both enforced below)."""

    RECORDED = "recorded"
    REVIEWED = "reviewed"
    ACTIONED = "actioned"
    SUPERSEDED = "superseded"


_JOURNAL_STATES_REQUIRING_OPERATOR_REVIEW = frozenset(
    {JournalState.REVIEWED, JournalState.ACTIONED, JournalState.SUPERSEDED}
)


# ---------------------------------------------------------------------------
# Nested value objects
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class OperatorReview:
    """``RecoveryJournalEntry``'s bounded local ``operator_review``
    disclosure object (mirrors ``publication.py``'s own uncertainty
    ``$def`` pattern; Sec.28 requires only that this be "an object"
    without naming sub-fields, NON-BLOCKING-136R-1). Present only when
    ``state`` is 'reviewed', 'actioned', or 'superseded'. A disclosure
    only -- never itself a review action."""

    notes: str

    def __post_init__(self) -> None:
        _validate_disclosure_text(self.notes, "OperatorReview.notes")


@dataclasses.dataclass(frozen=True)
class RecoveryAction:
    """``RecoveryJournalEntry``'s bounded local ``recovery_action``
    disclosure object (NON-BLOCKING-136R-1, same minimal-shape precedent
    as ``OperatorReview``). Present only when ``state`` is 'actioned'.
    Describing an action here never itself executes it (Sec.1, Sec.40)."""

    description: str

    def __post_init__(self) -> None:
        _validate_disclosure_text(self.description, "RecoveryAction.description")


# ---------------------------------------------------------------------------
# Shared field-extraction helpers (Layer 3 construction pipeline, 136Y plan
# Sec.16). Deliberately self-contained within this module rather than
# importing another group module's private helpers -- each group module
# owns its own Layer 3 construction boilerplate, matching authority_core.py,
# request_readiness.py, authorization_candidate.py, and publication.py's
# own precedent-setting structure.
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

# 136AJ independent re-derivation (reproduced against the live schema, not
# copied from an earlier group's own field table) -- see publication.py's
# identical comment for the same rationale.
_RECORD_REFERENCE_SCHEMA_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")


def _record_reference_schema_id_from_payload(payload: Mapping[str, Any], *, owner: str) -> str | AbsentType:
    raw = field_from_payload(payload, "schema_id")
    if raw is ABSENT:
        return ABSENT
    if not isinstance(raw, str) or not (1 <= len(raw) <= 512):
        raise TypedModelConstructionError(
            f"{owner}.schema_id must be a non-empty string of at most 512 characters "
            f"when present, got {raw!r}"
        )
    return raw


def _record_reference_schema_version_from_payload(
    payload: Mapping[str, Any], *, owner: str
) -> str | AbsentType:
    raw = field_from_payload(payload, "schema_version")
    if raw is ABSENT:
        return ABSENT
    if not isinstance(raw, str) or not _RECORD_REFERENCE_SCHEMA_VERSION_PATTERN.fullmatch(raw):
        raise TypedModelConstructionError(
            f"{owner}.schema_version must be a 'MAJOR.MINOR' string when present, got {raw!r}"
        )
    return raw


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
        schema_id=_record_reference_schema_id_from_payload(payload, owner=owner),
        schema_version=_record_reference_schema_version_from_payload(payload, owner=owner),
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


def _extensions_from_payload(payload: Mapping[str, Any], *, owner: str, reserved_keys: frozenset) -> (
    ExtensionMapping | AbsentType
):
    raw_extensions = field_from_payload(payload, "_extensions")
    if raw_extensions is ABSENT:
        return ABSENT
    if raw_extensions is None:
        raise TypedModelConstructionError(f"{owner}._extensions does not permit explicit null")
    extensions_payload = _require_mapping(raw_extensions, f"{owner}._extensions")
    for extension_value in extensions_payload.values():
        if not isinstance(extension_value, str):
            raise TypedModelConstructionError(
                f"{owner}._extensions values must be strings only (Sec.14 Tier 2 "
                f"string-valued map), got {type(extension_value)!r}"
            )
    return ExtensionMapping.from_mapping(extensions_payload, reserved_keys=reserved_keys)


# ---------------------------------------------------------------------------
# ConcurrencyConflict
# ---------------------------------------------------------------------------

_CONCURRENCY_CONFLICT_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/concurrency_conflict.schema.json"
)
_CONCURRENCY_CONFLICT_RECORD_TYPE = "concurrency_conflict"
_CONCURRENCY_CONFLICT_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})
_CONCURRENCY_CONFLICT_ACTORS_MIN_ITEMS = 2
_CONCURRENCY_CONFLICT_REQUESTS_MIN_ITEMS = 1

_CONCURRENCY_CONFLICT_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "actors",
        "requests",
        "expected_state",
        "observed_state",
        "type",
        "winner",
        "recovery_requirement",
        "limitations",
        "authority_disclosure",
        "_extensions",
    }
)

_CONCURRENCY_CONFLICT_RESERVED_FIELD_NAMES = frozenset(
    _CONCURRENCY_CONFLICT_KNOWN_KEYS - {"_extensions"}
)

ActorEntry = Union[PrincipalIdentifier, RecordReference]


def _actor_entry_from_payload(value: Any, *, owner: str) -> ActorEntry:
    if isinstance(value, str):
        return PrincipalIdentifier(value)
    if isinstance(value, dict):
        return _record_reference_from_dict(value, required_family=None, owner=owner)
    raise TypedModelConstructionError(
        f"{owner} must be either a principal-identifier string or a record_reference "
        f"object, got {type(value)!r}"
    )


def _actor_entry_to_wire(value: ActorEntry) -> Any:
    return serialize_value(value)


def _request_reference_from_dict(value: Mapping[str, Any], *, owner: str) -> RecordReference:
    payload = _require_mapping(value, owner)
    _require_cross_family_reference_fields(payload, owner=owner)
    return _record_reference_from_dict(payload, required_family=RecordFamily.CUTOVER_REQUEST, owner=owner)


@dataclasses.dataclass(frozen=True)
class ConcurrencyConflict:
    """Shape-only wire contract for a ``ConcurrencyConflict`` companion
    record (``records/concurrency_conflict.schema.json``, contract
    Sec.27). A ``ConcurrencyConflict`` document describes a claimed
    concurrent-writer or CAS-mismatch conflict among two or more actors
    contending over one or more ``CutoverRequest`` records; it never
    itself resolves a conflict, selects a winner, performs a
    compare-and-swap, retries publication, mutates an authority pointer,
    establishes current authority, or proves that a conflict actually
    occurred (Sec.1, Sec.40). Legacy lifecycle remains the sole production
    authority; CLTR remains derivative. Tier 2 (``_extensions`` only,
    Sec.14).

    This model does not: read current authority state, compare expected
    and actual values, detect conflicts, execute CAS, lock, retry, select
    a winner, resolve the conflict, modify publication state, or persist
    itself. A concurrency-conflict record describes an already-declared
    conflict; it does not discover one.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    actors: Tuple[ActorEntry, ...]
    requests: Tuple[RecordReference, ...]
    type: ConflictType
    winner: RecordReference | None
    recovery_requirement: RecoveryState
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    expected_state: RecordReference | AbsentType = ABSENT
    observed_state: RecordReference | AbsentType = ABSENT
    _extensions: ExtensionMapping | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _CONCURRENCY_CONFLICT_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"ConcurrencyConflict.envelope.record_type must be "
                f"{_CONCURRENCY_CONFLICT_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _CONCURRENCY_CONFLICT_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"ConcurrencyConflict.envelope.schema_id must be the frozen "
                f"const {_CONCURRENCY_CONFLICT_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family (Sec.9's 12-file list, schema description).
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "ConcurrencyConflict.authority_disclosure.authority_role must "
                "not be 'authoritative': a conflict declaration is never "
                "itself a resolved live-authority claim"
            )
        actors = tuple(self.actors)
        if len(actors) < _CONCURRENCY_CONFLICT_ACTORS_MIN_ITEMS:
            raise TypedModelInternalInvariantError(
                f"ConcurrencyConflict.actors must have at least "
                f"{_CONCURRENCY_CONFLICT_ACTORS_MIN_ITEMS} entries"
            )
        object.__setattr__(self, "actors", actors)
        requests = tuple(self.requests)
        if len(requests) < _CONCURRENCY_CONFLICT_REQUESTS_MIN_ITEMS:
            raise TypedModelInternalInvariantError(
                f"ConcurrencyConflict.requests must have at least "
                f"{_CONCURRENCY_CONFLICT_REQUESTS_MIN_ITEMS} entries"
            )
        object.__setattr__(self, "requests", requests)
        for request_reference in requests:
            require_family(request_reference, RecordFamily.CUTOVER_REQUEST)
        # type <-> expected_state/observed_state conditional (Sec.16, allOf
        # if/then/else in the executable schema).
        if self.type is ConflictType.CAS_MISMATCH:
            if self.expected_state is ABSENT:
                raise TypedModelInternalInvariantError(
                    "ConcurrencyConflict.expected_state is required when type "
                    "is 'cas_mismatch'"
                )
            if self.observed_state is ABSENT:
                raise TypedModelInternalInvariantError(
                    "ConcurrencyConflict.observed_state is required when type "
                    "is 'cas_mismatch'"
                )
        else:
            if self.expected_state is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "ConcurrencyConflict.expected_state is forbidden unless "
                    "type is 'cas_mismatch'"
                )
            if self.observed_state is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "ConcurrencyConflict.observed_state is forbidden unless "
                    "type is 'cas_mismatch'"
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "ConcurrencyConflict":
        if schema_version not in _CONCURRENCY_CONFLICT_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"ConcurrencyConflict does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "ConcurrencyConflict")
        _reject_unknown_keys(payload, _CONCURRENCY_CONFLICT_KNOWN_KEYS, "ConcurrencyConflict")

        envelope = _envelope_from_payload(
            payload,
            record_type=_CONCURRENCY_CONFLICT_RECORD_TYPE,
            schema_id=_CONCURRENCY_CONFLICT_SCHEMA_ID,
        )

        for required_key in (
            "migration_epoch",
            "actors",
            "requests",
            "type",
            "winner",
            "recovery_requirement",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"ConcurrencyConflict: missing required field {required_key!r}"
                )

        raw_actors = payload["actors"]
        if not isinstance(raw_actors, list):
            raise TypedModelConstructionError("ConcurrencyConflict.actors must be a JSON array")
        actors = tuple(
            _actor_entry_from_payload(entry, owner="ConcurrencyConflict.actors[]") for entry in raw_actors
        )

        raw_requests = payload["requests"]
        if not isinstance(raw_requests, list):
            raise TypedModelConstructionError("ConcurrencyConflict.requests must be a JSON array")
        requests = tuple(
            _request_reference_from_dict(entry, owner="ConcurrencyConflict.requests[]")
            for entry in raw_requests
        )

        raw_expected_state = field_from_payload(payload, "expected_state")
        expected_state: RecordReference | AbsentType
        if raw_expected_state is ABSENT:
            expected_state = ABSENT
        else:
            expected_state = _record_reference_from_dict(
                raw_expected_state, required_family=None, owner="ConcurrencyConflict.expected_state"
            )

        raw_observed_state = field_from_payload(payload, "observed_state")
        observed_state: RecordReference | AbsentType
        if raw_observed_state is ABSENT:
            observed_state = ABSENT
        else:
            observed_state = _record_reference_from_dict(
                raw_observed_state, required_family=None, owner="ConcurrencyConflict.observed_state"
            )

        raw_winner = payload["winner"]
        winner: RecordReference | None
        if raw_winner is None:
            winner = None
        else:
            winner = _record_reference_from_dict(
                raw_winner, required_family=None, owner="ConcurrencyConflict.winner"
            )

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "ConcurrencyConflict.migration_epoch")
            ),
            actors=actors,
            requests=requests,
            type=ConflictType(_require_str(payload["type"], "ConcurrencyConflict.type")),
            winner=winner,
            recovery_requirement=RecoveryState(
                _require_str(payload["recovery_requirement"], "ConcurrencyConflict.recovery_requirement")
            ),
            expected_state=expected_state,
            observed_state=observed_state,
            limitations=_limitations_from_list(
                payload["limitations"], owner="ConcurrencyConflict.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="ConcurrencyConflict.authority_disclosure"
            ),
            _extensions=_extensions_from_payload(
                payload,
                owner="ConcurrencyConflict",
                reserved_keys=_CONCURRENCY_CONFLICT_RESERVED_FIELD_NAMES,
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["actors"] = [_actor_entry_to_wire(a) for a in self.actors]
        result["requests"] = [serialize_value(r) for r in self.requests]
        if self.expected_state is not ABSENT:
            result["expected_state"] = serialize_value(self.expected_state)
        if self.observed_state is not ABSENT:
            result["observed_state"] = serialize_value(self.observed_state)
        result["type"] = serialize_value(self.type)
        result["winner"] = serialize_value(self.winner) if self.winner is not None else None
        result["recovery_requirement"] = serialize_value(self.recovery_requirement)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        if self._extensions is not ABSENT:
            result["_extensions"] = self._extensions.to_dict()
        return result


# ---------------------------------------------------------------------------
# RecoveryJournalEntry
# ---------------------------------------------------------------------------

_RECOVERY_JOURNAL_ENTRY_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/recovery_journal_entry.schema.json"
)
_RECOVERY_JOURNAL_ENTRY_RECORD_TYPE = "recovery_journal_entry"
_RECOVERY_JOURNAL_ENTRY_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_RECOVERY_JOURNAL_ENTRY_KNOWN_KEYS = frozenset(
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
        "sequence",
        "prior_entry_digest",
        "operation_reference",
        "prior_state_reference",
        "new_state_reference",
        "authority_state_reference",
        "generation_reference",
        "publication_attempt_reference",
        "external_effect_state",
        "retry_replay_classification",
        "operator_review",
        "recovery_action",
        "state",
        "limitations",
        "authority_disclosure",
        "_extensions",
    }
)

_RECOVERY_JOURNAL_ENTRY_RESERVED_FIELD_NAMES = frozenset(
    _RECOVERY_JOURNAL_ENTRY_KNOWN_KEYS - {"_extensions"}
)

_OPERATOR_REVIEW_KNOWN_KEYS = frozenset({"notes"})
_RECOVERY_ACTION_KNOWN_KEYS = frozenset({"description"})


def _operator_review_from_dict(value: Mapping[str, Any], *, owner: str) -> OperatorReview:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _OPERATOR_REVIEW_KNOWN_KEYS, owner)
    if "notes" not in payload:
        raise TypedModelConstructionError(f"{owner}: missing required field 'notes'")
    return OperatorReview(notes=_validate_disclosure_text(payload["notes"], f"{owner}.notes"))


def _recovery_action_from_dict(value: Mapping[str, Any], *, owner: str) -> RecoveryAction:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _RECOVERY_ACTION_KNOWN_KEYS, owner)
    if "description" not in payload:
        raise TypedModelConstructionError(f"{owner}: missing required field 'description'")
    return RecoveryAction(
        description=_validate_disclosure_text(payload["description"], f"{owner}.description")
    )


@dataclasses.dataclass(frozen=True)
class RecoveryJournalEntry:
    """Shape-only wire contract for a ``RecoveryJournalEntry`` companion
    record (``records/recovery_journal_entry.schema.json``, contract
    Sec.28). A ``RecoveryJournalEntry`` document describes a single,
    append-only entry in a hash-chained recovery journal for one
    operation (a request or attempt); it never itself executes the
    recorded recovery action, mutates lifecycle state, proves the event
    occurred, proves journal ordering across records, establishes replay
    safety, authorizes retry, or activates authority (Sec.1, Sec.40).
    Legacy lifecycle remains the sole production authority; CLTR remains
    derivative. Tier 2 (``_extensions`` only, Sec.14).

    This model does not: append itself to a journal, read previous
    entries, validate sequence continuity, determine the next recovery
    action, retry anything, replay anything, resume anything, roll back
    anything, repair records, update state, or persist itself. A recovery
    journal entry is a declared historical or intended recovery record
    only.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    transition_id: TransitionId
    sequence: int
    prior_entry_digest: JournalEntryDigest | None
    operation_reference: RecordReference
    prior_state_reference: RecordReference
    new_state_reference: RecordReference
    authority_state_reference: RecordReference
    generation_reference: GenerationReference
    external_effect_state: ExternalEffectState
    retry_replay_classification: RetryReplayClassification
    state: JournalState
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    publication_attempt_reference: RecordReference | AbsentType = ABSENT
    operator_review: OperatorReview | AbsentType = ABSENT
    recovery_action: RecoveryAction | AbsentType = ABSENT
    _extensions: ExtensionMapping | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _RECOVERY_JOURNAL_ENTRY_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"RecoveryJournalEntry.envelope.record_type must be "
                f"{_RECOVERY_JOURNAL_ENTRY_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _RECOVERY_JOURNAL_ENTRY_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"RecoveryJournalEntry.envelope.schema_id must be the frozen "
                f"const {_RECOVERY_JOURNAL_ENTRY_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family (Sec.9's 12-file list, schema description).
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "RecoveryJournalEntry.authority_disclosure.authority_role must "
                "not be 'authoritative': a journal entry is never itself a "
                "resolved live-authority claim"
            )
        require_family(self.authority_state_reference, RecordFamily.AUTHORITY_STATE)
        if self.publication_attempt_reference is not ABSENT:
            require_family(self.publication_attempt_reference, RecordFamily.PUBLICATION_ATTEMPT)
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool):
            raise TypedModelInternalInvariantError(
                "RecoveryJournalEntry.sequence must be a non-negative integer"
            )
        if self.sequence < 0:
            raise TypedModelInternalInvariantError(
                "RecoveryJournalEntry.sequence must be a non-negative integer"
            )
        # sequence <-> prior_entry_digest conditional (Sec.28 hash-chain
        # shape): null only when sequence == 0 (genesis), a well-formed
        # digest otherwise. Chain-integrity verification (that the digest
        # actually matches a real prior entry) is explicitly out of scope
        # (Layer 4) -- shape only.
        if self.sequence == 0:
            if self.prior_entry_digest is not None:
                raise TypedModelInternalInvariantError(
                    "RecoveryJournalEntry.prior_entry_digest must be null when "
                    "sequence is 0 (genesis entry)"
                )
        else:
            if self.prior_entry_digest is None:
                raise TypedModelInternalInvariantError(
                    "RecoveryJournalEntry.prior_entry_digest must be a "
                    "well-formed digest when sequence is not 0"
                )
        # state <-> operator_review conditional (Sec.28).
        if self.state in _JOURNAL_STATES_REQUIRING_OPERATOR_REVIEW:
            if self.operator_review is ABSENT:
                raise TypedModelInternalInvariantError(
                    "RecoveryJournalEntry.operator_review is required when "
                    "state is 'reviewed', 'actioned', or 'superseded'"
                )
        else:
            if self.operator_review is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "RecoveryJournalEntry.operator_review is forbidden when "
                    "state is 'recorded'"
                )
        # state <-> recovery_action conditional (Sec.28).
        if self.state is JournalState.ACTIONED:
            if self.recovery_action is ABSENT:
                raise TypedModelInternalInvariantError(
                    "RecoveryJournalEntry.recovery_action is required when "
                    "state is 'actioned'"
                )
        else:
            if self.recovery_action is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "RecoveryJournalEntry.recovery_action is forbidden unless "
                    "state is 'actioned'"
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "RecoveryJournalEntry":
        if schema_version not in _RECOVERY_JOURNAL_ENTRY_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"RecoveryJournalEntry does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "RecoveryJournalEntry")
        _reject_unknown_keys(payload, _RECOVERY_JOURNAL_ENTRY_KNOWN_KEYS, "RecoveryJournalEntry")

        envelope = _envelope_from_payload(
            payload,
            record_type=_RECOVERY_JOURNAL_ENTRY_RECORD_TYPE,
            schema_id=_RECOVERY_JOURNAL_ENTRY_SCHEMA_ID,
        )

        for required_key in (
            "migration_epoch",
            "transition_id",
            "sequence",
            "prior_entry_digest",
            "operation_reference",
            "prior_state_reference",
            "new_state_reference",
            "authority_state_reference",
            "generation_reference",
            "external_effect_state",
            "retry_replay_classification",
            "state",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"RecoveryJournalEntry: missing required field {required_key!r}"
                )

        sequence = payload["sequence"]

        raw_prior_entry_digest = payload["prior_entry_digest"]
        prior_entry_digest: JournalEntryDigest | None
        if raw_prior_entry_digest is None:
            prior_entry_digest = None
        else:
            prior_entry_digest = JournalEntryDigest(
                _require_str(raw_prior_entry_digest, "RecoveryJournalEntry.prior_entry_digest")
            )

        raw_publication_attempt_reference = field_from_payload(payload, "publication_attempt_reference")
        publication_attempt_reference: RecordReference | AbsentType
        if raw_publication_attempt_reference is ABSENT:
            publication_attempt_reference = ABSENT
        else:
            publication_attempt_reference = _record_reference_from_dict(
                raw_publication_attempt_reference,
                required_family=RecordFamily.PUBLICATION_ATTEMPT,
                owner="RecoveryJournalEntry.publication_attempt_reference",
            )

        raw_operator_review = field_from_payload(payload, "operator_review")
        operator_review: OperatorReview | AbsentType
        if raw_operator_review is ABSENT:
            operator_review = ABSENT
        else:
            operator_review = _operator_review_from_dict(
                raw_operator_review, owner="RecoveryJournalEntry.operator_review"
            )

        raw_recovery_action = field_from_payload(payload, "recovery_action")
        recovery_action: RecoveryAction | AbsentType
        if raw_recovery_action is ABSENT:
            recovery_action = ABSENT
        else:
            recovery_action = _recovery_action_from_dict(
                raw_recovery_action, owner="RecoveryJournalEntry.recovery_action"
            )

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "RecoveryJournalEntry.migration_epoch")
            ),
            transition_id=TransitionId(
                _require_str(payload["transition_id"], "RecoveryJournalEntry.transition_id")
            ),
            sequence=sequence,
            prior_entry_digest=prior_entry_digest,
            operation_reference=_record_reference_from_dict(
                payload["operation_reference"],
                required_family=None,
                owner="RecoveryJournalEntry.operation_reference",
            ),
            prior_state_reference=_record_reference_from_dict(
                payload["prior_state_reference"],
                required_family=None,
                owner="RecoveryJournalEntry.prior_state_reference",
            ),
            new_state_reference=_record_reference_from_dict(
                payload["new_state_reference"],
                required_family=None,
                owner="RecoveryJournalEntry.new_state_reference",
            ),
            authority_state_reference=_record_reference_from_dict(
                payload["authority_state_reference"],
                required_family=RecordFamily.AUTHORITY_STATE,
                owner="RecoveryJournalEntry.authority_state_reference",
            ),
            generation_reference=_generation_reference_from_dict(
                payload["generation_reference"], owner="RecoveryJournalEntry.generation_reference"
            ),
            publication_attempt_reference=publication_attempt_reference,
            external_effect_state=ExternalEffectState(
                _require_str(
                    payload["external_effect_state"], "RecoveryJournalEntry.external_effect_state"
                )
            ),
            retry_replay_classification=RetryReplayClassification(
                _require_str(
                    payload["retry_replay_classification"],
                    "RecoveryJournalEntry.retry_replay_classification",
                )
            ),
            operator_review=operator_review,
            recovery_action=recovery_action,
            state=JournalState(_require_str(payload["state"], "RecoveryJournalEntry.state")),
            limitations=_limitations_from_list(
                payload["limitations"], owner="RecoveryJournalEntry.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="RecoveryJournalEntry.authority_disclosure"
            ),
            _extensions=_extensions_from_payload(
                payload,
                owner="RecoveryJournalEntry",
                reserved_keys=_RECOVERY_JOURNAL_ENTRY_RESERVED_FIELD_NAMES,
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["transition_id"] = serialize_value(self.transition_id)
        result["sequence"] = self.sequence
        result["prior_entry_digest"] = (
            serialize_value(self.prior_entry_digest) if self.prior_entry_digest is not None else None
        )
        result["operation_reference"] = serialize_value(self.operation_reference)
        result["prior_state_reference"] = serialize_value(self.prior_state_reference)
        result["new_state_reference"] = serialize_value(self.new_state_reference)
        result["authority_state_reference"] = serialize_value(self.authority_state_reference)
        result["generation_reference"] = serialize_value(self.generation_reference)
        if self.publication_attempt_reference is not ABSENT:
            result["publication_attempt_reference"] = serialize_value(self.publication_attempt_reference)
        result["external_effect_state"] = serialize_value(self.external_effect_state)
        result["retry_replay_classification"] = serialize_value(self.retry_replay_classification)
        if self.operator_review is not ABSENT:
            result["operator_review"] = serialize_value(self.operator_review)
        if self.recovery_action is not ABSENT:
            result["recovery_action"] = serialize_value(self.recovery_action)
        result["state"] = serialize_value(self.state)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        if self._extensions is not ABSENT:
            result["_extensions"] = self._extensions.to_dict()
        return result


__all__ = [
    "ConflictType",
    "ExternalEffectState",
    "RetryReplayClassification",
    "JournalState",
    "OperatorReview",
    "RecoveryAction",
    "ConcurrencyConflict",
    "RecoveryJournalEntry",
]
