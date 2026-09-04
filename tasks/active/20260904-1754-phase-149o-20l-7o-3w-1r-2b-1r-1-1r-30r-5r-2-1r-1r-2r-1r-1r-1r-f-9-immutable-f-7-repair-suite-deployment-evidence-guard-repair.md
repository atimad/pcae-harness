# Task Contract

## Task ID

20260904-1754-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2r-1r-1r-1r-f-9-immutable-f-7-repair-suite-deployment-evidence-guard-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R: F-9 Immutable F-7-Repair-Suite Deployment-Evidence Guard Repair

## Status

active

## Mode

repair

## Goal

Repair exactly test_31_no_protected_root_mutation_in_repo_diff, test_32_no_helper_installation_artifact_added, and test_43_f4_change_is_test_only in tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_f4_immutable_scope_repair.py so they use the immutable fixed range R0..F4_REPAIR_FINALIZED instead of an unbounded/live-worktree diff; add a fresh F-9 phase-specific test suite; no repair of any other node; no production/contract/dependency change; F-5 stays absent; N-16-5 stays open

## Allowed Files

- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_f4_immutable_scope_repair.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_f9_deployment_evidence_guard_repair.py
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_F9_DEPLOYMENT_EVIDENCE_GUARD_REPAIR.md

## Forbidden Files

- src/pcae/**
- scripts/**
- pyproject.toml
- docs/contracts/**


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

- test_31, test_32, test_43 repaired to use immutable fixed historical bounds; no other node touched; F-7/F-8 repaired nodes and F-4-IV/F-6-IV nodes unchanged; F-5 remains absent; N-16-5 remains open; no production/script/dependency/contract change

## Acceptance Checks

- pcae status coherence
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-04T17:54:41.143828+02:00
