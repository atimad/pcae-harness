from __future__ import annotations

import argparse
import json

from pcae.core.paths import HarnessPath
from pcae.core.strategic_lineage import (
    STRATEGIC_LINEAGE_ADVISORY,
    strategic_continuity_summary,
    strategic_lineage_history,
    validate_strategic_lineage,
)


def run_strategic_continuity_show(args: argparse.Namespace) -> int:
    data = strategic_continuity_summary(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    print("Strategic Decision Continuity")
    current = data["current"]
    if current is None:
        print("Current lineage: none")
        print(f"Details: {STRATEGIC_LINEAGE_ADVISORY}")
        return 0

    print(f"Strategic Decision: {current['lineage_id']}")
    print(f"Activated: {current['activated_phase_id']} on {current['selected_branch_id']}")
    print(f"Decision Basis: {current['decision_basis']}")
    print(f"Reason: {current['rationale']}")
    print(f"Review references: {', '.join(current['review_ids']) or 'none'}")
    print("Deferred Alternatives:")
    deferred = data["deferred_alternatives"]
    if deferred:
        for alternative in deferred:
            print(
                f"  - {alternative['phase_id']} ({alternative['branch_id']}): "
                f"{alternative['reason']}"
            )
    else:
        print("  - none")
    print("Rejected Alternatives:")
    rejected = data["rejected_alternatives"]
    if rejected:
        for alternative in rejected:
            print(
                f"  - {alternative['phase_id']} ({alternative['branch_id']}): "
                f"{alternative['reason']}"
            )
    else:
        print("  - none")
    print("Referenced Review Findings:")
    referenced_findings = data["referenced_review_findings"]
    if referenced_findings:
        for reference in referenced_findings:
            print(
                f"  - {reference['review_id']}: "
                f"{reference['finding_count']} findings from review authority"
            )
    else:
        print("  - none")
    print(STRATEGIC_LINEAGE_ADVISORY)
    return 0


def run_strategic_continuity_history(args: argparse.Namespace) -> int:
    data = strategic_lineage_history(HarnessPath.cwd())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    print("Strategic Decision Continuity History")
    print(f"Records: {data['record_count']}")
    for record in data["records"]:
        print(
            f"  - {record['lineage_id']}: {record['lineage_status']} "
            f"{record['activated_phase_id']} ({record['decision_basis']})"
        )
    print(data["advisory"])
    return 0


def run_strategic_continuity_validate(args: argparse.Namespace) -> int:
    result = validate_strategic_lineage(HarnessPath.cwd())
    data = result.to_dict()
    data["advisory"] = STRATEGIC_LINEAGE_ADVISORY
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Strategic Decision Continuity Validation")
        print(f"Status: {'valid' if result.valid else 'invalid'}")
        print(f"Records: {result.record_count}")
        print(f"Active phase: {result.active_phase_id or 'none'}")
        print(f"Current lineage: {result.current_lineage_id or 'none'}")
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        print(STRATEGIC_LINEAGE_ADVISORY)
    return 0 if result.valid else 1
