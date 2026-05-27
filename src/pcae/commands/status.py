from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.core.status import (
    audit_governance_coherence,
    check_project_status_coherence,
    export_runtime_snapshot,
    inspect_runtime_snapshot,
    plan_governance_repairs,
    preview_runtime_snapshot,
    preview_runtime_snapshot_restore,
)


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


def run_governance_repair(args: argparse.Namespace) -> int:
    result = plan_governance_repairs(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance repair planning preview")
        print(f"Overall repairability status: {'repairable' if result.repairable else 'not repairable'}")
        print("Detected issues:")
        if result.detected_issues:
            for issue in result.detected_issues:
                print(f"  - {issue}")
        else:
            print("  - none")
        print("Proposed repairs:")
        if result.proposed_repairs:
            for repair in result.proposed_repairs:
                print(f"  - {repair}")
        else:
            print("  - none")
        print("Repair safety notes:")
        for note in result.safety_notes:
            print(f"  - {note}")
        print(result.advisory)
    return 0


def run_runtime_snapshot(args: argparse.Namespace) -> int:
    result = preview_runtime_snapshot(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance runtime snapshot preview")
        print(f"Snapshot readiness: {'ready' if result.snapshot_ready else 'not ready'}")
        print("Included runtime sections:")
        for section in result.included_sections:
            print(f"  - {section}")
        print("Portability notes:")
        for note in result.portability_notes:
            print(f"  - {note}")
        print("Safety notes:")
        for note in result.safety_notes:
            print(f"  - {note}")
        print(result.advisory)
    return 0


def run_runtime_snapshot_export(args: argparse.Namespace) -> int:
    result = export_runtime_snapshot(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance runtime snapshot export")
        print(f"Export path: {result.export_path.as_posix()}")
        print(f"Snapshot readiness: {'ready' if result.snapshot_ready else 'not ready'}")
    return 0


def run_runtime_snapshot_inspect(args: argparse.Namespace) -> int:
    try:
        result = inspect_runtime_snapshot(HarnessPath.cwd(), Path(args.path))
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance runtime snapshot inspection")
        print(f"Snapshot validity: {'valid' if result.valid else 'invalid'}")
        print(f"Exported timestamp: {result.exported_at}")
        print("Included sections:")
        for section in result.included_sections:
            print(f"  - {section}")
        print("Portability notes:")
        for note in result.portability_notes:
            print(f"  - {note}")
        print("Safety notes:")
        for note in result.safety_notes:
            print(f"  - {note}")
        print(result.advisory)
    return 0


def run_runtime_snapshot_restore(args: argparse.Namespace) -> int:
    try:
        result = preview_runtime_snapshot_restore(HarnessPath.cwd(), Path(args.path))
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance runtime snapshot restore preview")
        print("Restore preview status: ready")
        print(f"Snapshot validity: {'valid' if result.valid else 'invalid'}")
        print("Sections that would be restored:")
        for section in result.would_restore:
            print(f"  - {section}")
        print("Sections that would NOT be restored yet:")
        for section in result.would_not_restore:
            print(f"  - {section}")
        print("Safety notes:")
        for note in result.safety_notes:
            print(f"  - {note}")
        print(result.advisory)
    return 0
