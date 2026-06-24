from __future__ import annotations

import argparse
import json

from pcae.core.gate_dry_run import build_gate_dry_run
from pcae.core.paths import HarnessPath


def run_gate_dry_run(args: argparse.Namespace) -> int:
    requested_action = getattr(args, "requested_action", None)
    requested_files = getattr(args, "requested_file", None) or []
    requested_backend = getattr(args, "requested_backend", None)
    prompt_present = getattr(args, "prompt_present", False) or False
    data = build_gate_dry_run(
        HarnessPath.cwd().path,
        requested_action=requested_action,
        requested_files=requested_files,
        requested_backend=requested_backend,
        prompt_present=prompt_present,
    )
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        print("Gate dry-run evaluation")
        print(f"  Gates:    {data['gate_count']}")
        print(f"  Dry run:  {data['dry_run']}")
        print(f"  Warnings: {len(data['warnings'])}")
        print(f"  Errors:   {len(data['errors'])}")
        if requested_action:
            print(f"  Requested action: {requested_action}")
        if requested_files:
            print(f"  Requested files:  {requested_files}")
        for gate in data["gates"]:
            line = f"  [{gate['gate_category']}] {gate['gate_id']}: {gate['decision']} ({gate['risk_level']})"
            if "scope_evaluation" in gate:
                line += f" [scope={gate['scope_evaluation']['scope_status']}]"
            print(line)
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
