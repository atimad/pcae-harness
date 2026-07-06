# Task Contract

## Task ID

20260706-0459-fix-bootstrap-check-passed-idle-state-string-comparison-bug

## Title

Fix bootstrap check_passed idle-state string comparison bug

## Status

active

## Mode

implementation

## Goal

Correct run_session_bootstrap in commands/session.py to use is_healthy() helper instead of comparing the health display string to the literal 'healthy', which always failed when the repo was idle

## Allowed Files

- src/pcae/commands/session.py
- tests/test_session.py
- docs/PHASE_94Q1_BOOTSTRAP_RESUME_TELEGRAM_RUNTIME_HARDENING.md
- tasks/active/20260706-0459-fix-bootstrap-check-passed-idle-state-string-comparison-bug.md

## Forbidden Files

- TBD


## Allowed Zones

- commands
- docs
- tests
- tasks

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

- pcae session bootstrap reports Check: passed when pcae check independently passes and repo is idle

## Acceptance Checks

- python -m pytest tests/test_session.py -k bootstrap -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T04:59:05.637096+02:00
