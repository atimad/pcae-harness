# Task Contract

## Task ID

20260704-1308-phase-113x-1-finalization-gate-enforcement-repair

## Title

Phase 113X.1: Finalization Gate Enforcement Repair

## Status

done

## Mode

implementation

## Goal

Repair Finding 1 from the 113X forensic review: validate_finalization_gate() detects phase-identity/trust blockers but finalize_phase_report() writes canonical latest.md/latest.json unconditionally. Make blocked reports quarantine instead of overwriting canonical artifacts, persist blocker evidence, and keep push check/report trust from treating quarantined artifacts as latest.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- tests/test_phase_reports.py
- tests/test_phase_reports_cli.py
- tests/test_finalization_gate_enforcement.py
- docs/PHASE_113X1_FINALIZATION_GATE_ENFORCEMENT_REPAIR.md
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

- Blocked finalization (gate blockers present) never writes latest.md/latest.json
- Blocker details persisted in whatever artifact is written when blocked
- Valid (unblocked) finalization behavior is unchanged
- pcae phase complete exits non-zero on finalization blockers
- pcae push check / report trust does not treat a quarantined artifact as latest/trusted
- Execution capability remains unavailable; no Advisory Runtime, execution, authorization, or plugin changes

## Acceptance Checks

- python -m pytest tests/test_finalization_gate_enforcement.py -n auto -q
- python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py -n auto -q
- python -m pytest -m fast_green -n auto -q
- pcae health
- pcae check
- pcae doctor task-memory

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-04T13:08:16.678341+02:00
