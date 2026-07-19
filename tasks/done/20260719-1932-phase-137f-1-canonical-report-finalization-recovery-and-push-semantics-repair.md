# Task Contract

## Task ID

20260719-1932-phase-137f-1-canonical-report-finalization-recovery-and-push-semantics-repair

## Title

Phase 137F.1 — Canonical Report Finalization Recovery and Push-Semantics Repair

## Status

done

## Mode

recovery

## Goal

Investigate and repair the missing-canonical-report/push-semantics incident from Phase 137F finalization; recover the canonical 137F report through the governed lifecycle without altering the 137F verification verdict

## Allowed Files

- src/pcae/commands/push.py
- src/pcae/cli.py
- tests/test_push_phase_report_identity_137f1.py
- docs/PHASE_137F1_CANONICAL_REPORT_FINALIZATION_RECOVERY_AND_PUSH_SEMANTICS_REPAIR.md
- .pcae/phase-completion-metadata.json
- PROJECT_STATUS.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- CHANGELOG.md
- tasks/done/20260719-1905-idle-awaiting-next-governed-phase-post-137f.md
- tasks/active/20260719-1932-phase-137f-1-canonical-report-finalization-recovery-and-push-semantics-repair.md
- tasks/active

## Forbidden Files

- src/pcae/cltr/authority/**
- src/pcae/schema_resources/**
- src/pcae/schema_runtime/**
- prototypes/typed_authority_inspector.py
- tests/test_typed_authority_inspector_137e.py


## Allowed Zones

- commands
- cli
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

- TBD

## Acceptance Criteria

- Root cause independently demonstrated and reproduced
- Canonical 137F report recovered through governed lifecycle, distinguishing original vs recovery outcome
- pcae push and pcae push check can no longer reasonably be confused
- Regression tests cover the demonstrated failure paths
- Fast Green remains green; runtime remains Observed / observe / unavailable

## Acceptance Checks

- pcae check passes
- pytest -m fast_green passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-19T19:32:02.020795+02:00
