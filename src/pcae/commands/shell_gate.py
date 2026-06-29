"""CLI runners for pcae shell-gate commands.

Phase 88P: check — shell gate classifier (build_shell_gate)
Phase 93B: check — broker-integrated (check_shell_gate)
Phase 93C: check — audit evidence model
"""
from __future__ import annotations

import argparse
import json

from pcae.core.shell_gate import check_shell_gate
from pcae.core.paths import HarnessPath


def run_shell_gate_check(args: argparse.Namespace) -> int:
    """pcae shell-gate check --command <CMD> [--json]

    Phase 93B/93C: Classify a proposed shell command, evaluate via the
    permission broker, produce audit evidence, and return a structured
    simulation decision.  Never executes the command.  Simulation-only.
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

    data = check_shell_gate(HarnessPath.cwd().path, command_text=command_text)

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        decision = data["decision"]
        hard_block = data["hard_block"]
        command_class = data["command_class"]
        command_category = data["command_category"]
        action_type = data["action_type"]
        reason_code = data["reason_code"]
        message = data["message"]
        audit = data.get("audit_evidence", {})
        redacted = data.get("redaction_applied", False)

        print("Shell gate check (simulation only — Phase 93C)")
        print(f"  Command:            {data['command_text']!r}")
        if redacted:
            print(f"  ⚠︎ Command redacted (secrets detected)")
        print(f"  Command category:   {command_category}")
        print(f"  Command class:      {command_class}")
        print(f"  Action type:        {action_type}")
        print(f"  Decision:           {decision}")
        print(f"  Hard block:         {hard_block}")
        print(f"  Reason:             {reason_code}")
        if data.get("required_evidence"):
            print(f"  Evidence needed:    {', '.join(data['required_evidence'])}")
        if data.get("reason_codes"):
            rc = ', '.join(data["reason_codes"])
            print(f"  Reason codes:       {rc}")
        if data.get("extracted_paths"):
            print(f"  Extracted paths:    {', '.join(data['extracted_paths'])}")
        print()
        # Audit summary
        if audit:
            print(f"  Audit ID:           {audit.get('audit_id', '')}")
            print(f"  Command hash:       {audit.get('command_hash', '')[:16]}...")
            if redacted:
                print(f"  Redaction:          applied")
        print()
        print(f"  Message: {message}")
        print()
        print(f"  Simulation only:    {data['simulation_only']}")
        print(f"  No execution:       {data['no_execution']}")
        print(f"  No enforcement:     {data['no_enforcement']}")
        print(f"  Authorization:      {data['authorization_granted']}")
        print()
        if hard_block:
            print("  ⚠️  HARD BLOCK — non-overridable (88V §16).")
            print("  No human approval, accepted risk, or operator override can bypass.")
        print("  ⚠️  Simulation only — PCAE did NOT execute, intercept, or authorize anything.")
        print("  The operator retains full authority.")

    return 0
