"""Top-level Repository Knowledge Snapshot generation orchestration.

Wires together the 120D pipeline stages implemented across
``source_inventory``, ``attribution``, ``snapshot_builder``, and
``persistence``. This module is the only intended external entry
point into the ``repository_intelligence`` package (used by the CLI
handler and by tests).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pcae.repository_intelligence.persistence import write_snapshot
from pcae.repository_intelligence.snapshot_builder import (
    SnapshotGenerationError,
    build_snapshot_content,
)

__all__ = ["SnapshotGenerationError", "generate_snapshot"]


def generate_snapshot(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
    pretty: bool = False,
) -> dict:
    """Generate and persist one Repository Knowledge Snapshot.

    Returns generation metadata (not the snapshot content itself):
    artifact/snapshot identifiers, counts, and the paths written.

    Raises ``SnapshotGenerationError`` if a required deterministic
    source cannot be observed (fail-closed; nothing is persisted in
    that case).
    """
    now = datetime.now(timezone.utc)
    generated_at_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    snapshot = build_snapshot_content(repo_root, generated_at_utc=generated_at_utc)

    # Microsecond precision only in the persisted filename slug (an
    # approved, non-substantive metadata identifier, per 120B Section
    # 6) so two runs within the same second do not collide and
    # silently overwrite each other's timestamped snapshot file.
    timestamp_slug = now.strftime("%Y%m%dT%H%M%S%f") + "Z"
    paths = write_snapshot(
        snapshot,
        repo_root=repo_root,
        timestamp_slug=timestamp_slug,
        output_dir=output_dir,
        pretty=pretty,
    )

    return {
        "artifact_id": snapshot["envelope"]["artifact_id"],
        "snapshot_id": snapshot["snapshot_identity"]["snapshot_id"],
        "repository_commit": snapshot["envelope"]["repository_context"]["repository_commit"],
        "generated_at_utc": generated_at_utc,
        "architectural_entity_count": len(snapshot["architectural_entities"]),
        "subsystem_count": len(snapshot["subsystems"]),
        "knowledge_claim_count": len(snapshot["knowledge_claims"]),
        "knowledge_source_count": len(snapshot["knowledge_sources"]),
        "unknown_count": len(snapshot["unknowns"]),
        "latest_path": paths["latest_path"],
        "snapshot_path": paths["snapshot_path"],
    }
