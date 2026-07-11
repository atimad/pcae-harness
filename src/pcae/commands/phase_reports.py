"""CLI runners for pcae phase-report commands (Phase 92A).

Manual phase report creation and inspection.

Phase 128B.1 — ``pcae phase-report create`` is the documented recovery
path when ``pcae phase complete`` is rejected by the repository
transition validator (e.g. stale ``.pcae/phase-completion-metadata.json``
identity), so it now dispatches a notification for a trust-complete
report through the same certification/idempotency-marker mechanism
``pcae phase complete`` already uses (``certify_notification_transition()``
+ the shared ``.pcae/phase-reports/.last-notified.json`` marker) instead
of silently never dispatching. Dispatch remains fully governed: disabled
unless ``PCAE_NOTIFY_ENABLED=1``, skipped for a report that is not
trust-complete, and skipped (never duplicated) when the same phase_id
+ commit was already dispatched by any other governed path. See
``docs/PHASE_128B1_NOTIFICATION_DISPATCH_RELIABILITY_REPAIR.md``.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from pcae.core.phase_reports import (
    compute_finalization_snapshot_id,
    compute_report_digest,
    make_phase_report,
    build_architecture_status,
    write_phase_report,
    read_latest_report,
    write_notification_dispatch_marker,
    PhaseReport,
)

DEFAULT_REPORTS_DIR = Path(".pcae/phase-reports")


def _parse_key_value(raw: str, *, flag: str) -> tuple[str, str]:
    if "=" not in raw:
        raise ValueError(f"{flag} expects NAME=STATUS, got {raw!r}")
    name, _, value = raw.partition("=")
    name = name.strip()
    value = value.strip()
    if not name or not value:
        raise ValueError(f"{flag} expects NAME=STATUS, got {raw!r}")
    return name, value


def run_phase_report_create(args: argparse.Namespace) -> int:
    """pcae phase-report create --phase-id ... [options]

    Phase 126G — accepts structured governance/test/commit/no-go data
    directly, so a complete, trust-passing report can be produced
    through this governed command alone. Previously these fields (all
    already supported by the underlying PhaseReport/make_phase_report)
    were unreachable from this CLI, which forced operators to hand-edit
    the JSON artifact directly to reach report_completeness=complete —
    exactly the kind of unsafe workaround that caused the 126F/126G
    canonical-report/Telegram desync incident this phase repairs.
    """
    try:
        governance_results: dict[str, str] = {}
        for raw in getattr(args, "governance_result", None) or []:
            name, value = _parse_key_value(raw, flag="--governance-result")
            governance_results[name] = value

        test_results: dict[str, str] = {}
        for raw in getattr(args, "test_result", None) or []:
            name, value = _parse_key_value(raw, flag="--test-result")
            test_results[name] = value

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
            commits=list(getattr(args, "commit", None) or []),
            governance_results=governance_results,
            test_results=test_results,
            explicit_no_go_confirmations=list(getattr(args, "no_go_confirmation", None) or []),
        )
        # Phase 126G.1 — declare commit ownership in report.metadata
        # whenever --commit was explicitly supplied. assess_completeness()
        # checks report.metadata["phase_commits"]/["commit_attribution"]
        # (a separate field from the flat report.commits list) to verify
        # commit ownership is not just present but *attributed* to this
        # phase -- the same convention the internal finalize_phase_report()
        # pipeline already uses (see its own `commit_attribution` kwarg,
        # stored identically). 126G's CLI fix populated report.commits but
        # never this field, so the ownership warning fired unconditionally
        # for every report created through this command. Only set when
        # commits were actually supplied here -- if none were given, the
        # warning must correctly remain (false suppression is forbidden).
        commit_list = list(getattr(args, "commit", None) or [])
        if commit_list:
            report.metadata["commit_attribution"] = ", ".join(commit_list)
        report.metadata["phase_id"] = report.phase_id
        report.architecture_status = build_architecture_status()
        report.metadata["source_revision"] = report.architecture_status.get(
            "repository_revision", ""
        )
        # Phase 126G — assess trust completeness before writing so the
        # persisted report_completeness/missing_trust_fields reflect the
        # data actually supplied here, rather than being left permanently
        # blank (as before this fix) for every consumer that reads the
        # persisted artifact directly (e.g. notification dispatch) instead
        # of re-running `pcae phase-report trust`.
        report.apply_trust_assessment()
    except ValueError as exc:
        if args.json:
            print(json.dumps({"error": "validation_failed", "message": str(exc)}))
        else:
            print(f"Error: {exc}")
        return 1

    reports_dir = Path(getattr(args, "reports_dir", None) or DEFAULT_REPORTS_DIR)
    from pcae.core.phase_reports import notification_dispatch_state
    dispatch_state = notification_dispatch_state(
        report.phase_id,
        report_digest=compute_report_digest(report),
        finalization_snapshot_id=compute_finalization_snapshot_id(report),
    )
    if dispatch_state == "payload_conflict":
        if args.json:
            print(json.dumps({
                "error": "payload_conflict",
                "message": "ordinary completion already exists with a different bound payload",
            }, indent=2, sort_keys=True))
        else:
            print("Phase report creation: BLOCKED (ordinary-completion payload conflict)")
        return 1
    if dispatch_state == "already_dispatched":
        if args.json:
            print(json.dumps({
                "status": "skipped",
                "reason": "already_dispatched",
                "phase_id": report.phase_id,
            }, indent=2, sort_keys=True))
        else:
            print("Phase report creation: skipped (immutable ordinary completion already delivered)")
        return 0
    paths = write_phase_report(report, reports_dir)

    # Phase 128B.1 — a trust-complete report created through this manual
    # recovery command must dispatch identically to `pcae phase complete`,
    # never silently. See module docstring and _dispatch_manual_report_
    # notification()'s own docstring for the certification/idempotency
    # contract this shares with the primary finalization path.
    notification = _dispatch_manual_report_notification(report, paths)

    if args.json:
        print(json.dumps({
            "status": "created",
            "phase_id": report.phase_id,
            "paths": paths,
            "notification": notification,
        }, indent=2, sort_keys=True))
    else:
        print(f"Phase report created: {report.phase_id}")
        print(f"  Markdown: {paths['markdown']}")
        print(f"  JSON:     {paths['json']}")
        print(f"  Latest:   {paths['latest_markdown']} / {paths['latest_json']}")
        print(f"Notification dispatch: {notification['outcome']}")
        if notification.get("reason"):
            print(f"  Reason: {notification['reason']}")
        for r in notification.get("results", []):
            status = "OK" if r.get("success") else "FAILED"
            print(f"  [{r.get('sink_name', '?')}]: {status} — {r.get('message', '')}")

    return 0


def _dispatch_manual_report_notification(
    report: PhaseReport, paths: dict[str, str],
) -> dict[str, Any]:
    """Certify and dispatch a notification for a report created via
    ``pcae phase-report create``, mirroring ``pcae phase complete``'s own
    certify -> dispatch -> mark-notified sequence
    (``src/pcae/commands/phase.py``'s ``_finalize_report_and_notify()``)
    so both governed paths guarantee exactly one dispatch per trusted
    report and share the same idempotency marker.

    A report that is not trust-complete (``report.report_completeness
    != "complete"``) never dispatches here — restates the same
    "a partial report is never sent as final" rule the primary path
    already enforces, for this manual path.

    Unlike ``pcae phase complete``, this command has no completion-
    metadata file or active-task context to independently re-derive a
    phase identity from — the operator already asserted ``--phase-id``
    explicitly (that is the entire reason this command exists as a
    recovery path when the primary command's own metadata-derived
    identity check fails, e.g. 128B's stale-metadata incident). So
    identity here is deliberately NOT re-checked against
    ``.pcae/phase-completion-metadata.json`` (``metadata={}`` below) —
    doing so would simply reproduce the same rejection this recovery
    path exists to route around.
    """
    from pcae.core.notification_certification import certify_notification_transition
    from pcae.core.repository_transition_validator import TransitionKind

    if report.report_completeness != "complete":
        return {
            "outcome": "skipped",
            "reason": "report is not trust-complete; a partial report is never dispatched",
        }

    commit_hash = report.commits[0] if report.commits else ""

    try:
        from pcae.commands.phase import _read_lifecycle_current_phase_line
        lifecycle_line = _read_lifecycle_current_phase_line()
    except Exception:
        lifecycle_line = None

    active_task_title: str | None = None
    try:
        from pcae.core.paths import HarnessPath
        from pcae.core.tasks import find_latest_active_task
        active_task = find_latest_active_task(HarnessPath.cwd())
        active_task_title = active_task.title if active_task else None
    except Exception:
        active_task_title = None

    certification = certify_notification_transition(
        phase_id=report.phase_id,
        requested_phase_id=report.phase_id,
        active_task_title=active_task_title,
        metadata={},
        lifecycle_current_phase_line=lifecycle_line,
        trial_report=report,
        recommended_next_phase=report.recommended_next_phase,
        origin_main_head_count=report.origin_main_head_count,
        commit_hash=commit_hash,
        source_transition_kind=TransitionKind.REPORT_GENERATION,
        allow_partial_report=False,
    )

    if not certification.eligible:
        return {
            "outcome": certification.outcome.value,
            "reason": "; ".join(certification.reasons) or certification.outcome.value,
        }

    sink_names_raw = os.environ.get("PCAE_NOTIFY_SINKS", "filesystem")
    sink_names = [s.strip() for s in sink_names_raw.split(",") if s.strip()]
    output_dir = Path(os.environ.get("PCAE_NOTIFY_OUTPUT_DIR", ".pcae/notifications"))

    from pcae.core.notifications import (
        NoopSink,
        FilesystemSink,
        TelegramSink,
        dispatch,
        phase_report_to_notification_event,
    )

    report_path = paths.get("markdown", paths.get("latest_markdown", ""))
    event = phase_report_to_notification_event(
        report, artifact_paths=[str(report_path)] if report_path else [],
    )

    sinks = []
    for name in sink_names:
        if name == "noop":
            sinks.append(NoopSink())
        elif name == "filesystem":
            sinks.append(FilesystemSink(output_dir))
        elif name == "telegram":
            sinks.append(TelegramSink())

    if not sinks:
        return {
            "outcome": "skipped",
            "reason": "no notification sinks configured (PCAE_NOTIFY_SINKS)",
        }

    try:
        results = dispatch(event, sinks)
    except Exception as exc:
        return {"outcome": "failed", "reason": str(exc)}

    all_ok = bool(results) and all(r.success for r in results)
    if all_ok and commit_hash:
        write_notification_dispatch_marker(
            report.phase_id,
            commit_hash,
            report_digest=compute_report_digest(report),
            finalization_snapshot_id=compute_finalization_snapshot_id(report),
        )

    return {
        "outcome": "sent" if all_ok else "failed",
        "results": [r.to_dict() for r in results],
    }


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
