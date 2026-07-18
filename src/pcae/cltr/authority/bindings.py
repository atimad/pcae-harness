"""Phase 136AL: Stage 3 Typed Authority Model Notification Authority Binding
Implementation (Typed Model Implementation Group 7, per the 136Y plan
Sec.4/Sec.31, package layout Sec.7). Phase 136AN: Stage 3 Typed Authority
Model Marker Authority Binding Implementation (Typed Model Implementation
Group 8, per the 136Y plan Sec.4/Sec.32, package layout Sec.7 -- both
``NotificationAuthorityBinding`` and ``MarkerAuthorityBinding`` are
contract "Authority Bindings" group members and live in this same
``bindings.py`` module per the plan's Sec.7 file layout).

Implements exactly two record-family models: ``NotificationAuthorityBinding``,
schema-backed by ``records/notification_authority_binding.schema.json``,
and ``MarkerAuthorityBinding``, schema-backed by
``records/marker_authority_binding.schema.json``.

A constructed instance asserts only "this JSON was well-formed against
schema X at version Y and can be represented without loss" -- never
operational truth. ``NotificationAuthorityBinding`` does not send a
notification, dispatch Telegram/email/Slack, resolve a notification
provider, resolve a delivery channel, inspect runtime configuration,
inspect environment variables, inspect notification configuration,
determine notification success or failure, build a notification payload,
queue or schedule a notification, retry a notification, mutate
notification state, activate authority, resolve authority, determine
current authority, compare authorities, transfer authority, mutate an
authority pointer, or modify lifecycle state. It is a representation of a
claimed notification-dispatch association for a specific authoritative
generation, never proof that a notification was dispatched, delivered
exactly once, or that its claimed marker/receipt bindings are correct.
``MarkerAuthorityBinding`` does not create, write, update, delete, rename,
publish, discover, enumerate markers, resolve marker locations, inspect
marker files, validate marker existence, compare marker freshness,
reconcile marker state, read or write marker contents, modify marker
metadata, synchronize markers, activate authority, resolve authority,
determine current authority, compare authorities, transfer authority,
mutate an authority pointer, or modify lifecycle state. It is a
representation of a claimed production marker's association with a
specific generation, never proof that a marker was actually written, is
fresh, or that a duplicate-delivery conflict is actually resolved. Legacy
lifecycle remains the sole production authority; CLTR remains derivative.

No other record-family model (``FinalizationReceiptAuthorityBinding``,
``CompatibilityState``, ``QuarantineRecord``) is implemented here; those
belong to future, separately governed implementation groups. Forward
references to those not-yet-implemented families are shape-only,
family-tagged pointers and do not require the referenced family's own
model class to exist.

Tier boundary: ``NotificationAuthorityBinding`` is Tier 2 (``_extensions``
permitted, string-valued map only, Sec.14).
"""

from __future__ import annotations

import dataclasses
import enum
import re
from collections.abc import Mapping
from typing import Any

from pcae.cltr.authority.digest import GenerationDigest, RecordDigest, ReferencedRecordDigest, Sha256Digest
from pcae.cltr.authority.enums import AuthorityRole, RecordFamily
from pcae.cltr.authority.envelope import RecordEnvelope, SchemaVersionString, Timestamp
from pcae.cltr.authority.errors import (
    TypedModelConstructionError,
    TypedModelInternalInvariantError,
    UnsupportedSchemaVersionError,
)
from pcae.cltr.authority.extensions import ExtensionMapping
from pcae.cltr.authority.identity import GenerationId, MigrationEpochToken, RecordId
from pcae.cltr.authority.limitations import AuthorityDisclosure, Limitations
from pcae.cltr.authority.references import GenerationReference, RecordReference, require_family
from pcae.cltr.authority.sentinels import ABSENT, AbsentType
from pcae.cltr.authority.serialization import field_from_payload, serialize_value, to_dict_fields

