from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pcae.advisory.context import (
    AdvisoryContextBuilderError,
    AdvisoryContextRequest,
    build_advisory_context,
    serialize_context_package,
)


def run_advisory_context_build(args: argparse.Namespace) -> int:
    snapshot_path = Path(args.snapshot)

    try:
        request = _request_from_args(args)
        package = build_advisory_context(snapshot_path, request)
    except AdvisoryContextBuilderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    serialized = serialize_context_package(package, pretty=args.pretty)

    if args.output:
        Path(args.output).write_text(serialized)

    if args.json or args.pretty:
        print(serialized)
    else:
        metadata = package.context_metadata
        print("Advisory context package assembled")
        print(f"  Advisory purpose:   {metadata['advisory_purpose']}")
        print(f"  Category:           {metadata['query_request']['category']}")
        print(f"  Status:              {metadata['result_status']}")
        print(f"  Records selected:   {metadata['record_count']}")
        print(f"  Attribution records:{len(package.attribution_bundle)}")
        print(f"  Limitations:        {len(package.limitation_bundle)}")
        print(f"  Snapshot ID:        {metadata['source_artifact']['snapshot_id']}")
        if args.output:
            print(f"  Written to:         {args.output}")
    return 0


def _request_from_args(args: argparse.Namespace) -> AdvisoryContextRequest:
    purpose = args.purpose
    if args.entity:
        category, target = "entity_lookup", args.entity
    elif args.capability:
        category, target = "capability_lookup", args.capability
    elif args.contract:
        category, target = "architectural_contract_lookup", args.contract
    else:
        raise AdvisoryContextBuilderError("one context target must be provided")

    if not purpose:
        purpose = f"cli_advisory_context_build:{category}:{target}"

    return AdvisoryContextRequest(category=category, advisory_purpose=purpose, target=target)
