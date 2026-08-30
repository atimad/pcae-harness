# Task Contract

## Task ID

20260830-0901-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-15-2-gate-9-atomic-consumption-serialization-semantics-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2: Gate-9 Atomic-Consumption Serialization-Semantics Repair

## Status

active

## Mode

implementation

## Goal

Implement the narrow V-15-1 Gate-9 serialization-semantics repair frozen by .1R.15.1 (Option B): capture a monotonic authority-generation snapshot S1 after the full in-boundary revalidation battery; re-read tokens as S2 immediately before the create-only linearization with zero intervening effectful I/O; fail closed on any change; embed the snapshot durably in the existing authority_binding. Bundle V-15-2 (convert 3 HPAC-foundation zero-consumer guard suites to phase-aware subset invariants) and V-15-3 (replace 3 raw is_gate5_result assignments with monkeypatch.setattr). Keep the per-proof_id create-only primitive as the single linearization mechanism; no second global lock; no contract edit; no Gate 10; no execution; runtime unchanged.

## Allowed Files

- src/pcae/core/runtime_dispatch_gate9.py
- src/pcae/core/runtime_invocation_authority_consumption.py
- tests/test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2.py
- tests/test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14.py
- tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py
- tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py
- tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_15_2_GATE_9_ATOMIC_CONSUMPTION_SERIALIZATION_SEMANTICS_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/**

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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-30T09:01:02.975511+02:00
