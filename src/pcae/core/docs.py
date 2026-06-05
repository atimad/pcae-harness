from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.paths import HarnessPath


COMMANDS_RELATIVE_PATH = Path("docs") / "COMMANDS.md"
ARCHITECTURE_RELATIVE_PATH = Path("docs") / "ARCHITECTURE.md"
GLOSSARY_RELATIVE_PATH = Path("docs") / "GLOSSARY.md"


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
- `pcae session bootstrap --agent-id <id>`
- `pcae session bootstrap --agent-id <id> --json`

## phase

- `pcae phase start --agent-id <id>`
- `pcae phase complete --summary "<text>"`
- `pcae phase handoff --summary "<text>" --next-agent <id>`
- `pcae phase handoff --summary "<text>" --work-type <type>`
- `pcae phase handoff --summary "<text>" --workflow <name>`
- `pcae phase handoff --json`

## status

- `pcae status coherence`
- `pcae status coherence --json`

## governance

- `pcae governance audit`
- `pcae governance audit --json`
- `pcae governance repair --dry-run`
- `pcae governance repair --dry-run --json`

## runtime

- `pcae runtime snapshot --preview`
- `pcae runtime snapshot --preview --json`
- `pcae runtime snapshot export`
- `pcae runtime snapshot export --json`
- `pcae runtime snapshot inspect <path>`
- `pcae runtime snapshot inspect <path> --json`
- `pcae runtime snapshot restore <path> --dry-run`
- `pcae runtime snapshot restore <path> --dry-run --json`
- `pcae runtime snapshot compatibility <path>`
- `pcae runtime snapshot compatibility <path> --json`
- `pcae runtime snapshot manifest`
- `pcae runtime snapshot manifest --json`
- `pcae runtime snapshot retention --dry-run`
- `pcae runtime snapshot retention --dry-run --json`
- `pcae runtime snapshot lineage`
- `pcae runtime snapshot lineage --json`
- `pcae runtime snapshot validate-restore <path>`
- `pcae runtime snapshot validate-restore <path> --json`

## orchestration

- `pcae orchestration policy`
- `pcae orchestration policy --json`
- `pcae orchestration agents`
- `pcae orchestration agents --json`
- `pcae orchestration recommend --work-type <type>`
- `pcae orchestration recommend --work-type <type> --json`
- `pcae orchestration plan --workflow <name>`
- `pcae orchestration plan --workflow <name> --json`
- `pcae orchestration simulate --workflow <name>`
- `pcae orchestration simulate --workflow <name> --json`
- `pcae orchestration validate --workflow <name>`
- `pcae orchestration validate --workflow <name> --json`
- `pcae orchestration readiness --workflow <name>`
- `pcae orchestration readiness --workflow <name> --json`

## context

- `pcae context pack --preview`
- `pcae context pack --preview --json`

## provenance

- `pcae provenance status`
- `pcae provenance history`
- `pcae provenance history --json`
- `pcae provenance history --event-type <type>`
- `pcae provenance history --agent-id <id>`
- `pcae provenance timeline`
- `pcae provenance timeline --json`
- `pcae provenance sessions`
- `pcae provenance sessions --json`
- `pcae provenance session current`
- `pcae provenance session current --json`
- `pcae provenance record --event-type <type> --summary "<text>"`
- `pcae provenance export`
- `pcae provenance export --json`

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

## docs

- `pcae docs commands --dry-run`
- `pcae docs commands --force`
- `pcae docs architecture --dry-run`
- `pcae docs architecture --force`
- `pcae docs glossary --dry-run`
- `pcae docs glossary --force`

## planning-execution-design

- `pcae planning-execution-design`
- `pcae planning-execution-design --json`

## execution-framework-design

- `pcae execution-framework-design`
- `pcae execution-framework-design --json`

## adapter-design

- `pcae adapter-design`
- `pcae adapter-design --json`

## invocation-design

- `pcae invocation-design`
- `pcae invocation-design --json`

## real-planning-design

- `pcae real-planning-design`
- `pcae real-planning-design --json`

## consensus-execution-design

- `pcae consensus-execution-design`
- `pcae consensus-execution-design --json`

## runtime-execution-prototype

- `pcae runtime-execution-prototype`
- `pcae runtime-execution-prototype --json`

## planner-adapter-prototype

- `pcae planner-adapter-prototype`
- `pcae planner-adapter-prototype --json`

## multi-agent-prototype

- `pcae multi-agent-prototype`
- `pcae multi-agent-prototype --json`

