from __future__ import annotations

import json
from typing import Any


def serialize_deterministic_json(payload: dict[str, Any], *, pretty: bool = False) -> str:
    """Serialize Repository Intelligence payloads with stable JSON ordering."""
    indent = 2 if pretty else None
    return json.dumps(payload, indent=indent, sort_keys=True)
