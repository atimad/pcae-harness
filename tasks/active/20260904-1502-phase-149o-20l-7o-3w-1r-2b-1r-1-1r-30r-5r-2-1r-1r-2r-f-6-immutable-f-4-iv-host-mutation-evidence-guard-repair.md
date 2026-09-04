# Task Contract

## Task ID

20260904-1502-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2r-f-6-immutable-f-4-iv-host-mutation-evidence-guard-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R: F-6 Immutable F-4-IV Host-Mutation Evidence Guard Repair

## Status

active

## Mode

repair

## Goal

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R: F-6 Immutable F-4-IV Host-Mutation Evidence Guard Repair

## Allowed Files

- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_f6_immutable_host_mutation_guard_repair.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_F6_IMMUTABLE_HOST_MUTATION_GUARD_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
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

- python -m pytest -q tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py
- python -m pytest -q tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_f6_immutable_host_mutation_guard_repair.py
- pcae status coherence passes
- pcae health passes
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-04T15:02:04.575819+02:00
