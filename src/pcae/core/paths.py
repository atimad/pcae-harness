from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HarnessPath:
    path: Path

    @classmethod
    def cwd(cls) -> "HarnessPath":
        return cls(Path.cwd())

    def join(self, relative_path: Path) -> Path:
        return self.path / relative_path
