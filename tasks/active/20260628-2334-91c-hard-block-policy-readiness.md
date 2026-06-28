# Task Contract

## Task ID

20260628-2334-91c-hard-block-policy-readiness

## Title

91C — Hard-Block Policy Readiness

## Status

active

## Mode

implementation

## Goal

Harden the permission broker hard-block policy model with an explicit registry. Prove that non-overridable hard blocks are represented, explained, tested, auditable, and ready for future shell-gate planning.

## Allowed Files

- src/pcae/core/permission_broker.py
- src/pcae/commands/permission_broker.py
- src/pcae/cli.py
- tests/test_permission_broker.py
- docs/PHASE_91_HARD_BLOCK_POLICY_READINESS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- .githooks/**
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md

## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks

## Forbidden Zones

- hooks
- config
- session
- policy
- package
- scripts

## Enforcement Mode

advisory

## Acceptance Criteria

- Hard-block registry with all 12 categories, each with required fields
- Tests proving all invariants (non-overridable, audit_required, etc.)
- Optional CLI: pcae permission-broker hard-blocks --json
- Fast-green passes

## Acceptance Checks

- pcae health && pcae check
- python -m pytest tests/test_permission_broker.py tests/test_permission_broker_cli.py -q -ra
- python -m pytest -m "fast_green" -n auto -ra --durations=100

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T23:34:53.867254+02:00
