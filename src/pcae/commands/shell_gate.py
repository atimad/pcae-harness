"""CLI runners for pcae shell-gate commands.

Phase 88P: check — shell gate classifier
Phase 93B: check — broker-integrated
Phase 93C: check — audit evidence model
Phase 93E: check — audit persistence, audit show/list/verify
"""
from __future__ import annotations

import argparse
import json

from pcae.core.shell_gate import check_shell_gate
from pcae.core.paths import HarnessPath


def run_shell_gate_check(args: argparse.Namespace) -> int:
    """pcae shell-gate check --command <CMD> [--json]

    Phase 93E: Classify, evaluate via broker, produce audit evidence,
    persist audit record.  Never executes.  Simulation-only.
    """
    command_text: str = getattr(args, "command", "") or ""

    if not command_text.strip():
        if args.json:
            print(json.dumps({
                "error": "missing_command",
                "message": "No command provided. Use --command <CMD>.",
            }))
        else:
            print("Error: No command provided. Use --command <CMD>.")
        return 1

    no_audit = bool(getattr(args, "no_audit_write", False))
    data = check_shell_gate(HarnessPath.cwd().path, command_text=command_text,
                            no_audit_write=no_audit)

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        _print_check_text(data)
    return 0

def _print_check_text(data: dict) -> None:
    """Print human-readable shell-gate check output."""
    decision = data["decision"]
    hard_block = data["hard_block"]
    audit = data.get("audit_evidence", {})
    redacted = data.get("redaction_applied", False)
    persistence = data.get("audit_persistence", {})

    print("Shell gate check (simulation only — Phase 93E)")
    print(f"  Command:            {data['command_text']!r}")
    if redacted:
        print(f"  ⚠︎ Command redacted (secrets detected)")
    print(f"  Command category:   {data['command_category']}")
    print(f"  Command class:      {data['command_class']}")
    print(f"  Decision:           {decision}")
    print(f"  Hard block:         {hard_block}")
    print(f"  Reason:             {data['reason_code']}")
    if data.get("reason_codes"):
        print(f"  Reason codes:       {', '.join(data['reason_codes'])}")
    print()

    if audit:
        print(f"  Audit ID:           {audit.get('audit_id', '')}")
        print(f"  Command hash:       {audit.get('command_hash', '')[:16]}...")

    if persistence.get("status") == "written":
        print(f"  Audit persisted:    {persistence.get('latest_path', '')}")
        print(f"  Digest:             {persistence.get('record_digest', '')[:16]}...")
    elif persistence.get("status") == "failed":
        print(f"  Audit persistence:  FAILED — {persistence.get('error', 'unknown')}")

    print()
    print(f"  Simulation only:    {data['simulation_only']}")
    print(f"  No execution:       {data['no_execution']}")
    print(f"  No enforcement:     {data['no_enforcement']}")
    print()
    if hard_block:
        print("  ⚠️  HARD BLOCK — non-overridable (88V §16).")
    print("  ⚠️  Simulation only — PCAE did NOT execute, intercept, or authorize anything.")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 93E — Audit subcommands
# ═══════════════════════════════════════════════════════════════════════════════


def run_shell_gate_audit_show(args: argparse.Namespace) -> int:
    """pcae shell-gate audit show --latest [--json]"""
    from pcae.core.shell_gate import read_latest_audit

    record = read_latest_audit()
    if record is None:
        if args.json:
            print(json.dumps({"error": "no_records", "message": "No audit records found."}))
        else:
            print("No audit records found.")
        return 1

    if args.json:
        print(json.dumps(record, indent=2, sort_keys=True))
    else:
        print("Shell gate audit — latest")
        print(f"  Audit ID:      {record.get('audit_id', '')}")
        print(f"  Timestamp:     {record.get('timestamp_utc', '')}")
        print(f"  Command:       {record.get('redacted_command', '')}")
        print(f"  Decision:      {record.get('decision', '')}")
        print(f"  Hard block:    {record.get('hard_block', False)}")
        print(f"  Reason:        {record.get('reason_code', '')}")
        print(f"  Digest:        {record.get('record_digest', '')[:16]}...")
        print(f"  Persisted:     {record.get('persisted_at', '')}")
    return 0


def run_shell_gate_audit_list(args: argparse.Namespace) -> int:
    """pcae shell-gate audit list [--limit N] [--json]"""
    from pcae.core.shell_gate import list_audit_records

    limit = int(getattr(args, "limit", 10) or 10)
    records = list_audit_records(limit=limit)

    if args.json:
        print(json.dumps(records, indent=2, sort_keys=True))
    else:
        if not records:
            print("No audit records found.")
        else:
            print(f"Shell gate audit — last {len(records)} record(s)")
            for r in records:
                fname = r.get("file", "")
                dec = r.get("decision", "")
                reason = r.get("reason_code", "")
                cmd = (r.get("redacted_command", "") or "")[:50]
                print(f"  {fname}  {dec:8s}  {reason:40s}  {cmd}")
    return 0


def run_shell_gate_audit_verify(args: argparse.Namespace) -> int:
    """pcae shell-gate audit verify [--json]"""
    from pcae.core.shell_gate import verify_audit_records

    result = verify_audit_records()

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Shell gate audit verify")
        print(f"  Total:    {result['total']}")
        print(f"  Valid:    {result['valid']}")
        print(f"  Tampered: {result['tampered']}")
        print(f"  Missing:  {result['missing']}")
        if result["tampered"] > 0:
            print(f"  ⚠️  {result['tampered']} tampered record(s) detected!")
            for d in result.get("details", []):
                print(f"    {d['file']}: {d['status']}")
        else:
            print(f"  ✅  All records intact.")

    return 0 if result["tampered"] == 0 else 1
