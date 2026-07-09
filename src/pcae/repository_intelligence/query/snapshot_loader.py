from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUPPORTED_EXECUTABLE_SCHEMA_VERSION = "119O.1.0-json-schema"


class SnapshotLoadError(Exception):
    """Raised when a Repository Knowledge Snapshot cannot be loaded."""


class SnapshotCompatibilityError(Exception):
    """Raised when a snapshot is not supported by the query prototype."""


def load_snapshot(path: Path) -> dict[str, Any]:
    """Load a Repository Knowledge Snapshot artifact without modifying it."""
    if not path.is_file():
        raise SnapshotLoadError(f"snapshot not found: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SnapshotLoadError(f"snapshot is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise SnapshotLoadError("snapshot JSON root must be an object")
    verify_snapshot_compatibility(data)
    return data


def verify_snapshot_compatibility(snapshot: dict[str, Any]) -> None:
    identity = snapshot.get("snapshot_identity")
    if not isinstance(identity, dict):
        raise SnapshotCompatibilityError("snapshot_identity is missing or invalid")

    version = identity.get("executable_schema_version")
    if version != SUPPORTED_EXECUTABLE_SCHEMA_VERSION:
        raise SnapshotCompatibilityError(
            "unsupported Repository Knowledge Snapshot executable schema version: "
            f"{version!r}"
        )

    required_fields = (
        "envelope",
        "architectural_entities",
        "capabilities",
        "knowledge_sources",
        "snapshot_limitations",
        "boundary_disclosures",
        "disclaimers",
    )
    missing = [field for field in required_fields if field not in snapshot]
    if missing:
        raise SnapshotCompatibilityError(
            "snapshot is missing required query input fields: " + ", ".join(missing)
        )
