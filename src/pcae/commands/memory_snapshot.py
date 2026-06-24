from __future__ import annotations

import argparse
import json

from pcae.core.memory_snapshot import build_memory_snapshot
from pcae.core.paths import HarnessPath


def run_memory_snapshot(args: argparse.Namespace) -> int:
    data = build_memory_snapshot(HarnessPath.cwd().path)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        snapshot = data["snapshot"]
        print("Memory snapshot")
        print(f"  Project:          {snapshot['project_id']}")
        print(f"  Current phase:    {snapshot['current_phase'] or 'none'}")
        print(f"  Latest completed: {snapshot['latest_completed_phase'] or 'unknown'}")
        print(f"  Lifecycle state:  {snapshot['current_lifecycle_state']}")
        print(f"  Artifact index:   {snapshot['artifact_index_status']}")
        print(f"  Origin sync:      {snapshot['origin_sync_status']}")
        print(f"  Governance:       {snapshot['governance_status']}")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
