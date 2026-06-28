# Task Contract

## Task ID

20260628-2019-90b-full-suite-baseline-inspection-and-scope-preflight-repair

## Title

90B — Full-Suite Baseline Inspection and Scope/Preflight Repair

## Status

done

## Mode

implementation

## Goal

Investigate and repair the 188 pre-existing full-suite scope/preflight idle-state failures. Determine root cause, repair test isolation issues or source defects, and establish a stable baseline. End with full suite green or fully classified known baseline.

## Allowed Files

- docs/PHASE_90_FULL_SUITE_BASELINE_INSPECTION_AND_SCOPE_PREFLIGHT_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tests/test_scope_preflight.py
- tests/test_preflight_integration_verification.py
- tests/conftest.py
- src/pcae/core/scope_preflight.py

## Forbidden Files

- .githooks/**
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md

## Allowed Zones

- docs
- tasks
- tests
- core

## Forbidden Zones

- commands
- cli
- hooks
- config
- session
- policy
- package
- scripts

## Enforcement Mode

advisory

## Forbidden Changes

- No real enforcement, blocking, shell interception, wrappers, shell config modification
- No command execution, backend invocation, prompt sending, output capture, intake/adoption
- No real authorization, persistent enforcement state, persistent cache
- No weakening tests, no xfail/skip just to pass, no deleting test coverage
- No raw git commit, raw git push, force push
- No phase beyond 90B started

## Acceptance Criteria

- 188 full-suite failures investigated and root cause identified
- Repairs made if root cause justified
- No test weakening
- No enforcement implemented
- Fast-green passes
- Quick tier passes
- Full suite run once and classified
- Documentation artifact exists

## Acceptance Checks

- pcae health
- pcae check
- python -m pytest -m "fast_green" -n auto -ra --durations=100
- python -m pytest -m "not slow and not phase_closure" -n auto -ra --durations=150
- pcae doctor task-memory
- pcae doctor test-run --json
- pcae push check
- git status --branch --short

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T20:19:57.341290+02:00
