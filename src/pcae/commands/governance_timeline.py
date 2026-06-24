from __future__ import annotations

import argparse
import json

from pcae.core.governance_timeline import build_governance_timeline
from pcae.core.paths import HarnessPath


def run_governance_timeline(args: argparse.Namespace) -> int:
    data = build_governance_timeline(HarnessPath.cwd().path)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        print("Governance timeline")
        print(f"  Events:   {data['event_count']}")
        print(f"  Warnings: {len(data['warnings'])}")
        print(f"  Errors:   {len(data['errors'])}")
        for evt in data["events"]:
            ts = evt["event_timestamp"]
            if ts == "unknown":
                ts_short = "unknown"
            elif len(ts) >= 10:
                ts_short = ts[:10]
            else:
                ts_short = ts
            print(f"  [{evt['source_phase']}] {evt['event_type']} ({ts_short})")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
