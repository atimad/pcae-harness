"""Phase 136AR: Stage 3 Typed Authority Model CompatibilityState
Implementation (Typed Model Implementation Group 10, per the 136Y plan
Sec.4/Sec.34, package layout Sec.7).

Implements exactly one new record-family model: ``CompatibilityState``,
schema-backed by ``records/compatibility_state.schema.json`` (contract
Sec.34, Sec.46).

A constructed instance asserts only "this JSON was well-formed against
schema X at version Y and can be represented without loss" -- never
operational truth. ``CompatibilityState`` does not calculate, infer, or
determine compatibility; does not negotiate or select a version; does not
compare installed packages or inspect runtime versions, schema registries,
repository history, Git state, environment configuration, dependencies, or
artifacts; does not load or validate the existence of a referenced object;
does not perform, propose, or execute migration; does not transform a
record or convert a schema; does not reconcile incompatible states or
resolve conflicts; does not decide fallback behavior or activate/disable a
compatibility mode; does not determine upgrade or downgrade readiness or
safety; does not authorize or block a cutover; does not mutate lifecycle
state; does not create, quarantine, isolate, move, classify, release, or
delete any record or artifact; does not activate, resolve, determine,
compare, or transfer authority, and does not mutate an authority pointer.
It is a representation of a declared legacy-compatibility-layer
classification for one named component; it never itself performs a
migration, selects a migration adapter, rewrites a record, authorizes an
upgrade or downgrade, claims operational interoperability, mutates current
authority, or establishes semantic compatibility truth. Legacy lifecycle
remains the sole production authority; CLTR remains derivative.

No other record-family model (``QuarantineRecord``) is implemented here;
that belongs to a future, separately governed implementation group. A
module may exist with only ``CompatibilityState`` implemented while
``QuarantineRecord`` remains absent.

Tier boundary: Tier 2 (``_extensions`` permitted, string-valued map only,
Sec.14).
"""

from __future__ import annotations

import dataclasses
import enum
import re
from collections.abc import Mapping
from typing import Any

from pcae.cltr.authority.enums import AuthorityRole, CompatibilityMode
from pcae.cltr.authority.envelope import RecordEnvelope, SchemaVersionString, Timestamp
from pcae.cltr.authority.errors import (
    TypedModelConstructionError,
    TypedModelInternalInvariantError,
    UnsupportedSchemaVersionError,
)
from pcae.cltr.authority.extensions import ExtensionMapping
from pcae.cltr.authority.identity import MigrationEpochToken, RecordId
from pcae.cltr.authority.digest import RecordDigest
from pcae.cltr.authority.limitations import AuthorityDisclosure, Limitations
from pcae.cltr.authority.opaque import OpaqueJsonValue
from pcae.cltr.authority.sentinels import ABSENT, AbsentType
from pcae.cltr.authority.serialization import field_from_payload, serialize_value, to_dict_fields

# ---------------------------------------------------------------------------
# Shared local helpers (duplicated per-module, matching every sibling
# module's own precedent -- e.g. authority_core.py / publication.py /
# recovery_concurrency.py / bindings.py each define these locally rather
# than importing them from one another).
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
# CompatibilityState
# ---------------------------------------------------------------------------

_COMPATIBILITY_STATE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/compatibility_state.schema.json"
)
_COMPATIBILITY_STATE_RECORD_TYPE = "compatibility_state"
_COMPATIBILITY_STATE_SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

_COMPATIBILITY_STATE_KNOWN_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "contract_version",
        "record_type",
        "record_id",
        "record_digest",
        "created_at",
        "migration_epoch",
        "component",
        "role",
        "allowed_reads",
        "forbidden_authority_use",
        "fallback_disabled",
        "mode",
        "retirement_state",
        "limitations",
        "authority_disclosure",
        "_extensions",
    }
)

_COMPATIBILITY_STATE_RESERVED_FIELD_NAMES = frozenset(
    _COMPATIBILITY_STATE_KNOWN_KEYS - {"_extensions"}
)

