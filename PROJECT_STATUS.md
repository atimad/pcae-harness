# Project Status

## Current Phase

Phase 32F: Multi-agent governed bootstrap guidance.

## Current State

PCAE can preview and refresh adoption with init options, generate command, architecture, and glossary documentation, generate, inspect, detect drift in, preview repair for, and repair GitHub Actions governance CI workflows, inspect repo readiness in human-readable or JSON form, report governance health and agent lease state in human-readable or JSON form, run checks in human-readable or JSON form with agent lease state exposed in JSON, report architecture metrics in human-readable or JSON form, summarize governance trends and risk in human-readable or JSON form, list available governance pipelines, run or preview the default governance pipeline in human-readable or JSON form without dirtying tracked operational state, preview one governance daemon monitoring cycle, inspect daemon capability status, and preview future daemon watch behavior with policy-driven intervals in human-readable or JSON form, acquire and release a local agent session lease with policy-configured stale-lock status reporting and explicit stale force release, export portable governance bundles and fleet bundles as local ignored artifacts, preview and restore approved governance bundle state safely with optional architecture history merging, trial PCAE adoption against another Git repo in human-readable or JSON form, apply PCAE onboarding to external Git repos with explicit force, maintain a local fleet registry of governed repos, remove fleet repos safely, inspect fleet readiness, detect fleet governance drift, orchestrate fleet-wide governance apply in dry-run or force mode with optional JSON output, keep managed pre-commit hooks pointed at `pcae check`, aggregate fleet health in human-readable or JSON form, manage task lifecycle, validate task scope and policy with CI-safe exit codes, enforce strict architecture dependency gates, start or end governed engineering sessions, record and read governance provenance attribution events, and automate governed phase lifecycle handoff with `pcae phase complete` and `pcae phase start`, and execute governed handoff automation with `pcae phase handoff` including governance validation, agent lock transfer, and JSON output, and initialize a fresh governed session with `pcae session bootstrap` including agent lock acquisition, health/check validation, active task display, current provenance session, timeline summary, ready status, and JSON output, and print clear manual handoff steps and a copy-ready bootstrap prompt from `pcae phase handoff` with clear guidance when `--next-agent` is omitted, and display multi-agent restart workflow examples (Claude CLI, Codex Desktop, Generic governed agent) with a `restart_workflows` field in JSON output.

## Next

- Implement `pcae end`.

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
