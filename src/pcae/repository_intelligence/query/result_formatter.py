from __future__ import annotations

from pcae.repository_intelligence.query.query_result import QueryResult
from pcae.repository_intelligence.serialization import serialize_deterministic_json


def format_result(result: QueryResult, *, pretty: bool = False) -> str:
    return serialize_deterministic_json(result.to_dict(), pretty=pretty)
