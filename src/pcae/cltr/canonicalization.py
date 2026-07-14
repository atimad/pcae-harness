"""Deterministic canonical serialization (135I §14).

- UTF-8, compact JSON, no insignificant whitespace.
- Object keys sorted lexicographically (byte-wise ASCII) at every nesting
  level (§14.1-§14.2).
- Set-like collections (`phase_commit_ownership`, `notification_ids`)
  sorted by natural key; sequence-like collections (`event_history`)
  preserve declared order (§14.3).
- All strings normalized to Unicode NFC before serialization (§14.4).
- Integers only, no floats; booleans as JSON true/false (§14.5-§14.6).
- `record_digest` is excluded from the canonical form used for digesting
  (§15.2-§15.4) via `include_digest=False`.
"""

from __future__ import annotations

import dataclasses
import enum
import json
import unicodedata
from collections.abc import Mapping
from typing import Any

from pcae.cltr.models import CommitOwnershipEntry, EvidenceReference, ProductionCltrRecord

#: Fields whose collection value is set-like (sorted by natural key) rather
#: than sequence-like (order-preserving), per 135I §14.3.
_SET_LIKE_FIELDS = frozenset({"phase_commit_ownership", "notification_ids", "overlay_flags"})


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _natural_key(item: Any) -> str:
    if isinstance(item, Mapping):
        for key in ("commit_hash", "evidence_id"):
            if key in item:
                return _nfc(str(item[key]))
        return _nfc(json.dumps(item, sort_keys=True, default=str))
    return _nfc(str(item))


def _to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise ValueError("floating-point values are prohibited in the CLTR canonical form (135I §14.5)")
    if isinstance(value, str):
        return _nfc(value)
    if isinstance(value, enum.Enum):
        return _nfc(str(value.value))
    if isinstance(value, (CommitOwnershipEntry, EvidenceReference)) or (
        dataclasses.is_dataclass(value) and not isinstance(value, type)
    ):
        out = {}
        for f in dataclasses.fields(value):
            field_value = getattr(value, f.name)
            out[f.name] = _to_jsonable(field_value)
        return out
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, Mapping):
        return {_nfc(str(k)): _to_jsonable(v) for k, v in value.items()}
    return value


def record_to_dict(record: ProductionCltrRecord, *, include_digest: bool = True) -> dict:
    """Convert a record to a plain, canonically-orderable dict.

    Fields whose value is ``None`` (never-reached / not-yet-applicable) are
    omitted entirely rather than emitted as ``null`` — except fields whose
    contract semantics are explicitly nullable (``task_id``,
    ``prior_state``, ``final_revision``, ``marker_id``,
    ``predecessor_transition_id``, ``successor_transition_id``,
    ``failure_classification``), which are emitted as explicit ``null``
    when unresolved (135I §8.1's absent-vs-null distinction).
    """

    explicit_nullable = {
        "task_id",
        "prior_state",
        "final_revision",
        "marker_id",
        "predecessor_transition_id",
        "successor_transition_id",
        "failure_classification",
        "report_id",
        "report_digest",
        "metadata_id",
        "metadata_digest",
        "snapshot_id",
        "snapshot_digest",
        "checkpoint_id",
        "promotion_id",
        "receipt_id",
    }

    result: dict[str, Any] = {}
    for f in dataclasses.fields(record):
        key = f.name
        if key == "record_digest" and not include_digest:
            continue
        value = getattr(record, key)
        if value is None:
            if key in explicit_nullable:
                result[key] = None
            continue
        jsonable = _to_jsonable(value)
        if isinstance(jsonable, list) and len(jsonable) == 0 and key not in _SET_LIKE_FIELDS:
            result[key] = jsonable
            continue
        if key in _SET_LIKE_FIELDS and isinstance(jsonable, list):
            jsonable = sorted(jsonable, key=_natural_key)
        result[key] = jsonable
    return result


def canonicalize(record: ProductionCltrRecord, *, include_digest: bool = True) -> bytes:
    as_dict = record_to_dict(record, include_digest=include_digest)
    return _canonical_bytes(as_dict)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonicalize_dict(value: dict) -> bytes:
    """Canonicalize an arbitrary plain dict (used by adapters/manifests)."""

    return _canonical_bytes(_to_jsonable(value))
