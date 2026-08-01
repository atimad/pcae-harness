# Task Contract

## Task ID

20260801-0139-phase-147o-1-authority-evaluation-production-wiring

## Title

Phase 147O.1: Authority Evaluation Production Wiring

## Status

active

## Mode

implementation

## Goal

Implement AESIC-O-01 production wiring: one supported composition root that constructs AES (Registry, Decision Template resolver, AER store, canonical-pointer store) from persistent configuration and wires Stage 1 (Interactive Workflow) and Stage 2 (publication lifecycle) into supported production entry points, per AESIC-001 v1.3, bounded per the 147O.1 authorization (no contract amendment, no gating, no chapter certification).

## Allowed Files

- src/pcae/**
- tests/**
- docs/implementation/PHASE_147O1_AUTHORITY_EVALUATION_PRODUCTION_WIRING.md
- .pcae/policy.toml
- docs/COMMANDS.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

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

- One supported production composition path constructs AES automatically from persistent configuration
- Stage 1 reachable through Interactive Workflow; Stage 2 reachable through publication lifecycle
- Real AER and canonical-pointer persistence used; CHGR receives current-effective citation
- Legacy workflows remain backward compatible; missing configuration behaves safely
- Runtime remains Observed / observe / unavailable; no gating of confirmation/readiness/publication/execution
- AESIC-N-01 demonstrably contained or narrowly repaired if production reachability requires it

## Acceptance Checks

- pcae check passes
- pcae health passes
- python -m pytest -m fast_green -n auto -q passes
- AE chapter tests (147G/147H/147M/147N) pass
- New 147O.1 production-wiring tests pass

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-01T01:39:54.382569+02:00
