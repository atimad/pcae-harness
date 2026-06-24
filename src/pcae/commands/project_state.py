from __future__ import annotations

import argparse
import json

from pcae.core.project_state import build_project_state
from pcae.core.paths import HarnessPath


def run_project_state(args: argparse.Namespace) -> int:
    data = build_project_state(HarnessPath.cwd().path)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        snap = data["snapshot"]
        layers = data.get("layer_summary", {})
        print("Project state snapshot")
        print(f"  Latest completed:  {snap['latest_completed_phase'] or 'unknown'}")
        print(f"  Active phase:      {snap['current_active_phase'] or 'none'}")
        print(f"  Lifecycle state:   {snap['current_lifecycle_state']}")
        print(f"  Recommended next:  {snap['recommended_next_phase']}")
        print(f"  Repository clean:  {snap['repository_clean']}")
        print(f"  Origin sync:       {snap['origin_sync_status']}")
        print(f"  Active risks:      {len(snap['active_risks'])}")
        print(f"  Accepted risks:    {len(snap['accepted_risks'])}")
        print(f"  Stale signals:     {len(snap['stale_signals'])}")
        print(f"  Must-never-repeat: {len(snap['must_never_repeat_controls'])}")
        print(f"  Artifacts:         {layers.get('artifact_index', {}).get('record_count', '?')}")
        print(f"  Events:            {layers.get('governance_timeline', {}).get('event_count', '?')}")
        print(f"  Decisions:         {layers.get('decision_log', {}).get('decision_count', '?')}")
        print(f"  Risks:             {layers.get('risk_register', {}).get('risk_count', '?')}")
        for w in data["warnings"]:
            print(f"  warning: {w}")
    return 0
