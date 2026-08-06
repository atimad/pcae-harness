# Task Contract

## Task ID

20260806-1948-phase-149o-1h-3-hatp-sub-microsecond-timestamp-truncation-narrow-repair

## Title

Phase 149O.1H.3: HATP Sub-Microsecond Timestamp Truncation Narrow Repair

## Status

active

## Mode

implementation

## Goal

Repair the sub-microsecond fractional-second timestamp truncation defect (narrow reopened basis of B-149O.1H-1) in human_approval_trusted_provenance.py by validating raw lexical fractional-second precision before datetime.fromisoformat, without widening canonical precision, changing proof shape, or implementing Wave 4.

## Allowed Files

- src/pcae/core/human_approval_trusted_provenance.py
- tests/test_phase_149o_1h_2_hatp_proof_models_canonical_serialization_independent_reverification.py
- tests/test_phase_149o_1h_3_hatp_sub_microsecond_timestamp_truncation_repair.py
- docs/PHASE_149O_1H_3_HATP_SUB_MICROSECOND_TIMESTAMP_TRUNCATION_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-06T19:48:50.747862+02:00
