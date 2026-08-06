# Task Contract

## Task ID

20260806-2153-phase-149o-1h-5-hatp-timestamp-canonicalization-lexical-guard-widening

## Title

Phase 149O.1H.5: HATP Timestamp Canonicalization Lexical Guard Widening

## Status

active

## Mode

implementation

## Goal

Repair B-149O.1H.4-1 by widening the fractional-second lexical precision guard to be suffix-independent (covers every timezone-offset syntax and decimal separator datetime.fromisoformat accepts), without changing proof shape, canonical format, digest semantics, or implementing Wave 4.

## Allowed Files

- src/pcae/core/human_approval_trusted_provenance.py
- tests/test_phase_149o_1h_4_hatp_timestamp_canonicalization_final_independent_reverification.py
- tests/test_phase_149o_1h_5_hatp_timestamp_lexical_guard_widening.py
- docs/PHASE_149O_1H_5_HATP_TIMESTAMP_CANONICALIZATION_LEXICAL_GUARD_WIDENING.md
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

2026-08-06T21:53:59.742815+02:00
