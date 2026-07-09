from __future__ import annotations

import json

from pcae.repository_intelligence.change_impact.change_impact_report import (
    ChangeImpactReport,
)


def serialize_change_impact_report(
    report: ChangeImpactReport, *, pretty: bool = False
) -> str:
    indent = 2 if pretty else None
    return json.dumps(report.to_dict(), indent=indent, sort_keys=True)