## consensus-prototype

- `pcae consensus-prototype`
- `pcae consensus-prototype --json`

## invocation-pilot

- `pcae invocation-pilot`
- `pcae invocation-pilot --json`

## multi-runtime-pilot

- `pcae multi-runtime-pilot`
- `pcae multi-runtime-pilot --json`

## consensus-runtime-pilot

- `pcae consensus-runtime-pilot`
- `pcae consensus-runtime-pilot --json`

## governed-execution-dry-run

- `pcae governed-execution-dry-run`
- `pcae governed-execution-dry-run --json`

## invocation-contracts

- `pcae invocation-contracts`
- `pcae invocation-contracts --json`

## execution-readiness

- `pcae execution-readiness`
- `pcae execution-readiness --json`

## adapter-registry-design

- `pcae adapter-registry-design`
- `pcae adapter-registry-design --json`

## roadmap-generation-design

- `pcae roadmap-generation-design`
- `pcae roadmap-generation-design --json`

## roadmap-evidence

- `pcae roadmap-evidence`
- `pcae roadmap-evidence --json`

## roadmap-proposal-dry-run

- `pcae roadmap-proposal-dry-run`
- `pcae roadmap-proposal-dry-run --json`

## multi-agent-roadmap

- `pcae multi-agent-roadmap`
- `pcae multi-agent-roadmap --json`

## roadmap-approval-design

- `pcae roadmap-approval-design`
- `pcae roadmap-approval-design --json`

## prompt-generation-design

- `pcae prompt-generation-design`
- `pcae prompt-generation-design --json`

## adaptive-prompt-design

- `pcae adaptive-prompt-design`
- `pcae adaptive-prompt-design --json`

## prompt-validation-design

- `pcae prompt-validation-design`
- `pcae prompt-validation-design --json`

## prompt-governance-design

- `pcae prompt-governance-design`
- `pcae prompt-governance-design --json`

## prompt-artifact-design

- `pcae prompt-artifact-design`
- `pcae prompt-artifact-design --json`

## prompt-approval-design

- `pcae prompt-approval-design`
- `pcae prompt-approval-design --json`

## autonomous-phase-proposal

- `pcae autonomous-phase-proposal`
- `pcae autonomous-phase-proposal --json`

## autonomous-prompt-proposal

- `pcae autonomous-prompt-proposal`
- `pcae autonomous-prompt-proposal --json`

## prompt-render

- `pcae prompt-render`
- `pcae prompt-render --json`

## prompt-execution-readiness

- `pcae prompt-execution-readiness`
- `pcae prompt-execution-readiness --json`

## prompt-execution-dry-run

- `pcae prompt-execution-dry-run`
- `pcae prompt-execution-dry-run --json`

## human-agent-execution-design

- `pcae human-agent-execution-design`
- `pcae human-agent-execution-design --json`

## governed-execution-pilot

- `pcae governed-execution-pilot`
- `pcae governed-execution-pilot --json`

## live-execution-readiness

- `pcae live-execution-readiness`
- `pcae live-execution-readiness --json`

## execution-audit-design

- `pcae execution-audit-design`
- `pcae execution-audit-design --json`

## execution-consensus-design

- `pcae execution-consensus-design`
- `pcae execution-consensus-design --json`

## live-execution-pilot

- `pcae live-execution-pilot`
- `pcae live-execution-pilot --json`

## invocation-workload-validation

- `pcae invocation-workload-validation`
- `pcae invocation-workload-validation --json`

## execution-authorization-design

- `pcae execution-authorization-design`
- `pcae execution-authorization-design --json`

## read-only-invocation-pilot

- `pcae read-only-invocation-pilot`
- `pcae read-only-invocation-pilot --json`

## execution-result-review-design

- `pcae execution-result-review-design`
- `pcae execution-result-review-design --json`

## authorization-expiration-design

- `pcae authorization-expiration-design`
- `pcae authorization-expiration-design --json`

## invocation-pilot-status

- `pcae invocation-pilot-status`
- `pcae invocation-pilot-status --json`

## multi-agent-invocation-pilot

- `pcae multi-agent-invocation-pilot`
- `pcae multi-agent-invocation-pilot --json`

## execution-quality-design

- `pcae execution-quality-design`
- `pcae execution-quality-design --json`

## read-only-invocation-execution-pilot

- `pcae read-only-invocation-execution-pilot`
- `pcae read-only-invocation-execution-pilot --json`

