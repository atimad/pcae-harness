# Task Contract

## Task ID

20260918-1127-n16-5-f-5-tb-helper-installation-identity-contract-repair-iv

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1: Independent Adversarial Verification of Model I-B Installation Identity and Helper Admission Contracts (N16-5-F-5-TB-HELPER-INSTALLATION-IDENTITY-CONTRACT-REPAIR-IV)

## Status

active

## Mode

implementation

## Goal

N16-5-F-5-TB-HELPER-INSTALLATION-IDENTITY-CONTRACT-REPAIR-IV

## Allowed Files

- tests/**
- docs/PHASE_*
- docs/evidence/**
- .pcae/**
- tasks/**
- PROJECT_STATUS.md
- CHANGELOG.md

## Forbidden Files

- src/pcae/**
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
- No rollback

## Acceptance Criteria

- Complete independent contract IV, preserving source and contracts.
- Record verified findings and a truthful VERIFIED or BLOCKED verdict.
- Complete governed lifecycle; no successor begun.

## Acceptance Checks

- pcae check
- pcae health
- pcae status coherence
- python -m pytest -q tests/test_n16_5_f_5_tb_helper_installation_identity_contract_repair_iv.py

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-18T11:27:35.868484+02:00
