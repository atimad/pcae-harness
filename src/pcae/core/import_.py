from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from pcae.core.export import GOVERNANCE_BUNDLE_REQUIRED_KEYS


FUTURE_IMPORT_TARGETS = (
    ".pcae/session.json",
    ".pcae/architecture-history.json",
    ".pcae/policy.toml",
    "tasks/active/",
)


@dataclass(frozen=True)
class GovernanceBundlePreview:
    data: dict
    future_import_targets: tuple[str, ...] = FUTURE_IMPORT_TARGETS


def read_governance_bundle_preview(path: Path) -> GovernanceBundlePreview:
    if not path.is_file():
        raise ValueError(f"Governance bundle not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid governance bundle JSON: {error.msg}.") from error

    if not isinstance(data, dict):
        raise ValueError("Invalid governance bundle: expected a JSON object.")

    missing_keys = sorted(GOVERNANCE_BUNDLE_REQUIRED_KEYS - set(data))
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(f"Invalid governance bundle: missing required keys: {missing}.")

    return GovernanceBundlePreview(data=data)
