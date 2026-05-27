from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.core.status import (
    RUNTIME_SNAPSHOT_COMPATIBILITY_ADVISORY,
    RUNTIME_SNAPSHOT_MANIFEST_ADVISORY,
    RUNTIME_SNAPSHOT_RETENTION_ADVISORY,
    audit_governance_coherence,
    analyze_runtime_snapshot_compatibility,
    build_runtime_snapshot_manifest,
    check_project_status_coherence,
    export_runtime_snapshot,
    inspect_runtime_snapshot,
    plan_governance_repairs,
    plan_runtime_snapshot_retention,
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
        print(f"Schema version: {result.snapshot['snapshot_schema_version']}")
        print(f"Snapshot kind: {result.snapshot['snapshot_kind']}")
        print("Compatibility status: compatible")
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
        print(f"Schema version: {result.snapshot_schema_version}")
        print(f"Snapshot kind: {result.snapshot_kind}")
        print(f"Compatibility status: {result.compatibility_status}")
        print("Compatibility notes:")
        for note in result.compatibility_notes:
            print(f"  - {note}")
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
        print(f"Restore preview status: {'ready' if result.valid else 'blocked'}")
        print(f"Snapshot validity: {'valid' if result.valid else 'invalid'}")
        print(f"Schema version: {result.snapshot_schema_version}")
        print(f"Snapshot kind: {result.snapshot_kind}")
        print(f"Compatibility status: {result.compatibility_status}")
        print("Compatibility notes:")
        for note in result.compatibility_notes:
            print(f"  - {note}")
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


def run_runtime_snapshot_compatibility(args: argparse.Namespace) -> int:
    try:
        result = analyze_runtime_snapshot_compatibility(HarnessPath.cwd(), Path(args.path))
    except ValueError as error:
        print(str(error))
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance runtime snapshot compatibility")
        print(f"Compatibility status: {'compatible' if result.compatible else 'incompatible'}")
        print(f"Snapshot kind: {result.snapshot_kind}")
        print(f"Schema version: {result.snapshot_schema_version}")
        print(f"Exported by version: {result.exported_by_version}")
        print("Compatibility checks:")
        for check in result.compatibility_checks:
            status = "pass" if check.passed else "warn"
            print(f"  - {check.name}: {status} ({check.message})")
        print("Compatibility warnings:")
        if result.compatibility_warnings:
            for warning in result.compatibility_warnings:
                print(f"  - {warning}")
        else:
            print("  - none")
        print(f"Support level: {result.support_level}")
        print(RUNTIME_SNAPSHOT_COMPATIBILITY_ADVISORY)
    return 0


def run_runtime_snapshot_manifest(args: argparse.Namespace) -> int:
    result = build_runtime_snapshot_manifest(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance runtime snapshot manifest")
        print(f"Snapshot count: {result.snapshot_count}")
        latest = result.latest_snapshot
        latest_text = "none" if latest is None else latest["filename"]
        print(f"Latest snapshot: {latest_text}")
        print("Manifest entries:")
        if result.manifest_entries:
            for entry in result.manifest_entries:
                print(
                    "  - "
                    f"{entry.filename}: exported_at={entry.exported_at}, "
                    f"kind={entry.snapshot_kind}, "
                    f"schema={entry.snapshot_schema_version}, "
                    f"exported_by={entry.exported_by_version}, "
                    f"compatibility={entry.compatibility_status}, "
                    f"support={entry.support_level}"
                )
        else:
            print("  - none")
        print("Compatibility summary:")
        for key in (
            "compatible",
            "incompatible",
            "supported",
            "partially-supported",
            "unsupported",
        ):
            print(f"  - {key}: {result.compatibility_summary[key]}")
        print(RUNTIME_SNAPSHOT_MANIFEST_ADVISORY)
    return 0


def run_runtime_snapshot_retention(args: argparse.Namespace) -> int:
    result = plan_runtime_snapshot_retention(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance runtime snapshot retention preview")
        print(f"Snapshot count: {result.snapshot_count}")
        print(f"Keep count: {result.keep_count}")
        print(f"Prune candidate count: {result.prune_candidate_count}")
        print("Snapshots to keep:")
        if result.keep:
            for entry in result.keep:
                print(f"  - {entry.filename}")
        else:
            print("  - none")
        print("Prune candidates:")
        if result.prune_candidates:
            for entry in result.prune_candidates:
                print(f"  - {entry.filename}")
        else:
            print("  - none")
        print(RUNTIME_SNAPSHOT_RETENTION_ADVISORY)
    return 0
