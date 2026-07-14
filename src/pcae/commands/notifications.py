"""CLI runners for pcae notify commands (Phase 92B).

Manual notification testing and status.  No Telegram, no external
network calls, no automatic hooks.  Read-only except for explicit
filesystem sink writes via --sink filesystem.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcae.core.notifications import (
    NotificationEvent,
    make_notification_event,
    NoopSink,
    StdoutSink,
    FilesystemSink,
    dispatch,
    VALID_EVENT_TYPES,
    VALID_SEVERITIES,
    EVENT_TYPE_MANUAL_TEST,
)


def run_notify_status(args: argparse.Namespace) -> int:
    """pcae notify status [--json]"""
    import os
    from pcae.core.notifications import TelegramSink

    # Check Telegram configuration (without printing secrets)
    tg_token = os.environ.get("PCAE_TELEGRAM_BOT_TOKEN", "")
    tg_chat_id = os.environ.get("PCAE_TELEGRAM_CHAT_ID", "")
    tg_enabled = os.environ.get("PCAE_TELEGRAM_ENABLED", "").lower() in ("1", "true", "yes")
    tg_configured = bool(tg_token and tg_chat_id)
    tg_active = tg_enabled and tg_configured

    notify_enabled = os.environ.get("PCAE_NOTIFY_ENABLED", "").lower() in ("1", "true", "yes")
    notify_sinks_raw = os.environ.get("PCAE_NOTIFY_SINKS", "")
    notify_sinks = [s.strip() for s in notify_sinks_raw.split(",") if s.strip()]

    data = {
        "notification_foundation_available": True,
        "foundation_phase": "92B",
        "phase": "92D",
        "sinks_available": ["noop", "stdout", "filesystem", "mock", "telegram"],
        "event_types": sorted(VALID_EVENT_TYPES),
        "severities": sorted(VALID_SEVERITIES),
        "telegram_sink_available": True,
        "telegram_configured": tg_configured,
        "telegram_enabled": tg_active,
        "telegram_token_present": bool(tg_token),
        "telegram_chat_id_present": bool(tg_chat_id),
        "auto_finalization_hook_available": True,
        "notification_dispatch_default": "disabled",
        "notify_enabled": notify_enabled,
        "configured_sinks": notify_sinks,
        "external_network_possible": tg_active,
        "external_network_active_by_default": False,
    }

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Notification foundation status")
        print(f"  Available:              {data['notification_foundation_available']}")
        print(f"  Foundation phase:       {data['foundation_phase']}")
        print(f"  Current phase:          {data['phase']}")
        print(f"  Sinks:                  {', '.join(data['sinks_available'])}")
        print()
        print("  Telegram sink:")
        print(f"    Available:            {data['telegram_sink_available']}")
        print(f"    Configured:           {data['telegram_configured']}")
        print(f"    Enabled:              {data['telegram_enabled']}")
        print(f"    Token:                {'present' if tg_token else 'missing'}")
        print(f"    Chat ID:              {'present' if tg_chat_id else 'missing'}")
        print()
        print("  Auto finalization hook:")
        print(f"    Available:            {data['auto_finalization_hook_available']}")
        print(f"    Notify default:       {data['notification_dispatch_default']}")
        print(f"    Notify enabled:       {data['notify_enabled']}")
        if notify_sinks:
            print(f"    Configured sinks:     {', '.join(notify_sinks)}")
        print()
        print("  External network:")
        print(f"    Possible:             {data['external_network_possible']}")
        print(f"    Active by default:    {data['external_network_active_by_default']}")
        print()
        # Context-sensitive status text
        if tg_active and notify_enabled:
            print("  ✅ Telegram is configured, enabled, and ready for outbound delivery.")
            print("  Notifications will dispatch on pcae phase complete when PCAE_NOTIFY_ENABLED=1.")
        elif tg_configured and not tg_enabled:
            print("  Telegram is configured but disabled (PCAE_TELEGRAM_ENABLED not set).")
            print("  Set PCAE_TELEGRAM_ENABLED=1 to enable Telegram outbound delivery.")
        elif notify_enabled and not tg_configured:
            print("  Notifications are enabled but Telegram is not configured.")
            print("  Set PCAE_TELEGRAM_BOT_TOKEN and PCAE_TELEGRAM_CHAT_ID.")
        else:
            print("  Telegram is available but disabled unless configured.")
            print("  Auto finalization hook creates reports; notify dispatch is opt-in.")
            print("  Set PCAE_NOTIFY_ENABLED=1 to enable notification dispatch.")

    return 0


def run_notify_test(args: argparse.Namespace) -> int:
    """pcae notify test --sink <sink> [--output-dir <path>] [--json]"""
    sink_name: str = getattr(args, "sink", "noop") or "noop"

    event = make_notification_event(
        event_type=EVENT_TYPE_MANUAL_TEST,
        title="Manual notification test",
        message="This is a manual test notification from PCAE 92B.",
        severity="info",
    )

    is_json = bool(getattr(args, "json", False))

    if sink_name == "noop":
        sink = NoopSink()
    elif sink_name == "stdout":
        sink = StdoutSink(write=not is_json)  # Don't write to stdout in JSON mode
    elif sink_name == "filesystem":
        output_dir = Path(getattr(args, "output_dir", None) or ".pcae/notifications")
        sink = FilesystemSink(output_dir)
    elif sink_name == "mock":
        from pcae.core.notifications import MockSink
        sink = MockSink()
    else:
        msg = f"Unknown sink: {sink_name!r}. Available: noop, stdout, filesystem, mock"
        if args.json:
            print(json.dumps({"error": "unknown_sink", "message": msg}))
        else:
            print(f"Error: {msg}")
        return 1

    results = dispatch(event, [sink])

    if args.json:
        print(json.dumps({
            "event": event.to_dict(),
            "results": [r.to_dict() for r in results],
        }, indent=2, sort_keys=True))
    else:
        print(f"Notification test: {sink_name}")
        for r in results:
            status = "OK" if r.success else "FAILED"
            print(f"  [{status}] {r.message}")
            if r.error:
                print(f"    Error: {r.error}")

    return 0 if all(r.success for r in results) else 1


def run_notify_send_report(args: argparse.Namespace) -> int:
    """pcae notify send-report [--latest] [--json]

    Reads the latest phase report and sends it via Telegram.
    Manual command only — no automatic hooks.  No inbound commands.
    """
    from pcae.core.phase_reports import read_latest_report
    from pcae.core.notifications import (
        TelegramSink, phase_report_to_notification_event, dispatch,
    )

    reports_dir = Path(getattr(args, "reports_dir", None) or ".pcae/phase-reports")
    report = read_latest_report(reports_dir)

    if report is None:
        msg = "No latest phase report found. Create one with: pcae phase-report create ..."
        if args.json:
            print(json.dumps({"error": "no_report", "message": msg}))
        else:
            print(f"Error: {msg}")
        return 1

    # ── Phase 95M.1 — Finalization gate before Telegram send ─────────────
    from pcae.core.phase_reports import validate_finalization_gate
    from pcae.commands.phase import _load_completion_metadata as _lcm
    meta = _lcm()
    gate = validate_finalization_gate(
        phase_id=report.phase_id,
        report=report,
        metadata=meta,
        pushed_status=report.pushed_status,
        origin_main_head_count=report.origin_main_head_count,
        governance_results=report.governance_results,
        test_results=report.test_results,
        no_go_confirmations=report.explicit_no_go_confirmations,
        recommended_next_phase=report.recommended_next_phase,
        commit_attribution=meta.get("commit_attribution", ""),
    )
    if not gate["finalizable"]:
        if args.json:
            print(json.dumps({
                "error": "finalization_gate_failed",
                "finalizable": False,
                "blockers": gate["blockers"],
                "message": "Report is not finalizable. Repair before sending.",
            }, indent=2))
        else:
            print("Telegram send-report: BLOCKED by finalization gate")
            print("  Report is not finalizable. Repair before sending.")
            for blocker in gate["blockers"]:
                print(f"  Blocker: {blocker}")
        return 1

    # Phase 128B.1 — idempotency: `pcae notify send-report --latest` is a
    # documented recovery/manual re-send command (named explicitly by the
    # phase-finalization skill's own hint text) that must not duplicate a
    # notification `pcae phase complete` or `pcae phase-report create`
    # already dispatched for the same phase_id+commit. Shares the exact
    # same marker `write_notification_dispatch_marker()` writes to, so
    # "already dispatched" is true regardless of which governed path sent
    # it first.
    from pcae.core.phase_reports import (
        compute_finalization_snapshot_id,
        compute_report_digest,
        notification_dispatch_state,
        write_notification_dispatch_marker,
    )
    commit_hash = report.commits[0] if report.commits else ""
    report_digest = compute_report_digest(report)
    snapshot_id = compute_finalization_snapshot_id(report)
    dispatch_state = notification_dispatch_state(
        report.phase_id,
        report_digest=report_digest,
        finalization_snapshot_id=snapshot_id,
    )
    if dispatch_state == "payload_conflict":
        msg = (
            f"phase {report.phase_id} already has an ordinary completion with "
            "a different bound report digest or finalization snapshot"
        )
        if args.json:
            print(json.dumps({
                "error": "payload_conflict",
                "message": msg,
            }, indent=2, sort_keys=True))
        else:
            print("Telegram send-report: BLOCKED (payload conflict)")
            print(f"  Reason: {msg}")
        return 1
    if dispatch_state == "already_dispatched":
        msg = (
            f"phase {report.phase_id} final report already dispatched at commit "
            f"{commit_hash[:8]} — skipping duplicate send (idempotent)"
        )
        if args.json:
            print(json.dumps({
                "status": "skipped",
                "reason": "already_dispatched",
                "message": msg,
            }, indent=2, sort_keys=True))
        else:
            print("Telegram send-report: skipped (idempotent — already dispatched)")
            print(f"  Reason: {msg}")
        return 0

    event = phase_report_to_notification_event(
        report,
        artifact_paths=[str(reports_dir / "latest.md")],
    )

    # Phase 134E.10.1 — transaction-span repair: this entry point has no
    # promotion step of its own (the report was already promoted by a prior
    # entry point's run) -- only dispatch. Dispatch still now happens
    # INSIDE the authoritative finalization transaction, gated on the seven
    # newly-integrated modules' mandatory pre-promotion stages succeeding
    # first. `gate["finalizable"]` was already confirmed True earlier in
    # this function (the earlier `if not gate["finalizable"]: return 1`
    # check), so the transaction is entered unconditionally here.
    sink = TelegramSink()

    def _promote_and_dispatch() -> dict:
        dispatch_results = dispatch(event, [sink])
        dispatch_all_ok = bool(dispatch_results) and all(r.success for r in dispatch_results)
        if dispatch_all_ok and commit_hash:
            write_notification_dispatch_marker(
                report.phase_id,
                commit_hash,
                report_digest=report_digest,
                finalization_snapshot_id=snapshot_id,
            )
        report.notification_result = {
            "dispatched": bool(dispatch_results),
            "sinks": [r.sink_name for r in dispatch_results],
            "success": dispatch_all_ok,
            "error": None,
            "outcome": "sent" if dispatch_all_ok else "failed",
            "reason": "",
            "kind": "complete",
        }
        return {"report": report, "results": dispatch_results}

    from pcae.core.finalization_transaction import run_finalization_transaction
    txn_result = run_finalization_transaction(
        phase_id=report.phase_id,
        phase_name=report.phase_name,
        report=report,
        gate=gate,
        promote_and_dispatch=_promote_and_dispatch,
        entry_point="notify_send_report",
    )
    if txn_result.status in (
        "pre_promotion_certification_failed", "promotion_and_dispatch_failed",
    ):
        if args.json:
            print(json.dumps({
                "error": txn_result.status,
                "limitations": txn_result.limitations,
            }, indent=2, sort_keys=True))
        else:
            print(f"Telegram send-report: BLOCKED ({txn_result.status})")
            for limitation in txn_result.limitations:
                print(f"  {limitation}")
        return 1
    dispatch_outcome = txn_result.promotion_and_dispatch or {}
    results = dispatch_outcome.get("results", [])

    if args.json:
        print(json.dumps({
            "event": event.to_dict(),
            "results": [r.to_dict() for r in results],
        }, indent=2, sort_keys=True))
    else:
        print(f"Telegram send-report")
        print(f"  Phase:   {report.phase_id} — {report.phase_name}")
        print(f"  Status:  {report.status}")
        print(f"  Report:  {reports_dir / 'latest.md'}")
        for r in results:
            status = "OK" if r.success else "FAILED"
            print(f"  [{status}] {r.message}")
            if r.error:
                print(f"    Error: {r.error}")
        if not sink.is_configured():
            print()
            print("  Configure with environment variables:")
            print("    PCAE_TELEGRAM_BOT_TOKEN")
            print("    PCAE_TELEGRAM_CHAT_ID")
            print("    PCAE_TELEGRAM_ENABLED=1")

    return 0 if all(r.success for r in results) else 1
