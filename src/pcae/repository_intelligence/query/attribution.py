from __future__ import annotations

from typing import Any


def attribution_for_record(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return attribution already present on a snapshot record."""
    if "source_attribution" in record:
        attribution = record["source_attribution"]
        if isinstance(attribution, list):
            return attribution
    if "capability_source" in record and isinstance(record["capability_source"], dict):
        return [record["capability_source"]]
    return []


def require_attribution(record: dict[str, Any]) -> list[dict[str, Any]]:
    attribution = attribution_for_record(record)
    if not attribution:
        raise ValueError("content-bearing result record is missing attribution")
    return attribution
