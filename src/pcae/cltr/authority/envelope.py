"""``Timestamp`` and ``RecordEnvelope`` (136Y plan Sec.7, Sec.15; schema
source: ``shared/envelope.schema.json``).

Timestamps are stored as the exact original wire string, preserved
verbatim -- no timezone/format conversion, no fractional-second
truncation/padding, no re-derivation of a different precision at
construction. No timestamp establishes or is required for authority; every
timestamp is evidence-only, never proof of event-timing truth or
ordering.
"""

from __future__ import annotations

import dataclasses
import datetime as _datetime
import re

from pcae.cltr.authority.digest import RecordDigest
from pcae.cltr.authority.errors import InvalidTimestampError, TypedModelConstructionError
from pcae.cltr.authority.identity import RecordId

_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$"
)
_SCHEMA_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")


@dataclasses.dataclass(frozen=True)
class Timestamp:
    """RFC 3339 / ISO 8601 UTC timestamp, explicit ``Z`` suffix only.
    Validates shape only -- never freshness, expiry, monotonicity, causal
    order, or clock skew (Layer 4/5)."""

    wire: str

    def __post_init__(self) -> None:
        if not isinstance(self.wire, str) or not _TIMESTAMP_PATTERN.fullmatch(self.wire):
            raise InvalidTimestampError(
                "Timestamp: value does not match the required wire shape "
                "(YYYY-MM-DDTHH:MM:SS[.ffffff]Z)"
            )

    def to_datetime(self) -> _datetime.datetime:
        """A derived, non-authoritative convenience accessor computed from
        the stored string on demand. Never replaces the original string as
        the field of record for serialization -- serialization always
        emits ``self.wire``, never a re-formatted datetime."""

        normalized = self.wire[:-1] + "+00:00"  # 'Z' -> explicit UTC offset, for parsing only
        return _datetime.datetime.fromisoformat(normalized)

    def __str__(self) -> str:
        return self.wire

    def to_wire(self) -> str:
        return self.wire


@dataclasses.dataclass(frozen=True)
class SchemaVersionString:
    """A schema file's own ``MAJOR.MINOR`` version string."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _SCHEMA_VERSION_PATTERN.fullmatch(self.value):
            raise TypedModelConstructionError(
                "SchemaVersionString: value does not match the required "
                "'MAJOR.MINOR' wire shape"
            )

    def __str__(self) -> str:
        return self.value

    def to_wire(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class RecordEnvelope:
    """The 7 universal ``companion_envelope`` fields every
    ``records/*.schema.json`` file composes. Schema validity of this
    struct never establishes lifecycle authority, cutover eligibility,
    authorization, publication success, or recovery truth."""

    schema_id: str
    schema_version: SchemaVersionString
    record_type: str
    record_id: RecordId
    record_digest: RecordDigest
    created_at: Timestamp
    contract_version: str = "1.0"

    def __post_init__(self) -> None:
        if not isinstance(self.schema_id, str) or not (1 <= len(self.schema_id) <= 512):
            raise TypedModelConstructionError(
                "RecordEnvelope.schema_id must be a non-empty string of at most 512 characters"
            )
        if not isinstance(self.record_type, str) or not (1 <= len(self.record_type) <= 128):
            raise TypedModelConstructionError(
                "RecordEnvelope.record_type must be a non-empty string of at most 128 characters"
            )
        if self.contract_version != "1.0":
            raise TypedModelConstructionError(
                f"RecordEnvelope.contract_version must be the frozen const '1.0', "
                f"got {self.contract_version!r}"
            )


__all__ = ["Timestamp", "SchemaVersionString", "RecordEnvelope"]
