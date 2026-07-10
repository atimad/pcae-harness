"""Historical Memory Builder (Track 127, Phase 127E prototype).

Deterministic, read-only construction of a Historical Memory Snapshot
artifact from git commit history, ``tasks/done/*.md`` task contracts,
and an existing Repository Knowledge Snapshot (consumed exclusively
through the Track 121 Query Layer). No historical reasoning, no
inference, no recommendations, no execution capability.
"""

from __future__ import annotations

from pcae.repository_intelligence.historical_memory.historical_builder import (
    HistoricalGenerationError,
    build_historical_content,
)
from pcae.repository_intelligence.historical_memory.historical_generator import (
    generate_historical_memory,
)

__all__ = [
    "HistoricalGenerationError",
    "build_historical_content",
    "generate_historical_memory",
]
