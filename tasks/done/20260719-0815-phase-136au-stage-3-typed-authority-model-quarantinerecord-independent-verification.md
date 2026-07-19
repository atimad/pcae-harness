# Task Contract

## Task ID

20260719-0815-phase-136au-stage-3-typed-authority-model-quarantinerecord-independent-verification

## Title

Phase 136AU: Stage 3 Typed Authority Model QuarantineRecord Independent Verification

## Status

done

## Mode

verification

## Goal

Independently verify the QuarantineRecord record-family model (Typed Model Implementation Group 11) by re-deriving its contract from the frozen contract and live executable schema, without trusting Phase 136AT's implementation, tests, or report.

## Allowed Files

- tests/test_cltr_authority_136au_quarantine_record_independent.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_QUARANTINE_RECORD_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-metadata-repairs.log
- .pcae/phase-reports/**

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

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- QuarantineRecord contract independently re-derived from the live schema and confirmed to match the Phase 136AT implementation exactly; no Blocking defect found
- CompatibilityState behavior independently reconfirmed unchanged
- No production implementation change made (no Blocking defect demonstrated)

## Acceptance Checks

- New dedicated 136AU independent verification module passes (fast + slow tiers)
- All test_cltr_authority_136*/test_cltr_cutover_136* modules pass with no new failures beyond the known inherited baseline
- Fast Green passes unchanged (4391 passed)
- Fresh wheel/sdist build and isolated install verification passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-19T08:15:56.540933+02:00
