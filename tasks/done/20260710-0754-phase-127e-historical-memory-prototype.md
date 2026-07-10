# Task Contract

## Task ID

20260710-0754-phase-127e-historical-memory-prototype

## Title

Phase 127E Historical Memory Prototype

## Status

done

## Mode

implementation

## Goal

Implement the first deterministic, read-only Historical Memory Builder exactly as specified by 127A-127D. Builder constructs Historical Snapshot/Timeline/Event/Transition/Relationship/Context/Evidence from git-tracked task contracts (tasks/done/*.md), git history, and an existing Repository Knowledge Snapshot (via Query Layer). No reasoning, no inference, no recommendations, no execution capability.

## Allowed Files

- src/pcae/repository_intelligence/historical_memory/__init__.py
- src/pcae/repository_intelligence/historical_memory/git_source.py
- src/pcae/repository_intelligence/historical_memory/historical_builder.py
- src/pcae/repository_intelligence/historical_memory/historical_validation.py
- src/pcae/repository_intelligence/historical_memory/persistence.py
- src/pcae/repository_intelligence/historical_memory/historical_generator.py
- src/pcae/commands/repository_intelligence.py
- src/pcae/cli.py
- tests/test_phase_127e_historical_memory_prototype.py
- docs/PHASE_127_HISTORICAL_MEMORY_PROTOTYPE_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-0754-phase-127e-historical-memory-prototype.md

## Forbidden Files

- TBD


## Allowed Zones

- commands
- cli
- tests
- docs
- tasks
- unclassified

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

- Historical Memory Builder implemented per 127A-127D, consuming task contracts/git history/RKS deterministically
- Byte-deterministic across repeated runs, verified against real repository data (850+ task contracts)
- Independent schema conformance confirmed against frozen 119Q schema with zero errors on real generated output
- All required fail-closed scenarios verified
- Regressions (DKG/change-impact/advisory/query/snapshot), fast_green, and compileall all pass
- No reasoning, inference, recommendations, or execution capability introduced
- Runtime remains Observed/observe/execution-unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T07:54:44.909967+02:00
