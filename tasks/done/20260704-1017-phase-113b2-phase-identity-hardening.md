# Task Contract

## Task ID

20260704-1017-phase-113b2-phase-identity-hardening

## Title

Phase 113B.2: Phase Identity & Lifecycle Hardening

## Status

done

## Mode

implementation

## Goal

Harden PCAE phase identity validation so that future agents cannot silently drift into the wrong phase. Cross-validate phase identity across PROJECT_STATUS.md, active task, phase metadata, reports, and commit messages. Fail-closed on ambiguity.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/core/context.py
- tests/test_phase_identity.py
- docs/PHASE_113B2_PHASE_IDENTITY_HARDENING.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**

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

- Phase identity validation implemented
- Phase lifecycle consistency verified
- Canonical reports cannot describe the wrong phase
- Architecture Status consistency validated
- Bootstrap strengthened
- Execution remains unavailable

## Acceptance Checks

- python -m pytest tests/test_phase_identity.py -n auto -q
- python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py -n auto -q
- python -m pytest -m fast_green -n auto -q
- pcae health && pcae check && pcae doctor task-memory && pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-04T10:17:00.000000+00:00
