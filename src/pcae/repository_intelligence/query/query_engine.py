from __future__ import annotations

from pathlib import Path
from typing import Any

from pcae.repository_intelligence.query.attribution import require_attribution
from pcae.repository_intelligence.query.query_request import (
    QueryRequest,
    validate_request,
)
from pcae.repository_intelligence.query.query_result import QueryResult
from pcae.repository_intelligence.query.snapshot_loader import load_snapshot


class QueryExecutionError(Exception):
    """Raised when query execution must fail closed."""


def execute_query(snapshot_path: Path, request: QueryRequest) -> QueryResult:
    try:
        validate_request(request)
    except ValueError as exc:
        raise QueryExecutionError(str(exc)) from exc

    snapshot = load_snapshot(snapshot_path)
    return evaluate_query(snapshot, request)


def evaluate_query(snapshot: dict[str, Any], request: QueryRequest) -> QueryResult:
    query_metadata = request.normalized()
    source_artifact = _source_artifact(snapshot)
    base_limitations = _sort_limitations(snapshot.get("snapshot_limitations", []))
    boundaries = dict(snapshot.get("boundary_disclosures", {}))
    disclaimers = dict(snapshot.get("disclaimers", {}))

    records: list[dict[str, Any]]
    status = "ok"
    unknowns: list[str] = []
    limitations = list(base_limitations)

    if request.category == "entity_lookup":
        records = _select_records(
            snapshot.get("architectural_entities", []),
            request.target or "",
            ("entity_id", "entity_name", "entity_path"),
        )
        if not records:
            status = "unknown"
            unknowns.append(f"No architectural entity matched target {request.target!r}.")
            limitations.append(_query_limitation("missing_data", "Requested entity is not present in the snapshot."))
    elif request.category == "capability_lookup":
        records = _select_records(
            snapshot.get("capabilities", []),
            request.target or "",
            ("capability_id", "capability_name"),
        )
        if not records:
            status = "unknown"
            unknowns.append(f"No capability matched target {request.target!r}.")
            limitations.append(_query_limitation("missing_data", "Requested capability is not present in the snapshot."))
    elif request.category == "architectural_contract_lookup":
        records = _select_records(
            snapshot.get("contracts", []),
            request.target or "",
            ("contract_id", "contract_name", "contract_version"),
        )
        if not records:
            status = "unknown"
            unknowns.append(f"No architectural contract matched target {request.target!r}.")
            limitations.append(_query_limitation("missing_data", "Requested contract is not present in the snapshot."))
    elif request.category == "attribution_lookup":
        records = _attribution_records(snapshot, request.target or "")
        if not records:
            status = "unknown"
            unknowns.append(f"No attribution-bearing record matched target {request.target!r}.")
            limitations.append(_query_limitation("missing_data", "Requested attribution target is not present in the snapshot."))
    elif request.category == "limitation_lookup":
        records = base_limitations
        if not records:
            status = "unknown"
            limitations.append(_query_limitation("missing_data", "Snapshot has no limitation records."))
    elif request.category == "boundary_lookup":
        records = [{"boundary_disclosures": boundaries, "disclaimers": disclaimers}]
    else:
        raise QueryExecutionError(f"unsupported query category: {request.category}")

    try:
        attribution = _collect_attribution(records, request.category)
    except ValueError as exc:
        raise QueryExecutionError(str(exc)) from exc
    limitations.extend(_record_limitations(records))

    result_status = status if records or unknowns else "ok"
    return QueryResult(
        query_metadata=query_metadata,
        source_artifact=source_artifact,
        records=tuple(_sort_records(records)),
        attribution=tuple(_sort_attribution(attribution)),
        limitations=tuple(_sort_limitations(limitations)),
        unknowns=tuple(sorted(unknowns)),
        boundary_disclosures=boundaries,
        disclaimers=disclaimers,
        result_status=result_status,
    )


def _source_artifact(snapshot: dict[str, Any]) -> dict[str, Any]:
    envelope = snapshot.get("envelope", {})
    identity = snapshot.get("snapshot_identity", {})
    repository_context = envelope.get("repository_context", {})
    return {
        "artifact_id": envelope.get("artifact_id"),
        "artifact_type": envelope.get("artifact_type"),
        "snapshot_id": identity.get("snapshot_id"),
        "executable_schema_version": identity.get("executable_schema_version"),
        "repository_commit": repository_context.get("repository_commit"),
    }


def _select_records(
    records: Any,
    target: str,
    fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        return []
    selected = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if any(record.get(field) == target for field in fields):
            selected.append(dict(record))
    return _sort_records(selected)


def _attribution_records(snapshot: dict[str, Any], target: str) -> list[dict[str, Any]]:
    candidate_sections = (
        ("architectural_entities", ("entity_id", "entity_name", "entity_path")),
        ("capabilities", ("capability_id", "capability_name")),
        ("contracts", ("contract_id", "contract_name", "contract_version")),
    )
    attribution_records: list[dict[str, Any]] = []
    for section, fields in candidate_sections:
        for record in _select_records(snapshot.get(section, []), target, fields):
            try:
                record_attribution = require_attribution(record)
            except ValueError as exc:
                raise QueryExecutionError(str(exc)) from exc
            for attribution in record_attribution:
                attribution_records.append(dict(attribution))
    return _sort_records(attribution_records)


def _collect_attribution(
    records: list[dict[str, Any]],
    category: str,
) -> list[dict[str, Any]]:
    if category in {"limitation_lookup", "boundary_lookup"}:
        return []
    attribution: list[dict[str, Any]] = []
    for record in records:
        if category == "attribution_lookup":
            attribution.append(dict(record))
        else:
            for item in require_attribution(record):
                attribution.append(dict(item))
    return attribution


def _record_limitations(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    limitations: list[dict[str, Any]] = []
    for record in records:
        value = record.get("limitations")
        if isinstance(value, list):
            limitations.extend(dict(item) for item in value if isinstance(item, dict))
    return limitations


def _query_limitation(limitation_type: str, description: str) -> dict[str, str]:
    return {
        "limitation_type": limitation_type,
        "limitation_description": description,
    }


def _stable_key(record: dict[str, Any]) -> str:
    for field in (
        "entity_id",
        "capability_id",
        "contract_id",
        "source_id",
        "limitation_type",
    ):
        value = record.get(field)
        if isinstance(value, str):
            return value
    return repr(sorted(record.items()))


def _sort_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=_stable_key)


def _sort_attribution(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = {_stable_key(record): record for record in records}
    return [deduped[key] for key in sorted(deduped)]


def _sort_limitations(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = {
        (record.get("limitation_type", ""), record.get("limitation_description", "")): record
        for record in records
        if isinstance(record, dict)
    }
    return [deduped[key] for key in sorted(deduped)]
