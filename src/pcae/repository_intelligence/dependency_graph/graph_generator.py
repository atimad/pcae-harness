"""Top-level Dependency Knowledge Graph generation orchestration.

Wires together the 126D pipeline stages implemented across
``graph_builder``, ``graph_validation``, and ``persistence``. This
module is the only intended external entry point into the
``dependency_graph`` package (used by the CLI handler and by tests).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pcae.repository_intelligence.dependency_graph.graph_builder import (
    GraphGenerationError,
    build_graph_content,
)
from pcae.repository_intelligence.dependency_graph.graph_validation import (
    validate_graph,
)
from pcae.repository_intelligence.dependency_graph.persistence import write_graph

__all__ = ["GraphGenerationError", "generate_dependency_graph"]


def generate_dependency_graph(
    snapshot_path: Path,
    *,
    repo_root: Path,
    output_dir: Path | None = None,
    pretty: bool = False,
) -> dict:
    """Generate and persist one Dependency Knowledge Graph.

    Returns generation metadata (not the graph content itself):
    artifact/graph identifiers, counts, and the paths written.

    Raises ``GraphGenerationError`` if the source Repository Knowledge
    Snapshot is invalid, unsupported, or missing required provenance/
    limitation/boundary material (fail-closed; nothing is persisted in
    that case).
    """
    now = datetime.now(timezone.utc)
    generated_at_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    graph = build_graph_content(snapshot_path, generated_at_utc=generated_at_utc)
    validate_graph(graph)

    # Microsecond precision only in the persisted filename slug (an
    # approved, non-substantive metadata identifier, mirroring 120B
    # Section 6) so two runs within the same second do not collide.
    timestamp_slug = now.strftime("%Y%m%dT%H%M%S%f") + "Z"
    paths = write_graph(
        graph,
        repo_root=repo_root,
        timestamp_slug=timestamp_slug,
        output_dir=output_dir,
        pretty=pretty,
    )

    return {
        "artifact_id": graph["envelope"]["artifact_id"],
        "graph_id": graph["snapshot_identity"]["snapshot_id"],
        "repository_commit": graph["envelope"]["repository_context"]["repository_commit"],
        "source_snapshot_path": str(snapshot_path),
        "generated_at_utc": generated_at_utc,
        "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]),
        "dependency_claim_count": len(graph["dependency_claims"]),
        "dependency_source_count": len(graph["dependency_sources"]),
        "unknown_gap_count": len(graph["unknowns_gaps"]),
        "graph_completeness_state": graph["graph_metadata"]["graph_completeness_state"],
        "latest_path": paths["latest_path"],
        "graph_path": paths["graph_path"],
    }
