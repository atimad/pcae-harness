# Task Contract

## Task ID

20260706-0809-115d-repository-evidence-provider-prototype

## Title

115D: Repository Evidence Provider Prototype

## Status

active

## Mode

implementation

## Goal

Implement the first deterministic Repository Evidence Providers (Git/Runtime/Report/Metadata), read-only, no decision evaluation, no validator/lifecycle/notification integration

## Allowed Files

- src/pcae/core/evidence_providers.py
- tests/test_evidence_providers.py
- docs/PHASE_115D_REPOSITORY_EVIDENCE_PROVIDER_PROTOTYPE.md
- tasks/active/20260706-0809-115d-repository-evidence-provider-prototype.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- docs
- tests
- tasks

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

- Four deterministic evidence providers implemented producing EvidenceCollection; no integration with validator/lifecycle/notification/verify-handoff/runtime inspect

## Acceptance Checks

- python -m pytest tests/test_evidence_providers.py -n auto -q -ra --durations=100

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T08:09:28.338015+02:00
