# Task Contract

## Task ID

20260626-1428-88p-shell-gate-prototype

## Title

88P — Shell Gate Prototype

## Status

active

## Mode

implementation

## Goal

Implement the first shell gate prototype as a read-only command classifier and decision
envelope. Adds `pcae shell-gate check --command "<cmd>" --json` that classifies proposed
shell commands without executing them, returning a structured JSON gate decision.

## Allowed Files

- src/pcae/core/shell_gate.py
- src/pcae/commands/shell_gate.py
- src/pcae/cli.py
- tests/test_shell_gate.py
- tests/conftest.py
- docs/PHASE_88_SHELL_GATE_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**

## Forbidden Files

- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- README.md
- .githooks/**
- src/pcae/core/permission_broker.py
- src/pcae/commands/permission_broker.py

## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- Must not execute shell commands
- Must not intercept shell execution
- Must not install shell wrappers
- Must not modify shell configuration
- Must not invoke backends
- Must not send prompts
- Must not capture outputs
- Must not perform intake/adoption
- Must not implement permission broker
- Must not grant execution authorization
- Must not write persistent gate state/cache
- Must not raw git commit
- Must not raw git push
- Must not force push

## Acceptance Criteria

- pcae shell-gate check --command "..." --json returns valid JSON
- Prototype never executes command text
- All performed flags always false
- Read-only commands classify as read_only_inspection
- Raw git commit/push/force-push blocked
- Destructive filesystem commands blocked
- Shell redirection/file writes detected
- Policy-forbidden file writes blocked
- Test execution classified
- Package install/network commands require review
- Unknown commands not allowed by default
- Targeted shell gate tests pass
- Fast-green passes
- Quick tier passes

## Acceptance Checks

- python -m pytest tests/test_shell_gate.py -q
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Create docs/PHASE_88_SHELL_GATE_PROTOTYPE.md
- Update PROJECT_STATUS.md
- Update CHANGELOG.md
- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T14:28:40.697398+02:00
