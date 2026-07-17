"""Phase 136AB: Stage 3 Typed Authority Model Authority Core Implementation
(Typed Model Implementation Group 2, per the 136Y plan Sec.4/Sec.23).

Implements exactly two record-family models: ``AuthorityEpoch`` and
``AuthorityState``, schema-backed by ``records/authority_epoch.schema.json``
and ``records/authority_state.schema.json`` respectively.

A constructed instance of either model asserts only "this JSON was
well-formed against schema X at version Y and can be represented without
loss" -- never operational truth. Neither model activates itself, selects
current authority, compares epochs, evaluates readiness, enforces CAS,
resolves a reference, computes or verifies a digest, or performs any
semantic/cross-record validation. Legacy lifecycle remains the sole
production authority; CLTR remains derivative.

No other record-family model (``CutoverRequest``, ``ReadinessPackage``,
``HumanAuthorization``, ``CutoverCandidate``, ``Certification``,
``PublicationAttempt``, ``PublicationEvidence``, ``ConcurrencyConflict``,
``RecoveryJournalEntry``, ``NotificationAuthorityBinding``,
``MarkerAuthorityBinding``, ``FinalizationReceiptAuthorityBinding``,
``CompatibilityState``, ``QuarantineRecord``) is implemented here; those
belong to future, separately governed implementation groups.
"""

from __future__ import annotations

import dataclasses
import enum
from collections.abc import Mapping
from typing import Any, Optional

from pcae.cltr.authority.digest import (
    GenerationDigest,
    PointerDigest,
    RecordDigest,
    ReferencedRecordDigest,
)
from pcae.cltr.authority.enums import AuthorityKind, AuthorityRole, CompatibilityMode, RecordFamily
from pcae.cltr.authority.envelope import RecordEnvelope, SchemaVersionString, Timestamp
from pcae.cltr.authority.errors import (
    TypedModelConstructionError,
    TypedModelInternalInvariantError,
    UnsupportedSchemaVersionError,
)
from pcae.cltr.authority.identity import (
    GenerationId,
    MigrationEpochToken,
    RecordId,
    TransitionId,
)
from pcae.cltr.authority.limitations import AuthorityDisclosure, Limitations
from pcae.cltr.authority.references import GenerationReference, RecordReference, require_family
from pcae.cltr.authority.sentinels import ABSENT, AbsentType
from pcae.cltr.authority.serialization import field_from_payload, serialize_value, to_dict_fields

# ---------------------------------------------------------------------------
# Record-local enums (not part of the 9 shared cross-family enums in
# enums.py; each is scoped to its own owning record schema, matching the
# schema layer's own non-centralization choice -- see 136Y plan Sec.5/Sec.12,
# NON-BLOCKING-136V-2 precedent for a record-local enum distinct from a
# shared one of similar shape).
# ---------------------------------------------------------------------------


