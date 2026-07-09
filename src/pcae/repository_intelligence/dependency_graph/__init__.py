"""Dependency Knowledge Graph Builder (Track 126, Phase 126E prototype).

Deterministic, read-only construction of a Dependency Knowledge Graph
artifact from an existing Repository Knowledge Snapshot, consumed
exclusively through the Track 121 Query Layer. No graph traversal, no
reasoning, no execution capability.
"""

from __future__ import annotations

from pcae.repository_intelligence.dependency_graph.graph_builder import (
    GraphGenerationError,
    build_graph_content,
)
from pcae.repository_intelligence.dependency_graph.graph_generator import (
    generate_dependency_graph,
)

__all__ = [
    "GraphGenerationError",
    "build_graph_content",
    "generate_dependency_graph",
]
