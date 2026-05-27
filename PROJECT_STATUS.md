# Project Status

## Current Phase

Phase 34B: Governance repair planning preview.

## Governance Coherence Note

Governance documents are operational artifacts. Stale roadmap references in
PROJECT_STATUS.md, tasks/TODO.md, or CHANGELOG.md create orchestration risk:
agents read them as forward-looking guidance and attempt to implement work
that has already been done. Provenance history, runtime capabilities, and
roadmap guidance must remain coherent. When they drift, run
`pcae status coherence` to surface stale references.

## Current State

PCAE can preview and refresh adoption with init options, generate command,
architecture, and glossary documentation, generate, inspect, detect drift in,
preview repair for, and repair GitHub Actions governance CI workflows, inspect
repo readiness in human-readable or JSON form, report governance health and
agent lease state in human-readable or JSON form, run checks in human-readable
or JSON form with agent lease state exposed in JSON, report architecture
metrics in human-readable or JSON form, summarize governance trends and risk
in human-readable or JSON form, list available governance pipelines, run or
preview the default governance pipeline in human-readable or JSON form without
dirtying tracked operational state, preview one governance daemon monitoring
cycle, inspect daemon capability status, and preview future daemon watch
behavior with policy-driven intervals in human-readable or JSON form, acquire
and release a local agent session lease with policy-configured stale-lock
status reporting and explicit stale force release, export portable governance
bundles and fleet bundles as local ignored artifacts, preview and restore
approved governance bundle state safely with optional architecture history
merging, trial PCAE adoption against another Git repo in human-readable or
JSON form, apply PCAE onboarding to external Git repos with explicit force,
maintain a local fleet registry of governed repos, remove fleet repos safely,
inspect fleet readiness, detect fleet governance drift, orchestrate fleet-wide
governance apply in dry-run or force mode with optional JSON output, keep
managed pre-commit hooks pointed at `pcae check`, aggregate fleet health in
human-readable or JSON form, manage task lifecycle, validate task scope and
policy with CI-safe exit codes, enforce strict architecture dependency gates,
start or end governed engineering sessions with `pcae session start` and
`pcae session end`, record and read governance provenance attribution events,
automate governed phase lifecycle handoff with `pcae phase complete` and
`pcae phase start`, execute governed handoff automation with `pcae phase
handoff` including governance validation, agent lock transfer, and JSON output,
initialize a fresh governed session with `pcae session bootstrap` including
agent lock acquisition, health/check validation, active task display, current
provenance session, timeline summary, ready status, and JSON output, print
clear manual handoff steps and a copy-ready bootstrap prompt from `pcae phase
handoff` with clear guidance when `--next-agent` is omitted, display
multi-agent restart workflow examples (Claude CLI, Codex Desktop, Generic
governed agent) with a `restart_workflows` field in JSON output, check
PROJECT_STATUS.md for stale roadmap references with `pcae status coherence`
and `pcae status coherence --json`, and resume a governed session idempotently
with `pcae session bootstrap --agent-id <id>` when the same agent already
holds the lock, showing the full governance summary without duplicating
provenance events, and inspect the effective orchestration agent policy with
`pcae orchestration policy` and `pcae orchestration policy --json`, including
configurable `[orchestration]` section in `.pcae/policy.toml` with defaults
for `default_agent`, `documentation_agent`, `runtime_agent`, and
`validation_agent`, and list registered agents and their capabilities with
`pcae orchestration agents` and `pcae orchestration agents --json`, including
configurable `[agents.<id>]` sections in `.pcae/policy.toml` with `kind` and
`roles` fields, defaulting to `claude-local`, `codex-local`, and `pcae-native`
when no agent sections are configured, and recommend the best governed agent for
a work type with `pcae orchestration recommend --work-type TEXT` and
`pcae orchestration recommend --work-type TEXT --json`, matching the work type
against declared agent roles with deterministic fallback to `default_agent`,
and extended `pcae phase handoff` with `--work-type TEXT` to resolve the next
agent from orchestration policy when `--next-agent` is omitted, with
recommendation metadata in both human and JSON output, and generate
governance-aware workflow plans with `pcae orchestration plan --workflow TEXT`
and `pcae orchestration plan --workflow TEXT --json` for the built-in workflows
`documentation`, `implementation`, `validation`, and `release`, with
deterministic fallback for unknown workflows, and preview executable
orchestration workflow steps with `pcae orchestration simulate --workflow TEXT`
and `pcae orchestration simulate --workflow TEXT --json`, showing recommended
agents, work types, reasons, and governance checkpoints without executing work
or changing locks. Orchestration recommendations are advisory and
user-controlled: PCAE remains vendor-neutral and policy-guided, users may
override recommendations or prefer one agent for all work, and future agent
registries may include Claude, Codex, Kimi, DeepSeek, Perplexity, or other
models as capabilities evolve. Workflow coherence can be validated with
`pcae orchestration validate --workflow TEXT` and
`pcae orchestration validate --workflow TEXT --json`, which checks registry
membership, role coverage, deterministic ordering, fallback behavior, and
governance checkpoints without making recommendations mandatory. Phase handoff
guidance can include the same workflow validation with
`pcae phase handoff --workflow TEXT`, including JSON fields for workflow
validity, warnings, and governance checkpoints. Execution readiness can be
previewed with `pcae orchestration readiness --workflow TEXT` and
`pcae orchestration readiness --workflow TEXT --json`, combining workflow
validation, governance checkpoints, registry membership, health/check state,
and session continuity while remaining advisory and non-executing. Lightweight
governance coherence auditing is available with `pcae governance audit` and
`pcae governance audit --json`, checking phase and next-step status, stale
roadmap references, active task readability, session continuity availability,
provenance history presence, policy parsing, and agent registry presence
without mutating governance artifacts or rewriting roadmap files, and
deterministic advisory repair planning can be previewed with
`pcae governance repair --dry-run` and
`pcae governance repair --dry-run --json`, using audit results to report
detected issues, proposed repairs, safety notes, and the advisory reminder
that the user remains authoritative without modifying files.

## Next

- Update `pcae docs commands` to include the `phase`, `status`, and `orchestration` command groups.

## Future Explorations

- Automatic low-context detection triggering handoff.
- Compact-risk handoff: trigger `pcae phase handoff` when context compaction risk is high.
- Automatic governed bootstrap: `pcae session bootstrap` invoked on agent initialization.
- Automatic session restoration: replay provenance timeline on agent resume.
- Agent context monitoring: governance-aware context health reporting.
- Automatic AI session restart orchestration triggered by bootstrap.
- True interactive next-agent selection (e.g., from a configured agent roster).
- Auto-detect available agents from lock history or policy configuration.
- Orchestration-aware agent routing based on task type or governance context.
- Heterogeneous agent governance policies (per-agent policy overrides).
- Roadmap/provenance coherence validation: detect when completed features remain in the roadmap.
- Stale roadmap detection: automated scan of governance docs against CHANGELOG/DONE history.
- Governance artifact synchronization: keep PROJECT_STATUS.md, TODO.md, CHANGELOG.md coherent.
- Orchestration narrative validation: verify agent-facing guidance matches runtime capabilities.
- Governance drift detection for documentation artifacts beyond PROJECT_STATUS.md.
