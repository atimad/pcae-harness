from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.paths import HarnessPath


COMMANDS_RELATIVE_PATH = Path("docs") / "COMMANDS.md"
ARCHITECTURE_RELATIVE_PATH = Path("docs") / "ARCHITECTURE.md"


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
    return write_docs_artifact(
        root,
        COMMANDS_RELATIVE_PATH,
        render_commands_reference(),
        force,
    )


def render_architecture_overview() -> str:
    return """# PCAE Architecture Overview

## Governance Runtime

PCAE centers governance around local repository state: policy, task contracts, session snapshots, architecture history, and generated reports.

```
policy.toml + task contract
        |
        v
    pcae check
        |
        v
health / CI / daemon / pipeline
```

Major command groups:

- `pcae check` validates task scope, policy, session continuity, and architecture rules.
- `pcae health` summarizes readiness for humans, CI, and agents.
- `pcae inspect` reports harness installation and policy status.

## Orchestration Layer

The orchestration layer combines existing checks and reports into repeatable workflows.

```
health -> check -> analytics -> exports -> session end
              |
              v
        pipeline result
```

Major command groups:

- `pcae pipeline` runs or previews predefined governance workflows.
- `pcae session` starts, updates, reads, and ends governed work sessions.
- `pcae docs` generates human-readable project references.

## Analytics Layer

Analytics read architecture history and current governance state to summarize trends and risk.

```
architecture-history.json
        |
        v
analytics trends / analytics risk / architecture metrics
```

Major command groups:

- `pcae analytics trends` summarizes governance evolution.
- `pcae analytics risk` computes current governance risk.
- `pcae architecture metrics` reports architecture drift metrics.

## Fleet Layer

Fleet commands coordinate governance state across locally registered repositories.

```
.pcae/fleet.json
       |
       v
fleet health / inspect / drift / apply / export
```

Major command groups:

- `pcae fleet add`, `list`, and `remove` maintain the registry.
- `pcae fleet health`, `inspect`, and `drift` aggregate readiness.
- `pcae fleet apply` previews or applies governance files across repos.

## Agent Coordination Layer

Agent leasing protects a governed repo from accidental concurrent agent work.

```
agent acquire
     |
     v
.pcae/agent-lock.json
     |
     v
agent status / release / force-stale
```

Major command groups:

- `pcae agent acquire` creates a local lease.
- `pcae agent status` reports freshness and holder.
- `pcae agent release` releases matching or stale leases.

## CI Integration Layer

CI integration generates and validates a GitHub Actions governance workflow.

```
pcae ci generate github
          |
          v
.github/workflows/pcae-governance.yml
          |
          v
ci status / drift / repair
```

Major command groups:

- `pcae ci generate github` writes the expected workflow.
- `pcae ci status` inspects workflow completeness.
- `pcae ci drift` and `pcae ci repair` detect and repair workflow drift.

## Daemon Monitoring Layer

Daemon commands preview future always-on governance monitoring without running a loop.

```
daemon status
      |
      v
daemon run --dry-run -> planned monitoring checks
daemon watch --dry-run -> future continuous plan
```

Major command groups:

- `pcae daemon run --dry-run` simulates one monitoring cycle.
- `pcae daemon status` reports daemon capability state.
- `pcae daemon watch --dry-run` previews future watch behavior.

## Operational Artifact Hygiene

Generated runtime artifacts are separated from durable project memory.

```
durable memory: tasks/ .pcae/policy.toml docs/
runtime state:  .pcae/session.json .pcae/architecture-history.json
local exports:  .pcae/exports/ .pcae/fleet-exports/
```

Responsibilities:

- Durable governance files are tracked and reviewed.
- Runtime/session artifacts are local operational state.
- Export bundles are portable handoff artifacts and ignored by default.
"""


def generate_architecture_overview(
    root: HarnessPath,
    force: bool = False,
) -> DocsGenerateResult:
    return write_docs_artifact(
        root,
        ARCHITECTURE_RELATIVE_PATH,
        render_architecture_overview(),
        force,
    )


def write_docs_artifact(
    root: HarnessPath,
    relative_path: Path,
    content: str,
    force: bool,
) -> DocsGenerateResult:
    target = root.join(relative_path)
    if target.exists() and not force:
        raise FileExistsError(
            f"{relative_path.as_posix()} already exists. Use --force to overwrite."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    existed = target.exists()
    with target.open("w", encoding="utf-8", newline="\n") as file:
        file.write(content)

    return DocsGenerateResult(
        relative_path=relative_path,
        created=not existed,
        overwritten=existed,
    )
