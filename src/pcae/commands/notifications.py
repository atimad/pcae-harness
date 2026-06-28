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
    data = {
        "notification_foundation_available": True,
        "phase": "92B",
        "sinks_available": ["noop", "stdout", "filesystem", "mock"],
        "event_types": sorted(VALID_EVENT_TYPES),
        "severities": sorted(VALID_SEVERITIES),
        "telegram_implemented": False,
        "automatic_hooks": False,
        "external_network": False,
    }

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("Notification foundation status")
        print(f"  Available:        {data['notification_foundation_available']}")
        print(f"  Phase:            {data['phase']}")
        print(f"  Sinks:            {', '.join(data['sinks_available'])}")
        print(f"  Event types:      {', '.join(data['event_types'])}")
        print(f"  Telegram:         {data['telegram_implemented']}")
        print(f"  Auto hooks:       {data['automatic_hooks']}")
        print(f"  External network: {data['external_network']}")
        print()
        print("  No Telegram, no external network, no automatic hooks.")

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
