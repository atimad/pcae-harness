# Task Contract

## Task ID

20260711-1617-phase-134e-8-architecture-status-generation-repair

## Title

Phase 134E.8 Architecture Status Generation Repair

## Status

active

## Mode

implementation

## Goal

Repair Architecture Status generation so it derives completed/current/planned/runtime state from current governed project-state sources instead of stale hand-maintained roadmap fragments (root cause: regex mismatch between 'Recommended next repo phase:' and current 'Recommended next phase:' wording plus a first-match-in-file fallback, compounded by a completed-phase scope restricted to the 110-113 series only). Establish one explicit authority model, semantic freshness validation, conflict fail-closed/disclosure behavior, deterministic phase-ID ordering (dotted + verification suffixes), and a narrow read-only CLI inspection command. Reuse 134B.3 canonical identity resolution. No activation of Canonical Engineering Evidence, Evidence Extraction, Phase Report View, Operator Report View, Rendering Architecture, Delivery Pipeline, or Delivery Receipts. Do not begin 134E.8V or 134E.9.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/core/architecture_status.py
- src/pcae/cli.py
- src/pcae/commands/architecture_status.py
- docs/PHASE_134_ARCHITECTURE_STATUS_GENERATION_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active
- tasks/active/20260711-1617-phase-134e-8-architecture-status-generation-repair.md
- tests/test_architecture_status_generation_repair_134e8.py
- tests/test_architecture_status_canonicalization.py

## Forbidden Files

- TBD


## Allowed Zones

- core
- cli
- commands
- tests
- docs
- tasks

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

- Architecture Status no longer reports completed 132F work as planned when generated from the real repository
- Completed phases cannot remain planned; exact dotted/verification phase identities preserved; conflicts fail closed or disclosed
- fast_green test suite passes with only the known pre-existing unrelated failure

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-11T16:17:04.632145+02:00
