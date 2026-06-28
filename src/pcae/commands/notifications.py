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

    event = phase_report_to_notification_event(
        report,
        artifact_paths=[str(reports_dir / "latest.md")],
    )

    sink = TelegramSink()
    results = dispatch(event, [sink])

    if args.json:
        print(json.dumps({
            "event": event.to_dict(),
            "results": [r.to_dict() for r in results],
        }, indent=2, sort_keys=True))
    else:
        print(f"Telegram send-report: {report.phase_name}")
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
