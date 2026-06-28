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
    """Print human-readable simulation output (89B §19, refined 89E)."""
    decision = data["simulation_decision"]
    cmd = data["requested_command"]
    redacted = data["requested_command_redacted"]
    severity = data["simulation_severity"]
    severity_label = data.get("simulation_severity_label", severity.upper())

    # Severity header
    indicators = {
        "info": "ℹ️  INFO — SIMULATED ALLOW",
        "caution": "⚠️  CAUTION — SIMULATED GATE",
        "review_required": "👁️  REVIEW REQUIRED — SIMULATED GATE",
        "blocked": "🚫 SIMULATED BLOCK",
        "unknown": "❓ UNKNOWN",
    }
    header = indicators.get(severity, f"[{severity_label}]")

    print(f"PCAE Dry-Run Simulation — {header}")
    print("Simulation only. No command was executed. No enforcement occurred.")
    print()
    print(f"  Command:       {cmd!r}" + (" (redacted — secret material detected)" if redacted else ""))
    print(f"  Action:        {data['requested_action']}")
    if data.get("requested_files"):
        print(f"  Files:         {', '.join(data['requested_files'])}")
    print()
    print(f"  Shell Gate:    {data['shell_gate_category'] or 'N/A'}"
          f" → {data['shell_gate_decision'] or 'N/A'}")
    print(f"  Broker:        {data['broker_decision']}")
    print(f"  Simulation:    {decision}")
    print()

    # Decision-specific section
    if data["would_block"]:
        _print_blocked_section(data)
    elif data["would_deny"]:
        _print_deny_section(data)
    elif data["would_require_human_review"]:
        _print_review_section(data)
    elif data["would_require_preflight"]:
        _print_require_section("preflight", data)
    elif data["would_require_active_task"]:
        _print_require_section("active task", data)
    elif data["would_require_more_evidence"]:
        _print_evidence_section(data)
    else:
        _print_allowed_section(data)
    print()

    # Hard block status
    if data["hard_block_present"]:
        print(f"  Hard block:    yes — {data.get('hard_block_reason', 'policy')}")
        print(f"  Override:      not possible (hard blocks cannot be overridden")
        print(f"                 by human approval or accepted risk)")
    else:
        print(f"  Hard block:    none")
    print()

    # Redaction
    if data["redaction_applied"]:
        print(f"  Redaction:     applied — {data.get('redaction_reason', 'policy')}")
        print(f"                 No secret material is present in this output.")
    else:
        print(f"  Redaction:     not applied")
    print(f"  Safe to show:  {data['safe_to_display']}")
    print()

    # Enforcement readiness
    enf = data.get("enforcement_readiness", "")
    if enf:
        print(f"  Enforcement:   {enf}")
        print()

    # Next action (fix: dry-run explain, not advisory explain)
    next_action = data.get("next_required_action", "")
    if "pcae advisory explain" in next_action:
        next_action = next_action.replace("pcae advisory explain", "pcae dry-run explain")
    print(f"  Next action:   {next_action}")
    print()

    # Authorization status
    print(f"  Authorization: not granted")
    print(f"  Execution:     not authorized")
    print(f"  Enforcement:   not applied")
    print(f"  Interception:  not applied")
    print()

    # Footer
    print("  ────────────────────────────────────────────────────────")
    print("  ⚠️  Dry-run simulation complete. PCAE did NOT:")
    print()
    print("      • Execute this command")
    print("      • Intercept shell input")
    print("      • Grant authorization")
    print("      • Apply enforcement")
    print("      • Install wrappers or modify shell configuration")
    print()
    print("      This was a simulation of what PCAE enforcement")
    print("      would decide. The operator retains full and")
    print("      absolute authority over all command execution.")
    print("  ────────────────────────────────────────────────────────")


def _print_blocked_section(data: dict) -> None:
    decision = data["simulation_decision"]
    print(f"  ┌─ SIMULATED BLOCK ────────────────────────────────────┐")
    print(f"  │")
    print(f"  │  Decision: {decision}")
    if data["hard_block_present"]:
        print(f"  │  Type:     HARD BLOCK")
        print(f"  │  Override: NOT POSSIBLE — hard blocks cannot be")
        print(f"  │            overridden by human approval or accepted")
        print(f"  │            risk.")
    print(f"  │")
    print(f"  │  Under real enforcement, PCAE WOULD BLOCK this")
    print(f"  │  command. This simulation did not enforce any block.")
    gov = data.get("governed_alternative")
    if gov:
        print(f"  │")
        print(f"  │  Governed alternative: {gov}")
    print(f"  │")
    print(f"  └──────────────────────────────────────────────────────┘")