# ---------------------------------------------------------------------------
# Record-local enums (family-scoped, not part of the shared cross-family
# enums in enums.py -- matching the schema layer's own non-centralization
# choice, same precedent as authority_core.py / request_readiness.py /
# authorization_candidate.py / publication.py / recovery_concurrency.py).
# ---------------------------------------------------------------------------


class DeliveryState(str, enum.Enum):
    """``NotificationAuthorityBinding``'s record-local ``delivery_state``
    field (Sec.8.8, 3 values, home schema
    ``notification_authority_binding.schema.json``). 'payload_conflict'
    requires ``uncertainty``; any value other than 'not_dispatched'
    requires ``marker_reference``; 'already_dispatched' requires
    ``receipt_reference`` (all enforced below). A schema-valid value here
    never itself proves external delivery occurred (Layer 4/40)."""

    NOT_DISPATCHED = "not_dispatched"
    ALREADY_DISPATCHED = "already_dispatched"
    PAYLOAD_CONFLICT = "payload_conflict"


# ---------------------------------------------------------------------------
# Nested value objects
# ---------------------------------------------------------------------------

_DISCLOSURE_TEXT_MAX_LENGTH = 500
_DISCLOSURE_TEXT_PATTERN = re.compile(r"^[\x20-\x7E]*$")
_PFN001_CLASSIFICATION_MAX_LENGTH = 256
_PFN001_CLASSIFICATION_PATTERN = re.compile(r"^[\x20-\x7E]*$")


def _validate_disclosure_text(value: Any, owner: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= _DISCLOSURE_TEXT_MAX_LENGTH):
        raise TypedModelConstructionError(
            f"{owner} must be a non-empty string of at most "
            f"{_DISCLOSURE_TEXT_MAX_LENGTH} characters"
        )
    if not _DISCLOSURE_TEXT_PATTERN.fullmatch(value):
        raise TypedModelConstructionError(f"{owner} must be single-line printable ASCII only")
    return value


def _validate_pfn001_classification(value: Any, owner: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= _PFN001_CLASSIFICATION_MAX_LENGTH):
        raise TypedModelConstructionError(
            f"{owner} must be a non-empty string of at most "
            f"{_PFN001_CLASSIFICATION_MAX_LENGTH} characters"
        )
    if not _PFN001_CLASSIFICATION_PATTERN.fullmatch(value):
        raise TypedModelConstructionError(f"{owner} must be single-line printable ASCII only")
    return value


@dataclasses.dataclass(frozen=True)
class NotificationAuthorityBindingUncertainty:
    """``NotificationAuthorityBinding``'s bounded local ``uncertainty``
    disclosure object (mirrors ``publication_attempt.schema.json``'s
    ``uncertainty`` $def, restated for this record's own field per the
    schema's own local ``uncertainty`` $def). Present only when
    ``delivery_state`` is 'payload_conflict'. A disclosure only -- never
    itself a resolution of the uncertainty it names."""

    reason: str

    def __post_init__(self) -> None:
        _validate_disclosure_text(self.reason, "NotificationAuthorityBindingUncertainty.reason")


# ---------------------------------------------------------------------------
# Shared field-extraction helpers (Layer 3 construction pipeline, 136Y plan
# Sec.16). Deliberately self-contained within this module rather than
# importing another group module's private helpers -- each group module
# owns its own Layer 3 construction boilerplate, matching authority_core.py,
# request_readiness.py, authorization_candidate.py, publication.py, and
# recovery_concurrency.py's own precedent-setting structure.
# ---------------------------------------------------------------------------

_RECORD_REFERENCE_KNOWN_KEYS = frozenset(
    {"record_id", "record_digest", "record_family", "schema_id", "schema_version"}
)

# 136AL independent re-derivation (reproduced against the live schema, not
# copied from an earlier group's own field table) -- see publication.py's
# and recovery_concurrency.py's identical comment for the same rationale.
_RECORD_REFERENCE_SCHEMA_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")


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
# NotificationAuthorityBinding
# ---------------------------------------------------------------------------

_NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/notification_authority_binding.schema.json"
)
_NOTIFICATION_AUTHORITY_BINDING_RECORD_TYPE = "notification_authority_binding"
_NOTIFICATION_AUTHORITY_BINDING_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_NOTIFICATION_AUTHORITY_BINDING_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "authoritative_generation_reference",
        "authority_epoch_reference",
        "payload_digest",
        "attempt_identity",
        "pfn001_classification",
        "delivery_state",
        "uncertainty",
        "marker_reference",
        "receipt_reference",
        "limitations",
        "authority_disclosure",
        "_extensions",
    }
)

_NOTIFICATION_AUTHORITY_BINDING_RESERVED_FIELD_NAMES = frozenset(
    _NOTIFICATION_AUTHORITY_BINDING_KNOWN_KEYS - {"_extensions"}
)

_NOTIFICATION_AUTHORITY_BINDING_UNCERTAINTY_KNOWN_KEYS = frozenset({"reason"})

_NOTIFICATION_AUTHORITY_BINDING_STATES_REQUIRING_MARKER = frozenset(
    {DeliveryState.ALREADY_DISPATCHED, DeliveryState.PAYLOAD_CONFLICT}
)


def _notification_authority_binding_uncertainty_from_dict(
    value: Mapping[str, Any], *, owner: str
) -> NotificationAuthorityBindingUncertainty:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _NOTIFICATION_AUTHORITY_BINDING_UNCERTAINTY_KNOWN_KEYS, owner)
    if "reason" not in payload:
        raise TypedModelConstructionError(f"{owner}: missing required field 'reason'")
    return NotificationAuthorityBindingUncertainty(
        reason=_validate_disclosure_text(payload["reason"], f"{owner}.reason")
    )


