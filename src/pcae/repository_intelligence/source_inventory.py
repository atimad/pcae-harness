"""Repository source discovery and eligibility evaluation (120D pipeline stages 1-2).

Every function here is read-only: it observes the repository working
tree and git metadata without modifying anything, executing repository
code, or reaching outside the allowed input list frozen in 120B
Section 4 and reaffirmed in 120D Section 4.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class SourceInventoryError(RuntimeError):
    """Raised when a required, deterministic source cannot be observed.

    Fail-closed per 120B Section 15 / 120D Section 12: the generator
    must halt rather than proceed with a guessed or missing value for
    anything it treats as required.
    """


def _run_git(repo_root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_commit_sha(repo_root: Path) -> str:
    sha = _run_git(repo_root, ["rev-parse", "HEAD"])
    if not sha:
        raise SourceInventoryError(
            "Could not determine the current git commit SHA "
            "(git rev-parse HEAD failed). Repository knowledge "
            "cannot be attributed without a fixed commit."
        )
    return sha


def git_branch(repo_root: Path) -> str | None:
    return _run_git(repo_root, ["branch", "--show-current"]) or None


@dataclass(frozen=True)
class TopLevelEntry:
    """A single deterministically-observed top-level filesystem entry."""

    relative_path: str
    name: str
    is_dir: bool


def list_top_level_entries(repo_root: Path, subdirectory: str) -> tuple[TopLevelEntry, ...]:
    """List the direct children of ``subdirectory``, sorted by name.

    Read-only: uses ``Path.iterdir`` only, never opens or parses file
    contents. Sorting makes the result stable across filesystems and
    operating systems, per the 120D determinism risk mitigation.
    """
    target = repo_root / subdirectory
    if not target.is_dir():
        return ()
    entries = []
    for child in target.iterdir():
        if child.name.startswith("."):
            continue
        if child.name == "__pycache__":
            continue
        relative = f"{subdirectory}/{child.name}"
        entries.append(TopLevelEntry(relative_path=relative, name=child.name, is_dir=child.is_dir()))
    return tuple(sorted(entries, key=lambda e: e.relative_path))


_PYPROJECT_FIELD_RE = re.compile(r'^\s*(name|version|description)\s*=\s*"([^"]*)"\s*$')


def read_pyproject_project_fields(repo_root: Path) -> dict[str, str]:
    """Deterministically read name/version/description from ``[project]``.

    Uses a narrow regex over the ``[project]`` table only, rather than
    a TOML dependency, to stay within this prototype's minimal
    footprint. Read-only; the file is opened for reading only.
    """
    pyproject_path = repo_root / "pyproject.toml"
    fields: dict[str, str] = {}
    if not pyproject_path.is_file():
        return fields
    in_project_section = False
    for line in pyproject_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project_section = stripped == "[project]"
            continue
        if not in_project_section:
            continue
        match = _PYPROJECT_FIELD_RE.match(line)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def read_project_status_current_phase(repo_root: Path) -> str | None:
    """Deterministically read the first line of PROJECT_STATUS.md's

    ``## Current Phase`` section. Read-only; returns ``None`` (an
    honest unknown) rather than guessing if the file or section is
    absent, consistent with the no-inference rule.
    """
    status_path = repo_root / "PROJECT_STATUS.md"
    if not status_path.is_file():
        return None
    lines = status_path.read_text(encoding="utf-8").splitlines()
    in_section = False
    for line in lines:
        if line.strip() == "## Current Phase":
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("#"):
                break
            if line.strip():
                return line.strip()
    return None
