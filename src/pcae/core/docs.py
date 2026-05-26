from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.paths import HarnessPath


COMMANDS_RELATIVE_PATH = Path("docs") / "COMMANDS.md"


@dataclass(frozen=True)
class DocsGenerateResult:
    relative_path: Path
    created: bool
    overwritten: bool


def render_commands_reference() -> str:
    return """# PCAE Command Reference

## health

- `pcae health`
- `pcae health --json`

## check

- `pcae check`
- `pcae check --json`

## inspect

- `pcae inspect`
- `pcae inspect --json`

## task

- `pcae task new "<title>"`
- `pcae task list`
- `pcae task show`
- `pcae task update`
- `pcae task pause`
- `pcae task resume`
- `pcae task complete`
- `pcae task close [task-id]`

## session

- `pcae session start`
- `pcae session read`
- `pcae session write`
- `pcae session update`
- `pcae session end`

## architecture

- `pcae architecture snapshot`
- `pcae architecture history`
- `pcae architecture metrics`
- `pcae architecture metrics --json`

## analytics

- `pcae analytics trends`
- `pcae analytics trends --json`
- `pcae analytics risk`
- `pcae analytics risk --json`

## export/import

- `pcae export bundle`
- `pcae import bundle <bundle.json> --dry-run`
- `pcae import bundle <bundle.json>`
- `pcae import bundle <bundle.json> --merge-history`

## repo

- `pcae repo trial <path> --dry-run`
- `pcae repo trial <path> --dry-run --json`
- `pcae repo apply <path> --dry-run`
- `pcae repo apply <path> --force`

## fleet

- `pcae fleet add <path>`
- `pcae fleet list`
- `pcae fleet remove <path>`
- `pcae fleet health`
- `pcae fleet health --json`
- `pcae fleet inspect`
- `pcae fleet inspect --json`
- `pcae fleet drift`
- `pcae fleet drift --json`
- `pcae fleet apply --dry-run`
- `pcae fleet apply --force`
- `pcae fleet export`

## pipeline

- `pcae pipeline list`
- `pcae pipeline list --json`
- `pcae pipeline run`
- `pcae pipeline run default`
- `pcae pipeline run --dry-run`
- `pcae pipeline run --json`

## daemon

- `pcae daemon run --dry-run`
- `pcae daemon run --dry-run --json`
- `pcae daemon status`
- `pcae daemon status --json`
- `pcae daemon watch --dry-run`
- `pcae daemon watch --dry-run --json`

## agent

- `pcae agent acquire --agent-id <id>`
- `pcae agent release --agent-id <id>`
- `pcae agent release --agent-id <id> --force-stale`
- `pcae agent status`
- `pcae agent status --json`

## ci

- `pcae ci generate github --dry-run`
- `pcae ci generate github`
- `pcae ci generate github --force`
- `pcae ci status`
- `pcae ci status --json`
- `pcae ci drift`
- `pcae ci drift --json`
- `pcae ci repair --dry-run`
- `pcae ci repair --force`
"""


def generate_commands_reference(
    root: HarnessPath,
    force: bool = False,
) -> DocsGenerateResult:
    target = root.join(COMMANDS_RELATIVE_PATH)
    if target.exists() and not force:
        raise FileExistsError(
            f"{COMMANDS_RELATIVE_PATH.as_posix()} already exists. Use --force to overwrite."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    existed = target.exists()
    with target.open("w", encoding="utf-8", newline="\n") as file:
        file.write(render_commands_reference())

    return DocsGenerateResult(
        relative_path=COMMANDS_RELATIVE_PATH,
        created=not existed,
        overwritten=existed,
    )
