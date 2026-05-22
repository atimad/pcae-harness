from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from pcae.core.paths import HarnessPath


@dataclass(frozen=True)
class GitChange:
    path: Path
    status: str


def read_git_changes(root: HarnessPath) -> tuple[GitChange, ...]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=root.path,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(parse_status_line(line) for line in completed.stdout.splitlines() if line)


def parse_status_line(line: str) -> GitChange:
    status = line[:2]
    raw_path = line[3:]
    if " -> " in raw_path:
        raw_path = raw_path.split(" -> ", 1)[1]
    return GitChange(path=Path(raw_path), status=status)
