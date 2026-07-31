# Task Contract

## Task ID

20260731-1259-phase-147l-5-aesic-001-stage-1-idempotency-and-restart-matrix-contract-repair

## Title

Phase 147L.5: AESIC-001 Stage 1 Idempotency and Restart-Matrix Contract Repair

## Status

done

## Mode

contract-repair

## Goal

Repair AESIC-001 v1.2 to v1.3: resolve Finding A (idempotency no-op vs. mandatory stage_1_outcome_ref) and Finding B (missing restart-matrix row for AER-commit/pointer-write crash) from Phase 147L.4, per its recommended-next-phase. Contract-repair only, no implementation.

## Allowed Files

- docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md
- docs/verification/PHASE_147L5_AESIC_IDEMPOTENCY_RESTART_CONTRACT_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/**
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/**
- tests/**
- schemas/**


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

2026-07-31T12:59:15.062121+02:00
