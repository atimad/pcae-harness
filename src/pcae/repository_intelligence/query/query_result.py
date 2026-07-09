from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QueryResult:
    query_metadata: dict[str, Any]
    source_artifact: dict[str, Any]
    records: tuple[dict[str, Any], ...] = ()
    attribution: tuple[dict[str, Any], ...] = ()
    limitations: tuple[dict[str, Any], ...] = ()
    unknowns: tuple[str, ...] = ()
    boundary_disclosures: dict[str, Any] = field(default_factory=dict)
    disclaimers: dict[str, Any] = field(default_factory=dict)
    result_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_metadata": self.query_metadata,
            "source_artifact": self.source_artifact,
            "result_status": self.result_status,
            "records": list(self.records),
            "attribution": list(self.attribution),
            "limitations": list(self.limitations),
            "unknowns": list(self.unknowns),
            "boundary_disclosures": self.boundary_disclosures,
            "disclaimers": self.disclaimers,
            "determinism": {
                "deterministic": True,
                "rule": (
                    "identical Repository Knowledge Snapshot plus identical query "
                    "request produces identical logical result"
                ),
            },
        }
