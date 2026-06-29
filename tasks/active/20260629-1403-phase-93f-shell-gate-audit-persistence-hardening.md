# Task Contract

## Task ID

20260629-1403-phase-93f-shell-gate-audit-persistence-hardening

## Title

Phase 93F — Shell Gate Audit Persistence Hardening

## Status

active

## Mode

hardening

## Goal

Harden audit persistence: --no-audit-write, redaction safety, verify edge cases, gitignore hygiene.

## Allowed Files

- src/pcae/core/shell_gate.py
- src/pcae/commands/shell_gate.py
- src/pcae/cli.py
- tests/test_shell_gate.py
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- .pcae/.gitignore
- PROJECT_STATUS.md
- docs/PHASE_93_SHELL_GATE_AUDIT_PERSISTENCE_HARDENING.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- commands
- cli
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

2026-06-29T14:03:58.106810+02:00
