from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import stat

from pcae.core.paths import HarnessPath


@dataclass(frozen=True)
class WriteResult:
    relative_path: Path
    created: bool


def write_missing_files(root: HarnessPath, templates: dict[Path, str]) -> list[WriteResult]:
    results: list[WriteResult] = []

    for relative_path, content in templates.items():
        target = root.join(relative_path)
        if target.exists():
            results.append(WriteResult(relative_path=relative_path, created=False))
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as file:
            file.write(content)
        make_executable_when_needed(target)
        results.append(WriteResult(relative_path=relative_path, created=True))

    return results


def make_executable_when_needed(path: Path) -> None:
    if path.suffix != ".sh" and path.name != "pre-commit":
        return

    current_mode = path.stat().st_mode
    path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
