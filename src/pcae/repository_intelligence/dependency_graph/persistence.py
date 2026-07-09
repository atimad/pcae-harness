"""Dependency Knowledge Graph persistence (126D pipeline stage 12).

Writes only. Never modifies, deletes, or reads back an existing graph
artifact for extraction purposes. Mirrors
``pcae.repository_intelligence.persistence`` (Track 120) but writes to
a distinct location so the graph artifact family never overwrites or
is confused with the source Repository Knowledge Snapshot.

Reuses the Track 124 shared deterministic JSON serializer
(``serialize_deterministic_json``) rather than reintroducing parallel
serialization logic, resolving 126C Finding 2 / 126D Section 9.
"""

from __future__ import annotations

from pathlib import Path

from pcae.repository_intelligence.serialization import serialize_deterministic_json

DEFAULT_OUTPUT_SUBDIR = "repository-intelligence/dependency-graph"


def write_graph(
    graph: dict,
    *,
    repo_root: Path,
    timestamp_slug: str,
    output_dir: Path | None = None,
    pretty: bool = False,
) -> dict:
    """Persist ``graph`` as both the latest and a timestamped file.

    Returns a dict with the two absolute paths written.
    """
    base_dir = output_dir if output_dir is not None else repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR
    graphs_dir = base_dir / "graphs"
    graphs_dir.mkdir(parents=True, exist_ok=True)

    serialized = serialize_deterministic_json(graph, pretty=pretty)
    if pretty:
        serialized += "\n"

    latest_path = base_dir / "latest.json"
    latest_path.write_text(serialized, encoding="utf-8")

    timestamped_path = graphs_dir / f"{timestamp_slug}.json"
    timestamped_path.write_text(serialized, encoding="utf-8")

    return {
        "latest_path": str(latest_path),
        "graph_path": str(timestamped_path),
    }
