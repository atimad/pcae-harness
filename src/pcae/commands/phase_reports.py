"""CLI runners for pcae phase-report commands (Phase 92A).

Manual phase report creation and inspection.  No automatic hooks,
no Telegram, no notification dispatch.  Read-only except for
explicit local artifact writes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.core.phase_reports import (
    make_phase_report,
    write_phase_report,
    read_latest_report,
    PhaseReport,
)

DEFAULT_REPORTS_DIR = Path(".pcae/phase-reports")


def run_phase_report_create(args: argparse.Namespace) -> int:
    """pcae phase-report create --phase-id ... [options]"""
    try:
        report = make_phase_report(
            phase_id=args.phase_id,
            phase_name=args.phase_name,
            status=args.status,
            summary=args.summary,
            started_at=getattr(args, "started_at", None),
            completed_at=getattr(args, "completed_at", "") or "",
            files_changed=int(getattr(args, "files_changed", 0) or 0),
            tests_run=int(getattr(args, "tests_run", 0) or 0),
            pushed_status=getattr(args, "pushed_status", "") or "",
            origin_main_head_count=int(getattr(args, "origin_main_head_count", 0) or 0),
            recommended_next_phase=getattr(args, "recommended_next_phase", "") or "",
        )
    except ValueError as exc:
        if args.json:
            print(json.dumps({"error": "validation_failed", "message": str(exc)}))
        else:
            print(f"Error: {exc}")
        return 1

    reports_dir = Path(getattr(args, "reports_dir", None) or DEFAULT_REPORTS_DIR)
    paths = write_phase_report(report, reports_dir)

    if args.json:
        print(json.dumps({
            "status": "created",
            "phase_id": report.phase_id,
            "paths": paths,
        }, indent=2, sort_keys=True))
    else:
        print(f"Phase report created: {report.phase_id}")
        print(f"  Markdown: {paths['markdown']}")
        print(f"  JSON:     {paths['json']}")
        print(f"  Latest:   {paths['latest_markdown']} / {paths['latest_json']}")

    return 0


def run_phase_report_show(args: argparse.Namespace) -> int:
    """pcae phase-report show [--latest] [--json]"""
    reports_dir = Path(getattr(args, "reports_dir", None) or DEFAULT_REPORTS_DIR)

    report = read_latest_report(reports_dir)
    if report is None:
        if args.json:
            print(json.dumps({"error": "no_report", "message": "No phase report found."}))
        else:
            print("No phase report found. Create one with: pcae phase-report create ...")
        return 1

    if args.json:
        print(report.render_json())
    else:
        print(report.render_markdown())

    return 0