@dataclasses.dataclass(frozen=True)
class NotificationAuthorityBinding:
    """Shape-only wire contract for a ``NotificationAuthorityBinding``
    companion record (``records/notification_authority_binding.schema.json``,
    contract Sec.31, Sec.46). A ``NotificationAuthorityBinding`` document
    describes a claimed PFN-001 notification-dispatch association for a
    specific authoritative generation; it never itself dispatches a
    notification, proves external delivery, proves exactly-once behavior,
    creates a marker, creates a receipt, mutates lifecycle state, publishes
    authority, or triggers execution (Sec.1, Sec.31, Sec.40). Legacy
    lifecycle remains the sole production authority; CLTR remains
    derivative. Tier 2 (``_extensions`` only, Sec.14).

    This model does not: send a notification, dispatch Telegram, dispatch
    email, dispatch Slack, resolve a notification provider, resolve a
    delivery channel, inspect runtime configuration, inspect environment
    variables, inspect notification configuration, determine notification
    success or failure, build a notification payload, queue a
    notification, schedule a notification, retry a notification, mutate
    notification state, activate authority, resolve authority, determine
    current authority, compare authorities, transfer authority, mutate an
    authority pointer, or modify lifecycle state. A notification authority
    binding record describes a claimed dispatch association; it does not
    perform, verify, or resolve one.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    authoritative_generation_reference: GenerationReference
    authority_epoch_reference: RecordReference
    payload_digest: Sha256Digest
    attempt_identity: RecordId
    pfn001_classification: str
    delivery_state: DeliveryState
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    uncertainty: NotificationAuthorityBindingUncertainty | AbsentType = ABSENT
    marker_reference: RecordReference | AbsentType = ABSENT
    receipt_reference: RecordReference | AbsentType = ABSENT
    _extensions: ExtensionMapping | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _NOTIFICATION_AUTHORITY_BINDING_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"NotificationAuthorityBinding.envelope.record_type must be "
                f"{_NOTIFICATION_AUTHORITY_BINDING_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"NotificationAuthorityBinding.envelope.schema_id must be the frozen "
                f"const {_NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family (Sec.9's 12-file list, schema description).
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "NotificationAuthorityBinding.authority_disclosure.authority_role "
                "must not be 'authoritative': a notification-authority-binding "
                "record is never itself a resolved live-authority claim"
            )
        require_family(self.authority_epoch_reference, RecordFamily.AUTHORITY_EPOCH)
        _validate_pfn001_classification(
            self.pfn001_classification, "NotificationAuthorityBinding.pfn001_classification"
        )
        if self.marker_reference is not ABSENT:
            require_family(self.marker_reference, RecordFamily.MARKER_AUTHORITY_BINDING)
        if self.receipt_reference is not ABSENT:
            require_family(self.receipt_reference, RecordFamily.RECEIPT_AUTHORITY_BINDING)
        # delivery_state <-> uncertainty conditional (Sec.31).
        if self.delivery_state is DeliveryState.PAYLOAD_CONFLICT:
            if self.uncertainty is ABSENT:
                raise TypedModelInternalInvariantError(
                    "NotificationAuthorityBinding.uncertainty is required when "
                    "delivery_state is 'payload_conflict'"
                )
        else:
            if self.uncertainty is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "NotificationAuthorityBinding.uncertainty is forbidden unless "
                    "delivery_state is 'payload_conflict'"
                )
        # delivery_state <-> marker_reference conditional (Sec.31).
        if self.delivery_state in _NOTIFICATION_AUTHORITY_BINDING_STATES_REQUIRING_MARKER:
            if self.marker_reference is ABSENT:
                raise TypedModelInternalInvariantError(
                    "NotificationAuthorityBinding.marker_reference is required "
                    "unless delivery_state is 'not_dispatched'"
                )
        else:
            if self.marker_reference is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "NotificationAuthorityBinding.marker_reference is forbidden "
                    "when delivery_state is 'not_dispatched'"
                )
        # delivery_state <-> receipt_reference conditional (Sec.31).
        if self.delivery_state is DeliveryState.ALREADY_DISPATCHED:
            if self.receipt_reference is ABSENT:
                raise TypedModelInternalInvariantError(
                    "NotificationAuthorityBinding.receipt_reference is required "
                    "when delivery_state is 'already_dispatched'"
                )
        else:
            if self.receipt_reference is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "NotificationAuthorityBinding.receipt_reference is forbidden "
                    "unless delivery_state is 'already_dispatched'"
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "NotificationAuthorityBinding":
        if schema_version not in _NOTIFICATION_AUTHORITY_BINDING_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"NotificationAuthorityBinding does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "NotificationAuthorityBinding")
        _reject_unknown_keys(
            payload, _NOTIFICATION_AUTHORITY_BINDING_KNOWN_KEYS, "NotificationAuthorityBinding"
        )

        envelope = _envelope_from_payload(
            payload,
            record_type=_NOTIFICATION_AUTHORITY_BINDING_RECORD_TYPE,
            schema_id=_NOTIFICATION_AUTHORITY_BINDING_SCHEMA_ID,
        )

        for required_key in (
            "migration_epoch",
            "authoritative_generation_reference",
            "authority_epoch_reference",
            "payload_digest",
            "attempt_identity",
            "pfn001_classification",
            "delivery_state",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"NotificationAuthorityBinding: missing required field {required_key!r}"
                )

        raw_uncertainty = field_from_payload(payload, "uncertainty")
        uncertainty: NotificationAuthorityBindingUncertainty | AbsentType
        if raw_uncertainty is ABSENT:
            uncertainty = ABSENT
        else:
            uncertainty = _notification_authority_binding_uncertainty_from_dict(
                raw_uncertainty, owner="NotificationAuthorityBinding.uncertainty"
            )

        raw_marker_reference = field_from_payload(payload, "marker_reference")
        marker_reference: RecordReference | AbsentType
        if raw_marker_reference is ABSENT:
            marker_reference = ABSENT
        else:
            marker_reference_raw = _require_mapping(
                raw_marker_reference, "NotificationAuthorityBinding.marker_reference"
            )
            _require_cross_family_reference_fields(
                marker_reference_raw, owner="NotificationAuthorityBinding.marker_reference"
            )
            marker_reference = _record_reference_from_dict(
                marker_reference_raw,
                required_family=RecordFamily.MARKER_AUTHORITY_BINDING,
                owner="NotificationAuthorityBinding.marker_reference",
            )

        raw_receipt_reference = field_from_payload(payload, "receipt_reference")
        receipt_reference: RecordReference | AbsentType
        if raw_receipt_reference is ABSENT:
            receipt_reference = ABSENT
        else:
            receipt_reference_raw = _require_mapping(
                raw_receipt_reference, "NotificationAuthorityBinding.receipt_reference"
            )
            _require_cross_family_reference_fields(
                receipt_reference_raw, owner="NotificationAuthorityBinding.receipt_reference"
            )
            receipt_reference = _record_reference_from_dict(
                receipt_reference_raw,
                required_family=RecordFamily.RECEIPT_AUTHORITY_BINDING,
                owner="NotificationAuthorityBinding.receipt_reference",
            )

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "NotificationAuthorityBinding.migration_epoch")
            ),
            authoritative_generation_reference=_generation_reference_from_dict(
                payload["authoritative_generation_reference"],
                owner="NotificationAuthorityBinding.authoritative_generation_reference",
            ),
            authority_epoch_reference=_record_reference_from_dict(
                payload["authority_epoch_reference"],
                required_family=RecordFamily.AUTHORITY_EPOCH,
                owner="NotificationAuthorityBinding.authority_epoch_reference",
            ),
            payload_digest=Sha256Digest(
                _require_str(payload["payload_digest"], "NotificationAuthorityBinding.payload_digest")
            ),
            attempt_identity=RecordId(
                _require_str(payload["attempt_identity"], "NotificationAuthorityBinding.attempt_identity")
            ),
            pfn001_classification=_validate_pfn001_classification(
                payload["pfn001_classification"], "NotificationAuthorityBinding.pfn001_classification"
            ),
            delivery_state=DeliveryState(
                _require_str(payload["delivery_state"], "NotificationAuthorityBinding.delivery_state")
            ),
            uncertainty=uncertainty,
            marker_reference=marker_reference,
            receipt_reference=receipt_reference,
            limitations=_limitations_from_list(
                payload["limitations"], owner="NotificationAuthorityBinding.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="NotificationAuthorityBinding.authority_disclosure"
            ),
            _extensions=_extensions_from_payload(
                payload,
                owner="NotificationAuthorityBinding",
                reserved_keys=_NOTIFICATION_AUTHORITY_BINDING_RESERVED_FIELD_NAMES,
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["authoritative_generation_reference"] = serialize_value(
            self.authoritative_generation_reference
        )
        result["authority_epoch_reference"] = serialize_value(self.authority_epoch_reference)
        result["payload_digest"] = serialize_value(self.payload_digest)
        result["attempt_identity"] = serialize_value(self.attempt_identity)
        result["pfn001_classification"] = self.pfn001_classification
        result["delivery_state"] = serialize_value(self.delivery_state)
        if self.uncertainty is not ABSENT:
            result["uncertainty"] = serialize_value(self.uncertainty)
        if self.marker_reference is not ABSENT:
            result["marker_reference"] = serialize_value(self.marker_reference)
        if self.receipt_reference is not ABSENT:
            result["receipt_reference"] = serialize_value(self.receipt_reference)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        if self._extensions is not ABSENT:
            result["_extensions"] = self._extensions.to_dict()
        return result


# ---------------------------------------------------------------------------
# MarkerAuthorityBinding
# ---------------------------------------------------------------------------

_MARKER_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/marker_authority_binding.schema.json"
)
_MARKER_AUTHORITY_BINDING_RECORD_TYPE = "marker_authority_binding"
_MARKER_AUTHORITY_BINDING_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_MARKER_AUTHORITY_BINDING_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "generation_reference",
        "state",
        "duplicate_of",
        "compatibility_fallback_forbidden",
        "limitations",
        "authority_disclosure",
        "_extensions",
    }
)

_MARKER_AUTHORITY_BINDING_RESERVED_FIELD_NAMES = frozenset(
    _MARKER_AUTHORITY_BINDING_KNOWN_KEYS - {"_extensions"}
)


class MarkerState(str, enum.Enum):
    """``MarkerAuthorityBinding``'s record-local ``state`` field (Sec.8.8,
    4 values, home schema ``marker_authority_binding.schema.json``).
    'conflict' requires ``duplicate_of``; any other value forbids it
    (enforced below). A schema-valid value here never itself proves the
    marker's actual production state (Layer 4/5)."""

    ABSENT = "absent"
    WRITTEN = "written"
    STALE = "stale"
    CONFLICT = "conflict"


