# Task Contract

## Task ID

20260925-1813-phase-150i-pcae-lifecycle-phase-report-rehydration-identity-repair

## Title

Phase 150I - PCAE-LIFECYCLE-PHASE-REPORT-REHYDRATION-IDENTITY-REPAIR

## Status

active

## Mode

implementation

## Goal

Repair phase-report reconciliation so a completed finalization checkpoint
selects the terminal promoted generation by its certified Markdown digest and
semantic snapshot, while preserving historical generations and failing closed
on malformed, forged, missing, or ambiguous provenance.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/phase_reports.py
- src/pcae/commands/phase_reports.py
- tests/test_phase_150i_phase_report_rehydration_identity_repair.py
- tests/test_phase_150h_pcae_lifecycle_phase_150g_report_identity_reconciliation.py
- tests/test_phase_reports.py
- docs/PHASE_150I_PCAE_LIFECYCLE_PHASE_REPORT_REHYDRATION_IDENTITY_REPAIR.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/**
- .pcae/phase-reports/**
- .pcae/finalization-transactions/**
- .pcae/delivery-receipts/**
- .pcae/session.json
- .pcae/provenance/**

## Forbidden Files

- docs/contracts/**
- src/pcae/core/hpac_pawa_recognition_core.py
- src/pcae/core/hpac_protected_admin_writer.py
- src/pcae/core/hpac_pawa_helper_*.py
- src/pcae/core/hpac_foundation.py
- src/pcae/runtime/**
- src/pcae/permission_broker/**


## Allowed Zones

- core
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

strict

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No source behavior changes outside phase-report reconciliation/rehydration
- No execution authorization
- No rollback
- No Phase 150G artifact rewrite or deletion
- No recognition-core IV or helper-admission work
- DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED

## Acceptance Criteria

- Phase 150G's two promoted generations remain byte-for-byte preserved.
- The terminal 150G generation is selected from completed checkpoint identity,
  stored Markdown digest, and semantic snapshot, never filename/mtime order.
- Malformed, missing, forged, path-substituted, or ambiguous generation state
  fails closed.
- Historical generations remain inspectable and do not create a false conflict.
- Phase 150G reconcile is clean without marker/checkpoint/pointer mutation.
- Trust and consistency checks remain strict and passing.
- Fast Green records attributable_failures == [].
- Runtime remains Observed / observe / unavailable; N-16 state is unchanged.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- Fresh Phase 150I adversarial suite passes
- Relevant phase-report lifecycle regression suites pass
- pcae phase-report trust passes
- pcae phase-report consistency passes
- pcae phase-report reconcile --phase-id 150G passes
- Fresh Fast Green attributable_failures is empty

## Documentation Requirements

- Update PROJECT_STATUS.md, tasks/DECISIONS.md, tasks/DONE.md, CHANGELOG.md,
  completion metadata, canonical evidence, and canonical Phase Report.

## Created Timestamp

2026-09-25T18:13:36.130322+02:00
