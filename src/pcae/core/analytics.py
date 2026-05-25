from __future__ import annotations

from dataclasses import dataclass
import json

from pcae.core.architecture import (
    ARCHITECTURE_HISTORY_RELATIVE_PATH,
    integer_value,
    string_value,
)
from pcae.core.check import run_checks
from pcae.core.fleet import build_fleet_drift
from pcae.core.health import build_health_data
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


@dataclass(frozen=True)
class GovernanceRisk:
    risk_score: int
    risk_level: str
    contributing_factors: tuple[str, ...]
    dependency_warnings: int
    session_continuity_state: str
    policy_validation_state: str
    git_cleanliness: str
    fleet_drift_state: str


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


def calculate_governance_risk(root: HarnessPath) -> GovernanceRisk:
    health = build_health_data(root)
    check = run_checks(root)
    factors: list[str] = []
    score = 0

    if health["policy_validation"] != "valid":
        score += 40
        factors.append("invalid policy")

    if health["violations"]:
        score += 40
        factors.append("check violations")

    session_state = string_value(health["session_continuity"])
    if session_state in {"mismatch", "invalid"}:
        score += 20
        factors.append(f"session {session_state}")

    history_dependency_warnings = health["latest_dependency_warnings"]
    if not isinstance(history_dependency_warnings, int):
        history_dependency_warnings = 0
    dependency_warnings = max(
        history_dependency_warnings,
        len(check.architecture_dependency_warnings),
    )
    if dependency_warnings > 0:
        score += 15
        factors.append("dependency warnings")

    git_cleanliness = "clean" if health["git_status"] == "clean" else "dirty"
    if git_cleanliness == "dirty":
        score += 10
        factors.append("dirty git status")

    try:
        read_analytics_history(root)
    except ValueError:
        score += 5
        factors.append("missing architecture history")

    fleet_drift = build_fleet_drift(root)
    fleet_drift_state = "detected" if fleet_drift["drift_detected"] else "none"
    if fleet_drift_state == "detected":
        score += 15
        factors.append("fleet drift detected")

    capped_score = min(score, 100)
    return GovernanceRisk(
        risk_score=capped_score,
        risk_level=risk_level_for_score(capped_score),
        contributing_factors=tuple(factors),
        dependency_warnings=dependency_warnings,
        session_continuity_state=session_state,
        policy_validation_state=string_value(health["policy_validation"]),
        git_cleanliness=git_cleanliness,
        fleet_drift_state=fleet_drift_state,
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


def risk_level_for_score(score: int) -> str:
    if score >= 60:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


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
