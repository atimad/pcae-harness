"""Unified Repository Intelligence Query prototype (Phase 131E).

A single, deterministic, read-only access layer over the six existing,
independently-verified Repository Intelligence artifact families
(Repository Knowledge Snapshot, Dependency Knowledge Graph, Historical
Memory, Change Impact, Advisory Context, Cross-Artifact Integration),
implementing the contract 131B froze and 131C independently verified
with zero BLOCKING findings.

This package creates no new knowledge. It locates, correlates,
aggregates, exposes, and references content already present in the
six covered artifact families -- it never infers, reasons, recommends,
ranks, evaluates, authorizes, mutates, or executes (131B Section 6).
Every source artifact remains authoritative; this package is strictly
derivative (131B Section 5).
"""

from __future__ import annotations

from pcae.repository_intelligence.unified_query.errors import (
    RoutingAmbiguityError,
    UnifiedQueryError,
    UnsupportedQueryCategoryError,
)
from pcae.repository_intelligence.unified_query.request import (
    UnifiedQueryRequest,
    normalize_request,
)
from pcae.repository_intelligence.unified_query.response import UnifiedQueryResponse
from pcae.repository_intelligence.unified_query.unified_query_engine import (
    execute_unified_query,
)

__all__ = [
    "RoutingAmbiguityError",
    "UnifiedQueryError",
    "UnsupportedQueryCategoryError",
    "UnifiedQueryRequest",
    "UnifiedQueryResponse",
    "execute_unified_query",
    "normalize_request",
]
