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
from pcae.repository_intelligence.change_impact import (
    ChangeImpactBuilderError,
    ChangeImpactRequest,
    build_change_impact_report,
    serialize_change_impact_report,
)
from pcae.repository_intelligence.dependency_graph import (
    GraphGenerationError,
    generate_dependency_graph,
)
from pcae.repository_intelligence.historical_memory import (
    HistoricalGenerationError,
    generate_historical_memory,
)
from pcae.repository_intelligence.cross_artifact_integration import (
    IntegrationGenerationError,
    generate_cross_artifact_integration,
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


def run_repository_intelligence_change_impact(args: argparse.Namespace) -> int:
    snapshot_path = Path(args.snapshot)
    request = ChangeImpactRequest(
        requested_change=args.change,
        repository_scope=args.snapshot,
        target_entities=tuple(args.entity),
    )

    try:
        report = build_change_impact_report(snapshot_path, request)
    except ChangeImpactBuilderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(
            serialize_change_impact_report(report, pretty=args.pretty)
        )

    if args.json or args.pretty:
        print(serialize_change_impact_report(report, pretty=args.pretty))
    elif not args.output:
        data = report.to_dict()
        print("Repository Intelligence Change Impact Report")
        print(f"  Impacted entities: {len(data['impacted_entities'])}")
        print(f"  Relationships:     {len(data['impact_relationships'])}")
        print(f"  Attribution records:{len(data['attribution_bundle'])}")
        print(f"  Limitations:        {len(data['limitation_bundle'])}")
        print(f"  Unknowns:           {len(data['unknowns'])}")
    return 0


def run_repository_intelligence_dependency_graph_generate(args: argparse.Namespace) -> int:
    repo_root = HarnessPath.cwd().path
    snapshot_path = Path(args.snapshot)
    output_dir = Path(args.output) if args.output else None

    try:
        result = generate_dependency_graph(
            snapshot_path,
            repo_root=repo_root,
            output_dir=output_dir,
            pretty=args.pretty,
        )
    except GraphGenerationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Dependency Knowledge Graph generated")
        print(f"  Artifact ID:          {result['artifact_id']}")
        print(f"  Repository commit:    {result['repository_commit']}")
        print(f"  Source snapshot:      {result['source_snapshot_path']}")
        print(f"  Nodes:                {result['node_count']}")
        print(f"  Edges:                {result['edge_count']}")
        print(f"  Dependency claims:    {result['dependency_claim_count']}")
        print(f"  Dependency sources:   {result['dependency_source_count']}")
        print(f"  Unknown gaps:         {result['unknown_gap_count']}")
        print(f"  Completeness state:   {result['graph_completeness_state']}")
        print(f"  Latest graph:         {result['latest_path']}")
        print(f"  Timestamped graph:    {result['graph_path']}")
    return 0


def run_repository_intelligence_historical_memory_generate(args: argparse.Namespace) -> int:
    repo_root = HarnessPath.cwd().path
    snapshot_path = Path(args.snapshot)
    output_dir = Path(args.output) if args.output else None

    try:
        result = generate_historical_memory(
            snapshot_path,
            repo_root=repo_root,
            output_dir=output_dir,
            pretty=args.pretty,
        )
    except HistoricalGenerationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Historical Memory Snapshot generated")
        print(f"  Artifact ID:          {result['artifact_id']}")
        print(f"  Repository commit:    {result['repository_commit']}")
        print(f"  Source snapshot:      {result['source_snapshot_path']}")
        print(f"  Events:               {result['event_count']}")
        print(f"  Claims:               {result['claim_count']}")
        print(f"  Phase lineage:        {result['phase_lineage_count']}")
        print(f"  Release lineage:      {result['release_lineage_count']}")
        print(f"  Repair/hardening:     {result['repair_hardening_count']}")
        print(f"  Relationships:        {result['relationship_count']}")
        print(f"  Historical sources:   {result['historical_source_count']}")
        print(f"  Unknown gaps:         {result['unknown_gap_count']}")
        print(f"  Latest snapshot:      {result['latest_path']}")
        print(f"  Timestamped snapshot: {result['snapshot_path']}")
    return 0


def run_repository_intelligence_cross_artifact_integration_generate(
    args: argparse.Namespace,
) -> int:
    repo_root = HarnessPath.cwd().path
    change_impact_path = Path(args.change_impact)
    dependency_graph_path = Path(args.dependency_graph)
    output_dir = Path(args.output) if args.output else None
    rks_path = Path(args.repository_knowledge_snapshot) if args.repository_knowledge_snapshot else None
    historical_memory_path = Path(args.historical_memory) if args.historical_memory else None
    advisory_context_path = Path(args.advisory_context) if args.advisory_context else None

    try:
        result = generate_cross_artifact_integration(
            change_impact_path,
            dependency_graph_path,
            repo_root=repo_root,
            output_dir=output_dir,
            pretty=args.pretty,
            repository_knowledge_snapshot_path=rks_path,
            historical_memory_path=historical_memory_path,
            advisory_context_path=advisory_context_path,
        )
    except IntegrationGenerationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Cross-Artifact Knowledge Integration Package generated")
        print(f"  Configuration:          {result['integration_configuration']}")
        print(f"  Change Impact input:    {result['change_impact_path']}")
        print(f"  Dependency Graph input: {result['dependency_graph_path']}")
        print(f"  Referenced artifacts:   {result['referenced_artifact_count']}")
        print(f"  Dependency contexts:    {result['dependency_context_count']}")
        print(f"  Entity resolutions:     {result['entity_resolution_count']}")
        print(f"  Unresolved identities:  {result['unresolved_identity_count']}")
        print(f"  Latest package:         {result['latest_path']}")
        print(f"  Timestamped package:    {result['package_path']}")
    return 0


def run_repository_intelligence_unified_query(args: argparse.Namespace) -> int:
    from pcae.repository_intelligence.unified_query import (
        UnifiedQueryRequest,
        execute_unified_query,
    )
    from pcae.repository_intelligence.unified_query.errors import UnifiedQueryError
    from pcae.repository_intelligence.unified_query.routing import (
        ADVISORY_CONTEXT,
        CHANGE_IMPACT,
        CROSS_ARTIFACT_INTEGRATION,
        DEPENDENCY_KNOWLEDGE_GRAPH,
        HISTORICAL_MEMORY,
        REPOSITORY_KNOWLEDGE_SNAPSHOT,
    )

    artifact_paths: dict[str, Path] = {}
    if args.repository_knowledge_snapshot:
        artifact_paths[REPOSITORY_KNOWLEDGE_SNAPSHOT] = Path(args.repository_knowledge_snapshot)
    if args.dependency_graph:
        artifact_paths[DEPENDENCY_KNOWLEDGE_GRAPH] = Path(args.dependency_graph)
    if args.historical_memory:
        artifact_paths[HISTORICAL_MEMORY] = Path(args.historical_memory)
    if args.change_impact:
        artifact_paths[CHANGE_IMPACT] = Path(args.change_impact)
    if args.advisory_context:
        artifact_paths[ADVISORY_CONTEXT] = Path(args.advisory_context)
    if args.cross_artifact_integration:
        artifact_paths[CROSS_ARTIFACT_INTEGRATION] = Path(args.cross_artifact_integration)

    request = UnifiedQueryRequest(
        category=args.category,
        target=args.target,
        include_evidence=args.include_evidence,
    )

    try:
        response = execute_unified_query(request, artifact_paths=artifact_paths)
    except UnifiedQueryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (SnapshotLoadError, SnapshotCompatibilityError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    data = response.to_dict()
    if args.json or args.pretty:
        print(json.dumps(data, indent=2 if args.pretty else None, sort_keys=True))
    else:
        print("Unified Repository Intelligence Query result")
        print(f"  Status:              {data['result_status']}")
        print(f"  Category:            {data['query_metadata']['category']}")
        print(f"  References:          {len(data['references'])}")
        print(f"  Evidence records:    {len(data['evidence'])}")
        print(f"  Limitations:         {len(data['limitations'])}")
        print(f"  Uncertainty records: {len(data['uncertainty'])}")
    return 0


def run_repository_intelligence_service(args: argparse.Namespace) -> int:
    from pcae.repository_intelligence.service import (
        ServiceRequest,
        ServiceError,
        execute_service_request,
    )
    from pcae.repository_intelligence.unified_query.routing import (
        ADVISORY_CONTEXT,
        CHANGE_IMPACT,
        CROSS_ARTIFACT_INTEGRATION,
        DEPENDENCY_KNOWLEDGE_GRAPH,
        HISTORICAL_MEMORY,
        REPOSITORY_KNOWLEDGE_SNAPSHOT,
    )

    artifact_paths: dict[str, Path] = {}
    if args.repository_knowledge_snapshot:
        artifact_paths[REPOSITORY_KNOWLEDGE_SNAPSHOT] = Path(args.repository_knowledge_snapshot)
    if args.dependency_graph:
        artifact_paths[DEPENDENCY_KNOWLEDGE_GRAPH] = Path(args.dependency_graph)
    if args.historical_memory:
        artifact_paths[HISTORICAL_MEMORY] = Path(args.historical_memory)
    if args.change_impact:
        artifact_paths[CHANGE_IMPACT] = Path(args.change_impact)
    if args.advisory_context:
        artifact_paths[ADVISORY_CONTEXT] = Path(args.advisory_context)
    if args.cross_artifact_integration:
        artifact_paths[CROSS_ARTIFACT_INTEGRATION] = Path(args.cross_artifact_integration)

    families = tuple(args.family) if args.family else ()
    request = ServiceRequest(
        kind=args.kind,
        target=args.target,
        families=families,
        include_evidence=args.include_evidence,
    )

    try:
        response = execute_service_request(request, artifact_paths=artifact_paths)
    except ServiceError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (SnapshotLoadError, SnapshotCompatibilityError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    data = response.to_dict()
    if args.json or args.pretty:
        print(json.dumps(data, indent=2 if args.pretty else None, sort_keys=True))
    else:
        print("Repository Intelligence Service result")
        print(f"  Status:              {data['result_status']}")
        print(f"  Kind:                {data['request_metadata']['kind']}")
        print(f"  Families composed:   {len(data['families'])}")
        print(f"  Composition calls:   {len(data['composition_metadata'])}")
        print(f"  Limitations:         {len(data['limitations'])}")
        print(f"  Uncertainty records: {len(data['uncertainty'])}")
        print(f"  Composite responses: {len(data['composite_responses'])}")
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
