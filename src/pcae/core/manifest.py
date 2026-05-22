from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManifestEntry:
    relative_path: Path
    label: str
    category: str


MANIFEST_ENTRIES: tuple[ManifestEntry, ...] = (
    ManifestEntry(Path("AGENTS.md"), "Agent instructions", "Required files"),
    ManifestEntry(Path("PROJECT_STATUS.md"), "Project status", "Required files"),
    ManifestEntry(Path("CHANGELOG.md"), "Changelog", "Required files"),
    ManifestEntry(Path("tasks/TODO.md"), "TODO tasks", "Task files"),
    ManifestEntry(Path("tasks/DONE.md"), "Completed tasks", "Task files"),
    ManifestEntry(Path("tasks/DECISIONS.md"), "Decision log", "Task files"),
    ManifestEntry(Path(".githooks/pre-commit"), "Pre-commit hook", "Git hooks"),
    ManifestEntry(
        Path("scripts/check-docs-updated.sh"),
        "POSIX docs check",
        "Check scripts",
    ),
    ManifestEntry(
        Path("scripts/check-docs-updated.ps1"),
        "PowerShell docs check",
        "Check scripts",
    ),
)
