from __future__ import annotations

from pcae.repository_intelligence.change_impact.change_impact_report import (
    ChangeImpactReport,
)
from pcae.repository_intelligence.serialization import serialize_deterministic_json


def serialize_change_impact_report(
    report: ChangeImpactReport, *, pretty: bool = False
) -> str:
    return serialize_deterministic_json(report.to_dict(), pretty=pretty)
