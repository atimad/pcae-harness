# Task Contract

## Task ID

20260720-2148-phase-137s-canonical-phase-id-parser-independent-verification

## Title

Phase 137S - Canonical Phase ID Parser Independent Verification

## Status

active

## Mode

validation

## Goal

Independently verify Phase 137R's Canonical Phase ID Parser implementation against CPIPC-001 v1.0, re-deriving expected behavior from the frozen contract rather than trusting 137R's report. Repair only minimum implementation necessary if a Blocking defect is independently demonstrated.

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
- tests/**
- docs/PHASE_137S_CANONICAL_PHASE_ID_PARSER_INDEPENDENT_VERIFICATION.md
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

- Independent verification report confirms or refutes CPIPC-001 conformance with concrete, reproducible evidence
- Fresh consumer inventory produced independent of 137R's claimed migration list
- Any Blocking defect independently demonstrated is repaired minimally with regression coverage; non-blocking gaps disclosed
- Runtime remains Observed / observe / unavailable

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- pcae push check
- python -m pytest -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-20T21:48:31.879498+02:00
