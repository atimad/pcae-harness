# Task Contract

## Task ID

20260628-2329-91b-broker-cli-and-decision-explanation

## Title

91B — Broker CLI and Decision Explanation

## Status

active

## Mode

implementation

## Goal

Expose the Phase 91A simulation-only permission broker through safe CLI inspection commands (broker status, explain, check) and add decision explanation support.

## Allowed Files

- src/pcae/commands/permission_broker.py
- src/pcae/cli.py
- tests/test_permission_broker_cli.py
- docs/PHASE_91_BROKER_CLI_AND_DECISION_EXPLANATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- .githooks/**
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md

## Allowed Zones

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

## Forbidden Changes

- No real enforcement, blocking, shell interception, wrappers
- No backend invocation, prompt sending, output capture, intake/adoption
- No command execution through enforcement path
- No Telegram, notification code
- No weakening tests
- No raw git commit/push, force push, --no-verify
- No starting 91C

## Acceptance Criteria

- pcae broker status (text + JSON)
- pcae broker explain --reason-code <code> (text + JSON)
- pcae broker check with metadata flags (text + JSON)
- All reason codes from 91A have explanations
- CLI tests covering all outcomes
- Fast-green passes

## Acceptance Checks

- pcae health
- pcae check
- python -m pytest tests/test_permission_broker.py tests/test_permission_broker_cli.py -q -ra
- python -m pytest -m "fast_green" -n auto -ra --durations=100
- pcae doctor task-memory
- pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T23:29:00.489364+02:00
