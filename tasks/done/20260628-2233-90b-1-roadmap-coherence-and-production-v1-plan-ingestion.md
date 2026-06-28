# Task Contract

## Task ID

20260628-2233-90b-1-roadmap-coherence-and-production-v1-plan-ingestion

## Title

90B.1 — Roadmap Coherence and Production v1 Plan Ingestion

## Status

done

## Mode

implementation

## Goal

Inspect existing roadmap/planning artifacts, identify the canonical roadmap location, and update it with a coherent Production v1 roadmap plus future pluggability direction. Keep PCAE coherent as one product with one canonical roadmap.

## Allowed Files

- docs/ROADMAP.md
- README.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- docs/VISION.md

## Forbidden Files

- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- .githooks/**

## Allowed Zones

- docs
- tasks

## Forbidden Zones

- core
- commands
- cli
- tests
- hooks
- config
- session
- policy
- package
- scripts

## Enforcement Mode

advisory

## Forbidden Changes

- No Telegram implementation
- No notification code
- No shell interception
- No enforcement
- No backend invocation
- No raw git commit
- No raw git push
- No --no-verify
- No starting 90C

## Acceptance Criteria

- Canonical roadmap updated with Production v1 path
- Future v2/pluggability track defined
- Telegram scope clarified (outbound only, no remote shell)
- No competing roadmap files created
- README.md roadmap snapshot updated
- PROJECT_STATUS.md, CHANGELOG.md, TODO.md updated

## Acceptance Checks

- pcae health
- pcae check
- python -m pytest -m "fast_green" -n auto -ra --durations=100
- pcae doctor task-memory
- pcae push check
- git status --branch --short

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T22:33:39.676664+02:00
