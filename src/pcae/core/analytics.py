from __future__ import annotations

from dataclasses import dataclass
import json

from pcae.core.architecture import (
    ARCHITECTURE_HISTORY_RELATIVE_PATH,
    integer_value,
    string_value,
)
from pcae.core.paths import HarnessPath


@dataclass(frozen=True)
class GovernanceTrends:
    total_snapshots: int
    first_snapshot_timestamp: str | None
    latest_snapshot_timestamp: str | None
    dependency_warnings_trend: str
    max_dependency_warnings: int
    latest_dependency_warnings: int
    enforcement_modes_seen: tuple[str, ...]
    session_continuity_states_seen: tuple[str, ...]
    most_frequently_touched_zone: str | None


def calculate_governance_trends(root: HarnessPath) -> GovernanceTrends:
    entries = read_analytics_history(root)
    if not entries:
        return GovernanceTrends(
            total_snapshots=0,
            first_snapshot_timestamp=None,
            latest_snapshot_timestamp=None,
            dependency_warnings_trend="insufficient_data",
            max_dependency_warnings=0,
            latest_dependency_warnings=0,
            enforcement_modes_seen=(),
            session_continuity_states_seen=(),
            most_frequently_touched_zone=None,
        )

    warning_counts = tuple(
        integer_value(entry.get("dependency_warnings_count"))
        for entry in entries
    )
    return GovernanceTrends(
        total_snapshots=len(entries),
        first_snapshot_timestamp=string_value(entries[0].get("timestamp")),
        latest_snapshot_timestamp=string_value(entries[-1].get("timestamp")),
        dependency_warnings_trend=dependency_warning_trend(warning_counts),
        max_dependency_warnings=max(warning_counts),
        latest_dependency_warnings=warning_counts[-1],
        enforcement_modes_seen=unique_string_values(
            entry.get("enforcement_mode") for entry in entries
        ),
        session_continuity_states_seen=unique_string_values(
            entry.get("session_continuity") for entry in entries
        ),
        most_frequently_touched_zone=most_frequently_touched_zone(entries),
    )


def read_analytics_history(root: HarnessPath) -> tuple[dict, ...]:
    target = root.join(ARCHITECTURE_HISTORY_RELATIVE_PATH)
    if not target.is_file():
        raise ValueError("No architecture history found at .pcae/architecture-history.json.")

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid architecture history JSON: {error.msg}.") from error

    if not isinstance(data, list):
        raise ValueError("Invalid architecture history: expected a list of entries.")
    return tuple(entry for entry in data if isinstance(entry, dict))


def dependency_warning_trend(warning_counts: tuple[int, ...]) -> str:
    if len(warning_counts) < 2:
        return "insufficient_data"
    if warning_counts[-1] > warning_counts[0]:
        return "increasing"
    if warning_counts[-1] < warning_counts[0]:
        return "decreasing"
    return "stable"


def unique_string_values(values) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                string_value(value)
                for value in values
            }
        )
    )


def most_frequently_touched_zone(entries: tuple[dict, ...]) -> str | None:
    zone_counts: dict[str, int] = {}
    for entry in entries:
        zones = entry.get("architecture_zones_touched")
        if not isinstance(zones, dict):
            continue
        for zone_name, count in zones.items():
            if not isinstance(zone_name, str):
                continue
            zone_counts[zone_name] = zone_counts.get(zone_name, 0) + integer_value(count)

    if not zone_counts:
        return None
    return sorted(zone_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
