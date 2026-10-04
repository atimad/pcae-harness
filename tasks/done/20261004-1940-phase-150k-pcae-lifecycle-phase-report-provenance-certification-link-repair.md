# Task Contract

## Task ID

20261004-1940-phase-150k-pcae-lifecycle-phase-report-provenance-certification-link-repair

## Title

Phase 150K - PCAE-LIFECYCLE-PHASE-REPORT-PROVENANCE-CERTIFICATION-LINK-REPAIR

## Status

done

## Mode

implementation

## Goal

Reconstruct current lifecycle trust graph and reproduce 150J exploits; implement narrow provenance repair only if existing independent root proves historical generation relationships; otherwise complete blocked without pseudo-root or retroactive fabrication

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/commands/phase_reports.py
- src/pcae/core/finalization_transaction.py
- src/pcae/core/delivery_receipt.py
- tests/test_phase_150k_provenance_certification_link_repair.py
- docs/PHASE_150K_PROVENANCE_CERTIFICATION_LINK_REPAIR.md
- .pcae/**
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/**

## Forbidden Files

- src/pcae/core/hpac_*.py
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
- No commit
- No push
- No rollback

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae check
- pcae health
- pcae status coherence

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-10-04T19:40:11.712138+02:00
