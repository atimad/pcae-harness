from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import stat

from pcae.core.paths import HarnessPath


@dataclass(frozen=True)
class WriteResult:
    relative_path: Path
    created: bool


@dataclass(frozen=True)
class WritePlan:
    relative_path: Path
    kind: str
    exists: bool

    @property
    def would_create(self) -> bool:
        return not self.exists


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


def plan_missing_files(root: HarnessPath, templates: dict[Path, str]) -> list[WritePlan]:
    plans: list[WritePlan] = []
    directories = parent_directories(templates)

    for relative_path in directories:
        plans.append(
            WritePlan(
                relative_path=relative_path,
                kind="directory",
                exists=root.join(relative_path).is_dir(),
            )
        )

    for relative_path in templates:
        plans.append(
            WritePlan(
                relative_path=relative_path,
                kind="file",
                exists=root.join(relative_path).exists(),
            )
        )

    return plans


def parent_directories(templates: dict[Path, str]) -> tuple[Path, ...]:
    directories: set[Path] = set()
    for relative_path in templates:
        parent = relative_path.parent
        while parent != Path("."):
            directories.add(parent)
            parent = parent.parent
    return tuple(sorted(directories, key=lambda path: path.as_posix()))


def make_executable_when_needed(path: Path) -> None:
    if path.suffix != ".sh" and path.name != "pre-commit":
        return

    current_mode = path.stat().st_mode
    path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
