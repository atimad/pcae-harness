from __future__ import annotations

import json

from pcae.advisory.context.context_package import RepositoryIntelligenceContextPackage


def serialize_context_package(
    package: RepositoryIntelligenceContextPackage, *, pretty: bool = False
) -> str:
    """Produce deterministic serialized output for an assembled
    Advisory context package (122D S5, Stage 8's "produce deterministic
    serialized output"). Formatting never changes logical content."""
    indent = 2 if pretty else None
    return json.dumps(package.to_dict(), indent=indent, sort_keys=True)
