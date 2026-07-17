"""Shared ``to_dict``/``from_dict`` primitives (136Y plan Sec.16-17).

These are the Layer-3 construction/serialization primitives shared by
every typed model built in a future group. This module makes no semantic
decisions, performs no I/O, no network access, and no filesystem writes.

Canonical byte production reuses ``pcae.cltr.canonicalization`` unchanged,
as a thin pass-through wrapper -- never a new canonicalization
implementation.
"""

from __future__ import annotations

import dataclasses
import enum
from collections.abc import Mapping
from typing import Any

from pcae.cltr.authority.errors import SerializationError
from pcae.cltr.authority.extensions import ExtensionMapping
from pcae.cltr.authority.opaque import OpaqueJsonValue
from pcae.cltr.authority.sentinels import ABSENT
from pcae.cltr.canonicalization import canonicalize_dict


def field_from_payload(payload: Mapping[str, Any], key: str) -> Any:
    """Distinguish "key not present in payload" (returns ``ABSENT``) from
    "key present with an explicit value, including ``None``" (returns that
    value). The distinction is made by ``key in payload`` versus
    ``payload[key]``, never by ``payload.get(key)`` alone, which cannot
    distinguish the two cases."""

    if key not in payload:
        return ABSENT
    return payload[key]


def serialize_value(value: Any) -> Any:
    """Recursively convert a shared-core typed value into a JSON-
    compatible plain Python value. ``ABSENT`` must be filtered by the
    caller (``to_dict_fields``) before reaching this function -- it is
    never itself a valid serialized value."""

    if value is ABSENT:
        raise SerializationError(
            "ABSENT must be omitted by the caller before calling serialize_value"
        )
    if value is None:
        return None
    if isinstance(value, enum.Enum):
        # Checked before the scalar-type branch below: a `str`-mixin Enum
        # member is itself a `str` instance, so this ordering is required
        # to emit the plain wire value rather than the Enum instance.
        return value.value
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, OpaqueJsonValue):
        return value.to_json()
    if isinstance(value, ExtensionMapping):
        return value.to_dict()
    to_wire = getattr(value, "to_wire", None)
    if callable(to_wire) and dataclasses.is_dataclass(value):
        return to_wire()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return to_dict_fields(value)
    if isinstance(value, (list, tuple)):
        return [serialize_value(v) for v in value]
    if isinstance(value, Mapping):
        return {str(k): serialize_value(v) for k, v in value.items()}
    raise SerializationError(
        f"unsupported value type for serialization: {type(value)!r}"
    )


def to_dict_fields(instance: Any) -> dict:
    """``to_dict()`` for any frozen dataclass built from these shared
    primitives: every field whose value ``is ABSENT`` is omitted entirely;
    every other field's value is recursively serialized."""

    result: dict[str, Any] = {}
    for f in dataclasses.fields(instance):
        value = getattr(instance, f.name)
        if value is ABSENT:
            continue
        result[f.name] = serialize_value(value)
    return result


def to_canonical_bytes(value: dict) -> bytes:
    """Thin pass-through wrapper around
    ``pcae.cltr.canonicalization.canonicalize_dict`` -- never a new
    canonicalization implementation."""

    return canonicalize_dict(value)


__all__ = [
    "field_from_payload",
    "serialize_value",
    "to_dict_fields",
    "to_canonical_bytes",
]
