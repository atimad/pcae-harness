# Task Contract

## Task ID

20260911-0936-n16-5-f-5-tb-helper-impl-privileged-helper-hpac-pawa-helper-1-0-protocol-foundation-implementation

## Title

N16-5-F-5-TB-HELPER-IMPL: Privileged Helper + HPAC-PAWA-HELPER/1.0 Protocol Foundation Implementation

## Status

active

## Mode

implementation

## Goal

Implement the protected-helper + HPAC-PAWA-HELPER/1.0 protocol FOUNDATION per the frozen, independently-verified contract trio (HPAC-PAWA-001 v2.0, HPAC-PAWA-HELPER-001 v1.0, HPAC-PPA-001 v2.0). Foundation only: closed protocol schema/dispatch, provenance/anti-TOCTOU same-file-object execution, one-shot channel, OS peer-credential auth, configured-agent exclusion, freshness/replay, state machine, evidence staging, bounded per-operation handlers, and full positive/negative test matrix. No live protected-host mutation, no real ceremony, no caller migration, no legacy-path removal.

## Allowed Files

- src/pcae/core/hpac_pawa_helper_protocol.py
- src/pcae/core/hpac_pawa_helper_operations.py
- src/pcae/core/hpac_pawa_helper_os.py
- tests/test_hpac_pawa_helper_protocol_foundation.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1_1_1_1_1_1_1_1_N16_5_F_5_TB_HELPER_IMPL.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/**

## Forbidden Files

- TBD


## Allowed Zones

- tasks
- core
- docs
- tests
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

- TBD

## Acceptance Checks

- pcae health passes
- focused helper/protocol test suite passes
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-11T09:36:32.703772+02:00
