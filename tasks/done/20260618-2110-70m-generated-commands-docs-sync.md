# Task Contract

## Task ID

20260618-2110-70m-generated-commands-docs-sync

## Title

70M Generated Commands Docs Sync

## Status

done

## Mode

implementation

## Goal

Regenerate docs/COMMANDS.md from registered CLI commands to eliminate the drift warning.

## Allowed Files

- docs/COMMANDS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/DONE.md

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

- pcae health reports no COMMANDS.md drift warning
- pcae check passes
- pcae doctor task-memory reports clean

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-18T21:10:31.602245+02:00
