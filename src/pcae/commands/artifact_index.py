from __future__ import annotations

import argparse
import json

from pcae.core.artifact_index import build_artifact_index
from pcae.core.paths import HarnessPath


def run_artifact_index(args: argparse.Namespace) -> int:
    data = build_artifact_index(HarnessPath.cwd().path)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=False))
    else:
        print("Artifact index")
        print(f"  Records:  {data['record_count']}")
        print(f"  Present:  {data['present_count']}")
        print(f"  Missing:  {data['missing_count']}")
        for record in data["records"]:
            status_marker = "OK" if record["artifact_status"] == "current" else "MISSING"
            print(f"  [{status_marker}] {record['artifact_type']}: {record['artifact_path']}")
        for warning in data["warnings"]:
            print(f"  warning: {warning}")
    return 0
