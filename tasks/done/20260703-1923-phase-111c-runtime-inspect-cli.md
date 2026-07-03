# Task Contract

## Task ID

20260703-1923-phase-111c-runtime-inspect-cli

## Title

Phase 111C: Runtime Inspect CLI

## Status

done

## Mode

implementation

## Goal

Add the first official Runtime CLI inspection command, pcae runtime inspect (plus --json and --verbose), exposing 111B's observation-only runtime introspection model as a safe, read-only operational snapshot. No runtime behavior change, no plugin loading/instantiation/invocation, no Permission Broker evaluation, no execution capability.

## Allowed Files

- src/pcae/commands/runtime_inspect.py
- src/pcae/cli.py
- tests/test_runtime_inspect_cli.py
- docs/PHASE_111_RUNTIME_INSPECT_CLI.md
- docs/ROADMAP.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
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

2026-07-03T19:23:08.541682+02:00
