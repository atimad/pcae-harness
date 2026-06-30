# Task Contract

## Task ID

20260630-0836-phase-95g-runtime-evidence-broker-shell-gate-integration

## Title

Phase 95G — Runtime Evidence Broker/Shell-Gate Integration

## Status

done

## Mode

implementation

## Goal

Phase 95G — Runtime Evidence Broker/Shell-Gate Integration

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/commands/backend.py
- src/pcae/core/backend_invocations.py
- tests/test_backend_invocations.py
- .pcae/skills/phase-finalization
- docs/PHASE_95_RUNTIME_EVIDENCE_BROKER_SHELL_GATE_INTEGRATION.md

## Forbidden Files

- TBD

## Override Protected Files

- pyproject.toml


## Allowed Zones

- TBD

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
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-30T08:36:49.807377+02:00
