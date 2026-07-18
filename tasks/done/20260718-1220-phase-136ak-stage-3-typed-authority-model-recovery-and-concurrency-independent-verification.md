# Task Contract

## Task ID

20260718-1220-phase-136ak-stage-3-typed-authority-model-recovery-and-concurrency-independent-verification

## Title

Phase 136AK: Stage 3 Typed Authority Model Recovery and Concurrency Independent Verification

## Status

done

## Mode

implementation

## Goal

Independently re-derive and verify ConcurrencyConflict and RecoveryJournalEntry typed record models from Phase 136AJ against frozen contracts and live executable schemas; bounded repair of independently reproduced Blocking defects only.

## Allowed Files

- tests/test_cltr_authority_136ak_recovery_concurrency_independent.py
- src/pcae/cltr/authority/recovery_concurrency.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_RECOVERY_CONCURRENCY_INDEPENDENT_VERIFICATION.md
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

- src/pcae/cltr/authority/bindings.py
- src/pcae/cltr/authority/compatibility_quarantine.py


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

- Both ConcurrencyConflict and RecoveryJournalEntry record contracts independently re-derived from frozen contracts and live schemas, not from 136AJ tests/fixtures/prose
- No later record-family model introduced; no conflict detection, CAS execution, locking, retry, recovery planning/execution, replay, rollback, or journal persistence introduced
- No unresolved Blocking finding remains

## Acceptance Checks

- New independent test module passes
- 136AJ/136AI/136AH/136AG/136AF/136AE/136AD/136AC/136AB/136AA/136Z focused suites pass with no new failures
- Fresh wheel/sdist build and isolated install verification passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-18T12:22:00.141933+02:00
