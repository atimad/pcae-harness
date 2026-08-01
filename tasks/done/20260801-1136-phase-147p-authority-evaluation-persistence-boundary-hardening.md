# Task Contract

## Task ID

20260801-1136-phase-147p-authority-evaluation-persistence-boundary-hardening

## Title

Phase 147P: Authority Evaluation Persistence Boundary Hardening

## Status

done

## Mode

implementation

## Goal

Repair AESIC-N-01 (canonical-pointer cross-key confusion) and 147O.2-F-1 (package_id path containment) in AuthorityEvaluationRecordStore, per Phase 147O.3's recommendation.

## Allowed Files

- src/pcae/aesic/**
- tests/test_phase_147n_authority_evaluation_integration_independent_verification.py
- tests/test_phase_147o2_authority_evaluation_production_wiring_independent_verification.py
- tests/test_phase_147p_authority_evaluation_persistence_boundary_hardening.py
- docs/implementation/PHASE_147P_AUTHORITY_EVALUATION_PERSISTENCE_BOUNDARY_HARDENING.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/**

## Forbidden Files

- TBD


## Allowed Zones

- aesic
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

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-01T11:36:40.744653+02:00
