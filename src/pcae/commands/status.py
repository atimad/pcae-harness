from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.core.status import (
    GOVERNANCE_SYNC_CHECK_ADVISORY,
    GOVERNANCE_SYNC_REPAIR_ADVISORY,
    RESTORE_SAFETY_VALIDATION_ADVISORY,
    RUNTIME_SNAPSHOT_COMPATIBILITY_ADVISORY,
    RUNTIME_SNAPSHOT_LINEAGE_ADVISORY,
    RUNTIME_SNAPSHOT_MANIFEST_ADVISORY,
    RUNTIME_SNAPSHOT_RETENTION_ADVISORY,
    audit_governance_coherence,
    analyze_runtime_snapshot_compatibility,
    build_runtime_snapshot_lineage,
    build_runtime_snapshot_manifest,
    check_governance_sync,
    check_project_status_coherence,
    export_runtime_snapshot,
    inspect_runtime_snapshot,
    plan_governance_repairs,
    apply_governance_sync_repairs,
    plan_governance_sync_repairs,
    plan_runtime_snapshot_retention,
    preview_runtime_snapshot,
    preview_runtime_snapshot_restore,
    validate_runtime_snapshot_restore_safety,
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


def run_governance_sync_check(args: argparse.Namespace) -> int:
    result = check_governance_sync(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        status = "synchronized" if result.synchronized else "out of sync"
        print("Governance artifact synchronization check")
        print(f"Synchronization status: {status}")
        print("Operational stale references:")
        if result.operational_stale_references:
            for ref in result.operational_stale_references:
                print(f"  - {ref}")
        else:
            print("  - none")
        print("Preserved historical references:")
        if result.preserved_historical_references:
            for ref in result.preserved_historical_references:
                print(f"  - {ref}")
        else:
            print("  - none")
        print("Completed TODO entries:")
        if result.completed_todo_entries:
            for entry in result.completed_todo_entries:
                print(f"  - {entry}")
        else:
            print("  - none")
        print("Inconsistent roadmap entries:")
        if result.inconsistent_entries:
            for entry in result.inconsistent_entries:
                print(f"  - {entry}")
        else:
            print("  - none")
        print("Governance drift warnings:")
        if result.governance_drift_warnings:
            for warning in result.governance_drift_warnings:
                print(f"  - {warning}")
        else:
            print("  - none")
        print(GOVERNANCE_SYNC_CHECK_ADVISORY)
    return 0


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


def run_runtime_snapshot_validate_restore(args: argparse.Namespace) -> int:
    result = validate_runtime_snapshot_restore_safety(HarnessPath.cwd(), Path(args.path))
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        safe_label = "safe" if result.safe_to_restore else "unsafe"
        print("Governance runtime snapshot restore safety validation")
        print(f"Restore safety status: {safe_label}")
        print("Validation checks:")
        for check in result.validation_checks:
            if check.blocking and not check.passed:
                status = "blocked"
            elif not check.passed:
                status = "warn"
            else:
                status = "pass"
            print(f"  - {check.name}: {status} ({check.message})")
        print("Blocking issues:")
        if result.blocking_issues:
            for issue in result.blocking_issues:
                print(f"  - {issue}")
        else:
            print("  - none")
        print("Warnings:")
        if result.warnings:
            for warning in result.warnings:
                print(f"  - {warning}")
        else:
            print("  - none")
        print(f"Lineage continuity status: {result.lineage_status}")
        print(RESTORE_SAFETY_VALIDATION_ADVISORY)
    return 0


def run_runtime_snapshot_lineage(args: argparse.Namespace) -> int:
    result = build_runtime_snapshot_lineage(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance runtime snapshot lineage")
        print(f"Lineage chains: {len(result.lineage_chains)}")
        print(f"Lineage breaks: {len(result.lineage_breaks)}")
        if result.lineage_chains:
            for chain in result.lineage_chains:
                count = len(chain.entries)
                label = "snapshot" if count == 1 else "snapshots"
                print(f"Chain {chain.chain_index + 1} ({count} {label}):")
                for entry in chain.entries:
                    head_marker = " [head]" if entry is chain.head else ""
                    print(
                        f"  - {entry.filename}"
                        f" (exported_at={entry.exported_at},"
                        f" {entry.compatibility_status}){head_marker}"
                    )
        if result.lineage_breaks:
            print("Lineage breaks:")
            for brk in result.lineage_breaks:
                print(
                    f"  - {brk.filename}"
                    f" (exported_at={brk.exported_at},"
                    f" reason: {brk.reason})"
                )
        latest_text = (
            result.latest_head.filename
            if result.latest_head is not None
            else "none"
        )
        print(f"Latest lineage head: {latest_text}")
        print(RUNTIME_SNAPSHOT_LINEAGE_ADVISORY)
    return 0


def run_governance_sync_repair(args: argparse.Namespace) -> int:
    if not args.dry_run and not args.force:
        print(
            "Error: specify --dry-run to preview repairs or --force to apply them.",
            flush=True,
        )
        return 1

    if args.force:
        result = apply_governance_sync_repairs(HarnessPath.cwd())
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        else:
            if result.no_op:
                print("Governance sync repair: no operational repairs to apply.")
                print("Historical references are preserved as-is.")
            else:
                print("Governance sync repair applied.")
                for repair in result.applied_repairs:
                    print(
                        f"  Applied: {repair.artifact}"
                        f" — removed stale entry: {repair.stale_entry!r}"
                    )
        return 0

    # --dry-run
    result = plan_governance_sync_repairs(HarnessPath.cwd())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print("Governance synchronization repair preview")
        print(f"Repairable: {'yes' if result.repairable else 'no'}")
        print("Repair semantics:")
        print("  Operational artifacts (tasks/TODO.md, PROJECT_STATUS.md) may be updated.")
        print("  Historical artifacts (CHANGELOG.md, tasks/DONE.md) are preserved by default.")
        print("Proposed repairs:")
        if result.proposed_repairs:
            for repair in result.proposed_repairs:
                print(f"  Artifact: {repair.artifact} ({repair.artifact_type})")
                print(f"  Stale entry: {repair.stale_entry}")
                print(f"  Proposed action: {repair.proposed_action}")
                print(f"  Rationale: {repair.rationale}")
                print()
        else:
            print("  - none")
        print(GOVERNANCE_SYNC_REPAIR_ADVISORY)
        print("User remains authoritative over all repair decisions.")
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
