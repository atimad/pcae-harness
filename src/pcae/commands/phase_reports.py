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
    """pcae phase-report show [--latest] [--json] [--trust]"""
    reports_dir = Path(getattr(args, "reports_dir", None) or DEFAULT_REPORTS_DIR)

    report = read_latest_report(reports_dir)
    if report is None:
        if args.json:
            print(json.dumps({"error": "no_report", "message": "No phase report found."}))
        else:
            print("No phase report found. Create one with: pcae phase-report create ...")
        return 1

    trust_payload = None
    if getattr(args, "trust", False):
        from pcae.core.phase_report_trust import (
            adapt_report_for_trust_check,
            validate_phase_report_trust,
        )
        normalized = adapt_report_for_trust_check(report.to_dict())
        result = validate_phase_report_trust(normalized)
        trust_payload = result.to_dict()
        trust_payload["phase_id"] = report.phase_id

    if args.json:
        if trust_payload is not None:
            data = json.loads(report.render_json())
            data["trust"] = trust_payload
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print(report.render_json())
    else:
        print(report.render_markdown())
        if trust_payload is not None:
            print()
            print("## Trust Gate (Phase 105B)")
            print()
            print(f"- Status: {trust_payload['status']}")
            print(f"- Complete: {trust_payload['complete']}")
            print(f"- Can be active/latest: {trust_payload['can_be_active_latest']}")
            if trust_payload["missing_fields"]:
                print(f"- Missing fields: {', '.join(trust_payload['missing_fields'])}")
            if trust_payload["placeholder_fields"]:
                print(f"- Placeholder fields: {', '.join(trust_payload['placeholder_fields'])}")

    return 0


# ═══════════════════════════════════════════════════════════════════════════
# Phase 105B — Phase Report Trust Gate CLI Integration
# ═══════════════════════════════════════════════════════════════════════════

_COMPLETION_METADATA_PATH = Path(".pcae/phase-completion-metadata.json")


def _load_json_file(path: Path) -> tuple[dict | None, str | None]:
    """Read and parse a JSON file. Returns (data, error_message). Read-only."""
    if not path.exists():
        return None, f"file not found: {path}"
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in {path}: {exc}"
    if not isinstance(data, dict):
        return None, f"expected a JSON object in {path}, found {type(data).__name__}"
    return data, None


def _collect_reports_dir_candidates(reports_dir: Path, phase_id: str | None) -> list[dict]:
    """Collect report JSON records from a phase-reports directory, excluding
    the latest.json/latest.md convenience copies. Read-only."""
    candidates: list[dict] = []
    if not reports_dir.exists():
        return candidates
    for path in sorted(reports_dir.glob("*.json")):
        if path.name == "latest.json":
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if phase_id and str(data.get("phase_id", "")) != phase_id:
            continue
        candidates.append(data)
    return candidates


def _emit_trust_error(args: argparse.Namespace, message: str) -> int:
    if args.json:
        print(json.dumps(
            {"error": "trust_check_failed", "message": message}, indent=2, sort_keys=True,
        ))
    else:
        print("Phase report trust check: ERROR")
        print(f"  {message}")
    return 2


def _emit_trust_unsupported(args: argparse.Namespace, path: Path) -> int:
    message = (
        f"markdown report parsing is not supported ({path}); "
        "use --metadata PATH for structured JSON validation, "
        "or point --report at a JSON report file."
    )
    if args.json:
        print(json.dumps({
            "error": "unsupported_report_format",
            "message": message,
            "complete": False,
            "status": "unsupported",
        }, indent=2, sort_keys=True))
    else:
        print("Phase report trust check: UNSUPPORTED")
        print(f"  {message}")
    return 2


