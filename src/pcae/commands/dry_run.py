"""CLI runner for pcae dry-run (Phase 89C prototype)."""
from __future__ import annotations

import argparse
import json

from pcae.core.dry_run import (
    SIMULATION_DECISIONS,
    build_simulation,
    build_simulation_explain,
    build_simulation_status,
)
from pcae.core.paths import HarnessPath


def run_dry_run_check(args: argparse.Namespace) -> int:
    """pcae dry-run check --command <CMD> [--json]"""
    command_text = getattr(args, "command", "") or ""
    data = build_simulation(
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

    # Differentiated exit codes (89B §14): 0=allow, 1=blocked/deny, 2=error
    if data["simulation_severity"] in ("blocked",):
        return 1
    return 0


def run_dry_run_explain(args: argparse.Namespace) -> int:
    """pcae dry-run explain --decision <DECISION> [--json]"""
    decision = getattr(args, "decision", "") or ""
    data = build_simulation_explain(decision)

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        explanation = data["explanation"]
        print(f"Simulation decision: {decision}")
        print(f"  Valid: {data['valid_decision']}")
        print(f"  Severity: {data.get('severity', 'unknown')}")
        print(f"  Summary: {explanation.get('summary', 'N/A')}")
        print(f"  Meaning: {explanation.get('meaning', 'N/A')}")
        print(f"  Would block: {explanation.get('would_block', 'unknown')}")
        print(f"  Can override: {explanation.get('can_override', 'unknown')}")
        print(f"  Next step: {explanation.get('next_step', 'unknown')}")
        gov = data.get("governed_alternative")
        if gov:
            print(f"  Governed alternative: {gov}")
        enf = data.get("enforcement_readiness")
        if enf:
            print(f"  Enforcement readiness: {enf}")
        if not data["valid_decision"]:
            print(f"  Available decisions: {', '.join(SIMULATION_DECISIONS)}")

    return 0


def run_dry_run_status(args: argparse.Namespace) -> int:
    """pcae dry-run status [--json]"""
    data = build_simulation_status()

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        print("Dry-run blocking simulation status")
        print(f"  Available: {data['simulation_mode_available']}")
        print(f"  Version: {data['simulation_mode_version']}")
        print(f"  Phase: {data['phase']}")
        print(f"  Design: {data['design_source']}")
        print(f"  Enforcement stage: {data['enforcement_stage']}")
        print(f"  Status: {data['implementation_status']}")
        print("  Invariants:")
        for key, val in data["invariants"].items():
            print(f"    {key}: {val}")
        print("  Known limitations:")
        for lim in data["known_limitations"]:
            print(f"    - {lim}")

    return 0


def _print_human_readable(data: dict) -> None:
    """Print human-readable simulation output (89B §19)."""
    decision = data["simulation_decision"]
    cmd = data["requested_command"]
    redacted = data["requested_command_redacted"]
    severity = data["simulation_severity"]
    severity_label = data.get("simulation_severity_label", severity.upper())

    # Severity header
    indicators = {
        "info": "ℹ️  INFO",
        "caution": "⚠️  CAUTION",
        "review_required": "👁️  REVIEW REQUIRED",
        "blocked": "🚫 SIMULATED BLOCK",
        "unknown": "❓ UNKNOWN",
    }
    header = indicators.get(severity, f"[{severity_label}]")

    print(f"PCAE Dry-Run Simulation — {header}")
    print("Simulation only. No enforcement occurred.")
    print()
    print(f"  Command:       {cmd!r}" + (" (redacted)" if redacted else ""))
    print(f"  Action:        {data['requested_action']}")
    if data.get("requested_files"):
        print(f"  Files:         {', '.join(data['requested_files'])}")
    print()
    print(f"  Shell Gate:    {data['shell_gate_category'] or 'N/A'}"
          f" → {data['shell_gate_decision'] or 'N/A'}")
    print(f"  Broker:        {data['broker_decision']}")
    print(f"  Simulation:    {decision}")
    print()

    # Block/review/require/allow section
    if data["would_block"]:
        print(f"  ┌─ SIMULATED BLOCK ────────────────────────────────────┐")
        print(f"  │  SIMULATED: {decision}")
        if data["hard_block_present"]:
            print(f"  │  HARD BLOCK. Cannot be overridden by human approval")
            print(f"  │  or accepted risk.")
        print(f"  │  Under real enforcement, this command WOULD BE")
        print(f"  │  BLOCKED. This simulation did not enforce any block.")
        gov = data.get("governed_alternative")
        if gov:
            print(f"  │")
            print(f"  │  Governed alternative: {gov}")
        print(f"  └──────────────────────────────────────────────────────┘")
    elif data["would_deny"]:
        print(f"  ┌─ SIMULATED DENY ────────────────────────────────────┐")
        print(f"  │  SIMULATED: would_deny")
        print(f"  │  Under real enforcement, this command would be")
        print(f"  │  unconditionally DENIED.")
        print(f"  └──────────────────────────────────────────────────────┘")
    elif data["would_require_human_review"]:
        print(f"  ┌─ REVIEW REQUIRED ───────────────────────────────────┐")
        print(f"  │  SIMULATED: would_require_human_review")
        print(f"  │  Under enforcement, human review would be required.")
        print(f"  │  Human review is not authorization.")
        print(f"  │  Human review would change outcome: {'yes' if data['human_approval_would_change_outcome'] else 'no'}")
        print(f"  └──────────────────────────────────────────────────────┘")
    elif data["would_require_preflight"]:
        print(f"  Would require: preflight")
    elif data["would_require_active_task"]:
        print(f"  Would require: active task")
    elif data["would_require_more_evidence"]:
        print(f"  Would require: more evidence")
        if data.get("missing_evidence"):
            for item in data["missing_evidence"]:
                print(f"    - {item}")
    else:
        print(f"  Would allow: yes (preflight only, no execution)")
    print()

    if data["hard_block_present"]:
        print(f"  Hard block:    yes — {data.get('hard_block_reason', 'policy')}")
        print(f"  Override:      not possible (hard blocks cannot be overridden)")
    else:
        print(f"  Hard block:    none")
    print()

    if data["redaction_applied"]:
        print(f"  Redaction:     applied — {data.get('redaction_reason', 'policy')}")
    else:
        print(f"  Redaction:     not applied")
    print(f"  Safe to show:  {data['safe_to_display']}")
    print()

    enf = data.get("enforcement_readiness", "")
    if enf:
        print(f"  Enforcement:   {enf}")
        print()

    print(f"  Next action:   {data['next_required_action']}")
    print()
    print(f"  Authorization: not granted")
    print(f"  Execution:     not authorized")
    print(f"  Enforcement:   not applied")
    print(f"  Interception:  not applied")
    print()
    print("  ────────────────────────────────────────────────────────")
    print("  ⚠️  Dry-run simulation complete. No enforcement occurred.")
    print()
    print("      • No command was executed.")
    print("      • No shell was intercepted.")
    print("      • No authorization was granted.")
    print("      • No enforcement was applied.")
    print()
    print("      This was a simulation of what PCAE enforcement would")
    print("      decide. The operator retains full authority.")
    print("  ────────────────────────────────────────────────────────")


def _tri(value: object) -> bool | None:
    """Convert argparse tri-state (None / True / False) to bool | None."""
    if value is True:
        return True
    if value is False:
        return False
    return None
