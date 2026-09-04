# Task Contract

## Task ID

20260904-1612-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2r-1r-f-7-immutable-remaining-f-4-iv-evidence-guard-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R: F-7 Immutable Remaining F-4-IV Evidence Guard Repair

## Status

done

## Mode

repair

## Goal

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R: F-7 Immutable Remaining F-4-IV Evidence Guard Repair

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_f7_remaining_f4_iv_evidence_guard_repair.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_F7_REMAINING_F4_IV_EVIDENCE_GUARD_REPAIR.md
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

- No test change except exact F-4-IV tests 44, 46, and 56
- No production, script, dependency, or contract change
- No protected host deployment mutation or PAWA deployment authority
- No administrator, protected-human, or YubiKey interaction
- No N-16-5 closure, N-16-6/N-16-7, Slice C, dispatch, or first effect
- No raw git commit/push, bypass, force push, or history rewrite

## Acceptance Criteria

- Reconstruct and minimally bind tests 44, 46, and 56 to immutable evidence
- Preserve negative sensitivity and future-successor resilience without weakening
- Preserve F-3/F-4/F-6 and product/host/runtime boundaries
- Complete governed reporting, commit, push, notification, and lifecycle

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-04T16:12:21.731686+02:00
