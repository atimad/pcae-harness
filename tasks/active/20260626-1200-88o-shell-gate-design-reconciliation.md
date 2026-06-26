# Task Contract

## Task ID

20260626-1200-88o-shell-gate-design-reconciliation

## Title

88O — Shell Gate Design Reconciliation

## Status

active

## Mode

design

## Goal

Reconcile Phase 87 shell gate architecture with concrete Phase 88/88N preflight, permission-broker, fast-green, and policy-forbidden consistency work. Define how a future shell gate should reason about shell commands, filesystem mutation, git operations, test execution, raw push, backend invocation, and PCAE lifecycle state. Design only — no implementation.

## Allowed Files

- docs/PHASE_88_SHELL_GATE_RECONCILIATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260626-1200-88o-shell-gate-design-reconciliation.md
- tasks/active/**
- tasks/DONE.md
- tasks/done/**
- tasks/completed/**

## Forbidden Files

- src/**
- tests/**
- pyproject.toml
- README.md
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- .githooks/**


## Allowed Zones

- TBD

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

- docs/PHASE_88_SHELL_GATE_RECONCILIATION.md exists with full command taxonomy, decision model, role/non-role, and future roadmap
- No source files changed
- No test files changed
- Fast-green passes (1,792 tests)
- Health/check/doctor/push clean

## Acceptance Checks

- python -m pytest -m fast_green -n auto -q
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T12:00:25.502564+02:00
