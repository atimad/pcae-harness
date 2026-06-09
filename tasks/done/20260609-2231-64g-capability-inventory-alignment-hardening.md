# Task Contract

## Task ID

20260609-2231-64g-capability-inventory-alignment-hardening

## Title

64G Capability Inventory Alignment Hardening

## Status

done

## Mode

implementation

## Goal

Resolve capability registry defects identified during Phase 64F post-implementation inspection: add missing CI entries (63A–63F, 64B), add missing CRI entries (64C, 64G), fix domain mismatches, replace duplicate detection algorithm, add CLI surface for 64D, reconcile all CI/CRI commands, reduce signal count from 18 to 15, set assessment_status to inventory_complete.

## Allowed Files

- src/pcae/core/agent.py
- src/pcae/commands/agent.py
- src/pcae/cli.py
- src/pcae/core/docs.py
- tests/test_agent.py
- docs/CAPABILITY_INVENTORY.md
- docs/COMMANDS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/done/20260609-1937-64f-orchestration-readiness-gate.md
- .pcae/session.json

## Forbidden Files

- TBD


## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks
- session
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

- No runtime invocation
- No execution_allowed = True
- No task lifecycle changes outside task commands

## Acceptance Checks

- capability_count == len(_CI_KNOWN_CAPABILITIES)
- duplicate_count == 0
- assessment_status == inventory_complete
- All 3346 tests pass
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-09T22:31:46.253990+02:00
