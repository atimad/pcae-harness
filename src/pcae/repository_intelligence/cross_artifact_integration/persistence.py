"""Cross-Artifact Knowledge Integration persistence (130D pipeline).

Writes only. Never modifies, deletes, or reads back an existing
integration artifact for extraction purposes. Reuses the shared
deterministic JSON serializer (``serialize_deterministic_json``)
rather than reintroducing parallel serialization logic, mirroring
Dependency Knowledge Graph's own persistence module exactly (126D
Section 9 / 130D Section 17).
"""

from __future__ import annotations

from pathlib import Path

from pcae.repository_intelligence.serialization import serialize_deterministic_json

DEFAULT_OUTPUT_SUBDIR = "repository-intelligence/cross-artifact-integration"


def write_integration_package(
    integration: dict,
    *,
    repo_root: Path,
    timestamp_slug: str,
    output_dir: Path | None = None,
    pretty: bool = False,
) -> dict:
    """Persist ``integration`` as both the latest and a timestamped file.

    Returns a dict with the two absolute paths written.
    """
    base_dir = output_dir if output_dir is not None else repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR
    packages_dir = base_dir / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)

    serialized = serialize_deterministic_json(integration, pretty=pretty)

    timestamped_path = packages_dir / f"{timestamp_slug}.json"
    timestamped_path.write_text(serialized)

    latest_path = base_dir / "latest.json"
    latest_path.write_text(serialized)

    return {
        "latest": str(latest_path),
        "timestamped": str(timestamped_path),
    }
