from __future__ import annotations

import argparse
import json

from pcae.core.analytics import (
    GovernanceRisk,
    GovernanceTrends,
    calculate_governance_risk,
    calculate_governance_trends,
)
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


def run_analytics_risk(args: argparse.Namespace) -> int:
    risk = calculate_governance_risk(HarnessPath.cwd())
    if args.json:
        print(json.dumps(analytics_risk_json_data(risk), indent=2, sort_keys=True))
    else:
        print_analytics_risk(risk)
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


def print_analytics_risk(risk: GovernanceRisk) -> None:
    print("Governance risk")
    print(f"Risk score: {risk.risk_score}")
    print(f"Risk level: {risk.risk_level}")
    print(f"Dependency warnings: {risk.dependency_warnings}")
    print(f"Session continuity: {risk.session_continuity_state}")
    print(f"Policy validation: {risk.policy_validation_state}")
    print(f"Git cleanliness: {risk.git_cleanliness}")
    print(f"Fleet drift: {risk.fleet_drift_state}")
    print("Contributing factors:")
    if not risk.contributing_factors:
        print("  none")
        return
    for factor in risk.contributing_factors:
        print(f"  {factor}")


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


def analytics_risk_json_data(risk: GovernanceRisk) -> dict[str, object]:
    return {
        "contributing_factors": list(risk.contributing_factors),
        "dependency_warnings": risk.dependency_warnings,
        "fleet_drift_state": risk.fleet_drift_state,
        "git_cleanliness": risk.git_cleanliness,
        "policy_validation_state": risk.policy_validation_state,
        "risk_level": risk.risk_level,
        "risk_score": risk.risk_score,
        "session_continuity_state": risk.session_continuity_state,
    }
