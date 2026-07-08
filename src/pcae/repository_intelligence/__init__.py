"""Repository Intelligence read-only prototype (Phase 120E).

Deterministic, read-only generator for the Repository Knowledge Snapshot
artifact family, conforming to
``schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json``.

Boundaries frozen in Phase 120B and reaffirmed in Phase 120D apply to
every module in this package: read-only, deterministic, observe-only,
no execution, no repository/runtime mutation, no AI inference, no
network access, no Advisory/Decision Evaluation integration. No other
Repository Intelligence artifact family is implemented here.
"""

from __future__ import annotations
