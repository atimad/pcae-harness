# Task Contract

## Task ID

20260723-2034-phase-143f-1-phase-143e-canonical-report-and-metadata-repair

## Title

Phase 143F.1: Phase 143E Canonical Report and Metadata Repair

## Status

active

## Mode

governance

## Goal

Independently reproduce Phase 143F's report-integrity findings; repair any live inconsistency in the canonical governance-trust artifacts (.pcae/phase-completion-report.md, .pcae/phase-completion-metadata.json) associated with Phase 143E; classify the generator footer; document findings; no CHGR-001, schema, or production-code change.

## Allowed Files

- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- docs/PHASE_143F.1_PHASE_143E_CANONICAL_REPORT_AND_METADATA_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/done/20260723-2022-idle-awaiting-next-governed-phase-after-143f.md
- tasks/active/20260723-2034-phase-143f-1-phase-143e-canonical-report-and-metadata-repair.md
- tasks/DONE.md
- tasks/TODO.md

## Forbidden Files

- TBD


## Allowed Zones

- tasks
- docs
- config

## Forbidden Zones

- core
- commands
- cltr
- cli
- schema_runtime
- governance
- tests

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- Every Phase 143F reported inconsistency independently reproduced
- No implementation history rewritten
- Canonical report and metadata agree completely
- Generator footer independently classified
- Report validation and governance checks pass

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-23T20:34:16.756368+02:00
