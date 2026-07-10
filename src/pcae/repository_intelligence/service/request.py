"""Repository Intelligence Service request model (132D Section 5).

Four conceptual categories, no schema, no protocol (132B Section 7):
entity, artifact, scoped, composite. A composite request is planned as
N independent entity/artifact/scoped requests, each fully composed
independently, then wrapped in one outer envelope keyed by target --
no cross-target correlation is implemented (132D Section 5's own
explicit bounding of the composite-request scope 132B deferred).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pcae.repository_intelligence.unified_query.routing import SIX_ARTIFACT_FAMILIES

SERVICE_REQUEST_KINDS = frozenset({"entity", "artifact", "scoped", "composite"})

_VALID_FAMILIES = frozenset(SIX_ARTIFACT_FAMILIES)


@dataclass(frozen=True)
class ServiceRequest:
    """A bounded, structured request over Repository Intelligence Service.

    ``kind`` selects the conceptual request category (132A Section 6).
    ``target`` is the identifier to resolve, reused verbatim against
    whichever family's own stable identifier field Unified Query
    itself already resolves against (never a newly-minted identity
    scheme, 132B Section 14).
    ``families`` is the explicit family allow-list: empty for
    ``entity`` (means "all six families"), exactly one entry for
    ``artifact``, one or more entries for ``scoped``.
    ``composite_targets`` is used only for ``kind="composite"``: a
    tuple of inner entity/artifact/scoped requests, each independently
    composed (132D Section 5) -- never itself containing a nested
    composite request.
    ``include_evidence`` opts in to verbatim evidence content in the
    response, mirroring Unified Query's own opt-in "expose"
    responsibility (132B Section 8).
    """

    kind: str
    target: str | None = None
    families: tuple[str, ...] = ()
    composite_targets: tuple["ServiceRequest", ...] = ()
    include_evidence: bool = False
    filters: dict[str, str] = field(default_factory=dict)

    def normalized(self) -> dict:
        return normalize_service_request(self)


def normalize_service_request(request: ServiceRequest) -> dict:
    """Canonicalize and validate a request; raise ``ValueError`` on malformed shape.

    Mirrors ``unified_query.request.normalize_request``'s own
    validate-before-proceed pattern one layer up.
    """
    if request.kind not in SERVICE_REQUEST_KINDS:
        raise ValueError(f"unsupported service request kind: {request.kind!r}")

    if request.kind == "composite":
        if request.target is not None:
            raise ValueError("malformed request: composite requests must not set target")
        if not request.composite_targets:
            raise ValueError("malformed request: composite requests require at least one composite_target")
        for inner in request.composite_targets:
            if inner.kind == "composite":
                raise ValueError("malformed request: composite requests may not nest another composite request")
            normalize_service_request(inner)
        return {
            "kind": request.kind,
            "target": None,
            "families": [],
            "composite_target_count": len(request.composite_targets),
            "include_evidence": bool(request.include_evidence),
        }

    if not isinstance(request.target, str) or not request.target:
        raise ValueError("malformed request: target must be a non-empty string")

    if request.kind == "entity":
        if request.families:
            raise ValueError("malformed request: entity requests must not set families")
    elif request.kind == "artifact":
        if len(request.families) != 1:
            raise ValueError("malformed request: artifact requests require exactly one family")
        _validate_families(request.families)
    elif request.kind == "scoped":
        if not request.families:
            raise ValueError("malformed request: scoped requests require at least one family")
        _validate_families(request.families)

    if not isinstance(request.filters, dict):
        raise ValueError("malformed request: filters must be a dict")

    return {
        "kind": request.kind,
        "target": request.target,
        "families": sorted(request.families),
        "include_evidence": bool(request.include_evidence),
        "filters": {key: request.filters[key] for key in sorted(request.filters)},
    }


def _validate_families(families: tuple[str, ...]) -> None:
    if len(set(families)) != len(families):
        raise ValueError("malformed request: families must not contain duplicates")
    unknown = [f for f in families if f not in _VALID_FAMILIES]
    if unknown:
        raise ValueError(f"malformed request: unknown artifact family/families: {unknown!r}")


def resolve_scope(request: ServiceRequest) -> tuple[str, ...]:
    """Resolve a request's family scope, in the fixed declared order.

    Never expands a scoped/artifact request's own explicit allow-list
    (132B Section 7); an entity request resolves to all six families.
    """
    if request.kind == "entity":
        return SIX_ARTIFACT_FAMILIES
    allowed = set(request.families)
    return tuple(family for family in SIX_ARTIFACT_FAMILIES if family in allowed)