def _marker_authority_binding_duplicate_of_from_dict(
    value: Mapping[str, Any], *, owner: str
) -> RecordReference:
    payload = _require_mapping(value, owner)
    _reject_unknown_keys(payload, _RECORD_REFERENCE_KNOWN_KEYS, owner)
    for required_key in ("record_id", "record_digest", "record_family"):
        if required_key not in payload:
            raise TypedModelConstructionError(f"{owner}: missing required field {required_key!r}")
    _require_cross_family_reference_fields(payload, owner=owner)
    return _record_reference_from_dict(
        payload, required_family=RecordFamily.MARKER_AUTHORITY_BINDING, owner=owner
    )


@dataclasses.dataclass(frozen=True)
class MarkerAuthorityBinding:
    """Shape-only wire contract for a ``MarkerAuthorityBinding`` companion
    record (``records/marker_authority_binding.schema.json``, contract
    Sec.32, Sec.46). A ``MarkerAuthorityBinding`` document describes a
    claimed production marker's association with a specific generation; it
    never itself creates, writes, or verifies a marker, proves marker
    freshness, resolves a duplicate-delivery conflict, or authorizes a
    compatibility fallback (Sec.1, Sec.32, Sec.40). Legacy lifecycle
    remains the sole production authority; CLTR remains derivative. Tier 2
    (``_extensions`` only, Sec.14).

    This model does not: create, write, update, delete, rename, publish,
    discover, or enumerate markers, resolve marker locations, inspect
    marker files, validate marker existence, compare marker freshness,
    reconcile marker state, read marker contents, write marker contents,
    modify marker metadata, synchronize markers, activate authority,
    resolve authority, determine current authority, compare authorities,
    transfer authority, mutate an authority pointer, or modify lifecycle
    state. A marker authority binding record describes a claimed marker
    association; it does not perform, verify, or resolve one.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    generation_reference: GenerationReference
    state: MarkerState
    compatibility_fallback_forbidden: bool
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    duplicate_of: RecordReference | None | AbsentType = ABSENT
    _extensions: ExtensionMapping | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _MARKER_AUTHORITY_BINDING_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"MarkerAuthorityBinding.envelope.record_type must be "
                f"{_MARKER_AUTHORITY_BINDING_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _MARKER_AUTHORITY_BINDING_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"MarkerAuthorityBinding.envelope.schema_id must be the frozen "
                f"const {_MARKER_AUTHORITY_BINDING_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family (Sec.9's 12-file list, schema description).
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "MarkerAuthorityBinding.authority_disclosure.authority_role "
                "must not be 'authoritative': a marker-authority-binding "
                "record is never itself a resolved live-authority claim"
            )
        if self.compatibility_fallback_forbidden is not True:
            raise TypedModelInternalInvariantError(
                "MarkerAuthorityBinding.compatibility_fallback_forbidden must be "
                "the frozen const true"
            )
        if self.duplicate_of is not ABSENT and self.duplicate_of is not None:
            require_family(self.duplicate_of, RecordFamily.MARKER_AUTHORITY_BINDING)
        # state <-> duplicate_of conditional (Sec.32).
        if self.state is MarkerState.CONFLICT:
            if self.duplicate_of is ABSENT:
                raise TypedModelInternalInvariantError(
                    "MarkerAuthorityBinding.duplicate_of is required when state "
                    "is 'conflict'"
                )
        else:
            if self.duplicate_of is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "MarkerAuthorityBinding.duplicate_of is forbidden unless "
                    "state is 'conflict'"
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "MarkerAuthorityBinding":
        if schema_version not in _MARKER_AUTHORITY_BINDING_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"MarkerAuthorityBinding does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "MarkerAuthorityBinding")
        _reject_unknown_keys(payload, _MARKER_AUTHORITY_BINDING_KNOWN_KEYS, "MarkerAuthorityBinding")

        envelope = _envelope_from_payload(
            payload,
            record_type=_MARKER_AUTHORITY_BINDING_RECORD_TYPE,
            schema_id=_MARKER_AUTHORITY_BINDING_SCHEMA_ID,
        )

        for required_key in (
            "migration_epoch",
            "generation_reference",
            "state",
            "compatibility_fallback_forbidden",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"MarkerAuthorityBinding: missing required field {required_key!r}"
                )

        raw_duplicate_of = field_from_payload(payload, "duplicate_of")
        duplicate_of: RecordReference | None | AbsentType
        if raw_duplicate_of is ABSENT:
            duplicate_of = ABSENT
        elif raw_duplicate_of is None:
            duplicate_of = None
        else:
            duplicate_of = _marker_authority_binding_duplicate_of_from_dict(
                raw_duplicate_of, owner="MarkerAuthorityBinding.duplicate_of"
            )

        compatibility_fallback_forbidden = payload["compatibility_fallback_forbidden"]
        if not isinstance(compatibility_fallback_forbidden, bool):
            raise TypedModelConstructionError(
                "MarkerAuthorityBinding.compatibility_fallback_forbidden must be a boolean, "
                f"got {type(compatibility_fallback_forbidden)!r}"
            )

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "MarkerAuthorityBinding.migration_epoch")
            ),
            generation_reference=_generation_reference_from_dict(
                payload["generation_reference"], owner="MarkerAuthorityBinding.generation_reference"
            ),
            state=MarkerState(_require_str(payload["state"], "MarkerAuthorityBinding.state")),
            duplicate_of=duplicate_of,
            compatibility_fallback_forbidden=compatibility_fallback_forbidden,
            limitations=_limitations_from_list(
                payload["limitations"], owner="MarkerAuthorityBinding.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="MarkerAuthorityBinding.authority_disclosure"
            ),
            _extensions=_extensions_from_payload(
                payload,
                owner="MarkerAuthorityBinding",
                reserved_keys=_MARKER_AUTHORITY_BINDING_RESERVED_FIELD_NAMES,
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["generation_reference"] = serialize_value(self.generation_reference)
        result["state"] = serialize_value(self.state)
        if self.duplicate_of is not ABSENT:
            result["duplicate_of"] = (
                None if self.duplicate_of is None else serialize_value(self.duplicate_of)
            )
        result["compatibility_fallback_forbidden"] = self.compatibility_fallback_forbidden
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        if self._extensions is not ABSENT:
            result["_extensions"] = self._extensions.to_dict()
        return result


__all__ = [
    "DeliveryState",
    "NotificationAuthorityBindingUncertainty",
    "NotificationAuthorityBinding",
    "MarkerState",
    "MarkerAuthorityBinding",
]
