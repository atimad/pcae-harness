# Task Contract

## Task ID

20260618-0535-70f-pre-push-governance

## Title

70F Pre-Push Governance

## Status

done

## Mode

implementation

## Goal

Add pcae push check as a governed readiness command that summarizes whether the repository is safe to push.

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/push.py
- src/pcae/core/push.py
- tests/test_push.py
- docs/COMMANDS.md
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/active/**

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

advisory

## Forbidden Changes

- TBD

## Acceptance Checks

- pcae push check reports clean repo readiness
- pcae push check reports dirty repo refusal
- pcae push check reports unpushed commits
- pcae push check --json emits structured output
- Existing commands remain unchanged
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T05:35:07.700129+02:00
