# Task Contract

## Task ID

20260703-2240-phase-112b-1-planning-bootstrap-consistency-hardening

## Title

Phase 112B.1: Planning & Bootstrap Consistency Hardening

## Status

done

## Mode

implementation

## Goal

Repair stale tasks/TODO.md 90-series roadmap presentation, define source-of-truth precedence, harden pcae session bootstrap orientation output, and add regression coverage -- governance/planning/bootstrap hygiene only, no Runtime Context implementation.

## Allowed Files

- tasks/TODO.md
- docs/PHASE_112_PLANNING_BOOTSTRAP_CONSISTENCY_HARDENING.md
- src/pcae/core/context.py
- tests/test_bootstrap_todo_consistency.py
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

- tasks/TODO.md no longer presents the 90-series roadmap as current
- Bootstrap surfaces authoritative vs stale planning source explicitly
- 112C remains the recommended next phase

## Acceptance Checks

- python -m pytest tests/test_bootstrap_todo_consistency.py tests/test_context.py tests/test_session.py -q
- python -m pytest -m fast_green -n auto -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-03T22:40:59.834364+02:00