def _print_deny_section(data: dict) -> None:
    print(f"  ┌─ SIMULATED DENY ────────────────────────────────────┐")
    print(f"  │")
    print(f"  │  Decision: would_deny")
    print(f"  │  Type:     PERMANENT DENY")
    print(f"  │  Override: NONE — this decision is unconditional.")
    print(f"  │")
    print(f"  │  Under real enforcement, PCAE would PERMANENTLY")
    print(f"  │  DENY this command. No workaround exists.")
    print(f"  │")
    print(f"  └──────────────────────────────────────────────────────┘")


def _print_review_section(data: dict) -> None:
    will_change = "yes" if data.get("human_approval_would_change_outcome") else "no"
    print(f"  ┌─ SIMULATED REVIEW REQUIRED ─────────────────────────┐")
    print(f"  │")
    print(f"  │  Decision: would_require_human_review")
    print(f"  │  Type:     GATE (not a block)")
    print(f"  │")
    print(f"  │  Under enforcement, a human operator would need to")
    print(f"  │  review this command before it could proceed.")
    print(f"  │")
    print(f"  │  Review is NOT authorization. It confirms a human")
    print(f"  │  has examined the proposed action.")
    print(f"  │")
    if data["redaction_applied"]:
        print(f"  │  ⚠️  Command text was REDACTED — secret material")
        print(f"  │     was detected. Review the redaction reason.")
        print(f"  │")
    print(f"  │  Review would change outcome: {will_change}")
    print(f"  │")
    if data.get("governed_alternative"):
        print(f"  │  Governed alternative: {data['governed_alternative']}")
        print(f"  │")
    print(f"  └──────────────────────────────────────────────────────┘")


def _print_require_section(what: str, data: dict) -> None:
    print(f"  ┌─ SIMULATED REQUIREMENT ─────────────────────────────┐")
    print(f"  │")
    print(f"  │  Requirement: {what}")
    print(f"  │")
    print(f"  │  Under enforcement, this command would require")
    print(f"  │  {what} before it could proceed.")
    print(f"  │")
    print(f"  │  This is a gate, not a block. Provide the required")
    print(f"  │  item and re-evaluate.")
    print(f"  │")
    print(f"  └──────────────────────────────────────────────────────┘")


def _print_evidence_section(data: dict) -> None:
    print(f"  ┌─ SIMULATED EVIDENCE REQUIRED ───────────────────────┐")
    print(f"  │")
    print(f"  │  Decision: would_require_more_evidence")
    print(f"  │  Type:     GATE (not a block)")
    print(f"  │")
    print(f"  │  Under enforcement, additional governance evidence")
    print(f"  │  would be required before this command could proceed.")
    missing = data.get("missing_evidence", [])
    if missing:
        print(f"  │")
        print(f"  │  Missing evidence:")
        for item in missing:
            print(f"  │    • {item}")
    print(f"  │")
    print(f"  └──────────────────────────────────────────────────────┘")


def _print_allowed_section(data: dict) -> None:
    print(f"  ┌─ SIMULATED ALLOW ───────────────────────────────────┐")
    print(f"  │")
    print(f"  │  Decision: {data['simulation_decision']}")
    print(f"  │  Type:     ALLOW (preflight only)")
    print(f"  │")
    print(f"  │  Under enforcement, this command would be allowed")
    print(f"  │  to proceed. No PCAE governance concerns detected.")
    print(f"  │")
    print(f"  │  NOTE: Allow does NOT mean PCAE authorizes execution.")
    print(f"  │  PCAE never grants execution authorization. The")
    print(f"  │  operator retains full responsibility.")
    print(f"  │")
    print(f"  └──────────────────────────────────────────────────────┘")


def _tri(value: object) -> bool | None:
    """Convert argparse tri-state (None / True / False) to bool | None."""
    if value is True:
        return True
    if value is False:
        return False
    return None
