from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.repository_intelligence.snapshot_generator import (
    SnapshotGenerationError,
    generate_snapshot,
)


def run_repository_intelligence_snapshot_generate(args: argparse.Namespace) -> int:
    repo_root = HarnessPath.cwd().path
    output_dir = Path(args.output) if args.output else None

    try:
        result = generate_snapshot(repo_root, output_dir=output_dir, pretty=args.pretty)
    except SnapshotGenerationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Repository Knowledge Snapshot generated")
        print(f"  Artifact ID:        {result['artifact_id']}")
        print(f"  Repository commit:  {result['repository_commit']}")
        print(f"  Architectural entities: {result['architectural_entity_count']}")
        print(f"  Subsystems:         {result['subsystem_count']}")
        print(f"  Knowledge claims:   {result['knowledge_claim_count']}")
        print(f"  Knowledge sources:  {result['knowledge_source_count']}")
        print(f"  Unknowns declared:  {result['unknown_count']}")
        print(f"  Latest snapshot:    {result['latest_path']}")
        print(f"  Timestamped snapshot: {result['snapshot_path']}")
    return 0
