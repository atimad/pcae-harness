# Task Contract

## Task ID

20260720-2000-phase-137r-canonical-phase-id-parser-implementation

## Title

Phase 137R - Canonical Phase ID Parser Implementation

## Status

done

## Mode

implementation

## Goal

Implement the canonical Phase ID parser defined by CPIPC-001 v1.0 (src/pcae/core/phase_id.py) and migrate every inventoried lifecycle consumer to the shared implementation while preserving all externally observable behavior. Implementation phase only; grammar and comparison semantics are frozen and must not be redesigned.

## Allowed Files

- src/pcae/core/phase_id.py
- src/pcae/core/phase_reports.py
- src/pcae/core/check.py
- src/pcae/core/architecture_status.py
- src/pcae/core/context.py
- src/pcae/core/agent.py
- src/pcae/cltr_prototype/identity.py
- src/pcae/cltr_prototype/compatibility.py
- src/pcae/cltr/authority/identity.py
- src/pcae/commands/phase.py
- src/pcae/commands/push.py
- src/pcae/core/repository_transition_integration.py
- tests/test_phase_id.py
- tests/**
- docs/PHASE_137R_CANONICAL_PHASE_ID_PARSER_IMPLEMENTATION.md
- docs/CANONICAL_PHASE_ID_PARSER_MIGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/TODO.md
- tasks/DECISIONS.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-reports/latest.md
- .pcae/phase-reports/latest.json
- tasks/active/**
- tasks/done/**

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

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- Exactly one canonical Phase ID parser implementation exists, conforming to CPIPC-001 v1.0
- Every inventoried consumer (CPIPC-001 §14) is migrated or explicitly documented as a deferred exception
- All historical Phase ID forms remain valid; previously discovered truncation defects cannot recur
- Comparison semantics conform exactly to CPIPC-001 §10; no artificial total ordering introduced
- Runtime remains Observed / observe / unavailable; no lifecycle, governance, or CLI behavior changes

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- python -m pytest -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-20T20:00:01.260495+02:00
