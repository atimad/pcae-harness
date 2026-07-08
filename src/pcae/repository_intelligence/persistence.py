"""Repository Knowledge Snapshot persistence (120D pipeline stage 10).

Writes only. Never modifies, deletes, or reads back an existing
snapshot for extraction purposes. Persistence location follows the
conceptual model chosen in 120D Section 10:
``.pcae/repository-intelligence/``, with a ``latest.json`` file
(overwritten each run) and a ``snapshots/<timestamp>.json`` file
(one per run, never overwritten).

Writing these files to disk is not itself a governed commit; the
calling phase is responsible for committing the result through the
governed PCAE lifecycle (task contract, staged-file-aware commit,
``pcae task finish``, ``pcae phase complete``), per 120B Section 13.
"""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_OUTPUT_SUBDIR = "repository-intelligence"


def _serialize(snapshot: dict, *, pretty: bool) -> str:
    if pretty:
        return json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    return json.dumps(snapshot, separators=(",", ":"), sort_keys=True)


def write_snapshot(
    snapshot: dict,
    *,
    repo_root: Path,
    timestamp_slug: str,
    output_dir: Path | None = None,
    pretty: bool = False,
) -> dict:
    """Persist ``snapshot`` as both the latest and a timestamped file.

    Returns a dict with the two absolute paths written.
    """
    base_dir = output_dir if output_dir is not None else repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR
    snapshots_dir = base_dir / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    serialized = _serialize(snapshot, pretty=pretty)

    latest_path = base_dir / "latest.json"
    latest_path.write_text(serialized, encoding="utf-8")

    timestamped_path = snapshots_dir / f"{timestamp_slug}.json"
    timestamped_path.write_text(serialized, encoding="utf-8")

    return {
        "latest_path": str(latest_path),
        "snapshot_path": str(timestamped_path),
    }
