from __future__ import annotations

from dataclasses import dataclass, field

SUPPORTED_QUERY_CATEGORIES = frozenset(
    {
        "entity_lookup",
        "capability_lookup",
        "architectural_contract_lookup",
        "attribution_lookup",
        "limitation_lookup",
        "boundary_lookup",
    }
)


@dataclass(frozen=True)
class QueryRequest:
    """Bounded structured request for the Phase 121E query prototype."""

    category: str
    target: str | None = None
    filters: dict[str, str] = field(default_factory=dict)
    projection: tuple[str, ...] = ()

    def normalized(self) -> dict:
        return {
            "category": self.category,
            "target": self.target,
            "filters": {key: self.filters[key] for key in sorted(self.filters)},
            "projection": list(self.projection),
        }


def validate_request(request: QueryRequest) -> None:
    if request.category not in SUPPORTED_QUERY_CATEGORIES:
        raise ValueError(f"unsupported query category: {request.category}")
    if request.category in {
        "entity_lookup",
        "capability_lookup",
        "architectural_contract_lookup",
        "attribution_lookup",
    } and not request.target:
        raise ValueError(f"{request.category} requires a target")
