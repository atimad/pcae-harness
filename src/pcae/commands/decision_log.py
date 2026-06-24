from __future__ import annotations

import argparse
import json

from pcae.core.decision_log import build_decision_log
from pcae.core.paths import HarnessPath


def run_decision_log(args: argparse.Namespace) -> int:
    data = build_decision_log(HarnessPath.cwd().path)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        print("Decision log")
        print(f"  Decisions: {data['decision_count']}")
        print(f"  Warnings:  {len(data['warnings'])}")
        print(f"  Errors:    {len(data['errors'])}")
        for dec in data["decisions"]:
            ts = dec["decision_timestamp"]
            if ts == "unknown":
                ts_short = "unknown"
            elif len(ts) >= 10:
                ts_short = ts[:10]
            else:
                ts_short = ts
            print(f"  [{dec['source_phase']}] {dec['decision_type']} ({ts_short}) [{dec['decision_status']}]")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
