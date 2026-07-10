"""Unified Query request model (131D Section 11.1 / Section 3 stages 1-2).

Additive to, never a modification of, Track 121's own ``QueryRequest``
(``query.query_request``), which remains Repository Knowledge
Snapshot-scoped and untouched by this package.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UnifiedQueryRequest:
    """A bounded, structured request over the six covered artifact families.

    ``category`` selects a routing table entry (``routing.ROUTING_TABLE``).
    ``target`` is the identifier to resolve, reusing whichever stable
    identifier field each routed family's own frozen schema already
    declares (never a newly-minted identity scheme).
    ``include_evidence`` opts in to verbatim evidence content in the
    response (131B Section 6's "expose" is a distinct, requestable
    responsibility, not an always-on default).
    """

    category: str
    target: str | None = None
    include_evidence: bool = False
    filters: dict[str, str] = field(default_factory=dict)

    def normalized(self) -> dict:
        return normalize_request(self)


def normalize_request(request: UnifiedQueryRequest) -> dict:
    """Canonicalize a request into a deterministic, hashable form.

    Mirrors ``QueryRequest.normalized()``'s existing sorted-filters
    pattern (Track 121) so that two logically-equal requests produce
    identical normalized output, letting determinism (131B Section 13)
    be checked mechanically.
    """
    if not isinstance(request.category, str) or not request.category:
        raise ValueError("malformed request: category must be a non-empty string")
    if request.target is not None and not isinstance(request.target, str):
        raise ValueError("malformed request: target must be a string or None")
    if not isinstance(request.filters, dict):
        raise ValueError("malformed request: filters must be a dict")
    return {
        "category": request.category,
        "target": request.target,
        "include_evidence": bool(request.include_evidence),
        "filters": {key: request.filters[key] for key in sorted(request.filters)},
    }
