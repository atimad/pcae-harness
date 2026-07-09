from __future__ import annotations

from pcae.advisory.context.context_package import RepositoryIntelligenceContextPackage
from pcae.repository_intelligence.serialization import serialize_deterministic_json


def serialize_context_package(
    package: RepositoryIntelligenceContextPackage, *, pretty: bool = False
) -> str:
    """Produce deterministic serialized output for an assembled
    Advisory context package (122D S5, Stage 8's "produce deterministic
    serialized output"). Formatting never changes logical content."""
    return serialize_deterministic_json(package.to_dict(), pretty=pretty)
