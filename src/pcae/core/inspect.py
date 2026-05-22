from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.manifest import MANIFEST_ENTRIES, ManifestEntry
from pcae.core.paths import HarnessPath


@dataclass(frozen=True)
class InspectedPath:
    entry: ManifestEntry
    present: bool

    @property
    def relative_path(self) -> Path:
        return self.entry.relative_path


@dataclass(frozen=True)
class InspectionResult:
    root: HarnessPath
    paths: tuple[InspectedPath, ...]

    @property
    def missing_paths(self) -> tuple[InspectedPath, ...]:
        return tuple(path for path in self.paths if not path.present)

    @property
    def present_paths(self) -> tuple[InspectedPath, ...]:
        return tuple(path for path in self.paths if path.present)


def inspect_harness(root: HarnessPath) -> InspectionResult:
    inspected = tuple(
        InspectedPath(entry=entry, present=root.join(entry.relative_path).is_file())
        for entry in MANIFEST_ENTRIES
    )
    return InspectionResult(root=root, paths=inspected)
