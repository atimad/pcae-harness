# Task Contract

## Task ID

20260620-1554-phase-74w-claude-deepseek-output-only-prompt-smoke

## Title

Phase 74W: Claude-DeepSeek Output-Only Prompt Smoke

## Status

done

## Mode

implementation

## Goal

Add output-only prompt smoke scenario. Default must not invoke real backend. Real invocation requires --allow-real-invocation. Must send only harmless deterministic prompt, capture response, run mutation guard. Must not send task package, must not apply output.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/phase.py
- tests/test_phase.py
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active
- tasks/active/*

## Forbidden Files

- TBD


## Allowed Zones

- TBD

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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-20T15:54:06.731673+02:00