## write-invocation-design

- `pcae write-invocation-design`
- `pcae write-invocation-design --json`

## write-preflight-dry-run

- `pcae write-preflight-dry-run`
- `pcae write-preflight-dry-run --json`

## write-candidate-design

- `pcae write-candidate-design`
- `pcae write-candidate-design --json`

## write-invocation-pilot

- `pcae write-invocation-pilot`
- `pcae write-invocation-pilot --json`

## multi-agent-readonly-pilot

- `pcae multi-agent-readonly-pilot`
- `pcae multi-agent-readonly-pilot --json`

## consensus-engine

- `pcae consensus-engine`
- `pcae consensus-engine --json`

## arbitration

- `pcae arbitration`
- `pcae arbitration --json`

## evidence-framework

- `pcae evidence-framework`
- `pcae evidence-framework --json`

## decision-record

- `pcae decision-record`
- `pcae decision-record --json`

## write-result-review-design

- `pcae write-result-review-design`
- `pcae write-result-review-design --json`

## write-rollback-validation-design

- `pcae write-rollback-validation-design`
- `pcae write-rollback-validation-design --json`

## write-execution-readiness

- `pcae write-execution-readiness`
- `pcae write-execution-readiness --json`

## write-rollback-dry-run

- `pcae write-rollback-dry-run`
- `pcae write-rollback-dry-run --json`

## live-readonly-readiness

- `pcae live-readonly-readiness`
- `pcae live-readonly-readiness --json`

## live-write-readiness

- `pcae live-write-readiness`
- `pcae live-write-readiness --json`

## live-readonly-pilot

- `pcae live-readonly-pilot`
- `pcae live-readonly-pilot --json`

## rollback-execution-pilot

- `pcae rollback-execution-pilot`
- `pcae rollback-execution-pilot --json`

## live-write-pilot

- `pcae live-write-pilot`
- `pcae live-write-pilot --json`

## runtime-contracts

- `pcae runtime-contracts`
- `pcae runtime-contracts --json`

## governance-audit

- `pcae governance-audit`
- `pcae governance-audit --json`

## runtime-trust

- `pcae runtime-trust`
- `pcae runtime-trust --json`

## governance-maturity

- `pcae governance-maturity`
- `pcae governance-maturity --json`

## readonly-invocation

- `pcae readonly-invocation`
- `pcae readonly-invocation --json`

## invocation-result-capture

- `pcae invocation-result-capture`
- `pcae invocation-result-capture --json`

## runtime-contract-enforcement

- `pcae runtime-contract-enforcement`
- `pcae runtime-contract-enforcement --json`

## invocation-authorization-enforcement

- `pcae invocation-authorization-enforcement`
- `pcae invocation-authorization-enforcement --json`

## invocation-audit

- `pcae invocation-audit`
- `pcae invocation-audit --json`

## readonly-runtime-pilot

- `pcae readonly-runtime-pilot`
- `pcae readonly-runtime-pilot --json`

## invocation-result-review

- `pcae invocation-result-review`
- `pcae invocation-result-review --json`

## invocation-evidence

- `pcae invocation-evidence`
- `pcae invocation-evidence --json`

## multi-agent-governance-audit

- `pcae multi-agent-governance-audit`
- `pcae multi-agent-governance-audit --json`

## governance-state-audit

- `pcae governance-state-audit`
- `pcae governance-state-audit --json`

## governance-state-repair

- `pcae governance-state-repair`
- `pcae governance-state-repair --json`

## task-transition-governance

- `pcae task-transition-governance`
- `pcae task-transition-governance --json`

## session-continuity-governance

- `pcae session-continuity-governance`
- `pcae session-continuity-governance --json`

## governance-invariants

- `pcae governance-invariants`
- `pcae governance-invariants --json`

## runtime-safety-invariants

- `pcae runtime-safety-invariants`
- `pcae runtime-safety-invariants --json`

## governance-drift

- `pcae governance-drift`
- `pcae governance-drift --json`

## governance-drift-review

- `pcae governance-drift-review`
- `pcae governance-drift-review --json`

## agent-lock-governance

- `pcae agent-lock-governance`
- `pcae agent-lock-governance --json`

## agent-lock-conflicts

- `pcae agent-lock-conflicts`
- `pcae agent-lock-conflicts --json`
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


