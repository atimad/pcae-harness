"""Historical Memory persistence (127D pipeline stage 10).

Writes only. Never modifies, deletes, or reads back an existing
Historical Memory artifact for extraction purposes. Mirrors
``pcae.repository_intelligence.dependency_graph.persistence`` but
writes to a distinct location so no artifact family is ever confused
with another.

Reuses the Track 124 shared deterministic JSON serializer
(``serialize_deterministic_json``) rather than reintroducing parallel
serialization logic, per 127D Section 6 stage 10.
"""

from __future__ import annotations

from pathlib import Path

from pcae.repository_intelligence.serialization import serialize_deterministic_json

DEFAULT_OUTPUT_SUBDIR = "repository-intelligence/historical-memory"


def write_historical_snapshot(
    historical: dict,
    *,
    repo_root: Path,
    timestamp_slug: str,
    output_dir: Path | None = None,
    pretty: bool = False,
) -> dict:
    """Persist ``historical`` as both the latest and a timestamped file.

    Returns a dict with the two absolute paths written.
    """
    base_dir = output_dir if output_dir is not None else repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR
    snapshots_dir = base_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    serialized = serialize_deterministic_json(historical, pretty=pretty)
    if pretty:
        serialized += "\n"

    latest_path = base_dir / "latest.json"
    latest_path.write_text(serialized, encoding="utf-8")

    timestamped_path = snapshots_dir / f"{timestamp_slug}.json"
    timestamped_path.write_text(serialized, encoding="utf-8")

    return {
        "latest_path": str(latest_path),
        "snapshot_path": str(timestamped_path),
    }
