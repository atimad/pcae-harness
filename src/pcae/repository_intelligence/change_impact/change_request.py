from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChangeImpactRequest:
    """Bounded request for deterministic Change Impact reporting."""

    requested_change: str
    target_entities: tuple[str, ...]
    repository_scope: str | None = None
    evaluation_scope: tuple[str, ...] = ("entity_lookup",)
    metadata: dict[str, str] = field(default_factory=dict)

    def normalized(self) -> dict:
        return {
            "requested_change": self.requested_change,
            "repository_scope": self.repository_scope,
            "evaluation_scope": list(self.evaluation_scope),
            "target_entities": list(self.target_entities),
            "metadata": {key: self.metadata[key] for key in sorted(self.metadata)},
        }
