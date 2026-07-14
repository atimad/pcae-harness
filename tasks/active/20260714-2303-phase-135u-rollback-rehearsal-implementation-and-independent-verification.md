# Task Contract

## Task ID

20260714-2303-phase-135u-rollback-rehearsal-implementation-and-independent-verification

## Title

Phase 135U: Rollback Rehearsal Implementation and Independent Verification

## Status

active

## Mode

implementation

## Goal

Implement the rollback-rehearsal contract frozen in 135Q §33/§36-38 and verified in 135R, then independently attack that implementation within the same governed phase

## Allowed Files

- src/pcae/cltr/migration/rehearsal/enums.py
- src/pcae/cltr/migration/rehearsal/models.py
- src/pcae/cltr/migration/rehearsal/identity.py
- src/pcae/cltr/migration/rehearsal/persistence.py
- src/pcae/cltr/migration/rehearsal/pointer.py
- src/pcae/cltr/migration/rehearsal/rollback.py
- src/pcae/cltr/migration/rehearsal/status.py
- src/pcae/cltr/migration/rehearsal/reconciliation.py
- src/pcae/cltr/migration/rehearsal/__init__.py
- src/pcae/commands/cltr_migration.py
- src/pcae/cli.py
- tests/test_cltr_rehearsal_rollback.py
- tests/test_cltr_rehearsal_135u_independent_verification.py
- docs/PHASE_135_ROLLBACK_REHEARSAL_IMPLEMENTATION_AND_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Rollback rehearsal implemented per 135Q §33/§36-38 and independently verified within this phase

## Acceptance Checks

- pcae health passes
- pcae check passes
- python -m pytest -m fast_green -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-14T23:03:11.587533+02:00
