# Project Status

## Current Phase

Phase 27D: Configurable agent stale threshold.

## Current State

PCAE can preview and refresh adoption with init options, inspect repo readiness in human-readable or JSON form, report governance health in human-readable or JSON form, run checks in human-readable or JSON form, report architecture metrics in human-readable or JSON form, summarize governance trends and risk in human-readable or JSON form, list available governance pipelines, run or preview the default governance pipeline in human-readable or JSON form without dirtying tracked operational state, acquire and release a local agent session lease with policy-configured stale-lock status reporting and explicit stale force release, export portable governance bundles and fleet bundles as local ignored artifacts, preview and restore approved governance bundle state safely with optional architecture history merging, trial PCAE adoption against another Git repo in human-readable or JSON form, apply PCAE onboarding to external Git repos with explicit force, maintain a local fleet registry of governed repos, remove fleet repos safely, inspect fleet readiness, detect fleet governance drift, orchestrate fleet-wide governance apply in dry-run or force mode with optional JSON output, keep managed pre-commit hooks pointed at `pcae check`, aggregate fleet health in human-readable or JSON form, manage task lifecycle, validate task scope and policy with CI-safe exit codes, enforce strict architecture dependency gates, and start or end governed engineering sessions.

## Next

- Implement `pcae end`.