class ActivationState(str, enum.Enum):
    """``AuthorityEpoch``'s record-local ``activation_state`` (3 values,
    ``records/authority_epoch.schema.json``). "proposed" epochs must not
    carry a ``generation_binding``; "active" epochs must. "superseded"
    marks a formerly active epoch now retired from currency -- schema shape
    alone cannot verify that a superseded epoch is no longer resolved as
    live authority (Layer 4/6), and this type makes no such claim."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class VerificationState(str, enum.Enum):
    """``AuthorityState``'s record-local ``verification_state`` (3 values,
    ``records/authority_state.schema.json``). "unverified" requires an
    accompanying ``uncertainty`` disclosure; "verified" forbids one
    (mutually exclusive at the local shape level, restated, not extended,
    by ``__post_init__`` below)."""

    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    VERIFICATION_FAILED = "verification_failed"


# ---------------------------------------------------------------------------
# Nested value objects
# ---------------------------------------------------------------------------


_DISCLOSURE_TEXT_MAX_LENGTH = 500


def _validate_disclosure_text(value: str, type_name: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= _DISCLOSURE_TEXT_MAX_LENGTH):
        raise TypedModelConstructionError(
            f"{type_name}.reason must be a non-empty string of at most "
            f"{_DISCLOSURE_TEXT_MAX_LENGTH} characters"
        )
    if any(ord(ch) < 0x20 or ord(ch) > 0x7E for ch in value):
        raise TypedModelConstructionError(
            f"{type_name}.reason must be single-line printable ASCII only"
        )
    return value


@dataclasses.dataclass(frozen=True)
class Uncertainty:
    """``AuthorityState``'s bounded local ``uncertainty`` disclosure object
    (``records/authority_state.schema.json#/$defs/uncertainty``). Present
    only when ``verification_state`` is ``"unverified"``. A disclosure
    only -- never itself a resolution of the uncertainty it names."""

    reason: str

    def __post_init__(self) -> None:
        _validate_disclosure_text(self.reason, "Uncertainty")


# ---------------------------------------------------------------------------
# Shared field-extraction helpers (Layer 3 construction pipeline, 136Y plan
# Sec.16). Every helper re-validates enum/wrapper membership at the
# type-construction boundary rather than trusting an upstream schema-valid
# payload blindly, explicitly closing finding 136AA-1 (Sec.18 of the 136AA
# independent verification report).
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
    value: Mapping[str, Any], *, required_family: RecordFamily, owner: str
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
    return require_family(reference, required_family)


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


_UNCERTAINTY_KNOWN_KEYS = frozenset({"reason"})


def _uncertainty_from_dict(value: Mapping[str, Any], *, owner: str) -> Uncertainty:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _UNCERTAINTY_KNOWN_KEYS, owner)
    if "reason" not in payload:
        raise TypedModelConstructionError(f"{owner}: missing required field 'reason'")
    return Uncertainty(reason=_require_str(payload["reason"], f"{owner}.reason"))


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
# AuthorityEpoch
# ---------------------------------------------------------------------------

_AUTHORITY_EPOCH_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json"
_AUTHORITY_EPOCH_RECORD_TYPE = "authority_epoch"
_AUTHORITY_EPOCH_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_AUTHORITY_EPOCH_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "authority_kind",
        "activation_state",
        "predecessor_epoch",
        "generation_binding",
        "limitations",
        "authority_disclosure",
    }
)


@dataclasses.dataclass(frozen=True)
class AuthorityEpoch:
    """Shape-only wire contract for an ``AuthorityEpoch`` companion record
    (``records/authority_epoch.schema.json``, contract Sec.17). Identifies
    one migration-epoch-scoped authority lineage node: proposed, active, or
    superseded. Construction validity never establishes that the described
    epoch exists, is currently active, or is production authority.

    This model does not: activate itself, determine whether it is current,
    compare itself with repository state, read another epoch, calculate a
    generation, compute a digest, validate historical continuity, select
    authority, or mutate lifecycle state.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    authority_kind: AuthorityKind
    activation_state: ActivationState
    predecessor_epoch: Optional[RecordReference]
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    generation_binding: GenerationReference | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _AUTHORITY_EPOCH_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"AuthorityEpoch.envelope.record_type must be "
                f"{_AUTHORITY_EPOCH_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _AUTHORITY_EPOCH_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"AuthorityEpoch.envelope.schema_id must be the frozen const "
                f"{_AUTHORITY_EPOCH_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family (schema description, contract Sec.9): an epoch
        # identifies a lineage node, never a resolved live-authority claim.
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "AuthorityEpoch.authority_disclosure.authority_role must not be "
                "'authoritative': an epoch is a lineage node, never a resolved "
                "live-authority claim (that belongs to AuthorityState only)"
            )
        if self.predecessor_epoch is not None:
            require_family(self.predecessor_epoch, RecordFamily.AUTHORITY_EPOCH)
        # activation_state <-> generation_binding conditional (schema
        # allOf/if-then, restated here as the single-document Layer 3
        # invariant it already is -- not a new Layer 4/5 rule).
        if self.activation_state is ActivationState.ACTIVE and self.generation_binding is ABSENT:
            raise TypedModelInternalInvariantError(
                "AuthorityEpoch.generation_binding is required when "
                "activation_state is 'active'"
            )
        if self.activation_state is ActivationState.PROPOSED and self.generation_binding is not ABSENT:
            raise TypedModelInternalInvariantError(
                "AuthorityEpoch.generation_binding is forbidden when "
                "activation_state is 'proposed'"
            )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "AuthorityEpoch":
        if schema_version not in _AUTHORITY_EPOCH_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"AuthorityEpoch does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "AuthorityEpoch")
        _reject_unknown_keys(payload, _AUTHORITY_EPOCH_KNOWN_KEYS, "AuthorityEpoch")

        envelope = _envelope_from_payload(
            payload, record_type=_AUTHORITY_EPOCH_RECORD_TYPE, schema_id=_AUTHORITY_EPOCH_SCHEMA_ID
        )

        for required_key in (
            "migration_epoch",
            "authority_kind",
            "activation_state",
            "predecessor_epoch",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"AuthorityEpoch: missing required field {required_key!r}"
                )

        raw_predecessor = payload["predecessor_epoch"]
        predecessor_epoch: Optional[RecordReference]
        if raw_predecessor is None:
            predecessor_epoch = None
        else:
            predecessor_epoch = _record_reference_from_dict(
                raw_predecessor,
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="AuthorityEpoch.predecessor_epoch",
            )

        raw_generation_binding = field_from_payload(payload, "generation_binding")
        generation_binding: GenerationReference | AbsentType
        if raw_generation_binding is ABSENT:
            generation_binding = ABSENT
        else:
            generation_binding = _generation_reference_from_dict(
                raw_generation_binding, owner="AuthorityEpoch.generation_binding"
            )

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "AuthorityEpoch.migration_epoch")
            ),
            authority_kind=AuthorityKind(
                _require_str(payload["authority_kind"], "AuthorityEpoch.authority_kind")
            ),
            activation_state=ActivationState(
                _require_str(payload["activation_state"], "AuthorityEpoch.activation_state")
            ),
            predecessor_epoch=predecessor_epoch,
            generation_binding=generation_binding,
            limitations=_limitations_from_list(payload["limitations"], owner="AuthorityEpoch.limitations"),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="AuthorityEpoch.authority_disclosure"
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["authority_kind"] = serialize_value(self.authority_kind)
        result["activation_state"] = serialize_value(self.activation_state)
        result["predecessor_epoch"] = (
            None if self.predecessor_epoch is None else serialize_value(self.predecessor_epoch)
        )
        if self.generation_binding is not ABSENT:
            result["generation_binding"] = serialize_value(self.generation_binding)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        return result


