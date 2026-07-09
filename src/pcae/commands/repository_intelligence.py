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
from pcae.repository_intelligence.query import QueryExecutionError, QueryRequest
from pcae.repository_intelligence.query.query_engine import execute_query
from pcae.repository_intelligence.query.result_formatter import format_result
from pcae.repository_intelligence.query.snapshot_loader import (
    SnapshotCompatibilityError,
    SnapshotLoadError,
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


def run_repository_intelligence_query(args: argparse.Namespace) -> int:
    snapshot_path = Path(args.snapshot)
    request = _request_from_query_args(args)

    try:
        result = execute_query(snapshot_path, request)
    except (QueryExecutionError, SnapshotCompatibilityError, SnapshotLoadError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json or args.pretty:
        print(format_result(result, pretty=args.pretty))
    else:
        data = result.to_dict()
        print("Repository Intelligence query result")
        print(f"  Status:             {data['result_status']}")
        print(f"  Category:           {data['query_metadata']['category']}")
        print(f"  Records returned:   {len(data['records'])}")
        print(f"  Attribution records:{len(data['attribution'])}")
        print(f"  Limitations:        {len(data['limitations'])}")
        print(f"  Snapshot ID:        {data['source_artifact']['snapshot_id']}")
    return 0


def _request_from_query_args(args: argparse.Namespace) -> QueryRequest:
    if args.entity:
        return QueryRequest(category="entity_lookup", target=args.entity)
    if args.capability:
        return QueryRequest(category="capability_lookup", target=args.capability)
    if args.contract:
        return QueryRequest(category="architectural_contract_lookup", target=args.contract)
    if args.attribution:
        return QueryRequest(category="attribution_lookup", target=args.attribution)
    if args.limitations:
        return QueryRequest(category="limitation_lookup")
    if args.boundary:
        return QueryRequest(category="boundary_lookup")
    raise QueryExecutionError("one query target must be provided")
