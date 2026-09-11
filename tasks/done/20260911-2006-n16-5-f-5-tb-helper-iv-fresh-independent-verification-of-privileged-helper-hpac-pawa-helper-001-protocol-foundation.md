# Task Contract

## Task ID

20260911-2006-n16-5-f-5-tb-helper-iv-fresh-independent-verification-of-privileged-helper-hpac-pawa-helper-001-protocol-foundation

## Title

N16-5-F-5-TB-HELPER-IV — Fresh Independent Verification of Privileged Helper / HPAC-PAWA-HELPER-001 Protocol Foundation

## Status

done

## Mode

implementation

## Goal

Independently verify the helper/protocol foundation implemented by N16-5-F-5-TB-HELPER-IMPL / IMPL.1: process isolation, no ordinary-interpreter authority access, same-file-object execution (Linux vs macOS fail-closed), helper provenance, peer credentials, configured-agent exclusion, closed 5-op dispatch, replay/currentness (reproduce REPLAY-AFTER-RESTART defect via real cross-process test), state transitions, no-auto-retry boundary, no-authority-export, five-role/typed-read closure, ceremony_entry/presentation_evidence_write boundedness (disposable fixtures only), deterministic-vs-real separation, runtime/effect non-expansion. Verification only — no repair, no live/production/ceremony actions.

## Allowed Files

- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1_1_1_1_1_1_1_1_1_1_n16_5_f_5_tb_helper_iv.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1_1_1_1_1_1_1_1_1_1_N16_5_F_5_TB_HELPER_IV.md
- tasks/active/20260911-2006-n16-5-f-5-tb-helper-iv-fresh-independent-verification-of-privileged-helper-hpac-pawa-helper-001-protocol-foundation.md
- tasks/done/20260911-1828-idle-post-n16-5-f-5-tb-helper-impl-1-complete-scope-fence-reconciliation-done-n16-5-f-5-tb-helper-iv-next-n-16-5-not-closed.md

## Forbidden Files

- TBD


## Allowed Zones

- tests
- docs
- tasks
- config

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

- Independent cross-process replay-after-restart test executed and result (confirmed/refuted) recorded
- All scoped verification areas covered with explicit pass/fail/not-evaluated disposition
- No src/pcae production file, contract, schema, or dependency modified
- No live protected-host mutation, no real ceremony, no real certification performed

## Acceptance Checks

- pcae check
- python -m pytest -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-11T20:06:50.034745+02:00
