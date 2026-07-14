# Task Contract

## Task ID

20260714-2134-phase-135t-atomic-publication-rehearsal-independent-verification

## Title

Phase 135T: Atomic Publication Rehearsal Independent Verification

## Status

active

## Mode

implementation

## Goal

Independently verify Stage 2 (135S), reproduce and attack all claims, repair any Blocking defects found within the Stage 2 boundary

## Allowed Files

- src/pcae/cltr/migration/rehearsal/coordinator.py
- tests/test_cltr_migration_135p_verification.py
- tests/test_cltr_rehearsal_135t_independent_verification.py
- docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_INDEPENDENT_VERIFICATION.md
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

- Independent verification complete with evidence-based verdict

## Acceptance Checks

- pcae health passes
- pcae check passes
- python -m pytest -m fast_green -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-14T21:34:20.436467+02:00
