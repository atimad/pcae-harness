from __future__ import annotations

import json

from pcae.repository_intelligence.query.query_result import QueryResult


def format_result(result: QueryResult, *, pretty: bool = False) -> str:
    indent = 2 if pretty else None
    return json.dumps(result.to_dict(), indent=indent, sort_keys=True)
