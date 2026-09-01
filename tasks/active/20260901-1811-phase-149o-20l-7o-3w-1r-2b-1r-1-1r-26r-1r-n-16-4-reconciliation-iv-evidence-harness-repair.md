# Task Contract

## Task ID

20260901-1811-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-26r-1r-n-16-4-reconciliation-iv-evidence-harness-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R: N-16-4 Reconciliation IV Evidence-Harness Repair

## Status

active

## Mode

validation

## Goal

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R: N-16-4 Reconciliation IV Evidence-Harness Repair

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1_INDEPENDENT_VERIFICATION_OF_THE_N_16_4_SCOPE_FENCE_RECONCILIATION.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1R_N_16_4_RECONCILIATION_IV_EVIDENCE_HARNESS_REPAIR.md
- tests/test_runtime_dispatch_1r26r_reconciliation_independent_verification_3w1r2b1r1_1r26r1.py
- tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py
- tests/test_runtime_dispatch_1r26r1_harness_repair_3w1r2b1r1_1r26r1r.py
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/**
- docs/contracts/**
- tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py
- tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py


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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No rollback

## Acceptance Criteria

- Repair exactly the two self-referential scanner defects using executable-structure-aware inspection.
- Preserve detection of real executable xfail and live wildcard/fnmatch broadening.
- Preserve `.1R.26R.1` as historically BLOCKED and keep all substantive reconciliation guards byte-identical.
- Complete fresh repair tests, broad attribution, governed commit/push/report/notification lifecycle.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-01T18:11:40.325569+02:00