# ---------------------------------------------------------------------------
# AuthorityState
# ---------------------------------------------------------------------------

_AUTHORITY_STATE_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/records/authority_state.schema.json"
_AUTHORITY_STATE_RECORD_TYPE = "authority_state"
_AUTHORITY_STATE_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_AUTHORITY_STATE_KNOWN_KEYS = frozenset(
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
        "active_authority_epoch",
        "authority_kind",
        "authoritative_generation",
        "publication_evidence_reference",
        "pointer_digest",
        "verification_state",
        "uncertainty",
        "compatibility_mode",
        "limitations",
        "authority_disclosure",
    }
)


@dataclasses.dataclass(frozen=True)
class AuthorityState:
    """Shape-only wire contract for an ``AuthorityState`` companion record
    (``records/authority_state.schema.json``, contract Sec.18). The
    companion evidence-adjacent record documenting a resolved-authority
    claim; the architectural relationship (production authority pointer ->
    AuthorityState record -> authoritative generation) is documentation
    only and is never established by construction validity alone.

    This model does not: determine current authority, evaluate whether a
    transition is legal, compare expected state with actual state, enforce
    CAS, resolve epoch references, persist state, update state, authorize
    execution, demote legacy lifecycle, or retire an authority.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    transition_id: TransitionId
    active_authority_epoch: RecordReference
    authority_kind: AuthorityKind
    publication_evidence_reference: RecordReference
    pointer_digest: PointerDigest
    verification_state: VerificationState
    compatibility_mode: CompatibilityMode
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    authoritative_generation: GenerationReference | AbsentType = ABSENT
    uncertainty: Uncertainty | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _AUTHORITY_STATE_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"AuthorityState.envelope.record_type must be "
                f"{_AUTHORITY_STATE_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _AUTHORITY_STATE_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"AuthorityState.envelope.schema_id must be the frozen const "
                f"{_AUTHORITY_STATE_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        require_family(self.active_authority_epoch, RecordFamily.AUTHORITY_EPOCH)
        require_family(self.publication_evidence_reference, RecordFamily.PUBLICATION_EVIDENCE)
        # authority_kind <-> authoritative_generation conditional.
        if self.authority_kind is AuthorityKind.CLTR and self.authoritative_generation is ABSENT:
            raise TypedModelInternalInvariantError(
                "AuthorityState.authoritative_generation is required when "
                "authority_kind is 'cltr'"
            )
        # verification_state <-> uncertainty conditional.
        if self.verification_state is VerificationState.UNVERIFIED and self.uncertainty is ABSENT:
            raise TypedModelInternalInvariantError(
                "AuthorityState.uncertainty is required when verification_state "
                "is 'unverified'"
            )
        if self.verification_state is VerificationState.VERIFIED and self.uncertainty is not ABSENT:
            raise TypedModelInternalInvariantError(
                "AuthorityState.uncertainty is forbidden when verification_state "
                "is 'verified'"
            )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "AuthorityState":
        if schema_version not in _AUTHORITY_STATE_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"AuthorityState does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "AuthorityState")
        _reject_unknown_keys(payload, _AUTHORITY_STATE_KNOWN_KEYS, "AuthorityState")

        envelope = _envelope_from_payload(
            payload, record_type=_AUTHORITY_STATE_RECORD_TYPE, schema_id=_AUTHORITY_STATE_SCHEMA_ID
        )

        for required_key in (
            "migration_epoch",
            "transition_id",
            "active_authority_epoch",
            "authority_kind",
            "publication_evidence_reference",
            "pointer_digest",
            "verification_state",
            "compatibility_mode",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"AuthorityState: missing required field {required_key!r}"
                )

        raw_authoritative_generation = field_from_payload(payload, "authoritative_generation")
        authoritative_generation: GenerationReference | AbsentType
        if raw_authoritative_generation is ABSENT:
            authoritative_generation = ABSENT
        else:
            authoritative_generation = _generation_reference_from_dict(
                raw_authoritative_generation, owner="AuthorityState.authoritative_generation"
            )

        raw_uncertainty = field_from_payload(payload, "uncertainty")
        uncertainty: Uncertainty | AbsentType
        if raw_uncertainty is ABSENT:
            uncertainty = ABSENT
        else:
            uncertainty = _uncertainty_from_dict(raw_uncertainty, owner="AuthorityState.uncertainty")

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "AuthorityState.migration_epoch")
            ),
            transition_id=TransitionId(
                _require_str(payload["transition_id"], "AuthorityState.transition_id")
            ),
            active_authority_epoch=_record_reference_from_dict(
                payload["active_authority_epoch"],
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="AuthorityState.active_authority_epoch",
            ),
            authority_kind=AuthorityKind(
                _require_str(payload["authority_kind"], "AuthorityState.authority_kind")
            ),
            authoritative_generation=authoritative_generation,
            publication_evidence_reference=_record_reference_from_dict(
                payload["publication_evidence_reference"],
                required_family=RecordFamily.PUBLICATION_EVIDENCE,
                owner="AuthorityState.publication_evidence_reference",
            ),
            pointer_digest=PointerDigest(
                _require_str(payload["pointer_digest"], "AuthorityState.pointer_digest")
            ),
            verification_state=VerificationState(
                _require_str(payload["verification_state"], "AuthorityState.verification_state")
            ),
            uncertainty=uncertainty,
            compatibility_mode=CompatibilityMode(
                _require_str(payload["compatibility_mode"], "AuthorityState.compatibility_mode")
            ),
            limitations=_limitations_from_list(payload["limitations"], owner="AuthorityState.limitations"),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="AuthorityState.authority_disclosure"
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["transition_id"] = serialize_value(self.transition_id)
        result["active_authority_epoch"] = serialize_value(self.active_authority_epoch)
        result["authority_kind"] = serialize_value(self.authority_kind)
        if self.authoritative_generation is not ABSENT:
            result["authoritative_generation"] = serialize_value(self.authoritative_generation)
        result["publication_evidence_reference"] = serialize_value(self.publication_evidence_reference)
        result["pointer_digest"] = serialize_value(self.pointer_digest)
        result["verification_state"] = serialize_value(self.verification_state)
        if self.uncertainty is not ABSENT:
            result["uncertainty"] = serialize_value(self.uncertainty)
        result["compatibility_mode"] = serialize_value(self.compatibility_mode)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        return result


__all__ = [
    "ActivationState",
    "VerificationState",
    "Uncertainty",
    "AuthorityEpoch",
    "AuthorityState",
]
