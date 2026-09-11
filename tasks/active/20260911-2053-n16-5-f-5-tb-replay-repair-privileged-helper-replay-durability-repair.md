# Task Contract

## Task ID

20260911-2053-n16-5-f-5-tb-replay-repair-privileged-helper-replay-durability-repair

## Title

N16-5-F-5-TB-REPLAY-REPAIR: Privileged Helper Replay-Durability Repair

## Status

active

## Mode

implementation

## Goal

Canonical phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1 (alias N16-5-F-5-TB-REPLAY-REPAIR): implement smallest contract-preserving repair for durable/reconstructible cross-process spent-request replay state under the existing protected-root trust boundary, closing the confirmed REPLAY-AFTER-RESTART defect from N16-5-F-5-TB-HELPER-IV, without evolving HPAC-PAWA-001 v2.0 / HPAC-PAWA-HELPER-001 v1.0 / HPAC-PPA-001 v2.0.

## Allowed Files

- src/pcae/core/hpac_pawa_helper_protocol.py
- src/pcae/core/hpac_pawa_helper_operations.py
- src/pcae/core/hpac_pawa_helper_os.py
- src/pcae/core/hpac_pawa_helper_replay_state.py
- tests/test_hpac_pawa_helper_protocol_foundation.py
- tests/test_n16_5_f_5_tb_replay_repair.py
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_N16_5_F_5_TB_REPLAY_REPAIR.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/done/20260911-0949-idle-post-n16-5-f-5-tb-helper-impl-complete-helper-protocol-foundation-implemented-iv-pending-scope-fence-reconciliation-phase-then-n16-5-f-5-tb-helper-iv-next-n-16-5-not-closed.md
- tasks/done/20260911-2041-idle-post-n16-5-f-5-tb-helper-iv-complete-not-verified-blocked-n16-5-f-5-tb-replay-repair-next-n-16-5-not-closed.md
- tasks/active/20260911-2053-n16-5-f-5-tb-replay-repair-privileged-helper-replay-durability-repair.md
- tasks/done/20260911-2053-n16-5-f-5-tb-replay-repair-privileged-helper-replay-durability-repair.md

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

- TBD

## Acceptance Criteria

- Durable cross-process replay state implemented under existing protected-root trust boundary; clean-restart, response-loss, crash-after-attempt, concurrent-duplicate, conflicting-replay, malformed-record, and restart-dead-authority/history-persists tests all pass; contracts byte-unchanged

## Acceptance Checks

- pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-11T20:53:59.867828+02:00
