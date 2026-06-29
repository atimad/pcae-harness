"""CLI runners for pcae shell-gate commands.

Phase 88P: check — shell gate classifier (build_shell_gate)
Phase 93B: check — broker-integrated (check_shell_gate)
"""
from __future__ import annotations

import argparse
import json

from pcae.core.shell_gate import check_shell_gate
from pcae.core.paths import HarnessPath


def run_shell_gate_check(args: argparse.Namespace) -> int:
    """pcae shell-gate check --command <CMD> [--json]

    Phase 93B: Classify a proposed shell command, evaluate via the
    permission broker, and return a structured simulation decision.
    Never executes the command. Simulation-only.
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
        sim_only = data["simulation_only"]
        no_exec = data["no_execution"]
        no_enf = data["no_enforcement"]

        print("Shell gate check (simulation only — Phase 93B)")
        print(f"  Command:            {command_text!r}")
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
        print(f"  Message: {message}")
        print()
        print(f"  Simulation only:    {sim_only}")
        print(f"  No execution:       {no_exec}")
        print(f"  No enforcement:     {no_enf}")
        print(f"  Authorization:      {data['authorization_granted']}")
        print()
        if hard_block:
            print("  ⚠️  HARD BLOCK — non-overridable (88V §16).")
            print("  No human approval, accepted risk, or operator override can bypass.")
        print("  ⚠️  Simulation only — PCAE did NOT execute, intercept, or authorize anything.")
        print("  The operator retains full authority.")

    return 0
