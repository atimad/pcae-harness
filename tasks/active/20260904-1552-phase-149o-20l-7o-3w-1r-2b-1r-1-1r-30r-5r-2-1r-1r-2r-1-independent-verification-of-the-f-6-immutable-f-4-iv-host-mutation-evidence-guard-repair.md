# Task Contract

## Task ID

20260904-1552-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2r-1-independent-verification-of-the-f-6-immutable-f-4-iv-host-mutation-evidence-guard-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1: Independent Verification of the F-6 Immutable F-4-IV Host-Mutation Evidence Guard Repair

## Status

active

## Mode

independent verification

## Goal

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1: Independent Verification of the F-6 Immutable F-4-IV Host-Mutation Evidence Guard Repair

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1_f6_immutable_host_mutation_guard_iv.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1_F6_IMMUTABLE_HOST_MUTATION_GUARD_IV_BLOCKED.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/**
- scripts/**
- pyproject.toml
- docs/contracts/**
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_f6_immutable_host_mutation_guard_repair.py


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

- No repair of F-6 or the three disclosed sibling guards
- No production, script, contract, or dependency mutation
- No F-5 protected-root/helper deployment mutation
- No administrator, protected-human, or YubiKey interaction
- No N-16-5 closure; no N-16-6, N-16-7, Slice C, adapter dispatch, or first effect
- No raw git commit or push, hook bypass, force push, or history rewrite

## Acceptance Criteria

- Independently derive and verify immutable F-4-IV V4/U4 bounds, commits, files, and F-6 semantics
- Verify historical, current-successor, future-successor, and negative forbidden-history behavior
- Identify and independently adjudicate all three sibling moving-history guards without repairing them
- Issue explicit F-5 retry readiness and preserve F-5 absent and N-16-5 not closed
- Complete governed reporting, commit, push, notification, and lifecycle

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-04T15:52:17.505375+02:00
