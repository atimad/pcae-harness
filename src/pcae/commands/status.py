from __future__ import annotations

import argparse
import json

from pcae.core.paths import HarnessPath
from pcae.core.status import audit_governance_coherence, check_project_status_coherence


def run_status_coherence(args: argparse.Namespace) -> int:
    result = check_project_status_coherence(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance status coherence")
        if result.coherent:
            print("Status: coherent")
        else:
            print("Status: warnings")
            for warning in result.warnings:
                print(f"  - warning [{warning.document}]: {warning.message}")
    return 0 if result.coherent else 1


def run_governance_audit(args: argparse.Namespace) -> int:
    result = audit_governance_coherence(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance coherence audit")
        print(f"Overall status: {result.summary.status}")
        print("Audit checks:")
        for check in result.checks:
            status = "pass" if check.passed else "fail"
            print(f"  - {check.name}: {status} ({check.message})")
        print("Warnings:")
        if result.warnings:
            for warning in result.warnings:
                print(f"  - [{warning.document}] {warning.message}")
        else:
            print("  - none")
        print("Governance coherence summary:")
        print(f"  Checks passed: {result.summary.passed_count}/{result.summary.check_count}")
        print(f"  Failed checks: {result.summary.failed_count}")
        print(f"  Warnings: {result.summary.warning_count}")
    return 0 if result.valid else 1
