from __future__ import annotations

import argparse
import json

from pcae.core.risk_register import build_risk_register
from pcae.core.paths import HarnessPath


def run_risk_register(args: argparse.Namespace) -> int:
    data = build_risk_register(HarnessPath.cwd().path)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        print("Risk register")
        print(f"  Risks:    {data['risk_count']}")
        print(f"  Warnings: {len(data['warnings'])}")
        print(f"  Errors:   {len(data['errors'])}")
        for risk in data["risks"]:
            print(f"  [{risk['source_phase']}] {risk['risk_type']} ({risk['risk_status']}) [{risk['risk_severity']}]")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
