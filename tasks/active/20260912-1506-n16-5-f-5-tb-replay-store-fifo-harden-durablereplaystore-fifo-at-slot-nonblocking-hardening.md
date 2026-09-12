# Task Contract

## Task ID

20260912-1506-n16-5-f-5-tb-replay-store-fifo-harden-durablereplaystore-fifo-at-slot-nonblocking-hardening

## Title

N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN: DurableReplayStore FIFO-at-slot nonblocking hardening

## Status

active

## Mode

implementation

## Goal

Close the FIFO-at-slot blocking-open availability finding documented by N16-5-F-5-TB-HELPER-IV-R by adding O_NONBLOCK to DurableReplayStore._read(); add focused adversarial tests; run full governed finalization lifecycle.

## Allowed Files

- src/pcae/core/hpac_pawa_helper_replay_state.py
- tests/test_n16_5_f_5_tb_replay_repair.py
- tests/test_n16_5_f_5_tb_helper_iv_r.py
- docs/PHASE_N16_5_F_5_TB_REPLAY_STORE_FIFO_HARDEN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-12T15:06:22.186554+02:00
