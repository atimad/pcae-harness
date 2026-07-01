# Task Contract

## Task ID

20260701-2229-phase-106b-release-critical-warning-fast-green-triage

## Title

Phase 106B — Release-Critical Warning / Fast-Green Triage

## Status

done

## Mode

repair

## Goal

Triage the 3 known fast-green failures (Test94UPreflightArtifact, Test94UPreflightArtifactCLI, TestBackendShow), determine release disposition, repair if safe, confirm task-memory clean.

## Allowed Files

- docs/PHASE_106_RELEASE_CRITICAL_WARNING_FAST_GREEN_TRIAGE.md
- docs/RELEASE_SCOPE_V0_1.md
- tests/test_release_critical_triage_v0_1.py
- tests/test_release_scope_v0_1.py
- tests/test_backend_invocations.py
- tests/test_backend_cli.py
- src/pcae/core/backend_invocations.py
- src/pcae/commands/backend.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- tests
- docs
- tasks
- config
- commands

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

2026-07-01T22:29:01.509840+02:00
