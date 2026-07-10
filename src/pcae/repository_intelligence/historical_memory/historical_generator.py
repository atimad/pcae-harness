"""Top-level Historical Memory generation orchestration.

Wires together the 127D pipeline stages implemented across
``historical_builder``, ``historical_validation``, and
``persistence``. This module is the only intended external entry
point into the ``historical_memory`` package (used by the CLI handler
and by tests).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pcae.repository_intelligence.historical_memory.historical_builder import (
    HistoricalGenerationError,
    build_historical_content,
)
from pcae.repository_intelligence.historical_memory.historical_validation import (
    validate_historical_snapshot,
)
from pcae.repository_intelligence.historical_memory.persistence import (
    write_historical_snapshot,
)

__all__ = ["HistoricalGenerationError", "generate_historical_memory"]


def generate_historical_memory(
    snapshot_path: Path,
    *,
    repo_root: Path,
    output_dir: Path | None = None,
    pretty: bool = False,
) -> dict:
    """Generate and persist one Historical Memory Snapshot.

    Returns generation metadata (not the snapshot content itself):
    artifact/snapshot identifiers, counts, and the paths written.

    Raises ``HistoricalGenerationError`` if the source Repository
    Knowledge Snapshot or repository history is invalid, unsupported,
    or missing required provenance/limitation/boundary material
    (fail-closed; nothing is persisted in that case).
    """
    now = datetime.now(timezone.utc)
    generated_at_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    historical = build_historical_content(
        repo_root, snapshot_path, generated_at_utc=generated_at_utc
    )
    validate_historical_snapshot(historical)

    # Microsecond precision only in the persisted filename slug (an
    # approved, non-substantive metadata identifier, mirroring 120B
    # Section 6) so two runs within the same second do not collide.
    timestamp_slug = now.strftime("%Y%m%dT%H%M%S%f") + "Z"
    paths = write_historical_snapshot(
        historical,
        repo_root=repo_root,
        timestamp_slug=timestamp_slug,
        output_dir=output_dir,
        pretty=pretty,
    )

    return {
        "artifact_id": historical["envelope"]["artifact_id"],
        "snapshot_id": historical["snapshot_identity"]["snapshot_id"],
        "repository_commit": historical["envelope"]["repository_context"]["repository_commit"],
        "source_snapshot_path": str(snapshot_path),
        "generated_at_utc": generated_at_utc,
        "event_count": len(historical["historical_events"]),
        "claim_count": len(historical["historical_claims"]),
        "phase_lineage_count": len(historical["phase_lineage"]),
        "release_lineage_count": len(historical["release_lineage"]),
        "repair_hardening_count": len(historical["repair_hardening_history"]),
        "relationship_count": len(historical["historical_relationships"]),
        "historical_source_count": len(historical["historical_sources"]),
        "unknown_gap_count": len(historical["unknowns_gaps"]),
        "latest_path": paths["latest_path"],
        "snapshot_path": paths["snapshot_path"],
    }
