# Task Contract

## Task ID

20260719-1932-phase-137f-1-canonical-report-finalization-recovery-and-push-semantics-repair

## Title

Phase 137F.1 — Canonical Report Finalization Recovery and Push-Semantics Repair

## Status

active

## Reopen note

Closed via `pcae task complete` on 2026-07-19T19:32Z before its own
canonical phase report existed -- the same class of premature closure this
phase exists to prevent (see F5 in
docs/PHASE_137F1_CANONICAL_REPORT_FINALIZATION_RECOVERY_AND_PUSH_SEMANTICS_REPAIR.md).
Reopened rather than left closed without a matching report, so
`pcae push`'s own new phase-report-identity gate is not asked to accept a
completed phase with no report. Will be closed properly (via `pcae task
finish`) once Phase 137F.1V's independent verification or a future
governed phase resolves the transition-validator case-sensitivity defect
(F5) that currently prevents a clean `pcae phase complete` for this phase.

## Mode

recovery

## Goal

Investigate and repair the missing-canonical-report/push-semantics incident from Phase 137F finalization; recover the canonical 137F report through the governed lifecycle without altering the 137F verification verdict

## Allowed Files

- src/pcae/commands/push.py
- tests/test_push_phase_report_identity_137f1.py
- docs/PHASE_137F1_CANONICAL_REPORT_FINALIZATION_RECOVERY_AND_PUSH_SEMANTICS_REPAIR.md
- .pcae/phase-completion-metadata.json
- PROJECT_STATUS.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- CHANGELOG.md
- tasks/done/20260719-1905-idle-awaiting-next-governed-phase-post-137f.md
- tasks/done/20260719-1938-idle-awaiting-next-governed-phase-post-137f-1.md
- tasks/done/20260719-1932-phase-137f-1-canonical-report-finalization-recovery-and-push-semantics-repair.md
- tasks/active/20260719-1932-phase-137f-1-canonical-report-finalization-recovery-and-push-semantics-repair.md
- tasks/active/20260719-1938-idle-awaiting-next-governed-phase-post-137f-1.md
- tasks/active

## Forbidden Files

- src/pcae/cltr/authority/**
- src/pcae/schema_resources/**
- src/pcae/schema_runtime/**
- prototypes/typed_authority_inspector.py
- tests/test_typed_authority_inspector_137e.py


## Allowed Zones

- docs
- tasks
- config
- commands

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
