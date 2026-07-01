# Task Contract

## Task ID

20260701-0212-20260701-0030-phase-97f-execution-readiness-preflight

## Title

20260701-0030-phase-97f-execution-readiness-preflight

## Status

active

## Mode

implementation

## Goal

20260701-0030-phase-97f-execution-readiness-preflight

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/cli.py
- src/pcae/commands/agent.py
- src/pcae/core/backend_invocations.py
- docs/PHASE_97_EXECUTION_READINESS_PREFLIGHT_DRY_RUN.md
- tests/test_execution_readiness_preflight.py
- .pcae/phase-completion-metadata.json
- .pcae/execution-readiness-preflight/**
- .pcae/handoffs/**
- .pcae/session.json

## Forbidden Files

- .env
- .venv/**
- __pycache__/**


## Allowed Zones

- core
- cli
- commands
- tests
- docs
- tasks
- config

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No execution authorization
- No rollback

## Acceptance Criteria

- Phase 97F implementation complete
- 63 tests pass
- Governance checks pass
- Files committed and pushed

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest tests/test_execution_readiness_preflight.py -q passes

## Created Timestamp

2026-07-01T02:12:06.680006+02:00
