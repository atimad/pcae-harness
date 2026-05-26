# PCAE Architecture Overview

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
