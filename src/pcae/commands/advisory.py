"""CLI runner for pcae advisory (Phase 88X prototype)."""
from __future__ import annotations

import argparse
import json

from pcae.core.advisory import (
    ADVISORY_DECISIONS,
    build_advisory,
    build_advisory_explain,
    build_advisory_status,
)
from pcae.core.paths import HarnessPath


def run_advisory_check(args: argparse.Namespace) -> int:
    """pcae advisory check --command <CMD> [--json]"""
    command_text = getattr(args, "command", "") or ""
    data = build_advisory(
        repo_root=HarnessPath.cwd().path,
        requested_command=command_text,
        requested_action=getattr(args, "action", None),
        health_passed=_tri(getattr(args, "health_passed", None)),
        check_passed=_tri(getattr(args, "check_passed", None)),
        human_review_present=bool(getattr(args, "human_review_present", False)),
        human_approval_present=bool(getattr(args, "human_approval_present", False)),
        accepted_risk_present=bool(getattr(args, "accepted_risk_present", False)),
    )

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        _print_human_readable(data)

    return 0


def run_advisory_explain(args: argparse.Namespace) -> int:
    """pcae advisory explain --decision <DECISION> [--json]"""
    decision = getattr(args, "decision", "") or ""
    data = build_advisory_explain(decision)

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        explanation = data["explanation"]
        print(f"Advisory decision: {decision}")
        print(f"  Valid: {data['valid_decision']}")
        print(f"  Summary: {explanation.get('summary', 'N/A')}")
        print(f"  Meaning: {explanation.get('meaning', 'N/A')}")
        print(f"  Would block: {explanation.get('would_block', 'unknown')}")
        print(f"  Can override: {explanation.get('can_override', 'unknown')}")
        print(f"  Next step: {explanation.get('next_step', 'unknown')}")
        if not data["valid_decision"]:
            print(f"  Available decisions: {', '.join(ADVISORY_DECISIONS)}")

    return 0


def run_advisory_status(args: argparse.Namespace) -> int:
    """pcae advisory status [--json]"""
    data = build_advisory_status()

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        print("Advisory mode status")
        print(f"  Available: {data['advisory_mode_available']}")
        print(f"  Version: {data['advisory_mode_version']}")
        print(f"  Phase: {data['phase']}")
        print(f"  Status: {data['implementation_status']}")
        print("  Invariants:")
        for key, val in data["invariants"].items():
            print(f"    {key}: {val}")

    return 0


def _print_human_readable(data: dict) -> None:
    """Print compact human-readable advisory output."""
    decision = data["advisory_decision"]
    cmd = data["requested_command"]
    redacted = data["requested_command_redacted"]

    print("PCAE Advisory Mode — Non-Authorizing")
    print()
    print(f"  Command:       {cmd!r}" + (" (redacted)" if redacted else ""))
    print(f"  Action:        {data['requested_action']}")
    if data["requested_files"]:
        print(f"  Files:         {', '.join(data['requested_files'])}")
    print()
    print(f"  Shell Gate:    {data['shell_gate_category'] or 'N/A'}"
          f" → {data['shell_gate_decision'] or 'N/A'}")
    print(f"  Broker:        {data['broker_decision']}")
    print(f"  Advisory:      {decision}")
    print()
    if data["would_block"]:
        print(f"  Would block:   yes — {data['hard_block_reason'] or 'policy'}")
    elif data["would_deny"]:
        print(f"  Would deny:    yes")
    elif data["would_require_human_review"]:
        print(f"  Would require: human review")
    elif data["would_require_preflight"]:
        print(f"  Would require: preflight")
    elif data["would_require_active_task"]:
        print(f"  Would require: active task")
    elif data["would_require_more_evidence"]:
        print(f"  Would require: more evidence")
    else:
        print(f"  Would allow:   yes (preflight only, no execution)")
    print()
    print(f"  Hard block:    {data['hard_block_present']}")
    if data["hard_block_present"]:
        print(f"  Override:      not possible (hard blocks cannot be overridden)")
    print()
    if data["redaction_applied"]:
        print(f"  Redaction:     applied — {data['redaction_reason']}")
    print(f"  Safe to show:  {data['safe_to_display']}")
    print()
    print(f"  Operator:      {data['operator_message']}")
    print(f"  Next action:   {data['next_required_action']}")
    print()
    print(f"  Authorization: not granted")
    print(f"  Execution:     not authorized")
    print(f"  Enforcement:   not applied")
    print()
    print("  Advisory mode is non-authorizing. PCAE does not execute, block,")
    print("  or intercept commands. Operator retains full authority.")


def _tri(value: object) -> bool | None:
    """Convert argparse tri-state (None / True / False) to bool | None."""
    if value is True:
        return True
    if value is False:
        return False
    return None
