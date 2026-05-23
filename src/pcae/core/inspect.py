from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.manifest import MANIFEST_ENTRIES, ManifestEntry
from pcae.core.paths import HarnessPath
from pcae.core.policy import POLICY_RELATIVE_PATH, load_policy


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
    policy: PolicyInspection

    @property
    def missing_paths(self) -> tuple[InspectedPath, ...]:
        return tuple(path for path in self.paths if not path.present)

    @property
    def present_paths(self) -> tuple[InspectedPath, ...]:
        return tuple(path for path in self.paths if path.present)


@dataclass(frozen=True)
class PolicyInspection:
    relative_path: Path
    present: bool
    source: str
    protected_pattern_count: int
    architecture_zones: dict[str, int]
    valid: bool
    error: str | None


def inspect_harness(root: HarnessPath) -> InspectionResult:
    inspected = tuple(
        InspectedPath(entry=entry, present=root.join(entry.relative_path).is_file())
        for entry in MANIFEST_ENTRIES
    )
    policy = load_policy(root)
    return InspectionResult(
        root=root,
        paths=inspected,
        policy=PolicyInspection(
            relative_path=POLICY_RELATIVE_PATH,
            present=policy.file_exists,
            source=policy.source,
            protected_pattern_count=len(policy.protected_patterns),
            architecture_zones={
                name: len(patterns)
                for name, patterns in policy.architecture_zones.items()
            },
            valid=policy.valid,
            error=policy.error,
        ),
    )
