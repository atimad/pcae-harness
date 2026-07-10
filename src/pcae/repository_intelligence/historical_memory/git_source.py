"""Read-only git/task-contract source discovery (127D pipeline stages 1-3).

The only module in this package permitted to invoke ``git`` as a
subprocess, mirroring exactly the precedent already established by
``pcae.repository_intelligence.source_inventory`` for Track 120 (which
this module does not modify, per 127B Section 10's read-only
contract). ``historical_builder.py`` itself never imports
``subprocess`` -- it consumes only the plain data structures this
module returns.

Every function here is read-only: it observes git history and
``tasks/done/`` content without modifying anything, executing
repository code, or reaching outside the bounded input set 127D
Section 2/5.1 froze (git log for an explicit commit range, task
contract files, nothing else).
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class HistoricalSourceError(RuntimeError):
    """Raised when a required, deterministic historical source cannot be observed.

    Fail-closed per 127B Section 9 / 127D Section 9: the builder must
    halt rather than proceed with a guessed or missing value for
    anything it treats as required.
    """


def _run_git(repo_root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def git_head_commit_sha(repo_root: Path) -> str:
    """The current commit, used as the snapshot's own anchor."""
    output = _run_git(repo_root, ["rev-parse", "HEAD"])
    sha = output.strip() if output else None
    if not sha:
        raise HistoricalSourceError(
            "Could not determine the current git commit SHA "
            "(git rev-parse HEAD failed). Historical Memory cannot be "
            "attributed without a fixed commit anchor."
        )
    return sha


@dataclass(frozen=True)
class TaskIntroduction:
    """The commit that introduced a given ``tasks/done/`` file, if resolvable.

    ``commit_sha``/``commit_author_date_utc`` are ``None`` when git
    history could not establish an introducing commit (e.g. a
    shallow clone, or a file introduced before history tracking began)
    -- an honest unknown, never a fabricated value (127D Section 5.3's
    null-boundary resolution of 127C Finding 2).
    """

    relative_path: str
    commit_sha: str | None
    commit_author_date_utc: str | None


_LOG_FORMAT = "%H%x1f%aI"


def resolve_task_introduction(repo_root: Path, relative_path: str) -> TaskIntroduction:
    """Resolve the commit that added ``relative_path`` at its own exact path.

    Bounded to exactly one file's own history; never an unbounded or
    ambient ``git log`` call, per 127D Section 5.1.

    Deliberately omits ``--follow``: task contract files in this
    repository share heavy templated boilerplate (identical section
    headers across nearly every file), which causes git's content-
    similarity rename heuristic (invoked by ``--follow``) to falsely
    treat unrelated files as renames of one another, collapsing
    distinct task contracts onto the same introducing commit. Plain
    ``--diff-filter=A`` against the file's current path correctly
    resolves the commit that added it at that path -- for a task
    contract that moved from ``tasks/active/`` to ``tasks/done/``
    (an add-at-new-path, not a tracked rename, since this repository's
    governed task-finish flow does not use ``git mv``), this is also
    the semantically correct "task completed" commit, not merely an
    implementation detail.
    """
    output = _run_git(
        repo_root,
        [
            "log",
            "--diff-filter=A",
            f"--format={_LOG_FORMAT}",
            "--",
            relative_path,
        ],
    )
    if not output or not output.strip():
        return TaskIntroduction(
            relative_path=relative_path, commit_sha=None, commit_author_date_utc=None
        )
    # The earliest introduction is the last line git log prints (oldest last).
    lines = [line for line in output.strip().splitlines() if line.strip()]
    if not lines:
        return TaskIntroduction(
            relative_path=relative_path, commit_sha=None, commit_author_date_utc=None
        )
    sha, _, date = lines[-1].partition("\x1f")
    if not sha or not date:
        return TaskIntroduction(
            relative_path=relative_path, commit_sha=None, commit_author_date_utc=None
        )
    return TaskIntroduction(
        relative_path=relative_path, commit_sha=sha, commit_author_date_utc=date
    )


def list_task_contract_files(repo_root: Path) -> tuple[str, ...]:
    """Deterministically list ``tasks/done/*.md`` relative paths, sorted by name.

    Read-only: uses ``Path.iterdir`` only, never opens a file here.
    Sorting makes the result stable across filesystems, matching the
    same determinism-risk mitigation ``source_inventory.list_top_level_
    entries`` already applies for Track 120.
    """
    tasks_done = repo_root / "tasks" / "done"
    if not tasks_done.is_dir():
        return ()
    names = [p.name for p in tasks_done.iterdir() if p.suffix == ".md"]
    return tuple(f"tasks/done/{name}" for name in sorted(names))


_FIELD_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class TaskContract:
    """Deterministically parsed fields from one ``tasks/done/*.md`` file.

    Parsing is a fixed, rule-based extraction of already-labeled
    Markdown sections (``## Task ID``, ``## Title``, ...) -- never
    interpretation of prose content. A missing section yields ``None``
    for that field, an honest unknown, not a guessed default.
    """

    relative_path: str
    task_id: str | None
    title: str | None
    status: str | None
    mode: str | None
    goal: str | None
    created_timestamp: str | None


def _extract_section(text: str, heading: str) -> str | None:
    """Extract the body text directly under ``## {heading}`` up to the next ``##``."""
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n+(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    body = match.group(1).strip()
    return body if body else None


def parse_task_contract(path: Path) -> TaskContract:
    """Deterministically parse one task contract file. Read-only."""
    text = path.read_text(encoding="utf-8")
    relative_path = "tasks/done/" + path.name
    return TaskContract(
        relative_path=relative_path,
        task_id=_extract_section(text, "Task ID"),
        title=_extract_section(text, "Title"),
        status=_extract_section(text, "Status"),
        mode=_extract_section(text, "Mode"),
        goal=_extract_section(text, "Goal"),
        created_timestamp=_extract_section(text, "Created Timestamp"),
    )


@dataclass(frozen=True)
class GitTag:
    """A single deterministically-observed git tag and its target commit."""

    tag_name: str
    commit_sha: str
    commit_author_date_utc: str | None


def list_git_tags(repo_root: Path) -> tuple[GitTag, ...]:
    """List all git tags with their target commit, sorted by tag name.

    Read-only, bounded to exactly the repository's own tag list --
    never an unbounded remote fetch. v1 produces zero
    ``release_lineage_record`` entries where no tags exist (127D
    Section 7), an honest limitation, not a fabrication.
    """
    output = _run_git(repo_root, ["tag"])
    if not output or not output.strip():
        return ()
    tags: list[GitTag] = []
    for name in sorted(line.strip() for line in output.splitlines() if line.strip()):
        info = _run_git(repo_root, ["log", "-1", f"--format={_LOG_FORMAT}", name])
        if not info or not info.strip():
            continue
        sha, _, date = info.strip().splitlines()[0].partition("\x1f")
        if not sha:
            continue
        tags.append(
            GitTag(tag_name=name, commit_sha=sha, commit_author_date_utc=date or None)
        )
    return tuple(tags)


_PHASE_TITLE_RE = re.compile(r"^Phase\s+(\S+)\b")


def phase_code_from_title(title: str | None) -> str | None:
    """Extract a phase code from a ``"Phase <ID> ..."``-shaped title.

    Deterministic, rule-based string matching only -- never inference.
    Independently confirmed (127D Section 2 grounding) that only a
    minority of this repository's task contracts follow this
    convention; titles that do not match yield ``None``, an honest
    unknown, not a guess.
    """
    if not title:
        return None
    match = _PHASE_TITLE_RE.match(title.strip())
    return match.group(1) if match else None