_COMPONENT_MAX_LENGTH = 256
_COMPONENT_PATTERN = re.compile(r"^[\x20-\x7E]*$")

_ALLOWED_READ_PATH_MAX_LENGTH = 512
_ALLOWED_READ_PATH_PATTERN = re.compile(r"^(?!.*\.\.)[^\x00-\x1F\x7F]*$")
_MAX_ALLOWED_READS_ITEMS = 64

_MODES_RESTRICTING_AUTHORITY_ROLE = frozenset(
    {
        CompatibilityMode.LEGACY_HISTORICAL,
        CompatibilityMode.LEGACY_DISABLED,
        CompatibilityMode.LEGACY_RETIRED,
    }
)
_AUTHORITY_ROLES_PERMITTED_UNDER_RESTRICTION = frozenset(
    {AuthorityRole.HISTORICAL, AuthorityRole.COMPATIBILITY}
)


class CompatibilityRole(str, enum.Enum):
    """``CompatibilityState``'s record-local ``role`` field (Sec.34, 2
    values, home schema ``compatibility_state.schema.json``). A local
    2-value restatement of ``AuthorityRole`` (Sec.8.2) restricted to
    ``{compatibility, historical}`` (NON-BLOCKING-136V-2). Distinct from
    ``authority_disclosure.authority_role`` (the broader 7-value disclosure
    field)."""

    COMPATIBILITY = "compatibility"
    HISTORICAL = "historical"


def _validate_component(value: Any, owner: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= _COMPONENT_MAX_LENGTH):
        raise TypedModelConstructionError(
            f"{owner} must be a non-empty string of at most {_COMPONENT_MAX_LENGTH} characters"
        )
    if not _COMPONENT_PATTERN.fullmatch(value):
        raise TypedModelConstructionError(f"{owner} must be printable ASCII only")
    return value


def _validate_allowed_read_path(value: Any, owner: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= _ALLOWED_READ_PATH_MAX_LENGTH):
        raise TypedModelConstructionError(
            f"{owner} must be a non-empty string of at most {_ALLOWED_READ_PATH_MAX_LENGTH} characters"
        )
    if not _ALLOWED_READ_PATH_PATTERN.fullmatch(value):
        raise TypedModelConstructionError(
            f"{owner} must not contain the literal '..' substring or a C0/C1 control character"
        )
    return value


