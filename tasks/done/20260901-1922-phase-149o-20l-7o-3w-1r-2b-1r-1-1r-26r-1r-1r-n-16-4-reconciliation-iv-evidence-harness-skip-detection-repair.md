# Task Contract

## Task ID

20260901-1922-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-26r-1r-1r-n-16-4-reconciliation-iv-evidence-harness-skip-detection-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1R: N-16-4 Reconciliation IV Evidence-Harness Skip-Detection Repair

## Status

done

## Mode

validation

## Goal

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1R: N-16-4 Reconciliation IV Evidence-Harness Skip-Detection Repair

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py
- tests/test_runtime_dispatch_1r26r1_harness_repair_3w1r2b1r1_1r26r1r.py
- tests/test_runtime_dispatch_1r26r1_harness_repair_independent_verification_3w1r2b1r1_1r26r1r1.py
- tests/test_runtime_dispatch_1r26r1_skip_detection_repair_3w1r2b1r1_1r26r1r1r.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1R_N_16_4_RECONCILIATION_IV_EVIDENCE_HARNESS_REPAIR.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_1R_1R_N_16_4_RECONCILIATION_IV_EVIDENCE_HARNESS_SKIP_DETECTION_REPAIR.md
- .pcae/**

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
- No raw git commit or raw git push; governed PCAE lifecycle only
- No rollback

## Acceptance Criteria

- Reconstruct and restore the predecessor executable skip/xfail invariant with AST-aware detection.
- Preserve self-reference immunity, wildcard/fnmatch detection, substantive guards, and historical records.
- Complete fixed-SHA attribution, broad guard verification, governed commit/push/finalization, and notification.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-01T19:22:37.128728+02:00
