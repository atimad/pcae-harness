"""Cross-Artifact Knowledge Integration Builder (Track 130, Phase 130E prototype).

Deterministic, read-only construction of a derivative integration
package connecting existing Change Impact and Dependency Knowledge
Graph content via already-existing stable identifiers. No reasoning,
no inference, no traversal, no execution capability. See 130A-130D for
architecture, contract, verification, and plan.
"""

from __future__ import annotations

from pcae.repository_intelligence.cross_artifact_integration.integration_builder import (
    IntegrationGenerationError,
    build_integration_content,
)
from pcae.repository_intelligence.cross_artifact_integration.integration_generator import (
    generate_cross_artifact_integration,
)

__all__ = [
    "IntegrationGenerationError",
    "build_integration_content",
    "generate_cross_artifact_integration",
]
