# Task Contract

## Task ID
20260630-1300-phase-95k-command-boundary-model

## Title
Phase 95K — Artifact-Only Invocation Command Boundary Model

## Status
active

## Mode
implementation

## Goal
Implement data model and validation layer for artifact-only invocation command boundary.

## Allowed Files
- src/pcae/core/backend_invocations.py
- tests/test_backend_invocations.py
- .pcae/.gitignore
- docs/PHASE_95_ARTIFACT_ONLY_INVOCATION_COMMAND_BOUNDARY_MODEL.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- .pcae/phase-completion-metadata.json

## Allowed Zones
- core
- tests
- docs
- tasks
- config

## Forbidden Zones
- commands
- cli

## Enforcement Mode
advisory

## Forbidden Changes
- No real backend invocation. No adapter execution. No subprocess execution. No CLI command. No execute path.

## Created Timestamp
2026-06-30T13:00:00.000000+02:00
