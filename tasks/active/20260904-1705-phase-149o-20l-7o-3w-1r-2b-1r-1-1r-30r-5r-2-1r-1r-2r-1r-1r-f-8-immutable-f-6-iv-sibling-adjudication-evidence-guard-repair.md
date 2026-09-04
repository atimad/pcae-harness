# Task Contract

## Task ID

20260904-1705-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2r-1r-1r-f-8-immutable-f-6-iv-sibling-adjudication-evidence-guard-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R: F-8 Immutable F-6-IV Sibling-Adjudication Evidence Guard Repair

## Status

active

## Mode

repair

## Goal

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R: F-8 Immutable F-6-IV Sibling-Adjudication Evidence Guard Repair

## Allowed Files

- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1_f6_immutable_host_mutation_guard_iv.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_f8_immutable_f6_iv_evidence_guard_repair.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_F8_IMMUTABLE_F6_IV_EVIDENCE_GUARD_REPAIR.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No raw git commit or raw git push; governed lifecycle only
- No rollback
- No protected-root/helper deployment mutation
- No administrator, protected-human, or YubiKey interaction
- No changes to F-4-IV tests 44/46/56 or any node outside F-6-IV tests 36/38/40/44

## Acceptance Criteria

- F-6-IV tests 36/38/40/44 use immutable completed F-6-IV evidence.
- Historical/current/future validation passes and in-range unauthorized evidence remains detectable.
- F-7/F-6/F-4/F-3 non-regression passes with no test weakening.
- Production, contracts, dependencies, runtime, and F-5 host state remain unchanged.
- F-8 is REPAIRED / FRESH IV PENDING; F-5 retry remains pending fresh F-7/F-8 IV; N-16-5 remains not closed.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-04T17:05:34.950574+02:00
