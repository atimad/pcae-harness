from __future__ import annotations

import argparse
import json

from pcae.core.analytics import GovernanceTrends, calculate_governance_trends
from pcae.core.paths import HarnessPath


def run_analytics_trends(args: argparse.Namespace) -> int:
    try:
        trends = calculate_governance_trends(HarnessPath.cwd())
    except ValueError as error:
        print(error)
        return 1

    if args.json:
        print(json.dumps(analytics_trends_json_data(trends), indent=2, sort_keys=True))
    else:
        print_analytics_trends(trends)
    return 0


def print_analytics_trends(trends: GovernanceTrends) -> None:
    print("Governance trends")
    print(f"Total snapshots: {trends.total_snapshots}")
    print(f"First snapshot: {trends.first_snapshot_timestamp or 'none'}")
    print(f"Latest snapshot: {trends.latest_snapshot_timestamp or 'none'}")
    print(f"Dependency warnings trend: {trends.dependency_warnings_trend}")
    print(f"Max dependency warnings: {trends.max_dependency_warnings}")
    print(f"Latest dependency warnings: {trends.latest_dependency_warnings}")
    print(
        "Enforcement modes seen: "
        f"{', '.join(trends.enforcement_modes_seen) or 'none'}"
    )
    print(
        "Session continuity states seen: "
        f"{', '.join(trends.session_continuity_states_seen) or 'none'}"
    )
    print(
        "Most frequently touched zone: "
        f"{trends.most_frequently_touched_zone or 'none'}"
    )


def analytics_trends_json_data(trends: GovernanceTrends) -> dict[str, object]:
    return {
        "dependency_warnings_trend": trends.dependency_warnings_trend,
        "enforcement_modes_seen": list(trends.enforcement_modes_seen),
        "first_snapshot_timestamp": trends.first_snapshot_timestamp,
        "latest_dependency_warnings": trends.latest_dependency_warnings,
        "latest_snapshot_timestamp": trends.latest_snapshot_timestamp,
        "max_dependency_warnings": trends.max_dependency_warnings,
        "most_frequently_touched_zone": trends.most_frequently_touched_zone,
        "session_continuity_states_seen": list(trends.session_continuity_states_seen),
        "total_snapshots": trends.total_snapshots,
    }
