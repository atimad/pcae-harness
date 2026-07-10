"""Repository Intelligence Service prototype (Phase 132E).

The canonical, deterministic, read-only composition layer over Unified
Query (Track 131, independently verified complete). Repository
Intelligence Service exists solely to provide deterministic, governed
consumption of Repository Intelligence: it composes one or more
Unified Query results into a single, coherent, provenance-complete
package, preserving every governance guarantee Unified Query already
provides (132B Section 2).

This package introduces no new knowledge, no new identity resolution,
and no new artifact access path. It calls Unified Query's own real
``execute_unified_query`` entry point exclusively -- it never reads an
artifact file directly, never duplicates routing, and never duplicates
identity resolution (132B Section 3/14). Every source artifact and
Unified Query itself remain authoritative; this package is strictly
derivative and never becomes an evidence source (132B Section 4).
"""

from __future__ import annotations

from pcae.repository_intelligence.service.errors import (
    MalformedServiceRequestError,
    ServiceError,
    UnsupportedServiceRequestError,
)
from pcae.repository_intelligence.service.request import (
    ServiceRequest,
    normalize_service_request,
)
from pcae.repository_intelligence.service.response import ServiceResponse
from pcae.repository_intelligence.service.service_engine import execute_service_request

__all__ = [
    "MalformedServiceRequestError",
    "ServiceError",
    "UnsupportedServiceRequestError",
    "ServiceRequest",
    "ServiceResponse",
    "execute_service_request",
    "normalize_service_request",
]
