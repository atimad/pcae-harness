# Task Contract

## Task ID

20260801-1912-phase-148c-3-permission-broker-foundation-policy-applicability-contract-freeze

## Title

Phase 148C.3: Permission Broker Foundation Policy Applicability Contract Freeze

## Status

active

## Mode

implementation

## Goal

Freeze the normative Permission Broker Foundation Policy Applicability Contract (PBPA-001) recommended by 148C.2: applicability-vs-evaluation separation, applicability owner/authority, execution_class contract, POL-001..012 applicability matrix, security threat model, fail-closed defaults, versioning, backward compatibility, verification/implementation acceptance criteria. Contract-freeze only; no src/pcae/** modification; does not close B-1; does not begin 148D.

## Allowed Files

- docs/PHASE_148C.3_PERMISSION_BROKER_FOUNDATION_POLICY_APPLICABILITY_CONTRACT_FREEZE.md
- docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/**
- .pcae/**

## Forbidden Files

- src/pcae/**

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

- Primary sources independently re-inspected (Foundation source, POL-001..012, Phase 108/109, Autonomy Contract, NG-008, PR-compatible workflow Sec 5, PBPC-001 v1.1, 148C/148C.1/148C.2) rather than trusting 148C.2 summary alone
- PBPA-001 v1.0 frozen: applicability/evaluation separation, per-policy APPLICABLE/NOT_APPLICABLE result model (no broker-level decision expansion), applicability owner = policy-declared + registry-enforced, execution_class contract, anti-spoofing/classification-authenticity model, POL-001..012 applicability matrix, fail-closed defaults, determinism, versioning, backward compatibility, security threat model, verification and implementation acceptance requirements
- B-1 remains explicitly OPEN; no approval fabricated; no POL-001..012 modified; no POL-013+ added; no pcae push behavior modified; no src/pcae/** modification; runtime remains Observed/observe/unavailable
- PROJECT_STATUS.md, CHANGELOG.md, tasks/DONE.md updated; recommended next phase 148C.4 (independent verification) stated; 148D not recommended

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- pytest -m fast_green -n auto passes (4391 passed, 0 failed)

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-01T19:12:51.005923+02:00