def _allowed_reads_from_list(value: Any, *, owner: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypedModelConstructionError(f"{owner} must be a JSON array of strings")
    if len(value) > _MAX_ALLOWED_READS_ITEMS:
        raise TypedModelConstructionError(
            f"{owner} has {len(value)} entries, exceeding the maximum of {_MAX_ALLOWED_READS_ITEMS}"
        )
    return tuple(
        _validate_allowed_read_path(entry, f"{owner}[{index}]") for index, entry in enumerate(value)
    )


def _retirement_state_from_payload(raw: Any, *, owner: str) -> OpaqueJsonValue:
    # DEFERRED-136V-1: the live schema pins retirement_state to an
    # empty-shape placeholder object (additionalProperties: false, no
    # properties) -- only {} is schema-valid pending a future contract
    # amendment. OpaqueJsonValue itself is deliberately shape-agnostic
    # (opaque.py), so that restriction must be enforced here, at the
    # field's own construction site (same pattern as
    # FinalizationReceiptAuthorityBinding.staleness_check, DEFERRED-136T-1).
    mapping = _require_mapping(raw, owner)
    if mapping:
        raise TypedModelConstructionError(
            f"{owner} must be an empty JSON object ({{}}), got keys {sorted(mapping.keys())!r}"
        )
    return OpaqueJsonValue.from_json(raw)


@dataclasses.dataclass(frozen=True)
class CompatibilityState:
    """Shape-only wire contract for a ``CompatibilityState`` companion
    record (``records/compatibility_state.schema.json``, contract Sec.34,
    Sec.46). A ``CompatibilityState`` document describes a declared
    legacy-compatibility-layer classification for one named component; it
    never itself performs a migration, selects a migration adapter,
    rewrites a record, authorizes an upgrade or downgrade, claims
    operational interoperability, mutates current authority, or
    establishes semantic compatibility truth (Sec.1, Sec.40). Legacy
    lifecycle remains the sole production authority; CLTR remains
    derivative. Tier 2 (``_extensions`` only, Sec.14).

    This model does not: calculate, infer, or determine compatibility;
    negotiate or select a version; compare installed packages; inspect
    runtime versions, dependencies, artifacts, schema registries, Git
    state, or environment configuration; load or validate the existence of
    a referenced object; perform, propose, or execute migration; transform
    a record or convert a schema; reconcile incompatible states or resolve
    conflicts; decide fallback behavior; activate or disable a
    compatibility mode; determine upgrade or downgrade readiness/safety;
    authorize or block a cutover; mutate lifecycle state; create,
    quarantine, isolate, move, classify, release, or delete any record or
    artifact; or activate, resolve, determine, compare, or transfer
    authority.
    """

    envelope: RecordEnvelope
    migration_epoch: MigrationEpochToken
    component: str
    role: CompatibilityRole
    allowed_reads: tuple[str, ...]
    fallback_disabled: bool
    mode: CompatibilityMode
    limitations: Limitations
    authority_disclosure: AuthorityDisclosure
    forbidden_authority_use: bool = True
    retirement_state: OpaqueJsonValue | AbsentType = ABSENT
    _extensions: ExtensionMapping | AbsentType = ABSENT

    def __post_init__(self) -> None:
        if self.envelope.record_type != _COMPATIBILITY_STATE_RECORD_TYPE:
            raise TypedModelInternalInvariantError(
                f"CompatibilityState.envelope.record_type must be "
                f"{_COMPATIBILITY_STATE_RECORD_TYPE!r}, got {self.envelope.record_type!r}"
            )
        if self.envelope.schema_id != _COMPATIBILITY_STATE_SCHEMA_ID:
            raise TypedModelInternalInvariantError(
                f"CompatibilityState.envelope.schema_id must be the frozen const "
                f"{_COMPATIBILITY_STATE_SCHEMA_ID!r}, got {self.envelope.schema_id!r}"
            )
        if self.forbidden_authority_use is not True:
            raise TypedModelInternalInvariantError(
                "CompatibilityState.forbidden_authority_use is a frozen const true; "
                "no model may override it locally"
            )
        # authority_role "authoritative" is locally forbidden on this
        # record family (Sec.9's 12-file list includes compatibility_state).
        if self.authority_disclosure.authority_role is AuthorityRole.AUTHORITATIVE:
            raise TypedModelInternalInvariantError(
                "CompatibilityState.authority_disclosure.authority_role must not be "
                "'authoritative': a compatibility-state record is never itself a "
                "resolved live-authority claim"
            )
        # mode <-> retirement_state conditional (Sec.34, Sec.16).
        if self.mode is CompatibilityMode.LEGACY_RETIRED:
            if self.retirement_state is ABSENT:
                raise TypedModelInternalInvariantError(
                    "CompatibilityState.retirement_state is required when mode is 'legacy_retired'"
                )
        else:
            if self.retirement_state is not ABSENT:
                raise TypedModelInternalInvariantError(
                    "CompatibilityState.retirement_state is forbidden unless mode is 'legacy_retired'"
                )
        # mode <-> authority_disclosure.authority_role conditional (Sec.34,
        # Sec.16, NON-BLOCKING-136V-3): only for legacy_historical,
        # legacy_disabled, legacy_retired; no restriction beyond the
        # unconditional "not authoritative" check above for other modes.
        if self.mode in _MODES_RESTRICTING_AUTHORITY_ROLE:
            if self.authority_disclosure.authority_role not in _AUTHORITY_ROLES_PERMITTED_UNDER_RESTRICTION:
                raise TypedModelInternalInvariantError(
                    "CompatibilityState.authority_disclosure.authority_role must be "
                    "'historical' or 'compatibility' when mode is 'legacy_historical', "
                    "'legacy_disabled', or 'legacy_retired'"
                )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, schema_version: str) -> "CompatibilityState":
        if schema_version not in _COMPATIBILITY_STATE_SUPPORTED_SCHEMA_VERSIONS:
            raise UnsupportedSchemaVersionError(
                f"CompatibilityState does not recognize schema_version {schema_version!r}"
            )
        payload = _require_mapping(payload, "CompatibilityState")
        _reject_unknown_keys(payload, _COMPATIBILITY_STATE_KNOWN_KEYS, "CompatibilityState")

        envelope = _envelope_from_payload(
            payload,
            record_type=_COMPATIBILITY_STATE_RECORD_TYPE,
            schema_id=_COMPATIBILITY_STATE_SCHEMA_ID,
        )

        for required_key in (
            "migration_epoch",
            "component",
            "role",
            "allowed_reads",
            "forbidden_authority_use",
            "fallback_disabled",
            "mode",
            "limitations",
            "authority_disclosure",
        ):
            if required_key not in payload:
                raise TypedModelConstructionError(
                    f"CompatibilityState: missing required field {required_key!r}"
                )

        if payload["forbidden_authority_use"] is not True:
            raise TypedModelConstructionError(
                "CompatibilityState.forbidden_authority_use must be the frozen const true"
            )
        if not isinstance(payload["fallback_disabled"], bool):
            raise TypedModelConstructionError("CompatibilityState.fallback_disabled must be a boolean")

        raw_retirement_state = field_from_payload(payload, "retirement_state")
        retirement_state: OpaqueJsonValue | AbsentType
        if raw_retirement_state is ABSENT:
            retirement_state = ABSENT
        else:
            retirement_state = _retirement_state_from_payload(
                raw_retirement_state, owner="CompatibilityState.retirement_state"
            )

        return cls(
            envelope=envelope,
            migration_epoch=MigrationEpochToken(
                _require_str(payload["migration_epoch"], "CompatibilityState.migration_epoch")
            ),
            component=_validate_component(payload["component"], "CompatibilityState.component"),
            role=CompatibilityRole(_require_str(payload["role"], "CompatibilityState.role")),
            allowed_reads=_allowed_reads_from_list(
                payload["allowed_reads"], owner="CompatibilityState.allowed_reads"
            ),
            forbidden_authority_use=True,
            fallback_disabled=payload["fallback_disabled"],
            mode=CompatibilityMode(_require_str(payload["mode"], "CompatibilityState.mode")),
            retirement_state=retirement_state,
            limitations=_limitations_from_list(
                payload["limitations"], owner="CompatibilityState.limitations"
            ),
            authority_disclosure=_authority_disclosure_from_dict(
                payload["authority_disclosure"], owner="CompatibilityState.authority_disclosure"
            ),
            _extensions=_extensions_from_payload(
                payload,
                owner="CompatibilityState",
                reserved_keys=_COMPATIBILITY_STATE_RESERVED_FIELD_NAMES,
            ),
        )

    def to_dict(self) -> dict:
        result = _envelope_to_dict(self.envelope)
        result["migration_epoch"] = serialize_value(self.migration_epoch)
        result["component"] = self.component
        result["role"] = serialize_value(self.role)
        result["allowed_reads"] = list(self.allowed_reads)
        result["forbidden_authority_use"] = self.forbidden_authority_use
        result["fallback_disabled"] = self.fallback_disabled
        result["mode"] = serialize_value(self.mode)
        if self.retirement_state is not ABSENT:
            result["retirement_state"] = serialize_value(self.retirement_state)
        result["limitations"] = serialize_value(self.limitations)
        result["authority_disclosure"] = serialize_value(self.authority_disclosure)
        if self._extensions is not ABSENT:
            result["_extensions"] = self._extensions.to_dict()
        return result


__all__ = [
    "CompatibilityRole",
    "CompatibilityState",
]
