# Task Contract

## Task ID

20260630-1230-phase-95j-command-boundary-design

## Title

Phase 95J — Artifact-Only Invocation Command Boundary Design

## Status

active

## Mode

design

## Goal

Design the command boundary for a future single-backend artifact-only invocation command. Specify CLI shape, evidence inputs, broker/shell-gate sequence, execution boundary, audit/quarantine artifacts, failure states, and go/no-go rules. Design only — must not implement real backend invocation.

## Allowed Files

- docs/PHASE_95_ARTIFACT_ONLY_INVOCATION_COMMAND_BOUNDARY_DESIGN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/**
- tests/**

## Override Protected Files

- pyproject.toml


## Allowed Zones

- docs
- tasks
- config

## Forbidden Zones

- core
- commands
- cli
- tests
- scripts

## Allowed Dependencies

## Forbidden Dependencies

## Enforcement Mode

advisory

## Forbidden Changes

- No real backend invocation
- No adapter execution
- No subprocess execution
- No shell command execution
- No network calls
- No live runtime inspection
- No command path auto-discovery
- No PATH lookup
- No shell interception
- No wrappers
- No command mediation
- No Telegram inbound
- No remote shell
- No /run
- No runtime enforcement beyond planning/design documentation
- No autonomous mutation
- No automatic apply
- No apply execution
- No patch parsing for mutation
- No source file mutation outside scoped docs/status changes
- No automatic tests
- No automatic pcae check
- No commit/push authorization
- No real AI backend calls

## Acceptance Criteria

- Design document covers all 13 required sections
- Executive decision booleans present
- CLI structure proposed (plan, dry-run, execute-reserved)
- Required command inputs defined (15)
- Evidence verification order defined (21 steps)
- Hard-block rules defined (33 conditions)
- Output/audit boundary defined
- Failure classification (23 classes)
- Operator workflow defined
- Test plan (~41 tests)
- Go/no-go table (23 criteria)
- Recommended next phase: 95K

## Acceptance Checks

- python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py -q -ra passes
- python -m pytest tests/test_notifications.py tests/test_notifications_cli.py tests/test_telegram_notifications.py -q -ra passes
- pcae health passes
- pcae check passes

## Documentation Requirements

- docs/PHASE_95_ARTIFACT_ONLY_INVOCATION_COMMAND_BOUNDARY_DESIGN.md created
- PROJECT_STATUS.md updated
- CHANGELOG.md updated
- tasks/DONE.md updated

## Created Timestamp

2026-06-30T12:30:00.000000+02:00
