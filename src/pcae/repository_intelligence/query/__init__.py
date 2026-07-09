"""Read-only Repository Intelligence Query prototype (Phase 121E).

This package consumes existing Repository Knowledge Snapshot artifacts.
It does not generate Repository Intelligence, scan repositories, invoke
AI providers, mutate runtime state, or introduce execution capability.
"""

from __future__ import annotations

from pcae.repository_intelligence.query.query_engine import (
    QueryExecutionError,
    execute_query,
)
from pcae.repository_intelligence.query.query_request import QueryRequest

__all__ = ["QueryExecutionError", "QueryRequest", "execute_query"]
