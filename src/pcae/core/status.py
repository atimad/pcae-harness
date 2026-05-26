from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.paths import HarnessPath


PROJECT_STATUS_RELATIVE_PATH = Path("PROJECT_STATUS.md")

# Phrases known to be stale because the features they describe are already
# implemented. Stale roadmap references in governance documents create
# orchestration risk: agents read them as forward-looking guidance and
# attempt to implement work that has already been done.
KNOWN_STALE_PHRASES: tuple[str, ...] = (
    "Implement `pcae end`",
    "Implement `pcae session end`",
)


@dataclass(frozen=True)
class CoherenceWarning:
    document: str
    message: str

    def to_dict(self) -> dict:
        return {"document": self.document, "message": self.message}


@dataclass(frozen=True)
class CoherenceResult:
    warnings: tuple[CoherenceWarning, ...]

    @property
    def coherent(self) -> bool:
        return len(self.warnings) == 0

    def to_dict(self) -> dict:
        return {
            "coherent": self.coherent,
            "warning_count": len(self.warnings),
            "warnings": [w.to_dict() for w in self.warnings],
        }


def check_project_status_coherence(root: HarnessPath) -> CoherenceResult:
    """Return coherence warnings for PROJECT_STATUS.md stale roadmap references."""
    path = root.join(PROJECT_STATUS_RELATIVE_PATH)
    if not path.is_file():
        return CoherenceResult(
            warnings=(
                CoherenceWarning(
                    document=str(PROJECT_STATUS_RELATIVE_PATH),
                    message="PROJECT_STATUS.md not found",
                ),
            )
        )
    text = path.read_text(encoding="utf-8")
    warnings = []
    for phrase in KNOWN_STALE_PHRASES:
        if phrase in text:
            warnings.append(
                CoherenceWarning(
                    document=str(PROJECT_STATUS_RELATIVE_PATH),
                    message=f"Stale roadmap reference: {phrase!r} — feature already implemented.",
                )
            )
    return CoherenceResult(warnings=tuple(warnings))
