from __future__ import annotations

import argparse
import json

from pcae.core.gate_dry_run import build_gate_dry_run
from pcae.core.paths import HarnessPath


def run_gate_dry_run(args: argparse.Namespace) -> int:
    data = build_gate_dry_run(HarnessPath.cwd().path)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        print("Gate dry-run evaluation")
        print(f"  Gates:    {data['gate_count']}")
        print(f"  Dry run:  {data['dry_run']}")
        print(f"  Warnings: {len(data['warnings'])}")
        print(f"  Errors:   {len(data['errors'])}")
        for gate in data["gates"]:
            print(f"  [{gate['gate_category']}] {gate['gate_id']}: {gate['decision']} ({gate['risk_level']})")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
