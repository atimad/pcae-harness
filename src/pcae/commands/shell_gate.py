from __future__ import annotations

import argparse
import json

from pcae.core.shell_gate import build_shell_gate
from pcae.core.paths import HarnessPath


def run_shell_gate_check(args: argparse.Namespace) -> int:
    command_text = getattr(args, "command", "") or ""
    data = build_shell_gate(HarnessPath.cwd().path, command_text=command_text)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        sg = data["shell_gate"]
        print("Shell gate check (prototype)")
        print(f"  Command:   {sg['command_text']!r}")
        print(f"  Category:  {sg['command_category']}")
        print(f"  Decision:  {sg['decision']}")
        if sg["hard_block_present"]:
            print("  BLOCKED")
        if sg["requires_human_review"]:
            print("  Requires human review")
        if sg["requires_preflight"]:
            print("  Requires preflight")
        if sg["missing_evidence"]:
            print(f"  Missing evidence: {sg['missing_evidence']}")
        print(f"  Task active: {sg['active_task_detected']}")
        print(f"  Reason codes: {sg['reason_codes']}")
        print("  (shell gate prototype — no execution performed)")
    return 0
