# Task Contract

## Task ID

20260627-88x2-validation-runtime-budget-and-test-tier-rebalancing

## Title

88X.2 — Validation Runtime Budget and Test Tier Rebalancing

## Status

active

## Mode

implementation

## Goal

Reduce validation bottlenecks by profiling test runtime, rebalancing test tiers, reducing avoidable subprocess overhead, and documenting validation policy. Preserve all safety coverage. Do not delete, skip, xfail, or weaken tests.

Target budgets: fast-green ≤30s, quick tier ≤3min, full suite ≤25-30min.

## Allowed Files

- tests/conftest.py
- pyproject.toml
- Test files whose markers/fixtures/runtime behavior require adjustment
- docs/PHASE_88_VALIDATION_RUNTIME_BUDGET_AND_TEST_TIER_REBALANCING.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/DONE.md

## Forbidden Files

- Production source behavior files (unless tiny testability helper justified)
- Advisory feature expansion files
- Shell/system config files
- Phase 88Y task contract

## Acceptance Criteria

- Baseline runtimes captured and bottlenecks identified
- Tier policy documented
- Security-critical fast-green coverage preserved
- Fast-green under/near 30s, quick tier under/near 3min
- Full suite bottleneck documented
- No tests deleted, skipped, or xfailed; no assertions weakened
- All tiers green
- Documentation artifact exists

## Acceptance Checks

- python -m pytest -m "fast_green" -n auto -ra --durations=150
- python -m pytest -m "not slow and not phase_closure" -n auto -ra --durations=200
- python -m pytest -n auto -ra --durations=250 (full suite)
- pcae health, check, doctor task-memory, doctor test-run, push check

## Documentation Requirements

- Create docs/PHASE_88_VALIDATION_RUNTIME_BUDGET_AND_TEST_TIER_REBALANCING.md
- Update PROJECT_STATUS.md, CHANGELOG.md, tasks/DONE.md

## Created Timestamp

2026-06-27T06:00:00.000000+02:00
