# Task Contract

## Task ID

20260918-2040-n16-5-f-5-tb-helper-provisioning-source-conformance-repair-remove-forbidden-provisioning-dispatch-from-live-helper-source

## Title

N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR: remove forbidden provisioning dispatch from live helper source

## Status

active

## Mode

implementation

## Goal

Narrow source-only conformance repair: remove configure_privileged_helper/configure_presentation_mechanism from CLOSED_ADMIN_MUTATIONS and their store-adapter/operations dispatch branches, bringing production source into byte-level conformance with already-frozen HPAC-PAWA-001 v4.0 / HPAC-PAWA-HELPER-001 v5.0 / HPAC-PPA-001 v2.1 contracts; no contract change, no foundation repair, no PAWA-98 standalone implementation, no live host mutation

## Allowed Files

- src/pcae/core/hpac_pawa_helper_protocol.py
- src/pcae/core/hpac_pawa_helper_store_adapter.py
- src/pcae/core/hpac_pawa_helper_operations.py
- tests/test_n16_5_f_5_tb_provisioning_source_conformance_repair.py
- docs/PHASE_N16_5_F_5_TB_HELPER_PROVISIONING_SOURCE_CONFORMANCE_REPAIR.md
- PROJECT_STATUS.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- CHANGELOG.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-metadata-repairs.log
- .pcae/fast-green-attribution/*
- .pcae/session.json
- .pcae/agent-locks/latest.json
- .pcae/handoffs/*
- .pcae/architecture-history.json
- tasks/active/*
- tasks/done/*

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

- Both configure_privileged_helper and configure_presentation_mechanism absent from CLOSED_ADMIN_MUTATIONS and all H-side dispatch branches
- Contract files byte-unchanged; N-16-5 remains open; no live host mutation

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-18T20:40:27.510098+02:00
