"""Top-level Cross-Artifact Knowledge Integration generation orchestration.

Wires together the 130D pipeline stages implemented across
``integration_builder``, ``integration_validation``, and
``persistence``. This module is the only intended external entry
point into the ``cross_artifact_integration`` package (used by the CLI
handler and by tests).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pcae.repository_intelligence.cross_artifact_integration.integration_builder import (
    IntegrationGenerationError,
    build_integration_content,
)
from pcae.repository_intelligence.cross_artifact_integration.integration_validation import (
    validate_integration_package,
)
from pcae.repository_intelligence.cross_artifact_integration.persistence import (
    write_integration_package,
)

__all__ = [
    "IntegrationGenerationError",
    "build_integration_content",
    "generate_cross_artifact_integration",
]


def generate_cross_artifact_integration(
    change_impact_path: Path,
    dependency_graph_path: Path,
    *,
    repo_root: Path,
    output_dir: Path | None = None,
    pretty: bool = False,
    repository_knowledge_snapshot_path: Path | None = None,
    historical_memory_path: Path | None = None,
    advisory_context_path: Path | None = None,
) -> dict[str, Any]:
    """Generate, validate, and persist a Cross-Artifact Knowledge
    Integration package. Fails closed (raises ``IntegrationGenerationError``)
    without writing anything if construction or validation fails.
    """
    now = datetime.now(timezone.utc)
    generated_at_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamp_slug = now.strftime("%Y%m%dT%H%M%S%fZ")

    integration = build_integration_content(
        change_impact_path,
        dependency_graph_path,
        generated_at_utc=generated_at_utc,
        repository_knowledge_snapshot_path=repository_knowledge_snapshot_path,
        historical_memory_path=historical_memory_path,
        advisory_context_path=advisory_context_path,
    )
    validate_integration_package(integration)

    paths = write_integration_package(
        integration,
        repo_root=repo_root,
        timestamp_slug=timestamp_slug,
        output_dir=output_dir,
        pretty=pretty,
    )

    return {
        "integration_configuration": integration["integration_metadata"][
            "integration_configuration"
        ],
        "change_impact_path": str(change_impact_path),
        "dependency_graph_path": str(dependency_graph_path),
        "referenced_artifact_count": len(integration["referenced_artifacts"]),
        "dependency_context_count": len(integration["dependency_context"]),
        "entity_resolution_count": len(integration["entity_resolutions"]),
        "unresolved_identity_count": len(integration["unresolved_identities"]),
        "latest_path": paths["latest"],
        "package_path": paths["timestamped"],
    }
