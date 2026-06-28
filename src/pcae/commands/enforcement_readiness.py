"""CLI command for enforcement readiness gate status reporting.

Read-only reporter — no enforcement, no authorization, no command execution.
"""

from __future__ import annotations

import argparse

from pcae.core.enforcement_readiness import (
    ENFORCEMENT_NOT_AUTHORIZED,
    build_enforcement_readiness_report,
    format_readiness_report,
    format_readiness_report_json,
    validate_readiness_report,
)


def run_enforcement_readiness_status(args: argparse.Namespace) -> int:
    """pcae enforcement-readiness status [--json]"""
    report = build_enforcement_readiness_report()
    issues = validate_readiness_report(report)

    if args.json:
        print(format_readiness_report_json(report))
        if issues:
            print(f"\n# Validation issues: {len(issues)}")
            for issue in issues:
                print(f"#  - {issue}")
        return 0 if not issues else 1

    print(format_readiness_report(report))
    print()
    print(f"⚠️  {ENFORCEMENT_NOT_AUTHORIZED}")

    if issues:
        print(f"\nValidation issues ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    return 0
