# Task Contract

## Task ID

20260912-1707-n16-5-f-5-tb-caller-integration-arch-caller-client-integration-architecture-for-privileged-helper-consumption

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1 (N16-5-F-5-TB-CALLER-INTEGRATION-ARCH): Caller/Client Integration Architecture for Privileged Helper Consumption

## Status

done

## Mode

documentation

## Goal

Design (architecture-only, no implementation) the production caller/client integration architecture migrating in-process HPAC privileged-authority callers onto the verified out-of-process privileged-helper path. No production caller/helper/replay code changes. No contract/schema evolution. No macOS implementation. No packaging/live-host mutation. No real ceremony.

## Allowed Files

- docs/PHASE_N16_5_F_5_TB_CALLER_INTEGRATION_ARCH.md
- docs/ARCHITECTURE_CALLER_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/*.json
- tasks/active/*.md
- tasks/done/*.md
- tests/test_n16_5_f_5_tb_caller_integration_arch*.py

## Forbidden Files

- docs/HPAC_PAWA_HELPER_001.md
- docs/HPAC_PAWA_001.md
- docs/HPAC_PPA_001.md


## Allowed Zones

- TBD

## Forbidden Zones

- core
- commands
- cltr
- cli
- schema_runtime
- governance
- interactive_workflow
- authority_evaluation
- aesic
- package
- policy

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- Complete caller/legacy-authority inventory from primary source, not summaries
- Every caller mapped to one of the five existing closed helper operations; no sixth operation invented
- Client/transport/launcher architecture, platform model, no-fallback rule, retirement plan, migration slices, and threat matrix all defined
- Zero production src/pcae changes; contracts/schemas/dependencies unchanged; zero live protected-host writes; no real ceremony

## Acceptance Checks

- fast_green
- report_notification_tests
- bootstrap_session_reporting_tests

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-12T17:07:12.702809+02:00