def render_glossary() -> str:
    return """# PCAE Governance Glossary

## active task

The single task contract currently governing a work session. `pcae check` enforces
scope restrictions drawn from the active task. Only one task may be active at a time.

## agent lock

A local lease file (`.pcae/agent-lock.json`) that records which agent is performing
governed work. Prevents accidental concurrent agent sessions in the same repository.
Acquired with `pcae agent acquire` and released with `pcae agent release`.

## allowed files

A set of file paths declared in the active task contract that the agent is permitted
to read or modify. `pcae check` reports a violation if a file outside this set is
touched during the session.

## allowed zones

Named directory prefixes declared in the active task contract. Files under an allowed
zone are implicitly permitted. Zones provide coarser-grained scope control than
individual allowed files.

## architecture history

A local append-only log (`.pcae/architecture-history.json`) of architecture check
snapshots. Each entry records zone counts, rule violations, enforcement mode, and
timestamp. Read by `pcae analytics` and `pcae architecture metrics`.

## architecture rules

Constraints declared in `policy.toml` that govern module boundaries, import
directions, or file placement within architecture zones. Violations are recorded in
architecture history and surfaced by `pcae check`.

## architecture zones

Named directory regions defined in `policy.toml` that partition the repository into
logical modules (e.g. `src/`, `tests/`, `docs/`). Rules are expressed in terms of
zones. `pcae architecture snapshot` classifies files into zones at check time.

## CI drift

A divergence between the generated `.github/workflows/pcae-governance.yml` and the
canonical workflow content expected by the current harness version. Detected by
`pcae ci drift` and repaired by `pcae ci repair`.

## CI repair

The act of regenerating the GitHub Actions governance workflow to eliminate CI drift.
`pcae ci repair --dry-run` previews the repair; `pcae ci repair --force` writes it.

## daemon dry-run

A simulated single monitoring cycle executed by `pcae daemon run --dry-run`. Reports
which governance checks would run without starting a persistent process or writing
files.

## enforcement mode

A policy setting (`advisory` or `strict`) that controls how `pcae check` treats
violations. In `advisory` mode violations are reported but do not cause a non-zero
exit. In `strict` mode any violation causes the check to fail.

## fleet drift

A divergence in governance state detected across one or more repositories in the fleet
registry. `pcae fleet drift` aggregates per-repo drift signals and reports which repos
require attention.

## fleet registry

The local list of governed repository paths stored in `.pcae/fleet.json`. Managed
with `pcae fleet add`, `pcae fleet list`, and `pcae fleet remove`. Used by all
`pcae fleet` subcommands.

## forbidden files

File paths explicitly excluded by the active task contract. Touching a forbidden file
during a session is a scope violation regardless of allowed-zone declarations.

## forbidden zones

Named directory prefixes explicitly excluded by the active task contract. Files under
a forbidden zone are out of scope even if they would otherwise be permitted by an
allowed-zone declaration.

## governance bundle

A portable JSON export of current governance state produced by `pcae export bundle`.
Contains policy, task contracts, session snapshot, and architecture history. Can be
imported into another repository with `pcae import bundle`.

## governance health

A summary of whether a repository meets all PCAE readiness criteria. Reported by
`pcae health` (human-readable) or `pcae health --json` (machine-readable). Aggregates
policy validity, active task presence, session continuity, and agent lock state.

## governance risk

A computed score summarizing the likelihood of governance degradation based on
architecture history trends. Reported by `pcae analytics risk`. Higher scores indicate
accumulating drift, stale tasks, or repeated enforcement violations.

## governance runtime

The set of local files and processes that enforce PCAE governance: `policy.toml`,
task contracts, session snapshots, architecture history, and the `pcae check` and
`pcae health` commands. The runtime operates entirely within the repository without
external services.

## pipeline dry-run

A preview of a named governance workflow produced by `pcae pipeline run --dry-run`.
Reports which checks and exports would execute without writing operational artifacts
or advancing session state.

## session continuity

A property verified by `pcae check` confirming that a valid session snapshot exists
and that the current agent context matches the recorded session. Broken continuity
indicates a session was not properly started or was interrupted without being finalized.

## task contract

A structured TOML file in `tasks/active/` that defines the scope, goal, allowed
files, forbidden files, allowed zones, forbidden zones, and enforcement mode for a
unit of governed work. Created with `pcae task new` and consumed by `pcae check`.
"""


def generate_glossary(
    root: HarnessPath,
    force: bool = False,
) -> DocsGenerateResult:
    return write_docs_artifact(
        root,
        GLOSSARY_RELATIVE_PATH,
        render_glossary(),
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