def _print_trust_human(payload: dict, complete: bool) -> None:
    print("Phase report trust check")
    if payload.get("phase_id"):
        print(f"  Phase ID: {payload['phase_id']}")
    print(f"  Source:   {payload['source']}")
    print(f"  Status:   {payload['status']}")
    print(f"  Complete: {payload['complete']}")
    print(f"  Repair required:      {payload['repair_required']}")
    print(f"  Can be active/latest: {payload['can_be_active_latest']}")
    if payload["missing_fields"]:
        print(f"  Missing fields:     {', '.join(payload['missing_fields'])}")
    if payload["placeholder_fields"]:
        print(f"  Placeholder fields: {', '.join(payload['placeholder_fields'])}")
    if payload.get("note"):
        print(f"  Note: {payload['note']}")
    for warning in payload["warnings"]:
        print(f"  Warning: {warning}")
    print(f"  Summary:  {payload['summary']}")
    if not complete:
        print()
        print("Repair guidance:")
        for f in payload["missing_fields"]:
            print(f"  - populate missing field: {f}")
        for f in payload["placeholder_fields"]:
            print(f"  - replace disallowed placeholder value in: {f}")
        print("  This report cannot be trusted as the active/latest completion "
              "report until repaired.")


def run_phase_report_trust(args: argparse.Namespace) -> int:
    """pcae phase-report trust [--metadata PATH] [--report PATH] [--phase-id ID] [--json]

    Validates phase completion report trust (Phase 105B). Read-only —
    does not mutate any files. Non-executing, non-authorizing. Exit codes:
    0 = complete, 1 = partial/invalid, 2 = usage/IO error.
    """
    from pcae.core.phase_report_trust import (
        adapt_report_for_trust_check,
        select_active_phase_report,
        validate_phase_report_trust,
    )

    reports_dir = Path(getattr(args, "reports_dir", None) or DEFAULT_REPORTS_DIR)
    metadata_arg = getattr(args, "metadata", None)
    report_arg = getattr(args, "report", None)
    phase_id_filter = getattr(args, "phase_id", None)

    note = ""

    if metadata_arg:
        data, err = _load_json_file(Path(metadata_arg))
        if err:
            return _emit_trust_error(args, err)
        candidates = [data]
        source_kind = f"explicit metadata file: {metadata_arg}"
    elif report_arg:
        path = Path(report_arg)
        if not path.exists():
            return _emit_trust_error(args, f"file not found: {path}")
        if path.suffix.lower() == ".md":
            return _emit_trust_unsupported(args, path)
        data, err = _load_json_file(path)
        if err:
            return _emit_trust_error(args, err)
        candidates = [data]
        source_kind = f"explicit report file: {report_arg}"
    elif phase_id_filter:
        # Historical, phase-scoped selection: scan all records for this
        # phase_id and prefer a complete report over a partial one.
        candidates = _collect_reports_dir_candidates(reports_dir, phase_id_filter)
        if not candidates:
            return _emit_trust_error(
                args, f"no report found for phase_id={phase_id_filter!r} in {reports_dir}",
            )
        source_kind = f"canonical phase-reports directory (phase_id={phase_id_filter}): {reports_dir}"
    else:
        # Default: the single most-recent canonical report, not a
        # cross-phase selection (selecting "most complete across all
        # phases" would not answer "what is the latest report").
        data, err = _load_json_file(reports_dir / "latest.json")
        if data is not None:
            candidates = [data]
            source_kind = f"canonical latest report: {reports_dir / 'latest.json'}"
        else:
            data, err = _load_json_file(_COMPLETION_METADATA_PATH)
            if err:
                return _emit_trust_error(
                    args,
                    "no canonical phase report found "
                    f"(checked {reports_dir}/latest.json and {_COMPLETION_METADATA_PATH}: {err})",
                )
            candidates = [data]
            source_kind = f"pre-completion metadata draft: {_COMPLETION_METADATA_PATH}"
            note = (
                "source is a pre-completion metadata draft — status/summary "
                "are populated by `pcae phase complete`, not present in this "
                "file; their absence here is expected, not a defect."
            )

    normalized = [adapt_report_for_trust_check(c) for c in candidates if isinstance(c, dict)]
    if not normalized:
        return _emit_trust_error(args, "no valid report records found in source")

    if phase_id_filter:
        selected, result = select_active_phase_report(normalized, phase_id_filter)
        if result is None:
            return _emit_trust_error(
                args, f"no report found for phase_id={phase_id_filter!r}",
            )
        if selected is None:
            selected = normalized[-1]
    else:
        selected = normalized[0]
        result = validate_phase_report_trust(selected)

    payload = result.to_dict()
    payload["phase_id"] = selected.get("phase_id") if selected else None
    payload["source"] = source_kind
    if note:
        payload["note"] = note

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_trust_human(payload, result.complete)

    return 0 if result.complete else 1
